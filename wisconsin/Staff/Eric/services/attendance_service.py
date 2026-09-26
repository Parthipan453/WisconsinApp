from datetime import datetime

from django.db import transaction
from django.utils import timezone

from ..constants import EXPECTED_START_MINUTES, EXPECTED_END_MINUTES
from ..models import StaffAttendance
from ..repositories.attendance_repository import AttendanceRepository
from ..repositories.holiday_repository import HolidayRepository
from ..validators import parse_time, get_staff_profile


class AttendanceService:

    def __init__(self):
        self.repo = AttendanceRepository()
        self.holiday_repo = HolidayRepository()

    def calculate_working_hours(self, check_in_time, check_out_time):
        total_hours = None
        minutes_late = 0
        minutes_early = 0
        if check_in_time and check_out_time:
            ci_mins = check_in_time.hour * 60 + check_in_time.minute
            co_mins = check_out_time.hour * 60 + check_out_time.minute
            if co_mins > ci_mins:
                total_hours = round((co_mins - ci_mins) / 60, 2)
        if check_in_time:
            ci_mins = check_in_time.hour * 60 + check_in_time.minute
            if ci_mins > EXPECTED_START_MINUTES:
                minutes_late = ci_mins - EXPECTED_START_MINUTES
        if check_out_time:
            co_mins = check_out_time.hour * 60 + check_out_time.minute
            if EXPECTED_END_MINUTES > co_mins:
                minutes_early = EXPECTED_END_MINUTES - co_mins
        return total_hours, minutes_late, minutes_early

    @transaction.atomic
    def mark_attendance_bulk(self, request, selected_date, faculty_ids,
                             check_in_values, check_out_values, status_values):
        staff_profile = get_staff_profile(request)
        if not staff_profile:
            return 0

        records_to_update = []
        number_updated = 0

        for index, faculty_id in enumerate(faculty_ids):
            ci_raw = check_in_values[index].strip() if index < len(check_in_values) and check_in_values[index] else ""
            co_raw = check_out_values[index].strip() if index < len(check_out_values) and check_out_values[index] else ""
            st_raw = status_values[index].strip() if index < len(status_values) and status_values[index] else ""

            if not ci_raw and not co_raw and not st_raw:
                continue

            record, _ = self.repo.get_or_create_record(faculty_id, selected_date)
            ci_time = parse_time(ci_raw)
            co_time = parse_time(co_raw)

            record.check_in = ci_time
            record.check_out = co_time
            if st_raw:
                record.status = st_raw
            record.marked_by = staff_profile
            record.total_hours_worked, record.late_minutes, record.early_leave_minutes = \
                self.calculate_working_hours(ci_time, co_time)
            records_to_update.append(record)
            number_updated += 1

        if records_to_update:
            self.repo.bulk_update_records(
                records_to_update,
                ["check_in", "check_out", "status", "marked_by",
                 "total_hours_worked", "late_minutes", "early_leave_minutes"]
            )
        return number_updated

    @transaction.atomic
    def update_single_record(self, record, check_in_str, check_out_str, status, staff_profile):
        ci_time = parse_time(check_in_str)
        co_time = parse_time(check_out_str)
        record.check_in = ci_time
        record.check_out = co_time
        record.status = status
        record.marked_by = staff_profile
        record.total_hours_worked, record.late_minutes, record.early_leave_minutes = \
            self.calculate_working_hours(ci_time, co_time)
        record.save(update_fields=[
            "check_in", "check_out", "status", "marked_by",
            "total_hours_worked", "late_minutes", "early_leave_minutes"
        ])

    def check_staff_attendance(self, user, date):
        return self.repo.get_staff_attendance_today(user, date)

    def check_in_staff(self, user):
        now = timezone.localtime()
        today = timezone.localdate()
        record, created = StaffAttendance.objects.get_or_create(
            user=user, date=today,
            defaults={"check_in": now}
        )
        if not created and record.check_in is None:
            record.check_in = now
            record.save(update_fields=["check_in"])
        return record, created

    def check_out_staff(self, user, pk):
        record = StaffAttendance.objects.get(pk=pk, user=user)
        now = timezone.localtime()
        if record.check_in and record.check_out is None:
            record.check_out = now
            delta = record.check_out - record.check_in
            record.total_hours_worked = round(delta.total_seconds() / 3600, 2)
            record.save(update_fields=["check_out", "total_hours_worked"])
            return record
        return None
