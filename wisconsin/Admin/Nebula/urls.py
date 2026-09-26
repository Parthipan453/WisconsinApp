from django.urls import path
from .views import *

urlpatterns = [
    path('events/', EventsDashboard.as_view(), name='events_dashboard'),
    path('events/create', EventCreate.as_view(), name='event_create'),
    path('events/<int:pk>/', EventDetail.as_view(), name='event_detail'),
    path('events/<int:pk>/edit/', EventEdit.as_view(), name='event_edit'),
    path('events/categories/', ManageCategories.as_view(), name='manage_categories'),
    path('events/venues/', ManageVenues.as_view(), name='manage_venues'),
    path("ajax/departments/", get_departments, name="get_departments"),
    path("ajax/student-organizations/", get_student_organizations, name="get_student_organizations",),
    path("ajax/department-faculty/", get_department_faculty, name="department_faculty"),
    path("ajax/organization-members/", get_organization_members, name="organization_members"),
    path("ajax/administrators/", get_administrators, name="administrators"),
    path("ajax/all-departments/", get_all_departments, name="get_all_departments"),
    path("ajax/all-schools/", get_all_schools, name="get_all_schools"),
]