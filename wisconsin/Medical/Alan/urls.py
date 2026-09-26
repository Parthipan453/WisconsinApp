from django.urls import path
from . import views

urlpatterns = [
    path("hospital_dashboard/", views.hospital_dashboard, name="hospital_dashboard"),
    path("create_hospital/", views.create_hospital, name="create_hospital"),
    path("hospital/<uuid:uuid>/detail/", views.hospital_detail, name="hospital_detail"),
    path("own_hospital/<uuid:hospital_uuid>/", views.own_hospital, name="own_hospital"),
    path("facilities/add/", views.add_facility, name="add_facility"),
    path("add_hospital/", views.add_hospital, name="add_hospital"),
    path(
        "hospital/<uuid:hospital_uuid>/maintenance/add/",
        views.add_facility_maintenance,
        name="add_facility_maintenance",
    ),
    path(
        "maintenance/<int:maintenance_id>/",
        views.maintenance_detail,
        name="maintenance_detail",
    ),
    path(
        "maintenance/<int:maintenance_id>/complete/",
        views.complete_maintenance,
        name="complete_maintenance",
    ),
    path(
        "hospital/<uuid:hospital_uuid>/gallery/add/",
        views.add_hospital_gallery,
        name="add_hospital_gallery",
    ),
    path(
        "gallery/<int:gallery_id>/delete/",
        views.delete_hospital_gallery,
        name="delete_hospital_gallery",
    ),
    path(
        "facility/<int:facility_id>/maintenance-details/",
        views.facility_maintenance_details,
        name="facility_maintenance_details",
    ),
    path(
        "hospital/<uuid:hospital_uuid>/facility/allocate/",
        views.allocate_facility_room,
        name="allocate_facility_room",
    ),
    
    path(
        "hospital/<uuid:hospital_uuid>/working-hours/save/",
        views.save_working_hours,
        name="save_working_hours"
    ),
    path(
            "hospital/<uuid:hospital_uuid>/room-allocation/",
            views.room_alloation,
            name="room_allocation"
        ),
    
    path(
        "room-purpose/save/<uuid:hospital_uuid>/",
        views.save_room_purpose,
        name="save_room_purpose"
    ),
    
    path(
        "room-purpose/empty/<uuid:hospital_uuid>/",
        views.empty_room_purpose,
        name="empty_room_purpose"
    ),
    path(
        "ambulance_services/<uuid:hospital_uuid>/",
        views.ambulance_services,
        name="ambulance_services"
    ),
]
