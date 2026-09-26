
from datetime import date, timedelta, datetime
import calendar
from itertools import groupby

from django.db.models import Q
from django.utils import timezone
from django.views.generic import TemplateView, DetailView
from django.core.paginator import Paginator

from django.http import Http404, JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Event, EventCategory

# Gayathri G
class Events(TemplateView):
    template_name = "Events/events.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)
        
        calendar_year = int(
            self.request.GET.get("year", today.year)
        )
        
        calendar_month = int(
            self.request.GET.get("month", today.month)
        )
        
        cal = calendar.Calendar(firstweekday=6)
        
        month_days = cal.monthdatescalendar(
            calendar_year,
            calendar_month,
        )
        
        if calendar_month == 1:
            prev_month = 12
            prev_year = calendar_year - 1
        else:
            prev_month = calendar_month - 1
            prev_year = calendar_year

        if calendar_month == 12:
            next_month = 1
            next_year = calendar_year + 1
        else:
            next_month = calendar_month + 1
            next_year = calendar_year

        selected_date = self.request.GET.get("date")
        search = self.request.GET.get("search", "").strip()
        category = self.request.GET.get("category")
        
        selected_date_obj = None

        if selected_date:
            selected_date_obj = datetime.strptime(
                selected_date,
                "%Y-%m-%d"
            ).date()

        events = (
            Event.objects.filter(event_status__in=["Published", "Completed", "Cancelled"])
            .exclude(event_visibility=Event.INVITATION_ONLY)
            .select_related(
                "event_category",
                "venue",
                "organizer",
                "school",
                "department",
                "student_organization",
            )
            .order_by("start_datetime")
        )

        if not self.request.user.is_authenticated:
            events = events.exclude(event_visibility=Event.CAMPUS_ONLY)

        if selected_date:
            events = events.filter(
                start_datetime__date=selected_date
            )
        else:
            events = events.filter(
                # gte => greater than or equal to 
                start_datetime__date__gte=today
            )

        if search:
            events = events.filter(
                Q(event_title__icontains=search)
                | Q(event_subtitle__icontains=search)
                | Q(event_description__icontains=search)
            )

        if category:
            events = events.filter(event_category_id=category)

        paginator = Paginator(events, 5)   

        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        events = page_obj.object_list

        grouped_events = []

        for date, event_list in groupby(
            events,
            key=lambda event: event.start_datetime.date(),
        ):
            grouped_events.append(
                {
                    "date": date,
                    "events": list(event_list),
                }
            )
            

        # ---------------------------------------
        # Context
        # ---------------------------------------
        context["page_obj"] = page_obj
        context["total_events"] = paginator.count
        
        context["calendar_days"] = month_days
        context["calendar_month"] = calendar_month
        context["calendar_year"] = calendar_year
        context["calendar_month_name"] = calendar.month_name[
            calendar_month
        ]
        context["prev_month"] = prev_month
        context["prev_year"] = prev_year

        context["next_month"] = next_month
        context["next_year"] = next_year
                
        context["grouped_events"] = grouped_events
        context["categories"] = EventCategory.objects.order_by("category_name")

        context["today"] = today
        context["tomorrow"] = tomorrow
        context["selected_date"] = selected_date
        context["selected_date_obj"] = selected_date_obj
        context["calendar_date"] = selected_date or today.isoformat()  
        context["selected_category"] = category or ""
        context["search"] = search

        return context
    
class EventDetail(DetailView):
    model = Event
    template_name = "Events/event_detail.html"

    context_object_name = "event"

    queryset = (
        Event.objects
        .select_related(
            "event_category",
            "venue",
            "organizer",
            "school",
            "department",
            "student_organization",
        )
    )

    def get_object(self, queryset=None):
        event = super().get_object(queryset)
        user = self.request.user

        if event.event_visibility == Event.INVITATION_ONLY:
            is_invited = user.is_authenticated and event.invited_users.filter(pk=user.pk).exists()
            is_organizer = user.is_authenticated and event.organizer_id == user.pk

            if not (is_invited or is_organizer):
                raise Http404("Event not found.")

        elif event.event_visibility == Event.CAMPUS_ONLY:
            if not user.is_authenticated:
                raise Http404("Event not found.")

        return event

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        event = self.object

        context["show_contact"] = (
            bool(event.contact_email)
            or bool(event.contact_phone)
        )

        context["show_accessibility"] = (
            event.has_accessibility_information
            and (
                bool(event.accessibility_email)
                or bool(event.accessibility_phone)
            )
        )

        context["show_cost"] = (
            event.is_paid_event
            and bool(event.event_cost)
        )

        return context


@login_required
def event_detail_ajax(request, event_id):
    try:
        event = Event.objects.select_related('venue', 'organizer', 'event_category').get(event_id=event_id)
    except Event.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Event not found'}, status=404)

    if event.venue:
        venue_display = f"{event.venue.venue_name} - {event.venue.room_number}, {event.venue.building_name}"
        location_details = event.venue.location_details or "—"
    else:
        venue_display = "—"
        location_details = "—"

    organizer_name = event.organizer.get_full_name() if event.organizer else "—"

    return JsonResponse({
        'success': True,
        'event_title': event.event_title,
        'event_subtitle': event.event_subtitle,
        'category_name': event.event_category.category_name if event.event_category else '',
        'event_description': event.event_description,
        'event_mode': event.event_mode,
        'venue_display': venue_display,
        'location_details': location_details,
        'organizer_name': organizer_name,
        'contact_email': event.contact_email,
        'start_datetime_display': event.start_datetime.strftime('%A, %B %d, %Y @ %I:%M %p'),
        'end_datetime_display': (
            event.end_datetime.strftime('%A, %B %d, %Y @ %I:%M %p')
            if event.end_datetime else None
        ),
    })