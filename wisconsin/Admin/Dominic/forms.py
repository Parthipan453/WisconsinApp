from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Announcement

User = get_user_model()

# Password Reset
class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your registered email",
                "autofocus": True,
            }
        )
    )

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

class OTPVerifyForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control otp-input",
                "placeholder": "------",
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
                "autofocus": True,
            }
        ),
    )

    def clean_otp(self):
        otp = self.cleaned_data["otp"].strip()
        if not otp.isdigit():
            raise forms.ValidationError("OTP must contain digits only.")
        return otp

class SetNewPasswordForm(forms.Form):
    new_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "New password", "autofocus": True}
        )
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirm new password"}
        )
    )

    def clean_new_password(self):
        password = self.cleaned_data["new_password"]
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password")
        p2 = cleaned_data.get("confirm_password")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("The two password fields did not match.")
        return cleaned_data
    
# Announcement
class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = [
            'title', 'message', 'visibility', 'priority',
            'is_pinned', 'is_active', 'start_date', 'end_date',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'announce-input',
                'placeholder': 'e.g. Scheduled maintenance on Sunday',
            }),
            'message': forms.Textarea(attrs={
                'class': 'announce-textarea', 'rows': 5,
                'placeholder': 'Write the announcement content...',
            }),
            'visibility': forms.RadioSelect(),
            'priority': forms.RadioSelect(),
            'is_pinned': forms.CheckboxInput(attrs={'class': 'announce-toggle-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'announce-toggle-input'}),
            'start_date': forms.DateTimeInput(
                attrs={'class': 'announce-input', 'type': 'datetime-local'}
            ),
            'end_date': forms.DateTimeInput(
                attrs={'class': 'announce-input', 'type': 'datetime-local'}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError('End date must be after the start date.')
        return cleaned_data