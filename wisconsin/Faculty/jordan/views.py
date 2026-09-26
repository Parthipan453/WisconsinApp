from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
from django.db.models import Q, Sum, Count, Avg
from datetime import datetime, timedelta
import calendar
import json
from decimal import Decimal
import pandas as pd
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from Faculty.models import FacultyProfile, Department
from Staff.Eric.models import FacultyAttendanceRecord
import re
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import logging
import os
from mimetypes import guess_type
from urllib.parse import quote
from Research.models import StudentResearchApplication
from Students.models import StudentProfile

def own_faculty_attendance(request, uuid):
    faculty = get_object_or_404(FacultyProfile, user__uuid=uuid)
    today = datetime.now().date()

    # Get filter parameters
    month_filter = request.GET.get('month', '')
    status_filter = request.GET.get('status', '')
    day_of_week_filter = request.GET.get('day_of_week', '')
    year_filter = request.GET.get('year', '')
    search_query = request.GET.get('search', '').strip()
    export_type = request.GET.get('export', '')
    is_ajax = request.GET.get('ajax', False)
    page_number = request.GET.get('page', 1)

    # ============================================================
    # OVERALL STATISTICS - Get ALL records without any filters
    # ============================================================
    base_queryset = FacultyAttendanceRecord.objects.filter(
        faculty=faculty
    ).select_related('faculty__user')

    # Overall statistics from ALL records
    overall_total = base_queryset.count()
    overall_present = base_queryset.filter(status='PRESENT').count()
    overall_absent = base_queryset.filter(status='ABSENT').count()
    overall_late = base_queryset.filter(status='LATE').count()
    overall_halfday = base_queryset.filter(status='HALF_DAY').count()
    overall_leave = base_queryset.filter(status='ON_LEAVE').count()
    overall_holiday = base_queryset.filter(status='HOLIDAY').count()

    # Calculate overall average working hours
    overall_working_hours = base_queryset.exclude(
        status__in=['ABSENT', 'ON_LEAVE', 'HOLIDAY']
    ).exclude(total_hours_worked__isnull=True).values_list('total_hours_worked', flat=True)
    
    overall_avg_hours = 0
    if overall_working_hours:
        overall_avg_hours = round(sum(overall_working_hours) / len(overall_working_hours), 1)

    # ============================================================
    # FILTERED STATISTICS - Apply filters for table data
    # ============================================================
    attendance_queryset = base_queryset

    # Apply Year filter
    if year_filter:
        try:
            year = int(year_filter)
            attendance_queryset = attendance_queryset.filter(date__year=year)
        except:
            pass

    # Apply Month filter
    if month_filter:
        try:
            month = int(month_filter)
            attendance_queryset = attendance_queryset.filter(date__month=month)
        except:
            pass

    # Apply Day of Week filter
    # Django week_day: Sunday=1, Monday=2, Tuesday=3, Wednesday=4, Thursday=5, Friday=6, Saturday=7
    if day_of_week_filter:
        day_map = {
            'Monday': 2,
            'Tuesday': 3,
            'Wednesday': 4,
            'Thursday': 5,
            'Friday': 6,
            'Saturday': 7,
            'Sunday': 1
        }
        day_num = day_map.get(day_of_week_filter)
        if day_num:
            attendance_queryset = attendance_queryset.filter(date__week_day=day_num)

    # Apply Status filter
    if status_filter:
        status_mapping = {
            'present': 'PRESENT',
            'absent': 'ABSENT',
            'late': 'LATE',
            'half-day': 'HALF_DAY',
            'leave': 'ON_LEAVE',
            'holiday': 'HOLIDAY'
        }
        db_status = status_mapping.get(status_filter.lower(), status_filter.upper())
        attendance_queryset = attendance_queryset.filter(status=db_status)

    # Apply Search filter
    if search_query:
        search_conditions = Q()
        search_lower = search_query.lower()
        
        # Try to parse as date
        search_date = None
        date_formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', 
            '%d %m %Y', '%d/%m/%y', '%d-%m-%y',
            '%m/%d/%Y', '%m-%d-%Y'
        ]
        
        for fmt in date_formats:
            try:
                search_date = datetime.strptime(search_query, fmt).date()
                break
            except ValueError:
                continue
        
        if search_date:
            search_conditions |= Q(date=search_date)
        
        # Search in notes
        search_conditions |= Q(notes__icontains=search_query)
        
        # Search by day number
        try:
            day_num = int(search_query)
            if 1 <= day_num <= 31:
                search_conditions |= Q(date__day=day_num)
        except ValueError:
            pass
        
        # Search by status name
        status_search_map = {
            'present': 'PRESENT',
            'absent': 'ABSENT',
            'late': 'LATE',
            'half': 'HALF_DAY',
            'halfday': 'HALF_DAY',
            'half-day': 'HALF_DAY',
            'leave': 'ON_LEAVE',
            'holiday': 'HOLIDAY',
            'on leave': 'ON_LEAVE',
            'on_leave': 'ON_LEAVE'
        }
        
        for key, value in status_search_map.items():
            if key in search_lower:
                search_conditions |= Q(status=value)
                break
        
        # Apply search conditions
        if search_conditions:
            attendance_queryset = attendance_queryset.filter(search_conditions)

    # Order by date descending
    attendance_queryset = attendance_queryset.order_by('-date')
    
    # Get filtered records for stats
    all_records = attendance_queryset
    
    # Calculate filtered statistics
    total_days = all_records.count()
    present_days = all_records.filter(status='PRESENT').count()
    absent_days = all_records.filter(status='ABSENT').count()
    late_days = all_records.filter(status='LATE').count()
    halfday_days = all_records.filter(status='HALF_DAY').count()
    leave_days = all_records.filter(status='ON_LEAVE').count()
    holiday_days = all_records.filter(status='HOLIDAY').count()
    
    # Calculate average working hours for filtered data
    working_hours_list = all_records.exclude(
        status__in=['ABSENT', 'ON_LEAVE', 'HOLIDAY']
    ).exclude(total_hours_worked__isnull=True).values_list('total_hours_worked', flat=True)
    
    avg_hours = 0
    if working_hours_list:
        avg_hours = round(sum(working_hours_list) / len(working_hours_list), 1)
    
    # Calculate percentages
    present_percentage = round((present_days / total_days * 100), 1) if total_days > 0 else 0
    absent_percentage = round((absent_days / total_days * 100), 1) if total_days > 0 else 0
    late_percentage = round((late_days / total_days * 100), 1) if total_days > 0 else 0
    halfday_percentage = round((halfday_days / total_days * 100), 1) if total_days > 0 else 0
    
    # Today's record
    today_record = all_records.filter(date=today).first()
    if today_record:
        today_login = today_record.check_in.strftime('%I:%M %p') if today_record.check_in else "Not Checked In"
        today_logout = today_record.check_out.strftime('%I:%M %p') if today_record.check_out else "Not Checked Out"
        today_hours = f"{today_record.total_hours_worked:.2f}h" if today_record.total_hours_worked else "-"
        today_status = today_record.get_status_display().lower()
    else:
        today_login = "Not Logged In"
        today_logout = "Not Logged Out"
        today_hours = "-"
        today_status = "absent"
    
    # Get ALL records for the month (complete data)
    all_records_list = []
    for record in all_records:
        all_records_list.append({
            'id': record.id,
            'date': record.date.strftime('%d/%m/%Y'),
            'date_raw': record.date.isoformat(),
            'day': record.date.strftime('%A'),
            'day_short': record.date.strftime('%a'),
            'login': record.check_in.strftime('%I:%M %p') if record.check_in else '-',
            'logout': record.check_out.strftime('%I:%M %p') if record.check_out else '-',
            'hours': round(float(record.total_hours_worked), 2) if record.total_hours_worked else 0,
            'status': record.get_status_display().lower(),
            'status_display': record.get_status_display(),
            'notes': getattr(record, 'notes', '') or '',
            'month': record.date.month,
            'year': record.date.year,
            'week_number': record.date.isocalendar()[1],
            'late_minutes': record.late_minutes or 0,
            'early_leave_minutes': record.early_leave_minutes or 0,
            'week_day': record.date.weekday() + 1,  # Monday=1, Sunday=7
        })
    
    # Pagination - 10 items per page
    paginator = Paginator(all_records, 10)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Prepare paginated data
    attendance_list = []
    for record in page_obj:
        attendance_list.append({
            'id': record.id,
            'date': record.date.strftime('%d/%m/%Y'),
            'day': record.date.strftime('%A'),
            'login': record.check_in.strftime('%I:%M %p') if record.check_in else '-',
            'logout': record.check_out.strftime('%I:%M %p') if record.check_out else '-',
            'hours': round(float(record.total_hours_worked), 2) if record.total_hours_worked else 0,
            'status': record.get_status_display().lower(),
            'notes': getattr(record, 'notes', '') or '',
            'late_minutes': record.late_minutes or 0,
            'early_leave_minutes': record.early_leave_minutes or 0,
        })
    
    # Get weekly data (last 7 days) with status
    weekly_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        record = all_records.filter(date=date).first()
        if record and record.status not in ['ABSENT', 'ON_LEAVE', 'HOLIDAY'] and record.total_hours_worked:
            hours = float(record.total_hours_worked)
            percentage = (hours / 8) * 100
            weekly_data.append({
                'day': date.strftime('%A')[:3],
                'date': date.strftime('%d/%m'),
                'hours': hours,
                'percentage': round(min(percentage, 100), 1),
                'status': record.get_status_display().lower()
            })
        else:
            weekly_data.append({
                'day': date.strftime('%A')[:3],
                'date': date.strftime('%d/%m'),
                'hours': 0,
                'percentage': 0,
                'status': 'absent' if not record else record.get_status_display().lower()
            })
    
    # Monthly summary by status
    monthly_summary = {
        'present': present_days,
        'absent': absent_days,
        'late': late_days,
        'half_day': halfday_days,
        'leave': leave_days,
        'holiday': holiday_days,
        'total': total_days
    }
    
    # Get year range for filter
    current_year = today.year
    year_range = range(current_year - 5, current_year + 1)
    
    # Handle AJAX request
    if is_ajax:
        data = {
            'success': True,
            # Overall statistics (all time - no filters)
            'overall_total_days': overall_total,
            'overall_present_days': overall_present,
            'overall_absent_days': overall_absent + overall_late + overall_halfday,
            'overall_avg_hours': overall_avg_hours,
            
            # Filtered statistics
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days + late_days + halfday_days,
            'avg_hours': avg_hours,
            'today_login': today_login,
            'today_logout': today_logout,
            'today_hours': today_hours,
            'today_status': today_status,
            
            # Complete records
            'all_records': all_records_list,
            'all_records_count': len(all_records_list),
            
            # Paginated data
            'attendance_list': attendance_list,
            'page_obj': {
                'start_index': page_obj.start_index(),
                'end_index': page_obj.end_index(),
                'total_records': page_obj.paginator.count,
                'current_page': page_obj.number,
                'total_pages': page_obj.paginator.num_pages,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
                'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
                'page_range': list(page_obj.paginator.page_range),
            },
            
            # Statistics
            'present_percentage': present_percentage,
            'absent_percentage': absent_percentage,
            'late_percentage': late_percentage,
            'halfday_percentage': halfday_percentage,
            'late_days': late_days,
            'halfday_days': halfday_days,
            'leave_days': leave_days,
            
            # Monthly summary
            'monthly_summary': monthly_summary,
            
            # Weekly data
            'weekly_data': weekly_data,
            
            # Current info
            'current_month_name': today.strftime('%B %Y'),
            'current_month': today.strftime('%Y-%m'),
            'current_year': today.year,
            'current_month_number': today.month,
            'week_label': 'Week of ' + (today - timedelta(days=today.weekday())).strftime('%b %d, %Y'),
            
            # Filter state
            'filters': {
                'month': month_filter,
                'status': status_filter,
                'day_of_week': day_of_week_filter,
                'year': year_filter,
                'search': search_query,
            },
            
            # Faculty info
            'faculty_name': faculty.user.get_full_name(),
            'employee_id': faculty.employee_id,
            'search_query': search_query,
            'year_range': list(year_range),
        }
        return JsonResponse(data)
    
    # Handle export
    if export_type == 'excel':
        return export_attendance_excel(attendance_queryset, faculty)
    elif export_type == 'pdf':
        return export_attendance_pdf(attendance_queryset, faculty)
    
    context = {
        'page_obj': page_obj,
        'attendance_list': attendance_list,
        'all_records': all_records_list,
        # Overall statistics (all time - no filters)
        'overall_total_days': overall_total,
        'overall_present_days': overall_present,
        'overall_absent_days': overall_absent + overall_late + overall_halfday,
        'overall_avg_hours': overall_avg_hours,
        # Filtered statistics
        'total_days': total_days,
        'present_days': present_days,
        'absent_days': absent_days,
        'late_days': late_days,
        'halfday_days': halfday_days,
        'avg_hours': avg_hours,
        'present_percentage': present_percentage,
        'absent_percentage': absent_percentage,
        'late_percentage': late_percentage,
        'halfday_percentage': halfday_percentage,
        'today_date': today,
        'today_login': today_login,
        'today_logout': today_logout,
        'today_hours': today_hours,
        'today_status': today_status,
        'weekly_data': weekly_data,
        'current_month': today.strftime('%Y-%m'),
        'current_month_name': today.strftime('%B %Y'),
        'faculty_name': faculty.user.get_full_name(),
        'employee_id': faculty.employee_id,
        'search_query': search_query,
        'monthly_summary': monthly_summary,
        'leave_days': leave_days,
        'year_range': year_range,
    }
    
    return render(request, 'jordan/faculty_attendance.html', context)


def export_attendance_excel(queryset, faculty):
    """Export attendance data to Excel"""
    # Create DataFrame
    data = []
    for record in queryset.order_by('-date'):
        data.append({
            'Date': record.date.strftime('%d-%m-%Y'),
            'Day': record.date.strftime('%A'),
            'Check In': record.check_in.strftime('%I:%M %p') if record.check_in else '-',
            'Check Out': record.check_out.strftime('%I:%M %p') if record.check_out else '-',
            'Total Hours': float(record.total_hours_worked) if record.total_hours_worked else 0,
            'Status': record.get_status_display(),
            'Late Minutes': record.late_minutes or 0,
            'Early Leave Minutes': record.early_leave_minutes or 0,
            'Notes': getattr(record, 'notes', '') or ''
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Attendance', index=False)
        
        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Attendance']
        
        # Adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    
    # Create response
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="attendance_{faculty.employee_id}_{datetime.now().strftime("%Y%m%d")}.xlsx"'
    return response


def export_attendance_pdf(queryset, faculty):
    """Export attendance data to PDF"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="attendance_{faculty.employee_id}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    
    # Create PDF
    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    elements.append(Paragraph(f"Attendance Report - {faculty.user.get_full_name()}", title_style))
    elements.append(Paragraph(f"Employee ID: {faculty.employee_id}", styles['Normal']))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Table data
    table_data = [['#', 'Date', 'Day', 'Check In', 'Check Out', 'Hours', 'Status', 'Notes']]
    
    for idx, record in enumerate(queryset.order_by('-date'), 1):
        table_data.append([
            str(idx),
            record.date.strftime('%d-%m-%Y'),
            record.date.strftime('%A'),
            record.check_in.strftime('%I:%M %p') if record.check_in else '-',
            record.check_out.strftime('%I:%M %p') if record.check_out else '-',
            str(float(record.total_hours_worked)) if record.total_hours_worked else '0',
            record.get_status_display(),
            (getattr(record, 'notes', '') or '')[:30]
        ])
    
    # Create table
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    
    # Summary
    elements.append(Spacer(1, 20))
    summary_style = ParagraphStyle(
        'Summary',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_LEFT,
    )
    
    total = queryset.count()
    present = queryset.filter(status='PRESENT').count()
    absent = queryset.filter(status='ABSENT').count()
    late = queryset.filter(status='LATE').count()
    half_day = queryset.filter(status='HALF_DAY').count()
    
    elements.append(Paragraph(f"<b>Summary:</b>", summary_style))
    elements.append(Paragraph(f"Total Days: {total}", summary_style))
    elements.append(Paragraph(f"Present: {present}", summary_style))
    elements.append(Paragraph(f"Absent: {absent}", summary_style))
    elements.append(Paragraph(f"Late: {late}", summary_style))
    elements.append(Paragraph(f"Half Day: {half_day}", summary_style))
    
    # Build PDF
    doc.build(elements)
    return response


def approval_project(request, uuid):
    return render(request, 'jordan/approval_project.html')

def application_project(request, uuid):
    return render(request, 'jordan/application_project.html')

def progress_project(request, uuid):
    return render(request, 'jordan/progress_project.html')

def research_committee(request, uuid):
    return render(request, 'jordan/research_committee.html')

# ===================================== Research student Applications ==========================


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404
from mimetypes import guess_type
from urllib.parse import quote
import os
import json
import logging

from Research.models import StudentResearchApplication, ResearchOpportunity
from Research.Elsa_research.forms import StudentResearchApplicationForm
from Students.models import StudentProfile, StudentAcademicProfile
from Faculty.models import FacultyProfile, Department

logger = logging.getLogger(__name__)

@login_required
def student_applications(request, uuid):
    """
    View for faculty to see applications for their research opportunities only.
    """
    # Get the faculty profile for the logged-in user
    try:
        faculty = FacultyProfile.objects.get(user=request.user)
    except FacultyProfile.DoesNotExist:
        messages.error(request, 'Faculty profile not found.')
        return redirect('faculty_dashboard')

    # Get filter parameters
    status_filter = request.GET.get('status', '')
    department_filter = request.GET.get('department', '')
    program_filter = request.GET.get('program', '')
    search_query = request.GET.get('search', '')
    quick_filter = request.GET.get('quick_filter', 'all')
    page = request.GET.get('page', 1)
    
    # Base queryset - Only applications for research opportunities posted by this faculty
    applications = StudentResearchApplication.objects.select_related(
        'student',
        'student__user',
        'research_opportunity',
        'research_opportunity__faculty'
    ).filter(
        research_opportunity__faculty=faculty  # Filter by faculty
    ).exclude(status='draft').exclude(status='withdrawn').order_by('-submitted_at')
    
    # Apply filters
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    if department_filter:
        applications = applications.filter(
            student__academic_profile__department__slug=department_filter
        )
    
    if program_filter:
        applications = applications.filter(student__academic_level=program_filter)
    
    if quick_filter != 'all':
        applications = applications.filter(status=quick_filter)
    
    if search_query:
        applications = applications.filter(
            Q(reference_number__icontains=search_query) |
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__user__email__icontains=search_query) |
            Q(research_opportunity__title__icontains=search_query)
        ).distinct()
    
    # Get statistics - Only for this faculty's opportunities
    total_applications = StudentResearchApplication.objects.filter(
        research_opportunity__faculty=faculty
    ).exclude(status='draft').exclude(status='withdrawn').count()
    
    pending_applications = StudentResearchApplication.objects.filter(
        research_opportunity__faculty=faculty,
        status='submitted'
    ).count()
    
    under_review_applications = StudentResearchApplication.objects.filter(
        research_opportunity__faculty=faculty,
        status='under_review'
    ).count()
    
    shortlisted_applications = StudentResearchApplication.objects.filter(
        research_opportunity__faculty=faculty,
        status='shortlisted'
    ).count()
    
    accepted_applications = StudentResearchApplication.objects.filter(
        research_opportunity__faculty=faculty,
        status='accepted'
    ).count()
    
    rejected_applications = StudentResearchApplication.objects.filter(
        research_opportunity__faculty=faculty,
        status='rejected'
    ).count()
    
    # Get departments for filter (only those with applications for this faculty)
    departments = Department.objects.filter(
        student_academic_profiles__student__research_applications__research_opportunity__faculty=faculty
    ).distinct().filter(status='ACTIVE')
    
    # Program level options with display names
    PROGRAM_LEVELS = [
        {'value': 'UG', 'label': 'Undergraduate'},
        {'value': 'PG', 'label': 'Postgraduate'},
        {'value': 'MASTERS', 'label': 'Masters'},
        {'value': 'PHD', 'label': 'PhD'},
        {'value': 'DIPLOMA', 'label': 'Diploma'},
    ]
    
    # Filter programs that have applications for this faculty
    available_programs = StudentProfile.objects.filter(
        research_applications__research_opportunity__faculty=faculty,
        academic_level__isnull=False
    ).values_list('academic_level', flat=True).distinct()
    
    program_options = []
    for program in PROGRAM_LEVELS:
        if program['value'] in available_programs:
            program_options.append(program)
    
    # Pagination
    paginator = Paginator(applications, 10)
    
    try:
        applications_page = paginator.page(page)
    except PageNotAnInteger:
        applications_page = paginator.page(1)
    except EmptyPage:
        applications_page = paginator.page(paginator.num_pages)
    
    context = {
        'uuid': uuid,
        'applications': applications_page,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'under_review_applications': under_review_applications,
        'shortlisted_applications': shortlisted_applications,
        'accepted_applications': accepted_applications,
        'rejected_applications': rejected_applications,
        'departments': departments,
        'program_options': program_options,
        'status_filter': status_filter,
        'department_filter': department_filter,
        'program_filter': program_filter,
        'search_query': search_query,
        'quick_filter': quick_filter,
        'faculty': faculty,  # Pass faculty to template for debugging
    }
    
    return render(request, 'jordan/student_applications.html', context)


@login_required
def get_application_details(request, application_id):
    """
    Get application details for AJAX modal.
    Only allows access if faculty owns the research opportunity.
    """
    try:
        # Get faculty profile
        try:
            faculty = FacultyProfile.objects.get(user=request.user)
        except FacultyProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Faculty profile not found'}, status=403)
        
        application = StudentResearchApplication.objects.select_related(
            'student',
            'student__user',
            'student__academic_profile',
            'student__academic_profile__department',
            'research_opportunity',
            'research_opportunity__faculty'
        ).get(application_id=application_id)
        
        # Check permission - only allow if faculty owns this opportunity
        if application.research_opportunity.faculty != faculty:
            return JsonResponse({'success': False, 'error': 'You do not have permission to view this application'}, status=403)
        
        # Build documents list with full URLs
        documents = []
        if application.resume and application.resume.name:
            documents.append({
                'name': os.path.basename(application.resume.name),
                'url': application.resume.url,
                'icon': 'ti ti-file',
                'type': 'Resume'
            })
        if application.statement_of_interest and application.statement_of_interest.name:
            documents.append({
                'name': os.path.basename(application.statement_of_interest.name),
                'url': application.statement_of_interest.url,
                'icon': 'ti ti-file-text',
                'type': 'Statement'
            })
        if application.academic_transcript and application.academic_transcript.name:
            documents.append({
                'name': os.path.basename(application.academic_transcript.name),
                'url': application.academic_transcript.url,
                'icon': 'ti ti-file-analytics',
                'type': 'Transcript'
            })
        
        # Get program display name
        program_display = {
            'UG': 'Undergraduate',
            'PG': 'Postgraduate',
            'MASTERS': 'Masters',
            'PHD': 'PhD',
            'DIPLOMA': 'Diploma',
        }
        student_program = getattr(application.student, 'academic_level', 'Not specified')
        program_display_name = program_display.get(student_program, student_program.replace('_', ' ').title() if student_program else 'Not specified')
        
        data = {
            'id': application.application_id,
            'reference': application.reference_number,
            'status': application.status,
            'status_display': application.get_status_display(),
            'student': {
                'name': application.student.user.get_full_name(),
                'email': application.student.user.email,
                'student_id': application.student.student_number,
                'program': program_display_name,
                'program_value': student_program,
                'department': application.student.academic_profile.department.department_name if hasattr(application.student, 'academic_profile') and application.student.academic_profile and application.student.academic_profile.department else 'Not assigned',
                'phone': getattr(application.student.user, 'mobile_number', 'Not provided') or 'Not provided',
            },
            'project': {
                'title': application.research_opportunity.title if application.research_opportunity else 'Not specified',
                'motivation': application.motivation,
                'skills': application.skills_contribution,
                'experience': application.prior_experience or 'Not provided',
                'time_commitment': application.get_time_commitment_display(),
                'availability': application.get_availability_display(),
                'additional_info': application.additional_info or 'Not provided',
            },
            'documents': documents,
            'submitted_date': application.submitted_at.strftime('%Y-%m-%d %H:%M') if application.submitted_at else None,
            'review_comments': application.review_comments or '',
        }
        
        return JsonResponse({'success': True, 'data': data})
        
    except StudentResearchApplication.DoesNotExist:
        logger.error(f"Application {application_id} not found")
        return JsonResponse({'success': False, 'error': 'Application not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in get_application_details: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def update_application_status(request, application_id):
    """
    Update application status via AJAX.
    Only allows access if faculty owns the research opportunity.
    """
    try:
        # Get faculty profile
        try:
            faculty = FacultyProfile.objects.get(user=request.user)
        except FacultyProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Faculty profile not found'}, status=403)
        
        application = StudentResearchApplication.objects.get(application_id=application_id)
        
        # Check permission - only allow if faculty owns this opportunity
        if application.research_opportunity.faculty != faculty:
            return JsonResponse({'success': False, 'error': 'You do not have permission to update this application'}, status=403)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        
        status = data.get('status')
        comments = data.get('comments', '')
        
        valid_statuses = ['submitted', 'under_review', 'shortlisted', 'accepted', 'rejected']
        if status not in valid_statuses:
            return JsonResponse({
                'success': False, 
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }, status=400)
        
        if status in ['accepted', 'rejected'] and not comments:
            return JsonResponse({
                'success': False, 
                'error': 'Comments are required when accepting or rejecting an application.'
            }, status=400)
        
        application.status = status
        application.review_comments = comments
        application.reviewed_at = timezone.now()
        application.reviewed_by = request.user
        application.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Application {application.get_status_display()}',
            'status': application.status,
            'status_display': application.get_status_display()
        })
        
    except StudentResearchApplication.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Application not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in update_application_status: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def save_review_comment(request, application_id):
    """
    Save review comment via AJAX.
    Only allows access if faculty owns the research opportunity.
    """
    try:
        # Get faculty profile
        try:
            faculty = FacultyProfile.objects.get(user=request.user)
        except FacultyProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Faculty profile not found'}, status=403)
        
        application = StudentResearchApplication.objects.get(application_id=application_id)
        
        # Check permission - only allow if faculty owns this opportunity
        if application.research_opportunity.faculty != faculty:
            return JsonResponse({'success': False, 'error': 'You do not have permission to update this application'}, status=403)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
        
        comments = data.get('comments', '')
        
        application.review_comments = comments
        application.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Review comments saved successfully!'
        })
        
    except StudentResearchApplication.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Application not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in save_review_comment: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def view_document(request, application_id, doc_type):
    """
    View/download document from application.
    Only allows access if faculty owns the research opportunity.
    """
    try:
        # Get faculty profile
        try:
            faculty = FacultyProfile.objects.get(user=request.user)
        except FacultyProfile.DoesNotExist:
            raise Http404("Faculty profile not found")
        
        application = StudentResearchApplication.objects.get(application_id=application_id)
        
        # Check permission - only allow if faculty owns this opportunity
        if application.research_opportunity.faculty != faculty:
            raise Http404("You don't have permission to access this document")
        
        # Get the requested file
        if doc_type == 'resume':
            file_field = application.resume
        elif doc_type == 'statement':
            file_field = application.statement_of_interest
        elif doc_type == 'transcript':
            file_field = application.academic_transcript
        else:
            raise Http404("Document type not found")
        
        if not file_field or not file_field.name:
            raise Http404("Document not found")
        
        # Get file path
        file_path = file_field.path
        
        if not os.path.exists(file_path):
            raise Http404("File does not exist")
        
        # Determine content type
        content_type, encoding = guess_type(file_path)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        # Open and return file
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        
        # Set filename for download/view
        original_filename = os.path.basename(file_path)
        response['Content-Disposition'] = f'inline; filename="{quote(original_filename)}"'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        
        return response
        
    except StudentResearchApplication.DoesNotExist:
        raise Http404("Application not found")
    except Exception as e:
        logger.error(f"Error viewing document: {str(e)}")
        raise Http404("Error accessing document")

    
# ======================== Research team & Research team member =====================
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from Research.models import ResearchOpportunity, ResearchTeam, ResearchTeamMember, StudentResearchApplication
from Faculty.models import FacultyProfile
from Students.models import StudentProfile

@login_required
def research_team(request, uuid=None):
    """View for research team management page"""
    return render(request, 'jordan/research_team.html')

@login_required
@require_http_methods(["GET"])
def get_projects(request):
    """API endpoint to get research projects for the logged-in faculty member"""
    try:
        faculty = FacultyProfile.objects.get(user=request.user)
        projects = ResearchOpportunity.objects.filter(faculty=faculty).select_related('department', 'faculty', 'faculty__user')
        
        project_list = []
        for project in projects:
            # Get team data
            try:
                research_team = ResearchTeam.objects.get(research_details=project)
                team_members = ResearchTeamMember.objects.filter(team=research_team).select_related('faculty__user', 'student__user')
                team_name = research_team.team_name
            except ResearchTeam.DoesNotExist:
                team_members = []
                team_name = None
            
            members_data = []
            
            # Add mentor
            if project.faculty:
                members_data.append({
                    'id': f'mentor_{project.faculty.id}',
                    'original_id': project.faculty.id,
                    'name': project.faculty.user.get_full_name() or str(project.faculty),
                    'role': 'mentor',
                    'role_display': 'Mentor',
                    'type': 'Faculty',
                    'is_mentor': True,
                    'is_removable': False,
                    'is_application': False,
                    'member_type': 'faculty'
                })
            
            # Add team members
            for member in team_members:
                if member.faculty:
                    if project.faculty and member.faculty.id == project.faculty.id:
                        continue
                    name = member.faculty.user.get_full_name() or str(member.faculty)
                    member_type = "Faculty"
                    member_data = {
                        'id': member.id,  # Keep as integer
                        'original_id': member.id,
                        'name': name,
                        'role': member.role.lower().replace(' ', '_'),
                        'role_display': member.get_role_display(),
                        'type': member_type,
                        'is_mentor': False,
                        'is_removable': True,
                        'is_application': False,
                        'member_type': 'faculty'
                    }
                    members_data.append(member_data)
                elif member.student:
                    name = member.student.user.get_full_name() or str(member.student)
                    member_type = "Student"
                    member_data = {
                        'id': member.id,  # Keep as integer
                        'original_id': member.id,
                        'name': name,
                        'role': member.role.lower().replace(' ', '_'),
                        'role_display': member.get_role_display(),
                        'type': member_type,
                        'is_mentor': False,
                        'is_removable': True,
                        'is_application': False,
                        'member_type': 'student'
                    }
                    members_data.append(member_data)
            
            # Add accepted student applications
            applications = StudentResearchApplication.objects.filter(
                research_opportunity=project, status='accepted'
            ).select_related('student__user')
            
            for app in applications:
                student_name = app.student.user.get_full_name() or str(app.student)
                exists = any(m.get('name') == student_name and m.get('role') == 'student' for m in members_data)
                if not exists:
                    members_data.append({
                        'id': f'app_{app.application_id}',
                        'original_id': app.application_id,
                        'name': student_name,
                        'role': 'student',
                        'role_display': 'Student',
                        'type': 'Student',
                        'is_mentor': False,
                        'is_removable': False,
                        'is_application': True,
                        'member_type': 'student'
                    })
            
            department_name = project.department.department_name if project.department else 'No Department'
            
            project_list.append({
                'id': project.research_id,
                'title': project.title,
                'description': project.short_description or project.description,
                'start_date': project.start_date.isoformat() if project.start_date else None,
                'end_date': project.end_date.isoformat() if project.end_date else None,
                'department': department_name,
                'team_name': team_name or f"Team for {project.title}",
                'team_members': members_data
            })
        
        return JsonResponse({'success': True, 'projects': project_list})
        
    except FacultyProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Faculty profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def get_available_faculty(request):
    """Get available faculty members for team assignment"""
    try:
        project_id = request.GET.get('project_id')
        if not project_id:
            return JsonResponse({'success': False, 'error': 'Project ID required'}, status=400)
        
        project = get_object_or_404(ResearchOpportunity, research_id=project_id)
        all_faculty = FacultyProfile.objects.select_related('user', 'department').all()
        
        try:
            research_team = ResearchTeam.objects.get(research_details=project)
            existing_faculty_ids = ResearchTeamMember.objects.filter(
                team=research_team, faculty__isnull=False
            ).values_list('faculty_id', flat=True)
        except ResearchTeam.DoesNotExist:
            existing_faculty_ids = []
        
        mentor_id = project.faculty.id if project.faculty else None
        
        available_faculty = []
        for f in all_faculty:
            if mentor_id and f.id == mentor_id:
                continue
            if f.id in existing_faculty_ids:
                continue
            
            available_faculty.append({
                'id': f.id,
                'name': f.user.get_full_name() or str(f),
                'department': f.department.department_name if f.department else 'No Department'
            })
        
        available_faculty.sort(key=lambda x: x['name'])
        return JsonResponse({'success': True, 'faculty': available_faculty})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def get_available_students(request):
    """Get available students for team assignment"""
    try:
        project_id = request.GET.get('project_id')
        if not project_id:
            return JsonResponse({'success': False, 'error': 'Project ID required'}, status=400)
        
        project = get_object_or_404(ResearchOpportunity, research_id=project_id)
        accepted_applications = StudentResearchApplication.objects.filter(
            research_opportunity=project, status='accepted'
        ).select_related('student__user')
        
        try:
            research_team = ResearchTeam.objects.get(research_details=project)
            existing_student_ids = ResearchTeamMember.objects.filter(
                team=research_team, student__isnull=False
            ).values_list('student_id', flat=True)
        except ResearchTeam.DoesNotExist:
            existing_student_ids = []
        
        student_list = []
        for app in accepted_applications:
            if app.student.id in existing_student_ids:
                continue
            
            program_name = 'Not Specified'
            if hasattr(app.student, 'academic_profile') and app.student.academic_profile:
                if app.student.academic_profile.program:
                    program_name = str(app.student.academic_profile.program)
            
            student_list.append({
                'id': app.student.id,
                'name': app.student.user.get_full_name() or str(app.student),
                'program': program_name
            })
        
        student_list.sort(key=lambda x: x['name'])
        return JsonResponse({'success': True, 'students': student_list})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def add_team_member(request):
    """Add a team member to a research project"""
    try:
        data = json.loads(request.body)

        project_id = data.get('project_id')
        member_id = data.get('member_id')
        member_type = data.get('member_type')
        role = data.get('role')

        if not project_id or not member_id or not member_type or not role:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)

        # Get project
        project = get_object_or_404(
            ResearchOpportunity,
            research_id=project_id
        )

        # Get or create research team
        research_team, created = ResearchTeam.objects.get_or_create(
            research_details=project,
            defaults={
                'team_name': f'Team for {project.title}'
            }
        )

        # ==========================================
        # ADD FACULTY
        # ==========================================
        if member_type == 'faculty':

            faculty = get_object_or_404(
                FacultyProfile,
                id=member_id
            )

            # Don't allow mentor to be added again
            if project.faculty and faculty.id == project.faculty.id:
                return JsonResponse({
                    'success': False,
                    'error': 'This faculty member is already the mentor'
                }, status=400)

            # Check if already exists
            existing_member = ResearchTeamMember.objects.filter(
                team=research_team,
                faculty=faculty
            ).first()

            if existing_member:
                return JsonResponse({
                    'success': False,
                    'error': 'This faculty member is already in the team'
                }, status=400)

            team_member = ResearchTeamMember.objects.create(
                team=research_team,
                faculty=faculty,
                role=role
            )

            name = faculty.user.get_full_name() or str(faculty)

        # ==========================================
        # ADD STUDENT
        # ==========================================
        elif member_type == 'student':

            student = get_object_or_404(
                StudentProfile,
                id=member_id
            )

            # Check if already exists
            existing_member = ResearchTeamMember.objects.filter(
                team=research_team,
                student=student
            ).first()

            if existing_member:
                return JsonResponse({
                    'success': False,
                    'error': 'This student is already in the team'
                }, status=400)

            team_member = ResearchTeamMember.objects.create(
                team=research_team,
                student=student,
                role=role
            )

            name = student.user.get_full_name() or str(student)

        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid member type'
            }, status=400)

        # ==========================================
        # SUCCESS RESPONSE
        # ==========================================
        return JsonResponse({
            'success': True,
            'message': f'{name} added successfully',
            'member_id': team_member.id
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

    
@login_required
@require_http_methods(["POST"])
@csrf_exempt
def remove_team_member(request):
    """Remove a team member from a research project"""
    try:
        data = json.loads(request.body)
        member_id = data.get('member_id')
        project_id = data.get('project_id')
        
        # Check if it's an application-based member
        if isinstance(member_id, str) and member_id.startswith('app_'):
            return JsonResponse({'success': False, 'error': 'Cannot remove application-based member'}, status=400)
        
        # Convert to integer
        try:
            member_id = int(member_id)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid member ID'}, status=400)
        
        project = get_object_or_404(ResearchOpportunity, research_id=project_id)
        research_team = get_object_or_404(ResearchTeam, research_details=project)
        member = get_object_or_404(ResearchTeamMember, id=member_id, team=research_team)
        
        # Prevent removing mentor
        if member.faculty and project.faculty and member.faculty.id == project.faculty.id:
            return JsonResponse({'success': False, 'error': 'Cannot remove the mentor'}, status=400)
        
        # Get name for message
        if member.faculty:
            name = member.faculty.user.get_full_name() or str(member.faculty)
        elif member.student:
            name = member.student.user.get_full_name() or str(member.student)
        else:
            name = "Team member"
        
        member.delete()
        
        return JsonResponse({'success': True, 'message': f'{name} removed successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def update_team_name(request):
    """Update team name"""
    try:
        data = json.loads(request.body)
        project_id = data.get('project_id')
        team_name = data.get('team_name')
        
        if not team_name or not team_name.strip():
            return JsonResponse({'success': False, 'error': 'Team name required'}, status=400)
        
        project = get_object_or_404(ResearchOpportunity, research_id=project_id)
        research_team, created = ResearchTeam.objects.get_or_create(
            research_details=project,
            defaults={'team_name': team_name.strip()}
        )
        
        if not created:
            research_team.team_name = team_name.strip()
            research_team.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Team name updated',
            'team_name': research_team.team_name
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# =============================== Research Project ===========================================

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal
from Research.models import (
    ResearchOpportunity, ResearchTeam, ResearchTeamMember, 
    StudentResearchApplication, ResearchProgress, ResearchOpportunityDocument
)
from Faculty.models import FacultyProfile
from Students.models import StudentProfile

@login_required
def research_faculty_details(request, uuid):
    """
    View for research faculty details page - shows all research projects posted by the faculty
    """
    return render(request, 'jordan/research_details_faculty.html')

@login_required
@require_http_methods(["GET"])
def get_faculty_projects(request):
    """
    API endpoint to get all research projects for the logged-in faculty member
    """
    try:
        faculty = FacultyProfile.objects.get(user=request.user)
        
        projects = ResearchOpportunity.objects.filter(
            faculty=faculty
        ).select_related('department', 'faculty', 'faculty__user')
        
        project_list = []
        for project in projects:
            # Get team
            try:
                research_team = ResearchTeam.objects.get(research_details=project)
                team_members = ResearchTeamMember.objects.filter(team=research_team).select_related(
                    'faculty__user', 'student__user'
                )
                team_name = research_team.team_name
            except ResearchTeam.DoesNotExist:
                team_members = []
                team_name = None
            
            members_data = []
            
            # Mentor
            mentor_data = None
            if project.faculty:
                mentor_data = {
                    'id': project.faculty.id,
                    'name': project.faculty.user.get_full_name() if project.faculty.user else str(project.faculty),
                    'role': 'mentor',
                    'role_display': 'Mentor',
                    'type': 'Faculty',
                    'is_mentor': True
                }
                members_data.append(mentor_data)
            
            for member in team_members:
                if member.faculty:
                    # Skip if this is the mentor
                    if project.faculty and member.faculty.id == project.faculty.id:
                        continue
                    name = member.faculty.user.get_full_name() if member.faculty.user else str(member.faculty)
                    member_type = "Faculty"
                elif member.student:
                    name = member.student.user.get_full_name() if member.student.user else str(member.student)
                    member_type = "Student"
                else:
                    continue
                
                members_data.append({
                    'id': member.id,
                    'name': name,
                    'role': member.role.lower().replace(' ', '_'),
                    'role_display': member.get_role_display(),
                    'type': member_type,
                    'is_mentor': False
                })
            
            # Accepted students
            applications = StudentResearchApplication.objects.filter(
                research_opportunity=project,
                status='accepted'
            ).select_related('student__user')
            
            for app in applications:
                student_name = app.student.user.get_full_name() if app.student.user else str(app.student)
                exists = any(m['name'] == student_name and m['role'] == 'student' for m in members_data)
                if not exists:
                    members_data.append({
                        'id': f"app_{app.application_id}",
                        'name': student_name,
                        'role': 'student',
                        'role_display': 'Student',
                        'type': 'Student',
                        'is_mentor': False
                    })
            
            # Department name
            dept_name = 'No Department'
            dept_slug = 'no-department'
            if project.department:
                dept_name = getattr(project.department, 'name', str(project.department))
                dept_slug = getattr(project.department, 'slug', 'no-department')
            
            # Get project status - using project_status
            project_status_value = project.project_status if project.project_status else 'DRAFT'
            
            project_list.append({
                'id': project.research_id,
                'title': project.title,
                'description': project.short_description or project.description,
                'status': project_status_value.lower(),
                'status_display': project.get_project_status_display() if project.project_status else 'Draft',
                'start_date': project.start_date.isoformat() if project.start_date else None,
                'end_date': project.end_date.isoformat() if project.end_date else None,
                'department': dept_name,
                'department_slug': dept_slug,
                'team_name': team_name or f"Team for {project.title}",
                'mentor': mentor_data,
                'team_members': members_data,
                'category': project.category,
                'required_skills': project.required_skills,
                'skill_list': project.skill_list,
                'reference_link': project.reference_link,
                'additional_notes': project.additional_notes,
                'available_slots': project.available_slots,
                'application_deadline': project.application_deadline.strftime('%Y-%m-%d') if project.application_deadline else None,
                'application_open_date': project.application_open_date.strftime('%Y-%m-%d') if project.application_open_date else None,
                'estimated_amount': str(project.estimated_amount) if project.estimated_amount else None,
                'project_status': project_status_value.lower(),
                'project_status_display': project.get_project_status_display() if project.project_status else 'Draft',
            })
        
        return JsonResponse({
            'success': True,
            'projects': project_list
        })
        
    except FacultyProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Faculty profile not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def get_project_details_modal(request):
    """
    API endpoint to get detailed project information for the modal
    """
    try:
        project_id = request.GET.get('project_id')
        
        if not project_id:
            return JsonResponse({
                'success': False,
                'error': 'Project ID is required'
            }, status=400)
        
        project = get_object_or_404(ResearchOpportunity, research_id=project_id)
        
        # Get progress updates
        progress_updates = ResearchProgress.objects.filter(
            research=project
        ).order_by('-submission_date')
        
        progress_data = []
        for progress in progress_updates:
            progress_data.append({
                'id': progress.progress_id,
                'milestone': progress.milestone,
                'progress_percentage': progress.progress_percentage,
                'submission_date': progress.submission_date.strftime('%Y-%m-%d'),
            })
        
        # Calculate overall progress
        overall_progress = 0
        if progress_data:
            total = sum(p['progress_percentage'] for p in progress_data)
            overall_progress = round(total / len(progress_data))
        
        # Get team
        try:
            research_team = ResearchTeam.objects.get(research_details=project)
            team_members = ResearchTeamMember.objects.filter(team=research_team).select_related(
                'faculty__user', 'student__user'
            )
            team_name = research_team.team_name
        except ResearchTeam.DoesNotExist:
            team_members = []
            team_name = None
        
        # Organize team members by role - using a set to avoid duplicates
        team_by_role = {
            'mentor': [],
            'co_mentor': [],
            'advisor': [],
            'student': []
        }
        
        # Add mentor (only once)
        if project.faculty:
            mentor_name = project.faculty.user.get_full_name() if project.faculty.user else str(project.faculty)
            mentor_email = project.faculty.user.email if project.faculty.user else None
            team_by_role['mentor'].append({
                'name': mentor_name,
                'email': mentor_email,
                'role': 'Mentor'
            })
        
        # Track added members to avoid duplicates
        added_members = set()
        
        # Add team members from ResearchTeamMember
        for member in team_members:
            if member.faculty:
                # Skip if this is the mentor (already added)
                if project.faculty and member.faculty.id == project.faculty.id:
                    continue
                    
                name = member.faculty.user.get_full_name() if member.faculty.user else str(member.faculty)
                email = member.faculty.user.email if member.faculty.user else None
                
                # Check for duplicates
                member_key = f"{name}_{member.role}"
                if member_key in added_members:
                    continue
                added_members.add(member_key)
                
                role_display = member.get_role_display()
                if role_display == 'Co-Mentor':
                    team_by_role['co_mentor'].append({'name': name, 'email': email, 'role': role_display})
                elif role_display == 'Advisor':
                    team_by_role['advisor'].append({'name': name, 'email': email, 'role': role_display})
                else:
                    # Default fallback
                    team_by_role['co_mentor'].append({'name': name, 'email': email, 'role': role_display})
                    
            elif member.student:
                name = member.student.user.get_full_name() if member.student.user else str(member.student)
                email = member.student.user.email if member.student.user else None
                
                # Check for duplicates
                member_key = f"{name}_student"
                if member_key in added_members:
                    continue
                added_members.add(member_key)
                
                team_by_role['student'].append({'name': name, 'email': email, 'role': 'Student'})
        
        # Add accepted students (only if not already added)
        applications = StudentResearchApplication.objects.filter(
            research_opportunity=project,
            status='accepted'
        ).select_related('student__user')
        
        for app in applications:
            student_name = app.student.user.get_full_name() if app.student.user else str(app.student)
            
            # Check if already added
            exists = any(m['name'] == student_name for m in team_by_role['student'])
            if not exists:
                team_by_role['student'].append({
                    'name': student_name,
                    'email': app.student.user.email if app.student.user else None,
                    'role': 'Student'
                })
        
        # Get project status
        project_status_value = project.project_status if project.project_status else 'DRAFT'
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': project.research_id,
                'title': project.title,
                'description': project.description or project.short_description or '',
                'category': project.category or 'Not specified',
                'status_display': project.get_project_status_display() if project.project_status else 'Draft',
                'status': project_status_value.lower(),
                'start_date': project.start_date.strftime('%Y-%m-%d') if project.start_date else None,
                'end_date': project.end_date.strftime('%Y-%m-%d') if project.end_date else None,
                'application_deadline': project.application_deadline.strftime('%Y-%m-%d') if project.application_deadline else None,
                'application_open_date': project.application_open_date.strftime('%Y-%m-%d') if project.application_open_date else None,
                'available_slots': project.available_slots,
                'skill_list': project.skill_list,
                'reference_link': project.reference_link,
                'additional_notes': project.additional_notes or '',
                'team_name': team_name or f"Team for {project.title}",
                'team_by_role': team_by_role,
                'progress_updates': progress_data,
                'overall_progress': overall_progress,
                'estimated_amount': str(project.estimated_amount) if project.estimated_amount else None,
                'project_status': project_status_value.lower(),
                'project_status_display': project.get_project_status_display() if project.project_status else 'Draft',
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def update_project_status(request):
    """
    API endpoint to update project status
    """
    try:
        data = json.loads(request.body)
        project_id = data.get('project_id')
        new_status = data.get('status')
        
        if not project_id or not new_status:
            return JsonResponse({
                'success': False,
                'error': 'Project ID and status are required'
            }, status=400)
        
        # Verify the faculty owns this project
        faculty = FacultyProfile.objects.get(user=request.user)
        project = get_object_or_404(ResearchOpportunity, research_id=project_id, faculty=faculty)
        
        # Validate status
        valid_statuses = [choice[0] for choice in ResearchOpportunity.PROJECT_STATUS_CHOICES]
        if new_status.upper() not in valid_statuses:
            return JsonResponse({
                'success': False,
                'error': f'Invalid status. Valid statuses: {", ".join(valid_statuses)}'
            }, status=400)
        
        # Update status
        project.project_status = new_status.upper()
        project.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Project status updated to {project.get_project_status_display()}',
            'data': {
                'status': project.project_status.lower(),
                'status_display': project.get_project_status_display()
            }
        })
        
    except FacultyProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Faculty profile not found'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_project_status_options(request):
    """
    API endpoint to get all available project status options
    """
    try:
        status_options = []
        for choice in ResearchOpportunity.PROJECT_STATUS_CHOICES:
            status_options.append({
                'value': choice[0].lower(),
                'label': choice[1]
            })
        
        return JsonResponse({
            'success': True,
            'status_options': status_options
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)



# ==================== Research Publication ========================

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from Research.models import (
    ResearchOpportunity, ResearchTeam, ResearchTeamMember, 
    StudentResearchApplication, StudentResearchPublication, PublicationAuthor
)
from Faculty.models import FacultyProfile


@login_required
def research_publication(request, uuid):
    """
    View for research publication page - shows all research projects for the faculty
    """
    return render(request, 'jordan/research_publication.html')


@login_required
@require_http_methods(["GET"])
def get_faculty_research_projects(request):
    """
    API endpoint to get all research projects for the logged-in faculty
    """
    try:
        faculty = FacultyProfile.objects.get(user=request.user)
        
        projects = ResearchOpportunity.objects.filter(
            faculty=faculty
        ).select_related('department')
        
        project_list = []
        for project in projects:
            # Check if publication exists
            has_publication = StudentResearchPublication.objects.filter(research=project).exists()
            
            # Get publication if exists
            publication = None
            if has_publication:
                publication = StudentResearchPublication.objects.filter(research=project).first()
            
            project_list.append({
                'id': project.research_id,
                'uuid': str(project.research_uuid),
                'title': project.title,
                'description': project.short_description or project.description,
                'category': project.category,
                'status': project.status.lower(),
                'status_display': project.get_status_display(),
                'project_status': project.project_status.lower(),
                'project_status_display': project.get_project_status_display(),
                'department': project.department.department_name if project.department else 'No Department',
                'start_date': project.start_date.isoformat() if project.start_date else None,
                'end_date': project.end_date.isoformat() if project.end_date else None,
                'has_publication': has_publication,
                'publication': {
                    'id': publication.publication_id if publication else None,
                    'title': publication.title if publication else None,
                    'status': publication.status.lower() if publication else None,
                    'status_display': publication.get_status_display() if publication else None,
                    'publication_type': publication.get_publication_type_display() if publication else None,
                    'created_at': publication.created_at.strftime('%Y-%m-%d %H:%M') if publication else None,
                } if publication else None
            })
        
        return JsonResponse({
            'success': True,
            'projects': project_list
        })
        
    except FacultyProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Faculty profile not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_project_publication(request):
    """
    API endpoint to get publication details for a specific project
    """
    try:
        project_id = request.GET.get('project_id')
        
        if not project_id:
            return JsonResponse({
                'success': False,
                'error': 'Project ID is required'
            }, status=400)
        
        faculty = FacultyProfile.objects.get(user=request.user)
        project = get_object_or_404(ResearchOpportunity, research_id=project_id, faculty=faculty)
        
        publication = StudentResearchPublication.objects.filter(research=project).first()
        
        if publication:
            authors = []
            for author in publication.authors.all().order_by('author_order'):
                team_member = author.team_member
                
                # Get name based on member type
                if team_member.faculty:
                    name = team_member.faculty.user.get_full_name() if team_member.faculty.user else str(team_member.faculty)
                    team_role = team_member.get_role_display()
                elif team_member.student:
                    name = team_member.student.user.get_full_name() if team_member.student.user else str(team_member.student)
                    team_role = "Student"
                else:
                    continue
                
                authors.append({
                    'id': author.id,
                    'name': name,
                    'author_role': author.get_author_role_display(),
                    'team_member_role': team_role,
                    'order': author.author_order,
                    'team_member_id': team_member.id  # This will be a numeric ID
                })
            
            return JsonResponse({
                'success': True,
                'has_publication': True,
                'publication': {
                    'id': publication.publication_id,
                    'uuid': str(publication.publication_uuid),
                    'title': publication.title,
                    'abstract': publication.abstract,
                    'keywords': publication.keywords,
                    'publication_type': publication.publication_type,
                    'publication_type_display': publication.get_publication_type_display(),
                    'status': publication.status.lower(),
                    'status_display': publication.get_status_display(),
                    'created_at': publication.created_at.strftime('%Y-%m-%d %H:%M'),
                    'updated_at': publication.updated_at.strftime('%Y-%m-%d %H:%M'),
                    'created_by': publication.created_by.user.get_full_name() if publication.created_by and publication.created_by.user else None,
                    'authors': authors,
                    'author_count': len(authors)
                }
            })
        else:
            return JsonResponse({
                'success': True,
                'has_publication': False,
                'publication': None
            })
        
    except FacultyProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Faculty profile not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_team_members_for_publication(request):
    """
    API endpoint to get team members for a research project
    Including Mentor, Co-Mentor, Advisor, and Student roles
    """
    try:
        project_id = request.GET.get('project_id')
        
        if not project_id:
            return JsonResponse({
                'success': False,
                'error': 'Project ID is required'
            }, status=400)
        
        faculty = FacultyProfile.objects.get(user=request.user)
        research = get_object_or_404(ResearchOpportunity, research_id=project_id, faculty=faculty)
        
        member_list = []
        member_ids = set()
        
        # Get the mentor (faculty who created the research)
        # We need to get or create a ResearchTeamMember for the mentor
        if research.faculty:
            # Check if mentor is already in a team
            mentor_team_member = None
            research_teams = ResearchTeam.objects.filter(research_details=research)
            for team in research_teams:
                try:
                    mentor_team_member = ResearchTeamMember.objects.get(
                        team=team,
                        faculty=research.faculty
                    )
                    break
                except ResearchTeamMember.DoesNotExist:
                    continue
            
            # If mentor doesn't exist as a team member, create them
            if not mentor_team_member:
                # Create a team if needed
                team, created = ResearchTeam.objects.get_or_create(
                    research_details=research,
                    defaults={'team_name': f"Research Team - {research.title}"}
                )
                mentor_team_member = ResearchTeamMember.objects.create(
                    team=team,
                    faculty=research.faculty,
                    role='MENTOR'
                )
            
            mentor_name = research.faculty.user.get_full_name() if research.faculty.user else str(research.faculty)
            mentor_email = research.faculty.user.email if research.faculty.user else None
            
            member_list.append({
                'id': mentor_team_member.id,  # Use the actual team member ID
                'name': mentor_name,
                'email': mentor_email,
                'type': "Faculty",
                'role': "Mentor",
                'display_role': "Mentor",
                'is_mentor': True
            })
            member_ids.add(mentor_team_member.id)
        
        # Get team members from ResearchTeam
        research_teams = ResearchTeam.objects.filter(research_details=research)
        
        for team in research_teams:
            team_members = ResearchTeamMember.objects.filter(team=team).select_related(
                'faculty__user', 'student__user'
            )
            
            for member in team_members:
                # Skip if already added (avoid duplicates)
                if member.id in member_ids:
                    continue
                member_ids.add(member.id)
                
                # Get name and role based on member type
                if member.faculty:
                    # Skip if this is the mentor (already added)
                    if research.faculty and member.faculty.id == research.faculty.id:
                        continue
                        
                    name = member.faculty.user.get_full_name() if member.faculty.user else str(member.faculty)
                    email = member.faculty.user.email if member.faculty.user else None
                    role_display = member.get_role_display()
                    
                    member_list.append({
                        'id': member.id,
                        'name': name,
                        'email': email,
                        'type': "Faculty",
                        'role': role_display,
                        'display_role': role_display,
                        'is_mentor': False
                    })
                    
                elif member.student:
                    name = member.student.user.get_full_name() if member.student.user else str(member.student)
                    email = member.student.user.email if member.student.user else None
                    
                    member_list.append({
                        'id': member.id,
                        'name': name,
                        'email': email,
                        'type': "Student",
                        'role': "Student",
                        'display_role': "Student",
                        'is_mentor': False
                    })
        
        # Get accepted students who might not be in team_members
        accepted_applications = StudentResearchApplication.objects.filter(
            research_opportunity=research,
            status='accepted'
        ).select_related('student__user')
        
        for app in accepted_applications:
            student = app.student
            if student and student.user:
                # Check if student already in list
                exists = any(m.get('email') == student.user.email for m in member_list)
                if not exists:
                    # Create team member for this student
                    team, created = ResearchTeam.objects.get_or_create(
                        research_details=research,
                        defaults={'team_name': f"Research Team - {research.title}"}
                    )
                    team_member, created = ResearchTeamMember.objects.get_or_create(
                        team=team,
                        student=student,
                        defaults={'role': 'STUDENT'}
                    )
                    
                    name = student.user.get_full_name() if student.user else str(student)
                    email = student.user.email if student.user else None
                    member_list.append({
                        'id': team_member.id,
                        'name': name,
                        'email': email,
                        'type': "Student",
                        'role': "Student",
                        'display_role': "Student",
                        'is_mentor': False
                    })
        
        # Sort members: Mentors first, then by role
        member_list.sort(key=lambda x: (0 if x.get('is_mentor') else 1, x.get('display_role', '')))
        
        return JsonResponse({
            'success': True,
            'team_members': member_list
        })
        
    except FacultyProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Faculty profile not found'
        }, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def create_or_update_publication(request):
    """
    API endpoint to create or update a publication
    """
    try:
        data = json.loads(request.body)
        
        project_id = data.get('project_id')
        title = data.get('title')
        abstract = data.get('abstract')
        keywords = data.get('keywords')
        publication_type = data.get('publication_type')
        status = data.get('status', 'DRAFT')
        authors = data.get('authors', [])
        publication_id = data.get('publication_id')
        
        # Validation
        if not all([project_id, title, abstract, publication_type]):
            return JsonResponse({
                'success': False,
                'error': 'Project ID, title, abstract, and publication type are required'
            }, status=400)
        
        if len(title) < 5:
            return JsonResponse({
                'success': False,
                'error': 'Title must be at least 5 characters long'
            }, status=400)
        
        if len(abstract) < 20:
            return JsonResponse({
                'success': False,
                'error': 'Abstract must be at least 20 characters long'
            }, status=400)
        
        # Validate status
        valid_statuses = [choice[0] for choice in StudentResearchPublication.STATUS_CHOICES]
        if status and status.upper() not in valid_statuses:
            return JsonResponse({
                'success': False,
                'error': f'Invalid status. Valid statuses: {", ".join(valid_statuses)}'
            }, status=400)
        
        faculty = FacultyProfile.objects.get(user=request.user)
        research = get_object_or_404(ResearchOpportunity, research_id=project_id, faculty=faculty)
        
        # Create or update publication
        if publication_id:
            publication = get_object_or_404(StudentResearchPublication, publication_id=publication_id, research=research)
            publication.title = title
            publication.abstract = abstract
            publication.keywords = keywords
            publication.publication_type = publication_type
            if status:
                publication.status = status.upper()
            publication.save()
            message = 'Publication updated successfully'
        else:
            publication = StudentResearchPublication.objects.create(
                research=research,
                title=title,
                abstract=abstract,
                keywords=keywords,
                publication_type=publication_type,
                status=status.upper() if status else 'DRAFT',
                created_by=faculty
            )
            message = 'Publication created successfully'
        
        # Update authors - delete existing authors and add new ones
        PublicationAuthor.objects.filter(publication=publication).delete()
        
        for index, author_data in enumerate(authors):
            team_member_id = author_data.get('team_member_id')
            author_role = author_data.get('author_role', 'CO_AUTHOR')
            author_order = index + 1
            
            if team_member_id:
                try:
                    # Convert to integer if it's a string
                    if isinstance(team_member_id, str):
                        # Check if it's a numeric string
                        if team_member_id.isdigit():
                            team_member_id = int(team_member_id)
                        elif team_member_id.startswith('mentor_'):
                            # Handle mentor ID - but this shouldn't happen now since we use numeric IDs
                            faculty_id = team_member_id.replace('mentor_', '')
                            faculty_profile = get_object_or_404(FacultyProfile, id=faculty_id)
                            
                            # Create a team if it doesn't exist
                            team, created = ResearchTeam.objects.get_or_create(
                                research_details=research,
                                defaults={'team_name': f"Research Team - {research.title}"}
                            )
                            
                            # Create or get team member
                            team_member, created = ResearchTeamMember.objects.get_or_create(
                                team=team,
                                faculty=faculty_profile,
                                defaults={'role': 'MENTOR'}
                            )
                            team_member_id = team_member.id
                        elif team_member_id.startswith('app_'):
                            # Handle student from application
                            app_id = team_member_id.replace('app_', '')
                            application = get_object_or_404(StudentResearchApplication, application_id=app_id)
                            
                            # Create a team if it doesn't exist
                            team, created = ResearchTeam.objects.get_or_create(
                                research_details=research,
                                defaults={'team_name': f"Research Team - {research.title}"}
                            )
                            
                            # Create or get team member
                            team_member, created = ResearchTeamMember.objects.get_or_create(
                                team=team,
                                student=application.student,
                                defaults={'role': 'STUDENT'}
                            )
                            team_member_id = team_member.id
                    
                    # Get the team member
                    team_member = get_object_or_404(ResearchTeamMember, id=team_member_id)
                    
                    PublicationAuthor.objects.create(
                        publication=publication,
                        team_member=team_member,
                        author_role=author_role,
                        author_order=author_order
                    )
                    
                except Exception as e:
                    print(f"Error adding author: {e}")
                    continue
        
        # Return the publication data
        authors_list = []
        for author in publication.authors.all().order_by('author_order'):
            team_member = author.team_member
            if team_member.faculty:
                name = team_member.faculty.user.get_full_name() if team_member.faculty.user else str(team_member.faculty)
                team_role = team_member.get_role_display()
            elif team_member.student:
                name = team_member.student.user.get_full_name() if team_member.student.user else str(team_member.student)
                team_role = "Student"
            else:
                continue
            
            authors_list.append({
                'id': author.id,
                'name': name,
                'author_role': author.get_author_role_display(),
                'team_member_role': team_role,
                'order': author.author_order,
                'team_member_id': team_member.id
            })
        
        return JsonResponse({
            'success': True,
            'message': message,
            'publication': {
                'id': publication.publication_id,
                'uuid': str(publication.publication_uuid),
                'title': publication.title,
                'abstract': publication.abstract,
                'keywords': publication.keywords,
                'publication_type_display': publication.get_publication_type_display(),
                'status_display': publication.get_status_display(),
                'created_at': publication.created_at.strftime('%Y-%m-%d %H:%M'),
                'authors': authors_list,
                'author_count': len(authors_list)
            }
        })
        
    except FacultyProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Faculty profile not found'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def update_publication_status(request):
    """
    API endpoint to update publication status
    """
    try:
        data = json.loads(request.body)
        publication_id = data.get('publication_id')
        new_status = data.get('status')
        
        if not publication_id or not new_status:
            return JsonResponse({
                'success': False,
                'error': 'Publication ID and status are required'
            }, status=400)
        
        publication = get_object_or_404(StudentResearchPublication, publication_id=publication_id)
        
        # Check permission
        if publication.created_by and publication.created_by.user != request.user:
            return JsonResponse({
                'success': False,
                'error': 'You do not have permission to update this publication'
            }, status=403)
        
        valid_statuses = [choice[0] for choice in StudentResearchPublication.STATUS_CHOICES]
        if new_status.upper() not in valid_statuses:
            return JsonResponse({
                'success': False,
                'error': f'Invalid status. Valid statuses: {", ".join(valid_statuses)}'
            }, status=400)
        
        publication.status = new_status.upper()
        publication.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Publication status updated to {publication.get_status_display()}',
            'data': {
                'status': publication.status.lower(),
                'status_display': publication.get_status_display()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


    
# ================================ Research Submissions ===============================

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime

from Research.models import (
    ResearchOpportunity, ResearchTeam, ResearchTeamMember, 
    StudentResearchApplication, StudentResearchPublication, 
    PublicationAuthor, PublicationSubmission
)
from Faculty.models import FacultyProfile


@login_required
def research_submissions_mentor(request, uuid):
    """
    View for research submissions page
    """
    return render(request, 'jordan/research_submission_mentor.html')


@login_required
@require_http_methods(["GET"])
def get_faculty_research_projects_with_submissions(request):
    """
    API endpoint to get all research projects with submission status for logged-in faculty
    """
    try:
        faculty = FacultyProfile.objects.get(user=request.user)
        
        projects = ResearchOpportunity.objects.filter(
            faculty=faculty
        ).select_related('department')
        
        project_list = []
        for project in projects:
            # Get team members
            team_members = []
            try:
                research_team = ResearchTeam.objects.get(research_details=project)
                team_members_qs = ResearchTeamMember.objects.filter(team=research_team).select_related(
                    'faculty__user', 'student__user'
                )
                for member in team_members_qs:
                    if member.faculty:
                        name = member.faculty.user.get_full_name() if member.faculty.user else str(member.faculty)
                    elif member.student:
                        name = member.student.user.get_full_name() if member.student.user else str(member.student)
                    else:
                        continue
                    team_members.append({'name': name, 'id': member.id, 'role': member.get_role_display()})
            except ResearchTeam.DoesNotExist:
                pass
            
            # Get publication
            publication = StudentResearchPublication.objects.filter(research=project).first()
            
            has_submission = False
            submission = None
            
            if publication:
                # Get authors
                authors = []
                for author in publication.authors.all().order_by('author_order'):
                    team_member = author.team_member
                    if team_member.faculty:
                        name = team_member.faculty.user.get_full_name() if team_member.faculty.user else str(team_member.faculty)
                    elif team_member.student:
                        name = team_member.student.user.get_full_name() if team_member.student.user else str(team_member.student)
                    else:
                        continue
                    authors.append({
                        'name': name,
                        'role': author.get_author_role_display(),
                        'order': author.author_order
                    })
                
                # Check if submission exists
                submission_obj = PublicationSubmission.objects.filter(publication=publication).first()
                if submission_obj:
                    has_submission = True
                    submission = {
                        'id': submission_obj.id,
                        'publication_id': publication.publication_id,
                        'title': publication.title,
                        'abstract': publication.abstract,
                        'keywords': publication.keywords,
                        'publication_type': publication.publication_type,
                        'type_display': publication.get_publication_type_display(),
                        'status': submission_obj.status.lower() if submission_obj.status else 'draft',
                        'status_display': submission_obj.get_status_display() if submission_obj.status else 'Draft',
                        'journal_name': submission_obj.journal_name,
                        'conference_name': submission_obj.conference_name,
                        'publisher': submission_obj.publisher,
                        'submission_date': submission_obj.submission_date.isoformat() if submission_obj.submission_date else None,
                        'acceptance_date': submission_obj.acceptance_date.isoformat() if submission_obj.acceptance_date else None,
                        'publication_date': submission_obj.publication_date.isoformat() if submission_obj.publication_date else None,
                        'manuscript_number': submission_obj.manuscript_number,
                        'doi': submission_obj.doi,
                        'publication_url': submission_obj.publication_url,
                        'authors': authors,
                        'author_count': len(authors)
                    }
                else:
                    # Publication exists but no submission yet
                    submission = {
                        'publication_id': publication.publication_id,
                        'title': publication.title,
                        'abstract': publication.abstract,
                        'keywords': publication.keywords,
                        'publication_type': publication.publication_type,
                        'type_display': publication.get_publication_type_display(),
                        'authors': authors,
                        'author_count': len(authors),
                        'journal_name': '',
                        'conference_name': '',
                        'publisher': '',
                        'submission_date': None,
                        'acceptance_date': None,
                        'publication_date': None,
                        'manuscript_number': '',
                        'doi': '',
                        'publication_url': ''
                    }
            
            project_list.append({
                'id': project.research_id,
                'uuid': str(project.research_uuid),
                'title': project.title,
                'description': project.short_description or project.description,
                'category': project.category,
                'status': project.status.lower(),
                'status_display': project.get_status_display(),
                'project_status': project.project_status.lower(),
                'project_status_display': project.get_project_status_display(),
                'department': project.department.department_name if project.department else 'No Department',
                'start_date': project.start_date.isoformat() if project.start_date else None,
                'end_date': project.end_date.isoformat() if project.end_date else None,
                'team_members': team_members,
                'has_publication': bool(publication),
                'has_submission': has_submission,
                'submission': submission
            })
        
        return JsonResponse({
            'success': True,
            'projects': project_list
        })
        
    except FacultyProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Faculty profile not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_project_submission(request):
    """
    API endpoint to get submission details for a specific project
    """
    try:
        project_id = request.GET.get('project_id')
        
        if not project_id:
            return JsonResponse({
                'success': False,
                'error': 'Project ID is required'
            }, status=400)
        
        faculty = FacultyProfile.objects.get(user=request.user)
        project = get_object_or_404(ResearchOpportunity, research_id=project_id, faculty=faculty)
        
        # Get the publication linked to this research
        publication = StudentResearchPublication.objects.filter(research=project).first()
        
        if not publication:
            return JsonResponse({
                'success': False,
                'error': 'No publication found for this project'
            }, status=404)
        
        # Get authors
        authors = []
        for author in publication.authors.all().order_by('author_order'):
            team_member = author.team_member
            if team_member.faculty:
                name = team_member.faculty.user.get_full_name() if team_member.faculty.user else str(team_member.faculty)
            elif team_member.student:
                name = team_member.student.user.get_full_name() if team_member.student.user else str(team_member.student)
            else:
                continue
            
            authors.append({
                'id': author.id,
                'name': name,
                'role': author.get_author_role_display(),
                'order': author.author_order,
                'team_member_id': team_member.id
            })
        
        # Get submission
        submission_obj = PublicationSubmission.objects.filter(publication=publication).first()
        
        submission_data = {
            'publication_id': publication.publication_id,
            'title': publication.title,
            'abstract': publication.abstract,
            'keywords': publication.keywords,
            'publication_type': publication.publication_type,
            'type_display': publication.get_publication_type_display(),
            'authors': authors,
            'author_count': len(authors),
            'journal_name': '',
            'conference_name': '',
            'publisher': '',
            'submission_date': None,
            'acceptance_date': None,
            'publication_date': None,
            'manuscript_number': '',
            'doi': '',
            'publication_url': ''
        }
        
        if submission_obj:
            submission_data.update({
                'id': submission_obj.id,
                'status': submission_obj.status.lower() if submission_obj.status else 'draft',
                'status_display': submission_obj.get_status_display() if submission_obj.status else 'Draft',
                'journal_name': submission_obj.journal_name,
                'conference_name': submission_obj.conference_name,
                'publisher': submission_obj.publisher,
                'submission_date': submission_obj.submission_date.isoformat() if submission_obj.submission_date else None,
                'acceptance_date': submission_obj.acceptance_date.isoformat() if submission_obj.acceptance_date else None,
                'publication_date': submission_obj.publication_date.isoformat() if submission_obj.publication_date else None,
                'manuscript_number': submission_obj.manuscript_number,
                'doi': submission_obj.doi,
                'publication_url': submission_obj.publication_url,
            })
            has_submission = True
        else:
            has_submission = False
        
        return JsonResponse({
            'success': True,
            'has_submission': has_submission,
            'submission': submission_data
        })
        
    except FacultyProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Faculty profile not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def create_or_update_submission(request):
    """
    API endpoint to create or update a submission using PublicationSubmission model
    """
    try:
        data = json.loads(request.body)
        
        project_id = data.get('project_id')
        submission_id = data.get('submission_id')
        
        # Submission fields only
        journal_name = data.get('journal_name', '')
        conference_name = data.get('conference_name', '')
        publisher = data.get('publisher', '')
        submission_date = data.get('submission_date')
        manuscript_number = data.get('manuscript_number', '')
        acceptance_date = data.get('acceptance_date')
        publication_date = data.get('publication_date')
        doi = data.get('doi', '')
        publication_url = data.get('publication_url', '')
        status = data.get('status', 'DRAFT')
        
        faculty = FacultyProfile.objects.get(user=request.user)
        research = get_object_or_404(ResearchOpportunity, research_id=project_id, faculty=faculty)
        
        # Get the publication linked to this research
        publication = StudentResearchPublication.objects.filter(research=research).first()
        
        if not publication:
            return JsonResponse({
                'success': False,
                'error': 'No publication found for this project. Please create a publication first.'
            }, status=400)
        
        # Create or update submission
        if submission_id:
            submission = get_object_or_404(PublicationSubmission, id=submission_id)
            message = 'Submission updated successfully'
        else:
            existing_submission = PublicationSubmission.objects.filter(publication=publication).first()
            if existing_submission:
                submission = existing_submission
                message = 'Submission updated successfully'
            else:
                submission = PublicationSubmission(publication=publication)
                message = 'Submission created successfully'
        
        # Update submission fields - handle date conversion properly
        submission.journal_name = journal_name if publication.publication_type == 'JOURNAL' else ''
        submission.conference_name = conference_name if publication.publication_type == 'CONFERENCE' else ''
        submission.publisher = publisher
        
        # Convert date strings to date objects
        if submission_date:
            try:
                submission.submission_date = datetime.strptime(submission_date, '%Y-%m-%d').date()
            except ValueError:
                submission.submission_date = None
        else:
            submission.submission_date = None
        
        submission.manuscript_number = manuscript_number
        
        if acceptance_date:
            try:
                submission.acceptance_date = datetime.strptime(acceptance_date, '%Y-%m-%d').date()
            except ValueError:
                submission.acceptance_date = None
        else:
            submission.acceptance_date = None
        
        if publication_date:
            try:
                submission.publication_date = datetime.strptime(publication_date, '%Y-%m-%d').date()
            except ValueError:
                submission.publication_date = None
        else:
            submission.publication_date = None
        
        submission.doi = doi
        submission.publication_url = publication_url
        submission.status = status.upper() if status else 'DRAFT'
        submission.save()
        
        # Get authors for response
        authors = []
        for author in publication.authors.all().order_by('author_order'):
            team_member = author.team_member
            if team_member.faculty:
                name = team_member.faculty.user.get_full_name() if team_member.faculty.user else str(team_member.faculty)
            elif team_member.student:
                name = team_member.student.user.get_full_name() if team_member.student.user else str(team_member.student)
            else:
                continue
            authors.append({
                'name': name,
                'role': author.get_author_role_display()
            })
        
        # Prepare response data - safely handle None values
        response_data = {
            'submission_id': submission.id,
            'publication_id': publication.publication_id,
            'title': publication.title,
            'abstract': publication.abstract,
            'keywords': publication.keywords,
            'publication_type': publication.get_publication_type_display(),
            'status': submission.status.lower(),
            'status_display': submission.get_status_display(),
            'journal_name': submission.journal_name,
            'conference_name': submission.conference_name,
            'publisher': submission.publisher,
            'submission_date': submission.submission_date.isoformat() if submission.submission_date else None,
            'acceptance_date': submission.acceptance_date.isoformat() if submission.acceptance_date else None,
            'publication_date': submission.publication_date.isoformat() if submission.publication_date else None,
            'manuscript_number': submission.manuscript_number,
            'doi': submission.doi,
            'publication_url': submission.publication_url,
            'authors': authors
        }
        
        return JsonResponse({
            'success': True,
            'message': message,
            'data': response_data
        })
        
    except FacultyProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Faculty profile not found'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

    
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def update_submission_status(request):
    """
    API endpoint to update submission status using PublicationSubmission model
    """
    try:
        data = json.loads(request.body)
        submission_id = data.get('submission_id')
        new_status = data.get('status')
        
        if not submission_id or not new_status:
            return JsonResponse({
                'success': False,
                'error': 'Submission ID and status are required'
            }, status=400)
        
        submission = get_object_or_404(PublicationSubmission, id=submission_id)
        
        valid_statuses = [choice[0] for choice in PublicationSubmission.STATUS_CHOICES]
        if new_status.upper() not in valid_statuses:
            return JsonResponse({
                'success': False,
                'error': f'Invalid status. Valid statuses: {", ".join(valid_statuses)}'
            }, status=400)
        
        submission.status = new_status.upper()
        submission.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Submission status updated to {submission.get_status_display()}',
            'data': {
                'status': submission.status.lower(),
                'status_display': submission.get_status_display()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

        