import re
import random

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Q, Value
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.db.models.functions import Concat
import traceback
from django.urls import reverse
from django.db.models import Count
from django.http import HttpResponseForbidden

from Students.models import StudentProfile
from Faculty.models import FacultyProfile
from Staff.models import StaffProfile
from Admin.models import User,Athletic
from Medical.models import PatientProfile, Appointment, PatientRegistration, Shift,ShiftAssignment,MedicalVisit, AthleteMedicalProfile, InjuryRecord,MedicalStaffProfile, RoomCheckupNote


#--------------------------- Add patients view start ----------------------------------------------# 

PHONE_REGEX = re.compile(r"^\+?[1-9]\d{8,14}$")

PROFILE_CONFIG = {
    "STUDENT": {
        "model": StudentProfile,
        "existing_patient_lookup": "patient_student_profile",
        "patient_field": "student",
        "search_fields": ["student_number", "university_email"],
        "email_field": "university_email",
    },
    "FACULTY": {
        "model": FacultyProfile,
        "existing_patient_lookup": "patient_faculty_profile",
        "patient_field": "faculty",
        "search_fields": ["employee_id", "email"],
        "email_field": "email",
    },
    "STAFF": {
        "model": StaffProfile,
        "existing_patient_lookup": "patient_staff_profile",
        "patient_field": "staff",
        "search_fields": ["employee_id", "work_email"],
        "email_field": "work_email",
    },
    "ADMIN": {
        "model": User,
        "existing_patient_lookup": "patient_admin_profile",
        "patient_field": "admin",
        "search_fields": [
            "university_id",
            "email",
            "username",
        ],
        "email_field": "email",
    },
}


@login_required
def add_patient(request):
    context = {
        "active_sb": "patients",
    }

    return render(request, "swetha/add_patient.html", context)


@login_required
def search_patient_members(request):
    """
    AJAX: search existing Students/Faculty/Staff who do not already
    have a PatientProfile, by name / university id / employee id.
    
    """
    
    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Invalid request method.",
        })

    patient_type = request.POST.get("patient_type", "").upper()
    keyword = request.POST.get("keyword", "").strip()

    config = PROFILE_CONFIG.get(patient_type)

    if not config:
        return JsonResponse({
            "success": False,
            "message": "Please select a valid patient type.",
        })

    if not keyword:
        return JsonResponse({
            "success": False,
            "message": "Enter a name, University ID, or employee ID to search.",
        })

    profile_model = config["model"]
    if patient_type == "ADMIN":
      queryset = (
            profile_model.objects
            .filter(is_admin=True)
            .annotate(
                search_name=Concat(
                    "first_name",
                    Value(" "),
                    "last_name",
                )
            )
        )
    else:
        queryset = (
         profile_model.objects
         .select_related("user")
         .annotate(
            full_name=Concat(
                "user__first_name",
                Value(" "),
                "user__last_name",
            )
         )
        )

    parts = keyword.split()

    query = Q()

    for part in parts:

        if patient_type == "ADMIN":
          part_query = (
            Q(first_name__icontains=part)
            | Q(last_name__icontains=part)
            | Q(search_name__icontains=part)
            | Q(username__icontains=part)
            | Q(university_id__icontains=part)
            )
        else:
           part_query = (
            Q(user__first_name__icontains=part)
            | Q(user__last_name__icontains=part)
            | Q(full_name__icontains=part)
            | Q(user__university_id__icontains=part)
         )

        for field in config["search_fields"]:
            part_query |= Q(**{f"{field}__icontains": part})

        query &= part_query

    exclude_filter = {f"{config['existing_patient_lookup']}__isnull": False}

    queryset = (queryset.filter(query).exclude(**exclude_filter)[:8])

    results = []

    for profile in queryset:

        if patient_type == "ADMIN":
            user = profile
            photo_url = (
                user.profile_photo.url
                if user.profile_photo
                else None
            )
            email = user.email or ""

        else:
            user = profile.user

            photo_url = (
                user.profile_photo.url
                if user.profile_photo
                else None
            )

            email = (
                getattr(
                    profile,
                    config["email_field"],
                    ""
                )
                or user.email
            )

        # =====================================================
        # FULL NAME
        # =====================================================

        full_name = (
            f"{user.first_name} {user.last_name}"
        ).strip()

        athlete = None

        if patient_type in ["STUDENT", "FACULTY", "STAFF"]:

            athlete = (
                Athletic.objects
                .filter(
                    student=user,
                    is_active=True
                )
                .select_related("team")
                .prefetch_related("individual_sports")
                .first()
            )

        # =====================================================
        # ATHLETE DATA
        # =====================================================

        athlete_data = None

        if athlete:

            individual_sports = list(
                athlete.individual_sports.values_list(
                    "sport_name",
                    flat=True
                )
            )

            athlete_data = {
                "athlete_id": athlete.athlete_id,

                "team": (
                    athlete.team.team_name
                    if athlete.team
                    else None
                ),

                "individual_sports": individual_sports,
            }

        # =====================================================
        # RESULT
        # =====================================================

        results.append({

            "profile_id": profile.id,

            "university_id": (
                user.university_id or ""
            ),

            "full_name": full_name,

            "gender": (
                user.get_gender_display()
                if user.gender
                else ""
            ),

            "date_of_birth": (
                user.date_of_birth.isoformat()
                if user.date_of_birth
                else ""
            ),

            "mobile": (
                user.mobile_number or ""
            ),

            "email": email or "",

            "photo": photo_url,

            # =================================================
            # ATHLETE
            # =================================================

            "is_athlete": athlete is not None,

            "athlete": athlete_data,
        })
        

    return JsonResponse({
        "success": True,
        "results": results,
    })

def generate_patient_number():
    year = timezone.now().year

    last_patient = (
        PatientProfile.objects
        .filter(patient_number__startswith=f"PAT{year}")
        .order_by("-patient_number")
        .first()
    )

    if last_patient:
        last_sequence = int(last_patient.patient_number[-4:])
        next_sequence = last_sequence + 1
    else:
        next_sequence = 1

    return f"PAT{year}{next_sequence:04d}"

def generate_athlete_medical_id():
    last_profile = (
        AthleteMedicalProfile.objects
        .order_by("-athlete_medical_id")
        .first()
    )

    if not last_profile:
        return "AMP00001"

    try:
        last_number = int(
            last_profile.athlete_medical_id.replace("AMP", "")
        )
        return f"AMP{last_number + 1:05d}"

    except (ValueError, AttributeError):
        return "AMP00001"


@login_required
@transaction.atomic
def save_patient(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Invalid request method.",
        })

    try:

        # =====================================================
        # BASIC DATA
        # =====================================================

        patient_type = request.POST.get(
            "patient_type", ""
        ).upper()

        selected_profile_id = request.POST.get(
            "selected_profile_id", ""
        ).strip()

        blood_group = request.POST.get(
            "blood_group", ""
        ).strip()

        allergies = request.POST.get(
            "allergies", ""
        ).strip()

        chronic_conditions = request.POST.get(
            "chronic_conditions", ""
        ).strip()

        remarks = request.POST.get(
            "remarks", ""
        ).strip()


        # =====================================================
        # VISITOR DATA
        # =====================================================

        visitor_name = request.POST.get(
            "visitor_name", ""
        ).strip()

        visitor_phone = request.POST.get(
            "visitor_mobile", ""
        ).strip()

        visitor_email = request.POST.get(
            "visitor_email", ""
        ).strip()

        visitor_gender = request.POST.get(
            "visitor_gender", ""
        ).strip()

        visitor_address = request.POST.get(
            "visitor_address", ""
        ).strip()


        # =====================================================
        # EMERGENCY CONTACT
        # =====================================================

        emergency_contact_name = request.POST.get(
            "emergency_contact_name", ""
        ).strip()

        emergency_contact_phone = request.POST.get(
            "emergency_contact_phone", ""
        ).strip()


        errors = {}

        config = PROFILE_CONFIG.get(patient_type)

        if patient_type != "VISITOR":

            if not config:
                errors["patient_type"] = [
                    "Please select a valid patient type."
                ]

            if not selected_profile_id:
                errors["selected_profile_id"] = [
                    "Please search and select a university member."
                ]

        else:

            if not visitor_name:
                errors["visitor_name"] = [
                    "Visitor name is required."
                ]

            if not visitor_phone:
                errors["visitor_phone"] = [
                    "Visitor phone is required."
                ]

            elif not PHONE_REGEX.match(visitor_phone):
                errors["visitor_phone"] = [
                    "Enter a valid (9-15 digit) mobile number."
                ]


        # =====================================================
        # EMERGENCY VALIDATION
        # =====================================================

        if not emergency_contact_name:
            errors["emergency_contact_name"] = [
                "Emergency contact name is required."
            ]

        if not emergency_contact_phone:
            errors["emergency_contact_phone"] = [
                "Emergency contact number is required."
            ]

        elif not PHONE_REGEX.match(emergency_contact_phone):
            errors["emergency_contact_phone"] = [
                "Enter a valid (9-15 digit) contact number."
            ]


        if errors:

            return JsonResponse({
                "success": False,
                "message": "Please correct the highlighted fields.",
                "errors": errors,
            })

        if patient_type == "VISITOR":

            patient = PatientProfile.objects.create(

                patient_number=generate_patient_number(),

                patient_type="VISITOR",

                visitor_name=visitor_name,
                visitor_phone=visitor_phone,
                visitor_email=visitor_email,
                visitor_gender=visitor_gender,
                visitor_address=visitor_address,

                blood_group=blood_group,
                allergies=allergies,
                chronic_conditions=chronic_conditions,
                remarks=remarks,

                emergency_contact_name=emergency_contact_name,
                emergency_contact_phone=emergency_contact_phone,
            )

            return JsonResponse({

                "success": True,

                "message": "Visitor registered successfully.",

                "patient_id": patient.id,

                "patient_number": patient.patient_number,

                "redirect_url": reverse(
                    "Medical:patients"
                ),
            })


        # =====================================================
        # GET PROFILE
        # =====================================================

        profile_model = config["model"]

        try:

            if patient_type == "ADMIN":

                profile = profile_model.objects.get(
                    pk=selected_profile_id,
                    is_admin=True
                )

            else:

                profile = profile_model.objects.get(
                    pk=selected_profile_id
                )

        except profile_model.DoesNotExist:

            return JsonResponse({

                "success": False,

                "message": (
                    "The selected person could not be found. "
                    "Please search again."
                ),

                "errors": {
                    "selected_profile_id": [
                        "Selected person not found."
                    ]
                },
            })


        # =====================================================
        # ALREADY PATIENT CHECK
        # =====================================================

        if getattr(
            profile,
            config["existing_patient_lookup"],
            None
        ):

            return JsonResponse({

                "success": False,

                "message": (
                    "This person has already been "
                    "registered as a patient."
                ),

                "errors": {
                    "selected_profile_id": [
                        "Already registered as a patient."
                    ]
                },
            })


        # =====================================================
        # ATHLETE CHECK
        #
        # Works for:
        # STUDENT
        # FACULTY
        # STAFF
        #
        # because Athletic.student contains User
        # =====================================================

        athlete = None

        if patient_type in ["STUDENT", "FACULTY", "STAFF"]:

            athlete = (
                Athletic.objects
                .filter(
                    student=profile.user,
                    is_active=True
                )
                .first()
            )


        # =====================================================
        # ATHLETE MEDICAL PROFILE ALREADY LINKED CHECK
        # =====================================================

        if athlete:

            existing_athlete_medical = (
                AthleteMedicalProfile.objects
                .filter(athlete=athlete)
                .first()
            )

            if (
                existing_athlete_medical
                and existing_athlete_medical.patient_profile
            ):

                return JsonResponse({

                    "success": False,

                    "message": (
                        "This athlete already has "
                        "a medical patient profile."
                    ),

                    "errors": {
                        "selected_profile_id": [
                            "Athlete already registered."
                        ]
                    },
                })


        # =====================================================
        # CREATE PATIENT PROFILE
        # =====================================================

        patient_number = generate_patient_number()

        create_kwargs = {

            "patient_number": patient_number,

            "patient_type": patient_type,

            "blood_group": blood_group,

            "allergies": allergies,

            "chronic_conditions": chronic_conditions,

            "remarks": remarks,

            "emergency_contact_name":
                emergency_contact_name,

            "emergency_contact_phone":
                emergency_contact_phone,

            config["patient_field"]: profile,
        }

        patient = PatientProfile.objects.create(
            **create_kwargs
        )


        # =====================================================
        # CREATE / LINK ATHLETE MEDICAL PROFILE
        #
        # Student / Faculty / Staff athlete
        # =====================================================

        if athlete:

            athlete_medical_profile, created = (
                AthleteMedicalProfile.objects.get_or_create(

                    athlete=athlete,

                    defaults={
                        "athlete_medical_id":
                            generate_athlete_medical_id()
                    }
                )
            )

            # Link PatientProfile
            athlete_medical_profile.patient_profile = patient

            athlete_medical_profile.save(
                update_fields=["patient_profile"]
            )


        # =====================================================
        # SUCCESS
        # =====================================================

        return JsonResponse({

            "success": True,

            "message": (
                "Athlete patient registered successfully."
                if athlete
                else "Patient added successfully."
            ),

            "patient_id": patient.id,

            "patient_number":
                patient.patient_number,

            "is_athlete":
                athlete is not None,

            "athlete_medical_id": (
                athlete_medical_profile.athlete_medical_id
                if athlete
                else None
            ),

            "redirect_url":
                reverse("Medical:patients"),
        })


    # =========================================================
    # INTEGRITY ERROR
    # =========================================================

    except IntegrityError:

        return JsonResponse({

            "success": False,

            "message": (
                "This person has already been "
                "registered as a patient."
            ),
        })


    # =========================================================
    # UNKNOWN ERROR
    # =========================================================

    except Exception as e:

        traceback.print_exc()

        return JsonResponse({

            "success": False,

            "message": str(e),
        })


#--------------- Jack Views Start -----------------#

@login_required
def edit_patient(request, uuid):
    patient = get_object_or_404(PatientProfile, uuid=uuid)
    
    context = {
        "active_sb": "patients",
        "patient": patient,
        "linked_profile_id": "",
        "linked_full_name": "",
        "linked_university_id": "",
        "linked_gender": "",
        "linked_dob": "",
        "linked_mobile": "",
        "linked_email": "",
        "linked_photo": None,
    }

    if patient.patient_type != "VISITOR":
        linked_profile = None
        
        if patient.patient_type == "STUDENT" and patient.student:
            linked_profile = patient.student
        elif patient.patient_type == "FACULTY" and patient.faculty:
            linked_profile = patient.faculty
        elif patient.patient_type == "STAFF" and patient.staff:
            linked_profile = patient.staff
        elif patient.patient_type == "ADMIN" and patient.admin:
            linked_profile = patient.admin

        if linked_profile:
            user = linked_profile.user if hasattr(linked_profile, 'user') else linked_profile
            context["linked_profile_id"] = linked_profile.id
            context["linked_full_name"] = f"{user.first_name} {user.last_name}".strip()
            context["linked_university_id"] = getattr(user, 'university_id', '') or ''
            context["linked_gender"] = user.get_gender_display() if hasattr(user, 'get_gender_display') and user.gender else ''
            context["linked_dob"] = user.date_of_birth.isoformat() if user.date_of_birth else ''
            context["linked_mobile"] = getattr(user, 'mobile_number', '') or ''
            context["linked_email"] = getattr(user, 'email', '') or ''
            if hasattr(user, 'profile_photo') and user.profile_photo:
                context["linked_photo"] = user.profile_photo.url

    return render(request, "Jack/edit_patient.html", context)


@login_required
@transaction.atomic
def update_patient(request, uuid):
    print("POST DATA:", dict(request.POST))
    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Invalid request method.",
        })

    try:
        patient = get_object_or_404(PatientProfile, uuid=uuid)

        patient_type = request.POST.get("patient_type", "").upper()
        blood_group = request.POST.get("blood_group", "").strip() or None
        allergies = request.POST.get("allergies", "").strip() or None
        chronic_conditions = request.POST.get("chronic_conditions", "").strip() or None
        remarks = request.POST.get("remarks", "").strip() or None

        visitor_name = request.POST.get("visitor_name", "").strip()
        visitor_phone = request.POST.get("visitor_mobile", "").strip()
        visitor_email = request.POST.get("visitor_email", "").strip()
        visitor_gender = request.POST.get("visitor_gender", "").strip()
        visitor_address = request.POST.get("visitor_address", "").strip()

        emergency_contact_name = request.POST.get("emergency_contact_name", "").strip()
        emergency_contact_phone = request.POST.get("emergency_contact_phone", "").strip()

        errors = {}

        if patient_type == "VISITOR":
            if not visitor_name:
                errors["visitor_name"] = ["Visitor name is required."]
            if not visitor_phone:
                errors["visitor_phone"] = ["Visitor phone is required."]
            elif not PHONE_REGEX.match(visitor_phone):
                errors["visitor_phone"] = ["Enter a valid (9-15 digit) mobile number."]
            if visitor_email and not validate_email(visitor_email):
                errors["visitor_email"] = ["Enter a valid email address."]

        if not emergency_contact_name:
            errors["emergency_contact_name"] = ["Emergency contact name is required."]

        if not emergency_contact_phone:
            errors["emergency_contact_phone"] = ["Emergency contact number is required."]
        elif not PHONE_REGEX.match(emergency_contact_phone):
            errors["emergency_contact_phone"] = ["Enter a valid (9-15 digit) contact number."]

        if errors:
            return JsonResponse({
                "success": False,
                "message": "Please correct the highlighted fields.",
                "errors": errors,
            })

        if patient_type == "VISITOR":
            patient.visitor_name = visitor_name
            patient.visitor_phone = visitor_phone
            patient.visitor_email = visitor_email
            patient.visitor_gender = visitor_gender
            patient.visitor_address = visitor_address

        patient.blood_group = blood_group
        patient.allergies = allergies if allergies is not None else ""  
        patient.chronic_conditions = chronic_conditions if chronic_conditions is not None else ""
        patient.remarks = remarks if remarks is not None else ""
        
        
        patient.emergency_contact_name = emergency_contact_name
        patient.emergency_contact_phone = emergency_contact_phone

        patient.save()

        return JsonResponse({
            "success": True,
            "message": "Patient updated successfully.",
            "patient_id": patient.id,
            "patient_number": patient.patient_number,
            "redirect_url": reverse("Medical:patients"),
        })

    except PatientProfile.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Patient record not found.",
        })

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({
            "success": False,
            "message": str(e),
        })


def validate_email(email):
    """Helper function to validate email"""
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(pattern, email) is not None

#---------------- Jack Views End ------------------#

#--------------------------- Add patients view end--------------------------------------------#

# --------------------------- Appointment view start ----------------------------------------------# 

from django.views.decorators.http import require_POST
@login_required
def today_schedule(request):

    try:
        medical_staff = request.user.medical_staff_profile
    except Exception:
        return render(
            request,
            "swetha/Today_appointment.html",
            {
                "active_sb": "Today_schedule",
                "registrations": [],
                "total": 0,
                "waiting": 0,
                "in_progress": 0,
                "completed": 0,
                "cancelled": 0,
            }
        )

    today = timezone.localdate()

    base_qs = PatientRegistration.objects.filter(
        shift_assignment__medical_staff=medical_staff,
        registration_date=today,
    )
    admitted_qs = PatientRegistration.objects.filter(
        shift_assignment__medical_staff=medical_staff,
        admission_status__in=["REQUESTED", "ADMITTED"],
    )

    # registrations = (
    #     base_qs
    #     .select_related(
    #         "patient",
    #         "appointment",
    #         "schedule",
    #         "schedule__department",
    #         "shift_assignment",
    #         "shift_assignment__shift",
    #         "shift_assignment__shift__department",
    #         "medical_visit",
    #     )
    #     .exclude(status="CANCELLED")
    #     .order_by(
    #         "priority",
    #         "registration_time",
    #         "token_number",
    #     )
    # )

    registrations = (
        PatientRegistration.objects
        .filter(shift_assignment__medical_staff=medical_staff)
        .filter(
            Q(registration_date=today)
            | Q(admission_status__in=["REQUESTED", "ADMITTED"])
        )
        .select_related(
            "patient",
            "appointment",
            "schedule",
            "schedule__department",
            "shift_assignment",
            "shift_assignment__shift",
            "shift_assignment__shift__department",
            "medical_visit",
        )
        .exclude(status="CANCELLED")
        .order_by(
            "priority",
            "registration_time",
            "token_number",
        )
    )

    # context = {
    #     "active_sb": "Today_schedule",
    #     "registrations": registrations,

    #     "total": registrations.count(),

    #     "waiting": base_qs.filter(
    #         status="WAITING"
    #     ).count(),

    #     "in_progress": base_qs.filter(
    #         status="IN_PROGRESS"
    #     ).count(),

    #     "completed": base_qs.filter(
    #         status="COMPLETED"
    #     ).count(),

    #     "cancelled": base_qs.filter(
    #         status="CANCELLED"
    #     ).count(),
    # }

    context = {
        "active_sb": "Today_schedule",
        "registrations": registrations,

        "total": base_qs.exclude(
            status="CANCELLED"
        ).count(),

        "waiting": base_qs.filter(
            status="WAITING"
        ).count(),

        "in_progress": base_qs.filter(
            status="IN_PROGRESS"
        ).exclude(
            admission_status__in=["REQUESTED", "ADMITTED"]
        ).count(),

        "completed": base_qs.filter(
            status="COMPLETED"
        ).exclude(
            admission_status__in=["REQUESTED", "ADMITTED"]
        ).count(),

        "cancelled": base_qs.filter(
            status="CANCELLED"
        ).count(),

        "admitted": admitted_qs.count(),
    }

    return render(
        request,
        "swetha/Today_appointment.html",
        context,
    )

@login_required
@require_POST
def check_in_patient(request, registration_id):

    try:
        medical_staff = request.user.medical_staff_profile
    except Exception:
        return JsonResponse(
            {
                "success": False,
                "message": "Medical staff profile not found.",
            },
            status=403,
        )

    registration = get_object_or_404(
        PatientRegistration.objects.select_related(
            "patient",
            "appointment",
            "medical_visit",
            "shift_assignment",
            "shift_assignment__medical_staff",
            "shift_assignment__shift",
            "shift_assignment__shift__department",
        ),
        id=registration_id,
    )

    if (
        not registration.shift_assignment
        or registration.shift_assignment.medical_staff != medical_staff
    ):
        return JsonResponse(
            {
                "success": False,
                "message": "This patient is not assigned to you.",
            },
            status=403,
        )

    if registration.status != "WAITING":
        return JsonResponse(
            {
                "success": False,
                "message": "Patient is not waiting.",
            },
            status=400,
        )

    if registration.medical_visit:
        return JsonResponse(
            {
                "success": False,
                "message": "Medical visit already exists for this registration.",
            },
            status=400,
        )

    today = timezone.localdate()
    now = timezone.localtime()

    athlete_profile = (
        AthleteMedicalProfile.objects
        .select_related(
            "athlete",
            "primary_sport",
        )
        .filter(
            patient_profile=registration.patient
        )
        .first()
    )

    if not athlete_profile:

        athlete = None

        patient_student = getattr(
            registration.patient,
            "student",
            None
        )

        if patient_student:

            student_user_id = getattr(
                patient_student,
                "user_id",
                None
            )

            if student_user_id:

                athlete = (
                    Athletic.objects
                    .filter(
                        student_id=student_user_id
                    )
                    .first()
                )

        if athlete:

            try:

                athlete_profile, created = (
                    get_or_create_athlete_medical_profile(
                        athlete=athlete,
                        patient=registration.patient,
                    )
                )

            except ValueError:

                athlete_profile = None

    # DEPARTMENT
    department = None

    if (
        registration.shift_assignment
        and registration.shift_assignment.shift
    ):
        department = (
            registration
            .shift_assignment
            .shift
            .department
        )

    with transaction.atomic():

        # CREATE CURRENT VISIT
        visit = MedicalVisit.objects.create(
            visit_number=generate_visit_number(),
            patient=registration.patient,
            athlete_profile=athlete_profile,
            attending_staff=medical_staff,
            department=department,
            visit_type="CONSULTATION",
            visit_date=today,
            visit_time=now.time(),
            chief_complaint=(
                getattr(
                    registration,
                    "chief_complaint",
                    ""
                ) or ""
            ),
            visit_status="OPEN",
        )

        # REGISTRATION
        registration.status = "IN_PROGRESS"
        registration.medical_visit = visit

        registration.save(
            update_fields=[
                "status",
                "medical_visit",
                "updated_at",
            ]
        )

        # APPOINTMENT
        if registration.appointment:

            appointment = registration.appointment

            appointment.status = "IN_PROGRESS"
            appointment.checked_in_at = now

            appointment.save(
                update_fields=[
                    "status",
                    "checked_in_at",
                    "updated_at",
                ]
            )

    counts = get_today_registration_counts(
        medical_staff
    )

    return JsonResponse(
        {
            "success": True,
            "message": (
                "Athlete patient checked in successfully."
                if athlete_profile
                else "Patient checked in successfully."
            ),
            "status": "IN_PROGRESS",
            "registration_id": registration.id,
            "visit_id": visit.id,
            "visit_number": visit.visit_number,
            "is_athlete": bool(athlete_profile),
            "athlete_medical_id": (
                athlete_profile.athlete_medical_id
                if athlete_profile
                else None
            ),
            "counts": counts,
        }
    )

def get_or_create_athlete_medical_profile(
    patient,
    athlete
):
    medical_profile = (
        AthleteMedicalProfile.objects
        .filter(
            athlete=athlete
        )
        .first()
    )

    if medical_profile:

        if medical_profile.patient_profile_id != patient.id:

            medical_profile.patient_profile = patient

            medical_profile.save(
                update_fields=[
                    "patient_profile",
                    "updated_at",
                ]
            )

        return medical_profile, False

    last_profile = (
        AthleteMedicalProfile.objects
        .order_by("-id")
        .first()
    )

    if last_profile and last_profile.athlete_medical_id:

        try:
            last_number = int(
                last_profile
                .athlete_medical_id
                .replace("ATH-MED-", "")
            )

        except ValueError:
            last_number = 0

    else:
        last_number = 0

    next_number = last_number + 1

    athlete_medical_id = (
        f"ATH-MED-{next_number:04d}"
    )

    medical_profile = (
        AthleteMedicalProfile.objects.create(
            athlete=athlete,
            patient_profile=patient,
            athlete_medical_id=athlete_medical_id,
        )
    )

    return medical_profile, True

@login_required
@require_POST
def update_athlete_medical_care(request):

    try:

        try:
            data = json.loads(
                request.body.decode("utf-8")
            )
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse(
                {
                    "success": False,
                    "message": "Invalid JSON request.",
                },
                status=400,
            )

        patient_id = data.get("patient_id")
        athlete_id = data.get("athlete_id")

        if not patient_id:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Patient ID is required.",
                },
                status=400,
            )

        if not athlete_id:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Athlete ID is required.",
                },
                status=400,
            )
        patient = get_object_or_404(
            PatientProfile,
            id=patient_id,
        )

        try:
            athlete = (
                Athletic.objects
                .select_related("student")
                .get(
                    athlete_id=athlete_id,
                )
            )

        except Athletic.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Athlete record not found.",
                },
                status=404,
            )

        medical_profile = (
            AthleteMedicalProfile.objects
            .select_for_update()
            .select_related("athlete")
            .filter(
                athlete=athlete
            )
            .first()
        )

        if not medical_profile:
            last_profile = (
                AthleteMedicalProfile.objects
                .order_by("-id")
                .first()
            )

            last_number = 0

            if (
                last_profile
                and last_profile.athlete_medical_id
            ):
                try:
                    last_number = int(
                        last_profile
                        .athlete_medical_id
                        .replace(
                            "ATH-MED-",
                            ""
                        )
                    )

                except (
                    ValueError,
                    AttributeError,
                ):
                    last_number = 0

            athlete_medical_id = (
                f"ATH-MED-{last_number + 1:04d}"
            )
            medical_profile = (
                AthleteMedicalProfile.objects.create(
                    athlete=athlete,
                    patient_profile=patient,
                    athlete_medical_id=athlete_medical_id,
                )
            )

        else:
            existing_patient_id = (
                medical_profile.patient_profile_id
            )
            if (
                existing_patient_id
                and existing_patient_id != patient.id
            ):
                return JsonResponse(
                    {
                        "success": False,
                        "message": (
                            "This athlete is already linked "
                            "to another patient."
                        ),
                    },
                    status=409,
                )

            if not existing_patient_id:

                medical_profile.patient_profile = patient

                medical_profile.save(
                    update_fields=[
                        "patient_profile",
                        "updated_at",
                    ]
                )

        fitness_level = (
            data.get("fitness_level") or ""
        )

        if not isinstance(fitness_level, str):
            fitness_level = ""

        fitness_level = fitness_level.strip()

        valid_fitness_levels = {
            choice[0]
            for choice in AthleteMedicalProfile.FITNESS_LEVELS
        }

        fitness_display_to_code = {
            label.strip().upper(): code
            for code, label
            in AthleteMedicalProfile.FITNESS_LEVELS
        }

        if fitness_level:

            fitness_level_upper = (
                fitness_level.upper()
            )

            if fitness_level_upper in valid_fitness_levels:

                fitness_level = fitness_level_upper

            elif fitness_level_upper in fitness_display_to_code:

                fitness_level = (
                    fitness_display_to_code[
                        fitness_level_upper
                    ]
                )

            else:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Invalid fitness level.",
                        "received": fitness_level,
                        "allowed": list(
                            valid_fitness_levels
                        ),
                    },
                    status=400,
                )

        injury_risk = (
            data.get("injury_risk") or ""
        )

        if not isinstance(injury_risk, str):
            injury_risk = ""

        injury_risk = injury_risk.strip()

        valid_injury_risks = {
            choice[0]
            for choice in AthleteMedicalProfile.INJURY_RISK
        }

        injury_display_to_code = {
            label.strip().upper(): code
            for code, label
            in AthleteMedicalProfile.INJURY_RISK
        }

        if injury_risk:

            injury_risk_upper = (
                injury_risk.upper()
            )

            if injury_risk_upper in valid_injury_risks:

                injury_risk = injury_risk_upper

            elif injury_risk_upper in injury_display_to_code:

                injury_risk = (
                    injury_display_to_code[
                        injury_risk_upper
                    ]
                )

            else:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Invalid injury risk.",
                        "received": injury_risk,
                        "allowed": list(
                            valid_injury_risks
                        ),
                    },
                    status=400,
                )
        next_medical_checkup = (
            data.get("next_medical_checkup") or None
        )

        if next_medical_checkup:

            if not isinstance(
                next_medical_checkup,
                str,
            ):
                return JsonResponse(
                    {
                        "success": False,
                        "message": (
                            "Invalid next medical "
                            "checkup date."
                        ),
                    },
                    status=400,
                )

            next_medical_checkup = (
                next_medical_checkup.strip()
            )

            if next_medical_checkup:

                try:
                    next_medical_checkup = (
                        date.fromisoformat(
                            next_medical_checkup
                        )
                    )

                except (
                    ValueError,
                    TypeError,
                ):
                    return JsonResponse(
                        {
                            "success": False,
                            "message": (
                                "Invalid next medical "
                                "checkup date."
                            ),
                        },
                        status=400,
                    )

        medical_restrictions = (
            data.get(
                "medical_restrictions",
                "",
            )
        )

        if not isinstance(
            medical_restrictions,
            str,
        ):
            medical_restrictions = ""

        medical_restrictions = (
            medical_restrictions.strip()
        )

        emergency_action_plan = (
            data.get(
                "emergency_action_plan",
                "",
            )
        )

        if not isinstance(
            emergency_action_plan,
            str,
        ):
            emergency_action_plan = ""

        emergency_action_plan = (
            emergency_action_plan.strip()
        )

        medical_clearance_status = (
            data.get("medical_clearance_status") or ""
        )

        if not isinstance(
            medical_clearance_status,
            str,
        ):
            medical_clearance_status = ""

        medical_clearance_status = (
            medical_clearance_status.strip()
        )

        valid_clearance_statuses = {
            choice[0]
            for choice in AthleteMedicalProfile.MEDICAL_CLEARANCE_STATUS
        }

        if medical_clearance_status:

            if medical_clearance_status not in valid_clearance_statuses:

                return JsonResponse(
                    {
                        "success": False,
                        "message": "Invalid medical clearance status.",
                        "received": medical_clearance_status,
                        "allowed": list(
                            valid_clearance_statuses
                        ),
                    },
                    status=400,
                )

        update_fields = []

        if medical_clearance_status:
            medical_profile.medical_clearance_status = (
                medical_clearance_status
            )

            update_fields.append(
                "medical_clearance_status"
            )

        if fitness_level:
            medical_profile.fitness_level = (
                fitness_level
            )

            update_fields.append(
                "fitness_level"
            )

        if injury_risk:
            medical_profile.injury_risk = (
                injury_risk
            )

            update_fields.append(
                "injury_risk"
            )


        medical_profile.next_medical_checkup = (
            next_medical_checkup
        )

        update_fields.append(
            "next_medical_checkup"
        )

        medical_profile.current_medical_restrictions = (
            medical_restrictions
        )

        update_fields.append(
            "current_medical_restrictions"
        )

        medical_profile.emergency_action_plan = (
            emergency_action_plan
        )

        update_fields.append(
            "emergency_action_plan"
        )

        update_fields.append(
            "updated_at"
        )

        medical_profile.save(
            update_fields=list(
                dict.fromkeys(update_fields)
            )
        )


        medical_profile.refresh_from_db()

        print(
            "========== MEDICAL CARE SAVE =========="
        )
        print(
            "Patient ID:",
            patient.id,
        )
        print(
            "Athlete ID:",
            athlete.athlete_id,
        )
        print(
            "Medical Profile ID:",
            medical_profile.id,
        )
        print(
            "Athlete Medical ID:",
            medical_profile.athlete_medical_id,
        )
        print(
            "Fitness Level:",
            medical_profile.fitness_level,
        )
        print(
            "Injury Risk:",
            medical_profile.injury_risk,
        )
        print(
            "Next Checkup:",
            medical_profile.next_medical_checkup,
        )
        print(
            "Medical Restrictions:",
            medical_profile.current_medical_restrictions,
        )
        print(
            "Emergency Action Plan:",
            medical_profile.emergency_action_plan,
        )
        print(
            "========================================"
        )



        return JsonResponse(
            {
                "success": True,

                "message": (
                    "Medical care information "
                    "updated successfully."
                ),

                "athlete_id":
                    athlete.athlete_id,

                "athlete_medical_id":
                    medical_profile.athlete_medical_id,

                "medical_profile": {

                    "fitness_level":
                        medical_profile.fitness_level
                        or "",

                    "fitness_level_display":
                        (
                            medical_profile
                            .get_fitness_level_display()
                        ),

                    "injury_risk":
                        medical_profile.injury_risk
                        or "",

                    "injury_risk_display":
                        (
                            medical_profile
                            .get_injury_risk_display()
                        ),

                    "next_medical_checkup":
                        (
                            medical_profile
                            .next_medical_checkup.isoformat()
                            if medical_profile.next_medical_checkup
                            else ""
                        ),

                    "medical_restrictions":
                        (
                            medical_profile
                            .current_medical_restrictions
                            or ""
                        ),

                    "emergency_action_plan":
                        (
                            medical_profile
                            .emergency_action_plan
                            or ""
                        ),
                },
            }
        )

    except Exception as e:

        transaction.set_rollback(True)

        traceback.print_exc()

        return JsonResponse(
            {
                "success": False,
                "message": str(e),
            },
            status=500,
        )

@login_required
@require_POST
def update_registration_status(
    request,
    registration_id
):

    try:
        medical_staff = request.user.medical_staff_profile
    except Exception:
        return JsonResponse(
            {
                "success": False,
                "message": "Medical staff profile not found.",
            },
            status=403,
        )

    try:
        data = json.loads(
            request.body.decode("utf-8")
        )
    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid JSON.",
            },
            status=400,
        )

    registration = get_object_or_404(
        PatientRegistration.objects.select_related(
            "appointment",
            "medical_visit",
            "shift_assignment",
            "shift_assignment__medical_staff",
        ),
        id=registration_id,
    )

    if (
        not registration.shift_assignment
        or registration.shift_assignment.medical_staff != medical_staff
    ):
        return JsonResponse(
            {
                "success": False,
                "message": "This patient is not assigned to you.",
            },
            status=403,
        )

    new_status = data.get("status")

    if not new_status:
        return JsonResponse(
            {
                "success": False,
                "message": "Status is required.",
            },
            status=400,
        )

    allowed_statuses = {
        "WAITING",
        "IN_PROGRESS",
        "CANCELLED",
    }

    if new_status not in allowed_statuses:
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid registration status.",
            },
            status=400,
        )
    if new_status == "COMPLETED":
        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Use complete_patient_consultation "
                    "to complete the consultation."
                ),
            },
            status=400,
        )

    with transaction.atomic():

        registration.status = new_status

        registration.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        if registration.appointment:

            appointment = registration.appointment

            if new_status == "CANCELLED":
                appointment.status = "CANCELLED"

            elif new_status == "IN_PROGRESS":
                appointment.status = "IN_PROGRESS"

            elif new_status == "WAITING":
                appointment.status = "ARRIVED"

            appointment.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

    counts = get_today_registration_counts(
        medical_staff
    )

    return JsonResponse(
        {
            "success": True,
            "status": registration.status,
            "message": "Registration status updated successfully.",
            "counts": counts,
        }
    )

# def get_today_registration_counts(medical_staff):

#     today = timezone.localdate()

#     registrations = PatientRegistration.objects.filter(
#         shift_assignment__medical_staff=medical_staff,
#         registration_date=today,
#     )

#     return {
#         "total": registrations.exclude(
#             status="CANCELLED"
#         ).count(),

#         "waiting": registrations.filter(
#             status="WAITING"
#         ).count(),

#         "in_progress": registrations.filter(
#             status="IN_PROGRESS"
#         ).count(),

#         "completed": registrations.filter(
#             status="COMPLETED"
#         ).count(),

#         "cancelled": registrations.filter(
#             status="CANCELLED"
#         ).count(),
#     }


# def get_today_registration_counts(medical_staff):

#     today = timezone.localdate()

#     registrations = PatientRegistration.objects.filter(
#         shift_assignment__medical_staff=medical_staff,
#         registration_date=today,
#     )

#     return {
#         "total": registrations.exclude(
#             status="CANCELLED"
#         ).count(),

#         "waiting": registrations.filter(
#             status="WAITING"
#         ).count(),

#         "in_progress": registrations.filter(
#             status="IN_PROGRESS"
#         ).exclude(
#             admission_status__in=["REQUESTED", "ADMITTED"]
#         ).count(),

#         "completed": registrations.filter(
#             status="COMPLETED"
#         ).exclude(
#             admission_status__in=["REQUESTED", "ADMITTED"]
#         ).count(),

#         "cancelled": registrations.filter(
#             status="CANCELLED"
#         ).count(),

#         "admitted": registrations.filter(
#             admission_status__in=["REQUESTED", "ADMITTED"]
#         ).count(),
#     }


def get_today_registration_counts(medical_staff):

    today = timezone.localdate()

    registrations = PatientRegistration.objects.filter(
        shift_assignment__medical_staff=medical_staff,
        registration_date=today,
    )

    # Same as today_schedule(): ADMITTED count is not limited to today.
    admitted_qs = PatientRegistration.objects.filter(
        shift_assignment__medical_staff=medical_staff,
        admission_status__in=["REQUESTED", "ADMITTED"],
    )

    return {
        "total": registrations.exclude(
            status="CANCELLED"
        ).count(),

        "waiting": registrations.filter(
            status="WAITING"
        ).count(),

        "in_progress": registrations.filter(
            status="IN_PROGRESS"
        ).exclude(
            admission_status__in=["REQUESTED", "ADMITTED"]
        ).count(),

        "completed": registrations.filter(
            status="COMPLETED"
        ).exclude(
            admission_status__in=["REQUESTED", "ADMITTED"]
        ).count(),

        "cancelled": registrations.filter(
            status="CANCELLED"
        ).count(),

        "admitted": admitted_qs.count(),
    }

@login_required
@require_POST
def complete_patient_consultation(
    request,
    registration_id
):
    try:
        medical_staff = request.user.medical_staff_profile

    except Exception:
        return JsonResponse(
            {
                "success": False,
                "message": "Medical staff profile not found.",
            },
            status=403,
        )

    # ==========================================================
    # JSON
    # ==========================================================

    try:
        data = json.loads(
            request.body.decode("utf-8")
        )

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):
        return JsonResponse(
            {
                "success": False,
                "message": "Invalid JSON request.",
            },
            status=400,
        )

    # ==========================================================
    # REGISTRATION
    # ==========================================================

    registration = get_object_or_404(
        PatientRegistration.objects.select_related(
            "patient",
            "appointment",
            "medical_visit",
            "shift_assignment",
            "shift_assignment__medical_staff",
        ),
        id=registration_id,
    )

    # ==========================================================
    # STAFF VALIDATION
    # ==========================================================

    if (
        not registration.shift_assignment
        or registration.shift_assignment.medical_staff
        != medical_staff
    ):
        return JsonResponse(
            {
                "success": False,
                "message": "This patient is not assigned to you.",
            },
            status=403,
        )

    # ==========================================================
    # STATUS VALIDATION
    # ==========================================================

    if registration.status != "IN_PROGRESS":
        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Patient consultation is not in progress."
                ),
            },
            status=400,
        )

    # ==========================================================
    # MEDICAL VISIT
    # ==========================================================

    medical_visit = registration.medical_visit

    if not medical_visit:
        return JsonResponse(
            {
                "success": False,
                "message": "Medical visit not found.",
            },
            status=400,
        )

    # ==========================================================
    # NORMAL CONSULTATION DATA
    # ==========================================================

    visit_type = (
        data.get("visit_type")
        or medical_visit.visit_type
        or "CONSULTATION"
    )

    diagnosis = (
        data.get("diagnosis")
        or ""
    ).strip()

    treatment = (
        data.get("treatment")
        or ""
    ).strip()

    medications = (
        data.get("medications")
        or ""
    ).strip()

    notes = (
        data.get("notes")
        or ""
    ).strip()

    follow_up_required = bool(
        data.get(
            "follow_up_required",
            False
        )
    )

    follow_up_date_value = (
        data.get("follow_up_date")
        or None
    )

    # ==========================================================
    # REQUIRED VALIDATION
    # ==========================================================

    if not diagnosis:
        return JsonResponse(
            {
                "success": False,
                "message": "Diagnosis is required.",
            },
            status=400,
        )

    if not treatment:
        return JsonResponse(
            {
                "success": False,
                "message": "Treatment is required.",
            },
            status=400,
        )

    # ==========================================================
    # FOLLOW-UP DATE
    # ==========================================================

    follow_up_date = None

    if follow_up_date_value:
        try:
            follow_up_date = datetime.strptime(
                follow_up_date_value,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Invalid follow-up date.",
                },
                status=400,
            )

    # ==========================================================
    # ATHLETE TEMPORARY DATA
    #
    # These come from frontend ONLY when
    # Complete Consultation is clicked.
    # ==========================================================

    medical_care_data = (
        data.get("athlete_medical_care")
        or None
    )

    injury_data = (
        data.get("athlete_injury")
        or None
    )

    # ==========================================================
    # TRANSACTION
    # ==========================================================

    try:

        with transaction.atomic():

            # ==================================================
            # 1. SAVE NORMAL CONSULTATION
            # ==================================================

            medical_visit.visit_type = visit_type

            medical_visit.diagnosis = diagnosis

            medical_visit.treatment = treatment

            medical_visit.medications = medications

            medical_visit.notes = notes

            medical_visit.follow_up_required = (
                follow_up_required
            )

            medical_visit.follow_up_date = (
                follow_up_date
            )

            # Don't mark completed yet.
            # We will do it only after athlete data
            # is successfully saved.

            medical_visit.save()

            # ==================================================
            # 2. ATHLETE MEDICAL CARE
            # ==================================================

            if medical_care_data:

                athlete_id = (
                    medical_care_data.get(
                        "athlete_id"
                    )
                    or None
                )

                patient_id = (
                    medical_care_data.get(
                        "patient_id"
                    )
                    or registration.patient_id
                )

                if athlete_id:

                    athlete = get_object_or_404(
                        Athletic,
                        athlete_id=athlete_id,
                    )

                    # ------------------------------------------
                    # Get / create medical profile
                    # ------------------------------------------

                    athlete_profile = (
                        AthleteMedicalProfile.objects
                        .select_for_update()
                        .filter(
                            athlete=athlete
                        )
                        .first()
                    )

                    if not athlete_profile:

                        athlete_profile, created = (
                            get_or_create_athlete_medical_profile(
                                athlete=athlete,
                                patient=registration.patient,
                            )
                        )

                    # Make sure patient relation is correct

                    if (
                        patient_id
                        and str(
                            athlete_profile.patient_profile_id
                        )
                        != str(patient_id)
                    ):
                        athlete_profile.patient_profile = (
                            registration.patient
                        )

                    # ------------------------------------------
                    # Medical Care fields
                    # ------------------------------------------

                    if (
                        "medical_clearance_status"
                        in medical_care_data
                    ):
                        athlete_profile.medical_clearance_status = (
                            medical_care_data.get(
                                "medical_clearance_status"
                            )
                            or athlete_profile.medical_clearance_status
                        )

                    if "clearance_date" in medical_care_data:

                        clearance_date_value = (
                            medical_care_data.get(
                                "clearance_date"
                            )
                            or None
                        )

                        if clearance_date_value:
                            try:
                                athlete_profile.clearance_date = (
                                    datetime.strptime(
                                        clearance_date_value,
                                        "%Y-%m-%d"
                                    ).date()
                                )

                            except ValueError:
                                raise ValueError(
                                    "Invalid medical clearance date."
                                )

                        else:
                            athlete_profile.clearance_date = None

                    if "clearance_expiry" in medical_care_data:

                        clearance_expiry_value = (
                            medical_care_data.get(
                                "clearance_expiry"
                            )
                            or None
                        )

                        if clearance_expiry_value:
                            try:
                                athlete_profile.clearance_expiry = (
                                    datetime.strptime(
                                        clearance_expiry_value,
                                        "%Y-%m-%d"
                                    ).date()
                                )

                            except ValueError:
                                raise ValueError(
                                    "Invalid clearance expiry date."
                                )

                        else:
                            athlete_profile.clearance_expiry = None

                    if "fitness_level" in medical_care_data:
                        athlete_profile.fitness_level = (
                            medical_care_data.get(
                                "fitness_level"
                            )
                            or ""
                        )

                    if "injury_risk" in medical_care_data:
                        athlete_profile.injury_risk = (
                            medical_care_data.get(
                                "injury_risk"
                            )
                            or athlete_profile.injury_risk
                        )

                    if "medical_restrictions" in medical_care_data:
                        athlete_profile.current_medical_restrictions = (
                            medical_care_data.get(
                                "medical_restrictions"
                            )
                            or ""
                        )

                    if "emergency_action_plan" in medical_care_data:
                        athlete_profile.emergency_action_plan = (
                            medical_care_data.get(
                                "emergency_action_plan"
                            )
                            or ""
                        )

                    if "next_medical_checkup" in medical_care_data:

                        next_checkup_value = (
                            medical_care_data.get(
                                "next_medical_checkup"
                            )
                            or None
                        )

                        if next_checkup_value:
                            try:
                                athlete_profile.next_medical_checkup = (
                                    datetime.strptime(
                                        next_checkup_value,
                                        "%Y-%m-%d"
                                    ).date()
                                )

                            except ValueError:
                                raise ValueError(
                                    "Invalid next medical checkup date."
                                )

                        else:
                            athlete_profile.next_medical_checkup = None

                    # ==================================================
                    # TEAM PHYSICIAN
                    # ==================================================

                    # ==================================================
                    # TEAM PHYSICIAN
                    # ==================================================

                    if "team_physician" in medical_care_data:

                        team_physician_id = (
                            medical_care_data.get("team_physician")
                            or None
                        )

                        if team_physician_id:

                            team_physician = (
                                MedicalStaffProfile.objects
                                .filter(
                                    id=team_physician_id,
                                    status="ACTIVE",
                                )
                                .first()
                            )

                            if not team_physician:
                                raise ValueError(
                                    "Selected team physician not found or inactive."
                                )

                            athlete_profile.team_physician = (
                                team_physician
                            )

                        else:

                            athlete_profile.team_physician = None
                    # ==================================================
                    # PHYSIOTHERAPIST
                    # ==================================================

                    # ==================================================
                    # PHYSIOTHERAPIST
                    # ==================================================

                    if "physiotherapist" in medical_care_data:

                        physiotherapist_id = (
                            medical_care_data.get("physiotherapist")
                            or None
                        )

                        if physiotherapist_id:

                            physiotherapist = (
                                MedicalStaffProfile.objects
                                .filter(
                                    id=physiotherapist_id,
                                    status="ACTIVE",
                                )
                                .first()
                            )

                            if not physiotherapist:
                                raise ValueError(
                                    "Selected physiotherapist not found or inactive."
                                )

                            athlete_profile.physiotherapist = (
                                physiotherapist
                            )

                        else:

                            athlete_profile.physiotherapist = None

                    athlete_profile.save()

            # ==================================================
            # 3. ATHLETE INJURY
            # ==================================================

            if injury_data:

                athlete_id = (
                    injury_data.get(
                        "athlete_id"
                    )
                    or None
                )

                athlete_medical_id = (
                    injury_data.get(
                        "athlete_medical_id"
                    )
                    or None
                )

                if not athlete_id:
                    raise ValueError(
                        "Athlete ID is required for injury."
                    )

                # ------------------------------------------
                # Athlete
                # ------------------------------------------

                athlete = get_object_or_404(
                    Athletic,
                    athlete_id=athlete_id,
                )

                # ------------------------------------------
                # Medical Profile
                # ------------------------------------------

                athlete_profile = (
                    AthleteMedicalProfile.objects
                    .select_for_update()
                    .filter(
                        athlete=athlete
                    )
                    .first()
                )

                if not athlete_profile:

                    athlete_profile, created = (
                        get_or_create_athlete_medical_profile(
                            athlete=athlete,
                            patient=registration.patient,
                        )
                    )

                # ------------------------------------------
                # Injury fields
                # ------------------------------------------

                injury_title = (
                    injury_data.get(
                        "injury_title"
                    )
                    or ""
                ).strip()

                injury_type = (
                    injury_data.get(
                        "injury_type"
                    )
                    or ""
                ).strip()

                body_part = (
                    injury_data.get(
                        "body_part"
                    )
                    or ""
                ).strip()

                side = (
                    injury_data.get(
                        "side"
                    )
                    or ""
                )

                severity = (
                    injury_data.get(
                        "severity"
                    )
                    or ""
                )

                cause = (
                    injury_data.get(
                        "cause"
                    )
                    or ""
                ).strip()

                injury_date_value = (
                    injury_data.get(
                        "injury_date"
                    )
                    or None
                )

                injury_time_value = (
                    injury_data.get(
                        "injury_time"
                    )
                    or None
                )

                location = (
                    injury_data.get(
                        "location"
                    )
                    or ""
                ).strip()

                symptoms = (
                    injury_data.get(
                        "symptoms"
                    )
                    or ""
                ).strip()

                injury_diagnosis = (
                    injury_data.get(
                        "diagnosis"
                    )
                    or ""
                ).strip()

                injury_treatment = (
                    injury_data.get(
                        "treatment"
                    )
                    or ""
                ).strip()

                recovery_days_value = (
                    injury_data.get(
                        "estimated_recovery_days"
                    )
                    or 0
                )

                expected_return_value = (
                    injury_data.get(
                        "expected_return_date"
                    )
                    or None
                )

                actual_return_value = (
                    injury_data.get(
                        "actual_return_date"
                    )
                    or None
                )

                hospitalization_required = bool(
                    injury_data.get(
                        "hospitalization_required",
                        False
                    )
                )

                surgery_required = bool(
                    injury_data.get(
                        "surgery_required",
                        False
                    )
                )

                injury_status = (
                    injury_data.get(
                        "injury_status"
                    )
                    or "ACTIVE"
                )

                injury_notes = (
                    injury_data.get(
                        "notes"
                    )
                    or ""
                ).strip()

                # ------------------------------------------
                # Required injury validation
                # ------------------------------------------

                if not injury_title:
                    raise ValueError(
                        "Injury title is required."
                    )

                if not injury_type:
                    raise ValueError(
                        "Injury type is required."
                    )

                if not body_part:
                    raise ValueError(
                        "Body part is required."
                    )

                if not severity:
                    raise ValueError(
                        "Injury severity is required."
                    )

                if not injury_date_value:
                    raise ValueError(
                        "Injury date is required."
                    )

                if not injury_diagnosis:
                    raise ValueError(
                        "Injury diagnosis is required."
                    )

                # ------------------------------------------
                # Date conversion
                # ------------------------------------------

                try:
                    injury_date = datetime.strptime(
                        injury_date_value,
                        "%Y-%m-%d"
                    ).date()

                except ValueError:
                    raise ValueError(
                        "Invalid injury date."
                    )

                # ------------------------------------------
                # Time conversion
                # ------------------------------------------

                injury_time = None

                if injury_time_value:

                    try:
                        injury_time = datetime.strptime(
                            injury_time_value,
                            "%H:%M"
                        ).time()

                    except ValueError:

                        try:
                            injury_time = datetime.strptime(
                                injury_time_value,
                                "%H:%M:%S"
                            ).time()

                        except ValueError:
                            raise ValueError(
                                "Invalid injury time."
                            )

                # ------------------------------------------
                # Expected return date
                # ------------------------------------------

                expected_return_date = None

                if expected_return_value:

                    try:
                        expected_return_date = datetime.strptime(
                            expected_return_value,
                            "%Y-%m-%d"
                        ).date()

                    except ValueError:
                        raise ValueError(
                            "Invalid expected return date."
                        )

                # ------------------------------------------
                # Actual return date
                # ------------------------------------------

                actual_return_date = None

                if actual_return_value:

                    try:
                        actual_return_date = datetime.strptime(
                            actual_return_value,
                            "%Y-%m-%d"
                        ).date()

                    except ValueError:
                        raise ValueError(
                            "Invalid actual return date."
                        )

                # ------------------------------------------
                # Recovery days
                # ------------------------------------------

                try:
                    estimated_recovery_days = int(
                        recovery_days_value or 0
                    )

                except (
                    ValueError,
                    TypeError
                ):
                    estimated_recovery_days = 0

                # ------------------------------------------
                # Existing injury ID
                # ------------------------------------------

                injury_id = (
                    injury_data.get(
                        "injury_id"
                    )
                    or None
                )

                # ==========================================
                # UPDATE EXISTING INJURY
                # ==========================================

                if injury_id:

                    injury = (
                        InjuryRecord.objects
                        .select_for_update()
                        .filter(
                            id=injury_id,
                            medical_profile=athlete_profile,
                            athlete=athlete,
                        )
                        .first()
                    )

                    if not injury:
                        raise ValueError(
                            "Injury record not found."
                        )

                    injury.injury_title = injury_title
                    injury.injury_type = injury_type
                    injury.body_part = body_part
                    injury.side = side
                    injury.severity = severity
                    injury.cause = cause
                    injury.injury_date = injury_date
                    injury.injury_time = injury_time
                    injury.location = location
                    injury.symptoms = symptoms
                    injury.diagnosis = injury_diagnosis
                    injury.treatment = injury_treatment
                    injury.treated_by = medical_staff
                    injury.hospitalization_required = (
                        hospitalization_required
                    )
                    injury.surgery_required = (
                        surgery_required
                    )
                    injury.estimated_recovery_days = (
                        estimated_recovery_days
                    )
                    injury.expected_return_date = (
                        expected_return_date
                    )
                    injury.actual_return_date = (
                        actual_return_date
                    )
                    injury.injury_status = injury_status
                    injury.notes = injury_notes

                    injury.save()

                # ==========================================
                # CREATE NEW INJURY
                # ==========================================

                else:

                    InjuryRecord.objects.create(
                      
                        medical_profile=athlete_profile,

                        injury_title=injury_title,
                        injury_type=injury_type,
                        body_part=body_part,

                        side=side,
                        severity=severity,
                        cause=cause,

                        injury_date=injury_date,
                        injury_time=injury_time,

                        location=location,
                        symptoms=symptoms,

                        diagnosis=injury_diagnosis,
                        treatment=injury_treatment,

                        treated_by=medical_staff,

                        hospitalization_required=(
                            hospitalization_required
                        ),

                        surgery_required=(
                            surgery_required
                        ),

                        estimated_recovery_days=(
                            estimated_recovery_days
                        ),

                        expected_return_date=(
                            expected_return_date
                        ),

                        actual_return_date=(
                            actual_return_date
                        ),

                        injury_status=(
                            injury_status
                        ),

                        notes=injury_notes,
                    )

            # ==================================================
            # 4. ONLY NOW COMPLETE MEDICAL VISIT
            # ==================================================

            medical_visit.visit_status = "COMPLETED"

            medical_visit.save(
                update_fields=[
                    "visit_type",
                    "diagnosis",
                    "treatment",
                    "medications",
                    "notes",
                    "follow_up_required",
                    "follow_up_date",
                    "visit_status",
                    "updated_at",
                ]
            )

            # ==================================================
            # 5. COMPLETE REGISTRATION
            # ==================================================

            registration.status = "COMPLETED"

            registration.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )
            

            if (
                registration.admission_status == "ADMITTED"
                and registration.assigned_room_id
            ):
                room = registration.assigned_room

                room.status = "AVAILABLE"
                room.save(update_fields=["status"])

                registration.admission_status = "DISCHARGED"
                registration.assigned_room = None

                registration.save(
                    update_fields=[
                        "admission_status",
                        "assigned_room",
                        "updated_at",
                    ]
                )

            # ==================================================
            # 6. COMPLETE APPOINTMENT
            # ==================================================

            if registration.appointment:

                appointment = registration.appointment

                appointment.status = "COMPLETED"

                appointment.completed_at = (
                    timezone.localtime()
                )

                appointment.save(
                    update_fields=[
                        "status",
                        "completed_at",
                        "updated_at",
                    ]
                )

        # ======================================================
        # SUCCESS
        # ======================================================

        counts = get_today_registration_counts(
            medical_staff
        )

        return JsonResponse(
            {
                "success": True,

                "message": (
                    "Consultation completed successfully."
                ),

                "status": "COMPLETED",

                "registration_id": (
                    registration.id
                ),

                "visit_id": (
                    medical_visit.id
                ),

                "visit_number": (
                    medical_visit.visit_number
                ),

                "is_athlete": bool(
                    medical_care_data
                    or injury_data
                ),

                "medical_care_saved": bool(
                    medical_care_data
                ),

                "injury_saved": bool(
                    injury_data
                ),

                "counts": counts,
            }
        )

    except ValueError as e:

        return JsonResponse(
            {
                "success": False,
                "message": str(e),
            },
            status=400,
        )

    except Exception as e:

        import traceback

        traceback.print_exc()

        return JsonResponse(
            {
                "success": False,
                "message": str(e),
            },
            status=500,
        )

@login_required
def patient_details(request, patient_id=None):

    try:

        def format_date(value, fmt="%d %b %Y"):
            if not value:
                return "-"

            if hasattr(value, "strftime"):
                return value.strftime(fmt)

            return str(value)


        def format_time(value, fmt="%I:%M %p"):
            if not value:
                return "-"

            if hasattr(value, "strftime"):
                return value.strftime(fmt)

            return str(value)


        def get_staff_name(staff):

            if not staff:
                return "-"

            user = getattr(staff, "user", None)

            if user:

                # --------------------------------------------------
                # If full_name is a property
                # --------------------------------------------------

                full_name = getattr(user, "full_name", None)

                if full_name:
                    return full_name

                # --------------------------------------------------
                # If name is available
                # --------------------------------------------------

                name = getattr(user, "name", None)

                if name:
                    return name

                # --------------------------------------------------
                # Build name from actual User fields
                # --------------------------------------------------

                first_name = getattr(
                    user,
                    "first_name",
                    ""
                ) or ""

                middle_name = getattr(
                    user,
                    "middle_name",
                    ""
                ) or ""

                last_name = getattr(
                    user,
                    "last_name",
                    ""
                ) or ""

                full_name = " ".join(
                    filter(
                        None,
                        [
                            first_name,
                            middle_name,
                            last_name,
                        ],
                    )
                ).strip()

                if full_name:
                    return full_name

                # --------------------------------------------------
                # Username fallback
                # --------------------------------------------------

                username = getattr(
                    user,
                    "username",
                    None
                )

                if username:
                    return username

            return str(staff)


        # ==========================================================
        # REGISTRATION
        # ==========================================================

        registration_id = request.GET.get(
            "registration_id"
        )

        if not registration_id:

            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        "Registration ID is required."
                    ),
                },
                status=400,
            )


        registration = get_object_or_404(
            PatientRegistration.objects.select_related(
                "patient",
                "appointment",
                "medical_visit",
                "schedule",
                "schedule__department",
                "shift_assignment",
                "shift_assignment__shift",
                "shift_assignment__shift__department",
            ),
            id=registration_id,
        )


        patient = registration.patient


        if not patient:

            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        "Patient is not assigned to this "
                        "registration."
                    ),
                },
                status=400,
            )


        # ==========================================================
        # PATIENT ID VALIDATION
        # ==========================================================

        if patient_id is not None:

            if str(patient.id) != str(patient_id):

                print(
                    "WARNING: Patient ID mismatch",
                    {
                        "url_patient_id":
                            patient_id,

                        "registration_id":
                            registration.id,

                        "actual_patient_id":
                            patient.id,
                    },
                )


        appointment = registration.appointment


        # ==========================================================
        # PATIENT NAME
        # ==========================================================

        patient_name = "-"


        # ----------------------------------------------------------
        # STUDENT
        # ----------------------------------------------------------

        if hasattr(patient, "student") and patient.student:

            student_user = getattr(
                patient.student,
                "user",
                None
            )

            if student_user:

                patient_name = (
                    getattr(
                        student_user,
                        "full_name",
                        None
                    )
                    or (
                        f"{getattr(student_user, 'first_name', '')} "
                        f"{getattr(student_user, 'last_name', '')}"
                    ).strip()
                    or getattr(
                        student_user,
                        "username",
                        None
                    )
                    or "-"
                )


        # ----------------------------------------------------------
        # STAFF
        # ----------------------------------------------------------

        elif hasattr(patient, "staff") and patient.staff:

            staff_user = getattr(
                patient.staff,
                "user",
                None
            )

            if staff_user:

                patient_name = (
                    getattr(
                        staff_user,
                        "full_name",
                        None
                    )
                    or (
                        f"{getattr(staff_user, 'first_name', '')} "
                        f"{getattr(staff_user, 'last_name', '')}"
                    ).strip()
                    or getattr(
                        staff_user,
                        "username",
                        None
                    )
                    or "-"
                )


        # ----------------------------------------------------------
        # FACULTY
        # ----------------------------------------------------------

        elif hasattr(patient, "faculty") and patient.faculty:

            faculty_user = getattr(
                patient.faculty,
                "user",
                None
            )

            if faculty_user:

                patient_name = (
                    getattr(
                        faculty_user,
                        "full_name",
                        None
                    )
                    or (
                        f"{getattr(faculty_user, 'first_name', '')} "
                        f"{getattr(faculty_user, 'last_name', '')}"
                    ).strip()
                    or getattr(
                        faculty_user,
                        "username",
                        None
                    )
                    or "-"
                )


        # ----------------------------------------------------------
        # ADMIN
        # ----------------------------------------------------------

        elif hasattr(patient, "admin") and patient.admin:

            admin_obj = patient.admin


            patient_name = (

                getattr(
                    admin_obj,
                    "full_name",
                    None
                )

                or getattr(
                    admin_obj,
                    "name",
                    None
                )

                or "-"

            )


        # ----------------------------------------------------------
        # VISITOR
        # ----------------------------------------------------------

        else:

            patient_name = (

                getattr(
                    patient,
                    "visitor_name",
                    None
                )

                or "-"

            )


        # ==========================================================
        # APPOINTMENT TIME
        # ==========================================================

        appointment_time = "-"


        if (
            appointment
            and appointment.appointment_time
        ):

            appointment_time = format_time(
                appointment.appointment_time
            )


        # ==========================================================
        # PREVIOUS MEDICAL VISITS
        # ==========================================================

        previous_medical_visits_qs = (
            MedicalVisit.objects
            .filter(
                patient_id=patient.id,
                visit_status="COMPLETED",
            )
            .select_related(
                "attending_staff",
                "department",
            )
            .order_by(
                "-visit_date",
                "-visit_time",
            )
        )


        if registration.medical_visit:

            previous_medical_visits_qs = (
                previous_medical_visits_qs
                .exclude(
                    id=registration.medical_visit.id
                )
            )


        previous_visits_data = []


        for visit in previous_medical_visits_qs:

            attending_staff = get_staff_name(
                visit.attending_staff
            )


            department_name = "-"


            if visit.department:

                department_name = getattr(
                    visit.department,
                    "department_name",
                    str(visit.department),
                )


            previous_visits_data.append(
                {
                    "id":
                        visit.id,

                    "visit_number":
                        visit.visit_number or "-",

                    "visit_date":
                        format_date(
                            visit.visit_date,
                            "%d %b %Y",
                        ),

                    "visit_time":
                        format_time(
                            visit.visit_time,
                            "%I:%M %p",
                        ),

                    "visit_type":
                        (
                            visit.get_visit_type_display()
                            if visit.visit_type
                            else "-"
                        ),

                    "diagnosis":
                        visit.diagnosis or "-",

                    "treatment":
                        visit.treatment or "-",

                    "medications":
                        visit.medications or "-",

                    "notes":
                        visit.notes or "-",

                    "follow_up_required":
                        visit.follow_up_required,

                    "follow_up_date":
                        format_date(
                            visit.follow_up_date,
                            "%d %b %Y",
                        ),

                    "attending_staff":
                        attending_staff,

                    "department":
                        department_name,
                }
            )


        # ==========================================================
        # PREVIOUS VISITS COUNT
        # ==========================================================

        previous_visits_count_qs = (
            MedicalVisit.objects
            .filter(
                patient_id=patient.id,
                visit_status="COMPLETED",
            )
        )


        if registration.medical_visit:

            previous_visits_count_qs = (
                previous_visits_count_qs
                .exclude(
                    id=registration.medical_visit.id
                )
            )


        previous_visits_count = (
            previous_visits_count_qs.count()
        )


        # ==========================================================
        # LAST VISIT
        # ==========================================================

        last_visit_obj = (
            MedicalVisit.objects
            .filter(
                patient_id=patient.id,
                visit_status="COMPLETED",
            )
            .order_by(
                "-visit_date",
                "-visit_time",
            )
            .first()
        )


        last_visit = "-"


        if last_visit_obj:

            last_visit = format_date(
                last_visit_obj.visit_date,
                "%d %b %Y",
            )


        # ==========================================================
        # ATHLETE MEDICAL PROFILE
        # ==========================================================

        athlete_profile = (
            AthleteMedicalProfile.objects
            .select_related(
                "athlete",
                "primary_sport",
                "team_physician",
                "team_physician__user",
                "physiotherapist",
                "physiotherapist__user",
            )
            .filter(
                patient_profile_id=patient.id
            )
            .order_by(
                "-updated_at"
            )
            .first()
        )


        # ==========================================================
        # DEFAULT ATHLETE DATA
        # ==========================================================

        athlete_data = {

            "is_athlete":
                False,

            "athlete_id":
                None,

            "athlete_medical_id":
                None,

            "primary_sport":
                "-",

            "team":
                "-",

            "medical_clearance":
                "-",

            "medical_clearance_code":
                "",

            "clearance_date":
                "-",

            "clearance_date_input":
                "",

            "clearance_expiry":
                "-",

            "clearance_expiry_input":
                "",

            "fitness_level":
                "-",

            "fitness_level_code":
                "",

            "injury_risk":
                "-",

            "injury_risk_code":
                "",

            "medical_restrictions":
                "",

            "emergency_action_plan":
                "",

            "last_medical_checkup":
                "-",

            "next_medical_checkup":
                "",

            "previous_injuries":
                "-",

            "notes":
                "-",

            "injuries":
                [],

            "injury_count":
                0,

            "latest_injury":
                None,

            "previous_medical_plan":
                None,

            "care_team": {

                "team_physician":
                    None,

                "team_physician_name":
                    "-",

                "physiotherapist":
                    None,

                "physiotherapist_name":
                    "-",
            },
        }


        # ==========================================================
        # ATHLETE PROFILE DATA
        # ==========================================================

        if athlete_profile:

            athlete = athlete_profile.athlete


            # ------------------------------------------------------
            # PRIMARY SPORT
            # ------------------------------------------------------

            primary_sport = "-"


            if athlete_profile.primary_sport:

                primary_sport = getattr(
                    athlete_profile.primary_sport,
                    "sport_name",
                    str(
                        athlete_profile.primary_sport
                    ),
                )


            # ------------------------------------------------------
            # TEAM
            # ------------------------------------------------------

            team = "-"


            if (
                hasattr(athlete, "team")
                and athlete.team
            ):

                team = str(
                    athlete.team
                )


            # ------------------------------------------------------
            # INJURIES
            # ------------------------------------------------------

            injury_queryset = (
                InjuryRecord.objects
                .filter(
                    medical_profile=athlete_profile
                )
                .select_related(
                    "treated_by",
                    "treated_by__user",
                )
                .order_by(
                    "-injury_date",
                    "-created_at",
                )[:1]
            )


            injuries_data = []


            for injury in injury_queryset:

                treated_by = get_staff_name(
                    injury.treated_by
                )


                injury_data = {

                    "id":
                        injury.id,

                    "injury_title":
                        injury.injury_title or "-",

                    "injury_type":
                        injury.injury_type or "-",

                    "body_part":
                        injury.body_part or "-",

                    "side":
                        (
                            injury.get_side_display()
                            if injury.side
                            else "-"
                        ),

                    "side_code":
                        injury.side or "",

                    "severity":
                        (
                            injury.get_severity_display()
                            if injury.severity
                            else "-"
                        ),

                    "severity_code":
                        injury.severity or "",

                    "cause":
                        injury.cause or "-",

                    "injury_date":
                        format_date(
                            injury.injury_date,
                            "%d %b %Y",
                        ),

                    "injury_time":
                        format_time(
                            injury.injury_time,
                            "%I:%M %p",
                        ),

                    "location":
                        injury.location or "-",

                    "symptoms":
                        injury.symptoms or "-",

                    "diagnosis":
                        injury.diagnosis or "-",

                    "treatment":
                        injury.treatment or "-",

                    "hospitalization_required":
                        injury.hospitalization_required,

                    "surgery_required":
                        injury.surgery_required,

                    "estimated_recovery_days":
                        (
                            injury.estimated_recovery_days
                            if injury.estimated_recovery_days
                            is not None
                            else 0
                        ),

                    "expected_return_date":
                        format_date(
                            injury.expected_return_date,
                            "%d %b %Y",
                        ),

                    "actual_return_date":
                        format_date(
                            injury.actual_return_date,
                            "%d %b %Y",
                        ),

                    "injury_status":
                        injury.injury_status or "-",

                    "injury_status_display":
                        (
                            injury.get_injury_status_display()
                            if injury.injury_status
                            else "-"
                        ),

                    "notes":
                        injury.notes or "-",

                    "treated_by":
                        treated_by,
                }


                injuries_data.append(
                    injury_data
                )


            latest_injury_data = (

                injuries_data[0]

                if injuries_data

                else None
            )


            # ------------------------------------------------------
            # PREVIOUS MEDICAL PLAN
            # ------------------------------------------------------

            previous_medical_plan = None


            previous_visit = (
                MedicalVisit.objects
                .filter(
                    patient_id=patient.id,
                    visit_status="COMPLETED",
                )
            )


            if registration.medical_visit:

                previous_visit = (
                    previous_visit
                    .exclude(
                        id=registration.medical_visit.id
                    )
                )


            previous_visit = (
                previous_visit
                .order_by(
                    "-visit_date",
                    "-visit_time",
                )
                .first()
            )


            if previous_visit:

                previous_medical_plan = {

                    "diagnosis":
                        previous_visit.diagnosis or "",

                    "treatment":
                        previous_visit.treatment or "",

                    "medications":
                        previous_visit.medications or "",

                    "follow_up_required":
                        previous_visit.follow_up_required,

                    "follow_up_date":
                        (
                            previous_visit
                            .follow_up_date
                            .strftime(
                                "%d %b %Y"
                            )

                            if previous_visit.follow_up_date

                            else ""
                        ),

                    "notes":
                        previous_visit.notes or "",
                }


            # ======================================================
            # CARE TEAM
            # ======================================================

            team_physician = (
                athlete_profile.team_physician
            )


            physiotherapist = (
                athlete_profile.physiotherapist
            )


            care_team_data = {

                "team_physician":
                    (
                        team_physician.id
                        if team_physician
                        else None
                    ),

                "team_physician_name":
                    get_staff_name(
                        team_physician
                    ),

                "physiotherapist":
                    (
                        physiotherapist.id
                        if physiotherapist
                        else None
                    ),

                "physiotherapist_name":
                    get_staff_name(
                        physiotherapist
                    ),
            }


            # ======================================================
            # FINAL ATHLETE DATA
            # ======================================================

            athlete_data = {

                "is_athlete":
                    True,

                "athlete_id":
                    athlete.athlete_id,

                "athlete_medical_id":
                    athlete_profile.athlete_medical_id,

                "primary_sport":
                    primary_sport,

                "team":
                    team,

                "medical_clearance":
                    (
                        athlete_profile
                        .get_medical_clearance_status_display()
                    ),

                "medical_clearance_code":
                    (
                        athlete_profile
                        .medical_clearance_status
                        or ""
                    ),

                "clearance_date":
                    format_date(
                        athlete_profile.clearance_date,
                        "%d %b %Y",
                    ),

                "clearance_date_input":
                    (
                        athlete_profile
                        .clearance_date
                        .strftime(
                            "%Y-%m-%d"
                        )

                        if athlete_profile.clearance_date

                        else ""
                    ),

                "clearance_expiry":
                    format_date(
                        athlete_profile.clearance_expiry,
                        "%d %b %Y",
                    ),

                "clearance_expiry_input":
                    (
                        athlete_profile
                        .clearance_expiry
                        .strftime(
                            "%Y-%m-%d"
                        )

                        if athlete_profile.clearance_expiry

                        else ""
                    ),

                "fitness_level":
                    (
                        athlete_profile
                        .get_fitness_level_display()
                    ),

                "fitness_level_code":
                    (
                        athlete_profile.fitness_level
                        or ""
                    ),

                "injury_risk":
                    (
                        athlete_profile
                        .get_injury_risk_display()
                    ),

                "injury_risk_code":
                    (
                        athlete_profile.injury_risk
                        or ""
                    ),

                "medical_restrictions":
                    (
                        athlete_profile
                        .current_medical_restrictions
                        or ""
                    ),

                "emergency_action_plan":
                    (
                        athlete_profile
                        .emergency_action_plan
                        or ""
                    ),

                "last_medical_checkup":
                    format_date(
                        athlete_profile.last_medical_checkup,
                        "%d %b %Y",
                    ),

                "next_medical_checkup":
                    (
                        athlete_profile
                        .next_medical_checkup
                        .strftime(
                            "%Y-%m-%d"
                        )

                        if athlete_profile
                        .next_medical_checkup

                        else ""
                    ),

                "previous_injuries":
                    (
                        athlete_profile
                        .previous_injuries
                        or "-"
                    ),

                "notes":
                    (
                        athlete_profile.notes
                        or "-"
                    ),

                "injuries":
                    injuries_data,

                "injury_count":
                    len(injuries_data),

                "latest_injury":
                    latest_injury_data,

                "previous_medical_plan":
                    previous_medical_plan,

                "care_team":
                    care_team_data,
            }


        # ==========================================================
        # MEDICAL VISIT
        # ==========================================================

        medical_visit_data = None


        if registration.medical_visit:

            visit = (
                registration.medical_visit
            )


            medical_visit_data = {

                "id":
                    visit.id,

                "visit_number":
                    visit.visit_number or "-",

                "visit_type":
                    visit.visit_type or "",

                "visit_type_display":
                    (
                        visit.get_visit_type_display()

                        if visit.visit_type

                        else "-"
                    ),

                "diagnosis":
                    visit.diagnosis or "",

                "treatment":
                    visit.treatment or "",

                "medications":
                    visit.medications or "",

                "notes":
                    visit.notes or "",

                "follow_up_required":
                    visit.follow_up_required,

                "follow_up_date":
                    (
                        visit.follow_up_date
                        .strftime(
                            "%Y-%m-%d"
                        )

                        if visit.follow_up_date

                        else ""
                    ),

                "visit_status":
                    visit.visit_status,
            }


        # ==========================================================
        # QUEUE NUMBER
        # ==========================================================

        if (
            registration.registration_type
            == "APPOINTMENT"

            and appointment
        ):

            queue_number = (
                appointment.appointment_number
            )


        elif (
            registration.token_number
            is not None
        ):

            queue_number = (
                f"TK-{registration.token_number:03d}"
            )


        else:

            queue_number = (
                registration.registration_number
            )

        patient_data = {

            "id":
                patient.id,

            "name":
                patient_name,

            "role":
                (
                    patient.get_patient_type_display()

                    if hasattr(
                        patient,
                        "get_patient_type_display"
                    )

                    else getattr(
                        patient,
                        "patient_type",
                        "-"
                    )
                ),

            "patient_number":
                getattr(
                    patient,
                    "patient_number",
                    "-"
                ),

            "queue_number":
                queue_number,

            "registration_number":
                registration.registration_number,

            "registration_type":
                registration.registration_type,

            "registration_type_display":
                registration
                .get_registration_type_display(),

            "status":
                registration.status,

            "admission_status":
                    registration.admission_status,

            "appointment_time":
                appointment_time,

            "registration_time":
                format_time(
                    registration.registration_time,
                    "%I:%M %p",
                ),

            "age":
                getattr( 
                    patient,
                    "age",
                    "-"
                ),

            "gender":
                getattr(
                    patient,
                    "gender",
                    "-"
                ),

            "blood_group":
                (
                    getattr(
                        patient,
                        "blood_group",
                        "-"
                    )
                    or "-"
                ),

            "phone":
                (
                    getattr(
                        patient,
                        "phone",
                        "-"
                    )
                    or "-"
                ),

            "email":
                (
                    getattr(
                        patient,
                        "email",
                        "-"
                    )
                    or "-"
                ),

            "allergies":
                (
                    getattr(
                        patient,
                        "allergies",
                        "-"
                    )
                    or "-"
                ),

            "reason":
                (
                    getattr(
                        registration,
                        "chief_complaint",
                        ""
                    )

                    or (
                        getattr(
                            appointment,
                            "reason",
                            ""
                        )

                        if appointment

                        else ""
                    )

                    or "-"
                ),

            "previous_visits":
                previous_visits_count,

            "last_visit":
                last_visit,
        
            "arrived_by_ambulance": bool(registration.arrived_by_ambulance),

            "ambulance_unit_number":
                registration.ambulance_unit_number or "",

            "ambulance_plate":
                registration.ambulance_plate or "",

            "ambulance_service_type":
                registration.ambulance_service_type or "",
        }
        

        team_physicians = (
            MedicalStaffProfile.objects
            .filter(
                status="ACTIVE",
                role__category="DOCTOR",
            )
            .select_related(
                "user",
                "role",
            )
            .order_by(
                "user__first_name",
                "user__last_name",
                "user__username",
            )
        )


        team_physician_options = []


        for staff in team_physicians:

            team_physician_options.append(
                {
                    "id":
                        staff.id,

                    "name":
                        get_staff_name(staff),
                }
            )

        physiotherapists = (
            MedicalStaffProfile.objects
            .filter(
                status="ACTIVE",
                role__category="PHYSIO",
            )
            .select_related(
                "user",
                "role",
            )
            .order_by(
                "user__first_name",
                "user__last_name",
                "user__username",
            )
        )


        physiotherapist_options = []


        for staff in physiotherapists:

            physiotherapist_options.append(
                {
                    "id":
                        staff.id,

                    "name":
                        get_staff_name(staff),
                }
            )
        return JsonResponse(
            {
                "success":
                    True,

                "patient":
                    patient_data,

                "athlete":
                    athlete_data,

                # Dropdown data
                "team_physicians":
                    team_physician_options,

                "physiotherapists":
                    physiotherapist_options,

                "previous_medical_visits":
                    previous_visits_data,

                "medical_visit":
                    medical_visit_data,
            }
        )


    except Exception as e:

        import traceback

        traceback.print_exc()

        return JsonResponse(
            {
                "success":
                    False,

                "message":
                    str(e),
            },
            status=500,
        )

def generate_visit_number():

    today = timezone.localdate()

    prefix = (
        f"VIS-{today.strftime('%Y%m%d')}"
    )

    last_visit = (
        MedicalVisit.objects
        .filter(
            visit_number__startswith=prefix
        )
        .order_by("-id")
        .first()
    )

    if last_visit:

        try:
            last_number = int(
                last_visit
                .visit_number
                .split("-")[-1]
            )

        except (
            ValueError,
            AttributeError,
        ):
            last_number = 0

        next_number = (
            last_number + 1
        )

    else:

        next_number = 1

    return (
        f"{prefix}-{next_number:04d}"
    )

@login_required
@require_POST
def create_athlete_injury(request):

    try:
        try:
            data = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Invalid JSON request."
                },
                status=400
            )

        athlete_id = data.get("athlete_id")

        if not athlete_id:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Athlete ID is required."
                },
                status=400
            )

        try:
            athlete_profile = AthleteMedicalProfile.objects.get(
                athlete_id=athlete_id
            )
        except AthleteMedicalProfile.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Athlete medical profile not found."
                },
                status=404
            )

        injury_title = (
            data.get("injury_title") or ""
        ).strip()

        injury_type = (
            data.get("injury_type") or ""
        ).strip()

        body_part = (
            data.get("body_part") or ""
        ).strip()

        diagnosis = (
            data.get("diagnosis") or ""
        ).strip()

        severity = data.get("severity") or None
        injury_status = data.get("injury_status") or None

        if not injury_title:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Injury title is required."
                },
                status=400
            )

        if not injury_type:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Injury type is required."
                },
                status=400
            )

        if not body_part:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Body part is required."
                },
                status=400
            )

        if not severity:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Severity is required."
                },
                status=400
            )

        if not diagnosis:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Diagnosis is required."
                },
                status=400
            )

        if not injury_status:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Injury status is required."
                },
                status=400
            )

        injury_date = data.get("injury_date") or None

        if injury_date:
            try:
                injury_date = datetime.strptime(
                    injury_date,
                    "%Y-%m-%d"
                ).date()

            except (ValueError, TypeError):
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Invalid injury date."
                    },
                    status=400
                )

        injury_time = data.get("injury_time") or None

        if injury_time:
            try:
                injury_time = datetime.strptime(
                    injury_time,
                    "%H:%M"
                ).time()

            except (ValueError, TypeError):
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Invalid injury time."
                    },
                    status=400
                )

        estimated_recovery_days = (
            data.get("estimated_recovery_days")
        )

        if estimated_recovery_days in ("", None):
            estimated_recovery_days = 0

        else:
            try:
                estimated_recovery_days = int(
                    estimated_recovery_days
                )

            except (ValueError, TypeError):
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Estimated recovery days must be a number."
                    },
                    status=400
                )

            if estimated_recovery_days < 0:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Estimated recovery days cannot be negative."
                    },
                    status=400
                )

        expected_return_date = (
            data.get("expected_return_date") or None
        )

        if expected_return_date:
            try:
                expected_return_date = datetime.strptime(
                    expected_return_date,
                    "%Y-%m-%d"
                ).date()

            except (ValueError, TypeError):
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Invalid expected return date."
                    },
                    status=400
                )

        actual_return_date = (
            data.get("actual_return_date") or None
        )

        if actual_return_date:
            try:
                actual_return_date = datetime.strptime(
                    actual_return_date,
                    "%Y-%m-%d"
                ).date()

            except (ValueError, TypeError):
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Invalid actual return date."
                    },
                    status=400
                )

        hospitalization_value = data.get(
            "hospitalization_required",
            False
        )

        surgery_value = data.get(
            "surgery_required",
            False
        )

        hospitalization_required = (
            str(hospitalization_value).lower() == "true"
            or hospitalization_value is True
            or hospitalization_value == 1
        )

        surgery_required = (
            str(surgery_value).lower() == "true"
            or surgery_value is True
            or surgery_value == 1
        )

        injury = InjuryRecord.objects.create(

            medical_profile=athlete_profile,

            injury_title=injury_title,

            injury_type=injury_type,

            body_part=body_part,

            side=data.get("side") or None,

            severity=severity,

            cause=(
                data.get("cause") or ""
            ).strip(),

            injury_date=injury_date,

            injury_time=injury_time,

            location=(
                data.get("location") or ""
            ).strip(),

            symptoms=(
                data.get("symptoms") or ""
            ).strip(),

            diagnosis=diagnosis,

            treatment=(
                data.get("treatment") or ""
            ).strip(),

            hospitalization_required=(
                hospitalization_required
            ),

            surgery_required=(
                surgery_required
            ),

            estimated_recovery_days=(
                estimated_recovery_days
            ),

            expected_return_date=(
                expected_return_date
            ),

            actual_return_date=(
                actual_return_date
            ),

            injury_status=injury_status,

            notes=(
                data.get("notes") or ""
            ).strip(),
        )

        return JsonResponse(
            {
                "success": True,

                "message": (
                    "Athlete injury saved successfully."
                ),

                "injury": {
                    "id": injury.pk,

                    "injury_title": (
                        injury.injury_title or "-"
                    ),

                    "injury_type": (
                        injury.injury_type or "-"
                    ),

                    "body_part": (
                        injury.body_part or "-"
                    ),

                    "side": (
                        injury.side or "-"
                    ),

                    "severity": (
                        injury.severity or "-"
                    ),

                    "injury_date": (
                        injury.injury_date.isoformat()
                        if injury.injury_date
                        else "-"
                    ),

                    "injury_time": (
                        injury.injury_time.strftime("%H:%M")
                        if injury.injury_time
                        else "-"
                    ),

                    "diagnosis": (
                        injury.diagnosis or "-"
                    ),

                    "treatment": (
                        injury.treatment or "-"
                    ),

                    "injury_status": (
                        injury.injury_status or "-"
                    ),

                    "estimated_recovery_days": (
                        injury.estimated_recovery_days
                    ),

                    "expected_return_date": (
                        injury.expected_return_date.isoformat()
                        if injury.expected_return_date
                        else "-"
                    ),

                    "actual_return_date": (
                        injury.actual_return_date.isoformat()
                        if injury.actual_return_date
                        else "-"
                    ),
                }
            },
            status=201
        )

    except Exception as e:

        import traceback

        traceback.print_exc()

        return JsonResponse(
            {
                "success": False,
                "message": f"Unable to save athlete injury record: {str(e)}"
            },
            status=500
        )

def ensure_athlete_medical_profile(athlete):

    if not athlete:
        return None
    
    patient_profile = None

    if athlete.student:

        student_profile = getattr(
            athlete.student,
            "student_profile",
            None
        )

        if student_profile:

            patient_profile = getattr(
                student_profile,
                "patient_student_profile",
                None
            )


    if not patient_profile:
        return None

    medical_profile, created = (
        AthleteMedicalProfile.objects.get_or_create(
            athlete=athlete,
            defaults={
                "patient_profile": patient_profile
            }
        )
    )

    if (
        medical_profile.patient_profile_id
        != patient_profile.id
    ):
        medical_profile.patient_profile = patient_profile
        medical_profile.save(
            update_fields=[
                "patient_profile",
                "updated_at",
            ]
        )

    return medical_profile


#  #--------------------------- Appointmnet view end ----------------------------------------------#  

#----------------------------- attendace view start ----------------------------------------------#

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from datetime import datetime, timedelta, date
from decimal import Decimal
import calendar

from Staff.models import StaffAttendance, StaffLeaveRequest, Holiday
from Admin.models import User

@login_required
def attendance(request):
    context = {
        'page_title': 'Attendance',
        'user': request.user,
         "active_sb": "Attendance",
    }
    return render(request, 'swetha/attendance.html', context)

@login_required
def get_attendance_data(request):

    user = request.user
    today = timezone.localdate()

    weekday_map = [
        "MON", "TUE", "WED",
        "THU", "FRI", "SAT", "SUN"
    ]


    medical_staff = getattr(
        user,
        "medical_staff_profile",
        None
    )

    def get_shift_for_date(target_date):

        if not medical_staff:
            return None

        target_day = weekday_map[target_date.weekday()]

        shifts = Shift.objects.filter(
            department=medical_staff.department,
            start_date__lte=target_date,
            end_date__gte=target_date,
        ).order_by("start_time")

        for shift in shifts:

            if target_day in shift.active_weekdays():
                return shift

        return None
    today_shift = get_shift_for_date(today)

    shift_name = "--"
    shift_time = "--"

    if today_shift:

        shift_name = (
            today_shift.shift_label
            or today_shift.get_shift_type_display()
        )

        if (
            today_shift.start_time
            and today_shift.end_time
        ):
            shift_time = (
                f"{today_shift.start_time.strftime('%I:%M %p')}"
                f" - "
                f"{today_shift.end_time.strftime('%I:%M %p')}"
            )

    today_is_holiday = Holiday.objects.filter(
        date=today
    ).exists()

    month = request.GET.get(
        "month",
        today.month
    )

    year = request.GET.get(
        "year",
        today.year
    )

    try:

        month = int(month)
        year = int(year)

    except (ValueError, TypeError):

        month = today.month
        year = today.year

    start_date = date(
        year,
        month,
        1
    )

    if month == 12:

        end_date = (
            date(year + 1, 1, 1)
            - timedelta(days=1)
        )

    else:

        end_date = (
            date(year, month + 1, 1)
            - timedelta(days=1)
        )

    current_date = timezone.localdate()

    record_end_date = (
        current_date
        if (
            year == current_date.year
            and month == current_date.month
        )
        else end_date
    )

    attendances = StaffAttendance.objects.filter(
        user=user,
        date__range=(
            start_date,
            end_date
        )
    ).order_by("-date")

    attendance_by_date = {
        att.date: att
        for att in attendances
    }

    leaves = StaffLeaveRequest.objects.filter(
        staff=user,
        status="approved",
        start_date__lte=end_date,
        end_date__gte=start_date
    )

    all_holidays = Holiday.objects.filter(
        date__range=(
            start_date,
            end_date
        )
    )

    holiday_dates = {
        holiday.date
        for holiday in all_holidays
        if holiday.date <= record_end_date
    }

    holiday_days = len(holiday_dates)

    leave_dates = set()

    for leave in leaves:

        leave_start = max(
            leave.start_date,
            start_date
        )

        leave_end = min(
            leave.end_date,
            record_end_date
        )

        if leave_start <= leave_end:

            current = leave_start

            while current <= leave_end:

                leave_dates.add(current)

                current += timedelta(days=1)

    leave_days = len(leave_dates)

    total_days = (
        record_end_date - start_date
    ).days + 1

    present_days = 0

    for attendance in attendances:

        if (
            attendance.date <= record_end_date
            and attendance.check_in
        ):
            present_days += 1

    working_days = max(
        total_days
        - len(
            holiday_dates
        ),
        0
    )

    absent_days = max(
        working_days
        - present_days
        - leave_days,
        0
    )

    attendance_rate = (
        round(
            present_days
            / working_days
            * 100,
            1
        )
        if working_days > 0
        else 0
    )

    total_hours = Decimal("0.0")

    for attendance in attendances:

        if (
            attendance.date <= record_end_date
            and attendance.total_hours_worked
        ):

            total_hours += Decimal(
                str(
                    attendance.total_hours_worked
                )
            )

    avg_hours = (
        total_hours / present_days
        if present_days > 0
        else Decimal("0.0")
    )

    overtime_hours = Decimal("0.0")

    for attendance in attendances:

        if (
            attendance.date <= record_end_date
            and attendance.total_hours_worked
        ):

            overtime = (
                Decimal(
                    str(
                        attendance.total_hours_worked
                    )
                )
                - Decimal("8.0")
            )

            if overtime > 0:
                overtime_hours += overtime

    today_attendance = attendance_by_date.get(
        today
    )

    if today_is_holiday:

        if (
            today_attendance
            and today_attendance.check_in
        ):

            today_status = {

                "present": True,
                "holiday": True,

                "check_in":
                    timezone.localtime(
                        today_attendance.check_in
                    ).strftime("%I:%M %p"),

                "check_out":
                    timezone.localtime(
                        today_attendance.check_out
                    ).strftime("%I:%M %p")
                    if today_attendance.check_out
                    else "--",

                "hours":
                    (
                        f"{int(today_attendance.total_hours_worked)}h "
                        f"{int((today_attendance.total_hours_worked % 1) * 60)}m"
                    )
                    if today_attendance.total_hours_worked
                    else "--",

                "shift": shift_name,
                "shift_time": shift_time,

                "status":
                    "Working on Holiday"
            }

        else:

            today_status = {

                "present": False,
                "holiday": True,
                "working_holiday": False,

                "check_in": "--",
                "check_out": "--",
                "hours": "--",

                "shift": shift_name,
                "shift_time": shift_time,

                "status": "Holiday"
            }

    elif today_attendance:

        today_status = {

            "present":
                bool(
                    today_attendance.check_in
                ),

            "check_in":
                timezone.localtime(
                    today_attendance.check_in
                ).strftime("%I:%M %p")
                if today_attendance.check_in
                else "--",

            "check_out":
                timezone.localtime(
                    today_attendance.check_out
                ).strftime("%I:%M %p")
                if today_attendance.check_out
                else "--",

            "hours":
                (
                    f"{int(today_attendance.total_hours_worked)}h "
                    f"{int((today_attendance.total_hours_worked % 1) * 60)}m"
                )
                if today_attendance.total_hours_worked
                else "--",

            "shift": shift_name,
            "shift_time": shift_time,

            "status":
                "Completed"
                if today_attendance.check_out

                else "Ongoing"
                if today_attendance.check_in

                else "Not Started"
        }

    else:

        today_status = {

            "present": False,

            "check_in": "--",
            "check_out": "--",
            "hours": "--",

            "shift": shift_name,
            "shift_time": shift_time,

            "status": "Not Started"
        }

    records = []

    late_days = 0

    loop_date = start_date

    while loop_date <= record_end_date:

        att = attendance_by_date.get(
            loop_date
        )

        date_shift = get_shift_for_date(
            loop_date
        )

        status = "Absent"
        remarks = "No Check-in"

        check_in = "--"
        check_out = "--"
        hours = "--"

        if loop_date in leave_dates:

            status = "Leave"
            remarks = "On Leave"

        elif loop_date in holiday_dates:

            if att and att.check_in:

                status = "Present"
                remarks = "Worked on Holiday"

            else:

                status = "Holiday"
                remarks = "Public Holiday"

        elif att and att.check_in:

            check_in_dt = timezone.localtime(
                att.check_in
            )

            check_in = check_in_dt.strftime(
                "%I:%M %p"
            )

            if att.check_out:

                check_out = timezone.localtime(
                    att.check_out
                ).strftime(
                    "%I:%M %p"
                )

            if att.total_hours_worked:

                worked_hours = float(
                    att.total_hours_worked
                )

                hours = (
                    f"{int(worked_hours)}h "
                    f"{int((worked_hours % 1) * 60)}m"
                )

            if date_shift:

                shift_start_dt = datetime.combine(
                    loop_date,
                    date_shift.start_time
                )

                grace_limit = (
                    shift_start_dt
                    + timedelta(minutes=10)
                )

                if check_in_dt > timezone.make_aware(
                    grace_limit,
                    timezone.get_current_timezone()
                ):

                    status = "Late"
                    remarks = "Late Arrival"

                    late_days += 1

                elif att.check_out:

                    status = "Present"
                    remarks = "-"

                else:

                    status = "Present"
                    remarks = "Ongoing"

            else:

                # No shift found
                if att.check_out:

                    status = "Present"
                    remarks = "-"

                else:

                    status = "Present"
                    remarks = "Ongoing"

        elif att:

            status = "Absent"
            remarks = "No Check-in"

        else:

            status = "Absent"
            remarks = "No Check-in"

        records.append({

            "no":
                len(records) + 1,

            "date":
                loop_date.strftime(
                    "%d-%b-%Y"
                ),

            "check_in":
                check_in,

            "check_out":
                check_out,

            "hours":
                hours,

            "status":
                status,

            "remarks":
                remarks,

            "shift":
                (
                    date_shift.shift_label
                    if date_shift
                    else "--"
                ),

            "shift_time":
                (
                    f"{date_shift.start_time.strftime('%I:%M %p')}"
                    f" - "
                    f"{date_shift.end_time.strftime('%I:%M %p')}"
                    if date_shift
                    else "--"
                ),
        })

        loop_date += timedelta(days=1)

    trend_labels = []
    trend_hours = []

    trend_date = start_date

    while trend_date <= record_end_date:

        att = attendance_by_date.get(
            trend_date
        )

        if (
            att
            and att.check_in
            and att.total_hours_worked
        ):

            hours_worked = float(
                att.total_hours_worked
            )

        else:

            hours_worked = 0

        trend_labels.append(
            trend_date.strftime(
                "%d %b"
            )
        )

        trend_hours.append(
            hours_worked
        )

        trend_date += timedelta(days=1)

    return JsonResponse({

        "stats": {

            "total_days":
                total_days,

            "working_days":
                working_days,

            "present":
                present_days,

            "leave":
                leave_days,

            "holidays":
                holiday_days,

            "attendance_rate":
                attendance_rate,

            "avg_hours":
                (
                    f"{int(avg_hours)}h "
                    f"{int((avg_hours % 1) * 60)}m"
                )
                if avg_hours
                else "0h 0m",

            "overtime_hours":
                (
                    f"{int(overtime_hours)}h "
                    f"{int((overtime_hours % 1) * 60)}m"
                )
                if overtime_hours
                else "0h 0m",

            "late_count":
                late_days
        },

        "today":
            today_status,

        "records":
            records,

        "charts": {

            "breakdown": {

                "present":
                    present_days,

                "leave":
                    leave_days,

                "holiday":
                    holiday_days,

                "absent":
                    absent_days,

                "attendance_rate":
                    attendance_rate
            },

            "trend": {

                "labels":
                    trend_labels,

                "hours":
                    trend_hours
            }
        }
    })

@login_required
def check_in(request):

    """API endpoint for checking in"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    user = request.user
    today = timezone.localdate()
    
    existing = StaffAttendance.objects.filter(user=user, date=today).first()
    if existing and existing.check_in:
        return JsonResponse({'error': 'Already checked in today'}, status=400)
    
    now = timezone.now()    
    if existing:
        attendance = existing
        attendance.check_in = now
        attendance.check_out = None
        attendance.total_hours_worked = None
        attendance.save(
            update_fields=[
                "check_in",
                "check_out",
                "total_hours_worked",
            ]
        )

    else:
        attendance = StaffAttendance.objects.create(
            user=user,
            date=today,
            check_in=now,
        )
    return JsonResponse({
        'success': True,
        'check_in': timezone.localtime(now).strftime('%I:%M %p'),
        'message': 'Checked in successfully'
    })

from django.contrib.auth import logout
from django.shortcuts import redirect

@login_required
def logout_view(request):
    if request.method == "POST":

        attendance = StaffAttendance.objects.filter(
            user=request.user,
            date=timezone.localdate()
        ).first()

        if attendance and attendance.check_in and attendance.check_out is None:

            now = timezone.now()
        
            seconds = (now - attendance.check_in).total_seconds()
            hours = Decimal(
                str(round(seconds / 3600, 2))
            )
            attendance.check_out = now

            attendance.check_out = now
            attendance.total_hours_worked = hours
            attendance.save(
                update_fields=[
                    "check_out",
                    "total_hours_worked",
                ]
            )

        logout(request)

    return redirect("login")

@login_required
def export_attendance(request):
    """Export attendance data as Excel (.xlsx)"""

    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    from django.http import HttpResponse
    from datetime import date, timedelta, datetime

    user = request.user
    current_date = timezone.localdate()


    month = request.GET.get(
        "month",
        current_date.month
    )

    year = request.GET.get(
        "year",
        current_date.year
    )

    try:
        month = int(month)
        year = int(year)
    except (ValueError, TypeError):
        month = current_date.month
        year = current_date.year

    start_date = date(year, month, 1)

    if month == 12:
        end_date = date(
            year + 1,
            1,
            1
        ) - timedelta(days=1)
    else:
        end_date = date(
            year,
            month + 1,
            1
        ) - timedelta(days=1)


    record_end_date = (
        current_date
        if year == current_date.year
        and month == current_date.month
        else end_date
    )

    attendances = StaffAttendance.objects.filter(
        user=user,
        date__range=(
            start_date,
            end_date
        )
    ).order_by("date")

    attendance_by_date = {
        att.date: att
        for att in attendances
    }

    leaves = StaffLeaveRequest.objects.filter(
        staff=user,
        status="approved",
        start_date__lte=end_date,
        end_date__gte=start_date
    )

    leave_dates = set()

    for leave in leaves:

        leave_start = max(
            leave.start_date,
            start_date
        )

        leave_end = min(
            leave.end_date,
            record_end_date
        )

        if leave_start <= leave_end:

            loop_date = leave_start

            while loop_date <= leave_end:

                leave_dates.add(loop_date)

                loop_date += timedelta(days=1)

    all_holidays = Holiday.objects.filter(
        date__range=(
            start_date,
            end_date
        )
    )

    holiday_dates = {
        holiday.date
        for holiday in all_holidays
        if holiday.date <= record_end_date
    }

    workbook = Workbook()

    worksheet = workbook.active
    worksheet.title = "Attendance"

    worksheet.merge_cells(
        start_row=1,
        start_column=1,
        end_row=1,
        end_column=6
    )

    title_cell = worksheet.cell(
        row=1,
        column=1
    )

    title_cell.value = (
        f"Attendance Report - "
        f"{start_date.strftime('%B %Y')}"
    )

    title_cell.font = Font(
        bold=True,
        size=16
    )

    title_cell.alignment = Alignment(
        horizontal="center",
        vertical="center"
    )

    worksheet.row_dimensions[1].height = 28

    headers = [
        "Date",
        "Check In",
        "Check Out",
        "Hours Worked",
        "Status",
        "Remarks",
    ]

    header_row = 3

    for column, header in enumerate(
        headers,
        start=1
    ):

        cell = worksheet.cell(
            row=header_row,
            column=column
        )

        cell.value = header

        cell.font = Font(
            bold=True
        )

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

        cell.fill = PatternFill(
            fill_type="solid",
            fgColor="D9EAF7"
        )

    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    loop_date = start_date
    row = header_row + 1

    while loop_date <= record_end_date:

        att = attendance_by_date.get(
            loop_date
        )

        status = "Absent"
        remarks = "No Check-in"

        check_in = "--"
        check_out = "--"
        hours_worked = "--"

        if loop_date in leave_dates:

            status = "Leave"
            remarks = "On Leave"

            if att and att.check_in:

                check_in = timezone.localtime(
                    att.check_in
                ).strftime("%I:%M %p")

                if att.check_out:

                    check_out = timezone.localtime(
                        att.check_out
                    ).strftime("%I:%M %p")

                if att.total_hours_worked:

                    total_hours = float(
                        att.total_hours_worked
                    )

                    hours_worked = (
                        f"{int(total_hours)}h "
                        f"{int((total_hours % 1) * 60)}m"
                    )

        elif loop_date in holiday_dates:

            if att and att.check_in:

                status = "Present"
                remarks = "Worked on Holiday"

                check_in = timezone.localtime(
                    att.check_in
                ).strftime("%I:%M %p")

                if att.check_out:

                    check_out = timezone.localtime(
                        att.check_out
                    ).strftime("%I:%M %p")

                if att.total_hours_worked:

                    total_hours = float(
                        att.total_hours_worked
                    )

                    hours_worked = (
                        f"{int(total_hours)}h "
                        f"{int((total_hours % 1) * 60)}m"
                    )

            else:

                status = "Holiday"
                remarks = "Public Holiday"

        elif att and att.check_in:

            check_in = timezone.localtime(
                att.check_in
            ).strftime("%I:%M %p")

            if att.check_out:

                check_out = timezone.localtime(
                    att.check_out
                ).strftime("%I:%M %p")

            if att.total_hours_worked:

                total_hours = float(
                    att.total_hours_worked
                )

                hours_worked = (
                    f"{int(total_hours)}h "
                    f"{int((total_hours % 1) * 60)}m"
                )

            if (
                timezone.localtime(
                    att.check_in
                ).time()
                >
                datetime.strptime(
                    "09:30:00",
                    "%H:%M:%S"
                ).time()
            ):

                status = "Late"
                remarks = "Late Arrival"

            elif not att.check_out:

                status = "Present"
                remarks = "Ongoing"

            else:

                status = "Present"
                remarks = "-"

        else:

            status = "Absent"
            remarks = "No Check-in"

        values = [
            loop_date.strftime("%d-%b-%Y"),
            check_in,
            check_out,
            hours_worked,
            status,
            remarks,
        ]

        for column, value in enumerate(
            values,
            start=1
        ):

            cell = worksheet.cell(
                row=row,
                column=column
            )

            cell.value = value

            cell.alignment = Alignment(
                horizontal="center",
                vertical="center"
            )

            cell.border = thin_border

        row += 1
        loop_date += timedelta(days=1)

    column_widths = {
        1: 18,
        2: 16,
        3: 16,
        4: 18,
        5: 15,
        6: 25,
    }

    for column, width in column_widths.items():

        worksheet.column_dimensions[
            get_column_letter(column)
        ].width = width
    worksheet.freeze_panes = "A4"
    if row > header_row + 1:

        worksheet.auto_filter.ref = (
            f"A{header_row}:F{row - 1}"
        )
    response = HttpResponse(
        content_type=(
            "application/"
            "vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )

    response["Content-Disposition"] = (
        f'attachment; filename='
        f'"attendance_{month}_{year}.xlsx"'
    )

    workbook.save(response)

    return response



#----------------------------------- attendace view end ----------------------------------------------#

#---------------------------------- patient Regstartion view start ------------------------------------#
import json
from datetime import date
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

SCHEDULES_PER_PAGE = 5

def _patient_display_name(patient):

    if patient.patient_type == "STUDENT" and patient.student:
        return str(patient.student)

    if patient.patient_type == "STAFF" and patient.staff:
        return str(patient.staff)

    if patient.patient_type == "FACULTY" and patient.faculty:
        return str(patient.faculty)

    if patient.patient_type == "ADMIN" and patient.admin:
        return (
            getattr(patient.admin, "full_name", None)
            or patient.admin.get_full_name()
            or patient.admin.username
        )

    if patient.patient_type == "VISITOR":
        return patient.visitor_name or "Unknown"

    return "Unknown"


def _patient_phone(patient):
    if patient.patient_type == "VISITOR":
        return patient.visitor_phone or ""
    if patient.student:
        return patient.student.user.mobile_number or ""
    if patient.staff:
        return patient.staff.user.mobile_number or patient.staff.office_phone or ""
    if patient.faculty:
        return patient.faculty.user.mobile_number or patient.faculty.phone or ""
    if patient.admin:
        return patient.admin.mobile_number or ""
    return ""

def _doctor_display_name(assignment):
    staff = assignment.medical_staff

    if not staff:
        return "—"

    get_name = getattr(staff, "get_full_name", None)

    if callable(get_name):
        name = get_name()
        if name:
            return name

    return str(staff)


def _serialize_patient(patient):

    athlete = None
    medical_profile = None
    if patient.patient_type == "STUDENT" and patient.student:

        athlete = (
            Athletic.objects
            .filter(
                student=patient.student.user,
                is_active=True,
            )
            .first()
        )

    elif patient.patient_type == "STAFF" and patient.staff:

        athlete = (
            Athletic.objects
            .filter(
                student=patient.staff.user,
                is_active=True,
            )
            .first()
        )

    elif patient.patient_type == "FACULTY" and patient.faculty:

        athlete = (
            Athletic.objects
            .filter(
                student=patient.faculty.user,
                is_active=True,
            )
            .first()
        )
    if athlete:

        medical_profile, created = (
            get_or_create_athlete_medical_profile(
                patient=patient,
                athlete=athlete,
            )
        )
    return {

        "id":
            patient.id,

        "patient_number":
            patient.patient_number,

        "name":
            _patient_display_name(patient),

        "patient_type":
            patient.get_patient_type_display(),

        "phone":
            _patient_phone(patient),

        "is_athlete":
            athlete is not None,

        "athlete_id":
            athlete.athlete_id
            if athlete
            else None,

        "athlete_medical_id":
            medical_profile.athlete_medical_id
            if medical_profile
            else None,
    }

def _serialize_schedule(assignment):
    shift = assignment.shift

    return {
        # ShiftAssignment ID
        "assignment_id": assignment.id,

        
        "shift_id": shift.id,

        "doctor_name": _doctor_display_name(assignment),

        "department": (
            shift.department.department_name
            if shift.department
            else "—"
        ),

        "room_number": (
            assignment.room.room_number
            if assignment.room
            else "—"
        ),

        "start_time": (
            shift.start_time.strftime("%I:%M %p")
            if shift.start_time
            else "—"
        ),

        "end_time": (
            shift.end_time.strftime("%I:%M %p")
            if shift.end_time
            else "—"
        ),

        "shift": shift.shift_type,

        "shift_label": shift.shift_label,
    }

def _appointment_user_name(appointment):
    user = appointment.user

    if not user:
        return "—"

    name = user.get_full_name()

    if name:
        return name

    return user.username

def _serialize_queue_row(reg):
    patient = reg.patient
    assignment = reg.shift_assignment
    shift = assignment.shift if assignment else None
    appointment = reg.appointment 
    appointment_number = None

    if reg.appointment:
        appointment_number = reg.appointment.appointment_number

    if reg.registration_type == "APPOINTMENT" and appointment_number:
        display_token = appointment_number

    elif reg.token_number is not None:
        display_token = (
            f"TK-{reg.registration_date:%Y%m%d}-"
            f"{reg.token_number:03d}"
        )

    else:
        display_token = "—"

    return {
        "id": reg.id,

        "token_number": reg.token_number,

        "display_token": display_token,

        "appointment_number": appointment_number,

        "patient_name": (
            _patient_display_name(patient)
            if patient
            else "Unknown"
        ),

        "registration_type": (
            reg.get_registration_type_display()
        ),

        "doctor_name": (
            _doctor_display_name(assignment)
            if assignment
            else "—"
        ),
        "room_number": (
            assignment.room.room_number
            if assignment and assignment.room
            else "—"
        ),

        "registration_time": (
            reg.registration_time.strftime("%I:%M %p")
            if reg.registration_time
            else "—"
        ),
        "appointment_time": appointment.appointment_time.strftime("%H:%M")
        if appointment and appointment.appointment_time
        else None,

        "status": reg.status,

        "status_display": (
            reg.get_status_display()
        ),
    }

def _today_stats(hospital):

    today = date.today()

    qs = PatientRegistration.objects.filter(
        registration_date=today,
        shift_assignment__medical_staff__hospital=hospital,
    )

    return {
        "total": qs.count(),

        "walk_in": qs.filter(
            registration_type="WALK_IN"
        ).count(),

        "appointment": qs.filter(
            registration_type="APPOINTMENT"
        ).count(),

        "waiting": qs.filter(
            status="WAITING"
        ).count(),
    }

@login_required
def patient_registration_page(request):

    medical_staff = getattr(
        request.user,
        "medical_staff_profile",
        None,
    )

    if not medical_staff:
        return HttpResponseForbidden(
            "Medical staff profile not found."
        )

    hospital = medical_staff.hospital

    if not hospital:
        return HttpResponseForbidden(
            "No hospital assigned to this user."
        )


    context = {
        "active_sb": "register",

        "stats": _today_stats(hospital),

        "hospital": hospital,
    }

    return render(
        request,
        "swetha/patient_registration.html",
        context,
    )

@login_required
@require_GET
def patient_search(request):

    q = request.GET.get("q", "").strip()

    if len(q) < 2:
        return JsonResponse({"results": []})
    today = date.today()
    patients =  PatientProfile.objects.exclude(
            registrations__registration_date=today,
            registrations__status__in=["WAITING", "IN_PROGRESS"],
        ) .filter(
        Q(patient_number__icontains=q)

        # Visitor
        | Q(visitor_name__icontains=q)
        | Q(visitor_phone__icontains=q)

        # Student
        | Q(student__student_number__icontains=q)
        | Q(student__user__first_name__icontains=q)
        | Q(student__user__last_name__icontains=q)
        | Q(student__user__mobile_number__icontains=q)

        # Staff
        | Q(staff__employee_id__icontains=q)
        | Q(staff__user__first_name__icontains=q)
        | Q(staff__user__last_name__icontains=q)
        | Q(staff__user__mobile_number__icontains=q)
        | Q(staff__office_phone__icontains=q)

        # Faculty
        | Q(faculty__employee_id__icontains=q)
        | Q(faculty__user__first_name__icontains=q)
        | Q(faculty__user__last_name__icontains=q)
        | Q(faculty__user__mobile_number__icontains=q)
        | Q(faculty__phone__icontains=q)

        # Admin
        | Q(admin__first_name__icontains=q)
        | Q(admin__last_name__icontains=q)
        | Q(admin__mobile_number__icontains=q)
    ).select_related(
        "student",
        "staff",
        "faculty",
        "admin",
    )[:10]

    results = []

    for p in patients:

        data = _serialize_patient(p)

        appointment = (
        Appointment.objects
        .filter(
            patient=p,
            appointment_date=today,
            status__in=["CONFIRMED","ARRIVED", "CHECKED_IN"],
        )
        .select_related(
            "medical_staff",
        )
        .first()
    )

        if appointment and appointment.medical_staff:

            assignment = (
                ShiftAssignment.objects
                .filter(
                    medical_staff=appointment.medical_staff,
                    assignment_start_date__lte=today,
                    assignment_end_date__gte=today,
                    shift__start_date__lte=today,
                    shift__end_date__gte=today,
                )
                .select_related("shift")
                .first()
            )

            if assignment:
                data["has_appointment"] = True

                # IMPORTANT:
                # schedule_id = Shift ID
                data["schedule_id"] = assignment.shift.id

                # IMPORTANT:
                # assignment_id = ShiftAssignment ID
                data["assignment_id"] = assignment.id

            else:
                data["has_appointment"] = False
                data["schedule_id"] = None
                data["assignment_id"] = None

        else:
            data["has_appointment"] = False
            data["schedule_id"] = None
            data["assignment_id"] = None

        results.append(data)
    return JsonResponse({
        "results": results
    })
                
@login_required
def add_patient(request):
    return render(request, "swetha/add_patient.html", {"active_sb": "patients"})

@login_required
@require_GET
def schedule_search(request):

    shift = request.GET.get("shift", "ALL").upper()
    q = request.GET.get("q", "").strip()
    page_number = int(request.GET.get("page", 1))

    today = date.today()

    weekday_map = [
        "MON", "TUE", "WED",
        "THU", "FRI", "SAT", "SUN"
    ]

    today_code = weekday_map[today.weekday()]

    assignments = (
        ShiftAssignment.objects
        .filter(
            assignment_start_date__lte=today,
            assignment_end_date__gte=today,
            shift__start_date__lte=today,
            shift__end_date__gte=today,
        )
        .select_related(
            "shift",
            "shift__department",
            "shift__hospital",
            "medical_staff",
            "medical_staff__user",
            "room",

        )
    )

    # Only shifts active today
    assignments = assignments.filter(
        Q(
            shift__recurrence_type="DAILY"
        )
        |
        Q(
            shift__recurrence_type__in=["WEEKLY", "MONTHLY"],
            shift__weekday_pattern__icontains=today_code,
        )
    )
    if q:
        assignments = assignments.filter(
            Q(
                medical_staff__user__first_name__icontains=q
            )
            |
            Q(
                medical_staff__user__last_name__icontains=q
            )
            |
            Q(
                shift__department__department_name__icontains=q
            )
        )

    if shift != "ALL":
        assignments = assignments.filter(
            shift__shift_type=shift
        )

    assignments = assignments.order_by(
        "shift__start_time"
    )

    paginator = Paginator(
        assignments,
        SCHEDULES_PER_PAGE
    )

    page_obj = paginator.get_page(page_number)

    return JsonResponse({
        "results": [
            _serialize_schedule(assignment)
            for assignment in page_obj.object_list
        ],

        "total": paginator.count,
        "total_pages": paginator.num_pages,

        "start": (
            page_obj.start_index()
            if paginator.count
            else 0
        ),

        "end": (
            page_obj.end_index()
            if paginator.count
            else 0
        ),
    })

@login_required
@require_POST
def register_patient(request):
    try:
        payload = json.loads(
            request.body.decode("utf-8")
        )

    except (json.JSONDecodeError, UnicodeDecodeError):

        return JsonResponse(
            {"error": "Invalid request payload."},
            status=400,
        )

    patient_id = payload.get("patient_id")

    assignment_id = payload.get("assignment_id")

    registration_type = payload.get(
        "registration_type",
        "WALK_IN",
    )

    chief_complaint = payload.get(
        "chief_complaint",
        "",
    )

    arrived_by_ambulance = bool(
        payload.get(
            "arrived_by_ambulance",
            False,
        )
    )

    ambulance_id = payload.get(
        "ambulance_id",
        None,
    )

    if not patient_id:

        return JsonResponse(
            {"error": "Select a patient first."},
            status=400,
        )


    if not assignment_id:

        return JsonResponse(
            {"error": "Select a doctor assignment."},
            status=400,
        )


    if arrived_by_ambulance and not ambulance_id:

        return JsonResponse(
            {
                "error": (
                    "Please select the ambulance used "
                    "to bring the patient."
                )
            },
            status=400,
        )

    if registration_type == "APPOINTMENT":

        return JsonResponse(
            {
                "error": (
                    "Appointment registrations are created "
                    "when the appointment is marked as arrived."
                )
            },
            status=400,
        )

    patient = get_object_or_404(
        PatientProfile,
        id=patient_id,
    )

    shift_assignment = get_object_or_404(
        ShiftAssignment,
        id=assignment_id,
    )

    shift = shift_assignment.shift

    today = date.today()

    now = timezone_now_time()

    if registration_type == "WALK_IN":

        last_token = (
            PatientRegistration.objects
            .filter(
                shift_assignment=shift_assignment,
                registration_date=today,
                registration_type="WALK_IN",
            )
            .exclude(
                token_number__isnull=True
            )
            .order_by("-token_number")
            .values_list(
                "token_number",
                flat=True
            )
            .first()
        )

        next_token = (
            last_token or 0
        ) + 1

    else:

        next_token = None

    registration_number = (
        f"REG-"
        f"{today:%Y%m%d}-"
        f"{next_token:04d}-"
        f"{shift.id}"
    )


    registration = PatientRegistration.objects.create(

        registration_number=registration_number,

        patient=patient,

        appointment=None,

        schedule=shift,

        shift_assignment=shift_assignment,
        token_number=next_token,

        registration_type=registration_type,

        priority=2,

        registration_date=today,

        registration_time=now,

        chief_complaint=chief_complaint,

        arrived_by_ambulance=arrived_by_ambulance,

        ambulance_id=(
            str(ambulance_id)
            if ambulance_id
            else None
        ),

        status="WAITING",
    )

    return JsonResponse({
        "success": True,
        "token_number": (
            registration.token_number
        ),
        "display_token": (
            f"TK-"
            f"{registration.registration_date:%Y%m%d}-"
            f"{registration.token_number:03d}"
        ),
        "registration_number": (
            registration.registration_number
        ),
        "queue_row": (
            _serialize_queue_row(
                registration
            )
        ),
    })

def timezone_now_time():
    return timezone.localtime(timezone.now()).time()

from datetime import date, datetime

@login_required
@require_GET
def queue_list(request):
    q = request.GET.get("q", "").strip()
    date_str = request.GET.get("date")
    page = int(request.GET.get("page", 1))

    filter_date = date.today()

    if date_str:
        try:
            filter_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    registrations = (
        PatientRegistration.objects.filter(
            registration_date=filter_date
        )
        .select_related(
            "patient",
            "patient__student",
            "patient__staff",
            "patient__faculty",
            "patient__admin",

            "appointment",

            # ShiftAssignment
            "shift_assignment",
            "shift_assignment__shift",
            "shift_assignment__shift__department",
            "shift_assignment__shift__hospital",
            "shift_assignment__medical_staff",
            "shift_assignment__medical_staff__user",
            "shift_assignment__room",
        )
        .order_by("token_number")
    )

    if q:
        registrations = registrations.filter(
            Q(patient__patient_number__icontains=q)
            | Q(patient__visitor_name__icontains=q)

            | Q(patient__student__user__first_name__icontains=q)
            | Q(patient__student__user__last_name__icontains=q)

            | Q(patient__staff__user__first_name__icontains=q)
            | Q(patient__staff__user__last_name__icontains=q)

            | Q(patient__faculty__user__first_name__icontains=q)
            | Q(patient__faculty__user__last_name__icontains=q)

            | Q(patient__admin__first_name__icontains=q)
            | Q(patient__admin__last_name__icontains=q)

            | Q(token_number__icontains=q)

            | Q(
                shift_assignment__medical_staff__user__first_name__icontains=q
            )
            | Q(
                shift_assignment__medical_staff__user__last_name__icontains=q
            )

            | Q(shift_assignment__shift__department__department_name__icontains=q)
        )

    paginator = Paginator(registrations, 10)
    page_obj = paginator.get_page(page)

    results = []

    for r in page_obj.object_list:
        try:
            results.append(_serialize_queue_row(r))
        except Exception as e:
            import traceback
            traceback.print_exc()

            return JsonResponse({
                "error": str(e),
                "registration_id": r.id,
            }, status=500)

    return JsonResponse({
        "results": results,
        "page": page_obj.number,
        "total_pages": paginator.num_pages,
        "total": paginator.count,
        "start": page_obj.start_index() if paginator.count else 0,
        "end": page_obj.end_index() if paginator.count else 0,
        "has_next": page_obj.has_next(),
        "has_previous": page_obj.has_previous(),
    })

# appointment

def _appointment_user_name(appointment):
    user = appointment.user

    if not user:
        return "—"

    name = user.get_full_name()

    if name:
        return name

    return user.username


def _appointment_user_phone(appointment):
    user = appointment.user

    if not user:
        return ""

    return getattr(user, "mobile_number", "") or ""


def _appointment_doctor_name(appointment):
    staff = appointment.medical_staff

    if not staff:
        return "—"

    get_name = getattr(
        staff,
        "get_full_name",
        None,
    )

    if callable(get_name):
        name = get_name()

        if name:
            return name

    return str(staff)

def _serialize_frontdesk_appointment(appointment):
    patient = appointment.patient

    if patient:
        patient_name = _patient_display_name(patient)
        patient_number = patient.patient_number
        patient_type = patient.get_patient_type_display()
        phone = _patient_phone(patient)
    else:
        patient_name = _appointment_user_name(appointment)
        patient_number = "Not Registered"
        patient_type = "New User"
        phone = _appointment_user_phone(appointment)

    doctor_name = _appointment_doctor_name(appointment)

    room_number = "—"

    if appointment.medical_staff:

        appointment_date = (
            appointment.appointment_date
            or timezone.localdate()
        )

        assignment = (
            ShiftAssignment.objects
            .filter(
                Q(medical_staff=appointment.medical_staff)
                & Q(assignment_start_date__lte=appointment_date)
                & (
                    Q(assignment_end_date__isnull=True)
                    | Q(assignment_end_date__gte=appointment_date)
                )
                & Q(shift__start_date__lte=appointment_date)
                & (
                    Q(shift__end_date__isnull=True)
                    | Q(shift__end_date__gte=appointment_date)
                )
            )
            .select_related(
                "shift",
                "room",
                "medical_staff",
            )
            .order_by(
                "shift__start_time"
            )
            .first()
        )

        if assignment and assignment.room:
            room_number = (
                assignment.room.room_number
                or "—"
            )

    return {
        "id": appointment.id,
        "appointment_number": appointment.appointment_number,

        "patient_id": (
            patient.id
            if patient
            else None
        ),

        "patient_number": patient_number,
        "patient_name": patient_name,
        "patient_type": patient_type,
        "phone": phone,

        "doctor_name": doctor_name,

        "room_number": room_number,

        "service": (
            appointment.service
            if appointment.service
            else "—"
        ),

        "appointment_date": (
            appointment.appointment_date.strftime("%d %b %Y")
            if appointment.appointment_date
            else "—"
        ),

        "appointment_date_raw": (
            appointment.appointment_date.strftime("%Y-%m-%d")
            if appointment.appointment_date
            else ""
        ),

        "appointment_time": (
            appointment.appointment_time.strftime("%H:%M")
            if appointment.appointment_time
            else ""
        ),

        "status": appointment.status,

        "status_display": (
            appointment.get_status_display()
        ),
    }

@login_required
@require_GET
def appointment_list_frontdesk(request):

    today = date.today()

    status = request.GET.get(
        "status",
        "PENDING",
    )

    q = request.GET.get(
        "q",
        ""
    ).strip()


    allowed_statuses = [
        "PENDING",
        "CONFIRMED",
        "ARRIVED",
        "IN_PROGRESS",
         "COMPLETED",
        "NOT_ARRIVED",
         "CANCELLED",
    ]

    if status not in allowed_statuses:
        status = "PENDING"


    appointments = (
        Appointment.objects
        .filter(
            status=status,
        )
        .select_related(
            "patient",
            "patient__student",
            "patient__staff",
            "patient__faculty",
            "patient__admin",
            "medical_staff",
             "hospital",
           
        )
        .order_by(
            "appointment_time"
        )
    )


    # -------------------------
    # Search
    # -------------------------

    if q:

        appointments = appointments.filter(

            Q(
                appointment_number__icontains=q
            )

            |

            Q(
                patient__patient_number__icontains=q
            )

            |

            Q(
                patient__visitor_name__icontains=q
            )

            |

            Q(
                patient__student__user__first_name__icontains=q
            )

            |

            Q(
                patient__student__user__last_name__icontains=q
            )

            |

            Q(
                patient__staff__user__first_name__icontains=q
            )

            |

            Q(
                patient__staff__user__last_name__icontains=q
            )

            |

            Q(
                patient__faculty__user__first_name__icontains=q
            )

            |

            Q(
                patient__faculty__user__last_name__icontains=q
            )

            |

            Q(
                patient__admin__first_name__icontains=q
            )

            |

            Q(
                patient__admin__last_name__icontains=q
            )

            |

            Q(
                medical_staff__user__first_name__icontains=q
            )

            |

            Q(
                medical_staff__user__last_name__icontains=q
            )
            |
             Q(
            service__icontains=q
        )

        ).distinct()


    count_qs = Appointment.objects.all()


    counts = {

        "pending": count_qs.filter(
            status="PENDING"
        ).count(),

        "confirmed": count_qs.filter(
            status="CONFIRMED"
        ).count(),

        "arrived": count_qs.filter(
            status="ARRIVED"
        ).count(),

        "not_arrived": count_qs.filter(
            status="NOT_ARRIVED"
        ).count(),
    }


    return JsonResponse({

        "results": [
            _serialize_frontdesk_appointment(
                appointment
            )
            for appointment in appointments
        ],

        "counts": counts,

        "total": appointments.count(),

        "status": status,
    })

@login_required
@require_POST
def appointment_status_frontdesk(request):

    try:

        data = json.loads(request.body)

        appointment_id = data.get(
            "appointment_id"
        )

        new_status = data.get(
            "status"
        )

        if not appointment_id or not new_status:

            return JsonResponse(
                {
                    "error": (
                        "Appointment ID and status "
                        "are required."
                    )
                },
                status=400,
            )

        appointment = get_object_or_404(
            Appointment.objects.select_related(
                "user",
                "patient",
                "medical_staff",
            ),
            id=appointment_id,
        )

        if new_status == "PENDING":

            if appointment.status not in [
                "CONFIRMED",
                "NOT_ARRIVED",
            ]:
                return JsonResponse(
                    {
                        "error": (
                            "Appointment cannot be moved "
                            "back to pending from its current status."
                        )
                    },
                    status=400,
                )

            PatientRegistration.objects.filter(
                appointment=appointment,
                registration_date=date.today(),
                registration_type="APPOINTMENT",
            ).delete()

            appointment.status = "PENDING"

            appointment.save(
                update_fields=["status"]
            )

            return JsonResponse({
                "success": True,
                "message": (
                    "Appointment moved back to pending "
                    "and removed from today's queue."
                ),
                "status": appointment.status,
                "status_display": appointment.get_status_display(),
            })

        if new_status == "CONFIRMED":

            if appointment.status != "PENDING":

                return JsonResponse(
                    {
                        "error": (
                            "Only pending appointments "
                            "can be confirmed."
                        )
                    },
                    status=400,
                )

            confirmed_time = data.get("appointment_time")

            if not confirmed_time:
                return JsonResponse(
                    {
                        "error": (
                            "Appointment time is required "
                            "when confirming."
                        )
                    },
                    status=400,
                )

            try:
                confirmed_time = datetime.strptime(
                    confirmed_time,
                    "%H:%M"
                ).time()

            except ValueError:
                return JsonResponse(
                    {
                        "error": (
                            "Invalid appointment time format. "
                           
                        )
                    },
                    status=400,
                )
            
            today = timezone.localdate()
            current_time = timezone.localtime().time()

            if appointment.appointment_date == today:

                # Remove seconds/microseconds for comparison
                current_time = current_time.replace(
                    second=0,
                    microsecond=0
                )

                if confirmed_time < current_time:
                    return JsonResponse(
                        {
                            "error": (
                                "Past appointment time cannot be confirmed. "
                                "Please select the current or a future time."
                            )
                        },
                        status=400,
                    )
            appointment.appointment_time = confirmed_time
            appointment.status = "CONFIRMED"

            appointment.save(
                update_fields=[
                    "appointment_time",
                    "status"
                ]
            )

            return JsonResponse({

                "success": True,

                "message": (
                    "Appointment confirmed."
                ),

                "status": appointment.status,

                "status_display": (
                    appointment.get_status_display()
                ),
                "appointment_time": (
                    appointment.appointment_time.strftime(
                        "%H:%M"
                    )
                ),
            })

        if new_status == "CANCELLED":

            if appointment.status != "PENDING":

                return JsonResponse(
                    {
                        "error": (
                            "Only pending appointments "
                            "can be rejected."
                        )
                    },
                    status=400,
                )

            appointment.status = "CANCELLED"

            appointment.cancellation_reason = (
                data.get(
                    "cancellation_reason"
                )
                or "Rejected by front desk."
            )

            appointment.save(
                update_fields=[
                    "status",
                    "cancellation_reason",
                ]
            )

            return JsonResponse({

                "success": True,

                "message": (
                    "Appointment rejected."
                ),

                "status": appointment.status,

                "status_display": (
                    appointment.get_status_display()
                ),
            })


        if new_status == "NOT_ARRIVED":

            if appointment.status != "CONFIRMED":

                return JsonResponse(
                    {
                        "error": (
                            "Only confirmed appointments "
                            "can be marked as not arrived."
                        )
                    },
                    status=400,
                )

            today = date.today()

            PatientRegistration.objects.filter(
                appointment=appointment,
                registration_date=today,
                registration_type="APPOINTMENT",
            ).delete()


            appointment.status = "NOT_ARRIVED"

            appointment.save(
                update_fields=[
                    "status"
                ]
            )

            return JsonResponse({

                "success": True,

                "message": (
                    "Patient marked as not arrived "
                    "and removed from today's queue."
                ),

                "status": appointment.status,

                "status_display": (
                    appointment.get_status_display()
                ),
            })

        if new_status == "ARRIVED":

            if appointment.status != "CONFIRMED":

                return JsonResponse(
                    {
                        "error": (
                            "Only confirmed appointments "
                            "can be marked as arrived."
                        )
                    },
                    status=400,
                )
            today = timezone.localdate()

            if appointment.appointment_date != today:
                return JsonResponse(
                    {
                        "error": (
                            "This appointment can only be marked "
                            "arrived on the appointment date."
                        )
                    },
                    status=400,
                )

            if not appointment.patient:

                # -----------------------------------------------
                # SPORTS APPOINTMENT
                # -----------------------------------------------
                if appointment.service.strip().upper() == "SPORTS":

                    # Find athlete using appointment user
                    athlete = (
                        Athletic.objects
                        .filter(
                            student=appointment.user,
                            is_active=True,
                        )
                        .first()
                    )

                    if not athlete:
                        return JsonResponse(
                            {
                                "error": (
                                    "Athlete profile not found "
                                    "for this Sports appointment."
                                )
                            },
                            status=400,
                        )

                    # -------------------------------------------
                    # Create / get normal PatientProfile
                    # -------------------------------------------

                    patient, patient_created = (
                        get_or_create_patient_profile(
                            appointment.user
                        )
                    )

                    # -------------------------------------------
                    # Create / get AthleteMedicalProfile
                    # -------------------------------------------

                    athlete_medical_profile, medical_created = (
                        get_or_create_athlete_medical_profile(
                            athlete=athlete,
                            patient=patient,
                        )
                    )

                    # -------------------------------------------
                    # Link both to appointment
                    # -------------------------------------------

                    appointment.patient = patient
                    appointment.athlete = athlete_medical_profile

                # -----------------------------------------------
                # NORMAL APPOINTMENT
                # -----------------------------------------------
                else:

                    patient, created = (
                        get_or_create_patient_profile(
                            appointment.user
                        )
                    )

                    appointment.patient = patient

            shift_assignment = (
                ShiftAssignment.objects
                .filter(

                    medical_staff=(
                        appointment.medical_staff
                    ),

                    assignment_start_date__lte=today,

                    assignment_end_date__gte=today,

                    shift__start_date__lte=today,

                    shift__end_date__gte=today,
                )
                .select_related(
                    "shift"
                )
                .first()
            )

            if not shift_assignment:

                return JsonResponse(
                    {
                        "error": (
                            "No active shift assignment "
                            "found for this doctor today."
                        )
                    },
                    status=400,
                )

            shift = shift_assignment.shift

            existing_registration = (
                PatientRegistration.objects
                .filter(

                    appointment=appointment,

                    registration_date=today,

                    registration_type="APPOINTMENT",
                )
                .first()
            )

            if existing_registration:

                appointment.status = "ARRIVED"

                appointment.save(
                    update_fields=[
                        "patient",
                        "status",
                    ]
                )

                return JsonResponse({

                    "success": True,

                    "message": (
                        "Patient already exists "
                        "in today's queue."
                    ),

                    "status": appointment.status,

                    "status_display": (
                        appointment.get_status_display()
                    ),

                    "patient_id": (
                        appointment.patient.id
                    ),

                    "appointment_number": (
                        appointment.appointment_number
                    ),

                    "queue_row": (
                        _serialize_queue_row(
                            existing_registration
                        )
                    ),
                })
            
            registration_number = (
                f"REG-{today:%Y%m%d}-APT-{appointment.id}"
            )

            registration = (
                PatientRegistration.objects.create(

                    registration_number=(
                        registration_number
                    ),

                    patient=(
                        appointment.patient
                    ),
                    appointment=appointment,

                    schedule=shift,

                    shift_assignment=(
                        shift_assignment
                    ),

                    token_number=None,

                    registration_type=(
                        "APPOINTMENT"
                    ),

                    priority=2,

                    registration_date=today,

                    registration_time=(
                        timezone_now_time()
                    ),

                    chief_complaint="",

                    status="WAITING",
                )
            )

            appointment.status = "ARRIVED"

            appointment.save(
                update_fields=[
                    "patient",
                    "status",
                ]
            )

            return JsonResponse({

                "success": True,

                "message": (
                    "Patient marked as arrived "
                    "and added to queue."
                ),

                "status": appointment.status,

                "status_display": (
                    appointment.get_status_display()
                ),

                "patient_id": (
                    appointment.patient.id
                ),

                "appointment_number": (
                    appointment.appointment_number
                ),

                "queue_row": (
                    _serialize_queue_row(
                        registration
                    )
                ),
            })

        if new_status == "CHECKED_IN":

            if appointment.status != "ARRIVED":

                return JsonResponse(
                    {
                        "error": (
                            "Only arrived patients "
                            "can be checked in."
                        )
                    },
                    status=400,
                )
            registration = (
                PatientRegistration.objects
                .filter(
                    appointment=appointment,
                    registration_date=date.today(),
                    registration_type="APPOINTMENT",
                )
                .first()
            )

            if not registration:
                return JsonResponse(
                    {
                        "error": (
                            "No queue registration found "
                            "for this appointment."
                        )
                    },
                    status=400,
                )

            appointment.status = "IN_PROGRESS"

            appointment.checked_in_at = timezone.now()

            appointment.save(
                update_fields=[
                    "status",
                    "checked_in_at",
                ]
            )

            registration.status = "IN_PROGRESS"
            registration.save(
                update_fields=["status"]
            )

            return JsonResponse({

                "success": True,

                "message": (
                    "Patient checked in."
                ),

                "status": appointment.status,

                "status_display": (
                    appointment.get_status_display()

                ),
            })

        return JsonResponse(
            {
                "error": (
                    f"Invalid status transition: "
                    f"{appointment.status} → "
                    f"{new_status}"
                )
            },
            status=400,
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                "error": "Invalid JSON request."
            },
            status=400,
        )

    except Exception as e:

        import traceback

        traceback.print_exc()

        return JsonResponse(
            {
                "error": str(e)
            },
            status=400,
        )

def generate_athlete_medical_id():
    year = timezone.localdate().year

    last_profile = (
        AthleteMedicalProfile.objects
        .filter(
            athlete_medical_id__startswith=f"ATHMED{year}"
        )
        .order_by("-athlete_medical_id")
        .first()
    )

    if last_profile:
        try:
            last_number = int(
                last_profile.athlete_medical_id[-4:]
            )
        except (ValueError, TypeError):
            last_number = 0
    else:
        last_number = 0

    return f"ATHMED{year}{last_number + 1:04d}"

def get_or_create_athlete_medical_profile(
    athlete,
    patient,
):

    medical_profile = (
        AthleteMedicalProfile.objects
        .filter(athlete=athlete)
        .first()
    )

    if medical_profile:

        # Existing profile but patient profile
        # wasn't linked yet
        if not medical_profile.patient_profile:
            medical_profile.patient_profile = patient
            medical_profile.save(
                update_fields=["patient_profile"]
            )

        return medical_profile, False

    medical_profile = (
        AthleteMedicalProfile.objects.create(
            athlete_medical_id=generate_athlete_medical_id(),
            athlete=athlete,
            patient_profile=patient,

            # Optional initial values
            primary_sport=(
                athlete.team.sport
                if athlete.team
                and hasattr(athlete.team, "sport")
                else None
            ),
        )
    )

    return medical_profile, True

def get_or_create_patient_profile(user):


    student = getattr(user, "student_profile", None)

    if student:
        patient, created = PatientProfile.objects.get_or_create(
            student=student,
            defaults={
                "patient_number": generate_patient_number(),
                "patient_type": "STUDENT",
            },
        )

        return patient, created

    staff = getattr(user, "staff_profile", None)

    if staff:
        patient, created = PatientProfile.objects.get_or_create(
            staff=staff,
            defaults={
                "patient_number": generate_patient_number(),
                "patient_type": "STAFF",
            },
        )

        return patient, created

    faculty = getattr(user, "faculty_profile", None)

    if faculty:
        patient, created = PatientProfile.objects.get_or_create(
            faculty=faculty,
            defaults={
                "patient_number": generate_patient_number(),
                "patient_type": "FACULTY",
            },
        )

        return patient, created

    # ==================================================
    # ADMIN
    # ==================================================
    if getattr(user, "is_admin", False):

        patient, created = PatientProfile.objects.get_or_create(
            admin=user,
            defaults={
                "patient_number": generate_patient_number(),
                "patient_type": "ADMIN",
            },
        )

        return patient, created

    raise ValueError(
        "This user does not have a supported patient profile."
    )


def frontdesk_appointments(request):

    today = timezone.localdate()

    status = request.GET.get("status", "PENDING")
    query = request.GET.get("q", "").strip()

    page_number = request.GET.get("page", 1)

    appointments = (
        Appointment.objects
        .filter(
            appointment_date=today,
            status=status,
        )
        .select_related(
            "patient",
            "medical_staff",
            "user",
        )
        .order_by("appointment_time")
    )


    if query:
        appointments = appointments.filter(
            Q(appointment_number__icontains=query)

            | Q(patient__patient_number__icontains=query)
            | Q(patient__user__username__icontains=query)
            | Q(patient__user__first_name__icontains=query)
            | Q(patient__user__last_name__icontains=query)

            | Q(patient__patient_number__icontains=query)
            | Q(patient__visitor_name__icontains=query)

            | Q(patient__student__user__username__icontains=query)
            | Q(patient__student__user__first_name__icontains=query)
            | Q(patient__student__user__last_name__icontains=query)

            | Q(patient__staff__user__username__icontains=query)
            | Q(patient__staff__user__first_name__icontains=query)
            | Q(patient__staff__user__last_name__icontains=query)

            | Q(patient__faculty__user__username__icontains=query)
            | Q(patient__faculty__user__first_name__icontains=query)
            | Q(patient__faculty__user__last_name__icontains=query)

            | Q(patient__admin__username__icontains=query)
            | Q(patient__admin__first_name__icontains=query)
            | Q(patient__admin__last_name__icontains=query)
            # Doctor
            | Q(
                medical_staff__user__first_name__icontains=query
            )
            | Q(
                medical_staff__user__last_name__icontains=query
            )
        ).distinct()

    # =========================
    # PAGINATION
    # 10 APPOINTMENTS / PAGE
    # =========================

    paginator = Paginator(
        appointments,
        10
    )

    page_obj = paginator.get_page(page_number)

    # =========================
    # SERIALIZE
    # =========================

    results = [
        _serialize_frontdesk_appointment(appointment)
        for appointment in page_obj
    ]

    # =========================
    # TAB COUNTS
    # =========================

    counts = {
        "pending": Appointment.objects.filter(
            appointment_date=today,
            status="PENDING",
        ).count(),

        "confirmed": Appointment.objects.filter(
            appointment_date=today,
            status="CONFIRMED",
        ).count(),

        "arrived": Appointment.objects.filter(
            appointment_date=today,
            status="ARRIVED",
        ).count(),

        "not_arrived": Appointment.objects.filter(
            appointment_date=today,
            status="NOT_ARRIVED",
        ).count(),
    }

    return JsonResponse({
        "results": results,

        "total": paginator.count,

        "page": page_obj.number,

        "total_pages": paginator.num_pages,

        "start": (
            page_obj.start_index()
            if paginator.count
            else 0
        ),

        "end": (
            page_obj.end_index()
            if paginator.count
            else 0
        ),

        "counts": counts,
    })

from datetime import datetime, date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from Medical.models import (
    Appointment,
    ShiftAssignment,
)

def is_shift_active_on_date(shift, target_date):

    if not shift or not target_date:
        return False

    if shift.start_date:
        if target_date < shift.start_date:
            return False

    if shift.end_date:
        if target_date > shift.end_date:
            return False

    if shift.recurrence_type == "DAILY":

        return True


    weekday_map = [
        "MON",
        "TUE",
        "WED",
        "THU",
        "FRI",
        "SAT",
        "SUN",
    ]

    active_weekdays = {
        value.strip().upper()
        for value in (
            shift.weekday_pattern or ""
        ).split(",")
        if value.strip()
    }

    current_weekday = weekday_map[
        target_date.weekday()
    ]

    return current_weekday in active_weekdays

@login_required
@require_GET
def doctor_schedule_calendar(request):

    medical_staff = getattr(
        request.user,
        "medical_staff_profile",
        None,
    )

    if not medical_staff:

        return JsonResponse(
            {
                "success": False,
                "error": "Medical staff profile not found.",
            },
            status=403,
        )

    hospital = medical_staff.hospital

    if not hospital:

        return JsonResponse(
            {
                "success": False,
                "error": "No hospital assigned to this user.",
            },
            status=400,
        )

    date_str = request.GET.get("date")

    if date_str:

        try:

            selected_date = datetime.strptime(
                date_str,
                "%Y-%m-%d",
            ).date()

        except (TypeError, ValueError):

            return JsonResponse(
                {
                    "success": False,
                    "error": "Invalid date format. Use YYYY-MM-DD.",
                },
                status=400,
            )

        return get_doctor_schedule_for_date(
            hospital=hospital,
            selected_date=selected_date,
        )

    try:

        year = int(
            request.GET.get(
                "year",
                timezone.localdate().year,
            )
        )

        month = int(
            request.GET.get(
                "month",
                timezone.localdate().month,
            )
        )

    except (TypeError, ValueError):

        return JsonResponse(
            {
                "success": False,
                "error": "Invalid year or month.",
            },
            status=400,
        )


    if month < 1 or month > 12:

        return JsonResponse(
            {
                "success": False,
                "error": "Month must be between 1 and 12.",
            },
            status=400,
        )

    first_day = date(
        year,
        month,
        1,
    )

    if month == 12:

        next_month = date(
            year + 1,
            1,
            1,
        )

    else:

        next_month = date(
            year,
            month + 1,
            1,
        )

    last_day = (
        next_month -
        timedelta(days=1)
    )

    dates = {}

    current_date = first_day

    while current_date <= last_day:

        date_key = current_date.strftime(
            "%Y-%m-%d"
        )

        dates[date_key] = {
            "doctors": 0,
            "appointments": 0,
        }

        current_date += timedelta(days=1)

    # ======================================================
    # APPOINTMENT COUNTS
    # ======================================================

    appointment_counts = (
        Appointment.objects
        .filter(
            hospital=hospital,
            appointment_date__gte=first_day,
            appointment_date__lte=last_day,
        )
        .values(
            "appointment_date",
        )
        .annotate(
            total=Count("id"),
        )
        .order_by(
            "appointment_date",
        )
    )

    for item in appointment_counts:

        appointment_date = item[
            "appointment_date"
        ]

        if not appointment_date:
            continue

        date_key = appointment_date.strftime(
            "%Y-%m-%d"
        )

        if date_key in dates:

            dates[date_key][
                "appointments"
            ] = item["total"]

    assignments = (
    ShiftAssignment.objects
    .filter(
        medical_staff__hospital=hospital,
        assignment_start_date__lte=last_day,
    )
    .filter(
        Q(assignment_end_date__isnull=True)
        | Q(assignment_end_date__gte=first_day)
    )
        .select_related(
            "medical_staff",
            "medical_staff__user",
            "shift",
            "shift__department",
        )
    )

    # ======================================================
    # CHECK EVERY DATE IN MONTH
    # ======================================================

    current_date = first_day

    while current_date <= last_day:

        doctor_ids = set()

        # ==================================================
        # CHECK EVERY ASSIGNMENT
        # ==================================================

        for assignment in assignments:

            shift = assignment.shift


            # ------------------------------------------------
            # ASSIGNMENT RANGE
            # ------------------------------------------------

            assignment_start = (
                assignment.assignment_start_date
            )

            assignment_end = (
                assignment.assignment_end_date
            )

            if assignment_start and current_date < assignment_start:
                continue

            if assignment_end and current_date > assignment_end:
                continue


            # Current date must fall inside
            # assignment date range

            if current_date < assignment_start:
                continue

            if current_date > assignment_end:
                continue


            # ------------------------------------------------
            # SHIFT RANGE
            # ------------------------------------------------

            shift_start = shift.start_date

            shift_end = shift.end_date


            if shift_start:

                if current_date < shift_start:
                    continue


            if shift_end:

                if current_date > shift_end:
                    continue


            # ------------------------------------------------
            # RECURRENCE CHECK
            # ------------------------------------------------

            if not is_shift_active_on_date(
                shift,
                current_date,
            ):
                continue


            # ------------------------------------------------
            # ADD UNIQUE DOCTOR
            # ------------------------------------------------

            doctor_ids.add(
                assignment.medical_staff_id
            )


        # ==================================================
        # SAVE DOCTOR COUNT
        # ==================================================

        date_key = current_date.strftime(
            "%Y-%m-%d"
        )

        dates[date_key][
            "doctors"
        ] = len(doctor_ids)


        # ==================================================
        # NEXT DATE
        # ==================================================

        current_date += timedelta(days=1)


    # ======================================================
    # RESPONSE
    # ======================================================

    return JsonResponse(
        {
            "success": True,

            "year": year,

            "month": month,

            "dates": dates,
        }
    )

def get_doctor_schedule_for_date(
    hospital,
    selected_date,
):

    assignments = (
        ShiftAssignment.objects
        .filter(

            medical_staff__hospital=hospital,
        )
        .select_related(
            "medical_staff",
            "medical_staff__user",
            "shift",
            "shift__department",
        )
        .order_by(
            "shift__start_time",
            "medical_staff__user__first_name",
            "medical_staff__user__last_name",
        )
    )

    doctors = []

    for assignment in assignments:

        doctor = assignment.medical_staff

        shift = assignment.shift

        if shift.start_date:

            if selected_date < shift.start_date:
                continue

        if shift.end_date:

            if selected_date > shift.end_date:
                continue

        if not is_shift_active_on_date(
            shift,
            selected_date,
        ):
            continue

        first_name = (
            doctor.user.first_name or ""
        )

        last_name = (
            doctor.user.last_name or ""
        )

        doctor_name = (
            f"{first_name} {last_name}"
        ).strip()

        if not doctor_name:

            doctor_name = str(doctor)

        department_name = "—"

        if shift.department:

            department_name = (
                shift.department.department_name
            )

        shift_name = (
            getattr(
                shift,
                "shift_label",
                None,
            )
            or "Shift"
        )

        # ==================================================
        # SHIFT TYPE
        # ==================================================

        try:

            shift_type = (
                shift.get_shift_type_display()
            )

        except Exception:

            shift_type = "—"

        # ==================================================
        # START TIME
        # ==================================================

        if shift.start_time:

            start_time = (
                shift.start_time.strftime(
                    "%I:%M %p"
                )
            )

        else:

            start_time = "—"

        # ==================================================
        # END TIME
        # ==================================================

        if shift.end_time:

            end_time = (
                shift.end_time.strftime(
                    "%I:%M %p"
                )
            )

        else:

            end_time = "—"

        # ==================================================
        # ROOM
        # ==================================================

        room_number = (
           assignment.room.room_number
                if assignment.room
                else None
            )
        # ==================================================
        # APPOINTMENT COUNT
        # ==================================================

        appointment_count = (
            Appointment.objects
            .filter(
                hospital=hospital,

                medical_staff=doctor,

                appointment_date=selected_date,
            )
            .count()
        )

        # ==================================================
        # DOCTOR OBJECT
        # ==================================================

        doctors.append(
            {
                "doctor_id": doctor.id,

                "doctor_name": doctor_name,

                "department_name": department_name,

                "shift_name": shift_name,

                "shift_type": shift_type,

                "start_time": start_time,

                "end_time": end_time,

                "room_number": room_number,

                "appointment_count": (
                    appointment_count
                ),
            }
        )

    # ======================================================
    # TOTAL DOCTORS
    # ======================================================

    total_doctors = len(doctors)

    # ======================================================
    # TOTAL APPOINTMENTS
    # ======================================================

    total_appointments = sum(
        doctor["appointment_count"]
        for doctor in doctors
    )

    # ======================================================
    # RESPONSE
    # ======================================================

    return JsonResponse(
        {
            "success": True,

            "date": selected_date.strftime(
                "%Y-%m-%d"
            ),

            "date_display": selected_date.strftime(
                "%d %B %Y"
            ),

            "total_doctors": total_doctors,

            "total_appointments": (
                total_appointments
            ),

            "doctors": doctors,
        }
    )

@login_required
def patient_registration_ambulances(request):

    hospital = None

    if hasattr(request.user, "medical_staff_profile"):
        hospital = request.user.medical_staff_profile.hospital

    if not hospital:

        return JsonResponse({
            "success": True,
            "hospital": None,
            "total": 0,
            "available": 0,
            "dispatched": 0,
            "en_route": 0,
            "at_hospital": 0,
            "maintenance": 0,
            "ambulances": []
        })

    ambulances = hospital.ambulance_services or []

    available_count = sum(
        1 for ambulance in ambulances
        if ambulance.get("status", "").lower() == "available"
    )

    dispatched_count = sum(
        1 for ambulance in ambulances
        if ambulance.get("status", "").lower() == "dispatched"
    )

    en_route_count = sum(
        1 for ambulance in ambulances
        if ambulance.get("status", "").lower() == "en_route"
    )

    at_hospital_count = sum(
        1 for ambulance in ambulances
        if ambulance.get("status", "").lower() == "at_hospital"
    )

    maintenance_count = sum(
        1 for ambulance in ambulances
        if ambulance.get("status", "").lower() == "maintenance"
    )

    return JsonResponse({

        "success": True,

        "hospital": {
            "uuid": str(hospital.uuid),
            "name": hospital.hospital_name
        },

        "total": len(ambulances),

        "available": available_count,

        "dispatched": dispatched_count,

        "en_route": en_route_count,

        "at_hospital": at_hospital_count,

        "maintenance": maintenance_count,

        # IMPORTANT
        # Return ALL ambulances for the table
        "ambulances": ambulances

    })

@login_required
def available_ambulances(request):

    try:
        hospital = (request.user.medical_staff_profile.hospital)
    except Exception:
        return JsonResponse({
            "success": False,
            "message": "Hospital could not be determined.",
            "ambulances": []
        }, status=400)
    if not hospital:
        return JsonResponse({
            "success": False,
            "message": "No hospital assigned.",
            "ambulances": []
        }, status=400)
    ambulances = hospital.ambulance_services or []

    # Only dispatched_ambulances 
    dispatched_ambulances = [
        ambulance
        for ambulance in ambulances
        if ambulance.get("status") == "dispatched"
    ]

    return JsonResponse({

        "success": True,

        "hospital": {
            "id": str(hospital.uuid),
            "name": hospital.hospital_name
        },

        "total_available": len(dispatched_ambulances ),

        "ambulances":dispatched_ambulances 
    })

@login_required
@require_POST
def update_ambulance_status(request):
    try:
        hospital = request.user.medical_staff_profile.hospital

    except Exception:
        return JsonResponse({
            "success": False,
            "message": "Hospital could not be determined."
        }, status=400)

    try:
        data = json.loads(request.body.decode("utf-8"))

    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({
            "success": False,
            "message": "Invalid request data."
        }, status=400)


    ambulance_id = data.get("id")
    new_status = (
        data.get("status", "")
        .strip()
        .lower()
    )

    if not ambulance_id:
        return JsonResponse({
            "success": False,
            "message": "Ambulance ID is required."
        }, status=400)


    ALLOWED_STATUSES = {
            "available",
            "dispatched",
            "maintenance",
            "reserved",
            "outofservice",
        }

    if new_status not in ALLOWED_STATUSES:
        return JsonResponse({
            "success": False,
            "message": "Invalid ambulance status."
        }, status=400)

    ambulances = hospital.ambulance_services or []

    updated_ambulance = None

    for ambulance in ambulances:

        current_id = (
            ambulance.get("uuid")
            or ambulance.get("ambulance_id")
            or ambulance.get("id")
        )

        if str(current_id) == str(ambulance_id):

            ambulance["status"] = new_status

            ambulance["last_updated"] = (
                timezone.now().strftime(
                    "%d %b %Y, %I:%M %p"
                )
            )

            updated_ambulance = ambulance

            break

    if not updated_ambulance:

        return JsonResponse({
            "success": False,
            "message": "Ambulance not found."
        }, status=404)

    hospital.ambulance_services = ambulances

    hospital.save(
        update_fields=[
            "ambulance_services"
        ]
    )

    return JsonResponse({

        "success": True,

        "message": (
            "Ambulance status updated successfully."
        ),

        "ambulance": updated_ambulance,

    })

@login_required
@require_GET
def ambulance_availability(request):
    try:
        hospital = request.user.medical_staff_profile.hospital

    except Exception:
        return JsonResponse({
            "success": False,
            "message": "Hospital could not be determined."
        }, status=400)

    search_query = (
        request.GET.get("q", "")
        .strip()
        .lower()
    )

    try:
        page = int(
            request.GET.get("page", 1)
        )

    except (TypeError, ValueError):
        page = 1


    if page < 1:
        page = 1

    ambulances = (
        hospital.ambulance_services
        or []
    )

    status_counts = {
        "total": len(ambulances),
        "available": 0,
        "dispatched": 0,
        "reserved": 0,
        "outofservice": 0,
        "maintenance": 0,
    }

    for ambulance in ambulances:
        status = (
            str(
                ambulance.get(
                    "status",
                    ""
                )
            )
            .strip()
            .lower()
        )


        if status in status_counts and status != "total":

            status_counts[status] += 1   
    if search_query:

        filtered_ambulances = []

        for ambulance in ambulances:

            searchable_text = " ".join([

                str(
                    ambulance.get(
                        "unitNumber",
                        ambulance.get(
                            "unit_number",
                            ""
                        )
                    )
                ),

                str(
                    ambulance.get(
                        "ambulance_id",
                        ambulance.get(
                            "id",
                            ambulance.get(
                                "uuid",
                                ""
                            )
                        )
                    )
                ),

                str(
                    ambulance.get(
                        "plate",
                        ambulance.get(
                            "registration_number",
                            ""
                        )
                    )
                ),

                str(
                    ambulance.get(
                        "make",
                        ""
                    )
                ),

                str(
                    ambulance.get(
                        "model",
                        ""
                    )
                ),

                str(
                    ambulance.get(
                        "serviceType",
                        ambulance.get(
                            "service_type",
                            ""
                        )
                    )
                ),

                str(
                    ambulance.get(
                        "status",
                        ""
                    )
                ),

            ]).lower()


            if search_query in searchable_text:

                filtered_ambulances.append(
                    ambulance
                )

    else:

        filtered_ambulances = ambulances

    per_page = 5
    total_records = len(
        filtered_ambulances
    )
    total_pages = max(
        1,
        (
            total_records + per_page - 1
        ) // per_page
    )
    if page > total_pages:
        page = total_pages
    start_index = (
        page - 1
    ) * per_page
    end_index = (
        start_index + per_page
    )
    paginated_ambulances = (
        filtered_ambulances[
            start_index:end_index
        ]
    )
    return JsonResponse({

        "success": True,

        "ambulances":
            paginated_ambulances,
            
        "counts":
        status_counts,

        "page":
            page,


        "total_pages":
            total_pages,


        "total":
            total_records,


        "start":
            (
                start_index + 1
                if total_records > 0
                else 0
            ),


        "end":
            min(
                end_index,
                total_records
            ),

    })

#---------------------------------- patient Regstartion view end ------------------------------------#

#---------------------------------- patient History view start ------------------------------------#


from django.db.models import Min, Max, Count
@login_required
def patient_history(request):

    try:
        medical_staff = request.user.medical_staff_profile

    except Exception:
        return render(
            request,
            "swetha/patient_history.html",
            {
                "patient_data": [],
                "patients_page": [],
                "total_patients": 0,
                "total_consultations": 0,
                "this_month": 0,
                "total_followups": 0,
                "monthly_activity": [],
                "visit_breakdown": {
                    "walk_in": 0,
                    "appointment": 0,
                },
                "walk_in_percentage": 0,
                "appointment_percentage": 0,
                "active_sb": "patient_history",
            },
        )

    today = timezone.localdate()

    visits = (
        MedicalVisit.objects
        .filter(
            attending_staff=medical_staff
        )
        .select_related(
            "patient",
            "patient__student",
            "patient__staff",
            "patient__faculty",
            "patient__admin",
            "patient__athlete_profile",
            "department",
        )
        .order_by(
            "visit_date",
            "visit_time",
        )
    )

    total_consultations = visits.count()

    total_patients = (
        visits
        .values("patient_id")
        .distinct()
        .count()
    )

    month_start = today.replace(day=1)

    this_month = visits.filter(
        visit_date__gte=month_start,
        visit_date__lte=today,
    ).count()

    total_followups = visits.filter(
        follow_up_required=True
    ).count()

    patient_summary = (
        visits
        .values(
            "patient_id",
            "patient__patient_number",
        )
        .annotate(
            first_visit_date=Min("visit_date"),
            last_visit_date=Max("visit_date"),
            visits_count=Count("id"),
        )
        .order_by(
            "-last_visit_date"
        )
    )
    search = request.GET.get("search", "").strip().lower()
    visit_type_filter = request.GET.get(
        "visit_type",
        "all",
    ).strip().lower()

    date_filter = request.GET.get(
        "date",
        "all",
    ).strip().lower()

    status_filter = request.GET.get(
        "status",
        "all",
    ).strip().lower()


    patient_data = []


    for summary in patient_summary:

        patient_id = summary["patient_id"]

        patient_visit = (
            visits
            .filter(
                patient_id=patient_id
            )
            .select_related(
                "patient",
                "patient__student",
                "patient__staff",
                "patient__faculty",
                "patient__admin",
                "patient__athlete_profile",
            )
            .order_by(
                "visit_date",
                "visit_time",
            )
            .first()
        )

        if not patient_visit:
            continue

        patient = patient_visit.patient

        patient_name = str(patient)

        patient_visits = (
            visits
            .filter(
                patient_id=patient_id
            )
            .order_by(
                "visit_date",
                "visit_time",
            )
        )

        first_visit = patient_visits.first()
        last_visit = patient_visits.last()

        first_visit_type = "Consultation"

        if first_visit:

            first_registration = (
                PatientRegistration.objects
                .filter(
                    medical_visit=first_visit
                )
                .first()
            )

            if first_registration:

                if (
                    first_registration.registration_type
                    == "WALK_IN"
                ):
                    first_visit_type = "Walk-in"

                elif (
                    first_registration.registration_type
                    == "APPOINTMENT"
                ):
                    first_visit_type = "Appointment"

        status_map = {
            "OPEN": "In Progress",
            "COMPLETED": "Complete",
            "REFERRED": "Referred",
            "CANCELLED": "Cancelled",
        }

        if last_visit:

            status = status_map.get(
                last_visit.visit_status,
                (
                    last_visit.visit_status
                    .replace("_", " ")
                    .title()
                    if last_visit.visit_status
                    else "Completed"
                ),
            )

        else:
            status = "Completed"

        status_class_map = {
            "Complete": "complete",
            "In Progress": "in-progress",
            "Cancelled": "cancelled",
            "Referred": "in-progress",
        }

        status_class = status_class_map.get(
            status,
            "complete",
        )

        patient_type = "Patient"

        if getattr(patient, "athlete_profile", None):
            patient_type = "Athlete"
        elif getattr(patient, "student", None):
            patient_type = "Student"
        elif getattr(patient, "faculty", None):
            patient_type = "Faculty"
        elif getattr(patient, "staff", None):
            patient_type = "Staff"
        elif getattr(patient, "admin", None):
            patient_type = "Admin"

        patient_data.append(
            {
                "patient_id": patient.id,

                "patient": patient_name,

                "patient_number": (
                    patient.patient_number
                ),
                "patient_type": patient_type,

                "first_visit_date": (
                    summary["first_visit_date"]
                ),

                "last_visit_date": (
                    summary["last_visit_date"]
                ),

                "first_visit_type": (
                    first_visit_type
                ),

                "visits_count": (
                    summary["visits_count"]
                ),

                "status": status,

                "status_class": status_class,
            }
        )

    filtered_patient_data = []

    for item in patient_data:

        show = True

        if search:

            patient_name = (
                item["patient"] or ""
            ).lower()

            patient_number = (
                item["patient_number"] or ""
            ).lower()

            if (
                search not in patient_name
                and search not in patient_number
            ):
                show = False

        if (
            show
            and visit_type_filter != "all"
        ):

            row_visit_type = (
                item["first_visit_type"]
                or ""
            ).lower()

            if visit_type_filter == "walk_in":

                if row_visit_type != "walk-in":
                    show = False

            elif visit_type_filter == "appointment":

                if row_visit_type != "appointment":
                    show = False
        if (
            show
            and status_filter != "all"
        ):

            row_status = (
                item["status"] or ""
            ).lower()

            status_map_filter = {
                "complete": "complete",
                "completed": "complete",
                "in_progress": "in progress",
                "referred": "referred",
                "cancelled": "cancelled",
            }

            expected_status = (
                status_map_filter.get(
                    status_filter,
                    status_filter.replace(
                        "_",
                        " ",
                    ),
                )
            )

            if row_status != expected_status:
                show = False

        if (
            show
            and date_filter != "all"
        ):

            last_visit_date = (
                item["last_visit_date"]
            )

            if not last_visit_date:
                show = False

            else:

                if date_filter == "today":

                    if last_visit_date != today:
                        show = False

                elif date_filter == "week":

                    day = today.weekday()

                    week_start = (
                        today
                        - timedelta(
                            days=day
                        )
                    )

                    week_end = (
                        week_start
                        + timedelta(
                            days=6
                        )
                    )

                    if not (
                        week_start
                        <= last_visit_date
                        <= week_end
                    ):
                        show = False

                elif date_filter == "month":

                    if not (
                        last_visit_date.year
                        == today.year
                        and
                        last_visit_date.month
                        == today.month
                    ):
                        show = False

        if show:
            filtered_patient_data.append(item)

    patient_data = filtered_patient_data

    paginator = Paginator(
        patient_data,
        10,
    )

    is_ajax_pagination = (
        request.GET.get("ajax") == "1"
    )

    if is_ajax_pagination:
        page_number = request.GET.get(
            "page",
            1,
        )
    else:
        page_number = 1

    patients_page = paginator.get_page(
        page_number
    )

    monthly_activity = []

    current_month_start = today.replace(
        day=1
    )

    for month_offset in range(
        5,
        -1,
        -1,
    ):

        month = (
            current_month_start.month
            - month_offset
        )

        year = current_month_start.year

        while month <= 0:

            month += 12
            year -= 1

        month_start_date = (
            current_month_start.replace(
                year=year,
                month=month,
                day=1,
            )
        )

        if month == 12:

            next_month = (
                month_start_date.replace(
                    year=year + 1,
                    month=1,
                    day=1,
                )
            )

        else:

            next_month = (
                month_start_date.replace(
                    month=month + 1,
                    day=1,
                )
            )

        count = visits.filter(
            visit_date__gte=month_start_date,
            visit_date__lt=next_month,
        ).count()

        monthly_activity.append(
            {
                "label": month_start_date.strftime(
                    "%b"
                ),
                "count": count,
            }
        )

    registration_breakdown = (
        PatientRegistration.objects
        .filter(
            medical_visit__in=visits
        )
        .values(
            "registration_type"
        )
        .annotate(
            count=Count("id")
        )
    )

    visit_breakdown = {
        "walk_in": 0,
        "appointment": 0,
    }

    for item in registration_breakdown:

        registration_type = (
            item["registration_type"]
        )

        count = item["count"]

        if registration_type == "WALK_IN":

            visit_breakdown["walk_in"] = count

        elif registration_type == "APPOINTMENT":

            visit_breakdown["appointment"] = count

    total_breakdown = (
        visit_breakdown["walk_in"]
        + visit_breakdown["appointment"]
    )

    if total_breakdown > 0:

        walk_in_percentage = round(
            (
                visit_breakdown["walk_in"]
                / total_breakdown
            ) * 100
        )

        appointment_percentage = (
            100 - walk_in_percentage
        )

    else:

        walk_in_percentage = 0
        appointment_percentage = 0

    context = {

        "patient_data": patients_page,
        "patients_page": patients_page,

        "total_patients": total_patients,
        "total_consultations": total_consultations,
        "this_month": this_month,
        "total_followups": total_followups,

        "monthly_activity": monthly_activity,

        "visit_breakdown": visit_breakdown,

        "walk_in_percentage": walk_in_percentage,
        "appointment_percentage": appointment_percentage,
        "active_sb": "patient_history",
    }

    return render(
        request,
        "swetha/patient_history.html",
        context,
    )

@login_required
def patient_medical_history(request, patient_id):

    try:
        medical_staff = request.user.medical_staff_profile

    except Exception:
        return render(
            request,
            "swetha/patient_medical_history.html",
            {
                "patient": None,
                "history": [],
                "total_visits": 0,
                "follow_up_count": 0,
                "first_visit": None,
                "last_visit": None,
                "patient_type": "Patient",
                "is_athlete": False,
                "athlete_medical_history": None,
                "injury_records": [],
                "total_injuries": 0,
                "active_sb": "patient_history",
            }
        )

    patient = get_object_or_404(
        PatientProfile.objects.select_related(
            "student",
            "staff",
            "faculty",
            "admin",
            "athlete_profile",
            "athlete_profile__athlete",
            "athlete_profile__primary_sport",
            "athlete_profile__team_physician",
            "athlete_profile__physiotherapist",
        ),
        id=patient_id,
    )

    patient_type = "Patient"

    if getattr(patient, "athlete_profile", None):
        patient_type = "Athlete"

    elif getattr(patient, "student", None):
        patient_type = "Student"

    elif getattr(patient, "faculty", None):
        patient_type = "Faculty"

    elif getattr(patient, "staff", None):
        patient_type = "Staff"

    elif getattr(patient, "admin", None):
        patient_type = "Admin"

    elif patient.patient_type == "VISITOR":
        patient_type = "Visitor"

    athlete_medical_history = None
    injury_records = InjuryRecord.objects.none()

    athlete_profile = getattr(
        patient,
        "athlete_profile",
        None
    )

    if athlete_profile:

        athlete_medical_history = athlete_profile

        injury_records = (
            InjuryRecord.objects
            .filter(
                medical_profile=athlete_profile
            )
            .select_related(
                "treated_by",
            )
            .order_by(
                "-injury_date",
                "-injury_time",
            )
        )

    total_injuries = injury_records.count()

    injury_paginator = Paginator(
        injury_records,
        4
    )

    injury_page_number = request.GET.get(
        "injury_page",
        1
    )

    injury_records_page = injury_paginator.get_page(
        injury_page_number
    )

    visits = (
        MedicalVisit.objects
        .filter(
            patient=patient,
            attending_staff=medical_staff,
        )
        .select_related(
            "department",
            "athlete_profile",
            "injury_record",
        )
        .order_by(
            "-visit_date",
            "-visit_time",
        )
    )

    history = []

    status_map = {
        "OPEN": "In Progress",
        "COMPLETED": "Complete",
        "REFERRED": "Referred",
        "CANCELLED": "Cancelled",
    }

    status_class_map = {
        "Complete": "complete",
        "In Progress": "in-progress",
        "Cancelled": "cancelled",
        "Referred": "referred",
    }

    visit_type_class_map = {
        "CONSULTATION": "consultation",
        "FOLLOW_UP": "follow-up",
        "EMERGENCY": "emergency",
        "INJURY": "injury",
        "HEALTH_CHECK": "health-check",
        "VACCINATION": "vaccination",
    }

    for visit in visits:

        registration = (
            PatientRegistration.objects
            .filter(
                medical_visit=visit
            )
            .first()
        )

        registration_type = "—"
        registration_type_class = "default"

        if registration:

            registration_type_value = (
                registration.registration_type
            )

            if registration_type_value == "WALK_IN":

                registration_type = "Walk-in"
                registration_type_class = "walk-in"

            elif registration_type_value == "APPOINTMENT":

                registration_type = "Appointment"
                registration_type_class = "appointment"

        arrived_by_ambulance = False
        ambulance_unit_number = None
        ambulance_plate = None
        ambulance_service_type = None

        if registration:

            arrived_by_ambulance = (
                registration.arrived_by_ambulance
            )

            if arrived_by_ambulance:

                ambulance_unit_number = (
                    registration.ambulance_unit_number
                )

                ambulance_plate = (
                    registration.ambulance_plate
                )

                ambulance_service_type = (
                    registration.ambulance_service_type
                )

        visit_type = (
            visit.get_visit_type_display()
        )

        visit_type_class = (
            visit_type_class_map.get(
                visit.visit_type,
                "consultation"
            )
        )

        status = status_map.get(
            visit.visit_status,
            visit.get_visit_status_display()
        )

        status_class = (
            status_class_map.get(
                status,
                "complete"
            )
        )

        injury_record = visit.injury_record

        history.append(
            {
                "visit_id": visit.id,

                "visit_number": visit.visit_number,

                "date": visit.visit_date,

                "time": (
                    visit.visit_time.strftime(
                        "%I:%M %p"
                    )
                    if visit.visit_time
                    else None
                ),

                "registration_type": (
                    registration_type
                ),

                "registration_type_class": (
                    registration_type_class
                ),
                "arrived_by_ambulance": (
                    arrived_by_ambulance
                ),

                "ambulance_unit_number": (
                    ambulance_unit_number
                ),

                "ambulance_plate": (
                    ambulance_plate
                ),

                "ambulance_service_type": (
                    ambulance_service_type
                ),
                "visit_type": visit_type,

                "visit_type_class": (
                    visit_type_class
                ),
                "chief_complaint": (
                    visit.chief_complaint
                    or "No complaint recorded"
                ),

                "diagnosis": (
                    visit.diagnosis
                    or "No diagnosis recorded"
                ),

                "treatment": (
                    visit.treatment
                    or "No treatment recorded"
                ),

                "medications": (
                    visit.medications
                    or "No medications recorded"
                ),

                "notes": (
                    visit.notes
                    or "No additional notes"
                ),

                "follow_up_required": (
                    visit.follow_up_required
                ),

                "follow_up_date": (
                    visit.follow_up_date
                ),
                "status": status,

                "status_class": (
                    status_class
                ),
                "department": (
                    str(visit.department)
                    if visit.department
                    else "—"
                ),
                "injury_record": (
                    injury_record
                ),

                "injury_title": (
                    injury_record.injury_title
                    if injury_record
                    else None
                ),

                "injury_type": (
                    injury_record.injury_type
                    if injury_record
                    else None
                ),

                "injury_body_part": (
                    injury_record.body_part
                    if injury_record
                    else None
                ),

                "injury_severity": (
                    injury_record.get_severity_display()
                    if injury_record
                    else None
                ),

                "injury_status": (
                    injury_record.get_injury_status_display()
                    if injury_record
                    else None
                ),
            }
        )

    total_visits = visits.count()

    follow_up_count = (
        visits
        .filter(
            follow_up_required=True
        )
        .count()
    )

    last_visit = visits.first()

    first_visit = visits.last()

    history_paginator = Paginator(
        history,
        3
    )

    history_page_number = request.GET.get(
        "history_page",
        1
    )

    history_page = history_paginator.get_page(
        history_page_number
    )

    context = {

        "patient": patient,

        "patient_type": patient_type,

        "history": history_page,

        "total_visits": total_visits,

        "follow_up_count": follow_up_count,

        "first_visit": first_visit,

        "last_visit": last_visit,

        "is_athlete": bool(
            athlete_profile
        ),

        "athlete_medical_history": (
            athlete_medical_history
        ),

        "injury_records": (
            injury_records_page
        ),

        "total_injuries": (
            total_injuries
        ),

        "active_sb": "patient_history",
    }

    return render(
        request,
        "swetha/patient_medical_history.html",
        context,
    )

#---------------------------------- patient history view end ------------------------------------#


##########################  kali code start ###################################
from Admin.bela_admin.models import Building, Floor, Room


def _registration_patient_name(patient):
    if not patient:
        return "-"
    if getattr(patient, "student_id", None) and patient.student:
        return patient.student.user.full_name
    if getattr(patient, "staff_id", None) and patient.staff:
        return patient.staff.user.full_name
    if getattr(patient, "faculty_id", None) and patient.faculty:
        return patient.faculty.user.full_name
    if getattr(patient, "admin_id", None) and patient.admin:
        return patient.admin.full_name
    return patient.visitor_name or "-"


def _admission_priority_class(priority):
    if priority == 1:
        return "high"
    if priority == 3:
        return "low"
    return "medium"


def _user_display_name(user):
    if not user:
        return "-"
    if hasattr(user, "full_name") and user.full_name:
        return user.full_name
    if hasattr(user, "get_full_name"):
        name = user.get_full_name()
        if name:
            return name
    return str(user)


def _registration_number_label(reg):
    if reg.appointment:
        return reg.appointment.appointment_number
    if reg.token_number:
        return f"TK-{reg.token_number:03d}"
    return reg.registration_number


def _room_status_counts(building):
    # rooms_qs = Room.objects.filter(floor__building__hospital=hospital)
    if not building:
        rooms_qs = Room.objects.none()
    else:
        rooms_qs = Room.objects.filter(floor__building=building) 
    
    return {
        "available": rooms_qs.filter(status="AVAILABLE").count(),
        "occupied": rooms_qs.filter(status="OCCUPIED").count(),
        "maintenance": rooms_qs.filter(status="MAINTENANCE").count(),
        "blocked": rooms_qs.filter(status="BLOCKED").count(),
    }, rooms_qs.count()


def _serialize_admission_requests(hospital):
    requests = (
        PatientRegistration.objects
        .filter(shift_assignment__medical_staff__hospital=hospital, admission_status="REQUESTED")
        .select_related("patient", "appointment", "admission_requested_by")
        .order_by("-admission_requested_at")
    )

    data = []
    for reg in requests:
        data.append({
            "id": reg.id,
            "patient_name": _registration_patient_name(reg.patient),
            "patient_number": getattr(reg.patient, "patient_number", "-"),
            "number": _registration_number_label(reg),
            "remark": reg.admission_remark or "",
            "requested_by": _user_display_name(reg.admission_requested_by),
            "requested_at": (
                reg.admission_requested_at.strftime("%d %b %Y, %I:%M %p")
                if reg.admission_requested_at else "-"
            ),
            "priority": _admission_priority_class(reg.priority),
        })
    return data


@login_required
@require_POST
def admit_patient_request(request, registration_id):
    """Today's Appointment page — 'Admit' button next to Complete Consultation."""

    medical_staff = getattr(request.user, "medical_staff_profile", None)

    if not medical_staff:
        return JsonResponse(
            {"success": False, "message": "Medical staff profile not found."},
            status=403,
        )

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"success": False, "message": "Invalid JSON request."}, status=400
        )

    registration = get_object_or_404(
        PatientRegistration.objects.select_related(
            "patient", "appointment", "shift_assignment__medical_staff"
        ),
        id=registration_id,
    )

    if (
        not registration.shift_assignment
        or registration.shift_assignment.medical_staff != medical_staff
    ):
        return JsonResponse(
            {"success": False, "message": "This patient is not assigned to you."},
            status=403,
        )

    if registration.status not in ("IN_PROGRESS", "COMPLETED"):
        return JsonResponse(
            {
                "success": False,
                "message": "Patient must be checked in before requesting admission.",
            },
            status=400,
        )

    if registration.admission_status != "NOT_REQUESTED":
        return JsonResponse(
            {
                "success": False,
                "message": "Admission has already been requested for this patient.",
            },
            status=400,
        )

    remark = (data.get("remark") or "").strip()

    registration.admission_status = "REQUESTED"
    registration.admission_remark = remark
    registration.admission_requested_by = request.user
    registration.admission_requested_at = timezone.localtime()

    registration.save(update_fields=[
        "admission_status", "admission_remark",
        "admission_requested_by", "admission_requested_at", "updated_at",
    ])

    counts = get_today_registration_counts(medical_staff)
    return JsonResponse({
        "success": True,
        "message": "Admission request sent to Rooms.",
        "admission_status": "REQUESTED",
        "counts": counts,
    })



@login_required
def rooms_page(request):

    medical_staff = getattr(request.user, "medical_staff_profile", None)

    if not medical_staff:
        return HttpResponseForbidden("Medical staff profile not found.")

    hospital = medical_staff.hospital

    if not hospital:
        return HttpResponseForbidden("No hospital assigned to this user.")

    building = hospital.hospital_building  

    floors = (
        building.floors
        .prefetch_related("rooms")
        .order_by("floor_number")
        if building else Floor.objects.none()
    )

    status_counts, total_rooms = _room_status_counts(building)  

    context = {
        "active_sb": "rooms",
        "hospital": hospital,
        "building": building,
        "floors": floors,
        "total_floors": floors.count() if building else 0,
        "total_rooms": total_rooms,
        "status_counts": status_counts,
        "admission_requests": _serialize_admission_requests(hospital),
    }

    return render(request, "swetha/rooms.html", context)

@login_required
@require_GET
def admission_requests_list(request):

    medical_staff = getattr(request.user, "medical_staff_profile", None)

    if not medical_staff or not medical_staff.hospital:
        return JsonResponse(
            {"success": False, "message": "No hospital assigned."}, status=403
        )

    return JsonResponse({
        "success": True,
        "requests": _serialize_admission_requests(medical_staff.hospital),
    })


@login_required
@require_POST
def admit_patient_to_room(request):

    medical_staff = getattr(request.user, "medical_staff_profile", None)
    hospital = medical_staff.hospital if medical_staff else None

    if not hospital:
        return JsonResponse(
            {"success": False, "message": "No hospital assigned."}, status=403
        )

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"success": False, "message": "Invalid JSON request."}, status=400
        )

    registration_id = data.get("registration_id")
    room_id = data.get("room_id")

    if not registration_id or not room_id:
        return JsonResponse(
            {"success": False, "message": "Registration and room are required."},
            status=400,
        )

    registration = get_object_or_404(
        PatientRegistration, id=registration_id, shift_assignment__medical_staff__hospital=hospital
    )
    # room = get_object_or_404(Room, id=room_id, floor__building__hospital=hospital)
    building = medical_staff.hospital.hospital_building if medical_staff.hospital else None
    room = get_object_or_404(Room, id=room_id, floor__building=building)
    
    if registration.admission_status != "REQUESTED":
        return JsonResponse(
            {"success": False, "message": "This admission request is no longer pending."},
            status=400,
        )

    if room.status != "AVAILABLE":
        return JsonResponse(
            {"success": False, "message": "Selected room is no longer available."},
            status=400,
        )

    with transaction.atomic():
        room.status = "OCCUPIED"
        room.save(update_fields=["status"])

        registration.admission_status = "ADMITTED"
        registration.assigned_room = room
        registration.admitted_at = timezone.localtime()
        registration.admitted_by = request.user
        registration.save(update_fields=[
            "admission_status", "assigned_room",
            "admitted_at", "admitted_by", "updated_at",
        ])

        if registration.appointment:
            registration.appointment.status = "ADMITTED"
            registration.appointment.save(update_fields=["status", "updated_at"])

    status_counts, total_rooms = _room_status_counts(building)

    return JsonResponse({
        "success": True,
        "message": "Patient admitted successfully.",
        "registration_id": registration.id,
        "room_id": room.id,
        "status_counts": status_counts,
        "total_rooms": total_rooms,
    })


@login_required
@require_GET
def room_occupant_details(request, room_id):

    medical_staff = getattr(request.user, "medical_staff_profile", None)
    hospital = medical_staff.hospital if medical_staff else None

    if not hospital:
        return JsonResponse(
            {"success": False, "message": "No hospital assigned."}, status=403
        )

    # room = get_object_or_404(Room, id=room_id, floor__building__hospital=hospital)
    building = hospital.hospital_building
    room = get_object_or_404(Room, id=room_id, floor__building=building)

    registration = (
        PatientRegistration.objects
        .filter(assigned_room=room, admission_status="ADMITTED")
        .select_related("patient", "appointment", "admitted_by")
        .order_by("-admitted_at")
        .first()
    )

    if not registration:
        return JsonResponse(
            {"success": False, "message": "No patient found for this room."},
            status=404,
        )

    checkup_notes = [
        {
            "id": note.id,
            "note": note.note,
            "created_by": _user_display_name(note.created_by),
            "created_at": timezone.localtime(note.created_at).strftime("%d %b %Y, %I:%M %p"),
        }
        for note in registration.checkup_notes.select_related("created_by").all()
    ]

    return JsonResponse({
        "success": True,
        "occupant": {
            "registration_id": registration.id,
            "room_number": room.room_number,
            "room_name": room.room_name,
            "floor_name": str(room.floor),
            "patient_name": _registration_patient_name(registration.patient),
            "patient_number": getattr(registration.patient, "patient_number", "-"),
            "number": _registration_number_label(registration),
            "remark": registration.admission_remark or "",
            "admitted_at": (
                registration.admitted_at.strftime("%d %b %Y, %I:%M %p")
                if registration.admitted_at else "-"
            ),
            "admitted_by": _user_display_name(registration.admitted_by),
            "checkup_notes": checkup_notes,
        },
    })

@login_required
@require_POST
def save_room_checkup(request, registration_id):

    medical_staff = getattr(request.user, "medical_staff_profile", None)
    hospital = medical_staff.hospital if medical_staff else None

    if not hospital:
        return JsonResponse(
            {"success": False, "message": "No hospital assigned."}, status=403
        )

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"success": False, "message": "Invalid JSON request."}, status=400
        )

    note_text = (data.get("note") or "").strip()

    if not note_text:
        return JsonResponse(
            {"success": False, "message": "Checkup remark cannot be empty."},
            status=400,
        )

    building = hospital.hospital_building if hospital else None

    registration = get_object_or_404(
        PatientRegistration,
        id=registration_id,
        assigned_room__floor__building=building,
        admission_status="ADMITTED",
    )

    note = RoomCheckupNote.objects.create(
        registration=registration,
        note=note_text,
        created_by=request.user,
    )

    return JsonResponse({
        "success": True,
        "message": "Checkup remark saved.",
        "note": {
            "id": note.id,
            "note": note.note,
            "created_by": _user_display_name(note.created_by),
            "created_at": timezone.localtime(note.created_at).strftime("%d %b %Y, %I:%M %p"),
        },
    })

########################## kali code end  #####################################