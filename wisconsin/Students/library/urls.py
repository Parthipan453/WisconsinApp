from django.urls import path
from . import views

urlpatterns = [

    # =====================================================
    # LIBRARY HOME
    # =====================================================
    path(
        "<uuid:uuid>/",
        views.student_library_home,
        name="student_library_home",
    ),

    # =====================================================
    # CREATE/SUBMIT a borrow request
    # =====================================================
    path(
        "<uuid:uuid>/request/<uuid:book_uuid>/",
        views.student_request_borrow,
        name="student_request_borrow",
    ),

    # =====================================================
    # VIEW all borrow requests
    # =====================================================
    path(
        "<uuid:uuid>/requests/",
        views.student_borrow_requests,
        name="student_borrow_requests",
    ),

    # =====================================================
    # CANCEL BORROW REQUEST
    # =====================================================
    path(
        "<uuid:uuid>/requests/<uuid:request_id>/cancel/",
        views.student_cancel_borrow_request,
        name="student_cancel_borrow_request",
    ),

    # =====================================================
    # QR
    # uuid = Student UUID
    # request_uuid = BorrowRequest UUID
    # =====================================================
    path(
        "<uuid:uuid>/borrow-request/<uuid:request_uuid>/qr/",
        views.student_borrow_request_qr,
        name="student_borrow_request_qr",
    ),

    # =====================================================
    # MY BORROWED BOOKS
    # =====================================================
    path(
        "<uuid:uuid>/borrowed/",
        views.student_borrowed_books,
        name="student_borrowed_books",
    ),

    # =====================================================
    # RENEW BOOK
    # =====================================================
    path(
        "<uuid:uuid>/borrowed-books/<int:transaction_id>/renew/",
        views.renew_book,
        name="student_library_renew_book",
    ),

    # =====================================================
    # NEW ARRIVALS
    # =====================================================
    path(
        "<uuid:uuid>/new-arrivals/",
        views.student_new_arrivals,
        name="student_new_arrivals",
    ),
    
    
        path(
            "<uuid:uuid>/new-arrivals/live-search/",
            views.student_new_arrivals_live_search,
            name="student_new_arrivals_live_search",
        ),

        # =====================================================
    # Add to Student/urls.py, alongside your other
    # uuid-scoped library paths
    # =====================================================

    path(
        "<uuid:uuid>/library/ai-assistant/",
        views.library_ai_assistant,
        name="student_library_ai_assistant",
    ),
    
]