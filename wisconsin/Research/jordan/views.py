from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from Faculty.models import Department, FacultyProfile


# ============================================
# VIEW ALL FACULTY MEMBERS
# ============================================
@login_required
def faculty_list(request):
    """
    Display all faculty members with their details and assign button.
    """
    # Get filter parameters
    department_filter = request.GET.get('department', '')
    role_filter = request.GET.get('role', '')
    search_query = request.GET.get('search', '')
    
    # Get all faculty members
    faculty_list = FacultyProfile.objects.select_related(
        'department', 'user'
    ).all()
    
    # Apply department filter
    if department_filter:
        faculty_list = faculty_list.filter(department__slug=department_filter)
    
    # Apply role filter
    if role_filter:
        if role_filter == 'mentor':
            faculty_list = faculty_list.filter(is_mentor=True)
        elif role_filter == 'none':
            faculty_list = faculty_list.filter(
                is_mentor=False,
            )
    
    # Apply search
    if search_query:
        faculty_list = faculty_list.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(preferred_name__icontains=search_query) |
            Q(employee_id__icontains=search_query) |
            Q(department__department_name__icontains=search_query) |
            Q(email__icontains=search_query)
        ).distinct()
    
    # Get statistics
    total_faculty = FacultyProfile.objects.count()
    total_departments = Department.objects.filter(status='ACTIVE').count()
    mentors = FacultyProfile.objects.filter(is_mentor=True).count()
    no_role = FacultyProfile.objects.filter(
        is_mentor=False,
    ).count()
    
    # Get departments for filter
    departments = Department.objects.filter(status='ACTIVE')
    
    context = {
        'faculty_list': faculty_list,
        'total_faculty': total_faculty,
        'total_departments': total_departments,
        'mentors': mentors,
        'no_role': no_role,
        'departments': departments,
        'department_filter': department_filter,
        'role_filter': role_filter,
        'search_query': search_query,
    }
    
    return render(request, 'jordan/faculty_list.html', context)


# ============================================
# VIEW SINGLE FACULTY DETAILS - Using UUID
# ============================================
@login_required
def faculty_detail(request, faculty_uuid):
    """
    Display detailed information about a single faculty member using UUID.
    """
    faculty = get_object_or_404(
        FacultyProfile.objects.select_related('department', 'user'),
        user__uuid=faculty_uuid
    )
    
    context = {
        'faculty': faculty,
    }
    
    return render(request, 'jordan/faculty_detail.html', context)


# ============================================
# ASSIGN/UPDATE MENTOR ROLE - AJAX/JSON
# ============================================
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def assign_mentor_role(request, faculty_uuid):
    """
    Assign or update mentor role for a faculty member.
    Only one role can be assigned at a time.
    """
    try:
        faculty = get_object_or_404(
            FacultyProfile.objects.select_related('user'),
            user__uuid=faculty_uuid
        )
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False, 
                'error': 'Invalid JSON data'
            }, status=400)
        
        role_type = data.get('role')
        action = data.get('action')
        
        valid_roles = ['mentor', 'none']
        if role_type not in valid_roles:
            return JsonResponse({
                'success': False, 
                'error': f'Invalid role type. Must be one of: {", ".join(valid_roles)}'
            }, status=400)
        
        if action == 'assign':
            # Reset all roles first, then assign the selected one
            faculty.is_mentor = False
            
            if role_type == 'mentor':
                faculty.is_mentor = True
            
            faculty.save()
            
            role_labels = {
                'mentor': 'Mentor',
            }
            
            return JsonResponse({
                'success': True,
                'message': f'{role_labels.get(role_type, role_type)} role assigned successfully',
                'role': role_type,
                'role_display': role_labels.get(role_type, role_type),
                'has_role': True,
                'is_mentor': faculty.is_mentor,
            })
            
        elif action == 'remove':
            # Remove the role
            faculty.is_mentor = False
            faculty.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Role removed successfully',
                'role': 'none',
                'role_display': 'No Role',
                'has_role': False,
                'is_mentor': faculty.is_mentor,
            })
            
        else:
            return JsonResponse({
                'success': False, 
                'error': 'Invalid action. Must be "assign" or "remove"'
            }, status=400)
            
    except FacultyProfile.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Faculty not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=500)


# ============================================
# GET FACULTY ROLES - AJAX
# ============================================
@login_required
def get_faculty_roles(request, faculty_uuid):
    """
    Get current mentor roles for a faculty member.
    """
    try:
        faculty = get_object_or_404(
            FacultyProfile.objects.select_related('user'),
            user__uuid=faculty_uuid
        )
        
        # Get role display
        role_display = 'No Role'
        if faculty.is_mentor:
            role_display = 'Mentor'
        
        return JsonResponse({
            'success': True,
            'is_mentor': faculty.is_mentor,
            'has_role': faculty.has_any_mentor_role(),
            'role_display': role_display
        })
        
    except FacultyProfile.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Faculty not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=500)