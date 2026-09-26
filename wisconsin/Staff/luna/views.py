from datetime import datetime, timedelta
from types import SimpleNamespace

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from Medical.models import (
    Appointment,
    PatientRegistration,
    PatientProfile,
    MedicalVisit,
)


@login_required
def staff_medical_history(request):
    try:
        staff_profile = request.user.staff_profile
    except Exception:
        staff_profile = None

    staff_patient = None

    if staff_profile:

        staff_patient = (
            PatientProfile.objects
            .filter(
                staff=staff_profile,
                patient_type="STAFF",
            )
            .first()
        )

    appointments = (
        Appointment.objects
        .filter(
            user=request.user
        )
        .select_related(
            "patient",

            "medical_staff",
            "medical_staff__user",

            "hospital",
        )
        .order_by(
            "-appointment_date",
            "-appointment_time",
            "-created_at",
        )
    )

    registrations = PatientRegistration.objects.none()

    if staff_patient:

        registrations = (
            PatientRegistration.objects
            .filter(
                patient=staff_patient
            )
            .select_related(

                "patient",

                "appointment",
                "appointment__medical_staff",
                "appointment__medical_staff__user",
                "appointment__hospital",

                "medical_visit",
                "medical_visit__attending_staff",
                "medical_visit__attending_staff__user",

                "schedule",

                "shift_assignment",
                "shift_assignment__medical_staff",
                "shift_assignment__medical_staff__user",
            )
            .order_by(
                "-registration_date",
                "-registration_time",
            )
        )

    medical_visits = MedicalVisit.objects.none()

    if staff_patient:

        medical_visits = (
            MedicalVisit.objects
            .filter(
                patient=staff_patient
            )
            .select_related(
                "patient",

                "attending_staff",
                "attending_staff__user",

                "department",
            )
            .order_by(
                "-visit_date",
                "-visit_time",
            )
        )

    status_filter = request.GET.get(
        "status",
        "",
    ).strip()

    search_query = request.GET.get(
        "search",
        "",
    ).strip()

    history = []

    used_appointment_ids = set()
    used_visit_ids = set()

    for registration in registrations:

        appointment = registration.appointment
        visit = registration.medical_visit

        if appointment:

            used_appointment_ids.add(
                appointment.id
            )

        if visit:

            used_visit_ids.add(
                visit.id
            )

        if appointment:

            display_type = "Appointment"

        else:

            display_type = "Walk In"

        if appointment:

            display_number = (
                appointment.appointment_number
                or "—"
            )

        elif registration.token_number is not None:

            display_number = (
                f"TK-"
                f"{registration.registration_date.strftime('%Y%m%d')}-"
                f"{registration.token_number:03d}"
            )

        else:

            display_number = (
                registration.registration_number
                or "—"
            )

        if registration.token_number is not None:

            display_token = (
                f"TK-"
                f"{registration.registration_date.strftime('%Y%m%d')}-"
                f"{registration.token_number:03d}"
            )

        else:

            display_token = None

        if (
            visit
            and visit.attending_staff
        ):

            display_doctor = (
                visit.attending_staff
            )

        elif (
            appointment
            and appointment.medical_staff
        ):

            display_doctor = (
                appointment.medical_staff
            )

        elif (
            registration.shift_assignment
            and registration.shift_assignment.medical_staff
        ):

            display_doctor = (
                registration
                .shift_assignment
                .medical_staff
            )

        else:

            display_doctor = None


        if visit:

            display_date = visit.visit_date
            display_time = visit.visit_time

        elif appointment:

            display_date = appointment.appointment_date
            display_time = appointment.appointment_time

        else:

            display_date = registration.registration_date
            display_time = registration.registration_time


        if (
            appointment
            and appointment.reason
        ):

            display_reason = (
                appointment.reason
            )

        elif registration.chief_complaint:

            display_reason = (
                registration.chief_complaint
            )

        elif (
            visit
            and visit.chief_complaint
        ):

            display_reason = (
                visit.chief_complaint
            )

        else:

            display_reason = "-"


        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        if (
            visit
            and visit.visit_status == "COMPLETED"
        ):

            display_status = "COMPLETED"

        elif (
            registration.status == "COMPLETED"
        ):

            display_status = "COMPLETED"

        elif (
            registration.status == "IN_PROGRESS"
        ):

            display_status = "IN_PROGRESS"

        elif (
            registration.status == "CANCELLED"
        ):

            display_status = "CANCELLED"

        elif appointment:

            display_status = appointment.status

        else:

            display_status = "WAITING"

        history.append(
            SimpleNamespace(

                source="registration",

                registration=registration,

                appointment=appointment,

                medical_visit=visit,

                display_type=display_type,

                display_number=display_number,

                display_token=display_token,

                display_doctor=display_doctor,

                display_date=display_date,

                display_time=display_time,

                display_reason=display_reason,

                display_visit_type=(
                    visit.get_visit_type_display()
                    if visit
                    else None
                ),

                display_diagnosis=(
                    visit.diagnosis
                    if visit
                    else None
                ),

                display_treatment=(
                    visit.treatment
                    if visit
                    else None
                ),

                display_medications=(
                    visit.medications
                    if visit
                    else None
                ),

                display_follow_up_required=(
                    visit.follow_up_required
                    if visit
                    else False
                ),

                display_follow_up_date=(
                    visit.follow_up_date
                    if visit
                    else None
                ),

                display_status=display_status,

                can_cancel=False,

                remaining_time=None,
            )
        )

    now = timezone.now()

    for appointment in appointments:

        if appointment.id in used_appointment_ids:

            continue


        used_appointment_ids.add(
            appointment.id
        )

        can_cancel = False
        remaining_time = None


        if appointment.created_at:

            expiry_time = (
                appointment.created_at
                + timedelta(minutes=10)
            )

            if (
                appointment.status == "PENDING"
                and now < expiry_time
            ):

                can_cancel = True

                seconds = int(
                    (
                        expiry_time - now
                    ).total_seconds()
                )

                minutes = seconds // 60

                seconds = seconds % 60

                remaining_time = (
                    f"{minutes:02d}:{seconds:02d}"
                )

        history.append(
            SimpleNamespace(

                source="appointment",

                registration=None,

                appointment=appointment,

                medical_visit=None,

                display_type="Appointment",

                display_number=(
                    appointment.appointment_number
                    or "—"
                ),

                display_token=None,

                display_doctor=(
                    appointment.medical_staff
                    if appointment.medical_staff
                    else None
                ),

                display_date=(
                    appointment.appointment_date
                ),

                display_time=(
                    appointment.appointment_time
                ),

                display_reason=(
                    appointment.reason
                    or "-"
                ),

                display_visit_type=None,

                display_diagnosis=None,

                display_treatment=None,

                display_medications=None,

                display_follow_up_required=False,

                display_follow_up_date=None,

                display_status=(
                    appointment.status
                ),

                can_cancel=can_cancel,

                remaining_time=remaining_time,
            )
        )
    for visit in medical_visits:

        if visit.id in used_visit_ids:

            continue


        used_visit_ids.add(
            visit.id
        )


        history.append(
            SimpleNamespace(

                source="medical_visit",

                registration=None,

                appointment=None,

                medical_visit=visit,

                display_type="Walk In",

                display_number=(
                    visit.visit_number
                    or "—"
                ),

                display_token=None,

                display_doctor=(
                    visit.attending_staff
                    if visit.attending_staff
                    else None
                ),

                display_date=(
                    visit.visit_date
                ),

                display_time=(
                    visit.visit_time
                ),

                display_reason=(
                    visit.chief_complaint
                    or "-"
                ),

                display_visit_type=(
                    visit.get_visit_type_display()
                ),

                display_diagnosis=(
                    visit.diagnosis
                    or None
                ),

                display_treatment=(
                    visit.treatment
                    or None
                ),

                display_medications=(
                    visit.medications
                    or None
                ),

                display_follow_up_required=(
                    visit.follow_up_required
                ),

                display_follow_up_date=(
                    visit.follow_up_date
                ),

                display_status=(
                    visit.visit_status
                ),

                can_cancel=False,

                remaining_time=None,
            )
        )

    if search_query:

        search_lower = search_query.lower()

        filtered_history = []


        for item in history:

            appointment = item.appointment

            registration = item.registration

            visit = item.medical_visit

            values = []

            if appointment:

                values.extend([
                    appointment.appointment_number,

                    appointment.service,

                    appointment.reason,

                    (
                        appointment.medical_staff.user.first_name
                        if (
                            appointment.medical_staff
                            and appointment.medical_staff.user
                        )
                        else ""
                    ),

                    (
                        appointment.medical_staff.user.last_name
                        if (
                            appointment.medical_staff
                            and appointment.medical_staff.user
                        )
                        else ""
                    ),
                ])

            if registration:

                values.extend([
                    registration.registration_number,

                    registration.chief_complaint,

                    str(
                        registration.token_number
                        or ""
                    ),
                ])

            if visit:

                values.extend([
                    visit.visit_number,

                    visit.chief_complaint,

                    visit.diagnosis,

                    visit.treatment,

                    visit.medications,

                    (
                        visit.attending_staff.user.first_name
                        if (
                            visit.attending_staff
                            and visit.attending_staff.user
                        )
                        else ""
                    ),

                    (
                        visit.attending_staff.user.last_name
                        if (
                            visit.attending_staff
                            and visit.attending_staff.user
                        )
                        else ""
                    ),
                ])

            values.extend([
                item.display_type,

                item.display_number,
            ])


            found = any(
                search_lower in str(
                    value or ""
                ).lower()
                for value in values
            )


            if found:

                filtered_history.append(
                    item
                )


        history = filtered_history

    if (
        status_filter
        and status_filter != "All Status"
    ):

        history = [
            item
            for item in history
            if item.display_status == status_filter
        ]

    status_counts = {

        "total": len(history),

        "pending": sum(
            1
            for item in history
            if item.display_status == "PENDING"
        ),

        "confirmed": sum(
            1
            for item in history
            if item.display_status == "CONFIRMED"
        ),

        "arrived": sum(
            1
            for item in history
            if item.display_status == "ARRIVED"
        ),

        "in_progress": sum(
            1
            for item in history
            if item.display_status == "IN_PROGRESS"
        ),

        "completed": sum(
            1
            for item in history
            if item.display_status == "COMPLETED"
        ),

        "cancelled": sum(
            1
            for item in history
            if item.display_status == "CANCELLED"
        ),
    }

    def sort_key(item):

        if (
            item.display_date
            and item.display_time
        ):

            return datetime.combine(
                item.display_date,
                item.display_time,
            )

        if item.display_date:

            return datetime.combine(
                item.display_date,
                datetime.min.time(),
            )

        return datetime.min


    history.sort(
        key=sort_key,
        reverse=True,
    )

    paginator = Paginator(
        history,
        10,
    )

    page_number = request.GET.get(
        "page"
    )

    appointments_page = (
        paginator.get_page(
            page_number
        )
    )

    context = {

        "appointments": appointments_page,

        "status_counts": status_counts,

        "current_status": status_filter,

        "search_query": search_query,

        "page_title": "Medical History",
    }

    return render(
        request,
        "luna/staff_medical_history.html",
        context,
    )


@login_required
def staff_cancel_appointment(request, uuid):
    appointment = get_object_or_404(
        Appointment,
        uuid=uuid,
        user=request.user,
    )

    if appointment.status != "PENDING":

        messages.error(
            request,
            "Appointment cannot be cancelled."
        )

        return redirect(
            "staff_medical_history"
        )

    expiry_time = (
        appointment.created_at
        + timedelta(minutes=10)
    )

    if timezone.now() >= expiry_time:

        messages.error(
            request,
            "Cancellation time has expired."
        )

        return redirect(
            "staff_medical_history"
        )

    appointment.status = "CANCELLED"

    appointment.save(
        update_fields=["status"]
    )

    messages.success(
        request,
        "Appointment cancelled successfully."
    )

    return redirect(
        "staff_medical_history"
    )