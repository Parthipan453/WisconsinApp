// Student Applications JavaScript

let currentApplicationId = null;
let isProcessing = false;

function getCSRFToken() {
    return document.getElementById('csrfToken')?.value || '';
}

function openModal(applicationId) {
    const modal = document.getElementById('applicationModal');
    const loading = document.getElementById('modalLoading');
    const content = document.getElementById('modalContent');
    
    currentApplicationId = applicationId;
    
    loading.style.display = 'block';
    content.style.display = 'none';
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    clearErrors();
    
    fetch(`/faculty/api/application/${applicationId}/`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        if (data.success) {
            populateModal(data.data);
            loading.style.display = 'none';
            content.style.display = 'block';
        } else {
            showNotification(data.error || 'Error loading application', 'error');
            closeModal();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error loading application details. Please try again.', 'error');
        closeModal();
    });
}

function populateModal(data) {
    // Reference & Status
    document.getElementById('modalReference').textContent = data.reference;
    
    const statusElement = document.getElementById('modalStatus');
    statusElement.textContent = data.status_display;
    statusElement.className = `modal-status ${data.status}`;
    
    // Student Info
    const studentFields = {
        'modalStudentName': data.student.name,
        'modalStudentEmail': data.student.email,
        'modalStudentId': data.student.student_id,
        'modalStudentProgram': data.student.program,
        'modalStudentDept': data.student.department,
        'modalStudentPhone': data.student.phone
    };
    Object.keys(studentFields).forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = studentFields[id] || '-';
    });
    
    // Project Details
    const projectFields = {
        'modalProjectTitle': data.project.title,
        'modalMotivation': data.project.motivation,
        'modalSkills': data.project.skills,
        'modalExperience': data.project.experience,
        'modalTime': data.project.time_commitment,
        'modalAvailability': data.project.availability,
        'modalAdditional': data.project.additional_info
    };
    Object.keys(projectFields).forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = projectFields[id] || '-';
    });
    
    // Documents - With proper new tab functionality
    const docsContainer = document.getElementById('modalDocuments');
    docsContainer.innerHTML = '';
    if (data.documents && data.documents.length > 0) {
        data.documents.forEach(doc => {
            const div = document.createElement('div');
            div.className = 'document-item';
            
            // Get file extension for icon
            const fileExt = doc.name.split('.').pop().toLowerCase();
            let iconClass = 'ti ti-file';
            if (fileExt === 'pdf') iconClass = 'ti ti-file-type-pdf';
            else if (fileExt === 'doc' || fileExt === 'docx') iconClass = 'ti ti-file-word';
            else if (fileExt === 'xls' || fileExt === 'xlsx') iconClass = 'ti ti-file-excel';
            else if (fileExt === 'jpg' || fileExt === 'jpeg' || fileExt === 'png') iconClass = 'ti ti-file-image';
            else if (fileExt === 'txt') iconClass = 'ti ti-file-text';
            
            div.innerHTML = `
                <i class="${iconClass}"></i>
                <a href="#" class="document-link" onclick="openDocument('${doc.url}', '${doc.name}'); return false;">
                    ${doc.name}
                </a>
                <span class="document-type">${doc.type}</span>
            `;
            docsContainer.appendChild(div);
        });
    } else {
        docsContainer.innerHTML = '<p style="color: var(--text-secondary);">No documents uploaded</p>';
    }
    
    document.getElementById('reviewComment').value = data.review_comments || '';
    clearErrors();
}

// Function to open document in new tab
function openDocument(url, fileName) {
    // Open in new tab
    window.open(url, '_blank');
    
    // Show notification
    showNotification(`Opening ${fileName}...`, 'info');
}

function closeModal() {
    document.getElementById('applicationModal').style.display = 'none';
    document.body.style.overflow = '';
    currentApplicationId = null;
    clearErrors();
}

function clearErrors() {
    document.querySelectorAll('.error-border').forEach(el => el.classList.remove('error-border'));
    const comment = document.getElementById('reviewComment');
    if (comment) comment.classList.remove('error');
    document.getElementById('commentRequiredMsg').style.display = 'none';
}

function updateStatus(status) {
    if (isProcessing) return;
    
    const comment = document.getElementById('reviewComment').value.trim();
    
    if ((status === 'accepted' || status === 'rejected') && !comment) {
        document.getElementById('reviewComment').classList.add('error');
        document.getElementById('commentRequiredMsg').style.display = 'block';
        document.getElementById('reviewComment').focus();
        showNotification('Please add comments when accepting or rejecting.', 'warning');
        return;
    }
    
    clearErrors();
    if (!currentApplicationId) {
        showNotification('No application selected', 'error');
        return;
    }
    
    isProcessing = true;
    const csrfToken = getCSRFToken();
    
    document.querySelectorAll('.review-btn').forEach(btn => {
        btn.disabled = true;
        btn.style.opacity = '0.6';
        btn.style.cursor = 'not-allowed';
    });
    
    fetch(`/faculty/api/application/${currentApplicationId}/update-status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ status: status, comments: comment })
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        if (data.success) {
            closeModal();
            showNotification(data.message, 'success');
            setTimeout(() => window.location.reload(), 1500);
        } else {
            showNotification(data.error || 'Error updating status', 'error');
            document.querySelectorAll('.review-btn').forEach(btn => {
                btn.disabled = false;
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error updating application status.', 'error');
        document.querySelectorAll('.review-btn').forEach(btn => {
            btn.disabled = false;
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
        });
    })
    .finally(() => { isProcessing = false; });
}

function saveReview() {
    if (!currentApplicationId) {
        showNotification('No application selected', 'error');
        return;
    }
    
    const comment = document.getElementById('reviewComment').value.trim();
    const csrfToken = getCSRFToken();
    
    fetch(`/faculty/api/application/${currentApplicationId}/save-review/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ comments: comment })
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
        } else {
            showNotification(data.error || 'Error saving review', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error saving review.', 'error');
    });
}

function showNotification(message, type = 'success') {
    const notificationMap = {
        'success': { id: 'successNotification', msgId: 'notificationMessage' },
        'error': { id: 'errorNotification', msgId: 'errorMessage' },
        'warning': { id: 'warningNotification', msgId: 'warningMessage' },
        'info': { id: 'successNotification', msgId: 'notificationMessage' }
    };
    
    const config = notificationMap[type];
    if (!config) return;
    
    const notification = document.getElementById(config.id);
    if (!notification) return;
    
    document.getElementById(config.msgId).textContent = message;
    notification.style.display = 'flex';
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 4000);
}

function closeNotification() {
    document.getElementById('successNotification').style.display = 'none';
}

function closeErrorNotification() {
    document.getElementById('errorNotification').style.display = 'none';
}

function closeWarningNotification() {
    document.getElementById('warningNotification').style.display = 'none';
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialize SlimSelect
    document.querySelectorAll('.filter-input').forEach(element => {
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
    
    // Remove withdrawn from status filter
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.querySelectorAll('option').forEach(opt => {
            if (opt.value === 'withdrawn') opt.remove();
        });
    }
});

document.getElementById('applicationModal')?.addEventListener('click', function(e) {
    if (e.target === this) closeModal();
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeModal();
});

document.getElementById('reviewComment')?.addEventListener('input', function() {
    if (this.value.trim()) {
        this.classList.remove('error');
        document.getElementById('commentRequiredMsg').style.display = 'none';
    }
});