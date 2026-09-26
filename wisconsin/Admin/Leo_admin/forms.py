## Leo's Code Start ##

import re
from datetime import date
from pathlib import Path
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import AcademicStanding
from Faculty.models import FacultyProfile
from Students.models import StudentProfile
from Students.Leo_Student.models import (
    DoctoralCommittee,
    PhD,
    PhDStudent,
)


class AcademicStandingForm(forms.ModelForm):
    class Meta:
        model = AcademicStanding
        fields = [
            "standing_name",
            "minimum_gpa",
            "description",
        ]

    def clean_standing_name(self):
        standing_name = self.cleaned_data.get("standing_name", "").strip()

        if not standing_name:
            raise ValidationError("Standing Name is required.")

        if len(standing_name) < 3:
            raise ValidationError("Minimum 3 characters required.")

        if len(standing_name) > 100:
            raise ValidationError("Maximum 100 characters allowed.")

        if not re.match(r"^[A-Za-z0-9\s'&-]+$", standing_name):
            raise ValidationError("Invalid Standing Name.")

        queryset = AcademicStanding.objects.filter(standing_name__iexact=standing_name)

        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise ValidationError("Standing Name already exists.")

        return standing_name

    def clean_minimum_gpa(self):
        minimum_gpa = self.cleaned_data.get("minimum_gpa")

        if minimum_gpa is None:
            raise ValidationError("Minimum GPA is required.")

        queryset = AcademicStanding.objects.filter(minimum_gpa=minimum_gpa)

        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise ValidationError("Minimum GPA already exists.")

        if not (0 <= minimum_gpa <= 4):
            raise ValidationError("GPA must be between 0.00 and 4.00.")

        return minimum_gpa

    def clean_description(self):
        description = self.cleaned_data.get("description", "").strip()

        if not description:
            raise ValidationError("Description is required.")

        if len(description) > 500:
            raise ValidationError("Maximum 500 characters allowed.")

        return description


class PhDProgramForm(forms.ModelForm):

    class Meta:

        model = PhD

        fields = [
            "department",
            "program_name",
            "total_credits_required",
            "residency_requirement",
            "duration_years",
            "program_description",
            "status",
        ]

        widgets = {
            "department": forms.Select(
                attrs={
                    "class": "choices-select",
                    "id": "department",
                }
            ),
            "program_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "id": "programName",
                    "placeholder": "Enter Program Name",
                    "maxlength": 100,
                }
            ),
            "total_credits_required": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "id": "creditsRequired",
                    "placeholder": "Enter Credits Required",
                    "min": 1,
                    "max": 300,
                }
            ),
            "residency_requirement": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "id": "residencyRequirement",
                    "placeholder": "Enter Residency Requirement",
                    "min": 1,
                }
            ),
            "duration_years": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "id": "durationYears",
                    "placeholder": "Enter Duration",
                    "min": 1,
                    "max": 10,
                }
            ),
            "program_description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "id": "programDescription",
                    "placeholder": "Enter Program Description",
                    "rows": 5,
                    "maxlength": 1000,
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "choices-select",
                    "id": "status",
                }
            ),
        }

    def clean_program_name(self):

        program_name = self.cleaned_data.get(
            "program_name",
            "",
        ).strip()

        if not program_name:
            raise ValidationError("Program Name is required.")

        if len(program_name) < 3:
            raise ValidationError("Minimum 3 characters required.")

        if len(program_name) > 100:
            raise ValidationError("Maximum 100 characters allowed.")

        if not re.search(
            r"[A-Za-z]",
            program_name,
        ):
            raise ValidationError("Program Name must contain at least one alphabet.")

        queryset = PhD.objects.filter(
            department=self.cleaned_data.get("department"),
            program_name__iexact=program_name,
        )

        if self.instance.pk:
            queryset = queryset.exclude(
                pk=self.instance.pk,
            )

        if queryset.exists():
            raise ValidationError("This PhD Program already exists.")

        return program_name

    def clean_total_credits_required(self):

        credits = self.cleaned_data.get("total_credits_required")

        if credits is None:
            raise ValidationError("Total Credits Required is required.")

        if credits < 1 or credits > 300:
            raise ValidationError("Credits must be between 1 and 300.")

        return credits

    def clean_residency_requirement(self):

        residency_requirement = self.cleaned_data.get("residency_requirement")

        if residency_requirement is None:
            raise ValidationError("Residency Requirement is required.")

        if residency_requirement <= 0:
            raise ValidationError("Residency Requirement must be greater than 0.")

        return residency_requirement

    def clean_duration_years(self):

        duration = self.cleaned_data.get("duration_years")

        if duration is None:
            raise ValidationError("Duration is required.")

        if duration < 1 or duration > 10:
            raise ValidationError("Duration must be between 1 and 10 years.")

        return duration

    def clean_program_description(self):

        description = self.cleaned_data.get(
            "program_description",
            "",
        ).strip()

        if not description:
            raise ValidationError("Program Description is required.")

        if len(description) > 1000:
            raise ValidationError("Maximum 1000 characters allowed.")

        if len(description) < 10:
            raise ValidationError("Minimum 10 characters required.")

        if not re.match(
            r"^[A-Za-z0-9\s&().,'/-]+$",
            description,
        ):
            raise ValidationError("Invalid Program Description.")

        return description

    def clean_department(self):

        department = self.cleaned_data.get("department")

        if not department:
            raise ValidationError("Department is required.")

        return department

    def clean_status(self):

        status = self.cleaned_data.get("status")

        if not status:
            raise ValidationError("Status is required.")

        return status


class PhDStudentForm(forms.ModelForm):
    program_assignment_video = forms.FileField(
        required=False,
        widget=forms.FileInput(
            attrs={
                "class": "assignment-video-input",
                "accept": "video/mp4,video/webm,video/quicktime,video/x-m4v",
            }
        ),
    )

    advisor_assignment_video = forms.FileField(
        required=False,
        widget=forms.FileInput(
            attrs={
                "class": "assignment-video-input",
                "accept": "video/mp4,video/webm,video/quicktime,video/x-m4v",
            }
        ),
    )

    remove_program_assignment_video = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "assignment-video-remove",
            }
        ),
    )

    remove_advisor_assignment_video = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "assignment-video-remove",
            }
        ),
    )

    class Meta:
        model = PhDStudent
        fields = [
            "student",
            "phd_program",
            "advisor",
            "admission_date",
            "cohort_year",
            "current_status",
            "expected_graduation_date",
        ]
        widgets = {
            "student": forms.Select(
                attrs={
                    "class": "assignment-field assignment-select",
                    "id": "student",
                }
            ),
            "phd_program": forms.Select(
                attrs={
                    "class": "assignment-field assignment-select",
                    "id": "phdProgram",
                }
            ),
            "advisor": forms.Select(
                attrs={
                    "class": "assignment-field assignment-select",
                    "id": "advisor",
                }
            ),
            "admission_date": forms.TextInput(
                attrs={
                    "class": "assignment-field assignment-date",
                    "id": "admissionDate",
                    "placeholder": "Select admission date",
                    "autocomplete": "off",
                    "data-date-format": "Y-m-d",
                }
            ),
            "cohort_year": forms.NumberInput(
                attrs={
                    "class": "assignment-field assignment-readonly",
                    "id": "cohortYear",
                    "placeholder": "Auto-calculated",
                    "readonly": "readonly",
                }
            ),
            "current_status": forms.Select(
                attrs={
                    "class": "assignment-field assignment-select",
                    "id": "currentStatus",
                }
            ),
            "expected_graduation_date": forms.TextInput(
                attrs={
                    "class": "assignment-field assignment-readonly",
                    "id": "expectedGraduationDate",
                    "placeholder": "Auto-calculated",
                    "readonly": "readonly",
                    "data-date-format": "Y-m-d",
                }
            ),
        }
        labels = {
            "student": "Student",
            "phd_program": "PhD Program",
            "advisor": "Research Advisor",
            "admission_date": "Admission Date",
            "cohort_year": "Cohort Year",
            "current_status": "Current Status",
            "expected_graduation_date": "Expected Graduation Date",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            students = StudentProfile.objects.filter(
                phd_students__isnull=True
            ) | StudentProfile.objects.filter(pk=self.instance.student.pk)

            if self.instance.admission_date:
                self.fields["cohort_year"].initial = self.instance.admission_date.year

                if self.instance.phd_program:
                    duration = self.instance.phd_program.duration_years
                    expected_year = self.instance.admission_date.year + duration

                    try:
                        self.fields["expected_graduation_date"].initial = (
                            self.instance.admission_date.replace(year=expected_year)
                        )
                    except ValueError:
                        self.fields["expected_graduation_date"].initial = date(
                            expected_year,
                            self.instance.admission_date.month,
                            min(self.instance.admission_date.day, 28),
                        )
        else:
            students = StudentProfile.objects.filter(phd_students__isnull=True)

        self.fields["student"].queryset = students.select_related("user").order_by(
            "user__first_name",
            "user__last_name",
        )

        self.fields["phd_program"].queryset = PhD.objects.filter(
            status="ACTIVE"
        ).order_by("program_name")

        self.fields["advisor"].queryset = FacultyProfile.objects.select_related(
            "user"
        ).order_by(
            "user__first_name",
            "user__last_name",
        )

        self.fields["student"].empty_label = "Select Student"
        self.fields["phd_program"].empty_label = "Select PhD Program"
        self.fields["advisor"].empty_label = "Select Research Advisor"

        self.fields["current_status"].initial = "ACTIVE"

        self.fields["cohort_year"].required = False
        self.fields["advisor"].required = False
        self.fields["expected_graduation_date"].required = False

    def clean_student(self):
        student = self.cleaned_data.get("student")

        if not student:
            raise ValidationError("Student is required.")

        queryset = PhDStudent.objects.filter(student=student)

        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise ValidationError("This student is already enrolled in a PhD program.")

        return student

    def clean_phd_program(self):
        phd_program = self.cleaned_data.get("phd_program")

        if not phd_program:
            raise ValidationError("PhD Program is required.")

        if phd_program.status != "ACTIVE":
            raise ValidationError("Please select an active PhD program.")

        return phd_program

    def clean_advisor(self):
        advisor = self.cleaned_data.get("advisor")

        if advisor:
            if not FacultyProfile.objects.filter(pk=advisor.pk).exists():
                raise ValidationError("Invalid research advisor selected.")

        return advisor

    def clean_admission_date(self):
        admission_date = self.cleaned_data.get("admission_date")

        if not admission_date:
            raise ValidationError("Admission Date is required.")

        if admission_date > date.today():
            raise ValidationError("Admission Date cannot be in the future.")

        if admission_date.year < 2000:
            raise ValidationError("Admission Date is invalid.")

        return admission_date

    def clean_current_status(self):
        current_status = self.cleaned_data.get("current_status")

        if not current_status:
            raise ValidationError("Current Status is required.")

        return current_status

    def validate_video(self, uploaded_file, field_name):
        if not uploaded_file:
            return uploaded_file

        max_size = 200 * 1024 * 1024

        if uploaded_file.size > max_size:
            raise ValidationError(f"{field_name} cannot be larger than 200 MB.")

        allowed_extensions = {
            ".mp4",
            ".webm",
            ".mov",
            ".m4v",
        }

        extension = Path(uploaded_file.name).suffix.lower()

        if extension not in allowed_extensions:
            raise ValidationError(
                f"{field_name} must be an MP4, WebM, MOV, or M4V video."
            )

        allowed_content_types = {
            "video/mp4",
            "video/webm",
            "video/quicktime",
            "video/x-m4v",
        }

        if uploaded_file.content_type:
            if uploaded_file.content_type not in allowed_content_types:
                raise ValidationError(
                    f"{field_name} contains an unsupported video format."
                )

        return uploaded_file

    def clean_program_assignment_video(self):
        video = self.cleaned_data.get("program_assignment_video")

        return self.validate_video(video, "Program Assignment Video")

    def clean_advisor_assignment_video(self):
        video = self.cleaned_data.get("advisor_assignment_video")

        return self.validate_video(video, "Advisor Assignment Video")

    def clean(self):
        cleaned_data = super().clean()

        admission_date = cleaned_data.get("admission_date")
        phd_program = cleaned_data.get("phd_program")
        student = cleaned_data.get("student")

        if admission_date:
            cleaned_data["cohort_year"] = admission_date.year

        if admission_date and phd_program:
            duration = phd_program.duration_years
            expected_year = admission_date.year + duration

            try:
                cleaned_data["expected_graduation_date"] = admission_date.replace(
                    year=expected_year
                )
            except ValueError:
                if admission_date.month == 2 and admission_date.day == 29:
                    cleaned_data["expected_graduation_date"] = date(
                        expected_year,
                        2,
                        28,
                    )
                else:
                    cleaned_data["expected_graduation_date"] = date(
                        expected_year,
                        admission_date.month,
                        min(admission_date.day, 28),
                    )

        if student and phd_program:
            existing = PhDStudent.objects.filter(
                student=student,
                phd_program=phd_program,
            ).exclude(pk=(self.instance.pk if self.instance.pk else None))

            if existing.exists():
                raise ValidationError(
                    "This student is already enrolled in the selected PhD program."
                )

        if admission_date and cleaned_data.get("cohort_year"):
            if admission_date.year != cleaned_data["cohort_year"]:
                self.add_error(
                    "cohort_year",
                    "Cohort Year must be equal to the Admission Year.",
                )

        expected_graduation_date = cleaned_data.get("expected_graduation_date")

        if admission_date and expected_graduation_date:
            if expected_graduation_date <= admission_date:
                self.add_error(
                    "expected_graduation_date",
                    "Expected Graduation Date must be after the Admission Date.",
                )

            duration = expected_graduation_date.year - admission_date.year

            if duration > 10:
                self.add_error(
                    "expected_graduation_date",
                    "Expected Graduation Date cannot be more than 10 years from the Admission Date.",
                )

        return cleaned_data


class DoctoralCommitteeForm(forms.ModelForm):

    committee_assignment_video = forms.FileField(
        required=False,
        widget=forms.FileInput(
            attrs={
                "class": "assignment-video-input",
                "accept": "video/mp4,video/webm,video/quicktime,video/x-m4v",
            }
        ),
    )

    remove_committee_assignment_video = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "assignment-video-remove",
            }
        ),
    )

    class Meta:
        model = DoctoralCommittee

        fields = [
            "phd_student",
            "chair_faculty",
            "formation_date",
            "approval_status",
        ]

        widgets = {
            "phd_student": forms.Select(
                attrs={
                    "class": "form-select assignment-select",
                    "data-placeholder": "Select PhD Student",
                }
            ),
            "chair_faculty": forms.Select(
                attrs={
                    "class": "form-select assignment-select",
                    "data-placeholder": "Select Chair Faculty",
                }
            ),
            "formation_date": forms.TextInput(
                attrs={
                    "class": "form-control flatpickr-date assignment-date",
                    "id": "formation_date",
                    "placeholder": "Select Formation Date",
                    "autocomplete": "off",
                    "readonly": True,
                    "data-no-choices": "true",
                    "data-input": True,
                    "data-date-format": "Y-m-d",
                }
            ),
            "approval_status": forms.Select(
                attrs={
                    "class": "form-select assignment-select",
                    "data-placeholder": "Select Approval Status",
                }
            ),
        }

        labels = {
            "phd_student": "PhD Student",
            "chair_faculty": "Chair Faculty",
            "formation_date": "Formation Date",
            "approval_status": "Approval Status",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            phd_students = PhDStudent.objects.filter(
                doctoral_committee__isnull=True,
                phd_program__status="ACTIVE",
                advisor__isnull=False,
                current_status="ACTIVE",
            ) | PhDStudent.objects.filter(
                pk=self.instance.phd_student.pk,
            )
        else:
            phd_students = PhDStudent.objects.filter(
                doctoral_committee__isnull=True,
                phd_program__status="ACTIVE",
                advisor__isnull=False,
                current_status="ACTIVE",
            )

        self.fields["phd_student"].queryset = (
            phd_students.distinct()
            .select_related(
                "student",
                "student__user",
                "phd_program",
                "advisor",
                "advisor__user",
            )
            .order_by(
                "student__user__first_name",
                "student__user__last_name",
            )
        )

        chair_queryset = FacultyProfile.objects.select_related(
            "user",
        ).order_by(
            "user__first_name",
            "user__last_name",
        )

        self.fields["chair_faculty"].queryset = chair_queryset

        self.fields["phd_student"].empty_label = "-- Select PhD Student --"
        self.fields["chair_faculty"].empty_label = "-- Select Chair Faculty --"

        if not self.instance.pk:
            self.fields["approval_status"].initial = "PENDING"

        

    def clean_formation_date(self):
        formation_date = self.cleaned_data.get("formation_date")

        if not formation_date:
            raise ValidationError("Formation Date is required.")

        today = timezone.now().date()

        if formation_date > today:
            raise ValidationError("Formation date cannot be in the future.")

        if formation_date.year < 2000:
            raise ValidationError("Formation date is invalid.")

        return formation_date

    def clean_phd_student(self):
        phd_student = self.cleaned_data.get("phd_student")

        if not phd_student:
            raise ValidationError("Please select a PhD student.")

        if not phd_student.phd_program:
            raise ValidationError(
                "The PhD student must be assigned to a PhD program before creating a doctoral committee."
            )

        if phd_student.phd_program.status != "ACTIVE":
            raise ValidationError(
                "The PhD student's PhD program must be active before creating a doctoral committee."
            )

        if phd_student.current_status != "ACTIVE":
            raise ValidationError(
                "The PhD student must be active before creating a doctoral committee."
            )

        if not phd_student.advisor:
            raise ValidationError(
                "Please assign a research advisor to the PhD student before creating a doctoral committee."
            )

        existing_committee = DoctoralCommittee.objects.filter(
            phd_student=phd_student,
        ).exclude(pk=self.instance.pk if self.instance and self.instance.pk else None)

        if existing_committee.exists():
            raise ValidationError("This PhD student already has a doctoral committee.")

        return phd_student

    def clean_chair_faculty(self):
        chair_faculty = self.cleaned_data.get("chair_faculty")

        if not chair_faculty:
            raise ValidationError("Please select a chair faculty.")

        if not FacultyProfile.objects.filter(pk=chair_faculty.pk).exists():
            raise ValidationError("Invalid chair faculty selected.")

        phd_student = self.cleaned_data.get("phd_student")

        if (
            phd_student
            and phd_student.advisor
            and phd_student.advisor.pk == chair_faculty.pk
        ):
            raise ValidationError(
                "The PhD student's research advisor cannot serve as the chair of the committee."
            )

        return chair_faculty

    def clean_approval_status(self):
        approval_status = self.cleaned_data.get("approval_status")

        if not approval_status:
            raise ValidationError("Approval Status is required.")

        valid_values = {
            value for value, label in self.fields["approval_status"].choices if value
        }

        if approval_status not in valid_values:
            raise ValidationError("Please select a valid approval status.")

        return approval_status

    def validate_video(self, uploaded_file, field_name):
        if not uploaded_file:
            return uploaded_file

        if uploaded_file.size <= 0:
            raise ValidationError(f"{field_name} cannot be empty.")

        max_size = 200 * 1024 * 1024

        if uploaded_file.size > max_size:
            raise ValidationError(f"{field_name} cannot be larger than 200 MB.")

        allowed_extensions = {
            ".mp4",
            ".webm",
            ".mov",
            ".m4v",
        }

        extension = Path(uploaded_file.name).suffix.lower()

        if extension not in allowed_extensions:
            raise ValidationError(
                f"{field_name} must be an MP4, WebM, MOV, or M4V video."
            )

        allowed_content_types = {
            "video/mp4",
            "video/webm",
            "video/quicktime",
            "video/x-m4v",
        }

        content_type = getattr(
            uploaded_file,
            "content_type",
            None,
        )

        if content_type and content_type not in allowed_content_types:
            raise ValidationError(f"{field_name} contains an unsupported video format.")

        filename = Path(uploaded_file.name).name

        if len(filename) > 255:
            raise ValidationError(f"{field_name} filename is too long.")

        if not filename.strip():
            raise ValidationError(f"{field_name} filename is invalid.")

        return uploaded_file

    def clean_committee_assignment_video(self):
        video = self.cleaned_data.get("committee_assignment_video")

        return self.validate_video(
            video,
            "Doctoral Committee Assignment Video",
        )

    def clean(self):
        cleaned_data = super().clean()

        phd_student = cleaned_data.get("phd_student")
        chair_faculty = cleaned_data.get("chair_faculty")
        formation_date = cleaned_data.get("formation_date")

        if phd_student:
            if not phd_student.phd_program:
                self.add_error(
                    "phd_student",
                    "The PhD student must have an assigned PhD program.",
                )

            elif phd_student.phd_program.status != "ACTIVE":
                self.add_error(
                    "phd_student",
                    "The assigned PhD program must be active.",
                )

            if phd_student.current_status != "ACTIVE":
                self.add_error(
                    "phd_student",
                    "The PhD student must be active.",
                )

            if not phd_student.advisor:
                self.add_error(
                    "phd_student",
                    "The PhD student must have a research advisor before committee formation.",
                )

        if phd_student and chair_faculty:
            if phd_student.advisor and phd_student.advisor.pk == chair_faculty.pk:
                self.add_error(
                    "chair_faculty",
                    "The PhD student's research advisor cannot serve as the chair of the committee.",
                )

        if formation_date:
            today = timezone.now().date()

            if formation_date > today:
                self.add_error(
                    "formation_date",
                    "Formation date cannot be in the future.",
                )

            if (
                phd_student
                and phd_student.admission_date
                and formation_date < phd_student.admission_date
            ):
                self.add_error(
                    "formation_date",
                    "Formation date cannot be earlier than the student's admission date.",
                )

        return cleaned_data


## Leo's Code End ##
