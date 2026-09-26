// Research Project Progress/Tracking JavaScript

// Sample data for projects
const sampleProjects = [
    {
        id: 1,
        title: "AI-Based Student Performance Prediction System",
        type: "faculty",
        status: "in-progress",
        researchType: "thesis",
        department: "Computer Science",
        progress: 75,
        startDate: "2026-01-15",
        endDate: "2026-08-15",
        abstract: "This research proposes a machine learning-based system to predict student academic performance using historical data, attendance records, and engagement metrics.",
        objectives: [
            "Develop a predictive model using ensemble learning techniques",
            "Analyze the correlation between attendance and academic performance",
            "Create a real-time dashboard for faculty monitoring"
        ],
        team: [
            { name: "Dr. John Doe", role: "Principal Investigator", initials: "JD" },
            { name: "Ahmed Hassan", role: "Research Assistant", initials: "AH" },
            { name: "Mariam Al-Fahd", role: "Data Analyst", initials: "MA" }
        ],
        milestones: [
            { title: "Literature Review", status: "completed", date: "2026-02-15" },
            { title: "Data Collection", status: "completed", date: "2026-04-01" },
            { title: "Model Development", status: "in-progress", date: "2026-06-15" },
            { title: "Testing & Validation", status: "pending", date: "2026-07-15" },
            { title: "Final Report", status: "pending", date: "2026-08-15" }
        ],
        activity: [
            { text: "Model development phase 2 completed", time: "2 days ago" },
            { text: "Dataset expanded with 500 new records", time: "5 days ago" },
            { text: "Weekly progress meeting held", time: "1 week ago" }
        ],
        reviewNotes: ""
    },
    {
        id: 2,
        title: "Sustainable Energy Solutions for Smart Cities",
        type: "student",
        status: "pending-review",
        researchType: "project",
        department: "Engineering",
        progress: 40,
        startDate: "2026-03-01",
        endDate: "2026-12-01",
        abstract: "Exploring the integration of renewable energy sources with smart city infrastructure. Focus on optimizing energy distribution and reducing carbon footprint.",
        objectives: [
            "Design a hybrid renewable energy system",
            "Develop IoT sensors for energy monitoring",
            "Create optimization algorithm"
        ],
        team: [
            { name: "Mariam Al-Fahd", role: "Student Researcher", initials: "MA" },
            { name: "Dr. John Doe", role: "Supervisor", initials: "JD" }
        ],
        milestones: [
            { title: "Initial Research", status: "completed", date: "2026-04-01" },
            { title: "System Design", status: "in-progress", date: "2026-06-01" },
            { title: "Prototype Development", status: "pending", date: "2026-09-01" },
            { title: "Final Testing", status: "pending", date: "2026-11-01" }
        ],
        activity: [
            { text: "System design review submitted", time: "1 day ago" },
            { text: "Meeting with supervisor completed", time: "3 days ago" }
        ],
        reviewNotes: "Good progress. Please finalize the system design by next week."
    },
    {
        id: 3,
        title: "Blockchain for Secure Academic Credentials",
        type: "faculty",
        status: "in-progress",
        researchType: "dissertation",
        department: "Computer Science",
        progress: 60,
        startDate: "2026-02-01",
        endDate: "2026-10-01",
        abstract: "Investigating blockchain technology for creating a secure, verifiable system for academic credentials to eliminate fraud and simplify verification.",
        objectives: [
            "Design blockchain-based verification system",
            "Implement smart contracts",
            "Ensure GDPR compliance",
            "Create user interface"
        ],
        team: [
            { name: "Dr. John Doe", role: "Lead Researcher", initials: "JD" },
            { name: "Omar Al-Saud", role: "Research Assistant", initials: "OA" },
            { name: "Layla Al-Khalifa", role: "Developer", initials: "LK" },
            { name: "Khalid Al-Mansour", role: "Tester", initials: "KM" }
        ],
        milestones: [
            { title: "Research Proposal", status: "completed", date: "2026-03-01" },
            { title: "System Architecture", status: "completed", date: "2026-05-01" },
            { title: "Smart Contract Development", status: "in-progress", date: "2026-07-01" },
            { title: "Testing", status: "pending", date: "2026-09-01" }
        ],
        activity: [
            { text: "Smart contract deployment on testnet", time: "3 days ago" },
            { text: "Architecture review meeting", time: "1 week ago" },
            { text: "New team member joined", time: "2 weeks ago" }
        ],
        reviewNotes: ""
    },
    {
        id: 4,
        title: "Machine Learning in Medical Diagnosis",
        type: "student",
        status: "completed",
        researchType: "experimental",
        department: "Biology",
        progress: 100,
        startDate: "2025-09-01",
        endDate: "2026-06-30",
        abstract: "Applying deep learning to medical imaging for early detection of diseases. Developing CNN-based model for breast cancer detection.",
        objectives: [
            "Develop CNN model",
            "Train on medical datasets",
            "Achieve 90%+ accuracy",
            "Create web interface"
        ],
        team: [
            { name: "Layla Al-Khalifa", role: "Student Researcher", initials: "LK" },
            { name: "Dr. John Doe", role: "Supervisor", initials: "JD" }
        ],
        milestones: [
            { title: "Literature Review", status: "completed", date: "2025-10-01" },
            { title: "Model Development", status: "completed", date: "2026-03-01" },
            { title: "Testing", status: "completed", date: "2026-05-01" },
            { title: "Final Report", status: "completed", date: "2026-06-30" }
        ],
        activity: [
            { text: "Research paper submitted for publication", time: "1 week ago" },
            { text: "Final presentation completed", time: "2 weeks ago" }
        ],
        reviewNotes: "Excellent work! The results are very promising."
    },
    {
        id: 5,
        title: "Cybersecurity Threat Detection System",
        type: "student",
        status: "on-hold",
        researchType: "project",
        department: "Computer Science",
        progress: 25,
        startDate: "2026-04-01",
        endDate: "2026-12-31",
        abstract: "Developing an AI-based system for detecting cybersecurity threats in real-time using anomaly detection and behavioral analysis.",
        objectives: [
            "Implement real-time detection algorithms",
            "Create monitoring dashboard",
            "Test against attack vectors"
        ],
        team: [
            { name: "Khalid Al-Mansour", role: "Student Researcher", initials: "KM" },
            { name: "Dr. John Doe", role: "Supervisor", initials: "JD" }
        ],
        milestones: [
            { title: "Literature Review", status: "completed", date: "2026-05-01" },
            { title: "Algorithm Development", status: "in-progress", date: "2026-07-01" },
            { title: "Testing", status: "pending", date: "2026-10-01" }
        ],
        activity: [
            { text: "Project temporarily paused", time: "1 week ago" },
            { text: "Resource constraints identified", time: "2 weeks ago" }
        ],
        reviewNotes: "On hold pending resource allocation."
    }
];

// Store current state
let currentProjects = [];
let selectedProject = null;
let currentFilter = 'all';

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadData();
    setupEventListeners();
    document.querySelectorAll('.filter-input').forEach(select => {
        new SlimSelect({
            select: select,
            settings: {
                placeholderText: select.options[0].text,
                showSearch: false
            }
        });
    });
});

function setupEventListeners() {
    // Enter key on search
    document.getElementById('searchInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            applySearch();
        }
    });
    
    // Filter change events
    document.querySelectorAll('.filter-input').forEach(element => {
        element.addEventListener('change', function() {
            applyFilters();
        });
    });
    
    // Close modal on overlay click
    document.getElementById('projectModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal();
        }
    });
}

function loadData() {
    showLoading();
    
    setTimeout(() => {
        currentProjects = JSON.parse(JSON.stringify(sampleProjects));
        renderProjects(currentProjects);
        updateStats(currentProjects);
        updateProjectCount(currentProjects.length);
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

function renderProjects(projects) {
    const grid = document.getElementById('projectGrid');
    grid.innerHTML = '';
    
    if (!projects || projects.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="ti ti-folder-open"></i>
                <p>No projects found</p>
                <span class="empty-sub">Try adjusting your filters</span>
            </div>
        `;
        return;
    }
    
    projects.forEach(project => {
        const card = document.createElement('div');
        card.className = 'project-card';
        card.onclick = () => openModal(project);
        
        const statusClass = project.status.toLowerCase().replace(' ', '-');
        const typeClass = project.type || 'faculty';
        const progressColor = project.progress === 100 ? 'completed' : '';
        
        // Team avatars
        let teamHtml = '';
        const displayTeam = project.team.slice(0, 3);
        const remaining = project.team.length - 3;
        
        displayTeam.forEach((member, index) => {
            teamHtml += `
                <div class="team-avatar" title="${member.name} - ${member.role}">${member.initials}</div>
            `;
        });
        
        if (remaining > 0) {
            teamHtml += `
                <div class="team-avatar more" title="${remaining} more team members">+${remaining}</div>
            `;
        }
        
        card.innerHTML = `
            <div class="card-header">
                <h4 class="project-title">${project.title}</h4>
                <span class="status-badge ${statusClass}">${project.status.replace('-', ' ').toUpperCase()}</span>
            </div>
            
            <span class="project-type-badge ${typeClass}">
                <i class="ti ${typeClass === 'faculty' ? 'ti-user' : 'ti-users'}"></i>
                ${typeClass === 'faculty' ? 'Faculty Project' : 'Student Project'}
            </span>
            
            <div class="project-meta">
                <span><i class="ti ti-file"></i> ${project.researchType}</span>
                <span><i class="ti ti-building"></i> ${project.department}</span>
                <span><i class="ti ti-calendar"></i> ${new Date(project.startDate).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}</span>
            </div>
            
            <div class="progress-bar-container">
                <div class="progress-bar-label">
                    <span>Progress</span>
                    <span>${project.progress}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill ${progressColor}" style="width: ${project.progress}%"></div>
                </div>
            </div>
            
            <div class="project-footer">
                <div class="project-team">
                    ${teamHtml}
                </div>
                <span class="view-details-btn">
                    View Details <i class="ti ti-chevron-right"></i>
                </span>
            </div>
        `;
        grid.appendChild(card);
    });
}

function updateStats(projects) {
    const total = projects.length;
    const inProgress = projects.filter(p => p.status === 'in-progress').length;
    const pendingReview = projects.filter(p => p.status === 'pending-review').length;
    const onHold = projects.filter(p => p.status === 'on-hold').length;
    
    animateNumber('statTotalProjects', total);
    animateNumber('statInProgress', inProgress);
    animateNumber('statPendingReview', pendingReview);
    animateNumber('statOnHold', onHold);
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

function updateProjectCount(count) {
    const badge = document.getElementById('projectCount');
    if (badge) {
        badge.textContent = `${count} Project${count !== 1 ? 's' : ''}`;
    }
}

function openModal(project) {
    selectedProject = project;
    const modal = document.getElementById('projectModal');
    
    // Set modal content
    document.getElementById('modalProjectTitle').textContent = project.title;
    
    const statusElement = document.getElementById('modalStatus');
    statusElement.textContent = project.status.replace('-', ' ').toUpperCase();
    statusElement.className = `modal-status ${project.status.toLowerCase().replace(' ', '-')}`;
    
    const typeElement = document.getElementById('modalType');
    const typeLabel = project.type === 'faculty' ? 'Faculty Project' : 'Student Project';
    typeElement.textContent = typeLabel;
    typeElement.className = `modal-type ${project.type}`;
    
    // Progress Circle
    const circle = document.getElementById('progressCircle');
    circle.style.setProperty('--progress', project.progress + '%');
    document.getElementById('progressPercentage').textContent = project.progress + '%';
    
    // Progress Details
    document.getElementById('modalStatusDetail').textContent = project.status.replace('-', ' ').toUpperCase();
    document.getElementById('modalLastUpdated').textContent = new Date().toLocaleDateString('en-US', { 
        weekday: 'short', 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
    });
    document.getElementById('modalStartDate').textContent = new Date(project.startDate).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
    });
    document.getElementById('modalEndDate').textContent = new Date(project.endDate).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
    });
    
    // Project Details
    document.getElementById('modalProjectTitleDetail').textContent = project.title;
    document.getElementById('modalResearchType').textContent = project.researchType.charAt(0).toUpperCase() + project.researchType.slice(1);
    document.getElementById('modalDepartment').textContent = project.department;
    document.getElementById('modalAbstract').textContent = project.abstract;
    
    // Objectives
    const objectivesList = document.getElementById('modalObjectives');
    objectivesList.innerHTML = '';
    project.objectives.forEach(obj => {
        const li = document.createElement('li');
        li.textContent = obj;
        objectivesList.appendChild(li);
    });
    
    // Team
    const teamGrid = document.getElementById('modalTeam');
    teamGrid.innerHTML = '';
    project.team.forEach(member => {
        const div = document.createElement('div');
        div.className = 'team-member';
        div.innerHTML = `
            <div class="member-avatar">${member.initials}</div>
            <div class="member-info">
                <div class="member-name">${member.name}</div>
                <div class="member-role">${member.role}</div>
            </div>
        `;
        teamGrid.appendChild(div);
    });
    
    // Milestones
    const milestonesContainer = document.getElementById('modalMilestones');
    milestonesContainer.innerHTML = '';
    project.milestones.forEach(milestone => {
        const div = document.createElement('div');
        div.className = `milestone-item ${milestone.status}`;
        div.innerHTML = `
            <div class="milestone-title">
                ${milestone.title}
                <span class="milestone-status ${milestone.status}">${milestone.status.toUpperCase()}</span>
            </div>
            <div class="milestone-date">
                <i class="ti ti-calendar"></i> ${new Date(milestone.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
            </div>
        `;
        milestonesContainer.appendChild(div);
    });
    
    // Activity
    const activityContainer = document.getElementById('modalActivity');
    activityContainer.innerHTML = '';
    project.activity.forEach(item => {
        const div = document.createElement('div');
        div.className = 'activity-item';
        div.innerHTML = `
            <div class="activity-icon">
                <i class="ti ti-activity"></i>
            </div>
            <div class="activity-content">
                <div class="activity-text">${item.text}</div>
                <div class="activity-time">${item.time}</div>
            </div>
        `;
        activityContainer.appendChild(div);
    });
    
    // Comments
    document.getElementById('modalComments').value = project.reviewNotes || '';
    
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    document.getElementById('projectModal').style.display = 'none';
    document.body.style.overflow = '';
    selectedProject = null;
}

function updateProjectStatus(status) {
    if (!selectedProject) return;
    
    selectedProject.status = status;
    if (status === 'completed') {
        selectedProject.progress = 100;
    }
    
    saveChanges();
    
    const statusLabels = {
        'on-hold': 'On Hold',
        'pending-review': 'Pending Review',
        'completed': 'Completed'
    };
    
    showNotification(`Project status updated to ${statusLabels[status] || status}!`, 'success');
    closeModal();
}

function saveReviewNotes() {
    if (!selectedProject) return;
    
    const comments = document.getElementById('modalComments').value.trim();
    selectedProject.reviewNotes = comments;
    
    saveChanges();
    showNotification('Review notes saved successfully!', 'success');
}

function saveChanges() {
    const index = currentProjects.findIndex(p => p.id === selectedProject.id);
    if (index !== -1) {
        currentProjects[index] = selectedProject;
    }
    
    renderProjects(currentProjects);
    updateStats(currentProjects);
    updateProjectCount(currentProjects.length);
}

function setQuickFilter(type) {
    currentFilter = type;
    
    // Update active button
    document.querySelectorAll('.quick-filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    applyFilters();
}

function applyFilters() {
    const statusFilter = document.getElementById('statusFilter').value;
    const projectTypeFilter = document.getElementById('projectTypeFilter').value;
    const departmentFilter = document.getElementById('departmentFilter').value;
    const progressFilter = document.getElementById('progressFilter').value;
    const searchQuery = document.getElementById('searchInput').value.toLowerCase().trim();
    
    let filtered = JSON.parse(JSON.stringify(currentProjects));
    
    // Quick filter
    if (currentFilter === 'faculty') {
        filtered = filtered.filter(p => p.type === 'faculty');
    } else if (currentFilter === 'student') {
        filtered = filtered.filter(p => p.type === 'student');
    } else if (currentFilter === 'in-progress') {
        filtered = filtered.filter(p => p.status === 'in-progress');
    } else if (currentFilter === 'completed') {
        filtered = filtered.filter(p => p.status === 'completed');
    }
    
    // Status filter
    if (statusFilter) {
        filtered = filtered.filter(p => p.status === statusFilter);
    }
    
    // Project type filter
    if (projectTypeFilter) {
        filtered = filtered.filter(p => p.type === projectTypeFilter);
    }
    
    // Department filter
    if (departmentFilter) {
        filtered = filtered.filter(p => 
            p.department.toLowerCase().replace(' ', '-') === departmentFilter
        );
    }
    
    // Progress filter
    if (progressFilter) {
        const [min, max] = progressFilter.split('-').map(Number);
        filtered = filtered.filter(p => {
            const progress = p.progress;
            if (max) {
                return progress >= min && progress <= max;
            } else {
                return progress >= min;
            }
        });
    }
    
    // Search
    if (searchQuery) {
        filtered = filtered.filter(p => 
            p.title.toLowerCase().includes(searchQuery) ||
            p.abstract.toLowerCase().includes(searchQuery) ||
            p.department.toLowerCase().includes(searchQuery) ||
            p.team.some(m => m.name.toLowerCase().includes(searchQuery))
        );
    }
    
    renderProjects(filtered);
    updateStats(filtered);
    updateProjectCount(filtered.length);
    
    if (filtered.length === 0) {
        showNotification('No projects match your filters.', 'warning');
    }
}

function applySearch() {
    applyFilters();
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