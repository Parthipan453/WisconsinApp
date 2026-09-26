from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from Faculty.models import FacultyCourseAssignment
from Admin.Colleges.models import AcademicTerm
from Students.models import Schedule, CourseSection, Semester
from Faculty.leo.models import Attendance, AttendanceSession
from django.utils import timezone  

TERM_TYPE_MAP = {
    "FALL": "FA",
    "SPRING": "SP",
    "SUMMER": "SU",
    "WINTER": "WI",
}

def _get_current_semester():
    today = timezone.localdate()
    current_term = (
        AcademicTerm.objects
        .filter(status="ACTIVE", start_date__lte=today, end_date__gte=today)
        .order_by("start_date")
        .first()
    )
    if current_term:
        semester_type = TERM_TYPE_MAP.get(current_term.term_name)
        academic_year = int(current_term.academic_year.split("-")[0])
        semester = Semester.objects.filter(
            semester_type=semester_type,
            academic_year=academic_year,
        ).first()
        if semester:
            return semester
    current = Semester.objects.filter(is_current=True).first()
    if current:
        return current
    current = (
        Semester.objects
        .filter(start_date__lte=today, end_date__gte=today)
        .first()
    )
    if current:
        return current
    return Semester.objects.order_by("-start_date").first()


@login_required
def student_attendance_record(request, uuid):
    current_semester = _get_current_semester()
    current_semester_id = str(current_semester.pk) if current_semester else ""
    current_semester_label = (
        f"{current_semester.semester_type} {current_semester.academic_year}" if current_semester else ""
    )

    sections = (
        CourseSection.objects
        .select_related("course", "course__department", "semester_id")
        .annotate(student_count=Count("enrollments"))
    )

    courses_payload = []

    for section in sections:
        if not section.course:
            continue

        assignment = (
            FacultyCourseAssignment.objects
            .filter(course_section_id=section.section_id)
            .select_related("faculty", "faculty__user")
            .first()
        )
        faculty_name = assignment.faculty.user.get_full_name() if assignment and assignment.faculty else "Not assigned"
        faculty_id = str(assignment.faculty_id) if assignment else ""

        department = section.course.department
        department_name = department.department_name if department else "Not assigned"
        department_id = str(department.pk) if department else ""

        semester = section.semester_id
        semester_name = (
            f"{semester.semester_type} {semester.academic_year}" if semester else "Not assigned"
        )
        semester_id = str(semester.pk) if semester else ""

        schedule = Schedule.objects.filter(section_id=section.section_id).first()
        day = schedule.get_day_of_week_display() if schedule else ""
        time_range = (
            f"{schedule.start_time.strftime('%I:%M %p')} - {schedule.end_time.strftime('%I:%M %p')}"
            if schedule and schedule.start_time and schedule.end_time else ""
        )
        room = schedule.room if schedule else (section.room_number or "")

        # ---------------- ALL closed sessions for this section, not just the latest ----------------
        sessions = (
            AttendanceSession.objects
            .filter(section_id=section.section_id, status="CLOSED")
            .order_by("attendance_date")
        )
        sessions_payload = [
            {"id": s.id, "date": s.attendance_date.isoformat()}
            for s in sessions
        ]

        all_records = (
            Attendance.objects
            .filter(attendance_session__in=sessions)
            .select_related(
                "student", "student__user",
                "student__academic_profile", "student__academic_profile__program",
                "attendance_session",
            )
            .order_by("student__student_number", "attendance_session__attendance_date")
        )

        # Group every record by student -> {date: status}
        student_records = {}
        for record in all_records:
            student = record.student
            sid = student.id
            if sid not in student_records:
                student_records[sid] = {"student": student, "records": {}}
            date_iso = record.attendance_session.attendance_date.isoformat()
            student_records[sid]["records"][date_iso] = record.status.lower().replace("_", "-")

        students_payload = []
        for sid, data in student_records.items():
            student = data["student"]
            records = data["records"]
            name = student.preferred_name or student.user.get_full_name()

            academic_profile = getattr(student, "academic_profile", None)
            program = academic_profile.program if academic_profile else None
            program_name = program.program_name if program else "Not assigned"
            program_id = str(program.pk) if program else ""

            total_sessions = len(records)
            present_count = sum(1 for status in records.values() if status == "present")
            overall_percent = round((present_count / total_sessions) * 100) if total_sessions else 0
            latest_date = max(records.keys()) if records else None
            latest_status = records.get(latest_date, "") if latest_date else ""

            students_payload.append({
                "id": student.id,
                "name": name,
                "rollNo": student.student_number,
                "status": latest_status,
                "date": latest_date or "",
                "program": program_name,
                "programId": program_id,
                "attendancePercent": overall_percent,
                "totalSessions": total_sessions,
                "presentCount": present_count,
                "records": records,
            })

        students_payload.sort(key=lambda s: s["rollNo"])

        courses_payload.append({
            "id": section.section_id,
            "name": section.course.course_name,
            "subject": section.course.course_code,
            "section": section.section_number,
            "faculty": faculty_name,
            "facultyId": faculty_id,
            "code": section.course.course_code,
            "department": department_name,
            "departmentId": department_id,
            "semester": semester_name,
            "semesterId": semester_id,
            "day": day,
            "schedule": time_range,
            "room": room,
            "sessions": sessions_payload,
            "students": students_payload,
        })

    context = {
        "uuid": uuid,
        "courses_json": courses_payload,
        "current_semester_id": current_semester_id,
        "current_semester_label": current_semester_label,
    }
    return render(request, "Jordan/student_attendance.html", context)

@require_http_methods(["GET"])
def get_course_attendance(request, course_id):
    return JsonResponse({
        'status': 'success',
        'data': {
            # Course attendance data
        }
    })

@require_http_methods(["POST"])
def update_attendance(request):
    # In real implementation, update database
    data = json.loads(request.body)
    student_id = data.get('student_id')
    status = data.get('status')
    
    return JsonResponse({
        'status': 'success',
        'message': 'Attendance updated successfully'
    })