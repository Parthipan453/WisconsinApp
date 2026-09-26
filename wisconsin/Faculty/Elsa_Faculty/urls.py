from django.urls import path
from . import views

urlpatterns = [
path('teaching/course_grade_dashboard/', views.course_grade_dashboard, name='course_grade_dashboard'),    
path('teaching/course_grade/', views.course_grade, name='course_grade'),
path("teaching/course-grade/finalize/", views.finalize_course_grades, name="finalize_course_grades"),
path('teaching/save_course_grade/<int:grade_id>/', views.save_course_grade, name='save_course_grade'),
path('teaching/save_course_grades_bulk/', views.save_course_grades_bulk, name='save_course_grades_bulk'),
path('teaching/update_request/', views.update_request, name='update_request'),
path('teaching/export_grades/', views.export_grades, name='export_grades'),
]