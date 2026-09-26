"""Shared application review context for Admin + Staff review pages (Eric)."""

import json
import logging
import os

logger = logging.getLogger(__name__)

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.html import escape

from Applicants.models import (
    Application,
    ApplicationChecklistItem,
    ApplicantProfile,
    DocumentRequirement,
    FieldResponse,
    MaterialRequest,
)
from Applicants.services.form_engine import DynamicFormEngine


def _has_form_file_response(application, section_code, field_code):
    """Whether the applicant uploaded a file via an online form field."""
    return FieldResponse.objects.filter(
        response__application=application,
        response__section__code=section_code,
        field__code=field_code,
    ).exclude(file__in=["", None]).exists()


def fulfill_completed_material_requests(application):
    """Mark pending material requests fulfilled once their material exists.

    A request can be anchored to a DocumentRequirement, to a document type, or
    (for fee / high-school-grades) to a generic request with `requirement=None`.
    The latter have no upload action on the applicant status page, so they were
    never marked fulfilled. This syncs the stored status against live data.
    """
    if application.apply_method == "offline" and application.offline_form_pdf:
        has_offline_essay = application.essays.filter(is_complete=True).exists()
        has_offline_scores = bool(application.offline_extracted_test_scores)
        if not has_offline_essay or not has_offline_scores:
            from Applicants.services.offline_parser import extract_offline_content

            extract_offline_content(application)
            application.refresh_from_db()

    pending = list(application.material_requests.filter(status="pending"))
    if not pending:
        return []

    doc_requirement_codes = set(
        application.documents.exclude(requirement=None).values_list(
            "requirement__code", flat=True
        )
    )
    doc_types = set(application.documents.values_list("doc_type", flat=True))
    has_completed_payment = application.payments.filter(status="completed").exists()
    has_grades = (
        _has_form_file_response(application, "high_school", "hs_grades")
        or application.documents.filter(
            Q(requirement__code__icontains="grade")
            | Q(requirement__code__icontains="marksheet")
            | Q(file_name__icontains="grade")
        ).exists()
    )
    any_document = application.documents.exists()
    has_offline_essay = application.essays.filter(is_complete=True).exists()
    has_offline_scores = bool(application.offline_extracted_test_scores)

    fulfilled = []
    for mr in pending:
        if mr.requirement_id:
            if (
                mr.requirement.code in doc_requirement_codes
                or (
                    mr.requirement.code == "personal_statement"
                    and has_offline_essay
                )
                or (
                    mr.requirement.code == "english_proficiency"
                    and has_offline_scores
                )
            ):
                fulfilled.append(mr.pk)
        elif mr.doc_type and mr.doc_type != "other":
            if mr.doc_type in doc_types:
                fulfilled.append(mr.pk)
        else:
            msg = (mr.message or "").lower()
            if "fee" in msg or "pay" in msg:
                if has_completed_payment:
                    fulfilled.append(mr.pk)
            elif "grade" in msg or "academic" in msg or "school" in msg:
                if has_grades:
                    fulfilled.append(mr.pk)
            elif any_document:
                fulfilled.append(mr.pk)

    if fulfilled:
        MaterialRequest.objects.filter(pk__in=fulfilled).update(
            status="fulfilled", fulfilled_at=timezone.now()
        )
    return fulfilled


def _format_field_response(field_response):
    """Render a stored field value as a plain, readable string for review."""
    if field_response.file_name:
        return field_response.file_name
    value = field_response.typed_value()
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, dict):
        try:
            return json.dumps(value)
        except (TypeError, ValueError):
            return str(value)
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    return str(value)


def get_review_readiness(application):
    """Return which required materials are still missing from the applicant.

    An application may only be reviewed once everything below has been received:
      * Online applications: every required workflow step (academics, activities,
        essays, etc.) must have completed form responses.
      * Offline applications: the completed printed form PDF must be attached.
      * Required documents (e.g. transcripts) must have been uploaded.
    """
    from datetime import date
    missing = []

    if application.offline_form_pdf:
        if not application.offline_form_pdf.name:
            missing.append(
                {"code": "offline_form", "label": "Completed application form (PDF)"}
            )
    else:
        engine = DynamicFormEngine()
        for step in engine.get_active_workflow_steps(application):
            if step.is_required and not engine.is_step_complete(application, step.code):
                missing.append({"code": f"step:{step.code}", "label": step.name})

    for req in DocumentRequirement.objects.filter(is_required=True).order_by("name"):
        if req.university_id not in (None, application.university_id):
            continue
        if req.degree_level_id not in (None, application.degree_level_id):
            continue
        if not _doc_received(application, req.code):
            missing.append({"code": f"doc:{req.code}", "label": req.name})

    deadline_passed = False
    cycle = application.admission_cycle
    if cycle and cycle.application_deadline and date.today() > cycle.application_deadline:
        deadline_passed = True

    return {
        "ready": not missing,
        "missing": missing,
        "deadline_passed": deadline_passed,
    }


def _doc_received(application, req_code):
    """Whether the material backing a DocumentRequirement has been received.

    Matches the checklist: accepts online-form file uploads (hs_transcript,
    hs_grades), doc_type-based uploads, and documents anchored to the
    requirement itself.
    """
    if req_code == "transcript_hs":
        return (
            _has_form_file_response(application, "high_school", "hs_transcript")
            or application.documents.filter(requirement__code="transcript_hs").exists()
            or application.documents.filter(doc_type="transcript").exists()
        )
    if req_code == "transcript_college":
        return (
            _has_form_file_response(application, "higher_education_check", "college_transcript")
            or application.documents.filter(requirement__code="transcript_college").exists()
            or application.documents.filter(doc_type="transcript").exists()
        )
    if req_code == "personal_statement":
        resp = application.form_responses.filter(section__code="essay").first()
        fr = (
            resp.field_responses.filter(field__code="personal_essay").first()
            if resp
            else None
        )
        return (
            bool(fr and fr.typed_value())
            or application.essays.filter(
                essay_type="personal_statement", is_complete=True
            ).exists()
            or application.documents.filter(requirement__code="personal_statement").exists()
            or application.documents.filter(doc_type="essay").exists()
        )
    if req_code == "english_proficiency":
        resp = application.form_responses.filter(section__code="test_scores").first()
        return (
            bool(resp and resp.is_complete)
            or bool(application.offline_extracted_test_scores)
            or application.documents.filter(requirement__code="english_proficiency").exists()
            or application.documents.filter(doc_type="test_score").exists()
        )
    if "grade" in req_code:
        return (
            _has_form_file_response(application, "high_school", "hs_grades")
            or application.documents.filter(
                Q(requirement__code__icontains="grade")
                | Q(requirement__code__icontains="marksheet")
                | Q(file_name__icontains="grade")
            ).exists()
        )
    return application.documents.filter(requirement__code=req_code).exists()


def build_review_materials(application, form_groups):
    """Group everything a reviewer actually needs into five categories:
    transcript, essays, test scores, application fee, and high school grades.

    Each group carries a `received` flag so the reviewer can see at a glance
    which materials are still outstanding.
    """
    docs = list(application.documents.all())
    payments = list(application.payments.all())

    def _doc_items(predicate):
        items = []
        for d in docs:
            if not predicate(d):
                continue
            items.append(
                {
                    "label": d.file_name,
                    "meta": d.get_doc_type_display()
                    or (d.requirement.name if d.requirement else ""),
                    "verified": d.is_verified,
                    "url": d.file_path,
                }
            )
        return items

    def _form_items(section_code, skip_codes=(), skip_internal=True):
        items = []
        for group in form_groups:
            if group["response"].section.code != section_code:
                continue
            for f in group["fields"]:
                if f["field"].code in skip_codes:
                    continue
                if skip_internal and (f["field"].code.startswith("_") or not f["value"]):
                    continue
                items.append(
                    {
                        "label": f["field"].label,
                        "value": f["value"],
                        "url": f["file_url"] or "",
                        "verified": True,
                    }
                )
        return items

    def _form_file_items(section_code, field_codes):
        """File-upload form responses (e.g. hs_transcript) → transcript rows."""
        items = []
        for group in form_groups:
            if group["response"].section.code != section_code:
                continue
            for f in group["fields"]:
                if f["field"].code not in field_codes or not f["file_url"]:
                    continue
                items.append(
                    {
                        "label": f["field"].label,
                        "value": f["value"] or f["file_url"],
                        "url": f["file_url"],
                        "verified": True,
                    }
                )
        return items

    from Applicants.models import MaterialRequest

    mr_qs = MaterialRequest.objects.filter(
        application=application
    ).order_by("-requested_at")

    _CATEGORY_REQ_MAP = {
        "transcript": ("transcript_hs",),
        "essays": ("personal_statement",),
        "test_scores": ("english_proficiency",),
    }
    _CATEGORY_DOC_MAP = {
        "payment": "other",
    }

    def _requests_for(category):
        req_codes = _CATEGORY_REQ_MAP.get(category, ())
        doc_type = _CATEGORY_DOC_MAP.get(category)
        return [
            mr for mr in mr_qs
            if (mr.requirement and mr.requirement.code in req_codes)
            or (doc_type and mr.doc_type == doc_type)
        ]

    groups = []

    _TRANSCRIPT_FIELD_CODES = ("hs_transcript", "college_transcript")
    transcript_items = _doc_items(
        lambda d: d.doc_type == "transcript"
        or (d.requirement and d.requirement.code in ("transcript_hs", "transcript_college"))
    )
    for section_code in ("high_school", "higher_education_check"):
        transcript_items += _form_file_items(section_code, _TRANSCRIPT_FIELD_CODES)
    groups.append(
        {
            "key": "transcript",
            "title": "Transcript",
            "icon": "ti ti-certificate",
            "received": bool(transcript_items),
            "items": transcript_items,
            "missing_note": "Official high school transcript has not been received yet.",
            "sent_requests": _requests_for("transcript"),
            "sent_to": "applicant",
        }
    )

    essay_items = _doc_items(lambda d: d.doc_type in ("essay", "sop"))
    essay_items += _form_items("essay")
    for essay in application.essays.all():
        essay_items.append(
            {
                "label": essay.essay_type,
                "value": essay.content,
                "verified": essay.is_complete,
            }
        )
    groups.append(
        {
            "key": "essays",
            "title": "Essays",
            "icon": "ti ti-writing",
            "received": bool(essay_items),
            "items": essay_items,
            "missing_note": "No personal essay has been submitted yet.",
            "sent_requests": _requests_for("essays"),
            "sent_to": "applicant",
        }
    )

    test_items = _doc_items(
        lambda d: d.doc_type == "test_score"
        or (d.requirement and d.requirement.code == "english_proficiency")
    )
    test_items += _form_items("test_scores")
    for score in application.offline_extracted_test_scores or []:
        test_items.append(
            {
                "label": score.get("test") or "Test score",
                "value": score.get("score") or "",
                "meta": score.get("date") or "Extracted from offline PDF",
                "verified": True,
            }
        )
    groups.append(
        {
            "key": "test_scores",
            "title": "Test scores",
            "icon": "ti ti-chart-bar",
            "received": bool(test_items),
            "items": test_items,
            "missing_note": "No test score report has been submitted yet.",
            "sent_requests": _requests_for("test_scores"),
            "sent_to": "applicant",
        }
    )

    payment_items = [
        {
            "label": p.transaction_id,
            "value": f"${p.amount}",
            "meta": p.get_status_display(),
            "verified": p.status == "completed",
        }
        for p in payments
    ]
    groups.append(
        {
            "key": "payment",
            "title": "Application fee",
            "icon": "ti ti-credit-card",
            "received": any(p.status == "completed" for p in payments),
            "items": payment_items,
            "missing_note": "Application fee has not been paid yet.",
            "sent_requests": _requests_for("payment"),
            "sent_to": "applicant",
        }
    )

    grade_items = _doc_items(
        lambda d: "grade" in (d.file_name or "").lower()
        or (d.requirement and "grade" in d.requirement.code.lower())
    )
    groups.append(
        {
            "key": "grades",
            "title": "High school grades",
            "icon": "ti ti-school",
            "received": bool(grade_items),
            "items": grade_items,
            "missing_note": "High school academic history has not been completed.",
            "sent_requests": _requests_for("grades"),
            "sent_to": "applicant",
        }
    )

    return groups


_CHECKLIST_LABELS = {
    "payment": "Application Fee",
}


def _checklist_status(app):
    """Checklist items with `is_completed` computed from live application data.

    Items come from required DocumentRequirements plus payment.
    """
    stored = {c.code: c for c in app.checklist_items.all()}
    items = []

    payment_item = stored.get("payment")
    if payment_item is None:
        payment_item = ApplicationChecklistItem(
            application=app,
            code="payment",
            label="Application Fee",
            item_type="payment",
            is_required=True,
        )
    payment_item.is_completed = app.payments.filter(status="completed").exists()
    items.append(payment_item)

    for req in DocumentRequirement.objects.filter(is_required=True).order_by("name"):
        if req.university_id not in (None, app.university_id):
            continue
        if req.degree_level_id not in (None, app.degree_level_id):
            continue
        item = stored.get(req.code)
        if item is None:
            item = ApplicationChecklistItem(
                application=app,
                code=req.code,
                label=req.name,
                item_type="document",
                is_required=True,
            )
        item.is_completed = _doc_received(app, req.code)
        items.append(item)
    return items


def _uploaded_files(app):
    """Every file the applicant has on file: portal document uploads and
    files uploaded through the online application form."""
    files = []
    for doc in app.documents.all():
        files.append(
            {
                "name": doc.file_name,
                "category": (
                    doc.requirement.name if doc.requirement else doc.get_doc_type_display()
                ),
                "source": "Document upload",
                "url": doc.file_path,
            }
        )
    for fr in FieldResponse.objects.filter(
        response__application=app,
        field__field_type="file",
    ).exclude(file__in=["", None]).select_related("response__section", "field"):
        files.append(
            {
                "name": fr.file_name or os.path.basename(fr.file),
                "category": fr.response.section.title,
                "source": "Application form",
                "url": fr.file,
            }
        )
    return files


def build_review_context(application_id):
    """Assemble every application snapshot needed by the shared viewer partial."""
    app = get_object_or_404(
        Application.objects.select_related(
            "applicant",
            "university",
            "degree_level",
            "program",
            "backup_program",
            "school",
            "department",
            "admission_cycle",
            "review_assignment__reviewer",
            "review_assignment__assigned_by",
        ),
        application_id=application_id,
    )
    applicant = app.applicant
    profile = ApplicantProfile.objects.filter(applicant=applicant).first()

    _REVIEW_SECTION_ORDER = [
        "basic information",
        "contact information",
        "parent/guardian information",
        "residency information",
        "academic background: high school / secondary school",
        "academic background: college/post-secondary check",
        "academic background: test scores",
        "activities",
        "work experience",
        "essay",
        "additional information",
    ]
    _order_map = {t: i for i, t in enumerate(_REVIEW_SECTION_ORDER)}

    _SKIP_FIELD_TYPES = {"rich_text", "hidden", "heading"}

    form_groups = []
    for response in app.form_responses.select_related("form", "section").prefetch_related(
        "field_responses__field"
    ):
        fields = [
            {
                "field": fr.field,
                "value": _format_field_response(fr),
                "file_url": fr.file or "",
            }
            for fr in response.field_responses.select_related("field")
            if fr.field.field_type not in _SKIP_FIELD_TYPES
        ]
        if not fields:
            continue
        form_groups.append(
            {
                "response": response,
                "fields": fields,
            }
        )
    form_groups.sort(key=lambda g: (
        _order_map.get(g["response"].section.title.lower(), 999),
        g["response"].repeat_index,
    ))

    assignment = getattr(app, "review_assignment", None)
    fulfill_completed_material_requests(app)
    if app.apply_method == "offline" and app.offline_form_pdf:
        has_offline_essay = app.essays.filter(is_complete=True).exists()
        has_offline_scores = bool(app.offline_extracted_test_scores)
        if not has_offline_essay or not has_offline_scores:
            from Applicants.services.offline_parser import extract_offline_content

            extract_offline_content(app)
            app.refresh_from_db()

    return {
        "app": app,
        "applicant": applicant,
        "profile": profile,
        "form_groups": form_groups,
        "essays": app.essays.all(),
        "documents": app.documents.all(),
        "uploaded_files": _uploaded_files(app),
        "checklist_items": _checklist_status(app),
        "material_requests": app.material_requests.all(),
        "payments": app.payments.all(),
        "status_history": app.status_history.all(),
        "logs": app.logs.all(),
        "offline_test_scores": app.offline_extracted_test_scores or [],
        "assignment": assignment,
        "review_readiness": get_review_readiness(app),
        "form_preview": build_form_preview(app),
    }


# ---------------------------------------------------------------------------
# Real-form preview of online responses
# ---------------------------------------------------------------------------

HIDDEN_PREVIEW_TYPES = {"hidden", "heading"}


def _norm_visibility_value(value) -> str:
    s = str(value or "").strip().lower()
    if s in ("true", "on", "yes", "1"):
        return "yes"
    if s in ("false", "off", "no", "0", ""):
        return "no"
    return s


def _match_visibility_rule(rule, trigger_value) -> bool:
    """Mirror the applicant-side conditional logic (validation.js)."""
    cv = _norm_visibility_value(trigger_value)
    rv = _norm_visibility_value(rule.value)
    op = rule.operator

    if op == "neq":
        return cv == "" or cv != rv
    if op == "not_empty":
        return cv != ""
    if op == "is_empty":
        return cv == ""
    if op == "contains":
        return rv in cv
    if op in ("gt", "gte", "lt", "lte"):
        try:
            a, b = float(cv), float(rv)
        except (TypeError, ValueError):
            return False
        if op == "gt":
            return a > b
        if op == "gte":
            return a >= b
        if op == "lt":
            return a < b
        return a <= b
    if op == "in":
        return cv in [x.strip() for x in rule.value.split(",")]
    if op == "not_in":
        return cv not in [x.strip() for x in rule.value.split(",")]
    if op == "checked":
        return cv == "yes"
    if op == "not_checked":
        return cv == "no"
    return cv == "" or cv == rv


def _field_is_visible(field, value_lookup) -> bool:
    """Evaluate a field's conditional visibility from submitted values."""
    rules = list(field.visibility_rules.filter(is_active=True).order_by("sort_order"))
    if not rules:
        return True
    and_rules = [r for r in rules if r.logic_operator != "OR"]
    or_rules = [r for r in rules if r.logic_operator == "OR"]

    def _match(r):
        return _match_visibility_rule(r, value_lookup.get(r.target_field.code))

    return all(_match(r) for r in and_rules) and any(_match(r) for r in or_rules)


def _escape_form_value(value):
    """Escape a stored response value for safe interpolation into the form widgets."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return [escape(str(v)) for v in value]
    return escape(str(value))


def build_form_preview(application):
    """Assemble sections that render responses like the real dynamic form.

    Each section mirrors what the applicant saw: the same widget types, choices,
    layout and (server-side evaluated) conditional visibility — but read-only.
    Every field also carries its automatic validation result, and each section
    carries a validation summary so reviewers can scan pass/fail per section.
    """
    engine = DynamicFormEngine()
    groups = []
    responses = list(
        application.form_responses.select_related("section")
        .prefetch_related(
            "field_responses__field__choices",
            "field_responses__field__validations",
            "field_responses__field__visibility_rules__target_field",
        )
        .order_by("section__sort_order", "repeat_index")
    )
    for response in responses:
        frs = list(response.field_responses.select_related("field"))
        value_lookup = {}
        for fr in frs:
            if fr.field.field_type not in HIDDEN_PREVIEW_TYPES:
                value_lookup[fr.field.code] = _format_field_response(fr)

        fields = []
        total = 0
        invalid = 0
        for fr in frs:
            field = fr.field
            if field.field_type in HIDDEN_PREVIEW_TYPES:
                continue
            raw = fr.typed_value()
            valid, msg = engine.validate_field(field, raw)
            total += 1
            if not valid:
                invalid += 1
            fields.append(
                {
                    "field": field,
                    "choices": list(
                        field.choices.filter(is_active=True).order_by("sort_order")
                    ),
                    "value": _escape_form_value(raw),
                    "display_value": _format_field_response(fr),
                    "file_url": fr.file or "",
                    "is_required": field.is_required,
                    "validations": list(
                        field.validations.filter(is_active=True).order_by("sort_order")
                    ),
                    "visibility": list(
                        field.visibility_rules.filter(is_active=True).order_by("sort_order")
                    ),
                    "force_visible": True,
                    "is_visible": _field_is_visible(field, value_lookup),
                    "is_valid": valid,
                    "validation_msg": msg,
                    "review_validation": {"valid": valid, "msg": msg},
                }
            )

        visible_fields = [f for f in fields if f["is_visible"]]
        groups.append(
            {
                "section": response.section,
                "response": response,
                "repeat_index": response.repeat_index,
                "is_complete": response.is_complete,
                "fields": visible_fields,
                "hidden_count": len(fields) - len(visible_fields),
                "summary": {
                    "total": total,
                    "invalid": invalid,
                    "valid": total - invalid,
                },
            }
        )
    return groups


# ---------------------------------------------------------------------------
# Manual review system (section checklist + findings + offline PDF content)
# ---------------------------------------------------------------------------

MANUAL_SECTION_DEFS = [
    {"code": "application_info", "title": "Application Information", "icon": "ti-school"},
    {"code": "personal_info", "title": "Personal & Contact", "icon": "ti-user"},
    {"code": "academics", "title": "Academic Information", "icon": "ti-books"},
    {"code": "documents", "title": "Documents", "icon": "ti-files"},
    {"code": "essays", "title": "Essays", "icon": "ti-writing"},
    {"code": "additional", "title": "Other Information", "icon": "ti-dots"},
]


def _load_offline_pages(app):
    """Return cached extracted pages for the offline PDF, extracting on first use."""
    if app.offline_form_text:
        return app.offline_form_text
    if not app.offline_form_pdf or not app.offline_form_pdf.name:
        return []
    from Applicants.services.pdf_extractor import extract_pdf_pages

    try:
        with app.offline_form_pdf.open("rb") as fh:
            pages = extract_pdf_pages(fh)
    except Exception:
        logger.exception("Could not read offline PDF for app %s", app.Reference_id)
        pages = []
    if pages:
        app.offline_form_text = pages
        app.offline_form_extracted_at = timezone.now()
        app.save(
            update_fields=[
                "offline_form_text",
                "offline_form_extracted_at",
                "updated_date",
            ]
        )
    return pages


def build_manual_review_context(app, assignment):
    """Build the section checklist + findings + offline PDF content for the
    manual review workspace.

    `assignment` may be None (the page shows the materials checklist only).
    """
    reviews = {}
    if assignment is not None:
        reviews = {
            r.section_code: r
            for r in assignment.section_reviews.all()
        }

    offline_pages = []
    offline_text_available = False
    if app.apply_method == "offline" and app.offline_form_pdf:
        offline_pages = _load_offline_pages(app)
        offline_text_available = any(p.get("text") for p in offline_pages)

    sections = []
    for i, d in enumerate(MANUAL_SECTION_DEFS):
        rev = reviews.get(d["code"])
        status = rev.status if rev else "not_reviewed"
        note = rev.note if rev else ""
        sections.append(
            {
                "code": d["code"],
                "title": d["title"],
                "icon": d["icon"],
                "status": status,
                "note": note,
                "reviewed_by": rev.reviewed_by if rev else None,
                "reviewed_at": rev.reviewed_at if rev else None,
                "is_offline": app.apply_method == "offline",
            }
        )

    reviewed = sum(1 for s in sections if s["status"] == "reviewed")
    issue = sum(1 for s in sections if s["status"] == "issue")
    pending = len(sections) - reviewed - issue

    findings = [
        {
            "section_code": s["code"],
            "section_title": s["title"],
            "note": s["note"],
            "reviewed_by": s["reviewed_by"],
            "reviewed_at": s["reviewed_at"],
        }
        for s in sections
        if s["status"] == "issue"
    ]

    return {
        "manual_sections": sections,
        "manual_progress": {
            "reviewed": reviewed,
            "issue": issue,
            "pending": pending,
            "total": len(sections),
            "pct": round((reviewed + issue) / len(sections) * 100) if sections else 0,
        },
        "findings": findings,
        "offline_pages": offline_pages,
        "offline_text_available": offline_text_available,
        "offline_test_scores": app.offline_extracted_test_scores or [],
        "offline_pdf_name": (
            app.offline_form_pdf.name if app.offline_form_pdf else ""
        ),
    }
