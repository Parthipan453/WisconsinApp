import json
import random
import uuid
from datetime import date

from django.contrib.auth.hashers import make_password, check_password
from django.db import models
from Admin.models import User
from Admin.Colleges.models import University as CollegesUniversity
from Admin.Colleges.models import AcademicProgram, Degree, School
from Admin.bela_admin.models import Department



class AdmissionCycle(models.Model):
    DEADLINE_TYPE_CHOICES = (
        ("regular", "Regular Decision"),
        ("early_action", "Early Action"),
        ("early_decision", "Early Decision"),
        ("rolling", "Rolling Admission"),
        ("priority", "Priority Deadline"),
        ("spring_transfer", "Spring Transfer"),
        ("fall_transfer", "Fall Transfer"),
    )

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    academic_year = models.CharField(max_length=20)
    term = models.CharField(max_length=20)
    application_start = models.DateField()
    application_deadline = models.DateField()
    deadline_type = models.CharField(
        max_length=20, choices=DEADLINE_TYPE_CHOICES, default="regular",
    )
    materials_deadline = models.DateField(null=True, blank=True)
    decision_release = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_open = models.BooleanField(default=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "app_admission_cycles"
        ordering = ["-application_deadline"]

    def __str__(self):
        return self.name


class Applicant(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    converted_to_user = models.OneToOneField(
        User, null=True, blank=True, related_name="applicant_source",
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "applicants"
        ordering = ["-created_at"]

    def set_password(self, raw):
        self.password = make_password(raw)

    def check_password(self, raw):
        return check_password(raw, self.password)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class Application(models.Model):
    APPLICANT_TYPE_CHOICES = (
        # Undergraduate
        ("first_year", "First-Year"),
        ("transfer", "Transfer"),
        ("international_first_year", "International First-Year"),
        ("international_transfer", "International Transfer"),
        ("returning", "Returning Student"),
        ("reentry", "Re-entry"),
        ("non_degree", "Non-Degree"),
        ("special", "Special Student"),
        ("online_ug", "Online Undergraduate"),
        ("dual_enrollment", "Dual Enrollment"),
        ("early_college", "High School Early College"),
        # Graduate
        ("masters", "Master's"),
        ("phd", "PhD"),
        ("graduate_certificate", "Graduate Certificate"),
        ("professional", "Professional Program"),
        ("online_grad", "Online Graduate"),
        # International
        ("f1", "International F-1"),
        ("j1", "International J-1"),
        ("permanent_resident", "Permanent Resident"),
        ("refugee", "Refugee"),
        ("asylum", "Asylum"),
        ("daca", "DACA"),
        ("other_visa", "Other Visa Category"),
    )
    STATUS_CHOICES = (
        ("in_progress", "In Progress"),
        ("submitted", "Submitted"),
        ("awaiting_materials", "Awaiting Materials"),
        ("complete", "Complete"),
        ("under_review", "Under Review"),
        ("admitted", "Admitted"),
        ("offer_accepted", "Offer Accepted"),
        ("waitlisted", "Waitlisted"),
        ("denied", "Denied"),
        ("enrolled", "Enrolled"),
        ("withdrawn", "Withdrawn"),
        ("archived", "Archived"),
    )

    applicant = models.ForeignKey(
        Applicant, on_delete=models.CASCADE, related_name="applications"
    )
    application_id = models.AutoField(primary_key=True)
    Reference_id = models.CharField(max_length=8, unique=True, editable=False)

    applicant_type = models.CharField(
        max_length=30, choices=APPLICANT_TYPE_CHOICES, default="first_year",
    )
    university = models.ForeignKey(
        CollegesUniversity, on_delete=models.PROTECT, null=True, blank=True,
        related_name="applications",
    )
    campus_name = models.CharField(max_length=200, default="Main Campus")
    degree_level = models.ForeignKey(
        Degree, on_delete=models.PROTECT, null=True, blank=True,
        related_name="applications",
    )
    program = models.ForeignKey(
        AcademicProgram, on_delete=models.PROTECT, null=True, blank=True,
        related_name="applications",
    )
    backup_program = models.ForeignKey(
        AcademicProgram, on_delete=models.PROTECT, null=True, blank=True,
        related_name="backup_applications",
        help_text="Second-choice (backup) program",
    )
    school = models.ForeignKey(
        School, on_delete=models.PROTECT, null=True, blank=True,
        related_name="applications",
    )
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, null=True, blank=True,
        related_name="applications",
    )
    admission_cycle = models.ForeignKey(
        AdmissionCycle, on_delete=models.PROTECT, null=True, blank=True,
        related_name="applications",
    )

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="in_progress",
    )
    progress_pct = models.IntegerField(default=0)
    is_archived = models.BooleanField(default=False)
    apply_method = models.CharField(
        max_length=20,
        choices=[("online", "Online"), ("offline", "Offline")],
        default="online",
        help_text="How the applicant is applying: online or via the printed form",
    )
    offline_form_pdf = models.FileField(
        upload_to="offline-applications/",
        blank=True,
        null=True,
        help_text="Uploaded, completed copy of the printed offline application form",
    )
    offline_form_text = models.JSONField(
        blank=True,
        null=True,
        help_text="Cached per-page text extracted from offline_form_pdf",
    )
    offline_form_extracted_at = models.DateTimeField(null=True, blank=True)
    offline_extracted_test_scores = models.JSONField(
        blank=True,
        null=True,
        help_text="Test scores parsed from the offline_form_pdf (e.g., at submission)",
    )
    fee_waiver_requested = models.BooleanField(default=False)
    fee_waiver_approved = models.BooleanField(default=False)
    signature = models.CharField(max_length=255, blank=True, help_text="Applicant's typed signature")
    submitted_date = models.DateTimeField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    # ── Offer letter & deposit ──────────────────────────────────────
    OFFER_STATUS_CHOICES = (
        ("none", "No Offer"),
        ("pending", "Offer Pending"),
        ("accepted", "Offer Accepted"),
        ("declined", "Offer Declined"),
        ("expired", "Offer Expired"),
    )
    offer_status = models.CharField(
        max_length=20, choices=OFFER_STATUS_CHOICES, default="none",
    )
    offer_sent_at = models.DateTimeField(null=True, blank=True)
    offer_accepted_at = models.DateTimeField(null=True, blank=True)
    offer_declined_at = models.DateTimeField(null=True, blank=True)
    offer_note = models.TextField(blank=True, help_text="Note included with the offer letter")
    deposit_amount = models.DecimalField(max_digits=8, decimal_places=2, default=200.00)
    deposit_paid_at = models.DateTimeField(null=True, blank=True)
    deposit_transaction_id = models.CharField(max_length=100, blank=True)

    # ── Separated admission taxonomy ────────────────────────────────
    admission_level = models.CharField(
        max_length=30, blank=True,
        choices=[
            ("ug", "Undergraduate"),
            ("masters", "Master's"),
            ("phd", "PhD"),
            ("graduate_certificate", "Graduate Certificate"),
            ("professional", "Professional"),
            ("non_degree", "Non-Degree"),
        ],
        help_text="Academic level of the program",
    )
    applicant_category = models.CharField(
        max_length=30, blank=True,
        choices=[
            ("first_year", "First-Year"),
            ("transfer", "Transfer"),
            ("returning", "Returning"),
            ("reentry", "Re-entry"),
            ("continuing", "Continuing"),
            ("dual_enrollment", "Dual Enrollment"),
            ("early_college", "Early College"),
            ("non_degree", "Non-Degree"),
        ],
        help_text="Admission category within the level",
    )
    immigration_status = models.CharField(
        max_length=30, blank=True,
        choices=[
            ("us_citizen", "US Citizen"),
            ("permanent_resident", "Permanent Resident"),
            ("f1", "F-1 Student"),
            ("j1", "J-1 Exchange"),
            ("refugee", "Refugee/Asylee"),
            ("daca", "DACA"),
            ("other_visa", "Other Visa"),
        ],
        help_text="Citizenship / immigration status",
    )

    # ── Configuration snapshot (immutable after submission) ────────────
    config_snapshot = models.JSONField(
        null=True, blank=True,
        help_text="Immutable snapshot of resolved workflow + form schemas at creation/submission time",
    )

    # Military-affiliated applicant fields (configurable via workflow)
    military_status = models.CharField(max_length=50, blank=True)
    branch_of_service = models.CharField(max_length=100, blank=True)
    service_start_date = models.DateField(null=True, blank=True)
    service_end_date = models.DateField(null=True, blank=True)
    va_benefits = models.BooleanField(default=False)
    gi_bill_chapter = models.CharField(max_length=50, blank=True)
    tuition_assistance = models.BooleanField(default=False)

    # Residency
    residency_status = models.CharField(max_length=50, blank=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "applications"
        ordering = ["-created_date"]
        indexes = [
            models.Index(fields=["applicant", "status"]),
            models.Index(fields=["university", "status"]),
            models.Index(fields=["degree_level", "applicant_type"]),
        ]

    def save(self, *args, **kwargs):
        if not self.Reference_id:
            self.Reference_id = self._generate_reference()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_reference():
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        return "UW" + "".join(random.choices(chars, k=6))

    def __str__(self):
        return f"{self.Reference_id} — {self.applicant}"




FIELD_TYPE_CHOICES = [
    ("text", "Text"),
    ("textarea", "Textarea"),
    ("number", "Number"),
    ("date", "Date"),
    ("select", "Select (Single)"),
    ("multi_select", "Select (Multiple)"),
    ("radio", "Radio"),
    ("checkbox", "Checkbox"),
    ("file", "File Upload"),
    ("email", "Email"),
    ("phone", "Phone"),
    ("url", "URL"),
    ("gpa", "GPA"),
    ("currency", "Currency"),
    ("rich_text", "Rich Text"),
    ("country", "Country"),
    ("state", "State"),
    ("city", "City"),
    ("hidden", "Hidden"),
    ("password", "Password"),
    ("ssn", "SSN (Masked)"),
]

VALIDATION_TYPE_CHOICES = [
    ("required", "Required"),
    ("min_length", "Min Length"),
    ("max_length", "Max Length"),
    ("min_value", "Min Value"),
    ("max_value", "Max Value"),
    ("regex", "Regex Pattern"),
    ("regex_msg", "Regex Error Message"),
    ("email", "Email Format"),
    ("phone", "Phone Format"),
    ("url", "URL Format"),
    ("date_range", "Date Range"),
    ("file_size", "Max File Size"),
    ("file_extension", "Allowed Extensions"),
    ("word_count", "Word Count Range"),
    ("custom", "Custom Validation"),
]

VISIBILITY_OPERATOR_CHOICES = [
    ("eq", "Equals"),
    ("neq", "Not Equals"),
    ("contains", "Contains"),
    ("gt", "Greater Than"),
    ("gte", "Greater Than or Equal"),
    ("lt", "Less Than"),
    ("lte", "Less Than or Equal"),
    ("in", "In List"),
    ("not_in", "Not In List"),
    ("is_empty", "Is Empty"),
    ("not_empty", "Is Not Empty"),
    ("checked", "Is Checked"),
    ("not_checked", "Is Not Checked"),
]

LOGIC_OPERATOR_CHOICES = [
    ("AND", "All conditions must match"),
    ("OR", "Any condition must match"),
]

VISIBILITY_ACTION_CHOICES = [
    ("show", "Show"),
    ("hide", "Hide"),
    ("require", "Make Required"),
    ("optional", "Make Optional"),
]


class FormDefinition(models.Model):
    code = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Tabler icon name")
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "dyn_form_definitions"
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.name} (v{self.version})"


class FormSection(models.Model):
    form = models.ForeignKey(
        FormDefinition, on_delete=models.CASCADE, related_name="sections",
    )
    code = models.SlugField(max_length=100)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    help_text = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)
    is_repeatable = models.BooleanField(default=False, help_text="Allow multiple entries (e.g., multiple education entries)")
    max_repeat = models.IntegerField(default=1, help_text="Max entries if repeatable")
    is_active = models.BooleanField(default=True)
    render_as = models.CharField(
        max_length=50, default="card",
        choices=[("card", "Card"), ("fieldset", "Fieldset"), ("accordion", "Accordion")],
    )
    is_full_crud = models.BooleanField(default=True)
    start_hidden = models.BooleanField(default=False, help_text="Hide all non-heading fields until 'Add' button is clicked")

    class Meta:
        db_table = "dyn_form_sections"
        ordering = ["form", "sort_order"]
        unique_together = [["form", "code"]]

    def __str__(self):
        return f"{self.form.name} → {self.title}"


class FormField(models.Model):
    section = models.ForeignKey(
        FormSection, on_delete=models.CASCADE, related_name="fields",
    )
    code = models.SlugField(max_length=100)
    label = models.CharField(max_length=255)
    placeholder = models.CharField(max_length=255, blank=True)
    help_text = models.TextField(blank=True)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES)
    default_value = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)
    css_class = models.CharField(max_length=255, blank=True)
    layout_width = models.CharField(
        max_length=20, default="full",
        choices=[("full", "Full Width"), ("half", "Half Width"), ("third", "One Third"), ("two_thirds", "Two Thirds")],
    )

    # Configurable options
    placeholder_value = models.CharField(max_length=255, blank=True)
    prefix_text = models.CharField(max_length=100, blank=True, help_text="Text before input (e.g., $)")
    suffix_text = models.CharField(max_length=100, blank=True, help_text="Text after input (e.g., .00)")
    rows = models.IntegerField(default=4, help_text="Rows for textarea")

    # File upload config
    max_file_size_mb = models.IntegerField(default=10)
    allowed_extensions = models.CharField(max_length=500, default=".pdf,.doc,.docx,.jpg,.png")

    # Dynamic data source
    data_source = models.CharField(
        max_length=100, blank=True,
        help_text="Code reference to a data provider for dynamic choices",
    )

    is_required = models.BooleanField(default=False, help_text="Mark as required (creates a required ValidationRule)")
    is_active = models.BooleanField(default=True)
    is_readonly = models.BooleanField(default=False)
    is_encrypted = models.BooleanField(default=False, help_text="Encrypt stored value (e.g., SSN)")
    is_visible = models.BooleanField(default=True, help_text="Whether this field is visible by default")
    regex_pattern = models.CharField(max_length=500, blank=True, help_text="Client-side regex validation pattern")
    min_length = models.IntegerField(null=True, blank=True, help_text="Minimum character length")
    max_length = models.IntegerField(null=True, blank=True, help_text="Maximum character length")

    # ── Visual styling (used by the applicant form + preview) ──
    label_color = models.CharField(max_length=20, blank=True, default="", help_text="CSS color for the field label (e.g. #333333)")
    input_color = models.CharField(max_length=20, blank=True, default="", help_text="CSS color for the input text (e.g. #212529)")
    font_size = models.CharField(max_length=20, blank=True, default="", help_text="CSS font-size for the input (e.g. 14px)")
    input_background = models.CharField(max_length=30, blank=True, default="", help_text="CSS background color for the input (e.g. #ffffff)")
    border_color = models.CharField(max_length=20, blank=True, default="", help_text="CSS border color for the input (e.g. #d0d0d0)")
    input_height = models.CharField(max_length=20, blank=True, default="", help_text="CSS height for the input (e.g. 42px)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "dyn_form_fields"
        ordering = ["section__form", "section__sort_order", "sort_order"]
        unique_together = [["section", "code"]]

    def __str__(self):
        return f"{self.section.title} → {self.label}"


class FieldChoice(models.Model):
    field = models.ForeignKey(
        FormField, on_delete=models.CASCADE, related_name="choices",
    )
    value = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    sort_order = models.IntegerField(default=0)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    depends_on_field = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="dependent_choices",
        help_text="Parent choice for cascading selects",
    )
    metadata = models.JSONField(default=dict, blank=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "dyn_field_choices"
        ordering = ["field", "sort_order"]

    def __str__(self):
        return f"{self.field.label} → {self.label}"


class ValidationRule(models.Model):
    field = models.ForeignKey(
        FormField, on_delete=models.CASCADE, related_name="validations",
    )
    validation_type = models.CharField(max_length=50, choices=VALIDATION_TYPE_CHOICES)
    value = models.CharField(max_length=500, blank=True, help_text="e.g., 100 for max_length, ^[a-z]+$ for regex")
    value_max = models.CharField(max_length=500, blank=True, help_text="Upper bound for range validations")
    error_message = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "dyn_validation_rules"
        ordering = ["field", "sort_order"]

    def __str__(self):
        return f"{self.field.label} → {self.validation_type}"


class VisibilityRule(models.Model):
    field = models.ForeignKey(
        FormField, on_delete=models.CASCADE, related_name="visibility_rules",
    )
    target_field = models.ForeignKey(
        FormField, on_delete=models.CASCADE, related_name="+",
        help_text="Field whose value determines visibility",
    )
    operator = models.CharField(max_length=20, choices=VISIBILITY_OPERATOR_CHOICES)
    value = models.TextField(blank=True, help_text="Value to compare against")
    logic_operator = models.CharField(
        max_length=5, choices=LOGIC_OPERATOR_CHOICES, default="AND",
        help_text="How this rule combines with other rules",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    action = models.CharField(
        max_length=20, choices=VISIBILITY_ACTION_CHOICES, default="show",
        help_text="What to do when the condition matches",
    )
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "dyn_visibility_rules"
        ordering = ["field", "sort_order"]

    def __str__(self):
        return f"{self.get_action_display()} {self.field.label} when {self.target_field.label} {self.operator} {self.value}"


class FormAssignment(models.Model):
    form = models.ForeignKey(FormDefinition, on_delete=models.CASCADE, related_name="assignments")
    university = models.ForeignKey(
        CollegesUniversity, on_delete=models.CASCADE, null=True, blank=True,
        related_name="form_assignments",
    )
    degree_level = models.ForeignKey(
        Degree, on_delete=models.CASCADE, null=True, blank=True,
        related_name="form_assignments",
    )
    applicant_type = models.CharField(
        max_length=30, null=True, blank=True,
        help_text="Leave blank to apply to all applicant types",
    )
    program = models.ForeignKey(
        AcademicProgram, on_delete=models.CASCADE, null=True, blank=True,
        related_name="form_assignments",
    )
    school = models.ForeignKey(
        School, on_delete=models.CASCADE, null=True, blank=True,
        related_name="form_assignments",
    )
    sort_order = models.IntegerField(default=0)
    is_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "dyn_form_assignments"
        ordering = ["university", "degree_level", "sort_order"]
        indexes = [
            models.Index(fields=["university", "degree_level", "applicant_type"]),
            models.Index(fields=["form", "is_active"]),
        ]

    def __str__(self):
        return f"{self.form.name} → {self.university or 'All'} / {self.degree_level or 'All'}"


class SectionAssignment(models.Model):
    section = models.ForeignKey(
        FormSection, on_delete=models.CASCADE, related_name="assignments",
    )
    university = models.ForeignKey(
        CollegesUniversity, on_delete=models.CASCADE, null=True, blank=True,
        related_name="section_assignments",
    )
    degree_level = models.ForeignKey(
        Degree, on_delete=models.CASCADE, null=True, blank=True,
        related_name="section_assignments",
    )
    applicant_type = models.CharField(
        max_length=30, null=True, blank=True,
        help_text="Leave blank to apply to all applicant types",
    )
    program = models.ForeignKey(
        AcademicProgram, on_delete=models.CASCADE, null=True, blank=True,
        related_name="section_assignments",
    )
    school = models.ForeignKey(
        School, on_delete=models.CASCADE, null=True, blank=True,
        related_name="section_assignments",
    )
    sort_order = models.IntegerField(default=0)
    is_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "dyn_section_assignments"
        ordering = ["section", "sort_order"]
        indexes = [
            models.Index(fields=["university", "degree_level", "applicant_type"]),
            models.Index(fields=["section", "is_active"]),
        ]

    def __str__(self):
        return (
            f"{self.section.title} for "
            f"{self.university or 'All'} / {self.degree_level or 'All'} / "
            f"{self.applicant_type or 'All'}"
        )


 

class FormResponse(models.Model):
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="form_responses",
    )
    form = models.ForeignKey(FormDefinition, on_delete=models.CASCADE, related_name="responses")
    section = models.ForeignKey(FormSection, on_delete=models.CASCADE, related_name="responses")
    repeat_index = models.IntegerField(default=0, help_text="Index for repeatable sections")
    is_complete = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "dyn_form_responses"
        indexes = [
            models.Index(fields=["application", "form"]),
            models.Index(fields=["application", "section", "repeat_index"]),
        ]
        unique_together = [["application", "section", "repeat_index"]]

    def __str__(self):
        return f"Response: {self.application.Reference_id} → {self.section.title}"


class FieldResponse(models.Model):
    response = models.ForeignKey(
        FormResponse, on_delete=models.CASCADE, related_name="field_responses",
    )
    field = models.ForeignKey(FormField, on_delete=models.CASCADE, related_name="responses")

    # Typed value columns — only one is populated per field, based on field_type
    value = models.TextField(blank=True, null=True, help_text="Raw string value (text, textarea, select, radio, country, state, url, phone, email, password)")
    value_numeric = models.FloatField(null=True, blank=True, help_text="Numeric value (number, gpa, currency)")
    value_json = models.TextField(blank=True, help_text="JSON value (multi_select, repeatable group data)")
    value_bool = models.BooleanField(null=True, blank=True, help_text="Boolean value (checkbox)")
    value_encrypted = models.TextField(blank=True, help_text="Encrypted value for sensitive fields (ssn, password)")

    file = models.CharField(max_length=500, blank=True, help_text="File path for file uploads")
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "dyn_field_responses"
        unique_together = [["response", "field"]]
        indexes = [
            models.Index(fields=["response", "field"]),
            models.Index(fields=["field"]),
        ]

    def typed_value(self):
        """Return the value in its most appropriate Python type."""
        if self.value_encrypted:
            from django.core.signing import Signer, BadSignature
            try:
                return Signer().unsign(self.value_encrypted)
            except BadSignature:
                return self.value_encrypted
        if self.value_numeric is not None:
            return self.value_numeric
        if self.value_json:
            try:
                return json.loads(self.value_json)
            except (json.JSONDecodeError, TypeError):
                return self.value_json
        if self.value_bool is not None:
            return self.value_bool
        return self.value

    def __str__(self):
        display = str(self.typed_value())[:50] if self.typed_value() is not None else ""
        return f"{self.field.label}: {display}"


 

class WorkflowDefinition(models.Model):
    code = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    university = models.ForeignKey(
        CollegesUniversity, on_delete=models.CASCADE, null=True, blank=True,
        related_name="workflows",
    )
    degree_level = models.ForeignKey(
        Degree, on_delete=models.CASCADE, null=True, blank=True,
        related_name="workflows",
    )
    applicant_type = models.CharField(max_length=30, null=True, blank=True)
    program = models.ForeignKey(
        AcademicProgram, on_delete=models.CASCADE, null=True, blank=True,
        related_name="workflows",
    )
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "dyn_workflow_definitions"
        indexes = [
            models.Index(fields=["university", "degree_level", "applicant_type"]),
            models.Index(fields=["code", "is_active"]),
        ]

    def __str__(self):
        return f"Workflow: {self.name}"


class DynamicWorkflowStep(models.Model):
    workflow = models.ForeignKey(
        WorkflowDefinition, on_delete=models.CASCADE, related_name="steps",
    )
    code = models.SlugField(max_length=100)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    step_type = models.CharField(
        max_length=30,
        choices=[
            ("form", "Form Section"),
            ("review", "Review"),
            ("payment", "Payment"),
            ("submit", "Submit"),
            ("document", "Document Upload"),
            ("external", "External Redirect"),
        ],
        default="form",
    )
    form = models.ForeignKey(
        FormDefinition, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="workflow_steps",
        help_text="Linked form for form-type steps",
    )
    sort_order = models.IntegerField(default=0)
    is_required = models.BooleanField(default=True)
    is_skippable = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    group = models.CharField(max_length=100, blank=True, help_text="Group label for step categorization")
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "dyn_workflow_steps"
        ordering = ["workflow", "sort_order"]
        unique_together = [["workflow", "code"]]

    def __str__(self):
        return f"{self.workflow.name} → {self.name}"


class StepCondition(models.Model):
    step = models.ForeignKey(
        DynamicWorkflowStep, on_delete=models.CASCADE, related_name="conditions",
    )
    target_field = models.CharField(
        max_length=100, blank=True,
        help_text="Field code to check (e.g., applicant_type, military_status)",
    )
    operator = models.CharField(max_length=20, choices=VISIBILITY_OPERATOR_CHOICES)
    value = models.TextField(blank=True)
    logic_operator = models.CharField(
        max_length=5, choices=LOGIC_OPERATOR_CHOICES, default="AND",
    )
    is_active = models.BooleanField(default=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "dyn_step_conditions"

    def __str__(self):
        return f"Condition: {self.target_field} {self.operator} {self.value}"


 
DOCUMENT_CATEGORY_CHOICES = [
    ("identification", "Identification"),
    ("academic", "Academic"),
    ("financial", "Financial"),
    ("test_score", "Test Scores"),
    ("essay", "Essay/Writing Sample"),
    ("portfolio", "Portfolio"),
    ("legal", "Legal/Immigration"),
    ("military", "Military"),
    ("other", "Other"),
]


class DocumentRequirement(models.Model):
    code = models.SlugField(max_length=100)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=30, choices=DOCUMENT_CATEGORY_CHOICES)
    university = models.ForeignKey(
        CollegesUniversity, on_delete=models.CASCADE, null=True, blank=True,
        related_name="doc_requirements",
    )
    degree_level = models.ForeignKey(
        Degree, on_delete=models.CASCADE, null=True, blank=True,
        related_name="doc_requirements",
    )
    applicant_type = models.CharField(max_length=30, null=True, blank=True)
    program = models.ForeignKey(
        AcademicProgram, on_delete=models.CASCADE, null=True, blank=True,
        related_name="doc_requirements",
    )
    is_required = models.BooleanField(default=True)
    max_file_size_mb = models.IntegerField(default=10)
    allowed_extensions = models.CharField(max_length=500, default=".pdf,.doc,.docx,.jpg,.png")
    max_files = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "dyn_document_requirements"
        ordering = ["university", "degree_level", "sort_order"]
        unique_together = [["code", "university", "degree_level"]]
        indexes = [
            models.Index(fields=["university", "degree_level", "applicant_type"]),
        ]

    def __str__(self):
        return self.name


class Document(models.Model):
    DOC_TYPES = [
        ("transcript", "Transcript"),
        ("essay", "Personal Essay"),
        ("test_score", "Test Score Report"),
        ("resume", "Resume / CV"),
        ("id_proof", "ID Proof"),
        ("financial", "Financial Statement"),
        ("portfolio", "Portfolio"),
        ("sop", "Statement of Purpose"),
        ("other", "Other"),
    ]
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="documents",
    )
    requirement = models.ForeignKey(
        DocumentRequirement, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="uploaded_documents",
    )
    doc_type = models.CharField(max_length=50, blank=True, choices=DOC_TYPES)
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField(default=0)
    file_path = models.CharField(max_length=500)
    is_verified = models.BooleanField(default=False)
    verified_by = models.CharField(max_length=100, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "application_documents"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.file_name


 

class ApplicationChecklistItem(models.Model):
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="checklist_items",
    )
    code = models.CharField(max_length=50)
    label = models.CharField(max_length=200)
    item_type = models.CharField(
        max_length=30, default="form",
        choices=[("form", "Form Section"), ("document", "Document"), ("payment", "Payment"), ("review", "Review")],
    )
    reference_code = models.CharField(max_length=100, blank=True, help_text="Form code or document code")
    is_required = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "app_checklist_items"
        unique_together = [["application", "code"]]
        ordering = ["application", "code"]
        indexes = [
            models.Index(fields=["application", "code"]),
        ]

    def __str__(self):
        return self.label


 

class EssayPrompt(models.Model):
    code = models.SlugField(max_length=100)
    university = models.ForeignKey(
        CollegesUniversity, on_delete=models.CASCADE, null=True, blank=True,
        related_name="essay_prompts",
    )
    degree_level = models.ForeignKey(
        Degree, on_delete=models.CASCADE, null=True, blank=True,
        related_name="essay_prompts",
    )
    applicant_type = models.CharField(max_length=30, null=True, blank=True)
    program = models.ForeignKey(
        AcademicProgram, on_delete=models.CASCADE, null=True, blank=True,
        related_name="essay_prompts",
    )
    essay_type = models.CharField(max_length=100, help_text="e.g., personal_statement, sop, diversity")
    title = models.CharField(max_length=255)
    prompt_text = models.TextField()
    min_words = models.IntegerField(default=0)
    max_words = models.IntegerField(default=0)
    is_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "dyn_essay_prompts"
        ordering = ["university", "degree_level", "sort_order"]
        indexes = [
            models.Index(fields=["university", "degree_level", "applicant_type"]),
        ]

    def __str__(self):
        return f"{self.essay_type}: {self.title}"


 

class ApplicationEssay(models.Model):
    ESSAY_TYPE_CHOICES = (
        ("personal_statement", "Personal Statement"),
        ("statement_of_purpose", "Statement of Purpose"),
        ("diversity_statement", "Diversity Statement"),
        ("other", "Other"),
    )

    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="essays",
        db_index=True,
    )
    essay_prompt = models.ForeignKey(
        EssayPrompt, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="responses",
    )
    essay_type = models.CharField(max_length=100, choices=ESSAY_TYPE_CHOICES)
    prompt_text = models.TextField(blank=True)
    content = models.TextField(blank=True)
    word_count = models.IntegerField(default=0)
    is_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "app_essays"
        unique_together = [["application", "essay_type"]]

    def __str__(self):
        return f"{self.essay_type} — {self.application.Reference_id}"


  
class ApplicationLog(models.Model):
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="logs",
        db_index=True,
    )
    field_name = models.CharField(max_length=50)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    actor = models.CharField(max_length=100, default="applicant")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "application_logs"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.application.Reference_id} — {self.field_name}"


class FeePayment(models.Model):
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="payments",
    )
    transaction_id = models.CharField(max_length=100, unique=True)
    checkout_session_id = models.CharField(max_length=255, blank=True, default="")
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("completed", "Completed"), ("failed", "Failed"), ("refunded", "Refunded")],
        default="pending",
    )
    payment_method = models.CharField(max_length=50, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "application_payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.transaction_id} — {self.amount} {self.currency}"


class ApplicationTimeline(models.Model):
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="timeline",
    )
    event_type = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_date = models.DateTimeField()
    is_automated = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "app_timeline"
        ordering = ["event_date"]

    def __str__(self):
        return self.title


class ApplicationStatusHistory(models.Model):
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="status_history",
    )
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    changed_by = models.CharField(max_length=100, default="system")
    note = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "app_status_history"
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.from_status} → {self.to_status}"


class Country(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=2, unique=True, db_index=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "loc_countries"
        ordering = ["name"]

    def __str__(self):
        return self.name


class StateProvince(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, blank=True)
    country_code = models.CharField(max_length=2, db_index=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "loc_states"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}, {self.country_code}"


class City(models.Model):
    name = models.CharField(max_length=200)
    state = models.ForeignKey(
        StateProvince, on_delete=models.CASCADE, related_name="cities",
    )
    country_code = models.CharField(max_length=2, db_index=True, blank=True)
    is_full_crud = models.BooleanField(default=False)

    class Meta:
        db_table = "loc_cities"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}, {self.state.name}"


class ApplicantProfile(models.Model):
    applicant = models.OneToOneField(
        Applicant, on_delete=models.CASCADE, related_name="profile",
    )
    middle_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    photo = models.ImageField(upload_to="profile_photos/", blank=True)
    phone = models.CharField(max_length=20, blank=True)
    alternate_phone = models.CharField(max_length=20, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    languages = models.JSONField(default=list, blank=True)
    profile_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "applicant_profiles"

    def __str__(self):
        return f"Profile: {self.applicant}"


class FeeWaiver(models.Model):
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="fee_waivers",
    )
    waiver_type = models.CharField(max_length=50, blank=True)
    reason = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    approved_by = models.CharField(max_length=100, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "app_fee_waivers"

    def __str__(self):
        return f"Waiver: {self.application.Reference_id}"


class ApplicationFee(models.Model):
    university = models.ForeignKey(
        CollegesUniversity, on_delete=models.CASCADE, null=True, blank=True,
        related_name="application_fees",
    )
    degree_level = models.ForeignKey(
        Degree, on_delete=models.CASCADE, null=True, blank=True,
        related_name="application_fees",
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    waiver_available = models.BooleanField(default=False)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "app_application_fees"

    def __str__(self):
        return f"App Fee: ${self.amount}"


class ApplicantTypeRequirement(models.Model):
    APPLICANT_TYPE_CHOICES = [
        ("first_year", "First-Year"),
        ("transfer", "Transfer"),
        ("reentry", "Reentry"),
        ("second_degree", "Second Degree"),
        ("international_first_year", "International First-Year"),
        ("international_transfer", "International Transfer"),
        ("all", "All Types"),
    ]
    applicant_type = models.CharField(max_length=30, choices=APPLICANT_TYPE_CHOICES)
    degree_level = models.ForeignKey(Degree, on_delete=models.CASCADE, null=True, blank=True)
    requires_transcript = models.BooleanField(default=True)
    requires_high_school_courses = models.BooleanField(default=False)
    requires_college_transcript = models.BooleanField(default=False)
    requires_essay = models.BooleanField(default=True)
    requires_activities = models.BooleanField(default=True)
    requires_honors = models.BooleanField(default=True)
    requires_test_scores = models.BooleanField(default=False)
    test_optional = models.BooleanField(default=True)
    requires_resume = models.BooleanField(default=False)
    min_transfer_credits = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_full_crud = models.BooleanField(default=True)
    class Meta:
        db_table = "app_applicant_type_requirements"


class ProgramRequirement(models.Model):
    program = models.ForeignKey(AcademicProgram, on_delete=models.CASCADE, null=True, blank=True)
    degree_level = models.ForeignKey(Degree, on_delete=models.CASCADE, null=True, blank=True)
    min_gpa = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    required_documents = models.JSONField(default=list, blank=True)
    additional_questions = models.JSONField(default=list, blank=True)
    course_requirements = models.JSONField(default=dict, blank=True, help_text="Subject: credits required, e.g. {\"english\": 4, \"math\": 3}")
    min_total_credits = models.IntegerField(null=True, blank=True, help_text="Minimum total high school credits required")
    is_active = models.BooleanField(default=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "app_program_requirements"

    def __str__(self):
        return f"ProgReq: {self.program_id or 'N/A'}"


class UniversityDocumentRequirement(models.Model):
    university = models.ForeignKey(CollegesUniversity, on_delete=models.CASCADE, null=True, blank=True)
    degree_level = models.ForeignKey(Degree, on_delete=models.CASCADE, null=True, blank=True)
    document_type = models.CharField(max_length=50)
    display_name = models.CharField(max_length=200)
    is_required = models.BooleanField(default=True)
    max_size_mb = models.IntegerField(default=10)
    allowed_extensions = models.CharField(max_length=500, default=".pdf,.doc,.docx")
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "app_university_doc_requirements"
        ordering = ["university", "degree_level", "document_type"]

    def __str__(self):
        return f"DocReq: {self.display_name}"


class UniversityEssayRequirement(models.Model):
    university = models.ForeignKey(CollegesUniversity, on_delete=models.CASCADE, null=True, blank=True)
    degree_level = models.ForeignKey(Degree, on_delete=models.CASCADE, null=True, blank=True)
    applicant_type = models.CharField(
        max_length=30, default="all",
        choices=[
            ("first_year", "First-Year"), ("transfer", "Transfer"),
            ("reentry", "Reentry"), ("second_degree", "Second Degree"),
            ("international_first_year", "International First-Year"),
            ("international_transfer", "International Transfer"),
            ("all", "All Types"),
        ],
    )
    essay_type = models.CharField(max_length=50)
    prompt = models.TextField()
    min_words = models.IntegerField(default=0)
    max_words = models.IntegerField(default=0)
    is_required = models.BooleanField(default=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "app_university_essay_requirements"

    def __str__(self):
        return f"EssayReq: {self.essay_type}"


class ApplicationReviewAssignment(models.Model):
    """Admin assigns an application to a staff reviewer."""

    STATUS_CHOICES = [
        ("assigned", "Assigned"),
        ("in_progress", "In Progress"),
        ("awaiting_materials", "Awaiting Materials"),
        ("ready_for_decision", "Ready for Decision"),
        ("decided", "Decision Made"),
    ]

    RECOMMENDATION_CHOICES = [
        ("", "No recommendation yet"),
        ("admit", "Recommend Admission"),
        ("waitlist", "Recommend Waitlist"),
        ("deny", "Recommend Denial"),
        ("escalate", "Escalate to Senior Reviewer"),
    ]

    application = models.OneToOneField(
        Application, on_delete=models.CASCADE, related_name="review_assignment",
    )
    reviewer = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="application_reviews",
    )
    assigned_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="applications_assigned",
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="assigned")
    is_verified = models.BooleanField(default=False)
    recommendation = models.CharField(
        max_length=20,
        choices=RECOMMENDATION_CHOICES,
        blank=True,
        default="",
        help_text="The reviewer's manual recommendation. This is not the final admission decision.",
    )
    recommendation_note = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True, help_text="Internal notes for the admission committee")
    decision_note = models.TextField(blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "app_review_assignments"
        ordering = ["-assigned_at"]

    def __str__(self):
        return f"{self.application.Reference_id} → {self.reviewer}"


class FieldCorrectionRequest(models.Model):
    """A batch of form-response fields the reviewer flagged as wrong and
    asked the applicant to correct (online applications)."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("resubmitted", "Resubmitted"),
        ("closed", "Closed"),
    ]

    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="field_correction_requests",
    )
    requested_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="field_correction_requests_made",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending",
    )
    message = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    resubmitted_at = models.DateTimeField(null=True, blank=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "app_field_correction_requests"
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.application.Reference_id} — field corrections ({self.get_status_display()})"


class SectionReview(models.Model):
    """Manual review verdict for one named section of an application.

    The reviewer personally decides whether the information in a section is
    correct ("reviewed"), has a problem ("issue"), or has not been looked at
    yet. Nothing is generated automatically — this is purely manual.
    """

    STATUS_CHOICES = [
        ("not_reviewed", "Not Reviewed"),
        ("reviewed", "Reviewed"),
        ("issue", "Issue Found"),
        ("issue_solved", "Issue Solved"),
    ]

    assignment = models.ForeignKey(
        ApplicationReviewAssignment, on_delete=models.CASCADE,
        related_name="section_reviews",
    )
    section_code = models.CharField(max_length=50)
    section_title = models.CharField(max_length=120)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="not_reviewed",
    )
    note = models.TextField(blank=True, help_text="Reviewer note for this section")
    internal_note = models.TextField(blank=True, help_text="Internal note for the admission committee")
    applicant_reply = models.TextField(blank=True, help_text="Applicant reply to reviewer clarification request")
    applicant_replied_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="section_reviews",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "app_section_reviews"
        ordering = ["section_code"]
        unique_together = [["assignment", "section_code"]]

    def __str__(self):
        return f"{self.assignment.application.Reference_id} — {self.section_title} ({self.get_status_display()})"


class FieldReview(models.Model):
    """Reviewer verdict for a single submitted form-response field."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
    ]

    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="field_reviews",
    )
    assignment = models.ForeignKey(
        ApplicationReviewAssignment, on_delete=models.CASCADE,
        related_name="field_reviews",
    )
    field_response = models.ForeignKey(
        FieldResponse, on_delete=models.CASCADE, related_name="reviews",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending",
    )
    note = models.TextField(blank=True, help_text="Reviewer note shared with the applicant")
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="field_reviews",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    correction_request = models.ForeignKey(
        FieldCorrectionRequest, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="field_reviews",
        help_text="The correction request this rejection was sent in (null until sent)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "app_field_reviews"
        ordering = ["created_at"]
        unique_together = [["field_response", "assignment"]]

    def __str__(self):
        return f"{self.application.Reference_id} — {self.field_response.field.label} ({self.status})"


class MaterialRequest(models.Model):
    """Staff asks the applicant for a missing document/material."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("fulfilled", "Fulfilled"),
        ("waived", "Waived"),
    ]

    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="material_requests",
    )
    requested_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="material_requests_made",
    )
    requirement = models.ForeignKey(
        DocumentRequirement, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="material_requests",
    )
    doc_type = models.CharField(max_length=50, blank=True, choices=Document.DOC_TYPES)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    requested_at = models.DateTimeField(auto_now_add=True)
    fulfilled_at = models.DateTimeField(null=True, blank=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "app_material_requests"
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.application.Reference_id} — {self.get_doc_type_display() or self.requirement}"


class ApplicantNotification(models.Model):
    NOTIFICATION_TYPES = [
        ("INFO", "Info"),
        ("SUCCESS", "Success"),
        ("WARNING", "Warning"),
        ("ERROR", "Error"),
        ("REQUEST", "Request"),
        ("SYSTEM", "System"),
    ]

    applicant = models.ForeignKey(
        Applicant, on_delete=models.CASCADE, related_name="notifications",
    )
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)
    notification_type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPES, default="INFO",
    )
    link = models.CharField(max_length=500, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_full_crud = models.BooleanField(default=True)

    class Meta:
        db_table = "applicant_notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.applicant.email} — {self.title}"
