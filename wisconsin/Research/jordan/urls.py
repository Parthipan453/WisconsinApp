# Faculty/urls.py

from django.urls import path
from . import views

app_name = 'faculty'

urlpatterns = [
    # Faculty list page
    path('faculty/', views.faculty_list, name='faculty_list'),
    
    # Faculty detail page - Using UUID
    path('faculty/<uuid:faculty_uuid>/', views.faculty_detail, name='faculty_detail'),
    
    # Assign/Update mentor role - AJAX endpoint
    path('faculty/<uuid:faculty_uuid>/assign-role/', views.assign_mentor_role, name='assign_mentor_role'),
    
    # Get faculty roles - AJAX endpoint
    path('faculty/<uuid:faculty_uuid>/get-roles/', views.get_faculty_roles, name='get_faculty_roles'),
]