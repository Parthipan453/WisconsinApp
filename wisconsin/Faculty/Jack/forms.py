from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, time
from Medical.models import *

class AppointmentForm(forms.ModelForm):

    hospital = forms.ModelChoiceField(
        queryset=MedicalCenter.objects.filter(is_active=True),
        to_field_name="uuid",
        empty_label="Select Hospital",
        error_messages={
            "required": "Please select a hospital.",
            "invalid_choice": "Please select a valid hospital.",
        }
    )

    medical_staff = forms.ModelChoiceField(
        queryset=MedicalStaffProfile.objects.none(),
        to_field_name="uuid",
        empty_label="Select Staff",
        error_messages={
            "required": "Please select medical staff.",
            "invalid_choice": "Please select valid medical staff.",
        }
    )

    class Meta:
        model = Appointment
        fields = [
            "hospital",
            "medical_staff",
            "appointment_date",
            "service",
            "priority",
            "reason",
        ]
        widgets = {
            "appointment_date": forms.DateInput(attrs={"type": "date"}),
            "reason": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Briefly describe the reason for your appointment...",
            }),
        }
        labels = {
            "hospital": "Hospital",
            "medical_staff": "Medical Staff",
            "appointment_date": "Appointment Date",
            "priority": "Priority Level",
            "reason": "Reason for Appointment",
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.initial.setdefault("priority", "NORMAL")

        self.fields["hospital"].queryset = (
            MedicalCenter.objects
            .filter(is_active=True)
            .order_by("hospital_name")
        )

        self.fields["medical_staff"].queryset = MedicalStaffProfile.objects.none()

        hospital_uuid = self.data.get("hospital")
        appointment_date = self.data.get("appointment_date")

        if hospital_uuid and appointment_date:
            try:
                selected_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
                self.fields["medical_staff"].queryset = self.get_available_staff(
                    hospital_uuid, selected_date
                )
            except (ValueError, TypeError):
                pass

        self.fields["hospital"].required = True
        self.fields["medical_staff"].required = True
        self.fields["appointment_date"].required = True
        self.fields["reason"].required = True

        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ == "Select":
                field.widget.attrs["class"] = "mbp-select"
            elif field.widget.__class__.__name__ == "Textarea":
                field.widget.attrs["class"] = "mbp-textarea"
            elif field.widget.__class__.__name__ == "DateInput":
                field.widget.attrs["class"] = "mbp-input"


    @staticmethod
    def get_available_staff(hospital_uuid, selected_date):
        """Get staff members who have shifts on the selected date"""
        
        weekday_code = selected_date.strftime("%a").upper()[:3]

        shifts = Shift.objects.filter(
            start_date__lte=selected_date,
            end_date__gte=selected_date,
        )

        department_ids = []
        for shift in shifts:
            if weekday_code in shift.active_weekdays():
                department_ids.append(shift.department_id)

        if not department_ids:
            return MedicalStaffProfile.objects.none()

        return (
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
            .distinct()
        )


    def generate_appointment_id(self, appointment_date):
        date_code = appointment_date.strftime("%y%m%d")
        count = Appointment.objects.filter(appointment_date=appointment_date).count()
        sequence = count + 1
        return f"APP-{date_code}-{str(sequence).zfill(3)}"


    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get("appointment_date")
        
        if appointment_date:
            today = timezone.now().date()
            
            if appointment_date < today:
                raise ValidationError("Appointment date cannot be in the past.")
            
            max_date = today + timezone.timedelta(days=30)
            if appointment_date > max_date:
                raise ValidationError("Appointments can only be booked up to 30 days in advance.")
        
        return appointment_date


    def clean(self):
        cleaned_data = super().clean()
        medical_staff = cleaned_data.get("medical_staff")
        hospital = cleaned_data.get("hospital")
        appointment_date = cleaned_data.get("appointment_date")

        if medical_staff and hospital and appointment_date:

            if medical_staff.hospital_id != hospital.id:
                self.add_error(
                    "medical_staff",
                    f"The selected staff does not belong to {hospital.hospital_name}."
                )
            else:

                weekday_code = appointment_date.strftime("%a").upper()[:3]
                
                shifts = Shift.objects.filter(
                    department=medical_staff.department,
                    start_date__lte=appointment_date,
                    end_date__gte=appointment_date,
                )
                
                department_has_shift = False
                for shift in shifts:
                    if weekday_code in shift.active_weekdays():
                        department_has_shift = True
                        break

                if not department_has_shift:
                    self.add_error(
                        "medical_staff",
                        "The selected medical staff is not available on the selected appointment date."
                    )

        return cleaned_data


    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.user:
            instance.user = self.user

        if not instance.status:
            instance.status = "PENDING"

        # if not instance.appointment_time:
        #     instance.appointment_time = time(9, 0)

        if not instance.appointment_number:
            instance.appointment_number = self.generate_appointment_id(
                instance.appointment_date
            )

        if commit:
            instance.save()

        return instance