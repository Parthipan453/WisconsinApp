from django import forms
from .models import InstructionRequest


class InstructionRequestForm(forms.ModelForm):

    # Override the model field
    # delivery_mode = forms.ChoiceField(
    #     choices=InstructionRequest.DELIVERY_CHOICES,
    #     widget=forms.RadioSelect,
    #     required=True
    # )

    instruction_modes = forms.MultipleChoiceField(
        choices=InstructionRequest.INSTRUCTION_MODE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )

    class Meta:
        model = InstructionRequest

        fields = [
            "department",
            "course",
            "instructor_name",
            "phone",
            "instructor_email",
            "number_of_students",
            "instruction_modes",
            "instruction_support",
            "preferred_library",
            # "preferred_room",
            "preferred_schedule",
            "additional_notes",
            "consent",
        ]

        widgets = {

            "course": forms.Select(attrs={
                "class": "form-control"
            }),


            "instructor_name": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "phone": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "instructor_email": forms.EmailInput(attrs={
                "class": "form-control"
            }),

            "department": forms.Select(attrs={
                "class": "form-control"
            }),


            "number_of_students": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1
            }),

            # "delivery_mode": forms.RadioSelect(),

            "instruction_support": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5
            }),

            "preferred_library": forms.Select(attrs={
                "class": "form-control"
            }),

            # "preferred_room": forms.Select(attrs={
            #     "class": "form-control"
            # }),

            # "preferred_date": forms.DateInput(attrs={
            #     "type": "date",
            #     "class": "form-control"
            # }),

            "preferred_schedule": forms.Textarea(attrs={
            "class": "form-control",
            "rows": 4,
            "placeholder": "Enter three preferred dates/times or an assignment due date."
            }),

            "additional_notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4
            }),

        }

    def clean_consent(self):

        consent = self.cleaned_data.get("consent")

        if not consent:
            raise forms.ValidationError(
                "You must agree before submitting."
            )

        return consent
    

    
import re

def clean_phone(self):
    phone = self.cleaned_data.get("phone")

    if phone:
        phone = phone.strip()

        if not re.fullmatch(r"[0-9+\-\s()]{10,20}", phone):
            raise forms.ValidationError(
                "Enter a valid phone number."
            )

    return phone

def clean_instructor_name(self):
    name = self.cleaned_data.get("instructor_name")

    if not re.fullmatch(r"[A-Za-z .'-]+", name):
        raise forms.ValidationError(
            "Instructor name can contain only letters."
        )

    return name

def clean_number_of_students(self):
    number = self.cleaned_data.get("number_of_students")

    if number <= 0:
        raise forms.ValidationError(
            "Number of students must be greater than zero."
        )

    if number > 500:
        raise forms.ValidationError(
            "Please enter a realistic number of students."
        )

    return number

from datetime import date

def clean_preferred_date(self):
    preferred_date = self.cleaned_data.get("preferred_date")

    if preferred_date < date.today():
        raise forms.ValidationError(
            "Preferred date cannot be in the past."
        )

    return preferred_date

def clean_instruction_support(self):
    text = self.cleaned_data.get("instruction_support")

    if len(text.strip()) < 20:
        raise forms.ValidationError(
            "Please provide more details about your instruction request."
        )

    return text


# help support 
from django import forms
from .models import CirculationInquiry

class CirculationInquiryForm(forms.ModelForm):
    honeypot = forms.CharField(
        required=False,
        widget=forms.HiddenInput
    )

    class Meta:
        model = CirculationInquiry
        fields = ['name', 'email', 'question', 'consent_given']

        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter your name'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter your email'
            }),
            'question': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Enter your question'
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()

        if len(name) < 3:
            raise forms.ValidationError(
                "Name must contain at least 3 characters."
            )

        if not re.fullmatch(r"[A-Za-z\s'-]+", name):
            raise forms.ValidationError(
                "Name can only contain letters, spaces, apostrophes, and hyphens."
            )

        return name
    
    def clean_email(self):
        email = self.cleaned_data.get("email")

        if not email.endswith(".edu"):
            raise forms.ValidationError(
                "Please use a valid educational email address."
            )

        return email

    def clean_honeypot(self):
        if self.cleaned_data.get('honeypot'):
            raise forms.ValidationError("Spam detected.")
        return self.cleaned_data.get('honeypot')


# technical support page


from .models import TechnicalAssistanceInquiry


class TechnicalAssistanceInquiryForm(forms.ModelForm):
    honeypot = forms.CharField(
        required=False,
        widget=forms.HiddenInput
    )

    class Meta:

        model = TechnicalAssistanceInquiry
        fields = [
            "name",
            "email",
            "subject",
            "message",
            "consent_given",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "Enter your name"
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "Enter your email"
            }),
            "subject": forms.TextInput(attrs={
                "placeholder": "Enter subject"
            }),
            "message": forms.Textarea(attrs={
                "rows": 5,
                "placeholder": "Enter your message"
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name")

        if len(name) < 3:
            raise forms.ValidationError(
                "Name must contain at least 3 characters."
            )
        
        if re.search(r"\d", name):
            raise forms.ValidationError(
                "Name cannot contain numbers."
            )

        return name
    
    def clean_email(self):
        email = self.cleaned_data.get("email")

        if not email.endswith(".edu"):
            raise forms.ValidationError(
                "Please use a valid educational email address."
            )

        return email
    
    def clean_subject(self):
        subject = self.cleaned_data.get("subject")

        if len(subject) < 5:
            raise forms.ValidationError(
                "Subject is too short."
            )

        return subject
    
    def clean_message(self):
        message = self.cleaned_data.get("message")

        if len(message.strip()) < 20:
            raise forms.ValidationError(
                "Message should contain at least 20 characters."
            )

        return message

    def clean_honeypot(self):
        if self.cleaned_data.get("honeypot"):
            raise forms.ValidationError("Spam detected.")
        return self.cleaned_data.get("honeypot")
    

# Navina code starts 

from django import forms
from django.core.exceptions import ValidationError
from .models import FineAppeal
import re


class FineAppealForm(forms.ModelForm):

    class Meta:

        model = FineAppeal

        fields = [

            "uwid",

            "applicant_name",

            "applicant_phone",

            "applicant_email",

            "appeal_reason",

            "explanation_statement",

            "consent",

        ]

        widgets = {

            "uwid": forms.TextInput(attrs={

                "class": "form-control",

                "placeholder": "Enter your 10-digit UWID",

                "maxlength": "10",

            }),

            "applicant_name": forms.TextInput(attrs={

                "class": "form-control",

                "placeholder": "Enter your full name",

            }),

            "applicant_phone": forms.TextInput(attrs={

                "class": "form-control",

                "placeholder": "Enter your phone number",

                "maxlength": "10",

            }),

            "applicant_email": forms.EmailInput(attrs={

                "class": "form-control",

                "placeholder": "Enter your email address",

            }),

            "appeal_reason": forms.RadioSelect(),

            "explanation_statement": forms.Textarea(attrs={

                "class": "form-control",

                "rows": 6,

                "placeholder": "Explain why you are requesting an appeal.",

            }),

            "consent": forms.CheckboxInput(attrs={

                "class": "form-check-input",

            }),

        }

    # ======================================================
    # UWID VALIDATION
    # ======================================================

    def clean_uwid(self):

        uwid = self.cleaned_data.get("uwid", "").strip()

        if not uwid:

            raise ValidationError(
                "UWID is required."
            )

        if not uwid.isdigit():

            raise ValidationError(
                "UWID must contain only digits."
            )

        if len(uwid) != 10:

            raise ValidationError(
                "UWID must be exactly 10 digits."
            )

        return uwid

    # ======================================================
    # NAME VALIDATION
    # ======================================================

    def clean_applicant_name(self):

        name = self.cleaned_data.get(
            "applicant_name",
            ""
        ).strip()

        if not name:

            raise ValidationError(
                "Applicant name is required."
            )

        if len(name) < 3:

            raise ValidationError(
                "Name must contain at least 3 characters."
            )

        if len(name) > 100:

            raise ValidationError(
                "Name cannot exceed 100 characters."
            )

        if not re.fullmatch(r"[A-Za-z ]+", name):

            raise ValidationError(
                "Name should contain only letters and spaces."
            )

        return " ".join(word.capitalize() for word in name.split())

    # ======================================================
    # PHONE VALIDATION
    # ======================================================

    def clean_applicant_phone(self):

        phone = self.cleaned_data.get(
            "applicant_phone",
            ""
        )

        phone = phone.replace(" ", "").replace("-", "")

        if not phone:

            raise ValidationError(
                "Phone number is required."
            )

        if not phone.isdigit():

            raise ValidationError(
                "Phone number must contain only digits."
            )

        if len(phone) != 10:

            raise ValidationError(
                "Phone number must be exactly 10 digits."
            )

        return phone

    # ======================================================
    # EMAIL VALIDATION
    # ======================================================

    def clean_applicant_email(self):

        email = self.cleaned_data.get(
            "applicant_email",
            ""
        ).strip().lower()

        if not email:

            raise ValidationError(
                "Email address is required."
            )

        return email

    # ======================================================
    # APPEAL REASON VALIDATION
    # ======================================================

    def clean_appeal_reason(self):

        reason = self.cleaned_data.get(
            "appeal_reason"
        )

        if not reason:

            raise ValidationError(
                "Please select an appeal reason."
            )

        return reason

    # ======================================================
    # EXPLANATION VALIDATION
    # ======================================================

    def clean_explanation_statement(self):

        explanation = self.cleaned_data.get(
            "explanation_statement",
            ""
        ).strip()

        if len(explanation) > 2000:

            raise ValidationError(
                "Explanation cannot exceed 2000 characters."
            )

        return explanation

    # ======================================================
    # CONSENT VALIDATION
    # ======================================================

    def clean_consent(self):

        consent = self.cleaned_data.get("consent")

        if not consent:

            raise ValidationError(
                "You must agree before submitting the form."
            )

        return consent

    # ======================================================
    # FORM LEVEL VALIDATION
    # ======================================================

    def clean(self):

        cleaned_data = super().clean()

        reason = cleaned_data.get("appeal_reason")

        explanation = cleaned_data.get(
            "explanation_statement",
            ""
        ).strip()

        if reason in [

            "MEDICAL",

            "OTHER",

            "QUESTION",

        ]:

            if not explanation:

                self.add_error(

                    "explanation_statement",

                    "Please provide an explanation for your appeal."

                )

        return cleaned_data

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from .models import ContactRequest


class ContactRequestForm(forms.ModelForm):

    accepted_policy = forms.BooleanField(
        required=True,
        label="I understand my information is being used for University Library purposes."
    )

    class Meta:

        model = ContactRequest

        fields = [
            "name",
            "email",
            "affiliation",
            "message",
            "accepted_policy",
        ]

        widgets = {

            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your full name",
                    "maxlength": "150",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your email address",
                }
            ),

            "affiliation": forms.RadioSelect(),

            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Write your message here...",
                    "maxlength": "1000",
                }
            ),

        }

    # =====================================
    # Name Validation
    # =====================================

    def clean_name(self):

        name = self.cleaned_data.get("name", "").strip()

        if not name:
            raise ValidationError("Name is required.")

        if len(name) < 3:
            raise ValidationError("Name must contain at least 3 characters.")

        if len(name) > 150:
            raise ValidationError("Name cannot exceed 150 characters.")

        validator = RegexValidator(
            regex=r'^[A-Za-z ]+$',
            message="Name can contain only letters and spaces."
        )

        validator(name)

        return name

    # =====================================
    # Email Validation
    # =====================================

    def clean_email(self):

        email = self.cleaned_data.get("email", "").strip().lower()

        if not email:
            raise ValidationError("Email address is required.")

        return email

    # =====================================
    # Affiliation Validation
    # =====================================

    def clean_affiliation(self):

        affiliation = self.cleaned_data.get("affiliation")

        if not affiliation:
            raise ValidationError("Please select your affiliation.")

        return affiliation

    # =====================================
    # Message Validation
    # =====================================

    def clean_message(self):

        message = self.cleaned_data.get("message", "").strip()

        if not message:
            raise ValidationError("Message is required.")

        if len(message) < 20:
            raise ValidationError(
                "Message must contain at least 20 characters."
            )

        if len(message) > 1000:
            raise ValidationError(
                "Message cannot exceed 1000 characters."
            )

        return message

    # =====================================
    # Policy Validation
    # =====================================

    def clean_accepted_policy(self):

        accepted = self.cleaned_data.get("accepted_policy")

        if not accepted:
            raise ValidationError(
                "You must accept the privacy statement before submitting."
            )

        return accepted

from django import forms

from .models import RequestPurchase


class RequestPurchaseForm(forms.ModelForm):

    class Meta:

        model = RequestPurchase

        fields = [

            "email",

        ]

        widgets = {

            "email": forms.EmailInput(

                attrs={

                    "class": "form-control",

                    "placeholder": "Enter your @wisc.edu email address",

                    "autocomplete": "email",

                }

            ),

        }

        labels = {

            "email": "Your email address",

        }

        error_messages = {

            "email": {

                "required": "Please enter your email address.",

                "invalid": "Please enter a valid email address.",

            }

        }

    def clean_email(self):

        email = self.cleaned_data.get(
        "email",
        ""
        ).strip().lower()

        if not re.fullmatch(
        r"^[a-zA-Z0-9._%+-]+@wisc\.edu$",
        email
        ):
            raise ValidationError(
            "Please enter a valid @wisc.edu email address."
        )

        return email

from django import forms

from .models import (
    ShelvingFacilityRequest,
    Library,
)
from django import forms
from django.core.exceptions import ValidationError
import re


class ShelvingFacilityRequestForm(forms.ModelForm):

    class Meta:
        model = ShelvingFacilityRequest
        fields = "__all__"

    viewing_library = forms.ModelChoiceField(
        queryset=Library.objects.filter(status="ACTIVE"),
        widget=forms.RadioSelect,
        empty_label=None,
        required=True,
        label="Viewing Location"
    )

    consent = forms.BooleanField(
        required=True,
        label="I agree to the Libraries Privacy Statement."
    )

    class Meta:

        model = ShelvingFacilityRequest

        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "street_address",
            "city",
            "state",
            "zip_code",
            "country",
            "viewing_library",
            "title",
            "call_number",
            "shelving_number",
            "volume",
            "journal_date",
            "other_information",
            "consent",
        ]

        widgets = {

            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your first name",
                }
            ),

            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your last name",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your email address",
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your phone number",
                }
            ),

            "street_address": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Street address",
                }
            ),

            "city": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "City",
                }
            ),

            "state": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "State / Province / Region",
                }
            ),

            "zip_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "ZIP / Postal Code",
                }
            ),

            "country": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Country",
                }
            ),

            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Title of book or journal",
                }
            ),

            "call_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Call number",
                }
            ),

            "shelving_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Shelving number (optional)",
                }
            ),

            "volume": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Journal volume",
                }
            ),

            "journal_date": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Journal date(s)",
                }
            ),

            "other_information": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Enter any additional information...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove ":" after labels
        for field in self.fields.values():
            field.label_suffix = ""

    
    # First Name
    # ==================================================

    def clean_first_name(self):

        first_name = self.cleaned_data.get("first_name", "").strip()

        if not first_name:
            raise ValidationError("First name is required.")

        if len(first_name) < 2:
            raise ValidationError(
                "First name must contain at least 2 characters."
            )

        if not re.fullmatch(r"[A-Za-z ]+", first_name):
            raise ValidationError(
                "First name should contain only letters."
            )

        return first_name


    # ==================================================
    # Last Name
    # ==================================================

    def clean_last_name(self):

        last_name = self.cleaned_data.get("last_name", "").strip()

        if not last_name:
            raise ValidationError("Last name is required.")

        if len(last_name) < 2:
            raise ValidationError(
                "Last name must contain at least 2 characters."
            )

        if not re.fullmatch(r"[A-Za-z ]+", last_name):
            raise ValidationError(
                "Last name should contain only letters."
            )

        return last_name


    # ==================================================
    # Email
    # ==================================================

    def clean_email(self):

        email = self.cleaned_data.get("email", "").strip()

        if email:

            if not re.fullmatch(
                r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
                email
            ):
                raise ValidationError(
                    "Enter a valid email address."
                )

        return email


    # ==================================================
    # Phone
    # ==================================================

    def clean_phone(self):

        phone = self.cleaned_data.get("phone", "").strip()

        if phone:

            if not re.fullmatch(
                r"[0-9()+\-\s]+",
                phone
            ):
                raise ValidationError(
                    "Enter a valid phone number."
                )

            digits = re.sub(r"\D", "", phone)

            if len(digits) < 9:
                raise ValidationError(
                    "Phone number must contain at least 10 digits."
                )

            if len(digits) > 15:
                raise ValidationError(
                    "Phone number cannot exceed 15 digits."
                )

        return phone


    # ==================================================
    # Street Address
    # ==================================================

    def clean_street_address(self):

        address = self.cleaned_data.get(
            "street_address",
            ""
        ).strip()

        if address:

            if len(address) < 5:
                raise ValidationError(
                    "Enter a valid street address."
                )

        return address


    # ==================================================
    # City
    # ==================================================

    def clean_city(self):

        city = self.cleaned_data.get("city", "").strip()

        if city:

            if not re.fullmatch(
                r"[A-Za-z ]+",
                city
            ):
                raise ValidationError(
                    "City should contain only letters."
                )

        return city


    # ==================================================
    # State
    # ==================================================

    def clean_state(self):

        state = self.cleaned_data.get("state", "").strip()

        if state:

            if not re.fullmatch(
                r"[A-Za-z ]+",
                state
            ):
                raise ValidationError(
                    "State should contain only letters."
                )

        return state


    # ==================================================
    # ZIP / Postal Code
    # ==================================================

    def clean_zip_code(self):

        zip_code = self.cleaned_data.get(
        "zip_code",
        ""
        ).strip()

        if zip_code:

        # US ZIP Code validation
            if not re.fullmatch(
            r"^\d{5}(-\d{4})?$",
            zip_code
            ):
                raise ValidationError(
                "Enter a valid US ZIP Code "
                "(e.g., 53706 or 53706-1234)."
            )

            return zip_code


    # ==================================================
    # Country
    # ==================================================

    def clean_country(self):

        country = self.cleaned_data.get(
            "country",
            ""
        ).strip()

        if country:

            if not re.fullmatch(
                r"[A-Za-z ]+",
                country
            ):
                raise ValidationError(
                    "Country should contain only letters."
                )

        return country


    # ==================================================
    # Viewing Library
    # ==================================================

    def clean_viewing_library(self):

        library = self.cleaned_data.get("viewing_library")

        if not library:
            raise ValidationError(
                "Please choose a viewing location."
            )

        return library


    # ==================================================
    # Title
    # ==================================================

    def clean_title(self):

        title = self.cleaned_data.get("title", "").strip()

        if title:

            if len(title) < 2:
                raise ValidationError(
                    "Enter a valid title."
                )

        return title


    # ==================================================
    # Call Number
    # ==================================================

    def clean_call_number(self):

        call_number = self.cleaned_data.get(
            "call_number",
            ""
        ).strip()

        if call_number:

            if len(call_number) < 2:
                raise ValidationError(
                    "Enter a valid call number."
                )

        return call_number


    # ==================================================
    # Shelving Number
    # ==================================================

    def clean_shelving_number(self):

        shelving_number = self.cleaned_data.get(
            "shelving_number",
            ""
        ).strip()

        if shelving_number:

            if len(shelving_number) < 2:
                raise ValidationError(
                    "Enter a valid shelving number."
                )

        return shelving_number


    # ==================================================
    # Volume
    # ==================================================

    def clean_volume(self):

        volume = self.cleaned_data.get(
            "volume",
            ""
        ).strip()

        if volume:

            if len(volume) < 1:
                raise ValidationError(
                    "Enter a valid volume."
                )

        return volume


    # ==================================================
    # Journal Date
    # ==================================================

    def clean_journal_date(self):

        journal_date = self.cleaned_data.get(
            "journal_date",
            ""
        ).strip()

        if journal_date:

            if len(journal_date) < 2:
                raise ValidationError(
                    "Enter a valid journal date."
                )

        return journal_date


    # ==================================================
    # Other Information
    # ==================================================

    def clean_other_information(self):

        other_information = self.cleaned_data.get(
            "other_information",
            ""
        ).strip()

        if other_information:

            if len(other_information) > 1000:
                raise ValidationError(
                    "Maximum 1000 characters are allowed."
                )

        return other_information


    # ==================================================
    # Consent
    # ==================================================

    def clean_consent(self):

        consent = self.cleaned_data.get("consent")

        if not consent:
            raise ValidationError(
                "You must accept the privacy statement."
            )

        return consent


# UWDCC: Submit a Project Proposal form

from .models import ProposalSubmission
import re


class ProposalSubmissionForm(forms.ModelForm):

    class Meta:
        model = ProposalSubmission

        fields = [
            "project_idea",
            "name",
            "phone",
            "email",
            "title",
            "department",
            "institution",
            "institution_director",
            "agree",
        ]

        labels = {
            "project_idea": "Project Idea",
            "name": "Name",
            "phone": "Phone",
            "email": "Email",
            "title": "Title",
            "department": "Department",
            "institution": "Institution",
            "institution_director": "Institution Director / Head",
            "agree": "I understand my information is being used for University of Wisconsin–Madison Libraries purposes.",
        }

        help_texts = {
            "project_idea": "Please briefly describe the content you wish to digitize and the purpose of this project.",
        }

        widgets = {
            "project_idea": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Briefly describe your project...",
                    "class": "form-control",
                }
            ),

            "name": forms.TextInput(
                attrs={
                    "placeholder": "Enter your full name",
                    "class": "form-control",
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "placeholder": "Enter your phone number",
                    "class": "form-control",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Enter your email address",
                    "class": "form-control",
                }
            ),

            "title": forms.TextInput(
                attrs={
                    "placeholder": "Enter your title",
                    "class": "form-control",
                }
            ),

            "department": forms.TextInput(
                attrs={
                    "placeholder": "Enter your department",
                    "class": "form-control",
                }
            ),

            "institution": forms.TextInput(
                attrs={
                    "placeholder": "Enter your institution",
                    "class": "form-control",
                }
            ),

            "institution_director": forms.TextInput(
                attrs={
                    "placeholder": "Institution Director / Head",
                    "class": "form-control",
                }
            ),

            "agree": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    # -------------------------
    # Name Validation
    # -------------------------

    def clean_name(self):
        name = self.cleaned_data.get("name")

        if len(name.strip()) < 3:
            raise forms.ValidationError(
                "Name must contain at least 3 characters."
            )

        if not re.fullmatch(r"[A-Za-z .'-]+", name):
            raise forms.ValidationError(
                "Name should contain only letters and spaces."
            )

        return name

    # -------------------------
    # Phone Validation
    # -------------------------

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")

        digits = "".join(filter(str.isdigit, phone))

        if len(digits) < 9 or len(digits) > 15:
            raise forms.ValidationError(
                "Phone number must contain between 9 and 15 digits."
            )

        return phone

    

    # -------------------------
    # Consent Checkbox Validation
    # -------------------------

    def clean_agree(self):
        agree = self.cleaned_data.get("agree")

        if not agree:
            raise forms.ValidationError(
                "You must agree before submitting the form."
            )

        return agree


    # -------------------------
    # Project Idea Validation
    # -------------------------

    def clean_project_idea(self):
        project_idea = self.cleaned_data.get("project_idea", "").strip()

        if len(project_idea) < 20:
            raise forms.ValidationError(
                "Project idea must contain at least 20 characters."
            )

        return project_idea


    # -------------------------
    # Email Validation
    # -------------------------

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()

        if not email:
            raise forms.ValidationError(
                "Email is required."
            )

        return email


    # -------------------------
    # Title Validation
    # -------------------------

    def clean_title(self):
        title = self.cleaned_data.get("title", "").strip()

        if title:
            if len(title) < 2:
                raise forms.ValidationError(
                    "Title must contain at least 2 characters."
                )

            if not re.fullmatch(r"[A-Za-z .,'&()-]+", title):
                raise forms.ValidationError(
                    "Title contains invalid characters."
                )

        return title


    # -------------------------
    # Department Validation
    # -------------------------

    def clean_department(self):
        department = self.cleaned_data.get("department", "").strip()

        if department:
            if len(department) < 2:
                raise forms.ValidationError(
                    "Department must contain at least 2 characters."
                )

            if not re.fullmatch(r"[A-Za-z0-9 .,'&()-]+", department):
                raise forms.ValidationError(
                    "Department contains invalid characters."
                )

        return department


    # -------------------------
    # Institution Validation
    # -------------------------

    def clean_institution(self):
        institution = self.cleaned_data.get("institution", "").strip()

        if institution:
            if len(institution) < 2:
                raise forms.ValidationError(
                    "Institution must contain at least 2 characters."
                )

            if not re.fullmatch(r"[A-Za-z .,'&()-]+", institution):
                raise forms.ValidationError(
                    "Institution contains invalid characters."
                )

        return institution


    # -------------------------
    # Institution Director Validation
    # -------------------------

    def clean_institution_director(self):
        director = self.cleaned_data.get(
            "institution_director",
            ""
        ).strip()

        if director:
            if len(director) < 3:
                raise forms.ValidationError(
                    "Institution Director / Head name must contain at least 3 characters."
                )

            if not re.fullmatch(r"[A-Za-z .'-]+", director):
                raise forms.ValidationError(
                    "Institution Director / Head name should contain only letters and spaces."
                )

        return director
    


#  contact the UWDCC.form

from .models import DigitalCollectionsContact


class DigitalCollectionsContactForm(forms.ModelForm):

    class Meta:

        model = DigitalCollectionsContact

        fields = [
            "name",
            "email",
            "subject",
            "question",
        ]

        labels = {
            "name": "Your Name",
            "email": "Your Email",
            "subject": "Subject",
            "question": "Question / Comment",
        }

        widgets = {

            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your full name",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your email address",
                }
            ),

            "subject": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter subject (optional)",
                }
            ),

            "question": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Write your question or comment...",
                }
            ),
        }

    # -------------------------
    # Name Validation
    # -------------------------

    def clean_name(self):

        name = self.cleaned_data["name"].strip()

        if len(name) < 3:
            raise forms.ValidationError(
                "Name must contain at least 3 characters."
            )

        if not all(ch.isalpha() or ch.isspace() for ch in name):
            raise forms.ValidationError(
                "Name should contain only letters and spaces."
            )

        return name

    # -------------------------
    # Subject Validation
    # -------------------------

    def clean_subject(self):

        subject = self.cleaned_data.get("subject", "").strip()

        return subject

    # -------------------------
    # Question Validation
    # -------------------------

    def clean_question(self):

        question = self.cleaned_data["question"].strip()

        if len(question) < 10:
            raise forms.ValidationError(
                "Please enter at least 10 characters."
            )

        return question


