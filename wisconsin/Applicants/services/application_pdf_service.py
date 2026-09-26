"""Downloadable PDFs for submitted applicant applications."""

import json
from io import BytesIO
from math import ceil
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..models import Application, FormField
from .form_engine import DynamicFormEngine


UW_RED = colors.HexColor("#C5050C")
UW_NAVY = colors.HexColor("#062B60")
TEXT = colors.HexColor("#172033")


class ApplicationPdfService:
    """Creates applicant-facing PDFs directly from the saved application."""

    def build_next_steps_pdf(self, application: Application) -> bytes:
        university_name = getattr(application.university, "university_name", "Universities of Wisconsin")
        contact_email = getattr(application.university, "official_email", "") or "contact@go.wisconsin.edu"
        contact_phone = getattr(application.university, "phone_number", "")
        contact_website = getattr(application.university, "website", "")
        term = self._term(application)

        story = [
            self._title("Congratulations!"),
            Paragraph(
                f"Your application to <b>{escape(university_name)}</b> has been submitted successfully. "
                "Thank you for taking this important next step.",
                self._styles()["app_pdf_lead"],
            ),
            Spacer(1, 18),
            self._section("Application summary"),
            self._summary_table(application),
            Spacer(1, 22),
            self._section("What's next?"),
            Paragraph(
                "Your application will be reviewed by the admissions team. Please monitor "
                "your applicant portal for updates, outstanding materials, and important deadlines.",
                self._styles()["app_pdf_body"],
            ),
            Spacer(1, 10),
            Paragraph(
                "If you still need to provide transcripts, test scores, or other required materials, "
                "submit them through the Applicant Portal as soon as possible.",
                self._styles()["app_pdf_body"],
            ),
            Spacer(1, 18),
            self._section("Contact admissions"),
            Paragraph(
                self._contact_text(university_name, contact_email, contact_phone, contact_website),
                self._styles()["app_pdf_body"],
            ),
            Spacer(1, 24),
            Paragraph("Go Wisconsin", self._styles()["app_pdf_signoff"]),
        ]
        return self._build(story, "Next Steps")

    def build_application_pdf(self, application: Application) -> bytes:
        story = [
            self._receipt_title("Your Universities of Wisconsin<br/>Application Receipt"),
            Spacer(1, 16),
            self._receipt_section("Your Application Info"),
            self._receipt_subsection("APPLICATION TYPE"),
            self._receipt_grid([
                ("Application Type", application.get_applicant_type_display()),
                ("Academic Level", getattr(application.degree_level, "get_level_display", lambda: "")()),
                ("University", getattr(application.university, "university_name", "")),
                ("School", getattr(application.school, "school_name", "")),
                ("Program", getattr(application.program, "program_name", "")),
                ("Campus", application.campus_name),
                ("Starting Term", self._term(application)),
            ]),
        ]

        responses = (
            application.form_responses.select_related("form", "section")
            .prefetch_related("field_responses__field")
            .order_by("form__sort_order", "section__sort_order", "repeat_index")
        )
        current_form_id = None
        found_response = False
        for response in responses:
            values = []
            for field_response in response.field_responses.all().order_by("field__sort_order"):
                field = field_response.field
                values.append((field.label, self._display_value(field_response, field), field.layout_width))
            if not values:
                continue
            found_response = True
            if response.form_id != current_form_id:
                story.extend([
                    PageBreak(),
                    self._receipt_section(f"Your {response.form.name}"),
                ])
                current_form_id = response.form_id
            section_title = response.section.title
            if response.repeat_index:
                section_title += f" ({response.repeat_index + 1})"
            story.extend([
                self._receipt_subsection(section_title.upper()),
                self._receipt_grid(values),
                Spacer(1, 20),
            ])

        if not found_response:
            story.append(Paragraph("No form responses were recorded for this application.", self._styles()["app_pdf_body"]))
        story.extend([
            Spacer(1, 10),
            self._receipt_subsection("E-PAYMENT INFO"),
            self._receipt_grid([("E-Payment Status", self._payment_status(application))]),
            Spacer(1, 16),
            self._receipt_subsection("ELECTRONIC SIGNATURE INFO"),
            self._receipt_grid([
                ("Date", self._submitted_at(application)),
                ("Name", application.signature or "Not provided"),
            ]),
        ])
        return self._build(story, "Submitted Application", application=application, receipt=True)

    def build_offline_application_pdf(self, application: Application) -> bytes:
        """Fillable offline application form (AcroForm PDF).

        Every active form field becomes a real PDF form field (text box,
        dropdown, checkbox, or radio group) so the applicant can type answers
        directly in any PDF viewer. The uploaded copy keeps those values in the
        form fields, which the review tooling reads back out.
        """
        engine = DynamicFormEngine()
        forms = engine.get_forms_for_application(application)
        steps = engine.get_active_workflow_steps(application)

        output = BytesIO()
        canvas = Canvas(output, pagesize=letter)
        canvas.setTitle("Universities of Wisconsin - Offline Application Form")
        canvas.setAuthor("Universities of Wisconsin")
        painter = _FormPainter(canvas, application)
        painter.draw_cover(steps)
        painter.draw_forms(forms)
        painter.draw_signature()
        canvas.save()
        return output.getvalue()

    @staticmethod
    def _make_table(*args, **kwargs) -> Table:
        table = Table(*args, **kwargs)
        table.hAlign = "LEFT"
        return table

    def _choice_row(self, label, label_width=4.5 * inch) -> Table:
        box = self._make_table([[""]], colWidths=[10], rowHeights=[10])
        box.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#8A93A2")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        row = self._make_table(
            [[box, Paragraph(label, self._styles()["app_pdf_choice"])]],
            colWidths=[10, label_width],
        )
        row.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (0, 0), 0),
            ("RIGHTPADDING", (1, 0), (1, 0), 0),
            ("LEFTPADDING", (1, 0), (1, 0), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        return row

    def _build(self, story, document_title: str, application=None, receipt=False) -> bytes:
        output = BytesIO()
        document = SimpleDocTemplate(
            output,
            pagesize=letter,
            rightMargin=0.65 * inch,
            leftMargin=0.65 * inch,
            topMargin=1.35 * inch if receipt else 0.8 * inch,
            bottomMargin=0.65 * inch,
            title=document_title,
            author="Universities of Wisconsin",
        )
        on_page = (
            lambda canvas, doc: self._receipt_header(canvas, doc, application)
            if receipt
            else self._page_header
        )
        document.build(story, onFirstPage=on_page, onLaterPages=on_page)
        return output.getvalue()

    @staticmethod
    def _page_header(canvas, document) -> None:
        canvas.saveState()
        width, height = letter
        canvas.setFillColor(UW_NAVY)
        canvas.rect(0, height - 0.38 * inch, width, 0.38 * inch, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(0.65 * inch, height - 0.25 * inch, "UNIVERSITIES OF WISCONSIN")
        canvas.setFillColor(colors.HexColor("#606B7A"))
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(width - 0.65 * inch, 0.35 * inch, f"Page {document.page}")
        canvas.restoreState()

    def _receipt_header(self, canvas, document, application: Application) -> None:
        canvas.saveState()
        width, height = letter
        left = 0.65 * inch
        right = width - 0.65 * inch
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(2)
        canvas.line(left, height - 0.2 * inch, right, height - 0.2 * inch)
        canvas.setFillColor(colors.black)
        canvas.setFont("Helvetica", 7.5)
        applicant_name = f"{application.applicant.first_name} {application.applicant.last_name}".strip()
        left_lines = [
            f"Applicant: {applicant_name}",
            f"Application ID: {application.Reference_id}",
            f"Submitted Date: {self._submitted_at(application)}",
        ]
        right_lines = [
            f"Campus: {getattr(application.university, 'university_name', '')}",
            f"Semester: {self._term(application)}",
            f"Major/Program: {getattr(application.program, 'program_name', '')}",
        ]
        y = height - 0.45 * inch
        for line in left_lines:
            canvas.drawString(left, y, line)
            y -= 0.16 * inch
        y = height - 0.45 * inch
        for line in right_lines:
            canvas.drawString(left + 3.35 * inch, y, line)
            y -= 0.16 * inch
        canvas.setStrokeColor(colors.black)
        canvas.setLineWidth(2)
        canvas.line(left, height - 1.05 * inch, right, height - 1.05 * inch)
        canvas.setFillColor(colors.HexColor("#606B7A"))
        canvas.setFont("Helvetica", 7.5)
        canvas.drawRightString(right, 0.35 * inch, f"Page {document.page}")
        canvas.restoreState()

    def _summary_table(self, application: Application) -> Table:
        return self._value_table([
            ("Application reference", application.Reference_id),
            ("University", getattr(application.university, "university_name", "")),
            ("School", getattr(application.school, "school_name", "")),
            ("Program", getattr(application.program, "program_name", "")),
            ("Degree", getattr(application.degree_level, "degree_name", "")),
            ("Campus", application.campus_name),
            ("Applicant type", application.get_applicant_type_display()),
            ("Starting term", self._term(application)),
            ("Submitted", self._submitted_at(application)),
        ])

    def _value_table(self, values) -> Table:
        styles = self._styles()
        rows = [
            [Paragraph(f"<b>{escape(str(label))}</b>", styles["app_pdf_table_label"]), Paragraph(escape(str(value or "-")), styles["app_pdf_table_value"])]
            for label, value in values
            if value is not None
        ]
        table = self._make_table(rows, colWidths=[1.75 * inch, 4.85 * inch], repeatRows=0)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F5F7")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D8DEE6")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        return table

    def _receipt_grid(self, values) -> Table:
        styles = self._styles()
        rows, pending, full_rows = [], None, []
        for item in values:
            label, value = item[0], item[1]
            width = item[2] if len(item) > 2 else "half"
            cell = Paragraph(
                f"{escape(str(label))}: <b>{escape(str(value or '-'))}</b>",
                styles["app_pdf_receipt_value"],
            )
            if width == "full":
                if pending:
                    rows.append([pending, ""])
                    pending = None
                rows.append([cell, ""])
                full_rows.append(len(rows) - 1)
            elif pending:
                rows.append([pending, cell])
                pending = None
            else:
                pending = cell
        if pending:
            rows.append([pending, ""])
        table = self._make_table(rows, colWidths=[3.25 * inch, 3.25 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F1F1")),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9D9D9")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        for index in full_rows:
            table.setStyle(TableStyle([("SPAN", (0, index), (1, index))]))
        return table

    @staticmethod
    def _payment_status(application: Application) -> str:
        payment = application.payments.order_by("-created_at").first()
        if not payment:
            return "Not paid"
        return payment.get_status_display()

    @staticmethod
    def _term(application: Application) -> str:
        cycle = application.admission_cycle
        return " ".join(filter(None, (getattr(cycle, "term", ""), getattr(cycle, "academic_year", ""))))

    @staticmethod
    def _submitted_at(application: Application) -> str:
        submitted_at = application.submitted_date
        if not submitted_at:
            return ""
        return (
            f"{submitted_at.strftime('%B')} {submitted_at.day}, {submitted_at.year}, "
            f"{submitted_at.strftime('%I').lstrip('0')}:{submitted_at.strftime('%M %p')}"
        )

    @staticmethod
    def _contact_text(university_name, email, phone, website) -> str:
        details = [f"<b>{escape(university_name)} Admissions</b>", f"Email: {escape(email)}"]
        if phone:
            details.append(f"Phone: {escape(phone)}")
        if website:
            details.append(f"Website: {escape(website)}")
        return "<br/>".join(details)

    @staticmethod
    def _display_value(field_response, field) -> str:
        if field.is_encrypted or field.code.lower() in {"ssn", "password"}:
            return "Protected"
        if field_response.file_name:
            return field_response.file_name
        value = field_response.typed_value()
        if isinstance(value, bool):
            return "Yes" if value else "No"
        if isinstance(value, (list, dict)):
            return ", ".join(map(str, value)) if isinstance(value, list) else json.dumps(value)
        return str(value or "")

    @staticmethod
    def _styles():
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="app_pdf_title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=26, leading=31, textColor=TEXT, spaceAfter=12))
        styles.add(ParagraphStyle(name="app_pdf_lead", parent=styles["BodyText"], fontName="Helvetica", fontSize=14, leading=18, textColor=TEXT))
        styles.add(ParagraphStyle(name="app_pdf_section", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=17, leading=22, textColor=TEXT, spaceBefore=4, spaceAfter=9))
        styles.add(ParagraphStyle(name="app_pdf_body", parent=styles["BodyText"], fontName="Helvetica", fontSize=10.5, leading=15, textColor=TEXT))
        styles.add(ParagraphStyle(name="app_pdf_table_label", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13, textColor=TEXT))
        styles.add(ParagraphStyle(name="app_pdf_table_value", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13, textColor=TEXT))
        styles.add(ParagraphStyle(name="app_pdf_signoff", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=UW_RED))
        styles.add(ParagraphStyle(name="app_pdf_receipt_title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=15, leading=22, textColor=colors.black, spaceAfter=4))
        styles.add(ParagraphStyle(name="app_pdf_receipt_section", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=16, leading=21, textColor=colors.black, spaceBefore=4, spaceAfter=14))
        styles.add(ParagraphStyle(name="app_pdf_receipt_subsection", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=9.5, leading=13, textColor=colors.black, spaceBefore=3, spaceAfter=6))
        styles.add(ParagraphStyle(name="app_pdf_receipt_value", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.3, leading=11, textColor=colors.black))
        styles.add(ParagraphStyle(name="app_pdf_field_label", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=TEXT))
        styles.add(ParagraphStyle(name="app_pdf_heading", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=9.5, leading=13, textColor=UW_NAVY, spaceBefore=6, spaceAfter=2))
        styles.add(ParagraphStyle(name="app_pdf_choice", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.5, leading=11, textColor=TEXT))
        styles.add(ParagraphStyle(name="app_pdf_hint", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.5, leading=10, textColor=colors.HexColor("#606B7A")))
        styles.add(ParagraphStyle(name="app_pdf_help", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.5, leading=10, textColor=colors.HexColor("#606B7A")))
        return styles

    def _title(self, text: str) -> Paragraph:
        return Paragraph(text, self._styles()["app_pdf_title"])

    def _section(self, text: str) -> Paragraph:
        return Paragraph(text, self._styles()["app_pdf_section"])

    def _receipt_title(self, text: str) -> Paragraph:
        return Paragraph(text, self._styles()["app_pdf_receipt_title"])

    def _receipt_section(self, text: str) -> Paragraph:
        return Paragraph(text, self._styles()["app_pdf_receipt_section"])

    def _receipt_subsection(self, text: str) -> Paragraph:
        return Paragraph(text, self._styles()["app_pdf_receipt_subsection"])


class _FormPainter:
    """Draws the fillable offline application form onto a ReportLab canvas.

    Every dynamic-form field becomes a real PDF AcroForm widget (text field,
    dropdown, checkbox, or radio group) with a deterministic name of the form
    ``<section_code>.<field_code>`` so the offline parser can map filled values
    back to field codes.
    """

    LEFT = 0.65 * inch
    RIGHT = letter[0] - 0.65 * inch
    WIDTH = RIGHT - LEFT
    TOP = letter[1] - 1.35 * inch - 14
    BOTTOM = 0.65 * inch
    LINE = colors.HexColor("#8A93A2")
    FAINT = colors.HexColor("#606B7A")
    INK = TEXT

    LABEL_SIZE = 8.5
    LABEL_LEADING = 11.5
    BOX_H = 20
    FIELD_GAP = 12

    def __init__(self, canvas: Canvas, application: Application) -> None:
        self.c = canvas
        self.af = canvas.acroForm
        self.application = application
        self.page_no = 0
        self.y = 0
        self._new_page()


    def _new_page(self) -> None:
        if self.page_no:
            self.c.showPage()
        self.page_no += 1
        self.y = self.TOP
        app = self.application
        applicant_name = f"{app.applicant.first_name} {app.applicant.last_name}".strip()
        c = self.c
        c.saveState()
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.line(self.LEFT, letter[1] - 0.2 * inch, self.RIGHT, letter[1] - 0.2 * inch)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(colors.black)
        y = letter[1] - 0.45 * inch
        for line in (
            f"Applicant: {applicant_name}",
            f"Application ID: {app.Reference_id}",
            "Form: Offline Application",
        ):
            c.drawString(self.LEFT, y, line)
            y -= 0.16 * inch
        y = letter[1] - 0.45 * inch
        for line in (
            f"Campus: {getattr(app.university, 'university_name', '')}",
            f"Term: {ApplicationPdfService._term(app)}",
            f"Program: {getattr(app.program, 'program_name', '')}",
        ):
            c.drawString(self.LEFT + 3.35 * inch, y, line)
            y -= 0.16 * inch
        c.setLineWidth(2)
        c.line(self.LEFT, letter[1] - 1.05 * inch, self.RIGHT, letter[1] - 1.05 * inch)
        c.setFillColor(self.FAINT)
        c.drawRightString(self.RIGHT, 0.35 * inch, f"Page {self.page_no}")
        c.restoreState()

    def ensure(self, height) -> None:
        if self.y - height < self.BOTTOM:
            self._new_page()


    @staticmethod
    def _wrap(text, font, size, width):
        words = str(text).split()
        lines, cur = [], ""
        for word in words:
            trial = (cur + " " + word).strip()
            if stringWidth(trial, font, size) <= width:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines or [""]

    def _text(self, text, x, y, font="Helvetica", size=8.5, color=None, width=None, leading=None):
        color = color or self.INK
        leading = leading or size + 2
        width = width or (self.RIGHT - x)
        for line in self._wrap(text, font, size, width):
            self.c.setFont(font, size)
            self.c.setFillColor(color)
            self.c.drawString(x, y, line)
            y -= leading
        return y

    def _is_required(self, field) -> bool:
        return field.is_required or field.validations.filter(
            validation_type="required", is_active=True
        ).exists()


    def _label_lines(self, field, lines, x, top):
        required = self._is_required(field)
        y = top
        for i, line in enumerate(lines):
            self.c.setFont("Helvetica-Bold", self.LABEL_SIZE)
            self.c.setFillColor(self.INK)
            self.c.drawString(x, y, line)
            if required and i == len(lines) - 1:
                self.c.setFillColor(UW_RED)
                self.c.drawString(
                    x + stringWidth(line, "Helvetica-Bold", self.LABEL_SIZE) + 2,
                    y,
                    "*",
                )
            y -= self.LABEL_LEADING
        return y


    @staticmethod
    def _box_height(field) -> int:
        if field.field_type in ("textarea", "rich_text"):
            return max(field.rows or 4, 3) * 13 + 8
        return _FormPainter.BOX_H

    def _field_height(self, field, width) -> int:
        if field.field_type == "radio":
            return self._radio_rows(field, width) * 20 + 6
        if field.field_type == "checkbox":
            label_width = max(width - 18, 1)
            return len(self._wrap(field.label, "Helvetica-Bold", self.LABEL_SIZE, label_width)) * self.LABEL_LEADING + 4
        return self._box_height(field)

    @staticmethod
    def _hint(field) -> str:
        if field.field_type == "date":
            return "(MM/DD/YYYY)"
        if field.field_type == "year":
            return "(YYYY)"
        return ""

    def _field_flags(self, field, base) -> str:
        flags = base
        if self._is_required(field):
            flags = (flags + " required").strip()
        return flags

    def _radio_rows(self, field, width) -> int:
        total = sum(
            stringWidth(choice.label or "", "Helvetica", 8.5) + 20
            for choice in field.choices.filter(is_active=True).order_by("sort_order")
        )
        return max(1, ceil(total / max(width, 1)))

    def draw_field(self, section_code, field, x=None, width=None) -> None:
        x = x or self.LEFT
        width = width or self.WIDTH
        ftype = field.field_type
        if ftype == "hidden":
            return
        if ftype == "heading":
            self.ensure(42)
            self.y -= 12
            self.y = self._text(field.label, x, self.y, font="Helvetica-Bold", size=9.5, color=UW_NAVY, width=width)
            self.y -= 10
            return
        if ftype == "file":
            self.ensure(34)
            self.y = self._text(field.label, x, self.y, font="Helvetica-Bold", size=self.LABEL_SIZE, color=self.INK, width=width)
            self.y = self._text(
                "Attach the required document (PDF, DOC, JPG, PNG) through the online applicant portal.",
                x, self.y, font="Helvetica", size=7.5, color=self.FAINT, width=width,
            )
            self.y -= 8
            return
        if ftype == "checkbox":
            height = self._field_height(field, width)
            self.ensure(height + self.FIELD_GAP)
            top = self.y
            self.af.checkbox(size=12, x=x, y=top - 11, name=f"{section_code}.{field.code}",
                             tooltip=field.label, borderColor=self.LINE,
                             fieldFlags=self._field_flags(field, ""))
            label_lines = self._wrap(field.label, "Helvetica-Bold", self.LABEL_SIZE, width - 18)
            self._label_lines(field, label_lines, x + 18, top - 1)
            self.y = top - height - self.FIELD_GAP
            return
        label_lines = self._wrap(field.label, "Helvetica-Bold", self.LABEL_SIZE, width)
        if ftype == "radio":
            rows = self._radio_rows(field, width)
            block = (
                len(label_lines) * self.LABEL_LEADING
                + (self.LABEL_LEADING + 2)
                + rows * 20
                + self.FIELD_GAP
            )
            self.ensure(block)
            top = self.y
            self.y = self._label_lines(field, label_lines, x, top)
            last_baseline = top - (len(label_lines) - 1) * self.LABEL_LEADING
            radio_top = last_baseline - self.LABEL_LEADING - 2
            self._radios(f"{section_code}.{field.code}", field, x, radio_top, width)
            self.y = radio_top - rows * 20 - self.FIELD_GAP
            return
        height = self._field_height(field, width)
        block = len(label_lines) * self.LABEL_LEADING + 4 + height + self.FIELD_GAP
        self.ensure(block)
        top = self.y
        self.y = self._label_lines(field, label_lines, x, top)
        self.y -= 4
        box_y = self.y - height
        self._box(section_code, field, x, box_y, width, height)
        self.y = box_y - self.FIELD_GAP

    def draw_field_pair(self, section_code, a, b) -> None:
        gap = 12
        half = (self.WIDTH - gap) / 2
        if a.field_type == "checkbox" or b.field_type == "checkbox":
            self.draw_field(section_code, a)
            self.draw_field(section_code, b)
            return
        ha, hb = self._field_height(a, half), self._field_height(b, half)
        la = self._wrap(a.label, "Helvetica-Bold", self.LABEL_SIZE, half)
        lb = self._wrap(b.label, "Helvetica-Bold", self.LABEL_SIZE, half)
        box_h = max(ha, hb)
        block = max(len(la), len(lb)) * self.LABEL_LEADING + 4 + box_h + self.FIELD_GAP
        self.ensure(block)
        top = self.y
        left_bottom = self._label_lines(a, la, self.LEFT, top)
        right_bottom = self._label_lines(b, lb, self.LEFT + half + gap, top)
        self.y = min(left_bottom, right_bottom) - 4
        box_y = self.y - box_h
        self._box(section_code, a, self.LEFT, box_y, half, ha)
        self._box(section_code, b, self.LEFT + half + gap, box_y, half, hb)
        self.y = box_y - self.FIELD_GAP

    def _box(self, section_code, field, x, y, width, height) -> None:
        name = f"{section_code}.{field.code}"
        tooltip = field.label
        ftype = field.field_type
        hint = self._hint(field)
        af = self.af
        if ftype in ("textarea", "rich_text"):
            af.textfield(x=x, y=y, width=width, height=height, name=name, tooltip=tooltip,
                         fontName="Helvetica", fontSize=9.5, borderColor=self.LINE,
                         fieldFlags=self._field_flags(field, "multiline"))
        elif ftype in ("select", "multi_select"):
            labels = [c.label or "" for c in field.choices.filter(is_active=True).order_by("sort_order")]
            default = field.choices.filter(is_active=True, is_default=True).first()
            if not labels:
                af.textfield(x=x, y=y, width=width, height=height, name=name, tooltip=tooltip,
                             fontName="Helvetica", fontSize=9.5, borderColor=self.LINE,
                             fieldFlags=self._field_flags(field, ""))
            else:
                value = default.label if default else labels[0]
                flags = "combo multiSelect" if ftype == "multi_select" else "combo"
                af.choice(x=x, y=y, width=width, height=height, options=labels,
                          value=value, name=name, tooltip=tooltip,
                          fontSize=9.5, borderColor=self.LINE,
                          fieldFlags=self._field_flags(field, flags))
        elif ftype == "radio":
            self._radios(name, field, x, y + height - 2, width)
        elif ftype == "checkbox":
            af.checkbox(size=12, x=x, y=y + height - 12, name=name, tooltip=tooltip,
                        borderColor=self.LINE, fieldFlags=self._field_flags(field, ""))
        elif ftype == "password":
            af.textfield(x=x, y=y, width=width, height=height, name=name, tooltip=tooltip,
                         fontName="Helvetica", fontSize=9.5, borderColor=self.LINE,
                         fieldFlags=self._field_flags(field, "password"))
        else:
            af.textfield(x=x, y=y, width=width, height=height, name=name, tooltip=tooltip,
                         fontName="Helvetica", fontSize=9.5, borderColor=self.LINE,
                         fieldFlags=self._field_flags(field, ""))
        if hint:
            self.c.setFont("Helvetica", 7)
            self.c.setFillColor(self.FAINT)
            self.c.drawRightString(x + width, y + 2, hint)

    def _radios(self, name, field, x, top, width) -> None:
        size = 12
        cur_x = x
        row_top = top + size
        for choice in field.choices.filter(is_active=True).order_by("sort_order"):
            label = choice.label or ""
            label_w = stringWidth(label, "Helvetica", 8.5) + 4
            if cur_x > x and cur_x + size + 4 + label_w > x + width:
                cur_x = x
                row_top -= 20
            self.af.radio(x=cur_x, y=row_top - size, size=size, name=name,
                          value=choice.value, tooltip=label, borderColor=self.LINE)
            self.c.setFont("Helvetica", 8.5)
            self.c.setFillColor(self.INK)
            self.c.drawString(cur_x + size + 3, row_top - size + 2, label)
            cur_x += size + 4 + label_w


    def draw_cover(self, steps) -> None:
        self.y -= 6
        self.y = self._text("Your Universities of Wisconsin", self.LEFT, self.y,
                            font="Helvetica-Bold", size=20, color=colors.black, width=self.WIDTH)
        self.y -= 2
        self.y = self._text("Offline Application Form", self.LEFT, self.y,
                            font="Helvetica-Bold", size=15, color=UW_NAVY, width=self.WIDTH)
        self.y -= 10
        self.y = self._text(
            "Fill this form out directly in any PDF viewer, then upload the completed "
            "PDF from your applicant portal.",
            self.LEFT, self.y, font="Helvetica", size=8.5, color=self.FAINT, width=self.WIDTH,
        )
        self.y -= 6
        self._section_title("Your Application Info")
        app = self.application
        info = [
            ("Reference ID", app.Reference_id),
            ("Application Type", app.get_applicant_type_display()),
            ("Academic Level", getattr(app.degree_level, "get_level_display", lambda: "")()),
            ("University", getattr(app.university, "university_name", "")),
            ("School", getattr(app.school, "school_name", "")),
            ("Program", getattr(app.program, "program_name", "")),
            ("Campus", app.campus_name),
            ("Starting Term", ApplicationPdfService._term(app)),
        ]
        for label, value in info:
            self.y = self._text(f"{label}: {value or '-'}", self.LEFT, self.y,
                                font="Helvetica", size=8.5, color=self.INK, width=self.WIDTH)
            self.y -= 2
        self.y -= 6
        if steps:
            self._section_title("Your Application Steps")
            self.y = self._text(
                "Work through the steps below, then fill out every section of this form. "
                "Check each box as you finish that step.",
                self.LEFT, self.y, font="Helvetica", size=8.5, color=self.FAINT, width=self.WIDTH,
            )
            self.y -= 8
            for i, step in enumerate(steps):
                self.ensure(22)
                name = step.name
                if step.form:
                    name += f" ({step.form.name})"
                if step.is_required:
                    name += " *"
                self.af.checkbox(size=12, x=self.LEFT, y=self.y - 13, name=f"workflow.step_{i + 1}",
                                 tooltip=name, borderColor=self.LINE, fieldFlags="")
                self.c.setFont("Helvetica", 8.5)
                self.c.setFillColor(self.INK)
                self.c.drawString(self.LEFT + 18, self.y - 13, name)
                self.y -= 22
            self.y -= 10

    def draw_forms(self, forms) -> None:
        engine = DynamicFormEngine()
        found = False
        for form in forms:
            sections = engine.get_sections_for_application(self.application, form=form)
            if not sections:
                continue
            found = True
            for section in sections:
                self._new_page()
                self.y -= 2
                self.y = self._text(f"Your {form.name}", self.LEFT, self.y,
                                    font="Helvetica-Bold", size=16, color=colors.black, width=self.WIDTH)
                self.y -= 14
                self.draw_section(section)
        if not found:
            self.y = self._text(
                "No active application forms are configured for this application yet. "
                "Please check back soon.",
                self.LEFT, self.y, font="Helvetica", size=10, color=self.INK, width=self.WIDTH,
            )

    def draw_section(self, section) -> None:
        fields = list(
            FormField.objects.filter(section=section, is_active=True)
            .select_related("section")
            .prefetch_related("choices")
            .order_by("sort_order")
        )
        self.ensure(32)
        self.y -= 2
        self.y = self._text(section.title.upper(), self.LEFT, self.y,
                            font="Helvetica-Bold", size=9.5, color=colors.black, width=self.WIDTH)
        self.y -= 6
        if section.description:
            self.y = self._text(section.description, self.LEFT, self.y,
                                font="Helvetica", size=7.5, color=self.FAINT, width=self.WIDTH)
        if section.help_text:
            self.y = self._text(section.help_text, self.LEFT, self.y,
                                font="Helvetica", size=7.5, color=self.FAINT, width=self.WIDTH)
        self.y -= 8
        if not fields:
            self.y = self._text("No fields in this section.", self.LEFT, self.y,
                                font="Helvetica", size=7.5, color=self.FAINT, width=self.WIDTH)
            self.y -= 8
            return
        index = 0
        count = len(fields)
        while index < count:
            field = fields[index]
            if field.field_type == "hidden":
                index += 1
                continue
            if (
                field.layout_width == "half"
                and index + 1 < count
                and fields[index + 1].layout_width == "half"
                and fields[index + 1].field_type not in ("hidden", "heading", "file")
            ):
                self.draw_field_pair(section.code, field, fields[index + 1])
                index += 2
            else:
                self.draw_field(section.code, field)
                index += 1
        self.y -= 4

    def _section_title(self, text) -> None:
        self.ensure(24)
        self.y -= 6
        self.y = self._text(text, self.LEFT, self.y,
                            font="Helvetica-Bold", size=10, color=UW_NAVY, width=self.WIDTH)
        self.y -= 6

    def draw_signature(self) -> None:
        self._new_page()
        self.y -= 6
        self.y = self._text("Signature", self.LEFT, self.y,
                            font="Helvetica-Bold", size=16, color=colors.black, width=self.WIDTH)
        self.y -= 14
        y = self.y - 22
        self.af.textfield(x=self.LEFT, y=y, width=4.0 * inch, height=22, name="signature.applicant_signature",
                          tooltip="Applicant Signature", fontSize=10, borderColor=self.LINE, fieldFlags="")
        self.af.textfield(x=self.LEFT + 4.4 * inch, y=y, width=1.6 * inch, height=22, name="signature.date",
                          tooltip="Date", fontSize=10, borderColor=self.LINE, fieldFlags="")
        self.c.setFont("Helvetica-Bold", 8.5)
        self.c.setFillColor(self.INK)
        self.c.drawString(self.LEFT, y - 11, "Applicant Signature")
        self.c.drawString(self.LEFT + 4.4 * inch, y - 11, "Date")
