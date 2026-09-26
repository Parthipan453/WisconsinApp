from django.urls import path
from . import views
from .views import *
from Admin.views import *
from General.views import *



urlpatterns = [

    path('departments/', views.department_dashboard, name='department_dashboard'),
    
    path('department/add/', views.department_add, name='department_add'),

  path(
        'departments/<uuid:department_uuid>/edit/',
        views.department_edit,
        name='department_edit'
    ),

    path(
        'departments/<uuid:department_uuid>/inactivate/',
        views.department_inactivate,
        name='department_inactivate'
    ),

    path('courses/',views.course_dashboard, name='course_dashboard'),

     path('course_add',views.course_add,name='course_add'),

    path(
        'courses/<uuid:course_uuid>/edit/',
        views.course_edit,
        name='course_edit'
    ),

    path(
        'courses/<uuid:course_uuid>/inactivate/',
        views.course_inactivate,
        name='course_inactivate'
    ),

     path(
        'courses/<uuid:course_uuid>/',
        views.course_view,
        name='course_view'
    ),


     path('course_add',views.course_add,name='course_add'),

    path(
        'courses/<uuid:course_uuid>/edit/',
        views.course_edit,
        name='course_edit'
    ),

    path(
        'courses/<uuid:course_uuid>/inactivate/',
        views.course_inactivate,
        name='course_inactivate'
    ),

     path(
        'courses/<uuid:course_uuid>/',
        views.course_view,
        name='course_view'
    ),

   path(
    "departments/<uuid:department_uuid>/",
    views.department_view,
    name="department_view",
),
path("course_designation/",views.course_designation,name='course_designation'),
path("course_section/",views.course_section_dashboard,name='course_section'),
path(
    "ajax/department-courses/",
    views.get_department_courses,
    name="department_courses",
),
path(
    "ajax/department-faculty/",
    views.get_department_faculty,
    name="department_faculty",
),
path(
    "course-section/add/",
    views.course_section_add,
    name="course_section_add",
),
path(
    "course-section/view/<int:section_id>/",
    views.course_section_view,
    name="course_section_view",
),

path(
    "course-section/edit/<int:section_id>/",
    views.course_section_edit,
    name="course_section_edit",
),
path(
    "course-section/delete/<int:section_id>/",
    views.course_section_delete,
    name="course_section_delete",
),

path(
    "course-section/export/excel/",
    views.export_course_sections_excel,
    name="course_section_excel",
),

path(
    "course-section/export/pdf/",
    views.export_course_sections_pdf,
    name="course_section_pdf",
),

    path(
        "course-designation-dashboard/",
        views.course_designation_dashboard,
        name="course_designation_dashboard",
    ),

    path(
        "course-designation/export/excel/",
        views.export_designations_excel,
        name="export_designations_excel",
    ),
    path(
        "course-designation/export/pdf/",
        views.export_designations_pdf,
        name="export_designations_pdf",
    ),
    path(
        "designation-type/add/",
        views.designation_type_add,
        name="designation_type_add",
    ),
    path(
        "designation-type/<int:pk>/edit/",
        views.designation_type_edit,
        name="designation_type_edit",
    ),
    path(
        "designation-type/<int:pk>/delete/",
        views.designation_type_delete,
        name="designation_type_delete",
    ),
      path(
        "designation-type/<int:pk>/inactivate/",
        views.designation_type_inactivate,
        name="designation_type_inactivate",
    ),
path("course-requirement-types/", views.course_requirement_type_dashboard, name="course_requirement_type_dashboard"),
path('courses/<uuid:course_uuid>/requirement/add/',     views.course_requirement_add,    name='course_requirement_add'),
path('courses/requirement/<int:requirement_id>/delete/', views.course_requirement_delete, name='course_requirement_delete'),
path('courses/<uuid:course_uuid>/designation/add/',     views.course_designation_add,    name='course_designation_add'),
path('courses/designation/<int:designation_id>/delete/', views.course_designation_delete, name='course_designation_delete'),
path(
    "course/<uuid:course_uuid>/requirement/add/",
    views.course_requirement_add,
    name="course_requirement_add",
),
path(
    "courses/requirement-types/<int:pk>/view/",
    views.course_requirement_type_view,
    name="course_requirement_type_view",
),

#Ranganayagi code start
path(
    "courses/<uuid:course_uuid>/offering/add/",
    views.course_offering_add,
    name="course_offering_add",
),

path(
    "courses/<uuid:course_uuid>/learning-outcome/add/",
    views.course_learning_outcome_add,
    name="course_learning_outcome_add",
),

path(
    "courses/offering/<int:offering_id>/delete/",
    views.course_offering_delete,
    name="course_offering_delete",
),

path(
    "courses/learning-outcome/<int:outcome_id>/delete/",
    views.course_learning_outcome_delete,
    name="course_learning_outcome_delete",
),
path(
    "department/<int:department_id>/programs/",
    views.get_department_programs,
    name="department_programs",
),

#ranganayagi code end
path('courses/requirement-types/', views.course_requirement_type_dashboard, name='course_requirement_type_dashboard'),


path('courses/<uuid:course_uuid>/requirement/add/',     views.course_requirement_add,    name='course_requirement_add'),
path('courses/requirement/<int:requirement_id>/delete/', views.course_requirement_delete, name='course_requirement_delete'),
path('courses/<uuid:course_uuid>/designation/add/',     views.course_designation_add,    name='course_designation_add'),
path('courses/designation/<int:designation_id>/delete/', views.course_designation_delete, name='course_designation_delete'),

path('courses_requirement-types/', views.course_requirement_type_dashboard, name='course_requirement_type_dashboard'),
path('courses/requirement-types/add/', views.course_requirement_type_add, name='course_requirement_type_add'),
path('courses/requirement-types/<int:pk>/edit/', views.course_requirement_type_edit, name='course_requirement_type_edit'),
path('courses/requirement-types/<int:pk>/inactivate/', views.course_requirement_type_inactivate, name='course_requirement_type_inactivate'),
]



