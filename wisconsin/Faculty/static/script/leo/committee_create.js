
(function () {
    'use strict';

    // Live preview update
    const studentSelect = document.getElementById('id_phd_student');
    const dateInput = document.getElementById('id_formation_date');
    const statusSelect = document.getElementById('id_approval_status');

    const previewEmpty = document.getElementById('previewEmpty');
    const previewDetails = document.getElementById('previewDetails');
    const previewStudent = document.getElementById('previewStudent');
    const previewDate = document.getElementById('previewDate');
    const previewStatus = document.getElementById('previewStatus');
    const previewMembers = document.getElementById('previewMembers');

    function updatePreview() {
        const studentOption = studentSelect.options[studentSelect.selectedIndex];
        const studentName = studentOption ? studentOption.text : '';

        if (studentOption && studentOption.value) {
            previewEmpty.style.display = 'none';
            previewDetails.style.display = 'block';

            previewStudent.textContent = studentName || '—';
        } else {
            previewEmpty.style.display = 'block';
            previewDetails.style.display = 'none';
            return;
        }

        // Date
        if (dateInput.value) {
            const date = new Date(dateInput.value);
            previewDate.textContent = date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } else {
            previewDate.textContent = '—';
        }

        // Status
        const statusVal = statusSelect.value;
        let statusHTML = '';
        if (statusVal === 'PENDING') {
            statusHTML = '<span class="status-badge-preview bg-pending">Pending</span>';
        } else if (statusVal === 'APPROVED') {
            statusHTML = '<span class="status-badge-preview bg-approved">Approved</span>';
        } else if (statusVal === 'REJECTED') {
            statusHTML = '<span class="status-badge-preview bg-rejected">Rejected</span>';
        } else {
            statusHTML = '<span class="status-badge-preview bg-pending">Pending</span>';
        }
        previewStatus.innerHTML = statusHTML;

        // Members - always "Not Selected" for new committee
        previewMembers.textContent = 'Not Selected';
        previewMembers.className = 'preview-value text-muted';
    }

    // Event listeners
    if (studentSelect) {
        studentSelect.addEventListener('change', updatePreview);
    }
    if (dateInput) {
        dateInput.addEventListener('change', updatePreview);
    }
    if (statusSelect) {
        statusSelect.addEventListener('change', updatePreview);
    }

    // Initial update
    if (document.readyState === 'complete') {
        updatePreview();
    } else {
        document.addEventListener('DOMContentLoaded', updatePreview);
    }

    // Form validation with Bootstrap
    const form = document.getElementById('committeeForm');
    if (form) {
        form.addEventListener('submit', function (event) {
            const inputs = form.querySelectorAll('.form-control, .form-select');
            let isValid = true;

            inputs.forEach(function (input) {
                if (input.hasAttribute('required')) {
                    if (!input.value || input.value.trim() === '') {
                        input.classList.add('is-invalid');
                        isValid = false;
                    } else {
                        input.classList.remove('is-invalid');
                    }
                }
            });

            if (!isValid) {
                event.preventDefault();
                event.stopPropagation();
                // Scroll to first error
                const firstError = form.querySelector('.is-invalid');
                if (firstError) {
                    firstError.focus();
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });

        // Clear validation state on input
        form.querySelectorAll('.form-control, .form-select').forEach(function (input) {
            input.addEventListener('input', function () {
                if (this.classList.contains('is-invalid') && this.value && this.value.trim() !== '') {
                    this.classList.remove('is-invalid');
                }
            });
            input.addEventListener('change', function () {
                if (this.classList.contains('is-invalid') && this.value && this.value.trim() !== '') {
                    this.classList.remove('is-invalid');
                }
            });
        });
    }

})();
