from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from Medical.models import MedicalDepartment, AthleteMedicalProfile, InjuryRecord

from .forms import *
import logging
from django.db import transaction
from PermissionAccess.decorators import require_permission, require_page_access
import json
from datetime import timedelta

####################### MEDICAL VIEW START ##########################

@require_page_access("medical_department_page", shared_with_user_roles=True)
@login_required
def department(request):
    return render(request, "Jack/department.html")

@require_permission("medicaldepartment_create")
@login_required
def department_create(request):
    if request.method == 'POST':
        form = MedicalDepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department created successfully!')
            return redirect('Medical:medical_department')
    else:
        form = MedicalDepartmentForm()

    return render(request, "Jack/department_create.html", {'form': form})

@login_required
def department_json(request):

    department = MedicalDepartment.objects.all()

    data = []

    for dep in department:
        data.append({
            'uuid': dep.uuid,
            'department_code': dep.department_code,
            'department_name': dep.department_name,
            'short_name': dep.short_name,
            'department_type': dep.department_type,
            'description': dep.description,
            'location': dep.location,
            'email': dep.email,
            'phone': dep.phone,
            'opening_time': dep.opening_time,
            'closing_time': dep.closing_time,
            'is_emergency': dep.is_emergency,
            'is_active': dep.is_active,
        })

    return JsonResponse({
        'departments': data
    })

@require_permission("medicaldepartment_update")
@login_required
def department_edit(request, uuid):

    department = get_object_or_404(
        MedicalDepartment,
        uuid=uuid
    )

    if request.method == 'POST':
        form = MedicalDepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department updated successfully!')
            return redirect('Medical:medical_department')
    else:
        form = MedicalDepartmentForm(instance=department)

    return render(request, "Jack/department_create.html", {'form': form})

@require_page_access("athlete_medical_profile_page", shared_with_user_roles=True)
@login_required
def athlete_medical_profile(request):
    return render(request, "Jack/athlete_medical_profile.html")

@login_required
def athlete_medical_profile_json(request):
 
    athlete_medical_profile = AthleteMedicalProfile.objects.all()
 
    data = []
 
    for amp in athlete_medical_profile:
        data.append({
            'uuid': amp.uuid,
            'athlete': amp.athlete.student.get_full_name(),
            'athlete_profile': amp.athlete.student.profile_photo.url if amp.athlete.student.profile_photo else None,
            'athlete_medical_id': amp.athlete_medical_id,
            "blood_group": (
                    amp.patient_profile.blood_group
                    if amp.patient_profile
                    else "-"
                ),
            'primary_sport': amp.primary_sport.sport_name if amp.primary_sport else None,
            'medical_clearance_status': amp.medical_clearance_status,
            'fitness_level': amp.fitness_level,
            'injury_risk': amp.injury_risk,
            'is_active': amp.is_active
        })
 
    return JsonResponse({
        'athlete_medical_profile': data
    })

@require_page_access("athlete_medical_profile_view_page", shared_with_user_roles=True)
@login_required
def athlete_medical_profile_view(request, uuid):

    athlete = get_object_or_404(
        AthleteMedicalProfile,
        uuid=uuid
    )

    context = {
        'profile': athlete
    }

    return render(request, "Jack/athlete_medical_profile_view.html", context)

@require_page_access("athlete_injury_record_page", shared_with_user_roles=True)
@login_required
def athlete_injury_record(request, uuid):

    injuries = InjuryRecord.objects.filter(
        medical_profile__uuid=uuid
    )

    context = {
        'injury': injuries
    }

    return render(request, "Jack/athlete_injury_record.html", context)

########### MEDICAL DASHBOARD VIEW'S START ############

# @login_required
# def patients(request):

#     context = {
#         "active_sb": "patients"
#     }

#     return render(request, "Jack/patients.html", context)


########### SWETHA'S  VIEW'S START ############

# from django.http import JsonResponse
# from django.contrib.auth.decorators import login_required
# from Medical.models import PatientProfile, AthleteMedicalProfile
# from django.utils import timezone
# from datetime import timedelta
# today = timezone.now().date()

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from Medical.models import PatientProfile, AthleteMedicalProfile
from Admin.models import Athletic
from django.utils import timezone


today = timezone.now().date()


@login_required
def patients(request):

    context = {
        "active_sb": "patients"
    }

    return render(request, "Jack/patients.html", context)


@login_required
def patient_list_api(request):
    athletes = (
        Athletic.objects
        .select_related(
            "student",
            "team",
        )
        .prefetch_related(
            "individual_sports"
        )
    )
    athlete_map = {
        athlete.student_id: athlete
        for athlete in athletes
    }

    patients = (
        PatientProfile.objects
        .select_related(
            "student__user",
            "faculty__user",
            "staff__user",
            "admin",
        )
        .all()
    )


    data = []

    for patient in patients:
        if patient.student:

            user = patient.student.user

            person = {
                "first_name": user.first_name,
                "last_name": user.last_name,
            }

        elif patient.faculty:

            user = patient.faculty.user

            person = {
                "first_name": user.first_name,
                "last_name": user.last_name,
            }

        elif patient.staff:

            user = patient.staff.user

            person = {
                "first_name": user.first_name,
                "last_name": user.last_name,
            }

        elif patient.admin:

            user = patient.admin

            person = {
                "first_name": user.first_name,
                "last_name": user.last_name,
            }

        else:

            user = None
            person = None

        athlete = None

        if patient.student:

            athlete = athlete_map.get(
                patient.student.user_id
            )

        elif patient.faculty:

            athlete = athlete_map.get(
                patient.faculty.user_id
            )

        elif patient.staff:

            athlete = athlete_map.get(
                patient.staff.user_id
            )

        athlete_medical_profile = None

        if athlete:

            athlete_medical_profile = (
                AthleteMedicalProfile.objects
                .filter(athlete=athlete)
                .first()
            )

        individual_sports = []

        if athlete:

            individual_sports = list(
                athlete.individual_sports.values_list(
                    "sport_name",
                    flat=True
                )
            )

        avatar = None

        if user and user.profile_photo:

            avatar = request.build_absolute_uri(
                user.profile_photo.url
            )

        athlete_data = None

        if athlete:

            athlete_data = {

                "athlete_id": athlete.athlete_id,

                "medical_id": (
                    athlete_medical_profile.athlete_medical_id
                    if athlete_medical_profile
                    else None
                ),

                "team": (
                    athlete.team.team_name
                    if athlete.team
                    else None
                ),

                "individual_sports": individual_sports,
            }

        data.append({

            "id": patient.id,

            "uuid": str(patient.uuid),

            "patient_number": patient.patient_number,

            "patient_type": patient.patient_type,

            "student": (
                person
                if patient.student
                else None
            ),

            "faculty": (
                person
                if patient.faculty
                else None
            ),

            "staff": (
                person
                if patient.staff
                else None
            ),

            "admin": (
                person
                if patient.admin
                else None
            ),

            "visitor_name": patient.visitor_name,

            "is_athlete": athlete is not None,

            "athlete": athlete_data,

            "blood_group": patient.blood_group,

            "allergies": patient.allergies,

            "chronic_conditions": (
                patient.chronic_conditions
            ),

            "remarks": patient.remarks,

            "phone": (

                patient.student.user.mobile_number
                if patient.student

                else patient.faculty.phone
                if patient.faculty

                else patient.staff.office_phone
                if patient.staff

                else patient.admin.mobile_number
                if patient.admin

                else patient.visitor_phone
                if patient.visitor_name

                else None
            ),

            "email": (

                patient.student.university_email
                if patient.student

                else patient.faculty.email
                if patient.faculty

                else patient.staff.work_email
                if patient.staff

                else patient.admin.email
                if patient.admin

                else patient.visitor_email
                if patient.visitor_name

                else None
            ),


            "avatar": avatar,

            "is_active": patient.is_active,
        })

    current_month_start = today.replace(day=1)

    if current_month_start.month == 1:

        previous_month_start = current_month_start.replace(
            year=current_month_start.year - 1,
            month=12
        )

    else:

        previous_month_start = current_month_start.replace(
            month=current_month_start.month - 1
        )

    current_count = PatientProfile.objects.filter(
        created_at__date__gte=current_month_start
    ).count()

    previous_count = PatientProfile.objects.filter(
        created_at__date__gte=previous_month_start,
        created_at__date__lt=current_month_start
    ).count()

    growth = (
        100
        if previous_count == 0 and current_count

        else 0
        if previous_count == 0

        else round(
            ((current_count - previous_count) / previous_count) * 100
        )
    )


    student_current = PatientProfile.objects.filter(
        patient_type="STUDENT",
        created_at__date__gte=current_month_start
    ).count()

    student_previous = PatientProfile.objects.filter(
        patient_type="STUDENT",
        created_at__date__gte=previous_month_start,
        created_at__date__lt=current_month_start
    ).count()

    student_growth = (
        100
        if student_previous == 0 and student_current

        else 0
        if student_previous == 0

        else round(
            ((student_current - student_previous) / student_previous) * 100
        )
    )

    faculty_current = PatientProfile.objects.filter(
        patient_type="FACULTY",
        created_at__date__gte=current_month_start
    ).count()

    faculty_previous = PatientProfile.objects.filter(
        patient_type="FACULTY",
        created_at__date__gte=previous_month_start,
        created_at__date__lt=current_month_start
    ).count()

    faculty_growth = (
        100
        if faculty_previous == 0 and faculty_current

        else 0
        if faculty_previous == 0

        else round(
            ((faculty_current - faculty_previous) / faculty_previous) * 100
        )
    )


    staff_current = PatientProfile.objects.filter(
        patient_type="STAFF",
        created_at__date__gte=current_month_start
    ).count()

    staff_previous = PatientProfile.objects.filter(
        patient_type="STAFF",
        created_at__date__gte=previous_month_start,
        created_at__date__lt=current_month_start
    ).count()

    staff_growth = (
        100
        if staff_previous == 0 and staff_current

        else 0
        if staff_previous == 0

        else round(
            ((staff_current - staff_previous) / staff_previous) * 100
        )
    )

    return JsonResponse({

        "patients": data,

        "stats": {

            "growth": growth,

            "student_growth": student_growth,

            "faculty_growth": faculty_growth,

            "staff_growth": staff_growth,
        }
    })

########### SWETHA'S VIEW'S EMD ############

########### MEDICAL DASHBOARD VIEW'S END ############

@login_required
def view_patient(request, uuid):

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
            "total_visits": 0,
            "total_prescriptions": 0,
            "last_visit": None,
        }

    # Get linked profile data if not a visitor
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

    # Get statistics
    # context["total_visits"] = Visit.objects.filter(patient=patient).count()
    # context["total_prescriptions"] = Prescription.objects.filter(patient=patient).count()
    
    # last_visit = Visit.objects.filter(patient=patient).order_by('-visit_date').first()
    # if last_visit:
    #     context["last_visit"] = last_visit.visit_date.strftime("%b %d, %Y")
    
    return render(request, "Jack/view_patient.html", context)


@login_required
def leave(request):

    context = {
        "active_sb": "leave"
    }

    return render(request, "Jack/leave.html", context)


logger = logging.getLogger(__name__)

@login_required
def apply_leave(request):

    try:
        medical_staff = MedicalStaffProfile.objects.get(user=request.user)
    except MedicalStaffProfile.DoesNotExist:
        messages.error(request, 'Medical staff profile not found. Please contact administrator.')
        return redirect('Medical:leave')
    
    if request.method == 'POST':
        form = LeaveApplicationForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    leave_application = form.save(commit=False)
                    leave_application.medical_staff = medical_staff  
                    leave_application.user = request.user  
                    leave_application.save()
                    
                    messages.success(request, 
                        'Your leave request has been submitted successfully!')
                    
                    return redirect('Medical:leave')
                    
            except Exception as e:
                logger.error(f"Error saving leave application: {str(e)}")
                messages.error(request, 
                    'An error occurred while submitting your leave request. Please try again.')
        else:
            logger.debug(f"Form errors: {form.errors}")
            
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    
    else:
        initial_data = {}
        
        if request.GET.get('type') == 'PERMISSION':
            initial_data['leave_type'] = 'PERMISSION'
            initial_data['start_date'] = timezone.now().date()
            initial_data['end_date'] = timezone.now().date()
        
        form = LeaveApplicationForm(initial=initial_data)
    
    context = {
        'form': form,
        'medical_staff': medical_staff,
        'active_sb': 'leave',
    }
    return render(request, 'Jack/apply_leave.html', context)


@login_required
def leave_list(request):

    medical_staff = get_object_or_404(
        MedicalStaffProfile,
        user=request.user
    )

    leaves = MedicalStaffLeave.objects.filter(
        medical_staff=medical_staff
    )

    return JsonResponse({
        "success": True,
        "leaves": list(leaves.values())
    })


@login_required
def cancel_leave(request, leave_id):
    try:
        medical_staff = MedicalStaffProfile.objects.get(
            user=request.user
        )
    except MedicalStaffProfile.DoesNotExist:
        messages.error(
            request,
            'Medical staff profile not found. Please contact administrator.'
        )
        return redirect('Medical:leave')

    try:
        leave_application = MedicalStaffLeave.objects.get(
            uuid=leave_id,
            medical_staff=medical_staff
        )
    except MedicalStaffLeave.DoesNotExist:
        messages.error(
            request,
            'Leave application not found.'
        )
        return redirect('Medical:leave')

    if leave_application.status != 'PENDING':
        messages.error(
            request,
            'Only pending leave applications can be cancelled.'
        )
        return redirect('Medical:leave')

    if request.method == 'POST':
        leave_application.status = 'CANCELLED'
        leave_application.save(
            update_fields=['status', 'updated_at']
        )

        messages.success(
            request,
            'Your leave request has been cancelled successfully.'
        )

        return redirect('Medical:leave')

    messages.error(
        request,
        'Invalid request.'
    )
    return redirect('Medical:leave')


@login_required
def profile(request):

    staff = get_object_or_404(
        MedicalStaffProfile.objects
        .select_related(
            "user",
            "user__role",
            "department",
            "hospital",
            "role",
        ),
        user=request.user,
    )

    context = {
        "active_sb": "profile",
        "staff": staff,
    }
    
    return render(request, "Jack/profile.html", context)

####################### MEDICAL VIEW END ############################


####################### MEDICAL DASHBOARD OVERVIEW START ############################

from django.db.models import Count, Q


ROLE_META = {
    "DOCTOR": {"label": "Doctor"}, "NURSE": {"label": "Nurse"}, "LAB": {"label": "Lab Technician"},
    "PHYSIO": {"label": "Physiotherapist"}, "PHARMACY": {"label": "Pharmacist"},
    "FRONT_DESK": {"label": "Front Desk"}, "DIRECTOR": {"label": "Director"}, "OTHER": {"label": "Staff"},
}


def _card(id, icon, color, label, value, suffix=None):
    card = {"id": id, "icon": icon, "color": color, "label": label, "value": value}
    if suffix:
        card["suffix"] = suffix
    return card

@login_required
def medical_dashboard_data(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"error": "Forbidden"}, status=403)

    staff = getattr(request.user, "medical_staff_profile", None)
    if staff is None:
        return JsonResponse({"error": "No medical staff profile for this user."}, status=404)

    category = staff.role.category if staff.role_id else "OTHER"
    handler = ROLE_HANDLERS.get(category, _other_overview)

    today = timezone.localdate()
    week_start = today - timedelta(days=6)  # only used for the weekly TREND chart, not cards

    payload = handler(staff, today, week_start)
    payload["role"] = {
        "category": category,
        "label": ROLE_META.get(category, ROLE_META["OTHER"])["label"],
        "role_name": staff.role.name if staff.role_id else "Staff",
        "staff_name": str(staff.user),
        "department": staff.department.department_name if staff.department_id else "—",
    }
    return JsonResponse(payload)


# ---------------- shared chart helpers ---------------- #

def _weekly_trend(qs, today, date_field, title="Weekly Trend"):
    labels, data = [], []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime("%a"))
        data.append(qs.filter(**{date_field: day}).count())
    return {"title": title, "labels": labels, "data": data}


def _dist(qs, field, choice_map=None, title=""):
    counts = qs.exclude(**{field: ""}).values(field).annotate(count=Count("id")) if _is_charfield_blankable(field) \
        else qs.values(field).annotate(count=Count("id"))
    labels, data = [], []
    for r in counts:
        key = r[field]
        labels.append((choice_map or {}).get(key, key) if key else "—")
        data.append(r["count"])
    return {"title": title, "labels": labels, "data": data}


def _is_charfield_blankable(field):
    return False  # kept simple; callers pre-filter with .exclude() where needed


def _appointment_timeline(appts_qs):
    return [
        {
            "time": a.appointment_time.strftime("%H:%M") if a.appointment_time else "",
            "title": a.get_status_display(),
            "desc": f"{a.patient.patient_name if a.patient else 'Unknown'} · {a.service}",
        }
        for a in appts_qs.select_related("patient").order_by("-appointment_date", "-appointment_time")[:6]
    ]


def _athlete_status_breakdown(athletes_qs):
    status_map = dict(AthleteMedicalProfile.MEDICAL_CLEARANCE_STATUS)
    counts = athletes_qs.exclude(medical_clearance_status="NOT SELECTED").values(
        "medical_clearance_status"
    ).annotate(count=Count("id"))
    return [{"label": status_map.get(r["medical_clearance_status"], r["medical_clearance_status"]), "count": r["count"]} for r in counts]


def _status_dist(appts_qs):
    status_map = dict(Appointment.STATUS_CHOICES)
    counts = appts_qs.values("status").annotate(count=Count("id"))
    return {"title": "Appointment Status", "labels": [status_map.get(r["status"], r["status"]) for r in counts], "data": [r["count"] for r in counts]}


def _priority_dist(appts_qs):
    priority_map = dict(Appointment.PRIORITY_CHOICES)
    counts = appts_qs.values("priority").annotate(count=Count("id"))
    return {"title": "Priority Distribution", "labels": [priority_map.get(r["priority"], r["priority"]) for r in counts], "data": [r["count"] for r in counts]}


# ---------------- DOCTOR ---------------- #

def _doctor_overview(staff, today, week_start):
    appts_qs = Appointment.objects.filter(medical_staff=staff)
    injuries_qs = InjuryRecord.objects.filter(treated_by=staff)
    athletes_qs = AthleteMedicalProfile.objects.filter(team_physician=staff)
    tests_qs = LaboratoryTest.objects.filter(requested_by=staff)

    total_patients = appts_qs.filter(patient__isnull=False).values("patient").distinct().count()

    stats = [
        _card("patients", "fa-user-injured", "primary", "Total Patients", total_patients),
        _card("appointments", "fa-calendar-check", "secondary", "Total Appointments", appts_qs.count()),
        _card("pending", "fa-hourglass-half", "warning", "Pending Appointments", appts_qs.filter(status="PENDING").count()),
        _card("completed", "fa-circle-check", "success", "Completed Appointments", appts_qs.filter(status="COMPLETED").count()),
        _card("urgent", "fa-triangle-exclamation", "danger", "High/Emergency Priority", appts_qs.filter(priority__in=["HIGH", "EMERGENCY"]).count()),
        _card("athletes", "fa-running", "info", "Athletes Under Care", athletes_qs.count()),
        _card("injuries", "fa-bone", "orange", "Total Injuries Treated", injuries_qs.count()),
        _card("lab_requests", "fa-flask", "teal", "Total Lab Tests Requested", tests_qs.count()),
    ]

    injury_type_counts = injuries_qs.values("injury_type").annotate(count=Count("id"))
    patient_type_map = dict(__import__("Medical.models", fromlist=["PatientProfile"]).PatientProfile.PATIENT_TYPES)
    patient_type_counts = appts_qs.filter(patient__isnull=False).values("patient__patient_type").annotate(count=Count("id"))

    return {
        "stat_cards": stats,
        "chart_one": _weekly_trend(appts_qs, today, "appointment_date", "Weekly Appointments"),
        "chart_two": {"type": "bar", **_status_dist(appts_qs)},
        "chart_three": {"type": "doughnut", "title": "Patient Types",
                         "labels": [patient_type_map.get(r["patient__patient_type"], r["patient__patient_type"]) for r in patient_type_counts],
                         "data": [r["count"] for r in patient_type_counts]},
        "chart_four": {"type": "pie", "title": "Injury Types",
                       "labels": [r["injury_type"] for r in injury_type_counts],
                       "data": [r["count"] for r in injury_type_counts]},
        "timeline": _appointment_timeline(appts_qs),
        "side_panel": {"title": "Athlete Clearance Status", "type": "status_list", "items": _athlete_status_breakdown(athletes_qs)},
    }


# ---------------- NURSE ---------------- #

def _nurse_overview(staff, today, week_start):
    shifts_qs = ShiftAssignment.objects.filter(medical_staff=staff)
    leaves_qs = MedicalStaffLeave.objects.filter(medical_staff=staff)

    todays_shift = shifts_qs.filter(
        assignment_start_date__lte=today, assignment_end_date__gte=today
    ).select_related("shift", "room").first()

    upcoming_shifts = shifts_qs.filter(assignment_start_date__gt=today).count()
    past_shifts = shifts_qs.filter(assignment_end_date__lt=today).count()
    distinct_rooms = shifts_qs.exclude(room__isnull=True).values("room").distinct().count()

    stats = [
        _card("total_shifts", "fa-calendar-days", "primary", "Total Shifts Assigned", shifts_qs.count()),
        _card("upcoming_shifts", "fa-forward", "secondary", "Upcoming Shifts", upcoming_shifts),
        _card("past_shifts", "fa-calendar-check", "success", "Completed Shifts", past_shifts),
        _card("on_shift_today", "fa-user-clock", "info", "On Shift Today", "Yes" if todays_shift else "No"),
        _card("rooms_covered", "fa-door-open", "teal", "Rooms Covered", distinct_rooms),
        _card("total_leaves", "fa-plane-departure", "orange", "Total Leave Requests", leaves_qs.count()),
        _card("pending_leaves", "fa-hourglass-half", "warning", "Pending Leave Requests", leaves_qs.filter(status="PENDING").count()),
        _card("approved_leaves", "fa-circle-check", "danger", "Approved Leave Requests", leaves_qs.filter(status="APPROVED").count()),
    ]

    labels, data = [], []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime("%a"))
        data.append(shifts_qs.filter(assignment_start_date__lte=day, assignment_end_date__gte=day).count())
    chart_one = {"title": "Shift Coverage (7 days)", "labels": labels, "data": data}

    shift_type_map = dict(Shift.SHIFT_LABEL_CHOICES)
    shift_type_counts = shifts_qs.values("shift__shift_type").annotate(count=Count("id"))
    chart_two = {
        "type": "bar", "title": "Shift Type Breakdown",
        "labels": [shift_type_map.get(r["shift__shift_type"], r["shift__shift_type"]) for r in shift_type_counts],
        "data": [r["count"] for r in shift_type_counts],
    }

    leave_type_map = dict(MedicalStaffLeave.LEAVE_TYPES)
    leave_type_counts = leaves_qs.values("leave_type").annotate(count=Count("id"))
    chart_three = {
        "type": "doughnut", "title": "Leave Type Breakdown",
        "labels": [leave_type_map.get(r["leave_type"], r["leave_type"]) for r in leave_type_counts],
        "data": [r["count"] for r in leave_type_counts],
    }

    leave_status_map = dict(MedicalStaffLeave.STATUS_CHOICES)
    leave_status_counts = leaves_qs.values("status").annotate(count=Count("id"))
    chart_four = {
        "type": "pie", "title": "Leave Status",
        "labels": [leave_status_map.get(r["status"], r["status"]) for r in leave_status_counts],
        "data": [r["count"] for r in leave_status_counts],
    }

    timeline = [
        {
            "time": s.assignment_start_date.strftime("%b %d"),
            "title": s.shift.shift_label,
            "desc": f"{s.shift.department.department_name} · Room: {s.room.name if s.room else '—'}",
        }
        for s in shifts_qs.select_related("shift__department", "room").order_by("-assignment_start_date")[:6]
    ]

    return {
        "stat_cards": stats,
        "chart_one": chart_one,
        "chart_two": chart_two,
        "chart_three": chart_three,
        "chart_four": chart_four,
        "timeline": timeline,
        "side_panel": {
            "title": "Today's Shift",
            "type": "text",
            "items": [{
                "label": todays_shift.shift.shift_label if todays_shift else "No shift assigned today",
                "count": f"{todays_shift.shift.start_time.strftime('%H:%M')}–{todays_shift.shift.end_time.strftime('%H:%M')} · Room: {todays_shift.room.name if todays_shift.room else '—'}" if todays_shift else "",
            }],
        },
    }


# ---------------- LAB ---------------- #

def _lab_overview(staff, today, week_start):
    tests_qs = LaboratoryTest.objects.filter(Q(requested_by=staff) | Q(performed_by=staff))
    performed_qs = tests_qs.filter(performed_by=staff)

    stats = [
        _card("performed", "fa-flask", "primary", "Total Tests Performed", performed_qs.count()),
        _card("requested", "fa-file-medical", "secondary", "Total Tests Requested", tests_qs.filter(requested_by=staff).count()),
        _card("pending", "fa-hourglass-half", "warning", "Pending Tests", tests_qs.filter(status__in=["REQUESTED", "COLLECTED", "PROCESSING"]).count()),
        _card("completed", "fa-circle-check", "success", "Completed Tests", tests_qs.filter(status="COMPLETED").count()),
        _card("critical", "fa-triangle-exclamation", "danger", "Critical Results", tests_qs.filter(result_status="CRITICAL").count()),
        _card("abnormal", "fa-notes-medical", "orange", "Abnormal Results", tests_qs.filter(result_status="ABNORMAL").count()),
        _card("blood", "fa-droplet", "info", "Total Blood Tests", tests_qs.filter(test_category="BLOOD").count()),
        _card("imaging", "fa-x-ray", "teal", "Total Imaging Tests", tests_qs.filter(test_category__in=["XRAY", "MRI", "CT_SCAN", "ULTRASOUND"]).count()),
    ]

    category_map = dict(LaboratoryTest.TEST_CATEGORIES)
    cat_counts = tests_qs.values("test_category").annotate(count=Count("id"))
    sample_map = dict(LaboratoryTest.SAMPLE_TYPES)
    sample_counts = tests_qs.values("sample_type").annotate(count=Count("id"))
    result_counts = tests_qs.exclude(result_status="").values("result_status").annotate(count=Count("id"))

    timeline = [
        {"time": t.test_date.strftime("%b %d") if t.test_date else "—", "title": t.test_name,
         "desc": f"{t.patient.patient_name} · {t.get_status_display()}"}
        for t in tests_qs.select_related("patient").order_by("-requested_date")[:6]
    ]

    return {
        "stat_cards": stats,
        "chart_one": _weekly_trend(tests_qs, today, "test_date", "Weekly Tests Run"),
        "chart_two": {"type": "bar", "title": "Test Categories",
                      "labels": [category_map.get(r["test_category"], r["test_category"]) for r in cat_counts],
                      "data": [r["count"] for r in cat_counts]},
        "chart_three": {"type": "doughnut", "title": "Result Status",
                        "labels": [r["result_status"] for r in result_counts], "data": [r["count"] for r in result_counts]},
        "chart_four": {"type": "pie", "title": "Sample Types",
                       "labels": [sample_map.get(r["sample_type"], r["sample_type"]) for r in sample_counts],
                       "data": [r["count"] for r in sample_counts]},
        "timeline": timeline,
        "side_panel": {"title": "Result Status Breakdown", "type": "status_list",
                       "items": [{"label": r["result_status"], "count": r["count"]} for r in result_counts]},
    }


# ---------------- PHYSIO ---------------- #

def _physio_overview(staff, today, week_start):
    athletes_qs = AthleteMedicalProfile.objects.filter(physiotherapist=staff)
    injuries_qs = InjuryRecord.objects.filter(medical_profile__physiotherapist=staff)
    appts_qs = Appointment.objects.filter(medical_staff=staff)

    stats = [
        _card("athletes", "fa-running", "primary", "Athletes Assigned", athletes_qs.count()),
        _card("total_injuries", "fa-bone", "secondary", "Total Injuries Handled", injuries_qs.count()),
        _card("rehab", "fa-dumbbell", "warning", "In Rehabilitation", injuries_qs.filter(injury_status="REHABILITATION").count()),
        _card("recovering", "fa-heart-pulse", "info", "Recovering", injuries_qs.filter(injury_status="RECOVERING").count()),
        _card("active", "fa-triangle-exclamation", "danger", "Active Injuries", injuries_qs.filter(injury_status="ACTIVE").count()),
        _card("returned", "fa-flag-checkered", "success", "Returned to Sport (Total)", injuries_qs.filter(injury_status="RETURNED").count()),
        _card("high_risk", "fa-radiation", "orange", "High Injury Risk Athletes", athletes_qs.filter(injury_risk="HIGH").count()),
        _card("sessions", "fa-calendar-check", "teal", "Total Sessions", appts_qs.count()),
    ]

    risk_map = dict(AthleteMedicalProfile.INJURY_RISK)
    risk_counts = athletes_qs.exclude(injury_risk="NOT SELECTED").values("injury_risk").annotate(count=Count("id"))
    clearance_map = dict(AthleteMedicalProfile.MEDICAL_CLEARANCE_STATUS)
    clearance_counts = athletes_qs.exclude(medical_clearance_status="NOT SELECTED").values("medical_clearance_status").annotate(count=Count("id"))
    injury_status_map = dict(InjuryRecord.INJURY_STATUS)
    injury_status_counts = injuries_qs.values("injury_status").annotate(count=Count("id"))

    timeline = [
        {"time": i.injury_date.strftime("%b %d"), "title": i.injury_title,
         "desc": f"{i.medical_profile.athlete} · {i.get_injury_status_display()}"}
        for i in injuries_qs.select_related("medical_profile__athlete").order_by("-injury_date")[:6]
    ]

    return {
        "stat_cards": stats,
        "chart_one": _weekly_trend(appts_qs, today, "appointment_date", "Weekly Sessions"),
        "chart_two": {"type": "bar", "title": "Injury Risk Distribution",
                      "labels": [risk_map.get(r["injury_risk"], r["injury_risk"]) for r in risk_counts],
                      "data": [r["count"] for r in risk_counts]},
        "chart_three": {"type": "doughnut", "title": "Clearance Status",
                        "labels": [clearance_map.get(r["medical_clearance_status"], r["medical_clearance_status"]) for r in clearance_counts],
                        "data": [r["count"] for r in clearance_counts]},
        "chart_four": {"type": "pie", "title": "Injury Status",
                       "labels": [injury_status_map.get(r["injury_status"], r["injury_status"]) for r in injury_status_counts],
                       "data": [r["count"] for r in injury_status_counts]},
        "timeline": timeline,
        "side_panel": {"title": "Athlete Clearance Status", "type": "status_list", "items": _athlete_status_breakdown(athletes_qs)},
    }


# ---------------- PHARMACY ---------------- #

def _pharmacy_overview(staff, today, week_start):
    dept = staff.department
    services_qs = MedicalService.objects.filter(department=dept) if dept else MedicalService.objects.none()
    appts_qs = Appointment.objects.filter(medical_staff__department=dept) if dept else Appointment.objects.none()

    stats = [
        _card("dept_services", "fa-pills", "primary", "Department Services", services_qs.count()),
        _card("total_appts", "fa-calendar", "secondary", "Total Dept. Appointments", appts_qs.count()),
        _card("pending", "fa-hourglass-half", "warning", "Pending Appointments", appts_qs.filter(status="PENDING").count()),
        _card("completed", "fa-circle-check", "success", "Completed Appointments", appts_qs.filter(status="COMPLETED").count()),
        _card("emergency_services", "fa-truck-medical", "danger", "Emergency Services", services_qs.filter(is_emergency_service=True).count()),
        _card("appt_required", "fa-calendar-check", "info", "Appointment-Required Services", services_qs.filter(requires_appointment=True).count()),
        _card("dispensing", "fa-circle-info", "orange", "Dispensing Records", "—", suffix="No model yet"),
        _card("stock_alerts", "fa-circle-info", "teal", "Stock Alerts", "—", suffix="No model yet"),
    ]

    category_map = dict(MedicalService.SERVICE_CATEGORIES)
    cat_counts = services_qs.values("service_category").annotate(count=Count("id"))

    return {
        "stat_cards": stats,
        "chart_one": _weekly_trend(appts_qs, today, "appointment_date", "Weekly Dept. Appointments"),
        "chart_two": {"type": "bar", "title": "Service Categories",
                      "labels": [category_map.get(r["service_category"], r["service_category"]) for r in cat_counts],
                      "data": [r["count"] for r in cat_counts]},
        "chart_three": {"type": "doughnut", **_status_dist(appts_qs)},
        "chart_four": {"type": "pie", **_priority_dist(appts_qs)},
        "timeline": [],
        "side_panel": {"title": "Note", "type": "text",
                       "items": [{"label": "No pharmacy/dispensing model exists yet — these cards fall back to department-level service and appointment data.", "count": ""}]},
    }


# ---------------- FRONT DESK ---------------- #

def _frontdesk_overview(staff, today, week_start):
    regs_qs = PatientRegistration.objects.filter(shift_assignment__medical_staff=staff)
    appts_qs = Appointment.objects.filter(hospital=staff.hospital) if staff.hospital_id else Appointment.objects.none()

    stats = [
        _card("total_regs", "fa-clipboard-list", "primary", "Total Registrations", regs_qs.count()),
        _card("waiting", "fa-hourglass-half", "warning", "Currently Waiting", regs_qs.filter(status="WAITING").count()),
        _card("completed_regs", "fa-circle-check", "success", "Completed Registrations", regs_qs.filter(status="COMPLETED").count()),
        _card("total_appts", "fa-calendar", "secondary", "Total Appointments (Hospital)", appts_qs.count()),
        _card("walk_ins", "fa-person-walking", "teal", "Total Walk-Ins", regs_qs.filter(registration_type="WALK_IN").count()),
        _card("cancelled", "fa-ban", "danger", "Cancelled Appointments", appts_qs.filter(status="CANCELLED").count()),
        _card("no_shows", "fa-user-slash", "orange", "Total No-Shows", appts_qs.filter(status="NOT_ARRIVED").count()),
        _card("confirmed", "fa-circle-check", "info", "Confirmed Upcoming", appts_qs.filter(status="CONFIRMED", appointment_date__gte=today).count()),
    ]

    reg_type_map = dict(PatientRegistration._meta.get_field("registration_type").choices)
    reg_type_counts = regs_qs.values("registration_type").annotate(count=Count("id"))
    reg_status_counts = regs_qs.values("status").annotate(count=Count("id"))

    timeline = [
        {"time": r.registration_time.strftime("%H:%M") if r.registration_time else "", "title": f"Registration {r.registration_number}",
         "desc": f"{r.patient.patient_name} · {r.get_status_display()}"}
        for r in regs_qs.select_related("patient").order_by("-registration_date", "-registration_time")[:6]
    ]

    return {
        "stat_cards": stats,
        "chart_one": _weekly_trend(regs_qs, today, "registration_date", "Weekly Registrations"),
        "chart_two": {"type": "bar", "title": "Registration Type",
                      "labels": [reg_type_map.get(r["registration_type"], r["registration_type"]) for r in reg_type_counts],
                      "data": [r["count"] for r in reg_type_counts]},
        "chart_three": {"type": "doughnut", "title": "Registration Status",
                        "labels": [r["status"] for r in reg_status_counts], "data": [r["count"] for r in reg_status_counts]},
        "chart_four": {"type": "pie", **_status_dist(appts_qs)},
        "timeline": timeline,
        "side_panel": {"title": "Queue Status", "type": "status_list",
                       "items": [{"label": r["status"], "count": r["count"]} for r in reg_status_counts]},
    }


# ---------------- DIRECTOR ---------------- #

def _director_overview(staff, today, week_start):
    if not staff.department_id:
        return _other_overview(staff, today, week_start)

    dept = staff.department
    dept_staff = dept.staff_members.all()
    appts_qs = Appointment.objects.filter(medical_staff__department=dept)
    camps_qs = HealthCamp.objects.filter(department=dept)
    pending_leaves = MedicalStaffLeave.objects.filter(medical_staff__department=dept, status="PENDING")
    services_qs = MedicalService.objects.filter(department=dept)

    stats = [
        _card("dept_staff", "fa-user-md", "primary", "Department Staff", dept_staff.count()),
        _card("active_staff", "fa-user-check", "success", "Active Staff", dept_staff.filter(status="ACTIVE").count()),
        _card("on_leave", "fa-plane-departure", "warning", "Staff On Leave", dept_staff.filter(status="ON_LEAVE").count()),
        _card("total_appts", "fa-calendar", "info", "Total Dept. Appointments", appts_qs.count()),
        _card("completed_appts", "fa-circle-check", "secondary", "Completed Appointments", appts_qs.filter(status="COMPLETED").count()),
        _card("pending_leaves", "fa-hourglass-half", "orange", "Pending Leave Approvals", pending_leaves.count()),
        _card("camps", "fa-campground", "teal", "Health Camps (Dept)", camps_qs.count()),
        _card("services", "fa-briefcase-medical", "danger", "Department Services", services_qs.count()),
    ]

    staff_role_counts = dept_staff.values("role__name").annotate(count=Count("id")).order_by("-count")
    employment_map = dict(dept_staff.model.EMPLOYMENT_TYPES)
    employment_counts = dept_staff.values("employment_type").annotate(count=Count("id"))

    timeline = [
        {"time": l.start_date.strftime("%b %d"), "title": f"Leave Request — {l.get_leave_type_display()}",
         "desc": f"{l.medical_staff} · {l.get_status_display()}"}
        for l in pending_leaves.select_related("medical_staff__user")[:6]
    ]

    return {
        "stat_cards": stats,
        "chart_one": _weekly_trend(appts_qs, today, "appointment_date", "Weekly Dept. Appointments"),
        "chart_two": {"type": "bar", "title": "Staff by Role",
                      "labels": [r["role__name"] or "Unassigned" for r in staff_role_counts],
                      "data": [r["count"] for r in staff_role_counts]},
        "chart_three": {"type": "doughnut", "title": "Employment Type",
                        "labels": [employment_map.get(r["employment_type"], r["employment_type"]) for r in employment_counts],
                        "data": [r["count"] for r in employment_counts]},
        "chart_four": {"type": "pie", **_status_dist(appts_qs)},
        "timeline": timeline,
        "side_panel": {"title": "Pending Leave Requests", "type": "status_list",
                       "items": [{"label": str(l.medical_staff), "count": l.get_leave_type_display()} for l in pending_leaves[:5]]},
    }


# ---------------- OTHER / fallback ---------------- #

def _other_overview(staff, today, week_start):
    appts_qs = Appointment.objects.filter(medical_staff=staff)

    stats = [
        _card("total_appts", "fa-calendar", "primary", "Total Appointments", appts_qs.count()),
        _card("pending", "fa-hourglass-half", "warning", "Pending", appts_qs.filter(status="PENDING").count()),
        _card("completed", "fa-circle-check", "success", "Completed", appts_qs.filter(status="COMPLETED").count()),
        _card("cancelled", "fa-ban", "danger", "Cancelled", appts_qs.filter(status="CANCELLED").count()),
        _card("confirmed", "fa-calendar-check", "info", "Confirmed Upcoming", appts_qs.filter(status="CONFIRMED", appointment_date__gte=today).count()),
        _card("high_priority", "fa-triangle-exclamation", "orange", "High/Emergency Priority", appts_qs.filter(priority__in=["HIGH", "EMERGENCY"]).count()),
        _card("checked_in", "fa-clipboard-check", "secondary", "Checked In", appts_qs.filter(status="CHECKED_IN").count()),
        _card("in_progress", "fa-person-walking-arrow-right", "teal", "In Progress", appts_qs.filter(status="IN_PROGRESS").count()),
    ]

    return {
        "stat_cards": stats,
        "chart_one": _weekly_trend(appts_qs, today, "appointment_date", "Weekly Appointments"),
        "chart_two": {"type": "bar", **_status_dist(appts_qs)},
        "chart_three": {"type": "doughnut", **_priority_dist(appts_qs)},
        "chart_four": {"type": "pie", "title": "Appointments", "labels": ["Total"], "data": [appts_qs.count()]},
        "timeline": _appointment_timeline(appts_qs),
        "side_panel": {"title": "", "type": "text", "items": []},
    }


ROLE_HANDLERS = {
    "DOCTOR": _doctor_overview, "NURSE": _nurse_overview, "LAB": _lab_overview,
    "PHYSIO": _physio_overview, "PHARMACY": _pharmacy_overview,
    "FRONT_DESK": _frontdesk_overview, "DIRECTOR": _director_overview, "OTHER": _other_overview,
}

####################### MEDICAL DASHBOARD OVERVIEW END ############################

def _serialize_leave(lv):
    return {
        "id": lv.id,
        "staff_name": lv.medical_staff.preferred_name,
        "staff_role": getattr(lv.medical_staff, "designation", ""),
        "leave_type": lv.leave_type,
        "leave_type_display": lv.get_leave_type_display(),
        "start_date": lv.start_date.isoformat(),
        "end_date": lv.end_date.isoformat(),
        "permission_start_time": (
            lv.permission_start_time.strftime("%H:%M")
            if lv.permission_start_time else None
        ),
        "permission_end_time": (
            lv.permission_end_time.strftime("%H:%M")
            if lv.permission_end_time else None
        ),
        "reason": lv.reason,
        "status": lv.status,
        "approved_by": lv.approved_by.preferred_name if lv.approved_by else None,
        "approved_at": lv.approved_at.isoformat() if lv.approved_at else None,
        "rejection_reason": lv.rejection_reason,
        "created_at": lv.created_at.isoformat(),
    }

def leave_request(request):

    leaves = (
        MedicalStaffLeave.objects.all()
    )
    
    leaves_json = json.dumps([_serialize_leave(lv) for lv in leaves], default=str)

    context = {
        "active_sb": "leave_request",
        "leaves_json": leaves_json
    }

    return render(request, "Jack/leave_request.html", context)

@login_required
def staff_leave_update_status(request, pk):
    leave = get_object_or_404(MedicalStaffLeave, pk=pk)
    data = json.loads(request.body or "{}")
    new_status = data.get("status")

    if new_status not in ("APPROVED", "REJECTED"):
        return JsonResponse({"error": "Invalid status"}, status=400)

    leave.status = new_status

    leave.approved_by = getattr(request.user, "medicalstaffprofile", None)
    leave.approved_at = timezone.now()

    if new_status == "REJECTED":
        reason = (data.get("rejection_reason") or "").strip()
        if not reason:
            return JsonResponse({"error": "Rejection reason required"}, status=400)
        leave.rejection_reason = reason

    leave.save()

    return JsonResponse({
        "status": leave.status,
        "approved_by": leave.approved_by.get_full_name() if leave.approved_by else None,
    })