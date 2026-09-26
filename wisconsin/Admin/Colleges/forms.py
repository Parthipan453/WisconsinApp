#####################  steve code start ######################################
from django import forms
from .models import University, School, Degree,AcademicProgram, ProgramCourse,AcademicTerm
from Admin.models import User
from Admin.bela_admin.models import Course
import re
from .validators import validate_global_code
from django.core.exceptions import ValidationError


class UniversityForm(forms.ModelForm):

    class Meta:
        model = University
        fields = [
            "university_name",
            "university_short_name",
            "university_code",
            "university_type",
            "ownership_type",
            "official_email",
            "phone_number",
            "website",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "country",
            "postal_code",
            "established_year",
            "accreditation",
            "logo",
        ]

    
    def clean_university_name(self):
        name = self.cleaned_data.get("university_name", "").strip()

        if len(name) < 3:
            raise forms.ValidationError(
                "University name must contain at least 3 characters."
            )

        if University.objects.exclude(
            pk=self.instance.pk
        ).filter(
            university_name__iexact=name
        ).exists():
            raise forms.ValidationError(
                "A university with this name already exists."
            )

        return name

    
    def clean_university_short_name(self):
        short_name = self.cleaned_data.get(
            "university_short_name",
            ""
        ).strip()

        if len(short_name) < 2:
            raise ValidationError(
                "University short name must contain at least 2 characters."
            )

        return short_name

    
    def clean_university_code(self):
        code = self.cleaned_data.get(
            "university_code",
            ""
        ).strip().upper()

        if len(code) < 2:
            raise ValidationError(
                "University code is required."
            )

        validate_global_code(code, self.instance)

        return code

    
    def clean_official_email(self):
        email = self.cleaned_data.get(
            "official_email",
            ""
        ).strip().lower()

        if University.objects.exclude(
            pk=self.instance.pk
        ).filter(
            official_email__iexact=email
        ).exists():
            raise ValidationError(
                "This official email is already in use."
            )

        return email

    
    def clean_phone_number(self):
        phone = self.cleaned_data.get(
            "phone_number",
            ""
        ).strip()

        if not re.fullmatch(r"^\+?[0-9]{7,15}$", phone):
            raise ValidationError(
                "Enter a valid phone number."
            )

        return phone

    
    def clean_address_line_1(self):
        address = self.cleaned_data.get(
            "address_line_1",
            ""
        ).strip()

        if len(address) < 10:
            raise ValidationError(
                "Please enter a complete address."
            )

        return address

    
    def clean_city(self):
        city = self.cleaned_data.get("city", "").strip()

        if len(city) < 2:
            raise ValidationError(
                "City name must contain at least 2 characters."
            )

        return city

    
    def clean_state(self):
        state = self.cleaned_data.get("state", "").strip()

        if len(state) < 2:
            raise ValidationError(
                "State name must contain at least 2 characters."
            )

        return state

    
    def clean_country(self):
        country = self.cleaned_data.get("country", "").strip()

        if len(country) < 2:
            raise ValidationError(
                "Country name must contain at least 2 characters."
            )

        return country

    
    def clean_postal_code(self):
        postal = self.cleaned_data.get(
            "postal_code",
            ""
        ).strip()

        if len(postal) < 4:
            raise ValidationError(
                "Enter a valid postal code."
            )

        return postal

    
    def clean_established_year(self):
        year = self.cleaned_data.get(
            "established_year"
        )

        if year < 1800:
            raise ValidationError(
                "Please enter a valid established year."
            )

        from datetime import date

        if year > date.today().year:
            raise ValidationError(
                "Established year cannot be in the future."
            )

        return year

    
    def clean_accreditation(self):
        accreditation = self.cleaned_data.get(
            "accreditation"
        )

        if not accreditation:
            return accreditation

        accreditation = accreditation.strip()

        if len(accreditation) < 2:
            raise ValidationError(
                "Accreditation must contain at least 2 characters."
            )

        return accreditation

    
    def clean_website(self):
        website = self.cleaned_data.get("website")

        if not website:
            return website

        return website
    
class SchoolForm(forms.ModelForm):

    class Meta:
        model = School
        fields = [
            "university",
            "school_name",
            "school_short_name",
            "school_code",
            "school_type",
            "dean",
            "official_email",
            "phone_number",
            "website",
            "building_name",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "country",
            "postal_code",
            "established_year",
            "description",
            "logo",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["dean"].required = False
        self.fields["dean"].empty_label = "Assign Later"

        self.fields["dean"].queryset = User.objects.filter(
            is_active=True,
            account_status="ACTIVE",
            is_faculty=True
        ).order_by("first_name", "last_name")
    

    def clean_university(self):
        university = self.cleaned_data.get("university")

        if not university:
            raise forms.ValidationError(
                "Please select a university."
            )

        return university


    def clean_school_name(self):
        name = self.cleaned_data.get("school_name", "").strip()

        if len(name) < 3:
            raise forms.ValidationError(
                "School name must contain at least 3 characters."
            )

        return name


    def clean_school_short_name(self):
        short_name = self.cleaned_data.get(
            "school_short_name",
            ""
        ).strip()

        if len(short_name) < 2:
            raise forms.ValidationError(
                "School short name must contain at least 2 characters."
            )

        return short_name


    def clean_school_code(self):
        code = self.cleaned_data.get(
            "school_code",
            ""
        ).strip().upper()

        if len(code) < 2:
            raise forms.ValidationError(
                "School code is required."
            )

        validate_global_code(code, self.instance)

        return code


    def clean_official_email(self):
        email = self.cleaned_data.get(
            "official_email"
        )

        if not email:
            return email

        email = email.strip().lower()

        if School.objects.exclude(
            pk=self.instance.pk
        ).filter(
            official_email__iexact=email
        ).exists():
            raise forms.ValidationError(
                "This official email already exists."
            )

        return email

   
    def clean_phone_number(self):
        phone = self.cleaned_data.get(
            "phone_number"
        )

        if not phone:
            return phone

        phone = phone.strip()

        if not re.fullmatch(r"^\+?[0-9]{7,15}$", phone):
            raise forms.ValidationError(
                "Enter a valid phone number."
            )

        return phone


    def clean_address_line_1(self):
        address = self.cleaned_data.get(
            "address_line_1"
        )

        if not address:
            return address

        address = address.strip()

        if len(address) < 5:
            raise forms.ValidationError(
                "Please enter a valid address."
            )

        return address


    def clean_city(self):
        city = self.cleaned_data.get("city")

        if not city:
            return city

        city = city.strip()

        if len(city) < 2:
            raise forms.ValidationError(
                "City name is too short."
            )

        return city


    def clean_state(self):
        state = self.cleaned_data.get("state")

        if not state:
            return state

        state = state.strip()

        if len(state) < 2:
            raise forms.ValidationError(
                "State name is too short."
            )

        return state


    def clean_country(self):
        country = self.cleaned_data.get("country")

        if not country:
            return country

        country = country.strip()

        if len(country) < 2:
            raise forms.ValidationError(
                "Country name is too short."
            )

        return country


    def clean_postal_code(self):
        postal = self.cleaned_data.get(
            "postal_code"
        )

        if not postal:
            return postal

        postal = postal.strip()

        if len(postal) < 4:
            raise forms.ValidationError(
                "Enter a valid postal code."
            )

        return postal


    def clean_established_year(self):
        year = self.cleaned_data.get(
            "established_year"
        )

        if not year:
            return year

        from datetime import date

        if year < 1800:
            raise forms.ValidationError(
                "Please enter a valid established year."
            )

        if year > date.today().year:
            raise forms.ValidationError(
                "Established year cannot be in the future."
            )

        return year


    def clean_description(self):
        description = self.cleaned_data.get(
            "description"
        )

        if not description:
            return description

        description = description.strip()

        if len(description) < 20:
            raise forms.ValidationError(
                "Description must contain at least 20 characters."
            )

        return description



class DegreeForm(forms.ModelForm):

    class Meta:
        model = Degree
        fields = [
            "degree_name",
            "degree_code",
            "level",
        ]

    

    def clean_degree_name(self):
        name = self.cleaned_data.get("degree_name", "").strip()

        if len(name) < 3:
            raise forms.ValidationError(
                "Degree name must contain at least 3 characters."
            )

        if not re.match(r"^[A-Za-z\s&()'-]+$", name):
            raise forms.ValidationError(
                "Degree name can contain only letters and spaces."
            )

        return name.title()

  
    
    def clean_degree_code(self):

        code = self.cleaned_data.get("degree_code", "").strip().upper()

        if len(code) < 2:
            raise forms.ValidationError(
                "Degree code must contain at least 2 characters."
            )

        if not re.match(r"^[A-Z.-]+$", code):
            raise forms.ValidationError(
                "Degree code can contain only uppercase letters, hyphen (-) and period (.)."
            )


        validate_global_code(code, self.instance)

        return code


    def clean_level(self):
        level = self.cleaned_data.get("level")

        if not level:
            raise forms.ValidationError(
                "Please select a degree level."
            )

        valid_levels = ["UG", "PG", "PHD"]

        if level not in valid_levels:
            raise forms.ValidationError(
                "Invalid degree level selected."
            )

        return level
    
    

class AcademicProgramForm(forms.ModelForm):

    class Meta:
        model = AcademicProgram
        fields = [
            "program_code",
            "department",
            "degree",
            "program_name",
            "program_type",
            "duration",
            "total_credits",
            "description",
            "areas_of_interest",
        ]
        widgets = {
            "areas_of_interest": forms.CheckboxSelectMultiple(),
        }

    def clean(self):
        cleaned_data = super().clean()

        department = cleaned_data.get("department")
        degree = cleaned_data.get("degree")
        program_name = cleaned_data.get("program_name")

        if department and degree and program_name:
            qs = AcademicProgram.objects.filter(
                department=department,
                degree=degree,
                program_name__iexact=program_name.strip()
            )

            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise forms.ValidationError(
                    "This program already exists for the selected department and degree."
                )

        return cleaned_data


    def clean_program_code(self):
        code = self.cleaned_data.get("program_code", "")
        
        if code is None:
            code = ""
        
        code = code.strip().upper()
        
        if len(code) < 2:
            raise forms.ValidationError(
                "Program code must contain at least 2 characters."
            )
        
        if len(code) > 20:
            raise forms.ValidationError(
                "Program code cannot exceed 20 characters."
            )
        

        if not re.match(r"^[A-Z.-]+$", code):
            raise forms.ValidationError(
                "Program code can contain only uppercase letters, hyphen (-) and period (.). Numbers are not allowed."
            )

        validate_global_code(code, self.instance)

        return code

    def clean_department(self):
        department = self.cleaned_data.get("department")
        if not department:
            raise forms.ValidationError(
                "Please select a department."
            )
        return department

    def clean_degree(self):
        degree = self.cleaned_data.get("degree")
        if not degree:
            raise forms.ValidationError(
                "Please select a degree."
            )
        return degree

    def clean_program_name(self):
        name = self.cleaned_data.get("program_name", "").strip()
        
        if len(name) < 3:
            raise forms.ValidationError(
                "Program name must contain at least 3 characters."
            )
            
        if len(name) > 100:
            raise forms.ValidationError(
                "Program name cannot exceed 100 characters."
            )
        

        if not re.match(r"^[A-Za-z\s&()'.-]+$", name):
            raise forms.ValidationError(
                "Program name can only contain letters, spaces, and basic punctuation. Numbers are not allowed."
            )
        
        return name.title()

    def clean_program_type(self):
        program_type = self.cleaned_data.get("program_type")
        valid = ["FULL_TIME", "PART_TIME", "ONLINE"]
        if program_type not in valid:
            raise forms.ValidationError(
                "Please select a valid program type."
            )
        return program_type

    def clean_duration(self):
        duration = self.cleaned_data.get("duration")

        if duration is None:
            raise forms.ValidationError("Duration is required.")

        if not isinstance(duration, int):
            raise forms.ValidationError("Duration must be a whole number.")

        if duration < 1 or duration > 10:
            raise forms.ValidationError(
                "Duration must be between 1 and 10 years."
            )

        return duration

    def clean_total_credits(self):
        credits = self.cleaned_data.get("total_credits")

        if credits is None:
            raise forms.ValidationError(
                "Total credits is required."
            )

        if not isinstance(credits, int):
            raise forms.ValidationError(
                "Total credits must be a whole number."
            )

        if credits < 1 or credits > 300:
            raise forms.ValidationError(
                "Total credits must be between 1 and 300."
            )

        return credits

    def clean_description(self):
        description = self.cleaned_data.get("description", "").strip()

        # Normalize Windows CRLF to LF
        normalized = description.replace("\r\n", "\n")

        if len(normalized) < 20:
            raise forms.ValidationError(
                "Description must contain at least 20 characters."
            )

        if len(normalized) > 500:
            raise forms.ValidationError(
                "Description cannot exceed 500 characters."
            )

        return description
    
    


class ProgramCourseBulkForm(forms.Form):
    program = forms.ModelChoiceField(
        queryset=AcademicProgram.objects.all(),
        widget=forms.Select(attrs={"class": "form-select", "id": "id_program"}),
        error_messages={"required": "Please select a program."},
    )
    study_year = forms.ChoiceField(
        choices=ProgramCourse.YEAR_CHOICES,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_study_year"}),
        error_messages={"required": "Please select study year."},
    )
    term = forms.ChoiceField(
        choices=ProgramCourse.TERM_CHOICES,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_term"}),
        error_messages={"required": "Please select term."},
    )
    # status = forms.ChoiceField(
    #     choices=ProgramCourse.STATUS_CHOICES,
    #     initial="ACTIVE",
    #     widget=forms.Select(attrs={"class": "form-select"}),
    # )
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "course-checkbox"}),
        error_messages={"required": "Please select at least one course."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        
        program_id = None
        if self.data.get("program"):
            program_id = self.data.get("program")
        elif self.initial.get("program"):
            program_id = self.initial.get("program")

        if program_id:
            try:
                self.fields["courses"].queryset = Course.objects.filter(
                    academic_program_id=int(program_id),
                    status="ACTIVE",
                ).order_by("course_name")
            except (ValueError, TypeError):
                self.fields["courses"].queryset = Course.objects.none()
 #################  Rixie Code start ###############
    def clean_courses(self):
        courses = self.cleaned_data.get("courses")
        if courses:
            allocated_ids = set(
                ProgramCourse.objects.values_list("course_id", flat=True)
            )
            already_allocated = [
                c for c in courses if c.course_id in allocated_ids
            ]
            if already_allocated:
                names = ", ".join(c.course_name for c in already_allocated)
                raise ValidationError(
                    f'Course "{names}" is already allocated to another year/term. '
                    "A course can only be assigned to one year and one term."
                )
        return courses
############### Rixie Code End #######################
    def clean(self):
        cleaned_data = super().clean()
        program = cleaned_data.get("program")
        courses = cleaned_data.get("courses")

        if program and courses:
            mismatched = [c for c in courses if c.academic_program_id != program.program_id]
            if mismatched:
                raise ValidationError(
                    "One or more selected courses do not belong to the selected program."
                )

        return cleaned_data
        

class ProgramCourseForm(forms.ModelForm):

    class Meta:
        model = ProgramCourse
        fields = [
            "program",
            "course",
            "study_year",
            "term",
            "is_elective",
            # "status",
        ]

        widgets = {
            "program": forms.Select(attrs={"class": "form-select"}),
            "course": forms.Select(attrs={"class": "form-select"}),
            "study_year": forms.Select(attrs={"class": "form-select"}),
            "term": forms.Select(attrs={"class": "form-select"}),
            "is_elective": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            # "status": forms.Select(attrs={"class": "form-select"}),
        }
        
    def clean(self):
        cleaned_data = super().clean()

        program = cleaned_data.get("program")
        course = cleaned_data.get("course")

        if program and course:
            if course.academic_program_id != program.program_id:
                raise forms.ValidationError(
                    "The selected course does not belong to the selected program."
                )
############  Rixie Code Start ################
            allocated = ProgramCourse.objects.filter(course=course)
            if self.instance and self.instance.pk:
                allocated = allocated.exclude(pk=self.instance.pk)
            if allocated.exists():
                self.add_error(
                    "course",
                    f'Course "{course.course_name}" is already allocated to another year/term. '
                    "A course can only be assigned to one year and one term.",
                )
###########  Rixie Code End  ###################
        return cleaned_data



class AcademicTermForm(forms.ModelForm):

    class Meta:
        model = AcademicTerm

        fields = [
            "academic_year",
            "term_name",
            "start_date",
            "end_date",
            "registration_start",
            "registration_end",
            "status",
        ]

        widgets = {

            "academic_year": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: 2026-2027",
                    "maxlength": "9",
                    "autocomplete": "off",
                }
            ),

            "term_name": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "start_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "end_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "registration_start": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "registration_end": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }

    

    def clean_academic_year(self):

        academic_year = self.cleaned_data["academic_year"].strip()

        import re

        pattern = r"^\d{4}-\d{4}$"

        if not re.match(pattern, academic_year):
            raise forms.ValidationError(
                "Academic Year must be in YYYY-YYYY format."
            )

        start_year, end_year = map(int, academic_year.split("-"))

        if end_year != start_year + 1:
            raise forms.ValidationError(
                "End year must be exactly one year after the start year."
            )

        return academic_year

    

    def clean(self):

        cleaned_data = super().clean()

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        registration_start = cleaned_data.get("registration_start")
        registration_end = cleaned_data.get("registration_end")

        # Academic Term Dates

        if start_date and end_date:

            if start_date >= end_date:

                self.add_error(
                    "end_date",
                    "End Date must be later than Start Date."
                )

        # Registration Dates

        if registration_start and registration_end:

            if registration_start > registration_end:

                self.add_error(
                    "registration_end",
                    "Registration End must be after Registration Start."
                )

        # Registration before Term

        if registration_start and start_date:

            if registration_start > start_date:

                self.add_error(
                    "registration_start",
                    "Registration should begin before the academic term starts."
                )

        return cleaned_data
#####################  steve code end ######################################