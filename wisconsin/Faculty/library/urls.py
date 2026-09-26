from django.urls import path
from . import views

urlpatterns = [

    path(
        "<uuid:uuid>/",
        views.faculty_library_home,
        name="faculty_library_home",
    ),

    path(
        "<uuid:uuid>/request/<uuid:book_uuid>/",
        views.faculty_request_borrow,
        name="faculty_borrow_request",
    ),

    path(
        "<uuid:uuid>/requests/",
        views.faculty_borrow_requests,
        name="faculty_borrow_requests",
    ),

    path(
        "<uuid:uuid>/requests/<uuid:request_id>/cancel/",
        views.faculty_cancel_borrow_request,
        name="faculty_cancel_borrow_request",
    ),

    path(
        "<uuid:uuid>/borrow-request/<uuid:request_uuid>/qr/",
        views.faculty_borrow_request_qr,
        name="faculty_borrow_request_qr",
    ),

    path(
        "<uuid:uuid>/borrowed/",
        views.faculty_borrowed_books,
        name="faculty_borrowed_books",
    ),

    path(
        "<uuid:uuid>/borrowed-books/<int:transaction_id>/renew/",
        views.faculty_renew_book,
        name="faculty_library_renew_book",
    ),
    
    
    path(
        "<uuid:uuid>/new-arrivals/",
        views.faculty_new_arrivals,
        name="faculty_new_arrivals",
    ),
    
    path(
        "<uuid:uuid>/new-arrivals/live-search/",
        views.faculty_new_arrivals_live_search,
        name="faculty_new_arrivals_live_search",
    ),

]