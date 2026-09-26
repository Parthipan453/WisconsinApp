from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta,date,time
from django.contrib import messages
from django.core.paginator import Paginator
from Medical.models import (PatientProfile,PatientRegistration,Appointment,)


# @login_required
# def appointment_history(request):

#     user = request.user

#     student_profile = getattr(
#         user,
#         "student_profile",
#         None
#     )

#     if not student_profile:

#         empty_page = Paginator([], 10).get_page(1)

#         return render(
#             request,
#             "luna/appointment_history.html",
#             {
#                 "appointments": empty_page,

#                 "status_counts": {
#                     "total": 0,
#                     "pending": 0,
#                     "confirmed": 0,
#                     "arrived": 0,
#                     "in_progress": 0,
#                     "completed": 0,
#                     "cancelled": 0,
#                 },

#                 "search_query": "",
#                 "current_status": "",
#             }
#         )
#     patient = (
#         PatientProfile.objects
#         .filter(
#             student=student_profile,
#             patient_type="STUDENT"
#         )
#         .first()
#     )

#     search_query = request.GET.get(
#         "search",
#         ""
#     ).strip()

#     current_status = request.GET.get(
#         "status",
#         ""
#     ).strip().upper()

#     appointment_qs = (
#         Appointment.objects
#         .filter(
#             user=user
#         )
#         .select_related(
#             "patient",

#             "medical_staff",
#             "medical_staff__user",

#             "hospital",
#         )
#         .order_by(
#             "-appointment_date",
#             "-appointment_time",
#         )
#     )

#     if (
#         current_status
#         and current_status != "ALL STATUS"
#     ):

#         appointment_qs = appointment_qs.filter(
#             status=current_status
#         )

#     if search_query:

#         appointment_qs = appointment_qs.filter(

#             Q(
#                 appointment_number__icontains=
#                 search_query
#             )

#             |

#             Q(
#                 reason__icontains=
#                 search_query
#             )

#             |

#             Q(
#                 service__icontains=
#                 search_query
#             )

#             |

#             Q(
#                 medical_staff__user__first_name__icontains=
#                 search_query
#             )

#             |

#             Q(
#                 medical_staff__user__last_name__icontains=
#                 search_query
#             )
#         )

#     registration_map = {}

#     if patient:

#         registrations = (
#             PatientRegistration.objects
#             .filter(
#                 patient=patient
#             )
#             .select_related(
#                 "appointment",

#                 "medical_visit",
#                 "medical_visit__attending_staff",
#                 "medical_visit__attending_staff__user",

#                 "shift_assignment",
#                 "shift_assignment__medical_staff",
#                 "shift_assignment__medical_staff__user",
#             )
#         )

#         for registration in registrations:

#             if registration.appointment_id:

#                 registration_map[
#                     registration.appointment_id
#                 ] = registration

#     history = []

#     for appointment in appointment_qs:

#         registration = registration_map.get(
#             appointment.id
#         )

#         medical_visit = (
#             registration.medical_visit
#             if registration
#             else None
#         )


#         doctor = appointment.medical_staff
#         if (
#             medical_visit
#             and medical_visit.attending_staff
#         ):

#             doctor = medical_visit.attending_staff

#         if (
#             medical_visit
#             and medical_visit.visit_status == "COMPLETED"
#         ):

#             display_status = "COMPLETED"

#         elif registration:

#             if registration.status == "COMPLETED":

#                 display_status = "COMPLETED"

#             elif registration.status == "IN_PROGRESS":

#                 display_status = "IN_PROGRESS"

#             elif registration.status == "CANCELLED":

#                 display_status = "CANCELLED"

#             else:

#                 display_status = appointment.status

#         else:
#             display_status = appointment.status

#         if medical_visit:

#             display_date = medical_visit.visit_date
#             display_time = medical_visit.visit_time

#         else:

#             display_date = appointment.appointment_date
#             display_time = appointment.appointment_time

#         if appointment.reason:

#             display_reason = appointment.reason

#         elif (
#             registration
#             and registration.chief_complaint
#         ):

#             display_reason = (
#                 registration.chief_complaint
#             )

#         elif (
#             medical_visit
#             and medical_visit.chief_complaint
#         ):

#             display_reason = (
#                 medical_visit.chief_complaint
#             )

#         else:

#             display_reason = ""

#         if medical_visit:

#             display_visit_type = (
#                 medical_visit.get_visit_type_display()
#             )

#         else:

#             display_visit_type = ""


#         can_cancel = False
#         remaining_time = None

#         if appointment.status == "PENDING":

#             expiry_time = (
#                 appointment.created_at
#                 + timedelta(minutes=10)
#             )

#             now = timezone.now()

#             if now < expiry_time:

#                 can_cancel = True

#                 seconds = int(
#                     (
#                         expiry_time - now
#                     ).total_seconds()
#                 )

#                 minutes = seconds // 60
#                 seconds = seconds % 60

#                 remaining_time = (
#                     f"{minutes:02d}:{seconds:02d}"
#                 )


#         history.append({

#             "source": "APPOINTMENT",

#             "appointment": appointment,

#             "registration": registration,

#             "medical_visit": medical_visit,

#             "display_number": (
#                 appointment.appointment_number
#                 or "—"
#             ),

#             "display_type": "Appointment",

#             "display_status": display_status,

#             "display_date": display_date,

#             "display_time": display_time,

#             "display_reason": display_reason,

#             "display_doctor": doctor,

#             "display_visit_type": (
#                 display_visit_type
#             ),

#             "display_diagnosis": (
#                 medical_visit.diagnosis
#                 if medical_visit
#                 else None
#             ),

#             "display_treatment": (
#                 medical_visit.treatment
#                 if medical_visit
#                 else None
#             ),

#             "display_medications": (
#                 medical_visit.medications
#                 if medical_visit
#                 else None
#             ),

#             "display_follow_up_required": (
#                 medical_visit.follow_up_required
#                 if medical_visit
#                 else False
#             ),

#             "display_follow_up_date": (
#                 medical_visit.follow_up_date
#                 if medical_visit
#                 else None
#             ),

#             "can_cancel": can_cancel,

#             "remaining_time": remaining_time,
#         })

#     if patient:

#         walkin_qs = (
#             PatientRegistration.objects
#             .filter(
#                 patient=patient,
#                 appointment__isnull=True
#             )
#             .select_related(
#                 "medical_visit",

#                 "medical_visit__attending_staff",
#                 "medical_visit__attending_staff__user",

#                 "shift_assignment",
#                 "shift_assignment__medical_staff",
#                 "shift_assignment__medical_staff__user",
#             )
#             .order_by(
#                 "-registration_date",
#                 "-registration_time",
#             )
#         )

#         for registration in walkin_qs:

#             medical_visit = (
#                 registration.medical_visit
#             )

#             doctor = None

#             if (
#                 medical_visit
#                 and medical_visit.attending_staff
#             ):

#                 doctor = (
#                     medical_visit.attending_staff
#                 )

#             elif registration.shift_assignment:

#                 doctor = (
#                     registration
#                     .shift_assignment
#                     .medical_staff
#                 )

#             history.append({

#                 "source": "WALK_IN",

#                 "appointment": None,

#                 "registration": registration,

#                 "medical_visit": medical_visit,

#                 "display_number": (
#                     f"TK-"
#                     f"{registration.registration_date:%Y%m%d}-"
#                     f"{registration.token_number:03d}"
#                     if registration.token_number is not None
#                     else (
#                         registration.registration_number
#                         or "—"
#                     )
#                 ),

#                 "display_type": "Walk In",

#                 "display_status": (
#                     registration.status
#                 ),

#                 "display_date": (
#                     registration.registration_date
#                 ),

#                 "display_time": (
#                     registration.registration_time
#                 ),

#                 "display_reason": (
#                     registration.chief_complaint
#                     or ""
#                 ),

#                 "display_doctor": doctor,

#                 "display_visit_type": (
#                     medical_visit.get_visit_type_display()
#                     if medical_visit
#                     else ""
#                 ),

#                 "display_diagnosis": (
#                     medical_visit.diagnosis
#                     if medical_visit
#                     else None
#                 ),

#                 "display_treatment": (
#                     medical_visit.treatment
#                     if medical_visit
#                     else None
#                 ),

#                 "display_medications": (
#                     medical_visit.medications
#                     if medical_visit
#                     else None
#                 ),

#                 "display_follow_up_required": (
#                     medical_visit.follow_up_required
#                     if medical_visit
#                     else False
#                 ),

#                 "display_follow_up_date": (
#                     medical_visit.follow_up_date
#                     if medical_visit
#                     else None
#                 ),

#                 "can_cancel": False,

#                 "remaining_time": None,
#             })

#     if search_query:

#         search_lower = search_query.lower()

#         filtered_history = []

#         for item in history:

#             appointment = item.get(
#                 "appointment"
#             )

#             registration = item.get(
#                 "registration"
#             )

#             medical_visit = item.get(
#                 "medical_visit"
#             )

#             values = []

#             if appointment:

#                 values.extend([
#                     appointment.appointment_number,
#                     appointment.reason,
#                     appointment.service,
#                 ])

#             if registration:

#                 values.extend([
#                     registration.registration_number,
#                     registration.chief_complaint,
#                     registration.token_number,
#                 ])

#             if medical_visit:

#                 values.extend([
#                     medical_visit.visit_number,
#                     medical_visit.chief_complaint,
#                     medical_visit.diagnosis,
#                     medical_visit.treatment,
#                     medical_visit.medications,
#                 ])

#             doctor = item.get(
#                 "display_doctor"
#             )

#             if doctor and doctor.user:

#                 values.extend([
#                     doctor.user.first_name,
#                     doctor.user.last_name,
#                 ])

#             values.extend([
#                 item.get("display_number"),
#                 item.get("display_type"),
#                 item.get("display_status"),
#             ])

#             if any(
#                 search_lower in str(
#                     value or ""
#                 ).lower()
#                 for value in values
#             ):

#                 filtered_history.append(item)

#         history = filtered_history

#     status_counts = {

#         "total": len(history),

#         "pending": sum(
#             1
#             for item in history
#             if item["display_status"] == "PENDING"
#         ),

#         "confirmed": sum(
#             1
#             for item in history
#             if item["display_status"] == "CONFIRMED"
#         ),

#         "arrived": sum(
#             1
#             for item in history
#             if item["display_status"] == "ARRIVED"
#         ),

#         "in_progress": sum(
#             1
#             for item in history
#             if item["display_status"] == "IN_PROGRESS"
#         ),

#         "completed": sum(
#             1
#             for item in history
#             if item["display_status"] == "COMPLETED"
#         ),

#         "cancelled": sum(
#             1
#             for item in history
#             if item["display_status"] == "CANCELLED"
#         ),
#     }

#     history.sort(
#         key=lambda item: (
#             item["display_date"]
#             or date.min,

#             item["display_time"]
#             or time.min,
#         ),
#         reverse=True
#     )

#     paginator = Paginator(
#         history,
#         10
#     )

#     page_number = request.GET.get(
#         "page",
#         1
#     )

#     appointments = paginator.get_page(
#         page_number
#     )

#     context = {

#         "appointments": appointments,

#         "status_counts": status_counts,

#         "search_query": search_query,

#         "current_status": current_status,
#     }

#     return render(
#         request,
#         "luna/appointment_history.html",
#         context
#     )

from datetime import date, time, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from Medical.models import (
    PatientProfile,
    PatientRegistration,
    Appointment,
)


# ==========================================================
# STUDENT APPOINTMENT / MEDICAL HISTORY
# ==========================================================

@login_required
def appointment_history(request):

    user = request.user

    # ======================================================
    # GET STUDENT PROFILE
    # ======================================================

    student_profile = getattr(
        user,
        "student_profile",
        None
    )

    # ======================================================
    # EMPTY RESPONSE IF STUDENT PROFILE NOT FOUND
    # ======================================================

    if not student_profile:

        empty_page = Paginator(
            [],
            10
        ).get_page(1)

        return render(
            request,
            "luna/appointment_history.html",
            {
                "appointments": empty_page,

                "status_counts": {
                    "total": 0,
                    "pending": 0,
                    "confirmed": 0,
                    "arrived": 0,
                    "in_progress": 0,
                    "completed": 0,
                    "cancelled": 0,
                },

                "search_query": "",
                "current_status": "",
            }
        )

    # ======================================================
    # GET PATIENT PROFILE
    # ======================================================

    patient = (
        PatientProfile.objects
        .filter(
            student=student_profile,
            patient_type="STUDENT"
        )
        .first()
    )

    # ======================================================
    # FILTER VALUES
    # ======================================================

    search_query = (
        request.GET.get("search", "")
        .strip()
    )

    current_status = (
        request.GET.get("status", "")
        .strip()
        .upper()
    )

    # Normalize "All Status"
    if current_status == "ALL STATUS":
        current_status = ""

    # ======================================================
    # APPOINTMENTS
    #
    # IMPORTANT:
    # DO NOT APPLY STATUS / SEARCH FILTER HERE.
    #
    # Because final display_status can come from:
    #   - Appointment
    #   - PatientRegistration
    #   - MedicalVisit
    #
    # We first build complete history and then filter.
    # ======================================================

    appointment_qs = (
        Appointment.objects
        .filter(
            user=user
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
        )
    )

    # ======================================================
    # REGISTRATION MAP
    # ======================================================

    registration_map = {}

    if patient:

        registrations = (
            PatientRegistration.objects
            .filter(
                patient=patient
            )
            .select_related(
                "appointment",

                "medical_visit",
                "medical_visit__attending_staff",
                "medical_visit__attending_staff__user",

                "shift_assignment",
                "shift_assignment__medical_staff",
                "shift_assignment__medical_staff__user",
            )
        )

        for registration in registrations:

            if registration.appointment_id:

                registration_map[
                    registration.appointment_id
                ] = registration

    # ======================================================
    # COMPLETE HISTORY
    # ======================================================

    history = []

    # ======================================================
    # APPOINTMENT HISTORY
    # ======================================================

    for appointment in appointment_qs:

        registration = registration_map.get(
            appointment.id
        )

        medical_visit = (
            registration.medical_visit
            if registration
            else None
        )

        # --------------------------------------------------
        # DOCTOR
        # --------------------------------------------------

        doctor = appointment.medical_staff

        # If actual visit has attending doctor,
        # use that doctor.
        if (
            medical_visit
            and medical_visit.attending_staff
        ):
            doctor = (
                medical_visit.attending_staff
            )

        # --------------------------------------------------
        # DISPLAY STATUS
        # --------------------------------------------------
        #
        # Priority:
        #
        # 1. Completed medical visit
        # 2. Registration status
        # 3. Appointment status
        #
        # --------------------------------------------------

        if (
            medical_visit
            and medical_visit.visit_status == "COMPLETED"
        ):

            display_status = "COMPLETED"

        elif registration:

            registration_status = (
                registration.status or ""
            ).upper()

            if registration_status == "COMPLETED":

                display_status = "COMPLETED"

            elif registration_status == "IN_PROGRESS":

                display_status = "IN_PROGRESS"

            elif registration_status == "CANCELLED":

                display_status = "CANCELLED"

            elif registration_status == "WAITING":

                display_status = "WAITING"

            elif registration_status == "ARRIVED":

                display_status = "ARRIVED"

            else:

                display_status = (
                    appointment.status or ""
                ).upper()

        else:

            display_status = (
                appointment.status or ""
            ).upper()

        # --------------------------------------------------
        # DISPLAY DATE / TIME
        # --------------------------------------------------

        if medical_visit:

            display_date = (
                medical_visit.visit_date
            )

            display_time = (
                medical_visit.visit_time
            )

        else:

            display_date = (
                appointment.appointment_date
            )

            display_time = (
                appointment.appointment_time
            )

        # --------------------------------------------------
        # DISPLAY REASON
        # --------------------------------------------------

        if appointment.reason:

            display_reason = (
                appointment.reason
            )

        elif (
            registration
            and registration.chief_complaint
        ):

            display_reason = (
                registration.chief_complaint
            )

        elif (
            medical_visit
            and medical_visit.chief_complaint
        ):

            display_reason = (
                medical_visit.chief_complaint
            )

        else:

            display_reason = ""

        # --------------------------------------------------
        # VISIT TYPE
        # --------------------------------------------------

        if medical_visit:

            display_visit_type = (
                medical_visit.get_visit_type_display()
            )

        else:

            display_visit_type = ""

        # --------------------------------------------------
        # CANCEL AVAILABILITY
        # --------------------------------------------------

        can_cancel = False
        remaining_time = None

        if appointment.status == "PENDING":

            expiry_time = (
                appointment.created_at
                + timedelta(minutes=10)
            )

            now = timezone.now()

            if now < expiry_time:

                can_cancel = True

                total_seconds = int(
                    (
                        expiry_time - now
                    ).total_seconds()
                )

                minutes = (
                    total_seconds // 60
                )

                seconds = (
                    total_seconds % 60
                )

                remaining_time = (
                    f"{minutes:02d}:"
                    f"{seconds:02d}"
                )

        # --------------------------------------------------
        # ADD APPOINTMENT HISTORY
        # --------------------------------------------------

        history.append({

            "source": "APPOINTMENT",

            "appointment": appointment,

            "registration": registration,

            "medical_visit": medical_visit,

            "display_number": (
                appointment.appointment_number
                or "—"
            ),

            "display_type": "Appointment",

            "display_status": display_status,

            "display_date": display_date,

            "display_time": display_time,

            "display_reason": display_reason,

            "display_doctor": doctor,

            "display_visit_type": (
                display_visit_type
            ),

            "display_diagnosis": (
                medical_visit.diagnosis
                if medical_visit
                else None
            ),

            "display_treatment": (
                medical_visit.treatment
                if medical_visit
                else None
            ),

            "display_medications": (
                medical_visit.medications
                if medical_visit
                else None
            ),

            "display_follow_up_required": (
                medical_visit.follow_up_required
                if medical_visit
                else False
            ),

            "display_follow_up_date": (
                medical_visit.follow_up_date
                if medical_visit
                else None
            ),

            "can_cancel": can_cancel,

            "remaining_time": remaining_time,
        })

    # ======================================================
    # WALK-IN HISTORY
    # ======================================================

    if patient:

        walkin_qs = (
            PatientRegistration.objects
            .filter(
                patient=patient,
                appointment__isnull=True
            )
            .select_related(
                "medical_visit",

                "medical_visit__attending_staff",
                "medical_visit__attending_staff__user",

                "shift_assignment",
                "shift_assignment__medical_staff",
                "shift_assignment__medical_staff__user",
            )
            .order_by(
                "-registration_date",
                "-registration_time",
            )
        )

        for registration in walkin_qs:

            medical_visit = (
                registration.medical_visit
            )

            # --------------------------------------------------
            # DOCTOR
            # --------------------------------------------------

            doctor = None

            if (
                medical_visit
                and medical_visit.attending_staff
            ):

                doctor = (
                    medical_visit.attending_staff
                )

            elif registration.shift_assignment:

                doctor = (
                    registration
                    .shift_assignment
                    .medical_staff
                )

            # --------------------------------------------------
            # WALK-IN STATUS
            # --------------------------------------------------

            display_status = (
                registration.status or ""
            ).upper()

            # If completed medical visit,
            # show COMPLETED.
            if (
                medical_visit
                and medical_visit.visit_status == "COMPLETED"
            ):
                display_status = "COMPLETED"

            # --------------------------------------------------
            # WALK-IN NUMBER
            # --------------------------------------------------

            if registration.token_number is not None:

                display_number = (
                    f"TK-"
                    f"{registration.registration_date:%Y%m%d}-"
                    f"{registration.token_number:03d}"
                )

            else:

                display_number = (
                    registration.registration_number
                    or "—"
                )

            # --------------------------------------------------
            # VISIT TYPE
            # --------------------------------------------------

            if medical_visit:

                display_visit_type = (
                    medical_visit.get_visit_type_display()
                )

            else:

                display_visit_type = ""

            # --------------------------------------------------
            # ADD WALK-IN HISTORY
            # --------------------------------------------------

            history.append({

                "source": "WALK_IN",

                "appointment": None,

                "registration": registration,

                "medical_visit": medical_visit,

                "display_number": display_number,

                "display_type": "Walk In",

                "display_status": display_status,

                "display_date": (
                    registration.registration_date
                ),

                "display_time": (
                    registration.registration_time
                ),

                "display_reason": (
                    registration.chief_complaint
                    or ""
                ),

                "display_doctor": doctor,

                "display_visit_type": (
                    display_visit_type
                ),

                "display_diagnosis": (
                    medical_visit.diagnosis
                    if medical_visit
                    else None
                ),

                "display_treatment": (
                    medical_visit.treatment
                    if medical_visit
                    else None
                ),

                "display_medications": (
                    medical_visit.medications
                    if medical_visit
                    else None
                ),

                "display_follow_up_required": (
                    medical_visit.follow_up_required
                    if medical_visit
                    else False
                ),

                "display_follow_up_date": (
                    medical_visit.follow_up_date
                    if medical_visit
                    else None
                ),

                "can_cancel": False,

                "remaining_time": None,
            })

    filtered_history = []

    for item in history:

        if current_status:

            item_status = (
                item.get(
                    "display_status",
                    ""
                )
                or ""
            ).upper()

            if item_status != current_status:

                continue


        if search_query:

            search_lower = (
                search_query.lower()
            )

            appointment = item.get(
                "appointment"
            )

            registration = item.get(
                "registration"
            )

            medical_visit = item.get(
                "medical_visit"
            )

            values = []

            if appointment:

                values.extend([
                    appointment.appointment_number,
                    appointment.reason,
                ])

                if appointment.service:

                    values.append(
                        str(
                            appointment.service
                        )
                    )


            if registration:

                values.extend([
                    registration.registration_number,
                    registration.chief_complaint,
                    registration.token_number,
                ])

            if medical_visit:

                values.extend([
                    medical_visit.visit_number,
                    medical_visit.chief_complaint,
                    medical_visit.diagnosis,
                    medical_visit.treatment,
                    medical_visit.medications,
                ])


            doctor = item.get(
                "display_doctor"
            )

            if doctor:

                doctor_user = getattr(
                    doctor,
                    "user",
                    None
                )

                if doctor_user:

                    values.extend([
                        doctor_user.first_name,
                        doctor_user.last_name,
                        doctor_user.get_full_name(),
                    ])

                # Specialization
                specialization = getattr(
                    doctor,
                    "specialization",
                    None
                )

                if specialization:

                    values.append(
                        specialization
                    )

            values.extend([
                item.get("display_number"),
                item.get("display_type"),
                item.get("display_status"),
                item.get("display_visit_type"),
                item.get("display_reason"),
                item.get("display_diagnosis"),
                item.get("display_treatment"),
            ])

            matched = any(
                search_lower in str(
                    value or ""
                ).lower()
                for value in values
            )

            if not matched:

                continue

        filtered_history.append(item)

    history = filtered_history

    history.sort(
        key=lambda item: (
            item.get("display_date")
            or date.min,

            item.get("display_time")
            or time.min,
        ),
        reverse=True
    )

    # ======================================================
    # STATUS COUNTS
    #
    # These counts are based on the filtered history.
    # ======================================================

    status_counts = {

        "total": len(history),

        "pending": sum(
            1
            for item in history
            if item.get("display_status")
            == "PENDING"
        ),

        "confirmed": sum(
            1
            for item in history
            if item.get("display_status")
            == "CONFIRMED"
        ),

        "arrived": sum(
            1
            for item in history
            if item.get("display_status")
            == "ARRIVED"
        ),

        "in_progress": sum(
            1
            for item in history
            if item.get("display_status")
            == "IN_PROGRESS"
        ),

        "completed": sum(
            1
            for item in history
            if item.get("display_status")
            == "COMPLETED"
        ),

        "cancelled": sum(
            1
            for item in history
            if item.get("display_status")
            == "CANCELLED"
        ),
    }

    # ======================================================
    # PAGINATION
    # ======================================================

    paginator = Paginator(
        history,
        10
    )

    page_number = request.GET.get(
        "page",
        1
    )

    appointments = paginator.get_page(
        page_number
    )

    # ======================================================
    # CONTEXT
    # ======================================================

    context = {

        "appointments": appointments,

        "status_counts": status_counts,

        "search_query": search_query,

        "current_status": current_status,
    }

    # ======================================================
    # RENDER
    # ======================================================

    return render(
        request,
        "luna/appointment_history.html",
        context
    )


# ==========================================================
# CANCEL APPOINTMENT
# ==========================================================

@login_required
def cancel_appointment(request, uuid):

    appointment = get_object_or_404(
        Appointment,
        uuid=uuid,
        user=request.user
    )

    # ======================================================
    # STATUS CHECK
    # ======================================================

    if appointment.status != "PENDING":

        messages.error(
            request,
            "Appointment cannot be cancelled."
        )

        return redirect(
            "Student:appointment_history"
        )

    # ======================================================
    # 10 MINUTE CANCELLATION WINDOW
    # ======================================================

    expiry_time = (
        appointment.created_at
        + timedelta(minutes=10)
    )

    if timezone.now() > expiry_time:

        messages.error(
            request,
            "Cancellation time has expired."
        )

        return redirect(
            "Student:appointment_history"
        )

    # ======================================================
    # CANCEL
    # ======================================================

    appointment.status = "CANCELLED"

    appointment.save(
        update_fields=[
            "status"
        ]
    )

    # ======================================================
    # SUCCESS MESSAGE
    # ======================================================

    messages.success(
        request,
        "Appointment cancelled successfully."
    )

    return redirect(
        "Student:appointment_history"
    )


@login_required
def cancel_appointment(request,uuid):

    appointment = get_object_or_404(
        Appointment,
        uuid=uuid,
        user=request.user
    )
    if appointment.status != "PENDING":

        messages.error(
            request,
            "Appointment cannot be cancelled."
        )

        return redirect(
            "Student:appointment_history"
        )

    expiry_time = (
        appointment.created_at
        + timedelta(minutes=10)
    )

    if timezone.now() > expiry_time:

        messages.error(
            request,
            "Cancellation time has expired."
        )

        return redirect(
            "Student:appointment_history"
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
        "Student:appointment_history"
    )


