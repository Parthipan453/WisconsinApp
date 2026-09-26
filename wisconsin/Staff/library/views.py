# =====================================================
# Staff/library/views.py — Library section
# =====================================================

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from Library.models import (
    Library,
    LibraryResource,
    LibraryUser,
    LibraryEvent,
    BorrowRequest,
    BorrowTransaction,
)


ANNOUNCEMENT_ICON_MAP = {
    "HOURS": "ti ti-clock",
    "WORKSHOP": "ti ti-calendar-event",
    "DATABASE": "ti ti-database",
    "MAINTENANCE": "ti ti-tool",
}


def _announcement_icon(event_type):
    return ANNOUNCEMENT_ICON_MAP.get(
        (event_type or "").upper(),
        "ti ti-bell",
    )


# =====================================================
# STAFF LIBRARY HOME
# =====================================================

@login_required
def staff_library_home(request, uuid):

    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------
    search_query = request.GET.get("q", "").strip()
    library_scope = request.GET.get("scope", "all")

    search_results = None

    if search_query:

        search_results = (
            LibraryResource.objects
            .select_related("library", "category")
            .filter(status="ACTIVE")
            .filter(
                Q(title__icontains=search_query)
                | Q(author__icontains=search_query)
                | Q(isbn_issn__icontains=search_query)
                | Q(subject__icontains=search_query)
            )
        )

        if library_scope and library_scope != "all":
            search_results = search_results.filter(
                library__library_code=library_scope
            )

        search_results = search_results.order_by("title")[:30]

    # -----------------------------------------------------
    # Which searched books does this staff user already have
    # a PENDING BorrowRequest for, or is already borrowing?
    # -----------------------------------------------------
    pending_resource_ids = set()
    borrowed_resource_ids = set()

    library_user = LibraryUser.objects.filter(
        user=request.user
    ).first()

    if library_user and search_results:

        pending_resource_ids = set(
            BorrowRequest.objects
            .filter(
                library_user=library_user,
                status="PENDING"
            )
            .values_list("resource_id", flat=True)
        )

        borrowed_resource_ids = set(
            BorrowTransaction.objects
            .filter(
                library_user=library_user,
                status__in=["ISSUED", "OVERDUE"],
            )
            .values_list("copy__resource_id", flat=True)
        )

    # -----------------------------------------------------
    # NEW ARRIVALS
    # -----------------------------------------------------
    new_arrivals = (
        LibraryResource.objects
        .select_related("library", "category")
        .filter(status="ACTIVE")
        .order_by("-id")
    )

    # -----------------------------------------------------
    # POPULAR BOOKS
    # -----------------------------------------------------
    popular_books = (
        LibraryResource.objects
        .select_related("library", "category")
        .filter(status="ACTIVE")
        .annotate(
            borrow_count=Count("copies__transactions")
        )
        .order_by("-borrow_count", "-id")
    )

    # -----------------------------------------------------
    # LIBRARY ANNOUNCEMENTS
    # -----------------------------------------------------
    raw_announcements = (
        LibraryEvent.objects
        .select_related("library")
        .order_by("-event_date")[:3]
    )

    announcements = [
        {
            "event": event,
            "icon": _announcement_icon(event.event_type),
        }
        for event in raw_announcements
    ]

    libraries = Library.objects.filter(
        status="ACTIVE"
    ).order_by("library_name")

    context = {
        "search_query": search_query,
        "library_scope": library_scope,
        "search_results": search_results,
        "pending_resource_ids": pending_resource_ids,
        "borrowed_resource_ids": borrowed_resource_ids,
        "new_arrivals": new_arrivals,
        "popular_books": popular_books,
        "announcements": announcements,
        "libraries": libraries,
    }

    return render(
        request,
        "staff_library/home.html",
        context
    )


# =====================================================
# REQUEST TO BORROW
# Creates a PENDING BorrowRequest. Always requires staff
# approval via the admin page — never auto-issues a book.
# =====================================================

from Staff.models import Notification

from Staff.utils import notify_library_admin_new_borrow_request

from django.urls import reverse


@login_required
def staff_request_borrow(request, uuid, book_uuid):

    if request.method != "POST":
        return redirect(
            "staff_library_home",
            uuid=uuid
        )

    # uuid = Staff UUID
    # book_uuid = LibraryResource UUID
    book = get_object_or_404(
        LibraryResource,
        uuid=book_uuid
    )

    library_user = LibraryUser.objects.filter(
        user=request.user
    ).first()

    if library_user is None:
        messages.error(
            request,
            "Your library account isn't set up yet. Please contact library staff."
        )

        return redirect(
            "staff_library_home",
            uuid=uuid
        )

    if not library_user.active:
        messages.error(
            request,
            "Your library membership is currently inactive. Please contact library staff."
        )

        return redirect(
            "staff_library_home",
            uuid=uuid
        )

    # -------------------------------------------------
    # Already borrowing this exact book?
    # -------------------------------------------------
    already_borrowing = BorrowTransaction.objects.filter(
        library_user=library_user,
        copy__resource=book,
        status__in=["ISSUED", "OVERDUE"],
    ).exists()

    if already_borrowing:
        messages.info(
            request,
            f'You already have "{book.title}" checked out.'
        )

        return redirect(
            "staff_borrow_requests",
            uuid=uuid
        )

    # -------------------------------------------------
    # Already have a pending request for this book?
    # -------------------------------------------------
    already_requested = BorrowRequest.objects.filter(
        library_user=library_user,
        resource=book,
        status="PENDING",
    ).exists()

    if already_requested:
        messages.info(
            request,
            f'You already have a pending request for "{book.title}".'
        )

        return redirect(
            "staff_borrow_requests",
            uuid=uuid
        )

    # -------------------------------------------------
    # Borrowing limit check
    # -------------------------------------------------
    current_active_loans = BorrowTransaction.objects.filter(
        library_user=library_user,
        status__in=["ISSUED", "OVERDUE"],
    ).count()

    if current_active_loans >= library_user.borrowing_limit:
        messages.error(
            request,
            f"You've reached your borrowing limit of "
            f"{library_user.borrowing_limit} book(s)."
        )

        return redirect(
            "staff_library_home",
            uuid=uuid
        )

    # -------------------------------------------------
    # All checks passed — create the pending request.
    # -------------------------------------------------

    borrow_request = BorrowRequest.objects.create(
        resource=book,
        library_user=library_user,
        status="PENDING",
    )

    notify_library_admin_new_borrow_request(
        borrow_request
    )

    messages.success(
        request,
        f'Request submitted for "{book.title}" — pending librarian approval.'
    )

    return redirect(
        "staff_borrow_requests",
        uuid=uuid
    )


# =====================================================
# LIST + CANCEL BORROW REQUESTS
# =====================================================

@login_required
def staff_borrow_requests(request, uuid):
    """
    Lists every BorrowRequest the staff user has ever made
    (pending, approved, rejected, cancelled), newest first.
    """

    library_user = LibraryUser.objects.filter(
        user=request.user
    ).first()

    borrow_requests = []

    if library_user:
        borrow_requests = (
            BorrowRequest.objects
            .select_related(
                "resource",
                "resource__library",
                "approved_by"
            )
            .filter(
                library_user=library_user
            )
            .order_by("-request_date")
        )

    context = {
        "borrow_requests": borrow_requests,
        "has_library_profile": library_user is not None,
    }

    return render(
        request,
        "staff_library/borrow_request.html",
        context,
    )


@login_required
def staff_cancel_borrow_request(
    request,
    uuid,
    request_id
):

    if request.method != "POST":
        return redirect(
            "staff_borrow_requests",
            uuid=uuid
        )

    library_user = LibraryUser.objects.filter(
        user=request.user
    ).first()

    borrow_request = get_object_or_404(
        BorrowRequest,
        uuid=request_id,
        library_user=library_user,
    )

    if borrow_request.status != "PENDING":
        messages.error(
            request,
            "Only pending requests can be cancelled."
        )

        return redirect(
            "staff_borrow_requests",
            uuid=uuid
        )

    borrow_request.status = "CANCELLED"
    borrow_request.save()

    messages.success(
        request,
        f'Your request for "{borrow_request.resource.title}" was cancelled.'
    )

    return redirect(
        "staff_borrow_requests",
        uuid=uuid
    )


# =====================================================
# QR
# =====================================================

import qrcode

from io import BytesIO

from django.http import HttpResponse


@login_required
def staff_borrow_request_qr(
    request,
    uuid,
    request_uuid
):
    """
    Generates a QR code for an approved borrow request.

    The QR contains the Library Admin issue-book URL
    for this specific BorrowRequest.
    """

    # Get the logged-in staff user's LibraryUser
    library_user = LibraryUser.objects.filter(
        user=request.user
    ).first()

    if library_user is None:
        return HttpResponse(
            "Library profile not found.",
            status=403
        )

    # Get only this staff user's borrow request
    borrow_request = get_object_or_404(
        BorrowRequest,
        uuid=request_uuid,
        library_user=library_user,
    )

    # QR is available only after approval
    if borrow_request.status != "APPROVED":
        return HttpResponse(
            "QR code is available only for approved borrow requests.",
            status=400
        )

    # -------------------------------------------------
    # URL that the Library Admin will open after scanning
    # -------------------------------------------------

    issue_book_url = request.build_absolute_uri(
        reverse(
            "issue_book_qr_entry",
            kwargs={
                "request_uuid": str(
                    borrow_request.uuid
                )
            }
        )
    )

    # -------------------------------------------------
    # Generate QR code
    # -------------------------------------------------

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )

    qr.add_data(issue_book_url)
    qr.make(fit=True)

    qr_image = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    # -------------------------------------------------
    # Convert QR image to PNG in memory
    # -------------------------------------------------

    buffer = BytesIO()

    qr_image.save(
        buffer,
        format="PNG"
    )

    buffer.seek(0)

    return HttpResponse(
        buffer.getvalue(),
        content_type="image/png"
    )


# =====================================================
# My borrowed books
# =====================================================

from datetime import date

from django.shortcuts import render

from Library.models import LibraryUser, BorrowTransaction


# How many days before due_date a loan is flagged "Due soon".
DUE_SOON_THRESHOLD_DAYS = 3

@login_required
def staff_borrowed_books(request, uuid):
    """
    Shows the student's active and returned books.

    Active transactions:
        ISSUED
        OVERDUE

    Returned transactions:
        RETURNED

    Active loans get a computed status:
        ACTIVE
        DUE_SOON
        OVERDUE

    Returned loans get:
        RETURNED
    """

    library_user = LibraryUser.objects.filter(
        user=request.user
    ).first()

    loans = []

    if library_user:

        transactions = (
            BorrowTransaction.objects
            .select_related(
                "copy",
                "copy__resource",
                "copy__resource__library",
            )
            .filter(
                library_user=library_user,
                status__in=[
                    "ISSUED",
                    "OVERDUE",
                    "RETURNED",
                ],
            )
            .order_by("-id")
        )

        today = date.today()

        for txn in transactions:

            # =================================================
            # RETURNED BOOK
            # =================================================

            if txn.status == "RETURNED":

                loans.append({
                    "transaction": txn,

                    "computed_status": "RETURNED",

                    "days_left": 0,

                    "days_overdue": 0,

                    "filter_status": "RETURNED",
                })

                continue


            # =================================================
            # ACTIVE / OVERDUE BOOK
            # =================================================

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

                "filter_status": computed_status,

            })


    # =========================================================
    # COUNTS
    # =========================================================

    total_count = len(loans)

    active_count = sum(
        1
        for loan in loans
        if loan["filter_status"] == "ACTIVE"
    )

    due_soon_count = sum(
        1
        for loan in loans
        if loan["filter_status"] == "DUE_SOON"
    )

    overdue_count = sum(
        1
        for loan in loans
        if loan["filter_status"] == "OVERDUE"
    )

    returned_count = sum(
        1
        for loan in loans
        if loan["filter_status"] == "RETURNED"
    )


    # =========================================================
    # CONTEXT
    # =========================================================

    context = {

        "loans": loans,
        
        "uuid": uuid, 

        "has_library_profile": (
            library_user is not None
        ),

        "total_count": total_count,

        "active_count": active_count,

        "due_soon_count": due_soon_count,

        "overdue_count": overdue_count,

        "returned_count": returned_count,

    }


    return render(
        request,
        "staff_library/borrowed_books.html",
        context,
    )

# =====================================================
# Request renewal for borrowed book
# =====================================================

from django.utils import timezone

from Library.models import (
    LibraryUser,
    BorrowTransaction,
    # Reservation,
)


# =====================================================
# Renewal settings
# =====================================================

DUE_SOON_THRESHOLD_DAYS = 3
MAX_RENEWALS = 2


@login_required
def staff_renew_book(
    request,
    uuid,
    transaction_id
):
    """
    Staff user submits a renewal request.

    IMPORTANT:
    This view does NOT renew the book.

    It only marks the existing BorrowTransaction as
    having a pending renewal request.

    Actual renewal will happen later when library staff
    approves the request.
    """

    # -------------------------------------------------
    # 1. Renewal request must be POST
    # -------------------------------------------------

    if request.method != "POST":

        messages.error(
            request,
            "Invalid renewal request."
        )

        return redirect(
            "staff_borrowed_books",
            uuid=uuid
        )

    # -------------------------------------------------
    # 2. Get logged-in staff user's LibraryUser
    # -------------------------------------------------

    library_user = LibraryUser.objects.filter(
        user=request.user
    ).first()

    if not library_user:

        messages.error(
            request,
            "Your library account isn't set up yet."
        )

        return redirect(
            "staff_borrowed_books",
            uuid=uuid
        )

    # -------------------------------------------------
    # 3. Get the staff user's borrowing transaction
    # -------------------------------------------------

    loan = get_object_or_404(

        BorrowTransaction.objects.select_related(
            "copy",
            "copy__resource",
            "copy__resource__library",
        ),

        id=transaction_id,

        library_user=library_user,

    )

    # -------------------------------------------------
    # 4. Transaction must still be issued
    # -------------------------------------------------

    if loan.status != "ISSUED":

        messages.error(
            request,
            "This book cannot be renewed because it is no longer issued."
        )

        return redirect(
            "staff_borrowed_books",
            uuid=uuid
        )

    # -------------------------------------------------
    # 5. Book must not already be returned
    # -------------------------------------------------

    if loan.return_date is not None:

        messages.error(
            request,
            "This book has already been returned and cannot be renewed."
        )

        return redirect(
            "staff_borrowed_books",
            uuid=uuid
        )

    # -------------------------------------------------
    # 6. Calculate days remaining
    # -------------------------------------------------

    today = date.today()

    days_left = (
        loan.due_date - today
    ).days

    # -------------------------------------------------
    # 7. Overdue books cannot request renewal
    # -------------------------------------------------

    if days_left < 0:

        messages.error(
            request,
            "This book is already overdue and cannot be renewed."
        )

        return redirect(
            "staff_borrowed_books",
            uuid=uuid
        )

    # -------------------------------------------------
    # 8. Renewal request allowed only within 3 days
    # -------------------------------------------------

    if days_left > DUE_SOON_THRESHOLD_DAYS:

        messages.warning(
            request,
            f"This book can be renewed only when it is due "
            f"within {DUE_SOON_THRESHOLD_DAYS} days."
        )

        return redirect(
            "staff_borrowed_books",
            uuid=uuid
        )

    # -------------------------------------------------
    # 9. Maximum renewal limit
    # -------------------------------------------------

    if loan.renewal_count >= MAX_RENEWALS:

        messages.error(
            request,
            "You have already used the maximum number of renewals "
            "allowed for this book."
        )

        return redirect(
            "staff_borrowed_books",
            uuid=uuid
        )

    # -------------------------------------------------
    # 10. Check whether a request already exists
    # -------------------------------------------------

    if loan.renewal_requested:

        messages.warning(
            request,
            "A renewal request for this book has already been submitted "
            "and is waiting for library approval."
        )

        return redirect(
            "staff_borrowed_books",
            uuid=uuid
        )

    # -------------------------------------------------
    # 11. Check reservation from another library member
    # -------------------------------------------------

    # has_other_reservation = (
    #     Reservation.objects
    #     .filter(
    #         resource=loan.copy.resource,
    #         status="PENDING",
    #     )
    #     .exclude(
    #         library_user=library_user
    #     )
    #     .exists()
    # )

    # if has_other_reservation:

    #     messages.error(
    #         request,
    #         "This book cannot be renewed because another library member "
    #         "has reserved it."
    #     )

    #     return redirect(
    #         "staff_borrowed_books",
    #         uuid=uuid
    #     )

    # -------------------------------------------------
    # 12. CREATE RENEWAL REQUEST
    # -------------------------------------------------

    loan.renewal_requested = True

    loan.renewal_requested_at = timezone.now()

    loan.save(
        update_fields=[
            "renewal_requested",
            "renewal_requested_at",
        ]
    )

    # -------------------------------------------------
    # 13. Tell staff user that request was submitted
    # -------------------------------------------------

    messages.success(
        request,
        f'Renewal request for "{loan.copy.resource.title}" '
        f'has been sent to the library for approval.'
    )

    # -------------------------------------------------
    # 14. Return to My Borrowed Books
    # -------------------------------------------------

    return redirect(
        "staff_borrowed_books",
        uuid=uuid
    )
    
    
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.http import JsonResponse
from datetime import timedelta
from django.utils import timezone

from Library.models import (
    Library,
    LibraryResource,
    LibraryUser,
    BorrowRequest,
    BorrowTransaction,
)


@login_required
def staff_new_arrivals(request, uuid):

    search_query = request.GET.get("q", "").strip()
    library_scope = request.GET.get("scope", "all")
    sort = request.GET.get("sort", "newest")

    # -----------------------------------------
    # BASE QUERY
    # -----------------------------------------

    new_arrivals = (
        LibraryResource.objects
        .select_related("library", "category")
        .filter(status="ACTIVE")
        
    )

    # -----------------------------------------
    # SEARCH
    # -----------------------------------------

    if search_query:

        new_arrivals = new_arrivals.filter(
            Q(title__icontains=search_query)
            | Q(author__icontains=search_query)
            | Q(isbn_issn__icontains=search_query)
            | Q(subject__icontains=search_query)
        )

    # -----------------------------------------
    # LIBRARY FILTER
    # -----------------------------------------

    if library_scope and library_scope != "all":

        new_arrivals = new_arrivals.filter(
            library__library_code=library_scope
        )

    # -----------------------------------------
    # SORT
    # -----------------------------------------

    if sort == "oldest":

        new_arrivals = new_arrivals.order_by("id")

    elif sort == "title":

        new_arrivals = new_arrivals.order_by("title")

    elif sort == "author":

        new_arrivals = new_arrivals.order_by("author")

    else:

        new_arrivals = new_arrivals.order_by("-id")

    # -----------------------------------------
    # USER LIBRARY PROFILE
    # -----------------------------------------

    library_user = LibraryUser.objects.filter(
        user=request.user
    ).first()

    pending_resource_ids = set()
    borrowed_resource_ids = set()

    if library_user:

        pending_resource_ids = set(
            BorrowRequest.objects
            .filter(
                library_user=library_user,
                status="PENDING"
            )
            .values_list("resource_id", flat=True)
        )

        borrowed_resource_ids = set(
            BorrowTransaction.objects
            .filter(
                library_user=library_user,
                status__in=["ISSUED", "OVERDUE"]
            )
            .values_list(
                "copy__resource_id",
                flat=True
            )
        )

    # -----------------------------------------
    # PAGINATION
    # -----------------------------------------

    paginator = Paginator(
        new_arrivals,
        12
    )

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(
        page_number
    )

    # -----------------------------------------
    # LIBRARIES
    # -----------------------------------------

    libraries = (
        Library.objects
        .filter(status="ACTIVE")
        .order_by("library_name")
    )

    # -----------------------------------------
    # CONTEXT
    # -----------------------------------------

    context = {

        "new_arrivals": page_obj,

        "page_obj": page_obj,

        "search_query": search_query,

        "library_scope": library_scope,

        "sort": sort,

        "libraries": libraries,

        "pending_resource_ids":
            pending_resource_ids,

        "borrowed_resource_ids":
            borrowed_resource_ids,

    }

    return render(
        request,
        "staff_library/new_arrivals.html",
        context
    )
    
    
    
@login_required
def staff_new_arrivals_live_search(request, uuid):

    search_query = request.GET.get("q", "").strip()
    library_scope = request.GET.get("scope", "all")
    sort = request.GET.get("sort", "newest")
    page_number = request.GET.get("page", 1)

    # -----------------------------------------
    # BASE QUERY
    # -----------------------------------------

    new_arrivals = (
        LibraryResource.objects
        .select_related("library", "category")
        .filter(status="ACTIVE")
    )

    # -----------------------------------------
    # SEARCH
    # -----------------------------------------

    if search_query:
        new_arrivals = new_arrivals.filter(
            Q(title__icontains=search_query)
            | Q(author__icontains=search_query)
            | Q(isbn_issn__icontains=search_query)
            | Q(subject__icontains=search_query)
        )

    # -----------------------------------------
    # LIBRARY FILTER
    # -----------------------------------------

    if library_scope and library_scope != "all":
        new_arrivals = new_arrivals.filter(
            library__library_code=library_scope
        )

    # -----------------------------------------
    # SORT
    # -----------------------------------------

    if sort == "oldest":

        new_arrivals = new_arrivals.order_by("id")

    elif sort == "title":

        new_arrivals = new_arrivals.order_by("title")

    elif sort == "author":

        new_arrivals = new_arrivals.order_by("author")

    else:

        new_arrivals = new_arrivals.order_by("-id")

    # -----------------------------------------
    # PAGINATION
    # -----------------------------------------

    paginator = Paginator(
        new_arrivals,
        12
    )

    page_obj = paginator.get_page(
        page_number
    )

    # -----------------------------------------
    # USER LIBRARY PROFILE
    # -----------------------------------------

    library_user = LibraryUser.objects.filter(
        user=request.user
    ).first()

    pending_resource_ids = set()
    borrowed_resource_ids = set()

    if library_user:

        pending_resource_ids = set(
            BorrowRequest.objects
            .filter(
                library_user=library_user,
                status="PENDING"
            )
            .values_list(
                "resource_id",
                flat=True
            )
        )

        borrowed_resource_ids = set(
            BorrowTransaction.objects
            .filter(
                library_user=library_user,
                status__in=[
                    "ISSUED",
                    "OVERDUE"
                ]
            )
            .values_list(
                "copy__resource_id",
                flat=True
            )
        )

    # -----------------------------------------
    # BOOK RESULTS
    # -----------------------------------------

    books = []

    for book in page_obj:

        books.append({

            "uuid": str(book.uuid),

            "title": book.title,

            "author": (
                book.author
                or "Unknown Author"
            ),

            "library": (
                book.library.library_name
                if book.library
                else ""
            ),

            "cover_image": (
                book.cover_image.url
                if book.cover_image
                else ""
            ),

            "available_copies": (
                book.available_copies
            ),

            "is_pending": (
                book.id
                in pending_resource_ids
            ),

            "is_borrowed": (
                book.id
                in borrowed_resource_ids
            ),

            "borrow_url": reverse(
                "staff_borrow_request",
                kwargs={
                    "uuid": request.user.uuid,
                    "book_uuid": book.uuid,
                }
            ),

        })

    # -----------------------------------------
    # PAGINATION DATA
    # -----------------------------------------

    return JsonResponse({

        "success": True,

        "books": books,

        "pagination": {

            "current_page": (
                page_obj.number
            ),

            "total_pages": (
                paginator.num_pages
            ),

            "total_results": (
                paginator.count
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

        }

    })