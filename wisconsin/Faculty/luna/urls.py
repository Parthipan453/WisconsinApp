from django.urls import path
from . import views

urlpatterns = [

    path(
        "appointment-history/",
        views.faculty_appointment_history,
        name="faculty_appointment_history"
    ),

    path(
        "appointment/<uuid:uuid>/cancel/",
        views.faculty_cancel_appointment,
        name="faculty_cancel_appointment"
    ),
]