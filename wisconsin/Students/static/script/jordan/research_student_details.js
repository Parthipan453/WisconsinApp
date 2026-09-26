// ============================================
// Research Student Details - Complete JavaScript
// ============================================

let currentProjects = [];
let currentProjectId = null;
let isLoading = false;
let statusCheckInterval = null;

// Pagination variables
const ITEMS_PER_PAGE = 12;
let currentPage = 1;
let totalPages = 1;
let filteredProjects = [];

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
        document.getElementById('paginationContainer').style.display = 'none';
        
        const data = await apiRequest('/student/api/projects/');
        currentProjects = data.projects || [];
        filteredProjects = [...currentProjects];
        
        // Reset to first page when loading new data
        currentPage = 1;
        
        renderProjects();
        updateProjectCount();
        renderPagination();
        
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('projectsGrid').style.display = 'grid';
        document.getElementById('paginationContainer').style.display = 'flex';
        
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
        const data = await apiRequest(`/student/api/project-details/?project_id=${projectId}`);
        return data.data;
    } catch (error) {
        showNotification('Failed to load project details: ' + error.message, 'error');
        throw error;
    }
}

async function checkProjectStatusUpdate(projectId) {
    try {
        const data = await apiRequest(`/student/api/project-status-update/?project_id=${projectId}`);
        return data.data;
    } catch (error) {
        console.error('Failed to check status update:', error);
        return null;
    }
}

// ============================================
// RENDER FUNCTIONS
// ============================================

function renderProjects() {
    const grid = document.getElementById('projectsGrid');
    grid.innerHTML = '';
    
    if (!filteredProjects || filteredProjects.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="ti ti-folder-open"></i>
                <h3>No projects found</h3>
                <p>You haven't been accepted into any research projects yet.</p>
            </div>
        `;
        grid.style.display = 'block';
        document.getElementById('paginationContainer').style.display = 'none';
        return;
    }
    
    grid.style.display = 'grid';
    
    // Calculate pagination
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = Math.min(startIndex + ITEMS_PER_PAGE, filteredProjects.length);
    const pageProjects = filteredProjects.slice(startIndex, endIndex);
    
    pageProjects.forEach((project, index) => {
        const card = document.createElement('div');
        card.className = 'project-card';
        card.style.animationDelay = `${(index % 12) * 0.05}s`;
        card.onclick = function() { viewProjectDetails(project.id); };
        
        const teamCount = project.team_members ? project.team_members.length : 0;
        
        let teamAvatars = '';
        const displayMembers = project.team_members ? project.team_members.slice(0, 4) : [];
        const remaining = teamCount - 4;
        
        if (teamCount === 0) {
            teamAvatars = '<span class="no-team">No team assigned</span>';
        } else {
            displayMembers.forEach(member => {
                const isMentor = member.role === 'mentor';
                teamAvatars += `
                    <div class="team-avatar-small ${isMentor ? 'mentor-avatar' : ''}" title="${member.name} - ${member.role_display}">
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
        
        const statusClass = project.project_status || project.status || 'draft';
        const statusDisplay = project.project_status_display || project.status_display || 'Draft';
        
        card.innerHTML = `
            <div class="card-header">
                <div class="card-title-section">
                    <h4 class="project-title">${escapeHtml(project.title)}</h4>
                    <span class="status-badge ${statusClass}">${statusDisplay}</span>
                </div>
            </div>

            <div class="card-body">
                <p class="project-description">${project.description ? escapeHtml(project.description.substring(0, 120)) : ''}${project.description && project.description.length > 120 ? '...' : ''}</p>
                
                <div class="project-meta">
                    <span><i class="ti ti-calendar"></i> ${project.start_date ? new Date(project.start_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Not set'}</span>
                    <span><i class="ti ti-building"></i> ${escapeHtml(project.department)}</span>
                    <span><i class="ti ti-user"></i> ${teamCount} Members</span>
                </div>

                ${project.mentor ? `
                    <div class="mentor-badge-small">
                        <i class="ti ti-star"></i> Mentor: ${escapeHtml(project.mentor.name)}
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

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// PAGINATION FUNCTIONS
// ============================================

function renderPagination() {
    const totalItems = filteredProjects.length;
    totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);
    
    const container = document.getElementById('paginationContainer');
    const infoSpan = document.getElementById('paginationInfo');
    const numbersContainer = document.getElementById('paginationNumbers');
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    
    if (totalItems === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'flex';
    
    // Update info
    const start = (currentPage - 1) * ITEMS_PER_PAGE + 1;
    const end = Math.min(currentPage * ITEMS_PER_PAGE, totalItems);
    infoSpan.textContent = `Showing ${start}-${end} of ${totalItems} projects`;
    
    // Update buttons
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === totalPages;
    
    // Render page numbers
    numbersContainer.innerHTML = '';
    
    // Always show first page
    numbersContainer.appendChild(createPageButton(1));
    
    if (totalPages <= 7) {
        // Show all pages
        for (let i = 2; i <= totalPages; i++) {
            numbersContainer.appendChild(createPageButton(i));
        }
    } else {
        // Show pages with ellipsis
        if (currentPage <= 4) {
            // Show 1, 2, 3, 4, 5, ..., last
            for (let i = 2; i <= 5; i++) {
                numbersContainer.appendChild(createPageButton(i));
            }
            numbersContainer.appendChild(createEllipsis());
            numbersContainer.appendChild(createPageButton(totalPages));
        } else if (currentPage >= totalPages - 3) {
            // Show 1, ..., last-4, last-3, last-2, last-1, last
            numbersContainer.appendChild(createEllipsis());
            for (let i = totalPages - 4; i <= totalPages; i++) {
                numbersContainer.appendChild(createPageButton(i));
            }
        } else {
            // Show 1, ..., current-1, current, current+1, ..., last
            numbersContainer.appendChild(createEllipsis());
            for (let i = currentPage - 1; i <= currentPage + 1; i++) {
                numbersContainer.appendChild(createPageButton(i));
            }
            numbersContainer.appendChild(createEllipsis());
            numbersContainer.appendChild(createPageButton(totalPages));
        }
    }
}

function createPageButton(pageNum) {
    const btn = document.createElement('button');
    btn.className = `page-number ${pageNum === currentPage ? 'active' : ''}`;
    btn.textContent = pageNum;
    btn.onclick = function() { goToPage(pageNum); };
    return btn;
}

function createEllipsis() {
    const span = document.createElement('span');
    span.className = 'page-number ellipsis';
    span.textContent = '…';
    return span;
}

function goToPage(pageNum) {
    if (pageNum < 1 || pageNum > totalPages || pageNum === currentPage) return;
    currentPage = pageNum;
    renderProjects();
    renderPagination();
    // Scroll to top of grid
    document.getElementById('projectsGrid').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function changePage(direction) {
    if (direction === 'prev' && currentPage > 1) {
        goToPage(currentPage - 1);
    } else if (direction === 'next' && currentPage < totalPages) {
        goToPage(currentPage + 1);
    }
}

// ============================================
// VIEW PROJECT DETAILS (Modal)
// ============================================

async function viewProjectDetails(projectId) {
    try {
        currentProjectId = projectId;
        const data = await loadProjectDetails(projectId);
        renderProjectDetails(data);
        openModal('projectDetailModal');
        
        // Start checking for status updates
        startStatusPolling(projectId);
    } catch (error) {
        showNotification('Failed to load project details: ' + error.message, 'error');
    }
}

function renderProjectDetails(data) {
    // Basic Info
    document.getElementById('detailTitle').textContent = data.title;
    document.getElementById('detailStatus').textContent = data.project_status_display || data.status_display || 'Draft';
    const statusClass = data.project_status || data.status || 'draft';
    document.getElementById('detailStatus').className = `status-badge ${statusClass}`;
    document.getElementById('detailDescription').textContent = data.description || 'No description available.';
    document.getElementById('detailCategory').textContent = data.category || 'Not specified';
    
    // Dates
    document.getElementById('detailStartDate').textContent = data.start_date ? formatDate(data.start_date) : 'Not set';
    document.getElementById('detailEndDate').textContent = data.end_date ? formatDate(data.end_date) : 'Not set';
    
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
    
    // Reference Link
    const linkEl = document.getElementById('detailLink');
    if (data.reference_link) {
        linkEl.innerHTML = `<a href="${data.reference_link}" target="_blank">${data.reference_link}</a>`;
    } else {
        linkEl.textContent = 'No reference link';
    }
    
    document.getElementById('detailNotes').textContent = data.additional_notes || 'No additional notes.';
    
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
        'student': 'Students'
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
                membersHTML += `
                    <div class="team-member-chip ${roleColors[roleKey]}">
                        <span class="member-initials">${m.name.slice(0, 2).toUpperCase()}</span>
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
    document.getElementById('modalOverallProgressText').textContent = `${data.overall_progress || 0}%`;
    document.getElementById('modalOverallProgressBar').style.width = `${data.overall_progress || 0}%`;
}

function formatDate(dateStr) {
    if (!dateStr) return 'Not set';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

// ============================================
// STATUS POLLING (Real-time updates)
// ============================================

function startStatusPolling(projectId) {
    stopStatusPolling();
    
    statusCheckInterval = setInterval(async () => {
        try {
            const statusData = await checkProjectStatusUpdate(projectId);
            if (statusData) {
                updateStatusBadge(statusData);
            }
        } catch (error) {
            console.debug('Status polling error:', error);
        }
    }, 10000);
}

function stopStatusPolling() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
        statusCheckInterval = null;
    }
}

function updateStatusBadge(statusData) {
    const statusBadge = document.getElementById('detailStatus');
    if (statusBadge) {
        const currentStatus = statusBadge.className.split(' ').find(cls => 
            ['draft', 'pending', 'approved', 'rejected', 'ongoing', 'on_hold', 'completed', 'cancelled', 'archived'].includes(cls)
        );
        
        if (currentStatus !== statusData.status) {
            statusBadge.textContent = statusData.status_display;
            statusBadge.className = `status-badge ${statusData.status}`;
            showNotification(`Project status updated to: ${statusData.status_display}`, 'info');
            loadProjects();
        }
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
        'success': { id: 'successNotification', msgId: 'notificationMessage', icon: 'ti ti-check-circle' },
        'error': { id: 'errorNotification', msgId: 'errorMessage', icon: 'ti ti-exclamation-circle' },
        'warning': { id: 'warningNotification', msgId: 'warningMessage', icon: 'ti ti-alert-circle' },
        'info': { id: 'successNotification', msgId: 'notificationMessage', icon: 'ti ti-info-circle' }
    };
    
    const config = map[type];
    if (!config) return;
    
    const notification = document.getElementById(config.id);
    if (!notification) return;
    
    document.getElementById(config.msgId).textContent = message;
    const icon = notification.querySelector('.notification-icon');
    if (icon) icon.className = `notification-icon ${config.icon}`;
    
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
        stopStatusPolling();
    }
}

// ============================================
// KEYBOARD SHORTCUTS
// ============================================

document.addEventListener('keydown', function(e) {
    // Close modal with Escape
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay').forEach(modal => {
            if (modal.style.display === 'flex') {
                modal.style.display = 'none';
                document.body.style.overflow = '';
                stopStatusPolling();
            }
        });
    }
    
    // Arrow keys for pagination
    if (e.key === 'ArrowLeft' && currentPage > 1) {
        changePage('prev');
    }
    if (e.key === 'ArrowRight' && currentPage < totalPages) {
        changePage('next');
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
                stopStatusPolling();
            }
        });
    });
});

// ============================================
// EXPOSE FUNCTIONS GLOBALLY
// ============================================

window.viewProjectDetails = viewProjectDetails;
window.refreshData = refreshData;
window.goToPage = goToPage;
window.changePage = changePage;
window.closeModal = closeModal;
window.closeNotification = closeNotification;
window.closeErrorNotification = closeErrorNotification;
window.closeWarningNotification = closeWarningNotification;