from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.shortcuts import render, get_object_or_404
from .models import FacultyProfile
# Q is used for complex db queries using logical operators like AND, OR and NOT
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db import transaction

from datetime import date, datetime
import re
from .models import FacultyResearch, FacultyDocument, FacultyRank, FacultyGrant, FacultyEducation, FacultyAppointment
from .models import FacultyResearch, FacultyPublication,FacultyOfficeHours
from django.http import FileResponse, Http404
from django.core.files.storage import default_storage
from django.db.models import Q
import os

from Staff.models import Resource, AdvisorAssignment
from Staff.utils import get_resource_alerts_context, mark_resource_alerts_seen
from Students.models import StudentOrganization, StudentOrganizationMembership, StudentProfile,StudentAcademicProfile
from Students.models import StudentOrganization, StudentOrganizationMembership, StudentProfile
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from Admin.audit import AuditLogger

#blaze code start

# from Staff.utils import (
#     notify_staff_new_faculty_leave_request,
#     notify_faculty_leave_approved,
#     notify_faculty_leave_rejected,
# )


#blaze code end

# Gayathri G
class FacultyResearchView(TemplateView):
    template_name = "Academics/faculty_research.html"
    
    # To pass extra data to the template, kwargs mean keyword arguments
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        faculty = self.request.user.faculty_profile
        
        latest_evaluation = (
            faculty.evaluations
            .order_by("-id")      
            .first()
        )

        all_projects = (
            FacultyResearch.objects.filter(faculty=faculty)
        )

        total_projects = all_projects.count()
        ongoing_projects = all_projects.filter(status="ONGOING").count()
        completed_projects = all_projects.filter(status="COMPLETED").count()
        on_hold_projects = all_projects.filter(status="ON_HOLD").count()
        cancelled_projects = all_projects.filter(status="CANCELLED").count()
        
        if total_projects > 0:
            completed_percentage = round((completed_projects / total_projects) * 100)
            ongoing_percentage = round((ongoing_projects / total_projects) * 100)
            on_hold_percentage = round((on_hold_projects / total_projects) * 100)
            cancelled_percentage = round((cancelled_projects / total_projects) * 100)
        else:
            completed_percentage = 0
            ongoing_percentage = 0
            on_hold_percentage = 0
            cancelled_percentage = 0

        research_areas = (
            all_projects.values("research_area")
            .annotate(project_count=Count("id"))
            .order_by("-project_count")
        )
        
        # The second arg of get() is default value
        search = self.request.GET.get("search", "").strip()
        status = self.request.GET.get("status", "")
        sort = self.request.GET.get("sort") or "-start_date"
        
        research_projects = all_projects
        
        # Search
        if search:
            research_projects = research_projects.filter(
                Q(research_title__icontains=search) |
                Q(research_area__icontains=search)
            )

        # Filter by status
        if status:
            research_projects = research_projects.filter(status=status)

        # Sort
        research_projects = research_projects.order_by(sort)
        
        # Pagination
        paginator = Paginator(research_projects, 5)   # Show 5 projects per page

        page_number = self.request.GET.get("page")

        research_projects = paginator.get_page(page_number)

        context.update({
            "research_projects": research_projects,
            
            "total_projects": total_projects,
            "ongoing_projects": ongoing_projects,
            "completed_projects": completed_projects,
            "on_hold_projects": on_hold_projects,
            "cancelled_projects": cancelled_projects,
            
            "completed_percentage": completed_percentage,
            "ongoing_percentage": ongoing_percentage,
            "on_hold_percentage": on_hold_percentage,
            "cancelled_percentage": cancelled_percentage,
            
            "research_areas": research_areas,
            
            "latest_evaluation": latest_evaluation,
        })

        return context
    
# Gayathri G
class FacultyPublications(TemplateView):
    template_name = "Academics/faculty_publications.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        faculty = self.request.user.faculty_profile

        all_publications = (
            FacultyPublication.objects.filter(faculty=faculty)
        )

        # Statistics
        total_publications = all_publications.count()

        publications_with_doi = (
            all_publications.exclude(doi__isnull=True)
            .exclude(doi="")
            .count()
        )

        publication_types_count = (
            all_publications.values("publication_type")
            .distinct()
            .count()
        )

        latest_publication = (
            all_publications.exclude(publication_date__isnull=True)
            .order_by("-publication_date")
            .first()
        )

        # Search & Filter values
        search = self.request.GET.get("search", "").strip()
        publication_type = self.request.GET.get("type", "")
        sort = self.request.GET.get("sort") or "-publication_date"

        publications = all_publications

        # Search
        if search:
            publications = publications.filter(
                Q(title__icontains=search) |
                Q(journal_or_conference__icontains=search) |
                Q(doi__icontains=search)
            )

        # Filter
        if publication_type:
            publications = publications.filter(
                publication_type=publication_type
            )

        # Sort
        publications = publications.order_by(sort)

        # Pagination
        paginator = Paginator(publications, 5)
        
        # To get the current page number
        page_number = self.request.GET.get("page")

        # To get contents of the current page
        publications = paginator.get_page(page_number)

        context.update({
            "publications": publications,

            "total_publications": total_publications,
            "publications_with_doi": publications_with_doi,
            "publication_types_count": publication_types_count,
            "latest_publication": latest_publication,

            "publication_type_choices": FacultyPublication.PUBLICATION_TYPE_CHOICES,
        })

        return context
    
# Gayathri G
class FacultyGrants(TemplateView):
    template_name = 'Academics/faculty_grants.html'
    
# Gayathri G
class FacultyCommitteeWork(TemplateView):
    template_name = 'Academics/faculty_committeeWork.html'
    
# Gayathri G
class FacultyOfficeHoursView(TemplateView):
    template_name = 'Academics/faculty_officeHours.html'
    
# bela code********************************
class FacultyAdvisees(TemplateView):

    template_name = 'StudentAdvising/faculty_advisees.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        faculty = get_object_or_404(
            FacultyProfile,
            user=self.request.user
        )

        # -------------------------------------------------
        # Active advisor assignments belonging to faculty
        # -------------------------------------------------

        advisor_assignments = AdvisorAssignment.objects.filter(
            advisor=faculty,
            is_active=True
        ).select_related(
            "program",
            "program__department"
        )


        advisees = []


        # -------------------------------------------------
        # Find students covered by each assignment
        # -------------------------------------------------

        for assignment in advisor_assignments:

            students = StudentAcademicProfile.objects.filter(
                program=assignment.program,
                student__current_status="ACTIVE",
                student__admission_date__year=assignment.admission_batch
            ).select_related(
                "student",
                "student__user"
            ).order_by(
                "student__student_number"
            )


            roll_from = assignment.roll_number_from.strip().upper()
            roll_to = assignment.roll_number_to.strip().upper()


            for academic_profile in students:

                student = academic_profile.student

                student_number = (
                    student.student_number
                    .strip()
                    .upper()
                )


                # Check roll-number range

                if roll_from <= student_number <= roll_to:

                    advisees.append({
                        "student": student,
                        "academic_profile": academic_profile,
                        "assignment": assignment,
                        "program": assignment.program,
                        "department": assignment.program.department,
                        "batch": assignment.admission_batch,
                    })


        # -------------------------------------------------
        # Remove duplicates
        # -------------------------------------------------

        unique_advisees = {}

        for item in advisees:

            student_id = item["student"].pk

            unique_advisees[student_id] = item


        advisees = list(
            unique_advisees.values()
        )
        # =====================================================
        # SEARCH
        # =====================================================

        search = self.request.GET.get("q", "").strip().lower()

        if search:

            advisees = [
                item
                for item in advisees
                if (
                    search in item["student"].student_number.lower()
                    or search in (
                        item["student"].preferred_name or ""
                    ).lower()
                    or search in (
                        item["student"].user.get_full_name() or ""
                    ).lower()
                    or search in (
                        item["program"].program_name or ""
                    ).lower()
                )
            ]


        # =====================================================
        # STATS
        # =====================================================

        active_advisees = sum(
            1
            for item in advisees
            if item["student"].current_status == "ACTIVE"
        )


        undergraduate_advisees = sum(
            1
            for item in advisees
            if str(item["student"].academic_level).upper()
            in ["UNDERGRADUATE", "UG"]
        )


        graduate_advisees = len(advisees) - undergraduate_advisees

        # -------------------------------------------------
        # Sort by student number
        # -------------------------------------------------

        advisees.sort(
            key=lambda item: item["student"].student_number
        )


        context.update({

            "faculty": faculty,

            "advisees": advisees,

            "total_advisees": len(advisees),

            "active_advisees": active_advisees,

            "undergraduate_advisees": undergraduate_advisees,

            "graduate_advisees": graduate_advisees,

            "search": search,

            "advisor_assignments": advisor_assignments,

        })


        return context
    
# Navina


from django.db.models import Avg, Count

from collections import Counter


from django.contrib.auth.mixins import LoginRequiredMixin



class FacultyAdvisorDashboard(LoginRequiredMixin, TemplateView):

    template_name = "StudentAdvising/faculty_advisor_dashboard.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        # =====================================================
        # FACULTY
        # =====================================================

        faculty = FacultyProfile.objects.select_related(
            "user",
            "department",
        ).get(
            user=self.request.user
        )

        # =====================================================
        # FIND THIS FACULTY'S ACTIVE ADVISOR ASSIGNMENTS
        # =====================================================

        assignments = AdvisorAssignment.objects.filter(
            advisor=faculty,
            is_active=True,
        ).select_related(
            "program",
            "program__department",
        )

        # =====================================================
        # FIND ADVISEES
        #
        # Assignment rule:
        #
        # Program
        # + Admission Batch
        # + Roll Number From
        # + Roll Number To
        # =====================================================

        advisees = []

        for assignment in assignments:

            academic_profiles = (
                StudentAcademicProfile.objects
                .filter(
                    program=assignment.program,
                    student__admission_date__year=assignment.admission_batch,
                )
                .select_related(
                    "student",
                    "student__user",
                    "program",
                )
            )

            roll_from = assignment.roll_number_from.strip().upper()
            roll_to = assignment.roll_number_to.strip().upper()

            for academic_profile in academic_profiles:

                student = academic_profile.student

                student_number = (
                    student.student_number or ""
                ).strip().upper()

                if not student_number:
                    continue

                # Check roll-number range
                if roll_from <= student_number <= roll_to:

                    # Prevent duplicate student
                    if not any(
                        item["student"].pk == student.pk
                        for item in advisees
                    ):
                        advisees.append({
                            "student": student,
                            "academic": academic_profile,
                            "assignment": assignment,
                        })

        # =====================================================
        # SORT STUDENTS
        # =====================================================

        advisees.sort(
            key=lambda item: item["student"].student_number
        )

        # =====================================================
        # BASIC STUDENT LIST
        # =====================================================

        students = [
            item["student"]
            for item in advisees
        ]

        total_advisees = len(students)

        # =====================================================
        # ACTIVE STUDENTS
        # =====================================================

        active_advisees = sum(
            1
            for student in students
            if student.current_status == "ACTIVE"
        )

        # =====================================================
        # ACADEMIC LEVELS
        # =====================================================

        undergraduate_advisees = sum(
            1
            for student in students
            if student.academic_level == "UNDERGRADUATE"
        )

        graduate_advisees = sum(
            1
            for student in students
            if student.academic_level == "GRADUATE"
        )

        phd_advisees = sum(
            1
            for student in students
            if student.academic_level == "PHD"
        )

        # =====================================================
        # GPA
        # =====================================================

        gpas = [
            float(student.cumulative_gpa)
            for student in students
            if student.cumulative_gpa is not None
        ]

        average_gpa = (
            round(sum(gpas) / len(gpas), 2)
            if gpas
            else 0
        )

        # =====================================================
        # ENROLLMENT DATA
        #
        # A student can have multiple enrollment records.
        # We use the latest enrollment record by ID.
        # =====================================================

        enrollment_status_counts = {
            "FULL_TIME": 0,
            "PART_TIME": 0,
            "WITHDRAWN": 0,
            "LEAVE": 0,
        }

        academic_standing_counts = {
            "GOOD_STANDING": 0,
            "DEAN_LIST": 0,
            "HONOR_ROLL": 0,
            "PROBATION": 0,
            "SUSPENSION": 0,
        }

        student_enrollment_data = {}

        for student in students:

            enrollment = (
                StudentEnrollment.objects
                .filter(student=student)
                .order_by("-id")
                .first()
            )

            student_enrollment_data[student.pk] = enrollment

            if not enrollment:
                continue

            if enrollment.enrollment_status:
                if enrollment.enrollment_status in enrollment_status_counts:
                    enrollment_status_counts[
                        enrollment.enrollment_status
                    ] += 1

            if enrollment.academic_standing:
                if enrollment.academic_standing in academic_standing_counts:
                    academic_standing_counts[
                        enrollment.academic_standing
                    ] += 1

        # =====================================================
        # ACADEMIC STANDING PERCENTAGES
        # =====================================================

        standing_total = sum(
            academic_standing_counts.values()
        )

        academic_standing = []

        standing_config = [
            (
                "GOOD_STANDING",
                "Good Standing",
                "pf-green",
            ),
            (
                "DEAN_LIST",
                "Dean's List",
                "pf-blue",
            ),
            (
                "HONOR_ROLL",
                "Honor Roll",
                "pf-purple",
            ),
            (
                "PROBATION",
                "Probation",
                "pf-orange",
            ),
            (
                "SUSPENSION",
                "Suspension",
                "pf-red",
            ),
        ]

        for code, label, css_class in standing_config:

            count = academic_standing_counts[code]

            percentage = (
                round((count / standing_total) * 100)
                if standing_total
                else 0
            )

            academic_standing.append({
                "label": label,
                "count": count,
                "percentage": percentage,
                "css_class": css_class,
            })

        # =====================================================
        # MAJOR DISTRIBUTION
        # =====================================================

        major_counter = Counter()

        for item in advisees:

            major = item["academic"].major

            if major:
                major_counter[major.strip()] += 1

        major_distribution = [
            {
                "name": major,
                "count": count,
            }
            for major, count in major_counter.most_common()
        ]

        # =====================================================
        # EXPECTED GRADUATIONS
        # =====================================================

        graduation_counter = Counter()

        for student in students:

            if student.expected_graduation_date:

                graduation_date = (
                    student.expected_graduation_date
                )

                key = (
                    graduation_date.year,
                    graduation_date.month,
                )

                graduation_counter[key] += 1

        expected_graduations = []

        month_names = {
            1: "JAN",
            2: "FEB",
            3: "MAR",
            4: "APR",
            5: "MAY",
            6: "JUN",
            7: "JUL",
            8: "AUG",
            9: "SEP",
            10: "OCT",
            11: "NOV",
            12: "DEC",
        }

        for (year, month), count in sorted(
            graduation_counter.items()
        ):

            expected_graduations.append({
                "month": month_names[month],
                "year": year,
                "count": count,
            })

        # =====================================================
        # CURRENT ACADEMIC YEAR
        # =====================================================

        current_year = date.today().year

        academic_year = (
            f"{current_year} to {current_year + 1}"
        )

        # =====================================================
        # ADD ENROLLMENT DATA TO ADVISEE OBJECTS
        # =====================================================

        for item in advisees:

            student = item["student"]

            item["enrollment"] = (
                student_enrollment_data.get(
                    student.pk
                )
            )

        # =====================================================
        # CONTEXT
        # =====================================================

        context.update({

            "faculty": faculty,

            "assignments": assignments,

            "advisees": advisees,

            # Stats
            "total_advisees": total_advisees,
            "active_advisees": active_advisees,
            "average_gpa": average_gpa,

            "expected_graduation_count": sum(
                item["count"]
                for item in expected_graduations
                if item["year"] in (
                    current_year,
                    current_year + 1,
                )
            ),

            # Academic levels
            "undergraduate_advisees": undergraduate_advisees,
            "graduate_advisees": graduate_advisees,
            "phd_advisees": phd_advisees,

            # Enrollment
            "full_time_count": enrollment_status_counts[
                "FULL_TIME"
            ],

            "part_time_count": enrollment_status_counts[
                "PART_TIME"
            ],

            "withdrawn_count": enrollment_status_counts[
                "WITHDRAWN"
            ],

            "leave_count": enrollment_status_counts[
                "LEAVE"
            ],

            # Standing
            "academic_standing": academic_standing,

            # Major
            "major_distribution": major_distribution,

            # Graduation
            "expected_graduations": expected_graduations,

            # Academic year
            "academic_year": academic_year,

        })

        return context

def faculty_myprofile(request, uuid):
    return render(request, 'Personal/faculty_myprofile.html')

def faculty_notifications(request, uuid):
    return render(request,'Personal/faculty_notifications.html')

def faculty_settings(request, uuid):
    return render(request,'Personal/faculty_settings.html')

def faculty_advisordashboard(request, uuid):
    return render(request,'StudentAdvising/faculty_advisordashboard.html')
    


# rupa code start *********************************************************************************
def facultybase(request, uuid):
    return render(request, 'faculty_base.html')

from django.contrib.auth.decorators import login_required
from Research.models import ResearchTeamMember


@login_required
def facultydashboard(request, uuid):
    user = request.user
    faculty = user.faculty_profile

    is_research_team_member = ResearchTeamMember.objects.filter(
        faculty=faculty,
        role__in=["ADVISOR", "CO_MENTOR"],
    ).exists()

    context = {
        "uuid": uuid,
        "user": user,
        "is_research_team_member": is_research_team_member,
    }

    return render(
        request,
        "faculty_dashboard.html",
        context
    )

##########################################bela code start############################################
from django.shortcuts import render, get_object_or_404
from django.db.models import Count

from Faculty.models import FacultyProfile, FacultyCourseAssignment
from Students.models import CourseSection, Schedule



def my_courses(request, uuid):

    faculty = get_object_or_404(
        FacultyProfile,
        user=request.user
    )

    search = request.GET.get("q", "").strip()
    selected_semester = request.GET.get("semester")
    section_type = request.GET.get("type")

    assignments = FacultyCourseAssignment.objects.filter(
        faculty=faculty
    )

    section_ids = assignments.values_list(
        "course_section_id",
        flat=True
    )

    sections = (
        CourseSection.objects
        .filter(section_id__in=section_ids)
        .select_related("course", "semester_id")
        .prefetch_related("schedules")
        .annotate(student_count=Count("enrollments"))
    )
    

    # Search
    if search:
        sections = sections.filter(
            Q(course__course_code__icontains=search) |
            Q(course__course_name__icontains=search)
        )

    # Semester
    if selected_semester:
        sections = sections.filter(
            semester_id_id=selected_semester
        )

    # Section Type
    if section_type:
        sections = sections.filter(
            section_type=section_type
        )

    # Dictionary for quick lookup
    section_dict = {
        section.section_id: section
        for section in sections
    }

    course_data = []

    total_students = 0
    weekly_hours = 0

    theory = 0
    lab = 0

    for assignment in assignments:

        section = section_dict.get(
            assignment.course_section_id
        )

        if not section:
            continue

        total_students += section.student_count

        if section.course:
            weekly_hours += section.course.credits

        if section.section_type == "LEC":
            theory += 1

        elif section.section_type == "LAB":
            lab += 1

        capacity_pct = 0

        if section.capacity:
            capacity_pct = round(
                (section.student_count / section.capacity) * 100
            )
        schedule = section.schedules.first()
        course_data.append({
            "assignment": assignment,
            "section": section,
            "schedule": schedule,
            "student_count": section.student_count,
            "capacity_pct": capacity_pct,
        })

    # Pagination
    paginator = Paginator(course_data, 6)   # 6 records per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    total_courses = len(course_data)
    assigned_sections = total_courses

    if total_courses:

        theory_pct = round(
            (theory / total_courses) * 100
        )

        lab_pct = round(
            (lab / total_courses) * 100
        )

    else:

        theory_pct = 0
        lab_pct = 0

    semesters = Semester.objects.order_by(
        "-academic_year",
        "-semester_type"
    )

    context = {

       
        "course_data": page_obj.object_list,
        "page_obj": page_obj,

        "total_courses": total_courses,

        "assigned_sections": assigned_sections,

        "total_students": total_students,

        "weekly_hours": weekly_hours,

        "theory_pct": theory_pct,

        "lab_pct": lab_pct,

        "semesters": semesters,

        "selected_semester_id": selected_semester,
        "selected_type": section_type,
        
    }

    return render(
        request,
        "teaching/my_courses.html",
        context
    )

##########################################bela code end############################################
def course_schedule(request, uuid):
    return render(request, 'teaching/course_schedule.html')


###########################  Rixie code start ###########################
def _class_roster_data(request):
    faculty = get_object_or_404(FacultyProfile, user=request.user)

    assignments = FacultyCourseAssignment.objects.filter(
        faculty=faculty
    ).order_by("-id")

    section_ids = assignments.values_list("course_section_id", flat=True)

    sections = (
        CourseSection.objects
        .filter(section_id__in=section_ids)
        .select_related("course", "semester_id")
        .annotate(student_count=Count("enrollments"))
    )

    section_dict = {
        section.section_id: section
        for section in sections
    }

    # ----- students enrolled in the faculty's sections -----
    enrollments = (
        StudentEnrollment.objects
        .filter(section_id__in=section_ids)
        .select_related(
            "student",
            "student__user",
            "section_id",
            "section_id__course",
        )
        .order_by("-id")
    )

    total_students = enrollments.count()

    student_list = []
    for enrollment in enrollments:
        student = enrollment.student
        user = student.user
        name = (
            f"{user.first_name or ''} {user.last_name or ''}".strip()
            or student.preferred_name
            or student.student_number
        )
        initials = "".join(
            part[0].upper() for part in name.split()[:2]
        ) or "S"

        section = enrollment.section_id

        student_list.append({
            "name": name,
            "initials": initials,
            "student_number": student.student_number,
            "course_code": section.course.course_code if section.course else "-",
            "section_number": section.section_number,
            "status": (student.current_status or "ACTIVE").title(),
        })

    # ----- student filter -----
    student_search = request.GET.get("sq", "").strip()
    student_status = request.GET.get("sstatus", "").strip()

    if student_search:
        student_search_lower = student_search.lower()
        student_list = [
            s for s in student_list
            if (student_search_lower in s["name"].lower()
                or student_search_lower in s["student_number"].lower()
                or student_search_lower in s["course_code"].lower()
                or student_search_lower in str(s["section_number"]))
        ]

    if student_status:
        student_list = [
            s for s in student_list
            if s["status"].lower() == student_status.lower()
        ]

    # ----- student pagination -----
    student_paginator = Paginator(student_list, 6)   # 6 records per page
    student_page_number = request.GET.get("spage")
    student_page_obj = student_paginator.get_page(student_page_number)

    # ----- courses assigned to the faculty -----
    course_data = []
    for assignment in assignments:
        section = section_dict.get(assignment.course_section_id)
        if not section:
            continue
        course_data.append({
            "assignment": assignment,
            "section": section,
            "student_count": section.student_count,
        })

    # ----- course filter -----
    course_search = request.GET.get("cq", "").strip()
    course_type = request.GET.get("ctype", "").strip()

    if course_search:
        course_search_lower = course_search.lower()
        course_data = [
            c for c in course_data
            if (course_search_lower in c["section"].course.course_code.lower()
                or course_search_lower in c["section"].course.course_name.lower()
                or course_search_lower in str(c["section"].section_number))
        ]

    if course_type:
        course_data = [
            c for c in course_data
            if c["section"].section_type == course_type
        ]

    # ----- course pagination -----
    course_paginator = Paginator(course_data, 4)   # 4 records per page
    course_page_number = request.GET.get("cpage")
    course_page_obj = course_paginator.get_page(course_page_number)

    total_courses = len(course_data)

    # ----- recent activity -----
    recent_activities = []
    for enrollment in enrollments[:5]:
        section = enrollment.section_id
        code = section.course.course_code if section.course else "Course"
        name = (
            f"{enrollment.student.user.first_name or ''} "
            f"{enrollment.student.user.last_name or ''}".strip()
            or enrollment.student.preferred_name
            or enrollment.student.student_number
        )
        recent_activities.append({
            "dot_class": "green",
            "text": f"{name} enrolled in {code} Sec {section.section_number}",
        })

    for assignment in assignments[:3]:
        section = section_dict.get(assignment.course_section_id)
        if section and section.course:
            recent_activities.append({
                "dot_class": "blue",
                "text": (
                    f"Assigned as {assignment.get_role_display()} "
                    f"for {section.course.course_code}"
                ),
            })

    return {
        "student_list": student_page_obj.object_list,
        "student_page_obj": student_page_obj,
        "total_students": total_students,
        "student_statuses": ["ACTIVE", "LEAVE", "GRADUATED", "WITHDRAWN"],
        "selected_student_status": student_status,
        "student_search": student_search,
        "course_data": course_page_obj.object_list,
        "course_page_obj": course_page_obj,
        "total_courses": total_courses,
        "section_types": [
            ("LEC", "Lecture"),
            ("LAB", "Lab"),
            ("TUT", "Tutorial"),
            ("SEM", "Seminar"),
            ("DIS", "Discussion"),
        ],
        "selected_course_type": course_type,
        "course_search": course_search,
        "recent_activities": recent_activities,
    }


def class_roster(request, uuid):
    context = _class_roster_data(request)
    return render(request, 'teaching/class_roster.html', context)


def _serialize_student(student):
    return {
        "name": student["name"],
        "initials": student["initials"],
        "student_number": student["student_number"],
        "course_code": student["course_code"],
        "section_number": student["section_number"],
        "status": student["status"],
    }


def _serialize_course(course):
    section = course["section"]
    return {
        "code": section.course.course_code if section.course else "-",
        "course_name": section.course.course_name if section.course else "",
        "section_type_letter": section.section_type[:1],
        "section_number": section.section_number,
        "section_type_display": section.get_section_type_display(),
        "semester_id": str(section.semester_id),
        "student_count": section.student_count,
        "capacity": section.capacity,
        "role": course["assignment"].get_role_display(),
    }


def _serialize_page(page_obj, serializer):
    return {
        "items": [serializer(item) for item in page_obj.object_list],
        "page": page_obj.number,
        "num_pages": page_obj.paginator.num_pages,
        "count": page_obj.paginator.count,
        "start_index": page_obj.start_index(),
        "end_index": page_obj.end_index(),
        "has_previous": page_obj.has_previous(),
        "has_next": page_obj.has_next(),
        "previous_page_number": (
            page_obj.previous_page_number() if page_obj.has_previous() else None
        ),
        "next_page_number": (
            page_obj.next_page_number() if page_obj.has_next() else None
        ),
        "page_range": list(page_obj.paginator.page_range),
    }


def class_roster_ajax(request, uuid):
    context = _class_roster_data(request)
    return JsonResponse({
        "success": True,
        "students": _serialize_page(context["student_page_obj"], _serialize_student),
        "courses": _serialize_page(context["course_page_obj"], _serialize_course),
    })
###########################  Rixie code end ###########################



def _serialize_student(student):
    return {
        "name": student["name"],
        "initials": student["initials"],
        "student_number": student["student_number"],
        "course_code": student["course_code"],
        "section_number": student["section_number"],
        "status": student["status"],
    }


def _serialize_course(course):
    section = course["section"]
    return {
        "code": section.course.course_code if section.course else "-",
        "course_name": section.course.course_name if section.course else "",
        "section_type_letter": section.section_type[:1],
        "section_number": section.section_number,
        "section_type_display": section.get_section_type_display(),
        "semester_id": str(section.semester_id),
        "student_count": section.student_count,
        "capacity": section.capacity,
        "role": course["assignment"].get_role_display(),
    }


def _serialize_page(page_obj, serializer):
    return {
        "items": [serializer(item) for item in page_obj.object_list],
        "page": page_obj.number,
        "num_pages": page_obj.paginator.num_pages,
        "count": page_obj.paginator.count,
        "start_index": page_obj.start_index(),
        "end_index": page_obj.end_index(),
        "has_previous": page_obj.has_previous(),
        "has_next": page_obj.has_next(),
        "previous_page_number": (
            page_obj.previous_page_number() if page_obj.has_previous() else None
        ),
        "next_page_number": (
            page_obj.next_page_number() if page_obj.has_next() else None
        ),
        "page_range": list(page_obj.paginator.page_range),
    }


def class_roster_ajax(request, uuid):
    context = _class_roster_data(request)
    return JsonResponse({
        "success": True,
        "students": _serialize_page(context["student_page_obj"], _serialize_student),
        "courses": _serialize_page(context["course_page_obj"], _serialize_course),
    })
###########################  Rixie code end ###########################

def assignments(request, uuid):
    return render(request, 'teaching/assignments.html')

def library(request):
    return render(request, 'resources/library.html')

def academic_resources(request):
    return render(request, 'resources/academic_resources.html')


# faculty dashboard ***************************************************************************

from django.views.generic import TemplateView
from Faculty.models import (
    FacultyProfile,
    FacultyCourseAssignment,
)
from Students.models import *

import json
from datetime import date, timedelta

# def facultydashboard(request, uuid):
#     user = request.user
#     context = {
#         'uuid' : uuid,
#         'user' : user,
#     }
#     return render(request, 'faculty_dashboard.html', context)

class FacultyDashboardView(TemplateView):
    template_name = "faculty_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # AUTO-CREATE PROFILE IF IT DOESN'T EXIST
        faculty, created = FacultyProfile.objects.get_or_create(
            user=self.request.user,
            defaults={
                'employee_id': f"FAC{date.today().year}{FacultyProfile.objects.count() + 1:03d}",
                'email': self.request.user.email,
                'hire_date': date.today(),
                'employment_status': 'ACTIVE',
                'preferred_name': self.request.user.get_full_name() or self.request.user.username,
            }
        )
        
        if created:
            # Optional: Add a message to inform the user
            from django.contrib import messages
            messages.info(self.request, "Your faculty profile has been created automatically.")
        
        context["uuid"] = kwargs.get("uuid")
        context["faculty"] = faculty

        # Now proceed with your existing code
        assignments = FacultyCourseAssignment.objects.filter(faculty=faculty)
        section_ids = assignments.values_list("course_section_id", flat=True)

        sections = (
            CourseSection.objects
            .filter(section_id__in=section_ids)
            .select_related("course")
            .annotate(student_count=Count("enrollments"))
        )

        today = date.today()
        today_str = today.isoformat()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=5)  # Mon–Sat

        schedules = list(
            Schedule.objects.filter(section_id__in=section_ids)
            .select_related("section_id__course")
        )

        # ---------- Today's Teaching Schedule ----------
        today_schedules = sorted(
            (s for s in schedules if today_str in (s.dates or [])),
            key=lambda s: s.start_time,
        )

        # ---------- Classes This Week ----------
        classes_this_week = 0
        for s in schedules:
            occ_dates = _parse_schedule_dates(s.dates)
            classes_this_week += sum(1 for d in occ_dates if week_start <= d <= week_end)

        # ---------- Course Overview donut ----------
        color_cycle = ["red", "blue", "green", "purple", "orange"]
        course_overview = []
        total_enrolled = 0
        for i, section in enumerate(sections):
            count = section.student_count
            total_enrolled += count
            course_overview.append({
                "course_code": section.course.course_code if section.course else "N/A",
                "student_count": count,
                "color": color_cycle[i % len(color_cycle)],
            })

        # ---------- My Advising ----------
        advisees_qs = StudentAcademicProfile.objects.filter(advisor_id=faculty.id)
        total_advisees = advisees_qs.count()
        new_advisees = 0
        if hasattr(StudentAcademicProfile, "created_at"):
            new_advisees = advisees_qs.filter(
                created_at__gte=today - timedelta(days=90)
            ).count()

        avg_feedback = 0
        if hasattr(faculty, "evaluations"):
            evals = faculty.evaluations.all()
            ratings = [e.rating for e in evals if hasattr(e, "rating") and e.rating is not None]
            if ratings:
                avg_feedback = round(sum(ratings) / len(ratings), 1)

        context.update({
            "faculty": faculty,
            "total_courses": assignments.count(),
            "total_students": StudentEnrollment.objects.filter(section_id__in=section_ids).count(),
            "advisee_count": total_advisees,
            "office_hours_count": faculty.office_hours.count(),

            "today_schedules": today_schedules,
            "total_classes": classes_this_week,

            "course_overview": course_overview,
            "total_enrolled": total_enrolled,
            "course_overview_json": json.dumps(course_overview),

            "total_advisees": total_advisees,
            "new_advisees": new_advisees,
            "avg_feedback": avg_feedback,

            "assignments_to_grade": 0,
            "grade_distribution": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
            "upcoming_deadlines": [],
            "recent_activity": [],
        })

        return context
     

# my courses ****************************************************************************************

# def my_courses(request, uuid):
#     faculty = FacultyProfile.objects.get(user=request.user)
#     assignments = FacultyCourseAssignment.objects.filter(faculty=faculty)

#     total_students = 0
#     course_data = []

#     for assignment in assignments:
#         # Count students directly using the integer value
#         student_count = StudentEnrollment.objects.filter(
#             section_id=assignment.course_section_id
#         ).count()

#         total_students += student_count

#         course_data.append({
#             "assignment": assignment,
#             "student_count": student_count,
#         })

#     context = {
#         "faculty": faculty,
#         "course_data": course_data,
#         "total_courses": assignments.count(),
#         "total_students": total_students,
#     }

#     return render(request, "teaching/my_courses.html", context)

# course schedule **************************************************************************************
import calendar
from datetime import date, datetime, timedelta

from django.shortcuts import render


def _parse_schedule_dates(raw_dates):
    """Schedule.dates is stored as a list of ISO date strings (e.g. '2026-08-03').
    Safely turn that into a list of real date objects, skipping anything malformed."""
    parsed = []
    for d in raw_dates or []:
        if isinstance(d, date):
            parsed.append(d)
            continue
        try:
            parsed.append(datetime.strptime(str(d), "%Y-%m-%d").date())
        except (ValueError, TypeError):
            continue
    return parsed

import calendar
from datetime import date, datetime, timedelta

from django.shortcuts import render


def _parse_schedule_dates(raw_dates):
    """Schedule.dates is stored as a list of ISO date strings (e.g. '2026-08-03').
    Safely turn that into a list of real date objects, skipping anything malformed."""
    parsed = []
    for d in raw_dates or []:
        if isinstance(d, date):
            parsed.append(d)
            continue
        try:
            parsed.append(datetime.strptime(str(d), "%Y-%m-%d").date())
        except (ValueError, TypeError):
            continue
    return parsed


def course_schedule(request, uuid):

    faculty = FacultyProfile.objects.get(user=request.user)
    assignments = FacultyCourseAssignment.objects.filter(faculty=faculty)
    section_ids = assignments.values_list("course_section_id", flat=True)

    # Pulled once into a list — we loop over this several times below
    # (today/next/upcoming, weekly grid, monthly grid) and don't want to
    # hit the DB again for each pass.
    schedules = list(
        Schedule.objects.filter(section_id__in=section_ids)
        .select_related('section_id__course')
    )

    today = date.today()
    current_time = datetime.now().time()

    # ---------- view mode + reference date (drives Prev/Next) ----------
    view_mode = request.GET.get('view', 'weekly')
    if view_mode not in ('weekly', 'monthly'):
        view_mode = 'weekly'

    ref_param = request.GET.get('date')
    if ref_param:
        try:
            ref_date = datetime.strptime(ref_param, "%Y-%m-%d").date()
        except ValueError:
            ref_date = today
    else:
        ref_date = today

    # ---------- per-course accent color (stable regardless of iteration order) ----------
    color_palette = ["red", "orange", "blue", "green", "purple"]
    course_codes_sorted = sorted({
        s.section_id.course.course_code for s in schedules if s.section_id.course
    })
    course_colors = {
        code: color_palette[i % len(color_palette)]
        for i, code in enumerate(course_codes_sorted)
    }

    # ---------- Today's Classes / Next Class / Upcoming Classes ----------
    # Uses the real `dates` list now, not just day_of_week, so a class that
    # was skipped/cancelled for a given week correctly disappears here.
    today_str = today.isoformat()

    todays_schedules = [
        s for s in schedules if today_str in (s.dates or [])
    ]
    todays_schedules.sort(key=lambda s: s.start_time)

    today_classes = []
    for s in todays_schedules[:3]:
        if current_time < s.start_time:
            status, status_class = "Upcoming", "upcoming"
        elif s.start_time <= current_time <= s.end_time:
            status, status_class = "Ongoing", "ongoing"
        else:
            status, status_class = "Completed", "completed"

        today_classes.append({
            "course_code": s.section_id.course.course_code,
            "course_name": s.section_id.course.course_name,
            "section": s.section_id.section_number,
            "building": s.building,
            "room": s.room,
            "start_time": s.start_time.strftime("%I:%M %p"),
            "end_time": s.end_time.strftime("%I:%M %p"),
            "is_online": s.is_online,
            "status": status,
            "status_class": status_class,
        })

    next_class = None
    for s in todays_schedules:
        if s.end_time <= current_time:
            continue
        next_class = {
            "course_code": s.section_id.course.course_code,
            "course_name": s.section_id.course.course_name,
            "section": s.section_id.section_number,
            "building": s.building,
            "room": s.room,
            "start_time": s.start_time.strftime("%I:%M %p"),
            "end_time": s.end_time.strftime("%I:%M %p"),
            "is_online": s.is_online,
            "status": "Ongoing" if s.start_time <= current_time <= s.end_time else "Upcoming",
        }
        break

    # Next 3 real upcoming occurrences (by actual date), across all schedules
    future_occurrences = []
    for s in schedules:
        for d in _parse_schedule_dates(s.dates):
            if d > today:
                future_occurrences.append((d, s))
    future_occurrences.sort(key=lambda pair: (pair[0], pair[1].start_time))

    upcoming_classes = []
    for d, s in future_occurrences[:3]:
        upcoming_classes.append({
            "course_code": s.section_id.course.course_code,
            "course_name": s.section_id.course.course_name,
            "date": d.strftime("%b %d"),
            "day": s.get_day_of_week_display(),
            "start_time": s.start_time.strftime("%I:%M %p"),
            "end_time": s.end_time.strftime("%I:%M %p"),
            "building": s.building,
            "room": s.room,
            "section": s.section_id.section_number,
            "is_online": s.is_online,
        })

    # ---------- Stats cards ----------
    total_rooms = len({s.room for s in schedules if s.room})
    total_weekly_classes = len(schedules)

    total_minutes = 0
    for s in schedules:
        start = datetime.combine(today, s.start_time)
        end = datetime.combine(today, s.end_time)
        total_minutes += (end - start).seconds // 60
    teaching_hours = round(total_minutes / 60, 1)

    days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']

    timetable = {}
    time_labels = {}
    week_dates = {}
    calendar_weeks = []
    period_label = ""
    prev_ref = ref_date
    next_ref = ref_date

    if view_mode == 'weekly':
        # Monday..Saturday containing ref_date
        week_start = ref_date - timedelta(days=ref_date.weekday())
        week_end = week_start + timedelta(days=5)
        week_dates = {days[i]: week_start + timedelta(days=i) for i in range(6)}

        for s in schedules:
            occ_dates = _parse_schedule_dates(s.dates)
            if not any(week_start <= d <= week_end for d in occ_dates):
                continue

            time_key = f"{s.start_time.strftime('%I:%M %p')} - {s.end_time.strftime('%I:%M %p')}"
            day = s.day_of_week

            if time_key not in timetable:
                timetable[time_key] = {}
                start_label = s.start_time.strftime("%I:%M %p").lstrip("0")
                end_label = s.end_time.strftime("%I:%M %p").lstrip("0")
                time_labels[time_key] = f"{start_label} - {end_label}"

            timetable[time_key][day] = {
                "course_code": s.section_id.course.course_code,
                "course_name": s.section_id.course.course_name,
                "section": s.section_id.section_number,
                "room": s.room,
                "building": s.building,
                "color": course_colors.get(s.section_id.course.course_code, "red"),
            }

        prev_ref = week_start - timedelta(days=7)
        next_ref = week_start + timedelta(days=7)
        period_label = (
            f"{week_start.strftime('%b')} {week_start.day} - "
            f"{week_end.strftime('%b')} {week_end.day}, {week_end.year}"
        )

    else:
        # Monthly: build a full calendar grid (Mon-first), including the
        # leading/trailing days from adjacent months needed to fill each week.
        classes_by_date = {}
        for s in schedules:
            for d in _parse_schedule_dates(s.dates):
                if d.year == ref_date.year and d.month == ref_date.month:
                    classes_by_date.setdefault(d, []).append({
                            "course_code": s.section_id.course.course_code,
                            "course_name": s.section_id.course.course_name,
                            "start_time": s.start_time.strftime("%I:%M %p").lstrip("0"),
                            "building": s.building,
                            "room": s.room,
                            "color": course_colors.get(
                                s.section_id.course.course_code,
                                "red"
                            ),
                        })

        for d in classes_by_date:
            classes_by_date[d].sort(key=lambda c: c["start_time"])

        cal = calendar.Calendar(firstweekday=0)  # Monday first
        week = []
        for d in cal.itermonthdates(ref_date.year, ref_date.month):
            week.append({
                "date": d,
                "day_num": d.day,
                "in_month": d.month == ref_date.month,
                "is_today": d == today,
                "classes": classes_by_date.get(d, []),
            })
            if len(week) == 7:
                calendar_weeks.append(week)
                week = []

        first_of_month = ref_date.replace(day=1)
        prev_ref = (first_of_month - timedelta(days=1)).replace(day=1)
        days_in_month = calendar.monthrange(ref_date.year, ref_date.month)[1]
        next_ref = (first_of_month + timedelta(days=days_in_month))
        period_label = ref_date.strftime("%B %Y")

    context = {
        "faculty": faculty,
        "total_courses": assignments.count(),
        "total_weekly_classes": total_weekly_classes,
        "teaching_hours": teaching_hours,
        "total_rooms": total_rooms,
        "next_class": next_class,
        "today_classes": today_classes,
        "upcoming_classes": upcoming_classes,
        "timetable": timetable,
        "time_labels": time_labels,
        "week_dates": week_dates,
        "calendar_weeks": calendar_weeks,
        "days": days,
        "view_mode": view_mode,
        "ref_date": ref_date.isoformat(),
        "prev_ref": prev_ref.isoformat(),
        "next_ref": next_ref.isoformat(),
        "period_label": period_label,
        "today": today,
    }

    return render(request, "teaching/course_schedule.html", context)

# library *****************************************************************************************************

from django.views.generic import TemplateView
from Library.models import (
    LibraryResource,
    BorrowTransaction
)
from django.db.models import Count


class LibraryDashboardView(TemplateView):  
    template_name = "resources/library.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Stats
        context["total_books"] = LibraryResource.objects.count()

        context["issued_books"] = BorrowTransaction.objects.filter(
            status="ISSUED"
        ).count()

        context["overdue_books"] = BorrowTransaction.objects.filter(
            status="OVERDUE"
        ).count()

        context["returned_books"] = BorrowTransaction.objects.filter(
            status="RETURNED"
        ).count()

        # Recent Transactions
        context["recent_transactions"] = BorrowTransaction.objects.select_related(
            "copy__resource",
            "library_user__user"
        ).order_by("-issue_date")[:10]

        context["categories"] = (
            LibraryResource.objects
            .values("subject")
            .annotate(total=Count("id"))
            .order_by("-total")[:5]
        )

        return context

# rupa code ends****************************************************************************




# navina
def faculty_myprofile(request, uuid):

    profile = get_object_or_404(
        FacultyProfile,
        user__uuid=uuid
    )

    context = {
        "profile": profile,
    }

    return render(
        request,
        "Personal/faculty_myprofile.html",
        context
    )
 
def faculty_notifications(request, uuid):
    return render(request,'Personal/faculty_notifications.html')
 
def faculty_settings(request, uuid):
    return render(request,'Personal/faculty_settings.html')
# navina code ends



# ************************************************ Arun Code ********************************************************


def generate_faculty_employee_id(hire_year: int) -> str:
    prefix = f"FAC{hire_year}"
 
    existing = (
        FacultyProfile.objects
        .filter(employee_id__startswith=prefix)
        .values_list("employee_id", flat=True)
    )
 
    max_seq = 0
    pattern = re.compile(rf"^{prefix}(\d+)$")
    for emp_id in existing:
        m = pattern.match(emp_id)
        if m:
            seq = int(m.group(1))
            if seq > max_seq:
                max_seq = seq
 
    return f"{prefix}{max_seq + 1:03d}"
 
 
def suggested_faculty_id_for_context(hire_date_str=None):
    year = date.today().year
    if hire_date_str:
        try:
            year = int(hire_date_str[:4])
        except (ValueError, TypeError):
            pass
    return generate_faculty_employee_id(year)
 
 
@login_required
@require_http_methods(["GET"])
def next_faculty_id_json(request):
    year_param = request.GET.get("year", "").strip()
    try:
        year = int(year_param) if year_param else date.today().year
    except ValueError:
        year = date.today().year
    return JsonResponse({"employee_id": generate_faculty_employee_id(year)})
 
def save_faculty_details(request, user):
    post = request.POST
    files = request.FILES
 
    hire_date = post.get("faculty_hire_date") or None
 
    employee_id = (post.get("faculty_employee_id") or "").strip()
    if not employee_id:
        year = date.today().year
        if hire_date:
            try:
                year = int(hire_date[:4])
            except ValueError:
                pass
        employee_id = generate_faculty_employee_id(year)

    faculty_rank_obj = None
    rank_value = post.get("faculty_rank")
    if rank_value:
        try:
            faculty_rank_obj = FacultyRank.objects.get(id=rank_value)
        except (FacultyRank.DoesNotExist, ValueError):
            faculty_rank_obj = None
 
    with transaction.atomic():
        profile = FacultyProfile.objects.create(
            user=user,
            employee_id=employee_id,
            preferred_name=post.get("faculty_preferred_name", ""),
            email=post.get("faculty_email") or user.email,
            phone=post.get("faculty_phone", ""),
            office_location=post.get("faculty_office_location", ""),
            biography=post.get("faculty_biography", ""),
            hire_date=hire_date,
            employment_status=post.get("faculty_employment_status") or "ACTIVE",
            faculty_rank=faculty_rank_obj,
            department_id=post.get("faculty_department_id") or None,
        )
 
        # if post.get("faculty_appointment_type"):
        #     FacultyAppointment.objects.create(
        #         faculty=profile,
        #         department_id=post.get("faculty_appt_department_id") or 0,
        #         appointment_type=post.get("faculty_appointment_type"),
        #         start_date=post.get("faculty_appt_start_date") or date.today(),
        #         end_date=post.get("faculty_appt_end_date") or None,
        #         percentage_effort=post.get("faculty_percentage_effort") or None,
        #     )

        if post.get("faculty_degree"):
            FacultyEducation.objects.create(
                faculty=profile,
                degree=post.get("faculty_degree", ""),
                field_of_study=post.get("faculty_field_of_study", ""),
                institution_name=post.get("faculty_institution_name", ""),
                graduation_year=post.get("faculty_graduation_year") or None,
            )

        days = post.getlist("faculty_oh_day[]")
        locations = post.getlist("faculty_oh_location[]")
        starts = post.getlist("faculty_oh_start[]")
        ends = post.getlist("faculty_oh_end[]")
 
        for i in range(len(days)):
            day = days[i] if i < len(days) else ""
            if not day:
                continue  
            # FacultyOfficeHours.objects.create(
            #     faculty=profile,
            #     day_of_week=day,
            #     start_time=starts[i] if i < len(starts) and starts[i] else "09:00",
            #     end_time=ends[i] if i < len(ends) and ends[i] else "10:00",
            #     location=locations[i] if i < len(locations) else "",
            # )
 
        doc_types = post.getlist("faculty_doc_type[]")
        doc_names = post.getlist("faculty_doc_name[]")
        doc_files = files.getlist("faculty_doc_file[]")
 
        for i in range(max(len(doc_types), len(doc_names), len(doc_files))):
            doc_file = doc_files[i] if i < len(doc_files) else None
            if not doc_file:
                continue
            doc_type = doc_types[i] if i < len(doc_types) else ""
            doc_name = doc_names[i] if i < len(doc_names) else ""
            FacultyDocument.objects.create(
                faculty=profile,
                document_type=doc_type or "OTHER",
                file_name=doc_name or doc_file.name,
                file=doc_file,
                verification_status="PENDING",
            )
 
    return profile



from django.contrib import messages
from Students.models import SupportTicket, CourseSection
from Staff.utils import notify_staff_new_ticket


@login_required
def faculty_submit_ticket(request, uuid):
    faculty = get_object_or_404(FacultyProfile, user__uuid=uuid)

    if request.method == "POST":
        section_id = request.POST.get("course_section")
        subject = request.POST.get("subject", "").strip()
        description = request.POST.get("description", "").strip()
        priority = request.POST.get("priority", "MEDIUM")

        if not subject:
            messages.error(request, "Subject is required.")
            return redirect("faculty_submit_ticket", uuid=uuid)

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
        # ==========================================
        # AUDIT: AFTER DATA
        # ==========================================
        after_data = AuditLogger.model_to_dict(
            ticket,
            fields=[
                "subject",
                "description",
                "priority",
                "status",
                "course_section",
            ]
        )
        # ==========================================
        # AUDIT LOG: CREATE
        # ==========================================
        AuditLogger.log(
            request=request,
            action="CREATE",
            module="Faculty",
            object_type="Support Ticket",
            object_id=ticket.id,
            description=(
                f'Faculty created support ticket '
                f'#{ticket.id} with subject '
                f'"{ticket.subject}".'
            ),
            before_data=None,
            after_data=after_data,
            status="SUCCESS",
        )
        notify_staff_new_ticket(ticket)

        messages.success(request, "Ticket submitted successfully.")
        return redirect("faculty_my_tickets", uuid=uuid)

    assigned_section_ids = FacultyCourseAssignment.objects.filter(
        faculty=faculty
    ).values_list("course_section_id", flat=True)

    sections = CourseSection.objects.filter(
        section_id__in=assigned_section_ids
    ).select_related("course")

    context = {
        "sections": sections,
        "priority_choices": SupportTicket.PRIORITY_CHOICES,
    }
    return render(request, "teaching/submit_ticket.html", context)


@login_required
def faculty_my_tickets(request, uuid):
    tickets = SupportTicket.objects.filter(
        submitted_by=request.user
    ).select_related("course_section__course").order_by("-created_at")

    paginator = Paginator(tickets, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "teaching/my_tickets.html", {
        "tickets": page_obj,
        "priority_choices": SupportTicket.PRIORITY_CHOICES,
    })


from django.http import JsonResponse
import json


@login_required
def faculty_ticket_detail(request, uuid, ticket_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    ticket = get_object_or_404(SupportTicket, id=ticket_id, submitted_by=request.user)

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
            "course": "General",
        }
    })


@login_required
def faculty_update_ticket(request, uuid, ticket_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid method"}, status=405)

    ticket = get_object_or_404(SupportTicket, id=ticket_id, submitted_by=request.user)

    if ticket.status != "OPEN":
        return JsonResponse({"success": False, "error": "This ticket can no longer be edited."}, status=400)
    # ==========================================
    # AUDIT: BEFORE DATA
    # ==========================================
    before_data = AuditLogger.model_to_dict(
        ticket,
        fields=[
            "subject",
            "description",
            "priority",
            "status",
            "course_section",
        ]
    )

    payload = json.loads(request.body)
    subject = payload.get("subject", "").strip()

    if not subject:
        return JsonResponse({"success": False, "error": "Subject is required."}, status=400)

    ticket.subject = subject
    ticket.description = payload.get("description", "").strip()
    ticket.priority = payload.get("priority", ticket.priority)
    ticket.save()
    # ==========================================
    # AUDIT: AFTER DATA
    # ==========================================
    after_data = AuditLogger.model_to_dict(
        ticket,
        fields=[
            "subject",
            "description",
            "priority",
            "status",
            "course_section",
        ]
    )
    # ==========================================
    # AUDIT LOG: UPDATE
    # ==========================================
    AuditLogger.log(
        request=request,
        action="UPDATE",
        module="Faculty",
        object_type="Support Ticket",
        object_id=ticket.id,
        description=(
            f'Faculty updated support ticket '
            f'#{ticket.id} with subject '
            f'"{ticket.subject}".'
        ),
        before_data=before_data,
        after_data=after_data,
        status="SUCCESS",
    )
    return JsonResponse({"success": True})


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

#############   kali code start ##################

 

from Admin.models import Tournament, TournamentInvitation, TournamentParticipant, TournamentApplication
from django.contrib import messages
from django.template.loader import render_to_string
from Admin.Jack.models import Coach, SportTeamModel
from Admin.Colleges.models import School


@login_required
def faculty_tournament_track_filter(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    faculty = get_object_or_404(FacultyProfile, user__uuid=uuid)

    valid_statuses = {"INVITED", "APPLIED", "APPROVED", "REJECTED"}
    status = request.GET.get("status", "INVITED").upper()
    if status not in valid_statuses:
        status = "INVITED"

    invitations_qs = TournamentInvitation.objects.select_related(
        "tournament",
        "tournament__sport",
    ).filter(
        receiver_faculty=faculty,
        application_status=status,
    ).order_by("-invitation_sent_at")

    page_obj = Paginator(invitations_qs, 5).get_page(request.GET.get("page", 1))

  

    coaches_qs = Coach.objects.filter(
        is_active=True
    ).order_by("staff_id")

    staff_ids = list(
        coaches_qs.values_list("staff_id", flat=True)
    )

    staff_map = {
        staff.employee_id: staff
        for staff in StaffProfile.objects.select_related("user").filter(
            employee_id__in=staff_ids
        )
    }

    coaches = []

    for coach in coaches_qs:

        staff = staff_map.get(coach.staff_id)

        if not staff:
            continue

        coaches.append({
            "coach_id": coach.coach_id,
            "staff_id": coach.staff_id,
            "full_name": staff.user.full_name or "",
            "role": coach.get_role_display(),
        })

    internal_teams = SportTeamModel.objects.filter(
        status=True
    ).select_related(
        "sport_type"
    ).order_by("team_name")

    colleges = School.objects.filter(status="ACTIVE").order_by("school_name")

    html = render_to_string(
        "teaching/tt_invitation_cards.html",
        {
            "invitations": page_obj.object_list,
            "page_obj": page_obj,
            "today": timezone.localdate(),
            "coaches": coaches,
            "internal_teams": internal_teams,
            "colleges": colleges,
        },
        request=request,
    )

    return JsonResponse({
        "success": True,
        "html": html,
        "status": status,
        "current_page": page_obj.number,
        "total_pages": page_obj.paginator.num_pages,
    })


@login_required
def faculty_tournament_tracking(request, uuid, invitation_uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")

    faculty = get_object_or_404(FacultyProfile, user__uuid=uuid)

    
    active_invitation = get_object_or_404(
        TournamentInvitation,
        invitation_uuid=invitation_uuid,
        receiver_faculty=faculty, 
    )


    
    all_invitations = TournamentInvitation.objects.select_related(
        "tournament",
        "tournament__sport",
    ).filter(receiver_faculty=faculty)

    stats = {
        "total": all_invitations.count(),
        "invited": all_invitations.filter(application_status="INVITED").count(),
        "applied": all_invitations.filter(application_status="APPLIED").count(),
        "approved": all_invitations.filter(application_status="APPROVED").count(),
        "rejected": all_invitations.filter(application_status="REJECTED").count(),
    }

    
    initial_status = active_invitation.application_status

    initial_qs = all_invitations.filter(
        application_status=initial_status
    ).order_by("-invitation_sent_at")



    coaches_qs = Coach.objects.filter(
        is_active=True
    ).order_by("staff_id")

    staff_ids = list(
        coaches_qs.values_list("staff_id", flat=True)
    )

    staff_map = {
        staff.employee_id: staff
        for staff in StaffProfile.objects.select_related("user").filter(
            employee_id__in=staff_ids
        )
    }

    coaches = []

    for coach in coaches_qs:

        staff = staff_map.get(coach.staff_id)

        if not staff:
            continue

        coaches.append({
            "coach_id": coach.coach_id,
            "staff_id": coach.staff_id,
            "full_name": staff.user.full_name or "",
            "role": coach.get_role_display(),
        })

    internal_teams = SportTeamModel.objects.filter(
        status=True
    ).select_related(
        "sport_type"
    ).order_by("team_name")

    colleges = School.objects.filter(status="ACTIVE").order_by("school_name")

    page_obj = Paginator(initial_qs, 5).get_page(1)


    context = {
        "invitations": page_obj.object_list,
        "page_obj": page_obj,
        "stats": stats,
        "active_invitation_uuid": str(active_invitation.invitation_uuid),
        "initial_status": initial_status,
        "today": timezone.localdate(),
        "coaches": coaches,
        "internal_teams": internal_teams,
        "colleges": colleges,
    }

    return render(request, "teaching/tournament_track.html", context)

from django.urls import reverse
from Admin.models import Notification as DashboardNotification
from Admin.ws_utils import broadcast_invitation_status

@login_required
@require_http_methods(["POST"])
def faculty_tournament_application_submit(
    request,
    uuid,
    invitation_uuid
):

    if str(request.user.uuid) != str(uuid):
        return JsonResponse(
            {
                "success": False,
                "error": "Unauthorized"
            },
            status=403
        )

    invitation = get_object_or_404(
        TournamentInvitation.objects.select_related("tournament"),
        invitation_uuid=invitation_uuid,
        receiver_faculty__user=request.user,
    )

    tournament = invitation.tournament


   
    if invitation.application_status != "INVITED":
        return JsonResponse(
            {
                "success": False,
                "error": "This invitation is no longer open for application."
            },
            status=400
        )


    if (
        tournament.registration_deadline
        and tournament.registration_deadline < timezone.localdate()
    ):
        return JsonResponse(
            {
                "success": False,
                "error": "Registration deadline has passed."
            },
            status=400
        )


 

    entry_name = (
        request.POST.get("entry_name") or ""
    ).strip()

    contact_person = (
        request.POST.get("contact_person") or ""
    ).strip()

    contact_mobile = (
        request.POST.get("contact_mobile") or ""
    ).strip()

    if contact_person and re.search(r'\d', contact_person):
        return JsonResponse(
            {"success": False, "error": "Contact Person should only contain letters, not numbers."},
            status=400
        )

    if contact_mobile and not re.fullmatch(r'[0-9]{1,15}', contact_mobile):
        return JsonResponse(
            {"success": False, "error": "Contact Mobile should only contain digits (1 to 15 numbers)."},
            status=400
        )

    faculty_remarks = (
        request.POST.get("faculty_remarks") or ""
    ).strip()


    college_id = (
        request.POST.get("college_id") or ""
    ).strip()

    other_college_name = (
        request.POST.get("other_college_name") or ""
    ).strip()

    college_name = ""

    if college_id == "OTHER":

        if not other_college_name:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Please enter the college name."
                },
                status=400
            )

        college_name = other_college_name

    elif college_id:

        college = get_object_or_404(
            School,
            school_id=college_id
        )

        college_name = college.school_name

    else:
        return JsonResponse(
            {
                "success": False,
                "error": "Please select your college."
            },
            status=400
        )







    if tournament.participation_type != "TEAM" and not entry_name:
        return JsonResponse(
            {
                "success": False,
                "error": "Please provide a valid name."
            },
            status=400
        )

   

    coach_id = (
        request.POST.get("coach_id") or ""
    ).strip()

    other_coach_name = (
        request.POST.get("other_coach_name") or ""
    ).strip()

    coach_name = ""


    if coach_id == "OTHER":

        if not other_coach_name:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Please enter the coach name."
                },
                status=400
            )

        coach_name = other_coach_name

   

    elif coach_id:

        coach = get_object_or_404(
            Coach,
            coach_id=coach_id,
            is_active=True
        )

        staff = (
            StaffProfile.objects
            .select_related("user")
            .filter(employee_id=coach.staff_id)
            .first()
        )

        if not staff:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Staff profile for this coach was not found."
                },
                status=400
            )

        coach_name = staff.user.full_name or coach.staff_id

   

    internal_team = None
    team_name = ""

    internal_team_id = (
        request.POST.get("internal_team_id") or ""
    ).strip()

    other_team_name = (
        request.POST.get("other_team_name") or ""
    ).strip()


    if tournament.participation_type == "TEAM":

        if internal_team_id == "OTHER":

            if not other_team_name:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "Please enter the team name."
                    },
                    status=400
                )

            team_name = other_team_name

        elif internal_team_id:

            internal_team = get_object_or_404(
                SportTeamModel,
                team_id=internal_team_id,
                status=True
            )

            team_name = internal_team.team_name


   

    if tournament.participation_type == "TEAM":

        raw_players = [
            p.strip()
            for p in request.POST.getlist("player_name[]")
            if p.strip()
        ]

        seen = set()
        players = []

        for name in raw_players:

            key = name.lower()

            if key in seen:
                continue

            seen.add(key)

            players.append({
                "name": name
            })


        min_p = tournament.minimum_participants or 1
        max_p = tournament.maximum_participants or min_p


        if len(players) < min_p:
            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        f"At least {min_p} player(s) are required."
                    )
                },
                status=400
            )


        if len(players) > max_p:
            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        f"No more than {max_p} player(s) are allowed."
                    )
                },
                status=400
            )


        players_count = len(players)

    else:

        players = [
            {
                "name": entry_name
            }
        ]

        players_count = 1




    with transaction.atomic():

        application, _ = (
            TournamentApplication.objects.get_or_create(
                invitation=invitation,
                defaults={
                    "tournament": tournament,
                }
            )
        )


        application.entry_name = entry_name
        application.coach_name = coach_name
        application.contact_person = contact_person
        application.contact_mobile = contact_mobile
        application.players_count = players_count
        application.players = players
        application.faculty_remarks = faculty_remarks
        application.internal_team = internal_team      
        application.team_name = team_name 
        application.status = "APPLIED"

        application.save()


       
      

        invitation.application_status = "APPLIED"
        invitation.applied_at = timezone.now()
        invitation.college_name = college_name

        invitation.save(
            update_fields=[
                "application_status",
                "applied_at",
                "college_name"
            ]
        )

        transaction.on_commit(lambda inv=invitation: broadcast_invitation_status(inv))

    DashboardNotification.objects.create(
        notification_type='TOURNAMENT',
        tournament_application=application,
        event='tournament_applied',
        message=f'{request.user.get_full_name() or request.user.username} '
                f'submitted an application for "{invitation.tournament.tournament_name}"',
        icon='trophy',
        recipient=None,
    )

    return JsonResponse( 
        {
            "success": True,
            "application_status": invitation.application_status
        }
    )


@login_required
def faculty_tournament_invitation_detail(request, uuid, invitation_uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    try:
        invitation = TournamentInvitation.objects.select_related(
            "tournament",
            "tournament__sport",
            "tournament__organizer",
            "tournament__venue",
        ).get(
            invitation_uuid=invitation_uuid,
            receiver_faculty__user=request.user,
        ) 
    except TournamentInvitation.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Invitation not found or not linked to your account."},
            status=404,
        )

    tournament = invitation.tournament

    return JsonResponse({
        "success": True,
        "invitation_uuid": str(invitation.invitation_uuid),
        "tournament_name": tournament.tournament_name,
        "tournament_code": tournament.tournament_code,
        "sport_name": tournament.sport.sport_name if tournament.sport else "",
        "tournament_type": tournament.get_tournament_type_display(),
        "start_date": tournament.start_date.strftime("%d %b %Y") if tournament.start_date else "",
        "end_date": tournament.end_date.strftime("%d %b %Y") if tournament.end_date else "",
        "registration_deadline": tournament.registration_deadline.strftime("%d %b %Y") if tournament.registration_deadline else "",
        "entry_fee": str(tournament.entry_fee),
        "organizer": tournament.organizer.get_full_name() if tournament.organizer else "",
        "venue": tournament.venue.facility_name if tournament.venue else "",
        "description": tournament.description or "",
        "banner_url": tournament.banner.url if tournament.banner else "",
        "rules_pdf_url": tournament.rules_pdf.url if tournament.rules_pdf else "",
    })

#############   kali code end ##################


@login_required
def faculty_notification_history(request, uuid):
    if str(request.user.uuid) != str(uuid): 
        return redirect("login")

    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")


    faculty = get_object_or_404(
        FacultyProfile,
        user=request.user
    )

    tournament_invitations = TournamentInvitation.objects.filter(
        receiver_faculty=faculty
    ).order_by("-invitation_sent_at")

    has_tournament_invitations = tournament_invitations.exists()

   
    latest_tournament_invitation = tournament_invitations.first()

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
        "has_tournament_invitations": has_tournament_invitations,
        "latest_tournament_invitation": latest_tournament_invitation,
    }
    return render(request, "teaching/notification_history.html", context)
    
# ************************************************ Arun Code ********************************************************


#================================Blaze Code Start(22.07.26)================================

# Faculty/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Sum, Count, F
from datetime import datetime, timedelta
import json
import csv
import base64
from django.core.files.base import ContentFile
from .models import LeaveRequest, LeaveType, FacultyLeaveBalance

# ✅ Import notification function
try:
    from Admin.notifications import notify_staff_new_faculty_leave_request
except ImportError:
    # Fallback if notification module not available
    def notify_staff_new_faculty_leave_request(leave_request):
        print(f"⚠️ Notification not sent. Faculty leave created: {leave_request.id}")
        return False


@login_required
def faculty_leave_dashboard(request, uuid):
    """Main leave dashboard with stats and analytics"""
    if not hasattr(request.user, 'faculty_profile'):
        messages.error(request, 'Access denied. Faculty only.')
        return redirect('faculty_dashboard', uuid=uuid)
    
    # ===== AUTO-CREATE LEAVE TYPES IF NOT EXISTS =====
    default_leave_types = [
        {'name': 'Annual Leave', 'code': 'ANNUAL', 'max_days_per_year': 30, 'color': '#3b82f6'},
        {'name': 'Sick Leave', 'code': 'SICK', 'max_days_per_year': 15, 'color': '#22c55e'},
        {'name': 'Casual Leave', 'code': 'CASUAL', 'max_days_per_year': 10, 'color': '#f59e0b'},
        {'name': 'Earned Leave', 'code': 'EARNED', 'max_days_per_year': 5, 'color': '#8b5cf6'},
        {'name': 'Compensatory Leave', 'code': 'COMP', 'max_days_per_year': 5, 'color': '#ec4899'},
        {'name': 'Unpaid Leave', 'code': 'UNPAID', 'max_days_per_year': 0, 'color': '#6b7280'},
    ]
    
    for lt in default_leave_types:
        LeaveType.objects.get_or_create(
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
    
    leave_types = LeaveType.objects.all()
    leave_requests = LeaveRequest.objects.filter(faculty=request.user).order_by('-created_at')
    
    # Get leave balance
    balance, created = FacultyLeaveBalance.objects.get_or_create(
        faculty=request.user,
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
        month_leaves = LeaveRequest.objects.filter(
            faculty=request.user,
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
        count = LeaveRequest.objects.filter(
            faculty=request.user,
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
        # Stats
        'total_leaves': total_leaves,
        'pending_leaves': pending_leaves,
        'approved_leaves': approved_leaves,
        'rejected_leaves': rejected_leaves,
        'cancelled_leaves': cancelled_leaves,
        'year_days_used': year_days_used,
        'current_year': current_year,
        # Analytics
        'monthly_data': json.dumps(monthly_data),
        'months': json.dumps(months),
        'type_labels': json.dumps(type_labels),
        'type_counts': json.dumps(type_counts),
        'type_colors': json.dumps(type_colors),
    }
    return render(request, 'Faculty_Leave/leave_request.html', context)


@login_required
def submit_leave_request(request, uuid):
    """
    Submit new leave request with attachment
    """
    # Check if user has faculty access
    if not hasattr(request.user, 'faculty_profile'):
        return JsonResponse({
            'success': False, 
            'message': 'Access denied. Faculty only.'
        })
    
    if request.method != 'POST':
        return JsonResponse({
            'success': False, 
            'message': 'Invalid request method'
        })
    
    try:
        # Parse JSON data
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
            return JsonResponse({
                'success': False, 
                'message': 'Please select a leave type'
            })
        
        if not start_date:
            return JsonResponse({
                'success': False, 
                'message': 'Please select a start date'
            })
        
        if not end_date:
            return JsonResponse({
                'success': False, 
                'message': 'Please select an end date'
            })
        
        if not reason or not reason.strip():
            return JsonResponse({
                'success': False, 
                'message': 'Please provide a reason for your leave'
            })
        
        # Get leave type
        leave_type = get_object_or_404(LeaveType, id=leave_type_id)
        
        # Parse dates
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Validate dates
        if start > end:
            return JsonResponse({
                'success': False, 
                'message': 'Start date cannot be after end date'
            })
        
        if start < timezone.now().date():
            return JsonResponse({
                'success': False, 
                'message': 'Cannot request leave for past dates'
            })
        
        # Check for overlapping leave requests
        overlapping = LeaveRequest.objects.filter(
            faculty=request.user,
            status__in=['pending', 'approved'],
            start_date__lte=end,
            end_date__gte=start
        ).exists()
        
        if overlapping:
            return JsonResponse({
                'success': False, 
                'message': 'You already have a leave request for these dates'
            })
        
        # Create leave request
        leave_request = LeaveRequest.objects.create(
            faculty=request.user,
            leave_type=leave_type,
            start_date=start,
            end_date=end,
            half_day_type=half_day,
            reason=reason.strip(),
            status='pending'
        )
        # ==========================================
        # AUDIT LOG: LEAVE REQUEST CREATED
        # ==========================================
        after_data = AuditLogger.model_to_dict(
            leave_request,
            fields=[
                "leave_type",
                "start_date",
                "end_date",
                "half_day_type",
                "reason",
                "status",
                "days_count",
            ]
        )

        AuditLogger.log(
            request=request,
            action="CREATE",
            module="Faculty Leave",
            object_type="Leave Request",
            object_id=leave_request.id,
            description=(
                f'Faculty "{request.user.get_full_name()}" '
                f'submitted a {leave_type.name} leave request '
                f'from {start} to {end}.'
            ),
            before_data=None,
            after_data=after_data,
            status="SUCCESS",
        )
        
        print(f"✅ Faculty leave request created: {leave_request.id} by {request.user.get_full_name()}")
        
        # ✅ Send notification to STAFF for approval
        try:
            notify_staff_new_faculty_leave_request(leave_request)
            print(f"✅ Notification sent to staff for faculty leave: {leave_request.id}")
        except Exception as e:
            print(f"❌ Notification error: {e}")
            # Continue even if notification fails
        
        # Handle attachment if provided
        if attachment_data and attachment_name:
            try:
                # Decode base64 attachment
                format, imgstr = attachment_data.split(';base64,')
                ext = format.split('/')[-1]
                filename = f"{leave_request.id}_{attachment_name}"
                file_data = ContentFile(base64.b64decode(imgstr), name=filename)
                leave_request.attachment = file_data
                leave_request.attachment_name = attachment_name
                leave_request.save()
                print(f"✅ Attachment saved: {filename}")
            except Exception as e:
                print(f"⚠️ Attachment error: {e}")
                # Continue even if attachment fails
        
        # Return success response
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
        return JsonResponse({
            'success': False, 
            'message': 'Invalid JSON data'
        })
    
    except Exception as e:
        print(f"❌ Submit leave error: {e}")
        return JsonResponse({
            'success': False, 
            'message': str(e)
        })


@login_required
def cancel_leave_request(request, uuid, leave_id):
    """Cancel a pending leave request"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False, 
            'message': 'Invalid request method'
        })
    
    try:
        leave = get_object_or_404(LeaveRequest, id=leave_id, faculty=request.user)
        
        if leave.status != 'pending':
            # ==========================================
            # AUDIT: BEFORE DATA
            # ==========================================

            before_data = AuditLogger.model_to_dict(
                leave,
                fields=[
                    "leave_type",
                    "start_date",
                    "end_date",
                    "half_day_type",
                    "reason",
                    "status",
                ]
            )
            return JsonResponse({
                'success': False, 
                'message': 'Only pending requests can be cancelled'
            })
        
        leave.status = 'cancelled'
        leave.save()
        # ==========================================
        # AUDIT: AFTER DATA
        # ==========================================

        after_data = AuditLogger.model_to_dict(
            leave,
            fields=[
                "leave_type",
                "start_date",
                "end_date",
                "half_day_type",
                "reason",
                "status",
            ]
        )


        # ==========================================
        # AUDIT LOG: LEAVE CANCELLED
        # ==========================================

        AuditLogger.log(
            request=request,
            action="STATUS_CHANGE",
            module="Faculty Leave",
            object_type="Leave Request",
            object_id=leave.id,
            description=(
                f'Faculty "{request.user.get_full_name()}" '
                f'cancelled leave request #{leave.id}.'
            ),
            before_data=before_data,
            after_data=after_data,
            status="SUCCESS",
        )
        
        print(f"✅ Faculty leave cancelled: {leave.id} by {request.user.get_full_name()}")
        
        return JsonResponse({
            'success': True, 
            'message': 'Leave request cancelled successfully'
        })
        
    except Exception as e:
        print(f"❌ Cancel leave error: {e}")
        return JsonResponse({
            'success': False, 
            'message': str(e)
        })


@login_required
def get_leave_details(request, uuid, leave_id):
    """Get leave request details for editing"""
    try:
        leave = get_object_or_404(LeaveRequest, id=leave_id, faculty=request.user)
        
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
        print(f"❌ Get leave details error: {e}")
        return JsonResponse({
            'success': False, 
            'message': str(e)
        })


@login_required
def update_leave_request(request, uuid, leave_id):
    """Update a pending leave request"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False, 
            'message': 'Invalid request method'
        })
    
    try:
        leave = get_object_or_404(LeaveRequest, id=leave_id, faculty=request.user)
        
        if leave.status != 'pending':
            return JsonResponse({
                'success': False, 
                'message': 'Only pending requests can be updated'
            })
        # ==========================================
        # AUDIT: BEFORE DATA
        # ==========================================

        before_data = AuditLogger.model_to_dict(
            leave,
            fields=[
                "leave_type",
                "start_date",
                "end_date",
                "half_day_type",
                "reason",
                "status",
                "days_count",
            ]
        )
        data = json.loads(request.body)
        
        leave_type_id = data.get('leave_type')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        half_day = data.get('half_day', 'full')
        reason = data.get('reason')
        
        # Validate required fields
        if not leave_type_id:
            return JsonResponse({
                'success': False, 
                'message': 'Please select a leave type'
            })
        
        if not start_date:
            return JsonResponse({
                'success': False, 
                'message': 'Please select a start date'
            })
        
        if not end_date:
            return JsonResponse({
                'success': False, 
                'message': 'Please select an end date'
            })
        
        if not reason or not reason.strip():
            return JsonResponse({
                'success': False, 
                'message': 'Please provide a reason for your leave'
            })
        
        leave_type = get_object_or_404(LeaveType, id=leave_type_id)
        
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if start > end:
            return JsonResponse({
                'success': False, 
                'message': 'Start date cannot be after end date'
            })
        
        # Check overlapping (excluding current)
        overlapping = LeaveRequest.objects.filter(
            faculty=request.user,
            status__in=['pending', 'approved'],
            start_date__lte=end,
            end_date__gte=start
        ).exclude(id=leave_id).exists()
        
        if overlapping:
            return JsonResponse({
                'success': False, 
                'message': 'You already have a leave request for these dates'
            })
        
        leave.leave_type = leave_type
        leave.start_date = start
        leave.end_date = end
        leave.half_day_type = half_day
        leave.reason = reason.strip()
        leave.save()
        # ==========================================
        # AUDIT: AFTER DATA
        # ==========================================

        after_data = AuditLogger.model_to_dict(
            leave,
            fields=[
                "leave_type",
                "start_date",
                "end_date",
                "half_day_type",
                "reason",
                "status",
                "days_count",
            ]
        )


        # ==========================================
        # AUDIT LOG: LEAVE UPDATED
        # ==========================================

        AuditLogger.log(
            request=request,
            action="UPDATE",
            module="Faculty Leave",
            object_type="Leave Request",
            object_id=leave.id,
            description=(
                f'Faculty "{request.user.get_full_name()}" '
                f'updated leave request #{leave.id}.'
            ),
            before_data=before_data,
            after_data=after_data,
            status="SUCCESS",
        )
        
        print(f"✅ Faculty leave updated: {leave.id} by {request.user.get_full_name()}")
        
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
        return JsonResponse({
            'success': False, 
            'message': 'Invalid JSON data'
        })
    
    except Exception as e:
        print(f"❌ Update leave error: {e}")
        return JsonResponse({
            'success': False, 
            'message': str(e)
        })


@login_required
def get_leave_balance(request, uuid):
    """Get faculty leave balance"""
    try:
        balance, created = FacultyLeaveBalance.objects.get_or_create(
            faculty=request.user,
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
        print(f"❌ Get leave balance error: {e}")
        return JsonResponse({
            'success': False, 
            'message': str(e)
        })


@login_required
def export_leave_report(request, uuid):
    """Export leave report as CSV"""
    try:
        leaves = LeaveRequest.objects.filter(
            faculty=request.user
        ).order_by(
            '-created_at'
        )
        # ==========================================
        # AUDIT LOG: EXPORT LEAVE REPORT
        # ==========================================

        AuditLogger.log(
            request=request,
            action="EXPORT",
            module="Faculty Leave",
            object_type="Leave Report",
            object_id="",
            description=(
                f'Faculty "{request.user.get_full_name()}" '
                f'exported their leave report containing '
                f'{leaves.count()} leave request(s) as CSV.'
            ),
            before_data=None,
            after_data={
                "export_format": "CSV",
                "record_count": leaves.count(),
            },
            status="SUCCESS",
        )
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="leave_report_{}.csv"'.format(
            timezone.now().strftime('%Y%m%d')
        )
        
        writer = csv.writer(response)
        writer.writerow([
            'S.No', 'Leave Type', 'Start Date', 'End Date', 
            'Days', 'Half Day', 'Reason', 'Status', 
            'Submitted On', 'Approved On'
        ])
        
        leaves = LeaveRequest.objects.filter(faculty=request.user).order_by('-created_at')
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
        
        return response
        
    except Exception as e:
        print(f"❌ Export leave report error: {e}")
        messages.error(request, f'Error exporting report: {str(e)}')
        return redirect('faculty_leave_dashboard', uuid=uuid)


# ============================================
# URLS FOR FACULTY LEAVE
# ============================================
# Add these to Faculty/urls.py:
#
# path('leave-dashboard/<uuid:uuid>/', views.faculty_leave_dashboard, name='faculty_leave_dashboard'),
# path('leave-request/submit/<uuid:uuid>/', views.submit_leave_request, name='submit_leave_request'),
# path('leave-request/cancel/<uuid:uuid>/<int:leave_id>/', views.cancel_leave_request, name='cancel_leave_request'),
# path('leave-request/details/<uuid:uuid>/<int:leave_id>/', views.get_leave_details, name='get_leave_details'),
# path('leave-request/update/<uuid:uuid>/<int:leave_id>/', views.update_leave_request, name='update_leave_request'),
# path('leave-balance/<uuid:uuid>/', views.get_leave_balance, name='get_leave_balance'),
# path('leave-export/<uuid:uuid>/', views.export_leave_report, name='export_leave_report'),


#================================Blaze Code End================================


# ************************************************* Communication Code ************************************************

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
from Staff.models import MessageThread, Message, MessageRecipient, Announcement, MessageAttachment

logger = logging.getLogger(__name__)

FACULTY_TEMPLATE = "communications/communications.html"


AVATAR_PALETTE = ["#2563eb", "#16a34a", "#7c3aed", "#d97706", "#be185d", "#0891b2"]

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

    print("Avatar URL:", avatar_photo)

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
def faculty_communications(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")

    user = request.user

    threads_qs = (
        MessageThread.objects
        .filter(is_announcement=False)
        .filter(Q(messages__sender=user) | Q(messages__recipients__recipient=user))
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
    return render(request, FACULTY_TEMPLATE, context)


@login_required
def faculty_search_recipients_ajax(request):
    q = request.GET.get("q", "").strip()

    base_qs = User.objects.exclude(id=request.user.id)

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


@login_required
@require_http_methods(["POST"])
def faculty_send_message_ajax(request, uuid):
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
                subject=subject or "(No subject)", created_by=request.user
            )
            message = Message.objects.create(thread=thread, sender=request.user, body=body)
            save_attachments(message, files)

            MessageRecipient.objects.create(message=message, recipient=recipient)
            MessageRecipient.objects.create(message=message, recipient=request.user, is_read=True)

        return JsonResponse({"success": True, "message": "Message sent!", "thread_id": thread.id})

    except Exception as e:
        logger.error(f"Error sending faculty message: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def faculty_thread_detail_ajax(request, uuid, thread_id):
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
        "other_role": _role_label(other) if other else "",

        "other_avatar_photo": other_avatar_photo,
        "other_avatar_letter": _initials(other_name),
        "other_avatar_bg": _avatar_color(other_name),
    })


@login_required
@require_http_methods(["POST"])
def faculty_reply_message_ajax(request):
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
        logger.error(f"Error replying (faculty): {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def faculty_archive_thread_ajax(request, uuid, thread_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    MessageRecipient.objects.filter(
        message__thread_id=thread_id, recipient=request.user
    ).update(archived=True)

    return JsonResponse({"success": True, "message": "Thread archived."})


@login_required
@require_http_methods(["POST"])
def faculty_unarchive_thread_ajax(request, uuid, thread_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    MessageRecipient.objects.filter(
        message__thread_id=thread_id, recipient=request.user
    ).update(archived=False)

    return JsonResponse({"success": True, "message": "Thread moved back to inbox."})


@login_required
def faculty_volume_ajax(request, uuid):
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



@login_required
def faculty_unread_messages_ajax(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False}, status=403)

    from Students.models import StudentOrgMessageThread

    org_thread_ids = StudentOrgMessageThread.objects.values_list("thread_id", flat=True)

    unread_qs = MessageRecipient.objects.filter(
        recipient=request.user, is_read=False, archived=False,
    ).exclude(message__thread_id__in=org_thread_ids).select_related(
        "message", "message__sender", "message__thread"
    ).order_by("-message__sent_at")

    unread_count = unread_qs.count()
    latest = None
    latest_row = unread_qs.first()
    if latest_row:
        msg = latest_row.message
        latest = {
            "thread_id": msg.thread_id,
            "sender_name": msg.sender.get_full_name() or msg.sender.email,
            "preview": (msg.body or "")[:120],
            "sent_at": msg.sent_at.isoformat(),
        }

    return JsonResponse({"success": True, "unread_count": unread_count, "latest": latest})

# ************************************************* Communication Code ************************************************

@login_required
def faculty_downloads(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")

    resources_qs = Resource.objects.filter(visible_to_faculty=True)

    search_query = request.GET.get('search', '').strip()
    type_filter = request.GET.get('type', 'all')

    if search_query:
        resources_qs = resources_qs.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
    if type_filter != 'all':
        resources_qs = resources_qs.filter(resource_type=type_filter)

    alerts_ctx = get_resource_alerts_context(request.user, "visible_to_faculty")
    mark_resource_alerts_seen(request.user)

    context = {
        "user": request.user,
        "resources": resources_qs,
        "search_query": search_query,
        "type_filter": type_filter,
        **alerts_ctx,
    }
    return render(request, "resources/faculty_downloads.html", context)


@login_required
def faculty_download_resource(request, uuid, resource_id):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")

    resource = get_object_or_404(Resource, id=resource_id, visible_to_faculty=True)

    if not resource.file or not default_storage.exists(resource.file.name):
        raise Http404("File not found")

    resource.download_count += 1
    resource.save(update_fields=["download_count"])

    return FileResponse(
        resource.file.open("rb"), as_attachment=True,
        filename=os.path.basename(resource.file.name),
    )


# ************************************************* Organizations (Faculty Advisor) Code ************************************************

# ************************************************* Organizations (Faculty Advisor) Code ************************************************

@login_required
def faculty_my_organizations(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return redirect("login")

    faculty = request.user.faculty_profile
    orgs = StudentOrganization.objects.filter(advisor=faculty).select_related("school", "department")

    context = {
        "orgs": orgs,
    }
    return render(request, "StudentAdvising/my_organizations.html", context)


@login_required
def faculty_org_members_ajax(request, uuid, org_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    faculty = request.user.faculty_profile
    org = get_object_or_404(StudentOrganization, id=org_id, advisor=faculty)

    members = StudentOrganizationMembership.objects.filter(
        organization=org
    ).exclude(status="INACTIVE").select_related("student__user").order_by("student__user__first_name")

    return JsonResponse({
        "success": True,
        "org_name": org.organization_name,
        "members": [
            {
                "membership_id": m.membership_id,
                "name": m.student.user.get_full_name(),
                "email": m.student.university_email,
                "status": m.status,
            }
            for m in members
        ],
    })


@login_required
@require_http_methods(["POST"])
def faculty_remove_member_ajax(request, uuid, membership_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    faculty = request.user.faculty_profile
    membership = get_object_or_404(
        StudentOrganizationMembership,
        membership_id=membership_id,
        organization__advisor=faculty
    )
    membership.status = "INACTIVE"
    membership.save()

    return JsonResponse({"success": True, "message": "Member removed."})


@login_required
def faculty_search_students_ajax(request, uuid, org_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    faculty = request.user.faculty_profile
    org = get_object_or_404(StudentOrganization, id=org_id, advisor=faculty)

    q = request.GET.get("q", "").strip()
    if not q or len(q) < 2:
        return JsonResponse({"success": True, "students": []})

    already_in = StudentOrganizationMembership.objects.filter(
        organization=org
    ).exclude(status="INACTIVE").values_list("student_id", flat=True)

    students = StudentProfile.objects.filter(
        Q(user__first_name__icontains=q) |
        Q(user__last_name__icontains=q) |
        Q(university_email__icontains=q)
    ).exclude(id__in=already_in).select_related("user")[:10]

    return JsonResponse({
        "success": True,
        "students": [
            {"id": s.id, "name": s.user.get_full_name(), "email": s.university_email}
            for s in students
        ],
    })


@login_required
@require_http_methods(["POST"])
def faculty_add_member_ajax(request, uuid, org_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    faculty = request.user.faculty_profile
    org = get_object_or_404(StudentOrganization, id=org_id, advisor=faculty)

    student_id = request.POST.get("student_id")
    student = get_object_or_404(StudentProfile, id=student_id)

    if org.is_full:
        return JsonResponse({"success": False, "error": f"{org.organization_name} is at capacity."})

    existing = StudentOrganizationMembership.objects.filter(
        student=student, organization=org
    ).first()

    if existing:
        if existing.status != "INACTIVE":
            return JsonResponse({"success": False, "error": f"{student.user.get_full_name()} is already a member."})
        # Reactivate the old membership instead of creating a duplicate row
        existing.status = "ACTIVE"
        existing.role = "Member"
        existing.start_date = timezone.now().date()
        existing.end_date = None
        existing.save()
        membership = existing
    else:
        membership = StudentOrganizationMembership.objects.create(
            student=student,
            organization=org,
            status="ACTIVE",
            role="Member",
            start_date=timezone.now().date(),
        )

    Notification.objects.create(
        user=membership.student.user,
        title="Added to Organization",
        message=f"You have been added to {org.organization_name}.",
        notification_type="INFO",
    )

    return JsonResponse({"success": True, "message": f"{student.user.get_full_name()} added."})


@login_required
@require_http_methods(["POST"])
def faculty_broadcast_message_ajax(request, uuid, org_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    faculty = request.user.faculty_profile
    org = get_object_or_404(StudentOrganization, id=org_id, advisor=faculty)

    message_text = request.POST.get("message", "").strip()
    if not message_text:
        return JsonResponse({"success": False, "error": "Message cannot be empty."})
    if len(message_text) > 1000:
        return JsonResponse({"success": False, "error": "Message is too long (max 1000 characters)."})

    members = StudentOrganizationMembership.objects.filter(
        organization=org, status="ACTIVE"
    ).select_related("student__user")

    notifications = [
        Notification(
            user=m.student.user,
            title=f"Message from {org.organization_name}",
            message=message_text,
            notification_type="INFO",
        )
        for m in members
    ]

    if notifications:
        Notification.objects.bulk_create(notifications)

    return JsonResponse({
        "success": True,
        "message": f"Message sent to {len(notifications)} member{'s' if len(notifications) != 1 else ''}."
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
def faculty_org_chat_messages_ajax(request, uuid, org_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    faculty = request.user.faculty_profile
    org = get_object_or_404(StudentOrganization, id=org_id, advisor=faculty)
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
                    else (m.sender.profile_photo.url if getattr(m.sender, "profile_photo", None) else None)
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
def faculty_org_chat_send_ajax(request, uuid, org_id):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    faculty = request.user.faculty_profile
    org = get_object_or_404(StudentOrganization, id=org_id, advisor=faculty)

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
        other_members = StudentOrganizationMembership.objects.filter(
            organization=org, status="ACTIVE"
        ).select_related("student__user")

        for m in other_members:
            other_recipients.add(m.student.user)

        for u in other_recipients:
            MessageRecipient.objects.create(message=message, recipient=u)

    return JsonResponse({"success": True})






from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from Admin.models import User, RoomAllocation, Hostel, Room
from Students.models import MaintenanceRequest


@login_required
def faculty_housing_view(request, uuid):
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
        'page_title': 'Faculty Housing',
    }
    
    return render(request, 'Faculty_Leave/faculty_housing.html', context)


@login_required
def faculty_get_available_rooms_json(request, uuid):
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
def faculty_maintenance_request_submit(request, uuid):
    if str(request.user.uuid) != str(uuid):
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    faculty = get_object_or_404(User, uuid=uuid)
    
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
            student=faculty,
            room=room,
            status='ACTIVE'
        ).exists()
        
        if not has_allocation:
            return JsonResponse({'success': False, 'error': 'You are not allocated to this room'})
        
        MaintenanceRequest.objects.create(
            student=faculty,
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