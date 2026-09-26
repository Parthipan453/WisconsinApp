from Staff.models import Notification, MessageRecipient

def unread_notifications(request):
    if request.user.is_authenticated:
        unread_notifications_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

        unread_messages_count = MessageRecipient.objects.filter(
            recipient=request.user,
            is_read=False,
            archived=False
        ).count()

        return {
            "unread_notifications_count": unread_notifications_count,
            "unread_messages_count": unread_messages_count,
        }

    return {}