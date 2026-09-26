## Leo's Code Start ##

from django import forms
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from django.db import models
from Admin.bela_admin.models import Department
from decimal import Decimal, InvalidOperation
from Faculty.models import FacultyProfile

from Faculty.leo.models import (
    Coursework,
    FacultyCoursework,
    CourseworkSubmission,
    CourseworkEvaluation,
    PreliminaryExamEvaluation,
    DissertationEvaluation,
    DissertationApproval,
    DissertationAdvisorFeedback,
    DissertationChairReplyFeedback,
    DissertationAdvisorAdvice,
    ResearchMilestone,
    ResearchMilestoneSubmission,
    ResearchMilestoneEvaluation,
    AdvisorResearchAdvice,
    FinalDissertationAdvisorEvaluation,
    FinalDissertationCommitteeEvaluation,
)

from Students.models import (
    CommitteeMember,
    DoctoralCommittee,
    PhD,
    PhDStudent,
    PreliminaryExamination,
    DissertationProposal,
    DissertationProposalEvaluation,
    Dissertation,
    DoctoralCandidacy,
    AnnualProgressReview,
)
from decimal import Decimal, InvalidOperation

from django import forms
from django.utils import timezone

from Faculty.models import FacultyProfile
from Faculty.leo.models import (
    ResearchMilestoneEvaluation,
)
from Students.models import (
    CommitteeMember,
    DoctoralCommittee,
)


class CommitteeMemberForm(forms.ModelForm):
    class Meta:
        model = CommitteeMember
        fields = [
            "faculty",
            "role",
            "department",
        ]
        widgets = {
            "faculty": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "role": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "department": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.committee = kwargs.pop(
            "committee",
            None,
        )
        super().__init__(*args, **kwargs)

        if self.committee is None:
            raise ValueError("CommitteeMemberForm requires a committee instance.")

        faculty_queryset = (
            FacultyProfile.objects.filter(
                employment_status="ACTIVE",
            )
            .select_related(
                "user",
            )
            .order_by(
                "user__first_name",
            )
        )

        chair_faculty = self.committee.chair_faculty
        advisor = self.committee.phd_student.advisor

        if chair_faculty:
            faculty_queryset = faculty_queryset.exclude(
                pk=chair_faculty.pk,
            )

        if advisor:
            faculty_queryset = faculty_queryset.exclude(
                pk=advisor.pk,
            )

        self.fields["faculty"].queryset = faculty_queryset

        self.fields["department"].queryset = Department.objects.filter(
            status="ACTIVE",
        ).order_by(
            "department_name",
        )

        self.fields["role"].choices = [
            ("CO_CHAIR", "Co-Chair"),
            ("INTERNAL_MEMBER", "Internal Member"),
            ("EXTERNAL_MEMBER", "External Member"),
        ]

        self.fields["faculty"].empty_label = "Select Faculty"
        self.fields["department"].empty_label = "Select Department"

        self.fields["faculty"].label = "Faculty"
        self.fields["role"].label = "Role"
        self.fields["department"].label = "Department"

    def clean_faculty(self):
        faculty = self.cleaned_data.get(
            "faculty",
        )

        if not faculty:
            raise forms.ValidationError("Please select a faculty.")

        if faculty.employment_status != "ACTIVE":
            raise forms.ValidationError("Only active faculty can be assigned.")

        chair_faculty = self.committee.chair_faculty
        advisor = self.committee.phd_student.advisor

        if chair_faculty and faculty == chair_faculty:
            raise forms.ValidationError(
                "Chair Faculty cannot be added as a committee member."
            )

        if advisor and faculty == advisor:
            raise forms.ValidationError(
                "Advisor Faculty cannot be added as a committee member."
            )

        queryset = CommitteeMember.objects.filter(
            committee=self.committee,
            faculty=faculty,
        )

        if self.instance.pk:
            queryset = queryset.exclude(
                pk=self.instance.pk,
            )

        if queryset.exists():
            raise forms.ValidationError(
                "This faculty is already assigned to the committee."
            )

        return faculty

    def clean_department(self):
        department = self.cleaned_data.get(
            "department",
        )

        if not department:
            raise forms.ValidationError("Please select a department.")

        if department.status != "ACTIVE":
            raise forms.ValidationError("Only active departments can be selected.")

        return department

    def clean_role(self):
        role = self.cleaned_data.get(
            "role",
        )

        if not role:
            raise forms.ValidationError("Please select a role.")

        allowed_roles = [
            "CO_CHAIR",
            "INTERNAL_MEMBER",
            "EXTERNAL_MEMBER",
        ]

        if role not in allowed_roles:
            raise forms.ValidationError("Invalid committee role.")

        queryset = CommitteeMember.objects.filter(
            committee=self.committee,
            role=role,
        )

        if self.instance.pk:
            queryset = queryset.exclude(
                pk=self.instance.pk,
            )

        if queryset.exists():
            display = dict(
                CommitteeMember.ROLE_CHOICES,
            ).get(
                role,
                role,
            )

            raise forms.ValidationError(f"{display} already exists for this committee.")

        return role

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


class CourseworkForm(forms.ModelForm):
    class Meta:
        model = Coursework
        fields = [
            "program",
            "coursework_name",
            "description",
            "credits",
            "is_active",
        ]
        widgets = {
            "program": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "coursework_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter coursework name",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Enter coursework description",
                }
            ),
            "credits": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "step": 1,
                    "placeholder": "Enter credits",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.faculty = kwargs.pop("faculty", None)
        super().__init__(*args, **kwargs)
        if self.faculty is None:
            raise ValueError("CourseworkForm requires a faculty instance.")
        self.fields["program"].queryset = (
            PhD.objects.filter(
                phd_students__advisor=self.faculty,
                phd_students__current_status="ACTIVE",
            )
            .distinct()
            .order_by("program_name")
        )
        self.fields["program"].empty_label = "Select PhD Program"

    def clean_program(self):
        program = self.cleaned_data.get("program")
        if not program:
            raise forms.ValidationError("Please select a PhD program.")
        has_advisees = PhDStudent.objects.filter(
            advisor=self.faculty,
            phd_program=program,
            current_status="ACTIVE",
        ).exists()
        if not has_advisees:
            raise forms.ValidationError(
                "You do not have any active PhD students in this program."
            )
        return program

    def clean_coursework_name(self):
        coursework_name = self.cleaned_data.get("coursework_name")
        if not coursework_name:
            raise forms.ValidationError("Please enter a coursework name.")
        coursework_name = coursework_name.strip()
        if not coursework_name:
            raise forms.ValidationError("Coursework name cannot be empty.")
        return coursework_name

    def clean_credits(self):
        credits = self.cleaned_data.get("credits")
        if credits is None:
            raise forms.ValidationError("Please enter the coursework credits.")
        if credits <= 0:
            raise forms.ValidationError("Coursework credits must be greater than zero.")
        return credits

    def clean(self):
        cleaned_data = super().clean()
        program = cleaned_data.get("program")
        coursework_name = cleaned_data.get("coursework_name")
        if program and coursework_name:
            queryset = Coursework.objects.filter(
                program=program,
                coursework_name__iexact=coursework_name,
            )
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                self.add_error(
                    "coursework_name",
                    "This coursework already exists for the selected program.",
                )
        return cleaned_data

    def save(self, commit=True):
        coursework = super().save(commit=False)
        coursework.created_by = self.faculty
        if commit:
            coursework.save()
        return coursework


class FacultyCourseworkStudentSelect(forms.Select):
    def __init__(self, *args, faculty=None, **kwargs):
        self.faculty = faculty
        super().__init__(*args, **kwargs)

    def create_option(
        self,
        name,
        value,
        label,
        selected,
        index,
        subindex=None,
        attrs=None,
    ):
        option = super().create_option(
            name,
            value,
            label,
            selected,
            index,
            subindex=subindex,
            attrs=attrs,
        )
        student = getattr(value, "instance", None)
        if student and student.phd_program:
            program = student.phd_program
            department = program.department
            option["attrs"]["data-program-id"] = str(program.pk)
            option["attrs"]["data-program-name"] = program.program_name
            if department:
                option["attrs"]["data-department-id"] = str(department.pk)
                option["attrs"]["data-department-name"] = str(department)
        return option


class FacultyCourseworkForm(forms.ModelForm):
    department = forms.CharField(
        required=False,
        disabled=True,
        label="Department",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "id_department",
                "readonly": True,
            }
        ),
    )
    program = forms.ModelChoiceField(
        queryset=PhD.objects.none(),
        required=False,
        disabled=True,
        empty_label="Select PhD Program",
        label="PhD Program",
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_program",
            }
        ),
    )

    class Meta:
        model = FacultyCoursework
        fields = [
            "phd_student",
            "department",
            "program",
            "coursework",
            "start_date",
            "expected_completion_date",
            "completion_date",
            "status",
            "remarks",
        ]
        widgets = {
            "phd_student": FacultyCourseworkStudentSelect(
                attrs={
                    "class": "form-select",
                    "id": "id_phd_student",
                }
            ),
            "coursework": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "id_coursework",
                }
            ),
            "start_date": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "id": "id_start_date",
                    "autocomplete": "off",
                    "readonly": True,
                }
            ),
            "expected_completion_date": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "id": "id_expected_completion_date",
                    "autocomplete": "off",
                    "readonly": True,
                }
            ),
            "completion_date": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "id": "id_completion_date",
                    "autocomplete": "off",
                    "readonly": True,
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "id_status",
                }
            ),
            "remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "id": "id_remarks",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.faculty = kwargs.pop("faculty", None)
        super().__init__(*args, **kwargs)
        if self.faculty is None:
            raise ValueError("FacultyCourseworkForm requires a faculty instance.")
        self.fields["phd_student"].queryset = (
            PhDStudent.objects.filter(
                advisor=self.faculty,
                current_status="ACTIVE",
            )
            .select_related(
                "student",
                "student__user",
                "phd_program",
                "phd_program__department",
            )
            .order_by(
                "student__user__first_name",
                "student__user__last_name",
            )
        )
        self.fields["phd_student"].widget.faculty = self.faculty
        self.fields["coursework"].queryset = Coursework.objects.none()
        selected_student = None
        if self.instance and self.instance.pk:
            selected_student = self.instance.phd_student
        if not selected_student and self.data:
            student_id = self.data.get("phd_student")
            if student_id:
                try:
                    selected_student = (
                        self.fields["phd_student"]
                        .queryset.filter(pk=student_id)
                        .first()
                    )
                except (TypeError, ValueError):
                    selected_student = None
        if selected_student:
            program = selected_student.phd_program
            self.fields["program"].queryset = PhD.objects.filter(pk=program.pk)
            self.initial["program"] = program.pk
            department = getattr(
                program,
                "department",
                None,
            )
            self.initial["department"] = str(department) if department else ""
            if self.instance and self.instance.pk:
                current_coursework_id = self.instance.coursework_id
                self.fields["coursework"].queryset = (
                    Coursework.objects.filter(
                        program=program,
                        is_active=True,
                    )
                    .filter(
                        Q(pk=current_coursework_id)
                        | ~Q(faculty_courseworks__phd_student=selected_student)
                    )
                    .distinct()
                    .order_by("coursework_name")
                )
            else:
                assigned_coursework_ids = FacultyCoursework.objects.filter(
                    phd_student=selected_student,
                ).values_list(
                    "coursework_id",
                    flat=True,
                )
                self.fields["coursework"].queryset = (
                    Coursework.objects.filter(
                        program=program,
                        is_active=True,
                    )
                    .exclude(pk__in=assigned_coursework_ids)
                    .order_by("coursework_name")
                )

    def clean_phd_student(self):
        student = self.cleaned_data.get("phd_student")
        if not student:
            raise forms.ValidationError("Please select a PhD student.")
        if student.advisor_id != self.faculty.pk:
            raise forms.ValidationError(
                "You are not authorized to assign coursework to this student."
            )
        if student.current_status != "ACTIVE":
            raise forms.ValidationError(
                "Coursework can only be assigned to an active PhD student."
            )
        return student

    def clean_program(self):
        student = self.cleaned_data.get("phd_student")
        if not student:
            return None
        program = student.phd_program
        if not program:
            raise forms.ValidationError(
                "The selected student does not have a PhD program."
            )
        return program

    def clean_coursework(self):
        coursework = self.cleaned_data.get("coursework")
        if not coursework:
            raise forms.ValidationError("Please select a coursework.")
        if not coursework.is_active:
            raise forms.ValidationError("This coursework is no longer active.")
        return coursework

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get("phd_student")
        coursework = cleaned_data.get("coursework")
        program = cleaned_data.get("program")
        if not student:
            return cleaned_data
        actual_program = student.phd_program
        if not actual_program:
            self.add_error(
                "phd_student",
                "The selected student does not have a PhD program.",
            )
            return cleaned_data
        if program and program.pk != actual_program.pk:
            self.add_error(
                "program",
                "The selected program does not belong to this student.",
            )
        incomplete_assignments = FacultyCoursework.objects.filter(
            phd_student=student,
            status__in=[
                "NOT_STARTED",
                "IN_PROGRESS",
            ],
        )
        if self.instance and self.instance.pk:
            incomplete_assignments = incomplete_assignments.exclude(pk=self.instance.pk)
        if incomplete_assignments.exists():
            self.add_error(
                "phd_student",
                "This student already has an incomplete coursework. Complete the current coursework before assigning another one.",
            )
        if coursework:
            if coursework.program_id != actual_program.pk:
                self.add_error(
                    "coursework",
                    "This coursework does not belong to the student's PhD program.",
                )
            existing_assignment = FacultyCoursework.objects.filter(
                phd_student=student,
                coursework=coursework,
            )
            if self.instance and self.instance.pk:
                existing_assignment = existing_assignment.exclude(pk=self.instance.pk)
            if existing_assignment.exists():
                self.add_error(
                    "coursework",
                    "This coursework is already assigned to the selected PhD student.",
                )
        return cleaned_data

    def save(self, commit=True):
        coursework_assignment = super().save(commit=False)
        student = self.cleaned_data.get("phd_student")
        program = getattr(
            student,
            "phd_program",
            None,
        )
        coursework_assignment.program = program
        if commit:
            coursework_assignment.save()
        return coursework_assignment


class FacultyCourseworkUpdateForm(forms.ModelForm):

    department = forms.CharField(
        required=False,
        disabled=True,
        label="Department",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "id_department",
                "readonly": True,
            }
        ),
    )

    program = forms.ModelChoiceField(
        queryset=PhD.objects.none(),
        required=False,
        disabled=True,
        label="PhD Program",
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_program",
            }
        ),
    )

    class Meta:
        model = FacultyCoursework
        fields = [
            "phd_student",
            "department",
            "program",
            "coursework",
            "start_date",
            "expected_completion_date",
            "remarks",
        ]

        widgets = {
            "phd_student": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "id_phd_student",
                }
            ),
            "coursework": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "id_coursework",
                }
            ),
            "start_date": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "id": "id_start_date",
                    "autocomplete": "off",
                    "readonly": True,
                }
            ),
            "expected_completion_date": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "id": "id_expected_completion_date",
                    "autocomplete": "off",
                    "readonly": True,
                }
            ),
            "remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "id": "id_remarks",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.faculty = kwargs.pop(
            "faculty",
            None,
        )

        super().__init__(
            *args,
            **kwargs,
        )

        if self.faculty is None:
            raise ValueError("FacultyCourseworkUpdateForm requires a faculty instance.")

        assignment = self.instance

        self.fields["phd_student"].queryset = PhDStudent.objects.filter(
            advisor=self.faculty,
            current_status="ACTIVE",
        ).select_related(
            "student",
            "student__user",
            "phd_program",
            "phd_program__department",
        )

        if assignment and assignment.pk:
            student = assignment.phd_student
            program = student.phd_program
            coursework = assignment.coursework

            self.fields["phd_student"].initial = student
            self.fields["phd_student"].disabled = True

            self.fields["coursework"].queryset = Coursework.objects.filter(
                pk=coursework.pk,
            )

            self.fields["coursework"].initial = coursework
            self.fields["coursework"].disabled = True

            self.fields["program"].queryset = PhD.objects.filter(
                pk=program.pk,
            )

            self.fields["program"].initial = program

            department = getattr(
                program,
                "department",
                None,
            )

            self.fields["department"].initial = str(department) if department else ""

            self.fields["start_date"].initial = assignment.start_date
            self.fields["expected_completion_date"].initial = (
                assignment.expected_completion_date
            )
            self.fields["remarks"].initial = assignment.remarks

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get(
            "start_date",
        )

        expected_completion_date = cleaned_data.get(
            "expected_completion_date",
        )

        if (
            start_date
            and expected_completion_date
            and expected_completion_date < start_date
        ):
            self.add_error(
                "expected_completion_date",
                "Expected completion date must be after the start date.",
            )

        return cleaned_data


class CourseworkSubmissionForm(forms.ModelForm):
    class Meta:
        model = CourseworkSubmission
        fields = [
            "submission_file",
            "remarks",
        ]
        widgets = {
            "submission_file": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf,.doc,.docx",
                }
            ),
            "remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Enter submission remarks",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.faculty = kwargs.pop(
            "faculty",
            None,
        )
        self.coursework = kwargs.pop(
            "coursework",
            None,
        )
        super().__init__(
            *args,
            **kwargs,
        )
        if self.coursework is None:
            raise ValueError("CourseworkSubmissionForm requires a coursework instance.")

    def clean_submission_file(self):
        submission_file = self.cleaned_data.get(
            "submission_file",
        )
        if not submission_file:
            raise forms.ValidationError("Please upload the coursework submission file.")
        allowed_extensions = [
            ".pdf",
            ".doc",
            ".docx",
        ]
        file_name = submission_file.name.lower()
        if not any(file_name.endswith(extension) for extension in allowed_extensions):
            raise forms.ValidationError("Only PDF, DOC, and DOCX files are allowed.")
        max_size = 10 * 1024 * 1024
        if submission_file.size > max_size:
            raise forms.ValidationError("File size must not exceed 10 MB.")
        return submission_file

    def clean_remarks(self):
        remarks = self.cleaned_data.get(
            "remarks",
        )
        if remarks:
            remarks = remarks.strip()
        return remarks

    def clean(self):
        cleaned_data = super().clean()
        if self.coursework is None:
            return cleaned_data
        if self.coursework.status not in [
            "COMPLETED",
            "IN_PROGRESS",
        ]:
            raise forms.ValidationError(
                "Coursework must be in progress or completed before submitting."
            )
        if (
            self.faculty is not None
            and self.coursework.phd_student.advisor != self.faculty
        ):
            raise forms.ValidationError(
                "You are not authorized to submit this coursework."
            )
        existing_submission = CourseworkSubmission.objects.filter(
            coursework=self.coursework,
        )
        if self.instance.pk:
            existing_submission = existing_submission.exclude(
                pk=self.instance.pk,
            )
        if existing_submission.exists():
            raise forms.ValidationError(
                "A submission already exists for this coursework."
            )
        return cleaned_data

    def save(self, commit=True):
        submission = super().save(
            commit=False,
        )
        submission.coursework = self.coursework
        submission.status = "SUBMITTED"
        submission.submitted_at = timezone.now()
        if commit:
            submission.save()
        return submission


class CourseworkEvaluationForm(forms.ModelForm):
    class Meta:
        model = CourseworkEvaluation
        fields = [
            "marks",
            "faculty_feedback",
        ]
        widgets = {
            "marks": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "placeholder": "Enter marks",
                }
            ),
            "faculty_feedback": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Enter evaluation feedback",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.faculty = kwargs.pop("faculty", None)
        self.submission = kwargs.pop("submission", None)
        super().__init__(*args, **kwargs)
        if self.faculty is None:
            raise ValueError("CourseworkEvaluationForm requires a faculty instance.")
        if self.submission is None:
            raise ValueError("CourseworkEvaluationForm requires a submission instance.")

    def clean_marks(self):
        marks = self.cleaned_data.get("marks")
        if marks is None:
            raise forms.ValidationError("Please enter the marks.")
        if marks < 0:
            raise forms.ValidationError("Marks cannot be negative.")
        if marks > 100:
            raise forms.ValidationError("Marks cannot exceed 100.")
        return marks

    def clean_faculty_feedback(self):
        faculty_feedback = self.cleaned_data.get("faculty_feedback")
        if faculty_feedback:
            faculty_feedback = faculty_feedback.strip()
        return faculty_feedback

    def clean(self):
        cleaned_data = super().clean()
        if self.submission is None:
            return cleaned_data
        coursework = self.submission.coursework
        if coursework is None:
            raise forms.ValidationError("Invalid submission: coursework not found.")
        if not coursework.faculty_coursework_id:
            raise forms.ValidationError(
                "This submission is not associated with a valid coursework assignment."
            )
        if coursework.phd_student.advisor != self.faculty:
            raise forms.ValidationError(
                "You are not authorized to evaluate this submission."
            )
        if self.instance.pk is None:
            existing_evaluation = CourseworkEvaluation.objects.filter(
                submission=self.submission,
            ).exists()
            if existing_evaluation:
                raise forms.ValidationError(
                    "An evaluation already exists for this submission."
                )
        if self.instance.pk and self.instance.evaluated_by != self.faculty:
            raise forms.ValidationError(
                "You are not authorized to update this evaluation."
            )
        return cleaned_data

    def save(self, commit=True):
        evaluation = super().save(commit=False)
        evaluation.submission = self.submission
        evaluation.evaluated_by = self.faculty
        evaluation.evaluated_at = timezone.now()
        if commit:
            evaluation.save()
            self._update_related_objects(evaluation)
        return evaluation

    def _update_related_objects(self, evaluation):
        marks = evaluation.marks
        submission = evaluation.submission
        coursework = submission.coursework
        if marks >= 40:
            submission.status = "APPROVED"
            coursework.status = "COMPLETED"
        else:
            submission.status = "REJECTED"
            coursework.status = "FAILED"
        submission.reviewed_at = timezone.now()
        coursework.progress_percentage = 100
        coursework.completion_date = timezone.now().date()
        submission.save(update_fields=["status", "updated_at"])
        coursework.save(
            update_fields=[
                "status",
                "progress_percentage",
                "completion_date",
                "updated_at",
            ]
        )


class CourseworkEvaluationUpdateForm(forms.ModelForm):
    class Meta:
        model = CourseworkEvaluation
        fields = [
            "marks",
            "faculty_feedback",
        ]
        widgets = {
            "marks": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "placeholder": "Enter marks",
                }
            ),
            "faculty_feedback": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Enter evaluation feedback",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.faculty = kwargs.pop("faculty", None)
        super().__init__(*args, **kwargs)
        if self.faculty is None:
            raise ValueError(
                "CourseworkEvaluationUpdateForm requires a faculty instance."
            )

    def clean_marks(self):
        marks = self.cleaned_data.get("marks")
        if marks is None:
            raise forms.ValidationError("Please enter the marks.")
        if marks < 0:
            raise forms.ValidationError("Marks cannot be negative.")
        if marks > 100:
            raise forms.ValidationError("Marks cannot exceed 100.")
        return marks

    def clean_faculty_feedback(self):
        faculty_feedback = self.cleaned_data.get("faculty_feedback")
        if faculty_feedback:
            faculty_feedback = faculty_feedback.strip()
        return faculty_feedback

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.pk:
            if self.instance.evaluated_by != self.faculty:
                raise forms.ValidationError(
                    "You are not authorized to update this evaluation."
                )
        return cleaned_data

    def save(self, commit=True):
        evaluation = super().save(commit=False)
        evaluation.evaluated_at = timezone.now()
        if commit:
            evaluation.save()
            self._update_related_objects(evaluation)
        return evaluation

    def _update_related_objects(self, evaluation):
        marks = evaluation.marks
        submission = evaluation.submission
        coursework = submission.coursework
        if marks >= 40:
            submission.status = "APPROVED"
            coursework.status = "COMPLETED"
        else:
            submission.status = "REJECTED"
            coursework.status = "FAILED"
        submission.reviewed_at = timezone.now()
        coursework.progress_percentage = 100
        coursework.completion_date = timezone.now().date()
        submission.save(update_fields=["status", "reviewed_at", "updated_at"])
        coursework.save(
            update_fields=[
                "status",
                "progress_percentage",
                "completion_date",
                "updated_at",
            ]
        )

class PreliminaryExaminationForm(forms.ModelForm):
    class Meta:
        model = PreliminaryExamination
        fields = [
            "phd_student",
            "exam_type",
            "title",
            "description",
            "exam_date",
            "start_time",
            "end_time",
            "venue",
            "status",
            "is_published",
            "remarks",
        ]

        widgets = {
            "phd_student": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "exam_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                    "maxlength": 200,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "maxlength": 1000,
                }
            ),
            "exam_date": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "id": "id_exam_date",
                    "autocomplete": "off",
                    "readonly": True,
                }
            ),
            "start_time": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time",
                }
            ),
            "end_time": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time",
                }
            ),
            "venue": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "is_published": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "maxlength": 500,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.faculty = kwargs.pop(
            "faculty",
            None,
        )

        super().__init__(
            *args,
            **kwargs,
        )

        if self.faculty is None:
            raise ValueError(
                "PreliminaryExaminationForm requires a faculty instance."
            )

        passed_student_ids = PreliminaryExamination.objects.filter(
            result="PASS",
        ).values_list(
            "phd_student_id",
            flat=True,
        )

        self.fields["phd_student"].queryset = (
            PhDStudent.objects.filter(
                doctoral_committee__chair_faculty=self.faculty,
                current_status="ACTIVE",
            )
            .exclude(
                phd_student_id__in=passed_student_ids,
            )
            .select_related(
                "student",
                "student__user",
                "advisor",
                "phd_program",
                "doctoral_committee",
            )
            .prefetch_related(
                "doctoral_committee__committee_members__faculty__user",
            )
            .order_by(
                "student__user__first_name",
                "student__user__last_name",
            )
        )

        self.fields["phd_student"].empty_label = "Select PhD Student"

    def clean_phd_student(self):
        phd_student = self.cleaned_data.get(
            "phd_student",
        )

        if not phd_student:
            raise forms.ValidationError(
                "Please select a PhD student."
            )

        if phd_student.current_status != "ACTIVE":
            raise forms.ValidationError(
                "Only active PhD students can be selected."
            )

        has_passed = PreliminaryExamination.objects.filter(
            phd_student=phd_student,
            result="PASS",
        ).exists()

        if has_passed:
            raise forms.ValidationError(
                "This student has already passed the Preliminary / Qualifying Examination."
            )

        try:
            committee = phd_student.doctoral_committee
        except DoctoralCommittee.DoesNotExist:
            raise forms.ValidationError(
                "Doctoral committee has not been created for this student."
            )

        if committee.chair_faculty != self.faculty:
            raise forms.ValidationError(
                "You are not the Chair Faculty for this student."
            )

        return phd_student

    def clean_title(self):
        title = self.cleaned_data.get(
            "title",
        )

        if not title or not title.strip():
            raise forms.ValidationError(
                "Please enter the examination title."
            )

        title = title.strip()

        if len(title) < 5:
            raise forms.ValidationError(
                "Examination title must contain at least 5 characters."
            )

        if len(title) > 200:
            raise forms.ValidationError(
                "Examination title cannot exceed 200 characters."
            )

        return title

    def clean_exam_date(self):
        exam_date = self.cleaned_data.get(
            "exam_date",
        )

        if not exam_date:
            raise forms.ValidationError(
                "Please select the examination date."
            )

        if exam_date < timezone.now().date():
            raise forms.ValidationError(
                "Examination date cannot be earlier than today."
            )

        return exam_date

    def clean_venue(self):
        venue = self.cleaned_data.get(
            "venue",
        )

        if not venue or not venue.strip():
            raise forms.ValidationError(
                "Please enter the examination venue."
            )

        venue = venue.strip()

        if len(venue) < 3:
            raise forms.ValidationError(
                "Examination venue must contain at least 3 characters."
            )

        return venue

    def clean(self):
        cleaned_data = super().clean()

        phd_student = cleaned_data.get(
            "phd_student",
        )

        exam_type = cleaned_data.get(
            "exam_type",
        )

        exam_date = cleaned_data.get(
            "exam_date",
        )

        start_time = cleaned_data.get(
            "start_time",
        )

        end_time = cleaned_data.get(
            "end_time",
        )

        if start_time and end_time and start_time >= end_time:
            self.add_error(
                "end_time",
                "End time must be later than the start time.",
            )

        if phd_student and exam_type and exam_date:
            queryset = PreliminaryExamination.objects.filter(
                phd_student=phd_student,
                exam_type=exam_type,
                exam_date=exam_date,
            )

            if self.instance.pk:
                queryset = queryset.exclude(
                    pk=self.instance.pk,
                )

            if queryset.exists():
                self.add_error(
                    "exam_date",
                    (
                        "An examination already exists for this "
                        "student on the selected date."
                    ),
                )

        return cleaned_data


class PreliminaryExamEvaluationForm(forms.ModelForm):
    class Meta:
        model = PreliminaryExamEvaluation
        fields = [
            "knowledge_score",
            "research_aptitude_score",
            "presentation_score",
            "technical_score",
            "comments",
            "recommendation",
        ]
        widgets = {
            "knowledge_score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "max": 100,
                }
            ),
            "research_aptitude_score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "max": 100,
                }
            ),
            "presentation_score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "max": 100,
                }
            ),
            "technical_score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "max": 100,
                }
            ),
            "comments": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                }
            ),
            "recommendation": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.faculty = kwargs.pop(
            "faculty",
            None,
        )
        self.examination = kwargs.pop(
            "examination",
            None,
        )
        super().__init__(*args, **kwargs)
        if self.faculty is None:
            raise ValueError(
                "PreliminaryExamEvaluationForm requires a faculty instance."
            )
        if self.examination is None:
            raise ValueError(
                "PreliminaryExamEvaluationForm requires an examination instance."
            )

    def clean_knowledge_score(self):
        score = self.cleaned_data.get(
            "knowledge_score",
        )
        if score is None:
            raise forms.ValidationError("Please enter the knowledge score.")
        if score < 0 or score > 100:
            raise forms.ValidationError("Knowledge score must be between 0 and 100.")
        return score

    def clean_research_aptitude_score(self):
        score = self.cleaned_data.get(
            "research_aptitude_score",
        )
        if score is None:
            raise forms.ValidationError("Please enter the research aptitude score.")
        if score < 0 or score > 100:
            raise forms.ValidationError(
                "Research aptitude score must be between 0 and 100."
            )
        return score

    def clean_presentation_score(self):
        score = self.cleaned_data.get(
            "presentation_score",
        )
        if score is None:
            raise forms.ValidationError("Please enter the presentation score.")
        if score < 0 or score > 100:
            raise forms.ValidationError("Presentation score must be between 0 and 100.")
        return score

    def clean_technical_score(self):
        score = self.cleaned_data.get(
            "technical_score",
        )
        if score is None:
            raise forms.ValidationError("Please enter the technical score.")
        if score < 0 or score > 100:
            raise forms.ValidationError("Technical score must be between 0 and 100.")
        return score

    def clean_recommendation(self):
        recommendation = self.cleaned_data.get(
            "recommendation",
        )
        if not recommendation:
            raise forms.ValidationError("Please select a recommendation.")
        return recommendation

    def clean(self):
        cleaned_data = super().clean()
        if self.examination.status != "SCHEDULED":
            raise forms.ValidationError(
                "Evaluations can only be submitted for scheduled examinations."
            )
        if not self.examination.is_published:
            raise forms.ValidationError("This examination has not been published.")
        if self.examination.result != "PENDING":
            raise forms.ValidationError("Evaluation is closed for this examination.")
        if (
            PreliminaryExamEvaluation.objects.filter(
                examination=self.examination,
                faculty=self.faculty,
            )
            .exclude(
                pk=self.instance.pk,
            )
            .exists()
        ):
            raise forms.ValidationError(
                "You have already submitted an evaluation for this examination."
            )
        committee = self.examination.phd_student.doctoral_committee
        is_committee_member = CommitteeMember.objects.filter(
            committee=committee,
            faculty=self.faculty,
        ).exists()
        is_advisor = self.examination.phd_student.advisor == self.faculty
        if not is_committee_member and not is_advisor:
            raise forms.ValidationError(
                "You are not authorized to evaluate this examination."
            )
        if self.instance.pk and self.instance.is_submitted:
            raise forms.ValidationError("Submitted evaluations cannot be modified.")
        return cleaned_data

    def save(self, commit=True):
        evaluation = super().save(
            commit=False,
        )
        evaluation.examination = self.examination
        evaluation.faculty = self.faculty
        evaluation.is_submitted = True
        if commit:
            evaluation.save()
        return evaluation


class DissertationProposalAdvisorReviewForm(forms.ModelForm):

    class Meta:
        model = DissertationProposal
        fields = [
            "advisor_review_status",
            "advisor_review_remarks",
        ]
        widgets = {
            "advisor_review_status": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "advPrStatus",
                }
            ),
            "advisor_review_remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "id": "advPrRemarks",
                    "rows": 9,
                    "minlength": 20,
                    "maxlength": 2000,
                    "placeholder": "Write your academic assessment, observations, recommendations, required corrections, or other relevant feedback...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.faculty = kwargs.pop("faculty", None)

        super().__init__(*args, **kwargs)

        if self.faculty is None:
            raise ValueError(
                "DissertationProposalAdvisorReviewForm requires a faculty instance."
            )

        self.fields["advisor_review_status"].label = "Review Decision"
        self.fields["advisor_review_remarks"].label = "Advisor Remarks"

        self.fields["advisor_review_status"].required = True
        self.fields["advisor_review_remarks"].required = True

    def clean_advisor_review_status(self):
        status = self.cleaned_data.get("advisor_review_status")

        if not status:
            raise forms.ValidationError("Please select a review decision.")

        valid_statuses = [
            "APPROVED",
            "REVISION_REQUIRED",
            "REJECTED",
        ]

        if status not in valid_statuses:
            raise forms.ValidationError("Invalid advisor review decision.")

        return status

    def clean_advisor_review_remarks(self):
        remarks = self.cleaned_data.get("advisor_review_remarks")

        if not remarks or not remarks.strip():
            raise forms.ValidationError("Advisor review remarks are required.")

        remarks = remarks.strip()

        if len(remarks) < 20:
            raise forms.ValidationError(
                "Advisor review remarks must contain at least 20 characters."
            )

        if len(remarks) > 2000:
            raise forms.ValidationError(
                "Advisor review remarks cannot exceed 2000 characters."
            )

        return remarks

    def clean(self):
        cleaned_data = super().clean()

        if not self.instance.pk:
            raise forms.ValidationError(
                "A dissertation proposal is required for advisor review."
            )

        if self.instance.phd_student.advisor != self.faculty:
            raise forms.ValidationError(
                "You are not authorized to review this dissertation proposal."
            )

        if (
            self.instance.advisor_review_status != "PENDING"
            or self.instance.advisor_reviewed_at
        ):
            raise forms.ValidationError("Advisor review has already been submitted.")

        return cleaned_data

    def save(self, commit=True):
        proposal = super().save(commit=False)

        proposal.advisor_reviewed_at = timezone.now()

        if commit:
            proposal.save()

        return proposal


class DissertationProposalCommitteeEvaluationForm(forms.ModelForm):
    class Meta:
        model = DissertationProposalEvaluation
        fields = [
            "score",
            "recommendation",
            "comments",
        ]
        widgets = {
            "score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "max": 100,
                    "step": "0.01",
                    "placeholder": "Enter score",
                }
            ),
            "recommendation": forms.Select(
                attrs={
                    "class": "form-select choices",
                }
            ),
            "comments": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Enter your evaluation comments",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.faculty = kwargs.pop("faculty", None)
        self.proposal = kwargs.pop("proposal", None)

        super().__init__(*args, **kwargs)

        if self.faculty is None:
            raise ValueError(
                "DissertationProposalCommitteeEvaluationForm requires a faculty instance."
            )

        if self.proposal is None:
            raise ValueError(
                "DissertationProposalCommitteeEvaluationForm requires a proposal instance."
            )

    def clean_score(self):
        score = self.cleaned_data.get("score")

        if score is None:
            raise forms.ValidationError("Please enter the evaluation score.")

        if score < 0 or score > 100:
            raise forms.ValidationError("Evaluation score must be between 0 and 100.")

        return score

    def clean_recommendation(self):
        recommendation = self.cleaned_data.get("recommendation")

        if not recommendation:
            raise forms.ValidationError("Please select a recommendation.")

        return recommendation

    def clean_comments(self):
        comments = self.cleaned_data.get("comments")

        if not comments or not comments.strip():
            raise forms.ValidationError("Evaluation comments are required.")

        comments = comments.strip()

        if len(comments) < 20:
            raise forms.ValidationError(
                "Evaluation comments must contain at least 20 characters."
            )

        if len(comments) > 5000:
            raise forms.ValidationError(
                "Evaluation comments cannot exceed 5000 characters."
            )

        return comments

    def clean(self):
        cleaned_data = super().clean()

        try:
            committee = self.proposal.phd_student.doctoral_committee
        except DoctoralCommittee.DoesNotExist:
            raise forms.ValidationError(
                "Doctoral committee has not been created for this student."
            )

        committee_member = CommitteeMember.objects.filter(
            committee=committee,
            faculty=self.faculty,
        ).first()

        if not committee_member:
            raise forms.ValidationError(
                "You are not authorized to evaluate this dissertation proposal."
            )

        existing_evaluation = DissertationProposalEvaluation.objects.filter(
            proposal=self.proposal,
            committee_member=committee_member,
        )

        if self.instance.pk:
            existing_evaluation = existing_evaluation.exclude(pk=self.instance.pk)

        if existing_evaluation.exists():
            raise forms.ValidationError(
                "You have already submitted your evaluation for this proposal."
            )

        if self.instance.pk and self.instance.is_submitted:
            raise forms.ValidationError("Submitted evaluations cannot be modified.")

        if not self.proposal:
            raise forms.ValidationError(
                "A dissertation proposal is required for evaluation."
            )

        return cleaned_data

    def save(self, commit=True):
        evaluation = super().save(commit=False)

        committee = self.proposal.phd_student.doctoral_committee

        committee_member = CommitteeMember.objects.get(
            committee=committee,
            faculty=self.faculty,
        )

        evaluation.proposal = self.proposal
        evaluation.committee_member = committee_member
        evaluation.is_submitted = True
        evaluation.submitted_at = timezone.now()

        if commit:
            evaluation.save()

        return evaluation


class DissertationProposalFinalizationForm(forms.ModelForm):
    class Meta:
        model = DissertationProposal
        fields = [
            "final_remarks",
        ]
        widgets = {
            "final_remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 7,
                    "placeholder": "Enter final remarks for the dissertation proposal",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.faculty = kwargs.pop("faculty", None)

        super().__init__(*args, **kwargs)

        if self.faculty is None:
            raise ValueError(
                "DissertationProposalFinalizationForm requires a faculty instance."
            )

        self.fields["final_remarks"].label = "Final Remarks"

    def clean_final_remarks(self):
        remarks = self.cleaned_data.get("final_remarks")

        if not remarks or not remarks.strip():
            raise forms.ValidationError("Final remarks are required.")

        remarks = remarks.strip()

        if len(remarks) < 20:
            raise forms.ValidationError(
                "Final remarks must contain at least 20 characters."
            )

        if len(remarks) > 5000:
            raise forms.ValidationError("Final remarks cannot exceed 5000 characters.")

        return remarks

    def clean(self):
        cleaned_data = super().clean()

        if not self.instance.pk:
            raise forms.ValidationError(
                "A dissertation proposal is required for finalization."
            )

        try:
            committee = self.instance.phd_student.doctoral_committee
        except DoctoralCommittee.DoesNotExist:
            raise forms.ValidationError("Doctoral committee has not been created.")

        if committee.chair_faculty != self.faculty:
            raise forms.ValidationError(
                "Only the Chair Faculty can finalize this dissertation proposal."
            )

        if self.instance.advisor_review_status not in ["APPROVED"]:
            raise forms.ValidationError(
                "Advisor approval is required before finalizing the proposal."
            )

        total_members = committee.committee_members.count()

        submitted_count = DissertationProposalEvaluation.objects.filter(
            proposal=self.instance,
            committee_member__committee=committee,
            is_submitted=True,
        ).count()

        if submitted_count != total_members:
            raise forms.ValidationError(
                "All committee members must submit their evaluations before finalization."
            )

        if self.instance.finalized_at:
            raise forms.ValidationError(
                "This dissertation proposal has already been finalized."
            )

        return cleaned_data

    def save(self, commit=True):
        proposal = super().save(commit=False)

        proposal.finalized_at = timezone.now()
        proposal.finalized_by = self.faculty

        if commit:
            proposal.save()

        return proposal


class DissertationEvaluationForm(forms.ModelForm):
    class Meta:
        model = DissertationEvaluation
        fields = [
            "score",
            "recommendation",
            "remarks",
        ]
        widgets = {
            "score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "max": 100,
                    "step": "0.01",
                    "placeholder": "Enter overall score",
                }
            ),
            "recommendation": forms.Select(
                attrs={
                    "class": "form-select choices",
                }
            ),
            "remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Enter evaluation remarks",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.faculty = kwargs.pop("faculty", None)
        self.dissertation = kwargs.pop("dissertation", None)

        super().__init__(*args, **kwargs)

        if self.faculty is None:
            raise ValueError("DissertationEvaluationForm requires a faculty instance.")

        if self.dissertation is None:
            raise ValueError(
                "DissertationEvaluationForm requires a dissertation instance."
            )

    def clean_score(self):
        score = self.cleaned_data.get("score")

        if score is None:
            raise forms.ValidationError("Please enter the overall score.")

        if score < 0 or score > 100:
            raise forms.ValidationError("Overall score must be between 0 and 100.")

        return score

    def clean_recommendation(self):
        recommendation = self.cleaned_data.get("recommendation")

        if not recommendation:
            raise forms.ValidationError("Please select a recommendation.")

        return recommendation

    def clean_remarks(self):
        remarks = self.cleaned_data.get("remarks")

        if not remarks:
            raise forms.ValidationError("Remarks are required.")

        remarks = remarks.strip()

        if len(remarks) < 20:
            raise forms.ValidationError("Remarks must contain at least 20 characters.")

        if len(remarks) > 3000:
            raise forms.ValidationError("Remarks cannot exceed 3000 characters.")

        return remarks

    def clean(self):
        cleaned_data = super().clean()

        try:
            committee = self.dissertation.phd_student.doctoral_committee
        except DoctoralCommittee.DoesNotExist:
            raise forms.ValidationError("Doctoral committee has not been created.")

        committee_member = CommitteeMember.objects.filter(
            committee=committee,
            faculty=self.faculty,
        ).first()

        if not committee_member:
            raise forms.ValidationError(
                "You are not authorized to evaluate this dissertation."
            )

        existing_evaluation = DissertationEvaluation.objects.filter(
            dissertation=self.dissertation,
            committee_member=committee_member,
        )

        if self.instance.pk:
            existing_evaluation = existing_evaluation.exclude(pk=self.instance.pk)

        if existing_evaluation.exists():
            raise forms.ValidationError("You have already submitted your evaluation.")

        if self.instance.pk and self.instance.is_submitted:
            raise forms.ValidationError("Submitted evaluations cannot be modified.")

        return cleaned_data

    def save(self, commit=True):
        evaluation = super().save(commit=False)

        committee = self.dissertation.phd_student.doctoral_committee

        committee_member = CommitteeMember.objects.get(
            committee=committee,
            faculty=self.faculty,
        )

        evaluation.dissertation = self.dissertation
        evaluation.committee_member = committee_member
        evaluation.is_submitted = True
        evaluation.submitted_at = timezone.now()

        if commit:
            evaluation.save()

        return evaluation


class DissertationApprovalForm(forms.ModelForm):
    class Meta:
        model = DissertationApproval
        fields = [
            "decision",
            "final_remarks",
        ]
        widgets = {
            "decision": forms.Select(
                attrs={
                    "class": "form-select choices",
                }
            ),
            "final_remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Enter final remarks",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.faculty = kwargs.pop("faculty", None)
        self.dissertation = kwargs.pop("dissertation", None)

        super().__init__(*args, **kwargs)

        if self.faculty is None:
            raise ValueError("DissertationApprovalForm requires a faculty instance.")

        if self.dissertation is None:
            raise ValueError(
                "DissertationApprovalForm requires a dissertation instance."
            )

    def clean_decision(self):
        decision = self.cleaned_data.get("decision")

        if not decision:
            raise forms.ValidationError("Please select a final decision.")

        return decision

    def clean_final_remarks(self):
        remarks = self.cleaned_data.get("final_remarks")

        if not remarks:
            raise forms.ValidationError("Final remarks are required.")

        remarks = remarks.strip()

        if len(remarks) < 20:
            raise forms.ValidationError(
                "Final remarks must contain at least 20 characters."
            )

        if len(remarks) > 3000:
            raise forms.ValidationError("Final remarks cannot exceed 3000 characters.")

        return remarks

    def clean(self):
        cleaned_data = super().clean()

        try:
            committee = self.dissertation.phd_student.doctoral_committee
        except DoctoralCommittee.DoesNotExist:
            raise forms.ValidationError("Doctoral committee has not been created.")

        if committee.chair_faculty != self.faculty:
            raise forms.ValidationError(
                "You are not authorized to approve this dissertation."
            )

        total_members = committee.committee_members.count()

        submitted_count = DissertationEvaluation.objects.filter(
            dissertation=self.dissertation,
            committee_member__committee=committee,
            is_submitted=True,
        ).count()

        if submitted_count != total_members:
            raise forms.ValidationError(
                "All committee members must submit their evaluations before the final decision."
            )

        if self.instance.pk and self.instance.decision != "PENDING":
            raise forms.ValidationError(
                "The final decision has already been submitted."
            )

        return cleaned_data

    def save(self, commit=True):
        approval = super().save(commit=False)

        approval.dissertation = self.dissertation
        approval.chair_faculty = self.faculty
        approval.approved_at = timezone.now()

        if commit:
            approval.save()

        return approval


class DoctoralCandidacyForm(forms.ModelForm):

    class Meta:
        model = DoctoralCandidacy
        fields = [
            "phd_student",
            "candidacy_date",
        ]

        widgets = {
            "phd_student": forms.Select(
                attrs={
                    "class": "form-select dc-choices-select",
                    "id": "id_phd_student",
                    "form": "candidacyForm",
                    "data-choices": "doctoral-student",
                    "data-placeholder": "Select PhD Student",
                }
            ),
            "candidacy_date": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "id": "id_candidacy_date",
                    "autocomplete": "off",
                    "readonly": True,
                }
            ),
        }

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        self.faculty = kwargs.pop(
            "faculty",
            None,
        )

        super().__init__(
            *args,
            **kwargs,
        )

        if self.faculty is None:
            raise ValueError("DoctoralCandidacyForm requires a faculty instance.")

        bound_student_id = None

        if self.is_bound:
            bound_student_id = self.data.get("phd_student")

        eligible_students = (
            PhDStudent.objects.filter(
                doctoral_committee__chair_faculty=self.faculty,
                doctoral_committee__approval_status="APPROVED",
                current_status="ACTIVE",
            )
            .exclude(
                advisor=self.faculty,
            )
            .exclude(
                doctoral_candidacy__isnull=False,
            )
            .select_related(
                "student",
                "student__user",
                "advisor",
                "phd_program",
                "doctoral_committee",
            )
            .order_by(
                "student__user__first_name",
                "student__user__last_name",
            )
            .distinct()
        )

        if self.instance.pk:
            eligible_students = PhDStudent.objects.filter(
                pk=self.instance.phd_student_id,
                doctoral_committee__chair_faculty=self.faculty,
                doctoral_committee__approval_status="APPROVED",
                current_status="ACTIVE",
            ).select_related(
                "student",
                "student__user",
                "advisor",
                "phd_program",
                "doctoral_committee",
            )

        elif bound_student_id:
            bound_student = (
                PhDStudent.objects.filter(
                    pk=bound_student_id,
                    doctoral_committee__chair_faculty=self.faculty,
                    doctoral_committee__approval_status="APPROVED",
                    current_status="ACTIVE",
                )
                .exclude(
                    advisor=self.faculty,
                )
                .exclude(
                    doctoral_candidacy__isnull=False,
                )
                .select_related(
                    "student",
                    "student__user",
                    "advisor",
                    "phd_program",
                    "doctoral_committee",
                )
                .first()
            )

            if bound_student:
                eligible_students = (
                    PhDStudent.objects.filter(
                        Q(
                            doctoral_committee__chair_faculty=self.faculty,
                            doctoral_committee__approval_status="APPROVED",
                            current_status="ACTIVE",
                            advisor__isnull=False,
                            doctoral_candidacy__isnull=True,
                        )
                        | Q(
                            pk=bound_student.pk,
                        )
                    )
                    .exclude(
                        advisor=self.faculty,
                    )
                    .select_related(
                        "student",
                        "student__user",
                        "advisor",
                        "phd_program",
                        "doctoral_committee",
                    )
                    .order_by(
                        "student__user__first_name",
                        "student__user__last_name",
                    )
                    .distinct()
                )

        self.fields["phd_student"].queryset = eligible_students
        self.fields["phd_student"].empty_label = "Select PhD Student"

    def clean_phd_student(
        self,
    ):
        phd_student = self.cleaned_data.get("phd_student")

        if not phd_student:
            raise forms.ValidationError("Please select a PhD student.")

        if phd_student.current_status != "ACTIVE":
            raise forms.ValidationError("Only active PhD students can be selected.")

        if phd_student.advisor_id and phd_student.advisor_id == self.faculty.pk:
            raise forms.ValidationError(
                "You cannot create doctoral candidacy for your own advisee."
            )

        committee = (
            DoctoralCommittee.objects.filter(
                phd_student=phd_student,
                approval_status="APPROVED",
                chair_faculty=self.faculty,
            )
            .select_related(
                "chair_faculty",
            )
            .first()
        )

        if not committee:
            raise forms.ValidationError(
                "The student does not have an approved doctoral committee assigned to you as Chair Faculty."
            )

        existing_candidacy = DoctoralCandidacy.objects.filter(
            phd_student=phd_student,
        )

        if self.instance.pk:
            existing_candidacy = existing_candidacy.exclude(
                pk=self.instance.pk,
            )

        if existing_candidacy.exists():
            raise forms.ValidationError(
                "This student already has a doctoral candidacy record."
            )

        return phd_student

    def clean_candidacy_date(
        self,
    ):
        candidacy_date = self.cleaned_data.get("candidacy_date")

        if not candidacy_date:
            raise forms.ValidationError("Please select the candidacy date.")

        if candidacy_date > timezone.now().date():
            raise forms.ValidationError("Candidacy date cannot be in the future.")

        return candidacy_date

    def clean(
        self,
    ):
        cleaned_data = super().clean()
        phd_student = cleaned_data.get("phd_student")

        if not phd_student:
            return cleaned_data

        committee = (
            DoctoralCommittee.objects.filter(
                phd_student=phd_student,
                approval_status="APPROVED",
                chair_faculty=self.faculty,
            )
            .select_related(
                "chair_faculty",
            )
            .first()
        )

        if not committee:
            self.add_error(
                "phd_student",
                "Only the assigned Chair Faculty can create this doctoral candidacy.",
            )
            return cleaned_data

        required_credits = (
            getattr(
                phd_student.phd_program,
                "total_credits_required",
                0,
            )
            or 0
        )

        completed_credits = (
            FacultyCoursework.objects.filter(
                phd_student=phd_student,
                status="COMPLETED",
            ).aggregate(total=Sum("coursework__credits"))["total"]
            or 0
        )

        if required_credits <= 0:
            self.add_error(
                "phd_student",
                "The required coursework credits are not configured for this PhD program.",
            )
        elif completed_credits < required_credits:
            remaining_credits = required_credits - completed_credits
            self.add_error(
                "phd_student",
                (
                    "Doctoral candidacy cannot be created because the required "
                    "coursework credits have not been completed. "
                    f"Required: {required_credits}, "
                    f"Completed: {completed_credits}, "
                    f"Remaining: {remaining_credits}."
                ),
            )

        passed_exam = PreliminaryExamination.objects.filter(
            phd_student=phd_student,
            result="PASS",
            status="COMPLETED",
            is_published=True,
        ).exists()

        if not passed_exam:
            self.add_error(
                "phd_student",
                (
                    "Doctoral candidacy cannot be created because the student "
                    "has not passed the Preliminary / Qualifying Examination."
                ),
            )

        proposal_approved = DissertationProposal.objects.filter(
            phd_student=phd_student,
            result="APPROVED",
        ).exists()

        if not proposal_approved:
            self.add_error(
                "phd_student",
                (
                    "Doctoral candidacy cannot be created because the "
                    "Dissertation Proposal has not been approved."
                ),
            )

        return cleaned_data


class AnnualProgressReviewForm(forms.ModelForm):

    class Meta:

        model = AnnualProgressReview

        fields = [
            "phd_student",
            "review_year",
            "progress_score",
            "status",
            "committee_comments",
        ]

        widgets = {
            "phd_student": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "review_year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "readonly": True,
                    "min": 2000,
                    "max": 2100,
                    "step": 1,
                }
            ),
            "progress_score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "max": 100,
                    "step": "0.01",
                    "placeholder": "Enter progress score",
                }
            ),
            "status": forms.RadioSelect(
                attrs={
                    "class": "aprf-status-radio",
                }
            ),
            "committee_comments": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "maxlength": 5000,
                    "placeholder": "Enter the committee's annual progress assessment and comments",
                }
            ),
        }

    def __init__(
        self,
        *args,
        **kwargs,
    ):

        self.faculty = kwargs.pop(
            "faculty",
            None,
        )

        super().__init__(
            *args,
            **kwargs,
        )

        if self.faculty is None:
            raise ValueError("AnnualProgressReviewForm requires a faculty instance.")

        chair_students = (
            PhDStudent.objects.filter(
                doctoral_committee__chair_faculty=self.faculty,
                doctoral_committee__approval_status="APPROVED",
                current_status="ACTIVE",
            )
            .select_related(
                "student",
                "student__user",
                "phd_program",
                "phd_program__department",
                "advisor",
                "advisor__user",
            )
            .distinct()
            .order_by(
                "student__user__first_name",
                "student__user__last_name",
            )
        )

        self.fields["phd_student"].queryset = chair_students

        self.fields["phd_student"].empty_label = "Select PhD Student"

        current_year = timezone.now().year

        if self.instance.pk:
            review_year = self.instance.review_year
        else:
            review_year = current_year

        self.fields["review_year"].initial = review_year

        self.fields["review_year"].disabled = True

    def clean_phd_student(
        self,
    ):

        phd_student = self.cleaned_data.get(
            "phd_student",
        )

        if not phd_student:
            raise forms.ValidationError("Please select a PhD student.")

        if phd_student.current_status != "ACTIVE":
            raise forms.ValidationError("Only active PhD students can be selected.")

        chair_committee = DoctoralCommittee.objects.filter(
            phd_student=phd_student,
            chair_faculty=self.faculty,
            approval_status="APPROVED",
        ).exists()

        if not chair_committee:
            raise forms.ValidationError(
                "You are not the assigned Chair Faculty for this student."
            )

        return phd_student

    def clean_review_year(
        self,
    ):

        review_year = self.cleaned_data.get(
            "review_year",
        )

        current_year = timezone.now().year

        if review_year is None:
            raise forms.ValidationError("Review year could not be determined.")

        if review_year < 2000:
            raise forms.ValidationError("Review year must be 2000 or later.")

        if review_year > 2100:
            raise forms.ValidationError("Please enter a valid review year.")

        if self.instance.pk:

            if review_year != self.instance.review_year:
                raise forms.ValidationError("The review year cannot be changed.")

        else:

            if review_year != current_year:
                raise forms.ValidationError("The review year must be the current year.")

        return review_year

    def clean_progress_score(
        self,
    ):

        progress_score = self.cleaned_data.get(
            "progress_score",
        )

        if progress_score is None:
            raise forms.ValidationError("Please enter the progress score.")

        if progress_score < 0:
            raise forms.ValidationError("Progress score cannot be negative.")

        if progress_score > 100:
            raise forms.ValidationError("Progress score cannot exceed 100.")

        return progress_score

    def clean_status(
        self,
    ):

        status = self.cleaned_data.get(
            "status",
        )

        allowed_statuses = [
            "SATISFACTORY",
            "NEEDS_IMPROVEMENT",
            "UNSATISFACTORY",
        ]

        if not status:
            raise forms.ValidationError("Please select the review status.")

        if status not in allowed_statuses:
            raise forms.ValidationError("Invalid annual progress status.")

        return status

    def clean_committee_comments(
        self,
    ):

        comments = self.cleaned_data.get(
            "committee_comments",
        )

        if not comments:
            raise forms.ValidationError("Committee comments are required.")

        comments = comments.strip()

        if not comments:
            raise forms.ValidationError("Committee comments cannot be empty.")

        if len(comments) < 20:
            raise forms.ValidationError(
                "Committee comments must contain at least 20 characters."
            )

        if len(comments) > 5000:
            raise forms.ValidationError(
                "Committee comments cannot exceed 5000 characters."
            )

        return comments

    def clean(
        self,
    ):

        cleaned_data = super().clean()

        phd_student = cleaned_data.get(
            "phd_student",
        )

        review_year = cleaned_data.get(
            "review_year",
        )

        if not phd_student or not review_year:
            return cleaned_data

        existing_review = AnnualProgressReview.objects.filter(
            phd_student=phd_student,
            review_year=review_year,
        )

        if self.instance.pk:
            existing_review = existing_review.exclude(
                pk=self.instance.pk,
            )

        if existing_review.exists():
            self.add_error(
                "review_year",
                "An annual progress review already exists for this student and review year.",
            )

        return cleaned_data


class ResearchMilestoneForm(forms.ModelForm):
    class Meta:
        model = ResearchMilestone
        fields = [
            "phd_student",
            "milestone_title",
            "description",
            "expected_completion_date",
        ]
        widgets = {
            "phd_student": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "milestone_title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter research milestone title",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Enter milestone description",
                }
            ),
            "expected_completion_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "id": "id_expected_completion_date",
                    "autocomplete": "off",
                    "readonly": True,
                    "placeholder": "Select expected completion date",
                    "type": "date",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.faculty = kwargs.pop(
            "faculty",
            None,
        )

        super().__init__(
            *args,
            **kwargs,
        )

        if self.faculty is None:
            raise ValueError("ResearchMilestoneForm requires a faculty instance.")

        self.fields["phd_student"].queryset = (
            PhDStudent.objects.filter(
                doctoral_committee__chair_faculty=self.faculty,
                current_status="ACTIVE",
            )
            .select_related(
                "student",
                "student__user",
                "advisor",
                "phd_program",
                "doctoral_committee",
            )
            .order_by(
                "student__user__first_name",
                "student__user__last_name",
            )
        )

        self.fields["phd_student"].empty_label = "Select PhD Student"

        if self.instance.pk:
            self.fields["phd_student"].disabled = True

    def clean_phd_student(self):
        phd_student = self.cleaned_data.get(
            "phd_student",
        )

        if not phd_student:
            raise forms.ValidationError("Please select a PhD student.")

        if phd_student.current_status != "ACTIVE":
            raise forms.ValidationError("Only active PhD students can be selected.")

        try:
            committee = phd_student.doctoral_committee
        except DoctoralCommittee.DoesNotExist:
            raise forms.ValidationError(
                "Doctoral committee has not been created for this student."
            )

        if committee.chair_faculty != self.faculty:
            raise forms.ValidationError(
                "You are not the Chair Faculty for this student."
            )

        if not self.instance.pk:
            active_milestone = (
                ResearchMilestone.objects.filter(
                    phd_student=phd_student,
                    status="IN_PROGRESS",
                )
                .order_by(
                    "-sequence_number",
                    "-milestone_id",
                )
                .first()
            )

            if active_milestone:
                raise forms.ValidationError(
                    (
                        "This student already has an active research "
                        "milestone. The current milestone must be "
                        "completed before creating another one."
                    )
                )

            research_completed = ResearchMilestone.objects.filter(
                phd_student=phd_student,
                current_progress_percentage__gte=100,
            ).exists()

            if research_completed:
                raise forms.ValidationError(
                    (
                        "This student's research has already reached "
                        "100% completion. No additional research "
                        "milestones can be created."
                    )
                )

        return phd_student

    def clean_milestone_title(self):
        milestone_title = self.cleaned_data.get(
            "milestone_title",
        )

        if not milestone_title or not milestone_title.strip():
            raise forms.ValidationError("Please enter the research milestone title.")

        milestone_title = milestone_title.strip()

        if len(milestone_title) < 3:
            raise forms.ValidationError(
                "Milestone title must contain at least 3 characters."
            )

        if len(milestone_title) > 255:
            raise forms.ValidationError("Milestone title cannot exceed 255 characters.")

        return milestone_title

    def clean_description(self):
        description = self.cleaned_data.get(
            "description",
        )

        if description:
            description = description.strip()

        return description

    def clean_expected_completion_date(self):
        expected_completion_date = self.cleaned_data.get(
            "expected_completion_date",
        )

        if not expected_completion_date:
            raise forms.ValidationError("Please select the expected completion date.")

        if expected_completion_date < timezone.now().date():
            raise forms.ValidationError(
                "Expected completion date cannot be earlier than today."
            )

        return expected_completion_date

    def clean(self):
        cleaned_data = super().clean()

        if self.errors:
            return cleaned_data

        phd_student = cleaned_data.get(
            "phd_student",
        )

        if not phd_student:
            return cleaned_data

        if self.instance.pk:
            return cleaned_data

        active_milestone_exists = ResearchMilestone.objects.filter(
            phd_student=phd_student,
            status__in=[
                "PENDING",
                "IN_PROGRESS",
            ],
        ).exists()

        if active_milestone_exists:
            self.add_error(
                "phd_student",
                (
                    "This student already has an active research "
                    "milestone. Complete the current milestone "
                    "before creating a new one."
                ),
            )

            return cleaned_data

        research_completed = ResearchMilestone.objects.filter(
            phd_student=phd_student,
            current_progress_percentage__gte=100,
        ).exists()

        if research_completed:
            self.add_error(
                "phd_student",
                (
                    "This student's research has already reached "
                    "100% completion. No additional research "
                    "milestones can be created."
                ),
            )

        return cleaned_data

    def save(self, commit=True):
        milestone = super().save(
            commit=False,
        )

        milestone.chair_faculty = self.faculty

        if not milestone.pk:
            last_sequence = (
                ResearchMilestone.objects.filter(
                    phd_student=milestone.phd_student,
                )
                .aggregate(
                    max_sequence=models.Max(
                        "sequence_number",
                    ),
                )
                .get(
                    "max_sequence",
                )
            )

            milestone.sequence_number = (last_sequence or 0) + 1

        if commit:
            milestone.save()

        return milestone


class ResearchMilestoneForm(forms.ModelForm):
    class Meta:
        model = ResearchMilestone
        fields = [
            "phd_student",
            "milestone_title",
            "description",
            "expected_completion_date",
        ]
        widgets = {
            "phd_student": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "milestone_title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter research milestone title",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Enter milestone description",
                }
            ),
            "expected_completion_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "id": "id_expected_completion_date",
                    "autocomplete": "off",
                    "readonly": True,
                    "placeholder": "Select expected completion date",
                    "type": "date",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.faculty = kwargs.pop(
            "faculty",
            None,
        )

        super().__init__(
            *args,
            **kwargs,
        )

        if self.faculty is None:
            raise ValueError("ResearchMilestoneForm requires a faculty instance.")

        self.fields["phd_student"].queryset = (
            PhDStudent.objects.filter(
                doctoral_committee__chair_faculty=self.faculty,
                current_status="ACTIVE",
            )
            .select_related(
                "student",
                "student__user",
                "advisor",
                "phd_program",
                "doctoral_committee",
            )
            .order_by(
                "student__user__first_name",
                "student__user__last_name",
            )
        )

        self.fields["phd_student"].empty_label = "Select PhD Student"

        if self.instance.pk:
            self.fields["phd_student"].disabled = True

    def clean_phd_student(self):
        phd_student = self.cleaned_data.get(
            "phd_student",
        )

        if not phd_student:
            raise forms.ValidationError("Please select a PhD student.")

        if phd_student.current_status != "ACTIVE":
            raise forms.ValidationError("Only active PhD students can be selected.")

        try:
            committee = phd_student.doctoral_committee
        except DoctoralCommittee.DoesNotExist:
            raise forms.ValidationError(
                "Doctoral committee has not been created for this student."
            )

        if committee.chair_faculty != self.faculty:
            raise forms.ValidationError(
                "You are not the Chair Faculty for this student."
            )

        if not self.instance.pk:
            active_milestone = (
                ResearchMilestone.objects.filter(
                    phd_student=phd_student,
                    status="IN_PROGRESS",
                )
                .order_by(
                    "-sequence_number",
                    "-milestone_id",
                )
                .first()
            )

            if active_milestone:
                raise forms.ValidationError(
                    (
                        "This student already has an active research "
                        "milestone. The current milestone must be "
                        "completed before creating another one."
                    )
                )

            research_completed = ResearchMilestone.objects.filter(
                phd_student=phd_student,
                current_progress_percentage__gte=100,
            ).exists()

            if research_completed:
                raise forms.ValidationError(
                    (
                        "This student's research has already reached "
                        "100% completion. No additional research "
                        "milestones can be created."
                    )
                )

        return phd_student

    def clean_milestone_title(self):
        milestone_title = self.cleaned_data.get(
            "milestone_title",
        )

        if not milestone_title or not milestone_title.strip():
            raise forms.ValidationError("Please enter the research milestone title.")

        milestone_title = milestone_title.strip()

        if len(milestone_title) < 3:
            raise forms.ValidationError(
                "Milestone title must contain at least 3 characters."
            )

        if len(milestone_title) > 255:
            raise forms.ValidationError("Milestone title cannot exceed 255 characters.")

        return milestone_title

    def clean_description(self):
        description = self.cleaned_data.get(
            "description",
        )

        if description:
            description = description.strip()

        return description

    def clean_expected_completion_date(self):
        expected_completion_date = self.cleaned_data.get(
            "expected_completion_date",
        )

        if not expected_completion_date:
            raise forms.ValidationError("Please select the expected completion date.")

        if expected_completion_date < timezone.now().date():
            raise forms.ValidationError(
                "Expected completion date cannot be earlier than today."
            )

        return expected_completion_date

    def clean(self):
        cleaned_data = super().clean()

        if self.errors:
            return cleaned_data

        phd_student = cleaned_data.get(
            "phd_student",
        )

        if not phd_student:
            return cleaned_data

        if self.instance.pk:
            return cleaned_data

        active_milestone_exists = ResearchMilestone.objects.filter(
            phd_student=phd_student,
            status__in=[
                "PENDING",
                "IN_PROGRESS",
            ],
        ).exists()

        if active_milestone_exists:
            self.add_error(
                "phd_student",
                (
                    "This student already has an active research "
                    "milestone. Complete the current milestone "
                    "before creating a new one."
                ),
            )

            return cleaned_data

        research_completed = ResearchMilestone.objects.filter(
            phd_student=phd_student,
            current_progress_percentage__gte=100,
        ).exists()

        if research_completed:
            self.add_error(
                "phd_student",
                (
                    "This student's research has already reached "
                    "100% completion. No additional research "
                    "milestones can be created."
                ),
            )

        return cleaned_data

    def save(self, commit=True):
        milestone = super().save(
            commit=False,
        )

        milestone.chair_faculty = self.faculty

        if not milestone.pk:
            last_sequence = (
                ResearchMilestone.objects.filter(
                    phd_student=milestone.phd_student,
                )
                .aggregate(
                    max_sequence=models.Max(
                        "sequence_number",
                    ),
                )
                .get(
                    "max_sequence",
                )
            )

            milestone.sequence_number = (last_sequence or 0) + 1

            previous_progress = ResearchMilestone.objects.filter(
                phd_student=milestone.phd_student,
                sequence_number__lt=milestone.sequence_number,
            ).aggregate(
                total=models.Max(
                    "current_progress_percentage",
                ),
            ).get(
                "total",
            ) or Decimal(
                "0"
            )

            milestone.current_progress_percentage = max(
                min(
                    Decimal(str(previous_progress)),
                    Decimal("100"),
                ),
                Decimal("0"),
            )

        if commit:
            milestone.save()

        return milestone


class ResearchMilestoneEvaluationForm(forms.ModelForm):

    progress_percentage = forms.DecimalField(
        required=False,
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0.00"),
        max_value=Decimal("100.00"),
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": "1.00",
                "max": "100.00",
                "step": "0.01",
                "placeholder": "How much progress do you want to add?",
                "autocomplete": "off",
                "inputmode": "decimal",
            }
        ),
        label="Additional Research Progress",
    )

    class Meta:
        model = ResearchMilestoneEvaluation
        fields = [
            "progress_percentage",
            "feedback",
            "decision",
        ]
        widgets = {
            "feedback": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "maxlength": 5000,
                    "placeholder": "Enter your research evaluation feedback",
                }
            ),
            "decision": forms.Select(
                attrs={
                    "class": "form-select choices",
                }
            ),
        }

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        self.faculty = kwargs.pop(
            "faculty",
            None,
        )

        self.submission = kwargs.pop(
            "submission",
            None,
        )

        self.is_finalization = kwargs.pop(
            "is_finalization",
            False,
        )

        self.previous_progress = kwargs.pop(
            "previous_progress",
            Decimal("0.00"),
        )

        self.max_progress = kwargs.pop(
            "max_progress",
            Decimal("100.00"),
        )

        super().__init__(
            *args,
            **kwargs,
        )

        try:
            self.previous_progress = Decimal(
                str(
                    self.previous_progress
                    if self.previous_progress is not None
                    else "0.00"
                )
            )
        except (
            TypeError,
            ValueError,
            InvalidOperation,
        ):
            self.previous_progress = Decimal("0.00")

        self.previous_progress = max(
            self.previous_progress,
            Decimal("0.00"),
        )

        self.previous_progress = min(
            self.previous_progress,
            Decimal("100.00"),
        )

        try:
            requested_max_progress = Decimal(
                str(self.max_progress if self.max_progress is not None else "100.00")
            )
        except (
            TypeError,
            ValueError,
            InvalidOperation,
        ):
            requested_max_progress = Decimal("100.00")

        remaining_progress = max(
            Decimal("100.00") - self.previous_progress,
            Decimal("0.00"),
        )

        self.max_progress = min(
            max(requested_max_progress, Decimal("0.00")),
            remaining_progress,
        )

        if self.faculty is None:
            raise ValueError(
                "ResearchMilestoneEvaluationForm requires a faculty instance."
            )

        if self.submission is None:
            raise ValueError(
                "ResearchMilestoneEvaluationForm requires a submission instance."
            )

        self.fields["progress_percentage"].label = "Additional Research Progress"
        self.fields["feedback"].label = "Evaluation Feedback"
        self.fields["decision"].label = (
            "Final Decision" if self.is_finalization else "Evaluation Decision"
        )

        self.fields["progress_percentage"].widget.attrs.update(
            {
                "min": "1.00",
                "max": f"{self.max_progress:.2f}",
                "step": "0.01",
                "placeholder": "How much progress do you want to add?",
            }
        )

        self.fields["progress_percentage"].help_text = (
            f"Current overall research progress: {self.previous_progress:.2f}%. "
            f"Maximum you can add: {self.max_progress:.2f}%. "
            "Minimum: 1.00%. Enter how much progress you want to add."
        )

    def clean_progress_percentage(
        self,
    ):
        progress_percentage = self.cleaned_data.get("progress_percentage")
        decision = self.data.get("decision")

        if progress_percentage in [None, ""]:
            if decision == "REVISION_REQUIRED":
                return None

            raise forms.ValidationError(
                "Please enter how much research progress you want to add."
            )

        try:
            progress_percentage = Decimal(str(progress_percentage))
        except (
            TypeError,
            ValueError,
            InvalidOperation,
        ):
            raise forms.ValidationError("Please enter a valid progress percentage.")

        normalized_progress = progress_percentage.normalize()

        if normalized_progress.as_tuple().exponent < -2:
            raise forms.ValidationError(
                "Progress percentage can contain a maximum of 2 decimal places."
            )

        progress_percentage = progress_percentage.quantize(Decimal("0.01"))

        if progress_percentage < Decimal("1.00"):
            raise forms.ValidationError("You must add at least 1.00% progress.")

        if progress_percentage > self.max_progress:
            raise forms.ValidationError(
                f"You can add a maximum of {self.max_progress:.2f}% progress."
            )

        projected_progress = self.previous_progress + progress_percentage

        if projected_progress > Decimal("100.00"):
            raise forms.ValidationError(
                "The overall research progress cannot exceed 100.00%."
            )

        return progress_percentage

    def clean_feedback(
        self,
    ):
        feedback = self.cleaned_data.get("feedback")

        if not feedback or not feedback.strip():
            raise forms.ValidationError("Evaluation feedback is required.")

        feedback = feedback.strip()

        if len(feedback) < 10:
            raise forms.ValidationError(
                "Evaluation feedback must contain at least 10 characters."
            )

        if len(feedback) > 5000:
            raise forms.ValidationError(
                "Evaluation feedback cannot exceed 5000 characters."
            )

        return feedback

    def clean_decision(
        self,
    ):
        decision = self.cleaned_data.get("decision")

        if not decision:
            raise forms.ValidationError("Please select an evaluation decision.")

        if decision not in [
            "REVISION_REQUIRED",
            "COMPLETED",
        ]:
            raise forms.ValidationError("Invalid evaluation decision.")

        return decision

    def clean(
        self,
    ):
        cleaned_data = super().clean()

        if self.submission is None:
            return cleaned_data

        milestone = self.submission.milestone

        decision = cleaned_data.get("decision")
        progress_percentage = cleaned_data.get("progress_percentage")

        try:
            committee = milestone.phd_student.doctoral_committee
        except DoctoralCommittee.DoesNotExist:
            raise forms.ValidationError(
                "Doctoral committee has not been created for this student."
            )

        is_chair = committee.chair_faculty_id == self.faculty.pk

        is_committee_member = CommitteeMember.objects.filter(
            committee=committee,
            faculty=self.faculty,
        ).exists()

        if not is_chair and not is_committee_member:
            raise forms.ValidationError(
                "You are not authorized to evaluate this research submission."
            )

        if self.is_finalization:
            if not is_chair:
                raise forms.ValidationError(
                    "Only the Chair Faculty can finalize the research milestone."
                )

            committee_member_ids = list(
                CommitteeMember.objects.filter(
                    committee=committee,
                ).values_list(
                    "faculty_id",
                    flat=True,
                )
            )

            required_count = len(set(committee_member_ids))

            if required_count == 0:
                raise forms.ValidationError(
                    "No committee members are assigned to this doctoral committee."
                )

            submitted_committee_evaluations = (
                ResearchMilestoneEvaluation.objects.filter(
                    submission=self.submission,
                    evaluator_id__in=committee_member_ids,
                    evaluator_role="COMMITTEE_MEMBER",
                )
                .values_list(
                    "evaluator_id",
                    flat=True,
                )
                .distinct()
            )

            submitted_count = len(set(submitted_committee_evaluations))

            if submitted_count < required_count:
                pending_count = required_count - submitted_count

                raise forms.ValidationError(
                    (
                        "Chair Faculty can finalize the research milestone only "
                        "after all committee members submit their evaluations. "
                        f"{pending_count} evaluation(s) are still pending."
                    )
                )

            existing_chair_evaluation = ResearchMilestoneEvaluation.objects.filter(
                submission=self.submission,
                evaluator=self.faculty,
                evaluator_role="CHAIR",
            ).first()

            if existing_chair_evaluation:
                raise forms.ValidationError(
                    "The Chair Faculty has already finalized this research submission."
                )

        else:
            if not is_committee_member:
                raise forms.ValidationError(
                    "Only Committee Members can submit the research milestone evaluation."
                )

            existing_evaluation = ResearchMilestoneEvaluation.objects.filter(
                submission=self.submission,
                evaluator=self.faculty,
                evaluator_role="COMMITTEE_MEMBER",
            ).exists()

            if existing_evaluation:
                raise forms.ValidationError(
                    "You have already submitted an evaluation for this research submission."
                )

        if self.submission.status not in [
            "SUBMITTED",
            "UNDER_REVIEW",
        ]:
            raise forms.ValidationError(
                "This research submission is not available for evaluation."
            )

        if milestone.status == "COMPLETED":
            raise forms.ValidationError(
                "This research milestone has already been completed."
            )

        if decision == "REVISION_REQUIRED":
            cleaned_data["progress_percentage"] = None

        if decision == "COMPLETED" and progress_percentage is None:
            self.add_error(
                "progress_percentage",
                "Please enter how much research progress you want to add.",
            )

        return cleaned_data

    def save(
        self,
        commit=True,
    ):
        evaluation = super().save(commit=False)

        evaluation.submission = self.submission
        evaluation.evaluator = self.faculty
        evaluation.evaluator_role = (
            "CHAIR" if self.is_finalization else "COMMITTEE_MEMBER"
        )
        evaluation.evaluated_at = timezone.now()

        entered_progress = evaluation.progress_percentage

        if entered_progress is not None:
            evaluation.progress_percentage = min(
                self.previous_progress + entered_progress,
                Decimal("100.00"),
            )

        if commit:
            evaluation.save()
            self._update_related_objects(evaluation)

        return evaluation

    def _update_related_objects(
        self,
        evaluation,
    ):
        submission = evaluation.submission
        milestone = submission.milestone

        if evaluation.evaluator_role == "COMMITTEE_MEMBER":
            return

        if evaluation.evaluator_role == "CHAIR":
            if evaluation.decision == "REVISION_REQUIRED":
                submission.status = "REVISION_REQUIRED"

                submission.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

                return

            if evaluation.progress_percentage is not None:
                milestone.current_progress_percentage = evaluation.progress_percentage

            if evaluation.decision == "COMPLETED":
                submission.status = "EVALUATED"

            milestone.save(
                update_fields=[
                    "current_progress_percentage",
                    "updated_at",
                ]
            )

            submission.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )


class AdvisorResearchAdviceForm(forms.ModelForm):

    class Meta:
        model = AdvisorResearchAdvice
        fields = [
            "advice",
        ]

        widgets = {
            "advice": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 7,
                    "minlength": 20,
                    "maxlength": 5000,
                    "placeholder": "Provide guidance and advice based on the research evaluation...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.faculty = kwargs.pop(
            "faculty",
            None,
        )

        self.submission = kwargs.pop(
            "submission",
            None,
        )

        super().__init__(
            *args,
            **kwargs,
        )

        if self.faculty is None:
            raise ValueError("AdvisorResearchAdviceForm requires a faculty instance.")

        if self.submission is None:
            raise ValueError(
                "AdvisorResearchAdviceForm requires a submission instance."
            )

        self.fields["advice"].label = "Research Advice"
        self.fields["advice"].required = True

    def clean_advice(self):
        advice = self.cleaned_data.get(
            "advice",
        )

        if not advice or not advice.strip():
            raise forms.ValidationError("Research advice is required.")

        advice = advice.strip()

        if len(advice) < 20:
            raise forms.ValidationError(
                "Research advice must contain at least 20 characters."
            )

        if len(advice) > 5000:
            raise forms.ValidationError(
                "Research advice cannot exceed 5000 characters."
            )

        return advice

    def clean(self):
        cleaned_data = super().clean()

        if self.submission is None:
            return cleaned_data

        milestone = self.submission.milestone
        phd_student = milestone.phd_student

        if phd_student.advisor != self.faculty:
            raise forms.ValidationError(
                "You are not authorized to provide advice for this student."
            )

        if milestone.status == "COMPLETED":
            raise forms.ValidationError(
                "Advice cannot be provided for a completed research milestone."
            )

        evaluation_exists = ResearchMilestoneEvaluation.objects.filter(
            submission=self.submission,
        ).exists()

        if not evaluation_exists:
            raise forms.ValidationError(
                "Research evaluation must be completed before providing advisor advice."
            )

        existing_advice = AdvisorResearchAdvice.objects.filter(
            submission=self.submission,
            advisor=self.faculty,
        )

        if self.instance.pk:
            existing_advice = existing_advice.exclude(
                pk=self.instance.pk,
            )

        if existing_advice.exists():
            raise forms.ValidationError(
                "You have already provided advice for this research submission."
            )

        if self.instance.pk and self.instance.is_submitted:
            raise forms.ValidationError("Submitted advisor advice cannot be modified.")

        return cleaned_data

    def save(self, commit=True):
        advice = super().save(
            commit=False,
        )

        advice.submission = self.submission
        advice.advisor = self.faculty
        advice.status = "SUBMITTED"
        advice.is_submitted = True
        advice.submitted_at = timezone.now()

        if commit:
            advice.save()

        return advice


class FinalDissertationAdvisorEvaluationForm(forms.ModelForm):

    class Meta:
        model = FinalDissertationAdvisorEvaluation

        fields = [
            "recommendation",
            "comments",
        ]

        widgets = {
            "recommendation": forms.Select(
                attrs={
                    "class": "fde-recommendation-select",
                }
            ),
            "comments": forms.Textarea(
                attrs={
                    "class": "fde-comments-input",
                    "rows": 7,
                    "minlength": 20,
                    "maxlength": 5000,
                    "placeholder": (
                        "Provide your academic remarks on the final dissertation..."
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        self.faculty = kwargs.pop(
            "faculty",
            None,
        )

        self.submission = kwargs.pop(
            "submission",
            None,
        )

        super().__init__(
            *args,
            **kwargs,
        )

        if self.faculty is None:
            raise ValueError(
                "FinalDissertationAdvisorEvaluationForm requires a faculty instance."
            )

        if self.submission is None:
            raise ValueError(
                "FinalDissertationAdvisorEvaluationForm requires a submission instance."
            )

        self.fields["recommendation"].label = "Recommendation"
        self.fields["recommendation"].required = True

        self.fields["comments"].label = "Remarks"
        self.fields["comments"].required = True

        self.fields["comments"].help_text = (
            "Include your academic assessment, observations, "
            "required corrections, or other relevant feedback."
        )

    def clean_recommendation(self):

        recommendation = self.cleaned_data.get("recommendation")

        valid_recommendations = {
            "APPROVE",
            "REVISION_REQUIRED",
            "REJECT",
        }

        if not recommendation:
            raise forms.ValidationError("Please select a recommendation.")

        if recommendation not in valid_recommendations:
            raise forms.ValidationError("Invalid advisor recommendation.")

        return recommendation

    def clean_comments(self):

        comments = self.cleaned_data.get("comments")

        if not comments or not comments.strip():
            raise forms.ValidationError("Please provide your academic remarks.")

        comments = comments.strip()

        if len(comments) < 20:
            raise forms.ValidationError("Remarks must contain at least 20 characters.")

        if len(comments) > 5000:
            raise forms.ValidationError("Remarks cannot exceed 5000 characters.")

        return comments

    def clean(self):

        cleaned_data = super().clean()

        submission = self.submission
        faculty = self.faculty

        if submission is None or faculty is None:
            return cleaned_data

        if submission.phd_student.advisor_id != faculty.pk:
            raise forms.ValidationError(
                "You are not authorized to review this dissertation."
            )

        if submission.status != "ADVISOR_REVIEW":
            if not self.instance.pk:
                raise forms.ValidationError(
                    "This dissertation is not currently available for advisor review."
                )

        if (
            self.instance.pk
            and self.instance.is_submitted
            and not self.instance.is_full_crud
        ):
            raise forms.ValidationError(
                "This advisor evaluation has already been submitted "
                "and cannot be modified."
            )

        existing_evaluation = FinalDissertationAdvisorEvaluation.objects.filter(
            submission=submission,
            advisor=faculty,
            submission_number=submission.submission_number,
        )

        if self.instance.pk:
            existing_evaluation = existing_evaluation.exclude(pk=self.instance.pk)

        if existing_evaluation.exists():
            raise forms.ValidationError(
                "You have already created an evaluation "
                "for this dissertation submission."
            )

        if self.instance.pk:
            if self.instance.submission_number != submission.submission_number:
                raise forms.ValidationError(
                    "This evaluation does not belong to "
                    "the current dissertation submission version."
                )

        return cleaned_data

    def save(self, commit=True):

        evaluation = super().save(commit=False)

        evaluation.submission = self.submission
        evaluation.advisor = self.faculty

        evaluation.submission_number = self.submission.submission_number

        evaluation.resubmission_count = self.submission.resubmission_count

        evaluation.is_submitted = True
        evaluation.submitted_at = timezone.now()

        if commit:
            evaluation.save()

        return evaluation


class FinalDissertationCommitteeEvaluationForm(forms.ModelForm):
    class Meta:
        model = FinalDissertationCommitteeEvaluation
        fields = [
            "score",
            "recommendation",
        ]

        widgets = {
            "score": forms.NumberInput(
                attrs={
                    "class": "fde-score-input",
                    "min": 0,
                    "max": 100,
                    "step": "0.01",
                    "placeholder": "Enter evaluation score",
                }
            ),
            "recommendation": forms.Select(
                attrs={
                    "class": "fde-recommendation-select",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.faculty = kwargs.pop(
            "faculty",
            None,
        )

        self.submission = kwargs.pop(
            "submission",
            None,
        )

        super().__init__(
            *args,
            **kwargs,
        )

        if self.faculty is None:
            raise ValueError(
                "FinalDissertationCommitteeEvaluationForm requires a faculty instance."
            )

        if self.submission is None:
            raise ValueError(
                "FinalDissertationCommitteeEvaluationForm requires a submission instance."
            )

        self.fields["score"].label = "Evaluation Score"
        self.fields["score"].required = True

        self.fields["recommendation"].label = "Recommendation"
        self.fields["recommendation"].required = True

    def clean_score(self):
        score = self.cleaned_data.get("score")

        if score is None:
            raise forms.ValidationError("Please enter the evaluation score.")

        if score < 0 or score > 100:
            raise forms.ValidationError("Evaluation score must be between 0 and 100.")

        return score

    def clean_recommendation(self):
        recommendation = self.cleaned_data.get("recommendation")

        valid_recommendations = {
            "APPROVE",
            "REVISION_REQUIRED",
            "REJECT",
        }

        if not recommendation:
            raise forms.ValidationError("Please select a recommendation.")

        if recommendation not in valid_recommendations:
            raise forms.ValidationError("Invalid committee recommendation.")

        return recommendation

    def clean(self):
        cleaned_data = super().clean()

        submission = self.submission
        faculty = self.faculty

        if submission is None or faculty is None:
            return cleaned_data

        if submission.status != "COMMITTEE_EVALUATION":
            if not self.instance.pk:
                raise forms.ValidationError(
                    "This dissertation is not currently available for committee evaluation."
                )

        try:
            committee = submission.phd_student.doctoral_committee
        except DoctoralCommittee.DoesNotExist:
            raise forms.ValidationError(
                "Doctoral committee has not been created for this student."
            )

        committee_member = CommitteeMember.objects.filter(
            committee=committee,
            faculty=faculty,
        ).first()

        if not committee_member:
            raise forms.ValidationError(
                "You are not authorized to evaluate this dissertation."
            )

        if committee_member.role == "CHAIR":
            raise forms.ValidationError(
                "The Chair cannot submit a committee member evaluation."
            )

        if committee_member.role not in [
            "CO_CHAIR",
            "INTERNAL_MEMBER",
            "EXTERNAL_MEMBER",
        ]:
            raise forms.ValidationError("You are not an eligible committee evaluator.")

        if (
            self.instance.pk
            and self.instance.is_submitted
            and not self.instance.is_full_crud
        ):
            raise forms.ValidationError(
                "This committee evaluation has already been submitted and cannot be modified."
            )

        if self.instance.pk:
            if self.instance.submission_id != submission.submission_id:
                raise forms.ValidationError(
                    "This evaluation does not belong to the selected dissertation submission."
                )

            if self.instance.submission_number != submission.submission_number:
                raise forms.ValidationError(
                    "This evaluation does not belong to the current dissertation submission version."
                )

            if self.instance.committee_member_id != committee_member.pk:
                raise forms.ValidationError(
                    "This evaluation does not belong to your committee membership."
                )

            if self.instance.reviewer_role != "COMMITTEE_MEMBER":
                raise forms.ValidationError(
                    "This evaluation is not a committee member evaluation."
                )

        existing_evaluation = FinalDissertationCommitteeEvaluation.objects.filter(
            submission=submission,
            committee_member=committee_member,
            submission_number=submission.submission_number,
        )

        if self.instance.pk:
            existing_evaluation = existing_evaluation.exclude(pk=self.instance.pk)

        if existing_evaluation.exists():
            raise forms.ValidationError(
                "You have already submitted an evaluation for this dissertation submission."
            )

        advisor_evaluation_exists = FinalDissertationAdvisorEvaluation.objects.filter(
            submission=submission,
            submission_number=submission.submission_number,
            advisor=submission.phd_student.advisor,
            is_submitted=True,
            recommendation="APPROVE",
        ).exists()

        if not advisor_evaluation_exists:
            raise forms.ValidationError(
                "Advisor approval is required before committee evaluation."
            )

        return cleaned_data

    def save(self, commit=True):
        evaluation = super().save(commit=False)

        committee = self.submission.phd_student.doctoral_committee

        committee_member = CommitteeMember.objects.get(
            committee=committee,
            faculty=self.faculty,
        )

        evaluation.submission = self.submission
        evaluation.committee_member = committee_member
        evaluation.reviewer_role = "COMMITTEE_MEMBER"
        evaluation.submission_number = self.submission.submission_number
        evaluation.resubmission_count = self.submission.resubmission_count
        evaluation.is_final_decision = False
        evaluation.is_submitted = True
        evaluation.submitted_at = timezone.now()

        if commit:
            evaluation.save()

        return evaluation


class FinalDissertationChairFinalizationForm(forms.ModelForm):
    recommendation = forms.ChoiceField(
        choices=[
            ("", "Select final decision"),
            ("APPROVE", "Approve"),
            ("REVISION_REQUIRED", "Revision Required"),
            ("REJECT", "Reject"),
        ],
        widget=forms.Select(
            attrs={
                "class": "fcd-choice-select",
                "id": "recommendation",
            }
        ),
        required=True,
    )

    class Meta:
        model = FinalDissertationCommitteeEvaluation
        fields = [
            "score",
            "recommendation",
        ]

        widgets = {
            "score": forms.NumberInput(
                attrs={
                    "class": "fcd-input fcd-score-input",
                    "id": "score",
                    "min": "0",
                    "max": "100",
                    "step": "0.01",
                    "inputmode": "decimal",
                    "placeholder": "Enter final score",
                    "autocomplete": "off",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.faculty = kwargs.pop(
            "faculty",
            None,
        )

        self.submission = kwargs.pop(
            "submission",
            None,
        )

        super().__init__(
            *args,
            **kwargs,
        )

        if self.faculty is None:
            raise ValueError(
                "FinalDissertationChairFinalizationForm requires a faculty instance."
            )

        if self.submission is None:
            raise ValueError(
                "FinalDissertationChairFinalizationForm requires a submission instance."
            )

        self.fields["score"].label = "Final Score"
        self.fields["score"].required = True

        self.fields["recommendation"].label = "Final Decision"
        self.fields["recommendation"].required = True

        self.fields["recommendation"].choices = [
            ("", "Select final decision"),
            ("APPROVE", "Approve"),
            ("REVISION_REQUIRED", "Revision Required"),
            ("REJECT", "Reject"),
        ]

    def clean_score(self):
        score = self.cleaned_data.get("score")

        if score is None:
            raise forms.ValidationError("Please enter the final score.")

        if score < 0 or score > 100:
            raise forms.ValidationError("Final score must be between 0 and 100.")

        return score

    def clean_recommendation(self):
        recommendation = self.cleaned_data.get("recommendation")

        valid_recommendations = {
            "APPROVE",
            "REVISION_REQUIRED",
            "REJECT",
        }

        if not recommendation:
            raise forms.ValidationError("Please select the final decision.")

        if recommendation not in valid_recommendations:
            raise forms.ValidationError("Invalid final decision.")

        return recommendation

    def clean(self):
        cleaned_data = super().clean()

        submission = self.submission
        faculty = self.faculty

        if submission is None or faculty is None:
            return cleaned_data

        if submission.status != "CHAIR_REVIEW":
            raise forms.ValidationError(
                "This dissertation is not currently available for Chair final review."
            )

        try:
            committee = submission.phd_student.doctoral_committee
        except DoctoralCommittee.DoesNotExist:
            raise forms.ValidationError(
                "Doctoral committee has not been created for this student."
            )

        if committee.chair_faculty_id != faculty.pk:
            raise forms.ValidationError(
                "Only the Chair Faculty can finalize this dissertation."
            )

        if (
            self.instance.pk
            and self.instance.is_submitted
            and not self.instance.is_full_crud
        ):
            raise forms.ValidationError(
                "The Chair final decision has already been submitted and cannot be modified."
            )

        if self.instance.pk:
            if self.instance.submission_id != submission.submission_id:
                raise forms.ValidationError(
                    "This final decision does not belong to the selected dissertation submission."
                )

            if self.instance.submission_number != submission.submission_number:
                raise forms.ValidationError(
                    "This final decision does not belong to the current dissertation submission version."
                )

            if self.instance.reviewer_role != "CHAIR":
                raise forms.ValidationError(
                    "This evaluation is not a Chair final decision."
                )

            if not self.instance.is_final_decision:
                raise forms.ValidationError(
                    "This evaluation is not marked as a final Chair decision."
                )

        advisor_approval_exists = FinalDissertationAdvisorEvaluation.objects.filter(
            submission=submission,
            submission_number=submission.submission_number,
            advisor=submission.phd_student.advisor,
            is_submitted=True,
            recommendation="APPROVE",
        ).exists()

        if not advisor_approval_exists:
            raise forms.ValidationError(
                "Advisor approval is required before Chair finalization."
            )

        required_members = CommitteeMember.objects.filter(
            committee=committee,
            role__in=[
                "CO_CHAIR",
                "INTERNAL_MEMBER",
                "EXTERNAL_MEMBER",
            ],
        )

        required_member_ids = list(
            required_members.values_list(
                "pk",
                flat=True,
            )
        )

        if not required_member_ids:
            raise forms.ValidationError(
                "At least one committee evaluator is required before Chair finalization."
            )

        submitted_member_ids = set(
            FinalDissertationCommitteeEvaluation.objects.filter(
                submission=submission,
                submission_number=submission.submission_number,
                committee_member_id__in=required_member_ids,
                reviewer_role="COMMITTEE_MEMBER",
                is_submitted=True,
            ).values_list(
                "committee_member_id",
                flat=True,
            )
        )

        missing_member_ids = set(required_member_ids) - submitted_member_ids

        if missing_member_ids:
            remaining_count = len(missing_member_ids)

            raise forms.ValidationError(
                f"{remaining_count} required committee evaluation"
                f"{'s' if remaining_count != 1 else ''} "
                f"{'are' if remaining_count != 1 else 'is'} still pending."
            )

        existing_chair_decision = FinalDissertationCommitteeEvaluation.objects.filter(
            submission=submission,
            submission_number=submission.submission_number,
            reviewer_role="CHAIR",
            is_final_decision=True,
        )

        if self.instance.pk:
            existing_chair_decision = existing_chair_decision.exclude(
                pk=self.instance.pk
            )

        if existing_chair_decision.exists():
            raise forms.ValidationError(
                "A final Chair decision already exists for this dissertation submission."
            )

        return cleaned_data

    def save(self, commit=True):
        evaluation = super().save(commit=False)

        submission = self.submission
        committee = submission.phd_student.doctoral_committee

        chair_member = CommitteeMember.objects.filter(
            committee=committee,
            role="CHAIR",
            faculty=self.faculty,
        ).first()

        if chair_member is None:
            raise forms.ValidationError(
                "Chair committee member could not be found for this faculty."
            )

        evaluation.submission = submission
        evaluation.committee_member = chair_member
        evaluation.reviewer_role = "CHAIR"
        evaluation.submission_number = submission.submission_number
        evaluation.resubmission_count = submission.resubmission_count or 0
        evaluation.is_final_decision = True
        evaluation.is_submitted = True
        evaluation.submitted_at = timezone.now()

        recommendation = self.cleaned_data["recommendation"]

        if recommendation == "APPROVE":
            submission.status = "APPROVED"
            submission.approved_at = timezone.now()

        elif recommendation == "REVISION_REQUIRED":
            submission.status = "REVISION_REQUIRED"
            submission.approved_at = None

        elif recommendation == "REJECT":
            submission.status = "REJECTED"
            submission.approved_at = None

        submission.finalized_by = self.faculty
        submission.finalized_at = timezone.now()

        if commit:
            with transaction.atomic():
                evaluation.save()

                submission.save(
                    update_fields=[
                        "status",
                        "approved_at",
                        "finalized_by",
                        "finalized_at",
                        "updated_at",
                    ]
                )

        return evaluation


from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from Students.models import (
    CommitteeMember,
    DoctoralCommittee,
    PhDStudent,
)

from Students.Leo_Student.models import (
    DissertationDefense,
    DissertationDefenseEvaluation,
)


class DissertationDefenseScheduleForm(forms.ModelForm):
    class Meta:
        model = DissertationDefense
        fields = [
            "phd_student",
            "defense_date",
            "defense_time",
            "location",
        ]
        widgets = {
            "phd_student": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "defense_date": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                    "placeholder": "Select defense date",
                    "inputmode": "none",
                }
            ),
            "defense_time": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                    "placeholder": "Select defense time",
                    "inputmode": "none",
                }
            ),
            "location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Select defense location",
                    "autocomplete": "off",
                }
            ),
        }

        labels = {
            "phd_student": "PhD Student",
            "defense_date": "Defense Date",
            "defense_time": "Defense Time",
            "location": "Location",
        }

    def __init__(self, *args, **kwargs):
        self.faculty = kwargs.pop("faculty", None)
        super().__init__(*args, **kwargs)

        if self.faculty is None:
            raise ValueError(
                "DissertationDefenseScheduleForm requires a faculty instance."
            )

        self.fields["phd_student"].queryset = (
            PhDStudent.objects.filter(
                doctoral_committee__chair_faculty=self.faculty,
                current_status="ACTIVE",
            )
            .select_related(
                "student",
                "student__user",
                "advisor",
                "phd_program",
                "doctoral_committee",
            )
            .order_by(
                "student__user__first_name",
                "student__user__last_name",
            )
        )

        self.fields["phd_student"].empty_label = "Select PhD Student"

    def clean_phd_student(self):
        phd_student = self.cleaned_data.get("phd_student")

        if not phd_student:
            raise forms.ValidationError("Please select a PhD student.")

        if phd_student.current_status != "ACTIVE":
            raise forms.ValidationError("Only active PhD students can be selected.")

        try:
            committee = phd_student.doctoral_committee
        except DoctoralCommittee.DoesNotExist:
            raise forms.ValidationError(
                "Doctoral committee has not been created for this student."
            )

        if committee.chair_faculty_id != self.faculty.pk:
            raise forms.ValidationError(
                "Only the Chair Faculty can schedule this defense."
            )

        if not committee.committee_members.exists():
            raise forms.ValidationError(
                "At least one committee member is required before scheduling the defense."
            )

        existing_defense = DissertationDefense.objects.filter(
            phd_student=phd_student,
        )

        if self.instance.pk:
            existing_defense = existing_defense.exclude(
                pk=self.instance.pk,
            )

        if existing_defense.exists():
            raise forms.ValidationError(
                "A dissertation defense has already been scheduled for this student."
            )

        return phd_student

    def clean_defense_date(self):
        defense_date = self.cleaned_data.get("defense_date")

        if not defense_date:
            raise forms.ValidationError("Please select the defense date.")

        if defense_date < timezone.localdate():
            raise forms.ValidationError("Defense date cannot be earlier than today.")

        return defense_date

    def clean_defense_time(self):
        defense_time = self.cleaned_data.get("defense_time")

        if not defense_time:
            raise forms.ValidationError("Please select the defense time.")

        return defense_time

    def clean_location(self):
        location = self.cleaned_data.get("location")

        if not location or not location.strip():
            raise forms.ValidationError("Please select a defense location.")

        location = location.strip()

        if len(location) > 255:
            raise forms.ValidationError(
                "Defense location cannot exceed 255 characters."
            )

        return location

    def clean(self):
        cleaned_data = super().clean()

        defense_date = cleaned_data.get("defense_date")
        defense_time = cleaned_data.get("defense_time")
        phd_student = cleaned_data.get("phd_student")

        if defense_date and defense_time:
            defense_datetime = timezone.make_aware(
                datetime.combine(
                    defense_date,
                    defense_time,
                )
            )

            if defense_datetime <= timezone.now():
                self.add_error(
                    "defense_time",
                    "Defense date and time must be in the future.",
                )

        if phd_student and defense_date and defense_time:
            conflicting_defense = DissertationDefense.objects.filter(
                defense_date=defense_date,
                defense_time=defense_time,
            ).exclude(
                phd_student=phd_student,
            )

            if self.instance.pk:
                conflicting_defense = conflicting_defense.exclude(
                    pk=self.instance.pk,
                )

            if conflicting_defense.exists():
                self.add_error(
                    "defense_time",
                    "Another dissertation defense is already scheduled at this date and time.",
                )

        return cleaned_data

    def save(self, commit=True):
        defense = super().save(commit=False)

        defense.result = "PENDING"
        defense.committee_decision = "MINOR_REVISIONS"

        if commit:
            defense.save()

        return defense


class DissertationDefenseEvaluationForm(forms.ModelForm):

    class Meta:

        model = DissertationDefenseEvaluation

        fields = [
            "score",
            "recommendation",
        ]

        widgets = {
            "score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "max": "100",
                    "step": "0.01",
                    "placeholder": "Enter your score",
                    "inputmode": "decimal",
                }
            ),
            "recommendation": forms.Select(
                attrs={
                    "class": "form-select choices",
                }
            ),
        }

        labels = {
            "score": "Defense Evaluation Score",
            "recommendation": "Recommendation",
        }

    def __init__(self, *args, **kwargs):

        self.faculty = kwargs.pop(
            "faculty",
            None,
        )

        self.defense = kwargs.pop(
            "defense",
            None,
        )

        super().__init__(
            *args,
            **kwargs,
        )

        if self.faculty is None:
            raise ValueError(
                "DissertationDefenseEvaluationForm requires a faculty instance."
            )

        if self.defense is None:
            raise ValueError(
                "DissertationDefenseEvaluationForm requires a defense instance."
            )

        self.fields["score"].required = True
        self.fields["recommendation"].required = True

    def clean_score(self):

        score = self.cleaned_data.get(
            "score",
        )

        if score is None:
            raise forms.ValidationError("Please enter the defense evaluation score.")

        if score < 0 or score > 100:
            raise forms.ValidationError(
                "Defense evaluation score must be between 0 and 100."
            )

        return score

    def clean_recommendation(self):

        recommendation = self.cleaned_data.get(
            "recommendation",
        )

        if not recommendation:
            raise forms.ValidationError("Please select a recommendation.")

        valid_recommendations = {
            "PASS",
            "FAIL",
            "MINOR_REVISIONS",
            "MAJOR_REVISIONS",
        }

        if recommendation not in valid_recommendations:
            raise forms.ValidationError("Invalid defense recommendation.")

        return recommendation

    def clean(self):

        cleaned_data = super().clean()

        defense = self.defense
        faculty = self.faculty

        if defense is None or faculty is None:
            return cleaned_data

        if defense.result != "PENDING":
            raise forms.ValidationError(
                "Evaluation is closed for this dissertation defense."
            )

        if defense.defense_date > timezone.localdate():
            raise forms.ValidationError(
                "Defense evaluation can only be submitted after the defense date."
            )

        try:
            committee = defense.phd_student.doctoral_committee
        except DoctoralCommittee.DoesNotExist:
            raise forms.ValidationError(
                "Doctoral committee has not been created for this student."
            )

        committee_member = CommitteeMember.objects.filter(
            committee=committee,
            faculty=faculty,
        ).first()

        if not committee_member:
            raise forms.ValidationError(
                "You are not authorized to evaluate this dissertation defense."
            )

        existing_evaluation = DissertationDefenseEvaluation.objects.filter(
            defense=defense,
            committee_member=committee_member,
        )

        if self.instance.pk:
            existing_evaluation = existing_evaluation.exclude(
                pk=self.instance.pk,
            )

        if existing_evaluation.exists():
            raise forms.ValidationError(
                "You have already submitted your evaluation for this dissertation defense."
            )

        if self.instance.pk and self.instance.is_submitted:
            raise forms.ValidationError(
                "Submitted defense evaluations cannot be modified."
            )

        return cleaned_data

    def save(self, commit=True):

        evaluation = super().save(
            commit=False,
        )

        committee = self.defense.phd_student.doctoral_committee

        committee_member = CommitteeMember.objects.get(
            committee=committee,
            faculty=self.faculty,
        )

        evaluation.defense = self.defense
        evaluation.committee_member = committee_member
        evaluation.is_submitted = True
        evaluation.submitted_at = timezone.now()

        if commit:
            evaluation.save()

        return evaluation


class DissertationDefenseChairFinalizationForm(forms.ModelForm):

    class Meta:

        model = DissertationDefense

        fields = [
            "result",
            "committee_decision",
            "final_comments",
        ]

        widgets = {
            "result": forms.Select(
                attrs={
                    "class": "form-select choices",
                }
            ),
            "committee_decision": forms.Select(
                attrs={
                    "class": "form-select choices",
                }
            ),
            "final_comments": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 7,
                    "minlength": 20,
                    "maxlength": 5000,
                    "placeholder": "Enter the final defense decision and remarks...",
                }
            ),
        }

        labels = {
            "result": "Final Defense Result",
            "committee_decision": "Final Committee Decision",
            "final_comments": "Final Remarks",
        }

    def __init__(self, *args, **kwargs):

        self.faculty = kwargs.pop(
            "faculty",
            None,
        )

        super().__init__(
            *args,
            **kwargs,
        )

        if self.faculty is None:
            raise ValueError(
                "DissertationDefenseChairFinalizationForm requires a faculty instance."
            )

        self.fields["result"].choices = [
            (
                "",
                "Select final result",
            ),
            (
                "PASS",
                "Pass",
            ),
            (
                "FAIL",
                "Fail",
            ),
        ]

        self.fields["committee_decision"].choices = [
            (
                "",
                "Select final committee decision",
            ),
            (
                "APPROVED",
                "Approved",
            ),
            (
                "MINOR_REVISIONS",
                "Minor Revisions",
            ),
            (
                "MAJOR_REVISIONS",
                "Major Revisions",
            ),
            (
                "REJECTED",
                "Rejected",
            ),
        ]

        self.fields["result"].required = True
        self.fields["committee_decision"].required = True
        self.fields["final_comments"].required = True

    def clean_result(self):

        result = self.cleaned_data.get(
            "result",
        )

        if not result:
            raise forms.ValidationError("Please select the final defense result.")

        if result not in {
            "PASS",
            "FAIL",
        }:
            raise forms.ValidationError("Invalid final defense result.")

        return result

    def clean_committee_decision(self):

        committee_decision = self.cleaned_data.get(
            "committee_decision",
        )

        if not committee_decision:
            raise forms.ValidationError("Please select the final committee decision.")

        if committee_decision not in {
            "APPROVED",
            "MINOR_REVISIONS",
            "MAJOR_REVISIONS",
            "REJECTED",
        }:
            raise forms.ValidationError("Invalid final committee decision.")

        return committee_decision

    def clean_final_comments(self):

        final_comments = self.cleaned_data.get(
            "final_comments",
        )

        if not final_comments or not final_comments.strip():
            raise forms.ValidationError("Final remarks are required.")

        final_comments = final_comments.strip()

        if len(final_comments) < 20:
            raise forms.ValidationError(
                "Final remarks must contain at least 20 characters."
            )

        if len(final_comments) > 5000:
            raise forms.ValidationError("Final remarks cannot exceed 5000 characters.")

        return final_comments

    def clean(self):

        cleaned_data = super().clean()

        defense = self.instance
        faculty = self.faculty

        if not defense or not defense.pk:
            raise forms.ValidationError(
                "A dissertation defense is required for finalization."
            )

        if defense.result != "PENDING":
            raise forms.ValidationError(
                "This dissertation defense has already been finalized."
            )

        try:
            committee = defense.phd_student.doctoral_committee
        except DoctoralCommittee.DoesNotExist:
            raise forms.ValidationError(
                "Doctoral committee has not been created for this student."
            )

        if committee.chair_faculty_id != faculty.pk:
            raise forms.ValidationError(
                "Only the Chair Faculty can finalize this dissertation defense."
            )

        if defense.defense_date > timezone.localdate():
            raise forms.ValidationError(
                "The dissertation defense must be conducted before it can be finalized."
            )

        required_members = CommitteeMember.objects.filter(
            committee=committee,
            role__in=[
                "CO_CHAIR",
                "INTERNAL_MEMBER",
                "EXTERNAL_MEMBER",
            ],
        )

        required_member_ids = list(
            required_members.values_list(
                "pk",
                flat=True,
            )
        )

        if not required_member_ids:
            raise forms.ValidationError(
                "At least one committee member evaluation is required before finalization."
            )

        submitted_member_ids = set(
            DissertationDefenseEvaluation.objects.filter(
                defense=defense,
                committee_member_id__in=required_member_ids,
                is_submitted=True,
            ).values_list(
                "committee_member_id",
                flat=True,
            )
        )

        missing_member_ids = set(required_member_ids) - submitted_member_ids

        if missing_member_ids:
            raise forms.ValidationError(
                "All required committee members must submit their defense evaluations before Chair finalization."
            )

        result = cleaned_data.get(
            "result",
        )

        committee_decision = cleaned_data.get(
            "committee_decision",
        )

        if result == "PASS" and committee_decision == "REJECTED":
            raise forms.ValidationError(
                "A passed defense cannot have a rejected committee decision."
            )

        if result == "FAIL" and committee_decision == "APPROVED":
            raise forms.ValidationError(
                "A failed defense cannot have an approved committee decision."
            )

        return cleaned_data

    def save(self, commit=True):

        defense = super().save(
            commit=False,
        )

        if commit:
            defense.save()

        return defense


## Leo's Code End ##
