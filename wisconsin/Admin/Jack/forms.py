from django import forms
from django.core.exceptions import ValidationError
from .models import Sport, SportTeamModel, Coach, SportsFacility, SportClub, Athletic
from Admin.models import User
import re
import datetime
from Medical.models import *
from datetime import datetime, time


############ SPORT FORM START ##############

class SportForm(forms.ModelForm):

    class Meta:
        model = Sport
        fields = [
            "sport_name",
            "sport_type",
            "gender",
            "is_team_sport",
            "min_players",
            "max_players",
            "is_olympic_sport",
            "is_active",
            "icon",
            "thumbnail"
        ]

    def clean(self):
        cleaned_data = super().clean()

        sport_name = cleaned_data.get("sport_name")
        gender = cleaned_data.get("gender")
        is_team_sport = cleaned_data.get("is_team_sport")
        min_players = cleaned_data.get("min_players")
        max_players = cleaned_data.get("max_players")
        icon = cleaned_data.get("icon")
        thumbnail = cleaned_data.get("thumbnail")

        gender_suffix = {
            "MALE": "M",
            "FEMALE": "F",
            "TRANSGENDER": "TG",
            "NON_BINARY": "NB",
            "OTHER": "O",
            "PREFER_NOT_TO_SAY": "PNS",
        }

        if sport_name:
            sport_name = sport_name.strip()

            if len(sport_name) <= 2:
                self.add_error(
                    "sport_name",
                    "Sport name must be more than 2 characters long."
                )

            # alpha_count = sum(c.isalpha() for c in sport_name)
            # if alpha_count < 2:
            #     self.add_error(
            #         "sport_name",
            #         "Sport name must contain at least 2 alphabetic characters."
            #     )

            if not re.fullmatch(r"[A-Za-z ]+", sport_name):
                self.add_error(
                    "sport_name",
                    "Sport name can contain only alphabetic characters and spaces."
                )

        if sport_name and gender:
            generated_name = f"{sport_name.strip()} {gender_suffix.get(gender, '')}".strip()

            qs = Sport.objects.filter(sport_name__iexact=generated_name)

            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                self.add_error(
                    "sport_name",
                    "This sport already exists."
                )

        if not icon:
            self.add_error("icon", "Please upload an icon.")

        if not thumbnail:
            self.add_error("thumbnail", "Please upload a thumbnail.")

        if is_team_sport:
            if min_players is None:
                self.add_error(
                    "min_players",
                    "Minimum players is required."
                )
            elif min_players < 2:
                self.add_error(
                    "min_players",
                    "Minimum players must be at least 2."
                )

            if max_players is None:
                self.add_error(
                    "max_players",
                    "Maximum players is required."
                )
            elif max_players < min_players:
                self.add_error(
                    "max_players",
                    "Maximum players must be greater than or equal to minimum players."
                )

        return cleaned_data
    
############ SPORT FORM END ##############

############ TEAM FORM START ##############

class SportTeamForm(forms.ModelForm):
    
    class Meta:
        model = SportTeamModel
        fields = [
            'team_code',
            'team_name',
            'icon',
            'sport_type',
            'division',
            'head_coach',
            'home_facility',
            'founded_year',
            'status',
            'club',
        ]
        widgets = {
            'team_code': forms.TextInput(attrs={
                'class': 'tf-form-control',
                'placeholder': 'Enter team code...',
                'required': True
            }),
            'team_name': forms.TextInput(attrs={
                'class': 'tf-form-control',
                'placeholder': 'Enter team name...',
                'required': True
            }),
            'icon': forms.FileInput(attrs={
                'class': 'tf-form-control-file'
            }),
            'sport_type': forms.Select(attrs={
                'class': 'tf-form-control',
                'required': True
            }),
            # 'gender_category': forms.Select(attrs={
            #     'class': 'tf-form-control',
            #     'required': True
            # }),
            'division': forms.TextInput(attrs={
                'class': 'tf-form-control',
                'placeholder': 'Enter division name...',
                'required': True
            }),
            # 'season': forms.TextInput(attrs={
            #     'class': 'tf-form-control',
            #     'placeholder': 'Enter season...',
            #     'required': True
            # }),
            'head_coach': forms.Select(attrs={
                'class': 'tf-form-control'
            }),
            'home_facility': forms.Select(attrs={
                'class': 'tf-form-control'
            }),
            'founded_year': forms.NumberInput(attrs={
                'class': 'tf-form-control',
                'placeholder': 'Enter founded year...',
                'min': 1800,
                'max': 2099,
                'required': True
            }),
            'status': forms.CheckboxInput(attrs={
                'class': 'tf-form-check-input'
            }),
            'club': forms.Select(attrs={
                'class': 'tf-form-control'
            }),
        }
        labels = {
            'team_code': 'Team Code',
            'team_name': 'Team Name',
            'icon': 'Team Icon',
            'sport_type': 'Sport Type',
            # 'gender_category': 'Gender Category',
            'division': 'Division',
            # 'season': 'Season',
            'head_coach': 'Head Coach',
            'home_facility': 'Home Facility',
            'founded_year': 'Founded Year',
            'status': 'Active',
            'club': 'Club',
        }
        help_texts = {
            'team_code': 'Unique identifier for the team (e.g., FCB-M-01)',
            'team_name': 'Full name of the team',
            'icon': 'Upload a square image (recommended: 64x64px)',
            'division': 'League or division name (e.g., Premier League, NBA)',
            # 'season': 'Season year (e.g., 2024-2025)',
            'founded_year': 'Year the team was founded',
        }
        error_messages = {
            'team_code': {
                'required': 'Team code is required.',
                'unique': 'This team code already exists.',
                'max_length': 'Team code cannot exceed 20 characters.',
            },
            'team_name': {
                'required': 'Team name is required.',
                'unique': 'This team name already exists.',
                'max_length': 'Team name cannot exceed 100 characters.',
            },
            'sport_type': {
                'required': 'Please select a sport type.',
            },
            # 'gender_category': {
            #     'required': 'Please select a gender category.',
            # },
            'division': {
                'required': 'Division is required.',
                'max_length': 'Division cannot exceed 100 characters.',
            },
            # 'season': {
            #     'required': 'Season is required.',
            #     'max_length': 'Season cannot exceed 100 characters.',
            # },
            'founded_year': {
                'required': 'Founded year is required.',
                'invalid': 'Please enter a valid year.',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['sport_type'].queryset = Sport.objects.filter(is_active=True).order_by('sport_name')
        self.fields['head_coach'].queryset = Coach.objects.filter(is_active=True).order_by('staff_id')
        self.fields['home_facility'].queryset = SportsFacility.objects.filter(status='ACTIVE').order_by('facility_name')
        self.fields['club'].queryset = SportClub.objects.filter(is_active=True).order_by('club_name')
        
        self.fields['head_coach'].empty_label = 'Select Head Coach'
        self.fields['home_facility'].empty_label = 'Select Home Facility'
        self.fields['club'].empty_label = 'Select Club'
        
        self.fields['head_coach'].required = False
        self.fields['home_facility'].required = False
        self.fields['club'].required = False
        self.fields['icon'].required = False
        
        if not self.instance.pk:
            self.fields['status'].initial = True

    def clean_team_code(self):
        team_code = self.cleaned_data.get('team_code')
        if team_code:
            existing = SportTeamModel.objects.filter(team_code__iexact=team_code)
            if self.instance.pk:
                existing = existing.exclude(team_id=self.instance.pk)
            if existing.exists():
                raise ValidationError('A team with this code already exists.')
            
            if not re.match(r'^[A-Z]{2,4}-[A-Z]-\d{2,4}$', team_code):
                raise ValidationError('Team code should follow format: ABC-M-01')
        return team_code

    def clean_team_name(self):
        team_name = self.cleaned_data.get('team_name')
        if team_name:
            existing = SportTeamModel.objects.filter(team_name__iexact=team_name)
            if self.instance.pk:
                existing = existing.exclude(team_id=self.instance.pk)
            if existing.exists():
                raise ValidationError('A team with this name already exists.')
            if len(team_name) < 2:
                raise ValidationError("Team name must be at least 2 letters.")
            
            alpha_count = sum(c.isalpha() for c in team_name)
            if alpha_count < 2:
                raise ValidationError("Team name must contain at least 2 alphabetic characters.")
            
        return team_name

    def clean_founded_year(self):
        year = self.cleaned_data.get('founded_year')
        if year:
            current_year = datetime.now().year
            if year < 1800:
                raise ValidationError('Founded year must be greater than 1800.')
            if year > current_year:
                raise ValidationError(f'Founded year cannot be in the future. Current year is {current_year}.')
        return year
    
    def clean_division(self):

        division = self.cleaned_data.get('division')

        if division:

            if len(division) < 3:
                raise ValidationError("Division must be at least 3 letters.")
            
            alpha_count = sum(c.isalpha() for c in division)
            if alpha_count < 2:
                raise ValidationError("Division must contain at least 2 alphabetic characters.")
            
        return division

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data
    
############ TEAM FORM END ##############

############ ATHLETE FORM START ##############

class AthleticForm(forms.ModelForm):
    individual_sports = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        help_text="Search and select multiple sports"
    )
    
    class Meta:
        model = Athletic
        fields = [
            'student',
            'team',
            'individual_sports',
            'jersey_number',
            'position',
            'height',
            'weight',
            'class_year',
            'eligibility_status',
            'scholarship_status',
            'is_active',
        ]
        widgets = {
            'student': forms.Select(attrs={
                'class': 'af-form-control select2-search',
                'required': True,
                'id': 'id_student',
                'style': 'width: 100%;'
            }),
            'team': forms.Select(attrs={
                'class': 'af-form-control select2-search',
                'id': 'id_team',
                'style': 'width: 100%;'
            }),
            'jersey_number': forms.NumberInput(attrs={
                'class': 'af-form-control',
                'placeholder': 'Enter jersey number...',
                'min': 0,
                'id': 'id_jersey_number'
            }),
            'position': forms.TextInput(attrs={
                'class': 'af-form-control',
                'placeholder': 'Enter position...',
                'id': 'id_position'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'af-form-control',
                'placeholder': 'Enter height...',
                'step': '0.01',
                'min': 0,
                'max': 8,
                'id': 'id_height'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'af-form-control',
                'placeholder': 'Enter weight...',
                'step': '0.01',
                'min': 0,
                'id': 'id_weight'
            }),
            'class_year': forms.Select(attrs={
                'class': 'af-form-control',
                'id': 'id_class_year'
            }),
            'eligibility_status': forms.Select(attrs={
                'class': 'af-form-control',
                'required': True,
                'id': 'id_eligibility_status'
            }),
            'scholarship_status': forms.CheckboxInput(attrs={
                'class': 'af-form-check-input',
                'id': 'id_scholarship_status'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'af-form-check-input',
                'id': 'id_is_active'
            }),
        }
        labels = {
            'student': 'Athlete',
            'team': 'Team',
            'individual_sports': 'Individual Sports',
            'jersey_number': 'Jersey Number',
            'position': 'Position',
            'height': 'Height (ft)',
            'weight': 'Weight (lbs)',
            'class_year': 'Class Year',
            'eligibility_status': 'Eligibility Status',
            'scholarship_status': 'Scholarship',
            'is_active': 'Active',
        }
        help_texts = {
            'team': 'Select a team if the athlete is part of a team sport',
            'individual_sports': 'Search and select multiple sports',
            'height': 'Example: 5.11 for 5 feet 11 inches',
            'jersey_number': 'Enter the athlete\'s jersey number',
        }
        error_messages = {
            'student': {
                'required': 'Student is required.',
            },
            'eligibility_status': {
                'required': 'Eligibility status is required.',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['team'].queryset = SportTeamModel.objects.filter(status=True).order_by('team_name')
        
        self.fields['team'].empty_label = 'Select Team'
        self.fields['team'].required = False
        self.fields['jersey_number'].required = False
        self.fields['position'].required = False
        self.fields['height'].required = False
        self.fields['weight'].required = False
        self.fields['class_year'].required = False
        
        if self.instance and self.instance.pk:
            sport_ids = list(self.instance.individual_sports.values_list('id', flat=True))
            self.fields['individual_sports'].initial = ','.join(str(id) for id in sport_ids)
        else:
            self.fields['individual_sports'].initial = ''
        
        if not self.instance.pk:
            self.fields['scholarship_status'].initial = False
            self.fields['is_active'].initial = True

    def clean_student(self):
        student = self.cleaned_data.get('student')
        
        if student:
            existing_athlete = Athletic.objects.filter(student=student)
            if self.instance and self.instance.pk:
                existing_athlete = existing_athlete.exclude(pk=self.instance.pk)
            
            if existing_athlete.exists():
                raise ValidationError(f'Athlete "{student.username}" already has an athlete profile.')
        
        return student

    def clean_class_year(self):
        class_year = self.cleaned_data.get('class_year')
        student = self.cleaned_data.get('student')
        
        if student:
            if student.is_faculty:
                return 'FACULTY'
            elif student.is_staff:
                return 'STAFF'
        
        return class_year

    def clean_individual_sports(self):
        data = self.cleaned_data.get('individual_sports')
        
        if not data:
            return []
        
        if isinstance(data, str):
            cleaned_data = data.replace(' ', '')
            if cleaned_data:
                try:
                    sport_ids = [int(x) for x in cleaned_data.split(',') if x]
                    return sport_ids
                except ValueError:
                    raise ValidationError('Please enter valid sport IDs (numbers only).')
            return []
        
        if isinstance(data, list):
            return data
        
        return []

    def clean(self):
        cleaned_data = super().clean()
        team = cleaned_data.get('team')
        individual_sports = cleaned_data.get('individual_sports')
        student = cleaned_data.get('student')
        class_year = cleaned_data.get('class_year')
        
        if student and student.is_student and not class_year:
            self.add_error('class_year', 'Class year is required for students.')
        
        if student:
            if student.is_faculty and not class_year:
                cleaned_data['class_year'] = 'FACULTY'
            elif student.is_staff and not class_year:
                cleaned_data['class_year'] = 'STAFF'
        
        if not team and not individual_sports:
            raise ValidationError('Please select either a Team or at least one Individual Sport.')
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        sports_data = self.cleaned_data.get('individual_sports')
        
        if commit:
            instance.save()
            if sports_data:
                instance.individual_sports.set(sports_data)
            else:
                instance.individual_sports.clear()
            instance.save()
        else:
            instance._sports_data = sports_data
        
        return instance

    def save_m2m(self):
        if hasattr(self.instance, '_sports_data'):
            sports_data = self.instance._sports_data
            if sports_data:
                self.instance.individual_sports.set(sports_data)
            else:
                self.instance.individual_sports.clear()

############ ATHLETE FORM END ##############


############ MEDICAL FORM START ##############

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


############ MEDICAL FORM END ##############