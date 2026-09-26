// ============================================
// Research Team Management
// ============================================

let currentProjects = [];
let currentProjectId = null;
let isLoading = false;
let slimSelectInstance = null;

// ============================================
// API Utilities
// ============================================

function getCSRFToken() {
    return document.getElementById('csrfToken')?.value || '';
}

async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    };
    
    if (data) options.body = JSON.stringify(data);
    
    try {
        const response = await fetch(url, options);
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'An error occurred');
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ============================================
// Slim Select Initialization
// ============================================

function initSlimSelect(selectElement) {
    if (!selectElement) return null;
    
    try {
        // Destroy existing instance if any
        if (selectElement.slim) {
            selectElement.slim.destroy();
            delete selectElement.slim;
        }
        
        const instance = new SlimSelect({
            select: selectElement,
            settings: {
                placeholderText: selectElement.options[0]?.text || 'Select a member...',
                showSearch: false,
                allowDeselect: false
            }
        });
        
        selectElement.slim = instance;
        return instance;
    } catch (error) {
        console.error('Error initializing Slim Select:', error);
        return null;
    }
}

function destroySlimSelect(selectElement) {
    if (selectElement && selectElement.slim) {
        selectElement.slim.destroy();
        delete selectElement.slim;
    }
}

// ============================================
// Data Loading
// ============================================

async function loadProjects() {
    if (isLoading) return;
    isLoading = true;
    
    try {
        const data = await apiRequest('/faculty/api/projects/');
        currentProjects = data.projects || [];
        renderProjects();
        updateProjectCount();
    } catch (error) {
        showNotification('Failed to load projects: ' + error.message, 'error');
    } finally {
        isLoading = false;
    }
}

async function loadAvailableMembers(role) {
    const select = document.getElementById('memberSelect');
    const projectId = currentProjectId;
    
    // Determine which API to call based on role
    let url;
    let memberType;
    
    if (role === 'co_mentor' || role === 'advisor') {
        // Only faculty for Co-Mentor and Advisor
        url = `/faculty/api/faculty/?project_id=${projectId}`;
        memberType = 'faculty';
    } else if (role === 'student') {
        // Only accepted students for Student role
        url = `/faculty/api/students/?project_id=${projectId}`;
        memberType = 'student';
    } else {
        showNotification('Invalid role', 'error');
        return;
    }
    
    try {
        const data = await apiRequest(url);
        const members = memberType === 'faculty' ? data.faculty : data.students;
        
        // Clear existing options
        select.innerHTML = '<option value="">Select a member...</option>';
        
        if (!members || members.length === 0) {
            const msg = memberType === 'student' ? 'No accepted students available' : 'No faculty available';
            select.innerHTML += `<option value="" disabled>${msg}</option>`;
        } else {
            members.forEach(member => {
                const label = member.department 
                    ? `${member.name} (${member.department})`
                    : member.program 
                        ? `${member.name} - ${member.program}`
                        : member.name;
                select.innerHTML += `<option value="${member.id}">${label}</option>`;
            });
        }
        
        // Reinitialize Slim Select
        initSlimSelect(select);
        
        // Hide error if visible
        document.getElementById('memberSelectError').style.display = 'none';
        
    } catch (error) {
        showNotification('Failed to load members: ' + error.message, 'error');
    }
}

// ============================================
// Render Functions
// ============================================

function renderProjects() {
    const grid = document.getElementById('projectsGrid');
    grid.innerHTML = '';
    
    if (!currentProjects || currentProjects.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="ti ti-folder-open"></i>
                <h3>No projects found</h3>
                <p>You haven't posted any research opportunities yet.</p>
            </div>
        `;
        return;
    }
    
    currentProjects.forEach(project => {
        const card = document.createElement('div');
        card.className = 'project-card';
        
        const members = project.team_members || [];
        const count = members.length;
        
        let avatars = '';
        if (count === 0) {
            avatars = '<span class="no-team">No team assigned</span>';
        } else {
            const display = members.slice(0, 4);
            display.forEach(m => {
                const isMentor = m.is_mentor || false;
                avatars += `
                    <div class="team-avatar-small ${isMentor ? 'mentor-avatar' : ''}" 
                         title="${m.name} - ${m.role_display}${isMentor ? ' (Mentor)' : ''}">
                        <span>${m.name.slice(0, 2).toUpperCase()}</span>
                    </div>
                `;
            });
            if (count > 4) {
                avatars += `<div class="team-avatar-small more"><span>+${count - 4}</span></div>`;
            }
        }
        
        card.innerHTML = `
            <div class="card-header">
                <h4 class="project-title">${project.title}</h4>
            </div>
            <div class="card-body">
                <p class="project-description">${(project.description || '').substring(0, 120)}${(project.description || '').length > 120 ? '...' : ''}</p>
                <div class="project-meta">
                    <span><i class="ti ti-calendar"></i> ${project.start_date ? new Date(project.start_date).toLocaleDateString() : 'Not set'}</span>
                    <span><i class="ti ti-building"></i> ${project.department}</span>
                    <span><i class="ti ti-user"></i> ${count} Members</span>
                </div>
                ${project.team_members?.find(m => m.is_mentor) ? `
                    <div class="mentor-badge-small">
                        <i class="ti ti-star"></i> Mentor: ${project.team_members.find(m => m.is_mentor).name}
                    </div>
                ` : ''}
                <div class="team-preview">
                    <span class="team-preview-label"><i class="ti ti-users"></i> Team:</span>
                    <div class="team-avatars">${avatars}</div>
                </div>
            </div>
            <div class="card-footer">
                <button class="btn-view-details" onclick="viewProjectDetails('${project.id}')">
                    <i class="ti ti-eye"></i> View Details
                </button>
                <button class="btn-assign-team" onclick="openAssignTeamModal('${project.id}')">
                    <i class="ti ti-user-plus"></i> Assign Team
                </button>
            </div>
        `;
        grid.appendChild(card);
    });
}

function renderTeamMembers(project) {
    const members = project.team_members || [];
    const nonMentor = members.filter(m => !m.is_mentor);
    
    const roleMap = {
        'co_mentor': { list: 'coMentorList', label: 'Co-Mentors', icon: 'ti ti-user' },
        'advisor': { list: 'advisorList', label: 'Advisors', icon: 'ti ti-bulb' },
        'student': { list: 'studentList', label: 'Students', icon: 'ti ti-user-check' }
    };
    
    Object.keys(roleMap).forEach(role => {
        const container = document.getElementById(roleMap[role].list);
        const items = nonMentor.filter(m => m.role === role);
        
        container.innerHTML = '';
        if (items.length === 0) {
            container.innerHTML = `<p class="empty-message">No ${roleMap[role].label.toLowerCase()} assigned</p>`;
        } else {
            items.forEach(m => {
                const div = document.createElement('div');
                div.className = 'member-item';
                
                const canRemove = m.is_removable && !m.is_application;
                
                div.innerHTML = `
                    <div class="member-avatar"><span>${m.name.slice(0, 2).toUpperCase()}</span></div>
                    <div class="member-info">
                        <span class="member-name">${m.name}</span>
                        <span class="member-role">${m.role_display}</span>
                        <span class="member-type">${m.type}</span>
                    </div>
                    ${canRemove ? `
                        <button class="member-remove" onclick="openRemoveMemberModal('${m.id}', '${m.name}')" title="Remove member">
                            <i class="ti ti-x"></i>
                        </button>
                    ` : m.is_application ? `
                        <span class="member-auto-added" title="Auto-added from accepted application">
                            <i class="ti ti-lock"></i>
                        </span>
                    ` : ''}
                `;
                container.appendChild(div);
            });
        }
    });
}

// ============================================
// Modal Operations
// ============================================

function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

function closeAddMemberModal() {
    closeModal('addMemberModal');
    // Clean up Slim Select
    const select = document.getElementById('memberSelect');
    if (select) {
        destroySlimSelect(select);
    }
    // Reset form
    document.getElementById('addMemberForm').reset();
    document.getElementById('memberSelectError').style.display = 'none';
}

// ============================================
// Project Details
// ============================================

function viewProjectDetails(projectId) {
    const project = currentProjects.find(p => p.id === projectId);
    if (!project) {
        showNotification('Project not found', 'error');
        return;
    }
    
    currentProjectId = projectId;
    
    document.getElementById('detailTitle').textContent = project.title;
    document.getElementById('detailDescription').textContent = project.description || 'No description available';
    document.getElementById('detailStartDate').textContent = project.start_date ? new Date(project.start_date).toLocaleDateString() : 'Not set';
    document.getElementById('detailEndDate').textContent = project.end_date ? new Date(project.end_date).toLocaleDateString() : 'Not set';
    document.getElementById('detailDepartment').textContent = project.department || 'No Department';
    
    // Mentor
    const mentor = project.team_members?.find(m => m.is_mentor);
    const mentorContainer = document.getElementById('detailMentor');
    if (mentor) {
        mentorContainer.innerHTML = `
            <div class="mentor-card">
                <div class="mentor-avatar"><span>${mentor.name.slice(0, 2).toUpperCase()}</span></div>
                <div class="mentor-info">
                    <div class="mentor-name">${mentor.name}</div>
                    <div class="mentor-role">${mentor.role_display}</div>
                    <div class="mentor-type">${mentor.type}</div>
                </div>
                <div class="mentor-badge"><i class="ti ti-star"></i> Lead</div>
            </div>
        `;
    } else {
        mentorContainer.innerHTML = `<div class="no-mentor"><i class="ti ti-user-off"></i><span>No mentor assigned</span></div>`;
    }
    
    // Team Members
    const teamContainer = document.getElementById('detailTeamMembers');
    teamContainer.innerHTML = '';
    
    const nonMentor = (project.team_members || []).filter(m => !m.is_mentor);
    if (nonMentor.length === 0) {
        teamContainer.innerHTML = '<p class="no-team-members">No team members assigned</p>';
    } else {
        const roleMap = {
            'co_mentor': { label: 'Co-Mentors', icon: 'ti ti-user' },
            'advisor': { label: 'Advisors', icon: 'ti ti-bulb' },
            'student': { label: 'Students', icon: 'ti ti-user-check' }
        };
        
        Object.keys(roleMap).forEach(role => {
            const items = nonMentor.filter(m => m.role === role);
            if (items.length > 0) {
                const section = document.createElement('div');
                section.className = 'team-role-section';
                section.innerHTML = `
                    <div class="team-role-label">
                        <i class="${roleMap[role].icon}"></i>
                        ${roleMap[role].label}
                        <span class="team-role-count">${items.length}</span>
                    </div>
                    <div class="team-role-members">
                        ${items.map(m => `
                            <div class="team-role-member">
                                <span class="member-initials">${m.name.slice(0, 2).toUpperCase()}</span>
                                <span class="member-name">${m.name}</span>
                                <span class="member-type">(${m.type})</span>
                            </div>
                        `).join('')}
                    </div>
                `;
                teamContainer.appendChild(section);
            }
        });
    }
    
    openModal('projectDetailModal');
}

function openAssignTeamFromDetail() {
    closeModal('projectDetailModal');
    if (currentProjectId) {
        setTimeout(() => openAssignTeamModal(currentProjectId), 300);
    }
}

// ============================================
// Assign Team
// ============================================

function openAssignTeamModal(projectId) {
    const project = currentProjects.find(p => p.id === projectId);
    if (!project) {
        showNotification('Project not found', 'error');
        return;
    }
    
    currentProjectId = projectId;
    document.getElementById('assignProjectTitle').textContent = project.title;
    document.getElementById('teamNameInput').value = project.team_name || `Team for ${project.title}`;
    
    renderTeamMembers(project);
    openModal('assignTeamModal');
}

// ============================================
// Add Member - Updated
// ============================================

function addTeamMember(role) {
    // Set the role
    document.getElementById('addMemberRole').value = role;
    document.getElementById('addMemberProjectId').value = currentProjectId;
    
    // Set role display name
    const roleDisplayMap = {
        'co_mentor': 'CO-MENTOR',
        'advisor': 'ADVISOR',
        'student': 'STUDENT'
    };
    document.getElementById('memberRoleDisplay').value = roleDisplayMap[role] || role.toUpperCase();
    
    // Reset the select
    const select = document.getElementById('memberSelect');
    select.innerHTML = '<option value="">Select a member...</option>';
    destroySlimSelect(select);
    
    // Reset form fields
    document.getElementById('memberResponsibilities').value = '';
    document.getElementById('memberNotes').value = '';
    document.getElementById('memberSelectError').style.display = 'none';
    
    // Load available members based on role
    loadAvailableMembers(role).then(() => {
        // Open modal after loading
        openModal('addMemberModal');
    });
}

function getSelectedMemberId() {
    const select = document.getElementById('memberSelect');
    
    // Try to get from Slim Select first
    if (select.slim) {
        try {
            const selected = select.slim.getSelected();
            if (selected && selected.value) {
                return parseInt(selected.value);
            }
        } catch (e) {
            console.error('Error getting selected from Slim Select:', e);
        }
    }
    
    // Fallback to native select
    return parseInt(select.value);
}

async function confirmAddMember() {
    const projectId = document.getElementById('addMemberProjectId').value;
    const memberId = getSelectedMemberId();
    const role = document.getElementById('addMemberRole').value;
    
    // Determine member type based on role
    let memberType;
    if (role === 'co_mentor' || role === 'advisor') {
        memberType = 'faculty';
    } else if (role === 'student') {
        memberType = 'student';
    } else {
        showNotification('Invalid role', 'error');
        return;
    }
    
    // Validate selection
    if (!memberId || isNaN(memberId)) {
        document.getElementById('memberSelectError').style.display = 'block';
        document.getElementById('memberSelectError').textContent = 'Please select a member';
        showNotification('Please select a member', 'error');
        return;
    }
    
    try {
        const result = await apiRequest('/faculty/api/add-member/', 'POST', {
            project_id: projectId,
            member_id: memberId,
            member_type: memberType,
            role: role
        });
        
        await loadProjects();
        closeAddMemberModal();
        openAssignTeamModal(projectId);
        showNotification(result.message, 'success');
    } catch (error) {
        showNotification('Failed to add member: ' + error.message, 'error');
    }
}

// ============================================
// Remove Member
// ============================================

function openRemoveMemberModal(memberId, memberName) {
    document.getElementById('removeMemberName').textContent = memberName;
    document.getElementById('removeMemberId').value = memberId;
    document.getElementById('removeMemberProjectId').value = currentProjectId;
    openModal('removeMemberModal');
}

async function confirmRemoveMember() {
    const projectId = document.getElementById('removeMemberProjectId').value;
    const memberId = document.getElementById('removeMemberId').value;
    
    // Check if it's an application-based member
    if (typeof memberId === 'string' && memberId.startsWith('app_')) {
        showNotification('Cannot remove application-based member', 'warning');
        closeModal('removeMemberModal');
        return;
    }
    
    try {
        const result = await apiRequest('/faculty/api/remove-member/', 'POST', {
            member_id: memberId,
            project_id: projectId
        });
        
        await loadProjects();
        openAssignTeamModal(projectId);
        showNotification(result.message, 'success');
        closeModal('removeMemberModal');
    } catch (error) {
        showNotification('Failed to remove member: ' + error.message, 'error');
    }
}

// ============================================
// Team Name
// ============================================

async function saveTeamName() {
    const input = document.getElementById('teamNameInput');
    const teamName = input?.value?.trim();
    
    if (!teamName) {
        showNotification('Please enter a team name', 'warning');
        input?.focus();
        return;
    }
    
    try {
        const result = await apiRequest('/faculty/api/update-team-name/', 'POST', {
            project_id: currentProjectId,
            team_name: teamName
        });
        
        showNotification(result.message, 'success');
        const project = currentProjects.find(p => p.id === currentProjectId);
        if (project) project.team_name = teamName;
    } catch (error) {
        showNotification('Failed to update team name: ' + error.message, 'error');
    }
}

// ============================================
// Save Team
// ============================================

function saveTeamAssignment() {
    showNotification('Team updated successfully!', 'success');
    closeModal('assignTeamModal');
    loadProjects();
}

// ============================================
// Utilities
// ============================================

function updateProjectCount() {
    const count = currentProjects?.length || 0;
    const element = document.getElementById('projectCount');
    if (element) {
        element.textContent = `${count} projects`;
    }
}

function refreshData() {
    showNotification('Refreshing data...', 'info');
    loadProjects();
}

// ============================================
// Notifications
// ============================================

function showNotification(message, type = 'success') {
    const map = {
        'success': { id: 'successNotification', msgId: 'notificationMessage' },
        'error': { id: 'errorNotification', msgId: 'errorMessage' },
        'warning': { id: 'warningNotification', msgId: 'warningMessage' },
        'info': { id: 'successNotification', msgId: 'notificationMessage' }
    };
    
    const config = map[type];
    if (!config) return;
    
    const notification = document.getElementById(config.id);
    const msgElement = document.getElementById(config.msgId);
    
    if (notification && msgElement) {
        msgElement.textContent = message;
        notification.style.display = 'flex';
        notification.style.zIndex = '10000';
        
        clearTimeout(notification._timeout);
        notification._timeout = setTimeout(() => {
            notification.style.display = 'none';
        }, 4000);
    }
}

function closeNotification() {
    const el = document.getElementById('successNotification');
    if (el) { el.style.display = 'none'; clearTimeout(el._timeout); }
}

function closeErrorNotification() {
    const el = document.getElementById('errorNotification');
    if (el) { el.style.display = 'none'; clearTimeout(el._timeout); }
}

function closeWarningNotification() {
    const el = document.getElementById('warningNotification');
    if (el) { el.style.display = 'none'; clearTimeout(el._timeout); }
}

// ============================================
// Initialize
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    loadProjects();
    
    // Close modals on overlay click
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.style.display = 'none';
                document.body.style.overflow = '';
            }
        });
    });
    
    // Close modals on Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay').forEach(modal => {
                if (modal.style.display === 'flex') {
                    modal.style.display = 'none';
                    document.body.style.overflow = '';
                }
            });
        }
    });
});