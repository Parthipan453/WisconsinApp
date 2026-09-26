import json
import calendar as cal_mod
from datetime import date as date_type, timedelta
from calendar import monthrange

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from Admin.bela_admin.models import Department
from Faculty.models import FacultyProfile
from .models import Holiday, FacultyAttendanceRecord, StaffAttendance
from .constants import AttendanceStatus, EXPECTED_START_MINUTES, PAGINATE_BY
from .validators import clamp_year, parse_date, parse_time, check_owner_access, get_staff_profile
from .services.attendance_service import AttendanceService
from .services.holiday_service import HolidayService
from .services.statistics_service import StatisticsService
from .services.chart_service import ChartService
from .services.export_service import ExportService
from .repositories.attendance_repository import AttendanceRepository
from .repositories.holiday_repository import HolidayRepository
from .utils.calendar_utils import (
    get_us_holidays_for_year, get_holidays_for_month,
    build_month_calendar_data, MONTH_ABBREVIATIONS
)

attendance_service = AttendanceService()
holiday_service = HolidayService()
stats_service = StatisticsService()
chart_service = ChartService()
export_service = ExportService()
attendance_repo = AttendanceRepository()
holiday_repo = HolidayRepository()


@login_required
def faculty_attendance_view(request, user_uuid):
    access_response, staff_profile = check_owner_access(request, user_uuid)
    if access_response:
        return access_response

    selected_date = parse_date(request.GET.get("date", ""))
    selected_department = request.GET.get("department", "")
    search_term = request.GET.get("search", "").strip()
    department_ids, department_name_map = stats_service.get_department_ids_and_names()

    faculty_qs = FacultyProfile.objects.all().select_related("faculty_rank", "user")
    if selected_department:
        faculty_qs = faculty_qs.filter(department_id=selected_department)
    if search_term:
        faculty_qs = faculty_qs.filter(
            Q(user__first_name__icontains=search_term)
            | Q(user__last_name__icontains=search_term)
            | Q(employee_id__icontains=search_term)
        )
    faculty_qs = faculty_qs.filter(Q(hire_date__isnull=True) | Q(hire_date__lte=selected_date))

    existing_records = {
        r.faculty_id: r for r in
        FacultyAttendanceRecord.objects.filter(date=selected_date).select_related(
            "marked_by", "marked_by__user"
        )
    }

    month_holidays_lookup = get_holidays_for_month(selected_date.year, selected_date.month)
    selected_is_holiday = selected_date in month_holidays_lookup
    selected_holiday_name = month_holidays_lookup.get(selected_date, "")
    selected_is_weekend = selected_date.weekday() >= 5
    if holiday_service.is_working_day_override(selected_date):
        selected_is_weekend = False
        selected_is_holiday = False

    faculty_data_list = []
    for fm in faculty_qs:
        record = existing_records.get(fm.id)
        wh = None
        if record and record.total_hours_worked is not None:
            wh = float(record.total_hours_worked)
        elif record and record.check_in and record.check_out:
            ci_m = record.check_in.hour * 60 + record.check_in.minute
            co_m = record.check_out.hour * 60 + record.check_out.minute
            if co_m > ci_m:
                wh = round((co_m - ci_m) / 60, 2)
        faculty_data_list.append({
            "faculty": fm,
            "record": record,
            "dept_name": department_name_map.get(fm.department_id, f"Dept {fm.department_id}"),
            "working_hours": wh,
            "designation": fm.faculty_rank.rank_name if fm.faculty_rank else "",
        })

    filtered_ids = [f.id for f in faculty_qs]
    status_counts = dict(
        FacultyAttendanceRecord.objects.filter(
            date=selected_date, faculty_id__in=filtered_ids
        ).values("status").annotate(total=Count("id"))
        .values_list("status", "total")
    )
    count_present = status_counts.get("PRESENT", 0)
    count_absent = status_counts.get("ABSENT", 0)
    count_late = status_counts.get("LATE", 0)
    count_on_leave = status_counts.get("ON_LEAVE", 0)
    count_half_day = status_counts.get("HALF_DAY", 0)
    total_marked = count_present + count_absent + count_late + count_on_leave + count_half_day
    total_pending = len(faculty_data_list) - total_marked
    completion_pct = round((total_marked / len(faculty_data_list)) * 100) if faculty_data_list else 0

    days_in_month = monthrange(selected_date.year, selected_date.month)[1]
    first_day = date_type(selected_date.year, selected_date.month, 1)
    last_day = date_type(selected_date.year, selected_date.month, days_in_month)

    filtered_faculty_ids = list(faculty_qs.values_list("id", flat=True))
    monthly_qs = FacultyAttendanceRecord.objects.filter(
        date__gte=first_day, date__lte=last_day,
        faculty_id__in=filtered_faculty_ids
    )
    monthly_records = list(monthly_qs)
    records_by_date = {}
    for r in monthly_records:
        records_by_date.setdefault(r.date, []).append(r)

    total_faculty_count = faculty_qs.count()
    daily_data = build_month_calendar_data(
        selected_date.year, selected_date.month, records_by_date, total_faculty_count
    )

    prev_month_date = (first_day - timedelta(days=1)).replace(day=1)
    next_month_date = (last_day + timedelta(days=1)).replace(day=1)

    department_stats = []
    for dept_id in department_ids:
        dept_fac_ids = list(
            FacultyProfile.objects.filter(department_id=dept_id)
            .filter(Q(hire_date__isnull=True) | Q(hire_date__lte=selected_date))
            .values_list("id", flat=True)
        )
        dept_recs = FacultyAttendanceRecord.objects.filter(
            date=selected_date, faculty_id__in=dept_fac_ids
        )
        dept_counts = dict(
            dept_recs.values("status").annotate(total=Count("id"))
            .values_list("status", "total")
        )
        department_stats.append({
            "name": department_name_map.get(dept_id, f"Dept {dept_id}"),
            "total": len(dept_fac_ids),
            "present": dept_counts.get("PRESENT", 0),
            "absent": dept_counts.get("ABSENT", 0),
            "late": dept_counts.get("LATE", 0),
            "leave": dept_counts.get("ON_LEAVE", 0),
            "half": dept_counts.get("HALF_DAY", 0),
        })

    department_json = json.dumps([
        {"d": d["name"], "p": d["present"], "a": d["absent"],
         "l": d["late"], "v": d["leave"], "h": d["half"], "t": d["total"]}
        for d in department_stats
    ])

    donut_segments = chart_service.build_donut_segments(status_counts)
    paginator = Paginator(faculty_data_list, PAGINATE_BY)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    cal_popups = stats_service.build_calendar_popups(daily_data, total_faculty_count)
    trend_data = stats_service.build_trend_data(daily_data, total_faculty_count)
    month_holidays = get_holidays_for_month(selected_date.year, selected_date.month)

    undo_info = request.session.get("attendance_undo")
    undo_available = bool(undo_info and undo_info.get("date") == str(selected_date))

    context = {
        "user": request.user,
        "departments": [
            {"id": d.department_id, "name": d.department_name}
            for d in Department.objects.all().order_by("department_name")
        ],
        "selected_date": selected_date,
        "selected_search": search_term,
        "today": timezone.localdate(),
        "chart_data_json": chart_service.build_chart_data_json(
            chart_service.build_donut_json(status_counts),
            trend_data, total_marked, total_pending
        ),
        "calendar_data_json": chart_service.build_calendar_data_json(
            cal_popups, selected_date, selected_date.month, selected_date.year,
            selected_department, timezone.localdate()
        ),
        "prev_date": selected_date - timedelta(days=1),
        "next_date": selected_date + timedelta(days=1),
        "selected_dept": int(selected_department) if selected_department else None,
        "faculty_list": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "present_count": count_present,
        "absent_count": count_absent,
        "late_count": count_late,
        "leave_count": count_on_leave,
        "halfday_count": count_half_day,
        "total_count": len(faculty_data_list),
        "pending_count": total_pending,
        "marked_count": total_marked,
        "completion_pct": completion_pct,
        "prev_month_date": prev_month_date,
        "next_month_date": next_month_date,
        "month_holidays": month_holidays,
        "selected_is_holiday": selected_is_holiday,
        "selected_holiday_name": selected_holiday_name,
        "selected_is_weekend": selected_is_weekend,
        "undo_available": undo_available,
    }
    return render(request, "Eric/faculty_attendance.html", context)


@login_required
def mark_attendance(request):
    if request.method != "POST":
        return redirect("faculty_attendance", user_uuid=request.user.uuid)
    selected_date = parse_date(request.POST.get("attendance_date", ""))

    month_holidays_lookup = get_holidays_for_month(selected_date.year, selected_date.month)
    is_holiday_or_weekend = selected_date in month_holidays_lookup or selected_date.weekday() >= 5
    if is_holiday_or_weekend and not holiday_service.is_working_day_override(selected_date):
        messages.warning(request, f"Cannot mark attendance for {selected_date} — it is a weekend or holiday.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    faculty_ids = request.POST.getlist("faculty_id")
    ci_values = request.POST.getlist("check_in")
    co_values = request.POST.getlist("check_out")
    st_values = request.POST.getlist("status")

    undo_data = {"date": str(selected_date), "records": {}}
    for fid in faculty_ids:
        record = FacultyAttendanceRecord.objects.filter(faculty_id=fid, date=selected_date).first()
        if record:
            undo_data["records"][fid] = {
                "was_created": False,
                "check_in": str(record.check_in) if record.check_in else None,
                "check_out": str(record.check_out) if record.check_out else None,
                "status": record.status,
                "total_hours_worked": str(record.total_hours_worked) if record.total_hours_worked else None,
                "late_minutes": record.late_minutes,
                "early_leave_minutes": record.early_leave_minutes,
                "marked_by_id": record.marked_by_id,
            }
        else:
            undo_data["records"][fid] = {"was_created": True}

    number_updated = attendance_service.mark_attendance_bulk(
        request, selected_date, faculty_ids, ci_values, co_values, st_values
    )

    if number_updated > 0:
        request.session["attendance_undo"] = undo_data
        request.session.modified = True
        messages.success(request, f"Attendance saved for {number_updated} faculty member(s).")
    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def bulk_edit_attendance(request):
    if request.method != "POST":
        return redirect("faculty_attendance", user_uuid=request.user.uuid)
    selected_date = parse_date(request.POST.get("attendance_date", ""))

    faculty_ids = request.POST.getlist("faculty_id")
    ci_values = request.POST.getlist("check_in")
    co_values = request.POST.getlist("check_out")
    st_values = request.POST.getlist("status")

    undo_data = {"date": str(selected_date), "records": {}}
    for fid in faculty_ids:
        record = FacultyAttendanceRecord.objects.filter(faculty_id=fid, date=selected_date).first()
        if record:
            undo_data["records"][fid] = {
                "was_created": False,
                "check_in": str(record.check_in) if record.check_in else None,
                "check_out": str(record.check_out) if record.check_out else None,
                "status": record.status,
                "total_hours_worked": str(record.total_hours_worked) if record.total_hours_worked else None,
                "late_minutes": record.late_minutes,
                "early_leave_minutes": record.early_leave_minutes,
                "marked_by_id": record.marked_by_id,
            }

    number_updated = attendance_service.mark_attendance_bulk(
        request, selected_date, faculty_ids, ci_values, co_values, st_values
    )

    if number_updated > 0:
        request.session["attendance_undo"] = undo_data
        request.session.modified = True
        messages.success(request, f"Bulk edit saved for {number_updated} faculty member(s).")
    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def undo_mark_attendance(request):
    undo_info = request.session.pop("attendance_undo", None)
    if not undo_info:
        messages.warning(request, "Nothing to undo.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    from decimal import Decimal
    restored = 0
    for fid_str, snapshot in undo_info["records"].items():
        fid = int(fid_str)
        if snapshot.get("was_created"):
            deleted, _ = FacultyAttendanceRecord.objects.filter(
                faculty_id=fid, date=undo_info["date"]
            ).delete()
            if deleted:
                restored += 1
        else:
            record = FacultyAttendanceRecord.objects.filter(
                faculty_id=fid, date=undo_info["date"]
            ).first()
            if record:
                record.check_in = timezone.datetime.strptime(snapshot["check_in"], "%H:%M:%S").time() if snapshot.get("check_in") else None
                record.check_out = timezone.datetime.strptime(snapshot["check_out"], "%H:%M:%S").time() if snapshot.get("check_out") else None
                record.status = snapshot.get("status", "PRESENT")
                record.total_hours_worked = Decimal(snapshot["total_hours_worked"]) if snapshot.get("total_hours_worked") else None
                record.late_minutes = snapshot.get("late_minutes", 0)
                record.early_leave_minutes = snapshot.get("early_leave_minutes", 0)
                record.marked_by_id = snapshot.get("marked_by_id")
                record.save(update_fields=[
                    "check_in", "check_out", "status", "total_hours_worked",
                    "late_minutes", "early_leave_minutes", "marked_by_id"
                ])
                restored += 1

    messages.success(request, f"Undo successful. {restored} record(s) restored.")
    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def attendance_records_view(request, user_uuid):
    access_response, staff_profile = check_owner_access(request, user_uuid)
    if access_response:
        return access_response

    selected_department = request.GET.get("department", "")
    search_query = request.GET.get("search", "").strip()

    faculty_qs = FacultyProfile.objects.select_related("faculty_rank", "user").all()
    if selected_department:
        faculty_qs = faculty_qs.filter(department_id=selected_department)
    faculty_qs = faculty_qs.filter(Q(hire_date__isnull=True) | Q(hire_date__lte=timezone.localdate()))
    if search_query:
        faculty_qs = faculty_qs.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(employee_id__icontains=search_query)
        )

    department_ids, department_name_map = stats_service.get_department_ids_and_names()

    faculty_items = [
        {
            "faculty": fm,
            "dept_name": department_name_map.get(fm.department_id, f"Dept {fm.department_id}")
        }
        for fm in faculty_qs
    ]

    context = {
        "user": request.user,
        "faculty_list": faculty_items,
        "departments": [
            {"id": d, "name": department_name_map.get(d, f"Dept {d}")}
            for d in department_ids
        ],
        "selected_dept": selected_department,
        "search": search_query,
    }
    return render(request, "Eric/attendance_records.html", context)


@login_required
def faculty_monthly_view(request, faculty_uuid):
    staff_profile = get_staff_profile(request)
    if not staff_profile:
        return redirect("login")

    faculty_member = get_object_or_404(FacultyProfile, user__uuid=faculty_uuid)
    today = timezone.localdate()
    view_mode = request.GET.get("view", "month")
    selected_year = clamp_year(int(request.GET.get("year", today.year)), today.year)
    selected_month = int(request.GET.get("month", today.month))
    dept_name = stats_service.get_department_name(faculty_member.department_id)

    month_groups = []
    semester_groups = []
    last3_label = ""
    records = []
    sel_date = None
    prev_year = selected_year - 1
    next_year = selected_year + 1 if selected_year < today.year else None

    if view_mode == "day":
        sel_date = parse_date(request.GET.get("date", "")) or today
        records = attendance_repo.get_records_for_faculty_range(
            faculty_member, sel_date, sel_date
        )
        monthly_stats = stats_service.compute_monthly_stats(records)

    elif view_mode == "year":
        range_option = request.GET.get("range", "12")
        if range_option == "3":
            month_year_pairs = _last_three_calendar_months()
            first_y, first_m = month_year_pairs[0]
            last_y, last_m = month_year_pairs[-1]
            year_start = date_type(first_y, first_m, 1)
            year_end = date_type(last_y, last_m, monthrange(last_y, last_m)[1])
            last3_label = (
                f"{date_type(first_y, first_m, 1).strftime('%b %Y')} – "
                f"{date_type(last_y, last_m, 1).strftime('%b %Y')}"
            )
        else:
            month_year_pairs = [(selected_year, m) for m in range(1, 13)]
            year_start = date_type(selected_year, 1, 1)
            year_end = date_type(selected_year, 12, 31)
            last3_label = ""
        year_records = attendance_repo.get_records_for_faculty_range(
            faculty_member, year_start, year_end
        )
        grouped = {}
        for r in year_records:
            grouped.setdefault(r.date, []).append(r)
        for y, m in month_year_pairs:
            groups = {}
            for day_date, day_recs in grouped.items():
                if day_date.year == y and day_date.month == m:
                    groups[day_date] = day_recs
            month_groups.append({
                "month": m,
                "year": y,
                "label": date_type(y, m, 1).strftime("%B"),
                "count": sum(len(v) for v in groups.values()),
                "groups": groups,
            })
        records = year_records
        monthly_stats = stats_service.compute_monthly_stats(year_records)

    elif view_mode == "semester":
        sem_start = date_type(selected_year, 9, 1)
        sem_end = date_type(selected_year + 1, 8, 31)
        sem_records = attendance_repo.get_records_for_faculty_range(
            faculty_member, sem_start, sem_end
        )
        grouped = {}
        for r in sem_records:
            grouped.setdefault(r.date, []).append(r)
        semesters = [
            ("Fall", selected_year, 9, 12, "Fall " + str(selected_year)),
            ("Spring", selected_year + 1, 1, 4, "Spring " + str(selected_year + 1)),
            ("Summer", selected_year + 1, 5, 8, "Summer " + str(selected_year + 1)),
        ]
        for key, yr, m_start, m_end, label in semesters:
            s_start = date_type(yr, m_start, 1)
            s_end = date_type(yr, m_end, monthrange(yr, m_end)[1])
            if s_end > today:
                continue
            months = []
            for m in range(m_start, m_end + 1):
                groups = {}
                for day_date, day_recs in grouped.items():
                    if day_date.year == yr and day_date.month == m:
                        groups[day_date] = day_recs
                months.append({
                    "month": m,
                    "year": yr,
                    "label": date_type(yr, m, 1).strftime("%B"),
                    "count": sum(len(v) for v in groups.values()),
                    "groups": groups,
                })
            semester_groups.append({
                "key": label.replace(" ", "-"),
                "label": label,
                "subtitle": f"{s_start.strftime('%b %d')} – {s_end.strftime('%b %d, %Y')}",
                "count": sum(mg["count"] for mg in months),
                "months": months,
            })
        records = sem_records
        monthly_stats = stats_service.compute_monthly_stats(sem_records)

    else:
        view_mode = "month"
        monthly_records = attendance_repo.get_records_for_faculty_month(
            faculty_member, selected_year, selected_month
        )
        records = monthly_records

        if selected_month == 1:
            prev_y, prev_m = selected_year - 1, 12
        else:
            prev_y, prev_m = selected_year, selected_month - 1
        if selected_month == 12:
            next_y, next_m = selected_year + 1, 1
        else:
            next_y, next_m = selected_year, selected_month + 1

        monthly_stats = stats_service.compute_monthly_stats(monthly_records)
        status_by_day = {r.date.day: (r.status or "PENDING") for r in monthly_records}
        month_cal_grid = cal_mod.monthcalendar(selected_year, selected_month)
        flat_days = []
        for week in month_cal_grid:
            for day_num in week:
                if day_num == 0:
                    continue
                flat_days.append({"day": day_num, "status": status_by_day.get(day_num, "NO_DATA")})
        monthly_data_json = json.dumps({
            "donut": [
                {"l": "Present", "v": monthly_stats["PRESENT"], "c": "#16a34a"},
                {"l": "Absent", "v": monthly_stats["ABSENT"], "c": "#dc2626"},
                {"l": "Late", "v": monthly_stats["LATE"], "c": "#d97706"},
                {"l": "On Leave", "v": monthly_stats["ON_LEAVE"], "c": "#7c3aed"},
                {"l": "Half Day", "v": monthly_stats["HALF_DAY"], "c": "#2563eb"},
            ],
            "daily": flat_days,
            "year": selected_year,
            "month": selected_month,
            "legend": [
                {"color": "#16a34a", "label": "Present", "count": monthly_stats["PRESENT"]},
                {"color": "#dc2626", "label": "Absent", "count": monthly_stats["ABSENT"]},
                {"color": "#d97706", "label": "Late", "count": monthly_stats["LATE"]},
                {"color": "#7c3aed", "label": "Leave", "count": monthly_stats["ON_LEAVE"]},
                {"color": "#2563eb", "label": "Half", "count": monthly_stats["HALF_DAY"]},
            ]
        })

    total_records = monthly_stats.get("total", len(records))
    empty_status_count = sum(1 for r in records if not r.status)
    marked_count = total_records - empty_status_count
    completion_pct = round((marked_count / total_records) * 100) if total_records else 0

    context = {
        "user": request.user,
        "faculty": faculty_member,
        "view_mode": view_mode,
        "records": records,
        "year": selected_year,
        "month": selected_month,
        "prev_y": prev_y if view_mode == "month" else None,
        "prev_m": prev_m if view_mode == "month" else None,
        "next_y": next_y if view_mode == "month" else None,
        "next_m": next_m if view_mode == "month" else None,
        "prev_year": prev_year,
        "next_year": next_year,
        "sel_date": sel_date,
        "range_option": request.GET.get("range", "12") if view_mode == "year" else "",
        "month_groups": month_groups,
        "semester_groups": semester_groups,
        "last3_label": last3_label,
        "dept_name": dept_name,
        "month_name": date_type(selected_year, selected_month, 1).strftime("%B %Y"),
        "mpresent": monthly_stats.get("PRESENT", 0), "mabsent": monthly_stats.get("ABSENT", 0),
        "mlate": monthly_stats.get("LATE", 0), "mleave": monthly_stats.get("ON_LEAVE", 0),
        "mhalf": monthly_stats.get("HALF_DAY", 0),
        "total_records": total_records,
        "marked": marked_count,
        "completion": completion_pct,
        "monthly_data_json": monthly_data_json if view_mode == "month" else "{}",
    }
    return render(request, "Eric/faculty_monthly.html", context)


@login_required
def edit_attendance_view(request, record_id):
    staff_profile = get_staff_profile(request)
    if not staff_profile:
        return redirect("login")

    attendance_record = get_object_or_404(
        FacultyAttendanceRecord.objects.select_related(
            "faculty", "faculty__user", "marked_by", "marked_by__user"
        ),
        pk=record_id
    )
    dept_name = stats_service.get_department_name(attendance_record.faculty.department_id)

    if request.method == "POST":
        attendance_service.update_single_record(
            attendance_record,
            request.POST.get("check_in"),
            request.POST.get("check_out"),
            request.POST.get("status", attendance_record.status),
            staff_profile,
        )
        messages.success(request, "Attendance record updated.")
        fallback = reverse("attendance_records", kwargs={"user_uuid": request.user.uuid})
        return redirect(request.META.get("HTTP_REFERER", fallback))

    context = {
        "user": request.user,
        "record": attendance_record,
        "expected_day_duration": 8,
        "dept_name": dept_name,
    }
    return render(request, "Eric/edit_attendance.html", context)


def _faculty_export_context(request, faculty_member):
    """Resolve view/range/year/month (or date) and records/title for a faculty export.

    Returns a dict or None when the caller should fall back to the month export.
    """
    view = request.GET.get("view", "month")
    export_year = clamp_year(int(request.GET.get("year", timezone.localdate().year)))
    range_option = request.GET.get("range", "12")
    full_name = faculty_member.user.get_full_name()

    if view == "day":
        day_str = request.GET.get("date")
        sel_date = date_type.fromisoformat(day_str) if day_str else timezone.localdate()
        records = list(attendance_repo.get_records_for_faculty_range(faculty_member, sel_date, sel_date))
        title = f"{full_name} — {sel_date.strftime('%b %d, %Y')}"
        return {"records": records, "title": title, "export_year": export_year}
    if view == "year":
        if range_option == "3":
            months = _last_three_calendar_months()
            start = date_type(months[0][0], months[0][1], 1)
            end = date_type(months[-1][0], months[-1][1], 1)
            end = end.replace(day=cal_mod.monthrange(end.year, end.month)[1])
            label = f"{MONTH_ABBREVIATIONS[months[0][1]]} {months[0][0]} – {MONTH_ABBREVIATIONS[months[-1][1]]} {months[-1][0]}"
            title = f"{full_name} — Last 3 Months ({label})"
        else:
            start = date_type(export_year, 1, 1)
            end = date_type(export_year, 12, 31)
            title = f"{full_name} — Calendar Year {export_year}"
        records = list(attendance_repo.get_records_for_faculty_range(faculty_member, start, end))
        return {"records": records, "title": title, "export_year": export_year}
    if view == "semester":
        start = date_type(export_year, 9, 1)
        end = date_type(export_year + 1, 8, 31)
        records = list(attendance_repo.get_records_for_faculty_range(faculty_member, start, end))
        title = f"{full_name} — Academic Year {export_year}–{export_year + 1}"
        return {"records": records, "title": title, "export_year": export_year}
    return None


@login_required
def export_faculty_excel(request, faculty_uuid):
    staff_profile = get_staff_profile(request)
    if not staff_profile:
        return redirect("login")
    faculty_member = get_object_or_404(FacultyProfile, user__uuid=faculty_uuid)
    context = _faculty_export_context(request, faculty_member)
    if context is not None:
        return export_service.export_day_view_excel(context["records"], context["title"])
    export_year = clamp_year(int(request.GET.get("year", timezone.localdate().year)))
    return export_service.export_faculty_month_excel(
        faculty_member,
        export_year,
        int(request.GET.get("month", timezone.localdate().month)),
    )


@login_required
def export_faculty_pdf(request, faculty_uuid):
    staff_profile = get_staff_profile(request)
    if not staff_profile:
        return redirect("login")
    faculty_member = get_object_or_404(FacultyProfile, user__uuid=faculty_uuid)
    context = _faculty_export_context(request, faculty_member)
    if context is not None:
        return export_service.export_day_view_pdf(context["records"], context["title"])
    export_year = clamp_year(int(request.GET.get("year", timezone.localdate().year)))
    return export_service.export_faculty_month_pdf(
        faculty_member,
        export_year,
        int(request.GET.get("month", timezone.localdate().month)),
    )


def _last_three_calendar_months(from_date=None):
    """Return [(year, month)] for the current month and the two prior calendar months."""
    today = from_date or timezone.localdate()
    total = today.year * 12 + (today.month - 1)
    return [((total - back) // 12, (total - back) % 12 + 1) for back in range(2, -1, -1)]


def _build_period_summary(view_mode, range_option, academic_year, department_id):
    """Build attendance summary sections for year / last-3-months / semester views."""
    sections = []
    now = timezone.localdate()

    def _counts(start, end):
        recs = attendance_repo.get_records_for_date_range(start, end, department_id)
        return stats_service.get_status_counts_from_records(recs)

    if view_mode == "semester":
        semesters = [
            ("Fall " + str(academic_year),
             date_type(academic_year, 9, 1), date_type(academic_year, 12, 31)),
            ("Spring " + str(academic_year + 1),
             date_type(academic_year + 1, 1, 1), date_type(academic_year + 1, 4, 30)),
            ("Summer " + str(academic_year + 1),
             date_type(academic_year + 1, 5, 1), date_type(academic_year + 1, 8, 31)),
        ]
        for label, start, end in semesters:
            if end > now:
                continue
            sections.append({
                "label": label,
                "subtitle": f"{start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}",
                "counts": _counts(start, end),
            })
    else:
        if range_option == "3":
            work_months = _last_three_calendar_months()
        else:
            work_months = [(academic_year, m) for m in range(1, 13)]
        for year, month in work_months:
            start = date_type(year, month, 1)
            end = date_type(year, month, monthrange(year, month)[1])
            sections.append({
                "label": date_type(year, month, 1).strftime("%B"),
                "subtitle": f"{date_type(year, month, 1).strftime('%B %Y')}",
                "counts": _counts(start, end),
            })

    totals = {"PRESENT": 0, "ABSENT": 0, "LATE": 0, "ON_LEAVE": 0, "HALF_DAY": 0}
    for sec in sections:
        for k in totals:
            totals[k] += sec["counts"].get(k, 0)
    return {"sections": sections, "totals": totals}


@login_required
def attendance_day_month_view(request, user_uuid):
    access_response, staff_profile = check_owner_access(request, user_uuid)
    if access_response:
        return access_response

    view_mode = request.GET.get("view", "day")
    raw_department = request.GET.get("department", "")
    selected_department = (
        raw_department
        if (raw_department and raw_department.isdigit())
        else ""
    )
    selected_year = clamp_year(int(request.GET.get("year", timezone.localdate().year)))
    selected_month = int(request.GET.get("month", timezone.localdate().month))
    selected_date = parse_date(request.GET.get("date", ""))

    department_ids, department_name_map = stats_service.get_department_ids_and_names()
    department_list = [
        {"id": d, "name": department_name_map.get(d, f"Dept {d}")}
        for d in department_ids
        if d is not None
    ]

    def _annotate_dept_name(rec):
        rec.dept_name = department_name_map.get(rec.faculty.department_id, "\u2014")
        return rec

    records_list, grouped_records = None, {}

    if view_mode == "month":
        days_in_month = monthrange(selected_year, selected_month)[1]
        first_day = date_type(selected_year, selected_month, 1)
        last_day = date_type(selected_year, selected_month, days_in_month)

        records_list, grouped_records = attendance_repo.get_records_by_date_map(
            first_day, last_day, selected_department
        )
        for rec in records_list:
            _annotate_dept_name(rec)

        status_counts = stats_service.get_status_counts_from_records(records_list)
        unique_faculty = len(set(r.faculty_id for r in records_list))
        prev_month = (first_day - timedelta(days=1)).replace(day=1)
        next_month = (last_day + timedelta(days=1)).replace(day=1)

    elif view_mode in ("year", "semester"):
        range_option = request.GET.get("range", "12")
        academic_year = selected_year
        period = _build_period_summary(
            view_mode, range_option, academic_year, selected_department
        )
        status_counts = {"PRESENT": 0, "ABSENT": 0, "LATE": 0,
                         "ON_LEAVE": 0, "HALF_DAY": 0}
        for sec in period["sections"]:
            for k in status_counts:
                status_counts[k] += sec["counts"].get(k, 0)
        records_list = []
        month_groups = []
        semester_groups = []
        last3_label = ""
        if view_mode == "year":
            if range_option == "3":
                month_year_pairs = _last_three_calendar_months()
                first_y, first_m = month_year_pairs[0]
                last_y, last_m = month_year_pairs[-1]
                year_start = date_type(first_y, first_m, 1)
                year_end = date_type(last_y, last_m, monthrange(last_y, last_m)[1])
                last3_label = (
                    f"{date_type(first_y, first_m, 1).strftime('%b %Y')} – "
                    f"{date_type(last_y, last_m, 1).strftime('%b %Y')}"
                )
            else:
                month_year_pairs = [(academic_year, m) for m in range(1, 13)]
                year_start = date_type(academic_year, 1, 1)
                year_end = date_type(academic_year, 12, 31)
                last3_label = ""
            year_records, year_grouped = attendance_repo.get_records_by_date_map(
                year_start, year_end, selected_department
            )
            for rec in year_records:
                _annotate_dept_name(rec)
            records_list = year_records
            for y, m in month_year_pairs:
                groups = {}
                for day_date, day_recs in year_grouped.items():
                    if day_date.year == y and day_date.month == m:
                        groups[day_date] = day_recs
                month_groups.append({
                    "month": m,
                    "year": y,
                    "label": date_type(y, m, 1).strftime("%B"),
                    "count": sum(len(v) for v in groups.values()),
                    "groups": groups,
                })
        else:
            sem_start = date_type(academic_year, 9, 1)
            sem_end = date_type(academic_year + 1, 8, 31)
            sem_records, sem_grouped = attendance_repo.get_records_by_date_map(
                sem_start, sem_end, selected_department
            )
            for rec in sem_records:
                _annotate_dept_name(rec)
            records_list = sem_records
            today = timezone.localdate()
            semesters = [
                ("Fall", academic_year, 9, 12, "Fall " + str(academic_year)),
                ("Spring", academic_year + 1, 1, 4, "Spring " + str(academic_year + 1)),
                ("Summer", academic_year + 1, 5, 8, "Summer " + str(academic_year + 1)),
            ]
            for key, yr, m_start, m_end, label in semesters:
                s_start = date_type(yr, m_start, 1)
                s_end = date_type(yr, m_end, monthrange(yr, m_end)[1])
                if s_end > today:
                    continue
                months = []
                for m in range(m_start, m_end + 1):
                    groups = {}
                    for day_date, day_recs in sem_grouped.items():
                        if day_date.year == yr and day_date.month == m:
                            groups[day_date] = day_recs
                    months.append({
                        "month": m,
                        "year": yr,
                        "label": date_type(yr, m, 1).strftime("%B"),
                        "count": sum(len(v) for v in groups.values()),
                        "groups": groups,
                    })
                semester_groups.append({
                    "key": label.replace(" ", "-"),
                    "label": label,
                    "subtitle": f"{s_start.strftime('%b %d')} – {s_end.strftime('%b %d, %Y')}",
                    "count": sum(mg["count"] for mg in months),
                    "months": months,
                })
        # navigation
        end = date_type(academic_year + 1, 8, 31)
        prev_period = (date_type(academic_year, 1, 1) - timedelta(days=1))
        cur = date_type(academic_year, 9, 1)
        next_start = cur.replace(year=cur.year + 1)
        if next_start > timezone.localdate():
            next_start = None

    else:
        records_list, _ = attendance_repo.get_records_by_date_map(
            selected_date, selected_date, selected_department
        )
        for rec in records_list:
            _annotate_dept_name(rec)
        status_counts = stats_service.get_status_counts_from_records(records_list)

    total_marked = sum(status_counts.values())
    if view_mode in ("year", "semester"):
        total_records = total_marked
    else:
        total_records = len(records_list) if records_list else 0
    total_pending = total_records - total_marked

    if view_mode in ("year", "semester"):
        sel_date_obj = date_type(selected_year, 9, 1)
        chart_title = f"Academic Year {selected_year}"
    else:
        sel_date_obj = selected_date if view_mode == "day" else date_type(selected_year, selected_month, 1)
        chart_title = sel_date_obj.strftime("%M j, Y") if view_mode == "day" else sel_date_obj.strftime("%F Y")

    if view_mode == "month" and records_list:
        faculty_qs = FacultyProfile.objects.all()
        if selected_department:
            faculty_qs = faculty_qs.filter(department_id=selected_department)
        relevant_date = date_type(selected_year, selected_month, days_in_month)
        faculty_qs = faculty_qs.filter(Q(hire_date__isnull=True) | Q(hire_date__lte=relevant_date))
        total_faculty_count = faculty_qs.count()
        daily_data = build_month_calendar_data(
            selected_year, selected_month, grouped_records, total_faculty_count
        )
        trend_data = stats_service.build_trend_data(daily_data, total_faculty_count)
    else:
        trend_data = []

    chart_data_json = chart_service.build_chart_data_json(
        chart_service.build_donut_json(status_counts),
        trend_data, total_marked, total_pending
    )

    base_ctx = {
        "user": request.user,
        "departments": department_list,
        "selected_dept": selected_department,
        "records": records_list or [],
        "count_present": status_counts.get("PRESENT", 0),
        "count_absent": status_counts.get("ABSENT", 0),
        "count_late": status_counts.get("LATE", 0),
        "count_leave": status_counts.get("ON_LEAVE", 0),
        "count_half": status_counts.get("HALF_DAY", 0),
        "total_records": total_records,
        "chart_data_json": chart_data_json,
    }

    if view_mode == "day":
        month_holidays_lookup = get_holidays_for_month(selected_date.year, selected_date.month)
        base_ctx["selected_is_weekend"] = selected_date.weekday() >= 5
        base_ctx["selected_is_holiday"] = selected_date in month_holidays_lookup
        base_ctx["selected_holiday_name"] = month_holidays_lookup.get(selected_date, "")
        if holiday_service.is_working_day_override(selected_date):
            base_ctx["selected_is_weekend"] = False
            base_ctx["selected_is_holiday"] = False
    else:
        base_ctx["selected_is_weekend"] = False
        base_ctx["selected_is_holiday"] = False
        base_ctx["selected_holiday_name"] = ""

    if view_mode == "month":
        base_ctx.update({
            "view_mode": "month",
            "sel_year": selected_year, "sel_month": selected_month,
            "sel_date": sel_date_obj,
            "prev_month": prev_month, "next_month": next_month,
            "unique_faculty": unique_faculty,
            "total_days": len(grouped_records),
            "days_in_month": days_in_month,
            "grouped_records": dict(sorted(grouped_records.items())) if grouped_records else {},
        })
    elif view_mode in ("year", "semester"):
        base_ctx.update({
            "view_mode": view_mode,
            "sel_year": selected_year,
            "sel_date": sel_date_obj,
            "range_option": range_option,
            "period": period,
            "month_groups": month_groups,
            "semester_groups": semester_groups,
            "last3_label": last3_label,
            "prev_year": selected_year - 1,
            "next_year": selected_year + 1 if next_start else None,
        })
    else:
        base_ctx.update({
            "view_mode": "day",
            "sel_date": selected_date,
            "prev_date": selected_date - timedelta(days=1),
            "next_date": selected_date + timedelta(days=1),
        })

    context = base_ctx

    return render(request, "Eric/attendance_day_month.html", context)


@login_required
def export_day_month_excel(request, user_uuid):
    access_response, staff_profile = check_owner_access(request, user_uuid)
    if access_response:
        return access_response

    view_mode = request.GET.get("view", "day")
    selected_department = request.GET.get("department", "")
    selected_year = clamp_year(int(request.GET.get("year", timezone.localdate().year)))
    selected_month = int(request.GET.get("month", timezone.localdate().month))
    selected_date = parse_date(request.GET.get("date", ""))

    if view_mode == "month":
        first = date_type(selected_year, selected_month, 1)
        _, nd = monthrange(selected_year, selected_month)
        last = date_type(selected_year, selected_month, nd)
        title = f"Attendance_{MONTH_ABBREVIATIONS[selected_month]}_{selected_year}"
    elif view_mode == "year":
        range_option = request.GET.get("range", "12")
        if range_option == "3":
            pairs = _last_three_calendar_months()
            first = date_type(pairs[0][0], pairs[0][1], 1)
            last = date_type(pairs[-1][0], pairs[-1][1], monthrange(pairs[-1][0], pairs[-1][1])[1])
            title = f"Attendance_Last3Months_{first.strftime('%b%y')}-{last.strftime('%b%y')}"
        else:
            first = date_type(selected_year, 1, 1)
            last = date_type(selected_year, 12, 31)
            title = f"Attendance_{selected_year}_Year"
    elif view_mode == "semester":
        first = date_type(selected_year, 9, 1)
        last = date_type(selected_year + 1, 8, 31)
        title = f"Attendance_{selected_year}_{selected_year + 1}_Semester"
    else:
        records_list, _ = attendance_repo.get_records_by_date_map(
            selected_date, selected_date, selected_department
        )
        title = f"Attendance_{selected_date}"

    if view_mode in ("year", "semester"):
        records_list, _ = attendance_repo.get_records_by_date_map(first, last, selected_department)

    return export_service.export_day_view_excel(records_list, title)


@login_required
def export_day_month_pdf(request, user_uuid):
    access_response, staff_profile = check_owner_access(request, user_uuid)
    if access_response:
        return access_response

    view_mode = request.GET.get("view", "day")
    selected_department = request.GET.get("department", "")
    selected_year = clamp_year(int(request.GET.get("year", timezone.localdate().year)))
    selected_month = int(request.GET.get("month", timezone.localdate().month))
    selected_date = parse_date(request.GET.get("date", ""))

    if view_mode == "month":
        first = date_type(selected_year, selected_month, 1)
        _, nd = monthrange(selected_year, selected_month)
        last = date_type(selected_year, selected_month, nd)
        records_list, _ = attendance_repo.get_records_by_date_map(first, last, selected_department)
        title = f"All Faculty Attendance — {MONTH_ABBREVIATIONS[selected_month]} {selected_year}"
    elif view_mode == "year":
        range_option = request.GET.get("range", "12")
        if range_option == "3":
            pairs = _last_three_calendar_months()
            first = date_type(pairs[0][0], pairs[0][1], 1)
            last = date_type(pairs[-1][0], pairs[-1][1], monthrange(pairs[-1][0], pairs[-1][1])[1])
            title = f"All Faculty Attendance — Last 3 Months ({first.strftime('%b %Y')} – {last.strftime('%b %Y')})"
        else:
            first = date_type(selected_year, 1, 1)
            last = date_type(selected_year, 12, 31)
            title = f"All Faculty Attendance — Year {selected_year}"
        records_list, _ = attendance_repo.get_records_by_date_map(first, last, selected_department)
    elif view_mode == "semester":
        first = date_type(selected_year, 9, 1)
        last = date_type(selected_year + 1, 8, 31)
        records_list, _ = attendance_repo.get_records_by_date_map(first, last, selected_department)
        title = f"All Faculty Attendance — Academic Year {selected_year}–{selected_year + 1}"
    else:
        records_list, _ = attendance_repo.get_records_by_date_map(
            selected_date, selected_date, selected_department
        )
        title = f"All Faculty Attendance — {selected_date}"

    return export_service.export_day_view_pdf(records_list, title)


@login_required
def holiday_calendar_view(request, user_uuid):
    access_response, staff_profile = check_owner_access(request, user_uuid)
    if access_response:
        return access_response

    today = timezone.localdate()
    selected_year = clamp_year(int(request.GET.get("year", today.year)), today.year)
    selected_month = int(request.GET.get("month", today.month))

    if request.method == "POST":
        action = request.POST.get("action", "add")
        holiday_date = parse_date(request.POST.get("holiday_date", ""))
        holiday_name = request.POST.get("holiday_name", "").strip()
        if action == "add":
            if not holiday_name:
                messages.error(request, "Please enter a holiday name/reason.")
            else:
                holiday_service.add_holiday(holiday_date, holiday_name)
                messages.success(request, f'"{holiday_name}" set for {holiday_date}.')
        elif action == "delete":
            deleted = holiday_service.delete_holiday(holiday_date)
            if deleted:
                messages.success(request, f"Holiday removed for {holiday_date}.")
            else:
                messages.warning(request, f"No holiday found for {holiday_date}.")
        elif action == "toggle_working_day":
            reason = holiday_name
            is_now_working = holiday_service.toggle_working_day(holiday_date, reason)
            if is_now_working:
                messages.success(request, f"{holiday_date} marked as a working day.")
            else:
                messages.success(request, f"{holiday_date} restored to normal.")
        return redirect(f"{request.path}?year={selected_year}&month={selected_month}")

    cal_days = holiday_service.build_calendar_days(selected_year, selected_month)
    month_cal_grid = cal_mod.Calendar(cal_mod.SUNDAY).monthdayscalendar(selected_year, selected_month)
    _, num_days = monthrange(selected_year, selected_month)
    first_day = date_type(selected_year, selected_month, 1)
    last_day = date_type(selected_year, selected_month, num_days)
    prev_month = (first_day - timedelta(days=1)).replace(day=1)
    next_month = (last_day + timedelta(days=1)).replace(day=1)

    context = {
        "user": request.user,
        "sel_year": selected_year, "sel_month": selected_month,
        "month_name": first_day.strftime("%B %Y"),
        "month_cal": month_cal_grid,
        "cal_days": cal_days,
        "prev_month": prev_month,
        "next_month": next_month,
        "today": today,
    }
    return render(request, "Eric/holiday_calendar.html", context)


@login_required
def my_attendance_view(request, user_uuid):
    access_response, _ = check_owner_access(request, user_uuid)
    if access_response:
        return access_response

    today = timezone.localdate()
    now = timezone.localtime()
    sel_year = clamp_year(int(request.GET.get("year", today.year)), today.year)
    sel_month = int(request.GET.get("month", today.month))
    view_mode = request.GET.get("view", "month")

    today_record = attendance_repo.get_staff_attendance_today(request.user, today)
    today_check_in_late = False
    if today_record and today_record.check_in:
        check_in = timezone.localtime(today_record.check_in)
        today_check_in_late = (check_in.hour * 60 + check_in.minute) > EXPECTED_START_MINUTES

    month_records = attendance_repo.get_staff_attendance_month(request.user, sel_year, sel_month)
    total_month = month_records.count()
    mpresent = month_records.filter(check_in__isnull=False).count()
    mtotal_hours = sum((float(r.total_hours_worked) if r.total_hours_worked else 0) for r in month_records)
    mtotal_hours = round(mtotal_hours, 2)

    month_groups = []
    semester_groups = []
    records = []
    sel_date = None
    last3_label = ""
    page_obj = None
    mpresent = 0
    mtotal_hours = 0
    total_month = 0
    prev_month = None
    next_month = None
    month_name = date_type(sel_year, sel_month, 1).strftime("%B %Y")

    if view_mode == "day":
        sel_date = parse_date(request.GET.get("date", "")) or today
        records = attendance_repo.get_staff_attendance_range(request.user, sel_date, sel_date)
    elif view_mode == "year":
        range_option = request.GET.get("range", "12")
        if range_option == "3":
            month_year_pairs = _last_three_calendar_months()
            first_y, first_m = month_year_pairs[0]
            last_y, last_m = month_year_pairs[-1]
            year_start = date_type(first_y, first_m, 1)
            year_end = date_type(last_y, last_m, monthrange(last_y, last_m)[1])
            last3_label = (
                f"{date_type(first_y, first_m, 1).strftime('%b %Y')} – "
                f"{date_type(last_y, last_m, 1).strftime('%b %Y')}"
            )
        else:
            month_year_pairs = [(sel_year, m) for m in range(1, 13)]
            year_start = date_type(sel_year, 1, 1)
            year_end = date_type(sel_year, 12, 31)
        year_records = attendance_repo.get_staff_attendance_range(
            request.user, year_start, year_end
        )
        grouped = {}
        for r in year_records:
            grouped.setdefault(r.date, []).append(r)
        for y, m in month_year_pairs:
            groups = {}
            for day_date, day_recs in grouped.items():
                if day_date.year == y and day_date.month == m:
                    groups[day_date] = day_recs
            month_groups.append({
                "month": m,
                "year": y,
                "label": date_type(y, m, 1).strftime("%B"),
                "count": sum(len(v) for v in groups.values()),
                "groups": groups,
            })
        records = year_records
    elif view_mode == "semester":
        sem_start = date_type(sel_year, 9, 1)
        sem_end = date_type(sel_year + 1, 8, 31)
        sem_records = attendance_repo.get_staff_attendance_range(
            request.user, sem_start, sem_end
        )
        grouped = {}
        for r in sem_records:
            grouped.setdefault(r.date, []).append(r)
        semesters = [
            ("Fall", sel_year, 9, 12, "Fall " + str(sel_year)),
            ("Spring", sel_year + 1, 1, 4, "Spring " + str(sel_year + 1)),
            ("Summer", sel_year + 1, 5, 8, "Summer " + str(sel_year + 1)),
        ]
        for key, yr, m_start, m_end, label in semesters:
            s_start = date_type(yr, m_start, 1)
            s_end = date_type(yr, m_end, monthrange(yr, m_end)[1])
            if s_end > today:
                continue
            months = []
            for m in range(m_start, m_end + 1):
                groups = {}
                for day_date, day_recs in grouped.items():
                    if day_date.year == yr and day_date.month == m:
                        groups[day_date] = day_recs
                months.append({
                    "month": m,
                    "year": yr,
                    "label": date_type(yr, m, 1).strftime("%B"),
                    "count": sum(len(v) for v in groups.values()),
                    "groups": groups,
                })
            semester_groups.append({
                "key": label.replace(" ", "-"),
                "label": label,
                "subtitle": f"{s_start.strftime('%b %d')} – {s_end.strftime('%b %d, %Y')}",
                "count": sum(mg["count"] for mg in months),
                "months": months,
            })
        records = sem_records
    else:
        view_mode = "month"
        records = month_records
        paginator = Paginator(month_records, PAGINATE_BY)
        page_obj = paginator.get_page(request.GET.get("page", 1))
        prev_month = (date_type(sel_year, sel_month, 1) - timedelta(days=1)).replace(day=1)
        next_month = (date_type(sel_year, sel_month, 1) + timedelta(days=31)).replace(day=1)
        if next_month > date_type(today.year, today.month, 1):
            next_month = None

    context = {
        "today": today,
        "now": now,
        "today_record": today_record,
        "today_check_in_late": today_check_in_late,
        "sel_year": sel_year,
        "sel_month": sel_month,
        "month_name": month_name,
        "prev_month": prev_month,
        "next_month": next_month,
        "view_mode": view_mode,
        "records": records,
        "sel_date": sel_date,
        "month_groups": month_groups,
        "semester_groups": semester_groups,
        "last3_label": last3_label,
        "range_option": request.GET.get("range", "12") if view_mode == "year" else "",
        "prev_year": sel_year - 1,
        "next_year": sel_year + 1 if sel_year < today.year else None,
        "page_obj": page_obj,
        "total_month": total_month,
        "mpresent": mpresent,
        "mtotal_hours": mtotal_hours,
    }
    return render(request, "Eric/my_attendance.html", context)


@login_required
def my_attendance_checkin(request):
    record, created = attendance_service.check_in_staff(request.user)
    if created:
        messages.success(request, "Checked in successfully.")
    else:
        if record.check_out:
            messages.info(request, "Already checked in and out today.")
        else:
            messages.info(request, "Already checked in today.")
    return redirect("my_attendance", user_uuid=request.user.uuid)


@login_required
def my_attendance_checkout(request, pk):
    result = attendance_service.check_out_staff(request.user, pk)
    if result:
        messages.success(request, f"Checked out. Hours worked: {result.total_hours_worked}h")
    else:
        messages.warning(request, "Cannot check out.")
    return redirect("my_attendance", user_uuid=request.user.uuid)


def _my_attendance_export_context(request):
    """Resolve view/range and return (records, title) for My Attendance exports.

    Returns None when the caller should fall back to the month export.
    """
    view = request.GET.get("view", "month")
    sel_year = clamp_year(int(request.GET.get("year", timezone.localdate().year)))
    range_option = request.GET.get("range", "12")
    full_name = request.user.get_full_name()

    if view == "day":
        day_str = request.GET.get("date")
        sel_date = date_type.fromisoformat(day_str) if day_str else timezone.localdate()
        records = attendance_repo.get_staff_attendance_range(request.user, sel_date, sel_date)
        return records, f"{full_name} — {sel_date.strftime('%b %d, %Y')}"
    if view == "year":
        if range_option == "3":
            months = _last_three_calendar_months()
            start = date_type(months[0][0], months[0][1], 1)
            end = date_type(months[-1][0], months[-1][1], 1)
            end = end.replace(day=cal_mod.monthrange(end.year, end.month)[1])
            label = f"{MONTH_ABBREVIATIONS[months[0][1]]} {months[0][0]} – {MONTH_ABBREVIATIONS[months[-1][1]]} {months[-1][0]}"
            title = f"{full_name} — Last 3 Months ({label})"
        else:
            start = date_type(sel_year, 1, 1)
            end = date_type(sel_year, 12, 31)
            title = f"{full_name} — Calendar Year {sel_year}"
        records = attendance_repo.get_staff_attendance_range(request.user, start, end)
        return records, title
    if view == "semester":
        start = date_type(sel_year, 9, 1)
        end = date_type(sel_year + 1, 8, 31)
        records = attendance_repo.get_staff_attendance_range(request.user, start, end)
        title = f"{full_name} — Academic Year {sel_year}–{sel_year + 1}"
        return records, title
    return None


@login_required
def my_attendance_export_excel(request, user_uuid):
    access_response, _ = check_owner_access(request, user_uuid)
    if access_response:
        return access_response
    context = _my_attendance_export_context(request)
    if context is not None:
        return export_service.export_my_attendance_range_excel(
            context[0], request.user, context[1]
        )
    sel_year = clamp_year(int(request.GET.get("year", timezone.localdate().year)))
    sel_month = int(request.GET.get("month", timezone.localdate().month))
    records = attendance_repo.get_staff_attendance_month(request.user, sel_year, sel_month)
    return export_service.export_my_attendance_excel(records, request.user, sel_year, sel_month)


@login_required
def my_attendance_export_pdf(request, user_uuid):
    access_response, _ = check_owner_access(request, user_uuid)
    if access_response:
        return access_response
    context = _my_attendance_export_context(request)
    if context is not None:
        return export_service.export_my_attendance_range_pdf(
            context[0], request.user, context[1]
        )
    sel_year = clamp_year(int(request.GET.get("year", timezone.localdate().year)))
    sel_month = int(request.GET.get("month", timezone.localdate().month))
    records = attendance_repo.get_staff_attendance_month(request.user, sel_year, sel_month)
    return export_service.export_my_attendance_pdf(records, request.user, sel_year, sel_month)
