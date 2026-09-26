""" Dominic Code """
import re
from django import forms
from Admin.models import User

class AdministratorSetupForm(forms.Form):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(
        attrs={
            "id": "first_name",
            "placeholder": "First name",
            "autofocus": True,
            "class": "setup-form__input",
        }
    ), error_messages={"required": "First name is required."})
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(
        attrs={
            "id": "last_name",
            "placeholder": "Last name",
            "class": "setup-form__input",
        }
    ), error_messages={"required": "Last name is required."})
    username = forms.CharField(max_length=150, widget=forms.TextInput(
        attrs={
            "id": "username",
            "placeholder": "Username",
            "class": "setup-form__input",
            "autocomplete": "off",
        }
    ), error_messages={"required": "Username is required."})
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={
            "id": "email",
            "placeholder": "Email",
            "class": "setup-form__input",
        }
    ), error_messages={
        "required": "Email address is required.",
        "invalid": "Enter a valid email address.",
        })
    mobile_number = forms.CharField(max_length=20, widget=forms.TextInput(
        attrs={
            "id": "mobile_number",
            "placeholder": "Mobile number",
            "class": "setup-form__input",
        }
    ), error_messages={"required": "Mobile number is required."})
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            "id": "password",
            "placeholder": "Password",
            "class": "setup-form__input",
            "autocomplete": "new-password",
        }
    ), error_messages={"required": "Password is required."})
    confirm_password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            "id": "confirm_password",
            "placeholder": "Re-enter password",
            "class": "setup-form__input",
            "autocomplete": "new-password",
        }
    ), error_messages={"required": "Please confirm your password."})
    
    def clean_first_name(self):
        value = self.cleaned_data["first_name"].strip()
        if not value.replace(" ", "").isalpha():
            raise forms.ValidationError("First name may only contain letters.")
        return value.title()
    
    def clean_last_name(self):
        value = self.cleaned_data["last_name"].strip()
        if not value.replace(" ", "").isalpha():
            raise forms.ValidationError("Last name may only contain letters.")
        return value.title()
    
    def clean_username(self):
        value = self.cleaned_data["username"].strip().lower()
        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise forms.ValidationError("Username may only contain letters, digits, and underscores.")
        
        if User.objects.filter(username = value).exists():
            raise forms.ValidationError("This username is already taken.")
        return value
    
    def clean_email(self):
        value = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email = value).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return value
    
    def clean_mobile_number(self):
        value = self.cleaned_data["mobile_number"].strip()
        digits_only = re.sub(r"[\s\-\(\)\+]", "", value)
        if not digits_only.isdigit() or not (7 <= len(digits_only) <= 15):
            raise forms.ValidationError("Enter a valid mobile number (7-15 digits).")
        return value
    
    def clean_password(self):
        password = self.cleaned_data["password"]
        errors = []
        if len(password) < 8:
            errors.append("atleast 8 characters")
        if not re.search(r"[A-Z]", password):
            errors.append("one uppercase letter")
        if not re.search(r"[0-9]", password):
            errors.append("one number")
        if not re.search(r"[^A-Za-z0-9]", password):
            errors.append("one special character")
        if errors:
            raise forms.ValidationError(f"Password must contain {', '.join(errors)}.")
        return password
    
    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirm = cleaned.get("confirm_password")
        if password and confirm and password != confirm:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned