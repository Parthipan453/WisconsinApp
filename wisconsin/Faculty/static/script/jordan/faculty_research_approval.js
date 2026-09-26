// Faculty Research Approval JavaScript

// Sample data
const sampleData = {
    requests: [
        {
            id: 1,
            projectTitle: "AI-Based Student Performance Prediction System",
            researchType: "thesis",
            status: "pending",
            submissionDate: "2026-07-01",
            student: {
                name: "Ahmed Hassan",
                id: "S2024001",
                department: "Computer Science",
                email: "ahmed.hassan@university.edu",
                year: "4th Year",
                cgpa: "3.85"
            },
            abstract: "This research proposes a machine learning-based system to predict student academic performance using historical data, attendance records, and engagement metrics. The system aims to identify at-risk students early and provide actionable insights for intervention.",
            objectives: [
                "Develop a predictive model using ensemble learning techniques",
                "Analyze the correlation between attendance and academic performance",
                "Create a real-time dashboard for faculty monitoring",
                "Evaluate the model's accuracy across different student demographics"
            ],
            outcomes: [
                "A working prediction system with 85%+ accuracy",
                "Early warning system for at-risk students",
                "Faculty dashboard for performance monitoring",
                "Recommendation system for personalized interventions"
            ],
            facultyComments: ""
        },
        {
            id: 2,
            projectTitle: "Sustainable Energy Solutions for Smart Cities",
            researchType: "project",
            status: "in-review",
            submissionDate: "2026-06-28",
            student: {
                name: "Mariam Al-Fahd",
                id: "S2024015",
                department: "Engineering",
                email: "mariam.alfahd@university.edu",
                year: "3rd Year",
                cgpa: "3.72"
            },
            abstract: "This research explores the integration of renewable energy sources with smart city infrastructure. The study focuses on optimizing energy distribution, reducing carbon footprint, and implementing IoT-based monitoring systems.",
            objectives: [
                "Design a hybrid renewable energy system for urban areas",
                "Develop IoT sensors for real-time energy monitoring",
                "Create an optimization algorithm for energy distribution",
                "Analyze cost-benefit of implementation"
            ],
            outcomes: [
                "A scalable hybrid energy system design",
                "IoT-based monitoring prototype",
                "Energy optimization algorithm",
                "Implementation roadmap for smart cities"
            ],
            facultyComments: "Strong proposal with clear objectives. Please provide more details on the cost analysis methodology."
        },
        {
            id: 3,
            projectTitle: "Blockchain for Secure Academic Credentials",
            researchType: "dissertation",
            status: "pending",
            submissionDate: "2026-06-25",
            student: {
                name: "Omar Al-Saud",
                id: "S2024023",
                department: "Computer Science",
                email: "omar.alsaud@university.edu",
                year: "4th Year",
                cgpa: "3.91"
            },
            abstract: "This research investigates the use of blockchain technology for creating a secure, verifiable system for academic credentials. The proposed system aims to eliminate credential fraud and simplify the verification process for employers.",
            objectives: [
                "Design a blockchain-based credential verification system",
                "Implement smart contracts for automated verification",
                "Ensure GDPR compliance for data privacy",
                "Create a user-friendly interface for verification"
            ],
            outcomes: [
                "A fully functional blockchain credential system",
                "Smart contract implementation",
                "Security audit report",
                "User acceptance testing results"
            ],
            facultyComments: ""
        },
        {
            id: 4,
            projectTitle: "Machine Learning in Medical Diagnosis",
            researchType: "experimental",
            status: "approved",
            submissionDate: "2026-06-20",
            student: {
                name: "Layla Al-Khalifa",
                id: "S2024035",
                department: "Biology",
                email: "layla.alkhalifa@university.edu",
                year: "4th Year",
                cgpa: "3.78"
            },
            abstract: "This research applies deep learning techniques to medical imaging for early detection of diseases. The study focuses on developing a CNN-based model for detecting breast cancer from mammogram images with high accuracy.",
            objectives: [
                "Develop a CNN model for medical image classification",
                "Train model on publicly available medical datasets",
                "Achieve 90%+ accuracy in disease detection",
                "Create a web-based interface for model deployment"
            ],
            outcomes: [
                "High-accuracy detection model",
                "Web-based diagnostic tool",
                "Comprehensive testing results",
                "Research paper publication"
            ],
            facultyComments: "Excellent research proposal. The methodology is well-defined and feasible. I look forward to your progress."
        },
        {
            id: 5,
            projectTitle: "Cybersecurity Threat Detection System",
            researchType: "project",
            status: "rejected",
            submissionDate: "2026-06-15",
            student: {
                name: "Khalid Al-Mansour",
                id: "S2024042",
                department: "Computer Science",
                email: "khalid.almansour@university.edu",
                year: "3rd Year",
                cgpa: "3.45"
            },
            abstract: "This research aims to develop an AI-based system for detecting cybersecurity threats in real-time. The system uses anomaly detection and behavioral analysis to identify potential security breaches.",
            objectives: [
                "Implement real-time threat detection algorithms",
                "Create a dashboard for security monitoring",
                "Test against common attack vectors",
                "Develop response mechanisms"
            ],
            outcomes: [
                "Real-time threat detection system",
                "Security monitoring dashboard",
                "Comprehensive testing report",
                "Response protocol documentation"
            ],
            facultyComments: "The proposal lacks clear methodology and feasibility analysis. Please revise with more specific implementation details."
        }
    ]
};

// Store current state
let currentData = [];
let filteredData = [];
let selectedRequest = null;
let currentPage = 1;
const itemsPerPage = 8;

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
    document.getElementById('requestModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal();
        }
    });
}

function loadData() {
    showLoading();
    
    setTimeout(() => {
        currentData = JSON.parse(JSON.stringify(sampleData.requests));
        renderRequestCards(currentData);
        updateStats(currentData);
        updateRequestCount(currentData.length);
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

function renderRequestCards(requests) {
    const grid = document.getElementById('requestGrid');
    grid.innerHTML = '';
    
    if (!requests || requests.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="ti ti-file-inbox"></i>
                <p>No research requests found</p>
                <span class="empty-sub">Try adjusting your filters</span>
            </div>
        `;
        return;
    }
    
    requests.forEach(request => {
        const card = document.createElement('div');
        card.className = 'request-card';
        card.onclick = () => openModal(request);
        
        const studentInitials = request.student.name
            .split(' ')
            .map(word => word[0])
            .join('')
            .toUpperCase();
        
        const statusClass = request.status.toLowerCase().replace(' ', '-');
        const statusIcon = {
            'pending': 'ti ti-clock',
            'approved': 'ti ti-check-circle',
            'rejected': 'ti ti-x-circle',
            'in-review': 'ti ti-file-check'
        }[statusClass] || 'ti ti-file';
        
        card.innerHTML = `
            <div class="request-header">
                <h4 class="request-title">${request.projectTitle}</h4>
                <span class="request-status ${statusClass}">
                    <i class="${statusIcon}"></i>
                    ${request.status.charAt(0).toUpperCase() + request.status.slice(1).replace('-', ' ')}
                </span>
            </div>
            
            <div class="student-info">
                <div class="student-avatar">${studentInitials}</div>
                <div class="student-details">
                    <div class="student-name">${request.student.name}</div>
                    <div class="student-dept">${request.student.department} • ${request.student.year}</div>
                </div>
            </div>
            
            <div class="request-meta">
                <span><i class="ti ti-calendar"></i> ${new Date(request.submissionDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                <span><i class="ti ti-id"></i> ${request.student.id}</span>
                <span><i class="ti ti-star"></i> CGPA: ${request.student.cgpa}</span>
            </div>
            
            <div class="request-footer">
                <span class="request-type">
                    <i class="ti ti-book"></i>
                    ${request.researchType.charAt(0).toUpperCase() + request.researchType.slice(1)}
                </span>
                <span class="view-details-btn">
                    View Details <i class="ti ti-chevron-right"></i>
                </span>
            </div>
        `;
        grid.appendChild(card);
    });
}

function updateStats(requests) {
    const total = requests.length;
    const pending = requests.filter(r => r.status === 'pending').length;
    const approved = requests.filter(r => r.status === 'approved').length;
    const rejected = requests.filter(r => r.status === 'rejected').length;
    
    animateNumber('statTotalRequests', total);
    animateNumber('statPendingRequests', pending);
    animateNumber('statApprovedRequests', approved);
    animateNumber('statRejectedRequests', rejected);
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

function updateRequestCount(count) {
    const badge = document.getElementById('requestCount');
    if (badge) {
        badge.textContent = `${count} Request${count !== 1 ? 's' : ''}`;
    }
}

function openModal(request) {
    selectedRequest = request;
    const modal = document.getElementById('requestModal');
    
    // Set modal content
    document.getElementById('modalProjectTitle').textContent = request.projectTitle;
    
    const statusElement = document.getElementById('modalStatus');
    statusElement.textContent = request.status.charAt(0).toUpperCase() + request.status.slice(1).replace('-', ' ');
    statusElement.className = `modal-status ${request.status.toLowerCase().replace(' ', '-')}`;
    
    // Student info
    document.getElementById('modalStudentName').textContent = request.student.name;
    document.getElementById('modalStudentId').textContent = request.student.id;
    document.getElementById('modalStudentDept').textContent = request.student.department;
    document.getElementById('modalStudentEmail').textContent = request.student.email;
    document.getElementById('modalStudentYear').textContent = request.student.year;
    document.getElementById('modalStudentCgpa').textContent = request.student.cgpa;
    
    // Project details
    document.getElementById('modalProjectTitleDetail').textContent = request.projectTitle;
    document.getElementById('modalResearchType').textContent = request.researchType.charAt(0).toUpperCase() + request.researchType.slice(1);
    document.getElementById('modalSubmissionDate').textContent = new Date(request.submissionDate).toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
    document.getElementById('modalAbstract').textContent = request.abstract;
    
    // Objectives
    const objectivesList = document.getElementById('modalObjectives');
    objectivesList.innerHTML = '';
    request.objectives.forEach(obj => {
        const li = document.createElement('li');
        li.textContent = obj;
        objectivesList.appendChild(li);
    });
    
    // Outcomes
    const outcomesList = document.getElementById('modalOutcomes');
    outcomesList.innerHTML = '';
    request.outcomes.forEach(outcome => {
        const li = document.createElement('li');
        li.textContent = outcome;
        outcomesList.appendChild(li);
    });
    
    // Comments
    document.getElementById('modalComments').value = request.facultyComments || '';
    
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    document.getElementById('requestModal').style.display = 'none';
    document.body.style.overflow = '';
    selectedRequest = null;
}

function approveRequest() {
    if (!selectedRequest) return;
    
    const comments = document.getElementById('modalComments').value.trim();
    selectedRequest.status = 'approved';
    selectedRequest.facultyComments = comments || 'Approved.';
    
    saveChanges();
    showNotification(`Research project "${selectedRequest.projectTitle}" approved successfully!`, 'success');
    closeModal();
}

function rejectRequest() {
    if (!selectedRequest) return;
    
    const comments = document.getElementById('modalComments').value.trim();
    if (!comments) {
        showNotification('Please add comments explaining the rejection.', 'warning');
        document.getElementById('modalComments').focus();
        return;
    }
    
    selectedRequest.status = 'rejected';
    selectedRequest.facultyComments = comments;
    
    saveChanges();
    showNotification(`Research project "${selectedRequest.projectTitle}" rejected.`, 'info');
    closeModal();
}

function markInReview() {
    if (!selectedRequest) return;
    
    const comments = document.getElementById('modalComments').value.trim();
    selectedRequest.status = 'in-review';
    selectedRequest.facultyComments = comments || 'Under review.';
    
    saveChanges();
    showNotification(`Research project "${selectedRequest.projectTitle}" marked as in review.`, 'info');
    closeModal();
}

function saveChanges() {
    // Update the data
    const index = currentData.findIndex(r => r.id === selectedRequest.id);
    if (index !== -1) {
        currentData[index] = selectedRequest;
    }
    
    // Re-render
    renderRequestCards(currentData);
    updateStats(currentData);
    updateRequestCount(currentData.length);
}

function applyFilters() {
    const statusFilter = document.getElementById('statusFilter').value;
    const departmentFilter = document.getElementById('departmentFilter').value;
    const researchTypeFilter = document.getElementById('researchTypeFilter').value;
    const searchQuery = document.getElementById('searchInput').value.toLowerCase().trim();
    
    let filtered = JSON.parse(JSON.stringify(currentData));
    
    // Filter by status
    if (statusFilter) {
        filtered = filtered.filter(r => r.status === statusFilter);
    }
    
    // Filter by department
    if (departmentFilter) {
        filtered = filtered.filter(r => 
            r.student.department.toLowerCase().replace(' ', '-') === departmentFilter
        );
    }
    
    // Filter by research type
    if (researchTypeFilter) {
        filtered = filtered.filter(r => r.researchType === researchTypeFilter);
    }
    
    // Filter by search
    if (searchQuery) {
        filtered = filtered.filter(r => 
            r.projectTitle.toLowerCase().includes(searchQuery) ||
            r.student.name.toLowerCase().includes(searchQuery) ||
            r.student.id.toLowerCase().includes(searchQuery) ||
            r.researchType.toLowerCase().includes(searchQuery)
        );
    }
    
    renderRequestCards(filtered);
    updateStats(filtered);
    updateRequestCount(filtered.length);
    
    if (filtered.length === 0) {
        showNotification('No research requests match your filters.', 'warning');
    } else {
        showNotification(`Found ${filtered.length} request(s) matching your filters.`, 'info');
    }
}

function applySearch() {
    applyFilters();
}

function resetFilters() {
    document.getElementById('statusFilter').value = '';
    document.getElementById('departmentFilter').value = '';
    document.getElementById('researchTypeFilter').value = '';
    document.getElementById('searchInput').value = '';
    
    renderRequestCards(currentData);
    updateStats(currentData);
    updateRequestCount(currentData.length);
    
    showNotification('All filters have been reset!', 'info');
}

function refreshData() {
    showLoading();
    setTimeout(() => {
        loadData();
        document.getElementById('requestModal').style.display = 'none';
        selectedRequest = null;
        showNotification('Data refreshed successfully!', 'success');
    }, 500);
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