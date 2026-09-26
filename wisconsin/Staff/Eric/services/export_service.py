from django.http import HttpResponse
from django.utils import timezone

from ..constants import AttendanceStatus
from ..utils.calendar_utils import MONTH_ABBREVIATIONS
from ..utils.excel_export import ExcelWriter
from ..utils.pdf_export import PDFWriter
from ..repositories.attendance_repository import AttendanceRepository
from ..services.statistics_service import StatisticsService


class ExportService:

    def __init__(self):
        self.repo = AttendanceRepository()
        self.stats_service = StatisticsService()

    def format_check_in(self, record):
        return record.check_in.strftime("%H:%M") if record.check_in else ""

    def format_check_out(self, record):
        return record.check_out.strftime("%H:%M") if record.check_out else ""

    def format_hours(self, record):
        return float(record.total_hours_worked) if record.total_hours_worked else ""

    def format_marked_by(self, record):
        return record.marked_by.user.get_full_name() if record.marked_by else ""

    def _make_http_response(self, output, filename, content_type, disposition_type="attachment"):
        resp = HttpResponse(output, content_type=content_type)
        resp["Content-Disposition"] = f'{disposition_type}; filename="{filename}"'
        return resp

    def export_faculty_month_excel(self, faculty_member, export_year, export_month):
        records = self.repo.get_records_for_faculty_month(
            faculty_member, export_year, export_month
        )
        writer = ExcelWriter()
        sheet_title = f"{MONTH_ABBREVIATIONS[export_month]} {export_year}"
        writer.set_title(sheet_title)
        writer.write_headers(["Date", "Day", "Check In", "Check Out", "Status",
                              "Late (min)", "Early (min)", "Hours", "Marked By"])
        for row_idx, rec in enumerate(records, 2):
            writer.write_row(row_idx, [
                rec.date.strftime("%Y-%m-%d"),
                rec.date.strftime("%A"),
                self.format_check_in(rec),
                self.format_check_out(rec),
                rec.get_status_display(),
                rec.late_minutes,
                rec.early_leave_minutes,
                self.format_hours(rec),
                self.format_marked_by(rec),
            ])
        writer.set_column_widths([14, 12, 12, 12, 14, 12, 12, 10, 22])
        full_name = faculty_member.user.get_full_name().replace(" ", "_")
        filename = f"{full_name}_{MONTH_ABBREVIATIONS[export_month]}_{export_year}.xlsx"
        output, _ = writer.get_response(filename)
        return self._make_http_response(output, filename,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    def export_faculty_month_pdf(self, faculty_member, export_year, export_month):
        records = self.repo.get_records_for_faculty_month(
            faculty_member, export_year, export_month
        )
        dept_name = self.stats_service.get_department_name(faculty_member.department_id)
        full_name = faculty_member.user.get_full_name()
        title = f"{full_name} — {MONTH_ABBREVIATIONS[export_month]} {export_year}"

        pdf = PDFWriter(title)
        pdf.add_title(title)
        info = f"{faculty_member.employee_id} &nbsp;|&nbsp; {dept_name} &nbsp;|&nbsp; {MONTH_ABBREVIATIONS[export_month]} {export_year}"
        pdf.add_info(info)
        pdf.add_spacer()
        pdf.add_hr()
        pdf.add_spacer(12)

        header = ["Date", "Day", "Check In", "Check Out", "Status", "Late", "Early", "Hours", "Marked By"]
        data = [header]
        for rec in records:
            data.append([
                rec.date.strftime("%Y-%m-%d"),
                rec.date.strftime("%a"),
                rec.check_in.strftime("%I:%M %p") if rec.check_in else "\u2014",
                rec.check_out.strftime("%I:%M %p") if rec.check_out else "\u2014",
                rec.get_status_display(),
                f"{rec.late_minutes}m" if rec.late_minutes else "\u2014",
                f"{rec.early_leave_minutes}m" if rec.early_leave_minutes else "\u2014",
                f"{float(rec.total_hours_worked):.2f}h" if rec.total_hours_worked else "\u2014",
                rec.marked_by.user.get_full_name() if rec.marked_by else "\u2014",
            ])
        pdf.add_table(data)

        counts = self.stats_service.get_status_counts_from_records(records)
        pdf.add_spacer(16)
        summary = (
            f"<b>Summary:</b> &nbsp; Total: {len(records)} &nbsp;|&nbsp; "
            f"Present: {counts.get('PRESENT', 0)} &nbsp;|&nbsp; "
            f"Absent: {counts.get('ABSENT', 0)} &nbsp;|&nbsp; "
            f"Late: {counts.get('LATE', 0)} &nbsp;|&nbsp; "
            f"On Leave: {counts.get('ON_LEAVE', 0)}"
        )
        pdf.add_paragraph(summary, font_size=10)

        buffer = pdf.build()
        filename = f"{full_name.replace(' ', '_')}_{MONTH_ABBREVIATIONS[export_month]}_{export_year}.pdf"
        return self._make_http_response(buffer, filename, "application/pdf", "inline")

    def export_day_view_excel(self, records, title):
        writer = ExcelWriter()
        writer.set_title(title[:31])
        writer.write_headers(["Date", "Employee ID", "Name", "Department",
                              "Check In", "Check Out", "Status", "Late (min)",
                              "Early (min)", "Hours", "Marked By"])
        dept_cache = {}
        for row_idx, rec in enumerate(records, 2):
            dept_id = rec.faculty.department_id
            if dept_id and dept_id not in dept_cache:
                dept_cache[dept_id] = self.stats_service.get_department_name(dept_id)
            writer.write_row(row_idx, [
                rec.date.strftime("%Y-%m-%d"),
                rec.faculty.employee_id,
                rec.faculty.user.get_full_name(),
                dept_cache.get(dept_id, ""),
                self.format_check_in(rec),
                self.format_check_out(rec),
                rec.get_status_display(),
                rec.late_minutes,
                rec.early_leave_minutes,
                self.format_hours(rec),
                self.format_marked_by(rec),
            ])
        writer.set_column_widths([14, 14, 24, 20, 12, 12, 14, 12, 12, 10, 22])
        filename = f"{title.replace(' ', '_')}.xlsx"
        output, _ = writer.get_response(filename)
        return self._make_http_response(output, filename,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    def export_day_view_pdf(self, records, title):
        pdf = PDFWriter(title)
        pdf.add_title(title, 16)
        pdf.add_spacer(8)
        pdf.add_hr()
        pdf.add_spacer(12)

        dept_cache = {}
        header = ["Date", "ID", "Name", "Dept", "CI", "CO", "Status", "Late", "Early", "Hours"]
        data = [header]
        for rec in records:
            dept_id = rec.faculty.department_id
            if dept_id and dept_id not in dept_cache:
                dept_cache[dept_id] = self.stats_service.get_department_name(dept_id)
            data.append([
                rec.date.strftime("%Y-%m-%d"),
                rec.faculty.employee_id,
                rec.faculty.user.get_full_name(),
                dept_cache.get(dept_id, "")[:12],
                rec.check_in.strftime("%H:%M") if rec.check_in else "\u2014",
                rec.check_out.strftime("%H:%M") if rec.check_out else "\u2014",
                rec.get_status_display(),
                f"{rec.late_minutes}m" if rec.late_minutes else "\u2014",
                f"{rec.early_leave_minutes}m" if rec.early_leave_minutes else "\u2014",
                f"{float(rec.total_hours_worked):.2f}h" if rec.total_hours_worked else "\u2014",
            ])
        pdf.add_table(data, font_size=7)

        counts = self.stats_service.get_status_counts_from_records(records)
        pdf.add_spacer(14)
        summary = (
            f"<b>Summary:</b> &nbsp; Total: {len(records)} &nbsp;|&nbsp; "
            f"Present: {counts.get('PRESENT', 0)} &nbsp;|&nbsp; "
            f"Absent: {counts.get('ABSENT', 0)} &nbsp;|&nbsp; "
            f"Late: {counts.get('LATE', 0)} &nbsp;|&nbsp; "
            f"On Leave: {counts.get('ON_LEAVE', 0)} &nbsp;|&nbsp; "
            f"Half Day: {counts.get('HALF_DAY', 0)}"
        )
        pdf.add_paragraph(summary)

        buffer = pdf.build()
        filename = f"{title.replace(' ', '_')}.pdf"
        return self._make_http_response(buffer, filename, "application/pdf", "inline")

    def _local_time(self, dt):
        return timezone.localtime(dt) if dt else None

    def export_my_attendance_excel(self, records, user, sel_year, sel_month):
        writer = ExcelWriter()
        writer.set_title(f"{MONTH_ABBREVIATIONS[sel_month]} {sel_year}")
        writer.write_headers(["Date", "Day", "Check In", "Check Out", "Hours"])
        for row_idx, rec in enumerate(records, 2):
            ci = self._local_time(rec.check_in)
            co = self._local_time(rec.check_out)
            writer.write_row(row_idx, [
                rec.date.strftime("%Y-%m-%d"),
                rec.date.strftime("%A"),
                ci.strftime("%H:%M") if ci else "",
                co.strftime("%H:%M") if co else "",
                float(rec.total_hours_worked) if rec.total_hours_worked else "",
            ])
        writer.set_column_widths([14, 12, 12, 12, 10])
        filename = f"My_Attendance_{MONTH_ABBREVIATIONS[sel_month]}_{sel_year}.xlsx"
        output, _ = writer.get_response(filename)
        return self._make_http_response(output, filename,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    def export_my_attendance_pdf(self, records, user, sel_year, sel_month):
        title = f"My Attendance — {MONTH_ABBREVIATIONS[sel_month]} {sel_year}"
        pdf = PDFWriter(title)
        pdf.add_title(title)
        info = f"<b>{user.get_full_name()}</b> &nbsp;|&nbsp; {user.email}"
        pdf.add_info(info)
        pdf.add_spacer(12)
        pdf.add_hr()
        pdf.add_spacer(12)

        data = [["Date", "Day", "Check In", "Check Out", "Hours"]]
        for rec in records:
            ci = self._local_time(rec.check_in)
            co = self._local_time(rec.check_out)
            data.append([
                rec.date.strftime("%Y-%m-%d"),
                rec.date.strftime("%a"),
                ci.strftime("%I:%M %p") if ci else "\u2014",
                co.strftime("%I:%M %p") if co else "\u2014",
                f"{float(rec.total_hours_worked):.2f}h" if rec.total_hours_worked else "\u2014",
            ])
        pdf.add_table(data)

        total = len(records)
        checked = sum(1 for r in records if r.check_in)
        hours = sum((float(r.total_hours_worked) if r.total_hours_worked else 0) for r in records)
        pdf.add_spacer(16)
        summary = f"<b>Summary:</b> &nbsp; Total: {total} &nbsp;|&nbsp; Days worked: {checked} &nbsp;|&nbsp; Total hours: {hours:.2f}h"
        pdf.add_paragraph(summary)

        buffer = pdf.build()
        filename = f"My_Attendance_{MONTH_ABBREVIATIONS[sel_month]}_{sel_year}.pdf"
        return self._make_http_response(buffer, filename, "application/pdf", "inline")

    def export_my_attendance_range_excel(self, records, user, title):
        writer = ExcelWriter()
        writer.set_title(title[:31])
        writer.write_headers(["Date", "Day", "Check In", "Check Out", "Hours"])
        for row_idx, rec in enumerate(records, 2):
            ci = self._local_time(rec.check_in)
            co = self._local_time(rec.check_out)
            writer.write_row(row_idx, [
                rec.date.strftime("%Y-%m-%d"),
                rec.date.strftime("%A"),
                ci.strftime("%H:%M") if ci else "",
                co.strftime("%H:%M") if co else "",
                float(rec.total_hours_worked) if rec.total_hours_worked else "",
            ])
        writer.set_column_widths([14, 12, 12, 12, 10])
        filename = f"{title.replace(' ', '_')}.xlsx"
        output, _ = writer.get_response(filename)
        return self._make_http_response(output, filename,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    def export_my_attendance_range_pdf(self, records, user, title):
        pdf = PDFWriter(title)
        pdf.add_title(title)
        info = f"<b>{user.get_full_name()}</b> &nbsp;|&nbsp; {user.email}"
        pdf.add_info(info)
        pdf.add_spacer(12)
        pdf.add_hr()
        pdf.add_spacer(12)

        data = [["Date", "Day", "Check In", "Check Out", "Hours"]]
        for rec in records:
            ci = self._local_time(rec.check_in)
            co = self._local_time(rec.check_out)
            data.append([
                rec.date.strftime("%Y-%m-%d"),
                rec.date.strftime("%a"),
                ci.strftime("%I:%M %p") if ci else "\u2014",
                co.strftime("%I:%M %p") if co else "\u2014",
                f"{float(rec.total_hours_worked):.2f}h" if rec.total_hours_worked else "\u2014",
            ])
        pdf.add_table(data)

        total = len(records)
        checked = sum(1 for r in records if r.check_in)
        hours = sum((float(r.total_hours_worked) if r.total_hours_worked else 0) for r in records)
        pdf.add_spacer(16)
        summary = f"<b>Summary:</b> &nbsp; Total: {total} &nbsp;|&nbsp; Days worked: {checked} &nbsp;|&nbsp; Total hours: {hours:.2f}h"
        pdf.add_paragraph(summary)

        buffer = pdf.build()
        filename = f"{title.replace(' ', '_')}.pdf"
        return self._make_http_response(buffer, filename, "application/pdf", "inline")
