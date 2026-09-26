from django.urls import path
from . import views

urlpatterns = [
    path("admin_dashboard/", views.dashboard_base, name="library_admin_dashboard"),

    path("dashboard/<uuid:uuid>/", views.dashboard, name="library_dashboard"),


    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/edit/<uuid:category_uuid>/', views.category_edit, name='category_edit'),
    path('categories/delete/<uuid:category_uuid>/', views.category_delete, name='category_delete'),
    path('categories/toggle/<uuid:category_uuid>/', views.category_toggle, name='category_toggle'),

    # buildings

    path(
    "buildings/",
    views.building_list,
    name="building_list"
    ),
    path(
        "buildings/<int:building_id>/libraries/",
        views.building_libraries,
        name="building_libraries"
    ),

    path(
        "buildings/add/",
        views.building_add,
        name="building_add"
    ),

    path(
        "buildings/<int:building_id>/edit/",
        views.building_edit,
        name="building_edit"
    ),

    path(
        "buildings/<int:building_id>/delete/",
        views.building_delete,
        name="building_delete"
    ),

    path(
        "buildings/<int:building_id>/toggle/",
        views.building_toggle,
        name="building_toggle"
    ),



    path("books/",views.library_books,name="library_books"),

    path("books/add/",views.add_book,name="add_book",),

    path("books/view/<uuid:uuid>/",views.view_book,name="view_book",),

    path("books/edit/<uuid:uuid>/",views.edit_book,name="edit_book",),

    path("books/delete/<uuid:uuid>/",views.delete_book,name="delete_book",),

    path("libraries/",views.library_list,name="library_list"),

    path("libraries/add/",views.add_library,name="add_library",),

    path("libraries/delete/<int:pk>/",views.delete_library,name="delete_library",),

    path("libraries/edit/<int:pk>/",views.edit_library,name="edit_library",),

    path("libraries/view/<int:pk>/",views.view_library,name="view_library",),

    path("borrow-requests/",views.borrow_requests,name="borrow_requests",),

    path("borrow-request/<uuid:request_uuid>/",views.borrow_request_details,name="borrow_request_details",),

    path("fine-management/",views.fine_management,name="fine_management",),

    path("fine/<int:fine_id>/",views.fine_details,name="fine_details"),

    path("fines/<int:fine_id>/collect/",views.collect_fine,name="collect_fine"),

    path("fines/export/pdf/",views.export_fines_pdf,name="export_fines_pdf"),

    path("fines/export/excel/",views.export_fines_excel,name="export_fines_excel"),

    path("fines/<int:fine_id>/send-acknowledgement/",views.send_fine_acknowledgement,name="send_fine_acknowledgement",),

    path("renewal-requests/",views.renewal_requests,name="renewal_requests",),

    path("renewal-requests/<int:transaction_id>/approve/",views.approve_renewal,name="approve_renewal",),

    path("book-management-report/",views.book_management_report,name="book_management_report",),

    path("book-management-report/export/pdf/",views.export_book_management_report_pdf,name="book_management_report_pdf",),

    path("book-management-report/export/excel/",views.export_book_management_report_excel,name="book_management_report_excel",),

    path("members/",views.library_members,name="library_members",),

    path("members/ajax/",views.library_members_ajax,name="library_members_ajax",),

    path("members/<int:member_id>/details/",views.library_member_details_ajax,name="library_member_details_ajax",),

    path(
        "form-submissions/",
        views.library_form_submissions,
        name="library_form_submissions",
    ),


    # AJAX filtering
    path(
        "form-submissions/filter/",
        views.library_form_submissions_filter_ajax,
        name="library_form_submissions_filter_ajax",
    ),


    # AJAX modal details
    path(
        "form-submissions/<str:form_type>/<int:submission_id>/",
        views.library_form_submission_ajax,
        name="library_form_submission_ajax",
    ),

    

    
    
    
    path(
    "issue-queue/",
    views.issue_queue,
    name="issue_queue",
    ),
    
     
    path(
    "issue-queue/<uuid:request_uuid>/",
    views.issue_book_detail,
    name="issue_book_detail",
    ),
    
    
    # path(
    #     "issue-queue/<uuid:request_uuid>/verify-pin/",
    #     views.verify_issue_pin,
    #     name="verify_issue_pin",
    # ),
    
    # path(
    #     "issue-queue/<uuid:request_uuid>/verify/",
    #     views.issue_book_qr_entry,
    #     name="issue_book_qr_entry",
    # ),
    
    path(
        "active-loans/",
        views.active_loans,
        name="active_loans",
    ),
    
    path(
        "active-loans/<int:transaction_id>/return/",
        views.mark_returned,
        name="mark_returned",
    ),
    
    
    path(
        "active-loans/export/excel/",
        views.export_active_loans_excel,
        name="export_active_loans_excel",
    ),
    
    path(
        "active-loans/export/pdf/",
        views.export_active_loans_pdf,
        name="export_active_loans_pdf",
    ),
    
    
    # notifications
    
    path(
        "notifications/",
        views.library_notifications,
        name="library_notifications",
    ),
    
    path(
        "notifications/all/",
        views.library_all_notifications,
        name="library_all_notifications",
    ),
        
    
    
    path(
        "notifications/mark-all-read/",
        views.library_notifications_mark_all_read,
        name="library_notifications_mark_all_read",
    ),

    path(
        "notifications/<int:notification_id>/read/",
        views.library_notification_mark_read,
        name="library_notification_mark_read",
    ),
  
]