from django.urls import path
from . import views

urlpatterns = [
    path('student_research/<uuid:uuid>', views.student_research, name='student_research_page'),
    path('student_application/<uuid:uuid>', views.student_application, name='student_application_page'),

    # Student Research Details page
    path('student_research_details/<uuid:uuid>/', views.student_research_details, name='student_research_details_page'),
    
    # API endpoints for Student
    path('api/projects/', views.get_student_projects, name='get_student_projects'),
    path('api/project-details/', views.get_student_project_details, name='get_student_project_details'),
    path('api/project-status-update/', views.get_project_status_update, name='get_project_status_update'),


    # Student Research Publication page
    path('student_research_publication/<uuid:uuid>/', views.student_research_publication, name='student_research_publication_page'),
    
    # API endpoints for Student Publications
    path('api/student-publications/', views.get_student_publications, name='get_student_publications'),
    path('api/student-publication-detail/', views.get_student_publication_detail, name='get_student_publication_detail'),


    # Research submission details 
    path('student_research_submission/<uuid:uuid>/', 
         views.student_research_submission, 
         name='student_research_submission_page'),
    
    # API endpoints for student submissions
    path('api/student-research-projects-with-submissions/', 
         views.get_student_research_projects_with_submissions, 
         name='get_student_research_projects_with_submissions'),
    
    path('api/student-project-submission/', 
         views.get_student_project_submission, 
         name='get_student_project_submission'),


    path("student_research_application_details/<uuid:uuid>/",views.student_research_application_details,name="student_research_application_details_page")
]