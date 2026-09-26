# Medical/urls.py
from django.urls import path, include

app_name = "Medical"

urlpatterns = [
    path('', include('Medical.Dominic.urls')),
    path('', include('Medical.Jack.urls')),
    path('', include('Medical.Alan.urls')),
    path('', include('Medical.swetha.urls')),
]