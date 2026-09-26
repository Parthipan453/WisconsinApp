// ============================================
// APPLICATION FORM JAVASCRIPT
// UI Management with Step Validation
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Skip if in readonly view
    if (document.querySelector('.readonly-view')) {
        return;
    }

    // Initialize SlimSelect
    initSlimSelect();
    
    // Initialize file uploads
    initFileUploads();
    
    // Initialize review update
    updateReview();
    
    // Check for success on page load
    checkForSuccess();
    
    // Add input event listeners to clear errors on typing
    initInputListeners();
});

// ============================================
// STEP MANAGEMENT
// ============================================
let currentStep = 1;
const totalSteps = 4;

function initSlimSelect() {
    if (typeof SlimSelect === 'undefined') return;
    
    document.querySelectorAll('.filter-input').forEach(element => {
        if (element.tagName.toLowerCase() === 'select') {
            try {
                if (element.dataset.ssid) return;
                
                new SlimSelect({
                    select: element,
                    settings: {
                        placeholderText: element.options[0]?.text || 'Select an option',
                        showSearch: false
                    }
                });
            } catch (e) {
                console.debug('SlimSelect initialization skipped:', e);
            }
        }
    });
}

// ============================================
// INPUT LISTENERS - Clear errors on typing
// ============================================
function initInputListeners() {
    // Text inputs and textareas
    const textFields = [
        'id_motivation',
        'id_skills_contribution', 
        'id_prior_experience',
        'id_additional_info'
    ];
    
    textFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (!field) return;
        
        field.addEventListener('input', function() {
            clearFieldError(fieldId);
            // Remove error class from field
            this.classList.remove('error');
            // Remove error class from parent form group
            const formGroup = this.closest('.form-groups');
            if (formGroup) {
                formGroup.classList.remove('has-error');
            }
        });
    });
    
    // Select fields
    const selectFields = [
        'id_time_commitment',
        'id_availability'
    ];
    
    selectFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (!field) return;
        
        field.addEventListener('change', function() {
            if (this.value && this.value !== '') {
                clearFieldError(fieldId);
                this.classList.remove('error');
                const formGroup = this.closest('.form-groups');
                if (formGroup) {
                    formGroup.classList.remove('has-error');
                }
            }
        });
    });
    
    // File inputs
    const fileFields = [
        'id_resume',
        'id_statement_of_interest',
        'id_academic_transcript'
    ];
    
    fileFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (!field) return;
        
        field.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                clearFieldError(fieldId);
                this.classList.remove('error');
                const formGroup = this.closest('.form-groups');
                if (formGroup) {
                    formGroup.classList.remove('has-error');
                }
                // Remove error class from file upload div
                const fileUpload = this.closest('.file-upload-wrapper')?.querySelector('.file-upload');
                if (fileUpload) {
                    fileUpload.classList.remove('error');
                }
            }
        });
    });
    
    // Checkbox - Add event listener to clear error when checked
    const termsField = document.getElementById('id_confirm_terms');
    if (termsField) {
        termsField.addEventListener('change', function() {
            if (this.checked) {
                clearFieldError('id_confirm_terms');
                const formGroup = document.getElementById('terms-group');
                if (formGroup) {
                    formGroup.classList.remove('has-error');
                }
                // Also remove error class from the checkbox wrapper if exists
                const checkboxWrapper = this.closest('.checkbox-wrapper');
                if (checkboxWrapper) {
                    checkboxWrapper.classList.remove('has-error');
                }
            }
        });
    }
}

// ============================================
// FIELD VALIDATION FUNCTIONS
// ============================================

// Show error below a field
function showFieldError(fieldId, errorMessage) {
    // Find or create error container
    let container = document.getElementById(fieldId + '-error');
    
    // If container doesn't exist, try to find it by other naming convention
    if (!container) {
        // For file fields, the error container might be named differently
        const field = document.getElementById(fieldId);
        if (field) {
            const formGroup = field.closest('.form-groups') || field.closest('.form-checkbox');
            if (formGroup) {
                container = formGroup.querySelector('.error-container');
            }
        }
    }
    
    // If still no container, create one
    if (!container) {
        const field = document.getElementById(fieldId);
        if (field) {
            const formGroup = field.closest('.form-groups') || field.closest('.form-checkbox');
            if (formGroup) {
                container = document.createElement('div');
                container.className = 'error-container';
                container.id = fieldId + '-error';
                formGroup.appendChild(container);
            }
        }
    }
    
    if (!container) {
        // If still no container, try to find any error container in the parent
        const field = document.getElementById(fieldId);
        if (field) {
            const parent = field.closest('.form-groups') || field.closest('.form-checkbox');
            if (parent) {
                const existingContainer = parent.querySelector('.error-container');
                if (existingContainer) {
                    container = existingContainer;
                }
            }
        }
    }
    
    if (!container) return;
    
    // Clear existing errors
    container.innerHTML = '';
    
    // Create error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `<i class="ti ti-alert-circle"></i> ${errorMessage}`;
    container.appendChild(errorDiv);
    
    // Add error class to field
    const field = document.getElementById(fieldId);
    if (field) {
        field.classList.add('error');
        // Add error class to parent form group
        const formGroup = field.closest('.form-groups') || field.closest('.form-checkbox');
        if (formGroup) {
            formGroup.classList.add('has-error');
        }
    }
}

// Clear error below a field
function clearFieldError(fieldId) {
    let container = document.getElementById(fieldId + '-error');
    
    if (!container) {
        const field = document.getElementById(fieldId);
        if (field) {
            const formGroup = field.closest('.form-groups') || field.closest('.form-checkbox');
            if (formGroup) {
                container = formGroup.querySelector('.error-container');
            }
        }
    }
    
    if (container) {
        container.innerHTML = '';
    }
    
    const field = document.getElementById(fieldId);
    if (field) {
        field.classList.remove('error');
        const formGroup = field.closest('.form-groups') || field.closest('.form-checkbox');
        if (formGroup) {
            formGroup.classList.remove('has-error');
        }
    }
}

// Validate a single field
function validateField(fieldId) {
    const field = document.getElementById(fieldId);
    if (!field) return true;
    
    // Clear existing error
    clearFieldError(fieldId);
    
    // Check if field is required and empty
    if (field.hasAttribute('required')) {
        // For checkbox
        if (field.type === 'checkbox') {
            if (!field.checked) {
                showFieldError(fieldId, 'You must agree to the terms and conditions.');
                return false;
            }
            return true;
        }
        
        // For file inputs
        if (field.type === 'file') {
            if (!field.files || field.files.length === 0) {
                const label = document.querySelector(`label[for="${fieldId}"]`)?.textContent?.replace('*', '').trim() || 'File';
                showFieldError(fieldId, `${label} is required.`);
                return false;
            }
            return true;
        }
        
        // For text inputs, textareas, selects
        if (!field.value || field.value.trim() === '' || field.value === '') {
            const label = document.querySelector(`label[for="${fieldId}"]`)?.textContent?.replace('*', '').trim() || 'This field';
            showFieldError(fieldId, `${label} is required.`);
            return false;
        }
    }
    
    // Special validation for textareas (character limits)
    if (fieldId === 'id_motivation') {
        const value = field.value.trim();
        if (value.length > 0 && value.length < 50) {
            showFieldError(fieldId, `Motivation must be at least 50 characters. (Current: ${value.length} characters)`);
            return false;
        }
        if (value.length > 2000) {
            showFieldError(fieldId, `Motivation cannot exceed 2000 characters. (Current: ${value.length} characters)`);
            return false;
        }
    }
    
    if (fieldId === 'id_skills_contribution') {
        const value = field.value.trim();
        if (value.length > 0 && value.length < 30) {
            showFieldError(fieldId, `Skills contribution must be at least 30 characters. (Current: ${value.length} characters)`);
            return false;
        }
        if (value.length > 1500) {
            showFieldError(fieldId, `Skills contribution cannot exceed 1500 characters. (Current: ${value.length} characters)`);
            return false;
        }
    }
    
    return true;
}

// Validate select field (for placeholder check)
function validateSelectField(fieldId) {
    const field = document.getElementById(fieldId);
    if (!field) return true;
    
    // Clear existing error
    clearFieldError(fieldId);
    
    // Check if a valid option is selected (not the placeholder)
    if (field.value === '' || field.value === null) {
        const label = document.querySelector(`label[for="${fieldId}"]`)?.textContent?.replace('*', '').trim() || 'This field';
        showFieldError(fieldId, `Please select a ${label.toLowerCase()}.`);
        return false;
    }
    
    return true;
}

// ============================================
// STEP VALIDATION
// ============================================
function validateStep(step) {
    let valid = true;
    
    // Validate fields based on step
    if (step === 2) {
        // Step 2: Project Details
        const fields = [
            { id: 'id_motivation', type: 'text' },
            { id: 'id_skills_contribution', type: 'text' },
            { id: 'id_time_commitment', type: 'select' },
            { id: 'id_availability', type: 'select' }
        ];
        
        fields.forEach(({ id, type }) => {
            if (type === 'select') {
                if (!validateSelectField(id)) {
                    valid = false;
                }
            } else {
                if (!validateField(id)) {
                    valid = false;
                }
            }
        });
    }
    
    if (step === 3) {
        // Step 3: Documents
        const fileFields = [
            'id_resume',
            'id_statement_of_interest',
            'id_academic_transcript'
        ];
        
        fileFields.forEach(fieldId => {
            if (!validateField(fieldId)) {
                valid = false;
            }
        });
    }
    
    if (step === 4) {
        // Step 4: Terms - Validate checkbox
        const termsField = document.getElementById('id_confirm_terms');
        if (termsField) {
            // Clear any existing error first
            clearFieldError('id_confirm_terms');
            
            if (!termsField.checked) {
                // Show error for checkbox
                showFieldError('id_confirm_terms', 'You must agree to the terms and conditions.');
                
                // Add error class to the form-checkbox container
                const formGroup = document.getElementById('terms-group');
                if (formGroup) {
                    formGroup.classList.add('has-error');
                }
                
                // Add error class to checkbox wrapper
                const checkboxWrapper = termsField.closest('.checkbox-wrapper');
                if (checkboxWrapper) {
                    checkboxWrapper.classList.add('has-error');
                }
                
                valid = false;
            } else {
                // Clear error if checked
                clearFieldError('id_confirm_terms');
                const formGroup = document.getElementById('terms-group');
                if (formGroup) {
                    formGroup.classList.remove('has-error');
                }
                const checkboxWrapper = termsField.closest('.checkbox-wrapper');
                if (checkboxWrapper) {
                    checkboxWrapper.classList.remove('has-error');
                }
            }
        }
    }
    
    // Scroll to first error if invalid
    if (!valid) {
        const firstError = document.querySelector('.error-message');
        if (firstError) {
            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            const errorContainer = firstError.closest('.error-container');
            if (errorContainer) {
                const fieldId = errorContainer.id?.replace('-error', '');
                if (fieldId) {
                    const field = document.getElementById(fieldId);
                    if (field) {
                        setTimeout(() => field.focus(), 300);
                    }
                }
            }
        }
    }
    
    return valid;
}

// ============================================
// STEP NAVIGATION
// ============================================
function goToStep(step) {
    if (step < 1 || step > totalSteps) return;
    
    // If going forward, validate current step
    if (step > currentStep) {
        if (!validateStep(currentStep)) {
            return;
        }
    }
    
    currentStep = step;
    updateSteps();
}

function nextStep() {
    // Validate current step before proceeding
    if (!validateStep(currentStep)) {
        return;
    }
    
    if (currentStep < totalSteps) {
        currentStep++;
        updateSteps();
    }
}

function prevStep() {
    if (currentStep > 1) {
        currentStep--;
        updateSteps();
    }
}

function updateSteps() {
    // Update progress steps
    document.querySelectorAll('.progress-step').forEach((el, index) => {
        el.classList.remove('active', 'completed');
        if (index + 1 === currentStep) {
            el.classList.add('active');
        } else if (index + 1 < currentStep) {
            el.classList.add('completed');
        }
    });

    // Update form steps
    document.querySelectorAll('.form-step').forEach((el, index) => {
        el.classList.remove('active');
        if (index + 1 === currentStep) {
            el.classList.add('active');
        }
    });

    // Update navigation buttons
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    
    if (prevBtn) {
        prevBtn.style.display = currentStep === 1 ? 'none' : 'inline-flex';
    }
    if (nextBtn) {
        nextBtn.style.display = currentStep === totalSteps ? 'none' : 'inline-flex';
    }
    if (submitBtn) {
        submitBtn.style.display = currentStep === totalSteps ? 'inline-flex' : 'none';
    }

    // Scroll to top of form
    const formContainer = document.querySelector('.form-container');
    if (formContainer) {
        formContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    // Update review if on last step
    if (currentStep === totalSteps) {
        updateReview();
    }
}

// ============================================
// FILE UPLOADS WITH VALIDATION
// ============================================
function initFileUploads() {
    const fileConfigs = [
        { 
            inputId: 'id_resume', 
            previewId: 'resumePreview', 
            displayId: 'resumeFileName',
            fieldName: 'Resume/CV'
        },
        { 
            inputId: 'id_statement_of_interest', 
            previewId: 'sopPreview', 
            displayId: 'sopFileName',
            fieldName: 'Statement of Interest'
        },
        { 
            inputId: 'id_academic_transcript', 
            previewId: 'transcriptPreview', 
            displayId: 'transcriptFileName',
            fieldName: 'Academic Transcript'
        }
    ];

    fileConfigs.forEach(config => {
        const input = document.getElementById(config.inputId);
        const preview = document.getElementById(config.previewId);
        const display = document.getElementById(config.displayId);

        if (!input) return;

        input.addEventListener('change', function(e) {
            const file = this.files?.[0];
            
            // Clear existing errors
            clearFieldError(config.inputId);
            this.classList.remove('error');
            const fileUpload = this.closest('.file-upload-wrapper')?.querySelector('.file-upload');
            if (fileUpload) {
                fileUpload.classList.remove('error');
            }
            
            if (file) {
                // Validate file type - ONLY PDF, DOC, DOCX allowed
                const allowedExtensions = ['pdf', 'doc', 'docx'];
                const ext = file.name.split('.').pop().toLowerCase();
                
                if (!allowedExtensions.includes(ext)) {
                    showFieldError(
                        config.inputId, 
                        `Invalid file type for ${config.fieldName}. Only PDF, DOC, and DOCX files are allowed. (File: ${file.name})`
                    );
                    this.value = '';
                    if (display) display.textContent = 'No file selected';
                    if (preview) preview.style.display = 'none';
                    if (fileUpload) fileUpload.classList.add('error');
                    this.classList.add('error');
                    return;
                }
                
                // Validate file size (5MB max)
                const maxSize = 5 * 1024 * 1024;
                if (file.size > maxSize) {
                    const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
                    showFieldError(
                        config.inputId, 
                        `${config.fieldName} file size cannot exceed 5MB. (File: ${file.name}, Size: ${sizeMB}MB)`
                    );
                    this.value = '';
                    if (display) display.textContent = 'No file selected';
                    if (preview) preview.style.display = 'none';
                    if (fileUpload) fileUpload.classList.add('error');
                    this.classList.add('error');
                    return;
                }

                // Valid file
                if (display) display.textContent = file.name;
                if (preview) {
                    preview.style.display = 'flex';
                    const fileNameSpan = preview.querySelector('span');
                    if (fileNameSpan) {
                        fileNameSpan.textContent = file.name;
                    }
                }
                fileUpload?.classList.remove('error');
            } else {
                if (display) display.textContent = 'No file selected';
                if (preview) preview.style.display = 'none';
            }
        });
    });
}

function removeFile(inputId, previewId, displayId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    const display = document.getElementById(displayId);
    
    if (input) {
        input.value = '';
        clearFieldError(inputId);
        input.classList.remove('error');
        const formGroup = input.closest('.form-groups');
        if (formGroup) {
            formGroup.classList.remove('has-error');
        }
        const fileUpload = input.closest('.file-upload-wrapper')?.querySelector('.file-upload');
        if (fileUpload) {
            fileUpload.classList.remove('error');
        }
    }
    if (display) display.textContent = 'No file selected';
    if (preview) preview.style.display = 'none';
}

// ============================================
// REVIEW
// ============================================
function updateReview() {
    // Personal Info
    document.getElementById('reviewName').textContent = document.querySelector('[name="full_name"]')?.value || '-';
    document.getElementById('reviewEmail').textContent = document.querySelector('[name="email"]')?.value || '-';
    document.getElementById('reviewPhone').textContent = document.querySelector('[name="phone"]')?.value || '-';
    document.getElementById('reviewDepartment').textContent = document.querySelector('[name="department"]')?.value || '-';
    document.getElementById('reviewId').textContent = document.querySelector('[name="id_number"]')?.value || '-';
    document.getElementById('reviewProgram').textContent = document.querySelector('[name="program"]')?.value || '-';

    // Project Details
    document.getElementById('reviewMotivation').textContent = document.getElementById('id_motivation')?.value || '-';
    document.getElementById('reviewSkills').textContent = document.getElementById('id_skills_contribution')?.value || '-';
    document.getElementById('reviewExperience').textContent = document.getElementById('id_prior_experience')?.value || '-';
    
    const timeSelect = document.getElementById('id_time_commitment');
    document.getElementById('reviewTime').textContent = timeSelect?.options[timeSelect.selectedIndex]?.text || '-';
    
    const availSelect = document.getElementById('id_availability');
    document.getElementById('reviewAvailability').textContent = availSelect?.options[availSelect.selectedIndex]?.text || '-';
    
    document.getElementById('reviewAdditional').textContent = document.getElementById('id_additional_info')?.value || '-';

    // Documents
    const resumeInput = document.getElementById('id_resume');
    document.getElementById('reviewResume').textContent = resumeInput?.files[0]?.name || 'No file uploaded';
    
    const sopInput = document.getElementById('id_statement_of_interest');
    document.getElementById('reviewSOP').textContent = sopInput?.files[0]?.name || 'No file uploaded';
    
    const transcriptInput = document.getElementById('id_academic_transcript');
    document.getElementById('reviewTranscript').textContent = transcriptInput?.files[0]?.name || 'No file uploaded';
}

// ============================================
// CONFIRM MODAL
// ============================================
function showConfirmModal() {
    // First validate step 4 (terms checkbox)
    if (!validateStep(4)) {
        // If step 4 validation fails, stay on step 4
        currentStep = 4;
        updateSteps();
        showToast('Please agree to the terms and conditions.', 'error');
        return;
    }
    
    // Validate all steps before showing confirm modal
    let allValid = true;
    for (let i = 2; i <= 3; i++) {
        if (!validateStep(i)) {
            allValid = false;
            currentStep = i;
            updateSteps();
            break;
        }
    }
    
    // Also validate step 4 again
    if (!validateStep(4)) {
        allValid = false;
        currentStep = 4;
        updateSteps();
    }
    
    if (!allValid) {
        showToast('Please fill in all required fields before submitting.', 'error');
        return;
    }
    
    document.getElementById('confirmModal').style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeConfirmModal() {
    document.getElementById('confirmModal').style.display = 'none';
    document.body.style.overflow = '';
}

function submitApplication() {
    closeConfirmModal();
    const form = document.getElementById('applicationForm');
    if (form) {
        const confirmBtn = document.querySelector('.btn-confirm');
        if (confirmBtn) {
            confirmBtn.innerHTML = '<i class="ti ti-loader ti-spin"></i> Submitting...';
            confirmBtn.disabled = true;
        }
        form.submit();
    }
}

// ============================================
// WITHDRAW MODAL
// ============================================
function showWithdrawModal(applicationId) {
    const modal = document.getElementById('withdrawModal');
    const form = document.getElementById('withdrawForm');
    if (modal && form) {
        form.action = form.action.replace('/0/', `/${applicationId}/`);
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function closeWithdrawModal() {
    document.getElementById('withdrawModal').style.display = 'none';
    document.body.style.overflow = '';
}

// ============================================
// SUCCESS MODAL
// ============================================
function checkForSuccess() {
    const urlParams = new URLSearchParams(window.location.search);
    const showSuccess = urlParams.get('success');
    
    if (showSuccess === 'true') {
        setTimeout(() => {
            const refElement = document.getElementById('refNumber');
            const refNumber = refElement ? refElement.textContent : null;
            
            if (refNumber) {
                const refElement = document.getElementById('refNumber');
                if (refElement) {
                    refElement.textContent = refNumber;
                }
            }
            
            const dateElement = document.getElementById('submissionDate');
            if (dateElement) {
                const now = new Date();
                const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
                dateElement.textContent = now.toLocaleDateString('en-US', options);
            }
            
            const modal = document.getElementById('successModal');
            if (modal) {
                modal.style.display = 'flex';
                document.body.style.overflow = 'hidden';
                showConfetti();
                
                setTimeout(() => {
                    closeSuccessModal();
                }, 10000);
            }
            
            if (window.history && window.history.pushState) {
                const newUrl = window.location.pathname + window.location.search.replace(/[?&]success=true/, '');
                window.history.pushState({}, '', newUrl);
            }
        }, 500);
    }
}

function closeSuccessModal() {
    const modal = document.getElementById('successModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// ============================================
// CONFETTI ANIMATION
// ============================================
function showConfetti() {
    const colors = ['#ef4444', '#22c55e', '#3b82f6', '#f97316', '#8b5cf6', '#ec4899', '#14b8a6', '#eab308'];
    
    const container = document.createElement('div');
    container.className = 'confetti-container';
    document.body.appendChild(container);
    
    for (let i = 0; i < 150; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'confetti';
        confetti.style.left = Math.random() * 100 + '%';
        confetti.style.width = (Math.random() * 8 + 4) + 'px';
        confetti.style.height = (Math.random() * 8 + 4) + 'px';
        confetti.style.background = colors[Math.floor(Math.random() * colors.length)];
        confetti.style.borderRadius = Math.random() > 0.5 ? '50%' : '2px';
        confetti.style.animationDuration = (Math.random() * 2 + 2) + 's';
        confetti.style.animationDelay = (Math.random() * 2) + 's';
        container.appendChild(confetti);
    }
    
    setTimeout(() => {
        if (container.parentElement) {
            container.remove();
        }
    }, 5000);
}

// ============================================
// TOAST NOTIFICATION
// ============================================
function showToast(message, type = 'success') {
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) {
        existingToast.remove();
    }
    
    const toast = document.createElement('div');
    toast.className = `toast-notification ${type}`;
    const iconMap = {
        'success': 'ti-check-circle',
        'error': 'ti-alert-circle',
        'warning': 'ti-alert-triangle',
        'info': 'ti-info-circle'
    };
    toast.innerHTML = `
        <div class="toast-icon">
            <i class="ti ${iconMap[type] || 'ti-info-circle'}"></i>
        </div>
        <div class="toast-content">
            <div class="toast-title">${type === 'success' ? 'Success!' : type === 'error' ? 'Error!' : type === 'warning' ? 'Warning!' : 'Info'}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.closest('.toast-notification').remove()">
            <i class="ti ti-x"></i>
        </button>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
}

function closeToast() {
    const toast = document.querySelector('.toast-notification');
    if (toast) {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }
}

// ============================================
// FLOATING NOTIFICATION
// ============================================
function showFloatingNotification() {
    const notification = document.getElementById('floatingNotification');
    if (notification) {
        notification.style.display = 'flex';
        notification.style.animation = 'slideUpFade 0.5s ease';
        
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(20px)';
            notification.style.transition = 'all 0.3s ease';
            setTimeout(() => {
                notification.style.display = 'none';
                notification.style.opacity = '1';
                notification.style.transform = 'translateY(0)';
            }, 300);
        }, 6000);
    }
}

// ============================================
// CLOSE MODALS ON OVERLAY CLICK
// ============================================
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.style.display = 'none';
        document.body.style.overflow = '';
    }
});

// ============================================
// CLOSE MODALS ON ESCAPE KEY
// ============================================
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeConfirmModal();
        closeWithdrawModal();
        closeSuccessModal();
        document.querySelectorAll('.modal-overlay').forEach(modal => {
            if (modal.style.display === 'flex') {
                modal.style.display = 'none';
                document.body.style.overflow = '';
            }
        });
    }
});

// ============================================
// EXPOSE GLOBAL FUNCTIONS
// ============================================
window.goToStep = goToStep;
window.nextStep = nextStep;
window.prevStep = prevStep;
window.updateReview = updateReview;
window.removeFile = removeFile;
window.showConfirmModal = showConfirmModal;
window.closeConfirmModal = closeConfirmModal;
window.submitApplication = submitApplication;
window.showWithdrawModal = showWithdrawModal;
window.closeWithdrawModal = closeWithdrawModal;
window.closeSuccessModal = closeSuccessModal;
window.showToast = showToast;
window.closeToast = closeToast;
window.showFloatingNotification = showFloatingNotification;
window.currentStep = currentStep;