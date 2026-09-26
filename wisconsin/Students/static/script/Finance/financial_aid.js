// blaze code start--------------------------------------------------->


document.addEventListener('DOMContentLoaded', function() {
    // File input display
    const fileInput = document.getElementById('fileInput');
    const fileName = document.getElementById('fileName');
    
    if (fileInput && fileName) {
        fileInput.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                fileName.textContent = this.files[0].name;
            } else {
                fileName.textContent = 'No file chosen';
            }
        });
    }
    
    // Conditional fields toggle
    const aidTypeSelect = document.getElementById('aidTypeSelect');
    const loanFields = document.getElementById('loanFields');
    const assistantshipFields = document.getElementById('assistantshipFields');
    
    if (aidTypeSelect) {
        aidTypeSelect.addEventListener('change', function() {
            if (loanFields) loanFields.style.display = 'none';
            if (assistantshipFields) assistantshipFields.style.display = 'none';
            
            if (this.value === 'LOAN' && loanFields) {
                loanFields.style.display = 'block';
            } else if (this.value === 'ASSISTANTSHIP' && assistantshipFields) {
                assistantshipFields.style.display = 'block';
            }
        });
    }
    
    // Edit form submit
    const editForm = document.getElementById('editForm');
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            e.preventDefault();
            updateAid();
        });
    }
    
    // Add form submit
    const addForm = document.getElementById('addForm');
    if (addForm) {
        addForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitAid();
        });
    }
    
    // Close modals on backdrop click
    const addModal = document.getElementById('addModal');
    if (addModal) {
        addModal.addEventListener('click', function(e) {
            if (e.target === this) closeAddModal();
        });
    }
    
    const detailModal = document.getElementById('detailModal');
    if (detailModal) {
        detailModal.addEventListener('click', function(e) {
            if (e.target === this) closeDetailModal();
        });
    }
    
    const editModal = document.getElementById('editModal');
    if (editModal) {
        editModal.addEventListener('click', function(e) {
            if (e.target === this) closeEditModal();
        });
    }
    
    // ESC key to close modals
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeAddModal();
            closeDetailModal();
            closeEditModal();
        }
    });
    
    // Initialize Choices.js
    setTimeout(initChoicesJS, 300);
});

// ============================================================
// CHOICES.JS INITIALIZATION
// ============================================================

function initChoicesJS() {
    if (typeof Choices === 'undefined') {
        console.log('Choices.js not loaded, retrying...');
        setTimeout(initChoicesJS, 500);
        return;
    }
    
    const selectWrappers = document.querySelectorAll('.choices-form-wrapper select');
    selectWrappers.forEach(function(select) {
        try {
            if (select._choicesInstance) {
                select._choicesInstance.destroy();
                delete select._choicesInstance;
            }
            
            const choices = new Choices(select, {
                searchEnabled: true,
                searchPlaceholderValue: 'Search...',
                shouldSort: false,
                position: 'auto',
                placeholder: true,
                placeholderValue: select.options[0] ? select.options[0].text : 'Select...',
                itemSelectText: '',
                renderSelectedChoices: 'always',
                classNames: {
                    containerOuter: 'choices choices-form',
                    containerInner: 'choices__inner',
                    input: 'choices__input',
                    inputCloned: 'choices__input--cloned',
                    list: 'choices__list',
                    listItems: 'choices__list--multiple',
                    listSingle: 'choices__list--single',
                    listDropdown: 'choices__list--dropdown',
                    item: 'choices__item',
                    itemSelectable: 'choices__item--selectable',
                    itemDisabled: 'choices__item--disabled',
                    itemChoice: 'choices__item--choice',
                    placeholder: 'choices__placeholder',
                    group: 'choices__group',
                    groupHeading: 'choices__heading',
                    button: 'choices__button',
                    activeState: 'is-active',
                    focusState: 'is-focused',
                    openState: 'is-open',
                    disabledState: 'is-disabled',
                    highlightedState: 'is-highlighted',
                    hiddenState: 'is-hidden',
                    flippedState: 'is-flipped',
                    loadingState: 'is-loading',
                    noResults: 'has-no-results',
                    noChoices: 'has-no-choices'
                }
            });
            
            select._choicesInstance = choices;
            console.log('Choices.js initialized for #' + select.id);
        } catch (e) {
            console.log('Error initializing #' + select.id + ':', e);
        }
    });
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function getUUID() {
    const pathParts = window.location.pathname.split('/');
    for (let part of pathParts) {
        if (part && part.length === 36 && part.includes('-')) {
            return part;
        }
    }
    
    const meta = document.querySelector('meta[name="user-uuid"]');
    if (meta) {
        return meta.content;
    }
    
    console.error('Could not find UUID');
    return null;
}

// ============================================================
// ADD MODAL
// ============================================================

function openAddModal() {
    const m = document.getElementById('addModal');
    if (m) {
        m.classList.add('open');
        document.body.style.overflow = 'hidden';
        const f = m.querySelector('form');
        if (f) f.reset();
        const fn = document.getElementById('fileName');
        if (fn) fn.textContent = 'No file chosen';
        const loanFields = document.getElementById('loanFields');
        const assistantshipFields = document.getElementById('assistantshipFields');
        if (loanFields) loanFields.style.display = 'none';
        if (assistantshipFields) assistantshipFields.style.display = 'none';
        
        setTimeout(initChoicesJS, 100);
    }
}

function closeAddModal() {
    const m = document.getElementById('addModal');
    if (m) {
        m.classList.remove('open');
        document.body.style.overflow = '';
    }
}

// ============================================================
// SUBMIT AID (ADD) - UPDATED TOAST
// ============================================================

function submitAid() {
    const form = document.getElementById('addForm');
    if (!form) return;
    
    const aidTypeSelect = document.getElementById('aidTypeSelect');
    const academicYearSelect = document.getElementById('academicYearSelect');
    
    let aidType = aidTypeSelect.value;
    let academicYear = academicYearSelect.value;
    
    if (aidTypeSelect._choicesInstance) {
        aidType = aidTypeSelect._choicesInstance.getValue(true);
    }
    if ( academicYearSelect._choicesInstance) {
        academicYear = academicYearSelect._choicesInstance.getValue(true);
    }
    
    const formData = new FormData(form);
    formData.set('aid_type', aidType);
    formData.set('academic_year', academicYear);
    
    const btn = form.querySelector('.fa-btn-submit');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="ti ti-loader" style="animation: spin 1s linear infinite;"></i> Submitting...';
    btn.disabled = true;
    
    const u = getUUID();
    
    fetch(`/student/finance/aid/${u}/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: formData,
    })
    .then(response => {
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        }
        return response.text().then(text => {
            if (text.includes('Financial aid application')) {
                return { success: true, message: 'Application submitted! Please refresh.' };
            }
            throw new Error('Server returned HTML. Record may still be created.');
        });
    })
    .then(result => {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
        
        if (result.success) {
            toastSuccess('Application submitted successfully!');  
            setTimeout(() => {
                closeAddModal();
                window.location.reload();
            }, 1500);
        } else {
            toastError(result.error || 'Failed to submit'); 
        }
    })
    .catch(error => {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
        console.error('Submit error:', error);
        
        if (error.message.includes('HTML')) {
            toastSuccess('Application submitted! Refreshing...'); 
            setTimeout(() => window.location.reload(), 1500);
        } else {
            toastError('Error: ' + error.message); 
        }
    });
}

// ============================================================
// DETAIL MODAL
// ============================================================

function openDetail(data) {
    const m = document.getElementById('detailModal');
    if (!m) return;
    
    document.getElementById('detailType').textContent = data.aid_type_display || data.aid_type || '--';
    document.getElementById('detailYear').textContent = data.academic_year || '--';
    document.getElementById('detailReason').textContent = data.reason || data.financial_need_description || data.description || '--';
    document.getElementById('detailAmount').textContent = data.award_amount ? `$${data.award_amount}` : '--';
    
    const dateValue = data.applied_date || data.created_at || data.date || '--';
    document.getElementById('detailDate').textContent = dateValue;
    
    document.getElementById('detailRemarks').textContent = data.remarks || 'No remarks';
    
    const statusEl = document.getElementById('detailStatus');
    const statusClass = (data.status || 'pending').toLowerCase();
    statusEl.className = `fa-status-badge ${statusClass}`;
    statusEl.textContent = data.status_display || data.status || '--';
    
    const docLink = document.getElementById('detailDocLink');
    const noDoc = document.getElementById('detailNoDoc');
    if (data.supporting_document) {
        docLink.href = data.supporting_document;
        docLink.style.display = 'inline-flex';
        noDoc.style.display = 'none';
    } else {
        docLink.style.display = 'none';
        noDoc.style.display = 'inline';
    }
    
    m.classList.add('open');
    document.body.style.overflow = 'hidden';
}

function closeDetailModal() {
    const m = document.getElementById('detailModal');
    if (m) {
        m.classList.remove('open');
        document.body.style.overflow = '';
    }
}

// ============================================================
// EDIT MODAL
// ============================================================

function openEdit(data) {
    const m = document.getElementById('editModal');
    if (!m) return;
    
    document.getElementById('editId').value = data.id;
    
    const editType = document.getElementById('editType');
    const editYear = document.getElementById('editYear');
    
    if (editType._choicesInstance) {
        editType._choicesInstance.setChoiceByValue(data.aid_type || '');
    } else {
        editType.value = data.aid_type || '';
    }
    
    if (editYear._choicesInstance) {
        editYear._choicesInstance.setChoiceByValue(data.academic_year || '');
    } else {
        editYear.value = data.academic_year || '';
    }
    
    document.getElementById('editReason').value = data.reason || data.financial_need_description || '';
    
    const di = document.getElementById('editDocInfo');
    if (data.supporting_document) {
        const filename = data.supporting_document.split('/').pop();
        di.innerHTML = `<i class="ti ti-file"></i> Current: ${filename}`;
        di.style.display = 'block';
    } else {
        di.style.display = 'none';
    }
    
    m.classList.add('open');
    document.body.style.overflow = 'hidden';
}

function closeEditModal() {
    const m = document.getElementById('editModal');
    if (m) {
        m.classList.remove('open');
        document.body.style.overflow = '';
    }
}

// ============================================================
// UPDATE AID - UPDATED TOAST
// ============================================================

function updateAid() {
    const form = document.getElementById('editForm');
    if (!form) return;
    
    const editType = document.getElementById('editType');
    const editYear = document.getElementById('editYear');
    
    let aidType = editType.value;
    let academicYear = editYear.value;
    
    if (editType._choicesInstance) {
        aidType = editType._choicesInstance.getValue(true);
    }
    if (editYear._choicesInstance) {
        academicYear = editYear._choicesInstance.getValue(true);
    }
    
    const formData = new FormData(form);
    const data = {
        aid_id: formData.get('aid_id'),
        aid_type: aidType,
        academic_year: academicYear,
        reason: formData.get('reason'),
    };
    
    if (!data.aid_type || !data.academic_year || !data.reason) {
        toastError('All fields are required');  
        return;
    }
    
    const btn = form.querySelector('.fa-btn-submit');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="ti ti-loader" style="animation: spin 1s linear infinite;"></i> Updating...';
    btn.disabled = true;
    
    const u = getUUID();
    
    fetch(`/student/finance/aid/${u}/update/${data.aid_id}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify(data),
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || `HTTP ${response.status}`);
            });
        }
        return response.json();
    })
    .then(result => {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
        
        if (result.success) {
            toastSuccess('Application updated successfully!');  
            setTimeout(() => {
                closeEditModal();
                window.location.reload();
            }, 1000);
        } else {
            toastError(result.error || 'Failed to update');  
        }
    })
    .catch(error => {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
        console.error('Update error:', error);
        toastError('Error: ' + error.message);  
    });
}

// ============================================================
// FILTER
// ============================================================

function filterAid(btn, type) {
    document.querySelectorAll('.fa-tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    
    const rows = document.querySelectorAll('.fa-table tbody tr');
    let count = 0;
    
    rows.forEach(row => {
        const show = type === 'ALL' || row.dataset.type === type;
        row.style.display = show ? '' : 'none';
        if (show) count++;
    });
    
    document.querySelectorAll('.fa-tab').forEach(tab => {
        const tabType = tab.textContent.trim().split(' ')[0];
        if (tabType === 'All' && type === 'ALL') {
            const countSpan = tab.querySelector('.fa-tab-count');
            if (countSpan) countSpan.textContent = count;
        }
    });
    
    const empty = document.querySelector('.fa-empty');
    if (empty) {
        empty.style.display = count === 0 ? 'block' : 'none';
    }
}

// ============================================================
// ACTIONS - UPDATED TOAST
// ============================================================

function viewAid(id) {
    const u = getUUID();
    if (!u) {
        toastError('User ID not found');  
        return;
    }
    
    fetch(`/student/finance/aid/${u}/detail/${id}/`)
        .then(r => {
            if (!r.ok) {
                throw new Error('Network response was not ok');
            }
            return r.json();
        })
        .then(d => {
            if (d.success) {
                const aidData = d.data || d.aid || d;
                openDetail(aidData);
            } else {
                toastError('Failed to load details.');  
            }
        })
        .catch(() => toastError('Network error.')); 
}

function editAid(id) {
    const u = getUUID();
    if (!u) {
        toastError('User ID not found');  
        return;
    }
    
    fetch(`/student/finance/aid/${u}/detail/${id}/`)
        .then(r => {
            if (!r.ok) {
                throw new Error('Network response was not ok');
            }
            return r.json();
        })
        .then(d => {
            if (d.success) {
                const aidData = d.data || d.aid || d;
                openEdit(aidData);
            } else {
                toastError('Failed to load data.');  
            }
        })
        .catch(() => toastError('Network error.'));  
}

function cancelAid(id) {
    if (!confirm('Cancel this application? This cannot be undone.')) return;
    
    const u = getUUID();
    if (!u) {
        toastError('User ID not found');
        return;
    }
    
    fetch(`/student/finance/aid/${u}/cancel/${id}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ aid_id: id })
    })
    .then(r => r.json())
    .then(d => {
        if (d.success) {
            toastSuccess('Cancelled successfully.');  
            setTimeout(() => location.reload(), 1000);
        } else {
            toastError(d.message || 'Failed to cancel.');  
        }
    })
    .catch(() => toastError('Network error.')); 
}

function printAid(id) {
    const u = getUUID();
    if (!u) {
        toastError('User ID not found'); 
        return;
    }
    window.open(`/student/finance/aid/${u}/print/${id}/`, '_blank');
}

// ============================================================
// EXPOSE TO GLOBAL
// ============================================================

window.openAddModal = openAddModal;
window.closeAddModal = closeAddModal;
window.closeDetailModal = closeDetailModal;
window.closeEditModal = closeEditModal;
window.filterAid = filterAid;
window.viewAid = viewAid;
window.editAid = editAid;
window.cancelAid = cancelAid;
window.printAid = printAid;
window.getUUID = getUUID;
window.getCookie = getCookie;
window.submitAid = submitAid;
window.updateAid = updateAid;
window.initChoicesJS = initChoicesJS;

console.log('Financial Aid loaded with parent toast system');

// blaze code end--------------------------------------------------->