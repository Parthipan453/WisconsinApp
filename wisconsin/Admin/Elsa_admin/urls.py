from django.urls import path
from . import views

urlpatterns = [
path('grade_scale/', views.grade_scale, name='gradescale'),
path('grade_scale/add/', views.add_grade_scale, name='add_gradescale'),
path('grade_scale/edit/<int:id>/', views.edit_grade_scale, name='edit_gradescale'),
path("grade_scale/delete/<int:id>/", views.delete_grade_scale, name="delete_gradescale"),
path('score_request/', views.score_request, name='score_request'),
path("score_request/approve/<int:request_id>/", views.approve_request, name="approve_request"),
path("score_request/reject/<int:request_id>/", views.reject_request, name="reject_request"),
]