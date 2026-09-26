from django.urls import path,include
from . import views

# app_name = 'Staff' 

urlpatterns = [


    # Dashboard  →  /staff/<uuid>/
    path('<uuid:uuid>/', views.staff_dashboard, name='staff_dashboard'),
    path('<uuid:uuid>/staff-security/', views.staff_account_security, name='staff_account_security'),

    # Administration
    path('<uuid:uuid>/work-overview/', views.staff_work_overview, name='staff_work_overview'),
    path('<uuid:uuid>/requests/', views.staff_requests, name='staff_requests'),
    path('<uuid:uuid>/financial-aid/<int:aid_id>/', views.staff_financial_aid_detail, name='staff_financial_aid_detail'),
    
    path('<uuid:uuid>/financial-aid/approve/<int:aid_id>/', views.staff_financial_aid_approve, name='staff_financial_aid_approve'),
    
    path('<uuid:uuid>/financial-aid/reject/<int:aid_id>/', views.staff_financial_aid_reject, name='staff_financial_aid_reject'),
    
    path('<uuid:uuid>/financial-aid/under-review/<int:aid_id>/', views.staff_financial_aid_under_review, name='staff_financial_aid_under_review'),
    path('<uuid:uuid>/forms/', views.staff_forms, name='staff_forms'),
    path('<uuid:uuid>/communications/', views.staff_communications, name='staff_communications'),
    


    #<---------------------Blaze Code start(24.07.26)---------------------->
    path('student-records/<uuid:uuid>/', views.staff_student_records, name='staff_student_records'),
    path('api/student-detail/<int:student_id>/', views.get_student_detail, name='get_student_detail'),
    path('student-edit/<int:student_id>/', views.edit_student, name='edit_student'),
    path('api/update-student-status/', views.update_student_status, name='update_student_status'),
    path('api/student-statistics/', views.get_student_statistics, name='get_student_statistics'),
    path('api/search-students/', views.search_students, name='search_students'),
    path('api/export-students/', views.export_students, name='export_students'),
    

    path('<uuid:uuid>/enrollment/', views.staff_enrollment, name='staff_enrollment'),
    path('api/enrollment-detail/<int:enrollment_id>/', views.get_enrollment_detail, name='get_enrollment_detail'),
    path('api/update-enrollment/', views.update_enrollment, name='update_enrollment'),
    path('<uuid:uuid>/enrollment/new/', views.new_enrollment, name='new_enrollment'),
    path('api/create-enrollment/', views.create_enrollment, name='create_enrollment'),
    path('api/get-course-sections/',views.get_course_sections,name='get_course_sections',
    
),
    #speed code starts########################################################
    path('api/get-student-academic-profile/', views.get_student_academic_profile, name='get_student_academic_profile'),
    path('api/bulk-eligible-students/', views.get_bulk_eligible_students, name='get_bulk_eligible_students'),
    path('api/bulk-enroll/', views.bulk_enroll_students, name='bulk_enroll_students'),
     path('<uuid:uuid>/enrollment/bulk/', views.bulk_enrollment, name='bulk_enrollment'),
      path('api/remove-section-student/', views.remove_section_student, name='remove_section_student'),
       path('api/enrollments/', views.get_enrollment_list, name='get_enrollment_list'),
       path('<uuid:uuid>/enrollment/student/<int:enrollment_id>/', views.staff_enrollment_student_view, name='staff_enrollment_student_view'),
        path('<uuid:uuid>/course-allocation/', views.course_allocation, name='course_allocation'),
     path('api/course-allocations/', views.get_course_allocations, name='get_course_allocations'),
     path('api/save-course-allocations/', views.save_course_allocations, name='save_course_allocations'),
     path('api/delete-course-allocation/', views.delete_course_allocation, name='delete_course_allocation'),
     path('<uuid:uuid>/enrollment/department/<int:department_id>/', views.staff_department_enrollment, name='staff_department_enrollment'),
    path('<uuid:uuid>/enrollment/program/<int:program_id>/bulk/', views.staff_program_bulk_enrollment, name='staff_program_bulk_enrollment'),
    path('<uuid:uuid>/enrollment/program/<int:program_id>/bulk/sections/', views.staff_program_bulk_enrollment_sections, name='staff_program_bulk_enrollment_sections'),
    path('<uuid:uuid>/enrollment/program/<int:program_id>/bulk/students/', views.staff_program_bulk_enrollment_students, name='staff_program_bulk_enrollment_students'),
    path('<uuid:uuid>/enrollment/program/<int:program_id>/bulk/review/', views.staff_program_bulk_enrollment_review, name='staff_program_bulk_enrollment_review'),
    path('<uuid:uuid>/enrollment/students/', views.staff_view_students, name='staff_view_students'),
      path('<uuid:uuid>/enrollment/student/<int:enrollment_id>/edit/', views.staff_enrollment_student_edit, name='staff_enrollment_student_edit'),
    #speed code ends#####################################################################



    path('api/get-students-list/', views.get_students_list, name='get_students_list'),
    path('api/bulk-create-financial-aid/', views.bulk_create_financial_aid, name='bulk_create_financial_aid'),


    path('<uuid:uuid>/financial-aid/', views.staff_financial_aid, name='staff_financial_aid'),
    path('api/financial-aid-detail/<int:aid_id>/', views.get_financial_aid_detail, name='get_financial_aid_detail'),
    path('api/update-financial-aid/', views.update_financial_aid, name='update_financial_aid'),
    path('api/create-financial-aid/', views.create_financial_aid, name='create_financial_aid'),

    #<-----------------------Blaze Start bulk uplaod(28.07.26)---------------------------->

    path('staff/api/bulk-create-financial-aid/', views.bulk_create_financial_aid, name='bulk_create_financial_aid'),
    path('<uuid:uuid>/financial-aid-reports/', views.financial_aid_reports, name='staff_financial_aid_reports'),


    #<-----------------------Blaze End bulk uplaod(28.07.26)----------------------------->


    path('<uuid:uuid>/advising/', views.staff_advising, name='staff_advising'),


    path('<uuid:uuid>/directory/', views.staff_directory, name='staff_directory'),
    path('<uuid:uuid>/course-support/', views.staff_course_support, name='staff_course_support'),
    path('<uuid:uuid>/course-support/<uuid:course_uuid>/', views.staff_course_view, name='staff_course_view'),
    path('<uuid:uuid>/scheduling/', views.staff_scheduling, name='staff_scheduling'),
    path('<uuid:uuid>/exams/', views.staff_exams, name='staff_exams'),


    path('<uuid:uuid>/reports/', views.staff_reports, name='staff_reports'),
    path('<uuid:uuid>/knowledge/', views.staff_knowledge, name='staff_knowledge'),
  
    # blaze code start----------------------------------------------------------------------------------->(09.07.26)
    path('settings/<uuid:uuid>/staff-profile/', views.staff_profile_settings, name='staff_profile_settings'),
    
    path('settings/<uuid:uuid>/staff-profile/update-ajax/', views.update_staff_profile_ajax, name='update_staff_profile_ajax'),
    
    path('settings/<uuid:uuid>/staff-profile/change-password-ajax/', views.change_password_ajax, name='change_password_ajax'),

    #blaze code end--------------------------------------------------------------------------------------->(09.07.26)
    
    # AJAX Endpoints
#     path('settings/<uuid:uuid>/staff-profile/update-ajax/', views.update_profile_ajax, name='update_profile_ajax'),
    path('settings/<uuid:uuid>/staff-profile/change-password-ajax/', views.change_password_ajax, name='change_password_ajax'),
    path('settings/<uuid:uuid>/staff-profile/2fa/setup-ajax/', views.setup_2fa_ajax, name='setup_2fa_ajax'),
    path('settings/<uuid:uuid>/staff-profile/2fa/verify-ajax/', views.verify_2fa_ajax, name='verify_2fa_ajax'),
    path('settings/<uuid:uuid>/staff-profile/2fa/disable-ajax/', views.disable_2fa_ajax, name='disable_2fa_ajax'),
    path('settings/<uuid:uuid>/staff-profile/2fa/backup-codes-ajax/', views.get_backup_codes_ajax, name='backup_codes_ajax'),
    path('settings/<uuid:uuid>/staff-profile/sessions/revoke-ajax/', views.revoke_session_ajax, name='revoke_session_ajax'),
    path('settings/<uuid:uuid>/staff-profile/sessions/revoke-all-ajax/', views.revoke_all_sessions_ajax, name='revoke_all_sessions_ajax'),
    path('settings/<uuid:uuid>/staff-profile/deactivate-ajax/', views.deactivate_account_ajax, name='deactivate_account_ajax'),
    path('settings/<uuid:uuid>/staff-profile/delete-account-ajax/', views.delete_account_ajax, name='delete_account_ajax'),

    
    #blaze code start----------------------------------------------------------------------------------->
     path('settings/<uuid:uuid>/account-security/', views.staff_account_security, name='staff_account_security'),

     path('api/staff/<uuid:uuid>/update-account/',  views.update_account_settings,  name='update_account_settings'),

    # ************************************************ Arun Code ********************************************************


    path('<uuid:uuid>/course-support/materials/', views.course_materials_list, name='course_materials_list'),
    path('<uuid:uuid>/course-support/materials/upload/', views.upload_course_material, name='upload_course_material'),
    path('<uuid:uuid>/course-support/tickets/', views.support_tickets_list, name='support_tickets_list'),
    path('<uuid:uuid>/course-support/tickets/<int:ticket_id>/detail/', views.staff_ticket_detail, name='staff_ticket_detail'),
    path('<uuid:uuid>/course-support/tickets/<int:ticket_id>/resolve/', views.resolve_ticket, name='resolve_ticket'),
    path('<uuid:uuid>/course-support/tickets/<int:ticket_id>/in-progress/', views.mark_ticket_in_progress, name="mark_ticket_in_progress"),

    path("<uuid:uuid>/scheduling/new/", views.new_schedule, name="new_schedule"),
    #########   Rixie code start  ##########
    path("api/buildings/", views.get_buildings, name="get_buildings"),
    path("api/rooms-for-building/", views.get_rooms_for_building, name="get_rooms_for_building"),
     #########   Rixie code end  ##########
    path("api/schedule/sections-for-course/", views.get_sections_for_course, name="get_sections_for_course"),
    path("api/schedule/create/", views.create_schedule, name="create_schedule"),
    path("api/schedule/check-section-instructor-conflict/", views.check_section_instructor_conflict, name="check_section_instructor_conflict"),
    path("api/schedule/<int:schedule_id>/detail/", views.get_schedule_detail, name="get_schedule_detail"),
    path("api/schedule/update/", views.update_schedule, name="update_schedule"),
    path("api/schedule/<int:section_id>/resolve/", views.resolve_schedule_conflict, name="resolve_schedule_conflict"),

    path('<uuid:uuid>/scheduling/view/', views.schedule_view, name='staff_scheduling_view'),

    path('<uuid:uuid>/course-support/materials/<int:material_id>/delete/', views.delete_course_material, name='delete_course_material'),
    path('<uuid:uuid>/course-support/materials/<int:material_id>/edit/', views.edit_course_material, name='edit_course_material'),

    path('<uuid:uuid>/exams/', views.staff_exams, name='staff_exams'),
    path('<uuid:uuid>/exams/new/', views.new_exam, name='new_exam'),
    path("api/exams/create/", views.create_exam, name="create_exam"),
    path("api/exams/<int:exam_id>/detail/", views.exam_detail, name="exam_detail"),
    path('api/exams/enrolled-students/', views.get_course_enrolled_students, name='get_course_enrolled_students'),
    path("api/exams/update/",views.update_exam,name="update_exam"),
    path("api/exams/<int:exam_id>/delete/",views.delete_exam,name="delete_exam"),
    path("api/exams/allocate-room/", views.allocate_exam_room, name="allocate_exam_room"),
    path("api/exams/assign-invigilator/",views.assign_invigilator,name="assign_invigilator",),
    path("api/exams/reassign-invigilator/", views.reassign_invigilator, name="reassign_invigilator"),
    path('staff/<uuid:uuid>/exams/export/excel/', views.export_exams_excel, name='export_exams_excel'),
    path('staff/<uuid:uuid>/exams/export/pdf/', views.export_exams_pdf, name='export_exams_pdf'),

    path("api/exams/schedule/", views.schedule_exam, name="schedule_exam"),

    path('staff/<uuid:uuid>/reports/students/excel/', views.export_student_records_excel, name='export_student_records_excel'),
    path('staff/<uuid:uuid>/reports/students/pdf/', views.export_student_records_pdf, name='export_student_records_pdf'),
    path('staff/<uuid:uuid>/reports/financial-aid/excel/', views.export_financial_aid_excel, name='export_financial_aid_excel'),
    path('staff/<uuid:uuid>/reports/financial-aid/pdf/', views.export_financial_aid_pdf, name='export_financial_aid_pdf'),
    path('staff/<uuid:uuid>/reports/research/excel/', views.export_research_excel, name='export_research_excel'),
    path('staff/<uuid:uuid>/reports/research/pdf/', views.export_research_pdf, name='export_research_pdf'),

    path('staff/<uuid:uuid>/downloads/', views.staff_downloads, name='staff_downloads'),
    path('staff/<uuid:uuid>/downloads/upload/', views.upload_resource, name='upload_resource'),
    path('staff/<uuid:uuid>/downloads/<int:resource_id>/download/', views.download_resource, name='download_resource'),
    path('staff/<uuid:uuid>/downloads/<int:resource_id>/detail/', views.resource_detail_ajax, name='resource_detail_ajax'),
    path('staff/<uuid:uuid>/downloads/<int:resource_id>/delete/', views.delete_resource, name='delete_resource'),
    path('staff/<uuid:uuid>/forms/<int:resource_id>/update/', views.update_form_resource, name='update_form_resource'),
    path('<uuid:uuid>/downloads/mark-alerts-seen/', views.mark_resource_alerts_seen_ajax, name='mark_resource_alerts_seen'),
    
    path('staff/<uuid:uuid>/notifications/', views.staff_notifications, name='staff_notifications'),
    path('staff/<uuid:uuid>/notifications/page/', views.staff_notifications_page_ajax, name='staff_notifications_page_ajax'),
    path('staff/<uuid:uuid>/notifications/recent/', views.recent_notifications_ajax, name='recent_notifications_ajax'),
    path('staff/<uuid:uuid>/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('staff/<uuid:uuid>/notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),

    path("communications/search-recipients/", views.search_message_recipients, name="search_message_recipients"),
    path("communications/send/", views.send_message_ajax, name="send_message_ajax"),
    path("<uuid:uuid>/communications/thread/<int:thread_id>/", views.thread_detail_ajax,name="thread_detail_ajax"),
    path("communications/reply/", views.reply_message_ajax, name="reply_message_ajax"),
    path("<uuid:uuid>/communications/thread/<int:thread_id>/archive/", views.archive_thread_ajax, name="archive_thread_ajax"),
    path("<uuid:uuid>/communications/volume/", views.message_volume_ajax, name="message_volume_ajax"),
    path( "<uuid:uuid>/communications/thread/<int:thread_id>/unarchive/", views.unarchive_thread_ajax, name="unarchive_thread_ajax"),
    path("<uuid:uuid>/communications/unread/", views.unread_messages_ajax, name="unread_messages_ajax"),

    path('<uuid:uuid>/organizations/', views.staff_org_dashboard, name='staff_org_dashboard'),
    path('<uuid:uuid>/organizations/<int:org_id>/detail/', views.staff_org_detail_ajax, name='staff_org_detail_ajax'),
    path('<uuid:uuid>/organizations/<int:org_id>/update/', views.staff_org_update_ajax, name='staff_org_update_ajax'),
    path('<uuid:uuid>/organizations/<int:org_id>/delete/', views.staff_org_delete_ajax, name='staff_org_delete_ajax'),
    path('<uuid:uuid>/organizations/requests/<int:membership_id>/approve/', views.staff_org_approve_ajax, name='staff_org_approve_ajax'),
    path('<uuid:uuid>/organizations/requests/<int:membership_id>/reject/', views.staff_org_reject_ajax, name='staff_org_reject_ajax'),
    path('<uuid:uuid>/organizations/<int:org_id>/members/', views.staff_org_members_ajax, name='staff_org_members_ajax'),
    path('<uuid:uuid>/organizations/search-students/', views.staff_search_students_ajax, name='staff_search_students_ajax'),
    path('<uuid:uuid>/organizations/<int:org_id>/members/add/', views.staff_add_member_ajax, name='staff_add_member_ajax'),
    path('<uuid:uuid>/organizations/members/<int:membership_id>/remove/', views.staff_remove_member_ajax, name='staff_remove_member_ajax'),
    path('<uuid:uuid>/organizations/advisors-by-department/', views.staff_advisors_by_department_ajax, name='staff_advisors_by_department_ajax'),
    path("<uuid:uuid>/organizations/departments-by-school/", views.staff_departments_by_school_ajax, name="staff_departments_by_school_ajax"),
    
    # ************************************************ Arun Code ********************************************************
    
    #<-----------------------BLAZE CODE START STAFF LEAVE REQUEST(28.07.26)---------------------------->
     
    path('leave-dashboard/<uuid:uuid>/', views.staff_leave_dashboard, name='staff_leave_dashboard'),
    path('leave-submit/<uuid:uuid>/', views.submit_staff_leave, name='submit_staff_leave'),
    path('leave-cancel/<uuid:uuid>/<int:leave_id>/', views.cancel_staff_leave, name='cancel_staff_leave'),
    path('leave-details/<uuid:uuid>/<int:leave_id>/', views.get_staff_leave_details, name='get_staff_leave_details'),
    path('leave-update/<uuid:uuid>/<int:leave_id>/', views.update_staff_leave, name='update_staff_leave'),
    path('leave-balance/<uuid:uuid>/', views.get_staff_leave_balance, name='get_staff_leave_balance'),
    path('leave-export/<uuid:uuid>/', views.export_staff_leave_report, name='export_staff_leave_report'),


    path('housing/<uuid:uuid>/', views.staff_housing_view, name='staff_housing'),
    path('get-available-rooms/<uuid:uuid>/', views.staff_get_available_rooms_json, name='staff_get_available_rooms'),
    path('maintenance-request-submit/<uuid:uuid>/', views.staff_maintenance_request_submit, name='staff_maintenance_request_submit'),



    #<-----------------------BLAZE CODE END STAFF LEAVE REQUEST(28.07.26)---------------------------->


     
    #____ Eric code_____
    path('', include('Staff.Eric.urls')),
    #____Eric code end____
    path('', include('Staff.Jordan.urls')),

    #**********luna code start *********
    path('', include('Staff.luna.urls')),
    
    #*********Eric code end ************

    #### Leo's Code Update Start - 31/08/2026 ####
   
    path("", include("Staff.Leo_Staff.urls")),

    #### Leo's Code Update End - 31/08/2026 ####

   # ********************* Rixie code start ******************** #

  path(
    "<uuid:uuid>/course-section/",
    views.course_section_dashboard,
    name="staff_course_section",
),

  path(
    "<uuid:uuid>/course-section/add/",
    views.course_section_add,
    name="staff_course_section_add",
),

path(
    "<uuid:uuid>/course-section/view/<int:section_id>/",
    views.course_section_view,
    name="staff_course_section_view",
),

path(
    "<uuid:uuid>/course-section/edit/<int:section_id>/",
    views.course_section_edit,
    name="staff_course_section_edit",
),

path(
    "<uuid:uuid>/course-section/deactivate/<int:section_id>/",
    views.course_section_deactivate,
    name="staff_course_section_deactivate",
),

path(
    "<uuid:uuid>/course-section/export/excel/",
    views.export_course_sections_excel,
    name="staff_course_section_excel",
),

path(
    "<uuid:uuid>/course-section/export/pdf/",
    views.export_course_sections_pdf,
    name="staff_course_section_pdf",
),

path(
    "ajax/department-courses/",
    views.get_department_courses,
    name="staff_department_courses",
),

path(
    "ajax/department-faculty/",
    views.get_department_faculty,
    name="staff_department_faculty",
),

path(
    "api/programs/",
    views.get_programs_by_department,
    name="staff_get_programs",
),

path(
    "api/courses/",
    views.get_courses_by_program,
    name="staff_get_courses",
),

path(
    "<uuid:uuid>/course-section/check-section-number/",
    views.check_section_number_unique,
    name="staff_check_section_number",
),

path(
    "<uuid:uuid>/course-section/check-instructor/",
    views.check_instructor_unique,
    name="staff_check_instructor",
),


path(
    "schedule/<uuid:uuid>/<int:course_id>/edit/",
    views.schedule_edit,
    name="staff_schedule_edit",
),

path(
    "view-timetable/<uuid:uuid>/",
    views.view_timetable,
    name="view_timetable"
),

path(
    "faculty-availability/<uuid:uuid>/",
    views.faculty_availability,
    name="faculty_availability"
),

path(
    "room-management/<uuid:uuid>/",
    views.room_management,
    name="room_management"
),
 # ********************* Rixie code end ******************** #

# Jack urls Start

path("", include("Staff.Jack.urls")),
    
# Jack urls End
 # ********************* bela code start ******************** 

 path(
    '<uuid:uuid>/advising-support/department/<int:department_id>/',
    views.staff_advising_department,
    name='staff_advising_department'
),
path(
    '<uuid:uuid>/advising-support/department/<int:department_id>/program/<int:program_id>/',
    views.staff_advising_program,
    name='staff_advising_program'
),
path(
    '<uuid:uuid>/advising-support/assign-advisor/',
    views.staff_assign_advisor,
    name='staff_assign_advisor'
),

path(
    '<uuid:uuid>/advising-support/department/<int:department_id>/program/<int:program_id>/batch/<int:batch_year>/',
    views.staff_advising_batch,
    name='staff_advising_batch'
),


 # ********************* bela code end ******************** 
#<---------------------Blaze Code start--------------------->

path('<uuid:uuid>/faculty-leave/<int:leave_id>/', views.staff_faculty_leave_detail, name='staff_faculty_leave_detail'),

path('<uuid:uuid>/student-leave-detail/<int:leave_id>/', views.staff_student_leave_detail, name='staff_student_leave_detail'),

#<---------------------Blaze Code end----------------------->


# ===================================Elsa Code Start===================================================
path("", include("Staff.Elsa_staff.urls")),
# ===================================Elsa Code End===================================================
# *********************** Rupa code start ********************************************
path("library/", include("Staff.library.urls")),

# *********************** Rupa code end **********************************************
    
]