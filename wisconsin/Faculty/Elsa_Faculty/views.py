# ============================================================
# Django Core
# ============================================================
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Avg
from datetime import date, timedelta

# ============================================================
# Python Standard Library
# ============================================================
import csv
import json
from decimal import Decimal, InvalidOperation

# ============================================================
# Excel
# ============================================================
from openpyxl import Workbook


# ============================================================
# PDF
# ============================================================
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle


# ============================================================
# Application Models
# ============================================================
from Admin.Dominic.models import Notification as AdminBellNotification
from Admin.Elsa_admin.models import *
from Faculty.models import *
from Staff.models import Notification
from Students.models import *
from Faculty.leo.models import Attendance, AttendanceSession
from Admin.Colleges.models import ProgramCourse

# ============================================================
# Notifications
# ============================================================
from notifications.utils import notify_admins


# ============================================================================================================
# Notification Functions
# ============================================================================================================
def _notify_staff_grade_entered(faculty, grade):
    faculty_name = faculty.user.get_full_name() or faculty.user.username
    student_name = grade.student.preferred_name or grade.student.user.get_full_name()
    message = (
        f"{faculty_name} entered a grade for {student_name} "
        f"({grade.student.student_number}) in {grade.course.course_code}."
    )
    link = f"{reverse('gradebook', args=[faculty.user.uuid])}?course={grade.course.course_id}"
    for staff_user in get_user_model().objects.filter(is_staff=True):
        Notification.objects.create(
            user=staff_user,
            title="Grade Entered",
            message=message,
            notification_type="INFO",
            link=link,
        )


def _notify_staff_grades_entered_bulk(faculty, grades):
    faculty_name = faculty.user.get_full_name() or faculty.user.username
    course = grades[0].course
    message = (
        f"{faculty_name} entered grades for {len(grades)} student(s) in {course.course_code}."
    )
    link = f"{reverse('gradebook', args=[faculty.user.uuid])}?course={course.course_id}"
    for staff_user in get_user_model().objects.filter(is_staff=True):
        Notification.objects.create(
            user=staff_user,
            title="Grades Entered",
            message=message,
            notification_type="INFO",
            link=link,
        )


def _notify_staff_grades_finalized(faculty, course, section_id, count):
    faculty_name = faculty.user.get_full_name() or faculty.user.username
    section_label = f" (Section {section_id})" if section_id else ""
    message = (
        f"{faculty_name} finalized grades for {count} student(s) in "
        f"{course.course_code}{section_label}."
    )
    link = f"{reverse('gradebook', args=[faculty.user.uuid])}?course={course.course_id}"
    for staff_user in get_user_model().objects.filter(is_staff=True):
        Notification.objects.create(
            user=staff_user,
            title="Grades Finalized",
            message=message,
            notification_type="SUCCESS",
            link=link,
        )
# ============================================================================================================
# ============================================================================================================
@login_required
def course_grade_dashboard(request):
    faculty = get_object_or_404(FacultyProfile, user=request.user)
    assignments = FacultyCourseAssignment.objects.filter(faculty=faculty)
    section_ids = assignments.values_list("course_section_id", flat=True)
    sections = (
        CourseSection.objects
        .filter(section_id__in=section_ids)
        .select_related("course", "semester_id")
        .annotate(student_count=Count("enrollments"))
    )
    section_dict = {section.section_id: section for section in sections}
    course_map = {}

    for assignment in assignments:
        section = section_dict.get(assignment.course_section_id)
        if not section or not section.course:
            continue
        course = section.course
        enrolled_count = section.student_count

        section_student_ids = StudentEnrollment.objects.filter(
            section_id=section.section_id
        ).exclude(enrollment_status__in=["WITHDRAWN"]).values_list("student_id", flat=True)

        section_grades_qs = CourseGrade.objects.filter(
            course=course,
            instructor_id=faculty.employee_id,
            student_id__in=section_student_ids,
        )
        section_is_finalized = section_grades_qs.exists() and not section_grades_qs.filter(is_finalized=False).exists()

        section_info = {
            "section_id": section.section_id,
            "section_number": section.section_number,
            "section_type": section.get_section_type_display(),
            "semester": str(section.semester_id) if section.semester_id else "—",
            "enrolled_count": enrolled_count,
            "is_finalized": section_is_finalized,
        }
        if course.course_id not in course_map:
            course_map[course.course_id] = {
                "course_id": course.course_id,
                "course_code": course.course_code,
                "course_name": course.course_name,
                "course_obj": course,
                "sections": [],
                "enrolled_count": 0,
            }
        card = course_map[course.course_id]
        card["sections"].append(section_info)
        card["enrolled_count"] += enrolled_count

    for card in course_map.values():
        graded_count = CourseGrade.objects.filter(
            course=card["course_obj"],
            instructor_id=faculty.employee_id,
        ).exclude(numeric_score__isnull=True).count()
        card["graded_count"] = graded_count
        card["pending_count"] = max(card["enrolled_count"] - graded_count, 0)
        del card["course_obj"]

    course_cards = list(course_map.values())
    paginator = Paginator(course_cards, 12)
    course_page = paginator.get_page(request.GET.get("page"))
    context = {
        "user": request.user,
        "total_courses": len(course_cards),
        "total_students": sum(c["enrolled_count"] for c in course_cards),
        "total_graded": sum(c["graded_count"] for c in course_cards),
        "total_pending": sum(c["pending_count"] for c in course_cards),
        "course_cards": course_page,
        "course_page": course_page,
    }
    return render(request, "teaching/Elsa/course_grade_dashboard.html", context)
# ============================================================================================================
def resolve_grade_scale(score):
    if score is None:
        return None
    return GradeScale.objects.filter(minimum_percentage__lte=score,maximum_percentage__gte=score,).first()
# ============================================================================================================
@login_required
def course_grade(request):
    faculty = get_object_or_404(FacultyProfile, user=request.user)
    course_id = request.GET.get("course")
    section_id = request.GET.get("section")
    page_number = request.GET.get("page")
    selected_course = get_object_or_404(Course, course_id=course_id) if course_id else None
    if not selected_course:
        return render(request, "teaching/Elsa/course_grade.html", {
            "selected_course": None, "grades": [], "instructor": faculty,
            "semester": None, "total_students": 0, "graded_count": 0,
            "pending_count": 0, "progress": 0,
        })

    section_filter = {"course": selected_course}
    if section_id:
        section_filter["section_id"] = section_id
    sections = CourseSection.objects.filter(**section_filter)

    selected_section = None
    if section_id:
        selected_section = sections.filter(section_id=section_id).first()

    enrollments = (
        StudentEnrollment.objects
        .filter(section_id__in=sections)
        .exclude(enrollment_status__in=["WITHDRAWN"])
        .select_related("student", "semester")
    )

    for e in enrollments:
        CourseGrade.objects.get_or_create(
            student=e.student,
            course=selected_course,
            semester=e.semester,
            defaults={"instructor_id": faculty.employee_id},
        )

    grades_qs = CourseGrade.objects.select_related(
        "student", "course", "semester", "grade_scale"
    ).filter(course=selected_course, instructor_id=faculty.employee_id)

    if section_id:
        student_ids = enrollments.values_list("student_id", flat=True)
        grades_qs = grades_qs.filter(student_id__in=student_ids)

    all_finalized = grades_qs.exists() and not grades_qs.filter(is_finalized=False).exists()

    paginator = Paginator(grades_qs, 10)
    grades = paginator.get_page(page_number)
    student_numbers = [g.student.student_number for g in grades]

    latest_requests = {}
    for req in GradeChangeRequest.objects.filter(
        student_id__in=student_numbers,
        course_id=selected_course.course_code,
    ).order_by("student_id", "-request_date"):
        if req.student_id not in latest_requests:
            latest_requests[req.student_id] = req

    for g in grades:
        latest_req = latest_requests.get(g.student.student_number)
        if g.is_finalized:
            g.ui_state = "finalized"        
        elif g.numeric_score is None:
            g.ui_state = "unsaved"
        elif latest_req and latest_req.approval_status == "Pending":
            g.ui_state = "pending"
        else:
            g.ui_state = "graded"

    total_students = paginator.count
    graded_count = grades_qs.exclude(numeric_score__isnull=True).count()
    pending_count = total_students - graded_count
    progress = round((graded_count / total_students) * 100) if total_students else 0
    current_semester = sections.first().semester_id if sections.exists() else None
    pending_review_count = sum(1 for g in grades if g.ui_state == "pending")
    context = {
        "selected_course": selected_course,
        "selected_section": selected_section,
        "grades": grades,
        "instructor": faculty,
        "semester": current_semester,
        "sections": sections,
        "section_id": section_id,
        "total_students": total_students,
        "graded_count": graded_count,
        "pending_count": pending_count,
        "pending_review_count": pending_review_count,  
        "progress": progress,
        "all_finalized": all_finalized,
    }
    return render(request, "teaching/Elsa/course_grade.html", context)
# ============================================================================================================
@login_required
def save_course_grades_bulk(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    faculty = get_object_or_404(FacultyProfile, user=request.user)
    try:
        payload = json.loads(request.body)
        entries = payload.get("entries", [])
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"success": False, "message": "Invalid request body"}, status=400)
    if not entries:
        return JsonResponse({"success": False, "message": "No grades selected"}, status=400)
    results = []
    updated = 0
    first_time_saves = []

    for entry in entries:
        grade_id = entry.get("grade_id")
        raw_score = entry.get("numeric_score")
        try:
            grade = CourseGrade.objects.get(id=grade_id, instructor_id=faculty.employee_id)
            if grade.is_finalized:
                results.append({"grade_id": grade_id, "success": False, "message": "Finalized — cannot edit"})
                continue
        except CourseGrade.DoesNotExist:
            results.append({"grade_id": grade_id, "success": False, "message": "Not found"})
            continue
        try:
            score = Decimal(str(raw_score))
        except (InvalidOperation, TypeError):
            results.append({"grade_id": grade_id, "success": False, "message": "Invalid score"})
            continue
        if score < 0 or score > 100:
            results.append({"grade_id": grade_id, "success": False, "message": "Score must be 0–100"})
            continue

        was_first_save = grade.numeric_score is None
        grade.numeric_score = score
        grade.grade_scale = resolve_grade_scale(score)
        grade.save()
        updated += 1
        if was_first_save:
            first_time_saves.append(grade)
        results.append({
            "grade_id": grade_id,
            "success": True,
            "numeric_score": str(grade.numeric_score),
            "letter_grade": grade.grade_scale.letter_grade if grade.grade_scale else "—",
            "grade_points": str(grade.grade_scale.grade_points) if grade.grade_scale else "—",
            "grade_date": grade.grade_date.strftime("%Y-%m-%d"),
        })

    if first_time_saves:
        _notify_staff_grades_entered_bulk(faculty, first_time_saves)

    return JsonResponse({
        "success": True,
        "updated": updated,
        "results": results,
    })
# ============================================================================================================
@login_required
def export_grades(request):
    faculty = get_object_or_404(FacultyProfile, user=request.user)
    course_id = request.GET.get("course")
    export_format = request.GET.get("format", "csv").lower()
    if not course_id:
        return HttpResponse("Course is required.", status=400)
    selected_course = get_object_or_404(
        Course,
        course_id=course_id
    )
    grades = (
        CourseGrade.objects
        .select_related(
            "student",
            "course",
            "grade_scale"
        )
        .filter(
            course=selected_course,
            instructor_id=faculty.employee_id
        )
        .order_by("student__student_number")
    )
    headers = [
        "#",
        "Student ID",
        "Student Name",
        "Numeric Score",
        "Letter Grade",
        "Grade Points",
        "Grade Date",
    ]
    rows = []
    for index, grade in enumerate(grades, start=1):
        student_name = (
            grade.student.preferred_name
            or grade.student.user.get_full_name()
        )
        rows.append([
            index,
            grade.student.student_number,
            student_name,
            grade.numeric_score if grade.numeric_score is not None else "—",
            grade.grade_scale.letter_grade if grade.grade_scale else "—",
            grade.grade_scale.grade_points if grade.grade_scale else "—",
            grade.grade_date.strftime("%d-%m-%Y")
            if grade.grade_date else "—",
        ])
    # ---------------- CSV ----------------
    if export_format == "csv":
        response = HttpResponse(
            content_type="text/csv"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{selected_course.course_code}_grades.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(headers)
        writer.writerows(rows)
        return response
    # ---------------- EXCEL ----------------
    if export_format == "xlsx":
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Grades"
        worksheet.append(headers)
        for row in rows:
            worksheet.append(row)
        column_widths = {
            "A": 6,
            "B": 18,
            "C": 30,
            "D": 18,
            "E": 15,
            "F": 15,
            "G": 15,
        }
        for column, width in column_widths.items():
            worksheet.column_dimensions[column].width = width
        response = HttpResponse(
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            )
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{selected_course.course_code}_grades.xlsx"'
        )
        workbook.save(response)
        return response
    # ---------------- PDF ----------------
    if export_format == "pdf":
        response = HttpResponse(
            content_type="application/pdf"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{selected_course.course_code}_grades.pdf"'
        )
        document = SimpleDocTemplate(
            response,
            pagesize=landscape(A4),
            rightMargin=25,
            leftMargin=25,
            topMargin=25,
            bottomMargin=25,
        )
        table_data = [headers] + rows
        table = Table(
            table_data,
            repeatRows=1
        )
        table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.grey
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER"
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
            ])
        )
        document.build([table])
        return response
    return HttpResponse(
        "Invalid export format.",
        status=400
    )
# ============================================================================================================
@login_required
def save_course_grade(request, grade_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    faculty = get_object_or_404(FacultyProfile, user=request.user)
    grade = get_object_or_404(CourseGrade, id=grade_id)
    if grade.instructor_id != faculty.employee_id:
        return JsonResponse({"success": False, "message": "Not your student"}, status=403)
    if grade.is_finalized:
        return JsonResponse({"success": False, "message": "Grades are finalized and can no longer be edited directly."}, status=403)    
    try:
        score = Decimal(request.POST.get("numeric_score"))
    except (InvalidOperation, TypeError):
        return JsonResponse({"success": False, "message": "Invalid score"}, status=400)
    if score < 0 or score > 100:
        return JsonResponse({"success": False, "message": "Score must be 0–100"}, status=400)
    was_first_save = grade.numeric_score is None
    grade.numeric_score = score
    grade.grade_scale = resolve_grade_scale(score)
    grade.save()
    if was_first_save:
        _notify_staff_grade_entered(faculty, grade)
    return JsonResponse({
        "success": True,
        "numeric_score": str(grade.numeric_score), 
        "letter_grade": grade.grade_scale.letter_grade if grade.grade_scale else "—",
        "grade_points": str(grade.grade_scale.grade_points) if grade.grade_scale else "—",
        "grade_date": grade.grade_date.strftime("%Y-%m-%d"),
    })
# ============================================================================================================
@login_required
def update_request(request):
    faculty = get_object_or_404(FacultyProfile, user=request.user)
    grades = GradeScale.objects.all()
    errors = {}
    old = {}
    prefill_record = None
    view_history = request.GET.get("view") == "history"
    course_id_param = request.GET.get("course_id", "").strip()
    section_id_param = request.GET.get("section_id", "").strip() 
    if request.method == "POST":
        old = request.POST
        student_id = request.POST.get("student_id", "").strip()
        course_id = request.POST.get("course_id", "").strip()
        section_id_param = request.POST.get("section_id", "").strip()
        current_grade = request.POST.get("current_grade")
        requested_grade = request.POST.get("requested_grade")
        reason = request.POST.get("reason", "").strip()
        current_score = requested_score = None
        try:
            current_score = Decimal(request.POST.get("current_score"))
            if not (0 <= current_score <= 100):
                errors["current_score"] = "Current score must be between 0 and 100."
        except (InvalidOperation, TypeError):
            errors["current_score"] = "Enter a valid current score."
        try:
            requested_score = Decimal(request.POST.get("requested_score"))
            if not (0 <= requested_score <= 100):
                errors["requested_score"] = "Requested score must be between 0 and 100."
        except (InvalidOperation, TypeError):
            errors["requested_score"] = "Enter a valid requested score."
        if not student_id:
            errors["student_id"] = "Student ID is missing."
        if not course_id:
            errors["course_id"] = "Course ID is missing."
        if not requested_grade:
            errors["requested_grade"] = "Select the requested grade."
        if not reason:
            errors["reason"] = "Reason is required."
        if not errors and GradeChangeRequest.objects.filter(
            student_id=student_id, course_id=course_id, approval_status="Pending"
        ).exists():
            errors["duplicate"] = "A pending request already exists for this student and course."
 
        if not errors:
            new_request = GradeChangeRequest.objects.create(
                student_id=student_id,
                course_id=course_id,
                instructor_id=faculty.employee_id,
                current_score=current_score,
                requested_score=requested_score,
                current_grade_id=current_grade or None,
                requested_grade_id=requested_grade,
                reason=reason,
            )
    
            admin_link = reverse('score_request')
            faculty_display_name = faculty.user.get_full_name() or faculty.user.username
            User = get_user_model()
            admin_users = (User.objects.filter(is_admin=True) | User.objects.filter(is_super_admin=True)).distinct()
            Notification.objects.bulk_create([
                Notification(
                    user=admin_user,
                    title="New Grade Change Request",
                    message=f"{faculty_display_name} requested a grade change for {student_id} in {course_id}.",
                    notification_type="REQUEST",
                    link=admin_link,
                ) for admin_user in admin_users
            ])
            student_obj = StudentProfile.objects.select_related("user").filter(
                student_number=student_id
            ).first()
            course_obj = Course.objects.filter(course_code=course_id).first()
 
            notify_admins({
                "title": "New Grade Change Request",
                "message": f"{faculty_display_name} requested a grade change for {student_id} in {course_id}.",
                "request_id": new_request.request_id,
                "faculty_employee_id": faculty.employee_id,
                "faculty_name": faculty_display_name,
                "student_id": student_id,
                "student_name": f"{student_obj.user.first_name} {student_obj.user.last_name}" if student_obj else "",
                "course_code": course_id,
                "course_name": course_obj.course_name if course_obj else "",
                "current_score": f"{current_score:.2f}",
                "requested_score": f"{requested_score:.2f}",
                "reason": reason,
                "approve_url": reverse('approve_request', args=[new_request.request_id]),
                "reject_url": reverse('reject_request', args=[new_request.request_id]),
            }, event="grade_request_created")
            course_display = f"{course_id} ({course_obj.course_name})" if course_obj else course_id
    
            AdminBellNotification.objects.create(
                recipient=None,
                notification_type="ANNOUNCEMENT",
                event="new", 
                message=f"New grade change request: {faculty_display_name} requested a change for "
                        f"{student_id} in {course_display} (from {current_score} to {requested_score}).",
                icon="clipboard-list", 
                link_url=admin_link,
            )  
            course_obj = Course.objects.filter(course_code=course_id).first()

            if course_obj:
                redirect_url = f"{reverse('course_grade')}?course={course_obj.course_id}"

                if section_id_param:
                    redirect_url += f"&section={section_id_param}"

                return redirect(redirect_url)

            return redirect("update_request")

    else:
        student_number = request.GET.get("student_id", "").strip()
        if student_number and course_id_param and not view_history:
            prefill_record = (
                CourseGrade.objects
                .select_related("student", "student__user", "course", "grade_scale")
                .filter(
                    student__student_number=student_number,
                    course__course_code=course_id_param,
                    instructor_id=faculty.employee_id,
                )
                .first()
            )
            if prefill_record:
                old = {
                    "student_id": prefill_record.student.student_number,
                    "course_id": prefill_record.course.course_code,
                    "current_score": prefill_record.numeric_score,
                    "current_grade": prefill_record.grade_scale_id or "",
                }
            else:
                errors["lookup"] = "No matching grade record was found for that student and course."
    request_list = GradeChangeRequest.objects.filter(
        instructor_id=faculty.employee_id
    ).order_by("-request_date")
    if course_id_param:
        request_list = request_list.filter(course_id=course_id_param)
    if section_id_param:
        section_student_ids = StudentEnrollment.objects.filter(
            section_id=section_id_param
        ).values_list("student__student_number", flat=True)
        request_list = request_list.filter(student_id__in=section_student_ids)    
    paginator = Paginator(request_list, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    back_course = Course.objects.filter(course_code=course_id_param).first() if course_id_param else None
    context = {
        "requests": page_obj,
        "grades": grades,
        "errors": errors,
        "old": old,
        "prefill_record": prefill_record,
        "view_history": view_history,
        "course_id_param": course_id_param,
        "section_id_param": section_id_param,
        "back_course": back_course,
    }
    return render(request, "teaching/Elsa/update_request.html", context)

# ============================================================================================================
@login_required
def finalize_course_grades(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    faculty = get_object_or_404(FacultyProfile, user=request.user)
    course_id = request.POST.get("course_id")
    section_id = request.POST.get("section_id")
    selected_course = get_object_or_404(Course, course_id=course_id)

    grades_qs = CourseGrade.objects.filter(
        course=selected_course,
        instructor_id=faculty.employee_id,
    )
    if section_id:
        student_ids = StudentEnrollment.objects.filter(
            section_id=section_id
        ).values_list("student_id", flat=True)
        grades_qs = grades_qs.filter(student_id__in=student_ids)

    missing = grades_qs.filter(numeric_score__isnull=True).count()
    if missing > 0:
        return JsonResponse({
            "success": False,
            "message": f"{missing} student(s) still have no score entered."
        }, status=400)

    student_numbers = grades_qs.values_list("student__student_number", flat=True)
    pending_requests = GradeChangeRequest.objects.filter(
        student_id__in=student_numbers,
        course_id=selected_course.course_code,
        approval_status="Pending",
    ).count()
    if pending_requests > 0:
        return JsonResponse({
            "success": False,
            "message": f"{pending_requests} student(s) have a pending grade change request. Resolve those before finalizing."
        }, status=400)

    updated = grades_qs.update(is_finalized=True, finalized_at=timezone.now())
    _notify_staff_grades_finalized(faculty, selected_course, section_id, updated)
    return JsonResponse({"success": True, "updated": updated})
# ==========================================================================================================================================================
# ==========================================================================================================================================================
# ==========================================================================================================================================================
def _get_current_semester():
    """
    Resolve "the current semester" for defaulting the gradebook/attendance
    overview when no semester filter has been explicitly chosen.

    Tries, in order:
      1. An explicit `is_current` flag on Semester (most reliable — flip
         this once per term when registration/records switch over).
      2. A date-range match: today falls between start_date and end_date.
      3. Fallback: the most recently-starting semester on record.

    NOTE: adjust the field names below (`is_current`, `start_date`,
    `end_date`) if your Semester model uses different ones.
    """
    today = timezone.localdate()

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
# ==========================================================================================================================================================
from Admin.Colleges.models import ProgramCourse  # bulk (program, course) -> study_year lookup


def _match_curriculum_year(pairs, year_filter_int):
    pairs = list(pairs)
    if not pairs:
        return set()

    student_program_map = {}
    course_ids = set()
    for student, course_id in pairs:
        academic_profile = getattr(student, "academic_profile", None)
        program = academic_profile.program if academic_profile else None
        if program:
            student_program_map[student.id] = program.pk
        if course_id:
            course_ids.add(course_id)

    program_ids = set(student_program_map.values())
    program_course_map = {}
    if program_ids and course_ids:
        for pid, cid, study_year in ProgramCourse.objects.filter(
            program_id__in=program_ids, course_id__in=course_ids
        ).values_list("program_id", "course_id", "study_year"):
            program_course_map[(pid, cid)] = study_year

    matching_student_ids = set()
    for student, course_id in pairs:
        program_id = student_program_map.get(student.id)
        if program_id is None:
            continue
        study_year = program_course_map.get((program_id, course_id))
        if study_year == year_filter_int:
            matching_student_ids.add(student.id)

    return matching_student_ids


@login_required
def gradebook(request, uuid):
    faculty = get_object_or_404(FacultyProfile, user=request.user)
    department = faculty.department 

    assignments = FacultyCourseAssignment.objects.filter(faculty=faculty)
    section_ids = list(assignments.values_list("course_section_id", flat=True))

    sections = (
        CourseSection.objects
        .filter(section_id__in=section_ids)
        .select_related("course", "semester_id")
    )

    courses_in_scope = (
        Course.objects
        .filter(course_id__in=sections.values_list("course_id", flat=True))
        .distinct()
        .order_by("course_code")
    )
    total_courses = courses_in_scope.count()

    base_grades_qs = (
        CourseGrade.objects
        .select_related(
            "student", "student__user",
            "student__academic_profile", "student__academic_profile__program",
            "course", "grade_scale", "semester",
        )
        .filter(
            course__course_id__in=courses_in_scope.values_list("course_id", flat=True),
            instructor_id=faculty.employee_id,
        )
    )

    semesters_in_scope = (
        base_grades_qs
        .values("semester_id", "semester__academic_year", "semester__semester_type")
        .distinct()
        .order_by("-semester__academic_year", "-semester__semester_type")
    )

    grades_qs = base_grades_qs

    current_semester = _get_current_semester()

    # ---------------- Filters ----------------
    student_search = request.GET.get("student", "").strip()
    course_filter = request.GET.get("course", "").strip()
    year_filter = request.GET.get("year", "").strip()

    if "semester" in request.GET:
        semester_filter = request.GET.get("semester", "").strip()
    else:
        semester_filter = str(current_semester.pk) if current_semester else ""

    if student_search:
        grades_qs = grades_qs.filter(
            Q(student__user__first_name__icontains=student_search) |
            Q(student__user__last_name__icontains=student_search) |
            Q(student__preferred_name__icontains=student_search) |
            Q(student__student_number__icontains=student_search)
        )

    if course_filter:
        grades_qs = grades_qs.filter(course__course_id=course_filter)

    if semester_filter:
        grades_qs = grades_qs.filter(semester_id=semester_filter)

    if year_filter:
        try:
            year_filter_int = int(year_filter)
        except ValueError:
            year_filter_int = None

        if year_filter_int:
            candidate_grades = list(grades_qs)
            pairs = [(g.student, g.course_id) for g in candidate_grades]
            matching_student_ids = _match_curriculum_year(pairs, year_filter_int)

            matching_grade_ids = [
                g.pk for g in candidate_grades if g.student_id in matching_student_ids
            ]
            grades_qs = grades_qs.filter(pk__in=matching_grade_ids)

    grades_qs = grades_qs.order_by("course__course_code", "student__student_number")

    # ---------------- Stats ----------------
    enrollment_qs = (
        StudentEnrollment.objects
        .filter(section_id__in=section_ids)
        .exclude(enrollment_status__in=["WITHDRAWN"])
        .select_related("student__academic_profile__program", "section_id__course")
    )

    if course_filter:
        enrollment_qs = enrollment_qs.filter(section_id__course_id=course_filter)

    if semester_filter:
        enrollment_qs = enrollment_qs.filter(semester_id=semester_filter)

    if student_search:
        enrollment_qs = enrollment_qs.filter(
            Q(student__user__first_name__icontains=student_search) |
            Q(student__user__last_name__icontains=student_search) |
            Q(student__preferred_name__icontains=student_search) |
            Q(student__student_number__icontains=student_search)
        )

    enrolled_student_ids = list(
        enrollment_qs.values_list("student_id", flat=True).distinct()
    )

    if year_filter:
        try:
            year_filter_int = int(year_filter)
        except ValueError:
            year_filter_int = None

        if year_filter_int:
            enrollment_pairs = [
                (e.student, e.section_id.course_id)
                for e in enrollment_qs
                if e.section_id and e.section_id.course_id
            ]
            matching_ids = _match_curriculum_year(enrollment_pairs, year_filter_int)
            enrolled_student_ids = [sid for sid in enrolled_student_ids if sid in matching_ids]

    total_students = len(enrolled_student_ids)

    scored = grades_qs.exclude(numeric_score__isnull=True)
    average_score = round(scored.aggregate(avg=Avg("numeric_score"))["avg"] or 0)

    avg_grade_scale = resolve_grade_scale(average_score) if average_score else None
    average_grade_letter = avg_grade_scale.letter_grade if avg_grade_scale else "—"

    grade_counts = {}
    for g in scored:
        if g.grade_scale:
            letter = g.grade_scale.letter_grade
            grade_counts[letter] = grade_counts.get(letter, 0) + 1

    total_graded = scored.count()
    grade_distribution = [
        {
            "letter": letter,
            "count": count,
            "pct": round((count / total_graded) * 100) if total_graded else 0,
        }
        for letter, count in sorted(grade_counts.items(), key=lambda x: -x[1])
    ]

    course_performance = []
    for course in courses_in_scope:
        course_avg = (
            scored.filter(course=course)
            .aggregate(avg=Avg("numeric_score"))["avg"]
        )
        course_performance.append({
            "course_code": course.course_code,
            "course_name": course.course_name,
            "avg_score": round(course_avg) if course_avg else 0,
        })

    top_performers_by_course = []
    for course in courses_in_scope:
        course_top_qs = (
            scored.filter(course=course)
            .filter(grade_scale__passing_grade=True)
            .values("student_id", "student__preferred_name",
                     "student__user__first_name", "student__user__last_name")
            .annotate(avg_score=Avg("numeric_score"))
            .order_by("-avg_score")[:3]
        )
        course_top = [
            {
                "name": (
                    row["student__preferred_name"]
                    or f'{row["student__user__first_name"] or ""} {row["student__user__last_name"] or ""}'.strip()
                ),
                "avg_score": round(row["avg_score"], 2),
            }
            for row in course_top_qs
        ]
        if course_top:
            top_performers_by_course.append({
                "course_name": course.course_name,
                "course_code": course.course_code,
                "performers": course_top,
            })

    # ---------------- Pagination ----------------
    paginator = Paginator(grades_qs, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    is_default_semester = (
        not current_semester or semester_filter == str(current_semester.pk)
    )
    has_active_filters = bool(
        student_search or course_filter or year_filter or not is_default_semester
    )

    context = {
        "uuid": uuid,
        "faculty": faculty,
        "department": department,
        "grades": page_obj,
        "page_obj": page_obj,

        "current_semester": current_semester,
        "has_active_filters": has_active_filters,

        "total_students": total_students,
        "average_score": average_score,
        "average_grade_letter": average_grade_letter,
        "total_courses": total_courses,

        "grade_distribution": grade_distribution,
        "course_performance": course_performance,
        "top_performers_by_course": top_performers_by_course,

        "courses_in_scope": courses_in_scope,
        "semesters_in_scope": semesters_in_scope,
        "student_search": student_search,
        "course_filter": course_filter,
        "semester_filter": semester_filter,
        "year_filter": year_filter,
    }
    return render(request, "teaching/gradebook.html", context)
# ==========================================================================================================================================================
def _months_back(base_date, n):
    year = base_date.year
    month = base_date.month - n
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)

@login_required
def attendance(request, uuid):
    faculty = get_object_or_404(FacultyProfile, user=request.user)
    today = timezone.localdate()

    # ---------------- Faculty's OWN assigned sections only ----------------
    assignments = FacultyCourseAssignment.objects.filter(faculty=faculty)
    my_section_ids = list(assignments.values_list("course_section_id", flat=True))

    my_sections = (
        CourseSection.objects
        .filter(section_id__in=my_section_ids)
        .select_related("course")
    )

    my_course_ids = my_sections.values_list("course_id", flat=True).distinct()
    courses_in_scope = Course.objects.filter(course_id__in=my_course_ids).order_by("course_code")

    semesters_in_scope = (
        StudentEnrollment.objects
        .filter(section_id__in=my_section_ids)
        .values("semester_id", "semester__academic_year", "semester__semester_type")
        .distinct()
        .order_by("-semester__academic_year", "-semester__semester_type")
    )

    programs_in_scope = (
        AcademicProgram.objects
        .filter(student_academic_profiles__student__enrollments__section_id__in=my_section_ids)
        .distinct()
        .order_by("program_name")
    )

    # ---------------- Determine the CURRENT active semester ----------------
    current_semester = Semester.objects.filter(is_current=True).first()
    if not current_semester:
        current_semester = Semester.objects.order_by("-academic_year", "-start_date").first()

    if current_semester:
        current_semester_section_ids = list(
            StudentEnrollment.objects
            .filter(section_id__in=my_section_ids, semester=current_semester)
            .values_list("section_id", flat=True)
            .distinct()
        )
    else:
        current_semester_section_ids = []

    # ---------------- Read filters up front ----------------
    student_search = request.GET.get("student", "").strip()
    course_filter = request.GET.get("course", "").strip()
    year_filter = request.GET.get("year", "").strip()
    program_filter = request.GET.get("program", "").strip()

    if "semester" in request.GET:
        semester_filter = request.GET.get("semester", "").strip()
    else:
        semester_filter = str(current_semester.pk) if current_semester else ""

    scoped_section_ids = my_section_ids

    if course_filter:
        scoped_section_ids = list(
            my_sections.filter(course__course_id=course_filter)
            .values_list("section_id", flat=True)
        )

    if semester_filter:
        semester_section_ids = set(
            StudentEnrollment.objects
            .filter(section_id__in=scoped_section_ids, semester_id=semester_filter)
            .values_list("section_id", flat=True)
            .distinct()
        )
        scoped_section_ids = [sid for sid in scoped_section_ids if sid in semester_section_ids]

    # ---------------- FILTER-REACTIVE stats ----------------
    attendance_qs = Attendance.objects.filter(
        attendance_session__section_id__in=scoped_section_ids
    ).select_related(
        "attendance_session", "attendance_session__course", "student", "student__user"
    )

    today_qs = attendance_qs.filter(attendance_session__attendance_date=today)
    present_today = today_qs.filter(status="PRESENT").count()
    absent_today = today_qs.filter(status="ABSENT").count()

    total_students = (
        StudentEnrollment.objects
        .filter(section_id__in=scoped_section_ids)
        .values("student_id").distinct().count()
    )

    total_records = attendance_qs.count()
    present_records = attendance_qs.filter(status="PRESENT").count()
    attendance_rate = round((present_records / total_records) * 100) if total_records else 0

    monthly_progress = []
    for i in range(2, -1, -1):
        month_start = _months_back(today, i)
        month_qs = attendance_qs.filter(
            attendance_session__attendance_date__year=month_start.year,
            attendance_session__attendance_date__month=month_start.month,
        )
        month_total = month_qs.count()
        month_present = month_qs.filter(status="PRESENT").count()
        month_pct = round((month_present / month_total) * 100) if month_total else 0
        monthly_progress.append({"label": month_start.strftime("%B"), "pct": month_pct})

    course_wise_scope = courses_in_scope.filter(course_id=course_filter) if course_filter else courses_in_scope
    course_wise = []
    for course in course_wise_scope:
        course_section_ids = my_sections.filter(course=course).values_list("section_id", flat=True)
        course_qs = Attendance.objects.filter(attendance_session__section_id__in=course_section_ids)
        if semester_filter:
            sem_ids = set(
                StudentEnrollment.objects
                .filter(section_id__in=course_section_ids, semester_id=semester_filter)
                .values_list("section_id", flat=True)
            )
            course_section_ids = [sid for sid in course_section_ids if sid in sem_ids]
            course_qs = Attendance.objects.filter(attendance_session__section_id__in=course_section_ids)
        course_total = course_qs.count()
        course_present = course_qs.filter(status="PRESENT").count()
        course_pct = round((course_present / course_total) * 100) if course_total else 0
        course_wise.append({"course_name": course.course_name, "pct": course_pct})

    recent_sessions = (
        AttendanceSession.objects
        .filter(section_id__in=current_semester_section_ids, status="CLOSED")
        .select_related("course", "section")
        .order_by("-attendance_date", "-id")[:5]
    )
    recent_activities = []
    for session in recent_sessions:
        session_records = Attendance.objects.filter(attendance_session=session)
        absent_count = session_records.filter(status="ABSENT").count()
        if session.course:
            course_label = f"{session.course.course_code} — {session.course.course_name}"
        else:
            course_label = "Course"
        if absent_count > 0:
            title = f"{absent_count} Student{'s' if absent_count != 1 else ''} Absent"
            dot_class = "red"
        else:
            title = "Attendance Submitted"
            dot_class = "green"
        recent_activities.append({
            "title": title,
            "description": f"{course_label} — {session.attendance_date.strftime('%b %d, %Y')}",
            "dot_class": dot_class,
        })

    current_semester_attendance_qs = Attendance.objects.filter(
        attendance_session__section_id__in=current_semester_section_ids
    )
    total_sessions_conducted = AttendanceSession.objects.filter(
        section_id__in=current_semester_section_ids, status="CLOSED"
    ).count()

    current_semester_course_wise = []
    for course in courses_in_scope:
        course_section_ids = list(
            my_sections.filter(course=course).values_list("section_id", flat=True)
        )
        course_section_ids = [sid for sid in course_section_ids if sid in current_semester_section_ids]
        course_qs = Attendance.objects.filter(attendance_session__section_id__in=course_section_ids)
        course_total = course_qs.count()
        course_present = course_qs.filter(status="PRESENT").count()
        course_pct = round((course_present / course_total) * 100) if course_total else 0
        current_semester_course_wise.append({"course_name": course.course_name, "pct": course_pct})

    best_course = max(current_semester_course_wise, key=lambda c: c["pct"], default=None)
    lowest_course = min(current_semester_course_wise, key=lambda c: c["pct"], default=None)

    overall_records = current_semester_attendance_qs.count()
    overall_present = current_semester_attendance_qs.filter(status="PRESENT").count()
    overall_attendance_rate = round((overall_present / overall_records) * 100) if overall_records else 0

    # STUDENT ATTENDANCE TABLE (filter-reactive)
    enrolled_student_ids = (
        StudentEnrollment.objects
        .filter(section_id__in=scoped_section_ids)
        .values_list("student_id", flat=True)
        .distinct()
    )

    students_qs = StudentProfile.objects.filter(id__in=enrolled_student_ids).select_related(
        "user", "academic_profile__program"
    )

    if student_search:
        students_qs = students_qs.filter(
            Q(user__first_name__icontains=student_search) |
            Q(user__last_name__icontains=student_search) |
            Q(preferred_name__icontains=student_search) |
            Q(student_number__icontains=student_search)
        )

    if year_filter:
        try:
            year_filter_int = int(year_filter)
        except ValueError:
            year_filter_int = None

        if year_filter_int:

            candidate_student_ids = list(students_qs.values_list("id", flat=True))
            candidate_students = list(students_qs)
            student_by_id = {s.id: s for s in candidate_students}

            enrollment_pairs = []
            for enrollment in (
                StudentEnrollment.objects
                .filter(section_id__in=scoped_section_ids, student_id__in=candidate_student_ids)
                .select_related("section_id__course")
            ):
                student = student_by_id.get(enrollment.student_id)
                if student and enrollment.section_id and enrollment.section_id.course_id:
                    enrollment_pairs.append((student, enrollment.section_id.course_id))

            matching_ids = _match_curriculum_year(enrollment_pairs, year_filter_int)
            students_qs = students_qs.filter(id__in=matching_ids)

    if program_filter:
        students_qs = students_qs.filter(academic_profile__program_id=program_filter)

    students_qs = students_qs.order_by("student_number")

    student_rows = []
    for student in students_qs:
        student_records = attendance_qs.filter(student=student)
        sessions = student_records.count()
        present = student_records.filter(status="PRESENT").count()
        absent = student_records.filter(status="ABSENT").count()
        pct = round((present / sessions) * 100) if sessions else 0

        student_rows.append({
            "student_number": student.student_number,
            "name": student.preferred_name or student.user.get_full_name(),
            "initial": (student.preferred_name or student.user.get_full_name() or "?")[:1].upper(),
            "sessions": sessions,
            "present": present,
            "absent": absent,
            "pct": pct,
        })

    paginator = Paginator(student_rows, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    is_default_semester = (
        not current_semester or semester_filter == str(current_semester.pk)
    )
    has_active_filters = bool(
        student_search or course_filter or year_filter or program_filter or not is_default_semester
    )

    context = {
        "uuid": uuid,
        "faculty": faculty,
        "today": today,
        "current_semester": current_semester,
        "has_active_filters": has_active_filters,

        "total_students": total_students,
        "present_today": present_today,
        "absent_today": absent_today,
        "attendance_rate": attendance_rate,
        "total_records": total_records,

        "monthly_progress": monthly_progress,
        "course_wise": course_wise,
        "recent_activities": recent_activities,

        "courses_in_scope": courses_in_scope,
        "semesters_in_scope": semesters_in_scope,
        "programs_in_scope": programs_in_scope,
        "student_search": student_search,
        "course_filter": course_filter,
        "semester_filter": semester_filter,
        "year_filter": year_filter,
        "program_filter": program_filter,
        "student_rows": page_obj,
        "page_obj": page_obj,

        "total_sessions_conducted": total_sessions_conducted,
        "best_course": best_course,
        "lowest_course": lowest_course,
        "overall_attendance_rate": overall_attendance_rate,
    }
    return render(request, "teaching/attendance.html", context)