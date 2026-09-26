#####################  steve code start ######################################
from django.urls import path
from . import views
from .views import *
from General.views import *

urlpatterns = [
    
    path('universities/', views.university_list, name="university_list"),
    path('universities/add/', views.add_university, name="add_university"),
    path('universities/edit/<uuid:university_id>/', views.edit_university, name='edit_university'),
    path('universities/toggle-status/<uuid:university_id>/', views.toggle_university_status, name='toggle_university_status'),
    path('university-detail/<uuid:university_id>/', views.university_detail, name='university_detail'),
    path('schools/', views.school_list, name='school_list'),
    path('schools/add/', views.add_school, name='add_school'),
    path('schools/edit/<uuid:school_id>/', views.edit_school, name='edit_school'),  
    path('schools/toggle-status/<uuid:school_id>/', views.toggle_school_status, name='toggle_school_status'),  
    path('school/<uuid:school_id>/', views.school_detail, name='school_detail'),
    path('degrees/', views.degree_list, name="degree_list"),
    path('degrees/add/', views.add_degree, name="add_degree"),
    path('degrees/edit/<int:id>/', views.edit_degree, name="edit_degree"),
    path('degree/<int:id>/toggle-status/', views.toggle_degree_status, name="toggle_degree_status"),
    path('programs/', views.program_list, name="program_list"),
    path('programs/add/', views.add_program, name="add_program"),
    path('programs/edit/<int:id>/', views.edit_program, name="edit_program"),
    path('programs/toggle-status/<int:id>/',  views.toggle_program_status, name="toggle_program_status"),
    path('program/<int:program_id>/', views.program_detail, name='program_detail'),
    path('program-curriculum/', views.program_course_list, name="program_course_list"),
    path('program-curriculum/add/', views.add_program_course, name="add_program_course"),
    path('program-curriculum/<int:pk>/edit/', views.edit_program_course, name="edit_program_course"),
    path('program-curriculum/toggle-status/<int:program_course_id>/', views.toggle_program_course_status, name="toggle_program_course_status"),
    path('ajax/program/<int:program_id>/courses/',  views.get_program_courses, name="get_program_courses"),
    #####################  steve code end ######################################


    
    #################  Rixie code start ###############
    path(
    "area-of-interest/add/",
    views.add_area_of_interest,
    name="add_area_of_interest",
),
    path(
    "area-of-interest/delete/",
    views.delete_area_of_interest,
    name="delete_area_of_interest",
),
   #################  Rixie code end ###############
    path('academic-terms/', views.academic_term_list, name="academic_term_list"),
    path('academic-terms/add/', views.academic_term_create, name="academic_term_create"),
    path('academic-terms/<int:pk>/edit/', views.academic_term_update, name="academic_term_update"),
    path('academic-term/<int:pk>/toggle-status/', views.toggle_academic_term_status, name="toggle_academic_term_status"),

]

