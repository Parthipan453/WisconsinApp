from django.contrib import admin
from .models import *

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):

    list_display = (
        "university_name",
        "university_short_name",
        "university_code",
        "university_type",
        "ownership_type",
        "official_email",
        "city",
        "country",
        "established_year",
        "status",
    )

    search_fields = (
        "university_name",
        "university_short_name",
        "university_code",
        "official_email",
        "city",
        "country",
    )

    list_filter = (
        "status",
        "university_type",
        "ownership_type",
        "country",
        "state",
        "established_year",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "university_name",
    )

    list_per_page = 25

    fieldsets = (
        (
            "University Information",
            {
                "fields": (
                    "university_name",
                    "university_short_name",
                    "university_code",
                    "logo",
                )
            },
        ),
        (
            "Classification",
            {
                "fields": (
                    "university_type",
                    "ownership_type",
                    "status",
                )
            },
        ),
        (
            "Contact Information",
            {
                "fields": (
                    "official_email",
                    "phone_number",
                    "website",
                )
            },
        ),
        (
            "Address",
            {
                "fields": (
                    "address_line_1",
                    "address_line_2",
                    "city",
                    "state",
                    "country",
                    "postal_code",
                )
            },
        ),
        (
            "Academic Information",
            {
                "fields": (
                    "established_year",
                    "accreditation",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "is_full_crud",
                )
            },
        ),
    )


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):

    list_display = (
        "school_name",
        "school_short_name",
        "school_code",
        "university",
        "school_type",
        "official_email",
        "city",
        "status",
    )

    search_fields = (
        "school_name",
        "school_short_name",
        "school_code",
        "official_email",
        "city",
    )

    list_filter = (
        "status",
        "school_type",
        "university",
        "country",
        "state",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "school_name",
    )

    list_per_page = 25

    fieldsets = (
        (
            "School Information",
            {
                "fields": (
                    "university",
                    "school_name",
                    "school_short_name",
                    "school_code",
                    "school_type",
                    "logo",
                    "dean",
                )
            },
        ),
        (
            "Contact Information",
            {
                "fields": (
                    "official_email",
                    "phone_number",
                    "website",
                )
            },
        ),
        (
            "Location",
            {
                "fields": (
                    "building_name",
                    "address_line_1",
                    "address_line_2",
                    "city",
                    "state",
                    "country",
                    "postal_code",
                )
            },
        ),
        (
            "Academic Information",
            {
                "fields": (
                    "established_year",
                    "description",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "status",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )




@admin.register(Degree)
class DegreeAdmin(admin.ModelAdmin):
    list_display = (
        'degree_name',
        'degree_code',
        'level',
    )

    search_fields = (
        'degree_name',
        'degree_code',
    )

    list_filter = (
        'level',
    )

@admin.register(AcademicProgram)
class AcademicProgramAdmin(admin.ModelAdmin):
    list_display = (
        'program_name',
        'department',
        'degree',
        'program_type',
        'duration',
        'status',
    )

    search_fields = (
        'program_name',
    )

    list_filter = (
        'degree',
        'department',
        'program_type',
        'status',
    )






############# Steve code start #################
@admin.register(ProgramCourse)
class ProgramCourseAdmin(admin.ModelAdmin):

    list_display = (
        "program_course_id",
        "program",
        "course",
        "study_year",
        "term",
        "is_elective",
        "status",
        "created_at",
    )

    list_filter = (
        "program",
        "study_year",
        "term",
        "is_elective",
        "status",
    )

    search_fields = (
        "program__program_name",
        "course__course_name",
        "course__course_code",
    )

    ordering = (
        "program",
        "study_year",
        "term",
        "course",
    )

    autocomplete_fields = (
        "program",
        "course",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    list_per_page = 20
    
from .models import AreaOfInterest

admin.site.register(AreaOfInterest)




from django.contrib import admin
from .models import AcademicTerm


@admin.register(AcademicTerm)
class AcademicTermAdmin(admin.ModelAdmin):
    list_display = (
        "term_id",
        "academic_year",
        "term_name",
        "start_date",
        "end_date",
        "registration_start",
        "registration_end",
        "status",
        "created_at",
    )

    list_display_links = (
        "term_id",
        "academic_year",
    )

    list_filter = (
        "academic_year",
        "term_name",
        "status",
    )

    search_fields = (
        "academic_year",
        "term_name",
    )

    ordering = (
        "academic_year",
        "start_date",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    list_per_page = 25

    fieldsets = (
        (
            "Academic Term Information",
            {
                "fields": (
                    "academic_year",
                    "term_name",
                    "status",
                )
            },
        ),
        (
            "Academic Schedule",
            {
                "fields": (
                    "start_date",
                    "end_date",
                )
            },
        ),
        (
            "Registration Schedule",
            {
                "fields": (
                    "registration_start",
                    "registration_end",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "is_full_crud",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    
############# Steve code end #################