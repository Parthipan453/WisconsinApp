from django.contrib import admin

from .models import (
    AdmissionCycle,
    Applicant,
    Application,
    ApplicantProfile,
    FeePayment,
    FeeWaiver,
    ApplicationChecklistItem,
    ApplicationEssay,
    FormDefinition,
    FormSection,
    FormField,
    FieldChoice,
    ValidationRule,
    VisibilityRule,
    FormResponse,
    FieldResponse,
    FormAssignment,
    SectionAssignment,
    WorkflowDefinition,
    DynamicWorkflowStep,
    StepCondition,
    DocumentRequirement,
    Document,
    EssayPrompt,
    ApplicationFee,
    ApplicationReviewAssignment,
    MaterialRequest,
    FieldCorrectionRequest,
    FieldReview,
    ApplicantTypeRequirement,
    ProgramRequirement,
)




class FieldChoiceInline(admin.TabularInline):
    model = FieldChoice
    extra = 1
    fields = ["value", "label", "sort_order", "is_default", "is_active", "depends_on_field"]


class ValidationRuleInline(admin.TabularInline):
    model = ValidationRule
    extra = 1
    fields = ["validation_type", "value", "value_max", "error_message", "sort_order", "is_active"]


class VisibilityRuleInline(admin.TabularInline):
    model = VisibilityRule
    fk_name = "field"
    extra = 1
    fields = ["target_field", "operator", "value", "logic_operator", "sort_order", "is_active"]
    autocomplete_fields = ["target_field"]


class FormFieldInline(admin.TabularInline):
    model = FormField
    extra = 2
    fields = [
        "code",
        "label",
        "field_type",
        "placeholder",
        "sort_order",
        "layout_width",
        "is_required",
        "is_active",
    ]
    show_change_link = True


class FormSectionInline(admin.TabularInline):
    model = FormSection
    extra = 1
    fields = [
        "code",
        "title",
        "sort_order",
        "is_repeatable",
        "max_repeat",
        "render_as",
        "is_active",
    ]
    show_change_link = True


class StepConditionInline(admin.TabularInline):
    model = StepCondition
    extra = 1
    fields = ["target_field", "operator", "value", "logic_operator", "is_active"]


class FormAssignmentInline(admin.TabularInline):
    model = FormAssignment
    extra = 1
    fields = [
        "form",
        "degree_level",
        "applicant_type",
        "program",
        "school",
        "sort_order",
        "is_required",
        "is_active",
    ]
    autocomplete_fields = ["form", "degree_level", "program", "school"]
    classes = ["collapse"]


class SectionAssignmentInline(admin.TabularInline):
    model = SectionAssignment
    extra = 1
    fields = [
        "section",
        "degree_level",
        "applicant_type",
        "program",
        "school",
        "sort_order",
        "is_required",
        "is_active",
    ]
    autocomplete_fields = ["section", "degree_level", "program", "school"]
    classes = ["collapse"]


@admin.register(SectionAssignment)
class SectionAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "section",
        "university",
        "degree_level",
        "applicant_type",
        "program",
        "is_required",
        "is_active",
    )
    list_filter = ("is_active", "is_required", "applicant_type", "degree_level")
    search_fields = ("section__title", "section__code", "applicant_type")


class DynamicWorkflowStepInline(admin.TabularInline):
    model = DynamicWorkflowStep
    extra = 1
    fields = [
        "code",
        "name",
        "step_type",
        "form",
        "sort_order",
        "is_required",
        "is_skippable",
        "group",
        "is_active",
    ]
    autocomplete_fields = ["form"]
    show_change_link = True




@admin.register(AdmissionCycle)
class AdmissionCycleAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "code",
        "academic_year",
        "term",
        "application_start",
        "application_deadline",
        "deadline_type",
        "is_active",
        "is_open",
    ]
    list_filter = ["is_active", "is_open", "deadline_type", "academic_year"]
    search_fields = ["name", "code"]
    prepopulated_fields = {"code": ("name",)}


@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ["email", "first_name", "last_name", "email_verified", "created_at"]
    list_filter = ["email_verified"]
    search_fields = ["email", "first_name", "last_name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = [
        "Reference_id",
        "applicant",
        "university",
        "degree_level",
        "program",
        "applicant_type",
        "status",
        "progress_pct",
        "created_date",
    ]
    list_filter = ["status", "applicant_type", "university", "degree_level"]
    search_fields = ["Reference_id", "applicant__email", "applicant__first_name"]
    readonly_fields = ["Reference_id", "created_date", "updated_date"]
    fieldsets = [
        (None, {"fields": ["applicant", "Reference_id", "status", "progress_pct"]}),
        (
            "Program",
            {
                "fields": [
                    ("university", "campus_name"),
                    ("degree_level", "program"),
                    ("school", "department"),
                    "admission_cycle",
                ]
            },
        ),
        ("Classification", {"fields": ["applicant_type"]}),
        (
            "Military",
            {
                "fields": [
                    "military_status",
                    "branch_of_service",
                    "service_start_date",
                    "service_end_date",
                    "va_benefits",
                    "gi_bill_chapter",
                    "tuition_assistance",
                ]
            },
        ),
        ("Residency", {"fields": ["residency_status"]}),
        ("Financial", {"fields": ["fee_waiver_requested", "fee_waiver_approved"]}),
        ("Dates", {"fields": ["submitted_date", "created_date", "updated_date"]}),
        ("Archive", {"fields": ["is_archived"]}),
    ]


@admin.register(ApplicantProfile)
class ApplicantProfileAdmin(admin.ModelAdmin):
    list_display = ["applicant", "gender", "nationality", "profile_completed"]
    search_fields = ["applicant__email", "applicant__first_name"]




@admin.register(FormDefinition)
class FormDefinitionAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "name",
        "version",
        "sort_order",
        "is_active",
        "section_count",
        "assignment_count",
    ]
    list_filter = ["is_active"]
    search_fields = ["code", "name"]
    prepopulated_fields = {"code": ("name",)}
    inlines = [FormSectionInline, FormAssignmentInline]
    fieldsets = [
        (None, {"fields": ["code", "name", "description", "icon"]}),
        ("Configuration", {"fields": ["sort_order", "is_active", "version"]}),
    ]

    def section_count(self, obj: FormDefinition) -> int:
        return obj.sections.count()
    section_count.short_description = "Sections"

    def assignment_count(self, obj: FormDefinition) -> int:
        return obj.assignments.count()
    assignment_count.short_description = "Assignments"


@admin.register(FormSection)
class FormSectionAdmin(admin.ModelAdmin):
    list_display = ["title", "form", "code", "sort_order", "is_active"]
    list_filter = ["is_active", "form"]
    search_fields = ["title", "code", "form__name"]
    autocomplete_fields = ["form"]
    inlines = [FormFieldInline, SectionAssignmentInline]


@admin.register(FormField)
class FormFieldAdmin(admin.ModelAdmin):
    list_display = ["label", "code", "section", "field_type", "sort_order", "is_active"]
    list_filter = ["field_type", "is_active", "section__form"]
    search_fields = ["label", "code", "section__title"]
    autocomplete_fields = ["section"]
    inlines = [FieldChoiceInline, ValidationRuleInline, VisibilityRuleInline]
    fieldsets = [
        (None, {"fields": ["section", "code", "label", "placeholder", "help_text"]}),
        ("Type & Layout", {"fields": ["field_type", "layout_width", "css_class", "rows"]}),
        ("Values", {"fields": ["default_value", "prefix_text", "suffix_text"]}),
        ("File Config", {"fields": ["max_file_size_mb", "allowed_extensions"]}),
        ("Data Source", {"fields": ["data_source"]}),
        ("Behavior", {"fields": ["sort_order", "is_active", "is_readonly", "is_encrypted"]}),
    ]


@admin.register(FormResponse)
class FormResponseAdmin(admin.ModelAdmin):
    list_display = ["application", "form", "section", "repeat_index", "is_complete", "updated_at"]
    list_filter = ["is_complete", "form", "section"]
    search_fields = ["application__Reference_id"]
    autocomplete_fields = ["application", "form", "section"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(FieldResponse)
class FieldResponseAdmin(admin.ModelAdmin):
    list_display = ["response", "field", "short_value", "updated_at"]
    list_filter = ["field__section__form"]
    search_fields = ["response__application__Reference_id", "field__label"]
    autocomplete_fields = ["response", "field"]
    readonly_fields = ["created_at", "updated_at"]

    def short_value(self, obj: FieldResponse) -> str:
        return str(obj.value)[:80] if obj.value else ""
    short_value.short_description = "Value"




@admin.register(WorkflowDefinition)
class WorkflowDefinitionAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "name",
        "university",
        "degree_level",
        "applicant_type",
        "program",
        "is_default",
        "is_active",
        "version",
    ]
    list_filter = ["is_active", "is_default", "university", "degree_level"]
    search_fields = ["code", "name"]
    prepopulated_fields = {"code": ("name",)}
    inlines = [DynamicWorkflowStepInline]
    fieldsets = [
        (None, {"fields": ["code", "name", "description"]}),
        ("Scope", {"fields": [("university", "degree_level"), ("applicant_type", "program")]}),
        ("Settings", {"fields": ["is_active", "is_default", "version"]}),
    ]




@admin.register(DocumentRequirement)
class DocumentRequirementAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "name",
        "category",
        "university",
        "degree_level",
        "applicant_type",
        "program",
        "is_required",
        "is_active",
    ]
    list_filter = ["category", "is_required", "is_active", "university", "degree_level"]
    search_fields = ["name", "code"]
    fieldsets = [
        (None, {"fields": ["code", "name", "description", "category"]}),
        (
            "Scope",
            {"fields": [("university", "degree_level"), ("applicant_type", "program")]},
        ),
        (
            "Requirements",
            {"fields": ["is_required", "max_file_size_mb", "allowed_extensions", "max_files"]},
        ),
        ("Display", {"fields": ["sort_order", "is_active"]}),
    ]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["file_name", "application", "doc_type", "file_size", "is_verified", "uploaded_at"]
    list_filter = ["is_verified", "doc_type"]
    search_fields = ["file_name", "application__Reference_id"]
    readonly_fields = ["uploaded_at"]




@admin.register(EssayPrompt)
class EssayPromptAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "essay_type",
        "university",
        "degree_level",
        "applicant_type",
        "program",
        "is_required",
        "is_active",
    ]
    list_filter = ["essay_type", "is_required", "is_active", "university", "degree_level"]
    search_fields = ["title", "essay_type", "prompt_text"]
    fieldsets = [
        (None, {"fields": ["code", "title", "essay_type", "prompt_text"]}),
        (
            "Scope",
            {"fields": [("university", "degree_level"), ("applicant_type", "program")]},
        ),
        ("Requirements", {"fields": ["min_words", "max_words", "is_required"]}),
        ("Display", {"fields": ["sort_order", "is_active"]}),
    ]


@admin.register(ApplicationEssay)
class ApplicationEssayAdmin(admin.ModelAdmin):
    list_display = ["application", "essay_type", "word_count", "is_complete", "updated_at"]
    list_filter = ["is_complete", "essay_type"]
    search_fields = ["application__Reference_id", "essay_type"]
    readonly_fields = ["word_count", "created_at", "updated_at"]




@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ["transaction_id", "application", "amount", "currency", "status", "paid_at"]
    list_filter = ["status", "currency"]
    search_fields = ["transaction_id", "application__Reference_id"]


@admin.register(FeeWaiver)
class FeeWaiverAdmin(admin.ModelAdmin):
    list_display = ["application", "waiver_type", "is_approved", "approved_by", "created_at"]
    list_filter = ["is_approved", "waiver_type"]
    search_fields = ["application__Reference_id"]


@admin.register(ApplicationFee)
class ApplicationFeeAdmin(admin.ModelAdmin):
    list_display = ["university", "degree_level", "amount", "currency", "waiver_available"]
    list_filter = ["currency", "waiver_available"]
    search_fields = ["university__university_name", "degree_level__degree_name"]



@admin.register(ApplicationChecklistItem)
class ApplicationChecklistItemAdmin(admin.ModelAdmin):
    list_display = ["application", "code", "label", "item_type", "is_required", "is_completed"]
    list_filter = ["is_required", "is_completed", "item_type"]
    search_fields = ["application__Reference_id", "label"]


@admin.register(ApplicationReviewAssignment)
class ApplicationReviewAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        "application", "reviewer", "assigned_by", "status",
        "is_verified", "assigned_at", "completed_at",
    ]
    list_filter = ["status", "is_verified"]
    search_fields = [
        "application__Reference_id",
        "reviewer__username",
        "reviewer__first_name",
        "reviewer__last_name",
    ]
    list_select_related = ("application", "reviewer", "assigned_by")
    readonly_fields = ["assigned_at", "started_at", "completed_at", "updated_at"]


@admin.register(MaterialRequest)
class MaterialRequestAdmin(admin.ModelAdmin):
    list_display = ["application", "requested_by", "doc_type", "requirement", "status", "requested_at", "fulfilled_at"]
    list_filter = ["status", "doc_type"]
    search_fields = ["application__Reference_id", "requested_by__username", "message"]
    list_select_related = ("application", "requested_by", "requirement")


@admin.register(FieldCorrectionRequest)
class FieldCorrectionRequestAdmin(admin.ModelAdmin):
    list_display = ["application", "requested_by", "status", "requested_at"]
    list_filter = ["status"]
    search_fields = ["application__Reference_id", "requested_by__username", "message"]
    list_select_related = ("application", "requested_by")


@admin.register(FieldReview)
class FieldReviewAdmin(admin.ModelAdmin):
    list_display = ["application", "field_label", "status", "reviewed_by", "reviewed_at"]
    list_filter = ["status"]
    search_fields = ["application__Reference_id", "field_response__field__label"]
    list_select_related = ("application", "field_response__field", "reviewed_by")

    @admin.display(description="Field")
    def field_label(self, obj):
        return obj.field_response.field.label


@admin.register(ApplicantTypeRequirement)
class ApplicantTypeRequirementAdmin(admin.ModelAdmin):
    list_display = ("applicant_type", "degree_level", "requires_transcript",
                    "requires_essay", "is_active")
    list_filter = ("applicant_type", "degree_level", "is_active")
    search_fields = ("applicant_type",)
    list_editable = ("is_active",)


@admin.register(ProgramRequirement)
class ProgramRequirementAdmin(admin.ModelAdmin):
    list_display = ("program", "degree_level", "min_gpa", "is_active")
    list_filter = ("degree_level", "is_active")
    search_fields = ("program__program_name",)

