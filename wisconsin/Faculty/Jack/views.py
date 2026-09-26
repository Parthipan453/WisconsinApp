from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse
from .forms import AppointmentForm
from Medical.models import *
from Students.models import StudentProfile
from Faculty.models import FacultyProfile
from Staff.models import StaffProfile
import uuid
from datetime import datetime
from Admin.models import *


def get_patient_profile_if_exists(user):
    
    if hasattr(user, 'is_faculty') and user.is_faculty:
        faculty = FacultyProfile.objects.filter(user=user).first()
        if faculty:
            return PatientProfile.objects.filter(faculty=faculty).first()
    
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

                    if existing_patient:
                        appointment.patient = existing_patient
                        messages.info(request, "Using existing patient profile.")
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
                    return redirect("faculty_appointment_history")

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

    return render(request, "Jack/fac_medical_appointment.html", context)