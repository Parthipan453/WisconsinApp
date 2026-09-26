
from django import forms
from Students.models import CourseSection, Semester
from datetime import datetime
import re


class CourseSectionForm(forms.ModelForm):
    TERM_CHOICES = [
        ("", "— Select Semester —"),
        ("Spring", "Spring"),
        ("Summer", "Summer"),
        ("Fall", "Fall"),
        ("Winter", "Winter"),
    ]

    semester_id = forms.ChoiceField(
        choices=TERM_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        required=True,
    )

    class Meta:
        model = CourseSection
        fields = [
            "course",
            "section_number",
            "section_type",
            "semester_id",
            "capacity",
             "building_name",
            "room_number",
        ]

        widgets = {
            "course": forms.Select(attrs={
                "class": "form-select",
                "required": "required"
            }),

            "section_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Section Number",
                "required":"required"
            }),

            "section_type": forms.Select(attrs={
                "class": "form-select",
                "required":"required"
            }),
            "capacity": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Capacity",
                "required":"required"
            }),
            "building_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter Building Name",
                }
            ),

            "room_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter Room Number",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.semester_id_id:
            semester = self.instance.semester_id
            if semester:
                type_map = {'FA': 'Fall', 'SP': 'Spring', 'SU': 'Summer', 'WI': 'Winter'}
                self.initial['semester_id'] = type_map.get(semester.semester_type, '')

    def clean_semester_id(self):
        term = self.cleaned_data.get('semester_id')
        if not term:
            raise forms.ValidationError("This field is required.")
        type_map = {'Spring': 'SP', 'Summer': 'SU', 'Fall': 'FA', 'Winter': 'WI'}
        st_code = type_map.get(term)
        if not st_code:
            raise forms.ValidationError("Invalid semester selected.")
        semester = Semester.objects.filter(
            semester_type=st_code, is_current=True
        ).first()
        if not semester:
            semester = Semester.objects.filter(
                semester_type=st_code
            ).order_by('-academic_year', '-semester_id').first()
        if not semester:
            semester = Semester.objects.create(
                semester_code=f"{st_code}{datetime.now().year}",
                semester_type=st_code,
                academic_year=datetime.now().year,
                start_date=datetime.now().date(),
                end_date=datetime.now().date(),
            )
        return semester

#Ranganayagi code end