# **************** rupa code *************************************

from django.contrib import admin

from .models import (
    EventCategory,
    EventVenue,
    Event,
    EventRegistration,
    EventSpeaker,
    EventSession,
    EventSponsor,
    EventBudget,
    EventFeedback,
    EventCertificate,
    EventNotification,
)

# Event category

@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_id', 'category_name')
    search_fields = ('category_name',)

# Event Venue

@admin.register(EventVenue)
class EventVenueAdmin(admin.ModelAdmin):
    list_display = (
        'venue_id',
        'venue_name',
        'building_name',
        'room_number',
        'seating_capacity'
    )
    search_fields = (
        'venue_name',
        'building_name',
        'room_number'
    )

# Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'event_code',
        'event_title',
        'event_category',
        'event_status',
        'event_visibility',
        'start_datetime',
        'end_datetime'
    )

    list_filter = (
        'event_status',
        'event_visibility',
        'event_category'
    )

    search_fields = (
        'event_code',
        'event_title'
    )

    ordering = ('-start_datetime',)

# Event Registration

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'registration_id',
        'event',
        'user',
        'attendance_status',
        'registration_date'
    )

    list_filter = (
        'attendance_status',
    )

    search_fields = (
        'user__username',
        'event__event_title'
    )

# Event Speaker

@admin.register(EventSpeaker)
class EventSpeakerAdmin(admin.ModelAdmin):
    list_display = (
        'speaker_name',
        'organization',
        'designation',
        'event'
    )

    search_fields = (
        'speaker_name',
        'organization'
    )

# Event Session

@admin.register(EventSession)
class EventSessionAdmin(admin.ModelAdmin):
    list_display = (
        'session_title',
        'event',
        'speaker',
        'start_time',
        'end_time'
    )

    search_fields = (
        'session_title',
    )


# Event Sponsor

@admin.register(EventSponsor)
class EventSponsorAdmin(admin.ModelAdmin):
    list_display = (
        'sponsor_name',
        'event',
        'sponsorship_type',
        'sponsorship_amount'
    )

    list_filter = (
        'sponsorship_type',
    )

# Event Budget

@admin.register(EventBudget)
class EventBudgetAdmin(admin.ModelAdmin):
    list_display = (
        'event',
        'allocated_budget',
        'actual_expense',
        'remaining_budget'
    )

# Event Feedback

@admin.register(EventFeedback)
class EventFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'event',
        'attendee',
        'rating',
        'submitted_at'
    )

    list_filter = (
        'rating',
    )

# Event Certificate

@admin.register(EventCertificate)
class EventCertificateAdmin(admin.ModelAdmin):
    list_display = (
        'certificate_number',
        'event',
        'participant',
        'issue_date'
    )

    search_fields = (
        'certificate_number',
    )

# Event Notification

@admin.register(EventNotification)
class EventNotificationAdmin(admin.ModelAdmin):
    list_display = (
        'event',
        'notification_type',
        'sent_at'
    )

    list_filter = (
        'notification_type',
    )


# ************************ rupa code ends ******************************