import json
from types import SimpleNamespace
from calendar import monthrange, Calendar
from datetime import date, datetime, time as dtime, timedelta
from django.views.generic import TemplateView, View
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from django.http import JsonResponse
from django.core.exceptions import ValidationError as DjangoValidationError
from Admin.models import User
from Admin.Dominic.models import Notification
from Medical.Dominic.forms import (
    AssignMedicalStaffForm, MedicalStaffRoleForm, ShiftForm, ShiftAssignmentForm, ShiftAssignmentEditForm,
    _hospital_room_queryset, _reporting_staff_queryset,
)
from Medical.models import ( MedicalStaffProfile, MedicalStaffRole, Shift, ShiftAssignment, DailyNote, Appointment, LaboratoryTest, MedicalDepartment, MedicalCenter, PushSubscription, Facility)
from PermissionAccess.mixins import PageAccessMixin, PermissionRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from Admin.bela_admin.models import Room, RoomPurposeAllocation

WEEKDAY_CODES = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

class MedicalStaffDashboardView(LoginRequiredMixin, PageAccessMixin, TemplateView):
    page_key = "medical_staff_dashboard"
    shared_with_user_roles = True
    template_name = "Dominic/medical_staff_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.localdate()
        today_code = WEEKDAY_CODES[today.weekday()]
        month_start = today.replace(day=1)

        is_admin_view = bool(getattr(user, "is_administrator", False))
        staff_profile = MedicalStaffProfile.objects.filter(user=user).select_related(
            "department", "role"
        ).first()

        if is_admin_view or not staff_profile:
            department_filter = Q()
        else:
            department_filter = Q(department=staff_profile.department)

        staff_qs = MedicalStaffProfile.objects.filter(is_active=True).filter(department_filter)

        total_staff = staff_qs.count()
        todays_entries = _build_calendar_entries(department_filter, today, today).get(today, [])
        on_duty_today = len({e.medical_staff_id for e in todays_entries})

        month_days_count = monthrange(today.year, today.month)[1]
        cal_month_start = today.replace(day=1)
        cal_month_end = today.replace(day=month_days_count)
        month_entries_by_date = _build_calendar_entries(department_filter, cal_month_start, cal_month_end)
        active_staff_list = list(staff_qs.select_related("user", "role"))

        unassigned_calendar_days = []
        for day_date in Calendar(firstweekday=0).itermonthdates(today.year, today.month):
            in_month = day_date.month == today.month
            unassigned_members = []
            if in_month:
                covered_ids = {e.medical_staff_id for e in month_entries_by_date.get(day_date, [])}
                unassigned_members = [m for m in active_staff_list if m.pk not in covered_ids]
            unassigned_calendar_days.append({
                "date": day_date,
                "in_month": in_month,
                "is_today": day_date == today,
                "unassigned_staff": unassigned_members,
                "unassigned_count": len(unassigned_members),
            })
        on_leave_count = staff_qs.filter(status__in=["ON_LEAVE", "OFF_DUTY"]).count()
        total_roles = MedicalStaffRole.objects.filter(is_active=True).count()
        departments_covered = staff_qs.values("department").distinct().count()
        new_staff_this_month = staff_qs.filter(created_at__date__gte=month_start).count()

        todays_schedule = sorted(todays_entries, key=lambda e: e.start_time)[:10]

        recent_staff = staff_qs.select_related(
            "user", "role", "department"
        ).order_by("-created_at")[:8]

        appointments_qs = Appointment.objects.filter(department_filter)
        appointments_today = appointments_qs.filter(appointment_date=today).count()
        emergency_count = appointments_qs.filter(
            priority="EMERGENCY",
            status__in=["PENDING", "CONFIRMED", "CHECKED_IN", "IN_PROGRESS"],
        ).count()

        if is_admin_view or not staff_profile:
            labs_qs = LaboratoryTest.objects.all()
        else:
            labs_qs = LaboratoryTest.objects.filter(medical_visit__department=staff_profile.department)

        pending_labs = labs_qs.filter(status__in=["REQUESTED", "COLLECTED", "PROCESSING"]).count()

        dept_base = MedicalDepartment.objects.filter(is_active=True)
        if not is_admin_view and staff_profile:
            dept_base = dept_base.filter(pk=staff_profile.department_id)

        department_stats = []
        for dept in dept_base:
            dept_staff = staff_qs.filter(department=dept)
            department_stats.append({
                "department_name": dept.department_name,
                "total_staff": dept_staff.count(),
                "on_duty_today": len({e.medical_staff_id for e in todays_entries if e.department_id == dept.pk}),
                "doctors": dept_staff.filter(role__category="DOCTOR").count(),
                "nurses": dept_staff.filter(role__category="NURSE").count(),
                "physio": dept_staff.filter(role__category="PHYSIO").count(),
                "lab_techs": dept_staff.filter(role__category="LAB").count(),
            })

        department_staff = staff_qs.exclude(user=user).select_related(
            "user", "role", "department"
        ).order_by("user__first_name")

        todays_schedule_map = {e.medical_staff_id: e for e in todays_entries}
        for member in department_staff:
            member.todays_shift = todays_schedule_map.get(member.pk)

        role_counts = staff_qs.values("role__name").annotate(total=Count("id")).order_by("-total")
        role_labels = [row["role__name"] or "Unassigned" for row in role_counts]
        role_values = [row["total"] for row in role_counts]

        employment_display_map = dict(MedicalStaffProfile.EMPLOYMENT_TYPES)
        employment_counts = staff_qs.values("employment_type").annotate(total=Count("id")).order_by("-total")
        employment_labels = [employment_display_map.get(row["employment_type"], row["employment_type"]) for row in employment_counts]
        employment_values = [row["total"] for row in employment_counts]

        month_labels = []
        month_counts = []
        for i in range(5, -1, -1):
            year, month = today.year, today.month - i
            while month <= 0:
                month += 12
                year -= 1
            month_start_i = date(year, month, 1)
            month_end_i = date(year, month, monthrange(year, month)[1])
            month_labels.append(month_start_i.strftime("%b"))
            month_counts.append(
                staff_qs.filter(created_at__date__gte=month_start_i, created_at__date__lte=month_end_i).count()
            )

        medical_staff_roles = MedicalStaffRole.objects.filter(is_active=True).annotate(
            staff_count=Count("staff_members", filter=Q(staff_members__is_active=True))
        ).order_by("name")

        context.update({
            "is_admin_view": is_admin_view,
            "staff_profile": staff_profile,

            "total_staff": total_staff,
            "on_duty_today": on_duty_today,
            "on_leave_count": on_leave_count,
            "total_roles": total_roles,
            "departments_covered": departments_covered,
            "new_staff_this_month": new_staff_this_month,

            "appointments_today": appointments_today,
            "emergency_count": emergency_count,
            "pending_labs": pending_labs,

            "todays_schedule": todays_schedule,
            "recent_staff": recent_staff,
            "department_stats": department_stats,
            "department_staff": department_staff,

            "role_labels_json": json.dumps(role_labels),
            "role_values_json": json.dumps(role_values),
            "employment_labels_json": json.dumps(employment_labels),
            "employment_values_json": json.dumps(employment_values),
            "month_labels_json": json.dumps(month_labels),
            "month_counts_json": json.dumps(month_counts),

            "medical_staff_role_form": MedicalStaffRoleForm(), 
            "medical_staff_roles": medical_staff_roles,

            "unassigned_calendar_days": unassigned_calendar_days,
            "unassigned_month_label": today.strftime("%B %Y"),
        })
        return context

class AssignMedicalStaffView(LoginRequiredMixin, PageAccessMixin, PermissionRequiredMixin, View):
    page_key = "assign_medical_staff"
    shared_with_user_roles = True
    permission_required = "medicalstaffprofile_create"
    template_name = "Dominic/assign_medical_staff.html"

    def _build_staff_directory(self):
        users = (
            User.objects.filter(is_staff=True, medical_staff_profile__isnull=True)
            .exclude(is_superuser=True)
            .exclude(medical_centers__isnull=False)
            .select_related("staff_profile")
            .prefetch_related("staff_profile__emergency_contacts")
            .order_by("first_name")
        )

        directory = {}
        for u in users:
            sp = getattr(u, "staff_profile", None)

            employee_id = ""
            work_email = ""
            emergency_contact_name = ""
            emergency_contact_phone = ""

            if sp:
                employee_id = sp.employee_id or ""
                work_email = sp.work_email or ""
                emergency = sp.emergency_contacts.first()
                if emergency:
                    emergency_contact_name = emergency.contact_name or ""
                    emergency_contact_phone = emergency.phone_number or ""

            directory[str(u.pk)] = {
                "full_name": u.full_name,
                "username": u.username,
                "email": u.email or "",
                "phone": u.mobile_number or "",
                "university_id": u.university_id or "",
                "employee_id": employee_id,
                "work_email": work_email,
                "emergency_contact_name": emergency_contact_name,
                "emergency_contact_phone": emergency_contact_phone,
            }

        return users, directory

    def get(self, request, *args, **kwargs):
        category = request.GET.get("category") or None
        form = AssignMedicalStaffForm(category=category)
        assignable_staff_users, staff_directory = self._build_staff_directory()

        return render(request, self.template_name, {
            "assign_medical_staff_form": form,
            "assignable_staff_users": assignable_staff_users,
            "staff_directory": staff_directory,
            "category": category or "",
            "category_display": dict(MedicalStaffRole.CATEGORY_CHOICES).get(category, category or ""),
        })

    def post(self, request, *args, **kwargs):
        category = request.POST.get("category") or None
        form = AssignMedicalStaffForm(request.POST, category=category)

        if form.is_valid():
            profile = form.save()
            messages.success(
                request,
                f"{profile.user.full_name} has been assigned as {profile.role.name} "
                f"in {profile.department.department_name} at {profile.hospital.hospital_name}."
            )
            return redirect(reverse("Medical:medical_staff_dashboard"))

        messages.error(request, "Please fix the highlighted errors and try again.")
        assignable_staff_users, staff_directory = self._build_staff_directory()
        return render(request, self.template_name, {
            "assign_medical_staff_form": form,
            "assignable_staff_users": assignable_staff_users,
            "staff_directory": staff_directory,
            "category": category or "",
            "category_display": dict(MedicalStaffRole.CATEGORY_CHOICES).get(category, category or ""),
        })

class MedicalStaffRoleCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "medicalstaffrole_create"
    def post(self, request, *args, **kwargs):
        form = MedicalStaffRoleForm(request.POST)

        if form.is_valid():
            role = form.save()
            messages.success(request, f"Medical role '{role.name}' created successfully.")
            return redirect(reverse("Medical:medical_staff_dashboard"))

        messages.error(request, "Please fix the highlighted errors and try again.")
        dashboard_view = MedicalStaffDashboardView()
        dashboard_view.request = request
        context = dashboard_view.get_context_data()
        context["medical_staff_role_form"] = form
        context["open_role_modal"] = True
        return render(request, dashboard_view.template_name, context)

def _is_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"

def _form_errors_json(form):
    data = form.errors.get_json_data()
    return {field: [item["message"] for item in items] for field, items in data.items()}

def _validation_error_json(exc):
    if hasattr(exc, "message_dict"):
        return {field: list(msgs) for field, msgs in exc.message_dict.items()}
    return {"__all__": list(exc.messages)}

def _shift_department_filter(user):
    is_admin_view = bool(getattr(user, "is_administrator", False))
    staff_profile = MedicalStaffProfile.objects.filter(user=user).select_related("department", "role", "hospital").first()

    if is_admin_view or not staff_profile:
        return Q(), staff_profile, is_admin_view

    scope = Q(department=staff_profile.department)
    if staff_profile.hospital_id:
        scope &= Q(hospital_id=staff_profile.hospital_id)
    return scope, staff_profile, is_admin_view 

class DepartmentsByHospitalView(LoginRequiredMixin, View):
    def get(self, request, hospital_id, *args, **kwargs):
        hospital = MedicalCenter.objects.filter(pk=hospital_id).first()

        via_center = list(MedicalDepartment.objects.filter(is_active=True, medicalcenter__id=hospital_id).values_list("pk", "department_name"))
        via_m2m = list(MedicalDepartment.objects.filter(is_active=True, hospitals__id=hospital_id).values_list("pk", "department_name"))
        via_staff = list(MedicalDepartment.objects.filter(is_active=True, staff_members__hospital_id=hospital_id, staff_members__is_active=True).values_list("pk", "department_name"))

        department_ids = list(
            MedicalDepartment.objects.filter(is_active=True).filter(
                Q(medicalcenter__id=hospital_id) |
                Q(hospitals__id=hospital_id) |
                Q(staff_members__hospital_id=hospital_id, staff_members__is_active=True)
            ).values_list("pk", flat=True).distinct()
        )
        return JsonResponse({
            "department_ids": department_ids,
            "debug": {
                "hospital_id": hospital_id,
                "hospital_found": bool(hospital),
                "hospital_department_id": getattr(hospital, "department_id", None),
                "via_medicalcenter_department": via_center,
                "via_hospitals_m2m": via_m2m,
                "via_staff_members": via_staff,
            },
        })

class HospitalWorkingHoursView(LoginRequiredMixin, View):
    def get(self, request, hospital_id, *args, **kwargs):
        hospital = MedicalCenter.objects.filter(pk=hospital_id).first()
        if not hospital:
            return JsonResponse({"found": False}, status=404)

        working_hours = hospital.working_hours or {}
        return JsonResponse({
            "found": True,
            "hospital_id": hospital.pk,
            "hospital_name": hospital.hospital_name,
            "weekly_schedule": working_hours.get("weekly_schedule", {}),
            "overrides": working_hours.get("overrides", {}),
        })

class ReportingStaffOptionsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        hospital = MedicalCenter.objects.filter(pk=request.GET.get("hospital")).first()
        role = MedicalStaffRole.objects.filter(pk=request.GET.get("role")).first()
        is_senior = request.GET.get("is_senior") in ("1", "true", "True", "on")

        if role and role.category == "DOCTOR" and is_senior:
            director = getattr(hospital, "director_name", None) if hospital else None
            return JsonResponse({
                "mode": "director",
                "director": {"id": director.pk, "name": director.full_name} if director else None,
                "options": [],
            })

        qs = _reporting_staff_queryset(hospital, role.category if role else None, is_senior)
        options = [
            {"id": sp.pk, "name": sp.user.full_name, "role": sp.role.name}
            for sp in qs
        ]
        return JsonResponse({"mode": "list", "director": None, "options": options})


class HospitalFacilitiesView(LoginRequiredMixin, View):
    def get(self, request, hospital_id, *args, **kwargs):
        hospital = MedicalCenter.objects.filter(pk=hospital_id).first()
        if not hospital:
            return JsonResponse({"facilities": []})

        facility_ids = list(hospital.selected_facilities or []) + list(hospital.selected_other_facilities or [])
        facilities = Facility.objects.filter(pk__in=facility_ids, is_active=True)
        data = [
            {
                "id": f.pk,
                "name": f.name,
                "icon": f.icon,
                "type": f.facility_type,
                "is_available": f.is_available,
            }
            for f in facilities
        ]
        return JsonResponse({"facilities": data})

class ShiftManagementView(LoginRequiredMixin, PageAccessMixin, TemplateView):
    page_key = "medical_shift_management"
    shared_with_user_roles = True
    template_name = "Dominic/shift_management.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        dept_filter, staff_profile, is_admin_view = _shift_department_filter(user)

        shifts = Shift.objects.filter(dept_filter).select_related(
            "department", "created_by", "hospital"
        ).annotate(
            assigned_room_count=Count("assignments__room", distinct=True)
        ).order_by("-start_date", "start_time")

        context.update({
            "is_admin_view": is_admin_view,
            "staff_profile": staff_profile,
            "shifts": shifts,
            "shift_form": ShiftForm(user=user),
            "today": timezone.localdate(),
        })
        return context

class ShiftCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "shift_create"

    def post(self, request, *args, **kwargs):
        form = ShiftForm(request.POST, user=request.user)
        ajax = _is_ajax(request)

        if not form.is_valid():
            if ajax:
                return JsonResponse({"success": False, "errors": _form_errors_json(form)}, status=400)
            messages.error(request, "Please fix the highlighted errors and try again.")
            return redirect(reverse("Medical:shift_management"))

        shift = form.save(commit=False)
        shift.created_by = request.user
        shift.weekday_pattern = form.cleaned_data["weekday_pattern"]
        try:
            shift.full_clean()
            shift.save()
        except DjangoValidationError as e:
            errors = _validation_error_json(e)
            if ajax:
                return JsonResponse({"success": False, "errors": errors}, status=400)
            flat = "; ".join(msg for msgs in errors.values() for msg in msgs)
            messages.error(request, f"Could not create shift: {flat}")
            return redirect(reverse("Medical:shift_management"))
        except Exception as e:
            if ajax:
                return JsonResponse({"success": False, "errors": {"__all__": [str(e)]}}, status=400)
            messages.error(request, f"Could not create shift: {e}")
            return redirect(reverse("Medical:shift_management"))

        hospital_part = f" at {shift.hospital.hospital_name}" if shift.hospital_id else ""
        success_message = (
            f"{shift.shift_label} shift created for "
            f"{shift.department.department_name}{hospital_part} ({shift.start_date} to {shift.end_date})."
        )
        if ajax:
            return JsonResponse({"success": True, "message": success_message, "shift_id": shift.pk})
        messages.success(request, success_message)
        return redirect(reverse("Medical:shift_management"))

class ShiftUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "shift_update"

    def get_object(self, request, pk):
        dept_filter, _, _ = _shift_department_filter(request.user)
        return get_object_or_404(Shift.objects.filter(dept_filter), pk=pk)

    def get(self, request, pk, *args, **kwargs):
        shift = self.get_object(request, pk)
        return JsonResponse({
            "id": shift.pk,
            "hospital": shift.hospital_id,
            "department": shift.department_id,
            "shift_label": shift.shift_label,
            "shift_type": shift.shift_type,
            "start_time": shift.start_time.strftime("%H:%M"),
            "end_time": shift.end_time.strftime("%H:%M"),
            "recurrence_type": shift.recurrence_type,
            "start_date": shift.start_date.isoformat(),
            "end_date": shift.end_date.isoformat(),
            "weekday_pattern": shift.active_weekdays(),
        })

    def post(self, request, pk, *args, **kwargs):
        shift = self.get_object(request, pk)
        form = ShiftForm(request.POST, instance=shift, user=request.user)
        ajax = _is_ajax(request)

        if not form.is_valid():
            if ajax:
                return JsonResponse({"success": False, "errors": _form_errors_json(form)}, status=400)
            messages.error(request, "Please fix the highlighted errors and try again.")
            return redirect(reverse("Medical:shift_management"))

        try:
            form.save()
        except DjangoValidationError as e:
            errors = _validation_error_json(e)
            if ajax:
                return JsonResponse({"success": False, "errors": errors}, status=400)
            flat = "; ".join(msg for msgs in errors.values() for msg in msgs)
            messages.error(request, f"Could not update shift: {flat}")
            return redirect(reverse("Medical:shift_management"))
        except Exception as e:
            if ajax:
                return JsonResponse({"success": False, "errors": {"__all__": [str(e)]}}, status=400)
            messages.error(request, f"Could not update shift: {e}")
            return redirect(reverse("Medical:shift_management"))

        if ajax:
            return JsonResponse({"success": True, "message": "Shift updated successfully."})
        messages.success(request, "Shift updated successfully.")
        return redirect(reverse("Medical:shift_management"))

class ShiftDeleteView(LoginRequiredMixin, View):
    page_key = "medical_shift_management"

    def post(self, request, pk, *args, **kwargs):
        dept_filter, _, _ = _shift_department_filter(request.user)
        shift = get_object_or_404(Shift.objects.filter(dept_filter), pk=pk)
        shift.delete()
        messages.success(request, "Shift removed successfully.")
        return redirect(reverse("Medical:shift_management"))

class ShiftAssignmentsView(LoginRequiredMixin, View):
    page_key = "medical_shift_management"

    def get(self, request, pk, *args, **kwargs):
        dept_filter, _, _ = _shift_department_filter(request.user)
        shift = get_object_or_404(Shift.objects.filter(dept_filter), pk=pk)

        assignments = shift.assignments.select_related(
            "medical_staff__user", "medical_staff__role"
        ).order_by("medical_staff__user__first_name")

        assigned_ids = [a.medical_staff_id for a in assignments]
        available_staff_filter = {"is_active": True, "department": shift.department}
        if shift.hospital_id:
            available_staff_filter["hospital_id"] = shift.hospital_id
        available_staff = MedicalStaffProfile.objects.filter(
            **available_staff_filter
        ).exclude(pk__in=assigned_ids).select_related("user", "role").order_by("user__first_name")

        available_rooms = list(_hospital_room_queryset(shift.hospital))

        return JsonResponse({
            "shift": {
                "id": shift.pk,
                "label": shift.shift_label,
                "type": shift.shift_type,
                "hospital": shift.hospital.hospital_name if shift.hospital_id else "",
                "department": shift.department.department_name,
                "start_date": shift.start_date.isoformat(),
                "end_date": shift.end_date.isoformat(),
                "start_time": shift.start_time.strftime("%H:%M"),
                "end_time": shift.end_time.strftime("%H:%M"),
            },
            "assignments": [
                {
                    "id": a.pk,
                    "full_name": a.medical_staff.user.full_name,
                    "role": a.medical_staff.role.name if a.medical_staff.role else "",
                    "avatar_url": f"https://ui-avatars.com/api/?name={a.medical_staff.user.full_name}&background=c5050c&color=fff&size=64",
                    "room": str(a.room) if a.room_id else "",
                    "room_id": a.room_id or "",
                    "start_date": a.assignment_start_date.isoformat(),
                    "end_date": a.assignment_end_date.isoformat(),
                } for a in assignments
            ],
            "available_staff": [
                {
                    "id": s.pk,
                    "full_name": s.user.full_name,
                    "role": s.role.name if s.role else "",
                    "avatar_url": f"https://ui-avatars.com/api/?name={s.user.full_name}&background=c5050c&color=fff&size=64",
                } for s in available_staff
            ],
            "available_rooms": [
                {"id": r.pk, "name": str(r)} for r in available_rooms
            ],
        })

class ShiftAssignmentCreateView(LoginRequiredMixin, View):
    page_key = "medical_shift_management"

    def post(self, request, pk, *args, **kwargs):
        dept_filter, _, _ = _shift_department_filter(request.user)
        shift = get_object_or_404(Shift.objects.filter(dept_filter), pk=pk)

        form = ShiftAssignmentForm(request.POST, shift=shift)
        if form.is_valid():
            created, skipped = form.save(assigned_by=request.user, post_data=request.POST)
            if created:
                messages.success(request, f"{len(created)} staff member(s) assigned to this shift.")
                for assignment in created:
                    Notification.objects.create(
                        notification_type="SCHEDULE",
                        recipient=assignment.medical_staff.user,
                        schedule=shift,
                        event="shift_assigned",
                        message=(
                            f"You've been assigned to {shift.shift_label} "
                            f"({shift.start_time.strftime('%I:%M %p')}–{shift.end_time.strftime('%I:%M %p')}) "
                            f"starting {assignment.assignment_start_date.strftime('%b %d, %Y')}."
                        ),
                        icon="calendar-check",
                        link_url=reverse("Medical:my_shifts"),
                    )
            if skipped:
                messages.warning(request, f"{len(skipped)} staff member(s) could not be assigned (already assigned or invalid).")
        else:
            flat_errors = [m["message"] for msgs in form.errors.get_json_data().values() for m in msgs]
            messages.error(request, "; ".join(flat_errors) if flat_errors else "Please fix the highlighted errors and try again.")
        return redirect(reverse("Medical:shift_management"))

class ShiftAssignmentUpdateView(LoginRequiredMixin, View):
    page_key = "medical_shift_management"

    def _get_assignment(self, request, pk):
        dept_filter, _, _ = _shift_department_filter(request.user)
        assignment = get_object_or_404(ShiftAssignment, pk=pk)
        if not Shift.objects.filter(dept_filter, pk=assignment.shift_id).exists():
            return None
        return assignment

    def post(self, request, pk, *args, **kwargs):
        assignment = self._get_assignment(request, pk)
        if assignment is None:
            messages.error(request, "You do not have permission to modify this assignment.")
            return redirect(reverse("Medical:shift_management"))

        form = ShiftAssignmentEditForm(request.POST, instance=assignment)
        if form.is_valid():
            try:
                updated = form.save(commit=False)
                updated.full_clean()
                updated.save()
                messages.success(request, "Coverage dates updated successfully.")
            except Exception as e:
                messages.error(request, f"Could not update: {e}")
        else:
            messages.error(request, "Please fix the highlighted errors and try again.")
        return redirect(reverse("Medical:shift_management"))

class ShiftAssignmentDeleteView(LoginRequiredMixin, View):
    page_key = "medical_shift_management"

    def post(self, request, pk, *args, **kwargs):
        dept_filter, _, _ = _shift_department_filter(request.user)
        assignment = get_object_or_404(ShiftAssignment, pk=pk)
        if not Shift.objects.filter(dept_filter, pk=assignment.shift_id).exists():
            messages.error(request, "You do not have permission to modify this assignment.")
            return redirect(reverse("Medical:shift_management"))

        assignment.delete()
        messages.success(request, "Staff removed from shift.")
        return redirect(reverse("Medical:shift_management"))

def _build_calendar_entries(dept_filter, range_start, range_end):
    weekday_map = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

    shifts = Shift.objects.filter(
        dept_filter, start_date__lte=range_end, end_date__gte=range_start
    ).select_related("department").prefetch_related(
        "assignments__medical_staff__user", "assignments__medical_staff__role", "assignments__room"
    )

    entries_by_date = {}
    day_cursor = range_start
    while day_cursor <= range_end:
        entries_by_date[day_cursor] = []
        day_cursor += timedelta(days=1)

    for shift in shifts:
        active_codes = set(shift.active_weekdays())
        assignments = [a for a in shift.assignments.all() if a.medical_staff.is_active]
 
        day = max(shift.start_date, range_start)
        last = min(shift.end_date, range_end)
        while day <= last:
            if weekday_map[day.weekday()] in active_codes:
                for a in assignments:
                    if a.assignment_start_date <= day <= a.assignment_end_date:
                        entries_by_date[day].append(SimpleNamespace(
                            medical_staff_id=a.medical_staff_id,
                            medical_staff=a.medical_staff,
                            department=shift.department,
                            department_id=shift.department_id,
                            hospital=shift.hospital,
                            room=a.room,
                            start_time=shift.start_time,
                            end_time=shift.end_time,
                            shift=shift,
                            shift_label=shift.shift_label,
                            color_class=shift.color_class(),
                            get_shift_display=(lambda sl=shift.shift_label: sl),
                        ))
            day += timedelta(days=1)
 
    return entries_by_date

class StaffScheduleView(LoginRequiredMixin, PageAccessMixin, TemplateView):
    page_key = "medical_staff_schedule"
    shared_with_user_roles = True
    template_name = "Dominic/staff_schedule.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        dept_filter, staff_profile, is_admin_view = _shift_department_filter(user)

        today = timezone.localdate()
        try:
            year = int(self.request.GET.get("year", today.year))
            month = int(self.request.GET.get("month", today.month))
        except (TypeError, ValueError):
            year, month = today.year, today.month

        view_mode = self.request.GET.get("view", "calendar")

        days_in_month = monthrange(year, month)[1]
        month_start = date(year, month, 1)
        month_end = date(year, month, days_in_month)
        prev_month = (month_start - timedelta(days=1)).replace(day=1)
        next_month = (month_end + timedelta(days=1))

        entries_by_date = _build_calendar_entries(dept_filter, month_start, month_end)

        calendar_days = []
        list_entries = []

        for day_date in Calendar(firstweekday=0).itermonthdates(year, month):
            in_month = day_date.month == month
            day_entries = sorted(entries_by_date.get(day_date, []), key=lambda e: e.start_time) if in_month else []

            if in_month and view_mode == "list":
                for entry in day_entries:
                    list_entries.append((day_date, entry))

            calendar_days.append({
                "date": day_date,
                "in_month": in_month,
                "is_today": day_date == today,
                "entries": day_entries,
            })

        context.update({
            "is_admin_view": is_admin_view,
            "staff_profile": staff_profile,
            "view_mode": view_mode,
            "current_year": year,
            "current_month": month,
            "month_name": month_start.strftime("%B %Y"),
            "prev_month_year": prev_month.year,
            "prev_month_month": prev_month.month,
            "next_month_year": next_month.year,
            "next_month_month": next_month.month,
            "calendar_days": calendar_days,
            "list_entries": list_entries,
        })
        return context

class MyShiftsView(LoginRequiredMixin, TemplateView):
    template_name = "Dominic/my_shifts.html"

    def get(self, request, *args, **kwargs):
        if getattr(request.user, "is_administrator", False):
            messages.info(request, "Administrators don't have a personal shift schedule.")
            return redirect(reverse("Medical:medical_staff_dashboard"))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        dept_filter, staff_profile, _ = _shift_department_filter(user)

        today = timezone.localdate()

        if staff_profile:
            DailyNote.objects.filter(staff=staff_profile, date__lt=today).delete()

        try:
            year = int(self.request.GET.get("year", today.year))
            month = int(self.request.GET.get("month", today.month))
        except (TypeError, ValueError):
            year, month = today.year, today.month

        view_mode = self.request.GET.get("view", "calendar")

        days_in_month = monthrange(year, month)[1]
        month_start = date(year, month, 1)
        month_end = date(year, month, days_in_month)
        prev_month = (month_start - timedelta(days=1)).replace(day=1)
        next_month = (month_end + timedelta(days=1))

        entries_by_date = _build_calendar_entries(dept_filter, month_start, month_end)

        if staff_profile:
            for day_date, entries in entries_by_date.items():
                entries_by_date[day_date] = [e for e in entries if e.medical_staff_id == staff_profile.pk]
        else:
            entries_by_date = {d: [] for d in entries_by_date}

        notes_by_date = {}
        if staff_profile:
            notes_by_date = {
                n.date: n for n in DailyNote.objects.filter(
                    staff=staff_profile, date__gte=month_start, date__lte=month_end
                )
            }

        calendar_days = []
        list_entries = []

        for day_date in Calendar(firstweekday=0).itermonthdates(year, month):
            in_month = day_date.month == month
            day_entries = sorted(entries_by_date.get(day_date, []), key=lambda e: e.start_time) if in_month else []
            day_note = notes_by_date.get(day_date) if in_month else None

            if in_month and view_mode == "list":
                for entry in day_entries:
                    list_entries.append((day_date, entry))

            calendar_days.append({
                "date": day_date,
                "in_month": in_month,
                "is_today": day_date == today,
                "is_past": day_date < today,
                "entries": day_entries,
                "note": day_note,
            })

        context.update({
            "staff_profile": staff_profile,
            "view_mode": view_mode,
            "current_year": year,
            "current_month": month,
            "month_name": month_start.strftime("%B %Y"),
            "prev_month_year": prev_month.year,
            "prev_month_month": prev_month.month,
            "next_month_year": next_month.year,
            "next_month_month": next_month.month,
            "calendar_days": calendar_days,
            "list_entries": list_entries,
            "vapid_public_key": settings.VAPID_PUBLIC_KEY,
        })
        return context

class DailyNoteSaveView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        staff_profile = MedicalStaffProfile.objects.filter(user=request.user).first()
        if not staff_profile:
            return JsonResponse({"success": False, "error": "No staff profile found for this account."}, status=400)

        date_str = (request.POST.get("date") or "").strip()
        note_text = (request.POST.get("note_text") or "").strip()
        event_time_str = (request.POST.get("event_time") or "").strip()
        offset_str = (request.POST.get("reminder_offset_minutes") or "").strip()

        if not date_str or not note_text:
            return JsonResponse({"success": False, "error": "Date and note text are required."}, status=400)

        try:
            note_date = date.fromisoformat(date_str)
        except ValueError:
            return JsonResponse({"success": False, "error": "Invalid date."}, status=400)

        if note_date < timezone.localdate():
            return JsonResponse({"success": False, "error": "Can't add or edit a note on a past date."}, status=400)

        event_time_val = None
        offset_val = None
        if offset_str:
            if not event_time_str:
                return JsonResponse({"success": False, "error": "Set an event time to attach a reminder."}, status=400)
            try:
                hour, minute = (int(part) for part in event_time_str.split(":")[:2])
                event_time_val = dtime(hour, minute)
            except (ValueError, TypeError):
                return JsonResponse({"success": False, "error": "Invalid event time."}, status=400)
            try:
                offset_val = int(offset_str)
            except ValueError:
                return JsonResponse({"success": False, "error": "Invalid reminder option."}, status=400)
            if offset_val not in dict(DailyNote.REMINDER_CHOICES):
                return JsonResponse({"success": False, "error": "Invalid reminder option."}, status=400)

        note, _ = DailyNote.objects.update_or_create(
            staff=staff_profile,
            date=note_date,
            defaults={
                "note_text": note_text,
                "event_time": event_time_val,
                "reminder_offset_minutes": offset_val,
                "reminder_sent": False,
            },
        )
        return JsonResponse({
            "success": True,
            "note": {
                "id": note.pk,
                "date": note.date.isoformat(),
                "note_text": note.note_text,
                "event_time": note.event_time.strftime("%H:%M") if note.event_time else None,
                "reminder_offset_minutes": note.reminder_offset_minutes,
            },
        })

class DailyNoteDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        staff_profile = MedicalStaffProfile.objects.filter(user=request.user).first()
        if not staff_profile:
            return JsonResponse({"success": False, "error": "No staff profile found for this account."}, status=400)

        DailyNote.objects.filter(pk=pk, staff=staff_profile).delete()
        return JsonResponse({"success": True})

class DueRemindersView(LoginRequiredMixin, View):
    SHIFT_REMINDER_MINUTES_BEFORE = 10
    WINDOW_MINUTES = 2

    def get(self, request, *args, **kwargs):
        staff_profile = MedicalStaffProfile.objects.filter(user=request.user).first()
        if not staff_profile:
            return JsonResponse({"notifications": []})

        now = timezone.localtime()
        today = now.date()
        fired = []

        dept_filter, _, _ = _shift_department_filter(request.user)
        todays_entries = _build_calendar_entries(dept_filter, today, today).get(today, [])
        my_entries = [e for e in todays_entries if e.medical_staff_id == staff_profile.pk]

        for entry in my_entries:
            shift_start_dt = timezone.make_aware(datetime.combine(today, entry.start_time))
            remind_at = shift_start_dt - timedelta(minutes=self.SHIFT_REMINDER_MINUTES_BEFORE)
            if remind_at <= now <= remind_at + timedelta(minutes=self.WINDOW_MINUTES):
                already_sent = Notification.objects.filter(
                    recipient=request.user, schedule=entry.shift, event="shift_reminder",
                    created_at__date=today,
                ).exists()
                if not already_sent:
                    notif = Notification.objects.create(
                        notification_type="SCHEDULE",
                        recipient=request.user,
                        schedule=entry.shift,
                        event="shift_reminder",
                        message=f"Your {entry.shift_label} shift starts at {entry.start_time.strftime('%I:%M %p')}.",
                        icon="clock",
                        link_url=reverse("Medical:my_shifts"),
                    )
                    fired.append(notif)

        candidate_notes = DailyNote.objects.filter(
            staff=staff_profile, date=today, reminder_sent=False,
            event_time__isnull=False, reminder_offset_minutes__isnull=False,
        )
        for note in candidate_notes:
            remind_at = note.reminder_datetime
            if remind_at is None:
                continue
            remind_at = timezone.make_aware(remind_at)
            if remind_at <= now <= remind_at + timedelta(minutes=self.WINDOW_MINUTES):
                notif = Notification.objects.create(
                    notification_type="SCHEDULE",
                    recipient=request.user,
                    event="note_reminder",
                    message=note.note_text[:255],
                    icon="sticky-note",
                    link_url=reverse("Medical:my_shifts"),
                )
                note.reminder_sent = True
                note.save(update_fields=["reminder_sent"])
                fired.append(notif)

        DailyNote.objects.filter(staff=staff_profile, date__lt=today).delete()

        return JsonResponse({
            "notifications": [
                {"id": n.pk, "message": n.message, "icon": n.icon, "event": n.event, "link_url": n.link_url}
                for n in fired
            ]
        })

class SavePushSubscriptionView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return JsonResponse({"success": False, "error": "Invalid payload."}, status=400)

        endpoint = (payload.get("endpoint") or "").strip()
        keys = payload.get("keys") or {}
        p256dh = (keys.get("p256dh") or "").strip()
        auth = (keys.get("auth") or "").strip()

        if not endpoint or not p256dh or not auth:
            return JsonResponse({"success": False, "error": "Incomplete subscription."}, status=400)

        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                "user": request.user,
                "p256dh": p256dh,
                "auth": auth,
                "user_agent": request.META.get("HTTP_USER_AGENT", "")[:255],
            },
        )
        return JsonResponse({"success": True})

class RemovePushSubscriptionView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            payload = {}
        endpoint = (payload.get("endpoint") or "").strip()
        if endpoint:
            PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
        return JsonResponse({"success": True})

class NotificationListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by("-created_at")[:20]

        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()

        return JsonResponse({
            "unread_count": unread_count,
            "notifications": [
                {
                    "id": n.pk,
                    "message": n.message,
                    "icon": n.icon or "bell",
                    "event": n.event,
                    "link_url": n.link_url,
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat(),
                }
                for n in notifications
            ],
        })

class NotificationMarkReadView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        if str(pk) == "all":
            Notification.objects.filter(
                recipient=request.user,
                is_read=False,
            ).update(is_read=True)
            return JsonResponse({"success": True})

        notif = get_object_or_404(
            Notification.objects.filter(recipient=request.user),
            pk=pk,
        )
        notif.is_read = True
        notif.save(update_fields=["is_read"])
        return JsonResponse({"success": True})