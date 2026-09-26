from django.urls import path
from . import views

urlpatterns = [
    path("appointment_history/",  views.appointment_history, name="appointment_history"),
    path('cancel-appointment/<uuid:uuid>/', views.cancel_appointment, name='cancel_appointment'),

]