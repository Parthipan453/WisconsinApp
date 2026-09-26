from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from Admin.consumers import TOURNAMENT_DASHBOARD_GROUP


def broadcast_invitation_status(invitation):
    """
    Push one invitation's current status to every connected Admin
    Tournament Dashboard.

    IMPORTANT: only ever call this via transaction.on_commit(...), never
    directly inside a `with transaction.atomic():` block — otherwise the
    socket event can reach the browser before the row is actually committed.
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return  # no channel layer configured; no-op instead of crashing

    payload = {
        "invitation_uuid": str(invitation.invitation_uuid),
        "tournament": invitation.tournament.tournament_name if invitation.tournament else "—",
        "college_name": invitation.college_name or "—",
        "department_name": invitation.department_name or "—",
        "contact_person": invitation.contact_person or "—",
        "email": invitation.email,
        "application_status": invitation.application_status,
        "invitation_sent_at": (
            invitation.invitation_sent_at.date().isoformat()
            if invitation.invitation_sent_at else None
        ),
    }

    async_to_sync(channel_layer.group_send)(
        TOURNAMENT_DASHBOARD_GROUP,
        {"type": "invitation_status_update", "invitation": payload},
    )

def broadcast_participant_added(participant):
    """
    Push a newly-approved participant to every connected Admin Tournament
    Dashboard. Same rule as above: only call this via transaction.on_commit(...).
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    tournament = participant.tournament
    application = getattr(participant.invitation, "application", None) if participant.invitation_id else None
    players_list = application.players if (application and application.players) else []

    payload = {
        "invitation_uuid": str(participant.invitation.invitation_uuid) if participant.invitation_id else None,
        "participant_name": participant.participant_name,
        "team_name": participant.team_name or "—",
        "tournament": tournament.tournament_name if tournament else "—",
        "tournament_type": tournament.tournament_type if tournament else None,
        "participation_type": tournament.participation_type if tournament else None,
        "college_name": participant.college_name or "—",
        "internal_team": (
            getattr(participant.internal_team, "team_name", str(participant.internal_team))
            if participant.internal_team else "—"
        ),
        "internal_athlete": "—",
        "coach_name": participant.coach_name or "—",
        "players_count": participant.players_count,
        "players": players_list,
        "final_position": participant.final_position,
        "result": participant.result,
        "registered_at": (
            participant.registered_at.date().isoformat() if participant.registered_at else None
        ),
    }

    async_to_sync(channel_layer.group_send)(
        TOURNAMENT_DASHBOARD_GROUP,
        {"type": "participant_added", "participant": payload},
    )
