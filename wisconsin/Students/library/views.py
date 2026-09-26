# =====================================================
# Student/views.py — Library section
# =====================================================
from Admin.audit import AuditLogger

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


@login_required
def student_library_home(request, uuid):

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
            search_results = search_results.filter(library__library_code=library_scope)

        search_results = search_results.order_by("title")[:30]

    # -----------------------------------------------------
    # Which searched books does this student already have a
    # PENDING BorrowRequest for, or is already borrowing?
    # -----------------------------------------------------
    pending_resource_ids = set()
    borrowed_resource_ids = set()

    library_user = LibraryUser.objects.filter(user=request.user).first()

    if library_user and search_results:

        pending_resource_ids = set(
            BorrowRequest.objects
            .filter(library_user=library_user, status="PENDING")
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
        .annotate(borrow_count=Count("copies__transactions"))
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
        {"event": event, "icon": _announcement_icon(event.event_type)}
        for event in raw_announcements
    ]

    libraries = Library.objects.filter(status="ACTIVE").order_by("library_name")

    context = {
        
        "uuid": uuid,
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

    return render(request, "library/home.html", context)


# =====================================================
# REQUEST TO BORROW
# Creates a PENDING BorrowRequest. Always requires staff
# approval via the admin page — never auto-issues a book.
# =====================================================

from Staff.models import Notification

from Staff.utils import notify_library_admin_new_borrow_request

from django.urls import reverse
@login_required
def student_request_borrow(request, uuid, book_uuid):

    if request.method != "POST":
        return redirect("Student:student_library_home", uuid=uuid)

    book = get_object_or_404(LibraryResource, uuid=book_uuid)

    library_user = LibraryUser.objects.filter(user=request.user).first()

    if library_user is None:
        messages.error(
            request,
            "Your library account isn't set up yet. Please contact library staff."
        )
        return redirect("Student:student_library_home", uuid=uuid)

    if not library_user.active:
        messages.error(
            request,
            "Your library membership is currently inactive. Please contact library staff."
        )
        return redirect("Student:student_library_home", uuid=uuid)

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
        return redirect("Student:student_borrow_requests",uuid=request.user.uuid)

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
        return redirect("Student:student_borrow_requests", uuid=uuid)

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
            f"You've reached your borrowing limit of {library_user.borrowing_limit} book(s)."
        )
        return redirect("Student:student_library_home", uuid=uuid)

    # -------------------------------------------------
    # All checks passed — create the pending request.
    # request_date / created_at / updated_at are all
    # auto-set by the model itself.
    # -------------------------------------------------
    # BorrowRequest.objects.create(
    #     resource=book,
    #     library_user=library_user,
    #     status="PENDING",
    # )
    
    borrow_request = BorrowRequest.objects.create(
        resource=book,
        library_user=library_user,
        status="PENDING",
    )
    
    # =====================================================
    # AUDIT LOG — BORROW REQUEST CREATED
    # =====================================================

    AuditLogger.log(
        request=request,
        action="REQUEST",
        module="StudentLibrary",
        object_type="BorrowRequest",
        object_id=str(borrow_request.uuid),
        description=(
            f'Borrow request submitted for "{book.title}".'
        ),
        before_data=None,
        after_data={
            "resource": book.title,
            "resource_uuid": str(book.uuid),
            "library": (
                book.library.library_name
                if book.library
                else None
            ),
            "status": borrow_request.status,
            "request_uuid": str(borrow_request.uuid),
        },
        status="SUCCESS",
    )
    
    notify_library_admin_new_borrow_request(borrow_request)
      

    messages.success(
        request,
        f'Request submitted for "{book.title}" — pending librarian approval.'
    )

    return redirect("Student:student_borrow_requests", uuid=uuid)


# =====================================================
# LIST + CANCEL BORROW REQUESTS
# =====================================================

@login_required
def student_borrow_requests(request, uuid):
    """
    Lists every BorrowRequest the student has ever made
    (pending, approved, rejected, cancelled), newest first.
    """

    library_user = LibraryUser.objects.filter(user=request.user).first()

    borrow_requests = []

    if library_user:
        borrow_requests = (
            BorrowRequest.objects
            .select_related("resource", "resource__library", "approved_by")
            .filter(library_user=library_user)
            .order_by("-request_date")
        )

    context = {
        "borrow_requests": borrow_requests,
        "has_library_profile": library_user is not None,
    }

    return render(
        request,
        "library/borrow_request.html",
        context,
    )


@login_required
def student_cancel_borrow_request(request, uuid, request_id):

    if request.method != "POST":
        return redirect(
            "Student:student_borrow_requests",
            uuid=uuid
        )

    library_user = LibraryUser.objects.filter(
        user=request.user
    ).first()

    borrow_request = get_object_or_404(
        BorrowRequest.objects.select_related(
            "resource",
            "library_user",
            "library_user__user",
        ),
        uuid=request_id,
        library_user=library_user,
    )

    # =====================================================
    # VALIDATE STATUS
    # =====================================================

    if borrow_request.status != "PENDING":

        messages.error(
            request,
            "Only pending requests can be cancelled."
        )

        return redirect(
            "Student:student_borrow_requests",
            uuid=uuid
        )

    # =====================================================
    # AUDIT — BEFORE DATA
    # =====================================================

    before_data = {
        "status": borrow_request.status,
        "resource": borrow_request.resource.title,
        "request_date": (
            borrow_request.request_date.isoformat()
            if borrow_request.request_date
            else None
        ),
    }

    # =====================================================
    # CANCEL REQUEST
    # =====================================================

    borrow_request.status = "CANCELLED"
    borrow_request.save(
        update_fields=["status"]
    )

    # =====================================================
    # AUDIT — AFTER DATA
    # =====================================================

    after_data = {
        "status": borrow_request.status,
        "resource": borrow_request.resource.title,
        "request_date": (
            borrow_request.request_date.isoformat()
            if borrow_request.request_date
            else None
        ),
    }

    # =====================================================
    # AUDIT LOG — CANCEL BORROW REQUEST
    # =====================================================

    AuditLogger.log(
        request=request,

        action="CANCEL",

        module="Student",

        object_type="BorrowRequest",

        object_id=borrow_request.id,

        description=(
            f'Cancelled borrow request for '
            f'"{borrow_request.resource.title}".'
        ),

        before_data=before_data,

        after_data=after_data,

        status="SUCCESS",
    )

    # =====================================================
    # SUCCESS MESSAGE
    # =====================================================

    messages.success(
        request,
        f'Your request for "{borrow_request.resource.title}" '
        f'was cancelled.'
    )

    return redirect(
        "Student:student_borrow_requests",
        uuid=uuid
    )


# qr
import qrcode

from io import BytesIO

from django.http import HttpResponse

@login_required
def student_borrow_request_qr(request, uuid, request_uuid):
    """
    Generates a QR code for an approved borrow request.

    The QR contains the Library Admin issue-book URL
    for this specific BorrowRequest.
    """

    # Get the logged-in student's LibraryUser
    library_user = LibraryUser.objects.filter(
        user=request.user
    ).first()

    if library_user is None:
        return HttpResponse(
            "Library profile not found.",
            status=403
        )

    # Get only this student's borrow request
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
                "request_uuid": str(borrow_request.uuid)
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

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from Library.models import LibraryUser, BorrowTransaction


# How many days before due_date a loan is flagged "Due soon".
DUE_SOON_THRESHOLD_DAYS = 3


@login_required
def student_borrowed_books(request, uuid):
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
        "library/borrowed_books.html",
        context,
    )

# Navina code starts

# =====================================================
# Request renewal for borrowed book
# =====================================================

from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
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


# @login_required
# def renew_book(request, transaction_id):
   
#     if request.method != "POST":

#         messages.error(
#             request,
#             "Invalid renewal request."
#         )

#         return redirect(
#             "Student:student_borrowed_books"
#         )


#     library_user = LibraryUser.objects.filter(
#         user=request.user
#     ).first()


#     if not library_user:

#         messages.error(
#             request,
#             "Your library account isn't set up yet."
#         )

#         return redirect(
#             "Student:student_borrowed_books"
#         )
    

#     loan = get_object_or_404(

#         BorrowTransaction.objects.select_related(
#             "copy",
#             "copy__resource",
#             "copy__resource__library",
#         ),

#         id=transaction_id,

#         library_user=library_user,

#     )




#     if loan.status != "ISSUED":

#         messages.error(
#             request,
#             "This book cannot be renewed because it is no longer issued."
#         )

#         return redirect(
#             "Student:student_borrowed_books"
#         )


    

#     if loan.return_date is not None:

#         messages.error(
#             request,
#             "This book has already been returned and cannot be renewed."
#         )

#         return redirect(
#             "Student:student_borrowed_books"
#         )


   

#     today = date.today()

#     days_left = (
#         loan.due_date - today
#     ).days


 

#     if days_left < 0:

#         messages.error(
#             request,
#             "This book is already overdue and cannot be renewed."
#         )

#         return redirect(
#             "Student:student_borrowed_books"
#         )




#     if days_left > DUE_SOON_THRESHOLD_DAYS:

#         messages.warning(
#             request,
#             f"This book can be renewed only when it is due "
#             f"within {DUE_SOON_THRESHOLD_DAYS} days."
#         )

#         return redirect(
#             "Student:student_borrowed_books"
#         )




#     if loan.renewal_count >= MAX_RENEWALS:

#         messages.error(
#             request,
#             "You have already used the maximum number of renewals "
#             "allowed for this book."
#         )

#         return redirect(
#             "Student:student_borrowed_books"
#         )


   
#     if loan.renewal_requested:

#         messages.warning(
#             request,
#             "A renewal request for this book has already been submitted "
#             "and is waiting for library approval."
#         )

#         return redirect(
#             "Student:student_borrowed_books"
#         )


#     loan.renewal_requested = True

#     loan.renewal_requested_at = timezone.now()

#     loan.save(
#         update_fields=[
#             "renewal_requested",
#             "renewal_requested_at",
#         ]
#     )

    
#     messages.success(
#         request,
#         f'Renewal request for "{loan.copy.resource.title}" '
#         f'has been sent to the library for approval.'
#     )


#     return redirect(
#         "Student:student_borrowed_books",
#     )
    

@login_required
def renew_book(request, uuid, transaction_id):

    # -------------------------------------------------
    # 1. Renewal request must be POST
    # -------------------------------------------------

    if request.method != "POST":

        messages.error(
            request,
            "Invalid renewal request."
        )

        return redirect(
            "Student:student_borrowed_books",
            uuid=uuid,
        )

    # -------------------------------------------------
    # 2. Get logged-in student's LibraryUser
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
            "Student:student_borrowed_books",
            uuid=uuid,
        )

    # -------------------------------------------------
    # 3. Get the student's borrowing transaction
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
            "Student:student_borrowed_books",
            uuid=uuid,
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
            "Student:student_borrowed_books",
            uuid=uuid,
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
            "Student:student_borrowed_books",
            uuid=uuid,
        )

    # -------------------------------------------------
    # 8. Renewal request allowed only within threshold
    # -------------------------------------------------

    if days_left > DUE_SOON_THRESHOLD_DAYS:

        messages.warning(
            request,
            f"This book can be renewed only when it is due "
            f"within {DUE_SOON_THRESHOLD_DAYS} days."
        )

        return redirect(
            "Student:student_borrowed_books",
            uuid=uuid,
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
            "Student:student_borrowed_books",
            uuid=uuid,
        )

    # -------------------------------------------------
    # 10. Check whether request already exists
    # -------------------------------------------------

    if loan.renewal_requested:

        messages.warning(
            request,
            "A renewal request for this book has already been submitted "
            "and is waiting for library approval."
        )

        return redirect(
            "Student:student_borrowed_books",
            uuid=uuid,
        )

    # =====================================================
    # AUDIT — BEFORE DATA
    # =====================================================

    before_data = {
        "transaction_status": loan.status,

        "due_date": (
            loan.due_date.isoformat()
            if loan.due_date
            else None
        ),

        "renewal_count": loan.renewal_count,

        "renewal_requested": loan.renewal_requested,

        "renewal_requested_at": (
            loan.renewal_requested_at.isoformat()
            if loan.renewal_requested_at
            else None
        ),
    }

    # -------------------------------------------------
    # 11. CREATE RENEWAL REQUEST
    # -------------------------------------------------

    loan.renewal_requested = True

    loan.renewal_requested_at = timezone.now()

    loan.save(
        update_fields=[
            "renewal_requested",
            "renewal_requested_at",
        ]
    )

    # =====================================================
    # AUDIT — AFTER DATA
    # =====================================================

    after_data = {
        "transaction_status": loan.status,

        "due_date": (
            loan.due_date.isoformat()
            if loan.due_date
            else None
        ),

        "renewal_count": loan.renewal_count,

        "renewal_requested": loan.renewal_requested,

        "renewal_requested_at": (
            loan.renewal_requested_at.isoformat()
            if loan.renewal_requested_at
            else None
        ),
    }

    # =====================================================
    # AUDIT LOG — RENEWAL REQUEST
    # =====================================================

    AuditLogger.log(
        request=request,

        action="REQUEST",

        module="Student",

        object_type="BorrowTransaction",

        object_id=loan.id,

        description=(
            f'Submitted renewal request for '
            f'"{loan.copy.resource.title}".'
        ),

        before_data=before_data,

        after_data=after_data,

        status="SUCCESS",
    )

    # -------------------------------------------------
    # SUCCESS MESSAGE
    # -------------------------------------------------

    messages.success(
        request,
        f'Renewal request for "{loan.copy.resource.title}" '
        f'has been sent to the library for approval.'
    )

    return redirect(
        "Student:student_borrowed_books",
        uuid=uuid,
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
def student_new_arrivals(request, uuid):

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
        "library/new_arrivals.html",
        context
    )
    
    
@login_required
def student_new_arrivals_live_search(request, uuid):

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
                "Student:student_request_borrow",
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

# =====================================================
# Student/views.py — Ask a Librarian, using Groq
# =====================================================

import json
from datetime import date
from decimal import Decimal
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST

from Library.models import (
    LibraryResource,
    LibraryUser,
    BorrowRequest,
    BorrowTransaction,
    Fine,
    AIConversation, AIMessage
)

# ============================================================
# LIBRARY RULES
# ============================================================

DUE_SOON_THRESHOLD_DAYS = 3
MAX_RENEWALS = 2

GROQ_MODEL = "openai/gpt-oss-120b"


# ============================================================
# AI SYSTEM PROMPT
# ============================================================

AI_SYSTEM_PROMPT = f"""
You are a friendly and concise AI assistant for the UW–Madison
Libraries website.

You help students with:

1. Book catalog questions
2. Borrowing books
3. Borrow requests
4. Current borrowed books
5. Due dates
6. Borrowing limits
7. Book returns
8. Book renewals
9. Fines

IMPORTANT RULES:

- Use ONLY the LIBRARY CONTEXT provided with the student's question.
- Never invent books, authors, availability, due dates, fine amounts,
  borrowing limits, renewal eligibility, or student records.
- Django database information is authoritative.
- If the supplied context does not contain the answer, say that
  the information is not available.
- Never pretend that you performed an action.
- You cannot actually borrow, return, renew, cancel, or pay for anything.
- You can only explain the process or current eligibility.

BORROW REQUEST:

If the context contains the borrow request process, explain it accurately.
Do not invent additional buttons, pages, forms, or approval steps.

RETURN:

Explain the return process only from the supplied context.

RENEWAL:

A loan can be renewed only when:
- It is not overdue.
- It is due within {DUE_SOON_THRESHOLD_DAYS} days.
- There is no pending renewal request.
- It has been renewed fewer than {MAX_RENEWALS} times.

However, ALWAYS use the student's actual database information
to determine whether the student is eligible.

FINES:

Use only actual fine information from the student account.
Never calculate or invent a fine unless the supplied context provides
the required information.

PERSONAL INFORMATION:

When the student asks about "my" books, "my" fines, "my" due dates,
or "my" borrowing limit, use only the authenticated student's
account information.

CATALOG:

Use only the supplied catalog results for book information.

ANSWER STYLE:

- Be friendly.
- Be concise.
- Normally answer in 2 to 4 sentences.
- If several questions are asked, answer each part clearly.
- Do not mention internal code, database queries, intents, or context.
"""


# ============================================================
# AI INTENT DETECTION
# ============================================================

def _detect_library_ai_intents(question):
    """
    Use Groq to understand what the student is asking.

    This is AI-based intent detection rather than
    hard-coded phrase matching.

    EXISTING FUNCTIONALITY PRESERVED.
    """

    from groq import Groq

    client = Groq(
        api_key=settings.GROQ_API_KEY
    )

    classifier_prompt = """
You are an intent classifier for a university library chatbot.

Classify the student's question into one or more of these intents:

- catalog
- borrow_request
- borrowing_limit
- personal_loans
- renewal
- return
- personal_fine

Definitions:

catalog:
Questions about books, authors, subjects, categories,
availability, ISBN, or finding books.

borrow_request:
Questions about how to borrow/request a book.

borrowing_limit:
Questions about how many books the student can borrow
or their borrowing capacity.

personal_loans:
Questions about books currently borrowed by the student,
their due dates, or what books they currently have.

renewal:
Questions about renewing or extending a student's loan.

return:
Questions about returning/giving back books.

personal_fine:
Questions about the student's fines, late fees,
penalties, or how much they owe.

Return ONLY valid JSON in this format:

{
    "intents": ["catalog"]
}

If the question contains multiple requests,
return multiple intents.

Example:

Question:
"Can I renew my Python book and do I have a fine?"

Answer:
{
    "intents": ["renewal", "personal_fine"]
}
"""

    messages = [
        {
            "role": "system",
            "content": classifier_prompt,
        },
        {
            "role": "user",
            "content": question,
        },
    ]

    try:

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=100,
            messages=messages,
            response_format={
                "type": "json_object"
            },
        )

        content = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

        result = json.loads(content)

        intents = result.get(
            "intents",
            []
        )

        allowed_intents = {
            "catalog",
            "borrow_request",
            "borrowing_limit",
            "personal_loans",
            "renewal",
            "return",
            "personal_fine",
        }

        intents = [
            intent
            for intent in intents
            if intent in allowed_intents
        ]

        if intents:
            return intents

    except Exception:
        pass

    # Safe fallback
    return ["catalog"]


# ============================================================
# CATALOG SEARCH
# ============================================================

def _search_catalog_for_question(question, limit=5):

    words = [
        word.strip(".,!?;:'\"")
        for word in question.split()
        if len(
            word.strip(".,!?;:'\"")
        ) > 2
    ]

    stop_words = {
        "the",
        "and",
        "for",
        "book",
        "books",
        "about",
        "with",
        "from",
        "have",
        "does",
        "there",
        "this",
        "that",
        "show",
        "find",
        "give",
        "please",
        "some",
        "any",
        "available",
        "availability",
        "author",
        "authors",
        "library",
        "libraries",
        "recommend",
        "recommendation",
        "good",
        "can",
        "you",
        "is",
        "are",
        "do",
        "me",
        "want",
        "need",
        "looking",
        "which",
        "what",
        "where",

        # ------------------------------------------
        # Keep recommendation/search queries clean
        # ------------------------------------------
        "suggest",
        "suggested",
        "suggestions",
        "recommended",
        "recommendations",
        "related",
    }

    words = [
        word
        for word in words
        if word.lower() not in stop_words
    ][:8]

    if not words:
        return LibraryResource.objects.none()

    query = Q()

    for word in words:

        query |= (
            Q(title__icontains=word)
            | Q(author__icontains=word)
            | Q(subject__icontains=word)

            # category is a ForeignKey
            # so category__title is used
            | Q(category__title__icontains=word)

            | Q(isbn_issn__icontains=word)
        )

    return (
        LibraryResource.objects
        .select_related(
            "library",
            "category",
        )
        .filter(
            status="ACTIVE"
        )
        .filter(query)
        .distinct()[:limit]
    )


# ============================================================
# FORMAT CATALOG CONTEXT
# ============================================================

def _format_catalog_context(books):

    if not books:
        return (
            "No matching active books were found "
            "in the catalog."
        )

    lines = []

    for book in books:

        lines.append(
            f'- "{book.title}" by '
            f'{book.author or "Unknown author"} — '
            f'{book.category.title if book.category else "Uncategorized"} — '
            f'{book.library.library_name if book.library else "Unknown library"} — '
            f'{book.available_copies} of '
            f'{book.total_copies} copies available'
        )

    return "\n".join(lines)


# ============================================================
# BORROW REQUEST WORKFLOW
# ============================================================

def _get_borrow_request_context():

    return """
BORROW REQUEST PROCESS:

To request a book:

1. Search for the book in the Library catalog.
2. Select the required book.
3. Use the "Request to Borrow" option when it is available.
4. The system checks:
   - The student's library profile.
   - Whether the profile is active.
   - Whether the student already has the book.
   - Whether the student already has a pending request.
   - Whether the student is within the borrowing limit.
   - Whether a copy is available.
5. If the checks pass, a BorrowRequest is created with PENDING status.
6. The request is then available for library staff review.

A borrow request does NOT mean that the book has already been issued.
Library staff must review the request before the book is issued.
"""


# ============================================================
# RETURN WORKFLOW
# ============================================================

def _get_return_context():

    return """
RETURN PROCESS:

When a borrowed book is returned:

- The BorrowTransaction is updated with the actual return date.
- The transaction status becomes RETURNED.
- The physical book copy becomes available again.
- The available-copy count is restored.
- If the book is returned after its due date, overdue days are calculated.
- A fine may be created or updated according to the library's fine rules.

The AI assistant only explains the return process.
It does not perform the return operation itself.
"""


# ============================================================
# STUDENT ACCOUNT CONTEXT
# ============================================================

def _build_student_context(library_user):

    if library_user is None:

        return (
            "This student does not have a library profile "
            "set up yet."
        )

    today = date.today()

    lines = []

    # ========================================================
    # MEMBERSHIP + BORROWING LIMIT
    # ========================================================

    active_loans_qs = (
        BorrowTransaction.objects
        .filter(
            library_user=library_user,
            status__in=[
                "ISSUED",
                "OVERDUE",
            ],
        )
        .select_related(
            "copy__resource"
        )
    )

    active_count = active_loans_qs.count()

    remaining_capacity = max(
        library_user.borrowing_limit
        - active_count,
        0,
    )

    membership_status = (
        "Active"
        if library_user.active
        else (
            "INACTIVE — cannot borrow until "
            "reactivated by staff"
        )
    )

    lines.append(
        f"Membership: {membership_status}."
    )

    lines.append(
        f"Borrowing limit: "
        f"{library_user.borrowing_limit} books."
    )

    lines.append(
        f"Currently checked out: "
        f"{active_count} book(s)."
    )

    lines.append(
        f"Remaining borrowing capacity: "
        f"{remaining_capacity} book(s)."
    )

    # ========================================================
    # CURRENT LOANS
    # ========================================================

    if active_loans_qs.exists():

        lines.append(
            "\nCurrent loans:"
        )

        for txn in active_loans_qs:

            days_left = (
                txn.due_date - today
            ).days

            if days_left < 0:

                due_status = (
                    f"{abs(days_left)} day(s) OVERDUE"
                )

            elif days_left == 0:

                due_status = "DUE TODAY"

            else:

                due_status = (
                    f"{days_left} day(s) left"
                )

            renewal_eligible = (
                txn.status == "ISSUED"
                and 0 <= days_left <= DUE_SOON_THRESHOLD_DAYS
                and not txn.renewal_requested
                and txn.renewal_count < MAX_RENEWALS
            )

            if txn.renewal_requested:

                renewal_note = (
                    "renewal already requested, "
                    "awaiting staff approval"
                )

            elif renewal_eligible:

                renewal_note = (
                    "eligible for renewal now"
                )

            else:

                renewal_note = (
                    "not eligible for renewal right now"
                )

            lines.append(
                f'- "{txn.copy.resource.title}" — '
                f'due {txn.due_date.strftime("%b %d, %Y")} '
                f'({due_status}) — '
                f'renewals used: '
                f'{txn.renewal_count}/'
                f'{MAX_RENEWALS} — '
                f'{renewal_note}'
            )

    else:

        lines.append(
            "\nCurrent loans: none."
        )

    # ========================================================
    # FINES
    # ========================================================

    fines_qs = (
        Fine.objects
        .filter(
            transaction__library_user=library_user
        )
        .select_related(
            "transaction__copy__resource"
        )
        .order_by(
            "-created_at"
        )
    )

    unpaid_fines = fines_qs.filter(
        payment_status="UNPAID"
    )

    total_unpaid = (
        unpaid_fines
        .aggregate(
            total=Sum("fine_amount")
        )["total"]
        or Decimal("0.00")
    )

    if fines_qs.exists():

        lines.append(
            f"\nFines: "
            f"{unpaid_fines.count()} unpaid fine(s) "
            f"totaling ${total_unpaid}."
        )

        for fine in fines_qs[:5]:

            book_title = (
                fine.transaction.copy.resource.title
                if fine.transaction
                and fine.transaction.copy
                else "Unknown book"
            )

            overdue_note = (
                f" — {fine.overdue_days} day(s) overdue"
                if fine.overdue_days
                else ""
            )

            lines.append(
                f'- "{book_title}" — '
                f'${fine.fine_amount} — '
                f'{fine.payment_status}'
                f'{overdue_note}'
            )

    else:

        lines.append(
            "\nFines: none on record."
        )

    return "\n".join(lines)


# ============================================================
# BUILD RELEVANT LIBRARY CONTEXT
# ============================================================

def _build_library_context(
    intents,
    question,
    library_user,
):
    """
    Retrieve ONLY information relevant to the detected intents.

    EXISTING FUNCTIONALITY PRESERVED.
    """

    context_parts = []

    matched_books = LibraryResource.objects.none()

    # ========================================================
    # CATALOG
    # ========================================================

    if "catalog" in intents:

        matched_books = (
            _search_catalog_for_question(
                question
            )
        )

        catalog_context = (
            _format_catalog_context(
                matched_books
            )
        )

        context_parts.append(
            "CATALOG RESULTS:\n"
            + catalog_context
        )

    # ========================================================
    # BORROW REQUEST
    # ========================================================

    if "borrow_request" in intents:

        context_parts.append(
            "BORROW REQUEST INFORMATION:\n"
            + _get_borrow_request_context()
        )

    # ========================================================
    # RETURN
    # ========================================================

    if "return" in intents:

        context_parts.append(
            "RETURN INFORMATION:\n"
            + _get_return_context()
        )

    # ========================================================
    # PERSONAL ACCOUNT
    # ========================================================

    personal_intents = {
        "personal_loans",
        "borrowing_limit",
        "renewal",
        "personal_fine",
    }

    if any(
        intent in personal_intents
        for intent in intents
    ):

        student_context = (
            _build_student_context(
                library_user
            )
        )

        context_parts.append(
            "STUDENT ACCOUNT:\n"
            + student_context
        )

    # ========================================================
    # SAFETY FALLBACK
    # ========================================================

    if not context_parts:

        context_parts.append(
            "No specific library information was retrieved."
        )

    return {
        "context": "\n\n".join(
            context_parts
        ),
        "matched_books": matched_books,
    }


# ============================================================
# NEW:
# GET OR CREATE AI CONVERSATION
# ============================================================

def _get_or_create_ai_conversation(
    user,
    conversation_id=None,
):
    """
    Get an existing conversation belonging to the
    authenticated user.

    If conversation_id is not supplied, reuse the latest
    active conversation.

    If no active conversation exists, create one.

    This does NOT change any existing AI functionality.
    It only adds persistence.
    """

    conversation = None

    # --------------------------------------------------------
    # Try supplied conversation UUID
    # --------------------------------------------------------

    if conversation_id:

        try:

            conversation = (
                AIConversation.objects
                .filter(
                    uuid=conversation_id,
                    user=user,
                    is_active=True,
                )
                .first()
            )

        except (
            ValueError,
            TypeError,
        ):

            conversation = None

    # --------------------------------------------------------
    # If no conversation was supplied/found,
    # use latest active conversation.
    # --------------------------------------------------------

    if conversation is None:

        conversation = (
            AIConversation.objects
            .filter(
                user=user,
                is_active=True,
            )
            .order_by(
                "-updated_at"
            )
            .first()
        )

    # --------------------------------------------------------
    # Create first conversation
    # --------------------------------------------------------

    if conversation is None:

        conversation = (
            AIConversation.objects.create(
                user=user,
                title="New Chat",
                is_active=True,
                is_full_crud=True,
            )
        )

    return conversation


# ============================================================
# NEW:
# UPDATE AI CONVERSATION TITLE
# ============================================================

def _update_ai_conversation_title(
    conversation,
    question,
):
    """
    Use the first question as the conversation title.

    Example:

        "suggest java books"

    becomes:

        "suggest java books"
    """

    if (
        conversation.title
        and conversation.title != "New Chat"
    ):
        return

    question = (
        question
        .strip()
    )

    if not question:
        return

    title = question[:100]

    if len(question) > 100:
        title += "..."

    conversation.title = title

    conversation.save(
        update_fields=[
            "title",
            "updated_at",
        ]
    )


# ============================================================
# NEW:
# LOAD DATABASE CHAT HISTORY
# ============================================================

def _get_ai_conversation_history(
    conversation,
    limit=6,
):
    """
    Load recent AIMessage rows for the conversation.

    The database history is used in addition to the existing
    frontend history, but we avoid duplicating the current
    question because the current question is added separately.
    """

    db_messages = list(
        AIMessage.objects
        .filter(
            conversation=conversation
        )
        .order_by(
            "-created_at"
        )[:limit * 2]
    )

    db_messages.reverse()

    history = []

    for message in db_messages:

        role = (
            "user"
            if message.role == "USER"
            else "assistant"
        )

        history.append(
            {
                "role": role,
                "content": message.content,
            }
        )

    return history


# ============================================================
# NEW:
# SAVE AI MESSAGE
# ============================================================

def _save_ai_message(
    conversation,
    role,
    content,
    intents=None,
    source_type="",
):
    """
    Save a user/assistant message.

    Existing AI response behavior is unaffected.
    """

    if intents is None:
        intents = []

    # Store multiple intents as comma-separated text.
    intent_text = ",".join(
        intents
    )

    return AIMessage.objects.create(
        conversation=conversation,
        role=role,
        content=content,
        intent=intent_text,
        source_type=source_type,
        is_full_crud=True,
    )


# ============================================================
# CALL GROQ
# ============================================================

def _call_ai(
    system_prompt,
    messages,
):

    from groq import Groq

    client = Groq(
        api_key=settings.GROQ_API_KEY
    )

    full_messages = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ] + messages

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=500,
        messages=full_messages,
    )

    return (
        response
        .choices[0]
        .message
        .content
        .strip()
    )


# ============================================================
# MAIN AI ASSISTANT
# ============================================================

@login_required
@require_POST
def library_ai_assistant(
    request,
    uuid,
):
    """
    POST:

    {
        "question": "...",
        "history": [...],
        "conversation_id": "optional UUID"
    }

    Returns:

    {
        "answer": "...",
        "intents": [...],
        "matched_books": [...],
        "conversation_id": "...",
        "conversation_title": "..."
    }
    """

    # ========================================================
    # SECURITY
    # ========================================================

    if str(
        request.user.uuid
    ) != str(uuid):

        return JsonResponse(
            {
                "error": "Unauthorized request."
            },
            status=403,
        )

    # ========================================================
    # READ REQUEST
    # ========================================================

    try:

        data = json.loads(
            request.body
        )

    except (
        json.JSONDecodeError,
        TypeError,
    ):

        return JsonResponse(
            {
                "error": "Invalid request."
            },
            status=400,
        )

    question = (
        data.get("question")
        or ""
    ).strip()

    # --------------------------------------------------------
    # EXISTING FRONTEND HISTORY
    # --------------------------------------------------------

    history = (
        data.get("history")
        or []
    )

    # --------------------------------------------------------
    # NEW:
    # DATABASE CONVERSATION ID
    #
    # Optional so the existing frontend continues working.
    # --------------------------------------------------------

    conversation_id = (
        data.get(
            "conversation_id"
        )
        or ""
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    if not question:

        return JsonResponse(
            {
                "error": "Please type a question."
            },
            status=400,
        )

    if len(question) > 500:

        return JsonResponse(
            {
                "error":
                    "Please keep questions under "
                    "500 characters."
            },
            status=400,
        )

    # ========================================================
    # CHECK GROQ API KEY
    # ========================================================

    if not getattr(
        settings,
        "GROQ_API_KEY",
        "",
    ):

        return JsonResponse(
            {
                "error":
                    "The AI assistant isn't configured yet. "
                    "Please contact library staff."
            },
            status=503,
        )

    # ========================================================
    # AUTHENTICATED STUDENT
    # ========================================================

    library_user = (
        LibraryUser.objects
        .filter(
            user=request.user
        )
        .first()
    )

    # ========================================================
    # NEW:
    # GET / CREATE AI CONVERSATION
    # ========================================================

    conversation = (
        _get_or_create_ai_conversation(
            user=request.user,
            conversation_id=conversation_id,
        )
    )

    _update_ai_conversation_title(
        conversation,
        question,
    )

    # ========================================================
    # AI INTENT DETECTION
    #
    # EXISTING FUNCTIONALITY — UNCHANGED
    # ========================================================

    intents = (
        _detect_library_ai_intents(
            question
        )
    )

    # ========================================================
    # RETRIEVE ONLY RELEVANT DATA
    #
    # EXISTING FUNCTIONALITY — UNCHANGED
    # ========================================================

    context_data = (
        _build_library_context(
            intents=intents,
            question=question,
            library_user=library_user,
        )
    )

    library_context = (
        context_data["context"]
    )

    matched_books = (
        context_data["matched_books"]
    )

    # ========================================================
    # BORROW REQUEST BUTTON INFORMATION
    #
    # EXISTING FUNCTIONALITY — UNCHANGED
    # ========================================================

    pending_resource_ids = set()
    borrowed_resource_ids = set()

    if library_user:

        pending_resource_ids = set(
            BorrowRequest.objects
            .filter(
                library_user=library_user,
                status="PENDING",
            )
            .values_list(
                "resource_id",
                flat=True,
            )
        )

        borrowed_resource_ids = set(
            BorrowTransaction.objects
            .filter(
                library_user=library_user,
                status__in=[
                    "ISSUED",
                    "OVERDUE",
                ],
            )
            .values_list(
                "copy__resource_id",
                flat=True,
            )
        )

    # ========================================================
    # CONVERSATION HISTORY
    #
    # EXISTING FRONTEND HISTORY IS STILL SUPPORTED.
    #
    # NEW DATABASE HISTORY IS ALSO LOADED.
    # ========================================================

    messages = []

    # --------------------------------------------------------
    # First use database history.
    # --------------------------------------------------------

    db_history = (
        _get_ai_conversation_history(
            conversation,
            limit=6,
        )
    )

    # --------------------------------------------------------
    # If database history exists, use it.
    # Otherwise preserve the existing frontend history.
    # --------------------------------------------------------

    if db_history:

        messages.extend(
            db_history
        )

    else:

        for turn in history[-6:]:

            role = (
                turn.get("role")
            )

            content = (
                turn.get("content")
            )

            if (
                role in (
                    "user",
                    "assistant",
                )
                and content
            ):

                messages.append(
                    {
                        "role": role,
                        "content": str(content)[:1000],
                    }
                )

    # ========================================================
    # SAVE USER MESSAGE
    #
    # IMPORTANT:
    # We save the user question AFTER obtaining previous
    # history so the current question is not duplicated.
    # ========================================================

    _save_ai_message(
        conversation=conversation,
        role="USER",
        content=question,
        intents=intents,
        source_type="",
    )

    # ========================================================
    # CURRENT QUESTION + CONTEXT
    # ========================================================

    messages.append(
        {
            "role": "user",
            "content": (
                "LIBRARY CONTEXT:\n\n"
                f"{library_context}\n\n"
                "STUDENT QUESTION:\n"
                f"{question}\n\n"
                "Answer using ONLY the supplied "
                "library context."
            ),
        }
    )

    # ========================================================
    # GENERATE AI ANSWER
    # ========================================================

    try:

        answer = _call_ai(
            AI_SYSTEM_PROMPT,
            messages,
        )

    except Exception as exc:

        print(
            "Library AI error:",
            repr(exc),
        )

        return JsonResponse(
            {
                "error":
                    "The AI assistant is temporarily "
                    "unavailable. Please try again shortly."
            },
            status=502,
        )

    # ========================================================
    # DETERMINE MESSAGE SOURCE
    #
    # This does NOT change the intent system.
    # It only records where the context came from.
    # ========================================================

    source_type = "GROQ"

    if "catalog" in intents:

        source_type = "CATALOG"

    elif any(
        intent in {
            "personal_loans",
            "borrowing_limit",
            "renewal",
            "personal_fine",
        }
        for intent in intents
    ):

        source_type = "PERSONAL_DATA"

    elif any(
        intent in {
            "borrow_request",
            "return",
        }
        for intent in intents
    ):

        source_type = "WORKFLOW"

    # ========================================================
    # SAVE ASSISTANT MESSAGE
    # ========================================================

    _save_ai_message(
        conversation=conversation,
        role="ASSISTANT",
        content=answer,
        intents=intents,
        source_type=source_type,
    )

    # ========================================================
    # BOOK CARDS
    #
    # EXISTING FUNCTIONALITY — UNCHANGED
    # ========================================================

    matched_books_data = []

    for book in matched_books:

        already_borrowed = (
            book.id
            in borrowed_resource_ids
        )

        already_pending = (
            book.id
            in pending_resource_ids
        )

        can_request = (
            library_user is not None
            and library_user.active
            and book.available_copies > 0
            and not already_borrowed
            and not already_pending
        )

        matched_books_data.append(
            {
                "title": book.title,

                "author": book.author,

                "library": (
                    book.library.library_name
                    if book.library
                    else ""
                ),

                "available_copies": (
                    book.available_copies
                ),

                "search_url": (
                    reverse(
                        "Student:student_library_home",
                        kwargs={
                            "uuid": uuid
                        },
                    )
                    + f"?q={quote(book.title)}"
                ),

                "can_request": (
                    can_request
                ),

                "already_borrowed":
                    already_borrowed,

                "already_pending":
                    already_pending,

                "request_url": (
                    reverse(
                        "Student:student_request_borrow",
                        kwargs={
                            "uuid": uuid,
                            "book_uuid": book.uuid,
                        },
                    )
                    if can_request
                    else None
                ),
            }
        )

    # ========================================================
    # RESPONSE
    #
    # Existing response fields are preserved.
    # New conversation fields are added.
    # ========================================================

    return JsonResponse(
        {
            "answer": answer,

            "intents": intents,

            "matched_books":
                matched_books_data,

            # =================================================
            # NEW CHAT HISTORY FIELDS
            # =================================================

            "conversation_id": str(
                conversation.uuid
            ),

            "conversation_title": (
                conversation.title
            ),
        }
    )