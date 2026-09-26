from django.urls import path

from . import views

urlpatterns = [
    path("applications/", views.applications, name="applications"),
    path(
        "applications/<int:application_id>/",
        views.application_detail,
        name="application_detail",
    ),
    path(
        "applications/<int:application_id>/assign/",
        views.assign_reviewer,
        name="assign_reviewer",
    ),
    path(
        "applications/<int:application_id>/decide/",
        views.decide,
        name="decide",
    ),
    path(
        "applications/<int:application_id>/promote/",
        views.promote_from_waitlist,
        name="promote_from_waitlist",
    ),
    path(
        "applications/<int:application_id>/update-program/",
        views.update_program,
        name="update_program",
    ),
    path(
        "applications/<int:application_id>/create-student/",
        views.create_student,
        name="create_student",
    ),
]
