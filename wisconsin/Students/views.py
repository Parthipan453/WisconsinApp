import profile

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import StudentProfile, StudentEnrollment, Schedule, Semester , StudentHousing 
from .models import StudentAddress, StudentEmergencyContact, StudentDocument, StudentFinancialAid
from Admin.models import User
from Faculty.models import CourseGrade
from django.db import IntegrityError

from django.http import FileResponse, Http404
from django.core.files.storage import default_storage
from django.db.models import Q
import os

from Staff.models import Resource
from Staff.utils import get_resource_alerts_context, mark_resource_alerts_seen

from Admin.audit import AuditLogger

# *************************************** Arun Code ********************************************************** 

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from decimal import Decimal



from Staff.utils import notify_staff_new_leave_request







@login_required
def student_dashboard(request, uuid):

    profile, created = StudentProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "student_number": f"STU{request.user.id:06d}",
            "university_email": request.user.email,
            "current_status": "ACTIVE",
        }
    )

    current_enrollment = profile.enrollments.first()
    housing = profile.housing_records.first()
    academic = getattr(profile, "academic_profile", None)  

    total_aid = profile.financial_aids.filter(
        status="AWARDED"
    ).aggregate(total=Sum("award_amount"))["total"] or Decimal("0.00")

    context = {
        "profile": profile,
        "enrollment": current_enrollment,
        "housing": housing,
        "academic": academic,          
        "total_aid": total_aid,
    }

    return render(request, "student_dashboard.html", context)


@login_required
def student_profile(request, uuid):
    profile = request.user.student_profile
    user = request.user

    if request.method == "POST":

        # User model
        user.first_name = request.POST.get("first_name")
        user.middle_name = request.POST.get("middle_name")
        user.last_name = request.POST.get("last_name")
        user.mobile_number = request.POST.get("mobile_number")
        user.date_of_birth = request.POST.get("date_of_birth") or None
        user.gender = request.POST.get("gender")
        user.save()

        # Student Profile
        profile.preferred_name = request.POST.get("preferred_name")
        profile.personal_email = request.POST.get("personal_email")
        profile.marital_status = request.POST.get("marital_status")
        profile.citizenship_status = request.POST.get("citizenship_status")
        profile.save()

        return redirect("Student:student_profile", uuid=user.uuid)

    context = {
        "profile": profile,
        "academic": getattr(profile, "academic_profile", None),
    }

    return render(request, "Personal/profile.html", context)


# ─────────────────────────────────────────────
# personal — Address
# ─────────────────────────────────────────────

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from Students.models import StudentAddress

from django.http import JsonResponse

@login_required
def student_addresses(request, uuid):
    profile = request.user.student_profile
    
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == "POST":

        delete_address_id = request.POST.get("delete_address_id")
        if delete_address_id:
            try:
                address = get_object_or_404(
                    StudentAddress,
                    id=delete_address_id,
                    student=profile
                )
                address_type = address.get_address_type_display()
                address.delete()
                
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': f"{address_type} address deleted successfully!"
                    })
                else:
                    messages.success(request, f"{address_type} address deleted successfully!")
            except Exception as e:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': f"Error deleting address: {str(e)}"
                    })
                else:
                    messages.error(request, f"Error deleting address: {str(e)}")
            return redirect("Student:student_addresses", uuid=request.user.uuid)
        address_id = request.POST.get("address_id")
        if address_id:
            address = get_object_or_404(
                StudentAddress,
                id=address_id,
                student=profile
            )
        else:
            address = StudentAddress(student=profile)

        address.address_type = request.POST.get("address_type")
        address.address_line_1 = request.POST.get("address_line_1")
        address.address_line_2 = request.POST.get("address_line_2")
        address.city = request.POST.get("city")
        address.state = request.POST.get("state")
        address.postal_code = request.POST.get("postal_code")
        address.country = request.POST.get("country")

        address.save()

        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': "Address saved successfully!"
            })
        else:
            messages.success(request, "Address saved successfully!")

        return redirect(
            "Student:student_addresses",
            uuid=request.user.uuid
        )

    addresses = profile.addresses.all()

    return render(
        request,
        "Personal/address.html",
        {
            "addresses": addresses
        }
    )

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from Students.models import StudentEmergencyContact

@login_required
def student_emergency_contacts(request, uuid):
    profile = request.user.student_profile
    
   
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == "POST":
        
       
        delete_contact_id = request.POST.get("delete_contact_id")
        if delete_contact_id:
            try:
                contact = get_object_or_404(
                    StudentEmergencyContact,
                    id=delete_contact_id,
                    student=profile
                )
                contact_name = contact.contact_name
                contact.delete()
                
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': f"{contact_name} deleted successfully!"
                    })
                else:
                    messages.success(request, f"{contact_name} deleted successfully!")
                    return redirect("Student:student_emergency_contacts", uuid=request.user.uuid)
                    
            except Exception as e:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': f"Error deleting contact: {str(e)}"
                    })
                else:
                    messages.error(request, f"Error deleting contact: {str(e)}")
                    return redirect("Student:student_emergency_contacts", uuid=request.user.uuid)
        
       
        contact_id = request.POST.get("contact_id")
        
        if contact_id:
            contact = get_object_or_404(
                StudentEmergencyContact,
                id=contact_id,
                student=profile
            )
        else:
            contact = StudentEmergencyContact(student=profile)

        contact.contact_name = request.POST.get("contact_name")
        contact.relationship = request.POST.get("relationship")
        contact.phone_number = request.POST.get("phone_number")
        contact.email = request.POST.get("email")
        contact.priority = request.POST.get("priority")

        contact.save()
        
        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': "Emergency contact saved successfully!"
            })
        else:
            messages.success(request, "Emergency contact saved successfully!")
            return redirect("Student:student_emergency_contacts", uuid=request.user.uuid)

    contacts = profile.emergency_contacts.all().order_by("priority")

    return render(
        request,
        "Personal/emergency.html",
        {
            "contacts": contacts
        }
    )


# ─────────────────────────────────────────────
# Personal — Documents
# ─────────────────────────────────────────────

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from Students.models import StudentDocument

@login_required
def student_documents(request, uuid):
    profile = request.user.student_profile

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == "POST":
        
        # DELETE
        delete_document_id = request.POST.get("delete_document_id")
        if delete_document_id:
            try:
                document = get_object_or_404(
                    StudentDocument,
                    id=delete_document_id,
                    student=profile
                )
                doc_name = document.file_name
                
                # Delete file from storage
                if document.file:
                    document.file.delete()
                
                document.delete()
                
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': f'"{doc_name}" deleted successfully!'
                    })
                else:
                    messages.success(request, f'"{doc_name}" deleted successfully!')
                    return redirect("Student:student_documents", uuid=request.user.uuid)
                    
            except Exception as e:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': f"Error deleting document: {str(e)}"
                    })
                else:
                    messages.error(request, f"Error deleting document: {str(e)}")
                    return redirect("Student:student_documents", uuid=request.user.uuid)
        
       
        document_id = request.POST.get("document_id")
        
        if document_id:
            document = get_object_or_404(
                StudentDocument,
                id=document_id,
                student=profile
            )
        else:
            document = StudentDocument(student=profile)
            
        document.document_type = request.POST.get("document_type")
        
        if request.FILES.get("document_file"):
            uploaded_file = request.FILES["document_file"]
            # Delete old file if exists
            if document.file:
                document.file.delete()
            document.file = uploaded_file
            document.file_name = uploaded_file.name
            document.verification_status = "PENDING"
            
        document.save()
        
        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': "Document uploaded successfully!"
            })
        else:
            messages.success(request, "Document uploaded successfully!")
            return redirect("Student:student_documents", uuid=request.user.uuid)

    documents = profile.documents.all().order_by("-upload_date")
    
    return render(
        request,
        "Personal/documents.html",
        {
            "documents": documents
        }
    )

# ================================parthi update start(18.06.2026)====================================================    



# students/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from Admin.models import User
from .models import StudentProfile, StudentEnrollment, Schedule, Semester, CourseSection
from Admin.bela_admin.models import Course, Department
from Admin.Colleges.models import AcademicProgram

def get_or_create_student_profile(user):
    """Fetch the student's profile, creating one robustly if missing."""
    profile = StudentProfile.objects.filter(user=user).first()
    if profile:
        return profile, False

    email = (user.email or '').strip()
    if not email or StudentProfile.objects.filter(university_email=email).exists():
        email = f"STU{user.id:06d}@student.wisconsin.edu"

    try:
        return StudentProfile.objects.create(
            user=user,
            student_number=f"STU{user.id:06d}",
            university_email=email,
            current_status='ACTIVE',
        ), True
    except IntegrityError:
        return StudentProfile.objects.get(user=user), False

@login_required
def schedule_view(request, uuid):
    """Student schedule page"""
    user = get_object_or_404(User, uuid=uuid)
    
    student_profile, created = get_or_create_student_profile(user)
    if created:
        messages.success(request, 'Student profile created successfully!')
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    
    if not current_semester:
        current_semester = Semester.objects.order_by('-academic_year', '-start_date').first()
    #########  Rixie code start #######
    # Semester filter from query param
    semester_filter_code = request.GET.get('semester', '')
    semester_filter_obj = None
    if semester_filter_code:
        semester_filter_obj = Semester.objects.filter(semester_code=semester_filter_code).first()

    filter_kwargs = {
        'student': student_profile,
        'enrollment_status__in': ['FULL_TIME', 'PART_TIME'],
    }
    if semester_filter_obj:
        filter_kwargs['semester'] = semester_filter_obj
    enrollments = StudentEnrollment.objects.filter(
        **filter_kwargs
    ).select_related('section_id', 'section_id__course', 'semester')

    unique_semesters = StudentEnrollment.objects.filter(
        student=student_profile
    ).select_related('semester').values_list(
        'semester__semester_code', 'semester__semester_type', 'semester__academic_year'
    ).distinct()

    semester_list = []
    for code, stype, year in unique_semesters:
        if code and stype and year:
            semester_type_map = dict(Semester.SEMESTER_TYPES)
            semester_list.append({
                'code': code,
                'display': f"{code} - {semester_type_map.get(stype, stype)} {year}",
            })
    #######  Rixie code end ###########
    # Build schedule data
    schedule_items = []
    for enrollment in enrollments:
        if enrollment.section_id:
            section = enrollment.section_id
############  Rixie code start ################
            course = section.course
            sem = enrollment.semester
            sem_code = sem.semester_code if sem else ''
            sem_display = str(sem) if sem else ''
#############  Rixie code end ###########
            schedules = Schedule.objects.filter(section_id=section)
            from datetime import datetime

            for schedule in schedules:
                st = schedule.start_time
                slot_hour = int(schedule.start_time.hour)

                schedule_dates = schedule.dates or []
                if not schedule_dates:
                    schedule_dates = [None]

                for schedule_date in schedule_dates:
                    date_obj = None
                    week_number = None
                    if schedule_date:
                        try:
                            date_obj = datetime.strptime(
                                schedule_date,
                                "%Y-%m-%d"
                            ).date()
                            week_number = ((date_obj.day - 1) // 7) + 1
                        except (ValueError, TypeError):
                            date_obj = None
                            week_number = None

                    schedule_items.append({
                        'course_code': course.course_code,
                        'course_name': course.course_name,
                        'credits': course.credits,

                        'section_number': section.section_number,
                        'section_type': section.get_section_type_display(),

                        'day': schedule.day_of_week,
                        'day_display': schedule.get_day_of_week_display(),

                        'date': date_obj,
                        'week_number': week_number,

                        'start_time': schedule.start_time,
                        'end_time': schedule.end_time,
                        'slot_hour': slot_hour,

                        'room': schedule.room,
                        'building': schedule.building,
                        'is_online': schedule.is_online,

                        'instructor': section.faculty_name or "TBA",
###########  Rixie code start #########
                        'semester_code': sem_code,
                        'semester_display': sem_display,
##########  Rixie code End #############
                        'color': get_course_color(course.course_code),
                    })
    
    # Week / Month / Today filter based on ?view= & ?date= query params
    from datetime import date, timedelta

    view_mode = request.GET.get('view', 'week')
    if view_mode not in ('week', 'month', 'today'):
        view_mode = 'week'

    today = date.today()
    try:
        selected = date.fromisoformat(request.GET.get('date', ''))
    except (ValueError, TypeError):
        selected = today

    if view_mode == 'today':
        range_start = range_end = today
        filter_label = f"Today - {today.strftime('%b %d, %Y')}"
    elif view_mode == 'month':
        range_start = selected.replace(day=1)
        range_end = (range_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        filter_label = range_start.strftime('%B %Y')
    else:
        range_start = selected - timedelta(days=selected.weekday())
        range_end = range_start + timedelta(days=6)
        filter_label = f"Week of {range_start.strftime('%b %d')} - {range_end.strftime('%b %d, %Y')}"

    today_code = today.strftime('%A')[:3].upper()
    filtered_items = []
    for item in schedule_items:
        if item['date'] is None:
            if view_mode == 'today' and item['day'] != today_code:
                continue
            filtered_items.append(item)
        elif range_start <= item['date'] <= range_end:
            filtered_items.append(item)
    schedule_items = filtered_items

    # Build year / month / week options for the filter dropdowns
    years = sorted({today.year} | set(Semester.objects.values_list('academic_year', flat=True)))
    selected_year = selected.year

    months = []
    if view_mode in ('week', 'month'):
        months = [
            {
                'value': date(selected_year, m, 1).isoformat(),
                'label': date(selected_year, m, 1).strftime('%B'),
            }
            for m in range(1, 13)
        ]

    weeks = []
    if view_mode == 'week':
        month_first = date(selected_year, selected.month, 1)
        next_month_first = (date(selected_year + 1, 1, 1) if selected.month == 12
                            else date(selected_year, selected.month + 1, 1))
        month_end = next_month_first - timedelta(days=1)

        jan1 = date(selected_year, 1, 1)
        week_start = jan1 - timedelta(days=jan1.weekday())
        while week_start <= date(selected_year, 12, 31):
            week_end = week_start + timedelta(days=6)
            if week_end >= month_first and week_start <= month_end:
                weeks.append({
                    'value': week_start.isoformat(),
                    'label': f"Week of {week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}",
                })
            week_start += timedelta(days=7)

    selected_month_str = date(selected.year, selected.month, 1).isoformat()
    selected_week_start = selected - timedelta(days=selected.weekday())
    selected_date_str = selected_week_start.isoformat() if view_mode == 'week' else range_start.isoformat()

    # Group by day
    day_order = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    day_names = {
        'MON': 'Monday', 'TUE': 'Tuesday', 'WED': 'Wednesday',
        'THU': 'Thursday', 'FRI': 'Friday', 'SAT': 'Saturday', 'SUN': 'Sunday'
    }
    
    schedule_by_day = {}
    for day in day_order:
        schedule_by_day[day] = {
            'name': day_names[day],
            'items': sorted(
                [item for item in schedule_items if item['day'] == day],
                key=lambda x: x['start_time']
            )
        }
    
    # Build timetable grid
    time_slots = list(range(8, 18))
    day_keys = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']

    day_short_names = {
        'MON': 'Mon', 'TUE': 'Tue', 'WED': 'Wed',
        'THU': 'Thu', 'FRI': 'Fri', 'SAT': 'Sat', 'SUN': 'Sun'
    }

    # Day header columns with the actual scheduled dates for each day
    day_header_cols = []
    for day_key in day_keys:
        day_data = schedule_by_day.get(day_key, {'items': []})
        day_dates = sorted({
            item['date'] for item in day_data['items']
            if item.get('date')
        })
        day_header_cols.append({
            'code': day_key,
            'label': day_short_names.get(day_key, day_key.title()),
            'dates': day_dates,
        })

    timetable_rows = []
    for hour in time_slots:
        display_hour = hour if hour <= 12 else hour - 12
        display_time = f"{display_hour}:00"
        cells = []
        for day_key in day_keys:
            day_data = schedule_by_day.get(day_key, {'items': []})
            hour_items = sorted(
                [item for item in day_data['items'] if item['slot_hour'] == hour],
                key=lambda x: (x['start_time'], x['course_code'])
            )
            # Show each session only once per day/time cell
            seen = set()
            unique_items = []
            for item in hour_items:
                key = (item['course_code'], item['section_number'], item['start_time'], item['end_time'])
                if key in seen:
                    continue
                seen.add(key)
                unique_items.append(item)
            cells.append({
                'day': day_key,
                'items': unique_items,
            })
        timetable_rows.append({
            'hour': hour,
            'display_time': display_time,
            'cells': cells,
        })

    # Count unique locations
    all_locations = set()
    for item in schedule_items:
        all_locations.add((item['room'], item['building']))

    context = {
        'user': user,
        'student_profile': student_profile,
        'active_page': 'schedule',
        'page_title': 'My Schedule',
        'current_semester': current_semester,
        'schedule_by_day': schedule_by_day,
        'schedule_items': schedule_items,
        'day_header_cols': day_header_cols,
        'total_courses': len(set(item['course_code'] for item in schedule_items)),
        'total_credits': sum(item['credits'] for item in schedule_items) if schedule_items else 0,
        'total_sessions': len(schedule_items),
        'total_locations': len(all_locations),
        'has_schedule': len(schedule_items) > 0,
        'time_slots': time_slots,
        'day_keys': day_keys,
        'timetable_rows': timetable_rows,
        'view_mode': view_mode,
        'filter_label': filter_label,
        'years': years,
        'selected_year': selected_year,
        'weeks': weeks,
        'months': months,
        'selected_month_str': selected_month_str,
        'selected_date_str': selected_date_str,
        ###### Rixie code start #####
        'semester_list': semester_list,
        'semester_filter_code': semester_filter_code,
    }
    #####  Rixie code end ########
    return render(request, 'Academic/schedule.html', context)


@login_required
def my_courses(request, uuid):
    """My Courses page"""
    user = get_object_or_404(User, uuid=uuid)

    student_profile, _ = get_or_create_student_profile(user)

    current_semester = Semester.objects.filter(is_current=True).first()
    if not current_semester:
        current_semester = Semester.objects.order_by('-academic_year', '-start_date').first()

    enrollments = StudentEnrollment.objects.filter(
        student=student_profile,
        enrollment_status__in=['FULL_TIME', 'PART_TIME']
    ).select_related('section_id', 'section_id__course', 'semester')

    course_data = []
    for enrollment in enrollments:
        section = enrollment.section_id
        if not section:
            continue
        course = section.course
        if not course:
            continue
#############   Rixie code start   ##############
        schedules = Schedule.objects.filter(section_id=section)
        # Sort schedules by day of week
        day_order = {
           'MON': 1,
           'TUE': 2,
           'WED': 3,
           'THU': 4,
           'FRI': 5,
           'SAT': 6,
           'SUN': 7,
          }

        schedules = sorted(
              schedules,
              key=lambda s: day_order.get(s.day_of_week, 99)
           )

        sem = enrollment.semester
        sem_code = sem.semester_code if sem else ''
        sem_display = str(sem) if sem else ''

        is_current = current_semester and sem and sem.semester_id == current_semester.semester_id
#############  Rixie code end ##########
        course_data.append({
            'enrollment_id': enrollment.id,
            'course_code': course.course_code,
            'course_name': course.course_name,
            'credits': course.credits,
            'section_number': section.section_number,
            'section_type': section.get_section_type_display(),
            'section_type_code': section.section_type,
            'instructor': section.faculty_name or 'TBA',
            'room': section.room_number or '',
            'building': section.building_name or '',
            ######  Rixixe code start #####
            'semester_code': sem_code,
            'semester_display': sem_display,
            ###### Rixie code End ##########
            'schedule': [
                {
                    'day': schedule.get_day_of_week_display(),
                    'day_short': schedule.get_day_of_week_display()[:3],
                    'start_time': schedule.start_time.strftime('%I:%M %p'),
                    'end_time': schedule.end_time.strftime('%I:%M %p'),
                    'room': schedule.room,
                    'building': schedule.building,
                    'is_online': schedule.is_online,
                    'dates': schedule.dates or [],
                    'dates_display': format_schedule_dates(schedule.dates),
                }
                for schedule in schedules
            ],
            
            ######  Rixie code Start ########
            'status': 'In Progress' if is_current else 'Completed',
            ####### Rixie code End #########
        })

    unique_semesters = StudentEnrollment.objects.filter(
        student=student_profile
    ).select_related('semester').values_list(
        'semester__semester_code', 'semester__semester_type', 'semester__academic_year'
    ).distinct()

    semester_list = []
    for code, stype, year in unique_semesters:
        if code and stype and year:
            semester_type_map = dict(Semester.SEMESTER_TYPES)
            semester_list.append({
                'code': code,
                'display': f"{code} - {semester_type_map.get(stype, stype)} {year}",
            })

    context = {
        'user': user,
        'student_profile': student_profile,
        'academic': getattr(student_profile, 'academic_profile', None),
        'active_page': 'my_courses',
        'page_title': 'My Courses',
        'current_semester': current_semester,
        'courses': course_data,
        'total_courses': len(course_data),
        'total_credits': sum(c['credits'] for c in course_data),
        'semester_list': semester_list,
    }
    return render(request, 'Academic/my_courses.html', context)

###########   Rixie code start  #############
def format_schedule_dates(dates):
    """Format and sort a list of dates."""

    from datetime import datetime as _dt

    date_formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%b %d %Y",
        "%B %d %Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    ]

    parsed_dates = []
    invalid_dates = []

    for d in (dates or []):

        parsed_date = None

        for fmt in date_formats:

            try:

                parsed_date = _dt.strptime(str(d).strip(), fmt)

                break

            except (ValueError, TypeError):

                continue

        if parsed_date is not None:

            parsed_dates.append(parsed_date)

        else:

            invalid_dates.append(str(d))


    # Sort dates chronologically
    parsed_dates.sort()


    # Convert to display format
    formatted = [
        date.strftime("%b %d, %Y")
        for date in parsed_dates
    ]


    # Add any invalid dates at the end
    formatted.extend(invalid_dates)


    return formatted

############   Rixie code end  ###########
def get_course_color(course_code):
    """Color based on course code"""
    colors = {
        'CS': '#c5050c',
        'MATH': '#185fa5',
        'ENGL': '#228b22',
        'PHYSICS': '#d97706',
        'CHEM': '#7c3aed',
        'BIO': '#059669',
        'HIST': '#b45309',
        'PSYCH': '#db2777',
        'ECON': '#0d9488',
        'POLI': '#4f46e5',
    }
    for key, color in colors.items():
        if course_code.startswith(key):
            return color
    return '#6b7280'




def grades_view(request, uuid):
    """Student grades page"""
    user = get_object_or_404(User, uuid=uuid)
    
    # try:
    #     student_profile = StudentProfile.objects.get(user=user)
    # except StudentProfile.DoesNotExist:
    #     # Create profile if it doesn't exist
    #     student_profile = StudentProfile.objects.create(
    #         user=user,
    #         student_number=f"STU{user.id:06d}",
    #         university_email=user.email,
    #         current_status='ACTIVE',
    #     )
    #     messages.success(request, 'Student profile created successfully!')
    
    # # Get current semester
    # current_semester = Semester.objects.filter(is_current=True).first()
    
    # if not current_semester:
    #     current_semester = Semester.objects.order_by('-academic_year', '-start_date').first()
    
    # # Get student enrollments for current semester
    # enrollments = StudentEnrollment.objects.filter(
    #     student=student_profile,
    #     term_id=current_semester.semester_id if current_semester else None,
    #     enrollment_status__in=['FULL_TIME', 'PART_TIME']
    # ).select_related('section_id', 'section_id__course_id')
    
    # # Build grades data
    # grades_data = []
    # for enrollment in enrollments:
    #     if enrollment.section_id:
    #         section = enrollment.section_id
    #         course = section.course_id
            
    #         grades_data.append({
    #             'course_code': course.course_code,
    #             'course_name': course.course_name,
    #             'credits': course.credits,
    #             'section_number': section.section_number,
    #             'section_type': section.get_section_type_display(),
    #             'instructor': section.faculty_name or 'TBA',
    #             'grade': enrollment.grade or 'In Progress',
    #             'status': enrollment.enrollment_status,
    #         })
    
    # context = {
    #     'user': user,
    #     'student_profile': student_profile,
    #     'active_page': 'grades',
    #     'page_title': 'My Grades',
    #     'current_semester': current_semester,
    #     'grades': grades_data,
    #     'total_courses': len(grades_data),
    # }
    return render(request, 'Academic/grades.html') 


def degree_progress_view(request, uuid):
    """Degree progress page"""
    user = get_object_or_404(User, uuid=uuid)
    
    #Handle case where StudentProfile doesn't exist
    try:
        student_profile = StudentProfile.objects.get(user=user)
    except StudentProfile.DoesNotExist:
        # Create profile if it doesn't exist
        student_profile = StudentProfile.objects.create(
            user=user,
            student_number=f"STU{user.id:06d}",
            university_email=user.email,
            current_status='ACTIVE',
        )
        messages.success(request, 'Student profile created successfully!')
    
    context = {
        'user': user,
        'student_profile': student_profile,
        'active_page': 'degree_progress',
        'page_title': 'Degree Progress',
    }
    return render(request, 'Academic/Degree.html', context)


def _grade_css_class(letter_grade):
    if not letter_grade or letter_grade == "—":
        return ""
    first = letter_grade[0].upper()
    return f"grade-{first.lower()}" if first in "ABCDF" else ""


def transcripts_view(request, uuid):
    """Transcripts page"""
    user = get_object_or_404(User, uuid=uuid)

    try:
        student_profile = StudentProfile.objects.get(user=user)
    except StudentProfile.DoesNotExist:
        student_profile = StudentProfile.objects.create(
            user=user,
            student_number=f"STU{user.id:06d}",
            university_email=user.email,
            current_status='ACTIVE',
        )
        messages.success(request, 'Student profile created successfully!')

    academic_profile = StudentAcademicProfile.objects.filter(student=student_profile).first()

    latest_enrollment = (
        StudentEnrollment.objects
        .filter(student=student_profile)
        .order_by("-semester__start_date")
        .first()
    )

    enrollments = (
        StudentEnrollment.objects
        .filter(student=student_profile)
        .exclude(enrollment_status="WITHDRAWN")
        .select_related("semester", "section_id", "section_id__course")
        .order_by("semester__start_date")
    )

    finalized_grades = {
        (g.course_id, g.semester_id): g
        for g in CourseGrade.objects.select_related("grade_scale").filter(
            student=student_profile,
            is_finalized=True,
        )
    }

    semesters = {}
    for e in enrollments:
        section = e.section_id
        if not section or not section.course:
            continue
        course = section.course
        sem = e.semester
        sem_key = sem.semester_id

        if sem_key not in semesters:
            semesters[sem_key] = {
                "semester_obj": sem,
                "name": str(sem),
                "courses": [],
                "credits": 0,
                "quality_points": Decimal("0.00"),
                "graded_credits": 0,
            }
        entry = semesters[sem_key]

        credits = course.credits or 0
        grade = finalized_grades.get((course.course_id, sem.semester_id))

        if grade:
            status = "completed"
            letter_grade = grade.grade_scale.letter_grade if grade.grade_scale else "—"
            grade_points = grade.grade_scale.grade_points if grade.grade_scale else None
            numeric_score = grade.numeric_score
        else:
            status = "in-progress"
            letter_grade = "—"
            grade_points = None
            numeric_score = None

        entry["courses"].append({
            "course_code": course.course_code,
            "course_name": course.course_name,
            "credits": credits,
            "numeric_score": numeric_score,
            "letter_grade": letter_grade,
            "grade_points": grade_points,
            "status": status,
            "grade_class": _grade_css_class(letter_grade),
        })

        entry["credits"] += credits
        if status == "completed" and grade_points is not None:
            entry["quality_points"] += Decimal(grade_points) * credits
            entry["graded_credits"] += credits

    semester_list = []
    total_credits = 0
    total_quality_points = Decimal("0.00")
    total_graded_credits = 0
    courses_completed = 0

    for entry in semesters.values():
        entry["gpa"] = (
            round(entry["quality_points"] / entry["graded_credits"], 2)
            if entry["graded_credits"] else None
        )
        entry["status"] = (
            "in-progress" if any(c["status"] == "in-progress" for c in entry["courses"])
            else "completed"
        )

        total_credits += entry["credits"]
        total_quality_points += entry["quality_points"]
        total_graded_credits += entry["graded_credits"]
        courses_completed += sum(1 for c in entry["courses"] if c["status"] == "completed")
        semester_list.append(entry)
    semester_list.sort(key=lambda e: e["semester_obj"].start_date)
    if total_graded_credits > 0:
        cumulative_gpa = round(
            total_quality_points / total_graded_credits,
            2
        )
    else:
        cumulative_gpa = Decimal("0.00")

    context = {
        "user": user,
        "student_profile": student_profile,
        "academic_profile": academic_profile,
        "latest_enrollment": latest_enrollment,
        "active_page": "transcripts",
        "page_title": "Transcripts",
        "semesters": semester_list,
        "cumulative_gpa": cumulative_gpa,
        "total_credits": total_credits,
        "courses_completed": courses_completed,
        "semester_count": len(semester_list),
    }
    return render(request, "Academic/Transcripts.html", context)




#<-----------------Blaze Code Start 28.08.2026--------------------->



from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from Admin.models import User, RoomAllocation, Hostel, Room
from .models import MaintenanceRequest


@login_required
def housing_view(request, uuid):
    user = get_object_or_404(User, uuid=uuid)
    
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    
    current_allocation = RoomAllocation.objects.filter(
        student=user,
        status='ACTIVE'
    ).select_related('room', 'room__hostel').first()
    
    history_allocations = RoomAllocation.objects.filter(
        student=user
    ).exclude(
        id=current_allocation.id if current_allocation else None
    ).select_related('room', 'room__hostel').order_by('-allocated_date')[:5]
    
    roommate_info = None
    if current_allocation:
        roommates = RoomAllocation.objects.filter(
            room=current_allocation.room,
            status='ACTIVE'
        ).exclude(student=user).select_related('student')
        
        if roommates.exists():
            roommate = roommates.first().student
            roommate_info = {
                'name': roommate.full_name,
                'email': roommate.email,
                'username': roommate.username,
                'gender': getattr(roommate, 'gender', 'N/A'),
                'program': 'Unknown',
            }
    
    amenities_list = []
    if current_allocation and current_allocation.room.amenities:
        amenities_list = [a.strip() for a in current_allocation.room.amenities.split(',') if a.strip()]
    
    duration_days = None
    if current_allocation and current_allocation.move_in_date:
        today = timezone.now().date()
        duration_days = (today - current_allocation.move_in_date).days
    
    # Get maintenance requests for this student
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    search = request.GET.get('search', '').strip()
    
    maintenance_requests = MaintenanceRequest.objects.filter(
        student=user
    ).select_related('room', 'room__hostel').order_by('-created_at')
    
    if status_filter != 'all':
        maintenance_requests = maintenance_requests.filter(status=status_filter.upper())
    
    if priority_filter != 'all':
        maintenance_requests = maintenance_requests.filter(priority=priority_filter.upper())
    
    if search:
        maintenance_requests = maintenance_requests.filter(
            Q(room__room_number__icontains=search) |
            Q(issue_type__icontains=search) |
            Q(description__icontains=search)
        )
    
    context = {
        'user': user,
        'current_allocation': current_allocation,
        'history_allocations': history_allocations,
        'roommate_info': roommate_info,
        'amenities_list': amenities_list,
        'duration_days': duration_days,
        'has_housing': current_allocation is not None,
        'maintenance_requests': maintenance_requests,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search': search,
        'active_sb': 'housing',
        'page_title': 'Housing',
    }
    
    return render(request, 'Campus_life/housing.html', context)


@login_required
def get_available_rooms_json(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        current_allocation = RoomAllocation.objects.filter(
            student=request.user,
            status='ACTIVE'
        ).select_related('room', 'room__hostel').first()
        
        if not current_allocation:
            return JsonResponse([], safe=False)
        
        rooms = Room.objects.filter(
            hostel=current_allocation.room.hostel
        ).values(
            'id', 'room_number', 'capacity', 'current_occupancy', 'status'
        ).order_by('room_number')
        
        room_list = []
        for room in rooms:
            room_list.append({
                'id': room['id'],
                'room_number': room['room_number'],
                'capacity': room['capacity'],
                'current_occupancy': room['current_occupancy'],
                'status': room['status'],
                'available_slots': room['capacity'] - room['current_occupancy'],
                'is_available': room['current_occupancy'] < room['capacity'],
                'is_current_room': room['id'] == current_allocation.room.id
            })
        
        return JsonResponse(room_list, safe=False)
        
    except Exception as e:
        import logging
        logging.error(f"Error loading rooms: {e}")
        return JsonResponse([], safe=False)


@login_required
@require_http_methods(["POST"])
def maintenance_request_submit(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    student = get_object_or_404(User, uuid=uuid)
    
    room_id = request.POST.get('room_id')
    issue_type = request.POST.get('issue_type')
    description = request.POST.get('description')
    priority = request.POST.get('priority', 'MEDIUM')
    preferred_time = request.POST.get('preferred_time', '')
    
    if not room_id or not issue_type or not description:
        return JsonResponse({'success': False, 'error': 'All required fields must be filled'})
    
    try:
        room = get_object_or_404(Room, id=room_id)
        
        has_allocation = RoomAllocation.objects.filter(
            student=student,
            room=room,
            status='ACTIVE'
        ).exists()
        
        if not has_allocation:
            return JsonResponse({'success': False, 'error': 'You are not allocated to this room'})
        
        MaintenanceRequest.objects.create(
            student=student,
            room=room,
            issue_type=issue_type,
            description=description,
            priority=priority,
            preferred_time=preferred_time,
            status='PENDING'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Maintenance request submitted successfully!'
        })
        
    except Room.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Room not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

#<-----------------Blaze Code End 28.08.2026--------------------->





from .models import StudentOrganization, StudentOrganizationMembership

@login_required
def organizations_view(request, uuid):
    """Student Organizations page"""
    user = get_object_or_404(User, uuid=uuid)
    student_profile = get_object_or_404(StudentProfile, user=user)

    memberships = StudentOrganizationMembership.objects.filter(
        student=student_profile
    ).select_related("organization", "organization__advisor")

    active_memberships = memberships.filter(
        status__in=["ACTIVE", "PENDING"]
    ).order_by("organization__organization_name")

    past_memberships = memberships.filter(
        status__in=["INACTIVE", "ALUMNI"]
    ).order_by("-end_date")

    context = {
        "user": user,
        "student_profile": student_profile,
        "active_page": "organizations",
        "page_title": "Organizations",
        "active_memberships": active_memberships,
        "past_memberships": past_memberships,
        "total_active": active_memberships.count(),
        "total_past": past_memberships.count(),
    }
    return render(request, "Campus_life/organizations.html", context)


@login_required
def browse_organizations_ajax(request, uuid):
    """Return orgs the student hasn't joined yet, for the Join Organization modal"""
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    student_profile = request.user.student_profile

    joined_ids = StudentOrganizationMembership.objects.filter(
        student=student_profile
    ).exclude(status="INACTIVE").values_list("organization_id", flat=True)

    search = request.GET.get("q", "").strip()

    available = StudentOrganization.objects.exclude(id__in=joined_ids)
    if search:
        available = available.filter(organization_name__icontains=search)
    available = available.order_by("organization_name")

    return JsonResponse({
        "success": True,
        "organizations": [
            {
                "id": o.id,
                "name": o.organization_name,
                "description": o.description or "",
                "advisor": o.advisor.user.get_full_name() if o.advisor else "TBA",
                "school": o.school.school_name if o.school else "",
            }
            for o in available
        ],
    })


@login_required
def request_join_organization(request, uuid, org_id):
    """Student requests to join an org → creates a PENDING membership"""
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid method"}, status=405)

    student_profile = request.user.student_profile
    org = get_object_or_404(StudentOrganization, id=org_id)

    existing = StudentOrganizationMembership.objects.filter(
        student=student_profile, organization=org
    ).exclude(status="INACTIVE").first()

    if existing:
        return JsonResponse({
            "success": False,
            "error": f"You already have a {existing.get_status_display().lower()} membership in this organization."
        })

    if org.is_full:
        return JsonResponse({
            "success": False,
            "error": f"{org.organization_name} has reached its maximum of {org.max_members} members."
        })

    membership = StudentOrganizationMembership.objects.create(
        student=student_profile,
        organization=org,
        status="PENDING",
        start_date=timezone.now().date(),
    )
    
    AuditLogger.log(
        request=request,
        action="REQUEST",
        module="Student Organizations",
        object_type="StudentOrganizationMembership",
        object_id=membership.id,
        description=(
            f"Student '{request.user.username}' requested to join "
            f"organization '{org.organization_name}'."
        ),
        after_data={
            "organization_id": org.id,
            "organization_name": org.organization_name,
            "student_id": student_profile.id,
            "status": membership.status,
            "start_date": membership.start_date,
        },
        user=request.user,
    )

    try:
        from Staff.utils import notify_staff_new_org_join_request
        notify_staff_new_org_join_request(membership)
    except ImportError:
        pass

    return JsonResponse({
        "success": True,
        "message": f"Request to join {org.organization_name} submitted! Staff will review it shortly."
    })


@login_required
def leave_organization(request, uuid, membership_id):
    """Student voluntarily leaves an org they're currently in"""
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid method"}, status=405)

    student_profile = request.user.student_profile
    membership = get_object_or_404(
        StudentOrganizationMembership,
        id=membership_id,
        student=student_profile,
    )

    if membership.status not in ["ACTIVE", "PENDING"]:
        return JsonResponse({"success": False, "error": "This membership can't be left."})
    
    
    # ==============================
    # BEFORE DATA
    # ==============================
    before_data = {
        "organization_id": membership.organization.id,
        "organization_name": membership.organization.organization_name,
        "status": membership.status,
        "start_date": membership.start_date,
        "end_date": membership.end_date,
    }

    old_status = membership.status

    membership.status = "INACTIVE"
    membership.end_date = timezone.now().date()
    membership.save()
    
    # ==============================
    # AFTER DATA
    # ==============================
    after_data = {
        "organization_id": membership.organization.id,
        "organization_name": membership.organization.organization_name,
        "status": membership.status,
        "start_date": membership.start_date,
        "end_date": membership.end_date,
    }
    
    # ==============================
    # AUDIT LOG
    # ==============================
    AuditLogger.log(
        request=request,
        action="CANCEL",
        module="Student Organizations",
        object_type="StudentOrganizationMembership",
        object_id=membership.id,
        description=(
            f"Student '{request.user.username}' left "
            f"organization '{membership.organization.organization_name}'. "
            f"Membership status changed from '{old_status}' to 'INACTIVE'."
        ),
        before_data=before_data,
        after_data=after_data,
        user=request.user,
    )


    return JsonResponse({"success": True, "message": "You've left the organization."})



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models  
from Admin.models import User
from .models import StudentProfile, StudentResearchProfile

@login_required
def research_view(request, uuid):
    """Student Research page"""
    user = get_object_or_404(User, uuid=uuid)
    
    try:
        student_profile = StudentProfile.objects.get(user=user)
    except StudentProfile.DoesNotExist:
        messages.warning(request, 'Student profile not found.')
        return redirect('Student:student_dashboard', uuid=user.uuid)
    
    active_research = StudentResearchProfile.objects.filter(
        student=student_profile
    ).filter(
        models.Q(participation_end__isnull=True) | 
        models.Q(participation_end__gte=timezone.now().date())
    ).order_by('-participation_start')
    
  
    completed_research = StudentResearchProfile.objects.filter(
        student=student_profile,
        participation_end__lt=timezone.now().date()
    ).order_by('-participation_start')[:5]
    
    context = {
        'user': user,
        'student_profile': student_profile,
        'active_page': 'research',
        'page_title': 'Research',
        'active_research': active_research,
        'completed_research': completed_research,
        'total_active': active_research.count(),
        'total_completed': completed_research.count(),
        'has_active': active_research.exists(),
        'has_completed': completed_research.exists(),
        'now': timezone.now(),
    }
    return render(request, 'campus_life/research.html', context)

@login_required
def career_profile_view(request, uuid):
    """Student Career Profile page"""
    user = get_object_or_404(User, uuid=uuid)
    student_profile = get_object_or_404(StudentProfile, user=user)
    
    # Get or create career profile
    career_profile, created = StudentCareerProfile.objects.get_or_create(
        student=student_profile
    )
    
    context = {
        'user': user,
        'student_profile': student_profile,
        'active_page': 'career_profile',
        'page_title': 'Career Profile',
        'career_profile': career_profile,
        'has_internship': career_profile.internship_company is not None,
    }
    return render(request, 'Campus_life/career_profile.html', context)


    



# ================================Parthi Update end====================================================    



from uuid import uuid4
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
import json
from Staff.utils import notify_staff_new_financial_aid

@login_required
def student_financial_aid(request, uuid):
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')

    # =====  AJAX REQUEST =====
    if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            app_number = f"FA-{timezone.now().year}-{uuid4().hex[:8].upper()}"
            
            aid = StudentFinancialAid.objects.create(
                student=profile,
                aid_type=request.POST.get("aid_type"),
                academic_year=request.POST.get("academic_year"),
                reason=request.POST.get("financial_need_description") or request.POST.get("reason", ""),
                status="PENDING",
                financial_need_description=request.POST.get("financial_need_description"),
                loan_amount_requested=request.POST.get("loan_amount_requested") or None,
                loan_purpose=request.POST.get("loan_purpose"),
                cosigner_name=request.POST.get("cosigner_name"),
                cosigner_relationship=request.POST.get("cosigner_relationship"),
                preferred_department=request.POST.get("preferred_department"),
                faculty_interest=request.POST.get("faculty_interest"),
                relevant_skills=request.POST.get("relevant_skills"),
                application_number=app_number,
                terms_accepted=request.POST.get("terms_accepted") == 'on',
                terms_accepted_date=timezone.now() if request.POST.get("terms_accepted") else None,
            )
            
            if request.FILES.get("supporting_document"):
                aid.supporting_document = request.FILES["supporting_document"]
                aid.save()
                
            AuditLogger.log(
                request=request,
                action="REQUEST",
                module="Financial Aid",
                object_type="Student Financial Aid",
                object_id=aid.id,
                description=(
                    f"Student '{request.user.username}' submitted financial aid "
                    f"application '{aid.application_number}'."
                ),
                after_data={
                    "application_number": aid.application_number,
                    "aid_type": aid.aid_type,
                    "academic_year": aid.academic_year,
                    "status": aid.status,
                    "loan_amount_requested": (
                        str(aid.loan_amount_requested)
                        if aid.loan_amount_requested else None
                    ),
                    "has_supporting_document": bool(aid.supporting_document),
                },
                user=request.user,
            )
            
            notify_staff_new_financial_aid(aid)

            print(f" AJAX Created aid: {aid.id} - {app_number}")

            return JsonResponse({
                'success': True,
                'message': f'Application #{app_number} submitted successfully!',
                'data': {
                    'id': aid.id,
                    'application_number': app_number,
                }
            })

        except Exception as e:
            print(f" AJAX Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    # ===== NORMAL POST - Redirect =====
    if request.method == "POST":
        try:
            app_number = f"FA-{timezone.now().year}-{uuid4().hex[:8].upper()}"
            
            aid = StudentFinancialAid.objects.create(
                student=profile,
                aid_type=request.POST.get("aid_type"),
                academic_year=request.POST.get("academic_year"),
                reason=request.POST.get("financial_need_description") or request.POST.get("reason", ""),
                status="PENDING",
                financial_need_description=request.POST.get("financial_need_description"),
                loan_amount_requested=request.POST.get("loan_amount_requested") or None,
                loan_purpose=request.POST.get("loan_purpose"),
                cosigner_name=request.POST.get("cosigner_name"),
                cosigner_relationship=request.POST.get("cosigner_relationship"),
                preferred_department=request.POST.get("preferred_department"),
                faculty_interest=request.POST.get("faculty_interest"),
                relevant_skills=request.POST.get("relevant_skills"),
                application_number=app_number,
                terms_accepted=request.POST.get("terms_accepted") == 'on',
                terms_accepted_date=timezone.now() if request.POST.get("terms_accepted") else None,
            )
            
            if request.FILES.get("supporting_document"):
                aid.supporting_document = request.FILES["supporting_document"]
                aid.save()
                
            AuditLogger.log(
                request=request,
                action="REQUEST",
                module="Financial Aid",
                object_type="Student Financial Aid",
                object_id=aid.id,
                description=(
                    f"Student '{request.user.username}' submitted financial aid "
                    f"application '{aid.application_number}'."
                ),
                after_data={
                    "application_number": aid.application_number,
                    "aid_type": aid.aid_type,
                    "academic_year": aid.academic_year,
                    "status": aid.status,
                    "loan_amount_requested": (
                        str(aid.loan_amount_requested)
                        if aid.loan_amount_requested else None
                    ),
                    "has_supporting_document": bool(aid.supporting_document),
                },
                user=request.user,
            )
            
            notify_staff_new_financial_aid(aid)

            messages.success(
                request,
                f"Financial aid application #{app_number} submitted successfully!"
            )

        except Exception as e:
            messages.error(request, f"Error submitting application: {str(e)}")
            print(f" Error: {str(e)}")
            import traceback
            traceback.print_exc()

        return redirect("student_financial_aid", uuid=request.user.uuid)

    # ===== GET - Show page with PAGINATION =====
    #  FOR STATISTICS - ALL records
    aids_list = profile.financial_aids.all().order_by("-applied_date")

    #  FOR PAGINATION - Current page only
    page = request.GET.get('page', 1)
    paginator = Paginator(aids_list, 5)  # 5 records per page
    
    try:
        aids = paginator.page(page)
    except PageNotAnInteger:
        aids = paginator.page(1)
    except EmptyPage:
        aids = paginator.page(paginator.num_pages)

    # STATISTICS - Use aids_list (ALL records)
    total_awarded = aids_list.filter(status="AWARDED").aggregate(
        total=models.Sum("award_amount")
    )["total"] or Decimal("0.00")

    total_pending = aids_list.filter(status="PENDING").aggregate(
        total=models.Sum("award_amount")
    )["total"] or Decimal("0.00")

    total_aid = aids_list.exclude(
        status__in=["CANCELLED", "EXPIRED"]
    ).aggregate(
        total=models.Sum("award_amount")
    )["total"] or Decimal("0.00")

    # ===== FILTER COUNTS - For tab badges =====
    scholarship_count = aids_list.filter(aid_type="SCHOLARSHIP").count()
    grant_count = aids_list.filter(aid_type="GRANT").count()
    fellowship_count = aids_list.filter(aid_type="FELLOWSHIP").count()
    assistantship_count = aids_list.filter(aid_type="ASSISTANTSHIP").count()
    loan_count = aids_list.filter(aid_type="LOAN").count()

    return render(
        request,
        "Finance/financial_aid.html",
        {
            "aids": aids,  #Paginated objects for table
            "total_awarded": total_awarded,
            "total_pending": total_pending,
            "total_aid": total_aid,
            # Filter counts for tabs
            "scholarship_count": scholarship_count,
            "grant_count": grant_count,
            "fellowship_count": fellowship_count,
            "assistantship_count": assistantship_count,
            "loan_count": loan_count,
        },
    )

#Blaze code start for student financial------------->(02.07.26)

@login_required
def student_financial_aid_detail(request, uuid, aid_id):
    """View individual financial aid application details - AJAX"""
    try:
        profile = request.user.student_profile
        aid = get_object_or_404(
            StudentFinancialAid, 
            id=aid_id, 
            student=profile
        )
    except StudentProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student profile not found'
        }, status=404)
    
    # Return JSON for AJAX
    return JsonResponse({
        'success': True,
        'aid': {
            'id': aid.id,
            'aid_type': aid.aid_type,
            'aid_type_display': aid.get_aid_type_display(),
            'academic_year': aid.academic_year,
            'reason': aid.reason,
            'award_amount': str(aid.award_amount),
            'status': aid.status,
            'status_display': aid.get_status_display(),
            'applied_date': aid.applied_date.strftime('%B %d, %Y'),
            'updated_date': aid.updated_date.strftime('%B %d, %Y'),
            'remarks': aid.remarks or 'No remarks',
            'supporting_document': aid.supporting_document.url if aid.supporting_document else None,
            'student_name': aid.student.user.get_full_name(),
            'student_number': aid.student.student_number,
            'loan_amount_requested': str(aid.loan_amount_requested) if aid.loan_amount_requested else None,
            'loan_purpose': aid.loan_purpose,
            'cosigner_name': aid.cosigner_name,
            'cosigner_relationship': aid.cosigner_relationship,
            'preferred_department': aid.preferred_department,
            'faculty_interest': aid.faculty_interest,
            'relevant_skills': aid.relevant_skills,
            'financial_need_description': aid.financial_need_description,
        }
    })

    
from django.http import JsonResponse
import json

@login_required
def update_financial_aid(request, uuid, aid_id):
    """
    Update financial aid application via AJAX
    """
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=400)
    
    try:
        # Get JSON data
        data = json.loads(request.body)
        profile = request.user.student_profile
        
        # Get the aid
        aid = get_object_or_404(
            StudentFinancialAid, 
            id=aid_id, 
            student=profile
        )
        
        # Check if can edit (only PENDING)
        if aid.status != 'PENDING':
            return JsonResponse({'success': False, 'error': 'Only pending applications can be edited'}, status=400)
        
        before_data = {
            "aid_type": aid.aid_type,
            "academic_year": aid.academic_year,
            "reason": aid.reason,
            "status": aid.status,
        }
        
        # Update fields
        if 'aid_type' in data:
            aid.aid_type = data['aid_type']
        if 'academic_year' in data:
            aid.academic_year = data['academic_year']
        if 'reason' in data:
            aid.reason = data['reason']
        
        aid.save()
        
        after_data = {
            "aid_type": aid.aid_type,
            "academic_year": aid.academic_year,
            "reason": aid.reason,
            "status": aid.status,
        }

        AuditLogger.log(
            request=request,
            action="UPDATE",
            module="Financial Aid",
            object_type="Student Financial Aid",
            object_id=aid.id,
            description=(
                f"Student '{request.user.username}' updated financial aid "
                f"application '{aid.application_number}'."
            ),
            before_data=before_data,
            after_data=after_data,
            user=request.user,
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Application updated successfully!',
            'data': {
                'id': aid.id,
                'aid_type': aid.aid_type,
                'academic_year': aid.academic_year,
                'reason': aid.reason,
                'status': aid.status,
            }
        })
        
    except StudentFinancialAid.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Application not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        print(f"Error updating financial aid: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)    


@login_required
def student_financial_aid_print(request, uuid, aid_id):

    """Print financial aid application - Print-friendly version"""
    try:
        profile = request.user.student_profile
        aid = get_object_or_404(
            StudentFinancialAid, 
            id=aid_id, 
            student=profile
        )
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')
    
    return render(
        request,
        "Finance/financial_aid_print.html",
        {
            "aid": aid,
            "student": profile,
            "today": timezone.now(),
        }
    )


# Add to Students/views.py

@login_required
def cancel_financial_aid(request, uuid, aid_id):
    """
    Cancel financial aid application via AJAX
    """
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=400)
    
    try:
        data = json.loads(request.body)
        profile = request.user.student_profile
        
        aid = get_object_or_404(
            StudentFinancialAid, 
            id=aid_id, 
            student=profile
        )
        
        if aid.status != 'PENDING':
            return JsonResponse({'success': False, 'error': 'Only pending applications can be cancelled'}, status=400)
        
        # ==============================
        # AUDIT - BEFORE DATA
        # ==============================
        before_data = AuditLogger.model_to_dict(
            aid,
            [
                "aid_type",
                "academic_year",
                "reason",
                "status",
                "remarks",
            ]
        )
        
        aid.status = 'CANCELLED'
        aid.remarks = 'Cancelled by student'
        aid.save()
        
        # ==============================
        # AUDIT - AFTER DATA
        # ==============================
        after_data = AuditLogger.model_to_dict(
            aid,
            [
                "aid_type",
                "academic_year",
                "reason",
                "status",
                "remarks",
            ]
        )

        AuditLogger.log(
            request=request,
            action="CANCEL",
            module="Financial Aid",
            object_type="Student Financial Aid",
            object_id=aid.id,
            description=(
                f"Student cancelled financial aid application "
                f"'{aid.application_number}'."
            ),
            before_data=before_data,
            after_data=after_data,
            user=request.user,
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Application cancelled successfully!'
        })
        
    except StudentFinancialAid.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Application not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def student_financial_aid_edit(request, uuid, aid_id):
    """
    Edit a financial aid application (only if PENDING)
    """
    try:
        profile = request.user.student_profile
        aid = get_object_or_404(
            StudentFinancialAid, 
            id=aid_id, 
            student=profile,
            status="PENDING"  # Only pending can be edited
        )
    except (StudentProfile.DoesNotExist, StudentFinancialAid.DoesNotExist):
        messages.error(request, "Application not found or cannot be edited.")
        return redirect('Student:student_financial_aid', uuid=request.user.uuid)
    
    if request.method == "POST":
        
        # ==============================
        # AUDIT - BEFORE DATA
        # ==============================
        before_data = AuditLogger.model_to_dict(
            aid,
            [
                "aid_type",
                "academic_year",
                "reason",
                "supporting_document",
                "status",
            ]
        )
        
        aid.aid_type = request.POST.get("aid_type")
        aid.academic_year = request.POST.get("academic_year")
        aid.reason = request.POST.get("reason")
        
        if request.FILES.get("supporting_document"):
            aid.supporting_document = request.FILES["supporting_document"]
        
        aid.save()
        
        # ==============================
        # AUDIT - AFTER DATA
        # ==============================
        after_data = AuditLogger.model_to_dict(
            aid,
            [
                "aid_type",
                "academic_year",
                "reason",
                "supporting_document",
                "status",
            ]
        )

        AuditLogger.log(
            request=request,
            action="UPDATE",
            module="Financial Aid",
            object_type="Student Financial Aid",
            object_id=aid.id,
            description=(
                f"Student updated financial aid application "
                f"'{aid.application_number}'."
            ),
            before_data=before_data,
            after_data=after_data,
            user=request.user,
        )

        
        messages.success(request, "Application updated successfully.")
        return redirect('Student:student_financial_aid_detail', uuid=uuid, aid_id=aid_id)
    
    return render(
        request,
        "Finance/financial_aid_edit.html",
        {
            "aid": aid,
        }
    )

 
 
# ─────────────────────────────────────────────
# Finance — Fee Payments
# ─────────────────────────────────────────────
 
@login_required
def student_fee_payments(request, uuid):
    profile = request.user.student_profile
    charges = profile.fees.all().order_by("due_date")
    payments = profile.fee_payments.all().order_by("-payment_date")
    total_fee = charges.aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")
    total_paid = payments.filter(
        status="SUCCESS"
    ).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")
    aid_applied = profile.financial_aids.filter(
        status="AWARDED"
    ).aggregate(
        total=Sum("award_amount")
    )["total"] or Decimal("0.00")
    outstanding_balance = total_fee - total_paid - aid_applied

    if outstanding_balance < 0:
        outstanding_balance = Decimal("0.00")
    current_term = "Fall 2026"
    due_date = None
    if charges.exists():
        due_date = charges.order_by("due_date").first().due_date
        
    # ==============================
    # AUDIT LOG - FEE PAYMENTS VIEW
    # ==============================
    AuditLogger.log(
        request=request,
        action="VIEW",
        module="Finance",
        object_type="Student Fee Payments",
        object_id=profile.id,
        description=(
            f"Student viewed fee payments and outstanding balance. "
            f"Outstanding balance: {outstanding_balance}."
        ),
        after_data={
            "total_fee": str(total_fee),
            "total_paid": str(total_paid),
            "financial_aid_applied": str(aid_applied),
            "outstanding_balance": str(outstanding_balance),
            "current_term": current_term,
        },
        user=request.user,
    )
    
    return render(
        request,
        "Finance/feepayments.html",
        {
            "charges": charges,
            "payments": payments,
            "outstanding_balance": outstanding_balance,
            "total_paid": total_paid,
            "aid_applied": aid_applied,
            "current_term": current_term,
            "due_date": due_date,

        },
    )
 
 
# ─────────────────────────────────────────────
# Settings — Notifications
# ─────────────────────────────────────────────
 
@login_required
def student_notifications(request, uuid):
    """
    GET  → display current preferences (stored in session or a
           NotificationPreference model once created).
    POST → save updated preferences.
    """
    profile = request.user.student_profile
 
    if request.method == 'POST':
        prefs = {key: True for key in request.POST if key != 'csrfmiddlewaretoken'}

        request.session['notif_prefs'] = prefs
        
        AuditLogger.log(
            request=request,
            action="UPDATE",
            module="Settings",
            object_type="Notification Preferences",
            object_id=request.user.id,
            description=(
                f"Notification preferences updated by user "
                f"'{request.user.username}'."
            ),
            after_data={
                "preferences": list(prefs.keys()),
            },
            status="SUCCESS",
            user=request.user,
        )
 
    prefs = request.session.get('notif_prefs', {})
 
    return render(request, 'Settings/notifications.html', {
        'prefs':           prefs,
        'academic_notifs': [],  
    })
 
 
# ─────────────────────────────────────────────
# Settings — Account & Security
# ─────────────────────────────────────────────
 
@login_required
def student_account_security(request, uuid):
    profile = request.user.student_profile
 
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
 
        if form_type == 'change_password':
            from django.contrib.auth import update_session_auth_hash
            from django.contrib import messages
 
            current  = request.POST.get('current_password', '')
            new_pwd  = request.POST.get('new_password', '')
            confirm  = request.POST.get('confirm_password', '')
 
            if not request.user.check_password(current):
                messages.error(request, 'Current password is incorrect.')
            elif new_pwd != confirm:
                messages.error(request, 'New passwords do not match.')
            elif len(new_pwd) < 8:
                messages.error(request, 'Password must be at least 8 characters.')
            else:
                request.user.set_password(new_pwd)
                request.user.save()
                update_session_auth_hash(request, request.user)
                
                AuditLogger.log(
                    request=request,
                    action="PASSWORD_CHANGE",
                    module="Settings",
                    object_type="User",
                    object_id=request.user.id,
                    description=f"Password changed successfully for user '{request.user.username}'.",
                    status="SUCCESS",
                    user=request.user,
                )
                
                messages.success(request, 'Password updated successfully.')

    try:
        from django.contrib.sessions.models import Session
        from django.utils import timezone
        import json
 
        active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        sessions = []
        current_key = request.session.session_key
 
        for s in active_sessions:
            data = s.get_decoded()
            if data.get('_auth_user_id') == str(request.user.pk):
                sessions.append({
                    'session_key': s.session_key,
                    'last_active': s.expire_date,
                    'is_current':  s.session_key == current_key,
                    'device':      data.get('device', 'Unknown Device'),
                    'location':    data.get('location', ''),
                })
    except Exception:
        sessions = []
 
    return render(request, 'Settings/account_security.html', {
        'sessions':    sessions,
        'tfa_enabled': getattr(profile, 'tfa_enabled', False),
    })


# views.py - Add these AJAX endpoints

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import update_session_auth_hash
import json
import pyotp
import qrcode
import io
import base64

@login_required
@require_http_methods(["POST"])
def change_password_ajax(request):
    """Handle password change via AJAX"""
    try:
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            current_password = data.get('current_password', '')
            new_password = data.get('new_password', '')
            confirm_password = data.get('confirm_password', '')
        else:
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
        
        # Validate
        if not current_password or not new_password or not confirm_password:
            return JsonResponse({'success': False, 'message': 'All fields are required'})
        
        if new_password != confirm_password:
            return JsonResponse({'success': False, 'message': 'Passwords do not match'})
        
        if not request.user.check_password(current_password):
            return JsonResponse({'success': False, 'message': 'Current password is incorrect'})
        
        # Validate password strength
        try:
            validate_password(new_password, request.user)
        except ValidationError as e:
            return JsonResponse({'success': False, 'message': ' '.join(e.messages)})
        
        # Update password
        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)
        
        return JsonResponse({'success': True, 'message': 'Password updated successfully'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@require_http_methods(["POST"])
def setup_2fa_ajax(request):
    """Generate 2FA secret key and QR code"""
    try:
        # Generate secret key
        secret = pyotp.random_base32()
        request.session['2fa_secret'] = secret
        
        # Generate QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=request.user.email,
            issuer_name="Student Portal"
        )
        
        # Create QR code image
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for display
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return JsonResponse({
            'success': True,
            'secret_key': secret,
            'qr_code': f'data:image/png;base64,{qr_base64}'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@require_http_methods(["POST"])
def verify_2fa_ajax(request):
    """Verify 2FA setup with code"""
    try:
        data = json.loads(request.body)
        code = data.get('code')
        secret = request.session.get('2fa_secret')
        
        if not code or not secret:
            return JsonResponse({'success': False, 'message': 'Invalid setup'})
        
        totp = pyotp.TOTP(secret)
        if totp.verify(code):
            # Save secret to user profile
            profile = request.user.student_profile
            profile.tfa_enabled = True
            profile.tfa_secret = secret
            profile.save()
            
            # Generate backup codes
            backup_codes = []
            for _ in range(10):
                backup_codes.append(pyotp.random_base32()[:12])
            
            profile.tfa_backup_codes = json.dumps(backup_codes)
            profile.save()
            
            del request.session['2fa_secret']
            return JsonResponse({'success': True, 'message': '2FA enabled successfully'})
        
        return JsonResponse({'success': False, 'message': 'Invalid verification code'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@require_http_methods(["POST"])
def disable_2fa_ajax(request):
    """Disable two-factor authentication"""
    try:
        data = json.loads(request.body)
        password = data.get('password')
        
        if not request.user.check_password(password):
            return JsonResponse({'success': False, 'message': 'Invalid password'})
        
        profile = request.user.student_profile
        profile.tfa_enabled = False
        profile.tfa_secret = None
        profile.tfa_backup_codes = None
        profile.save()
        
        return JsonResponse({'success': True, 'message': '2FA disabled'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@require_http_methods(["GET"])
def get_backup_codes_ajax(request):
    """Get backup codes for 2FA"""
    try:
        profile = request.user.student_profile
        
        if not profile.tfa_enabled:
            return JsonResponse({'success': False, 'message': '2FA not enabled'})
        
        codes = json.loads(profile.tfa_backup_codes) if profile.tfa_backup_codes else []
        return JsonResponse({'success': True, 'codes': codes})
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@require_http_methods(["POST"])
def revoke_session_ajax(request):
    """Revoke a specific session"""
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        
        if not session_key:
            return JsonResponse({'success': False, 'message': 'Session key required'})
        
        from django.contrib.sessions.models import Session
        
        try:
            session = Session.objects.get(session_key=session_key)
            session.delete()
            return JsonResponse({'success': True, 'message': 'Session revoked'})
        except Session.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Session not found'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@require_http_methods(["POST"])
def revoke_all_sessions_ajax(request):
    """Revoke all sessions except current"""
    try:
        from django.contrib.sessions.models import Session
        from django.utils import timezone
        
        current_session_key = request.session.session_key
        
        user_sessions = Session.objects.filter(
            expire_date__gte=timezone.now()
        )
        
        for session in user_sessions:
            try:
                data = session.get_decoded()
                if data.get('_auth_user_id') == str(request.user.pk):
                    if session.session_key != current_session_key:
                        session.delete()
            except:
                continue
        
        return JsonResponse({'success': True, 'message': 'All other sessions revoked'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@require_http_methods(["POST"])
def deactivate_account_ajax(request):
    """Deactivate user account"""
    try:
        data = json.loads(request.body)
        password = data.get('password')
        
        if not request.user.check_password(password):
            return JsonResponse({'success': False, 'message': 'Invalid password'})
        
        request.user.is_active = False
        request.user.save()
        
        return JsonResponse({'success': True, 'message': 'Account deactivated'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@require_http_methods(["POST"])
def delete_account_ajax(request):
    """Permanently delete user account"""
    try:
        data = json.loads(request.body)
        password = data.get('password')
        
        if not request.user.check_password(password):
            return JsonResponse({'success': False, 'message': 'Invalid password'})
   
        request.user.delete()
        
        return JsonResponse({'success': True, 'message': 'Account deleted permanently'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})    



# *************************************** Arun Code ********************************************************** 

import re
from datetime import date
from django.db import transaction
from django.db.models import Max
 
from Students.models import (
    StudentProfile,
    StudentAcademicProfile,
    StudentAddress,
    StudentEmergencyContact,
    StudentDocument,
)
 
def generate_student_number(admission_year: int, prefix: str = "STU") -> str:
    """
    Returns the next available student number for the given admission year.
    Looks at existing StudentProfile rows whose student_number starts with
    <year><prefix> and increments the highest sequence found.
    """
    prefix = f"{admission_year}{prefix}"

    existing = (
        StudentProfile.objects
        .filter(student_number__startswith=prefix)
        .values_list("student_number", flat=True)
    )
 
    max_seq = 0
    pattern = re.compile(rf"^{prefix}(\d+)$")
    for num in existing:
        m = pattern.match(num)
        if m:
            seq = int(m.group(1))
            if seq > max_seq:
                max_seq = seq
 
    next_seq = max_seq + 1
    return f"{prefix}{next_seq:03d}"  
 
 
def suggested_student_number_for_context(admission_date_str=None, prefix=None):
    """
    Used to pre-fill the form field on GET (before any date is picked,
    default to the current calendar year — once the admin picks an
    admission date, JS re-requests / recalculates using the year from that date).

    The student number prefix is the selected department's code, which is not
    known until a department is chosen in the form, so this returns an empty
    string until a prefix is supplied.
    """
    if not prefix:
        return ""
    year = date.today().year
    if admission_date_str:
        try:
            year = int(admission_date_str[:4])
        except (ValueError, TypeError):
            pass
    return generate_student_number(year, prefix)
 
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
 
 
@login_required
@require_http_methods(["GET"])
def next_student_number_json(request):
    year_param = request.GET.get("year", "").strip()
    try:
        year = int(year_param) if year_param else date.today().year
    except ValueError:
        year = date.today().year

    program_id = request.GET.get("program", "").strip()
    prefix = None
    if program_id:
        prefix = (
            AcademicProgram.objects.filter(pk=program_id)
            .values_list("program_code", flat=True)
            .first()
        )

    if not prefix:
        return JsonResponse({"student_number": ""})

    return JsonResponse({"student_number": generate_student_number(year, prefix)})
 
from django.core.exceptions import ValidationError
from django.db import transaction
from datetime import date


def save_student_details(request, user):
    """
    Reads all student-related POST fields and creates:
      - StudentProfile
      - StudentAcademicProfile (1:1)
      - StudentAddress (one or more rows)
      - StudentEmergencyContact (one row)
      - StudentDocument (multiple)

    Raises ValidationError if required fields are missing — nothing is
    written to the DB in that case (validation happens before the
    transaction starts).

    Wrapped in a transaction so a failure partway through doesn't leave
    a half-created student record.
    """
    post = request.POST
    files = request.FILES

    required_academic_fields = {
        "school": "College",
        "department": "Department",
        "degree": "Degree",
        "program": "Program",
    }
    missing_academic = [
        label for field, label in required_academic_fields.items()
        if not (post.get(field) or "").strip()
    ]

    required_emergency_fields = {
        "student_emergency_name": "Emergency contact name",
        "student_emergency_relationship": "Emergency contact relationship",
        "student_emergency_phone": "Emergency contact phone",
    }
    missing_emergency = [
        label for field, label in required_emergency_fields.items()
        if not (post.get(field) or "").strip()
    ]

    address_line1s = post.getlist("student_address_line_1[]")
    has_any_address = any((a or "").strip() for a in address_line1s)

    errors = []
    if missing_academic:
        errors.append(f"Missing required academic fields: {', '.join(missing_academic)}")
    if missing_emergency:
        errors.append(f"Missing required emergency contact fields: {', '.join(missing_emergency)}")
    if not has_any_address:
        errors.append("At least one address is required.")

    if errors:
        raise ValidationError(errors)

    admission_date = post.get("admission_date") or None
    expected_graduation_date = post.get("expected_graduation_date") or None

    student_number = (post.get("student_number") or "").strip()
    if not student_number:
        year = date.today().year
        if admission_date:
            try:
                year = int(admission_date[:4])
            except ValueError:
                pass
        prefix = "STU"
        program_id = (post.get("program") or "").strip()
        if program_id:
            program_code = (
                AcademicProgram.objects.filter(pk=program_id)
                .values_list("program_code", flat=True)
                .first()
            )
            if program_code:
                prefix = program_code
        student_number = generate_student_number(year, prefix)

    with transaction.atomic():
        profile = StudentProfile.objects.create(
            user=user,
            student_number=student_number,
            preferred_name=post.get("student_preferred_name", ""),
            university_email=post.get("university_email") or user.email,
            personal_email=post.get("student_personal_email", ""),
            citizenship_status=post.get("citizenship_status") or None,
            country_of_citizenship=post.get("country_of_citizenship") or None,
            marital_status=post.get("marital_status") or None,
            admission_date=admission_date,
            expected_graduation_date=expected_graduation_date,
            current_status=post.get("student_current_status") or "ACTIVE",
            academic_level=post.get("academic_level") or None,
            cumulative_gpa=post.get("cumulative_gpa") or None,
        )
        
        AuditLogger.log(
            request=request,
            action="CREATE",
            module="Student Management",
            object_type="Student Profile",
            object_id=profile.id,
            description=f"Student profile created for {user.username}.",
            after_data=AuditLogger.model_to_dict(
                profile,
                [
                    "student_number",
                    "preferred_name",
                    "university_email",
                    "personal_email",
                    "current_status",
                    "academic_level",
                ],
            ),
            user=request.user,
        )

        # StudentAcademicProfile.objects.create(
        #     student=profile,
        #     university_id=post.get("university") or None,
        #     school_id=post.get("school"),
        #     department_id=post.get("department"),
        #     degree_id=post.get("degree"),
        #     program_id=post.get("program"),
        #     catalog_year=post.get("catalog_year") or None,
        # )
        
        academic_profile = StudentAcademicProfile.objects.create(
            student=profile,
            university_id=post.get("university") or None,
            school_id=post.get("school"),
            department_id=post.get("department"),
            degree_id=post.get("degree"),
            program_id=post.get("program"),
            catalog_year=post.get("catalog_year") or None,
        )
        
        AuditLogger.log(
            request=request,
            action="CREATE",
            module="Academic",
            object_type="Student Academic Profile",
            object_id=academic_profile.id,
            description=f"Academic profile created for student {profile.student_number}.",
            after_data=AuditLogger.model_to_dict(
                academic_profile,
                [
                    "university",
                    "school",
                    "department",
                    "degree",
                    "program",
                    "catalog_year",
                ],
            ),
            user=request.user,
        )

        address_types = post.getlist("student_address_type[]")
        address_line2s = post.getlist("student_address_line_2[]")
        cities = post.getlist("student_city[]")
        states = post.getlist("student_state[]")
        postal_codes = post.getlist("student_postal_code[]")
        countries = post.getlist("student_country[]")

        count = max(len(address_types), len(address_line1s), len(cities))

        for i in range(count):
            line1 = address_line1s[i] if i < len(address_line1s) else ""
            if not line1.strip():
                continue

            StudentAddress.objects.create(
                student=profile,
                address_type=address_types[i] if i < len(address_types) else "PERMANENT",
                address_line_1=line1,
                address_line_2=address_line2s[i] if i < len(address_line2s) else "",
                city=cities[i] if i < len(cities) else "",
                state=states[i] if i < len(states) else "",
                postal_code=postal_codes[i] if i < len(postal_codes) else "",
                country=countries[i] if i < len(countries) else "",
            )

        StudentEmergencyContact.objects.create(
            student=profile,
            contact_name=post.get("student_emergency_name", ""),
            relationship=post.get("student_emergency_relationship", ""),
            phone_number=post.get("student_emergency_phone", ""),
            email=post.get("student_emergency_email", ""),
            priority=post.get("student_emergency_priority") or 1,
        )

        doc_types = post.getlist("student_doc_type[]")
        doc_files = files.getlist("student_doc_file[]")

        for i in range(max(len(doc_types), len(doc_files))):
            doc_type = doc_types[i] if i < len(doc_types) else ""
            doc_file = doc_files[i] if i < len(doc_files) else None

            if not doc_file:
                continue

            # StudentDocument.objects.create(
            #     student=profile,
            #     document_type=doc_type or "OTHER",
            #     file=doc_file,
            #     verification_status="PENDING",
            # )
            
            document = StudentDocument.objects.create(
                student=profile,
                document_type=doc_type or "OTHER",
                file=doc_file,
                verification_status="PENDING",
            )
            AuditLogger.log(
                request=request,
                action="UPLOAD",
                module="Student Management",
                object_type="Student Document",
                object_id=document.id,
                description=(
                    f"Document '{doc_file.name}' uploaded for "
                    f"student {profile.student_number}."
                ),
                after_data={
                    "document_type": document.document_type,
                    "file_name": doc_file.name,
                    "verification_status": document.verification_status,
                },
                user=request.user,
            )

    return profile



# ****************************************************** Ticket students ************************************************

from Students.models import SupportTicket, CourseSection

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator

from Students.models import SupportTicket, CourseSection, StudentEnrollment, StudentProfile
from Staff.utils import notify_staff_new_ticket, notify_staff_new_financial_aid


@login_required
def submit_support_ticket(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")

    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect("Student:student_dashboard", uuid=uuid)

    if request.method == "POST":
        section_id = request.POST.get("course_section")
        subject = request.POST.get("subject", "").strip()
        description = request.POST.get("description", "").strip()
        priority = request.POST.get("priority", "MEDIUM")

        if not subject:
            messages.error(request, "Subject is required.")
            return redirect("Student:submit_support_ticket", uuid=uuid)

        section = None
        if section_id:
            section = CourseSection.objects.filter(section_id=section_id).first()

        ticket = SupportTicket.objects.create(
            course_section=section,
            submitted_by=request.user,
            subject=subject,
            description=description,
            priority=priority,
            status="OPEN",
        )
        
        AuditLogger.log(
            request=request,
            action="CREATE",
            module="Support Tickets",
            object_type="SupportTicket",
            object_id=ticket.id,
            description=(
                f"Student '{request.user.username}' submitted support ticket "
                f"'{ticket.subject}'."
            ),
            after_data={
                "ticket_id": ticket.id,
                "course_section": str(section) if section else None,
                "subject": ticket.subject,
                "description": ticket.description,
                "priority": ticket.priority,
                "status": ticket.status,
            },
            user=request.user,
        )

        notify_staff_new_ticket(ticket)

        messages.success(request, "Your ticket has been submitted. Staff will review it shortly.")
        return redirect("Student:my_support_tickets", uuid=uuid)

    enrolled_section_ids = StudentEnrollment.objects.filter(
        student=profile
    ).exclude(section_id__isnull=True).values_list("section_id", flat=True)

    sections = CourseSection.objects.filter(
        section_id__in=enrolled_section_ids
    ).select_related("course")

    context = {
        "sections": sections,
        "priority_choices": SupportTicket.PRIORITY_CHOICES,
    }
    return render(request, "Academic/submit_ticket.html", context)


@login_required
def my_support_tickets(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")

    tickets = SupportTicket.objects.filter(
        submitted_by=request.user
    ).select_related("course_section__course").order_by("-created_at")

    paginator = Paginator(tickets, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "Academic/my_support_tickets.html", {
        "tickets": page_obj,
        "priority_choices": SupportTicket.PRIORITY_CHOICES,
    })


@login_required
def edit_support_ticket(request, uuid, ticket_id):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")

    ticket = get_object_or_404(SupportTicket, id=ticket_id, submitted_by=request.user)

    if ticket.status != 'OPEN':
        messages.error(request, "This ticket is already being handled and can no longer be edited.")
        return redirect("Student:my_support_tickets", uuid=uuid)

    if request.method == "POST":
        subject = request.POST.get("subject", "").strip()
        description = request.POST.get("description", "").strip()
        priority = request.POST.get("priority", "MEDIUM")

        if not subject:
            messages.error(request, "Subject is required.")
            return redirect("Student:edit_support_ticket", uuid=uuid, ticket_id=ticket_id)
        
        # Store old values for audit log
        before_data = {
            "subject": ticket.subject,
            "description": ticket.description,
            "priority": ticket.priority,
            "status": ticket.status,
        }

        ticket.subject = subject
        ticket.description = description
        ticket.priority = priority
        ticket.save()
        
        # Store new values
        after_data = {
            "subject": ticket.subject,
            "description": ticket.description,
            "priority": ticket.priority,
            "status": ticket.status,
        }

        # Audit log
        AuditLogger.log(
            request=request,
            action="UPDATE",
            module="Support Tickets",
            object_type="SupportTicket",
            object_id=ticket.id,
            description=(
                f"Student '{request.user.username}' updated support ticket "
                f"'{ticket.subject}'."
            ),
            before_data=before_data,
            after_data=after_data,
            user=request.user,
        )
        
        messages.success(request, "Ticket updated.")
        return redirect("Student:my_support_tickets", uuid=uuid)

    context = {"ticket": ticket, "priority_choices": SupportTicket.PRIORITY_CHOICES}
    return render(request, "Academic/edit_ticket.html", context)

from django.http import JsonResponse

@login_required
def ticket_detail(request, uuid, ticket_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    ticket = get_object_or_404(SupportTicket, id=ticket_id, submitted_by=request.user)
    
    AuditLogger.log(
        request=request,
        action="VIEW",
        module="Support Tickets",
        object_type="SupportTicket",
        object_id=ticket.id,
        description=(
            f"Student '{request.user.username}' viewed support ticket "
            f"'{ticket.subject}'."
        ),
        user=request.user,
    )

    return JsonResponse({
        "success": True,
        "data": {
            "id": ticket.id,
            "subject": ticket.subject,
            "description": ticket.description,
            "priority": ticket.priority,
            "priority_display": ticket.get_priority_display(),
            "status": ticket.status,
            "status_display": ticket.get_status_display(),
            "course": ticket.course_section.course.course_code if ticket.course_section else None,
        }
    })


@login_required
def update_ticket(request, uuid, ticket_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid method"}, status=405)

    ticket = get_object_or_404(SupportTicket, id=ticket_id, submitted_by=request.user)

    if ticket.status != "OPEN":
        return JsonResponse({"success": False, "error": "This ticket can no longer be edited."}, status=400)

    import json
    payload = json.loads(request.body)
    subject = payload.get("subject", "").strip()

    if not subject:
        return JsonResponse({"success": False, "error": "Subject is required."}, status=400)
    
    # -------------------------------
    # Capture BEFORE data
    # -------------------------------
    before_data = {
        "subject": ticket.subject,
        "description": ticket.description,
        "priority": ticket.priority,
        "status": ticket.status,
    }

    ticket.subject = subject
    ticket.description = payload.get("description", "").strip()
    ticket.priority = payload.get("priority", ticket.priority)
    ticket.save()
    
    # -------------------------------
    # Capture AFTER data
    # -------------------------------
    after_data = {
        "subject": ticket.subject,
        "description": ticket.description,
        "priority": ticket.priority,
        "status": ticket.status,
    }
    
    # -------------------------------
    # Audit Log
    # -------------------------------
    AuditLogger.log(
        request=request,
        action="UPDATE",
        module="Support Tickets",
        object_type="SupportTicket",
        object_id=ticket.id,
        description=(
            f"Student '{request.user.username}' updated support ticket "
            f"'{ticket.subject}' via AJAX."
        ),
        before_data=before_data,
        after_data=after_data,
        user=request.user,
    )

    return JsonResponse({"success": True})

# ****************************************************** Ticket students ************************************************


# ****************************************************** Notification  ************************************************

from collections import OrderedDict
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from Staff.models import Notification


def _group_label_for_date(n_date, today, yesterday, week_start):
    if n_date == today:
        return "Today"
    elif n_date == yesterday:
        return "Yesterday"
    elif n_date >= week_start:
        return "This Week"
    elif n_date.year == today.year:
        return n_date.strftime("%B %Y")
    else:
        return n_date.strftime("%B %Y, %Y")


@login_required
def student_notification_history(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")

    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")

    paginator = Paginator(notifications, 10)   
    page_obj = paginator.get_page(1)

    today = timezone.localdate()
    yesterday = today - timedelta(days=1)
    week_start = today - timedelta(days=7)

    groups = OrderedDict()
    for n in page_obj.object_list:
        n_date = timezone.localtime(n.created_at).date()
        label = _group_label_for_date(n_date, today, yesterday, week_start)
        groups.setdefault(label, []).append(n)

    context = {
        "user": request.user,
        "grouped_notifications": groups,
        "unread_count": notifications.filter(is_read=False).count(),
        "total_count": notifications.count(),
        "current_page": page_obj.number,
        "total_pages": paginator.num_pages,
        "has_next": page_obj.has_next(),
        "has_previous": page_obj.has_previous(),
    }
    return render(request, "Academic/notification_history.html", context)


# ****************************************************** Notification  ************************************************



import json
import logging
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q, Max
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from Admin.models import User
from Staff.models import (
    MessageThread,
    Message,
    MessageRecipient,
    Announcement,
    MessageAttachment,
)

logger = logging.getLogger(__name__)

STUDENT_TEMPLATE = "communications.html"

AVATAR_PALETTE = [
    "#2563eb", "#16a34a", "#7c3aed", "#d97706", "#be185d", "#0891b2",
]

from Staff.models import MessageAttachment

ALLOWED_ATTACHMENT_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "video/mp4", "video/quicktime", "video/webm",
    "application/pdf",
}
MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024
MAX_ATTACHMENTS_PER_MESSAGE = 5


def save_attachments(message, files):
    """files = request.FILES.getlist('attachments')"""
    saved = []
    for f in files[:MAX_ATTACHMENTS_PER_MESSAGE]:
        if f.size > MAX_ATTACHMENT_SIZE:
            continue
        if f.content_type not in ALLOWED_ATTACHMENT_TYPES:
            continue
        att = MessageAttachment.objects.create(
            message=message,
            file=f,
            original_name=f.name,
            content_type=f.content_type,
            size=f.size,
        )
        saved.append(att)
    return saved


def serialize_attachments(message):
    return [
        {
            "id": a.id,
            "url": a.file.url,
            "name": a.original_name,
            "content_type": a.content_type,
            "size": a.size,
            "is_image": a.is_image(),
            "is_video": a.is_video(),
        }
        for a in message.attachments.all()
    ]

def _avatar_color(seed_text):
    idx = sum(ord(c) for c in (seed_text or "?")) % len(AVATAR_PALETTE)
    return AVATAR_PALETTE[idx]


def _initials(full_name):
    parts = (full_name or "").split()
    letters = "".join(p[0] for p in parts[:2]).upper()
    return letters or "?"

def _role_label(u):
    if getattr(u, "is_faculty", False):
        return "Faculty"
    if hasattr(u, "staff_profile"):
        return "Staff"
    if getattr(u, "is_student", False):
        return "Student"
    return "Admin"

def _other_party_for_thread(thread, current_user, last_msg):
    if last_msg.sender_id == current_user.id:
        recip = last_msg.recipients.exclude(recipient=current_user).first()
        return recip.recipient if recip else None
    return last_msg.sender

def _build_thread_row(thread, current_user, last_msg, is_archived=False):
    other = _other_party_for_thread(thread, current_user, last_msg)
    other_name = other.get_full_name() if other else "Unknown"
    is_sent_by_me = last_msg.sender_id == current_user.id

    my_recipient_row = None
    if not is_sent_by_me:
        my_recipient_row = last_msg.recipients.filter(recipient=current_user).first()
    unread = bool(my_recipient_row and not my_recipient_row.is_read)

    if is_archived:
        kind = "archived"
    elif is_sent_by_me:
        kind = "sent"
    elif unread:
        kind = "unread"
    else:
        kind = "all"

    avatar_photo = None

    if other and other.profile_photo:
        avatar_photo = other.profile_photo.url

    return {
        "thread_id": thread.id,
        "subject": thread.subject,
        "preview": (last_msg.body or "")[:140],
        "sender_display": f"To: {other_name}" if is_sent_by_me else other_name,

        "avatar_photo": avatar_photo,
        "avatar_bg": _avatar_color(other_name),
        "avatar_letter": _initials(other_name),

        "time": timezone.localtime(last_msg.sent_at).strftime("%b %d, %Y")
                if timezone.localdate(last_msg.sent_at) != timezone.localdate()
                else timezone.localtime(last_msg.sent_at).strftime("%I:%M %p").lstrip("0"),

        "unread": unread,
        "is_sent": is_sent_by_me,
        "is_archived": is_archived,
        "kind": kind,
    }

@login_required
def student_communications(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")

    user = request.user

    from Students.models import StudentOrgMessageThread

    org_thread_ids = StudentOrgMessageThread.objects.values_list("thread_id", flat=True)

    threads_qs = (
        MessageThread.objects
        .filter(is_announcement=False)
        .filter(Q(messages__sender=user) | Q(messages__recipients__recipient=user))
        .exclude(id__in=org_thread_ids)
        .distinct()
        .annotate(last_sent=Max("messages__sent_at"))
        .order_by("-last_sent")
        .prefetch_related("messages__recipients", "messages__sender")
    )

    archived_thread_ids = set(
        MessageRecipient.objects.filter(
            recipient=user, archived=True
        ).values_list("message__thread_id", flat=True)
    )

    thread_rows = []
    unread_count = 0
    week_ago = timezone.now() - timedelta(days=7)

    for thread in threads_qs:
        last_msg = thread.last_message()
        if not last_msg:
            continue
        is_archived = thread.id in archived_thread_ids
        row = _build_thread_row(thread, user, last_msg, is_archived=is_archived)
        thread_rows.append(row)
        if row["unread"] and not is_archived:
            unread_count += 1

    sent_this_week = Message.objects.filter(sender=user, sent_at__gte=week_ago).count()
    active_count = sum(1 for r in thread_rows if not r["is_archived"])

    today = timezone.localdate()
    announcements = (
        Announcement.objects
        .filter(Q(expires_at__isnull=True) | Q(expires_at__gte=today))
        .order_by("-posted_at")[:5]
    )

    context = {
        "user": user,
        "uuid": uuid,
        "thread_rows": thread_rows,
        "announcements": announcements,
        "kpi_inbox": active_count,
        "kpi_unread": unread_count,
        "kpi_sent_week": sent_this_week,
        "kpi_announcements": announcements.count(),
    }
    return render(request, STUDENT_TEMPLATE, context)

@login_required
def student_search_recipients_ajax(request):
    q = request.GET.get("q", "").strip()

    base_qs = User.objects.exclude(id=request.user.id).exclude(is_student=True)

    if not q:
        users = base_qs.order_by("first_name", "last_name")[:15]
    else:
        users = base_qs.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q)
        )[:15]

    results = [{
        "id": u.id,
        "name": u.get_full_name() or u.email,
        "email": u.email,
        "role": _role_label(u),
    } for u in users]

    return JsonResponse({"results": results})


# ── Send new message ──────────────────────────────────────────
@login_required
@require_http_methods(["POST"])
def student_send_message_ajax(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    try:
        recipient_id = request.POST.get("recipient_id")
        subject = (request.POST.get("subject") or "").strip()
        body = (request.POST.get("body") or "").strip()
        files = request.FILES.getlist("attachments")

        if not recipient_id:
            return JsonResponse({"success": False, "error": "Please choose a recipient."}, status=400)
        if not body and not files:
            return JsonResponse({"success": False, "error": "Message body or an attachment is required."}, status=400)

        recipient = get_object_or_404(User, id=recipient_id)

        with transaction.atomic():
            thread = MessageThread.objects.create(
                subject=subject or "(No subject)",
                created_by=request.user,
            )
            message = Message.objects.create(thread=thread, sender=request.user, body=body)
            save_attachments(message, files)

            MessageRecipient.objects.create(message=message, recipient=recipient)
            MessageRecipient.objects.create(message=message, recipient=request.user, is_read=True)

        return JsonResponse({"success": True, "message": "Message sent!", "thread_id": thread.id})

    except Exception as e:
        logger.error(f"Error sending student message: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@login_required
def student_thread_detail_ajax(request, uuid, thread_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    thread = get_object_or_404(
        MessageThread.objects.filter(
            Q(messages__sender=request.user) | Q(messages__recipients__recipient=request.user)
        ).distinct(),
        id=thread_id,
    )

    messages_qs = thread.messages.select_related("sender").order_by("sent_at")

    MessageRecipient.objects.filter(
        message__thread=thread, recipient=request.user, is_read=False
    ).update(is_read=True, read_at=timezone.now())

    data = []
    for m in messages_qs:
        sender_name = m.sender.get_full_name() or m.sender.email
        data.append({
            "id": m.id,
            "sender_name": sender_name,
            "sender_role": _role_label(m.sender),
            "avatar_bg": _avatar_color(sender_name),
            "avatar_letter": _initials(sender_name),
            "is_mine": m.sender_id == request.user.id,
            "body": m.body,
            "sent_at": timezone.localtime(m.sent_at).strftime("%b %d, %Y at %I:%M %p").replace(" 0", " "),
            "attachments": serialize_attachments(m),
        })

    last_msg = messages_qs.last()
    other = _other_party_for_thread(thread, request.user, last_msg)
    other_name = other.get_full_name() if other else "Unknown"
    other_role = _role_label(other) if other else ""

    other_avatar_letter = _initials(other_name)
    other_avatar_bg = _avatar_color(other_name)

    other_avatar_photo = None

    if other and other.profile_photo:
        other_avatar_photo = other.profile_photo.url

    return JsonResponse({
        "success": True,
        "thread_id": thread.id,
        "subject": thread.subject,
        "messages": data,

        "reply_to_id": other.id if other else None,
        "reply_to_name": other_name,

        "other_name": other_name,
        "other_role": other_role,

        "other_avatar_photo": other_avatar_photo,
        "other_avatar_letter": other_avatar_letter,
        "other_avatar_bg": other_avatar_bg,
    })


@login_required
@require_http_methods(["POST"])
def student_reply_message_ajax(request):
    try:
        thread_id = request.POST.get("thread_id")
        recipient_id = request.POST.get("recipient_id")
        body = (request.POST.get("body") or "").strip()
        files = request.FILES.getlist("attachments")

        if not thread_id or not recipient_id or (not body and not files):
            return JsonResponse({"success": False, "error": "Missing required fields."}, status=400)

        thread = get_object_or_404(MessageThread, id=thread_id)
        recipient = get_object_or_404(User, id=recipient_id)

        with transaction.atomic():
            message = Message.objects.create(thread=thread, sender=request.user, body=body)
            save_attachments(message, files)

            MessageRecipient.objects.create(message=message, recipient=recipient)
            MessageRecipient.objects.create(message=message, recipient=request.user, is_read=True)

        return JsonResponse({"success": True, "message": "Reply sent!"})

    except Exception as e:
        logger.error(f"Error replying (student): {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def student_archive_thread_ajax(request, uuid, thread_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    MessageRecipient.objects.filter(
        message__thread_id=thread_id, recipient=request.user
    ).update(archived=True)

    return JsonResponse({"success": True, "message": "Thread archived."})


@login_required
@require_http_methods(["POST"])
def student_unarchive_thread_ajax(request, uuid, thread_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    MessageRecipient.objects.filter(
        message__thread_id=thread_id, recipient=request.user
    ).update(archived=False)

    return JsonResponse({"success": True, "message": "Thread moved back to inbox."})

@login_required
def student_volume_ajax(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False}, status=403)

    today = timezone.localdate()
    start_of_week = today - timedelta(days=today.weekday())

    day_labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    counts = []
    for i, label in enumerate(day_labels):
        day = start_of_week + timedelta(days=i)
        count = Message.objects.filter(sent_at__date=day).filter(
            Q(sender=request.user) | Q(recipients__recipient=request.user)
        ).distinct().count()
        counts.append({"label": label, "count": count})

    return JsonResponse({"success": True, "days": counts, "total": sum(c["count"] for c in counts)})

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from Staff.models import MessageRecipient

@login_required
def student_check_new_messages(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False}, status=403)
    from Students.models import StudentOrgMessageThread

    org_thread_ids = StudentOrgMessageThread.objects.values_list("thread_id", flat=True)

    unread = MessageRecipient.objects.filter(
        recipient=request.user,
        is_read=False,
        archived=False
    ).exclude(message__thread_id__in=org_thread_ids).count()
    return JsonResponse({
        "success": True,
        "unread_count": unread,
    })


from Staff.models import MessageThread, Message, MessageRecipient
from Students.models import StudentOrgMessageThread


def get_or_create_org_thread(org, creator):
    link, created = StudentOrgMessageThread.objects.get_or_create(
        organization=org,
        defaults={
            "thread": MessageThread.objects.create(
                subject=f"{org.organization_name} — Group Chat",
                created_by=creator,
            )
        }
    )
    return link.thread


@login_required
def student_org_chat_messages_ajax(request, uuid, org_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    membership = get_object_or_404(
        StudentOrganizationMembership,
        organization_id=org_id,
        student__user=request.user,
        status="ACTIVE"
    )
    org = membership.organization
    thread = get_or_create_org_thread(org, request.user)

    messages = Message.objects.filter(thread=thread).select_related("sender").order_by("sent_at")

    MessageRecipient.objects.filter(
        message__thread=thread, recipient=request.user, is_read=False
    ).update(is_read=True)

    return JsonResponse({
        "success": True,
        "org_name": org.organization_name,
        "messages": [
            {
                "id": m.id,
                "sender_name": m.sender.get_full_name() or m.sender.email,
                "sender_photo": (
                    m.sender.faculty_profile.profile_photo.url
                    if hasattr(m.sender, "faculty_profile") and m.sender.faculty_profile.profile_photo
                    else None
                ),
                "is_me": m.sender_id == request.user.id,
                "body": m.body,
                "sent_at": m.sent_at.isoformat(),
            }
            for m in messages
        ],
    })

@login_required
@require_http_methods(["POST"])
def student_org_chat_send_ajax(request, uuid, org_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    membership = get_object_or_404(
        StudentOrganizationMembership,
        organization_id=org_id,
        student__user=request.user,
        status="ACTIVE"
    )
    org = membership.organization

    body = (request.POST.get("body") or "").strip()
    if not body:
        return JsonResponse({"success": False, "error": "Message cannot be empty."})
    if len(body) > 1000:
        return JsonResponse({"success": False, "error": "Message is too long (max 1000 characters)."})

    thread = get_or_create_org_thread(org, request.user)

    with transaction.atomic():
        message = Message.objects.create(thread=thread, sender=request.user, body=body)
        MessageRecipient.objects.create(message=message, recipient=request.user, is_read=True)

        other_recipients = set()
        if org.advisor and org.advisor.user_id != request.user.id:
            other_recipients.add(org.advisor.user)

        other_members = StudentOrganizationMembership.objects.filter(
            organization=org, status="ACTIVE"
        ).exclude(student__user=request.user).select_related("student__user")

        for m in other_members:
            other_recipients.add(m.student.user)

        for u in other_recipients:
            MessageRecipient.objects.create(message=message, recipient=u)

    return JsonResponse({"success": True})


# *************************************** Arun Code ********************************************************** 


#<----------------------Blaze Code Start Student Leave Req(25.07.26)-------------------------->

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Sum, Count
from datetime import datetime, timedelta
import json
import csv
import base64
from django.core.files.base import ContentFile
from .models import StudentLeaveRequest, StudentLeaveType, StudentLeaveBalance

@login_required
def student_leave_dashboard(request, uuid):
    """Main student leave dashboard with stats and analytics"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Access denied. Student only.')
        return redirect('student_dashboard', uuid=uuid)
    
    # Auto-create leave types if not exists
    default_leave_types = [
        {'name': 'Annual Leave', 'code': 'ANNUAL', 'max_days_per_year': 30, 'color': '#3b82f6'},
        {'name': 'Sick Leave', 'code': 'SICK', 'max_days_per_year': 15, 'color': '#22c55e'},
        {'name': 'Casual Leave', 'code': 'CASUAL', 'max_days_per_year': 10, 'color': '#f59e0b'},
        {'name': 'Earned Leave', 'code': 'EARNED', 'max_days_per_year': 5, 'color': '#8b5cf6'},
        {'name': 'Compensatory Leave', 'code': 'COMP', 'max_days_per_year': 5, 'color': '#ec4899'},
        {'name': 'Unpaid Leave', 'code': 'UNPAID', 'max_days_per_year': 0, 'color': '#6b7280'},
    ]
    
    for lt in default_leave_types:
        StudentLeaveType.objects.get_or_create(
            code=lt['code'],
            defaults={
                'name': lt['name'],
                'max_days_per_year': lt['max_days_per_year'],
                'color': lt['color'],
                'is_paid': lt['code'] != 'UNPAID',
                'is_half_day_allowed': lt['code'] != 'UNPAID',
                'is_full_crud': True
            }
        )
    
    leave_types = StudentLeaveType.objects.all()
    leave_requests = StudentLeaveRequest.objects.filter(student=request.user).order_by('-created_at')
    
    # Get leave balance
    balance, created = StudentLeaveBalance.objects.get_or_create(
        student=request.user,
        defaults={
            'annual_leave_balance': 30.0,
            'sick_leave_balance': 15.0,
            'casual_leave_balance': 10.0,
            'earned_leave_balance': 0.0,
            'compensatory_leave_balance': 0.0,
        }
    )
    
    # Statistics
    total_leaves = leave_requests.count()
    pending_leaves = leave_requests.filter(status='pending').count()
    approved_leaves = leave_requests.filter(status='approved').count()
    rejected_leaves = leave_requests.filter(status='rejected').count()
    cancelled_leaves = leave_requests.filter(status='cancelled').count()
    
    # Current year usage
    current_year = timezone.now().year
    year_leaves = leave_requests.filter(
        start_date__year=current_year,
        status__in=['approved']
    )
    
    # Calculate days used
    year_days_used = 0
    for leave in year_leaves:
        year_days_used += leave.days_count
    
    # Analytics data - Monthly usage
    monthly_data = []
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for month in range(1, 13):
        month_leaves = StudentLeaveRequest.objects.filter(
            student=request.user,
            start_date__year=current_year,
            start_date__month=month,
            status__in=['approved']
        )
        total_days = 0
        for leave in month_leaves:
            total_days += leave.days_count
        monthly_data.append(float(total_days))
    
    # Leave type distribution
    type_distribution = []
    for leave_type in leave_types:
        count = StudentLeaveRequest.objects.filter(
            student=request.user,
            leave_type=leave_type,
            status__in=['approved']
        ).count()
        if count > 0:
            type_distribution.append({
                'leave_type__name': leave_type.name,
                'leave_type__color': leave_type.color,
                'count': count,
            })
    
    type_labels = [item['leave_type__name'] for item in type_distribution]
    type_counts = [item['count'] for item in type_distribution]
    type_colors = [item['leave_type__color'] for item in type_distribution]
    
    context = {
        'leave_types': leave_types,
        'leave_requests': leave_requests,
        'leave_balance': balance,
        'today': timezone.now().date(),
        'uuid': uuid,
        'total_leaves': total_leaves,
        'pending_leaves': pending_leaves,
        'approved_leaves': approved_leaves,
        'rejected_leaves': rejected_leaves,
        'cancelled_leaves': cancelled_leaves,
        'year_days_used': year_days_used,
        'current_year': current_year,
        'monthly_data': json.dumps(monthly_data),
        'months': json.dumps(months),
        'type_labels': json.dumps(type_labels),
        'type_counts': json.dumps(type_counts),
        'type_colors': json.dumps(type_colors),
    }
    return render(request, 'Student_Leave/leave_dashboard.html', context)


@login_required
def submit_student_leave(request, uuid):
    """Submit new student leave request with attachment"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        
        leave_type_id = data.get('leave_type')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        half_day = data.get('half_day', 'full')
        reason = data.get('reason')
        attachment_data = data.get('attachment', None)
        attachment_name = data.get('attachment_name', '')
        
        # Validate required fields
        if not leave_type_id:
            return JsonResponse({'success': False, 'message': 'Please select a leave type'})
        if not start_date:
            return JsonResponse({'success': False, 'message': 'Please select a start date'})
        if not end_date:
            return JsonResponse({'success': False, 'message': 'Please select an end date'})
        if not reason or not reason.strip():
            return JsonResponse({'success': False, 'message': 'Please provide a reason for your leave'})
        
        leave_type = get_object_or_404(StudentLeaveType, id=leave_type_id)
        
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if start > end:
            return JsonResponse({'success': False, 'message': 'Start date cannot be after end date'})
        
        if start < timezone.now().date():
            return JsonResponse({'success': False, 'message': 'Cannot request leave for past dates'})
        
        # Check overlapping
        overlapping = StudentLeaveRequest.objects.filter(
            student=request.user,
            status__in=['pending', 'approved'],
            start_date__lte=end,
            end_date__gte=start
        ).exists()
        
        if overlapping:
            return JsonResponse({'success': False, 'message': 'You already have a leave request for these dates'})
        
        # Create leave request
        leave_request = StudentLeaveRequest.objects.create(
            student=request.user,
            leave_type=leave_type,
            start_date=start,
            end_date=end,
            half_day_type=half_day,
            reason=reason.strip(),
            status='pending'
        )
        
        # ==========================================
        # AUDIT LOG — STUDENT LEAVE REQUEST CREATED
        # ==========================================
        AuditLogger.log(
            request=request,
            action="REQUEST",
            module="Student Leave",
            object_type="StudentLeaveRequest",
            object_id=leave_request.id,
            description=(
                f"Student '{request.user.username}' submitted a "
                f"{leave_type.name} leave request "
                f"from {start} to {end}."
            ),
            after_data=AuditLogger.model_to_dict(
                leave_request,
                [
                    "id",
                    "start_date",
                    "end_date",
                    "half_day_type",
                    "reason",
                    "status",
                ]
            ),
            status="SUCCESS",
            user=request.user,
        )


        from Staff.utils import notify_staff_new_leave_request
        notify_staff_new_leave_request(leave_request)
        
        # Handle attachment if provided
        if attachment_data and attachment_name:
            try:
                format, imgstr = attachment_data.split(';base64,')
                ext = format.split('/')[-1]
                filename = f"{leave_request.id}_{attachment_name}"
                data_file = ContentFile(base64.b64decode(imgstr), name=filename)
                leave_request.attachment = data_file
                leave_request.attachment_name = attachment_name
                leave_request.save()
                
                AuditLogger.log(
                    request=request,
                    action="UPLOAD",
                    module="Student Leave",
                    object_type="LeaveAttachment",
                    object_id=leave_request.id,
                    description=(
                        f"Student '{request.user.username}' uploaded attachment "
                        f"'{attachment_name}' for leave request #{leave_request.id}."
                    ),
                    after_data={
                        "leave_request_id": leave_request.id,
                        "attachment_name": attachment_name,
                    },
                    user=request.user,
                )
            except Exception as e:
                print(f"Attachment error: {e}")
        
        return JsonResponse({
            'success': True,
            'message': 'Leave request submitted successfully!',
            'leave_id': leave_request.id,
            'leave': {
                'id': leave_request.id,
                'type': leave_request.leave_type.name,
                'start_date': leave_request.start_date.strftime('%b %d, %Y'),
                'end_date': leave_request.end_date.strftime('%b %d, %Y'),
                'days': leave_request.days_count,
                'status': leave_request.status,
                'half_day': leave_request.half_day_type,
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def cancel_student_leave(request, uuid, leave_id):
    """Cancel a pending student leave request"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        leave = get_object_or_404(StudentLeaveRequest, id=leave_id, student=request.user)
        
        if leave.status != 'pending':
            return JsonResponse({'success': False, 'message': 'Only pending requests can be cancelled'})
        
        # ==========================================
        # AUDIT LOG — CAPTURE OLD STATUS
        # ==========================================
        before_data = {
            "status": leave.status,
            "leave_type": leave.leave_type.name if leave.leave_type else None,
            "start_date": leave.start_date.isoformat() if leave.start_date else None,
            "end_date": leave.end_date.isoformat() if leave.end_date else None,
        }
        
        leave.status = 'cancelled'
        leave.save()
        
        # ==========================================
        # AUDIT LOG — STUDENT CANCELLED LEAVE
        # ==========================================
        after_data = {
            "status": leave.status,
            "leave_type": leave.leave_type.name if leave.leave_type else None,
            "start_date": leave.start_date.isoformat() if leave.start_date else None,
            "end_date": leave.end_date.isoformat() if leave.end_date else None,
        }

        AuditLogger.log(
            request=request,
            action="CANCEL",
            module="Student Leave",
            object_type="StudentLeaveRequest",
            object_id=leave.id,
            description=(
                f"Student '{request.user.username}' cancelled leave request "
                f"#{leave.id}."
            ),
            before_data=before_data,
            after_data=after_data,
            status="SUCCESS",
            user=request.user,
        )
        
        return JsonResponse({'success': True, 'message': 'Leave request cancelled successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def get_student_leave_details(request, uuid, leave_id):
    """Get student leave request details for editing"""
    try:
        leave = get_object_or_404(StudentLeaveRequest, id=leave_id, student=request.user)
        
        if leave.status != 'pending':
            return JsonResponse({
                'success': False, 
                'message': 'Only pending requests can be edited'
            })
        
        data = {
            'id': leave.id,
            'leave_type': leave.leave_type_id,
            'start_date': leave.start_date.strftime('%Y-%m-%d'),
            'end_date': leave.end_date.strftime('%Y-%m-%d'),
            'half_day': leave.half_day_type,
            'reason': leave.reason,
            'status': leave.status,
            'days_count': leave.days_count,
        }
        return JsonResponse({'success': True, 'data': data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def update_student_leave(request, uuid, leave_id):
    """Update a pending student leave request"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        leave = get_object_or_404(StudentLeaveRequest, id=leave_id, student=request.user)
        
        if leave.status != 'pending':
            return JsonResponse({'success': False, 'message': 'Only pending requests can be updated'})
        
        data = json.loads(request.body)
        
        leave_type_id = data.get('leave_type')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        half_day = data.get('half_day', 'full')
        reason = data.get('reason')
        
        # Validate required fields
        if not leave_type_id:
            return JsonResponse({'success': False, 'message': 'Please select a leave type'})
        if not start_date:
            return JsonResponse({'success': False, 'message': 'Please select a start date'})
        if not end_date:
            return JsonResponse({'success': False, 'message': 'Please select an end date'})
        if not reason or not reason.strip():
            return JsonResponse({'success': False, 'message': 'Please provide a reason for your leave'})
        
        leave_type = get_object_or_404(StudentLeaveType, id=leave_type_id)
        
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if start > end:
            return JsonResponse({'success': False, 'message': 'Start date cannot be after end date'})
        
        overlapping = StudentLeaveRequest.objects.filter(
            student=request.user,
            status__in=['pending', 'approved'],
            start_date__lte=end,
            end_date__gte=start
        ).exclude(id=leave_id).exists()
        
        if overlapping:
            return JsonResponse({'success': False, 'message': 'You already have a leave request for these dates'})
        
        
        # ==========================================
        # AUDIT LOG — CAPTURE OLD DATA
        # ==========================================
        before_data = {
            "leave_type": leave.leave_type.name if leave.leave_type else None,
            "start_date": leave.start_date.isoformat() if leave.start_date else None,
            "end_date": leave.end_date.isoformat() if leave.end_date else None,
            "half_day_type": leave.half_day_type,
            "reason": leave.reason,
            "status": leave.status,
        }
        
        leave.leave_type = leave_type
        leave.start_date = start
        leave.end_date = end
        leave.half_day_type = half_day
        leave.reason = reason.strip()
        leave.save()
        
        
        # ==========================================
        # AUDIT LOG — STUDENT LEAVE UPDATED
        # ==========================================
        after_data = {
            "leave_type": leave.leave_type.name if leave.leave_type else None,
            "start_date": leave.start_date.isoformat() if leave.start_date else None,
            "end_date": leave.end_date.isoformat() if leave.end_date else None,
            "half_day_type": leave.half_day_type,
            "reason": leave.reason,
            "status": leave.status,
        }

        AuditLogger.log(
            request=request,
            action="UPDATE",
            module="Student Leave",
            object_type="StudentLeaveRequest",
            object_id=leave.id,
            description=(
                f"Student '{request.user.username}' updated leave request "
                f"#{leave.id}."
            ),
            before_data=before_data,
            after_data=after_data,
            status="SUCCESS",
            user=request.user,
        )
        
        return JsonResponse({
            'success': True, 
            'message': 'Leave request updated successfully!',
            'leave': {
                'id': leave.id,
                'type': leave.leave_type.name,
                'start_date': leave.start_date.strftime('%b %d, %Y'),
                'end_date': leave.end_date.strftime('%b %d, %Y'),
                'days': leave.days_count,
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def get_student_leave_balance(request, uuid):
    """Get student leave balance"""
    try:
        balance, created = StudentLeaveBalance.objects.get_or_create(
            student=request.user,
            defaults={
                'annual_leave_balance': 30.0,
                'sick_leave_balance': 15.0,
                'casual_leave_balance': 10.0,
                'earned_leave_balance': 0.0,
                'compensatory_leave_balance': 0.0,
            }
        )
        data = {
            'annual_leave': balance.annual_leave_balance,
            'sick_leave': balance.sick_leave_balance,
            'casual_leave': balance.casual_leave_balance,
            'earned_leave': balance.earned_leave_balance,
            'compensatory_leave': balance.compensatory_leave_balance,
        }
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def export_student_leave_report(request, uuid):
    """Export student leave report as CSV"""
    try:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="student_leave_report_{}.csv"'.format(
            timezone.now().strftime('%Y%m%d')
        )
        
        writer = csv.writer(response)
        writer.writerow([
            'S.No', 'Leave Type', 'Start Date', 'End Date', 
            'Days', 'Half Day', 'Reason', 'Status', 
            'Submitted On', 'Approved On'
        ])
        
        leaves = StudentLeaveRequest.objects.filter(student=request.user).order_by('-created_at')
        for idx, leave in enumerate(leaves, 1):
            writer.writerow([
                idx,
                leave.leave_type.name,
                leave.start_date.strftime('%Y-%m-%d'),
                leave.end_date.strftime('%Y-%m-%d'),
                leave.days_count,
                leave.get_half_day_type_display(),
                leave.reason[:100] if leave.reason else '',
                leave.get_status_display(),
                leave.created_at.strftime('%Y-%m-%d %H:%M'),
                leave.approved_date.strftime('%Y-%m-%d %H:%M') if leave.approved_date else '',
            ])
            
        AuditLogger.log(
            request=request,
            action="EXPORT",
            module="Student Leave",
            object_type="StudentLeaveReport",
            object_id=str(request.user.id),
            description=(
                f"Student '{request.user.username}' exported "
                f"their student leave report as CSV."
            ),
            after_data={
                "format": "CSV",
                "total_leave_records": leaves.count(),
                "exported_at": timezone.now().isoformat(),
            },
            user=request.user,
        )
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error exporting report: {str(e)}')
        return redirect('Student:student_leave_dashboard', uuid=uuid)


#<----------------------Blaze Code End(25.07.26)--------------------------->



@login_required
def student_downloads(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")

    resources_qs = Resource.objects.filter(visible_to_students=True)

    search_query = request.GET.get('search', '').strip()
    type_filter = request.GET.get('type', 'all')

    if search_query:
        resources_qs = resources_qs.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
    if type_filter != 'all':
        resources_qs = resources_qs.filter(resource_type=type_filter)

    alerts_ctx = get_resource_alerts_context(request.user, "visible_to_students")
    mark_resource_alerts_seen(request.user)

    context = {
        "user": request.user,
        "resources": resources_qs,
        "search_query": search_query,
        "type_filter": type_filter,
        **alerts_ctx,
    }
    return render(request, "Academic/student_downloads.html", context)


@login_required
def student_download_resource(request, uuid, resource_id):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")

    resource = get_object_or_404(Resource, id=resource_id, visible_to_students=True)

    if not resource.file or not default_storage.exists(resource.file.name):
        
        # log failed download attempt
        AuditLogger.log(
            request=request,
            action="DOWNLOAD",
            module="Student Downloads",
            object_type="Resource",
            object_id=resource.id,
            description=(
                f"Student '{request.user.username}' attempted to download "
                f"resource '{resource.title}', but the file was not found."
            ),
            status="FAILED",
            after_data={
                "resource_id": resource.id,
                "resource_title": resource.title,
                "file_name": resource.file.name if resource.file else None,
                "reason": "File not found",
            },
            user=request.user,
        )
        
        raise Http404("File not found")
    
    # Store count before download
    previous_download_count = resource.download_count

    resource.download_count += 1
    resource.save(update_fields=["download_count"])
    
    # Audit successful download
    AuditLogger.log(
        request=request,
        action="DOWNLOAD",
        module="Student Downloads",
        object_type="Resource",
        object_id=resource.id,
        description=(
            f"Student '{request.user.username}' downloaded "
            f"resource '{resource.title}'."
        ),
        before_data={
            "download_count": previous_download_count,
        },
        after_data={
            "resource_id": resource.id,
            "resource_title": resource.title,
            "resource_type": getattr(resource, "resource_type", None),
            "file_name": os.path.basename(resource.file.name),
            "download_count": resource.download_count,
        },
        status="SUCCESS",
        user=request.user,
    )

    return FileResponse(
        resource.file.open("rb"), as_attachment=True,
        filename=os.path.basename(resource.file.name),
    )