from django.contrib import admin
from .models import *

@admin.register(ResearchCommittee)
class ResearchCommitteeAdmin(admin.ModelAdmin):
    list_display = ("faculty", "department", "role", "is_active")
    list_filter = ("department", "role", "is_active")
    search_fields = ("faculty__user__first_name", "faculty__user__last_name")


@admin.register(ResearchOpportunity)
class ResearchOpportunityAdmin(admin.ModelAdmin):
    list_display = ("title", "department", "faculty", "status", "project_status")
    list_filter = ("status", "project_status", "department")
    search_fields = ("title", "category")


@admin.register(ResearchOpportunityDocument)
class ResearchOpportunityDocumentAdmin(admin.ModelAdmin):
    list_display = ("opportunity", "uploaded_at")


@admin.register(ResearchMilestone)
class ResearchMilestoneAdmin(admin.ModelAdmin):
    list_display = ("title", "research", "deadline", "status")


@admin.register(StudentMilestoneAssignment)
class StudentMilestoneAssignmentAdmin(admin.ModelAdmin):
    list_display = ("student", "milestone", "status", "student_progress")


@admin.register(StudentProgressReport)
class StudentProgressReportAdmin(admin.ModelAdmin):
    list_display = ("title", "assignment", "progress_percentage", "status")


@admin.register(StudentReportAttachment)
class StudentReportAttachmentAdmin(admin.ModelAdmin):
    list_display = ("report", "uploaded_at")


@admin.register(StudentResearchApplication)
class StudentResearchApplicationAdmin(admin.ModelAdmin):
    list_display = ("reference_number", "student", "research_opportunity", "status")
    list_filter = ("status",)
    search_fields = ("reference_number", "student__user__first_name")


@admin.register(ResearchTeam)
class ResearchTeamAdmin(admin.ModelAdmin):
    list_display = ("team_name", "research_details")


@admin.register(ResearchTeamMember)
class ResearchTeamMemberAdmin(admin.ModelAdmin):
    list_display = ("team", "faculty", "student", "role")


@admin.register(ResearchFunding)
class ResearchFundingAdmin(admin.ModelAdmin):
    list_display = ("research", "funding_source", "amount", "award_date")


@admin.register(StudentResearchPublication)
class StudentResearchPublicationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "get_journal_name",
        "get_submission_date",
    )

    def get_journal_name(self, obj):
        if hasattr(obj, "submission"):
            return obj.submission.journal_name
        return "-"

    get_journal_name.short_description = "Journal"

    def get_submission_date(self, obj):
        if hasattr(obj, "submission"):
            return obj.submission.submission_date
        return "-"

    get_submission_date.short_description = "Submission Date"


@admin.register(ResearchProgress)
class ResearchProgressAdmin(admin.ModelAdmin):
    list_display = ("research", "milestone", "progress_percentage", "submission_date")


@admin.register(ResearchPresentation)
class ResearchPresentationAdmin(admin.ModelAdmin):
    list_display = ("event_name", "research", "presentation_date", "award")
    search_fields = ("event_name", "research__title")