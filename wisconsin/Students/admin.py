

# *************************************** Arun Code ********************************************************** 

from django.contrib import admin
from .models import (
    StudentProfile, StudentAddress, StudentEmergencyContact,
    StudentAcademicProfile, StudentEnrollment, StudentFinancialAid,
    StudentHousing, StudentResearchProfile, StudentOrganization, StudentOrganizationMembership,
    StudentCareerProfile, StudentDocument, StudentFee, StudentFeePayment,    Semester,
    CourseSection,
    Schedule,
    CourseMaterial,
    SupportTicket,
)
# from .models import Semester, CourseSection, Schedule
from Admin.bela_admin.models import Course
from .models import (
    Exam,
    ExamRoomAllocation,
    ExamInvigilator,
    ExamSeat,
    ExamAttendance,
    ExamConflict
)

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("student_number", "get_full_name", "university_email", "current_status", "academic_level", "cumulative_gpa")
    list_filter = ("current_status", "academic_level", "citizenship_status")
    search_fields = ("student_number", "university_email", "user__first_name", "user__last_name")

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = "Full Name"

@admin.register(StudentAddress)
class StudentAddressAdmin(admin.ModelAdmin):
    list_display = ("student", "address_type", "city", "state", "country")
    list_filter = ("address_type", "country")

@admin.register(StudentEmergencyContact)
class StudentEmergencyContactAdmin(admin.ModelAdmin):
    list_display = ("student", "contact_name", "relationship", "phone_number", "priority")

@admin.register(StudentAcademicProfile)
class StudentAcademicProfileAdmin(admin.ModelAdmin):
    list_display = ("student", "major", "minor", "catalog_year")
    search_fields = ("student__student_number", "major")

@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "section_id",
        "semester",
        "enrollment_status",
        "credit_load",
        "academic_standing",
    )

    list_filter = (
        "semester",
        "enrollment_status",
        "academic_standing",
    )

    search_fields = (
        "student__student_number",
        "student__user__first_name",
        "student__user__last_name",
        "section_id__course__course_code",
        "section_id__course__course_name",
    )

@admin.register(StudentFinancialAid)
class StudentFinancialAidAdmin(admin.ModelAdmin):
    list_display = ("student", "aid_type", "award_amount", "academic_year", "status")
    list_filter = ("aid_type", "status")

@admin.register(StudentHousing)
class StudentHousingAdmin(admin.ModelAdmin):
    list_display = ("student", "residence_hall", "room_number", "move_in_date", "move_out_date")

@admin.register(StudentResearchProfile)
class StudentResearchProfileAdmin(admin.ModelAdmin):
    list_display = ("student", "project_title", "research_area", "participation_start", "participation_end")

@admin.register(StudentOrganization)
class StudentOrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "organization_name",
        "description",
        "advisor",
        "created_at",
    )

    search_fields = (
        "organization_name",
    )

    list_filter = (
        "advisor",
    )

    ordering = (
        "organization_name",
    )
    
@admin.register(StudentOrganizationMembership)
class StudentOrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "organization",
        "role",
        "status",
        "start_date",
        "end_date",
    )

    search_fields = (
        "student__user__first_name",
        "student__user__last_name",
        "organization__organization_name",
    )

    list_filter = (
        "status",
        "organization",
    )

    ordering = (
        "organization",
        "student",
    )

@admin.register(StudentCareerProfile)
class StudentCareerProfileAdmin(admin.ModelAdmin):
    list_display = ("student", "internship_company", "internship_title", "internship_start", "internship_end")

@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ("student", "document_type", "file_name", "upload_date", "verification_status")
    list_filter = ("document_type", "verification_status")

@admin.register(StudentFee)
class StudentFeeAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "fee_type",
        "description",
        "academic_year",
        "amount",
        "due_date",
        "status",
    )
    list_filter = (
        "fee_type",
        "status",
        "academic_year",
    )
    search_fields = (
        "student__student_number",
        "description",
    )


@admin.register(StudentFeePayment)
class StudentFeePaymentAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "fee",
        "amount",
        "payment_method",
        "payment_date",
        "status",
    )
    list_filter = (
        "payment_method",
        "status",
    )
    search_fields = (
        "student__student_number",
        "transaction_id",
    )



@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = (
        "semester_code",
        "semester_type",
        "academic_year",
        "start_date",
        "end_date",
        "is_current",
    )
    list_filter = (
        "semester_type",
        "academic_year",
        "is_current",
    )
    search_fields = (
        "semester_code",
    )


@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = (
        "section_id",
        "course_id",
        "section_number",
        "section_type",
        "semester_id",
        "faculty_name",
        "room_number",
        "building_name",
        "capacity",
        "status",
    )

    list_filter = (
        "semester_id",
        "section_type",
        "status",
    )

    search_fields = (
        "course_id__course_code",
        "course_id__course_name",
        "section_number",
        "faculty_name",
    )

    autocomplete_fields = (
        "course_id",
        "semester_id",
    )

@admin.register(CourseMaterial)
class CourseMaterialAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "course_section",
        "material_type",
        "uploaded_by",
        "uploaded_at",
    )

    list_filter = (
        "material_type",
        "uploaded_at",
    )

    search_fields = (
        "title",
        "course_section__course_id__course_code",
        "course_section__course_id__course_name",
        "uploaded_by__first_name",
        "uploaded_by__last_name",
    )

    autocomplete_fields = (
        "course_section",
        "uploaded_by",
    )

    ordering = (
        "-uploaded_at",
    )

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "submitted_by",
        "course_section",
        "priority",
        "status",
        "created_at",
        "resolved_by",
    )

    list_filter = (
        "status",
        "priority",
        "created_at",
    )

    search_fields = (
        "subject",
        "submitted_by__first_name",
        "submitted_by__last_name",
        "course_section__course_id__course_code",
        "course_section__course_id__course_name",
    )

    autocomplete_fields = (
        "submitted_by",
        "resolved_by",
        "course_section",
    )

    ordering = (
        "-created_at",
    )
    
@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "section_id",
        "day_of_week",
        "start_time",
        "end_time",
        "room",
        "building",
        "is_online",
    )

    list_filter = (
        "day_of_week",
        "is_online",
    )

    search_fields = (
        "section_id__course_id__course_code",
        "section_id__course_id__course_name",
        "room",
        "building",
    )


## Leo's Code Start ##
from Students.Leo_Student.admin import *
## Leo's Code End ##

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = (
        "exam_name",
        "exam_type",
        "exam_date",
        "start_time",
        "end_time",
        "course_section",
        "semester",
        "status",
        "created_by",
    )
    list_filter = ("exam_type", "status", "exam_date", "semester")
    search_fields = ("exam_name", "course_section__course__course_code")


@admin.register(ExamRoomAllocation)
class ExamRoomAllocationAdmin(admin.ModelAdmin):
    list_display = ("exam", "room", "allocated_capacity", "allocated_by", "allocated_at")


@admin.register(ExamInvigilator)
class ExamInvigilatorAdmin(admin.ModelAdmin):
    list_display = ("exam", "faculty", "assigned_by", "assigned_at")


@admin.register(ExamSeat)
class ExamSeatAdmin(admin.ModelAdmin):
    list_display = ("exam", "student", "room", "seat_number")


@admin.register(ExamAttendance)
class ExamAttendanceAdmin(admin.ModelAdmin):
    list_display = ("exam", "student", "attendance")


@admin.register(ExamConflict)
class ExamConflictAdmin(admin.ModelAdmin):
    list_display = ("exam", "conflict_type", "resolved", "resolved_by")

# *************************************** Arun Code ********************************************************** 
