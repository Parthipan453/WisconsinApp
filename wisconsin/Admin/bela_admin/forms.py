import code
from datetime import datetime
import re

from django import forms

from .models import CourseLearningOutcome, CourseOffering, CourseRequirementType, Department,Course
from .models import Department,Course
from Admin.Colleges.models import School, AcademicProgram, Degree
from .models import Department, Course, CourseDesignationType


class DepartmentForm(forms.ModelForm):

    school = forms.ModelChoiceField(
        queryset=School.objects.select_related('university').all(),
        empty_label='— Select a school —',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Department
        fields = [
            'school',
            'department_code',
            'department_name',
            'short_name',
            'description',
            'website',
            'office_location',
            'email',
            'phone_number',
            'established_year',
            
        ]

        widgets = {
            'department_code': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g. CS-001'
                }
            ),

            'department_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g. Computer Science'
                }
            ),

            'short_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g. CS'
                }
            ),

            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4
                }
            ),

            'website': forms.URLInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'https://example.com'
                }
            ),

            'office_location': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Building, Room Number'
                }
            ),

            'email': forms.EmailInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'department@university.edu'
                }
            ),

            'phone_number': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '+1 (608) 000-0000'
                }
            ),

            'established_year': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '1950'
                }
            ),

           
        }


    def clean_department_name(self):
        """
        Prevent duplicate department names.
        """
        name = self.cleaned_data.get('department_name')

        qs = Department.objects.filter(
            department_name__iexact=name
        )

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(
                "A department with this name already exists."
            )

        return name

    def clean_established_year(self):
        """
        Prevent future years.
        """
        year = self.cleaned_data.get('established_year')

        if year:
            current_year = datetime.now().year

            if year > current_year:
                raise forms.ValidationError(
                    "Established year cannot be in the future."
                )

        return year
    
    
    def clean_department_code(self):

        code = self.cleaned_data.get("department_code")

        if not code:
            return code

        # Convert to uppercase and remove extra spaces
        code = " ".join(code.strip().upper().split())

        # Only letters and spaces allowed
        if not re.fullmatch(r"[A-Z\s]+", code):
            raise forms.ValidationError(
                "Department code can contain only letters and spaces."
            )

        qs = Department.objects.filter(
            department_code__iexact=code
        )

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(
                "Department code already exists."
            )

        return code
    
    def clean_short_name(self):
        short_name = self.cleaned_data.get("short_name")

        if short_name:
            qs = Department.objects.filter(
                short_name__iexact=short_name
            )

            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise forms.ValidationError(
                    "Short name already exists."
                )

        return short_name



class DepartmentEditForm(forms.ModelForm):

    school = forms.ModelChoiceField(
        queryset=School.objects.select_related('university').all(),
        empty_label='— Select a school —',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Department

        fields = [
            'school',
            'department_code',
            'department_name',
            'short_name',
            'description',
            'website',
            'office_location',
            'email',
            'phone_number',
            'established_year',
            'status',
        ]

        widgets = {

            'department_code': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g. CS-001'
                }
            ),

            'department_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g. Computer Science'
                }
            ),

            'short_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g. CS'
                }
            ),

            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4
                }
            ),

            'website': forms.URLInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'https://example.com'
                }
            ),

            'office_location': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Building, Room Number'
                }
            ),

            'email': forms.EmailInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'department@university.edu'
                }
            ),

            'phone_number': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '+1 (608) 000-0000'
                }
            ),

            'established_year': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '1950'
                }
            ),

            'status': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),
        }

    def clean_department_code(self):

        code = self.cleaned_data.get("department_code")

        if not code:
            return code
 
        # Convert to uppercase and remove extra spaces
        code = " ".join(code.strip().upper().split())

        # Only letters and spaces allowed
        if not re.fullmatch(r"[A-Z\s]+", code):
            raise forms.ValidationError(
                "Department code can contain only letters and spaces."
            )

        qs = Department.objects.filter(
            department_code__iexact=code
        )

        # Ignore current department while editing
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(
                "Department code already exists."
            )

        return code

    def clean_department_name(self):

        name = self.cleaned_data.get('department_name')

        qs = Department.objects.filter(
            department_name__iexact=name
        )

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(
                "A department with this name already exists."
            )

        return name

    def clean_established_year(self):

        year = self.cleaned_data.get('established_year')

        if year:

            current_year = datetime.now().year

            if year > current_year:
                raise forms.ValidationError(
                    "Established year cannot be in the future."
                )

        return year



class CourseRequirementTypeForm(forms.ModelForm):
    class Meta:
        model = CourseRequirementType
        fields = [
            "name",
            "description",
            "status",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Requirement Type"
            }),

            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Enter Description"
            }),

            "status": forms.Select(attrs={
                "class": "form-select"
            }),
        }

        labels = {
            "name": "Requirement Type",
            "description": "Description",
            "status": "Status",
        }

        




############aadharsh code #######################################################

class CourseForm(forms.ModelForm):

    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(status='ACTIVE').select_related('school'),
        empty_label='— Select a department —',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    academic_program = forms.ModelChoiceField(
        queryset=AcademicProgram.objects.filter(status='ACTIVE').select_related('department'),
        empty_label='— Select an academic program —',
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
    )

    degree = forms.ModelChoiceField(
        queryset=Degree.objects.filter(status='ACTIVE'),
        empty_label='— Select a degree —',
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
    )

    class Meta:
        model = Course
        fields = [
            'department',
            'academic_program',
            'degree',
            'course_code',
            'course_name',
            'credits',
            'description',
            'email',
            'phone_number',
            'website',
            'office_location',
        ]

        widgets = {
            'course_code': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g. CS-101'
                }
            ),

            'course_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g. Introduction to Computer Science'
                }
            ),

            'credits': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g. 3'
                }
            ),

            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Course description and learning outcomes'
                }
            ),

            'email': forms.EmailInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'course@wisc.edu'
                }
            ),

            'phone_number': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '+1 608-123-4567'
                }
            ),

            'website': forms.URLInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'https://course.wisc.edu'
                }
            ),

            'office_location': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g. Engineering Hall, Room 101'
                }
            ),
        }

    def clean_course_code(self):

        code = self.cleaned_data.get("course_code")

        if not code:
            return code

        code = code.strip()

        # Only numbers allowed
        if not code.isdigit():
            raise forms.ValidationError(
                "Course code must contain numbers only."
            )

        department = self.cleaned_data.get("department")

        qs = Course.objects.filter(
            department=department,
            course_code=code
        )

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(
                "A course with this code already exists for the selected department."
            )

        return code

    def clean_course_name(self):
        name = self.cleaned_data.get('course_name')

        qs = Course.objects.filter(
            course_name__iexact=name
        )

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(
                "A course with this name already exists."
            )

        return name

    def clean_description(self):
        desc = self.cleaned_data.get('description')
        if desc:
            import re
            desc = re.sub(r'[ \t]+', ' ', desc.strip())
            word_count = len(desc.split())
            if word_count > 1000:
                raise forms.ValidationError(
                    f"Description must be 1000 words or fewer. Currently {word_count} words."
                )
        return desc


# Speed code: CourseEditForm 
class CourseEditForm(forms.ModelForm):

    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(status='ACTIVE').select_related('school'),
        empty_label='— Select a department —',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    academic_program = forms.ModelChoiceField(
        queryset=AcademicProgram.objects.filter(status='ACTIVE').select_related('department'),
        empty_label='— Select an academic program —',
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
    )

    degree = forms.ModelChoiceField(
        queryset=Degree.objects.filter(status='ACTIVE'),
        empty_label='— Select a degree —',
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
    )

    class Meta:
        model = Course

        fields = [
            'department',
            'academic_program',
            'degree',
            'course_code',
            'course_name',
            'credits',
            'description',
            'email',
            'phone_number',
            'website',
            'office_location',
            'status',
        ]

        widgets = {

            'course_code': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g. CS-101'
                }
            ),

            'course_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g. Introduction to Computer Science'
                }
            ),

            'credits': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g. 3'
                }
            ),

            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Course description and learning outcomes'
                }
            ),

            'email': forms.EmailInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'course@wisc.edu'
                }
            ),

            'phone_number': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '+1 608-123-4567'
                }
            ),

            'website': forms.URLInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'https://course.wisc.edu'
                }
            ),

            'office_location': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g. Engineering Hall, Room 101'
                }
            ),

            'status': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),
        }

    def clean_course_code(self):

        code = self.cleaned_data.get("course_code")

        if not code:
            return code

        code = code.strip()

        # Only numbers allowed
        if not code.isdigit():
            raise forms.ValidationError(
                "Course code must contain numbers only."
            )

        department = self.cleaned_data.get("department")

        qs = Course.objects.filter(
            department=department,
            course_code=code
        )

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(
                "A course with this code already exists for the selected department."
            )

        return code
    def clean_course_name(self):

        name = self.cleaned_data.get('course_name')

        qs = Course.objects.filter(
            course_name__iexact=name
        )

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(
                "A course with this name already exists."
            )

        return name

    def clean_description(self):
        desc = self.cleaned_data.get('description')
        if desc:
            import re
            desc = re.sub(r'[ \t]+', ' ', desc.strip())
            word_count = len(desc.split())
            if word_count > 1000:
                raise forms.ValidationError(
                    f"Description must be 1000 words or fewer. Currently {word_count} words."
                )
        return desc
    
    def clean_credits(self):
        credits = self.cleaned_data.get("credits")

        if credits is None:
            return credits

        if credits < 1 or credits > 20:
            raise forms.ValidationError(
                "Credits must be between 1 and 20."
            )

        return credits
    
class CourseDesignationTypeForm(forms.ModelForm):
    class Meta:
        model = CourseDesignationType
        fields = ["designation_name", "description"]
        widgets = {
            "designation_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Writing Intensive",
                "data-validate": "required|text-only|min:2|max:150",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Brief description of this designation type",
                "data-maxchars": "500",
            }),
        }

    def clean_designation_name(self):
        name = self.cleaned_data.get("designation_name")
        if name:
            name = name.strip()
            qs = CourseDesignationType.objects.filter(designation_name__iexact=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("A designation type with this name already exists.")
        return name


class CourseDesignationTypeEditForm(forms.ModelForm):
    class Meta:
        model = CourseDesignationType
        fields = ["designation_name", "description", "status"]
        widgets = {
            "designation_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Writing Intensive",
                "data-validate": "required|text-only|min:2|max:150",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Brief description of this designation type",
                "data-maxchars": "500",
            }),
            "status": forms.Select(attrs={
                "class": "form-select",
            }),
        }

    def clean_designation_name(self):
        name = self.cleaned_data.get("designation_name")
        if name:
            name = name.strip()
            qs = CourseDesignationType.objects.filter(designation_name__iexact=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("A designation type with this name already exists.")
        return name



    #Ranganayagi code start
    
class CourseOfferingForm(forms.ModelForm):
    year = forms.IntegerField(
        min_value=1800,
        max_value=2100,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "2026",
                "min": "1800",
                "max": "2100",
            }
        ),
        error_messages={
            "min_value": "Year must be 1800 or later.",
            "max_value": "Year must be a valid 4-digit year.",
            "invalid": "Enter a valid 4-digit year.",
        }
    )

    class Meta:
        model = CourseOffering
        fields = ["term", "year"]

        widgets = {
            "term": forms.Select(attrs={"class": "form-select"}),
        }



class CourseLearningOutcomeForm(forms.ModelForm):
      class Meta:
        model = CourseLearningOutcome
        fields = ["outcome"]

        widgets = {
            "outcome": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter learning outcome"
                }
            ),
        }



      def clean_outcome(self):
          import re
          outcome = self.cleaned_data.get('outcome', '')
          outcome = re.sub(r'\n+', '\n', outcome)
          return outcome.strip()




from django import forms
from Students.models import CourseSection, Semester


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