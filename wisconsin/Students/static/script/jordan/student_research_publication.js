// ============================================
// Student Research Publication - Complete JavaScript
// ============================================

let currentPublications = [];
let filteredPublications = [];
let isLoading = false;
let currentPublicationId = null;

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

async function loadPublications() {
    if (isLoading) return;
    isLoading = true;
    
    try {
        document.getElementById('loadingState').style.display = 'block';
        document.getElementById('publicationsGrid').style.display = 'none';
        document.getElementById('paginationContainer').style.display = 'none';
        
        const data = await apiRequest('/student/api/student-publications/');
        currentPublications = data.publications || [];
        filteredPublications = [...currentPublications];
        
        // Reset to first page
        currentPage = 1;
        
        renderPublications();
        updateStats(currentPublications);
        updateActiveFilters();
        
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('publicationsGrid').style.display = 'grid';
        
    } catch (error) {
        showNotification('Failed to load publications: ' + error.message, 'error');
        document.getElementById('loadingState').innerHTML = `
            <div class="empty-state">
                <i class="ti ti-alert-circle"></i>
                <h3>Failed to load publications</h3>
                <p>${error.message}</p>
                <button class="btn-refresh" onclick="refreshData()" style="margin-top: 16px;">
                    <i class="ti ti-refresh"></i> Try Again
                </button>
            </div>
        `;
    } finally {
        isLoading = false;
    }
}

// ============================================
// RENDER FUNCTIONS
// ============================================

function renderPublications() {
    const grid = document.getElementById('publicationsGrid');
    grid.innerHTML = '';
    
    if (!filteredPublications || filteredPublications.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="ti ti-journal"></i>
                <h3>No publications found</h3>
                <p>Try adjusting your filters or check back later.</p>
            </div>
        `;
        grid.style.display = 'block';
        document.getElementById('paginationContainer').style.display = 'none';
        return;
    }
    
    grid.style.display = 'grid';
    
    // Calculate pagination
    totalPages = Math.ceil(filteredPublications.length / ITEMS_PER_PAGE);
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = Math.min(startIndex + ITEMS_PER_PAGE, filteredPublications.length);
    const pagePublications = filteredPublications.slice(startIndex, endIndex);
    
    // Show pagination
    renderPagination();
    
    pagePublications.forEach((pub) => {
        const card = document.createElement('div');
        card.className = 'publication-card';
        card.onclick = function() { viewPublicationDetails(pub.id); };
        
        // Authors preview
        let authorsPreview = '';
        if (pub.authors && pub.authors.length > 0) {
            const authorNames = pub.authors.map(a => a.name).join(', ');
            authorsPreview = `
                <div class="authors-preview">
                    <i class="ti ti-users"></i>
                    <span>${escapeHtml(authorNames)}</span>
                </div>
            `;
        }
        
        // Author badge - check if current user is an author
        const userEmail = document.getElementById('userEmail')?.value || '';
        const isAuthor = pub.authors && pub.authors.some(a => a.email === userEmail);
        
        let authorBadge = '';
        if (isAuthor) {
            authorBadge = `<span class="author-badge"><i class="ti ti-user-check"></i> You're an author</span>`;
        }
        
        card.innerHTML = `
            <div class="card-header">
                <div class="card-title-section">
                    <h4 class="publication-title">
                        <i class="ti ti-file-text"></i>
                        ${escapeHtml(pub.title)}
                    </h4>
                    <span class="status-badge ${pub.status}">${escapeHtml(pub.status_display)}</span>
                </div>
            </div>
            
            <div class="card-body">
                <div class="publication-meta-top">
                    <span class="publication-type">
                        <i class="ti ti-book"></i> ${escapeHtml(pub.publication_type_display)}
                    </span>
                    <span class="research-project">
                        <i class="ti ti-flask"></i> ${escapeHtml(pub.research_title)}
                    </span>
                </div>
                
                <p class="publication-abstract">
                    ${pub.abstract ? escapeHtml(pub.abstract.substring(0, 150)) : ''}
                    ${pub.abstract && pub.abstract.length > 150 ? '...' : ''}
                </p>
                
                ${authorsPreview}
                
                ${authorBadge}
                
                <div class="publication-meta">
                    <span><i class="ti ti-user"></i> ${pub.author_count || 0} Authors</span>
                    <span><i class="ti ti-calendar"></i> ${escapeHtml(pub.created_at)}</span>
                </div>
            </div>
            
            <div class="card-footer">
                <button class="btn-view-details" onclick="event.stopPropagation(); viewPublicationDetails(${pub.id})">
                    <i class="ti ti-eye"></i> View Details
                </button>
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

function updateStats(publications) {
    const total = publications.length;
    const published = publications.filter(p => p.status === 'published').length;
    const underReview = publications.filter(p => ['under_review', 'committee_review', 'submitted'].includes(p.status)).length;
    
    // Count publications where current user is an author
    const userEmail = document.getElementById('userEmail')?.value || '';
    const asAuthor = publications.filter(pub => 
        pub.authors && pub.authors.some(a => a.email === userEmail)
    ).length;
    
    document.getElementById('totalPublications').textContent = total;
    document.getElementById('publishedCount').textContent = published;
    document.getElementById('pendingCount').textContent = underReview;
    document.getElementById('authorCount').textContent = asAuthor;
}

// ============================================
// PAGINATION FUNCTIONS
// ============================================

function renderPagination() {
    const totalItems = filteredPublications.length;
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
    infoSpan.textContent = `Showing ${start}-${end} of ${totalItems} publications`;
    
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
    renderPublications();
    // Scroll to top of grid
    const grid = document.getElementById('publicationsGrid');
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
// FILTER FUNCTIONS
// ============================================

function filterPublications() {
    const statusFilter = document.getElementById('statusFilter').value;
    const authorFilter = document.getElementById('authorFilter').value;
    const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
    const userEmail = document.getElementById('userEmail')?.value || '';
    
    filteredPublications = [...currentPublications];
    
    // Filter by status
    if (statusFilter !== 'all') {
        filteredPublications = filteredPublications.filter(pub => pub.status === statusFilter);
    }
    
    // Filter by author
    if (authorFilter === 'author') {
        filteredPublications = filteredPublications.filter(pub => 
            pub.authors && pub.authors.some(a => a.email === userEmail)
        );
    }
    
    // Filter by search term
    if (searchTerm) {
        filteredPublications = filteredPublications.filter(pub => 
            (pub.title && pub.title.toLowerCase().includes(searchTerm)) ||
            (pub.abstract && pub.abstract.toLowerCase().includes(searchTerm)) ||
            (pub.research_title && pub.research_title.toLowerCase().includes(searchTerm)) ||
            (pub.authors && pub.authors.some(a => a.name && a.name.toLowerCase().includes(searchTerm)))
        );
    }
    
    // Reset to first page
    currentPage = 1;
    
    renderPublications();
    updateActiveFilters();
}

function updateActiveFilters() {
    const container = document.getElementById('activeFilters');
    const statusFilter = document.getElementById('statusFilter').value;
    const authorFilter = document.getElementById('authorFilter').value;
    const searchTerm = document.getElementById('searchInput').value.trim();
    
    let tags = [];
    
    if (statusFilter !== 'all') {
        const statusDisplay = document.getElementById('statusFilter').selectedOptions[0]?.text || statusFilter;
        tags.push({ key: 'status', label: statusDisplay, value: statusFilter });
    }
    
    if (authorFilter === 'author') {
        tags.push({ key: 'author', label: 'As Author', value: 'author' });
    }
    
    if (searchTerm) {
        tags.push({ key: 'search', label: `"${escapeHtml(searchTerm)}"`, value: searchTerm });
    }
    
    if (tags.length === 0) {
        container.innerHTML = '';
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'flex';
    container.innerHTML = `
        <span class="active-filters-label">Active Filters:</span>
        ${tags.map(tag => `
            <span class="filter-tag" data-key="${tag.key}" data-value="${tag.value}">
                ${escapeHtml(tag.label)}
                <i class="ti ti-x" onclick="removeFilter('${tag.key}', '${tag.value}')"></i>
            </span>
        `).join('')}
        <button class="clear-all-filters" onclick="clearFilters()">
            Clear All
        </button>
    `;
}

function removeFilter(key, value) {
    if (key === 'status') {
        document.getElementById('statusFilter').value = 'all';
    } else if (key === 'author') {
        document.getElementById('authorFilter').value = 'all';
    } else if (key === 'search') {
        document.getElementById('searchInput').value = '';
    }
    filterPublications();
}

function clearFilters() {
    document.getElementById('statusFilter').value = 'all';
    document.getElementById('authorFilter').value = 'all';
    document.getElementById('searchInput').value = '';
    filterPublications();
}

// ============================================
// VIEW PUBLICATION DETAILS
// ============================================

async function viewPublicationDetails(publicationId) {
    try {
        currentPublicationId = publicationId;
        
        const data = await apiRequest(`/student/api/student-publication-detail/?publication_id=${publicationId}`);
        if (data.success && data.data) {
            renderPublicationDetails(data.data);
            openModal('publicationDetailModal');
        }
        
    } catch (error) {
        showNotification('Failed to load publication details: ' + error.message, 'error');
    }
}

function renderPublicationDetails(pub) {
    const userEmail = document.getElementById('userEmail')?.value || '';
    
    // Basic Info
    document.getElementById('detailTitle').textContent = pub.title || 'Untitled';
    document.getElementById('detailStatus').textContent = pub.status_display || 'Draft';
    document.getElementById('detailStatus').className = `status-badge ${pub.status || 'draft'}`;
    document.getElementById('detailResearchTitle').textContent = pub.research_title || 'N/A';
    
    // Type
    document.getElementById('detailType').textContent = pub.publication_type_display || 'Not specified';
    
    // Abstract
    document.getElementById('detailAbstract').textContent = pub.abstract || 'No abstract provided.';
    
    // Keywords
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
        keywordsContainer.innerHTML = '<span class="no-keywords">No keywords specified</span>';
    }
    
    // Authors
    const authorsContainer = document.getElementById('detailAuthors');
    authorsContainer.innerHTML = '';
    if (pub.authors && pub.authors.length > 0) {
        pub.authors.forEach(author => {
            const div = document.createElement('div');
            div.className = 'author-item';
            const isYou = author.email === userEmail;
            div.innerHTML = `
                <span class="author-name">
                    <i class="ti ti-user"></i>
                    ${escapeHtml(author.name)}
                    ${isYou ? '<span class="you-badge">You</span>' : ''}
                </span>
                <span class="author-role-badge">${escapeHtml(author.role)}</span>
            `;
            authorsContainer.appendChild(div);
        });
    } else {
        authorsContainer.innerHTML = '<p class="empty-message">No authors assigned</p>';
    }
    
    // Metadata
    document.getElementById('detailCreated').textContent = pub.created_at || 'N/A';
    document.getElementById('detailUpdated').textContent = pub.updated_at || 'N/A';
    document.getElementById('detailCreatedBy').textContent = pub.created_by || 'Unknown';
    
    // Author Status
    const authorStatus = document.getElementById('detailAuthorStatus');
    if (pub.is_author) {
        authorStatus.className = 'author-status-badge yes';
        authorStatus.innerHTML = `
            <i class="ti ti-user-check"></i>
            <span>You are an author of this publication</span>
        `;
    } else {
        authorStatus.className = 'author-status-badge no';
        authorStatus.innerHTML = `
            <i class="ti ti-user-x"></i>
            <span>You are not an author of this publication</span>
        `;
    }
}

// ============================================
// REFRESH
// ============================================

function refreshData() {
    showNotification('Refreshing data...', 'info');
    loadPublications();
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
    loadPublications();
    
    // Close modal on overlay click
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.style.display = 'none';
                document.body.style.overflow = '';
            }
        });
    });

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
// EXPOSE FUNCTIONS GLOBALLY
// ============================================

window.viewPublicationDetails = viewPublicationDetails;
window.refreshData = refreshData;
window.filterPublications = filterPublications;
window.clearFilters = clearFilters;
window.removeFilter = removeFilter;
window.goToPage = goToPage;
window.changePage = changePage;
window.closeModal = closeModal;
window.closeNotification = closeNotification;
window.closeErrorNotification = closeErrorNotification;
window.closeWarningNotification = closeWarningNotification;