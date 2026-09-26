from django import forms
from Research.models import *


class ResearchCommitteeForm(forms.ModelForm):
    class Meta:
        model = ResearchCommittee
        fields = ['department', 'faculty', 'role']
        widgets = {
            'department': forms.Select(attrs={
                'class': 'rc-input department-select'
            }),
            'faculty': forms.Select(attrs={
                'class': 'rc-input faculty-select'
            }),
            'role': forms.Select(attrs={
                'class': 'rc-input role-select',
                'data-placeholder': 'Select Role'
            }),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assigned = ResearchCommittee.objects.filter(
            is_active=True
        ).values_list(
            'faculty_id',
            flat=True
        )
        # Department list
        self.fields['department'].queryset = Department.objects.order_by(
            'department_name'
        )
         
        # Initially no faculty
        self.fields['faculty'].queryset = FacultyProfile.objects.none()
        # Edit mode
        if self.instance.pk:
            self.fields['faculty'].queryset = FacultyProfile.objects.filter(
                department_id=self.instance.department_id
            )
            # Disable department + faculty in edit
            self.fields['department'].disabled = True
            self.fields['faculty'].disabled = True
        # When validation fails after submit
        elif self.data.get('department'):
            self.fields['faculty'].queryset = FacultyProfile.objects.filter(
                department_id=self.data.get('department')
            ).exclude(
                id__in=assigned
            )
        self.fields['department'].empty_label = "Select Department"
        self.fields['faculty'].empty_label = "Select Faculty"
        self.fields['role'].choices = ResearchCommittee.COMMITTEE_ROLES
    def clean_faculty(self):
        faculty = self.cleaned_data['faculty']
        exists = ResearchCommittee.objects.filter(
            faculty=faculty,
            is_active=True
        )
        if self.instance.pk:
            exists = exists.exclude(
                pk=self.instance.pk
            )
        if exists.exists():
            raise forms.ValidationError(
                "This faculty member is already assigned to a committee."
            )
        return faculty
    def clean(self):
        cleaned_data = super().clean()
        department = cleaned_data.get("department") 
        role = cleaned_data.get("role")
        if department and role == "chair":
            exists = ResearchCommittee.objects.filter(
                department=department,
                role="chair",
                is_active=True
            )
            if self.instance.pk:
                exists = exists.exclude(pk=self.instance.pk)            
            if exists.exists():
                self.add_error(
                    'role',
                    "This department already has a Chairperson."
                )
        return cleaned_data
        
    


# ======================== Jordan code Start's Here ========================

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from Research.models import StudentResearchApplication


class StudentResearchApplicationForm(forms.ModelForm):
    """
    Form for students to apply for research opportunities.
    All validation is handled server-side in this form.
    """
    
    confirm_terms = forms.BooleanField(
        required=True,
        label="I confirm that all information provided is accurate and complete.",
        error_messages={
            'required': 'You must agree to the terms and conditions to submit your application.'
        }
    )
    
    # Define choices for select fields with proper labels
    TIME_COMMITMENT_CHOICES = [
        ('', 'Time Commitment'),  # Empty choice with label
        ('5-10', '5-10 hours/week'),
        ('10-15', '10-15 hours/week'),
        ('15-20', '15-20 hours/week'),
        ('20+', '20+ hours/week'),
    ]
    
    AVAILABILITY_CHOICES = [
        ('', 'Availability'),  # Empty choice with label
        ('semester', 'Full Semester'),
        ('summer', 'Summer Only'),
        ('winter', 'Winter Break'),
        ('year-round', 'Year Round'),
    ]
    
    class Meta:
        model = StudentResearchApplication
        fields = [
            'motivation',
            'skills_contribution',
            'prior_experience',
            'time_commitment',
            'availability',
            'additional_info',
            'resume',
            'statement_of_interest',
            'academic_transcript',
        ]
        widgets = {
            'motivation': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Describe your motivation for joining this research project...',
                'class': 'filter-input',
                'id': 'id_motivation'
            }),
            'skills_contribution': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'List your relevant skills and how they can benefit the research...',
                'class': 'filter-input',
                'id': 'id_skills_contribution'
            }),
            'prior_experience': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Describe any previous research experience...',
                'class': 'filter-input',
                'id': 'id_prior_experience'
            }),
            'additional_info': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Any additional information about yourself...',
                'class': 'filter-input',
                'id': 'id_additional_info'
            }),
            'time_commitment': forms.Select(attrs={
                'class': 'filter-input',
                'id': 'id_time_commitment'
            }),
            'availability': forms.Select(attrs={
                'class': 'filter-input',
                'id': 'id_availability'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('student', None)
        self.research_opportunity = kwargs.pop('research_opportunity', None)
        super().__init__(*args, **kwargs)
        
        # Set choices for select fields with proper labels
        self.fields['time_commitment'].choices = self.TIME_COMMITMENT_CHOICES
        self.fields['availability'].choices = self.AVAILABILITY_CHOICES
        
        # Make fields required with custom error messages
        required_fields = {
            'motivation': {
                'required': 'Motivation is required. Please describe why you want to join this research.'
            },
            'skills_contribution': {
                'required': 'Skills contribution is required. Please tell us what skills you bring.'
            },
            'time_commitment': {
                'required': 'Please select your expected time commitment.'
            },
            'availability': {
                'required': 'Please select your availability period.'
            },
            'resume': {
                'required': 'Please upload your resume/CV.'
            },
            'statement_of_interest': {
                'required': 'Please upload your statement of interest.'
            },
            'academic_transcript': {
                'required': 'Please upload your academic transcript.'
            }
        }
        
        for field_name, error_messages in required_fields.items():
            if field_name in self.fields:
                self.fields[field_name].required = True
                self.fields[field_name].error_messages.update(error_messages)
        
        # Add help texts
        help_texts = {
            'motivation': 'Minimum 50 characters, maximum 2000 characters.',
            'skills_contribution': 'Minimum 30 characters, maximum 1500 characters.',
            'resume': 'PDF, DOC, DOCX (Max 5MB)',
            'statement_of_interest': 'PDF, DOC, DOCX (Max 5MB)',
            'academic_transcript': 'PDF, DOC, DOCX (Max 5MB)',
            'time_commitment': 'Select your expected time commitment',
            'availability': 'Select your availability period'
        }
        
        for field_name, help_text in help_texts.items():
            if field_name in self.fields:
                self.fields[field_name].help_text = help_text
        
        # File field attributes - restrict to PDF, DOC, DOCX only
        for field in ['resume', 'statement_of_interest', 'academic_transcript']:
            if field in self.fields:
                self.fields[field].widget.attrs['accept'] = '.pdf,.doc,.docx'
    
    def clean_motivation(self):
        """Validate motivation field"""
        value = self.cleaned_data.get('motivation', '').strip()
        
        if not value:
            raise ValidationError('Motivation is required.')
        
        if len(value) < 50:
            raise ValidationError(
                f'Motivation must be at least 50 characters. (Current: {len(value)} characters)'
            )
        
        if len(value) > 2000:
            raise ValidationError(
                f'Motivation cannot exceed 2000 characters. (Current: {len(value)} characters)'
            )
        
        return value
    
    def clean_skills_contribution(self):
        """Validate skills contribution field"""
        value = self.cleaned_data.get('skills_contribution', '').strip()
        
        if not value:
            raise ValidationError('Skills contribution is required.')
        
        if len(value) < 30:
            raise ValidationError(
                f'Skills contribution must be at least 30 characters. (Current: {len(value)} characters)'
            )
        
        if len(value) > 1500:
            raise ValidationError(
                f'Skills contribution cannot exceed 1500 characters. (Current: {len(value)} characters)'
            )
        
        return value
    
    def clean_prior_experience(self):
        """Validate prior experience field (optional)"""
        value = self.cleaned_data.get('prior_experience', '').strip()
        
        if value and len(value) > 2000:
            raise ValidationError(
                f'Prior experience cannot exceed 2000 characters. (Current: {len(value)} characters)'
            )
        
        return value
    
    def clean_additional_info(self):
        """Validate additional info field (optional)"""
        value = self.cleaned_data.get('additional_info', '').strip()
        
        if value and len(value) > 2000:
            raise ValidationError(
                f'Additional information cannot exceed 2000 characters. (Current: {len(value)} characters)'
            )
        
        return value
    
    def _validate_file(self, file, field_name, max_size_mb=5):
        """Helper method to validate file uploads - only PDF, DOC, DOCX allowed"""
        if not file:
            return file
        
        # Get file extension
        ext = file.name.split('.')[-1].lower()
        allowed_extensions = ['pdf', 'doc', 'docx']
        
        # Validate file extension - ONLY these are allowed
        if ext not in allowed_extensions:
            raise ValidationError(
                f'Invalid file type for {field_name}. Only PDF, DOC, and DOCX files are allowed. '
                f'(File: {file.name})'
            )
        
        # Validate file size
        max_size = max_size_mb * 1024 * 1024
        if file.size > max_size:
            size_mb = file.size / (1024 * 1024)
            raise ValidationError(
                f'{field_name} file size cannot exceed {max_size_mb}MB. '
                f'(File: {file.name}, Size: {size_mb:.1f}MB)'
            )
        
        return file
    
    def clean_resume(self):
        """Validate resume file - Only PDF, DOC, DOCX allowed"""
        file = self.cleaned_data.get('resume')
        
        # If editing and file already exists, allow it
        if not file and self.instance and self.instance.resume:
            return file
        
        if not file:
            return file
        
        return self._validate_file(file, 'Resume/CV', 5)
    
    def clean_statement_of_interest(self):
        """Validate statement of interest file - Only PDF, DOC, DOCX allowed"""
        file = self.cleaned_data.get('statement_of_interest')
        
        if not file and self.instance and self.instance.statement_of_interest:
            return file
        
        if not file:
            return file
        
        return self._validate_file(file, 'Statement of Interest', 5)
    
    def clean_academic_transcript(self):
        """Validate academic transcript file - Only PDF, DOC, DOCX allowed"""
        file = self.cleaned_data.get('academic_transcript')
        
        if not file and self.instance and self.instance.academic_transcript:
            return file
        
        if not file:
            return file
        
        return self._validate_file(file, 'Academic Transcript', 5)
    
    def clean_time_commitment(self):
        """Validate time commitment selection"""
        value = self.cleaned_data.get('time_commitment')
        
        if not value or value == '':
            raise ValidationError('Please select your expected time commitment.')
        
        valid_choices = ['5-10', '10-15', '15-20', '20+']
        if value not in valid_choices:
            raise ValidationError('Invalid time commitment selection.')
        
        return value
    
    def clean_availability(self):
        """Validate availability selection"""
        value = self.cleaned_data.get('availability')
        
        if not value or value == '':
            raise ValidationError('Please select your availability period.')
        
        valid_choices = ['semester', 'summer', 'winter', 'year-round']
        if value not in valid_choices:
            raise ValidationError('Invalid availability selection.')
        
        return value
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        
        # Check if application deadline has passed
        if self.research_opportunity:
            deadline = self.research_opportunity.application_deadline
            if deadline and deadline < timezone.now().date():
                raise ValidationError(
                    f"Application deadline ({deadline.strftime('%B %d, %Y')}) has passed."
                )
        
        # Check if student already has an active application
        if self.student and self.research_opportunity:
            existing = StudentResearchApplication.objects.filter(
                student=self.student,
                research_opportunity=self.research_opportunity,
                status__in=['submitted', 'under_review']
            )
            
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    'You already have an active application for this research opportunity. '
                    'You cannot apply again.'
                )
        
        return cleaned_data
