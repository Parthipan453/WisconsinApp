# ******* Navina Code ******* #
from django.utils.html import format_html
from django.contrib import admin
from .models import (
    Library,
    LibraryResource,
    ResourceCopy,
    LibraryUser,
    BorrowTransaction,
    # Reservation,
    DigitalResource,
    # StudyRoom,
    # StudyRoomBooking,
    LibraryStaff,
    LibraryEvent,
    Building,
)



# Library

@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = (
        "library_code",
        "library_name",
        "phone",
        "status",
    )
    search_fields = ("library_code", "library_name")

# rupa update starts****************************
# resourcecategory
from django.contrib import admin
from .models import ResourceCategory, LibraryResource


@admin.register(ResourceCategory)
class ResourceCategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'status','get_book_count']
    list_filter = ['status', 'created_at', 'updated_at']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description')
        }),
        ('Display & Ordering', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_book_count(self, obj):
        return obj.resources.count()
    get_book_count.short_description = 'Books'


# Library Resource
@admin.register(LibraryResource)
class LibraryResourceAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "category",
        "resource_type",
        "library",
        "author",
        "available_copies",
        "status",
        "cover_preview",
    )


    search_fields = (
        "title",
        "author",
        "isbn_issn",
        "publisher",
    )


    list_filter = (
        "category",
        "resource_type",
        "library",
        "status",
    )


    ordering = (
        "title",
    )


    readonly_fields = (
        "cover_preview",
        "available_copies",
    )


    fields = (
        "cover_image",
        "cover_preview",
        "title",
        "category",
        "resource_type",
        "library",
        "author",
        "isbn_issn",
        "publisher",
        "publication_year",
        "edition",
        "language",
        "subject",
        "total_copies",
        "available_copies",
        "shelf_location",
        "status",
        "is_full_crud",
    )


    def cover_preview(self, obj):

        if obj.cover_image:

            return format_html(
                '<img src="{}" width="60" height="80" style="object-fit:cover;border-radius:5px;" />',
                obj.cover_image.url
            )

        return "No Cover"


    cover_preview.short_description = "Cover"
    
    
# rupa update ends*****************
# Resource Copy

@admin.register(ResourceCopy)
class ResourceCopyAdmin(admin.ModelAdmin):
    list_display = (
        "barcode",
        "resource",
        "status",
        "acquisition_date",
    )
    search_fields = ("barcode",)
    list_filter = ("status",)

# Library User

@admin.register(LibraryUser)
class LibraryUserAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "user_type",
        "membership_date",
        "active",
    )

    list_filter = (
        "user_type",
        "active",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
    )

# Borrow Transactions

@admin.register(BorrowTransaction)
class BorrowTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "library_user",
        "copy",
        "issue_date",
        "due_date",
        "status",
    )
    list_filter = ("status",)

# Reservation

# @admin.register(Reservation)
# class ReservationAdmin(admin.ModelAdmin):
#     list_display = (
#         "library_user",
#         "resource",
#         "reservation_date",
#         "status",
#     )
#     list_filter = ("status",)

# Fine

# @admin.register(Fine)
# class FineAdmin(admin.ModelAdmin):
#     list_display = (
#         "transaction",
#         "amount",
#         "payment_status",
#     )
#     list_filter = ("payment_status",)

from django.contrib import admin
from .models import Fine


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "transaction",
        "fine_amount",
        "payment_status",
        "payment_transaction_id",
        "receipt_number",
        "paid_date",
    )

    list_filter = (
        "payment_status",
        "payment_method",
        "paid_date",
    )

    search_fields = (
        "payment_transaction_id",
        "receipt_number",
        "payment_reference",
        "transaction__student__first_name",
        "transaction__student__last_name",
        "transaction__student__university_id",
        "transaction__book__title",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

    fieldsets = (
        (
            "Borrow Transaction",
            {
                "fields": (
                    "transaction",
                )
            },
        ),

        (
            "Fine Details",
            {
                "fields": (
                    "fine_per_day",
                    "overdue_days",
                    "fine_amount",
                )
            },
        ),

        (
            "Payment Details",
            {
                "fields": (
                    "payment_status",
                    "payment_method",
                    "amount_received",
                    "payment_transaction_id",
                    "payment_reference",
                    "receipt_number",
                    "paid_date",
                    "collected_by",
                )
            },
        ),

        (
            "Remarks",
            {
                "fields": (
                    "remarks",
                )
            },
        ),

        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

from django.contrib import admin
from .models import FineAppeal


@admin.register(FineAppeal)
class FineAppealAdmin(admin.ModelAdmin):

    list_display = (
        "uwid",
        "applicant_name",
        "applicant_email",
        "appeal_reason",
        "appeal_status",
        "submitted_at",
    )

    list_filter = (
        "appeal_reason",
        "appeal_status",
        "submitted_at",
    )

    search_fields = (
        "uwid",
        "applicant_name",
        "applicant_email",
    )

    readonly_fields = (
        "submitted_at",
    )

    fieldsets = (

        (
            "Applicant Information",
            {
                "fields": (
                    "uwid",
                    "applicant_name",
                    "applicant_phone",
                    "applicant_email",
                )
            },
        ),

        (
            "Appeal Details",
            {
                "fields": (
                    "appeal_reason",
                    "explanation_statement",
                    "consent",
                )
            },
        ),

        (
            "Library Review",
            {
                "fields": (
                    "appeal_status",
                    "admin_notes",
                )
            },
        ),

        (
            "System Information",
            {
                "fields": (
                    "submitted_at",
                    "is_full_crud",
                )
            },
        ),

    )

from .models import ContactRequest

@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):

    list_display = (

        "name",

        "email",

        "affiliation",

        "status",

        "created_at",

        "is_active",

    )

    list_filter = (

        "status",

        "affiliation",

        "is_active",

    )

    search_fields = (

        "name",

        "email",

        "message",

    )

    readonly_fields = (

        "created_at",

        "updated_at",

    )

    list_per_page = 25

from django.contrib import admin

from .models import RequestPurchase


@admin.register(RequestPurchase)
class RequestPurchaseAdmin(admin.ModelAdmin):

    list_display = (

        "email",

        "created_at",

    )

    search_fields = (

        "email",

    )

    ordering = (

        "-created_at",

    )

from .models import ShelvingFacilityRequest


@admin.register(ShelvingFacilityRequest)
class ShelvingFacilityRequestAdmin(admin.ModelAdmin):

    list_display = (
        "first_name",
        "last_name",
        "email",
        "viewing_library",
        "created_at",
    )

    search_fields = (
        "first_name",
        "last_name",
        "email",
        "title",
    )

    list_filter = (
        "viewing_library",
        "created_at",
    )

    readonly_fields = (
        "created_at",
    )

# Digital Resource

@admin.register(DigitalResource)
class DigitalResourceAdmin(admin.ModelAdmin):
    list_display = (
        "resource",
        "vendor",
        "license_type",
    )

# StudyRoom

# from django.contrib import admin

# from .models import StudyRoom

# @admin.register(StudyRoom)
# class StudyRoomAdmin(admin.ModelAdmin):

#     list_display = (
#         "id",
#         "library",
#         "room",
#         "equipment",
#         "status",
#         "is_full_crud",
#     )

#     list_filter = (
#         "library",
#         "status",
#         "is_full_crud",
#     )

#     search_fields = (
#         "room__room_number",
#         "room__room_name",
#         "library__library_name",
#     )

#     ordering = (
#         "library",
#         "room__room_number",
#     )

# # StudyRoom Booking

# @admin.register(StudyRoomBooking)
# class StudyRoomBookingAdmin(admin.ModelAdmin):
#     list_display = (
#         "room",
#         "user",
#         "booking_date",
#         "status",
#     )
#     list_filter = ("status",)



# LibraryEvent

@admin.register(LibraryEvent)
class LibraryEventAdmin(admin.ModelAdmin):
    list_display = (
        "event_name",
        "event_type",
        "event_date",
    )
    list_filter = ("event_type",)


# New models- navina

# from django.contrib import admin
# from .models import (
#     ResourceTypeItem,
#     ResourceSubject,
# )



# @admin.register(FindCard)
# class FindCardAdmin(admin.ModelAdmin):
#     list_display = (
#         'title',
#         'display_order',
#         'active',
#     )

#     list_filter = (
#         'active',
#     )

#     search_fields = (
#         'title',
#         'description',
#     )

#     ordering = (
#         'display_order',
#     )


# @admin.register(ResourceTypeItem)
# class ResourceTypeItemAdmin(admin.ModelAdmin):
#     list_display = (
#         'title',
#         'display_order',
#         'active',
#     )

#     list_filter = (
#         'active',
#     )

#     search_fields = (
#         'title',
#     )

#     ordering = (
#         'display_order',
#     )


# @admin.register(ResourceSubject)
# class ResourceSubjectAdmin(admin.ModelAdmin):
#     list_display = (
#         'title',
#         'display_order',
#         'active',
#     )

#     list_filter = (
#         'active',
#     )

#     search_fields = (
#         'title',
#         'description',
#     )

#     ordering = (
#         'display_order',
#     )


# from django.contrib import admin
# from .models import (
#     LibraryAdditionalResource,
#     LibraryHours,
#     LibraryAccessInfo,
# )

# @admin.register(LibraryAdditionalResource)
# class LibraryAdditionalResourceAdmin(admin.ModelAdmin):
#     list_display = (
#         'title',
#         'page_type',
#         'display_order',
#         'active',
#     )

#     list_filter = (
#         'page_type',
#         'active',
#     )

#     search_fields = (
#         'title',
#     )

#     ordering = (
#         'display_order',
#     )


# @admin.register(LibraryHours)
# class LibraryHoursAdmin(admin.ModelAdmin):
#     list_display = (
#         'library',
#         'day',
#         'opening_time',
#         'closing_time',
#         'is_closed',
#     )

#     list_filter = (
#         'library',
#         'is_closed',
#     )

#     search_fields = (
#         'library__library_name',
#         'day',
#     )

#     ordering = (
#         'library',
#         'display_order',
#     )


# @admin.register(LibraryAccessInfo)
# class LibraryAccessInfoAdmin(admin.ModelAdmin):
#     list_display = (
#         'library',
#         'title',
#         'display_order',
#         'active',
#     )

#     list_filter = (
#         'library',
#         'active',
#     )

#     search_fields = (
#         'library__library_name',
#         'title',
#     )

#     ordering = (
#         'library',
#         'display_order',
#     )


# @admin.register(LibraryService)
# class LibraryServiceAdmin(admin.ModelAdmin):
#     list_display = (
#         'library',
#         'service_name',
#         'active',
#     )

#     list_filter = (
#         'library',
#         'active',
#     )

#     search_fields = (
#         'library__library_name',
#         'service_name',
#     )

# Borrow & Request

# from .models import (
#     # BorrowCard,
#     # BorrowCardLink,
#     LibraryAdditionalResource,
#     # GivingPage,
# )

# @admin.register(BorrowCard)
# class BorrowCardAdmin(admin.ModelAdmin):
#     list_display = (
#         'title',
#         'display_order',
#         'active'
#     )
#     list_editable = (
#         'display_order',
#         'active'
#     )


# @admin.register(BorrowCardLink)
# class BorrowCardLinkAdmin(admin.ModelAdmin):
#     list_display = (
#         'title',
#         'card',
#         'display_order',
#         'active'
#     )
#     list_filter = ('card',)
#     list_editable = (
#         'display_order',
#         'active'
#     )


# @admin.register(GivingPage)
# class GivingPageAdmin(admin.ModelAdmin):
#     list_display = (
#         'banner_title',
#         'button_text',
#         'active',
#     )
 
#     list_filter = (
#         'active',
#     )
 
#     search_fields = (
#         'banner_title',
#         'main_heading',
#     )
 

# *****************************************rupa code start *************************************

# from django.contrib import admin
# from .models import (
#     ResearchSupportCategory,
#     ResearchSupportCategoryLink,
#     ResearchSupportFeaturedResource,
#     ResearchSupportSection,
#     ResearchSupportSectionItem,
# )


# ----------------------------
# Inlines
# ----------------------------

# class ResearchSupportCategoryLinkInline(admin.TabularInline):
#     model = ResearchSupportCategoryLink
#     extra = 1
#     fields = (
#         "link_text",
#         "link_url",
#         "display_order",
#         "status",
#     )


# class ResearchSupportSectionItemInline(admin.TabularInline):
#     model = ResearchSupportSectionItem
#     extra = 1
#     fields = (
#         "title",
#         "url",
#         "description",
#         "display_order",
#         "status",
#     )


# ----------------------------
# Research Support Category
# ----------------------------

# @admin.register(ResearchSupportCategory)
# class ResearchSupportCategoryAdmin(admin.ModelAdmin):
#     list_display = (
#         "title",
#         "display_order",
#         "status",
#         "created_at",
#     )

#     list_filter = (
#         "status",
#     )

#     search_fields = (
#         "title",
#         "description",
#         "intro",
#     )

#     prepopulated_fields = {
#         "slug": ("title",)
#     }

#     ordering = (
#         "display_order",
#         "title",
#     )

#     inlines = [
#         ResearchSupportCategoryLinkInline,
#     ]


# # ----------------------------
# # Category Links
# # ----------------------------

# @admin.register(ResearchSupportCategoryLink)
# class ResearchSupportCategoryLinkAdmin(admin.ModelAdmin):
#     list_display = (
#         "link_text",
#         "category",
#         "display_order",
#         "status",
#     )

#     list_filter = (
#         "category",
#         "status",
#     )

#     search_fields = (
#         "link_text",
#         "category__title",
#     )

#     ordering = (
#         "category",
#         "display_order",
#     )


# ----------------------------
# Featured Resources
# ----------------------------

# @admin.register(ResearchSupportFeaturedResource)
# class ResearchSupportFeaturedResourceAdmin(admin.ModelAdmin):
#     list_display = (
#         "title",
#         "display_order",
#         "status",
#     )

#     list_filter = (
#         "status",
#     )

#     search_fields = (
#         "title",
#     )

#     ordering = (
#         "display_order",
#         "title",
#     )


# # ----------------------------
# # Research Support Sections
# # ----------------------------

# @admin.register(ResearchSupportSection)
# class ResearchSupportSectionAdmin(admin.ModelAdmin):
#     list_display = (
#         "title",
#         "category",
#         "display_order",
#         "status",
#     )

#     list_filter = (
#         "category",
#         "status",
#     )

#     search_fields = (
#         "title",
#         "category__title",
#     )

#     ordering = (
#         "category",
#         "display_order",
#     )

#     inlines = [
#         ResearchSupportSectionItemInline,
#     ]


# ----------------------------
# Section Items
# ----------------------------

# @admin.register(ResearchSupportSectionItem)
# class ResearchSupportSectionItemAdmin(admin.ModelAdmin):
#     list_display = (
#         "title",
#         "section",
#         "display_order",
#         "status",
#     )

#     list_filter = (
#         "section",
#         "status",
#     )

#     search_fields = (
#         "title",
#         "section__title",
#     )

#     ordering = (
#         "section",
#         "display_order",
    # )



# instruction request

# from .models import InstructionRequest
# @admin.register(InstructionRequest)
# class InstructionRequestAdmin(admin.ModelAdmin):

#     list_display = (
#         "course",
#         "instructor_name",
#         "department",
#         "preferred_date",
#         "assigned_librarian",
#         "status",
#     )

#     list_filter = (
#         "status",
#         "delivery_mode",
#         "department",
#     )

#     search_fields = (
#         "course__course_name",
#         "course__course_code",
#         "instructor_name",
#         "instructor_email",
#     )

#     autocomplete_fields = (
#         "department",
#         "course",
#         "preferred_library",
#         "assigned_librarian",
#     )

#     readonly_fields = (
#         "created_at",
#         "updated_at",
#     )

#     fieldsets = (

#         (
#             "Instructor Information",
#             {
#                 "fields": (
#                     "instructor_name",
#                     "phone",
#                     "instructor_email",
#                 )
#             }
#         ),

#         (
#             "Course Information",
#             {
#                 "fields": (
#                     "department",
#                     "course",
#                     "number_of_students",
#                 )
#             }
#         ),

#         (
#             "Instruction",
#             {
#                 "fields": (
#                     "delivery_mode",
#                     "instruction_support",
#                 )
#             }
#         ),

#         (
#             "Library Preference",
#             {
#                 "fields": (
#                     "preferred_library",
#                     "preferred_room",
#                     "preferred_date",
#                     "additional_notes",
#                 )
#             }
#         ),

#         (
#             "Administration",
#             {
#                 "fields": (
#                     "assigned_librarian",
#                     "status",
#                     "admin_notes",
#                 )
#             }
#         ),

#         (
#             "System",
#             {
#                 "fields": (
#                     "created_at",
#                     "updated_at",
#                 )
#             }
#         ),

#     )


from .models import InstructionRequest


@admin.register(InstructionRequest)
class InstructionRequestAdmin(admin.ModelAdmin):

    list_display = (
        "instructor_name",
        "instructor_email",
        "department",
        "course",
        "preferred_library",
        "status",
        "created_at",
    )
    def display_instruction_modes(self, obj):
        labels = dict(InstructionRequest.INSTRUCTION_MODE_CHOICES)
        return ", ".join(labels.get(mode, mode) for mode in obj.instruction_modes)
    display_instruction_modes.short_description = "Instruction Modes"

    list_filter = (
        "status",
        "department",
        "course",
        "preferred_library",
        "created_at",
    )

    search_fields = (
        "instructor_name",
        "instructor_email",
        "phone",
        "instruction_support",
        "admin_notes",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (

        (
            "Instructor Information",
            {
                "fields": (
                    "instructor_name",
                    "instructor_email",
                    "phone",
                )
            },
        ),

        (
            "Course Information",
            {
                "fields": (
                    "department",
                    "course",
                    "number_of_students",
                )
            },
        ),

        (
            "Instruction Details",
            {
                "fields": (
                    "instruction_modes",
                    "instruction_support",
                )
            },
        ),

        (
            "Library Preferences",
            {
                "fields": (
                    "preferred_library",
                    "preferred_room",
                    "preferred_schedule",
                    "additional_notes",
                )
            },
        ),

        (
            "Consent",
            {
                "fields": (
                    "consent",
                )
            },
        ),

        (
            "Administration",
            {
                "fields": (
                    "assigned_librarian",
                    "status",
                    "admin_notes",
                    "is_full_crud",
                )
            },
        ),

        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

# instruction support

# from .models import (
#     InstructionSupportCategory,
#     InstructionSupportCategoryLink,
#     InstructionSupportSidebarLink,
# )


# ==========================================================
# Category Links Inline
# ==========================================================

# class InstructionSupportCategoryLinkInline(admin.TabularInline):
#     model = InstructionSupportCategoryLink
#     extra = 1

#     fields = (
#         "link_text",
#         "link_url",
#         "icon",
#         "open_in_new_tab",
#         "display_order",
#         "status",
#     )

#     ordering = ("display_order",)


# # ==========================================================
# # Category Admin
# # ==========================================================

# @admin.register(InstructionSupportCategory)
# class InstructionSupportCategoryAdmin(admin.ModelAdmin):

#     list_display = (
#         "title",
#         "display_order",
#         "status",
#         "created_at",
#     )

#     list_filter = (
#         "status",
#     )

#     search_fields = (
#         "title",
#         "description",
#     )

#     prepopulated_fields = {
#         "slug": ("title",)
#     }

#     ordering = (
#         "display_order",
#     )

#     inlines = [
#         InstructionSupportCategoryLinkInline
#     ]


# # ==========================================================
# # Category Link Admin
# # ==========================================================

# @admin.register(InstructionSupportCategoryLink)
# class InstructionSupportCategoryLinkAdmin(admin.ModelAdmin):

#     list_display = (
#         "link_text",
#         "category",
#         "display_order",
#         "status",
#     )

#     list_filter = (
#         "category",
#         "status",
#     )

#     search_fields = (
#         "link_text",
#     )

#     ordering = (
#         "category",
#         "display_order",
#     )


# ==========================================================
# Sidebar Admin
# ==========================================================

# @admin.register(InstructionSupportSidebarLink)
# class InstructionSupportSidebarLinkAdmin(admin.ModelAdmin):

#     list_display = (
#         "title",
#         "display_order",
#         "status",
#     )

#     list_filter = (
#         "status",
#     )

#     search_fields = (
#         "title",
#     )

#     ordering = (
#         "display_order",
#     )



# office of the dean
from django.contrib import admin
from .models import OfficeOfDeanMember


@admin.register(OfficeOfDeanMember)
class OfficeOfDeanMemberAdmin(admin.ModelAdmin):
    list_display = (
        "staff",
        "designation",
        "display_order",
        "show_about_link",
    )

    list_editable = (
        "designation",
        "display_order",
        "show_about_link",
    )

    list_filter = (
        "show_about_link",
    )

    search_fields = (
        "staff__staff__user__first_name",
        "staff__staff__user__last_name",
        "staff__staff__work_email",
        "designation",
    )

    ordering = (
        "display_order",
    )

    autocomplete_fields = (
        "staff",
    )

    exclude = (
        "is_full_crud",
    )


# peoples 

from .models import (
    
    Subject,
    SubjectLibrarian,
    
)



# updated departmentmember model

from django.contrib import admin
from .models import DepartmentMember


@admin.register(DepartmentMember)
class DepartmentMemberAdmin(admin.ModelAdmin):

    list_display = (
        "staff",
        "department",
        "job_title",
        "display_order",
    )

    list_filter = (
        "department",
    )

    search_fields = (
        "staff__staff__user__first_name",
        "staff__staff__user__last_name",
        "staff__staff__employee_id",
        "staff__role",
        "job_title",
        "department__department_name",
    )

    autocomplete_fields = (
        "staff",
        "department",
    )

    ordering = (
        "department",
        "display_order",
    )

    list_per_page = 25

    fieldsets = (

        (
            "Department Information",
            {
                "fields": (
                    "department",
                    "staff",
                    "job_title",
                )
            },
        ),

        (
            "Display Settings",
            {
                "fields": (
                    "display_order",
                    "is_full_crud",
                )
            },
        ),

    )

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "team_email",
        "status",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "name",
    )

    prepopulated_fields = {
        "slug": ("name",)
    }


@admin.register(SubjectLibrarian)
class SubjectLibrarianAdmin(admin.ModelAdmin):

    list_display = (
        "subject",
        "staff",
        "display_order",
        "status",
    )

    list_filter = (
        "subject",
        "status",
    )

    search_fields = (
        "subject__name",
        "staff__first_name",
        "staff__last_name",
    )

    ordering = (
        "display_order",
    )


# @admin.register(PeoplePageCard)
# class PeoplePageCardAdmin(admin.ModelAdmin):

#     # readonly_fields = ("url",)
 
#     list_display = (
#         "title",
#         "display_order",
#         "status",
#     )
 
#     list_filter = (
#         "status",
#     )
 
#     search_fields = (
#         "title",
#     )
 
#     ordering = (
#         "display_order",
#     )
 

# about page


# from .models import (
#     # AboutCategory,
#     # AboutCategoryLink,
#     # AboutSidebarLink,
#     CollectionSection,
#     CollectionStatistic,
#     CollectionDefinition,
# )


# ==========================
# About Category
# ==========================

# class AboutCategoryLinkInline(admin.TabularInline):
#     model = AboutCategoryLink
#     extra = 1
#     ordering = ("display_order",)


# @admin.register(AboutCategory)
# class AboutCategoryAdmin(admin.ModelAdmin):
#     list_display = (
#         "title",
#         "display_order",
#         "status",
#         "created_at",
#     )

#     list_filter = (
#         "status",
#     )

#     search_fields = (
#         "title",
#         "description",
#     )

#     prepopulated_fields = {
#         "slug": ("title",)
#     }

#     ordering = (
#         "display_order",
#         "title",
#     )

#     inlines = [
#         AboutCategoryLinkInline,
#     ]


# ==========================
# About Category Links
# ==========================

# @admin.register(AboutCategoryLink)
# class AboutCategoryLinkAdmin(admin.ModelAdmin):
#     list_display = (
#         "link_text",
#         "category",
#         "display_order",
#         "status",
#     )

#     list_filter = (
#         "status",
#         "category",
#     )

#     search_fields = (
#         "link_text",
#         "category__title",
#     )

#     ordering = (
#         "category",
#         "display_order",
#     )


# ==========================
# About Sidebar Links
# ==========================

# @admin.register(AboutSidebarLink)
# class AboutSidebarLinkAdmin(admin.ModelAdmin):
#     list_display = (
#         "title",
#         "display_order",
#         "status",
#     )

#     list_filter = (
#         "status",
#     )

#     search_fields = (
#         "title",
#     )

#     ordering = (
#         "display_order",
#         "title",
#     )


# ==========================
# Collection Statistics
# ==========================

# from django.contrib import admin
# from .models import (
#     CollectionSection,
#     CollectionStatistic,
#     CollectionDefinition,
# )


# ==========================================
# Collection Statistics Inline
# ==========================================

# class CollectionStatisticInline(admin.TabularInline):
#     model = CollectionStatistic
#     extra = 1
#     ordering = ("display_order",)


# ==========================================
# Collection Section
# ==========================================

# @admin.register(CollectionSection)
# class CollectionSectionAdmin(admin.ModelAdmin):

#     list_display = (
#         "title",
#         "display_order",
#         "status",
#         "created_at",
#     )

#     list_filter = (
#         "status",
#     )

#     search_fields = (
#         "title",
#         "description",
#     )

#     prepopulated_fields = {
#         "slug": ("title",)
#     }

#     ordering = (
#         "display_order",
#         "title",
#     )

#     inlines = [
#         CollectionStatisticInline,
#     ]


# ==========================================
# Collection Statistic
# ==========================================

# @admin.register(CollectionStatistic)
# class CollectionStatisticAdmin(admin.ModelAdmin):

#     list_display = (
#         "label",
#         "value",
#         "section",
#         "display_order",
#     )

#     list_filter = (
#         "section",
#     )

#     search_fields = (
#         "label",
#         "value",
#         "section__title",
#     )

#     ordering = (
#         "section",
#         "display_order",
#     )


# ==========================================
# Collection Definition
# ==========================================

# @admin.register(CollectionDefinition)
# class CollectionDefinitionAdmin(admin.ModelAdmin):

#     list_display = (
#         "term",
#         "display_order",
#     )

#     search_fields = (
#         "term",
#         "description",
#     )

#     ordering = (
#         "display_order",
#         "term",
#     )

    
# help page
# from .models import (
#     HelpSection,
#     HelpTopic,
#     HelpContactMethod,
#     HelpSidebarLink
# )
# from .models import HelpTopicRelatedLink

# class HelpTopicInline(admin.TabularInline):
#     model = HelpTopic
#     extra = 1


# @admin.register(HelpSection)
# class HelpSectionAdmin(admin.ModelAdmin):
#     list_display = (
#         "title",
#         "display_order",
#         "is_horizontal",
#         "is_active",
#     )

#     list_filter = (
#         "is_active",
#         "is_horizontal",
#     )

#     prepopulated_fields = {
#         "slug": ("title",)
#     }

#     inlines = [HelpTopicInline]


# @admin.register(HelpTopic)
# class HelpTopicAdmin(admin.ModelAdmin):
#     list_display = (
#         "title",
#         "section",
#         "category",
#         "display_order",
#         "is_active",
#     )

#     list_filter = (
#         "category",
#         "section",
#         "is_active",
#     )

#     prepopulated_fields = {
#         "slug": ("title",)
#     }


# @admin.register(HelpContactMethod)
# class HelpContactMethodAdmin(admin.ModelAdmin):
#     list_display = (
#         "label",
#         "method_type",
#         "library",
#         "is_online",
#         "display_order",
#         "is_active",
#     )

#     list_filter = (
#         "method_type",
#         "is_online",
#         "is_active",
#     )


# @admin.register(HelpSidebarLink)
# class HelpSidebarLinkAdmin(admin.ModelAdmin):
    # list_display = (
    #     "title",
    #     "display_order",
    #     "is_active",
    # )

    # list_filter = (
    #     "is_active",
    # )

# updated help section

# from django.contrib import admin
# from .models import (
#     HelpPageSection,
#     HelpPageItem,
# )
# class HelpPageItemInline(admin.TabularInline):
#     model = HelpPageItem
#     extra = 1
#     fields = (
#         "title",
#         "url",
#         "display_order",
#         "is_active",
#     )

# @admin.register(HelpPageSection)
# class HelpPageSectionAdmin(admin.ModelAdmin):
    # list_display = (
    #     "title",
    #     "help_topic",
    #     "display_order",
    #     "is_active",
    # )

    # list_filter = (
    #     "help_topic",
    #     "is_active",
    # )

    # search_fields = (
    #     "title",
    #     "description",
    # )

    # list_editable = (
    #     "display_order",
    #     "is_active",
    # )

    # ordering = (
    #     "help_topic",
    #     "display_order",
    # )

    # inlines = [HelpPageItemInline]


# @admin.register(HelpPageItem)
# class HelpPageItemAdmin(admin.ModelAdmin):
    # list_display = (
    #     "title",
    #     "page_section",
    #     "display_order",
    #     "is_active",
    # )

    # list_filter = (
    #     "page_section",
    #     "is_active",
    # )

    # search_fields = (
    #     "title",
    # )

    # list_editable = (
    #     "display_order",
    #     "is_active",
    # )

    # ordering = (
    #     "page_section",
    #     "display_order",
    # )

# from django.contrib import admin

# from .models import (
#     HelpTopicPage,
#     HelpTopicContent,
#     HelpTopicBullet,
# )


# -----------------------------
# Inline for HelpTopicBullet
# -----------------------------
# class HelpTopicBulletInline(admin.TabularInline):
#     model = HelpTopicBullet
#     extra = 1


# -----------------------------
# Inline for HelpTopicContent
# -----------------------------
# class HelpTopicContentInline(admin.StackedInline):
#     model = HelpTopicContent
#     extra = 1

# class HelpTopicRelatedLinkInline(admin.TabularInline):
#     model = HelpTopicRelatedLink
#     extra = 1

# -----------------------------
# HelpTopicContent Admin
# -----------------------------
# @admin.register(HelpTopicContent)
# class HelpTopicContentAdmin(admin.ModelAdmin):

    # list_display = (
    #     "heading",
    #     "page",
    #     "display_order",
    #     "is_active",
    # )

    # list_filter = (
    #     "page",
    #     "is_active",
    # )

    # search_fields = (
    #     "heading",
    # )

    # ordering = (
    #     "page",
    #     "display_order",
    # )

    # inlines = [
    #     HelpTopicBulletInline,
    #     HelpTopicRelatedLinkInline,
    # ]
# -----------------------------
# HelpTopicPage Admin
# -----------------------------
# @admin.register(HelpTopicPage)
# class HelpTopicPageAdmin(admin.ModelAdmin):

#     list_display = (
#         "page_title",
#         "help_topic",
#         "display_order",
#         "is_active",
#     )

#     list_filter = (
#         "is_active",
#     )

#     search_fields = (
#         "page_title",
#     )

#     list_editable = (
#         "display_order",
#         "is_active",
#     )

#     ordering = (
#         "display_order",
#     )
#     fields = (
#         "help_topic",
#         "page_title",
#         "breadcrumb_title",
#         "banner_image",
#         "display_order",
#         "is_active",
#         "is_full_crud",
#     )

#     inlines = [HelpTopicContentInline]


# -----------------------------
# HelpTopicBullet Admin
# -----------------------------
# @admin.register(HelpTopicBullet)
# class HelpTopicBulletAdmin(admin.ModelAdmin):

#     list_display = (
#         "bullet_text",
#         "section",
#         "display_order",
#         "is_active",
#     )

#     list_filter = (
#         "section",
#         "is_active",
#     )

#     search_fields = (
#         "bullet_text",
#     )

#     list_editable = (
#         "display_order",
#         "is_active",
#     )

#     ordering = (
#         "section",
#         "display_order",
#     )

# from django.contrib import admin

# from .models import (
#     HelpFAQPage,
#     HelpFAQ,
#     HelpTopicRelatedLink,
# )


# class HelpFAQInline(admin.TabularInline):

#     model = HelpFAQ

#     extra = 1

#     fields = (
#         "question",
#         "display_order",
#         "is_active",
#     )

#     ordering = (
#         "display_order",
#     )


# @admin.register(HelpFAQPage)
# class HelpFAQPageAdmin(admin.ModelAdmin):

#     list_display = (
#         "page_title",
#         "help_topic",
#         "display_order",
#         "is_active",
#     )

#     search_fields = (
#         "page_title",
#         "help_topic__title",
#     )

#     list_filter = (
#         "is_active",
#     )

#     ordering = (
#         "display_order",
#     )

#     list_editable = (
#         "display_order",
#         "is_active",
#     )
#     fields = (
#         "help_topic",
#         "intro",
#         "banner_image",
#         "display_order",
#         "is_active",
#         "is_full_crud",
#     )

#     inlines = [
#         HelpFAQInline,
#     ]


# @admin.register(HelpFAQ)
# class HelpFAQAdmin(admin.ModelAdmin):

#     list_display = (
#         "question",
#         "page",
#         "display_order",
#         "is_active",
#     )

#     list_filter = (
#         "page",
#         "is_active",
#     )

#     search_fields = (
#         "question",
#     )

#     ordering = (
#         "page",
#         "display_order",
#     )

#     list_editable = (
#         "display_order",
#         "is_active",
#     )


# updated librarystaff

from .models import LibraryStaff


@admin.register(LibraryStaff)
class LibraryStaffAdmin(admin.ModelAdmin):

    list_display = (
        "staff",
        "role",
        "assigned_library",
        "office_location",
        "active",
        "is_public",
        "display_order",
    )
    filter_horizontal = (
        "subject_specialties",
    )

    list_filter = (
        "role",
        "assigned_library",
        "active",
        "is_public",
    )

    search_fields = (
        "staff__user__first_name",
        "staff__user__last_name",
        "staff__preferred_name",
        "staff__work_email",
        "office_location",
    )

    autocomplete_fields = (
        "staff",
        "assigned_library",
    )

    ordering = (
        "display_order",
        "staff__user__first_name",
    )

    list_editable = (
        "display_order",
        "active",
        "is_public",
    )

    fieldsets = (
        (
            "Library Assignment",
            {
                "fields": (
                    "staff",
                    "assigned_library",
                    "role",
                    "assigned_date",
                )
            },
        ),
        (
            "Directory Information",
            {
                "fields": (
                    "profile_photo",
                    "office_location",
                    "biography",
                    "office_address",
                    "campus_map_link",
                    "office_hours",
                    "subject_specialties",
                )
            },
        ),
        (
            "Display Settings",
            {
                "fields": (
                    "active",
                    "is_public",
                    "display_order",
                )
            },
        ),
    )

from django.contrib import admin
from .models import BorrowRequest


@admin.register(BorrowRequest)
class BorrowRequestAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "resource",
        "library_user",
        "status",
        "request_date",
        "approved_by",
        "approved_date",
    )

    list_filter = (
        "status",
        "request_date",
        "approved_date",
    )

    search_fields = (
        "resource__title",
        "library_user__user__username",
        "library_user__user__first_name",
        "library_user__user__last_name",
    )

    readonly_fields = (
        "request_date",
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "resource",
        "library_user",
        "approved_by",
    )

    ordering = (
        "-request_date",
    )

    fieldsets = (

        (
            "Borrow Request Information",
            {
                "fields": (
                    "resource",
                    "library_user",
                    "request_date",
                    "status",
                )
            },
        ),

        (
            "Approval Information",
            {
                "fields": (
                    "approved_by",
                    "approved_date",
                    "rejection_reason",
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

from django.contrib import admin
from .models import LibraryStaff, SubjectSpecialty

@admin.register(SubjectSpecialty)
class SubjectSpecialtyAdmin(admin.ModelAdmin):
    list_display = ("name",)



# dataadmin

# from django.contrib import admin

# from .models import (
#     DataManagementPlan,
#     DataManagementSidebar,
#     DataManagementPlanSection,
#     DataManagementSectionLink,
# )


# @admin.register(DataManagementPlan)
# class DataManagementPlanAdmin(admin.ModelAdmin):

#     list_display = (
#         "title",
#         "display_order",
#         "status",
#     )

#     list_filter = (
#         "status",
#     )

#     search_fields = (
#         "title",
#         "introduction",
#     )

#     ordering = (
#         "display_order",
#         "title",
#     )

#     prepopulated_fields = {
#         "slug": ("title",)
#     }

# @admin.register(DataManagementSidebar)
# class DataManagementSidebarAdmin(admin.ModelAdmin):

#     list_display = (
#         "title",
#         "page",
#         "anchor",
#         "display_order",
#         "status",
#     )

#     list_filter = (
#         "page",
#         "status",
#     )

#     search_fields = (
#         "title",
#         "anchor",
#         "page__title",
#     )

#     ordering = (
#         "page",
#         "display_order",
#     )

# @admin.register(DataManagementPlanSection)
# class DataManagementPlanSectionAdmin(admin.ModelAdmin):

#     list_display = (
#         "heading",
#         "menu",
#         "display_order",
#         "status",
#     )

#     list_filter = (
#         "menu",
#         "status",
#     )

#     search_fields = (
#         "heading",
#         "content",
#         "menu__title",
#         "menu__page__title",
#     )

#     ordering = (
#         "menu",
#         "display_order",
#     )


# @admin.register(DataManagementSectionLink)
# class DataManagementSectionLinkAdmin(admin.ModelAdmin):

#     list_display = (
#         "title",
#         "section",
#         "display_order",
#     )

#     list_filter = (
#         "section",
#     )

#     search_fields = (
#         "title",
#         "section__heading",
#     )

#     ordering = (
#         "section",
#         "display_order",
#     )



# grants

# from django.contrib import admin

# from .models import (
#     GrantsScholarshipPage,
#     GrantsScholarshipSidebar,
#     GrantsScholarshipGuide,
# )


# @admin.register(GrantsScholarshipPage)
# class GrantsScholarshipPageAdmin(admin.ModelAdmin):

#     list_display = (
#         "title",
#         "status",
#         "display_order",
#     )

#     list_filter = (
#         "status",
#     )

#     search_fields = (
#         "title",
#     )

#     prepopulated_fields = {
#         "slug": ("title",)
#     }

#     ordering = (
#         "display_order",
#         "title",
#     )


# @admin.register(GrantsScholarshipSidebar)
# class GrantsScholarshipSidebarAdmin(admin.ModelAdmin):

#     list_display = (
#         "title",
#         "page",
#         "status",
#         "display_order",
#     )

#     list_filter = (
#         "page",
#         "status",
#     )

#     search_fields = (
#         "title",
#         "page__title",
#     )

#     ordering = (
#         "page",
#         "display_order",
#     )


# @admin.register(GrantsScholarshipGuide)
# class GrantsScholarshipGuideAdmin(admin.ModelAdmin):

#     list_display = (
#         "title",
#         "menu",
#         "updated_date",
#         "views",
#         "status",
#         "display_order",
#     )

#     list_filter = (
#         "menu",
#         "status",
#     )

#     search_fields = (
#         "title",
#         "menu__title",
#     )

#     ordering = (
#         "menu",
#         "display_order",
#     )


#evidance
# from django.contrib import admin

# from .models import (
#     EvidenceSynthesisPage,
#     EvidenceSynthesisSection,
#     EvidenceSynthesisSectionLink,
# )
# @admin.register(EvidenceSynthesisPage)
# class EvidenceSynthesisPageAdmin(admin.ModelAdmin):

#     list_display=("title","status","display_order")

#     prepopulated_fields={
#         "slug":("title",)
#     }

#     list_filter=("status",)

#     search_fields=("title",)

# @admin.register(EvidenceSynthesisSection)
# class EvidenceSynthesisSectionAdmin(admin.ModelAdmin):

#     list_display=(
#         "title",
#         "page",
#         "status",
#         "display_order"
#     )

#     list_filter=(
#         "page",
#         "status"
#     )

#     search_fields=("title",)


# @admin.register(EvidenceSynthesisSectionLink)
# class EvidenceSynthesisSectionLinkAdmin(admin.ModelAdmin):

#     list_display=(
#         "title",
#         "section",
#         "status"
#     )

#     list_filter=(
#         "section",
#         "status"
#     )


# help support 
from django.contrib import admin
from .models import CirculationInquiry


@admin.register(CirculationInquiry)
class CirculationInquiryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "consent_given",
        "submitted_at",
    )

    list_filter = (
        "consent_given",
        "submitted_at",
    )

    search_fields = (
        "name",
        "email",
        "question",
    )

    readonly_fields = (
        "submitted_at",
    )

    ordering = (
        "-submitted_at",
    )

    fieldsets = (
        ("User Information", {
            "fields": (
                "name",
                "email",
            )
        }),
        ("Inquiry", {
            "fields": (
                "question",
                "consent_given",
            )
        }),
        ("System Information", {
            "fields": (
                "submitted_at",
            )
        }),
    )


# techical assistance page
from .models import TechnicalAssistanceInquiry


@admin.register(TechnicalAssistanceInquiry)
class TechnicalAssistanceInquiryAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "email",
        "subject",
        "submitted_at",
    )

    search_fields = (
        "name",
        "email",
        "subject",
    )

    list_filter = (
        "submitted_at",
    )

    readonly_fields = (
        "submitted_at",
    )

    ordering = (
        "-submitted_at",
    )

# find a consultant

# from django.contrib import admin
# from .models import CitationManager

# @admin.register(CitationManager)
# class CitationManagerAdmin(admin.ModelAdmin):
#     list_display = ("name",)
#     search_fields = ("name",)


# UWDCC: Submit a Project Proposal

from django.contrib import admin
from .models import ProposalSubmission


@admin.register(ProposalSubmission)
class ProposalSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "phone",
        "institution",
        "submitted_at",
    )

    search_fields = (
        "name",
        "email",
        "institution",
    )

    list_filter = (
        "institution",
        "submitted_at",
    )

    readonly_fields = ("submitted_at",)


#  contact the UWDCC.form 

from django.contrib import admin
from .models import DigitalCollectionsContact


@admin.register(DigitalCollectionsContact)
class DigitalCollectionsContactAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "email",
        "subject",
        "created_at",
    )

    search_fields = (
        "name",
        "email",
        "subject",
        "question",
    )

    list_filter = (
        "created_at",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
    )

    fieldsets = (

        (
            "Contact Information",
            {
                "fields": (
                    "name",
                    "email",
                    "subject",
                )
            },
        ),

        (
            "Question / Comment",
            {
                "fields": (
                    "question",
                )
            },
        ),

        (
            "Submission Details",
            {
                "fields": (
                    "created_at",
                )
            },
        ),

    )

# library instruction room

# from .models import LibraryInstructionSpace

# @admin.register(LibraryInstructionSpace)
# class LibraryInstructionSpaceAdmin(admin.ModelAdmin):
#     list_display = (
#         "room_name",
#         "display_order",
#         "is_active",
#     )

#     list_editable = (
#         "display_order",
#         "is_active",
#     )

#     search_fields = ("room_name",)

from django.contrib import admin

from .models import (
    AIConversation,
    AIMessage,
)


# ============================================================
# AI MESSAGE INLINE
# ============================================================

class AIMessageInline(admin.TabularInline):
    model = AIMessage
    extra = 0

    fields = (
        "role",
        "content",
        "intent",
        "source_type",
        "created_at",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "created_at",
    )


# ============================================================
# AI CONVERSATION ADMIN
# ============================================================

@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "user",
        "is_active",
        "message_count",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "is_active",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "title",
        "user__username",
        "user__email",
    )

    readonly_fields = (
        "uuid",
        "created_at",
        "updated_at",
        "message_count",
    )

    ordering = (
        "-updated_at",
    )

    inlines = (
        AIMessageInline,
    )

    fieldsets = (
        (
            "Conversation Information",
            {
                "fields": (
                    "uuid",
                    "user",
                    "title",
                    "is_active",
                )
            },
        ),
        (
            "Statistics",
            {
                "fields": (
                    "message_count",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def message_count(self, obj):
        return obj.messages.count()

    message_count.short_description = "Messages"


# ============================================================
# AI MESSAGE ADMIN
# ============================================================

@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):

    list_display = (
        "conversation",
        "role",
        "intent",
        "source_type",
        "short_content",
        "created_at",
    )

    list_filter = (
        "role",
        "intent",
        "source_type",
        "created_at",
    )

    search_fields = (
        "content",
        "conversation__title",
        "conversation__user__username",
        "conversation__user__email",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "conversation",
        "created_at",
    )

    fieldsets = (
        (
            "Message Information",
            {
                "fields": (
                    "conversation",
                    "role",
                    "content",
                )
            },
        ),
        (
            "AI Metadata",
            {
                "fields": (
                    "intent",
                    "source_type",
                )
            },
        ),
        (
            "Timestamp",
            {
                "fields": (
                    "created_at",
                )
            },
        ),
    )

    def short_content(self, obj):
        if len(obj.content) > 80:
            return f"{obj.content[:80]}..."
        return obj.content

    short_content.short_description = "Message"