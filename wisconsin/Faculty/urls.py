from django.urls import path, include
from . import views
from Staff import views as staff_views
from Faculty import views as faculty_views
from Faculty import views as comms_views
from Faculty.Elsa_Faculty.views import gradebook, attendance

urlpatterns = [

    # rupa
    path('facultybase/', views.facultybase, name='faculty_base'),
    path('facultydashboard/<uuid:uuid>/', views.FacultyDashboardView.as_view(), name='faculty_dashboard'),
    
    path('teaching/courses/<uuid:uuid>/', views.my_courses, name='my_courses_page'),
    path('teaching/schedule/<uuid:uuid>/', views.course_schedule, name='course_schedule_page'),
    path('teaching/roster/<uuid:uuid>/', views.class_roster, name='class_roster_page'),
    path('teaching/roster/data/<uuid:uuid>/', views.class_roster_ajax, name='class_roster_ajax'),
    path('teaching/attendance/<uuid:uuid>/', attendance, name='attendance_page'),
    path('teaching/gradebook/<uuid:uuid>/', gradebook, name='gradebook_page'),
    path('teaching/assignments/<uuid:uuid>/', views.assignments, name='assignments_page'),

    path('resources/library/', views.library, name='library'),
    path('resources/academic_resources/', views.academic_resources, name='academic_resources'),
    
    
    path("library/", include("Faculty.library.urls")),

    # rupa code ends



    
    # Gayathri G
    path('research/<uuid:uuid>/', views.FacultyResearchView.as_view(), name = 'faculty_research'),
    path('publications/<uuid:uuid>/', views.FacultyPublications.as_view(), name = 'faculty_publications'),
    path('grants/<uuid:uuid>/', views.FacultyGrants.as_view(), name = 'faculty_grants'),
    path('committee-work/<uuid:uuid>/', views.FacultyCommitteeWork.as_view(), name = 'faculty_committee-work'),
    path('office-hours/<uuid:uuid>/', views.FacultyOfficeHoursView.as_view(), name = 'faculty_office-hours'),


    # navina
    path('myprofile/<uuid:uuid>/',views.faculty_myprofile,name='faculty_myprofile'),
 
    path('faculty/<uuid:uuid>/notifications/',views.faculty_notifications,name='faculty_notifications'),
 
    path('faculty/<uuid:uuid>/settings/',views.faculty_settings,name='faculty_settings'),
    path('advisees/<uuid:uuid>/', views.FacultyAdvisees.as_view(), name = 'faculty_advisees'),
    
    # Navina
    path('advisor-dashboard/<uuid:uuid>/', views.FacultyAdvisorDashboard.as_view(), name = 'faculty_advisor-dashboard'),


    # ************************************************ Arun Code ********************************************************

    path("faculty/<uuid:uuid>/support-tickets/new/", views.faculty_submit_ticket, name="faculty_submit_ticket"),
    path("faculty/<uuid:uuid>/support-tickets/", views.faculty_my_tickets, name="faculty_my_tickets"),
    path('faculty/<uuid:uuid>/support-tickets/<int:ticket_id>/detail/', views.faculty_ticket_detail, name='faculty_ticket_detail'),
    path('faculty/<uuid:uuid>/support-tickets/<int:ticket_id>/update/', views.faculty_update_ticket, name='faculty_update_ticket'),

    path('faculty/<uuid:uuid>/notifications/history/', faculty_views.faculty_notification_history, name='faculty_notifications_history'),
    path('faculty/<uuid:uuid>/notifications/history/page/', staff_views.staff_notifications_page_ajax, name='faculty_notifications_page_ajax'),
    path('faculty/<uuid:uuid>/notifications/recent/', staff_views.recent_notifications_ajax, name='faculty_recent_notifications_ajax'),
    path('faculty/<uuid:uuid>/notifications/<int:notification_id>/read/', staff_views.mark_notification_read, name='faculty_mark_notification_read'),
    path('faculty/<uuid:uuid>/notifications/read-all/', staff_views.mark_all_notifications_read, name='faculty_mark_all_notifications_read'),
    ###########  kali  code start  ###########
    path("<uuid:uuid>/notifications/tournament-invitation/<uuid:invitation_uuid>/",views.faculty_tournament_invitation_detail,name="faculty_tournament_invitation_detail",),
    path("faculty/<uuid:uuid>/tournament-tracking/<uuid:invitation_uuid>/",views.faculty_tournament_tracking,name="faculty_tournament_tracking"),
    path("faculty/<uuid:uuid>/tournament-tracking/<uuid:invitation_uuid>/apply/",views.faculty_tournament_application_submit,name="faculty_tournament_application_submit"),
    path("<uuid:uuid>/tournament-track/filter/",views.faculty_tournament_track_filter,name="faculty_tournament_track_filter",),
    ###########  kali  code end ###########
    ############# luna's code start ###########
    path("",include("Faculty.luna.urls")),
    ############# luna's code end #############

    # ── Communications ──────────────────────────────────────────
    path('faculty/<uuid:uuid>/communications/', comms_views.faculty_communications, name='faculty_communications'),
    path('faculty/<uuid:uuid>/communications/thread/<int:thread_id>/', comms_views.faculty_thread_detail_ajax, name='faculty_thread_detail_ajax'),
    path('faculty/<uuid:uuid>/communications/send/', comms_views.faculty_send_message_ajax, name='faculty_send_message_ajax'),
    path('faculty/communications/reply/', comms_views.faculty_reply_message_ajax, name='faculty_reply_message_ajax'),
    path('faculty/<uuid:uuid>/communications/thread/<int:thread_id>/archive/', comms_views.faculty_archive_thread_ajax, name='faculty_archive_thread_ajax'),
    path('faculty/<uuid:uuid>/communications/thread/<int:thread_id>/unarchive/', comms_views.faculty_unarchive_thread_ajax, name='faculty_unarchive_thread_ajax'),
    path('faculty/<uuid:uuid>/communications/volume/', comms_views.faculty_volume_ajax, name='faculty_volume_ajax'),
    path('faculty/communications/search-recipients/', comms_views.faculty_search_recipients_ajax, name='faculty_search_recipients_ajax'),
    path("<uuid:uuid>/communications/unread/", views.faculty_unread_messages_ajax, name="faculty_unread_messages_ajax"),
    path('<uuid:uuid>/organizations/', views.faculty_my_organizations, name='faculty_my_organizations'),
    path('<uuid:uuid>/organizations/<int:org_id>/members/', views.faculty_org_members_ajax, name='faculty_org_members_ajax'),
    path('<uuid:uuid>/organizations/members/<int:membership_id>/remove/', views.faculty_remove_member_ajax, name='faculty_remove_member_ajax'),
    path('<uuid:uuid>/organizations/<int:org_id>/search-students/', views.faculty_search_students_ajax, name='faculty_search_students_ajax'),
    path('<uuid:uuid>/organizations/<int:org_id>/members/add/', views.faculty_add_member_ajax, name='faculty_add_member_ajax'),
    path('<uuid:uuid>/organizations/<int:org_id>/broadcast/', views.faculty_broadcast_message_ajax, name='faculty_broadcast_message_ajax'),
    path('<uuid:uuid>/organizations/<int:org_id>/chat/messages/', views.faculty_org_chat_messages_ajax, name='faculty_org_chat_messages_ajax'),
    path('<uuid:uuid>/organizations/<int:org_id>/chat/send/', views.faculty_org_chat_send_ajax, name='faculty_org_chat_send_ajax'),

    path('<uuid:uuid>/downloads/', views.faculty_downloads, name='faculty_downloads'),
    path('<uuid:uuid>/downloads/<int:resource_id>/download/', views.faculty_download_resource, name='faculty_download_resource'),

    # ************************************************ Arun Code ********************************************************

    # ================ Jordan code start here =====================

    path('',include('Faculty.jordan.urls')),
    
    # ================ Jordan code ends here =====================
    ## leo's code start ##
    path("", include("Faculty.leo.urls")),
    ## leo's code end ##


    # <==== ELSA CODE START ====>
    path("", include('Faculty.Elsa_Faculty.urls')),
    path("", include('Research.Elsa_research.urls')),
    # <==== ELSA CODE END ====>




    #<================================Blaze Code Start(22.07.26)================================>


    path('leave-dashboard/<uuid:uuid>/', views.faculty_leave_dashboard, name='faculty_leave_request'),
    # Crud 
    path('leave-request/submit/<uuid:uuid>/', views.submit_leave_request, name='submit_leave_request'),
    path('leave-request/cancel/<uuid:uuid>/<int:leave_id>/', views.cancel_leave_request, name='cancel_leave_request'),
    path('leave-request/details/<uuid:uuid>/<int:leave_id>/', views.get_leave_details, name='get_leave_details'),
    path('leave-request/update/<uuid:uuid>/<int:leave_id>/', views.update_leave_request, name='update_leave_request'), 
    # Balance
    path('leave-balance/<uuid:uuid>/', views.get_leave_balance, name='get_leave_balance'),
    # Comments
    # path('leave-comment/<uuid:uuid>/<int:leave_id>/', views.add_leave_comment, name='add_leave_comment'),
    # Export
    path('leave-export/<uuid:uuid>/', views.export_leave_report, name='export_leave_report'),




    path('housing/<uuid:uuid>/', views.faculty_housing_view, name='faculty_housing'),
    path('get-available-rooms/<uuid:uuid>/', views.faculty_get_available_rooms_json, name='faculty_get_available_rooms'),
    path('maintenance-request-submit/<uuid:uuid>/', views.faculty_maintenance_request_submit, name='faculty_maintenance_request_submit'),    

    #<================================Blaze Code End(22.07.26)================================>


    # Jack urls Start

    path("", include("Faculty.Jack.urls")),
    
    # Jack urls End



]
