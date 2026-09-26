from django.contrib import admin
# ==== ELSA CODE START ====
from .Elsa_Faculty.admin import *
from Research.Elsa_research.admin import *
# ===== ELSA CODE END =====
## Leo's code start ##
from .leo.admin import *

## Leo's code end ##


from .models import (
    FacultyRank, FacultyProfile, FacultyAppointment, FacultyEducation,
    FacultyCourseAssignment, FacultyResearch, FacultyGrant,
    FacultyPublication, FacultyOfficeHours, FacultyCommittee,
    FacultyEvaluation,
)

class FacultyAppointmentInline(admin.TabularInline):
    model = FacultyAppointment
    extra = 0

class FacultyEducationInline(admin.TabularInline):
    model = FacultyEducation
    extra = 0

class FacultyCourseAssignmentInline(admin.TabularInline):
    model = FacultyCourseAssignment
    extra = 0

class FacultyResearchInline(admin.TabularInline):
    model = FacultyResearch
    extra = 0

class FacultyGrantInline(admin.TabularInline):
    model = FacultyGrant
    extra = 0

class FacultyPublicationInline(admin.TabularInline):
    model = FacultyPublication
    extra = 0

class FacultyOfficeHoursInline(admin.TabularInline):
    model = FacultyOfficeHours
    extra = 0

class FacultyCommitteeInline(admin.TabularInline):
    model = FacultyCommittee
    extra = 0

class FacultyEvaluationInline(admin.TabularInline):
    model = FacultyEvaluation
    extra = 0


@admin.register(FacultyRank)
class FacultyRankAdmin(admin.ModelAdmin):
    list_display = ("rank_name", "tenure_track")
    search_fields = ("rank_name",)


@admin.register(FacultyProfile)
class FacultyProfileAdmin(admin.ModelAdmin):
    list_display = (
        "employee_id", "get_full_name", "email",
        "faculty_rank", "employment_status", "hire_date",
    )
    list_filter = ("employment_status", "faculty_rank")
    search_fields = (
        "employee_id", "email",
        "user__first_name", "user__last_name",
    )
    inlines = [
        FacultyAppointmentInline,
        FacultyEducationInline,
        FacultyCourseAssignmentInline,
        FacultyResearchInline,
        FacultyGrantInline,
        FacultyPublicationInline,
        FacultyOfficeHoursInline,
        FacultyCommitteeInline,
        FacultyEvaluationInline,
    ]

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = "Full Name"

@admin.register(FacultyAppointment)
class FacultyAppointmentAdmin(admin.ModelAdmin):
    list_display = ("faculty", "appointment_type", "department_id", "start_date", "end_date", "percentage_effort")
    list_filter = ("appointment_type",)
    search_fields = ("faculty__employee_id",)


@admin.register(FacultyEducation)
class FacultyEducationAdmin(admin.ModelAdmin):
    list_display = ("faculty", "degree", "institution_name", "field_of_study", "graduation_year")
    search_fields = ("faculty__employee_id", "degree", "institution_name")


@admin.register(FacultyCourseAssignment)
class FacultyCourseAssignmentAdmin(admin.ModelAdmin):
    list_display = ("faculty", "course_section_id", "semester_id", "role")
    list_filter = ("role",)
    search_fields = ("faculty__employee_id",)


@admin.register(FacultyResearch)
class FacultyResearchAdmin(admin.ModelAdmin):
    list_display = ("faculty", "research_title", "research_area", "start_date", "end_date", "status")
    list_filter = ("status",)
    search_fields = ("faculty__employee_id", "research_title", "research_area")


@admin.register(FacultyGrant)
class FacultyGrantAdmin(admin.ModelAdmin):
    list_display = ("faculty", "grant_title", "sponsor", "grant_amount", "award_date", "end_date")
    search_fields = ("faculty__employee_id", "grant_title", "sponsor")


@admin.register(FacultyPublication)
class FacultyPublicationAdmin(admin.ModelAdmin):
    list_display = ("faculty", "title", "publication_type", "journal_or_conference", "publication_date")
    list_filter = ("publication_type",)
    search_fields = ("faculty__employee_id", "title", "journal_or_conference")


@admin.register(FacultyOfficeHours)
class FacultyOfficeHoursAdmin(admin.ModelAdmin):
    list_display = ("faculty", "day_of_week", "start_time", "end_time", "location")
    list_filter = ("day_of_week",)
    search_fields = ("faculty__employee_id",)


@admin.register(FacultyCommittee)
class FacultyCommitteeAdmin(admin.ModelAdmin):
    list_display = ("faculty", "committee_name", "role", "start_date", "end_date")
    list_filter = ("role",)
    search_fields = ("faculty__employee_id", "committee_name")


@admin.register(FacultyEvaluation)
class FacultyEvaluationAdmin(admin.ModelAdmin):
    list_display = ("faculty", "evaluation_period", "teaching_score", "research_score", "service_score", "overall_rating")
    list_filter = ("overall_rating",)
    search_fields = ("faculty__employee_id", "evaluation_period")
