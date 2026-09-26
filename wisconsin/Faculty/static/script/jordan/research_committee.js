// Research Committee Approval JavaScript

// Sample data
const sampleApplications = [
    {
        id: "RC2024-001",
        projectTitle: "AI-Based Student Performance Prediction System",
        type: "faculty",
        status: "pending",
        researchType: "thesis",
        department: "Computer Science",
        duration: "1 Year",
        submittedDate: "2026-07-01",
        applicant: {
            name: "Dr. John Doe",
            role: "Assistant Professor",
            department: "Computer Science",
            email: "john.doe@university.edu",
            phone: "+1 234 567 8900",
            initials: "JD"
        },
        abstract: "This research proposes a machine learning-based system to predict student academic performance using historical data, attendance records, and engagement metrics.",
        objectives: [
            "Develop a predictive model using ensemble learning techniques",
            "Analyze the correlation between attendance and academic performance",
            "Create a real-time dashboard for faculty monitoring"
        ],
        outcomes: [
            "A working prediction system with 85%+ accuracy",
            "Early warning system for at-risk students",
            "Faculty dashboard for performance monitoring"
        ],
        reviewHistory: [
            {
                action: "Submitted",
                reviewer: "System",
                date: "2026-07-01",
                comment: "Application submitted successfully"
            }
        ],
        reviewerComments: "",
        selectedRecommendation: null
    },
    {
        id: "RC2024-002",
        projectTitle: "Sustainable Energy Solutions for Smart Cities",
        type: "student",
        status: "reviewing",
        researchType: "project",
        department: "Engineering",
        duration: "6 Months",
        submittedDate: "2026-06-28",
        applicant: {
            name: "Mariam Al-Fahd",
            role: "Graduate Student",
            department: "Engineering",
            email: "mariam.alfahd@university.edu",
            phone: "+1 234 567 8901",
            initials: "MA"
        },
        abstract: "Exploring the integration of renewable energy sources with smart city infrastructure. Focus on optimizing energy distribution and reducing carbon footprint.",
        objectives: [
            "Design a hybrid renewable energy system",
            "Develop IoT sensors for energy monitoring",
            "Create optimization algorithm"
        ],
        outcomes: [
            "Scalable hybrid energy system design",
            "IoT-based monitoring prototype",
            "Energy optimization algorithm"
        ],
        reviewHistory: [
            {
                action: "Submitted",
                reviewer: "System",
                date: "2026-06-28",
                comment: "Application submitted successfully"
            },
            {
                action: "Under Review",
                reviewer: "Dr. Sarah Al-Qahtani",
                date: "2026-06-30",
                comment: "Initial review started. Promising topic."
            }
        ],
        reviewerComments: "Strong proposal with clear objectives. Need to verify feasibility.",
        selectedRecommendation: null
    },
    {
        id: "RC2024-003",
        projectTitle: "Blockchain for Secure Academic Credentials",
        type: "faculty",
        status: "revision-required",
        researchType: "dissertation",
        department: "Computer Science",
        duration: "2 Years",
        submittedDate: "2026-06-25",
        applicant: {
            name: "Dr. Ahmad Al-Saud",
            role: "Professor",
            department: "Computer Science",
            email: "ahmad.alsaud@university.edu",
            phone: "+1 234 567 8902",
            initials: "AS"
        },
        abstract: "Investigating blockchain technology for creating a secure, verifiable system for academic credentials to eliminate fraud and simplify verification.",
        objectives: [
            "Design blockchain-based verification system",
            "Implement smart contracts",
            "Ensure GDPR compliance",
            "Create user interface"
        ],
        outcomes: [
            "Verification system",
            "Smart contract implementation",
            "Security audit report"
        ],
        reviewHistory: [
            {
                action: "Submitted",
                reviewer: "System",
                date: "2026-06-25",
                comment: "Application submitted successfully"
            },
            {
                action: "Revision Required",
                reviewer: "Dr. Sarah Al-Qahtani",
                date: "2026-06-29",
                comment: "Please provide more details on GDPR compliance and security measures."
            }
        ],
        reviewerComments: "Good concept. Need to strengthen the security section.",
        selectedRecommendation: "revision"
    },
    {
        id: "RC2024-004",
        projectTitle: "Machine Learning in Medical Diagnosis",
        type: "student",
        status: "approved",
        researchType: "experimental",
        department: "Biology",
        duration: "8 Months",
        submittedDate: "2026-06-20",
        applicant: {
            name: "Layla Al-Khalifa",
            role: "Graduate Student",
            department: "Biology",
            email: "layla.alkhalifa@university.edu",
            phone: "+1 234 567 8903",
            initials: "LK"
        },
        abstract: "Applying deep learning to medical imaging for early detection of diseases. Developing CNN-based model for breast cancer detection.",
        objectives: [
            "Develop CNN model",
            "Train on medical datasets",
            "Achieve 90%+ accuracy",
            "Create web interface"
        ],
        outcomes: [
            "High-accuracy detection model",
            "Web-based diagnostic tool",
            "Research paper publication"
        ],
        reviewHistory: [
            {
                action: "Submitted",
                reviewer: "System",
                date: "2026-06-20",
                comment: "Application submitted successfully"
            },
            {
                action: "Approved",
                reviewer: "Dr. Sarah Al-Qahtani",
                date: "2026-06-23",
                comment: "Excellent research proposal. Approved."
            }
        ],
        reviewerComments: "Excellent work. Approved.",
        selectedRecommendation: "approve"
    },
    {
        id: "RC2024-005",
        projectTitle: "Cybersecurity Threat Detection System",
        type: "student",
        status: "rejected",
        researchType: "project",
        department: "Computer Science",
        duration: "6 Months",
        submittedDate: "2026-06-15",
        applicant: {
            name: "Khalid Al-Mansour",
            role: "Undergraduate Student",
            department: "Computer Science",
            email: "khalid.almansour@university.edu",
            phone: "+1 234 567 8904",
            initials: "KM"
        },
        abstract: "Developing an AI-based system for detecting cybersecurity threats in real-time using anomaly detection and behavioral analysis.",
        objectives: [
            "Implement real-time detection algorithms",
            "Create monitoring dashboard",
            "Test against attack vectors"
        ],
        outcomes: [
            "Real-time threat detection system",
            "Security monitoring dashboard",
            "Response protocol documentation"
        ],
        reviewHistory: [
            {
                action: "Submitted",
                reviewer: "System",
                date: "2026-06-15",
                comment: "Application submitted successfully"
            },
            {
                action: "Rejected",
                reviewer: "Dr. Sarah Al-Qahtani",
                date: "2026-06-18",
                comment: "The proposal lacks clear methodology and feasibility analysis."
            }
        ],
        reviewerComments: "The proposal lacks clear methodology and feasibility analysis.",
        selectedRecommendation: "reject"
    }
];

// Store current state
let currentApplications = [];
let selectedApplication = null;
let currentFilter = 'all';
let selectedRecommendation = null;

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
    document.getElementById('appModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal();
        }
    });
}

function loadData() {
    showLoading();
    
    setTimeout(() => {
        currentApplications = JSON.parse(JSON.stringify(sampleApplications));
        renderApplications(currentApplications);
        updateStats(currentApplications);
        updateAppCount(currentApplications.length);
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

function renderApplications(applications) {
    const grid = document.getElementById('applicationsGrid');
    grid.innerHTML = '';
    
    if (!applications || applications.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="ti ti-file-inbox"></i>
                <p>No applications found</p>
                <span class="empty-sub">Try adjusting your filters</span>
            </div>
        `;
        return;
    }
    
    applications.forEach(app => {
        const card = document.createElement('div');
        card.className = 'application-card';
        card.onclick = () => openModal(app);
        
        const statusClass = app.status.toLowerCase().replace(' ', '-');
        const typeClass = app.type || 'faculty';
        
        card.innerHTML = `
            <div class="card-header">
                <h4 class="project-title">${app.projectTitle}</h4>
                <span class="status-badge ${statusClass}">${app.status.replace('-', ' ').toUpperCase()}</span>
            </div>
            
            <span class="app-type-badge ${typeClass}">
                <i class="ti ${typeClass === 'faculty' ? 'ti-user' : 'ti-users'}"></i>
                ${typeClass === 'faculty' ? 'Faculty' : 'Student'}
            </span>
            
            <div class="app-meta">
                <span><i class="ti ti-file"></i> ${app.researchType}</span>
                <span><i class="ti ti-building"></i> ${app.department}</span>
                <span><i class="ti ti-calendar"></i> ${new Date(app.submittedDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                <span><i class="ti ti-id"></i> ${app.id}</span>
            </div>
            
            <div class="app-footer">
                <div class="applicant">
                    <div class="applicant-avatar">${app.applicant.initials}</div>
                    <span class="applicant-name">${app.applicant.name}</span>
                </div>
                <span class="view-details-btn">
                    Review <i class="ti ti-chevron-right"></i>
                </span>
            </div>
        `;
        grid.appendChild(card);
    });
}

function updateStats(applications) {
    const total = applications.length;
    const pending = applications.filter(a => a.status === 'pending').length;
    const reviewing = applications.filter(a => a.status === 'reviewing').length;
    const approved = applications.filter(a => a.status === 'approved').length;
    const rejected = applications.filter(a => a.status === 'rejected').length;
    
    // Unique departments
    const departments = new Set(applications.map(a => a.department));
    
    // Unique applicants
    const applicants = new Set(applications.map(a => a.applicant.name));
    
    animateNumber('statTotalApplications', total);
    animateNumber('statPendingApplications', pending);
    animateNumber('statReviewingApplications', reviewing);
    animateNumber('statApprovedApplications', approved);
    animateNumber('statRejectedApplications', rejected);
    animateNumber('statDepartments', departments.size);
    animateNumber('statApplicants', applicants.size);
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

function updateAppCount(count) {
    const badge = document.getElementById('appCount');
    if (badge) {
        badge.textContent = `${count} Application${count !== 1 ? 's' : ''}`;
    }
}



function setRecommendation(type) {
    selectedRecommendation = type;
    document.querySelectorAll('.recommend-btn').forEach(btn => {
        btn.classList.remove('selected');
    });
    const btn = document.querySelector(`.recommend-btn.${type}`);
    if (btn) btn.classList.add('selected');
    updateRecommendationDisplay();
}

function updateRecommendationDisplay() {
    const display = document.getElementById('selectedRecommendation');
    if (selectedRecommendation === 'approve') {
        display.innerHTML = '<span style="color: var(--primary-green);">✓ Recommendation: Approve</span>';
    } else if (selectedRecommendation === 'revision') {
        display.innerHTML = '<span style="color: var(--primary-orange);">⟳ Recommendation: Revision Required</span>';
    } else if (selectedRecommendation === 'reject') {
        display.innerHTML = '<span style="color: var(--primary-red);">✗ Recommendation: Reject</span>';
    } else {
        display.innerHTML = '';
    }
}

function submitReview(status) {
    if (!selectedApplication) return;
    
    const comments = document.getElementById('modalComments').value.trim();
    
    // Validate recommendation if rejecting or requiring revision
    if ((status === 'rejected' || status === 'revision-required') && !comments) {
        showNotification('Please add comments explaining your decision.', 'warning');
        document.getElementById('modalComments').focus();
        return;
    }
    
    // Update status
    selectedApplication.status = status;
    selectedApplication.reviewerComments = comments || selectedApplication.reviewerComments;
    selectedApplication.selectedRecommendation = selectedRecommendation;
    
    // Add to review history
    const statusLabels = {
        'approved': 'Approved',
        'rejected': 'Rejected',
        'revision-required': 'Revision Required',
        'reviewing': 'Under Review'
    };
    
    selectedApplication.reviewHistory.push({
        action: statusLabels[status] || status,
        reviewer: 'Committee Member',
        date: new Date().toISOString().split('T')[0],
        comment: comments || `Application ${statusLabels[status] || status}`
    });
    
    saveChanges();
    
    showNotification(`Application ${statusLabels[status] || status}!`, status === 'approved' ? 'success' : 'info');
    closeModal();
}

function saveChanges() {
    const index = currentApplications.findIndex(a => a.id === selectedApplication.id);
    if (index !== -1) {
        currentApplications[index] = selectedApplication;
    }
    
    renderApplications(currentApplications);
    updateStats(currentApplications);
    updateAppCount(currentApplications.length);
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
    const appTypeFilter = document.getElementById('appTypeFilter').value;
    const departmentFilter = document.getElementById('departmentFilter').value;
    const dateFilter = document.getElementById('dateFilter').value;
    const searchQuery = document.getElementById('searchInput').value.toLowerCase().trim();
    
    let filtered = JSON.parse(JSON.stringify(currentApplications));
    
    // Quick filter
    if (currentFilter === 'faculty') {
        filtered = filtered.filter(a => a.type === 'faculty');
    } else if (currentFilter === 'student') {
        filtered = filtered.filter(a => a.type === 'student');
    } else if (currentFilter === 'pending') {
        filtered = filtered.filter(a => a.status === 'pending');
    } else if (currentFilter === 'reviewing') {
        filtered = filtered.filter(a => a.status === 'reviewing');
    } else if (currentFilter === 'approved') {
        filtered = filtered.filter(a => a.status === 'approved');
    } else if (currentFilter === 'revision-required') {
        filtered = filtered.filter(a => a.status === 'revision-required');
    }
    
    // Status filter
    if (statusFilter) {
        filtered = filtered.filter(a => a.status === statusFilter);
    }
    
    // Application type filter
    if (appTypeFilter) {
        filtered = filtered.filter(a => a.type === appTypeFilter);
    }
    
    // Department filter
    if (departmentFilter) {
        filtered = filtered.filter(a => 
            a.department.toLowerCase().replace(' ', '-') === departmentFilter
        );
    }
    
    // Date filter
    if (dateFilter) {
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        
        filtered = filtered.filter(a => {
            const submitted = new Date(a.submittedDate);
            if (dateFilter === 'today') {
                return submitted.getTime() >= today.getTime();
            } else if (dateFilter === 'week') {
                const weekAgo = new Date(today);
                weekAgo.setDate(weekAgo.getDate() - 7);
                return submitted >= weekAgo;
            } else if (dateFilter === 'month') {
                return submitted.getMonth() === today.getMonth() && 
                       submitted.getFullYear() === today.getFullYear();
            } else if (dateFilter === 'quarter') {
                const quarterAgo = new Date(today);
                quarterAgo.setMonth(quarterAgo.getMonth() - 3);
                return submitted >= quarterAgo;
            }
            return true;
        });
    }
    
    // Search
    if (searchQuery) {
        filtered = filtered.filter(a => 
            a.projectTitle.toLowerCase().includes(searchQuery) ||
            a.applicant.name.toLowerCase().includes(searchQuery) ||
            a.department.toLowerCase().includes(searchQuery) ||
            a.id.toLowerCase().includes(searchQuery) ||
            a.researchType.toLowerCase().includes(searchQuery)
        );
    }
    
    renderApplications(filtered);
    updateStats(filtered);
    updateAppCount(filtered.length);
    
    if (filtered.length === 0) {
        showNotification('No applications match your filters.', 'warning');
    }
}

function applySearch() {
    applyFilters();
}

function refreshData() {
    showLoading();
    setTimeout(() => {
        loadData();
        document.getElementById('appModal').style.display = 'none';
        selectedApplication = null;
        showNotification('Data refreshed successfully!', 'success');
    }, 500);
}

function exportReport() {
    // Export to Excel
    try {
        const data = currentApplications.map(app => ({
            'ID': app.id,
            'Project Title': app.projectTitle,
            'Type': app.type,
            'Status': app.status,
            'Research Type': app.researchType,
            'Department': app.department,
            'Applicant': app.applicant.name,
            'Submitted': new Date(app.submittedDate).toLocaleDateString(),
            'Duration': app.duration
        }));
        
        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.json_to_sheet(data);
        XLSX.utils.book_append_sheet(wb, ws, 'Applications');
        
        const fileName = `Research_Applications_${new Date().toISOString().split('T')[0]}.xlsx`;
        XLSX.writeFile(wb, fileName);
        
        showNotification('Report exported successfully!', 'success');
    } catch (error) {
        console.error('Export error:', error);
        showNotification('Error exporting report.', 'error');
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