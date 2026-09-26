// ============================================
// Research Publication - Complete JavaScript
// ============================================

let currentProjects = [];
let teamMembers = [];
let isLoading = false;
let currentPublicationId = null;
let currentProjectId = null;
let isEditMode = false;
let existingAuthorIds = [];
let customSelectsInitialized = false;

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
        
        const data = await apiRequest('/faculty/api/faculty-research-projects/');
        currentProjects = data.projects || [];
        
        renderProjects(currentProjects);
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

async function loadProjectPublication(projectId) {
    try {
        const data = await apiRequest(`/faculty/api/project-publication/?project_id=${projectId}`);
        return data;
    } catch (error) {
        showNotification('Failed to load publication: ' + error.message, 'error');
        return null;
    }
}

async function loadTeamMembers(projectId) {
    try {
        const data = await apiRequest(`/faculty/api/team-members-for-publication/?project_id=${projectId}`);
        teamMembers = data.team_members || [];
        return teamMembers;
    } catch (error) {
        console.error('Failed to load team members:', error);
        showNotification('Failed to load team members: ' + error.message, 'error');
        return [];
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
    
    projects.forEach(project => {
        const card = document.createElement('div');
        card.className = 'project-card';
        
        const statusClass = project.project_status || 'draft';
        const statusDisplay = project.project_status_display || 'Draft';
        
        card.innerHTML = `
            <div class="card-header">
                <div class="card-title-section">
                    <h4 class="project-title">${escapeHtml(project.title)}</h4>
                    <span class="status-badge ${statusClass}">${statusDisplay}</span>
                </div>
            </div>
            
            <div class="card-body">
                <p class="project-description">${escapeHtml(project.description ? project.description.substring(0, 120) : '')}${project.description && project.description.length > 120 ? '...' : ''}</p>
                
                <div class="project-meta">
                    <span><i class="ti ti-building"></i> ${escapeHtml(project.department)}</span>
                    <span><i class="ti ti-calendar"></i> ${project.start_date ? new Date(project.start_date).toLocaleDateString() : 'Not set'}</span>
                    <span><i class="ti ti-tag"></i> ${escapeHtml(project.category || 'No category')}</span>
                </div>
                
                ${project.has_publication ? `
                    <div class="publication-preview">
                        <i class="ti ti-file-text"></i>
                        <span>${escapeHtml(project.publication.title)}</span>
                        <span class="status-badge ${project.publication.status}">${project.publication.status_display}</span>
                    </div>
                ` : `
                    <div class="no-publication">
                        <i class="ti ti-file-off"></i>
                        <span>No publication yet</span>
                    </div>
                `}
            </div>
            
            <div class="card-footer">
                ${project.has_publication ? `
                    <button class="btn-view-details" onclick="event.stopPropagation(); viewPublicationDetails('${project.id}')">
                        <i class="ti ti-eye"></i> Details
                    </button>
                    <button class="btn-edit-publication" onclick="event.stopPropagation(); openEditPublication('${project.id}')">
                        <i class="ti ti-edit"></i> Update
                    </button>
                ` : `
                    <button class="btn-create-publication" onclick="event.stopPropagation(); openCreatePublication('${project.id}')">
                        <i class="ti ti-plus"></i> Create Publication
                    </button>
                `}
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
    const withPublication = projects.filter(p => p.has_publication).length;
    const published = projects.filter(p => p.has_publication && p.publication && p.publication.status === 'published').length;
    const draft = projects.filter(p => p.has_publication && p.publication && p.publication.status === 'draft').length;
    
    document.getElementById('totalProjects').textContent = total;
    document.getElementById('totalPublications').textContent = withPublication;
    document.getElementById('publishedCount').textContent = published;
    document.getElementById('draftCount').textContent = draft;
}

// ============================================
// CREATE/EDIT PUBLICATION
// ============================================

async function openCreatePublication(projectId) {
    currentProjectId = projectId;
    isEditMode = false;
    existingAuthorIds = [];
    customSelectsInitialized = false;
    
    // Reset form
    const form = document.getElementById('publicationForm');
    form.reset();
    document.getElementById('formPublicationId').value = '';
    document.getElementById('pubTitle').value = '';
    document.getElementById('pubAbstract').value = '';
    document.getElementById('pubKeywords').value = '';
    document.getElementById('pubType').value = '';
    document.getElementById('pubStatus').value = 'DRAFT';
    document.getElementById('authorsContainer').innerHTML = '';
    document.getElementById('submitBtn').innerHTML = '<i class="ti ti-check"></i> Create Publication';
    document.getElementById('modalTitle').innerHTML = '<i class="ti ti-file-plus"></i> Create Publication';
    
    clearErrors();
    
    const project = currentProjects.find(p => p.id == projectId);
    if (project) {
        document.getElementById('formProjectId').value = projectId;
        document.getElementById('formProjectTitle').textContent = project.title;
        document.getElementById('formProjectCategory').textContent = project.category || 'N/A';
        document.getElementById('formProjectDepartment').textContent = project.department || 'N/A';
    }
    
    // Load team members
    await loadTeamMembers(projectId);
    addAuthorRow();
    
    // Open modal
    openModal('publicationModal');
}

async function openEditPublication(projectId) {
    currentProjectId = projectId;
    isEditMode = true;
    existingAuthorIds = [];
    customSelectsInitialized = false;
    
    // Reset form
    const form = document.getElementById('publicationForm');
    form.reset();
    document.getElementById('authorsContainer').innerHTML = '';
    document.getElementById('submitBtn').innerHTML = '<i class="ti ti-check"></i> Update Publication';
    document.getElementById('modalTitle').innerHTML = '<i class="ti ti-edit"></i> Update Publication';
    
    clearErrors();
    
    const project = currentProjects.find(p => p.id == projectId);
    if (project) {
        document.getElementById('formProjectId').value = projectId;
        document.getElementById('formProjectTitle').textContent = project.title;
        document.getElementById('formProjectCategory').textContent = project.category || 'N/A';
        document.getElementById('formProjectDepartment').textContent = project.department || 'N/A';
    }
    
    // Load team members first
    await loadTeamMembers(projectId);
    
    // Load publication data
    const pubData = await loadProjectPublication(projectId);
    if (pubData && pubData.has_publication && pubData.publication) {
        const pub = pubData.publication;
        document.getElementById('formPublicationId').value = pub.id;
        document.getElementById('pubTitle').value = pub.title;
        document.getElementById('pubAbstract').value = pub.abstract;
        document.getElementById('pubKeywords').value = pub.keywords || '';
        document.getElementById('pubType').value = pub.publication_type;
        document.getElementById('pubStatus').value = pub.status.toUpperCase();
        currentPublicationId = pub.id;
        
        // Add author rows for existing authors
        if (pub.authors && pub.authors.length > 0) {
            document.getElementById('authorsContainer').innerHTML = '';
            pub.authors.forEach((author) => {
                if (author.team_member_id) {
                    existingAuthorIds.push(author.team_member_id.toString());
                }
                addAuthorRow(author.team_member_id);
                const rows = document.querySelectorAll('.author-row');
                const row = rows[rows.length - 1];
                const roleSelect = row.querySelector('.author-role');
                if (roleSelect) {
                    const roleMap = {
                        'First Author': 'FIRST',
                        'Corresponding Author': 'CORRESPONDING',
                        'Co Author': 'CO_AUTHOR'
                    };
                    roleSelect.value = roleMap[author.author_role] || 'CO_AUTHOR';
                }
            });
        } else {
            addAuthorRow();
        }
    } else {
        addAuthorRow();
    }
    
    // Open modal
    openModal('publicationModal');
}

// ============================================
// FORM VALIDATION
// ============================================

function validateForm() {
    let isValid = true;
    clearErrors();
    
    const title = document.getElementById('pubTitle').value.trim();
    if (title.length < 5) {
        document.getElementById('titleError').textContent = 'Title must be at least 5 characters long';
        document.getElementById('pubTitle').classList.add('error');
        isValid = false;
    }
    
    const abstract = document.getElementById('pubAbstract').value.trim();
    if (abstract.length < 20) {
        document.getElementById('abstractError').textContent = 'Abstract must be at least 20 characters long';
        document.getElementById('pubAbstract').classList.add('error');
        isValid = false;
    }
    
    const pubType = document.getElementById('pubType').value;
    if (!pubType) {
        document.getElementById('typeError').textContent = 'Please select a publication type';
        document.getElementById('pubType').classList.add('error');
        isValid = false;
    }
    
    const authorRows = document.querySelectorAll('.author-row');
    let hasAuthor = false;
    authorRows.forEach(row => {
        const select = row.querySelector('.author-select');
        if (select && select.value) {
            hasAuthor = true;
        }
    });
    if (!hasAuthor) {
        document.getElementById('authorsError').textContent = 'Please select at least one author';
        isValid = false;
    }
    
    return isValid;
}

function clearErrors() {
    document.querySelectorAll('.error-message').forEach(el => el.textContent = '');
    document.querySelectorAll('.form-control.error').forEach(el => el.classList.remove('error'));
}

// ============================================
// SUBMIT PUBLICATION
// ============================================

document.getElementById('publicationForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    if (!validateForm()) {
        showNotification('Please fix the errors in the form', 'warning');
        return;
    }
    
    const projectId = document.getElementById('formProjectId').value;
    const publicationId = document.getElementById('formPublicationId').value;
    const title = document.getElementById('pubTitle').value.trim();
    const abstract = document.getElementById('pubAbstract').value.trim();
    const keywords = document.getElementById('pubKeywords').value.trim();
    const pubType = document.getElementById('pubType').value;
    const pubStatus = document.getElementById('pubStatus').value;
    
    const authorRows = document.querySelectorAll('.author-row');
    const authors = [];
    authorRows.forEach((row) => {
        const select = row.querySelector('.author-select');
        const role = row.querySelector('.author-role').value;
        const teamMemberId = select ? select.value : '';
        
        if (teamMemberId) {
            authors.push({
                team_member_id: teamMemberId,
                author_role: role,
                author_order: authors.length + 1
            });
        }
    });
    
    try {
        const data = {
            project_id: projectId,
            title: title,
            abstract: abstract,
            keywords: keywords,
            publication_type: pubType,
            status: pubStatus,
            authors: authors
        };
        
        if (publicationId) {
            data.publication_id = publicationId;
        }
        
        const result = await apiRequest('/faculty/api/create-or-update-publication/', 'POST', data);
        
        showNotification(result.message, 'success');
        closeModal('publicationModal');
        await loadProjects();
        
    } catch (error) {
        showNotification('Failed to save publication: ' + error.message, 'error');
    }
});

// ============================================
// VIEW PUBLICATION DETAILS
// ============================================

async function viewPublicationDetails(projectId) {
    try {
        const data = await loadProjectPublication(projectId);
        if (!data || !data.has_publication || !data.publication) {
            showNotification('Publication not found', 'error');
            return;
        }
        
        const pub = data.publication;
        currentPublicationId = pub.id;
        
        document.getElementById('detailTitle').textContent = pub.title;
        document.getElementById('detailStatus').textContent = pub.status_display;
        document.getElementById('detailStatus').className = `status-badge ${pub.status}`;
        document.getElementById('detailType').textContent = pub.publication_type_display;
        document.getElementById('detailAbstract').textContent = pub.abstract || 'No abstract provided.';
        
        const keywordsContainer = document.getElementById('detailKeywords');
        keywordsContainer.innerHTML = '';
        if (pub.keywords) {
            const keywords = pub.keywords.split(',').map(k => k.trim()).filter(k => k);
            keywords.forEach(keyword => {
                const tag = document.createElement('span');
                tag.className = 'keyword-tag';
                tag.textContent = keyword;
                keywordsContainer.appendChild(tag);
            });
        } else {
            keywordsContainer.innerHTML = '<span style="color: var(--text-light);">No keywords specified</span>';
        }
        
        const authorsContainer = document.getElementById('detailAuthors');
        authorsContainer.innerHTML = '';
        if (pub.authors && pub.authors.length > 0) {
            pub.authors.forEach(author => {
                const div = document.createElement('div');
                div.className = 'author-item';
                const roleClass = author.author_role.replace(/ /g, '_').toLowerCase();
                const memberRole = author.team_member_role || '';
                div.innerHTML = `
                    <span class="author-name">
                        <i class="ti ti-user"></i> 
                        ${escapeHtml(author.name)}
                        ${memberRole ? `<span class="member-role">(${escapeHtml(memberRole)})</span>` : ''}
                    </span>
                    <span class="author-role-badge ${roleClass}">${escapeHtml(author.author_role)}</span>
                `;
                authorsContainer.appendChild(div);
            });
        } else {
            authorsContainer.innerHTML = '<p style="color: var(--text-light);">No authors assigned</p>';
        }
        
        document.getElementById('detailCreated').textContent = pub.created_at || 'N/A';
        document.getElementById('detailUpdated').textContent = pub.updated_at || 'N/A';
        document.getElementById('detailCreatedBy').textContent = pub.created_by || 'Unknown';
        
        // Set status value
        const detailStatusSelect = document.getElementById('detailStatusSelect');
        if (detailStatusSelect) {
            detailStatusSelect.value = pub.status.toUpperCase();
        }
        
        openModal('publicationDetailModal');
        
    } catch (error) {
        showNotification('Failed to load publication details: ' + error.message, 'error');
    }
}

// ============================================
// UPDATE PUBLICATION STATUS
// ============================================

async function updatePublicationStatus() {
    try {
        const detailStatusSelect = document.getElementById('detailStatusSelect');
        const newStatus = detailStatusSelect ? detailStatusSelect.value : null;
        
        if (!newStatus) {
            showNotification('Please select a status', 'warning');
            return;
        }
        
        if (!currentPublicationId) {
            showNotification('No publication selected', 'error');
            return;
        }
        
        const data = {
            publication_id: currentPublicationId,
            status: newStatus
        };
        
        const result = await apiRequest('/faculty/api/update-publication-status/', 'POST', data);
        
        showNotification(result.message, 'success');
        
        document.getElementById('detailStatus').textContent = result.data.status_display;
        document.getElementById('detailStatus').className = `status-badge ${result.data.status}`;
        
        await loadProjects();
        
    } catch (error) {
        showNotification('Failed to update status: ' + error.message, 'error');
    }
}

// ============================================
// AUTHOR MANAGEMENT
// ============================================

function populateAuthorSelects() {
    const selects = document.querySelectorAll('.author-select');
    
    // Get all currently selected values
    const selectedValues = [];
    selects.forEach(select => {
        if (select.value) {
            selectedValues.push(select.value);
        }
    });
    
    selects.forEach(select => {
        const currentValue = select.value;
        
        // Clear existing options
        select.innerHTML = '';
        
        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Select Team Member';
        select.appendChild(defaultOption);
        
        if (!teamMembers || teamMembers.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No team members found';
            option.disabled = true;
            select.appendChild(option);
            return;
        }
        
        // Get selected values from other selects
        const otherSelectedValues = [];
        selects.forEach(otherSelect => {
            if (otherSelect !== select && otherSelect.value) {
                otherSelectedValues.push(otherSelect.value);
            }
        });
        
        // Add team members
        teamMembers.forEach(member => {
            const option = document.createElement('option');
            const memberId = member.id.toString();
            option.value = memberId;
            option.textContent = `${member.name} (${member.role})`;
            
            // Check if this member is selected in another row
            const isSelectedElsewhere = otherSelectedValues.includes(memberId);
            const isCurrentSelection = memberId === currentValue;
            
            // If selected elsewhere AND not the current selection, disable it
            if (isSelectedElsewhere && !isCurrentSelection) {
                option.disabled = true;
                option.textContent += ' (Already selected)';
            }
            
            // If this is the current selection, mark as selected
            if (isCurrentSelection) {
                option.selected = true;
            }
            
            select.appendChild(option);
        });
    });
}

function addAuthorRow(selectedValue = null) {
    const container = document.getElementById('authorsContainer');
    
    const row = document.createElement('div');
    row.className = 'author-row';
    
    row.innerHTML = `
        <div class="author-select-wrapper">
            <select class="form-control author-select" required>
                <option value="">Select Team Member</option>
            </select>
        </div>
        <div class="author-role-wrapper">
            <select class="form-control author-role">
                <option value="FIRST">First Author</option>
                <option value="CORRESPONDING">Corresponding Author</option>
                <option value="CO_AUTHOR" selected>Co Author</option>
            </select>
        </div>
        <button type="button" class="btn-remove-author" onclick="removeAuthor(this)">
            <i class="ti ti-trash"></i>
        </button>
    `;
    
    container.appendChild(row);
    
    // Populate the select
    populateAuthorSelects();
    
    // If we have a selected value, set it
    if (selectedValue) {
        const select = row.querySelector('.author-select');
        setTimeout(() => {
            select.value = selectedValue.toString();
            populateAuthorSelects();
        }, 50);
    }
    
    // Add change event listener
    const select = row.querySelector('.author-select');
    select.addEventListener('change', function() {
        setTimeout(() => {
            populateAuthorSelects();
        }, 50);
    });
}

function removeAuthor(button) {
    const container = document.getElementById('authorsContainer');
    if (container.children.length <= 1) {
        showNotification('At least one author is required', 'warning');
        return;
    }
    const row = button.closest('.author-row');
    row.remove();
    setTimeout(() => {
        populateAuthorSelects();
    }, 50);
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
    }
}

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
            }
        });
    });
    
    // Close modal on ESC key
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