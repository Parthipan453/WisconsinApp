from django.urls import path
from . import views




urlpatterns = [
    path(
        "patients/add/", views.add_patient,
        name="add_patient"
    ),
    path(
        "patients/save/", views.save_patient,
        name="save_patient"
    ),
    path(
        "patients/ajax/search-members/", views.search_patient_members,
         name="search_patient_members"
    ),

    #---------------- Jack Views End ------------------#

    path("edit_patient/<uuid:uuid>", views.edit_patient, name="edit_patient"),
    path("patients/update/<uuid:uuid>", views.update_patient, name="update_patient"),

    #---------------- Jack Views End ------------------#
    path("patients/add/", views.add_patient,name="add_patient"),
    path("patients/save/", views.save_patient,name="save_patient"),
    path("patients/ajax/search-members/", views.search_patient_members, name="search_patient_members"),
    
    path(
        "appointments/",
        views.today_schedule,
        name="today_schedule",
    ),

    path(
        "patient/<int:patient_id>/details/",
        views.patient_details,
        name="patient_details",
    ),

   path(
    "Register-patient/<int:registration_id>/check-in/",
    views.check_in_patient,
    name="check_in_patient",
    ),
    path(
        "patient-status/<int:registration_id>/complete/",
        views.complete_patient_consultation,
        name="complete_patient_consultation",
    ),

    path(
        "patient-status/<int:registration_id>/status/",
        views.update_registration_status,
        name="update_registration_status",
    ),

    path(
         "athlete/injury/create/",
        views.create_athlete_injury,
        name="create_athlete_injury",
    ),
    path(
        "athlete/medical-care/update/",
        views.update_athlete_medical_care,
        name="update_athlete_medical_care",
    ),

    path(
    "patient-registration/ambulances/",
    views.patient_registration_ambulances,
    name="patient_registration_ambulances"
    ),
    path(
        "ambulance/available/",
        views.available_ambulances,
        name="available_ambulances"
    ),

    path(
    "patient-registration/ambulance/update-status/",
    views.update_ambulance_status,
    name="update_ambulance_status"
),
    path(
    "ambulance/availability/",
    views.ambulance_availability,
    name="ambulance_availability",
),



    path('attendance', views.attendance, name='attendance'),
    path( "attendance/data/",views.get_attendance_data,name="attendance_data",),
    path('api/check-in/', views.check_in, name='check_in'),
    path("logout/", views.logout_view, name="medical_logout"),
    path('attendance/export/', views.export_attendance, name='export_attendance'),
  

    
    path("patients/register/", views.patient_registration_page, name="patient_registration"),
    path("patients/add/", views.add_patient, name="add_patient"),
    path("patients/register/search-patient/", views.patient_search, name="patient_search"),
    path("patients/register/search-schedule/", views.schedule_search, name="schedule_search"),
    path("patients/register/save/", views.register_patient, name="register_patient"),
    path("patients/register/queue/", views.queue_list, name="queue_list"),
      path("patients/register/doctor-schedule-calendar/", views.doctor_schedule_calendar, name='doctor_schedule_calendar'),

    path("appointments/frontdesk/",views.appointment_list_frontdesk,name="appointment_list_frontdesk",),
    path("appointments/frontdesk/status/",views.appointment_status_frontdesk,name="appointment_status_frontdesk",),

    path('patient-history/', views.patient_history, name='patient_history'),
    # path('patient-history/<uuid:patient_uuid>/', views.patient_history, name='patient_history_detail'),
    path("patient-history/<int:patient_id>/",views.patient_medical_history,name="patient_medical_history",),

    #################### kali code ###########################
    path("patients/rooms/", views.rooms_page, name="rooms"),
    path("patients/patient-status/<int:registration_id>/admit-request/", views.admit_patient_request, name="admit_patient_request"),
    path("patients/rooms/", views.rooms_page, name="rooms_page"),
    path("patients/rooms/admission-requests/", views.admission_requests_list, name="admission_requests_list"),
    path("patients/rooms/admit/", views.admit_patient_to_room, name="admit_patient_to_room"),
    path("rooms/room/<int:room_id>/occupant/", views.room_occupant_details, name="room_occupant_details"),
    path("rooms/room/<int:registration_id>/checkup/save/",views.save_room_checkup,name="save_room_checkup",),

    #################### kali code end ########################
  

]