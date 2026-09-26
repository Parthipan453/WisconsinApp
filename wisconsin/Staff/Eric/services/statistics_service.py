from datetime import date as date_type
from calendar import monthrange
from collections import defaultdict

from django.db.models import Count
from django.utils import timezone

from ..models import FacultyProfile
from ..constants import AttendanceStatus
from ..repositories.attendance_repository import AttendanceRepository


class StatisticsService:

    def __init__(self):
        self.repo = AttendanceRepository()

    def get_department_ids_and_names(self, department_ids=None):
        if department_ids is None:
            department_ids = list(
                FacultyProfile.objects.values_list("department_id", flat=True).distinct()
            )
        from Admin.bela_admin.models import Department
        dept_map = {}
        if department_ids:
            for d in Department.objects.filter(department_id__in=department_ids).values("department_id", "department_name"):
                dept_map[d["department_id"]] = d["department_name"]
        return department_ids, dept_map

    def build_department_name_map(self, department_ids):
        from Admin.bela_admin.models import Department
        name_map = {}
        if department_ids:
            for d in Department.objects.filter(department_id__in=department_ids).values("department_id", "department_name"):
                name_map[d["department_id"]] = d["department_name"]
        return name_map

    def get_department_name(self, department_id):
        if not department_id:
            return "\u2014"
        from Admin.bela_admin.models import Department
        try:
            return Department.objects.get(department_id=department_id).department_name
        except Exception:
            return f"Dept {department_id}"

    def get_status_counts_from_records(self, records_list):
        status_counts = {s: 0 for s in ["PRESENT", "ABSENT", "LATE", "ON_LEAVE", "HALF_DAY"]}
        for r in records_list:
            if r.status in status_counts:
                status_counts[r.status] += 1
        return status_counts

    def compute_monthly_stats(self, records):
        total = records.count()
        counts = dict(
            records.values("status").annotate(total=Count("id"))
            .values_list("status", "total")
        )
        return {
            "total": total,
            AttendanceStatus.PRESENT: counts.get(AttendanceStatus.PRESENT, 0),
            AttendanceStatus.ABSENT: counts.get(AttendanceStatus.ABSENT, 0),
            AttendanceStatus.LATE: counts.get(AttendanceStatus.LATE, 0),
            AttendanceStatus.ON_LEAVE: counts.get(AttendanceStatus.ON_LEAVE, 0),
            AttendanceStatus.HALF_DAY: counts.get(AttendanceStatus.HALF_DAY, 0),
        }

    def get_department_stats(self, date, department_ids):
        return self.repo.get_department_stats_for_date(date, department_ids)

    def build_calendar_popups(self, daily_data, total_faculty):
        popups = {}
        for day_info in daily_data:
            marked_pct = day_info["pct"]
            color_mod = (
                "za-cal-dot-green" if marked_pct >= 80
                else "za-cal-dot-amber" if marked_pct >= 50
                else "za-cal-dot-red" if marked_pct > 0
                else ""
            )
            key = day_info["date"].strftime("%Y-%m-%d")
            popups[key] = {
                "modifier": color_mod,
                "html": (
                    f"Day {day_info['day']}<br>"
                    f"{day_info['marked']}/{total_faculty} marked<br>"
                    f"{day_info['present']}P {day_info['absent']}A "
                    f"{day_info['late']}L {day_info['leave']}LV {day_info['halfday']}HD"
                ),
            }
        return popups

    def build_trend_data(self, daily_data, total_faculty):
        trend = []
        for d in daily_data:
            present_pct = round((d["present"] / total_faculty) * 100) if total_faculty else 0
            trend.append({
                "d": d["day"], "pct": d["pct"],
                "present_pct": present_pct,
                "p": d["present"], "a": d["absent"],
                "l": d["late"], "v": d["leave"],
                "h": d["halfday"], "m": d["marked"],
            })
        return trend

    def get_staff_monthly_hours(self, records):
        total_hours = 0
        for r in records:
            if r.total_hours_worked:
                total_hours += float(r.total_hours_worked)
        return round(total_hours, 2)
