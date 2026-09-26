from django.urls import path
from . import views

urlpatterns = [
    path('student_attendance_record/<uuid:uuid>/', views.student_attendance_record, name='student_attendance_record'),
    path('api/course-attendance/<int:course_id>/', views.get_course_attendance, name='get_course_attendance'),
    path('api/update-attendance/', views.update_attendance, name='update_attendance'),
]