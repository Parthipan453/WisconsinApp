from django.urls import path
from . import views

urlpatterns = [

    # =====================================================
    # LIBRARY HOME
    # =====================================================
    path(
        "<uuid:uuid>/",
        views.staff_library_home,
        name="staff_library_home",
    ),

    # =====================================================
    # REQUEST TO BORROW
    # uuid      = Staff UUID
    # book_uuid = Book/LibraryResource UUID
    # =====================================================
    path(
        "<uuid:uuid>/request/<uuid:book_uuid>/",
        views.staff_request_borrow,
        name="staff_borrow_request",
    ),

    # =====================================================
    # BORROW REQUESTS
    # =====================================================
    path(
        "<uuid:uuid>/requests/",
        views.staff_borrow_requests,
        name="staff_borrow_requests",
    ),

    # =====================================================
    # CANCEL BORROW REQUEST
    # =====================================================
    path(
        "<uuid:uuid>/requests/<uuid:request_id>/cancel/",
        views.staff_cancel_borrow_request,
        name="staff_cancel_borrow_request",
    ),

    # =====================================================
    # QR
    # uuid         = Staff UUID
    # request_uuid = BorrowRequest UUID
    # =====================================================
    path(
        "<uuid:uuid>/borrow-request/<uuid:request_uuid>/qr/",
        views.staff_borrow_request_qr,
        name="staff_borrow_request_qr",
    ),

    # =====================================================
    # MY BORROWED BOOKS
    # =====================================================
    path(
        "<uuid:uuid>/borrowed/",
        views.staff_borrowed_books,
        name="staff_borrowed_books",
    ),

    # =====================================================
    # RENEW BOOK
    # uuid           = Staff UUID
    # transaction_id = BorrowTransaction ID
    # =====================================================
    path(
        "<uuid:uuid>/borrowed-books/<int:transaction_id>/renew/",
        views.staff_renew_book,
        name="staff_library_renew_book",
    ),
    
    path(
            "<uuid:uuid>/new-arrivals/",
            views.staff_new_arrivals,
            name="staff_new_arrivals",
        ),
    
    
    path(
        "<uuid:uuid>/new-arrivals/live-search/",
        views.staff_new_arrivals_live_search,
        name="staff_new_arrivals_live_search",
    ),


]