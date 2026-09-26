from django.urls import path
from .views import *

# Gayathri G
urlpatterns = [
    path('', Events.as_view(), name='events' ),
    path("event-detail/<int:pk>/", EventDetail.as_view(), name="event-detail"),
    path('ajax/<int:event_id>/detail/', event_detail_ajax, name='event_detail_ajax'),
]