# ============================================================
# Python Standard Library
# ============================================================
import json
import re
from decimal import Decimal, InvalidOperation


# ============================================================
# Django Core
# ============================================================
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone


# ============================================================
# Application Forms
# ============================================================
from Admin.Elsa_admin.forms import GradeScaleForm


# ============================================================
# Application Models
# ============================================================
from Admin.bela_admin.models import Course
from Faculty.models import FacultyProfile, GradeChangeRequest
from Staff.models import Notification
from Students.models import StudentEnrollment, StudentProfile
from .models import *

# ============================================================
# Notifications
# ============================================================
from notifications.utils import send_notification

# ============================================================================================================
# ============================================================================================================
@login_required
def grade_scale(request):
    grades = GradeScale.objects.all().order_by("-grade_points")
    active_grades = grades.filter(is_active=True)
    chart_labels = list(active_grades.values_list("letter_grade", flat=True))
    chart_min = [float(g.minimum_percentage) for g in active_grades]
    chart_max = [float(g.maximum_percentage) for g in active_grades]
    chart_points = [float(p) for p in active_grades.values_list("grade_points", flat=True)]
    palette = [
        "#16a34a", "#22c55e", "#84cc16", "#facc15",
        "#fb923c", "#f97316", "#dc2626", "#c026d3",
        "#7c3aed", "#2563eb", "#0891b2", "#0d9488",
    ]
    chart_colors = [palette[i % len(palette)] for i in range(len(chart_labels))]
    context = {
        "grades": grades,
        "total_grades": grades.count(),
        "pass_count": grades.filter(passing_grade=True).count(),
        "fail_count": grades.filter(passing_grade=False).count(),
        "active_count": grades.filter(is_active=True).count(),
        "chart_labels": json.dumps(chart_labels),
        "chart_min": json.dumps(chart_min),
        "chart_max": json.dumps(chart_max),
        "chart_points": json.dumps(chart_points),
        "chart_colors": json.dumps(chart_colors),
    }
    return render(request, "Grade/Elsa/grade_scale.html", context)
# ============================================================================================================
@login_required
def add_grade_scale(request):
    if request.method == "POST":
        errors = {}
        letter_grade = request.POST.get("letter_grade", "").strip().upper()
        description = request.POST.get("description", "").strip()
        grade_points = request.POST.get("grade_points", "").strip()
        minimum_percentage = request.POST.get("minimum_percentage", "").strip()
        maximum_percentage = request.POST.get("maximum_percentage", "").strip()
        passing_grade = request.POST.get("passing_grade")
        is_active = request.POST.get("is_active")
        if not letter_grade:
            errors["letter_grade"] = "Letter Grade is required."
        elif not re.fullmatch(r"^[A-Z]+[+-]?$", letter_grade):
            errors["letter_grade"] = "Grade can contain Only alphabets with optional + or - allowed."      
        elif len(letter_grade) > 3:
            errors["letter_grade"] = ( "Maximum 3 characters allowed." )
        elif GradeScale.objects.filter(letter_grade=letter_grade).exists():
            errors["letter_grade"] = "Grade already exists."
        try:
            grade_points = Decimal(grade_points)

            if grade_points < 0 or grade_points > 4:
                errors["grade_points"] = "Grade Point must be between 0 and 4."
            elif grade_points.as_tuple().exponent < -1:
                errors["grade_points"] = ( "Only one decimal place allowed." )
            elif GradeScale.objects.filter(
                grade_points=grade_points
            ).exists():
                errors["grade_points"] = "Grade point already assigned to another grade."
        except:
            errors["grade_points"] = "Enter a valid Grade Point."
        try:
            minimum_percentage = Decimal(minimum_percentage)

            if minimum_percentage < 0 or minimum_percentage > 100:
                errors["minimum_percentage"] = "Minimum Percentage must be between 0 and 100."
        except:
            errors["minimum_percentage"] = "Enter a valid Minimum Percentage."
        try:
            maximum_percentage = Decimal(maximum_percentage)

            if maximum_percentage < 0 or maximum_percentage > 100:
                errors["maximum_percentage"] = "Maximum Percentage must be between 0 and 100."

        except:
            errors["maximum_percentage"] = "Enter a valid Maximum Percentage."
              # RANGE CHECK
        if (
            "minimum_percentage" not in errors
            and "maximum_percentage" not in errors
        ):
            if minimum_percentage > maximum_percentage:
                errors["minimum_percentage"] = "Minimum Percentage cannot be greater than Maximum Percentage."
            if (
                "minimum_percentage" not in errors
                and "maximum_percentage" not in errors
            ):

                overlap = GradeScale.objects.filter(
                    minimum_percentage__lt=maximum_percentage,
                    maximum_percentage__gt=minimum_percentage
                )

                if overlap.exists():
                    existing = overlap.first()
                    if (
                        minimum_percentage >= existing.minimum_percentage
                        and minimum_percentage <= existing.maximum_percentage
                    ):
                        errors["minimum_percentage"] = (
                            f"Minimum percentage overlaps with {existing.letter_grade} range."
                        )

                    elif (
                        maximum_percentage >= existing.minimum_percentage
                        and maximum_percentage <= existing.maximum_percentage
                    ):
                        errors["maximum_percentage"] = (
                            f"Maximum percentage overlaps with {existing.letter_grade} range."
                        )

                    else:
                        errors["minimum_percentage"] = (
                            "Percentage range overlaps with an existing grade."
                        )               
        if len(description) > 30:
            errors["description"] = "Maximum 30 characters allowed."
        if description and not re.fullmatch(r"[A-Za-z ]+", description):
            errors["description"] = "Description can contain only alphabets and spaces."
        if passing_grade is None:
            errors["passing_grade"] = "Please select Pass or Fail."
        else:
            passing_grade = passing_grade == "1"
        if is_active is None:
            errors["is_active"] = "Please select Active or Inactive"
        else:
            is_active = True if is_active == "1" else False

        if errors:
            return JsonResponse({
                "success": False,
                "errors": errors
            })
        GradeScale.objects.create(
            letter_grade=letter_grade,
            description=description,
            grade_points=grade_points,
            minimum_percentage=minimum_percentage,
            maximum_percentage=maximum_percentage,
            passing_grade=passing_grade,
            is_active=is_active
        )
        return JsonResponse({
            "success": True,
            "message": "Grade added successfully."
        })
    return render(request, "Grade/Elsa/add_grade_scale.html")
# ============================================================================================================
@login_required
def edit_grade_scale(request, id):
    grade = get_object_or_404(GradeScale, id=id)
    if request.method == "POST":
        errors = {}
        letter_grade = request.POST.get("letter_grade", "").strip().upper()
        description = request.POST.get("description", "").strip()
        grade_points = request.POST.get("grade_points", "").strip()
        minimum_percentage = request.POST.get("minimum_percentage", "").strip()
        maximum_percentage = request.POST.get("maximum_percentage", "").strip()
        passing_grade = request.POST.get("passing_grade")
        is_active = request.POST.get("is_active")
        # LETTER GRADE VALIDATION
        if not letter_grade:
            errors["letter_grade"] = "Letter Grade is required."

        elif not re.fullmatch(r"^[A-Za]+[+-]?$", letter_grade):
            errors["letter_grade"] = (
                "Grade can contain only letters with an optional '+' or '-' at the end."
            )
        elif len(letter_grade) > 3:
            errors["letter_grade"] = "Maximum 3 characters allowed."
        elif GradeScale.objects.exclude(id=grade.id).filter(
            letter_grade=letter_grade
        ).exists():
            errors["letter_grade"] = "Grade already exists."

        # GRADE POINT VALIDATION
        try:
            grade_points = Decimal(grade_points)

            if grade_points < 0 or grade_points > 4:
                errors["grade_points"] = (
                    "Grade Point must be between 0 and 4."
                )
            elif grade_points.as_tuple().exponent < -1:
                errors["grade_points"] = (
                    "Only one decimal place allowed."
               )
            elif GradeScale.objects.exclude(id=grade.id).filter(
                grade_points=grade_points
            ).exists():
                errors["grade_points"] = (
                    "Grade point already assigned to another grade."
                )
        except:
            errors["grade_points"] = "Enter a valid Grade Point."

        # MINIMUM PERCENTAGE
        try:
            minimum_percentage = Decimal(minimum_percentage)

            if minimum_percentage < 0 or minimum_percentage > 100:
                errors["minimum_percentage"] = (
                    "Minimum Percentage must be between 0 and 100."
                )

        except:
            errors["minimum_percentage"] = (
                "Enter a valid Minimum Percentage."
            )
        # MAXIMUM PERCENTAGE
        try:
            maximum_percentage = Decimal(maximum_percentage)

            if maximum_percentage < 0 or maximum_percentage > 100:
                errors["maximum_percentage"] = (
                    "Maximum Percentage must be between 0 and 100."
                )
        except:
            errors["maximum_percentage"] = (
                "Enter a valid Maximum Percentage."
            )
        # RANGE VALIDATION
        if (
            "minimum_percentage" not in errors
            and "maximum_percentage" not in errors
        ):
            if minimum_percentage > maximum_percentage:
                errors["minimum_percentage"] = (
                    "Minimum Percentage cannot be greater than Maximum Percentage."
                )
            else:
                overlap = GradeScale.objects.exclude(
                    id=grade.id
                ).filter(
                    minimum_percentage__lte=maximum_percentage,
                    maximum_percentage__gte=minimum_percentage
                )
                if overlap.exists():
                    errors["minimum_percentage"] = (
                        "Percentage range overlaps with an existing grade."
                    )
        # DESCRIPTION
        if len(description) > 30:
            errors["description"] = (
                "Maximum 30 characters allowed."
            )
        elif description and not re.fullmatch(
            r"[A-Za-z ]+",
            description
        ):
            errors["description"] = (
                "Description can contain only alphabets and spaces."
            )
        # PASS / FAIL
        if passing_grade is None:
            errors["passing_grade"] = (
                "Please select Pass or Fail."
            )
        else:
            passing_grade = passing_grade == "1"
        # ACTIVE STATUS
        if is_active is None:
            errors["is_active"] = (
                "Please select Active or Inactive."
            )
        else:
            is_active = True if is_active == "1" else False
       # RETURN ERRORS
        if errors:
            return JsonResponse({
                "success": False,
                "errors": errors
            })
        # UPDATE
        grade.letter_grade = letter_grade
        grade.description = description
        grade.grade_points = grade_points
        grade.minimum_percentage = minimum_percentage
        grade.maximum_percentage = maximum_percentage
        grade.passing_grade = passing_grade
        grade.is_active = is_active
        grade.save()
        return JsonResponse({
            "success": True,
            "message": "Grade updated successfully."
        })
    return render( request, "Grade/Elsa/edit_grade_scale.html",{"grade": grade})
# ============================================================================================================
def _grade_scale_usage_count(grade):
    """
    Counts how many records anywhere in the project reference this GradeScale,
    using Django's own reverse-relation metadata — no need to know every model
    that has a ForeignKey to GradeScale.
    """
    total = 0
    for rel in grade._meta.related_objects:
        if rel.many_to_many:
            continue
        accessor_name = rel.get_accessor_name()
        related_manager = getattr(grade, accessor_name, None)
        if related_manager is not None and hasattr(related_manager, "count"):
            total += related_manager.count()
    return total

@login_required
def delete_grade_scale(request, id):
    grade = get_object_or_404(GradeScale, id=id)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method != "POST":
        if is_ajax:
            return JsonResponse({
                "success": False,
                "errors": {"delete": "Invalid request method."}
            }, status=405)
        return redirect('gradescale')

    usage_count = _grade_scale_usage_count(grade)
    if usage_count > 0:
        reason = (
            f"Grade {grade.letter_grade} is currently in use "
            f"and cannot be deleted. Use Edit to mark it Inactive instead."
        )
        if is_ajax:
            return JsonResponse({
                "success": False,
                "message": reason,
                "errors": {"delete": reason}
            }, status=400)
        messages.error(request, reason)
        return redirect('gradescale')

    letter_grade = grade.letter_grade
    grade.delete()

    if is_ajax:
        return JsonResponse({"success": True, "message": f"Grade {letter_grade} deleted successfully."})
    return redirect('gradescale')
# =======================================================================================================================================
# ======= SCORE REQUEST =================================================================================================================
@login_required
def score_request(request):
    requests = GradeChangeRequest.objects.all().order_by("-request_date")

    today = timezone.now().date()
    selected_date = request.GET.get("date", "").strip()

    if selected_date:
        try:
            filter_date = timezone.datetime.strptime(selected_date, "%Y-%m-%d").date()
            if filter_date > today:
                selected_date = ""
            else:
                requests = requests.filter(request_date__date=filter_date)
        except ValueError:
            selected_date = ""

    total_count = requests.count()
    pending_count = requests.filter(approval_status="Pending").count()
    approved_count = requests.filter(approval_status="Approved").count()
    rejected_count = requests.filter(approval_status="Rejected").count()

    paginator = Paginator(requests, 10)
    request_page = paginator.get_page(request.GET.get("page"))
    for r in request_page:
        try:
            faculty = FacultyProfile.objects.select_related("user").get(employee_id=r.instructor_id)
            r.faculty_obj = faculty
        except FacultyProfile.DoesNotExist:
            r.faculty_obj = None

        try:
            r.student_obj = StudentProfile.objects.select_related("user").get(student_number=r.student_id)
        except StudentProfile.DoesNotExist:
            r.student_obj = None

        try:
            r.course_obj = Course.objects.get(course_code=r.course_id)
        except Course.DoesNotExist:
            r.course_obj = None

    toast = request.GET.get("toast")
    toast_map = {
        "approved": ("Request approved successfully", "success"),
        "rejected": ("Request rejected successfully", "danger"),
        "finalized": ("This request is already finalized", "warning"),
    }
    toast_message, toast_type = toast_map.get(toast, (None, None))

    context = {
        "requests": request_page,
        "request_page": request_page,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "total_count": total_count,
        "toast_message": toast_message,
        "toast_type": toast_type,
        "selected_date": selected_date,
        "today": today.isoformat(),
    }
    return render(request, "Grade/Elsa_Score_Request/score_request.html", context)

# ============================================================================================================
@login_required
def approve_request(request, request_id):

    req = get_object_or_404(GradeChangeRequest, request_id=request_id)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if req.approval_status != "Pending":
        if is_ajax:
            return JsonResponse({"success": False, "message": "This request is already finalized."}, status=400)
        return redirect("/score_request/?toast=finalized")

    req.approval_status = "Approved"
    req.approved_by = request.user.username
    req.approved_date = timezone.now().date()
    req.save()

    faculty = FacultyProfile.objects.select_related("user").filter(employee_id=req.instructor_id).first()
    if faculty:
        message = f"Your grade change request for student {req.student_id} in {req.course_id} was approved."
        course_obj = Course.objects.filter(course_code=req.course_id).first()

        enrollment = (
            StudentEnrollment.objects
            .filter(
                student__student_number=req.student_id,
                section_id__course__course_code=req.course_id,
            )
            .exclude(enrollment_status__in=["WITHDRAWN"])
            .select_related("section_id")
            .first()
        )
        section_id = enrollment.section_id.section_id if enrollment else None

        if course_obj and section_id:
            notification_link = f"{reverse('course_grade')}?course={course_obj.course_id}&section={section_id}&student_id={req.student_id}"
        elif course_obj:
            notification_link = f"{reverse('course_grade')}?course={course_obj.course_id}&student_id={req.student_id}"
        else:
            notification_link = reverse("course_grade")

        Notification.objects.create(
            user=faculty.user,
            title="Grade Change Approved",
            message=message,
            notification_type="SUCCESS",
            link=notification_link,
        )

        send_notification(faculty.user_id, {
            "title": "Grade Change Approved",
            "message": message,
            "request_id": req.request_id,
            "status": "Approved",
            "student_id": req.student_id,
            "course_id": req.course_id,
            "approved_by": req.approved_by,
            "approved_date": req.approved_date.strftime("%d %b %Y") if req.approved_date else "",
        }, event="grade_request_decided")

    if is_ajax:
        return JsonResponse({"success": True, "status": "Approved", "request_id": req.request_id})
    return redirect("score_request")

# ============================================================================================================
@login_required
def reject_request(request, request_id):

    req = get_object_or_404(GradeChangeRequest, request_id=request_id)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if req.approval_status != "Pending":
        if is_ajax:
            return JsonResponse({"success": False, "message": "This request is already finalized."}, status=400)
        return redirect("/score_request/?toast=finalized")

    req.approval_status = "Rejected"
    req.approved_by = request.user.username
    req.save()

    faculty = FacultyProfile.objects.select_related("user").filter(employee_id=req.instructor_id).first()
    if faculty:
        message = f"Your grade change request for student {req.student_id} in {req.course_id} was rejected."
        course_obj = Course.objects.filter(course_code=req.course_id).first()

        enrollment = (
            StudentEnrollment.objects
            .filter(
                student__student_number=req.student_id,
                section_id__course__course_code=req.course_id,
            )
            .exclude(enrollment_status__in=["WITHDRAWN"])
            .select_related("section_id")
            .first()
        )
        section_id = enrollment.section_id.section_id if enrollment else None

        if course_obj and section_id:
            notification_link = f"{reverse('course_grade')}?course={course_obj.course_id}&section={section_id}&student_id={req.student_id}"
        elif course_obj:
            notification_link = f"{reverse('course_grade')}?course={course_obj.course_id}&student_id={req.student_id}"
        else:
            notification_link = reverse("course_grade")

        Notification.objects.create(
            user=faculty.user,
            title="Grade Change Rejected",
            message=message,
            notification_type="ERROR",
            link=notification_link,
        )

        send_notification(faculty.user_id, {
            "title": "Grade Change Rejected",
            "message": message,
            "request_id": req.request_id,
            "status": "Rejected",
            "student_id": req.student_id,
            "course_id": req.course_id,
            "approved_by": req.approved_by,
            "approved_date": "",
        }, event="grade_request_decided")

    if is_ajax:
        return JsonResponse({"success": True, "status": "Rejected", "request_id": req.request_id})
    return redirect("score_request")
# ============================================================================================================