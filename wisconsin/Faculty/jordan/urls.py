from django.urls import path
from . import views

urlpatterns = [
    path('faculty_attendance/<uuid:uuid>', views.own_faculty_attendance, name='own_faculty_attendance'),


    # =============== Research Projects Urls =======================
    path('approval_project/<uuid:uuid>',views.approval_project, name='approval_project_page'),
    path('application_project/<uuid:uuid>',views.application_project, name='application_project_page'),
    path('progress_project/<uuid:uuid>',views.progress_project, name='progress_project_page'),

    # =============== Research Committee member ====================

    path('Research_committee/<uuid:uuid>', views.research_committee, name='research_committee_page'), 


    # ======================= Student Application Review ===========================
    
    path('student_applications/<uuid:uuid>/', 
         views.student_applications, 
         name='research_student_application_page'),
    
    # AJAX Endpoints
    path('api/application/<int:application_id>/', 
         views.get_application_details, 
         name='get_application_details'),
    
    path('api/application/<int:application_id>/update-status/', 
         views.update_application_status, 
         name='update_application_status'),
    
    path('api/application/<int:application_id>/save-review/', 
         views.save_review_comment, 
         name='save_review_comment'),
    
    # Document View Endpoint
    path('api/document/<int:application_id>/<str:doc_type>/', 
         views.view_document, 
         name='view_document'),


     # ===================== Research Team URLS =========================

    path('research_team/<uuid:uuid>/', views.research_team, name='research_team_page'),
    
    # API endpoints
    path('api/projects/', views.get_projects, name='get_projects'),
    path('api/faculty/', views.get_available_faculty, name='get_faculty'),
    path('api/students/', views.get_available_students, name='get_students'),
    path('api/add-member/', views.add_team_member, name='add_member'),
    path('api/remove-member/', views.remove_team_member, name='remove_member'),
    path('api/update-team-name/', views.update_team_name, name='update_team_name'),


    path('research_project_faculty_details/<uuid:uuid>/', views.research_faculty_details, name='research_faculty_details_page'),
    
    # API endpoints for Faculty Details page
    path('api/faculty-projects/', views.get_faculty_projects, name='get_faculty_projects'),
    path('api/project-details-modal/', views.get_project_details_modal, name='get_project_details_modal'),
    
    # API endpoints for Project Status Management
    path('api/update-project-status/', views.update_project_status, name='update_project_status'),
    path('api/project-status-options/', views.get_project_status_options, name='get_project_status_options'),


     # ========================= Research Publication =========================
    # Research Publication page
    path('research_publication_mentor/<uuid:uuid>/', views.research_publication, name='research_publication_mentor_page'),
    
    # API endpoints
    path('api/faculty-research-projects/', views.get_faculty_research_projects, name='get_faculty_research_projects'),
    path('api/project-publication/', views.get_project_publication, name='get_project_publication'),
    path('api/team-members-for-publication/', views.get_team_members_for_publication, name='get_team_members_for_publication'),
    path('api/create-or-update-publication/', views.create_or_update_publication, name='create_or_update_publication'),
    path('api/update-publication-status/', views.update_publication_status, name='update_publication_status'),


    # ========================== Research Submissions ===========================

    # Research Publication page
    path('research_publication_mentor/<uuid:uuid>/', 
         views.research_publication, 
         name='research_publication_mentor_page'),
    
    # Research Submissions page
    path('research_submissions_mentor/<uuid:uuid>/', 
         views.research_submissions_mentor, 
         name='research_submissions_mentor_page'),
    
    # API endpoints for Publications
    path('api/faculty-research-projects/', 
         views.get_faculty_research_projects, 
         name='get_faculty_research_projects'),
    
    path('api/project-publication/', 
         views.get_project_publication, 
         name='get_project_publication'),
    
    path('api/team-members-for-publication/', 
         views.get_team_members_for_publication, 
         name='get_team_members_for_publication'),
    
    path('api/create-or-update-publication/', 
         views.create_or_update_publication, 
         name='create_or_update_publication'),
    
    path('api/update-publication-status/', 
         views.update_publication_status, 
         name='update_publication_status'),
    
    # API endpoints for Submissions
    path('api/faculty-research-projects-with-submissions/', 
         views.get_faculty_research_projects_with_submissions, 
         name='get_faculty_research_projects_with_submissions'),
    
    path('api/project-submission/', 
         views.get_project_submission, 
         name='get_project_submission'),
    
    path('api/create-or-update-submission/', 
         views.create_or_update_submission, 
         name='create_or_update_submission'),
    
    path('api/update-submission-status/', 
         views.update_submission_status, 
         name='update_submission_status'),
]
