# Research/urls.py

from django.urls import path, include
from . import views

urlpatterns = [
    path("", include('Research.Elsa_research.urls')),

    # ================ Jordan code Start's Here ===============
    path("assign/", include('Research.jordan.urls')),
    # ================ Jordan code End's Here ===============

]