import re
from django import forms
from django.utils import timezone
from Events.models import *
from datetime import datetime, timedelta

# Modelform creates Form from the existing model
class EventCategoryForm(forms.ModelForm):

    class Meta:
        model = EventCategory
        fields = [
            "category_name",
            "description",
        ]
        # Widgets help us customize the HTML generated for each field. 
        widgets = {
            "category_name": forms.TextInput(
                attrs={
                    "placeholder": "e.g. Workshop"
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Brief description of this category..."
                }
            ),
        }
        
    def clean_category_name(self):

        category_name = self.cleaned_data["category_name"].strip()

        # Prevent empty or whitespace-only values
        if not category_name:
            raise forms.ValidationError(
                "Category name cannot be empty."
            )

        # Minimum length
        if len(category_name) < 3:
            raise forms.ValidationError(
                "Category name must contain at least 3 characters."
            )

        # Allow only letters, numbers, spaces, &, -, / and parentheses
        if not re.fullmatch(r"[A-Za-z0-9 &()/\-]+", category_name):
            raise forms.ValidationError(
                "Category name contains invalid characters."
            )
            
        if not re.search(r"[A-Za-z]", category_name):
            raise forms.ValidationError(
                "Category name must contain at least one alphabet."
            )

        # Case-insensitive uniqueness
        queryset = EventCategory.objects.filter(
            category_name__iexact=category_name
        )

        # Exclude current instance while editing
        # self.instance is a new, unsaved EventCategory Object
        # This part is useful when editing only category description and do nothing when creating a category
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise forms.ValidationError(
                "A category with this name already exists."
            )

        return category_name

    def clean_description(self):
        
        description = self.cleaned_data["description"].strip()

        # Maximum length
        if description and len(description) > 500:
            raise forms.ValidationError(
                "Description cannot exceed 500 characters."
            )

        return description
    
class EventVenueForm(forms.ModelForm):

    class Meta:
        model = EventVenue
        fields = [
            "venue_name",
            "building_name",
            "room_number",
            "seating_capacity",
            "location_details",
        ]

        widgets = {

            "venue_name": forms.TextInput(
                attrs={
                    "placeholder": "e.g. Engineering Hall"
                }
            ),

            "building_name": forms.TextInput(
                attrs={
                    "placeholder": "e.g. North Academic Block"
                }
            ),

            "room_number": forms.TextInput(
                attrs={
                    "placeholder": "e.g. E102"
                }
            ),

            "seating_capacity": forms.NumberInput(
                attrs={
                    "min": 1,
                    "placeholder": "Enter seating capacity"
                }
            ),

            "location_details": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Landmark, floor, directions, or additional location details..."
                }
            ),
        }
        
    def clean_venue_name(self):

        venue_name = self.cleaned_data["venue_name"].strip()

        if not venue_name:
            raise forms.ValidationError(
                "Venue name cannot be empty."
            )

        if len(venue_name) < 3:
            raise forms.ValidationError(
                "Venue name must contain at least 3 characters."
            )

        if not re.fullmatch(r"[A-Za-z0-9 &()/\-]+", venue_name):
            raise forms.ValidationError(
                "Only letters, numbers, spaces, &, (), / and - are allowed."
            )

        if not re.search(r"[A-Za-z]", venue_name):
            raise forms.ValidationError(
                "Venue name must contain at least one alphabet."
            )

        queryset = EventVenue.objects.filter(
            venue_name__iexact=venue_name
        )

        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise forms.ValidationError(
                "A venue with this name already exists."
            )

        return venue_name
    
    def clean_building_name(self):

        building_name = self.cleaned_data["building_name"].strip()

        # Prevent empty or whitespace-only values
        if not building_name:
            raise forms.ValidationError(
                "Building name cannot be empty."
            )

        # Minimum length
        if len(building_name) < 3:
            raise forms.ValidationError(
                "Building name must contain at least 3 characters."
            )

        # Allow only letters, numbers, spaces, &, -, / and parentheses
        if not re.fullmatch(r"[A-Za-z0-9 &()/\-]+", building_name):
            raise forms.ValidationError(
                "Only letters, numbers, spaces, &, (), /, and - are allowed."
            )

        # Must contain at least one alphabet
        if not re.search(r"[A-Za-z]", building_name):
            raise forms.ValidationError(
                "Building name must contain at least one alphabet."
            )

        return building_name


    def clean_room_number(self):

        room_number = self.cleaned_data["room_number"].strip()

        # Prevent empty or whitespace-only values
        if not room_number:
            raise forms.ValidationError(
                "Room number cannot be empty."
            )

        # Maximum length
        if len(room_number) > 50:
            raise forms.ValidationError(
                "Room cannot exceed 50 characters."
            )

        # Allow only letters, numbers, spaces, hyphen and slash
        if not re.fullmatch(r"[A-Za-z0-9 /\-]+", room_number):
            raise forms.ValidationError(
                "Only letters, numbers, spaces, /, and - are allowed."
            )

        return room_number


    def clean_seating_capacity(self):

        seating_capacity = self.cleaned_data["seating_capacity"]

        if seating_capacity is None:
            raise forms.ValidationError(
                "Seating capacity is required."
            )

        if seating_capacity < 1:
            raise forms.ValidationError(
                "Seating capacity must be at least 1."
            )

        if seating_capacity > 10000:
            raise forms.ValidationError(
                "Seating capacity cannot exceed 10000."
            )

        return seating_capacity


    def clean_location_details(self):

        location_details = self.cleaned_data.get(
            "location_details"
        )

        if location_details:
            location_details = location_details.strip()

            if len(location_details) > 500:
                raise forms.ValidationError(
                    "Location details cannot exceed 500 characters."
                )

        return location_details
    
class EventCreateForm(forms.ModelForm):

    start_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "class": "form-control date-picker",
                "placeholder": "Select start date",
                "autocomplete": "off",
            }
        )
    )

    start_time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={
                "class": "form-control time-picker",
                "placeholder": "Select start time",
                "autocomplete": "off",
            }
        )
    )

    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "class": "form-control date-picker",
                "placeholder": "Select end date",
                "autocomplete": "off",
            }
        )
    )

    end_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(
            attrs={
                "class": "form-control time-picker",
                "placeholder": "Select end time",
                "autocomplete": "off",
            }
        )
    )

    invited_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).order_by("first_name", "last_name"),
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "id": "id_invited_users",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            if self.instance.start_datetime:
                self.fields["start_date"].initial = self.instance.start_datetime.date()
                self.fields["start_time"].initial = self.instance.start_datetime.time()

            if self.instance.end_datetime:
                self.fields["end_date"].initial = self.instance.end_datetime.date()
                self.fields["end_time"].initial = self.instance.end_datetime.time()

    class Meta:
        model = Event

        fields = [
            # Basic Information
            "event_title",
            "event_subtitle",
            "event_description",
            "event_category",
            
            "organizer_type",
            "school",
            "department",
            "student_organization",
            "organizer",
            
            "event_visibility",
            "invited_users",   
            
            # Schedule and Venue
            "event_mode",
            "venue",
            "max_capacity",
            
            # Registration
            "registration_required",
            
            # Pricing
            "is_paid_event",
            "event_cost",

            # Website
            "event_website",
            
            # Contact
            "contact_email",
            "contact_phone",
            
            # Accessibility
            "has_accessibility_information",
            "accessibility_email",
            "accessibility_phone",
        ]

        widgets = {

            "event_title": forms.TextInput(
                attrs={
                    "placeholder": "e.g. AI Innovation Summit 2026"
                }
            ),

            "event_subtitle": forms.TextInput(
                attrs={
                    "placeholder": "Optional subtitle"
                }
            ),

            "event_description": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Provide a brief overview of the event..."
                }
            ),

            "event_category": forms.Select(attrs={"class": "form-select"}),

            "organizer_type": forms.Select(attrs={"class": "form-select"}),
            
            "school": forms.Select(attrs={"class": "form-select"}),

            "department": forms.Select(attrs={"class": "form-select"}),

            "student_organization": forms.Select(attrs={"class": "form-select"}),

            "organizer": forms.Select(attrs={"class": "form-select"}),

            "event_visibility": forms.Select(attrs={"class": "form-select"}),
            
            "start_datetime": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                }
            ),

            "end_datetime": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                }
            ),
            
            "event_mode": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "venue": forms.Select(attrs={"class": "form-select"}),

            # Either no value should be entered or the value >= 1
            "max_capacity": forms.NumberInput(
                attrs={
                    "min": 1,
                    "placeholder": "Leave empty to use venue capacity",
                }
            ),
            
            "registration_required": forms.RadioSelect(
                choices=[
                    (True, "Required"),
                    (False, "Not Required"),
                ]
            ),

            "contact_email": forms.EmailInput(
                attrs={
                    "placeholder": "event@university.edu",
                }
            ),

            "contact_phone": forms.TextInput(
                attrs={
                    "placeholder": "+1 234 567 890",
                }
            ),
            
            "is_paid_event": forms.RadioSelect(
                choices=[
                    (False, "Free"),
                    (True, "Paid"),
                ]
            ),

            "event_cost": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": (
                        "Example:\n"
                        "Students: Free\n"
                        "Public: $20"
                    )
                }
            ),

            "event_website": forms.URLInput(
                attrs={
                    "placeholder": "https://example.com"
                }
            ),

            "has_accessibility_information": forms.RadioSelect(
                choices=[
                    (False, "No"),
                    (True, "Yes"),
                ]
            ),

            "accessibility_email": forms.EmailInput(
                attrs={
                    "placeholder": "accessibility@university.edu"
                }
            ),

            "accessibility_phone": forms.TextInput(
                attrs={
                    "placeholder": "+1 234 567 890"
                }
            ),
        }
        
    def clean_event_title(self):

        event_title = self.cleaned_data["event_title"].strip()

        if not event_title:
            raise forms.ValidationError(
                "Event title cannot be empty."
            )

        if len(event_title) < 5:
            raise forms.ValidationError(
                "Event title must contain at least 5 characters."
            )

        if len(event_title) > 200:
            raise forms.ValidationError(
                "Event title cannot exceed 200 characters."
            )

        if not re.fullmatch(
            r"[A-Za-z0-9 &(),.:/'@\-]+",
            event_title,
        ):
            raise forms.ValidationError(
                "Event title contains invalid characters."
            )

        if not re.search(r"[A-Za-z]", event_title):
            raise forms.ValidationError(
                "Event title must contain at least one alphabet."
            )

        return event_title
    
    def clean_event_subtitle(self):

        subtitle = self.cleaned_data.get("event_subtitle")

        if subtitle:

            subtitle = subtitle.strip()
            
            if len(subtitle) < 5:
                raise forms.ValidationError(
                    "Event subtitle must contain at least 5 characters."
                )

            if len(subtitle) > 200:
                raise forms.ValidationError(
                    "Event subtitle cannot exceed 200 characters."
                )
                
            if not re.search(r"[A-Za-z]", subtitle):
                raise forms.ValidationError(
                    "Event title must contain at least one alphabet."
                )

        return subtitle
    
    def clean_event_description(self):

        description = self.cleaned_data["event_description"].strip()

        if not description:
            raise forms.ValidationError(
                "Event description cannot be empty."
            )

        if len(description) < 10:
            raise forms.ValidationError(
                "Event description must contain at least 10 characters."
            )

        if len(description) > 2000:
            raise forms.ValidationError(
                "Event description cannot exceed 2000 characters."
            )

        return description
    
    def clean_event_category(self):

        category = self.cleaned_data.get("event_category")

        if not category:
            raise forms.ValidationError(
                "Please select an event category."
            )

        return category
    
    def clean_organizer_type(self):

        organizer_type = self.cleaned_data.get("organizer_type")

        if not organizer_type:
            raise forms.ValidationError(
                "Please select an organizer type."
            )

        return organizer_type
    
    def clean_organizer(self):

        organizer = self.cleaned_data.get("organizer")

        if not organizer:
            raise forms.ValidationError(
                "Please select an organizer."
            )

        return organizer
    
    def clean_max_capacity(self):

        max_capacity = self.cleaned_data.get("max_capacity")

        # Blank means use venue seating capacity
        if max_capacity is None:
            return max_capacity

        if max_capacity < 1:
            raise forms.ValidationError(
                "Maximum capacity must be at least 1."
            )

        if max_capacity > 10000:
            raise forms.ValidationError(
                "Maximum capacity cannot exceed 10000."
            )

        return max_capacity
    
    def clean_contact_email(self):

        email = self.cleaned_data.get("contact_email")

        if not email:
            return email

        return email.strip().lower()
        
    def clean_contact_phone(self):

        phone = self.cleaned_data["contact_phone"].strip()

        if not phone:
            return phone

        if len(phone) > 20:
            raise forms.ValidationError(
                "Phone number cannot exceed 20 characters."
            )

        if not re.fullmatch(
            r"[0-9+\-() ]+",
            phone
        ):
            raise forms.ValidationError(
                "Enter a valid phone number."
            )
            
        # sub means substitute
        # syntax re.sub(pattern, replacement, string)
        # \D means any character that is not a digit
        digits = re.sub(r"\D", "", phone)

        if len(digits) < 7:
            raise forms.ValidationError(
                "Enter a valid phone number."
            )

        return phone
    
    def clean_event_cost(self):

        cost = self.cleaned_data.get("event_cost", "").strip()

        if cost and len(cost) > 1000:
            raise forms.ValidationError(
                "Pricing information cannot exceed 1000 characters."
            )

        return cost
    
    def clean_event_website(self):

        website = self.cleaned_data.get("event_website")

        if not website:
            return website

        return website.strip()
    
    def clean_accessibility_email(self):

        email = self.cleaned_data.get("accessibility_email")

        if not email:
            return email

        return email.strip().lower()
    
    def clean_accessibility_phone(self):

        phone = self.cleaned_data.get(
            "accessibility_phone",
            ""
        ).strip()

        if not phone:
            return phone

        if len(phone) > 20:
            raise forms.ValidationError(
                "Phone number cannot exceed 20 characters."
            )

        if not re.fullmatch(
            r"[0-9+\-() ]+",
            phone
        ):
            raise forms.ValidationError(
                "Enter a valid phone number."
            )

        digits = re.sub(r"\D", "", phone)

        if len(digits) < 7:
            raise forms.ValidationError(
                "Enter a valid phone number."
            )

        return phone
        
    def clean(self):

        cleaned_data = super().clean()
        
        # ---------------------------------------
        # Basic Information
        # ---------------------------------------

        organizer_type = cleaned_data.get("organizer_type")
        school = cleaned_data.get("school")
        department = cleaned_data.get("department")
        student_organization = cleaned_data.get("student_organization")

        if organizer_type == "Department":

            if not cleaned_data.get("school"):
                self.add_error(
                    "school",
                    "Please select a school."
                )

            if not cleaned_data.get("department"):
                self.add_error(
                    "department",
                    "Please select a department."
                )

            cleaned_data["student_organization"] = None

        elif organizer_type == "Student Organization":

            if not cleaned_data.get("school"):
                self.add_error(
                    "school",
                    "Please select a school."
                )

            if not cleaned_data.get("student_organization"):
                self.add_error(
                    "student_organization",
                    "Please select a student organization."
                )

            cleaned_data["department"] = None

        elif organizer_type == "Administration":

            cleaned_data["school"] = None
            cleaned_data["department"] = None
            cleaned_data["student_organization"] = None
            
        # Ensure the selected department belongs to the selected school
        if department and school and department.school != school:
            self.add_error(
                "department",
                "Selected department does not belong to the selected school."
            )

        # Ensure the selected student organization belongs to the selected school
        if student_organization and school and student_organization.school != school:
            self.add_error(
                "student_organization",
                "Selected student organization does not belong to the selected school."
            )
        
        # ---------------------------------------
        # Schedule & Venue
        # ---------------------------------------
        start_date = cleaned_data.get("start_date")
        start_time = cleaned_data.get("start_time")

        end_date = cleaned_data.get("end_date")
        end_time = cleaned_data.get("end_time")
        
        if start_date and start_time:
            start_datetime = datetime.combine(
                start_date,
                start_time,
            )
            cleaned_data["start_datetime"] = start_datetime
        else:
            start_datetime = None
            
        # End date and end time must either both exist or both be empty.
        if end_date and not end_time:
            self.add_error(
                "end_time",
                "Please select an end time."
            )

        if end_time and not end_date:
            self.add_error(
                "end_date",
                "Please select an end date."
            )
            
        if end_date and end_time:
            end_datetime = datetime.combine(
                end_date,
                end_time,
            )
            cleaned_data["end_datetime"] = end_datetime
        else:
            end_datetime = None

        if start_datetime and end_datetime:

            if end_datetime <= start_datetime:
                self.add_error(
                    "end_date",
                    "End date and time must be after the start date and time."
                )
            elif end_datetime - start_datetime < timedelta(minutes=10):
                self.add_error(
                    "end_date",
                    "The event must last at least 10 minutes."
                )
                
        event_mode = cleaned_data.get("event_mode")
        event_website = cleaned_data.get("event_website")
        venue = cleaned_data.get("venue")
        max_capacity = cleaned_data.get("max_capacity")
        
        if event_mode in [Event.ONLINE, Event.HYBRID] and not event_website:
            self.add_error(
                "event_website",
                "Website URL is required for online and hybrid events."
            )
            
        if event_mode in [Event.OFFLINE, Event.HYBRID] and not venue:
            self.add_error(
                "venue",
                "Please select an event venue."
            )

        if event_mode == Event.ONLINE:
            cleaned_data["venue"] = None

        if venue and max_capacity:

            if max_capacity > venue.seating_capacity:
                self.add_error(
                    "max_capacity",
                    f"Maximum registration capacity cannot exceed the venue seating capacity ({venue.seating_capacity})."
                )
                    
        registration_required = cleaned_data.get(
            "registration_required"
        )

        email = cleaned_data.get(
            "contact_email"
        )

        phone = cleaned_data.get(
            "contact_phone"
        )

        if registration_required and not email and not phone:
            self.add_error(
                "contact_email",
                "Provide an email or phone number when registration required"
            )
            self.add_error(
                "contact_phone",
                "Provide an email or phone number when registration required"
            )
            
        # ---------------------------------------
        # Pricing
        # ---------------------------------------

        is_paid_event = cleaned_data.get("is_paid_event")
        event_cost = cleaned_data.get("event_cost", "").strip()

        if is_paid_event:

            if not event_cost:
                self.add_error(
                    "event_cost",
                    "Please provide pricing information for this paid event."
                )

        else:
            cleaned_data["event_cost"] = ""

        # ---------------------------------------
        # Accessibility
        # ---------------------------------------

        has_accessibility_information = cleaned_data.get(
            "has_accessibility_information"
        )

        accessibility_email = cleaned_data.get(
            "accessibility_email"
        )

        if has_accessibility_information:

            if not accessibility_email:
                self.add_error(
                    "accessibility_email",
                    "Accessibility email is required."
                )

        else:

            cleaned_data["accessibility_email"] = ""
            cleaned_data["accessibility_phone"] = ""

        # ---------------------------------------
        # Visibility / Invitations
        # ---------------------------------------

        event_visibility = cleaned_data.get("event_visibility")
        invited_users = cleaned_data.get("invited_users")

        if event_visibility == Event.INVITATION_ONLY and not invited_users:
            self.add_error(
                "invited_users",
                "Please select at least one person to invite."
            )

        return cleaned_data

    
    