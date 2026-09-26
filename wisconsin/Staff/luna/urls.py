from django.urls import path
from . import views
urlpatterns=[
    path('staff-appointments/',views.staff_medical_history,name='staff_medical_history'),
    path('appointments/<uuid:uuid>/cancel/',views.staff_cancel_appointment,name='staff_cancel_appointment'),
]