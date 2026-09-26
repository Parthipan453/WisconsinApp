from datetime import date
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django import forms
from urllib.parse import urlparse
import json
import re
from .models import Facility,MedicalCenter, HospitalStatistics,FacilityMaintenance


class FacilityForm(forms.ModelForm):
    class Meta:
        model = Facility
        fields = [
            "name",
            "icon",
            "facility_type",
        ]

    def clean_name(self):
        name = self.cleaned_data["name"].strip()

        if len(name) < 2:
            raise forms.ValidationError(
                "Facility name must contain at least 2 characters."
            )

        if len(name) > 50:
            raise forms.ValidationError(
                "Facility name cannot exceed 50 characters."
            )

        qs = Facility.objects.filter(name__iexact=name)

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(
                "Facility already exists."
            )

        return name

    def clean_icon(self):
        icon = self.cleaned_data["icon"].strip()

        if not icon:
            raise forms.ValidationError(
                "Please select an icon."
            )

        return icon

    def clean_facility_type(self):
        facility_type = self.cleaned_data["facility_type"]

        valid_types = [
            choice[0]
            for choice in Facility.FACILITY_TYPES
        ]

        if facility_type not in valid_types:
            raise forms.ValidationError(
                "Invalid facility type."
            )

        return facility_type 
    
    
# Create hospital form

class MedicalCenterForm(forms.ModelForm):

    class Meta:
        model = MedicalCenter
        fields = [
            "hospital_name",
            "short_description",
            "about_hospital",
            "director_name",

            "hospital_building",

            "hospital_phone",
            "hospital_emgphone",
            "hospital_email",
            "working_hours",
            "established_year",
            "hospital_status",
            "hospital_banner",
            "selected_facilities",
            "selected_other_facilities",
        ]
        
        # hospital name
        
        def clean_hospital_name(self):
            name = self.cleaned_data["hospital_name"]

            name = re.sub(r"\s+", " ", name).strip()

            if len(name) < 3:
                raise forms.ValidationError(
                    "Hospital name must contain at least 3 characters."
                )

            if len(name) > 50:
                raise forms.ValidationError(
                    "Hospital name cannot exceed 50 characters."
                )

            if not re.match(r"^[A-Za-z]", name):
                raise forms.ValidationError(
                    "Hospital name must start with a letter."
                )

            if not re.fullmatch(r"[A-Za-z0-9\s&().'-]+", name):
                raise forms.ValidationError(
                    "Hospital name contains invalid characters."
                )

            exists = MedicalCenter.objects.exclude(
                pk=self.instance.pk
            ).filter(
                hospital_name__iexact=name
            ).exists()

            if exists:
                raise forms.ValidationError(
                    "Hospital name already exists."
                )

            return name
        
        # Short description
        def clean_short_description(self):
            value = self.cleaned_data["short_description"]

            value = re.sub(r"\s+", " ", value).strip()

            if len(value) < 10:
                raise forms.ValidationError(
                    "Short description must contain at least 10 characters."
                )

            if len(value) > 60:
                raise forms.ValidationError(
                    "Short description cannot exceed 60 characters."
                )

            if len(value.split()) < 2:
                raise forms.ValidationError(
                    "Please enter at least two words."
                )

            if not re.search(r"[A-Za-z]", value):
                raise forms.ValidationError(
                    "Description must contain at least one letter."
                )

            return value
        
        # about section

        def clean_about_hospital(self):
            value = self.cleaned_data["about_hospital"]

            value = re.sub(r"\s+", " ", value).strip()

            if len(value) < 30:
                raise forms.ValidationError(
                    "About hospital must contain at least 30 characters."
                )

            if len(value) > 500:
                raise forms.ValidationError(
                    "About hospital cannot exceed 500 characters."
                )

            if len(value.split()) < 5:
                raise forms.ValidationError(
                    "Please enter at least five words."
                )

            return value
        
        # director name
        
        def clean_director_name(self):
            director = self.cleaned_data.get("director_name")

            if not director:
                raise forms.ValidationError("Please select a director.")

            if director.role.category != "DIRECTOR":
                raise forms.ValidationError("Selected staff is not a director.")

            if director.status != "ACTIVE":
                raise forms.ValidationError("Selected director is not active.")

            return director
        
        
        # established year
        
        def clean_established_year(self):
            year = self.cleaned_data.get("established_year")

            if not year:
                raise forms.ValidationError(
                    "Please enter the established year."
                )

            current_year = date.today().year

            if year < 1800:
                raise forms.ValidationError(
                    "Please enter a valid established year."
                )

            if year > current_year:
                raise forms.ValidationError(
                    "Established year cannot be in the future."
                )

            return year

        def clean_hospital_phone(self):
            phone = self.cleaned_data["hospital_phone"].strip()

            if not phone:
                raise forms.ValidationError(
                    "Phone number is required."
                )

            if not re.fullmatch(r"[\d+\-\s]+", phone):
                raise forms.ValidationError(
                    "Phone number contains invalid characters."
                )

            if "+" in phone and not phone.startswith("+"):
                raise forms.ValidationError(
                    "Invalid phone number format."
                )

            digits = re.sub(r"[\s\-+]", "", phone)

            if not digits.isdigit():
                raise forms.ValidationError(
                    "Enter a valid phone number."
                )

            if not 7 <= len(digits) <= 15:
                raise forms.ValidationError(
                    "Phone number must contain 7 to 15 digits."
                )

            # Exclude current hospital while editing
            qs = MedicalCenter.objects.filter(
                hospital_phone=phone
            )

            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise forms.ValidationError(
                    "This phone number is already registered."
                )

            return phone
        
    
        def clean_hospital_emgphone(self):
            phone = self.cleaned_data.get(
                "hospital_emgphone",
                ""
            ).strip()

            if not phone:
                return ""

            if not re.fullmatch(r"[\d+\-\s]+", phone):
                raise forms.ValidationError(
                    "Emergency phone number contains invalid characters."
                )

            cleaned = re.sub(r"[\s-]", "", phone)

            india = r"^(?:\+91|91)?[6-9]\d{9}$"
            us = r"^(?:\+1|1)?\d{10}$"

            if not (
                re.fullmatch(india, cleaned)
                or re.fullmatch(us, cleaned)
            ):
                raise forms.ValidationError(
                    "Enter a valid Indian or US emergency phone number."
                )
            if MedicalCenter.objects.filter(hospital_emgphone=phone).exists():
                            raise forms.ValidationError(
                                "This phone number is already registered."
                            )

            return phone
        
        def clean_hospital_email(self):
            email = self.cleaned_data["hospital_email"].strip().lower()

            # Maximum length
            if len(email) > 254:
                raise forms.ValidationError(
                    "Email address is too long."
                )

            # Email format validation
            try:
                validate_email(email)
            except ValidationError:
                raise forms.ValidationError(
                    "Enter a valid email address."
                )

            # Already exists
            if MedicalCenter.objects.filter(hospital_email__iexact=email).exists():
                raise forms.ValidationError(
                    "This email address is already registered."
                )

            return email

        def clean_hospital_banner(self):
            banner = self.cleaned_data.get("hospital_banner")

            if not banner:
                return banner

            allowed_types = [
                "image/jpeg",
                "image/png",
                "image/webp",
            ]

            if banner.content_type not in allowed_types:
                raise forms.ValidationError(
                    "Only JPG, PNG and WEBP images are allowed."
                )

            if banner.size > 5 * 1024 * 1024:
                raise forms.ValidationError(
                    "Banner image must not exceed 5 MB."
                )

            return banner
        
    
        def clean_working_hours(self):
            data = self.cleaned_data.get("working_hours")

            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    raise forms.ValidationError(
                        "Invalid working hours data."
                    )

            if not isinstance(data, dict):
                raise forms.ValidationError(
                    "Working hours must be a valid object."
                )

            enabled_days = 0

            for day, value in data.items():

                if not value.get("enabled"):
                    continue

                enabled_days += 1

                opening = value.get("opening")
                closing = value.get("closing")

                if not opening or not closing:
                    raise forms.ValidationError(
                        f"{day.title()} requires opening and closing time."
                    )

                if closing <= opening:
                    raise forms.ValidationError(
                        f"{day.title()} closing time must be later than opening time."
                    )

            if enabled_days == 0:
                raise forms.ValidationError(
                    "Please enable at least one working day."
                )

            return data
        
    
        def clean_selected_facilities(self):
            data = self.cleaned_data.get("selected_facilities")

            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    raise forms.ValidationError(
                        "Invalid facilities data."
                    )

            # At least one facility must be selected
            if not data:
                raise forms.ValidationError(
                    "Please select at least one facility."
                )

            if not isinstance(data, list):
                raise forms.ValidationError(
                    "Selected facilities must be a list."
                )

            if len(data) != len(set(data)):
                raise forms.ValidationError(
                    "Duplicate facilities are not allowed."
                )

            existing = Facility.objects.filter(
                id__in=data,
                is_active=True
            ).count()

            if existing != len(data):
                raise forms.ValidationError(
                    "One or more selected facilities are invalid."
                )

            return data
        
    
        def clean(self):
            cleaned_data = super().clean()

            phone = cleaned_data.get("hospital_phone")
            emergency = cleaned_data.get("hospital_emgphone")

            if (
                phone
                and emergency
                and phone.replace(" ", "") == emergency.replace(" ", "")
            ):
                self.add_error(
                    "hospital_emgphone",
                    "Emergency phone number must be different from hospital phone number."
                )

            return cleaned_data
        
# FACILITY MAINTENANCE

class FacilityMaintenanceForm(forms.ModelForm):
    class Meta:
        model = FacilityMaintenance
        fields = [
            "title",
            "description",
            "status",
            "priority",
            "start_date",
            "expected_completion",
            "assigned_engineer",
            "contact_number",
            "remarks",
        ]

    def clean_title(self):
        title = self.cleaned_data["title"].strip()

        if len(title) < 5:
            raise forms.ValidationError(
                "Title must contain at least 5 characters."
            )

        if len(title) > 100:
            raise forms.ValidationError(
                "Title cannot exceed 100 characters."
            )

        return title

    def clean_description(self):
        description = self.cleaned_data["description"].strip()

        if len(description) < 10:
            raise forms.ValidationError(
                "Description must contain at least 10 characters."
            )

        return description

    def clean_assigned_engineer(self):
        engineer = self.cleaned_data["assigned_engineer"].strip()

        if len(engineer) < 3:
            raise forms.ValidationError(
                "Engineer name is too short."
            )

        return engineer

    def clean_contact_number(self):
        contact = self.cleaned_data["contact_number"].strip()

        if not contact.isdigit():
            raise forms.ValidationError(
                "Contact number must contain only digits."
            )

        if len(contact) != 10:
            raise forms.ValidationError(
                "Contact number must be exactly 10 digits."
            )

        return contact

    def clean(self):
        cleaned_data = super().clean()

        start = cleaned_data.get("start_date")
        expected = cleaned_data.get("expected_completion")

        if start and expected and expected < start:
            self.add_error(
                "expected_completion",
                "Expected completion date cannot be before the start date."
            )

        return cleaned_data


