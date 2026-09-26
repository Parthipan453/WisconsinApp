// ============================================
// NEW APPLICATION - FORM VALIDATION & SUBMISSION
// ============================================

// Sample Data
const facultyData = [
    { id: 1, name: "Dr. Sarah Johnson", department: "computer-science", email: "sarah.johnson@university.edu", researchAreas: ["AI", "Machine Learning", "Data Science"] },
    { id: 2, name: "Prof. Michael Chen", department: "computer-science", email: "michael.chen@university.edu", researchAreas: ["Blockchain", "Cybersecurity"] },
    { id: 3, name: "Prof. Robert Williams", department: "engineering", email: "robert.williams@university.edu", researchAreas: ["Sustainable Energy", "Solar Power"] },
    { id: 4, name: "Dr. Lisa Park", department: "engineering", email: "lisa.park@university.edu", researchAreas: ["Biomedical Engineering", "Biometrics"] },
    { id: 5, name: "Dr. Maria Garcia", department: "physics", email: "maria.garcia@university.edu", researchAreas: ["Quantum Computing", "Quantum Physics"] },
    { id: 6, name: "Prof. David Kim", department: "mathematics", email: "david.kim@university.edu", researchAreas: ["Machine Learning", "Statistics"] },
    { id: 7, name: "Dr. Rachel Chen", department: "mathematics", email: "rachel.chen@university.edu", researchAreas: ["Climate Modeling", "Applied Mathematics"] },
    { id: 8, name: "Dr. James Wilson", department: "computer-science", email: "james.wilson@university.edu", researchAreas: ["Blockchain", "Smart Contracts"] },
    { id: 9, name: "Prof. Laura Chen", department: "engineering", email: "laura.chen@university.edu", researchAreas: ["Security Systems", "Biometrics"] },
    { id: 10, name: "Dr. Amanda Foster", department: "biology", email: "amanda.foster@university.edu", researchAreas: ["Molecular Biology", "Drug Discovery"] },
];

// Sample applications data for stats
let studentApplications = [
    { id: 1, status: "approved" },
    { id: 2, status: "pending" },
    { id: 3, status: "rejected" },
    { id: 4, status: "pending" },
];

let teamMembers = [];

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    updateStats();
    setupEventListeners();
});

function setupEventListeners() {
    // Funding source change
    document.getElementById('fundingSource').addEventListener('change', function() {
        const detailsGroup = document.getElementById('fundingDetailsGroup');
        if (this.value === 'other' || this.value === 'external-grant' || this.value === 'industry-sponsorship') {
            detailsGroup.style.display = 'block';
        } else {
            detailsGroup.style.display = 'none';
        }
    });

    // Real-time validation on input
    document.getElementById('projectTitle').addEventListener('input', function() {
        validateField('title');
    });
    document.getElementById('researchArea').addEventListener('input', function() {
        validateField('area');
    });
    document.getElementById('projectDescription').addEventListener('input', function() {
        validateField('desc');
    });
    document.getElementById('duration').addEventListener('input', function() {
        validateField('duration');
    });
    document.getElementById('studentRole').addEventListener('change', function() {
        validateField('role');
    });
    document.getElementById('agreeTerms').addEventListener('change', function() {
        validateField('terms');
    });
}

// ============================================
// STATS UPDATES
// ============================================

function updateStats() {
    const total = studentApplications.length;
    const approved = studentApplications.filter(a => a.status === 'approved').length;
    const pending = studentApplications.filter(a => a.status === 'pending').length;
    const rejected = studentApplications.filter(a => a.status === 'rejected').length;

    document.getElementById('statTotalProjects').textContent = total;
    document.getElementById('statActiveProjects').textContent = approved;
    document.getElementById('statPendingProjects').textContent = pending;
    document.getElementById('statRejectedProjects').textContent = rejected;
}

// ============================================
// APPLICATION TYPE SELECTION
// ============================================

function selectApplicationType(element, type) {
    document.querySelectorAll('.type-option').forEach(el => el.classList.remove('selected'));
    element.classList.add('selected');
    document.getElementById('applicationType').value = type;
    document.getElementById('typeError').style.display = 'none';

    // Show/hide funding section based on type
    const fundingSection = document.getElementById('fundingSection');
    if (type === 'external-funding') {
        fundingSection.style.display = 'block';
    } else {
        fundingSection.style.display = 'block';
    }
}

// ============================================
// DEPARTMENT SELECTION
// ============================================

function selectDepartment(element, department) {
    document.querySelectorAll('.dept-option').forEach(el => el.classList.remove('selected'));
    element.classList.add('selected');
    document.getElementById('selectedDepartment').value = department;
    document.getElementById('deptError').style.display = 'none';
    
    // Show faculty section and load faculty
    document.getElementById('facultySection').style.display = 'block';
    loadFaculty(department);
}

function loadFaculty(department) {
    const grid = document.getElementById('facultyGrid');
    const faculty = facultyData.filter(f => f.department === department);
    
    if (faculty.length === 0) {
        grid.innerHTML = '<p style="color: var(--text-secondary);">No faculty members available in this department.</p>';
        return;
    }

    grid.innerHTML = faculty.map(f => `
        <div class="faculty-card" onclick="selectFaculty(this, ${f.id})">
            <div class="faculty-name">${f.name}</div>
            <div class="faculty-dept">${f.department.replace('-', ' ').toUpperCase()}</div>
            <div class="faculty-email">${f.email}</div>
            <div class="research-tags">
                ${f.researchAreas.map(area => `<span class="research-tag">${area}</span>`).join('')}
            </div>
        </div>
    `).join('');
}

function selectFaculty(element, facultyId) {
    document.querySelectorAll('.faculty-card').forEach(el => el.classList.remove('selected'));
    element.classList.add('selected');
    document.getElementById('selectedFaculty').value = facultyId;
    document.getElementById('facultyError').style.display = 'none';
}

// ============================================
// TEAM MEMBER MANAGEMENT
// ============================================

function addTeamMember() {
    const nameInput = document.getElementById('teamMemberName');
    const roleSelect = document.getElementById('teamMemberRole');
    const name = nameInput.value.trim();
    const role = roleSelect.value;

    if (!name) {
        showNotification('Please enter a team member name', 'warning');
        return;
    }

    if (teamMembers.some(m => m.name.toLowerCase() === name.toLowerCase())) {
        showNotification('Team member already exists', 'warning');
        return;
    }

    teamMembers.push({ name, role });
    nameInput.value = '';
    renderTeamMembers();
}

function removeTeamMember(index) {
    teamMembers.splice(index, 1);
    renderTeamMembers();
}

function renderTeamMembers() {
    const list = document.getElementById('teamMembersList');
    
    if (teamMembers.length === 0) {
        list.innerHTML = '<div class="empty-team-message">No team members added yet</div>';
        return;
    }

    list.innerHTML = teamMembers.map((m, index) => `
        <span class="team-member-tag">
            ${m.name}
            <span class="role">(${m.role})</span>
            <span class="remove-btn" onclick="removeTeamMember(${index})">&times;</span>
        </span>
    `).join('');
}

// ============================================
// FORM VALIDATION
// ============================================

function validateForm() {
    let isValid = true;

    // Validate Application Type
    if (!document.getElementById('applicationType').value) {
        document.getElementById('typeError').style.display = 'block';
        isValid = false;
    } else {
        document.getElementById('typeError').style.display = 'none';
    }

    // Validate Department
    if (!document.getElementById('selectedDepartment').value) {
        document.getElementById('deptError').style.display = 'block';
        isValid = false;
    } else {
        document.getElementById('deptError').style.display = 'none';
    }

    // Validate Faculty
    if (!document.getElementById('selectedFaculty').value) {
        document.getElementById('facultyError').style.display = 'block';
        isValid = false;
    } else {
        document.getElementById('facultyError').style.display = 'none';
    }

    // Validate Title
    if (!document.getElementById('projectTitle').value.trim()) {
        document.getElementById('titleError').style.display = 'block';
        isValid = false;
    } else {
        document.getElementById('titleError').style.display = 'none';
    }

    // Validate Research Area
    if (!document.getElementById('researchArea').value.trim()) {
        document.getElementById('areaError').style.display = 'block';
        isValid = false;
    } else {
        document.getElementById('areaError').style.display = 'none';
    }

    // Validate Description
    if (!document.getElementById('projectDescription').value.trim()) {
        document.getElementById('descError').style.display = 'block';
        isValid = false;
    } else {
        document.getElementById('descError').style.display = 'none';
    }

    // Validate Duration
    const duration = parseInt(document.getElementById('duration').value);
    if (duration && (duration < 1 || duration > 36)) {
        document.getElementById('durationError').style.display = 'block';
        isValid = false;
    } else {
        document.getElementById('durationError').style.display = 'none';
    }

    // Validate Role
    if (!document.getElementById('studentRole').value) {
        document.getElementById('roleError').style.display = 'block';
        isValid = false;
    } else {
        document.getElementById('roleError').style.display = 'none';
    }

    // Validate Terms
    if (!document.getElementById('agreeTerms').checked) {
        document.getElementById('termsError').style.display = 'block';
        isValid = false;
    } else {
        document.getElementById('termsError').style.display = 'none';
    }

    return isValid;
}

function validateField(field) {
    switch(field) {
        case 'title':
            if (document.getElementById('projectTitle').value.trim()) {
                document.getElementById('titleError').style.display = 'none';
            }
            break;
        case 'area':
            if (document.getElementById('researchArea').value.trim()) {
                document.getElementById('areaError').style.display = 'none';
            }
            break;
        case 'desc':
            if (document.getElementById('projectDescription').value.trim()) {
                document.getElementById('descError').style.display = 'none';
            }
            break;
        case 'duration':
            const duration = parseInt(document.getElementById('duration').value);
            if (!duration || (duration >= 1 && duration <= 36)) {
                document.getElementById('durationError').style.display = 'none';
            }
            break;
        case 'role':
            if (document.getElementById('studentRole').value) {
                document.getElementById('roleError').style.display = 'none';
            }
            break;
        case 'terms':
            if (document.getElementById('agreeTerms').checked) {
                document.getElementById('termsError').style.display = 'none';
            }
            break;
    }
}

// ============================================
// FORM SUBMISSION
// ============================================

function submitApplication(e) {
    e.preventDefault();
    
    if (!validateForm()) {
        showNotification('Please fix the validation errors', 'error');
        // Scroll to first error
        const firstError = document.querySelector('.validation-error[style*="display: block"]');
        if (firstError) {
            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        return;
    }

    showLoading(true);

    // Collect form data
    const formData = {
        applicationType: document.getElementById('applicationType').value,
        department: document.getElementById('selectedDepartment').value,
        facultyId: parseInt(document.getElementById('selectedFaculty').value),
        projectTitle: document.getElementById('projectTitle').value.trim(),
        researchArea: document.getElementById('researchArea').value.trim(),
        description: document.getElementById('projectDescription').value.trim(),
        objectives: document.getElementById('projectObjectives').value.trim().split('\n').filter(o => o.trim()),
        startDate: document.getElementById('startDate').value,
        duration: parseInt(document.getElementById('duration').value) || null,
        fundingSource: document.getElementById('fundingSource').value,
        fundingDetails: document.getElementById('fundingDetails').value.trim(),
        estimatedBudget: parseFloat(document.getElementById('estimatedBudget').value) || null,
        fundingStatus: document.getElementById('fundingStatus').value,
        studentRole: document.getElementById('studentRole').value,
        teamMembers: teamMembers,
        teamRolesDescription: document.getElementById('teamRolesDescription').value.trim(),
        motivation: document.getElementById('motivation').value.trim(),
        skills: document.getElementById('skills').value.trim(),
        availability: parseInt(document.getElementById('availability').value) || null,
        submittedAt: new Date().toISOString()
    };

    console.log('Application Data:', formData);

    // Simulate API call
    setTimeout(() => {
        showLoading(false);
        
        // Add to applications for stats
        studentApplications.push({
            id: studentApplications.length + 1,
            status: 'pending'
        });
        updateStats();

        // Show success modal
        document.getElementById('successModal').style.display = 'flex';
        
        // Reset form
        // Don't reset yet, keep data for review
    }, 1500);
}

// ============================================
// FORM RESET
// ============================================

function resetForm() {
    if (!confirm('Are you sure you want to reset the form? All entered data will be lost.')) {
        return;
    }

    document.getElementById('applicationForm').reset();
    document.querySelectorAll('.dept-option').forEach(el => el.classList.remove('selected'));
    document.querySelectorAll('.faculty-card').forEach(el => el.classList.remove('selected'));
    document.querySelectorAll('.type-option').forEach(el => el.classList.remove('selected'));
    
    document.getElementById('selectedDepartment').value = '';
    document.getElementById('selectedFaculty').value = '';
    document.getElementById('applicationType').value = '';
    document.getElementById('facultySection').style.display = 'none';
    document.getElementById('fundingDetailsGroup').style.display = 'none';
    
    teamMembers = [];
    renderTeamMembers();
    
    // Clear validation errors
    document.querySelectorAll('.validation-error').forEach(el => el.style.display = 'none');
    
    showNotification('Form has been reset', 'info');
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

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

// Close modal on outside click
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.style.display = 'none';
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay').forEach(m => m.style.display = 'none');
    }
});

console.log('New Application Module Loaded');