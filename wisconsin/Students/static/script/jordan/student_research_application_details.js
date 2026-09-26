// ============================================
// STUDENT RESEARCH APPLICATION DETAILS JS
// Complete working functionality with Pagination
// ============================================

// Pagination variables
const ITEMS_PER_PAGE = 12;
let currentPage = 1;
let totalPages = 1;
let filteredApplications = [];
let allApplications = [];

document.addEventListener('DOMContentLoaded', function() {
    console.log('Application Details page loaded');
    console.log('Applications Data:', applicationsData);
    
    // Store all applications
    allApplications = [...applicationsData];
    filteredApplications = [...allApplications];
    
    // Render initial applications with pagination
    renderApplications();
    renderPagination();
    
    // Add click event to all application cards (event delegation)
    const grid = document.getElementById('applicationsGrid');
    if (grid) {
        grid.addEventListener('click', function(e) {
            const card = e.target.closest('.application-card');
            if (card) {
                const index = parseInt(card.dataset.index);
                if (!isNaN(index)) {
                    openDetailModal(index);
                }
            }
        });
        
        // Keyboard accessibility for cards (event delegation)
        grid.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                const card = e.target.closest('.application-card');
                if (card) {
                    e.preventDefault();
                    const index = parseInt(card.dataset.index);
                    if (!isNaN(index)) {
                        openDetailModal(index);
                    }
                }
            }
        });
    }
    
    // Initialize Slim Select
    document.querySelectorAll('.filter-select').forEach(element => {
        if (element.tagName.toLowerCase() === 'select') {
            try {
                new SlimSelect({
                    select: element,
                    settings: {
                        placeholderText: element.options[0]?.text || 'Select an option',
                        showSearch: false
                    }
                });
            } catch (e) {
                console.warn('SlimSelect initialization failed:', e);
            }
        }
    });
});

// ============================================
// RENDER APPLICATIONS WITH PAGINATION
// ============================================

function renderApplications() {
    const grid = document.getElementById('applicationsGrid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    // Check if there are any applications
    if (!filteredApplications || filteredApplications.length === 0) {
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <i class="ti ti-file-off"></i>
                <h3>No Applications Found</h3>
                <p>No applications match your current filter or search criteria.</p>
            </div>
        `;
        const paginationContainer = document.getElementById('paginationContainer');
        if (paginationContainer) {
            paginationContainer.style.display = 'none';
        }
        return;
    }
    
    // Calculate pagination
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = Math.min(startIndex + ITEMS_PER_PAGE, filteredApplications.length);
    const pageApplications = filteredApplications.slice(startIndex, endIndex);
    
    // Show pagination container
    const paginationContainer = document.getElementById('paginationContainer');
    if (paginationContainer) {
        paginationContainer.style.display = 'flex';
    }
    
    // Render each application card
    pageApplications.forEach((app, index) => {
        // Find the actual index in the original array
        const actualIndex = allApplications.indexOf(app);
        const card = document.createElement('div');
        card.className = 'application-card';
        card.dataset.index = actualIndex;
        card.dataset.status = app.status;
        card.setAttribute('tabindex', '0');
        card.style.animationDelay = `${(index % 12) * 0.05}s`;
        
        const statusClass = app.status || 'submitted';
        const statusDisplay = app.statusDisplay || 'Submitted';
        
        card.innerHTML = `
            <div class="card-status-indicator ${statusClass}"></div>
            
            <div class="application-header">
                <div class="application-title">
                    <h4>${escapeHtml(app.title || 'Untitled Application')}</h4>
                    <span class="status-badge ${statusClass}">${escapeHtml(statusDisplay)}</span>
                </div>
            </div>
            
            <div class="application-preview">
                <div class="preview-item">
                    <span class="preview-label">Reference</span>
                    <span class="preview-value">${escapeHtml(app.reference || 'N/A')}</span>
                </div>
                <div class="preview-item">
                    <span class="preview-label">Department</span>
                    <span class="preview-value">${escapeHtml(app.department || 'Not specified')}</span>
                </div>
                <div class="preview-item">
                    <span class="preview-label">Status</span>
                    <span class="preview-value"><span class="status-badge ${statusClass}">${escapeHtml(statusDisplay)}</span></span>
                </div>
            </div>
            
            <div class="application-footer">
                <span class="click-hint"><i class="ti ti-click"></i> Click to view details</span>
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
    const totalItems = filteredApplications.length;
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
    infoSpan.textContent = `Showing ${start}-${end} of ${totalItems} applications`;
    
    // Update prev/next buttons
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === totalPages;
    
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
            // Show 1, 2, 3, 4, 5, ..., last
            for (let i = 1; i <= 5; i++) {
                numbersContainer.appendChild(createPageButton(i));
            }
            numbersContainer.appendChild(createEllipsis());
            numbersContainer.appendChild(createPageButton(totalPages));
        } else if (currentPage >= totalPages - 3) {
            // Show 1, ..., last-4, last-3, last-2, last-1, last
            numbersContainer.appendChild(createPageButton(1));
            numbersContainer.appendChild(createEllipsis());
            for (let i = totalPages - 4; i <= totalPages; i++) {
                numbersContainer.appendChild(createPageButton(i));
            }
        } else {
            // Show 1, ..., current-1, current, current+1, ..., last
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
    renderApplications();
    renderPagination();
    // Scroll to top of grid
    const grid = document.getElementById('applicationsGrid');
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

// ============================================
// FILTER AND SEARCH (Updated with pagination)
// ============================================

function filterApplications() {
    const filter = document.getElementById('statusFilter')?.value || 'all';
    const searchTerm = document.getElementById('searchInput')?.value?.toLowerCase().trim() || '';
    
    filteredApplications = allApplications.filter(app => {
        // Filter by status
        if (filter !== 'all' && app.status !== filter) {
            return false;
        }
        
        // Filter by search
        if (searchTerm) {
            const title = (app.title || '').toLowerCase();
            const reference = (app.reference || '').toLowerCase();
            const searchData = title + ' ' + reference;
            if (!searchData.includes(searchTerm)) {
                return false;
            }
        }
        
        return true;
    });
    
    // Reset to first page
    currentPage = 1;
    
    // Re-render
    renderApplications();
    renderPagination();
}

function searchApplications() {
    filterApplications();
}

// ============================================
// OPEN DETAIL MODAL
// ============================================

function openDetailModal(index) {
    // Get data from the global applicationsData array
    const data = allApplications[index];
    
    if (!data) {
        showToast('Application data not found.', 'error');
        return;
    }
    
    console.log('Opening modal for:', data.title);
    
    const modal = document.getElementById('detailModal');
    const content = document.getElementById('detailContent');
    
    if (!modal || !content) return;
    
    // Build the modal content
    content.innerHTML = buildModalContent(data);
    
    // Show modal
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    
    // Add animation
    setTimeout(function() {
        const container = modal.querySelector('.modal-container');
        if (container) {
            container.classList.add('show');
        }
    }, 10);
}

// ============================================
// BUILD MODAL CONTENT
// ============================================

function buildModalContent(data) {
    const statusClass = data.status || 'submitted';
    const statusDisplay = data.statusDisplay || 'Submitted';
    const isAccepted = statusClass === 'accepted';
    const isRejected = statusClass === 'rejected';
    const isPending = ['submitted', 'under_review', 'shortlisted'].includes(statusClass);
    const isWithdrawn = statusClass === 'withdrawn';
    
    // Build review section based on status
    let reviewHtml = '';
    if (isAccepted) {
        reviewHtml = `
            <div class="detail-section review-accepted">
                <h4><i class="ti ti-check-circle"></i> Application Accepted</h4>
                <div class="detail-row full">
                    <span class="detail-value" style="color: #16a34a; font-weight: 600;">🎉 Congratulations! Your application has been accepted.</span>
                </div>
                ${data.reviewedAt && data.reviewedAt !== 'N/A' ? `
                <div class="detail-row">
                    <span class="detail-label">Reviewed On</span>
                    <span class="detail-value">${escapeHtml(data.reviewedAt)}</span>
                </div>
                ` : ''}
                ${data.reviewComments && data.reviewComments !== 'No comments' ? `
                <div class="detail-row full">
                    <span class="detail-label">Review Comments</span>
                    <span class="detail-value">${escapeHtml(data.reviewComments)}</span>
                </div>
                ` : ''}
            </div>
        `;
    } else if (isRejected) {
        reviewHtml = `
            <div class="detail-section review-rejected">
                <h4><i class="ti ti-x-circle"></i> Application Rejected</h4>
                <div class="detail-row full">
                    <span class="detail-value" style="color: #dc2626; font-weight: 600;">Your application has been rejected.</span>
                </div>
                ${data.reviewedAt && data.reviewedAt !== 'N/A' ? `
                <div class="detail-row">
                    <span class="detail-label">Reviewed On</span>
                    <span class="detail-value">${escapeHtml(data.reviewedAt)}</span>
                </div>
                ` : ''}
                ${data.reviewComments && data.reviewComments !== 'No comments' ? `
                <div class="detail-row full">
                    <span class="detail-label">Review Comments</span>
                    <span class="detail-value">${escapeHtml(data.reviewComments)}</span>
                </div>
                ` : ''}
            </div>
        `;
    } else if (isPending) {
        reviewHtml = `
            <div class="detail-section review-pending">
                <h4><i class="ti ti-clock"></i> Application Under Review</h4>
                <div class="detail-row full">
                    <span class="detail-value" style="color: #ea580c; font-weight: 600;">Your application is currently being reviewed by the committee.</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Submitted On</span>
                    <span class="detail-value">${escapeHtml(data.submittedDate || 'N/A')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Status</span>
                    <span class="detail-value"><span class="status-badge ${statusClass}">${escapeHtml(statusDisplay)}</span></span>
                </div>
            </div>
        `;
    } else if (isWithdrawn) {
        reviewHtml = `
            <div class="detail-section review-withdrawn">
                <h4><i class="ti ti-arrow-back"></i> Application Withdrawn</h4>
                <div class="detail-row full">
                    <span class="detail-value" style="color: #64748b; font-weight: 600;">You have withdrawn this application.</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Submitted On</span>
                    <span class="detail-value">${escapeHtml(data.submittedDate || 'N/A')}</span>
                </div>
            </div>
        `;
    }
    
    // Build documents section
    let docsHtml = '';
    if (data.hasResume || data.hasStatement || data.hasTranscript) {
        docsHtml = `
            <div class="detail-section">
                <h4><i class="ti ti-file"></i> Documents</h4>
                <div class="document-list">
                    ${data.hasResume ? `
                    <a href="${data.resumeUrl}" target="_blank" class="document-link">
                        <i class="ti ti-file"></i> Resume/CV
                    </a>
                    ` : `
                    <span class="document-link disabled"><i class="ti ti-file"></i> Resume/CV (Not uploaded)</span>
                    `}
                    ${data.hasStatement ? `
                    <a href="${data.statementUrl}" target="_blank" class="document-link">
                        <i class="ti ti-file-text"></i> Statement of Interest
                    </a>
                    ` : `
                    <span class="document-link disabled"><i class="ti ti-file-text"></i> Statement of Interest (Not uploaded)</span>
                    `}
                    ${data.hasTranscript ? `
                    <a href="${data.transcriptUrl}" target="_blank" class="document-link">
                        <i class="ti ti-file-analytics"></i> Academic Transcript
                    </a>
                    ` : `
                    <span class="document-link disabled"><i class="ti ti-file-pdf"></i> Academic Transcript (Not uploaded)</span>
                    `}
                </div>
            </div>
        `;
    }
    
    return `
        <div class="detail-header">
            <div class="detail-status-badge ${statusClass}">${escapeHtml(statusDisplay)}</div>
            <span class="detail-reference">${escapeHtml(data.reference || 'N/A')}</span>
        </div>
        
        <h2 class="detail-title">${escapeHtml(data.title || 'Untitled Application')}</h2>
        
        <div class="detail-meta">
            <div class="meta-item">
                <i class="ti ti-calendar"></i>
                <span>Submitted: ${escapeHtml(data.submittedDate || 'N/A')}</span>
            </div>
            <div class="meta-item">
                <i class="ti ti-clock"></i>
                <span>Last Updated: ${escapeHtml(data.updatedDate || 'N/A')}</span>
            </div>
            <div class="meta-item">
                <i class="ti ti-file-text"></i>
                <span>Reference: ${escapeHtml(data.reference || 'N/A')}</span>
            </div>
            <div class="meta-item">
                <i class="ti ti-building"></i>
                <span>Department: ${escapeHtml(data.department || 'Not specified')}</span>
            </div>
        </div>
        
        <div class="detail-grid">
            <div class="detail-section">
                <h4><i class="ti ti-info-circle"></i> Project Information</h4>
                <div class="detail-row">
                    <span class="detail-label">Research Area</span>
                    <span class="detail-value">${escapeHtml(data.researchArea || 'Not specified')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Time Commitment</span>
                    <span class="detail-value">${escapeHtml(data.timeCommitment || 'Not specified')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Availability</span>
                    <span class="detail-value">${escapeHtml(data.availability || 'Not specified')}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Status</span>
                    <span class="detail-value"><span class="status-badge ${statusClass}">${escapeHtml(statusDisplay)}</span></span>
                </div>
            </div>
            
            <div class="detail-section">
                <h4><i class="ti ti-file-text"></i> Application Details</h4>
                <div class="detail-row full">
                    <span class="detail-label">Motivation</span>
                    <span class="detail-value">${escapeHtml(data.motivation || 'Not provided')}</span>
                </div>
                <div class="detail-row full">
                    <span class="detail-label">Skills Contribution</span>
                    <span class="detail-value">${escapeHtml(data.skillsContribution || 'Not provided')}</span>
                </div>
                ${data.priorExperience && data.priorExperience !== 'Not provided' ? `
                <div class="detail-row full">
                    <span class="detail-label">Prior Experience</span>
                    <span class="detail-value">${escapeHtml(data.priorExperience)}</span>
                </div>
                ` : ''}
                ${data.additionalInfo && data.additionalInfo !== 'Not provided' ? `
                <div class="detail-row full">
                    <span class="detail-label">Additional Info</span>
                    <span class="detail-value">${escapeHtml(data.additionalInfo)}</span>
                </div>
                ` : ''}
            </div>
        </div>
        
        ${reviewHtml}
        ${docsHtml}
        
        <div class="detail-actions">
            <button class="btn-close-modal" onclick="closeDetailModal()">
                <i class="ti ti-x"></i> Close
            </button>
        </div>
    `;
}

// ============================================
// CLOSE DETAIL MODAL
// ============================================

function closeDetailModal() {
    const modal = document.getElementById('detailModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
        const container = modal.querySelector('.modal-container');
        if (container) {
            container.classList.remove('show');
        }
    }
}

// ============================================
// TOAST NOTIFICATIONS
// ============================================

function showToast(message, type) {
    type = type || 'success';
    
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    const icon = toast ? toast.querySelector('.toast-icon i') : null;
    
    if (!toast || !toastMessage) return;
    
    toast.className = 'toast-notification ' + type;
    toastMessage.textContent = message;
    
    if (icon) {
        var iconClass = 'ti-check-circle';
        if (type === 'error') iconClass = 'ti-alert-circle';
        else if (type === 'warning') iconClass = 'ti-alert-triangle';
        else if (type === 'info') iconClass = 'ti-info-circle';
        icon.className = 'ti ' + iconClass;
    }
    
    toast.style.display = 'flex';
    toast.style.opacity = '1';
    toast.style.transform = 'translateX(0)';
    
    clearTimeout(toast._timeout);
    toast._timeout = setTimeout(closeToast, 5000);
}

function closeToast() {
    const toast = document.getElementById('toast');
    if (toast) {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(function() {
            toast.style.display = 'none';
            toast.style.opacity = '1';
            toast.style.transform = 'translateX(0)';
        }, 300);
    }
}

// ============================================
// KEYBOARD SHORTCUTS
// ============================================

document.addEventListener('keydown', function(e) {
    // Close modal with Escape
    if (e.key === 'Escape') {
        const detailModal = document.getElementById('detailModal');
        if (detailModal && detailModal.style.display === 'flex') {
            closeDetailModal();
        }
        closeToast();
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
// CLOSE MODALS ON OVERLAY CLICK
// ============================================

document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        if (e.target.id === 'detailModal') {
            closeDetailModal();
        }
    }
});

// ============================================
// EXPOSE FUNCTIONS GLOBALLY
// ============================================

window.openDetailModal = openDetailModal;
window.closeDetailModal = closeDetailModal;
window.filterApplications = filterApplications;
window.searchApplications = searchApplications;
window.goToPage = goToPage;
window.changePage = changePage;
window.showToast = showToast;
window.closeToast = closeToast;