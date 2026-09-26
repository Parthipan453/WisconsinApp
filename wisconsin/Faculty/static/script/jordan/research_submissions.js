// ============================================
// Research Submission - Complete JavaScript
// ============================================

let currentProjects = [];
let isLoading = false;
let currentSubmissionId = null;
let currentProjectId = null;
let isEditMode = false;

// Status mapping for badges
const STATUS_CLASS_MAP = {
    'DRAFT': 'draft',
    'SUBMITTED': 'submitted',
    'UNDER_REVIEW': 'under_review',
    'REVISION_REQUIRED': 'revision',
    'RESUBMITTED': 'submitted',
    'ACCEPTED': 'accepted',
    'REJECTED': 'rejected',
    'PUBLISHED': 'published',
    'WITHDRAWN': 'draft'
};

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
        
        const data = await apiRequest('/faculty/api/faculty-research-projects-with-submissions/');
        currentProjects = data.projects || [];
        
        renderProjects(currentProjects);
        updateStats(currentProjects);
        
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('projectsGrid').style.display = 'grid';
        
    } catch (error) {
        showNotification('Failed to load projects: ' + error.message, 'error');
        document.getElementById('loadingState').innerHTML = `
            <i class="ti ti-alert-circle" style="font-size: 48px; color: var(--primary-red);"></i>
            <h3 style="margin-top: 16px; color: var(--gray-600);">Failed to load projects</h3>
            <p style="color: var(--gray-400);">${error.message}</p>
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
        const data = await apiRequest(`/faculty/api/project-submission/?project_id=${projectId}`);
        return data;
    } catch (error) {
        showNotification('Failed to load submission: ' + error.message, 'error');
        return null;
    }
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
                <p>You haven't created any research projects yet.</p>
            </div>
        `;
        grid.style.display = 'block';
        return;
    }
    
    grid.style.display = 'grid';
    
    projects.forEach((project, index) => {
        const card = document.createElement('div');
        card.className = 'project-card';
        card.style.animationDelay = `${index * 0.05}s`;
        
        const statusClass = project.project_status || 'draft';
        const statusDisplay = project.project_status_display || 'Draft';
        
        const startDate = project.start_date ? new Date(project.start_date).toLocaleDateString('en-US', {
            year: 'numeric', month: 'short', day: 'numeric'
        }) : 'Not set';
        
        const endDate = project.end_date ? new Date(project.end_date).toLocaleDateString('en-US', {
            year: 'numeric', month: 'short', day: 'numeric'
        }) : 'Not set';
        
        const category = project.category || 'Not specified';
        const department = project.department || 'Not specified';
        
        let teamMembersHtml = '';
        if (project.team_members && project.team_members.length > 0) {
            project.team_members.forEach(member => {
                teamMembersHtml += `
                    <span class="team-member-tag">
                        <i class="ti ti-user"></i> ${escapeHtml(member.name)}
                    </span>
                `;
            });
        }
        
        // Publication preview
        let publicationHtml = '';
        if (project.has_submission && project.submission) {
            const pubStatus = project.submission.status || 'draft';
            const pubStatusDisplay = project.submission.status_display || 'Draft';
            const pubTitle = project.submission.title || 'Publication';
            publicationHtml = `
                <div class="publication-preview">
                    <i class="ti ti-file-text"></i>
                    <span class="publication-title">${escapeHtml(pubTitle)}</span>
                    <span class="status-badge ${pubStatus}">${pubStatusDisplay}</span>
                </div>
            `;
        } else if (project.has_publication) {
            publicationHtml = `
                <div class="publication-preview">
                    <i class="ti ti-file-text"></i>
                    <span class="publication-title">${escapeHtml(project.submission?.title || 'Publication')}</span>
                    <span class="status-badge draft">Draft</span>
                </div>
            `;
        } else {
            publicationHtml = `
                <div class="no-publication">
                    <i class="ti ti-file-off"></i>
                    <span>No publication yet</span>
                </div>
            `;
        }
        
        // Determine button states
        let buttonsHtml = '';
        if (project.has_submission) {
            buttonsHtml = `
                <button class="btn btn-view-details" onclick="event.stopPropagation(); viewSubmissionDetails('${project.id}')">
                    <i class="ti ti-eye"></i> View Details
                </button>
                <button class="btn btn-edit-submission" onclick="event.stopPropagation(); openEditSubmission('${project.id}')">
                    <i class="ti ti-edit"></i> Update Submission
                </button>
            `;
        } else if (project.has_publication) {
            buttonsHtml = `
                <button class="btn btn-view-details" onclick="event.stopPropagation(); viewSubmissionDetails('${project.id}')">
                    <i class="ti ti-eye"></i> View Publication
                </button>
                <button class="btn btn-create-submission" onclick="event.stopPropagation(); openCreateSubmission('${project.id}')">
                    <i class="ti ti-plus"></i> Add Submission
                </button>
            `;
        } else {
            buttonsHtml = `
                <button class="btn btn-view-details" disabled style="opacity:0.5;cursor:not-allowed;width:100%;">
                    <i class="ti ti-file"></i> Create Publication First
                </button>
            `;
        }
        
        card.innerHTML = `
            <div class="card-header">
                <div class="card-title-section">
                    <h4 class="project-title">${escapeHtml(project.title)}</h4>
                    <span class="status-badge ${statusClass}">${statusDisplay}</span>
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
                
                <div class="team-section">
                    <div class="team-header">
                        <i class="ti ti-users"></i>
                        <span>Team Members</span>
                        <span class="team-count">${project.team_members ? project.team_members.length : 0}</span>
                    </div>
                    <div class="team-members">
                        ${teamMembersHtml || '<span class="no-team-members">No team members assigned</span>'}
                    </div>
                </div>
                
                ${publicationHtml}
            </div>
            
            <div class="card-footer">
                ${buttonsHtml}
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

function updateStats(projects) {
    const total = projects.length;
    const withSubmission = projects.filter(p => p.has_submission).length;
    const pending = projects.filter(p => p.has_submission && p.submission && 
        ['under_review', 'submitted', 'resubmitted'].includes(p.submission.status)).length;
    const completed = projects.filter(p => p.has_submission && p.submission && 
        ['accepted', 'published'].includes(p.submission.status)).length;
    
    document.getElementById('totalProjects').textContent = total;
    document.getElementById('totalSubmissions').textContent = withSubmission;
    document.getElementById('pendingCount').textContent = pending;
    document.getElementById('completedCount').textContent = completed;
}

// ============================================
// CREATE/EDIT SUBMISSION
// ============================================

async function openCreateSubmission(projectId) {
    currentProjectId = projectId;
    isEditMode = false;
    currentSubmissionId = null;
    
    resetForm();
    document.getElementById('submitBtn').innerHTML = '<i class="ti ti-check"></i> Create Submission';
    document.getElementById('modalTitle').innerHTML = '<i class="ti ti-file-plus"></i> Create Submission';
    
    clearErrors();
    
    const project = currentProjects.find(p => p.id == projectId);
    if (project) {
        document.getElementById('formProjectId').value = projectId;
        document.getElementById('formProjectTitle').textContent = project.title;
        document.getElementById('formProjectCategory').textContent = project.category || 'N/A';
        document.getElementById('formProjectDepartment').textContent = project.department || 'N/A';
    }
    
    const pubData = await loadProjectSubmission(projectId);
    if (pubData && pubData.submission) {
        displayPublicationInfo(pubData.submission);
    }
    
    openModal('submissionModal');
}

async function openEditSubmission(projectId) {
    currentProjectId = projectId;
    isEditMode = true;
    
    resetForm();
    document.getElementById('submitBtn').innerHTML = '<i class="ti ti-check"></i> Update Submission';
    document.getElementById('modalTitle').innerHTML = '<i class="ti ti-edit"></i> Update Submission';
    
    clearErrors();
    
    const project = currentProjects.find(p => p.id == projectId);
    if (project) {
        document.getElementById('formProjectId').value = projectId;
        document.getElementById('formProjectTitle').textContent = project.title;
        document.getElementById('formProjectCategory').textContent = project.category || 'N/A';
        document.getElementById('formProjectDepartment').textContent = project.department || 'N/A';
    }
    
    const subData = await loadProjectSubmission(projectId);
    if (subData && subData.submission) {
        const sub = subData.submission;
        document.getElementById('formSubmissionId').value = sub.id || '';
        document.getElementById('journalName').value = sub.journal_name || sub.conference_name || '';
        document.getElementById('publisher').value = sub.publisher || '';
        document.getElementById('submissionDate').value = sub.submission_date || '';
        document.getElementById('manuscriptNumber').value = sub.manuscript_number || '';
        document.getElementById('acceptanceDate').value = sub.acceptance_date || '';
        document.getElementById('publicationDate').value = sub.publication_date || '';
        document.getElementById('doi').value = sub.doi || '';
        document.getElementById('publicationUrl').value = sub.publication_url || '';
        
        const statusValue = sub.status || 'DRAFT';
        document.getElementById('submissionStatus').value = statusValue.toUpperCase();
        currentSubmissionId = sub.id;
        
        displayPublicationInfo(sub);
    }
    
    openModal('submissionModal');
}

// ============================================
// DISPLAY PUBLICATION INFO (Read-only)
// ============================================

function displayPublicationInfo(submission) {
    document.getElementById('formPubTitle').textContent = submission.title || 'N/A';
    document.getElementById('formPubType').textContent = submission.type_display || 'N/A';
    document.getElementById('formPubAbstract').textContent = submission.abstract || 'N/A';
    document.getElementById('formPubKeywords').textContent = submission.keywords || 'N/A';
    
    const authorsContainer = document.getElementById('formAuthorsList');
    authorsContainer.innerHTML = '';
    
    if (submission.authors && submission.authors.length > 0) {
        const list = document.createElement('div');
        list.className = 'authors-list-readonly';
        
        submission.authors.forEach(author => {
            const item = document.createElement('div');
            item.className = 'author-readonly-item';
            
            const roleMap = {
                'First Author': 'first',
                'Corresponding Author': 'corresponding',
                'Co Author': 'co_author'
            };
            const roleClass = roleMap[author.role] || 'co_author';
            
            item.innerHTML = `
                <span style="display: flex; align-items: center; gap: 8px; font-weight: 500;">
                    <i class="ti ti-user"></i> ${escapeHtml(author.name)}
                </span>
                <span class="author-role-badge ${roleClass}">${escapeHtml(author.role)}</span>
            `;
            list.appendChild(item);
        });
        authorsContainer.appendChild(list);
    } else {
        authorsContainer.innerHTML = '<p style="color: var(--gray-400);">No authors assigned</p>';
    }
}

// ============================================
// RESET FORM
// ============================================

function resetForm() {
    document.getElementById('formSubmissionId').value = '';
    document.getElementById('journalName').value = '';
    document.getElementById('publisher').value = '';
    document.getElementById('submissionDate').value = '';
    document.getElementById('manuscriptNumber').value = '';
    document.getElementById('acceptanceDate').value = '';
    document.getElementById('publicationDate').value = '';
    document.getElementById('doi').value = '';
    document.getElementById('publicationUrl').value = '';
    document.getElementById('submissionStatus').value = 'DRAFT';
    
    document.getElementById('formPubTitle').textContent = '-';
    document.getElementById('formPubType').textContent = '-';
    document.getElementById('formPubAbstract').textContent = '-';
    document.getElementById('formPubKeywords').textContent = '-';
    document.getElementById('formAuthorsList').innerHTML = '<p style="color: var(--gray-400);">No authors assigned</p>';
}

// ============================================
// FORM VALIDATION
// ============================================

function validateForm() {
    clearErrors();
    return true;
}

function clearErrors() {
    document.querySelectorAll('.error-message').forEach(el => el.textContent = '');
    document.querySelectorAll('.form-control.error').forEach(el => el.classList.remove('error'));
}

// ============================================
// SUBMIT FORM
// ============================================

document.getElementById('submissionForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const projectId = document.getElementById('formProjectId').value;
    const submissionId = document.getElementById('formSubmissionId').value;
    const journalName = document.getElementById('journalName').value.trim();
    const publisher = document.getElementById('publisher').value.trim();
    const submissionDate = document.getElementById('submissionDate').value;
    const manuscriptNumber = document.getElementById('manuscriptNumber').value.trim();
    const acceptanceDate = document.getElementById('acceptanceDate').value;
    const publicationDate = document.getElementById('publicationDate').value;
    const doi = document.getElementById('doi').value.trim();
    const publicationUrl = document.getElementById('publicationUrl').value.trim();
    const status = document.getElementById('submissionStatus').value;
    
    // Show loading state on button
    const submitBtn = document.getElementById('submitBtn');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="ti ti-loader ti-spin"></i> Saving...';
    submitBtn.disabled = true;
    
    try {
        const data = {
            project_id: projectId,
            journal_name: journalName,
            conference_name: journalName,
            publisher: publisher,
            submission_date: submissionDate || null,
            manuscript_number: manuscriptNumber,
            acceptance_date: acceptanceDate || null,
            publication_date: publicationDate || null,
            doi: doi,
            publication_url: publicationUrl,
            status: status
        };
        
        if (submissionId) {
            data.submission_id = submissionId;
        }
        
        const result = await apiRequest('/faculty/api/create-or-update-submission/', 'POST', data);
        
        showNotification(result.message, 'success');
        closeModal('submissionModal');
        await loadProjects();
        
    } catch (error) {
        showNotification('Failed to save submission: ' + error.message, 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
});

// ============================================
// VIEW SUBMISSION DETAILS
// ============================================

async function viewSubmissionDetails(projectId) {
    try {
        const data = await loadProjectSubmission(projectId);
        if (!data || !data.submission) {
            showNotification('No publication found for this project', 'warning');
            return;
        }
        
        const sub = data.submission;
        currentSubmissionId = sub.id;
        
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
            keywordsContainer.innerHTML = '<span style="color: var(--gray-400);">No keywords specified</span>';
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
            authorsContainer.innerHTML = '<p style="color: var(--gray-400);">No authors assigned</p>';
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
        
        const statusSelect = document.getElementById('detailStatusSelect');
        if (statusSelect) {
            const statusValue = sub.status ? sub.status.toUpperCase() : 'DRAFT';
            statusSelect.value = statusValue;
        }
        
        openModal('submissionDetailModal');
        
    } catch (error) {
        showNotification('Failed to load submission details: ' + error.message, 'error');
    }
}

// ============================================
// UPDATE SUBMISSION STATUS
// ============================================

async function updateSubmissionStatus() {
    try {
        const statusSelect = document.getElementById('detailStatusSelect');
        if (!statusSelect) {
            showNotification('Status select not found', 'error');
            return;
        }
        
        const newStatus = statusSelect.value;
        
        if (!currentSubmissionId) {
            showNotification('No submission selected', 'error');
            return;
        }
        
        const data = {
            submission_id: currentSubmissionId,
            status: newStatus
        };
        
        const result = await apiRequest('/faculty/api/update-submission-status/', 'POST', data);
        
        showNotification(result.message, 'success');
        
        document.getElementById('detailStatus').textContent = result.data.status_display;
        const statusClass = STATUS_CLASS_MAP[result.data.status.toUpperCase()] || 'draft';
        document.getElementById('detailStatus').className = `project-badge ${statusClass}`;
        
        await loadProjects();
        
    } catch (error) {
        showNotification('Failed to update status: ' + error.message, 'error');
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

    document.querySelectorAll('.form-control').forEach(element => {
        if (element.tagName.toLowerCase() === 'select') {
            new SlimSelect({
                select: element,
                settings: {
                    placeholderText: element.options[0]?.text || 'Select an option',
                    showSearch: false
                }
            });
        }
    });
});