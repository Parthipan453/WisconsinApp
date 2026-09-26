import os,re
from notifications.utils import send_notification, broadcast_update
from Staff.models import Notification
from Research.models import *
from Students.models import StudentProfile
from .forms import *
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from urllib.parse import urlparse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Sum, Count
from decimal import Decimal, InvalidOperation
from django.views.decorators.cache import never_cache
from django.db.models import Avg


# ====== ADMIN RESEARCH  ========================================================================================================================
def _filtered_queryset(request):
    qs = ResearchCommittee.objects.select_related('faculty', 'faculty__faculty_rank', 'department').all()
    status = request.GET.get('status', '')
    dept_id = request.GET.get('department', '')
    role = request.GET.get('role', '')
    query = request.GET.get('q', '')
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)
    if dept_id:
        qs = qs.filter(department_id=dept_id)
    if role:
        qs = qs.filter(role=role)
    if query:
        qs = qs.filter(
            Q(faculty__name__icontains=query) |
            Q(department__department_name__icontains=query)|
            Q(role__icontains=query)
        )
    return qs, status, dept_id, role, query


def _build_context(request, role_form=None, add_form=None, show_add_modal=False,
                    open_edit_id=None, edit_form_override=None):
    qs, status, dept_id, role, query = _filtered_queryset(request)
    paginator = Paginator(qs, 12)

    page_number = request.GET.get("page")
    members_page = paginator.get_page(page_number)    

    edit_forms = {m.id: ResearchCommitteeForm(instance=m) for m in qs}
    if edit_form_override is not None and open_edit_id is not None:
        edit_forms[open_edit_id] = edit_form_override

    return {
        'members': members_page,
        'page_obj': members_page,
        'departments': Department.objects.all().order_by('department_name'),
        'roles': ResearchCommittee.COMMITTEE_ROLES,
        'selected_department': dept_id,
        'selected_status': status,
        'selected_role': role,
        'search_query': query,
        'stat_total': qs.count(),
        'stat_active': qs.filter(is_active=True).count(),
        'stat_inactive': qs.filter(is_active=False).count(),
        'stat_roles': qs.values('role').distinct().count(),
        'stat_departments': qs.values('department').distinct().count(),
        'stat_chairpersons': qs.filter(role='chair',is_active=True).count(),
        'add_form': add_form or ResearchCommitteeForm(),
        'show_add_modal': show_add_modal,
        'edit_forms': edit_forms,
        'open_edit_id': open_edit_id,
    }

@login_required
def research_committee(request):
    add_form = None
    show_add_modal = False

    if request.session.pop('rc_add_form_reopen', False):
        posted_data = request.session.pop('rc_add_form_data', None)
        if posted_data:
            add_form = ResearchCommitteeForm(posted_data)
            add_form.is_valid()  # populate .errors, don't save
            show_add_modal = True

    context = _build_context(request, add_form=add_form, show_add_modal=show_add_modal)
    return render(request, "admin_research/research_committee.html", context)

@login_required
def committee_create(request):
    if request.method != 'POST':
        return redirect('Elsa_research:research_committee')
    form = ResearchCommitteeForm(request.POST)
    if form.is_valid():
        committee_member = form.save()
        messages.success(request, 'Committee member added successfully.')

        faculty_user = committee_member.faculty.user
        profile_link = reverse('faculty_myprofile', kwargs={'uuid': faculty_user.uuid})
        message = (
            f"You have been appointed as {committee_member.get_role_display()} on the Research Committee."
        )
        Notification.objects.create(
            user=faculty_user,
            title="Research Committee Appointment",
            message=message,
            notification_type="SUCCESS",
            link=profile_link,
        )
        send_notification(faculty_user.id, {
            "title": "Research Committee Appointment",
            "message": message,
        }, event="grade_request_decided")

        return redirect('Elsa_research:research_committee')
    messages.error(request, 'Please fix the errors below.')
    request.session['rc_add_form_data'] = request.POST.dict()
    request.session['rc_add_form_reopen'] = True
    return redirect('Elsa_research:research_committee')


@login_required
def committee_update(request, pk):
    member = get_object_or_404(ResearchCommittee, pk=pk)
    old_role_display = member.get_role_display()
    if request.method != "POST":
        return redirect('Elsa_research:research_committee')
    form = ResearchCommitteeForm(request.POST, instance=member)
    form.data = form.data.copy()
    form.data['department'] = member.department_id
    form.data['faculty'] = member.faculty_id
    if form.is_valid():
        if (
            form.cleaned_data['role'] == "CHAIRPERSON"
            and ResearchCommittee.objects.filter(
                department=member.department,
                role="CHAIRPERSON",
                is_active=True
            ).exclude(pk=member.pk).exists()
        ):
            return JsonResponse({
                "success": False,
                "errors": {
                    "role": [
                        "This department already has a Chairperson."
                    ]
                }
            })
 
        updated_member = form.save()
        messages.success(request, "Committee member updated successfully.")
 
        if updated_member.get_role_display() != old_role_display:
            faculty_user = updated_member.faculty.user
            profile_link = reverse('faculty_myprofile', kwargs={'uuid': faculty_user.uuid})
            message = (
                f"Your role on the Research Committee has been updated to {updated_member.get_role_display()}."
            )
 
            Notification.objects.create(
                user=faculty_user,
                title="Research Committee Role Updated",
                message=message,
                notification_type="SUCCESS",
                link=profile_link,
            )
 
            send_notification(faculty_user.id, {
                "title": "Research Committee Role Updated",
                "message": message,
            }, event="grade_request_decided")
 
        return JsonResponse({
            "success": True
        })
    return JsonResponse({
        "success": False,
        "errors": {
            field: list(errors)
            for field, errors in form.errors.items()
        }
    })

@login_required
def committee_deactivate(request, pk):
    if request.method == 'POST':
        member = get_object_or_404(ResearchCommittee, pk=pk)
        member.is_active = False
        member.ended_at = timezone.now().date()
        member.save()
        messages.success(request, f'{member.faculty} marked inactive.')
    return redirect('Elsa_research:research_committee')

@login_required
def committee_reactivate(request, pk):
    if request.method == 'POST':
        member = get_object_or_404(ResearchCommittee, pk=pk)
        member.is_active = True
        member.ended_at = None
        member.save()
        messages.success(request, f'{member.faculty} reactivated.')
    return redirect('Elsa_research:research_committee')

def get_faculty_by_department(request, department_id):
    assigned = ResearchCommittee.objects.values_list(
        'faculty_id',
        flat=True
    )
    faculties = FacultyProfile.objects.filter(
        department_id=department_id
    ).exclude(
        id__in=assigned
    ).order_by(
        'user__first_name'
    )
    data = [
        {
            "id": faculty.id,
            "name": faculty.user.get_full_name()
        }
        for faculty in faculties
    ]
    return JsonResponse({
        "faculties": data
    })


# ====== FACULTY RESEARCH  ======================================================================================================================
def _get_team_recipients(research, exclude_user=None):
    """Active co-mentors/advisors on the research team (excluding exclude_user)."""
    recipients = {}
    team = ResearchTeam.objects.filter(research_details=research).first()
    if team:
        members = team.member.filter(
            role__in=["ADVISOR", "CO_MENTOR"],
            faculty__isnull=False,
        ).select_related("faculty__user")
        for member in members:
            u = member.faculty.user
            if exclude_user and u.id == exclude_user.id:
                continue
            recipients[u.id] = u
    return recipients


def _get_committee_recipients(research, exclude_user=None):
    """Active research committee members (excluding exclude_user)."""
    recipients = {}
    members = ResearchCommittee.objects.filter(
        is_active=True
    ).select_related("faculty__user")
    for member in members:
        u = member.faculty.user
        if exclude_user and u.id == exclude_user.id:
            continue
        recipients[u.id] = u
    return recipients

@login_required
def hod_research(request, uuid):
    context = {
        "uuid": uuid,
    }
    return render(request, "hod_research.html", context)

@login_required
def dean_research(request, uuid):
    context = {
        "uuid": uuid,
    }
    return render(request, "dean_research.html", context)

@login_required
def research_opportunity(request, uuid):
    faculty = FacultyProfile.objects.get(
        user=request.user
    )
    if not faculty.is_mentor:
        messages.error(
            request,
            "You do not have permission to access Research Funding."
        )
        return redirect(
            "faculty_dashboard",
            uuid=uuid
        )    
    selected_status = request.GET.get("status", "ALL")
    opportunity_list = ResearchOpportunity.objects.filter(faculty=request.user.faculty_profile).order_by("-created_at")
    total_count = opportunity_list.count()
    open_count = opportunity_list.filter(status="OPEN").count()
    draft_count = opportunity_list.filter(status="DRAFT").count()
    ongoing_count = opportunity_list.filter(status="ONGOING").count()
    closed_count = opportunity_list.filter(status="CLOSED").count()
    completed_count = opportunity_list.filter(status="COMPLETED").count()
    if selected_status != "ALL":
        opportunity_list = opportunity_list.filter(status=selected_status)
    paginator = Paginator(opportunity_list, 10)
    page = request.GET.get("op_page", 1)
    opportunities = paginator.get_page(page)
    context = {
        "uuid": uuid,
        "opportunities": opportunities,
        "selected_status": selected_status,
        "total_count": total_count,
        "open_count": open_count,
        "draft_count": draft_count,
        "ongoing_count": ongoing_count,
        "closed_count": closed_count,
        "completed_count": completed_count,
    }
    return render(
        request,
        "faculty_research/research_opportunity.html",
        context,
    )

@require_POST
def toggle_opportunity_status(request, research_id):
    try:
        opportunity = ResearchOpportunity.objects.get(research_id=research_id)
        if opportunity.status == "OPEN":
            opportunity.status = "CLOSED"
        else:
            opportunity.status = "OPEN"
        opportunity.save()
        return JsonResponse({
            "success": True,
            "status": opportunity.status
        })
    except ResearchOpportunity.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Research Opportunity not found."
        }, status=404)

@login_required
def post_research_opportunity(request, uuid):
    faculty = FacultyProfile.objects.get(user=request.user)
    department = faculty.department
    if request.method == "POST":
        errors = {}
        action = request.POST.get("action")
        status = "OPEN" if action == "publish" else "DRAFT"
        title = request.POST.get("title","").strip()
        category = request.POST.get("category","").strip()
        short_description = request.POST.get("short_description","").strip()
        description = request.POST.get("description","").strip()
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        available_slots = request.POST.get("available_slots")
        estimated_amount = request.POST.get("estimated_amount", "").strip()        
        required_skills = request.POST.get("required_skills","").strip()
        application_open_date = request.POST.get("application_open_date")
        application_deadline = request.POST.get("application_deadline")
        reference_link = request.POST.get("reference_link","").strip()
        additional_notes = request.POST.get("additional_notes","").strip()
        files = request.FILES.getlist("supporting_documents")
        # ---------- Title ----------
        if not title:
            errors["title"] = "Research title is required."
        elif len(title) < 10:
            errors["title"] = "Minimum 10 characters."
        elif len(title) > 255:
            errors["title"] = "Maximum 255 characters."
        # Must start with a letter
        elif not re.match(r"^[A-Za-z]", title):
            errors["title"] = "Title must start with an alphabet."
        # Must contain at least one alphabet
        elif not re.search(r"[A-Za-z]", title):
            errors["title"] = "Title must contain at least one alphabet."
        # Allow only letters, numbers, spaces, (), _, -, &
        elif not re.fullmatch(r"[A-Za-z][A-Za-z0-9\s()_\-&]*", title):
            errors["title"] = (
                "Only letters, numbers, spaces, (), _, -, and & are allowed."
            )

        # ---------- Category ----------
        if not category:
            errors["category"] = "Category is required."
        elif len(category) < 3 or len(category) > 100:
            errors["category"] = "Category must be 3-100 characters."
        elif not re.fullmatch(r"[A-Za-z][A-Za-z0-9\s()_\-&]*", category):
            errors["category"] = (
                "Category must start with an alphabet and can contain only "
                "letters, numbers, spaces, (), _, -, and &."
            )

        # ---------- Descriptions ----------
        if len(short_description)<30 or len(short_description)>250:
            errors["short_description"]="Short description must be 30-250 characters."

        if len(description)<100 or len(description)>3000:
            errors["description"]="Detailed description must be 100-3000 characters."

        # ---------- Slots ----------
        if not available_slots:
            errors["available_slots"] = "Available slots is required."
        else:
            try:
                slots = int(available_slots)
                if slots < 1 or slots > 10:
                    errors["available_slots"] = "Slots must be between 1 and 10."
            except ValueError:
                errors["available_slots"] = "Enter a valid number."

        # ---------- Skills ----------
        if not required_skills:
            errors["required_skills"] = "Required skills is mandatory."
        elif len(required_skills) < 5:
            errors["required_skills"] = "Minimum 5 characters."
        elif len(required_skills) > 500:
            errors["required_skills"] = "Maximum 500 characters."
        # ---------- Amount ----------
        if not estimated_amount:
            errors["estimated_amount"] = "Funding estimated amount is required."
        else:
            try:
                estimated_amount = Decimal(estimated_amount)
                if estimated_amount <= 0:
                    errors["estimated_amount"] = "Amount must be greater than zero."
                elif estimated_amount > Decimal("9999999999999.99"):
                    errors["estimated_amount"] = "Amount cannot exceed $9,999,999,999,999.99"
            except InvalidOperation:
                errors["estimated_amount"] = "Enter a valid amount."  
        # ---------- URL ----------
        if reference_link:
            p=urlparse(reference_link)
            if not p.scheme or not p.netloc:
                errors["reference_link"]="Enter valid URL."

        # ---------- Dates ----------
        op = dl = st = ed = None
        # Application Open Date
        if not application_open_date:
            errors["application_open_date"] = "Application opening date is required."
        else:
            op = datetime.strptime(application_open_date, "%Y-%m-%d").date()
        # Application Deadline
        if not application_deadline:
            errors["application_deadline"] = "Application deadline is required."
        else:
            dl = datetime.strptime(application_deadline, "%Y-%m-%d").date()
        # Research Start Date
        if not start_date:
            errors["start_date"] = "Research start date is required."
        else:
            st = datetime.strptime(start_date, "%Y-%m-%d").date()
        # Research End Date
        if not end_date:
            errors["end_date"] = "Research end date is required."
        else:
            ed = datetime.strptime(end_date, "%Y-%m-%d").date()
        # Deadline must be after opening date
        if op and dl and dl <= op:
            errors["application_deadline"] = (
                "Application deadline must be after the opening date."
            )
        # Research must start at least 30 days after deadline
        if st and dl and st < dl + timedelta(days=30):
            errors["start_date"] = (
                "Research must start at least 30 days after the application deadline."
            )
        # End date must be after start date
        if st and ed and ed <= st:
            errors["end_date"] = (
                "Research end date must be after the start date."
            )
            
        # ---------- Files ----------
        allowed_documents = [".pdf", ".doc", ".docx",".xls", ".xlsx"]
        allowed_images = [ ".jpg", ".jpeg", ".png" ]
        allowed_videos = [".mp4", ".mov", ".avi"]
        names = set()
        for f in files:
            ext = os.path.splitext(f.name)[1].lower()
            # Check file type
            if ext not in allowed_documents + allowed_images + allowed_videos:
                errors["supporting_documents"] = (
                    f"{f.name}: Unsupported file type."
                )
                break
            # Different size limits
            if ext in allowed_videos:
                max_size = 300 * 1024 * 1024   # 300 MB for videos
            elif ext in allowed_images:
                max_size = 20 * 1024 * 1024    # 20 MB for images
            else:
                max_size = 20 * 1024 * 1024    # 20 MB for documents
            if f.size > max_size:
                errors["supporting_documents"] = (
                    f"{f.name} exceeds the allowed size limit."
                )
                break
            # Duplicate file check
            if f.name.lower() in names:
                errors["supporting_documents"] = (
                    f"Duplicate file: {f.name}"
                )
                break
            names.add(f.name.lower())

        if errors:
            return render(request,
                "faculty_research/post_research_opportunity.html",
                {"uuid":uuid,
                "errors":errors,
                "faculty": faculty,
                "department": department,
                "old":request.POST}
            )
        opportunity=ResearchOpportunity.objects.create(
            title=title,
            category=category,
            short_description=short_description,
            description=description,
            start_date=start_date,
            end_date=end_date,
            available_slots=slots,
            estimated_amount = estimated_amount, 
            required_skills=required_skills,
            application_open_date=application_open_date,
            application_deadline=application_deadline,
            reference_link=reference_link,
            additional_notes=additional_notes,
            status=status,
            faculty=faculty,
            department=department,
        )
        for f in files:
            ResearchOpportunityDocument.objects.create(
                opportunity=opportunity,
                document=f
            )

        if status == "OPEN":
            opportunity_link = reverse(
                'Elsa_research:view_research',
                args=[opportunity.research_id, uuid]
            )
            faculty_display_name = faculty.user.get_full_name() or faculty.user.username
            all_students = StudentProfile.objects.select_related('user').all()
            Notification.objects.bulk_create([
                Notification(
                    user=student.user,
                    title="New Research Opportunity",
                    message=f"{faculty_display_name} posted a new research opportunity: {title}.",
                    notification_type="INFO",
                    link=opportunity_link,
                ) for student in all_students
            ])

            broadcast_update({
                "title": "New Research Opportunity",
                "message": f"{title} \u2014 posted by {faculty_display_name}",
                "opportunity": {
                    "research_id": opportunity.research_id,
                    "title": opportunity.title,
                    "short_description": opportunity.short_description,
                    "department_name": department.department_name if department else "",
                    "faculty_first_name": faculty.user.first_name,
                    "faculty_last_name": faculty.user.last_name,
                    "available_slots": opportunity.available_slots,
                    "application_deadline": (
                        dl.strftime("%d %b %Y") if dl else ""
                    ),
                    "skills": opportunity.skill_list,
                    "view_url": opportunity_link,
                },
            }, event="research_opportunity_published")
            committee_link = reverse('Elsa_research:committee_research_details_view', args=[uuid, opportunity.research_id])
            committee_message = f"{faculty_display_name} posted a new research opportunity: \"{title}\"."

            committee_recipients = _get_committee_recipients(opportunity, exclude_user=faculty.user)

            for recipient_user in committee_recipients.values():
                Notification.objects.create(
                    user=recipient_user,
                    title="New Research Opportunity",
                    message=committee_message,
                    notification_type="INFO",
                    link=committee_link,
                )
                send_notification(recipient_user.id, {
                    "title": "New Research Opportunity",
                    "message": committee_message,
                    "research_id": opportunity.research_id,
                    "research_title": opportunity.title,
                    "faculty_name": faculty_display_name,
                    "department_name": department.department_name if department else "",
                    "available_slots": opportunity.available_slots,
                    "application_deadline": dl.strftime("%d %b %Y") if dl else "",
                    "view_url": committee_link,
                }, event="research_opportunity_committee")            
        messages.success(
            request,
            "Research Opportunity Published Successfully."
            if status=="OPEN"
            else "Research Opportunity Saved as Draft."
        )
        return redirect("Elsa_research:research_opportunity",uuid=uuid)
    return render(request,
        "faculty_research/post_research_opportunity.html",
        {"uuid":uuid,
        "faculty": faculty,
        "department": department
        }
    )


@login_required
def edit_research_opportunity(request, research_id, uuid):
    try:
        opportunity = ResearchOpportunity.objects.get(
            research_id=research_id
        )
    except ResearchOpportunity.DoesNotExist:
        messages.error(request, "Research Opportunity not found.")
        return redirect(
            "Elsa_research:research_opportunity",
            uuid=uuid
        )
    faculty = FacultyProfile.objects.get(user=request.user)
    department = faculty.department   
    documents = ResearchOpportunityDocument.objects.filter(opportunity=opportunity)
    if request.method == "POST":
        errors = {}
        action = request.POST.get("action")
        if action == "publish":
            status = "OPEN"
        else:
            status = "DRAFT"
        title = request.POST.get("title","").strip()
        category = request.POST.get("category","").strip()
        short_description = request.POST.get("short_description","").strip()
        description = request.POST.get("description","").strip()
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        available_slots = request.POST.get("available_slots")
        estimated_amount = request.POST.get("estimated_amount", "").strip()
        required_skills = request.POST.get("required_skills","").strip()
        application_open_date = request.POST.get("application_open_date")
        application_deadline = request.POST.get("application_deadline")
        reference_link = request.POST.get("reference_link","").strip()
        additional_notes = request.POST.get("additional_notes","").strip()
        files = request.FILES.getlist(
            "supporting_documents"
        )
        delete_documents = request.POST.getlist(
            "delete_documents"
        )

        # ---------- Title ----------       
        if not title:
            errors["title"] = "Research title is required."
        elif len(title) < 10:
            errors["title"] = "Minimum 10 characters."
        elif len(title) > 255:
            errors["title"] = "Maximum 255 characters."
        # Must start with a letter
        elif not re.match(r"^[A-Za-z]", title):
            errors["title"] = "Title must start with an alphabet."
        # Must contain at least one alphabet
        elif not re.search(r"[A-Za-z]", title):
            errors["title"] = "Title must contain at least one alphabet."
        # Allow only letters, numbers, spaces, (), _, -, &
        elif not re.fullmatch(r"[A-Za-z][A-Za-z0-9\s()_\-&]*", title):
            errors["title"] = (
                "Only letters, numbers, spaces, (), _, -, and & are allowed."
            )
        # ---------- Category ----------
        if not category:
            errors["category"] = "Category is required."
        elif len(category) < 3 or len(category) > 100:
            errors["category"] = "Category must be 3-100 characters."
        elif not re.fullmatch(r"[A-Za-z][A-Za-z0-9\s()_\-&]*", category):
            errors["category"] = (
                "Category must start with an alphabet and can contain only "
                "letters, numbers, spaces, (), _, -, and &."
            )
        # ---------- Descriptions ----------
        if len(short_description)<30 or len(short_description)>250:
            errors["short_description"]="Short description must be 30-250 characters."

        if len(description)<100 or len(description)>3000:
            errors["description"]="Detailed description must be 100-3000 characters."

        # ---------- Slots ----------
        if not available_slots:
            errors["available_slots"] = "Available slots is required."
        else:
            try:
                slots = int(available_slots)
                if slots < 1 or slots > 10:
                    errors["available_slots"] = "Slots must be between 1 and 10."
            except ValueError:
                errors["available_slots"] = "Enter a valid number."
                
        # ---------- Skills ----------
        if not required_skills:
            errors["required_skills"] = "Required skills is mandatory."
        elif len(required_skills) < 5:
            errors["required_skills"] = "Minimum 5 characters."
        elif len(required_skills) > 500:
            errors["required_skills"] = "Maximum 500 characters."
        # ---------- Amount ----------
        if not estimated_amount:
            errors["estimated_amount"] = "Funding estimated amount is required."
        else:
            try:
                estimated_amount = Decimal(estimated_amount)
                if estimated_amount <= 0:
                    errors["estimated_amount"] = "Amount must be greater than zero."
                elif estimated_amount > Decimal("9999999999999.99"):
                    errors["estimated_amount"] = "Amount cannot exceed $9,999,999,999,999.99"
            except InvalidOperation:
                errors["estimated_amount"] = "Enter a valid amount."            

        # ---------- URL ----------
        if reference_link:
            p=urlparse(reference_link)
            if not p.scheme or not p.netloc:
                errors["reference_link"]="Enter valid URL."
        # ---------- Dates ----------
        op = dl = st = ed = None
        # Application Open Date
        if not application_open_date:
            errors["application_open_date"] = "Application opening date is required."
        else:
            op = datetime.strptime(application_open_date, "%Y-%m-%d").date()
        # Application Deadline
        if not application_deadline:
            errors["application_deadline"] = "Application deadline is required."
        else:
            dl = datetime.strptime(application_deadline, "%Y-%m-%d").date()
        # Research Start Date
        if not start_date:
            errors["start_date"] = "Research start date is required."
        else:
            st = datetime.strptime(start_date, "%Y-%m-%d").date()
        # Research End Date
        if not end_date:
            errors["end_date"] = "Research end date is required."
        else:
            ed = datetime.strptime(end_date, "%Y-%m-%d").date()
        # Deadline must be after opening date
        if op and dl and dl <= op:
            errors["application_deadline"] = (
                "Application deadline must be after the opening date."
            )
        # Research must start at least 30 days after deadline
        if st and dl and st < dl + timedelta(days=30):
            errors["start_date"] = (
                "Research must start at least 30 days after the application deadline."
            )
        # End date must be after start date
        if st and ed and ed <= st:
            errors["end_date"] = (
                "Research end date must be after the start date."
            )

        # ---------- Files ----------
        allowed_documents = [".pdf", ".doc", ".docx", ".xls", ".xlsx"]
        allowed_images = [".jpg", ".jpeg", ".png"]
        allowed_videos = [".mp4", ".mov", ".avi"]
        names = set()
        # Existing files in database
        existing_files = ResearchOpportunityDocument.objects.filter(
            opportunity=opportunity
        ).values_list("document", flat=True)
        for old_file in existing_files:
            names.add(os.path.basename(old_file).lower())
        # New uploaded files validation
        for f in files:
            ext = os.path.splitext(f.name)[1].lower()
            # Check file type
            if ext not in allowed_documents + allowed_images + allowed_videos:
                errors["supporting_documents"] = (
                    f"{f.name}: Unsupported file type."
                )
                break
            # File size validation
            if ext in allowed_videos:
                max_size = 300 * 1024 * 1024  # 300 MB
            elif ext in allowed_images:
                max_size = 20 * 1024 * 1024   # 20 MB
            else:
                max_size = 20 * 1024 * 1024   # 20 MB
            if f.size > max_size:
                errors["supporting_documents"] = (
                    f"{f.name} exceeds the allowed size limit."
                )
                break
            # Duplicate check (old files + newly uploaded files)
            if f.name.lower() in names:
                errors["supporting_documents"] = (
                    f"Duplicate file: {f.name}"
                )
                break
            # Add current file name for checking next uploads
            names.add(f.name.lower())
        if errors:
            return render(
                request,
                "faculty_research/edit_research_opportunity.html",
                {
                    "uuid":uuid,
                    "opportunity":opportunity,
                    "errors":errors,
                    "documents": documents,
                    "faculty": faculty,
                    "department": department,
                    "old":request.POST
                }
            )
        # ---------- UPDATE ----------
        faculty = FacultyProfile.objects.get(user=request.user)
        department = faculty.department
        opportunity.title = title
        opportunity.category = category
        opportunity.short_description = short_description
        opportunity.description = description
        opportunity.start_date = start_date
        opportunity.end_date = end_date
        opportunity.available_slots = slots
        opportunity.required_skills = required_skills
        opportunity.estimated_amount = estimated_amount
        opportunity.application_open_date = application_open_date
        opportunity.application_deadline = application_deadline
        opportunity.reference_link = reference_link
        opportunity.additional_notes = additional_notes
        opportunity.status = status
        opportunity.save()
        # Delete selected old documents
        for doc_id in delete_documents:
            try:
                doc = ResearchOpportunityDocument.objects.get(
                    id=doc_id,
                    opportunity=opportunity
                )
                doc.document.delete()   # delete actual file
                doc.delete()            # delete database record
            except ResearchOpportunityDocument.DoesNotExist:
                pass        
        # Add new documents
        for f in files:
            ResearchOpportunityDocument.objects.create(
                opportunity=opportunity,
                document=f
            )
        messages.success(
            request,
            "Research Opportunity Updated Successfully."
        )
        return redirect(
            "Elsa_research:research_opportunity",
            uuid=uuid
        )
    return render(
        request,
        "faculty_research/edit_research_opportunity.html",
        {
            "uuid":uuid,
            "opportunity":opportunity,
            'is_published': opportunity.status != "DRAFT",
            "documents": documents,
            "faculty":faculty,
            "department":department,
        }
    )

@login_required
def view_research_opportunity(request, research_id, uuid):
    opportunity = get_object_or_404(
        ResearchOpportunity,
        research_id=research_id
    )
    documents = ResearchOpportunityDocument.objects.filter(
        opportunity=opportunity
    )
    faculty = FacultyProfile.objects.get(user=request.user)
    department = faculty.department
    context = {
        "uuid": uuid,
        "opportunity": opportunity,
        "documents": documents,
        "faculty":faculty,
        "department":department,
    }
    return render(
        request,
        "faculty_research/view_research_opportunity.html",
        context
    )


@login_required
@never_cache
def research_funding(request, uuid):    
    faculty = FacultyProfile.objects.get(
        user=request.user
    )
    if not faculty.is_mentor:
        messages.error(
            request,
            "You do not have permission to access Research Funding."
        )
        return redirect(
            "faculty_dashboard",
            uuid=uuid
        )
    opportunities = ResearchOpportunity.objects.filter(
        faculty=faculty
    )
    if request.method == "POST":
        errors = {}

        research_id = request.POST.get("research")
        funding_source = request.POST.get(
            "funding_source",
            ""
        ).strip()
        funding_id = request.POST.get("funding_id")
        amount = request.POST.get("amount", "").strip()
        award_date = request.POST.get("award_date")
        sponsor = request.POST.get("sponsor", "").strip()

        # ---------- Research ----------
        if not research_id:
            errors["research"] = "Please select a research project."
        else:
            try:
                research = ResearchOpportunity.objects.get(
                    research_id=research_id,
                    faculty=faculty
                )
            except ResearchOpportunity.DoesNotExist:
                errors["research"] = "Invalid research project."

        # ---------- Funding Source ----------
        if not funding_source:
            errors["funding_source"] = "Funding source is required."
        elif len(funding_source) < 3:
            errors["funding_source"] = "Minimum 3 characters."
        elif len(funding_source) > 255:
            errors["funding_source"] = "Maximum 255 characters."
        elif not re.fullmatch(r"[A-Za-z][A-Za-z0-9\s()_\-&]*", funding_source):
            errors["funding_source"] = (
                "Funding source must start with an alphabet and contain only "
                "letters, numbers, spaces, (), _, -, and &."
            )

        # ---------- Amount ----------
        if not amount:
            errors["amount"] = "Funding amount is required."
        else:
            try:
                amount = Decimal(amount)
                if amount <= 0:
                    errors["amount"] = "Amount must be greater than zero."
                elif amount > Decimal("9999999999999.99"):
                    errors["amount"] = "Amount cannot exceed $9,999,999,999,999.99"
            except InvalidOperation:
                errors["amount"] = "Enter a valid amount."
        # ---------- Award Date ----------
        if not award_date:
            errors["award_date"] = "Award date is required."
        else:
            try:
                award = datetime.strptime(
                    award_date,
                    "%Y-%m-%d"
                ).date()
                if award > datetime.today().date():
                    errors["award_date"] = (
                        "Award date cannot be in the future."
                    )
            except ValueError:
                errors["award_date"] = "Enter a valid date."
        # ---------- Sponsor ----------
        if not sponsor:
            errors["sponsor"] = "Sponsor is required."
        elif len(sponsor) < 3:
            errors["sponsor"] = "Minimum 3 characters."
        elif len(sponsor) > 255:
            errors["sponsor"] = "Maximum 255 characters."
        elif not re.fullmatch(r"[A-Za-z][A-Za-z0-9\s()_\-&]*", sponsor):
            errors["sponsor"] = (
                "Sponsor must start with an alphabet and contain only "
                "letters, numbers, spaces, (), _, -, and &."
            )
        # ---------- Validation Failed ----------
        if errors:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                            return JsonResponse({"success": False, "errors": errors}, status=400)            
            all_fundings = ResearchFunding.objects.filter(
                research__faculty=faculty
            )
            total_funding = all_fundings.count()
            total_amount = (
                all_fundings.aggregate(
                    total=Sum("amount")
                )["total"] or Decimal("0.00")).quantize(Decimal("0.01")
            )
            total_sponsors = (
                all_fundings.values("sponsor")
                .distinct()
                .count()
            )
            total_projects = (
                all_fundings.values("research")
                .distinct()
                .count()
            )
            project_filter = request.GET.get(
                "research_filter",
                "all"
            )
            source_filter = request.GET.get(
                "source",
                "all"
            )
            sponsor_filter = request.GET.get(
                "sponsor",
                "all"
            )
            fundings = (
                ResearchFunding.objects
                .filter(research__faculty=faculty)
                .select_related(
                    "research",
                    "research__department"
                )
                .order_by("-award_date")
            )
            if project_filter != "all":
                fundings = fundings.filter(
                    research_id=project_filter
                )
            if source_filter != "all":
                fundings = fundings.filter(
                    funding_source=source_filter
                )
            if sponsor_filter != "all":
                fundings = fundings.filter(
                    sponsor=sponsor_filter
                )
            paginator = Paginator(fundings, 12)
            page_number = request.GET.get("page")
            fundings = paginator.get_page(page_number)
            funding_sources = (
                all_fundings.values_list(
                    "funding_source",
                    flat=True
                )
                .distinct()
                .order_by("funding_source")
            )
            sponsors = (
                all_fundings.values_list(
                    "sponsor",
                    flat=True
                )
                .distinct()
                .order_by("sponsor")
            )
            context = {
                "uuid": uuid,
                "fundings": fundings,
                "opportunities": opportunities,
                "errors": errors,
                "old": request.POST,
                "open_modal": True,
                "total_funding": total_funding,
                "total_amount": total_amount,
                "total_sponsors": total_sponsors,
                "total_projects": total_projects,
                "funding_sources": funding_sources,
                "sponsors": sponsors,
                "context_filters": {
                    "project": project_filter,
                    "source": source_filter,
                    "sponsor": sponsor_filter,
                },
            }
            return render(
                request,
                "faculty_research/research_funding.html",
                context,
            )
        # ---------- Save / Update ----------
        if funding_id:
            try:
                funding = ResearchFunding.objects.get(
                   funding_id=funding_id,
                    research__faculty=faculty
                )
                funding.research = research
                funding.funding_source = funding_source
                funding.amount = amount
                funding.award_date = award_date
                funding.sponsor = sponsor
                funding.save()
                messages.success(
                    request,
                    "Research funding updated successfully."
                )
            except ResearchFunding.DoesNotExist:
                messages.error(
                    request,
                    "Funding record not found."
                )
        else:
            new_funding = ResearchFunding.objects.create(
                research=research,
                funding_source=funding_source,
                amount=amount,
                award_date=award_date,
                sponsor=sponsor,
            )
            messages.success(
                request,
                "Research funding added successfully."
            )

            faculty_display_name = faculty.user.get_full_name() or faculty.user.username
            funding_message = f"{faculty_display_name} added funding for \"{research.title}\"."
            received_total = ResearchFunding.objects.filter(
                research=research
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
            estimated_total = research.estimated_amount or Decimal("0.00")
            balance_total = estimated_total - received_total
            award_date_display = award.strftime("%d %b %Y") if award else str(award_date)

            # ---- Split recipients: team-link vs committee-only-link ----
            team_recipients = _get_team_recipients(research, exclude_user=faculty.user)
            committee_recipients = _get_committee_recipients(research, exclude_user=faculty.user)
            committee_only_recipients = {
                uid: u for uid, u in committee_recipients.items()
                if uid not in team_recipients
            }

            funding_link_team = f"{reverse('Elsa_research:research_overview', args=[uuid])}?research={research.research_id}"
            funding_link_committee = reverse('Elsa_research:committee_funding_view', args=[uuid, research.research_id])

            def _send_funding_notification(recipient_user, link):
                Notification.objects.create(
                    user=recipient_user,
                    title="New Research Funding Entry",
                    message=funding_message,
                    notification_type="INFO",
                    link=link,
                )
                send_notification(recipient_user.id, {
                    "title": "New Research Funding Entry",
                    "message": funding_message,
                    "research_id": research.research_id,
                    "research_title": research.title,
                    "faculty_name": faculty_display_name,
                    "estimated_amount": f"{estimated_total:.2f}",
                    "received_amount": f"{received_total:.2f}",
                    "balance_amount": f"{balance_total:.2f}",
                    "funding_id": new_funding.funding_code,
                    "funding_source": funding_source,
                    "sponsor": sponsor,
                    "amount": f"{amount:.2f}",
                    "award_date": award_date_display,
                    "view_url": link,
                }, event="research_funding_added")

            for recipient_user in team_recipients.values():
                _send_funding_notification(recipient_user, funding_link_team)

            for recipient_user in committee_only_recipients.values():
                _send_funding_notification(recipient_user, funding_link_committee)             
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return redirect(
            "Elsa_research:research_funding",
            uuid=uuid
        )
    all_fundings = ResearchFunding.objects.filter(
        research__faculty=faculty
    )
    total_funding = all_fundings.count()
    total_amount = (all_fundings.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")).quantize(Decimal("0.01"))
    total_sponsors = (all_fundings.values("sponsor").distinct().count())
    total_projects = (all_fundings.values("research").distinct().count())
    project_filter = request.GET.get("research_filter","all")
    source_filter = request.GET.get("source","all")
    sponsor_filter = request.GET.get( "sponsor","all")
    fundings = (
        ResearchFunding.objects
        .filter(research__faculty=faculty)
        .select_related("research", "research__department")
        .order_by("-award_date"))
    if project_filter != "all":
        fundings = fundings.filter(research_id=project_filter)
    if source_filter != "all":
        fundings = fundings.filter(funding_source=source_filter)
    if sponsor_filter != "all":
        fundings = fundings.filter(sponsor=sponsor_filter)
    paginator = Paginator( fundings,12)
    page_number = request.GET.get( "page")
    fundings = paginator.get_page( page_number)
    funding_sources = (all_fundings.values_list("funding_source",flat=True).distinct().order_by("funding_source"))
    sponsors = (
        all_fundings.values_list("sponsor",flat=True).distinct().order_by("sponsor"))
    context = {
        "uuid": uuid,
        "fundings": fundings,
        "opportunities": opportunities,
        # stats
        "total_funding": total_funding,
        "total_amount": total_amount,
        "total_sponsors": total_sponsors,
        "total_projects": total_projects,
        # dropdowns
        "funding_sources": funding_sources,
        "sponsors": sponsors,
        # selected filters
        "context_filters": {
            "project": project_filter,
            "source": source_filter,
            "sponsor": sponsor_filter,
        }
    }
    return render( request,"faculty_research/research_funding.html", context)

@login_required
def research_funding_view(request, uuid, research_id):
    faculty = request.user.faculty_profile
    if not faculty.is_mentor:
        messages.error(request, "You do not have permission to access this page.")
        return redirect("faculty_dashboard",uuid=uuid)
    # Get selected research
    research = get_object_or_404(
        ResearchOpportunity,
        research_id=research_id
    )
    fundings = ResearchFunding.objects.filter(
        research=research
    ).order_by("-award_date")
    paginator = Paginator(fundings, 10)
    page_number = request.GET.get("page")
    funding_list = paginator.get_page(page_number)
    # Get all funding records
    fundings = ResearchFunding.objects.filter(
        research=research
    ).order_by("-award_date")
    # Received amount
    received_amount = fundings.aggregate(
        total=Sum("amount")
    )["total"] or 0
    estimated_amount = research.estimated_amount or Decimal("0.00")
    balance_amount = estimated_amount - received_amount
    context = {
        "uuid": uuid,
        "research": research,
        "fundings": funding_list,
        "estimated_amount": estimated_amount,
        "received_amount": received_amount,
        "balance_amount": balance_amount,
    }
    return render(
        request,
        "faculty_research/research_funding_view.html",
        context
    )

@login_required
def committee_funding(request, uuid):
    faculty = request.user.faculty_profile
    if not faculty.is_research_committee_member:
        messages.error(
            request,
            "You do not have permission to access this page."
        )
        return redirect(
            "faculty_dashboard",
            uuid=uuid
        )
    estimated_amount = 1000000
    all_researches = ResearchOpportunity.objects.filter(
        fundings__isnull=False
    ).distinct()
    total_projects = all_researches.count()
    total_estimated_amount = (
                    all_researches.aggregate(
                        total=Sum("estimated_amount")
                    )["total"] or Decimal("0.00")
                ).quantize(Decimal("0.01"))
    total_amount = (
        ResearchFunding.objects.aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")).quantize(Decimal("0.01")
    )
    total_balance_amount = total_estimated_amount - total_amount
    research_filter = request.GET.get("research_filter", "all")
    mentor = request.GET.get("mentor", "all")
    sponsor = request.GET.get("sponsor", "all")
    source = request.GET.get("source", "all")
    researches = (
        ResearchOpportunity.objects.filter(
            fundings__isnull=False
        )
        .select_related(
            "faculty",
            "faculty__user"
        )
        .prefetch_related(
            "fundings"
        )
        .distinct()
    )
    if research_filter != "all":
        researches = researches.filter(
            research_id=research_filter
        )
    if mentor != "all":
        researches = researches.filter(
            faculty_id=mentor
        )
    if sponsor != "all":
        researches = researches.filter(
            fundings__sponsor=sponsor
        )
    if source != "all":
        researches = researches.filter(
            fundings__funding_source=source
        )
    researches = researches.distinct()
    funding_data = []
    for research in researches:
        received_amount = (
            research.fundings.aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00")).quantize(Decimal("0.01")
        )
        estimated_amount = research.estimated_amount or Decimal("0.00")
        funding_data.append({
            "research": research,
            "estimated_amount": estimated_amount,
            "received_amount": received_amount,
            "balance_amount": estimated_amount - received_amount,
        })
    paginator = Paginator(funding_data, 10)
    page_number = request.GET.get("page")
    funding_list = paginator.get_page(page_number)
    research_ids = (
        ResearchOpportunity.objects.filter(
            fundings__isnull=False
        )
        .values_list(
            "research_id",
            flat=True
        )
        .distinct()
        .order_by("research_id")
    )
    mentors = (
        FacultyProfile.objects.filter(
            research_opportunities__fundings__isnull=False
        )
        .select_related("user")
        .distinct()
        .order_by("user__first_name")
    )
    sponsors = (
        ResearchFunding.objects.values_list(
            "sponsor",
            flat=True
        )
        .distinct()
        .order_by("sponsor")
    )
    funding_sources = (
        ResearchFunding.objects.values_list(
            "funding_source",
            flat=True
        )
        .distinct()
        .order_by("funding_source")
    )
    context = {
        "uuid": uuid,
        "funding_data": funding_list,
        "total_projects": total_projects,
        "total_estimated_amount": total_estimated_amount,
        "total_amount": total_amount,
        "total_balance_amount": total_balance_amount,
        "total_funding": ResearchFunding.objects.count(),
        "research_ids": research_ids,
        "mentors": mentors,
        "sponsors": sponsors,
        "funding_sources": funding_sources,
        "context_filters": {
            "research": research_filter,
            "mentor": mentor,
            "sponsor": sponsor,
            "source": source,
        },
    }
    return render(
        request,
        "faculty_research/committee_funding.html",
        context
    )

@login_required
def committee_funding_view(request, uuid, research_id):
    faculty = request.user.faculty_profile
    if not faculty.is_research_committee_member:
        messages.error(
            request,
            "You do not have permission to access this page."
        )
        return redirect(
            "faculty_dashboard",
            uuid=uuid
        )
    research = get_object_or_404(
        ResearchOpportunity,
        research_id=research_id
    )
    fundings = ResearchFunding.objects.filter(
        research=research
    ).order_by("-award_date")
    paginator = Paginator(fundings, 10)
    page_number = request.GET.get("page")
    funding_list = paginator.get_page(page_number)
    fundings = ResearchFunding.objects.filter(
        research=research
    ).order_by("-award_date")   
    received_amount =(fundings.aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")).quantize(Decimal("0.01"))
    estimated_amount = 1000000
    estimated_amount = research.estimated_amount or Decimal("0.00")
    balance_amount = estimated_amount - received_amount
    context = {
        "uuid": uuid,
        "research": research,
        "fundings": funding_list,
        "estimated_amount": estimated_amount,
        "received_amount": received_amount,
        "balance_amount": balance_amount,
    }
    return render(
        request,
        "faculty_research/committee_funding_view.html",
        context
    )

@login_required
def research_progress(request, uuid):
    faculty = FacultyProfile.objects.get(user=request.user)
    if not faculty.is_mentor:
        messages.error(request, "You do not have permission to access Research Funding.")
        return redirect("faculty_dashboard", uuid=uuid)

    researches = ResearchOpportunity.objects.filter(faculty=faculty)
    research_id = request.GET.get("research")

    if research_id:
        research = ResearchOpportunity.objects.get(
            research_id=research_id,
            faculty=faculty
        )
    else:
        research = researches.first()

    milestones = ResearchMilestone.objects.none()
    assignments = StudentMilestoneAssignment.objects.none()
    reports = []
    team_members = []
    student_progress_list = []
    overall_progress = 0
    completed_milestones = 0
    total_milestones = 0
    co_mentor_names = []
    student_member_count = 0
    faculty_member_count = 0
    days_remaining = None
    current_phase = "Not Started"
    team = None
    total_team_members = 0

    if research:
        milestones = research.milestones.prefetch_related(
            "student_assignments__student__user"
        )
        total_milestones = milestones.count()
        completed_milestones = milestones.filter(status="completed").count()

        assignments = StudentMilestoneAssignment.objects.select_related(
            "student", "student__user", "milestone",
        ).filter(milestone__research=research)
        student_progress_data = {}

        student_departments = {
            ap.student_id: ap.department.department_name if ap.department else "No Department"
            for ap in StudentAcademicProfile.objects.select_related("department").filter(
                student_id__in=assignments.values_list("student_id", flat=True)
            )
        }

        for assignment in assignments:
            student = assignment.student
            if student.id not in student_progress_data:
                student_progress_data[student.id] = {
                    "student": student,
                    "department_name": student_departments.get(student.id, "No Department"),
                    "milestones": [],
                    "total_progress": 0,
                    "count": 0,
                    "statuses": [],
                }

            student_progress_data[student.id]["milestones"].append(assignment)
            student_progress_data[student.id]["total_progress"] += assignment.student_progress
            student_progress_data[student.id]["count"] += 1
            student_progress_data[student.id]["statuses"].append(assignment.status)

        for data in student_progress_data.values():
            data["average_progress"] = round(
                data["total_progress"] / data["count"]
            )
            statuses = data["statuses"]
            data["all_completed"] = bool(statuses) and all(s == "completed" for s in statuses)
            data["has_started"] = any(s != "assigned" for s in statuses)
        reports = StudentProgressReport.objects.select_related(
            "assignment__student__user", "assignment__milestone",
        ).filter(
            assignment__milestone__research=research,
            status="submitted"
        )

        overall_progress = assignments.aggregate(
            Avg("student_progress")
        )["student_progress__avg"] or 0

        team = ResearchTeam.objects.filter(research_details=research).first()
        if team:
            team_members = team.member.select_related(
                "faculty__user", "student__user"
            ).all()
            co_mentor_names = [
                m.faculty.user.get_full_name()
                for m in team_members if m.role == "CO_MENTOR"
            ]
            student_member_count = sum(1 for m in team_members if m.role == "STUDENT")
            faculty_member_count = sum(1 for m in team_members if m.faculty_id)
            total_team_members = team_members.count()

        if research.end_date:
            days_remaining = (research.end_date - timezone.now().date()).days

        in_progress_milestone = milestones.filter(status="in_progress").order_by("-deadline").first()
        if in_progress_milestone:
            current_phase = in_progress_milestone.title
        elif completed_milestones and completed_milestones == total_milestones and total_milestones > 0:
            current_phase = "Completed"

        student_progress_list = list(student_progress_data.values())
    context = {
        "uuid": uuid,
        "researches": researches,
        "research": research,
        "milestones": milestones,
        "assignments": assignments,
        "reports": reports,
        "team_members": team_members,
        "overall_progress": round(overall_progress),
        "completed_milestones": completed_milestones,
        "total_milestones": total_milestones,
        "co_mentor_names": co_mentor_names,
        "student_member_count": student_member_count,
        "faculty_member_count": faculty_member_count,
        "days_remaining": days_remaining,
        "current_phase": current_phase,
        "team": team,
        "total_team_members": total_team_members,
        "student_progress_list": student_progress_list,
    }
    return render(request, "faculty_research/research_progress.html", context)


def _student_progress_summary(student, research):
    assignments = StudentMilestoneAssignment.objects.filter(
        student=student,
        milestone__research=research
    ).select_related("milestone")
    total = assignments.count()
    avg_progress = round(
        sum(a.student_progress for a in assignments) / total
    ) if total else 0
    statuses = [a.status for a in assignments]
    all_completed = bool(statuses) and all(s == "completed" for s in statuses)
    has_started = any(s != "assigned" for s in statuses)
    try:
        academic = StudentAcademicProfile.objects.select_related("department").get(student=student)
        department_name = academic.department.department_name if academic.department else "No Department"
    except StudentAcademicProfile.DoesNotExist:
        department_name = "No Department"
    return {
        "student_id": student.pk,
        "name": student.user.get_full_name(),
        "department_name": department_name,
        "average_progress": avg_progress,
        "all_completed": all_completed,    
        "has_started": has_started,        
        "milestones": [
            {"milestone_id": a.milestone_id, "title": a.milestone.title}
            for a in assignments
        ],
    }

@login_required
@require_POST
def review_student_report(request, uuid, report_id):
    faculty = FacultyProfile.objects.get(user=request.user)
    report = get_object_or_404(
        StudentProgressReport,
        report_id=report_id,
        assignment__milestone__research__faculty=faculty
    )
    action = request.POST.get("action")
    feedback = request.POST.get("feedback", "").strip()
    progress_url = (
        f"{reverse('Elsa_research:research_progress', args=[uuid])}"
        f"?research={report.assignment.milestone.research_id}"
    )
    if action == "approve":
        report.status = "approved"
        report.assignment.student_progress = report.progress_percentage
        report.assignment.status = "completed"
        report.assignment.save()
    elif action == "revision":
        if not feedback:
            messages.error(request, "Feedback is required.")
            return redirect(progress_url)
        elif not re.search(r"[A-Za-z]", feedback):
            messages.error(request, "Feedback cannot have only letters and special characters.")
            return redirect(progress_url)
        report.status = "revision"
    else:
        messages.error(request, "Invalid review action.")
        return redirect(progress_url)
    report.faculty_feedback = feedback
    report.reviewed_by = faculty
    report.reviewed_date = timezone.now()
    report.save()
 
    student_user = report.assignment.student.user
    research = report.assignment.milestone.research
    student_link = f"{reverse('Elsa_research:student_research_progress', args=[uuid])}?research_id={research.research_id}"
 
    if action == "approve":
        review_title = "Report Approved"
        review_message = f"Your report for \"{report.assignment.milestone.title}\" was approved."
    else:
        review_title = "Revision Requested"
        review_message = f"Revision requested for \"{report.assignment.milestone.title}\": {feedback}"
 
    Notification.objects.create(
        user=student_user,
        title=review_title,
        message=review_message,
        notification_type="SUCCESS" if action == "approve" else "WARNING",
        link=student_link,
    )
    send_notification(student_user.id, {
        "title": review_title,
        "message": review_message,
        "research_id": research.research_id,
        "assignment_id": report.assignment.assignment_id,
        "report_id": report.report_id,
        "report_title": report.title,
        "milestone_title": report.assignment.milestone.title,
        "milestone_status": report.assignment.milestone.status, 
        "status": report.status,
        "status_display": report.get_status_display(),
        "feedback": feedback,
        "student_progress": report.assignment.student_progress,
        "submitted_date": report.submitted_date.strftime("%d %b %Y") if report.submitted_date else "",
        "reviewed_date": report.reviewed_date.strftime("%d %b %Y") if report.reviewed_date else "",
    }, event="report_reviewed")
 
    messages.success(
        request,
        "Report approved successfully." if action == "approve" else "Revision requested."
    )
    return redirect(progress_url)

def _student_progress_summary(student, research):
    assignments = StudentMilestoneAssignment.objects.filter(
        student=student,
        milestone__research=research
    ).select_related("milestone")
    total = assignments.count()
    avg_progress = round(
        sum(a.student_progress for a in assignments) / total
    ) if total else 0
    try:
        academic = StudentAcademicProfile.objects.select_related("department").get(student=student)
        department_name = academic.department.department_name if academic.department else "No Department"
    except StudentAcademicProfile.DoesNotExist:
        department_name = "No Department"
    return {
        "student_id": student.pk,
        "name": student.user.get_full_name(),
        "department_name": department_name,
        "average_progress": avg_progress,
        "milestones": [
            {"milestone_id": a.milestone_id, "title": a.milestone.title}
            for a in assignments
        ],
    }


@login_required
def create_milestone(request, uuid, research_id):
    faculty = FacultyProfile.objects.get(user=request.user)
    if not faculty.is_mentor:
        messages.error(request, "You do not have permission.")
        return redirect("faculty_dashboard", uuid=uuid)
    try:
        research = ResearchOpportunity.objects.get(
            research_id=research_id,
            faculty=faculty
        )
    except ResearchOpportunity.DoesNotExist:
        messages.error(request, "Research project not found.")
        return redirect("Elsa_research:research_progress", uuid=uuid)
    progress_url = f"{reverse('Elsa_research:research_progress', args=[uuid])}?research={research_id}"
    if request.method != "POST":
        return redirect(progress_url)

    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    # ---------- Read submitted fields ----------
    milestone_id = request.POST.get("milestone_id")
    title = request.POST.get("title", "").strip()
    description = request.POST.get("description", "").strip()
    start_date = request.POST.get("start_date")
    deadline = request.POST.get("deadline")
    expected_percentage = request.POST.get("expected_percentage", "0").strip()
    status = request.POST.get("status", "not_started")
    errors = {}
    # ---------- Title ----------
    if not title:
        errors["title"] = "Milestone title is required."
    elif len(title) < 3:
        errors["title"] = "Minimum 3 characters."
    elif len(title) > 255:
        errors["title"] = "Maximum 255 characters."
    elif not re.search(r"[A-Za-z]", title):
        errors["title"] = "Title must contain at least one alphabet character."

    # ---------- Description ----------
    if not description:
        errors["description"] = "Description is required."
    elif not re.search(r"[A-Za-z]", description):
        errors["description"] = "Description must contain at least one alphabet character."

    # ---------- Dates ----------
    start = deadline_date = None

    if not start_date:
        errors["start_date"] = "Start date is required."
    else:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            errors["start_date"] = "Enter a valid date."

    if not deadline:
        errors["deadline"] = "Deadline is required."
    else:
        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
        except ValueError:
            errors["deadline"] = "Enter a valid date."

    if start and deadline_date and deadline_date <= start:
        errors["deadline"] = "Deadline must be after the start date."
    # ---------- Expected Percentage ----------
    if not expected_percentage:
        errors["expected_percentage"] = "Percentage is required."    
    try:
        expected_percentage = int(expected_percentage or 0)
        if expected_percentage < 0 or expected_percentage > 100:
            errors["expected_percentage"] = "Must be between 0 and 100."
    except ValueError:
        errors["expected_percentage"] = "Enter a valid number."
    # ---------- Status ----------
    valid_statuses = dict(ResearchMilestone.STATUS_CHOICES)

    if status not in valid_statuses:
        errors["status"] = "Invalid status."

    # Status can only move forward once
    if milestone_id:
        try:
            existing_milestone = ResearchMilestone.objects.get(
                milestone_id=milestone_id,
                research=research
            )
            current_status = existing_milestone.status
            allowed_transition = {
                "not_started": "in_progress",
                "in_progress": "completed",
            }
            if current_status == "completed":
                errors["status"] = "Completed milestones cannot be changed."
            elif current_status == "delayed":
                errors["status"] = "Delayed milestones cannot be changed."
            elif status != allowed_transition.get(current_status):
                errors["status"] = (
                    f"Milestone is already '{existing_milestone.get_status_display()}'. "
                    f"It can only be moved to the next stage."
                )
        except ResearchMilestone.DoesNotExist:
            errors["status"] = "Milestone not found."

    # ---------- Validation failed ----------
    if errors:
        if is_ajax:
            return JsonResponse({"success": False, "errors": errors}, status=400)
        for msg in errors.values():
            messages.error(request, msg)
        return redirect(progress_url)

    # ---------- Save ----------
    if milestone_id:
        # UPDATE existing milestone
        try:
            milestone = ResearchMilestone.objects.get(
                milestone_id=milestone_id,
                research=research
            )
        except ResearchMilestone.DoesNotExist:
            if is_ajax:
                return JsonResponse(
                    {"success": False, "errors": {"title": "Milestone not found."}},
                    status=404
                )
            messages.error(request, "Milestone not found.")
            return redirect(progress_url)
        milestone.title = title
        milestone.description = description
        milestone.start_date = start
        milestone.deadline = deadline_date
        milestone.expected_percentage = expected_percentage
        milestone.status = status
        milestone.save()
        for assignment in milestone.student_assignments.select_related("student__user"):
            student_user = assignment.student.user
            update_message = f"\"{milestone.title}\" was updated to {milestone.get_status_display()}."
            student_link = f"{reverse('Elsa_research:student_research_progress', args=[uuid])}?research_id={research.research_id}"
 
            Notification.objects.create(
                user=student_user,
                title="Milestone Updated",
                message=update_message,
                notification_type="INFO",
                link=student_link,
            )
            send_notification(student_user.id, {
                "title": "Milestone Updated",
                "message": update_message,
                "research_id": research.research_id,
                "assignment_id": assignment.assignment_id,
                "assignment_status": assignment.status,
                "milestone_title": milestone.title,
                "milestone_description": milestone.description,
                "milestone_status": milestone.status,
                "deadline": milestone.deadline.strftime("%d %b %Y"),
                "expected_percentage": milestone.expected_percentage,
            }, event="milestone_updated")      
        team_recipients = _get_team_recipients(research, exclude_user=faculty.user)
        committee_recipients = _get_committee_recipients(research, exclude_user=faculty.user)
        committee_only_recipients = {
            uid: u for uid, u in committee_recipients.items()
            if uid not in team_recipients
        }

        overview_link = f"{reverse('Elsa_research:research_overview', args=[uuid])}?research={research.research_id}"
        committee_link = reverse('Elsa_research:committee_research_details_view', args=[uuid, research.research_id])
        update_message_overview = (
            f"{faculty.user.get_full_name() or faculty.user.username} updated milestone "
            f"\"{milestone.title}\" to {milestone.get_status_display()} for \"{research.title}\"."
        )

        for recipient_user in team_recipients.values():
            Notification.objects.create(
                user=recipient_user,
                title="Milestone Updated",
                message=update_message_overview,
                notification_type="INFO",
                link=overview_link,
            )
            send_notification(recipient_user.id, {
                "title": "Milestone Updated",
                "message": update_message_overview,
                "research_id": research.research_id,
                "milestone_id": milestone.milestone_id,
                "milestone_title": milestone.title,
                "status": milestone.status,
                "status_display": milestone.get_status_display(),
                "deadline": milestone.deadline.strftime("%d %b %Y"),
                "expected_percentage": milestone.expected_percentage,
            }, event="milestone_updated_overview")

        for recipient_user in committee_only_recipients.values():
            Notification.objects.create(
                user=recipient_user,
                title="Milestone Updated",
                message=update_message_overview,
                notification_type="INFO",
                link=committee_link,
            )
            send_notification(recipient_user.id, {
                "title": "Milestone Updated",
                "message": update_message_overview,
                "research_id": research.research_id,
                "milestone_id": milestone.milestone_id,
                "milestone_title": milestone.title,
                "status": milestone.status,
                "status_display": milestone.get_status_display(),
                "deadline": milestone.deadline.strftime("%d %b %Y"),
                "expected_percentage": milestone.expected_percentage,
            }, event="milestone_updated_overview")         
        messages.success(request, "Milestone updated successfully.")
    else:
        # CREATE new milestone
        milestone = ResearchMilestone.objects.create(
            research=research,
            title=title,
            description=description,
            start_date=start,
            deadline=deadline_date,
            expected_percentage=expected_percentage,
            status=status,
            created_by=faculty,
        )
        team = ResearchTeam.objects.filter(research_details=research).first()

        faculty_display_name = faculty.user.get_full_name() or faculty.user.username
        milestone_message = f"{faculty_display_name} assigned a new milestone \"{title}\" for {research.title}."
        student_link = f"{reverse('Elsa_research:student_research_progress', args=[uuid])}?research_id={research.research_id}"
        assigned_chip_data = []

        if team:
            student_members = team.member.filter(
                role="STUDENT",
                student__isnull=False
            ).select_related("student__user")

            new_assignments = StudentMilestoneAssignment.objects.bulk_create([
                StudentMilestoneAssignment(milestone=milestone, student=member.student, student_progress=0)
                for member in student_members
            ])

            # ---- notify assigned students ----
            for assignment in new_assignments:
                student_user = assignment.student.user
                Notification.objects.create(
                    user=student_user,
                    title="New Milestone Assigned",
                    message=milestone_message,
                    notification_type="INFO",
                    link=student_link,
                )
                send_notification(student_user.id, {
                    "title": "New Milestone Assigned",
                    "message": milestone_message,
                    "research_id": research.research_id,
                    "assignment_id": assignment.assignment_id,
                    "milestone_title": milestone.title,
                    "milestone_description": milestone.description,
                    "milestone_status": milestone.status,
                    "deadline": milestone.deadline.strftime("%d %b %Y"),
                    "expected_percentage": milestone.expected_percentage,
                }, event="milestone_assigned")

            assigned_chip_data = [
                {
                    "name": a.student.user.get_full_name(),
                    "progress": a.student_progress,
                    "status": a.status,
                    "status_display": a.get_status_display(),
                }
                for a in new_assignments
            ]

        # ---- notify co-mentors/committee ONCE, regardless of whether a team exists ----
        team_recipients = _get_team_recipients(research, exclude_user=faculty.user)
        committee_recipients = _get_committee_recipients(research, exclude_user=faculty.user)
        committee_only_recipients = {
            uid: u for uid, u in committee_recipients.items()
            if uid not in team_recipients
        }

        overview_link = f"{reverse('Elsa_research:research_overview', args=[uuid])}?research={research.research_id}"
        committee_link = reverse('Elsa_research:committee_research_details_view', args=[uuid, research.research_id])

        def _send_milestone_created_notification(recipient_user, link):
            Notification.objects.create(
                user=recipient_user,
                title="New Milestone Created",
                message=milestone_message,
                notification_type="INFO",
                link=link,
            )
            send_notification(recipient_user.id, {
                "title": "New Milestone Created",
                "message": milestone_message,
                "research_id": research.research_id,
                "milestone_id": milestone.milestone_id,
                "title_text": milestone.title,
                "description": milestone.description,
                "status": milestone.status,
                "status_display": milestone.get_status_display(),
                "start_date": milestone.start_date.strftime("%d %b %Y"),
                "deadline": milestone.deadline.strftime("%d %b %Y"),
                "expected_percentage": milestone.expected_percentage,
                "assigned_students": assigned_chip_data,
            }, event="milestone_created")

        for recipient_user in team_recipients.values():
            _send_milestone_created_notification(recipient_user, overview_link)

        for recipient_user in committee_only_recipients.values():
            _send_milestone_created_notification(recipient_user, committee_link)

        messages.success(request, "Milestone created successfully.")
    # ---------- Response ----------
    if is_ajax:
        assigned_students = [
            a.student.user.get_full_name()
            for a in milestone.student_assignments.select_related("student__user").all()
        ]
 
        students_update = []
        for a in milestone.student_assignments.select_related("student__user").all():
            student = a.student
            assignments_qs = StudentMilestoneAssignment.objects.filter(
                student=student, milestone__research=research
            ).select_related("milestone")
            total = assignments_qs.count()
            avg_progress = round(sum(x.student_progress for x in assignments_qs) / total) if total else 0
            statuses = [x.status for x in assignments_qs]
            all_completed = bool(statuses) and all(s == "completed" for s in statuses)
            has_started = any(s != "assigned" for s in statuses)
            try:
                academic = StudentAcademicProfile.objects.select_related("department").get(student=student)
                department_name = academic.department.department_name if academic.department else "No Department"
            except StudentAcademicProfile.DoesNotExist:
                department_name = "No Department"
 
            students_update.append({
                "student_id": student.pk,
                "name": student.user.get_full_name(),
                "department_name": department_name,
                "average_progress": avg_progress,
                "all_completed": all_completed,
                "has_started": has_started,
                "milestones": [
                    {"milestone_id": x.milestone_id, "title": x.milestone.title}
                    for x in assignments_qs
                ],
            })
 
        return JsonResponse({
            "success": True,
            "milestone": {
                "milestone_id": milestone.milestone_id,
                "title": milestone.title,
                "description": milestone.description,
                "start_date": milestone.start_date.strftime("%d %b %Y"),
                "deadline": milestone.deadline.strftime("%d %b %Y"),
                "start_date_iso": milestone.start_date.strftime("%Y-%m-%d"),
                "deadline_iso": milestone.deadline.strftime("%Y-%m-%d"),
                "expected_percentage": milestone.expected_percentage,
                "status": milestone.status,
                "status_display": milestone.get_status_display(),
                "assigned_students": assigned_students,
            },
            "students_update": students_update,
        })
    return redirect(progress_url)

@login_required
def student_progress_detail(request, uuid, student_id, research_id):
    faculty = FacultyProfile.objects.get(user=request.user)
    research = get_object_or_404(
        ResearchOpportunity,
        research_id=research_id,
        faculty=faculty
    )
    student = get_object_or_404(StudentProfile, pk=student_id)
    assignments = StudentMilestoneAssignment.objects.filter(
        student=student,
        milestone__research=research
    ).select_related("milestone")
    try:
        academic = StudentAcademicProfile.objects.select_related("department").get(student=student)
        department_name = academic.department.department_name if academic.department else "No Department"
    except StudentAcademicProfile.DoesNotExist:
        department_name = "No Department"

    overall_progress = (
        round(sum(a.student_progress for a in assignments) / assignments.count())
        if assignments.exists() else 0
    )
    reports = StudentProgressReport.objects.filter(
        assignment__student=student,
        assignment__milestone__research=research
    ).select_related(
        "assignment__milestone"
    ).prefetch_related(
        "attachments"
    ).order_by("-submitted_date")
    data = {
        "name": student.user.get_full_name(),
        "email": student.user.email,
        "department": department_name,
        "overall_progress": overall_progress,
        "total_milestones": assignments.count(),
        "completed_milestones": assignments.filter(status="completed").count(),
        "milestones": [
            {
                "title": a.milestone.title,
                "progress": a.student_progress,
                "status": a.get_status_display(),
                "deadline": a.milestone.deadline.strftime("%d %b %Y") if a.milestone.deadline else "--",
            }
            for a in assignments
        ],
        "reports": [
            {
                "title": r.title,
                "milestone": r.assignment.milestone.title,
                "status": r.get_status_display(),
                "status_raw": r.status,
                "submitted_date": r.submitted_date.strftime("%d %b %Y") if r.submitted_date else "--",
                "progress": r.progress_percentage,
                "feedback": r.faculty_feedback or "",
                "attachments": [
                    {
                        "name": a.file.name.split("/")[-1],
                        "url": a.file.url,
                    }
                    for a in r.attachments.all()
                ],
            }
            for r in reports
        ],
    }
    return JsonResponse(data)

@login_required
def research_presentation(request, uuid):
    faculty = FacultyProfile.objects.get(user=request.user)
    if not faculty.is_mentor:
        messages.error(request, "You do not have permission to access this page.")
        return redirect("faculty_dashboard", uuid=uuid)

    researches = ResearchOpportunity.objects.filter(faculty=faculty)
    research_id = request.GET.get("research")

    if research_id:
        research = get_object_or_404(ResearchOpportunity, research_id=research_id, faculty=faculty)
    else:
        research = researches.first()

    presentations = ResearchPresentation.objects.none()
    total_presentations = 0
    total_awards = 0
    total_certificates = 0
    paginator = Paginator(presentations, 12)
    presentation_page = paginator.get_page(request.GET.get("page"))

    if research:
        presentations = ResearchPresentation.objects.filter(
            research=research
        ).prefetch_related("documents").order_by("-presentation_date")
        total_presentations = presentations.count()
        total_awards = presentations.exclude(award__isnull=True).exclude(award__exact="").count()
        total_certificates = presentations.exclude(certificate_file="").exclude(certificate_file__isnull=True).count()
        paginator = Paginator(presentations, 12)
        presentation_page = paginator.get_page(request.GET.get("page"))
    context = {
        "uuid": uuid,
        "researches": researches,
        "research": research,
        "presentations": presentation_page,
        "presentation_page": presentation_page,
        "total_presentations": total_presentations,
        "total_awards": total_awards,
        "total_certificates": total_certificates,
    }
    return render(request, "faculty_research/research_presentation.html", context)


@login_required
def create_presentation(request, uuid, research_id):
    faculty = FacultyProfile.objects.get(user=request.user)
    if not faculty.is_mentor:
        messages.error(request, "You do not have permission.")
        return redirect("faculty_dashboard", uuid=uuid)

    try:
        research = ResearchOpportunity.objects.get(research_id=research_id, faculty=faculty)
    except ResearchOpportunity.DoesNotExist:
        messages.error(request, "Research project not found.")
        return redirect("Elsa_research:research_presentation", uuid=uuid)

    progress_url = f"{reverse('Elsa_research:research_presentation', args=[uuid])}?research={research_id}"

    if request.method != "POST":
        return redirect(progress_url)

    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    presentation_id = request.POST.get("presentation_id")
    event_name = request.POST.get("event_name", "").strip()
    presentation_date = request.POST.get("presentation_date")
    award = request.POST.get("award", "").strip()
    certificate_file = request.FILES.get("certificate_file")
    extra_files = request.FILES.getlist("documents")

    errors = {}

    if not event_name:
        errors["event_name"] = "Event name is required."
    elif len(event_name) < 3:
        errors["event_name"] = "Minimum 3 characters."
    elif len(event_name) > 255:
        errors["event_name"] = "Maximum 255 characters."
    elif not re.search(r"[A-Za-z]", event_name):
        errors["event_name"] = "Event name cannot have numbers and special characters alone."

    pres_date = None
    if not presentation_date:
        errors["presentation_date"] = "Date is required."
    else:
        try:
            pres_date = datetime.strptime(presentation_date, "%Y-%m-%d").date()
            if pres_date > datetime.today().date():
                errors["presentation_date"] = "Date cannot be in the future."
        except ValueError:
            errors["presentation_date"] = "Enter a valid date."

    if award and not re.search(r"[A-Za-z]", award):
        errors["award"] = "Award must contain at least one alphabet character."

    allowed_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".ppt", ".pptx", ".doc", ".docx"]
    max_size = 20 * 1024 * 1024
    if certificate_file:
        ext = os.path.splitext(certificate_file.name)[1].lower()
        if ext not in allowed_extensions:
            errors["certificate_file"] = "Only PDF, JPG, PNG, PPT/PPTX, and DOC/DOCX files are allowed."
        elif certificate_file.size > 10 * 1024 * 1024:
            errors["certificate_file"] = "File exceeds the 10MB size limit."
    for f in extra_files:
        ext = os.path.splitext(f.name)[1].lower()
        if ext not in allowed_extensions:
            errors["documents"] = f"{f.name}: unsupported file type."
            break
        if f.size > max_size:
            errors["documents"] = f"{f.name} exceeds the 20MB size limit."
            break

    if errors:
        if is_ajax:
            return JsonResponse({"success": False, "errors": errors}, status=400)
        for msg in errors.values():
            messages.error(request, msg)
        return redirect(progress_url)

    if presentation_id:
        try:
            presentation = ResearchPresentation.objects.get(
                presentation_id=presentation_id,
                research=research
            )
        except ResearchPresentation.DoesNotExist:
            if is_ajax:
                return JsonResponse({"success": False, "errors": {"event_name": "Presentation not found."}}, status=404)
            messages.error(request, "Presentation not found.")
            return redirect(progress_url)

        presentation.event_name = event_name
        presentation.presentation_date = pres_date
        presentation.award = award
        if certificate_file:
            presentation.certificate_file = certificate_file
        presentation.save()
        messages.success(request, "Presentation updated successfully.")
    else:
        presentation = ResearchPresentation.objects.create(
            research=research,
            event_name=event_name,
            presentation_date=pres_date,
            award=award,
            certificate_file=certificate_file,
        )
        messages.success(request, "Presentation added successfully.")

        faculty_display_name = faculty.user.get_full_name() or faculty.user.username
        presentation_message = f"{faculty_display_name} added a new presentation \"{event_name}\" for \"{research.title}\"."

        team_recipients = _get_team_recipients(research, exclude_user=faculty.user)
        committee_recipients = _get_committee_recipients(research, exclude_user=faculty.user)
        committee_only_recipients = {
            uid: u for uid, u in committee_recipients.items()
            if uid not in team_recipients
        }

        presentation_link_team = f"{reverse('Elsa_research:research_overview', args=[uuid])}?research={research.research_id}"
        presentation_link_committee = reverse('Elsa_research:committee_research_details_view', args=[uuid, research.research_id])

        def _send_presentation_notification(recipient_user, link):
            Notification.objects.create(
                user=recipient_user,
                title="New Presentation Added",
                message=presentation_message,
                notification_type="INFO",
                link=link,
            )
            send_notification(recipient_user.id, {
                "title": "New Presentation Added",
                "message": presentation_message,
                "research_id": research.research_id,
                "event_name": event_name,
                "presentation_date": pres_date.strftime("%d %b %Y") if pres_date else "",
                "award": award,
                "certificate_url": presentation.certificate_file.url if presentation.certificate_file else "",
            }, event="presentation_created")

        for recipient_user in team_recipients.values():
            _send_presentation_notification(recipient_user, presentation_link_team)

        for recipient_user in committee_only_recipients.values():
            _send_presentation_notification(recipient_user, presentation_link_committee)       
    for f in extra_files:
        ResearchPresentationDocument.objects.create(presentation=presentation, file=f)
    if is_ajax:
        return JsonResponse({"success": True})

    return redirect(progress_url)


@login_required
@require_POST
def delete_presentation(request, uuid, presentation_id):
    faculty = FacultyProfile.objects.get(user=request.user)
    presentation = get_object_or_404(
        ResearchPresentation,
        presentation_id=presentation_id,
        research__faculty=faculty
    )
    research_id = presentation.research_id
    if presentation.certificate_file:
        presentation.certificate_file.delete()
    presentation.delete()
    messages.success(request, "Presentation deleted.")
    return redirect(f"{reverse('Elsa_research:research_presentation', args=[uuid])}?research={research_id}")

@login_required
@require_POST
def delete_presentation_document(request, uuid, document_id):
    faculty = FacultyProfile.objects.get(user=request.user)
    doc = get_object_or_404(
        ResearchPresentationDocument,
        document_id=document_id,
        presentation__research__faculty=faculty
    )
    doc.file.delete()
    doc.delete()
    messages.success(request, "File removed.")
    return redirect(request.META.get("HTTP_REFERER", reverse("Elsa_research:research_presentation", args=[uuid])))

@login_required
def committee_research_details(request, uuid):
    faculty = request.user.faculty_profile
    if not faculty.is_research_committee_member:
        messages.error(
            request,
            "You do not have permission to access this page."
        )
        return redirect("faculty_dashboard", uuid=uuid)

    researches = ResearchOpportunity.objects.select_related(
        "faculty", "faculty__user", "department"
    ).order_by("-created_at")

    department_filter = request.GET.get("department", "all")
    mentor_filter = request.GET.get("mentor", "all")
    status_filter = request.GET.get("status", "all")

    if department_filter != "all":
        researches = researches.filter(department_id=department_filter)
    if mentor_filter != "all":
        researches = researches.filter(faculty_id=mentor_filter)
    if status_filter != "all":
        researches = researches.filter(project_status=status_filter)

    total_projects = researches.count()
    total_estimated_amount = (
        researches.aggregate(total=Sum("estimated_amount"))["total"] or Decimal("0.00")
    ).quantize(Decimal("0.01"))
    total_ongoing = researches.filter(project_status="ONGOING").count()
    total_completed = researches.filter(project_status="COMPLETED").count()

    paginator = Paginator(researches, 10)
    page_number = request.GET.get("page")
    research_list = paginator.get_page(page_number)

    departments = Department.objects.all().order_by("department_name")
    mentors = FacultyProfile.objects.filter(
        research_opportunities__isnull=False
    ).select_related("user").distinct().order_by("user__first_name")

    context = {
        "uuid": uuid,
        "researches": research_list,
        "total_projects": total_projects,
        "total_estimated_amount": total_estimated_amount,
        "total_ongoing": total_ongoing,
        "total_completed": total_completed,
        "departments": departments,
        "mentors": mentors,
        "status_choices": ResearchOpportunity.PROJECT_STATUS_CHOICES,
        "context_filters": {
            "department": department_filter,
            "mentor": mentor_filter,
            "status": status_filter,
        },
    }
    return render(
        request,
        "faculty_research/committee_research_details.html",
        context
    )


@login_required
def committee_research_details_view(request, uuid, research_id):
    faculty = request.user.faculty_profile
    if not faculty.is_research_committee_member:
        messages.error(
            request,
            "You do not have permission to access this page."
        )
        return redirect("faculty_dashboard", uuid=uuid)

    research = get_object_or_404(
        ResearchOpportunity.objects.select_related("faculty", "faculty__user", "department"),
        research_id=research_id
    )

    milestones = research.milestones.prefetch_related(
        "student_assignments__student__user"
    ).order_by("deadline")
    total_milestones = milestones.count()
    completed_milestones = milestones.filter(status="completed").count()

    assignments = StudentMilestoneAssignment.objects.filter(milestone__research=research)
    overall_progress = round(
        assignments.aggregate(Avg("student_progress"))["student_progress__avg"] or 0
    )

    team = ResearchTeam.objects.filter(research_details=research).first()
    team_members = []
    student_member_count = 0
    faculty_member_count = 0
    if team:
        team_members = team.member.select_related("faculty__user", "student__user").all()
        student_member_count = sum(1 for m in team_members if m.role == "STUDENT")
        faculty_member_count = sum(1 for m in team_members if m.faculty_id)

    fundings = ResearchFunding.objects.filter(research=research).order_by("-award_date")
    total_funding_amount = (
        fundings.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    ).quantize(Decimal("0.01"))

    presentations = ResearchPresentation.objects.filter(
        research=research
    ).prefetch_related("documents").order_by("-presentation_date")
    total_presentations = presentations.count()
    total_awards = presentations.exclude(award__isnull=True).exclude(award__exact="").count()

    days_remaining = None
    if research.end_date:
        days_remaining = (research.end_date - timezone.now().date()).days

    current_phase = "Not Started"
    in_progress_milestone = milestones.filter(status="in_progress").order_by("-deadline").first()
    if in_progress_milestone:
        current_phase = in_progress_milestone.title
    elif completed_milestones and completed_milestones == total_milestones and total_milestones > 0:
        current_phase = "Completed"

    context = {
        "uuid": uuid,
        "research": research,
        "milestones": milestones,
        "total_milestones": total_milestones,
        "completed_milestones": completed_milestones,
        "overall_progress": overall_progress,
        "team": team,
        "team_members": team_members,
        "student_member_count": student_member_count,
        "faculty_member_count": faculty_member_count,
        "fundings": fundings,
        "total_funding_amount": total_funding_amount,
        "presentations": presentations,
        "total_presentations": total_presentations,
        "total_awards": total_awards,
        "days_remaining": days_remaining,
        "current_phase": current_phase,
    }
    return render(
        request,
        "faculty_research/committee_research_details_view.html",
        context
    )


@login_required
def committee_research_details(request, uuid):
    faculty = request.user.faculty_profile
    if not faculty.is_research_committee_member:
        messages.error(
            request,
            "You do not have permission to access this page."
        )
        return redirect("faculty_dashboard", uuid=uuid)

    researches = ResearchOpportunity.objects.select_related(
        "faculty", "faculty__user", "department"
    ).order_by("-created_at")

    research_id = request.GET.get("research")
    if research_id:
        research = get_object_or_404(ResearchOpportunity, research_id=research_id)
    else:
        research = researches.first()

    milestones = ResearchMilestone.objects.none()
    team = None
    team_members = []
    student_member_count = 0
    faculty_member_count = 0
    fundings = ResearchFunding.objects.none()
    total_funding_amount = Decimal("0.00")
    presentations = ResearchPresentation.objects.none()
    total_presentations = 0
    total_awards = 0
    total_milestones = 0
    completed_milestones = 0
    overall_progress = 0
    days_remaining = None
    current_phase = "Not Started"

    if research:
        milestones = research.milestones.prefetch_related(
            "student_assignments__student__user"
        ).order_by("deadline")
        total_milestones = milestones.count()
        completed_milestones = milestones.filter(status="completed").count()

        assignments = StudentMilestoneAssignment.objects.filter(
            milestone__research=research
        )
        overall_progress = round(
            assignments.aggregate(Avg("student_progress"))["student_progress__avg"] or 0
        )

        team = ResearchTeam.objects.filter(research_details=research).first()
        if team:
            team_members = team.member.select_related(
                "faculty__user", "student__user"
            ).all()
            student_member_count = sum(1 for m in team_members if m.role == "STUDENT")
            faculty_member_count = sum(1 for m in team_members if m.faculty_id)

        fundings = ResearchFunding.objects.filter(
            research=research
        ).order_by("-award_date")
        total_funding_amount = (
            fundings.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        ).quantize(Decimal("0.01"))

        presentations = ResearchPresentation.objects.filter(
            research=research
        ).prefetch_related("documents").order_by("-presentation_date")
        total_presentations = presentations.count()
        total_awards = presentations.exclude(award__isnull=True).exclude(award__exact="").count()

        if research.end_date:
            days_remaining = (research.end_date - timezone.now().date()).days

        in_progress_milestone = milestones.filter(status="in_progress").order_by("-deadline").first()
        if in_progress_milestone:
            current_phase = in_progress_milestone.title
        elif completed_milestones and completed_milestones == total_milestones and total_milestones > 0:
            current_phase = "Completed"

    context = {
        "uuid": uuid,
        "researches": researches,
        "research": research,
        "milestones": milestones,
        "total_milestones": total_milestones,
        "completed_milestones": completed_milestones,
        "overall_progress": overall_progress,
        "team": team,
        "team_members": team_members,
        "student_member_count": student_member_count,
        "faculty_member_count": faculty_member_count,
        "fundings": fundings,
        "total_funding_amount": total_funding_amount,
        "presentations": presentations,
        "total_presentations": total_presentations,
        "total_awards": total_awards,
        "days_remaining": days_remaining,
        "current_phase": current_phase,
    }
    return render(
        request,
        "faculty_research/committee_research_details.html",
        context
    )

@login_required
def research_overview(request, uuid):
    faculty = request.user.faculty_profile

    is_team_member = ResearchTeamMember.objects.filter(
        faculty=faculty,
        role__in=["ADVISOR", "CO_MENTOR"]
    ).exists()

    if not is_team_member:
        messages.error(
            request,
            "You do not have permission to access this page."
        )
        return redirect("faculty_dashboard", uuid=uuid)

    researches = ResearchOpportunity.objects.filter(
        research_teams__member__faculty=faculty,
        research_teams__member__role__in=["ADVISOR", "CO_MENTOR"]
    ).select_related(
        "faculty", "faculty__user", "department"
    ).distinct().order_by("-created_at")

    research_id = request.GET.get("research")
    if research_id:
        research = get_object_or_404(
            ResearchOpportunity,
            research_id=research_id,
            research_teams__member__faculty=faculty,
            research_teams__member__role__in=["ADVISOR", "CO_MENTOR"]
        )
    else:
        research = researches.first()

    milestones = ResearchMilestone.objects.none()
    team = None
    team_members = []
    student_member_count = 0
    faculty_member_count = 0
    fundings = ResearchFunding.objects.none()
    total_funding_amount = Decimal("0.00")
    presentations = ResearchPresentation.objects.none()
    total_presentations = 0
    total_awards = 0
    total_milestones = 0
    completed_milestones = 0
    overall_progress = 0
    days_remaining = None
    current_phase = "Not Started"

    if research:
        milestones = research.milestones.prefetch_related(
            "student_assignments__student__user"
        ).order_by("deadline")
        total_milestones = milestones.count()
        completed_milestones = milestones.filter(status="completed").count()

        assignments = StudentMilestoneAssignment.objects.filter(
            milestone__research=research
        )
        overall_progress = round(
            assignments.aggregate(Avg("student_progress"))["student_progress__avg"] or 0
        )

        team = ResearchTeam.objects.filter(research_details=research).first()
        if team:
            team_members = team.member.select_related(
                "faculty__user", "student__user"
            ).all()
            student_member_count = sum(1 for m in team_members if m.role == "STUDENT")
            faculty_member_count = sum(1 for m in team_members if m.faculty_id)

        fundings = ResearchFunding.objects.filter(
            research=research
        ).order_by("-award_date")
        total_funding_amount = (
            fundings.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        ).quantize(Decimal("0.01"))

        presentations = ResearchPresentation.objects.filter(
            research=research
        ).prefetch_related("documents").order_by("-presentation_date")
        total_presentations = presentations.count()
        total_awards = presentations.exclude(award__isnull=True).exclude(award__exact="").count()

        if research.end_date:
            days_remaining = (research.end_date - timezone.now().date()).days

        in_progress_milestone = milestones.filter(status="in_progress").order_by("-deadline").first()
        if in_progress_milestone:
            current_phase = in_progress_milestone.title
        elif completed_milestones and completed_milestones == total_milestones and total_milestones > 0:
            current_phase = "Completed"

    context = {
        "uuid": uuid,
        "researches": researches,
        "research": research,
        "milestones": milestones,
        "total_milestones": total_milestones,
        "completed_milestones": completed_milestones,
        "overall_progress": overall_progress,
        "team": team,
        "team_members": team_members,
        "student_member_count": student_member_count,
        "faculty_member_count": faculty_member_count,
        "fundings": fundings,
        "total_funding_amount": total_funding_amount,
        "presentations": presentations,
        "total_presentations": total_presentations,
        "total_awards": total_awards,
        "days_remaining": days_remaining,
        "current_phase": current_phase,
    }
    return render(
        request,
        "faculty_research/research_overview.html",
        context
    )

@login_required
def research_overview(request, uuid):
    faculty = request.user.faculty_profile

    is_team_member = ResearchTeamMember.objects.filter(
        faculty=faculty,
        role__in=[
            ResearchTeamMember.ROLE_ADVISOR,
            ResearchTeamMember.ROLE_CO_MENTOR,
        ],
    ).exists()
    print("FACULTY:", faculty)
    print("IS TEAM MEMBER:", is_team_member)
    if not is_team_member:
        messages.error(
            request,
            "You do not have permission to access this page."
        )
        return redirect("faculty_dashboard", uuid=uuid)

    researches = ResearchOpportunity.objects.filter(
        research_teams__member__faculty=faculty
    ).select_related(
        "faculty", "faculty__user", "department"
    ).distinct().order_by("-created_at")

    research_id = request.GET.get("research")
    if research_id:
        research = get_object_or_404(
            ResearchOpportunity,
            research_id=research_id,
            research_teams__member__faculty=faculty
        )
    else:
        research = researches.first()

    milestones = ResearchMilestone.objects.none()
    team = None
    team_members = []
    student_member_count = 0
    faculty_member_count = 0
    fundings = ResearchFunding.objects.none()
    total_funding_amount = Decimal("0.00")
    presentations = ResearchPresentation.objects.none()
    total_presentations = 0
    total_awards = 0
    total_milestones = 0
    completed_milestones = 0
    overall_progress = 0
    days_remaining = None
    current_phase = "Not Started"

    if research:
        milestones = research.milestones.prefetch_related(
            "student_assignments__student__user"
        ).order_by("deadline")
        total_milestones = milestones.count()
        completed_milestones = milestones.filter(status="completed").count()

        assignments = StudentMilestoneAssignment.objects.filter(
            milestone__research=research
        )
        overall_progress = round(
            assignments.aggregate(Avg("student_progress"))["student_progress__avg"] or 0
        )

        team = ResearchTeam.objects.filter(research_details=research).first()
        if team:
            team_members = team.member.select_related(
                "faculty__user", "student__user"
            ).all()
            student_member_count = sum(1 for m in team_members if m.role == "STUDENT")
            faculty_member_count = sum(1 for m in team_members if m.faculty_id)

        fundings = ResearchFunding.objects.filter(
            research=research
        ).order_by("-award_date")
        total_funding_amount = (
            fundings.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        ).quantize(Decimal("0.01"))

        presentations = ResearchPresentation.objects.filter(
            research=research
        ).prefetch_related("documents").order_by("-presentation_date")
        total_presentations = presentations.count()
        total_awards = presentations.exclude(award__isnull=True).exclude(award__exact="").count()

        if research.end_date:
            days_remaining = (research.end_date - timezone.now().date()).days

        in_progress_milestone = milestones.filter(status="in_progress").order_by("-deadline").first()
        if in_progress_milestone:
            current_phase = in_progress_milestone.title
        elif completed_milestones and completed_milestones == total_milestones and total_milestones > 0:
            current_phase = "Completed"

    context = {
        "uuid": uuid,
        "is_research_team_member": is_team_member,
        "researches": researches,
        "research": research,
        "milestones": milestones,
        "total_milestones": total_milestones,
        "completed_milestones": completed_milestones,
        "overall_progress": overall_progress,
        "team": team,
        "team_members": team_members,
        "student_member_count": student_member_count,
        "faculty_member_count": faculty_member_count,
        "fundings": fundings,
        "total_funding_amount": total_funding_amount,
        "presentations": presentations,
        "total_presentations": total_presentations,
        "total_awards": total_awards,
        "days_remaining": days_remaining,
        "current_phase": current_phase,
    }
    return render(
        request,
        "faculty_research/research_overview.html",
        context
    )

@login_required
def committee_research_details(request, uuid):
    faculty = request.user.faculty_profile
    if not faculty.is_research_committee_member:
        messages.error(
            request,
            "You do not have permission to access this page."
        )
        return redirect("faculty_dashboard", uuid=uuid)

    researches = ResearchOpportunity.objects.select_related(
        "faculty", "faculty__user", "department"
    ).order_by("-created_at")
    print("Initial count:", researches.count())

    department_filter = request.GET.get("department") or "all"
    mentor_filter = request.GET.get("mentor") or "all"
    status_filter = request.GET.get("status") or "all"

    if department_filter != "all":
        researches = researches.filter(department_id=department_filter)
 
    if mentor_filter != "all":
        researches = researches.filter(faculty_id=mentor_filter)
  
    if status_filter != "all":
        researches = researches.filter(project_status=status_filter)

    total_projects = researches.count()
    total_estimated_amount = (
        researches.aggregate(total=Sum("estimated_amount"))["total"] or Decimal("0.00")
    ).quantize(Decimal("0.01"))
    total_ongoing = researches.filter(project_status="ONGOING").count()
    total_completed = researches.filter(project_status="COMPLETED").count()

    paginator = Paginator(researches, 10)
    page_number = request.GET.get("page")
    research_list = paginator.get_page(page_number)
  
    for r in research_list:
        print(r.research_id, r.title, r.department_id)
    departments = Department.objects.all().order_by("department_name")
    mentors = FacultyProfile.objects.filter(
        research_opportunities__isnull=False
    ).select_related("user").distinct().order_by("user__first_name")

    context = {
        "uuid": uuid,
        "researches": research_list,
        "total_projects": total_projects,
        "total_estimated_amount": total_estimated_amount,
        "total_ongoing": total_ongoing,
        "total_completed": total_completed,
        "departments": departments,
        "mentors": mentors,
        "status_choices": ResearchOpportunity.PROJECT_STATUS_CHOICES,
        "context_filters": {
            "department": department_filter,
            "mentor": mentor_filter,
            "status": status_filter,
        },
    }
    return render(
        request,
        "faculty_research/committee_research_details.html",
        context
    )


@login_required
def committee_research_details_view(request, uuid, research_id):
    faculty = request.user.faculty_profile
    if not faculty.is_research_committee_member:
        messages.error(
            request,
            "You do not have permission to access this page."
        )
        return redirect("faculty_dashboard", uuid=uuid)

    research = get_object_or_404(
        ResearchOpportunity.objects.select_related("faculty", "faculty__user", "department"),
        research_id=research_id
    )

    milestones = research.milestones.prefetch_related(
        "student_assignments__student__user"
    ).order_by("deadline")
    total_milestones = milestones.count()
    completed_milestones = milestones.filter(status="completed").count()

    assignments = StudentMilestoneAssignment.objects.filter(milestone__research=research)
    overall_progress = round(
        assignments.aggregate(Avg("student_progress"))["student_progress__avg"] or 0
    )

    team = ResearchTeam.objects.filter(research_details=research).first()
    team_members = []
    student_member_count = 0
    faculty_member_count = 0
    if team:
        team_members = team.member.select_related("faculty__user", "student__user").all()
        student_member_count = sum(1 for m in team_members if m.role == "STUDENT")
        faculty_member_count = sum(1 for m in team_members if m.faculty_id)

    fundings = ResearchFunding.objects.filter(research=research).order_by("-award_date")
    total_funding_amount = (
        fundings.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    ).quantize(Decimal("0.01"))

    presentations = ResearchPresentation.objects.filter(
        research=research
    ).prefetch_related("documents").order_by("-presentation_date")
    total_presentations = presentations.count()
    total_awards = presentations.exclude(award__isnull=True).exclude(award__exact="").count()

    days_remaining = None
    if research.end_date:
        days_remaining = (research.end_date - timezone.now().date()).days

    current_phase = "Not Started"
    in_progress_milestone = milestones.filter(status="in_progress").order_by("-deadline").first()
    if in_progress_milestone:
        current_phase = in_progress_milestone.title
    elif completed_milestones and completed_milestones == total_milestones and total_milestones > 0:
        current_phase = "Completed"

    context = {
        "uuid": uuid,
        "research": research,
        "milestones": milestones,
        "total_milestones": total_milestones,
        "completed_milestones": completed_milestones,
        "overall_progress": overall_progress,
        "team": team,
        "team_members": team_members,
        "student_member_count": student_member_count,
        "faculty_member_count": faculty_member_count,
        "fundings": fundings,
        "total_funding_amount": total_funding_amount,
        "presentations": presentations,
        "total_presentations": total_presentations,
        "total_awards": total_awards,
        "days_remaining": days_remaining,
        "current_phase": current_phase,
    }
    return render(
        request,
        "faculty_research/committee_research_details_view.html",
        context
    )

# ====== STUDENT RESEARCH =======================================================================================================================
@login_required
def student_research_opportunity(request, uuid):
    opportunities = (
        ResearchOpportunity.objects.filter(status="OPEN")
        .select_related("faculty", "faculty__department", "faculty__user")
        .order_by("-created_at")
    )
    # ------------------ Filters ------------------
    search = request.GET.get("search")
    department = request.GET.get("department")
    faculty = request.GET.get("faculty")
    deadline = request.GET.get("deadline")
    if search:
        opportunities = opportunities.filter(
            Q(title__icontains=search) |
            Q(short_description__icontains=search) |
            Q(required_skills__icontains=search)
        )
    if department:
        opportunities = opportunities.filter(
            faculty__department_id=department
        )
    if faculty:
        opportunities = opportunities.filter(
            faculty_id=faculty
        )
    if deadline:
        last_date = timezone.now().date() + timedelta(days=int(deadline))
        opportunities = opportunities.filter(
            application_deadline__gte=timezone.now().date(),
            application_deadline__lte=last_date
        )
    paginator = Paginator(opportunities, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    # ---------------------------------------------
    departments = Department.objects.all()
    mentors = (
        FacultyProfile.objects.filter(
            research_opportunities__status="OPEN"
        )
        .select_related("user")
        .distinct()
        .order_by("user__first_name")
    )
    context = {
        "uuid": uuid,
        "page_obj": page_obj,
        "opportunities": opportunities,
        "departments": departments,
        "mentors": mentors,
    }
    return render(
        request,
        "student_research/student_research_opportunity.html",
        context,
    )


@login_required
def student_research_progress(request, uuid):
    student = get_object_or_404( StudentProfile,user=request.user)
    researches = ResearchOpportunity.objects.filter(
        research_teams__member__student=student,
        research_teams__member__role="STUDENT"
    ).distinct()
    research_id = request.GET.get("research_id")
    research = None
    assignments = []
    reports = []
    feedback_reports = []
    revision_reports = []
    overall_progress = 0
    completed_count = 0
    total_milestones = 0

    team = None
    team_members = []
    student_member_count = 0
    faculty_member_count = 0
    days_remaining = None
    current_phase = "Not Started"
    if research_id:
        research = get_object_or_404(
            ResearchOpportunity,
            research_id=research_id
        )

        assigned = ResearchTeamMember.objects.filter(
            team__research_details=research,
            student=student,
            role="STUDENT"
        ).exists()

        if not assigned:
            messages.error(request, "You are not assigned to this research.")
            return redirect("Elsa_research:student_research_progress", uuid=uuid)

        assignments = StudentMilestoneAssignment.objects.filter(
            student=student,
            milestone__research=research
        ).select_related("milestone")

        reports = StudentProgressReport.objects.filter(
            assignment__student=student,
            assignment__milestone__research=research
        ).select_related(
            "assignment__milestone"
        ).prefetch_related(
            "attachments"
        ).order_by("-submitted_date")

        latest_report_by_assignment = {}
        for r in reports:
            if r.assignment_id not in latest_report_by_assignment:
                latest_report_by_assignment[r.assignment_id] = r.report_id

        revision_reports = [r for r in reports if r.status == "revision"]

        feedback_reports = []
        for r in reports:
            if r.faculty_feedback:
                r.is_latest_for_assignment = (
                    latest_report_by_assignment.get(r.assignment_id) == r.report_id
                )
                feedback_reports.append(r)
        total_milestones = assignments.count()
        completed_count = assignments.filter(milestone__status="completed").count()

        if assignments.exists():
            total = sum(item.student_progress for item in assignments)
            overall_progress = round(total / assignments.count())

        # ---- Team info ----
        team = ResearchTeam.objects.filter(research_details=research).first()
        if team:
            team_members = team.member.select_related(
                "faculty__user", "student__user"
            ).all()
            student_member_count = sum(1 for m in team_members if m.role == "STUDENT")
            faculty_member_count = sum(1 for m in team_members if m.faculty_id)

        # ---- Timeline ----
        if research.end_date:
            days_remaining = (research.end_date - timezone.now().date()).days

        project_milestones = research.milestones.all()
        in_progress_milestone = project_milestones.filter(
            status="in_progress"
        ).order_by("-deadline").first()
        completed_project_milestones = project_milestones.filter(status="completed").count()
        total_project_milestones = project_milestones.count()

        if in_progress_milestone:
            current_phase = in_progress_milestone.title
        elif completed_project_milestones and completed_project_milestones == total_project_milestones and total_project_milestones > 0:
            current_phase = "Completed"

    context = {
        "uuid": uuid,
        "researches": researches,
        "research": research,
        "assignments": assignments,
        "reports": reports,
        "revision_reports": revision_reports,
        "feedback_reports": feedback_reports,
        "overall_progress": overall_progress,
        "completed_count": completed_count,
        "total_milestones": total_milestones,
        "team": team,
        "team_members": team_members,
        "student_member_count": student_member_count,
        "faculty_member_count": faculty_member_count,
        "days_remaining": days_remaining,
        "current_phase": current_phase,
    }
    return render(
        request,
        "student_research/student_research_progress.html",
        context
    )

def student_progress_tab(request):
    research_id = request.GET.get("research_id")
    tab = request.GET.get("tab")
    if tab == "reports":
        reports = StudentProgressReport.objects.filter(
            assignment__student=request.user.studentprofile,
            assignment__milestone__research_id=research_id
        ).prefetch_related("attachments")
        data = []
        for report in reports:
            data.append({
                "title": report.title,
                "milestone": report.assignment.milestone.title,
                "status": report.get_status_display(),
                "progress": report.progress_percentage,
                "date": report.submitted_date.strftime("%d %b %Y"),
                "attachments": [
                    {
                        "name": a.file.name,
                        "url": a.file.url
                    }
                    for a in report.attachments.all()
                ]
            })
        return JsonResponse({
            "reports": data
        })



@login_required
def submit_student_report(request, uuid, assignment_id):
    student = get_object_or_404(
        StudentProfile,
        user=request.user
    )
    assignment = get_object_or_404(
        StudentMilestoneAssignment,
        assignment_id=assignment_id,
        student=student
    )
    research_id = assignment.milestone.research_id
    progress_url = f"{reverse('Elsa_research:student_research_progress', args=[uuid])}?research_id={research_id}"
    # ---------- Block submissions ONLY when the milestone itself is completed ----------
    if assignment.milestone.status == "completed":
        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
        if is_ajax:
            return JsonResponse({
                "success": False,
                "message": "This milestone is already completed. Reports can no longer be submitted."
            }, status=400)
        messages.error(request, "This milestone is already completed. You can't submit a report for it.")
        return redirect(progress_url)    
    if request.method != "POST":
        return redirect(progress_url)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    title = request.POST.get("title", "").strip()
    description = request.POST.get("description", "").strip()
    progress_percentage = request.POST.get("progress_percentage", "").strip()
    files = request.FILES.getlist("files")
    errors = {}

    if not title:
        errors["title"] = "Report title is required."
    elif len(title) < 3:
        errors["title"] = "Minimum 3 characters."
    elif len(title) > 255:
        errors["title"] = "Maximum 255 characters."

    if not description:
        errors["description"] = "Description is required."

    try:
        progress_value = int(progress_percentage or -1)
        if progress_value < 0 or progress_value > 100:
            errors["progress_percentage"] = "Must be between 0 and 100."
    except ValueError:
        errors["progress_percentage"] = "Enter a valid number."
        progress_value = None

    allowed_extensions = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip"]
    standard_max_size = 20 * 1024 * 1024
    zip_max_size = 500 * 1024 * 1024

    if not files:
        errors["files"] = "Please upload at least one file."
    else:
        for f in files:
            ext = os.path.splitext(f.name)[1].lower()
            if ext not in allowed_extensions:
                errors["files"] = f"{f.name}: only PDF, DOC, DOCX, XLS, XLSX, and ZIP files are allowed."
                break
            max_size = zip_max_size if ext == ".zip" else standard_max_size
            if f.size > max_size:
                limit_label = "500MB" if ext == ".zip" else "20MB"
                errors["files"] = f"{f.name} exceeds the {limit_label} size limit."
                break

    if errors:
        if is_ajax:
            return JsonResponse({"success": False, "errors": errors}, status=400)
        for msg in errors.values():
            messages.error(request, msg)
        return redirect(progress_url)

    # ---------- Save ----------
    report = StudentProgressReport.objects.create(
        assignment=assignment,
        title=title,
        description=description,
        progress_percentage=progress_value,
        status="submitted"
    )
    for uploaded_file in files:
        StudentReportAttachment.objects.create(report=report, file=uploaded_file)

    assignment.status = "submitted"
    assignment.save()
 
    research = assignment.milestone.research
    faculty_user = research.faculty.user
    student_display_name = student.user.get_full_name() or student.user.username
    faculty_link = f"{reverse('Elsa_research:research_progress', args=[uuid])}?research={research.research_id}"
    report_message = f"{student_display_name} submitted a report for \"{assignment.milestone.title}\"."
 
    first_attachment = report.attachments.first()
 
    Notification.objects.create(
        user=faculty_user,
        title="New Report Submitted",
        message=report_message,
        notification_type="INFO",
        link=faculty_link,
    )
    send_notification(faculty_user.id, {
        "title": "New Report Submitted",
        "message": report_message,
        "research_id": research.research_id,
        "report_id": report.report_id,
        "student_name": student_display_name,
        "milestone_title": assignment.milestone.title,
        "report_title": report.title,
        "attachment_url": first_attachment.file.url if first_attachment else "",
        "attachment_name": first_attachment.file.name.split("/")[-1] if first_attachment else "",
        "approve_url": reverse('Elsa_research:review_student_report', kwargs={'uuid': uuid, 'report_id': report.report_id}),
    }, event="report_submitted")
 
    messages.success(request, "Report submitted successfully.")

    if is_ajax:
            return JsonResponse({
                "success": True,
                "assignment": {
                    "assignment_id": assignment.assignment_id,
                    "status": assignment.status,
                    "status_display": assignment.get_status_display(),
                },
                "report": {
                    "report_id": report.report_id,
                    "title": report.title,
                    "milestone_title": assignment.milestone.title,
                    "description": report.description,          # <-- add this
                    "status": report.status,
                    "status_display": report.get_status_display(),
                    "submitted_date": report.submitted_date.strftime("%d %b %Y"),
                    "progress": report.progress_percentage,
                    "attachments": [
                        {"name": a.file.name.split("/")[-1], "url": a.file.url}
                        for a in report.attachments.all()
                    ],
                }
            })

    
@login_required
@require_POST
def start_milestone_work(request, uuid, assignment_id):
    student = get_object_or_404(StudentProfile, user=request.user)
    assignment = get_object_or_404(
        StudentMilestoneAssignment,
        assignment_id=assignment_id,
        student=student
    )
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    if assignment.status == "assigned" and assignment.milestone.status == "in_progress":
        assignment.status = "working"
        assignment.save()
 
        research = assignment.milestone.research
        faculty_user = research.faculty.user
        student_display_name = student.user.get_full_name() or student.user.username
        faculty_link = f"{reverse('Elsa_research:research_progress', args=[uuid])}?research={research.research_id}"
        message = f"{student_display_name} started working on \"{assignment.milestone.title}\"."
 
        Notification.objects.create(
            user=faculty_user,
            title="Student Started Milestone",
            message=message,
            notification_type="INFO",
            link=faculty_link,
        )
 
        assignments_qs = StudentMilestoneAssignment.objects.filter(
            student=student, milestone__research=research
        ).select_related("milestone")
        total = assignments_qs.count()
        avg_progress = round(sum(a.student_progress for a in assignments_qs) / total) if total else 0
        statuses = [a.status for a in assignments_qs]
        all_completed = bool(statuses) and all(s == "completed" for s in statuses)
        has_started = any(s != "assigned" for s in statuses)
        try:
            academic = StudentAcademicProfile.objects.select_related("department").get(student=student)
            department_name = academic.department.department_name if academic.department else "No Department"
        except StudentAcademicProfile.DoesNotExist:
            department_name = "No Department"
 
        student_summary = {
            "student_id": student.pk,
            "name": student_display_name,
            "department_name": department_name,
            "average_progress": avg_progress,
            "all_completed": all_completed,
            "has_started": has_started,
            "milestones": [
                {"milestone_id": a.milestone_id, "title": a.milestone.title}
                for a in assignments_qs
            ],
        }
 
        send_notification(faculty_user.id, {
            "title": "Student Started Milestone",
            "message": message,
            "research_id": research.research_id,
            "students_update": [student_summary],
        }, event="milestone_started")
    elif is_ajax and not (assignment.status == "assigned" and assignment.milestone.status == "in_progress"):
        return JsonResponse({
            "success": False,
            "message": "This milestone hasn't been started by your mentor yet."
        }, status=400)
 
    if is_ajax:
        return JsonResponse({
            "success": True,
            "assignment": {
                "assignment_id": assignment.assignment_id,
                "status": assignment.status,
                "status_display": assignment.get_status_display(),
            }
        })
    progress_url = (
        f"{reverse('Elsa_research:student_research_progress', args=[uuid])}"
        f"?research_id={assignment.milestone.research_id}"
    )
    return redirect(progress_url)  


@login_required
def view_research(request, research_id, uuid):  
    opportunity = get_object_or_404(
        ResearchOpportunity,
        research_id=research_id,
        status="OPEN"
    )
    faculty = opportunity.faculty    
    documents = ResearchOpportunityDocument.objects.filter(
        opportunity=opportunity
    )
    department = faculty.department      
    context = {
        "uuid": uuid,
        "opportunity": opportunity,
        "documents": documents,
        "faculty":faculty,
        "department":department,        
    }
    return render(
        request,
        "student_research/view_research.html",
        context
    )


# ======================== Jordan code Start's Here ========================
# Research/Elsa_research/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from Research.models import StudentResearchApplication, ResearchOpportunity, ResearchOpportunityDocument
from Research.Elsa_research.forms import StudentResearchApplicationForm
from Students.models import StudentProfile, StudentAcademicProfile


@login_required
def view_application(request, research_id, uuid):
    """
    View for student research application
    URL: student_research_opportunity/research_application/<str:research_id>/<uuid:uuid>/
    """
    try:
        research_id_int = str(research_id)
    except (ValueError, TypeError):
        messages.error(request, 'Invalid research ID.')
        return redirect('Elsa_research:student_research_opportunity', uuid=uuid)
    
    # Get the research opportunity
    opportunity = get_object_or_404(
        ResearchOpportunity,
        research_id=research_id_int,
        status="OPEN"
    )
    
    # Get student profile
    try:
        student = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('Elsa_research:student_research_opportunity', uuid=uuid)
    
    # Check for existing application
    existing_application = StudentResearchApplication.objects.filter(
        student=student,
        research_opportunity=opportunity
    ).order_by('-created_at').first()
    
    # Get academic info
    try:
        academic_info = StudentAcademicProfile.objects.get(student=student)
        department_name = academic_info.department.department_name if academic_info.department else None
        program_name = academic_info.program.program_name if academic_info.program else None
    except StudentAcademicProfile.DoesNotExist:
        department_name = None
        program_name = None
    
    # Check if application was just submitted (success flag)
    success = request.GET.get('success', False)
    
    # If application exists and is submitted, show read-only view
    if existing_application and existing_application.is_submitted():
        context = {
            'uuid': uuid,
            'opportunity': opportunity,
            'student': student,
            'application': existing_application,
            'department_name': department_name,
            'program_name': program_name,
            'is_readonly': True,
            'show_success': success,
            'research_id': research_id,
            'phone': student.user.mobile_number,
        }
        return render(request, 'student_research/application.html', context)
    
    # Handle form submission
    if request.method == 'POST':
        form = StudentResearchApplicationForm(
            request.POST,
            request.FILES,
            student=student,
            research_opportunity=opportunity
        )
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create or update application
                    if existing_application and existing_application.status == 'draft':
                        application = existing_application
                    else:
                        application = StudentResearchApplication(
                            student=student,
                            research_opportunity=opportunity
                        )
                    
                    # Update fields from form
                    for field in ['motivation', 'skills_contribution', 'prior_experience',
                                  'time_commitment', 'availability', 'additional_info']:
                        setattr(application, field, form.cleaned_data[field])
                    
                    # Handle file uploads
                    if 'resume' in request.FILES:
                        application.resume = request.FILES['resume']
                    if 'statement_of_interest' in request.FILES:
                        application.statement_of_interest = request.FILES['statement_of_interest']
                    if 'academic_transcript' in request.FILES:
                        application.academic_transcript = request.FILES['academic_transcript']
                    
                    # Submit the application
                    application.submit()
                    application.save()
                    
                    messages.success(request, 'Your application has been submitted successfully!')
                    
                    # Redirect back to the application page with success flag
                    redirect_url = reverse('Elsa_research:research_student_application', kwargs={
                        'research_id': research_id,
                        'uuid': uuid
                    })
                    return redirect(f'{redirect_url}?success=true')
                    
            except Exception as e:
                messages.error(request, f'Error submitting application: {str(e)}')
                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Application submission error: {str(e)}')
        else:
            # Form is invalid - display all errors
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        # Field errors will be displayed in template
                        pass
            
            # Add a general error message if needed
            if form.non_field_errors():
                for error in form.non_field_errors():
                    messages.error(request, error)
    
    else:
        # GET request - initialize form
        if existing_application and existing_application.status == 'draft':
            form = StudentResearchApplicationForm(
                instance=existing_application,
                student=student,
                research_opportunity=opportunity
            )
        else:
            form = StudentResearchApplicationForm(
                student=student,
                research_opportunity=opportunity
            )
    
    # Get documents
    documents = ResearchOpportunityDocument.objects.filter(opportunity=opportunity)
    
    context = {
        "phone": student.user.mobile_number,
        'uuid': uuid,
        'opportunity': opportunity,
        'documents': documents,
        'form': form,
        'student': student,
        'department_name': department_name,
        'program_name': program_name,
        'application': existing_application,
        'is_readonly': False,
        'show_success': False,
        'research_id': research_id,
    }
    
    return render(request, 'student_research/application.html', context)


@login_required
def withdraw_application(request, application_id, uuid):
    """
    View for withdrawing an application
    """
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('Elsa_research:student_research_opportunity', uuid=uuid)
    
    application = get_object_or_404(
        StudentResearchApplication,
        application_id=application_id,
        student__user=request.user
    )
    
    # Check if application can be withdrawn
    if application.status in ['withdrawn', 'accepted', 'rejected']:
        messages.error(request, 'This application cannot be withdrawn.')
        return redirect('Elsa_research:student_research_opportunity', uuid=uuid)
    
    # Withdraw the application
    application.status = 'withdrawn'
    application.save()
    
    messages.success(request, 'Application withdrawn successfully.')
    
    return redirect('Elsa_research:student_research_opportunity', uuid=uuid)



# ======================== Jordan code End's Here ========================
