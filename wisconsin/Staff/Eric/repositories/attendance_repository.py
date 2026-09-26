from collections import defaultdict
from datetime import date as date_type

from django.db.models import Count

from Faculty.models import FacultyProfile
from ..models import FacultyAttendanceRecord, StaffAttendance
from ..constants import AttendanceStatus


class AttendanceRepository:

    def get_records_for_date(self, date, department_id=None):
        qs = FacultyAttendanceRecord.objects.filter(date=date)
        return self._apply_department_filter(qs, department_id)

    def get_records_for_date_range(self, start_date, end_date, department_id=None):
        qs = FacultyAttendanceRecord.objects.filter(
            date__gte=start_date, date__lte=end_date
        )
        return self._apply_department_filter(qs, department_id)

    def get_records_for_faculty_month(self, faculty, year, month):
        first = date_type(year, month, 1)
        if month == 12:
            last = date_type(year + 1, 1, 1)
        else:
            last = date_type(year, month + 1, 1)
        return FacultyAttendanceRecord.objects.filter(
            faculty=faculty,
            date__gte=first,
            date__lt=last,
        ).order_by("date")

    def get_records_for_faculty_range(self, faculty, start_date, end_date):
        return FacultyAttendanceRecord.objects.filter(
            faculty=faculty,
            date__gte=start_date,
            date__lte=end_date,
        ).select_related(
            "faculty", "faculty__user", "marked_by", "marked_by__user"
        ).order_by("date")

    def get_or_create_record(self, faculty_id, date):
        record, created = FacultyAttendanceRecord.objects.get_or_create(
            faculty_id=faculty_id, date=date
        )
        return record, created

    def get_record_by_id(self, record_id):
        return FacultyAttendanceRecord.objects.select_related(
            "faculty", "faculty__user", "marked_by", "marked_by__user"
        ).get(pk=record_id)

    def get_monthly_records_optimized(self, start_date, end_date, department_id=None):
        qs = FacultyAttendanceRecord.objects.filter(
            date__gte=start_date, date__lte=end_date
        ).select_related(
            "faculty", "faculty__user", "faculty__faculty_rank",
            "marked_by", "marked_by__user"
        )
        return self._apply_department_filter(qs, department_id)

    def get_status_counts_for_date(self, date, department_id=None):
        qs = FacultyAttendanceRecord.objects.filter(date=date)
        if department_id is not None and str(department_id).isdigit():
            dept_faculty_ids = list(
                FacultyProfile.objects.filter(department_id=department_id)
                .values_list("id", flat=True)
            )
            qs = qs.filter(faculty_id__in=dept_faculty_ids)
        return dict(
            qs.values("status").annotate(total=Count("id"))
            .values_list("status", "total")
        )

    def get_status_counts_for_date_range(self, start_date, end_date, department_id=None):
        qs = FacultyAttendanceRecord.objects.filter(
            date__gte=start_date, date__lte=end_date
        )
        if department_id is not None and str(department_id).isdigit():
            dept_faculty_ids = list(
                FacultyProfile.objects.filter(department_id=department_id)
                .values_list("id", flat=True)
            )
            qs = qs.filter(faculty_id__in=dept_faculty_ids)
        return dict(
            qs.values("status").annotate(total=Count("id"))
            .values_list("status", "total")
        )

    def get_department_stats_for_date(self, date, department_ids):
        qs = FacultyAttendanceRecord.objects.filter(date=date)
        stats = {}
        for dept_id in department_ids:
            dept_faculty_ids = list(
                FacultyProfile.objects.filter(department_id=dept_id)
                .values_list("id", flat=True)
            )
            dept_records = qs.filter(faculty_id__in=dept_faculty_ids)
            counts = dict(
                dept_records.values("status").annotate(total=Count("id"))
                .values_list("status", "total")
            )
            stats[dept_id] = {
                "total": len(dept_faculty_ids),
                AttendanceStatus.PRESENT: counts.get(AttendanceStatus.PRESENT, 0),
                AttendanceStatus.ABSENT: counts.get(AttendanceStatus.ABSENT, 0),
                AttendanceStatus.LATE: counts.get(AttendanceStatus.LATE, 0),
                AttendanceStatus.ON_LEAVE: counts.get(AttendanceStatus.ON_LEAVE, 0),
                AttendanceStatus.HALF_DAY: counts.get(AttendanceStatus.HALF_DAY, 0),
            }
        return stats

    def get_records_by_date_map(self, start_date, end_date, department_id=None):
        qs = FacultyAttendanceRecord.objects.filter(
            date__gte=start_date, date__lte=end_date
        ).select_related(
            "faculty", "faculty__user", "marked_by", "marked_by__user"
        )
        if department_id:
            dept_faculty_ids = list(
                FacultyProfile.objects.filter(department_id=department_id)
                .values_list("id", flat=True)
            )
            qs = qs.filter(faculty_id__in=dept_faculty_ids)
        records_list = list(qs.order_by("date", "faculty__user__last_name"))
        grouped = defaultdict(list)
        for record in records_list:
            grouped[record.date].append(record)
        return records_list, grouped

    def bulk_update_records(self, records, fields):
        FacultyAttendanceRecord.objects.bulk_update(records, fields)

    def get_staff_attendance_month(self, user, year, month):
        return StaffAttendance.objects.filter(
            user=user,
            date__year=year,
            date__month=month,
        ).order_by("-date")

    def get_staff_attendance_range(self, user, start_date, end_date):
        return StaffAttendance.objects.filter(
            user=user,
            date__range=(start_date, end_date),
        ).order_by("date")

    def get_staff_attendance_today(self, user, today):
        return StaffAttendance.objects.filter(user=user, date=today).first()

    def _apply_department_filter(self, qs, department_id):
        if department_id is not None and str(department_id).isdigit():
            dept_faculty_ids = list(
                FacultyProfile.objects.filter(department_id=department_id)
                .values_list("id", flat=True)
            )
            qs = qs.filter(faculty_id__in=dept_faculty_ids)
        return qs
