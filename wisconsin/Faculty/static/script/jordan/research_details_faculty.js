// ============================================
// Research Faculty Details - Complete JavaScript
// ============================================

let currentProjects = [];
let currentProjectId = null;
let isLoading = false;
let statusOptions = [];
let currentProjectStatus = '';
let selectedStatus = null;
let isDropdownOpen = false;

// ============================================
// API FUNCTIONS
// ============================================

function getCSRFToken() {
    return document.getElementById('csrfToken')?.value || '';
}

async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    };
    if (data) options.body = JSON.stringify(data);
    
    try {
        const response = await fetch(url, options);
        const result = await response.json();
        if (!result.success) throw new Error(result.error || 'An error occurred');
        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ============================================
// LOAD DATA
// ============================================

async function loadProjects() {
    if (isLoading) return;
    isLoading = true;
    
    try {
        document.getElementById('loadingState').style.display = 'block';
        document.getElementById('projectsGrid').style.display = 'none';
        
        const data = await apiRequest('/faculty/api/faculty-projects/');
        currentProjects = data.projects;
        renderProjects(currentProjects);
        updateProjectCount();
        
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('projectsGrid').style.display = 'grid';
        
    } catch (error) {
        showNotification('Failed to load projects: ' + error.message, 'error');
        document.getElementById('loadingState').innerHTML = `
            <i class="ti ti-alert-circle" style="font-size: 48px; color: var(--primary-red);"></i>
            <h3 style="margin-top: 16px; color: var(--text-secondary);">Failed to load projects</h3>
            <p style="color: var(--text-light);">${error.message}</p>
            <button class="btn btn-primary" onclick="refreshData()" style="margin-top: 16px;">
                <i class="ti ti-refresh"></i> Try Again
            </button>
        `;
    } finally {
        isLoading = false;
    }
}

async function loadProjectDetails(projectId) {
    try {
        const data = await apiRequest(`/faculty/api/project-details-modal/?project_id=${projectId}`);
        return data.data;
    } catch (error) {
        showNotification('Failed to load project details: ' + error.message, 'error');
        throw error;
    }
}

async function loadStatusOptions() {
    try {
        const data = await apiRequest('/faculty/api/project-status-options/');
        statusOptions = data.status_options;
        return statusOptions;
    } catch (error) {
        console.error('Failed to load status options:', error);
        return [];
    }
}

async function updateProjectStatus(projectId, status) {
    try {
        const data = await apiRequest('/faculty/api/update-project-status/', 'POST', {
            project_id: projectId,
            status: status
        });
        return data;
    } catch (error) {
        throw error;
    }
}

// ============================================
// CUSTOM STATUS DROPDOWN FUNCTIONS
// ============================================

function populateStatusDropdown(currentStatus) {
    const container = document.getElementById('statusOptionsContainer');
    container.innerHTML = '';
    
    if (!statusOptions || statusOptions.length === 0) {
        container.innerHTML = '<div class="custom-select-option" style="color: #9ca3af; cursor: default;">No options available</div>';
        return;
    }
    
    statusOptions.forEach(option => {
        const optionDiv = document.createElement('div');
        optionDiv.className = 'custom-select-option';
        if (option.value === currentStatus) {
            optionDiv.classList.add('selected');
            selectedStatus = option.value;
            // Update placeholder
            document.getElementById('statusPlaceholder').textContent = option.label;
            document.getElementById('statusPlaceholder').classList.remove('placeholder');
        }
        
        const dotColor = option.value.toLowerCase().replace(' ', '-');
        optionDiv.innerHTML = `
            <span>
                <span class="status-dot ${dotColor}"></span>
                ${option.label}
            </span>
            <span class="option-check"><i class="ti ti-check"></i></span>
        `;
        
        optionDiv.onclick = function(e) {
            e.stopPropagation();
            selectStatusOption(option.value, option.label);
        };
        
        container.appendChild(optionDiv);
    });
}

function selectStatusOption(value, label) {
    // Update selected status
    selectedStatus = value;
    
    // Update placeholder
    const placeholder = document.getElementById('statusPlaceholder');
    placeholder.textContent = label;
    placeholder.classList.remove('placeholder');
    
    // Update options
    document.querySelectorAll('.custom-select-option').forEach(opt => {
        opt.classList.remove('selected');
        if (opt.querySelector('span').textContent.trim() === label) {
            opt.classList.add('selected');
        }
    });
    
    // Close dropdown
    closeStatusDropdown();
}

function toggleStatusDropdown() {
    if (isDropdownOpen) {
        closeStatusDropdown();
    } else {
        openStatusDropdown();
    }
}

function openStatusDropdown() {
    const dropdown = document.getElementById('statusDropdown');
    const trigger = document.querySelector('.custom-select-trigger');
    dropdown.style.display = 'block';
    trigger.classList.add('active');
    isDropdownOpen = true;
}

function closeStatusDropdown() {
    const dropdown = document.getElementById('statusDropdown');
    const trigger = document.querySelector('.custom-select-trigger');
    dropdown.style.display = 'none';
    trigger.classList.remove('active');
    isDropdownOpen = false;
}

function getSelectedStatusValue() {
    return selectedStatus;
}

// ============================================
// RENDER FUNCTIONS
// ============================================

function renderProjects(projects) {
    const grid = document.getElementById('projectsGrid');
    grid.innerHTML = '';
    
    if (!projects || projects.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="ti ti-folder-open"></i>
                <h3>No projects found</h3>
                <p>You haven't posted any research opportunities yet.</p>
            </div>
        `;
        grid.style.display = 'block';
        return;
    }
    
    grid.style.display = 'grid';
    
    projects.forEach(project => {
        const card = document.createElement('div');
        card.className = 'project-card';
        card.onclick = function() { viewProjectDetails(project.id); };
        
        const teamCount = project.team_members ? project.team_members.length : 0;
        
        let teamAvatars = '';
        const displayMembers = project.team_members ? project.team_members.slice(0, 4) : [];
        const remaining = teamCount - 4;
        
        if (teamCount === 0) {
            teamAvatars = '<span class="no-team">No team assigned</span>';
        } else {
            displayMembers.forEach(member => {
                const isMentor = member.is_mentor || false;
                teamAvatars += `
                    <div class="team-avatar-small ${isMentor ? 'mentor-avatar' : ''}" 
                         title="${member.name} - ${member.role_display}${isMentor ? ' (Mentor)' : ''}">
                        <span>${member.name.slice(0, 2).toUpperCase()}</span>
                    </div>
                `;
            });
            if (remaining > 0) {
                teamAvatars += `
                    <div class="team-avatar-small more">
                        <span>+${remaining}</span>
                    </div>
                `;
            }
        }
        
        const statusClass = project.project_status || 'draft';
        const statusDisplay = project.project_status_display || 'Draft';
        
        card.innerHTML = `
            <div class="card-header">
                <div class="card-title-section">
                    <h4 class="project-title">${project.title}</h4>
                    <span class="status-badge ${statusClass}">${statusDisplay}</span>
                </div>
            </div>

            <div class="card-body">
                <p class="project-description">${project.description ? project.description.substring(0, 120) : ''}${project.description && project.description.length > 120 ? '...' : ''}</p>
                
                <div class="project-meta">
                    <span><i class="ti ti-calendar"></i> ${project.start_date ? new Date(project.start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Not set'}</span>
                    <span><i class="ti ti-building"></i> ${project.department}</span>
                    <span><i class="ti ti-user"></i> ${teamCount} Members</span>
                </div>

                ${project.mentor ? `
                    <div class="mentor-badge-small">
                        <i class="ti ti-star"></i> Mentor: ${project.mentor.name}
                    </div>
                ` : ''}

                <div class="team-preview">
                    <span class="team-preview-label"><i class="ti ti-users"></i> Team:</span>
                    <div class="team-avatars">
                        ${teamAvatars}
                    </div>
                </div>
            </div>

            <div class="card-footer">
                <button class="btn-view-details" onclick="event.stopPropagation(); viewProjectDetails('${project.id}')">
                    <i class="ti ti-eye"></i> View Details
                </button>
            </div>
        `;
        grid.appendChild(card);
    });
}

// ============================================
// VIEW PROJECT DETAILS (Modal)
// ============================================

async function viewProjectDetails(projectId) {
    try {
        currentProjectId = projectId;
        const data = await loadProjectDetails(projectId);
        currentProjectStatus = data.project_status || 'draft';
        renderProjectDetails(data);
        
        // Load status options for the editor
        await loadStatusOptions();
        populateStatusDropdown(currentProjectStatus);
        
        openModal('projectDetailModal');
    } catch (error) {
        showNotification('Failed to load project details: ' + error.message, 'error');
    }
}

function renderProjectDetails(data) {
    // Basic Info
    document.getElementById('detailTitle').textContent = data.title;
    document.getElementById('detailStatus').textContent = data.project_status_display || 'Draft';
    const statusClass = data.project_status || 'draft';
    document.getElementById('detailStatus').className = `status-badge ${statusClass}`;
    document.getElementById('detailDescription').textContent = data.description || 'No description available.';
    document.getElementById('detailCategory').textContent = data.category || 'Not specified';
    
    // Dates
    document.getElementById('detailStartDate').textContent = data.start_date ? formatDate(data.start_date) : 'Not set';
    document.getElementById('detailEndDate').textContent = data.end_date ? formatDate(data.end_date) : 'Not set';
    document.getElementById('detailSlots').textContent = data.available_slots || 'Not specified';
    document.getElementById('detailEstimatedAmount').textContent = data.estimated_amount ? `$${data.estimated_amount}` : 'Not specified';
    
    // Skills
    const skillsContainer = document.getElementById('detailSkills');
    skillsContainer.innerHTML = '';
    if (data.skill_list && data.skill_list.length > 0) {
        data.skill_list.forEach(skill => {
            const tag = document.createElement('span');
            tag.className = 'skill-tag';
            tag.textContent = skill;
            skillsContainer.appendChild(tag);
        });
    } else {
        skillsContainer.innerHTML = '<span style="color: var(--text-light);">No skills specified</span>';
    }
    
    // Team Name
    document.getElementById('detailTeamName').textContent = data.team_name || 'Team Name';
    
    // Team Members by Role
    const teamContainer = document.getElementById('detailTeamMembers');
    teamContainer.innerHTML = '';
    
    const roleOrder = ['mentor', 'co_mentor', 'advisor', 'student'];
    const roleLabels = {
        'mentor': 'Mentor',
        'co_mentor': 'Co-Mentor',
        'advisor': 'Advisor',
        'student': 'Student'
    };
    const roleColors = {
        'mentor': 'mentor',
        'co_mentor': 'co-mentor',
        'advisor': 'advisor',
        'student': 'student'
    };
    
    let hasMembers = false;
    
    roleOrder.forEach(roleKey => {
        const members = data.team_by_role[roleKey] || [];
        if (members.length > 0) {
            hasMembers = true;
            const section = document.createElement('div');
            section.className = 'team-role-section';
            
            let membersHTML = '';
            members.forEach(m => {
                const initials = m.name.slice(0, 2).toUpperCase();
                membersHTML += `
                    <div class="team-member-chip ${roleColors[roleKey]}">
                        <span class="member-initials">${initials}</span>
                        <span class="member-name">${m.name}</span>
                        ${m.email ? `<span class="member-email">${m.email}</span>` : ''}
                        <span class="member-role-badge">${m.role}</span>
                    </div>
                `;
            });
            
            section.innerHTML = `
                <div class="team-role-label">
                    <i class="ti ti-users"></i>
                    ${roleLabels[roleKey]}
                    <span class="team-role-count">${members.length}</span>
                </div>
                <div class="team-role-members">
                    ${membersHTML}
                </div>
            `;
            teamContainer.appendChild(section);
        }
    });
    
    if (!hasMembers) {
        teamContainer.innerHTML = '<p class="empty-message">No team members assigned</p>';
    }
    
    // Progress
    renderModalProgress(data.overall_progress || 0);
}

function renderModalProgress(overall) {
    document.getElementById('modalOverallProgressText').textContent = `${overall}%`;
    document.getElementById('modalOverallProgressBar').style.width = `${overall}%`;
}

function formatDate(dateStr) {
    if (!dateStr) return 'Not set';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

// ============================================
// STATUS MANAGEMENT
// ============================================

function openStatusEditor() {
    const editor = document.getElementById('statusEditor');
    const statusBadge = document.getElementById('detailStatus');
    
    // Close any existing status editors first
    closeStatusEditor();
    
    // Reset selected status
    selectedStatus = currentProjectStatus;
    
    // Update the dropdown with current status
    populateStatusDropdown(currentProjectStatus);
    
    // Show the editor
    editor.style.display = 'block';
    statusBadge.style.display = 'none';
}

function closeStatusEditor() {
    const editor = document.getElementById('statusEditor');
    const statusBadge = document.getElementById('detailStatus');
    
    editor.style.display = 'none';
    statusBadge.style.display = 'inline-block';
    
    // Close dropdown if open
    closeStatusDropdown();
}

async function saveProjectStatus() {
    const selectedValue = getSelectedStatusValue();
    
    if (!selectedValue) {
        showNotification('Please select a status', 'warning');
        return;
    }
    
    try {
        const result = await updateProjectStatus(currentProjectId, selectedValue);
        
        // Update the status badge
        const statusBadge = document.getElementById('detailStatus');
        statusBadge.textContent = result.data.status_display;
        statusBadge.className = `status-badge ${result.data.status}`;
        
        // Update the stored current status
        currentProjectStatus = result.data.status;
        
        // Close the editor
        closeStatusEditor();
        
        // Refresh the projects list to update cards
        await loadProjects();
        
        showNotification(result.message, 'success');
        
    } catch (error) {
        showNotification('Failed to update status: ' + error.message, 'error');
    }
}

// ============================================
// UPDATE PROJECT COUNT
// ============================================

function updateProjectCount() {
    const count = currentProjects ? currentProjects.length : 0;
    const element = document.getElementById('projectCount');
    if (element) {
        element.textContent = `${count} projects`;
    }
}

// ============================================
// REFRESH
// ============================================

function refreshData() {
    showNotification('Refreshing data...', 'info');
    loadProjects();
}

// ============================================
// NOTIFICATIONS
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
    if (!notification) return;
    
    document.getElementById(config.msgId).textContent = message;
    notification.style.display = 'flex';
    
    clearTimeout(notification._timeout);
    notification._timeout = setTimeout(() => { notification.style.display = 'none'; }, 4000);
}

function closeNotification() {
    const n = document.getElementById('successNotification');
    if (n) { n.style.display = 'none'; clearTimeout(n._timeout); }
}

function closeErrorNotification() {
    const n = document.getElementById('errorNotification');
    if (n) { n.style.display = 'none'; clearTimeout(n._timeout); }
}

function closeWarningNotification() {
    const n = document.getElementById('warningNotification');
    if (n) { n.style.display = 'none'; clearTimeout(n._timeout); }
}

// ============================================
// MODAL FUNCTIONS
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
        // Close status editor if open
        closeStatusEditor();
    }
}

// ============================================
// CLICK OUTSIDE HANDLER
// ============================================

// Close dropdown when clicking outside
document.addEventListener('click', function(e) {
    const customSelect = document.getElementById('customStatusSelect');
    if (customSelect && !customSelect.contains(e.target)) {
        closeStatusDropdown();
    }
});

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    loadProjects();

    // Close modal on overlay click
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.style.display = 'none';
                document.body.style.overflow = '';
                closeStatusEditor();
            }
        });
    });
    
    // Close modal on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay').forEach(modal => {
                if (modal.style.display === 'flex') {
                    modal.style.display = 'none';
                    document.body.style.overflow = '';
                    closeStatusEditor();
                }
            });
        }
    });
});