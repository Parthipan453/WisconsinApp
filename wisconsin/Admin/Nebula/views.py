from django.db.models import Q, Count
from django.shortcuts import redirect
from django.contrib import messages
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.utils import timezone
from Faculty.models import FacultyProfile
from Students.models import StudentOrganizationMembership
from Admin.models import User
from Events.models import Event, EventCategory, EventVenue
from .forms import *
from django.core.paginator import Paginator
from Staff.utils import notify_event_invited, notify_event_cancelled, notify_campus_event_published
 
class EventsDashboard(TemplateView):
    template_name = 'eventDashboard/event_dashboard.html'
   
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
 
        events = (
            Event.objects
            .select_related("event_category", "venue", "organizer")
            .order_by("-created_at")
        )
       
        category = self.request.GET.get("category", "").strip()
        status = self.request.GET.get("status", "").strip()
        visibility = self.request.GET.get("visibility", "").strip()
        from_date = self.request.GET.get("from_date", "").strip()
        to_date = self.request.GET.get("to_date", "").strip()
        search_query = self.request.GET.get("search", "").strip()

        if category:
            events = events.filter(event_category__category_name__iexact=category)
        if status:
            events = events.filter(event_status__iexact=status)
        if visibility:
            events = events.filter(event_visibility__iexact=visibility)
        if from_date:
            events = events.filter(start_datetime__date__gte=from_date)
        if to_date:
            events = events.filter(start_datetime__date__lte=to_date)
        if search_query:
            events = events.filter(
                Q(event_title__icontains=search_query) |
                Q(event_code__icontains=search_query) |
                Q(venue__venue_name__icontains=search_query) |
                Q(organizer__first_name__icontains=search_query) |
                Q(organizer__last_name__icontains=search_query) |
                Q(organizer__username__icontains=search_query)
            )

        paginator = Paginator(events, 5)
 
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)
 
        current = page_obj.number
        total = paginator.num_pages
 
        page_numbers = []
 
        # First page
        page_numbers.append(1)
 
        # Left ellipsis
        if current > 3:
            page_numbers.append("...")
 
        # Pages around current page
        start = max(2, current - 1)
        end = min(total - 1, current + 1)
 
        for num in range(start, end + 1):
            page_numbers.append(num)
 
        # Right ellipsis
        if current < total - 2:
            page_numbers.append("...")
 
        # Last page
        if total > 1:
            page_numbers.append(total)

        # Dynamic Stats
        context["total_events"] = Event.objects.count()
        context["published_events"] = Event.objects.filter(event_status="Published").count()
        context["upcoming_events"] = Event.objects.filter(start_datetime__gte=timezone.now()).exclude(event_status="Cancelled").count()
        context["draft_events"] = Event.objects.filter(event_status="Draft").count()
        context["completed_events"] = Event.objects.filter(event_status="Completed").count()
        context["total_categories"] = EventCategory.objects.count()
        context["total_venues"] = EventVenue.objects.count()

        context["categories"] = EventCategory.objects.all().order_by("category_name")
        context["page_obj"] = page_obj
        context["events"] = page_obj.object_list
        context["page_numbers"] = page_numbers
        context["selected_category"] = category
        context["selected_status"] = status
        context["selected_visibility"] = visibility
        context["selected_from_date"] = from_date
        context["selected_to_date"] = to_date
        context["search_query"] = search_query
        context["now"] = timezone.now()

        return context

    def post(self, request, *args, **kwargs):
        event_id = request.POST.get("event_id")
        action = request.POST.get("action")

        if event_id and action:
            try:
                event = Event.objects.get(pk=event_id)
                target_status = None

                if event.event_status == Event.COMPLETED or (event.end_datetime and timezone.now() > event.end_datetime):
                    msg = f'Event "{event.event_title}" is completed and its status cannot be changed.'
                    if request.headers.get("x-requested-with") == "XMLHttpRequest":
                        return JsonResponse({"status": "error", "message": msg}, status=400)
                    messages.error(request, msg)
                    return redirect("events_dashboard")

                if action == "publish" and event.event_status == Event.DRAFT:
                    target_status = Event.PUBLISHED
                elif action == "unpublish" and event.event_status == Event.PUBLISHED:
                    target_status = Event.DRAFT
                elif action == "cancel" and event.event_status == Event.PUBLISHED:
                    target_status = Event.CANCELLED
                elif action == "complete" and event.event_status == Event.PUBLISHED and not event.end_datetime and event.is_past_start:
                    target_status = Event.COMPLETED

                if target_status:
                    event.event_status = target_status
                    event.save()

                    if target_status == Event.CANCELLED:
                        notify_event_cancelled(event)  

                    msg = f'Event "{event.event_title}" status changed to {target_status}.'
                    if request.headers.get("x-requested-with") == "XMLHttpRequest":
                        return JsonResponse({"status": "success", "message": msg, "new_status": target_status})
                    messages.success(request, msg)
                    return redirect("events_dashboard")
                else:
                    msg = "Invalid status transition."
                    if request.headers.get("x-requested-with") == "XMLHttpRequest":
                        return JsonResponse({"status": "error", "message": msg}, status=400)
                    messages.error(request, msg)
                    return redirect("events_dashboard")  

            except Event.DoesNotExist:
                msg = "Event not found."
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({"status": "error", "message": msg}, status=404)
                messages.error(request, msg)
                return redirect("events_dashboard")  

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"status": "error", "message": "Invalid request."}, status=400)

        return redirect("events_dashboard") 

from django.template.loader import render_to_string

class ManageCategories(TemplateView):
    template_name = 'eventDashboard/manage_categories.html'

    def get_filtered_queryset(self):
        categories = (
            EventCategory.objects
            .annotate(event_count=Count("events", distinct=True))
            .order_by("category_name")
        )
        search_query = self.request.GET.get("search", "").strip()
        if search_query:
            categories = categories.filter(
                Q(category_name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        return categories, search_query

    def build_page_numbers(self, page_obj, paginator):
        current = page_obj.number
        total = paginator.num_pages
        page_numbers = [1]
        if current > 3:
            page_numbers.append("...")
        start = max(2, current - 1)
        end = min(total - 1, current + 1)
        for num in range(start, end + 1):
            page_numbers.append(num)
        if current < total - 2:
            page_numbers.append("...")
        if total > 1:
            page_numbers.append(total)
        return page_numbers

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        categories_qs, search_query = self.get_filtered_queryset()

        paginator = Paginator(categories_qs, 5)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["categories"] = page_obj.object_list
        context["page_obj"] = page_obj
        context["page_numbers"] = self.build_page_numbers(page_obj, paginator)
        context["search_query"] = search_query

        context["total_categories"] = EventCategory.objects.count()
        context["categories_in_use"] = (
            EventCategory.objects
            .annotate(event_count=Count("events", distinct=True))
            .filter(event_count__gt=0)
            .count()
        )
        context["total_associated_events"] = Event.objects.filter(
            event_category__isnull=False
        ).count()

        if "category_form" not in context:
            context["category_form"] = EventCategoryForm()

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            html = render_to_string(
                "eventDashboard/partials/_categories_table.html",
                context,
                request=request,
            )
            page_obj = context["page_obj"]
            if page_obj.paginator.count > 0:
                count_text = (
                    f"Showing {page_obj.start_index()}–{page_obj.end_index()} "
                    f"of {page_obj.paginator.count} Categories"
                )
            else:
                count_text = "Showing 0 of 0 Categories"
            return JsonResponse({"html": html, "count_text": count_text})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        category_id = request.POST.get("category_id")
        action = request.POST.get("action")

        if action == "delete" and category_id:
            try:
                category = EventCategory.objects.get(pk=category_id)
                if category.events.exists():
                    messages.error(
                        request,
                        f'Cannot delete "{category.category_name}" — it still has events linked to it.'
                    )
                else:
                    category.delete()
                    messages.success(request, "Category deleted successfully.")
            except EventCategory.DoesNotExist:
                messages.error(request, "Category not found.")
            return redirect("manage_categories")

        if request.POST.get("form_type") == "category":
            if category_id:
                try:
                    instance = EventCategory.objects.get(pk=category_id)
                except EventCategory.DoesNotExist:
                    messages.error(request, "Category not found.")
                    return redirect("manage_categories")
                category_form = EventCategoryForm(request.POST, instance=instance)
            else:
                category_form = EventCategoryForm(request.POST)

            if category_form.is_valid():
                category_form.save()
                messages.success(
                    request,
                    "Category updated successfully." if category_id else "Category added successfully."
                )
                return redirect("manage_categories")

            context = self.get_context_data()
            context["category_form"] = category_form
            context["reopen_category_modal"] = True
            context["edit_category_id"] = category_id
            return self.render_to_response(context)

        return redirect("manage_categories")


class ManageVenues(TemplateView):
    template_name = 'eventDashboard/manage_venues.html'

    def get_filtered_queryset(self):
        venues = (
            EventVenue.objects
            .annotate(event_count=Count("event", distinct=True))
            .order_by("venue_name")
        )
        search_query = self.request.GET.get("search", "").strip()
        if search_query:
            venues = venues.filter(
                Q(venue_name__icontains=search_query) |
                Q(building_name__icontains=search_query) |
                Q(room_number__icontains=search_query)
            )
        return venues, search_query

    def build_page_numbers(self, page_obj, paginator):
        current = page_obj.number
        total = paginator.num_pages
        page_numbers = [1]
        if current > 3:
            page_numbers.append("...")
        start = max(2, current - 1)
        end = min(total - 1, current + 1)
        for num in range(start, end + 1):
            page_numbers.append(num)
        if current < total - 2:
            page_numbers.append("...")
        if total > 1:
            page_numbers.append(total)
        return page_numbers

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        venues_qs, search_query = self.get_filtered_queryset()

        paginator = Paginator(venues_qs, 5)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["venues"] = page_obj.object_list
        context["page_obj"] = page_obj
        context["page_numbers"] = self.build_page_numbers(page_obj, paginator)
        context["search_query"] = search_query

        context["total_venues"] = EventVenue.objects.count()
        context["venues_in_use"] = (
            EventVenue.objects
            .annotate(event_count=Count("event", distinct=True))
            .filter(event_count__gt=0)
            .count()
        )
        context["total_associated_events"] = Event.objects.filter(venue__isnull=False).count()

        if "venue_form" not in context:
            context["venue_form"] = EventVenueForm()

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            html = render_to_string(
                "eventDashboard/partials/_venues_table.html",
                context,
                request=request,
            )
            page_obj = context["page_obj"]
            if page_obj.paginator.count > 0:
                count_text = (
                    f"Showing {page_obj.start_index()}–{page_obj.end_index()} "
                    f"of {page_obj.paginator.count} Venues"
                )
            else:
                count_text = "Showing 0 of 0 Venues"
            return JsonResponse({"html": html, "count_text": count_text})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        venue_id = request.POST.get("venue_id")
        action = request.POST.get("action")

        if action == "delete" and venue_id:
            try:
                venue = EventVenue.objects.get(pk=venue_id)
                if venue.event.exists():
                    messages.error(
                        request,
                        f'Cannot delete "{venue.venue_name}" — it still has events linked to it.'
                    )
                else:
                    venue.delete()
                    messages.success(request, "Venue deleted successfully.")
            except EventVenue.DoesNotExist:
                messages.error(request, "Venue not found.")
            return redirect("manage_venues")

        if request.POST.get("form_type") == "venue":
            if venue_id:
                try:
                    instance = EventVenue.objects.get(pk=venue_id)
                except EventVenue.DoesNotExist:
                    messages.error(request, "Venue not found.")
                    return redirect("manage_venues")
                venue_form = EventVenueForm(request.POST, instance=instance)
            else:
                venue_form = EventVenueForm(request.POST)

            if venue_form.is_valid():
                venue_form.save()
                messages.success(
                    request,
                    "Venue updated successfully." if venue_id else "Venue added successfully."
                )
                return redirect("manage_venues")

            context = self.get_context_data()
            context["venue_form"] = venue_form
            context["reopen_venue_modal"] = True
            context["edit_venue_id"] = venue_id
            return self.render_to_response(context)

        return redirect("manage_venues")
    
class EventCreate(TemplateView):
    template_name = "eventDashboard/event_create.html"
 
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
       
        # Main Event Form
        if "event_form" not in context:
            context["event_form"] = EventCreateForm()
 
        if "category_form" not in context:
            context["category_form"] = EventCategoryForm()
           
        if "venue_form" not in context:
            context["venue_form"] = EventVenueForm()
 
        return context
 
    def post(self, request, *args, **kwargs):
 
        form_type = request.POST.get("form_type")
 
        if form_type == "category":
            return self.handle_category_form(request)
       
        if form_type == "venue":
            return self.handle_venue_form(request)
       
        if form_type == "event":
            return self.handle_event_form(request)
 
        return redirect("event_create")
 
    def handle_category_form(self, request):
 
        category_form = EventCategoryForm(request.POST)
 
        if category_form.is_valid():
 
            category_form.save()
 
            messages.success(
                request,
                "Category added successfully."
            )
 
            return redirect("event_create")
       
        context = self.get_context_data()
 
        context["category_form"] = category_form
        context["reopen_category_modal"] = True
 
        return self.render_to_response(context)
   
    def handle_venue_form(self, request):
 
        venue_form = EventVenueForm(request.POST)
 
        if venue_form.is_valid():
 
            venue_form.save()
 
            messages.success(
                request,
                "Venue added successfully."
            )
 
            return redirect("event_create")
 
        context = self.get_context_data()
 
        context["venue_form"] = venue_form
        context["reopen_venue_modal"] = True
 
        return self.render_to_response(context)
   
    def handle_event_form(self, request):

        event_form = EventCreateForm(request.POST)

        if event_form.is_valid():

            event = event_form.save(commit=False)
        
            event.start_datetime = event_form.cleaned_data["start_datetime"]
            event.end_datetime = event_form.cleaned_data.get("end_datetime")

            event.event_code = Event.generate_event_code()
        
            action = request.POST.get("action")
        
            if action == "publish":
                event.event_status = "Published"
            else:
                event.event_status = "Draft"

            event.save()
            event_form.save_m2m()   

            if event.event_visibility == Event.INVITATION_ONLY:   
                for user in event.invited_users.all():
                    notify_event_invited(event, user)

            elif event.event_visibility == Event.CAMPUS_ONLY and action == "publish":
                notify_campus_event_published(event)

            if action == "publish":
                messages.success(request, "Event published successfully.")
            else:
                messages.success(request, "Event saved as draft.")

            return redirect("events_dashboard")
       
        # else:
        #     print(event_form.errors)
 
        context = self.get_context_data()
 
        context["event_form"] = event_form
 
        return self.render_to_response(context)



from django.shortcuts import get_object_or_404


class EventDetail(TemplateView):
    template_name = "eventDashboard/event_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = get_object_or_404(
            Event.objects.select_related("event_category", "venue", "organizer"),
            pk=kwargs["pk"],
        )
        context["event"] = event
        return context


class EventEdit(TemplateView):
    template_name = "eventDashboard/event_create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        event = get_object_or_404(Event, pk=kwargs["pk"])
        context["event"] = event
        context["is_edit"] = True

        if "event_form" not in context:
            context["event_form"] = EventCreateForm(instance=event)

        if "category_form" not in context:
            context["category_form"] = EventCategoryForm()

        if "venue_form" not in context:
            context["venue_form"] = EventVenueForm()

        return context

    def post(self, request, *args, **kwargs):
        form_type = request.POST.get("form_type")

        if form_type == "category":
            return self.handle_category_form(request)

        if form_type == "venue":
            return self.handle_venue_form(request)

        if form_type == "event":
            return self.handle_event_form(request, kwargs["pk"])

        return redirect("event_edit", pk=kwargs["pk"])

    def handle_category_form(self, request):
        category_form = EventCategoryForm(request.POST)
        if category_form.is_valid():
            category_form.save()
            messages.success(request, "Category added successfully.")
            return redirect("event_edit", pk=request.resolver_match.kwargs["pk"])

        context = self.get_context_data(pk=request.resolver_match.kwargs["pk"])
        context["category_form"] = category_form
        context["reopen_category_modal"] = True
        return self.render_to_response(context)

    def handle_venue_form(self, request):
        venue_form = EventVenueForm(request.POST)
        if venue_form.is_valid():
            venue_form.save()
            messages.success(request, "Venue added successfully.")
            return redirect("event_edit", pk=request.resolver_match.kwargs["pk"])

        context = self.get_context_data(pk=request.resolver_match.kwargs["pk"])
        context["venue_form"] = venue_form
        context["reopen_venue_modal"] = True
        return self.render_to_response(context)

    def handle_event_form(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        
        was_draft = event.event_status == Event.DRAFT

        event_form = EventCreateForm(request.POST, instance=event)

        if event_form.is_valid():
            updated_event = event_form.save(commit=False)
            updated_event.start_datetime = event_form.cleaned_data["start_datetime"]
            updated_event.end_datetime = event_form.cleaned_data.get("end_datetime")
            updated_event.save()

            if (
                was_draft
                and updated_event.event_status == Event.PUBLISHED
                and updated_event.event_visibility == Event.CAMPUS_ONLY
            ):
                notify_campus_event_published(updated_event)

            messages.success(request, "Event updated successfully.")
            return redirect("events_dashboard")

        context = self.get_context_data(pk=pk)
        context["event_form"] = event_form
        context["is_edit"] = True
        return self.render_to_response(context)
        
def get_departments(request):
 
    school_id = request.GET.get("school_id")
 
    departments = Department.objects.filter(
        school_id=school_id
    ).order_by("department_name")
 
    data = [
        {
            "id": dept.department_id,
            "name": dept.department_name,
        }
        for dept in departments
    ]
 
    return JsonResponse(data, safe=False)
   
def get_student_organizations(request):
 
    school_id = request.GET.get("school_id")
 
    organizations = StudentOrganization.objects.filter(
        school_id=school_id
    ).order_by("organization_name")
 
    data = [
        {
            "id": organization.id,
            "name": organization.organization_name,
        }
        for organization in organizations
    ]
 
    return JsonResponse(data, safe=False)
   
def get_department_faculty(request):
 
    department_id = request.GET.get("department_id")
 
    faculty_members = FacultyProfile.objects.filter(
        department_id=department_id,
        employment_status="ACTIVE",
        user__is_faculty=True,
    ).select_related("user")
 
    data = [
        {
            "id": faculty.user.id,
            "name": faculty.user.full_name,
        }
        for faculty in faculty_members
    ]
 
    return JsonResponse(data, safe=False)
 
def get_organization_members(request):
 
    organization_id = request.GET.get("organization_id")
 
    members = (
        StudentOrganizationMembership.objects
        .filter(
            organization_id=organization_id,
            status="ACTIVE",
        )
        .select_related(
            "student__user"
        )
    )
 
    data = [
        {
            "id": member.student.user.id,
            "name": member.student.user.full_name,
        }
        for member in members
    ]
 
    return JsonResponse(data, safe=False)
 
def get_administrators(request):
 
    administrators = User.objects.filter(
        is_admin=True,
        account_status="ACTIVE"
    ).order_by("first_name", "last_name")
 
    data = [
        {
            "id": user.id,
            "name": user.full_name,
        }
        for user in administrators
    ]
 
    return JsonResponse(data, safe=False)

def search_users(request):
    query = request.GET.get("q", "").strip()
    role = request.GET.get("role", "").strip()
    department_id = request.GET.get("department_id", "").strip()

    users = User.objects.filter(is_active=True)

    if role == "student":
        users = users.filter(is_student=True)
    elif role == "staff":
        users = users.filter(is_staff=True)
    elif role == "faculty":
        users = users.filter(is_faculty=True)

    if department_id:
        if role == "faculty":
            users = users.filter(facultyprofile__department_id=department_id)
        else:
            users = users.filter(department_id=department_id) 

    if query:
        users = users.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query)
        )

    users = users.order_by("first_name", "last_name")[:20]

    data = [
        {
            "id": user.id,
            "name": user.full_name,
        }
        for user in users
    ]

    return JsonResponse(data, safe=False)

def get_all_departments(request):
    departments = Department.objects.all().order_by("department_name")

    data = [
        {"id": dept.department_id, "name": dept.department_name}
        for dept in departments
    ]

    return JsonResponse(data, safe=False)


def get_all_schools(request):
    schools = School.objects.all().order_by("school_name")  

    data = [
        {"id": school.school_id, "name": school.school_name} 
        for school in schools
    ]

    return JsonResponse(data, safe=False)