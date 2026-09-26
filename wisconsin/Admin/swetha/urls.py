from django.urls import path
from . import views

urlpatterns=[
    
    ########################## swetha's code start ############################
    
    path("user_reports/", views.user_reports, name="user_reports"),
    path("export/users/excel/",views.export_users_excel,name="export_users_excel"),
    path("export/users/pdf/",views.export_users_pdf,name="export_users_pdf"),

    path("login_reports",views.login_reports, name="login_reports"),
    path("login-reports/json/",views.login_reports_json,name="login_reports_json"),
    path("recent-sessions/json/",views.recent_sessions_json, name="recent_sessions_json"),
    path("reports/login/export/excel/",views.export_login_excel, name="export_login_excel"),
    path("reports/login/export/pdf/",views.export_login_pdf, name="export_login_pdf"),

    path("facility",views.facility,name="facility"),
    path("facility/add/",views.add_facility,name="add_facility"),
    path("facility/save/", views.facility_save, name="facility_save"),
    path("facility/update/", views.facility_update, name="facility_update"),
    path("facility/status/",views.facility_status,name="facility_status"),

    path("club/", views.club, name="club"),path("club/save/",views.club_save,name="club_save"),
    path("club_view/<int:pk>/", views.club_view, name="club_view"),
    path("club_update/<int:id>/",views.club_update,name="club_update"),
    
    path("profile_setting/",views.profile_setting,name="profile_setting"),
    
    path("Coach/",views.coach_management,name="coach_management"),
    path("coaches/assign/", views.assign_coach, name="assign_coach"),
    path("coaches/<int:coach_id>/",views.coach_view,name="coach_view",),
    path("coach/<int:coach_id>/edit/", views.edit_coach, name="edit_coach"),

    path("patients/", views.patient_profile, name="patient_profile"),
    path("patient-profile/list/", views.patient_profile_list, name="patient_profile_list"),
    path("patient-profile/<int:patient_id>/",views.patient_profile_view,name="patient_profile_view",),

    path("appointments/",views.appointment,name="appointment_overview",),

    path("healthcamp/", views.healthcamp_management,name="healthcamp_management",),
    
    path("admin/medical-history/",views.admin_medical_history,name="admin_medical_history"),
    path("admin/medical-history/cancel/<uuid:uuid>/",views.admin_cancel_appointment,name="admin_cancel_appointment"),

    ################################ swetha's code end ##########################
]