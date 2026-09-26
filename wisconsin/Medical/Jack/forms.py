from django import forms
from Medical.models import *
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, date

############ MEDICAL DEPARTMENT FORM START ##############

class MedicalDepartmentForm(forms.ModelForm):

    class Meta:

        model = MedicalDepartment

        fields = [
            'department_code',
            'department_name',
            'short_name',
            'department_type',
            'description',
            'location',
            'phone',
            'email',
            'opening_time',
            'closing_time',
            'is_emergency',
            'is_active',
        ]

        widgets = {
            'department_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., CARD',
                'required': True
            }),
            'department_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Cardiology',
                'required': True,
                'pattern': '[A-Za-z ]+',
                'oninput': "this.value=this.value.replace(/[^A-Za-z ]/g,'')"
            }),
            'short_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Cardio',
                'pattern': '[A-Za-z ]+',
                'oninput': "this.value=this.value.replace(/[^A-Za-z ]/g,'')"
            }),
            'department_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Specialized Care',
                'required': True,
                'pattern': '[A-Za-z ]+',
                'oninput': "this.value=this.value.replace(/[^A-Za-z ]/g,'')"
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of the department...'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Medical Tower, 3rd Floor',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., +1 555 123 4567',
                'required': True,
                'maxlength': '15',
                'pattern': r'^\+?[0-9 ]+$',
                'oninput': "this.value=this.value.replace(/[^0-9+ ]/g,'')"
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., cardiology@hospital.com',
                'required': True
            }),
            'opening_time': forms.TimeInput(attrs={
                'id': 'opening_time',
                'class': 'form-control',
                'type': 'time',
                'required': True
            }),
            'closing_time': forms.TimeInput(attrs={
                'id': 'closing_time',
                'class': 'form-control',
                'type': 'time',
                'required': True
            }),
            'is_emergency': forms.CheckboxInput(attrs={
                'id': 'is_emergency',
                'class': 'dept-form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'id': 'is_active',
                'class': 'dept-form-check-input'
            })
        }

        labels = {
            'department_code': 'Department Code',
            'department_name': 'Department Name',
            'short_name': 'Short Name',
            'department_type': 'Department Type',
            'description': 'Description',
            'location': 'Location',
            'phone': 'Phone Number',
            'email': 'Email Address',
            'opening_time': 'Opening Time',
            'closing_time': 'Closing Time',
            'is_emergency': 'Emergency Department',
            'is_active': 'Active Department'
        }
        help_texts = {
            'department_code': 'Unique code for the department',
            'short_name': 'Abbreviated name e.g., ER, Cardio',
            'department_type': 'e.g., Specialized Care, Emergency, Diagnostic',
            'location': 'Building and floor number',
            'phone': 'Contact number with country code',
            'opening_time': 'When does the department open?',
            'closing_time': 'When does the department close?',
        }
        error_messages = {
            'department_code': {
                'required': 'Department code is required',
                'unique': 'This department code already exists'
            },
            'department_name': {
                'required': 'Department name is required',
                'unique': 'This department name already exists'
            },
            'department_type': {
                'required': 'Department type is required'
            },
            'location': {
                'required': 'Location is required'
            },
            'phone': {
                'required': 'Phone No is required'
            },
            'email': {
                'required': 'Email Address is required'
            },
            'opening_time': {
                'required': 'Opening time is required'
            },
            'closing_time': {
                'required': 'Closing time is required'
            }
        }

    def clean(self):
        cleaned_data = super().clean()
        opening_time = cleaned_data.get('opening_time')
        closing_time = cleaned_data.get('closing_time')
        is_emergency = cleaned_data.get('is_emergency')

        if is_emergency:
            cleaned_data['opening_time'] = '00:00'
            cleaned_data['closing_time'] = '23:59'
            return cleaned_data

        if opening_time and closing_time:
            if opening_time >= closing_time:
                raise forms.ValidationError(
                    'Opening time must be before closing time'
                )

        return cleaned_data
    
############ MEDICAL DEPARTMENT FORM END ##############

class LeaveApplicationForm(forms.ModelForm):
    
    permission_start_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'hidden'}),
        input_formats=['%H:%M']
    )
    permission_end_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'type': 'hidden'}),
        input_formats=['%H:%M']
    )

    class Meta:
        model = MedicalStaffLeave
        fields = [
            'leave_type',
            'start_date',
            'end_date',
            'reason',
            'permission_start_time',
            'permission_end_time',
        ]

        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'hidden'}),
            'end_date': forms.DateInput(attrs={'type': 'hidden'}),
            'leave_type': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'maxlength': '500',
                'placeholder': 'Briefly explain why you\'re requesting this leave'
            }),
        }
        labels = {
            'leave_type': 'Leave Type',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'reason': 'Reason',
        }
        error_messages = {
            'leave_type': {
                'required': 'Please select a leave type.',
            },
            'start_date': {
                'required': 'Please select a start date.',
            },
            'end_date': {
                'required': 'Please select an end date.',
            },
            'reason': {
                'required': 'Please provide a reason for your leave request.',
                'max_length': 'Reason cannot exceed 500 characters.',
            },
        }

    def clean(self):
        cleaned_data = super().clean()
        leave_type = cleaned_data.get('leave_type')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        permission_start_time = cleaned_data.get('permission_start_time')
        permission_end_time = cleaned_data.get('permission_end_time')
        
        if start_date and end_date:
            if end_date < start_date:
                self.add_error('end_date', 'End date must be after start date.')
        
        today = date.today()
        if start_date and start_date < today:
            self.add_error('start_date', 'Start date cannot be in the past.')
        
        if end_date and end_date < today:
            self.add_error('end_date', 'End date cannot be in the past.')
        
        if leave_type == 'PERMISSION':
            
            if not permission_start_time:
                self.add_error('permission_start_time', 'Please select a start time for permission leave.')
            
            if not permission_end_time:
                self.add_error('permission_end_time', 'Please select an end time for permission leave.')
            
            if permission_start_time and permission_end_time:
                start_minutes = permission_start_time.hour * 60 + permission_start_time.minute
                end_minutes = permission_end_time.hour * 60 + permission_end_time.minute
                
                if end_minutes <= start_minutes:
                    self.add_error('permission_end_time', 'End time must be after the start time.')
                
                duration_hours = (end_minutes - start_minutes) / 60
                if duration_hours > 4:
                    self.add_error('permission_end_time', 
                        f'Permission leave cannot exceed 4 hours. Current duration: {duration_hours:.1f} hours.')
                
                now = datetime.now().time()
                if start_date == today:
                    if permission_start_time < now:
                        self.add_error('permission_start_time', 
                            'Start time cannot be in the past. Please select a future time.')
                    if permission_end_time < now:
                        self.add_error('permission_end_time', 
                            'End time cannot be in the past. Please select a future time.')
        
        if leave_type and leave_type != 'PERMISSION':
            if not end_date:
                self.add_error('end_date', 'Please select an end date.')
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if instance.leave_type == 'PERMISSION':
            instance.permission_start_time = self.cleaned_data.get('permission_start_time')
            instance.permission_end_time = self.cleaned_data.get('permission_end_time')
            instance.end_date = instance.start_date
        else:
            instance.permission_start_time = None
            instance.permission_end_time = None
        
        instance.status = 'PENDING'
        
        if commit:
            instance.save()
        
        return instance