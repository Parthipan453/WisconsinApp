# Admin/templatetags/announcement_tags.py
from django import template
from Admin.Dominic.models import Announcement

register = template.Library()


@register.inclusion_tag('Dominic/announcements/announcement_widget.html')
def show_announcements(channel):
    if channel not in ('website', 'dashboard'):
        channel = 'website'
    announcements = Announcement.visible_queryset(channel)
    return {'announcements': announcements, 'channel': channel}