import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable

from ..constants import UW_RED_RGB


class PDFWriter:

    def __init__(self, title="", landscape_mode=True):
        self.buffer = io.BytesIO()
        page_size = landscape(letter) if landscape_mode else letter
        self.doc = SimpleDocTemplate(
            self.buffer, pagesize=page_size,
            rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
        )
        self.styles = getSampleStyleSheet()
        self.elements = []
        self.uw_red = colors.Color(*UW_RED_RGB)

    def add_title(self, text, font_size=18):
        style = ParagraphStyle(
            "Title2", parent=self.styles["Title"],
            textColor=self.uw_red, fontSize=font_size, spaceAfter=4
        )
        self.elements.append(Paragraph(text, style))

    def add_info(self, text, font_size=11):
        style = ParagraphStyle(
            "Info", parent=self.styles["Normal"],
            fontSize=font_size, spaceAfter=2
        )
        self.elements.append(Paragraph(text, style))

    def add_spacer(self, height=12):
        self.elements.append(Spacer(1, height))

    def add_hr(self):
        self.elements.append(HRFlowable(width="100%", thickness=1, color=self.uw_red))

    def add_table(self, data, font_size=8, repeat_rows=1):
        table = Table(data, repeatRows=repeat_rows)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.uw_red),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), font_size),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.Color(0.8, 0.8, 0.8)),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        self.elements.append(table)

    def add_paragraph(self, text, font_size=10, bold=False):
        style = ParagraphStyle(
            "Custom", parent=self.styles["Normal"],
            fontSize=font_size, spaceAfter=3
        )
        prefix = "<b>" if bold else ""
        suffix = "</b>" if bold else ""
        self.elements.append(Paragraph(f"{prefix}{text}{suffix}", style))

    def build(self):
        self.doc.build(self.elements)
        self.buffer.seek(0)
        return self.buffer
