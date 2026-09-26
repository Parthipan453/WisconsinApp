import json

# ====== ERIC CODE START ======
from channels.db import database_sync_to_async
# ====== ERIC CODE END ======
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Single WebSocket endpoint (ws/notifications/) handling three kinds of live events:

      - Private:   only the one connected user  (e.g. "your grade change request was approved")
      - Admin:     only staff/admin users        (e.g. "new grade change request submitted")
      - Broadcast: every connected user          (e.g. site-wide announcements)
    """

    async def connect(self):
        self.user = self.scope["user"]

        self.broadcast_group_name = "broadcast"
        await self.channel_layer.group_add(self.broadcast_group_name, self.channel_name)

        self.private_group_name = None
        self.is_admin_group = False

        if self.user and self.user.is_authenticated:
            self.private_group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(self.private_group_name, self.channel_name)

            if getattr(self.user, "is_admin", False) and getattr(self.user, "is_super_admin", False):
                self.is_admin_group = True
                await self.channel_layer.group_add("admins", self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.broadcast_group_name, self.channel_name)
        if self.private_group_name:
            await self.channel_layer.group_discard(self.private_group_name, self.channel_name)
        if self.is_admin_group:
            await self.channel_layer.group_discard("admins", self.channel_name)

    async def receive(self, text_data):
        pass

    async def notify_message(self, event):
        """type: notify.message -> private notification to one user."""
        await self.send(text_data=json.dumps({
            "type": "notification",
            "event": event.get("event", "notification"),
            "data": event["data"],
        }))

    async def admin_message(self, event):
        """type: admin.message -> visible only to staff/admin users."""
        await self.send(text_data=json.dumps({
            "type": "admin_alert",
            "event": event.get("event", "admin_alert"),
            "data": event["data"],
        }))

    async def broadcast_message(self, event):
        """type: broadcast.message -> visible to everyone connected."""
        await self.send(text_data=json.dumps({
            "type": "broadcast",
            "event": event.get("event", "broadcast"),
            "data": event["data"],
        }))


# ====== ERIC CODE START ======

def _app_authorization(app_id, user_id=None, applicant_id=None, is_admin=False):
    """Return True when the given identity may subscribe to one application's group.

    Accepts: the owning applicant (custom Applicant session), the assigned staff
    reviewer, or any admissions admin/staff user. Returns None when unknown so
    the consumer can reject the connection.
    """
    from Applicants.models import Application, ApplicationReviewAssignment

    try:
        app = Application.objects.get(application_id=int(app_id))
    except (Application.DoesNotExist, ValueError, TypeError):
        return None

    if applicant_id and app.applicant_id == int(applicant_id):
        return True
    if user_id:
        if is_admin:
            return True
        if ApplicationReviewAssignment.objects.filter(
            application=app, reviewer_id=user_id
        ).exists():
            return True
    return None


def _is_admin_user(user):
    return bool(
        user and user.is_authenticated
        and (getattr(user, "is_admin", False) or getattr(user, "is_super_admin", False))
    )


class ApplicationConsumer(AsyncWebsocketConsumer):
    """Live page updates for application pages (Applicant / Staff / Admin).

    One socket per page, opened at ws/app-events/<app_id>/.

      * <app_id> == an application pk -> subscribes to that application's
        update group (authorized: owning applicant, assigned reviewer, admin).
      * <app_id> == "me" -> subscribes to the connected user's own channel
        (used by list pages: my reviews, admin queue, applicant hub).

    The socket only carries lightweight event names. Page content is always
    re-read from secured ?partial= endpoints.
    """

    async def connect(self):
        self.user = self.scope.get("user")
        self.session = self.scope.get("session") or {}
        self.app_id = self.scope["url_route"]["kwargs"].get("app_id", "me")

        self.joined_groups = []
        self.identity_user_id = None
        self.is_admin = False

        # Resolve the identity: Django User (staff/admin) wins over the custom
        # Applicant session used by the /applicants/ portal.
        if self.user and self.user.is_authenticated:
            self.identity_user_id = self.user.id
            self.is_admin = _is_admin_user(self.user)
        else:
            applicant_id = self.session.get("applicant_id")
            if not applicant_id:
                await self.close(code=4403)
                return
            self.applicant_id = applicant_id

        if self.app_id != "me":
            ok = await database_sync_to_async(_app_authorization)(
                self.app_id,
                user_id=self.identity_user_id,
                applicant_id=getattr(self, "applicant_id", None),
                is_admin=self.is_admin,
            )
            if not ok:
                await self.close(code=4403)
                return
            await self._join(f"app_{self.app_id}")

        if self.identity_user_id:
            await self._join(f"appuser_{self.identity_user_id}")
            if self.is_admin:
                await self._join("appadmins")
        else:
            await self._join(f"appapplicant_{self.applicant_id}")

        await self.accept()

    async def _join(self, group):
        await self.channel_layer.group_add(group, self.channel_name)
        self.joined_groups.append(group)

    async def disconnect(self, close_code):
        for group in self.joined_groups:
            await self.channel_layer.group_discard(group, self.channel_name)

    async def receive(self, text_data):
        pass

    async def live_event(self, event):
        """type: live.event -> pushed from notify_application() / notify_live_*()."""
        await self.send(text_data=json.dumps({
            "type": "live",
            "event": event.get("event", "update"),
            "app": event.get("app", ""),
            "ts": event.get("ts"),
        }))

# ====== ERIC CODE END ======