from django.shortcuts import render,redirect,get_object_or_404
from django.db.models import Count
from Admin.models import User
from django.db.models.functions import ExtractYear
from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.platypus import (SimpleDocTemplate,Table,TableStyle, Paragraph,Spacer,Image)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from django.conf import settings
import os
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import HRFlowable
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField
from django.db.models.functions import TruncDate, ExtractHour
from django.http import JsonResponse
from Admin.models import UserAuditLog, UserSession
from django.contrib.sessions.models import Session
from Admin.Jack.models import Sport, SportsFacility,SportClub,SportTeamModel,Coach
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Prefetch
from Staff.models import StaffProfile, StaffPosition, StaffDepartmentAssignment
from django.templatetags.static import static
from datetime import date,datetime
from django.template.loader import render_to_string
import json


#################################  user_reports start #############################################################
def user_reports(request):

    total_users=User.objects.count()
    active_users=User.objects.filter(account_status="ACTIVE").count()
    students=User.objects.filter(is_student=True).count()
    faculty=User.objects.filter(is_faculty=True).count()
    admins=User.objects.filter(is_admin=True).count()

    today = timezone.now()

    current_month = today.month
    current_year = today.year

    if current_month == 1:
        previous_month = 12
        previous_year = current_year - 1
    else:
        previous_month = current_month - 1
        previous_year = current_year

    current_total = User.objects.filter(
    created_at__year=current_year,
    created_at__month=current_month
     ).count()

    previous_total = User.objects.filter(
        created_at__year=previous_year,
        created_at__month=previous_month
    ).count()

    if previous_total > 0:
        total_growth = round(
            ((current_total - previous_total) / previous_total) * 100,
            1
        )
    else:
        total_growth = 100 if current_total > 0 else 0

    current_active_login = User.objects.filter(
    last_login__year=current_year,
    last_login__month=current_month
    ).count()

    previous_active_login = User.objects.filter(
        last_login__year=previous_year,
        last_login__month=previous_month
    ).count()

    if previous_active_login > 0:
        active_growth = round(
            ((current_active_login - previous_active_login)
            / previous_active_login) * 100,
            1
        )
    else:
       active_growth = 100 if current_active_login > 0 else 0

    current_students = User.objects.filter(
    is_student=True,
    created_at__year=current_year,
    created_at__month=current_month
    ).count()

    previous_students = User.objects.filter(
        is_student=True,
        created_at__year=previous_year,
        created_at__month=previous_month
    ).count()

    if previous_students > 0:
        student_growth = round(
            ((current_students - previous_students)
            / previous_students) * 100,
            1
        )
    else:
        student_growth = 100 if current_students > 0 else 0

    current_faculty = User.objects.filter(
    is_faculty=True,
    created_at__year=current_year,
    created_at__month=current_month
    ).count()

    previous_faculty = User.objects.filter(
        is_faculty=True,
        created_at__year=previous_year,
        created_at__month=previous_month
    ).count()

    if previous_faculty > 0:
        faculty_growth = round(
            ((current_faculty - previous_faculty)
            / previous_faculty) * 100,
            1
        )
    else:
        faculty_growth = 100 if current_faculty > 0 else 0

    current_admin = User.objects.filter(
    is_admin=True,
    created_at__year=current_year,
    created_at__month=current_month
    ).count()

    previous_admin = User.objects.filter(
        is_admin=True,
        created_at__year=previous_year,
        created_at__month=previous_month
    ).count()

    if previous_admin > 0:
        admin_growth = round(
            ((current_admin - previous_admin)
            / previous_admin) * 100,
            1
        )
    else:
        admin_growth = 100 if current_admin > 0 else 0
    
    male_count=User.objects.filter(gender="MALE").count()
    female_count=User.objects.filter(gender="FEMALE").count()
    transgender_count=User.objects.filter(gender="TRANSGENDER").count()
    non_binary_count = User.objects.filter(gender="NON_BINARY").count()
    other_count = User.objects.filter(gender="OTHER").count()
    prefer_not_say_count = User.objects.filter(gender="PREFER_NOT_TO_SAY").count()
    
    active_count = User.objects.filter(account_status="ACTIVE").count()
    inactive_count = User.objects.filter(account_status="INACTIVE").count()
    pending_count = User.objects.filter(account_status="PENDING").count()
    suspended_count = User.objects.filter(account_status="SUSPENDED").count()
    
    registration_data = (User.objects.annotate(year=ExtractYear("created_at"))
                         .values("year").annotate(total=Count("id")).order_by("year"))
    year_dict = {
        row["year"]: row["total"]
        for row in registration_data
    }
    registration_years = []
    registration_counts = []

    for year in range(2021, 2027):
        registration_years.append(str(year))
        registration_counts.append(
        year_dict.get(year, 0) )
    
    # =====================================================
    # RECENT REGISTRATIONS + OVERALL DATABASE SEARCH
    # =====================================================

    six_months_ago = timezone.now() - timedelta(days=180)

    # Get search value
    search_query = request.GET.get("q", "").strip()


    # Base queryset
    recent_users_queryset = User.objects.filter(
        created_at__gte=six_months_ago
    )


    # Search across ALL recent registration records
    if search_query:
        recent_users_queryset = recent_users_queryset.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(university_id__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(role__role_name__icontains=search_query) |
            Q(gender__icontains=search_query) |
            Q(account_status__icontains=search_query)
        )


    # Order results
    recent_users_queryset = recent_users_queryset.order_by(
        "-created_at"
    )


    # Pagination - ONLY 5 RECORDS PER PAGE
    paginator = Paginator(recent_users_queryset, 5)

    page_number = request.GET.get("page")

    recent_users = paginator.get_page(page_number)
    context = {
        "total_users": total_users,
        "active_users": active_users,
        "students": students,
        "faculty": faculty,
        "admins": admins,

        "total_growth": total_growth,
        "active_growth": active_growth,
        "student_growth": student_growth,
        "faculty_growth": faculty_growth,
        "admin_growth": admin_growth,

        "male_count": male_count,
        "female_count": female_count,
        "transgender_count": transgender_count,
        "non_binary_count": non_binary_count,
        "other_count": other_count,
        "prefer_not_say_count": prefer_not_say_count,

        "active_count": active_count,
        "inactive_count": inactive_count,
        "pending_count": pending_count,
        "suspended_count": suspended_count,

        "registration_years": registration_years,
        "registration_counts": registration_counts,

        "recent_users": recent_users,
        "search_query": search_query,
    }
    
    
    return render(request, "reports/user_reports.html",context)

# download excel
def export_users_excel(request):
    wb=Workbook()
    ws=wb.active
    ws.title="User Reports"
    headers=["Name","Username","University ID","Email","Role","Gender","Status","Created On"]
    ws.append(headers)
    users=User.objects.all()
    for user in users:
        role=("student" if user.is_student else
              "Faculty" if user.is_faculty else
              "Admin" if user.is_admin else
              "staff"
              )
        ws.append([
            f"{user.first_name} {user.last_name}",
            user.username, 
            user.university_id,
            user.email,
            role,
            user.get_gender_display(),
            user.get_account_status_display(),
            user.created_at.strftime("%d-%m-%Y")
        ])
    response=HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"]=('attachment; filename=users_report.xlsx')
    wb.save(response)
    return response

# pdf view

def export_users_pdf(request):

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = ('attachment; filename="users_report.pdf"')
    doc = SimpleDocTemplate(response,pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    logo_path = os.path.join(settings.BASE_DIR,
        "admin",
        "static",
        "images",
        "logo-photoroom.png"
    )
    logo = Image(logo_path,width=60,height=60)
    logo.hAlign = "CENTER"
    elements.append(logo)

    university_style = ParagraphStyle(
      "UniversityStyle",
       parent=styles["Normal"],
       alignment=TA_CENTER,
       fontSize=20,
       leading=24,
       textColor=colors.HexColor("#a8040a")
    )

    address_style = ParagraphStyle(
    "AddressStyle",
    parent=styles["Normal"],
    alignment=TA_CENTER,
    fontSize=10,
    textColor=colors.grey
    )

    title = [
    Paragraph("<b>University of Wisconsin</b>",university_style),
    Paragraph("500 Lincoln Drive, Madison, WI 53706<br/>https://www.wisc.edu/",address_style)
    ]

    header = Table([[ title]],colWidths=[515])
    header.setStyle(TableStyle([
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ('TOPPADDING', (0, 0), (-1, -1), 0),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
]))
    elements.append(header)
    elements.append(Spacer(1, 15))

    users = User.objects.all()
    filter_text = "All Users"
    role = request.GET.get("role")
    gender = request.GET.get("gender")
    status = request.GET.get("status")
    if role:
        filter_text = f"Role : {role.title()}"
        if role == "student":
            users = users.filter(is_student=True)

        elif role == "faculty":
            users = users.filter(is_faculty=True)

        elif role == "admin":
            users = users.filter(is_admin=True)

        elif role == "staff":
            users = users.filter(is_staff=True)
    elif gender:

        filter_text = f"Gender : {gender.title()}"
        users = users.filter(gender=gender.upper())
    elif status:
        filter_text = f"Status : {status}"
        users = users.filter(account_status=status)

    elements.append(
        HRFlowable(
        width="100%",
        thickness=1,
        color=colors.HexColor("#a8040a")
    )
)
    subheading_style=styles["Heading3"]
    subheading_style.alignment=TA_CENTER
    subheading_style.fontname="Helvetica-Bold"
    elements.append(
        Paragraph("USER REPORT", subheading_style)
    )
    elements.append(
        Paragraph(
            f"<b>Filter Applied:</b> {filter_text}",
            styles["Normal"]
        )
    )
    elements.append(Spacer(1, 15))

    data = [["Name","Username","University ID","Email","Role","Gender","Status","Created On"]]

    for user in users:
        role_name = (
            "Student" if user.is_student else
            "Faculty" if user.is_faculty else
            "Admin" if user.is_admin else
            "Staff"
        )
        data.append([
            f"{user.first_name} {user.last_name}",
            user.username,
            user.university_id,
            user.email,
            role_name,
            user.get_gender_display(),
            user.get_account_status_display(),
            user.created_at.strftime("%d-%m-%Y")
        ])
    table = Table(data)
    table.setStyle(TableStyle([

        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#c5050c")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS',
         (0, 1),
         (-1, -1),
         [colors.transparent])
    ]))
    elements.append(table)
    doc.build(elements,onFirstPage=add_watermark,onLaterPages=add_watermark)
    return response


# water mark
def add_watermark(canvas, doc):
    canvas.saveState()
    canvas.setFillAlpha(0.08)
    canvas.translate(350,5)
    canvas.rotate(45)
    logo_path = os.path.join(settings.BASE_DIR,"admin","static","images","logo-black.png")

    canvas.drawImage(logo_path,120,180,width=350,height=350,mask='auto')
    canvas.restoreState()

    canvas.saveState()
    page_width, page_height = A4

    canvas.setStrokeColor(colors.grey)
    canvas.line(40,35,page_width - 40,35)

    canvas.setFont("Helvetica",8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(40,20,"© University of Wisconsin–Madison Since 1881")

    canvas.drawRightString(page_width - 40,20, f"Page {doc.page}")
    canvas.restoreState()

#################################  user_reports end #############################################################


#################################  login_reports start #############################################################
# login reports
@login_required
def login_reports(request):
    return render(request, "reports/login_reports.html")

@login_required
def login_reports_json(request):

  
    total_logins = UserAuditLog.objects.filter(
        action="LOGIN",
        status="SUCCESS"
    ).count()

    online_users=Session.objects.filter(expire_date__gte=timezone.now()).count()

    failed_logins = UserAuditLog.objects.filter(action="LOGIN",status="FAILED").count()

    avrg_logins = UserAuditLog.objects.filter(
    action="LOGIN",
    status="SUCCESS",
    timestamp__gte=timezone.now() - timedelta(days=7)).count()
    avg_logins=round(avrg_logins/7,2)

    todays_logins = UserAuditLog.objects.filter(
        action="LOGIN",
        status="SUCCESS",
        timestamp__date=timezone.now().date()
    ).count()
       

    last7 = timezone.now() - timedelta(days=6)
    trend = (
        UserAuditLog.objects.filter(action="LOGIN",status="SUCCESS",timestamp__date__gte=last7.date())
        .annotate(day=TruncDate("timestamp"))
        .values("day")
        .annotate(total=Count("id"))
        .order_by("day")
    )
    trend_dict = {
        row["day"]: row["total"]
        for row in trend
    }

    trend_labels = []
    trend_values = []
    for i in range(7):

        day = (last7 + timedelta(days=i)).date()
        trend_labels.append(day.strftime("%a"))
        trend_values.append(trend_dict.get(day, 0))

    device_data = (UserAuditLog.objects.filter(action="LOGIN",status="SUCCESS").values("device").annotate(total=Count("id")).order_by("-total"))

    device_labels = []
    device_values = []

    for row in device_data:
        device_labels.append(row["device"] if row["device"] else "Anonymous")
        device_values.append(row["total"])

    browser_data = (
        UserAuditLog.objects.filter(action="LOGIN",status="SUCCESS").values("browser").annotate(total=Count("id")).order_by("-total"))
    browser_labels = []
    browser_values = []

    for row in browser_data:
        browser_labels.append(row["browser"] if row["browser"] else "Anonymous")
        browser_values.append(row["total"])

    hour_data = (
        UserAuditLog.objects.filter(
            action="LOGIN",
            status="SUCCESS"
        ).annotate(hour=ExtractHour("timestamp")).values("hour").annotate(total=Count("id")).order_by("hour")
    )

    hour_dict = {
        row["hour"]: row["total"]
        for row in hour_data
    }

    hour_labels = []
    hour_values = []

    for hour in range(24):
        hour_labels.append(f"{hour}:00")
        hour_values.append(
            hour_dict.get(hour, 0)
        )

    today = timezone.now()

    current_month = today.month
    current_year = today.year

    if current_month == 1:
        previous_month = 12
        previous_year = current_year - 1
    else:
        previous_month = current_month - 1
        previous_year = current_year

    current_total_logins = UserAuditLog.objects.filter(
    action="LOGIN",
    status="SUCCESS",
    timestamp__year=current_year,
    timestamp__month=current_month
    ).count()

    previous_total_logins = UserAuditLog.objects.filter(
        action="LOGIN",
        status="SUCCESS",
        timestamp__year=previous_year,
        timestamp__month=previous_month
    ).count()

    if previous_total_logins > 0:
        total_login_growth = round(
            ((current_total_logins - previous_total_logins) / previous_total_logins) * 100,
            1
        )
    else:
        total_login_growth = 100 if current_total_logins > 0 else 0

    current_failed = UserAuditLog.objects.filter(
    action="LOGIN",
    status="FAILED",
    timestamp__year=current_year,
    timestamp__month=current_month
    ).count()

    previous_failed = UserAuditLog.objects.filter(
        action="LOGIN",
        status="FAILED",
        timestamp__year=previous_year,
        timestamp__month=previous_month
    ).count()

    if previous_failed > 0:
        failed_growth = round(
            ((current_failed - previous_failed) / previous_failed) * 100,
            1
        )
    else:
        failed_growth = 100 if current_failed > 0 else 0

    current_failed = UserAuditLog.objects.filter(
        action="LOGIN",
        status="FAILED",
        timestamp__year=current_year,
        timestamp__month=current_month
    ).count()

    previous_failed = UserAuditLog.objects.filter(
        action="LOGIN",
        status="FAILED",
        timestamp__year=previous_year,
        timestamp__month=previous_month
    ).count()

    if previous_failed > 0:
        failed_growth = round(
            ((current_failed - previous_failed) / previous_failed) * 100,
            1
        )
    else:
        failed_growth = 100 if current_failed > 0 else 0

    today_count = UserAuditLog.objects.filter(
    action="LOGIN",
    status="SUCCESS",
    timestamp__date=timezone.now().date()
).count()

    yesterday = timezone.now().date() - timedelta(days=1)

    yesterday_count = UserAuditLog.objects.filter(
        action="LOGIN",
        status="SUCCESS",
        timestamp__date=yesterday
    ).count()

    if yesterday_count > 0:
        today_growth = round(
            ((today_count - yesterday_count) / yesterday_count) * 100,
            1
        )
    else:
        today_growth = 100 if today_count > 0 else 0

    return JsonResponse({
        "cards": {
            "total_logins": total_logins,
            "online_users": online_users,
            "failed_logins": failed_logins,
            "avg_logins":avg_logins,
            "todays_logins": todays_logins,


            "total_login_growth": total_login_growth,
            "failed_growth": failed_growth,
            "today_growth": today_growth,
        },
        "login_trend": {
            "labels": trend_labels,
            "values": trend_values,
        },
        "login_status": {
            "success": total_logins,
            "failed": failed_logins,
        },
        "device_usage": {
            "labels": device_labels,
            "values": device_values,
        },
        "browser_usage": {
            "labels": browser_labels,
            "values": browser_values,
        },
        "peak_hours": {
            "labels": hour_labels,
            "values": hour_values,
        }
    })

# recent sessions
@login_required
def recent_sessions_json(request):

    page = request.GET.get("page", 1)
    status = request.GET.get("status")
    logs = []

    audits = UserAuditLog.objects.filter(action="LOGIN")
    if status:
        audits = audits.filter(status=status)
    audits = audits.select_related(
        "user",
        "user__role"
    ).order_by("-timestamp")
    paginator = Paginator(audits, 5)
    page = request.GET.get("page", 1)
    page_obj = paginator.get_page(page)
    for audit in page_obj:
        logs.append({
            "user": audit.user.username if audit.user else "Anonymous",
            "role": audit.user.role.role_name if audit.user and audit.user.role else "--",
            "login_time": audit.timestamp,
            "device": audit.device or "--",
            "browser": audit.browser or "--",
            "ip": audit.ip_address or "--",
            "status": audit.status,
        })

    return JsonResponse({
    "logs": logs,

    "current_page": page_obj.number,
    "total_pages": paginator.num_pages,

    "has_next": page_obj.has_next(),
    "has_previous": page_obj.has_previous(),

    "previous_page": page_obj.previous_page_number() if page_obj.has_previous() else None,

    "next_page": page_obj.next_page_number() if page_obj.has_next() else None,

    "page_range": list(paginator.page_range),

    "start_index": page_obj.start_index(),

    "end_index": page_obj.end_index(),

    "count": paginator.count,

})


# pdf for login
@login_required
def export_login_pdf(request):

    status = request.GET.get("status")

    logs = UserAuditLog.objects.filter(action="LOGIN")

    if status in ["SUCCESS", "FAILED"]:
        logs = logs.filter(status=status)

    logs = logs.order_by("-timestamp")

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="login_reports.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # ================= HEADER LOGO =================
    logo_path = os.path.join(
        settings.BASE_DIR,
        "admin",
        "static",
        "images",
        "logo-photoroom.png"
    )

    logo = Image(logo_path, width=60, height=60)
    logo.hAlign = "CENTER"
    elements.append(logo)

    # ================= UNIVERSITY TITLE =================
    university_style = ParagraphStyle(
        "UniversityStyle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#a8040a")
    )

    address_style = ParagraphStyle(
        "AddressStyle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.grey
    )

    title = [
        Paragraph("<b>Login Activity Report</b>", university_style),
        Paragraph("University Login Monitoring System", address_style)
    ]

    header = Table([[title]], colWidths=[515])
    header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    elements.append(header)
    elements.append(Spacer(1, 15))

    # ================= FILTER INFO =================
    filter_text = "All Logins"
    if status:
        filter_text = f"Status: {status}"

    elements.append(HRFlowable(
        width="100%",
        thickness=1,
        color=colors.HexColor("#a8040a")
    ))

    subheading_style = styles["Heading3"]
    subheading_style.alignment = TA_CENTER

    elements.append(Paragraph("LOGIN REPORT", subheading_style))
    elements.append(Paragraph(f"<b>Filter Applied:</b> {filter_text}", styles["Normal"]))
    elements.append(Spacer(1, 15))

    # ================= TABLE DATA =================
    data = [["User", "Role", "Login Time", "Device", "Browser", "IP", "Status"]]

    for log in logs:
        data.append([
            log.user.username if log.user else "Unknown",
            log.user.role.role_name if log.user and log.user.role else "--",
            log.timestamp.strftime("%d-%m-%Y %H:%M"),
            log.device or "--",
            log.browser or "--",
            log.ip_address or "--",
            log.status
        ])

    table = Table(data)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#c5050c")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white]),
    ]))

    elements.append(table)

    # ================= BUILD WITH WATERMARK =================
    doc.build(
        elements,
        onFirstPage=add_watermark,
        onLaterPages=add_watermark
    )

    return response

# excel for login report
@login_required
def export_login_excel(request):

    wb = Workbook()
    ws = wb.active
    ws.title = "All Login Reports"

    ws.append(["User", "Role", "Login Time", "Device", "Browser", "IP", "Status"])

    logs = UserAuditLog.objects.filter(action="LOGIN").order_by("-timestamp")

    for log in logs:
        ws.append([
            log.user.username if log.user else "Unknown",
            log.user.role.role_name if log.user and log.user.role else "--",
            log.timestamp.strftime("%d-%m-%Y %H:%M"),
            log.device or "--",
            log.browser or "--",
            log.ip_address or "--",
            log.status
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="login_reports.xlsx"'

    wb.save(response)
    return response

#################################  user_reports end #############################################################


############################ facility view start ###############################

@login_required
def facility(request):

    facilities_qs = (
        SportsFacility.objects
        .select_related("sport")
        .all()
        .order_by("-created_at")
    )

    search = request.GET.get(
        "search",
        ""
    ).strip()

    sport = request.GET.get(
        "sport",
        ""
    ).strip()

    facility_type = request.GET.get(
        "type",
        ""
    ).strip()

    status = request.GET.get(
        "status",
        ""
    ).strip()

    if search:

        facilities_qs = facilities_qs.filter(

            Q(
                facility_name__icontains=search
            )
            |
            Q(
                location__icontains=search
            )
            |
            Q(
                sport__sport_name__icontains=search
            )

        )

    if sport:

        facilities_qs = facilities_qs.filter(
            sport_id=sport
        )

    if facility_type:

        facilities_qs = facilities_qs.filter(
            facility_type=facility_type
        )

    if status:

        facilities_qs = facilities_qs.filter(
            status=status
        )

    paginator = Paginator(
        facilities_qs,
        9
    )


    page_number = request.GET.get(
        "page",
        1
    )


    facilities = paginator.get_page(
        page_number
    )

    context = {

        "sports":
            Sport.objects.all(),

        "facilities":
            facilities,

        "facility_types":
            SportsFacility.FACILITY_TYPES,

        "facility_status":
            SportsFacility.STATUS_CHOICES,

        "search":
            search,

        "sport":
            sport,

        "facility_type":
            facility_type,

        "status":
            status,

    }

    return render(
        request,
        "reports/facility.html",
        context
    )


@login_required
def add_facility(request):
    if request.method == "POST":

        SportsFacility.objects.create(
            facility_name=request.POST.get("facility_name"),
            facility_type=request.POST.get("facility_type"),
            capacity=request.POST.get("capacity"),
            location=request.POST.get("location"),
            status=request.POST.get("status")
        )

        return JsonResponse({"success": True})

def facility_save(request):
    if request.method == "POST":
        sport = None
        sport_id = request.POST.get("sport")
        facility_name = request.POST.get("facility_name").strip()
        if sport_id:
            sport = Sport.objects.get(id=sport_id)

        if SportsFacility.objects.filter(facility_name__iexact=facility_name).exists():
            return JsonResponse({
                "success": False,
                "message": "Facility already exists."
            })

        SportsFacility.objects.create(
            facility_name=request.POST.get("facility_name"),
            sport=sport,
            facility_type=request.POST.get("facility_type"),
            capacity=request.POST.get("capacity"),
            location=request.POST.get("location"),
            status=request.POST.get("status"),
            image=request.FILES.get("image")
        )
        return JsonResponse({"success": True})


def facility_update(request):
    if request.method == "POST":

        facility = get_object_or_404(SportsFacility,facility_id=request.POST.get("facility_id"))

        facility_name = request.POST.get("facility_name")

        if SportsFacility.objects.filter(
                facility_name__iexact=facility_name
            ).exclude(
                facility_id=facility.facility_id
            ).exists():

            messages.error(request, "Facility already created")
            return redirect("facility")

        facility.facility_name = facility_name
        facility.sport_id = request.POST.get("sport")
        facility.facility_type = request.POST.get("facility_type") or facility.facility_type
        facility.status = request.POST.get("status")
        facility.capacity = request.POST.get("capacity")
        facility.location = request.POST.get("location")

        if request.FILES.get("image"):
            facility.image = request.FILES["image"]

        facility.save()

        messages.success(request, "Facility updated successfully")
        return redirect("facility")
    
from django.shortcuts import redirect, get_object_or_404

def facility_status(request):

    if request.method == "POST":

        facility = get_object_or_404(
            SportsFacility,
            facility_id=request.POST.get("facility_id")
        )

        facility.status = request.POST.get("status")
        facility.save()
        return JsonResponse({
            "success": True,
            "status": facility.status
        })

    return JsonResponse({"success": False})


#################################  facility view end #############################################################

#################################  club view start #############################################################
@login_required
def club(request):

    clubs = SportClub.objects.all()
    
    context = {
        "clubs": clubs,
        "sports":Sport.objects.filter(is_active=True),
        "total_clubs": clubs.count(),
        "active_clubs": clubs.filter(is_active=True).count(),
        "total_teams": SportTeamModel.objects.filter(club__isnull=False, status=True).count(),
        "total_coaches": Coach.objects.filter(head_coached_teams__club__isnull=False).distinct().count(),

    }

    return render(
        request,
        "reports/club.html",
        context
    )

def club_save(request):
    if request.method == "POST":

        club_name = request.POST.get("club_name", "").strip()
        sport_id = request.POST.get("sport")
        status = request.POST.get("status")

        if not club_name:
            return JsonResponse({
                "success": False,
                "message": "Club name is required."
            })
        if not sport_id:
            return JsonResponse({
                "success": False,
                "message": "Please select a sport."
            })

        if status not in ["ACTIVE", "INACTIVE"]:
            return JsonResponse({
                "success": False,
                "message": "Please select a status."
            })

        sport = Sport.objects.get(id=sport_id)

        if SportClub.objects.filter(club_name__iexact=club_name).exists():
            return JsonResponse({
                "success": False,
                "message": "Club name already exists."
            })

        SportClub.objects.create(
            club_name=club_name,
            sport=sport,
            description=request.POST.get("description"),
            is_active=request.POST.get("status") == "ACTIVE",
            logo=request.FILES.get("logo"),
            image=request.FILES.get("image")
        )

        return JsonResponse({
            "success": True,
            "message": "Club created successfully."
        })

    return JsonResponse({
        "success": False,
        "message": "Invalid request."
    })


def club_view(request, pk):
    club = get_object_or_404(SportClub, pk=pk)

    teams = SportTeamModel.objects.filter(
        club=club
    ).select_related(
        "head_coach",
        "home_facility"
    )

    coaches = Coach.objects.filter(head_coached_teams__club=club).distinct()

    facilities = SportsFacility.objects.filter(
    home_teams__club=club).distinct()

    context = {
        "club": club,
        "teams": teams,
        "coaches": coaches,
        "sports": Sport.objects.all(),
        "facility":facilities,
    }

    return render(request, "reports/club_view.html", context)


def club_update(request, id):
    club = get_object_or_404(SportClub, id=id)
    

    if request.method == "POST":
        club_name = request.POST.get("club_name").strip()
        sport_id = request.POST.get("sport")
        status = request.POST.get("status")

        if not club_name:
            return JsonResponse({
                "success": False,
                "message": "Club name is required."
            })

        if not sport_id:
            return JsonResponse({
                "success": False,
                "message": "Please select a sport."
            })

        if status not in ["ACTIVE", "INACTIVE"]:
            return JsonResponse({
                "success": False,
                "message": "Please select a status."
            })

        if SportClub.objects.filter(club_name__iexact=club_name).exclude(id=club.id).exists():
            return JsonResponse({
                    "success": False,
                     "message": "Club name already exists."
            })

        club.club_name = club_name
        club.description = request.POST.get("description")

        sport_id = request.POST.get("sport")
        if sport_id:
            club.sport = Sport.objects.get(id=sport_id)

        status = request.POST.get("status")
        club.is_active = (status == "ACTIVE")

        if request.FILES.get("logo"):
            club.logo = request.FILES["logo"]

        if request.FILES.get("image"):
            club.image = request.FILES["image"]

        club.save()

        return JsonResponse({
            "success": True,
            "message": "Club updated successfully."
        })

    return JsonResponse({
        "success": False,
        "message": "Invalid Request"
    })

#################################  club view end #############################################################

#################################  profile_setting view start #############################################################

@login_required
@require_http_methods(["GET", "POST"])
def profile_setting(request):

    user = request.user
    if not (request.user.is_admin or request.user.is_super_admin):
        return redirect("dashboard")

    if request.method == "POST":

        try:

            user.first_name = request.POST.get("first_name", "").strip()
            user.middle_name = request.POST.get("middle_name", "").strip()
            user.last_name = request.POST.get("last_name", "").strip()
            user.username = request.POST.get("username", "").strip()
            user.email = request.POST.get("email", "").strip()
            user.mobile_number = request.POST.get("mobile_number", "").strip()
            user.gender = request.POST.get("gender") or None
         

            dob = request.POST.get("date_of_birth")
            user.date_of_birth = dob if dob else None

            if request.FILES.get("profile_photo"):
                user.profile_photo = request.FILES["profile_photo"]

            # ---------- Password Change ----------

            current_password = request.POST.get("current_password")
            new_password = request.POST.get("new_password")
            confirm_password = request.POST.get("confirm_password")

            if new_password or confirm_password:
                if not current_password:
                    return JsonResponse({
                        "success": False,
                        "message": "Current password is required."
                    }, status=400)

                if not user.check_password(current_password):
                    return JsonResponse({
                        "success": False,
                        "message": "Current password is incorrect."
                    }, status=400)

                if new_password != confirm_password:
                    return JsonResponse({
                        "success": False,
                        "message": "Passwords do not match."
                    }, status=400)

                if new_password != confirm_password:
                    return JsonResponse({
                        "success": False,
                        "message": "Passwords do not match."
                    })

                user.set_password(new_password)

            user.save()

            if new_password:
                update_session_auth_hash(request, user)

            return JsonResponse({
                "success": True,
                "message": "Profile updated successfully."
            })

        except Exception as e:

            return JsonResponse({
                "success": False,
                "message": str(e)
            })

    return render(request, "profile_setting.html")
    

#################################  profile_setting view end #############################################################

#################################  Coaches view start #############################################################

@login_required
def coach_management(request):
    SPORT_ICONS = {
        
    "football": "ti ti-ball-football",
    "basketball": "ti ti-ball-basketball",
    "cricket": "ti ti-cricket",
    "volleyball": "ti ti-ball-volleyball",
    "tennis": "ti ti-ball-tennis",
    "Badminton": "ti ti-racket",
    "table ennis": "ti ti-ping-pong",
    "Swimming": "ti ti-swimming",
    "Rugby": "ti ti-ball-rugby",
}

    coach_qs = (Coach.objects.all().order_by("-created_at"))
    covered_sports = (Sport.objects.filter(teams__head_coach__isnull=False).distinct().count())
    covered_sports = set()
    coaches = []
    departments = set()

    for coach in coach_qs:
        
        sports = Sport.objects.filter(teams__head_coach=coach).distinct()

        sport_list = list(sports.values_list("sport_name", flat=True))

        sport_names = ", ".join(sport_list)

        first_sport = sport_list[0] if sport_list else "Not Assigned"
        more_sports = max(len(sport_list) - 1, 0)

        

        for sport in sports:
            covered_sports.add(sport.sport_name)

        if not sport_names:
            sport_names = "Not Assigned"

        sport_lower = sport_names.lower()

        if "football" in sport_lower:
            sport_class = "football"
        elif "basketball" in sport_lower:
            sport_class = "basketball"
        elif "cricket" in sport_lower:
            sport_class = "cricket"
        elif "badminton" in sport_lower:
            sport_class = "badminton"
        elif "tennis" in sport_lower and "table tennis" not in sport_lower:
            sport_class = "tennis"
        elif "table tennis" in sport_lower:
            sport_class = "tabletennis"
        elif "volleyball" in sport_lower:
            sport_class = "volleyball"
        elif "rugby" in sport_lower:
            sport_class = "rugby"
        elif "swimming" in sport_lower:
            sport_class = "swimming"
        else:
            sport_class = "other"

        staff = (
            StaffProfile.objects
            .select_related("user")
            .prefetch_related("department_assignments")
            .filter(employee_id=coach.staff_id)
            .first()
        )

        # Skip invalid coach records that do not have
        # a matching StaffProfile
        if not staff:
            continue

        dept_assignment = (
            staff.department_assignments
            .filter(primary_assignment=True)
            .first()
            or staff.department_assignments.first()
        )

        department_name = (
            getattr(dept_assignment, "department_name", None)
            or (
                f"Dept {dept_assignment.department_id}"
                if dept_assignment else "—"
            )
        )

        departments.add(department_name)

        full_name = staff.user.full_name or ""

        initials = "".join(
            word[0]
            for word in full_name.split()[:2]
            if word
        ).upper()
        experience_years = (date.today().year-coach.hire_date.year-(
        (date.today().month, date.today().day)< (coach.hire_date.month, coach.hire_date.day)))

        

        coaches.append({
            "coach_id": coach.coach_id,

            "staff_id": coach.staff_id,
            "full_name": full_name,
            "initials": initials,
            "photo_url": (staff.user.profile_photo.url
                if staff.user.profile_photo
                else None
            ),
            "email": staff.work_email,
            "phone": staff.office_phone,
            "department": department_name,
            "sport": sport_names,
            "first_sport": first_sport,
            "more_sports": more_sports,
            "sport_class": sport_class,
         
            "employment_type": staff.get_employment_type_display(),
            "employment_status": staff.employment_status,
            "role": coach.get_role_display(),
            "hire_date": coach.hire_date,
            "certifications": coach.certifications,
            "gender": staff.user.gender,
            "experience_years": experience_years,
            
            "account_status": staff.user.account_status,
      

            
        })
    assigned_staff = Coach.objects.values_list("staff_id",flat=True)

    available_staff = (
        StaffProfile.objects
        .select_related("user")
        .exclude(employee_id__in=assigned_staff)
    )

    context = {

        "hero_photo_url": static("images/coach2.jpg"),
        "coaches": coaches,
        "total_coaches": len(coaches),
        "active_coaches": sum(
            1 for c in coaches
            if c["account_status"] == "ACTIVE"
        ),
     
        "certified_coaches": sum(
            1 for c in coaches
            if c["certifications"]
        ),
       "sports_covered": len(covered_sports),
        "full_time_coaches": sum(
            1 for c in coaches
            if c["employment_type"] == "Full-Time"
        ),
        "department_count": len(departments),
         "available_staff": available_staff,
         "roles": Coach.ROLE_CHOICES,
    }

    return render(
        request,
        "reports/coach.html",
        context,
    )

@login_required
def assign_coach(request):

    assigned_staff = Coach.objects.values_list(
        "staff_id",
        flat=True
    )
    available_staff = StaffProfile.objects.select_related("user").exclude(employee_id__in=assigned_staff)

    if request.method == "POST":

        staff_emp_id = request.POST.get("staff")
        role = request.POST.get("role")
        hire_date = request.POST.get("hire_date")
        certifications = request.POST.get("certifications")

        if Coach.objects.filter(staff_id=staff_emp_id).exists():
            messages.error(request, "This staff is already assigned as a coach.")
            return redirect("assign_coach")
        staff = StaffProfile.objects.get(employee_id=staff_emp_id)
        Coach.objects.create(
            staff_id=staff.employee_id,
            role=role,
            hire_date=hire_date,
            certifications=certifications,
        )
    # Mark as coach
        staff.is_coach = True
        staff.save(update_fields=["is_coach"])

        messages.success(request, "Coach assigned successfully.")
        return redirect("coach_management")
    
    context = {
            "available_staff": available_staff,
            "roles": Coach.ROLE_CHOICES,
        } 

    return render(request, "reports/assign_coach.html", context)

@login_required
def coach_view(request, coach_id):
    """
    Coach profile / view page.
    Mirrors the data-building logic used in coach_management(), but scoped
    to a single coach, plus assigned teams and a parsed certification list.
    """
 
    coach_obj = get_object_or_404(Coach, coach_id=coach_id)
 
    staff = (
        StaffProfile.objects
        .select_related("user")
        .prefetch_related("department_assignments")
        .filter(employee_id=coach_obj.staff_id)
        .first()
    )
 
    dept_assignment = (
        staff.department_assignments.filter(primary_assignment=True).first()
        or staff.department_assignments.first()
    )
 
    department_name = (
        getattr(dept_assignment, "department_name", None)
        or (f"Dept {dept_assignment.department_id}" if dept_assignment else "—")
    )
 
    full_name = staff.user.full_name or ""
 
    initials = "".join(
        word[0] for word in full_name.split()[:2] if word
    ).upper()
 
    experience_years = (
        date.today().year
        - coach_obj.hire_date.year
        - ((date.today().month, date.today().day) < (coach_obj.hire_date.month, coach_obj.hire_date.day))
    )
 
    assigned_teams = (
        SportTeamModel.objects
        .select_related("sport_type")
        .filter(head_coach=coach_obj)
        .order_by("team_name")
    )
 
    sports = Sport.objects.filter(teams__head_coach=coach_obj).distinct()
    sport_names = ", ".join(sports.values_list("sport_name", flat=True)) or "Not Assigned"
 
    certification_list = [
        line.strip()
        for line in (coach_obj.certifications or "").splitlines()
        if line.strip()
    ]
 
    coach = {
        "coach_id": coach_obj.coach_id,
        "staff_id": coach_obj.staff_id,
        "full_name": full_name,
        "initials": initials,
        "photo_url": staff.user.profile_photo.url if staff.user.profile_photo else None,
        "email": staff.work_email,
        "phone": staff.office_phone,
        "department": department_name,
        "sport": sport_names,
        "employment_type": staff.get_employment_type_display(),
        "employment_status": staff.employment_status,
        "role": coach_obj.get_role_display(),
        "hire_date": coach_obj.hire_date,
        "certifications": coach_obj.certifications,
        "gender": staff.user.gender,
        "experience_years": experience_years,
        "account_status": staff.user.account_status,
        # "is_active": coach_obj.is_active,
    }
 
    context = {
        "coach": coach,
        "assigned_teams": assigned_teams,
        "certification_list": certification_list,
    }
 
    return render(request, "reports/coach_view.html", context)
 

@login_required
def edit_coach(request, coach_id):
    """
    Edit an existing coach's role, hire date, status and certifications.
    Staff assignment itself is not editable here (remove + re-assign instead),
    matching the read-only "Staff" field shown on the form.
    """
 
    coach_obj = get_object_or_404(Coach, coach_id=coach_id)
    
    staff = (
        StaffProfile.objects
        .select_related("user")
        .filter(employee_id=coach_obj.staff_id)
        .first()
    )
 
    if request.method == "POST":
        role = request.POST.get("role")
        hire_date = request.POST.get("hire_date")
        certifications = request.POST.get("certifications", "")
        account_status = request.POST.get("account_status")
        errors = {}
        if not role:
            errors["role"] = "Role is required."
        if not hire_date:
            errors["hire_date"] = "Hire date is required."
 
        if errors:
            for field, msg in errors.items():
                messages.error(request, msg)
        else:
            coach_obj.role = role
            coach_obj.hire_date = hire_date
            coach_obj.certifications = certifications
            coach_obj.save()

            staff.user.account_status = account_status
            staff.user.save(update_fields=["account_status"])

            coach_obj.refresh_from_db()
 
            messages.success(request, "Coach details updated successfully.")
            return redirect("coach_view", coach_id=coach_obj.coach_id)
 
    full_name = staff.user.full_name if staff else ""
    initials = "".join(word[0] for word in full_name.split()[:2] if word).upper()
 
    coach = {
        "coach_id": coach_obj.coach_id,
        "staff_id": coach_obj.staff_id,
        "full_name": full_name,
        "initials": initials,
        "photo_url": staff.user.profile_photo.url if staff and staff.user.profile_photo else None,
        "email": staff.work_email if staff else "",
        "role_value": coach_obj.role,
        "hire_date": coach_obj.hire_date,
        "certifications": coach_obj.certifications,
        "account_status": staff.user.account_status,
    }
    context = {
        "coach": coach,
        "roles": Coach.ROLE_CHOICES,
    }
 
    return render(request, "reports/coach_edit.html", context)

# ################################  coaches view end #############################################################
 

# # ################################  patient profile view start#############################################################

from Medical.models import PatientProfile, MedicalVisit, Appointment,  MedicalDepartment
from django.db.models import Value
from django.db.models.functions import Coalesce


@login_required
def patient_profile(request):
    search_query = request.GET.get("search", "").strip()
    selected_type = request.GET.get("patient_type", "")
    selected_blood_group = request.GET.get("blood_group", "")
    selected_sort = request.GET.get("sort", "recent")

    # patients = PatientProfile.objects.select_related( "student", "staff", "faculty")
    patients = PatientProfile.objects.select_related("student__user","staff__user","faculty__user","admin",)

    # Search
    if search_query:
        patients = patients.filter(
            Q(patient_number__icontains=search_query)

            # Student
            | Q(student__user__first_name__icontains=search_query)
            | Q(student__user__last_name__icontains=search_query)
            | Q(student__student_number__icontains=search_query)

            # Faculty
            | Q(faculty__user__first_name__icontains=search_query)
            | Q(faculty__user__last_name__icontains=search_query)
            | Q(faculty__employee_id__icontains=search_query)

            # Staff
            | Q(staff__user__first_name__icontains=search_query)
            | Q(staff__user__last_name__icontains=search_query)
            | Q(staff__employee_id__icontains=search_query)

            # Admin
            | Q(admin__first_name__icontains=search_query)
            | Q(admin__last_name__icontains=search_query)
            | Q(admin__email__icontains=search_query)

            # Visitor
            | Q(visitor_name__icontains=search_query)
            | Q(visitor_phone__icontains=search_query)
            | Q(visitor_email__icontains=search_query)
        )

    # Patient Type Filter
    if selected_type:
        patients = patients.filter(patient_type=selected_type)

    # Blood Group Filter
    if selected_blood_group:
        patients = patients.filter(blood_group=selected_blood_group)

    # Sorting
    if selected_sort == "oldest":
        patients = patients.order_by("created_at")
    else:
        patients = patients.order_by("-created_at")

    # Pagination
    paginator = Paginator(patients, 10)   
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Statistics
    stats = {
        "total": PatientProfile.objects.count(),
        "students": PatientProfile.objects.filter(patient_type="STUDENT").count(),
        "faculty": PatientProfile.objects.filter(patient_type="FACULTY").count(),
        "staff": PatientProfile.objects.filter(patient_type="STAFF").count(),
        "admins": PatientProfile.objects.filter(patient_type="ADMIN").count(),
       "visitors": PatientProfile.objects.filter(patient_type="VISITOR").count(),
    }

    context = {
        "patients": page_obj,
        "page_obj": page_obj,
        "stats": stats,
        "search_query": search_query,
        "selected_type": selected_type,
        "selected_blood_group": selected_blood_group,
        "selected_sort": selected_sort,
        "patient_types": PatientProfile.PATIENT_TYPES,
        "blood_groups": PatientProfile.BLOOD_GROUPS,
    }

    return render(request, "swetha/patient_profile.html", context)

@login_required
def patient_profile_list(request):
    search_query = request.GET.get("search", "").strip()
    selected_type = request.GET.get("patient_type", "")
    selected_blood_group = request.GET.get("blood_group", "")
    selected_sort = request.GET.get("sort", "recent")


    # patients = PatientProfile.objects.select_related( "student", "staff", "faculty")
    patients = PatientProfile.objects.select_related(
    "student__user",
    "staff__user",
    "faculty__user",
    "admin",
)
    patients = patients.annotate(
    first_name=Coalesce(
        "student__user__first_name",
        "faculty__user__first_name",
        "staff__user__first_name",
        "admin__first_name",
        "visitor_name",
        Value("")
    )
)

    if search_query:
        patients = patients.filter(
            Q(patient_number__icontains=search_query) |

            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__student_number__icontains=search_query) |

            Q(faculty__user__first_name__icontains=search_query) |
            Q(faculty__user__last_name__icontains=search_query) |
            Q(faculty__employee_id__icontains=search_query) |

            Q(staff__user__first_name__icontains=search_query) |
            Q(staff__user__last_name__icontains=search_query) |
            Q(staff__employee_id__icontains=search_query)

                # Admin
            | Q(admin__first_name__icontains=search_query)
            | Q(admin__last_name__icontains=search_query)
            | Q(admin__email__icontains=search_query)

            # Visitor
            | Q(visitor_name__icontains=search_query)
            | Q(visitor_phone__icontains=search_query)
            | Q(visitor_email__icontains=search_query)
        )

    if selected_type:
        patients = patients.filter(patient_type=selected_type)

    if selected_blood_group:
        patients = patients.filter(blood_group=selected_blood_group)

    if selected_sort == "oldest":
        patients = patients.order_by("created_at")
    elif selected_sort == "name_az":
        patients = patients.order_by("first_name")
    elif selected_sort == "name_za":
        patients = patients.order_by("-first_name")
    else:
        patients = patients.order_by("-created_at")
    
    paginator = Paginator(patients, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    html = render_to_string(
    "swetha/patient_table.html",
    {
        "patients": page_obj,
        "page_obj": page_obj,
    },
    request=request,
)

    return JsonResponse({
        "html": html
    })


@login_required
def patient_profile_view(request, patient_id):
    patient = get_object_or_404(
        PatientProfile.objects.select_related(
            "student__user",
            "staff__user",
            "faculty__user", "admin",
        ),
        pk=patient_id,
    )


    # ---------------------------- Patient Details -----------------------------#

    patient_name = ""
    patient_phone = ""
    patient_id_number = ""
    department = ""


    if patient.patient_type == "STUDENT" and patient.student:
        student = patient.student
        user = patient.student.user

        patient_name = user.get_full_name()
        patient_phone =  user.phone if hasattr(user, "phone") else ""
        patient_id_number = patient.student.student_number

        if hasattr(patient.student, "department"):
            department = patient.student.department
        # department = getattr(student, "department", "")
       

    elif patient.patient_type == "FACULTY" and patient.faculty:
        faculty = patient.faculty
        user = patient.faculty.user

        patient_name = user.get_full_name()
        patient_phone = patient.faculty.phone
        patient_id_number = patient.faculty.employee_id

        if patient.faculty.department:
            department = patient.faculty.department.name

        # department = getattr(faculty, "department", "")
       
    elif patient.patient_type == "STAFF" and patient.staff:
        staff = patient.staff
        user = patient.staff.user

        patient_name = user.get_full_name()
        patient_phone = patient.staff.office_phone
        patient_id_number = patient.staff.employee_id
        # department = getattr(staff, "department", "")

    elif patient.patient_type == "ADMIN" and patient.admin:
        admin = patient.admin

        patient_name = admin.get_full_name()
        patient_phone = admin.phone if hasattr(admin, "phone") else ""
        patient_id_number = admin.university_id if hasattr(admin, "university_id") else ""

        if hasattr(admin, "department") and admin.department:
            department = admin.department.name
    
    elif patient.patient_type == "VISITOR":

            patient_name = patient.visitor_name
            patient_phone = patient.visitor_phone
            patient_id_number = "Visitor"

            # department = "-"

    # ----------------------------
    # Medical Visits
    # ----------------------------
    visits = (
        MedicalVisit.objects
        .filter(patient=patient)
        .select_related("attending_staff__user")
        .order_by("-visit_date")
    )

    total_visits = visits.count()

    last_visit = visits.first()
    first_visit = visits.order_by("visit_date").first()

    last_visit_date = last_visit.visit_date if last_visit else None
    first_visit_date = first_visit.visit_date if first_visit else None

    paginator = Paginator(visits, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "patient": patient,

        # Patient Information
        "patient_name": patient_name,
        "patient_phone": patient_phone,
        "patient_id_number": patient_id_number,
        "department": department,
  

        # Summary
        "total_visits": total_visits,
        "last_visit_date": last_visit_date,
        "first_visit_date": first_visit_date,

        # Visit History
        "page_obj": page_obj,
    }

    return render(
        request,
        "swetha/patient_profile_view.html",
        context,
    )



# # ################################  patient profile view end #############################################################

# # ################################  appoinment view start #############################################################


from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone


@login_required
def appointment(request):

    today = timezone.localdate()

    appointments_qs = (
        Appointment.objects
        .select_related(
            "patient",
            "athlete",
            "user",
            "medical_staff",
            "medical_staff__department",
            "hospital",
        )
        .order_by(
            "-appointment_date",
            "appointment_time",
        )
    )

    search = request.GET.get(
        "search",
        ""
    ).strip()

    department = request.GET.get(
        "department",
        ""
    ).strip()

    status = request.GET.get(
        "status",
        ""
    ).strip()

    priority = request.GET.get(
        "priority",
        ""
    ).strip()


    if search:

        appointments_qs = appointments_qs.filter(
            Q(
                appointment_number__icontains=search
            )
            |
            Q(
                service__icontains=search
            )
            |
            Q(
                reason__icontains=search
            )
            |
            Q(
                patient__patient_number__icontains=search
            )
            |
            Q(
                user__first_name__icontains=search
            )
            |
            Q(
                user__last_name__icontains=search
            )
        )

    if department:

        appointments_qs = appointments_qs.filter(
            medical_staff__department_id=department
        )

    if status:

        appointments_qs = appointments_qs.filter(
            status=status
        )

    if priority:

        appointments_qs = appointments_qs.filter(
            priority=priority
        )

    today_count = Appointment.objects.filter(
        appointment_date=today
    ).count()


    pending_count = Appointment.objects.filter(
        status="PENDING"
    ).count()


    checked_count = Appointment.objects.filter(
        status="CHECKED_IN"
    ).count()


    completed_count = Appointment.objects.filter(
        status="COMPLETED"
    ).count()


    cancelled_count = Appointment.objects.filter(
        status="CANCELLED"
    ).count()

    paginator = Paginator(
        appointments_qs,
        10
    )

    page_number = request.GET.get(
        "page",
        1
    )

    appointments = paginator.get_page(
        page_number
    )
    context = {

        "appointments": appointments,

        "today": today,

        "today_count": today_count,
        "pending_count": pending_count,
        "checked_count": checked_count,
        "completed_count": completed_count,
        "cancelled_count": cancelled_count,

        "departments": MedicalDepartment.objects.all(),

        "search": search,
        "department": department,
        "status": status,
        "priority": priority,
    }

    return render(
        request,
        "swetha/appointment.html",
        context
    )



# # ################################  appoinment view end #############################################################

# # ################################  healthcamp view satrt #############################################################

from Medical.models import HealthCamp, MedicalDepartment, HealthCampRegistry

def healthcamp_management(request):

    student_count = User.objects.filter(role__role_name__iexact="Student").count()
    faculty_count = User.objects.filter(role__role_name__iexact="Faculty").count()
    staff_count = User.objects.filter(role__role_name__iexact="Staff").count()
    admin_count = User.objects.filter(role__role_name__iexact="Admin").count()

    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "")
    camp_type = request.GET.get("camp_type", "")
    department = request.GET.get("department", "")

    filters = Q()

    if search:
        filters &= (
            Q(camp_name__icontains=search) |
            Q(camp_code__icontains=search) |
            Q(venue__icontains=search)
        )

    if status:
        filters &= Q(status=status)

    if camp_type:
        filters &= Q(camp_type=camp_type)

    if department:
        filters &= Q(department_id=department)

    camps = (HealthCamp.objects
        .select_related("department", "organizer").filter(filters)
        .order_by("-start_date")
    )

    paginator = Paginator(camps, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    now = timezone.localtime()
    today_camps = []
    upcoming_camps = []

    all_camps = (
        HealthCamp.objects
        .select_related("department", "organizer").filter(filters)
        .order_by("start_date", "start_time")
    )

    for camp in all_camps:

        start_dt = timezone.make_aware(
            datetime.combine(camp.start_date, camp.start_time)
        )

        end_dt = timezone.make_aware(
            datetime.combine(camp.end_date, camp.end_time)
        )

        # LIVE CAMP
        if start_dt <= now <= end_dt:
            today_camps.append(camp)

        # UPCOMING CAMP
        elif now < start_dt:
            upcoming_camps.append(camp)

    # Show only first 5 upcoming camps
    upcoming_camps = upcoming_camps[:5]

    # past 5year
    current_year = timezone.now().year

    camp_data = (
        HealthCamp.objects
        .filter(start_date__year__gte=current_year - 4)
        .annotate(year=ExtractYear("start_date"))
        .values("year")
        .annotate(total=Count("id"))
    )

    camp_dict = {
        item["year"]: item["total"]
        for item in camp_data
    }

    year_labels = []
    year_values = []

    for year in range(current_year - 4, current_year + 1):
        year_labels.append(str(year))
        year_values.append(camp_dict.get(year, 0))

    # yearly
#     yearly_camps = (
#     HealthCamp.objects
#     .annotate(year=ExtractYear("start_date"))
#     .values("year")
#     .annotate(total=Count("id"))
#     .order_by("year")
# )   
#     year_labels = [
#     str(item["year"])
#     for item in yearly_camps
# ]

#     year_values = [
#         item["total"]
#         for item in yearly_camps
#     ]

    stats = {

        "total": HealthCamp.objects.count(),

        "open": HealthCamp.objects.filter(
            status="OPEN"
        ).count(),

        "ongoing": HealthCamp.objects.filter(
            status="ONGOING"
        ).count(),

        "completed": HealthCamp.objects.filter(
            status="COMPLETED"
        ).count(),

        "participants": sum(
            HealthCamp.objects.values_list(
                "registered_participants",
                flat=True
            )
        )
     
    }
    participant_stats = (
        HealthCampRegistry.objects
        .values("participant_type")
        .annotate(total=Count("id"))
    )

    participant_dict = {
        item["participant_type"]: item["total"]
        for item in participant_stats
    }

    participant_labels = [
        "Students",
        "Athletes",
        "Faculty",
        "Staff",
        "Visitors"
    ]

    participant_values = [
        participant_dict.get("STUDENT", 0),
        participant_dict.get("ATHLETE", 0),
        participant_dict.get("FACULTY", 0),
        participant_dict.get("STAFF", 0),
        participant_dict.get("VISITOR", 0),
    ]
    status_labels = [
    "Planned",
    "Open",
    "Ongoing",
    "Completed",
    "Cancelled",
    ]

    status_values = [
        camps.filter(status="PLANNED").count(),
        camps.filter(status="OPEN").count(),
        camps.filter(status="ONGOING").count(),
        camps.filter(status="COMPLETED").count(),
        camps.filter(status="CANCELLED").count(),
    ]

    context = {

        "page_obj": page_obj,

        "today_camps": today_camps,

        "upcoming_camps": upcoming_camps,

        "stats": stats,

        "status_choices": HealthCamp.STATUS_CHOICES,

        "camp_types": HealthCamp.CAMP_TYPES,

        "departments": MedicalDepartment.objects.all(),

        "search": search,

        "status": status,

        "camp_type": camp_type,

        "department": department,
        "student_count": student_count,
        "faculty_count": faculty_count,
        "staff_count": staff_count,
        "admin_count": admin_count,
        
        "year_labels": json.dumps(year_labels),
        "year_values": json.dumps(year_values),

        "participant_labels": json.dumps(participant_labels),
        "participant_values": json.dumps(participant_values),

        "status_labels": json.dumps(status_labels),
        "status_values": json.dumps(status_values),
        

    }

    return render(
    request,
    "swetha/healthcamp.html",
    context,
)


##################################  healthcamp view end #############################################################

########################################  medical history view start #####################################################
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import date, time, timedelta

from Medical.models import (
    Appointment,
    PatientRegistration,
    PatientProfile,
)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta, date, time

from Medical.models import (
    Appointment,
    PatientRegistration,
    PatientProfile,
)


@login_required
def admin_medical_history(request):

    user = request.user

    # =====================================================
    # 1. ONLY LOGGED-IN ADMIN'S APPOINTMENTS
    # =====================================================

    appointment_qs = (
        Appointment.objects
        .filter(user=user)
        .select_related(
            "patient",
            "medical_staff",
            "medical_staff__user",
            "hospital",
        )
        .order_by(
            "-appointment_date",
            "-appointment_time",
        )
    )

    # =====================================================
    # 2. FILTERS
    # =====================================================

    search_query = request.GET.get(
        "search",
        ""
    ).strip()

    current_status = request.GET.get(
        "status",
        ""
    ).strip().upper()

    if current_status and current_status != "ALL STATUS":

        appointment_qs = appointment_qs.filter(
            status=current_status
        )

    if search_query:

        appointment_qs = appointment_qs.filter(
            Q(
                appointment_number__icontains=
                search_query
            )
            |
            Q(
                reason__icontains=
                search_query
            )
            |
            Q(
                service__icontains=
                search_query
            )
            |
            Q(
                medical_staff__user__first_name__icontains=
                search_query
            )
            |
            Q(
                medical_staff__user__last_name__icontains=
                search_query
            )
        )

    # =====================================================
    # 3. REGISTRATIONS
    #
    # Only registrations belonging to this admin's
    # appointments.
    # =====================================================

    registration_qs = (
        PatientRegistration.objects
        .filter(
            appointment__user=user
        )
        .select_related(
            "patient",
            "appointment",
            "appointment__medical_staff",
            "appointment__medical_staff__user",
            "medical_visit",
            "medical_visit__attending_staff",
            "medical_visit__attending_staff__user",
            "medical_visit__department",
            "shift_assignment",
            "shift_assignment__medical_staff",
            "shift_assignment__medical_staff__user",
        )
    )

    registration_map = {
        registration.appointment_id: registration
        for registration in registration_qs
    }

    # =====================================================
    # 4. BUILD HISTORY
    # =====================================================

    history = []

    for appointment in appointment_qs:

        registration = registration_map.get(
            appointment.id
        )

        medical_visit = (
            registration.medical_visit
            if registration
            else None
        )

        # -------------------------------------------------
        # DOCTOR
        # -------------------------------------------------

        doctor = appointment.medical_staff

        if (
            medical_visit
            and medical_visit.attending_staff
        ):
            doctor = medical_visit.attending_staff

        # -------------------------------------------------
        # STATUS
        # -------------------------------------------------

        if (
            medical_visit
            and medical_visit.visit_status == "COMPLETED"
        ):
            display_status = "COMPLETED"

        elif registration:

            if registration.status in [
                "COMPLETED",
                "IN_PROGRESS",
                "CANCELLED",
            ]:
                display_status = registration.status
            else:
                display_status = appointment.status

        else:
            display_status = appointment.status

        # -------------------------------------------------
        # CANCEL WINDOW
        # -------------------------------------------------

        can_cancel = False
        remaining_time = None

        if appointment.status == "PENDING":

            expiry_time = (
                appointment.created_at
                + timedelta(minutes=10)
            )

            now = timezone.now()

            if now < expiry_time:

                can_cancel = True

                seconds = int(
                    (
                        expiry_time - now
                    ).total_seconds()
                )

                minutes = seconds // 60
                seconds = seconds % 60

                remaining_time = (
                    f"{minutes:02d}:{seconds:02d}"
                )

        # -------------------------------------------------
        # HISTORY OBJECT
        # -------------------------------------------------

        history.append({

            "source": "APPOINTMENT",

            "appointment": appointment,

            "registration": registration,

            "medical_visit": medical_visit,

            "display_number": (
                appointment.appointment_number
                or "—"
            ),

            "display_type": "Appointment",

            "display_status": display_status,

            "display_date": (
                medical_visit.visit_date
                if medical_visit
                else appointment.appointment_date
            ),

            "display_time": (
                medical_visit.visit_time
                if medical_visit
                else appointment.appointment_time
            ),

            "display_reason": (
                appointment.reason
                or (
                    registration.chief_complaint
                    if registration
                    else ""
                )
                or "—"
            ),

            "display_doctor": doctor,

            "display_visit_type": (
                medical_visit.get_visit_type_display()
                if medical_visit
                else ""
            ),

            "display_diagnosis": (
                medical_visit.diagnosis
                if medical_visit
                else ""
            ),

            "display_treatment": (
                medical_visit.treatment
                if medical_visit
                else ""
            ),

            "display_medications": (
                medical_visit.medications
                if medical_visit
                else ""
            ),

            "can_cancel": can_cancel,

            "remaining_time": remaining_time,
        })

    # =====================================================
    # 5. SORT
    # =====================================================

    history.sort(
        key=lambda item: (
            item["display_date"] or date.min,
            item["display_time"] or time.min,
        ),
        reverse=True,
    )

    # =====================================================
    # 6. STATUS COUNTS
    # =====================================================

    status_counts = {

        "total": len(history),

        "pending": sum(
            1
            for item in history
            if item["display_status"] == "PENDING"
        ),

        "confirmed": sum(
            1
            for item in history
            if item["display_status"] == "CONFIRMED"
        ),

        "arrived": sum(
            1
            for item in history
            if item["display_status"] == "ARRIVED"
        ),

        "in_progress": sum(
            1
            for item in history
            if item["display_status"] == "IN_PROGRESS"
        ),

        "completed": sum(
            1
            for item in history
            if item["display_status"] == "COMPLETED"
        ),

        "cancelled": sum(
            1
            for item in history
            if item["display_status"] == "CANCELLED"
        ),
    }

    # =====================================================
    # 7. PAGINATION
    # =====================================================

    paginator = Paginator(
        history,
        10
    )

    page_number = request.GET.get(
        "page",
        1
    )

    appointments = paginator.get_page(
        page_number
    )

    # =====================================================
    # 8. CONTEXT
    # =====================================================

    context = {

        "appointments": appointments,

        "status_counts": status_counts,

        "search_query": search_query,

        "current_status": current_status,

        "page_title": "Medical History",
    }

    return render(
        request,
        "swetha/admin_medical_history.html",
        context
    )

@login_required
def admin_cancel_appointment(request, uuid):

    appointment = get_object_or_404(
        Appointment,
        uuid=uuid,
        user=request.user
    )

    # ONLY PENDING
    if appointment.status != "PENDING":

        messages.error(
            request,
            "Appointment cannot be cancelled."
        )

        return redirect(
            "admin_medical_history"
        )

    # 10 MINUTE WINDOW
    expiry_time = (
        appointment.created_at
        + timedelta(minutes=10)
    )

    if timezone.now() > expiry_time:

        messages.error(
            request,
            "Cancellation time has expired."
        )

        return redirect(
            "admin_medical_history"
        )

    # CANCEL
    appointment.status = "CANCELLED"

    appointment.save(
        update_fields=["status"]
    )

    messages.success(
        request,
        "Appointment cancelled successfully."
    )

    return redirect(
        "admin_medical_history"
    )
########################################  medical history view start #####################################################