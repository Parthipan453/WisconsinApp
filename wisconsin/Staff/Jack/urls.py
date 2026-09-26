from django.urls import path
from . import views

urlpatterns = [
    path("book_appointment/",  views.book_appointment, name="staff_book_appointment"),
    path(
        "get-available-medical-staff/",
        views.get_available_medical_staff,
        name="get_available_medical_staff",
    ),
]