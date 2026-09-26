########################## kali code  #################################

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserCreateForm
from Admin.models import User,UserRole, Firearm,OlympicAthlete,OlympicPerformance
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from Admin.audit import AuditLogger
from PermissionAccess.decorators import require_permission, require_page_access
from Admin.models import UserAuditLog
from collections import Counter
from datetime import timedelta
from datetime import timedelta, datetime
import re
from Students.models import StudentProfile
from Staff.models import StaffProfile
from Students.views import save_student_details, suggested_student_number_for_context
from Faculty.views import save_faculty_details, suggested_faculty_id_for_context
from Staff.views import save_staff_details, suggested_staff_id_for_context
from Students.models import StudentProfile         
from Faculty.models import FacultyProfile,FacultyEducation         
from Staff.models import StaffProfile
from Admin.bela_admin.models import Department, Course 
from django.utils.timesince import timesince
from django.db.models import Count, Q
from django.db import transaction
from django.db.utils import IntegrityError
from Admin.Jack.models import Athletic, Sport, SportTeamModel, Coach, SportClub, SportsFacility
from Admin.models import Tournament, TournamentInvitation, TournamentParticipant, TournamentApplication
from django.db.models import Sum
from calendar import month_abbr 
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.validators import validate_email
from django.conf import settings
from decimal import Decimal, InvalidOperation
from email.mime.image import MIMEImage
import os
import re
import logging
from Staff.utils import notify_faculty_new_tournament_invitation
import random
from django.contrib.auth.hashers import make_password, check_password
from Admin.Colleges.models import School
from Admin.ws_utils import broadcast_invitation_status, broadcast_participant_added
from Admin.bela_admin.models import Room


logger = logging.getLogger(__name__)

from Admin.Colleges.models import (
    University,
    School,
    Degree,
    AcademicProgram,
)
from Admin.Jack.models import Coach


@require_page_access("user_page")
@login_required
def user_page(request):
    return render(request, "user_page.html") 


 

ROLE_COLORS = ["red", "blue", "purple", "green", "amber", "gray"]


def _role_color_map():
    """Map each UserRole id -> a color, in a stable order (by role_name)."""
    ids = list(UserRole.objects.order_by("role_name").values_list("id", flat=True))
    return {rid: ROLE_COLORS[i % len(ROLE_COLORS)] for i, rid in enumerate(ids)}

@require_page_access("role")
@login_required
def role(request):
    roles = UserRole.objects.all().order_by("role_name")
    color_map = _role_color_map()

    total_roles = roles.count()
    total_users = User.objects.count()
    active_users = User.objects.filter(account_status="ACTIVE").count()
    unassigned_users = User.objects.filter(role__isnull=True).count() 

    now = timezone.now()
    roles_this_month = roles.filter(
        created_at__year=now.year, created_at__month=now.month
    ).count()
    users_this_month = User.objects.filter(
        created_at__year=now.year, created_at__month=now.month
    ).count()

    active_pct = round((active_users / total_users * 100), 1) if total_users else 0
    unassigned_pct = round((unassigned_users / total_users * 100), 1) if total_users else 0

    role_pills = []
    for r in roles:
        role_pills.append({
            "id": r.id,
            "name": r.role_name,
            "count": r.users.count(),
            "color": color_map.get(r.id, "gray"),
        })

    context = {
        "roles": roles,
        "role_pills": role_pills,
        "total_roles": total_roles,
        "total_users": total_users,
        "active_users": active_users,
        "unassigned_users": unassigned_users,
        "active_pct": active_pct,
        "unassigned_pct": unassigned_pct,
        "roles_this_month": roles_this_month,
        "users_this_month": users_this_month,
    }
    return render(request, "role.html", context)


@login_required
@require_http_methods(["GET"])
def role_assignments_json(request):
    try:
        page = int(request.GET.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(request.GET.get("page_size", 10))
    except (TypeError, ValueError):
        page_size = 10

    role_id = request.GET.get("role", "").strip()
    search = request.GET.get("search", "").strip()

    users = User.objects.select_related("role").all().order_by("-created_at")

    if role_id:
        users = users.filter(role_id=role_id)

    if search:
        users = users.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(username__icontains=search)
            | Q(email__icontains=search)
            | Q(university_id__icontains=search)
            | Q(role__role_name__icontains=search)
        )

    total = users.count()
    paginator = Paginator(users, page_size)
    page_obj = paginator.get_page(page)

    color_map = _role_color_map()

   
    STATUS_MAP = {
        "ACTIVE": "active",
        "INACTIVE": "inactive",
        "PENDING": "pending",
        "SUSPENDED": "inactive",
    }

    data = []
    for u in page_obj:
        full_name = f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username
        data.append({
            "id": u.id,
            "name": full_name,
            "email": u.email,
            "uid": u.university_id or "—",
            "role": u.role.role_name if u.role else "Unassigned",
            "role_id": u.role_id,
            "role_color": color_map.get(u.role_id, "gray"),
            "status": STATUS_MAP.get(u.account_status, "inactive"),
            "assigned": u.updated_at.strftime("%Y-%m-%d") if u.updated_at else "",
        })

    return JsonResponse({
        "results": data,
        "total": total,
        "page": page_obj.number,
        "total_pages": paginator.num_pages,
        "page_size": page_size,
    })

@require_permission("userrole_create")
@login_required
@require_http_methods(["POST"])  
def role_create_json(request):
    """Create a new UserRole from the Add Role modal."""
    name = (request.POST.get("role_name") or "").strip()
    description = (request.POST.get("description") or "").strip()
    user_type = (request.POST.get("user_type") or "").strip() 

    if not name:
        return JsonResponse(
            {"ok": False, "errors": {"role_name": ["Role name is required."]}},
            status=400,
        )
    if len(name) > 100:
        return JsonResponse(
            {"ok": False, "errors": {"role_name": ["Role name must be 100 characters or fewer."]}},
            status=400,
        )
    if UserRole.objects.filter(role_name__iexact=name).exists():
        return JsonResponse(
            {"ok": False, "errors": {"role_name": ["A role with this name already exists."]}},
            status=400,
        )
   

    role_obj = UserRole.objects.create(role_name=name, description=description,user_type= user_type)

    AuditLogger.log(
        request=request,
        action="CREATE",
        module="RoleManagement",
        object_type="UserRole",
        object_id=role_obj.id,
        description=f"Created role '{role_obj.role_name}'.",
        after_data={"role_name": role_obj.role_name, "description": role_obj.description, "user_type": role_obj.user_type},
        status="SUCCESS",
    )

    return JsonResponse({
        "ok": True,
        "role": {
            "id": role_obj.id,
            "name": role_obj.role_name,
            "description": role_obj.description or "",
            "count": 0,
        },
    })

@require_permission("userrole_update")
@login_required
@require_http_methods(["POST"])
def role_unassign_json(request, uid):
    """Remove the role from a single user (used by the row-level delete action)."""
    user_obj = get_object_or_404(User, id=uid)
    before = AuditLogger.model_to_dict(user_obj, ["role"])
    user_obj.role = None
    user_obj.save(update_fields=["role"])
    AuditLogger.log(
        request=request,
        action="ROLE_REMOVE",
        module="RoleManagement",
        object_type="User",
        object_id=user_obj.id,
        description=f"Removed role from user '{user_obj.username}'.",
        before_data=before,
        after_data={"role": None},
        status="SUCCESS",
    )
    return JsonResponse({"ok": True})

# ************************************************ Arun Code **********************************************************

@login_required
@require_http_methods(["GET"])
def check_field_unique_json(request):
    """
    GET /dashboard/users/check-unique/?field=username&value=facultytest
    GET /dashboard/users/check-unique/?field=university_email&value=x@wisc.edu
    Optional &exclude_id=<user id> when editing, so a user's own existing
    value doesn't flag itself as a duplicate.
    """
    field = request.GET.get("field", "").strip()
    value = request.GET.get("value", "").strip()
    exclude_id = request.GET.get("exclude_id", "").strip()

    if not value:
        return JsonResponse({"taken": False})

    FIELD_MAP = {
        "username":       (User, "username", True),
        # Jack Code Start's
        "ssn_number":     (User, "ssn_number", True),
        # Jack Code End's
        "email":          (User, "email", True),
        "university_id":  (User, "university_id", True),
        "mobile_number":  (User, "mobile_number", True),

        # Student
        "student_number":    (StudentProfile, "student_number", False),
        "university_email":  (StudentProfile, "university_email", False),

        "faculty_employee_id": (FacultyProfile, "employee_id", False),
        "faculty_email":        (FacultyProfile, "email", False),

        # Staff
        "staff_employee_id":  (StaffProfile, "employee_id", False),
        "staff_work_email":    (StaffProfile, "work_email", False),
    }

    mapping = FIELD_MAP.get(field)
    if not mapping:
        return JsonResponse({"taken": False})

    Model, column, is_user_model = mapping

    qs = Model.objects.filter(**{column: value})
    if exclude_id:
        if is_user_model:
            qs = qs.exclude(pk=exclude_id)
        else:
            qs = qs.exclude(user_id=exclude_id)

    return JsonResponse({"taken": qs.exists()})


from django.http import JsonResponse

@login_required
def get_schools(request):
    university_id = request.GET.get("university_id")

    schools = School.objects.filter(
        university_id=university_id,
        status="ACTIVE"
    ).order_by("school_name")

    return JsonResponse([
        {
            "id": str(s.school_id),
            "name": s.school_name,
        }
        for s in schools
    ], safe=False)

from Admin.bela_admin.models import Department

@login_required
def get_departments(request):
    school_id = request.GET.get("school_id")

    departments = Department.objects.filter(
        school_id=school_id,
        status="ACTIVE"
    ).order_by("department_name")

    data = [
        {
            "id": department.department_id,
            "name": department.department_name,
        }
        for department in departments
    ]

    return JsonResponse(data, safe=False)

@login_required
def get_schools(request):

    university_id = request.GET.get("university_id")

    schools = School.objects.filter(
        university_id=university_id,
        status="ACTIVE"
    ).order_by("school_name")

    data = [
        {
            "id": str(school.school_id),
            "name": school.school_name,
        }
        for school in schools
    ]

    return JsonResponse(data, safe=False)

@login_required
def get_degrees(request):

    degrees = Degree.objects.filter(
        status="ACTIVE"
    ).order_by("degree_name")

    return JsonResponse([
        {
            "id": d.degree_id,
            "name": d.degree_name,
        }
        for d in degrees
    ], safe=False)

@login_required
def get_programs(request):

    department_id = request.GET.get("department_id")
    degree_id = request.GET.get("degree_id")

    programs = AcademicProgram.objects.filter(
        department_id=department_id,
        degree_id=degree_id,
        status="ACTIVE"
    ).order_by("program_name")

    return JsonResponse([
        {
            "id": p.program_id,
            "name": p.program_name,
        }
        for p in programs
    ], safe=False)

from django.core.exceptions import ValidationError
from django.db import transaction

# Admin/views.py - Complete fixed user_create

@require_page_access("user_create_page")
# @require_page_access("user_create_page", user_types=["admin"])
@require_permission("user_create")
@login_required
def user_create(request):
    roles = UserRole.objects.all().order_by("role_name").exclude(role_name="Administrator")

    universities = University.objects.filter(status="ACTIVE").order_by("university_name")
    degrees = Degree.objects.filter(status="ACTIVE").order_by("degree_name")
    departments = Department.objects.filter(status="ACTIVE").order_by("department_name")
    courses = Course.objects.filter(status="ACTIVE").select_related("department").order_by("course_name")

    if request.method == "POST":
        form = UserCreateForm(request.POST, request.FILES)
        if form.is_valid():
            user_type = request.POST.get("user_type")
            
            # Debug print
            print(f"👤 User Type: {user_type}")
            print(f"📌 Department ID from form: {request.POST.get('department_id')}")

            try:
                with transaction.atomic():
                    user, password = form.save()

                    user.is_student = False
                    user.is_faculty = False
                    user.is_admin = False
                    user.is_staff = False

                    is_hostel_admin = request.POST.get("is_hostel_admin") == "yes"

                    if is_hostel_admin:
                        user.is_hostel_admin = True
                        user.is_staff = True

                    if user_type == "student":
                        user.is_student = True
                        user.save()
                        save_student_details(request, user)

                        
                        from Students.models import StudentProfile
                        from Admin.bela_admin.models import AcademicProgram
                        
                        department_id = request.POST.get("department_id")
                        
                        if department_id:
                            # Find program in this department
                            program = AcademicProgram.objects.filter(
                                department_id=department_id,
                                status='ACTIVE'
                            ).first()
                            
                            if program:
                                # Get or create StudentProfile
                                profile, created = StudentProfile.objects.get_or_create(user=user)
                                profile.program_id = program.program_id
                                profile.save()
                                print(f" Assigned {user.full_name} to {program.program_name}")
                            else:
                                print(f" No program found for department {department_id}")
                        else:
                            print(" No department selected, assigning default program")
                            default_program = AcademicProgram.objects.filter(
                                department_id=1,
                                status='ACTIVE'
                            ).first()
                            if default_program:
                                profile, created = StudentProfile.objects.get_or_create(user=user)
                                profile.program_id = default_program.program_id
                                profile.save()
                                print(f" Assigned {user.full_name} to default: {default_program.program_name}")

                    elif user_type == "faculty":
                        user.is_faculty = True
                        user.save()
                        save_faculty_details(request, user)

                    elif user_type == "staff":
                        user.is_staff = True
                        user.save()
                        save_staff_details(request, user)

                    elif user_type == "admin":
                        user.is_admin = True
                        user.save()

                    user.save()
                    has_firearm = request.POST.get("has_firearm") == "yes"
                    if has_firearm:
                        save_firearm_details(request, user)

                AuditLogger.log(
                    request=request,
                    action="CREATE",
                    module="UserManagement",
                    object_type="User",
                    object_id=user.id,
                    description=f"Created user '{user.username}'.",
                    after_data=AuditLogger.model_to_dict(
                        user, ["username", "email", "first_name", "last_name", "role"]
                    ),
                    status="SUCCESS",
                )

                return render(request, "user_create.html", {
                    "form": UserCreateForm(),
                    "roles": roles,
                    "success": True,
                    "new_username": user.username,
                    "new_password": password,
                })

            except ValidationError as e:
                error_messages = e.messages if hasattr(e, "messages") else [str(e)]
                for msg in error_messages:
                    form.add_error(None, msg)

                print("STUDENT/FACULTY/STAFF DETAIL VALIDATION FAILED:")
                for msg in error_messages:
                    print(f"  - {msg}")

        else:
            print("FORM IS INVALID. Errors:")
            for field, errors in form.errors.items():
                print(f"  - {field}: {errors}")
    else:
        form = UserCreateForm()

    return render(request, "user_create.html", {
        "form": form,
        "roles": roles,
        "departments": departments,
        "universities": universities,
        "degrees": degrees,
        "courses": courses,
        "suggested_student_number": suggested_student_number_for_context(),
        "suggested_faculty_employee_id": suggested_faculty_id_for_context(),
        "suggested_staff_employee_id": suggested_staff_id_for_context(),
        "student_number_prefix": "STU",
        "existing_staff": StaffProfile.objects.select_related("user").order_by("employee_id"),
    })

# ************************************************ Arun Code **********************************************************

@login_required
def users_json(request):

    # users = User.objects.all()
    users = User.objects.exclude(
        is_superuser=True
    ).exclude(
        is_super_admin=True
    )
    data = []

    for u in users:

        if u.is_admin:
            user_type = "admin"
        elif u.is_faculty:
            user_type = "faculty"
        elif u.is_staff:
            user_type = "staff"
        elif u.is_student:
            user_type = "student"
        else:
            user_type = ""

        data.append({
            "id": u.id,
            "uuid": str(u.uuid), 
            "username": u.username,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "full_name": f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username,
            "email": u.email,
            "university_id": u.university_id,
            "gender": u.gender,
            "account_status": u.account_status,
            "created_at": u.created_at.strftime('%d %b %Y %I:%M %p') if u.created_at else '',
            "is_student": u.is_student,
            "is_faculty": u.is_faculty,
            "is_admin": u.is_admin,
            "is_staff": u.is_staff,
            "role": user_type,
            "profile_photo": (
                u.profile_photo.url if u.profile_photo else ""
            ),
        })

    return JsonResponse({"users": data})



#### swetha's code #####
@require_permission("user_update")
@login_required
def user_edit(request, user_id):
    user_obj = get_object_or_404(User, uuid=user_id)

    student = StudentProfile.objects.filter(user=user_obj).first()

    faculty = FacultyProfile.objects.filter(user=user_obj).first()
    staff = StaffProfile.objects.filter(user=user_obj).first()
    
    position = StaffPosition.objects.filter(staff=staff).first() if staff else None
  

    if student:
        user_type = "student"
    elif faculty:
        user_type = "faculty"
    elif staff:
        user_type = "staff"
    elif user_obj.is_admin:
        user_type = "admin"
    else:
        user_type = "user"

    context = {
        "user_obj": user_obj,
        "student": student,
        "faculty": faculty,
        "staff": staff,
        "position":position,
        "user_type": user_type,
        "user_initial": user_obj.first_name[:1].upper() if user_obj.first_name else "U",
       
        # choices
        "gender_choices": User.GENDER_CHOICES,
        "account_status_choices": User.STATUS_CHOICES,
        "employment_status_choices": FacultyProfile.EMPLOYMENT_STATUS_CHOICES,
        "citizenship_choices": StudentProfile.CITIZENSHIP_CHOICES,
        "marital_choices": StudentProfile.MARITAL_STATUS_CHOICES,
        "student_status_choices": StudentProfile.STATUS_CHOICES,
        "academic_level_choices": StudentProfile.ACADEMIC_LEVEL_CHOICES,
        "current_status_choices": StudentProfile.STATUS_CHOICES,

        "student_address_type_choices": StudentAddress.ADDRESS_TYPE_CHOICES,
        "address_type_choices": StaffAddress.ADDRESS_TYPE_CHOICES,
        "document_type_choices": StaffDocument.DOCUMENT_TYPE_CHOICES,
        "employment_type_choices": StaffProfile.EMPLOYMENT_TYPE_CHOICES,
        "position_status_choices": StaffPosition.POSITION_STATUS_CHOICES,


        # dropdowns
        "role_options": UserRole.objects.all(),
        "university_options": University.objects.all(),
        "department_options": Department.objects.all(),
         "degree_options": Degree.objects.all(),
        "advisor_options": FacultyProfile.objects.all(),
        "school_options": School.objects.all(),
        "program_options": AcademicProgram.objects.all(),

        "faculty_rank_options": FacultyRank.objects.all(),
    }

    if staff:
        context["supervisor_options"] = StaffProfile.objects.exclude(
            pk=staff.pk
        ).select_related("user")
    return render(request, "user__edit.html", context)

@login_required
def user_update(request, user_id):
    user_obj = get_object_or_404(User, uuid=user_id)

    if request.method == "POST":

        user_obj.first_name = request.POST.get("first_name")
        user_obj.middle_name = request.POST.get("middle_name")
        user_obj.last_name = request.POST.get("last_name")
        # user_obj.username = request.POST.get("username")
        user_obj.email = request.POST.get("email")
        user_obj.mobile_number = request.POST.get("mobile_number")
        user_obj.gender = request.POST.get("gender")
        user_obj.date_of_birth = request.POST.get("date_of_birth") or None
        user_obj.account_status = request.POST.get("account_status")
        user_obj.is_super_admin = "is_super_admin" in request.POST
        user_obj.is_full_crud = "is_full_crud" in request.POST


        user_obj.email_verified = "email_verified" in request.POST
        user_obj.mobile_verified = "mobile_verified" in request.POST

        role = request.POST.get("admin-role_id")
        if role:
            user_obj.role_id = role
        else:
            user_obj.role = None

        # if request.FILES.get("profile_photo"):
        #     user_obj.profile_photo = request.FILES["profile_photo"]

        profile_photo = request.FILES.get("profile_photo")

        if profile_photo:
            allowed = [
                "image/jpeg",
                "image/png",
                "image/jpg",
                "image/webp"
            ]

            if profile_photo.content_type not in allowed:
                messages.error(
                    request,
                    "Only JPG, PNG and WEBP images are allowed."
                )
                return redirect("user_edit", user_obj.uuid)

            user_obj.profile_photo = profile_photo
        user_obj.save()


        # ---------------- Student ----------------

        student = StudentProfile.objects.filter(user=user_obj).first()

        if student:
            student.preferred_name = request.POST.get("student-preferred_name")
            student.university_email = request.POST.get("student-university_email")
            student.personal_email = request.POST.get("student-personal_email")
            student.citizenship_status = (request.POST.get("student-citizenship_status") or student.citizenship_status)
            student.marital_status = (request.POST.get("student-marital_status") or student.marital_status)
            student.academic_level = (request.POST.get("student-academic_level") or student.academic_level)
            student.current_status = (request.POST.get("student-current_status") or student.current_status)
            student.cumulative_gpa = request.POST.get("student-cumulative_gpa") or None
            student.admission_date = request.POST.get("student-admission_date") or student.admission_date
            student.expected_graduation_date = request.POST.get("student-expected_graduation_date") or student.expected_graduation_date
            student.save()

            # ---------------- Student Academic Profile ----------------

            academic, created = StudentAcademicProfile.objects.get_or_create(
                student=student
            )

            academic.university_id = request.POST.get("academic-university_id") or None
            academic.school_id = request.POST.get("academic-school_id") or None
            academic.department_id = request.POST.get("academic-department_id") or None
            academic.degree_id = request.POST.get("academic-degree_id") or None
            academic.program_id = request.POST.get("academic-program_id") or None

            academic.major = request.POST.get("academic-major")
            academic.minor = request.POST.get("academic-minor")
            academic.concentration = request.POST.get("academic-concentration")
            academic.catalog_year = request.POST.get("academic-catalog_year") 
            academic.advisor_id = request.POST.get("academic-advisor_id") or None

            academic.save()

            # Student Addresses
            address_ids = request.POST.getlist("student-address_id[]")
            address_types = request.POST.getlist("student-address_type[]")
            line1s = request.POST.getlist("student-address_line_1[]")
            line2s = request.POST.getlist("student-address_line_2[]")
            cities = request.POST.getlist("student-city[]")
            states = request.POST.getlist("student-state[]")
            postal_codes = request.POST.getlist("student-postal_code[]")
            countries = request.POST.getlist("student-country[]")

            existing_addresses = list(student.addresses.all())
            saved_address_ids = []

            for i in range(len(address_types)):

                if i < len(address_ids) and address_ids[i].strip():
                  address = StudentAddress.objects.filter(id=address_ids[i],student=student).first()
                else:
                    address = StudentAddress(student=student)
                
                if not address:
                    address = StudentAddress(student=student)

                address.address_type = address_types[i]
                address.address_line_1 = line1s[i] if i < len(line1s) else ""
                address.address_line_2 = line2s[i] if i < len(line2s) else ""
                address.city = cities[i] if i < len(cities) else ""
                address.state = states[i] if i < len(states) else ""
                address.postal_code = postal_codes[i] if i < len(postal_codes) else ""
                address.country = countries[i] if i < len(countries) else ""

                address.save()
                saved_address_ids.append(address.id)

            StudentAddress.objects.filter(
                student=student
            ).exclude(
                id__in=saved_address_ids
            ).delete()

            # Student Emergency Contacts
            contact_ids = request.POST.getlist("student-emergency_id[]")
            names = request.POST.getlist("student-emergency_name[]")
            relationships = request.POST.getlist("student-emergency_relationship[]")
            phones = request.POST.getlist("student-emergency_phone[]")
            emails = request.POST.getlist("student-emergency_email[]")
            priorities = request.POST.getlist("student-emergency_priority[]")

            # existing_contacts = list(student.emergency_contacts.all())
            saved_contact_ids = []

            for i in range(len(names)):

                if not names[i].strip():
                    continue

                if i < len(contact_ids) and contact_ids[i].strip():
                    contact = StudentEmergencyContact.objects.filter(
                        id=contact_ids[i],
                        student=student
                    ).first()
                else:
                    contact = StudentEmergencyContact(student=student)

                if not contact:
                    contact = StudentEmergencyContact(student=student)
            
                contact.contact_name = names[i]
                contact.relationship = relationships[i] if i < len(relationships) else ""
                contact.phone_number = phones[i] if i < len(phones) else ""
                contact.email = emails[i] if i < len(emails) else ""
                contact.priority = (priorities[i] if i < len(priorities) and priorities[i] else 1 )

                contact.save()
                saved_contact_ids.append(contact.id)

            StudentEmergencyContact.objects.filter(student=student ).exclude(  id__in=saved_contact_ids).delete()

        # ---------------- Faculty ----------------

        faculty = FacultyProfile.objects.filter(user=user_obj).first()

        if faculty:
            existing_ids = []
            faculty.preferred_name = request.POST.get("faculty-preferred_name")
            faculty.email = request.POST.get("faculty-email")
            faculty.phone = request.POST.get("faculty-phone")
            faculty.office_location = request.POST.get("faculty-office_location")
            faculty.department_id = request.POST.get("faculty-department_id") or None
            faculty.faculty_rank_id = request.POST.get("faculty-faculty_rank_id") or None
            faculty.hire_date = request.POST.get("faculty-hire_date") or None
            faculty.employment_status = (request.POST.get("faculty-employment_status") or faculty.employment_status)
            faculty.employment_status = (request.POST.get("faculty-employment_status")or faculty.employment_status)
            faculty.biography = request.POST.get("faculty-biography")
            faculty.save()
            # ---------------- Faculty Education ----------------

            education_ids = request.POST.getlist("education_id")
            degrees = request.POST.getlist("education_degree")
            fields = request.POST.getlist("education_field")
            institutions = request.POST.getlist("education_institution")
            years = request.POST.getlist("education_year")

            

            for i in range(len(degrees)):
                degree = degrees[i].strip()
                if not degree:
                    continue
                edu = None
                if i < len(education_ids) and education_ids[i]:
                    edu = FacultyEducation.objects.filter(id=education_ids[i],faculty=faculty).first()

                if not edu:
                     edu = FacultyEducation(faculty=faculty)

                edu.degree = degree
                edu.field_of_study = fields[i] if i < len(fields) else ""
                edu.institution_name = institutions[i] if i < len(institutions) else ""
                # edu.graduation_year = years[i] or None
                year = years[i].strip() if i < len(years) else ""

                if not year:
                    edu.graduation_year = None
                elif not year.isdigit():
                    messages.error(request, "Graduation year must contain only numbers.")
                    return redirect("user_edit", user_obj.uuid)
                elif len(year) != 4:
                    messages.error(request, "Graduation year must be exactly 4 digits.")
                    return redirect("user_edit", user_obj.uuid)
                else:
                    edu.graduation_year = int(year)

                edu.save()

                existing_ids.append(edu.id)

            # Delete removed education records
            FacultyEducation.objects.filter(faculty=faculty).exclude(id__in=existing_ids).delete()

        # ---------------- Staff ----------------

        staff = StaffProfile.objects.filter(user=user_obj).first()

        if staff:

            # Staff Profile
            staff.preferred_name = request.POST.get("staff-preferred_name")
            staff.work_email = request.POST.get("staff-work_email")
            staff.personal_email = request.POST.get("staff-personal_email")
            staff.office_phone = request.POST.get("staff-office_phone")
            staff.hire_date = request.POST.get("staff-hire_date") or None
            staff.employment_status = request.POST.get("staff-employment_status")
            staff.employment_type = request.POST.get("staff-employment_type")
            staff.supervisor_id = request.POST.get("staff-supervisor") or None
          
            staff.save()

            # Position
            position = StaffPosition.objects.filter(staff=staff).first()

            if position:
                position.job_title = (
                    request.POST.get("staff-job_title")
                    or position.job_title
                )
                position.department_id = (
                    request.POST.get("staff-department_id")
                    or position.department_id
                )
                position.unit_id = (
                    request.POST.get("staff-unit_id")
                    or position.unit_id
                )
                position.position_start_date = (
                    request.POST.get("staff-position_start_date")
                    or position.position_start_date
                )
                position.position_status = (
                    request.POST.get("staff-position_status")
                    or position.position_status
                )
               
                position.save()

            # Addresses
            address_types = request.POST.getlist("staff-address_type[]")
            line1s = request.POST.getlist("staff-address_line_1[]")
            line2s = request.POST.getlist("staff-address_line_2[]")
            cities = request.POST.getlist("staff-city[]")
            states = request.POST.getlist("staff-state[]")
            postal_codes = request.POST.getlist("staff-postal_code[]")
            countries = request.POST.getlist("staff-country[]")

            existing_addresses = list(staff.addresses.all())
            saved_address_ids = []

            for i in range(len(address_types)):

                if i < len(existing_addresses):
                    address = existing_addresses[i]
                else:
                    address = StaffAddress(staff=staff)

                address.address_type = address_types[i]
                address.address_line_1 = line1s[i] if i < len(line1s) else ""
                address.address_line_2 = line2s[i] if i < len(line2s) else ""
                address.city = cities[i] if i < len(cities) else ""
                address.state = states[i] if i < len(states) else ""
                address.postal_code = postal_codes[i] if i < len(postal_codes) else ""
                address.country = countries[i] if i < len(countries) else ""

                address.save()
                saved_address_ids.append(address.id)

            StaffAddress.objects.filter(
                staff=staff
            ).exclude(
                id__in=saved_address_ids
            ).delete()

            # ---------------------------------------------------
            # Emergency Contacts
            # ---------------------------------------------------

            names = request.POST.getlist("staff-emergency_name[]")
            relationships = request.POST.getlist("staff-emergency_relationship[]")
            phones = request.POST.getlist("staff-emergency_phone[]")
            emails = request.POST.getlist("staff-emergency_email[]")
            priorities = request.POST.getlist("staff-emergency_priority[]")

            existing_contacts = list(staff.emergency_contacts.all())
            saved_contact_ids = []

            for i in range(len(names)):

                if not names[i].strip():
                    continue

                if i < len(existing_contacts):
                    contact = existing_contacts[i]
                else:
                    contact = StaffEmergencyContact(staff=staff)

                contact.contact_name = names[i]
                contact.relationship = (
                    relationships[i]
                    if i < len(relationships)
                    else ""
                )
                contact.phone_number = (
                    phones[i]
                    if i < len(phones)
                    else ""
                )
                contact.email = (
                    emails[i]
                    if i < len(emails)
                    else ""
                )
                contact.priority = (
                    priorities[i]
                    if i < len(priorities) and priorities[i]
                    else 1
                )

                contact.save()
                saved_contact_ids.append(contact.id)

            StaffEmergencyContact.objects.filter(
                staff=staff
            ).exclude(
                id__in=saved_contact_ids
            ).delete()

            # ---------------------------------------------------
    # Staff Education
    # ---------------------------------------------------

        education_ids = request.POST.getlist("staff-education_id[]")
        degrees = request.POST.getlist("staff-degree[]")
        institutions = request.POST.getlist("staff-institution_name[]")
        fields = request.POST.getlist("staff-field_of_study[]")
        years = request.POST.getlist("staff-graduation_year[]")

        saved_ids = []

        for i in range(len(degrees)):

            if not degrees[i].strip():
                continue

            edu = None

            if i < len(education_ids) and education_ids[i].strip():
                edu = StaffEducation.objects.filter(
                    id=education_ids[i],
                    staff=staff
                ).first()

            if not edu:
                edu = StaffEducation(staff=staff)

            edu.degree = degrees[i]
            edu.institution_name = institutions[i] if i < len(institutions) else ""
            edu.field_of_study = fields[i] if i < len(fields) else ""

            year = years[i].strip() if i < len(years) else ""

            if not year:
                edu.graduation_year = None
            elif not year.isdigit():
                messages.error(request, "Graduation year must contain only numbers.")
                return redirect("user_edit", user_obj.uuid)
            elif len(year) != 4:
                messages.error(request, "Graduation year must be exactly 4 digits.")
                return redirect("user_edit", user_obj.uuid)
            else:
                edu.graduation_year = int(year)

            edu.save()
            saved_ids.append(edu.id)

        StaffEducation.objects.filter(
            staff=staff
        ).exclude(
            id__in=saved_ids
        ).delete()


        # ---------------------------------------------------
        # Staff Certifications
        # ---------------------------------------------------

        cert_ids = request.POST.getlist("staff-certification_id[]")
        cert_names = request.POST.getlist("staff-certification_name[]")
        orgs = request.POST.getlist("staff-issuing_organization[]")
        issue_dates = request.POST.getlist("staff-issue_date[]")
        expiry_dates = request.POST.getlist("staff-expiration_date[]")

        saved_ids = []

        for i in range(len(cert_names)):

            if not cert_names[i].strip():
                continue

            cert = None

            if i < len(cert_ids) and cert_ids[i].strip():
                cert = StaffCertification.objects.filter(
                    id=cert_ids[i],
                    staff=staff
                ).first()

            if not cert:
                cert = StaffCertification(staff=staff)

            cert.certification_name = cert_names[i]
            cert.issuing_organization = orgs[i] if i < len(orgs) else ""
            cert.issue_date = issue_dates[i] or None
            cert.expiration_date = expiry_dates[i] or None

            cert.save()
            saved_ids.append(cert.id)

        StaffCertification.objects.filter(
            staff=staff
        ).exclude(
            id__in=saved_ids
        ).delete()


        # ---------------------------------------------------
        # Staff Documents
        # ---------------------------------------------------
        print("DOC IDS :", request.POST.getlist("staff-document_id[]"))
        print("DOC TYPES :", request.POST.getlist("staff-document_type[]"))
        print("DOC NAMES :", request.POST.getlist("staff-file_name[]"))
        print("FILES :", request.FILES.getlist("staff-new-file[]"))

        doc_ids = request.POST.getlist("staff-document_id[]")
        doc_types = request.POST.getlist("staff-document_type[]")
        file_names = request.POST.getlist("staff-file_name[]")
        # files = request.FILES.getlist("staff-file[]")
        # existing replace
        new_files = request.FILES.getlist("staff-new-file[]")

        saved_doc_ids = []

        for i in range(len(doc_types)):

            doc = None

            # Existing document
            if i < len(doc_ids) and doc_ids[i].strip():

                doc = StaffDocument.objects.filter(
                    id=doc_ids[i],
                    staff=staff
                ).first()

            if doc:

                doc.document_type = doc_types[i]
                doc.file_name = file_names[i] if i < len(file_names) else doc.file_name

                # Replace file only if new uploaded
                if i < len(new_files) and new_files[i]:
                    doc.file = new_files[i]

                doc.verification_status = "PENDING"
                doc.save()

                saved_doc_ids.append(doc.id)

            else:

                # New document
                uploaded_file = new_files[i] if i < len(new_files) else None

                if uploaded_file:

                    new_doc = StaffDocument.objects.create(
                        staff=staff,
                        document_type=doc_types[i],
                        file_name=file_names[i] if i < len(file_names) and file_names[i] else uploaded_file.name,
                        file=uploaded_file,
                        verification_status="PENDING"
                    )

                    saved_doc_ids.append(new_doc.id)

        # Delete removed documents

        StaffDocument.objects.filter(
            staff=staff
        ).exclude(
            id__in=saved_doc_ids
        ).delete()
                    

        # if staff:
        #     staff.preferred_name = request.POST.get("staff-preferred_name")
        #     staff.work_email = request.POST.get("staff-work_email")
        #     staff.personal_email = request.POST.get("staff-personal_email")
        #     staff.office_phone = request.POST.get("staff-office_phone")
        #     staff.hire_date = request.POST.get("staff-hire_date") or None
        #     staff.employment_status = request.POST.get("staff-employment_status")
        #     staff.employment_type = request.POST.get("staff-employment_type")
        #     staff.supervisor_id = request.POST.get("staff-supervisor_id") or None
        #     staff.save()
        #     position = StaffPosition.objects.filter(staff=staff).first()

        #     if position:
        #         position.job_title = request.POST.get("staff-job_title") or position.job_title
        #         # position.school_id = request.POST.get("staff-school") or position.school_id
        #         position.department_id = request.POST.get("staff-department_id") or position.department_id
        #         position.unit_id = request.POST.get("staff-unit_id") or position.unit_id
        #         position.position_start_date = request.POST.get("staff-position_start_date") or position.position_start_date 
        #         position.position_status = request.POST.get("staff-position_status") or position.position_status
        #         position.save()

        #         address_types = request.POST.getlist("staff-address_type[]")
        #         line1s = request.POST.getlist("staff-address_line_1[]")
        #         line2s = request.POST.getlist("staff-address_line_2[]")
        #         cities = request.POST.getlist("staff-city[]")
        #         states = request.POST.getlist("staff-state[]")
        #         postal_codes = request.POST.getlist("staff-postal_code[]")
        #         countries = request.POST.getlist("staff-country[]")

        #         existing_addresses = list(staff.addresses.all())

        #         for i in range(len(address_types)):

        #             if i < len(existing_addresses):
        #                 address = existing_addresses[i]
        #             else:
        #                 address = StaffAddress(staff=staff)

        #             address.address_type = address_types[i]
        #             address.address_line_1 = line1s[i]
        #             address.address_line_2 = line2s[i]
        #             address.city = cities[i]
        #             address.state = states[i]
        #             address.postal_code = postal_codes[i]
        #             address.country = countries[i]

        #             address.save()

        #         existing_contacts = list(staff.emergency_contacts.all())
        #         names = request.POST.getlist("staff-emergency_name[]")
        #         relationships = request.POST.getlist("staff-emergency_relationship[]")
        #         phones = request.POST.getlist("staff-emergency_phone[]")
        #         emails = request.POST.getlist("staff-emergency_email[]")
        #         priorities = request.POST.getlist("staff-emergency_priority[]")

        #         for i in range(len(names)):
        #             if i < len(existing_contacts):
        #                     contact = existing_contacts[i]
        #             else:
        #                 contact = StaffEmergencyContact(staff=staff)
        #                 contact.contact_name = names[i]
        #                 contact.relationship = relationships[i]
        #                 contact.phone_number = phones[i]
        #                 contact.email = emails[i]
        #                 contact.priority = priorities[i] or 1

        #                 contact.save()

        #             # Delete removed contacts
                   
        #         if len(existing_contacts) > len(names):
        #             for contact in existing_contacts[len(names):]:
        #                 contact.delete()

        #             education_ids = request.POST.getlist("staff-education_id[]")
        #             degrees = request.POST.getlist("staff-degree[]")
        #             institutions = request.POST.getlist("staff-institution_name[]")
        #             fields = request.POST.getlist("staff-field_of_study[]")
        #             years = request.POST.getlist("staff-graduation_year[]")

        #             saved_ids = []

        #             for i in range(len(degrees)):
        #                 if not degrees[i].strip():
        #                     continue

        #                 if i < len(education_ids) and education_ids[i]:
        #                     edu = StaffEducation.objects.filter(
        #                         id=education_ids[i],
        #                         staff=staff
        #                     ).first()
        #                 else:
        #                     edu = StaffEducation(staff=staff)

        #                 edu.degree = degrees[i]
        #                 edu.institution_name = institutions[i]
        #                 edu.field_of_study = fields[i]
        #                 edu.graduation_year = years[i] or None
        #                 edu.save()

        #                 saved_ids.append(edu.id)
                # #satff eductaions 
                # StaffEducation.objects.filter(staff=staff).exclude(id__in=saved_ids).delete()
                # cert_ids = request.POST.getlist("staff-certification_id[]")
                # names = request.POST.getlist("staff-certification_name[]")
                # orgs = request.POST.getlist("staff-issuing_organization[]")
                # issue_dates = request.POST.getlist("staff-issue_date[]")
                # expiry_dates = request.POST.getlist("staff-expiration_date[]")
                # saved_ids = []
                # for i in range(len(names)):
                #     if not names[i].strip():
                #         continue

                #     if i < len(cert_ids) and cert_ids[i]:
                #             cert = StaffCertification.objects.filter(
                #                 id=cert_ids[i],
                #                 staff=staff
                #             ).first()
                #     else:
                #             cert = StaffCertification(staff=staff)

                #     cert.certification_name = names[i]
                #     cert.issuing_organization = orgs[i]
                #     cert.issue_date = issue_dates[i] or None
                #     cert.expiration_date = expiry_dates[i] or None
                #     cert.save()
                #     saved_ids.append(cert.id)
                #     StaffCertification.objects.filter(staff=staff).exclude(id__in=saved_ids).delete()

                #     # Existing documents update
                #     # ---------------- Staff Documents ----------------

                # existing_doc_ids = []

                #     # Existing documents
                # doc_ids = request.POST.getlist("staff-document_id[]")
                # doc_types = request.POST.getlist("staff-document_type[]")
                # file_names = request.POST.getlist("staff-file_name[]")
                # files = request.FILES.getlist("staff-file[]")
                # for i in range(len(doc_types)):
                #     doc = None
                #     doc_id = doc_ids[i].strip() if i < len(doc_ids) else ""
                #     if doc_id.isdigit():
                #         doc = StaffDocument.objects.filter(
                #                 id=int(doc_id),
                #                 staff=staff
                #             ).first()

                #     if not doc:
                #         continue

                #     doc.document_type = doc_types[i]
                #     if i < len(file_names):
                #         doc.file_name = file_names[i]

                #     if i < len(files) and files[i]:
                #         doc.file = files[i]

                #     doc.verification_status = "PENDING"
                #     doc.save()

                #     existing_doc_ids.append(doc.id)


                #     # Newly added documents
                #     new_types = request.POST.getlist("staff-new-document_type[]")
                #     new_names = request.POST.getlist("staff-new-file_name[]")
                #     new_files = request.FILES.getlist("staff-new-file[]")

                #     for i, file in enumerate(new_files):

                #         if not file:
                #             continue

                #         StaffDocument.objects.create(
                #             staff=staff,
                #             document_type=new_types[i] if i < len(new_types) else "OTHER",
                #             file_name=new_names[i] if i < len(new_names) and new_names[i] else file.name,
                #             file=file,
                #             verification_status="PENDING",
                #         )
                

      
                                    
        messages.success(request, "User updated successfully.")
        return redirect("user_view", uid=user_obj.uuid)

    return redirect("user_edit", uid=user_obj.uuid)

##swetha's code end ######


import traceback

@login_required
@require_http_methods(["POST"])
def user_update_json(request, uid):

    try:

        user_obj = get_object_or_404(User, id=uid)

        before = AuditLogger.model_to_dict(
            user_obj, ["first_name", "last_name", "email", "mobile_number", "account_status", "role"]
        )

        form = UserCreateForm(
            request.POST,
            request.FILES,
            instance=user_obj,
            is_edit=True
        )

        if form.is_valid():

            user = form.save(commit=False, is_edit=True)

         
            role_id = request.POST.get("role")

            if role_id:
                user.role = UserRole.objects.get(id=role_id)

            user.is_student = False
            user.is_faculty = False
            user.is_admin = False
            user.is_staff = False

            user_type = request.POST.get("user_type")

            if user_type == "student":
                user.is_student = True

            elif user_type == "faculty":
                user.is_faculty = True

            elif user_type == "admin":
                user.is_admin = True

            elif user_type == "staff":
                user.is_staff = True

            user.save()

            AuditLogger.log(
                request=request,
                action="UPDATE",
                module="UserManagement",
                object_type="User",
                object_id=user.id,
                description=f"Updated user '{user.username}'.",
                before_data=before,
                after_data=AuditLogger.model_to_dict(
                    user, ["first_name", "last_name", "email", "mobile_number", "account_status", "role"]
                ),
                status="SUCCESS",
            )


            

            return JsonResponse({"ok": True})


        AuditLogger.log(
            request=request,
            action="UPDATE",
            module="UserManagement",
            object_type="User",
            object_id=uid,
            description=f"Failed to update user (uid={uid}): validation errors.",
            before_data=before,
            status="FAILED",
        )

        return JsonResponse({
            "ok": False,
            "errors": form.errors
        }, status=400)

    except Exception as e:
        traceback.print_exc()

        return JsonResponse({
            "ok": False,
            "error": str(e)
        }, status=500)


@login_required
@require_http_methods(["DELETE"])
def user_delete_json(request, uid):
    """AJAX delete — returns JSON."""
    from django.shortcuts import get_object_or_404
    user_obj = get_object_or_404(User, id=uid)
    before = AuditLogger.model_to_dict(
        user_obj, ["username", "email", "first_name", "last_name", "role", "account_status"]
    )
    deleted_username = user_obj.username
    user_obj.delete()
    AuditLogger.log(
        request=request,
        action="DELETE",
        module="UserManagement",
        object_type="User",
        object_id=uid,
        description=f"Deleted user '{deleted_username}'.",
        before_data=before,
        status="SUCCESS",
    )
    return JsonResponse({"ok": True})


VALID_STATUS_VALUES = {choice[0] for choice in User.STATUS_CHOICES}


@login_required
@require_http_methods(["POST"])
def user_status_update_json(request, uid):
   
    user_obj = get_object_or_404(User, id=uid)

    new_status = (request.POST.get("status") or "").strip().upper()

    if new_status not in VALID_STATUS_VALUES:
        AuditLogger.log(
            request=request,
            action="UPDATE",
            module="UserManagement",
            object_type="User",
            object_id=user_obj.id,
            description=f"Failed status change for user '{user_obj.username}': invalid status '{new_status}'.",
            status="FAILED",
        )
        return JsonResponse(
            {"ok": False, "error": "Invalid status value."},
            status=400,
        )

    before_status = user_obj.account_status
    user_obj.account_status = new_status
    user_obj.save(update_fields=["account_status"])

    AuditLogger.log(
        request=request,
        action="UPDATE",
        module="UserManagement",
        object_type="User",
        object_id=user_obj.id,
        description=f"Changed status of user '{user_obj.username}' from {before_status} to {new_status}.",
        before_data={"account_status": before_status},
        after_data={"account_status": new_status},
        status="SUCCESS",
    )

    return JsonResponse({"ok": True, "status": user_obj.account_status})

 
import json
 
 
@login_required
@require_http_methods(["GET"])
def role_detail_json(request, role_id):
    """
    GET /roles/<role_id>/details/
    Returns role info + all assigned users.
    """
    role_obj = get_object_or_404(UserRole, id=role_id)
    color_map = _role_color_map()
 
    STATUS_MAP = {
        "ACTIVE": "active",
        "INACTIVE": "inactive",
        "PENDING": "pending",
        "SUSPENDED": "inactive",
    }
 
    users = role_obj.users.all().order_by("first_name", "last_name")
    users_data = []
    for u in users:
        full_name = f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username
        users_data.append({
            "id": u.id,
            "name": full_name,
            "email": u.email or "",
            "uid": u.university_id or "—",
            "status": STATUS_MAP.get(u.account_status, "inactive"),
        })
 
    return JsonResponse({
        "role_id": role_obj.id,
        "role_name": role_obj.role_name,
        "description": role_obj.description or "",
        "total_users": len(users_data),
        "users": users_data,
    })
 
 
@login_required
@require_http_methods(["GET"])
def role_available_users_json(request, role_id):
    """
    GET /roles/<role_id>/available-users/?search=
    Returns users NOT currently assigned to this role.
    """
    role_obj = get_object_or_404(UserRole, id=role_id)
    search = request.GET.get("search", "").strip()
 
    users = User.objects.exclude(role=role_obj).order_by("first_name", "last_name")
 
    if search:
        users = users.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(username__icontains=search)
            | Q(email__icontains=search)
            | Q(university_id__icontains=search)
        )
 
    users = users[:20]  # cap autocomplete results
 
    data = []
    for u in users:
        full_name = f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username
        data.append({
            "id": u.id,
            "name": full_name,
            "email": u.email or "",
            "uid": u.university_id or "",
        })
 
    return JsonResponse({"users": data})
 
@require_permission("userrole_update")
@login_required
@require_http_methods(["POST"])
def role_assign_users_json(request, role_id):
   
    role_obj = get_object_or_404(UserRole, id=role_id)
 
    try:
        body = json.loads(request.body)
        user_ids = body.get("user_ids", [])
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)
 
    if not user_ids:
        return JsonResponse({"ok": False, "error": "No user IDs provided."}, status=400)
 
    updated = 0
    for uid in user_ids:
        try:
            u = User.objects.get(id=uid)
            before_role = str(u.role) if u.role else None
            u.role = role_obj
            u.save(update_fields=["role"])
            updated += 1
            AuditLogger.log(
                request=request,
                action="ROLE_ASSIGN",
                module="RoleManagement",
                object_type="User",
                object_id=u.id,
                description=f"Assigned role '{role_obj.role_name}' to user '{u.username}'.",
                before_data={"role": before_role},
                after_data={"role": role_obj.role_name},
                status="SUCCESS",
            )

        except User.DoesNotExist:
            pass
 
    total_users = role_obj.users.count()
    return JsonResponse({"ok": True, "updated": updated, "total_users": total_users})
 
@require_permission("userrole_update")
@login_required
@require_http_methods(["POST"])
def role_revoke_user_json(request, role_id):
 
    role_obj = get_object_or_404(UserRole, id=role_id)
 
    try:
        body = json.loads(request.body)
        user_id = body.get("user_id")
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)
 
    if not user_id:
        return JsonResponse({"ok": False, "error": "user_id is required."}, status=400)
 
    user_obj = get_object_or_404(User, id=user_id)
 
    # Only revoke if they actually belong to this role
    if user_obj.role_id != role_obj.id:
        return JsonResponse({"ok": False, "error": "User is not assigned to this role."}, status=400)
 
    before_role_name = role_obj.role_name
    user_obj.role = None
    user_obj.save(update_fields=["role"])

    AuditLogger.log(
        request=request,
        action="ROLE_REMOVE",
        module="RoleManagement",
        object_type="User",
        object_id=user_obj.id,
        description=f"Revoked role '{before_role_name}' from user '{user_obj.username}'.",
        before_data={"role": before_role_name},
        after_data={"role": None},
        status="SUCCESS",
    )
 
    return JsonResponse({"ok": True, "total_users": role_obj.users.count()})

@require_permission("userrole_update")
@login_required
@require_http_methods(["POST"])
def role_update_json(request, role_id):

    role_obj = get_object_or_404(UserRole, id=role_id)

    try:
        body = json.loads(request.body)
        new_name = (body.get("role_name") or "").strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)

    if not new_name:
        return JsonResponse({"ok": False, "error": "Role name cannot be empty."}, status=400)

    if len(new_name) > 100:
        return JsonResponse({"ok": False, "error": "Role name must be 100 characters or fewer."}, status=400)

    if UserRole.objects.filter(role_name__iexact=new_name).exclude(id=role_obj.id).exists():
        return JsonResponse({"ok": False, "error": "A role with this name already exists."}, status=400)

    old_name = role_obj.role_name
    role_obj.role_name = new_name
    role_obj.save(update_fields=["role_name"])

    AuditLogger.log(
        request=request,
        action="UPDATE",
        module="RoleManagement",
        object_type="UserRole",
        object_id=role_obj.id,
        description=f"Renamed role '{old_name}' to '{new_name}'.",
        before_data={"role_name": old_name},
        after_data={"role_name": new_name},
        status="SUCCESS",
    )

    return JsonResponse({
        "ok": True,
        "role_id": role_obj.id,
        "role_name": role_obj.role_name,
    })

@require_permission("userrole_update")
@login_required
@require_http_methods(["POST"])
def role_convert_users_json(request, role_id):
 
    source_role = get_object_or_404(UserRole, id=role_id)

    try:
        body = json.loads(request.body)
        target_role_id = body.get("target_role_id")
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)

    if not target_role_id:
        return JsonResponse({"ok": False, "error": "target_role_id is required."}, status=400)

    if str(target_role_id) == str(source_role.id):
        return JsonResponse({"ok": False, "error": "Target role must be different from the current role."}, status=400)

    target_role = get_object_or_404(UserRole, id=target_role_id)

    moved_count = User.objects.filter(role=source_role).update(role=target_role)

    AuditLogger.log(
        request=request,
        action="ROLE_ASSIGN",
        module="RoleManagement",
        object_type="UserRole",
        object_id=target_role.id,
        description=f"Bulk-migrated {moved_count} user(s) from role '{source_role.role_name}' to '{target_role.role_name}'.",
        before_data={"source_role": source_role.role_name, "moved_count": moved_count},
        after_data={"target_role": target_role.role_name},
        status="SUCCESS",
    )

    return JsonResponse({
        "ok": True,
        "moved_count": moved_count,
        "source_role": {"id": source_role.id, "name": source_role.role_name, "count": source_role.users.count()},
        "target_role": {"id": target_role.id, "name": target_role.role_name, "count": target_role.users.count()},
    })



@require_page_access("audit_log_page")
@login_required
def audit_log_page(request):
    return render(request, "audit_log.html")
 
 
@login_required
def audit_log_json(request):
   
    logs = (
        UserAuditLog.objects
        .select_related("user")
        .order_by("-timestamp")[:2000]   
    )
 
    data = []
    for log in logs:
        data.append({
            "id": log.id,
            "user": log.user.username if log.user else "Anonymous",
            "action": log.action,
            "module": log.module,
            "object_type": log.object_type,
            "object_id": log.object_id,
            "description": log.description,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "ip_address": log.ip_address,
            "browser": log.browser,
            "operating_system": log.operating_system,
            "device": log.device,
            "request_method": log.request_method,
            "request_url": log.request_url,
            "status": log.status,
            "before_data": log.before_data,
            "after_data": log.after_data,
            "session_key": log.session_key,
            "request_id": log.request_id,
        })
 
    return JsonResponse({"results": data, "count": len(data)})




from datetime import date
from Admin.models import UserRoleAssignment, UserSession, UserNotificationPreference
from Students.models import (
    StudentProfile, StudentAddress, StudentEmergencyContact, StudentAcademicProfile,
    StudentEnrollment, StudentFinancialAid, StudentFee, StudentFeePayment,
    StudentHousing, StudentResearchProfile, StudentOrganization, StudentCareerProfile,
    StudentDocument,
)
from Faculty.models import (
    FacultyProfile, FacultyRank, FacultyAppointment, FacultyEducation,
    FacultyCourseAssignment, FacultyResearch, FacultyGrant, FacultyPublication,
    FacultyOfficeHours, FacultyCommittee, FacultyEvaluation, FacultyDocument,
)
from Staff.models import (
    StaffProfile, StaffPosition, StaffAddress, StaffEmergencyContact,
    StaffDepartmentAssignment, StaffEducation, StaffCertification, StaffTraining,
    StaffPerformanceReview, StaffLeave, StaffPayroll, StaffAccessRole, StaffDocument,
)

def _calculate_age(dob):
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _get_student_context(user_obj):
    student = (
        StudentProfile.objects
        .select_related("academic_profile", "career_profile")
        .prefetch_related(
            "addresses",
            "emergency_contacts",
            "enrollments__section_id__course",
            "enrollments__section_id__semester_id",
            "financial_aids",
            "fees__payments",
            "housing_records",
            "research_profiles",
            # "organizations",
            "organization_memberships",
            "documents",
        )
        .filter(user=user_obj)
        .first()
    )
    return {"student": student}


def _get_faculty_context(user_obj):
    faculty = (
        FacultyProfile.objects
        .select_related("faculty_rank")
        .prefetch_related(
            "appointments",
            "education_records",
            "course_assignments",
            "research_projects",
            "grants",
            "publications",
            "office_hours",
            "committee_memberships",
            "evaluations", 
            "documents",
        )
        .filter(user=user_obj)
        .first()
    )
    return {"faculty": faculty}



def _get_staff_context(user_obj):

    staff = (
        StaffProfile.objects
        .select_related("supervisor", "supervisor__user")
        .filter(user=user_obj)
        .first()
    )

    if not staff:
        return {}

    return {
        "staff": staff,
        "staff_positions": staff.positions.all(),
        "staff_addresses": staff.addresses.all(),
        "staff_emergency_contacts": staff.emergency_contacts.all(),
        "staff_department_assignments": staff.department_assignments.all(),
        "staff_education": staff.education_records.all(),
        "staff_certifications": staff.certifications.all(),
        "staff_training": staff.training_records.all(),
        "staff_reviews": staff.performance_reviews.all(),
        "staff_leaves": staff.leave_records.all(),
        "staff_payrolls": staff.payroll_records.all(),
        "staff_access_roles": staff.access_roles.all(),
        "staff_documents": staff.documents.all(),
    }

@require_page_access("user_view_page")
@login_required
def user_view(request, uid):
   
    user_obj = get_object_or_404(
        User.objects.select_related("role"),
        uuid=uid
    )

    if user_obj.is_admin:
        user_type = "admin"
    elif user_obj.is_faculty:
        user_type = "faculty"
    elif user_obj.is_staff:
        user_type = "staff"
    elif user_obj.is_student:
        user_type = "student"
    else:
        user_type = ""

    context = {
        "user_obj": user_obj,
        "user_type": user_type,
        "user_initial": (user_obj.first_name or user_obj.username or "U")[:1].upper(),
        "user_age": _calculate_age(user_obj.date_of_birth),
        "student": None,
        "faculty": None,
        "staff": None,
        
    }

    if user_type == "student":
        context.update(_get_student_context(user_obj))
    elif user_type == "faculty":
        context.update(_get_faculty_context(user_obj))
    elif user_type == "staff":
        context.update(_get_staff_context(user_obj))

    # System information — applies to every user type
    context["role_assignments"] = (
        UserRoleAssignment.objects.filter(user=user_obj)
        .select_related("role").order_by("-assigned_at")
    )
    context["recent_sessions"] = (
        UserSession.objects.filter(user=user_obj).order_by("-login_time")[:5]
    )
    context["recent_audit_logs"] = (
        UserAuditLog.objects.filter(user=user_obj).order_by("-timestamp")[:10]
    )
    context["notif_prefs"] = UserNotificationPreference.objects.filter(user=user_obj).first()

    AuditLogger.log(
        request=request,
        action="VIEW",
        module="UserManagement",
        object_type="User",
        object_id=user_obj.id,
        description=f"Viewed profile of user '{user_obj.username}'.",
        status="SUCCESS",
    )

    return render(request, "user_view.html", context)
 
 

def _relative_time(dt):
    """Simple 'time ago' formatter, no extra app dependency needed."""
    if not dt:
        return ""
    delta = timezone.now() - dt
    seconds = delta.total_seconds()
    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        m = int(seconds // 60)
        return f"{m} minute{'s' if m != 1 else ''} ago"
    if seconds < 86400:
        h = int(seconds // 3600)
        return f"{h} hour{'s' if h != 1 else ''} ago"
    if seconds < 604800:
        d = int(seconds // 86400)
        return "Yesterday" if d == 1 else f"{d} days ago"
    weeks = int(seconds // 604800)
    return f"{weeks} week{'s' if weeks != 1 else ''} ago"


def _firearm_recent_activity(firearms, limit=6):
    
    events = []
    for f in firearms:
        is_new = (f.updated_at - f.created_at) < timedelta(seconds=5)
        if is_new:
            icon, tone, title, ts = "plus-circle", "green", "Added new firearm", f.created_at
        else:
            icon, tone, title, ts = "pencil-line", "blue", "Updated firearm details", f.updated_at
        events.append({
            "icon": icon,
            "tone": tone,
            "title": title,
            "detail": f"{f.firearm_name} ({f.serial_number}) — status: {f.get_current_status_display()}.",
            "timestamp": _relative_time(ts),
            "_sort": ts,
        })
    events.sort(key=lambda e: e["_sort"], reverse=True)
    return [{k: v for k, v in e.items() if k != "_sort"} for e in events[:limit]]


@require_page_access("firearm_page")
@login_required
def firearm_page(request):


    firearms = list(Firearm.objects.all().order_by("-created_at"))
    now_year = date.today().year

    status_counts = Counter(f.current_status for f in firearms)
    type_counts = Counter(f.firearm_type for f in firearms)
    manufacturers = {f.manufacturer for f in firearms if f.manufacturer}
    purchased_this_year = sum(
        1 for f in firearms if f.purchase_date and f.purchase_date.year == now_year
    )

    stats = {
        "total": len(firearms),
        "active": status_counts.get("ACTIVE", 0),
        "stored": status_counts.get("STORED", 0),
        "retired": status_counts.get("RETIRED", 0), 
        "disposed": status_counts.get("DISPOSED", 0),
        "purchased_this_year": purchased_this_year,
        "total_manufacturers": len(manufacturers),
    }

    status_chart = {
        "labels": ["Active", "Stored", "Retired", "Disposed"],
        "data": [
            status_counts.get("ACTIVE", 0),
            status_counts.get("STORED", 0),
            status_counts.get("RETIRED", 0),
            status_counts.get("DISPOSED", 0),
        ],
    }
    type_chart = {
        "labels": ["Handgun", "Rifle", "Shotgun", "Training", "Other"],
        "data": [
            type_counts.get("HANDGUN", 0),
            type_counts.get("RIFLE", 0),
            type_counts.get("SHOTGUN", 0),
            type_counts.get("TRAINING", 0),
            type_counts.get("OTHER", 0),
        ],
    }

   

    def _build_permission_user(u):
            latest_firearm = u.firearms.order_by("-created_at").first()
            return {
                "uuid": str(u.uuid),
                "name": u.full_name,
                "initials": (u.first_name[:1].upper() if u.first_name else u.username[:1].upper()),
                "employeeId": u.university_id or u.username,
                "department": u.role.role_name if u.role else "",
                "role": u.role.get_user_type_display() if u.role else "",
                "permission": "Full Access" if u.is_full_crud else "Custody Only",
                "firearmsAssigned": u.firearms.count(),
                "grantedOn": u.created_at.strftime("%Y-%m-%d"),
                # "status": u.account_status.title(),
                "status": latest_firearm.get_current_status_display() if latest_firearm else "",
                "username": u.username,
                "firearmId": latest_firearm.id if latest_firearm else None,
                "firearmType": latest_firearm.get_firearm_type_display() if latest_firearm else "",
            }

    permission_users = [
        _build_permission_user(u)
        for u in User.objects.filter(firearms__isnull=False).distinct()
    ]

    context = {
        "firearms": firearms,
        "stats": stats,
        "status_chart_labels": json.dumps(status_chart["labels"]),
        "status_chart_data": json.dumps(status_chart["data"]),
        "type_chart_labels": json.dumps(type_chart["labels"]),
        "type_chart_data": json.dumps(type_chart["data"]),
        "recent_activity": _firearm_recent_activity(firearms),
        "permission_users_json": json.dumps(permission_users),
    }

    AuditLogger.log(
        request=request,
        action="VIEW",
        module="FirearmManagement",
        object_type="Firearm",
        object_id="",
        description="Viewed the Firearm Management dashboard.",
        status="SUCCESS",
    )

    return render(request, "firearm.html", context) 

@require_permission("firearm_update")
@login_required
@require_http_methods(["POST"])
def firearm_update_json(request, fid):

    firearm = get_object_or_404(Firearm, id=fid)
    errors = {}

    firearm_name = (request.POST.get("firearm_name") or "").strip()
    firearm_type = (request.POST.get("firearm_type") or "").strip()
    manufacturer = (request.POST.get("manufacturer") or "").strip()
    model_name = (request.POST.get("model_name") or "").strip()
    serial_number = (request.POST.get("serial_number") or "").strip()
    caliber = (request.POST.get("caliber") or "").strip()
    purchase_date_raw = (request.POST.get("purchase_date") or "").strip()
    acquisition_method = (request.POST.get("acquisition_method") or "").strip() or "PURCHASE"
    location_name = (request.POST.get("location_name") or "").strip()
    building_name = (request.POST.get("building_name") or "").strip()
    room_number = (request.POST.get("room_number") or "").strip()
    security_level = (request.POST.get("security_level") or "").strip()
    current_status = (request.POST.get("current_status") or "").strip() or "ACTIVE"
    notes = (request.POST.get("notes") or "").strip()
    is_full_crud = (request.POST.get("is_full_crud") or "").strip().lower() in ("on", "true", "1")

    if not firearm_name:
        errors["firearm_name"] = "Firearm name is required."
    elif len(firearm_name) > 150:
        errors["firearm_name"] = "Firearm name must be 150 characters or fewer."

    if not firearm_type:
        errors["firearm_type"] = "Firearm type is required."
    elif firearm_type not in FIREARM_TYPE_VALUES:
        errors["firearm_type"] = "Select a valid firearm type."

    if manufacturer and len(manufacturer) > 150:
        errors["manufacturer"] = "Manufacturer must be 150 characters or fewer."
    if model_name and len(model_name) > 150:
        errors["model_name"] = "Model must be 150 characters or fewer."

    if not serial_number:
        errors["serial_number"] = "Serial number is required."
    elif len(serial_number) > 150:
        errors["serial_number"] = "Serial number must be 150 characters or fewer."
    elif len(serial_number) < 3:
        errors["serial_number"] = "Serial number looks too short."
    elif Firearm.objects.filter(serial_number__iexact=serial_number).exclude(id=firearm.id).exists():
        errors["serial_number"] = "A firearm with this serial number already exists."

    if caliber and len(caliber) > 50:
        errors["caliber"] = "Caliber must be 50 characters or fewer."

    parsed_purchase_date = None
    if purchase_date_raw:
        try:
            parsed_purchase_date = datetime.strptime(purchase_date_raw, "%Y-%m-%d").date()
            if parsed_purchase_date > date.today():
                errors["purchase_date"] = "Purchase date cannot be in the future."
        except ValueError:
            errors["purchase_date"] = "Enter a valid date (YYYY-MM-DD)."

    if acquisition_method not in FIREARM_ACQUISITION_VALUES:
        errors["acquisition_method"] = "Select a valid acquisition method."

    if location_name and len(location_name) > 150:
        errors["location_name"] = "Storage location must be 150 characters or fewer."
    if building_name and len(building_name) > 150:
        errors["building_name"] = "Building name must be 150 characters or fewer."
    if room_number and len(room_number) > 50:
        errors["room_number"] = "Room number must be 50 characters or fewer."
    if security_level and len(security_level) > 100:
        errors["security_level"] = "Security level must be 100 characters or fewer."

    if current_status not in FIREARM_STATUS_VALUES:
        errors["current_status"] = "Select a valid status."

    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)

    before_data = AuditLogger.model_to_dict(
        firearm, ["firearm_name", "firearm_type", "serial_number", "current_status"]
    )

    firearm.firearm_name = firearm_name
    firearm.firearm_type = firearm_type
    firearm.manufacturer = manufacturer or None
    firearm.model_name = model_name or None
    firearm.serial_number = serial_number
    firearm.caliber = caliber or None
    firearm.purchase_date = parsed_purchase_date
    firearm.acquisition_method = acquisition_method
    firearm.location_name = location_name or None
    firearm.building_name = building_name or None
    firearm.room_number = room_number or None
    firearm.security_level = security_level or None
    firearm.current_status = current_status
    firearm.notes = notes or None
    firearm.is_full_crud = is_full_crud
    firearm.save()

    AuditLogger.log(
        request=request,
        action="UPDATE",
        module="FirearmManagement",
        object_type="Firearm",
        object_id=firearm.id,
        description=(
            f"Updated firearm '{firearm.firearm_name}' ({firearm.serial_number}) "
            f"via Edit Firearm form, linked to user '{firearm.user.username}'."
        ),
        before_data=before_data,
        after_data=AuditLogger.model_to_dict(
            firearm, ["firearm_name", "firearm_type", "serial_number", "current_status"]
        ),
        status="SUCCESS",
    )

    return JsonResponse({
        "ok": True,
        "message": f"Firearm '{firearm.firearm_name}' updated successfully.",
        "firearm_id": firearm.id,
    })



FIREARM_TYPE_VALUES = {c[0] for c in Firearm.FIREARM_TYPE_CHOICES}
FIREARM_STATUS_VALUES = {c[0] for c in Firearm.STATUS_CHOICES}
FIREARM_ACQUISITION_VALUES = {c[0] for c in Firearm.ACQUISITION_METHOD_CHOICES}


@login_required
@require_http_methods(["GET"])
def firearm_user_search_json(request):
    """Autocomplete endpoint backing the 'Assigned User' field on the
    Add Firearm form. Returns usernames that contain the given query."""
    query = (request.GET.get("q") or "").strip()
    if not query:
        return JsonResponse({"results": []})

    users = User.objects.filter(username__icontains=query).order_by("username")[:10]
    results = [
        {
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name,
        }
        for u in users
    ]
    return JsonResponse({"results": results})


@login_required
def firearm_view(request, uid):
   

    user_obj = get_object_or_404(
        User.objects.select_related("role"),
        uuid=uid
    )

    if user_obj.is_admin:
        user_type = "admin"
    elif user_obj.is_faculty:
        user_type = "faculty"
    elif user_obj.is_staff:
        user_type = "staff"
    elif user_obj.is_student:
        user_type = "student"
    else:
        user_type = ""

    context = {
        "user_obj": user_obj,
        "user_type": user_type,
        "user_initial": (user_obj.first_name or user_obj.username or "U")[:1].upper(),
        "user_age": _calculate_age(user_obj.date_of_birth),
        "student": None,
        "faculty": None,
        "staff": None,
    }

    if user_type == "student":
        context.update(_get_student_context(user_obj))
    elif user_type == "faculty":
        context.update(_get_faculty_context(user_obj))
    elif user_type == "staff":
        context.update(_get_staff_context(user_obj))

   
    firearms = (
        Firearm.objects.filter(user=user_obj).order_by("-created_at")
    )
    status_counts = Counter(f.current_status for f in firearms)

    context["firearms"] = firearms
    context["firearm_count"] = firearms.count()
    context["firearm_active_count"] = status_counts.get("ACTIVE", 0)
    context["firearm_stored_count"] = status_counts.get("STORED", 0)
    context["firearm_retired_count"] = status_counts.get("RETIRED", 0)
    context["firearm_disposed_count"] = status_counts.get("DISPOSED", 0)

    AuditLogger.log(
        request=request,
        action="VIEW",
        module="FirearmManagement",
        object_type="User",
        object_id=user_obj.id,
        description=f"Viewed firearm custody profile of user '{user_obj.username}'.",
        status="SUCCESS",
    )

    return render(request, "firearm_view.html", context)

@require_permission("firearm_create")
@login_required
@require_http_methods(["POST"])
def firearm_create_json(request):
   
    errors = {}

    username = (request.POST.get("username") or "").strip()
    firearm_name = (request.POST.get("firearm_name") or "").strip()
    firearm_type = (request.POST.get("firearm_type") or "").strip()
    manufacturer = (request.POST.get("manufacturer") or "").strip()
    model_name = (request.POST.get("model_name") or "").strip()
    serial_number = (request.POST.get("serial_number") or "").strip()
    caliber = (request.POST.get("caliber") or "").strip()
    purchase_date_raw = (request.POST.get("purchase_date") or "").strip()
    acquisition_method = (request.POST.get("acquisition_method") or "").strip() or "PURCHASE"
    location_name = (request.POST.get("location_name") or "").strip()
    building_name = (request.POST.get("building_name") or "").strip()
    room_number = (request.POST.get("room_number") or "").strip()
    security_level = (request.POST.get("security_level") or "").strip()
    current_status = (request.POST.get("current_status") or "").strip() or "ACTIVE"
    notes = (request.POST.get("notes") or "").strip()
    is_full_crud = (request.POST.get("is_full_crud") or "").strip().lower() in ("on", "true", "1")

    
    user_obj = None
    if not username:
        errors["username"] = "Please select an existing username."
    else:
        user_obj = User.objects.filter(username=username).first()
        if not user_obj:
            errors["username"] = "Username does not exist."

   
    if not firearm_name:
        errors["firearm_name"] = "Firearm name is required."
    elif len(firearm_name) > 150:
        errors["firearm_name"] = "Firearm name must be 150 characters or fewer."

    
    if not firearm_type:
        errors["firearm_type"] = "Firearm type is required."
    elif firearm_type not in FIREARM_TYPE_VALUES:
        errors["firearm_type"] = "Select a valid firearm type."

   
    if manufacturer and len(manufacturer) > 150:
        errors["manufacturer"] = "Manufacturer must be 150 characters or fewer."
    if model_name and len(model_name) > 150:
        errors["model_name"] = "Model must be 150 characters or fewer."

   
    if not serial_number:
        errors["serial_number"] = "Serial number is required."
    elif len(serial_number) > 150:
        errors["serial_number"] = "Serial number must be 150 characters or fewer."
    elif len(serial_number) < 3:
        errors["serial_number"] = "Serial number looks too short."
    elif Firearm.objects.filter(serial_number__iexact=serial_number).exists():
        errors["serial_number"] = "A firearm with this serial number already exists."

   
    if caliber and len(caliber) > 50:
        errors["caliber"] = "Caliber must be 50 characters or fewer."

   
    parsed_purchase_date = None
    if purchase_date_raw:
        try:
            parsed_purchase_date = datetime.strptime(purchase_date_raw, "%Y-%m-%d").date()
            if parsed_purchase_date > date.today():
                errors["purchase_date"] = "Purchase date cannot be in the future."
        except ValueError:
            errors["purchase_date"] = "Enter a valid date (YYYY-MM-DD)."

  
    if acquisition_method not in FIREARM_ACQUISITION_VALUES:
        errors["acquisition_method"] = "Select a valid acquisition method."

   
    if location_name and len(location_name) > 150:
        errors["location_name"] = "Storage location must be 150 characters or fewer."
    if building_name and len(building_name) > 150:
        errors["building_name"] = "Building name must be 150 characters or fewer."
    if room_number and len(room_number) > 50:
        errors["room_number"] = "Room number must be 50 characters or fewer."
    if security_level and len(security_level) > 100:
        errors["security_level"] = "Security level must be 100 characters or fewer."


    if current_status not in FIREARM_STATUS_VALUES:
        errors["current_status"] = "Select a valid status."

    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)

    firearm = Firearm.objects.create(
        user=user_obj,
        firearm_name=firearm_name,
        firearm_type=firearm_type,
        manufacturer=manufacturer or None,
        model_name=model_name or None,
        serial_number=serial_number,
        caliber=caliber or None,
        purchase_date=parsed_purchase_date,
        acquisition_method=acquisition_method,
        location_name=location_name or None,
        building_name=building_name or None,
        room_number=room_number or None,
        security_level=security_level or None,
        current_status=current_status,
        notes=notes or None,
        is_full_crud=is_full_crud,
    )

    AuditLogger.log(
        request=request,
        action="CREATE",
        module="FirearmManagement",
        object_type="Firearm",
        object_id=firearm.id,
        description=(
            f"Created firearm '{firearm.firearm_name}' ({firearm.serial_number}) "
            f"via Add Firearm form, linked to user '{user_obj.username}'."
        ),
        after_data=AuditLogger.model_to_dict(
            firearm, ["firearm_name", "firearm_type", "serial_number", "current_status"]
        ),
        status="SUCCESS",
    )

    return JsonResponse({
        "ok": True,
        "message": f"Firearm '{firearm.firearm_name}' added successfully.",
        "firearm_id": firearm.id,
    })


def save_firearm_details(request, user):
    """Creates a linked Firearm record for a newly created user when the
    'Does the user have a firearm or gun?' question is answered Yes.
    Mirrors save_student_details / save_faculty_details / save_staff_details."""
    if request.POST.get("has_firearm") != "yes":
        return None

    name = (request.POST.get("firearm_firearm_name") or "").strip()
    ftype = (request.POST.get("firearm_firearm_type") or "").strip()
    serial = (request.POST.get("firearm_serial_number") or "").strip()

    
    if not (name and ftype and serial):
        return None

    firearm = Firearm.objects.create(
        user=user,
        firearm_name=name,
        firearm_type=ftype,
        manufacturer=(request.POST.get("firearm_manufacturer") or "").strip() or None,
        model_name=(request.POST.get("firearm_model_name") or "").strip() or None,
        serial_number=serial,
        caliber=(request.POST.get("firearm_caliber") or "").strip() or None,
        purchase_date=request.POST.get("firearm_purchase_date") or None,
        acquisition_method=request.POST.get("firearm_acquisition_method") or "PURCHASE",
        location_name=(request.POST.get("firearm_location_name") or "").strip() or None,
        building_name=(request.POST.get("firearm_building_name") or "").strip() or None,
        room_number=(request.POST.get("firearm_room_number") or "").strip() or None,
        security_level=(request.POST.get("firearm_security_level") or "").strip() or None,
        current_status=request.POST.get("firearm_current_status") or "ACTIVE",
        notes=(request.POST.get("firearm_notes") or "").strip() or None,
    )

    AuditLogger.log(
        request=request,
        action="CREATE",
        module="FirearmManagement",
        object_type="Firearm",
        object_id=firearm.id,
        description=f"Created firearm '{firearm.firearm_name}' ({firearm.serial_number}) linked to user '{user.username}'.",
        after_data=AuditLogger.model_to_dict(firearm, ["firearm_name", "firearm_type", "serial_number", "current_status"]),
        status="SUCCESS",
    )
    return firearm

@login_required
def olympic_athlete_data_json(request):
    """Returns all OlympicAthlete records as JSON for olympicathlete.js to render."""
    athletes = OlympicAthlete.objects.select_related(
        "athlete__student", "sport", "team", "coach"
    ).order_by("-created_at")

    data = []
    for o in athletes:
        full_name = (
            o.athlete.student.full_name
            if o.athlete_id and o.athlete.student_id
            else "Unknown Athlete"
        )

        if o.profile_photo:
            photo_url = request.build_absolute_uri(o.profile_photo.url)
        else:
            photo_url = (
                f"https://ui-avatars.com/api/?name={full_name.replace(' ', '+')}"
                f"&background=0081C8&color=fff&size=128"
            )

        data.append({
            "id": o.id,
            "uuid": str(o.olympic_uuid),
            "photo": photo_url,
            "name": full_name,
            "athlete_number": o.athlete_number,
            "sport": str(o.sport) if o.sport_id else "—",
            "team": str(o.team) if o.team_id else "—",
            "coach": str(o.coach) if o.coach_id else "—",
            "nationality": o.nationality,
            "olympic_status": o.olympic_status,
            "target_olympics": o.target_olympics,
            "event_name": o.event_name,
            "event_category": o.event_category,
            "governing_body": o.governing_body,
            "world_ranking": o.world_ranking,
            "qualification_date": o.qualification_date.strftime("%Y-%m-%d") if o.qualification_date else None,
            "qualification_score": o.qualification_score or "—",
            "qualification_standard": o.qualification_standard or "—",
            "qualification_status": o.qualification_status,
            "personal_best": o.personal_best or "N/A",
            "biography": o.biography or "",
            "is_active": o.is_active,
        })


    progress_qs = (
        OlympicAthlete.objects
        .values("sport__sport_name")          
        .annotate(
            total=Count("id"),
            progressed=Count(
                "id",
                filter=Q(olympic_status__in=["QUALIFIED", "SELECTED", "PARTICIPATED", "RETIRED"])
            ),
        )
        .order_by("-total")
    )

    qualification_progress = [
        {
            "sport": row["sport__sport_name"] or "—",
            "percentage": round((row["progressed"] / row["total"]) * 100) if row["total"] else 0,
        }
        for row in progress_qs
    ]

   
    recent_logs = (
        UserAuditLog.objects
        .filter(object_type="OlympicAthlete")
        .order_by("-timestamp")[:3]
    )
    recent_updates = [
        {
            "text": log.description,
            "time": f"{timesince(log.timestamp)} ago",
        }
        for log in recent_logs
    ]

    return JsonResponse({
        "results": data,
        "qualification_progress": qualification_progress,
        "recent_updates": recent_updates,
    })

@require_page_access("olympic_page")
@login_required
def olympic_athlete_page(request):
    return render(request, "olympicathlete.html")



OLYMPIC_STATUS_VALUES = {c[0] for c in OlympicAthlete.OLYMPIC_STATUS}
QUALIFICATION_STATUS_VALUES = {c[0] for c in OlympicAthlete.QUALIFICATION_STATUS}
EVENT_CATEGORY_VALUES = {c[0] for c in OlympicAthlete.EVENT_CATEGORY}


def _athletic_display(athletic):
    """Best-effort resolution of an Athletic record's display name and photo.
    Mirrors the fallback pattern already used in olympic_athlete_data_json.
    NOTE: adjust `student.user` below if your StudentProfile's FK to User
    is named differently in Students/models.py."""
    full_name = "Unknown Athlete"
    photo_url = None
    student = getattr(athletic, "student", None)  
    if student:
        full_name = getattr(student, "full_name", full_name) or full_name
        if getattr(student, "profile_photo", None):
            try:
                photo_url = student.profile_photo.url
            except ValueError:
                photo_url = None
    return full_name, photo_url


COUNTRIES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola",
    "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria",
    "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados",
    "Belarus", "Belgium", "Belize", "Benin", "Bhutan",
    "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei",
    "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia",
    "Cameroon", "Canada", "Central African Republic", "Chad", "Chile",
    "China", "Colombia", "Comoros", "Congo (Brazzaville)", "Congo (Kinshasa)",
    "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czechia",
    "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador",
    "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia",
    "Eswatini", "Ethiopia", "Fiji", "Finland", "France",
    "Gabon", "Gambia", "Georgia", "Germany", "Ghana",
    "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau",
    "Guyana", "Haiti", "Honduras", "Hungary", "Iceland",
    "India", "Indonesia", "Iran", "Iraq", "Ireland",
    "Israel", "Italy", "Jamaica", "Japan", "Jordan",
    "Kazakhstan", "Kenya", "Kiribati", "Kosovo", "Kuwait",
    "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho",
    "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg",
    "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali",
    "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico",
    "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro",
    "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru",
    "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger",
    "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman",
    "Pakistan", "Palau", "Palestine", "Panama", "Papua New Guinea",
    "Paraguay", "Peru", "Philippines", "Poland", "Portugal",
    "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis",
    "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe",
    "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone",
    "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia",
    "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka",
    "Sudan", "Suriname", "Sweden", "Switzerland", "Syria",
    "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste",
    "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey",
    "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates",
    "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Vanuatu",
    "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia",
    "Zimbabwe",
]
COUNTRY_SET = set(COUNTRIES)



def _generate_next_olympic_athlete_id():
   
    year = timezone.now().year
    prefix = f"OLY-{year}-"
    count = OlympicAthlete.objects.filter(athlete_number__startswith=prefix).count()
    return f"{prefix}{count + 1:03d}"

@require_page_access("olympic_athlete_add_page")
@require_permission("olympicathlete_create")
@login_required
def olympic_athlete_add_page(request):
    """Renders the Add Olympic Athlete registration form."""
    linked_ids = OlympicAthlete.objects.values_list("athlete_id", flat=True)
    available_athletes = (
        Athletic.objects.exclude(athlete_id__in=linked_ids)
        .select_related("student")
    )

    athlete_options = []
    for a in available_athletes:
        name, photo = _athletic_display(a)
        athlete_options.append({
            "id": a.athlete_id,
            "name": name,
            "photo": photo or (
                f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}"
                f"&background=0081C8&color=fff&size=128"
            ),
        })

    context = {
        "sports": Sport.objects.all().order_by("sport_name"),
        "teams": SportTeamModel.objects.all(),
        "coaches": Coach.objects.all(),
        "athlete_options": athlete_options,
        "countries": COUNTRIES,
        "next_athlete_number": _generate_next_olympic_athlete_id(),
        "olympic_status_choices": OlympicAthlete.OLYMPIC_STATUS,
        "qualification_status_choices": OlympicAthlete.QUALIFICATION_STATUS,
        "event_category_choices": OlympicAthlete.EVENT_CATEGORY,
        "is_edit": False,
        "selected_olympic_status": "PENDING",
        "selected_qualification_status": "PENDING",
    }
    return render(request, "olympic_athlete_add.html", context)


# @require_page_access("olympic_athlete_edit_page")
@require_permission("olympicathlete_update")
@login_required
def olympic_athlete_edit_page(request, uuid):
    """Renders the Add/Edit form pre-filled with an existing Olympic athlete's data."""
    oa = get_object_or_404(
        OlympicAthlete.objects.select_related("athlete__student", "sport", "team", "coach"),
        olympic_uuid=uuid,
    )

    # Exclude athletes already linked to a DIFFERENT Olympic profile,
    # but keep this record's own athlete selectable.
    linked_ids = (
        OlympicAthlete.objects.exclude(pk=oa.pk).values_list("athlete_id", flat=True)
    )
    available_athletes = (
        Athletic.objects.exclude(athlete_id__in=linked_ids)
        .select_related("student")
    )

    athlete_options = []
    for a in available_athletes:
        name, photo = _athletic_display(a)
        athlete_options.append({
            "id": a.athlete_id,
            "name": name,
            "photo": photo or (
                f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}"
                f"&background=0081C8&color=fff&size=128"
            ),
        })

    current_name, current_photo = (
        _athletic_display(oa.athlete) if oa.athlete_id else ("Unknown Athlete", None)
    )
    if oa.profile_photo:
        current_photo = request.build_absolute_uri(oa.profile_photo.url)
    elif not current_photo:
        current_photo = (
            f"https://ui-avatars.com/api/?name={current_name.replace(' ', '+')}"
            f"&background=0081C8&color=fff&size=128"
        )

    context = {
        "is_edit": True,
        "athlete_obj": oa,
        "sports": Sport.objects.all().order_by("sport_name"),
        "teams": SportTeamModel.objects.all(),
        "coaches": Coach.objects.all(),
        "athlete_options": athlete_options,
        "countries": COUNTRIES,
        "next_athlete_number": oa.athlete_number,
        "olympic_status_choices": OlympicAthlete.OLYMPIC_STATUS,
        "qualification_status_choices": OlympicAthlete.QUALIFICATION_STATUS,
        "event_category_choices": OlympicAthlete.EVENT_CATEGORY,
        "selected_olympic_status": oa.olympic_status,
        "selected_qualification_status": oa.qualification_status,
        "current_athlete_name": current_name,
        "current_athlete_photo": current_photo,
    }
    return render(request, "olympic_athlete_add.html", context)

@require_permission("olympicathlete_update")
@login_required
@require_http_methods(["POST"])
def olympic_athlete_update_json(request, uuid):
    """Updates an existing OlympicAthlete record."""
    oa = get_object_or_404(OlympicAthlete,  olympic_uuid=uuid)
    errors = {}

    athlete_id = (request.POST.get("athlete") or "").strip()
    sport_id = (request.POST.get("sport") or "").strip()
    team_id = (request.POST.get("team") or "").strip()
    coach_id = (request.POST.get("coach") or "").strip()
    nationality = (request.POST.get("nationality") or "").strip()
    olympic_status = (request.POST.get("olympic_status") or "").strip() or "PENDING"
    target_olympics = (request.POST.get("target_olympics") or "").strip()
    event_name = (request.POST.get("event_name") or "").strip()
    event_category = (request.POST.get("event_category") or "").strip() or "INDIVIDUAL"
    governing_body = (request.POST.get("governing_body") or "").strip()
    world_ranking_raw = (request.POST.get("world_ranking") or "").strip()
    qualification_date_raw = (request.POST.get("qualification_date") or "").strip()
    qualification_score = (request.POST.get("qualification_score") or "").strip()
    qualification_standard = (request.POST.get("qualification_standard") or "").strip()
    qualification_status = (request.POST.get("qualification_status") or "").strip() or "PENDING"
    personal_best = (request.POST.get("personal_best") or "").strip()
    biography = (request.POST.get("biography") or "").strip()

    athletic_obj = None
    if not athlete_id:
        errors["athlete"] = "Please select an athlete."
    else:
        athletic_obj = Athletic.objects.filter(athlete_id=athlete_id).first()
        if not athletic_obj:
            errors["athlete"] = "Selected athlete does not exist."
        elif OlympicAthlete.objects.filter(athlete_id=athlete_id).exclude(pk=oa.pk).exists():
            errors["athlete"] = "This athlete already has an Olympic profile."

    sport_obj = None
    if not sport_id:
        errors["sport"] = "Sport is required."
    else:
        sport_obj = Sport.objects.filter(id=sport_id).first()
        if not sport_obj:
            errors["sport"] = "Select a valid sport."

    team_obj = SportTeamModel.objects.filter(team_id=team_id).first() if team_id else None
    coach_obj = Coach.objects.filter(coach_id=coach_id).first() if coach_id else None

    if not nationality:
        errors["nationality"] = "Nationality is required."
    elif nationality not in COUNTRY_SET:
        errors["nationality"] = "Select a valid nationality."

    if olympic_status not in OLYMPIC_STATUS_VALUES:
        errors["olympic_status"] = "Select a valid Olympic status."

    if not target_olympics:
        errors["target_olympics"] = "Target Olympics is required."
    elif len(target_olympics) > 100:
        errors["target_olympics"] = "Target Olympics must be 100 characters or fewer."

    if not event_name:
        errors["event_name"] = "Event name is required."
    elif len(event_name) > 150:
        errors["event_name"] = "Event name must be 150 characters or fewer."

    if event_category not in EVENT_CATEGORY_VALUES:
        errors["event_category"] = "Select a valid event category."

    if not governing_body:
        errors["governing_body"] = "Governing body is required."
    elif len(governing_body) > 150:
        errors["governing_body"] = "Governing body must be 150 characters or fewer."

    world_ranking = None
    if world_ranking_raw:
        try:
            world_ranking = int(world_ranking_raw)
            if world_ranking <= 0:
                errors["world_ranking"] = "World ranking must be a positive number."
        except ValueError:
            errors["world_ranking"] = "World ranking must be a whole number."

    parsed_qualification_date = None
    if qualification_date_raw:
        try:
            parsed_qualification_date = datetime.strptime(qualification_date_raw, "%Y-%m-%d").date()
            if parsed_qualification_date > date.today():
                errors["qualification_date"] = "Qualification date cannot be in the future."
        except ValueError:
            errors["qualification_date"] = "Enter a valid date (YYYY-MM-DD)."

    if qualification_status not in QUALIFICATION_STATUS_VALUES:
        errors["qualification_status"] = "Select a valid qualification status."

    if qualification_score and len(qualification_score) > 100:
        errors["qualification_score"] = "Score / time must be 100 characters or fewer."
    if qualification_standard and len(qualification_standard) > 100:
        errors["qualification_standard"] = "Standard must be 100 characters or fewer."
    if personal_best and len(personal_best) > 100:
        errors["personal_best"] = "Personal best must be 100 characters or fewer."

    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)

    before_data = AuditLogger.model_to_dict(
        oa, ["athlete_number", "target_olympics", "olympic_status", "event_name"]
    )

    with transaction.atomic():
        oa.athlete = athletic_obj
        oa.sport = sport_obj
        oa.team = team_obj
        oa.coach = coach_obj
        oa.nationality = nationality
        oa.olympic_status = olympic_status
        oa.target_olympics = target_olympics
        oa.event_name = event_name
        oa.event_category = event_category
        oa.governing_body = governing_body
        oa.world_ranking = world_ranking
        oa.qualification_date = parsed_qualification_date
        oa.qualification_score = qualification_score or None
        oa.qualification_standard = qualification_standard or None
        oa.qualification_status = qualification_status
        oa.personal_best = personal_best or None
        oa.biography = biography or None
        oa.save()

    AuditLogger.log(
        request=request,
        action="UPDATE",
        module="OlympicAthleteManagement",
        object_type="OlympicAthlete",
        object_id=oa.id,
        description=f"Updated Olympic athlete targeting {target_olympics}.",
        before_data=before_data,
        after_data=AuditLogger.model_to_dict(
            oa, ["athlete_number", "target_olympics", "olympic_status", "event_name"]
        ),
        status="SUCCESS",
    )

    return JsonResponse({
        "ok": True,
        "message": "Olympic Athlete updated successfully.",
        "athlete_id": oa.id,
        "redirect_url": str(reverse("olympic_athlete_page")),
    })


@login_required
@require_http_methods(["POST"])
def olympic_athlete_create_json(request):
   
    errors = {}

    athlete_id = (request.POST.get("athlete") or "").strip()
    sport_id = (request.POST.get("sport") or "").strip()
    team_id = (request.POST.get("team") or "").strip()
    coach_id = (request.POST.get("coach") or "").strip()
    nationality = (request.POST.get("nationality") or "").strip()
    olympic_status = (request.POST.get("olympic_status") or "").strip() or "PENDING"
    target_olympics = (request.POST.get("target_olympics") or "").strip()
    event_name = (request.POST.get("event_name") or "").strip()
    event_category = (request.POST.get("event_category") or "").strip() or "INDIVIDUAL"
    governing_body = (request.POST.get("governing_body") or "").strip()
    world_ranking_raw = (request.POST.get("world_ranking") or "").strip()
    qualification_date_raw = (request.POST.get("qualification_date") or "").strip()
    qualification_score = (request.POST.get("qualification_score") or "").strip()
    qualification_standard = (request.POST.get("qualification_standard") or "").strip()
    qualification_status = (request.POST.get("qualification_status") or "").strip() or "PENDING"
    personal_best = (request.POST.get("personal_best") or "").strip()
    biography = (request.POST.get("biography") or "").strip()

    athletic_obj = None
    if not athlete_id:
        errors["athlete"] = "Please select an athlete."
    else:
        athletic_obj = Athletic.objects.filter(athlete_id=athlete_id).first()
        if not athletic_obj:
            errors["athlete"] = "Selected athlete does not exist."
        elif OlympicAthlete.objects.filter(athlete_id=athlete_id).exists():
            errors["athlete"] = "This athlete already has an Olympic profile."

    sport_obj = None
    if not sport_id:
        errors["sport"] = "Sport is required."
    else:
        sport_obj = Sport.objects.filter(id=sport_id).first()
        if not sport_obj:
            errors["sport"] = "Select a valid sport."

    team_obj = SportTeamModel.objects.filter(team_id=team_id).first() if team_id else None
    coach_obj = Coach.objects.filter(coach_id=coach_id).first() if coach_id else None

    if not nationality:
        errors["nationality"] = "Nationality is required."
    elif nationality not in COUNTRY_SET:
        errors["nationality"] = "Select a valid nationality."

    if olympic_status not in OLYMPIC_STATUS_VALUES:
        errors["olympic_status"] = "Select a valid Olympic status."

    if not target_olympics:
        errors["target_olympics"] = "Target Olympics is required."
    elif len(target_olympics) > 100:
        errors["target_olympics"] = "Target Olympics must be 100 characters or fewer."

    if not event_name:
        errors["event_name"] = "Event name is required."
    elif len(event_name) > 150:
        errors["event_name"] = "Event name must be 150 characters or fewer."

    if event_category not in EVENT_CATEGORY_VALUES:
        errors["event_category"] = "Select a valid event category."

    if not governing_body:
        errors["governing_body"] = "Governing body is required."
    elif len(governing_body) > 150:
        errors["governing_body"] = "Governing body must be 150 characters or fewer."

    world_ranking = None
    if world_ranking_raw:
        try:
            world_ranking = int(world_ranking_raw)
            if world_ranking <= 0:
                errors["world_ranking"] = "World ranking must be a positive number."
        except ValueError:
            errors["world_ranking"] = "World ranking must be a whole number."

    parsed_qualification_date = None
    if qualification_date_raw:
        try:
            parsed_qualification_date = datetime.strptime(qualification_date_raw, "%Y-%m-%d").date()
            if parsed_qualification_date > date.today():
                errors["qualification_date"] = "Qualification date cannot be in the future."
        except ValueError:
            errors["qualification_date"] = "Enter a valid date (YYYY-MM-DD)."

    if qualification_status not in QUALIFICATION_STATUS_VALUES:
        errors["qualification_status"] = "Select a valid qualification status."

    if qualification_score and len(qualification_score) > 100:
        errors["qualification_score"] = "Score / time must be 100 characters or fewer."
    if qualification_standard and len(qualification_standard) > 100:
        errors["qualification_standard"] = "Standard must be 100 characters or fewer."
    if personal_best and len(personal_best) > 100:
        errors["personal_best"] = "Personal best must be 100 characters or fewer."

    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)

    olympic_athlete = None
    for _attempt in range(5):
        try:
            with transaction.atomic():
                olympic_athlete = OlympicAthlete.objects.create(
                    athlete=athletic_obj,
                    sport=sport_obj,
                    team=team_obj,
                    coach=coach_obj,
                    athlete_number=_generate_next_olympic_athlete_id(),
                    nationality=nationality,
                    olympic_status=olympic_status,
                    target_olympics=target_olympics,
                    event_name=event_name,
                    event_category=event_category,
                    governing_body=governing_body,
                    world_ranking=world_ranking,
                    qualification_date=parsed_qualification_date,
                    qualification_score=qualification_score or None,
                    qualification_standard=qualification_standard or None,
                    qualification_status=qualification_status,
                    personal_best=personal_best or None,
                    biography=biography or None,
                )
            break
        except IntegrityError:
            continue

    if olympic_athlete is None:
        return JsonResponse(
            {"ok": False, "errors": {"athlete_number": "Could not generate a unique Olympic Athlete ID, please retry."}},
            status=409,
        )

    AuditLogger.log(
        request=request,
        action="CREATE",
        module="OlympicAthleteManagement",
        object_type="OlympicAthlete",
        object_id=olympic_athlete.id,
        description=f"Added Olympic athlete targeting {target_olympics}.",
        after_data=AuditLogger.model_to_dict(
            olympic_athlete, ["athlete_number", "target_olympics", "olympic_status", "event_name"]
        ),
        status="SUCCESS",
    )

    return JsonResponse({
        "ok": True,
        "message": "Olympic Athlete added successfully.",
        "athlete_id": olympic_athlete.id,
        "redirect_url": str(reverse("olympic_athlete_page")),
    })




@login_required
def olympic_performance_data_json(request):
   

    show_archived = request.GET.get("archived") == "1"
    
    # performances = OlympicPerformance.objects.select_related(
    #     "olympic_athlete__athlete__student"
    # ).order_by("-competition_date")

    performances = OlympicPerformance.objects.select_related(
        "olympic_athlete__athlete__student"
    ).filter(is_archived=show_archived).order_by("-competition_date")

    data = []
    for p in performances:
        oa = p.olympic_athlete
        full_name = (
            oa.athlete.student.full_name
            if oa and oa.athlete_id and oa.athlete.student_id
            else "Unknown Athlete"
        )
        data.append({
            "id": p.id,
            "uuid": str(p.performance_uuid),
            "athlete": full_name,
            "athlete_no": oa.athlete_number if oa else "—",
            "competition_name": p.competition_name,
            "competition_level": p.competition_level,
            "event_name": p.event_name,
            "competition_date": p.competition_date.strftime("%Y-%m-%d") if p.competition_date else None,
            "host_city": p.host_city,
            "host_country": p.host_country,
            "score_time": p.score_time or "—",
            "ranking": p.ranking,
            "medal": p.medal,
            "participation_status": p.participation_status,
            "remarks": p.remarks or "",
            "created_at": p.created_at.strftime("%Y-%m-%d") if p.created_at else None,
            "updated_at": p.updated_at.strftime("%Y-%m-%d") if p.updated_at else None,
        })

    return JsonResponse({"results": data})

@login_required
@require_http_methods(["POST"])
def olympic_performance_archive_json(request, uuid):
   
    performance = get_object_or_404(OlympicPerformance, performance_uuid=uuid)

    if performance.is_archived:
        return JsonResponse({"ok": False, "message": "Record is already archived."}, status=400)

    performance.is_archived = True
    performance.archived_at = timezone.now()
    performance.save(update_fields=["is_archived", "archived_at", "updated_at"])

    AuditLogger.log(
        request=request,
        action="ARCHIVE",
        module="OlympicPerformanceManagement",
        object_type="OlympicPerformance",
        object_id=performance.id,
        description=f"Archived performance '{performance.competition_name}'.",
        status="SUCCESS",
    )

    return JsonResponse({"ok": True, "message": "Record archived successfully."})


@login_required
@require_http_methods(["POST"])
def olympic_performance_restore_json(request, uuid):
    
    performance = get_object_or_404(OlympicPerformance, performance_uuid=uuid)

    if not performance.is_archived:
        return JsonResponse({"ok": False, "message": "Record is not archived."}, status=400)

    performance.is_archived = False
    performance.archived_at = None
    performance.save(update_fields=["is_archived", "archived_at", "updated_at"])

    AuditLogger.log(
        request=request,
        action="RESTORE",
        module="OlympicPerformanceManagement",
        object_type="OlympicPerformance",
        object_id=performance.id,
        description=f"Restored performance '{performance.competition_name}'.",
        status="SUCCESS",
    )

    return JsonResponse({"ok": True, "message": "Record restored successfully."})

@require_page_access("olympic_performance_page")
@login_required
def olympic_performance_page(request):
    return render(request, "olympic_performance.html")


PERF_LEVEL_VALUES = {c[0] for c in OlympicPerformance.COMPETITION_LEVEL}
PERF_MEDAL_VALUES = {c[0] for c in OlympicPerformance.MEDAL_CHOICES}
PERF_STATUS_VALUES = {c[0] for c in OlympicPerformance.PARTICIPATION_STATUS}



def _build_olympic_performance_form_context(request, performance=None):
    
    athletes = OlympicAthlete.objects.select_related("athlete__student").order_by("athlete_number")

    selected_uuid = (
        str(performance.olympic_athlete.olympic_uuid)
        if performance and performance.olympic_athlete_id else ""
    )

    athlete_options = []
    for oa in athletes:
        full_name = (
            oa.athlete.student.full_name
            if oa.athlete_id and oa.athlete.student_id
            else "Unknown Athlete"
        )

        user_photo = None
        student = getattr(oa.athlete, "student", None) if oa.athlete_id else None
        user_obj = getattr(student, "user", None)
        if user_obj and getattr(user_obj, "profile_photo", None):
            try:
                user_photo = request.build_absolute_uri(user_obj.profile_photo.url)
            except ValueError:
                user_photo = None
        photo_url = user_photo or (
            f"https://ui-avatars.com/api/?name={full_name.replace(' ', '+')}"
            f"&background=0081C8&color=fff&size=128"
        )

        athlete_options.append({
            "uuid": str(oa.olympic_uuid),
            "name": full_name,
            "athlete_number": oa.athlete_number,
            "photo": photo_url,
            "selected": str(oa.olympic_uuid) == selected_uuid,
        })

    return {
        "athlete_options": athlete_options,
        "competition_level_choices": OlympicPerformance.COMPETITION_LEVEL,
        "medal_choices": OlympicPerformance.MEDAL_CHOICES,
        "participation_status_choices": OlympicPerformance.PARTICIPATION_STATUS,
        "countries": COUNTRIES,
        "is_edit": performance is not None,
        "performance_obj": performance,
    }

@require_page_access("oympic_performane_add_page")
@require_permission("olympicperformance_create")
@login_required
def olympic_performance_add_page(request):
   
    context = _build_olympic_performance_form_context(request)
    return render(request, "add_performance.html", context)

@require_page_access("olympic_performance_edit_page")
@require_permission("olympicperformance_update")
@login_required
def olympic_performance_edit_page(request, uuid):
    
    performance = get_object_or_404(
        OlympicPerformance.objects.select_related("olympic_athlete"),
        performance_uuid=uuid,
    )
    context = _build_olympic_performance_form_context(request, performance=performance)
    return render(request, "add_performance.html", context)


@login_required
def olympic_performance_detail_json(request, uuid):
    
    p = get_object_or_404(
        OlympicPerformance.objects.select_related("olympic_athlete__athlete__student"),
        performance_uuid=uuid,
    )
    oa = p.olympic_athlete
    full_name = (
        oa.athlete.student.full_name
        if oa and oa.athlete_id and oa.athlete.student_id
        else "Unknown Athlete"
    )

    user_photo = None
    student = getattr(oa.athlete, "student", None) if oa and oa.athlete_id else None
    user_obj = getattr(student, "user", None)
    if user_obj and getattr(user_obj, "profile_photo", None):
        try:
            user_photo = request.build_absolute_uri(user_obj.profile_photo.url)
        except ValueError:
            user_photo = None
    photo_url = user_photo or (
        f"https://ui-avatars.com/api/?name={full_name.replace(' ', '+')}"
        f"&background=0081C8&color=fff&size=128"
    )

    data = {
        "uuid": str(p.performance_uuid),
        "athlete": full_name,
        "athlete_no": oa.athlete_number if oa else "—",
        "athlete_photo": photo_url,
        "competition_name": p.competition_name,
        "competition_level": p.competition_level,
        "event_name": p.event_name,
        "competition_date": p.competition_date.strftime("%Y-%m-%d") if p.competition_date else None,
        "host_city": p.host_city,
        "host_country": p.host_country,
        "score_time": p.score_time or "—",
        "ranking": p.ranking,
        "medal": p.medal,
        "participation_status": p.participation_status,
        "remarks": p.remarks or "",
        "created_at": p.created_at.strftime("%b %d, %Y") if p.created_at else None,
        "updated_at": p.updated_at.strftime("%b %d, %Y") if p.updated_at else None,
    }
    return JsonResponse({"ok": True, "result": data})


@require_permission("olympicperformance_update")
@login_required
@require_http_methods(["POST"])
def olympic_performance_update_json(request, uuid):
   
    performance = get_object_or_404(OlympicPerformance, performance_uuid=uuid)
    errors = {}

    olympic_athlete_uuid = (request.POST.get("olympic_athlete") or "").strip()
    competition_name = (request.POST.get("competition_name") or "").strip()
    competition_level = (request.POST.get("competition_level") or "").strip()
    event_name = (request.POST.get("event_name") or "").strip()
    competition_date_raw = (request.POST.get("competition_date") or "").strip()
    host_city = (request.POST.get("host_city") or "").strip()
    host_country = (request.POST.get("host_country") or "").strip()
    score_time = (request.POST.get("score_time") or "").strip()
    ranking_raw = (request.POST.get("ranking") or "").strip()
    medal = (request.POST.get("medal") or "").strip() or "NONE"
    participation_status = (request.POST.get("participation_status") or "").strip() or "SCHEDULED"
    remarks = (request.POST.get("remarks") or "").strip()

    olympic_athlete_obj = None
    if not olympic_athlete_uuid:
        errors["olympic_athlete"] = "Please select an Olympic athlete."
    else:
        olympic_athlete_obj = OlympicAthlete.objects.filter(olympic_uuid=olympic_athlete_uuid).first()
        if not olympic_athlete_obj:
            errors["olympic_athlete"] = "Selected athlete does not exist."

    if not competition_name:
        errors["competition_name"] = "Competition name is required."
    elif len(competition_name) > 150:
        errors["competition_name"] = "Competition name must be 150 characters or fewer."

    if competition_level not in PERF_LEVEL_VALUES:
        errors["competition_level"] = "Select a valid competition level."

    if not event_name:
        errors["event_name"] = "Event name is required."
    elif len(event_name) > 150:
        errors["event_name"] = "Event name must be 150 characters or fewer."

    parsed_competition_date = None
    if not competition_date_raw:
        errors["competition_date"] = "Competition date is required."
    else:
        try:
            parsed_competition_date = datetime.strptime(competition_date_raw, "%Y-%m-%d").date()
        except ValueError:
            errors["competition_date"] = "Enter a valid date (YYYY-MM-DD)."

    if not host_city:
        errors["host_city"] = "Host city is required."
    elif len(host_city) > 100:
        errors["host_city"] = "Host city must be 100 characters or fewer."

    if not host_country:
        errors["host_country"] = "Host country is required."
    elif len(host_country) > 100:
        errors["host_country"] = "Host country must be 100 characters or fewer."

    if score_time and len(score_time) > 100:
        errors["score_time"] = "Score / time must be 100 characters or fewer."

    ranking = None
    if ranking_raw:
        try:
            ranking = int(ranking_raw)
            if ranking <= 0:
                errors["ranking"] = "Ranking must be a positive number."
        except ValueError:
            errors["ranking"] = "Ranking must be a whole number."

    if medal not in PERF_MEDAL_VALUES:
        errors["medal"] = "Select a valid medal."

    if participation_status not in PERF_STATUS_VALUES:
        errors["participation_status"] = "Select a valid participation status."

    if remarks and len(remarks) > 5000:
        errors["remarks"] = "Remarks are too long."

    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)

    before_data = AuditLogger.model_to_dict(
        performance, ["competition_name", "competition_level", "event_name", "medal", "participation_status"]
    )

    with transaction.atomic():
        performance.olympic_athlete = olympic_athlete_obj
        performance.competition_name = competition_name
        performance.competition_level = competition_level
        performance.event_name = event_name
        performance.competition_date = parsed_competition_date
        performance.host_city = host_city
        performance.host_country = host_country
        performance.score_time = score_time or None
        performance.ranking = ranking
        performance.medal = medal
        performance.participation_status = participation_status
        performance.remarks = remarks or None
        performance.save()

    AuditLogger.log(
        request=request,
        action="UPDATE",
        module="OlympicPerformanceManagement",
        object_type="OlympicPerformance",
        object_id=performance.id,
        description=f"Updated performance '{performance.competition_name}' for {olympic_athlete_obj}.",
        before_data=before_data,
        after_data=AuditLogger.model_to_dict(
            performance, ["competition_name", "competition_level", "event_name", "medal", "participation_status"]
        ),
        status="SUCCESS",
    )

    return JsonResponse({
        "ok": True,
        "message": "Olympic Performance updated successfully.",
        "performance_id": performance.id,
        "redirect_url": str(reverse("olympic_performance_page")),
    })


    

@login_required
@require_http_methods(["POST"])
def olympic_performance_create_json(request):
   
    errors = {}

    olympic_athlete_uuid = (request.POST.get("olympic_athlete") or "").strip()
    competition_name = (request.POST.get("competition_name") or "").strip()
    competition_level = (request.POST.get("competition_level") or "").strip()
    event_name = (request.POST.get("event_name") or "").strip()
    competition_date_raw = (request.POST.get("competition_date") or "").strip()
    host_city = (request.POST.get("host_city") or "").strip()
    host_country = (request.POST.get("host_country") or "").strip()
    score_time = (request.POST.get("score_time") or "").strip()
    ranking_raw = (request.POST.get("ranking") or "").strip()
    medal = (request.POST.get("medal") or "").strip() or "NONE"
    participation_status = (request.POST.get("participation_status") or "").strip() or "SCHEDULED"
    remarks = (request.POST.get("remarks") or "").strip()

    olympic_athlete_obj = None
    if not olympic_athlete_uuid:
        errors["olympic_athlete"] = "Please select an Olympic athlete."
    else:
        olympic_athlete_obj = OlympicAthlete.objects.filter(olympic_uuid=olympic_athlete_uuid).first()
        if not olympic_athlete_obj:
            errors["olympic_athlete"] = "Selected athlete does not exist."

    if not competition_name:
        errors["competition_name"] = "Competition name is required."
    elif len(competition_name) > 150:
        errors["competition_name"] = "Competition name must be 150 characters or fewer."

    if competition_level not in PERF_LEVEL_VALUES:
        errors["competition_level"] = "Select a valid competition level."

    if not event_name:
        errors["event_name"] = "Event name is required."
    elif len(event_name) > 150:
        errors["event_name"] = "Event name must be 150 characters or fewer."

    parsed_competition_date = None
    if not competition_date_raw:
        errors["competition_date"] = "Competition date is required."
    else:
        try:
            parsed_competition_date = datetime.strptime(competition_date_raw, "%Y-%m-%d").date()
        except ValueError:
            errors["competition_date"] = "Enter a valid date (YYYY-MM-DD)."

    if not host_city:
        errors["host_city"] = "Host city is required."
    elif len(host_city) > 100:
        errors["host_city"] = "Host city must be 100 characters or fewer."

    if not host_country:
        errors["host_country"] = "Host country is required."
    elif len(host_country) > 100:
        errors["host_country"] = "Host country must be 100 characters or fewer."

    

    if score_time and len(score_time) > 100:
        errors["score_time"] = "Score / time must be 100 characters or fewer."

  
    ranking = None
    if ranking_raw:
        try:
            ranking = int(ranking_raw)
            if ranking <= 0:
                errors["ranking"] = "Ranking must be a positive number."
        except ValueError:
            errors["ranking"] = "Ranking must be a whole number."

    if medal not in PERF_MEDAL_VALUES:
        errors["medal"] = "Select a valid medal."

    if participation_status not in PERF_STATUS_VALUES:
        errors["participation_status"] = "Select a valid participation status."

    if remarks and len(remarks) > 5000:
        errors["remarks"] = "Remarks are too long."

    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)

    performance = OlympicPerformance.objects.create(
        olympic_athlete=olympic_athlete_obj,
        competition_name=competition_name,
        competition_level=competition_level,
        event_name=event_name,
        competition_date=parsed_competition_date,
        host_city=host_city,
        host_country=host_country,
        # score_time=score_time,
        score_time=score_time or None,
        ranking=ranking,
        medal=medal,
        participation_status=participation_status,
        remarks=remarks or None,
    )

    AuditLogger.log(
        request=request,
        action="CREATE",
        module="OlympicPerformanceManagement",
        object_type="OlympicPerformance",
        object_id=performance.id,
        description=f"Added performance '{performance.competition_name}' for {olympic_athlete_obj}.",
        after_data=AuditLogger.model_to_dict(
            performance, ["competition_name", "competition_level", "event_name", "medal", "participation_status"]
        ),
        status="SUCCESS",
    )

    return JsonResponse({
        "ok": True,
        "message": "Olympic Performance added successfully.",
        "performance_id": performance.id,
        "redirect_url": str(reverse("olympic_performance_page")),
    })



@require_page_access("tournament_page")
@login_required
def tournament_dashboard_page(request):
    tournaments_qs = (
        Tournament.objects.select_related("sport", "venue")
        .order_by("-created_at")
    )
    invitations_qs = (
        TournamentInvitation.objects.select_related("tournament")
        .order_by("-invitation_sent_at")
    )
    participants_qs = (
        TournamentParticipant.objects.select_related(
            "tournament", "internal_team", "internal_athlete", "invitation__application"
        ).order_by("-registered_at")
    )

    UPCOMING_STATUSES = ["CREATED", "INVITATION_SENT", "REGISTRATION_OPEN", "REGISTRATION_CLOSED"]
    ACTIVE_STATUSES = ["VERIFICATION", "APPROVED", "FIXTURES_READY", "ONGOING"]

    total_tournaments_count = tournaments_qs.count()
    active_tournaments_count = tournaments_qs.filter(status__in=ACTIVE_STATUSES).count()
    upcoming_tournaments_count = tournaments_qs.filter(status__in=UPCOMING_STATUSES).count()
    completed_tournaments_count = tournaments_qs.filter(status="COMPLETED").count()
    invitations_sent_count = invitations_qs.count()
    approved_participants_count = invitations_qs.filter(application_status="APPROVED").count()
    pending_applications_count = invitations_qs.filter(application_status="APPLIED").count()
    total_registered_participants_count = (
        participants_qs.aggregate(total=Sum("players_count"))["total"] or 0
    )

   
    tournaments_data = []
    for t in tournaments_qs:
        tournaments_data.append({
            "tournament_name": t.tournament_name,
            "tournament_code": t.tournament_code,
            "sport": t.sport.sport_name if t.sport else "—",
            "tournament_type": t.tournament_type,
            "participation_type": t.participation_type,
            
            "venue": getattr(t.venue, "facility_name", str(t.venue)) if t.venue else "—",
            "start_date": t.start_date.isoformat() if t.start_date else None,
            "end_date": t.end_date.isoformat() if t.end_date else None,
            "registration_deadline": (
                t.registration_deadline.isoformat()
                if t.registration_deadline else None
            ),
            "status": t.status,
            "registered_participants": t.participants.count(),
            "maximum_participants": t.maximum_participants,
            "tournament_uuid": str(t.tournament_uuid),
            "tournament_name": t.tournament_name,
        })

    invitations_data = []
    for inv in invitations_qs:
        invitations_data.append({
            "invitation_uuid": str(inv.invitation_uuid),
            "tournament": inv.tournament.tournament_name if inv.tournament else "—",
            "college_name": inv.college_name or "—",
            "department_name": inv.department_name or "—",
            "contact_person": inv.contact_person or "—",
            "email": inv.email,
            "application_status": inv.application_status,
            "invitation_sent_at": (
                inv.invitation_sent_at.date().isoformat() if inv.invitation_sent_at else None
            ),
        })

    participants_data = []
    for p in participants_qs:
        # NOTE: adjust `internal_team.team_name` below if SportTeamModel uses a different display field.
        team_name = getattr(p.internal_team, "team_name", str(p.internal_team)) if p.internal_team else "—"
        
        athlete_name = "—"
        if p.internal_athlete:
            athlete_name, _ = _athletic_display(p.internal_athlete)
     

        application = getattr(p.invitation, "application", None)
        players_list = application.players if (application and application.players) else []
        participants_data.append({
            "participant_name": p.participant_name,

            "team_name": p.team_name or "—",
            "tournament": p.tournament.tournament_name if p.tournament else "—",
            "tournament_type": (
                p.tournament.tournament_type
                if p.tournament else None
            ),
            "participation_type": p.tournament.participation_type if p.tournament else None,
            "college_name": p.college_name or "—",
            "internal_team": team_name,
            "internal_athlete": athlete_name,
            "coach_name": p.coach_name or "—",
            "players_count": p.players_count,
            "players": players_list,
            "final_position": p.final_position,
            "result": p.result,
            "registered_at": p.registered_at.date().isoformat() if p.registered_at else None,
        })

   
    status_counts = Counter(t.status for t in tournaments_qs)
    status_labels = [c[0] for c in Tournament.STATUS_CHOICES if status_counts.get(c[0])]
    status_chart = {
        "labels": [dict(Tournament.STATUS_CHOICES)[s] for s in status_labels],
        "data": [status_counts[s] for s in status_labels],
    }

    type_counts = Counter(t.tournament_type for t in tournaments_qs)
    type_labels = [c[0] for c in Tournament.TOURNAMENT_TYPE if type_counts.get(c[0])]
    type_chart = {
        "labels": [dict(Tournament.TOURNAMENT_TYPE)[t] for t in type_labels],
        "data": [type_counts[t] for t in type_labels],
    }

    month_labels = [m for m in month_abbr if m]  # Jan..Dec
    monthly_counts = Counter()
    for t in tournaments_qs:
        if t.created_at:
            monthly_counts[t.created_at.strftime("%b")] += 1
    monthly_chart = {
        "labels": month_labels,
        "data": [monthly_counts.get(m, 0) for m in month_labels],
    }

    invitation_status_counts = Counter(inv.application_status for inv in invitations_qs)
    invitation_status_labels = [
        c[0] for c in TournamentInvitation.APPLICATION_STATUS if invitation_status_counts.get(c[0])
    ]
    invitation_status_chart = {
        "labels": [dict(TournamentInvitation.APPLICATION_STATUS)[s] for s in invitation_status_labels],
        "data": [invitation_status_counts[s] for s in invitation_status_labels],
    }

    growth_counts = Counter()
    for p in participants_qs:
        if p.registered_at:
            growth_counts[p.registered_at.strftime("%b")] += p.players_count
    growth_chart = {
        "labels": month_labels,
        "data": [growth_counts.get(m, 0) for m in month_labels],
    }

    context = {
        "total_tournaments_count": total_tournaments_count,
        "active_tournaments_count": active_tournaments_count,
        "upcoming_tournaments_count": upcoming_tournaments_count,
        "completed_tournaments_count": completed_tournaments_count,
        "invitations_sent_count": invitations_sent_count,
        "approved_participants_count": approved_participants_count,
        "pending_applications_count": pending_applications_count,
        "total_registered_participants_count": total_registered_participants_count,
        "tournament_dashboard_data": {
            "tournaments": tournaments_data,
            "invitations": invitations_data,
            "participants": participants_data,
            "charts": {
                "status_distribution": status_chart,
                "type_distribution": type_chart,
                "monthly_creation": monthly_chart,
                "invitation_status": invitation_status_chart,
                "participant_growth": growth_chart,
            },
        },
    }

    return render(request, "Tournament.html", context)


@require_page_access("tournament_view_page")

@login_required
def tournament_view(request, tournament_uuid):
    tournament = get_object_or_404(
        Tournament.objects.select_related("sport", "club", "venue", "organizer"),
        tournament_uuid=tournament_uuid,
    )

    context = {
        "tournament": tournament,
        "sport_name": tournament.sport.sport_name if tournament.sport else "—",
        "club_name": getattr(tournament.club, "club_name", str(tournament.club)) if tournament.club else "—",
        "venue_name": getattr(tournament.venue, "facility_name", str(tournament.venue)) if tournament.venue else "—",
        "tournament_type_label": dict(Tournament.TOURNAMENT_TYPE).get(
            tournament.tournament_type, tournament.tournament_type
        ),
        "status_label": dict(Tournament.STATUS_CHOICES).get(tournament.status, tournament.status),
        "registered_participants_count": tournament.participants.count(),
    }

    AuditLogger.log(
        request=request,
        action="VIEW",
        module="Tournament",
        object_type="Tournament",
        object_id=tournament.id,
        description=f"Viewed tournament '{tournament.tournament_name}'.",
        status="SUCCESS",
    )

    return render(request, "tournament_view.html", context)


@login_required
@require_permission("tournament_update")
@require_http_methods(["POST"])
def tournament_complete_json(request, tournament_uuid):
    with transaction.atomic():
        tournament = get_object_or_404(
            Tournament.objects.select_for_update(),
            tournament_uuid=tournament_uuid,
        )

        if tournament.status == "COMPLETED":
            return JsonResponse({
                "tournament_uuid": str(tournament.tournament_uuid),
                "status": tournament.status,
            })

        tournament.status = "COMPLETED"
        tournament.save(update_fields=["status", "updated_at"])

    AuditLogger.log(
        request=request,
        action="UPDATE",
        module="Tournament",
        object_type="Tournament",
        object_id=tournament.id,
        description=f"Marked tournament '{tournament.tournament_name}' as Completed.",
        status="SUCCESS",
    )

    return JsonResponse({
        "tournament_uuid": str(tournament.tournament_uuid),
        "status": tournament.status,
    })



@login_required
def tournament_invitation_detail_json(request, invitation_uuid):
    invitation = get_object_or_404(
        TournamentInvitation.objects.select_related("tournament"),
        invitation_uuid=invitation_uuid,
    )

    application = getattr(invitation, "application", None)

    
    applied_at_dt = (application.applied_at if application else None) or invitation.applied_at

    data = {
        "invitation_uuid": str(invitation.invitation_uuid),
        "tournament": invitation.tournament.tournament_name if invitation.tournament else "—",
        "participation_type": invitation.tournament.participation_type if invitation.tournament else None,
        "college_name": invitation.college_name or "—",
        "department_name": invitation.department_name or "—",
        "contact_person": invitation.contact_person or "—",
        "email": invitation.email,
        "mobile_number": invitation.mobile_number or "—",
        "application_status": invitation.application_status,
        "invitation_sent_at": invitation.invitation_sent_at.isoformat() if invitation.invitation_sent_at else None,
        "applied_at": applied_at_dt.isoformat() if applied_at_dt else None,
        "applied_at_display": (
            timezone.localtime(applied_at_dt).strftime("%d %b %Y, %I:%M %p") if applied_at_dt else "—"
        ),
        "application": None,
    }

    if application:
       
        raw_players = application.players or []
        players = []
        for p in raw_players:
            if isinstance(p, dict):
                name = (p.get("name") or p.get("player_name") or "").strip()
            else:
                name = str(p).strip()
            if name:
                players.append(name)

        data["application"] = {
            "entry_name": application.entry_name or "—",
            "team_name": application.team_name or "—",
            "coach_name": application.coach_name or "—",
            "contact_person": application.contact_person or "—",
            "contact_mobile": application.contact_mobile or "—",
            "players_count": application.players_count,
            "players": players,
            "faculty_remarks": application.faculty_remarks or "",
            "status": application.status,
            "admin_remarks": application.admin_remarks or "",
            "applied_at": application.applied_at.isoformat() if application.applied_at else None,
        }

    return JsonResponse(data)



@login_required
@require_permission("tournamentinvitation_update")
@require_http_methods(["POST"])
def tournament_invitation_action_json(request, invitation_uuid):
   
    action = request.POST.get("action")
    if action not in ("accept", "reject"):
        return JsonResponse({"error": "Invalid action."}, status=400)

    with transaction.atomic():
        invitation = get_object_or_404(
            TournamentInvitation.objects.select_for_update().select_related("tournament"),
            invitation_uuid=invitation_uuid,
        )

        if invitation.application_status in ("APPROVED", "REJECTED"):
            return JsonResponse({
                "invitation_uuid": str(invitation.invitation_uuid),
                "application_status": invitation.application_status,
            })

        application = getattr(invitation, "application", None)

       

        if action == "accept":
            if not application:
                return JsonResponse({"error": "No application found for this invitation."}, status=400)
            if application.status != "APPLIED" or invitation.application_status != "APPLIED":
                return JsonResponse({"error": "This application is not pending review."}, status=400)

            tournament = invitation.tournament

            if tournament.participation_type == "TEAM":
                team_name = (application.team_name or "").strip()
                if not team_name:
                    return JsonResponse({"error": "Application is missing a team name."}, status=400)
                entry_name = ""  
            else:
                entry_name = (application.entry_name or "").strip()
                if not entry_name:
                    return JsonResponse({"error": "Application is missing a valid entry name."}, status=400)
                team_name = None

            if tournament.participation_type == "TEAM":
                min_p = tournament.minimum_participants or 1
                max_p = tournament.maximum_participants or min_p
                if application.players_count < min_p or application.players_count > max_p:
                    return JsonResponse({"error": "Submitted player count is outside the allowed range."}, status=400)
            else:
                if application.players_count != 1:
                    return JsonResponse({"error": "Individual application must have exactly one participant."}, status=400)

            participant, _ = TournamentParticipant.objects.update_or_create(
                invitation=invitation,
                defaults={
                    "tournament": application.tournament,
                    "internal_team": application.internal_team,   
                    "team_name": team_name,                       
                    "participant_name": entry_name,
                    "college_name": invitation.college_name,
                    "coach_name": application.coach_name,
                    "players_count": application.players_count,
                }
            )
            transaction.on_commit(lambda p=participant: broadcast_participant_added(p))



            invitation.application_status = "APPROVED"
            invitation.approved_at = timezone.now()
            invitation.save(update_fields=["application_status", "approved_at"])

            application.status = "APPROVED"
            application.reviewed_at = timezone.now()
            application.reviewed_by = request.user
            application.participant = participant
            application.save(update_fields=["status", "reviewed_at", "reviewed_by", "participant"])

        else:  
            invitation.application_status = "REJECTED"
            invitation.save(update_fields=["application_status"])

            if application:
                application.status = "REJECTED"
                application.reviewed_at = timezone.now()
                application.reviewed_by = request.user
                application.save(update_fields=["status", "reviewed_at", "reviewed_by"])

        transaction.on_commit(lambda inv=invitation: broadcast_invitation_status(inv))

    return JsonResponse({
        "invitation_uuid": str(invitation.invitation_uuid),
        "application_status": invitation.application_status,
    })



@require_page_access("create_tournament_page")
@require_permission("tournament_create")
@login_required
def tournament_create_page(request):
    sports = Sport.objects.filter(is_active=True).order_by("sport_name")
    clubs = SportClub.objects.filter(is_active=True).select_related("sport").order_by("club_name")
    venues = SportsFacility.objects.filter(status="ACTIVE").order_by("facility_name")

    clubs_data = [
        {"id": c.id, "name": c.club_name, "sport_id": c.sport_id}
        for c in clubs
    ]
    venues_data = [
        {"id": v.facility_id, "name": v.facility_name, "sport_id": v.sport_id}
        for v in venues
    ]

    context = {
        "sports": sports,
        "clubs_data": clubs_data,
        "venues_data": venues_data,
        "tournament_type_choices": Tournament.TOURNAMENT_TYPE,
        "participation_type_choices": Tournament.PARTICIPATION_TYPE,
        "status_choices": Tournament.STATUS_CHOICES,
        "invitation_type_choices": TournamentInvitation.INVITATION_TYPE,
    }
    return render(request, "create_tournament.html", context)


def _send_tournament_invitation_email(request, tournament, invitation):
   
    if not invitation.email:
        return False

    # apply_url = request.build_absolute_uri(f"/tournaments/apply/{invitation.invitation_token}/")
    apply_url = request.build_absolute_uri(
        reverse(
            "email_tournament_apply_page",
            kwargs={
                "invitation_token": invitation.invitation_token
            }
        )
    )

    context = {
        "tournament": tournament,
        "invitation": invitation,
        "apply_url": apply_url,
        "has_banner": bool(tournament.banner),
        "has_rules_pdf": bool(tournament.rules_pdf),
    }
    html_body = render_to_string("tournament_invitation_email.html", context)
    text_body = (
        f"You're invited to {tournament.tournament_name} ({tournament.tournament_code}).\n"
        f"Sport: {tournament.sport.sport_name if tournament.sport else '-'}\n"
        f"Dates: {tournament.start_date} to {tournament.end_date}\n"
        f"Registration deadline: {tournament.registration_deadline}\n"
        f"Apply here: {apply_url}\n"
    )

    try:
        msg = EmailMultiAlternatives(
            subject=f"You're invited: {tournament.tournament_name}",
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[invitation.email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.mixed_subtype = "related"  

        if tournament.banner and os.path.exists(tournament.banner.path):
            with open(tournament.banner.path, "rb") as banner_fh:
                banner_image = MIMEImage(banner_fh.read())
                banner_image.add_header("Content-ID", "<tournament_banner>")
                banner_image.add_header(
                    "Content-Disposition", "inline", filename=os.path.basename(tournament.banner.name)
                )
                msg.attach(banner_image)

        if tournament.rules_pdf and os.path.exists(tournament.rules_pdf.path):
            with open(tournament.rules_pdf.path, "rb") as rules_fh:
                msg.attach(os.path.basename(tournament.rules_pdf.name), rules_fh.read(), "application/pdf")

        msg.send(fail_silently=False)
        return True
    except Exception:
        logger.exception(
            "Failed to send tournament invitation email to %s for tournament %s",
            invitation.email, tournament.tournament_code,
        )
        return False


@login_required
@require_http_methods(["POST"])
def tournament_create_json(request):
    errors = {}

    tournament_name = (request.POST.get("tournament_name") or "").strip()
    tournament_code = (request.POST.get("tournament_code") or "").strip()
    sport_id = (request.POST.get("sport") or "").strip()
    club_id = (request.POST.get("club") or "").strip()
    venue_id = (request.POST.get("venue") or "").strip()
    tournament_type = (request.POST.get("tournament_type") or "").strip()
    participation_type = (request.POST.get("participation_type") or "").strip()
    description = (request.POST.get("description") or "").strip()
    start_date_raw = (request.POST.get("start_date") or "").strip()
    end_date_raw = (request.POST.get("end_date") or "").strip()
    registration_deadline_raw = (request.POST.get("registration_deadline") or "").strip()
    minimum_participants_raw = (request.POST.get("minimum_participants") or "").strip()
    maximum_participants_raw = (request.POST.get("maximum_participants") or "").strip()
    entry_fee_raw = (request.POST.get("entry_fee") or "").strip()
    status = (request.POST.get("status") or "").strip() or "CREATED"

    invitation_type = (request.POST.get("invitation_type") or "").strip() or "EMAIL"
    college_name = (request.POST.get("college_name") or "").strip()
    department_name = (request.POST.get("department_name") or "").strip()
    contact_person = (request.POST.get("contact_person") or "").strip()
    mobile_number = (request.POST.get("mobile_number") or "").strip()
    remarks = (request.POST.get("remarks") or "").strip()
    college_id = (request.POST.get("college_id") or "").strip()
    department_id = (request.POST.get("department_id") or "").strip()
    receiver_ids_raw = request.POST.get("receiver_faculty_ids") or "[]"

    banner_file = request.FILES.get("banner")
    logo_file = request.FILES.get("logo")
    rules_file = request.FILES.get("rules_pdf")

    if not tournament_name:
        errors["tournament_name"] = "Tournament name is required."
    elif len(tournament_name) > 200:
        errors["tournament_name"] = "Tournament name must be 200 characters or fewer."

    if not tournament_code:
        errors["tournament_code"] = "Tournament code is required."
    elif len(tournament_code) > 30:
        errors["tournament_code"] = "Tournament code must be 30 characters or fewer."
    elif Tournament.objects.filter(tournament_code__iexact=tournament_code).exists():
        errors["tournament_code"] = "This tournament code is already in use."

    sport_obj = None
    if not sport_id:
        errors["sport"] = "Sport is required."
    else:
        sport_obj = Sport.objects.filter(id=sport_id, is_active=True).first()
        if not sport_obj:
            errors["sport"] = "Select a valid, active sport."

    club_obj = None
    if club_id:
        club_obj = SportClub.objects.filter(id=club_id, is_active=True).first()
        if not club_obj:
            errors["club"] = "Select a valid club."
        elif sport_obj and club_obj.sport_id != sport_obj.id:
            errors["club"] = "Selected club does not belong to the selected sport."

    venue_obj = None
    if venue_id:
        venue_obj = SportsFacility.objects.filter(facility_id=venue_id, status="ACTIVE").first()
        if not venue_obj:
            errors["venue"] = "Select a valid venue."

    if tournament_type not in dict(Tournament.TOURNAMENT_TYPE):
        errors["tournament_type"] = "Select a valid tournament type."

    if participation_type not in dict(Tournament.PARTICIPATION_TYPE):
        errors["participation_type"] = "Select a valid participation type."

    if status not in dict(Tournament.STATUS_CHOICES):
        errors["status"] = "Select a valid status."

    def parse_required_date(raw, field):
        if not raw:
            errors[field] = "This date is required."
            return None
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            errors[field] = "Enter a valid date (YYYY-MM-DD)."
            return None

    start_date = parse_required_date(start_date_raw, "start_date")
    end_date = parse_required_date(end_date_raw, "end_date")
    registration_deadline = parse_required_date(registration_deadline_raw, "registration_deadline")

    if start_date and end_date and start_date > end_date:
        errors["end_date"] = "End date cannot be before the start date."
    if registration_deadline and start_date and registration_deadline > start_date:
        errors["registration_deadline"] = "Registration deadline cannot be after the start date."

    minimum_participants = None
    maximum_participants = None
 
    if participation_type != "INDIVIDUAL":

        if not minimum_participants_raw:
            errors["minimum_participants"] = "Minimum participants is required."
        else:
            try:
                minimum_participants = int(minimum_participants_raw)

                if minimum_participants < 1:
                    errors["minimum_participants"] = (
                        "Minimum participants must be at least 1."
                    )

            except ValueError:
                errors["minimum_participants"] = (
                    "Minimum participants must be a whole number."
                )

        if not maximum_participants_raw:
            errors["maximum_participants"] = "Maximum participants is required."
        else:
            try:
                maximum_participants = int(maximum_participants_raw)

                if maximum_participants < 1:
                    errors["maximum_participants"] = (
                        "Maximum participants must be at least 1."
                    )

                elif (
                    minimum_participants is not None
                    and maximum_participants < minimum_participants
                ):
                    errors["maximum_participants"] = (
                        "Maximum participants must be greater than "
                        "or equal to the minimum."
                    )

            except ValueError:
                errors["maximum_participants"] = (
                    "Maximum participants must be a whole number."
                )


    entry_fee = Decimal("0")
    if entry_fee_raw:
        try:
            entry_fee = Decimal(entry_fee_raw)
            if entry_fee < 0:
                errors["entry_fee"] = "Entry fee cannot be negative."
        except InvalidOperation:
            errors["entry_fee"] = "Enter a valid entry fee."

    if invitation_type not in dict(TournamentInvitation.INVITATION_TYPE):
        errors["invitation_type"] = "Select a valid invitation type."

    college_mode = False
    is_other_college = False
    school_obj = None
    department_obj = None
    receiver_faculties = []

    if invitation_type == "DEPARTMENT":
        if tournament_type and tournament_type not in DEPARTMENT_ONLY_TOURNAMENT_TYPES + COLLEGE_TOURNAMENT_TYPES:
            errors["invitation_type"] = (
                "Department invitations are only available for Inter Department, "
                "Intra Department, Inter College and Intra College tournaments."
            )
        elif tournament_type in COLLEGE_TOURNAMENT_TYPES:
            college_mode = True
            is_other_college = (not college_id) or college_id == "OTHER"

            if is_other_college:
                if not college_name:
                    errors["college_name"] = "Enter the college name."
                if not department_name:
                    errors["department_name"] = "Enter the department name."
            else:
                school_obj = School.objects.filter(school_id=college_id, status="ACTIVE").first()
                if not school_obj:
                    errors["college_id"] = "Select a valid college."

                if not department_id:
                    errors["department_id"] = "Select a department."
                elif school_obj:
                    department_obj = Department.objects.filter(
                        department_id=department_id, school_id=school_obj.school_id, status="ACTIVE"
                    ).first()
                    if not department_obj:
                        errors["department_id"] = "Select a valid department for the chosen college."

                if school_obj and department_obj:
                    try:
                        receiver_ids = json.loads(receiver_ids_raw)
                        if not isinstance(receiver_ids, list):
                            raise ValueError
                    except (ValueError, TypeError):
                        receiver_ids = []

                    receiver_faculties = list(
                        FacultyProfile.objects.filter(
                            id__in=receiver_ids,
                            department_id=department_obj.department_id,
                            employment_status="ACTIVE",
                        ).select_related("user", "faculty_rank")
                    )
                    if not receiver_faculties:
                        errors["receiver_faculty_ids"] = "Select at least one receiver."

                college_name = school_obj.school_name if school_obj else college_name
                department_name = department_obj.department_name if department_obj else department_name

    emails_raw = request.POST.get("emails") or "[]"
    try:
        email_list = json.loads(emails_raw)
        if not isinstance(email_list, list):
            raise ValueError
    except (ValueError, TypeError):
        email_list = []
        errors["emails"] = "Could not read the recipient list. Please re-add the emails."

    clean_emails = []
    seen = set()
    for raw_email in email_list:
        candidate = (raw_email or "").strip()
        if not candidate:
            continue
        key = candidate.lower()
        if key in seen:
            continue
        try:
            validate_email(candidate)
        except ValidationError:
            errors["emails"] = f'"{candidate}" is not a valid email address.'
            break
        seen.add(key)
        clean_emails.append(candidate)

    if not errors.get("emails") and not clean_emails and not (college_mode and not is_other_college):
        errors["emails"] = "Add at least one recipient email."

    ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}
    MAX_IMAGE_SIZE = 5 * 1024 * 1024
    MAX_PDF_SIZE = 10 * 1024 * 1024

    if banner_file:
        if banner_file.content_type not in ALLOWED_IMAGE_TYPES:
            errors["banner"] = "Banner must be a PNG, JPG or WEBP image."
        elif banner_file.size > MAX_IMAGE_SIZE:
            errors["banner"] = "Banner must be 5 MB or smaller."

    if logo_file:
        if logo_file.content_type not in ALLOWED_IMAGE_TYPES:
            errors["logo"] = "Logo must be a PNG, JPG or WEBP image."
        elif logo_file.size > MAX_IMAGE_SIZE:
            errors["logo"] = "Logo must be 5 MB or smaller."

    if rules_file:
        if rules_file.content_type != "application/pdf":
            errors["rules_pdf"] = "Rules document must be a PDF file."
        elif rules_file.size > MAX_PDF_SIZE:
            errors["rules_pdf"] = "Rules document must be 10 MB or smaller."

    if errors:
        return JsonResponse(
            {"ok": False, "message": "Please fix the highlighted fields.", "errors": errors}, status=400
        )

    try:
        with transaction.atomic():
            tournament = Tournament.objects.create(
                organizer=request.user,
                sport=sport_obj,
                club=club_obj,
                venue=venue_obj,
                tournament_name=tournament_name,
                tournament_code=tournament_code,
                tournament_type=tournament_type,
                participation_type=participation_type,
                banner=banner_file,
                logo=logo_file,
                description=description,
                rules_pdf=rules_file,
                start_date=start_date,
                end_date=end_date,
                registration_deadline=registration_deadline,
                minimum_participants=minimum_participants,
                maximum_participants=maximum_participants,
                entry_fee=entry_fee,
                status=status,
            )

            invitations = []
            if college_mode and not is_other_college and receiver_faculties:
                for faculty in receiver_faculties:
                    invitation = TournamentInvitation.objects.create(
                        tournament=tournament,
                        invitation_type=invitation_type,
                        college_name=college_name or None,
                        department_name=department_name or None,
                        contact_person=contact_person or None,
                        email=faculty.email,
                        mobile_number=mobile_number,
                        receiver_faculty=faculty,
                        application_status="INVITED",
                        remarks=remarks or None,
                    )
                    invitations.append(invitation)
            else:
                for email_addr in clean_emails:
                    invitation = TournamentInvitation.objects.create(
                        tournament=tournament,
                        invitation_type=invitation_type,
                        college_name=college_name or None,
                        department_name=department_name or None,
                        contact_person=contact_person or None,
                        email=email_addr,
                        mobile_number=mobile_number,
                        application_status="INVITED",
                        remarks=remarks or None,
                    )
                    invitations.append(invitation)
    
    except IntegrityError as e:
        logger.exception("Tournament creation failed due to IntegrityError")

        return JsonResponse(
            {
                "ok": False,
                "message": "Could not create tournament.",
                "errors": {
                    "general": "A database error occurred while creating the tournament."
                },
                "debug": str(e),
            },
            status=500,
        )
    
    AuditLogger.log(
        request=request,
        action="CREATE",
        module="TournamentManagement",
        object_type="Tournament",
        object_id=tournament.id,
        description=f"Created tournament '{tournament.tournament_name}' with {len(invitations)} invitation(s).",
        after_data=AuditLogger.model_to_dict(
            tournament, ["tournament_name", "tournament_code", "tournament_type", "status"]
        ),
        status="SUCCESS",
    )

    emails_sent = 0
    emails_failed = 0

    if college_mode and not is_other_college and receiver_faculties:
        for invitation in invitations:
            notify_faculty_new_tournament_invitation(invitation)
        message = f"Tournament created successfully. {len(invitations)} invitation(s) sent."
    else:
        for invitation in invitations:
            if _send_tournament_invitation_email(request, tournament, invitation):
                emails_sent += 1
            else:
                emails_failed += 1
        message = f"Tournament created successfully. {emails_sent} invitation(s) sent."
        if emails_failed:
            message += f" {emails_failed} invitation email(s) failed to send."
            
    return JsonResponse({
        "ok": True,
        "message": message,
        "tournament_id": tournament.id,
        "invitations_created": len(invitations),
        "emails_sent": emails_sent,
        "emails_failed": emails_failed,
        "redirect_url": str(reverse("tournament_dashboard_page")),
    })


DEPARTMENT_ONLY_TOURNAMENT_TYPES = ("INTER_DEPARTMENT", "INTRA_DEPARTMENT")
COLLEGE_TOURNAMENT_TYPES = ("INTER_COLLEGE", "INTRA_COLLEGE")


@login_required
def tournament_invitation_colleges_json(request):
    schools = School.objects.filter(status="ACTIVE").order_by("school_name")
    return JsonResponse(
        [{"id": str(s.school_id), "name": s.school_name} for s in schools], safe=False
    )


@login_required
def tournament_invitation_faculty_json(request):
    department_id = request.GET.get("department_id")
    faculties = (
        FacultyProfile.objects.filter(department_id=department_id, employment_status="ACTIVE")
        .select_related("user", "faculty_rank")
        .order_by("user__first_name", "user__last_name")
    )
    data = [
        {
            "id": f.id,
            "name": f"{f.user.get_full_name()} ({f.faculty_rank.rank_name if f.faculty_rank else 'Faculty'})",
        }
        for f in faculties
    ]
    return JsonResponse(data, safe=False)



OTP_EXPIRY_MINUTES = 10
OTP_RESEND_COOLDOWN_SECONDS = 45
OTP_MAX_ATTEMPTS = 5


def _mask_email(email):
    try:
        local, domain = email.split("@", 1)
    except (ValueError, AttributeError):
        return email or ""
    if len(local) <= 2:
        masked_local = local[0] + "*" * max(len(local) - 1, 1)
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def _resolve_choice_name(selected_id, other_name, queryset, id_field, name_field):
    """Resolve a college/coach/team select value that may be a real id or 'OTHER'."""
    selected_id = (selected_id or "").strip()
    other_name = (other_name or "").strip()
    if selected_id == "OTHER":
        return other_name
    if selected_id:
        obj = queryset.filter(**{id_field: selected_id}).first()
        if obj:
            return getattr(obj, name_field)
    return ""


def _coach_display_name(coach_obj):
    
    if not coach_obj or not coach_obj.staff_id:
        return ""
    staff = (
        StaffProfile.objects.filter(employee_id=coach_obj.staff_id)
        .select_related("user")
        .first()
    )
    if staff and staff.user:
        name = staff.user.get_full_name().strip()
        if name:
            return name
    
    return coach_obj.staff_id


def _resolve_coach_application_name(coach_id, other_coach_name):
    coach_id = (coach_id or "").strip()
    other_coach_name = (other_coach_name or "").strip()[:150]
    if coach_id == "OTHER":
        return other_coach_name, (not other_coach_name)  # (name, is_error)
    if coach_id:
        coach_obj = Coach.objects.filter(coach_id=coach_id).first()
        return (_coach_display_name(coach_obj) if coach_obj else ""), False
    return "", False


def _get_email_invitation_or_404(invitation_token):
    return get_object_or_404(
        TournamentInvitation.objects.select_related("tournament", "tournament__sport", "tournament__venue"),
        invitation_token=invitation_token,
        invitation_type="EMAIL",
    )


def _invitation_status_meta(invitation, application):
    status = invitation.application_status
    if status == "APPLIED":
        return "Applied — Awaiting Admin Approval", "applied", "ti-clock-hour-4"
    if status == "APPROVED":
        return "Approved", "approved", "ti-circle-check"
    if status == "REJECTED":
        remarks = application.admin_remarks if application and application.admin_remarks else ""
        label = f"Rejected: {remarks}" if remarks else "Rejected"
        return label, "rejected", "ti-circle-x"
    return "Invited", "invited", "ti-mail"


def email_tournament_apply_page(request, invitation_token):
    invitation = _get_email_invitation_or_404(invitation_token)
    tournament = invitation.tournament

    application = getattr(invitation, "application", None)
    already_submitted = application is not None or invitation.application_status != "INVITED"
    deadline_passed = tournament.registration_deadline < timezone.localdate()

    status_display, status_class, status_icon = _invitation_status_meta(invitation, application)

    context = {
        "tournament": tournament,
        "invitation": invitation,
        "application": application,
        "already_submitted": already_submitted,
        "deadline_passed": deadline_passed,
        "status_display": status_display,
        "status_class": status_class,
        "status_icon": status_icon,
    }

    if not already_submitted and not deadline_passed:
        context["colleges"] = School.objects.filter(status="ACTIVE").order_by("school_name")
       

        coach_qs = Coach.objects.filter(is_active=True).order_by("staff_id")
        context["coaches"] = [
            {"coach_id": c.coach_id, "full_name": _coach_display_name(c)}
            for c in coach_qs
        ]

        if tournament.participation_type == "TEAM":
            teams_qs = SportTeamModel.objects.all()
            if tournament.sport_id:
                teams_qs = teams_qs.filter(sport_type_id=tournament.sport_id)
            context["internal_teams"] = teams_qs.order_by("team_name")

    return render(request, "email_tournament_apply.html", context)


@require_http_methods(["POST"])
def email_tournament_apply_send_otp_json(request, invitation_token):
    with transaction.atomic():
        invitation = get_object_or_404(
            TournamentInvitation.objects.select_for_update().select_related("tournament"),
            invitation_token=invitation_token,
            invitation_type="EMAIL",
        )
        tournament = invitation.tournament

        application = getattr(invitation, "application", None)
        if application is not None or invitation.application_status != "INVITED":
            return JsonResponse({"error": "An application has already been submitted for this invitation."}, status=400)

        if tournament.registration_deadline < timezone.localdate():
            return JsonResponse({"error": "Registration for this tournament is closed."}, status=400)

        if not invitation.email:
            return JsonResponse({"error": "No email is associated with this invitation."}, status=400)

        now = timezone.now()
        if invitation.otp_last_sent_at and (now - invitation.otp_last_sent_at).total_seconds() < OTP_RESEND_COOLDOWN_SECONDS:
            wait_left = OTP_RESEND_COOLDOWN_SECONDS - int((now - invitation.otp_last_sent_at).total_seconds())
            return JsonResponse({"error": f"Please wait {wait_left}s before requesting another code."}, status=429)

        otp_code = f"{random.randint(0, 999999):06d}"
        invitation.otp_hash = make_password(otp_code)
        invitation.otp_expires_at = now + timedelta(minutes=OTP_EXPIRY_MINUTES)
        invitation.otp_attempts = 0
        invitation.otp_last_sent_at = now
        invitation.save(update_fields=["otp_hash", "otp_expires_at", "otp_attempts", "otp_last_sent_at"])

        try:
            text_body = (
                f"Your verification code for {tournament.tournament_name} is: {otp_code}\n"
                f"This code will expire in {OTP_EXPIRY_MINUTES} minutes.\n"
                f"If you did not request this, you can ignore this email."
            )
            msg = EmailMultiAlternatives(
                subject=f"Your verification code — {tournament.tournament_name}",
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[invitation.email],
            )
            msg.send(fail_silently=False)
        except Exception:
            logger.exception(
                "Failed to send tournament application OTP to %s for invitation %s",
                invitation.email, invitation.invitation_uuid,
            )
            return JsonResponse({"error": "Could not send the verification code. Please try again."}, status=500)

        return JsonResponse({
            "success": True,
            "masked_email": _mask_email(invitation.email),
            "resend_in": OTP_RESEND_COOLDOWN_SECONDS,
        })

from Admin.models import Notification as DashboardNotification
@require_http_methods(["POST"])
def email_tournament_apply_submit_json(request, invitation_token):
    with transaction.atomic():
        invitation = get_object_or_404(
            TournamentInvitation.objects.select_for_update().select_related("tournament"),
            invitation_token=invitation_token,
            invitation_type="EMAIL",
        )
        tournament = invitation.tournament

        application = getattr(invitation, "application", None)
        if application is not None or invitation.application_status != "INVITED":
            return JsonResponse({"error": "An application has already been submitted for this invitation."}, status=400)

        if tournament.registration_deadline < timezone.localdate():
            return JsonResponse({"error": "Registration for this tournament is closed."}, status=400)

        submitted_otp = (request.POST.get("otp") or "").strip()
        if not submitted_otp:
            return JsonResponse({"error": "Verification code is required."}, status=400)

        if not invitation.otp_hash or not invitation.otp_expires_at:
            return JsonResponse({"error": "No active verification code. Please request a new one."}, status=400)

        if invitation.otp_attempts >= OTP_MAX_ATTEMPTS:
            invitation.otp_hash = None
            invitation.otp_expires_at = None
            invitation.save(update_fields=["otp_hash", "otp_expires_at"])
            return JsonResponse({"error": "Too many incorrect attempts. Please request a new code."}, status=400)

        if timezone.now() > invitation.otp_expires_at:
            invitation.otp_hash = None
            invitation.otp_expires_at = None
            invitation.save(update_fields=["otp_hash", "otp_expires_at"])
            return JsonResponse({"error": "This code has expired. Please request a new one."}, status=400)

        if not check_password(submitted_otp, invitation.otp_hash):
            invitation.otp_attempts += 1
            invitation.save(update_fields=["otp_attempts"])
            attempts_left = max(OTP_MAX_ATTEMPTS - invitation.otp_attempts, 0)
            return JsonResponse({"error": f"Incorrect code. {attempts_left} attempt(s) left."}, status=400)

        college_id = request.POST.get("college_id", "")
        # other_college_name = request.POST.get("other_college_name", "")
        
        other_college_name = (request.POST.get("other_college_name") or "").strip()[:200]
        college_name = _resolve_choice_name(
            college_id, other_college_name, School.objects.all(), "school_id", "school_name"
        )
        if not college_name:
            return JsonResponse({"error": "College is required."}, status=400)

        coach_id = request.POST.get("coach_id", "")
        other_coach_name = request.POST.get("other_coach_name", "")
        # coach_name = _resolve_choice_name(
        #     coach_id, other_coach_name, Coach.objects.all(), "coach_id", "staff_id"
        # )

        coach_name, coach_missing = _resolve_coach_application_name(coach_id, other_coach_name)
        if coach_missing:
            return JsonResponse({"error": "Please enter the coach name."}, status=400)

        contact_person = (request.POST.get("contact_person") or "").strip()[:150]
        contact_mobile = (request.POST.get("contact_mobile") or "").strip()[:20]
        faculty_remarks = (request.POST.get("faculty_remarks") or "").strip()[:500]

        if contact_mobile and not re.fullmatch(r"\d{1,15}", contact_mobile):
                return JsonResponse(
                    {"error": "Contact mobile must contain only numbers and be 1 to 15 digits."},
                    status=400,
                )

        internal_team_obj = None
        if tournament.participation_type == "TEAM":
            team_id = request.POST.get("internal_team_id", "")
            # other_team_name = request.POST.get("other_team_name", "")
            other_team_name = (request.POST.get("other_team_name") or "").strip()[:200]
            if team_id and team_id != "OTHER":
                internal_team_obj = SportTeamModel.objects.filter(team_id=team_id).first()

            team_name = _resolve_choice_name(
                team_id, other_team_name, SportTeamModel.objects.all(), "team_id", "team_name"
            )
            if not team_name:
                return JsonResponse({"error": "Internal team is required."}, status=400)

            players = [p.strip()[:150] for p in request.POST.getlist("player_name[]") if p.strip()]
            lower_names = [p.lower() for p in players]
            if len(set(lower_names)) != len(lower_names):
                return JsonResponse({"error": "Duplicate player names are not allowed."}, status=400)

            min_p = tournament.minimum_participants or 1
            max_p = tournament.maximum_participants or min_p
            if len(players) < min_p:
                return JsonResponse({"error": f"At least {min_p} player(s) are required."}, status=400)
            if len(players) > max_p:
                return JsonResponse({"error": f"No more than {max_p} player(s) are allowed."}, status=400)

            entry_name = ""
            players_count = len(players)
        else:
            entry_name = (request.POST.get("entry_name") or "").strip()[:200]
            if not entry_name:
                return JsonResponse({"error": "Participant name is required."}, status=400)
            team_name = ""
            players = []
            players_count = 1

        application = TournamentApplication.objects.create(
            tournament=tournament,
            invitation=invitation,
            entry_name=entry_name,
            team_name=team_name,
            internal_team=internal_team_obj,
            coach_name=coach_name,
            contact_person=contact_person,
            contact_mobile=contact_mobile,
            players_count=players_count,
            players=players,
            faculty_remarks=faculty_remarks,
            status="APPLIED",
        )

        invitation.college_name = college_name
        invitation.contact_person = contact_person or invitation.contact_person
        invitation.mobile_number = contact_mobile or invitation.mobile_number
        invitation.application_status = "APPLIED"
        invitation.applied_at = timezone.now()
        invitation.otp_hash = None
        invitation.otp_expires_at = None
        invitation.otp_attempts = 0
        invitation.save(update_fields=[
            "college_name", "contact_person", "mobile_number",
            "application_status", "applied_at",
            "otp_hash", "otp_expires_at", "otp_attempts",
        ])

        transaction.on_commit(lambda inv=invitation: broadcast_invitation_status(inv))
        AuditLogger.log(
            request,
            action="CREATE",
            module="TournamentManagement",
            object_type="TournamentApplication",
            object_id=application.id,
            description=(
                f"Public email application submitted for "
                f"'{tournament.tournament_name}' via invitation "
                f"{invitation.invitation_uuid}."
            ),
        )

        entry_display = team_name if tournament.participation_type == "TEAM" else entry_name

        DashboardNotification.objects.create(
            notification_type='TOURNAMENT',
            tournament_application=application,
            event='tournament_applied',
            message=f'{entry_display} submitted an application for '
                    f'"{tournament.tournament_name}"',
            icon='trophy',
            recipient=None,
        )

        return JsonResponse({
            "success": True,
            "participation_type": tournament.participation_type,
            "entry_display": team_name if tournament.participation_type == "TEAM" else entry_name,
            "college_name": college_name,
            "coach_name": coach_name,
            "contact_person": contact_person,
            "contact_mobile": contact_mobile,
            "players": players,
            "players_count": players_count,
            "status_display": "Applied — Awaiting Admin Approval",
            "applied_at_display": invitation.applied_at.strftime("%d %b %Y, %I:%M %p"),
        })


from xhtml2pdf import pisa
from openpyxl import Workbook

from Admin.Jack.models import Sport, SportTeamModel, Coach, SportClub, SportsFacility



SPORTS_REPORT_TITLES = {
    "sports": "Sports Records",
    "teams": "Team Records",
    "clubs": "Club Records",
    "facilities": "Facility Records",
    "coaches": "Coach Records",
    "tournaments": "Tournament Records",
    "athletes": "Olympic Athlete Records",
    "performances": "Performance Records",
}
 
 
def _sr_active_label(is_active):
    return "Active" if is_active else "Inactive"
 
 
def _sports_report_dataset(report_type, status_filter):
    """
    Returns (columns, rows) for the given report_type.
    columns: [{"label": ..., "key": ...}, ...]
    rows: [{"key": value, ...}, ...]   (values are already display-ready strings)
    status_filter: "ALL" | "ACTIVE" | "INACTIVE"
    """
 
    if report_type == "teams":
        columns = [
            {"label": "Team Code", "key": "team_code"},
            {"label": "Team Name", "key": "team_name"},
            {"label": "Sport", "key": "sport"},
            {"label": "Gender Category", "key": "gender_category"},
            {"label": "Division", "key": "division"},
            {"label": "Season", "key": "season"},
            {"label": "Head Coach", "key": "head_coach"},
            {"label": "Home Facility", "key": "home_facility"},
            {"label": "Founded Year", "key": "founded_year"},
            {"label": "Status", "key": "status"},
        ]
 
        qs = SportTeamModel.objects.select_related(
            "sport_type", "head_coach", "home_facility"
        ).order_by("team_name")
 
        if status_filter == "ACTIVE":
            qs = qs.filter(status=True)
        elif status_filter == "INACTIVE":
            qs = qs.filter(status=False)
 
        rows = [{
            "team_code": t.team_code,
            "team_name": t.team_name,
            "sport": t.sport_type.sport_name if t.sport_type else "",
            "gender_category": t.get_gender_category_display(),
            "division": t.division,
            "season": t.season,
            "head_coach": t.head_coach.staff_id if t.head_coach else "",
            "home_facility": t.home_facility.facility_name if t.home_facility else "",
            "founded_year": t.founded_year,
            "status": _sr_active_label(t.status),
        } for t in qs]
 
        return columns, rows
 
    if report_type == "clubs":
        columns = [
            {"label": "Club Name", "key": "club_name"},
            {"label": "Sport", "key": "sport"},
            {"label": "Total Teams", "key": "total_teams"},
            {"label": "Total Coaches", "key": "total_coaches"},
            {"label": "Status", "key": "status"},
        ]
 
        qs = SportClub.objects.select_related("sport").order_by("club_name")
 
        if status_filter == "ACTIVE":
            qs = qs.filter(is_active=True)
        elif status_filter == "INACTIVE":
            qs = qs.filter(is_active=False)
 
        rows = [{
            "club_name": c.club_name,
            "sport": c.sport.sport_name if c.sport else "",
            "total_teams": c.total_teams,
            "total_coaches": c.total_coaches,
            "status": _sr_active_label(c.is_active),
        } for c in qs]
 
        return columns, rows
 
    if report_type == "facilities":
        columns = [
            {"label": "Facility Name", "key": "facility_name"},
            {"label": "Sport", "key": "sport"},
            {"label": "Type", "key": "facility_type"},
            {"label": "Capacity", "key": "capacity"},
            {"label": "Location", "key": "location"},
            {"label": "Status", "key": "status"},
        ]
 
        qs = SportsFacility.objects.select_related("sport").order_by("facility_name")
 
        if status_filter == "ACTIVE":
            qs = qs.filter(status="ACTIVE")
        elif status_filter == "INACTIVE":
            qs = qs.exclude(status="ACTIVE")
 
        rows = [{
            "facility_name": f.facility_name,
            "sport": f.sport.sport_name if f.sport else "",
            "facility_type": f.get_facility_type_display(),
            "capacity": f.capacity,
            "location": f.location,
            "status": f.get_status_display(),
        } for f in qs]
 
        return columns, rows
 
    if report_type == "coaches":
        columns = [
            {"label": "Staff ID", "key": "staff_id"},
            {"label": "Role", "key": "role"},
            {"label": "Hire Date", "key": "hire_date"},
            {"label": "Status", "key": "status"},
        ]
 
        qs = Coach.objects.order_by("staff_id")
 
        if status_filter == "ACTIVE":
            qs = qs.filter(is_active=True)
        elif status_filter == "INACTIVE":
            qs = qs.filter(is_active=False)
 
        rows = [{
            "staff_id": c.staff_id,
            "role": c.get_role_display(),
            "hire_date": c.hire_date.strftime("%b %d, %Y") if c.hire_date else "",
            "status": _sr_active_label(c.is_active),
        } for c in qs]
 
        return columns, rows
 
    if report_type == "tournaments":
        columns = [
            {"label": "Code", "key": "tournament_code"},
            {"label": "Name", "key": "tournament_name"},
            {"label": "Sport", "key": "sport"},
            {"label": "Type", "key": "tournament_type"},
            {"label": "Participation", "key": "participation_type"},
            {"label": "Start Date", "key": "start_date"},
            {"label": "End Date", "key": "end_date"},
            {"label": "Status", "key": "status"},
        ]
 
        qs = Tournament.objects.select_related("sport").order_by("-start_date")
 
        if status_filter == "ACTIVE":
            qs = qs.filter(is_active=True)
        elif status_filter == "INACTIVE":
            qs = qs.filter(is_active=False)
 
        rows = [{
            "tournament_code": t.tournament_code,
            "tournament_name": t.tournament_name,
            "sport": t.sport.sport_name if t.sport else "",
            "tournament_type": t.get_tournament_type_display(),
            "participation_type": t.get_participation_type_display(),
            "start_date": t.start_date.strftime("%b %d, %Y") if t.start_date else "",
            "end_date": t.end_date.strftime("%b %d, %Y") if t.end_date else "",
            "status": t.get_status_display(),
        } for t in qs]
 
        return columns, rows
 
    if report_type == "athletes":
        columns = [
            {"label": "Athlete No.", "key": "athlete_number"},
            {"label": "Sport", "key": "sport"},
            {"label": "Team", "key": "team"},
            {"label": "Nationality", "key": "nationality"},
            {"label": "Target Olympics", "key": "target_olympics"},
            {"label": "World Ranking", "key": "world_ranking"},
            {"label": "Status", "key": "status"},
        ]
 
        qs = OlympicAthlete.objects.select_related("sport", "team").order_by("athlete_number")
 
        if status_filter == "ACTIVE":
            qs = qs.filter(is_active=True)
        elif status_filter == "INACTIVE":
            qs = qs.filter(is_active=False)
 
        rows = [{
            "athlete_number": a.athlete_number,
            "sport": a.sport.sport_name if a.sport else "",
            "team": a.team.team_name if a.team else "",
            "nationality": a.nationality,
            "target_olympics": a.target_olympics,
            "world_ranking": a.world_ranking,
            "status": _sr_active_label(a.is_active),
        } for a in qs]
 
        return columns, rows
 
    if report_type == "performances":
        columns = [
            {"label": "Competition", "key": "competition_name"},
            {"label": "Athlete", "key": "athlete"},
            {"label": "Level", "key": "competition_level"},
            {"label": "Event", "key": "event_name"},
            {"label": "Date", "key": "competition_date"},
            {"label": "Medal", "key": "medal"},
            {"label": "Status", "key": "status"},
        ]
 
        qs = OlympicPerformance.objects.select_related(
            "olympic_athlete", "olympic_athlete__athlete__student"
        ).order_by("-competition_date")
 
        if status_filter == "ACTIVE":
            qs = qs.filter(is_archived=False)
        elif status_filter == "INACTIVE":
            qs = qs.filter(is_archived=True)
 
        rows = []
        for p in qs:
            athlete_label = p.olympic_athlete.athlete_number if p.olympic_athlete else ""
            rows.append({
                "competition_name": p.competition_name,
                "athlete": athlete_label,
                "competition_level": p.get_competition_level_display(),
                "event_name": p.event_name,
                "competition_date": p.competition_date.strftime("%b %d, %Y") if p.competition_date else "",
                "medal": p.get_medal_display(),
                "status": "Archived" if p.is_archived else "Active",
            })
 
        return columns, rows
 
    columns = [
        {"label": "Sport Name", "key": "sport_name"},
        {"label": "Type", "key": "sport_type"},
        {"label": "Gender", "key": "gender"},
        {"label": "Team Sport", "key": "is_team_sport"},
        {"label": "Players", "key": "players"},
        {"label": "Status", "key": "status"},
    ]
 
    qs = Sport.objects.order_by("sport_name")
 
    if status_filter == "ACTIVE":
        qs = qs.filter(is_active=True)
    elif status_filter == "INACTIVE":
        qs = qs.filter(is_active=False)
 
    rows = []
    for s in qs:
        if s.min_players and s.max_players:
            players = "{}-{}".format(s.min_players, s.max_players)
        else:
            players = ""
        rows.append({
            "sport_name": s.sport_name,
            "sport_type": s.get_sport_type_display(),
            "gender": s.get_gender_display(),
            "is_team_sport": "Yes" if s.is_team_sport else "No",
            "players": players,
            "status": _sr_active_label(s.is_active),
        })
 
    return columns, rows
 
 
def _sports_report_chart_data():
    sports_by_type = (
        Sport.objects.values("sport_type")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    type_labels_map = dict(Sport.SPORT_TYPE)
 
    teams_by_sport = (
        SportTeamModel.objects.values("sport_type__sport_name")
        .annotate(total=Count("team_id"))
        .order_by("-total")[:6]
    )
 
    tournament_status = (
        Tournament.objects.values("status")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    status_labels_map = dict(Tournament.STATUS_CHOICES)
 
    medal_distribution = (
        OlympicPerformance.objects.exclude(medal="NONE")
        .values("medal")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    medal_labels_map = dict(OlympicPerformance.MEDAL_CHOICES)
 
    return {
        "sports_by_type": {
            "labels": [type_labels_map.get(row["sport_type"], row["sport_type"]) for row in sports_by_type],
            "values": [row["total"] for row in sports_by_type],
        },
        "teams_by_sport": {
            "labels": [row["sport_type__sport_name"] or "Unassigned" for row in teams_by_sport],
            "values": [row["total"] for row in teams_by_sport],
        },
        "tournament_status": {
            "labels": [status_labels_map.get(row["status"], row["status"]) for row in tournament_status],
            "values": [row["total"] for row in tournament_status],
        },
        "medal_distribution": {
            "labels": [medal_labels_map.get(row["medal"], row["medal"]) for row in medal_distribution],
            "values": [row["total"] for row in medal_distribution],
        },
    }
 
 

@require_page_access("sports_reports_page")
@login_required
def sports_reports_page(request):
 
    context = {
        "total_sports": Sport.objects.count(),
        "total_teams": SportTeamModel.objects.count(),
        "total_clubs": SportClub.objects.count(),
        "total_facilities": SportsFacility.objects.count(),
        "total_coaches": Coach.objects.count(),
        "total_tournaments": Tournament.objects.count(),
        "total_athletes": OlympicAthlete.objects.count(),
        "total_performances": OlympicPerformance.objects.count(),
        "chart_data_json": json.dumps(_sports_report_chart_data()),
    }
 
    return render(request, "sports_reports.html", context)
 
 
def sports_reports_data_json(request):
 
    report_type = request.GET.get("report_type", "sports")
    status_filter = request.GET.get("status", "ALL")
    page_number = request.GET.get("page", 1)
 
    columns, rows = _sports_report_dataset(report_type, status_filter)
 
    paginator = Paginator(rows, 10)
    page_obj = paginator.get_page(page_number)
 
    return JsonResponse({
        "columns": columns,
        "rows": list(page_obj.object_list),
        "count": paginator.count,
        "page": page_obj.number,
        "num_pages": paginator.num_pages,
        "page_size": 10,
        "title": SPORTS_REPORT_TITLES.get(report_type, "Records"),
    })
 
 
def sports_reports_export_excel(request):
 
    report_type = request.GET.get("report_type", "sports")
    status_filter = request.GET.get("status", "ALL")
 
    columns, rows = _sports_report_dataset(report_type, status_filter)
 
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = SPORTS_REPORT_TITLES.get(report_type, "Report")[:31]
 
    for col_index, col in enumerate(columns, 1):
        worksheet.cell(row=1, column=col_index).value = col["label"]
 
    for row_index, row in enumerate(rows, 2):
        for col_index, col in enumerate(columns, 1):
            worksheet.cell(row=row_index, column=col_index).value = row.get(col["key"], "")
 
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    filename = "{}.xlsx".format(SPORTS_REPORT_TITLES.get(report_type, "Sports_Report").replace(" ", "_"))
    response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename)
 
    workbook.save(response)
 
    return response
 
 
def sports_reports_export_pdf(request):
 
    report_type = request.GET.get("report_type", "sports")
    status_filter = request.GET.get("status", "ALL")
 
    columns, rows = _sports_report_dataset(report_type, status_filter)
 
    ordered_rows = [[row.get(col["key"], "") for col in columns] for row in rows]
 
    html_string = render_to_string("pdf_template.html", {
        "report_title": SPORTS_REPORT_TITLES.get(report_type, "Sports Report"),
        "generated_at": datetime.now().strftime("%B %d, %Y %I:%M %p"),
        "status_filter": status_filter,
        "columns": columns,
        "rows": ordered_rows,
    })
 
    response = HttpResponse(content_type="application/pdf")
    filename = "{}.pdf".format(SPORTS_REPORT_TITLES.get(report_type, "Sports_Report").replace(" ", "_"))
    response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename)
 
    pisa_status = pisa.CreatePDF(html_string, dest=response)
 
    if pisa_status.err:
        return HttpResponse("PDF generation failed.", status=500)
 
    return response

####################################### kali code End ######################################
 


###################################### GURU CODE START ##############################################

def students(request):
    return render(request, 'students.html')

###################################### GURU CODE END ################################################


######################################  Rixie Code Start  ###########################################

from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from Admin.bela_admin.models import Building, Floor, Room


def building_page(request):

    # =========================================================
    # ADD BUILDING
    # =========================================================

    if request.method == "POST":

        building_name = request.POST.get("building_name", "").strip()
        building_code = request.POST.get("building_code", "").strip()
        address = request.POST.get("address", "").strip()
        building_image = request.FILES.get("building_image")
        building_type = request.POST.get("building_type", "NORMAL").strip()

        if building_type not in ("MEDICAL", "NORMAL"):
            building_type = "NORMAL"

        # -------------------------
        # Validation
        # -------------------------

        if not building_name:
            messages.error(request, "Building name is required.")
            return redirect("building_page")

        if not building_code:
            messages.error(request, "Building code is required.")
            return redirect("building_page")

        # Check duplicate building code

        if Building.objects.filter(
            building_code=building_code
        ).exists():

            messages.error(
                request,
                "A building with this building code already exists."
            )

            return redirect("building_page")

        # -------------------------
        # Create Building
        # -------------------------

        Building.objects.create(
            building_name=building_name,
            building_code=building_code,
            address=address,
            building_image=building_image,
            building_type=building_type,
            status="ACTIVE"
        )

        messages.success(
            request,
            f"Building '{building_name}' added successfully."
        )

        return redirect("building_page")


    # =========================================================
    # BUILDING LIST
    # =========================================================

    building_type_filter = request.GET.get("building_type", "")

    buildings_qs = Building.objects.annotate(

        floor_count=Count(
            "floors",
            distinct=True
        ),

        room_count=Count(
            "floors__rooms",
            distinct=True
        )

    ).order_by("-created_at")

    if building_type_filter in ("MEDICAL", "NORMAL"):
        buildings_qs = buildings_qs.filter(building_type=building_type_filter)

    paginator = Paginator(buildings_qs, 10)
    page_number = request.GET.get("page")
    buildings = paginator.get_page(page_number)


    # =========================================================
    # SUMMARY
    # =========================================================

    total_buildings = Building.objects.count()

    active_buildings = Building.objects.filter(
        status="ACTIVE"
    ).count()

    inactive_buildings = Building.objects.filter(
        status="INACTIVE"
    ).count()

    normal_buildings = Building.objects.filter(
        building_type="NORMAL"
    ).count()

    medical_buildings = Building.objects.filter(
        building_type="MEDICAL"
    ).count()


    # =========================================================
    # CONTEXT
    # =========================================================

    context = {

        "buildings": buildings,

        "total_buildings": total_buildings,

        "active_buildings": active_buildings,

        "inactive_buildings": inactive_buildings,

        "normal_buildings": normal_buildings,

        "medical_buildings": medical_buildings,

        "building_type_filter": building_type_filter,

    }


    return render(
        request,
        "Rixie/building.html",
        context
    )


def building_add(request):

    if request.method == "POST":

        building_name = request.POST.get(
            "building_name",
            ""
        ).strip()

        building_code = request.POST.get(
            "building_code",
            ""
        ).strip().upper()
        building_type = request.POST.get(
              "building_type",
              "NORMAL"
        ).strip()

        address = request.POST.get(
            "address",
            ""
        ).strip()

        building_image = request.FILES.get(
            "building_image"
        )

        # Basic validation
        if not building_name:
            messages.error(
                request,
                "Building name is required."
            )
            return redirect("building_page")

        if not building_code:
            messages.error(
                request,
                "Building code is required."
            )
            return redirect("building_page")
        if building_type not in ["MEDICAL", "NORMAL"]:
            messages.error(
                 request,
                 "Please select a valid building type."
            )
            return redirect("building_page")

        # Check duplicate building code
        if Building.objects.filter(
            building_code=building_code
        ).exists():

            messages.error(
                request,
                f"Building code '{building_code}' already exists."
            )

            return redirect("building_page")

        # Create building
        Building.objects.create(
            building_name=building_name,
            building_code=building_code,
            building_type=building_type,
            address=address,
            building_image=building_image,
            status="ACTIVE"
        )

        messages.success(
            request,
            f"{building_name} added successfully."
        )

        return redirect("building_page")

    return redirect("building_page")



def building_edit(request, building_id):

    building = get_object_or_404(
        Building,
        pk=building_id
    )

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Invalid request."
        }, status=400)

    building_name = request.POST.get(
        "building_name",
        ""
    ).strip()

    building_code = request.POST.get(
        "building_code",
        ""
    ).strip()

    address = request.POST.get(
        "address",
        ""
    ).strip()

    building_image = request.FILES.get(
        "building_image"
    )

    if not building_name:

        return JsonResponse({
            "success": False,
            "message": "Building name is required."
        })

    if not building_code:

        return JsonResponse({
            "success": False,
            "message": "Building code is required."
        })

    # Check duplicate building code
    if Building.objects.filter(
        building_code=building_code
    ).exclude(
        pk=building.pk
    ).exists():

        return JsonResponse({
            "success": False,
            "message": "Building code already exists."
        })

    building.building_name = building_name
    building.building_code = building_code
    building.address = address

    if building_image:
        building.building_image = building_image

    status = request.POST.get("status", "").strip()

    if status in ("ACTIVE", "INACTIVE"):
        building.status = status

    building_type = request.POST.get(
        "building_type",
        ""
    ).strip()

    if building_type in ("MEDICAL", "NORMAL"):
        building.building_type = building_type

    building.save()

    return JsonResponse({
        "success": True,
        "message": "Building updated successfully."
    })



def building_inactivate(request, building_id):

    building = get_object_or_404(
        Building,
        pk=building_id
    )

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Invalid request."
        }, status=400)

    if building.status != "INACTIVE":

        building.status = "INACTIVE"

        building.save(update_fields=["status"])

        return JsonResponse({
            "success": True,
            "message": f'"{building.building_name}" marked as inactive.'
        })

    return JsonResponse({
        "success": False,
        "message": "Already inactive."
    }, status=400)


def building_export_excel(request):

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Buildings"

    headers = [
        "Building Name",
        "Building Code",
        "Address",
        "Floors",
        "Rooms",
        "Status",
    ]

    for col, header in enumerate(headers, 1):
        worksheet.cell(row=1, column=col).value = header

    buildings = (
        Building.objects.annotate(
            floor_count=Count(
                "floors",
                distinct=True
            ),
            room_count=Count(
                "floors__rooms",
                distinct=True
            )
        ).order_by("building_name")
    )

    row = 2

    for building in buildings:

        worksheet.cell(row=row, column=1).value = building.building_name
        worksheet.cell(row=row, column=2).value = building.building_code
        worksheet.cell(row=row, column=3).value = building.address or ""
        worksheet.cell(row=row, column=4).value = building.floor_count
        worksheet.cell(row=row, column=5).value = building.room_count
        worksheet.cell(row=row, column=6).value = building.get_status_display()

        row += 1

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response[
        "Content-Disposition"
    ] = 'attachment; filename="Buildings.xlsx"'

    workbook.save(response)

    return response


def building_export_pdf(request):

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="Buildings.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)

    data = [
        [
            "Building Name",
            "Building Code",
            "Address",
            "Floors",
            "Rooms",
            "Status"
        ]
    ]

    buildings = (
        Building.objects.annotate(
            floor_count=Count(
                "floors",
                distinct=True
            ),
            room_count=Count(
                "floors__rooms",
                distinct=True
            )
        ).order_by("building_name")
    )

    for building in buildings:

        data.append([
            building.building_name,
            building.building_code,
            building.address or "",
            building.floor_count,
            building.room_count,
            building.get_status_display(),
        ])

    table = Table(data)

    table.setStyle(TableStyle([

        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),

        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),

        ("GRID", (0,0), (-1,-1), 1, colors.black),

        ("BACKGROUND", (0,1), (-1,-1), colors.beige),

        ("ALIGN", (0,0), (-1,-1), "CENTER"),

        ("BOTTOMPADDING", (0,0), (-1,0), 10),

    ]))

    elements = [table]

    doc.build(elements)

    return response


from django.db.models import Count
from django.shortcuts import render, redirect
from django.contrib import messages


def floors_page(request):

    if request.method == "POST":

        building_id = request.POST.get("building")
        floor_name = request.POST.get("floor_name", "").strip()
        floor_number = request.POST.get("floor_number")


        if not building_id:
            messages.error(
                request,
                "Please select a building."
            )
            return redirect("floor_page")


        if not floor_name:
            messages.error(
                request,
                "Please enter the floor name."
            )
            return redirect("floor_page")

        if floor_number == "":
            messages.error(
                request,
                "Please enter the floor number."
            )
            return redirect("floor_page")


        try:

            floor_number = int(floor_number)

        except (ValueError, TypeError):

            messages.error(
                request,
                "Floor number must be a valid number."
            )

            return redirect("floor_page")


        if floor_number < 0:

            messages.error(
                request,
                "Floor number cannot be negative."
            )

            return redirect("floor_page")

        if floor_number > 10:

            messages.error(
                request,
                "Floor number cannot be greater than 10."
            )

            return redirect("floor_page")

        if not re.fullmatch(r"[A-Za-z0-9 ]+", floor_name):

            messages.error(
                request,
                "Floor name must contain only letters and numbers."
            )

            return redirect("floor_page")

        if Floor.objects.filter(
            building_id=building_id,
            floor_name__iexact=floor_name
        ).exists():

            messages.error(
                request,
                "A floor with this name already exists in this building."
            )

            return redirect("floor_page")


        try:

            building = Building.objects.get(
                id=building_id,
                status="ACTIVE"
            )

        except Building.DoesNotExist:

            messages.error(
                request,
                "Selected building does not exist or is inactive."
            )

            return redirect("floor_page")


        Floor.objects.create(
            building=building,
            floor_name=floor_name,
            floor_number=floor_number
        )


        messages.success(
            request,
            "Floor added successfully."
        )

        return redirect("floor_page")


    floors = Floor.objects.select_related(
        "building"
    ).annotate(
        room_count=Count(
            "rooms",
            distinct=True
        )
    ).order_by(
        "building__building_name",
        "floor_number"
    )

    building_type_filter = request.GET.get("building_type", "")

    if building_type_filter in ("MEDICAL", "NORMAL"):
        floors = floors.filter(building__building_type=building_type_filter)

    all_floors = floors

    paginator = Paginator(floors, 10)
    page_number = request.GET.get("page")
    floors = paginator.get_page(page_number)


    buildings = Building.objects.filter(
        status="ACTIVE"
    )


    total_floors = Floor.objects.count()

    total_rooms = Room.objects.count()

    total_buildings = Building.objects.count()

    buildings_with_floors = Building.objects.filter(
        floors__isnull=False
    ).distinct().count()

    normal_floors = Floor.objects.filter(
        building__building_type="NORMAL"
    ).count()

    medical_floors = Floor.objects.filter(
        building__building_type="MEDICAL"
    ).count()

    context = {

        "floors": floors,

        "all_floors": all_floors,

        "buildings": buildings,

        "total_floors": total_floors,

        "total_rooms": total_rooms,

        "total_buildings": total_buildings,

        "buildings_with_floors": buildings_with_floors,

        "normal_floors": normal_floors,

        "medical_floors": medical_floors,

        "building_type_filter": building_type_filter,

    }


    return render(
        request,
        "Rixie/floors.html",
        context
    )



def floor_edit(request, floor_id):

    floor = get_object_or_404(
        Floor,
        pk=floor_id
    )


    if request.method != "POST":

        return JsonResponse({
            "success": False,
            "message": "Invalid request."
        }, status=400)


    building_id = request.POST.get(
        "building"
    )

    floor_name = request.POST.get(
        "floor_name",
        ""
    ).strip()

    floor_number = request.POST.get(
        "floor_number"
    )


    # =========================================================
    # VALIDATION
    # =========================================================

    if not building_id:

        return JsonResponse({
            "success": False,
            "message": "Building is required."
        })


    if not floor_name:

        return JsonResponse({
            "success": False,
            "message": "Floor name is required."
        })


    if floor_number == "":

        return JsonResponse({
            "success": False,
            "message": "Floor number is required."
        })


    try:

        floor_number = int(
            floor_number
        )

    except (ValueError, TypeError):

        return JsonResponse({
            "success": False,
            "message": "Floor number must be a valid number."
        })


    if floor_number < 0:

        return JsonResponse({
            "success": False,
            "message": "Floor number cannot be negative."
        })

    if floor_number > 10:

        return JsonResponse({
            "success": False,
            "message": "Floor number cannot be greater than 10."
        })

    if not re.fullmatch(r"[A-Za-z0-9 ]+", floor_name):

        return JsonResponse({
            "success": False,
            "message": "Floor name must contain only letters and numbers."
        })

    if Floor.objects.filter(
        building_id=building_id,
        floor_name__iexact=floor_name
    ).exclude(
        pk=floor.id
    ).exists():

        return JsonResponse({
            "success": False,
            "message": "A floor with this name already exists in this building."
        })


    # =========================================================
    # GET BUILDING
    # =========================================================

    try:

        building = Building.objects.get(
            pk=building_id,
            status="ACTIVE"
        )

    except Building.DoesNotExist:

        return JsonResponse({
            "success": False,
            "message": "Selected building does not exist or is inactive."
        })


    # =========================================================
    # UPDATE FLOOR
    # =========================================================

    floor.building = building

    floor.floor_name = floor_name

    floor.floor_number = floor_number

    floor.save()


    # =========================================================
    # RESPONSE
    # =========================================================

    return JsonResponse({
        "success": True,
        "message": "Floor updated successfully."
    })


def floor_export_excel(request):

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Floors"

    headers = [
        "Floor Name",
        "Floor Number",
        "Building",
        "Building Code",
        "Rooms",
        "Status",
    ]

    for col, header in enumerate(headers, 1):
        worksheet.cell(row=1, column=col).value = header

    floors = (
        Floor.objects
        .select_related("building")
        .annotate(
            room_count=Count(
                "rooms",
                distinct=True
            )
        )
        .order_by("building__building_name", "floor_number")
    )

    row = 2

    for floor in floors:

        worksheet.cell(row=row, column=1).value = floor.floor_name
        worksheet.cell(row=row, column=2).value = floor.floor_number
        worksheet.cell(row=row, column=3).value = floor.building.building_name
        worksheet.cell(row=row, column=4).value = floor.building.building_code
        worksheet.cell(row=row, column=5).value = floor.room_count
        worksheet.cell(row=row, column=6).value = floor.building.get_status_display()

        row += 1

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response[
        "Content-Disposition"
    ] = 'attachment; filename="Floors.xlsx"'

    workbook.save(response)

    return response


def floor_export_pdf(request):

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="Floors.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)

    data = [
        [
            "Floor Name",
            "Floor Number",
            "Building",
            "Building Code",
            "Rooms",
            "Status"
        ]
    ]

    floors = (
        Floor.objects
        .select_related("building")
        .annotate(
            room_count=Count(
                "rooms",
                distinct=True
            )
        )
        .order_by("building__building_name", "floor_number")
    )

    for floor in floors:

        data.append([
            floor.floor_name,
            floor.floor_number,
            floor.building.building_name,
            floor.building.building_code,
            floor.room_count,
            floor.building.get_status_display(),
        ])

    table = Table(data)

    table.setStyle(TableStyle([

        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),

        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),

        ("GRID", (0,0), (-1,-1), 1, colors.black),

        ("BACKGROUND", (0,1), (-1,-1), colors.beige),

        ("ALIGN", (0,0), (-1,-1), "CENTER"),

        ("BOTTOMPADDING", (0,0), (-1,0), 10),

    ]))

    elements = [table]

    doc.build(elements)

    return response



from django.db.models import Sum



def room_page(request):
    from Admin.bela_admin.models import Room
    all_rooms = Room.objects.select_related(
        "floor",
        "floor__building"
    ).all().order_by(
        "floor__building__building_name",
        "floor__floor_number",
        "room_number"
    )

    building_type_filter = request.GET.get("building_type", "")

    rooms = all_rooms

    if building_type_filter in ("MEDICAL", "NORMAL"):
        rooms = rooms.filter(
            floor__building__building_type=building_type_filter
        )

    paginator = Paginator(
        rooms,
        10
    )

    page_number = request.GET.get("page")

    rooms_page = paginator.get_page(
        page_number
    )

    buildings = Building.objects.all().order_by("building_name")

    room_list = []

    for room in rooms:

        room_floor = getattr(room, "floor", None)
        room_building = (
            getattr(room_floor, "building", None)
            if room_floor else None
        )

        room_list.append({
            "id": room.pk,
            "room_number": room.room_number,
            "room_name": room.room_name,
            "building": (
                getattr(room_building, "building_name", "")
                if room_building else ""
            ),
            "building_type": (
                getattr(room_building, "building_type", "NORMAL")
                if room_building else "NORMAL"
            ),
            "floor": (
                getattr(room_floor, "floor_number", "")
                if room_floor else ""
            ),
            "floor_name": (
                getattr(room_floor, "floor_name", "")
                if room_floor else ""
            ),
            "room_type_display": room.get_room_type_display(),
            "room_type_value": room.room_type or "",
            "capacity": room.capacity,
            "status": room.status,
            "status_display": room.get_status_display(),
            "has_ac": room.has_ac,
            "has_projector": room.has_projector,
            "has_computers": room.has_computers,
            "building_id": (
                getattr(room_building, "pk", None)
                if room_building else None
            ),
            "floor_id": (
                getattr(room_floor, "pk", None)
                if room_floor else None
            ),
        })

    context = {
        "rooms": rooms,
        "rooms_json": room_list,
        "buildings": buildings,
        "paginated_rooms": rooms_page,
        "total_rooms": all_rooms.count(),
        "normal_rooms": all_rooms.filter(
            floor__building__building_type="NORMAL"
        ).count(),
        "medical_rooms": all_rooms.filter(
            floor__building__building_type="MEDICAL"
        ).count(),
        "available_rooms": all_rooms.filter(status="AVAILABLE").count(),
        "maintenance_rooms": all_rooms.filter(status="MAINTENANCE").count(),
        "blocked_rooms": all_rooms.filter(status="BLOCKED").count(),
        "total_capacity": all_rooms.aggregate(
            total=Sum("capacity")
        )["total"] or 0,
        "building_type_filter": building_type_filter,
    }
    
    return render(request, "Rixie/rooms.html", context)


def room_export_excel(request):
    from Admin.bela_admin.models import Room

    from Admin.bela_admin.models import Room

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Rooms"

    headers = [
        "Room Number",
        "Room Name",
        "Building",
        "Floor",
        "Floor Name",
        "Room Type",
        "Capacity",
        "Status",
        "AC",
        "Projector",
        "Computers",
    ]

    for col, header in enumerate(headers, 1):
        worksheet.cell(row=1, column=col).value = header

    rooms = (
        Room.objects
        .select_related("floor", "floor__building")
        .order_by(
            "floor__building__building_name",
            "floor__floor_number",
            "room_number"
        )
    )

    row = 2

    for room in rooms:

        # Medical rooms do not use room name,
        # room type, capacity or facilities.

        is_medical = (
            room.floor.building.building_type == "MEDICAL"
        )

        worksheet.cell(row=row, column=1).value = room.room_number
        worksheet.cell(row=row, column=2).value = (
            "" if is_medical else room.room_name
        )
        worksheet.cell(row=row, column=3).value = room.floor.building.building_name
        worksheet.cell(row=row, column=4).value = room.floor.floor_number
        worksheet.cell(row=row, column=5).value = room.floor.floor_name
        worksheet.cell(row=row, column=6).value = (
            "" if is_medical else room.get_room_type_display()
        )
        worksheet.cell(row=row, column=7).value = (
            "" if is_medical else room.capacity
        )
        worksheet.cell(row=row, column=8).value = room.get_status_display()
        worksheet.cell(row=row, column=9).value = (
            "" if is_medical else ("Yes" if room.has_ac else "No")
        )
        worksheet.cell(row=row, column=10).value = (
            "" if is_medical else ("Yes" if room.has_projector else "No")
        )
        worksheet.cell(row=row, column=11).value = (
            "" if is_medical else ("Yes" if room.has_computers else "No")
        )

        row += 1

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response[
        "Content-Disposition"
    ] = 'attachment; filename="Rooms.xlsx"'

    workbook.save(response)

    return response


def room_export_pdf(request):

    from Admin.bela_admin.models import Room

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="Rooms.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)

    data = [
        [
            "Room No.",
            "Room Name",
            "Building",
            "Floor",
            "Room Type",
            "Capacity",
            "Status"
        ]
    ]

    rooms = (
        Room.objects
        .select_related("floor", "floor__building")
        .order_by(
            "floor__building__building_name",
            "floor__floor_number",
            "room_number"
        )
    )

    for room in rooms:

        # Medical rooms do not use room name,
        # room type or capacity.

        is_medical = (
            room.floor.building.building_type == "MEDICAL"
        )

        data.append([
            room.room_number,
            "" if is_medical else room.room_name,
            room.floor.building.building_name,
            room.floor.floor_name,
            "" if is_medical else room.get_room_type_display(),
            "" if is_medical else room.capacity,
            room.get_status_display(),
        ])

    table = Table(data)

    table.setStyle(TableStyle([

        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),

        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),

        ("GRID", (0,0), (-1,-1), 1, colors.black),

        ("BACKGROUND", (0,1), (-1,-1), colors.beige),

        ("ALIGN", (0,0), (-1,-1), "CENTER"),

        ("BOTTOMPADDING", (0,0), (-1,0), 10),

    ]))

    doc.build([table])

    return response

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET, require_POST




@require_GET
def room_floors(request):
    from Admin.bela_admin.models import Room
    building_id = request.GET.get("building_id")

    if not building_id:
        return JsonResponse({
            "success": False,
            "floors": []
        })

    floors = Floor.objects.filter(
        building_id=building_id
    ).order_by("floor_number")

    data = []

    for floor in floors:
        data.append({
            "id": floor.pk,
            "floor_number": floor.floor_number,
        })

    return JsonResponse({
        "success": True,
        "floors": data
    })

@require_POST
def add_room(request):
    from Admin.bela_admin.models import Room
    building_id = request.POST.get("building")
    floor_id = request.POST.get("floor")
    room_number = request.POST.get("room_number", "").strip()
    room_name = request.POST.get("room_name", "").strip()
    room_type = request.POST.get("room_type")
    capacity = request.POST.get("capacity")
    status = request.POST.get("status")

    has_ac = request.POST.get("has_ac") == "on"
    has_projector = request.POST.get("has_projector") == "on"
    has_computers = request.POST.get("has_computers") == "on"

    if not all([
        building_id,
        floor_id,
        room_number,
        status,
    ]):
        return JsonResponse({
            "success": False,
            "message": "Please fill in all required fields."
        }, status=400)

    building = get_object_or_404(
        Building,
        pk=building_id
    )

    if building.building_type == "MEDICAL":

        # Medical rooms do not use room name,
        # room type, capacity or facilities.

        room_name = ""
        room_type = None
        capacity = 0

        has_ac = False
        has_projector = False
        has_computers = False

    else:

        if not all([
            room_name,
            room_type,
            capacity,
        ]):
            return JsonResponse({
                "success": False,
                "message": "Please fill in all required fields."
            }, status=400)

        try:
            capacity = int(capacity)
        except (TypeError, ValueError):
            return JsonResponse({
                "success": False,
                "message": "Capacity must be a valid number."
            }, status=400)

        if capacity <= 0:
            return JsonResponse({
                "success": False,
                "message": "Capacity must be greater than 0."
            }, status=400)

        if capacity > 200:
            return JsonResponse({
                "success": False,
                "message": "Capacity cannot exceed 200."
            }, status=400)

    if not re.fullmatch(r"\d+", room_number):
        return JsonResponse({
            "success": False,
            "message": "Room number must contain only numbers."
        }, status=400)

    if int(room_number) > 50:
        return JsonResponse({
            "success": False,
            "message": "Room number cannot exceed 50."
        }, status=400)

    floor = get_object_or_404(
        Floor,
        pk=floor_id,
        building=building
    )

    if Room.objects.filter(
        floor=floor,
        room_number=room_number
    ).exists():
        return JsonResponse({
            "success": False,
            "message": "A room with this number already exists on this floor."
        }, status=400)

    room = Room.objects.create(
        floor=floor,
        room_number=room_number,
        room_name=room_name,
        room_type=room_type,
        capacity=capacity,
        status=status,
        has_ac=has_ac,
        has_projector=has_projector,
        has_computers=has_computers,
    )

    return JsonResponse({
        "success": True,
        "message": f"Room {room.room_number} added successfully.",

        "room": {
            "id": room.pk,
            "room_number": room.room_number,
            "room_name": room.room_name,
            "building": building.building_name,
            "building_type": building.building_type,
            "floor": floor.floor_number,
            "floor_name": floor.floor_name,
            "building_id": building.pk,
            "floor_id": floor.pk,
            "room_type_value": room.room_type or "",
            "room_type": room.get_room_type_display(),
            "capacity": room.capacity,
            "status": room.status,
            "status_display": room.get_status_display(),
            "has_ac": room.has_ac,
            "has_projector": room.has_projector,
            "has_computers": room.has_computers,
        },

        "statistics": {
            "total_rooms": Room.objects.count(),
            "normal_rooms": Room.objects.filter(
                floor__building__building_type="NORMAL"
            ).count(),
            "medical_rooms": Room.objects.filter(
                floor__building__building_type="MEDICAL"
            ).count(),
            "available_rooms": Room.objects.filter(
                status="AVAILABLE"
            ).count(),
            "maintenance_rooms": Room.objects.filter(
                status="MAINTENANCE"
            ).count(),
            "blocked_rooms": Room.objects.filter(
                status="BLOCKED"
            ).count(),
            "total_capacity": sum(
                Room.objects.values_list(
                    "capacity",
                    flat=True
                )
            ),
        }
    })


@require_POST
def edit_room(request, room_id):
    from Admin.bela_admin.models import Room
    room = get_object_or_404(
        Room.objects.select_related(
            "floor",
            "floor__building"
        ),
        pk=room_id
    )

    building_id = request.POST.get("building")
    floor_id = request.POST.get("floor")
    room_number = request.POST.get("room_number", "").strip()
    room_name = request.POST.get("room_name", "").strip()
    room_type = request.POST.get("room_type")
    capacity = request.POST.get("capacity")
    status = request.POST.get("status")

    has_ac = request.POST.get("has_ac") == "on"
    has_projector = request.POST.get("has_projector") == "on"
    has_computers = request.POST.get("has_computers") == "on"

    if not all([
        building_id,
        floor_id,
        room_number,
        status,
    ]):
        return JsonResponse({
            "success": False,
            "message": "Please fill in all required fields."
        }, status=400)

    building = get_object_or_404(
        Building,
        pk=building_id
    )

    if building.building_type == "MEDICAL":

        # Medical rooms do not use room name,
        # room type, capacity or facilities.

        room_name = ""
        room_type = None
        capacity = 0

        has_ac = False
        has_projector = False
        has_computers = False

    else:

        if not all([
            room_name,
            room_type,
            capacity,
        ]):
            return JsonResponse({
                "success": False,
                "message": "Please fill in all required fields."
            }, status=400)

        try:
            capacity = int(capacity)
        except (TypeError, ValueError):
            return JsonResponse({
                "success": False,
                "message": "Capacity must be a valid number."
            }, status=400)

        if capacity <= 0:
            return JsonResponse({
                "success": False,
                "message": "Capacity must be greater than 0."
            }, status=400)

        if capacity > 200:
            return JsonResponse({
                "success": False,
                "message": "Capacity cannot exceed 200."
            }, status=400)

    if not re.fullmatch(r"\d+", room_number):
        return JsonResponse({
            "success": False,
            "message": "Room number must contain only numbers."
        }, status=400)

    if int(room_number) > 50:
        return JsonResponse({
            "success": False,
            "message": "Room number cannot exceed 50."
        }, status=400)

    # Important:
    # The floor MUST belong to the selected building.
    floor = get_object_or_404(
        Floor,
        pk=floor_id,
        building=building
    )

    if Room.objects.filter(
        floor=floor,
        room_number=room_number
    ).exclude(
        pk=room.pk
    ).exists():
        return JsonResponse({
            "success": False,
            "message": "A room with this number already exists on this floor."
        }, status=400)

    room.floor = floor
    room.room_number = room_number
    room.room_name = room_name
    room.room_type = room_type
    room.capacity = capacity
    room.status = status
    room.has_ac = has_ac
    room.has_projector = has_projector
    room.has_computers = has_computers

    room.save()

    return JsonResponse({
        "success": True,
        "message": f"Room {room.room_number} updated successfully.",

        "room": {
            "id": room.pk,
            "room_number": room.room_number,
            "room_name": room.room_name,
            "building": building.building_name,
            "building_type": building.building_type,
            "building_id": building.pk,
            "floor": floor.floor_number,
            "floor_name": floor.floor_name,
            "floor_id": floor.pk,
            "room_type": room.get_room_type_display(),
            "room_type_value": room.room_type or "",
            "capacity": room.capacity,
            "status": room.status,
            "status_display": room.get_status_display(),
            "has_ac": room.has_ac,
            "has_projector": room.has_projector,
            "has_computers": room.has_computers,
        },

        "statistics": {
            "total_rooms": Room.objects.count(),

            "normal_rooms": Room.objects.filter(
                floor__building__building_type="NORMAL"
            ).count(),

            "medical_rooms": Room.objects.filter(
                floor__building__building_type="MEDICAL"
            ).count(),

            "available_rooms": Room.objects.filter(
                status="AVAILABLE"
            ).count(),

            "maintenance_rooms": Room.objects.filter(
                status="MAINTENANCE"
            ).count(),

            "blocked_rooms": Room.objects.filter(
                status="BLOCKED"
            ).count(),

            "total_capacity": sum(
                Room.objects.values_list(
                    "capacity",
                    flat=True
                )
            ),
        }
    })

    
######################################  Rixie Code End  ###########################################

#<-----------------Blaze code start(13.08.26)---------------->






















from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Exists, OuterRef, Subquery
from django.db.models.functions import ExtractMonth, ExtractYear
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime

from .models import Hostel, Room, RoomAllocation, HostelAuditLog
from Admin.models import User


@login_required
def hostel_dashboard(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        messages.error(request, "You don't have permission to access this page.")
        return redirect("login")
    
    total_hostels = Hostel.objects.filter(status='ACTIVE').count()
    total_rooms = Room.objects.count()
    available_rooms = Room.objects.filter(is_available=True, status='AVAILABLE').count()
    occupied_rooms = Room.objects.filter(status='OCCUPIED').count()
    maintenance_rooms = Room.objects.filter(status='MAINTENANCE').count()
    active_allocations = RoomAllocation.objects.filter(status='ACTIVE').count()
    total_students = User.objects.filter(is_student=True, account_status='ACTIVE').count()
    
    total_capacity = total_rooms if total_rooms > 0 else 1
    available_percentage = round((available_rooms / total_capacity) * 100)
    allocation_percentage = round((active_allocations / total_students) * 100) if total_students > 0 else 0
    occupancy_rate = round((occupied_rooms / total_capacity) * 100)
    
    recent_allocations = RoomAllocation.objects.select_related(
        'student', 'room', 'room__hostel'
    ).order_by('-allocated_date')[:5]
    
    hostels_qs = Hostel.objects.all().annotate(
        total_rooms_count=Count('rooms'),
        available_rooms_count=Count('rooms', filter=Q(rooms__status='AVAILABLE')),
        occupied_rooms_count=Count('rooms', filter=Q(rooms__status='OCCUPIED')),
    )

    hostels_map_data = [
        {
            'id': h.id,
            'name': h.name,
            'code': h.code,
            'address': h.address or '',
            'lat': float(h.latitude) if h.latitude is not None else None,
            'lng': float(h.longitude) if h.longitude is not None else None,
            'total_rooms': h.total_rooms_count,
            'available_rooms': h.available_rooms_count,
            'occupied_rooms': h.occupied_rooms_count,
            'total_floors': h.total_floors,
            'image_url': h.image.url if h.image else '',
            'status': h.status.lower()
        }
        for h in hostels_qs
    ]
    
    monthly_allocations = []
    month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    current_year = timezone.now().year
    
    for month in range(1, 13):
        count = RoomAllocation.objects.filter(
            allocated_date__month=month,
            allocated_date__year=current_year
        ).count()
        monthly_allocations.append(count)
    
    context = {
        'user': request.user,
        'total_hostels': total_hostels,
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'occupied_rooms': occupied_rooms,
        'maintenance_rooms': maintenance_rooms,
        'active_allocations': active_allocations,
        'total_students': total_students,
        'available_percentage': available_percentage,
        'allocation_percentage': allocation_percentage,
        'occupancy_rate': occupancy_rate,
        'recent_allocations': recent_allocations,
        'hostels_map_data': hostels_map_data,
        'monthly_allocations': monthly_allocations,
        'month_labels': month_labels,
        'active_sb': 'hostel_dashboard'
    }
    return render(request, 'Blaze_Hostel/hostel_dashboard.html', context)


@login_required
def hostel_list(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        messages.error(request, "Permission denied.")
        return redirect("login")
    
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', 'all')
    
    hostels = Hostel.objects.all().annotate(
        room_count=Count('rooms'),
        occupied_count=Count('rooms', filter=Q(rooms__status='OCCUPIED')),
        student_count=Count('rooms__allocations', filter=Q(rooms__allocations__status='ACTIVE'), distinct=True)
    )
    
    if search:
        hostels = hostels.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(address__icontains=search)
        )
    
    if status_filter != 'all':
        hostels = hostels.filter(status=status_filter.upper())
    
    paginator = Paginator(hostels, 10)
    page = request.GET.get('page')
    hostels_page = paginator.get_page(page)
    
    context = {
        'user': request.user,
        'hostels': hostels_page,
        'active_sb': 'hostel_list',
        'search': search,
        'status_filter': status_filter,
    }
    return render(request, 'Blaze_Hostel/hostel_list.html', context)


@login_required
def hostel_detail(request, uuid, hostel_id):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    hostel = get_object_or_404(Hostel, id=hostel_id)
    rooms = Room.objects.filter(hostel=hostel).order_by('floor', 'room_number')
    allocations = RoomAllocation.objects.filter(
        room__hostel=hostel,
        status='ACTIVE'
    ).select_related('student', 'room')
    
    context = {
        'user': request.user,
        'hostel': hostel,
        'rooms': rooms,
        'allocations': allocations,
        'active_sb': 'hostel_list'
    }
    return render(request, 'Blaze_Hostel/hostel_detail.html', context)


@login_required
@require_http_methods(["POST"])
def add_hostel_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    name = request.POST.get('name', '').strip()
    code = request.POST.get('code', '').strip().upper()
    address = request.POST.get('address', '').strip()
    contact_number = request.POST.get('contact_number', '').strip()
    description = request.POST.get('description', '').strip()
    gender_restriction = request.POST.get('gender_restriction', 'ANY')
    total_floors_raw = request.POST.get('total_floors', '').strip()
    latitude_raw = request.POST.get('latitude', '').strip()
    longitude_raw = request.POST.get('longitude', '').strip()
    image = request.FILES.get('image')
    
    if not name:
        return JsonResponse({'success': False, 'error': 'Hostel name is required'})
    
    if not code:
        return JsonResponse({'success': False, 'error': 'Hostel code is required'})
    
    if Hostel.objects.filter(code=code).exists():
        return JsonResponse({'success': False, 'error': f'Hostel with code "{code}" already exists'})
    
    if Hostel.objects.filter(name=name).exists():
        return JsonResponse({'success': False, 'error': f'Hostel with name "{name}" already exists'})
    
    latitude = None
    longitude = None
    try:
        if latitude_raw and longitude_raw:
            latitude = float(latitude_raw)
            longitude = float(longitude_raw)
    except ValueError:
        latitude = None
        longitude = None

    try:
        total_floors = int(total_floors_raw) if total_floors_raw else 1
        if total_floors < 1:
            total_floors = 1
    except ValueError:
        total_floors = 1
    
    try:
        hostel = Hostel.objects.create(
            name=name,
            code=code,
            address=address or None,
            contact_number=contact_number or None,
            description=description or None,
            gender_restriction=gender_restriction,
            latitude=latitude,
            longitude=longitude,
            total_floors=total_floors,
            image=image,
            status='ACTIVE',
            created_by=request.user
        )
        
        HostelAuditLog.objects.create(
            user=request.user,
            action='CREATE',
            module='HOSTEL',
            object_type='Hostel',
            object_id=hostel.id,
            changes={'name': name, 'code': code, 'gender_restriction': gender_restriction}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Hostel "{name}" created successfully!',
            'hostel_id': hostel.id,
            'hostel_name': hostel.name,
            'hostel_code': hostel.code,
            'hostel_total_floors': hostel.total_floors,
            'hostel_image_url': hostel.image.url if hostel.image else ''
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def update_hostel_json(request, uuid, hostel_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    hostel = get_object_or_404(Hostel, id=hostel_id)
    
    name = request.POST.get('name', '').strip()
    code = request.POST.get('code', '').strip().upper()
    address = request.POST.get('address', '').strip()
    contact_number = request.POST.get('contact_number', '').strip()
    description = request.POST.get('description', '').strip()
    gender_restriction = request.POST.get('gender_restriction', 'ANY')
    status = request.POST.get('status', 'ACTIVE')
    total_floors_raw = request.POST.get('total_floors', '').strip()
    latitude_raw = request.POST.get('latitude', '').strip()
    longitude_raw = request.POST.get('longitude', '').strip()
    
    if not name:
        return JsonResponse({'success': False, 'error': 'Hostel name is required'})
    
    if not code:
        return JsonResponse({'success': False, 'error': 'Hostel code is required'})
    
    if Hostel.objects.filter(code=code).exclude(id=hostel_id).exists():
        return JsonResponse({'success': False, 'error': f'Hostel with code "{code}" already exists'})
    
    if Hostel.objects.filter(name=name).exclude(id=hostel_id).exists():
        return JsonResponse({'success': False, 'error': f'Hostel with name "{name}" already exists'})
    
    try:
        if latitude_raw and longitude_raw:
            latitude = float(latitude_raw)
            longitude = float(longitude_raw)
        else:
            latitude = None
            longitude = None
    except ValueError:
        latitude = None
        longitude = None
    
    try:
        total_floors = int(total_floors_raw) if total_floors_raw else 1
        if total_floors < 1:
            total_floors = 1
    except ValueError:
        total_floors = 1
    
    try:
        hostel.name = name
        hostel.code = code
        hostel.address = address or None
        hostel.contact_number = contact_number or None
        hostel.description = description or None
        hostel.gender_restriction = gender_restriction
        hostel.status = status
        hostel.total_floors = total_floors
        hostel.latitude = latitude
        hostel.longitude = longitude
        
        if request.FILES.get('image'):
            hostel.image = request.FILES.get('image')
        
        hostel.save()
        
        HostelAuditLog.objects.create(
            user=request.user,
            action='UPDATE',
            module='HOSTEL',
            object_type='Hostel',
            object_id=hostel.id,
            changes={'name': name, 'code': code, 'status': status}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Hostel "{name}" updated successfully!',
            'hostel_id': hostel.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def delete_hostel_json(request, uuid, hostel_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    hostel = get_object_or_404(Hostel, id=hostel_id)
    
    if not hostel.can_delete():
        occupied_rooms = hostel.get_occupied_rooms_count()
        students_count = hostel.get_students_count()
        
        return JsonResponse({
            'success': False,
            'error': f'Cannot delete "{hostel.name}" because it has {occupied_rooms} occupied room(s) and {students_count} student(s) allocated.',
            'occupied_rooms': occupied_rooms,
            'students_count': students_count
        })
    
    if Room.objects.filter(hostel=hostel).exists():
        return JsonResponse({
            'success': False,
            'error': f'Cannot delete "{hostel.name}" because it has rooms. Please delete all rooms first.'
        })
    
    try:
        hostel_name = hostel.name
        hostel.delete()
        
        HostelAuditLog.objects.create(
            user=request.user,
            action='DELETE',
            module='HOSTEL',
            object_type='Hostel',
            object_id=hostel_id,
            changes={'name': hostel_name}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Hostel "{hostel_name}" deleted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def hostel_details_json(request, uuid, hostel_id):
    try:
        user_uuid = str(request.user.uuid)
        url_uuid = str(uuid)
        
        if user_uuid != url_uuid:
            return JsonResponse({
                'success': False, 
                'error': 'Unauthorized - UUID mismatch',
                'debug': f'User UUID: {user_uuid}, URL UUID: {url_uuid}'
            }, status=401)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'UUID error: {str(e)}'}, status=401)
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    try:
        hostel = get_object_or_404(Hostel, id=hostel_id)
        
        room_count = Room.objects.filter(hostel=hostel).count()
        occupied_count = Room.objects.filter(hostel=hostel, status='OCCUPIED').count()
        available_count = Room.objects.filter(hostel=hostel, status='AVAILABLE').count()
        student_count = RoomAllocation.objects.filter(
            room__hostel=hostel,
            status='ACTIVE'
        ).values('student').distinct().count()
        
        has_occupied_rooms = Room.objects.filter(hostel=hostel, status='OCCUPIED').exists()
        has_active_allocations = RoomAllocation.objects.filter(
            room__hostel=hostel,
            status='ACTIVE'
        ).exists()
        can_delete = not (has_occupied_rooms or has_active_allocations)
        
        return JsonResponse({
            'success': True,
            'hostel': {
                'id': hostel.id,
                'name': hostel.name,
                'code': hostel.code,
                'address': hostel.address or '',
                'contact_number': hostel.contact_number or '',
                'description': hostel.description or '',
                'gender_restriction': hostel.gender_restriction,
                'gender_restriction_display': hostel.get_gender_restriction_display(),
                'status': hostel.status,
                'status_display': hostel.get_status_display(),
                'total_floors': hostel.total_floors,
                'latitude': float(hostel.latitude) if hostel.latitude else None,
                'longitude': float(hostel.longitude) if hostel.longitude else None,
                'image_url': hostel.image.url if hostel.image else '',
                'created_at': hostel.created_at.strftime('%d %b %Y, %I:%M %p') if hostel.created_at else '',
                'room_count': room_count,
                'occupied_count': occupied_count,
                'available_count': available_count,
                'student_count': student_count,
                'can_delete': can_delete
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def student_list(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        messages.error(request, "Permission denied.")
        return redirect("login")
    
    search = request.GET.get('search', '').strip()
    hostel_filter = request.GET.get('hostel', 'all')
    status_filter = request.GET.get('status', 'all')
    
    students = User.objects.filter(is_student=True)
    
    students = students.annotate(
        has_allocation=Exists(RoomAllocation.objects.filter(student=OuterRef('pk'), status='ACTIVE')),
        hostel_name=Subquery(
            RoomAllocation.objects.filter(
                student=OuterRef('pk'),
                status='ACTIVE'
            ).values('room__hostel__name')[:1]
        ),
        room_number=Subquery(
            RoomAllocation.objects.filter(
                student=OuterRef('pk'),
                status='ACTIVE'
            ).values('room__room_number')[:1]
        )
    )
    
    if search:
        students = students.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(username__icontains=search) |
            Q(email__icontains=search)
        )
  
    if hostel_filter != 'all':
        students = students.filter(
            id__in=RoomAllocation.objects.filter(
                room__hostel_id=hostel_filter,
                status='ACTIVE'
            ).values_list('student_id', flat=True)
        )
    
    if status_filter == 'allocated':
        students = students.filter(has_allocation=True)
    elif status_filter == 'unallocated':
        students = students.filter(has_allocation=False)
    
    paginator = Paginator(students, 15)
    page = request.GET.get('page')
    students_page = paginator.get_page(page)
    
    hostels = Hostel.objects.filter(status='ACTIVE')
    
    context = {
        'user': request.user,
        'students': students_page,
        'hostels': hostels,
        'active_sb': 'student_list',
        'search': search,
        'hostel_filter': hostel_filter,
        'status_filter': status_filter,
    }
    return render(request, 'Blaze_Hostel/student_list.html', context)


@login_required
def student_detail_json(request, uuid, student_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    student = get_object_or_404(User, id=student_id, is_student=True)
    
    allocation = RoomAllocation.objects.filter(
        student=student,
        status='ACTIVE'
    ).select_related('room', 'room__hostel').first()
    
    history = RoomAllocation.objects.filter(
        student=student
    ).select_related('room', 'room__hostel').order_by('-allocated_date')
    
    data = {
        'success': True,
        'student': {
            'id': student.id,
            'full_name': student.full_name,
            'username': student.username,
            'email': student.email,
            'first_name': student.first_name or '',
            'last_name': student.last_name or '',
            'account_status': student.account_status,
            'mobile_number': getattr(student, 'mobile_number', 'N/A'),
            'gender': getattr(student, 'gender', 'N/A'),
            'date_of_birth': getattr(student, 'date_of_birth', None),
        },
        'current_allocation': {
            'id': allocation.id if allocation else None,
            'room_number': allocation.room.room_number if allocation else None,
            'hostel_name': allocation.room.hostel.name if allocation else None,
            'move_in_date': allocation.move_in_date.strftime('%d %b %Y') if allocation and allocation.move_in_date else None,
            'allocated_date': allocation.allocated_date.strftime('%d %b %Y') if allocation else None,
        } if allocation else None,
        'allocation_history': [
            {
                'id': a.id,
                'room_number': a.room.room_number,
                'hostel_name': a.room.hostel.name,
                'move_in_date': a.move_in_date.strftime('%d %b %Y') if a.move_in_date else None,
                'move_out_date': a.move_out_date.strftime('%d %b %Y') if a.move_out_date else None,
                'status': a.status,
                'status_display': a.get_status_display(),
                'allocated_date': a.allocated_date.strftime('%d %b %Y')
            }
            for a in history
        ]
    }
    
    return JsonResponse(data)


@login_required
def room_management(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        messages.error(request, "Permission denied.")
        return redirect("login")
    
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', 'all')
    hostel_filter = request.GET.get('hostel', 'all')
    
    rooms = Room.objects.select_related('hostel', 'created_by').all()
    
    if search:
        rooms = rooms.filter(
            Q(room_number__icontains=search) |
            Q(hostel__name__icontains=search)
        )
    
    if status_filter != 'all':
        rooms = rooms.filter(status=status_filter.upper())
    
    if hostel_filter != 'all':
        rooms = rooms.filter(hostel_id=hostel_filter)
    
    paginator = Paginator(rooms, 15)
    page = request.GET.get('page')
    rooms_page = paginator.get_page(page)
    
    hostels = Hostel.objects.filter(status='ACTIVE')
    
    context = {
        'user': request.user,
        'rooms': rooms_page,
        'hostels': hostels,
        'active_sb': 'room_management',
        'search': search,
        'status_filter': status_filter,
        'hostel_filter': hostel_filter,
    }
    return render(request, 'Blaze_Hostel/room_management.html', context)


@login_required
def add_room_page(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        messages.error(request, "Permission denied.")
        return redirect("login")
    
    hostels = Hostel.objects.filter(status='ACTIVE')
    hostel_floors_map = {str(h.id): h.total_floors for h in hostels}

    context = {
        'user': request.user,
        'hostels': hostels,
        'hostel_floors_map': hostel_floors_map,
        'active_sb': 'add_room'
    }
    return render(request, 'Blaze_Hostel/add_room.html', context)


@login_required
@require_http_methods(["POST"])
def add_room_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    hostel_id = request.POST.get('hostel_id')
    room_number = request.POST.get('room_number')
    floor_raw = request.POST.get('floor')
    capacity_raw = request.POST.get('capacity')
    rent_raw = request.POST.get('rent_per_month')
    amenities = request.POST.get('amenities', '')
    status = request.POST.get('status', 'AVAILABLE')
    image = request.FILES.get('image')
    
    if not all([hostel_id, room_number, floor_raw, capacity_raw, rent_raw]):
        return JsonResponse({'success': False, 'error': 'All required fields must be filled'})
    
    try:
        floor = int(floor_raw)
        capacity = int(capacity_raw)
        rent_per_month = float(rent_raw)
    except ValueError as e:
        return JsonResponse({'success': False, 'error': f'Invalid number format: {str(e)}'})
    
    if Room.objects.filter(hostel_id=hostel_id, room_number=room_number).exists():
        return JsonResponse({'success': False, 'error': 'Room number already exists in this hostel'})
    
    try:
        room = Room.objects.create(
            hostel_id=hostel_id,
            room_number=room_number,
            floor=floor,
            capacity=capacity,
            current_occupancy=0,
            rent_per_month=rent_per_month,
            amenities=amenities,
            image=image,
            created_by=request.user,
            is_available=True,
            status=status if status != 'RESERVED' else 'AVAILABLE'
        )
        
        HostelAuditLog.objects.create(
            user=request.user,
            action='CREATE',
            module='ROOM',
            object_type='Room',
            object_id=room.id,
            changes={'room_number': room_number, 'hostel': room.hostel.name}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Room {room_number} added successfully!',
            'room_id': room.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def delete_room_json(request, uuid, room_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        room = get_object_or_404(Room, id=room_id)
        
        if room.status == 'OCCUPIED':
            return JsonResponse({'success': False, 'error': 'Cannot delete occupied room'})
        
        room.delete()
        return JsonResponse({'success': True, 'message': 'Room deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def room_details_json(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    return JsonResponse({
        'success': True,
        'room': {
            'id': room.id,
            'room_number': room.room_number,
            'hostel': room.hostel.name,
            'hostel_id': room.hostel.id,
            'floor': room.floor,
            'capacity': room.capacity,
            'current_occupancy': room.current_occupancy,
            'rent_per_month': str(room.rent_per_month),
            'status': room.status,
            'status_display': room.get_status_display(),
            'amenities': room.amenities or '',
            'image_url': room.image.url if room.image else '',
            'created_at': room.created_at.strftime('%d %b %Y, %I:%M %p') if room.created_at else '',
        }
    })


@login_required
@require_http_methods(["POST"])
def update_room_json(request, room_id):
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    room = get_object_or_404(Room, id=room_id)
    
    hostel_id = request.POST.get('hostel_id')
    room_number = request.POST.get('room_number')
    floor = request.POST.get('floor')
    capacity = request.POST.get('capacity')
    rent_per_month = request.POST.get('rent_per_month')
    status = request.POST.get('status')
    amenities = request.POST.get('amenities', '')
    
    if not all([hostel_id, room_number, floor, capacity, rent_per_month]):
        return JsonResponse({'success': False, 'error': 'All required fields must be filled'})
    
    try:
        room.hostel_id = hostel_id
        room.room_number = room_number
        room.floor = int(floor)
        room.capacity = int(capacity)
        room.rent_per_month = float(rent_per_month)
        room.status = status
        room.amenities = amenities
        room.save()
        
        return JsonResponse({'success': True, 'message': 'Room updated successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def allocate_room(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        messages.error(request, "Permission denied.")
        return redirect("login")
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        room_id = request.POST.get('room_id')
        move_in_date = request.POST.get('move_in_date')
        remarks = request.POST.get('remarks', '')
        force = request.POST.get('force') == 'true'
        
        user = get_object_or_404(User, id=user_id)
        room = get_object_or_404(Room, id=room_id, is_available=True)
        
        if RoomAllocation.objects.filter(student=user, status='ACTIVE').exists():
            return JsonResponse({'success': False, 'conflict': 'already_allocated', 'error': 'User already has an active room allocation.'})
        
        if room.current_occupancy >= room.capacity:
            return JsonResponse({'success': False, 'conflict': 'room_full', 'error': 'Room is full.'})

        user_gender = (getattr(user, 'gender', '') or '').strip().upper()
        hostel_gender = room.hostel.gender_restriction
        if not force and hostel_gender != 'ANY' and user_gender and user_gender != hostel_gender:
            return JsonResponse({
                'success': False,
                'conflict': 'gender_mismatch',
                'error': f'{room.hostel.name} is {room.hostel.get_gender_restriction_display()}, but this user is registered as {user_gender.title()}.'
            })
        
        allocation = RoomAllocation.objects.create(
            student=user,
            room=room,
            allocated_by=request.user,
            move_in_date=move_in_date,
            status='ACTIVE',
            remarks=remarks
        )
        
        room.current_occupancy += 1
        room.save()
        
        return JsonResponse({'success': True, 'message': f'Room {room.room_number} allocated to {user.full_name} successfully!'})
    
    from Admin.bela_admin.models import Department
    
    hostels = Hostel.objects.filter(status='ACTIVE')
    departments = Department.objects.filter(status='ACTIVE').order_by('department_name')
    
    context = {
        'user': request.user,
        'hostels': hostels,
        'departments': departments,
        'active_sb': 'allocate_room'
    }
    return render(request, 'Blaze_Hostel/allocate_room.html', context)


@login_required
def allocations_list(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        messages.error(request, "Permission denied.")
        return redirect("login")
    
    status_filter = request.GET.get('status', 'all')
    search = request.GET.get('search', '').strip()
    
    allocations = RoomAllocation.objects.select_related(
        'student', 'room', 'room__hostel', 'allocated_by'
    ).all()
    
    if status_filter != 'all':
        allocations = allocations.filter(status=status_filter.upper())
    
    if search:
        allocations = allocations.filter(
            Q(student__full_name__icontains=search) |
            Q(student__username__icontains=search) |
            Q(room__room_number__icontains=search) |
            Q(room__hostel__name__icontains=search)
        )
    
    paginator = Paginator(allocations, 15)
    page = request.GET.get('page')
    allocations_page = paginator.get_page(page)
    
    context = {
        'user': request.user,
        'allocations': allocations_page,
        'active_sb': 'allocations',
        'status_filter': status_filter,
        'search': search,
    }
    return render(request, 'Blaze_Hostel/allocations.html', context)


@login_required
def get_users_by_department_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    department_id = request.GET.get('department_id')
    user_type = request.GET.get('user_type', 'student')
    
    try:
        from Students.models import StudentProfile, FacultyProfile, StaffProfile
        from Admin.bela_admin.models import AcademicProgram
        from Admin.models import User
        
        users = User.objects.filter(account_status='ACTIVE')
        
        if user_type == 'student':
            if not department_id:
                return JsonResponse([], safe=False)
            
            # Get all students (even those without allocations)
            program_ids = AcademicProgram.objects.filter(
                department_id=department_id,
                status='ACTIVE'
            ).values_list('program_id', flat=True)
            
            print(f"Department ID: {department_id}")
            print(f"Program IDs found: {list(program_ids)}")
            
            if program_ids:
                student_ids = StudentProfile.objects.filter(
                    program_id__in=program_ids
                ).values_list('user_id', flat=True)
                print(f"Student IDs from profiles: {list(student_ids)}")
                
                if student_ids:
                    users = users.filter(id__in=student_ids)
                    print(f"Users before allocation filter: {users.count()}")
                else:
                    # Try to get students directly from User model with is_student=True
                    users = users.filter(is_student=True)
                    print(f"No student profiles found, using is_student flag: {users.count()}")
            else:
                # No programs found, try to get students from User model
                users = users.filter(is_student=True)
                print(f"No programs found, using is_student flag: {users.count()}")
        
        elif user_type == 'faculty':
            faculty_user_ids = list(FacultyProfile.objects.all().values_list('user_id', flat=True))
            faculty_flag_users = list(User.objects.filter(is_faculty=True).values_list('id', flat=True))
            all_faculty_ids = list(set(faculty_user_ids + faculty_flag_users))
            users = users.filter(id__in=all_faculty_ids)
            
        elif user_type == 'staff':
            staff_user_ids = list(StaffProfile.objects.all().values_list('user_id', flat=True))
            staff_flag_users = list(User.objects.filter(is_staff=True).values_list('id', flat=True))
            all_staff_ids = list(set(staff_user_ids + staff_flag_users))
            users = users.filter(id__in=all_staff_ids)
        
        else:
            return JsonResponse([], safe=False)
        
        # Exclude users with active allocations
        allocated_ids = RoomAllocation.objects.filter(status='ACTIVE').values_list('student_id', flat=True)
        users = users.exclude(id__in=allocated_ids)
        
        print(f"Final available {user_type} count: {users.count()}")
        
        data = []
        for user in users:
            role = 'student'
            if user.is_faculty:
                role = 'faculty'
            elif user.is_staff:
                role = 'staff'
            
            data.append({
                'id': user.id,
                'full_name': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username,
                'username': user.username,
                'email': user.email,
                'role': role
            })
        
        return JsonResponse(data, safe=False)
        
    except Exception as e:
        import logging
        logging.error(f"Error in get_users_by_department: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse([], safe=False)


@login_required
def get_user_details_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)
    
    user_id = request.GET.get('user_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'error': 'User ID required'})
    
    try:
        from Students.models import StudentProfile, FacultyProfile, StaffProfile, StudentAcademicProfile
        from Admin.bela_admin.models import AcademicProgram, Department
        
        try:
            user = User.objects.get(id=int(user_id))
        except (ValueError, TypeError):
            user = User.objects.get(username=user_id)
        
        user_data = {
            'id': user.id,
            'full_name': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'account_status': user.account_status,
            'mobile_number': getattr(user, 'mobile_number', 'N/A'),
            'gender': getattr(user, 'gender', 'N/A'),
            'date_of_birth': getattr(user, 'date_of_birth', None),
        }
        
        if user.is_student:
            try:
                profile = StudentProfile.objects.get(user=user)
                user_data['user_id'] = profile.student_number or 'N/A'
                user_data['role'] = 'student'
                
                try:
                    academic = StudentAcademicProfile.objects.get(student=profile)
                    if academic.department_id:
                        try:
                            dept = Department.objects.get(department_id=academic.department_id)
                            user_data['department_name'] = dept.department_name
                        except Department.DoesNotExist:
                            user_data['department_name'] = 'N/A'
                    else:
                        user_data['department_name'] = 'N/A'
                    
                    if academic.program_id:
                        try:
                            program = AcademicProgram.objects.get(program_id=academic.program_id)
                            user_data['program_name'] = program.program_name
                        except AcademicProgram.DoesNotExist:
                            user_data['program_name'] = 'N/A'
                    else:
                        user_data['program_name'] = 'N/A'
                except StudentAcademicProfile.DoesNotExist:
                    user_data['department_name'] = 'N/A'
                    user_data['program_name'] = 'N/A'
                    
            except StudentProfile.DoesNotExist:
                user_data['user_id'] = 'N/A'
                user_data['role'] = 'student'
                user_data['department_name'] = 'N/A'
                user_data['program_name'] = 'N/A'
        
        elif user.is_faculty:
            try:
                profile = FacultyProfile.objects.get(user=user)
                user_data['user_id'] = profile.faculty_id or 'N/A'
                user_data['role'] = 'faculty'
                if profile.department_id:
                    try:
                        dept = Department.objects.get(department_id=profile.department_id)
                        user_data['department_name'] = dept.department_name
                    except Department.DoesNotExist:
                        user_data['department_name'] = 'N/A'
                else:
                    user_data['department_name'] = 'N/A'
            except FacultyProfile.DoesNotExist:
                user_data['user_id'] = 'N/A'
                user_data['role'] = 'faculty'
                user_data['department_name'] = 'N/A'
        
        elif user.is_staff:
            try:
                profile = StaffProfile.objects.get(user=user)
                user_data['user_id'] = profile.staff_id or 'N/A'
                user_data['role'] = 'staff'
                if profile.department_id:
                    try:
                        dept = Department.objects.get(department_id=profile.department_id)
                        user_data['department_name'] = dept.department_name
                    except Department.DoesNotExist:
                        user_data['department_name'] = 'N/A'
                else:
                    user_data['department_name'] = 'N/A'
            except StaffProfile.DoesNotExist:
                user_data['user_id'] = 'N/A'
                user_data['role'] = 'staff'
                user_data['department_name'] = 'N/A'
        else:
            user_data['role'] = 'user'
            user_data['department_name'] = 'N/A'
        
        current_allocation = RoomAllocation.objects.filter(
            student=user, 
            status='ACTIVE'
        ).select_related('room', 'room__hostel').first()
        
        if current_allocation:
            user_data['current_allocation'] = {
                'room_number': current_allocation.room.room_number,
                'hostel_name': current_allocation.room.hostel.name,
                'allocated_date': current_allocation.allocated_date.strftime('%d %b %Y'),
                'move_in_date': current_allocation.move_in_date.strftime('%d %b %Y') if current_allocation.move_in_date else 'N/A',
                'status': current_allocation.status
            }
        else:
            user_data['current_allocation'] = None
        
        return JsonResponse({'success': True, 'user': user_data})
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': f'User not found: {user_id}'})
    except Exception as e:
        import logging
        logging.error(f"Error in get_user_details: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_students_by_department_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    department_id = request.GET.get('department_id')
    
    if not department_id:
        return JsonResponse([], safe=False)
    
    try:
        from Students.models import StudentProfile
        from Admin.bela_admin.models import AcademicProgram
        from Admin.models import User
        
        program_ids = AcademicProgram.objects.filter(
            department_id=department_id,
            status='ACTIVE'
        ).values_list('program_id', flat=True)
        
        if not program_ids:
            return JsonResponse([], safe=False)
        
        student_ids = StudentProfile.objects.filter(
            program_id__in=program_ids
        ).values_list('user_id', flat=True)
        
        students = User.objects.filter(
            id__in=student_ids,
            is_student=True,
            account_status='ACTIVE'
        ).exclude(
            id__in=RoomAllocation.objects.filter(status='ACTIVE').values_list('student_id', flat=True)
        )
        
        data = []
        for student in students:
            try:
                profile = StudentProfile.objects.get(user=student)
                student_number = profile.student_number or 'N/A'
            except StudentProfile.DoesNotExist:
                student_number = 'N/A'
            
            data.append({
                'id': student.id,
                'full_name': f"{student.first_name or ''} {student.last_name or ''}".strip() or student.username,
                'username': student.username,
                'email': student.email,
                'student_number': student_number
            })
        
        return JsonResponse(data, safe=False)
        
    except Exception as e:
        return JsonResponse([], safe=False)


@login_required
def get_student_details_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)
    
    student_id = request.GET.get('student_id')
    
    if not student_id:
        return JsonResponse({'success': False, 'error': 'Student ID required'})
    
    try:
        from Students.models import StudentProfile, StudentAcademicProfile
        from Admin.bela_admin.models import AcademicProgram, Department
        
        try:
            student = User.objects.get(id=int(student_id), is_student=True)
        except (ValueError, TypeError):
            student = User.objects.get(username=student_id, is_student=True)
        
        student_data = {
            'id': student.id,
            'full_name': f"{student.first_name or ''} {student.last_name or ''}".strip() or student.username,
            'username': student.username,
            'email': student.email,
            'first_name': student.first_name or '',
            'last_name': student.last_name or '',
            'account_status': student.account_status,
            'mobile_number': getattr(student, 'mobile_number', 'N/A'),
            'gender': getattr(student, 'gender', 'N/A'),
            'date_of_birth': getattr(student, 'date_of_birth', None),
        }
        
        try:
            profile = StudentProfile.objects.get(user=student)
            student_data['student_number'] = profile.student_number or 'N/A'
            student_data['preferred_name'] = profile.preferred_name or 'N/A'
            student_data['university_email'] = profile.university_email or 'N/A'
            student_data['personal_email'] = profile.personal_email or 'N/A'
            student_data['citizenship_status'] = profile.citizenship_status or 'N/A'
            student_data['marital_status'] = profile.marital_status or 'N/A'
            student_data['academic_level'] = profile.academic_level or 'N/A'
            student_data['current_status'] = profile.current_status or 'N/A'
            student_data['cumulative_gpa'] = str(profile.cumulative_gpa) if profile.cumulative_gpa else 'N/A'
            
            try:
                academic = StudentAcademicProfile.objects.get(student=profile)
                student_data['major'] = academic.major or 'N/A'
                student_data['minor'] = academic.minor or 'N/A'
                student_data['concentration'] = academic.concentration or 'N/A'
                student_data['catalog_year'] = academic.catalog_year or 'N/A'
                
                if academic.department_id:
                    try:
                        dept = Department.objects.get(department_id=academic.department_id)
                        student_data['department_name'] = dept.department_name
                    except Department.DoesNotExist:
                        student_data['department_name'] = 'N/A'
                else:
                    student_data['department_name'] = 'N/A'
                
                if academic.program_id:
                    try:
                        program = AcademicProgram.objects.get(program_id=academic.program_id)
                        student_data['program_name'] = program.program_name
                    except AcademicProgram.DoesNotExist:
                        student_data['program_name'] = 'N/A'
                else:
                    student_data['program_name'] = 'N/A'
                    
            except StudentAcademicProfile.DoesNotExist:
                student_data['department_name'] = 'N/A'
                student_data['program_name'] = 'N/A'
                
        except StudentProfile.DoesNotExist:
            student_data['student_number'] = 'N/A'
            student_data['preferred_name'] = 'N/A'
            student_data['university_email'] = 'N/A'
            student_data['personal_email'] = 'N/A'
        
        current_allocation = RoomAllocation.objects.filter(
            student=student, 
            status='ACTIVE'
        ).select_related('room', 'room__hostel').first()
        
        if current_allocation:
            student_data['current_allocation'] = {
                'room_number': current_allocation.room.room_number,
                'hostel_name': current_allocation.room.hostel.name,
                'allocated_date': current_allocation.allocated_date.strftime('%d %b %Y'),
                'move_in_date': current_allocation.move_in_date.strftime('%d %b %Y') if current_allocation.move_in_date else 'N/A',
                'status': current_allocation.status
            }
        else:
            student_data['current_allocation'] = None
        
        return JsonResponse({'success': True, 'student': student_data})
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': f'Student not found: {student_id}'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def hostel_rooms_map_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    hostel_id = request.GET.get('hostel_id')
    if not hostel_id:
        return JsonResponse([], safe=False)

    rooms = Room.objects.filter(hostel_id=hostel_id).select_related('hostel').order_by('floor', 'room_number')

    data = []
    for room in rooms:
        occupants = RoomAllocation.objects.filter(room=room, status='ACTIVE').select_related('student')
        data.append({
            'id': room.id,
            'room_number': room.room_number,
            'floor': room.floor,
            'capacity': room.capacity,
            'current_occupancy': room.current_occupancy,
            'status': room.status,
            'status_display': room.get_status_display(),
            'rent_per_month': str(room.rent_per_month),
            'image_url': room.image.url if room.image else '',
            'occupants': [
                {
                    'allocation_id': a.id,
                    'student_id': a.student.id,
                    'name': a.student.full_name,
                    'move_in_date': a.move_in_date.strftime('%d %b %Y') if a.move_in_date else '',
                }
                for a in occupants
            ],
        })

    return JsonResponse(data, safe=False)


@login_required
def unallocated_users_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    user_type = request.GET.get('user_type', 'all')
    search = request.GET.get('search', '').strip()

    users = User.objects.filter(account_status='ACTIVE').exclude(
        id__in=RoomAllocation.objects.filter(status='ACTIVE').values_list('student_id', flat=True)
    )

    if user_type == 'student':
        users = users.filter(is_student=True)
    elif user_type == 'faculty':
        users = users.filter(is_faculty=True)
    elif user_type == 'staff':
        users = users.filter(is_staff=True)

    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(username__icontains=search)
        )

    data = []
    for u in users[:200]:
        role = 'student'
        if u.is_faculty:
            role = 'faculty'
        elif u.is_staff:
            role = 'staff'
        
        data.append({
            'id': u.id,
            'full_name': u.full_name,
            'username': u.username,
            'gender': (getattr(u, 'gender', '') or '').strip().upper(),
            'role': role
        })
    
    return JsonResponse(data, safe=False)


@login_required
def unallocated_students_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    search = request.GET.get('search', '').strip()

    students = User.objects.filter(
        is_student=True,
        account_status='ACTIVE'
    ).exclude(
        id__in=RoomAllocation.objects.filter(status='ACTIVE').values_list('student_id', flat=True)
    )

    if search:
        students = students.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(username__icontains=search)
        )

    data = [
        {
            'id': s.id,
            'full_name': s.full_name,
            'username': s.username,
            'gender': (getattr(s, 'gender', '') or '').strip().upper(),
        }
        for s in students[:200]
    ]
    return JsonResponse(data, safe=False)


@login_required
def get_available_rooms_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    hostel_id = request.GET.get('hostel_id')
    
    if not hostel_id:
        return JsonResponse([], safe=False)
    
    try:
        hostel_id = int(hostel_id)
        
        rooms = Room.objects.filter(
            hostel_id=hostel_id,
            status='AVAILABLE'
        ).exclude(
            status='OCCUPIED'
        ).values(
            'id', 'room_number', 'capacity', 'current_occupancy', 
            'rent_per_month', 'status'
        )
        
        room_list = []
        for room in rooms:
            available_slots = room['capacity'] - room['current_occupancy']
            if available_slots > 0:
                room_list.append({
                    'id': room['id'],
                    'room_number': room['room_number'],
                    'capacity': room['capacity'],
                    'current_occupancy': room['current_occupancy'],
                    'available_slots': available_slots,
                    'rent_per_month': float(room['rent_per_month']) if room['rent_per_month'] else 0,
                    'status': room['status']
                })
        
        return JsonResponse(room_list, safe=False)
        
    except ValueError:
        return JsonResponse([], safe=False)
    except Exception as e:
        import logging
        logging.error(f"Error loading rooms: {e}")
        return JsonResponse([], safe=False)


@login_required
@require_http_methods(["POST"])
def bulk_allocate_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})

    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})

    room_id = request.POST.get('room_id')
    move_in_date = request.POST.get('move_in_date')
    remarks = request.POST.get('remarks', '')
    force = request.POST.get('force') == 'true'
    user_ids = request.POST.getlist('user_ids[]') or request.POST.getlist('user_ids')

    if not room_id or not move_in_date or not user_ids:
        return JsonResponse({'success': False, 'error': 'room_id, move_in_date and at least one user are required'})

    room = get_object_or_404(Room, id=room_id)

    available_slots = room.capacity - room.current_occupancy
    if len(user_ids) > available_slots:
        return JsonResponse({
            'success': False,
            'error': f'Only {available_slots} slot(s) left in Room {room.room_number}, but {len(user_ids)} users were selected.'
        })

    results = []
    allocated_count = 0

    for uid in user_ids:
        try:
            user = User.objects.get(id=uid)
        except User.DoesNotExist:
            results.append({'user_id': uid, 'success': False, 'error': 'User not found'})
            continue

        if RoomAllocation.objects.filter(student=user, status='ACTIVE').exists():
            results.append({'user_id': uid, 'name': user.full_name, 'success': False, 'error': 'Already allocated'})
            continue

        user_gender = (getattr(user, 'gender', '') or '').strip().upper()
        hostel_gender = room.hostel.gender_restriction
        if not force and hostel_gender != 'ANY' and user_gender and user_gender != hostel_gender:
            results.append({'user_id': uid, 'name': user.full_name, 'success': False, 'error': 'Gender/hostel eligibility mismatch'})
            continue

        if room.current_occupancy >= room.capacity:
            results.append({'user_id': uid, 'name': user.full_name, 'success': False, 'error': 'Room became full'})
            continue

        RoomAllocation.objects.create(
            student=user,
            room=room,
            allocated_by=request.user,
            move_in_date=move_in_date,
            status='ACTIVE',
            remarks=remarks
        )
        room.current_occupancy += 1
        room.save()
        allocated_count += 1
        results.append({'user_id': uid, 'name': user.full_name, 'success': True})

    return JsonResponse({
        'success': allocated_count > 0,
        'allocated_count': allocated_count,
        'total_requested': len(user_ids),
        'results': results,
        'message': f'{allocated_count} of {len(user_ids)} user(s) allocated to Room {room.room_number}.'
    })


@login_required
@require_http_methods(["POST"])
def check_allocation_conflict_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    user_id = request.POST.get('user_id')
    room_id = request.POST.get('room_id')

    if not user_id or not room_id:
        return JsonResponse({'success': False, 'error': 'user_id and room_id are required'})

    user = get_object_or_404(User, id=user_id)
    room = get_object_or_404(Room, id=room_id)

    already_allocated = RoomAllocation.objects.filter(student=user, status='ACTIVE').exists()
    room_full = room.current_occupancy >= room.capacity

    user_gender = (getattr(user, 'gender', '') or '').strip().upper()
    hostel_gender = room.hostel.gender_restriction
    gender_mismatch = bool(hostel_gender != 'ANY' and user_gender and user_gender != hostel_gender)

    return JsonResponse({
        'success': True,
        'already_allocated': already_allocated,
        'room_full': room_full,
        'gender_mismatch': gender_mismatch,
        'hostel_gender_display': room.hostel.get_gender_restriction_display(),
        'user_gender': user_gender.title() if user_gender else 'Not set',
        'has_conflict': already_allocated or room_full or gender_mismatch,
        'blocking': already_allocated or room_full,
    })


@login_required
@require_http_methods(["POST"])
def check_in_json(request, uuid, allocation_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    allocation = get_object_or_404(RoomAllocation, id=allocation_id)
    
    if allocation.status != 'PENDING':
        return JsonResponse({'success': False, 'error': 'Allocation is not pending'})
    
    allocation.status = 'ACTIVE'
    allocation.move_in_date = timezone.now().date()
    allocation.save()
    
    HostelAuditLog.objects.create(
        user=request.user,
        action='UPDATE',
        module='ROOM_ALLOCATION',
        object_type='RoomAllocation',
        object_id=allocation.id,
        changes={'status': 'ACTIVE', 'action': 'CHECK_IN'}
    )
    
    return JsonResponse({'success': True, 'message': 'User checked in successfully'})


@login_required
@require_http_methods(["POST"])
def check_out_json(request, uuid, allocation_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    allocation = get_object_or_404(RoomAllocation, id=allocation_id)
    
    try:
        data = json.loads(request.body)
        reason = data.get('reason', 'Completed stay')
    except:
        reason = 'Completed stay'
    
    if allocation.status != 'ACTIVE':
        return JsonResponse({'success': False, 'error': 'Allocation is not active'})
    
    allocation.status = 'COMPLETED'
    allocation.move_out_date = timezone.now().date()
    allocation.remarks = (allocation.remarks or '') + f'\nCheck-out reason: {reason}'
    allocation.save()
    
    room = allocation.room
    room.current_occupancy = max(0, room.current_occupancy - 1)
    room.save()
    
    HostelAuditLog.objects.create(
        user=request.user,
        action='UPDATE',
        module='ROOM_ALLOCATION',
        object_type='RoomAllocation',
        object_id=allocation.id,
        changes={'status': 'COMPLETED', 'action': 'CHECK_OUT', 'reason': reason}
    )
    
    return JsonResponse({'success': True, 'message': 'User checked out successfully'})


@login_required
@require_http_methods(["POST"])
def bulk_check_in_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        data = json.loads(request.body)
        user_ids = data.get('user_ids', [])
    except:
        return JsonResponse({'success': False, 'error': 'Invalid data'})
    
    checked_in = 0
    errors = []
    
    for user_id in user_ids:
        allocation = RoomAllocation.objects.filter(
            student_id=user_id,
            status='PENDING'
        ).first()
        
        if allocation:
            allocation.status = 'ACTIVE'
            allocation.move_in_date = timezone.now().date()
            allocation.save()
            checked_in += 1
        else:
            errors.append(f'User ID {user_id} has no pending allocation')
    
    return JsonResponse({
        'success': True,
        'checked_in': checked_in,
        'errors': errors if errors else None,
        'message': f'{checked_in} user(s) checked in successfully'
    })


@login_required
def allocation_details_json(request, uuid, allocation_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    allocation = get_object_or_404(
        RoomAllocation.objects.select_related('student', 'room', 'room__hostel', 'allocated_by'),
        id=allocation_id
    )
    
    data = {
        'success': True,
        'allocation': {
            'id': allocation.id,
            'user_name': allocation.student.full_name,
            'user_id': allocation.student.id,
            'room_number': allocation.room.room_number,
            'room_id': allocation.room.id,
            'hostel_name': allocation.room.hostel.name,
            'move_in_date': allocation.move_in_date.strftime('%Y-%m-%d') if allocation.move_in_date else None,
            'move_out_date': allocation.move_out_date.strftime('%Y-%m-%d') if allocation.move_out_date else None,
            'status': allocation.status.lower(),
            'status_display': allocation.get_status_display(),
            'allocated_by': allocation.allocated_by.full_name if allocation.allocated_by else 'System',
            'remarks': allocation.remarks or '',
            'allocated_date': allocation.allocated_date.strftime('%d %b %Y, %I:%M %p')
        }
    }
    
    return JsonResponse(data)


@login_required
def get_allocations_by_room_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    room_id = request.GET.get('room_id')
    if not room_id:
        return JsonResponse([], safe=False)
    
    allocations = RoomAllocation.objects.filter(
        room_id=room_id
    ).select_related('student').order_by('-allocated_date')
    
    data = []
    for alloc in allocations:
        data.append({
            'id': alloc.id,
            'user_name': alloc.student.full_name,
            'user_id': alloc.student.id,
            'move_in_date': alloc.move_in_date.strftime('%d %b %Y') if alloc.move_in_date else None,
            'move_out_date': alloc.move_out_date.strftime('%d %b %Y') if alloc.move_out_date else None,
            'status': alloc.status,
            'status_display': alloc.get_status_display()
        })
    
    return JsonResponse(data, safe=False)


@login_required
def allocated_users_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    user_type = request.GET.get('user_type', 'all')
    search = request.GET.get('search', '').strip()

    allocations = RoomAllocation.objects.filter(status='ACTIVE').select_related('student', 'room', 'room__hostel')

    if user_type == 'student':
        allocations = allocations.filter(student__is_student=True)
    elif user_type == 'faculty':
        allocations = allocations.filter(student__is_faculty=True)
    elif user_type == 'staff':
        allocations = allocations.filter(student__is_staff=True)

    if search:
        allocations = allocations.filter(
            Q(student__first_name__icontains=search) |
            Q(student__last_name__icontains=search) |
            Q(student__username__icontains=search) |
            Q(room__room_number__icontains=search)
        )

    data = []
    for a in allocations[:200]:
        role = 'student'
        if a.student.is_faculty:
            role = 'faculty'
        elif a.student.is_staff:
            role = 'staff'
        
        data.append({
            'user_id': a.student.id,
            'full_name': a.student.full_name,
            'username': a.student.username,
            'role': role,
            'current_room_id': a.room.id,
            'current_room_number': a.room.room_number,
            'current_hostel_name': a.room.hostel.name,
            'move_in_date': a.move_in_date.strftime('%d %b %Y') if a.move_in_date else '',
        })
    
    return JsonResponse(data, safe=False)


@login_required
def allocated_students_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    search = request.GET.get('search', '').strip()

    allocations = RoomAllocation.objects.filter(status='ACTIVE').select_related('student', 'room', 'room__hostel')

    if search:
        allocations = allocations.filter(
            Q(student__first_name__icontains=search) |
            Q(student__last_name__icontains=search) |
            Q(student__username__icontains=search) |
            Q(room__room_number__icontains=search)
        )

    data = [
        {
            'student_id': a.student.id,
            'full_name': a.student.full_name,
            'username': a.student.username,
            'current_room_id': a.room.id,
            'current_room_number': a.room.room_number,
            'current_hostel_name': a.room.hostel.name,
            'move_in_date': a.move_in_date.strftime('%d %b %Y') if a.move_in_date else '',
        }
        for a in allocations[:200]
    ]
    return JsonResponse(data, safe=False)


@login_required
@require_http_methods(["POST"])
def transfer_user_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})

    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})

    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    user_id = data.get('user_id')
    new_room_id = data.get('new_room_id')
    transfer_date = data.get('transfer_date')
    remarks = data.get('remarks', '')
    force = data.get('force') == 'true' if data.get('force') else False

    if not user_id or not new_room_id or not transfer_date:
        return JsonResponse({'success': False, 'error': 'user_id, new_room_id and transfer_date are required'})

    user = get_object_or_404(User, id=user_id)
    new_room = get_object_or_404(Room, id=new_room_id)

    current_allocation = RoomAllocation.objects.filter(student=user, status='ACTIVE').select_related('room').first()
    if not current_allocation:
        return JsonResponse({'success': False, 'error': 'This user has no active allocation to transfer from.'})

    if current_allocation.room_id == new_room.id:
        return JsonResponse({'success': False, 'error': 'User is already in this room.'})

    if new_room.current_occupancy >= new_room.capacity:
        return JsonResponse({'success': False, 'conflict': 'room_full', 'error': f'Room {new_room.room_number} is full.'})

    user_gender = (getattr(user, 'gender', '') or '').strip().upper()
    hostel_gender = new_room.hostel.gender_restriction
    if not force and hostel_gender != 'ANY' and user_gender and user_gender != hostel_gender:
        return JsonResponse({
            'success': False,
            'conflict': 'gender_mismatch',
            'error': f'{new_room.hostel.name} is {new_room.hostel.get_gender_restriction_display()}, but this user is registered as {user_gender.title()}.'
        })

    old_room = current_allocation.room

    current_allocation.status = 'COMPLETED'
    current_allocation.move_out_date = transfer_date
    current_allocation.remarks = (current_allocation.remarks or '') + f'\n[Transferred to {new_room.hostel.name} - Room {new_room.room_number} on {transfer_date}]'
    current_allocation.save()

    old_room.current_occupancy = max(0, old_room.current_occupancy - 1)
    old_room.save()

    RoomAllocation.objects.create(
        student=user,
        room=new_room,
        allocated_by=request.user,
        move_in_date=transfer_date,
        status='ACTIVE',
        remarks=remarks or f'Transferred from {old_room.hostel.name} - Room {old_room.room_number}'
    )
    new_room.current_occupancy += 1
    new_room.save()

    HostelAuditLog.objects.create(
        user=request.user,
        action='MOVE',
        module='ROOM_ALLOCATION',
        object_type='RoomAllocation',
        object_id=current_allocation.id,
        changes={
            'user': user.full_name,
            'from_room': old_room.room_number,
            'from_hostel': old_room.hostel.name,
            'to_room': new_room.room_number,
            'to_hostel': new_room.hostel.name,
            'transfer_date': transfer_date
        }
    )

    return JsonResponse({
        'success': True,
        'message': f'{user.full_name} transferred from Room {old_room.room_number} to Room {new_room.room_number}.'
    })


@login_required
@require_http_methods(["POST"])
def transfer_student_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})

    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})

    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    student_id = data.get('student_id')
    new_room_id = data.get('new_room_id')
    transfer_date = data.get('transfer_date')
    remarks = data.get('remarks', '')
    force = data.get('force') == 'true' if data.get('force') else False

    if not student_id or not new_room_id or not transfer_date:
        return JsonResponse({'success': False, 'error': 'student_id, new_room_id and transfer_date are required'})

    student = get_object_or_404(User, id=student_id, is_student=True)
    new_room = get_object_or_404(Room, id=new_room_id)

    current_allocation = RoomAllocation.objects.filter(student=student, status='ACTIVE').select_related('room').first()
    if not current_allocation:
        return JsonResponse({'success': False, 'error': 'This student has no active allocation to transfer from.'})

    if current_allocation.room_id == new_room.id:
        return JsonResponse({'success': False, 'error': 'Student is already in this room.'})

    if new_room.current_occupancy >= new_room.capacity:
        return JsonResponse({'success': False, 'conflict': 'room_full', 'error': f'Room {new_room.room_number} is full.'})

    student_gender = (getattr(student, 'gender', '') or '').strip().upper()
    hostel_gender = new_room.hostel.gender_restriction
    if not force and hostel_gender != 'ANY' and student_gender and student_gender != hostel_gender:
        return JsonResponse({
            'success': False,
            'conflict': 'gender_mismatch',
            'error': f'{new_room.hostel.name} is {new_room.hostel.get_gender_restriction_display()}, but this student is registered as {student_gender.title()}.'
        })

    old_room = current_allocation.room

    current_allocation.status = 'COMPLETED'
    current_allocation.move_out_date = transfer_date
    current_allocation.remarks = (current_allocation.remarks or '') + f'\n[Transferred to {new_room.hostel.name} - Room {new_room.room_number} on {transfer_date}]'
    current_allocation.save()

    old_room.current_occupancy = max(0, old_room.current_occupancy - 1)
    old_room.save()

    RoomAllocation.objects.create(
        student=student,
        room=new_room,
        allocated_by=request.user,
        move_in_date=transfer_date,
        status='ACTIVE',
        remarks=remarks or f'Transferred from {old_room.hostel.name} - Room {old_room.room_number}'
    )
    new_room.current_occupancy += 1
    new_room.save()

    HostelAuditLog.objects.create(
        user=request.user,
        action='MOVE',
        module='ROOM_ALLOCATION',
        object_type='RoomAllocation',
        object_id=current_allocation.id,
        changes={
            'student': student.full_name,
            'from_room': old_room.room_number,
            'from_hostel': old_room.hostel.name,
            'to_room': new_room.room_number,
            'to_hostel': new_room.hostel.name,
            'transfer_date': transfer_date
        }
    )

    return JsonResponse({
        'success': True,
        'message': f'{student.full_name} transferred from Room {old_room.room_number} to Room {new_room.room_number}.'
    })


@login_required
@require_http_methods(["POST"])
def update_allocation_json(request, uuid, allocation_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    allocation = get_object_or_404(RoomAllocation, id=allocation_id)
    
    status = request.POST.get('status')
    move_in_date = request.POST.get('move_in_date')
    move_out_date = request.POST.get('move_out_date')
    remarks = request.POST.get('remarks', '')
    
    if not status:
        return JsonResponse({'success': False, 'error': 'Status is required'})
    
    try:
        allocation.status = status
        
        if move_in_date:
            allocation.move_in_date = move_in_date
        
        if move_out_date:
            allocation.move_out_date = move_out_date
        
        allocation.remarks = remarks
        allocation.save()
        
        room = allocation.room
        active_allocations = RoomAllocation.objects.filter(room=room, status='ACTIVE').count()
        room.current_occupancy = active_allocations
        room.save()
        
        HostelAuditLog.objects.create(
            user=request.user,
            action='UPDATE',
            module='ROOM_ALLOCATION',
            object_type='RoomAllocation',
            object_id=allocation.id,
            changes={
                'status': status,
                'move_in_date': move_in_date,
                'move_out_date': move_out_date
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Allocation updated successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def delete_allocation_json(request, uuid, allocation_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    allocation = get_object_or_404(RoomAllocation, id=allocation_id)
    
    try:
        if allocation.status == 'ACTIVE':
            room = allocation.room
            room.current_occupancy = max(0, room.current_occupancy - 1)
            room.save()
        
        HostelAuditLog.objects.create(
            user=request.user,
            action='DELETE',
            module='ROOM_ALLOCATION',
            object_type='RoomAllocation',
            object_id=allocation.id,
            changes={
                'user': allocation.student.full_name,
                'room': allocation.room.room_number,
                'hostel': allocation.room.hostel.name,
                'status': allocation.status
            }
        )
        
        allocation.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Allocation deleted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# Housing Applications and Maintenance
from Students.models import MaintenanceRequest, RoomInspection


@login_required
def admin_housing_dashboard(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        messages.error(request, "Permission denied.")
        return redirect("login")
    
    # total_applications = HousingApplication.objects.count()
    # pending_applications = HousingApplication.objects.filter(status='PENDING').count()
    # under_review_applications = HousingApplication.objects.filter(status='UNDER_REVIEW').count()
    # approved_applications = HousingApplication.objects.filter(status='APPROVED').count()
    # allocated_applications = HousingApplication.objects.filter(status='ALLOCATED').count()
    # rejected_applications = HousingApplication.objects.filter(status='REJECTED').count()
    
    total_maintenance = MaintenanceRequest.objects.count()
    pending_maintenance = MaintenanceRequest.objects.filter(status='PENDING').count()
    in_progress_maintenance = MaintenanceRequest.objects.filter(status='IN_PROGRESS').count()
    completed_maintenance = MaintenanceRequest.objects.filter(status='COMPLETED').count()
    emergency_maintenance = MaintenanceRequest.objects.filter(priority='EMERGENCY', status__in=['PENDING', 'IN_PROGRESS']).count()
    
    total_inspections = RoomInspection.objects.count()
    pending_inspections = RoomInspection.objects.filter(status='PENDING').count()
    
    # recent_applications = HousingApplication.objects.select_related('student', 'preferred_hostel').order_by('-application_date')[:10]
    recent_maintenance = MaintenanceRequest.objects.select_related('student', 'room', 'room__hostel').order_by('-created_at')[:10]
    
    context = {
        'user': request.user,
        # 'total_applications': total_applications,
        # 'pending_applications': pending_applications,
        # 'under_review_applications': under_review_applications,
        # 'approved_applications': approved_applications,
        # 'allocated_applications': allocated_applications,
        # 'rejected_applications': rejected_applications,
        'total_maintenance': total_maintenance,
        'pending_maintenance': pending_maintenance,
        'in_progress_maintenance': in_progress_maintenance,
        'completed_maintenance': completed_maintenance,
        'emergency_maintenance': emergency_maintenance,
        'total_inspections': total_inspections,
        'pending_inspections': pending_inspections,
        # 'recent_applications': recent_applications,
        'recent_maintenance': recent_maintenance,
        'active_sb': 'housing_dashboard'
    }
    return render(request, 'Blaze_Hostel/housing_dashboard.html', context)


# @login_required
# def admin_housing_applications(request, uuid):
#     if str(request.user.uuid) != str(uuid):
#         return redirect("login")
    
#     if not (request.user.is_admin or request.user.is_hostel_admin):
#         messages.error(request, "Permission denied.")
#         return redirect("login")
    
#     status_filter = request.GET.get('status', 'all')
#     search = request.GET.get('search', '').strip()
    
#     applications = HousingApplication.objects.select_related('student', 'preferred_hostel', 'reviewed_by').all()
    
#     if status_filter != 'all':
#         applications = applications.filter(status=status_filter.upper())
    
#     if search:
#         applications = applications.filter(
#             Q(student__full_name__icontains=search) |
#             Q(student__username__icontains=search) |
#             Q(student__email__icontains=search)
#         )
    
#     paginator = Paginator(applications, 20)
#     page = request.GET.get('page')
#     applications_page = paginator.get_page(page)
    
#     hostels = Hostel.objects.filter(status='ACTIVE')
    
#     context = {
#         'user': request.user,
#         'applications': applications_page,
#         'hostels': hostels,
#         'status_filter': status_filter,
#         'search': search,
#         'active_sb': 'housing_applications'
#     }
#     return render(request, 'Blaze_Hostel/housing_applications.html', context)


# @login_required
# @require_http_methods(["POST"])
# def admin_update_application(request, uuid, application_id):
#     if str(request.user.uuid) != str(uuid):
#         return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
#     if not (request.user.is_admin or request.user.is_hostel_admin):
#         return JsonResponse({'success': False, 'error': 'Permission denied'})
    
#     application = get_object_or_404(HousingApplication, id=application_id)
    
#     status = request.POST.get('status')
#     notes = request.POST.get('notes', '')
#     allocate_room = request.POST.get('allocate_room') == 'true'
#     room_id = request.POST.get('room_id')
    
#     if not status:
#         return JsonResponse({'success': False, 'error': 'Status is required'})
    
#     try:
#         application.status = status
#         application.reviewed_by = request.user
#         application.reviewed_date = timezone.now()
        
#         if notes:
#             application.admin_notes = (application.admin_notes or '') + f'\n[{timezone.now().date()}] {notes}'
        
#         application.save()
        
#         if status == 'ALLOCATED' and allocate_room and room_id:
#             try:
#                 room = Room.objects.get(id=room_id)
                
#                 if room.current_occupancy >= room.capacity:
#                     return JsonResponse({
#                         'success': False,
#                         'error': f'Room {room.room_number} is full (Capacity: {room.capacity})'
#                     })
                
#                 if RoomAllocation.objects.filter(student=application.student, status='ACTIVE').exists():
#                     return JsonResponse({
#                         'success': False,
#                         'error': 'Student already has an active allocation'
#                     })
                
#                 allocation = RoomAllocation.objects.create(
#                     student=application.student,
#                     room=room,
#                     allocated_by=request.user,
#                     move_in_date=timezone.now().date(),
#                     status='ACTIVE',
#                     remarks=f'Allocated from housing application #{application.id}'
#                 )
                
#                 room.current_occupancy += 1
#                 room.save()
                
#                 HostelAuditLog.objects.create(
#                     user=request.user,
#                     action='ALLOCATE',
#                     module='HOUSING',
#                     object_type='RoomAllocation',
#                     object_id=allocation.id,
#                     changes={
#                         'student': application.student.full_name,
#                         'room': room.room_number,
#                         'hostel': room.hostel.name,
#                         'application_id': application.id
#                     }
#                 )
                
#             except Room.DoesNotExist:
#                 return JsonResponse({'success': False, 'error': 'Room not found'})
        
#         HostelAuditLog.objects.create(
#             user=request.user,
#             action='UPDATE',
#             module='HOUSING',
#             object_type='HousingApplication',
#             object_id=application.id,
#             changes={'status': status, 'notes': notes}
#         )
        
#         return JsonResponse({
#             'success': True,
#             'message': f'Application updated to {application.get_status_display()}'
#         })
        
#     except Exception as e:
#         return JsonResponse({'success': False, 'error': str(e)})


# @login_required
# def admin_application_detail(request, uuid, application_id):
#     if str(request.user.uuid) != str(uuid):
#         return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
#     if not (request.user.is_admin or request.user.is_hostel_admin):
#         return JsonResponse({'success': False, 'error': 'Permission denied'})
    
#     application = get_object_or_404(
#         HousingApplication.objects.select_related('student', 'preferred_hostel', 'reviewed_by'),
#         id=application_id
#     )
    
#     data = {
#         'success': True,
#         'application': {
#             'id': application.id,
#             'student_name': application.student.full_name,
#             'student_email': application.student.email,
#             'student_username': application.student.username,
#             'preferred_hostel': application.preferred_hostel.name if application.preferred_hostel else 'No preference',
#             'preferred_room_type': application.get_preferred_room_type_display(),
#             'preferred_floor': application.preferred_floor or 'No preference',
#             'gender': application.get_gender_display(),
#             'year_of_study': application.get_year_of_study_display(),
#             'special_needs': application.special_needs or 'None',
#             'dietary_preferences': application.dietary_preferences or 'None',
#             'medical_conditions': application.medical_conditions or 'None',
#             'roommate_preference': application.roommate_preference or 'None',
#             'roommate_gender_preference': application.roommate_gender_preference or 'No preference',
#             'roommate_study_habits': application.roommate_study_habits or 'None',
#             'hobbies_interests': application.hobbies_interests or 'None',
#             'sleep_schedule': application.sleep_schedule or 'None',
#             'smoking_preference': 'Non-smoker' if application.smoking_preference else 'Smoker',
#             'pet_preference': 'No pets' if application.pet_preference else 'Has pets',
#             'status': application.status,
#             'status_display': application.get_status_display(),
#             'application_date': application.application_date.strftime('%d %b %Y, %I:%M %p'),
#             'admin_notes': application.admin_notes or '',
#             'reviewed_by': application.reviewed_by.full_name if application.reviewed_by else 'Not reviewed',
#             'reviewed_date': application.reviewed_date.strftime('%d %b %Y') if application.reviewed_date else 'Not reviewed'
#         }
#     }
    
#     return JsonResponse(data)

from Students.models import MaintenanceRequest  

@login_required
def admin_maintenance_requests(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        messages.error(request, "Permission denied.")
        return redirect("login")
    
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    search = request.GET.get('search', '').strip()
    
    from Students.models import MaintenanceRequest
    
    requests = MaintenanceRequest.objects.select_related('student', 'room', 'room__hostel', 'assigned_to').all()
    
    if status_filter != 'all':
        requests = requests.filter(status=status_filter.upper())
    
    if priority_filter != 'all':
        requests = requests.filter(priority=priority_filter.upper())
    
    if search:
        requests = requests.filter(
            Q(student__full_name__icontains=search) |
            Q(room__room_number__icontains=search) |
            Q(issue_type__icontains=search) |
            Q(description__icontains=search)
        )
    
    from django.core.paginator import Paginator
    paginator = Paginator(requests, 20)
    page = request.GET.get('page')
    requests_page = paginator.get_page(page)
    
    staff_users = User.objects.filter(is_staff=True)
    
    context = {
        'user': request.user,
        'requests': requests_page,
        'staff_users': staff_users,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search': search,
        'active_sb': 'maintenance_requests'
    }
    return render(request, 'Blaze_Hostel/maintenance_requests.html', context)


@login_required
@require_http_methods(["POST"])
def admin_update_maintenance(request, uuid, request_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    from Students.models import MaintenanceRequest
    
    req = get_object_or_404(MaintenanceRequest, id=request_id)
    
    status = request.POST.get('status')
    assigned_to_id = request.POST.get('assigned_to')
    resolution_notes = request.POST.get('resolution_notes', '')
    
    if not status:
        return JsonResponse({'success': False, 'error': 'Status is required'})
    
    try:
        req.status = status
        
        if assigned_to_id:
            req.assigned_to_id = assigned_to_id
        
        if resolution_notes:
            req.resolution_notes = (req.resolution_notes or '') + f'\n[{timezone.now().date()}] {resolution_notes}'
        
        if status == 'COMPLETED':
            req.completed_date = timezone.now()
        
        req.save()
        
        HostelAuditLog.objects.create(
            user=request.user,
            action='UPDATE',
            module='MAINTENANCE',
            object_type='MaintenanceRequest',
            object_id=req.id,
            changes={'status': status}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Maintenance request updated to {req.get_status_display()}'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

#<-----------------Blaze code End(29.08.26)---------------->




























#<-----------------Blaze App Start(23.09.26)---------------->



########################## kali code  #################################

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserCreateForm
from Admin.models import User,UserRole, Firearm,OlympicAthlete,OlympicPerformance
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from Admin.audit import AuditLogger
from PermissionAccess.decorators import require_permission, require_page_access
from Admin.models import UserAuditLog
from collections import Counter
from datetime import timedelta
from datetime import timedelta, datetime
import re
from Students.models import StudentProfile
from Staff.models import StaffProfile
from Students.views import save_student_details, suggested_student_number_for_context
from Faculty.views import save_faculty_details, suggested_faculty_id_for_context
from Staff.views import save_staff_details, suggested_staff_id_for_context
from Students.models import StudentProfile         
from Faculty.models import FacultyProfile,FacultyEducation         
from Staff.models import StaffProfile
from Admin.bela_admin.models import Department, Course 
from django.utils.timesince import timesince
from django.db.models import Count, Q
from django.db import transaction
from django.db.utils import IntegrityError
from Admin.Jack.models import Athletic, Sport, SportTeamModel, Coach, SportClub, SportsFacility
from Admin.models import Tournament, TournamentInvitation, TournamentParticipant, TournamentApplication
from django.db.models import Sum
from calendar import month_abbr 
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.validators import validate_email
from django.conf import settings
from decimal import Decimal, InvalidOperation
from email.mime.image import MIMEImage
import os
import re
import logging
from Staff.utils import notify_faculty_new_tournament_invitation
import random
from django.contrib.auth.hashers import make_password, check_password
from Admin.Colleges.models import School
from Admin.ws_utils import broadcast_invitation_status, broadcast_participant_added
from Admin.bela_admin.models import Room


logger = logging.getLogger(__name__)

from Admin.Colleges.models import (
    University,
    School,
    Degree,
    AcademicProgram,
)
from Admin.Jack.models import Coach


@require_page_access("user_page")
@login_required
def user_page(request):
    return render(request, "user_page.html") 


 

ROLE_COLORS = ["red", "blue", "purple", "green", "amber", "gray"]


def _role_color_map():
    """Map each UserRole id -> a color, in a stable order (by role_name)."""
    ids = list(UserRole.objects.order_by("role_name").values_list("id", flat=True))
    return {rid: ROLE_COLORS[i % len(ROLE_COLORS)] for i, rid in enumerate(ids)}

@require_page_access("role")
@login_required
def role(request):
    roles = UserRole.objects.all().order_by("role_name")
    color_map = _role_color_map()

    total_roles = roles.count()
    total_users = User.objects.count()
    active_users = User.objects.filter(account_status="ACTIVE").count()
    unassigned_users = User.objects.filter(role__isnull=True).count() 

    now = timezone.now()
    roles_this_month = roles.filter(
        created_at__year=now.year, created_at__month=now.month
    ).count()
    users_this_month = User.objects.filter(
        created_at__year=now.year, created_at__month=now.month
    ).count()

    active_pct = round((active_users / total_users * 100), 1) if total_users else 0
    unassigned_pct = round((unassigned_users / total_users * 100), 1) if total_users else 0

    role_pills = []
    for r in roles:
        role_pills.append({
            "id": r.id,
            "name": r.role_name,
            "count": r.users.count(),
            "color": color_map.get(r.id, "gray"),
        })

    context = {
        "roles": roles,
        "role_pills": role_pills,
        "total_roles": total_roles,
        "total_users": total_users,
        "active_users": active_users,
        "unassigned_users": unassigned_users,
        "active_pct": active_pct,
        "unassigned_pct": unassigned_pct,
        "roles_this_month": roles_this_month,
        "users_this_month": users_this_month,
    }
    return render(request, "role.html", context)


@login_required
@require_http_methods(["GET"])
def role_assignments_json(request):
    try:
        page = int(request.GET.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(request.GET.get("page_size", 10))
    except (TypeError, ValueError):
        page_size = 10

    role_id = request.GET.get("role", "").strip()
    search = request.GET.get("search", "").strip()

    users = User.objects.select_related("role").all().order_by("-created_at")

    if role_id:
        users = users.filter(role_id=role_id)

    if search:
        users = users.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(username__icontains=search)
            | Q(email__icontains=search)
            | Q(university_id__icontains=search)
            | Q(role__role_name__icontains=search)
        )

    total = users.count()
    paginator = Paginator(users, page_size)
    page_obj = paginator.get_page(page)

    color_map = _role_color_map()

   
    STATUS_MAP = {
        "ACTIVE": "active",
        "INACTIVE": "inactive",
        "PENDING": "pending",
        "SUSPENDED": "inactive",
    }

    data = []
    for u in page_obj:
        full_name = f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username
        data.append({
            "id": u.id,
            "name": full_name,
            "email": u.email,
            "uid": u.university_id or "—",
            "role": u.role.role_name if u.role else "Unassigned",
            "role_id": u.role_id,
            "role_color": color_map.get(u.role_id, "gray"),
            "status": STATUS_MAP.get(u.account_status, "inactive"),
            "assigned": u.updated_at.strftime("%Y-%m-%d") if u.updated_at else "",
        })

    return JsonResponse({
        "results": data,
        "total": total,
        "page": page_obj.number,
        "total_pages": paginator.num_pages,
        "page_size": page_size,
    })

@require_permission("userrole_create")
@login_required
@require_http_methods(["POST"])  
def role_create_json(request):
    """Create a new UserRole from the Add Role modal."""
    name = (request.POST.get("role_name") or "").strip()
    description = (request.POST.get("description") or "").strip()
    user_type = (request.POST.get("user_type") or "").strip() 

    if not name:
        return JsonResponse(
            {"ok": False, "errors": {"role_name": ["Role name is required."]}},
            status=400,
        )
    if len(name) > 100:
        return JsonResponse(
            {"ok": False, "errors": {"role_name": ["Role name must be 100 characters or fewer."]}},
            status=400,
        )
    if UserRole.objects.filter(role_name__iexact=name).exists():
        return JsonResponse(
            {"ok": False, "errors": {"role_name": ["A role with this name already exists."]}},
            status=400,
        )
   

    role_obj = UserRole.objects.create(role_name=name, description=description,user_type= user_type)

    AuditLogger.log(
        request=request,
        action="CREATE",
        module="RoleManagement",
        object_type="UserRole",
        object_id=role_obj.id,
        description=f"Created role '{role_obj.role_name}'.",
        after_data={"role_name": role_obj.role_name, "description": role_obj.description, "user_type": role_obj.user_type},
        status="SUCCESS",
    )

    return JsonResponse({
        "ok": True,
        "role": {
            "id": role_obj.id,
            "name": role_obj.role_name,
            "description": role_obj.description or "",
            "count": 0,
        },
    })

@require_permission("userrole_update")
@login_required
@require_http_methods(["POST"])
def role_unassign_json(request, uid):
    """Remove the role from a single user (used by the row-level delete action)."""
    user_obj = get_object_or_404(User, id=uid)
    before = AuditLogger.model_to_dict(user_obj, ["role"])
    user_obj.role = None
    user_obj.save(update_fields=["role"])
    AuditLogger.log(
        request=request,
        action="ROLE_REMOVE",
        module="RoleManagement",
        object_type="User",
        object_id=user_obj.id,
        description=f"Removed role from user '{user_obj.username}'.",
        before_data=before,
        after_data={"role": None},
        status="SUCCESS",
    )
    return JsonResponse({"ok": True})

# ************************************************ Arun Code **********************************************************

@login_required
@require_http_methods(["GET"])
def check_field_unique_json(request):
    """
    GET /dashboard/users/check-unique/?field=username&value=facultytest
    GET /dashboard/users/check-unique/?field=university_email&value=x@wisc.edu
    Optional &exclude_id=<user id> when editing, so a user's own existing
    value doesn't flag itself as a duplicate.
    """
    field = request.GET.get("field", "").strip()
    value = request.GET.get("value", "").strip()
    exclude_id = request.GET.get("exclude_id", "").strip()

    if not value:
        return JsonResponse({"taken": False})

    FIELD_MAP = {
        "username":       (User, "username", True),
        # Jack Code Start's
        "ssn_number":     (User, "ssn_number", True),
        # Jack Code End's
        "email":          (User, "email", True),
        "university_id":  (User, "university_id", True),
        "mobile_number":  (User, "mobile_number", True),

        # Student
        "student_number":    (StudentProfile, "student_number", False),
        "university_email":  (StudentProfile, "university_email", False),

        "faculty_employee_id": (FacultyProfile, "employee_id", False),
        "faculty_email":        (FacultyProfile, "email", False),

        # Staff
        "staff_employee_id":  (StaffProfile, "employee_id", False),
        "staff_work_email":    (StaffProfile, "work_email", False),
    }

    mapping = FIELD_MAP.get(field)
    if not mapping:
        return JsonResponse({"taken": False})

    Model, column, is_user_model = mapping

    qs = Model.objects.filter(**{column: value})
    if exclude_id:
        if is_user_model:
            qs = qs.exclude(pk=exclude_id)
        else:
            qs = qs.exclude(user_id=exclude_id)

    return JsonResponse({"taken": qs.exists()})


from django.http import JsonResponse

@login_required
def get_schools(request):
    university_id = request.GET.get("university_id")

    schools = School.objects.filter(
        university_id=university_id,
        status="ACTIVE"
    ).order_by("school_name")

    return JsonResponse([
        {
            "id": str(s.school_id),
            "name": s.school_name,
        }
        for s in schools
    ], safe=False)

from Admin.bela_admin.models import Department

@login_required
def get_departments(request):
    school_id = request.GET.get("school_id")

    departments = Department.objects.filter(
        school_id=school_id,
        status="ACTIVE"
    ).order_by("department_name")

    data = [
        {
            "id": department.department_id,
            "name": department.department_name,
        }
        for department in departments
    ]

    return JsonResponse(data, safe=False)

@login_required
def get_schools(request):

    university_id = request.GET.get("university_id")

    schools = School.objects.filter(
        university_id=university_id,
        status="ACTIVE"
    ).order_by("school_name")

    data = [
        {
            "id": str(school.school_id),
            "name": school.school_name,
        }
        for school in schools
    ]

    return JsonResponse(data, safe=False)

@login_required
def get_degrees(request):

    degrees = Degree.objects.filter(
        status="ACTIVE"
    ).order_by("degree_name")

    return JsonResponse([
        {
            "id": d.degree_id,
            "name": d.degree_name,
        }
        for d in degrees
    ], safe=False)

@login_required
def get_programs(request):

    department_id = request.GET.get("department_id")
    degree_id = request.GET.get("degree_id")

    programs = AcademicProgram.objects.filter(
        department_id=department_id,
        degree_id=degree_id,
        status="ACTIVE"
    ).order_by("program_name")

    return JsonResponse([
        {
            "id": p.program_id,
            "name": p.program_name,
        }
        for p in programs
    ], safe=False)

from django.core.exceptions import ValidationError
from django.db import transaction

# Admin/views.py - Complete fixed user_create

@require_page_access("user_create_page")
# @require_page_access("user_create_page", user_types=["admin"])
@require_permission("user_create")
@login_required
def user_create(request):
    roles = UserRole.objects.all().order_by("role_name").exclude(role_name="Administrator")

    universities = University.objects.filter(status="ACTIVE").order_by("university_name")
    degrees = Degree.objects.filter(status="ACTIVE").order_by("degree_name")
    departments = Department.objects.filter(status="ACTIVE").order_by("department_name")
    courses = Course.objects.filter(status="ACTIVE").select_related("department").order_by("course_name")

    if request.method == "POST":
        form = UserCreateForm(request.POST, request.FILES)
        if form.is_valid():
            user_type = request.POST.get("user_type")
            
            # Debug print
            print(f"👤 User Type: {user_type}")
            print(f"📌 Department ID from form: {request.POST.get('department_id')}")

            try:
                with transaction.atomic():
                    user, password = form.save()

                    user.is_student = False
                    user.is_faculty = False
                    user.is_admin = False
                    user.is_staff = False

                    is_hostel_admin = request.POST.get("is_hostel_admin") == "yes"

                    if is_hostel_admin:
                        user.is_hostel_admin = True
                        user.is_staff = True

                    if user_type == "student":
                        user.is_student = True
                        user.save()
                        save_student_details(request, user)

                        
                        from Students.models import StudentProfile
                        from Admin.bela_admin.models import AcademicProgram
                        
                        department_id = request.POST.get("department_id")
                        
                        if department_id:
                            # Find program in this department
                            program = AcademicProgram.objects.filter(
                                department_id=department_id,
                                status='ACTIVE'
                            ).first()
                            
                            if program:
                                # Get or create StudentProfile
                                profile, created = StudentProfile.objects.get_or_create(user=user)
                                profile.program_id = program.program_id
                                profile.save()
                                print(f" Assigned {user.full_name} to {program.program_name}")
                            else:
                                print(f" No program found for department {department_id}")
                        else:
                            print(" No department selected, assigning default program")
                            default_program = AcademicProgram.objects.filter(
                                department_id=1,
                                status='ACTIVE'
                            ).first()
                            if default_program:
                                profile, created = StudentProfile.objects.get_or_create(user=user)
                                profile.program_id = default_program.program_id
                                profile.save()
                                print(f" Assigned {user.full_name} to default: {default_program.program_name}")

                    elif user_type == "faculty":
                        user.is_faculty = True
                        user.save()
                        save_faculty_details(request, user)

                    elif user_type == "staff":
                        user.is_staff = True
                        user.save()
                        save_staff_details(request, user)

                    elif user_type == "admin":
                        user.is_admin = True
                        user.save()

                    user.save()
                    has_firearm = request.POST.get("has_firearm") == "yes"
                    if has_firearm:
                        save_firearm_details(request, user)

                AuditLogger.log(
                    request=request,
                    action="CREATE",
                    module="UserManagement",
                    object_type="User",
                    object_id=user.id,
                    description=f"Created user '{user.username}'.",
                    after_data=AuditLogger.model_to_dict(
                        user, ["username", "email", "first_name", "last_name", "role"]
                    ),
                    status="SUCCESS",
                )

                return render(request, "user_create.html", {
                    "form": UserCreateForm(),
                    "roles": roles,
                    "success": True,
                    "new_username": user.username,
                    "new_password": password,
                })

            except ValidationError as e:
                error_messages = e.messages if hasattr(e, "messages") else [str(e)]
                for msg in error_messages:
                    form.add_error(None, msg)

                print("STUDENT/FACULTY/STAFF DETAIL VALIDATION FAILED:")
                for msg in error_messages:
                    print(f"  - {msg}")

        else:
            print("FORM IS INVALID. Errors:")
            for field, errors in form.errors.items():
                print(f"  - {field}: {errors}")
    else:
        form = UserCreateForm()

    return render(request, "user_create.html", {
        "form": form,
        "roles": roles,
        "departments": departments,
        "universities": universities,
        "degrees": degrees,
        "courses": courses,
        "suggested_student_number": suggested_student_number_for_context(),
        "suggested_faculty_employee_id": suggested_faculty_id_for_context(),
        "suggested_staff_employee_id": suggested_staff_id_for_context(),
        "student_number_prefix": "STU",
        "existing_staff": StaffProfile.objects.select_related("user").order_by("employee_id"),
    })

# ************************************************ Arun Code **********************************************************

@login_required
def users_json(request):

    # users = User.objects.all()
    users = User.objects.exclude(
        is_superuser=True
    ).exclude(
        is_super_admin=True
    )
    data = []

    for u in users:

        if u.is_admin:
            user_type = "admin"
        elif u.is_faculty:
            user_type = "faculty"
        elif u.is_staff:
            user_type = "staff"
        elif u.is_student:
            user_type = "student"
        else:
            user_type = ""

        data.append({
            "id": u.id,
            "uuid": str(u.uuid), 
            "username": u.username,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "full_name": f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username,
            "email": u.email,
            "university_id": u.university_id,
            "gender": u.gender,
            "account_status": u.account_status,
            "created_at": u.created_at.strftime('%d %b %Y %I:%M %p') if u.created_at else '',
            "is_student": u.is_student,
            "is_faculty": u.is_faculty,
            "is_admin": u.is_admin,
            "is_staff": u.is_staff,
            "role": user_type,
            "profile_photo": (
                u.profile_photo.url if u.profile_photo else ""
            ),
        })

    return JsonResponse({"users": data})



#### swetha's code #####
@require_permission("user_update")
@login_required
def user_edit(request, user_id):
    user_obj = get_object_or_404(User, uuid=user_id)

    student = StudentProfile.objects.filter(user=user_obj).first()

    faculty = FacultyProfile.objects.filter(user=user_obj).first()
    staff = StaffProfile.objects.filter(user=user_obj).first()
    
    position = StaffPosition.objects.filter(staff=staff).first() if staff else None
  

    if student:
        user_type = "student"
    elif faculty:
        user_type = "faculty"
    elif staff:
        user_type = "staff"
    elif user_obj.is_admin:
        user_type = "admin"
    else:
        user_type = "user"

    context = {
        "user_obj": user_obj,
        "student": student,
        "faculty": faculty,
        "staff": staff,
        "position":position,
        "user_type": user_type,
        "user_initial": user_obj.first_name[:1].upper() if user_obj.first_name else "U",
       
        # choices
        "gender_choices": User.GENDER_CHOICES,
        "account_status_choices": User.STATUS_CHOICES,
        "employment_status_choices": FacultyProfile.EMPLOYMENT_STATUS_CHOICES,
        "citizenship_choices": StudentProfile.CITIZENSHIP_CHOICES,
        "marital_choices": StudentProfile.MARITAL_STATUS_CHOICES,
        "student_status_choices": StudentProfile.STATUS_CHOICES,
        "academic_level_choices": StudentProfile.ACADEMIC_LEVEL_CHOICES,
        "current_status_choices": StudentProfile.STATUS_CHOICES,

        "student_address_type_choices": StudentAddress.ADDRESS_TYPE_CHOICES,
        "address_type_choices": StaffAddress.ADDRESS_TYPE_CHOICES,
        "document_type_choices": StaffDocument.DOCUMENT_TYPE_CHOICES,
        "employment_type_choices": StaffProfile.EMPLOYMENT_TYPE_CHOICES,
        "position_status_choices": StaffPosition.POSITION_STATUS_CHOICES,


        # dropdowns
        "role_options": UserRole.objects.all(),
        "university_options": University.objects.all(),
        "department_options": Department.objects.all(),
         "degree_options": Degree.objects.all(),
        "advisor_options": FacultyProfile.objects.all(),
        "school_options": School.objects.all(),
        "program_options": AcademicProgram.objects.all(),

        "faculty_rank_options": FacultyRank.objects.all(),
    }

    if staff:
        context["supervisor_options"] = StaffProfile.objects.exclude(
            pk=staff.pk
        ).select_related("user")
    return render(request, "user__edit.html", context)

@login_required
def user_update(request, user_id):
    user_obj = get_object_or_404(User, uuid=user_id)

    if request.method == "POST":

        user_obj.first_name = request.POST.get("first_name")
        user_obj.middle_name = request.POST.get("middle_name")
        user_obj.last_name = request.POST.get("last_name")
        # user_obj.username = request.POST.get("username")
        user_obj.email = request.POST.get("email")
        user_obj.mobile_number = request.POST.get("mobile_number")
        user_obj.gender = request.POST.get("gender")
        user_obj.date_of_birth = request.POST.get("date_of_birth") or None
        user_obj.account_status = request.POST.get("account_status")
        user_obj.is_super_admin = "is_super_admin" in request.POST
        user_obj.is_full_crud = "is_full_crud" in request.POST


        user_obj.email_verified = "email_verified" in request.POST
        user_obj.mobile_verified = "mobile_verified" in request.POST

        role = request.POST.get("admin-role_id")
        if role:
            user_obj.role_id = role
        else:
            user_obj.role = None

        # if request.FILES.get("profile_photo"):
        #     user_obj.profile_photo = request.FILES["profile_photo"]

        profile_photo = request.FILES.get("profile_photo")

        if profile_photo:
            allowed = [
                "image/jpeg",
                "image/png",
                "image/jpg",
                "image/webp"
            ]

            if profile_photo.content_type not in allowed:
                messages.error(
                    request,
                    "Only JPG, PNG and WEBP images are allowed."
                )
                return redirect("user_edit", user_obj.uuid)

            user_obj.profile_photo = profile_photo
        user_obj.save()


        # ---------------- Student ----------------

        student = StudentProfile.objects.filter(user=user_obj).first()

        if student:
            student.preferred_name = request.POST.get("student-preferred_name")
            student.university_email = request.POST.get("student-university_email")
            student.personal_email = request.POST.get("student-personal_email")
            student.citizenship_status = (request.POST.get("student-citizenship_status") or student.citizenship_status)
            student.marital_status = (request.POST.get("student-marital_status") or student.marital_status)
            student.academic_level = (request.POST.get("student-academic_level") or student.academic_level)
            student.current_status = (request.POST.get("student-current_status") or student.current_status)
            student.cumulative_gpa = request.POST.get("student-cumulative_gpa") or None
            student.admission_date = request.POST.get("student-admission_date") or student.admission_date
            student.expected_graduation_date = request.POST.get("student-expected_graduation_date") or student.expected_graduation_date
            student.save()

            # ---------------- Student Academic Profile ----------------

            academic, created = StudentAcademicProfile.objects.get_or_create(
                student=student
            )

            academic.university_id = request.POST.get("academic-university_id") or None
            academic.school_id = request.POST.get("academic-school_id") or None
            academic.department_id = request.POST.get("academic-department_id") or None
            academic.degree_id = request.POST.get("academic-degree_id") or None
            academic.program_id = request.POST.get("academic-program_id") or None

            academic.major = request.POST.get("academic-major")
            academic.minor = request.POST.get("academic-minor")
            academic.concentration = request.POST.get("academic-concentration")
            academic.catalog_year = request.POST.get("academic-catalog_year") 
            academic.advisor_id = request.POST.get("academic-advisor_id") or None

            academic.save()

            # Student Addresses
            address_ids = request.POST.getlist("student-address_id[]")
            address_types = request.POST.getlist("student-address_type[]")
            line1s = request.POST.getlist("student-address_line_1[]")
            line2s = request.POST.getlist("student-address_line_2[]")
            cities = request.POST.getlist("student-city[]")
            states = request.POST.getlist("student-state[]")
            postal_codes = request.POST.getlist("student-postal_code[]")
            countries = request.POST.getlist("student-country[]")

            existing_addresses = list(student.addresses.all())
            saved_address_ids = []

            for i in range(len(address_types)):

                if i < len(address_ids) and address_ids[i].strip():
                  address = StudentAddress.objects.filter(id=address_ids[i],student=student).first()
                else:
                    address = StudentAddress(student=student)
                
                if not address:
                    address = StudentAddress(student=student)

                address.address_type = address_types[i]
                address.address_line_1 = line1s[i] if i < len(line1s) else ""
                address.address_line_2 = line2s[i] if i < len(line2s) else ""
                address.city = cities[i] if i < len(cities) else ""
                address.state = states[i] if i < len(states) else ""
                address.postal_code = postal_codes[i] if i < len(postal_codes) else ""
                address.country = countries[i] if i < len(countries) else ""

                address.save()
                saved_address_ids.append(address.id)

            StudentAddress.objects.filter(
                student=student
            ).exclude(
                id__in=saved_address_ids
            ).delete()

            # Student Emergency Contacts
            contact_ids = request.POST.getlist("student-emergency_id[]")
            names = request.POST.getlist("student-emergency_name[]")
            relationships = request.POST.getlist("student-emergency_relationship[]")
            phones = request.POST.getlist("student-emergency_phone[]")
            emails = request.POST.getlist("student-emergency_email[]")
            priorities = request.POST.getlist("student-emergency_priority[]")

            # existing_contacts = list(student.emergency_contacts.all())
            saved_contact_ids = []

            for i in range(len(names)):

                if not names[i].strip():
                    continue

                if i < len(contact_ids) and contact_ids[i].strip():
                    contact = StudentEmergencyContact.objects.filter(
                        id=contact_ids[i],
                        student=student
                    ).first()
                else:
                    contact = StudentEmergencyContact(student=student)

                if not contact:
                    contact = StudentEmergencyContact(student=student)
            
                contact.contact_name = names[i]
                contact.relationship = relationships[i] if i < len(relationships) else ""
                contact.phone_number = phones[i] if i < len(phones) else ""
                contact.email = emails[i] if i < len(emails) else ""
                contact.priority = (priorities[i] if i < len(priorities) and priorities[i] else 1 )

                contact.save()
                saved_contact_ids.append(contact.id)

            StudentEmergencyContact.objects.filter(student=student ).exclude(  id__in=saved_contact_ids).delete()

        # ---------------- Faculty ----------------

        faculty = FacultyProfile.objects.filter(user=user_obj).first()

        if faculty:
            existing_ids = []
            faculty.preferred_name = request.POST.get("faculty-preferred_name")
            faculty.email = request.POST.get("faculty-email")
            faculty.phone = request.POST.get("faculty-phone")
            faculty.office_location = request.POST.get("faculty-office_location")
            faculty.department_id = request.POST.get("faculty-department_id") or None
            faculty.faculty_rank_id = request.POST.get("faculty-faculty_rank_id") or None
            faculty.hire_date = request.POST.get("faculty-hire_date") or None
            faculty.employment_status = (request.POST.get("faculty-employment_status") or faculty.employment_status)
            faculty.employment_status = (request.POST.get("faculty-employment_status")or faculty.employment_status)
            faculty.biography = request.POST.get("faculty-biography")
            faculty.save()
            # ---------------- Faculty Education ----------------

            education_ids = request.POST.getlist("education_id")
            degrees = request.POST.getlist("education_degree")
            fields = request.POST.getlist("education_field")
            institutions = request.POST.getlist("education_institution")
            years = request.POST.getlist("education_year")

            

            for i in range(len(degrees)):
                degree = degrees[i].strip()
                if not degree:
                    continue
                edu = None
                if i < len(education_ids) and education_ids[i]:
                    edu = FacultyEducation.objects.filter(id=education_ids[i],faculty=faculty).first()

                if not edu:
                     edu = FacultyEducation(faculty=faculty)

                edu.degree = degree
                edu.field_of_study = fields[i] if i < len(fields) else ""
                edu.institution_name = institutions[i] if i < len(institutions) else ""
                # edu.graduation_year = years[i] or None
                year = years[i].strip() if i < len(years) else ""

                if not year:
                    edu.graduation_year = None
                elif not year.isdigit():
                    messages.error(request, "Graduation year must contain only numbers.")
                    return redirect("user_edit", user_obj.uuid)
                elif len(year) != 4:
                    messages.error(request, "Graduation year must be exactly 4 digits.")
                    return redirect("user_edit", user_obj.uuid)
                else:
                    edu.graduation_year = int(year)

                edu.save()

                existing_ids.append(edu.id)

            # Delete removed education records
            FacultyEducation.objects.filter(faculty=faculty).exclude(id__in=existing_ids).delete()

        # ---------------- Staff ----------------

        staff = StaffProfile.objects.filter(user=user_obj).first()

        if staff:

            # Staff Profile
            staff.preferred_name = request.POST.get("staff-preferred_name")
            staff.work_email = request.POST.get("staff-work_email")
            staff.personal_email = request.POST.get("staff-personal_email")
            staff.office_phone = request.POST.get("staff-office_phone")
            staff.hire_date = request.POST.get("staff-hire_date") or None
            staff.employment_status = request.POST.get("staff-employment_status")
            staff.employment_type = request.POST.get("staff-employment_type")
            staff.supervisor_id = request.POST.get("staff-supervisor") or None
          
            staff.save()

            # Position
            position = StaffPosition.objects.filter(staff=staff).first()

            if position:
                position.job_title = (
                    request.POST.get("staff-job_title")
                    or position.job_title
                )
                position.department_id = (
                    request.POST.get("staff-department_id")
                    or position.department_id
                )
                position.unit_id = (
                    request.POST.get("staff-unit_id")
                    or position.unit_id
                )
                position.position_start_date = (
                    request.POST.get("staff-position_start_date")
                    or position.position_start_date
                )
                position.position_status = (
                    request.POST.get("staff-position_status")
                    or position.position_status
                )
               
                position.save()

            # Addresses
            address_types = request.POST.getlist("staff-address_type[]")
            line1s = request.POST.getlist("staff-address_line_1[]")
            line2s = request.POST.getlist("staff-address_line_2[]")
            cities = request.POST.getlist("staff-city[]")
            states = request.POST.getlist("staff-state[]")
            postal_codes = request.POST.getlist("staff-postal_code[]")
            countries = request.POST.getlist("staff-country[]")

            existing_addresses = list(staff.addresses.all())
            saved_address_ids = []

            for i in range(len(address_types)):

                if i < len(existing_addresses):
                    address = existing_addresses[i]
                else:
                    address = StaffAddress(staff=staff)

                address.address_type = address_types[i]
                address.address_line_1 = line1s[i] if i < len(line1s) else ""
                address.address_line_2 = line2s[i] if i < len(line2s) else ""
                address.city = cities[i] if i < len(cities) else ""
                address.state = states[i] if i < len(states) else ""
                address.postal_code = postal_codes[i] if i < len(postal_codes) else ""
                address.country = countries[i] if i < len(countries) else ""

                address.save()
                saved_address_ids.append(address.id)

            StaffAddress.objects.filter(
                staff=staff
            ).exclude(
                id__in=saved_address_ids
            ).delete()

            # ---------------------------------------------------
            # Emergency Contacts
            # ---------------------------------------------------

            names = request.POST.getlist("staff-emergency_name[]")
            relationships = request.POST.getlist("staff-emergency_relationship[]")
            phones = request.POST.getlist("staff-emergency_phone[]")
            emails = request.POST.getlist("staff-emergency_email[]")
            priorities = request.POST.getlist("staff-emergency_priority[]")

            existing_contacts = list(staff.emergency_contacts.all())
            saved_contact_ids = []

            for i in range(len(names)):

                if not names[i].strip():
                    continue

                if i < len(existing_contacts):
                    contact = existing_contacts[i]
                else:
                    contact = StaffEmergencyContact(staff=staff)

                contact.contact_name = names[i]
                contact.relationship = (
                    relationships[i]
                    if i < len(relationships)
                    else ""
                )
                contact.phone_number = (
                    phones[i]
                    if i < len(phones)
                    else ""
                )
                contact.email = (
                    emails[i]
                    if i < len(emails)
                    else ""
                )
                contact.priority = (
                    priorities[i]
                    if i < len(priorities) and priorities[i]
                    else 1
                )

                contact.save()
                saved_contact_ids.append(contact.id)

            StaffEmergencyContact.objects.filter(
                staff=staff
            ).exclude(
                id__in=saved_contact_ids
            ).delete()

            # ---------------------------------------------------
    # Staff Education
    # ---------------------------------------------------

        education_ids = request.POST.getlist("staff-education_id[]")
        degrees = request.POST.getlist("staff-degree[]")
        institutions = request.POST.getlist("staff-institution_name[]")
        fields = request.POST.getlist("staff-field_of_study[]")
        years = request.POST.getlist("staff-graduation_year[]")

        saved_ids = []

        for i in range(len(degrees)):

            if not degrees[i].strip():
                continue

            edu = None

            if i < len(education_ids) and education_ids[i].strip():
                edu = StaffEducation.objects.filter(
                    id=education_ids[i],
                    staff=staff
                ).first()

            if not edu:
                edu = StaffEducation(staff=staff)

            edu.degree = degrees[i]
            edu.institution_name = institutions[i] if i < len(institutions) else ""
            edu.field_of_study = fields[i] if i < len(fields) else ""

            year = years[i].strip() if i < len(years) else ""

            if not year:
                edu.graduation_year = None
            elif not year.isdigit():
                messages.error(request, "Graduation year must contain only numbers.")
                return redirect("user_edit", user_obj.uuid)
            elif len(year) != 4:
                messages.error(request, "Graduation year must be exactly 4 digits.")
                return redirect("user_edit", user_obj.uuid)
            else:
                edu.graduation_year = int(year)

            edu.save()
            saved_ids.append(edu.id)

        StaffEducation.objects.filter(
            staff=staff
        ).exclude(
            id__in=saved_ids
        ).delete()


        # ---------------------------------------------------
        # Staff Certifications
        # ---------------------------------------------------

        cert_ids = request.POST.getlist("staff-certification_id[]")
        cert_names = request.POST.getlist("staff-certification_name[]")
        orgs = request.POST.getlist("staff-issuing_organization[]")
        issue_dates = request.POST.getlist("staff-issue_date[]")
        expiry_dates = request.POST.getlist("staff-expiration_date[]")

        saved_ids = []

        for i in range(len(cert_names)):

            if not cert_names[i].strip():
                continue

            cert = None

            if i < len(cert_ids) and cert_ids[i].strip():
                cert = StaffCertification.objects.filter(
                    id=cert_ids[i],
                    staff=staff
                ).first()

            if not cert:
                cert = StaffCertification(staff=staff)

            cert.certification_name = cert_names[i]
            cert.issuing_organization = orgs[i] if i < len(orgs) else ""
            cert.issue_date = issue_dates[i] or None
            cert.expiration_date = expiry_dates[i] or None

            cert.save()
            saved_ids.append(cert.id)

        StaffCertification.objects.filter(
            staff=staff
        ).exclude(
            id__in=saved_ids
        ).delete()


        # ---------------------------------------------------
        # Staff Documents
        # ---------------------------------------------------
        print("DOC IDS :", request.POST.getlist("staff-document_id[]"))
        print("DOC TYPES :", request.POST.getlist("staff-document_type[]"))
        print("DOC NAMES :", request.POST.getlist("staff-file_name[]"))
        print("FILES :", request.FILES.getlist("staff-new-file[]"))

        doc_ids = request.POST.getlist("staff-document_id[]")
        doc_types = request.POST.getlist("staff-document_type[]")
        file_names = request.POST.getlist("staff-file_name[]")
        # files = request.FILES.getlist("staff-file[]")
        # existing replace
        new_files = request.FILES.getlist("staff-new-file[]")

        saved_doc_ids = []

        for i in range(len(doc_types)):

            doc = None

            # Existing document
            if i < len(doc_ids) and doc_ids[i].strip():

                doc = StaffDocument.objects.filter(
                    id=doc_ids[i],
                    staff=staff
                ).first()

            if doc:

                doc.document_type = doc_types[i]
                doc.file_name = file_names[i] if i < len(file_names) else doc.file_name

                # Replace file only if new uploaded
                if i < len(new_files) and new_files[i]:
                    doc.file = new_files[i]

                doc.verification_status = "PENDING"
                doc.save()

                saved_doc_ids.append(doc.id)

            else:

                # New document
                uploaded_file = new_files[i] if i < len(new_files) else None

                if uploaded_file:

                    new_doc = StaffDocument.objects.create(
                        staff=staff,
                        document_type=doc_types[i],
                        file_name=file_names[i] if i < len(file_names) and file_names[i] else uploaded_file.name,
                        file=uploaded_file,
                        verification_status="PENDING"
                    )

                    saved_doc_ids.append(new_doc.id)

        # Delete removed documents

        StaffDocument.objects.filter(
            staff=staff
        ).exclude(
            id__in=saved_doc_ids
        ).delete()
                    

        # if staff:
        #     staff.preferred_name = request.POST.get("staff-preferred_name")
        #     staff.work_email = request.POST.get("staff-work_email")
        #     staff.personal_email = request.POST.get("staff-personal_email")
        #     staff.office_phone = request.POST.get("staff-office_phone")
        #     staff.hire_date = request.POST.get("staff-hire_date") or None
        #     staff.employment_status = request.POST.get("staff-employment_status")
        #     staff.employment_type = request.POST.get("staff-employment_type")
        #     staff.supervisor_id = request.POST.get("staff-supervisor_id") or None
        #     staff.save()
        #     position = StaffPosition.objects.filter(staff=staff).first()

        #     if position:
        #         position.job_title = request.POST.get("staff-job_title") or position.job_title
        #         # position.school_id = request.POST.get("staff-school") or position.school_id
        #         position.department_id = request.POST.get("staff-department_id") or position.department_id
        #         position.unit_id = request.POST.get("staff-unit_id") or position.unit_id
        #         position.position_start_date = request.POST.get("staff-position_start_date") or position.position_start_date 
        #         position.position_status = request.POST.get("staff-position_status") or position.position_status
        #         position.save()

        #         address_types = request.POST.getlist("staff-address_type[]")
        #         line1s = request.POST.getlist("staff-address_line_1[]")
        #         line2s = request.POST.getlist("staff-address_line_2[]")
        #         cities = request.POST.getlist("staff-city[]")
        #         states = request.POST.getlist("staff-state[]")
        #         postal_codes = request.POST.getlist("staff-postal_code[]")
        #         countries = request.POST.getlist("staff-country[]")

        #         existing_addresses = list(staff.addresses.all())

        #         for i in range(len(address_types)):

        #             if i < len(existing_addresses):
        #                 address = existing_addresses[i]
        #             else:
        #                 address = StaffAddress(staff=staff)

        #             address.address_type = address_types[i]
        #             address.address_line_1 = line1s[i]
        #             address.address_line_2 = line2s[i]
        #             address.city = cities[i]
        #             address.state = states[i]
        #             address.postal_code = postal_codes[i]
        #             address.country = countries[i]

        #             address.save()

        #         existing_contacts = list(staff.emergency_contacts.all())
        #         names = request.POST.getlist("staff-emergency_name[]")
        #         relationships = request.POST.getlist("staff-emergency_relationship[]")
        #         phones = request.POST.getlist("staff-emergency_phone[]")
        #         emails = request.POST.getlist("staff-emergency_email[]")
        #         priorities = request.POST.getlist("staff-emergency_priority[]")

        #         for i in range(len(names)):
        #             if i < len(existing_contacts):
        #                     contact = existing_contacts[i]
        #             else:
        #                 contact = StaffEmergencyContact(staff=staff)
        #                 contact.contact_name = names[i]
        #                 contact.relationship = relationships[i]
        #                 contact.phone_number = phones[i]
        #                 contact.email = emails[i]
        #                 contact.priority = priorities[i] or 1

        #                 contact.save()

        #             # Delete removed contacts
                   
        #         if len(existing_contacts) > len(names):
        #             for contact in existing_contacts[len(names):]:
        #                 contact.delete()

        #             education_ids = request.POST.getlist("staff-education_id[]")
        #             degrees = request.POST.getlist("staff-degree[]")
        #             institutions = request.POST.getlist("staff-institution_name[]")
        #             fields = request.POST.getlist("staff-field_of_study[]")
        #             years = request.POST.getlist("staff-graduation_year[]")

        #             saved_ids = []

        #             for i in range(len(degrees)):
        #                 if not degrees[i].strip():
        #                     continue

        #                 if i < len(education_ids) and education_ids[i]:
        #                     edu = StaffEducation.objects.filter(
        #                         id=education_ids[i],
        #                         staff=staff
        #                     ).first()
        #                 else:
        #                     edu = StaffEducation(staff=staff)

        #                 edu.degree = degrees[i]
        #                 edu.institution_name = institutions[i]
        #                 edu.field_of_study = fields[i]
        #                 edu.graduation_year = years[i] or None
        #                 edu.save()

        #                 saved_ids.append(edu.id)
                # #satff eductaions 
                # StaffEducation.objects.filter(staff=staff).exclude(id__in=saved_ids).delete()
                # cert_ids = request.POST.getlist("staff-certification_id[]")
                # names = request.POST.getlist("staff-certification_name[]")
                # orgs = request.POST.getlist("staff-issuing_organization[]")
                # issue_dates = request.POST.getlist("staff-issue_date[]")
                # expiry_dates = request.POST.getlist("staff-expiration_date[]")
                # saved_ids = []
                # for i in range(len(names)):
                #     if not names[i].strip():
                #         continue

                #     if i < len(cert_ids) and cert_ids[i]:
                #             cert = StaffCertification.objects.filter(
                #                 id=cert_ids[i],
                #                 staff=staff
                #             ).first()
                #     else:
                #             cert = StaffCertification(staff=staff)

                #     cert.certification_name = names[i]
                #     cert.issuing_organization = orgs[i]
                #     cert.issue_date = issue_dates[i] or None
                #     cert.expiration_date = expiry_dates[i] or None
                #     cert.save()
                #     saved_ids.append(cert.id)
                #     StaffCertification.objects.filter(staff=staff).exclude(id__in=saved_ids).delete()

                #     # Existing documents update
                #     # ---------------- Staff Documents ----------------

                # existing_doc_ids = []

                #     # Existing documents
                # doc_ids = request.POST.getlist("staff-document_id[]")
                # doc_types = request.POST.getlist("staff-document_type[]")
                # file_names = request.POST.getlist("staff-file_name[]")
                # files = request.FILES.getlist("staff-file[]")
                # for i in range(len(doc_types)):
                #     doc = None
                #     doc_id = doc_ids[i].strip() if i < len(doc_ids) else ""
                #     if doc_id.isdigit():
                #         doc = StaffDocument.objects.filter(
                #                 id=int(doc_id),
                #                 staff=staff
                #             ).first()

                #     if not doc:
                #         continue

                #     doc.document_type = doc_types[i]
                #     if i < len(file_names):
                #         doc.file_name = file_names[i]

                #     if i < len(files) and files[i]:
                #         doc.file = files[i]

                #     doc.verification_status = "PENDING"
                #     doc.save()

                #     existing_doc_ids.append(doc.id)


                #     # Newly added documents
                #     new_types = request.POST.getlist("staff-new-document_type[]")
                #     new_names = request.POST.getlist("staff-new-file_name[]")
                #     new_files = request.FILES.getlist("staff-new-file[]")

                #     for i, file in enumerate(new_files):

                #         if not file:
                #             continue

                #         StaffDocument.objects.create(
                #             staff=staff,
                #             document_type=new_types[i] if i < len(new_types) else "OTHER",
                #             file_name=new_names[i] if i < len(new_names) and new_names[i] else file.name,
                #             file=file,
                #             verification_status="PENDING",
                #         )
                

      
                                    
        messages.success(request, "User updated successfully.")
        return redirect("user_view", uid=user_obj.uuid)

    return redirect("user_edit", uid=user_obj.uuid)

##swetha's code end ######


import traceback

@login_required
@require_http_methods(["POST"])
def user_update_json(request, uid):

    try:

        user_obj = get_object_or_404(User, id=uid)

        before = AuditLogger.model_to_dict(
            user_obj, ["first_name", "last_name", "email", "mobile_number", "account_status", "role"]
        )

        form = UserCreateForm(
            request.POST,
            request.FILES,
            instance=user_obj,
            is_edit=True
        )

        if form.is_valid():

            user = form.save(commit=False, is_edit=True)

         
            role_id = request.POST.get("role")

            if role_id:
                user.role = UserRole.objects.get(id=role_id)

            user.is_student = False
            user.is_faculty = False
            user.is_admin = False
            user.is_staff = False

            user_type = request.POST.get("user_type")

            if user_type == "student":
                user.is_student = True

            elif user_type == "faculty":
                user.is_faculty = True

            elif user_type == "admin":
                user.is_admin = True

            elif user_type == "staff":
                user.is_staff = True

            user.save()

            AuditLogger.log(
                request=request,
                action="UPDATE",
                module="UserManagement",
                object_type="User",
                object_id=user.id,
                description=f"Updated user '{user.username}'.",
                before_data=before,
                after_data=AuditLogger.model_to_dict(
                    user, ["first_name", "last_name", "email", "mobile_number", "account_status", "role"]
                ),
                status="SUCCESS",
            )


            

            return JsonResponse({"ok": True})


        AuditLogger.log(
            request=request,
            action="UPDATE",
            module="UserManagement",
            object_type="User",
            object_id=uid,
            description=f"Failed to update user (uid={uid}): validation errors.",
            before_data=before,
            status="FAILED",
        )

        return JsonResponse({
            "ok": False,
            "errors": form.errors
        }, status=400)

    except Exception as e:
        traceback.print_exc()

        return JsonResponse({
            "ok": False,
            "error": str(e)
        }, status=500)


@login_required
@require_http_methods(["DELETE"])
def user_delete_json(request, uid):
    """AJAX delete — returns JSON."""
    from django.shortcuts import get_object_or_404
    user_obj = get_object_or_404(User, id=uid)
    before = AuditLogger.model_to_dict(
        user_obj, ["username", "email", "first_name", "last_name", "role", "account_status"]
    )
    deleted_username = user_obj.username
    user_obj.delete()
    AuditLogger.log(
        request=request,
        action="DELETE",
        module="UserManagement",
        object_type="User",
        object_id=uid,
        description=f"Deleted user '{deleted_username}'.",
        before_data=before,
        status="SUCCESS",
    )
    return JsonResponse({"ok": True})


VALID_STATUS_VALUES = {choice[0] for choice in User.STATUS_CHOICES}


@login_required
@require_http_methods(["POST"])
def user_status_update_json(request, uid):
   
    user_obj = get_object_or_404(User, id=uid)

    new_status = (request.POST.get("status") or "").strip().upper()

    if new_status not in VALID_STATUS_VALUES:
        AuditLogger.log(
            request=request,
            action="UPDATE",
            module="UserManagement",
            object_type="User",
            object_id=user_obj.id,
            description=f"Failed status change for user '{user_obj.username}': invalid status '{new_status}'.",
            status="FAILED",
        )
        return JsonResponse(
            {"ok": False, "error": "Invalid status value."},
            status=400,
        )

    before_status = user_obj.account_status
    user_obj.account_status = new_status
    user_obj.save(update_fields=["account_status"])

    AuditLogger.log(
        request=request,
        action="UPDATE",
        module="UserManagement",
        object_type="User",
        object_id=user_obj.id,
        description=f"Changed status of user '{user_obj.username}' from {before_status} to {new_status}.",
        before_data={"account_status": before_status},
        after_data={"account_status": new_status},
        status="SUCCESS",
    )

    return JsonResponse({"ok": True, "status": user_obj.account_status})

 
import json
 
 
@login_required
@require_http_methods(["GET"])
def role_detail_json(request, role_id):
    """
    GET /roles/<role_id>/details/
    Returns role info + all assigned users.
    """
    role_obj = get_object_or_404(UserRole, id=role_id)
    color_map = _role_color_map()
 
    STATUS_MAP = {
        "ACTIVE": "active",
        "INACTIVE": "inactive",
        "PENDING": "pending",
        "SUSPENDED": "inactive",
    }
 
    users = role_obj.users.all().order_by("first_name", "last_name")
    users_data = []
    for u in users:
        full_name = f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username
        users_data.append({
            "id": u.id,
            "name": full_name,
            "email": u.email or "",
            "uid": u.university_id or "—",
            "status": STATUS_MAP.get(u.account_status, "inactive"),
        })
 
    return JsonResponse({
        "role_id": role_obj.id,
        "role_name": role_obj.role_name,
        "description": role_obj.description or "",
        "total_users": len(users_data),
        "users": users_data,
    })
 
 
@login_required
@require_http_methods(["GET"])
def role_available_users_json(request, role_id):
    """
    GET /roles/<role_id>/available-users/?search=
    Returns users NOT currently assigned to this role.
    """
    role_obj = get_object_or_404(UserRole, id=role_id)
    search = request.GET.get("search", "").strip()
 
    users = User.objects.exclude(role=role_obj).order_by("first_name", "last_name")
 
    if search:
        users = users.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(username__icontains=search)
            | Q(email__icontains=search)
            | Q(university_id__icontains=search)
        )
 
    users = users[:20]  # cap autocomplete results
 
    data = []
    for u in users:
        full_name = f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username
        data.append({
            "id": u.id,
            "name": full_name,
            "email": u.email or "",
            "uid": u.university_id or "",
        })
 
    return JsonResponse({"users": data})
 
@require_permission("userrole_update")
@login_required
@require_http_methods(["POST"])
def role_assign_users_json(request, role_id):
   
    role_obj = get_object_or_404(UserRole, id=role_id)
 
    try:
        body = json.loads(request.body)
        user_ids = body.get("user_ids", [])
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)
 
    if not user_ids:
        return JsonResponse({"ok": False, "error": "No user IDs provided."}, status=400)
 
    updated = 0
    for uid in user_ids:
        try:
            u = User.objects.get(id=uid)
            before_role = str(u.role) if u.role else None
            u.role = role_obj
            u.save(update_fields=["role"])
            updated += 1
            AuditLogger.log(
                request=request,
                action="ROLE_ASSIGN",
                module="RoleManagement",
                object_type="User",
                object_id=u.id,
                description=f"Assigned role '{role_obj.role_name}' to user '{u.username}'.",
                before_data={"role": before_role},
                after_data={"role": role_obj.role_name},
                status="SUCCESS",
            )

        except User.DoesNotExist:
            pass
 
    total_users = role_obj.users.count()
    return JsonResponse({"ok": True, "updated": updated, "total_users": total_users})
 
@require_permission("userrole_update")
@login_required
@require_http_methods(["POST"])
def role_revoke_user_json(request, role_id):
 
    role_obj = get_object_or_404(UserRole, id=role_id)
 
    try:
        body = json.loads(request.body)
        user_id = body.get("user_id")
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)
 
    if not user_id:
        return JsonResponse({"ok": False, "error": "user_id is required."}, status=400)
 
    user_obj = get_object_or_404(User, id=user_id)
 
    # Only revoke if they actually belong to this role
    if user_obj.role_id != role_obj.id:
        return JsonResponse({"ok": False, "error": "User is not assigned to this role."}, status=400)
 
    before_role_name = role_obj.role_name
    user_obj.role = None
    user_obj.save(update_fields=["role"])

    AuditLogger.log(
        request=request,
        action="ROLE_REMOVE",
        module="RoleManagement",
        object_type="User",
        object_id=user_obj.id,
        description=f"Revoked role '{before_role_name}' from user '{user_obj.username}'.",
        before_data={"role": before_role_name},
        after_data={"role": None},
        status="SUCCESS",
    )
 
    return JsonResponse({"ok": True, "total_users": role_obj.users.count()})

@require_permission("userrole_update")
@login_required
@require_http_methods(["POST"])
def role_update_json(request, role_id):

    role_obj = get_object_or_404(UserRole, id=role_id)

    try:
        body = json.loads(request.body)
        new_name = (body.get("role_name") or "").strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)

    if not new_name:
        return JsonResponse({"ok": False, "error": "Role name cannot be empty."}, status=400)

    if len(new_name) > 100:
        return JsonResponse({"ok": False, "error": "Role name must be 100 characters or fewer."}, status=400)

    if UserRole.objects.filter(role_name__iexact=new_name).exclude(id=role_obj.id).exists():
        return JsonResponse({"ok": False, "error": "A role with this name already exists."}, status=400)

    old_name = role_obj.role_name
    role_obj.role_name = new_name
    role_obj.save(update_fields=["role_name"])

    AuditLogger.log(
        request=request,
        action="UPDATE",
        module="RoleManagement",
        object_type="UserRole",
        object_id=role_obj.id,
        description=f"Renamed role '{old_name}' to '{new_name}'.",
        before_data={"role_name": old_name},
        after_data={"role_name": new_name},
        status="SUCCESS",
    )

    return JsonResponse({
        "ok": True,
        "role_id": role_obj.id,
        "role_name": role_obj.role_name,
    })

@require_permission("userrole_update")
@login_required
@require_http_methods(["POST"])
def role_convert_users_json(request, role_id):
 
    source_role = get_object_or_404(UserRole, id=role_id)

    try:
        body = json.loads(request.body)
        target_role_id = body.get("target_role_id")
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)

    if not target_role_id:
        return JsonResponse({"ok": False, "error": "target_role_id is required."}, status=400)

    if str(target_role_id) == str(source_role.id):
        return JsonResponse({"ok": False, "error": "Target role must be different from the current role."}, status=400)

    target_role = get_object_or_404(UserRole, id=target_role_id)

    moved_count = User.objects.filter(role=source_role).update(role=target_role)

    AuditLogger.log(
        request=request,
        action="ROLE_ASSIGN",
        module="RoleManagement",
        object_type="UserRole",
        object_id=target_role.id,
        description=f"Bulk-migrated {moved_count} user(s) from role '{source_role.role_name}' to '{target_role.role_name}'.",
        before_data={"source_role": source_role.role_name, "moved_count": moved_count},
        after_data={"target_role": target_role.role_name},
        status="SUCCESS",
    )

    return JsonResponse({
        "ok": True,
        "moved_count": moved_count,
        "source_role": {"id": source_role.id, "name": source_role.role_name, "count": source_role.users.count()},
        "target_role": {"id": target_role.id, "name": target_role.role_name, "count": target_role.users.count()},
    })



@require_page_access("audit_log_page")
@login_required
def audit_log_page(request):
    return render(request, "audit_log.html")
 
 
@login_required
def audit_log_json(request):
   
    logs = (
        UserAuditLog.objects
        .select_related("user")
        .order_by("-timestamp")[:2000]   
    )
 
    data = []
    for log in logs:
        data.append({
            "id": log.id,
            "user": log.user.username if log.user else "Anonymous",
            "action": log.action,
            "module": log.module,
            "object_type": log.object_type,
            "object_id": log.object_id,
            "description": log.description,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "ip_address": log.ip_address,
            "browser": log.browser,
            "operating_system": log.operating_system,
            "device": log.device,
            "request_method": log.request_method,
            "request_url": log.request_url,
            "status": log.status,
            "before_data": log.before_data,
            "after_data": log.after_data,
            "session_key": log.session_key,
            "request_id": log.request_id,
        })
 
    return JsonResponse({"results": data, "count": len(data)})




from datetime import date
from Admin.models import UserRoleAssignment, UserSession, UserNotificationPreference
from Students.models import (
    StudentProfile, StudentAddress, StudentEmergencyContact, StudentAcademicProfile,
    StudentEnrollment, StudentFinancialAid, StudentFee, StudentFeePayment,
    StudentHousing, StudentResearchProfile, StudentOrganization, StudentCareerProfile,
    StudentDocument,
)
from Faculty.models import (
    FacultyProfile, FacultyRank, FacultyAppointment, FacultyEducation,
    FacultyCourseAssignment, FacultyResearch, FacultyGrant, FacultyPublication,
    FacultyOfficeHours, FacultyCommittee, FacultyEvaluation, FacultyDocument,
)
from Staff.models import (
    StaffProfile, StaffPosition, StaffAddress, StaffEmergencyContact,
    StaffDepartmentAssignment, StaffEducation, StaffCertification, StaffTraining,
    StaffPerformanceReview, StaffLeave, StaffPayroll, StaffAccessRole, StaffDocument,
)

def _calculate_age(dob):
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _get_student_context(user_obj):
    student = (
        StudentProfile.objects
        .select_related("academic_profile", "career_profile")
        .prefetch_related(
            "addresses",
            "emergency_contacts",
            "enrollments__section_id__course",
            "enrollments__section_id__semester_id",
            "financial_aids",
            "fees__payments",
            "housing_records",
            "research_profiles",
            # "organizations",
            "organization_memberships",
            "documents",
        )
        .filter(user=user_obj)
        .first()
    )
    return {"student": student}


def _get_faculty_context(user_obj):
    faculty = (
        FacultyProfile.objects
        .select_related("faculty_rank")
        .prefetch_related(
            "appointments",
            "education_records",
            "course_assignments",
            "research_projects",
            "grants",
            "publications",
            "office_hours",
            "committee_memberships",
            "evaluations", 
            "documents",
        )
        .filter(user=user_obj)
        .first()
    )
    return {"faculty": faculty}



def _get_staff_context(user_obj):

    staff = (
        StaffProfile.objects
        .select_related("supervisor", "supervisor__user")
        .filter(user=user_obj)
        .first()
    )

    if not staff:
        return {}

    return {
        "staff": staff,
        "staff_positions": staff.positions.all(),
        "staff_addresses": staff.addresses.all(),
        "staff_emergency_contacts": staff.emergency_contacts.all(),
        "staff_department_assignments": staff.department_assignments.all(),
        "staff_education": staff.education_records.all(),
        "staff_certifications": staff.certifications.all(),
        "staff_training": staff.training_records.all(),
        "staff_reviews": staff.performance_reviews.all(),
        "staff_leaves": staff.leave_records.all(),
        "staff_payrolls": staff.payroll_records.all(),
        "staff_access_roles": staff.access_roles.all(),
        "staff_documents": staff.documents.all(),
    }

@require_page_access("user_view_page")
@login_required
def user_view(request, uid):
   
    user_obj = get_object_or_404(
        User.objects.select_related("role"),
        uuid=uid
    )

    if user_obj.is_admin:
        user_type = "admin"
    elif user_obj.is_faculty:
        user_type = "faculty"
    elif user_obj.is_staff:
        user_type = "staff"
    elif user_obj.is_student:
        user_type = "student"
    else:
        user_type = ""

    context = {
        "user_obj": user_obj,
        "user_type": user_type,
        "user_initial": (user_obj.first_name or user_obj.username or "U")[:1].upper(),
        "user_age": _calculate_age(user_obj.date_of_birth),
        "student": None,
        "faculty": None,
        "staff": None,
        
    }

    if user_type == "student":
        context.update(_get_student_context(user_obj))
    elif user_type == "faculty":
        context.update(_get_faculty_context(user_obj))
    elif user_type == "staff":
        context.update(_get_staff_context(user_obj))

    # System information — applies to every user type
    context["role_assignments"] = (
        UserRoleAssignment.objects.filter(user=user_obj)
        .select_related("role").order_by("-assigned_at")
    )
    context["recent_sessions"] = (
        UserSession.objects.filter(user=user_obj).order_by("-login_time")[:5]
    )
    context["recent_audit_logs"] = (
        UserAuditLog.objects.filter(user=user_obj).order_by("-timestamp")[:10]
    )
    context["notif_prefs"] = UserNotificationPreference.objects.filter(user=user_obj).first()

    AuditLogger.log(
        request=request,
        action="VIEW",
        module="UserManagement",
        object_type="User",
        object_id=user_obj.id,
        description=f"Viewed profile of user '{user_obj.username}'.",
        status="SUCCESS",
    )

    return render(request, "user_view.html", context)
 
 

def _relative_time(dt):
    """Simple 'time ago' formatter, no extra app dependency needed."""
    if not dt:
        return ""
    delta = timezone.now() - dt
    seconds = delta.total_seconds()
    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        m = int(seconds // 60)
        return f"{m} minute{'s' if m != 1 else ''} ago"
    if seconds < 86400:
        h = int(seconds // 3600)
        return f"{h} hour{'s' if h != 1 else ''} ago"
    if seconds < 604800:
        d = int(seconds // 86400)
        return "Yesterday" if d == 1 else f"{d} days ago"
    weeks = int(seconds // 604800)
    return f"{weeks} week{'s' if weeks != 1 else ''} ago"


def _firearm_recent_activity(firearms, limit=6):
    
    events = []
    for f in firearms:
        is_new = (f.updated_at - f.created_at) < timedelta(seconds=5)
        if is_new:
            icon, tone, title, ts = "plus-circle", "green", "Added new firearm", f.created_at
        else:
            icon, tone, title, ts = "pencil-line", "blue", "Updated firearm details", f.updated_at
        events.append({
            "icon": icon,
            "tone": tone,
            "title": title,
            "detail": f"{f.firearm_name} ({f.serial_number}) — status: {f.get_current_status_display()}.",
            "timestamp": _relative_time(ts),
            "_sort": ts,
        })
    events.sort(key=lambda e: e["_sort"], reverse=True)
    return [{k: v for k, v in e.items() if k != "_sort"} for e in events[:limit]]


@require_page_access("firearm_page")
@login_required
def firearm_page(request):


    firearms = list(Firearm.objects.all().order_by("-created_at"))
    now_year = date.today().year

    status_counts = Counter(f.current_status for f in firearms)
    type_counts = Counter(f.firearm_type for f in firearms)
    manufacturers = {f.manufacturer for f in firearms if f.manufacturer}
    purchased_this_year = sum(
        1 for f in firearms if f.purchase_date and f.purchase_date.year == now_year
    )

    stats = {
        "total": len(firearms),
        "active": status_counts.get("ACTIVE", 0),
        "stored": status_counts.get("STORED", 0),
        "retired": status_counts.get("RETIRED", 0), 
        "disposed": status_counts.get("DISPOSED", 0),
        "purchased_this_year": purchased_this_year,
        "total_manufacturers": len(manufacturers),
    }

    status_chart = {
        "labels": ["Active", "Stored", "Retired", "Disposed"],
        "data": [
            status_counts.get("ACTIVE", 0),
            status_counts.get("STORED", 0),
            status_counts.get("RETIRED", 0),
            status_counts.get("DISPOSED", 0),
        ],
    }
    type_chart = {
        "labels": ["Handgun", "Rifle", "Shotgun", "Training", "Other"],
        "data": [
            type_counts.get("HANDGUN", 0),
            type_counts.get("RIFLE", 0),
            type_counts.get("SHOTGUN", 0),
            type_counts.get("TRAINING", 0),
            type_counts.get("OTHER", 0),
        ],
    }

   

    def _build_permission_user(u):
            latest_firearm = u.firearms.order_by("-created_at").first()
            return {
                "uuid": str(u.uuid),
                "name": u.full_name,
                "initials": (u.first_name[:1].upper() if u.first_name else u.username[:1].upper()),
                "employeeId": u.university_id or u.username,
                "department": u.role.role_name if u.role else "",
                "role": u.role.get_user_type_display() if u.role else "",
                "permission": "Full Access" if u.is_full_crud else "Custody Only",
                "firearmsAssigned": u.firearms.count(),
                "grantedOn": u.created_at.strftime("%Y-%m-%d"),
                # "status": u.account_status.title(),
                "status": latest_firearm.get_current_status_display() if latest_firearm else "",
                "username": u.username,
                "firearmId": latest_firearm.id if latest_firearm else None,
                "firearmType": latest_firearm.get_firearm_type_display() if latest_firearm else "",
            }

    permission_users = [
        _build_permission_user(u)
        for u in User.objects.filter(firearms__isnull=False).distinct()
    ]

    context = {
        "firearms": firearms,
        "stats": stats,
        "status_chart_labels": json.dumps(status_chart["labels"]),
        "status_chart_data": json.dumps(status_chart["data"]),
        "type_chart_labels": json.dumps(type_chart["labels"]),
        "type_chart_data": json.dumps(type_chart["data"]),
        "recent_activity": _firearm_recent_activity(firearms),
        "permission_users_json": json.dumps(permission_users),
    }

    AuditLogger.log(
        request=request,
        action="VIEW",
        module="FirearmManagement",
        object_type="Firearm",
        object_id="",
        description="Viewed the Firearm Management dashboard.",
        status="SUCCESS",
    )

    return render(request, "firearm.html", context) 

@require_permission("firearm_update")
@login_required
@require_http_methods(["POST"])
def firearm_update_json(request, fid):

    firearm = get_object_or_404(Firearm, id=fid)
    errors = {}

    firearm_name = (request.POST.get("firearm_name") or "").strip()
    firearm_type = (request.POST.get("firearm_type") or "").strip()
    manufacturer = (request.POST.get("manufacturer") or "").strip()
    model_name = (request.POST.get("model_name") or "").strip()
    serial_number = (request.POST.get("serial_number") or "").strip()
    caliber = (request.POST.get("caliber") or "").strip()
    purchase_date_raw = (request.POST.get("purchase_date") or "").strip()
    acquisition_method = (request.POST.get("acquisition_method") or "").strip() or "PURCHASE"
    location_name = (request.POST.get("location_name") or "").strip()
    building_name = (request.POST.get("building_name") or "").strip()
    room_number = (request.POST.get("room_number") or "").strip()
    security_level = (request.POST.get("security_level") or "").strip()
    current_status = (request.POST.get("current_status") or "").strip() or "ACTIVE"
    notes = (request.POST.get("notes") or "").strip()
    is_full_crud = (request.POST.get("is_full_crud") or "").strip().lower() in ("on", "true", "1")

    if not firearm_name:
        errors["firearm_name"] = "Firearm name is required."
    elif len(firearm_name) > 150:
        errors["firearm_name"] = "Firearm name must be 150 characters or fewer."

    if not firearm_type:
        errors["firearm_type"] = "Firearm type is required."
    elif firearm_type not in FIREARM_TYPE_VALUES:
        errors["firearm_type"] = "Select a valid firearm type."

    if manufacturer and len(manufacturer) > 150:
        errors["manufacturer"] = "Manufacturer must be 150 characters or fewer."
    if model_name and len(model_name) > 150:
        errors["model_name"] = "Model must be 150 characters or fewer."

    if not serial_number:
        errors["serial_number"] = "Serial number is required."
    elif len(serial_number) > 150:
        errors["serial_number"] = "Serial number must be 150 characters or fewer."
    elif len(serial_number) < 3:
        errors["serial_number"] = "Serial number looks too short."
    elif Firearm.objects.filter(serial_number__iexact=serial_number).exclude(id=firearm.id).exists():
        errors["serial_number"] = "A firearm with this serial number already exists."

    if caliber and len(caliber) > 50:
        errors["caliber"] = "Caliber must be 50 characters or fewer."

    parsed_purchase_date = None
    if purchase_date_raw:
        try:
            parsed_purchase_date = datetime.strptime(purchase_date_raw, "%Y-%m-%d").date()
            if parsed_purchase_date > date.today():
                errors["purchase_date"] = "Purchase date cannot be in the future."
        except ValueError:
            errors["purchase_date"] = "Enter a valid date (YYYY-MM-DD)."

    if acquisition_method not in FIREARM_ACQUISITION_VALUES:
        errors["acquisition_method"] = "Select a valid acquisition method."

    if location_name and len(location_name) > 150:
        errors["location_name"] = "Storage location must be 150 characters or fewer."
    if building_name and len(building_name) > 150:
        errors["building_name"] = "Building name must be 150 characters or fewer."
    if room_number and len(room_number) > 50:
        errors["room_number"] = "Room number must be 50 characters or fewer."
    if security_level and len(security_level) > 100:
        errors["security_level"] = "Security level must be 100 characters or fewer."

    if current_status not in FIREARM_STATUS_VALUES:
        errors["current_status"] = "Select a valid status."

    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)

    before_data = AuditLogger.model_to_dict(
        firearm, ["firearm_name", "firearm_type", "serial_number", "current_status"]
    )

    firearm.firearm_name = firearm_name
    firearm.firearm_type = firearm_type
    firearm.manufacturer = manufacturer or None
    firearm.model_name = model_name or None
    firearm.serial_number = serial_number
    firearm.caliber = caliber or None
    firearm.purchase_date = parsed_purchase_date
    firearm.acquisition_method = acquisition_method
    firearm.location_name = location_name or None
    firearm.building_name = building_name or None
    firearm.room_number = room_number or None
    firearm.security_level = security_level or None
    firearm.current_status = current_status
    firearm.notes = notes or None
    firearm.is_full_crud = is_full_crud
    firearm.save()

    AuditLogger.log(
        request=request,
        action="UPDATE",
        module="FirearmManagement",
        object_type="Firearm",
        object_id=firearm.id,
        description=(
            f"Updated firearm '{firearm.firearm_name}' ({firearm.serial_number}) "
            f"via Edit Firearm form, linked to user '{firearm.user.username}'."
        ),
        before_data=before_data,
        after_data=AuditLogger.model_to_dict(
            firearm, ["firearm_name", "firearm_type", "serial_number", "current_status"]
        ),
        status="SUCCESS",
    )

    return JsonResponse({
        "ok": True,
        "message": f"Firearm '{firearm.firearm_name}' updated successfully.",
        "firearm_id": firearm.id,
    })



FIREARM_TYPE_VALUES = {c[0] for c in Firearm.FIREARM_TYPE_CHOICES}
FIREARM_STATUS_VALUES = {c[0] for c in Firearm.STATUS_CHOICES}
FIREARM_ACQUISITION_VALUES = {c[0] for c in Firearm.ACQUISITION_METHOD_CHOICES}


@login_required
@require_http_methods(["GET"])
def firearm_user_search_json(request):
    """Autocomplete endpoint backing the 'Assigned User' field on the
    Add Firearm form. Returns usernames that contain the given query."""
    query = (request.GET.get("q") or "").strip()
    if not query:
        return JsonResponse({"results": []})

    users = User.objects.filter(username__icontains=query).order_by("username")[:10]
    results = [
        {
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name,
        }
        for u in users
    ]
    return JsonResponse({"results": results})


@login_required
def firearm_view(request, uid):
   

    user_obj = get_object_or_404(
        User.objects.select_related("role"),
        uuid=uid
    )

    if user_obj.is_admin:
        user_type = "admin"
    elif user_obj.is_faculty:
        user_type = "faculty"
    elif user_obj.is_staff:
        user_type = "staff"
    elif user_obj.is_student:
        user_type = "student"
    else:
        user_type = ""

    context = {
        "user_obj": user_obj,
        "user_type": user_type,
        "user_initial": (user_obj.first_name or user_obj.username or "U")[:1].upper(),
        "user_age": _calculate_age(user_obj.date_of_birth),
        "student": None,
        "faculty": None,
        "staff": None,
    }

    if user_type == "student":
        context.update(_get_student_context(user_obj))
    elif user_type == "faculty":
        context.update(_get_faculty_context(user_obj))
    elif user_type == "staff":
        context.update(_get_staff_context(user_obj))

   
    firearms = (
        Firearm.objects.filter(user=user_obj).order_by("-created_at")
    )
    status_counts = Counter(f.current_status for f in firearms)

    context["firearms"] = firearms
    context["firearm_count"] = firearms.count()
    context["firearm_active_count"] = status_counts.get("ACTIVE", 0)
    context["firearm_stored_count"] = status_counts.get("STORED", 0)
    context["firearm_retired_count"] = status_counts.get("RETIRED", 0)
    context["firearm_disposed_count"] = status_counts.get("DISPOSED", 0)

    AuditLogger.log(
        request=request,
        action="VIEW",
        module="FirearmManagement",
        object_type="User",
        object_id=user_obj.id,
        description=f"Viewed firearm custody profile of user '{user_obj.username}'.",
        status="SUCCESS",
    )

    return render(request, "firearm_view.html", context)

@require_permission("firearm_create")
@login_required
@require_http_methods(["POST"])
def firearm_create_json(request):
   
    errors = {}

    username = (request.POST.get("username") or "").strip()
    firearm_name = (request.POST.get("firearm_name") or "").strip()
    firearm_type = (request.POST.get("firearm_type") or "").strip()
    manufacturer = (request.POST.get("manufacturer") or "").strip()
    model_name = (request.POST.get("model_name") or "").strip()
    serial_number = (request.POST.get("serial_number") or "").strip()
    caliber = (request.POST.get("caliber") or "").strip()
    purchase_date_raw = (request.POST.get("purchase_date") or "").strip()
    acquisition_method = (request.POST.get("acquisition_method") or "").strip() or "PURCHASE"
    location_name = (request.POST.get("location_name") or "").strip()
    building_name = (request.POST.get("building_name") or "").strip()
    room_number = (request.POST.get("room_number") or "").strip()
    security_level = (request.POST.get("security_level") or "").strip()
    current_status = (request.POST.get("current_status") or "").strip() or "ACTIVE"
    notes = (request.POST.get("notes") or "").strip()
    is_full_crud = (request.POST.get("is_full_crud") or "").strip().lower() in ("on", "true", "1")

    
    user_obj = None
    if not username:
        errors["username"] = "Please select an existing username."
    else:
        user_obj = User.objects.filter(username=username).first()
        if not user_obj:
            errors["username"] = "Username does not exist."

   
    if not firearm_name:
        errors["firearm_name"] = "Firearm name is required."
    elif len(firearm_name) > 150:
        errors["firearm_name"] = "Firearm name must be 150 characters or fewer."

    
    if not firearm_type:
        errors["firearm_type"] = "Firearm type is required."
    elif firearm_type not in FIREARM_TYPE_VALUES:
        errors["firearm_type"] = "Select a valid firearm type."

   
    if manufacturer and len(manufacturer) > 150:
        errors["manufacturer"] = "Manufacturer must be 150 characters or fewer."
    if model_name and len(model_name) > 150:
        errors["model_name"] = "Model must be 150 characters or fewer."

   
    if not serial_number:
        errors["serial_number"] = "Serial number is required."
    elif len(serial_number) > 150:
        errors["serial_number"] = "Serial number must be 150 characters or fewer."
    elif len(serial_number) < 3:
        errors["serial_number"] = "Serial number looks too short."
    elif Firearm.objects.filter(serial_number__iexact=serial_number).exists():
        errors["serial_number"] = "A firearm with this serial number already exists."

   
    if caliber and len(caliber) > 50:
        errors["caliber"] = "Caliber must be 50 characters or fewer."

   
    parsed_purchase_date = None
    if purchase_date_raw:
        try:
            parsed_purchase_date = datetime.strptime(purchase_date_raw, "%Y-%m-%d").date()
            if parsed_purchase_date > date.today():
                errors["purchase_date"] = "Purchase date cannot be in the future."
        except ValueError:
            errors["purchase_date"] = "Enter a valid date (YYYY-MM-DD)."

  
    if acquisition_method not in FIREARM_ACQUISITION_VALUES:
        errors["acquisition_method"] = "Select a valid acquisition method."

   
    if location_name and len(location_name) > 150:
        errors["location_name"] = "Storage location must be 150 characters or fewer."
    if building_name and len(building_name) > 150:
        errors["building_name"] = "Building name must be 150 characters or fewer."
    if room_number and len(room_number) > 50:
        errors["room_number"] = "Room number must be 50 characters or fewer."
    if security_level and len(security_level) > 100:
        errors["security_level"] = "Security level must be 100 characters or fewer."


    if current_status not in FIREARM_STATUS_VALUES:
        errors["current_status"] = "Select a valid status."

    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)

    firearm = Firearm.objects.create(
        user=user_obj,
        firearm_name=firearm_name,
        firearm_type=firearm_type,
        manufacturer=manufacturer or None,
        model_name=model_name or None,
        serial_number=serial_number,
        caliber=caliber or None,
        purchase_date=parsed_purchase_date,
        acquisition_method=acquisition_method,
        location_name=location_name or None,
        building_name=building_name or None,
        room_number=room_number or None,
        security_level=security_level or None,
        current_status=current_status,
        notes=notes or None,
        is_full_crud=is_full_crud,
    )

    AuditLogger.log(
        request=request,
        action="CREATE",
        module="FirearmManagement",
        object_type="Firearm",
        object_id=firearm.id,
        description=(
            f"Created firearm '{firearm.firearm_name}' ({firearm.serial_number}) "
            f"via Add Firearm form, linked to user '{user_obj.username}'."
        ),
        after_data=AuditLogger.model_to_dict(
            firearm, ["firearm_name", "firearm_type", "serial_number", "current_status"]
        ),
        status="SUCCESS",
    )

    return JsonResponse({
        "ok": True,
        "message": f"Firearm '{firearm.firearm_name}' added successfully.",
        "firearm_id": firearm.id,
    })


def save_firearm_details(request, user):
    """Creates a linked Firearm record for a newly created user when the
    'Does the user have a firearm or gun?' question is answered Yes.
    Mirrors save_student_details / save_faculty_details / save_staff_details."""
    if request.POST.get("has_firearm") != "yes":
        return None

    name = (request.POST.get("firearm_firearm_name") or "").strip()
    ftype = (request.POST.get("firearm_firearm_type") or "").strip()
    serial = (request.POST.get("firearm_serial_number") or "").strip()

    
    if not (name and ftype and serial):
        return None

    firearm = Firearm.objects.create(
        user=user,
        firearm_name=name,
        firearm_type=ftype,
        manufacturer=(request.POST.get("firearm_manufacturer") or "").strip() or None,
        model_name=(request.POST.get("firearm_model_name") or "").strip() or None,
        serial_number=serial,
        caliber=(request.POST.get("firearm_caliber") or "").strip() or None,
        purchase_date=request.POST.get("firearm_purchase_date") or None,
        acquisition_method=request.POST.get("firearm_acquisition_method") or "PURCHASE",
        location_name=(request.POST.get("firearm_location_name") or "").strip() or None,
        building_name=(request.POST.get("firearm_building_name") or "").strip() or None,
        room_number=(request.POST.get("firearm_room_number") or "").strip() or None,
        security_level=(request.POST.get("firearm_security_level") or "").strip() or None,
        current_status=request.POST.get("firearm_current_status") or "ACTIVE",
        notes=(request.POST.get("firearm_notes") or "").strip() or None,
    )

    AuditLogger.log(
        request=request,
        action="CREATE",
        module="FirearmManagement",
        object_type="Firearm",
        object_id=firearm.id,
        description=f"Created firearm '{firearm.firearm_name}' ({firearm.serial_number}) linked to user '{user.username}'.",
        after_data=AuditLogger.model_to_dict(firearm, ["firearm_name", "firearm_type", "serial_number", "current_status"]),
        status="SUCCESS",
    )
    return firearm

@login_required
def olympic_athlete_data_json(request):
    """Returns all OlympicAthlete records as JSON for olympicathlete.js to render."""
    athletes = OlympicAthlete.objects.select_related(
        "athlete__student", "sport", "team", "coach"
    ).order_by("-created_at")

    data = []
    for o in athletes:
        full_name = (
            o.athlete.student.full_name
            if o.athlete_id and o.athlete.student_id
            else "Unknown Athlete"
        )

        if o.profile_photo:
            photo_url = request.build_absolute_uri(o.profile_photo.url)
        else:
            photo_url = (
                f"https://ui-avatars.com/api/?name={full_name.replace(' ', '+')}"
                f"&background=0081C8&color=fff&size=128"
            )

        data.append({
            "id": o.id,
            "uuid": str(o.olympic_uuid),
            "photo": photo_url,
            "name": full_name,
            "athlete_number": o.athlete_number,
            "sport": str(o.sport) if o.sport_id else "—",
            "team": str(o.team) if o.team_id else "—",
            "coach": str(o.coach) if o.coach_id else "—",
            "nationality": o.nationality,
            "olympic_status": o.olympic_status,
            "target_olympics": o.target_olympics,
            "event_name": o.event_name,
            "event_category": o.event_category,
            "governing_body": o.governing_body,
            "world_ranking": o.world_ranking,
            "qualification_date": o.qualification_date.strftime("%Y-%m-%d") if o.qualification_date else None,
            "qualification_score": o.qualification_score or "—",
            "qualification_standard": o.qualification_standard or "—",
            "qualification_status": o.qualification_status,
            "personal_best": o.personal_best or "N/A",
            "biography": o.biography or "",
            "is_active": o.is_active,
        })


    progress_qs = (
        OlympicAthlete.objects
        .values("sport__sport_name")          
        .annotate(
            total=Count("id"),
            progressed=Count(
                "id",
                filter=Q(olympic_status__in=["QUALIFIED", "SELECTED", "PARTICIPATED", "RETIRED"])
            ),
        )
        .order_by("-total")
    )

    qualification_progress = [
        {
            "sport": row["sport__sport_name"] or "—",
            "percentage": round((row["progressed"] / row["total"]) * 100) if row["total"] else 0,
        }
        for row in progress_qs
    ]

   
    recent_logs = (
        UserAuditLog.objects
        .filter(object_type="OlympicAthlete")
        .order_by("-timestamp")[:3]
    )
    recent_updates = [
        {
            "text": log.description,
            "time": f"{timesince(log.timestamp)} ago",
        }
        for log in recent_logs
    ]

    return JsonResponse({
        "results": data,
        "qualification_progress": qualification_progress,
        "recent_updates": recent_updates,
    })

@require_page_access("olympic_page")
@login_required
def olympic_athlete_page(request):
    return render(request, "olympicathlete.html")



OLYMPIC_STATUS_VALUES = {c[0] for c in OlympicAthlete.OLYMPIC_STATUS}
QUALIFICATION_STATUS_VALUES = {c[0] for c in OlympicAthlete.QUALIFICATION_STATUS}
EVENT_CATEGORY_VALUES = {c[0] for c in OlympicAthlete.EVENT_CATEGORY}


def _athletic_display(athletic):
    """Best-effort resolution of an Athletic record's display name and photo.
    Mirrors the fallback pattern already used in olympic_athlete_data_json.
    NOTE: adjust `student.user` below if your StudentProfile's FK to User
    is named differently in Students/models.py."""
    full_name = "Unknown Athlete"
    photo_url = None
    student = getattr(athletic, "student", None)  
    if student:
        full_name = getattr(student, "full_name", full_name) or full_name
        if getattr(student, "profile_photo", None):
            try:
                photo_url = student.profile_photo.url
            except ValueError:
                photo_url = None
    return full_name, photo_url


COUNTRIES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola",
    "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria",
    "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados",
    "Belarus", "Belgium", "Belize", "Benin", "Bhutan",
    "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei",
    "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia",
    "Cameroon", "Canada", "Central African Republic", "Chad", "Chile",
    "China", "Colombia", "Comoros", "Congo (Brazzaville)", "Congo (Kinshasa)",
    "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czechia",
    "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador",
    "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia",
    "Eswatini", "Ethiopia", "Fiji", "Finland", "France",
    "Gabon", "Gambia", "Georgia", "Germany", "Ghana",
    "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau",
    "Guyana", "Haiti", "Honduras", "Hungary", "Iceland",
    "India", "Indonesia", "Iran", "Iraq", "Ireland",
    "Israel", "Italy", "Jamaica", "Japan", "Jordan",
    "Kazakhstan", "Kenya", "Kiribati", "Kosovo", "Kuwait",
    "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho",
    "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg",
    "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali",
    "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico",
    "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro",
    "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru",
    "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger",
    "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman",
    "Pakistan", "Palau", "Palestine", "Panama", "Papua New Guinea",
    "Paraguay", "Peru", "Philippines", "Poland", "Portugal",
    "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis",
    "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe",
    "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone",
    "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia",
    "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka",
    "Sudan", "Suriname", "Sweden", "Switzerland", "Syria",
    "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste",
    "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey",
    "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates",
    "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Vanuatu",
    "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia",
    "Zimbabwe",
]
COUNTRY_SET = set(COUNTRIES)



def _generate_next_olympic_athlete_id():
   
    year = timezone.now().year
    prefix = f"OLY-{year}-"
    count = OlympicAthlete.objects.filter(athlete_number__startswith=prefix).count()
    return f"{prefix}{count + 1:03d}"

@require_page_access("olympic_athlete_add_page")
@require_permission("olympicathlete_create")
@login_required
def olympic_athlete_add_page(request):
    """Renders the Add Olympic Athlete registration form."""
    linked_ids = OlympicAthlete.objects.values_list("athlete_id", flat=True)
    available_athletes = (
        Athletic.objects.exclude(athlete_id__in=linked_ids)
        .select_related("student")
    )

    athlete_options = []
    for a in available_athletes:
        name, photo = _athletic_display(a)
        athlete_options.append({
            "id": a.athlete_id,
            "name": name,
            "photo": photo or (
                f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}"
                f"&background=0081C8&color=fff&size=128"
            ),
        })

    context = {
        "sports": Sport.objects.all().order_by("sport_name"),
        "teams": SportTeamModel.objects.all(),
        "coaches": Coach.objects.all(),
        "athlete_options": athlete_options,
        "countries": COUNTRIES,
        "next_athlete_number": _generate_next_olympic_athlete_id(),
        "olympic_status_choices": OlympicAthlete.OLYMPIC_STATUS,
        "qualification_status_choices": OlympicAthlete.QUALIFICATION_STATUS,
        "event_category_choices": OlympicAthlete.EVENT_CATEGORY,
        "is_edit": False,
        "selected_olympic_status": "PENDING",
        "selected_qualification_status": "PENDING",
    }
    return render(request, "olympic_athlete_add.html", context)


# @require_page_access("olympic_athlete_edit_page")
@require_permission("olympicathlete_update")
@login_required
def olympic_athlete_edit_page(request, uuid):
    """Renders the Add/Edit form pre-filled with an existing Olympic athlete's data."""
    oa = get_object_or_404(
        OlympicAthlete.objects.select_related("athlete__student", "sport", "team", "coach"),
        olympic_uuid=uuid,
    )

    # Exclude athletes already linked to a DIFFERENT Olympic profile,
    # but keep this record's own athlete selectable.
    linked_ids = (
        OlympicAthlete.objects.exclude(pk=oa.pk).values_list("athlete_id", flat=True)
    )
    available_athletes = (
        Athletic.objects.exclude(athlete_id__in=linked_ids)
        .select_related("student")
    )

    athlete_options = []
    for a in available_athletes:
        name, photo = _athletic_display(a)
        athlete_options.append({
            "id": a.athlete_id,
            "name": name,
            "photo": photo or (
                f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}"
                f"&background=0081C8&color=fff&size=128"
            ),
        })

    current_name, current_photo = (
        _athletic_display(oa.athlete) if oa.athlete_id else ("Unknown Athlete", None)
    )
    if oa.profile_photo:
        current_photo = request.build_absolute_uri(oa.profile_photo.url)
    elif not current_photo:
        current_photo = (
            f"https://ui-avatars.com/api/?name={current_name.replace(' ', '+')}"
            f"&background=0081C8&color=fff&size=128"
        )

    context = {
        "is_edit": True,
        "athlete_obj": oa,
        "sports": Sport.objects.all().order_by("sport_name"),
        "teams": SportTeamModel.objects.all(),
        "coaches": Coach.objects.all(),
        "athlete_options": athlete_options,
        "countries": COUNTRIES,
        "next_athlete_number": oa.athlete_number,
        "olympic_status_choices": OlympicAthlete.OLYMPIC_STATUS,
        "qualification_status_choices": OlympicAthlete.QUALIFICATION_STATUS,
        "event_category_choices": OlympicAthlete.EVENT_CATEGORY,
        "selected_olympic_status": oa.olympic_status,
        "selected_qualification_status": oa.qualification_status,
        "current_athlete_name": current_name,
        "current_athlete_photo": current_photo,
    }
    return render(request, "olympic_athlete_add.html", context)

@require_permission("olympicathlete_update")
@login_required
@require_http_methods(["POST"])
def olympic_athlete_update_json(request, uuid):
    """Updates an existing OlympicAthlete record."""
    oa = get_object_or_404(OlympicAthlete,  olympic_uuid=uuid)
    errors = {}

    athlete_id = (request.POST.get("athlete") or "").strip()
    sport_id = (request.POST.get("sport") or "").strip()
    team_id = (request.POST.get("team") or "").strip()
    coach_id = (request.POST.get("coach") or "").strip()
    nationality = (request.POST.get("nationality") or "").strip()
    olympic_status = (request.POST.get("olympic_status") or "").strip() or "PENDING"
    target_olympics = (request.POST.get("target_olympics") or "").strip()
    event_name = (request.POST.get("event_name") or "").strip()
    event_category = (request.POST.get("event_category") or "").strip() or "INDIVIDUAL"
    governing_body = (request.POST.get("governing_body") or "").strip()
    world_ranking_raw = (request.POST.get("world_ranking") or "").strip()
    qualification_date_raw = (request.POST.get("qualification_date") or "").strip()
    qualification_score = (request.POST.get("qualification_score") or "").strip()
    qualification_standard = (request.POST.get("qualification_standard") or "").strip()
    qualification_status = (request.POST.get("qualification_status") or "").strip() or "PENDING"
    personal_best = (request.POST.get("personal_best") or "").strip()
    biography = (request.POST.get("biography") or "").strip()

    athletic_obj = None
    if not athlete_id:
        errors["athlete"] = "Please select an athlete."
    else:
        athletic_obj = Athletic.objects.filter(athlete_id=athlete_id).first()
        if not athletic_obj:
            errors["athlete"] = "Selected athlete does not exist."
        elif OlympicAthlete.objects.filter(athlete_id=athlete_id).exclude(pk=oa.pk).exists():
            errors["athlete"] = "This athlete already has an Olympic profile."

    sport_obj = None
    if not sport_id:
        errors["sport"] = "Sport is required."
    else:
        sport_obj = Sport.objects.filter(id=sport_id).first()
        if not sport_obj:
            errors["sport"] = "Select a valid sport."

    team_obj = SportTeamModel.objects.filter(team_id=team_id).first() if team_id else None
    coach_obj = Coach.objects.filter(coach_id=coach_id).first() if coach_id else None

    if not nationality:
        errors["nationality"] = "Nationality is required."
    elif nationality not in COUNTRY_SET:
        errors["nationality"] = "Select a valid nationality."

    if olympic_status not in OLYMPIC_STATUS_VALUES:
        errors["olympic_status"] = "Select a valid Olympic status."

    if not target_olympics:
        errors["target_olympics"] = "Target Olympics is required."
    elif len(target_olympics) > 100:
        errors["target_olympics"] = "Target Olympics must be 100 characters or fewer."

    if not event_name:
        errors["event_name"] = "Event name is required."
    elif len(event_name) > 150:
        errors["event_name"] = "Event name must be 150 characters or fewer."

    if event_category not in EVENT_CATEGORY_VALUES:
        errors["event_category"] = "Select a valid event category."

    if not governing_body:
        errors["governing_body"] = "Governing body is required."
    elif len(governing_body) > 150:
        errors["governing_body"] = "Governing body must be 150 characters or fewer."

    world_ranking = None
    if world_ranking_raw:
        try:
            world_ranking = int(world_ranking_raw)
            if world_ranking <= 0:
                errors["world_ranking"] = "World ranking must be a positive number."
        except ValueError:
            errors["world_ranking"] = "World ranking must be a whole number."

    parsed_qualification_date = None
    if qualification_date_raw:
        try:
            parsed_qualification_date = datetime.strptime(qualification_date_raw, "%Y-%m-%d").date()
            if parsed_qualification_date > date.today():
                errors["qualification_date"] = "Qualification date cannot be in the future."
        except ValueError:
            errors["qualification_date"] = "Enter a valid date (YYYY-MM-DD)."

    if qualification_status not in QUALIFICATION_STATUS_VALUES:
        errors["qualification_status"] = "Select a valid qualification status."

    if qualification_score and len(qualification_score) > 100:
        errors["qualification_score"] = "Score / time must be 100 characters or fewer."
    if qualification_standard and len(qualification_standard) > 100:
        errors["qualification_standard"] = "Standard must be 100 characters or fewer."
    if personal_best and len(personal_best) > 100:
        errors["personal_best"] = "Personal best must be 100 characters or fewer."

    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)

    before_data = AuditLogger.model_to_dict(
        oa, ["athlete_number", "target_olympics", "olympic_status", "event_name"]
    )

    with transaction.atomic():
        oa.athlete = athletic_obj
        oa.sport = sport_obj
        oa.team = team_obj
        oa.coach = coach_obj
        oa.nationality = nationality
        oa.olympic_status = olympic_status
        oa.target_olympics = target_olympics
        oa.event_name = event_name
        oa.event_category = event_category
        oa.governing_body = governing_body
        oa.world_ranking = world_ranking
        oa.qualification_date = parsed_qualification_date
        oa.qualification_score = qualification_score or None
        oa.qualification_standard = qualification_standard or None
        oa.qualification_status = qualification_status
        oa.personal_best = personal_best or None
        oa.biography = biography or None
        oa.save()

    AuditLogger.log(
        request=request,
        action="UPDATE",
        module="OlympicAthleteManagement",
        object_type="OlympicAthlete",
        object_id=oa.id,
        description=f"Updated Olympic athlete targeting {target_olympics}.",
        before_data=before_data,
        after_data=AuditLogger.model_to_dict(
            oa, ["athlete_number", "target_olympics", "olympic_status", "event_name"]
        ),
        status="SUCCESS",
    )

    return JsonResponse({
        "ok": True,
        "message": "Olympic Athlete updated successfully.",
        "athlete_id": oa.id,
        "redirect_url": str(reverse("olympic_athlete_page")),
    })


@login_required
@require_http_methods(["POST"])
def olympic_athlete_create_json(request):
   
    errors = {}

    athlete_id = (request.POST.get("athlete") or "").strip()
    sport_id = (request.POST.get("sport") or "").strip()
    team_id = (request.POST.get("team") or "").strip()
    coach_id = (request.POST.get("coach") or "").strip()
    nationality = (request.POST.get("nationality") or "").strip()
    olympic_status = (request.POST.get("olympic_status") or "").strip() or "PENDING"
    target_olympics = (request.POST.get("target_olympics") or "").strip()
    event_name = (request.POST.get("event_name") or "").strip()
    event_category = (request.POST.get("event_category") or "").strip() or "INDIVIDUAL"
    governing_body = (request.POST.get("governing_body") or "").strip()
    world_ranking_raw = (request.POST.get("world_ranking") or "").strip()
    qualification_date_raw = (request.POST.get("qualification_date") or "").strip()
    qualification_score = (request.POST.get("qualification_score") or "").strip()
    qualification_standard = (request.POST.get("qualification_standard") or "").strip()
    qualification_status = (request.POST.get("qualification_status") or "").strip() or "PENDING"
    personal_best = (request.POST.get("personal_best") or "").strip()
    biography = (request.POST.get("biography") or "").strip()

    athletic_obj = None
    if not athlete_id:
        errors["athlete"] = "Please select an athlete."
    else:
        athletic_obj = Athletic.objects.filter(athlete_id=athlete_id).first()
        if not athletic_obj:
            errors["athlete"] = "Selected athlete does not exist."
        elif OlympicAthlete.objects.filter(athlete_id=athlete_id).exists():
            errors["athlete"] = "This athlete already has an Olympic profile."

    sport_obj = None
    if not sport_id:
        errors["sport"] = "Sport is required."
    else:
        sport_obj = Sport.objects.filter(id=sport_id).first()
        if not sport_obj:
            errors["sport"] = "Select a valid sport."

    team_obj = SportTeamModel.objects.filter(team_id=team_id).first() if team_id else None
    coach_obj = Coach.objects.filter(coach_id=coach_id).first() if coach_id else None

    if not nationality:
        errors["nationality"] = "Nationality is required."
    elif nationality not in COUNTRY_SET:
        errors["nationality"] = "Select a valid nationality."

    if olympic_status not in OLYMPIC_STATUS_VALUES:
        errors["olympic_status"] = "Select a valid Olympic status."

    if not target_olympics:
        errors["target_olympics"] = "Target Olympics is required."
    elif len(target_olympics) > 100:
        errors["target_olympics"] = "Target Olympics must be 100 characters or fewer."

    if not event_name:
        errors["event_name"] = "Event name is required."
    elif len(event_name) > 150:
        errors["event_name"] = "Event name must be 150 characters or fewer."

    if event_category not in EVENT_CATEGORY_VALUES:
        errors["event_category"] = "Select a valid event category."

    if not governing_body:
        errors["governing_body"] = "Governing body is required."
    elif len(governing_body) > 150:
        errors["governing_body"] = "Governing body must be 150 characters or fewer."

    world_ranking = None
    if world_ranking_raw:
        try:
            world_ranking = int(world_ranking_raw)
            if world_ranking <= 0:
                errors["world_ranking"] = "World ranking must be a positive number."
        except ValueError:
            errors["world_ranking"] = "World ranking must be a whole number."

    parsed_qualification_date = None
    if qualification_date_raw:
        try:
            parsed_qualification_date = datetime.strptime(qualification_date_raw, "%Y-%m-%d").date()
            if parsed_qualification_date > date.today():
                errors["qualification_date"] = "Qualification date cannot be in the future."
        except ValueError:
            errors["qualification_date"] = "Enter a valid date (YYYY-MM-DD)."

    if qualification_status not in QUALIFICATION_STATUS_VALUES:
        errors["qualification_status"] = "Select a valid qualification status."

    if qualification_score and len(qualification_score) > 100:
        errors["qualification_score"] = "Score / time must be 100 characters or fewer."
    if qualification_standard and len(qualification_standard) > 100:
        errors["qualification_standard"] = "Standard must be 100 characters or fewer."
    if personal_best and len(personal_best) > 100:
        errors["personal_best"] = "Personal best must be 100 characters or fewer."

    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)

    olympic_athlete = None
    for _attempt in range(5):
        try:
            with transaction.atomic():
                olympic_athlete = OlympicAthlete.objects.create(
                    athlete=athletic_obj,
                    sport=sport_obj,
                    team=team_obj,
                    coach=coach_obj,
                    athlete_number=_generate_next_olympic_athlete_id(),
                    nationality=nationality,
                    olympic_status=olympic_status,
                    target_olympics=target_olympics,
                    event_name=event_name,
                    event_category=event_category,
                    governing_body=governing_body,
                    world_ranking=world_ranking,
                    qualification_date=parsed_qualification_date,
                    qualification_score=qualification_score or None,
                    qualification_standard=qualification_standard or None,
                    qualification_status=qualification_status,
                    personal_best=personal_best or None,
                    biography=biography or None,
                )
            break
        except IntegrityError:
            continue

    if olympic_athlete is None:
        return JsonResponse(
            {"ok": False, "errors": {"athlete_number": "Could not generate a unique Olympic Athlete ID, please retry."}},
            status=409,
        )

    AuditLogger.log(
        request=request,
        action="CREATE",
        module="OlympicAthleteManagement",
        object_type="OlympicAthlete",
        object_id=olympic_athlete.id,
        description=f"Added Olympic athlete targeting {target_olympics}.",
        after_data=AuditLogger.model_to_dict(
            olympic_athlete, ["athlete_number", "target_olympics", "olympic_status", "event_name"]
        ),
        status="SUCCESS",
    )

    return JsonResponse({
        "ok": True,
        "message": "Olympic Athlete added successfully.",
        "athlete_id": olympic_athlete.id,
        "redirect_url": str(reverse("olympic_athlete_page")),
    })




@login_required
def olympic_performance_data_json(request):
   

    show_archived = request.GET.get("archived") == "1"
    
    # performances = OlympicPerformance.objects.select_related(
    #     "olympic_athlete__athlete__student"
    # ).order_by("-competition_date")

    performances = OlympicPerformance.objects.select_related(
        "olympic_athlete__athlete__student"
    ).filter(is_archived=show_archived).order_by("-competition_date")

    data = []
    for p in performances:
        oa = p.olympic_athlete
        full_name = (
            oa.athlete.student.full_name
            if oa and oa.athlete_id and oa.athlete.student_id
            else "Unknown Athlete"
        )
        data.append({
            "id": p.id,
            "uuid": str(p.performance_uuid),
            "athlete": full_name,
            "athlete_no": oa.athlete_number if oa else "—",
            "competition_name": p.competition_name,
            "competition_level": p.competition_level,
            "event_name": p.event_name,
            "competition_date": p.competition_date.strftime("%Y-%m-%d") if p.competition_date else None,
            "host_city": p.host_city,
            "host_country": p.host_country,
            "score_time": p.score_time or "—",
            "ranking": p.ranking,
            "medal": p.medal,
            "participation_status": p.participation_status,
            "remarks": p.remarks or "",
            "created_at": p.created_at.strftime("%Y-%m-%d") if p.created_at else None,
            "updated_at": p.updated_at.strftime("%Y-%m-%d") if p.updated_at else None,
        })

    return JsonResponse({"results": data})

@login_required
@require_http_methods(["POST"])
def olympic_performance_archive_json(request, uuid):
   
    performance = get_object_or_404(OlympicPerformance, performance_uuid=uuid)

    if performance.is_archived:
        return JsonResponse({"ok": False, "message": "Record is already archived."}, status=400)

    performance.is_archived = True
    performance.archived_at = timezone.now()
    performance.save(update_fields=["is_archived", "archived_at", "updated_at"])

    AuditLogger.log(
        request=request,
        action="ARCHIVE",
        module="OlympicPerformanceManagement",
        object_type="OlympicPerformance",
        object_id=performance.id,
        description=f"Archived performance '{performance.competition_name}'.",
        status="SUCCESS",
    )

    return JsonResponse({"ok": True, "message": "Record archived successfully."})


@login_required
@require_http_methods(["POST"])
def olympic_performance_restore_json(request, uuid):
    
    performance = get_object_or_404(OlympicPerformance, performance_uuid=uuid)

    if not performance.is_archived:
        return JsonResponse({"ok": False, "message": "Record is not archived."}, status=400)

    performance.is_archived = False
    performance.archived_at = None
    performance.save(update_fields=["is_archived", "archived_at", "updated_at"])

    AuditLogger.log(
        request=request,
        action="RESTORE",
        module="OlympicPerformanceManagement",
        object_type="OlympicPerformance",
        object_id=performance.id,
        description=f"Restored performance '{performance.competition_name}'.",
        status="SUCCESS",
    )

    return JsonResponse({"ok": True, "message": "Record restored successfully."})

@require_page_access("olympic_performance_page")
@login_required
def olympic_performance_page(request):
    return render(request, "olympic_performance.html")


PERF_LEVEL_VALUES = {c[0] for c in OlympicPerformance.COMPETITION_LEVEL}
PERF_MEDAL_VALUES = {c[0] for c in OlympicPerformance.MEDAL_CHOICES}
PERF_STATUS_VALUES = {c[0] for c in OlympicPerformance.PARTICIPATION_STATUS}



def _build_olympic_performance_form_context(request, performance=None):
    
    athletes = OlympicAthlete.objects.select_related("athlete__student").order_by("athlete_number")

    selected_uuid = (
        str(performance.olympic_athlete.olympic_uuid)
        if performance and performance.olympic_athlete_id else ""
    )

    athlete_options = []
    for oa in athletes:
        full_name = (
            oa.athlete.student.full_name
            if oa.athlete_id and oa.athlete.student_id
            else "Unknown Athlete"
        )

        user_photo = None
        student = getattr(oa.athlete, "student", None) if oa.athlete_id else None
        user_obj = getattr(student, "user", None)
        if user_obj and getattr(user_obj, "profile_photo", None):
            try:
                user_photo = request.build_absolute_uri(user_obj.profile_photo.url)
            except ValueError:
                user_photo = None
        photo_url = user_photo or (
            f"https://ui-avatars.com/api/?name={full_name.replace(' ', '+')}"
            f"&background=0081C8&color=fff&size=128"
        )

        athlete_options.append({
            "uuid": str(oa.olympic_uuid),
            "name": full_name,
            "athlete_number": oa.athlete_number,
            "photo": photo_url,
            "selected": str(oa.olympic_uuid) == selected_uuid,
        })

    return {
        "athlete_options": athlete_options,
        "competition_level_choices": OlympicPerformance.COMPETITION_LEVEL,
        "medal_choices": OlympicPerformance.MEDAL_CHOICES,
        "participation_status_choices": OlympicPerformance.PARTICIPATION_STATUS,
        "countries": COUNTRIES,
        "is_edit": performance is not None,
        "performance_obj": performance,
    }

@require_page_access("oympic_performane_add_page")
@require_permission("olympicperformance_create")
@login_required
def olympic_performance_add_page(request):
   
    context = _build_olympic_performance_form_context(request)
    return render(request, "add_performance.html", context)

@require_page_access("olympic_performance_edit_page")
@require_permission("olympicperformance_update")
@login_required
def olympic_performance_edit_page(request, uuid):
    
    performance = get_object_or_404(
        OlympicPerformance.objects.select_related("olympic_athlete"),
        performance_uuid=uuid,
    )
    context = _build_olympic_performance_form_context(request, performance=performance)
    return render(request, "add_performance.html", context)


@login_required
def olympic_performance_detail_json(request, uuid):
    
    p = get_object_or_404(
        OlympicPerformance.objects.select_related("olympic_athlete__athlete__student"),
        performance_uuid=uuid,
    )
    oa = p.olympic_athlete
    full_name = (
        oa.athlete.student.full_name
        if oa and oa.athlete_id and oa.athlete.student_id
        else "Unknown Athlete"
    )

    user_photo = None
    student = getattr(oa.athlete, "student", None) if oa and oa.athlete_id else None
    user_obj = getattr(student, "user", None)
    if user_obj and getattr(user_obj, "profile_photo", None):
        try:
            user_photo = request.build_absolute_uri(user_obj.profile_photo.url)
        except ValueError:
            user_photo = None
    photo_url = user_photo or (
        f"https://ui-avatars.com/api/?name={full_name.replace(' ', '+')}"
        f"&background=0081C8&color=fff&size=128"
    )

    data = {
        "uuid": str(p.performance_uuid),
        "athlete": full_name,
        "athlete_no": oa.athlete_number if oa else "—",
        "athlete_photo": photo_url,
        "competition_name": p.competition_name,
        "competition_level": p.competition_level,
        "event_name": p.event_name,
        "competition_date": p.competition_date.strftime("%Y-%m-%d") if p.competition_date else None,
        "host_city": p.host_city,
        "host_country": p.host_country,
        "score_time": p.score_time or "—",
        "ranking": p.ranking,
        "medal": p.medal,
        "participation_status": p.participation_status,
        "remarks": p.remarks or "",
        "created_at": p.created_at.strftime("%b %d, %Y") if p.created_at else None,
        "updated_at": p.updated_at.strftime("%b %d, %Y") if p.updated_at else None,
    }
    return JsonResponse({"ok": True, "result": data})


@require_permission("olympicperformance_update")
@login_required
@require_http_methods(["POST"])
def olympic_performance_update_json(request, uuid):
   
    performance = get_object_or_404(OlympicPerformance, performance_uuid=uuid)
    errors = {}

    olympic_athlete_uuid = (request.POST.get("olympic_athlete") or "").strip()
    competition_name = (request.POST.get("competition_name") or "").strip()
    competition_level = (request.POST.get("competition_level") or "").strip()
    event_name = (request.POST.get("event_name") or "").strip()
    competition_date_raw = (request.POST.get("competition_date") or "").strip()
    host_city = (request.POST.get("host_city") or "").strip()
    host_country = (request.POST.get("host_country") or "").strip()
    score_time = (request.POST.get("score_time") or "").strip()
    ranking_raw = (request.POST.get("ranking") or "").strip()
    medal = (request.POST.get("medal") or "").strip() or "NONE"
    participation_status = (request.POST.get("participation_status") or "").strip() or "SCHEDULED"
    remarks = (request.POST.get("remarks") or "").strip()

    olympic_athlete_obj = None
    if not olympic_athlete_uuid:
        errors["olympic_athlete"] = "Please select an Olympic athlete."
    else:
        olympic_athlete_obj = OlympicAthlete.objects.filter(olympic_uuid=olympic_athlete_uuid).first()
        if not olympic_athlete_obj:
            errors["olympic_athlete"] = "Selected athlete does not exist."

    if not competition_name:
        errors["competition_name"] = "Competition name is required."
    elif len(competition_name) > 150:
        errors["competition_name"] = "Competition name must be 150 characters or fewer."

    if competition_level not in PERF_LEVEL_VALUES:
        errors["competition_level"] = "Select a valid competition level."

    if not event_name:
        errors["event_name"] = "Event name is required."
    elif len(event_name) > 150:
        errors["event_name"] = "Event name must be 150 characters or fewer."

    parsed_competition_date = None
    if not competition_date_raw:
        errors["competition_date"] = "Competition date is required."
    else:
        try:
            parsed_competition_date = datetime.strptime(competition_date_raw, "%Y-%m-%d").date()
        except ValueError:
            errors["competition_date"] = "Enter a valid date (YYYY-MM-DD)."

    if not host_city:
        errors["host_city"] = "Host city is required."
    elif len(host_city) > 100:
        errors["host_city"] = "Host city must be 100 characters or fewer."

    if not host_country:
        errors["host_country"] = "Host country is required."
    elif len(host_country) > 100:
        errors["host_country"] = "Host country must be 100 characters or fewer."

    if score_time and len(score_time) > 100:
        errors["score_time"] = "Score / time must be 100 characters or fewer."

    ranking = None
    if ranking_raw:
        try:
            ranking = int(ranking_raw)
            if ranking <= 0:
                errors["ranking"] = "Ranking must be a positive number."
        except ValueError:
            errors["ranking"] = "Ranking must be a whole number."

    if medal not in PERF_MEDAL_VALUES:
        errors["medal"] = "Select a valid medal."

    if participation_status not in PERF_STATUS_VALUES:
        errors["participation_status"] = "Select a valid participation status."

    if remarks and len(remarks) > 5000:
        errors["remarks"] = "Remarks are too long."

    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)

    before_data = AuditLogger.model_to_dict(
        performance, ["competition_name", "competition_level", "event_name", "medal", "participation_status"]
    )

    with transaction.atomic():
        performance.olympic_athlete = olympic_athlete_obj
        performance.competition_name = competition_name
        performance.competition_level = competition_level
        performance.event_name = event_name
        performance.competition_date = parsed_competition_date
        performance.host_city = host_city
        performance.host_country = host_country
        performance.score_time = score_time or None
        performance.ranking = ranking
        performance.medal = medal
        performance.participation_status = participation_status
        performance.remarks = remarks or None
        performance.save()

    AuditLogger.log(
        request=request,
        action="UPDATE",
        module="OlympicPerformanceManagement",
        object_type="OlympicPerformance",
        object_id=performance.id,
        description=f"Updated performance '{performance.competition_name}' for {olympic_athlete_obj}.",
        before_data=before_data,
        after_data=AuditLogger.model_to_dict(
            performance, ["competition_name", "competition_level", "event_name", "medal", "participation_status"]
        ),
        status="SUCCESS",
    )

    return JsonResponse({
        "ok": True,
        "message": "Olympic Performance updated successfully.",
        "performance_id": performance.id,
        "redirect_url": str(reverse("olympic_performance_page")),
    })


    

@login_required
@require_http_methods(["POST"])
def olympic_performance_create_json(request):
   
    errors = {}

    olympic_athlete_uuid = (request.POST.get("olympic_athlete") or "").strip()
    competition_name = (request.POST.get("competition_name") or "").strip()
    competition_level = (request.POST.get("competition_level") or "").strip()
    event_name = (request.POST.get("event_name") or "").strip()
    competition_date_raw = (request.POST.get("competition_date") or "").strip()
    host_city = (request.POST.get("host_city") or "").strip()
    host_country = (request.POST.get("host_country") or "").strip()
    score_time = (request.POST.get("score_time") or "").strip()
    ranking_raw = (request.POST.get("ranking") or "").strip()
    medal = (request.POST.get("medal") or "").strip() or "NONE"
    participation_status = (request.POST.get("participation_status") or "").strip() or "SCHEDULED"
    remarks = (request.POST.get("remarks") or "").strip()

    olympic_athlete_obj = None
    if not olympic_athlete_uuid:
        errors["olympic_athlete"] = "Please select an Olympic athlete."
    else:
        olympic_athlete_obj = OlympicAthlete.objects.filter(olympic_uuid=olympic_athlete_uuid).first()
        if not olympic_athlete_obj:
            errors["olympic_athlete"] = "Selected athlete does not exist."

    if not competition_name:
        errors["competition_name"] = "Competition name is required."
    elif len(competition_name) > 150:
        errors["competition_name"] = "Competition name must be 150 characters or fewer."

    if competition_level not in PERF_LEVEL_VALUES:
        errors["competition_level"] = "Select a valid competition level."

    if not event_name:
        errors["event_name"] = "Event name is required."
    elif len(event_name) > 150:
        errors["event_name"] = "Event name must be 150 characters or fewer."

    parsed_competition_date = None
    if not competition_date_raw:
        errors["competition_date"] = "Competition date is required."
    else:
        try:
            parsed_competition_date = datetime.strptime(competition_date_raw, "%Y-%m-%d").date()
        except ValueError:
            errors["competition_date"] = "Enter a valid date (YYYY-MM-DD)."

    if not host_city:
        errors["host_city"] = "Host city is required."
    elif len(host_city) > 100:
        errors["host_city"] = "Host city must be 100 characters or fewer."

    if not host_country:
        errors["host_country"] = "Host country is required."
    elif len(host_country) > 100:
        errors["host_country"] = "Host country must be 100 characters or fewer."

    

    if score_time and len(score_time) > 100:
        errors["score_time"] = "Score / time must be 100 characters or fewer."

  
    ranking = None
    if ranking_raw:
        try:
            ranking = int(ranking_raw)
            if ranking <= 0:
                errors["ranking"] = "Ranking must be a positive number."
        except ValueError:
            errors["ranking"] = "Ranking must be a whole number."

    if medal not in PERF_MEDAL_VALUES:
        errors["medal"] = "Select a valid medal."

    if participation_status not in PERF_STATUS_VALUES:
        errors["participation_status"] = "Select a valid participation status."

    if remarks and len(remarks) > 5000:
        errors["remarks"] = "Remarks are too long."

    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)

    performance = OlympicPerformance.objects.create(
        olympic_athlete=olympic_athlete_obj,
        competition_name=competition_name,
        competition_level=competition_level,
        event_name=event_name,
        competition_date=parsed_competition_date,
        host_city=host_city,
        host_country=host_country,
        # score_time=score_time,
        score_time=score_time or None,
        ranking=ranking,
        medal=medal,
        participation_status=participation_status,
        remarks=remarks or None,
    )

    AuditLogger.log(
        request=request,
        action="CREATE",
        module="OlympicPerformanceManagement",
        object_type="OlympicPerformance",
        object_id=performance.id,
        description=f"Added performance '{performance.competition_name}' for {olympic_athlete_obj}.",
        after_data=AuditLogger.model_to_dict(
            performance, ["competition_name", "competition_level", "event_name", "medal", "participation_status"]
        ),
        status="SUCCESS",
    )

    return JsonResponse({
        "ok": True,
        "message": "Olympic Performance added successfully.",
        "performance_id": performance.id,
        "redirect_url": str(reverse("olympic_performance_page")),
    })



@require_page_access("tournament_page")
@login_required
def tournament_dashboard_page(request):
    tournaments_qs = (
        Tournament.objects.select_related("sport", "venue")
        .order_by("-created_at")
    )
    invitations_qs = (
        TournamentInvitation.objects.select_related("tournament")
        .order_by("-invitation_sent_at")
    )
    participants_qs = (
        TournamentParticipant.objects.select_related(
            "tournament", "internal_team", "internal_athlete", "invitation__application"
        ).order_by("-registered_at")
    )

    UPCOMING_STATUSES = ["CREATED", "INVITATION_SENT", "REGISTRATION_OPEN", "REGISTRATION_CLOSED"]
    ACTIVE_STATUSES = ["VERIFICATION", "APPROVED", "FIXTURES_READY", "ONGOING"]

    total_tournaments_count = tournaments_qs.count()
    active_tournaments_count = tournaments_qs.filter(status__in=ACTIVE_STATUSES).count()
    upcoming_tournaments_count = tournaments_qs.filter(status__in=UPCOMING_STATUSES).count()
    completed_tournaments_count = tournaments_qs.filter(status="COMPLETED").count()
    invitations_sent_count = invitations_qs.count()
    approved_participants_count = invitations_qs.filter(application_status="APPROVED").count()
    pending_applications_count = invitations_qs.filter(application_status="APPLIED").count()
    total_registered_participants_count = (
        participants_qs.aggregate(total=Sum("players_count"))["total"] or 0
    )

   
    tournaments_data = []
    for t in tournaments_qs:
        tournaments_data.append({
            "tournament_name": t.tournament_name,
            "tournament_code": t.tournament_code,
            "sport": t.sport.sport_name if t.sport else "—",
            "tournament_type": t.tournament_type,
            "participation_type": t.participation_type,
            
            "venue": getattr(t.venue, "facility_name", str(t.venue)) if t.venue else "—",
            "start_date": t.start_date.isoformat() if t.start_date else None,
            "end_date": t.end_date.isoformat() if t.end_date else None,
            "registration_deadline": (
                t.registration_deadline.isoformat()
                if t.registration_deadline else None
            ),
            "status": t.status,
            "registered_participants": t.participants.count(),
            "maximum_participants": t.maximum_participants,
            "tournament_uuid": str(t.tournament_uuid),
            "tournament_name": t.tournament_name,
        })

    invitations_data = []
    for inv in invitations_qs:
        invitations_data.append({
            "invitation_uuid": str(inv.invitation_uuid),
            "tournament": inv.tournament.tournament_name if inv.tournament else "—",
            "college_name": inv.college_name or "—",
            "department_name": inv.department_name or "—",
            "contact_person": inv.contact_person or "—",
            "email": inv.email,
            "application_status": inv.application_status,
            "invitation_sent_at": (
                inv.invitation_sent_at.date().isoformat() if inv.invitation_sent_at else None
            ),
        })

    participants_data = []
    for p in participants_qs:
        # NOTE: adjust `internal_team.team_name` below if SportTeamModel uses a different display field.
        team_name = getattr(p.internal_team, "team_name", str(p.internal_team)) if p.internal_team else "—"
        
        athlete_name = "—"
        if p.internal_athlete:
            athlete_name, _ = _athletic_display(p.internal_athlete)
     

        application = getattr(p.invitation, "application", None)
        players_list = application.players if (application and application.players) else []
        participants_data.append({
            "participant_name": p.participant_name,

            "team_name": p.team_name or "—",
            "tournament": p.tournament.tournament_name if p.tournament else "—",
            "tournament_type": (
                p.tournament.tournament_type
                if p.tournament else None
            ),
            "participation_type": p.tournament.participation_type if p.tournament else None,
            "college_name": p.college_name or "—",
            "internal_team": team_name,
            "internal_athlete": athlete_name,
            "coach_name": p.coach_name or "—",
            "players_count": p.players_count,
            "players": players_list,
            "final_position": p.final_position,
            "result": p.result,
            "registered_at": p.registered_at.date().isoformat() if p.registered_at else None,
        })

   
    status_counts = Counter(t.status for t in tournaments_qs)
    status_labels = [c[0] for c in Tournament.STATUS_CHOICES if status_counts.get(c[0])]
    status_chart = {
        "labels": [dict(Tournament.STATUS_CHOICES)[s] for s in status_labels],
        "data": [status_counts[s] for s in status_labels],
    }

    type_counts = Counter(t.tournament_type for t in tournaments_qs)
    type_labels = [c[0] for c in Tournament.TOURNAMENT_TYPE if type_counts.get(c[0])]
    type_chart = {
        "labels": [dict(Tournament.TOURNAMENT_TYPE)[t] for t in type_labels],
        "data": [type_counts[t] for t in type_labels],
    }

    month_labels = [m for m in month_abbr if m]  # Jan..Dec
    monthly_counts = Counter()
    for t in tournaments_qs:
        if t.created_at:
            monthly_counts[t.created_at.strftime("%b")] += 1
    monthly_chart = {
        "labels": month_labels,
        "data": [monthly_counts.get(m, 0) for m in month_labels],
    }

    invitation_status_counts = Counter(inv.application_status for inv in invitations_qs)
    invitation_status_labels = [
        c[0] for c in TournamentInvitation.APPLICATION_STATUS if invitation_status_counts.get(c[0])
    ]
    invitation_status_chart = {
        "labels": [dict(TournamentInvitation.APPLICATION_STATUS)[s] for s in invitation_status_labels],
        "data": [invitation_status_counts[s] for s in invitation_status_labels],
    }

    growth_counts = Counter()
    for p in participants_qs:
        if p.registered_at:
            growth_counts[p.registered_at.strftime("%b")] += p.players_count
    growth_chart = {
        "labels": month_labels,
        "data": [growth_counts.get(m, 0) for m in month_labels],
    }

    context = {
        "total_tournaments_count": total_tournaments_count,
        "active_tournaments_count": active_tournaments_count,
        "upcoming_tournaments_count": upcoming_tournaments_count,
        "completed_tournaments_count": completed_tournaments_count,
        "invitations_sent_count": invitations_sent_count,
        "approved_participants_count": approved_participants_count,
        "pending_applications_count": pending_applications_count,
        "total_registered_participants_count": total_registered_participants_count,
        "tournament_dashboard_data": {
            "tournaments": tournaments_data,
            "invitations": invitations_data,
            "participants": participants_data,
            "charts": {
                "status_distribution": status_chart,
                "type_distribution": type_chart,
                "monthly_creation": monthly_chart,
                "invitation_status": invitation_status_chart,
                "participant_growth": growth_chart,
            },
        },
    }

    return render(request, "Tournament.html", context)


@require_page_access("tournament_view_page")

@login_required
def tournament_view(request, tournament_uuid):
    tournament = get_object_or_404(
        Tournament.objects.select_related("sport", "club", "venue", "organizer"),
        tournament_uuid=tournament_uuid,
    )

    context = {
        "tournament": tournament,
        "sport_name": tournament.sport.sport_name if tournament.sport else "—",
        "club_name": getattr(tournament.club, "club_name", str(tournament.club)) if tournament.club else "—",
        "venue_name": getattr(tournament.venue, "facility_name", str(tournament.venue)) if tournament.venue else "—",
        "tournament_type_label": dict(Tournament.TOURNAMENT_TYPE).get(
            tournament.tournament_type, tournament.tournament_type
        ),
        "status_label": dict(Tournament.STATUS_CHOICES).get(tournament.status, tournament.status),
        "registered_participants_count": tournament.participants.count(),
    }

    AuditLogger.log(
        request=request,
        action="VIEW",
        module="Tournament",
        object_type="Tournament",
        object_id=tournament.id,
        description=f"Viewed tournament '{tournament.tournament_name}'.",
        status="SUCCESS",
    )

    return render(request, "tournament_view.html", context)


@login_required
@require_permission("tournament_update")
@require_http_methods(["POST"])
def tournament_complete_json(request, tournament_uuid):
    with transaction.atomic():
        tournament = get_object_or_404(
            Tournament.objects.select_for_update(),
            tournament_uuid=tournament_uuid,
        )

        if tournament.status == "COMPLETED":
            return JsonResponse({
                "tournament_uuid": str(tournament.tournament_uuid),
                "status": tournament.status,
            })

        tournament.status = "COMPLETED"
        tournament.save(update_fields=["status", "updated_at"])

    AuditLogger.log(
        request=request,
        action="UPDATE",
        module="Tournament",
        object_type="Tournament",
        object_id=tournament.id,
        description=f"Marked tournament '{tournament.tournament_name}' as Completed.",
        status="SUCCESS",
    )

    return JsonResponse({
        "tournament_uuid": str(tournament.tournament_uuid),
        "status": tournament.status,
    })



@login_required
def tournament_invitation_detail_json(request, invitation_uuid):
    invitation = get_object_or_404(
        TournamentInvitation.objects.select_related("tournament"),
        invitation_uuid=invitation_uuid,
    )

    application = getattr(invitation, "application", None)

    
    applied_at_dt = (application.applied_at if application else None) or invitation.applied_at

    data = {
        "invitation_uuid": str(invitation.invitation_uuid),
        "tournament": invitation.tournament.tournament_name if invitation.tournament else "—",
        "participation_type": invitation.tournament.participation_type if invitation.tournament else None,
        "college_name": invitation.college_name or "—",
        "department_name": invitation.department_name or "—",
        "contact_person": invitation.contact_person or "—",
        "email": invitation.email,
        "mobile_number": invitation.mobile_number or "—",
        "application_status": invitation.application_status,
        "invitation_sent_at": invitation.invitation_sent_at.isoformat() if invitation.invitation_sent_at else None,
        "applied_at": applied_at_dt.isoformat() if applied_at_dt else None,
        "applied_at_display": (
            timezone.localtime(applied_at_dt).strftime("%d %b %Y, %I:%M %p") if applied_at_dt else "—"
        ),
        "application": None,
    }

    if application:
       
        raw_players = application.players or []
        players = []
        for p in raw_players:
            if isinstance(p, dict):
                name = (p.get("name") or p.get("player_name") or "").strip()
            else:
                name = str(p).strip()
            if name:
                players.append(name)

        data["application"] = {
            "entry_name": application.entry_name or "—",
            "team_name": application.team_name or "—",
            "coach_name": application.coach_name or "—",
            "contact_person": application.contact_person or "—",
            "contact_mobile": application.contact_mobile or "—",
            "players_count": application.players_count,
            "players": players,
            "faculty_remarks": application.faculty_remarks or "",
            "status": application.status,
            "admin_remarks": application.admin_remarks or "",
            "applied_at": application.applied_at.isoformat() if application.applied_at else None,
        }

    return JsonResponse(data)



@login_required
@require_permission("tournamentinvitation_update")
@require_http_methods(["POST"])
def tournament_invitation_action_json(request, invitation_uuid):
   
    action = request.POST.get("action")
    if action not in ("accept", "reject"):
        return JsonResponse({"error": "Invalid action."}, status=400)

    with transaction.atomic():
        invitation = get_object_or_404(
            TournamentInvitation.objects.select_for_update().select_related("tournament"),
            invitation_uuid=invitation_uuid,
        )

        if invitation.application_status in ("APPROVED", "REJECTED"):
            return JsonResponse({
                "invitation_uuid": str(invitation.invitation_uuid),
                "application_status": invitation.application_status,
            })

        application = getattr(invitation, "application", None)

       

        if action == "accept":
            if not application:
                return JsonResponse({"error": "No application found for this invitation."}, status=400)
            if application.status != "APPLIED" or invitation.application_status != "APPLIED":
                return JsonResponse({"error": "This application is not pending review."}, status=400)

            tournament = invitation.tournament

            if tournament.participation_type == "TEAM":
                team_name = (application.team_name or "").strip()
                if not team_name:
                    return JsonResponse({"error": "Application is missing a team name."}, status=400)
                entry_name = ""  
            else:
                entry_name = (application.entry_name or "").strip()
                if not entry_name:
                    return JsonResponse({"error": "Application is missing a valid entry name."}, status=400)
                team_name = None

            if tournament.participation_type == "TEAM":
                min_p = tournament.minimum_participants or 1
                max_p = tournament.maximum_participants or min_p
                if application.players_count < min_p or application.players_count > max_p:
                    return JsonResponse({"error": "Submitted player count is outside the allowed range."}, status=400)
            else:
                if application.players_count != 1:
                    return JsonResponse({"error": "Individual application must have exactly one participant."}, status=400)

            participant, _ = TournamentParticipant.objects.update_or_create(
                invitation=invitation,
                defaults={
                    "tournament": application.tournament,
                    "internal_team": application.internal_team,   
                    "team_name": team_name,                       
                    "participant_name": entry_name,
                    "college_name": invitation.college_name,
                    "coach_name": application.coach_name,
                    "players_count": application.players_count,
                }
            )
            transaction.on_commit(lambda p=participant: broadcast_participant_added(p))



            invitation.application_status = "APPROVED"
            invitation.approved_at = timezone.now()
            invitation.save(update_fields=["application_status", "approved_at"])

            application.status = "APPROVED"
            application.reviewed_at = timezone.now()
            application.reviewed_by = request.user
            application.participant = participant
            application.save(update_fields=["status", "reviewed_at", "reviewed_by", "participant"])

        else:  
            invitation.application_status = "REJECTED"
            invitation.save(update_fields=["application_status"])

            if application:
                application.status = "REJECTED"
                application.reviewed_at = timezone.now()
                application.reviewed_by = request.user
                application.save(update_fields=["status", "reviewed_at", "reviewed_by"])

        transaction.on_commit(lambda inv=invitation: broadcast_invitation_status(inv))

    return JsonResponse({
        "invitation_uuid": str(invitation.invitation_uuid),
        "application_status": invitation.application_status,
    })



@require_page_access("create_tournament_page")
@require_permission("tournament_create")
@login_required
def tournament_create_page(request):
    sports = Sport.objects.filter(is_active=True).order_by("sport_name")
    clubs = SportClub.objects.filter(is_active=True).select_related("sport").order_by("club_name")
    venues = SportsFacility.objects.filter(status="ACTIVE").order_by("facility_name")

    clubs_data = [
        {"id": c.id, "name": c.club_name, "sport_id": c.sport_id}
        for c in clubs
    ]
    venues_data = [
        {"id": v.facility_id, "name": v.facility_name, "sport_id": v.sport_id}
        for v in venues
    ]

    context = {
        "sports": sports,
        "clubs_data": clubs_data,
        "venues_data": venues_data,
        "tournament_type_choices": Tournament.TOURNAMENT_TYPE,
        "participation_type_choices": Tournament.PARTICIPATION_TYPE,
        "status_choices": Tournament.STATUS_CHOICES,
        "invitation_type_choices": TournamentInvitation.INVITATION_TYPE,
    }
    return render(request, "create_tournament.html", context)


def _send_tournament_invitation_email(request, tournament, invitation):
   
    if not invitation.email:
        return False

    # apply_url = request.build_absolute_uri(f"/tournaments/apply/{invitation.invitation_token}/")
    apply_url = request.build_absolute_uri(
        reverse(
            "email_tournament_apply_page",
            kwargs={
                "invitation_token": invitation.invitation_token
            }
        )
    )

    context = {
        "tournament": tournament,
        "invitation": invitation,
        "apply_url": apply_url,
        "has_banner": bool(tournament.banner),
        "has_rules_pdf": bool(tournament.rules_pdf),
    }
    html_body = render_to_string("tournament_invitation_email.html", context)
    text_body = (
        f"You're invited to {tournament.tournament_name} ({tournament.tournament_code}).\n"
        f"Sport: {tournament.sport.sport_name if tournament.sport else '-'}\n"
        f"Dates: {tournament.start_date} to {tournament.end_date}\n"
        f"Registration deadline: {tournament.registration_deadline}\n"
        f"Apply here: {apply_url}\n"
    )

    try:
        msg = EmailMultiAlternatives(
            subject=f"You're invited: {tournament.tournament_name}",
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[invitation.email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.mixed_subtype = "related"  

        if tournament.banner and os.path.exists(tournament.banner.path):
            with open(tournament.banner.path, "rb") as banner_fh:
                banner_image = MIMEImage(banner_fh.read())
                banner_image.add_header("Content-ID", "<tournament_banner>")
                banner_image.add_header(
                    "Content-Disposition", "inline", filename=os.path.basename(tournament.banner.name)
                )
                msg.attach(banner_image)

        if tournament.rules_pdf and os.path.exists(tournament.rules_pdf.path):
            with open(tournament.rules_pdf.path, "rb") as rules_fh:
                msg.attach(os.path.basename(tournament.rules_pdf.name), rules_fh.read(), "application/pdf")

        msg.send(fail_silently=False)
        return True
    except Exception:
        logger.exception(
            "Failed to send tournament invitation email to %s for tournament %s",
            invitation.email, tournament.tournament_code,
        )
        return False


@login_required
@require_http_methods(["POST"])
def tournament_create_json(request):
    errors = {}

    tournament_name = (request.POST.get("tournament_name") or "").strip()
    tournament_code = (request.POST.get("tournament_code") or "").strip()
    sport_id = (request.POST.get("sport") or "").strip()
    club_id = (request.POST.get("club") or "").strip()
    venue_id = (request.POST.get("venue") or "").strip()
    tournament_type = (request.POST.get("tournament_type") or "").strip()
    participation_type = (request.POST.get("participation_type") or "").strip()
    description = (request.POST.get("description") or "").strip()
    start_date_raw = (request.POST.get("start_date") or "").strip()
    end_date_raw = (request.POST.get("end_date") or "").strip()
    registration_deadline_raw = (request.POST.get("registration_deadline") or "").strip()
    minimum_participants_raw = (request.POST.get("minimum_participants") or "").strip()
    maximum_participants_raw = (request.POST.get("maximum_participants") or "").strip()
    entry_fee_raw = (request.POST.get("entry_fee") or "").strip()
    status = (request.POST.get("status") or "").strip() or "CREATED"

    invitation_type = (request.POST.get("invitation_type") or "").strip() or "EMAIL"
    college_name = (request.POST.get("college_name") or "").strip()
    department_name = (request.POST.get("department_name") or "").strip()
    contact_person = (request.POST.get("contact_person") or "").strip()
    mobile_number = (request.POST.get("mobile_number") or "").strip()
    remarks = (request.POST.get("remarks") or "").strip()
    college_id = (request.POST.get("college_id") or "").strip()
    department_id = (request.POST.get("department_id") or "").strip()
    receiver_ids_raw = request.POST.get("receiver_faculty_ids") or "[]"

    banner_file = request.FILES.get("banner")
    logo_file = request.FILES.get("logo")
    rules_file = request.FILES.get("rules_pdf")

    if not tournament_name:
        errors["tournament_name"] = "Tournament name is required."
    elif len(tournament_name) > 200:
        errors["tournament_name"] = "Tournament name must be 200 characters or fewer."

    if not tournament_code:
        errors["tournament_code"] = "Tournament code is required."
    elif len(tournament_code) > 30:
        errors["tournament_code"] = "Tournament code must be 30 characters or fewer."
    elif Tournament.objects.filter(tournament_code__iexact=tournament_code).exists():
        errors["tournament_code"] = "This tournament code is already in use."

    sport_obj = None
    if not sport_id:
        errors["sport"] = "Sport is required."
    else:
        sport_obj = Sport.objects.filter(id=sport_id, is_active=True).first()
        if not sport_obj:
            errors["sport"] = "Select a valid, active sport."

    club_obj = None
    if club_id:
        club_obj = SportClub.objects.filter(id=club_id, is_active=True).first()
        if not club_obj:
            errors["club"] = "Select a valid club."
        elif sport_obj and club_obj.sport_id != sport_obj.id:
            errors["club"] = "Selected club does not belong to the selected sport."

    venue_obj = None
    if venue_id:
        venue_obj = SportsFacility.objects.filter(facility_id=venue_id, status="ACTIVE").first()
        if not venue_obj:
            errors["venue"] = "Select a valid venue."

    if tournament_type not in dict(Tournament.TOURNAMENT_TYPE):
        errors["tournament_type"] = "Select a valid tournament type."

    if participation_type not in dict(Tournament.PARTICIPATION_TYPE):
        errors["participation_type"] = "Select a valid participation type."

    if status not in dict(Tournament.STATUS_CHOICES):
        errors["status"] = "Select a valid status."

    def parse_required_date(raw, field):
        if not raw:
            errors[field] = "This date is required."
            return None
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            errors[field] = "Enter a valid date (YYYY-MM-DD)."
            return None

    start_date = parse_required_date(start_date_raw, "start_date")
    end_date = parse_required_date(end_date_raw, "end_date")
    registration_deadline = parse_required_date(registration_deadline_raw, "registration_deadline")

    if start_date and end_date and start_date > end_date:
        errors["end_date"] = "End date cannot be before the start date."
    if registration_deadline and start_date and registration_deadline > start_date:
        errors["registration_deadline"] = "Registration deadline cannot be after the start date."

    minimum_participants = None
    maximum_participants = None
 
    if participation_type != "INDIVIDUAL":

        if not minimum_participants_raw:
            errors["minimum_participants"] = "Minimum participants is required."
        else:
            try:
                minimum_participants = int(minimum_participants_raw)

                if minimum_participants < 1:
                    errors["minimum_participants"] = (
                        "Minimum participants must be at least 1."
                    )

            except ValueError:
                errors["minimum_participants"] = (
                    "Minimum participants must be a whole number."
                )

        if not maximum_participants_raw:
            errors["maximum_participants"] = "Maximum participants is required."
        else:
            try:
                maximum_participants = int(maximum_participants_raw)

                if maximum_participants < 1:
                    errors["maximum_participants"] = (
                        "Maximum participants must be at least 1."
                    )

                elif (
                    minimum_participants is not None
                    and maximum_participants < minimum_participants
                ):
                    errors["maximum_participants"] = (
                        "Maximum participants must be greater than "
                        "or equal to the minimum."
                    )

            except ValueError:
                errors["maximum_participants"] = (
                    "Maximum participants must be a whole number."
                )


    entry_fee = Decimal("0")
    if entry_fee_raw:
        try:
            entry_fee = Decimal(entry_fee_raw)
            if entry_fee < 0:
                errors["entry_fee"] = "Entry fee cannot be negative."
        except InvalidOperation:
            errors["entry_fee"] = "Enter a valid entry fee."

    if invitation_type not in dict(TournamentInvitation.INVITATION_TYPE):
        errors["invitation_type"] = "Select a valid invitation type."

    college_mode = False
    is_other_college = False
    school_obj = None
    department_obj = None
    receiver_faculties = []

    if invitation_type == "DEPARTMENT":
        if tournament_type and tournament_type not in DEPARTMENT_ONLY_TOURNAMENT_TYPES + COLLEGE_TOURNAMENT_TYPES:
            errors["invitation_type"] = (
                "Department invitations are only available for Inter Department, "
                "Intra Department, Inter College and Intra College tournaments."
            )
        elif tournament_type in COLLEGE_TOURNAMENT_TYPES:
            college_mode = True
            is_other_college = (not college_id) or college_id == "OTHER"

            if is_other_college:
                if not college_name:
                    errors["college_name"] = "Enter the college name."
                if not department_name:
                    errors["department_name"] = "Enter the department name."
            else:
                school_obj = School.objects.filter(school_id=college_id, status="ACTIVE").first()
                if not school_obj:
                    errors["college_id"] = "Select a valid college."

                if not department_id:
                    errors["department_id"] = "Select a department."
                elif school_obj:
                    department_obj = Department.objects.filter(
                        department_id=department_id, school_id=school_obj.school_id, status="ACTIVE"
                    ).first()
                    if not department_obj:
                        errors["department_id"] = "Select a valid department for the chosen college."

                if school_obj and department_obj:
                    try:
                        receiver_ids = json.loads(receiver_ids_raw)
                        if not isinstance(receiver_ids, list):
                            raise ValueError
                    except (ValueError, TypeError):
                        receiver_ids = []

                    receiver_faculties = list(
                        FacultyProfile.objects.filter(
                            id__in=receiver_ids,
                            department_id=department_obj.department_id,
                            employment_status="ACTIVE",
                        ).select_related("user", "faculty_rank")
                    )
                    if not receiver_faculties:
                        errors["receiver_faculty_ids"] = "Select at least one receiver."

                college_name = school_obj.school_name if school_obj else college_name
                department_name = department_obj.department_name if department_obj else department_name

    emails_raw = request.POST.get("emails") or "[]"
    try:
        email_list = json.loads(emails_raw)
        if not isinstance(email_list, list):
            raise ValueError
    except (ValueError, TypeError):
        email_list = []
        errors["emails"] = "Could not read the recipient list. Please re-add the emails."

    clean_emails = []
    seen = set()
    for raw_email in email_list:
        candidate = (raw_email or "").strip()
        if not candidate:
            continue
        key = candidate.lower()
        if key in seen:
            continue
        try:
            validate_email(candidate)
        except ValidationError:
            errors["emails"] = f'"{candidate}" is not a valid email address.'
            break
        seen.add(key)
        clean_emails.append(candidate)

    if not errors.get("emails") and not clean_emails and not (college_mode and not is_other_college):
        errors["emails"] = "Add at least one recipient email."

    ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}
    MAX_IMAGE_SIZE = 5 * 1024 * 1024
    MAX_PDF_SIZE = 10 * 1024 * 1024

    if banner_file:
        if banner_file.content_type not in ALLOWED_IMAGE_TYPES:
            errors["banner"] = "Banner must be a PNG, JPG or WEBP image."
        elif banner_file.size > MAX_IMAGE_SIZE:
            errors["banner"] = "Banner must be 5 MB or smaller."

    if logo_file:
        if logo_file.content_type not in ALLOWED_IMAGE_TYPES:
            errors["logo"] = "Logo must be a PNG, JPG or WEBP image."
        elif logo_file.size > MAX_IMAGE_SIZE:
            errors["logo"] = "Logo must be 5 MB or smaller."

    if rules_file:
        if rules_file.content_type != "application/pdf":
            errors["rules_pdf"] = "Rules document must be a PDF file."
        elif rules_file.size > MAX_PDF_SIZE:
            errors["rules_pdf"] = "Rules document must be 10 MB or smaller."

    if errors:
        return JsonResponse(
            {"ok": False, "message": "Please fix the highlighted fields.", "errors": errors}, status=400
        )

    try:
        with transaction.atomic():
            tournament = Tournament.objects.create(
                organizer=request.user,
                sport=sport_obj,
                club=club_obj,
                venue=venue_obj,
                tournament_name=tournament_name,
                tournament_code=tournament_code,
                tournament_type=tournament_type,
                participation_type=participation_type,
                banner=banner_file,
                logo=logo_file,
                description=description,
                rules_pdf=rules_file,
                start_date=start_date,
                end_date=end_date,
                registration_deadline=registration_deadline,
                minimum_participants=minimum_participants,
                maximum_participants=maximum_participants,
                entry_fee=entry_fee,
                status=status,
            )

            invitations = []
            if college_mode and not is_other_college and receiver_faculties:
                for faculty in receiver_faculties:
                    invitation = TournamentInvitation.objects.create(
                        tournament=tournament,
                        invitation_type=invitation_type,
                        college_name=college_name or None,
                        department_name=department_name or None,
                        contact_person=contact_person or None,
                        email=faculty.email,
                        mobile_number=mobile_number,
                        receiver_faculty=faculty,
                        application_status="INVITED",
                        remarks=remarks or None,
                    )
                    invitations.append(invitation)
            else:
                for email_addr in clean_emails:
                    invitation = TournamentInvitation.objects.create(
                        tournament=tournament,
                        invitation_type=invitation_type,
                        college_name=college_name or None,
                        department_name=department_name or None,
                        contact_person=contact_person or None,
                        email=email_addr,
                        mobile_number=mobile_number,
                        application_status="INVITED",
                        remarks=remarks or None,
                    )
                    invitations.append(invitation)
    
    except IntegrityError as e:
        logger.exception("Tournament creation failed due to IntegrityError")

        return JsonResponse(
            {
                "ok": False,
                "message": "Could not create tournament.",
                "errors": {
                    "general": "A database error occurred while creating the tournament."
                },
                "debug": str(e),
            },
            status=500,
        )
    
    AuditLogger.log(
        request=request,
        action="CREATE",
        module="TournamentManagement",
        object_type="Tournament",
        object_id=tournament.id,
        description=f"Created tournament '{tournament.tournament_name}' with {len(invitations)} invitation(s).",
        after_data=AuditLogger.model_to_dict(
            tournament, ["tournament_name", "tournament_code", "tournament_type", "status"]
        ),
        status="SUCCESS",
    )

    emails_sent = 0
    emails_failed = 0

    if college_mode and not is_other_college and receiver_faculties:
        for invitation in invitations:
            notify_faculty_new_tournament_invitation(invitation)
        message = f"Tournament created successfully. {len(invitations)} invitation(s) sent."
    else:
        for invitation in invitations:
            if _send_tournament_invitation_email(request, tournament, invitation):
                emails_sent += 1
            else:
                emails_failed += 1
        message = f"Tournament created successfully. {emails_sent} invitation(s) sent."
        if emails_failed:
            message += f" {emails_failed} invitation email(s) failed to send."
            
    return JsonResponse({
        "ok": True,
        "message": message,
        "tournament_id": tournament.id,
        "invitations_created": len(invitations),
        "emails_sent": emails_sent,
        "emails_failed": emails_failed,
        "redirect_url": str(reverse("tournament_dashboard_page")),
    })


DEPARTMENT_ONLY_TOURNAMENT_TYPES = ("INTER_DEPARTMENT", "INTRA_DEPARTMENT")
COLLEGE_TOURNAMENT_TYPES = ("INTER_COLLEGE", "INTRA_COLLEGE")


@login_required
def tournament_invitation_colleges_json(request):
    schools = School.objects.filter(status="ACTIVE").order_by("school_name")
    return JsonResponse(
        [{"id": str(s.school_id), "name": s.school_name} for s in schools], safe=False
    )


@login_required
def tournament_invitation_faculty_json(request):
    department_id = request.GET.get("department_id")
    faculties = (
        FacultyProfile.objects.filter(department_id=department_id, employment_status="ACTIVE")
        .select_related("user", "faculty_rank")
        .order_by("user__first_name", "user__last_name")
    )
    data = [
        {
            "id": f.id,
            "name": f"{f.user.get_full_name()} ({f.faculty_rank.rank_name if f.faculty_rank else 'Faculty'})",
        }
        for f in faculties
    ]
    return JsonResponse(data, safe=False)



OTP_EXPIRY_MINUTES = 10
OTP_RESEND_COOLDOWN_SECONDS = 45
OTP_MAX_ATTEMPTS = 5


def _mask_email(email):
    try:
        local, domain = email.split("@", 1)
    except (ValueError, AttributeError):
        return email or ""
    if len(local) <= 2:
        masked_local = local[0] + "*" * max(len(local) - 1, 1)
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def _resolve_choice_name(selected_id, other_name, queryset, id_field, name_field):
    """Resolve a college/coach/team select value that may be a real id or 'OTHER'."""
    selected_id = (selected_id or "").strip()
    other_name = (other_name or "").strip()
    if selected_id == "OTHER":
        return other_name
    if selected_id:
        obj = queryset.filter(**{id_field: selected_id}).first()
        if obj:
            return getattr(obj, name_field)
    return ""


def _coach_display_name(coach_obj):
    
    if not coach_obj or not coach_obj.staff_id:
        return ""
    staff = (
        StaffProfile.objects.filter(employee_id=coach_obj.staff_id)
        .select_related("user")
        .first()
    )
    if staff and staff.user:
        name = staff.user.get_full_name().strip()
        if name:
            return name
    
    return coach_obj.staff_id


def _resolve_coach_application_name(coach_id, other_coach_name):
    coach_id = (coach_id or "").strip()
    other_coach_name = (other_coach_name or "").strip()[:150]
    if coach_id == "OTHER":
        return other_coach_name, (not other_coach_name)  # (name, is_error)
    if coach_id:
        coach_obj = Coach.objects.filter(coach_id=coach_id).first()
        return (_coach_display_name(coach_obj) if coach_obj else ""), False
    return "", False


def _get_email_invitation_or_404(invitation_token):
    return get_object_or_404(
        TournamentInvitation.objects.select_related("tournament", "tournament__sport", "tournament__venue"),
        invitation_token=invitation_token,
        invitation_type="EMAIL",
    )


def _invitation_status_meta(invitation, application):
    status = invitation.application_status
    if status == "APPLIED":
        return "Applied — Awaiting Admin Approval", "applied", "ti-clock-hour-4"
    if status == "APPROVED":
        return "Approved", "approved", "ti-circle-check"
    if status == "REJECTED":
        remarks = application.admin_remarks if application and application.admin_remarks else ""
        label = f"Rejected: {remarks}" if remarks else "Rejected"
        return label, "rejected", "ti-circle-x"
    return "Invited", "invited", "ti-mail"


def email_tournament_apply_page(request, invitation_token):
    invitation = _get_email_invitation_or_404(invitation_token)
    tournament = invitation.tournament

    application = getattr(invitation, "application", None)
    already_submitted = application is not None or invitation.application_status != "INVITED"
    deadline_passed = tournament.registration_deadline < timezone.localdate()

    status_display, status_class, status_icon = _invitation_status_meta(invitation, application)

    context = {
        "tournament": tournament,
        "invitation": invitation,
        "application": application,
        "already_submitted": already_submitted,
        "deadline_passed": deadline_passed,
        "status_display": status_display,
        "status_class": status_class,
        "status_icon": status_icon,
    }

    if not already_submitted and not deadline_passed:
        context["colleges"] = School.objects.filter(status="ACTIVE").order_by("school_name")
       

        coach_qs = Coach.objects.filter(is_active=True).order_by("staff_id")
        context["coaches"] = [
            {"coach_id": c.coach_id, "full_name": _coach_display_name(c)}
            for c in coach_qs
        ]

        if tournament.participation_type == "TEAM":
            teams_qs = SportTeamModel.objects.all()
            if tournament.sport_id:
                teams_qs = teams_qs.filter(sport_type_id=tournament.sport_id)
            context["internal_teams"] = teams_qs.order_by("team_name")

    return render(request, "email_tournament_apply.html", context)


@require_http_methods(["POST"])
def email_tournament_apply_send_otp_json(request, invitation_token):
    with transaction.atomic():
        invitation = get_object_or_404(
            TournamentInvitation.objects.select_for_update().select_related("tournament"),
            invitation_token=invitation_token,
            invitation_type="EMAIL",
        )
        tournament = invitation.tournament

        application = getattr(invitation, "application", None)
        if application is not None or invitation.application_status != "INVITED":
            return JsonResponse({"error": "An application has already been submitted for this invitation."}, status=400)

        if tournament.registration_deadline < timezone.localdate():
            return JsonResponse({"error": "Registration for this tournament is closed."}, status=400)

        if not invitation.email:
            return JsonResponse({"error": "No email is associated with this invitation."}, status=400)

        now = timezone.now()
        if invitation.otp_last_sent_at and (now - invitation.otp_last_sent_at).total_seconds() < OTP_RESEND_COOLDOWN_SECONDS:
            wait_left = OTP_RESEND_COOLDOWN_SECONDS - int((now - invitation.otp_last_sent_at).total_seconds())
            return JsonResponse({"error": f"Please wait {wait_left}s before requesting another code."}, status=429)

        otp_code = f"{random.randint(0, 999999):06d}"
        invitation.otp_hash = make_password(otp_code)
        invitation.otp_expires_at = now + timedelta(minutes=OTP_EXPIRY_MINUTES)
        invitation.otp_attempts = 0
        invitation.otp_last_sent_at = now
        invitation.save(update_fields=["otp_hash", "otp_expires_at", "otp_attempts", "otp_last_sent_at"])

        try:
            text_body = (
                f"Your verification code for {tournament.tournament_name} is: {otp_code}\n"
                f"This code will expire in {OTP_EXPIRY_MINUTES} minutes.\n"
                f"If you did not request this, you can ignore this email."
            )
            msg = EmailMultiAlternatives(
                subject=f"Your verification code — {tournament.tournament_name}",
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[invitation.email],
            )
            msg.send(fail_silently=False)
        except Exception:
            logger.exception(
                "Failed to send tournament application OTP to %s for invitation %s",
                invitation.email, invitation.invitation_uuid,
            )
            return JsonResponse({"error": "Could not send the verification code. Please try again."}, status=500)

        return JsonResponse({
            "success": True,
            "masked_email": _mask_email(invitation.email),
            "resend_in": OTP_RESEND_COOLDOWN_SECONDS,
        })

from Admin.models import Notification as DashboardNotification
@require_http_methods(["POST"])
def email_tournament_apply_submit_json(request, invitation_token):
    with transaction.atomic():
        invitation = get_object_or_404(
            TournamentInvitation.objects.select_for_update().select_related("tournament"),
            invitation_token=invitation_token,
            invitation_type="EMAIL",
        )
        tournament = invitation.tournament

        application = getattr(invitation, "application", None)
        if application is not None or invitation.application_status != "INVITED":
            return JsonResponse({"error": "An application has already been submitted for this invitation."}, status=400)

        if tournament.registration_deadline < timezone.localdate():
            return JsonResponse({"error": "Registration for this tournament is closed."}, status=400)

        submitted_otp = (request.POST.get("otp") or "").strip()
        if not submitted_otp:
            return JsonResponse({"error": "Verification code is required."}, status=400)

        if not invitation.otp_hash or not invitation.otp_expires_at:
            return JsonResponse({"error": "No active verification code. Please request a new one."}, status=400)

        if invitation.otp_attempts >= OTP_MAX_ATTEMPTS:
            invitation.otp_hash = None
            invitation.otp_expires_at = None
            invitation.save(update_fields=["otp_hash", "otp_expires_at"])
            return JsonResponse({"error": "Too many incorrect attempts. Please request a new code."}, status=400)

        if timezone.now() > invitation.otp_expires_at:
            invitation.otp_hash = None
            invitation.otp_expires_at = None
            invitation.save(update_fields=["otp_hash", "otp_expires_at"])
            return JsonResponse({"error": "This code has expired. Please request a new one."}, status=400)

        if not check_password(submitted_otp, invitation.otp_hash):
            invitation.otp_attempts += 1
            invitation.save(update_fields=["otp_attempts"])
            attempts_left = max(OTP_MAX_ATTEMPTS - invitation.otp_attempts, 0)
            return JsonResponse({"error": f"Incorrect code. {attempts_left} attempt(s) left."}, status=400)

        college_id = request.POST.get("college_id", "")
        # other_college_name = request.POST.get("other_college_name", "")
        
        other_college_name = (request.POST.get("other_college_name") or "").strip()[:200]
        college_name = _resolve_choice_name(
            college_id, other_college_name, School.objects.all(), "school_id", "school_name"
        )
        if not college_name:
            return JsonResponse({"error": "College is required."}, status=400)

        coach_id = request.POST.get("coach_id", "")
        other_coach_name = request.POST.get("other_coach_name", "")
        # coach_name = _resolve_choice_name(
        #     coach_id, other_coach_name, Coach.objects.all(), "coach_id", "staff_id"
        # )

        coach_name, coach_missing = _resolve_coach_application_name(coach_id, other_coach_name)
        if coach_missing:
            return JsonResponse({"error": "Please enter the coach name."}, status=400)

        contact_person = (request.POST.get("contact_person") or "").strip()[:150]
        contact_mobile = (request.POST.get("contact_mobile") or "").strip()[:20]
        faculty_remarks = (request.POST.get("faculty_remarks") or "").strip()[:500]

        if contact_mobile and not re.fullmatch(r"\d{1,15}", contact_mobile):
                return JsonResponse(
                    {"error": "Contact mobile must contain only numbers and be 1 to 15 digits."},
                    status=400,
                )

        internal_team_obj = None
        if tournament.participation_type == "TEAM":
            team_id = request.POST.get("internal_team_id", "")
            # other_team_name = request.POST.get("other_team_name", "")
            other_team_name = (request.POST.get("other_team_name") or "").strip()[:200]
            if team_id and team_id != "OTHER":
                internal_team_obj = SportTeamModel.objects.filter(team_id=team_id).first()

            team_name = _resolve_choice_name(
                team_id, other_team_name, SportTeamModel.objects.all(), "team_id", "team_name"
            )
            if not team_name:
                return JsonResponse({"error": "Internal team is required."}, status=400)

            players = [p.strip()[:150] for p in request.POST.getlist("player_name[]") if p.strip()]
            lower_names = [p.lower() for p in players]
            if len(set(lower_names)) != len(lower_names):
                return JsonResponse({"error": "Duplicate player names are not allowed."}, status=400)

            min_p = tournament.minimum_participants or 1
            max_p = tournament.maximum_participants or min_p
            if len(players) < min_p:
                return JsonResponse({"error": f"At least {min_p} player(s) are required."}, status=400)
            if len(players) > max_p:
                return JsonResponse({"error": f"No more than {max_p} player(s) are allowed."}, status=400)

            entry_name = ""
            players_count = len(players)
        else:
            entry_name = (request.POST.get("entry_name") or "").strip()[:200]
            if not entry_name:
                return JsonResponse({"error": "Participant name is required."}, status=400)
            team_name = ""
            players = []
            players_count = 1

        application = TournamentApplication.objects.create(
            tournament=tournament,
            invitation=invitation,
            entry_name=entry_name,
            team_name=team_name,
            internal_team=internal_team_obj,
            coach_name=coach_name,
            contact_person=contact_person,
            contact_mobile=contact_mobile,
            players_count=players_count,
            players=players,
            faculty_remarks=faculty_remarks,
            status="APPLIED",
        )

        invitation.college_name = college_name
        invitation.contact_person = contact_person or invitation.contact_person
        invitation.mobile_number = contact_mobile or invitation.mobile_number
        invitation.application_status = "APPLIED"
        invitation.applied_at = timezone.now()
        invitation.otp_hash = None
        invitation.otp_expires_at = None
        invitation.otp_attempts = 0
        invitation.save(update_fields=[
            "college_name", "contact_person", "mobile_number",
            "application_status", "applied_at",
            "otp_hash", "otp_expires_at", "otp_attempts",
        ])

        transaction.on_commit(lambda inv=invitation: broadcast_invitation_status(inv))
        AuditLogger.log(
            request,
            action="CREATE",
            module="TournamentManagement",
            object_type="TournamentApplication",
            object_id=application.id,
            description=(
                f"Public email application submitted for "
                f"'{tournament.tournament_name}' via invitation "
                f"{invitation.invitation_uuid}."
            ),
        )

        entry_display = team_name if tournament.participation_type == "TEAM" else entry_name

        DashboardNotification.objects.create(
            notification_type='TOURNAMENT',
            tournament_application=application,
            event='tournament_applied',
            message=f'{entry_display} submitted an application for '
                    f'"{tournament.tournament_name}"',
            icon='trophy',
            recipient=None,
        )

        return JsonResponse({
            "success": True,
            "participation_type": tournament.participation_type,
            "entry_display": team_name if tournament.participation_type == "TEAM" else entry_name,
            "college_name": college_name,
            "coach_name": coach_name,
            "contact_person": contact_person,
            "contact_mobile": contact_mobile,
            "players": players,
            "players_count": players_count,
            "status_display": "Applied — Awaiting Admin Approval",
            "applied_at_display": invitation.applied_at.strftime("%d %b %Y, %I:%M %p"),
        })


from xhtml2pdf import pisa
from openpyxl import Workbook

from Admin.Jack.models import Sport, SportTeamModel, Coach, SportClub, SportsFacility



SPORTS_REPORT_TITLES = {
    "sports": "Sports Records",
    "teams": "Team Records",
    "clubs": "Club Records",
    "facilities": "Facility Records",
    "coaches": "Coach Records",
    "tournaments": "Tournament Records",
    "athletes": "Olympic Athlete Records",
    "performances": "Performance Records",
}
 
 
def _sr_active_label(is_active):
    return "Active" if is_active else "Inactive"
 
 
def _sports_report_dataset(report_type, status_filter):
    """
    Returns (columns, rows) for the given report_type.
    columns: [{"label": ..., "key": ...}, ...]
    rows: [{"key": value, ...}, ...]   (values are already display-ready strings)
    status_filter: "ALL" | "ACTIVE" | "INACTIVE"
    """
 
    if report_type == "teams":
        columns = [
            {"label": "Team Code", "key": "team_code"},
            {"label": "Team Name", "key": "team_name"},
            {"label": "Sport", "key": "sport"},
            {"label": "Gender Category", "key": "gender_category"},
            {"label": "Division", "key": "division"},
            {"label": "Season", "key": "season"},
            {"label": "Head Coach", "key": "head_coach"},
            {"label": "Home Facility", "key": "home_facility"},
            {"label": "Founded Year", "key": "founded_year"},
            {"label": "Status", "key": "status"},
        ]
 
        qs = SportTeamModel.objects.select_related(
            "sport_type", "head_coach", "home_facility"
        ).order_by("team_name")
 
        if status_filter == "ACTIVE":
            qs = qs.filter(status=True)
        elif status_filter == "INACTIVE":
            qs = qs.filter(status=False)
 
        rows = [{
            "team_code": t.team_code,
            "team_name": t.team_name,
            "sport": t.sport_type.sport_name if t.sport_type else "",
            "gender_category": t.get_gender_category_display(),
            "division": t.division,
            "season": t.season,
            "head_coach": t.head_coach.staff_id if t.head_coach else "",
            "home_facility": t.home_facility.facility_name if t.home_facility else "",
            "founded_year": t.founded_year,
            "status": _sr_active_label(t.status),
        } for t in qs]
 
        return columns, rows
 
    if report_type == "clubs":
        columns = [
            {"label": "Club Name", "key": "club_name"},
            {"label": "Sport", "key": "sport"},
            {"label": "Total Teams", "key": "total_teams"},
            {"label": "Total Coaches", "key": "total_coaches"},
            {"label": "Status", "key": "status"},
        ]
 
        qs = SportClub.objects.select_related("sport").order_by("club_name")
 
        if status_filter == "ACTIVE":
            qs = qs.filter(is_active=True)
        elif status_filter == "INACTIVE":
            qs = qs.filter(is_active=False)
 
        rows = [{
            "club_name": c.club_name,
            "sport": c.sport.sport_name if c.sport else "",
            "total_teams": c.total_teams,
            "total_coaches": c.total_coaches,
            "status": _sr_active_label(c.is_active),
        } for c in qs]
 
        return columns, rows
 
    if report_type == "facilities":
        columns = [
            {"label": "Facility Name", "key": "facility_name"},
            {"label": "Sport", "key": "sport"},
            {"label": "Type", "key": "facility_type"},
            {"label": "Capacity", "key": "capacity"},
            {"label": "Location", "key": "location"},
            {"label": "Status", "key": "status"},
        ]
 
        qs = SportsFacility.objects.select_related("sport").order_by("facility_name")
 
        if status_filter == "ACTIVE":
            qs = qs.filter(status="ACTIVE")
        elif status_filter == "INACTIVE":
            qs = qs.exclude(status="ACTIVE")
 
        rows = [{
            "facility_name": f.facility_name,
            "sport": f.sport.sport_name if f.sport else "",
            "facility_type": f.get_facility_type_display(),
            "capacity": f.capacity,
            "location": f.location,
            "status": f.get_status_display(),
        } for f in qs]
 
        return columns, rows
 
    if report_type == "coaches":
        columns = [
            {"label": "Staff ID", "key": "staff_id"},
            {"label": "Role", "key": "role"},
            {"label": "Hire Date", "key": "hire_date"},
            {"label": "Status", "key": "status"},
        ]
 
        qs = Coach.objects.order_by("staff_id")
 
        if status_filter == "ACTIVE":
            qs = qs.filter(is_active=True)
        elif status_filter == "INACTIVE":
            qs = qs.filter(is_active=False)
 
        rows = [{
            "staff_id": c.staff_id,
            "role": c.get_role_display(),
            "hire_date": c.hire_date.strftime("%b %d, %Y") if c.hire_date else "",
            "status": _sr_active_label(c.is_active),
        } for c in qs]
 
        return columns, rows
 
    if report_type == "tournaments":
        columns = [
            {"label": "Code", "key": "tournament_code"},
            {"label": "Name", "key": "tournament_name"},
            {"label": "Sport", "key": "sport"},
            {"label": "Type", "key": "tournament_type"},
            {"label": "Participation", "key": "participation_type"},
            {"label": "Start Date", "key": "start_date"},
            {"label": "End Date", "key": "end_date"},
            {"label": "Status", "key": "status"},
        ]
 
        qs = Tournament.objects.select_related("sport").order_by("-start_date")
 
        if status_filter == "ACTIVE":
            qs = qs.filter(is_active=True)
        elif status_filter == "INACTIVE":
            qs = qs.filter(is_active=False)
 
        rows = [{
            "tournament_code": t.tournament_code,
            "tournament_name": t.tournament_name,
            "sport": t.sport.sport_name if t.sport else "",
            "tournament_type": t.get_tournament_type_display(),
            "participation_type": t.get_participation_type_display(),
            "start_date": t.start_date.strftime("%b %d, %Y") if t.start_date else "",
            "end_date": t.end_date.strftime("%b %d, %Y") if t.end_date else "",
            "status": t.get_status_display(),
        } for t in qs]
 
        return columns, rows
 
    if report_type == "athletes":
        columns = [
            {"label": "Athlete No.", "key": "athlete_number"},
            {"label": "Sport", "key": "sport"},
            {"label": "Team", "key": "team"},
            {"label": "Nationality", "key": "nationality"},
            {"label": "Target Olympics", "key": "target_olympics"},
            {"label": "World Ranking", "key": "world_ranking"},
            {"label": "Status", "key": "status"},
        ]
 
        qs = OlympicAthlete.objects.select_related("sport", "team").order_by("athlete_number")
 
        if status_filter == "ACTIVE":
            qs = qs.filter(is_active=True)
        elif status_filter == "INACTIVE":
            qs = qs.filter(is_active=False)
 
        rows = [{
            "athlete_number": a.athlete_number,
            "sport": a.sport.sport_name if a.sport else "",
            "team": a.team.team_name if a.team else "",
            "nationality": a.nationality,
            "target_olympics": a.target_olympics,
            "world_ranking": a.world_ranking,
            "status": _sr_active_label(a.is_active),
        } for a in qs]
 
        return columns, rows
 
    if report_type == "performances":
        columns = [
            {"label": "Competition", "key": "competition_name"},
            {"label": "Athlete", "key": "athlete"},
            {"label": "Level", "key": "competition_level"},
            {"label": "Event", "key": "event_name"},
            {"label": "Date", "key": "competition_date"},
            {"label": "Medal", "key": "medal"},
            {"label": "Status", "key": "status"},
        ]
 
        qs = OlympicPerformance.objects.select_related(
            "olympic_athlete", "olympic_athlete__athlete__student"
        ).order_by("-competition_date")
 
        if status_filter == "ACTIVE":
            qs = qs.filter(is_archived=False)
        elif status_filter == "INACTIVE":
            qs = qs.filter(is_archived=True)
 
        rows = []
        for p in qs:
            athlete_label = p.olympic_athlete.athlete_number if p.olympic_athlete else ""
            rows.append({
                "competition_name": p.competition_name,
                "athlete": athlete_label,
                "competition_level": p.get_competition_level_display(),
                "event_name": p.event_name,
                "competition_date": p.competition_date.strftime("%b %d, %Y") if p.competition_date else "",
                "medal": p.get_medal_display(),
                "status": "Archived" if p.is_archived else "Active",
            })
 
        return columns, rows
 
    columns = [
        {"label": "Sport Name", "key": "sport_name"},
        {"label": "Type", "key": "sport_type"},
        {"label": "Gender", "key": "gender"},
        {"label": "Team Sport", "key": "is_team_sport"},
        {"label": "Players", "key": "players"},
        {"label": "Status", "key": "status"},
    ]
 
    qs = Sport.objects.order_by("sport_name")
 
    if status_filter == "ACTIVE":
        qs = qs.filter(is_active=True)
    elif status_filter == "INACTIVE":
        qs = qs.filter(is_active=False)
 
    rows = []
    for s in qs:
        if s.min_players and s.max_players:
            players = "{}-{}".format(s.min_players, s.max_players)
        else:
            players = ""
        rows.append({
            "sport_name": s.sport_name,
            "sport_type": s.get_sport_type_display(),
            "gender": s.get_gender_display(),
            "is_team_sport": "Yes" if s.is_team_sport else "No",
            "players": players,
            "status": _sr_active_label(s.is_active),
        })
 
    return columns, rows
 
 
def _sports_report_chart_data():
    sports_by_type = (
        Sport.objects.values("sport_type")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    type_labels_map = dict(Sport.SPORT_TYPE)
 
    teams_by_sport = (
        SportTeamModel.objects.values("sport_type__sport_name")
        .annotate(total=Count("team_id"))
        .order_by("-total")[:6]
    )
 
    tournament_status = (
        Tournament.objects.values("status")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    status_labels_map = dict(Tournament.STATUS_CHOICES)
 
    medal_distribution = (
        OlympicPerformance.objects.exclude(medal="NONE")
        .values("medal")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    medal_labels_map = dict(OlympicPerformance.MEDAL_CHOICES)
 
    return {
        "sports_by_type": {
            "labels": [type_labels_map.get(row["sport_type"], row["sport_type"]) for row in sports_by_type],
            "values": [row["total"] for row in sports_by_type],
        },
        "teams_by_sport": {
            "labels": [row["sport_type__sport_name"] or "Unassigned" for row in teams_by_sport],
            "values": [row["total"] for row in teams_by_sport],
        },
        "tournament_status": {
            "labels": [status_labels_map.get(row["status"], row["status"]) for row in tournament_status],
            "values": [row["total"] for row in tournament_status],
        },
        "medal_distribution": {
            "labels": [medal_labels_map.get(row["medal"], row["medal"]) for row in medal_distribution],
            "values": [row["total"] for row in medal_distribution],
        },
    }
 
 

@require_page_access("sports_reports_page")
@login_required
def sports_reports_page(request):
 
    context = {
        "total_sports": Sport.objects.count(),
        "total_teams": SportTeamModel.objects.count(),
        "total_clubs": SportClub.objects.count(),
        "total_facilities": SportsFacility.objects.count(),
        "total_coaches": Coach.objects.count(),
        "total_tournaments": Tournament.objects.count(),
        "total_athletes": OlympicAthlete.objects.count(),
        "total_performances": OlympicPerformance.objects.count(),
        "chart_data_json": json.dumps(_sports_report_chart_data()),
    }
 
    return render(request, "sports_reports.html", context)
 
 
def sports_reports_data_json(request):
 
    report_type = request.GET.get("report_type", "sports")
    status_filter = request.GET.get("status", "ALL")
    page_number = request.GET.get("page", 1)
 
    columns, rows = _sports_report_dataset(report_type, status_filter)
 
    paginator = Paginator(rows, 10)
    page_obj = paginator.get_page(page_number)
 
    return JsonResponse({
        "columns": columns,
        "rows": list(page_obj.object_list),
        "count": paginator.count,
        "page": page_obj.number,
        "num_pages": paginator.num_pages,
        "page_size": 10,
        "title": SPORTS_REPORT_TITLES.get(report_type, "Records"),
    })
 
 
def sports_reports_export_excel(request):
 
    report_type = request.GET.get("report_type", "sports")
    status_filter = request.GET.get("status", "ALL")
 
    columns, rows = _sports_report_dataset(report_type, status_filter)
 
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = SPORTS_REPORT_TITLES.get(report_type, "Report")[:31]
 
    for col_index, col in enumerate(columns, 1):
        worksheet.cell(row=1, column=col_index).value = col["label"]
 
    for row_index, row in enumerate(rows, 2):
        for col_index, col in enumerate(columns, 1):
            worksheet.cell(row=row_index, column=col_index).value = row.get(col["key"], "")
 
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    filename = "{}.xlsx".format(SPORTS_REPORT_TITLES.get(report_type, "Sports_Report").replace(" ", "_"))
    response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename)
 
    workbook.save(response)
 
    return response
 
 
def sports_reports_export_pdf(request):
 
    report_type = request.GET.get("report_type", "sports")
    status_filter = request.GET.get("status", "ALL")
 
    columns, rows = _sports_report_dataset(report_type, status_filter)
 
    ordered_rows = [[row.get(col["key"], "") for col in columns] for row in rows]
 
    html_string = render_to_string("pdf_template.html", {
        "report_title": SPORTS_REPORT_TITLES.get(report_type, "Sports Report"),
        "generated_at": datetime.now().strftime("%B %d, %Y %I:%M %p"),
        "status_filter": status_filter,
        "columns": columns,
        "rows": ordered_rows,
    })
 
    response = HttpResponse(content_type="application/pdf")
    filename = "{}.pdf".format(SPORTS_REPORT_TITLES.get(report_type, "Sports_Report").replace(" ", "_"))
    response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename)
 
    pisa_status = pisa.CreatePDF(html_string, dest=response)
 
    if pisa_status.err:
        return HttpResponse("PDF generation failed.", status=500)
 
    return response

####################################### kali code End ######################################
 


###################################### GURU CODE START ##############################################

def students(request):
    return render(request, 'students.html')

###################################### GURU CODE END ################################################


######################################  Rixie Code Start  ###########################################

from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from Admin.bela_admin.models import Building, Floor, Room


def building_page(request):

    # =========================================================
    # ADD BUILDING
    # =========================================================

    if request.method == "POST":

        building_name = request.POST.get("building_name", "").strip()
        building_code = request.POST.get("building_code", "").strip()
        address = request.POST.get("address", "").strip()
        building_image = request.FILES.get("building_image")
        building_type = request.POST.get("building_type", "NORMAL").strip()

        if building_type not in ("MEDICAL", "NORMAL"):
            building_type = "NORMAL"

        # -------------------------
        # Validation
        # -------------------------

        if not building_name:
            messages.error(request, "Building name is required.")
            return redirect("building_page")

        if not building_code:
            messages.error(request, "Building code is required.")
            return redirect("building_page")

        # Check duplicate building code

        if Building.objects.filter(
            building_code=building_code
        ).exists():

            messages.error(
                request,
                "A building with this building code already exists."
            )

            return redirect("building_page")

        # -------------------------
        # Create Building
        # -------------------------

        Building.objects.create(
            building_name=building_name,
            building_code=building_code,
            address=address,
            building_image=building_image,
            building_type=building_type,
            status="ACTIVE"
        )

        messages.success(
            request,
            f"Building '{building_name}' added successfully."
        )

        return redirect("building_page")


    # =========================================================
    # BUILDING LIST
    # =========================================================

    building_type_filter = request.GET.get("building_type", "")

    buildings_qs = Building.objects.annotate(

        floor_count=Count(
            "floors",
            distinct=True
        ),

        room_count=Count(
            "floors__rooms",
            distinct=True
        )

    ).order_by("-created_at")

    if building_type_filter in ("MEDICAL", "NORMAL"):
        buildings_qs = buildings_qs.filter(building_type=building_type_filter)

    paginator = Paginator(buildings_qs, 10)
    page_number = request.GET.get("page")
    buildings = paginator.get_page(page_number)


    # =========================================================
    # SUMMARY
    # =========================================================

    total_buildings = Building.objects.count()

    active_buildings = Building.objects.filter(
        status="ACTIVE"
    ).count()

    inactive_buildings = Building.objects.filter(
        status="INACTIVE"
    ).count()

    normal_buildings = Building.objects.filter(
        building_type="NORMAL"
    ).count()

    medical_buildings = Building.objects.filter(
        building_type="MEDICAL"
    ).count()


    # =========================================================
    # CONTEXT
    # =========================================================

    context = {

        "buildings": buildings,

        "total_buildings": total_buildings,

        "active_buildings": active_buildings,

        "inactive_buildings": inactive_buildings,

        "normal_buildings": normal_buildings,

        "medical_buildings": medical_buildings,

        "building_type_filter": building_type_filter,

    }


    return render(
        request,
        "Rixie/building.html",
        context
    )


def building_add(request):

    if request.method == "POST":

        building_name = request.POST.get(
            "building_name",
            ""
        ).strip()

        building_code = request.POST.get(
            "building_code",
            ""
        ).strip().upper()
        building_type = request.POST.get(
              "building_type",
              "NORMAL"
        ).strip()

        address = request.POST.get(
            "address",
            ""
        ).strip()

        building_image = request.FILES.get(
            "building_image"
        )

        # Basic validation
        if not building_name:
            messages.error(
                request,
                "Building name is required."
            )
            return redirect("building_page")

        if not building_code:
            messages.error(
                request,
                "Building code is required."
            )
            return redirect("building_page")
        if building_type not in ["MEDICAL", "NORMAL"]:
            messages.error(
                 request,
                 "Please select a valid building type."
            )
            return redirect("building_page")

        # Check duplicate building code
        if Building.objects.filter(
            building_code=building_code
        ).exists():

            messages.error(
                request,
                f"Building code '{building_code}' already exists."
            )

            return redirect("building_page")

        # Create building
        Building.objects.create(
            building_name=building_name,
            building_code=building_code,
            building_type=building_type,
            address=address,
            building_image=building_image,
            status="ACTIVE"
        )

        messages.success(
            request,
            f"{building_name} added successfully."
        )

        return redirect("building_page")

    return redirect("building_page")



def building_edit(request, building_id):

    building = get_object_or_404(
        Building,
        pk=building_id
    )

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Invalid request."
        }, status=400)

    building_name = request.POST.get(
        "building_name",
        ""
    ).strip()

    building_code = request.POST.get(
        "building_code",
        ""
    ).strip()

    address = request.POST.get(
        "address",
        ""
    ).strip()

    building_image = request.FILES.get(
        "building_image"
    )

    if not building_name:

        return JsonResponse({
            "success": False,
            "message": "Building name is required."
        })

    if not building_code:

        return JsonResponse({
            "success": False,
            "message": "Building code is required."
        })

    # Check duplicate building code
    if Building.objects.filter(
        building_code=building_code
    ).exclude(
        pk=building.pk
    ).exists():

        return JsonResponse({
            "success": False,
            "message": "Building code already exists."
        })

    building.building_name = building_name
    building.building_code = building_code
    building.address = address

    if building_image:
        building.building_image = building_image

    status = request.POST.get("status", "").strip()

    if status in ("ACTIVE", "INACTIVE"):
        building.status = status

    building_type = request.POST.get(
        "building_type",
        ""
    ).strip()

    if building_type in ("MEDICAL", "NORMAL"):
        building.building_type = building_type

    building.save()

    return JsonResponse({
        "success": True,
        "message": "Building updated successfully."
    })



def building_inactivate(request, building_id):

    building = get_object_or_404(
        Building,
        pk=building_id
    )

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Invalid request."
        }, status=400)

    if building.status != "INACTIVE":

        building.status = "INACTIVE"

        building.save(update_fields=["status"])

        return JsonResponse({
            "success": True,
            "message": f'"{building.building_name}" marked as inactive.'
        })

    return JsonResponse({
        "success": False,
        "message": "Already inactive."
    }, status=400)


def building_export_excel(request):

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Buildings"

    headers = [
        "Building Name",
        "Building Code",
        "Address",
        "Floors",
        "Rooms",
        "Status",
    ]

    for col, header in enumerate(headers, 1):
        worksheet.cell(row=1, column=col).value = header

    buildings = (
        Building.objects.annotate(
            floor_count=Count(
                "floors",
                distinct=True
            ),
            room_count=Count(
                "floors__rooms",
                distinct=True
            )
        ).order_by("building_name")
    )

    row = 2

    for building in buildings:

        worksheet.cell(row=row, column=1).value = building.building_name
        worksheet.cell(row=row, column=2).value = building.building_code
        worksheet.cell(row=row, column=3).value = building.address or ""
        worksheet.cell(row=row, column=4).value = building.floor_count
        worksheet.cell(row=row, column=5).value = building.room_count
        worksheet.cell(row=row, column=6).value = building.get_status_display()

        row += 1

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response[
        "Content-Disposition"
    ] = 'attachment; filename="Buildings.xlsx"'

    workbook.save(response)

    return response


def building_export_pdf(request):

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="Buildings.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)

    data = [
        [
            "Building Name",
            "Building Code",
            "Address",
            "Floors",
            "Rooms",
            "Status"
        ]
    ]

    buildings = (
        Building.objects.annotate(
            floor_count=Count(
                "floors",
                distinct=True
            ),
            room_count=Count(
                "floors__rooms",
                distinct=True
            )
        ).order_by("building_name")
    )

    for building in buildings:

        data.append([
            building.building_name,
            building.building_code,
            building.address or "",
            building.floor_count,
            building.room_count,
            building.get_status_display(),
        ])

    table = Table(data)

    table.setStyle(TableStyle([

        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),

        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),

        ("GRID", (0,0), (-1,-1), 1, colors.black),

        ("BACKGROUND", (0,1), (-1,-1), colors.beige),

        ("ALIGN", (0,0), (-1,-1), "CENTER"),

        ("BOTTOMPADDING", (0,0), (-1,0), 10),

    ]))

    elements = [table]

    doc.build(elements)

    return response


from django.db.models import Count
from django.shortcuts import render, redirect
from django.contrib import messages


def floors_page(request):

    if request.method == "POST":

        building_id = request.POST.get("building")
        floor_name = request.POST.get("floor_name", "").strip()
        floor_number = request.POST.get("floor_number")


        if not building_id:
            messages.error(
                request,
                "Please select a building."
            )
            return redirect("floor_page")


        if not floor_name:
            messages.error(
                request,
                "Please enter the floor name."
            )
            return redirect("floor_page")

        if floor_number == "":
            messages.error(
                request,
                "Please enter the floor number."
            )
            return redirect("floor_page")


        try:

            floor_number = int(floor_number)

        except (ValueError, TypeError):

            messages.error(
                request,
                "Floor number must be a valid number."
            )

            return redirect("floor_page")


        if floor_number < 0:

            messages.error(
                request,
                "Floor number cannot be negative."
            )

            return redirect("floor_page")

        if floor_number > 10:

            messages.error(
                request,
                "Floor number cannot be greater than 10."
            )

            return redirect("floor_page")

        if not re.fullmatch(r"[A-Za-z0-9 ]+", floor_name):

            messages.error(
                request,
                "Floor name must contain only letters and numbers."
            )

            return redirect("floor_page")

        if Floor.objects.filter(
            building_id=building_id,
            floor_name__iexact=floor_name
        ).exists():

            messages.error(
                request,
                "A floor with this name already exists in this building."
            )

            return redirect("floor_page")


        try:

            building = Building.objects.get(
                id=building_id,
                status="ACTIVE"
            )

        except Building.DoesNotExist:

            messages.error(
                request,
                "Selected building does not exist or is inactive."
            )

            return redirect("floor_page")


        Floor.objects.create(
            building=building,
            floor_name=floor_name,
            floor_number=floor_number
        )


        messages.success(
            request,
            "Floor added successfully."
        )

        return redirect("floor_page")


    floors = Floor.objects.select_related(
        "building"
    ).annotate(
        room_count=Count(
            "rooms",
            distinct=True
        )
    ).order_by(
        "building__building_name",
        "floor_number"
    )

    building_type_filter = request.GET.get("building_type", "")

    if building_type_filter in ("MEDICAL", "NORMAL"):
        floors = floors.filter(building__building_type=building_type_filter)

    all_floors = floors

    paginator = Paginator(floors, 10)
    page_number = request.GET.get("page")
    floors = paginator.get_page(page_number)


    buildings = Building.objects.filter(
        status="ACTIVE"
    )


    total_floors = Floor.objects.count()

    total_rooms = Room.objects.count()

    total_buildings = Building.objects.count()

    buildings_with_floors = Building.objects.filter(
        floors__isnull=False
    ).distinct().count()

    normal_floors = Floor.objects.filter(
        building__building_type="NORMAL"
    ).count()

    medical_floors = Floor.objects.filter(
        building__building_type="MEDICAL"
    ).count()

    context = {

        "floors": floors,

        "all_floors": all_floors,

        "buildings": buildings,

        "total_floors": total_floors,

        "total_rooms": total_rooms,

        "total_buildings": total_buildings,

        "buildings_with_floors": buildings_with_floors,

        "normal_floors": normal_floors,

        "medical_floors": medical_floors,

        "building_type_filter": building_type_filter,

    }


    return render(
        request,
        "Rixie/floors.html",
        context
    )



def floor_edit(request, floor_id):

    floor = get_object_or_404(
        Floor,
        pk=floor_id
    )


    if request.method != "POST":

        return JsonResponse({
            "success": False,
            "message": "Invalid request."
        }, status=400)


    building_id = request.POST.get(
        "building"
    )

    floor_name = request.POST.get(
        "floor_name",
        ""
    ).strip()

    floor_number = request.POST.get(
        "floor_number"
    )


    # =========================================================
    # VALIDATION
    # =========================================================

    if not building_id:

        return JsonResponse({
            "success": False,
            "message": "Building is required."
        })


    if not floor_name:

        return JsonResponse({
            "success": False,
            "message": "Floor name is required."
        })


    if floor_number == "":

        return JsonResponse({
            "success": False,
            "message": "Floor number is required."
        })


    try:

        floor_number = int(
            floor_number
        )

    except (ValueError, TypeError):

        return JsonResponse({
            "success": False,
            "message": "Floor number must be a valid number."
        })


    if floor_number < 0:

        return JsonResponse({
            "success": False,
            "message": "Floor number cannot be negative."
        })

    if floor_number > 10:

        return JsonResponse({
            "success": False,
            "message": "Floor number cannot be greater than 10."
        })

    if not re.fullmatch(r"[A-Za-z0-9 ]+", floor_name):

        return JsonResponse({
            "success": False,
            "message": "Floor name must contain only letters and numbers."
        })

    if Floor.objects.filter(
        building_id=building_id,
        floor_name__iexact=floor_name
    ).exclude(
        pk=floor.id
    ).exists():

        return JsonResponse({
            "success": False,
            "message": "A floor with this name already exists in this building."
        })


    # =========================================================
    # GET BUILDING
    # =========================================================

    try:

        building = Building.objects.get(
            pk=building_id,
            status="ACTIVE"
        )

    except Building.DoesNotExist:

        return JsonResponse({
            "success": False,
            "message": "Selected building does not exist or is inactive."
        })


    # =========================================================
    # UPDATE FLOOR
    # =========================================================

    floor.building = building

    floor.floor_name = floor_name

    floor.floor_number = floor_number

    floor.save()


    # =========================================================
    # RESPONSE
    # =========================================================

    return JsonResponse({
        "success": True,
        "message": "Floor updated successfully."
    })


def floor_export_excel(request):

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Floors"

    headers = [
        "Floor Name",
        "Floor Number",
        "Building",
        "Building Code",
        "Rooms",
        "Status",
    ]

    for col, header in enumerate(headers, 1):
        worksheet.cell(row=1, column=col).value = header

    floors = (
        Floor.objects
        .select_related("building")
        .annotate(
            room_count=Count(
                "rooms",
                distinct=True
            )
        )
        .order_by("building__building_name", "floor_number")
    )

    row = 2

    for floor in floors:

        worksheet.cell(row=row, column=1).value = floor.floor_name
        worksheet.cell(row=row, column=2).value = floor.floor_number
        worksheet.cell(row=row, column=3).value = floor.building.building_name
        worksheet.cell(row=row, column=4).value = floor.building.building_code
        worksheet.cell(row=row, column=5).value = floor.room_count
        worksheet.cell(row=row, column=6).value = floor.building.get_status_display()

        row += 1

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response[
        "Content-Disposition"
    ] = 'attachment; filename="Floors.xlsx"'

    workbook.save(response)

    return response


def floor_export_pdf(request):

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="Floors.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)

    data = [
        [
            "Floor Name",
            "Floor Number",
            "Building",
            "Building Code",
            "Rooms",
            "Status"
        ]
    ]

    floors = (
        Floor.objects
        .select_related("building")
        .annotate(
            room_count=Count(
                "rooms",
                distinct=True
            )
        )
        .order_by("building__building_name", "floor_number")
    )

    for floor in floors:

        data.append([
            floor.floor_name,
            floor.floor_number,
            floor.building.building_name,
            floor.building.building_code,
            floor.room_count,
            floor.building.get_status_display(),
        ])

    table = Table(data)

    table.setStyle(TableStyle([

        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),

        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),

        ("GRID", (0,0), (-1,-1), 1, colors.black),

        ("BACKGROUND", (0,1), (-1,-1), colors.beige),

        ("ALIGN", (0,0), (-1,-1), "CENTER"),

        ("BOTTOMPADDING", (0,0), (-1,0), 10),

    ]))

    elements = [table]

    doc.build(elements)

    return response



from django.db.models import Sum



def room_page(request):
    from Admin.bela_admin.models import Room
    all_rooms = Room.objects.select_related(
        "floor",
        "floor__building"
    ).all().order_by(
        "floor__building__building_name",
        "floor__floor_number",
        "room_number"
    )

    building_type_filter = request.GET.get("building_type", "")

    rooms = all_rooms

    if building_type_filter in ("MEDICAL", "NORMAL"):
        rooms = rooms.filter(
            floor__building__building_type=building_type_filter
        )

    paginator = Paginator(
        rooms,
        10
    )

    page_number = request.GET.get("page")

    rooms_page = paginator.get_page(
        page_number
    )

    buildings = Building.objects.all().order_by("building_name")

    room_list = []

    for room in rooms:

        room_floor = getattr(room, "floor", None)
        room_building = (
            getattr(room_floor, "building", None)
            if room_floor else None
        )

        room_list.append({
            "id": room.pk,
            "room_number": room.room_number,
            "room_name": room.room_name,
            "building": (
                getattr(room_building, "building_name", "")
                if room_building else ""
            ),
            "building_type": (
                getattr(room_building, "building_type", "NORMAL")
                if room_building else "NORMAL"
            ),
            "floor": (
                getattr(room_floor, "floor_number", "")
                if room_floor else ""
            ),
            "floor_name": (
                getattr(room_floor, "floor_name", "")
                if room_floor else ""
            ),
            "room_type_display": room.get_room_type_display(),
            "room_type_value": room.room_type or "",
            "capacity": room.capacity,
            "status": room.status,
            "status_display": room.get_status_display(),
            "has_ac": room.has_ac,
            "has_projector": room.has_projector,
            "has_computers": room.has_computers,
            "building_id": (
                getattr(room_building, "pk", None)
                if room_building else None
            ),
            "floor_id": (
                getattr(room_floor, "pk", None)
                if room_floor else None
            ),
        })

    context = {
        "rooms": rooms,
        "rooms_json": room_list,
        "buildings": buildings,
        "paginated_rooms": rooms_page,
        "total_rooms": all_rooms.count(),
        "normal_rooms": all_rooms.filter(
            floor__building__building_type="NORMAL"
        ).count(),
        "medical_rooms": all_rooms.filter(
            floor__building__building_type="MEDICAL"
        ).count(),
        "available_rooms": all_rooms.filter(status="AVAILABLE").count(),
        "maintenance_rooms": all_rooms.filter(status="MAINTENANCE").count(),
        "blocked_rooms": all_rooms.filter(status="BLOCKED").count(),
        "total_capacity": all_rooms.aggregate(
            total=Sum("capacity")
        )["total"] or 0,
        "building_type_filter": building_type_filter,
    }
    
    return render(request, "Rixie/rooms.html", context)


def room_export_excel(request):
    from Admin.bela_admin.models import Room

    from Admin.bela_admin.models import Room

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Rooms"

    headers = [
        "Room Number",
        "Room Name",
        "Building",
        "Floor",
        "Floor Name",
        "Room Type",
        "Capacity",
        "Status",
        "AC",
        "Projector",
        "Computers",
    ]

    for col, header in enumerate(headers, 1):
        worksheet.cell(row=1, column=col).value = header

    rooms = (
        Room.objects
        .select_related("floor", "floor__building")
        .order_by(
            "floor__building__building_name",
            "floor__floor_number",
            "room_number"
        )
    )

    row = 2

    for room in rooms:

        # Medical rooms do not use room name,
        # room type, capacity or facilities.

        is_medical = (
            room.floor.building.building_type == "MEDICAL"
        )

        worksheet.cell(row=row, column=1).value = room.room_number
        worksheet.cell(row=row, column=2).value = (
            "" if is_medical else room.room_name
        )
        worksheet.cell(row=row, column=3).value = room.floor.building.building_name
        worksheet.cell(row=row, column=4).value = room.floor.floor_number
        worksheet.cell(row=row, column=5).value = room.floor.floor_name
        worksheet.cell(row=row, column=6).value = (
            "" if is_medical else room.get_room_type_display()
        )
        worksheet.cell(row=row, column=7).value = (
            "" if is_medical else room.capacity
        )
        worksheet.cell(row=row, column=8).value = room.get_status_display()
        worksheet.cell(row=row, column=9).value = (
            "" if is_medical else ("Yes" if room.has_ac else "No")
        )
        worksheet.cell(row=row, column=10).value = (
            "" if is_medical else ("Yes" if room.has_projector else "No")
        )
        worksheet.cell(row=row, column=11).value = (
            "" if is_medical else ("Yes" if room.has_computers else "No")
        )

        row += 1

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response[
        "Content-Disposition"
    ] = 'attachment; filename="Rooms.xlsx"'

    workbook.save(response)

    return response


def room_export_pdf(request):

    from Admin.bela_admin.models import Room

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="Rooms.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)

    data = [
        [
            "Room No.",
            "Room Name",
            "Building",
            "Floor",
            "Room Type",
            "Capacity",
            "Status"
        ]
    ]

    rooms = (
        Room.objects
        .select_related("floor", "floor__building")
        .order_by(
            "floor__building__building_name",
            "floor__floor_number",
            "room_number"
        )
    )

    for room in rooms:

        # Medical rooms do not use room name,
        # room type or capacity.

        is_medical = (
            room.floor.building.building_type == "MEDICAL"
        )

        data.append([
            room.room_number,
            "" if is_medical else room.room_name,
            room.floor.building.building_name,
            room.floor.floor_name,
            "" if is_medical else room.get_room_type_display(),
            "" if is_medical else room.capacity,
            room.get_status_display(),
        ])

    table = Table(data)

    table.setStyle(TableStyle([

        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),

        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),

        ("GRID", (0,0), (-1,-1), 1, colors.black),

        ("BACKGROUND", (0,1), (-1,-1), colors.beige),

        ("ALIGN", (0,0), (-1,-1), "CENTER"),

        ("BOTTOMPADDING", (0,0), (-1,0), 10),

    ]))

    doc.build([table])

    return response

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET, require_POST




@require_GET
def room_floors(request):
    from Admin.bela_admin.models import Room
    building_id = request.GET.get("building_id")

    if not building_id:
        return JsonResponse({
            "success": False,
            "floors": []
        })

    floors = Floor.objects.filter(
        building_id=building_id
    ).order_by("floor_number")

    data = []

    for floor in floors:
        data.append({
            "id": floor.pk,
            "floor_number": floor.floor_number,
        })

    return JsonResponse({
        "success": True,
        "floors": data
    })

@require_POST
def add_room(request):
    from Admin.bela_admin.models import Room
    building_id = request.POST.get("building")
    floor_id = request.POST.get("floor")
    room_number = request.POST.get("room_number", "").strip()
    room_name = request.POST.get("room_name", "").strip()
    room_type = request.POST.get("room_type")
    capacity = request.POST.get("capacity")
    status = request.POST.get("status")

    has_ac = request.POST.get("has_ac") == "on"
    has_projector = request.POST.get("has_projector") == "on"
    has_computers = request.POST.get("has_computers") == "on"

    if not all([
        building_id,
        floor_id,
        room_number,
        status,
    ]):
        return JsonResponse({
            "success": False,
            "message": "Please fill in all required fields."
        }, status=400)

    building = get_object_or_404(
        Building,
        pk=building_id
    )

    if building.building_type == "MEDICAL":

        # Medical rooms do not use room name,
        # room type, capacity or facilities.

        room_name = ""
        room_type = None
        capacity = 0

        has_ac = False
        has_projector = False
        has_computers = False

    else:

        if not all([
            room_name,
            room_type,
            capacity,
        ]):
            return JsonResponse({
                "success": False,
                "message": "Please fill in all required fields."
            }, status=400)

        try:
            capacity = int(capacity)
        except (TypeError, ValueError):
            return JsonResponse({
                "success": False,
                "message": "Capacity must be a valid number."
            }, status=400)

        if capacity <= 0:
            return JsonResponse({
                "success": False,
                "message": "Capacity must be greater than 0."
            }, status=400)

        if capacity > 200:
            return JsonResponse({
                "success": False,
                "message": "Capacity cannot exceed 200."
            }, status=400)

    if not re.fullmatch(r"\d+", room_number):
        return JsonResponse({
            "success": False,
            "message": "Room number must contain only numbers."
        }, status=400)

    if int(room_number) > 50:
        return JsonResponse({
            "success": False,
            "message": "Room number cannot exceed 50."
        }, status=400)

    floor = get_object_or_404(
        Floor,
        pk=floor_id,
        building=building
    )

    if Room.objects.filter(
        floor=floor,
        room_number=room_number
    ).exists():
        return JsonResponse({
            "success": False,
            "message": "A room with this number already exists on this floor."
        }, status=400)

    room = Room.objects.create(
        floor=floor,
        room_number=room_number,
        room_name=room_name,
        room_type=room_type,
        capacity=capacity,
        status=status,
        has_ac=has_ac,
        has_projector=has_projector,
        has_computers=has_computers,
    )

    return JsonResponse({
        "success": True,
        "message": f"Room {room.room_number} added successfully.",

        "room": {
            "id": room.pk,
            "room_number": room.room_number,
            "room_name": room.room_name,
            "building": building.building_name,
            "building_type": building.building_type,
            "floor": floor.floor_number,
            "floor_name": floor.floor_name,
            "building_id": building.pk,
            "floor_id": floor.pk,
            "room_type_value": room.room_type or "",
            "room_type": room.get_room_type_display(),
            "capacity": room.capacity,
            "status": room.status,
            "status_display": room.get_status_display(),
            "has_ac": room.has_ac,
            "has_projector": room.has_projector,
            "has_computers": room.has_computers,
        },

        "statistics": {
            "total_rooms": Room.objects.count(),
            "normal_rooms": Room.objects.filter(
                floor__building__building_type="NORMAL"
            ).count(),
            "medical_rooms": Room.objects.filter(
                floor__building__building_type="MEDICAL"
            ).count(),
            "available_rooms": Room.objects.filter(
                status="AVAILABLE"
            ).count(),
            "maintenance_rooms": Room.objects.filter(
                status="MAINTENANCE"
            ).count(),
            "blocked_rooms": Room.objects.filter(
                status="BLOCKED"
            ).count(),
            "total_capacity": sum(
                Room.objects.values_list(
                    "capacity",
                    flat=True
                )
            ),
        }
    })


@require_POST
def edit_room(request, room_id):
    from Admin.bela_admin.models import Room
    room = get_object_or_404(
        Room.objects.select_related(
            "floor",
            "floor__building"
        ),
        pk=room_id
    )

    building_id = request.POST.get("building")
    floor_id = request.POST.get("floor")
    room_number = request.POST.get("room_number", "").strip()
    room_name = request.POST.get("room_name", "").strip()
    room_type = request.POST.get("room_type")
    capacity = request.POST.get("capacity")
    status = request.POST.get("status")

    has_ac = request.POST.get("has_ac") == "on"
    has_projector = request.POST.get("has_projector") == "on"
    has_computers = request.POST.get("has_computers") == "on"

    if not all([
        building_id,
        floor_id,
        room_number,
        status,
    ]):
        return JsonResponse({
            "success": False,
            "message": "Please fill in all required fields."
        }, status=400)

    building = get_object_or_404(
        Building,
        pk=building_id
    )

    if building.building_type == "MEDICAL":

        # Medical rooms do not use room name,
        # room type, capacity or facilities.

        room_name = ""
        room_type = None
        capacity = 0

        has_ac = False
        has_projector = False
        has_computers = False

    else:

        if not all([
            room_name,
            room_type,
            capacity,
        ]):
            return JsonResponse({
                "success": False,
                "message": "Please fill in all required fields."
            }, status=400)

        try:
            capacity = int(capacity)
        except (TypeError, ValueError):
            return JsonResponse({
                "success": False,
                "message": "Capacity must be a valid number."
            }, status=400)

        if capacity <= 0:
            return JsonResponse({
                "success": False,
                "message": "Capacity must be greater than 0."
            }, status=400)

        if capacity > 200:
            return JsonResponse({
                "success": False,
                "message": "Capacity cannot exceed 200."
            }, status=400)

    if not re.fullmatch(r"\d+", room_number):
        return JsonResponse({
            "success": False,
            "message": "Room number must contain only numbers."
        }, status=400)

    if int(room_number) > 50:
        return JsonResponse({
            "success": False,
            "message": "Room number cannot exceed 50."
        }, status=400)

    # Important:
    # The floor MUST belong to the selected building.
    floor = get_object_or_404(
        Floor,
        pk=floor_id,
        building=building
    )

    if Room.objects.filter(
        floor=floor,
        room_number=room_number
    ).exclude(
        pk=room.pk
    ).exists():
        return JsonResponse({
            "success": False,
            "message": "A room with this number already exists on this floor."
        }, status=400)

    room.floor = floor
    room.room_number = room_number
    room.room_name = room_name
    room.room_type = room_type
    room.capacity = capacity
    room.status = status
    room.has_ac = has_ac
    room.has_projector = has_projector
    room.has_computers = has_computers

    room.save()

    return JsonResponse({
        "success": True,
        "message": f"Room {room.room_number} updated successfully.",

        "room": {
            "id": room.pk,
            "room_number": room.room_number,
            "room_name": room.room_name,
            "building": building.building_name,
            "building_type": building.building_type,
            "building_id": building.pk,
            "floor": floor.floor_number,
            "floor_name": floor.floor_name,
            "floor_id": floor.pk,
            "room_type": room.get_room_type_display(),
            "room_type_value": room.room_type or "",
            "capacity": room.capacity,
            "status": room.status,
            "status_display": room.get_status_display(),
            "has_ac": room.has_ac,
            "has_projector": room.has_projector,
            "has_computers": room.has_computers,
        },

        "statistics": {
            "total_rooms": Room.objects.count(),

            "normal_rooms": Room.objects.filter(
                floor__building__building_type="NORMAL"
            ).count(),

            "medical_rooms": Room.objects.filter(
                floor__building__building_type="MEDICAL"
            ).count(),

            "available_rooms": Room.objects.filter(
                status="AVAILABLE"
            ).count(),

            "maintenance_rooms": Room.objects.filter(
                status="MAINTENANCE"
            ).count(),

            "blocked_rooms": Room.objects.filter(
                status="BLOCKED"
            ).count(),

            "total_capacity": sum(
                Room.objects.values_list(
                    "capacity",
                    flat=True
                )
            ),
        }
    })

    
######################################  Rixie Code End  ###########################################

#<-----------------Blaze code start(13.08.26)---------------->






















from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Exists, OuterRef, Subquery
from django.db.models.functions import ExtractMonth, ExtractYear
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime

from .models import Hostel, Room, RoomAllocation, HostelAuditLog
from Admin.models import User


@login_required
def hostel_dashboard(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        messages.error(request, "You don't have permission to access this page.")
        return redirect("login")
    
    total_hostels = Hostel.objects.filter(status='ACTIVE').count()
    total_rooms = Room.objects.count()
    available_rooms = Room.objects.filter(is_available=True, status='AVAILABLE').count()
    occupied_rooms = Room.objects.filter(status='OCCUPIED').count()
    maintenance_rooms = Room.objects.filter(status='MAINTENANCE').count()
    active_allocations = RoomAllocation.objects.filter(status='ACTIVE').count()
    total_students = User.objects.filter(is_student=True, account_status='ACTIVE').count()
    
    total_capacity = total_rooms if total_rooms > 0 else 1
    available_percentage = round((available_rooms / total_capacity) * 100)
    allocation_percentage = round((active_allocations / total_students) * 100) if total_students > 0 else 0
    occupancy_rate = round((occupied_rooms / total_capacity) * 100)
    
    recent_allocations = RoomAllocation.objects.select_related(
        'student', 'room', 'room__hostel'
    ).order_by('-allocated_date')[:5]
    
    hostels_qs = Hostel.objects.all().annotate(
        total_rooms_count=Count('rooms'),
        available_rooms_count=Count('rooms', filter=Q(rooms__status='AVAILABLE')),
        occupied_rooms_count=Count('rooms', filter=Q(rooms__status='OCCUPIED')),
    )

    hostels_map_data = [
        {
            'id': h.id,
            'name': h.name,
            'code': h.code,
            'address': h.address or '',
            'lat': float(h.latitude) if h.latitude is not None else None,
            'lng': float(h.longitude) if h.longitude is not None else None,
            'total_rooms': h.total_rooms_count,
            'available_rooms': h.available_rooms_count,
            'occupied_rooms': h.occupied_rooms_count,
            'total_floors': h.total_floors,
            'image_url': h.image.url if h.image else '',
            'status': h.status.lower()
        }
        for h in hostels_qs
    ]
    
    monthly_allocations = []
    month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    current_year = timezone.now().year
    
    for month in range(1, 13):
        count = RoomAllocation.objects.filter(
            allocated_date__month=month,
            allocated_date__year=current_year
        ).count()
        monthly_allocations.append(count)
    
    context = {
        'user': request.user,
        'total_hostels': total_hostels,
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'occupied_rooms': occupied_rooms,
        'maintenance_rooms': maintenance_rooms,
        'active_allocations': active_allocations,
        'total_students': total_students,
        'available_percentage': available_percentage,
        'allocation_percentage': allocation_percentage,
        'occupancy_rate': occupancy_rate,
        'recent_allocations': recent_allocations,
        'hostels_map_data': hostels_map_data,
        'monthly_allocations': monthly_allocations,
        'month_labels': month_labels,
        'active_sb': 'hostel_dashboard'
    }
    return render(request, 'Blaze_Hostel/hostel_dashboard.html', context)


@login_required
def hostel_list(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        messages.error(request, "Permission denied.")
        return redirect("login")
    
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', 'all')
    
    hostels = Hostel.objects.all().annotate(
        room_count=Count('rooms'),
        occupied_count=Count('rooms', filter=Q(rooms__status='OCCUPIED')),
        student_count=Count('rooms__allocations', filter=Q(rooms__allocations__status='ACTIVE'), distinct=True)
    )
    
    if search:
        hostels = hostels.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(address__icontains=search)
        )
    
    if status_filter != 'all':
        hostels = hostels.filter(status=status_filter.upper())
    
    paginator = Paginator(hostels, 10)
    page = request.GET.get('page')
    hostels_page = paginator.get_page(page)
    
    context = {
        'user': request.user,
        'hostels': hostels_page,
        'active_sb': 'hostel_list',
        'search': search,
        'status_filter': status_filter,
    }
    return render(request, 'Blaze_Hostel/hostel_list.html', context)


@login_required
def hostel_detail(request, uuid, hostel_id):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    hostel = get_object_or_404(Hostel, id=hostel_id)
    rooms = Room.objects.filter(hostel=hostel).order_by('floor', 'room_number')
    allocations = RoomAllocation.objects.filter(
        room__hostel=hostel,
        status='ACTIVE'
    ).select_related('student', 'room')
    
    context = {
        'user': request.user,
        'hostel': hostel,
        'rooms': rooms,
        'allocations': allocations,
        'active_sb': 'hostel_list'
    }
    return render(request, 'Blaze_Hostel/hostel_detail.html', context)


@login_required
@require_http_methods(["POST"])
def add_hostel_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    name = request.POST.get('name', '').strip()
    code = request.POST.get('code', '').strip().upper()
    address = request.POST.get('address', '').strip()
    contact_number = request.POST.get('contact_number', '').strip()
    description = request.POST.get('description', '').strip()
    gender_restriction = request.POST.get('gender_restriction', 'ANY')
    total_floors_raw = request.POST.get('total_floors', '').strip()
    latitude_raw = request.POST.get('latitude', '').strip()
    longitude_raw = request.POST.get('longitude', '').strip()
    image = request.FILES.get('image')
    
    if not name:
        return JsonResponse({'success': False, 'error': 'Hostel name is required'})
    
    if not code:
        return JsonResponse({'success': False, 'error': 'Hostel code is required'})
    
    if Hostel.objects.filter(code=code).exists():
        return JsonResponse({'success': False, 'error': f'Hostel with code "{code}" already exists'})
    
    if Hostel.objects.filter(name=name).exists():
        return JsonResponse({'success': False, 'error': f'Hostel with name "{name}" already exists'})
    
    latitude = None
    longitude = None
    try:
        if latitude_raw and longitude_raw:
            latitude = float(latitude_raw)
            longitude = float(longitude_raw)
    except ValueError:
        latitude = None
        longitude = None

    try:
        total_floors = int(total_floors_raw) if total_floors_raw else 1
        if total_floors < 1:
            total_floors = 1
    except ValueError:
        total_floors = 1
    
    try:
        hostel = Hostel.objects.create(
            name=name,
            code=code,
            address=address or None,
            contact_number=contact_number or None,
            description=description or None,
            gender_restriction=gender_restriction,
            latitude=latitude,
            longitude=longitude,
            total_floors=total_floors,
            image=image,
            status='ACTIVE',
            created_by=request.user
        )
        
        HostelAuditLog.objects.create(
            user=request.user,
            action='CREATE',
            module='HOSTEL',
            object_type='Hostel',
            object_id=hostel.id,
            changes={'name': name, 'code': code, 'gender_restriction': gender_restriction}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Hostel "{name}" created successfully!',
            'hostel_id': hostel.id,
            'hostel_name': hostel.name,
            'hostel_code': hostel.code,
            'hostel_total_floors': hostel.total_floors,
            'hostel_image_url': hostel.image.url if hostel.image else ''
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def update_hostel_json(request, uuid, hostel_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    hostel = get_object_or_404(Hostel, id=hostel_id)
    
    name = request.POST.get('name', '').strip()
    code = request.POST.get('code', '').strip().upper()
    address = request.POST.get('address', '').strip()
    contact_number = request.POST.get('contact_number', '').strip()
    description = request.POST.get('description', '').strip()
    gender_restriction = request.POST.get('gender_restriction', 'ANY')
    status = request.POST.get('status', 'ACTIVE')
    total_floors_raw = request.POST.get('total_floors', '').strip()
    latitude_raw = request.POST.get('latitude', '').strip()
    longitude_raw = request.POST.get('longitude', '').strip()
    
    if not name:
        return JsonResponse({'success': False, 'error': 'Hostel name is required'})
    
    if not code:
        return JsonResponse({'success': False, 'error': 'Hostel code is required'})
    
    if Hostel.objects.filter(code=code).exclude(id=hostel_id).exists():
        return JsonResponse({'success': False, 'error': f'Hostel with code "{code}" already exists'})
    
    if Hostel.objects.filter(name=name).exclude(id=hostel_id).exists():
        return JsonResponse({'success': False, 'error': f'Hostel with name "{name}" already exists'})
    
    try:
        if latitude_raw and longitude_raw:
            latitude = float(latitude_raw)
            longitude = float(longitude_raw)
        else:
            latitude = None
            longitude = None
    except ValueError:
        latitude = None
        longitude = None
    
    try:
        total_floors = int(total_floors_raw) if total_floors_raw else 1
        if total_floors < 1:
            total_floors = 1
    except ValueError:
        total_floors = 1
    
    try:
        hostel.name = name
        hostel.code = code
        hostel.address = address or None
        hostel.contact_number = contact_number or None
        hostel.description = description or None
        hostel.gender_restriction = gender_restriction
        hostel.status = status
        hostel.total_floors = total_floors
        hostel.latitude = latitude
        hostel.longitude = longitude
        
        if request.FILES.get('image'):
            hostel.image = request.FILES.get('image')
        
        hostel.save()
        
        HostelAuditLog.objects.create(
            user=request.user,
            action='UPDATE',
            module='HOSTEL',
            object_type='Hostel',
            object_id=hostel.id,
            changes={'name': name, 'code': code, 'status': status}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Hostel "{name}" updated successfully!',
            'hostel_id': hostel.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def delete_hostel_json(request, uuid, hostel_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    hostel = get_object_or_404(Hostel, id=hostel_id)
    
    if not hostel.can_delete():
        occupied_rooms = hostel.get_occupied_rooms_count()
        students_count = hostel.get_students_count()
        
        return JsonResponse({
            'success': False,
            'error': f'Cannot delete "{hostel.name}" because it has {occupied_rooms} occupied room(s) and {students_count} student(s) allocated.',
            'occupied_rooms': occupied_rooms,
            'students_count': students_count
        })
    
    if Room.objects.filter(hostel=hostel).exists():
        return JsonResponse({
            'success': False,
            'error': f'Cannot delete "{hostel.name}" because it has rooms. Please delete all rooms first.'
        })
    
    try:
        hostel_name = hostel.name
        hostel.delete()
        
        HostelAuditLog.objects.create(
            user=request.user,
            action='DELETE',
            module='HOSTEL',
            object_type='Hostel',
            object_id=hostel_id,
            changes={'name': hostel_name}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Hostel "{hostel_name}" deleted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def hostel_details_json(request, uuid, hostel_id):
    try:
        user_uuid = str(request.user.uuid)
        url_uuid = str(uuid)
        
        if user_uuid != url_uuid:
            return JsonResponse({
                'success': False, 
                'error': 'Unauthorized - UUID mismatch',
                'debug': f'User UUID: {user_uuid}, URL UUID: {url_uuid}'
            }, status=401)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'UUID error: {str(e)}'}, status=401)
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    try:
        hostel = get_object_or_404(Hostel, id=hostel_id)
        
        room_count = Room.objects.filter(hostel=hostel).count()
        occupied_count = Room.objects.filter(hostel=hostel, status='OCCUPIED').count()
        available_count = Room.objects.filter(hostel=hostel, status='AVAILABLE').count()
        student_count = RoomAllocation.objects.filter(
            room__hostel=hostel,
            status='ACTIVE'
        ).values('student').distinct().count()
        
        has_occupied_rooms = Room.objects.filter(hostel=hostel, status='OCCUPIED').exists()
        has_active_allocations = RoomAllocation.objects.filter(
            room__hostel=hostel,
            status='ACTIVE'
        ).exists()
        can_delete = not (has_occupied_rooms or has_active_allocations)
        
        return JsonResponse({
            'success': True,
            'hostel': {
                'id': hostel.id,
                'name': hostel.name,
                'code': hostel.code,
                'address': hostel.address or '',
                'contact_number': hostel.contact_number or '',
                'description': hostel.description or '',
                'gender_restriction': hostel.gender_restriction,
                'gender_restriction_display': hostel.get_gender_restriction_display(),
                'status': hostel.status,
                'status_display': hostel.get_status_display(),
                'total_floors': hostel.total_floors,
                'latitude': float(hostel.latitude) if hostel.latitude else None,
                'longitude': float(hostel.longitude) if hostel.longitude else None,
                'image_url': hostel.image.url if hostel.image else '',
                'created_at': hostel.created_at.strftime('%d %b %Y, %I:%M %p') if hostel.created_at else '',
                'room_count': room_count,
                'occupied_count': occupied_count,
                'available_count': available_count,
                'student_count': student_count,
                'can_delete': can_delete
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def student_list(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        messages.error(request, "Permission denied.")
        return redirect("login")
    
    search = request.GET.get('search', '').strip()
    hostel_filter = request.GET.get('hostel', 'all')
    status_filter = request.GET.get('status', 'all')
    
    students = User.objects.filter(is_student=True)
    
    students = students.annotate(
        has_allocation=Exists(RoomAllocation.objects.filter(student=OuterRef('pk'), status='ACTIVE')),
        hostel_name=Subquery(
            RoomAllocation.objects.filter(
                student=OuterRef('pk'),
                status='ACTIVE'
            ).values('room__hostel__name')[:1]
        ),
        room_number=Subquery(
            RoomAllocation.objects.filter(
                student=OuterRef('pk'),
                status='ACTIVE'
            ).values('room__room_number')[:1]
        )
    )
    
    if search:
        students = students.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(username__icontains=search) |
            Q(email__icontains=search)
        )
  
    if hostel_filter != 'all':
        students = students.filter(
            id__in=RoomAllocation.objects.filter(
                room__hostel_id=hostel_filter,
                status='ACTIVE'
            ).values_list('student_id', flat=True)
        )
    
    if status_filter == 'allocated':
        students = students.filter(has_allocation=True)
    elif status_filter == 'unallocated':
        students = students.filter(has_allocation=False)
    
    paginator = Paginator(students, 15)
    page = request.GET.get('page')
    students_page = paginator.get_page(page)
    
    hostels = Hostel.objects.filter(status='ACTIVE')
    
    context = {
        'user': request.user,
        'students': students_page,
        'hostels': hostels,
        'active_sb': 'student_list',
        'search': search,
        'hostel_filter': hostel_filter,
        'status_filter': status_filter,
    }
    return render(request, 'Blaze_Hostel/student_list.html', context)


@login_required
def student_detail_json(request, uuid, student_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    student = get_object_or_404(User, id=student_id, is_student=True)
    
    allocation = RoomAllocation.objects.filter(
        student=student,
        status='ACTIVE'
    ).select_related('room', 'room__hostel').first()
    
    history = RoomAllocation.objects.filter(
        student=student
    ).select_related('room', 'room__hostel').order_by('-allocated_date')
    
    data = {
        'success': True,
        'student': {
            'id': student.id,
            'full_name': student.full_name,
            'username': student.username,
            'email': student.email,
            'first_name': student.first_name or '',
            'last_name': student.last_name or '',
            'account_status': student.account_status,
            'mobile_number': getattr(student, 'mobile_number', 'N/A'),
            'gender': getattr(student, 'gender', 'N/A'),
            'date_of_birth': getattr(student, 'date_of_birth', None),
        },
        'current_allocation': {
            'id': allocation.id if allocation else None,
            'room_number': allocation.room.room_number if allocation else None,
            'hostel_name': allocation.room.hostel.name if allocation else None,
            'move_in_date': allocation.move_in_date.strftime('%d %b %Y') if allocation and allocation.move_in_date else None,
            'allocated_date': allocation.allocated_date.strftime('%d %b %Y') if allocation else None,
        } if allocation else None,
        'allocation_history': [
            {
                'id': a.id,
                'room_number': a.room.room_number,
                'hostel_name': a.room.hostel.name,
                'move_in_date': a.move_in_date.strftime('%d %b %Y') if a.move_in_date else None,
                'move_out_date': a.move_out_date.strftime('%d %b %Y') if a.move_out_date else None,
                'status': a.status,
                'status_display': a.get_status_display(),
                'allocated_date': a.allocated_date.strftime('%d %b %Y')
            }
            for a in history
        ]
    }
    
    return JsonResponse(data)


@login_required
def room_management(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        messages.error(request, "Permission denied.")
        return redirect("login")
    
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', 'all')
    hostel_filter = request.GET.get('hostel', 'all')
    
    rooms = Room.objects.select_related('hostel', 'created_by').all()
    
    if search:
        rooms = rooms.filter(
            Q(room_number__icontains=search) |
            Q(hostel__name__icontains=search)
        )
    
    if status_filter != 'all':
        rooms = rooms.filter(status=status_filter.upper())
    
    if hostel_filter != 'all':
        rooms = rooms.filter(hostel_id=hostel_filter)
    
    paginator = Paginator(rooms, 15)
    page = request.GET.get('page')
    rooms_page = paginator.get_page(page)
    
    hostels = Hostel.objects.filter(status='ACTIVE')
    
    context = {
        'user': request.user,
        'rooms': rooms_page,
        'hostels': hostels,
        'active_sb': 'room_management',
        'search': search,
        'status_filter': status_filter,
        'hostel_filter': hostel_filter,
    }
    return render(request, 'Blaze_Hostel/room_management.html', context)


@login_required
def add_room_page(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        messages.error(request, "Permission denied.")
        return redirect("login")
    
    hostels = Hostel.objects.filter(status='ACTIVE')
    hostel_floors_map = {str(h.id): h.total_floors for h in hostels}

    context = {
        'user': request.user,
        'hostels': hostels,
        'hostel_floors_map': hostel_floors_map,
        'active_sb': 'add_room'
    }
    return render(request, 'Blaze_Hostel/add_room.html', context)


@login_required
@require_http_methods(["POST"])
def add_room_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    hostel_id = request.POST.get('hostel_id')
    room_number = request.POST.get('room_number')
    floor_raw = request.POST.get('floor')
    capacity_raw = request.POST.get('capacity')
    rent_raw = request.POST.get('rent_per_month')
    amenities = request.POST.get('amenities', '')
    status = request.POST.get('status', 'AVAILABLE')
    image = request.FILES.get('image')
    
    if not all([hostel_id, room_number, floor_raw, capacity_raw, rent_raw]):
        return JsonResponse({'success': False, 'error': 'All required fields must be filled'})
    
    try:
        floor = int(floor_raw)
        capacity = int(capacity_raw)
        rent_per_month = float(rent_raw)
    except ValueError as e:
        return JsonResponse({'success': False, 'error': f'Invalid number format: {str(e)}'})
    
    if Room.objects.filter(hostel_id=hostel_id, room_number=room_number).exists():
        return JsonResponse({'success': False, 'error': 'Room number already exists in this hostel'})
    
    try:
        room = Room.objects.create(
            hostel_id=hostel_id,
            room_number=room_number,
            floor=floor,
            capacity=capacity,
            current_occupancy=0,
            rent_per_month=rent_per_month,
            amenities=amenities,
            image=image,
            created_by=request.user,
            is_available=True,
            status=status if status != 'RESERVED' else 'AVAILABLE'
        )
        
        HostelAuditLog.objects.create(
            user=request.user,
            action='CREATE',
            module='ROOM',
            object_type='Room',
            object_id=room.id,
            changes={'room_number': room_number, 'hostel': room.hostel.name}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Room {room_number} added successfully!',
            'room_id': room.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def delete_room_json(request, uuid, room_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        room = get_object_or_404(Room, id=room_id)
        
        if room.status == 'OCCUPIED':
            return JsonResponse({'success': False, 'error': 'Cannot delete occupied room'})
        
        room.delete()
        return JsonResponse({'success': True, 'message': 'Room deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def room_details_json(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    return JsonResponse({
        'success': True,
        'room': {
            'id': room.id,
            'room_number': room.room_number,
            'hostel': room.hostel.name,
            'hostel_id': room.hostel.id,
            'floor': room.floor,
            'capacity': room.capacity,
            'current_occupancy': room.current_occupancy,
            'rent_per_month': str(room.rent_per_month),
            'status': room.status,
            'status_display': room.get_status_display(),
            'amenities': room.amenities or '',
            'image_url': room.image.url if room.image else '',
            'created_at': room.created_at.strftime('%d %b %Y, %I:%M %p') if room.created_at else '',
        }
    })


@login_required
@require_http_methods(["POST"])
def update_room_json(request, room_id):
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    room = get_object_or_404(Room, id=room_id)
    
    hostel_id = request.POST.get('hostel_id')
    room_number = request.POST.get('room_number')
    floor = request.POST.get('floor')
    capacity = request.POST.get('capacity')
    rent_per_month = request.POST.get('rent_per_month')
    status = request.POST.get('status')
    amenities = request.POST.get('amenities', '')
    
    if not all([hostel_id, room_number, floor, capacity, rent_per_month]):
        return JsonResponse({'success': False, 'error': 'All required fields must be filled'})
    
    try:
        room.hostel_id = hostel_id
        room.room_number = room_number
        room.floor = int(floor)
        room.capacity = int(capacity)
        room.rent_per_month = float(rent_per_month)
        room.status = status
        room.amenities = amenities
        room.save()
        
        return JsonResponse({'success': True, 'message': 'Room updated successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def allocate_room(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        messages.error(request, "Permission denied.")
        return redirect("login")
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        room_id = request.POST.get('room_id')
        move_in_date = request.POST.get('move_in_date')
        remarks = request.POST.get('remarks', '')
        force = request.POST.get('force') == 'true'
        
        user = get_object_or_404(User, id=user_id)
        room = get_object_or_404(Room, id=room_id, is_available=True)
        
        if RoomAllocation.objects.filter(student=user, status='ACTIVE').exists():
            return JsonResponse({'success': False, 'conflict': 'already_allocated', 'error': 'User already has an active room allocation.'})
        
        if room.current_occupancy >= room.capacity:
            return JsonResponse({'success': False, 'conflict': 'room_full', 'error': 'Room is full.'})

        user_gender = (getattr(user, 'gender', '') or '').strip().upper()
        hostel_gender = room.hostel.gender_restriction
        if not force and hostel_gender != 'ANY' and user_gender and user_gender != hostel_gender:
            return JsonResponse({
                'success': False,
                'conflict': 'gender_mismatch',
                'error': f'{room.hostel.name} is {room.hostel.get_gender_restriction_display()}, but this user is registered as {user_gender.title()}.'
            })
        
        allocation = RoomAllocation.objects.create(
            student=user,
            room=room,
            allocated_by=request.user,
            move_in_date=move_in_date,
            status='ACTIVE',
            remarks=remarks
        )
        
        room.current_occupancy += 1
        room.save()
        
        return JsonResponse({'success': True, 'message': f'Room {room.room_number} allocated to {user.full_name} successfully!'})
    
    from Admin.bela_admin.models import Department
    
    hostels = Hostel.objects.filter(status='ACTIVE')
    departments = Department.objects.filter(status='ACTIVE').order_by('department_name')
    
    context = {
        'user': request.user,
        'hostels': hostels,
        'departments': departments,
        'active_sb': 'allocate_room'
    }
    return render(request, 'Blaze_Hostel/allocate_room.html', context)


@login_required
def allocations_list(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        messages.error(request, "Permission denied.")
        return redirect("login")
    
    status_filter = request.GET.get('status', 'all')
    search = request.GET.get('search', '').strip()
    
    allocations = RoomAllocation.objects.select_related(
        'student', 'room', 'room__hostel', 'allocated_by'
    ).all()
    
    if status_filter != 'all':
        allocations = allocations.filter(status=status_filter.upper())
    
    if search:
        allocations = allocations.filter(
            Q(student__full_name__icontains=search) |
            Q(student__username__icontains=search) |
            Q(room__room_number__icontains=search) |
            Q(room__hostel__name__icontains=search)
        )
    
    paginator = Paginator(allocations, 15)
    page = request.GET.get('page')
    allocations_page = paginator.get_page(page)
    
    context = {
        'user': request.user,
        'allocations': allocations_page,
        'active_sb': 'allocations',
        'status_filter': status_filter,
        'search': search,
    }
    return render(request, 'Blaze_Hostel/allocations.html', context)


@login_required
def get_users_by_department_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    department_id = request.GET.get('department_id')
    user_type = request.GET.get('user_type', 'student')
    
    try:
        from Students.models import StudentProfile, FacultyProfile, StaffProfile
        from Admin.bela_admin.models import AcademicProgram
        from Admin.models import User
        
        users = User.objects.filter(account_status='ACTIVE')
        
        if user_type == 'student':
            if not department_id:
                return JsonResponse([], safe=False)
            
            # Get all students (even those without allocations)
            program_ids = AcademicProgram.objects.filter(
                department_id=department_id,
                status='ACTIVE'
            ).values_list('program_id', flat=True)
            
            print(f"Department ID: {department_id}")
            print(f"Program IDs found: {list(program_ids)}")
            
            if program_ids:
                student_ids = StudentProfile.objects.filter(
                    program_id__in=program_ids
                ).values_list('user_id', flat=True)
                print(f"Student IDs from profiles: {list(student_ids)}")
                
                if student_ids:
                    users = users.filter(id__in=student_ids)
                    print(f"Users before allocation filter: {users.count()}")
                else:
                    # Try to get students directly from User model with is_student=True
                    users = users.filter(is_student=True)
                    print(f"No student profiles found, using is_student flag: {users.count()}")
            else:
                # No programs found, try to get students from User model
                users = users.filter(is_student=True)
                print(f"No programs found, using is_student flag: {users.count()}")
        
        elif user_type == 'faculty':
            faculty_user_ids = list(FacultyProfile.objects.all().values_list('user_id', flat=True))
            faculty_flag_users = list(User.objects.filter(is_faculty=True).values_list('id', flat=True))
            all_faculty_ids = list(set(faculty_user_ids + faculty_flag_users))
            users = users.filter(id__in=all_faculty_ids)
            
        elif user_type == 'staff':
            staff_user_ids = list(StaffProfile.objects.all().values_list('user_id', flat=True))
            staff_flag_users = list(User.objects.filter(is_staff=True).values_list('id', flat=True))
            all_staff_ids = list(set(staff_user_ids + staff_flag_users))
            users = users.filter(id__in=all_staff_ids)
        
        else:
            return JsonResponse([], safe=False)
        
        # Exclude users with active allocations
        allocated_ids = RoomAllocation.objects.filter(status='ACTIVE').values_list('student_id', flat=True)
        users = users.exclude(id__in=allocated_ids)
        
        print(f"Final available {user_type} count: {users.count()}")
        
        data = []
        for user in users:
            role = 'student'
            if user.is_faculty:
                role = 'faculty'
            elif user.is_staff:
                role = 'staff'
            
            data.append({
                'id': user.id,
                'full_name': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username,
                'username': user.username,
                'email': user.email,
                'role': role
            })
        
        return JsonResponse(data, safe=False)
        
    except Exception as e:
        import logging
        logging.error(f"Error in get_users_by_department: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse([], safe=False)


@login_required
def get_user_details_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)
    
    user_id = request.GET.get('user_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'error': 'User ID required'})
    
    try:
        from Students.models import StudentProfile, FacultyProfile, StaffProfile, StudentAcademicProfile
        from Admin.bela_admin.models import AcademicProgram, Department
        
        try:
            user = User.objects.get(id=int(user_id))
        except (ValueError, TypeError):
            user = User.objects.get(username=user_id)
        
        user_data = {
            'id': user.id,
            'full_name': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'account_status': user.account_status,
            'mobile_number': getattr(user, 'mobile_number', 'N/A'),
            'gender': getattr(user, 'gender', 'N/A'),
            'date_of_birth': getattr(user, 'date_of_birth', None),
        }
        
        if user.is_student:
            try:
                profile = StudentProfile.objects.get(user=user)
                user_data['user_id'] = profile.student_number or 'N/A'
                user_data['role'] = 'student'
                
                try:
                    academic = StudentAcademicProfile.objects.get(student=profile)
                    if academic.department_id:
                        try:
                            dept = Department.objects.get(department_id=academic.department_id)
                            user_data['department_name'] = dept.department_name
                        except Department.DoesNotExist:
                            user_data['department_name'] = 'N/A'
                    else:
                        user_data['department_name'] = 'N/A'
                    
                    if academic.program_id:
                        try:
                            program = AcademicProgram.objects.get(program_id=academic.program_id)
                            user_data['program_name'] = program.program_name
                        except AcademicProgram.DoesNotExist:
                            user_data['program_name'] = 'N/A'
                    else:
                        user_data['program_name'] = 'N/A'
                except StudentAcademicProfile.DoesNotExist:
                    user_data['department_name'] = 'N/A'
                    user_data['program_name'] = 'N/A'
                    
            except StudentProfile.DoesNotExist:
                user_data['user_id'] = 'N/A'
                user_data['role'] = 'student'
                user_data['department_name'] = 'N/A'
                user_data['program_name'] = 'N/A'
        
        elif user.is_faculty:
            try:
                profile = FacultyProfile.objects.get(user=user)
                user_data['user_id'] = profile.faculty_id or 'N/A'
                user_data['role'] = 'faculty'
                if profile.department_id:
                    try:
                        dept = Department.objects.get(department_id=profile.department_id)
                        user_data['department_name'] = dept.department_name
                    except Department.DoesNotExist:
                        user_data['department_name'] = 'N/A'
                else:
                    user_data['department_name'] = 'N/A'
            except FacultyProfile.DoesNotExist:
                user_data['user_id'] = 'N/A'
                user_data['role'] = 'faculty'
                user_data['department_name'] = 'N/A'
        
        elif user.is_staff:
            try:
                profile = StaffProfile.objects.get(user=user)
                user_data['user_id'] = profile.staff_id or 'N/A'
                user_data['role'] = 'staff'
                if profile.department_id:
                    try:
                        dept = Department.objects.get(department_id=profile.department_id)
                        user_data['department_name'] = dept.department_name
                    except Department.DoesNotExist:
                        user_data['department_name'] = 'N/A'
                else:
                    user_data['department_name'] = 'N/A'
            except StaffProfile.DoesNotExist:
                user_data['user_id'] = 'N/A'
                user_data['role'] = 'staff'
                user_data['department_name'] = 'N/A'
        else:
            user_data['role'] = 'user'
            user_data['department_name'] = 'N/A'
        
        current_allocation = RoomAllocation.objects.filter(
            student=user, 
            status='ACTIVE'
        ).select_related('room', 'room__hostel').first()
        
        if current_allocation:
            user_data['current_allocation'] = {
                'room_number': current_allocation.room.room_number,
                'hostel_name': current_allocation.room.hostel.name,
                'allocated_date': current_allocation.allocated_date.strftime('%d %b %Y'),
                'move_in_date': current_allocation.move_in_date.strftime('%d %b %Y') if current_allocation.move_in_date else 'N/A',
                'status': current_allocation.status
            }
        else:
            user_data['current_allocation'] = None
        
        return JsonResponse({'success': True, 'user': user_data})
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': f'User not found: {user_id}'})
    except Exception as e:
        import logging
        logging.error(f"Error in get_user_details: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_students_by_department_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    department_id = request.GET.get('department_id')
    
    if not department_id:
        return JsonResponse([], safe=False)
    
    try:
        from Students.models import StudentProfile
        from Admin.bela_admin.models import AcademicProgram
        from Admin.models import User
        
        program_ids = AcademicProgram.objects.filter(
            department_id=department_id,
            status='ACTIVE'
        ).values_list('program_id', flat=True)
        
        if not program_ids:
            return JsonResponse([], safe=False)
        
        student_ids = StudentProfile.objects.filter(
            program_id__in=program_ids
        ).values_list('user_id', flat=True)
        
        students = User.objects.filter(
            id__in=student_ids,
            is_student=True,
            account_status='ACTIVE'
        ).exclude(
            id__in=RoomAllocation.objects.filter(status='ACTIVE').values_list('student_id', flat=True)
        )
        
        data = []
        for student in students:
            try:
                profile = StudentProfile.objects.get(user=student)
                student_number = profile.student_number or 'N/A'
            except StudentProfile.DoesNotExist:
                student_number = 'N/A'
            
            data.append({
                'id': student.id,
                'full_name': f"{student.first_name or ''} {student.last_name or ''}".strip() or student.username,
                'username': student.username,
                'email': student.email,
                'student_number': student_number
            })
        
        return JsonResponse(data, safe=False)
        
    except Exception as e:
        return JsonResponse([], safe=False)


@login_required
def get_student_details_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)
    
    student_id = request.GET.get('student_id')
    
    if not student_id:
        return JsonResponse({'success': False, 'error': 'Student ID required'})
    
    try:
        from Students.models import StudentProfile, StudentAcademicProfile
        from Admin.bela_admin.models import AcademicProgram, Department
        
        try:
            student = User.objects.get(id=int(student_id), is_student=True)
        except (ValueError, TypeError):
            student = User.objects.get(username=student_id, is_student=True)
        
        student_data = {
            'id': student.id,
            'full_name': f"{student.first_name or ''} {student.last_name or ''}".strip() or student.username,
            'username': student.username,
            'email': student.email,
            'first_name': student.first_name or '',
            'last_name': student.last_name or '',
            'account_status': student.account_status,
            'mobile_number': getattr(student, 'mobile_number', 'N/A'),
            'gender': getattr(student, 'gender', 'N/A'),
            'date_of_birth': getattr(student, 'date_of_birth', None),
        }
        
        try:
            profile = StudentProfile.objects.get(user=student)
            student_data['student_number'] = profile.student_number or 'N/A'
            student_data['preferred_name'] = profile.preferred_name or 'N/A'
            student_data['university_email'] = profile.university_email or 'N/A'
            student_data['personal_email'] = profile.personal_email or 'N/A'
            student_data['citizenship_status'] = profile.citizenship_status or 'N/A'
            student_data['marital_status'] = profile.marital_status or 'N/A'
            student_data['academic_level'] = profile.academic_level or 'N/A'
            student_data['current_status'] = profile.current_status or 'N/A'
            student_data['cumulative_gpa'] = str(profile.cumulative_gpa) if profile.cumulative_gpa else 'N/A'
            
            try:
                academic = StudentAcademicProfile.objects.get(student=profile)
                student_data['major'] = academic.major or 'N/A'
                student_data['minor'] = academic.minor or 'N/A'
                student_data['concentration'] = academic.concentration or 'N/A'
                student_data['catalog_year'] = academic.catalog_year or 'N/A'
                
                if academic.department_id:
                    try:
                        dept = Department.objects.get(department_id=academic.department_id)
                        student_data['department_name'] = dept.department_name
                    except Department.DoesNotExist:
                        student_data['department_name'] = 'N/A'
                else:
                    student_data['department_name'] = 'N/A'
                
                if academic.program_id:
                    try:
                        program = AcademicProgram.objects.get(program_id=academic.program_id)
                        student_data['program_name'] = program.program_name
                    except AcademicProgram.DoesNotExist:
                        student_data['program_name'] = 'N/A'
                else:
                    student_data['program_name'] = 'N/A'
                    
            except StudentAcademicProfile.DoesNotExist:
                student_data['department_name'] = 'N/A'
                student_data['program_name'] = 'N/A'
                
        except StudentProfile.DoesNotExist:
            student_data['student_number'] = 'N/A'
            student_data['preferred_name'] = 'N/A'
            student_data['university_email'] = 'N/A'
            student_data['personal_email'] = 'N/A'
        
        current_allocation = RoomAllocation.objects.filter(
            student=student, 
            status='ACTIVE'
        ).select_related('room', 'room__hostel').first()
        
        if current_allocation:
            student_data['current_allocation'] = {
                'room_number': current_allocation.room.room_number,
                'hostel_name': current_allocation.room.hostel.name,
                'allocated_date': current_allocation.allocated_date.strftime('%d %b %Y'),
                'move_in_date': current_allocation.move_in_date.strftime('%d %b %Y') if current_allocation.move_in_date else 'N/A',
                'status': current_allocation.status
            }
        else:
            student_data['current_allocation'] = None
        
        return JsonResponse({'success': True, 'student': student_data})
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': f'Student not found: {student_id}'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def hostel_rooms_map_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    hostel_id = request.GET.get('hostel_id')
    if not hostel_id:
        return JsonResponse([], safe=False)

    rooms = Room.objects.filter(hostel_id=hostel_id).select_related('hostel').order_by('floor', 'room_number')

    data = []
    for room in rooms:
        occupants = RoomAllocation.objects.filter(room=room, status='ACTIVE').select_related('student')
        data.append({
            'id': room.id,
            'room_number': room.room_number,
            'floor': room.floor,
            'capacity': room.capacity,
            'current_occupancy': room.current_occupancy,
            'status': room.status,
            'status_display': room.get_status_display(),
            'rent_per_month': str(room.rent_per_month),
            'image_url': room.image.url if room.image else '',
            'occupants': [
                {
                    'allocation_id': a.id,
                    'student_id': a.student.id,
                    'name': a.student.full_name,
                    'move_in_date': a.move_in_date.strftime('%d %b %Y') if a.move_in_date else '',
                }
                for a in occupants
            ],
        })

    return JsonResponse(data, safe=False)


@login_required
def unallocated_users_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    user_type = request.GET.get('user_type', 'all')
    search = request.GET.get('search', '').strip()

    users = User.objects.filter(account_status='ACTIVE').exclude(
        id__in=RoomAllocation.objects.filter(status='ACTIVE').values_list('student_id', flat=True)
    )

    if user_type == 'student':
        users = users.filter(is_student=True)
    elif user_type == 'faculty':
        users = users.filter(is_faculty=True)
    elif user_type == 'staff':
        users = users.filter(is_staff=True)

    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(username__icontains=search)
        )

    data = []
    for u in users[:200]:
        role = 'student'
        if u.is_faculty:
            role = 'faculty'
        elif u.is_staff:
            role = 'staff'
        
        data.append({
            'id': u.id,
            'full_name': u.full_name,
            'username': u.username,
            'gender': (getattr(u, 'gender', '') or '').strip().upper(),
            'role': role
        })
    
    return JsonResponse(data, safe=False)


@login_required
def unallocated_students_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    search = request.GET.get('search', '').strip()

    students = User.objects.filter(
        is_student=True,
        account_status='ACTIVE'
    ).exclude(
        id__in=RoomAllocation.objects.filter(status='ACTIVE').values_list('student_id', flat=True)
    )

    if search:
        students = students.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(username__icontains=search)
        )

    data = [
        {
            'id': s.id,
            'full_name': s.full_name,
            'username': s.username,
            'gender': (getattr(s, 'gender', '') or '').strip().upper(),
        }
        for s in students[:200]
    ]
    return JsonResponse(data, safe=False)


@login_required
def get_available_rooms_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    hostel_id = request.GET.get('hostel_id')
    
    if not hostel_id:
        return JsonResponse([], safe=False)
    
    try:
        hostel_id = int(hostel_id)
        
        rooms = Room.objects.filter(
            hostel_id=hostel_id,
            status='AVAILABLE'
        ).exclude(
            status='OCCUPIED'
        ).values(
            'id', 'room_number', 'capacity', 'current_occupancy', 
            'rent_per_month', 'status'
        )
        
        room_list = []
        for room in rooms:
            available_slots = room['capacity'] - room['current_occupancy']
            if available_slots > 0:
                room_list.append({
                    'id': room['id'],
                    'room_number': room['room_number'],
                    'capacity': room['capacity'],
                    'current_occupancy': room['current_occupancy'],
                    'available_slots': available_slots,
                    'rent_per_month': float(room['rent_per_month']) if room['rent_per_month'] else 0,
                    'status': room['status']
                })
        
        return JsonResponse(room_list, safe=False)
        
    except ValueError:
        return JsonResponse([], safe=False)
    except Exception as e:
        import logging
        logging.error(f"Error loading rooms: {e}")
        return JsonResponse([], safe=False)


@login_required
@require_http_methods(["POST"])
def bulk_allocate_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})

    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})

    room_id = request.POST.get('room_id')
    move_in_date = request.POST.get('move_in_date')
    remarks = request.POST.get('remarks', '')
    force = request.POST.get('force') == 'true'
    user_ids = request.POST.getlist('user_ids[]') or request.POST.getlist('user_ids')

    if not room_id or not move_in_date or not user_ids:
        return JsonResponse({'success': False, 'error': 'room_id, move_in_date and at least one user are required'})

    room = get_object_or_404(Room, id=room_id)

    available_slots = room.capacity - room.current_occupancy
    if len(user_ids) > available_slots:
        return JsonResponse({
            'success': False,
            'error': f'Only {available_slots} slot(s) left in Room {room.room_number}, but {len(user_ids)} users were selected.'
        })

    results = []
    allocated_count = 0

    for uid in user_ids:
        try:
            user = User.objects.get(id=uid)
        except User.DoesNotExist:
            results.append({'user_id': uid, 'success': False, 'error': 'User not found'})
            continue

        if RoomAllocation.objects.filter(student=user, status='ACTIVE').exists():
            results.append({'user_id': uid, 'name': user.full_name, 'success': False, 'error': 'Already allocated'})
            continue

        user_gender = (getattr(user, 'gender', '') or '').strip().upper()
        hostel_gender = room.hostel.gender_restriction
        if not force and hostel_gender != 'ANY' and user_gender and user_gender != hostel_gender:
            results.append({'user_id': uid, 'name': user.full_name, 'success': False, 'error': 'Gender/hostel eligibility mismatch'})
            continue

        if room.current_occupancy >= room.capacity:
            results.append({'user_id': uid, 'name': user.full_name, 'success': False, 'error': 'Room became full'})
            continue

        RoomAllocation.objects.create(
            student=user,
            room=room,
            allocated_by=request.user,
            move_in_date=move_in_date,
            status='ACTIVE',
            remarks=remarks
        )
        room.current_occupancy += 1
        room.save()
        allocated_count += 1
        results.append({'user_id': uid, 'name': user.full_name, 'success': True})

    return JsonResponse({
        'success': allocated_count > 0,
        'allocated_count': allocated_count,
        'total_requested': len(user_ids),
        'results': results,
        'message': f'{allocated_count} of {len(user_ids)} user(s) allocated to Room {room.room_number}.'
    })


@login_required
@require_http_methods(["POST"])
def check_allocation_conflict_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    user_id = request.POST.get('user_id')
    room_id = request.POST.get('room_id')

    if not user_id or not room_id:
        return JsonResponse({'success': False, 'error': 'user_id and room_id are required'})

    user = get_object_or_404(User, id=user_id)
    room = get_object_or_404(Room, id=room_id)

    already_allocated = RoomAllocation.objects.filter(student=user, status='ACTIVE').exists()
    room_full = room.current_occupancy >= room.capacity

    user_gender = (getattr(user, 'gender', '') or '').strip().upper()
    hostel_gender = room.hostel.gender_restriction
    gender_mismatch = bool(hostel_gender != 'ANY' and user_gender and user_gender != hostel_gender)

    return JsonResponse({
        'success': True,
        'already_allocated': already_allocated,
        'room_full': room_full,
        'gender_mismatch': gender_mismatch,
        'hostel_gender_display': room.hostel.get_gender_restriction_display(),
        'user_gender': user_gender.title() if user_gender else 'Not set',
        'has_conflict': already_allocated or room_full or gender_mismatch,
        'blocking': already_allocated or room_full,
    })


@login_required
@require_http_methods(["POST"])
def check_in_json(request, uuid, allocation_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    allocation = get_object_or_404(RoomAllocation, id=allocation_id)
    
    if allocation.status != 'PENDING':
        return JsonResponse({'success': False, 'error': 'Allocation is not pending'})
    
    allocation.status = 'ACTIVE'
    allocation.move_in_date = timezone.now().date()
    allocation.save()
    
    HostelAuditLog.objects.create(
        user=request.user,
        action='UPDATE',
        module='ROOM_ALLOCATION',
        object_type='RoomAllocation',
        object_id=allocation.id,
        changes={'status': 'ACTIVE', 'action': 'CHECK_IN'}
    )
    
    return JsonResponse({'success': True, 'message': 'User checked in successfully'})


@login_required
@require_http_methods(["POST"])
def check_out_json(request, uuid, allocation_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    allocation = get_object_or_404(RoomAllocation, id=allocation_id)
    
    try:
        data = json.loads(request.body)
        reason = data.get('reason', 'Completed stay')
    except:
        reason = 'Completed stay'
    
    if allocation.status != 'ACTIVE':
        return JsonResponse({'success': False, 'error': 'Allocation is not active'})
    
    allocation.status = 'COMPLETED'
    allocation.move_out_date = timezone.now().date()
    allocation.remarks = (allocation.remarks or '') + f'\nCheck-out reason: {reason}'
    allocation.save()
    
    room = allocation.room
    room.current_occupancy = max(0, room.current_occupancy - 1)
    room.save()
    
    HostelAuditLog.objects.create(
        user=request.user,
        action='UPDATE',
        module='ROOM_ALLOCATION',
        object_type='RoomAllocation',
        object_id=allocation.id,
        changes={'status': 'COMPLETED', 'action': 'CHECK_OUT', 'reason': reason}
    )
    
    return JsonResponse({'success': True, 'message': 'User checked out successfully'})


@login_required
@require_http_methods(["POST"])
def bulk_check_in_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        data = json.loads(request.body)
        user_ids = data.get('user_ids', [])
    except:
        return JsonResponse({'success': False, 'error': 'Invalid data'})
    
    checked_in = 0
    errors = []
    
    for user_id in user_ids:
        allocation = RoomAllocation.objects.filter(
            student_id=user_id,
            status='PENDING'
        ).first()
        
        if allocation:
            allocation.status = 'ACTIVE'
            allocation.move_in_date = timezone.now().date()
            allocation.save()
            checked_in += 1
        else:
            errors.append(f'User ID {user_id} has no pending allocation')
    
    return JsonResponse({
        'success': True,
        'checked_in': checked_in,
        'errors': errors if errors else None,
        'message': f'{checked_in} user(s) checked in successfully'
    })


@login_required
def allocation_details_json(request, uuid, allocation_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    allocation = get_object_or_404(
        RoomAllocation.objects.select_related('student', 'room', 'room__hostel', 'allocated_by'),
        id=allocation_id
    )
    
    data = {
        'success': True,
        'allocation': {
            'id': allocation.id,
            'user_name': allocation.student.full_name,
            'user_id': allocation.student.id,
            'room_number': allocation.room.room_number,
            'room_id': allocation.room.id,
            'hostel_name': allocation.room.hostel.name,
            'move_in_date': allocation.move_in_date.strftime('%Y-%m-%d') if allocation.move_in_date else None,
            'move_out_date': allocation.move_out_date.strftime('%Y-%m-%d') if allocation.move_out_date else None,
            'status': allocation.status.lower(),
            'status_display': allocation.get_status_display(),
            'allocated_by': allocation.allocated_by.full_name if allocation.allocated_by else 'System',
            'remarks': allocation.remarks or '',
            'allocated_date': allocation.allocated_date.strftime('%d %b %Y, %I:%M %p')
        }
    }
    
    return JsonResponse(data)


@login_required
def get_allocations_by_room_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    room_id = request.GET.get('room_id')
    if not room_id:
        return JsonResponse([], safe=False)
    
    allocations = RoomAllocation.objects.filter(
        room_id=room_id
    ).select_related('student').order_by('-allocated_date')
    
    data = []
    for alloc in allocations:
        data.append({
            'id': alloc.id,
            'user_name': alloc.student.full_name,
            'user_id': alloc.student.id,
            'move_in_date': alloc.move_in_date.strftime('%d %b %Y') if alloc.move_in_date else None,
            'move_out_date': alloc.move_out_date.strftime('%d %b %Y') if alloc.move_out_date else None,
            'status': alloc.status,
            'status_display': alloc.get_status_display()
        })
    
    return JsonResponse(data, safe=False)


@login_required
def allocated_users_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    user_type = request.GET.get('user_type', 'all')
    search = request.GET.get('search', '').strip()

    allocations = RoomAllocation.objects.filter(status='ACTIVE').select_related('student', 'room', 'room__hostel')

    if user_type == 'student':
        allocations = allocations.filter(student__is_student=True)
    elif user_type == 'faculty':
        allocations = allocations.filter(student__is_faculty=True)
    elif user_type == 'staff':
        allocations = allocations.filter(student__is_staff=True)

    if search:
        allocations = allocations.filter(
            Q(student__first_name__icontains=search) |
            Q(student__last_name__icontains=search) |
            Q(student__username__icontains=search) |
            Q(room__room_number__icontains=search)
        )

    data = []
    for a in allocations[:200]:
        role = 'student'
        if a.student.is_faculty:
            role = 'faculty'
        elif a.student.is_staff:
            role = 'staff'
        
        data.append({
            'user_id': a.student.id,
            'full_name': a.student.full_name,
            'username': a.student.username,
            'role': role,
            'current_room_id': a.room.id,
            'current_room_number': a.room.room_number,
            'current_hostel_name': a.room.hostel.name,
            'move_in_date': a.move_in_date.strftime('%d %b %Y') if a.move_in_date else '',
        })
    
    return JsonResponse(data, safe=False)


@login_required
def allocated_students_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    search = request.GET.get('search', '').strip()

    allocations = RoomAllocation.objects.filter(status='ACTIVE').select_related('student', 'room', 'room__hostel')

    if search:
        allocations = allocations.filter(
            Q(student__first_name__icontains=search) |
            Q(student__last_name__icontains=search) |
            Q(student__username__icontains=search) |
            Q(room__room_number__icontains=search)
        )

    data = [
        {
            'student_id': a.student.id,
            'full_name': a.student.full_name,
            'username': a.student.username,
            'current_room_id': a.room.id,
            'current_room_number': a.room.room_number,
            'current_hostel_name': a.room.hostel.name,
            'move_in_date': a.move_in_date.strftime('%d %b %Y') if a.move_in_date else '',
        }
        for a in allocations[:200]
    ]
    return JsonResponse(data, safe=False)


@login_required
@require_http_methods(["POST"])
def transfer_user_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})

    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})

    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    user_id = data.get('user_id')
    new_room_id = data.get('new_room_id')
    transfer_date = data.get('transfer_date')
    remarks = data.get('remarks', '')
    force = data.get('force') == 'true' if data.get('force') else False

    if not user_id or not new_room_id or not transfer_date:
        return JsonResponse({'success': False, 'error': 'user_id, new_room_id and transfer_date are required'})

    user = get_object_or_404(User, id=user_id)
    new_room = get_object_or_404(Room, id=new_room_id)

    current_allocation = RoomAllocation.objects.filter(student=user, status='ACTIVE').select_related('room').first()
    if not current_allocation:
        return JsonResponse({'success': False, 'error': 'This user has no active allocation to transfer from.'})

    if current_allocation.room_id == new_room.id:
        return JsonResponse({'success': False, 'error': 'User is already in this room.'})

    if new_room.current_occupancy >= new_room.capacity:
        return JsonResponse({'success': False, 'conflict': 'room_full', 'error': f'Room {new_room.room_number} is full.'})

    user_gender = (getattr(user, 'gender', '') or '').strip().upper()
    hostel_gender = new_room.hostel.gender_restriction
    if not force and hostel_gender != 'ANY' and user_gender and user_gender != hostel_gender:
        return JsonResponse({
            'success': False,
            'conflict': 'gender_mismatch',
            'error': f'{new_room.hostel.name} is {new_room.hostel.get_gender_restriction_display()}, but this user is registered as {user_gender.title()}.'
        })

    old_room = current_allocation.room

    current_allocation.status = 'COMPLETED'
    current_allocation.move_out_date = transfer_date
    current_allocation.remarks = (current_allocation.remarks or '') + f'\n[Transferred to {new_room.hostel.name} - Room {new_room.room_number} on {transfer_date}]'
    current_allocation.save()

    old_room.current_occupancy = max(0, old_room.current_occupancy - 1)
    old_room.save()

    RoomAllocation.objects.create(
        student=user,
        room=new_room,
        allocated_by=request.user,
        move_in_date=transfer_date,
        status='ACTIVE',
        remarks=remarks or f'Transferred from {old_room.hostel.name} - Room {old_room.room_number}'
    )
    new_room.current_occupancy += 1
    new_room.save()

    HostelAuditLog.objects.create(
        user=request.user,
        action='MOVE',
        module='ROOM_ALLOCATION',
        object_type='RoomAllocation',
        object_id=current_allocation.id,
        changes={
            'user': user.full_name,
            'from_room': old_room.room_number,
            'from_hostel': old_room.hostel.name,
            'to_room': new_room.room_number,
            'to_hostel': new_room.hostel.name,
            'transfer_date': transfer_date
        }
    )

    return JsonResponse({
        'success': True,
        'message': f'{user.full_name} transferred from Room {old_room.room_number} to Room {new_room.room_number}.'
    })


@login_required
@require_http_methods(["POST"])
def transfer_student_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})

    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})

    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    student_id = data.get('student_id')
    new_room_id = data.get('new_room_id')
    transfer_date = data.get('transfer_date')
    remarks = data.get('remarks', '')
    force = data.get('force') == 'true' if data.get('force') else False

    if not student_id or not new_room_id or not transfer_date:
        return JsonResponse({'success': False, 'error': 'student_id, new_room_id and transfer_date are required'})

    student = get_object_or_404(User, id=student_id, is_student=True)
    new_room = get_object_or_404(Room, id=new_room_id)

    current_allocation = RoomAllocation.objects.filter(student=student, status='ACTIVE').select_related('room').first()
    if not current_allocation:
        return JsonResponse({'success': False, 'error': 'This student has no active allocation to transfer from.'})

    if current_allocation.room_id == new_room.id:
        return JsonResponse({'success': False, 'error': 'Student is already in this room.'})

    if new_room.current_occupancy >= new_room.capacity:
        return JsonResponse({'success': False, 'conflict': 'room_full', 'error': f'Room {new_room.room_number} is full.'})

    student_gender = (getattr(student, 'gender', '') or '').strip().upper()
    hostel_gender = new_room.hostel.gender_restriction
    if not force and hostel_gender != 'ANY' and student_gender and student_gender != hostel_gender:
        return JsonResponse({
            'success': False,
            'conflict': 'gender_mismatch',
            'error': f'{new_room.hostel.name} is {new_room.hostel.get_gender_restriction_display()}, but this student is registered as {student_gender.title()}.'
        })

    old_room = current_allocation.room

    current_allocation.status = 'COMPLETED'
    current_allocation.move_out_date = transfer_date
    current_allocation.remarks = (current_allocation.remarks or '') + f'\n[Transferred to {new_room.hostel.name} - Room {new_room.room_number} on {transfer_date}]'
    current_allocation.save()

    old_room.current_occupancy = max(0, old_room.current_occupancy - 1)
    old_room.save()

    RoomAllocation.objects.create(
        student=student,
        room=new_room,
        allocated_by=request.user,
        move_in_date=transfer_date,
        status='ACTIVE',
        remarks=remarks or f'Transferred from {old_room.hostel.name} - Room {old_room.room_number}'
    )
    new_room.current_occupancy += 1
    new_room.save()

    HostelAuditLog.objects.create(
        user=request.user,
        action='MOVE',
        module='ROOM_ALLOCATION',
        object_type='RoomAllocation',
        object_id=current_allocation.id,
        changes={
            'student': student.full_name,
            'from_room': old_room.room_number,
            'from_hostel': old_room.hostel.name,
            'to_room': new_room.room_number,
            'to_hostel': new_room.hostel.name,
            'transfer_date': transfer_date
        }
    )

    return JsonResponse({
        'success': True,
        'message': f'{student.full_name} transferred from Room {old_room.room_number} to Room {new_room.room_number}.'
    })


@login_required
@require_http_methods(["POST"])
def update_allocation_json(request, uuid, allocation_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    allocation = get_object_or_404(RoomAllocation, id=allocation_id)
    
    status = request.POST.get('status')
    move_in_date = request.POST.get('move_in_date')
    move_out_date = request.POST.get('move_out_date')
    remarks = request.POST.get('remarks', '')
    
    if not status:
        return JsonResponse({'success': False, 'error': 'Status is required'})
    
    try:
        allocation.status = status
        
        if move_in_date:
            allocation.move_in_date = move_in_date
        
        if move_out_date:
            allocation.move_out_date = move_out_date
        
        allocation.remarks = remarks
        allocation.save()
        
        room = allocation.room
        active_allocations = RoomAllocation.objects.filter(room=room, status='ACTIVE').count()
        room.current_occupancy = active_allocations
        room.save()
        
        HostelAuditLog.objects.create(
            user=request.user,
            action='UPDATE',
            module='ROOM_ALLOCATION',
            object_type='RoomAllocation',
            object_id=allocation.id,
            changes={
                'status': status,
                'move_in_date': move_in_date,
                'move_out_date': move_out_date
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Allocation updated successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def delete_allocation_json(request, uuid, allocation_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    allocation = get_object_or_404(RoomAllocation, id=allocation_id)
    
    try:
        if allocation.status == 'ACTIVE':
            room = allocation.room
            room.current_occupancy = max(0, room.current_occupancy - 1)
            room.save()
        
        HostelAuditLog.objects.create(
            user=request.user,
            action='DELETE',
            module='ROOM_ALLOCATION',
            object_type='RoomAllocation',
            object_id=allocation.id,
            changes={
                'user': allocation.student.full_name,
                'room': allocation.room.room_number,
                'hostel': allocation.room.hostel.name,
                'status': allocation.status
            }
        )
        
        allocation.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Allocation deleted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# Housing Applications and Maintenance
from Students.models import MaintenanceRequest, RoomInspection


@login_required
def admin_housing_dashboard(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        messages.error(request, "Permission denied.")
        return redirect("login")
    
    # total_applications = HousingApplication.objects.count()
    # pending_applications = HousingApplication.objects.filter(status='PENDING').count()
    # under_review_applications = HousingApplication.objects.filter(status='UNDER_REVIEW').count()
    # approved_applications = HousingApplication.objects.filter(status='APPROVED').count()
    # allocated_applications = HousingApplication.objects.filter(status='ALLOCATED').count()
    # rejected_applications = HousingApplication.objects.filter(status='REJECTED').count()
    
    total_maintenance = MaintenanceRequest.objects.count()
    pending_maintenance = MaintenanceRequest.objects.filter(status='PENDING').count()
    in_progress_maintenance = MaintenanceRequest.objects.filter(status='IN_PROGRESS').count()
    completed_maintenance = MaintenanceRequest.objects.filter(status='COMPLETED').count()
    emergency_maintenance = MaintenanceRequest.objects.filter(priority='EMERGENCY', status__in=['PENDING', 'IN_PROGRESS']).count()
    
    total_inspections = RoomInspection.objects.count()
    pending_inspections = RoomInspection.objects.filter(status='PENDING').count()
    
    # recent_applications = HousingApplication.objects.select_related('student', 'preferred_hostel').order_by('-application_date')[:10]
    recent_maintenance = MaintenanceRequest.objects.select_related('student', 'room', 'room__hostel').order_by('-created_at')[:10]
    
    context = {
        'user': request.user,
        # 'total_applications': total_applications,
        # 'pending_applications': pending_applications,
        # 'under_review_applications': under_review_applications,
        # 'approved_applications': approved_applications,
        # 'allocated_applications': allocated_applications,
        # 'rejected_applications': rejected_applications,
        'total_maintenance': total_maintenance,
        'pending_maintenance': pending_maintenance,
        'in_progress_maintenance': in_progress_maintenance,
        'completed_maintenance': completed_maintenance,
        'emergency_maintenance': emergency_maintenance,
        'total_inspections': total_inspections,
        'pending_inspections': pending_inspections,
        # 'recent_applications': recent_applications,
        'recent_maintenance': recent_maintenance,
        'active_sb': 'housing_dashboard'
    }
    return render(request, 'Blaze_Hostel/housing_dashboard.html', context)


# @login_required
# def admin_housing_applications(request, uuid):
#     if str(request.user.uuid) != str(uuid):
#         return redirect("login")
    
#     if not (request.user.is_admin or request.user.is_hostel_admin):
#         messages.error(request, "Permission denied.")
#         return redirect("login")
    
#     status_filter = request.GET.get('status', 'all')
#     search = request.GET.get('search', '').strip()
    
#     applications = HousingApplication.objects.select_related('student', 'preferred_hostel', 'reviewed_by').all()
    
#     if status_filter != 'all':
#         applications = applications.filter(status=status_filter.upper())
    
#     if search:
#         applications = applications.filter(
#             Q(student__full_name__icontains=search) |
#             Q(student__username__icontains=search) |
#             Q(student__email__icontains=search)
#         )
    
#     paginator = Paginator(applications, 20)
#     page = request.GET.get('page')
#     applications_page = paginator.get_page(page)
    
#     hostels = Hostel.objects.filter(status='ACTIVE')
    
#     context = {
#         'user': request.user,
#         'applications': applications_page,
#         'hostels': hostels,
#         'status_filter': status_filter,
#         'search': search,
#         'active_sb': 'housing_applications'
#     }
#     return render(request, 'Blaze_Hostel/housing_applications.html', context)


# @login_required
# @require_http_methods(["POST"])
# def admin_update_application(request, uuid, application_id):
#     if str(request.user.uuid) != str(uuid):
#         return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
#     if not (request.user.is_admin or request.user.is_hostel_admin):
#         return JsonResponse({'success': False, 'error': 'Permission denied'})
    
#     application = get_object_or_404(HousingApplication, id=application_id)
    
#     status = request.POST.get('status')
#     notes = request.POST.get('notes', '')
#     allocate_room = request.POST.get('allocate_room') == 'true'
#     room_id = request.POST.get('room_id')
    
#     if not status:
#         return JsonResponse({'success': False, 'error': 'Status is required'})
    
#     try:
#         application.status = status
#         application.reviewed_by = request.user
#         application.reviewed_date = timezone.now()
        
#         if notes:
#             application.admin_notes = (application.admin_notes or '') + f'\n[{timezone.now().date()}] {notes}'
        
#         application.save()
        
#         if status == 'ALLOCATED' and allocate_room and room_id:
#             try:
#                 room = Room.objects.get(id=room_id)
                
#                 if room.current_occupancy >= room.capacity:
#                     return JsonResponse({
#                         'success': False,
#                         'error': f'Room {room.room_number} is full (Capacity: {room.capacity})'
#                     })
                
#                 if RoomAllocation.objects.filter(student=application.student, status='ACTIVE').exists():
#                     return JsonResponse({
#                         'success': False,
#                         'error': 'Student already has an active allocation'
#                     })
                
#                 allocation = RoomAllocation.objects.create(
#                     student=application.student,
#                     room=room,
#                     allocated_by=request.user,
#                     move_in_date=timezone.now().date(),
#                     status='ACTIVE',
#                     remarks=f'Allocated from housing application #{application.id}'
#                 )
                
#                 room.current_occupancy += 1
#                 room.save()
                
#                 HostelAuditLog.objects.create(
#                     user=request.user,
#                     action='ALLOCATE',
#                     module='HOUSING',
#                     object_type='RoomAllocation',
#                     object_id=allocation.id,
#                     changes={
#                         'student': application.student.full_name,
#                         'room': room.room_number,
#                         'hostel': room.hostel.name,
#                         'application_id': application.id
#                     }
#                 )
                
#             except Room.DoesNotExist:
#                 return JsonResponse({'success': False, 'error': 'Room not found'})
        
#         HostelAuditLog.objects.create(
#             user=request.user,
#             action='UPDATE',
#             module='HOUSING',
#             object_type='HousingApplication',
#             object_id=application.id,
#             changes={'status': status, 'notes': notes}
#         )
        
#         return JsonResponse({
#             'success': True,
#             'message': f'Application updated to {application.get_status_display()}'
#         })
        
#     except Exception as e:
#         return JsonResponse({'success': False, 'error': str(e)})


# @login_required
# def admin_application_detail(request, uuid, application_id):
#     if str(request.user.uuid) != str(uuid):
#         return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
#     if not (request.user.is_admin or request.user.is_hostel_admin):
#         return JsonResponse({'success': False, 'error': 'Permission denied'})
    
#     application = get_object_or_404(
#         HousingApplication.objects.select_related('student', 'preferred_hostel', 'reviewed_by'),
#         id=application_id
#     )
    
#     data = {
#         'success': True,
#         'application': {
#             'id': application.id,
#             'student_name': application.student.full_name,
#             'student_email': application.student.email,
#             'student_username': application.student.username,
#             'preferred_hostel': application.preferred_hostel.name if application.preferred_hostel else 'No preference',
#             'preferred_room_type': application.get_preferred_room_type_display(),
#             'preferred_floor': application.preferred_floor or 'No preference',
#             'gender': application.get_gender_display(),
#             'year_of_study': application.get_year_of_study_display(),
#             'special_needs': application.special_needs or 'None',
#             'dietary_preferences': application.dietary_preferences or 'None',
#             'medical_conditions': application.medical_conditions or 'None',
#             'roommate_preference': application.roommate_preference or 'None',
#             'roommate_gender_preference': application.roommate_gender_preference or 'No preference',
#             'roommate_study_habits': application.roommate_study_habits or 'None',
#             'hobbies_interests': application.hobbies_interests or 'None',
#             'sleep_schedule': application.sleep_schedule or 'None',
#             'smoking_preference': 'Non-smoker' if application.smoking_preference else 'Smoker',
#             'pet_preference': 'No pets' if application.pet_preference else 'Has pets',
#             'status': application.status,
#             'status_display': application.get_status_display(),
#             'application_date': application.application_date.strftime('%d %b %Y, %I:%M %p'),
#             'admin_notes': application.admin_notes or '',
#             'reviewed_by': application.reviewed_by.full_name if application.reviewed_by else 'Not reviewed',
#             'reviewed_date': application.reviewed_date.strftime('%d %b %Y') if application.reviewed_date else 'Not reviewed'
#         }
#     }
    
#     return JsonResponse(data)

from Students.models import MaintenanceRequest  

@login_required
def admin_maintenance_requests(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        messages.error(request, "Permission denied.")
        return redirect("login")
    
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    search = request.GET.get('search', '').strip()
    
    from Students.models import MaintenanceRequest
    
    requests = MaintenanceRequest.objects.select_related('student', 'room', 'room__hostel', 'assigned_to').all()
    
    if status_filter != 'all':
        requests = requests.filter(status=status_filter.upper())
    
    if priority_filter != 'all':
        requests = requests.filter(priority=priority_filter.upper())
    
    if search:
        requests = requests.filter(
            Q(student__full_name__icontains=search) |
            Q(room__room_number__icontains=search) |
            Q(issue_type__icontains=search) |
            Q(description__icontains=search)
        )
    
    from django.core.paginator import Paginator
    paginator = Paginator(requests, 20)
    page = request.GET.get('page')
    requests_page = paginator.get_page(page)
    
    staff_users = User.objects.filter(is_staff=True)
    
    context = {
        'user': request.user,
        'requests': requests_page,
        'staff_users': staff_users,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search': search,
        'active_sb': 'maintenance_requests'
    }
    return render(request, 'Blaze_Hostel/maintenance_requests.html', context)


@login_required
@require_http_methods(["POST"])
def admin_update_maintenance(request, uuid, request_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    if not (request.user.is_admin or request.user.is_hostel_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    from Students.models import MaintenanceRequest
    
    req = get_object_or_404(MaintenanceRequest, id=request_id)
    
    status = request.POST.get('status')
    assigned_to_id = request.POST.get('assigned_to')
    resolution_notes = request.POST.get('resolution_notes', '')
    
    if not status:
        return JsonResponse({'success': False, 'error': 'Status is required'})
    
    try:
        req.status = status
        
        if assigned_to_id:
            req.assigned_to_id = assigned_to_id
        
        if resolution_notes:
            req.resolution_notes = (req.resolution_notes or '') + f'\n[{timezone.now().date()}] {resolution_notes}'
        
        if status == 'COMPLETED':
            req.completed_date = timezone.now()
        
        req.save()
        
        HostelAuditLog.objects.create(
            user=request.user,
            action='UPDATE',
            module='MAINTENANCE',
            object_type='MaintenanceRequest',
            object_id=req.id,
            changes={'status': status}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Maintenance request updated to {req.get_status_display()}'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

#<-----------------Blaze code End(29.08.26)---------------->




























