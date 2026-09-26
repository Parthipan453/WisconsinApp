# Leo's Code Start
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count

from .models import (
    PhD,
    PhDStudent,
    ResearchAdvisor,
    DoctoralCommittee,
    CommitteeMember,
    PreliminaryExamination,
    DissertationProposal,
    DoctoralCandidacy,
    PhDMilestone,
    Dissertation,
    ResearchPublication,
    AnnualProgressReview,
    DissertationDefense,
    Graduation,
)


@admin.register(PhD)
class PhDAdmin(admin.ModelAdmin):
    list_display = (
        "phd_program_id",
        "program_name",
        "department",
        "degree_type",
        "total_credits_required",
        "duration_years",
        "status",
        "student_count",
    )

    list_filter = (
        "status",
        "degree_type",
        "department",
    )

    search_fields = (
        "program_name",
        "department__department_name",
        "program_description",
    )

    readonly_fields = (
        "phd_program_id",
    )

    fieldsets = (
        ("Program Information", {
            "fields": ("program_name", "department", "degree_type")
        }),
        ("Requirements", {
            "fields": ("total_credits_required", "residency_requirement", "duration_years")
        }),
        ("Additional Information", {
            "fields": ("program_description", "status"),
            "classes": ("collapse",)
        }),
    )

    def student_count(self, obj):
        """Display the number of students in this program"""
        count = obj.phd_students.count()
        url = reverse("admin:Students_phdstudent_changelist") + f"?phd_program__id={obj.pk}"
        return format_html('<a href="{}">{} Students</a>', url, count)
    student_count.short_description = "Enrolled Students"


@admin.register(PhDStudent)
class PhDStudentAdmin(admin.ModelAdmin):
    list_display = (
        "phd_student_id",
        "student",
        "phd_program",
        "advisor",
        "cohort_year",
        "current_status",
        "admission_date",
        "expected_graduation_date",
    )

    list_filter = (
        "current_status",
        "phd_program",
        "cohort_year",
        "advisor",
    )

    search_fields = (
        "student__student_number",
        "student__user__first_name",
        "student__user__last_name",
        "phd_program__program_name",
    )

    readonly_fields = (
        "phd_student_id",
    )

    fieldsets = (
        ("Student Information", {
            "fields": ("student", "phd_program")
        }),
        ("Advisor & Academic Details", {
            "fields": ("advisor", "admission_date", "cohort_year")
        }),
        ("Status", {
            "fields": ("current_status", "expected_graduation_date")
        }),
    )

    def get_queryset(self, request):
        """Optimize queries with select_related"""
        return super().get_queryset(request).select_related(
            "student",
            "student__user",
            "phd_program",
            "advisor",
            "advisor__user",
        )


@admin.register(ResearchAdvisor)
class ResearchAdvisorAdmin(admin.ModelAdmin):
    list_display = (
        "advisor_id",
        "faculty",
        "research_area",
        "lab_name",
        "available_slots",
        "publications_count",
        "advisee_count",
    )

    list_filter = (
        "available_slots",
        "research_area",
    )

    search_fields = (
        "faculty__user__first_name",
        "faculty__user__last_name",
        "faculty__employee_id",
        "research_area",
        "lab_name",
    )

    readonly_fields = (
        "advisor_id",
    )

    fieldsets = (
        ("Faculty Information", {
            "fields": ("faculty",)
        }),
        ("Research Details", {
            "fields": ("research_area", "lab_name")
        }),
        ("Capacity & Metrics", {
            "fields": ("available_slots", "publications_count")
        }),
    )

    def advisee_count(self, obj):
        """Count how many PhD students this advisor supervises"""
        count = obj.faculty.phd_advisees.count()
        url = reverse("admin:Students_phdstudent_changelist") + f"?advisor__id={obj.faculty.pk}"
        return format_html('<a href="{}">{} Students</a>', url, count)
    advisee_count.short_description = "Current Advisees"


@admin.register(DoctoralCommittee)
class DoctoralCommitteeAdmin(admin.ModelAdmin):
    list_display = (
        "committee_id",
        "phd_student",
        "chair_faculty",
        "formation_date",
        "approval_status",
        "member_count",
    )

    list_filter = (
        "approval_status",
        "formation_date",
    )

    search_fields = (
        "phd_student__student__student_number",
        "phd_student__student__user__first_name",
        "phd_student__student__user__last_name",
        "chair_faculty__user__first_name",
        "chair_faculty__user__last_name",
    )

    readonly_fields = (
        "committee_id",
    )

    fieldsets = (
        ("Committee Information", {
            "fields": ("phd_student", "chair_faculty", "formation_date")
        }),
        ("Status", {
            "fields": ("approval_status",)
        }),
    )

    def member_count(self, obj):
        """Display number of committee members"""
        count = obj.committee_members.count()
        url = reverse("admin:Students_committeemember_changelist") + f"?committee__id={obj.pk}"
        return format_html('<a href="{}">{} Members</a>', url, count)
    member_count.short_description = "Committee Members"


@admin.register(CommitteeMember)
class CommitteeMemberAdmin(admin.ModelAdmin):
    list_display = (
        "member_id",
        "committee",
        "faculty",
        "role",
        "department",
    )

    list_filter = (
        "role",
        "department",
    )

    search_fields = (
        "committee__phd_student__student__student_number",
        "committee__phd_student__student__user__first_name",
        "committee__phd_student__student__user__last_name",
        "faculty__user__first_name",
        "faculty__user__last_name",
        "faculty__employee_id",
    )

    readonly_fields = (
        "member_id",
    )

    fieldsets = (
        ("Committee Association", {
            "fields": ("committee",)
        }),
        ("Member Details", {
            "fields": ("faculty", "role", "department")
        }),
    )


@admin.register(PreliminaryExamination)
class PreliminaryExaminationAdmin(admin.ModelAdmin):
    list_display = (
        "prelim_exam_id",
        "phd_student",
        "exam_type",
        "exam_date",
        "start_time",
        "end_time",
        "status",
        "result",
        "is_published",
        "evaluation_count",
    )

    list_filter = (
        "exam_type",
        "status",
        "result",
        "is_published",
        "exam_date",
    )

    search_fields = (
        "phd_student__student__student_number",
        "phd_student__student__user__first_name",
        "phd_student__student__user__last_name",
        "title",
        "venue",
    )

    readonly_fields = (
        "prelim_exam_id",
    )

    fieldsets = (
        ("Student & Exam Details", {
            "fields": ("phd_student", "exam_type", "title", "description")
        }),
        ("Schedule", {
            "fields": ("exam_date", "start_time", "end_time", "venue")
        }),
        ("Status & Results", {
            "fields": ("status", "result", "is_published", "remarks")
        }),
    )

    def evaluation_count(self, obj):
        """Display number of evaluations submitted"""
        count = obj.evaluations.count()
        url = reverse("admin:Faculty_preliminaryexamevaluation_changelist") + f"?examination__id={obj.pk}"
        return format_html('<a href="{}">{} Evaluations</a>', url, count)
    evaluation_count.short_description = "Evaluations"


@admin.register(DissertationProposal)
class DissertationProposalAdmin(admin.ModelAdmin):
    list_display = (
        "proposal_id",
        "phd_student",
        "proposal_title",
        "submission_date",
        "hearing_date",
        "result",
        "approved_by",
    )

    list_filter = (
        "result",
        "submission_date",
        "hearing_date",
    )

    search_fields = (
        "phd_student__student__student_number",
        "phd_student__student__user__first_name",
        "phd_student__student__user__last_name",
        "proposal_title",
        "abstract",
    )

    readonly_fields = (
        "proposal_id",
    )

    fieldsets = (
        ("Proposal Details", {
            "fields": ("phd_student", "proposal_title", "abstract")
        }),
        ("Schedule", {
            "fields": ("submission_date", "hearing_date")
        }),
        ("Decision", {
            "fields": ("result", "approved_by")
        }),
    )


@admin.register(DoctoralCandidacy)
class DoctoralCandidacyAdmin(admin.ModelAdmin):
    list_display = (
        "candidacy_id",
        "phd_student",
        "candidacy_date",
        "candidacy_status",
        "approval_date",
    )

    list_filter = (
        "candidacy_status",
        "candidacy_date",
        "approval_date",
    )

    search_fields = (
        "phd_student__student__student_number",
        "phd_student__student__user__first_name",
        "phd_student__student__user__last_name",
    )

    readonly_fields = (
        "candidacy_id",
    )

    fieldsets = (
        ("Candidacy Information", {
            "fields": ("phd_student", "candidacy_date")
        }),
        ("Status", {
            "fields": ("candidacy_status", "approval_date")
        }),
    )


@admin.register(PhDMilestone)
class PhDMilestoneAdmin(admin.ModelAdmin):
    list_display = (
        "milestone_id",
        "phd_student",
        "milestone_name",
        "status",
        "completion_date",
    )

    list_filter = (
        "status",
        "completion_date",
    )

    search_fields = (
        "phd_student__student__student_number",
        "phd_student__student__user__first_name",
        "phd_student__student__user__last_name",
        "milestone_name",
    )

    readonly_fields = (
        "milestone_id",
    )

    fieldsets = (
        ("Milestone Information", {
            "fields": ("phd_student", "milestone_name")
        }),
        ("Status", {
            "fields": ("status", "completion_date")
        }),
    )


@admin.register(Dissertation)
class DissertationAdmin(admin.ModelAdmin):
    list_display = (
        "dissertation_id",
        "phd_student",
        "dissertation_title",
        "submission_date",
        "status",
        "current_version",
    )

    list_filter = (
        "status",
        "submission_date",
    )

    search_fields = (
        "phd_student__student__student_number",
        "phd_student__student__user__first_name",
        "phd_student__student__user__last_name",
        "dissertation_title",
        "abstract",
    )

    readonly_fields = (
        "dissertation_id",
    )

    fieldsets = (
        ("Dissertation Information", {
            "fields": ("phd_student", "dissertation_title", "abstract")
        }),
        ("Submission Details", {
            "fields": ("submission_date", "current_version", "status")
        }),
    )


@admin.register(ResearchPublication)
class ResearchPublicationAdmin(admin.ModelAdmin):
    list_display = (
        "publication_id",
        "phd_student",
        "title",
        "journal",
        "publication_date",
        "doi",
        "indexed_status",
    )

    list_filter = (
        "indexed_status",
        "publication_date",
    )

    search_fields = (
        "phd_student__student__student_number",
        "phd_student__student__user__first_name",
        "phd_student__student__user__last_name",
        "title",
        "journal",
        "doi",
    )

    readonly_fields = (
        "publication_id",
    )

    fieldsets = (
        ("Publication Details", {
            "fields": ("phd_student", "title", "journal")
        }),
        ("Publication Information", {
            "fields": ("publication_date", "doi", "indexed_status")
        }),
    )


@admin.register(AnnualProgressReview)
class AnnualProgressReviewAdmin(admin.ModelAdmin):
    list_display = (
        "review_id",
        "phd_student",
        "review_year",
        "progress_score",
        "status",
        "committee_comments_preview",
    )

    list_filter = (
        "status",
        "review_year",
    )

    search_fields = (
        "phd_student__student__student_number",
        "phd_student__student__user__first_name",
        "phd_student__student__user__last_name",
        "committee_comments",
    )

    readonly_fields = (
        "review_id",
    )

    fieldsets = (
        ("Review Information", {
            "fields": ("phd_student", "review_year")
        }),
        ("Performance Metrics", {
            "fields": ("progress_score", "status")
        }),
        ("Comments", {
            "fields": ("committee_comments",)
        }),
    )

    def committee_comments_preview(self, obj):
        """Display truncated committee comments"""
        if obj.committee_comments:
            return obj.committee_comments[:50] + "..." if len(obj.committee_comments) > 50 else obj.committee_comments
        return "-"
    committee_comments_preview.short_description = "Comments"


@admin.register(DissertationDefense)
class DissertationDefenseAdmin(admin.ModelAdmin):
    list_display = (
        "defense_id",
        "phd_student",
        "defense_date",
        "location",
        "result",
        "committee_decision",
    )

    list_filter = (
        "result",
        "committee_decision",
        "defense_date",
    )

    search_fields = (
        "phd_student__student__student_number",
        "phd_student__student__user__first_name",
        "phd_student__student__user__last_name",
        "location",
        "final_comments",
    )

    readonly_fields = (
        "defense_id",
    )

    fieldsets = (
        ("Defense Information", {
            "fields": ("phd_student", "defense_date", "location")
        }),
        ("Results", {
            "fields": ("result", "committee_decision", "final_comments")
        }),
    )


@admin.register(Graduation)
class GraduationAdmin(admin.ModelAdmin):
    list_display = (
        "graduation_id",
        "phd_student",
        "graduation_date",
        "degree_awarded",
        "final_gpa",
        "dissertation_accepted",
    )

    list_filter = (
        "dissertation_accepted",
        "graduation_date",
    )

    search_fields = (
        "phd_student__student__student_number",
        "phd_student__student__user__first_name",
        "phd_student__student__user__last_name",
        "degree_awarded",
    )

    readonly_fields = (
        "graduation_id",
    )

    fieldsets = (
        ("Graduation Details", {
            "fields": ("phd_student", "graduation_date", "degree_awarded")
        }),
        ("Academic Performance", {
            "fields": ("final_gpa", "dissertation_accepted")
        }),
    )
