#####################  steve code start ######################################

from django.shortcuts import render, redirect
from .models import University,School, Degree, AcademicProgram, ProgramCourse,AcademicTerm, ProgramConcentration
from .forms import UniversityForm, SchoolForm, DegreeForm, AcademicProgramForm, AcademicTermForm,ProgramCourseForm,ProgramCourseBulkForm
from django.utils import timezone
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404    
from django.db.models import Count, Avg, Q,Sum
from datetime import datetime
import uuid
from django.shortcuts import render, redirect
from django.contrib import messages
from Admin.bela_admin.models import Department, Course
from django.db.models import Q
from math import ceil
from django.db import transaction
from Admin.bela_admin.models import (
    Department,
    CourseLearningOutcome,
)
from itertools import groupby

from Faculty.models import FacultyProfile
from django.http import JsonResponse
from Admin.bela_admin.models import Course

def university_list(request):
 
    universities_qs = University.objects.all().order_by('-created_at')
 
    # Search 
    search_query = request.GET.get('q', '').strip()
    from django.db.models import Q

    if search_query:
        universities_qs = universities_qs.filter(
            Q(university_name__icontains=search_query) |
            Q(university_short_name__icontains=search_query) |
            Q(university_code__icontains=search_query) |
            Q(official_email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(state__icontains=search_query) |
            Q(country__icontains=search_query) |
            Q(postal_code__icontains=search_query)
        )
        universities_qs = universities_qs.distinct()
 
    # Pagination 
    paginator = Paginator(universities_qs, 10)  
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
 
    
    current = page_obj.number
    total   = paginator.num_pages
 
    def smart_range(current, total):
        pages = set()
        pages.update([1, 2])                        
        pages.update([total - 1, total])             
        for i in range(current - 2, current + 3):   
            if 1 <= i <= total:
                pages.add(i)
        return sorted(pages)
 
    page_range = smart_range(current, total)
 

    smart_pages = []
    prev = None
    for p in page_range:
        if prev is not None and p - prev > 1:
            smart_pages.append(None)   
        smart_pages.append(p)
        prev = p
 

    all_universities = University.objects.all()
    total_schools    = School.objects.count()
    added_this_year  = University.objects.filter(
        created_at__year=timezone.now().year
    ).count()
    oldest_university = all_universities.order_by('established_year').first()
    newest_university = all_universities.order_by('-established_year').first()
 
    context = {
        "universities":      page_obj,         
        "all_count":         all_universities.count(),
        "page_obj":          page_obj,
        "paginator":         paginator,
        "smart_pages":       smart_pages,
        "search_query":      search_query,
        "total_schools":     total_schools,
        "added_this_year":   added_this_year,
        "oldest_university": oldest_university,
        "newest_university": newest_university,
    }
 
    return render(request, "university/university_list.html", context)





def add_university(request):

    if request.method == "POST":

    
        form = UniversityForm(request.POST, request.FILES)

        if form.is_valid():
            university = form.save()

            messages.success(
                request,
                f'University "{university.university_name}" has been created successfully.'
            )
            return redirect("university_list")

        else:

            messages.error(
                request,
                "University could not be saved — please open each section "
                "below and correct the highlighted fields."
            )

    else:
        form = UniversityForm()

    return render(
        request,
        "university/add_university.html",
        {
            "form": form
        }
    )



def edit_university(request, university_id):

    university = get_object_or_404(
        University,
        university_id=university_id
    )

    if university.status == "INACTIVE":
        messages.info(
            request,
            f'University "{university.university_name}" is inactive. Please activate it before editing.'
        )
        return redirect("university_list")

    
    if request.method == "POST":
        form = UniversityForm(
            request.POST,
            request.FILES,
            instance=university
        )

        if form.is_valid():

            if not form.has_changed():
                messages.info(
                    request,
                    "No changes were made. University details remain unchanged."
                )

                return render(
                    request,
                    "university/edit_university.html",
                    {
                        "form": form,
                        "university": university,
                    }
                )

            university = form.save()

            messages.success(
                request,
                f'University "{university.university_name}" has been updated successfully.'
            )

            return redirect("university_list")

    else:

        form = UniversityForm(
            instance=university
        )

    return render(
        request,
        'university/edit_university.html',
        {
            'form': form,
            'university': university
        }
    )





@transaction.atomic
def toggle_university_status(request, university_id):

    university = get_object_or_404(
        University,
        university_id=university_id
    )

    new_status = (
        "INACTIVE"
        if university.status == "ACTIVE"
        else "ACTIVE"
    )

    # University
    university.status = new_status
    university.save(update_fields=["status"])

    # Schools
    School.objects.filter(
        university=university
    ).update(status=new_status)

    # Departments
    Department.objects.filter(
        school__university=university
    ).update(status=new_status)

    # Courses
    Course.objects.filter(
        department__school__university=university
    ).update(status=new_status)

    # Academic Programs
    AcademicProgram.objects.filter(
        department__school__university=university
    ).update(status=new_status)

    # Program Curriculum
    ProgramCourse.objects.filter(
        program__department__school__university=university
    ).update(status=new_status)

    return redirect('university_list')









def university_detail(request, university_id):

    if isinstance(university_id, str):
        university_id = uuid.UUID(university_id)

    university = get_object_or_404(
        University,
        university_id=university_id
    )

    schools = School.objects.filter(
        university=university
    ).order_by("school_name")

    total_schools = schools.count()

    departments = Department.objects.filter(
        school__university=university
    )

    total_departments = departments.count()

    programs = AcademicProgram.objects.filter(
        department__school__university=university
    )

    total_programs = programs.count()

    courses = Course.objects.filter(
        department__school__university=university
    )

    total_courses = courses.count()

    total_degrees = Degree.objects.filter(
        programs__department__school__university=university
    ).distinct().count()

    total_concentrations = ProgramConcentration.objects.filter(
        program__department__school__university=university
    ).count()

    for school in schools:
        school.department_count = Department.objects.filter(
            school=school
        ).count()

        school.program_count = AcademicProgram.objects.filter(
            department__school=school
        ).count()

        school.course_count = Course.objects.filter(
            department__school=school
        ).count()

    recent_schools = schools.order_by("-created_at")[:5]

    accreditations = []

    if university.accreditation:
        accreditations = [
            item.strip()
            for item in university.accreditation.split(",")
        ]

    current_year = datetime.now().year

    years_active = current_year - university.established_year

    context = {
        "university": university,
        "schools": schools,
        "recent_schools": recent_schools,
        "accreditations": accreditations,
        "current_year": current_year,
        "years_active": years_active,
        "total_schools": total_schools,
        "total_departments": total_departments,
        "total_programs": total_programs,
        "total_courses": total_courses,
        # "total_students": total_students,
        "total_degrees": total_degrees,
        "total_concentrations": total_concentrations,
    }

    return render(
        request,
        "university/university_detail.html",
        context,
    )

def school_list(request):
 
    schools_qs = School.objects.select_related('university').order_by('-created_at')
 

    search_query = request.GET.get('q', '').strip()
    if search_query:
        schools_qs = schools_qs.filter(

            Q(school_name__icontains=search_query) |
            Q(school_short_name__icontains=search_query) |
            Q(school_code__icontains=search_query) |
            Q(university__university_name__icontains=search_query) |
            Q(university__university_short_name__icontains=search_query) |
            Q(official_email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(state__icontains=search_query) |
            Q(country__icontains=search_query) |
            Q(school_type__icontains=search_query)

        ).distinct()
 
  
    all_schools        = School.objects.select_related('university')
    total_schools      = all_schools.count()
    total_universities = all_schools.values('university').distinct().count()
    added_this_year    = all_schools.filter(
        created_at__year=timezone.now().year
    ).count()
 
 
    paginator   = Paginator(schools_qs, 10)
    page_number = request.GET.get('page', 1)
    page_obj    = paginator.get_page(page_number)
 

    def smart_range(current, total):
        pages = set()
        pages.update([1, 2])
        pages.update([total - 1, total])
        for i in range(current - 2, current + 3):
            if 1 <= i <= total:
                pages.add(i)
        return sorted(pages)
 
    page_range  = smart_range(page_obj.number, paginator.num_pages)
    smart_pages = []
    prev = None
    for p in page_range:
        if prev is not None and p - prev > 1:
            smart_pages.append(None)
        smart_pages.append(p)
        prev = p
    
    has_universities = University.objects.exists()
    
    # Schools with no dean assigned
    schools_without_dean = School.objects.select_related(
        "university"
    ).filter(
        dean__isnull=True,
        status="ACTIVE"
    ).order_by("school_name")
    
    context = {
        'schools':            page_obj,
        'page_obj':           page_obj,
        'paginator':          paginator,
        'smart_pages':        smart_pages,
        'search_query':       search_query,
        'total_schools':      total_schools,
        'total_universities': total_universities,
        'added_this_year':    added_this_year,
        'has_universities':   has_universities,
        'schools_without_dean': schools_without_dean,
        'schools_without_dean_count': schools_without_dean.count(),
    }
 
    return render(request, 'school/school_list.html', context)
 
    


def add_school(request):

    if not University.objects.exists():
        messages.warning(
            request,
            "You must create a university before adding a school."
        )
        return redirect("add_university")

    universities = University.objects.all()

    if request.method == "POST":


        form = SchoolForm(request.POST, request.FILES)

        if form.is_valid():
            school = form.save()

            messages.success(
                request,
                f'School "{school.school_name}" has been created successfully.'
            )
            return redirect("school_list")

        else:

            messages.error(
                request,
                "School could not be saved — please open each section "
                "below and correct the highlighted fields."
            )

    else:
        form = SchoolForm()

    return render(
        request,
        "school/add_school.html",
        {
            "form": form,
            "universities": universities,
        },
    )



def edit_school(request, school_id):

    school = get_object_or_404(
        School,
        school_id=school_id
    )

    if school.status == "INACTIVE":
        messages.info(
            request,
            f'School "{school.school_name}" is inactive. Please activate it before editing.'
        )
        return redirect("school_list")

    universities = University.objects.all()

    if request.method == "POST":

        form = SchoolForm(
            request.POST,
            request.FILES,   
            instance=school
        )

        if form.is_valid():

            if form.has_changed():

                school = form.save()

                messages.success(
                    request,
                    f'School "{school.school_name}" has been updated successfully.'
                )

                return redirect("school_list")

            messages.info(
                request,
                "No changes were made. School details remain unchanged."
            )

    else:

        form = SchoolForm(
            instance=school
        )

    return render(
        request,
        "school/edit_school.html",
        {
            "form": form,
            "school": school,
            "universities": universities,
        }
    )
    
    




def toggle_school_status(request, school_id):

    school = get_object_or_404(
        School,
        school_id=school_id
    )

    # If currently ACTIVE -> Deactivate
    if school.status == "ACTIVE":

        school.status = "INACTIVE"
        school.save(update_fields=["status"])

        messages.success(
            request,
            f'"{school.school_name}" has been deactivated successfully.'
        )

    else:
        # Before activating, check parent University
        if school.university.status == "INACTIVE":

            messages.error(
                request,
                f'Cannot activate "{school.school_name}" because the parent University "{school.university.university_name}" is inactive. Please activate the University first.'
            )

            return redirect("school_list")

        school.status = "ACTIVE"
        school.save(update_fields=["status"])

        messages.success(
            request,
            f'"{school.school_name}" has been activated successfully.'
        )

    return redirect("school_list")


def school_detail(request, school_id):

    if isinstance(school_id, str):
        try:
            school_id = uuid.UUID(school_id)
        except ValueError:
            pass

    school = get_object_or_404(
        School.objects.select_related('university'),
        school_id=school_id
    )
    university = school.university

    
    departments = Department.objects.filter(school=school).order_by("department_name")
    total_departments = departments.count()

    
    programs = AcademicProgram.objects.filter(department__school=school)
    total_programs = programs.count()

    
    total_courses = Course.objects.filter(department__school=school).count()

    
    for dept in departments:
        dept.program_count = AcademicProgram.objects.filter(department=dept).count()
        dept.course_count = Course.objects.filter(department=dept).count()

    
    current_year = datetime.now().year
    years_active = (
        current_year - school.established_year
        if school.established_year else None
    )

    

    context = {
        'school': school,
        'university': university,
        'departments': departments,
        'programs': programs,
        'total_departments': total_departments,
        'total_programs': total_programs,
        'total_courses': total_courses,
        'current_year': current_year,
        'years_active': years_active,
    }

    return render(request, 'school/school_detail.html', context)



def degree_list(request):

    degrees_qs = Degree.objects.all().order_by("degree_name")


    search_query = request.GET.get("q", "").strip()
    if search_query:
        degrees_qs = (
            degrees_qs.filter(degree_name__icontains=search_query)
            | degrees_qs.filter(degree_code__icontains=search_query)
            | degrees_qs.filter(level__icontains=search_query)
        ).distinct()

    paginator   = Paginator(degrees_qs, 10)
    page_number = request.GET.get("page", 1)
    page_obj    = paginator.get_page(page_number)

    current = page_obj.number
    total   = paginator.num_pages

    def smart_range(current, total):
        pages = set()
        pages.update([1, 2])
        pages.update([total - 1, total])
        for i in range(current - 2, current + 3):
            if 1 <= i <= total:
                pages.add(i)
        return sorted(pages)

    page_range  = smart_range(current, total)
    smart_pages = []
    prev        = None
    for p in page_range:
        if prev is not None and p - prev > 1:
            smart_pages.append(None)  
        smart_pages.append(p)
        prev = p


    all_degrees = Degree.objects.all()

    context = {
        "degrees":      page_obj,
        "all_count":    all_degrees.count(),
        "ug_count":     all_degrees.filter(level="UG").count(),
        "pg_count":     all_degrees.filter(level="PG").count(),
        "phd_count":    all_degrees.filter(level="PHD").count(),
        "page_obj":     page_obj,
        "paginator":    paginator,
        "smart_pages":  smart_pages,
        "search_query": search_query,
    }

    return render(request, "degree/degree_list.html", context)
    

def add_degree(request):

    if request.method == "POST":

        form = DegreeForm(request.POST)

        if form.is_valid():

            degree = form.save()
            
            messages.success(
                request,
                f'Degree "{degree.degree_name}" has been created successfully.'
            )

            return redirect("degree_list")

    else:

        form = DegreeForm()

    return render(
        request,
        "degree/add_degree.html",
        {
            "form": form
        }
    )

def edit_degree(request, id):

    degree = get_object_or_404(Degree, pk=id)
    
    
    if degree.status == "INACTIVE":
        messages.info(
            request,
            f'Degree "{degree.degree_name}" is inactive. Please activate it before editing.'
        )
        return redirect("degree_list")

    if request.method == "POST":

        form = DegreeForm(
            request.POST,
            instance=degree
        )

        if form.is_valid():
            degree = form.save()
            
            messages.success(
                request,
                f'Degree "{degree.degree_name}" has been updated successfully.'
            )
            
            return redirect("degree_list")

    else:

        form = DegreeForm(instance=degree)

    return render(
        request,
        "degree/edit_degree.html",
        {
            "form": form,
            "degree": degree,
        },
    )




def toggle_degree_status(request, id):

    degree = get_object_or_404(Degree, pk=id)

    if degree.status == "ACTIVE":
        degree.status = "INACTIVE"
    else:
        degree.status = "ACTIVE"

    degree.save()

    return redirect("degree_list")


def program_list(request):
    search_query = request.GET.get("q", "").strip()
    
    programs = AcademicProgram.objects.select_related(
        "department",
        "degree"
    )
    
    if search_query:
        programs = programs.filter(
            Q(program_name__icontains=search_query) |
            Q(program_code__icontains=search_query) |
            Q(department__department_name__icontains=search_query) |
            Q(degree__degree_name__icontains=search_query)
        )
    
    paginator = Paginator(programs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
  
    current = page_obj.number
    total = paginator.num_pages
    
    if total <= 7:
        smart_pages = list(range(1, total + 1))
    else:
        smart_pages = []
        if current <= 4:
            smart_pages = [1, 2, 3, 4, 5, None, total]
        elif current >= total - 3:
            smart_pages = [1, None, total - 4, total - 3, total - 2, total - 1, total]
        else:
            smart_pages = [1, None, current - 1, current, current + 1, None, total]
            
    
    has_departments = Department.objects.exists()
    has_degrees = Degree.objects.exists()
    
    context = {
        "programs": page_obj,
        "page_obj": page_obj,
        "paginator": paginator,
        "smart_pages": smart_pages,
        "search_query": search_query,
        "all_count": AcademicProgram.objects.count(),
        "active_count": AcademicProgram.objects.filter(status="ACTIVE").count(),
        "inactive_count": AcademicProgram.objects.filter(status="INACTIVE").count(),
        "full_time_count": AcademicProgram.objects.filter(program_type="FULL_TIME").count(),
        "has_departments": has_departments,
        "has_degrees": has_degrees,
    }
    
    return render(request, "program/program_list.html", context)




def add_program(request):
    if request.method == "POST":
        form = AcademicProgramForm(request.POST)
        if form.is_valid():
            program = form.save()
            messages.success(request, f'Program "{program.program_name}" has been created successfully.')
            return redirect("program_list")
    else:
        form = AcademicProgramForm()
    
    
    context = {
        "form": form,
        "total_count": AcademicProgram.objects.count(),
        "active_count": AcademicProgram.objects.filter(status="ACTIVE").count(),
        "dept_count": Department.objects.count(),
    }
    return render(request, "program/add_program.html", context)




def edit_program(request, id):

    program = get_object_or_404(
        AcademicProgram,
        pk=id
    )
    
    if program.status == "INACTIVE":
        messages.info(
            request,
            f'Program "{program.program_name}" is inactive. Please activate it before editing.'
        )
        return redirect("program_list")

    if request.method == "POST":

        form = AcademicProgramForm(
            request.POST,
            instance=program
        )

        if form.is_valid():

            program = form.save()

            messages.success(
                request,
                f'Program "{program.program_name}" has been updated successfully.'
            )

            return redirect("program_list")

    else:

        form = AcademicProgramForm(
            instance=program
        )

    context = {
        "form": form,
        "program": program,
        "total_count": AcademicProgram.objects.count(),
        "active_count": AcademicProgram.objects.filter(status="ACTIVE").count(),
        "dept_count": Department.objects.count(),
    }

    return render(
        request,
        "program/edit_program.html",
        context,
    )
    
    


def toggle_program_status(request, id):

    program = get_object_or_404(
        AcademicProgram,
        pk=id
    )

    # Deactivate Program
    if program.status == "ACTIVE":

        program.status = "INACTIVE"
        program.save(update_fields=["status"])

        messages.success(
            request,
            f'"{program.program_name}" has been deactivated successfully.'
        )

    else:

        # Check if parent Department is active
        if program.department.status == "INACTIVE":

            messages.error(
                request,
                f'Cannot activate "{program.program_name}" because the parent Department "{program.department.department_name}" is inactive. Please activate the Department first.'
            )

            return redirect("program_list")

        program.status = "ACTIVE"
        program.save(update_fields=["status"])

        messages.success(
            request,
            f'"{program.program_name}" has been activated successfully.'
        )

    return redirect("program_list")




def program_detail(request, program_id):

    program = get_object_or_404(
        AcademicProgram.objects.select_related(
            "department",
            "department__school",
            "department__school__university",
            "degree",
        ),
        program_id=program_id,
    )

    department = program.department
    school = department.school
    university = school.university
    degree = program.degree

    courses = (
        ProgramCourse.objects
        .filter(program=program)
        .select_related("course")
        .order_by("study_year", "term", "course__course_code")
    )
    
    from itertools import groupby

    course_groups = []

    for (year, term), items in groupby(
        courses,
        key=lambda x: (x.study_year, x.term)
    ):
        course_groups.append({
            "study_year": year,
            "term": term,
            "courses": list(items),
        })

    total_courses = courses.count()
    total_credits = (
        courses.aggregate(
            total=Sum("course__credits")
        )["total"] or 0
    )

    faculty_members = (
        FacultyProfile.objects
        .filter(
            department=department,
            employment_status="ACTIVE",
        )
        .select_related(
            "user",
            "faculty_rank",
        )
        .order_by("user__first_name")
    )

    total_faculty = faculty_members.count()

    learning_outcomes = (
        CourseLearningOutcome.objects
        .filter(
            course__in=courses.values_list(
                "course_id",
                flat=True
            )
        )
        .order_by(
            "course__course_code",
            "display_order"
        )
    )

    program_timeline = (
        courses
        .values("study_year", "term")
        .annotate(
            total_courses=Count("course"),
            total_credits=Sum("course__credits"),
        )
        .order_by("study_year", "term")
    )

    program_stats = {

        "faculty": total_faculty,
        "courses": total_courses,
        "credits": total_credits,
        "duration": program.duration,
        "students": 0,
        "graduated": 0,
    }

    career_opportunities = []
    admission_requirements = None
    accreditations = []

    context = {

        "program": program,
        "department": department,
        "school": school,
        "university": university,
        "degree": degree,
        "courses": courses,
        "faculty_members": faculty_members,
        "learning_outcomes": learning_outcomes,
        "program_timeline": program_timeline,
        "career_opportunities": career_opportunities,
        "admission_requirements": admission_requirements,
        "accreditations": accreditations,
        "program_stats": program_stats,
        "total_courses": total_courses,
        "total_faculty": total_faculty,
        "total_credits": total_credits,
        "current_year": datetime.now().year,
        "course_groups": course_groups,
    }

    return render(
        request,
        "program/program_detail.html",
        context,
    )



def get_page_range(current, total, edge=2, window=1):


    if total <= (edge * 2 + window * 2 + 3):
        return list(range(1, total + 1))

    pages = set()

    for i in range(1, edge + 1):
        pages.add(i)

    for i in range(total - edge + 1, total + 1):
        pages.add(i)

    for i in range(current - window, current + window + 1):
        if 1 <= i <= total:
            pages.add(i)

    sorted_pages = sorted(pages)

    result = []
    prev = None

    for p in sorted_pages:
        if prev is not None and p - prev > 1:
            result.append("...")
        result.append(p)
        prev = p

    return result



def program_course_list(request):

    program_courses = (
        ProgramCourse.objects
        .select_related("program", "course")
        .order_by(
            "program",
            "study_year",
            "term",
            "course",
        )
    )

    search     = request.GET.get("search", "").strip()
    semester   = request.GET.get("semester", "").strip()   
    program_id = request.GET.get("program", "").strip()
    status     = request.GET.get("status", "").strip()
    elective   = request.GET.get("elective", "").strip()

    if search:
        program_courses = program_courses.filter(
            Q(program__program_name__icontains=search) |
            Q(course__course_name__icontains=search) |
            Q(course__course_code__icontains=search)
        )

    if semester:
      
        program_courses = program_courses.filter(term=semester)

    if program_id:
        program_courses = program_courses.filter(program_id=program_id)

    if status:
        program_courses = program_courses.filter(status=status)

    if elective in ("yes", "no"):
        program_courses = program_courses.filter(is_elective=(elective == "yes"))

    total_count = program_courses.count()

    
    groups = []
    for (program_id_key, study_year, term), items in groupby(
        program_courses, key=lambda pc: (pc.program_id, pc.study_year, pc.term)
    ):
        items = list(items)
        groups.append({
            "program": items[0].program,
            "study_year": study_year,
            "study_year_display": items[0].get_study_year_display(),
            "term": term,
            "term_display": items[0].get_term_display(),
            "courses": items,
            "course_count": len(items),
            "active_count": sum(1 for i in items if i.status == "ACTIVE"),
            "elective_count": sum(1 for i in items if i.is_elective),
        })

    group_count = len(groups)

    paginator   = Paginator(groups, 8) 
    page_number = request.GET.get("page")
    page_obj    = paginator.get_page(page_number)

    page_range = get_page_range(page_obj.number, paginator.num_pages)

    querydict = request.GET.copy()
    querydict.pop("page", None)

    active_filters = any([search, semester, program_id, status, elective])

    has_programs = AcademicProgram.objects.exists()
    has_courses = Course.objects.exists()

    context = {
        "page_obj": page_obj,
        "page_range": page_range,
        "groups": page_obj.object_list,
        "programs": AcademicProgram.objects.all().order_by("program_name"),

        "status_choices": ProgramCourse.STATUS_CHOICES,
        "semester_choices": ProgramCourse.TERM_CHOICES,   
        "search": search,
        "selected_semester": semester,
        "selected_program": program_id,
        "selected_status": status,
        "selected_elective": elective,
        "querystring": querydict.urlencode(),
        "total_count": total_count,
        "group_count": group_count,
        "active_filters": active_filters,
        "has_programs": has_programs,
        "has_courses": has_courses,
    }

    return render(
        request,
        "program_course/program_course_list.html",
        context
    )





def add_program_course(request):
    if request.method == "POST":
        form = ProgramCourseBulkForm(request.POST)

        if form.is_valid():
            program = form.cleaned_data["program"]
            study_year = form.cleaned_data["study_year"]
            term = form.cleaned_data["term"]
            # status = form.cleaned_data["status"]
            courses = form.cleaned_data["courses"]

            # elective_courses[] holds the ids of courses whose "Elective" toggle was on
            elective_ids = set(request.POST.getlist("elective_courses"))

            created_count = 0
            skipped_count = 0

            with transaction.atomic():
                for course in courses:
                    obj, was_created = ProgramCourse.objects.get_or_create(
                        program=program,
                        course=course,
                        study_year=study_year,
                        term=term,
                        defaults={
                            "is_elective": str(course.course_id) in elective_ids,
                            # "status": status,
                        },
                    )
                    if was_created:
                        created_count += 1
                    else:
                        skipped_count += 1

            if created_count:
                messages.success(
                    request,
                    f"{created_count} course(s) added to the curriculum successfully."
                )
            if skipped_count:
                messages.warning(
                    request,
                    f"{skipped_count} course(s) were already in this program/year/term "
                    f"and were skipped."
                )

            return redirect("program_course_list")
    else:
        form = ProgramCourseBulkForm()

    return render(request, "program_course/add_program_course.html", {"form": form})


def get_program_courses(request, program_id):
  
    courses = Course.objects.filter(
        academic_program_id=program_id,
        status="ACTIVE",
    ).order_by("course_name")

 ###############  Rixie Code Start  ################
    if request.GET.get("exclude_allocated"):
        allocated_course_ids = set(
            ProgramCourse.objects.values_list("course_id", flat=True)
        )
        current_program_course_id = request.GET.get("current_program_course_id")
        if current_program_course_id:
            current_course_id = (
                ProgramCourse.objects.filter(
                    program_course_id=current_program_course_id
                )
                .values_list("course_id", flat=True)
                .first()
            )
            if current_course_id:
                allocated_course_ids.discard(current_course_id)
        courses = courses.exclude(course_id__in=allocated_course_ids)
###################  Rixie Code End  ########################
    data = [
        {
            "id": course.course_id,
            "code": course.course_code,
            "name": course.course_name,
        }
        for course in courses
    ]
    return JsonResponse(data, safe=False)
    
from django.db import IntegrityError, transaction

def edit_program_course(request, pk):

    program_course = get_object_or_404(ProgramCourse, pk=pk)

    if program_course.status == "INACTIVE":
        messages.info(
            request,
            f'Program course "{program_course.course.course_name}" is inactive. Please activate it before editing.'
        )
        return redirect("program_course_list")

    if request.method == "POST":
        form = ProgramCourseForm(request.POST, instance=program_course)

        if form.is_valid():
            try:
                with transaction.atomic():
                    program_course = form.save()
            except IntegrityError:
                form.add_error(
                    None,
                    "This program + course + year + term combination already exists."
                )
            else:
                messages.success(
                    request,
                    f'Program course "{program_course.course.course_name}" has been updated successfully.'
                )
                return redirect("program_course_list")
    else:
        form = ProgramCourseForm(instance=program_course)

    return render(
        request,
        "program_course/edit_program_course.html",
        {
            "form": form,
            "program_course": program_course,
        }
    )
    
    
def toggle_program_course_status(request, program_course_id):

    program_course = get_object_or_404(
        ProgramCourse,
        program_course_id=program_course_id
    )

    if program_course.status == "ACTIVE":

        program_course.status = "INACTIVE"
        program_course.save(update_fields=["status"])

        messages.success(
            request,
            "Program curriculum deactivated successfully."
        )

    else:

        if program_course.program.status == "INACTIVE":

            messages.error(
                request,
                "Cannot activate this curriculum because the Academic Program is inactive."
            )

            return redirect("program_course_list")

        if program_course.course.status == "INACTIVE":

            messages.error(
                request,
                "Cannot activate this curriculum because the Course is inactive."
            )

            return redirect("program_course_list")

        program_course.status = "ACTIVE"
        program_course.save(update_fields=["status"])

        messages.success(
            request,
            "Program curriculum activated successfully."
        )

    return redirect("program_course_list")




def academic_term_list(request):

    academic_terms = AcademicTerm.objects.all().order_by(
        "academic_year", "start_date"
    )

    search         = request.GET.get("search", "").strip()
    term           = request.GET.get("term",   "").strip()
    status         = request.GET.get("status", "").strip()

    if search:
        academic_terms = academic_terms.filter(
            Q(academic_year__icontains=search)
        )

    if term:
        academic_terms = academic_terms.filter(term_name=term)

    if status:
        academic_terms = academic_terms.filter(status=status)

    total_count = academic_terms.count()

    # ── Sidebar stat counts (always from full queryset) ──
    all_terms    = AcademicTerm.objects.all()
    active_count = all_terms.filter(status="ACTIVE").count()
    sem1_count   = all_terms.filter(term_name="SEM1").count() 
    sem2_count   = all_terms.filter(term_name="SEM2").count()
    summer_count = all_terms.filter(term_name="SUMMER").count()

    # ── Pagination ──
    paginator   = Paginator(academic_terms, 10)
    page_number = request.GET.get("page")
    page_obj    = paginator.get_page(page_number)
    page_range  = get_page_range(page_obj.number, paginator.num_pages)

    querydict = request.GET.copy()
    querydict.pop("page", None)

    context = {
        "page_obj":        page_obj,
        "academic_terms":  page_obj.object_list,
        "page_range":      page_range,
        "total_count":     total_count,
        "active_count":    active_count,
        "sem1_count":      sem1_count,
        "sem2_count":      sem2_count,
        "summer_count":    summer_count,
        "search":          search,
        "selected_term":   term,
        "selected_status": status,
        "querystring":     querydict.urlencode(),
        "active_filters":  any([search, term, status]),
        "term_choices":    AcademicTerm.TERM_CHOICES,
        "status_choices":  AcademicTerm.STATUS_CHOICES,
    }

    return render(request, "academic_term/academic_term_list.html", context)


def academic_term_create(request):

    if request.method == "POST":

        form = AcademicTermForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Academic Term created successfully."
            )

            return redirect("academic_term_list")

    else:

        form = AcademicTermForm()

    return render(
        request,
        "academic_term/academic_term_form.html",
        {
            "form": form,
            "page_title": "Add Academic Term",
            "submit_text": "Save Academic Term",
        },
    )


def academic_term_update(request, pk):

    academic_term = get_object_or_404(
        AcademicTerm,
        pk=pk,
    )

    
    if academic_term.status == "INACTIVE":
        messages.info(
            request,
            f'Academic Term "{academic_term.term_name}" is inactive. Please activate it before editing.'
        )
        return redirect("academic_term_list")

    if request.method == "POST":

        form = AcademicTermForm(
            request.POST,
            instance=academic_term,
        )

        if form.is_valid():

            academic_term = form.save()

            messages.success(
                request,
                f'Academic Term "{academic_term.term_name}" has been updated successfully.'
            )

            return redirect("academic_term_list")

    else:

        form = AcademicTermForm(
            instance=academic_term,
        )

    return render(
        request,
        "academic_term/edit_academic_term.html",
        {
            "form": form,
            "academic_term": academic_term,
            "page_title": "Edit Academic Term",
            "submit_text": "Update Academic Term",
        },
    )



def toggle_academic_term_status(request, pk):

    term = get_object_or_404(AcademicTerm, pk=pk)

    if term.status == "ACTIVE":
        term.status = "INACTIVE"
        messages.success(request, "Academic Term deactivated successfully.")
    else:
        term.status = "ACTIVE"
        messages.success(request, "Academic Term activated successfully.")

    term.save()

    return redirect("academic_term_list")






#####################  steve code end ######################################



from django.http import JsonResponse
from .models import AreaOfInterest

def add_area_of_interest(request):

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        print("Name:", name)

        if not name:
            return JsonResponse({
                "success": False,
                "message": "Area name is required."
            })

        if AreaOfInterest.objects.filter(interest_name__iexact=name).exists():
            return JsonResponse({
                "success": False,
                "message": "An area with this name already exists."
            })

        obj, created = AreaOfInterest.objects.get_or_create(
            interest_name=name
        )

        return JsonResponse({
            "success": True,
            "id": obj.id,
            "name": obj.interest_name
        })

    return JsonResponse({"success": False})


def delete_area_of_interest(request):
    if request.method == "POST":
        area_id = request.POST.get("area_id")
        if not area_id:
            return JsonResponse({"success": False, "message": "Area ID is required."})
        try:
            area = AreaOfInterest.objects.get(id=area_id)
            area.delete()
            return JsonResponse({"success": True, "message": "Area of interest deleted."})
        except AreaOfInterest.DoesNotExist:
            return JsonResponse({"success": False, "message": "Area not found."})
    return JsonResponse({"success": False})