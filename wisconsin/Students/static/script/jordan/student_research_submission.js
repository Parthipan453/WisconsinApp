// ============================================
// Student Research Submission - JavaScript
// ============================================

let currentProjects = [];
let filteredProjects = [];
let isLoading = false;
let currentSubmissionId = null;

// Pagination variables
const ITEMS_PER_PAGE = 12;
let currentPage = 1;
let totalPages = 1;

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
        
        const data = await apiRequest('/student/api/student-research-projects-with-submissions/');
        currentProjects = data.projects || [];
        filteredProjects = [...currentProjects];
        
        // Reset to first page
        currentPage = 1;
        
        renderProjects();
        updateStats(currentProjects);
        
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('projectsGrid').style.display = 'grid';
        
    } catch (error) {
        showNotification('Failed to load projects: ' + error.message, 'error');
        document.getElementById('loadingState').innerHTML = `
            <i class="ti ti-alert-circle" style="font-size: 48px; color: var(--primary-red);"></i>
            <h3 style="margin-top: 16px; color: var(--text-secondary);">Failed to load projects</h3>
            <p style="color: var(--text-light);">${error.message}</p>
            <button class="btn-refresh" onclick="refreshData()" style="margin-top: 16px;">
                <i class="ti ti-refresh"></i> Try Again
            </button>
        `;
    } finally {
        isLoading = false;
    }
}

async function loadProjectSubmission(projectId) {
    try {
        const data = await apiRequest(`/student/api/student-project-submission/?project_id=${projectId}`);
        return data;
    } catch (error) {
        showNotification('Failed to load submission: ' + error.message, 'error');
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
                <p>You are not part of any research projects yet.</p>
            </div>
        `;
        grid.style.display = 'block';
        document.getElementById('paginationContainer').style.display = 'none';
        return;
    }
    
    grid.style.display = 'grid';
    
    // Calculate pagination
    totalPages = Math.ceil(filteredProjects.length / ITEMS_PER_PAGE);
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = Math.min(startIndex + ITEMS_PER_PAGE, filteredProjects.length);
    const pageProjects = filteredProjects.slice(startIndex, endIndex);
    
    // Show pagination
    renderPagination();
    
    pageProjects.forEach((project, index) => {
        const card = document.createElement('div');
        card.className = 'project-card';
        card.style.animationDelay = `${(index % 12) * 0.05}s`;
        
        const statusClass = project.project_status || 'draft';
        const statusDisplay = project.project_status_display || 'Draft';
        
        const startDate = project.start_date ? new Date(project.start_date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        }) : 'Not set';
        
        const endDate = project.end_date ? new Date(project.end_date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        }) : 'Not set';
        
        const category = project.category || 'Not specified';
        const department = project.department || 'Not specified';
        
        // Submission preview
        let submissionHtml = '';
        if (project.has_submission && project.submission) {
            const subStatus = project.submission.status || 'draft';
            const subStatusDisplay = project.submission.status_display || 'Draft';
            const subTitle = project.submission.title || 'Submission';
            submissionHtml = `
                <div class="submission-preview">
                    <i class="ti ti-file-text"></i>
                    <span class="submission-title">${escapeHtml(subTitle)}</span>
                    <span class="status-badge ${subStatus}">${escapeHtml(subStatusDisplay)}</span>
                </div>
            `;
        } else if (project.has_publication) {
            submissionHtml = `
                <div class="no-submission">
                    <i class="ti ti-file-text"></i>
                    <span>Publication exists, no submission yet</span>
                </div>
            `;
        } else {
            submissionHtml = `
                <div class="no-submission">
                    <i class="ti ti-file-off"></i>
                    <span>No submission yet</span>
                </div>
            `;
        }
        
        card.innerHTML = `
            <div class="card-header">
                <div class="card-title-section">
                    <h4 class="project-title">${escapeHtml(project.title)}</h4>
                    <span class="status-badge ${statusClass}">${escapeHtml(statusDisplay)}</span>
                </div>
            </div>
            
            <div class="card-body">
                <p class="project-description">${escapeHtml(project.description ? project.description.substring(0, 120) : 'No description available')}${project.description && project.description.length > 120 ? '...' : ''}</p>
                
                <div class="project-details-grid">
                    <div class="detail-item">
                        <i class="ti ti-tag"></i>
                        <div class="detail-info">
                            <span class="detail-label">Category</span>
                            <span class="detail-value">${escapeHtml(category)}</span>
                        </div>
                    </div>
                    <div class="detail-item">
                        <i class="ti ti-building"></i>
                        <div class="detail-info">
                            <span class="detail-label">Department</span>
                            <span class="detail-value">${escapeHtml(department)}</span>
                        </div>
                    </div>
                    <div class="detail-item">
                        <i class="ti ti-calendar"></i>
                        <div class="detail-info">
                            <span class="detail-label">Start Date</span>
                            <span class="detail-value">${startDate}</span>
                        </div>
                    </div>
                    <div class="detail-item">
                        <i class="ti ti-calendar-end"></i>
                        <div class="detail-info">
                            <span class="detail-label">End Date</span>
                            <span class="detail-value">${endDate}</span>
                        </div>
                    </div>
                </div>
                
                ${submissionHtml}
            </div>
            
            <div class="card-footer">
                ${project.has_submission ? `
                    <button class="btn btn-view-submission" onclick="event.stopPropagation(); viewSubmissionDetails('${project.id}')">
                        <i class="ti ti-eye"></i> View Submission
                    </button>
                ` : (project.has_publication ? `
                    <button class="btn btn-view-details" onclick="event.stopPropagation(); viewSubmissionDetails('${project.id}')">
                        <i class="ti ti-eye"></i> View Publication
                    </button>
                ` : `
                    <button class="btn btn-view-details" onclick="event.stopPropagation(); showNotification('No publication available for this project yet', 'warning')">
                        <i class="ti ti-eye"></i> View Details
                    </button>
                `)}
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
    
    if (!container) return;
    
    // Hide pagination if no items or only one page
    if (totalItems === 0 || totalPages <= 1) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'flex';
    
    // Update info text
    const start = (currentPage - 1) * ITEMS_PER_PAGE + 1;
    const end = Math.min(currentPage * ITEMS_PER_PAGE, totalItems);
    infoSpan.textContent = `Showing ${start}-${end} of ${totalItems} projects`;
    
    // Update prev/next buttons
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === totalPages;
    
    // Update button click handlers
    prevBtn.onclick = function() { changePage('prev'); };
    nextBtn.onclick = function() { changePage('next'); };
    
    // Render page numbers
    numbersContainer.innerHTML = '';
    
    if (totalPages <= 7) {
        // Show all pages
        for (let i = 1; i <= totalPages; i++) {
            numbersContainer.appendChild(createPageButton(i));
        }
    } else {
        // Show pages with ellipsis
        if (currentPage <= 4) {
            for (let i = 1; i <= 5; i++) {
                numbersContainer.appendChild(createPageButton(i));
            }
            numbersContainer.appendChild(createEllipsis());
            numbersContainer.appendChild(createPageButton(totalPages));
        } else if (currentPage >= totalPages - 3) {
            numbersContainer.appendChild(createPageButton(1));
            numbersContainer.appendChild(createEllipsis());
            for (let i = totalPages - 4; i <= totalPages; i++) {
                numbersContainer.appendChild(createPageButton(i));
            }
        } else {
            numbersContainer.appendChild(createPageButton(1));
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
    // Scroll to top of grid
    const grid = document.getElementById('projectsGrid');
    if (grid) {
        grid.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function changePage(direction) {
    if (direction === 'prev' && currentPage > 1) {
        goToPage(currentPage - 1);
    } else if (direction === 'next' && currentPage < totalPages) {
        goToPage(currentPage + 1);
    }
}

function updateStats(projects) {
    const total = projects.length;
    const withSubmission = projects.filter(p => p.has_submission).length;
    const pending = projects.filter(p => p.has_submission && p.submission && 
        ['under_review', 'submitted', 'resubmitted'].includes(p.submission.status)).length;
    const published = projects.filter(p => p.has_submission && p.submission && 
        ['published', 'accepted'].includes(p.submission.status)).length;
    
    document.getElementById('totalProjects').textContent = total;
    document.getElementById('totalSubmissions').textContent = withSubmission;
    document.getElementById('pendingCount').textContent = pending;
    document.getElementById('publishedCount').textContent = published;
}

// ============================================
// VIEW SUBMISSION DETAILS
// ============================================

async function viewSubmissionDetails(projectId) {
    try {
        const data = await loadProjectSubmission(projectId);
        if (!data || !data.submission) {
            showNotification('No submission found for this project', 'warning');
            return;
        }
        
        const sub = data.submission;
        currentSubmissionId = sub.id;
        
        // Project Info
        document.getElementById('detailProjectTitle').textContent = data.project_title || 'N/A';
        document.getElementById('detailProjectCategory').textContent = data.project_category || 'N/A';
        document.getElementById('detailProjectDepartment').textContent = data.project_department || 'N/A';
        
        // Submission Info
        document.getElementById('detailTitle').textContent = sub.title || 'Untitled';
        document.getElementById('detailStatus').textContent = sub.status_display || 'Draft';
        document.getElementById('detailStatus').className = `project-badge ${sub.status || 'draft'}`;
        document.getElementById('detailType').textContent = sub.type_display || sub.publication_type || 'N/A';
        document.getElementById('detailJournal').textContent = sub.journal_name || sub.conference_name || 'N/A';
        document.getElementById('detailPublisher').textContent = sub.publisher || 'N/A';
        document.getElementById('detailAbstract').textContent = sub.abstract || 'No abstract provided.';
        document.getElementById('detailManuscript').textContent = sub.manuscript_number || 'N/A';
        
        // Keywords
        const keywordsContainer = document.getElementById('detailKeywords');
        keywordsContainer.innerHTML = '';
        if (sub.keywords) {
            const keywords = sub.keywords.split(',').map(k => k.trim()).filter(k => k);
            keywords.forEach(keyword => {
                const tag = document.createElement('span');
                tag.className = 'keyword-tag';
                tag.textContent = keyword;
                keywordsContainer.appendChild(tag);
            });
        } else {
            keywordsContainer.innerHTML = '<span style="color: var(--text-light);">No keywords specified</span>';
        }
        
        // Authors
        const authorsContainer = document.getElementById('detailAuthors');
        authorsContainer.innerHTML = '';
        if (sub.authors && sub.authors.length > 0) {
            sub.authors.forEach(author => {
                const div = document.createElement('div');
                div.className = 'author-item';
                const roleMap = {
                    'First Author': 'first',
                    'Corresponding Author': 'corresponding',
                    'Co Author': 'co_author'
                };
                const roleClass = roleMap[author.role] || 'co_author';
                div.innerHTML = `
                    <span class="author-name"><i class="ti ti-user"></i> ${escapeHtml(author.name)}</span>
                    <span class="author-role-badge ${roleClass}">${escapeHtml(author.role)}</span>
                `;
                authorsContainer.appendChild(div);
            });
        } else {
            authorsContainer.innerHTML = '<p style="color: var(--text-light);">No authors assigned</p>';
        }
        
        // Dates
        document.getElementById('detailSubmissionDate').textContent = sub.submission_date ? new Date(sub.submission_date).toLocaleDateString() : 'N/A';
        document.getElementById('detailAcceptanceDate').textContent = sub.acceptance_date ? new Date(sub.acceptance_date).toLocaleDateString() : 'N/A';
        document.getElementById('detailPublicationDate').textContent = sub.publication_date ? new Date(sub.publication_date).toLocaleDateString() : 'N/A';
        
        // Identifiers
        document.getElementById('detailDoi').textContent = sub.doi || 'N/A';
        if (sub.publication_url) {
            document.getElementById('detailUrl').innerHTML = `<a href="${sub.publication_url}" target="_blank">${sub.publication_url}</a>`;
        } else {
            document.getElementById('detailUrl').textContent = 'N/A';
        }
        
        openModal('submissionDetailModal');
        
    } catch (error) {
        showNotification('Failed to load submission details: ' + error.message, 'error');
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
    
    const messageEl = document.getElementById(config.msgId);
    if (messageEl) messageEl.textContent = message;
    
    const icon = notification.querySelector('.notification-icon');
    if (icon) icon.className = `notification-icon ${config.icon}`;
    
    notification.style.display = 'flex';
    clearTimeout(notification._timeout);
    notification._timeout = setTimeout(() => { 
        notification.style.display = 'none'; 
    }, 4000);
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
            }
        });
    }
    
    // Arrow keys for pagination
    if (e.key === 'ArrowLeft' && currentPage > 1) {
        changePage('prev');
        e.preventDefault();
    }
    if (e.key === 'ArrowRight' && currentPage < totalPages) {
        changePage('next');
        e.preventDefault();
    }
});

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    loadProjects();
    
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.style.display = 'none';
                document.body.style.overflow = '';
            }
        });
    });
});

// ============================================
// EXPOSE FUNCTIONS GLOBALLY
// ============================================

window.viewSubmissionDetails = viewSubmissionDetails;
window.refreshData = refreshData;
window.goToPage = goToPage;
window.changePage = changePage;
window.closeModal = closeModal;
window.showNotification = showNotification;
window.closeNotification = closeNotification;
window.closeErrorNotification = closeErrorNotification;
window.closeWarningNotification = closeWarningNotification;