// ============================================
// STUDENT RESEARCH PROJECT MANAGEMENT
// ============================================

// Faculty Data
const facultyData = [
    { id: 1, name: "Dr. Sarah Johnson", department: "computer-science", email: "sarah.johnson@university.edu", researchAreas: ["AI", "Machine Learning", "Data Science"] },
    { id: 2, name: "Prof. Michael Chen", department: "computer-science", email: "michael.chen@university.edu", researchAreas: ["Blockchain", "Cybersecurity", "Distributed Systems"] },
    { id: 3, name: "Prof. Robert Williams", department: "engineering", email: "robert.williams@university.edu", researchAreas: ["Sustainable Energy", "Solar Power", "Energy Systems"] },
    { id: 4, name: "Dr. Lisa Park", department: "engineering", email: "lisa.park@university.edu", researchAreas: ["Biomedical Engineering", "Biometrics"] },
    { id: 5, name: "Dr. Maria Garcia", department: "physics", email: "maria.garcia@university.edu", researchAreas: ["Quantum Computing", "Quantum Physics"] },
    { id: 6, name: "Dr. Thomas Lee", department: "physics", email: "thomas.lee@university.edu", researchAreas: ["Theoretical Physics", "Particle Physics"] },
    { id: 7, name: "Prof. David Kim", department: "mathematics", email: "david.kim@university.edu", researchAreas: ["Machine Learning", "Statistics", "Data Science"] },
    { id: 8, name: "Dr. Rachel Chen", department: "mathematics", email: "rachel.chen@university.edu", researchAreas: ["Climate Modeling", "Applied Mathematics"] },
    { id: 9, name: "Dr. James Wilson", department: "computer-science", email: "james.wilson@university.edu", researchAreas: ["Blockchain", "Smart Contracts"] },
    { id: 10, name: "Prof. Laura Chen", department: "engineering", email: "laura.chen@university.edu", researchAreas: ["Security Systems", "Biometrics"] },
    { id: 11, name: "Dr. Amanda Foster", department: "biology", email: "amanda.foster@university.edu", researchAreas: ["Molecular Biology", "Drug Discovery"] },
    { id: 12, name: "Prof. Anna Martinez", department: "computer-science", email: "anna.martinez@university.edu", researchAreas: ["Blockchain", "Cryptography"] },
    { id: 13, name: "Dr. Peter Park", department: "engineering", email: "peter.park@university.edu", researchAreas: ["Biometrics", "Signal Processing"] },
    { id: 14, name: "Prof. Kevin Brown", department: "engineering", email: "kevin.brown@university.edu", researchAreas: ["Security", "Authentication"] }
];

// Projects Data
let projectsData = [
    {
        id: 1,
        title: "AI-Driven Predictive Analytics for Student Success",
        leadResearcher: "Dr. Sarah Johnson",
        department: "computer-science",
        status: "active",
        priority: "high",
        startDate: "2024-01-15",
        deadline: "2024-06-30",
        description: "Developing machine learning models to predict student performance and identify at-risk students early.",
        objectives: [
            "Build predictive models using ensemble learning",
            "Create interactive dashboard for faculty",
            "Pilot program with 500 students",
            "Publish research paper"
        ],
        teamMembers: [
            { name: "Dr. Sarah Johnson", role: "Lead Researcher" },
            { name: "Prof. Michael Chen", role: "Co-Researcher" },
            { name: "Dr. Emily Davis", role: "Data Scientist" }
        ],
        facultyId: 1,
        availableSlots: 3,
        totalSlots: 5,
        progress: 65,
        createdAt: "2024-01-10",
        updatedAt: "2024-03-15"
    },
    {
        id: 2,
        title: "Sustainable Energy Solutions for Campus Facilities",
        leadResearcher: "Prof. Robert Williams",
        department: "engineering",
        status: "active",
        priority: "medium",
        startDate: "2024-02-01",
        deadline: "2024-08-31",
        description: "Researching and implementing sustainable energy solutions for campus buildings.",
        objectives: [
            "Complete comprehensive energy audit",
            "Evaluate solar panel feasibility",
            "Develop implementation roadmap"
        ],
        teamMembers: [
            { name: "Prof. Robert Williams", role: "Lead Researcher" },
            { name: "Dr. Lisa Park", role: "Energy Systems Specialist" }
        ],
        facultyId: 3,
        availableSlots: 2,
        totalSlots: 4,
        progress: 40,
        createdAt: "2024-01-25",
        updatedAt: "2024-03-10"
    },
    {
        id: 3,
        title: "Quantum Computing Applications in Drug Discovery",
        leadResearcher: "Dr. Maria Garcia",
        department: "physics",
        status: "pending",
        priority: "high",
        startDate: "2024-03-01",
        deadline: "2024-12-31",
        description: "Exploring quantum computing algorithms for molecular simulation in drug discovery.",
        objectives: [
            "Develop quantum algorithms for molecular simulation",
            "Test algorithms on quantum hardware",
            "Collaborate with pharmaceutical partners"
        ],
        teamMembers: [
            { name: "Dr. Maria Garcia", role: "Lead Researcher" },
            { name: "Dr. Thomas Lee", role: "Quantum Physicist" }
        ],
        facultyId: 5,
        availableSlots: 4,
        totalSlots: 4,
        progress: 15,
        createdAt: "2024-02-15",
        updatedAt: "2024-03-05"
    },
    {
        id: 4,
        title: "Machine Learning for Climate Pattern Prediction",
        leadResearcher: "Prof. David Kim",
        department: "mathematics",
        status: "completed",
        priority: "medium",
        startDate: "2023-09-01",
        deadline: "2024-02-28",
        description: "Using advanced machine learning models to predict climate patterns and extreme weather events.",
        objectives: [
            "Collect and preprocess climate data",
            "Train ensemble ML models",
            "Validate predictions against historical data"
        ],
        teamMembers: [
            { name: "Prof. David Kim", role: "Lead Researcher" },
            { name: "Dr. Rachel Chen", role: "Climate Data Scientist" }
        ],
        facultyId: 7,
        availableSlots: 0,
        totalSlots: 3,
        progress: 100,
        createdAt: "2023-08-15",
        updatedAt: "2024-03-01"
    }
];

// Student Applications Data
let studentApplications = [
    {
        id: 1,
        projectId: 1,
        studentName: "John Doe",
        studentId: "2024001",
        studentRole: "Lead Researcher",
        motivation: "I am passionate about AI and have completed several machine learning courses.",
        skills: "Python, TensorFlow, Data Analysis",
        availability: 15,
        teamMembers: [
            { name: "Jane Smith", role: "Co-Researcher" },
            { name: "Mike Johnson", role: "Research Assistant" }
        ],
        facultyId: 1,
        department: "computer-science",
        status: "approved",
        appliedDate: "2024-02-01",
        reviewedDate: "2024-02-10",
        facultyFeedback: "Excellent proposal. You're approved to start the project."
    },
    {
        id: 2,
        projectId: 2,
        studentName: "John Doe",
        studentId: "2024001",
        studentRole: "Research Assistant",
        motivation: "I'm interested in sustainable energy and have worked on solar panel projects.",
        skills: "Renewable Energy, MATLAB",
        availability: 10,
        teamMembers: [
            { name: "Sarah Wilson", role: "Data Analyst" }
        ],
        facultyId: 3,
        department: "engineering",
        status: "pending",
        appliedDate: "2024-03-01",
        reviewedDate: null,
        facultyFeedback: null
    }
];

// State variables
let currentTab = 'all-projects';
let currentStep = 1;
let totalSteps = 4;
let appTeamMembers = [];
let selectedFacultyId = null;

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    initializePage();
    setupEventListeners();
});

function initializePage() {
    updateStats();
    renderProjects();
    renderApplications();
    renderTeamMembers();
    showNotification('Research projects loaded successfully', 'success');
}

function setupEventListeners() {
    document.getElementById('departmentFilter').addEventListener('change', applyFilters);
    document.getElementById('statusFilter').addEventListener('change', applyFilters);
    document.getElementById('searchInput').addEventListener('keyup', function(e) {
        if (e.key === 'Enter') applyFilters();
    });
}

// ============================================
// TAB SWITCHING
// ============================================

function switchTab(tabName) {
    currentTab = tabName;
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) btn.classList.add('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById('tab-' + tabName).classList.add('active');
}

// ============================================
// STATS UPDATES
// ============================================

function updateStats() {
    const total = projectsData.length;
    const active = projectsData.filter(p => p.status === 'active').length;
    const pendingApps = studentApplications.filter(a => a.status === 'pending').length;
    const approvedApps = studentApplications.filter(a => a.status === 'approved').length;
    
    // Get unique team members from applications
    const teamSet = new Set();
    studentApplications.forEach(app => {
        app.teamMembers.forEach(m => teamSet.add(m.name));
        teamSet.add(app.studentName);
    });

    document.getElementById('statTotalProjects').textContent = total;
    document.getElementById('statActiveProjects').textContent = active;
    document.getElementById('statPendingProjects').textContent = pendingApps;
    document.getElementById('statApprovedProjects').textContent = approvedApps;
    document.getElementById('statTeamMembers').textContent = teamSet.size;
    document.getElementById('statMyApplications').textContent = studentApplications.length;
}

// ============================================
// RENDER PROJECTS
// ============================================

function renderProjects() {
    const grid = document.getElementById('projectGrid');
    const departmentFilter = document.getElementById('departmentFilter').value;
    const statusFilter = document.getElementById('statusFilter').value;
    const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();

    let filtered = projectsData.filter(p => {
        let match = true;
        if (departmentFilter && p.department !== departmentFilter) match = false;
        if (statusFilter && p.status !== statusFilter) match = false;
        if (searchTerm) {
            const searchable = [p.title, p.leadResearcher, p.department].join(' ').toLowerCase();
            if (!searchable.includes(searchTerm)) match = false;
        }
        return match;
    });

    document.getElementById('projectCount').textContent = filtered.length + ' Projects';

    if (filtered.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="ti ti-folder-off"></i>
                <p>No projects found</p>
                <p class="empty-sub">Try adjusting your filters</p>
            </div>
        `;
        return;
    }

    let html = '';
    filtered.forEach(project => {
        const hasApplied = studentApplications.some(a => a.projectId === project.id);
        const faculty = facultyData.find(f => f.id === project.facultyId);
        const progress = project.progress || 0;

        html += `
            <div class="project-card">
                <div class="project-header">
                    <h4 class="project-title">${project.title}</h4>
                    <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 4px;">
                        <span class="project-id-badge">#${String(project.id).padStart(4, '0')}</span>
                        <span class="priority-badge ${project.priority}">${project.priority.toUpperCase()}</span>
                    </div>
                </div>
                <div class="project-meta">
                    <span><i class="ti ti-user"></i> ${project.leadResearcher}</span>
                    <span><i class="ti ti-building"></i> ${project.department.replace('-', ' ').toUpperCase()}</span>
                    <span class="status-badge ${project.status}">${project.status.toUpperCase()}</span>
                    ${hasApplied ? '<span class="status-badge pending"><i class="ti ti-check"></i> Applied</span>' : ''}
                </div>
                <p class="project-description">${project.description}</p>
                <div class="project-slots">
                    <span><i class="ti ti-users"></i> ${project.availableSlots || 0} / ${project.totalSlots || 0} slots available</span>
                </div>
                <div class="progress-container">
                    <div class="progress-label">
                        <span>Progress</span>
                        <span>${progress}%</span>
                    </div>
                    <div class="progress-bar-container">
                        <div class="progress-bar-fill" style="width: ${progress}%;"></div>
                    </div>
                </div>
                <div class="project-footer">
                    <span class="project-date">
                        <i class="ti ti-calendar"></i> Deadline: ${formatDate(project.deadline)}
                    </span>
                    <div style="display: flex; gap: 8px;">
                        <button class="view-details-link" onclick="viewProjectDetails(${project.id})">
                            View Details <i class="ti ti-arrow-right"></i>
                        </button>
                        ${!hasApplied && project.availableSlots > 0 ? 
                            `<button class="apply-btn" onclick="openNewApplicationModalWithProject(${project.id})">
                                <i class="ti ti-send"></i> Apply
                            </button>` : ''
                        }
                    </div>
                </div>
                ${faculty ? `
                    <div style="margin-top: 8px; padding: 8px 12px; background: #f0f7ff; border-radius: 6px; font-size: 12px; color: var(--text-secondary);">
                        <i class="ti ti-user"></i> Faculty: ${faculty.name}
                    </div>
                ` : ''}
            </div>
        `;
    });

    grid.innerHTML = html;
}

// ============================================
// RENDER APPLICATIONS
// ============================================

function renderApplications() {
    const grid = document.getElementById('applicationsGrid');
    document.getElementById('myApplicationsCount').textContent = studentApplications.length + ' Applications';

    if (studentApplications.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="ti ti-file-off"></i>
                <p>No applications yet</p>
                <p class="empty-sub">Submit a new application to get started!</p>
            </div>
        `;
        return;
    }

    let html = '';
    studentApplications.forEach(app => {
        const project = projectsData.find(p => p.id === app.projectId);
        const faculty = facultyData.find(f => f.id === app.facultyId);

        html += `
            <div class="application-card status-${app.status}">
                <div class="app-header">
                    <h4 class="app-title">${project ? project.title : 'Unknown Project'}</h4>
                    <span class="app-status-badge ${app.status}">
                        <i class="ti ${app.status === 'pending' ? 'ti-clock' : app.status === 'approved' ? 'ti-check-circle' : 'ti-x-circle'}"></i>
                        ${app.status.toUpperCase()}
                    </span>
                </div>
                <div class="app-meta">
                    <div class="app-meta-item">
                        <label>Faculty Supervisor</label>
                        <span>${faculty ? faculty.name : 'N/A'}</span>
                    </div>
                    <div class="app-meta-item">
                        <label>Department</label>
                        <span>${app.department.replace('-', ' ').toUpperCase()}</span>
                    </div>
                    <div class="app-meta-item">
                        <label>Your Role</label>
                        <span>${app.studentRole}</span>
                    </div>
                    <div class="app-meta-item">
                        <label>Applied Date</label>
                        <span>${formatDate(app.appliedDate)}</span>
                    </div>
                </div>
                <div class="app-team-members">
                    <label style="font-size: 12px; color: var(--text-secondary);">Team Members</label>
                    <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px;">
                        <span class="team-tag" style="background: var(--primary-blue); color: white;">
                            ${app.studentName} (You - ${app.studentRole})
                        </span>
                        ${app.teamMembers.map(m => `
                            <span class="team-tag">${m.name} (${m.role})</span>
                        `).join('')}
                    </div>
                </div>
                ${app.facultyFeedback ? `
                    <div class="faculty-feedback">
                        <span class="feedback-label"><i class="ti ti-message"></i> Faculty Feedback</span>
                        <p class="feedback-text">${app.facultyFeedback}</p>
                        ${app.reviewedDate ? `<span class="feedback-date">Reviewed on ${formatDate(app.reviewedDate)}</span>` : ''}
                    </div>
                ` : app.status === 'pending' ? `
                    <div style="padding: 12px; background: var(--primary-orange-light); border-radius: 8px; text-align: center; margin-top: 10px;">
                        <i class="ti ti-clock" style="color: var(--primary-orange);"></i>
                        <span style="color: var(--primary-orange); font-weight: 500; margin-left: 8px;">Waiting for faculty review</span>
                    </div>
                ` : ''}
                <div class="app-footer">
                    <span class="app-date">
                        <i class="ti ti-calendar"></i> ${app.status === 'pending' ? 'Under Review' : 'Reviewed'}
                    </span>
                    <div class="app-actions">
                        <button class="view-btn" onclick="viewApplicationDetails(${app.projectId})">
                            <i class="ti ti-eye"></i> View Details
                        </button>
                    </div>
                </div>
            </div>
        `;
    });

    grid.innerHTML = html;
}

// ============================================
// RENDER TEAM MEMBERS
// ============================================

function renderTeamMembers() {
    const grid = document.getElementById('teamGrid');
    const allTeamMembers = [];
    
    studentApplications.forEach(app => {
        allTeamMembers.push({ name: app.studentName, role: app.studentRole, project: app.projectId, status: app.status });
        app.teamMembers.forEach(m => {
            allTeamMembers.push({ ...m, project: app.projectId, status: app.status });
        });
    });

    document.getElementById('teamCount').textContent = allTeamMembers.length + ' Members';

    if (allTeamMembers.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="ti ti-users"></i>
                <p>No team members yet</p>
                <p class="empty-sub">Join a project to collaborate with team members</p>
            </div>
        `;
        return;
    }

    const projectMap = {};
    projectsData.forEach(p => projectMap[p.id] = p.title);

    grid.innerHTML = allTeamMembers.map(m => `
        <div class="team-member-card">
            <div class="team-member-avatar">${getInitials(m.name)}</div>
            <div class="team-member-info">
                <h4>${m.name}</h4>
                <p>${m.role}</p>
                <span class="team-member-project">${projectMap[m.project] || 'Unknown Project'}</span>
                <span class="status-badge ${m.status}" style="font-size: 10px; padding: 2px 8px; margin-top: 4px;">${m.status}</span>
            </div>
        </div>
    `).join('');
}

// ============================================
// NEW APPLICATION MODAL
// ============================================

function openNewApplicationModal() {
    resetApplicationForm();
    currentStep = 1;
    document.getElementById('newApplicationModal').style.display = 'flex';
    updateStepVisibility();
}

function openNewApplicationModalWithProject(projectId) {
    openNewApplicationModal();
    const project = projectsData.find(p => p.id === projectId);
    if (project) {
        document.getElementById('appDepartment').value = project.department;
        updateFacultySelect();
        document.getElementById('appProjectTitle').value = project.title;
        document.getElementById('appProjectDescription').value = project.description;
        document.getElementById('appProjectObjectives').value = project.objectives.join('\n');
    }
}

function resetApplicationForm() {
    document.getElementById('newApplicationForm').reset();
    appTeamMembers = [];
    document.getElementById('appTeamTags').innerHTML = '<span style="color: var(--text-light); font-size: 13px;">No team members added</span>';
    document.getElementById('appTeamMembers').value = '[]';
    document.getElementById('facultyDetails').style.display = 'none';
}

function updateFacultySelect() {
    const dept = document.getElementById('appDepartment').value;
    const select = document.getElementById('appFaculty');
    select.innerHTML = '<option value="">Select Faculty</option>';
    
    const faculties = facultyData.filter(f => f.department === dept);
    faculties.forEach(f => {
        const option = document.createElement('option');
        option.value = f.id;
        option.textContent = `${f.name} (${f.researchAreas.join(', ')})`;
        select.appendChild(option);
    });

    if (faculties.length === 0) {
        select.innerHTML = '<option value="">No faculty available in this department</option>';
    }
}

function updateFacultyDetails() {
    const facultyId = parseInt(document.getElementById('appFaculty').value);
    const faculty = facultyData.find(f => f.id === facultyId);
    const details = document.getElementById('facultyDetails');
    
    if (faculty) {
        document.getElementById('facultyName').textContent = faculty.name;
        document.getElementById('facultyDept').textContent = faculty.department.replace('-', ' ').toUpperCase();
        document.getElementById('facultyEmail').textContent = faculty.email;
        details.style.display = 'block';
    } else {
        details.style.display = 'none';
    }
}

// Add event listener for faculty selection
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('appFaculty').addEventListener('change', updateFacultyDetails);
});

function addAppTeamMember() {
    const input = document.getElementById('appTeamMemberInput');
    const roleSelect = document.getElementById('appTeamMemberRole');
    const name = input.value.trim();
    const role = roleSelect.value;

    if (!name) {
        showNotification('Please enter a team member name', 'warning');
        return;
    }

    if (appTeamMembers.some(m => m.name.toLowerCase() === name.toLowerCase())) {
        showNotification('Team member already exists', 'warning');
        return;
    }

    appTeamMembers.push({ name, role });
    input.value = '';
    renderAppTeamTags();
}

function renderAppTeamTags() {
    const container = document.getElementById('appTeamTags');
    if (appTeamMembers.length === 0) {
        container.innerHTML = '<span style="color: var(--text-light); font-size: 13px;">No team members added</span>';
        document.getElementById('appTeamMembers').value = '[]';
        return;
    }

    container.innerHTML = appTeamMembers.map((m, index) => `
        <span class="team-tag">
            ${m.name} (${m.role})
            <span class="remove-tag" onclick="removeAppTeamMember(${index})">&times;</span>
        </span>
    `).join('');

    document.getElementById('appTeamMembers').value = JSON.stringify(appTeamMembers);
}

function removeAppTeamMember(index) {
    appTeamMembers.splice(index, 1);
    renderAppTeamTags();
}

// ============================================
// STEP NAVIGATION
// ============================================

function nextStep() {
    // Validate current step
    if (!validateStep(currentStep)) return;

    if (currentStep < totalSteps) {
        currentStep++;
        updateStepVisibility();
    }
}

function prevStep() {
    if (currentStep > 1) {
        currentStep--;
        updateStepVisibility();
    }
}

function validateStep(step) {
    switch(step) {
        case 1:
            if (!document.getElementById('appDepartment').value) {
                showNotification('Please select a department', 'warning');
                return false;
            }
            return true;
        case 2:
            if (!document.getElementById('appFaculty').value) {
                showNotification('Please select a faculty supervisor', 'warning');
                return false;
            }
            return true;
        case 3:
            if (!document.getElementById('appProjectTitle').value.trim()) {
                showNotification('Please enter a project title', 'warning');
                return false;
            }
            if (!document.getElementById('appProjectDescription').value.trim()) {
                showNotification('Please enter a project description', 'warning');
                return false;
            }
            return true;
        case 4:
            return true;
        default:
            return true;
    }
}

function updateStepVisibility() {
    // Hide all steps
    document.querySelectorAll('.form-step').forEach(el => el.style.display = 'none');
    
    // Show current step
    document.getElementById('step' + currentStep).style.display = 'block';
    
    // Update buttons
    document.getElementById('prevStepBtn').style.display = currentStep > 1 ? 'inline-flex' : 'none';
    document.getElementById('nextStepBtn').style.display = currentStep < totalSteps ? 'inline-flex' : 'none';
    document.getElementById('submitBtn').style.display = currentStep === totalSteps ? 'inline-flex' : 'none';
}

// ============================================
// SUBMIT APPLICATION
// ============================================

function submitNewApplication(e) {
    e.preventDefault();
    showLoading(true);

    const department = document.getElementById('appDepartment').value;
    const facultyId = parseInt(document.getElementById('appFaculty').value);
    const projectTitle = document.getElementById('appProjectTitle').value.trim();
    const projectDescription = document.getElementById('appProjectDescription').value.trim();
    const objectivesText = document.getElementById('appProjectObjectives').value.trim();
    const objectives = objectivesText ? objectivesText.split('\n').filter(o => o.trim()) : [];
    const startDate = document.getElementById('appStartDate').value;
    const duration = parseInt(document.getElementById('appDuration').value) || 6;
    const studentRole = document.getElementById('appStudentRole').value;
    const teamMembers = JSON.parse(document.getElementById('appTeamMembers').value || '[]');

    // Validate
    if (!department || !facultyId || !projectTitle || !projectDescription) {
        showNotification('Please fill in all required fields', 'warning');
        showLoading(false);
        return;
    }

    // Create new project
    const faculty = facultyData.find(f => f.id === facultyId);
    const newProject = {
        id: projectsData.length + 1,
        title: projectTitle,
        leadResearcher: faculty ? faculty.name : 'Unknown',
        department: department,
        status: 'pending',
        priority: 'medium',
        startDate: startDate || new Date().toISOString().split('T')[0],
        deadline: new Date(new Date().setMonth(new Date().getMonth() + duration)).toISOString().split('T')[0],
        description: projectDescription,
        objectives: objectives,
        teamMembers: [{ name: faculty ? faculty.name : 'Unknown', role: 'Faculty Supervisor' }],
        facultyId: facultyId,
        availableSlots: 5,
        totalSlots: 5,
        progress: 0,
        createdAt: new Date().toISOString().split('T')[0],
        updatedAt: new Date().toISOString().split('T')[0]
    };

    projectsData.push(newProject);

    // Create application
    const newApplication = {
        id: studentApplications.length + 1,
        projectId: newProject.id,
        studentName: "John Doe", // In real app, get from logged in user
        studentId: "2024001",
        studentRole: studentRole,
        motivation: projectDescription,
        skills: "Various skills",
        availability: 10,
        teamMembers: teamMembers,
        facultyId: facultyId,
        department: department,
        status: "pending",
        appliedDate: new Date().toISOString().split('T')[0],
        reviewedDate: null,
        facultyFeedback: null
    };

    studentApplications.push(newApplication);

    closeModal('newApplicationModal');
    updateStats();
    renderProjects();
    renderApplications();
    renderTeamMembers();
    showNotification('Application submitted successfully!', 'success');
    showLoading(false);
}

// ============================================
// PROJECT DETAIL VIEW
// ============================================

function viewProjectDetails(id) {
    const project = projectsData.find(p => p.id === id);
    if (!project) {
        showNotification('Project not found', 'error');
        return;
    }

    const faculty = facultyData.find(f => f.id === project.facultyId);
    const application = studentApplications.find(a => a.projectId === id);
    
    const modal = document.getElementById('projectDetailModal');
    const body = document.getElementById('projectDetailBody');
    document.getElementById('detailModalTitle').textContent = project.title;

    body.innerHTML = `
        <div class="detail-info-grid">
            <div class="info-item">
                <label><i class="ti ti-user"></i> Lead Researcher</label>
                <span>${project.leadResearcher}</span>
            </div>
            <div class="info-item">
                <label><i class="ti ti-building"></i> Department</label>
                <span>${project.department.replace('-', ' ').toUpperCase()}</span>
            </div>
            <div class="info-item">
                <label><i class="ti ti-calendar"></i> Start Date</label>
                <span>${formatDate(project.startDate)}</span>
            </div>
            <div class="info-item">
                <label><i class="ti ti-calendar-check"></i> Deadline</label>
                <span>${formatDate(project.deadline)}</span>
            </div>
            <div class="info-item">
                <label><i class="ti ti-users"></i> Available Slots</label>
                <span>${project.availableSlots} / ${project.totalSlots}</span>
            </div>
            <div class="info-item">
                <label><i class="ti ti-chart-bar"></i> Progress</label>
                <div class="detail-progress">
                    <div class="progress-bar-container">
                        <div class="progress-bar-fill" style="width: ${project.progress}%;"></div>
                    </div>
                    <span>${project.progress}%</span>
                </div>
            </div>
            ${faculty ? `
                <div class="info-item full-width">
                    <label><i class="ti ti-user"></i> Faculty Supervisor</label>
                    <span>${faculty.name}</span>
                    <span style="font-size: 13px; color: var(--text-secondary);">${faculty.researchAreas.join(', ')}</span>
                </div>
            ` : ''}
            <div class="info-item full-width">
                <label><i class="ti ti-file-text"></i> Description</label>
                <p>${project.description}</p>
            </div>
        </div>
        <div style="margin-top: 20px;">
            <h4><i class="ti ti-list"></i> Objectives</h4>
            <ul class="detail-list">
                ${project.objectives.map(obj => `<li>${obj}</li>`).join('')}
            </ul>
        </div>
        <div style="margin-top: 20px;">
            <h4><i class="ti ti-users"></i> Team Members</h4>
            <div class="team-members-grid">
                ${project.teamMembers.map(m => `
                    <div class="team-member-item">
                        <span class="avatar">${getInitials(m.name)}</span>
                        <div>
                            <div class="name">${m.name}</div>
                            <div class="role">${m.role}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--border-color); display: flex; justify-content: flex-end; gap: 12px;">
            ${!application && project.availableSlots > 0 ? 
                `<button class="filter-btn primary-btn" onclick="closeModal('projectDetailModal'); openNewApplicationModalWithProject(${project.id})">
                    <i class="ti ti-send"></i> Apply Now
                </button>` : 
                application ? `
                    <button class="filter-btn" onclick="closeModal('projectDetailModal'); viewApplicationDetails(${project.id})" style="background: var(--primary-blue);">
                        <i class="ti ti-file-text"></i> View Application
                    </button>
                ` : ''
            }
        </div>
    `;

    modal.style.display = 'flex';
}

// ============================================
// APPLICATION DETAIL VIEW
// ============================================

function viewApplicationDetails(projectId) {
    const application = studentApplications.find(a => a.projectId === projectId);
    if (!application) {
        showNotification('Application not found', 'error');
        return;
    }

    const project = projectsData.find(p => p.id === projectId);
    const faculty = facultyData.find(f => f.id === application.facultyId);
    
    const modal = document.getElementById('applicationDetailModal');
    const body = document.getElementById('applicationDetailBody');

    body.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
            <div>
                <h3 style="margin: 0;">${project ? project.title : 'Unknown Project'}</h3>
                <p style="margin: 4px 0 0 0; color: var(--text-secondary);">Supervisor: ${faculty ? faculty.name : 'N/A'}</p>
            </div>
            <span class="app-status-badge ${application.status}">
                <i class="ti ${application.status === 'pending' ? 'ti-clock' : application.status === 'approved' ? 'ti-check-circle' : 'ti-x-circle'}"></i>
                ${application.status.toUpperCase()}
            </span>
        </div>
        
        <div class="app-meta" style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-bottom: 20px; padding: 16px; background: #f8fafc; border-radius: 10px;">
            <div>
                <label style="font-size: 12px; color: var(--text-secondary);">Your Role</label>
                <p style="font-weight: 600; margin: 2px 0;">${application.studentRole}</p>
            </div>
            <div>
                <label style="font-size: 12px; color: var(--text-secondary);">Applied Date</label>
                <p style="font-weight: 600; margin: 2px 0;">${formatDate(application.appliedDate)}</p>
            </div>
            <div>
                <label style="font-size: 12px; color: var(--text-secondary);">Department</label>
                <p style="font-weight: 600; margin: 2px 0;">${application.department.replace('-', ' ').toUpperCase()}</p>
            </div>
        </div>
        
        <div style="margin-bottom: 16px;">
            <label style="font-size: 13px; font-weight: 600; display: block; margin-bottom: 4px;"><i class="ti ti-users"></i> Team Members</label>
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                <span class="team-tag" style="background: var(--primary-blue); color: white;">
                    ${application.studentName} (You - ${application.studentRole})
                </span>
                ${application.teamMembers.map(m => `
                    <span class="team-tag">${m.name} (${m.role})</span>
                `).join('')}
            </div>
        </div>
        
        ${application.facultyFeedback ? `
            <div style="padding: 16px; border-left: 4px solid var(--primary-blue); background: #f0f7ff; border-radius: 8px; margin-bottom: 16px;">
                <label style="font-size: 13px; font-weight: 600; display: block; margin-bottom: 4px;"><i class="ti ti-message"></i> Faculty Feedback</label>
                <p style="margin: 0; color: var(--text-secondary);">${application.facultyFeedback}</p>
                ${application.reviewedDate ? `<p style="margin: 4px 0 0 0; font-size: 12px; color: var(--text-light);">Reviewed on ${formatDate(application.reviewedDate)}</p>` : ''}
            </div>
        ` : application.status === 'pending' ? `
            <div style="padding: 16px; background: var(--primary-orange-light); border-radius: 8px; text-align: center;">
                <i class="ti ti-clock" style="font-size: 24px; color: var(--primary-orange); display: block; margin-bottom: 4px;"></i>
                <p style="margin: 0; color: var(--primary-orange); font-weight: 500;">Your application is under review by the faculty</p>
            </div>
        ` : ''}
        
        ${project ? `
            <div style="margin-top: 16px; padding: 16px; background: #f8fafc; border-radius: 8px; border: 1px solid var(--border-color);">
                <label style="font-size: 13px; font-weight: 600; display: block; margin-bottom: 4px;"><i class="ti ti-folder"></i> Project Information</label>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px;">
                    <div>
                        <span style="font-size: 12px; color: var(--text-secondary);">Status</span>
                        <p style="margin: 2px 0; font-weight: 500;">${project.status.toUpperCase()}</p>
                    </div>
                    <div>
                        <span style="font-size: 12px; color: var(--text-secondary);">Progress</span>
                        <p style="margin: 2px 0; font-weight: 500;">${project.progress}%</p>
                    </div>
                </div>
                <button class="view-details-link" onclick="closeModal('applicationDetailModal'); viewProjectDetails(${project.id})" style="margin-top: 8px;">
                    View Full Project Details <i class="ti ti-arrow-right"></i>
                </button>
            </div>
        ` : ''}
    `;

    modal.style.display = 'flex';
}

// ============================================
// FILTERS
// ============================================

function applyFilters() {
    renderProjects();
}

function resetFilters() {
    document.getElementById('departmentFilter').value = '';
    document.getElementById('statusFilter').value = '';
    document.getElementById('searchInput').value = '';
    renderProjects();
}

function applySearch() {
    renderProjects();
}

// ============================================
// HELPER FUNCTIONS
// ============================================

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function getInitials(name) {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function refreshData() {
    showLoading(true);
    setTimeout(() => {
        updateStats();
        renderProjects();
        renderApplications();
        renderTeamMembers();
        showNotification('Data refreshed successfully!', 'success');
        showLoading(false);
    }, 500);
}

function showLoading(show) {
    document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
}

function showNotification(message, type = 'info') {
    const existing = document.querySelector('.custom-notification');
    if (existing) {
        existing.style.animation = 'slideOutRight 0.4s ease forwards';
        setTimeout(() => existing.remove(), 400);
    }

    const colors = {
        success: '#22c55e',
        error: '#ef4444',
        info: '#2563eb',
        warning: '#f97316'
    };

    const icons = {
        success: 'ti-check-circle',
        error: 'ti-x-circle',
        info: 'ti-info-circle',
        warning: 'ti-alert-triangle'
    };

    const notification = document.createElement('div');
    notification.className = 'custom-notification';
    notification.style.backgroundColor = colors[type] || colors.info;
    notification.innerHTML = `
        <i class="ti ${icons[type] || icons.info}" style="font-size: 20px;"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.4s ease forwards';
        setTimeout(() => notification.remove(), 400);
    }, 3000);
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay').forEach(m => m.style.display = 'none');
    }
});

console.log('Student Research Module Loaded');