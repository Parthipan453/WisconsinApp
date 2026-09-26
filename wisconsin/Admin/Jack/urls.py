from django.urls import path
from . import views

urlpatterns = [
    path('admin_faculty/', views.faculty, name="faculty"),
    path('api/students/list/', views.student_json, name="student_json"),
    path('student_view/<int:id>', views.student_view, name="student_view"),

    ############## SPORTS URLS START ###############
    path('sports/', views.sports, name="sports"),
    path('sport_create/', views.sports_create, name="sport_create"),
    path('api/sports/list/', views.sports_json, name="sports_json"),
    path('sports/edit/<uuid:sport_uuid>',  views.sports_edit, name="sports_edit"),
    path('sports/delete/<uuid:sport_uuid>', views.sports_delete, name="sports_delete"),

    ############## SPORTS URLS END ###############

    ############## TEAM URLS START ###############

    path('teams/', views.teams, name="teams"),
    path('team_create/', views.team_create, name="team_create"),
    path('team_edit/<uuid:team_uuid>', views.team_edit, name="team_edit"),
    path('team_delete/<uuid:team_uuid>', views.team_delete, name="team_delete"),
    path('api/teams/list/', views.team_json, name="team_json"),
    path('team_view/<uuid:team_uuid>', views.team_view, name="team_view"),
    
    ############## TEAM URLS END ###############

    ############## ATHLETIC URLS START ###############

    path('athletics/', views.athletic, name="athletics"),
    path('athletic_create/',  views.athletic_create, name="athletic_create"),
    path('athlete_edit/<uuid:athlete_uuid>', views.athlete_edit, name="athlete_edit"),
    path('api/athletes/list/', views.athlete_json, name="athlete_json"),
    path('athlete_view/<uuid:athlete_uuid>', views.athlete_view, name="athlete_view"),

    ############## ATHLETIC URLS END ###############

    ############## MEDICAL APPOINTMENT URLS START ###############
    
    path("book_appointment/",  views.book_appointment, name="admin_book_appointment"),
    path(
        "get-available-medical-staff/",
        views.get_available_medical_staff,
        name="get_available_medical_staff",
    ),

    ##############MEDICAL APPOINTMENT URLS END ###############
    
    path('medical_reports/', views.medical_reports, name="medical_reports"),
    path('medical_reports/api/<str:report_key>/data/', views.report_data, name='report_data'),

]