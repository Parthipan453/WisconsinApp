document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.filter-input').forEach(select => {
        new SlimSelect({
            select: select,
            settings: {
                placeholderText: select.options[0].text,
                showSearch: false
            }
        });
    });
    AOS.init({
        duration: 600,
        once: true,
        offset: 50
    });

});

let currentFacultyUuid = null;
let currentFacultyName = '';

function getCSRFToken() {
    return document.getElementById('csrfToken')?.value || '';
}

function resetFilters() {
    document.getElementById('departmentFilter').value = '';
    document.getElementById('roleFilter').value = '';
    document.getElementById('searchInput').value = '';
    document.getElementById('filterForm').submit();
}

function openModal(facultyUuid, facultyName, facultyDept) {
    const modal = document.getElementById('assignModal');
    currentFacultyUuid = facultyUuid;
    currentFacultyName = facultyName;
    
    document.getElementById('modalFacultyName').textContent = facultyName;
    document.getElementById('modalFacultyDept').textContent = facultyDept || 'No Department';
    document.getElementById('modalFacultyAvatar').textContent = facultyName.slice(0, 2).toUpperCase();
    
    // Reset radio buttons
    document.querySelectorAll('input[name="mentor_role"]').forEach(el => el.checked = false);
    
    // Set modal title
    document.getElementById('modalTitle').innerHTML = `
        <i class="ti ti-user-plus"></i>
        Assign Mentor Role
    `;
    document.getElementById('confirmAssignBtn').innerHTML = '<i class="ti ti-check"></i> Assign Role';
    
    // Load current role
    loadCurrentRole(facultyUuid);
    
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function loadCurrentRole(facultyUuid) {
    const url = `/research/assign/faculty/${facultyUuid}/get-roles/`;
    
    fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            const currentRoleSpan = document.getElementById('currentRole');
            if (data.has_role) {
                currentRoleSpan.textContent = data.role_display;
                document.getElementById('modalTitle').innerHTML = `
                    <i class="ti ti-edit"></i>
                    Update Mentor Role
                `;
                document.getElementById('confirmAssignBtn').innerHTML = '<i class="ti ti-check"></i> Update Role';
            } else {
                currentRoleSpan.textContent = 'No Role Assigned';
            }
        }
    })
    .catch(error => {
        console.error('Error loading role:', error);
    });
}

function closeModal() {
    document.getElementById('assignModal').style.display = 'none';
    document.body.style.overflow = '';
    currentFacultyUuid = null;
}

function confirmAssign() {
    if (!currentFacultyUuid) {
        showNotification('No faculty selected', 'error');
        return;
    }

    const selectedRole = document.querySelector('input[name="mentor_role"]:checked');
    
    if (!selectedRole) {
        showNotification('Please select a role to assign.', 'error');
        return;
    }

    const role = selectedRole.value;
    const action = role === 'none' ? 'remove' : 'assign';
    const csrfToken = getCSRFToken();
    const url = `/research/assign/faculty/${currentFacultyUuid}/assign-role/`;
    
    // Disable button to prevent double submission
    const confirmBtn = document.getElementById('confirmAssignBtn');
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = '<i class="ti ti-loader"></i> Processing...';
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            role: role,
            action: action
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || 'Server error');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            const roleLabels = {
                'mentor': 'Mentor',
            };
            if (action === 'remove') {
                showNotification(`Role removed successfully from ${currentFacultyName}`, 'success');
            } else {
                showNotification(`${roleLabels[role]} role assigned to ${currentFacultyName}`, 'success');
            }
            closeModal();
            // Refresh page after a short delay
            setTimeout(() => {
                location.reload();
            }, 1500);
        } else {
            showNotification(data.error || 'An error occurred', 'error');
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = '<i class="ti ti-check"></i> Assign Role';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred. Please try again.', 'error');
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = '<i class="ti ti-check"></i> Assign Role';
    });
}

// Notification Functions
function showNotification(message, type = 'success') {
    if (type === 'success') {
        const notification = document.getElementById('successNotification');
        document.getElementById('notificationMessage').textContent = message;
        notification.style.display = 'flex';
        setTimeout(() => {
            notification.style.display = 'none';
        }, 4000);
    } else {
        const notification = document.getElementById('errorNotification');
        document.getElementById('errorMessage').textContent = message;
        notification.style.display = 'flex';
        setTimeout(() => {
            notification.style.display = 'none';
        }, 4000);
    }
}

function closeNotification() {
    document.getElementById('successNotification').style.display = 'none';
}

function closeErrorNotification() {
    document.getElementById('errorNotification').style.display = 'none';
}

// Close modal on overlay click
document.getElementById('assignModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeModal();
    }
});
