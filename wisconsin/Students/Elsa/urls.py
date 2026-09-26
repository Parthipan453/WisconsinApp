from django.urls import path
from Students.views import *
from . import views


 
app_name = 'Elsa'

urlpatterns = [
 path('attendance_view/<uuid:uuid>/', views.attendance_view, name='attendance'),
 path('export_attendance/', views.export_attendance, name='export_attendance'),
]