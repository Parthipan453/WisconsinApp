from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserSession, UserNotificationPreference, UserAuditLog, UserRole, UserRoleAssignment
from .Alan.admin import *
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin 
from .models import User
from .Jack.admin import *
from .Leo_admin.admin import *
from .models import Firearm 

from .models import OlympicAthlete, OlympicPerformance,Tournament, TournamentInvitation, TournamentParticipant, TournamentApplication

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_student",
        "is_faculty",
        "is_staff",
        "is_admin",
        "is_medical_staff",
        "is_super_admin",
        "account_status",
    )
    list_filter = (
        "is_student",
        "is_faculty",
        "is_staff",
        "is_admin",
        "is_medical_staff",
        "is_super_admin",
        "account_status",
        "gender",
    )
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "university_id",
    )
    fieldsets = (
        (None, {
            "fields": ("username", "password")
        }),
        ("Personal info", {
            "fields": (
                "first_name",
                "middle_name",
                "last_name",
                "ssn_number",
                "email",
                "mobile_number",
                "profile_photo",
                "date_of_birth",
                "gender",
            )
        }),
        ("University", {
            "fields": ("university_id",)
        }),
        ("Status", {
            "fields": (
                "account_status",
                "email_verified",
                "mobile_verified",
                "is_active",
            )
        }),
        ("User Type", {
            "fields": (
                "is_student",
                "is_faculty",
                "is_staff",
                "is_admin",
                "is_super_admin",
                "is_medical_staff",
            )
        }),
        ("Permissions", {
            "fields": (
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Important dates", {
            "fields": (
                "last_login",
                "date_joined",
            )
        }),
    )

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "login_time", "logout_time", "device_type", "browser")
    search_fields = ("user__username",)

@admin.register(UserNotificationPreference)
class UserNotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "email_enabled", "sms_enabled", "push_enabled", "emergency_alert_enabled")

@admin.register(UserAuditLog)
class UserAuditLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "timestamp")
    search_fields = ("user__username", "action")

@admin.register(OlympicAthlete)
class OlympicAthleteAdmin(admin.ModelAdmin):
    pass

@admin.register(OlympicPerformance)
class OlympicPerformanceAdmin(admin.ModelAdmin):
    pass

@admin.register(UserRoleAssignment)
class UserRoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "start_date", "end_date", "active")

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("role_name", "created_at")

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    pass

@admin.register(TournamentInvitation)
class TournamentInvitationAdmin(admin.ModelAdmin):
    pass



@admin.register(TournamentParticipant)
class TournamentParticipantAdmin(admin.ModelAdmin):
    pass

@admin.register(TournamentApplication)
class TournamentApplicationAdmin(admin.ModelAdmin):
    pass


@admin.register(Firearm)
class FirearmAdmin(admin.ModelAdmin):
    list_display = (
        "firearm_name",
        "serial_number",
        "firearm_type",
        "manufacturer",
        "model_name",
        "caliber",
        "current_status",
        "user",
        "purchase_date",
        "created_at",
    )

    list_filter = (
        "firearm_type",
        "current_status",
        "acquisition_method",
        "purchase_date",
        "created_at",
    )

    search_fields = (
        "firearm_name",
        "serial_number",
        "manufacturer",
        "model_name",
        "caliber",
        "user__username",
        "user__first_name",
        "user__last_name",
        "location_name",
        "building_name",
        "room_number",
    )

    readonly_fields = (
        "uuid",
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

    list_per_page = 25







from django.contrib import admin
from Students.models import MaintenanceRequest, RoomInspection


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'student', 'issue_type', 'priority', 'status', 'created_at')
    list_filter = ('status', 'priority', 'issue_type', 'created_at')
    search_fields = ('student__full_name', 'student__username', 'room__room_number', 'description')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(RoomInspection)
class RoomInspectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'student', 'inspection_date', 'status')
    list_filter = ('status', 'inspection_date')
    search_fields = ('room__room_number', 'student__full_name', 'inspector_name')
    readonly_fields = ('uuid', 'created_at', 'updated_at')
    ordering = ('-inspection_date',)    
