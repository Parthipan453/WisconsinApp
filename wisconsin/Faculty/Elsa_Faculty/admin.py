from django.contrib import admin
from .models import *


@admin.register(CourseGrade)
class CourseGradeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "course",
        "semester",
        "numeric_score",
        "instructor_id",
        "grade_date",
    )

    list_filter = ("course", "semester")
    search_fields = ("student__student_number", "course__course_code")


@admin.register(GradeChangeRequest)
class GradeChangeRequestAdmin(admin.ModelAdmin):
    list_display = (
        "request_id",
        "student_id",
        "course_id",
        "current_score",
        "requested_score",
        "current_grade",
        "requested_grade",
        "approval_status",
        "instructor_id",
        "request_date",
        "approved_by",
    )

    list_filter = ("approval_status", "course_id")
    search_fields = (
        "student__student_number",
        "course__course_code",
        "instructor_id",
    )

    list_editable = ("approval_status",)