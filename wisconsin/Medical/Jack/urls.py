from django.urls import path
from . import views

urlpatterns = [

    ############## MEDICAL  DEPARTMENT URLS START ###############

    path('department/', views.department, name="medical_department"),
    path('department_create/',  views.department_create, name="department_create"),
    path('api/department/list/', views.department_json, name="department_json"),
    path('department_edit/<uuid:uuid>', views.department_edit,  name="department_edit"),

    ############## MEDICAL DEPARTMENT URLS START ###############

    ############## ATHLETE MEDICAL  PROFILE URLS START ###############

    path('athlete_medical_profile/', views.athlete_medical_profile, name="athlete_medical_profile"),
    path('api/athlete_medical_profile/list/', views.athlete_medical_profile_json, name="athlete_medical_profile_json"),
    path('athlete_medical_profile_view/<uuid:uuid>', views.athlete_medical_profile_view, name="athlete_medical_profile_view"),
    path('athlete_injury_record/<uuid:uuid>',  views.athlete_injury_record, name="athlete_injury_record"),

    ############## ATHLETE MEDICAL  PROFILE URLS END #################

    ############## MEDICAL DASHBOARD URLS START ##############

    # path('patients/', views.patients, name="patients"),

    ######--------------- SWETHA'S URLS START ------------------#######

    path('patients/', views.patients, name="patients" ),
    path('patients/api/',views.patient_list_api,name="patient_list_api"),

    ######--------------- SWETHA'S  URLS END --------------------#######

    path('view_patient/<uuid:uuid>',  views.view_patient, name="view_patient"),

    ############## MEDICAL DASHBOARD URLS END ##############

    path('leave/', views.leave, name="leave"),
    path('apply_leave/',  views.apply_leave, name="apply_leave"),
    path('api/leave_list/',  views.leave_list, name="leave_list"),
    path('cancel_leave/<uuid:leave_id>/', views.cancel_leave, name='cancel_leave'),

    path('profile/', views.profile, name="profile"),

    path('medical/dashboard/<uuid:uuid>/data/', views.medical_dashboard_data, name='medical_dashboard_data'),

    path('leave_request/', views.leave_request, name="leave_request"),
    path("leaves/<int:pk>/status/", views.staff_leave_update_status, name="staff_leave_update_status"),
]