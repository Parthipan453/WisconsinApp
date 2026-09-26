from django.urls import path
from . import views
app_name = "Elsa_research"
urlpatterns = [

    # ====== ADMIN RESEARCH  ========================================================================================================================
    path("hod_research/<uuid:uuid>/", views.hod_research, name="hod_research"),
    path("dean_research/<uuid:uuid>/", views.dean_research, name="dean_research"),
    path("research_committee/",views.research_committee, name="research_committee"),
    path("research_committee/create/", views.committee_create, name="committee_create"),
    path("research_committee/<int:pk>/update/", views.committee_update, name="committee_update"),
    path("research_committee/<int:pk>/deactivate/", views.committee_deactivate, name="committee_deactivate"),
    path("research_committee/<int:pk>/reactivate/", views.committee_reactivate, name="committee_reactivate"),
    path('get-faculty/<int:department_id>/',views.get_faculty_by_department, name='get_faculty_by_department'),






    # ====== FACULTY RESEARCH  ======================================================================================================================
    path("research_opportunity/<uuid:uuid>/", views.research_opportunity, name="research_opportunity"),
    path("post_research_opportunity/<uuid:uuid>/",views.post_research_opportunity,name="post_research_opportunity"),
    path("toggle_opportunity_status/<str:research_id>/", views.toggle_opportunity_status, name="toggle_opportunity_status"),
    path("edit_research_opportunity/<str:research_id>/<uuid>", views.edit_research_opportunity, name="edit_research_opportunity"),
    path( "view-research-opportunity/<str:research_id>/<uuid>",views.view_research_opportunity, name="view_research_opportunity"),
    path("research_funding/<uuid:uuid>/",views.research_funding, name="research_funding"),
    path("research_funding_view/<uuid:uuid>/<str:research_id>/",views.research_funding_view,name="research_funding_view"), 
    path("committee_funding/<uuid:uuid>/",views.committee_funding, name="committee_funding"),
    path("committee_funding_view/<uuid:uuid>/<str:research_id>/",views.committee_funding_view,name="committee_funding_view"), 
    path("research_progress/<uuid:uuid>/", views.research_progress, name="research_progress"),
    path("create_milestone/<uuid:uuid>/<str:research_id>/", views.create_milestone, name="create_milestone"),
    path("student-progress/<uuid:uuid>/<str:research_id>/<int:student_id>/",views.student_progress_detail,name="student_progress_detail"),
    path("review_student_report/<uuid:uuid>/<int:report_id>/", views.review_student_report, name="review_student_report"),
    path("research_presentation/<uuid:uuid>/", views.research_presentation, name="research_presentation"),
    path("create_presentation/<uuid:uuid>/<str:research_id>/", views.create_presentation, name="create_presentation"),
    path("delete_presentation/<uuid:uuid>/<int:presentation_id>/", views.delete_presentation, name="delete_presentation"),
    path("delete_presentation_document/<uuid:uuid>/<int:document_id>/", views.delete_presentation_document, name="delete_presentation_document"),
    path("committee_research_details/<uuid:uuid>/", views.committee_research_details, name="committee_research_details"),
    path("committee_research_details_view/<uuid:uuid>/<str:research_id>/", views.committee_research_details_view, name="committee_research_details_view"),
    path("research_overview/<uuid:uuid>/", views.research_overview, name="research_overview"),

    # ====== STUDENT RESEARCH =======================================================================================================================
    path("student_research_opportunity/<uuid:uuid>/", views.student_research_opportunity, name="student_research_opportunity"),
    path("student_research_opportunity/view_research/<str:research_id>/<uuid:uuid>/",views.view_research,name="view_research"),
    path("student_research_progress/<uuid:uuid>/",views.student_research_progress,name="student_research_progress"),
    path('submit_student_report/<uuid:uuid>/<int:assignment_id>/',views.submit_student_report,name='submit_student_report'),
    path('student_research_opportunity/research_application/<str:research_id>/<uuid:uuid>/', views.view_application, name='research_student_application'),
    path("student-progress-tab/<uuid:uuid>/",views.student_progress_tab,name="student_progress_tab",),
    path('start_milestone_work/<uuid:uuid>/<int:assignment_id>/', views.start_milestone_work, name='start_milestone_work'),


    path('withdraw_application/<int:application_id>/<uuid:uuid>/', views.withdraw_application, name='withdraw_application'),
]