from django.contrib import admin
from Admin.models import User
from .models import (
    StaffProfile, StaffPosition, StaffAddress, StaffEmergencyContact,
    StaffDepartmentAssignment, StaffEducation, StaffCertification,
    StaffTraining, StaffPerformanceReview, StaffLeave,
    StaffPayroll, StaffAccessRole,Message, MessageRecipient, MessageThread, Announcement
)
#______Eric code______
from  Staff.Eric.admin import *
#_______Eric code end_____
class StaffPositionInline(admin.TabularInline):
    model = StaffPosition
    extra = 0

class StaffAddressInline(admin.TabularInline):
    model = StaffAddress
    extra = 0

class StaffEmergencyContactInline(admin.TabularInline):
    model = StaffEmergencyContact
    extra = 0

class StaffDepartmentAssignmentInline(admin.TabularInline):
    model = StaffDepartmentAssignment
    extra = 0

class StaffEducationInline(admin.TabularInline):
    model = StaffEducation
    extra = 0

class StaffCertificationInline(admin.TabularInline):
    model = StaffCertification
    extra = 0

class StaffTrainingInline(admin.TabularInline):
    model = StaffTraining
    extra = 0

class StaffLeaveInline(admin.TabularInline):
    model = StaffLeave
    extra = 0

class StaffPayrollInline(admin.TabularInline):
    model = StaffPayroll
    extra = 0

class StaffAccessRoleInline(admin.TabularInline):
    model = StaffAccessRole
    extra = 0

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = (
        "employee_id", "get_full_name", "work_email",
        "employment_status", "employment_type", "hire_date",
    )
    list_filter = ("employment_status", "employment_type")
    search_fields = (
        "employee_id", "work_email",
        "user__first_name", "user__last_name",
    )
    inlines = [
        StaffPositionInline,
        StaffAddressInline,
        StaffEmergencyContactInline,
        StaffDepartmentAssignmentInline,
        StaffEducationInline,
        StaffCertificationInline,
        StaffTrainingInline,
        StaffLeaveInline,
        StaffPayrollInline,
        StaffAccessRoleInline,
    ]

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = "Full Name"


@admin.register(StaffPosition)
class StaffPositionAdmin(admin.ModelAdmin):
    list_display = ("staff", "job_title", "job_code", "position_status", "position_start_date", "position_end_date")
    list_filter = ("position_status",)
    search_fields = ("staff__employee_id", "job_title", "job_code")


@admin.register(StaffAddress)
class StaffAddressAdmin(admin.ModelAdmin):
    list_display = ("staff", "address_type", "city", "state", "country")
    list_filter = ("address_type", "country")


@admin.register(StaffEmergencyContact)
class StaffEmergencyContactAdmin(admin.ModelAdmin):
    list_display = ("staff", "contact_name", "relationship", "phone_number", "priority")


@admin.register(StaffDepartmentAssignment)
class StaffDepartmentAssignmentAdmin(admin.ModelAdmin):
    list_display = ("staff", "department_id", "start_date", "end_date", "primary_assignment")
    list_filter = ("primary_assignment",)


@admin.register(StaffEducation)
class StaffEducationAdmin(admin.ModelAdmin):
    list_display = ("staff", "degree", "institution_name", "field_of_study", "graduation_year")


@admin.register(StaffCertification)
class StaffCertificationAdmin(admin.ModelAdmin):
    list_display = ("staff", "certification_name", "issuing_organization", "issue_date", "expiration_date")


@admin.register(StaffTraining)
class StaffTrainingAdmin(admin.ModelAdmin):
    list_display = ("staff", "training_title", "provider", "completion_date", "training_status")
    list_filter = ("training_status",)


@admin.register(StaffPerformanceReview)
class StaffPerformanceReviewAdmin(admin.ModelAdmin):
    list_display = ("staff", "review_period", "reviewer", "performance_rating", "review_date")
    list_filter = ("performance_rating",)
    search_fields = ("staff__employee_id", "review_period")


@admin.register(StaffLeave)
class StaffLeaveAdmin(admin.ModelAdmin):
    list_display = ("staff", "leave_type", "start_date", "end_date", "approval_status")
    list_filter = ("leave_type", "approval_status")


@admin.register(StaffPayroll)
class StaffPayrollAdmin(admin.ModelAdmin):
    list_display = ("staff", "pay_grade", "annual_salary", "pay_frequency", "effective_date")
    list_filter = ("pay_frequency",)


@admin.register(StaffAccessRole)
class StaffAccessRoleAdmin(admin.ModelAdmin):
    list_display = ("staff", "system_role", "assigned_date", "active")
    list_filter = ("system_role", "active")

@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "subject",
        "created_by",
        "created_at",
        "is_announcement",
    )
    list_filter = ("is_announcement",)
    search_fields = ("subject", "created_by__email", "created_by__first_name")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "thread",
        "sender",
        "sent_at",
    )
    list_filter = ("sent_at",)
    search_fields = (
        "thread__subject",
        "sender__email",
        "body",
    )


@admin.register(MessageRecipient)
class MessageRecipientAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "message",
        "recipient",
        "is_read",
        "archived",
        "read_at",
    )
    list_filter = (
        "is_read",
        "archived",
    )
    search_fields = (
        "recipient__email",
        "message__thread__subject",
    )


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "priority",
        "posted_by",
        "posted_at",
        "expires_at",
    )
    list_filter = (
        "priority",
        "posted_at",
    )
    search_fields = (
        "title",
        "body",
    )