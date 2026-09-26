from django.urls import path
from . import views

urlpatterns = [
    path("<uuid:staff_uuid>/gradebook/",views.gradebook,name="gradebook",),
]
