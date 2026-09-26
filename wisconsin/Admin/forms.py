
# /* kali's  code  */

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, UserRole
import re


class UserCreateForm(forms.ModelForm):  
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"placeholder": "student@university.edu"}),
    )
    username = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "sample_name"}),
    )
    confirm_mobile = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "Confirm mobile number"}),
    )

    class Meta: 
        model = User
        fields = [
            # Identity
            "username",
            "email",
            "university_id",
            # Personal
            "first_name",
            "middle_name",
            "last_name",
            "date_of_birth",
            "gender",
            "profile_photo",
            "ssn_number",
            # Contact
            "mobile_number",
            # Role
            "is_student",
            "is_faculty",
            "is_admin",
            "is_staff",
            # Status
            "account_status",
            "role",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "sample_name"}),
            "email": forms.EmailInput(attrs={"placeholder": "student@university.edu"}),
            "university_id": forms.TextInput(attrs={"placeholder": "e.g. UNI2024001"}),
            "first_name": forms.TextInput(attrs={"placeholder": "First name"}),
            "middle_name": forms.TextInput(attrs={"placeholder": "Middle name (optional)"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Last name"}),
            "date_of_birth": forms.DateInput(attrs={"type": "date","max": "9999-12-31"}),
            "gender": forms.Select(),
            "mobile_number": forms.TextInput(attrs={"placeholder": "+91 9876543210"}),
            "ssn_number": forms.TextInput(attrs={"placeholder": "xxx-xx-xxxx"}),
            "account_status": forms.Select(),
            "role": forms.Select(),
        }

   

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long.")
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            raise ValidationError("Username may only contain letters, numbers, and underscores.")
        # if User.objects.filter(username=username).exists():
        #     raise ValidationError("This username is already taken.")

        qs = User.objects.filter(username=username)

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError(
                "This username is already taken."
            )
        return username

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        # if User.objects.filter(email=email).exists():
        #     raise ValidationError("A user with this email already exists.")

        qs = User.objects.filter(email=email)

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError(
                "A user with this email already exists."
            )
        return email


    def clean_university_id(self):
        uid = (self.cleaned_data.get("university_id") or "").strip()

        # Treat "None" as empty
        if uid.lower() == "none":
            uid = ""

        if not uid:
            return None

        qs = User.objects.filter(university_id=uid)

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError("This university ID is already registered.")

        return uid

    def clean_first_name(self):
        name = (self.cleaned_data.get("first_name") or "").strip()
        if not name:
            raise ValidationError("First name is required.")
        if not re.match(r"^[a-zA-Z\s\-']+$", name):
            raise ValidationError("First name may only contain letters, spaces, hyphens, or apostrophes.")
        return name.title()

    def clean_last_name(self):
        name = (self.cleaned_data.get("last_name") or "").strip()
        if not name:
            raise ValidationError("Last name is required.")
        if not re.match(r"^[a-zA-Z\s\-']+$", name):
            raise ValidationError("Last name may only contain letters, spaces, hyphens, or apostrophes.")
        return name.title()



    def clean_middle_name(self):
        name = self.cleaned_data.get("middle_name")

        if not name:
            return ""

        name = name.strip()

        if not re.match(r"^[a-zA-Z\s\-']+$", name):
            raise ValidationError(
                "Middle name may only contain letters, spaces, hyphens, or apostrophes."
            )

        return name.title()
    

    # Jack Code Start's

    def clean_ssn_number(self):
        ssn = self.cleaned_data.get('ssn_number')

        if not ssn:
            return ssn

        ssn = ssn.strip()

        if not re.fullmatch(r'\d{3}-\d{2}-\d{4}', ssn):
            raise forms.ValidationError(
                'Enter a valid SSN in the format XXX-XX-XXXX.'
            )

        area, group, serial = ssn.split('-')

        if area == '000' or group == '00' or serial == '0000':
            raise forms.ValidationError(
                'Enter a valid SSN number.'
            )

        queryset = User.objects.filter(ssn_number=ssn)

        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise forms.ValidationError(
                'This SSN number already exists.'
            )

        return ssn

    # Jack Code End's

    # /* ***************************************************** Arun code *************************************************** */

    def clean_mobile_number(self):
        mobile = (self.cleaned_data.get("mobile_number") or "").strip()
        if not mobile:
            raise ValidationError("Mobile number is required.")
        digits = re.sub(r"[\s\-\+\(\)]", "", mobile)
        if not digits.isdigit():
            raise ValidationError("Mobile number must contain only digits (spaces, +, - allowed).")
        if len(digits) < 10 or len(digits) > 15:
            raise ValidationError("Mobile number must be between 10 and 15 digits.")

        qs = User.objects.filter(mobile_number=mobile)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("This mobile number is already registered.")

        return mobile

    # /* ***************************************************** Arun code *************************************************** */

    def clean_confirm_mobile(self):
        mobile = self.cleaned_data.get("mobile_number", "")
        confirm = self.cleaned_data.get("confirm_mobile", "")
        if mobile and confirm and mobile != confirm:
            raise ValidationError("Mobile numbers do not match.")
        return confirm

    def clean_date_of_birth(self):
        from datetime import date
        dob = self.cleaned_data.get("date_of_birth")
        if dob:
            today = date.today()
            age = (today - dob).days // 365
            if dob > today:
                raise ValidationError("Date of birth cannot be in the future.")
            if age < 10:
                raise ValidationError("User must be at least 10 years old.")
            if age > 120:
                raise ValidationError("Please enter a valid date of birth.")
        return dob

    def clean_profile_photo(self):
        photo = self.cleaned_data.get("profile_photo")
        if photo:
            # Max 5 MB
            if photo.size > 5 * 1024 * 1024:
                raise ValidationError("Profile photo must be smaller than 5 MB.")
            allowed = ["image/jpeg", "image/png", "image/webp", "image/gif"]
            if hasattr(photo, "content_type") and photo.content_type not in allowed:
                raise ValidationError("Only JPEG, PNG, WebP, or GIF images are allowed.")
        return photo

  

    def __init__(self, *args, **kwargs):
        self.is_edit = kwargs.pop("is_edit", False)

        super().__init__(*args, **kwargs)

        self.fields["university_id"].required = False
        self.fields["role"].queryset = UserRole.objects.all()
        self.fields["role"].empty_label = "Select Role"

        if self.is_edit:
            self.fields.pop("password", None)

        else:
            self.fields["account_status"].choices = [
                ("", "Select Status"),
                ("ACTIVE", "Active"),
                ("PENDING", "Pending"),
            ]
            self.fields["account_status"].initial = ""
            self.fields["account_status"].required = True
    

    def save(self, commit=True, is_edit=False):
        user = super().save(commit=False)

        if not is_edit:
            user.email = self.cleaned_data["email"]

            # Auto-generate password: firstname + last 4 digits of mobile
            first = self.cleaned_data.get("first_name", "user").lower()
            mobile = re.sub(r"\D", "", self.cleaned_data.get("mobile_number", "0000"))
            password = f"{first}{mobile[-4:]}"
            user.set_password(password)
            if commit:
                user.save()
            return user, password

        if commit:
            user.save()
        return user 