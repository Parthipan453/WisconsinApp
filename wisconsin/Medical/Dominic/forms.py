from django import forms
from Admin.models import User
from Medical.models import MedicalStaffProfile, MedicalStaffRole, MedicalDepartment, Shift, ShiftAssignment
from Medical.models import MedicalCenter, Facility
from Admin.bela_admin.models import Room, RoomPurposeAllocation


def _hospital_room_queryset(hospital):
    if not hospital:
        return Room.objects.none()

    room_ids = set()
    if hospital.hospital_building_id:
        room_ids.update(
            Room.objects.filter(
                floor__building_id=hospital.hospital_building_id
            ).values_list("id", flat=True)
        )
    room_ids.update(
        RoomPurposeAllocation.objects.filter(
            medical_center_id=hospital.pk
        ).values_list("room_id", flat=True)
    )
    return Room.objects.filter(id__in=room_ids, status="AVAILABLE").order_by("room_number")


def _reporting_staff_queryset(hospital, category, is_senior):
    if not hospital or not category:
        return MedicalStaffProfile.objects.none()

    base = MedicalStaffProfile.objects.filter(
        hospital=hospital, is_active=True, is_senior=True
    ).select_related("user", "role")

    if category == "DOCTOR" and is_senior:
        return MedicalStaffProfile.objects.none()
    if category == "NURSE" and not is_senior:
        return base.filter(role__category="NURSE")
    if category == "DOCTOR" or (category == "NURSE" and is_senior):
        return base.filter(role__category="DOCTOR")
    return base.filter(role__category=category)


class AssignMedicalStaffForm(forms.ModelForm):

    user = forms.ModelChoiceField(
        queryset=User.objects.filter(
            is_staff=True,
            medical_staff_profile__isnull=True,
        ).exclude(is_superuser=True).exclude(medical_centers__isnull=False).order_by("first_name"),
        label="Select Staff User",
        widget=forms.Select(attrs={"id": "id_user", "class": "med-native-select"}),
    )

    hospital = forms.ModelChoiceField(
        queryset=MedicalCenter.objects.filter(is_active=True, hospital_status="active").order_by("hospital_name"),
        label="Hospital",
        widget=forms.Select(attrs={"id": "id_hospital"}),
    )

    department = forms.ModelChoiceField(
        queryset=MedicalDepartment.objects.filter(is_active=True).order_by("department_name"),
        label="Department",
    )

    role = forms.ModelChoiceField(
        queryset=MedicalStaffRole.objects.filter(is_active=True).order_by("name"),
        label="Medical Role",
    )

    is_senior = forms.BooleanField(
        required=False,
        label="Mark as Senior Staff",
        help_text="Turn this on if this person is a senior — juniors in the same hospital will be able to report to them.",
        widget=forms.CheckboxInput(attrs={"id": "id_is_senior", "class": "med-toggle-input"}),
    )

    reporting_to = forms.ModelChoiceField(
        queryset=MedicalStaffProfile.objects.none(),
        required=False,
        label="Reporting Staff",
        widget=forms.Select(attrs={"id": "id_reporting_to"}),
    )

    work_facilities = forms.ModelMultipleChoiceField(
        queryset=Facility.objects.none(),
        required=False,
        label="Facilities Assigned To",
        widget=forms.CheckboxSelectMultiple(attrs={"id": "id_work_facilities"}),
    )

    class Meta:
        model = MedicalStaffProfile
        fields = [
            "user",
            "hospital",
            "department",
            "role",
            "employee_id",
            "work_email",
            "personal_email",
            "phone",
            "address",
            "preferred_name",
            "qualification",
            "specialization",
            "medical_license_number",
            "years_of_experience",
            "hire_date",
            "employment_type",
            "emergency_contact_name",
            "emergency_contact_phone",
            "is_senior",
            "reporting_to",
            "work_facilities",
        ]
        widgets = {
            "hire_date": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 2}),
            "personal_email": forms.EmailInput(attrs={"readonly": "readonly"}),
            "phone": forms.TextInput(attrs={"readonly": "readonly"}),
            "preferred_name": forms.TextInput(attrs={"readonly": "readonly"}),
        }

    READONLY_AUTOFILL_FIELDS = ("personal_email", "phone", "preferred_name")

    def __init__(self, *args, **kwargs):
        category = kwargs.pop("category", None)
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            existing = field.widget.attrs.get("class", "")
            if name == "user":
                field.widget.attrs["class"] = (existing + " med-native-select").strip()
            elif name in self.READONLY_AUTOFILL_FIELDS:
                field.widget.attrs["class"] = (existing + " form-control med-input--readonly").strip()
                field.required = False
            else:
                field.widget.attrs["class"] = (existing + " form-control").strip()

        if category:
            self.fields["role"].queryset = self.fields["role"].queryset.filter(category=category)
            self.fields["role"].empty_label = None

        hospital = None
        is_senior = False
        role_category = category

        if self.is_bound:
            hospital_id = self.data.get("hospital")
            hospital = MedicalCenter.objects.filter(pk=hospital_id).first() if hospital_id else None
            is_senior = self.data.get("is_senior") in ("on", "true", "True", "1")
            role_id = self.data.get("role")
            if role_id:
                role_obj = MedicalStaffRole.objects.filter(pk=role_id).first()
                if role_obj:
                    role_category = role_obj.category
        elif self.instance and self.instance.pk:
            hospital = self.instance.hospital
            is_senior = self.instance.is_senior
            role_category = self.instance.role.category if self.instance.role_id else category

        self.fields["reporting_to"].queryset = _reporting_staff_queryset(hospital, role_category, is_senior)

        if hospital:
            facility_ids = list(hospital.selected_facilities or []) + list(hospital.selected_other_facilities or [])
            self.fields["work_facilities"].queryset = Facility.objects.filter(pk__in=facility_ids, is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get("user")
        if user:
            cleaned_data["personal_email"] = user.email or ""
            cleaned_data["phone"] = user.mobile_number or ""
            cleaned_data["preferred_name"] = user.full_name or ""

        reporting_to = cleaned_data.get("reporting_to")
        if reporting_to and reporting_to not in self.fields["reporting_to"].queryset:
            self.add_error("reporting_to", "Selected reporting staff isn't valid for this role/hospital.")

        return cleaned_data

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.save()
            self.save_m2m()
            user = profile.user
            if not user.is_medical_staff:
                user.is_medical_staff = True
                user.save(update_fields=["is_medical_staff"])
        return profile

class MedicalStaffRoleForm(forms.ModelForm):
    class Meta:
        model = MedicalStaffRole
        fields = ["name", "category"]
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "e.g. ENT Specialist, Staff Nurse, Lab Technician"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " form-control").strip()

class ShiftForm(forms.ModelForm):

    weekday_pattern = forms.MultipleChoiceField(
        choices=Shift.WEEKDAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        initial=["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
        label="Active Days",
    )

    hospital = forms.ModelChoiceField(
        queryset=MedicalCenter.objects.filter(is_active=True, hospital_status="active").order_by("hospital_name"),
        label="Hospital",
    )

    class Meta:
        model = Shift
        fields = [
            "hospital", "department", "shift_label", "shift_type", "start_time", "end_time",
            "recurrence_type", "start_date", "weekday_pattern",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        dept_qs = MedicalDepartment.objects.filter(is_active=True)
        hospital_qs = self.fields["hospital"].queryset
        staff_profile = None
        if user is not None and not getattr(user, "is_administrator", False):
            staff_profile = MedicalStaffProfile.objects.filter(user=user).first()
            if staff_profile:
                dept_qs = dept_qs.filter(pk=staff_profile.department_id)
                if staff_profile.hospital_id:
                    hospital_qs = hospital_qs.filter(pk=staff_profile.hospital_id)

        self.fields["department"].queryset = dept_qs.order_by("department_name")
        self.fields["hospital"].queryset = hospital_qs
        if staff_profile and staff_profile.hospital_id:
            self.fields["hospital"].initial = staff_profile.hospital_id
        self.fields["shift_label"].widget.attrs.update({
            "placeholder": "e.g. Morning Rounds, ICU Night Cover, Weekend OPD",
            "list": "shiftLabelSuggestions",
            "maxlength": "60",
        })

        if self.instance and self.instance.pk:
            self.initial["weekday_pattern"] = self.instance.active_weekdays()

        for name, field in self.fields.items():
            if name == "weekday_pattern":
                continue
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " form-control").strip()

    def clean_weekday_pattern(self):
        days = self.cleaned_data.get("weekday_pattern") or []
        weekday_order = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        ordered = [d for d in weekday_order if d in days]
        return ",".join(ordered) if ordered else ",".join(weekday_order)

    def save(self, commit=True):
        shift = super().save(commit=False)
        shift.weekday_pattern = self.cleaned_data["weekday_pattern"]
        if commit:
            shift.full_clean()
            shift.save()
        return shift

class ShiftAssignmentForm(forms.Form):

    medical_staff = forms.ModelMultipleChoiceField(
        queryset=MedicalStaffProfile.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        label="Staff Members",
    )
    custom_range = forms.BooleanField(required=False, label="Customize date range")
    assignment_start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    assignment_end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, shift=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.shift = shift

        staff_qs = MedicalStaffProfile.objects.none()
        if shift is not None:
            already_assigned_ids = shift.assignments.values_list("medical_staff_id", flat=True)
            staff_filter = {"is_active": True, "department": shift.department}
            if shift.hospital_id:
                staff_filter["hospital_id"] = shift.hospital_id
            staff_qs = (
                MedicalStaffProfile.objects.filter(**staff_filter)
                .exclude(pk__in=already_assigned_ids)
                .select_related("user", "role")
                .order_by("user__first_name")
            )

        self.fields["medical_staff"].queryset = staff_qs

        self.room_qs = Room.objects.none()
        if shift is not None and shift.hospital_id:
            self.room_qs = _hospital_room_queryset(shift.hospital)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("custom_range"):
            start = cleaned_data.get("assignment_start_date")
            end = cleaned_data.get("assignment_end_date")
            if not start or not end:
                self.add_error("assignment_start_date", "Provide both dates when customizing the range.")
            elif self.shift and (start < self.shift.start_date or end > self.shift.end_date or start > end):
                self.add_error("assignment_start_date", "Dates must fall within the shift range and start must be on/before end.")

        staff_qs = cleaned_data.get("medical_staff")
        if staff_qs:
            missing_names = []
            for staff in staff_qs:
                raw = self.data.get(f"room_{staff.pk}")
                if not raw or not self.room_qs.filter(pk=raw).exists():
                    missing_names.append(staff.user.full_name if staff.user_id else f"Staff #{staff.pk}")
            if missing_names:
                self.add_error(
                    "medical_staff",
                    "Please select a room for: " + ", ".join(missing_names) + "."
                )

        return cleaned_data

    def _room_for_staff(self, staff_id, post_data):
        raw = post_data.get(f"room_{staff_id}")
        if not raw:
            return None
        return self.room_qs.filter(pk=raw).first()

    def save(self, assigned_by=None, post_data=None):
        data = self.cleaned_data
        use_custom = data.get("custom_range")
        start = data["assignment_start_date"] if use_custom else self.shift.start_date
        end = data["assignment_end_date"] if use_custom else self.shift.end_date
        post_data = post_data or {}

        created, skipped = [], []
        for staff in data["medical_staff"]:
            assignment = ShiftAssignment(
                shift=self.shift,
                medical_staff=staff,
                room=self._room_for_staff(staff.pk, post_data),
                assignment_start_date=start,
                assignment_end_date=end,
                assigned_by=assigned_by,
            )
            try:
                assignment.full_clean()
                assignment.save()
                created.append(assignment)
            except Exception:
                skipped.append(staff)

        return created, skipped

class ShiftAssignmentEditForm(forms.ModelForm):
    class Meta:
        model = ShiftAssignment
        fields = ["assignment_start_date", "assignment_end_date", "room"]
        widgets = {
            "assignment_start_date": forms.DateInput(attrs={"type": "date"}),
            "assignment_end_date": forms.DateInput(attrs={"type": "date"}),
        }