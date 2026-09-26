import json

from channels.generic.websocket import AsyncWebsocketConsumer

TOURNAMENT_DASHBOARD_GROUP = "tournament_dashboard"


class TournamentDashboardConsumer(AsyncWebsocketConsumer):
    """Pushes invitation status-change events to the Admin Tournament Dashboard."""

    async def connect(self):
        user = self.scope.get("user")

        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        
        self.group_name = TOURNAMENT_DASHBOARD_GROUP
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if getattr(self, "group_name", None):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
       
        pass

    async def invitation_status_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "invitation_status_update",
            "invitation": event["invitation"],
        }))

    async def participant_added(self, event):
        await self.send(text_data=json.dumps({
            "type": "participant_added",
            "participant": event["participant"],
        }))