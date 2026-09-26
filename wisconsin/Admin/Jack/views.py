from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from Students.models import StudentProfile
from django.http import JsonResponse
from .forms import *
from django.contrib import messages
from .models import Sport, SportClub, SportsFacility, SportTeamModel, Coach, Athletic
from Admin.models import User
from Students.models import StudentProfile
from Medical.models import *
from django.utils import timezone
import datetime
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.serializers import serialize
from django.db.models import Q
import json
from django.db import models as django_models
from PermissionAccess.decorators import require_permission, require_page_access

@login_required
def faculty(request):
    return render(request, 'jack/faculty.html')

@login_required
def student_json(request):

    students = StudentProfile.objects.all()

    total_stu = students.count()

    active_stu = StudentProfile.objects.filter(
        current_status = "ACTIVE"
    ).count()

    leave_stu = StudentProfile.objects.filter(
        current_status = "LEAVE"
    ).count()

    graduated_stu = StudentProfile.objects.filter(
        current_status = "GRADUATED"
    ).count()

    withdrawn_stu = StudentProfile.objects.filter(
        current_status = "WITHDRAWN"
    ).count()

    data = []

    for stu in students:
        data.append({
            "id": stu.id,
            "user": stu.user.username,
            "image": stu.user.profile_photo.url if stu.user.profile_photo else None,
            "student_number": stu.student_number,
            "preferred_name": stu.preferred_name,
            "university_email": stu.university_email,
            "personal_email": stu.personal_email,
            "citizenship_status": stu.citizenship_status,
            "marital_status": stu.marital_status,
            "admission_date": stu.admission_date,
            "expected_graduation_date": stu.expected_graduation_date,
            "current_status": stu.current_status,
            "academic_level": stu.academic_level,
            "cumulative_gpa": stu.cumulative_gpa,
            "created_at": stu.created_at,
            "updated_at": stu.updated_at,
        })

    
    student_trend = [
        {"year": 2022, "stu_total": 2850},
        {"year": 2023, "stu_total": 4020},
        {"year": 2024, "stu_total": 5150},
        {"year": 2025, "stu_total": 4248},
        {"year": 2026, "stu_total": 7320},
    ]

    return JsonResponse({
        "students": data,
        "total_students": total_stu,
        "active_students": active_stu,
        "leave_students": leave_stu,
        "graduated_students": graduated_stu,
        "withdrawn_students": withdrawn_stu,
        "student_trend": student_trend,
    })


@login_required
def student_view(request, id):
    student = get_object_or_404(
        StudentProfile,
        id=id
    )

    full_name = (
        " ".join(
            filter(
                None,
                [
                    student.user.first_name,
                    student.user.middle_name,
                    student.user.last_name,
                ],
            )
        )
        or student.preferred_name
    )
    
    context = {
        'student': student,
        'full_name': full_name
    }
    
    return render(request, "jack/student_view.html", context)


####################### SPORTS VIEW START ############################

@require_page_access("sports_page", user_types=["admin"])
@login_required
def sports(request):
    return render(request, "jack/sports.html")

@require_permission("sport_create")
@login_required
def sports_create(request):

    form = SportForm()

    gender_suffix = {
        "MALE": "M",
        "FEMALE": "F",
        "TRANSGENDER": "TG",
        "NON_BINARY": "NB",
        "OTHER": "O",
        "PREFER_NOT_TO_SAY": "PNS",
    }

    if request.method == "POST":
        form = SportForm(request.POST, request.FILES)
        print(request.POST)
        print(request.POST.get("sport_name"))

        if form.is_valid():
            sport = form.save(commit=False)

            suffix = gender_suffix.get(sport.gender, "")
            sport.sport_name = f"{sport.sport_name.strip()} {suffix}".strip()

            sport.save()
            messages.success(request, "Sport created successfully.")
            return redirect("sports")
        
    context = {
        'form': form
    }

    return render(request, "jack/sport_create.html", context)

@login_required
def sports_json(request):

    sports = Sport.objects.all()

    data = []

    for s in sports:
        data.append({
            'id': s.id,
            'sport_uuid': s.sport_uuid,
            'sport_name': s.sport_name,
            'sport_type': s.sport_type,
            'gender': s.gender,
            'is_team_sport': s.is_team_sport,
            'min_players': s.min_players,
            'max_players': s.max_players,
            'is_olympic_sport': s.is_olympic_sport,
            'is_active': s.is_active,
            'icon': s.icon.url if s.icon else None,
            'thumbnail': s.thumbnail.url if s.icon else None,
        })

    return JsonResponse({
        "sports": data
    })

@require_permission("sport_update")
@login_required
def sports_edit(request, sport_uuid):

    sport = get_object_or_404(
        Sport,
        sport_uuid=sport_uuid
    )

    gender_suffix = {
        "MALE": "M",
        "FEMALE": "F",
        "TRANSGENDER": "TG",
        "NON_BINARY": "NB",
        "OTHER": "O",
        "PREFER_NOT_TO_SAY": "PNS",
    }

    suffix = gender_suffix.get(sport.gender, "")

    if suffix and sport.sport_name.endswith(f" {suffix}"):
        sport.sport_name = sport.sport_name[:-(len(suffix) + 1)]

    form = SportForm(instance=sport)

    if request.method == "POST":

        form = SportForm(
            request.POST,
            request.FILES,
            instance=sport
        )

        if form.is_valid():

            sport = form.save(commit=False)

            suffix = gender_suffix.get(sport.gender, "")
            sport.sport_name = f"{sport.sport_name.strip()} {suffix}".strip()

            sport.save()

            messages.success(request, "Sport updated successfully.")

            return redirect("sports")

    context = {
        'sport': sport,
        'form': form
    }

    return render(request, 'jack/sport_edit.html', context)

@require_permission("sport_delete")
@login_required
def sports_delete(request, sport_uuid):

    sport = get_object_or_404(
        Sport,
        sport_uuid=sport_uuid
    )

    sport.delete()

    messages.success(request, "Sport deleted successfully.")

    return redirect("sports")

####################### SPORTS VIEW END ############################


####################### TEAM VIEW START ############################

@require_page_access("teams_page", user_types=["admin"])
@login_required
def teams(request):
    return render(request, 'jack/team.html')

@require_permission("sportteammodel_create")
@login_required
def team_create(request):

    sports = Sport.objects.filter(is_active=True).order_by('sport_name')
    coaches = Coach.objects.filter(is_active=True).order_by('staff_id')
    facilities = SportsFacility.objects.filter(status='ACTIVE').order_by('facility_name')
    clubs = SportClub.objects.filter(is_active=True).order_by('club_name')
    
    if request.method == 'POST':
        form = SportTeamForm(request.POST, request.FILES)
        if form.is_valid():
            team = form.save()
            messages.success(request, f'Team "{team.team_name}" created successfully!')
            return redirect('teams')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SportTeamForm()
    
    context = {
        'form': form,
        'sports': sports,
        'coaches': coaches,
        'facilities': facilities,
        'clubs': clubs,
    }
    return render(request, 'jack/team_create.html', context)

@require_permission("sportteammodel_update")
@login_required
def team_edit(request, team_uuid):

    team = get_object_or_404(SportTeamModel, team_uuid=team_uuid)
    
    sports = Sport.objects.filter(is_active=True).order_by('sport_name')
    coaches = Coach.objects.filter(is_active=True).order_by('staff_id')
    facilities = SportsFacility.objects.filter(status='ACTIVE').order_by('facility_name')
    clubs = SportClub.objects.filter(is_active=True).order_by('club_name')
    
    if request.method == 'POST':
        form = SportTeamForm(request.POST, request.FILES, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, f'Team "{team.team_name}" updated successfully!')
            return redirect('teams')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SportTeamForm(instance=team)
    
    context = {
        'form': form,
        'sports': sports,
        'coaches': coaches,
        'facilities': facilities,
        'clubs': clubs,
    }
    return render(request, 'jack/team_create.html', context)

@require_permission("sportteammodel_delete")
@login_required
def team_delete(request, team_uuid):

    team = get_object_or_404(
        SportTeamModel,
        team_uuid=team_uuid
    )

    team.delete()

    messages.success(request, "Team deleted successfully.")

    return redirect("teams")

@login_required
def team_json(request):

    team = SportTeamModel.objects.all()

    data = []

    for t in team:
        data.append({
            "id": t.team_id,
            "team_uuid": t.team_uuid,
            "team_code": t.team_code,
            "team_name": t.team_name,
            "icon": t.icon.url if t.icon else None,
            "sport_type": t.sport_type.sport_name if t.sport_type else None,
            "division": t.division,
            "head_coach": t.head_coach.staff_id if t.head_coach else None,
            "home_facility": t.home_facility.facility_name if t.home_facility else None,
            "founded_year": t.founded_year,
            "status": t.status,
            "club": t.club.club_name if t.club else None
        })

    return JsonResponse({
        'teams': data
    })

def get_initials(name):
    if not name:
        return "TE"

    return "".join(word[0] for word in name.split()).upper()[:2]

@require_page_access("team_view_page", user_types=["admin"])
@login_required
def team_view(request, team_uuid):

    team = get_object_or_404(
        SportTeamModel,
        team_uuid = team_uuid
    )

    team_initial = get_initials(team.team_name)

    context = {
        'team': team,
        'initials': team_initial
    }

    return render(request, 'jack/team_view.html', context)

####################### TEAM VIEW END ############################

####################### ATHLETIC VIEW START ############################

@require_page_access("athletes_page", user_types=["admin"])
@login_required
def athletic(request):
    return render(request, 'jack/athletic.html')

@require_permission("athletic_create")
@login_required
def athletic_create(request):
    role_filter = request.GET.get('role_filter', '')
    
    students = User.objects.all().order_by('username')
    
    if role_filter == 'is_student':
        students = students.filter(is_student=True)
    elif role_filter == 'is_faculty':
        students = students.filter(is_faculty=True)
    elif role_filter == 'is_staff':
        students = students.filter(is_staff=True)
    
    teams = SportTeamModel.objects.filter(status=True).order_by('team_name')
    individual_sports = Sport.objects.filter(is_active=True, is_team_sport=False).order_by('sport_name')
    
    if request.method == 'POST':
        form = AthleticForm(request.POST)
        form.fields['student'].queryset = students
        if form.is_valid():
            athlete = form.save()
            messages.success(request, f'Athlete "{athlete.student}" created successfully!')
            return redirect('athletics')
        else:
            messages.error(request, 'Please correct the errors below.')
            print("Form errors:", form.errors)
    else:
        form = AthleticForm()
        form.fields['student'].queryset = students
    
    context = {
        'form': form,
        'students': students,
        'teams': teams,
        'individual_sports': individual_sports,
        'role_filter': role_filter,
    }

    return render(request, 'jack/athletic_create.html', context)

@require_permission("athletic_update")
@login_required
def athlete_edit(request, athlete_uuid):
    athlete = get_object_or_404(Athletic, student__uuid=athlete_uuid)
    
    role_filter = request.GET.get('role_filter', '')
    
    students = User.objects.all().order_by('username')
    
    if role_filter == 'is_student':
        students = students.filter(is_student=True)
    elif role_filter == 'is_faculty':
        students = students.filter(is_faculty=True)
    elif role_filter == 'is_staff':
        students = students.filter(is_staff=True)
    
    teams = SportTeamModel.objects.filter(status=True).order_by('team_name')
    individual_sports = Sport.objects.filter(is_active=True, is_team_sport=False).order_by('sport_name')
    
    if request.method == 'POST':
        form = AthleticForm(request.POST, instance=athlete)
        form.fields['student'].queryset = students
        if form.is_valid():
            form.save()
            messages.success(request, f'Athlete "{athlete.student}" updated successfully!')
            return redirect('athletics')
        else:
            messages.error(request, 'Please correct the errors below.')
            print("Form errors:", form.errors)
    else:
        form = AthleticForm(instance=athlete)
        form.fields['student'].queryset = students
    
    context = {
        'form': form,
        'students': students,
        'teams': teams,
        'individual_sports': individual_sports,
        'role_filter': role_filter,
    }
    return render(request, 'jack/athletic_create.html', context)

@login_required
def athlete_json(request):

    athletes = Athletic.objects.select_related(
        "student", "team"
    ).prefetch_related(
        "individual_sports"
    )

    data = []

    for ath in athletes:
        data.append({
            "id": ath.athlete_id,

            "student": {
                "id": ath.student.id,
                "username": ath.student.username,
                "full_name": ath.student.get_full_name(),
            },

            "athlete_uuid": ath.student.uuid,

            "profile_photo": (
                request.build_absolute_uri(ath.student.profile_photo.url)
                if ath.student.profile_photo
                else None
            ),

            "team": {
                "id": ath.team.team_id,
                "name": ath.team.team_name,
            } if ath.team else None,

            "individual_sports": [
                {
                    "id": sport.id,
                    "name": sport.sport_name,
                }
                for sport in ath.individual_sports.all()
            ],

            "jersey_number": ath.jersey_number,
            "position": ath.position,
            "height": float(ath.height) if ath.height else None,
            "weight": float(ath.weight) if ath.weight else None,

            "class_year": ath.class_year,
            "class_year_display": ath.get_class_year_display(),

            "eligibility_status": ath.eligibility_status,
            "eligibility_status_display": ath.get_eligibility_status_display(),

            "scholarship_status": ath.scholarship_status,
            "is_active": ath.is_active,
        })

    return JsonResponse({
        "athletes": data
    })

@require_page_access("athlete_view_page", user_types=["admin"])
@login_required
def athlete_view(request, athlete_uuid):

    athlete = get_object_or_404(
        Athletic.objects.select_related(
            "team",
            "student",
            "student__role",
            # "student__patient_profile",
            "student__student_profile",
            "student__staff_profile",
            "student__staff_profile__supervisor",
            "student__staff_profile__supervisor__user",
            "student__faculty_profile",
            "student__faculty_profile__faculty_rank",
            "student__faculty_profile__department",
        ).prefetch_related("individual_sports"),
        student__uuid=athlete_uuid,
    )

    athlete_initial = get_initials(athlete.student.get_full_name())

    context = {
        "athlete": athlete,
        "initial": athlete_initial
    }

    return render(request, "jack/athletic_view.html", context)

# @require_permission("athletic_delete")
# @login_required
# def athlete_delete(request, athlete_id):
#     athlete = get_object_or_404(Athletic, athlete_id=athlete_id)
    
#     if request.method == 'POST':
#         username = athlete.student.username
#         athlete.delete()
#         messages.success(request, f'Athlete "{username}" deleted successfully!')
#         return redirect('athletes')
    
#     context = {
#         'athlete': athlete,
#     }
#     return render(request, 'athlete_confirm_delete.html', context)


####################### ATHLETIC VIEW END ############################

####################### MEDICAL VIEW START ############################

def get_patient_profile_if_exists(user):
    
    if getattr(user, 'is_admin', False):
        return PatientProfile.objects.filter(admin=user).first()
    
    return None


def get_athlete_profile_if_exists(user):
    
    athlete = Athletic.objects.filter(student=user).first()
    if athlete:
        return AthleteMedicalProfile.objects.filter(athlete=athlete).first()
    
    return None


def is_athlete(user):

    return Athletic.objects.filter(student=user).exists()


@login_required
def get_available_medical_staff(request):
    
    hospital_uuid = request.GET.get("hospital")
    appointment_date = request.GET.get("date")

    print(f"🔍 Fetching staff for hospital: {hospital_uuid}, date: {appointment_date}")

    if not hospital_uuid or not appointment_date:
        return JsonResponse({
            "success": False,
            "message": "Hospital and appointment date are required.",
            "staff": [],
        })

    try:
        selected_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({
            "success": False,
            "message": "Invalid appointment date.",
            "staff": [],
        })

    weekday_code = selected_date.strftime("%a").upper()[:3]
    print(f"📅 Weekday code: {weekday_code}")

    shifts = Shift.objects.filter(
        start_date__lte=selected_date,
        end_date__gte=selected_date,
    )
    
    print(f"🔄 Found {shifts.count()} shifts")

    department_ids = []
    for shift in shifts:
        active_days = shift.active_weekdays()
        print(f"  Shift: {shift.shift_label}, Active days: {active_days}")
        if weekday_code in active_days:
            department_ids.append(shift.department_id)
            print(f"  ✅ Added department: {shift.department.department_name}")

    print(f"📋 Department IDs: {department_ids}")

    if not department_ids:
        print("❌ No departments have shifts on this date")
        return JsonResponse({
            "success": True,
            "staff": [],
            "message": "No departments have shifts on this date."
        })

    staff_queryset = (
        MedicalStaffProfile.objects
        .filter(
            hospital__uuid=hospital_uuid,
            department_id__in=department_ids,
            status="ACTIVE",
            role__category="DOCTOR",
        )
        .select_related(
            "user",
            "department",
            "hospital",
            "role",
        )
        .order_by(
            "user__first_name",
            "user__last_name",
        )
    )

    print(f"👨‍⚕️ Found {staff_queryset.count()} staff members")

    staff = []
    for member in staff_queryset:
        user = member.user
        full_name = (
            member.preferred_name
            or user.get_full_name()
            or user.username
        )

        staff.append({
            "uuid": str(member.uuid),
            "name": full_name,
            "employee_id": member.employee_id,
            "department": member.department.department_name if member.department else "N/A",
            "role": str(member.role) if member.role else "N/A",
        })

    return JsonResponse({
        "success": True,
        "staff": staff,
    })


@login_required
def book_appointment(request):

    service_param = request.GET.get('service', '')
    requires_athlete = False
    
    if service_param.upper() == 'SPORTS':
        if not is_athlete(request.user):
            requires_athlete = True
            messages.error(
                request,
                "🏃 Sports services are available only for athletes."
            )

    if request.method == "POST":
        service = request.POST.get('service', '')
        service_custom = request.POST.get('service_custom', '')
        
        post_data = request.POST.copy()
        
        if service == 'OTHER' and service_custom:
            post_data['service'] = service_custom.strip()
        elif service == 'OTHER' and not service_custom:
            post_data['service'] = 'Other Service'
        
        form = AppointmentForm(post_data, user=request.user)

        if form.is_valid():
            if service.upper() == 'SPORTS':
                if not is_athlete(request.user):
                    messages.error(
                        request,
                        "❌ Sports services are available only for athletes."
                    )
                    context = {
                        "form": form,
                        "hospitals": MedicalCenter.objects.filter(is_active=True),
                        "today": timezone.now().date(),
                        "max_date": timezone.now().date() + timezone.timedelta(days=30),
                        "requires_athlete": True,
                    }
                    return render(request, "Jack/medical_appointment.html", context)
            
            try:
                with transaction.atomic():
                    existing_patient = get_patient_profile_if_exists(request.user)
                    
                    appointment = form.save(commit=False)
                    appointment.user = request.user
                    appointment.appointment_time = None
                    if existing_patient:
                        appointment.patient = existing_patient
                        messages.info(request, "📋 Using existing patient profile.")
                    else:
                        appointment.patient = None
                        messages.info(request, "📝 Patient profile will be created upon arrival confirmation.")
                    
                    if service.upper() == 'SPORTS':
                        athlete_profile = get_athlete_profile_if_exists(request.user)
                        if athlete_profile:
                            appointment.athlete = athlete_profile
                            messages.info(request, "🏃 Athlete profile linked to appointment.")

                    appointment.appointment_number = form.generate_appointment_id(
                        appointment.appointment_date
                    )

                    appointment.save()

                    messages.success(
                        request,
                        f"✅ Appointment #{appointment.appointment_number} has been scheduled successfully!"
                    )
                    return redirect("appointment_overview")

            except Exception as e:
                messages.error(request, f"❌ Error scheduling appointment: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"❌ {field}: {error}")

    else:
        form = AppointmentForm(user=request.user)

    has_athlete_profile = is_athlete(request.user)

    context = {
        "form": form,
        "hospitals": MedicalCenter.objects.filter(is_active=True),
        "today": timezone.now().date(),
        "max_date": timezone.now().date() + timezone.timedelta(days=30),
        "requires_athlete": requires_athlete,
        "has_athlete_profile": has_athlete_profile,
    }

    return render(request, "Jack/admin_medical_appointment.html", context)

@require_page_access("medical_reports_page", user_types=["admin"])
@login_required
def medical_reports(request):
    return render(request, "jack/medical_reports.html")


def _serialize_value(value):
    if value is None or value == '':
        return '—'
    if isinstance(value, datetime.datetime):
        return value.strftime('%Y-%m-%d %H:%M')
    if isinstance(value, datetime.date):
        return value.strftime('%Y-%m-%d')
    if isinstance(value, datetime.time):
        return value.strftime('%H:%M')
    if isinstance(value, django_models.Model):
        return str(value)
    if isinstance(value, bool):
        return value
    return value


@require_http_methods(["GET"])
def report_data(request, report_key):

    try:
        report_configs = {
            'patient-profile-list': {
                'model': PatientProfile,
                'fields': ['patient_number', 'patient_name', 'patient_type', 'blood_group',
                          'allergies', 'chronic_conditions', 'created_at'],
                'date_field': 'created_at',
                'filter_fields': ['patient_type', 'blood_group']
            },
            'patient-registry-list': {
                'model': PatientRegistry,
                'fields': ['patient_number', 'patient_type', 'registration_date'],
                'date_field': 'registration_date',
                'filter_fields': ['patient_type']
            },

            'appointment-list': {
                'model': Appointment,
                'fields': ['appointment_number', 'patient', 'medical_staff', 'hospital',
                          'appointment_date', 'appointment_time', 'priority', 'status',
                          'service', 'reason'],
                'date_field': 'appointment_date',
                'filter_fields': ['priority', 'status']
            },
            'medical-visit-list': {
                'model': MedicalVisit,
                'fields': ['visit_number', 'patient', 'attending_staff', 'department',
                          'visit_date', 'visit_time', 'visit_type', 'visit_status',
                          'chief_complaint'],
                'date_field': 'visit_date',
                'filter_fields': ['visit_type', 'visit_status']
            },
            'patient-registration-list': {
                'model': PatientRegistration,
                'fields': ['registration_number', 'patient', 'registration_date',
                          'registration_time', 'registration_type', 'status',
                          'token_number', 'chief_complaint'],
                'date_field': 'registration_date',
                'filter_fields': ['registration_type', 'status']
            },

            'athlete-medical-profile-list': {
                'model': AthleteMedicalProfile,
                'fields': ['athlete_medical_id', 'athlete', 'medical_clearance_status',
                          'fitness_level', 'injury_risk', 'clearance_date',
                          'next_medical_checkup'],
                'date_field': 'next_medical_checkup',
                'filter_fields': ['medical_clearance_status', 'fitness_level', 'injury_risk']
            },
            'injury-record-list': {
                'model': InjuryRecord,
                'fields': ['injury_title', 'medical_profile', 'body_part', 'severity',
                          'injury_date', 'injury_status', 'estimated_recovery_days'],
                'date_field': 'injury_date',
                'filter_fields': ['severity', 'injury_status']
            },

            'laboratory-test-list': {
                'model': LaboratoryTest,
                'fields': ['test_number', 'patient', 'test_name', 'test_category',
                          'sample_type', 'result', 'result_status', 'status',
                          'requested_date'],
                'date_field': 'requested_date',
                'filter_fields': ['test_category', 'result_status', 'status']
            },

            'medical-staff-profile-list': {
                'model': MedicalStaffProfile,
                'fields': ['employee_id', 'role', 'department', 'status',
                          'employment_type', 'hire_date'],
                'date_field': 'hire_date',
                'filter_fields': ['role', 'status', 'employment_type']
            },
            'shift-list': {
                'model': Shift,
                'fields': ['shift_label', 'department', 'hospital', 'shift_type',
                          'start_time', 'end_time', 'start_date', 'end_date'],
                'date_field': 'start_date',
                'filter_fields': ['shift_type']
            },
            'medical-staff-leave-list': {
                'model': MedicalStaffLeave,
                'fields': ['medical_staff', 'leave_type', 'start_date', 'end_date',
                          'status', 'reason'],
                'date_field': 'start_date',
                'filter_fields': ['leave_type', 'status']
            },

            'medical-center-list': {
                'model': MedicalCenter,
                'fields': ['hospital_name', 'hospital_code', 'hospital_location',
                          'hospital_status', 'established_year', 'is_active'],
                'date_field': None,
                'filter_fields': ['hospital_status', 'is_active']
            },
            'medical-department-list': {
                'model': MedicalDepartment,
                'fields': ['department_code', 'department_name', 'department_type',
                          'location', 'is_emergency'],
                'date_field': None,
                'filter_fields': ['department_type', 'is_emergency']
            },
            'health-camp-list': {
                'model': HealthCamp,
                'fields': ['camp_code', 'camp_name', 'department', 'organizer',
                          'camp_type', 'start_date', 'end_date', 'status', 'venue'],
                'date_field': 'start_date',
                'filter_fields': ['camp_type', 'status']
            },
        }

        config = report_configs.get(report_key)
        if not config:
            return JsonResponse({'error': 'Report not found'}, status=404)

        model = config['model']
        fields = config['fields']
        date_field = config['date_field']
        filter_fields = config['filter_fields']

        queryset = model.objects.filter(is_active=True)

        fk_fields = [f for f in fields if f in [f.name for f in model._meta.get_fields()
                     if getattr(f, 'many_to_one', False) or getattr(f, 'one_to_one', False)]]
        if fk_fields:
            queryset = queryset.select_related(*fk_fields)

        EXTRA_SELECT_RELATED = {
            'patient-profile-list': ['student', 'staff', 'faculty', 'admin'],
        }
        extra = EXTRA_SELECT_RELATED.get(report_key)
        if extra:
            queryset = queryset.select_related(*extra)

        for key in filter_fields:
            value = request.GET.get(key)
            if value:
                queryset = queryset.filter(**{key: value})

        if date_field:
            date_value = request.GET.get(date_field)
            if date_value:
                try:
                    filter_date = datetime.datetime.strptime(date_value, '%Y-%m-%d').date()
                    queryset = queryset.filter(**{f'{date_field}__date': filter_date})
                except ValueError:
                    pass

        rows = []
        for obj in queryset:
            row = {}
            for field in fields:
                value = getattr(obj, field, None)
                row[field] = _serialize_value(value)
            rows.append(row)

        columns = [{'key': field, 'label': field.replace('_', ' ').title()} for field in fields]

        return JsonResponse({
            'rows': rows,
            'columns': columns,
            'total': queryset.count()
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e), 'trace': traceback.format_exc()}, status=500)
    
####################### MEDICAL VIEW END ############################