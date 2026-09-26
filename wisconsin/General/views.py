from multiprocessing import context

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from calendar import month_abbr
from django.utils import timezone

from Admin.models import User, UserSession, UserAuditLog
from Admin.Alan.models import Article
from Events.models import Event
from Admin.Colleges.models import School
from Admin.bela_admin.models import Department, CourseDesignationType
from django.db.models.functions import Lower
from Admin.Colleges.models import AcademicProgram,AreaOfInterest
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import JsonResponse


def academics(request):
    return render(
        request,
        "Academics/academic_home.html",
        context={"active_main_nav": "academics"},
    )


def about(request):
  return render(request, "About/about.html", context={"active_main_nav": "aboutuw"})
    
    


def majors(request):

    programs = (
        AcademicProgram.objects
        .filter(status="ACTIVE")
        .select_related("department", "degree")
        .order_by("program_name")
    )

    selected_program_type = request.GET.get("program_type", "all")
    search = request.GET.get("search", "").strip()
    interest_ids = request.GET.getlist("interest")

    # Program Type
    if selected_program_type == "major":
        programs = programs.exclude(
            degree__degree_name__iexact="Certificate"
        )

    elif selected_program_type == "certificate":
        programs = programs.filter(
            degree__degree_name__iexact="Certificate"
        )

    # Search
    if search:
        programs = programs.filter(
            program_name__icontains=search
        )

    # Area of Interest
    if interest_ids:
        programs = programs.filter(
            areas_of_interest__id__in=interest_ids
        ).distinct()

    # AJAX
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":

        rows = ""

        if programs.exists():
            for program in programs:
                rows += f"""
                <tr>
                    <td style='text-align:left;'>{program.program_name}</td>
                    <td class='type-badge-cell' style='text-align:left;'>
                        <a href='#' class='program-row-link'>
                            {program.degree.degree_name}
                        </a>
                    </td>
                </tr>
                """
        else:
            rows = """
            <tr>
                <td colspan='2'>No Programs Available</td>
            </tr>
            """

        return JsonResponse({"rows": rows})

    interests = AreaOfInterest.objects.filter(
        status="ACTIVE"
    ).order_by("interest_name")

    return render(
        request,
        "Academics/majorcertificates.html",
        {
            "programs": programs,
            "interests": interests,
            "selected_program_type": selected_program_type,
        },
    )


def schools(request):

    schools = (
        School.objects.filter(status="ACTIVE")
        .select_related("university")
        .order_by("school_name")
    )

    context = {
        "schools": schools,
    }

    return render(request, "Academics/schools.html", context)


########################################## Steve code Start #####################################
def admissions(request):
    return render(
        request,
        "admissions/admissions_aid.html",
        context={"active_main_nav": "admissions"},
    )


def research(request):
    return render(
        request, "research/research.html", context={"active_main_nav": "research"}
    )  


########################################## Steve code End    #####################################
# LOGIN VIEW (TOM)

import secrets
def login_view(request):
    if request.user.is_authenticated:
        return redirect_user_by_role(request.user)

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.account_status == "SUSPENDED":
                messages.error(
                    request,
                    "Your account has been suspended. Please contact the help desk.",
                )
                return render(request, "login/login.html")

            if user.account_status == "INACTIVE":
                messages.error(
                    request, "Your account is inactive. Please contact the help desk."
                )
                return render(request, "login/login.html")

            login(request, user)
            
            
            # Generate a new 6-digit PIN for this login session
            issue_pin = str(secrets.randbelow(900000) + 100000)

            # Store the PIN in the current Django session
            request.session["library_issue_pin"] = issue_pin
            
            print("LIBRARY ISSUE PIN:", issue_pin)


            return redirect_user_by_role(user)

        else:
            messages.error(request, "Invalid NetID or Password. Please try again.")
            return render(request, "login/login.html")

    return render(request, "login/login.html")

import re
def redirect_user_by_role(user):
    uuid = user.uuid

    if user.is_hostel_admin:
        return redirect("hostel_dashboard", uuid=uuid)

    if user.is_admin:
        return redirect("admin_dashboard", uuid=uuid)
 
    elif user.is_faculty:
        return redirect("faculty_dashboard", uuid=uuid)
 
    elif user.is_student:
        return redirect("Student:student_dashboard", uuid=uuid)
    
    elif user.is_medical_staff:
            return redirect("medical_dashboard", uuid=uuid)

    elif user.is_staff:

        if user.role:
            role_name = user.role.role_name.strip().lower()

            if re.search(r"(^|[\s_-])(library|librarian)([\s_-]|$)", role_name):
                return redirect("library_dashboard", uuid=uuid)

        return redirect("staff_dashboard", uuid=uuid)

    else:
        return redirect("home_page")


def logout_view(request):
    logout(request)
    return redirect("login")


# ── Dashboards ───────────────────────────────────────────────────────────────


@login_required
def admin_dashboard(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")

    now = timezone.now()
    last_month_cutoff = now - timedelta(days=30)

    def stat_entry(queryset, date_field="created_at"):
        count = queryset.count()
        previous = queryset.filter(**{f"{date_field}__lte": last_month_cutoff}).count()
        if previous == 0:
            delta = 100.0 if count > 0 else 0.0
        else:
            delta = round(((count - previous) / previous) * 100, 1)
        return {
            "count": count,
            "delta": abs(delta),
            "direction": "up" if delta >= 0 else "down",
        }

    stats = {
        "total_users": stat_entry(User.objects.all()),
        "active_users": stat_entry(User.objects.filter(account_status="ACTIVE")),
        "students": stat_entry(User.objects.filter(is_student=True)),
        "faculty": stat_entry(User.objects.filter(is_faculty=True)),
        "administrators": stat_entry(User.objects.filter(is_admin=True)),
        "pending_accounts": stat_entry(User.objects.filter(account_status="PENDING")),
        "active_sessions": stat_entry(
            UserSession.objects.filter(logout_time__isnull=True),
            date_field="login_time",
        ),
    }

    # ---- User growth chart (last 6 months) ----
    months = []
    y, m = now.year, now.month
    for _ in range(6):
        months.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    months.reverse()

    growth_labels, growth_students, growth_faculty, growth_admins = [], [], [], []
    for yr, mo in months:
        growth_labels.append(month_abbr[mo].upper())
        growth_students.append(
            User.objects.filter(
                is_student=True, created_at__year=yr, created_at__month=mo
            ).count()
        )
        growth_faculty.append(
            User.objects.filter(
                is_faculty=True, created_at__year=yr, created_at__month=mo
            ).count()
        )
        growth_admins.append(
            User.objects.filter(
                is_admin=True, created_at__year=yr, created_at__month=mo
            ).count()
        )

    # ---- User distribution donut ----
    students_count = stats["students"]["count"]
    faculty_count = stats["faculty"]["count"]
    admin_count = stats["administrators"]["count"]
    distribution_total = students_count + faculty_count + admin_count

    def pct_of(n):
        return round((n / distribution_total) * 100) if distribution_total else 0

    user_distribution = {
        "students": students_count,
        "students_pct": pct_of(students_count),
        "faculty": faculty_count,
        "faculty_pct": pct_of(faculty_count),
        "administrators": admin_count,
        "administrators_pct": pct_of(admin_count),
        "total": distribution_total,
    }

    # ---- Account status bar chart ----
    account_status_counts = {
        "active": User.objects.filter(account_status="ACTIVE").count(),
        "pending": User.objects.filter(account_status="PENDING").count(),
        "suspended": User.objects.filter(account_status="SUSPENDED").count(),
        "inactive": User.objects.filter(account_status="INACTIVE").count(),
    }

    chart_data = {
        "userGrowth": {
            "labels": growth_labels,
            "students": growth_students,
            "faculty": growth_faculty,
            "administrators": growth_admins,
        },
        "userDistribution": user_distribution,
        "accountStatus": account_status_counts,
    }

    # ---- Recent audit activities ----
    action_color_map = {
        "CREATE": "green",
        "LOGIN": "green",
        "UPDATE": "blue",
        "LOGOUT": "blue",
        "DOWNLOAD": "blue",
        "UPLOAD": "blue",
        "VIEW": "blue",
        "EXPORT": "orange",
        "IMPORT": "orange",
        "PASSWORD_CHANGE": "orange",
        "ROLE_ASSIGN": "purple",
        "ROLE_REMOVE": "purple",
        "DELETE": "red",
    }
    audit_activities = []
    for log in UserAuditLog.objects.select_related("user").order_by("-timestamp")[:3]:
        color = (
            "red"
            if log.status == "FAILED"
            else action_color_map.get(log.action, "blue")
        )
        actor = log.user.full_name if log.user else "System"
        detail = log.module or log.object_type or log.description or ""
        audit_activities.append(
            {
                "time": log.timestamp,
                "text": f"{actor} \u2013 {log.get_action_display()}",
                "detail": detail,
                "color": color,
            }
        )

    # ---- Upcoming events ----
    upcoming_events = (
        Event.objects.filter(start_datetime__gte=now)
        .exclude(event_status__in=["Cancelled", "Completed"])
        .select_related("venue")
        .order_by("start_datetime")[:3]
    )

    # ---- Latest news ----
    articles = list(
        Article.objects.filter(status="published").order_by(
            "-published_at", "-created_at"
        )[:12]
    )
    news_slides = [articles[i : i + 4] for i in range(0, len(articles), 4)]

    context = {
        "user": request.user,
        "stats": stats,
        "chart_data": chart_data,
        "audit_activities": audit_activities,
        "upcoming_events": upcoming_events,
        "news_slides": news_slides,
    }
    return render(request, "main/dashboard.html", context)


@login_required
def faculty_dashboard(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    return render(request, "faculty_dashboard.html", {"user": request.user})


@login_required
def staff_dashboard(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")
    return render(request, "staff_dashboard.html", {"user": request.user})

# Jack Code Start

@login_required
def medical_dashboard(request, uuid):

    if str(request.user.uuid) != str(uuid):
        return redirect("login")

    context = {
        "user": request.user, 
        "active_sb": "medical_dashboard"
    }
    
    return render(request, 'medical_dashboard.html', context)

# Jack Code End


def website(request):
    return render(request, "landing_page.html")


def student_lifestyle(request):
    return render(
        request,
        "studentlifestyle/student_lifestyle.html",
        context={"active_main_nav": "studentlife"},
    )


########################################## Athletics page #####################################


def athletics(request):
    return render(
        request, "athletics_page.html", context={"active_main_nav": "athletics"}
    )


########################################## News page - MrGow #####################################


def news_page(request):

    latest_news = (
        Article.objects.filter(status="published")
        .exclude(category__category_name__in=["Recent visit"])
        .order_by("-created_at")[:6]
    )

    recent_visit = Article.objects.filter(
        status="published", category__category_name="Recent visit"
    ).order_by("-created_at")[:1]

    context = {
        "latest_news": latest_news,
        "recent_visit": recent_visit,
        "active_main_nav": "news",
    }
    return render(request, "news/news_page.html", context)


# CAMPUS NEWS FUNCTION


def campus_news(request):

    news_list = Article.objects.filter(
        status="published", category__category_name="Campus News"
    ).order_by("-published_at")

    paginator = Paginator(news_list, 4)
    page = request.GET.get("page")
    campus_news = paginator.get_page(page)

    context = {"campus_news": campus_news, "active_main_nav": "campus_news"}

    # AJAX REQUEST
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string(
            "news/partials/campus_news_list.html", context, request=request
        )
        return JsonResponse({"success": True, "html": html})
    return render(request, "news/campus_news.html", context)

# SCIENCE AND TECHNOLOGY NEWS


def society_news(request):

    society_news = Article.objects.filter(
        status="published",
        category__category_name="Society & Culture"
    )

    top_society_news = society_news[:3]

    paginator = Paginator(society_news[3:], 4)

    page = request.GET.get("page")
    remaining_society_news = paginator.get_page(page)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string(
            "partials/society_latest_news.html",
            {"remaining_society_news": remaining_society_news},
            request=request,
        )
        return JsonResponse({"html": html})

    return render(request, "news/society_news.html", {
        "top_society_news": top_society_news,
        "remaining_society_news": remaining_society_news,
    })


def state_news(request):

    state_news = Article.objects.filter(
        status="published",
        category__category_name="State & Global"
    )

    top_state_news = state_news[:3]

    paginator = Paginator(state_news[3:], 4)

    page = request.GET.get("page")
    remaining_state_news = paginator.get_page(page)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string(
            "partials/state_latest_news.html",
            {"remaining_state_news": remaining_state_news},
            request=request,
        )
        return JsonResponse({"html": html})

    return render(request, "news/state_news.html", {
        "top_state_news": top_state_news,
        "remaining_state_news": remaining_state_news,
    })


def health_news(request):

    health_news = Article.objects.filter(
        status="published",
        category__category_name="Health & Wellness"
    )

    top_health_news = health_news[:3]

    paginator = Paginator(health_news[3:], 4)

    page = request.GET.get("page")
    remaining_health_news = paginator.get_page(page)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string(
            "partials/health_latest_news.html",
            {"remaining_health_news": remaining_health_news},
            request=request,
        )
        return JsonResponse({"html": html})

    return render(request, "news/health_news.html", {
        "top_health_news": top_health_news,
        "remaining_health_news": remaining_health_news,
    })


def science_news(request):

    science_news = Article.objects.filter(
        status="published",
        category__category_name="Science & Technology"
    )

    top_science_news = science_news[:3]

    paginator = Paginator(science_news[3:], 4)

    page = request.GET.get("page")
    remaining_science_news = paginator.get_page(page)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string(
            "partials/science_latest_news.html",
            {"remaining_science_news": remaining_science_news},
            request=request,
        )
        return JsonResponse({"html": html})

    return render(request, "news/science_news.html", {
        "top_science_news": top_science_news,
        "remaining_science_news": remaining_science_news,
    })


def expanded_news(request, slug):
    
    return render(request, "news/expanded_news.html")

def get_newsarticle_data(request, slug):
    
    article = get_object_or_404(
        Article.objects.select_related("category"),
        
        slug=slug,
        status="published"
    )
    
    hero = {}

    if article.hero_media:
        ext = article.hero_media.name.split(".")[-1].lower()

        if ext in ["mp4", "webm", "ogg"]:
            hero = {
                "type": "video",
                "src": article.hero_media.url,
                "caption": article.hero_caption or ""
            }
        else:
            hero = {
                "type": "image",
                "src": article.hero_media.url,
                "caption": article.hero_caption or ""
            }
    
    blocks = article.blocks.all()
    
    body_blocks = []
    
    for block in blocks:
        
        print("Block ID:", block.id)
        print("Block Type:", block.block_type)
        print("----------------------")
        data = block.data or {}
        
        block_json = {
            "type": block.block_type
        }
        
        if block.block_type == "paragraph":
            
            block_json["content"] = data.get("content","")
            
        
        elif block.block_type == "heading":

            block_json["content"] = block.title
            
        elif block.block_type == "highlight":
            block_json["type"] = "box-highlight"
            block_json["title"] = data.get("title", "")
            block_json["content"] = data.get("content", "")
        
        elif block.block_type == "warning":
            block_json["type"] = "box-warning"
            block_json["title"] = data.get("title", "")
            block_json["content"] = data.get("content", "")
        
        elif block.block_type == "info":
            block_json["type"] = "box-info"
            block_json["title"] = data.get("title", "")
            block_json["content"] = data.get("content", "")
        
        elif block.block_type == "image":

            media = block.media_files.first()

            block_json["src"] = media.file.url if media else ""
            block_json["caption"] = media.caption if media else ""
            block_json["alt"] = data.get("alt", "")
            block_json["alignment"] = data.get("alignment", "left")
            
        elif block.block_type == "pull-quote":
            block_json["type"] = "pull-quote"
            block_json["content"] = data.get("quote", "")
            block_json["attribution"] = data.get("author", "")
        
        elif block.block_type == "list":

            block_json["ordered"] = data.get("ordered", False)
            block_json["items"] = data.get("items", [])
            
        elif block.block_type == "table":

            block_json["headers"] = data.get("headers", [])
            block_json["rows"] = data.get("rows", [])
        
        elif block.block_type == "gallery":

            images = []

            for media in block.media_files.all():
                images.append({
                    "src": media.file.url,
                    "caption": media.caption
                })

            block_json["images"] = images
            
        elif block.block_type == "video":

            media = block.media_files.first()

            block_json["sourceType"] = data.get("sourceType", "upload")
            block_json["url"] = media.file.url if media else ""
            block_json["embedUrl"] = data.get("embedUrl", "")
            

            media = block.media_files.first()

                            
        
        body_blocks.append(block_json)
        


    
    return JsonResponse({
        "success": True,
        "title": article.title,
        "subtitle": article.subtitle,
        "category": article.category.category_name,
        "reading_time": article.reading_time,
        "hero": hero,
        "bodyBlocks": body_blocks
    })

########################################## News page  END- MrGow #####################################


##########################################Speed  Guide page #####################################
def guide(request):
    return render(
        request, "Academics/speed/Guide.html", context={"active_main_nav": "academics"}
    )


def actuarialscience(request):
    return render(request, "Academics/actuarialscience_dashboard.html")


############################################speed code end #######################################


######  Rixie code  start###############################


def accountingcourse(request):
    return render(request, "Academics/accountingcourse_dashboard.html")


###########Rixie code end #################################

########### Speed code Starts######################################


def academic_course_details(request):
    departments = Department.objects.filter(status="ACTIVE").order_by(
        Lower("department_name")
    )

    grouped = {}
    for dept in departments:
        first_letter = dept.department_name[0].upper()
        grouped.setdefault(first_letter, []).append(dept)

    sorted_items = sorted(grouped.items())

    return render(
        request,
        "Academics/Acedemic_department_details.html",
        {"grouped_items": sorted_items},
    )


from django.utils.text import slugify

DESIGNATION_SECTION_MAP = {
    'core general education': 'core-general-education',
    'communication': 'communication',
    'quantitative reasoning': 'quantitative-reasoning',
    'ethnic studies': 'ethnic-studies',
    'breadth': 'breadth',
    'language': 'language',
    'l&s level': 'ls-level',
    'l&s liberal arts and science': 'additional-designations',
    'honors': 'honors',
    'counts toward 50% graduate coursework requirement': 'graduate-coursework',
    'workplace experience': 'workplace-experience',
}


def course_designation_page(request):
    designation_types = CourseDesignationType.objects.filter(status='ACTIVE').order_by('designation_name')
    enriched = []
    for dt in designation_types:
        section_id = DESIGNATION_SECTION_MAP.get(
            dt.designation_name.lower(),
            slugify(dt.designation_name)
        )
        enriched.append({'name': dt.designation_name, 'section_id': section_id})
    return render(request, 'Academics/course_designation_page.html', {
        'designation_types': enriched,
    })

def course_requisites_page(request):
    return render(request, "Academics/course_requisites_page.html")


def acedemic_department_details(request, slug):
    dept = get_object_or_404(Department, slug=slug, status="ACTIVE")
    courses = (
        dept.courses.filter(status="ACTIVE")
        .select_related("department")
        .prefetch_related(
            "requirements__requirement_type",
            "requirements__related_course",
            "designations__designation_type",
            "offerings",
            "learning_outcomes",
        )
        .order_by("course_code")
    )
    return render(
        request,
        "Academics/Academic_course_details.html",
        {
            "dept": dept,
            "courses": courses,
        },
    )


########### Speed code ends ######################################


####################Rixie code start ########################
def graduate_programs(request):
    return render(request, "Academics/Rixie/graduatebase.html")


def graduate_page(request):
    return render(request, 'Academics/Rixie/graduatepage.html')
def academic_advising(request):
    return render(request,'Academics/Rixie/academic_advising.html')
def academic_advising_about(request):
    return render(request,'Academics/Rixie/academic_domain_about.html')
def academic_advising_contact(request):
    return render(request,'Academics/Rixie/academic_domain_contact.html')
def findadvisor(request):
    return render(request,'Academics/Rixie/findadvisor.html')
def student_searchandenroll(request):
    return render(request,'Academics/Rixie/student_searchandenroll.html')
def student_thirdsection(request):
    return render(request,'Academics/Rixie/student_thirdsection.html')
def student_resources(request):
    return render(request,'Academics/speed/student_resources.html')
def depart_and_programs(request):
    departments = Department.objects.filter(
        status='ACTIVE'
    ).order_by('department_name')

    context = {
        'departments': departments
    }

    return render(
        request,
        'Academics/Rixie/depart_and_program.html',
        context
    )
def student_fourthsection(request):
    return render(request,'Academics/Rixie/student_fourthsection.html')
def prospective(request):
    return render(request,'Academics/Rixie/prospective.html')
def leadership_page(request):
    return render(request,'About/Rixie/leadershippage.html')
def explore(request):
    return render(request,'About/Rixie/explorefactspage.html')
def meetleader(request):
    return render(request,'About/Rixie/meetleaderpage.html')
def reghomepage(request):
    return render(request,'Academics/Rixie/registerbase.html')
def reghome(request):
    return render(request,'Academics/Rixie/registrarhomepage.html')
def transfer(request):
    return render(request,'Academics/Rixie/transfercredit.html')
def coursecreditevaluation(request):
    return render(request,'Academics/Rixie/coursecreditevaluation.html')
def testcredit(request):
    return render(request,'Academics/Rixie/testcredit.html')

# Admin/views.py - Add this function

# from .models import Hostel, Room, RoomAllocation  # Add this import at top

# @login_required
# def hostel_dashboard(request, uuid):
#     """Hostel Admin Dashboard"""
#     if str(request.user.uuid) != str(uuid):
#         return redirect("login")
    
#     # Permission check
#     if not (request.user.is_admin or request.user.is_hostel_admin):
#         messages.error(request, "You don't have permission to access this page.")
#         return redirect("login")
    
#     # Statistics
#     total_hostels = Hostel.objects.filter(status='ACTIVE').count()
#     total_rooms = Room.objects.count()
#     available_rooms = Room.objects.filter(is_available=True, status='AVAILABLE').count()
#     occupied_rooms = Room.objects.filter(status='OCCUPIED').count()
#     maintenance_rooms = Room.objects.filter(status='MAINTENANCE').count()
#     active_allocations = RoomAllocation.objects.filter(status='ACTIVE').count()
#     total_students = User.objects.filter(is_student=True, account_status='ACTIVE').count()
    
#     # Recent allocations
#     recent_allocations = RoomAllocation.objects.select_related(
#         'student', 'room', 'room__hostel'
#     ).order_by('-allocated_date')[:5]
    
#     context = {
#         'user': request.user,
#         'total_hostels': total_hostels,
#         'total_rooms': total_rooms,
#         'available_rooms': available_rooms,
#         'occupied_rooms': occupied_rooms,
#         'maintenance_rooms': maintenance_rooms,
#         'active_allocations': active_allocations,
#         'total_students': total_students,
#         'recent_allocations': recent_allocations,
#         'active_sb': 'hostel_dashboard'
#     }
#     return render(request, 'Admin/Blaze_Hostel/hostel_dashboard.html', context)


