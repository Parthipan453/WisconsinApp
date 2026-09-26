from django.urls import path, include
from . import views
from .views import *
from General.views import *
# from swetha.views import *
from Students.views import next_student_number_json
from Faculty.views import next_faculty_id_json
from Staff.views import next_staff_id_json

urlpatterns = [
    # /* kali's  code  */
    path("user/" ,views.user_create,name="user_create"),
    path("users/", views.user_page, name="user_page"),

    # *********************************** Arun Code ************************************************************

    path( 'users/next-student-number/', next_student_number_json, name='next_student_number'),
    path( 'users/next-faculty-id/', next_faculty_id_json, name='next_faculty_id'),
    path( 'users/next-staff-id/', next_staff_id_json, name='next_staff_id'),
    path("users/check-unique/", views.check_field_unique_json, name="check_field_unique"),

    path("ajax/get-schools/",views.get_schools, name="get_schools",),
    path("ajax/get-degrees/",views.get_degrees,name="get_degrees",),
    path("ajax/get-programs/",views.get_programs,name="get_programs",),
    path("ajax/get-departments/",views.get_departments,name="get_departments",),

    # *********************************** Arun Code ************************************************************

    path("role/", views.role, name="role"),
    path("api/roles/assignments/", views.role_assignments_json, name="role_assignments_json"),
    path("api/roles/create/", views.role_create_json, name="role_create_json"),
    path("api/roles/<int:uid>/unassign/", views.role_unassign_json, name="role_unassign_json"),
    path("api/users/list/", views.users_json, name="users_json"),
    # path("user/<uuid:uid>/edit/", views.user_edit,   name="user_edit"),
    path("user/<uuid:uid>/view/", views.user_view, name="user_view"),
    # path("api/users/<int:uid>/update/", views.user_update_json, name="user_update_json"),
    path("api/users/<int:uid>/delete/", views.user_delete_json, name="user_delete_json"),
    path("api/users/<int:uid>/status/", views.user_status_update_json, name="user_status_update_json"),
    path('roles/<int:role_id>/details/',         views.role_detail_json,           name='role_detail_json'),
    path('roles/<int:role_id>/available-users/', views.role_available_users_json,  name='role_available_users_json'),
    path('roles/<int:role_id>/assign-users/',    views.role_assign_users_json,     name='role_assign_users_json'),
    path('roles/<int:role_id>/revoke-user/',     views.role_revoke_user_json,      name='role_revoke_user_json'),
    path('roles/<int:role_id>/update/',          views.role_update_json,           name='role_update_json'),
    path('roles/<int:role_id>/convert-users/',   views.role_convert_users_json,    name='role_convert_users_json'),
    path("audit-logs/", views.audit_log_page, name="audit_log_page"),
    path("api/audit-logs/", views.audit_log_json, name="audit_log_json"),
    path("firearms/", views.firearm_page, name="firearm_page"),
    path("firearm-management/users/search/",views.firearm_user_search_json,name="firearm_user_search_json"),
    path("firearm-management/create/",views.firearm_create_json,name="firearm_create_json"),
    path("firearm-management/<int:fid>/update/", views.firearm_update_json, name="firearm_update_json"),
    path("firearm/view/<uuid:uid>/", views.firearm_view, name="firearm_view"),
    path("olympics/athletes/", views.olympic_athlete_page, name="olympic_athlete_page"),
    path("olympics/performances/", views.olympic_performance_page, name="olympic_performance_page"),
    path("olympics/performances/data/", views.olympic_performance_data_json, name="olympic_performance_data_json"),
    path("olympics/athletes/data/", views.olympic_athlete_data_json, name="olympic_athlete_data_json"),
    path("olympics/athletes/add/", views.olympic_athlete_add_page, name="olympic_athlete_add_page"),
    path("olympics/athletes/create/", views.olympic_athlete_create_json, name="olympic_athlete_create_json"),
    path("olympics/athletes/<uuid:uuid>/edit/", views.olympic_athlete_edit_page, name="olympic_athlete_edit_page"),
    path("olympics/athletes/<uuid:uuid>/update/", views.olympic_athlete_update_json, name="olympic_athlete_update_json"),
    path("olympics/performances/add/", views.olympic_performance_add_page, name="olympic_performance_add_page"),
    path("olympics/performances/create/", views.olympic_performance_create_json, name="olympic_performance_create_json"),
    path("olympics/performances/<uuid:uuid>/", views.olympic_performance_detail_json, name="olympic_performance_detail_json"),
    path("olympics/performances/<uuid:uuid>/edit/", views.olympic_performance_edit_page, name="olympic_performance_edit_page"),
    path("olympics/performances/<uuid:uuid>/update/", views.olympic_performance_update_json, name="olympic_performance_update_json"),
    path("olympics/performances/<uuid:uuid>/archive/", views.olympic_performance_archive_json, name="olympic_performance_archive_json"),
    path("olympics/performances/<uuid:uuid>/restore/", views.olympic_performance_restore_json, name="olympic_performance_restore_json"),
    path("tournaments/", views.tournament_dashboard_page, name="tournament_dashboard_page"),
    path("tournaments/create/", views.tournament_create_page, name="tournament_create_page"),
    path("tournaments/create/submit/", views.tournament_create_json, name="tournament_create_json"),
    path("tournaments/invitation/colleges/", views.tournament_invitation_colleges_json, name="tournament_invitation_colleges_json"),
    path("tournaments/invitation/faculty/", views.tournament_invitation_faculty_json, name="tournament_invitation_faculty_json"),
    path("tournaments/invitation/<uuid:invitation_uuid>/", views.tournament_invitation_detail_json, name="tournament_invitation_detail_json"),
    path("tournaments/invitation/<uuid:invitation_uuid>/action/", views.tournament_invitation_action_json, name="tournament_invitation_action_json"),
    path("tournaments/apply/<uuid:invitation_token>/", views.email_tournament_apply_page, name="email_tournament_apply_page"),
    path("tournaments/apply/<uuid:invitation_token>/send-otp/", views.email_tournament_apply_send_otp_json, name="email_tournament_apply_send_otp_json"),
    path("tournaments/apply/<uuid:invitation_token>/submit/", views.email_tournament_apply_submit_json, name="email_tournament_apply_submit_json"),
    path("tournaments/<uuid:tournament_uuid>/view/", views.tournament_view, name="tournament_view"),
    path("tournaments/<uuid:tournament_uuid>/complete/", views.tournament_complete_json, name="tournament_complete_json"),
    path("reports/sports/", views.sports_reports_page, name="sports_reports_page"),
    path("reports/sports/data/", views.sports_reports_data_json, name="sports_reports_data_json"),
    path("reports/sports/export/excel/", views.sports_reports_export_excel, name="sports_reports_export_excel"),
    path("reports/sports/export/pdf/", views.sports_reports_export_pdf, name="sports_reports_export_pdf"),
    # /* kali's  code end */
 
    ####### Guru code start ########

    path("students/", views.students, name="students"),
    path("", include("Admin.Jack.urls")),

    ####### Guru code end ########
    
    ####### swetha's code start ######## 
    
    path("", include("Admin.swetha.urls")),
    
    ####### swetha's code end ########
    ####### MrGow code start ########
    path("", include("Admin.Alan.urls")), 
    ####### MrGow code end ########
    # <==== ELSA CODE START ====>
    path("", include('Admin.Elsa_admin.urls')),
    path("", include('Research.Elsa_research.urls')),
    # <==== ELSA CODE END ====>
    ## Leo's Code Start ##
    path("", include("Admin.Leo_admin.urls")),
    ## Leo's Code End ##

    path("", include('Admin.Alan.urls')),

    ####### MrGow code end ########
    
    # Dominic Code Start's
    path("", include('Admin.Dominic.urls')),
    # Dominic Code End's

    #Eric code
    path("", include('Admin.Eric.urls')),
    
    # Nebula
    path('', include('Admin.Nebula.urls')),

    #swetha's code start ## 
    
    path("user/<uuid:user_id>/edit/",views.user_edit,name="user_edit",),
    path("user/<uuid:user_id>/update/",views.user_update,name="user_update",),

    #swetha's code end ## 




##############  Rixie code start ################
    path("buildings/", views.building_page, name="building_page"),
path("floors/", views.floors_page, name="floor_page"),
path(
    "floors/<int:floor_id>/edit/",
    views.floor_edit,
    name="floor_edit"
),
path("rooms/", views.room_page, name="room_page"),
   path(
        "buildings/add/",
        views.building_add,
        name="admin_building_add"
    ),
path(
    "buildings/<int:building_id>/edit/",
    building_edit,
    name="admin_building_edit"
),
path(
    "buildings/<int:building_id>/inactivate/",
    views.building_inactivate,
    name="building_inactivate"
),
path(
    "buildings/export/excel/",
    views.building_export_excel,
    name="building_excel"
),
path(
    "buildings/export/pdf/",
    views.building_export_pdf,
    name="building_pdf"
),
path(
    "floors/export/excel/",
    views.floor_export_excel,
    name="floor_excel"
),
path(
    "floors/export/pdf/",
    views.floor_export_pdf,
    name="floor_pdf"
),



path(
    "rooms/add/",
    views.add_room,
    name="rixie_add_room"
),

path(
    "rooms/floors/",
    views.room_floors,
    name="room_floors"
),

path(
    "rooms/edit/<int:room_id>/",
    views.edit_room,
    name="edit_room",
),

path(
    "rooms/export/excel/",
    views.room_export_excel,
    name="room_excel"
),

path(
    "rooms/export/pdf/",
    views.room_export_pdf,
    name="room_pdf"
),

###############  Rixie code End ###############
    #<-----------------Blaze code start---------------->

    path('hostel-dashboard/<uuid:uuid>/', views.hostel_dashboard, name='hostel_dashboard'),
    
    path('hostels/<uuid:uuid>/', views.hostel_list, name='hostel_list'),
    path('hostel-detail/<uuid:uuid>/<int:hostel_id>/', views.hostel_detail, name='hostel_detail'),
    
    path('add-hostel/<uuid:uuid>/', views.add_hostel_json, name='add_hostel'),
    path('update-hostel/<uuid:uuid>/<int:hostel_id>/', views.update_hostel_json, name='update_hostel'),
    path('delete-hostel/<uuid:uuid>/<int:hostel_id>/', views.delete_hostel_json, name='delete_hostel'),
    path('hostel-details/<uuid:uuid>/<int:hostel_id>/', views.hostel_details_json, name='hostel_details'),
    
    path('students/<uuid:uuid>/', views.student_list, name='student_list'),
    path('student-details/<uuid:uuid>/<int:student_id>/', views.student_detail_json, name='student_detail'),
    
    path('room-management/<uuid:uuid>/', views.room_management, name='hostel_room_management'),
    path('add-room/<uuid:uuid>/', views.add_room_page, name='add_room_page'),
    path('add-room-ajax/<uuid:uuid>/', views.add_room_json, name='add_room'),
    path('room-details/<int:room_id>/', views.room_details_json, name='room_details_json'),
    path('update-room/<int:room_id>/', views.update_room_json, name='update_room_json'),
    path('delete-room/<uuid:uuid>/<int:room_id>/', views.delete_room_json, name='delete_room'),
    path('get-available-rooms/<uuid:uuid>/', views.get_available_rooms_json, name='get_available_rooms'),
    
    path('allocate-room/<uuid:uuid>/', views.allocate_room, name='allocate_room'),
    path('allocations/<uuid:uuid>/', views.allocations_list, name='allocations_list'),
    
    # User Type Based AJAX - Supports Students, Faculty, Staff
    path('get-users-by-department/<uuid:uuid>/', views.get_users_by_department_json, name='get_users_by_department'),
    path('get-user-details/<uuid:uuid>/', views.get_user_details_json, name='get_user_details'),
    path('unallocated-users/<uuid:uuid>/', views.unallocated_users_json, name='unallocated_users'),
    path('allocated-users/<uuid:uuid>/', views.allocated_users_json, name='allocated_users'),
    path('transfer-user/<uuid:uuid>/', views.transfer_user_json, name='transfer_user'),
    
    # Legacy Student AJAX
    path('get-students-by-department/<uuid:uuid>/', views.get_students_by_department_json, name='get_students_by_department'),
    path('get-student-details/<uuid:uuid>/', views.get_student_details_json, name='get_student_details'),
    
    path('hostel-rooms-map/<uuid:uuid>/', views.hostel_rooms_map_json, name='hostel_rooms_map'),
    path('unallocated-students/<uuid:uuid>/', views.unallocated_students_json, name='unallocated_students'),
    path('check-allocation-conflict/<uuid:uuid>/', views.check_allocation_conflict_json, name='check_allocation_conflict'),
    path('bulk-allocate/<uuid:uuid>/', views.bulk_allocate_json, name='bulk_allocate'),
    path('transfer-student/<uuid:uuid>/', views.transfer_student_json, name='transfer_student'),
    path('allocated-students/<uuid:uuid>/', views.allocated_students_json, name='allocated_students'),
    
    path('check-in/<uuid:uuid>/<int:allocation_id>/', views.check_in_json, name='check_in'),
    path('check-out/<uuid:uuid>/<int:allocation_id>/', views.check_out_json, name='check_out'),
    path('bulk-check-in/<uuid:uuid>/', views.bulk_check_in_json, name='bulk_check_in'),
    path('allocation-details/<uuid:uuid>/<int:allocation_id>/', views.allocation_details_json, name='allocation_details'),
    path('allocations-by-room/<uuid:uuid>/', views.get_allocations_by_room_json, name='allocations_by_room'),
    path('update-allocation/<uuid:uuid>/<int:allocation_id>/', views.update_allocation_json, name='update_allocation'),
    path('delete-allocation/<uuid:uuid>/<int:allocation_id>/', views.delete_allocation_json, name='delete_allocation'),
    
    path('housing-dashboard/<uuid:uuid>/', views.admin_housing_dashboard, name='housing_dashboard'),
    # path('housing-applications/<uuid:uuid>/', views.admin_housing_applications, name='housing_applications'),
    # path('housing-application-update/<uuid:uuid>/<int:application_id>/', views.admin_update_application, name='housing_application_update'),
    # path('housing-application-detail/<uuid:uuid>/<int:application_id>/', views.admin_application_detail, name='housing_application_detail'),
    path('maintenance-requests/<uuid:uuid>/', views.admin_maintenance_requests, name='maintenance_requests'),
    path('maintenance-request-update/<uuid:uuid>/<int:request_id>/', views.admin_update_maintenance, name='maintenance_request_update'),
    # path('admin-get-available-rooms/<uuid:uuid>/', views.admin_get_available_rooms_json, name='admin_get_available_rooms'),




    #<-----------------Blaze code End---------------->
    
]