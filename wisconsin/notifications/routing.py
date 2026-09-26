from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/notifications/$", consumers.NotificationConsumer.as_asgi()),
    # ====== ERIC CODE START ======
    re_path(
        r"ws/app-events/(?P<app_id>[0-9a-zA-Z\-]+)/$",
        consumers.ApplicationConsumer.as_asgi(),
    ),
    # ====== ERIC CODE END ======
]