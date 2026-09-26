from django.urls import path

from . import views

app_name = "students_eric"

urlpatterns = [
    path(
        "applications/<int:application_id>/create-student/",
        views.create_student,
        name="create_student",
    ),
]
