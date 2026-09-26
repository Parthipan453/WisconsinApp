from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Count, Q
from Students.models import StudentProfile, StudentEnrollment, CourseSection, Schedule
from Faculty.leo.models import Attendance, AttendanceSession
from Students.models import Course
from Students.models import Semester


STATUS_CLASS_MAP = {
    "PRESENT": "present",
    "ABSENT": "absent",
    "LATE": "late",
    "LEAVE": "leave",
    "HALF_DAY": "halfday",
    "PERMISSION": "permission",
    "NOT_MARKED": "notmarked",
    "SCHEDULED": "scheduled",
}


@login_required
def attendance_view(request, uuid=None):

    student = get_object_or_404(
        StudentProfile.objects.select_related("user"),
        user=request.user
    )

    today = timezone.localdate()
    date_param = request.GET.get("date")

    if date_param:
        try:
            selected_date = datetime.strptime(date_param, "%Y-%m-%d").date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    attendance_qs = (
        Attendance.objects
        .filter(student=student)
        .select_related(
            "attendance_session",
            "attendance_session__course",
            "attendance_session__section",
            "attendance_session__faculty",
        )
        .order_by("-attendance_session__attendance_date")
    )

    total_classes = attendance_qs.count()
    present_count = attendance_qs.filter(status="PRESENT").count()
    absent_count = attendance_qs.filter(status="ABSENT").count()
    leave_count = attendance_qs.filter(status="LEAVE").count()
    late_count = attendance_qs.filter(status="LATE").count()
    half_day_count = attendance_qs.filter(status="HALF_DAY").count()
    permission_count = attendance_qs.filter(status="PERMISSION").count()

    attended_classes = present_count + (half_day_count * 0.5)
    attendance_pct = round((attended_classes / total_classes) * 100, 1) if total_classes else 0
# ================= DONUT DATA =================

    present_pct = round((present_count / total_classes) * 100, 1) if total_classes else 0
    absent_pct = round((absent_count / total_classes) * 100, 1) if total_classes else 0
    late_pct = round((late_count / total_classes) * 100, 1) if total_classes else 0
    leave_pct = round((leave_count / total_classes) * 100, 1) if total_classes else 0
    halfday_pct = round((half_day_count / total_classes) * 100, 1) if total_classes else 0
    permission_pct = round((permission_count / total_classes) * 100, 1) if total_classes else 0
    donut_circumference = 440
    donut_offset = round(donut_circumference - (donut_circumference * attendance_pct / 100), 2)

    overall = {
        "total_classes": total_classes,
        "present_count": present_count,
        "absent_count": absent_count,
        "leave_count": leave_count,
        "late_count": late_count,
        "half_day_count": half_day_count,
        "permission_count": permission_count,

        "attendance_pct": attendance_pct,

        "present_pct": present_pct,
        "absent_pct": absent_pct,
        "late_pct": late_pct,
        "leave_pct": leave_pct,
        "halfday_pct": halfday_pct,
        "permission_pct": permission_pct,
    }

    today_records = attendance_qs.filter(attendance_session__attendance_date=selected_date)
    today_ctx = {
        "present_count": today_records.filter(status="PRESENT").count(),
        "absent_count": today_records.filter(status="ABSENT").count(),
        "leave_count": today_records.filter(status="LEAVE").count(),
        "late_count": today_records.filter(status="LATE").count(),
        "half_day_count": today_records.filter(status="HALF_DAY").count(),
        "permission_count": today_records.filter(status="PERMISSION").count(),
    }

    

    day_of_week_map = {
        0: "MON",
        1: "TUE",
        2: "WED",
        3: "THU",
        4: "FRI",
        5: "SAT",
        6: "SUN",
    }

    selected_dow = day_of_week_map[selected_date.weekday()]

    enrollments = (
        StudentEnrollment.objects
        .filter(
            student=student,
            enrollment_status__in=["FULL_TIME", "PART_TIME"]
        )
        .select_related(
            "section_id",
            "section_id__course",
            "semester",
        )
    )

    # Attendance records for the selected date
    today_records = attendance_qs.filter(
        attendance_session__attendance_date=selected_date
    )

    today_by_section = {
        (record.attendance_session.section_id, record.attendance_session.schedule_id): record
        for record in today_records
        if record.attendance_session and record.attendance_session.section_id
    }

    selected_date_string = selected_date.isoformat()

    day_sessions = []

    for enrollment in enrollments:

        section = enrollment.section_id

        if not section or not section.course:
            continue

        schedules = Schedule.objects.filter(section_id=section)

        # Only schedules that actually list this date as a class date
        matched_schedules = [
            s for s in schedules
            if selected_date_string in (s.dates or [])
        ]

        for schedule in matched_schedules:

            record = today_by_section.get((section.section_id, schedule.pk))

            if record:
                status = record.status
                status_class = STATUS_CLASS_MAP.get(
                    record.status,
                    "notmarked"
                )
                remarks = record.remarks
            else:
                status = "SCHEDULED" if selected_date > today else "NOT_MARKED"
                status_class = (
                    "scheduled"
                    if selected_date > today
                    else "notmarked"
                )
                remarks = None

            day_sessions.append({
                "course": section.course,
                "course_name": section.course.course_name,
                "course_code": section.course.course_code,

                "section": section,
                "section_number": section.section_number,

                "faculty": section.faculty_name,

                "status": status,
                "status_class": status_class,
                "remarks": remarks,

                "attendance_date": selected_date,

                "start_time": schedule.start_time,
                "end_time": schedule.end_time,

                "room": schedule.room,
                "building": schedule.building,
                "is_online": schedule.is_online,
            })

    day_sessions.sort(
        key=lambda x: x["start_time"]
    )
    subject_data = {}
    for record in attendance_qs:
        session = record.attendance_session
        if not session or not session.course:
            continue
        course = session.course
        course_id = course.pk
        if course_id not in subject_data:
            subject_data[course_id] = {
                "name": course.course_name,
                "course_code": course.course_code,
                "total": 0,
                "attended": 0,
            }
        subject_data[course_id]["total"] += 1

        if record.status == "PRESENT":
            subject_data[course_id]["attended"] += 1

        elif record.status == "HALF_DAY":
            subject_data[course_id]["attended"] += 0.5

    subject_attendance = []
    for subject in subject_data.values():
        pct = round(subject["attended"] / subject["total"] * 100, 1) if subject["total"] else 0
        if pct >= 75:
            bar_color = "success"
        elif pct >= 60:
            bar_color = "primary"
        else:
            bar_color = "danger"
        subject_attendance.append({
            "name": subject["name"],
            "course_code": subject["course_code"],
            "pct": pct,
            "bar_color": bar_color,
        })

    attendance_history = []

    for record in attendance_qs[:10]:
        session = record.attendance_session

        if not session:
            continue

        schedule = session.schedule  # use the actual schedule this session was taken for

        faculty_name = ""

        if session.faculty:
            faculty_name = (
                getattr(session.faculty, "preferred_name", None)
                or session.faculty.user.get_full_name()
            )

        attendance_history.append({
            "date": session.attendance_date,
            "course": session.course,
            "course_name": session.course.course_name,
            "course_code": session.course.course_code,
            "faculty_name": faculty_name,
            "status": record.status,
            "status_class": STATUS_CLASS_MAP.get(record.status, "present"),
            "remarks": record.remarks,
            "start_time": getattr(schedule, "start_time", None),
            "end_time": getattr(schedule, "end_time", None),
        })

    academic_year_values = (
        Semester.objects
        .values_list("academic_year", flat=True)
        .distinct()
        .order_by("-academic_year")
    )
    academic_years = [{"value": y, "label": y} for y in academic_year_values]

    all_subjects = [{"id": cid, "name": data["name"]} for cid, data in subject_data.items()]

    context = {
        "student": student,
        "overall": overall,
        "today": today_ctx,
        "selected_date": selected_date,
        "day_sessions": day_sessions,
        "subject_attendance": subject_attendance,
        "attendance_history": attendance_history,
        "academic_years": academic_years,
        "all_subjects": all_subjects,
        "late_count": late_count,
        "half_day_count": half_day_count,
        "permission_count": permission_count,
    }

    return render(request, "Academic/Elsa/attendance.html", context)

import csv
from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle


@login_required
def export_attendance(request):
    student = get_object_or_404(
        StudentProfile.objects.select_related("user"),
        user=request.user
    )

    subject_param = request.GET.get("subject", "all")
    from_date_param = request.GET.get("from_date")
    to_date_param = request.GET.get("to_date")
    export_format = request.GET.get("format", "csv").lower()

    records = (
        Attendance.objects
        .filter(student=student)
        .select_related(
            "attendance_session",
            "attendance_session__course",
            "attendance_session__section",
            "attendance_session__faculty",
        )
        .order_by("-attendance_session__attendance_date")
    )

    if subject_param and subject_param != "all":
        try:
            course_id = int(subject_param)
            records = records.filter(attendance_session__course_id=course_id)
        except (ValueError, TypeError):
            pass

    if from_date_param:
        try:
            from_date = datetime.strptime(from_date_param, "%Y-%m-%d").date()
            records = records.filter(attendance_session__attendance_date__gte=from_date)
        except ValueError:
            pass

    if to_date_param:
        try:
            to_date = datetime.strptime(to_date_param, "%Y-%m-%d").date()
            records = records.filter(attendance_session__attendance_date__lte=to_date)
        except ValueError:
            pass

    headers = ["Date", "Subject", "Course Code", "Faculty", "Time", "Status", "Remarks"]
    rows = []

    for record in records:
        session = record.attendance_session
        if not session:
            continue

        schedule = session.schedule  # use the actual schedule this session was taken for

        faculty_name = "—"
        if session.faculty:
            faculty_name = (
                getattr(session.faculty, "preferred_name", None)
                or session.faculty.user.get_full_name()
            )

        time_str = "—"
        if schedule:
            time_str = f"{schedule.start_time.strftime('%I:%M %p')} - {schedule.end_time.strftime('%I:%M %p')}"

        rows.append([
            session.attendance_date.strftime("%d %b %Y"),
            session.course.course_name if session.course else "—",
            session.course.course_code if session.course else "—",
            faculty_name,
            time_str,
            record.get_status_display(),
            record.remarks or "—",
        ])

    filename_base = f"{student.student_number}_attendance"

    if export_format == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename_base}.csv"'
        writer = csv.writer(response)
        writer.writerow(headers)
        writer.writerows(rows)
        return response

    if export_format == "xlsx":
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Attendance"
        worksheet.append(headers)
        for row in rows:
            worksheet.append(row)

        column_widths = {"A": 14, "B": 26, "C": 14, "D": 20, "E": 18, "F": 14, "G": 24}
        for column, width in column_widths.items():
            worksheet.column_dimensions[column].width = width

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename_base}.xlsx"'
        workbook.save(response)
        return response

    if export_format == "pdf":
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename_base}.pdf"'

        document = SimpleDocTemplate(
            response,
            pagesize=landscape(A4),
            rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25,
        )

        table_data = [headers] + rows
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#c5050c")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))

        document.build([table])
        return response

    return HttpResponse("Invalid export format.", status=400)