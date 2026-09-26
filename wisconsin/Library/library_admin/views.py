# =====================================================
# IMPORTS
# =====================================================
from Admin.audit import AuditLogger
import re

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q, F
from django.http import JsonResponse
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)
from django.utils.text import slugify

from Admin.bela_admin.models import Building, Floor, Room

from Admin.audit import AuditLogger

from Library.models import (
    ResourceCategory,
    LibraryResource,
    Library,
)


# =====================================================
# DASHBOARD VIEWS
# =====================================================

def dashboard_base(request):
    return render(
        request,
        "library_admin/library_dashboard_base.html"
    )


# =====================================================
# IMPORTS
# =====================================================
import re
import json

from datetime import timedelta
from django.db.models import Count, Q, F, Sum, Max
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

from Library.models import (
    ResourceCategory,
    LibraryResource,
    Library,
    LibraryUser,
    ResourceCopy,
    BorrowRequest,
    BorrowTransaction,
    Fine,
    DigitalResource,
    # StudyRoom,
    # StudyRoomBooking,
    LibraryEvent,
)

@login_required
def dashboard(request, uuid):

    # =================================================
    # CHECK LOGGED-IN USER
    # =================================================

    if str(request.user.uuid) != str(uuid):
        return redirect("login")


    issue_pin = request.session.get("library_issue_pin")

    today = timezone.localdate()
    # =====================================================
    # TODAY'S NEW MEMBERS
    # =====================================================

    new_members_today = LibraryUser.objects.filter(
        membership_date=today
    ).count()

    current_month = today.month
    current_year = today.year

    # Last 7 days including today
    chart_start_date = today - timedelta(days=6)


    # =====================================================
    # DASHBOARD STATISTICS
    # =====================================================

    total_books = (
        LibraryResource.objects
        .filter(
            resource_type="BOOK",
            status="ACTIVE",
        )
        .aggregate(
            total=Sum("total_copies")
        )["total"] or 0
    )


    active_members = (
        LibraryUser.objects
        .filter(
            active=True
        )
        .count()
    )


    books_issued_today = (
        BorrowTransaction.objects
        .filter(
            issue_date=today
        )
        .count()
    )

    overdue_books = Fine.objects.filter(
        payment_status="UNPAID"
    ).count()

    pending_renewals = BorrowTransaction.objects.filter(
        renewal_requested=True,
        status="ISSUED",
    ).count()



    total_fines = Fine.objects.filter(
        payment_status="PAID"
    ).aggregate(
        total=Sum("amount_received")
    )["total"] or 0


    # -------------------------------------------------
    # SMALL STATISTICS
    # -------------------------------------------------

    members_this_month = LibraryUser.objects.filter(
        membership_date__month=current_month,
        membership_date__year=current_year,
    ).count()


    overdue_today = BorrowTransaction.objects.filter(
        due_date=today,
        return_date__isnull=True,
    ).count()


    # -------------------------------------------------
    # RENEWAL REQUESTS TODAY
    # -------------------------------------------------

    renewals_today = BorrowTransaction.objects.filter(
        renewal_requested=True,
        status="ISSUED",
        renewal_requested_at__date=today,
    ).count()


    chart_labels = []
    chart_issued = []
    chart_returned = []


    for day_number in range(7):

        current_date = chart_start_date + timedelta(
            days=day_number
        )

        # Label displayed on chart
        chart_labels.append(
            current_date.strftime("%d %b")
        )


        # Books issued on this date
        issued_count = BorrowTransaction.objects.filter(
            issue_date=current_date
        ).count()


        # Books returned on this date
        returned_count = BorrowTransaction.objects.filter(
            return_date=current_date
        ).count()


        chart_issued.append(issued_count)
        chart_returned.append(returned_count)


    activities = []


    recent_members = (
        LibraryUser.objects
        .select_related("user")
        .order_by("-membership_date")[:5]
    )


    for member in recent_members:

        member_name = (
            member.user.get_full_name()
            or member.user.username
        )

        activities.append({
            "type": "member",
            "title": "New member registered",
            "description": member_name,
            "date": member.membership_date,
        })


    recent_issued = (
        BorrowTransaction.objects
        .select_related(
            "library_user__user",
            "copy__resource",
        )
        .order_by("-issue_date")[:5]
    )


    for transaction in recent_issued:

        activities.append({
            "type": "issued",
            "title": "Book issued",
            "description": transaction.copy.resource.title,
            "date": transaction.issue_date,
        })


    recent_returned = (
        BorrowTransaction.objects
        .filter(
            return_date__isnull=False
        )
        .select_related(
            "library_user__user",
            "copy__resource",
        )
        .order_by("-return_date")[:5]
    )


    for transaction in recent_returned:

        activities.append({
            "type": "returned",
            "title": "Book returned",
            "description": transaction.copy.resource.title,
            "date": transaction.return_date,
        })

    recent_fines = (
        Fine.objects
        .filter(
            payment_status="PAID",
            paid_date__isnull=False,
        )
        .select_related(
            "transaction__library_user__user"
        )
        .order_by("-paid_date")[:5]
    )


    for fine in recent_fines:

        member_name = (
            fine.transaction.library_user.user.get_full_name()
            or fine.transaction.library_user.user.username
        )

        amount = fine.amount_received or fine.fine_amount

        activities.append({
            "type": "fine",
            "title": "Fine collected",
            "description": f"₹{amount} from {member_name}",
            "date": fine.paid_date.date(),
        })


    recent_book_copies = (
        ResourceCopy.objects
        .select_related("resource")
        .order_by("-acquisition_date")
    )


    seen_resources = set()

    recent_unique_books = []


    for copy in recent_book_copies:

        resource_id = copy.resource_id


        if resource_id in seen_resources:
            continue

        seen_resources.add(resource_id)

        recent_unique_books.append(copy)

        if len(recent_unique_books) >= 5:
            break


    # =================================================
    # ADD UNIQUE BOOK ACTIVITIES
    # =================================================

    for copy in recent_unique_books:

        activities.append({

            "type": "book",

            "title": "New book added",

            "description": copy.resource.title,

            "date": copy.acquisition_date,

        })


    # =================================================
    # SORT ALL ACTIVITIES
    # =================================================

    activities.sort(
        key=lambda activity: activity["date"],
        reverse=True
    )


    # Show only latest 5 activities
    recent_activities = activities[:5]


    for activity in recent_activities:

        activity["display_date"] = activity["date"].strftime(
            "%d %b %Y"
        )


    recent_borrowings = (
        BorrowTransaction.objects
        .select_related(
            "library_user__user",
            "copy__resource",
        )
        .order_by("-issue_date")[:5]
    )


    overdue_transactions = (
        BorrowTransaction.objects
        .filter(
            due_date__lt=today,
            return_date__isnull=True,
        )
        .select_related(
            "library_user__user",
            "copy__resource",
        )
        .order_by("due_date")[:5]
    )


    # =====================================================
    # CALCULATE DAYS OVERDUE
    # =====================================================

    for transaction in overdue_transactions:

        transaction.days_overdue = (
            today - transaction.due_date
        ).days

    top_borrowed_books = (
        BorrowTransaction.objects
        .values(
            "copy__resource__id",
            "copy__resource__title",
            "copy__resource__author",
            "copy__resource__cover_image",
        )
        .annotate(
            borrow_count=Count("id")
        )
        .order_by("-borrow_count")[:5]
    )


    # =====================================================
    # ADD RANK TO TOP BORROWED BOOKS
    # =====================================================

    for rank, book in enumerate(top_borrowed_books, start=1):

        book["rank"] = rank


    # =====================================================
    # PENDING RENEWAL REQUESTS LIST
    # =====================================================

    pending_renewal_list = (
        BorrowTransaction.objects
        .filter(
            renewal_requested=True,
            status="ISSUED",
        )
        .select_related(
            "library_user__user",
            "copy__resource",
        )
        .order_by("renewal_requested_at")[:5]
    )


    dashboard_notifications = []


    # =====================================================
    # GET PENDING BORROW REQUESTS
    # =====================================================

    recent_borrow_requests = (
        BorrowRequest.objects
        .select_related(
            "resource",
            "library_user__user",
        )
        .order_by(
            "-request_date",
            "-created_at",
        )[:5]
    )


    # =====================================================
    # CREATE DASHBOARD NOTIFICATIONS
    # =====================================================

    for borrow_request in recent_borrow_requests:

        user = borrow_request.library_user.user

        member_name = (
            user.get_full_name()
            or user.username
        )

        dashboard_notifications.append({

            "type": "borrow_request",

            "title": "New Borrow Request",

            "description": (
                f'{member_name} requested '
                f'"{borrow_request.resource.title}".'
            ),

            "date": borrow_request.request_date,

            # UUID for opening the request
            "request_uuid": str(
                borrow_request.uuid
            ),
        })


    # =====================================================
    # FORMAT DATE
    # =====================================================

    for notification in dashboard_notifications:

        notification["display_date"] = (
            notification["date"].strftime(
                "%b %d, %Y • %I:%M %p"
            )
        )

    dashboard_notifications = dashboard_notifications[:5]


    analytics_active_members = LibraryUser.objects.filter(
        active=True
    ).count()


    digital_resources_count = DigitalResource.objects.count()


    # total_study_rooms = StudyRoom.objects.filter(
    #     status="AVAILABLE"
    # ).count()


    # study_rooms_used_today = (
    #     StudyRoomBooking.objects
    #     .filter(
    #         booking_date=today,
    #         status__in=["BOOKED", "COMPLETED"],
    #     )
    #     .values("room_id")
    #     .distinct()
    #     .count()
    # )


    # if total_study_rooms > 0:

    #     study_room_usage = round(
    #         (
    #             study_rooms_used_today
    #             / total_study_rooms
    #         ) * 100
    #     )

    # else:

    #     study_room_usage = 0


    # # Keep percentage between 0 and 100
    # study_room_usage = min(
    #     max(study_room_usage, 0),
    #     100
    # )

    ebook_downloads = None

    current_year = today.year


    # Total physical copies
    total_collection_copies = ResourceCopy.objects.count()


    # Copies acquired this year
    copies_acquired_this_year = ResourceCopy.objects.filter(
        acquisition_date__year=current_year
    ).count()


    if total_collection_copies > 0:

        collection_growth_percentage = round(
            (
                copies_acquired_this_year
                / total_collection_copies
            ) * 100
        )

    else:

        collection_growth_percentage = 0


    collection_growth_percentage = min(
        max(collection_growth_percentage, 0),
        100
    )


    book_copies = ResourceCopy.objects.filter(
        resource__resource_type="BOOK"
    ).count()


    if total_collection_copies > 0:

        books_collection_percentage = round(
            (
                book_copies
                / total_collection_copies
            ) * 100
        )

    else:

        books_collection_percentage = 0


    ebook_resources = LibraryResource.objects.filter(
        resource_type="EBOOK",
        status="ACTIVE",
    ).count()


    total_active_resources = LibraryResource.objects.filter(
        status="ACTIVE"
    ).count()


    if total_active_resources > 0:

        ebooks_collection_percentage = round(
            (
                ebook_resources
                / total_active_resources
            ) * 100
        )

    else:

        ebooks_collection_percentage = 0


    journal_resources = LibraryResource.objects.filter(
        resource_type="JOURNAL",
        status="ACTIVE",
    ).count()


    if total_active_resources > 0:

        journals_collection_percentage = round(
            (
                journal_resources
                / total_active_resources
            ) * 100
        )

    else:

        journals_collection_percentage = 0


    usage_books_issued = BorrowTransaction.objects.filter(
        issue_date=today
    ).count()


    usage_books_returned = BorrowTransaction.objects.filter(
        return_date=today
    ).count()


    usage_renewals = BorrowTransaction.objects.filter(
        renewal_requested=True,
        status="ISSUED",
        renewal_requested_at__date=today,
    ).count()

    usage_fine_collection = (
        Fine.objects
        .filter(
            payment_status="PAID",
            paid_date__date=today,
        )
        .aggregate(
            total=Sum("amount_received")
        )["total"] or 0
    )

    library_visitors_today = None



    analytics_pending_renewals = (
        BorrowTransaction.objects
        .filter(
            renewal_requested=True,
            status="ISSUED",
        )
        .select_related(
            "library_user__user",
            "copy__resource",
        )
        .order_by("renewal_requested_at")[:5]
    )


    for renewal in analytics_pending_renewals:

        member_name = (
            renewal.library_user.user.get_full_name()
            or renewal.library_user.user.username
        )

        renewal.member_name = member_name

        renewal.member_initial = (
            member_name[0].upper()
            if member_name
            else "?"
        )

    recent_books = (
        LibraryResource.objects
        .filter(
            resource_type="BOOK",
            status="ACTIVE",
        )
        .annotate(
            latest_acquisition_date=Max(
                "copies__acquisition_date"
            )
        )
        .filter(
            latest_acquisition_date__isnull=False
        )
        .order_by(
            "-latest_acquisition_date"
        )[:4]
    )


    for book in recent_books:

        acquisition_date = book.latest_acquisition_date

        days_old = (
            today - acquisition_date
        ).days

        if days_old == 0:

            book.added_label = "Added Today"

        elif days_old == 1:

            book.added_label = "Yesterday"

        elif days_old == 2:

            book.added_label = "2 Days Ago"

        elif days_old <= 7:

            book.added_label = "This Week"

        else:

            book.added_label = acquisition_date.strftime(
                "%d %b %Y"
            )


    upcoming_events = (
        LibraryEvent.objects
        .filter(
            event_date__gte=today
        )
        .select_related(
            "library"
        )
        .order_by(
            "event_date"
        )[:3]
    )


    for event in upcoming_events:

        event.day_number = event.event_date.strftime(
            "%d"
        )

        event.month_name = event.event_date.strftime(
            "%b"
        ).upper()


    recent_fine_payments = (
        Fine.objects
        .filter(
            payment_status="PAID",
            paid_date__isnull=False,
        )
        .select_related(
            "transaction__library_user__user",
            "collected_by",
        )
        .order_by(
            "-paid_date",
            "-updated_at",
        )[:10]
    )


    for fine in recent_fine_payments:
        user = fine.transaction.library_user.user

        fine.member_name = (
            user.get_full_name()
            or user.username
        )


        if fine.amount_received is not None:

            fine.display_amount = fine.amount_received

        else:

            fine.display_amount = fine.fine_amount



        if fine.collected_by:

            fine.collector_name = (
                fine.collected_by.get_full_name()
                or fine.collected_by.username
            )

        else:

            fine.collector_name = "—"

        fine.display_paid_date = fine.paid_date

    context = {

        # ---------------------------------------------
        # USER / SESSION
        # ---------------------------------------------

        "user": request.user,
        "issue_pin": issue_pin,


        # ---------------------------------------------
        # STATISTICS
        # ---------------------------------------------

        "total_books": total_books,
        "active_members": active_members,
        "books_issued_today": books_issued_today,
        "overdue_books": overdue_books,
        "pending_renewals": pending_renewals,
        "total_fines": total_fines,


        # ---------------------------------------------
        # SMALL STATISTICS
        # ---------------------------------------------

        "members_this_month": members_this_month,
        "overdue_today": overdue_today,
        "renewals_today": renewals_today,


        # ---------------------------------------------
        # CIRCULATION CHART
        # ---------------------------------------------

        "circulation_labels": chart_labels,
        "circulation_issued": chart_issued,
        "circulation_returned": chart_returned,


        # ---------------------------------------------
        # QUICK ACTIVITY
        # ---------------------------------------------

        "recent_activities": recent_activities,
        "recent_borrowings": recent_borrowings,
        "overdue_transactions": overdue_transactions,

        "top_borrowed_books": top_borrowed_books,
        "dashboard_notifications": dashboard_notifications,
        "pending_renewal_list": pending_renewal_list,

        # =================================================
        # LIBRARY ANALYTICS
        # =================================================

        "analytics_active_members": analytics_active_members,

        "digital_resources_count": digital_resources_count,

        # "study_room_usage": study_room_usage,

        "ebook_downloads": ebook_downloads,

        "collection_growth_percentage": (
            collection_growth_percentage
        ),

        "books_collection_percentage": (
            books_collection_percentage
        ),

        "ebooks_collection_percentage": (
            ebooks_collection_percentage
        ),

        "journals_collection_percentage": (
            journals_collection_percentage
        ),

        # Library Usage
        "library_visitors_today": library_visitors_today,

        "usage_books_issued": usage_books_issued,

        "usage_books_returned": usage_books_returned,

        "usage_renewals": usage_renewals,

        "usage_fine_collection": usage_fine_collection,

        "analytics_pending_renewals": (
            analytics_pending_renewals
        ),
        "recent_books": recent_books,

        # =====================================================
        # TODAY'S SUMMARY
        # =====================================================

        "new_members_today": new_members_today,

        "usage_books_issued": usage_books_issued,

        "usage_books_returned": usage_books_returned,

        "usage_fine_collection": usage_fine_collection,


        # =====================================================
        # UPCOMING EVENTS
        # =====================================================

        "upcoming_events": upcoming_events,

        "recent_fine_payments": recent_fine_payments,
    }


    # =================================================
    # RENDER
    # =================================================

    return render(
        request,
        "library_admin/dashboard_lib.html",
        context,
    )

# =====================================================
# CATEGORY LIST VIEW
# =====================================================

@staff_member_required
def category_list(request):
    """
    Display all categories with statistics and search.
    """

    categories = (
        ResourceCategory.objects
        .annotate(
            total_books=Count("resources")
        )
        .order_by(
            "title"
        )
    )


    # -------------------------------
    # SEARCH
    # -------------------------------

    search_query = request.GET.get(
        "search",
        ""
    )

    if search_query:

        categories = categories.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )


    # -------------------------------
    # PAGINATION
    # -------------------------------

    paginator = Paginator(
        categories,
        5
    )

    page_number = request.GET.get(
        "page",
        1
    )

    page_obj = paginator.get_page(
        page_number
    )

    page_numbers = get_page_numbers(
        page_obj
    )
        # -------------------------------
    # STATISTICS
    # -------------------------------

    total_categories = (
        ResourceCategory.objects.count()
    )

    active_categories = (
        ResourceCategory.objects
        .filter(
            is_full_crud=True
        )
        .count()
    )

    inactive_categories = (
        total_categories -
        active_categories
    )


    total_books = (
        LibraryResource.objects
        .filter(
            category__isnull=False
        )
        .count()
    )


    categories_with_books = (
        categories
        .filter(
            total_books__gt=0
        )
        .count()
    )


    # -------------------------------
    # TOP CATEGORIES
    # -------------------------------

    top_categories = (
        categories
        .order_by(
            "-total_books"
        )[:5]
    )


    max_books = (
        top_categories[0].total_books
        if top_categories
        else 0
    )


    for category in top_categories:

        if max_books:

            category.percentage = int(
                (
                    category.total_books /
                    max_books
                ) * 100
            )

        else:

            category.percentage = 0



    context = {

        "page_obj": page_obj,

        "page_numbers": page_numbers,

        "search_query": search_query,

        "total_categories": total_categories,

        "active_categories": active_categories,

        "inactive_categories": inactive_categories,

        "total_books": total_books,

        "top_categories": top_categories,

        "categories_with_books": categories_with_books,

    }


    # -------------------------------
    # AJAX LIVE SEARCH
    # -------------------------------

    # if request.headers.get(
    #     "X-Requested-With"
    # ) == "XMLHttpRequest":


    #     data = []


        # -------------------------------
        # AJAX RESPONSE
        # -------------------------------

        # if request.headers.get("X-Requested-With") == "XMLHttpRequest":

        #     return render(
        #         request,
        #         "library_admin/nancy/category_list.html",
        #         context
        #     )

        # return JsonResponse({

        #     "categories": data

        # })


    return render(
        request,
        "library_admin/nancy/category_list.html",
        context
    )


def get_page_numbers(page_obj):

    current_page = page_obj.number

    total_pages = page_obj.paginator.num_pages


    if total_pages <= 5:

        return list(
            range(
                1,
                total_pages + 1
            )
        )


    if current_page <= 2:

        return [
            1,
            2,
            3,
            "...",
            total_pages,
        ]


    if current_page >= total_pages - 1:

        return [
            1,
            "...",
            total_pages - 2,
            total_pages - 1,
            total_pages,
        ]


    return [
        1,
        "...",
        current_page,
        "...",
        total_pages,
    ]
    
# =====================================================
# ADD CATEGORY VIEW
# =====================================================

@staff_member_required
def category_add(request):
    """
    Add a new category.
    """


    if request.method == "POST":


        title = request.POST.get(
            "title",
            ""
        ).strip()


        icon = request.POST.get(
            "icon",
            ""
        ).strip()


        description = request.POST.get(
            "description",
            ""
        ).strip()


        # display_order = request.POST.get(
        #     "display_order",
        #     "0"
        # ).strip()


        is_active = (
            request.POST.get(
                "is_active"
            )
            ==
            "on"
        )


        context = {

            "is_edit": False,

            "title": title,

            "icon": icon,

            "description": description,

            "is_active": is_active,

        }


        # -------------------------------
        # VALIDATION
        # -------------------------------

        if not title:

            messages.error(
                request,
                "Category title is required."
            )

            return render(
                request,
                "library_admin/nancy/category_form.html",
                context
            )


        if len(title) < 3:

            messages.error(
                request,
                "Category title must be at least 3 characters."
            )

            return render(
                request,
                "library_admin/nancy/category_form.html",
                context
            )


        if len(title) > 100:

            messages.error(
                request,
                "Category title cannot exceed 100 characters."
            )

            return render(
                request,
                "library_admin/nancy/category_form.html",
                context
            )


        if not re.fullmatch(r"[A-Za-z][A-Za-z\s&()\-]*", title):

            messages.error(
                request,
                "Category title can contain only letters, numbers, spaces, &, ( ), and -."
            )

            return render(
                request,
                "library_admin/nancy/category_form.html",
                context
            )


        if ResourceCategory.objects.filter(
            title__iexact=title
        ).exists():

            messages.error(
                request,
                f'Category "{title}" already exists.'
            )

            return render(
                request,
                "library_admin/nancy/category_form.html",
                context
            )


        # try:

        #     display_order = int(
        #         display_order
        #     )

        #     if display_order < 0:
        #         raise ValueError


        # except ValueError:

        #     messages.error(
        #         request,
        #         "Display order must be a positive number."
        #     )

            return render(
                request,
                "library_admin/nancy/category_form.html",
                context
            )


        if len(description) > 500:

            messages.error(
                request,
                "Description cannot exceed 500 characters."
            )

            return render(
                request,
                "library_admin/nancy/category_form.html",
                context
            )


        # -------------------------------
        # SLUG GENERATION
        # -------------------------------

        slug = slugify(title)

        original_slug = slug

        counter = 1


        while ResourceCategory.objects.filter(
            slug=slug
        ).exists():

            slug = (
                f"{original_slug}-{counter}"
            )

            counter += 1



        category = ResourceCategory.objects.create(
            title=title,
            slug=slug,
            description=description,
            is_full_crud=is_active,
        )

        AuditLogger.log(
            request=request,
            action="CREATE",
            module="LibraryAdmin",
            object_type="ResourceCategory",
            object_id=category.uuid,
            description=f'Created category "{category.title}".',
            after_data=AuditLogger.model_to_dict(
                category,
                [
                    "title",
                    "slug",
                    "description",
                    "is_full_crud",
                ]
            ),
            status="SUCCESS",
        )

        messages.success(
            request,
            f'Category "{title}" added successfully!'
        )


        return redirect(
            "category_list"
        )


    return render(
        request,
        "library_admin/nancy/category_form.html",
        {
            "is_edit": False,
            "title": "",
            "icon": "",
            "description": "",
            "is_active": True,
        },
    )
    
    
    
# =====================================================
# EDIT CATEGORY VIEW
# =====================================================

@staff_member_required
def category_edit(request, category_uuid):
    """
    Edit an existing category.
    """

    category = get_object_or_404(
        ResourceCategory,
        uuid=category_uuid
    )


    if request.method == "POST":

        title = request.POST.get(
            "title",
            ""
        ).strip()


        description = request.POST.get(
            "description",
            ""
        ).strip()


        # display_order = request.POST.get(
        #     "display_order",
        #     "0"
        # ).strip()


        is_active = (
            request.POST.get("is_active")
            ==
            "on"
        )


        context = {

            "category": category,

            "is_edit": True,

            "title": title,

            "description": description,

            "is_active": is_active,

        }


        # -------------------------------
        # VALIDATION
        # -------------------------------

        if not title:

            messages.error(
                request,
                "Category title is required."
            )

            return render(
                request,
                "library_admin/nancy/category_form.html",
                context
            )


        if len(title) < 3:

            messages.error(
                request,
                "Category title must be at least 3 characters."
            )

            return render(
                request,
                "library_admin/nancy/category_form.html",
                context
            )


        if len(title) > 100:

            messages.error(
                request,
                "Category title cannot exceed 100 characters."
            )

            return render(
                request,
                "library_admin/nancy/category_form.html",
                context
            )


        if not re.match(
            r"^[A-Za-z0-9 &()\-]+$",
            title
        ):

            messages.error(
                request,
                "Invalid category title."
            )

            return render(
                request,
                "library_admin/nancy/category_form.html",
                context
            )


        if (
            ResourceCategory.objects
            .filter(
                title__iexact=title
            )
            .exclude(
                uuid=category.uuid
            )
            .exists()
        ):

            messages.error(
                request,
                f'Category "{title}" already exists.'
            )

            return render(
                request,
                "library_admin/nancy/category_form.html",
                context
            )


        # try:

        #     display_order = int(
        #         display_order
        #     )

        #     if display_order < 0:
        #         raise ValueError


        # except ValueError:

        #     messages.error(
        #         request,
        #         "Display order must be positive."
        #     )

            return render(
                request,
                "library_admin/nancy/category_form.html",
                context
            )



        # -------------------------------
        # UPDATE SLUG
        # -------------------------------

        slug = slugify(title)

        original_slug = slug

        counter = 1


        while (
            ResourceCategory.objects
            .filter(
                slug=slug
            )
            .exclude(
                uuid=category.uuid
            )
            .exists()
        ):

            slug = (
                f"{original_slug}-{counter}"
            )

            counter += 1

        before_data = AuditLogger.model_to_dict(
            category,
            [
                "title",
                "slug",
                "icon",
                "description",
                "is_full_crud",
            ]
        )

        category.title = title

        category.slug = slug

        category.description = description

        category.is_full_crud = is_active


        category.save()
        
        after_data = AuditLogger.model_to_dict(
            category,
            [
                "title",
                "slug",
                "description",
                "is_full_crud",
            ]
        )

        AuditLogger.log(
            request=request,
            action="UPDATE",
            module="LibraryAdmin",
            object_type="ResourceCategory",
            object_id=category.uuid,
            description=f'Updated category "{category.title}".',
            before_data=before_data,
            after_data=after_data,
            status="SUCCESS",
        )



        messages.success(
            request,
            f'Category "{title}" updated successfully!'
        )


        return redirect(
            "category_list"
        )



    return render(

        request,

        "library_admin/nancy/category_form.html",

        {

            "category": category,

            "is_edit": True,

            "title": category.title,

            "description": category.description,

            "is_active": category.is_full_crud,

        }

    )
    
    
# =====================================================
# DELETE CATEGORY VIEW
# =====================================================

@staff_member_required
def category_delete(request, category_uuid):
    """
    Delete a category.
    """

    category = get_object_or_404(
        ResourceCategory,
        uuid=category_uuid
    )


    if request.method != "POST":

        return redirect(
            "category_list"
        )


    # ---------------------------------
    # CHECK BOOKS BEFORE DELETE
    # ---------------------------------

    book_count = (
        category.resources.count()
    )


    if book_count > 0:

        messages.error(
            request,
            f'Cannot delete "{category.title}" because it contains {book_count} book(s).'
        )

        return redirect(
            "category_list"
        )



    before_data = AuditLogger.model_to_dict(
        category,
        [
            "title",
            "slug",
            "icon",
            "description",
            "is_full_crud",
        ]
    )

    category_uuid = category.uuid
    title = category.title

    category.delete()

    AuditLogger.log(
        request=request,
        action="DELETE",
        module="LibraryAdmin",
        object_type="ResourceCategory",
        object_id=category_uuid,
        description=f'Deleted category "{title}".',
        before_data=before_data,
        status="SUCCESS",
    )



    messages.success(
        request,
        f'Category "{title}" deleted successfully.'
    )


    return redirect(
        "category_list"
    )



# =====================================================
# TOGGLE CATEGORY STATUS VIEW
# =====================================================

@staff_member_required
def category_toggle(request, category_uuid):
    """
    Toggle category active/inactive status.
    """

    category = get_object_or_404(
        ResourceCategory,
        uuid=category_uuid
    )


    before_data = {
    "is_full_crud": category.is_full_crud,
}

    category.is_full_crud = (
        not category.is_full_crud
    )

    category.save()

    status = (
        "activated"
        if category.is_full_crud
        else
        "deactivated"
    )

    after_data = {
        "is_full_crud": category.is_full_crud,
    }

    AuditLogger.log(
        request=request,
        action="STATUS_CHANGE",
        module="LibraryAdmin",
        object_type="ResourceCategory",
        object_id=category.uuid,
        description=(
            f'Category "{category.title}" was {status}.'
        ),
        before_data=before_data,
        after_data=after_data,
        status="SUCCESS",
    )


    messages.success(
        request,
        f'Category "{category.title}" {status}!'
    )


    return redirect(
        "category_list"
    )
    
# =====================================================
# BUILDING LIST VIEW
# =====================================================

@staff_member_required
def building_list(request):
    """
    Display all buildings with statistics and search.
    """

    buildings = (
        Building.objects
        .annotate(
            total_libraries=Count(
                "libraries",
                distinct=True
            ),
            total_floors=Count(
                "floors",
                distinct=True
            ),
            total_rooms=Count(
                "floors__rooms",
                distinct=True
            ),
        )
        .order_by(
            "building_name"
        )
    )


    # ---------------------------------
    # SEARCH
    # ---------------------------------

    search_query = request.GET.get(
        "search",
        ""
    ).strip()


    if search_query:

        buildings = buildings.filter(

            Q(building_name__icontains=search_query) |

            Q(building_code__icontains=search_query) |

            Q(address__icontains=search_query)

        )


    # ---------------------------------
    # PAGINATION
    # ---------------------------------

    paginator = Paginator(
        buildings,
        5
    )


    page_number = request.GET.get(
        "page",
        1
    )


    page_obj = paginator.get_page(
        page_number
    )

    page_numbers = get_page_numbers(
        page_obj
    )



    # ---------------------------------
    # STATISTICS
    # ---------------------------------

    total_buildings = (
        Building.objects.count()
    )


    active_buildings = (
        Building.objects
        .filter(
            status="ACTIVE"
        )
        .count()
    )


    inactive_buildings = (
        Building.objects
        .filter(
            status="INACTIVE"
        )
        .count()
    )


    total_libraries = (
        Library.objects.count()
    )


    total_resources = (
        LibraryResource.objects.count()
    )


    buildings_with_libraries = (
        buildings
        .filter(
            total_libraries__gt=0
        )
        .count()
    )



    # ---------------------------------
    # TOP BUILDINGS
    # ---------------------------------

    top_buildings = (

        Building.objects

        .annotate(

            total_libraries=Count(
                "libraries",
                distinct=True
            )

        )

        .order_by(
            "-total_libraries"
        )[:5]

    )


    max_libraries = (

        top_buildings[0].total_libraries

        if top_buildings

        else 0

    )


    for building in top_buildings:


        if max_libraries:

            building.percentage = int(

                (
                    building.total_libraries /
                    max_libraries
                ) * 100

            )

        else:

            building.percentage = 0



    context = {


        "page_obj": page_obj,

        "page_numbers": page_numbers,

        "search_query": search_query,

        "total_buildings": total_buildings,

        "active_buildings": active_buildings,

        "inactive_buildings": inactive_buildings,

        "total_libraries": total_libraries,

        "total_resources": total_resources,

        "buildings_with_libraries": buildings_with_libraries,

        "top_buildings": top_buildings,

    }



    # ---------------------------------
    # AJAX RESPONSE
    # ---------------------------------

    if request.headers.get(
        "X-Requested-With"
    ) == "XMLHttpRequest":


        return render(

            request,

            "library_admin/nancy/building_list.html",

            context

        )


    return render(

        request,

        "library_admin/nancy/building_list.html",

        context

    )

def get_page_numbers(page_obj):

    current_page = page_obj.number

    total_pages = page_obj.paginator.num_pages


    if total_pages <= 5:

        return list(
            range(
                1,
                total_pages + 1
            )
        )


    if current_page <= 2:

        return [
            1,
            2,
            3,
            "...",
            total_pages,
        ]


    if current_page >= total_pages - 1:

        return [
            1,
            "...",
            total_pages - 2,
            total_pages - 1,
            total_pages,
        ]


    return [
        1,
        "...",
        current_page,
        "...",
        total_pages,
    ]
# =====================================================
# BUILDING LIBRARIES AJAX VIEW
# =====================================================

@staff_member_required
def building_libraries(request, building_id):

    # ---------------------------------
    # GET BUILDING
    # ---------------------------------

    building = get_object_or_404(
        Building,
        id=building_id
    )


    # ---------------------------------
    # GET LIBRARIES
    # ---------------------------------

    libraries = (
        Library.objects
        .filter(
            building=building
        )
        .order_by(
            "library_name"
        )
    )


    # ---------------------------------
    # PREPARE LIBRARY DATA
    # ---------------------------------

    library_data = []


    for library in libraries:

        library_data.append({

            "id": library.id,

            "library_name": (
                library.library_name
                or ""
            ),

            "library_code": (
                library.library_code
                or ""
            ),

            "address": (
                library.address
                or "No Address"
            ),

            "email": (
                library.email
                or "—"
            ),

            "phone": (
                library.phone
                or "—"
            ),

            "status": (
                library.status
                or "INACTIVE"
            ),

            "image": (

                library.image.url

                if library.image

                else ""

            ),

            "view_url": reverse(

                "view_library",

                args=[
                    library.id
                ]

            ),

        })


    # ---------------------------------
    # JSON RESPONSE
    # ---------------------------------

    return JsonResponse({

        "building": {

            "id": building.id,

            "building_name": (
                building.building_name
            ),

            "building_code": (
                building.building_code
            ),

        },


        "libraries": library_data,


        "total_libraries": (
            libraries.count()
        ),

    })


# =====================================================
# ADD BUILDING VIEW
# =====================================================

@staff_member_required
def building_add(request):
    """
    Add a new building.
    """


    if request.method == "POST":


        building_code = request.POST.get(
            "building_code",
            ""
        ).strip().upper()


        building_name = request.POST.get(
            "building_name",
            ""
        ).strip()


        address = request.POST.get(
            "address",
            ""
        ).strip()


        status = request.POST.get(
            "status",
            "ACTIVE"
        )


        building_image = request.FILES.get(
            "building_image"
        )


        context = {


            "is_edit": False,

            "building_code": building_code,

            "building_name": building_name,

            "address": address,

            "status": status,

        }



        # ---------------------------------
        # BUILDING CODE VALIDATION
        # ---------------------------------

        if not building_code:


            messages.error(
                request,
                "Building code is required."
            )


            return render(

                request,

                "library_admin/nancy/building_form.html",

                context

            )



        if len(building_code) < 2:


            messages.error(

                request,

                "Building code must contain at least 2 characters."

            )


            return render(

                request,

                "library_admin/nancy/building_form.html",

                context

            )



        if len(building_code) > 20:


            messages.error(

                request,

                "Building code cannot exceed 20 characters."

            )


            return render(

                request,

                "library_admin/nancy/building_form.html",

                context

            )



        if not re.match(

            r"^[A-Z0-9\-]+$",

            building_code

        ):


            messages.error(

                request,

                "Building code may contain only uppercase letters, numbers and hyphen (-)."

            )


            return render(

                request,

                "library_admin/nancy/building_form.html",

                context

            )



        if Building.objects.filter(

            building_code__iexact=building_code

        ).exists():


            messages.error(

                request,

                f'Building code "{building_code}" already exists.'

            )


            return render(

                request,

                "library_admin/nancy/building_form.html",

                context

            )



        # ---------------------------------
        # BUILDING NAME VALIDATION
        # ---------------------------------

        if not building_name:


            messages.error(

                request,

                "Building name is required."

            )


            return render(

                request,

                "library_admin/nancy/building_form.html",

                context

            )
            
        if not re.fullmatch(r"[A-Za-z][A-Za-z\s&()\-]*", building_name):

            messages.error(
                request,
                "Building name must start with a letter and can contain only letters, spaces, &, ( ), and -."
            )

            return render(
                request,
                "library_admin/building/building_form.html",
                context
            )



        if len(building_name) < 3:


            messages.error(

                request,

                "Building name must contain at least 3 characters."

            )


            return render(

                request,

                "library_admin/nancy/building_form.html",

                context

            )



        if len(building_name) > 150:


            messages.error(

                request,

                "Building name cannot exceed 150 characters."

            )


            return render(

                request,

                "library_admin/nancy/building_form.html",

                context

            )



        if Building.objects.filter(

            building_name__iexact=building_name

        ).exists():


            messages.error(

                request,

                f'Building "{building_name}" already exists.'

            )


            return render(

                request,

                "library_admin/nancy/building_form.html",

                context

            )



        # ---------------------------------
        # STATUS VALIDATION
        # ---------------------------------

        if status not in [

            "ACTIVE",

            "INACTIVE",

        ]:


            messages.error(

                request,

                "Invalid building status."

            )


            return render(

                request,

                "library_admin/nancy/building_form.html",

                context

            )



        # ---------------------------------
        # IMAGE VALIDATION
        # ---------------------------------

        if building_image:


            if building_image.size > 2 * 1024 * 1024:


                messages.error(

                    request,

                    "Image size must not exceed 2 MB."

                )


                return render(

                    request,

                    "library_admin/nancy/building_form.html",

                    context

                )



        # ---------------------------------
        # SAVE BUILDING
        # ---------------------------------

        building = Building.objects.create(

            building_code=building_code,

            building_name=building_name,

            address=address,

            status=status,

            building_image=building_image,

            is_full_crud=True,

        )


        AuditLogger.log(
            request=request,
            action="CREATE",
            module="LibraryAdmin",
            object_type="Building",
            object_id=building.id,
            description=f'Created building "{building.building_name}".',
            after_data={
                **AuditLogger.model_to_dict(
                    building,
                    [
                        "building_code",
                        "building_name",
                        "address",
                        "status",
                        "is_full_crud",
                    ]
                ),
                "has_building_image": bool(building.building_image),
            },
            status="SUCCESS",
        )


        messages.success(

            request,

            f'Building "{building_name}" created successfully.'

        )


        return redirect(
            "building_list"
        )



    return render(

        request,

        "library_admin/nancy/building_form.html",

        {

            "is_edit": False,

            "building_code": "",

            "building_name": "",

            "address": "",

            "status": "ACTIVE",

        },

    )
    
    
# =====================================================
# EDIT BUILDING VIEW
# =====================================================

@staff_member_required
def building_edit(request, building_id):
    """
    Edit an existing building.
    """

    building = get_object_or_404(
        Building,
        pk=building_id
    )


    if request.method == "POST":


        building_code = request.POST.get(
            "building_code",
            ""
        ).strip().upper()


        building_name = request.POST.get(
            "building_name",
            ""
        ).strip()


        address = request.POST.get(
            "address",
            ""
        ).strip()


        status = request.POST.get(
            "status",
            "ACTIVE"
        )


        building_image = request.FILES.get(
            "building_image"
        )


        context = {

            "building": building,

            "is_edit": True,

            "building_code": building_code,

            "building_name": building_name,

            "address": address,

            "status": status,

        }



        # ---------------------------------
        # BUILDING CODE VALIDATION
        # ---------------------------------

        if not building_code:

            messages.error(
                request,
                "Building code is required."
            )

            return render(
                request,
                "library_admin/nancy/building_form.html",
                context
            )


        if len(building_code) < 2:

            messages.error(
                request,
                "Building code must contain at least 2 characters."
            )

            return render(
                request,
                "library_admin/nancy/building_form.html",
                context
            )


        if len(building_code) > 20:

            messages.error(
                request,
                "Building code cannot exceed 20 characters."
            )

            return render(
                request,
                "library_admin/nancy/building_form.html",
                context
            )


        if not re.match(
            r"^[A-Z0-9\-]+$",
            building_code
        ):

            messages.error(
                request,
                "Building code may contain only uppercase letters, numbers and hyphen (-)."
            )

            return render(
                request,
                "library_admin/nancy/building_form.html",
                context
            )


        if (
            Building.objects
            .filter(
                building_code__iexact=building_code
            )
            .exclude(
                pk=building.id
            )
            .exists()
        ):

            messages.error(
                request,
                f'Building code "{building_code}" already exists.'
            )

            return render(
                request,
                "library_admin/nancy/building_form.html",
                context
            )



        # ---------------------------------
        # BUILDING NAME VALIDATION
        # ---------------------------------

        if not building_name:

            messages.error(
                request,
                "Building name is required."
            )

            return render(
                request,
                "library_admin/nancy/building_form.html",
                context
            )


        if len(building_name) < 3:

            messages.error(
                request,
                "Building name must contain at least 3 characters."
            )

            return render(
                request,
                "library_admin/nancy/building_form.html",
                context
            )


        if len(building_name) > 150:

            messages.error(
                request,
                "Building name cannot exceed 150 characters."
            )

            return render(
                request,
                "library_admin/nancy/building_form.html",
                context
            )


        if (
            Building.objects
            .filter(
                building_name__iexact=building_name
            )
            .exclude(
                pk=building.id
            )
            .exists()
        ):

            messages.error(
                request,
                f'Building "{building_name}" already exists.'
            )

            return render(
                request,
                "library_admin/nancy/building_form.html",
                context
            )



        # ---------------------------------
        # STATUS VALIDATION
        # ---------------------------------

        if status not in [
            "ACTIVE",
            "INACTIVE",
        ]:

            messages.error(
                request,
                "Invalid building status."
            )

            return render(
                request,
                "library_admin/nancy/building_form.html",
                context
            )



        # ---------------------------------
        # IMAGE VALIDATION
        # ---------------------------------

        if building_image:


            if building_image.size > 2 * 1024 * 1024:

                messages.error(
                    request,
                    "Image size must not exceed 2 MB."
                )

                return render(
                    request,
                    "library_admin/nancy/building_form.html",
                    context
                )


            building.building_image = building_image


        before_data = AuditLogger.model_to_dict(
            building,
            [
                "building_code",
                "building_name",
                "address",
                "status",
                "is_full_crud",
            ]
        )

        before_data["has_building_image"] = bool(
            building.building_image
        )
        
        # ---------------------------------
        # UPDATE BUILDING
        # ---------------------------------

        building.building_code = building_code

        building.building_name = building_name

        building.address = address

        building.status = status


        building.save()
        
        
        after_data = AuditLogger.model_to_dict(
            building,
            [
                "building_code",
                "building_name",
                "address",
                "status",
                "is_full_crud",
            ]
        )

        after_data["has_building_image"] = bool(
            building.building_image
        )


        AuditLogger.log(
            request=request,
            action="UPDATE",
            module="LibraryAdmin",
            object_type="Building",
            object_id=building.id,
            description=f'Updated building "{building.building_name}".',
            before_data=before_data,
            after_data=after_data,
            status="SUCCESS",
        )



        messages.success(
            request,
            f'Building "{building_name}" updated successfully.'
        )


        return redirect(
            "building_list"
        )



    return render(

        request,

        "library_admin/nancy/building_form.html",

        {

            "building": building,

            "is_edit": True,

            "building_code": building.building_code,

            "building_name": building.building_name,

            "address": building.address,

            "status": building.status,

        },

    )



# =====================================================
# DELETE BUILDING VIEW
# =====================================================

@staff_member_required
def building_delete(request, building_id):
    """
    Delete a building.
    """

    building = get_object_or_404(
        Building,
        pk=building_id
    )


    if request.method != "POST":

        return redirect(
            "building_list"
        )


    # ---------------------------------
    # CHECK LIBRARIES
    # ---------------------------------

    library_count = (
        building.libraries.count()
    )


    if library_count > 0:

        messages.error(
            request,
            f'Cannot delete "{building.building_name}" because it contains {library_count} library(s).'
        )

        return redirect(
            "building_list"
        )



    # ---------------------------------
    # CHECK FLOORS
    # ---------------------------------

    floor_count = (
        building.floors.count()
    )


    if floor_count > 0:

        messages.error(
            request,
            f'Cannot delete "{building.building_name}" because it contains {floor_count} floor(s).'
        )

        return redirect(
            "building_list"
        )

    before_data = AuditLogger.model_to_dict(
        building,
        [
            "building_code",
            "building_name",
            "address",
            "status",
            "is_full_crud",
        ]
    )

    before_data["has_building_image"] = bool(
        building.building_image
    )

    building_id_for_audit = building.id
    building_name = building.building_name

    # ---------------------------------
    # DELETE IMAGE
    # ---------------------------------

    if building.building_image:

        building.building_image.delete(
            save=False
        )



    building_name = (
        building.building_name
    )


    building.delete()
    
    AuditLogger.log(
        request=request,
        action="DELETE",
        module="LibraryAdmin",
        object_type="Building",
        object_id=building_id_for_audit,
        description=f'Deleted building "{building_name}".',
        before_data=before_data,
        status="SUCCESS",
    )



    messages.success(
        request,
        f'Building "{building_name}" deleted successfully.'
    )


    return redirect(
        "building_list"
    )



# =====================================================
# TOGGLE BUILDING STATUS VIEW
# =====================================================

@staff_member_required
def building_toggle(request, building_id):
    """
    Toggle building active/inactive status.
    """

    building = get_object_or_404(
        Building,
        pk=building_id
    )
    
    before_data = {
        "status": building.status,
    }


    if building.status == "ACTIVE":

        building.status = "INACTIVE"

    else:

        building.status = "ACTIVE"



    building.save()



    status = (
        "activated"
        if building.status == "ACTIVE"
        else "deactivated"
    )
    
    after_data = {
        "status": building.status,
    }


    AuditLogger.log(
        request=request,
        action="STATUS_CHANGE",
        module="LibraryAdmin",
        object_type="Building",
        object_id=building.id,
        description=(
            f'Building "{building.building_name}" was {status}.'
        ),
        before_data=before_data,
        after_data=after_data,
        status="SUCCESS",
    )


    messages.success(
        request,
        f'Building "{building.building_name}" {status}!'
    )


    return redirect(
        "building_list"
    )
    
    

# ***********************************navina code starts ******************************************
# ============================================
# LIBRARY BOOKS VIEW
# ============================================
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.db import models
from django.urls import reverse

from Library.models import LibraryResource, ResourceCategory


def library_books(request):

    # ==========================
    # BOOKS QUERY
    # ==========================

    books = (
        LibraryResource.objects
        .select_related("library", "category")
        .all()
        .order_by("-id")
    )

    # ==========================
    # SEARCH
    # ==========================

    search_query = (
    request.GET.get("q")
    or request.GET.get("search")
    or ""
    ).strip()

    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn_issn__icontains=search_query) |
            Q(subject__icontains=search_query)
        )

    # ==========================
    # FILTERS
    # ==========================

    category = request.GET.get("category")
    resource_type = request.GET.get("resource_type")
    status = request.GET.get("status")
    language = request.GET.get("language")
    availability = request.GET.get("availability")

    if category:
        books = books.filter(category_id=category)

    if resource_type:
        books = books.filter(resource_type=resource_type)

    if status:
        books = books.filter(status=status)

    if language:
        books = books.filter(language=language)

    if availability == "available":
        books = books.filter(available_copies__gt=0)

    elif availability == "unavailable":
        books = books.filter(available_copies=0)

    # ==========================
    # DASHBOARD COUNTS
    # ==========================

    total_books = LibraryResource.objects.count()

    available_books = LibraryResource.objects.filter(
        available_copies__gt=0
    ).count()

    borrowed_books = LibraryResource.objects.filter(
        available_copies__lt=models.F("total_copies")
    ).count()

    total_categories = ResourceCategory.objects.count()

    # ==========================
    # FILTER DATA
    # ==========================

    categories = ResourceCategory.objects.filter(
    is_full_crud=True
    ).order_by("title")

    languages = (
        LibraryResource.objects
        .exclude(language__isnull=True)
        .exclude(language="")
        .values_list("language", flat=True)
        .distinct()
        .order_by("language")
    )

    resource_types = LibraryResource.RESOURCE_TYPES
    status_choices = LibraryResource.STATUS_CHOICES

    # ==========================
    # PAGINATION
    # ==========================

    paginator = Paginator(books, 5)
    page_obj = paginator.get_page(request.GET.get("page"))

    # ==========================
    # AJAX RESPONSE
    # ==========================

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":

        book_list = []

        for book in page_obj:

           book_list.append({

            "uuid": str(book.uuid),

            "view_url": reverse("view_book", args=[book.uuid]),

            "title": book.title,

            "library": (
                book.library.library_name
                if book.library
                else ""
            ),

            "isbn": book.isbn_issn or "—",

            "author": book.author,

            "category": (
                book.category.title
                if book.category
                else "—"
            ),

            "edit_url": reverse(
               "edit_book",
               args=[book.uuid]
            ),

            "delete_url": reverse(
               "delete_book",
                args=[book.uuid]
            ),

            "resource_type": book.get_resource_type_display(),

            "available": book.available_copies,

            "total": book.total_copies,

            "status": book.status,

        })

        return JsonResponse({

           "books": book_list,

           "pagination": {

              "current_page": page_obj.number,

              "num_pages": paginator.num_pages,

              "has_previous": page_obj.has_previous(),

              "has_next": page_obj.has_next(),

              "previous_page": (
                page_obj.previous_page_number()
                if page_obj.has_previous()
                else None
               ),

               "next_page": (
                page_obj.next_page_number()
                if page_obj.has_next()
                else None
               ),

               "start_index": page_obj.start_index(),

               "end_index": page_obj.end_index(),

               "total": paginator.count,

            }

        })

    # ==========================
    # TEMPLATE
    # ==========================

    context = {

        "books": page_obj,

        "page_obj": page_obj,

        "search_query": search_query,

        "total_books": total_books,

        "available_books": available_books,

        "borrowed_books": borrowed_books,

        "total_categories": total_categories,

        "categories": categories,

        "languages": languages,

        "resource_types": resource_types,

        "status_choices": status_choices,

    }

    return render(
        request,
        "library_admin/books.html",
        context,
    )
    
    
    
# ============================================
# ADD BOOK VIEW
# ============================================
# from .forms import LibraryResourceForm

# def add_book(request):
#     if request.method == "POST":
#         form = LibraryResourceForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(
#                 request,
#                 "Book added successfully."
#             )
#             return redirect("library_books")
#     else:
#         form = LibraryResourceForm()

#     return render(
#         request,
#         "library_admin/add_book.html",
#         {
#             "form": form
#         }

#     )


# =====================================================
# library_admin/views.py — replaces your existing add_book
# =====================================================

from datetime import date
from uuid import uuid4

from django.contrib import messages
from django.shortcuts import redirect, render

from Library.models import ResourceCopy
from .forms import LibraryResourceForm


# def add_book(request):
   

#     if request.method == "POST":

#         form = LibraryResourceForm(request.POST)

#         if form.is_valid():

#             resource = form.save()

            
#             condition = request.POST.get("condition", "").strip() or "New"

#             _create_copies_for_resource(resource, resource.total_copies, condition)

#             messages.success(
#                 request,
#                 f'Book added successfully with {resource.total_copies} '
#                 f'physical cop{"y" if resource.total_copies == 1 else "ies"} '
#                 f'created ({condition} condition).'
#             )

#             return redirect("library_books")

#     else:

#         form = LibraryResourceForm()

#     return render(
#         request,
#         "library_admin/add_book.html",
#         {
#             "form": form
#         },
#     )


# def _create_copies_for_resource(resource, count, condition="New"):
    

#     new_copies = []

#     for _ in range(count):

#         barcode = f"{resource.id}-{uuid4().hex[:6].upper()}"

#         new_copies.append(
#             ResourceCopy(
#                 resource=resource,
#                 barcode=barcode,
#                 acquisition_date=date.today(),
#                 condition=condition,
#                 status="AVAILABLE",
#             )
#         )

#     ResourceCopy.objects.bulk_create(new_copies)


def add_book(request):

    if request.method == "POST":

        form = LibraryResourceForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            resource = form.save()

            AuditLogger.log(
                request=request,
                action="CREATE",
                module="LibraryAdmin",
                object_type="Book",
                object_id=resource.id,
                description=f"Created book '{resource.title}'.",
                after_data=AuditLogger.model_to_dict(
                    resource,
                    fields=[
                        "title",
                        "isbn_issn",
                        "author",
                        "publisher",
                        "publication_year",
                        "edition",
                        "language",
                        "subject",
                        "shelf_location",
                        "total_copies",
                        "available_copies",
                        "resource_type",
                        "status",
                        "library",
                        "category",
                    ],
                ),
            )

            messages.success(
                request,
                f'Book added successfully with {resource.total_copies} '
                f'physical cop{"y" if resource.total_copies == 1 else "ies"} '
                f'created.'
            )

            return redirect("library_books")

    else:

        form = LibraryResourceForm()

    return render(
        request,
        "library_admin/add_book.html",
        {
            "form": form
        },
    )

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from Library.models import LibraryResource


def view_book(request, uuid):

    print("UUID RECEIVED:", uuid)

    book = get_object_or_404(
        LibraryResource,
        uuid=uuid
    )

    return render(
        request,
        "library_admin/view_book.html",
        {
            "book": book
        }
    )

# ============================================
# EDIT BOOK VIEW
# ============================================

from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)

from django.contrib import messages

from Library.models import (
    Library,
    LibraryResource,
    ResourceCategory,
)


def edit_book(request, uuid):

    # ==========================================
    # GET BOOK
    # ==========================================

    book = get_object_or_404(
        LibraryResource,
        uuid=uuid
    )


    # ==========================================
    # DROPDOWN DATA
    # ==========================================

    libraries = (
        Library.objects
        .filter(
            status="ACTIVE"
        )
        .order_by(
            "library_name"
        )
    )


    categories = (
        ResourceCategory.objects
        .filter(
            status="ACTIVE"
        )
        .order_by(
            "title"
        )
    )


    languages = (
        LibraryResource.objects
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


    # ==========================================
    # POST
    # ==========================================

    if request.method == "POST":

        try:

            # ======================================
            # BASIC INFORMATION
            # ======================================

            library_id = request.POST.get(
                "library"
            )

            category_id = request.POST.get(
                "category"
            )

            resource_type = request.POST.get(
                "resource_type"
            )

            title = request.POST.get(
                "title",
                ""
            ).strip()

            isbn = request.POST.get(
                "isbn",
                ""
            ).strip()

            author = request.POST.get(
                "author",
                ""
            ).strip()


            # ======================================
            # PUBLICATION DETAILS
            # ======================================

            publisher = request.POST.get(
                "publisher",
                ""
            ).strip()

            publication_year = request.POST.get(
                "publication_year"
            )

            edition = request.POST.get(
                "edition",
                ""
            ).strip()

            language = request.POST.get(
                "language",
                ""
            ).strip()

            subject = request.POST.get(
                "subject",
                ""
            ).strip()


            # ======================================
            # INVENTORY
            # ======================================

            shelf_location = request.POST.get(
                "shelf_location",
                ""
            ).strip()

            total_copies = int(
                request.POST.get(
                    "total_copies"
                ) or 0
            )

            available_copies = int(
                request.POST.get(
                    "available_copies"
                ) or 0
            )

            status = request.POST.get(
                "status"
            )


            # ======================================
            # COVER IMAGE
            # ======================================
            #
            # This is the important fix.
            #
            # request.FILES contains uploaded files.
            #
            # If the user selects a NEW image,
            # replace the existing cover.
            #
            # If no image is selected,
            # keep the existing cover.
            # ======================================

            new_cover_image = request.FILES.get(
                "cover_image"
            )


            # ======================================
            # VALIDATION
            # ======================================

            if not library_id:

                messages.error(
                    request,
                    "Please select a library."
                )

                return redirect(
                    "edit_book",
                    uuid=book.uuid
                )


            if not category_id:

                messages.error(
                    request,
                    "Please select a category."
                )

                return redirect(
                    "edit_book",
                    uuid=book.uuid
                )


            if not resource_type:

                messages.error(
                    request,
                    "Please select a resource type."
                )

                return redirect(
                    "edit_book",
                    uuid=book.uuid
                )


            if not title:

                messages.error(
                    request,
                    "Book title is required."
                )

                return redirect(
                    "edit_book",
                    uuid=book.uuid
                )


            if not author:

                messages.error(
                    request,
                    "Author is required."
                )

                return redirect(
                    "edit_book",
                    uuid=book.uuid
                )


            # ======================================
            # GET LIBRARY
            # ======================================

            library = get_object_or_404(
                Library,
                pk=library_id,
                status="ACTIVE"
            )


            # ======================================
            # GET CATEGORY
            # ======================================

            category = get_object_or_404(
                ResourceCategory,
                pk=category_id,
                status="ACTIVE"
            )


            # ======================================
            # COPY VALIDATION
            # ======================================

            if total_copies < 0:

                messages.error(
                    request,
                    "Total copies cannot be negative."
                )

                return redirect(
                    "edit_book",
                    uuid=book.uuid
                )


            if available_copies < 0:

                messages.error(
                    request,
                    "Available copies cannot be negative."
                )

                return redirect(
                    "edit_book",
                    uuid=book.uuid
                )


            if available_copies > total_copies:

                messages.error(
                    request,
                    "Available copies cannot exceed total copies."
                )

                return redirect(
                    "edit_book",
                    uuid=book.uuid
                )


            # ======================================
            # ISBN DUPLICATE CHECK
            # ======================================

            if isbn:

                duplicate = (
                    LibraryResource.objects
                    .filter(
                        isbn_issn=isbn
                    )
                    .exclude(
                        uuid=book.uuid
                    )
                    .exists()
                )

                if duplicate:

                    messages.error(
                        request,
                        "ISBN already exists."
                    )

                    return redirect(
                        "edit_book",
                        uuid=book.uuid
                    )


            # ======================================
            # UPDATE BOOK
            # ======================================

            # ======================================
            # AUDIT - BEFORE DATA
            # ======================================

            before_data = AuditLogger.model_to_dict(
                book,
                fields=[
                    "title",
                    "isbn_issn",
                    "author",
                    "publisher",
                    "publication_year",
                    "edition",
                    "language",
                    "subject",
                    "shelf_location",
                    "total_copies",
                    "available_copies",
                    "resource_type",
                    "status",
                    "library",
                    "category",
                ],
            )

            book.library = library

            book.category = category

            book.resource_type = resource_type

            book.title = title

            book.isbn_issn = isbn

            book.author = author

            book.publisher = (
                publisher
                if publisher
                else None
            )

            book.publication_year = (
                publication_year
                if publication_year
                else None
            )

            book.edition = (
                edition
                if edition
                else None
            )

            book.language = (
                language
                if language
                else None
            )

            book.subject = (
                subject
                if subject
                else None
            )

            book.shelf_location = (
                shelf_location
                if shelf_location
                else None
            )

            book.total_copies = total_copies

            book.available_copies = available_copies

            book.status = status


            # ======================================
            # UPDATE COVER IMAGE
            # ======================================
            #
            # Only replace the image if the user
            # selected a new image.
            # ======================================

            if new_cover_image:

                book.cover_image = new_cover_image


            # ======================================
            # SAVE
            # ======================================

            book.save()

            # ======================================
            # AUDIT - AFTER DATA
            # ======================================

            after_data = AuditLogger.model_to_dict(
                book,
                fields=[
                    "title",
                    "isbn_issn",
                    "author",
                    "publisher",
                    "publication_year",
                    "edition",
                    "language",
                    "subject",
                    "shelf_location",
                    "total_copies",
                    "available_copies",
                    "resource_type",
                    "status",
                    "library",
                    "category",
                ],
            )


            # ======================================
            # CREATE AUDIT LOG
            # ======================================

            AuditLogger.log(
                request=request,
                action="UPDATE",
                module="LibraryAdmin",
                object_type="Book",
                object_id=book.id,
                description=f"Updated book '{book.title}'.",
                before_data=before_data,
                after_data=after_data,
                status="SUCCESS",
            )

            # ======================================
            # SUCCESS MESSAGE
            # ======================================

            messages.success(
                request,
                "Book updated successfully."
            )


            return redirect(
                "library_books"
            )


        # ==========================================
        # VALUE ERROR
        # ==========================================

        except ValueError:

            messages.error(
                request,
                "Please enter valid numbers for the copy fields."
            )

            return redirect(
                "edit_book",
                uuid=book.uuid
            )


        # ==========================================
        # OTHER ERRORS
        # ==========================================

        except Exception as e:

            messages.error(
                request,
                f"Error updating book: {e}"
            )

            return redirect(
                "edit_book",
                uuid=book.uuid
            )


    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        "book": book,

        "libraries": libraries,

        "categories": categories,

        "languages": languages,

        "resource_types": (
            LibraryResource.RESOURCE_TYPES
        ),

        "status_choices": (
            LibraryResource.STATUS_CHOICES
        ),

    }


    # ==========================================
    # RENDER
    # ==========================================

    return render(
        request,
        "library_admin/edit_book.html",
        context
    )

# ============================================
# DELETE BOOK VIEW
# ============================================

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect

def delete_book(request, uuid):

    book = get_object_or_404(
        LibraryResource,
        uuid=uuid
    )

    if request.method == "POST":

        # ======================================
        # AUDIT - CAPTURE BEFORE DATA
        # ======================================

        before_data = AuditLogger.model_to_dict(
            book,
            fields=[
                "title",
                "isbn_issn",
                "author",
                "publisher",
                "publication_year",
                "edition",
                "language",
                "subject",
                "shelf_location",
                "total_copies",
                "available_copies",
                "resource_type",
                "status",
                "library",
                "category",
            ],
        )


        book_id = book.id

        book_title = book.title

        book.delete()

        # ======================================
        # CREATE AUDIT LOG
        # ======================================

        AuditLogger.log(
            request=request,
            action="DELETE",
            module="LibraryAdmin",
            object_type="Book",
            object_id=book_id,
            description=f"Deleted book '{book_title}'.",
            before_data=before_data,
            after_data=None,
            status="SUCCESS",
        )


        messages.success(
            request,
            f'"{book_title}" has been deleted successfully.'
        )

    return redirect("library_books")

# ============================================
# LIBRARIES LIST VIEW
# ============================================

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse

from Library.models import Library
from Admin.bela_admin.models import Building


@staff_member_required
def library_list(request):

    search_query = request.GET.get("q", "").strip()
    building = request.GET.get("building", "")
    status = request.GET.get("status", "")

    libraries = Library.objects.select_related(
    "building"
    ).order_by("library_code")

    # =====================================
    # Search
    # =====================================

    if search_query:

        libraries = libraries.filter(

            Q(library_name__icontains=search_query) |
            Q(library_code__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)

        )

    # =====================================
    # Building Filter
    # =====================================

    if building:

        libraries = libraries.filter(

            building_id=building

        )

    # =====================================
    # Status Filter
    # =====================================

    if status:

        libraries = libraries.filter(

            status=status

        )

    paginator = Paginator(libraries, 5)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    # =====================================
    # AJAX RESPONSE
    # =====================================

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":

        data = []

        for library in page_obj:

            data.append({

                "id": library.id,

                "library_name": library.library_name,

                "library_code": library.library_code,

                "address": library.address or "No Address",

                "building": (
                    library.building.building_name
                    if library.building
                    else ""
                ),

                "email": library.email or "—",

                "phone": library.phone or "—",

                "status": library.status,

                "image": (
                    library.image.url
                    if library.image
                    else ""
                ),


                "view_url": reverse(
                    "view_library",
                    args=[library.id]
                ),

                "edit_url": reverse(
                   "edit_library",
                   args=[library.id]
                ),

                "delete_url": reverse(
                   "delete_library",
                   args=[library.id]
                ),

            })

        return JsonResponse({

            "libraries": data,

            "total": paginator.count,

            "current_page": page_obj.number,

            "num_pages": paginator.num_pages,

            "has_previous": page_obj.has_previous(),

            "has_next": page_obj.has_next(),

            "previous_page": (
                page_obj.previous_page_number()
                if page_obj.has_previous()
                else None
            ),

            "next_page": (
                page_obj.next_page_number()
                if page_obj.has_next()
                else None
            ),

            "start_index": page_obj.start_index(),

            "end_index": page_obj.end_index(),

            "total": paginator.count,

        })

    # =====================================
    # NORMAL PAGE LOAD
    # =====================================

    context = {

        "page_obj": page_obj,

        "libraries": page_obj,

        "search_query": search_query,

        "buildings": Building.objects.filter(
            status="ACTIVE"
        ),

        "selected_building": building,

        "selected_status": status,

        "total_libraries": Library.objects.count(),

        "active_libraries": Library.objects.filter(
            status="ACTIVE"
        ).count(),

        "inactive_libraries": Library.objects.filter(
            status="INACTIVE"
        ).count(),

        "total_buildings": Building.objects.filter(
            status="ACTIVE"
        ).count(),

    }

    return render(

        request,

        "library_admin/libraries.html",

        context

    )

# ============================================
# ADD LIBRARY VIEW
# ============================================

from django.contrib import messages
from django.shortcuts import render, redirect

from .forms import LibraryForm


def add_library(request):

    if request.method == "POST":

        form = LibraryForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            # LibraryForm.save() will create
            # library_hours JSON and save it.
            library = form.save()

            # ======================================
            # AUDIT LOG - CREATE
            # ======================================

            after_data = AuditLogger.model_to_dict(
                library,
                fields=[
                    "library_name",
                    "location",
                    "status",
                    "contact_email",
                    "contact_phone",
                    "library_hours",
                ],
            )

            AuditLogger.log(
                request=request,
                action="CREATE",
                module="LibraryAdmin",
                object_type="Library",
                object_id=library.id,
                description=f"Created library '{library.library_name}'.",
                before_data=None,
                after_data=after_data,
                status="SUCCESS",
            )

            messages.success(
                request,
                "Library added successfully."
            )

            return redirect("library_list")

    else:

        form = LibraryForm()

    return render(
        request,
        "library_admin/add_library.html",
        {
            "form": form
        }
    )

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect

@staff_member_required
def delete_library(request, pk):

    library = get_object_or_404(
        Library,
        pk=pk
    )

    if request.method == "POST":

        # ======================================
        # AUDIT - BEFORE DATA
        # ======================================

        before_data = AuditLogger.model_to_dict(
            library,
            fields=[
                "library_name",
                "location",
                "status",
                "contact_email",
                "contact_phone",
                "library_hours",
            ],
        )

        library_id = library.id

        library_name = library.library_name

        library.delete()

        # ======================================
        # AUDIT LOG - DELETE
        # ======================================

        AuditLogger.log(
            request=request,
            action="DELETE",
            module="LibraryAdmin",
            object_type="Library",
            object_id=library_id,
            description=f"Deleted library '{library_name}'.",
            before_data=before_data,
            after_data=None,
            status="SUCCESS",
        )


        messages.success(
            request,
            f'"{library_name}" deleted successfully.'
        )

    return redirect("library_list")

# ============================================
# EDIT LIBRARY
# ============================================

from django.contrib import messages
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .forms import LibraryForm
from Library.models import Library


@staff_member_required
def edit_library(request, pk):

    library = get_object_or_404(

        Library,

        pk=pk

    )

    if request.method == "POST":

        # ======================================
        # AUDIT - BEFORE DATA
        # Capture before form.save()
        # ======================================

        before_data = AuditLogger.model_to_dict(
            library,
            fields=[
                "library_name",
                "location",
                "status",
                "contact_email",
                "contact_phone",
                "library_hours",
            ],
        )

        form = LibraryForm(

            request.POST,

            request.FILES,

            instance=library

        )

        if form.is_valid():

            library = form.save()

            # ======================================
            # AUDIT - AFTER DATA
            # ======================================

            after_data = AuditLogger.model_to_dict(
                library,
                fields=[
                    "library_name",
                    "location",
                    "status",
                    "contact_email",
                    "contact_phone",
                    "library_hours",
                ],
            )


            # ======================================
            # AUDIT LOG - UPDATE
            # ======================================

            AuditLogger.log(
                request=request,
                action="UPDATE",
                module="LibraryAdmin",
                object_type="Library",
                object_id=library.id,
                description=f"Updated library '{library.library_name}'.",
                before_data=before_data,
                after_data=after_data,
                status="SUCCESS",
            )


            messages.success(

                request,

                "Library updated successfully."

            )

            return redirect(

                "library_list"

            )

    else:

        form = LibraryForm(

            instance=library

        )

    context = {

        "form": form,

        "library": library,

    }

    return render(

        request,

        "library_admin/edit_library.html",

        context

    )

# ============================================
# VIEW LIBRARY
# ============================================

from django.shortcuts import (
    get_object_or_404,
    render,
)

from Library.models import Library


@staff_member_required
def view_library(request, pk):

    library = get_object_or_404(

        Library,

        pk=pk

    )

    context = {

        "library": library,

    }

    return render(

        request,

        "library_admin/view_library.html",

        context

    )

from django.shortcuts import render
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q

from Library.models import (
    BorrowRequest,
    Library,
    LibraryUser,
)

@staff_member_required
def borrow_requests(request):

    # =====================================================
    # GET PARAMETERS
    # =====================================================

    search = request.GET.get(
        "q",
        ""
    ).strip()

    library = request.GET.get(
        "library",
        ""
    ).strip()

    status = request.GET.get(
        "status",
        ""
    ).strip()

    user_type = request.GET.get(
        "user_type",
        ""
    ).strip()

    request_date = request.GET.get(
        "request_date",
        ""
    ).strip()

    # =====================================================
    # BASE QUERYSET
    # =====================================================

    borrow_requests = (

        BorrowRequest.objects

        .select_related(

            "resource",

            "resource__library",

            "library_user",

            "library_user__user",

        )

        .order_by("-request_date")

    )

    # =====================================================
    # SEARCH
    # =====================================================

    if search:

        borrow_requests = borrow_requests.filter(

            Q(resource__title__icontains=search)

            |

            Q(resource__author__icontains=search)

            |

            Q(resource__isbn_issn__icontains=search)

            |

            Q(library_user__user__username__icontains=search)

            |

            Q(library_user__user__first_name__icontains=search)

            |

            Q(library_user__user__last_name__icontains=search)

        )

    # =====================================================
    # LIBRARY FILTER
    # =====================================================

    if library:

        borrow_requests = borrow_requests.filter(

            resource__library_id=library

        )

    # =====================================================
    # STATUS FILTER
    # =====================================================

    if status:

        borrow_requests = borrow_requests.filter(

            status=status

        )

    # =====================================================
    # USER TYPE FILTER
    # =====================================================

    if user_type:

        borrow_requests = borrow_requests.filter(

            library_user__user_type=user_type

        )

    # =====================================================
    # REQUEST DATE FILTER
    # =====================================================

    if request_date:

        borrow_requests = borrow_requests.filter(

            request_date=request_date

        )

    # =====================================================
    # PAGINATION
    # =====================================================

    paginator = Paginator(

        borrow_requests,

        5

    )

    page = request.GET.get(

        "page",

        1

    )

    page_obj = paginator.get_page(page)

        # =====================================================
    # AJAX RESPONSE
    # =====================================================

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":

        borrow_request_data = []

        for obj in page_obj:

            # ----------------------------------------
            # USER
            # ----------------------------------------

            user = obj.library_user.user

            full_name = user.get_full_name().strip()

            if not full_name:
                full_name = user.username

            first_letter = (
                full_name[0].upper()
                if full_name
                else "U"
            )

            # ----------------------------------------
            # PROFILE IMAGE
            # ----------------------------------------

            profile_image = ""

            try:

                if hasattr(user, "profile_image") and user.profile_image:

                    profile_image = user.profile_image.url

            except Exception:

                profile_image = ""

            # ----------------------------------------
            # LIBRARY
            # ----------------------------------------

            library_name = ""

            library_code = ""

            if obj.resource and obj.resource.library:

                library_name = obj.resource.library.library_name or ""

                if hasattr(obj.resource.library, "library_code"):

                    library_code = obj.resource.library.library_code or ""

            # ----------------------------------------
            # REQUEST DATE
            # ----------------------------------------

            request_date_text = ""

            if obj.request_date:

                request_date_text = obj.request_date.strftime(
                    "%d %b %Y"
                )

            # ----------------------------------------
            # APPEND JSON
            # ----------------------------------------

            borrow_request_data.append({

                "uuid": str(obj.uuid),

                "full_name": full_name,

                "username": user.username,

                "first_letter": first_letter,

                "profile_image": profile_image,

                "user_type": obj.library_user.get_user_type_display(),

                "book": obj.resource.title if obj.resource else "",

                "author": obj.resource.author if obj.resource else "",

                "isbn": obj.resource.isbn_issn if obj.resource else "",

                "library": library_name,

                "library_code": library_code,

                "request_date": request_date_text,

                "status": obj.status,

            })

        # =====================================================
        # JSON RESPONSE
        # =====================================================

        return JsonResponse({

            "borrow_requests": borrow_request_data,

            "page": page_obj.number,

            "pages": paginator.num_pages,

            "has_previous": page_obj.has_previous(),

            "has_next": page_obj.has_next(),

            "start": page_obj.start_index(),

            "end": page_obj.end_index(),

            "total": paginator.count,

            "total_requests": BorrowRequest.objects.count(),

            "pending_requests": BorrowRequest.objects.filter(
                status="PENDING"
            ).count(),

            "approved_requests": BorrowRequest.objects.filter(
                status="APPROVED"
            ).count(),

            "rejected_requests": BorrowRequest.objects.filter(
                status="REJECTED"
            ).count(),

        })
        # =====================================================
    # NORMAL PAGE RENDER
    # =====================================================

    context = {

        # -------------------------------------------------
        # TABLE DATA
        # -------------------------------------------------

        "borrow_requests": page_obj,

        "page_obj": page_obj,

        "search_query": search,

        # -------------------------------------------------
        # FILTERS
        # -------------------------------------------------

        "libraries": Library.objects.filter(
            status="ACTIVE"
        ).order_by("library_name"),

        "status_choices": BorrowRequest.STATUS_CHOICES,

        "user_types": LibraryUser.USER_TYPES,

        # -------------------------------------------------
        # STATISTICS
        # -------------------------------------------------

        "total_requests": BorrowRequest.objects.count(),

        "pending_requests": BorrowRequest.objects.filter(
            status="PENDING"
        ).count(),

        "approved_requests": BorrowRequest.objects.filter(
            status="APPROVED"
        ).count(),

        "rejected_requests": BorrowRequest.objects.filter(
            status="REJECTED"
        ).count(),

        # -------------------------------------------------
        # CURRENT FILTER VALUES
        # -------------------------------------------------

        "selected_library": library,

        "selected_status": status,

        "selected_user_type": user_type,

        "selected_request_date": request_date,

    }

    return render(

        request,

        "library_admin/borrow_requests.html",

        context

    )

from django.shortcuts import (
    render,
    get_object_or_404,
    redirect,
)

from django.utils import timezone
from django.urls import reverse
from Library.models import (
    BorrowRequest,
    LibraryStaff,
)
from Staff.models import Notification
 
@staff_member_required
def borrow_request_details(request, request_uuid):

    # =====================================================
    # GET BORROW REQUEST
    # =====================================================

    borrow_request = get_object_or_404(
        BorrowRequest.objects.select_related(
            "resource",
            "resource__library",
            "library_user",
            "library_user__user",
        ),
        uuid=request_uuid
    )

    # =====================================================
    # AVAILABLE COPIES
    # =====================================================

    available_copies = borrow_request.resource.copies.filter(
        status="AVAILABLE"
    ).count()

    # =====================================================
    # STUDENT UUID
    # =====================================================

    student_uuid = borrow_request.library_user.user.uuid

    # =====================================================
    # APPROVE / REJECT
    # =====================================================

    if request.method == "POST":

        action = request.POST.get("action")

        # ---------------------------------------------
        # CURRENT LIBRARY STAFF
        # ---------------------------------------------

        library_staff = LibraryStaff.objects.filter(
            staff__user=request.user,
            active=True
        ).first()

        # ---------------------------------------------
        # APPROVE
        # ---------------------------------------------
        

        if action == "approve":
            
            before_data = AuditLogger.model_to_dict(
                borrow_request,
                [
                    "status",
                    "approved_date",
                    "rejection_reason",
                ]
            )

            borrow_request.status = "APPROVED"
            borrow_request.approved_by = library_staff
            borrow_request.approved_date = timezone.now()
            borrow_request.rejection_reason = ""

            borrow_request.save()
            
            after_data = AuditLogger.model_to_dict(
                borrow_request,
                [
                    "status",
                    "approved_date",
                    "rejection_reason",
                ]
            )

            AuditLogger.log(
                request=request,
                action="APPROVE",
                module="LibraryAdmin",
                object_type="BorrowRequest",
                object_id=borrow_request.uuid,
                description=(
                    f'Approved borrow request for '
                    f'"{borrow_request.resource.title}".'
                ),
                before_data=before_data,
                after_data=after_data,
                status="SUCCESS",
            )

            Notification.objects.create(
                user=borrow_request.library_user.user,

                title="Borrow Request Approved",

                message=(
                    f'Your request for "{borrow_request.resource.title}" '
                    f'has been approved. '
                    f'Please visit the library to collect your book.'
                ),

                notification_type="SUCCESS",
                link=reverse("Student:student_borrow_requests",kwargs={"uuid": borrow_request.library_user.user.uuid}),
                            
                # NEW
                related_borrow_request_uuid=borrow_request.uuid,
            )

            return redirect("borrow_requests")

        # ---------------------------------------------
        # REJECT
        # ---------------------------------------------

        elif action == "reject":
            
            before_data = AuditLogger.model_to_dict(
                borrow_request,
                [
                    "status",
                    "approved_date",
                    "rejection_reason",
                ]
            )

            borrow_request.status = "REJECTED"
            borrow_request.approved_by = library_staff
            borrow_request.approved_date = timezone.now()

            borrow_request.rejection_reason = request.POST.get(
                "rejection_reason",
                ""
            )

            borrow_request.save()
            
            after_data = AuditLogger.model_to_dict(
                borrow_request,
                [
                    "status",
                    "approved_date",
                    "rejection_reason",
                ]
            )

            AuditLogger.log(
                request=request,
                action="REJECT",
                module="LibraryAdmin",
                object_type="BorrowRequest",
                object_id=borrow_request.uuid,
                description=(
                    f'Rejected borrow request for '
                    f'"{borrow_request.resource.title}".'
                ),
                before_data=before_data,
                after_data=after_data,
                status="SUCCESS",
            )

            Notification.objects.create(
                user=borrow_request.library_user.user,

                title="Borrow Request Rejected",

                message=(
                    f'Your request for "{borrow_request.resource.title}" '
                    f'has been rejected.\n\n'
                    f'Reason: {borrow_request.rejection_reason}'
                ),

                notification_type="ERROR",
                link=reverse("Student:student_borrow_requests",kwargs={"uuid": borrow_request.library_user.user.uuid}),
                 
            )

            return redirect("borrow_requests")

    # =====================================================
    # USER BORROW DETAILS
    # =====================================================
    
    library_user = borrow_request.library_user
    
    
    # ---------------------------------------------
    # USER TYPE
    # ---------------------------------------------
    
    user_type = library_user.get_user_type_display()
    
    
    # ---------------------------------------------
    # CURRENTLY BORROWED
    # ---------------------------------------------
    
    current_borrowed_count = BorrowRequest.objects.filter(
        library_user=library_user,
        status="APPROVED"
    ).count()
    
    
    # ---------------------------------------------
    # PENDING REQUESTS
    # ---------------------------------------------
    
    pending_requests_count = BorrowRequest.objects.filter(
        library_user=library_user,
        status="PENDING"
    ).count()

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {
        "borrow_request": borrow_request,
        "available_copies": available_copies,

        # USER INFORMATION
        "user_type": user_type,
        "current_borrowed_count": current_borrowed_count,
        "pending_requests_count": pending_requests_count,
    }

    # =====================================================
    # RENDER
    # =====================================================

    return render(
        request,
        "library_admin/borrow_request_details.html",
        context
    )

# =====================================================
# issue queue
# =====================================================
 
 
 
from datetime import date
 
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.core.paginator import Paginator
 
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.shortcuts import render
 
from Library.models import (
    BorrowRequest,
    BorrowTransaction,
    Library,
    LibraryUser,
    ResourceCategory,
)
 
STALE_THRESHOLD_DAYS = 3
 
SORT_OPTIONS = {
    "oldest_waiting": "approved_date",
    "newest_approved": "-approved_date",
    "student_name": "library_user__user__first_name",
    "book_title": "resource__title",
}
 
 
@staff_member_required
def issue_queue(request):
    """
    Issue Queue
    """
 
    # -------------------------------------------------
    # SEARCH + FILTER VALUES
    # -------------------------------------------------
 
    search_query = request.GET.get("q", "").strip()
 
    selected_library = request.GET.get("library", "")
    selected_user_type = request.GET.get("user_type", "")
    selected_category = request.GET.get("category", "")
 
    waiting_filter = request.GET.get("waiting", "all")
    sort_by = request.GET.get("sort", "oldest_waiting")
 
    page = request.GET.get("page", 1)
 
    # -------------------------------------------------
    # BASE QUERY
    # -------------------------------------------------
 
    base_qs = (
        BorrowRequest.objects
        .select_related(
            "resource",
            "resource__library",
            "resource__category",
            "library_user",
            "library_user__user",
            "approved_by",
        )
        .filter(
            status="APPROVED",
            issued_transaction__isnull=True,
        )
    )
 
    # -------------------------------------------------
    # SEARCH
    # -------------------------------------------------
 
    if search_query:
        base_qs = base_qs.filter(
            Q(resource__title__icontains=search_query)
            | Q(resource__author__icontains=search_query)
            | Q(resource__isbn_issn__icontains=search_query)
            | Q(library_user__user__first_name__icontains=search_query)
            | Q(library_user__user__last_name__icontains=search_query)
        )
 
    # -------------------------------------------------
    # LIBRARY FILTER
    # -------------------------------------------------
 
    if selected_library:
        base_qs = base_qs.filter(
            resource__library__library_code=selected_library
        )
 
    # -------------------------------------------------
    # USER TYPE FILTER
    # -------------------------------------------------
 
    if selected_user_type:
        base_qs = base_qs.filter(
            library_user__user_type=selected_user_type
        )
 
    # -------------------------------------------------
    # CATEGORY FILTER
    # -------------------------------------------------
 
    if selected_category and selected_category.isdigit():
        base_qs = base_qs.filter(
            resource__category_id=selected_category
        )
 
    # -------------------------------------------------
    # SORT
    # -------------------------------------------------
 
    order_field = SORT_OPTIONS.get(sort_by, "approved_date")
    base_qs = base_qs.order_by(order_field)
 
    # -------------------------------------------------
    # BUILD RESULT ROWS
    # -------------------------------------------------
 
    today = date.today()
    
 
    all_rows = []
 
    for req in base_qs:
 
        approved_date = (
            req.approved_date.date()
            if req.approved_date
            else None
        )
 
        waiting_days = (
            (today - approved_date).days
            if approved_date
            else None
        )
 
        is_stale = (
            waiting_days is not None
            and waiting_days >= STALE_THRESHOLD_DAYS
        )
 
        no_copies = req.resource.available_copies <= 0
 
        all_rows.append({
            "request": req,
            "waiting_days": waiting_days,
            "is_stale": is_stale,
            "no_copies": no_copies,
        })
 
    # -------------------------------------------------
    # WAITING FILTER
    # -------------------------------------------------
 
    def matches_waiting(row):
 
        d = row["waiting_days"]
 
        if waiting_filter == "all":
            return True
 
        if waiting_filter == "today":
            return d == 0
 
        if waiting_filter == "1-3":
            return d is not None and 1 <= d <= 3
 
        if waiting_filter in ("gt3", "stale"):
            return d is not None and d >= STALE_THRESHOLD_DAYS
 
        return True
 
    pending_issue = [
        row
        for row in all_rows
        if matches_waiting(row)
    ]
 
    # -------------------------------------------------
    # PAGINATION (NEW)
    # -------------------------------------------------
 
    paginator = Paginator(pending_issue, 5)
 
    page_obj = paginator.get_page(page)
   
        # -------------------------------------------------
    # STATISTICS
    # -------------------------------------------------
 
    all_count = len(all_rows)
 
    ready_today_count = sum(
        1 for row in all_rows
        if row["waiting_days"] == 0
    )
 
    stale_count = sum(
        1 for row in all_rows
        if row["is_stale"]
    )
 
    no_copies_count = sum(
        1 for row in all_rows
        if row["no_copies"]
    )
 
    # -------------------------------------------------
    # ISSUED TODAY
    # -------------------------------------------------
 
    issued_today_count = BorrowTransaction.objects.filter(
        issue_date=today,
        borrow_request__isnull=False,
    ).count()
 
    # -------------------------------------------------
    # DROPDOWN DATA
    # -------------------------------------------------
 
    libraries = (
        Library.objects
        .filter(status="ACTIVE")
        .order_by("library_name")
    )
 
    categories = (
        ResourceCategory.objects
        .filter(status="ACTIVE")
        .order_by("title")
    )
 
    user_type_choices = LibraryUser.USER_TYPES
 
    # -------------------------------------------------
    # CONTEXT
    # -------------------------------------------------
 
    context = {
 
        # Paginated rows
        "page_obj": page_obj,
 
        # Counts
        "pending_count": len(pending_issue),
        "all_count": all_count,
        "ready_today_count": ready_today_count,
        "stale_count": stale_count,
        "no_copies_count": no_copies_count,
        "issued_today_count": issued_today_count,
 
        # Search
        "search_query": search_query,
 
        # Dropdowns
        "libraries": libraries,
        "categories": categories,
        "user_type_choices": user_type_choices,
 
        # Selected values
        "selected_library": selected_library,
        "selected_user_type": selected_user_type,
        "selected_category": selected_category,
        "waiting_filter": waiting_filter,
        "sort_by": sort_by,
    }
 
    # -------------------------------------------------
    # AJAX
    # -------------------------------------------------
 
    is_ajax = (
        request.headers.get("X-Requested-With")
        == "XMLHttpRequest"
    )
 
    if is_ajax:
 
        html = render_to_string(
            "library_admin/nancy/issue_queue.html",
            context,
            request=request,
        )
 
        return JsonResponse({
            "html": html
        })
 
    return render(
        request,
        "library_admin/nancy/issue_queue.html",
        context,
    )
   
   
# =====================================================
# issue date
# =====================================================


from datetime import date, timedelta
 
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
 
from Library.models import BorrowRequest, BorrowTransaction, ResourceCopy
 
 
LOAN_PERIOD_BY_USER_TYPE = {
    "STUDENT": 28,
    "FACULTY": 112,
    "STAFF": 112,
    "ALUMNI": 28,
    "GUEST": 14,
}
 
DEFAULT_LOAN_PERIOD_DAYS = 28
 
 
def _loan_period_for(library_user):
    return LOAN_PERIOD_BY_USER_TYPE.get(
        library_user.user_type,
        DEFAULT_LOAN_PERIOD_DAYS,
    )
 
 
def _evaluate_blockers(borrow_request):
   
    library_user = borrow_request.library_user
    today = date.today()
 
    blockers = []
 
    if not library_user.active:
        blockers.append("This student's library membership is inactive.")
 
    if library_user.membership_expiry and library_user.membership_expiry < today:
        blockers.append(
            f"Membership expired on {library_user.membership_expiry.strftime('%b %d, %Y')}."
        )
 
    active_loans = BorrowTransaction.objects.filter(
        library_user=library_user,
        status__in=["ISSUED", "OVERDUE"],
    )
 
    overdue_count = active_loans.filter(status="OVERDUE").count()
    active_count = active_loans.count()
 
    if overdue_count > 0:
        blockers.append(
            f"Student has {overdue_count} overdue book{'s' if overdue_count != 1 else ''}. "
            f"Must be returned before a new book can be issued."
        )
 
    if active_count >= library_user.borrowing_limit:
        blockers.append(
            f"Student is at their borrowing limit ({active_count} of {library_user.borrowing_limit})."
        )
 
    available_copies = ResourceCopy.objects.filter(
        resource=borrow_request.resource,
        status="AVAILABLE",
    ).order_by("barcode")
 
    if not available_copies.exists():
        blockers.append("No available copies of this book right now.")
 
    return blockers, available_copies, active_count, overdue_count
 
 
# @staff_member_required
@login_required(login_url="/login/")
def issue_book_detail(request, request_uuid):
    
    
    if not request.user.is_staff:
        return HttpResponseForbidden(
            "You are not authorized to issue library books."
        )

    # if not request.session.get("issue_pin_verified", False):
    #     return redirect(
    #         "issue_book_qr_entry",
    #         request_uuid=request_uuid,
    #     )
 
    borrow_request = get_object_or_404(
        BorrowRequest,
        uuid=request_uuid,
        status="APPROVED",
    )
 
    # Already issued? (e.g. staff opened this page twice)
    if hasattr(borrow_request, "issued_transaction") and borrow_request.issued_transaction:
        messages.info(
            request,
            f'"{borrow_request.resource.title}" has already been issued for this request.'
        )
        return redirect("issue_queue")
 
    # -------------------------------------------------
    # POST — actually issue the book
    # -------------------------------------------------
    if request.method == "POST":
 
        blockers, available_copies, active_count, overdue_count = _evaluate_blockers(borrow_request)
 
        if blockers:
            for reason in blockers:
                messages.error(request, reason)
            return redirect("issue_book_detail",request_uuid=borrow_request.uuid)
        
        before_data = {
            "transaction_status": None,
            "borrow_request_status": borrow_request.status,
            "copy_status": "AVAILABLE",
            "available_copies": borrow_request.resource.available_copies,
            "active_loans": active_count,
        }
 
        selected_copy_id = request.POST.get("copy_id")
 
        today = date.today()
        loan_period_days = _loan_period_for(borrow_request.library_user)
        due_date = today + timedelta(days=loan_period_days)
 
        # ---------------------------------------------
        # Everything below happens as one atomic unit:
        # ---------------------------------------------
        try:
            with transaction.atomic():
 
                copy = (
                    ResourceCopy.objects
                    .select_for_update()
                    .filter(id=selected_copy_id, resource=borrow_request.resource, status="AVAILABLE")
                    .first()
                )
 
                if copy is None:
                    messages.error(
                        request,
                        "The selected copy is no longer available. Please choose another."
                    )
                    return redirect("issue_book_detail",request_uuid=borrow_request.uuid)
 
                borrow_transaction = BorrowTransaction.objects.create(
                    copy=copy,
                    library_user=borrow_request.library_user,
                    borrow_request=borrow_request,
                    issue_date=today,
                    due_date=due_date,
                    status="ISSUED",
                )
                
                # ============================================
                # NEW — advance the request's own status too,
                # so it doesn't stay stuck at "Approved" forever
                # ============================================
       
 
                copy.status = "CHECKED_OUT"
                copy.save()
 
                resource = borrow_request.resource
                if resource.available_copies > 0:
                    resource.available_copies -= 1
                    resource.save()
 
        except Exception:
            messages.error(
                request,
                "Something went wrong while issuing this book. Nothing was saved — please try again."
            )
            return redirect("issue_book_detail",request_uuid=borrow_request.uuid)
        
        after_data = {
            "transaction_id": borrow_transaction.id,
            "transaction_status": borrow_transaction.status,
            "copy_status": copy.status,
            "available_copies": resource.available_copies,
            "issue_date": borrow_transaction.issue_date.isoformat(),
            "due_date": borrow_transaction.due_date.isoformat(),
            "renewal_count": borrow_transaction.renewal_count,
        }

        AuditLogger.log(
            request=request,
            action="ISSUE",
            module="LibraryAdmin",
            object_type="BorrowTransaction",
            object_id=borrow_transaction.id,
            description=(
                f'Issued "{borrow_request.resource.title}" '
                f'(Copy: {copy.barcode}) to '
                f'{borrow_request.library_user.user.get_full_name() or borrow_request.library_user.user.username}.'
            ),
            before_data=before_data,
            after_data=after_data,
            status="SUCCESS",
        )
 
        messages.success(
            request,
            f'"{borrow_request.resource.title}" issued to {borrow_request.library_user.user.get_full_name()}. '
            f'Due back {due_date.strftime("%b %d, %Y")}.'
        )
 
        return redirect("issue_queue")
 
    # -------------------------------------------------
    # GET — show the confirmation page
    # -------------------------------------------------
    blockers, available_copies, active_count, overdue_count = _evaluate_blockers(borrow_request)
 
    loan_period_days = _loan_period_for(borrow_request.library_user)
    due_date_preview = date.today() + timedelta(days=loan_period_days)
    default_copy = available_copies.first()

    resource = borrow_request.resource

    
    cover_class = f"cover-{(resource.id % 5) + 1}"

    context = {
        "borrow_request": borrow_request,
        "library_user": borrow_request.library_user,
        "blockers": blockers,
        "is_blocked": len(blockers) > 0,
        "available_copies": available_copies,
        "default_copy_id": default_copy.id if default_copy else None,
        "active_loan_count": active_count,
        "overdue_count": overdue_count,
        "issue_date_preview": date.today(),
        "due_date_preview": due_date_preview,
        "loan_period_days": loan_period_days,
        "cover_class": cover_class,
        "issuing_staff": request.user.get_full_name() or request.user.username,
        "total_copies": resource.total_copies,
    }
 
    return render(
        request,
        "library_admin/nancy/issue_book_detail.html",
        context,
    )
    
# =====================================================
# library_admin/views.py — Active Loans + exports
# =====================================================

from datetime import date
from io import BytesIO

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from Library.models import BorrowTransaction

import openpyxl
from openpyxl.styles import Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


DUE_SOON_THRESHOLD_DAYS = 3

EXPORT_COLUMNS = [
    "Student", "User Type", "Book Title", "Author",
    "Barcode", "Library", "Issue Date", "Due Date", "Status",
]


# =====================================================
# SHARED FILTER LOGIC
# =====================================================

def _get_filtered_loans(request):

    search_query = request.GET.get("q", "").strip()

    transactions = (
        BorrowTransaction.objects
        .select_related(
            "copy",
            "copy__resource",
            "copy__resource__library",
            "library_user",
            "library_user__user",
        )
        .filter(status__in=["ISSUED", "OVERDUE"])
        .order_by("due_date")
    )

    if search_query:
        transactions = transactions.filter(
            Q(copy__resource__title__icontains=search_query)
            | Q(library_user__user__first_name__icontains=search_query)
            | Q(library_user__user__last_name__icontains=search_query)
            | Q(copy__barcode__icontains=search_query)
        )

    today = date.today()

    loans = []
    for txn in transactions:

        days_left = (txn.due_date - today).days

        if days_left < 0:
            computed_status = "OVERDUE"
        elif days_left <= DUE_SOON_THRESHOLD_DAYS:
            computed_status = "DUE_SOON"
        else:
            computed_status = "ACTIVE"

        loans.append({
            "transaction": txn,
            "computed_status": computed_status,
            "days_left": days_left,
            "days_overdue": abs(days_left) if days_left < 0 else 0,
        })

    return loans, search_query


def _loan_row(loan):
    """
    One flat row of plain values, shared by both export formats,
    so Excel and PDF always show identical data.
    """
    txn = loan["transaction"]

    status_label = {
        "OVERDUE": f'{loan["days_overdue"]} day(s) overdue',
        "DUE_SOON": f'{loan["days_left"]} day(s) left',
        "ACTIVE": f'{loan["days_left"]} days left',
    }[loan["computed_status"]]

    return [
        txn.library_user.user.get_full_name(),
        txn.library_user.get_user_type_display(),
        txn.copy.resource.title,
        txn.copy.resource.author,
        txn.copy.barcode,
        txn.copy.resource.library.library_name if txn.copy.resource.library else "—",
        txn.issue_date.strftime("%b %d, %Y"),
        txn.due_date.strftime("%b %d, %Y"),
        status_label,
    ]


# =====================================================
# PAGE VIEW
# =====================================================

# @staff_member_required
# def active_loans(request):

#     loans, search_query = _get_filtered_loans(request)

#     total_active = len(loans)
#     overdue_count = sum(1 for l in loans if l["computed_status"] == "OVERDUE")
#     due_soon_count = sum(1 for l in loans if l["computed_status"] == "DUE_SOON")

#     today = date.today()
#     returned_today_count = BorrowTransaction.objects.filter(
#         status="RETURNED",
#         return_date=today,
#     ).count()

#     context = {
#         "loans": loans,
#         "total_active": total_active,
#         "overdue_count": overdue_count,
#         "due_soon_count": due_soon_count,
#         "returned_today_count": returned_today_count,
#         "search_query": search_query,
#     }

#     return render(request, "library_admin/active_loans.html", context)


# =====================================================
# EXCEL EXPORT
# =====================================================

@staff_member_required
def export_active_loans_excel(request):

    loans, search_query = _get_filtered_loans(request)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Active Loans"

    header_fill = PatternFill(start_color="9B1B30", end_color="9B1B30", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)

    ws.append(EXPORT_COLUMNS)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font

    for loan in loans:
        ws.append(_loan_row(loan))

    for col in ws.columns:
        max_len = max(len(str(cell.value)) for cell in col if cell.value)
        ws.column_dimensions[col[0].column_letter].width = max_len + 4

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"active_loans_{date.today().isoformat()}.xlsx"

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response


# =====================================================
# PDF EXPORT
# =====================================================

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import mm

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)

from django.contrib.staticfiles.finders import find
from django.utils import timezone


@staff_member_required
def export_active_loans_pdf(request):

    # ======================================================
    # WISCONSIN COLORS
    # ======================================================

    WISCONSIN_RED = colors.HexColor("#C5050C")
    DARK_RED = colors.HexColor("#9E0006")
    WISCONSIN_NAVY = colors.HexColor("#13294B")
    DARK_NAVY = colors.HexColor("#0B1F3A")

    WHITE = colors.white
    BLACK = colors.HexColor("#1A1A1A")
    TEXT = colors.HexColor("#273142")
    MUTED = colors.HexColor("#667085")
    BORDER = colors.HexColor("#D5D9E0")
    LIGHT_GRAY = colors.HexColor("#F7F8FA")
    VERY_LIGHT_GRAY = colors.HexColor("#FBFBFC")

    # ======================================================
    # GET SEARCH FILTER
    # ======================================================

    search_query = request.GET.get(
        "q",
        ""
    ).strip()

    # ======================================================
    # GET ACTIVE LOANS
    # ======================================================

    loans, search_query = _get_filtered_loans(request)

    # ======================================================
    # GENERATED DATE
    # ======================================================

    from django.utils import timezone

    generated_at = timezone.localtime().strftime(
        "%d %b %Y, %I:%M %p"
    )

    # ======================================================
    # PDF BUFFER
    # ======================================================

    buffer = BytesIO()

    # ======================================================
    # A4 LANDSCAPE
    # ======================================================

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=13 * mm,
        rightMargin=13 * mm,
        topMargin=12 * mm,
        bottomMargin=14 * mm,
        title="Wisconsin Libraries - Active Loans Report",
        author="Wisconsin Libraries",
    )

    # ======================================================
    # STYLES
    # ======================================================

    styles = getSampleStyleSheet()

    # ======================================================
    # BRAND NAME
    # ======================================================

    brand_style = ParagraphStyle(
        "BrandStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=17,
        textColor=WISCONSIN_RED,
        alignment=TA_LEFT,
    )

    # ======================================================
    # LIBRARIES TEXT
    # ======================================================

    libraries_style = ParagraphStyle(
        "LibrariesStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=9,
        textColor=WISCONSIN_NAVY,
        alignment=TA_LEFT,
        letterSpacing=1.5,
    )

    # ======================================================
    # REPORT TITLE
    # ======================================================

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=20,
        textColor=DARK_NAVY,
        alignment=TA_CENTER,
    )

    # ======================================================
    # SUBTITLE
    # ======================================================

    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=MUTED,
        alignment=TA_CENTER,
    )

    # ======================================================
    # GENERATED STYLE
    # ======================================================

    generated_style = ParagraphStyle(
        "GeneratedStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=10,
        textColor=MUTED,
        alignment=TA_RIGHT,
    )

    # ======================================================
    # GENERATED VALUE
    # ======================================================

    generated_value_style = ParagraphStyle(
        "GeneratedValueStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=DARK_NAVY,
        alignment=TA_RIGHT,
    )

    # ======================================================
    # TABLE TEXT
    # ======================================================

    table_style = ParagraphStyle(
        "TableStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.6,
        leading=8,
        textColor=TEXT,
        alignment=TA_LEFT,
    )

    # ======================================================
    # TABLE CENTER
    # ======================================================

    table_center_style = ParagraphStyle(
        "TableCenterStyle",
        parent=table_style,
        alignment=TA_CENTER,
    )

    # ======================================================
    # TABLE HEADER
    # ======================================================

    table_header_style = ParagraphStyle(
        "TableHeaderStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=6.2,
        leading=7,
        textColor=WHITE,
        alignment=TA_LEFT,
    )

    table_header_center_style = ParagraphStyle(
        "TableHeaderCenterStyle",
        parent=table_header_style,
        alignment=TA_CENTER,
    )

    # ======================================================
    # FOOTER
    # ======================================================

    footer_style = ParagraphStyle(
        "FooterStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.5,
        leading=8,
        textColor=MUTED,
        alignment=TA_CENTER,
    )

    # ======================================================
    # PDF ELEMENTS
    # ======================================================

    elements = []

    # ======================================================
    # WISCONSIN LOGO
    # ======================================================

    logo_path = find(
        "images/navina/W-logo.png"
    )

    if logo_path:

        logo = Image(
            logo_path,
            width=35 * mm,
            height=25 * mm,
        )

    else:

        logo = Table(
            [
                [
                    Paragraph(
                        "<b>W</b>",
                        ParagraphStyle(
                            "FallbackLogo",
                            parent=styles["Normal"],
                            fontName="Helvetica-Bold",
                            fontSize=18,
                            textColor=WHITE,
                            alignment=TA_CENTER,
                        )
                    )
                ]
            ],
            colWidths=[18 * mm],
            rowHeights=[18 * mm],
        )

        logo.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    DARK_NAVY,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    1,
                    DARK_NAVY,
                ),
            ])
        )

    # ======================================================
    # BRAND TEXT
    # ======================================================

    brand_text = Table(
        [
            [
                Paragraph(
                    "WISCONSIN",
                    brand_style
                )
            ],
            [
                Paragraph(
                    "L I B R A R I E S",
                    libraries_style
                )
            ],
        ],
        colWidths=[47 * mm],
    )

    brand_text.setStyle(
        TableStyle([
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
        ])
    )

    # ======================================================
    # BRAND BLOCK
    # ======================================================

    brand_block = Table(
        [
            [
                logo,
                brand_text
            ]
        ],
        colWidths=[27 * mm, 47 * mm],
    )

    brand_block.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
        ])
    )

    # ======================================================
    # CENTER REPORT TITLE
    # ======================================================

    report_title = Table(
        [
            [
                Paragraph(
                    "ACTIVE LOANS REPORT",
                    title_style
                )
            ],
            [
                Paragraph(
                    "Currently Issued Books &amp; Loan Management",
                    subtitle_style
                )
            ],
        ],
        colWidths=[135 * mm],
    )

    report_title.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
        ])
    )

    # ======================================================
    # GENERATED BOX
    # ======================================================

    generated_block = Table(
        [
            [
                Paragraph(
                    "GENERATED",
                    generated_style
                )
            ],
            [
                Paragraph(
                    generated_at,
                    generated_value_style
                )
            ],
        ],
        colWidths=[55 * mm],
    )

    generated_block.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
        ])
    )

    # ======================================================
    # MAIN HEADER
    # ======================================================

    header = Table(
        [
            [
                brand_block,
                report_title,
                generated_block
            ]
        ],
        colWidths=[70 * mm, 137 * mm, 70 * mm],
    )

    header.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
        ])
    )

    elements.append(header)

    # ======================================================
    # NAVY DIVIDER
    # ======================================================

    elements.append(
        Spacer(
            1,
            4 * mm
        )
    )

    accent = Table(
        [[""]],
        colWidths=[270 * mm],
        rowHeights=[1.3 * mm],
    )

    accent.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                DARK_NAVY,
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
        ])
    )

    elements.append(accent)

    elements.append(
        Spacer(
            1,
            5 * mm
        )
    )

    # ======================================================
    # FILTER INFORMATION
    # ======================================================

    if search_query:

        filter_text = (
            f"Search: {search_query}"
        )

    else:

        filter_text = "All Active Loan Records"

    filter_style = ParagraphStyle(
        "FilterStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        textColor=MUTED,
        alignment=TA_LEFT,
    )

    elements.append(
        Paragraph(
            filter_text,
            filter_style
        )
    )

    elements.append(
        Spacer(
            1,
            4 * mm
        )
    )

    # ======================================================
    # TABLE DATA
    # ======================================================

    table_data = [
        [
            Paragraph(
                "STUDENT",
                table_header_style
            ),
            Paragraph(
                "USER TYPE",
                table_header_style
            ),
            Paragraph(
                "BOOK",
                table_header_style
            ),
            Paragraph(
                "AUTHOR",
                table_header_style
            ),
            Paragraph(
                "BARCODE",
                table_header_center_style
            ),
            Paragraph(
                "LIBRARY",
                table_header_style
            ),
            Paragraph(
                "ISSUE",
                table_header_center_style
            ),
            Paragraph(
                "DUE",
                table_header_center_style
            ),
            Paragraph(
                "STATUS",
                table_header_center_style
            ),
        ]
    ]

    # ======================================================
    # ADD ACTIVE LOAN RECORDS
    # ======================================================

    for loan in loans:

        transaction = loan["transaction"]

        library_user = transaction.library_user

        user = library_user.user

        resource = (
            transaction.copy.resource
            if transaction.copy
            else None
        )

        # --------------------------------------------------
        # STUDENT
        # --------------------------------------------------

        student_name = (
            user.get_full_name().strip()
            or user.first_name
            or user.username
            or "Unknown"
        )

        student_email = (
            user.email
            or ""
        )

        student_text = (
            f"<b>{student_name}</b>"
            f"<br/>"
            f"<font color='#667085'>"
            f"{student_email}"
            f"</font>"
        )

        # --------------------------------------------------
        # BOOK
        # --------------------------------------------------

        book_title = (
            resource.title
            if resource
            else "Unknown Book"
        )

        book_author = (
            resource.author
            if resource and resource.author
            else "Unknown Author"
        )

        book_text = (
            f"<b>{book_title}</b>"
            f"<br/>"
            f"<font color='#667085'>"
            f"{book_author}"
            f"</font>"
        )

        # --------------------------------------------------
        # USER TYPE
        # --------------------------------------------------

        user_type = (
            library_user.get_user_type_display()
        )

        # --------------------------------------------------
        # BARCODE
        # --------------------------------------------------

        barcode = (
            transaction.copy.barcode
            if transaction.copy
            else "-"
        )

        # --------------------------------------------------
        # LIBRARY
        # --------------------------------------------------

        library_name = (
            resource.library.library_name
            if resource and resource.library
            else "-"
        )

        # --------------------------------------------------
        # DATES
        # --------------------------------------------------

        issue_date = (
            transaction.issue_date.strftime(
                "%d %b %Y"
            )
            if transaction.issue_date
            else "-"
        )

        due_date = (
            transaction.due_date.strftime(
                "%d %b %Y"
            )
            if transaction.due_date
            else "-"
        )

        # --------------------------------------------------
        # STATUS
        # --------------------------------------------------

        if loan["computed_status"] == "OVERDUE":

            status_text = (
                f"<b>"
                f"<font color='#C5050C'>"
                f"OVERDUE"
                f"</font>"
                f"</b>"
                f"<br/>"
                f"{loan['days_overdue']} days"
            )

        elif loan["computed_status"] == "DUE_SOON":

            status_text = (
                f"<b>"
                f"<font color='#B36B00'>"
                f"DUE SOON"
                f"</font>"
                f"</b>"
                f"<br/>"
                f"{loan['days_left']} days left"
            )

        else:

            status_text = (
                f"<b>"
                f"<font color='#16834A'>"
                f"ACTIVE"
                f"</font>"
                f"</b>"
                f"<br/>"
                f"{loan['days_left']} days left"
            )

        # ==================================================
        # ADD ROW
        # ==================================================

        table_data.append(
            [
                Paragraph(
                    student_text,
                    table_style
                ),

                Paragraph(
                    user_type,
                    table_style
                ),

                Paragraph(
                    book_text,
                    table_style
                ),

                Paragraph(
                    book_author,
                    table_style
                ),

                Paragraph(
                    barcode,
                    table_center_style
                ),

                Paragraph(
                    library_name,
                    table_style
                ),

                Paragraph(
                    issue_date,
                    table_center_style
                ),

                Paragraph(
                    due_date,
                    table_center_style
                ),

                Paragraph(
                    status_text,
                    table_center_style
                ),
            ]
        )

    # ======================================================
    # EMPTY DATA
    # ======================================================

    if not loans:

        table_data.append(
            [
                Paragraph(
                    "No active loan records found.",
                    ParagraphStyle(
                        "EmptyStyle",
                        parent=table_style,
                        alignment=TA_CENTER,
                        textColor=MUTED,
                    )
                ),
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        )

    # ======================================================
    # PROFESSIONAL TABLE
    # ======================================================

    loan_table = Table(
        table_data,

        colWidths=[
            43 * mm,   # Student
            27 * mm,   # User Type
            42 * mm,   # Book
            34 * mm,   # Author
            24 * mm,   # Barcode
            32 * mm,   # Library
            22 * mm,   # Issue
            22 * mm,   # Due
            24 * mm,   # Status
        ],

        repeatRows=1,
        hAlign="CENTER",
    )

    # ======================================================
    # TABLE STYLE
    # ======================================================

    table_commands = [

        # Header
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            WISCONSIN_NAVY,
        ),

        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            WHITE,
        ),

        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE",
        ),

        # Outer border
        (
            "BOX",
            (0, 0),
            (-1, -1),
            0.8,
            WISCONSIN_NAVY,
        ),

        # Inner grid
        (
            "INNERGRID",
            (0, 0),
            (-1, -1),
            0.35,
            BORDER,
        ),

        # Padding
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            5,
        ),

        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            5,
        ),

        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),

        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
    ]

    # ======================================================
    # ALTERNATING ROWS
    # ======================================================

    for row_index in range(
        1,
        len(table_data)
    ):

        if row_index % 2 == 0:

            table_commands.append(
                (
                    "BACKGROUND",
                    (0, row_index),
                    (-1, row_index),
                    LIGHT_GRAY,
                )
            )

        else:

            table_commands.append(
                (
                    "BACKGROUND",
                    (0, row_index),
                    (-1, row_index),
                    WHITE,
                )
            )

    loan_table.setStyle(
        TableStyle(
            table_commands
        )
    )

    elements.append(
        loan_table
    )

    # ======================================================
    # FOOTER SPACE
    # ======================================================

    elements.append(
        Spacer(
            1,
            5 * mm
        )
    )

    # ======================================================
    # FOOTER
    # ======================================================

    footer = Table(
        [
            [
                Paragraph(
                    "Wisconsin Libraries • Active Loan Management System",
                    footer_style
                )
            ]
        ],
        colWidths=[270 * mm],
    )

    footer.setStyle(
        TableStyle([
            (
                "LINEABOVE",
                (0, 0),
                (-1, -1),
                0.5,
                BORDER,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
        ])
    )

    elements.append(
        footer
    )

    # ======================================================
    # BUILD PDF
    # ======================================================

    doc.build(
        elements
    )

    # ======================================================
    # RESPONSE
    # ======================================================

    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'attachment; '
        'filename="wisconsin_active_loans_report.pdf"'
    )

    return response
# =====================================================
# ACTIVE LOANS
# =====================================================

from datetime import date

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render

from Library.models import BorrowTransaction


DUE_SOON_THRESHOLD_DAYS = 3


@staff_member_required
def active_loans(request):
    """
    Every currently-issued book, library-wide.

    Search is performed BEFORE pagination so that live search
    can find a loan even if that loan was originally on another
    page.
    """

    # =====================================================
    # SEARCH
    # =====================================================

    search_query = request.GET.get(
        "q",
        ""
    ).strip()

    today = date.today()
    # =====================================================
    # BASE QUERYSET
    # =====================================================

    transactions = (
        BorrowTransaction.objects
        .select_related(
            "copy",
            "copy__resource",
            "copy__resource__library",
            "library_user",
            "library_user__user",
        )
        .filter(
            Q(status__in=["ISSUED", "OVERDUE"])
            |
            Q(
                status="RETURNED",
                return_date=today,
            )
        )
        .order_by("due_date")
    )

    # =====================================================
    # SEARCH
    #
    # IMPORTANT:
    # Search happens BEFORE pagination.
    # =====================================================

    if search_query:

        transactions = transactions.filter(

            Q(
                copy__resource__title__icontains=search_query
            )

            |

            Q(
                copy__resource__author__icontains=search_query
            )

            |

            Q(
                library_user__user__first_name__icontains=search_query
            )

            |

            Q(
                library_user__user__last_name__icontains=search_query
            )

            |

            Q(
                library_user__user__username__icontains=search_query
            )

            |

            Q(
                copy__barcode__icontains=search_query
            )

        ).distinct()


    # =====================================================
    # COMPUTED LOANS
    # =====================================================

    today = date.today()

    loans = []


    for txn in transactions:

        # =====================================================
        # RETURNED BOOK
        # =====================================================

        if txn.status == "RETURNED":

            loans.append({
                "transaction": txn,
                "computed_status": "RETURNED",
                "days_left": 0,
                "days_overdue": 0,
            })

            continue


        # =====================================================
        # ACTIVE / OVERDUE BOOK
        # =====================================================

        days_left = (
            txn.due_date - today
        ).days


        if days_left < 0:

            computed_status = "OVERDUE"

        elif days_left <= DUE_SOON_THRESHOLD_DAYS:

            computed_status = "DUE_SOON"

        else:

            computed_status = "ACTIVE"


        loans.append({
            "transaction": txn,
            "computed_status": computed_status,
            "days_left": days_left,
            "days_overdue": (
                abs(days_left)
                if days_left < 0
                else 0
            ),
        })


    # =====================================================
    # STATISTICS
    #
    # These are calculated from the COMPLETE SEARCH RESULT,
    # before pagination.
    # =====================================================

    total_active = sum(
        1
        for loan in loans
        if loan["computed_status"] != "RETURNED"
    )


    overdue_count = sum(

        1

        for loan in loans

        if loan["computed_status"] == "OVERDUE"

    )


    due_soon_count = sum(

        1

        for loan in loans

        if loan["computed_status"] == "DUE_SOON"

    )


    # =====================================================
    # RETURNED TODAY
    # =====================================================

    returned_today_count = (
        BorrowTransaction.objects

        .filter(
            status="RETURNED",
            return_date=today,
        )

        .count()
    )

    returned_today = (
        BorrowTransaction.objects
        .select_related(
            "copy",
            "copy__resource",
            "library_user",
            "library_user__user",
        )
        .filter(
            status="RETURNED",
            return_date=today,
        )
        .order_by("-return_date", "-id")
    )


    # =====================================================
    # PAGINATION
    #
    # Search has already happened.
    # Therefore pagination only paginates the matching
    # results.
    # =====================================================

    paginator = Paginator(
        loans,
        5
    )


    page_number = request.GET.get(
        "page",
        1
    )


    page_obj = paginator.get_page(
        page_number
    )


    # =====================================================
    # AJAX RESPONSE
    #
    # Used by live search.
    # =====================================================

    if request.headers.get(
        "X-Requested-With"
    ) == "XMLHttpRequest":

        loan_data = []


        for loan in page_obj:

            txn = loan["transaction"]

            user = (
                txn.library_user.user
            )


            # -------------------------------------------------
            # USER NAME
            # -------------------------------------------------

            full_name = (
                user.get_full_name().strip()
            )


            if not full_name:

                full_name = (
                    user.username
                )


            # -------------------------------------------------
            # USER INITIALS
            # -------------------------------------------------

            initials = ""


            if user.first_name:

                initials += (
                    user.first_name[0]
                )


            if user.last_name:

                initials += (
                    user.last_name[0]
                )


            if not initials:

                initials = (
                    user.username[:1]
                    if user.username
                    else "U"
                )


            # -------------------------------------------------
            # BOOK
            # -------------------------------------------------

            resource = (
                txn.copy.resource
                if txn.copy
                else None
            )


            # -------------------------------------------------
            # APPEND
            # -------------------------------------------------

            loan_data.append({

                "id": txn.id,

                "full_name": full_name,

                "initials": initials.upper(),

                "user_type": (
                    txn.library_user
                    .get_user_type_display()
                ),

                "book": (
                    resource.title
                    if resource
                    else ""
                ),

                "author": (
                    resource.author
                    if resource
                    else ""
                ),

                "barcode": (
                    txn.copy.barcode
                    if txn.copy
                    else ""
                ),

                "issue_date": (
                    txn.issue_date.strftime(
                        "%b %d, %Y"
                    )
                    if txn.issue_date
                    else ""
                ),

                "due_date": (
                    txn.due_date.strftime(
                        "%b %d, %Y"
                    )
                    if txn.due_date
                    else ""
                ),

                "computed_status": (
                    loan["computed_status"]
                ),

                "days_left": (
                    loan["days_left"]
                ),

                "days_overdue": (
                    loan["days_overdue"]
                ),

            })


        # -------------------------------------------------
        # AJAX JSON
        # -------------------------------------------------

        return JsonResponse({

            "loans": loan_data,

            "page": page_obj.number,

            "pages": paginator.num_pages,

            "total": paginator.count,

            "start": (
                page_obj.start_index()
                if paginator.count
                else 0
            ),

            "end": (
                page_obj.end_index()
                if paginator.count
                else 0
            ),

            "has_previous": (
                page_obj.has_previous()
            ),

            "has_next": (
                page_obj.has_next()
            ),

            "previous_page": (
                page_obj.previous_page_number()
                if page_obj.has_previous()
                else None
            ),

            "next_page": (
                page_obj.next_page_number()
                if page_obj.has_next()
                else None
            ),


        })


    # =====================================================
    # NORMAL PAGE
    # =====================================================

    context = {

        # -------------------------------------------------
        # PAGINATED LOANS
        # -------------------------------------------------

        "loans": page_obj,

        "page_obj": page_obj,


        # -------------------------------------------------
        # STATISTICS
        # -------------------------------------------------

        "total_active": total_active,

        "overdue_count": overdue_count,

        "due_soon_count": due_soon_count,

        "returned_today_count": (
            returned_today_count
        ),
        "returned_today": returned_today,


        # -------------------------------------------------
        # SEARCH
        # -------------------------------------------------

        "search_query": search_query,

    }


    return render(

        request,

        "library_admin/nancy/active_loans.html",

        context

    )


# =====================================================
# library_admin/views.py — active_loans_view.py
# =====================================================

from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from Library.models import BorrowTransaction, Fine, ResourceCopy


DEFAULT_FINE_PER_DAY = Decimal("5.00")

@staff_member_required
def mark_returned(request, transaction_id):
    """
    Marks a BorrowTransaction as returned, frees up the copy,
    restores it to available_copies, and finalizes any fine
    for late return using the real return date.
    """

    # =====================================================
    # ONLY ALLOW POST
    # =====================================================

    if request.method != "POST":
        return redirect("active_loans")

    try:

        # =====================================================
        # DATABASE TRANSACTION
        # =====================================================

        with transaction.atomic():

            # -------------------------------------------------
            # GET TRANSACTION
            # -------------------------------------------------

            txn = get_object_or_404(
                BorrowTransaction.objects.select_for_update(),
                id=transaction_id,
                status__in=["ISSUED", "OVERDUE"],
            )

            today = date.today()

            # =====================================================
            # AUDIT — BEFORE DATA
            # =====================================================

            before_data = {
                "transaction_status": txn.status,
                "return_date": (
                    txn.return_date.isoformat()
                    if txn.return_date
                    else None
                ),
                "copy_status": txn.copy.status,
                "available_copies": (
                    txn.copy.resource.available_copies
                ),
            }

            # =====================================================
            # MARK TRANSACTION AS RETURNED
            # =====================================================

            txn.return_date = today
            txn.status = "RETURNED"
            txn.save()

            # =====================================================
            # FINE DEFAULT VALUES
            # =====================================================

            fine_amount = None
            fine_status = None

            # =====================================================
            # FINE CHECK
            # =====================================================

            days_late = (
                today - txn.due_date
            ).days

            if days_late > 0:

                try:
                    fine = txn.fine

                except Fine.DoesNotExist:
                    fine = None

                # ---------------------------------------------
                # CREATE FINE
                # ---------------------------------------------

                if fine is None:

                    fine = Fine.objects.create(
                        transaction=txn,
                        fine_per_day=DEFAULT_FINE_PER_DAY,
                        overdue_days=days_late,
                        fine_amount=(
                            DEFAULT_FINE_PER_DAY * days_late
                        ),
                        payment_status="UNPAID",
                    )

                # ---------------------------------------------
                # UPDATE EXISTING UNPAID FINE
                # ---------------------------------------------

                elif fine.payment_status == "UNPAID":

                    fine.overdue_days = days_late

                    fine.fine_amount = (
                        fine.fine_per_day * days_late
                    )

                    fine.save()

                # ---------------------------------------------
                # CAPTURE FINE DETAILS
                # ---------------------------------------------

                fine_amount = str(
                    fine.fine_amount
                )

                fine_status = (
                    fine.payment_status
                )

            # =====================================================
            # MAKE COPY AVAILABLE
            # =====================================================

            copy = txn.copy

            copy.status = "AVAILABLE"

            copy.save()

            # =====================================================
            # RESTORE RESOURCE AVAILABLE COPIES
            # =====================================================

            resource = copy.resource

            if (
                resource.available_copies
                < resource.total_copies
            ):

                resource.available_copies += 1

                resource.save()

            # =====================================================
            # UPDATE RELATED BORROW REQUEST
            # =====================================================

            if txn.borrow_request:

                txn.borrow_request.status = "RETURNED"

                txn.borrow_request.save()

    # =====================================================
    # ERROR
    # =====================================================

    except Exception:

        messages.error(
            request,
            "Something went wrong while processing the return. "
            "Please try again."
        )

        return redirect("active_loans")

    # =====================================================
    # AUDIT — AFTER DATA
    # =====================================================

    after_data = {
        "transaction_status": txn.status,
        "return_date": (
            txn.return_date.isoformat()
            if txn.return_date
            else None
        ),
        "copy_status": copy.status,
        "available_copies": (
            resource.available_copies
        ),
        "days_late": max(days_late, 0),
        "fine_amount": fine_amount,
        "fine_status": fine_status,
    }

    # =====================================================
    # AUDIT LOG — RETURN
    # =====================================================

    AuditLogger.log(
        request=request,
        action="RETURN",
        module="LibraryAdmin",
        object_type="BorrowTransaction",
        object_id=txn.id,
        description=(
            f'Returned "{copy.resource.title}" '
            f'(Copy: {copy.barcode}) from '
            f'{txn.library_user.user.get_full_name() or txn.library_user.user.username}.'
        ),
        before_data=before_data,
        after_data=after_data,
        status="SUCCESS",
    )

    # =====================================================
    # SUCCESS MESSAGE
    # =====================================================

    if days_late > 0:

        messages.success(
            request,
            f'"{copy.resource.title}" marked as returned — '
            f'{days_late} day{"s" if days_late != 1 else ""} late.'
        )

    else:

        messages.success(
            request,
            f'"{copy.resource.title}" marked as returned.'
        )

    return redirect("active_loans")
  
  
    
# notifications
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from Staff.models import Notification

# =========================================================
# LIBRARY ADMIN NOTIFICATIONS
# =========================================================

@login_required
def library_notifications(request):
    """
    Returns the latest notifications belonging only to
    the currently logged-in Library Admin.
    """

    notifications = (
        Notification.objects
        .filter(user=request.user)
        .order_by("-created_at")[:10]
    )

    unread_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    notification_list = []

    for notification in notifications:

        notification_list.append({
            "id": notification.id,
            "title": notification.title,
            "message": notification.message or "",
            "notification_type": notification.notification_type,
            "link": notification.link or "",
            "is_read": notification.is_read,
            "created_at": notification.created_at.isoformat(),
        })

    return JsonResponse({
        "notifications": notification_list,
        "unread_count": unread_count,
    })


@login_required
@require_POST
def library_notification_mark_read(request, notification_id):
    """
    Marks one notification as read.

    Only the notification belonging to the currently
    logged-in user can be modified.
    """

    notification = Notification.objects.filter(
        id=notification_id,
        user=request.user,
    ).first()

    if notification is None:
        return JsonResponse(
            {
                "success": False,
                "message": "Notification not found."
            },
            status=404,
        )

    notification.is_read = True
    notification.save(update_fields=["is_read"])

    unread_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    return JsonResponse({
        "success": True,
        "unread_count": unread_count,
    })
    
    
    # =========================================================
# MARK ALL LIBRARY ADMIN NOTIFICATIONS AS READ
# =========================================================

@login_required
@require_POST
def library_notifications_mark_all_read(request):
    """
    Marks all unread notifications belonging to
    the currently logged-in Library Admin as read.
    """

    Notification.objects.filter(
        user=request.user,
        is_read=False,
    ).update(
        is_read=True
    )

    return JsonResponse({
        "success": True,
        "unread_count": 0,
    })
    
    
# =========================================================
# ALL LIBRARY ADMIN NOTIFICATIONS PAGE
# =========================================================

@login_required
def library_all_notifications(request):

    notifications = (
        Notification.objects
        .filter(user=request.user)
        .order_by("-created_at")
    )

    paginator = Paginator(
        notifications,
        10
    )

    page_number = request.GET.get(
        "page",
        1
    )

    page_obj = paginator.get_page(
        page_number
    )

    unread_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    return render(
        request,
        "library_admin/nancy/all_notifications.html",
        {
            "notifications": page_obj,
            "page_obj": page_obj,
            "unread_count": unread_count,
        }
    )
    
    
# fine management 

from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import render
from django.http import JsonResponse
from django.template.loader import render_to_string
from Library.models import Fine

@staff_member_required
def fine_management(request):

    fines = (
        Fine.objects
        .select_related(
            "transaction",
            "transaction__library_user",
            "transaction__library_user__user",
            "transaction__copy",
            "transaction__copy__resource",
        )
        .order_by("-created_at")
    )

    search = request.GET.get("search", "").strip()

    if search:
       fines = fines.filter(
        Q(transaction__library_user__user__first_name__icontains=search)
        | Q(transaction__library_user__user__last_name__icontains=search)
        | Q(transaction__library_user__user__username__icontains=search)
        | Q(transaction__copy__resource__title__icontains=search)
        | Q(payment_transaction_id__icontains=search)
        | Q(receipt_number__icontains=search)
    )
    payment_status = request.GET.get("status")

    if payment_status:
        fines = fines.filter(payment_status=payment_status)

    payment_method = request.GET.get("method")

    if payment_method:
        fines = fines.filter(payment_method=payment_method)

    start_date = request.GET.get("start_date")

    end_date = request.GET.get("end_date")

    if start_date:
        fines = fines.filter(created_at__date__gte=start_date)

    if end_date:
        fines = fines.filter(created_at__date__lte=end_date)

    total_fines = (
        Fine.objects.aggregate(total=Sum("fine_amount"))["total"]
        or Decimal("0.00")
    )

    pending_fines = (
        Fine.objects.filter(payment_status="UNPAID")
        .aggregate(total=Sum("fine_amount"))["total"]
        or Decimal("0.00")
    )

    collected_fines = (
        Fine.objects.filter(payment_status="PAID")
        .aggregate(total=Sum("amount_received"))["total"]
        or Decimal("0.00")
    )

    overdue_books = Fine.objects.filter(
        payment_status="UNPAID"
    ).count()

    paginator = Paginator(fines, 5)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)


    context = {

        "page_obj": page_obj,

        "search": search,

        "payment_status": payment_status,

        "payment_method": payment_method,

        "start_date": start_date,

        "end_date": end_date,

        "total_fines": total_fines,

        "pending_fines": pending_fines,

        "collected_fines": collected_fines,

        "overdue_books": overdue_books,

    }

    # AJAX Request

    if request.headers.get("x-requested-with") == "XMLHttpRequest":

        html = render_to_string(

           "library_admin/partials/fine_table.html",

           context,

          request=request,

        )

        return JsonResponse({

        "html": html

        })

    return render(
        request,
        "library_admin/fine_management.html",
        context,
    )


from django.shortcuts import get_object_or_404, render

from Library.models import Fine
@staff_member_required
def fine_details(request, fine_id):

    fine = get_object_or_404(
        Fine.objects.select_related(
            "transaction",
            "transaction__library_user",
            "transaction__library_user__user",
            "transaction__copy",
            "transaction__copy__resource",
        ),
        id=fine_id
    )

    return render(
        request,
        "library_admin/fine_details.html",
        {
            "fine": fine,
        }
    )

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from Library.models import Fine


@staff_member_required
def collect_fine(request, fine_id):

    fine = get_object_or_404(
        Fine.objects.select_related(
            "transaction",
            "transaction__library_user",
            "transaction__library_user__user",
            "transaction__copy",
            "transaction__copy__resource",
        ),
        id=fine_id,
    )

    # =========================================================
    # ALREADY PAID
    # =========================================================

    if fine.payment_status == "PAID":

        messages.warning(
            request,
            "This fine has already been paid."
        )

        return redirect(
            "fine_details",
            fine_id=fine.id
        )

    # =========================================================
    # CURRENT DATE / TIME
    # =========================================================

    now = timezone.localtime()

    # =========================================================
    # RECEIPT NUMBER
    # =========================================================

    receipt_number = (
        f"REC-{now.strftime('%Y%m%d')}-{fine.id:05d}"
    )

    # =========================================================
    # GET
    # =========================================================

    if request.method == "GET":

        context = {
            "fine": fine,
            "receipt_number": receipt_number,
            "payment_date": now.strftime(
                "%Y-%m-%dT%H:%M"
            ),
        }

        return render(
            request,
            "library_admin/collect_fine.html",
            context
        )

    # =========================================================
    # POST
    # =========================================================

    payment_method = request.POST.get(
        "payment_method",
        ""
    ).strip().upper()

    amount_value = request.POST.get(
        "amount_received",
        ""
    ).strip()

    transaction_id = request.POST.get(
        "payment_transaction_id",
        ""
    ).strip()

    # =========================================================
    # VALID PAYMENT METHODS
    # =========================================================

    allowed_methods = {
        "CASH",
        "CARD",
        "UPI",
        "BANK",
    }

    if payment_method not in allowed_methods:

        messages.error(
            request,
            "Please select a valid payment method."
        )

        return redirect(
            "collect_fine",
            fine_id=fine.id
        )

    # =========================================================
    # AMOUNT VALIDATION
    # =========================================================

    try:

        amount_received = Decimal(
            amount_value
        )

    except (InvalidOperation, TypeError):

        messages.error(
            request,
            "Please enter a valid amount."
        )

        return redirect(
            "collect_fine",
            fine_id=fine.id
        )

    if amount_received <= Decimal("0.00"):

        messages.error(
            request,
            "Payment amount must be greater than zero."
        )

        return redirect(
            "collect_fine",
            fine_id=fine.id
        )

    if amount_received > fine.fine_amount:

        messages.error(
            request,
            "Payment amount cannot exceed the outstanding fine."
        )

        return redirect(
            "collect_fine",
            fine_id=fine.id
        )

    # =========================================================
    # TRANSACTION ID
    # =========================================================

    if payment_method != "CASH" and not transaction_id:

        messages.error(
            request,
            "Transaction ID is required for this payment method."
        )

        return redirect(
            "collect_fine",
            fine_id=fine.id
        )

    if payment_method == "CASH":

        transaction_id = ""

    # =========================================================
    # SAVE PAYMENT
    # =========================================================

    with transaction.atomic():

        # Refresh the latest database value
        fine.refresh_from_db()

        # Check again
        if fine.payment_status == "PAID":

            messages.warning(
                request,
                "This fine has already been paid."
            )

            return redirect(
                "fine_details",
                fine_id=fine.id
            )

        # =====================================================
        # PAYMENT DETAILS
        # =====================================================

        fine.payment_status = "PAID"

        fine.payment_method = payment_method

        fine.amount_received = amount_received

        fine.payment_transaction_id = (
            transaction_id or None
        )

        fine.receipt_number = receipt_number

        # =====================================================
        # IMPORTANT
        # =====================================================
        # Your Fine model uses paid_date.
        # Therefore save paid_date directly.

        fine.paid_date = timezone.now()

        # =====================================================
        # ADMIN WHO COLLECTED THE MONEY
        # =====================================================

        fine.collected_by = request.user

        # =====================================================
        # SAVE
        # =====================================================

        fine.save(
            update_fields=[
                "payment_status",
                "payment_method",
                "amount_received",
                "payment_transaction_id",
                "receipt_number",
                "paid_date",
                "collected_by",
                "updated_at",
            ]
        )

    # =========================================================
    # SUCCESS
    # =========================================================

    messages.success(
        request,
        f"Payment of ₹{amount_received:.2f} collected successfully."
    )

    return redirect(
        "fine_details",
        fine_id=fine.id
    )

# ==========================================================
# PROFESSIONAL WISCONSIN LIBRARIES - FINE REPORT PDF
# ==========================================================

from io import BytesIO
from decimal import Decimal

from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone

from django.contrib.staticfiles.finders import find

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import mm

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)

@staff_member_required
def export_fines_pdf(request):

    # ======================================================
    # WISCONSIN COLORS
    # ======================================================

    WISCONSIN_RED = colors.HexColor("#C5050C")

    DARK_RED = colors.HexColor("#9E0006")

    WISCONSIN_NAVY = colors.HexColor("#13294B")

    DARK_NAVY = colors.HexColor("#0B1F3A")

    WHITE = colors.white

    BLACK = colors.HexColor("#1A1A1A")

    TEXT = colors.HexColor("#273142")

    MUTED = colors.HexColor("#667085")

    BORDER = colors.HexColor("#D5D9E0")

    LIGHT_GRAY = colors.HexColor("#F7F8FA")

    VERY_LIGHT_GRAY = colors.HexColor("#FBFBFC")


    # ======================================================
    # GET FILTERS
    # ======================================================

    search = request.GET.get(
        "search",
        ""
    ).strip()

    payment_status = request.GET.get(
        "status",
        ""
    ).strip()

    payment_method = request.GET.get(
        "method",
        ""
    ).strip()

    start_date = request.GET.get(
        "start_date",
        ""
    ).strip()

    end_date = request.GET.get(
        "end_date",
        ""
    ).strip()


    # ======================================================
    # GET FINES
    # ======================================================

    fines = (
        Fine.objects
        .select_related(
            "transaction",
            "transaction__library_user",
            "transaction__library_user__user",
            "transaction__copy",
            "transaction__copy__resource",
        )
        .order_by("-created_at")
    )


    # ======================================================
    # SEARCH FILTER
    # ======================================================

    if search:

        fines = fines.filter(

            Q(
                transaction__library_user__user__first_name__icontains=search
            )

            |

            Q(
                transaction__library_user__user__last_name__icontains=search
            )

            |

            Q(
                transaction__library_user__user__email__icontains=search
            )

            |

            Q(
                transaction__copy__resource__title__icontains=search
            )

            |

            Q(
                transaction__copy__resource__author__icontains=search
            )

            |

            Q(
                payment_transaction_id__icontains=search
            )

            |

            Q(
                receipt_number__icontains=search
            )

        )


    # ======================================================
    # STATUS FILTER
    # ======================================================

    if payment_status:

        fines = fines.filter(
            payment_status=payment_status
        )


    # ======================================================
    # PAYMENT METHOD FILTER
    # ======================================================

    if payment_method:

        fines = fines.filter(
            payment_method=payment_method
        )


    # ======================================================
    # DATE FILTER
    # ======================================================

    if start_date:

        fines = fines.filter(
            created_at__date__gte=start_date
        )


    if end_date:

        fines = fines.filter(
            created_at__date__lte=end_date
        )


    # ======================================================
    # EVALUATE QUERYSET
    # ======================================================

    fines = list(fines)


    # ======================================================
    # GENERATED DATE
    # ======================================================

    generated_at = timezone.localtime().strftime(
        "%d %b %Y, %I:%M %p"
    )


    # ======================================================
    # PDF BUFFER
    # ======================================================

    buffer = BytesIO()


    # ======================================================
    # A4 LANDSCAPE
    # ======================================================

    doc = SimpleDocTemplate(

        buffer,

        pagesize=landscape(A4),

        leftMargin=13 * mm,

        rightMargin=13 * mm,

        topMargin=12 * mm,

        bottomMargin=14 * mm,

        title="Wisconsin Libraries - Fine Management Report",

        author="Wisconsin Libraries",

    )


    # ======================================================
    # STYLES
    # ======================================================

    styles = getSampleStyleSheet()


    # ======================================================
    # BRAND NAME
    # ======================================================

    brand_style = ParagraphStyle(

        "BrandStyle",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=15,

        leading=17,

        textColor=WISCONSIN_RED,

        alignment=TA_LEFT,

    )


    # ======================================================
    # LIBRARIES TEXT
    # ======================================================

    libraries_style = ParagraphStyle(

        "LibrariesStyle",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=7,

        leading=9,

        textColor=WISCONSIN_NAVY,

        alignment=TA_LEFT,

        letterSpacing=1.5,

    )


    # ======================================================
    # REPORT TITLE
    # ======================================================

    title_style = ParagraphStyle(

        "TitleStyle",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=17,

        leading=20,

        textColor=DARK_NAVY,

        alignment=TA_CENTER,

    )


    # ======================================================
    # SUBTITLE
    # ======================================================

    subtitle_style = ParagraphStyle(

        "SubtitleStyle",

        parent=styles["Normal"],

        fontName="Helvetica",

        fontSize=7.5,

        leading=10,

        textColor=MUTED,

        alignment=TA_CENTER,

    )


    # ======================================================
    # GENERATED STYLE
    # ======================================================

    generated_style = ParagraphStyle(

        "GeneratedStyle",

        parent=styles["Normal"],

        fontName="Helvetica",

        fontSize=7,

        leading=10,

        textColor=MUTED,

        alignment=TA_RIGHT,

    )


    # ======================================================
    # GENERATED VALUE
    # ======================================================

    generated_value_style = ParagraphStyle(

        "GeneratedValueStyle",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=8,

        leading=10,

        textColor=DARK_NAVY,

        alignment=TA_RIGHT,

    )


    # ======================================================
    # TABLE TEXT
    # ======================================================

    table_style = ParagraphStyle(

        "TableStyle",

        parent=styles["Normal"],

        fontName="Helvetica",

        fontSize=6.6,

        leading=8,

        textColor=TEXT,

        alignment=TA_LEFT,

    )


    # ======================================================
    # TABLE CENTER
    # ======================================================

    table_center_style = ParagraphStyle(

        "TableCenterStyle",

        parent=table_style,

        alignment=TA_CENTER,

    )


    # ======================================================
    # TABLE RIGHT
    # ======================================================

    table_right_style = ParagraphStyle(

        "TableRightStyle",

        parent=table_style,

        alignment=TA_RIGHT,

    )


    # ======================================================
    # TABLE HEADER
    # ======================================================

    table_header_style = ParagraphStyle(

        "TableHeaderStyle",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=6.2,

        leading=7,

        textColor=WHITE,

        alignment=TA_LEFT,

    )


    table_header_center_style = ParagraphStyle(

        "TableHeaderCenterStyle",

        parent=table_header_style,

        alignment=TA_CENTER,

    )


    # ======================================================
    # FOOTER STYLE
    # ======================================================

    footer_style = ParagraphStyle(

        "FooterStyle",

        parent=styles["Normal"],

        fontName="Helvetica",

        fontSize=6.5,

        leading=8,

        textColor=MUTED,

        alignment=TA_CENTER,

    )


    # ======================================================
    # PDF ELEMENTS
    # ======================================================

    elements = []


    # ======================================================
    # WISCONSIN LOGO
    # ======================================================

    logo_path = find(
        "images/navina/W-logo.png"
    )


    if logo_path:

        logo = Image(

            logo_path,
              width=35 * mm,
              height=25 * mm,


        )

    else:

        # Fallback if logo is not found

        logo = Table(

            [

                [

                    Paragraph(

                        "<b>W</b>",

                        ParagraphStyle(

                            "FallbackLogo",

                            parent=styles["Normal"],

                            fontName="Helvetica-Bold",

                            fontSize=18,

                            textColor=WHITE,

                            alignment=TA_CENTER,

                        )

                    )

                ]

            ],

            colWidths=[18 * mm],

            rowHeights=[18 * mm],

        )

        logo.setStyle(

            TableStyle([

                (

                    "BACKGROUND",

                    (0, 0),

                    (-1, -1),

                    DARK_NAVY,

                ),

                (

                    "BOX",

                    (0, 0),

                    (-1, -1),

                    1,

                    DARK_NAVY,

                ),

            ])

        )


    # ======================================================
    # BRAND TEXT
    # ======================================================

    brand_text = Table(

        [

            [

                Paragraph(
                    "WISCONSIN",
                    brand_style
                )

            ],

            [

                Paragraph(
                    "L I B R A R I E S",
                    libraries_style
                )

            ],

        ],

        colWidths=[47 * mm],

    )


    brand_text.setStyle(

        TableStyle([

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

        ])

    )


    # ======================================================
    # BRAND BLOCK
    # ======================================================

    brand_block = Table(

        [

            [

                logo,

                brand_text

            ]

        ],

        colWidths=[27 * mm, 47 * mm],

    )


    brand_block.setStyle(

        TableStyle([

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

        ])

    )


    # ======================================================
    # CENTER REPORT TITLE
    # ======================================================

    report_title = Table(

        [

            [

                Paragraph(
                    "FINE MANAGEMENT REPORT",
                    title_style
                )

            ],

            [

                Paragraph(
                    "Library Fine Collection & Management",
                    subtitle_style
                )

            ],

        ],

        colWidths=[135 * mm],

    )


    report_title.setStyle(

        TableStyle([

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

        ])

    )


    # ======================================================
    # GENERATED BOX
    # ======================================================

    generated_block = Table(

        [

            [

                Paragraph(
                    "GENERATED",
                    generated_style
                )

            ],

            [

                Paragraph(
                    generated_at,
                    generated_value_style
                )

            ],

        ],

        colWidths=[55 * mm],

    )


    generated_block.setStyle(

        TableStyle([

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

        ])

    )


    # ======================================================
    # MAIN HEADER
    # ======================================================

    header = Table(

        [

            [

                brand_block,

                report_title,

                generated_block

            ]

        ],

        colWidths=[70 * mm, 137 * mm, 70 * mm],

    )


    header.setStyle(

        TableStyle([

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

        ])

    )


    elements.append(
        header
    )


    # ======================================================
    # RED ACCENT LINE
    # ======================================================

    elements.append(
        Spacer(
            1,
            4 * mm
        )
    )

    # ======================================================
    # WISCONSIN RED DIVIDER
    # ======================================================

    accent = Table(

        [
           [""]
        ],

        colWidths=[270 * mm],

        rowHeights=[1.3 * mm],

    )

    accent.setStyle(

        TableStyle([

          (
            "BACKGROUND",
            (0, 0),
            (-1, -1),
            DARK_NAVY,
          ),

          (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            0,
           ),

           (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            0,
           ),

           (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            0,
           ),

           (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            0,
           ),

        ])

    )
    elements.append(
        accent
    )


    elements.append(
        Spacer(
            1,
            5 * mm
        )
    )


    # ======================================================
    # FILTER INFORMATION
    # ======================================================

    filter_values = []


    if search:

        filter_values.append(
            f"Search: {search}"
        )


    if payment_status:

        filter_values.append(
            f"Status: {payment_status}"
        )


    if payment_method:

        filter_values.append(
            f"Payment Method: {payment_method}"
        )


    if start_date:

        filter_values.append(
            f"From: {start_date}"
        )


    if end_date:

        filter_values.append(
            f"To: {end_date}"
        )


    if filter_values:

        filter_text = "   |   ".join(
            filter_values
        )

    else:

        filter_text = "All Fine Records"


    filter_style = ParagraphStyle(

        "FilterStyle",

        parent=styles["Normal"],

        fontName="Helvetica",

        fontSize=7,

        leading=9,

        textColor=MUTED,

        alignment=TA_LEFT,

    )


    elements.append(

        Paragraph(
            filter_text,
            filter_style
        )

    )


    elements.append(
        Spacer(
            1,
            4 * mm
        )
    )


    # ======================================================
    # TABLE DATA
    # ======================================================

    table_data = [

        [

            Paragraph(
                "FINE ID",
                table_header_center_style
            ),

            Paragraph(
                "STUDENT",
                table_header_style
            ),

            Paragraph(
                "BOOK",
                table_header_style
            ),

            Paragraph(
                "ISSUE",
                table_header_center_style
            ),

            Paragraph(
                "DUE",
                table_header_center_style
            ),

            Paragraph(
                "RETURN",
                table_header_center_style
            ),

            Paragraph(
                "OVERDUE",
                table_header_center_style
            ),

            Paragraph(
                "FINE / DAY",
                table_header_center_style
            ),

            Paragraph(
                "TOTAL FINE",
                table_header_center_style
            ),

            Paragraph(
                "STATUS",
                table_header_center_style
            ),

            Paragraph(
                "PAYMENT",
                table_header_center_style
            ),

        ]

    ]


    # ======================================================
    # ADD FINE RECORDS
    # ======================================================

    for fine in fines:

        transaction = fine.transaction

        library_user = transaction.library_user

        user = library_user.user

        resource = transaction.copy.resource


        # --------------------------------------------------
        # STUDENT
        # --------------------------------------------------

        student_name = (

            user.get_full_name()

            or user.username

            or "Unknown"

        )


        student_email = (
            user.email
            or ""
        )


        student_text = (

            f"<b>{student_name}</b>"

            f"<br/>"

            f"<font color='#667085'>"
            f"{student_email}"
            f"</font>"

        )


        # --------------------------------------------------
        # BOOK
        # --------------------------------------------------

        book_title = (
            resource.title
            or "Unknown Book"
        )


        book_author = (
            resource.author
            or "Unknown Author"
        )


        book_text = (

            f"<b>{book_title}</b>"

            f"<br/>"

            f"<font color='#667085'>"
            f"{book_author}"
            f"</font>"

        )


        # --------------------------------------------------
        # DATES
        # --------------------------------------------------

        issue_date = (

            transaction.issue_date.strftime(
                "%d %b %Y"
            )

            if transaction.issue_date

            else "-"

        )


        due_date = (

            transaction.due_date.strftime(
                "%d %b %Y"
            )

            if transaction.due_date

            else "-"

        )


        return_date = (

            transaction.return_date.strftime(
                "%d %b %Y"
            )

            if transaction.return_date

            else "-"

        )


        # --------------------------------------------------
        # OVERDUE
        # --------------------------------------------------

        overdue = (

            f"{fine.overdue_days} days"

            if fine.overdue_days

            else "On Time"

        )


        # --------------------------------------------------
        # FINE PER DAY
        # --------------------------------------------------

        fine_per_day = (

            f"${fine.fine_per_day:.2f}"

            if fine.fine_per_day is not None

            else "-"

        )


        # --------------------------------------------------
        # TOTAL FINE
        # --------------------------------------------------

        fine_amount = (

            f"${fine.fine_amount:.2f}"

            if fine.fine_amount is not None

            else "$0.00"

        )


        # --------------------------------------------------
        # STATUS
        # --------------------------------------------------

        if fine.payment_status == "PAID":

            status_text = (

                "<b>"
                "<font color='#16834A'>"
                "PAID"
                "</font>"
                "</b>"

            )

            payment_text = (
                fine.payment_method
                or "-"
            )

        else:

            status_text = (

                "<b>"
                "<font color='#C5050C'>"
                "UNPAID"
                "</font>"
                "</b>"

            )

            payment_text = "Outstanding"


        # ==================================================
        # ADD ROW
        # ==================================================

        table_data.append(

            [

                Paragraph(
                    f"FIN-{fine.id:05d}",
                    table_center_style
                ),

                Paragraph(
                    student_text,
                    table_style
                ),

                Paragraph(
                    book_text,
                    table_style
                ),

                Paragraph(
                    issue_date,
                    table_center_style
                ),

                Paragraph(
                    due_date,
                    table_center_style
                ),

                Paragraph(
                    return_date,
                    table_center_style
                ),

                Paragraph(
                    overdue,
                    table_center_style
                ),

                Paragraph(
                    fine_per_day,
                    table_right_style
                ),

                Paragraph(
                    f"<b>{fine_amount}</b>",
                    table_right_style
                ),

                Paragraph(
                    status_text,
                    table_center_style
                ),

                Paragraph(
                    payment_text,
                    table_center_style
                ),

            ]

        )


    # ======================================================
    # EMPTY DATA
    # ======================================================

    if not fines:

        table_data.append(

            [

                Paragraph(
                    "No fine records found for the selected filters.",
                    ParagraphStyle(
                        "EmptyStyle",
                        parent=table_style,
                        alignment=TA_CENTER,
                        textColor=MUTED,
                    )
                ),

                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",

            ]

        )


    # ======================================================
    # PROFESSIONAL CENTERED TABLE
    # ======================================================

    fine_table = Table(

        table_data,

        # TOTAL = 270 MM
        colWidths=[

            17 * mm,   # Fine ID

            38 * mm,   # Student

            44 * mm,   # Book

            21 * mm,   # Issue

            21 * mm,   # Due

            23 * mm,   # Return

            19 * mm,   # Overdue

            19 * mm,   # Fine/day

            22 * mm,   # Total fine

            20 * mm,   # Status

            26 * mm,   # Payment

        ],

        repeatRows=1,

        hAlign="CENTER",

    )


    # ======================================================
    # TABLE STYLE
    # ======================================================

    table_commands = [

        # --------------------------------------------------
        # HEADER
        # --------------------------------------------------

        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            WISCONSIN_NAVY,
        ),

        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            WHITE,
        ),

        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE",
        ),

        # --------------------------------------------------
        # OUTER BORDER
        # --------------------------------------------------

        (
            "BOX",
            (0, 0),
            (-1, -1),
            0.8,
            WISCONSIN_NAVY,
        ),

        # --------------------------------------------------
        # INNER GRID
        # --------------------------------------------------

        (
            "INNERGRID",
            (0, 0),
            (-1, -1),
            0.35,
            BORDER,
        ),

        # --------------------------------------------------
        # PADDING
        # --------------------------------------------------

        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            5,
        ),

        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            5,
        ),

        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),

        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),

    ]


    # ======================================================
    # ALTERNATING ROWS
    # ======================================================

    for row_index in range(
        1,
        len(table_data)
    ):

        if row_index % 2 == 0:

            table_commands.append(

                (
                    "BACKGROUND",
                    (0, row_index),
                    (-1, row_index),
                    LIGHT_GRAY,
                )

            )

        else:

            table_commands.append(

                (
                    "BACKGROUND",
                    (0, row_index),
                    (-1, row_index),
                    WHITE,
                )

            )


    fine_table.setStyle(

        TableStyle(
            table_commands
        )

    )


    elements.append(
        fine_table
    )


    # ======================================================
    # FOOTER SPACE
    # ======================================================

    elements.append(
        Spacer(
            1,
            5 * mm
        )
    )


    # ======================================================
    # SIMPLE FOOTER
    # ======================================================

    footer = Table(

        [

            [

                Paragraph(
                    "Wisconsin Libraries • Fine Management System",
                    footer_style
                )

            ]

        ],

        colWidths=[270 * mm],

    )


    footer.setStyle(

        TableStyle([

            (
                "LINEABOVE",
                (0, 0),
                (-1, -1),
                0.5,
                BORDER,
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

        ])

    )


    elements.append(
        footer
    )


    # ======================================================
    # BUILD PDF
    # ======================================================

    doc.build(
        elements
    )


    # ======================================================
    # RESPONSE
    # ======================================================

    buffer.seek(0)


    response = HttpResponse(

        buffer.getvalue(),

        content_type="application/pdf"

    )


    response["Content-Disposition"] = (

        'attachment; '
        'filename="wisconsin_fine_management_report.pdf"'

    )


    return response

from io import BytesIO

from openpyxl import Workbook
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Q
@staff_member_required
def export_fines_excel(request):

    # ======================================================
    # GET FILTERS
    # ======================================================

    search = request.GET.get("search", "").strip()

    payment_status = request.GET.get("status", "").strip()

    payment_method = request.GET.get("method", "").strip()

    start_date = request.GET.get("start_date", "").strip()

    end_date = request.GET.get("end_date", "").strip()


    # ======================================================
    # GET FINES
    # ======================================================

    fines = (
        Fine.objects
        .select_related(
            "transaction",
            "transaction__library_user",
            "transaction__library_user__user",
            "transaction__copy",
            "transaction__copy__resource",
        )
        .order_by("-created_at")
    )


    # ======================================================
    # SEARCH
    # ======================================================

    if search:

        fines = fines.filter(

            Q(
                transaction__library_user__user__first_name__icontains=search
            )

            |

            Q(
                transaction__library_user__user__last_name__icontains=search
            )

            |

            Q(
                transaction__library_user__user__email__icontains=search
            )

            |

            Q(
                transaction__copy__resource__title__icontains=search
            )

            |

            Q(
                transaction__copy__resource__author__icontains=search
            )

            |

            Q(
                payment_transaction_id__icontains=search
            )

            |

            Q(
                receipt_number__icontains=search
            )
        )


    # ======================================================
    # STATUS FILTER
    # ======================================================

    if payment_status:

        fines = fines.filter(
            payment_status=payment_status
        )


    # ======================================================
    # PAYMENT METHOD FILTER
    # ======================================================

    if payment_method:

        fines = fines.filter(
            payment_method=payment_method
        )


    # ======================================================
    # DATE FILTER
    # ======================================================

    if start_date:

        fines = fines.filter(
            created_at__date__gte=start_date
        )


    if end_date:

        fines = fines.filter(
            created_at__date__lte=end_date
        )


    # ======================================================
    # CREATE EXCEL FILE
    # ======================================================

    workbook = Workbook()

    worksheet = workbook.active

    worksheet.title = "Fine Report"

    # ======================================================
    # COLUMN WIDTHS
    # ======================================================

    worksheet.column_dimensions["A"].width = 15   # Fine ID
    worksheet.column_dimensions["B"].width = 22   # Student
    worksheet.column_dimensions["C"].width = 30   # Email
    worksheet.column_dimensions["D"].width = 25   # Book
    worksheet.column_dimensions["E"].width = 20   # Author

    worksheet.column_dimensions["F"].width = 16   # Issue Date
    worksheet.column_dimensions["G"].width = 16   # Due Date
    worksheet.column_dimensions["H"].width = 16   # Return Date

    worksheet.column_dimensions["I"].width = 14   # Overdue Days
    worksheet.column_dimensions["J"].width = 14   # Fine Per Day
    worksheet.column_dimensions["K"].width = 15   # Fine Amount
    worksheet.column_dimensions["L"].width = 18   # Amount Received
    worksheet.column_dimensions["M"].width = 14   # Status
    worksheet.column_dimensions["N"].width = 18   # Payment Method
    worksheet.column_dimensions["O"].width = 20   # Transaction ID
    worksheet.column_dimensions["P"].width = 20   # Receipt Number
    worksheet.column_dimensions["Q"].width = 22   # Created Date


    # ======================================================
    # HEADERS
    # ======================================================

    headers = [
        "Fine ID",
        "Student",
        "Email",
        "Book",
        "Author",
        "Issue Date",
        "Due Date",
        "Return Date",
        "Overdue Days",
        "Fine Per Day",
        "Fine Amount",
        "Amount Received",
        "Status",
        "Payment Method",
        "Transaction ID",
        "Receipt Number",
        "Created Date",
    ]


    worksheet.append(headers)


    # ======================================================
    # DATA
    # ======================================================

    for fine in fines:

        transaction = fine.transaction

        library_user = transaction.library_user

        user = library_user.user

        resource = transaction.copy.resource


        student_name = (
            user.get_full_name()
            or user.username
            or "Unknown"
        )


        worksheet.append([

            f"FIN-{fine.id:05d}",

            student_name,

            user.email,

            resource.title,

            resource.author,

            transaction.issue_date,

            transaction.due_date,

            transaction.return_date,

            fine.overdue_days or 0,

            fine.fine_per_day or 0,

            fine.fine_amount or 0,

            fine.amount_received or 0,

            fine.payment_status or "UNPAID",

            fine.payment_method or "Outstanding",

            fine.payment_transaction_id or "-",

            fine.receipt_number or "-",

            timezone.localtime(fine.created_at).replace(tzinfo=None)

        ])

    # ======================================================
    # DATE FORMATTING
    # ======================================================

    current_row = worksheet.max_row

    worksheet.cell(
        current_row,
        6
    ).number_format = "dd/mm/yyyy"

    worksheet.cell(
        current_row,
        7
    ).number_format = "dd/mm/yyyy"

    worksheet.cell(
        current_row,
        8
    ).number_format = "dd/mm/yyyy"

    worksheet.cell(
        current_row,
        17
    ).number_format = "dd/mm/yyyy"


    # ======================================================
    # SAVE EXCEL INTO MEMORY
    # ======================================================

    output = BytesIO()

    workbook.save(output)

    output.seek(0)


    # ======================================================
    # DOWNLOAD RESPONSE
    # ======================================================

    response = HttpResponse(

        output.getvalue(),

        content_type=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        )
    )


    response["Content-Disposition"] = (
        'attachment; '
        'filename="wisconsin_fine_report.xlsx"'
    )


    return response


# ============================================================
# IMPORTS
# ============================================================

import ssl
import smtplib
import threading

from django.db import close_old_connections
from io import BytesIO
from email.message import EmailMessage

from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib.staticfiles.finders import find

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)

from reportlab.lib.units import mm

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
@staff_member_required
def send_fine_acknowledgement(request, fine_id):

    # =========================================================
    # 1. GET FINE
    # =========================================================

    fine = get_object_or_404(
        Fine.objects.select_related(
            "transaction",
            "transaction__library_user",
            "transaction__library_user__user",
            "transaction__copy",
            "transaction__copy__resource",
        ),
        id=fine_id,
    )


    # =========================================================
    # 2. PAYMENT STATUS CHECK
    # =========================================================

    if fine.payment_status != "PAID":

        messages.error(
            request,
            "Payment receipt can only be sent for a paid fine."
        )

        return redirect(
            "fine_details",
            fine_id=fine.id,
        )


    # =========================================================
    # 3. GET USER
    # =========================================================

    user = fine.transaction.library_user.user

    user_email = (
        user.email or ""
    ).strip()


    # =========================================================
    # 4. EMAIL CHECK
    # =========================================================

    if not user_email:

        messages.error(
            request,
            "This user does not have a registered email address."
        )

        return redirect(
            "fine_details",
            fine_id=fine.id,
        )


    # =========================================================
    # 5. GET BOOK
    # =========================================================

    resource = fine.transaction.copy.resource


    # =========================================================
    # 6. STUDENT NAME
    # =========================================================

    student_name = (
        user.get_full_name()
        or user.username
        or "Library User"
    )


    # =========================================================
    # 7. PAYMENT VALUES
    # =========================================================

    fine_id_display = (
        f"FIN-{fine.id:05d}"
    )

    book_title = (
        resource.title
        or "Unknown Book"
    )

    fine_amount = (
        fine.fine_amount
        or 0
    )

    amount_paid = (
        fine.amount_received
        or 0
    )

    payment_method = (
        fine.payment_method
        or "N/A"
    )

    transaction_id = (
        fine.payment_transaction_id
        or "N/A"
    )

    receipt_number = (
        fine.receipt_number
        or "N/A"
    )

    receipt_datetime = (
        timezone.localtime().strftime(
            "%d %b %Y, %I:%M %p"
        )
    )


    # =========================================================
    # =========================================================
    # 8. CREATE PROFESSIONAL RECEIPT PDF
    #    BLACK & WHITE / OFFICIAL RECEIPT STYLE
    # =========================================================

    pdf_buffer = BytesIO()

    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=(
            "Wisconsin Libraries "
            f"Payment Receipt - {receipt_number}"
        ),
        author="Wisconsin Libraries",
    )

    # =========================================================
    # 9. RECEIPT COLORS
    # =========================================================

    BLACK = colors.HexColor("#000000")
    DARK = colors.HexColor("#202020")
    GRAY = colors.HexColor("#555555")
    LIGHT_GRAY = colors.HexColor("#F2F2F2")
    MID_GRAY = colors.HexColor("#BDBDBD")
    WHITE = colors.white

    # =========================================================
    # 10. RECEIPT STYLES
    # =========================================================

    styles = getSampleStyleSheet()

    receipt_brand_style = ParagraphStyle(
        "ReceiptBrand",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=18,
        textColor=BLACK,
        alignment=TA_LEFT,
    )

    receipt_subbrand_style = ParagraphStyle(
        "ReceiptSubBrand",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=GRAY,
        alignment=TA_LEFT,
    )

    receipt_title_style = ParagraphStyle(
        "ReceiptTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=BLACK,
        alignment=TA_RIGHT,
    )

    receipt_meta_style = ParagraphStyle(
        "ReceiptMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=BLACK,
        alignment=TA_RIGHT,
    )

    receipt_section_style = ParagraphStyle(
        "ReceiptSection",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=BLACK,
        alignment=TA_LEFT,
    )

    receipt_label_style = ParagraphStyle(
        "ReceiptLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        textColor=BLACK,
        alignment=TA_LEFT,
    )

    receipt_value_style = ParagraphStyle(
        "ReceiptValue",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=DARK,
        alignment=TA_LEFT,
    )

    receipt_value_right_style = ParagraphStyle(
        "ReceiptValueRight",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=DARK,
        alignment=TA_RIGHT,
    )

    receipt_amount_style = ParagraphStyle(
        "ReceiptAmount",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        textColor=BLACK,
        alignment=TA_RIGHT,
    )

    receipt_footer_style = ParagraphStyle(
        "ReceiptFooter",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        textColor=GRAY,
        alignment=TA_CENTER,
    )

    elements = []

    # =========================================================
    # 11. RECEIPT HEADER
    # =========================================================

    logo_path = find(
        "images/navina/W-logo.png"
    )

    if logo_path:
        logo = Image(
            logo_path,
            width=18 * mm,
            height=18 * mm,
        )
    else:
        logo = Paragraph(
            "<b>W</b>",
            receipt_brand_style,
        )

    brand_block = [
        Paragraph(
            "WISCONSIN LIBRARIES",
            receipt_brand_style,
        ),
        Spacer(1, 1 * mm),
        Paragraph(
            "LIBRARY FINE MANAGEMENT SYSTEM",
            receipt_subbrand_style,
        ),
    ]

    header_left = Table(
        [[logo, brand_block]],
        colWidths=[23 * mm, 68 * mm],
    )

    header_left.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ])
    )

    header_right = [
        Paragraph("PAYMENT RECEIPT", receipt_title_style),
        Spacer(1, 2 * mm),
        Paragraph(
            f"<b>Receipt No:</b> {receipt_number}",
            receipt_meta_style,
        ),
        Spacer(1, 1 * mm),
        Paragraph(
            f"<b>Receipt Date:</b> {receipt_datetime}",
            receipt_meta_style,
        ),
    ]

    header_table = Table(
        [[header_left, header_right]],
        colWidths=[91 * mm, 79 * mm],
    )

    header_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ])
    )

    elements.append(header_table)
    elements.append(Spacer(1, 5 * mm))

    # =========================================================
    # 12. MAIN RECEIPT DIVIDER
    # =========================================================

    divider = Table(
        [[""]],
        colWidths=[170 * mm],
        rowHeights=[0.8 * mm],
    )

    divider.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BLACK),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ])
    )

    elements.append(divider)
    elements.append(Spacer(1, 4 * mm))

    # =========================================================
    # 13. RECEIPT / PAYMENT INFORMATION
    # =========================================================

    department_data = [
        [
            Paragraph("Department", receipt_label_style),
            Paragraph("LIBRARY", receipt_value_style),
            Paragraph("Receipt Status", receipt_label_style),
            Paragraph("PAID", receipt_value_right_style),
        ],
        [
            Paragraph("Fine ID", receipt_label_style),
            Paragraph(fine_id_display, receipt_value_style),
            Paragraph("Payment Method", receipt_label_style),
            Paragraph(payment_method, receipt_value_right_style),
        ],
    ]

    department_table = Table(
        department_data,
        colWidths=[32 * mm, 53 * mm, 38 * mm, 47 * mm],
        rowHeights=[8 * mm, 8 * mm],
    )

    department_table.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.7, BLACK),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, MID_GRAY),
            ("BACKGROUND", (0, 0), (0, -1), LIGHT_GRAY),
            ("BACKGROUND", (2, 0), (2, -1), LIGHT_GRAY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ])
    )

    elements.append(department_table)
    elements.append(Spacer(1, 5 * mm))

    # =========================================================
    # 14. STUDENT / BOOK DETAILS
    # =========================================================

    elements.append(
        Paragraph(
            "STUDENT & BOOK DETAILS",
            receipt_section_style,
        )
    )
    elements.append(Spacer(1, 2 * mm))

    student_book_data = [
        [
            Paragraph("Student Name", receipt_label_style),
            Paragraph(student_name, receipt_value_style),
        ],
        [
            Paragraph("Email Address", receipt_label_style),
            Paragraph(user_email, receipt_value_style),
        ],
        [
            Paragraph("Book Title", receipt_label_style),
            Paragraph(book_title, receipt_value_style),
        ],
    ]

    student_book_table = Table(
        student_book_data,
        colWidths=[42 * mm, 128 * mm],
        rowHeights=[8 * mm, 8 * mm, 8 * mm],
    )

    student_book_table.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.7, BLACK),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, MID_GRAY),
            ("BACKGROUND", (0, 0), (0, -1), LIGHT_GRAY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ])
    )

    elements.append(student_book_table)
    elements.append(Spacer(1, 5 * mm))

    # =========================================================
    # 15. PAYMENT DETAILS
    # =========================================================

    elements.append(
        Paragraph(
            "PAYMENT DETAILS",
            receipt_section_style,
        )
    )
    elements.append(Spacer(1, 2 * mm))

    payment_details_data = [
        [
            Paragraph("Description", receipt_label_style),
            Paragraph("Reference", receipt_label_style),
            Paragraph("Amount", receipt_label_style),
        ],
        [
            Paragraph("Library Fine Payment", receipt_value_style),
            Paragraph(fine_id_display, receipt_value_style),
            Paragraph(
                f"${fine_amount:,.2f}",
                receipt_value_right_style,
            ),
        ],
    ]

    payment_details_table = Table(
        payment_details_data,
        colWidths=[82 * mm, 45 * mm, 43 * mm],
        rowHeights=[8 * mm, 11 * mm],
    )

    payment_details_table.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.8, BLACK),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, MID_GRAY),
            ("BACKGROUND", (0, 0), (-1, 0), BLACK),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (2, 0), (2, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ])
    )

    elements.append(payment_details_table)
    elements.append(Spacer(1, 3 * mm))

    # =========================================================
    # 16. TOTAL AMOUNT
    # =========================================================

    total_table = Table(
        [[
            Paragraph("TOTAL AMOUNT PAID", receipt_label_style),
            Paragraph(
                f"${amount_paid:,.2f}",
                receipt_amount_style,
            ),
        ]],
        colWidths=[125 * mm, 45 * mm],
        rowHeights=[12 * mm],
    )

    total_table.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.9, BLACK),
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )

    elements.append(total_table)
    elements.append(Spacer(1, 5 * mm))

    # =========================================================
    # 17. TRANSACTION / RECEIPT DATA
    # =========================================================

    transaction_data = [
        [
            Paragraph("Transaction ID", receipt_label_style),
            Paragraph(transaction_id, receipt_value_style),
        ],
        [
            Paragraph("Receipt Number", receipt_label_style),
            Paragraph(receipt_number, receipt_value_style),
        ],
        [
            Paragraph("Payment Date", receipt_label_style),
            Paragraph(receipt_datetime, receipt_value_style),
        ],
    ]

    transaction_table = Table(
        transaction_data,
        colWidths=[42 * mm, 128 * mm],
        rowHeights=[8 * mm, 8 * mm, 8 * mm],
    )

    transaction_table.setStyle(
        TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.35, MID_GRAY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ])
    )

    elements.append(transaction_table)
    elements.append(Spacer(1, 7 * mm))

    # =========================================================
    # 18. OFFICIAL FOOTER
    # =========================================================

    footer_line = Table(
        [[""]],
        colWidths=[170 * mm],
        rowHeights=[0.7 * mm],
    )

    footer_line.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BLACK),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ])
    )

    elements.append(footer_line)
    elements.append(Spacer(1, 3 * mm))

    elements.append(
        Paragraph(
            "This is an electronically generated payment receipt.",
            receipt_footer_style,
        )
    )

    elements.append(Spacer(1, 1 * mm))

    elements.append(
        Paragraph(
            "Wisconsin Libraries • Library Fine Management System",
            receipt_footer_style,
        )
    )

    # =========================================================
    # 19. BUILD PDF
    # =========================================================

    try:

        document.build(elements)

    except Exception as e:

        messages.error(
            request,
            (
                "Unable to create payment receipt: "
                f"{e}"
            ),
        )

        return redirect(
            "fine_details",
            fine_id=fine.id,
        )

    # 19. GET PDF BYTES
    # =========================================================

    pdf_buffer.seek(0)

    pdf_data = (
        pdf_buffer.getvalue()
    )


    # =========================================================
    # 20. PROFESSIONAL HTML EMAIL
    # =========================================================

    html_content = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>
Wisconsin Libraries Payment Receipt
</title>

</head>


<body
style="
margin:0;
padding:0;
background:#f4f6f8;
font-family:Arial,Helvetica,sans-serif;
color:#202124;
"
>


<table
width="100%"
cellpadding="0"
cellspacing="0"
border="0"
style="
background:#f4f6f8;
padding:35px 15px;
"
>

<tr>

<td align="center">


<table
width="600"
cellpadding="0"
cellspacing="0"
border="0"
style="
max-width:600px;
width:100%;
background:#ffffff;
border:1px solid #e1e4e8;
"
>


<!-- =====================================================
     HEADER
===================================================== -->

<tr>

<td
align="center"
style="
padding:28px 25px 20px;
border-bottom:1px solid #eeeeee;
"
>

<div
style="
font-size:20px;
font-weight:bold;
letter-spacing:.6px;
color:#13294b;
"
>
WISCONSIN LIBRARIES
</div>


<div
style="
margin-top:5px;
font-size:11px;
color:#737784;
"
>
Library Fine Management System
</div>

</td>

</tr>


<!-- =====================================================
     SUCCESS ICON
===================================================== -->

<tr>

<td
align="center"
style="
padding-top:28px;
"
>

<div
style="
width:58px;
height:58px;
line-height:58px;
border-radius:50%;
background:#dcfce7;
color:#16a34a;
font-size:30px;
font-weight:bold;
"
>
✓
</div>

</td>

</tr>


<!-- =====================================================
     SUCCESS TITLE
===================================================== -->

<tr>

<td
align="center"
style="
padding:18px 30px 5px;
"
>

<div
style="
font-size:25px;
font-weight:bold;
color:#16a34a;
"
>
Payment Successful!
</div>

</td>

</tr>


<tr>

<td
align="center"
style="
padding:5px 40px 25px;
"
>

<div
style="
font-size:14px;
line-height:22px;
color:#737784;
"
>

Dear
<strong>{student_name}</strong>,

<br>

Your library fine payment has been successfully processed.

</div>

</td>

</tr>


<!-- =====================================================
     PAYMENT CARD
===================================================== -->

<tr>

<td
style="
padding:0 30px 20px;
"
>


<table
width="100%"
cellpadding="0"
cellspacing="0"
border="0"
style="
background:#f6f7f9;
border:1px solid #e1e4e8;
"
>


<!-- AMOUNT -->

<tr>

<td
style="
padding:17px 16px;
font-size:13px;
color:#737784;
border-bottom:1px solid #e1e4e8;
"
>
Amount
</td>


<td
align="right"
style="
padding:17px 16px;
font-size:21px;
font-weight:bold;
color:#202124;
border-bottom:1px solid #e1e4e8;
"
>
${amount_paid:.2f}
</td>

</tr>


<!-- FINE ID -->

<tr>

<td
style="
padding:11px 16px;
font-size:13px;
color:#737784;
border-bottom:1px solid #e1e4e8;
"
>
Fine ID
</td>


<td
align="right"
style="
padding:11px 16px;
font-size:13px;
font-weight:bold;
color:#202124;
border-bottom:1px solid #e1e4e8;
"
>
{fine_id_display}
</td>

</tr>


<!-- BOOK -->

<tr>

<td
style="
padding:11px 16px;
font-size:13px;
color:#737784;
border-bottom:1px solid #e1e4e8;
"
>
Book
</td>


<td
align="right"
style="
padding:11px 16px;
font-size:13px;
font-weight:bold;
color:#202124;
border-bottom:1px solid #e1e4e8;
"
>
{book_title}
</td>

</tr>


<!-- TRANSACTION -->

<tr>

<td
style="
padding:11px 16px;
font-size:13px;
color:#737784;
border-bottom:1px solid #e1e4e8;
"
>
Transaction ID
</td>


<td
align="right"
style="
padding:11px 16px;
font-size:13px;
font-weight:bold;
color:#202124;
border-bottom:1px solid #e1e4e8;
"
>
{transaction_id}
</td>

</tr>


<!-- PAYMENT METHOD -->

<tr>

<td
style="
padding:11px 16px;
font-size:13px;
color:#737784;
border-bottom:1px solid #e1e4e8;
"
>
Payment Method
</td>


<td
align="right"
style="
padding:11px 16px;
font-size:13px;
font-weight:bold;
color:#202124;
border-bottom:1px solid #e1e4e8;
"
>
{payment_method}
</td>

</tr>


<!-- DATE -->

<tr>

<td
style="
padding:11px 16px;
font-size:13px;
color:#737784;
border-bottom:1px solid #e1e4e8;
"
>
Date
</td>


<td
align="right"
style="
padding:11px 16px;
font-size:13px;
font-weight:bold;
color:#202124;
border-bottom:1px solid #e1e4e8;
"
>
{receipt_datetime}
</td>

</tr>


<!-- RECEIPT -->

<tr>

<td
style="
padding:11px 16px;
font-size:13px;
color:#737784;
"
>
Receipt Number
</td>


<td
align="right"
style="
padding:11px 16px;
font-size:13px;
font-weight:bold;
color:#202124;
"
>
{receipt_number}
</td>

</tr>


</table>

</td>

</tr>


<!-- =====================================================
     PAID STATUS
===================================================== -->

<tr>

<td
align="center"
style="
padding:0 30px 20px;
"
>

<div
style="
display:inline-block;
background:#ecfdf3;
border:1px solid #bbf7d0;
color:#15803d;
padding:7px 18px;
font-size:12px;
font-weight:bold;
"
>
✓ PAYMENT PAID
</div>

</td>

</tr>


<!-- =====================================================
     PDF ATTACHMENT MESSAGE
===================================================== -->

<tr>

<td
style="
padding:0 30px 25px;
"
>

<table
width="100%"
cellpadding="0"
cellspacing="0"
border="0"
style="
background:#eff6ff;
border:1px solid #d5e5f7;
"
>

<tr>

<td
align="center"
style="
padding:15px;
font-size:12px;
line-height:19px;
color:#536174;
"
>

📎

<strong>
Official Receipt Attached
</strong>

<br>

Your payment receipt is attached to this email
as a PDF for your records.

</td>

</tr>

</table>

</td>

</tr>


<!-- =====================================================
     FOOTER
===================================================== -->

<tr>

<td
align="center"
style="
padding:22px 30px;
background:#fafafa;
border-top:1px solid #eeeeee;
"
>

<div
style="
font-size:14px;
font-weight:bold;
color:#13294b;
"
>
Wisconsin Libraries
</div>


<div
style="
margin-top:5px;
font-size:11px;
color:#8a9099;
"
>
Library Fine Management System
</div>


<div
style="
margin-top:10px;
font-size:10px;
color:#a0a5ad;
"
>
This is an automatically generated
payment acknowledgement.
</div>

</td>

</tr>


</table>

</td>

</tr>

</table>


</body>

</html>
"""


    # =========================================================
    # 21. PLAIN TEXT FALLBACK
    # =========================================================

    text_content = f"""
Dear {student_name},

Your Wisconsin Libraries fine payment has been
successfully processed.

PAYMENT DETAILS
---------------

Amount Paid:
${amount_paid:.2f}

Fine ID:
{fine_id_display}

Book:
{book_title}

Transaction ID:
{transaction_id}

Payment Method:
{payment_method}

Date:
{receipt_datetime}

Receipt Number:
{receipt_number}

Payment Status:
PAID

Your official payment receipt is attached
to this email as a PDF.

Please retain the attached receipt
for your records.

Thank you for using Wisconsin Libraries.

Library Administration
Wisconsin Libraries
"""


    # =========================================================
    # 22. CREATE EMAIL
    # =========================================================

    email_message = EmailMessage()


    email_message["Subject"] = (
        "Wisconsin Libraries | "
        f"Payment Successful - {receipt_number}"
    )


    email_message["From"] = (
        settings.EMAIL_HOST_USER
    )


    email_message["To"] = (
        user_email
    )


    # Plain text fallback
    email_message.set_content(
        text_content
    )


    # HTML version
    email_message.add_alternative(
        html_content,
        subtype="html",
    )


    # =========================================================
    # 23. ATTACH PDF RECEIPT
    # =========================================================

    email_message.add_attachment(

        pdf_data,

        maintype="application",

        subtype="pdf",

        filename=(
            "Wisconsin_Libraries_"
            f"Payment_Receipt_"
            f"{receipt_number}.pdf"
        ),

    )


    # =========================================================
    # =========================================================
    # 24. SEND EMAIL IN BACKGROUND
    # =========================================================

    def send_email_background():

        close_old_connections()

        try:

            print(
                "======================================"
            )
            print(
                "SENDING PAYMENT RECEIPT"
            )
            print(
                "Recipient:",
                user_email
            )
            print(
                "Receipt:",
                receipt_number
            )
            print(
                "======================================"
            )

            context = ssl.create_default_context()

            context.verify_flags &= (
                ~ssl.VERIFY_X509_STRICT
            )

            with smtplib.SMTP(
                settings.EMAIL_HOST,
                settings.EMAIL_PORT,
                timeout=30,
            ) as server:

                server.ehlo()

                server.starttls(
                    context=context
                )

                server.ehlo()

                print(
                    "SMTP TLS connection established."
                )

                server.login(
                    settings.EMAIL_HOST_USER,
                    settings.EMAIL_HOST_PASSWORD,
                )

                print(
                    "SMTP authentication successful."
                )

                server.send_message(
                    email_message
                )

                print(
                    "Payment receipt email accepted by Gmail."
                )

            print(
                "Email sending completed successfully."
            )

        except Exception as e:

            import traceback

            traceback.print_exc()

            print(
                "Payment receipt email FAILED:",
                str(e)
            )

        finally:

            close_old_connections()


    # =========================================================
    # 25. START BACKGROUND EMAIL
    # =========================================================

    email_thread = threading.Thread(
        target=send_email_background,
        daemon=True,
    )

    email_thread.start()


    # =========================================================
    # 26. IMMEDIATE TOAST
    # =========================================================

    messages.success(
        request,
        (
            "Payment receipt is being sent to "
            f"{user_email}."
        ),
    )


    # =========================================================
    # 27. RETURN IMMEDIATELY
    # =========================================================

    return redirect(

        "fine_details",

        fine_id=fine.id,

    )
    
    
# from django.contrib.auth.decorators import login_required
# from django.http import JsonResponse
# from django.shortcuts import get_object_or_404


# @login_required
# def verify_issue_pin(request, request_uuid):

#     if not request.user.is_staff:
#         return JsonResponse(
#             {
#                 "success": False,
#                 "message": "You are not authorized to issue books."
#             },
#             status=403,
#         )

#     if request.method != "POST":
#         return JsonResponse(
#             {
#                 "success": False,
#                 "message": "Invalid request method."
#             },
#             status=400,
#         )

#     entered_pin = request.POST.get("pin", "").strip()

#     session_pin = request.session.get("library_issue_pin")

#     if not session_pin:
#         return JsonResponse(
#             {
#                 "success": False,
#                 "message": "Your verification PIN is not available. Please log in again."
#             },
#             status=400,
#         )

#     if entered_pin != session_pin:
#         return JsonResponse(
#             {
#                 "success": False,
#                 "message": "Invalid verification PIN."
#             },
#             status=400,
#         )

#     # PIN is correct for this logged-in staff session.
#     request.session["issue_pin_verified"] = True

#     return JsonResponse(
#         {
#             "success": True,
#             "redirect_url": reverse(
#                 "issue_book_detail",
#                 kwargs={
#                     "request_uuid": str(request_uuid)
#                 },
#             ),
#         }
#     )
    
# from django.http import HttpResponseForbidden   
# @login_required(login_url="/login/")
# def issue_book_qr_entry(request, request_uuid):

#     if not request.user.is_staff:
#         return HttpResponseForbidden(
#             "You are not authorized to issue library books."
#         )

#     borrow_request = get_object_or_404(
#         BorrowRequest,
#         uuid=request_uuid,
#         status="APPROVED",
#     )

#     return render(
#         request,
#         "library_admin/nancy/issue_book_qr_verify.html",
#         {
#             "borrow_request": borrow_request,
#         },)


from django.core.paginator import Paginator
from django.shortcuts import render

from Library.models import BorrowTransaction


RENEWAL_REQUESTS_PER_PAGE = 10


@staff_member_required
def renewal_requests(request):

    renewal_requests_queryset = (
        BorrowTransaction.objects
        .select_related(
            "library_user",
            "library_user__user",
            "copy",
            "copy__resource",
            "copy__resource__library",
        )
        .filter(
            renewal_requested=True,
            status="ISSUED",
        )
        .order_by(
            "renewal_requested_at"
        )
    )

    paginator = Paginator(
        renewal_requests_queryset,
        RENEWAL_REQUESTS_PER_PAGE
    )

    page_number = request.GET.get("page", 1)

    page_obj = paginator.get_page(page_number)

    page_numbers = get_page_numbers(page_obj)

    context = {
        "renewal_requests": page_obj.object_list,

        "page_obj": page_obj,

        "page_numbers": page_numbers,

        "paginator": paginator,

        "total_renewal_requests": paginator.count,
    }

    return render(
        request,
        "library_admin/renewal_requests.html",
        context,
    )

def get_page_numbers(page_obj):
    current_page = page_obj.number
    total_pages = page_obj.paginator.num_pages

    if total_pages <= 5:
        return list(range(1, total_pages + 1))

    if current_page <= 2:
        return [1, 2, 3, "...", total_pages]

    if current_page >= total_pages - 1:
        return [
            1,
            "...",
            total_pages - 2,
            total_pages - 1,
            total_pages,
        ]

    return [
        1,
        "...",
        current_page,
        "...",
        total_pages,
    ]

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone

from Library.models import (
    BorrowTransaction,
    # Reservation,
)

from Staff.models import Notification


# =====================================================
# Renewal settings
# =====================================================

RENEWAL_DAYS = 28
MAX_RENEWALS = 2


# @staff_member_required
# def approve_renewal(request, transaction_id):


#     if request.method != "POST":

#         messages.error(
#             request,
#             "Invalid renewal approval request."
#         )

#         return redirect(
#             "renewal_requests"
#         )

#     loan = get_object_or_404(

#         BorrowTransaction.objects.select_related(
#             "library_user",
#             "library_user__user",
#             "copy",
#             "copy__resource",
#             "copy__resource__library",
#         ),

#         id=transaction_id,

#     )

#     if not loan.renewal_requested:

#         messages.warning(
#             request,
#             "This renewal request has already been processed."
#         )

#         return redirect(
#             "renewal_requests"
#         )


#     if loan.status != "ISSUED":

#         messages.error(
#             request,
#             "This book cannot be renewed because the loan is no longer active."
#         )

#         return redirect(
#             "renewal_requests"
#         )


#     if loan.return_date is not None:

#         messages.error(
#             request,
#             "This book has already been returned and cannot be renewed."
#         )

#         return redirect(
#             "renewal_requests"
#         )



#     if loan.renewal_count >= MAX_RENEWALS:

#         messages.error(
#             request,
#             "This book has already reached the maximum renewal limit."
#         )

#         return redirect(
#             "renewal_requests"
#         )


#     old_due_date = loan.due_date

#     new_due_date = (
#         old_due_date +
#         timedelta(
#             days=RENEWAL_DAYS
#         )
#     )


#     before_data = AuditLogger.model_to_dict(
#         loan,
#         fields=[
#             "status",
#             "due_date",
#             "renewal_count",
#             "last_renewed_at",
#             "renewal_requested",
#             "renewal_requested_at",
#         ],
#     )



#     with db_transaction.atomic():

#         loan.due_date = new_due_date

#         loan.renewal_count += 1

#         loan.last_renewed_at = timezone.now()

#         loan.renewal_requested = False

#         loan.renewal_requested_at = None

#         loan.save(
#             update_fields=[
#                 "due_date",
#                 "renewal_count",
#                 "last_renewed_at",
#                 "renewal_requested",
#                 "renewal_requested_at",
#             ]
#         )


#     after_data = AuditLogger.model_to_dict(
#         loan,
#         fields=[
#             "status",
#             "due_date",
#             "renewal_count",
#             "last_renewed_at",
#             "renewal_requested",
#             "renewal_requested_at",
#         ],
#     )



#     AuditLogger.log(
#         request=request,
#         action="RENEW",
#         module="LibraryAdmin",
#         object_type="Borrow Transaction",
#         object_id=loan.id,
#         description=(
#             f"Approved renewal for "
#             f"'{loan.copy.resource.title}'. "
#             f"Due date changed from "
#             f"{old_due_date.strftime('%b %d, %Y')} to "
#             f"{new_due_date.strftime('%b %d, %Y')}."
#         ),
#         before_data=before_data,
#         after_data=after_data,
#         status="SUCCESS",
#     )


#     Notification.objects.create(

#         user=loan.library_user.user,

#         title="Book Renewal Approved",

#         message=(
#             f'Your renewal request for '
#             f'"{loan.copy.resource.title}" '
#             f'has been approved. '
#             f'Your new due date is '
#             f'{new_due_date.strftime("%b %d, %Y")}.'
#         ),

#         notification_type="SUCCESS",

#         link=reverse(
#             "Student:student_borrowed_books",
#             kwargs={
#                 "uuid": transaction.library_user.user.uuid
#             }
#         ),

#     )


#     messages.success(

#         request,

#         f'"{loan.copy.resource.title}" has been '
#         f'renewed successfully. '
#         f'New due date: '
#         f'{new_due_date.strftime("%b %d, %Y")}.'

#     )


#     return redirect(
#         "renewal_requests"
#     )


@staff_member_required
def approve_renewal(request, transaction_id):

    # =================================================
    # 1. APPROVAL MUST BE POST
    # =================================================

    if request.method != "POST":

        messages.error(
            request,
            "Invalid renewal approval request."
        )

        return redirect(
            "renewal_requests"
        )

    # =================================================
    # 2. GET TRANSACTION
    # =================================================

    loan = get_object_or_404(

        BorrowTransaction.objects.select_related(
            "library_user",
            "library_user__user",
            "copy",
            "copy__resource",
            "copy__resource__library",
        ),

        id=transaction_id,
    )

    # =================================================
    # 3. CHECK REQUEST
    # =================================================

    if not loan.renewal_requested:

        messages.warning(
            request,
            "This renewal request has already been processed."
        )

        return redirect(
            "renewal_requests"
        )

    # =================================================
    # 4. CHECK STATUS
    # =================================================

    if loan.status != "ISSUED":

        messages.error(
            request,
            "This book cannot be renewed because the loan is no longer active."
        )

        return redirect(
            "renewal_requests"
        )

    # =================================================
    # 5. CHECK RETURN
    # =================================================

    if loan.return_date is not None:

        messages.error(
            request,
            "This book has already been returned and cannot be renewed."
        )

        return redirect(
            "renewal_requests"
        )

    # =================================================
    # 6. CHECK RENEWAL LIMIT
    # =================================================

    if loan.renewal_count >= MAX_RENEWALS:

        messages.error(
            request,
            "This book has already reached the maximum renewal limit."
        )

        return redirect(
            "renewal_requests"
        )

    # =================================================
    # 7. CHECK RESERVATION
    # =================================================

    # has_other_reservation = (
    #
    #     Reservation.objects
    #
    #     .filter(
    #         resource=loan.copy.resource,
    #         status="PENDING",
    #     )
    #
    #     .exclude(
    #         library_user=loan.library_user
    #     )
    #
    #     .exists()
    # )
    #
    # if has_other_reservation:
    #
    #     messages.error(
    #         request,
    #         "This renewal cannot be approved because another "
    #         "student has reserved this book."
    #     )
    #
    #     return redirect(
    #         "renewal_requests"
    #     )

    # =================================================
    # 8. CALCULATE NEW DUE DATE
    # =================================================

    old_due_date = loan.due_date

    new_due_date = (
        old_due_date +
        timedelta(
            days=RENEWAL_DAYS
        )
    )

    # =================================================
    # 9. AUDIT — BEFORE DATA
    # =================================================

    before_data = AuditLogger.model_to_dict(
        loan,
        fields=[
            "status",
            "due_date",
            "renewal_count",
            "last_renewed_at",
            "renewal_requested",
            "renewal_requested_at",
        ],
    )

    # =================================================
    # 10. PERFORM RENEWAL
    # =================================================

    with db_transaction.atomic():

        loan.due_date = new_due_date

        loan.renewal_count += 1

        loan.last_renewed_at = timezone.now()

        loan.renewal_requested = False

        loan.renewal_requested_at = None

        loan.save(
            update_fields=[
                "due_date",
                "renewal_count",
                "last_renewed_at",
                "renewal_requested",
                "renewal_requested_at",
            ]
        )

    # =================================================
    # 11. AUDIT — AFTER DATA
    # =================================================

    after_data = AuditLogger.model_to_dict(
        loan,
        fields=[
            "status",
            "due_date",
            "renewal_count",
            "last_renewed_at",
            "renewal_requested",
            "renewal_requested_at",
        ],
    )

    # =================================================
    # 12. AUDIT LOG — RENEW
    # =================================================

    AuditLogger.log(
        request=request,

        action="RENEW",

        module="LibraryAdmin",

        object_type="BorrowTransaction",

        object_id=loan.id,

        description=(
            f"Approved and renewed "
            f"'{loan.copy.resource.title}'. "
            f"Due date changed from "
            f"{old_due_date.strftime('%b %d, %Y')} to "
            f"{new_due_date.strftime('%b %d, %Y')}."
        ),

        before_data=before_data,

        after_data=after_data,

        status="SUCCESS",
    )

    # =================================================
    # 13. NOTIFY STUDENT
    # =================================================

    Notification.objects.create(

        user=loan.library_user.user,

        title="Book Renewal Approved",

        message=(
            f'Your renewal request for '
            f'"{loan.copy.resource.title}" '
            f'has been approved. '
            f'Your new due date is '
            f'{new_due_date.strftime("%b %d, %Y")}.'
        ),

        notification_type="SUCCESS",

        link=reverse(
            "Student:student_borrowed_books",
            kwargs={
                "uuid": loan.library_user.user.uuid
            }
        ),
    )

    # =================================================
    # 14. STAFF SUCCESS MESSAGE
    # =================================================

    messages.success(

        request,

        f'"{loan.copy.resource.title}" has been '
        f'renewed successfully. '
        f'New due date: '
        f'{new_due_date.strftime("%b %d, %Y")}.'

    )

    # =================================================
    # 15. RETURN TO RENEWAL REQUESTS
    # =================================================

    return redirect(
        "renewal_requests"
    )
    
    

from datetime import date, timedelta
from collections import OrderedDict
from io import BytesIO

from django.db.models import Q
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required

from Library.models import (
    Library,
    LibraryResource,
    ResourceCategory,
    ResourceCopy,
    LibraryUser,
    BorrowTransaction,
    # Reservation,
)

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from django.http import JsonResponse
from django.template.loader import render_to_string

# ============================================================
# BOOK MANAGEMENT REPORT
# ============================================================

@staff_member_required
def book_management_report(request):

    today = date.today()

    # ========================================================
    # FILTER VALUES
    # ========================================================

    period = request.GET.get("period", "month").strip()

    selected_library = request.GET.get("library", "").strip()
    selected_category = request.GET.get("category", "").strip()

    start_date_value = request.GET.get("start_date", "").strip()
    end_date_value = request.GET.get("end_date", "").strip()

    # ========================================================
    # DATE RANGE
    # ========================================================

    if period == "today":

        start_date = today
        end_date = today

    elif period == "week":

        # Monday -> Sunday
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)

    elif period == "custom":

        try:
            start_date = date.fromisoformat(start_date_value)
            end_date = date.fromisoformat(end_date_value)

            if start_date > end_date:
                start_date, end_date = end_date, start_date

        except (ValueError, TypeError):

            start_date = today.replace(day=1)
            end_date = today
            period = "month"

    else:

        # Current month
        start_date = today.replace(day=1)
        end_date = today
        period = "month"

    # ========================================================
    # BASE BOOK QUERY
    #
    # Only BOOK resources are included.
    # ========================================================

    resources = (
        LibraryResource.objects
        .select_related("library", "category")
        .filter(resource_type="BOOK")
    )

    # ========================================================
    # LIBRARY FILTER
    # ========================================================

    if selected_library:
        resources = resources.filter(
            library_id=selected_library
        )

    # ========================================================
    # CATEGORY FILTER
    # ========================================================

    if selected_category:
        resources = resources.filter(
            category_id=selected_category
        )

    # ========================================================
    # RESOURCE IDs
    # ========================================================

    resource_ids = resources.values_list(
        "id",
        flat=True
    )

    # ========================================================
    # COPY QUERY
    # ========================================================

    copies = ResourceCopy.objects.filter(
        resource_id__in=resource_ids
    )

    # ========================================================
    # INVENTORY STATISTICS
    # ========================================================

    total_copies = copies.count()

    available_copies = copies.filter(
        status="AVAILABLE"
    ).count()

    borrowed_copies = copies.filter(
        status="CHECKED_OUT"
    ).count()

    reserved_copies = copies.filter(
        status="RESERVED"
    ).count()

    damaged_copies = copies.filter(
        status="DAMAGED"
    ).count()

    lost_copies = copies.filter(
        status="LOST"
    ).count()

    # ========================================================
    # TOTAL BOOK TITLES
    # ========================================================

    total_book_titles = resources.count()

    # ========================================================
    # BORROW TRANSACTIONS
    # ========================================================

    transactions = (
        BorrowTransaction.objects
        .select_related(
            "copy",
            "copy__resource",
            "copy__resource__library",
            "copy__resource__category",
            "library_user",
            "library_user__user",
        )
        .filter(
            copy__resource_id__in=resource_ids
        )
    )

    # ========================================================
    # PERIOD BORROWINGS
    # ========================================================

    period_transactions = transactions.filter(
        issue_date__gte=start_date,
        issue_date__lte=end_date,
    )

    total_borrowed_period = period_transactions.count()

    # ========================================================
    # PERIOD RETURNS
    # ========================================================

    total_returned_period = transactions.filter(
        return_date__gte=start_date,
        return_date__lte=end_date,
        status="RETURNED",
    ).count()

    # ========================================================
    # BORROWED TODAY
    # ========================================================

    borrowed_today = transactions.filter(
        issue_date=today
    ).count()

    # ========================================================
    # BORROWED THIS WEEK
    # ========================================================

    week_start = today - timedelta(
        days=today.weekday()
    )

    week_end = week_start + timedelta(days=6)

    borrowed_this_week = transactions.filter(
        issue_date__gte=week_start,
        issue_date__lte=week_end,
    ).count()

    # ========================================================
    # BORROWED THIS MONTH
    # ========================================================

    month_start = today.replace(day=1)

    borrowed_this_month = transactions.filter(
        issue_date__gte=month_start,
        issue_date__lte=today,
    ).count()

    # ========================================================
    # USER TYPE BORROWING
    # ========================================================

    user_type_data = []

    for value, label in LibraryUser.USER_TYPES:

        count = period_transactions.filter(
            library_user__user_type=value
        ).count()

        user_type_data.append({
            "value": value,
            "label": label,
            "count": count,
        })

    # ========================================================
    # DAILY BORROWING / RETURN DATA
    # ========================================================

    daily_data = []

    current_date = start_date

    while current_date <= end_date:

        borrowed_count = period_transactions.filter(
            issue_date=current_date
        ).count()

        returned_count = transactions.filter(
            return_date=current_date,
            status="RETURNED",
        ).count()

        daily_data.append({
            "date": current_date.isoformat(),
            "display_date": current_date.strftime("%d %b %Y"),
            "label": current_date.strftime("%d %b"),
            "borrowed": borrowed_count,
            "returned": returned_count,
        })

        current_date += timedelta(days=1)

    # ========================================================
    # CATEGORY STATISTICS
    # ========================================================

    category_data = []

    category_queryset = (
        ResourceCategory.objects
        .filter(
            resources__id__in=resource_ids
        )
        .distinct()
        .order_by("title")
    )

    for category in category_queryset:

        category_resources = resources.filter(
            category=category
        )

        category_resource_ids = category_resources.values_list(
            "id",
            flat=True
        )

        category_copies = ResourceCopy.objects.filter(
            resource_id__in=category_resource_ids
        )

        category_borrowed = period_transactions.filter(
            copy__resource__category=category
        ).count()

        category_data.append({
            "title": category.title,
            "total_books": category_resources.count(),
            "total_copies": category_copies.count(),
            "available": category_copies.filter(
                status="AVAILABLE"
            ).count(),
            "borrowed": category_copies.filter(
                status="CHECKED_OUT"
            ).count(),
            "period_borrowed": category_borrowed,
        })

    # Most borrowed categories
    most_borrowed_categories = sorted(
        category_data,
        key=lambda x: x["period_borrowed"],
        reverse=True
    )[:5]

    # ========================================================
    # MOST BORROWED BOOKS
    # ========================================================

    book_borrow_counts = {}

    for txn in period_transactions:

        resource = txn.copy.resource

        if resource.id not in book_borrow_counts:

            book_borrow_counts[resource.id] = {
                "title": resource.title,
                "author": resource.author,
                "category": (
                    resource.category.title
                    if resource.category
                    else "Uncategorized"
                ),
                "library": (
                    resource.library.library_name
                    if resource.library
                    else "—"
                ),
                "borrowed": 0,
            }

        book_borrow_counts[
            resource.id
        ]["borrowed"] += 1

    most_borrowed_books = sorted(
        book_borrow_counts.values(),
        key=lambda x: x["borrowed"],
        reverse=True
    )[:10]

    # ========================================================
    # MOST BORROWED CATEGORIES
    # ========================================================

    most_borrowed_categories = sorted(
        category_data,
        key=lambda category_row: category_row["period_borrowed"],
        reverse=True
    )[:5]

    if most_borrowed_categories:
        max_category_borrowed = (
        most_borrowed_categories[0]["period_borrowed"]
    )
    else:
        max_category_borrowed = 0

    for category_row in most_borrowed_categories:

        if max_category_borrowed > 0:
            category_row["percentage"] = round(
            (
                category_row["period_borrowed"]
                / max_category_borrowed
            ) * 100
        )
        else:
            category_row["percentage"] = 0

    # ========================================================
    # LIBRARY-WISE SUMMARY
    # ========================================================

    library_data = []

    libraries = (
        Library.objects
        .filter(
            resources__id__in=resource_ids
        )
        .distinct()
        .order_by("library_name")
    )

    for library in libraries:

        library_resources = resources.filter(
            library=library
        )

        library_resource_ids = library_resources.values_list(
            "id",
            flat=True
        )

        library_copies = ResourceCopy.objects.filter(
            resource_id__in=library_resource_ids
        )

        library_transactions = period_transactions.filter(
            copy__resource__library=library
        )

        library_data.append({
            "library_name": library.library_name,
            "total_books": library_resources.count(),
            "total_copies": library_copies.count(),
            "available": library_copies.filter(
                status="AVAILABLE"
            ).count(),
            "borrowed": library_copies.filter(
                status="CHECKED_OUT"
            ).count(),
            "reserved": library_copies.filter(
                status="RESERVED"
            ).count(),
            "damaged": library_copies.filter(
                status="DAMAGED"
            ).count(),
            "lost": library_copies.filter(
                status="LOST"
            ).count(),
            "period_borrowed": library_transactions.count(),
        })

    # ========================================================
    # PENDING RESERVATIONS
    # ========================================================

    # reservations = Reservation.objects.filter(
    #     resource_id__in=resource_ids,
    #     status="PENDING",
    # )

    # reserved_requests = reservations.count()

    # ========================================================
    # PERIOD LABEL
    # ========================================================

    if start_date == end_date:

        period_label = start_date.strftime(
            "%d %B %Y"
        )

    else:

        period_label = (
            f"{start_date.strftime('%d %b %Y')} - "
            f"{end_date.strftime('%d %b %Y')}"
        )

    # ========================================================
    # CONTEXT
    # ========================================================

    context = {

        # ---------------------------------------------
        # FILTERS
        # ---------------------------------------------

        "libraries": Library.objects.filter(
            status="ACTIVE"
        ).order_by("library_name"),

        "categories": ResourceCategory.objects.filter(
            status="ACTIVE"
        ).order_by("title"),

        "selected_library": selected_library,
        "selected_category": selected_category,

        "period": period,

        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),

        "period_label": period_label,

        # ---------------------------------------------
        # INVENTORY
        # ---------------------------------------------

        "total_book_titles": total_book_titles,

        "total_copies": total_copies,

        "available_copies": available_copies,

        "borrowed_copies": borrowed_copies,

        "reserved_copies": reserved_copies,

        "damaged_copies": damaged_copies,

        "lost_copies": lost_copies,

        # "reserved_requests": reserved_requests,

        # ---------------------------------------------
        # PERIOD COUNTS
        # ---------------------------------------------

        "borrowed_today": borrowed_today,

        "borrowed_this_week": borrowed_this_week,

        "borrowed_this_month": borrowed_this_month,

        "total_borrowed_period": total_borrowed_period,

        "total_returned_period": total_returned_period,

        # ---------------------------------------------
        # CHART DATA
        # ---------------------------------------------

        "daily_data": daily_data,

        "user_type_data": user_type_data,

        # ---------------------------------------------
        # TABLE DATA
        # ---------------------------------------------

        "category_data": category_data,

        "most_borrowed_categories":
            most_borrowed_categories,

        "most_borrowed_books":
            most_borrowed_books,

        "library_data":
            library_data,
    }

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":

        return JsonResponse({
            "total_book_titles": total_book_titles,
            "total_copies": total_copies,
            "available_copies": available_copies,
            "borrowed_copies": borrowed_copies,
            "reserved_copies": reserved_copies,
            "damaged_copies": damaged_copies,
            "lost_copies": lost_copies,

            "borrowed_today": borrowed_today,
            "borrowed_this_week": borrowed_this_week,
            "borrowed_this_month": borrowed_this_month,

            "total_borrowed_period": total_borrowed_period,
            "total_returned_period": total_returned_period,

            "daily_data": daily_data,
            "user_type_data": user_type_data,

            "category_data": category_data,
            "most_borrowed_categories": most_borrowed_categories,
            "most_borrowed_books": most_borrowed_books,

            "library_data": library_data,

            "period": period,
            "period_label": period_label,

            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        })


    return render(
        request,
           "library_admin/book_management_report.html",
           context
    )

# ============================================================
# BOOK MANAGEMENT REPORT - PDF EXPORT
# ============================================================

@staff_member_required
def export_book_management_report_pdf(request):

    from datetime import datetime

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import (
        getSampleStyleSheet,
        ParagraphStyle,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        KeepTogether,
    )

    # ============================================================
    # GET FILTERED DATA
    # ============================================================

    data = _get_book_report_export_data(request)

    buffer = BytesIO()

    # ============================================================
    # PAGE SETTINGS
    # ============================================================

    PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)

    document = SimpleDocTemplate(

        buffer,

        pagesize=landscape(A4),

        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,

        title="Book Management Report",
    )

    # ============================================================
    # COLORS
    # ============================================================

    NAVY = colors.HexColor("#13294B")

    RED = colors.HexColor("#C5050C")

    LIGHT_GREY = colors.HexColor("#F3F5F7")

    BORDER = colors.HexColor("#C3CBD4")

    DARK_GREY = colors.HexColor("#5E6873")

    GREEN = colors.HexColor("#D9EAD3")

    YELLOW = colors.HexColor("#FFF2CC")

    PINK = colors.HexColor("#F4CCCC")

    WHITE = colors.white

    BLACK = colors.HexColor("#222222")

    # ============================================================
    # STYLES
    # ============================================================

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(

        "BookReportTitle",

        parent=styles["Title"],

        fontName="Helvetica-Bold",

        fontSize=20,

        leading=23,

        alignment=TA_CENTER,

        textColor=NAVY,

        spaceAfter=2,
    )

    subtitle_style = ParagraphStyle(

        "BookReportSubtitle",

        parent=styles["Normal"],

        fontName="Helvetica",

        fontSize=8.5,

        leading=10,

        alignment=TA_CENTER,

        textColor=DARK_GREY,

    )

    brand_style = ParagraphStyle(

        "BookReportBrand",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=11,

        leading=13,

        alignment=TA_LEFT,

        textColor=NAVY,

    )

    generated_label_style = ParagraphStyle(

        "GeneratedLabel",

        parent=styles["Normal"],

        fontName="Helvetica",

        fontSize=7.5,

        leading=9,

        alignment=TA_RIGHT,

        textColor=DARK_GREY,

    )

    generated_value_style = ParagraphStyle(

        "GeneratedValue",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=8.5,

        leading=10,

        alignment=TA_RIGHT,

        textColor=NAVY,

    )

    section_style = ParagraphStyle(

        "BookReportSection",

        parent=styles["Heading2"],

        fontName="Helvetica-Bold",

        fontSize=10.5,

        leading=13,

        alignment=TA_LEFT,

        textColor=NAVY,

        spaceBefore=2,

        spaceAfter=5,
    )

    center_section_style = ParagraphStyle(

        "BookReportCenterSection",

        parent=section_style,

        alignment=TA_CENTER,
    )

    table_header_style = ParagraphStyle(

        "BookReportHeader",

        parent=styles["Normal"],

        fontName="Helvetica-Bold",

        fontSize=6.8,

        leading=8,

        alignment=TA_CENTER,

        textColor=WHITE,
    )

    table_cell_style = ParagraphStyle(

        "BookReportCell",

        parent=styles["Normal"],

        fontName="Helvetica",

        fontSize=6.8,

        leading=8,

        alignment=TA_CENTER,

        textColor=BLACK,
    )

    small_cell_style = ParagraphStyle(

        "BookReportSmallCell",

        parent=styles["Normal"],

        fontName="Helvetica",

        fontSize=6.2,

        leading=7.2,

        alignment=TA_CENTER,

        textColor=BLACK,
    )

    period_style = ParagraphStyle(

        "BookReportPeriod",

        parent=styles["Normal"],

        fontName="Helvetica",

        fontSize=8.5,

        leading=10,

        alignment=TA_CENTER,

        textColor=DARK_GREY,

        spaceAfter=5,
    )

    footer_style = ParagraphStyle(

        "BookReportFooter",

        parent=styles["Normal"],

        fontName="Helvetica",

        fontSize=7,

        leading=8,

        alignment=TA_CENTER,

        textColor=DARK_GREY,
    )

    # ============================================================
    # HELPERS
    # ============================================================

    def P(value, style=table_cell_style):

        if value in (None, ""):

            value = "—"

        return Paragraph(
            str(value),
            style,
        )

    def header_row(headers):

        return [

            Paragraph(
                str(header),
                table_header_style
            )

            for header in headers
        ]

    def common_table_style():

        return TableStyle([

            # Header
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                NAVY,
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                WHITE,
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),

            # Borders
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.45,
                BORDER,
            ),

            # Alignment
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER",
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),

            # Alternating rows
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    WHITE,
                    LIGHT_GREY,
                ],
            ),

            # Padding
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                4,
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4,
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                3,
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                3,
            ),
        ])

    # ============================================================
    # STORY
    # ============================================================

    story = []

    # ============================================================
    # PROFESSIONAL HEADER
    # ============================================================

    generated_date = datetime.now().strftime(
        "%d %b %Y, %I:%M %p"
    )

    header = Table(

        [
            [

                Paragraph(
                    "<b>WISCONSIN</b><br/>"
                    "<font size='8'>LIBRARIES</font>",
                    brand_style,
                ),

                [
                    Paragraph(
                        "BOOK MANAGEMENT REPORT",
                        title_style,
                    ),

                    Paragraph(
                        "Library Book Stock & Management",
                        subtitle_style,
                    ),
                ],

                [
                    Paragraph(
                        "GENERATED",
                        generated_label_style,
                    ),

                    Paragraph(
                        generated_date,
                        generated_value_style,
                    ),
                ],
            ]
        ],

        colWidths=[
            55 * mm,
            145 * mm,
            55 * mm,
        ],
    )

    header.setStyle(
        TableStyle([

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),

            (
                "ALIGN",
                (0, 0),
                (0, 0),
                "LEFT",
            ),

            (
                "ALIGN",
                (1, 0),
                (1, 0),
                "CENTER",
            ),

            (
                "ALIGN",
                (2, 0),
                (2, 0),
                "RIGHT",
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
        ])
    )

    story.append(header)

    story.append(
        Spacer(1, 6)
    )

    # ============================================================
    # NAVY DIVIDER
    # ============================================================

    divider = Table(
        [[""]],
        colWidths=[253 * mm],
        rowHeights=[3 * mm],
    )

    divider.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                NAVY,
            ),

            (
                "BOX",
                (0, 0),
                (-1, -1),
                0,
                NAVY,
            ),
        ])
    )

    divider.hAlign = "CENTER"

    story.append(divider)

    story.append(
        Spacer(1, 8)
    )

    # ============================================================
    # REPORTING PERIOD
    # ============================================================

    story.append(
        Paragraph(
            f"<b>Reporting Period:</b> "
            f"{data['period_label']}",
            period_style,
        )
    )

    # ============================================================
    # FILTER INFORMATION
    # ============================================================

    filter_text = []

    if data.get("selected_library"):

        try:

            library = Library.objects.get(
                id=data["selected_library"]
            )

            filter_text.append(
                f"Library: {library.library_name}"
            )

        except Library.DoesNotExist:

            pass

    if data.get("selected_category"):

        try:

            category = ResourceCategory.objects.get(
                id=data["selected_category"]
            )

            filter_text.append(
                f"Category: {category.title}"
            )

        except ResourceCategory.DoesNotExist:

            pass

    if filter_text:

        story.append(
            Paragraph(
                " | ".join(filter_text),
                period_style,
            )
        )

    # ============================================================
    # SUMMARY SECTION
    # INVENTORY LEFT / BORROWING RIGHT
    # ============================================================

    inventory_title = Paragraph(
        "Inventory Summary",
        section_style,
    )

    borrowing_title = Paragraph(
        "Borrowing Summary",
        section_style,
    )

    inventory_data = [

        header_row([
            "Metric",
            "Count",
        ]),

        [
            P("Book Titles"),
            P(data["total_book_titles"]),
        ],

        [
            P("Total Copies"),
            P(data["total_copies"]),
        ],

        [
            P("Available"),
            P(data["available_copies"]),
        ],

        [
            P("Borrowed"),
            P(data["borrowed_copies"]),
        ],

        [
            P("Reserved"),
            P(data["reserved_copies"]),
        ],

        [
            P("Damaged"),
            P(data["damaged_copies"]),
        ],

        [
            P("Lost"),
            P(data["lost_copies"]),
        ],
    ]

    inventory_table = Table(

        inventory_data,

        colWidths=[
            48 * mm,
            22 * mm,
        ],
    )

    inventory_table.hAlign = "CENTER"

    inventory_table.setStyle(
        common_table_style()
    )

    borrowing_data = [

        header_row([
            "Metric",
            "Count",
        ]),

        [
            P("Books Borrowed During Period"),
            P(data["total_borrowed_period"]),
        ],

        [
            P("Books Returned During Period"),
            P(data["total_returned_period"]),
        ],
    ]

    borrowing_table = Table(

        borrowing_data,

        colWidths=[
            58 * mm,
            22 * mm,
        ],
    )

    borrowing_table.hAlign = "CENTER"

    borrowing_table.setStyle(
        common_table_style()
    )

    # ============================================================
    # SUMMARY CARDS
    # ============================================================

    left_card = Table(

        [
            [inventory_title],
            [inventory_table],
        ],

        colWidths=[
            82 * mm
        ],
    )

    left_card.setStyle(
        TableStyle([

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER",
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                2,
            ),
        ])
    )

    right_card = Table(

        [
            [borrowing_title],
            [borrowing_table],
        ],

        colWidths=[
            82 * mm
        ],
    )

    right_card.setStyle(
        TableStyle([

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER",
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                2,
            ),
        ])
    )

    summary_wrapper = Table(

        [
            [
                left_card,
                right_card,
            ]
        ],

        colWidths=[
            120 * mm,
            120 * mm,
        ],
    )

    summary_wrapper.hAlign = "CENTER"

    summary_wrapper.setStyle(
        TableStyle([

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER",
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0,
            ),
        ])
    )

    story.append(
        summary_wrapper
    )

    story.append(
        Spacer(1, 12)
    )

    # ============================================================
    # BOOK STOCK DETAILS
    # ============================================================

    story.append(
        Paragraph(
            "Book Stock Details",
            section_style,
        )
    )

    stock_headers = [

        "Book",
        "Author",
        "ISBN",
        "Category",
        "Library",
        "Total",
        "Available",
        "Borrowed",
        "Reserved",
        "Damaged",
        "Lost",
        "Stock Status",
    ]

    stock_data = [
        header_row(stock_headers)
    ]

    for row in data.get(
        "stock_details",
        []
    ):

        stock_data.append([

            P(
                row["book"],
                small_cell_style
            ),

            P(
                row["author"],
                small_cell_style
            ),

            P(
                row["isbn"],
                small_cell_style
            ),

            P(
                row["category"],
                small_cell_style
            ),

            P(
                row["library"],
                small_cell_style
            ),

            P(
                row["total"],
                small_cell_style
            ),

            P(
                row["available"],
                small_cell_style
            ),

            P(
                row["borrowed"],
                small_cell_style
            ),

            P(
                row["reserved"],
                small_cell_style
            ),

            P(
                row["damaged"],
                small_cell_style
            ),

            P(
                row["lost"],
                small_cell_style
            ),

            P(
                row["stock_status"],
                small_cell_style
            ),
        ])

    if len(stock_data) == 1:

        stock_data.append([

            P(
                "No book stock records found."
            )
        ] + [""] * 11)

    stock_table = Table(

        stock_data,

        colWidths=[

            29 * mm,
            24 * mm,
            18 * mm,
            22 * mm,
            27 * mm,
            13 * mm,
            16 * mm,
            16 * mm,
            16 * mm,
            16 * mm,
            13 * mm,
            24 * mm,
        ],

        repeatRows=1,
    )

    stock_table.hAlign = "CENTER"

    stock_style = common_table_style()

    # Available status
    for row_index, row in enumerate(
        data.get("stock_details", []),
        start=1
    ):

        status = row["stock_status"]

        if status == "AVAILABLE":

            stock_style.add(
                "BACKGROUND",
                (11, row_index),
                (11, row_index),
                GREEN,
            )

        elif status == "LOW STOCK":

            stock_style.add(
                "BACKGROUND",
                (11, row_index),
                (11, row_index),
                YELLOW,
            )

        else:

            stock_style.add(
                "BACKGROUND",
                (11, row_index),
                (11, row_index),
                PINK,
            )

    stock_table.setStyle(
        stock_style
    )

    story.append(
        stock_table
    )

    story.append(
        Spacer(1, 12)
    )

    # ============================================================
    # BOOKS BY CATEGORY
    # ============================================================

    if data.get("category_data"):

        story.append(
            Paragraph(
                "Books by Category",
                section_style,
            )
        )

        category_data = [

            header_row([
                "Category",
                "Book Titles",
                "Copies",
                "Available",
                "Borrowed",
            ])
        ]

        for row in data["category_data"]:

            category_data.append([

                P(row["title"]),

                P(row["total_books"]),

                P(row["total_copies"]),

                P(row["available"]),

                P(row["borrowed"]),
            ])

        category_table = Table(

            category_data,

            colWidths=[
                55 * mm,
                30 * mm,
                25 * mm,
                30 * mm,
                30 * mm,
            ],
        )

        category_table.hAlign = "CENTER"

        category_table.setStyle(
            common_table_style()
        )

        story.append(
            category_table
        )

        story.append(
            Spacer(1, 10)
        )

    # ============================================================
    # MOST BORROWED BOOKS
    # ============================================================

    if data.get("most_borrowed_books"):

        story.append(
            Paragraph(
                "Most Borrowed Books",
                section_style,
            )
        )

        most_data = [

            header_row([
                "Rank",
                "Book",
                "Author",
                "Category",
                "Library",
                "Times Borrowed",
            ])
        ]

        for index, row in enumerate(
            data["most_borrowed_books"],
            start=1
        ):

            most_data.append([

                P(index),

                P(row["title"]),

                P(row["author"]),

                P(row["category"]),

                P(row["library"]),

                P(row["borrowed"]),
            ])

        most_table = Table(

            most_data,

            colWidths=[
                15 * mm,
                40 * mm,
                35 * mm,
                35 * mm,
                40 * mm,
                30 * mm,
            ],

            repeatRows=1,
        )

        most_table.hAlign = "CENTER"

        most_table.setStyle(
            common_table_style()
        )

        story.append(
            most_table
        )

        story.append(
            Spacer(1, 10)
        )

    # ============================================================
    # PERIOD BORROWING DETAILS
    # ============================================================

    story.append(
        Paragraph(
            f"{data['period_name']} Borrowing Details",
            section_style,
        )
    )

    detail_headers = [

        "Date",
        "Day",
        "Book",
        "Author",
        "Category",
        "Library",
        "User",
        "User Type",
        "Issue",
        "Due",
        "Return",
        "Status",
    ]

    detail_data = [
        header_row(detail_headers)
    ]

    for row in data.get(
        "borrowing_details",
        []
    ):

        detail_data.append([

            P(
                row["date"],
                small_cell_style
            ),

            P(
                row["day"],
                small_cell_style
            ),

            P(
                row["book"],
                small_cell_style
            ),

            P(
                row["author"],
                small_cell_style
            ),

            P(
                row["category"],
                small_cell_style
            ),

            P(
                row["library"],
                small_cell_style
            ),

            P(
                row["user"],
                small_cell_style
            ),

            P(
                row["user_type"],
                small_cell_style
            ),

            P(
                row["issue_date"],
                small_cell_style
            ),

            P(
                row["due_date"],
                small_cell_style
            ),

            P(
                row["return_date"],
                small_cell_style
            ),

            P(
                row["status"],
                small_cell_style
            ),
        ])

    if len(detail_data) == 1:

        detail_data.append([

            P(
                "No borrowing records found "
                "for this period."
            )

        ] + [""] * 11)

    detail_table = Table(

        detail_data,

        colWidths=[

            18 * mm,
            12 * mm,
            28 * mm,
            24 * mm,
            22 * mm,
            27 * mm,
            27 * mm,
            21 * mm,
            18 * mm,
            18 * mm,
            18 * mm,
            22 * mm,
        ],

        repeatRows=1,
    )

    detail_table.hAlign = "CENTER"

    detail_table.setStyle(
        common_table_style()
    )

    story.append(
        detail_table
    )

    # ============================================================
    # FOOTER
    # ============================================================

    story.append(
        Spacer(1, 10)
    )

    footer_line = Table(
        [[""]],
        colWidths=[253 * mm],
        rowHeights=[0.5 * mm],
    )

    footer_line.hAlign = "CENTER"

    footer_line.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                BORDER,
            ),
        ])
    )

    story.append(
        footer_line
    )

    story.append(
        Spacer(1, 4)
    )

    story.append(
        Paragraph(
            "Wisconsin Libraries • Book Management System",
            footer_style,
        )
    )

    # ============================================================
    # BUILD
    # ============================================================

    document.build(
        story
    )

    buffer.seek(0)

    filename = (

        "book_management_report_"

        f"{data['period']}_"

        f"{data['start_date']}_"

        f"{data['end_date']}.pdf"
    )

    response = HttpResponse(

        buffer.getvalue(),

        content_type="application/pdf",
    )

    response["Content-Disposition"] = (

        f'attachment; filename="{filename}"'
    )

    return response


# ============================================================
# SHARED REPORT DATA FOR PDF / EXCEL
# ============================================================

def _get_book_report_export_data(request):
    """
    Returns ONLY the data required for PDF / Excel export.

    The selected period is respected:
        today -> today's records
        week  -> current week's records
        month -> current month's records
        custom -> selected date range

    Library and Category filters are also respected.
    """

    today = date.today()

    # ============================================================
    # FILTERS
    # ============================================================

    period = request.GET.get("period", "month").strip()

    selected_library = request.GET.get(
        "library",
        ""
    ).strip()

    selected_category = request.GET.get(
        "category",
        ""
    ).strip()

    start_value = request.GET.get(
        "start_date",
        ""
    ).strip()

    end_value = request.GET.get(
        "end_date",
        ""
    ).strip()

    # ============================================================
    # DATE RANGE
    # ============================================================

    if period == "today":

        start_date = today
        end_date = today

    elif period == "week":

        # Monday -> Sunday
        start_date = (
            today -
            timedelta(days=today.weekday())
        )

        end_date = start_date + timedelta(days=6)

    elif period == "custom":

        try:

            start_date = date.fromisoformat(
                start_value
            )

            end_date = date.fromisoformat(
                end_value
            )

            if start_date > end_date:
                start_date, end_date = (
                    end_date,
                    start_date
                )

        except (ValueError, TypeError):

            start_date = today.replace(day=1)
            end_date = today
            period = "month"

    else:

        # Default = current month
        start_date = today.replace(day=1)
        end_date = today
        period = "month"

    # ============================================================
    # BOOK RESOURCES
    # ============================================================

    resources = (
        LibraryResource.objects
        .select_related(
            "library",
            "category"
        )
        .filter(
            resource_type="BOOK"
        )
    )

    # ============================================================
    # LIBRARY FILTER
    # ============================================================

    if selected_library:

        resources = resources.filter(
            library_id=selected_library
        )

    # ============================================================
    # CATEGORY FILTER
    # ============================================================

    if selected_category:

        resources = resources.filter(
            category_id=selected_category
        )

    resource_ids = resources.values_list(
        "id",
        flat=True
    )

    # ============================================================
    # COPIES
    # ============================================================

    copies = ResourceCopy.objects.filter(
        resource_id__in=resource_ids
    )

    # ============================================================
    # ALL TRANSACTIONS
    # ============================================================

    transactions = (
        BorrowTransaction.objects
        .select_related(
            "copy",
            "copy__resource",
            "copy__resource__library",
            "copy__resource__category",
            "library_user",
            "library_user__user",
        )
        .filter(
            copy__resource_id__in=resource_ids
        )
    )

    # ============================================================
    # ONLY SELECTED PERIOD
    # ============================================================

    period_transactions = transactions.filter(
        issue_date__gte=start_date,
        issue_date__lte=end_date,
    ).order_by(
        "-issue_date"
    )

    # ============================================================
    # INVENTORY COUNTS
    #
    # These are CURRENT inventory values.
    # They are not historical values.
    # ============================================================

    total_book_titles = resources.count()

    total_copies = copies.count()

    available_copies = copies.filter(
        status="AVAILABLE"
    ).count()

    borrowed_copies = copies.filter(
        status="CHECKED_OUT"
    ).count()

    reserved_copies = copies.filter(
        status="RESERVED"
    ).count()

    damaged_copies = copies.filter(
        status="DAMAGED"
    ).count()

    lost_copies = copies.filter(
        status="LOST"
    ).count()

    # ============================================================
    # PERIOD RETURN COUNT
    # ============================================================

    total_returned_period = transactions.filter(
        return_date__gte=start_date,
        return_date__lte=end_date,
        status="RETURNED",
    ).count()

    # ============================================================
    # PERIOD USER TYPE DATA
    # ============================================================

    user_type_data = []

    for value, label in LibraryUser.USER_TYPES:

        user_type_data.append({
            "label": label,
            "count": period_transactions.filter(
                library_user__user_type=value
            ).count(),
        })

    # ============================================================
    # DETAILED BORROWING DATA
    #
    # THIS IS THE IMPORTANT PART FOR EXCEL + PDF
    # ============================================================

    borrowing_details = []

    for transaction in period_transactions:

        resource = transaction.copy.resource

        # --------------------------------------------------------
        # USER
        # --------------------------------------------------------

        user_name = "—"
        user_email = ""

        library_user = getattr(
            transaction,
            "library_user",
            None
        )

        if library_user:

            user = getattr(
                library_user,
                "user",
                None
            )

            if user:

                if hasattr(
                    user,
                    "get_full_name"
                ):

                    user_name = (
                        user.get_full_name()
                        or getattr(
                            user,
                            "username",
                            "—"
                        )
                    )

                else:

                    user_name = getattr(
                        user,
                        "username",
                        "—"
                    )

                user_email = getattr(
                    user,
                    "email",
                    ""
                )

            else:

                user_name = str(
                    library_user
                )

        # --------------------------------------------------------
        # USER TYPE
        # --------------------------------------------------------

        user_type = getattr(
            library_user,
            "user_type",
            "—"
        )

        # Convert choice value to readable label
        try:

            user_type_display = (
                library_user.get_user_type_display()
            )

        except Exception:

            user_type_display = user_type

        # --------------------------------------------------------
        # ISSUE DATE
        # --------------------------------------------------------

        issue_date = getattr(
            transaction,
            "issue_date",
            None
        )

        # --------------------------------------------------------
        # RETURN DATE
        # --------------------------------------------------------

        return_date = getattr(
            transaction,
            "return_date",
            None
        )

        # --------------------------------------------------------
        # DUE DATE
        #
        # Only use it if your BorrowTransaction model has it.
        # --------------------------------------------------------

        due_date = getattr(
            transaction,
            "due_date",
            None
        )

        # --------------------------------------------------------
        # STATUS
        # --------------------------------------------------------

        try:

            status_display = (
                transaction.get_status_display()
            )

        except Exception:

            status_display = getattr(
                transaction,
                "status",
                "—"
            )

        borrowing_details.append({

            "date":
                issue_date.strftime("%d-%m-%Y")
                if issue_date
                else "—",

            "day":
                issue_date.strftime("%a")
                if issue_date
                else "—",

            "book":
                resource.title
                if resource
                else "—",

            "author":
                getattr(
                    resource,
                    "author",
                    ""
                )
                or "—",

            "category":
                (
                    resource.category.title
                    if resource.category
                    else "Uncategorized"
                ),

            "library":
                (
                    resource.library.library_name
                    if resource.library
                    else "—"
                ),

            "user":
                user_name,

            "email":
                user_email,

            "user_type":
                user_type_display,

            "issue_date":
                issue_date.strftime("%d-%m-%Y")
                if issue_date
                else "—",

            "due_date":
                due_date.strftime("%d-%m-%Y")
                if due_date
                else "—",

            "return_date":
                return_date.strftime("%d-%m-%Y")
                if return_date
                else "—",

            "status":
                status_display,
        })

    # ============================================================
    # PERIOD LABEL
    # ============================================================

    if period == "today":

        period_name = "Today"

    elif period == "week":

        period_name = "This Week"

    elif period == "month":

        period_name = "This Month"

    elif period == "custom":

        period_name = "Custom Range"

    else:

        period_name = "This Month"

    if start_date == end_date:

        period_label = (
            f"{period_name} - "
            f"{start_date.strftime('%d %B %Y')}"
        )

    else:

        period_label = (
            f"{period_name} - "
            f"{start_date.strftime('%d %b %Y')} "
            f"to "
            f"{end_date.strftime('%d %b %Y')}"
        )

    # ============================================================
    # BOOK STOCK DETAILS
    #
    # One row for each book.
    # This is CURRENT stock, not period-filtered stock.
    # ============================================================

    stock_details = []

    for resource in resources:

        book_copies = ResourceCopy.objects.filter(
            resource_id=resource.id
        )

        total = book_copies.count()

        available = book_copies.filter(
            status="AVAILABLE"
        ).count()

        borrowed = book_copies.filter(
            status="CHECKED_OUT"
        ).count()

        reserved = book_copies.filter(
            status="RESERVED"
        ).count()

        damaged = book_copies.filter(
            status="DAMAGED"
        ).count()

        lost = book_copies.filter(
            status="LOST"
        ).count()

        # --------------------------------------------------------
        # STOCK STATUS
        # --------------------------------------------------------

        if total == 0:

            stock_status = "NO STOCK"

        elif available == 0:

            stock_status = "OUT OF STOCK"

        elif available <= 2:

            stock_status = "LOW STOCK"

        else:

            stock_status = "AVAILABLE"

        stock_details.append({

            "book":
                resource.title,

            "author":
                resource.author or "—",

            "isbn":
                getattr(
                    resource,
                    "isbn_issn",
                    ""
                ) or "—",

            "category":
                (
                    resource.category.title
                    if resource.category
                    else "Uncategorized"
                ),

            "library":
                (
                    resource.library.library_name
                    if resource.library
                    else "—"
                ),

            "total":
                total,

            "available":
                available,

            "borrowed":
                borrowed,

            "reserved":
                reserved,

            "damaged":
                damaged,

            "lost":
                lost,

            "stock_status":
                stock_status,
        })

    # ============================================================
    # RETURN DATA
    # ============================================================

    return {

        "period":
            period,

        "period_name":
            period_name,

        "period_label":
            period_label,

        "start_date":
            start_date.isoformat(),

        "end_date":
            end_date.isoformat(),

        "selected_library":
            selected_library,

        "selected_category":
            selected_category,

        "total_book_titles":
            total_book_titles,

        "total_copies":
            total_copies,

        "available_copies":
            available_copies,

        "borrowed_copies":
            borrowed_copies,

        "reserved_copies":
            reserved_copies,

        "damaged_copies":
            damaged_copies,

        "lost_copies":
            lost_copies,

        "total_borrowed_period":
            period_transactions.count(),

        "total_returned_period":
            total_returned_period,

        "user_type_data":
            user_type_data,

        "borrowing_details":
            borrowing_details,

        "stock_details": stock_details,
    }

# ============================================================
# BOOK MANAGEMENT REPORT - EXCEL EXPORT
# ============================================================

@staff_member_required
def export_book_management_report_excel(request):

    data = _get_book_report_export_data(request)

    workbook = openpyxl.Workbook()

    ws = workbook.active
    ws.title = "Book Management Report"

    # ============================================================
    # COLORS
    # ============================================================

    NAVY = "13294B"
    RED = "C5050C"
    LIGHT_GREY = "F5F6F7"
    BORDER_GREY = "B7B7B7"
    WHITE = "FFFFFF"

    GREEN = "C6EFCE"
    YELLOW = "FFF2CC"
    PINK = "FFC7CE"

    # ============================================================
    # FONTS
    # ============================================================

    title_font = Font(
        bold=True,
        size=18,
    )

    section_font = Font(
        bold=True,
        size=12,
    )

    header_font = Font(
        bold=True,
        color=WHITE,
        size=10,
    )

    normal_font = Font(
        size=10,
    )

    # ============================================================
    # FILLS
    # ============================================================

    navy_fill = PatternFill(
        start_color=NAVY,
        end_color=NAVY,
        fill_type="solid",
    )

    red_fill = PatternFill(
        start_color=RED,
        end_color=RED,
        fill_type="solid",
    )

    grey_fill = PatternFill(
        start_color=LIGHT_GREY,
        end_color=LIGHT_GREY,
        fill_type="solid",
    )

    green_fill = PatternFill(
        start_color=GREEN,
        end_color=GREEN,
        fill_type="solid",
    )

    yellow_fill = PatternFill(
        start_color=YELLOW,
        end_color=YELLOW,
        fill_type="solid",
    )

    pink_fill = PatternFill(
        start_color=PINK,
        end_color=PINK,
        fill_type="solid",
    )

    # ============================================================
    # BORDER
    # ============================================================

    from openpyxl.styles import Border, Side

    thin = Side(
        style="thin",
        color=BORDER_GREY,
    )

    border = Border(
        left=thin,
        right=thin,
        top=thin,
        bottom=thin,
    )

    # ============================================================
    # HELPER: SECTION TITLE
    # ============================================================

    def section_title(
        row,
        title,
        end_column
    ):

        ws.merge_cells(
            start_row=row,
            start_column=1,
            end_row=row,
            end_column=end_column,
        )

        cell = ws.cell(
            row=row,
            column=1,
        )

        cell.value = title

        cell.fill = red_fill

        cell.font = Font(
            bold=True,
            color=WHITE,
            size=11,
        )

        cell.alignment = Alignment(
            horizontal="left",
            vertical="center",
        )

        return row + 1

    # ============================================================
    # HELPER: TABLE HEADER
    # ============================================================

    def table_header(
        row,
        headers
    ):

        for column, value in enumerate(
            headers,
            start=1
        ):

            cell = ws.cell(
                row=row,
                column=column
            )

            cell.value = value

            cell.fill = navy_fill

            cell.font = header_font

            cell.border = border

            cell.alignment = Alignment(
                horizontal="center",
                vertical="center",
                wrap_text=True,
            )

        ws.row_dimensions[row].height = 30

    # ============================================================
    # HELPER: DATA CELL
    # ============================================================

    def data_cell(
        row,
        column,
        value,
        alternate=False
    ):

        cell = ws.cell(
            row=row,
            column=column
        )

        cell.value = value

        cell.font = normal_font

        cell.border = border

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )

        if alternate:
            cell.fill = grey_fill

        return cell

    # ============================================================
    # TITLE
    # ============================================================

    ws.merge_cells("A1:L1")

    ws["A1"] = "BOOK MANAGEMENT REPORT"

    ws["A1"].font = title_font

    ws["A1"].alignment = Alignment(
        horizontal="center",
        vertical="center",
    )

    ws.row_dimensions[1].height = 32

    # ============================================================
    # REPORTING PERIOD
    # ============================================================

    ws["A2"] = "Reporting Period"

    ws["A2"].font = Font(
        bold=True,
        size=10,
    )

    ws.merge_cells("B2:L2")

    ws["B2"] = data["period_label"]

    ws["B2"].font = Font(
        bold=True,
        size=10,
    )

    current_row = 4

    # ============================================================
    # FILTER INFORMATION
    # ============================================================

    if data.get("selected_library"):

        try:

            library = Library.objects.get(
                id=data["selected_library"]
            )

            ws.cell(
                row=current_row,
                column=1
            ).value = "Library"

            ws.cell(
                row=current_row,
                column=2
            ).value = library.library_name

            ws.cell(
                row=current_row,
                column=1
            ).font = Font(
                bold=True
            )

            current_row += 1

        except Library.DoesNotExist:

            pass

    if data.get("selected_category"):

        try:

            category = ResourceCategory.objects.get(
                id=data["selected_category"]
            )

            ws.cell(
                row=current_row,
                column=1
            ).value = "Category"

            ws.cell(
                row=current_row,
                column=2
            ).value = category.title

            ws.cell(
                row=current_row,
                column=1
            ).font = Font(
                bold=True
            )

            current_row += 1

        except ResourceCategory.DoesNotExist:

            pass

    # ============================================================
    # 1. INVENTORY SUMMARY
    # ============================================================

    current_row += 1

    current_row = section_title(
        current_row,
        "Inventory Summary",
        7,
    )

    inventory_headers = [

        "Book Titles",
        "Total Copies",
        "Available",
        "Borrowed",
        "Reserved",
        "Damaged",
        "Lost",
    ]

    table_header(
        current_row,
        inventory_headers
    )

    current_row += 1

    inventory_values = [

        data["total_book_titles"],

        data["total_copies"],

        data["available_copies"],

        data["borrowed_copies"],

        data["reserved_copies"],

        data["damaged_copies"],

        data["lost_copies"],
    ]

    for column, value in enumerate(
        inventory_values,
        start=1
    ):

        data_cell(
            current_row,
            column,
            value,
        )

    current_row += 2

    # ============================================================
    # 2. BOOK STOCK DETAILS
    # ============================================================

    current_row = section_title(
        current_row,
        "Book Stock Details",
        12,
    )

    stock_headers = [

        "Book",

        "Author",

        "ISBN",

        "Category",

        "Library",

        "Total Copies",

        "Available",

        "Borrowed",

        "Reserved",

        "Damaged",

        "Lost",

        "Stock Status",
    ]

    stock_header_row = current_row

    table_header(
        current_row,
        stock_headers
    )

    current_row += 1

    stock_first_row = current_row

    for index, row in enumerate(
        data.get(
            "stock_details",
            []
        )
    ):

        alternate = (
            index % 2 == 1
        )

        values = [

            row["book"],

            row["author"],

            row["isbn"],

            row["category"],

            row["library"],

            row["total"],

            row["available"],

            row["borrowed"],

            row["reserved"],

            row["damaged"],

            row["lost"],

            row["stock_status"],
        ]

        for column, value in enumerate(
            values,
            start=1
        ):

            data_cell(
                current_row,
                column,
                value,
                alternate,
            )

        # --------------------------------------------------------
        # STATUS COLOR
        # --------------------------------------------------------

        status_cell = ws.cell(
            row=current_row,
            column=12
        )

        status = row["stock_status"]

        if status == "AVAILABLE":

            status_cell.fill = green_fill

        elif status == "LOW STOCK":

            status_cell.fill = yellow_fill

        else:

            status_cell.fill = pink_fill

        current_row += 1

    if not data.get("stock_details"):

        ws.merge_cells(
            start_row=current_row,
            start_column=1,
            end_row=current_row,
            end_column=12,
        )

        ws.cell(
            row=current_row,
            column=1
        ).value = (
            "No book stock records found."
        )

        ws.cell(
            row=current_row,
            column=1
        ).alignment = Alignment(
            horizontal="center"
        )

        current_row += 1

    # ============================================================
    # 5. BOOKS BY CATEGORY
    # ============================================================

    if data.get("category_data"):

        current_row += 2

        current_row = section_title(
            current_row,
            "Books by Category",
            5,
        )

        category_headers = [

            "Category",

            "Book Titles",

            "Copies",

            "Available",

            "Borrowed",
        ]

        table_header(
            current_row,
            category_headers
        )

        current_row += 1

        for index, row in enumerate(
            data["category_data"]
        ):

            values = [

                row["title"],

                row["total_books"],

                row["total_copies"],

                row["available"],

                row["borrowed"],
            ]

            for column, value in enumerate(
                values,
                start=1
            ):

                data_cell(
                    current_row,
                    column,
                    value,
                    index % 2 == 1,
                )

            current_row += 1

    # ============================================================
    # 6. MOST BORROWED BOOKS
    # ============================================================

    if data.get("most_borrowed_books"):

        current_row += 2

        current_row = section_title(
            current_row,
            "Most Borrowed Books",
            6,
        )

        most_headers = [

            "Rank",

            "Book",

            "Author",

            "Category",

            "Library",

            "Times Borrowed",
        ]

        table_header(
            current_row,
            most_headers
        )

        current_row += 1

        for index, row in enumerate(
            data["most_borrowed_books"],
            start=1
        ):

            values = [

                index,

                row["title"],

                row["author"],

                row["category"],

                row["library"],

                row["borrowed"],
            ]

            for column, value in enumerate(
                values,
                start=1
            ):

                data_cell(
                    current_row,
                    column,
                    value,
                    index % 2 == 0,
                )

            current_row += 1

    # ============================================================
    # 7. PERIOD BORROWING DETAILS
    # ============================================================

    current_row += 2

    current_row = section_title(
        current_row,
        f"{data['period_name']} Borrowing Details",
        12,
    )

    detail_headers = [

        "Date",

        "Day",

        "Book",

        "Author",

        "Category",

        "Library",

        "User",

        "User Type",

        "Issue Date",

        "Due Date",

        "Return Date",

        "Status",
    ]

    detail_header_row = current_row

    table_header(
        current_row,
        detail_headers
    )

    current_row += 1

    detail_first_row = current_row

    details = data.get(
        "borrowing_details",
        []
    )

    for index, row in enumerate(
        details
    ):

        values = [

            row["date"],

            row["day"],

            row["book"],

            row["author"],

            row["category"],

            row["library"],

            row["user"],

            row["user_type"],

            row["issue_date"],

            row["due_date"],

            row["return_date"],

            row["status"],
        ]

        for column, value in enumerate(
            values,
            start=1
        ):

            data_cell(
                current_row,
                column,
                value,
                index % 2 == 1,
            )

        current_row += 1

    if not details:

        ws.merge_cells(
            start_row=current_row,
            start_column=1,
            end_row=current_row,
            end_column=12,
        )

        ws.cell(
            row=current_row,
            column=1
        ).value = (
            "No borrowing records found "
            "for this period."
        )

        ws.cell(
            row=current_row,
            column=1
        ).alignment = Alignment(
            horizontal="center"
        )

    # ============================================================
    # COLUMN WIDTHS
    # ============================================================

    widths = {

        "A": 18,
        "B": 22,
        "C": 25,
        "D": 22,
        "E": 22,
        "F": 16,
        "G": 24,
        "H": 16,
        "I": 16,
        "J": 16,
        "K": 16,
        "L": 18,
    }

    for column, width in widths.items():

        ws.column_dimensions[
            column
        ].width = width

    # ============================================================
    # GENERAL FORMATTING
    # ============================================================

    ws.sheet_view.showGridLines = False

    # ============================================================
    # FREEZE
    # ============================================================

    # Keep title + reporting period visible
    ws.freeze_panes = "A3"

    # ============================================================
    # PAGE SETUP
    # ============================================================

    ws.page_setup.orientation = "landscape"

    ws.page_setup.paperSize = (
        ws.PAPERSIZE_A4
    )

    ws.page_setup.fitToWidth = 1

    ws.page_setup.fitToHeight = 0

    ws.sheet_properties.pageSetUpPr.fitToPage = True

    ws.page_margins.left = 0.25
    ws.page_margins.right = 0.25
    ws.page_margins.top = 0.5
    ws.page_margins.bottom = 0.5

    # Repeat title when printing
    ws.print_title_rows = "1:2"

    # ============================================================
    # SAVE
    # ============================================================

    buffer = BytesIO()

    workbook.save(
        buffer
    )

    buffer.seek(0)

    filename = (
        "book_management_report_"
        f"{data['period']}_"
        f"{data['start_date']}_"
        f"{data['end_date']}.xlsx"
    )

    response = HttpResponse(
        buffer.getvalue(),
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"'
    )

    return response

from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from Library.models import (
    LibraryUser,
    BorrowTransaction,
)

# ============================================================
# MEMBERS PAGE
# ============================================================

@login_required
def library_members(request):

    return render(
        request,
        "library_admin/library_members.html",
    )

# ============================================================
# MEMBERS AJAX
# ============================================================

@login_required
def library_members_ajax(request):

    # ========================================================
    # TODAY
    # ========================================================

    today = timezone.localdate()


    # ========================================================
    # GET PARAMETERS
    # ========================================================

    search = request.GET.get(
        "search",
        ""
    ).strip()


    member_type = request.GET.get(
        "type",
        "ALL"
    ).upper()


    status_filter = request.GET.get(
        "status",
        "ALL"
    ).upper()


    period = request.GET.get(
        "period",
        "TODAY"
    ).upper()


    page_number = request.GET.get(
        "page",
        "1"
    )


    # ========================================================
    # PERIOD
    # ========================================================

    if period == "WEEK":

        start_date = (
            today - timedelta(days=6)
        )

    elif period == "MONTH":

        start_date = (
            today - timedelta(days=29)
        )

    else:

        period = "TODAY"

        start_date = today


    end_date = today


    # ========================================================
    # ALL MEMBERS BASE QUERY
    # ========================================================

    members = (
        LibraryUser.objects
        .select_related("user")
        .order_by(
            "user__first_name",
            "user__last_name",
            "user__username",
        )
    )


    # ========================================================
    # LIVE SEARCH
    # ========================================================

    if search:

        members = members.filter(

            Q(
                user__first_name__icontains=search
            )

            |

            Q(
                user__last_name__icontains=search
            )

            |

            Q(
                user__username__icontains=search
            )

            |

            Q(
                user__email__icontains=search
            )

        )


    # ========================================================
    # MEMBER TYPE
    # ========================================================

    if member_type in [
        "STUDENT",
        "FACULTY",
        "STAFF",
    ]:

        members = members.filter(
            user_type=member_type
        )


    # ========================================================
    # STATUS
    # ========================================================

    if status_filter == "ACTIVE":

        members = members.filter(
            active=True
        )

    elif status_filter == "INACTIVE":

        members = members.filter(
            active=False
        )


    # ========================================================
    # TOTAL MEMBERS
    #
    # Overall total - independent of search.
    # ========================================================

    total_members = (
        LibraryUser.objects.count()
    )


    # ========================================================
    # BORROWED BOOKS
    #
    # A book is counted as borrowed when issue_date
    # falls inside selected period.
    # ========================================================

    borrowed_queryset = (
        BorrowTransaction.objects.filter(

            issue_date__gte=start_date,

            issue_date__lte=end_date,

        )
    )


    books_borrowed = (
        borrowed_queryset.count()
    )


    # ========================================================
    # RETURNED BOOKS
    #
    # IMPORTANT:
    # We use return_date.
    # ========================================================

    returned_queryset = (
        BorrowTransaction.objects.filter(

            return_date__isnull=False,

            return_date__gte=start_date,

            return_date__lte=end_date,

        )
    )


    books_returned = (
        returned_queryset.count()
    )


    # ========================================================
    # RENEWED BOOKS
    #
    # last_renewed_at is a DateTimeField.
    #
    # We count transactions whose latest renewal occurred
    # inside the selected period.
    # ========================================================

    renewed_queryset = (
        BorrowTransaction.objects.filter(

            last_renewed_at__date__gte=start_date,

            last_renewed_at__date__lte=end_date,

            renewal_count__gt=0,

        )
    )


    books_renewed = (
        renewed_queryset.count()
    )


    # ========================================================
    # OVERDUE BOOKS
    # ========================================================

    overdue_queryset = (
        BorrowTransaction.objects.filter(

            status="OVERDUE",

            due_date__gte=start_date,

            due_date__lte=end_date,

        )
    )


    books_overdue = (
        overdue_queryset.count()
    )


    # ========================================================
    # MEMBER ACTIVITY
    # ========================================================

    member_data = []


    for member in members:

        # ====================================================
        # MEMBER NAME
        # ====================================================

        full_name = (
            member.user.get_full_name()
        )


        if full_name:

            member_name = full_name

        else:

            member_name = (
                member.user.username
            )


        # ====================================================
        # BORROWED
        # ====================================================

        borrowed_count = (
            BorrowTransaction.objects.filter(

                library_user=member,

                issue_date__gte=start_date,

                issue_date__lte=end_date,

            )
            .count()
        )


        # ====================================================
        # RETURNED
        # ====================================================

        returned_count = (
            BorrowTransaction.objects.filter(

                library_user=member,

                return_date__isnull=False,

                return_date__gte=start_date,

                return_date__lte=end_date,

            )
            .count()
        )


        # ====================================================
        # RENEWED
        # ====================================================

        renewed_count = (
            BorrowTransaction.objects.filter(

                library_user=member,

                last_renewed_at__date__gte=start_date,

                last_renewed_at__date__lte=end_date,

                renewal_count__gt=0,

            )
            .count()
        )


        # ====================================================
        # OVERDUE
        # ====================================================

        overdue_count = (
            BorrowTransaction.objects.filter(

                library_user=member,

                status="OVERDUE",

                due_date__gte=start_date,

                due_date__lte=end_date,

            )
            .count()
        )


        # ====================================================
        # MEMBER DATA
        # ====================================================

        member_data.append({

            "id":
                str(member.uuid)
                if hasattr(member, "uuid")
                else str(member.pk),

            "name":
                member_name,

            "username":
                member.user.username,

            "email":
                member.user.email or "",

            "type":
                member.get_user_type_display(),

            "borrowed":
                borrowed_count,

            "returned":
                returned_count,

            "renewed":
                renewed_count,

            "overdue":
                overdue_count,

            "status":
                "Active"
                if member.active
                else "Inactive",

        })


    # ========================================================
    # PAGINATION
    # ========================================================

    paginator = Paginator(
        member_data,
        5,
    )


    page_obj = paginator.get_page(
        page_number
    )


    # ========================================================
    # RECENT MEMBER ACTIVITY
    #
    # No reservation.
    #
    # Borrowed
    # Returned
    # Renewed
    # Overdue
    # ========================================================

    recent_transactions = (
        BorrowTransaction.objects
        .select_related(
            "library_user__user",
            "copy__resource",
        )
        .order_by(
            "-issue_date"
        )[:10]
    )


    recent_activity = []


    for transaction in recent_transactions:

        # ----------------------------------------------------
        # MEMBER NAME
        # ----------------------------------------------------

        member_name = (
            transaction
            .library_user
            .user
            .get_full_name()
        )


        if not member_name:

            member_name = (
                transaction
                .library_user
                .user
                .username
            )


        # ----------------------------------------------------
        # BOOK
        # ----------------------------------------------------

        try:

            book_title = (
                transaction
                .copy
                .resource
                .title
            )

        except AttributeError:

            book_title = "Library Resource"


        # ----------------------------------------------------
        # ACTIVITY
        # ----------------------------------------------------

        if (
            transaction.last_renewed_at
            and
            transaction.renewal_count > 0
        ):

            activity_type = "Renewed"

            activity_date = (
                transaction
                .last_renewed_at
                .strftime("%d %b %Y")
            )


        elif transaction.return_date:

            activity_type = "Returned"

            activity_date = (
                transaction
                .return_date
                .strftime("%d %b %Y")
            )


        elif (
            transaction.status ==
            "OVERDUE"
        ):

            activity_type = "Overdue"

            activity_date = (
                transaction
                .due_date
                .strftime("%d %b %Y")
            )


        else:

            activity_type = "Borrowed"

            activity_date = (
                transaction
                .issue_date
                .strftime("%d %b %Y")
            )


        recent_activity.append({

            "member":
                member_name,

            "book":
                book_title,

            "type":
                activity_type,

            "date":
                activity_date,

        })


    # ========================================================
    # RESPONSE
    # ========================================================

    return JsonResponse({

        "success":
            True,

        "statistics": {

            "total_members":
                total_members,

            "borrowed":
                books_borrowed,

            "returned":
                books_returned,

            "renewed":
                books_renewed,

            "overdue":
                books_overdue,

        },

        "members":
            list(page_obj.object_list),

        "recent_activity":
            recent_activity,

        "pagination": {

            "current":
                page_obj.number,

            "total_pages":
                paginator.num_pages,

            "total_items":
                paginator.count,

            "has_previous":
                page_obj.has_previous(),

            "has_next":
                page_obj.has_next(),

        },

    })

# ============================================================
# MEMBER DETAILS AJAX
# ============================================================

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from Library.models import (
    LibraryUser,
    BorrowTransaction,
)


@login_required
def library_member_details_ajax(
    request,
    member_id
):

    # ========================================================
    # GET MEMBER
    # ========================================================

    member = get_object_or_404(
        LibraryUser.objects.select_related(
            "user"
        ),
        id=member_id
    )


    # ========================================================
    # MEMBER NAME
    # ========================================================

    full_name = (
        member.user.get_full_name()
    )

    if full_name:

        member_name = full_name

    else:

        member_name = (
            member.user.username
        )


    # ========================================================
    # GET ALL TRANSACTIONS
    #
    # NO RESERVATION
    # ========================================================

    transactions = (
        BorrowTransaction.objects
        .filter(
            library_user=member
        )
        .select_related(
            "copy",
            "copy__resource",
        )
        .order_by(
            "-issue_date"
        )
    )


    borrowed_books = []

    returned_books = []

    renewed_books = []


    # ========================================================
    # PROCESS TRANSACTIONS
    # ========================================================

    for transaction in transactions:

        # ----------------------------------------------------
        # BOOK
        # ----------------------------------------------------

        resource = (
            transaction.copy.resource
        )

        title = (
            resource.title
            or "Untitled Book"
        )

        author = (
            resource.author
            or "Unknown Author"
        )


        # ----------------------------------------------------
        # BARCODE
        #
        # ResourceCopy has barcode
        # ----------------------------------------------------

        barcode = (
            transaction.copy.barcode
            or "-"
        )


        # ----------------------------------------------------
        # ISSUE DATE
        # ----------------------------------------------------

        issue_date = "-"

        if transaction.issue_date:

            issue_date = (
                transaction.issue_date
                .strftime("%d %b %Y")
            )


        # ----------------------------------------------------
        # DUE DATE
        # ----------------------------------------------------

        due_date = "-"

        if transaction.due_date:

            due_date = (
                transaction.due_date
                .strftime("%d %b %Y")
            )


        # ----------------------------------------------------
        # RETURN DATE
        # ----------------------------------------------------

        return_date = "-"

        if transaction.return_date:

            return_date = (
                transaction.return_date
                .strftime("%d %b %Y")
            )


        # ----------------------------------------------------
        # LAST RENEWED DATE
        # ----------------------------------------------------

        renewed_date = "-"

        if transaction.last_renewed_at:

            renewed_date = (
                transaction.last_renewed_at
                .strftime("%d %b %Y")
            )


        # ----------------------------------------------------
        # RENEWAL COUNT
        # ----------------------------------------------------

        renewal_count = (
            transaction.renewal_count
            or 0
        )


        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        transaction_status = (
            transaction.status
        )


        # ====================================================
        # BOOK DATA
        # ====================================================

        book_data = {

            "id":
                transaction.id,

            "title":
                title,

            "author":
                author,

            "barcode":
                barcode,

            "issue_date":
                issue_date,

            "due_date":
                due_date,

            "return_date":
                return_date,

            "renewed_date":
                renewed_date,

            "renewal_count":
                renewal_count,

            "status":
                transaction_status,

        }


        # ====================================================
        # CURRENTLY BORROWED
        #
        # ISSUED / OVERDUE
        # ====================================================

        if transaction.status in [
            "ISSUED",
            "OVERDUE",
        ]:

            borrowed_books.append(
                book_data
            )


        # ====================================================
        # RETURNED
        # ====================================================

        if transaction.return_date:

            returned_books.append(
                book_data
            )


        # ====================================================
        # RENEWED
        #
        # Any transaction which has been renewed
        # ====================================================

        if renewal_count > 0:

            renewed_books.append(
                book_data
            )


    # ========================================================
    # RESPONSE
    # ========================================================

    return JsonResponse({

        "success": True,

        "member": {

            "id":
                member.id,

            "name":
                member_name,

            "username":
                member.user.username,

            "email":
                member.user.email or "",

            "type":
                member.get_user_type_display(),

            "status":
                (
                    "Active"
                    if member.active
                    else "Inactive"
                ),

        },

        "borrowed_books":
            borrowed_books,

        "returned_books":
            returned_books,

        "renewed_books":
            renewed_books,

        "counts": {

            "borrowed":
                len(borrowed_books),

            "returned":
                len(returned_books),

            "renewed":
                len(renewed_books),

        },

    })

# =========================================================
# LIBRARY FORM SUBMISSIONS
# =========================================================

import json

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from Staff.models import Notification

from Library.models import (
    CirculationInquiry,
    TechnicalAssistanceInquiry,
    ShelvingFacilityRequest,
    ContactRequest,
    InstructionRequest,
    DigitalCollectionsContact,
    ProposalSubmission,
)


# =========================================================
# FORM CONFIGURATION
# =========================================================

FORM_CONFIG = {

    "circulation": {
        "model": CirculationInquiry,
        "label": "Circulation Assistance",
        "date_field": "submitted_at",
        "icon": "book-open",
    },

    "technical": {
        "model": TechnicalAssistanceInquiry,
        "label": "Technical Assistance",
        "date_field": "submitted_at",
        "icon": "laptop",
    },

    "shelving": {
        "model": ShelvingFacilityRequest,
        "label": "Shelving Facility Request",
        "date_field": "created_at",
        "icon": "library",
    },

    "contact": {
        "model": ContactRequest,
        "label": "Contact Us",
        "date_field": "created_at",
        "icon": "mail",
    },

    "instruction": {
        "model": InstructionRequest,
        "label": "Instruction Request",
        "date_field": "created_at",
        "icon": "graduation-cap",
    },

    "digital": {
        "model": DigitalCollectionsContact,
        "label": "Digital Collections",
        "date_field": "created_at",
        "icon": "database",
    },

    "proposal": {
        "model": ProposalSubmission,
        "label": "Digital Collections Proposal",
        "date_field": "submitted_at",
        "icon": "lightbulb",
    },
}


# =========================================================
# GET SUBMISSION QUERYSET
# =========================================================

def get_submission_queryset(form_type):

    config = FORM_CONFIG.get(form_type)

    if not config:
        return None

    return config["model"].objects.all()


# =========================================================
# GET ONE SUBMISSION
# =========================================================

def get_submission_object(form_type, submission_id):

    config = FORM_CONFIG.get(form_type)

    if not config:
        raise Http404("Invalid form type.")

    return get_object_or_404(
        config["model"],
        id=submission_id
    )


# =========================================================
# GET SUBMISSION DATE
# =========================================================

def get_submission_date(item, form_type):

    date_field = FORM_CONFIG[form_type]["date_field"]

    return getattr(
        item,
        date_field,
        None
    )


# =========================================================
# GET NOTIFICATION
# =========================================================

def get_submission_notification(
    request,
    form_type,
    submission_id
):

    detail_url = (
        f"{reverse('library_form_submissions')}"
        f"?open={form_type}:{submission_id}"
    )

    return (
        Notification.objects
        .filter(
            user=request.user,
            link=detail_url,
        )
        .order_by("-created_at")
        .first()
    )


# =========================================================
# GET STATUS
# =========================================================

def get_submission_status(
    request,
    form_type,
    submission_id
):

    notification = get_submission_notification(
        request,
        form_type,
        submission_id
    )

    if notification and notification.is_read:
        return "VIEWED"

    return "NEW"


# =========================================================
# GET NAME
# =========================================================

def get_submission_name(
    item,
    form_type
):

    # Shelving
    if form_type == "shelving":

        name = (
            f"{getattr(item, 'first_name', '')} "
            f"{getattr(item, 'last_name', '')}"
        ).strip()

        return name or "Unknown"


    # Normal name
    if hasattr(item, "name"):

        return (
            getattr(item, "name", "")
            or "Unknown"
        )


    # Instruction
    if hasattr(item, "instructor_name"):

        return (
            getattr(
                item,
                "instructor_name",
                ""
            )
            or "Unknown"
        )


    # Technical
    if hasattr(item, "full_name"):

        return (
            getattr(
                item,
                "full_name",
                ""
            )
            or "Unknown"
        )


    return "Unknown"


# =========================================================
# GET EMAIL
# =========================================================

def get_submission_email(item):

    return (
        getattr(
            item,
            "email",
            None
        )
        or getattr(
            item,
            "instructor_email",
            None
        )
        or ""
    )


# =========================================================
# GET SUBJECT
# =========================================================

def get_submission_subject(
    item,
    form_type
):

    if form_type == "circulation":

        return "Library circulation assistance"


    if form_type == "technical":

        return (
            getattr(
                item,
                "subject",
                None
            )
            or "Technical assistance request"
        )


    if form_type == "shelving":

        return (
            getattr(
                item,
                "title",
                None
            )
            or "Shelving facility request"
        )


    if form_type == "contact":

        return "Contact request"


    if form_type == "instruction":

        return "Library instruction request"


    if form_type == "digital":

        return (
            getattr(
                item,
                "subject",
                None
            )
            or "Digital collections contact"
        )


    if form_type == "proposal":

        return (
            getattr(
                item,
                "title",
                None
            )
            or getattr(
                item,
                "project_title",
                None
            )
            or "Digital collections proposal"
        )


    return ""


# =========================================================
# BUILD ONE SUBMISSION
# =========================================================

def build_submission(
    request,
    item,
    form_type
):

    submission_date = get_submission_date(
        item,
        form_type
    )

    status = get_submission_status(
        request,
        form_type,
        item.id
    )

    notification = get_submission_notification(
        request,
        form_type,
        item.id
    )

    return {

        "id": item.id,

        "type": FORM_CONFIG[
            form_type
        ]["label"],

        "type_key": form_type,

        "icon": FORM_CONFIG[
            form_type
        ]["icon"],

        "name": get_submission_name(
            item,
            form_type
        ),

        "email": get_submission_email(
            item
        ),

        "subject": get_submission_subject(
            item,
            form_type
        ),

        "date": submission_date,

        "status": status,

        "notification_id": (
            notification.id
            if notification
            else None
        ),

        "detail_url": (
            f"{reverse('library_form_submissions')}"
            f"?open={form_type}:{item.id}"
        ),
    }


# =========================================================
# FORM BADGES
# =========================================================

def get_form_badges(request):

    badges = {}

    submissions_url = reverse(
        "library_form_submissions"
    )

    for form_type in FORM_CONFIG:

        prefix = (
            f"{submissions_url}"
            f"?open={form_type}:"
        )

        badges[form_type] = (
            Notification.objects
            .filter(
                user=request.user,
                is_read=False,
                notification_type="REQUEST",
                link__startswith=prefix,
            )
            .count()
        )

    return badges


# =========================================================
# FORM COUNTS
# =========================================================

def get_form_counts():

    counts = {}

    for form_type, config in FORM_CONFIG.items():

        counts[form_type] = (
            config["model"]
            .objects
            .count()
        )

    return counts


    # =========================================================
# LIBRARY FORM SUBMISSIONS PAGE
# =========================================================

@login_required
def library_form_submissions(request):

    search_query = (
        request.GET
        .get("q", "")
        .strip()
    )

    form_type = (
        request.GET
        .get("form_type", "all")
        .strip()
        .lower()
    )

    status_filter = (
        request.GET
        .get("status", "all")
        .strip()
        .lower()
    )

    page_number = (
        request.GET
        .get("page", 1)
    )


    # =====================================================
    # VALIDATE FORM TYPE
    # =====================================================

    if (
        form_type != "all"
        and form_type not in FORM_CONFIG
    ):
        form_type = "all"


    # =====================================================
    # SELECT FORM TYPES
    # =====================================================

    if form_type == "all":

        selected_types = list(
            FORM_CONFIG.keys()
        )

    else:

        selected_types = [
            form_type
        ]


    # =====================================================
    # BUILD ALL SUBMISSIONS
    # =====================================================

    all_submissions = []


    for current_type in selected_types:

        config = FORM_CONFIG[
            current_type
        ]

        queryset = (
            config["model"]
            .objects
            .all()
        )

        date_field = config[
            "date_field"
        ]

        queryset = queryset.order_by(
            f"-{date_field}"
        )


        for obj in queryset:

            all_submissions.append(
                build_submission(
                    request,
                    obj,
                    current_type
                )
            )


    # =====================================================
    # SORT
    # =====================================================

    all_submissions.sort(
        key=lambda item: (
            item["date"]
            or timezone.now()
        ),
        reverse=True
    )


    # =====================================================
    # SEARCH
    # =====================================================

    filtered_submissions = (
        all_submissions
    )


    if search_query:

        search_lower = (
            search_query.lower()
        )

        filtered_submissions = [

            item

            for item in filtered_submissions

            if (

                search_lower
                in str(
                    item["name"]
                ).lower()

                or

                search_lower
                in str(
                    item["email"]
                ).lower()

                or

                search_lower
                in str(
                    item["subject"]
                ).lower()

                or

                search_lower
                in str(
                    item["type"]
                ).lower()

            )

        ]


    # =====================================================
    # STATUS FILTER
    # =====================================================

    if status_filter in (
        "new",
        "viewed"
    ):

        filtered_submissions = [

            item

            for item in filtered_submissions

            if (
                item["status"].lower()
                == status_filter
            )

        ]


    # =====================================================
    # COUNTS
    # =====================================================

    total_submissions = len(
        all_submissions
    )

    new_submissions = sum(
        1
        for item in all_submissions
        if item["status"] == "NEW"
    )

    viewed_submissions = sum(
        1
        for item in all_submissions
        if item["status"] == "VIEWED"
    )


    # =====================================================
    # BADGES
    # =====================================================

    form_badges = get_form_badges(
        request
    )


    # =====================================================
    # FORM COUNTS
    # =====================================================

    form_counts = get_form_counts()


    # =====================================================
    # UNREAD NOTIFICATIONS
    # =====================================================

    unread_count = (
        Notification.objects
        .filter(
            user=request.user,
            is_read=False,
        )
        .count()
    )


    # =====================================================
    # PAGINATION
    # =====================================================

    paginator = Paginator(
        filtered_submissions,
        5
    )

    page_obj = paginator.get_page(
        page_number
    )


    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "submissions": page_obj,

        "page_obj": page_obj,

        "total_submissions":
            total_submissions,

        "new_submissions":
            new_submissions,

        "viewed_submissions":
            viewed_submissions,

        "unread_count":
            unread_count,

        "form_badges":
            form_badges,

        "form_counts":
            form_counts,

        "form_config":
            FORM_CONFIG,

        "search_query":
            search_query,

        "form_type":
            form_type,

        "status_filter":
            status_filter,
    }


    return render(
        request,
        "library_admin/library_form_submissions.html",
        context
    )

    # =========================================================
# AJAX FILTER SUBMISSIONS
# =========================================================

@login_required
def library_form_submissions_filter_ajax(request):

    if request.method != "GET":

        return JsonResponse(
            {
                "success": False,
                "message": "GET request required."
            },
            status=405
        )


    search_query = (
        request.GET
        .get("q", "")
        .strip()
        .lower()
    )

    form_type = (
        request.GET
        .get("form_type", "all")
        .strip()
        .lower()
    )

    status_filter = (
        request.GET
        .get("status", "all")
        .strip()
        .lower()
    )

    page_number = (
        request.GET
        .get("page", 1)
    )


    # =====================================================
    # VALIDATE
    # =====================================================

    if (
        form_type != "all"
        and form_type not in FORM_CONFIG
    ):

        form_type = "all"


    # =====================================================
    # FORM TYPES
    # =====================================================

    if form_type == "all":

        selected_types = list(
            FORM_CONFIG.keys()
        )

    else:

        selected_types = [
            form_type
        ]


    # =====================================================
    # BUILD
    # =====================================================

    submissions = []


    for current_type in selected_types:

        config = FORM_CONFIG[
            current_type
        ]

        queryset = (
            config["model"]
            .objects
            .all()
            .order_by(
                f"-{config['date_field']}"
            )
        )


        for obj in queryset:

            item = build_submission(
                request,
                obj,
                current_type
            )


            # =================================================
            # SEARCH
            # =================================================

            if search_query:

                searchable = " ".join(
                    [
                        str(
                            item.get(
                                "name",
                                ""
                            )
                        ),

                        str(
                            item.get(
                                "email",
                                ""
                            )
                        ),

                        str(
                            item.get(
                                "subject",
                                ""
                            )
                        ),

                        str(
                            item.get(
                                "type",
                                ""
                            )
                        ),
                    ]
                ).lower()


                if search_query not in searchable:

                    continue


            # =================================================
            # STATUS
            # =================================================

            if status_filter in (
                "new",
                "viewed"
            ):

                if (
                    item["status"].lower()
                    != status_filter
                ):

                    continue


            submissions.append(
                item
            )


    # =====================================================
    # SORT
    # =====================================================

    submissions.sort(
        key=lambda item: (
            item["date"]
            or timezone.now()
        ),
        reverse=True
    )


    # =====================================================
    # PAGINATION
    # =====================================================

    paginator = Paginator(
        submissions,
        5
    )

    page_obj = paginator.get_page(
        page_number
    )


    # =====================================================
    # SERIALIZE
    # =====================================================

    data = []


    for item in page_obj.object_list:

        date_value = item["date"]


        if date_value:

            formatted_date = (
                timezone.localtime(
                    date_value
                ).strftime(
                    "%b %d, %Y"
                )
            )

            formatted_time = (
                timezone.localtime(
                    date_value
                ).strftime(
                    "%I:%M %p"
                )
            )

            modal_date = (
                timezone.localtime(
                    date_value
                ).strftime(
                    "%b %d, %Y %I:%M %p"
                )
            )

        else:

            formatted_date = "—"

            formatted_time = ""

            modal_date = "—"


        data.append({

            "id":
                item["id"],

            "type":
                item["type"],

            "type_key":
                item["type_key"],

            "icon":
                item["icon"],

            "name":
                item["name"],

            "email":
                item["email"],

            "subject":
                item["subject"],

            "date":
                formatted_date,

            "time":
                formatted_time,

            "modal_date":
                modal_date,

            "status":
                item["status"],

            "notification_id":
                item["notification_id"],

        })


    # =====================================================
    # RETURN
    # =====================================================

    return JsonResponse({

        "success": True,

        "submissions": data,

        "pagination": {
            # Current page
            "current_page": page_obj.number,

            # Total pages
            "total_pages": paginator.num_pages,
            "num_pages": paginator.num_pages,

            # Total records
            "total_items": paginator.count,
            "total": paginator.count,

            # Display range
            "start_index": (
                page_obj.start_index()
                if paginator.count > 0
                else 0
            ),

            "end_index": (
                page_obj.end_index()
                if paginator.count > 0
                else 0
            ),

            # Previous
            "has_previous": page_obj.has_previous(),

            "previous_page": (
                page_obj.previous_page_number()
                if page_obj.has_previous()
                else None
            ),

            # Next
            "has_next": page_obj.has_next(),

            "next_page": (
                page_obj.next_page_number()
                if page_obj.has_next()
                else None
            ),
        },

        "counts": {

            "total":
                len(submissions),

            "new":
                sum(
                    1
                    for item in submissions
                    if item["status"] == "NEW"
                ),

            "viewed":
                sum(
                    1
                    for item in submissions
                    if item["status"] == "VIEWED"
                ),
        },

        # ==========================================
        # BADGES FOR ALL FORM TYPES
        # ==========================================

        "form_badges":
            get_form_badges(request),

        # ==========================================
        # TOTAL UNREAD NOTIFICATIONS
        # ==========================================

        "unread_count":
            Notification.objects.filter(
                user=request.user,
                is_read=False,
            ).count(),

    })

    # =========================================================
# AJAX VIEW SUBMISSION DETAILS
# =========================================================

@login_required
def library_form_submission_ajax(
    request,
    form_type,
    submission_id
):

    if request.method != "GET":

        return JsonResponse(
            {
                "success": False,
                "message": "GET request required."
            },
            status=405
        )


    # =====================================================
    # VALIDATE FORM TYPE
    # =====================================================

    if form_type not in FORM_CONFIG:

        return JsonResponse(
            {
                "success": False,
                "message": "Invalid form type."
            },
            status=400
        )


    # =====================================================
    # GET SUBMISSION
    # =====================================================

    submission = get_submission_object(
        form_type,
        submission_id
    )


    # =====================================================
    # GET NOTIFICATION
    # =====================================================

    notification = (
        get_submission_notification(
            request,
            form_type,
            submission_id
        )
    )


    # =====================================================
    # MARK AS VIEWED
    # =====================================================

    if (
        notification
        and not notification.is_read
    ):

        notification.is_read = True

        notification.save(
            update_fields=[
                "is_read"
            ]
        )


    # =====================================================
    # BUILD DETAILS
    # =====================================================

    fields = []


    for field in submission._meta.fields:

        # Don't show database primary key
        if field.name == "id":
            continue


        value = getattr(
            submission,
            field.name,
            None
        )


        # -------------------------------------------------
        # FORMAT VALUE
        # -------------------------------------------------

        if value is None:

            display_value = "—"


        elif isinstance(
            value,
            bool
        ):

            display_value = (
                "Yes"
                if value
                else "No"
            )


        elif hasattr(
            value,
            "strftime"
        ):

            try:

                display_value = (
                    timezone.localtime(
                        value
                    ).strftime(
                        "%b %d, %Y %I:%M %p"
                    )
                )

            except Exception:

                display_value = (
                    value.strftime(
                        "%b %d, %Y %I:%M %p"
                    )
                )


        else:

            display_value = str(
                value
            )


        # -------------------------------------------------
        # HUMAN LABEL
        # -------------------------------------------------

        label = (
            field.verbose_name
            .replace(
                "_",
                " "
            )
            .title()
        )


        fields.append({

            "name":
                label,

            "value":
                display_value,

        })


    # =====================================================
    # FORM STATUS
    # =====================================================

    status = "VIEWED"


    # =====================================================
    # UNREAD COUNT
    # =====================================================

    unread_count = (
        Notification.objects
        .filter(
            user=request.user,
            is_read=False,
        )
        .count()
    )


    # =====================================================
    # FORM BADGES
    # =====================================================

    form_badges = get_form_badges(
        request
    )


    # =====================================================
    # SUBMISSION DATE
    # =====================================================

    submission_date = get_submission_date(
        submission,
        form_type
    )


    if submission_date:

        try:

            formatted_date = (
                timezone.localtime(
                    submission_date
                ).strftime(
                    "%b %d, %Y %I:%M %p"
                )
            )

        except Exception:

            formatted_date = (
                submission_date.strftime(
                    "%b %d, %Y %I:%M %p"
                )
            )

    else:

        formatted_date = "—"


    # =====================================================
    # RESPONSE
    # =====================================================

    return JsonResponse({

        "success": True,

        "submission_id":
            submission.id,

        "type":
            FORM_CONFIG[
                form_type
            ]["label"],

        "type_key":
            form_type,

        "name":
            get_submission_name(
                submission,
                form_type
            ),

        "email":
            get_submission_email(
                submission
            ),

        "subject":
            get_submission_subject(
                submission,
                form_type
            ),

        "date":
            formatted_date,

        "status":
            status,

        "fields":
            fields,

        "unread_count":
            unread_count,

        "form_badges":
            form_badges,

    })

    