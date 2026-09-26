

 
# ***************************************************** Arun Code ******************************************************

from django.urls import path, include
from . import views
from Staff import views as staff_views
from Students import views as comms_views

app_name = "Student"

urlpatterns = [
    
    
    path("dashboard/<uuid:uuid>/", views.student_dashboard, name="student_dashboard"),
    path("profile/<uuid:uuid>/", views.student_profile, name="student_profile"),
    path(
        "profile/addresses/<uuid:uuid>/",
        views.student_addresses,
        name="student_addresses",
    ),
    
    path(
        "profile/emergency/<uuid:uuid>/",
        views.student_emergency_contacts,
        name="student_emergency_contacts",
    ),
    path(
        "profile/documents/<uuid:uuid>/",
        views.student_documents,
        name="student_documents",
    ),
    # ── Finance ────────────────────────────────────────────────────────
    path('finance/aid/<uuid:uuid>/', views.student_financial_aid, name='student_financial_aid'),
    path('finance/payments/<uuid:uuid>/', views.student_fee_payments,name='student_fee_payments'),
    

    path('finance/aid/<uuid:uuid>/detail/<int:aid_id>/', views.student_financial_aid_detail, name='student_financial_aid_detail'),
    path('finance/aid/<uuid:uuid>/print/<int:aid_id>/', views.student_financial_aid_print, name='student_financial_aid_print'),
    path('finance/aid/<uuid:uuid>/update/<int:aid_id>/', 
         views.update_financial_aid, 
         name='update_financial_aid'),
    path('finance/aid/<uuid:uuid>/edit/<int:aid_id>/', views.student_financial_aid_edit, name='student_financial_aid_edit'),
        path('finance/aid/<uuid:uuid>/cancel/<int:aid_id>/', 
         views.cancel_financial_aid, 
         name='cancel_financial_aid'),
 
    # ── Settings ───────────────────────────────────────────────────────
    path( 'settings/notifications/<uuid:uuid>/', views.student_notifications, name='student_notifications'),
    path('settings/security/<uuid:uuid>/', views.student_account_security, name='student_account_security'),
    
    # AJAX Endpoints (add these)
    path('settings/security/change-password-ajax/', views.change_password_ajax, name='change_password_ajax'),
    path('settings/security/2fa/setup-ajax/', views.setup_2fa_ajax, name='setup_2fa_ajax'),
    path('settings/security/2fa/verify-ajax/', views.verify_2fa_ajax, name='verify_2fa_ajax'),
    path('settings/security/2fa/disable-ajax/', views.disable_2fa_ajax, name='disable_2fa_ajax'),
    path('settings/security/2fa/backup-codes-ajax/', views.get_backup_codes_ajax, name='backup_codes_ajax'),
    path('settings/security/sessions/revoke-ajax/', views.revoke_session_ajax, name='revoke_session_ajax'),
    path('settings/security/sessions/revoke-all-ajax/', views.revoke_all_sessions_ajax, name='revoke_all_sessions_ajax'),
    path('settings/security/deactivate-ajax/', views.deactivate_account_ajax, name='deactivate_account_ajax'),
    path('settings/security/delete-account-ajax/', views.delete_account_ajax, name='delete_account_ajax'),

    # parth update start(17.06.2026)
    #Academic related urls


    path('my-courses/<uuid:uuid>/', views.my_courses, name='my_courses'),   
    path('schedule/<uuid:uuid>/', views.schedule_view, name='schedule'),
    path('grades/<uuid:uuid>/', views.grades_view, name='grades'),
    path('degree-progress/<uuid:uuid>/', views.degree_progress_view, name='degree_progress'),
    path('transcripts/<uuid:uuid>/', views.transcripts_view, name='transcripts'),


    #<----------------------Blaze Code Start(18.06.2026)--------------------------->

    path('housing/<uuid:uuid>/', views.housing_view, name='housing'),
    path('get-available-rooms/<uuid:uuid>/', views.get_available_rooms_json, name='get_available_rooms'),
    path('maintenance-request-submit/<uuid:uuid>/', views.maintenance_request_submit, name='maintenance_request_submit'),



    
    path('organizations/<uuid:uuid>/', views.organizations_view, name='organizations'),
    path('research/<uuid:uuid>/', views.research_view, name='research'),
    path('career-profile/<uuid:uuid>/', views.career_profile_view, name='career_profile'),


    #<----------------------Blaze Code End  (18.06.2026)--------------------------->

    
    # ************************************************ Arun Code ********************************************************
    
    path("student/<uuid:uuid>/support-tickets/new/", views.submit_support_ticket, name="submit_support_ticket"),
    path("student/<uuid:uuid>/support-tickets/", views.my_support_tickets, name="my_support_tickets"),
    path("student/<uuid:uuid>/support-tickets/<int:ticket_id>/detail/", views.ticket_detail, name="ticket_detail"),
    path("student/<uuid:uuid>/support-tickets/<int:ticket_id>/update/", views.update_ticket, name="update_ticket"),

    path('student/<uuid:uuid>/notifications/history/', views.student_notification_history, name='student_notifications_history'),
    path('student/<uuid:uuid>/notifications/history/page/', staff_views.staff_notifications_page_ajax, name='student_notifications_page_ajax'),
    path('student/<uuid:uuid>/notifications/recent/', staff_views.recent_notifications_ajax, name='student_recent_notifications_ajax'),
    path('student/<uuid:uuid>/notifications/<int:notification_id>/read/', staff_views.mark_notification_read, name='student_mark_notification_read'),
    path('student/<uuid:uuid>/notifications/read-all/', staff_views.mark_all_notifications_read, name='student_mark_all_notifications_read'),


    path("<uuid:uuid>/communications/", comms_views.student_communications,name="student_communications"),
    path("<uuid:uuid>/communications/thread/<int:thread_id>/",comms_views.student_thread_detail_ajax,name="student_thread_detail_ajax"),
    path("<uuid:uuid>/communications/send/",comms_views.student_send_message_ajax,name="student_send_message_ajax"),
    path("communications/reply/",comms_views.student_reply_message_ajax,name="student_reply_message_ajax"),
    path("<uuid:uuid>/communications/thread/<int:thread_id>/archive/",comms_views.student_archive_thread_ajax,name="student_archive_thread_ajax",),
    path("<uuid:uuid>/communications/thread/<int:thread_id>/unarchive/",comms_views.student_unarchive_thread_ajax,name="student_unarchive_thread_ajax"),
    path("<uuid:uuid>/communications/volume/",comms_views.student_volume_ajax,name="student_volume_ajax"),
    path("communications/search-recipients/",comms_views.student_search_recipients_ajax,name="student_search_recipients_ajax"),
    path("<uuid:uuid>/communications/check-new-messages/",comms_views.student_check_new_messages,name="student_check_new_messages",),

    path('<uuid:uuid>/downloads/', views.student_downloads, name='student_downloads'),
    path('<uuid:uuid>/downloads/<int:resource_id>/download/', views.student_download_resource, name='student_download_resource'),

    path('<uuid:uuid>/organizations/browse/', views.browse_organizations_ajax, name='browse_organizations_ajax'),
    path('<uuid:uuid>/organizations/', views.organizations_view, name='organizations'),
    path('<uuid:uuid>/organizations/browse/', views.browse_organizations_ajax, name='browse_organizations_ajax'),
    path('<uuid:uuid>/organizations/<int:org_id>/join/', views.request_join_organization, name='request_join_organization'),
    path('<uuid:uuid>/organizations/membership/<int:membership_id>/leave/', views.leave_organization, name='leave_organization'),

    path('<uuid:uuid>/organizations/<int:org_id>/chat/messages/', views.student_org_chat_messages_ajax, name='student_org_chat_messages_ajax'),

    path('<uuid:uuid>/organizations/<int:org_id>/chat/send/', views.student_org_chat_send_ajax, name='student_org_chat_send_ajax'),

    # ************************************************ Arun Code ********************************************************

#<----------------------Blaze Code Start(25.07.26)------------------------->

    path('leave-dashboard/<str:uuid>/', views.student_leave_dashboard, name='student_leave_dashboard'),
    path('leave-submit/<str:uuid>/', views.submit_student_leave, name='submit_student_leave'),
    path('leave-cancel/<str:uuid>/<int:leave_id>/', views.cancel_student_leave, name='cancel_student_leave'),
    path('leave-details/<str:uuid>/<int:leave_id>/', views.get_student_leave_details, name='get_student_leave_details'),
    path('leave-update/<str:uuid>/<int:leave_id>/', views.update_student_leave, name='update_student_leave'),
    path('leave-balance/<str:uuid>/', views.get_student_leave_balance, name='get_student_leave_balance'),
    path('leave-export/<str:uuid>/', views.export_student_leave_report, name='export_student_leave_report'),

#<----------------------Blaze Code End(25.07.26)--------------------------->
    
    # ***********************************Rupa code start ************************************************
    # Library URLs - Student Library Module
    path(
        "",include("Students.library.urls")
    ),

    
    
    # **********************************Rupa code end ***************************************************


    path('',include('Students.jordan.urls')),

    # Jack urls Start

    path("", include("Students.Jack.urls")),
    
    # Jack urls End

    #-------------------------luna urls Start---------------------------------------#

    path("", include("Students.luna.urls")),
    
    #--------------------------luna urls End----------------------------------------#

]
urlpatterns += [
    path("", include("Students.Leo_Student.urls")),
]


# ***************************************************** Arun Code ******************************************************
