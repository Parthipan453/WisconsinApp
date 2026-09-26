"""Structured content extraction from offline application PDFs.

The offline form (built by ApplicationPdfService.build_offline_application_pdf)
is a fillable AcroForm: every dynamic-form field is a real PDF widget with a
deterministic name ``<section_code>.<field_code>``. Filled answers therefore
live in the widget values, so this module reads those first and falls back to
the plain text layer (for typed/older PDFs) when no widget values exist.

Extraction produces the two pieces reviewers care about most:

* the personal essay  -> ApplicationEssay row (shown in admin + staff pages)
* test scores         -> Application.offline_extracted_test_scores JSON

Extraction never raises: a scanned (image-only) PDF simply yields no results.
"""

import logging
import re

from django.utils import timezone

from .pdf_extractor import extract_pdf_pages

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Test scores
# ---------------------------------------------------------------------------

class _TestDef:
    __slots__ = ("test", "score_label", "date_label", "score_pattern", "max_score")

    def __init__(self, test, score_label, date_label, score_pattern, max_score):
        self.test = test
        self.score_label = score_label
        self.date_label = date_label
        self.score_pattern = score_pattern
        self.max_score = max_score


# Mirrors the "test_scores" section of the offline form (see seed.py).
TEST_DEFS = [
    _TestDef(
        "IELTS", "IELTS Total Score", "IELTS Exam Date",
        re.compile(r"\b\d(?:\.\d)?\b"), 9.0,
    ),
    _TestDef(
        "TOEFL", "TOEFL Total Score", "TOEFL Exam Date",
        re.compile(r"\b\d{1,3}\b"), 120,
    ),
    _TestDef(
        "Duolingo", "Duolingo English Test Score", "Duolingo Exam Date",
        re.compile(r"\b\d{2,3}\b"), 160,
    ),
]

_DATE_PATTERN = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")


def _value_after_label(text, label, pattern, max_score, lookahead_lines=3):
    """Find a numeric value that follows `label` in the same or next lines."""
    match = re.search(re.escape(label), text, re.IGNORECASE)
    if not match:
        return None
    window = text[match.end(): match.end() + 400]
    lines = window.splitlines()
    sample = "\n".join(lines[:lookahead_lines])
    value_match = pattern.search(sample)
    if not value_match:
        return None
    try:
        value = float(value_match.group())
    except ValueError:
        return None
    if value > max_score:
        return None
    return value_match.group()


def parse_test_scores(text):
    """Return [{test, score, date}] for every known test found in `text`."""
    scores = []
    for definition in TEST_DEFS:
        raw = _value_after_label(
            text, definition.score_label, definition.score_pattern,
            definition.max_score,
        )
        date_match = None
        if definition.date_label:
            label_idx = text.lower().find(definition.date_label.lower())
            if label_idx != -1:
                date_match = _DATE_PATTERN.search(text[label_idx:label_idx + 200])
        if raw is not None:
            scores.append({
                "test": definition.test,
                "score": raw,
                "date": date_match.group(0) if date_match else "",
            })
    return scores


# ---------------------------------------------------------------------------
# Personal essay
# ---------------------------------------------------------------------------

_ESSAY_FIELD_LABEL = "Personal Essay"
_ESSAY_TYPE = "personal_statement"
_ESSAY_TITLE = "Personal Statement"


def _is_section_header(line):
    stripped = line.strip()
    if len(stripped) < 2 or len(stripped) > 90:
        return False
    if stripped.isupper() and stripped.isalpha() and not re.search(r"[.!?]$", stripped):
        return True
    return False


def parse_essays(text):
    """Return [{essay_type, title, content, word_count}] from the PDF text."""
    match = re.search(re.escape(_ESSAY_FIELD_LABEL), text, re.IGNORECASE)
    if not match:
        return []
    body = text[match.end():]
    lines = body.splitlines()
    content_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if content_lines:
                content_lines.append("")
            continue
        if _is_section_header(stripped):
            break
        content_lines.append(stripped)
    content = "\n".join(content_lines).strip()
    if not content:
        return []
    return [
        {
            "essay_type": _ESSAY_TYPE,
            "title": _ESSAY_TITLE,
            "content": content,
            "word_count": len(content.split()),
        }
    ]


# ---------------------------------------------------------------------------
# Widget (AcroForm) values
# ---------------------------------------------------------------------------

# Field codes (see seed data) for the "Academic Background: Test Scores" section.
_TEST_FIELD_CODES = [
    ("IELTS", "ielts_total", "ielts_exam_date"),
    ("TOEFL", "toefl_total", "toefl_exam_date"),
    ("Duolingo", "duolingo_total", "duolingo_exam_date"),
]

_ESSAY_FIELD_LABEL = "Personal Essay"


def _widget_values_by_code(pages):
    """Return {field_code: value} from the AcroForm widgets across all pages.

    Widget names are ``<section_code>.<field_code>``; the section prefix is
    stripped so the map keys match ``FormField.code``. Later pages win when a
    code repeats (defensive; codes should be unique per form).
    """
    by_code = {}
    for page in pages:
        for widget in page.get("widgets") or []:
            name = widget.get("name") or ""
            value = widget.get("value")
            if "." in name:
                name = name.split(".", 1)[1]
            if name and value not in (None, ""):
                by_code[name] = value
    return by_code


def widget_values_by_section(pages):
    """Return {section_code: {field_code: value}} grouped by section.

    Widget names are ``<section_code>.<field_code>``.
    """
    by_section = {}
    for page in pages:
        for widget in page.get("widgets") or []:
            name = widget.get("name") or ""
            value = widget.get("value")
            if "." not in name:
                continue
            section_code, field_code = name.split(".", 1)
            if field_code and value not in (None, ""):
                by_section.setdefault(section_code, {})[field_code] = value
    return by_section


def _resolve_test_scores(widget_by_code):
    """Build test-score rows from widget values, or [] when none are present."""
    scores = []
    for test, total_code, date_code in _TEST_FIELD_CODES:
        raw = widget_by_code.get(total_code)
        if raw is None:
            continue
        raw = str(raw).strip()
        try:
            float(raw)
        except (TypeError, ValueError):
            continue
        scores.append({
            "test": test,
            "score": raw,
            "date": str(widget_by_code.get(date_code, "") or ""),
        })
    return scores


def _resolve_essay(widget_by_code):
    """Build an essay row from the AcroForm essay widget, or [] when empty."""
    from ..models import FormField

    essay_field = (
        FormField.objects.filter(label__iexact=_ESSAY_FIELD_LABEL).first()
        or FormField.objects.filter(code="personal_essay").first()
    )
    if essay_field is None:
        return []
    content = str(widget_by_code.get(essay_field.code) or "").strip()
    if not content:
        return []
    return [
        {
            "essay_type": "personal_statement",
            "title": "Personal Statement",
            "content": content,
            "word_count": len(content.split()),
        }
    ]


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def _load_pages(app):
    if app.offline_form_text:
        return app.offline_form_text
    if not app.offline_form_pdf or not app.offline_form_pdf.name:
        return []
    try:
        with app.offline_form_pdf.open("rb") as fh:
            pages = extract_pdf_pages(fh)
    except Exception:
        logger.exception("Could not read offline PDF for app %s", app.Reference_id)
        return []
    app.offline_form_text = pages
    app.offline_form_extracted_at = timezone.now()
    app.save(update_fields=["offline_form_text", "offline_form_extracted_at", "updated_date"])
    return pages


def extract_offline_content(app):
    """Extract essays + test scores from the offline PDF and persist them.

    AcroForm widget values are preferred (they carry the digitally-typed
    answers); the text layer is used as a fallback for typed / older PDFs.

    Returns a summary dict; never raises.
    """
    from ..models import ApplicationEssay

    pages = _load_pages(app)
    text = "\n".join((page.get("text") or "") for page in pages)

    results = {"essays": [], "test_scores": [], "text_available": bool(text.strip())}

    widget_by_code = _widget_values_by_code(pages)

    essays = _resolve_essay(widget_by_code)
    if not essays:
        essays = parse_essays(text)
    for essay in essays:
        ApplicationEssay.objects.update_or_create(
            application=app,
            essay_type=essay["essay_type"],
            defaults={
                "prompt_text": "",
                "content": essay["content"],
                "word_count": essay["word_count"],
                "is_complete": True,
            },
        )
        results["essays"].append(essay)

    test_scores = _resolve_test_scores(widget_by_code)
    if not test_scores:
        test_scores = parse_test_scores(text)
    app.offline_extracted_test_scores = test_scores
    app.save(update_fields=["offline_extracted_test_scores", "updated_date"])
    results["test_scores"] = test_scores

    return results
