from django.shortcuts import render
from django.views.generic import TemplateView
# Navina

def libraryhome(request):
    return render(request, "Library/library.html")

def library_find(request):
    return render(request, "Library/library_find.html")

def library_borrow_req(request):
    return render(request, "Library/library_borrow_req.html")

def library_locations(request):
    return render(request, "Library/library_locations.html")

def library_give(request):
    return render(request, "Library/library_give.html")

def search_base(request):
    return render(request, 'search_base.html')

def catalog_search(request):
    return render(request,"Library/find/catalog_search.html")

def citation_search(request):
    return render(request,"Library/find/citation_search.html")

def browse_by_format(request):
    return render(request,"Library/find/browse_by_format.html")

def introductory_databases(request):
    return render(request,"Library/find/introductory_databases.html")

def explore_by_subject(request):
    return render(request, "Library/find/explore_by_subject.html")

def popular_databases(request):
    return render(request, "Library/find/popular_databases.html")

def journal_browse_by_title(request):
    return render(request, "Library/find/journal_browse_by_title.html")

def databases(request):
    return render(request, "Library/find/databases.html")

def ebooks(request):
    return render(request, "Library/find/ebooks.html")

def dissertations(request):
    return render(request, "Library/find/dissertations.html")

def other_university_dissertations(request):
    return render(request,"Library/find/other_university_dissertations.html")

def prepare_deposit(request):
    return render(request, "Library/find/prepare_deposit.html")

def browzine(request):
    return render(request, "Library/find/browzine.html")

def borrowing_policies(request):
    return render(request, "Library/borrow/borrowing_policies.html")

def renew_materials(request):
    return render(request, "Library/borrow/renew_materials.html")

def return_materials(request):
    return render(request, "Library/borrow/return_materials.html")

def open_return_libraries(request):
    return render(request, "Library/borrow/open_return_libraries.html")

def outside_book_returns(request):
    return render(request, "Library/borrow/outside_book_returns.html")

def borrowing_history(request):
    return render(request,"Library/borrow/borrowing_history.html")

def fines_blocks_holds(request):
    return render(request,"Library/borrow/fines_blocks_holds.html")

def lost_or_damaged_items(request):
    return render(request,"Library/borrow/lost_or_damaged_items.html")

def request_dissertation_thesis(request):
    return render(request,"Library/borrow/request_dissertation_thesis.html")

def request_articles(request):
    return render(request,"Library/borrow/request_articles.html")

def request_materials(request):
    return render(request,"Library/borrow/request_materials.html")

def not_affiliated_uw(request):
    return render(request,"Library/borrow/not_affiliated_uw.html")

def shelving_facilities(request):
    return render(request,"Library/borrow/shelving_facilities.html")

def on_campus_shelving_facilities(request):
    return render(request,"Library/borrow/on_campus_shelving_facilities.html",)

def request_materials_shelving_facilities(request):
    return render(request,"Library/borrow/request_materials_shelving_facilities.html",)

def shelving_facility_faq(request):
    return render(request,"Library/borrow/shelving_facility_faq.html",)

def libraries_collections_preservation_facility(request):
    return render(request,"Library/borrow/libraries_collections_preservation_facility.html",)

def preservation_facility_faq(request):
    return render(request,"Library/borrow/preservation_facility_faq.html")

def project_organization(request):
    return render(request,"Library/borrow/project_organization.html")

def verona_shelving_facility(request):
    return render(request,"Library/borrow/verona_shelving_facility.html")

def request_book_chapters(request):
    return render(request,"Library/borrow/request_book_chapters.html")

def request_books_media(request):
    return render(request,"Library/borrow/request_books_media.html")

def interlibrary_loan(request):
    return render(request,"Library/borrow/interlibrary_loan.html")

def interlibrary_loan_copyright(request):
    return render(request,"Library/borrow/interlibrary_loan_copyright.html")

def pickup_by_appointment(request):
    return render(request,"Library/Borrow/pickup_by_appointment.html")

def other_libraries(request):
    return render(request,"Library/borrow/other_libraries.html")

def uw_madison_alumni(request):
    return render(request,"Library/borrow/uw_madison_alumni.html",)

def ill_lending(request):
    return render(request,"library/borrow/ill_lending.html",)


def ill_contact_us(request):
    return render(request,"Library/borrow/ill_contact_us.html",)

def policies_and_charges(request):
    return render(request,"Library/borrow/policies_and_charges.html",)

def billing_and_shipping(request):
    return render(request,"Library/borrow/billing_and_shipping.html",)

def credit_card_payments(request):
    return render(request,"Library/borrow/credit_card_payments.html",)


def media_for_courses(request):
    return render(request,"Library/borrow/media_for_courses.html",)

def students_accessing_course_materials(request):
    return render(request,"Library/borrow/students_accessing_course_materials.html",)

def textbooks_initiative(request):
    return render(request,"Library/borrow/textbooks_initiative.html",)

def streaming_video_database_information(request):
    return render(request, "Library/borrow/streaming_video_database_information.html",)
# Access Library Resource

def library_access(request):
    return render(request, "Library/library_access.html")

def library_account(request):
    return render(request,"Library/library_account.html")
 
# rupa code
def librarybase(request):
    return render(request, 'lib_base.html')

def research_support(request):
    return render(request, "rupa/research_support/research_support.html")

def instruction_support(request):
    return render(request, "rupa/instruction_support/instruction_support.html")

def about(request):
    return render(request, "rupa/about/about.html")

def people(request):
    return render(request, "rupa/people/people.html")

def help(request):
    return render(request, "rupa/help.html")



from django.shortcuts import render, get_object_or_404

# from .models import (
#     ResearchSupportCategory,
#     ResearchSupportFeaturedResource,
#     ResearchSupportSection,
# )


# Research Support Landing Page
# def research_support(request):

#     categories = ResearchSupportCategory.objects.filter(
#         status="ACTIVE"
#     ).prefetch_related("links")

#     featured_resources = ResearchSupportFeaturedResource.objects.filter(
#         status="ACTIVE"
#     )

#     context = {
#         "categories": categories,
#         "featured_resources": featured_resources,
#     }

#     return render(
#         request,
#         "rupa/research_support.html",
#         context,
#     )


# # Research Support Detail Page
# def research_support_detail(request, slug):

#     category = get_object_or_404(
#         ResearchSupportCategory,
#         slug=slug,
#         status="ACTIVE"
#     )

#     sections = category.sections.filter(
#         status="ACTIVE"
#     ).prefetch_related("items")

#     context = {
#         "category": category,
#         "sections": sections,
#     }

#     return render(
#         request,
#         "rupa/research_support_detail.html",
#         context,
#     )

# from django.shortcuts import render
# from .models import (
#     InstructionSupportCategory,
#     InstructionSupportSidebarLink
# )

# def instruction_support(request):

#     categories = (
#         InstructionSupportCategory.objects
#         .filter(status="ACTIVE")
#         .prefetch_related("links")
#     )

#     sidebar_links = (
#         InstructionSupportSidebarLink.objects
#         .filter(status="ACTIVE")
#     )

#     context = {
#         "categories": categories,
#         "sidebar_links": sidebar_links,
#     }

#     return render(
#         request,
#         "rupa/instruction_support/instruction_support.html",
#         context,
#     )


from django.contrib import messages
from django.shortcuts import render, redirect

from .forms import InstructionRequestForm
from .notification_helpers import create_library_form_notification


def instruction_request(request):

    if request.method == "POST":

        form = InstructionRequestForm(
            request.POST
        )

        if form.is_valid():

            submission = form.save()

            create_library_form_notification(

                title="New Library Instruction Request",

                message=(
                    f"{submission.instructor_name} "
                    f"submitted a library instruction request."
                ),

                link=(
                    f"{reverse('library_form_submissions')}"
                    f"?open=instruction:{submission.id}"
                ),
            )

            messages.success(
                request,
                "Your instruction request has been submitted successfully."
            )

            return redirect(
                "instruction_support"
            )

    else:

        form = InstructionRequestForm()

    return render(
        request,
        "rupa/instruction_support/instruction_request.html",
        {
            "form": form
        },
    )


# def people(request):

#     cards = PeoplePageCard.objects.filter(
#         status="ACTIVE"
#     ).order_by("display_order")

#     context = {
#         "cards": cards,
#     }

#     return render(
#         request,
#         "rupa/people/people.html",
#         context,
#     )

# updated people dynamic card


# people/librarystaff

from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.template.loader import render_to_string

from .models import LibraryStaff


def people_directory(request):

    search = request.GET.get("search")
    library = request.GET.get("library")
    role = request.GET.get("role")

    staff = (
        LibraryStaff.objects.filter(
            is_public=True,
            active=True,
        )
        .select_related(
            "staff",
            "assigned_library",
        )
        .prefetch_related(
            "staff__subject_assignments__subject",
            "staff__department_assignments",
        )
    )

    # Search by first name, last name, preferred name and email
    if search:
        staff = staff.filter(
            Q(staff__user__first_name__icontains=search) |
            Q(staff__user__last_name__icontains=search) |
            Q(staff__preferred_name__icontains=search) |
            Q(staff__work_email__icontains=search)
        )

    # Filter by library
    if library:
        staff = staff.filter(
            assigned_library_id=library
        )

    # Filter by role
    if role:
        staff = staff.filter(
            role=role
        )

    # Sort directory
    staff = staff.order_by(
        "display_order",
        "staff__user__first_name"
    )

    paginator = Paginator(staff, 8)

    page = request.GET.get("page")

    staff = paginator.get_page(page)

    context = {
        "staff": staff,
        "libraries":Library.objects.all(),
        "roles":LibraryStaff.ROLE_CHOICES
    }

    if request.headers.get("x-requested-with")=="XMLHttpRequest":

        html=render_to_string(
            "rupa/includes/staff_cards.html",
            context,
            request=request
        )

        return JsonResponse({
            "html":html,
            "count":staff.paginator.count
        })

    return render(
        request,
        "rupa/people/people_directory.html",
        context,
    )

from django.shortcuts import render, get_object_or_404
from .models import LibraryStaff

def staff_profile(request, staff_id):

    person = get_object_or_404(
        LibraryStaff,
        id=staff_id,
        is_public=True
    )

    context = {
        "person": person
    }

    return render(
        request,
        "rupa/people/staff_profile.html",
        context
    )

# about page 
# from .models import AboutCategory, AboutCategoryLink

# def about(request):
#     categories = (
#         AboutCategory.objects
#         .filter(status="ACTIVE")
#         .prefetch_related("links")
#     )

#     context = {
#         "categories": categories,
#     }

#     return render(request, "rupa/about/about.html", context)


# collections page


def collections(request):

    return render(
        request,
        "rupa/about/collections.html",
    )

def dataset_acquisition_policy(request):
    return render(
        request,
        "rupa/about/dataset_acquisition_policy.html"
    )


def managing_physical_collections(request):
    return render(
        request,
        "rupa/about/managing_physical_collections.html"
    )


def campus_collections_plan(request):
    return render(
        request,
        "rupa/about/campus_collections_plan.html"
    )

def print_journal_management(request):
    return render(
        request,
        "rupa/about/print_journal_management.html"
    )


def shared_print_projects(request):
    return render(
        request,
        "rupa/about/shared_print_projects.html"
    )

def preservation(request):
    return render(
        request,
        "rupa/about/preservation.html"
    )

def scholarly_communication(request):
    return render(
        request,
        "rupa/research_support/scholarly_communication.html"
    )

# help page

from .models import (
    # HelpSection,
    HelpContactMethod,
    HelpSidebarLink
)


def help(request):

#     left_sections = HelpSection.objects.filter(
#         is_active=True,
#         is_horizontal=False
#     ).prefetch_related("topics")

#     horizontal_section = HelpSection.objects.filter(
#         is_active=True,
#         is_horizontal=True
#     ).prefetch_related("topics").first()

#     chat = HelpContactMethod.objects.filter(
#         method_type="CHAT",
#         library__isnull=True,
#         is_active=True
#     ).first()

#     other_contacts = HelpContactMethod.objects.filter(
#         is_active=True
#     ).exclude(
#         method_type="CHAT"
#     )

#     library_chats = HelpContactMethod.objects.filter(
#         method_type="CHAT",
#         library__isnull=False,
#         is_active=True
#     )

#     sidebar_links = HelpSidebarLink.objects.filter(
#         is_active=True
#     )

#     context = {

#         "left_sections": left_sections,

#         "horizontal_section": horizontal_section,

#         "chat": chat,

#         "other_contacts": other_contacts,

#         "library_chats": library_chats,

#         "sidebar_links": sidebar_links,

#     }

    return render(
        request,
        "rupa/help/help.html",
        
    )

# updated help section
# from django.shortcuts import render, get_object_or_404
# from django.db.models import Prefetch

# from .models import (
#     HelpTopic,
#     HelpTopicPage,
#     HelpTopicContent,
#     HelpTopicBullet,
#     HelpFAQPage,
#     HelpFAQ,
#     HelpPageSection,
#     HelpPageItem,
#     HelpTopicRelatedLink,
# )


# def help_topic_detail(request, slug):

#     topic = get_object_or_404(
#         HelpTopic,
#         slug=slug,
#         is_active=True,
#     )

#     # ==========================
#     # CATALOG PAGE
#     # ==========================
#     if topic.page_type == "CATALOG":

#         page_sections = (
#             HelpPageSection.objects
#             .filter(
#                 help_topic=topic,
#                 is_active=True,
#             )
#             .prefetch_related(
#                 Prefetch(
#                     "items",
#                     queryset=HelpPageItem.objects.filter(
#                         is_active=True
#                     ).order_by("display_order")
#                 )
#             )
#             .order_by("display_order")
#         )

#         context = {
#             "help_topic": topic,
#             "page_sections": page_sections,
#         }

#         return render(
#             request,
#             "rupa/help_section_detail.html",
#             context,
#         )

#     # ==========================
#     # CONTENT PAGE
#     # ==========================
#     elif topic.page_type == "CONTENT":

#         page = get_object_or_404(
#             HelpTopicPage,
#             help_topic=topic,
#             is_active=True,
#         )

#         sections = (
#             HelpTopicContent.objects
#             .filter(
#                 page=page,
#                 is_active=True,
#             )
#             .prefetch_related(
#                 Prefetch(
#                     "bullets",
#                     queryset=HelpTopicBullet.objects.filter(
#                         is_active=True
#                     ).order_by("display_order")
#                 ),

#                 Prefetch(
#                     "related_links",
#                     queryset=HelpTopicRelatedLink.objects.filter(
#                         is_active=True
#                     ).order_by("display_order")
#                 ),
#             )
#             .order_by("display_order")
   
#         )

#         context = {
#             "topic": topic,
#             "page": page,
#             "sections": sections,
#         }

#         return render(
#             request,
#             "rupa/help_section_detail.html",
#             context,
#         )

#     # ==========================
#     # FAQ PAGE
#     # ==========================
#     elif topic.page_type == "FAQ":

#         page = get_object_or_404(
#             HelpFAQPage,
#             help_topic=topic,
#             is_active=True,
#         )

#         faqs = HelpFAQ.objects.filter(
#             page=page,
#             is_active=True,
#         ).order_by("display_order")

#         context = {
#             "topic": topic,
#             "page": page,
#             "faqs": faqs,
#         }

#         return render(
#             request,
#             "rupa/help/help_faq.html",
#             context,
#         )

#     # ==========================
#     # DEFAULT
#     # ==========================
#     return render(
#         request,
#         "rupa/help/help.html",
#     )



# office of the dean page
# from Admin.bela_admin.models import Department
# from .models import DepartmentMember

# def office_of_the_dean(request):

#     department = Department.objects.get(
#     department_name="Office of the Dean",
#     status="ACTIVE"
#     )

#     members = (
#         DepartmentMember.objects.filter(
#             department=department
#         )
#         .select_related(
#             "staff",
#             "staff__staff",
#             "staff__staff__user",
#         )
#         .order_by("display_order")
#     )

#     return render(
#         request,
#         "rupa/office_of_the_dean.html",
#         {
#             "members": members,
#         },
#     )
from .models import OfficeOfDeanMember
def office_of_the_dean(request):
    members = (
        OfficeOfDeanMember.objects
        .select_related(
            "staff",
            "staff__staff",
            "staff__staff__user",
        )
        .order_by("display_order")
    )

    return render(
        request,
        "rupa/people/office_of_the_dean.html",
        {
            "members": members,
        },
    )


# subject librarian
from django.db.models import Prefetch
from .models import Subject, SubjectLibrarian

def subject_librarians(request):

    search = request.GET.get("search", "").strip()
    filter_type = request.GET.get("filter", "subject")

    subjects = Subject.objects.filter(
        status="ACTIVE"
    ).prefetch_related(
        Prefetch(
            "librarians",
            queryset=SubjectLibrarian.objects.filter(
                status="ACTIVE"
            ).select_related(
                "staff",
                "staff__user",
                "department",
            )
        )
    )

    if search:

        if filter_type == "subject":
            subjects = subjects.filter(
                name__icontains=search
            )

        elif filter_type == "department":
            subjects = subjects.filter(
                librarians__department__department_name__icontains=search
            ).distinct()

    return render(
        request,
        "rupa/people/subject_librarians.html",
        {
            "subjects": subjects,
        },
    )
# rupa code ends *********************************************************************

# Navina code starts 

from datetime import datetime, timedelta

from django.shortcuts import render
from django.utils import timezone

from .models import Library


def _format_library_time(value):

    if not value:
        return ""

    try:

        time_obj = datetime.strptime(
            value,
            "%H:%M"
        )

        formatted = time_obj.strftime("%I:%M %p")

        formatted = formatted.lstrip("0")

        formatted = formatted.replace(
            ":00 AM",
            " a.m."
        )

        formatted = formatted.replace(
            ":00 PM",
            " p.m."
        )

        formatted = formatted.replace(
            " AM",
            " a.m."
        )

        formatted = formatted.replace(
            " PM",
            " p.m."
        )

        return formatted

    except (ValueError, TypeError):

        return str(value)


def _get_library_hours(library, target_date=None):

    hours = library.library_hours or []

    if target_date is None:
        target_date = timezone.localdate()

    target_day = target_date.strftime("%A").strip().lower()

    # -----------------------------------------
    # Make sure hours is a list
    # -----------------------------------------

    if not isinstance(hours, list):
        return {
            "opening": "",
            "closing": "",
            "status": "CLOSED",
            "is_closed": True,
        }

    # -----------------------------------------
    # Find matching day
    # -----------------------------------------

    for row in hours:

        if not isinstance(row, dict):
            continue

        row_day = str(
            row.get("day", "")
        ).strip().lower()

        # Compare Monday / monday / MONDAY
        if row_day == target_day:

            status = str(
                row.get("status", "OPEN")
            ).strip().upper()

            opening = str(
                row.get("opening", "")
            ).strip()

            closing = str(
                row.get("closing", "")
            ).strip()

            # ---------------------------------
            # Explicitly closed
            # ---------------------------------

            if status == "CLOSED":

                return {
                    "opening": "",
                    "closing": "",
                    "status": "CLOSED",
                    "is_closed": True,
                }

            # ---------------------------------
            # Open
            # ---------------------------------

            return {
                "opening": _format_library_time(opening),
                "closing": _format_library_time(closing),
                "status": "OPEN",
                "is_closed": False,
            }

    # -----------------------------------------
    # Day was not found
    # -----------------------------------------

    return {
        "opening": "",
        "closing": "",
        "status": "CLOSED",
        "is_closed": True,
    }

def library_locations(request):

    # =====================================================
    # DATE
    # =====================================================

    selected_date = timezone.localdate()

    date_value = request.GET.get(
        "date",
        ""
    ).strip()

    if date_value:

        try:

            selected_date = datetime.strptime(
                date_value,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            selected_date = timezone.localdate()


    # =====================================================
    # FILTER VALUES
    # =====================================================

    location_id = request.GET.get(
        "location",
        ""
    ).strip()

    service_filter = request.GET.get(
        "service",
        ""
    ).strip()


    # =====================================================
    # ALL ACTIVE LIBRARIES
    # =====================================================

    all_libraries = list(
        Library.objects
        .filter(status="ACTIVE")
        .select_related("building")
        .order_by("library_name")
    )


    # =====================================================
    # FILTER LIBRARIES
    # =====================================================

    libraries = all_libraries


    if location_id:

        libraries = [
            library
            for library in libraries
            if str(library.id) == location_id
        ]


    # =====================================================
    # SERVICE CHOICES
    # =====================================================

    service_labels = dict(
        Library.SERVICE_CHOICES
    )


    # =====================================================
    # DYNAMIC SERVICE FILTER
    # =====================================================

    if location_id:

        # A specific library is selected.
        #
        # Only services selected for that library
        # will appear in the Services dropdown.

        selected_library = next(
            (
                library
                for library in all_libraries
                if str(library.id) == location_id
            ),
            None
        )

        if selected_library:

            selected_service_values = (
                selected_library.services or []
            )

        else:

            selected_service_values = []


    else:

        # All Locations selected.
        #
        # Collect services from ALL libraries.

        selected_service_values = set()

        for library in all_libraries:

            selected_service_values.update(
                library.services or []
            )


    # =====================================================
    # CREATE AVAILABLE SERVICES
    # =====================================================

    available_services = []

    for value, label in Library.SERVICE_CHOICES:

        if value in selected_service_values:

            available_services.append(
                (value, label)
            )


    # =====================================================
    # SERVICE FILTER
    # =====================================================

    if service_filter:

        libraries = [
            library
            for library in libraries
            if service_filter in (
                library.services or []
            )
        ]


    # =====================================================
    # PREPARE LIBRARY DATA
    # =====================================================

    for library in libraries:

        # ---------------------------------------------
        # SERVICE LABELS
        # ---------------------------------------------

        library.service_labels = [

            service_labels.get(
                service,
                service
            )

            for service in (
                library.services or []
            )

        ]


        # ---------------------------------------------
        # THREE DAYS
        # ---------------------------------------------

        library.location_days = []


        for offset in range(3):

            current_date = (
                selected_date
                + timedelta(days=offset)
            )

            hours = _get_library_hours(
                library,
                current_date
            )


            library.location_days.append({

                "date": current_date,

                "day_name":
                    current_date.strftime("%A"),

                "month_day":
                    f"{current_date.strftime('%B')} "
                    f"{current_date.day}",

                "hours":
                    hours,

            })


    # =====================================================
    # ADDITIONAL RESOURCES
    # =====================================================

    additional_resources = [
        {
            "title": "Campus Map",
        },
        {
            "title": "Printing and Photocopies",
        },
        {
            "title": "Study Rooms",
        },
    ]


    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "libraries":
            libraries,

        "all_libraries":
            all_libraries,

        "available_services":
            available_services,

        "additional_resources":
            additional_resources,

        "selected_date":
            selected_date,

        "selected_date_value":
            selected_date.strftime(
                "%Y-%m-%d"
            ),

        "selected_location":
            location_id,

        "selected_service":
            service_filter,

    }


    return render(
        request,
        "Library/library_locations.html",
        context
    )

# def library_borrow_req(request):
#     cards = BorrowCard.objects.filter(
#         active=True
#     ).prefetch_related('links')

#     sidebar_links = LibraryAdditionalResource.objects.filter(
#     active=True,
#     page_type='BORROW'
#     ).order_by('display_order')

#     context = {
#         'cards': cards,
#         'sidebar_links': sidebar_links,
#     }

#     return render(
#         request,
#         'Library/library_borrow_req.html',
#         context
#     )


def library_give(request):
 
    giving = GivingPage.objects.filter(
        active=True
    ).first()
 
    sidebar_links = LibraryAdditionalResource.objects.filter(
        active=True,
        page_type='GIVING'
    ).order_by(
        'display_order'
    )
 
    context = {
        'giving': giving,
        'sidebar_links': sidebar_links,
    }
 
    return render(
        request,
        'Library/library_give.html',
        context
    )

from django.shortcuts import render
from .models import (
    Library,
    LibraryResource,
)

def advanced_search(request):

    # -----------------------------
    # Dropdown Data
    # -----------------------------

    libraries = Library.objects.filter(
        status="ACTIVE"
    ).order_by("library_name")

    formats = (
        LibraryResource.objects
        .values_list("resource_type", flat=True)
        .distinct()
        .order_by("resource_type")
    )

    languages = (
        LibraryResource.objects
        .exclude(language__isnull=True)
        .exclude(language="")
        .values_list("language", flat=True)
        .distinct()
        .order_by("language")
    )

    # -----------------------------
    # Initial Query
    # -----------------------------

    resources = LibraryResource.objects.filter(
        status="ACTIVE"
    ).select_related(
        "library",
        "category",
    )

    # -----------------------------
    # Read GET Parameters
    # -----------------------------

    available_online = request.GET.get("available_online")

    print_items = request.GET.get("print_items")

    match = request.GET.get(
        "match",
        "all"
    )

    keywords = request.GET.get(
        "keywords",
        ""
    ).strip()

    title = request.GET.get(
        "title",
        ""
    ).strip()

    author = request.GET.get(
        "author",
        ""
    ).strip()

    publisher = request.GET.get(
        "publisher",
        ""
    ).strip()

    identifiers = request.GET.get(
        "identifiers",
        ""
    ).strip()

    subjects = request.GET.get(
        "subjects",
        ""
    ).strip()

    publication_start = request.GET.get(
        "publication_start",
        ""
    )

    publication_end = request.GET.get(
        "publication_end",
        ""
    )

    location = request.GET.get(
        "location",
        ""
    )

    resource_format = request.GET.get(
        "format",
        ""
    )

    language = request.GET.get(
        "language",
        ""
    )

    # -----------------------------
    # Apply Filters
    # -----------------------------

    if title:

        resources = resources.filter(
            title__icontains=title
        )

    if author:

        resources = resources.filter(
            author__icontains=author
        )

    if publisher:

        resources = resources.filter(
            publisher__icontains=publisher
        )

    if identifiers:

        resources = resources.filter(
            isbn_issn__icontains=identifiers
        )

    if subjects:

        resources = resources.filter(
            subject__icontains=subjects
        )

    if publication_start:

        resources = resources.filter(
            publication_year__gte=publication_start
        )

    if publication_end:

        resources = resources.filter(
            publication_year__lte=publication_end
        )

    if location:

        resources = resources.filter(
            library_id=location
        )

    if resource_format:

        resources = resources.filter(
            resource_type=resource_format
        )

    if language:

        resources = resources.filter(
            language=language
        )

    if available_online:

        resources = resources.filter(
            resource_type="EBOOK"
        )

    if print_items:

        resources = resources.exclude(
            resource_type="EBOOK"
        )

    # -----------------------------
    # Keyword Search
    # -----------------------------

    if keywords:

        resources = resources.filter(
            title__icontains=keywords
        ) | LibraryResource.objects.filter(
            author__icontains=keywords
        ) | LibraryResource.objects.filter(
            publisher__icontains=keywords
        ) | LibraryResource.objects.filter(
            subject__icontains=keywords
        )

    # -----------------------------
    # Context
    # -----------------------------

    context = {

        "resources": resources.distinct(),

        "libraries": libraries,

        "formats": formats,

        "languages": languages,

    }

    return render(

        request,

        "Library/find/advanced_search.html",

        context,

    )

from django.shortcuts import render
from django.db.models import Count
from .models import LibraryResource


def browse_subjects(request):

    search = request.GET.get("q", "")

    subjects = (
        LibraryResource.objects
        .exclude(subject__isnull=True)
        .exclude(subject="")
        .values("subject")
        .annotate(total=Count("id"))
        .order_by("subject")
    )

    if search:
        subjects = subjects.filter(
            subject__icontains=search
        )

    context = {

        "subjects": subjects,

        "search": search,

    }

    return render(

        request,

        "Library/find/browse_subjects.html",

        context,

    )
from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator

from .models import (
    LibraryResource,
    Library,
    ResourceCategory,
)


def catalog_search(request):

    # ==================================================
    # GET VALUES
    # ==================================================

    # Main search text
    query = request.GET.get(
        "query",
        ""
    ).strip()

    # Keywords / Title / Author / Subject
    search_by = request.GET.get(
        "search_by",
        "keywords"
    )

    # Used when search comes from:
    # Journals page -> JOURNAL
    # Articles page -> ARTICLE
    # Books page -> BOOK
    #
    # Catalog page does not send resource_type,
    # so all active resources will be searched.
    resource_type = request.GET.get(
        "resource_type",
        ""
    )

    # Current tab
    tab = request.GET.get(
        "tab",
        "catalog"
    )

    # Modal / Quick Search Filters
    library = request.GET.get(
        "library"
    )

    format_filter = request.GET.get(
        "format"
    )

    author = request.GET.get(
        "author"
    )

    subject = request.GET.get(
        "subject"
    )

    language = request.GET.get(
        "language"
    )

    year = request.GET.get(
        "year"
    )

    category = request.GET.get(
        "category"
    )

    # Checkboxes
    online = request.GET.get(
        "online"
    )

    print_only = request.GET.get(
        "print_only"
    )

    limit_uw = request.GET.get(
        "limit_uw"
    )

    scholarly = request.GET.get("scholarly")

    open_access = request.GET.get("open_access")

    # Sorting
    sort = request.GET.get(
        "sort",
        "title"
    )


    # ==================================================
    # BASE QUERYSET
    # ==================================================

    resources = (
        LibraryResource.objects
        .filter(
            status="ACTIVE"
        )
        .select_related(
            "library",
            "category"
        )
    )


    # ==================================================
    # RESOURCE TYPE FILTER
    # ==================================================
    #
    # Catalog Browse:
    # No resource_type -> Searches everything
    #
    # Journals Browse:
    # resource_type=JOURNAL -> Searches journals only
    #
    # Articles Browse:
    # resource_type=ARTICLE -> Searches articles only
    #
    # Books Browse:
    # resource_type=BOOK -> Searches books only
    # ==================================================

    if resource_type:

        resources = resources.filter(
            resource_type=resource_type
        )


    # ==================================================
    # SEARCH
    # ==================================================

    if query:

        # ------------------------------
        # Search by Title
        # ------------------------------

        if search_by == "title":

            resources = resources.filter(
                title__icontains=query
            )


        # ------------------------------
        # Search by Author
        # ------------------------------

        elif search_by == "author":

            resources = resources.filter(
                author__icontains=query
            )


        # ------------------------------
        # Search by Subject
        # ------------------------------

        elif search_by == "subject":

            resources = resources.filter(
                subject__icontains=query
            )


        # ------------------------------
        # Keyword Search
        # ------------------------------

        else:

            resources = resources.filter(

                Q(title__icontains=query) |

                Q(author__icontains=query) |

                Q(subject__icontains=query) |

                Q(isbn_issn__icontains=query)

            )


    # ==================================================
    # LIBRARY FILTER
    # ==================================================

    if library:

        resources = resources.filter(
            library_id=library
        )


    # ==================================================
    # FORMAT FILTER
    # ==================================================

    if format_filter:

        resources = resources.filter(
            resource_type=format_filter
        )


    # ==================================================
    # AUTHOR FILTER
    # ==================================================

    if author:

        resources = resources.filter(
            author=author
        )


    # ==================================================
    # SUBJECT FILTER
    # ==================================================

    if subject:

        resources = resources.filter(
            subject=subject
        )


    # ==================================================
    # LANGUAGE FILTER
    # ==================================================

    if language:

        resources = resources.filter(
            language=language
        )


    # ==================================================
    # PUBLICATION YEAR FILTER
    # ==================================================

    if year:

        resources = resources.filter(
            publication_year=year
        )


    # ==================================================
    # CATEGORY FILTER
    # ==================================================

    if category:

        try:

            resources = resources.filter(
                category_id=int(category)
            )

        except (ValueError, TypeError):

            pass


    # ==================================================
    # AVAILABLE ONLINE FILTER
    # ==================================================
    #
    # IMPORTANT:
    # This uses digitalresource because that is what
    # you used in your previous catalog_search view.
    #
    # If your DigitalResource model uses:
    #
    # related_name="digital_resource"
    #
    # then change:
    #
    # digitalresource__isnull=False
    #
    # to:
    #
    # digital_resource__isnull=False
    # ==================================================

    if online:

        resources = resources.filter(
            digitalresource__isnull=False
        )

    if scholarly:
        resources = resources.filter(
        is_scholarly=True
    )

    if open_access:
        resources = resources.filter(
        is_open_access=True
    )


    # ==================================================
    # PRINT / PHYSICAL ITEMS
    # ==================================================

    if print_only:

        resources = resources.filter(
            available_copies__gt=0
        )


    # ==================================================
    # LIMIT TO UW-MADISON
    # ==================================================

    if limit_uw:

        resources = resources.filter(
            library__status="ACTIVE"
        )


    # ==================================================
    # REMOVE DUPLICATES
    # ==================================================

    resources = resources.distinct()


    # ==================================================
    # SORTING
    # ==================================================

    if sort == "oldest":

        resources = resources.order_by(
            "publication_year",
            "title"
        )

    elif sort == "newest":

        resources = resources.order_by(
            "-publication_year",
            "title"
        )

    elif sort == "author_asc":

        resources = resources.order_by(
            "author",
            "title"
        )

    elif sort == "author_desc":

        resources = resources.order_by(
            "-author",
            "title"
        )

    elif sort == "title_desc":

        resources = resources.order_by(
            "-title"
        )

    else:

        # Default: Title A-Z

        resources = resources.order_by(
            "title"
        )


    # ==================================================
    # FILTER MODAL BASE DATA
    # ==================================================
    #
    # For normal Catalog Search:
    # Show filters from all active resources.
    #
    # For Journal Search:
    # Show filters related to JOURNAL resources.
    #
    # For Article Search:
    # Show filters related to ARTICLE resources.
    # ==================================================

    filter_resources = (
        LibraryResource.objects
        .filter(
            status="ACTIVE"
        )
    )


    if resource_type:

        filter_resources = filter_resources.filter(
            resource_type=resource_type
        )


    # ==================================================
    # LIBRARIES FOR MODAL
    # ==================================================

    libraries = (
        Library.objects
        .filter(
            status="ACTIVE"
        )
        .order_by(
            "library_name"
        )
    )


    # ==================================================
    # FORMATS FOR MODAL
    # ==================================================

    formats = (
        filter_resources
        .values_list(
            "resource_type",
            flat=True
        )
        .distinct()
        .order_by(
            "resource_type"
        )
    )


    # ==================================================
    # AUTHORS FOR MODAL
    # ==================================================

    authors = (
        filter_resources
        .exclude(
            author__isnull=True
        )
        .exclude(
            author=""
        )
        .values_list(
            "author",
            flat=True
        )
        .distinct()
        .order_by(
            "author"
        )
    )


    # ==================================================
    # SUBJECTS FOR MODAL
    # ==================================================

    subjects = (
        filter_resources
        .exclude(
            subject__isnull=True
        )
        .exclude(
            subject=""
        )
        .values_list(
            "subject",
            flat=True
        )
        .distinct()
        .order_by(
            "subject"
        )
    )


    # ==================================================
    # LANGUAGES FOR MODAL
    # ==================================================

    languages = (
        filter_resources
        .exclude(
            language__isnull=True
        )
        .exclude(
            language=""
        )
        .values_list(
            "language",
            flat=True
        )
        .distinct()
        .order_by(
            "language"
        )
    )


    # ==================================================
    # YEARS FOR MODAL
    # ==================================================

    years = (
        filter_resources
        .exclude(
            publication_year__isnull=True
        )
        .values_list(
            "publication_year",
            flat=True
        )
        .distinct()
        .order_by(
            "-publication_year"
        )
    )


    # ==================================================
    # CONTENT TYPES FOR MODAL
    # ==================================================

    content_types = (
        ResourceCategory.objects
        .filter(status="ACTIVE")
        .order_by("title")
    )


    # ==================================================
    # PAGINATION
    # ==================================================

    paginator = Paginator(
        resources,
        10
    )

    page_number = request.GET.get(
        "page"
    )

    books = paginator.get_page(
        page_number
    )


    # ==================================================
    # DYNAMIC PAGE TITLE / NO RESULTS MESSAGE
    # ==================================================

    if resource_type == "JOURNAL":

        result_heading = "Journal Search Results"

        no_results_title = "No journals found"

        if query:

            no_results_message = (
                f'No journals were found matching "{query}".'
            )

        else:

            no_results_message = (
                "There are currently no journals available."
            )


    elif resource_type == "ARTICLE":

        result_heading = "Article Search Results"

        no_results_title = "No articles found"

        if query:

            no_results_message = (
                f'No articles were found matching "{query}".'
            )

        else:

            no_results_message = (
                "There are currently no articles available."
            )


    elif resource_type == "BOOK":

        result_heading = "Book Search Results"

        no_results_title = "No books found"

        if query:

            no_results_message = (
                f'No books were found matching "{query}".'
            )

        else:

            no_results_message = (
                "There are currently no books available."
            )


    else:

        result_heading = "Catalog Search Results"

        no_results_title = "No results found"

        if query:

            no_results_message = (
                f'No resources were found matching "{query}".'
            )

        else:

            no_results_message = (
                "There are currently no resources available."
            )


    # ==================================================
    # CONTEXT
    # ==================================================

    context = {

        # ------------------------------------------
        # Search Results
        # ------------------------------------------

        # Keeping "books" because your existing
        # catalog_search.html may already use:
        #
        # {% for book in books %}
        #
        "books": books,


        # ------------------------------------------
        # Search Values
        # ------------------------------------------

        "query": query,

        "search_by": search_by,

        "resource_type": resource_type,


        # ------------------------------------------
        # Checkbox Values
        # ------------------------------------------

        "online": online,

        "print_only": print_only,

        "limit_uw": limit_uw,

        "scholarly": scholarly,
        
        "open_access": open_access,


        # ------------------------------------------
        # Sorting
        # ------------------------------------------

        "sort": sort,


        # ------------------------------------------
        # Dynamic Result Messages
        # ------------------------------------------

        "result_heading": result_heading,

        "no_results_title": no_results_title,

        "no_results_message": no_results_message,


        # ------------------------------------------
        # Filter Modal Data
        # ------------------------------------------

        "libraries": libraries,

        "formats": formats,

        "authors": authors,

        "subjects": subjects,

        "languages": languages,

        "years": years,

        "content_types": content_types,


        # ------------------------------------------
        # Currently Selected Filters
        # ------------------------------------------

        "context_library": library,

        "context_format": format_filter,

        "context_author": author,

        "context_subject": subject,

        "context_language": language,

        "context_year": year,

        "context_category": category,

        "context_tab": tab,

    }


    # ==================================================
    # RENDER
    # ==================================================

    return render(
        request,
        "Library/find/catalog_search.html",
        context
    )

from django.shortcuts import render

from django.db.models import Q, Count

from django.core.paginator import Paginator

from .models import LibraryResource, DigitalResource

def catalog_browse(request): 

    # ------------------------------------------
    # GET Parameters
    # ------------------------------------------

    query = request.GET.get("query", "").strip()

    search_by = request.GET.get("search_by", "keywords")

    library_id = request.GET.get("library")

    resource_type = request.GET.get("format")

    media = request.GET.get("media")

    subject = request.GET.get("subject")

    author = request.GET.get("author")

    language = request.GET.get("language")

    year = request.GET.get("year")

    online = request.GET.get("online")

    print_only = request.GET.get("print_only")

    limit_uw = request.GET.get("limit_uw")

    # ------------------------------------------
    # Base Query
    # ------------------------------------------

    books = (

        LibraryResource.objects

        .filter(status="ACTIVE")

        .select_related("library", "category")

        .order_by("title")

    )
    # ------------------------------------------
    # Search
    # ------------------------------------------

    if query:

        if search_by == "title":

            books = books.filter(

                title__icontains=query

            )

        elif search_by == "author":

            books = books.filter(

                author__icontains=query

            )

        elif search_by == "subject":

            books = books.filter(

                subject__icontains=query

            )

        else:

            books = books.filter(

                Q(title__icontains=query) |

                Q(author__icontains=query) |

                Q(subject__icontains=query) |

                Q(isbn_issn__icontains=query)


            )

    # ------------------------------------------
    # Filters
    # ------------------------------------------

    if library_id:

        books = books.filter(

            library_id=library_id

        )

    if resource_type:

        books = books.filter(

            resource_type=resource_type

        )

    if media:

        books = books.filter(

            resource_type=media

        )

    if subject:

        books = books.filter(

            subject=subject

        )

    if author:

        books = books.filter(

            author=author

        )

    if language:

        books = books.filter(

            language=language

        )

    if year:

        books = books.filter(

            publication_year=year

        )

    # ------------------------------------------
    # Available Online
    # ------------------------------------------

    if online:

        books = books.filter(

            digital_resource__isnull=False

        )

    # ------------------------------------------
    # Print Only
    # ------------------------------------------

    if print_only:

        books = books.filter(

            digital_resource__isnull=True

        )

    # ------------------------------------------
    # Limit to UW Madison
    # ------------------------------------------

    if limit_uw:

        books = books.filter(

            library__status="ACTIVE"

        )

    # ------------------------------------------
    # Quick Search Counts
    # ------------------------------------------

    libraries = (

        LibraryResource.objects

        .filter(status="ACTIVE")

        .values(

            "library__id",

            "library__library_name"

        )

        .annotate(

            total=Count("id")

        )

        .order_by(

            "library__library_name"

        )

    )

    formats = (

        LibraryResource.objects

        .filter(status="ACTIVE")

        .values(

            "resource_type"

        )
        .annotate(

            total=Count("id")

        )

        .order_by(

            "resource_type"

        )
    )

    media_types = formats

    subjects = (

        LibraryResource.objects

        .filter(status="ACTIVE")

        .exclude(subject="")

        .values("subject")

        .annotate(

            total=Count("id")

        )

        .order_by(

            "subject"

        )
    )

    authors = (
        LibraryResource.objects

        .filter(status="ACTIVE")

        .exclude(author="")

        .values("author")

        .annotate(

            total=Count("id")

        )

        .order_by(

            "author"

        )

    )
    languages = (

        LibraryResource.objects

        .filter(status="ACTIVE")

        .exclude(language="")

        .values("language")

        .annotate(

            total=Count("id")

        )

        .order_by(

            "language"

        )

    )

    years = (

        LibraryResource.objects

        .filter(status="ACTIVE")

        .exclude(publication_year=None)

        .values(

            "publication_year"

        )

        .annotate(

            total=Count("id")

        )

        .order_by(

            "-publication_year"

        )

    )

    # ------------------------------------------
    # Quick Search Libraries Pagination
    # ------------------------------------------

    paginator = Paginator(
       libraries,
       21
    )

    page_number = request.GET.get(
      "page"
    )

    libraries = paginator.get_page(
      page_number
    )

    # ------------------------------------------
    # Context
    # ------------------------------------------

    context = {
        "books": books,

        "query": query,

        "search_by": search_by,

        "online": online,

        "print_only": print_only,

        "limit_uw": limit_uw,

        "libraries": libraries,

        "formats": formats,

        "media_types": media_types,

        "subjects": subjects,

        "authors": authors,

        "languages": languages,

        "years": years,

    }

    return render(

        request,

        "Library/find/catalog_browse.html", 

        context

    )

from django.shortcuts import render
from django.db.models import Count
from django.core.paginator import Paginator

from .models import LibraryResource


def journals_browse(request):

    # ==================================================
    # BASE JOURNAL QUERYSET
    # Only active JOURNAL resources
    # ==================================================

    journals = LibraryResource.objects.filter(
        status="ACTIVE",
        resource_type="JOURNAL"
    )


    # ==================================================
    # QUICK SEARCH - LIBRARIES
    # ==================================================

    libraries_queryset = (
        journals
        .filter(library__isnull=False)
        .values(
            "library__id",
            "library__library_name"
        )
        .annotate(
            total=Count("id")
        )
        .order_by(
            "library__library_name"
        )
    )


    # ==================================================
    # LIBRARIES PAGINATION
    # ==================================================

    # Show 21 libraries per page.
    # With col-lg-4 this gives 3 columns x 7 rows.

    library_paginator = Paginator(
        libraries_queryset,
        21
    )

    library_page_number = request.GET.get(
        "library_page"
    )

    libraries = library_paginator.get_page(
        library_page_number
    )


    # ==================================================
    # QUICK SEARCH - SUBJECTS
    # ==================================================

    subjects = (
        journals
        .exclude(subject__isnull=True)
        .exclude(subject="")
        .values(
            "subject"
        )
        .annotate(
            total=Count("id")
        )
        .order_by(
            "subject"
        )
    )


    # ==================================================
    # QUICK SEARCH - CREATORS
    # Author field is used as Creator
    # ==================================================

    creators = (
        journals
        .exclude(author__isnull=True)
        .exclude(author="")
        .values(
            "author"
        )
        .annotate(
            total=Count("id")
        )
        .order_by(
            "author"
        )
    )


    # ==================================================
    # QUICK SEARCH - LANGUAGES
    # ==================================================

    languages = (
        journals
        .exclude(language__isnull=True)
        .exclude(language="")
        .values(
            "language"
        )
        .annotate(
            total=Count("id")
        )
        .order_by(
            "language"
        )
    )


    # ==================================================
    # CONTEXT
    # ==================================================

    context = {

        # Paginated libraries
        "libraries": libraries,

        # Other quick-search data
        "subjects": subjects,
        "creators": creators,
        "languages": languages,


    }


    # ==================================================
    # RENDER
    # ==================================================

    return render(
        request,
        "Library/find/journals_browse.html",
        context
    )

# Appeal form of borrow page
from django.contrib import messages
from django.shortcuts import render, redirect

from .forms import FineAppealForm


def appeal_library_charges(request):

    if request.method == "POST":

        form = FineAppealForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Your appeal request has been submitted successfully."
            )

            return redirect("appeal_library_charges")

    else:

        form = FineAppealForm()

    return render(

        request,

        "Library/borrow/appeal_library_charges.html",

        {

            "form": form,

        }

    )

from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import ContactRequestForm
from .notification_helpers import create_library_form_notification


def contact_us(request):

    if request.method == "POST":

        form = ContactRequestForm(
            request.POST
        )

        if form.is_valid():

            submission = form.save()

            create_library_form_notification(

                title="New Library Contact Request",

                message=(
                    f"{submission.name} submitted "
                    f"a new contact request."
                ),

                link=(
                    f"{reverse('library_form_submissions')}"
                    f"?open=contact:{submission.id}"
                ),
            )

            messages.success(
                request,
                "Thank you! Your message has been submitted successfully."
            )

            return redirect(
                "contact_us"
            )

    else:

        form = ContactRequestForm()

    return render(
        request,
        "Library/borrow/contact_us.html",
        {
            "form": form
        },
    )
from django.contrib import messages
from django.shortcuts import render, redirect

from .forms import RequestPurchaseForm


def request_purchase(request):

    if request.method == "POST":

        form = RequestPurchaseForm(request.POST)

        if form.is_valid():

            # Save the submitted email
            form.save()

            # Redirect to Sign In page
            return redirect("login")

    else:

        form = RequestPurchaseForm()

    context = {
        "form": form,
    }

    return render(
        request,
        "Library/Borrow/request_purchase.html",
        context,
    )

from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import ShelvingFacilityRequestForm
from .notification_helpers import create_library_form_notification


def shelving_request(request):

    if request.method == "POST":

        form = ShelvingFacilityRequestForm(request.POST)

        if form.is_valid():

            submission = form.save()

            full_name = (
                f"{submission.first_name} "
                f"{submission.last_name}"
            ).strip()

            create_library_form_notification(
                title="New Shelving Facility Request",
                message=(
                    f"{full_name} submitted a shelving facility "
                    f"request for '{submission.title}'."
                ),
                link=(
                    f"{reverse('library_form_submissions')}"
                    f"?open=shelving:{submission.id}"
                )
            )

            messages.success(
                request,
                "Your shelving facility request has been submitted successfully."
            )

            return redirect("shelving_request")

    else:

        form = ShelvingFacilityRequestForm()

    return render(
        request,
        "Library/borrow/shelving_request.html",
        {"form": form},
    )


# datapage
# from django.shortcuts import get_object_or_404, render
# from .models import (
#     DataManagementPlan,
#     DataManagementSidebar,
#     DataManagementPlanSection,
# )

# def data_management_plan_detail(request, slug):
#     page = get_object_or_404(
#         DataManagementPlan,
#         slug=slug,
#         status="ACTIVE"
#     )

#     menus = page.menus.filter(
#         status="ACTIVE"
#     ).order_by("display_order")

#     sections = (
#         DataManagementPlanSection.objects
#         .filter(
#             menu__page=page,
#             status="ACTIVE"
#         )
#         .prefetch_related("links")
#         .select_related("menu")
#         .order_by(
#             "menu__display_order",
#             "display_order"
#         )
#     )

#     return render(
#         request,
#         "rupa/research_support/data_management_plan_detail.html",
#         {
#             "page": page,
#             "menus": menus,
#             "sections": sections,
#         },
#     )

# from django.shortcuts import render

# def data_management_plan_detail(request):
#     return render(
#         request,
#         "rupa/research_support/data_management_plan_detail.html"
#     )
    
    
# grants and scholarships
# from django.shortcuts import render

# from .models import (
#     GrantsScholarshipPage,
#     GrantsScholarshipGuide,
# )


# def grants_scholarships_detail(request, slug):

#     page = GrantsScholarshipPage.objects.filter(
#         slug=slug,
#         status="ACTIVE"
#     ).first()

#     if page:
#         menus = page.menus.filter(status="ACTIVE")

#         guides = (
#             GrantsScholarshipGuide.objects.filter(
#                 menu__page=page,
#                 status="ACTIVE"
#             )
#             .select_related("menu")
#             .order_by("display_order")
#         )

#     else:
#         menus = []
#         guides = []

#     return render(
#         request,
#         "rupa/research_support/grants_scholarships_detail.html",
#         {
#             "page": page,
#             "menus": menus,
#             "guides": guides,
#         },
#     )


# from django.shortcuts import render, get_object_or_404

# from .models import (
#     EvidenceSynthesisPage,
#     EvidenceSynthesisSection,
# )
# def evidence_synthesis_detail(request, slug):

#     page = get_object_or_404(
#         EvidenceSynthesisPage,
#         slug=slug,
#         status="ACTIVE"
#     )

#     sections = (
#         EvidenceSynthesisSection.objects.filter(
#             page=page,
#             status="ACTIVE"
#         )
#         .prefetch_related("links")
#         .order_by("display_order")
#     )

#     context = {
#         "page": page,
#         "sections": sections,
#     }

#     return render(
#         request,
#         "rupa/research_support/evidence_synthesis_detail.html",

#     )

# navina code
from django.shortcuts import render
from .models import LibraryResource


def book_details(request, pk):
    """
    Dynamic Book Details Page
    """

    # ---------------------------------------------------
    # Get Books
    # ---------------------------------------------------
    books = LibraryResource.objects.filter(
    status="ACTIVE",
    resource_type="BOOK"
    ).select_related(
        "library",
        "category"
    ).order_by("id")

    # ---------------------------------------------------
    # Current Book
    # ---------------------------------------------------
    book = books.filter(pk=pk).first()

    # ---------------------------------------------------
    # If Book Not Found
    # ---------------------------------------------------
    if not book:

        return render(
            request,
            "Library/find/book_details.html",
            {
                "book": None,
                "books": [],
                "related_books": [],
                "previous_book": None,
                "next_book": None,
                "total_results": 0,
                "current_position": 0,
                "library_staff": [],
            },
        )

    # ---------------------------------------------------
    # Total Results
    # ---------------------------------------------------
    total_results = books.count()

    # ---------------------------------------------------
    # Current Position
    # ---------------------------------------------------
    book_ids = list(
        books.values_list("id", flat=True)
    )

    current_position = book_ids.index(book.id) + 1

    # ---------------------------------------------------
    # Previous Book
    # ---------------------------------------------------
    previous_book = books.filter(
        id__lt=book.id
    ).order_by("-id").first()

    # ---------------------------------------------------
    # Next Book
    # ---------------------------------------------------
    next_book = books.filter(
        id__gt=book.id
    ).order_by("id").first()

    # ---------------------------------------------------
    # Related Books - Same Subject
    # ---------------------------------------------------
    related_books = LibraryResource.objects.filter(
        status="ACTIVE",
        resource_type="BOOK",
        subject=book.subject
    ).exclude(
        pk=book.pk
    ).order_by("title")

    # ---------------------------------------------------
    # If no subject match, use same category
    # ---------------------------------------------------
    if not related_books.exists():

        related_books = LibraryResource.objects.filter(
            status="ACTIVE",
            resource_type="BOOK",
            category=book.category
        ).exclude(
            pk=book.pk
        )[:10]

    # ---------------------------------------------------
    # If still empty, show other Python books
    # ---------------------------------------------------
    if not related_books.exists():

        related_books = LibraryResource.objects.filter(
            status="ACTIVE",
            resource_type="BOOK",
            title__icontains="python"
        ).exclude(
            pk=book.pk
        )[:10]

    # ---------------------------------------------------
    # Context
    # ---------------------------------------------------
    context = {
        "book": book,
        "books": books,
        "total_results": total_results,
        "current_position": current_position,
        "previous_book": previous_book,
        "next_book": next_book,
        "related_books": related_books,
        "library_staff": [],
    }

    # ---------------------------------------------------
    # Render Page
    # ---------------------------------------------------
    return render(
        request,
        "Library/find/book_details.html",
        context,
    )


from django.shortcuts import render
from .models import LibraryResource


def articles(request):

    query = request.GET.get("q", "")
    search_by = request.GET.get("search_by", "anywhere")

    articles = LibraryResource.objects.filter(
        resource_type="ARTICLE",
        status="ACTIVE"
    )

    if query:

        if search_by == "title":
            articles = articles.filter(title__icontains=query)

        elif search_by == "author":
            articles = articles.filter(author__icontains=query)

        elif search_by == "subject":
            articles = articles.filter(subject__icontains=query)

        else:
            articles = articles.filter(title__icontains=query)

    context = {
        "articles": articles,
        "query": query,
        "search_by": search_by,
    }

    return render(request, "Library/find/articles.html", context)

# rupa code********************
# help support 

from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import CirculationInquiryForm
from .notification_helpers import create_library_form_notification


def circulation_assistance(request):

    if request.method == "POST":

        form = CirculationInquiryForm(
            request.POST
        )

        if form.is_valid():

            submission = form.save()

            create_library_form_notification(

                title="New Circulation Assistance Request",

                message=(
                    f"{submission.name} submitted a "
                    f"circulation assistance request."
                ),

                link=(
                    f"{reverse('library_form_submissions')}"
                    f"?open=circulation:{submission.id}"
                ),
            )

            messages.success(
                request,
                "Thanks for your message! Please submit "
                "one form per question and library staff "
                "will work as a team to respond."
            )

            return redirect(
                "circulation_assistance"
            )

    else:

        form = CirculationInquiryForm()

    return render(
        request,
        "rupa/help/circulation_assistance.html",
        {
            "form": form
        },
    )

from django.shortcuts import render

def planning_research_project(request):
    return render(
        request,
        "rupa/research_support/planning_research_support.html",
        {
            "active_menu": "research_support",
        }
    )
    
def evidence_synthesis(request):
    return render(request, "rupa/research_support/evidence_synthesis.html")

def id_problems(request):
    return render(request, "rupa/help/id_problems.html")

def off_campus_access(request):
    return render(request, "rupa/help/off_campus_access.html")

def library_catalog_help(request):
    return render(request, "rupa/help/library_catalog_help.html")

def research_support_cards(request):
    return render(request, "rupa/research_support/research_support_page.html")


# technical assistance page

from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import TechnicalAssistanceInquiryForm
from .notification_helpers import create_library_form_notification


def technical_assistance(request):

    if request.method == "POST":

        form = TechnicalAssistanceInquiryForm(
            request.POST
        )

        if form.is_valid():

            submission = form.save()

            create_library_form_notification(

                title="New Technical Assistance Request",

                message=(
                    f"{submission.name} submitted a "
                    f"technical assistance request: "
                    f"{submission.subject}"
                ),

                link=(
                    f"{reverse('library_form_submissions')}"
                    f"?open=technical:{submission.id}"
                ),
            )

            messages.success(
                request,
                "Thank you for submitting your request."
            )

            return redirect(
                "technical_assistance"
            )

    else:

        form = TechnicalAssistanceInquiryForm()

    return render(
        request,
        "rupa/help/technical_assistance.html",
        {
            "form": form
        },
    )


def finding_evaluating_information(request):
    return render(
        request,
        "rupa/research_support/finding_evaluating_information.html"
    )


def data_services(request):
    return render(
        request,
        "rupa/research_support/data_services.html"
    )

# def reusing_data(request):
#     return render(
#         request,
#         "rupa/research_support/datasets.html"
#     )


def interlibrary_loan_faq(request):
    return render(request, "rupa/help/interlibrary_loan_faq.html")


def finding_reusing_citing_data(request):
    return render(request, "rupa/research_support/datasets.html")

def collecting_organizing_analyzing_information(request):
    return render(
        request,
        "rupa/research_support/collecting_organizing_information.html"
    )


def patent_services(request):
    return render(request, "rupa/research_support/patent_services.html")


def citation_managers(request):
    return render(request, "rupa/research_support/citation_managers.html")


def library_instruction_options(request):
    return render(request, "rupa/instruction_support/instruction_options.html")

def grants_information_collection(request):
    return render(
        request,
        "rupa/research_support/grants_information_collection.html"
    )


from django.shortcuts import render
from .models import LibraryStaff


def consultants(request):
    return render(
        request,
        "rupa/research_support/consultants.html",
    )

def electronic_lab_notebooks(request):
    return render(request, "rupa/eln/home.html")

def publishing_sharing_research(request):
    return render(
        request,
        "rupa/research_support/publishing_sharing_research.html",
    )

def copyright_resources(request):
    return render(
        request,
        "rupa/research_support/copyright_resources.html",
    )

def how_to_use_others_materials(request):
    return render(
        request,
        "rupa/research_support/copyright/use_other_materials.html"
    )

def managing_your_copyright(request):
    return render(
        request,
        "rupa/research_support/copyright/managing_your_copyright.html"
    )

def navigating_copyright_online(request):
    return render(
        request,
        "rupa/research_support/copyright/navigating_copyright_online.html"
    )

def copyright_basics(request):
    return render(
        request,
        "rupa/research_support/copyright/copyright_basics.html"
    )

def measuring_impact(request):
    return render(request, "rupa/research_support/measuring_impact.html")

def curating_research_outputs(request):
    return render(
        request,
        "rupa/research_support/curating_research_outputs.html"
    )

def submitting_digital_collections_proposal(request):
    return render(
        request,
        "rupa/research_support/digital_collections_proposal.html"
    )

def literature_review(request):
    return render(
        request,
        "rupa/research_support/literature_review.html"
    )

def consultations(request):
    return render(
        request,
        "rupa/research_support/consultations.html"
    )

def public_access(request):
    return render(
        request,
        "rupa/research_support/public_access.html"
    )

def library_support_open_access(request):
    return render(
        request,
        "rupa/research_support/open_access_agreement.html"
    )

def open_access(request):
    return render(
        request,
        "rupa/research_support/open_access.html"
    )

def ensuring_scientific_rigor(request):
    return render(
        request,
        "rupa/research_support/featured_resources/ensuring_scientific_rigor.html"
    )

def funder_public_access_requirements(request):
    return render(
        request,
        "rupa/research_support/funder_public_access_requirements.html"
    )


def core_resource_acknowledgements(request):
    return render(
        request,
        "rupa/research_support/core_resource_acknowledgements.html"
    )



# UWDCC: Submit a Project Proposal from
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import ProposalSubmissionForm
from .notification_helpers import create_library_form_notification


def proposal_submission_form(request):

    if request.method == "POST":

        form = ProposalSubmissionForm(
            request.POST
        )

        if form.is_valid():

            submission = form.save()

            create_library_form_notification(

                title="New Digital Collections Proposal",

                message=(
                    f"{submission.name} submitted "
                    f"a new digital collections project proposal."
                ),

                link=(
                    f"{reverse('library_form_submissions')}"
                    f"?open=proposal:{submission.id}"
                ),
            )

            messages.success(
                request,
                "Your proposal has been submitted successfully."
            )

            return redirect(
                "proposal_submission_form"
            )

    else:

        form = ProposalSubmissionForm()

    return render(
        request,
        "rupa/research_support/proposal_submission_form.html",
        {
            "form": form
        },
    )

#  contact the UWDCC. form

from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import DigitalCollectionsContactForm
from .notification_helpers import create_library_form_notification


def contact_digital_collections(request):

    if request.method == "POST":

        form = DigitalCollectionsContactForm(
            request.POST
        )

        if form.is_valid():

            submission = form.save()

            create_library_form_notification(

                title="New Digital Collections Contact",

                message=(
                    f"{submission.name} contacted "
                    f"the Digital Collections Center."
                ),

                link=(
                    f"{reverse('library_form_submissions')}"
                    f"?open=digital:{submission.id}"
                ),
            )

            messages.success(
                request,
                "Thank you! Your message has been submitted successfully. "
                "We will contact you soon."
            )

            return redirect(
                "contact_digital_collections"
            )

    else:

        form = DigitalCollectionsContactForm()

    return render(
        request,
        "rupa/research_support/contact_digital_collections.html",
        {
            "form": form
        },
    )

def library_services_canvas(request):
    return render(
        request,
        "rupa/instruction_support/library_services_canvas.html",
    )

def course_content_support(request):
    return render(
        request,
        "rupa/instruction_support/course_content_support.html",
    )

def research_guides(request):
    return render(
        request,
        "rupa/instruction_support/research_guides.html",
    )

def designing_assignments(request):
    return render(
        request,
        "rupa/instruction_support/designing_assignments.html",
    )


# library instruction room

from django.shortcuts import render


def spaces_to_support_instruction(request):
    return render(
        request,
        "rupa/instruction_support/spaces_support_instruction.html",
    )


def undergraduate_services(request):
    return render(
        request,
        "rupa/instruction_support/undergraduate_services.html"
    )

def resources_to_support_instructors(request):
    return render(
        request,
        "rupa/instruction_support/resources_to_support_instructors.html",
    )

def sift_winnow(request):

    return render(
        request,
        "rupa/instruction_support/sift.html",
    )


def avoiding_plagiarism(request):

    return render(
        request,
        "rupa/instruction_support/avoiding_plagiarism.html",
    )

def remote_delivery(request):
    return render(
        request,
        "rupa/instruction_support/remote_delivery.html",
    )

def diversity_equity_inclusion(request):

    return render(
        request,
        "rupa/about/diversity.html",
    )

def about_page(request):
    return render(request, "rupa/about/about_page.html")

def employment(request):
    return render(
        request,
        "rupa/about/employment.html",
    )

def featured_news_resources(request):
    return render(
        request,
        "rupa/about/featured_news_resources.html",
    )

def jobs_home(request):
    return render(request, "rupa/about/jobs_home.html")

def contact(request):
    return render(
        request,
        "rupa/about/contact.html",
    )

def diversity_strategic_plan(request):
    return render(
        request,
        "rupa/about/diversity_strategic_plan.html",
    )

def diversity_inclusion(request):
    return render(
        request,
        "rupa/about/diversity_inclusion.html",
    )

def employment_card(request):
    return render(
        request,
        "rupa/about/employment_card.html",
    )

def instruction_support_content_resources(request):
    return render(
        request,
        "rupa/instruction_support/instruction_support_content_resources.html",
    )

def library_research_tutorials(request):
    return render(
        request,
        "rupa/instruction_support/library_research_tutorials.html",
    )

def micro_courses(request):
    return render(
        request,
        "rupa/instruction_support/micro_courses.html",
    )
    
    
def data_introduction(request):

    return render(
        request,
        "rupa/research_support/data-management/introduction.html",
        {
            "active_page": "introduction",
        },
    )
    
def dmp_why_create_plan(request):
    return render(
        request,
        "rupa/research_support/data-management/dmp_why_create_plan.html",
        {
            "active_page": "why_create",
        },
    )
    
def dmp_use_dmptool(request):

    return render(
        request,
        "rupa/research_support/data-management/dmp_use_dmptool.html",
        {
            "active_page": "use_dmptool",
        },
    )
    
def dmp_data_type(request):

    return render(
        request,
        "rupa/research_support/data-management/dmp_data_type.html",
        {
            "active_page": "data_type",
        },
    )
    
def dmp_related_tools(request):

    return render(
        request,
        "rupa/research_support/data-management/dmp_related_tools.html",
        {
            "active_page": "related_tools",
        },
    )
    
def dmp_standards(request):

    return render(
        request,
        "rupa/research_support/data-management/dmp_standards.html",
        {
            "active_page": "standards",
        },
    )
    
def dmp_data_preservation(request):

    return render(
        request,
        "rupa/research_support/data-management/dmp_data_preservation.html",
        {
            "active_page": "data_preservation",
        },
    )
    
def dmp_data_sharing(request):

    return render(
        request,
        "rupa/research_support/data-management/dmp_data_sharing.html",
        {
            "active_page": "data_sharing",
        },
    )
    
def dmp_oversight(request):

    return render(
        request,
        "rupa/research_support/data-management/dmp_oversight.html",
        {
            "active_page": "oversight",
        },
    )
def grants_scholarships_static(request):

    return render(
        request,
        "rupa/research_support/grants/grants_scholarships.html",
    )  
    

def building_nonprofit_board(request):

    return render(
        request,
        "rupa/research_support/grants/building_nonprofit_board.html"
    )
    

def finding_federal_funding(request):
    return render(
        request,
        "rupa/research_support/grants/finding_federal_funding.html",
    )
    

def funding_academics_researchers(request):
    return render(
        request,
        "rupa/research_support/grants/funding_academics_researchers.html",
    )
    
def funding_graduate_students(request):
    return render(
        request,
        "rupa/research_support/grants/funding_graduate_students.html",
    )
    
def funding_individuals(request):
    return render(
        request,
        "rupa/research_support/grants/funding_individuals.html",
    )
    
def funding_international_students(request):
    return render(
        request,
        "rupa/research_support/grants/funding_international_students.html",
    )
    
def funding_study_abroad(request):
    return render(
        request,
        "rupa/research_support/grants/funding_study_abroad.html",
    )
    
def funding_undergraduates(request):
    return render(
        request,
        "rupa/research_support/grants/funding_undergraduates.html",
    )
    

def funding_students(request):
    return render(
        request,
        "rupa/research_support/grants/funding_students.html",
    )
    

def grant_funding_individuals(request):
    return render(
        request,
        "rupa/research_support/grants/grant_funding_individuals.html"
    )
    
def grant_funding_nonprofit(request):
    return render(
        request,
        "rupa/research_support/grants/grant_funding_nonprofit.html"
    )
    
def proposal_writing(request):
    return render(
        request,
        "rupa/research_support/grants/proposal_writing.html"
    )
    
def nonprofit_startup(request):
    return render(
        request,
        "rupa/research_support/grants/nonprofit_startup.html"
    )
    
def prospect(request):
    return render(
        request,
        "rupa/research_support/grants/prospect.html"
    )
    
def corporate_giving(request):
    return render(
        request,
        "rupa/research_support/grants/corporate_giving.html"
    )
    
def grants_for_nonprofits(request):
    return render(
        request,
        "rupa/research_support/grants/grants_for_nonprofits.html",
    )
    
def wisconsin(request):
    return render(
        request,
        "rupa/research_support/grants/wisconsin.html",
    )
    
def minds(request):
    return render(request, "rupa/research_support/featured_resources/minds.html")
# rupa code*****************
