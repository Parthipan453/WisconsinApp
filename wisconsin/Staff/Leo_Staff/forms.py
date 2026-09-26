from django import forms

from django.db.models import OuterRef, Subquery, Q

from Students.Leo_Student.models import (
    Graduation,
    PhDStudent,
    FinalDissertationSubmission,
    DissertationDefense,
)


class GraduationCreationForm(forms.ModelForm):

    phd_student = forms.ModelChoiceField(
        queryset=PhDStudent.objects.none(),
        empty_label=None,
        widget=forms.Select(
            attrs={
                "class": "form-select choices-select",
                "data-placeholder": "Select PhD Student",
            }
        ),
    )

    graduation_date = forms.DateField(
        required=True,
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "class": "form-control flatpickr-date",
                "placeholder": "Select graduation date",
                "autocomplete": "off",
            },
        ),
    )

    graduation_time = forms.TimeField(
        required=True,
        widget=forms.TimeInput(
            format="%H:%M",
            attrs={
                "class": "form-control",
                "type": "time",
            },
        ),
    )

    graduation_location = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Graduation location",
            },
        ),
    )

    final_gpa = forms.DecimalField(
        required=True,
        max_digits=4,
        decimal_places=2,
        min_value=0,
        max_value=10,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter final GPA",
                "step": "0.01",
                "min": "0",
                "max": "10",
            },
        ),
    )

    class Meta:

        model = Graduation

        fields = [
            "phd_student",
            "graduation_date",
            "graduation_time",
            "graduation_location",
            "final_gpa",
        ]

        labels = {
            "phd_student": "PhD Student",
            "graduation_date": "Graduation Date",
            "graduation_time": "Graduation Time",
            "graduation_location": "Graduation Location",
            "final_gpa": "Final GPA",
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        latest_dissertation = (
            FinalDissertationSubmission.objects.filter(
                phd_student=OuterRef("pk"),
            )
            .order_by(
                "-submission_number",
                "-created_at",
            )
            .values("status")[:1]
        )

        students = (
            PhDStudent.objects.select_related(
                "student__user",
            )
            .annotate(
                latest_dissertation_status=Subquery(
                    latest_dissertation,
                ),
            )
            .filter(
                latest_dissertation_status="APPROVED",
                dissertation_defense__result="PASS",
            )
        )

        if self.instance.pk:
            students = students.filter(
                Q(graduation__isnull=True) | Q(graduation=self.instance)
            )
        else:
            students = students.filter(
                graduation__isnull=True,
            )

        self.fields["phd_student"].queryset = students.order_by(
            "student__user__first_name",
            "student__user__last_name",
        )

        if not self.instance.pk:
            self.fields["graduation_location"].initial = "University Common Hall"

    def clean(self):

        cleaned_data = super().clean()

        student = cleaned_data.get("phd_student")

        if not student:
            return cleaned_data

        latest_final_dissertation = (
            FinalDissertationSubmission.objects.filter(
                phd_student=student,
            )
            .order_by(
                "-submission_number",
                "-created_at",
            )
            .first()
        )

        if not latest_final_dissertation:
            raise forms.ValidationError(
                "The student has not submitted a final dissertation."
            )

        if latest_final_dissertation.status != "APPROVED":
            raise forms.ValidationError(
                "The student's final dissertation must be approved before graduation can be created."
            )

        defense = getattr(
            student,
            "dissertation_defense",
            None,
        )

        if not defense:
            raise forms.ValidationError(
                "The student has not completed the dissertation defense."
            )

        if defense.result != "PASS":
            raise forms.ValidationError(
                "The student must pass the dissertation defense before graduation can be created."
            )

        existing_graduation = (
            Graduation.objects.filter(
                phd_student=student,
            )
            .exclude(
                pk=self.instance.pk,
            )
            .first()
        )

        if existing_graduation:
            raise forms.ValidationError(
                "A graduation record already exists for this student."
            )

        cleaned_data["final_dissertation"] = latest_final_dissertation
        cleaned_data["dissertation_defense"] = defense
        cleaned_data["dissertation_accepted"] = True
        cleaned_data["defense_passed"] = True

        return cleaned_data

    def clean_graduation_date(self):

        graduation_date = self.cleaned_data.get(
            "graduation_date",
        )

        if graduation_date:
            from django.utils import timezone

            if graduation_date < timezone.localdate():
                raise forms.ValidationError("Graduation date cannot be in the past.")

        return graduation_date

    def clean_final_gpa(self):

        final_gpa = self.cleaned_data.get(
            "final_gpa",
        )

        if final_gpa is not None and final_gpa < 0:
            raise forms.ValidationError("Final GPA cannot be negative.")

        return final_gpa
