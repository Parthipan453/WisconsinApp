// Faculty Research Project Application JavaScript

// Sample data for my applications
const sampleApplications = [
    {
        id: 1,
        projectTitle: "AI-Based Student Performance Prediction",
        researchType: "thesis",
        status: "approved",
        submissionDate: "2026-06-15",
        facultyName: "Dr. John Doe",
        facultyDept: "Computer Science",
        duration: "1-year",
        abstract: "This research proposes a machine learning-based system to predict student academic performance...",
        objectives: ["Develop predictive model", "Analyze correlations", "Create dashboard"],
        outcomes: ["Prediction system", "Early warning system", "Recommendation system"]
    },
    {
        id: 2,
        projectTitle: "Sustainable Energy Solutions for Smart Cities",
        researchType: "project",
        status: "pending",
        submissionDate: "2026-06-28",
        facultyName: "Dr. John Doe",
        facultyDept: "Engineering",
        duration: "6-months",
        abstract: "Exploring renewable energy integration with smart city infrastructure...",
        objectives: ["Design hybrid system", "Develop IoT sensors", "Create optimization algorithm"],
        outcomes: ["System design", "Monitoring prototype", "Optimization algorithm"]
    },
    {
        id: 3,
        projectTitle: "Blockchain for Secure Academic Credentials",
        researchType: "dissertation",
        status: "in-review",
        submissionDate: "2026-06-20",
        facultyName: "Dr. John Doe",
        facultyDept: "Computer Science",
        duration: "2-years",
        abstract: "Using blockchain for secure, verifiable academic credentials...",
        objectives: ["Design verification system", "Implement smart contracts", "Ensure privacy"],
        outcomes: ["Verification system", "Smart contract implementation", "Security audit"]
    }
];

// Store current state
let currentApplications = [];
let objectivesList = [];
let outcomesList = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadData();
    setupFormListeners();
    updateFacultyProfile();
});

function loadData() {
    showLoading();
    
    setTimeout(() => {
        currentApplications = JSON.parse(JSON.stringify(sampleApplications));
        renderApplications(currentApplications);
        updateStats(currentApplications);
        updateApplicationCount(currentApplications.length);
        hideLoading();
    }, 500);
}

function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.style.display = 'flex';
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.style.display = 'none';
}

function updateFacultyProfile() {
    // In a real application, this would come from the backend
    document.getElementById('facultyInitials').textContent = 'JD';
    document.getElementById('facultyName').textContent = 'Dr. John Doe';
    document.getElementById('facultyDepartment').textContent = 'Computer Science Department';
    document.getElementById('facultyEmail').textContent = 'john.doe@university.edu';
    document.getElementById('facultyPhone').textContent = '+1 234 567 8900';
    document.getElementById('facultyExpertise').textContent = 'AI, Machine Learning, Data Science';
}

function setupFormListeners() {
    // Enter key for list inputs
    document.getElementById('objectiveInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            addListItem('objectiveInput', 'objectivesList');
        }
    });
    
    document.getElementById('outcomeInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            addListItem('outcomeInput', 'outcomesList');
        }
    });
}

function addListItem(inputId, listId) {
    const input = document.getElementById(inputId);
    const list = document.getElementById(listId);
    const value = input.value.trim();
    
    if (value === '') {
        showNotification('Please enter a value first.', 'warning');
        return;
    }
    
    // Check for duplicates
    const existingItems = list.querySelectorAll('li');
    for (let item of existingItems) {
        if (item.textContent.replace('✕', '').trim() === value) {
            showNotification('This item already exists in the list.', 'warning');
            return;
        }
    }
    
    const li = document.createElement('li');
    li.innerHTML = `
        ${value}
        <span class="remove-item" onclick="removeListItem(this)">✕</span>
    `;
    list.appendChild(li);
    input.value = '';
    input.focus();
}

function removeListItem(element) {
    element.parentElement.remove();
}

function submitApplication(event) {
    event.preventDefault();
    
    // Validate form
    const title = document.getElementById('projectTitleInput').value.trim();
    const abstract = document.getElementById('projectAbstractInput').value.trim();
    const objectives = document.querySelectorAll('#objectivesList li');
    const outcomes = document.querySelectorAll('#outcomesList li');
    
    if (!title) {
        showNotification('Please enter a project title.', 'error');
        document.getElementById('projectTitleInput').focus();
        return;
    }
    
    if (!abstract) {
        showNotification('Please enter an abstract.', 'error');
        document.getElementById('projectAbstractInput').focus();
        return;
    }
    
    if (objectives.length === 0) {
        showNotification('Please add at least one research objective.', 'error');
        document.getElementById('objectiveInput').focus();
        return;
    }
    
    if (outcomes.length === 0) {
        showNotification('Please add at least one expected outcome.', 'error');
        document.getElementById('outcomeInput').focus();
        return;
    }
    
    // Collect form data
    const applicationData = {
        id: currentApplications.length + 1,
        projectTitle: title,
        researchType: document.getElementById('researchTypeInput').value,
        status: 'pending',
        submissionDate: new Date().toISOString().split('T')[0],
        facultyName: document.getElementById('facultyNameInput').value || 'Dr. John Doe',
        facultyDept: document.getElementById('facultyDeptInput').value || 'Computer Science',
        duration: document.getElementById('projectDurationInput').value || '1-year',
        abstract: abstract,
        objectives: Array.from(objectives).map(li => li.textContent.replace('✕', '').trim()),
        outcomes: Array.from(outcomes).map(li => li.textContent.replace('✕', '').trim()),
        keywords: document.getElementById('projectKeywordsInput').value || ''
    };
    
    // Add to applications list
    currentApplications.unshift(applicationData);
    renderApplications(currentApplications);
    updateStats(currentApplications);
    updateApplicationCount(currentApplications.length);
    
    // Show success modal
    document.getElementById('successModal').style.display = 'flex';
    document.body.style.overflow = 'hidden';
    
    // Reset form
    resetForm();
    
    showNotification('Application submitted successfully!', 'success');
}

function resetForm() {
    document.getElementById('applicationForm').reset();
    document.getElementById('objectivesList').innerHTML = '';
    document.getElementById('outcomesList').innerHTML = '';
}

function closeSuccessModal() {
    document.getElementById('successModal').style.display = 'none';
    document.body.style.overflow = '';
}

function renderApplications(applications) {
    const grid = document.getElementById('applicationsGrid');
    grid.innerHTML = '';
    
    if (!applications || applications.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="ti ti-file-inbox"></i>
                <p>No applications submitted yet</p>
                <span class="empty-sub">Submit your first research project application above</span>
            </div>
        `;
        return;
    }
    
    applications.forEach(app => {
        const card = document.createElement('div');
        card.className = 'application-card';
        
        const statusClass = app.status.toLowerCase().replace(' ', '-');
        const statusIcon = {
            'pending': 'ti ti-clock',
            'approved': 'ti ti-check-circle',
            'rejected': 'ti ti-x-circle',
            'in-review': 'ti ti-file-check'
        }[statusClass] || 'ti ti-file';
       
    
        const typeLabels = {
            'thesis': 'Thesis',
            'dissertation': 'Dissertation',
            'project': 'Project',
            'case-study': 'Case Study',
            'experimental': 'Experimental'
        };
        
        card.innerHTML = `
            <div class="card-header">
                <h4 class="card-title">${app.projectTitle}</h4>
                <span class="status-badge ${statusClass}">
                    <i class="${statusIcon}"></i>
                    ${app.status.charAt(0).toUpperCase() + app.status.slice(1).replace('-', ' ')}
                </span>
            </div>
            
            <div class="card-meta">
                <span><i class="ti ti-calendar"></i> ${new Date(app.submissionDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                <span><i class="ti ti-clock"></i> ${app.duration || 'N/A'}</span>
                <span><i class="ti ti-building"></i> ${app.facultyDept || 'N/A'}</span>
            </div>
            
            <div class="card-footer">
                <span class="type-tag">
                    <i class="ti ti-book"></i>
                    ${typeLabels[app.researchType] || app.researchType}
                </span>
                <span class="view-btn" onclick="viewApplication(${app.id})">
                    View Details <i class="ti ti-chevron-right"></i>
                </span>
            </div>
        `;
        grid.appendChild(card);
    });
}

function viewApplication(id) {
    const app = currentApplications.find(a => a.id === id);
    if (!app) return;
    
    // In a real application, this would open a detailed view
    showNotification(`Viewing: ${app.projectTitle}`, 'info');
}

function updateStats(applications) {
    const total = applications.length;
    const pending = applications.filter(a => a.status === 'pending').length;
    const approved = applications.filter(a => a.status === 'approved').length;
    const rejected = applications.filter(a => a.status === 'rejected').length;
    
    animateNumber('statTotalApplications', total);
    animateNumber('statPendingApplications', pending);
    animateNumber('statApprovedApplications', approved);
    animateNumber('statRejectedApplications', rejected);
}

function animateNumber(elementId, targetValue) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const currentValue = parseInt(element.textContent) || 0;
    const duration = 500;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(currentValue + (targetValue - currentValue) * eased);
        
        element.textContent = current;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

function updateApplicationCount(count) {
    const badge = document.getElementById('myApplicationsCount');
    if (badge) {
        badge.textContent = `${count} Application${count !== 1 ? 's' : ''}`;
    }
}

function showNotification(message, type = 'info') {
    const existing = document.querySelector('.custom-notification');
    if (existing) existing.remove();
    
    const notification = document.createElement('div');
    notification.className = 'custom-notification';
    
    const colors = {
        success: '#22c55e',
        error: '#ef4444',
        info: '#3b82f6',
        warning: '#f97316'
    };
    
    const icons = {
        success: 'ti ti-check-circle',
        error: 'ti ti-exclamation-circle',
        info: 'ti ti-info-circle',
        warning: 'ti ti-alert-circle'
    };
    
    notification.style.cssText = `
        position: fixed;
        top: 24px;
        right: 24px;
        padding: 16px 24px;
        border-radius: 12px;
        background: ${colors[type] || colors.info};
        color: white;
        font-weight: 500;
        z-index: 9999;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 14px;
        animation: slideInRight 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        min-width: 280px;
        max-width: 480px;
    `;
    
    notification.innerHTML = `
        <i class="${icons[type] || icons.info}" style="font-size: 20px;"></i>
        <span>${message}</span>
        <i class="ti ti-x" style="margin-left: auto; cursor: pointer; opacity: 0.7; font-size: 16px;" onclick="this.parentElement.remove()"></i>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
        setTimeout(() => notification.remove(), 400);
    }, 4000);
}