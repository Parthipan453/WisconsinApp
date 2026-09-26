"""Extract text from uploaded PDFs (offline application forms).

Best effort only: a text-layer PDF (digital form) extracts cleanly, while a
scanned/handwritten form has no text layer and returns empty pages. For the
latter the reviewer still has the original "Open PDF" button and the manual
review notes.

Available engine: PyMuPDF (fitz).
"""

import logging

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    fitz = None


def extract_pdf_pages(file_path) -> list:
    """Return [{page_number, text, widgets}] for a PDF at path/file-like.

    ``widgets`` lists the AcroForm fields on the page with any filled values
    as [{name, label, value}], which lets reviewers see typed answers to
    checkbox/radio/select fields that do not appear in the plain text layer.

    Returns an empty list if the engine is unavailable or the file cannot be
    opened. Never raises for the caller.
    """
    if fitz is None:
        return []
    try:
        if hasattr(file_path, "read"):
            pdf = fitz.open(stream=file_path.read(), filetype="pdf")
        else:
            pdf = fitz.open(file_path)
        pages = []
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()
            widgets = _page_widgets(page)
            pages.append(
                {
                    "page_number": page_number,
                    "text": text,
                    "widgets": widgets,
                }
            )
        pdf.close()
        return pages
    except Exception:
        logger.exception("PDF text extraction failed for %r", file_path)
        return []


def _page_widgets(page) -> list:
    """Read AcroForm fields from a page, ignoring empty ones."""
    widgets = []
    try:
        for widget in page.widgets():
            name = widget.field_name or ""
            if not name:
                continue
            value = widget.field_value
            if value is None or value == "" or value == "Off":
                continue
            if isinstance(value, bool):
                value = "Yes" if value else "No"
            widgets.append(
                {
                    "name": name,
                    "label": name.split(".", 1)[-1],
                    "value": str(value),
                }
            )
    except Exception:
        logger.exception("PDF widget extraction failed for a page")
        return []
    return widgets


def extract_all_text(file_path) -> str:
    """Return the full document text (pages joined by blank lines)."""
    return "\n\n".join(
        page["text"] for page in extract_pdf_pages(file_path) if page["text"]
    )
