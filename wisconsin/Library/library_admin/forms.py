from django import forms
from django.core.exceptions import ValidationError
from datetime import date
import re

from Library.models import LibraryResource


class LibraryResourceForm(forms.ModelForm):

    class Meta:

        model = LibraryResource

        fields = [

            "library",

            "category",

            "resource_type",

            "title",

            "isbn_issn",

            "author",

            "publisher",

            "publication_year",

            "edition",

            "language",

            "subject",

            "total_copies",

            "available_copies",

            "shelf_location",

            "status",

            "cover_image",

        ]

        widgets = {

            "library": forms.Select(
             attrs={
                "class": "form-select library-choice"
                }
            ),

            "category": forms.Select(
                attrs={
                    "class": "form-select library-choice"
                }
            ),

            "resource_type": forms.Select(
                attrs={
                    "class": "form-select library-choice"
                }
            ),

            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter Book Title"
                }
            ),

            "isbn_issn": forms.TextInput(
                attrs={
                   "class": "form-control",
                   "placeholder": "9781234567890",
                   "maxlength": "13",
                   "minlength": "13",
                   "inputmode": "numeric",
                   "pattern": "[0-9]{13}",
                }
            ),

            "author": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter Author Name"
                }
            ),

            "publisher": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Publisher"
                }
            ),

            "publication_year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "2026"
                }
            ),

            "edition": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "First Edition"
                }
            ),

            "language": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "English"
                }
            ),

            "subject": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Computer Science"
                }
            ),

            "total_copies": forms.NumberInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "available_copies": forms.NumberInput(
                attrs={
                    "class": "form-control"
                }
            ),

            "shelf_location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "A-102"
                }
            ),

            "status": forms.Select(
                attrs={
                    "class": "form-select library-choice"
                }
            ),

        }

    def clean_title(self):

        title = self.cleaned_data.get(
        "title",
        ""
        ).strip()

        if not title:

           raise ValidationError(
            "Book title is required."
        )

        if len(title) < 2:

           raise ValidationError(
            "Book title must contain at least 2 characters."
        )

        if title.isdigit():

           raise ValidationError(
            "Book title cannot contain only numbers."
        )

        return title


    def clean_author(self):

        author = self.cleaned_data.get(
        "author",
        ""
        ).strip()

        if not author:

           raise ValidationError(
            "Author name is required."
        )

        if len(author) < 2:

           raise ValidationError(
            "Author name must contain at least 2 characters."
        )

        if not re.match(r"^[A-Za-z .'-]+$", author):

           raise ValidationError(
            "Author name contains invalid characters."
        )

        return author

    def clean_library(self):

        library = self.cleaned_data.get("library")

        if not library:

           raise ValidationError(
            "Please select a library."
        )

        return library

    def clean_category(self):

        category = self.cleaned_data.get("category")

        if not category:

           raise ValidationError(
            "Please select a category."
        )

        return category

    def clean_resource_type(self):

        resource = self.cleaned_data.get("resource_type")

        if not resource:

           raise ValidationError(
            "Please select a resource type."
        )

        return resource

    def clean_publisher(self):

        publisher = self.cleaned_data.get(
        "publisher",
        ""
        ).strip()

        if not publisher:

           raise ValidationError(
            "Publisher is required."
        )

        if len(publisher) < 2:

           raise ValidationError(
            "Publisher name is too short."
        )

        return publisher

    def clean_edition(self):

        edition = self.cleaned_data.get(
        "edition",
        ""
        ).strip()

        if edition and len(edition) > 50:

            raise ValidationError(
            "Edition cannot exceed 50 characters."
        )

        return edition

    def clean_subject(self):

        subject = self.cleaned_data.get(
        "subject",
        ""
        ).strip()

        if not subject:

           raise ValidationError(
            "Subject is required."
        )

        return subject

    def clean_shelf_location(self):

        shelf = self.cleaned_data.get(
        "shelf_location",
        ""
        ).strip()

        if not shelf:

           raise ValidationError(
            "Shelf location is required."
        )

        if len(shelf) > 30:

           raise ValidationError(
            "Shelf location is too long."
        )

        return shelf

    def clean_status(self):

        status = self.cleaned_data.get("status")

        if not status:

           raise ValidationError(
            "Please select a status."
        )

        return status

    def clean_isbn_issn(self):

        isbn = self.cleaned_data.get(
        "isbn_issn",
        ""
        ).replace("-", "").strip()

        if not isbn:

           raise ValidationError(
            "ISBN is required."
        )

        if not isbn.isdigit():

            raise ValidationError(
            "ISBN must contain numbers only."
        )

        if len(isbn) not in [10, 13]:

            raise ValidationError(
            "ISBN must contain 10 or 13 digits."
        )

        if LibraryResource.objects.filter(
        isbn_issn=isbn
        ).exists():

            raise ValidationError(
            "A book with this ISBN already exists."
        )

        return isbn


    def clean_publication_year(self):

        year = self.cleaned_data.get(
            "publication_year"
        )

        current_year = date.today().year

        if year is None:
           raise ValidationError(
        "Publication year is required."
        )

        current_year = date.today().year

        if year < 1800:
            raise ValidationError(
        "Enter a valid publication year."
        )

        if year > current_year:
            raise ValidationError(
        "Publication year cannot be in the future."
        )

        return year


    def clean_language(self):

        language = self.cleaned_data.get(
        "language",
        ""
        ).strip()

        if not language:

           raise ValidationError(
            "Language is required."
        )

        if len(language) < 2:

           raise ValidationError(
            "Enter a valid language."
        )

        if not re.match(r"^[A-Za-z ]+$", language):

            raise ValidationError(
            "Language can contain only letters."
        )

        return language


    def clean_total_copies(self):
        total = self.cleaned_data.get("total_copies")

        if total is None:
            raise ValidationError("Total copies is required.")

        if total <= 0:
           raise ValidationError(
            "Total copies must be greater than zero."
        )

        return total


    def clean_available_copies(self):

        available = self.cleaned_data.get("available_copies")

        if available is None:
            raise ValidationError(
            "Available copies is required."
        )

        if available < 0:
            raise ValidationError(
            "Available copies cannot be negative."
        )

        return available


    def clean(self):

        cleaned_data = super().clean()

        total = cleaned_data.get(
            "total_copies"
        )

        available = cleaned_data.get(
            "available_copies"
        )

        if total and available:

            if available > total:

                self.add_error(

                    "available_copies",

                    "Available copies cannot be greater than total copies."

                )

        return cleaned_data



import re

from django import forms
from django.core.exceptions import ValidationError

from Library.models import Library


class LibraryForm(forms.ModelForm):

    # =====================================================
    # LIBRARY SERVICES
    # =====================================================

    SERVICE_CHOICES = [
        ("24_HOUR_SERVICE", "24-hour service"),
        ("AV_EQUIPMENT", "AV equipment for check out"),
        ("BOOK_SCANNER", "Book scanner"),
        ("CAFE_VENDING", "Café/Vending area"),
        ("COLOR_COPIER", "Color copier"),
        ("COLOR_LASER_PRINTER", "Color laser printer"),
        ("COMPUTER_LAB", "Computer lab"),
        ("GENDER_INCLUSIVE_RESTROOM", "Gender-inclusive restroom"),
        ("LACTATION_ROOM", "Lactation room"),
        ("LAPTOPS_CHECKOUT", "Laptops for check out"),
        ("LOCKERS", "Lockers"),
        ("MICROFORM_PRINTER", "Microform printer"),
        ("OPEN_RETURN", "Open return"),
        ("PHOTOCOPIER", "Photocopier"),
        ("PICKUP_BOOKS_APPOINTMENT", "Pickup books by appointment"),
        ("POSTER_PRINTING", "Poster printing"),
        ("REFLECTION_SPACE", "Reflection space"),
        ("RESERVABLE_STUDY_ROOMS", "Reservable study rooms"),
        ("SILENT_STUDY_SPACES", "Silent study spaces"),
    ]

    services = forms.MultipleChoiceField(
        choices=SERVICE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={
                "class": "library-services-checkboxes"
            }
        )
    )

    # =====================================================
    # DAY CHOICES
    # =====================================================

    DAY_CHOICES = [
        ("", "Select day"),
        ("monday", "Monday"),
        ("tuesday", "Tuesday"),
        ("wednesday", "Wednesday"),
        ("thursday", "Thursday"),
        ("friday", "Friday"),
        ("saturday", "Saturday"),
        ("sunday", "Sunday"),
    ]

    # =====================================================
    # TIME CHOICES
    # =====================================================

    TIME_CHOICES = [
        ("", "Select time"),

        ("06:00", "6:00 AM"),
        ("06:30", "6:30 AM"),

        ("07:00", "7:00 AM"),
        ("07:30", "7:30 AM"),

        ("08:00", "8:00 AM"),
        ("08:30", "8:30 AM"),

        ("09:00", "9:00 AM"),
        ("09:30", "9:30 AM"),

        ("10:00", "10:00 AM"),
        ("10:30", "10:30 AM"),

        ("11:00", "11:00 AM"),
        ("11:30", "11:30 AM"),

        ("12:00", "12:00 PM"),
        ("12:30", "12:30 PM"),

        ("13:00", "1:00 PM"),
        ("13:30", "1:30 PM"),

        ("14:00", "2:00 PM"),
        ("14:30", "2:30 PM"),

        ("15:00", "3:00 PM"),
        ("15:30", "3:30 PM"),

        ("16:00", "4:00 PM"),
        ("16:30", "4:30 PM"),

        ("17:00", "5:00 PM"),
        ("17:30", "5:30 PM"),

        ("18:00", "6:00 PM"),
        ("18:30", "6:30 PM"),

        ("19:00", "7:00 PM"),
        ("19:30", "7:30 PM"),

        ("20:00", "8:00 PM"),
        ("20:30", "8:30 PM"),

        ("21:00", "9:00 PM"),
        ("21:30", "9:30 PM"),

        ("22:00", "10:00 PM"),
        ("22:30", "10:30 PM"),

        ("23:00", "11:00 PM"),
    ]

    # =====================================================
    # OPEN / CLOSED CHOICES
    # =====================================================

    HOURS_STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("CLOSED", "Closed"),
    ]

    # =====================================================
    # MODEL FIELDS
    # =====================================================

    class Meta:

        model = Library

        fields = [
            "library_name",
            "library_code",
            "building",
            "email",
            "phone",
            "website",
            "address",
            "description",
            "image",
            "status",
            "services",
        ]

        widgets = {

            "library_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Memorial Library",
                }
            ),

            "library_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "MEM001",
                }
            ),

            "building": forms.Select(
                attrs={
                    "class": "form-select library-choice",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "library@wisc.edu",
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "(608) 555-1234",
                }
            ),

            "website": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://www.library.wisc.edu",
                }
            ),

            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Library Address",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Library Description",
                }
            ),

            "image": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".jpg,.jpeg,.png,.webp",
                    "id": "libraryImageInput",
                }
            ),

            "status": forms.Select(
                attrs={
                    "class": "form-select library-choice",
                }
            ),
        }

    # =====================================================
    # INITIALIZE
    # =====================================================

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        existing_hours = []

        if self.instance and self.instance.pk:
            existing_hours = self.instance.library_hours or []

        # -------------------------------------------------
        # Handle old dictionary format too
        # -------------------------------------------------

        if isinstance(existing_hours, dict):

            converted_hours = []

            for day_key, day_data in existing_hours.items():

                converted_hours.append({
                    "day": day_key,
                    "opening": day_data.get("opening", ""),
                    "closing": day_data.get("closing", ""),
                    "status": (
                        "CLOSED"
                        if day_data.get("closed", False)
                        else "OPEN"
                    ),
                })

            existing_hours = converted_hours

        # -------------------------------------------------
        # Create 7 rows
        # -------------------------------------------------

        for index in range(7):

            day_initial = ""
            opening_initial = ""
            closing_initial = ""
            status_initial = "OPEN"

            if index < len(existing_hours):

                row = existing_hours[index]

                day_initial = row.get("day", "")
                opening_initial = row.get("opening", "")
                closing_initial = row.get("closing", "")
                status_initial = row.get("status", "OPEN")

            # ---------------------------------------------
            # DAY
            # ---------------------------------------------

            self.fields[f"hours_{index}_day"] = forms.ChoiceField(
                label="Day",
                choices=self.DAY_CHOICES,
                required=False,
                initial=day_initial,
                widget=forms.Select(
                    attrs={
                        "class": "library-choice",
                    }
                )
            )

            # ---------------------------------------------
            # OPENING TIME
            # ---------------------------------------------

            self.fields[f"hours_{index}_opening"] = forms.ChoiceField(
                label="Opening Time",
                choices=self.TIME_CHOICES,
                required=False,
                initial=opening_initial,
                widget=forms.Select(
                    attrs={
                        "class": "library-choice",
                    }
                )
            )

            # ---------------------------------------------
            # CLOSING TIME
            # ---------------------------------------------

            self.fields[f"hours_{index}_closing"] = forms.ChoiceField(
                label="Closing Time",
                choices=self.TIME_CHOICES,
                required=False,
                initial=closing_initial,
                widget=forms.Select(
                    attrs={
                        "class": "library-choice",
                    }
                )
            )

            # ---------------------------------------------
            # OPEN / CLOSED
            # ---------------------------------------------

            self.fields[f"hours_{index}_status"] = forms.ChoiceField(
                label="Status",
                choices=self.HOURS_STATUS_CHOICES,
                required=False,
                initial=status_initial,
                widget=forms.Select(
                    attrs={
                        "class": "library-choice",
                    }
                )
            )

    # =====================================================
    # SAVE LIBRARY HOURS
    # =====================================================

    def save(self, commit=True):

        library = super().save(commit=False)

        library_hours = []

        used_days = set()

        for index in range(7):

            day = self.cleaned_data.get(
                f"hours_{index}_day"
            )

            opening = self.cleaned_data.get(
                f"hours_{index}_opening"
            )

            closing = self.cleaned_data.get(
                f"hours_{index}_closing"
            )

            status = self.cleaned_data.get(
                f"hours_{index}_status"
            )

            # ---------------------------------------------
            # Completely empty row
            # ---------------------------------------------

            if not day:
                continue

            # ---------------------------------------------
            # Prevent duplicate days
            # ---------------------------------------------

            if day in used_days:

                self.add_error(
                    f"hours_{index}_day",
                    "This day has already been selected."
                )

                continue

            used_days.add(day)

            # ---------------------------------------------
            # Closed
            # ---------------------------------------------

            if status == "CLOSED":

                opening = ""
                closing = ""

            # ---------------------------------------------
            # Open requires opening and closing time
            # ---------------------------------------------

            elif status == "OPEN":

                if not opening:

                    self.add_error(
                        f"hours_{index}_opening",
                        "Please select an opening time."
                    )

                if not closing:

                    self.add_error(
                        f"hours_{index}_closing",
                        "Please select a closing time."
                    )

            # ---------------------------------------------
            # Save row
            # ---------------------------------------------

            library_hours.append({
                "day": day,
                "opening": opening or "",
                "closing": closing or "",
                "status": status or "OPEN",
            })

        # ---------------------------------------------
        # Don't save if validation errors were added
        # ---------------------------------------------

        if self.errors:
            return library

        library.library_hours = library_hours

        if commit:
            library.save()

        return library

    # =====================================================
    # LIBRARY NAME
    # =====================================================

    def clean_library_name(self):

        name = self.cleaned_data.get(
            "library_name",
            ""
        ).strip()

        if not name:

            raise ValidationError(
                "Library name is required."
            )

        if len(name) < 3:

            raise ValidationError(
                "Library name must contain at least 3 characters."
            )

        if len(name) > 255:

            raise ValidationError(
                "Library name cannot exceed 255 characters."
            )

        if not re.fullmatch(
            r"[A-Za-z0-9&().,'/\-\s]+",
            name
        ):

            raise ValidationError(
                "Library name contains invalid characters."
            )

        if Library.objects.exclude(
            pk=self.instance.pk
        ).filter(
            library_name__iexact=name
        ).exists():

            raise ValidationError(
                "A library with this name already exists."
            )

        return name.title()

    # =====================================================
    # LIBRARY CODE
    # =====================================================

    def clean_library_code(self):

        code = self.cleaned_data.get(
            "library_code",
            ""
        ).strip().upper()

        if not code:

            raise ValidationError(
                "Library code is required."
            )

        if not re.fullmatch(
            r"[A-Z0-9_-]{3,50}",
            code
        ):

            raise ValidationError(
                "Library code may contain only uppercase letters, numbers, hyphens and underscores."
            )

        if Library.objects.exclude(
            pk=self.instance.pk
        ).filter(
            library_code__iexact=code
        ).exists():

            raise ValidationError(
                "Library code already exists."
            )

        return code

    # =====================================================
    # BUILDING
    # =====================================================

    def clean_building(self):

        building = self.cleaned_data.get("building")

        if not building:

            raise ValidationError(
                "Please select the building where this library is located."
            )

        return building

    # =====================================================
    # EMAIL
    # =====================================================

    def clean_email(self):

        email = self.cleaned_data.get("email")

        if not email:
            return email

        email = email.strip().lower()

        if not email.endswith("@wisc.edu"):

            raise ValidationError(
                "Email address must end with @wisc.edu."
            )

        return email

    # =====================================================
    # PHONE
    # =====================================================

    def clean_phone(self):

        phone = self.cleaned_data.get("phone")

        if not phone:
            return phone

        phone = phone.strip()

        us_phone_pattern = re.compile(
            r"^(?:\+1\s?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}$"
        )

        if not us_phone_pattern.match(phone):

            raise ValidationError(
                "Enter a valid U.S. phone number "
                "(Example: (608) 555-1234 or +1 608-555-1234)."
            )

        return phone

    # =====================================================
    # WEBSITE
    # =====================================================

    def clean_website(self):

        website = self.cleaned_data.get("website")

        if not website:
            return website

        website = website.strip()

        if not website.startswith("https://"):

            raise ValidationError(
                "Website must begin with https://"
            )

        if len(website) > 200:

            raise ValidationError(
                "Website URL cannot exceed 200 characters."
            )

        return website

    # =====================================================
    # ADDRESS
    # =====================================================

    def clean_address(self):

        address = self.cleaned_data.get("address")

        if not address:
            return address

        address = address.strip()

        if len(address) < 10:

            raise ValidationError(
                "Address must contain at least 10 characters."
            )

        if len(address) > 500:

            raise ValidationError(
                "Address cannot exceed 500 characters."
            )

        return address

    # =====================================================
    # DESCRIPTION
    # =====================================================

    def clean_description(self):

        description = self.cleaned_data.get("description")

        if not description:
            return description

        description = description.strip()

        if len(description) < 20:

            raise ValidationError(
                "Description must contain at least 20 characters."
            )

        if len(description) > 2000:

            raise ValidationError(
                "Description cannot exceed 2000 characters."
            )

        return description

    # =====================================================
    # IMAGE
    # =====================================================

    def clean_image(self):

        image = self.cleaned_data.get("image")

        if not image:
            return image

        max_size = 5 * 1024 * 1024

        if image.size > max_size:

            raise ValidationError(
                "Image size cannot exceed 5 MB."
            )

        allowed_extensions = (
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        )

        if not image.name.lower().endswith(
            allowed_extensions
        ):

            raise ValidationError(
                "Only JPG, JPEG, PNG and WEBP images are allowed."
            )

        return image

    # =====================================================
    # STATUS
    # =====================================================

    def clean_status(self):

        status = self.cleaned_data.get("status")

        allowed_status = [
            "ACTIVE",
            "INACTIVE",
        ]

        if status not in allowed_status:

            raise ValidationError(
                "Invalid library status selected."
            )

        return status