# Faculty/leo/admin.py

# Standard Library Imports
# (None required for this file)

# Django Imports
from django.contrib import admin

# Local Imports - Faculty App Models Only
from .models import (
    Attendance,
    AttendanceSession,
    FacultyCoursework,
    CourseworkSubmission,
    CourseworkEvaluation,
    PreliminaryExamEvaluation,
    DissertationEvaluation,
    DissertationApproval,
    DissertationAdvisorFeedback,
    DissertationChairReplyFeedback,
    DissertationAdvisorAdvice,
)

# Faculty App Admin Configurations


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = (
        "faculty",
        "course",
        "section",
        "attendance_date",
        "get_day",
        "get_start_time",
        "get_end_time",
        "status",
    )

    list_filter = (
        "status",
        "attendance_date",
        "course",
    )

    search_fields = (
        "faculty__employee_id",
        "course__course_code",
        "course__course_name",
    )

    @admin.display(description="Day")
    def get_day(self, obj):
        from Students.models import Schedule

        schedule = Schedule.objects.filter(section_id=obj.section).first()
        if schedule:
            return schedule.get_day_of_week_display()
        return "-"

    @admin.display(description="Start Time")
    def get_start_time(self, obj):
        from Students.models import Schedule

        schedule = Schedule.objects.filter(section_id=obj.section).first()
        if schedule:
            return schedule.start_time.strftime("%H:%M")
        return "-"

    @admin.display(description="End Time")
    def get_end_time(self, obj):
        from Students.models import Schedule

        schedule = Schedule.objects.filter(section_id=obj.section).first()
        if schedule:
            return schedule.end_time.strftime("%H:%M")
        return "-"


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "attendance_session",
        "status",
    )

    list_filter = (
        "status",
        "attendance_session__attendance_date",
    )

    search_fields = (
        "student__student_number",
        "student__user__first_name",
        "student__user__last_name",
    )


@admin.register(FacultyCoursework)
class FacultyCourseworkAdmin(admin.ModelAdmin):
    list_display = (
        "faculty_coursework_id",
        "phd_student",
        "program",
        "coursework",
        "academic_year",
        "status",
        "progress_percentage",
        "start_date",
        "expected_completion_date",
        "completion_date",
    )

    list_filter = (
        "status",
        "coursework",
        "academic_year",
        "program",
    )

    search_fields = (
        "phd_student__student__student_number",
        "phd_student__student__user__first_name",
        "phd_student__student__user__last_name",
        "coursework__coursework_name",
        "program__program_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(CourseworkSubmission)
class CourseworkSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "submission_id",
        "coursework",
        "submitted_at",
        "status",
    )

    list_filter = (
        "status",
        "submitted_at",
    )

    search_fields = (
        "coursework__phd_student__student__student_number",
        "coursework__phd_student__student__user__first_name",
        "coursework__phd_student__student__user__last_name",
        "coursework__coursework__coursework_name",
    )

    readonly_fields = (
        "submitted_at",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Submission Details",
            {
                "fields": (
                    "coursework",
                    "submission_file",
                    "remarks",
                )
            },
        ),
        (
            "Submission Status",
            {
                "fields": (
                    "status",
                    "submitted_at",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(PreliminaryExamEvaluation)
class PreliminaryExamEvaluationAdmin(admin.ModelAdmin):
    list_display = (
        "evaluation_id",
        "examination",
        "faculty",
        "knowledge_score",
        "research_aptitude_score",
        "presentation_score",
        "technical_score",
        "recommendation",
        "is_submitted",
        "submitted_at",
    )

    list_filter = (
        "recommendation",
        "is_submitted",
        "submitted_at",
        "examination__exam_type",
    )

    search_fields = (
        "examination__phd_student__student__student_number",
        "examination__phd_student__student__user__first_name",
        "examination__phd_student__student__user__last_name",
        "faculty__user__first_name",
        "faculty__user__last_name",
        "faculty__employee_id",
    )

    readonly_fields = ("submitted_at",)

    fieldsets = (
        ("Examination Details", {"fields": ("examination", "faculty")}),
        (
            "Scores",
            {
                "fields": (
                    "knowledge_score",
                    "research_aptitude_score",
                    "presentation_score",
                    "technical_score",
                )
            },
        ),
        ("Evaluation", {"fields": ("comments", "recommendation", "is_submitted")}),
        (
            "System Information",
            {
                "fields": ("submitted_at",),
                "classes": ("collapse",),
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make key fields read-only after submission"""
        if obj and obj.is_submitted:
            return self.readonly_fields + (
                "examination",
                "faculty",
                "knowledge_score",
                "research_aptitude_score",
                "presentation_score",
                "technical_score",
                "comments",
                "recommendation",
                "is_submitted",
            )
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        """Override save to handle full_crud flag if needed"""
        if not change:  # New object
            obj.is_full_crud = True
        super().save_model(request, obj, form, change)


@admin.register(DissertationEvaluation)
class DissertationEvaluationAdmin(admin.ModelAdmin):
    list_display = (
        "evaluation_id",
        "dissertation",
        "committee_member",
        "score",
        "recommendation",
        "is_submitted",
        "submitted_at",
    )

    list_filter = (
        "recommendation",
        "is_submitted",
        "submitted_at",
    )

    search_fields = (
        "dissertation__phd_student__student__student_number",
        "dissertation__phd_student__student__user__first_name",
        "dissertation__phd_student__student__user__last_name",
        "committee_member__faculty__employee_id",
        "committee_member__faculty__user__first_name",
        "committee_member__faculty__user__last_name",
    )

    readonly_fields = (
        "submitted_at",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Dissertation Information",
            {
                "fields": (
                    "dissertation",
                    "committee_member",
                )
            },
        ),
        (
            "Evaluation",
            {
                "fields": (
                    "score",
                    "recommendation",
                    "remarks",
                    "is_submitted",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "submitted_at",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_submitted:
            return self.readonly_fields + (
                "dissertation",
                "committee_member",
                "score",
                "recommendation",
                "remarks",
                "is_submitted",
            )
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:
            obj.is_full_crud = True
        super().save_model(request, obj, form, change)


@admin.register(DissertationApproval)
class DissertationApprovalAdmin(admin.ModelAdmin):
    list_display = (
        "approval_id",
        "dissertation",
        "chair_faculty",
        "decision",
        "approved_at",
    )

    list_filter = (
        "decision",
        "approved_at",
    )

    search_fields = (
        "dissertation__phd_student__student__student_number",
        "dissertation__phd_student__student__user__first_name",
        "dissertation__phd_student__student__user__last_name",
        "chair_faculty__employee_id",
        "chair_faculty__user__first_name",
        "chair_faculty__user__last_name",
    )

    readonly_fields = (
        "approved_at",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Dissertation Information",
            {
                "fields": (
                    "dissertation",
                    "chair_faculty",
                )
            },
        ),
        (
            "Approval",
            {
                "fields": (
                    "decision",
                    "final_remarks",
                    "approved_at",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.is_full_crud = True
        super().save_model(request, obj, form, change)


@admin.register(CourseworkEvaluation)
class CourseworkEvaluationAdmin(admin.ModelAdmin):
    list_display = (
        "evaluation_id",
        "submission",
        "evaluated_by",
        "marks",
        "grade",
        "evaluated_at",
    )

    list_filter = (
        "grade",
        "evaluated_at",
    )

    search_fields = (
        "submission__coursework__phd_student__student__student_number",
        "submission__coursework__phd_student__student__user__first_name",
        "submission__coursework__phd_student__student__user__last_name",
        "submission__coursework__coursework__coursework_name",
        "evaluated_by__employee_id",
        "evaluated_by__user__first_name",
        "evaluated_by__user__last_name",
    )

    readonly_fields = (
        "grade",
        "evaluated_at",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Submission Information",
            {
                "fields": (
                    "submission",
                    "evaluated_by",
                )
            },
        ),
        (
            "Evaluation",
            {
                "fields": (
                    "marks",
                    "grade",
                    "faculty_feedback",
                    "evaluated_at",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.is_full_crud = True
        super().save_model(request, obj, form, change)


@admin.register(DissertationAdvisorFeedback)
class DissertationAdvisorFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "advisor_feedback_id",
        "dissertation",
        "advisor",
        "status",
        "is_submitted",
        "submitted_at",
    )

    list_filter = (
        "status",
        "is_submitted",
        "submitted_at",
    )

    search_fields = (
        "dissertation__phd_student__student__student_number",
        "advisor__employee_id",
        "advisor__user__first_name",
        "advisor__user__last_name",
    )

    readonly_fields = (
        "submitted_at",
        "created_at",
        "updated_at",
    )


@admin.register(DissertationChairReplyFeedback)
class DissertationChairReplyFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "chair_reply_feedback_id",
        "dissertation",
        "chair_faculty",
        "decision",
        "status",
        "is_submitted",
        "replied_at",
    )

    list_filter = (
        "decision",
        "status",
        "is_submitted",
        "replied_at",
    )

    search_fields = (
        "dissertation__phd_student__student__student_number",
        "chair_faculty__employee_id",
        "chair_faculty__user__first_name",
        "chair_faculty__user__last_name",
    )

    readonly_fields = (
        "replied_at",
        "created_at",
        "updated_at",
    )


@admin.register(DissertationAdvisorAdvice)
class DissertationAdvisorAdviceAdmin(admin.ModelAdmin):
    list_display = (
        "advice_id",
        "dissertation",
        "advisor",
        "is_submitted",
        "submitted_at",
    )

    list_filter = (
        "is_submitted",
        "submitted_at",
    )

    search_fields = (
        "dissertation__phd_student__student__student_number",
        "advisor__employee_id",
        "advisor__user__first_name",
        "advisor__user__last_name",
    )

    readonly_fields = (
        "submitted_at",
        "created_at",
        "updated_at",
    )
