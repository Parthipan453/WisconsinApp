from django.shortcuts import render

def student_research(request, uuid):
    return render(request, 'jordan/student_research.html')

def student_application(request, uuid):
    return render(request, 'jordan/new_application.html')

# =================================== Research Project ===================================
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
def student_research_details(request, uuid):
    """
    View for student research details page - shows accepted research projects for the student
    """
    return render(request, 'jordan/research_student_details.html')

@login_required
@require_http_methods(["GET"])
def get_student_projects(request):
    """
    API endpoint to get all accepted research projects for the logged-in student
    """
    try:
        student = StudentProfile.objects.get(user=request.user)
        
        # Get all accepted applications for this student
        applications = StudentResearchApplication.objects.filter(
            student=student,
            status='accepted'
        ).select_related('research_opportunity', 'research_opportunity__faculty', 'research_opportunity__department')
        
        project_list = []
        for app in applications:
            project = app.research_opportunity
            if not project:
                continue
            
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
            
            # Track existing member IDs to avoid duplicates
            existing_member_ids = set()
            
            # Add Mentor (only once)
            if project.faculty:
                mentor_data = {
                    'id': project.faculty.id,
                    'name': project.faculty.user.get_full_name() if project.faculty.user else str(project.faculty),
                    'role': 'mentor',
                    'role_display': 'Mentor',
                    'type': 'Faculty'
                }
                members_data.append(mentor_data)
                existing_member_ids.add(f"faculty_{project.faculty.id}")
            
            # Add team members
            for member in team_members:
                if member.faculty:
                    # Skip if this is the mentor
                    if project.faculty and member.faculty.id == project.faculty.id:
                        continue
                    
                    # Check for duplicate
                    member_key = f"faculty_{member.faculty.id}"
                    if member_key in existing_member_ids:
                        continue
                    existing_member_ids.add(member_key)
                    
                    name = member.faculty.user.get_full_name() if member.faculty.user else str(member.faculty)
                    member_type = "Faculty"
                    
                    members_data.append({
                        'id': member.id,
                        'name': name,
                        'role': member.role.lower().replace(' ', '_'),
                        'role_display': member.get_role_display(),
                        'type': member_type
                    })
                    
                elif member.student:
                    # Check for duplicate
                    member_key = f"student_{member.student.id}"
                    if member_key in existing_member_ids:
                        continue
                    existing_member_ids.add(member_key)
                    
                    name = member.student.user.get_full_name() if member.student.user else str(member.student)
                    member_type = "Student"
                    
                    members_data.append({
                        'id': member.id,
                        'name': name,
                        'role': member.role.lower().replace(' ', '_'),
                        'role_display': member.get_role_display(),
                        'type': member_type
                    })
            
            # Department name
            dept_name = 'No Department'
            if project.department:
                dept_name = getattr(project.department, 'name', str(project.department))
            
            # Get project status
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
                'team_name': team_name or f"Team for {project.title}",
                'mentor': mentor_data if project.faculty else None,
                'team_members': members_data,
                'category': project.category,
                'skill_list': project.skill_list,
                'application_id': app.application_id,
                'reference_number': app.reference_number,
                'submitted_at': app.submitted_at.strftime('%Y-%m-%d') if app.submitted_at else None,
                'project_status': project_status_value.lower(),
                'project_status_display': project.get_project_status_display() if project.project_status else 'Draft',
            })
        
        return JsonResponse({
            'success': True,
            'projects': project_list
        })
        
    except StudentProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student profile not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def get_student_project_details(request):
    """
    API endpoint to get detailed project information for student modal
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
        
        # Organize team members by role - using sets to avoid duplicates
        team_by_role = {
            'mentor': [],
            'co_mentor': [],
            'advisor': [],
            'student': []
        }
        
        # Track added member names to avoid duplicates
        added_members = set()
        
        # Add mentor (only once)
        if project.faculty:
            mentor_name = project.faculty.user.get_full_name() if project.faculty.user else str(project.faculty)
            mentor_email = project.faculty.user.email if project.faculty.user else None
            mentor_key = f"{mentor_name}_mentor"
            if mentor_key not in added_members:
                added_members.add(mentor_key)
                team_by_role['mentor'].append({
                    'name': mentor_name,
                    'email': mentor_email,
                    'role': 'Mentor'
                })
        
        # Add team members
        for member in team_members:
            if member.faculty:
                # Skip if this is the mentor (already added)
                if project.faculty and member.faculty.id == project.faculty.id:
                    continue
                
                name = member.faculty.user.get_full_name() if member.faculty.user else str(member.faculty)
                email = member.faculty.user.email if member.faculty.user else None
                role_display = member.get_role_display()
                
                # Create unique key to avoid duplicates
                member_key = f"{name}_{role_display}"
                if member_key in added_members:
                    continue
                added_members.add(member_key)
                
                if role_display == 'Co-Mentor':
                    team_by_role['co_mentor'].append({'name': name, 'email': email, 'role': role_display})
                elif role_display == 'Advisor':
                    team_by_role['advisor'].append({'name': name, 'email': email, 'role': role_display})
                else:
                    # For any other faculty role, add as co-mentor
                    team_by_role['co_mentor'].append({'name': name, 'email': email, 'role': 'Co-Mentor'})
                    
            elif member.student:
                name = member.student.user.get_full_name() if member.student.user else str(member.student)
                email = member.student.user.email if member.student.user else None
                
                member_key = f"{name}_student"
                if member_key in added_members:
                    continue
                added_members.add(member_key)
                
                team_by_role['student'].append({'name': name, 'email': email, 'role': 'Student'})
        
        # Get accepted students for this project (only if not already added)
        accepted_students = StudentResearchApplication.objects.filter(
            research_opportunity=project,
            status='accepted'
        ).select_related('student__user')
        
        for app in accepted_students:
            student_name = app.student.user.get_full_name() if app.student.user else str(app.student)
            student_email = app.student.user.email if app.student.user else None
            
            # Check if already added
            member_key = f"{student_name}_student"
            if member_key not in added_members:
                added_members.add(member_key)
                team_by_role['student'].append({
                    'name': student_name,
                    'email': student_email,
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
                'available_slots': project.available_slots,
                'skill_list': project.skill_list,
                'reference_link': project.reference_link,
                'additional_notes': project.additional_notes or '',
                'team_name': team_name or f"Team for {project.title}",
                'team_by_role': team_by_role,
                'progress_updates': progress_data,
                'overall_progress': overall_progress,
                'project_status': project_status_value.lower(),
                'project_status_display': project.get_project_status_display() if project.project_status else 'Draft',
                'student_list': []  # No need for separate student list as students are in team_by_role
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
@require_http_methods(["GET"])
def get_project_status_update(request):
    """
    API endpoint to get updated project status (for real-time updates)
    """
    try:
        project_id = request.GET.get('project_id')
        
        if not project_id:
            return JsonResponse({
                'success': False,
                'error': 'Project ID is required'
            }, status=400)
        
        project = get_object_or_404(ResearchOpportunity, research_id=project_id)
        
        project_status_value = project.project_status if project.project_status else 'DRAFT'
        
        return JsonResponse({
            'success': True,
            'data': {
                'status': project_status_value.lower(),
                'status_display': project.get_project_status_display() if project.project_status else 'Draft',
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

    
# ================================ Research Publication ==============================

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
from Students.models import StudentProfile
from Faculty.models import FacultyProfile


@login_required
def student_research_publication(request, uuid):
    """
    View for student research publication page - shows publications for student's research projects
    """
    try:
        student = StudentProfile.objects.get(user=request.user)
        
        context = {
            'student': student,
        }
        
        return render(request, 'jordan/student_research_publication.html', context)
        
    except StudentProfile.DoesNotExist:
        return render(request, 'jordan/error.html', {
            'error': 'Student Profile Not Found',
            'message': 'Your student profile could not be found.'
        })
    except Exception as e:
        return render(request, 'jordan/error.html', {
            'error': 'Error',
            'message': str(e)
        })


@login_required
@require_http_methods(["GET"])
def get_student_publications(request):
    """
    API endpoint to get all publications for a student's research projects
    """
    try:
        student = StudentProfile.objects.get(user=request.user)
        
        # Get all research projects the student is part of
        research_ids = []
        
        # 1. Through ResearchTeamMember
        team_memberships = ResearchTeamMember.objects.filter(student=student)
        for membership in team_memberships:
            if membership.team and membership.team.research_details:
                research_ids.append(membership.team.research_details.research_id)
        
        # 2. Through accepted applications
        accepted_applications = StudentResearchApplication.objects.filter(
            student=student,
            status='accepted'
        ).select_related('research_opportunity')
        
        for app in accepted_applications:
            if app.research_opportunity:
                research_ids.append(app.research_opportunity.research_id)
        
        # Remove duplicates
        research_ids = list(set(research_ids))
        
        # If no research projects found, return empty list
        if not research_ids:
            return JsonResponse({
                'success': True,
                'publications': []
            })
        
        # Get all publications for these research projects
        publications = StudentResearchPublication.objects.filter(
            research__research_id__in=research_ids
        ).select_related(
            'research', 'research__faculty', 'research__faculty__user',
            'created_by', 'created_by__user'
        ).prefetch_related(
            'authors__team_member', 
            'authors__team_member__faculty__user', 
            'authors__team_member__student__user'
        )
        
        publication_list = []
        for pub in publications:
            # Get authors
            authors = []
            for author in pub.authors.all():
                team_member = author.team_member
                if team_member.faculty:
                    name = team_member.faculty.user.get_full_name() if team_member.faculty.user else str(team_member.faculty)
                    email = team_member.faculty.user.email if team_member.faculty.user else None
                elif team_member.student:
                    name = team_member.student.user.get_full_name() if team_member.student.user else str(team_member.student)
                    email = team_member.student.user.email if team_member.student.user else None
                else:
                    continue
                
                authors.append({
                    'id': author.id,
                    'name': name,
                    'email': email,
                    'role': author.get_author_role_display(),
                    'order': author.author_order,
                    'team_member_id': team_member.id
                })
            
            # Check if current student is an author
            is_author = any(
                author.get('email') == student.user.email for author in authors
            )
            
            publication_list.append({
                'id': pub.publication_id,
                'uuid': str(pub.publication_uuid),
                'title': pub.title,
                'abstract': pub.abstract,
                'keywords': pub.keywords,
                'publication_type': pub.publication_type,
                'publication_type_display': pub.get_publication_type_display(),
                'status': pub.status.lower(),
                'status_display': pub.get_status_display(),
                'research_title': pub.research.title if pub.research else 'N/A',
                'research_id': pub.research.research_id if pub.research else None,
                'created_by': pub.created_by.user.get_full_name() if pub.created_by and pub.created_by.user else None,
                'created_at': pub.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': pub.updated_at.strftime('%Y-%m-%d %H:%M'),
                'authors': authors,
                'author_count': len(authors),
                'is_author': is_author,
            })
        
        return JsonResponse({
            'success': True,
            'publications': publication_list
        })
        
    except StudentProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student profile not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_student_publication_detail(request):
    """
    API endpoint to get detailed publication information for student
    """
    try:
        publication_id = request.GET.get('publication_id')
        
        if not publication_id:
            return JsonResponse({
                'success': False,
                'error': 'Publication ID is required'
            }, status=400)
        
        student = StudentProfile.objects.get(user=request.user)
        publication = get_object_or_404(StudentResearchPublication, publication_id=publication_id)
        
        # Get authors
        authors = []
        for author in publication.authors.all():
            team_member = author.team_member
            if team_member.faculty:
                name = team_member.faculty.user.get_full_name() if team_member.faculty.user else str(team_member.faculty)
                email = team_member.faculty.user.email if team_member.faculty.user else None
            elif team_member.student:
                name = team_member.student.user.get_full_name() if team_member.student.user else str(team_member.student)
                email = team_member.student.user.email if team_member.student.user else None
            else:
                continue
            
            authors.append({
                'id': author.id,
                'name': name,
                'email': email,
                'role': author.get_author_role_display(),
                'order': author.author_order,
                'team_member_id': team_member.id
            })
        
        # Check if current student is an author
        is_author = any(
            author.get('email') == student.user.email for author in authors
        )
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': publication.publication_id,
                'uuid': str(publication.publication_uuid),
                'title': publication.title,
                'abstract': publication.abstract,
                'keywords': publication.keywords,
                'publication_type': publication.publication_type,
                'publication_type_display': publication.get_publication_type_display(),
                'status': publication.status.lower(),
                'status_display': publication.get_status_display(),
                'research_title': publication.research.title if publication.research else 'N/A',
                'research_id': publication.research.research_id if publication.research else None,
                'created_by': publication.created_by.user.get_full_name() if publication.created_by and publication.created_by.user else None,
                'created_at': publication.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': publication.updated_at.strftime('%Y-%m-%d %H:%M'),
                'authors': authors,
                'author_count': len(authors),
                'is_author': is_author,
                'manuscript_url': publication.manuscript.url if publication.manuscript else None,
            }
        })
        
    except StudentProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student profile not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ===================================== Research Submission ==========================

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

from Research.models import (
    ResearchOpportunity, ResearchTeam, ResearchTeamMember, 
    StudentResearchApplication, StudentResearchPublication, 
    PublicationAuthor, PublicationSubmission
)
from Students.models import StudentProfile


@login_required
def student_research_submission(request, uuid):
    """
    View for students to view research submissions
    """
    return render(request, 'jordan/student_research_submission.html')


@login_required
@require_http_methods(["GET"])
def get_student_research_projects_with_submissions(request):
    """
    API endpoint to get all research projects for a student with submission status
    """
    try:
        student = StudentProfile.objects.get(user=request.user)
        
        # Get all accepted applications for this student
        applications = StudentResearchApplication.objects.filter(
            student=student,
            status='accepted'
        ).select_related('research_opportunity')
        
        project_list = []
        for app in applications:
            project = app.research_opportunity
            if not project:
                continue
            
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
                'has_publication': bool(publication),
                'has_submission': has_submission,
                'submission': submission
            })
        
        return JsonResponse({
            'success': True,
            'projects': project_list
        })
        
    except StudentProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student profile not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_student_project_submission(request):
    """
    API endpoint to get submission details for a specific project for a student
    """
    try:
        project_id = request.GET.get('project_id')
        
        if not project_id:
            return JsonResponse({
                'success': False,
                'error': 'Project ID is required'
            }, status=400)
        
        student = StudentProfile.objects.get(user=request.user)
        
        # Verify student is part of this project
        application = StudentResearchApplication.objects.filter(
            student=student,
            research_opportunity_id=project_id,
            status='accepted'
        ).first()
        
        if not application:
            return JsonResponse({
                'success': False,
                'error': 'You are not authorized to view this project'
            }, status=403)
        
        project = application.research_opportunity
        
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
            'submission': submission_data,
            'project_title': project.title,
            'project_category': project.category,
            'project_department': project.department.department_name if project.department else 'No Department'
        })
        
    except StudentProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student profile not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)



# ============================== Research Student Application Details ==============================

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from Research.models import StudentResearchApplication, ResearchOpportunity, ResearchOpportunityDocument
from Research.Elsa_research.forms import StudentResearchApplicationForm
from Students.models import StudentProfile, StudentAcademicProfile
import json


@login_required
def view_application(request, research_id, uuid):
    """
    View for student research application
    URL: student_research_opportunity/research_application/<str:research_id>/<uuid:uuid>/
    """
    # Convert research_id to int if it's a string
    try:
        research_id_int = int(research_id)
    except (ValueError, TypeError):
        messages.error(request, 'Invalid research ID.')
        return redirect('Elsa_research:student_research_opportunity', uuid=uuid)
    
    opportunity = get_object_or_404(
        ResearchOpportunity,
        research_id=research_id_int,
        status="OPEN"
    )
    
    try:
        student = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('Elsa_research:student_research_opportunity', uuid=uuid)
    
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
                    if existing_application and existing_application.status == 'draft':
                        application = existing_application
                    else:
                        application = StudentResearchApplication(
                            student=student,
                            research_opportunity=opportunity
                        )
                    
                    # Update fields
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
                    
                    application.submit()
                    application.save()
                    
                    redirect_url = reverse('Elsa_research:research_student_application', kwargs={
                        'research_id': research_id,
                        'uuid': uuid
                    })
                    return redirect(f'{redirect_url}?success=true')
                    
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        else:
            if form.non_field_errors():
                for error in form.non_field_errors():
                    messages.error(request, error)
    else:
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
    
    documents = ResearchOpportunityDocument.objects.filter(opportunity=opportunity)
    
    context = {
        "phone": int(student.user.mobile_number) if student.user.mobile_number else None,
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
def student_research_application_details(request, uuid):
    """
    View for students to see their research application history and status
    URL: student_research_application_details/<uuid:uuid>/
    """
    try:
        student = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('Elsa_research:student_research_opportunity', uuid=uuid)
    
    # Get all applications for this student
    applications = StudentResearchApplication.objects.filter(
        student=student
    ).select_related('research_opportunity').order_by('-created_at')
    
    # Get academic info
    try:
        academic_info = StudentAcademicProfile.objects.get(student=student)
        department_name = academic_info.department.department_name if academic_info.department else None
        program_name = academic_info.program.program_name if academic_info.program else None
    except StudentAcademicProfile.DoesNotExist:
        department_name = None
        program_name = None
    
    # Statistics
    total_applications = applications.count()
    accepted_count = applications.filter(status='accepted').count()
    rejected_count = applications.filter(status='rejected').count()
    pending_count = applications.filter(status__in=['submitted', 'under_review', 'shortlisted']).count()
    withdrawn_count = applications.filter(status='withdrawn').count()
    
    # Prepare application data as JSON for JavaScript
    applications_json = []
    for app in applications:
        applications_json.append({
            'id': str(app.application_id),
            'reference': app.reference_number or f'RSP-{app.application_id:06d}',
            'title': app.research_opportunity.title if app.research_opportunity else 'Unknown Project',
            'status': app.status,
            'statusDisplay': app.get_status_display(),
            'submittedDate': app.submitted_at.strftime('%B %d, %Y %H:%M') if app.submitted_at else app.created_at.strftime('%B %d, %Y %H:%M'),
            'updatedDate': app.updated_at.strftime('%B %d, %Y %H:%M'),
            'researchArea': app.research_opportunity.category if app.research_opportunity else 'Not specified',
            'timeCommitment': app.get_time_commitment_display(),
            'availability': app.get_availability_display(),
            'motivation': app.motivation,
            'skillsContribution': app.skills_contribution,
            'priorExperience': app.prior_experience or 'Not provided',
            'additionalInfo': app.additional_info or 'Not provided',
            'reviewedAt': app.reviewed_at.strftime('%B %d, %Y %H:%M') if app.reviewed_at else 'N/A',
            'reviewComments': app.review_comments or 'No comments',
            'hasResume': bool(app.resume),
            'resumeUrl': app.resume.url if app.resume else None,
            'hasStatement': bool(app.statement_of_interest),
            'statementUrl': app.statement_of_interest.url if app.statement_of_interest else None,
            'hasTranscript': bool(app.academic_transcript),
            'transcriptUrl': app.academic_transcript.url if app.academic_transcript else None,
            'department': app.research_opportunity.department.department_name if app.research_opportunity and app.research_opportunity.department else 'Not specified',
        })
    
    context = {
        'uuid': uuid,
        'student': student,
        'department_name': department_name,
        'program_name': program_name,
        'applications': applications,
        'applications_json': json.dumps(applications_json),
        'total_applications': total_applications,
        'accepted_count': accepted_count,
        'rejected_count': rejected_count,
        'pending_count': pending_count,
        'withdrawn_count': withdrawn_count,
        'has_applications': total_applications > 0,
    }
    
    return render(request, 'jordan/student_research_application_details.html', context)

