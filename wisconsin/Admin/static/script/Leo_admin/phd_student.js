const PhDStudentManager = {
    initialized: false,
    flatpickrInstances: {},
    choicesInstances: {},
    studentNames: {},
    createModal: null,
    editModal: null,
    activateModal: null,
    deactivateModal: null,
    tooltips: [],

    init: function () {
        if (this.initialized) {
            return;
        }

        this.initialized = true;
        this.initializeStudentNames();
        this.initializeChoices();
        this.initializeFlatpickr();
        this.initializeTooltips();
        this.initializeCreateModal();
        this.initializeCreateStudentButtons();
        this.initializeEditModal();
        this.initializeActivateModal();
        this.initializeDeactivateModal();
        this.initializeViewButtons();
        this.initializeSearch();
        this.initializeFormSubmissions();
        this.initializeResetButton();
    },

    initializeStudentNames: function () {
        document.querySelectorAll('tbody tr').forEach(function (row) {
            const nameCell = row.querySelector('.fw-semibold');

            if (nameCell) {
                const editBtn = row.querySelector('.edit-btn');

                if (editBtn) {
                    const id = editBtn.dataset.id;

                    if (id) {
                        this.studentNames[id] = nameCell.textContent.trim();
                    }
                }
            }
        }.bind(this));
    },

    initializeChoices: function () {
        const selects = document.querySelectorAll('.choices-select');

        selects.forEach(function (el) {
            if (!el.dataset.choicesInitialized) {
                if (typeof Choices !== 'undefined') {
                    this.choicesInstances[el.id] = new Choices(el, {
                        searchEnabled: true,
                        shouldSort: false,
                        itemSelectText: '',
                        renderSelectedChoices: 'always'
                    });

                    el.dataset.choicesInitialized = 'true';
                }
            }
        }.bind(this));
    },

    reinitializeChoices: function (container) {
        const selects = container.querySelectorAll('.choices-select');

        selects.forEach(function (el) {
            if (!el.dataset.choicesInitialized) {
                if (typeof Choices !== 'undefined') {
                    this.choicesInstances[el.id] = new Choices(el, {
                        searchEnabled: true,
                        shouldSort: false,
                        itemSelectText: '',
                        renderSelectedChoices: 'always'
                    });

                    el.dataset.choicesInitialized = 'true';
                }
            }
        }.bind(this));
    },

    destroyChoices: function (container) {
        const selects = container.querySelectorAll('.choices-select');

        selects.forEach(function (el) {
            if (el.dataset.choicesInitialized) {
                if (this.choicesInstances[el.id]) {
                    this.choicesInstances[el.id].destroy();
                    delete this.choicesInstances[el.id];
                }

                el.dataset.choicesInitialized = 'false';
            }
        }.bind(this));
    },

    initializeFlatpickr: function () {
        const dateInputs = document.querySelectorAll('.flatpickr-date');

        dateInputs.forEach(function (el) {
            this.createFlatpickrInstance(el);
        }.bind(this));
    },

    createFlatpickrInstance: function (el) {
        if (el._flatpickr) {
            el._flatpickr.destroy();
            delete el._flatpickr;
        }

        const isAdmissionDate =
            el.id === "admissionDate" ||
            el.id === "id_admission_date" ||
            el.name === "admission_date";

        const isGraduationDate =
            el.id === "expectedGraduationDate" ||
            el.id === "id_expected_graduation_date" ||
            el.name === "expected_graduation_date";

        const config = {
            dateFormat: "Y-m-d",
            allowInput: false,
            disableMobile: true,
            clickOpens: true,
            animate: true,
            static: false,
            position: "below",
            positionElement: el,

            onChange: function (selectedDates, dateStr) {
                const event = new Event("change", {
                    bubbles: true
                });

                el.dispatchEvent(event);

                if (isAdmissionDate) {
                    const form = el.closest("form");

                    if (form) {
                        const cohortYear = form.querySelector(
                            "#id_cohort_year, #cohortYear"
                        );

                        if (cohortYear && dateStr) {
                            cohortYear.value = dateStr.split("-")[0];
                        }
                    }
                }
            }
        };

        if (isAdmissionDate) {
            config.maxDate = "today";

            const modal = el.closest(".modal");

            if (modal) {
                config.appendTo = modal;
            }
        }

        if (isGraduationDate) {
            config.minDate = "today";

            const modal = el.closest(".modal");

            if (modal) {
                config.appendTo = modal;
            }
        }

        const instance = flatpickr(el, config);

        el._flatpickr = instance;

        return instance;
    },

    reinitializeFlatpickr: function (container) {
        const dateInputs = container.querySelectorAll('.flatpickr-date');

        dateInputs.forEach(function (el) {
            this.createFlatpickrInstance(el);
        }.bind(this));
    },

    destroyFlatpickr: function (container) {
        const dateInputs = container.querySelectorAll('.flatpickr-date');

        dateInputs.forEach(function (el) {
            if (el._flatpickr) {
                el._flatpickr.destroy();
                delete el._flatpickr;
            }
        });
    },

    initializeTooltips: function () {
        this.tooltips = [];

        const tooltipTriggerList = [].slice.call(
            document.querySelectorAll('[data-bs-toggle="tooltip"]')
        );

        tooltipTriggerList.forEach(function (el) {
            this.tooltips.push(new bootstrap.Tooltip(el));
        }.bind(this));
    },

    destroyTooltips: function () {
        this.tooltips.forEach(function (tooltip) {
            tooltip.dispose();
        });

        this.tooltips = [];
    },

    initializeCreateModal: function () {
        const modalEl = document.getElementById('createModal');

        if (!modalEl) {
            return;
        }

        this.createModal = new bootstrap.Modal(modalEl);

        modalEl.addEventListener('shown.bs.modal', function () {
            this.reinitializeChoices(modalEl);
            this.reinitializeFlatpickr(modalEl);

            const input = modalEl.querySelector(
                'input:not([type="hidden"]):not([disabled]), select:not([disabled]), textarea:not([disabled])'
            );

            if (input) {
                setTimeout(function () {
                    input.focus();
                }, 100);
            }
        }.bind(this));

        modalEl.addEventListener('hidden.bs.modal', function () {
            this.destroyFlatpickr(modalEl);
            this.destroyChoices(modalEl);
        }.bind(this));
    },

    initializeCreateStudentButtons: function () {
        const createButtons = document.querySelectorAll(
            '.create-phd-student-btn'
        );

        createButtons.forEach(function (button) {
            button.addEventListener('click', function (event) {
                event.preventDefault();

                const pageContainer = document.querySelector(
                    '[data-has-active-phd-program]'
                );

                const hasActiveProgram =
                    pageContainer?.dataset.hasActivePhdProgram === 'true';

                if (!hasActiveProgram) {
                    if (typeof Swal === 'undefined') {
                        alert(
                            'No active PhD program is available. Please create a PhD program before adding a PhD student.'
                        );

                        return;
                    }

                    Swal.fire({
                        icon: 'warning',
                        title: 'PhD Program Required',
                        text: 'No active PhD program is available. Please create a PhD program before adding a PhD student.',
                        confirmButtonText: 'Create PhD Program',
                        confirmButtonColor: '#C5050C',
                        showCloseButton: true,
                        allowOutsideClick: false
                    }).then(function (result) {
                        if (result.isConfirmed) {
                            window.location.href = '/dashboard/phd-program/';
                        }
                    });
                    return;
                }

                if (this.createModal) {
                    this.createModal.show();
                }
            }.bind(this));
        }.bind(this));
    },

    initializeEditModal: function () {
        const modalEl = document.getElementById('editModal');

        if (!modalEl) {
            return;
        }

        this.editModal = new bootstrap.Modal(modalEl);

        const editForm = document.getElementById('editForm');

        modalEl.addEventListener('shown.bs.modal', function () {
            this.reinitializeChoices(modalEl);
            this.reinitializeFlatpickr(modalEl);

            const input = modalEl.querySelector(
                'input:not([type="hidden"]):not([disabled]), select:not([disabled]), textarea:not([disabled])'
            );

            if (input) {
                setTimeout(function () {
                    input.focus();
                }, 100);
            }
        }.bind(this));

        modalEl.addEventListener('hidden.bs.modal', function () {
            this.destroyFlatpickr(modalEl);
            this.destroyChoices(modalEl);

            const container = document.getElementById(
                'editFormContainer'
            );

            if (container) {
                container.innerHTML =
                    '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2 text-muted">Loading student data...</p></div>';
            }
        }.bind(this));

        document.querySelectorAll('.edit-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                const id = this.dataset.id;
                const baseUrl = '/dashboard/phd-student/update/';
                const updateUrl = baseUrl + id + '/';

                editForm.action = updateUrl;

                const container = document.getElementById(
                    'editFormContainer'
                );

                container.innerHTML =
                    '<div class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2 text-muted">Loading student data...</p></div>';

                this.editModal.show();

                fetch(updateUrl + '?ajax=1')
                    .then(function (response) {
                        if (!response.ok) {
                            throw new Error(
                                'Network response was not ok (Status: ' +
                                response.status +
                                ')'
                            );
                        }

                        return response.json();
                    })
                    .then(function (data) {
                        if (data.form) {
                            container.innerHTML = data.form;

                            this.reinitializeChoices(container);
                            this.reinitializeFlatpickr(container);
                        } else {
                            container.innerHTML =
                                '<div class="alert alert-danger"><i class="bi bi-exclamation-triangle me-2"></i>Failed to load student data. Please try again.</div>';
                        }
                    }.bind(this))
                    .catch(function (error) {
                        console.error('Error:', error);

                        container.innerHTML =
                            '<div class="alert alert-danger"><i class="bi bi-exclamation-triangle me-2"></i>Error loading student data: ' +
                            error.message +
                            '</div>';
                    });
            }.bind(this));
        }.bind(this));
    },

    initializeActivateModal: function () {
        const modalEl = document.getElementById('activateModal');

        if (!modalEl) {
            return;
        }

        this.activateModal = new bootstrap.Modal(modalEl);

        const form = document.getElementById('activateForm');

        document.querySelectorAll('.activate-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                const id = this.dataset.id;
                const studentName =
                    this.studentNames[id] || 'Student';

                form.action =
                    '/dashboard/phd-student/activate/' +
                    id +
                    '/';

                document.getElementById(
                    'activateStudentName'
                ).textContent = studentName;

                this.activateModal.show();
            }.bind(this));
        }.bind(this));
    },

    initializeDeactivateModal: function () {
        const modalEl = document.getElementById('deactivateModal');

        if (!modalEl) {
            return;
        }

        this.deactivateModal = new bootstrap.Modal(modalEl);

        const form = document.getElementById('deactivateForm');

        document.querySelectorAll('.deactivate-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                const id = this.dataset.id;
                const studentName =
                    this.studentNames[id] || 'Student';

                form.action =
                    '/dashboard/phd-student/deactivate/' +
                    id +
                    '/';

                document.getElementById(
                    'deactivateStudentName'
                ).textContent = studentName;

                this.deactivateModal.show();
            }.bind(this));
        }.bind(this));
    },

    initializeViewButtons: function () {
        document.querySelectorAll('.view-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                const id = this.dataset.id;
                const studentName =
                    this.studentNames[id] || 'Student';

                alert(
                    'Viewing details for: ' +
                    studentName +
                    '\nStudent ID: ' +
                    id +
                    '\n\nDetailed view coming soon!'
                );
            });
        });
    },

    initializeSearch: function () {
        const searchInput = document.getElementById('search');

        if (searchInput) {
            searchInput.addEventListener('keypress', function (e) {
                if (e.key === 'Enter') {
                    e.preventDefault();

                    document.getElementById(
                        'filterForm'
                    ).submit();
                }
            });
        }
    },

    initializeFormSubmissions: function () {
        document.querySelectorAll('form').forEach(function (form) {
            form.addEventListener('submit', function (e) {
                const submitBtn = this.querySelector(
                    'button[type="submit"]'
                );

                if (submitBtn && !submitBtn.disabled) {
                    submitBtn.disabled = true;

                    submitBtn.innerHTML =
                        '<span class="spinner-border spinner-border-sm me-1"></span> Processing...';
                }
            });
        });
    },

    initializeResetButton: function () {
        const resetBtn = document.querySelector(
            'a[href="/dashboard/phd-student/"]'
        );

        if (resetBtn) {
            resetBtn.addEventListener('click', function (e) {
                e.preventDefault();

                window.location.href = this.href;
            });
        }
    },

    destroy: function () {
        this.destroyTooltips();
        this.destroyFlatpickr(document);
        this.destroyChoices(document);

        if (this.createModal) {
            this.createModal.dispose();
            this.createModal = null;
        }

        if (this.editModal) {
            this.editModal.dispose();
            this.editModal = null;
        }

        if (this.activateModal) {
            this.activateModal.dispose();
            this.activateModal = null;
        }

        if (this.deactivateModal) {
            this.deactivateModal.dispose();
            this.deactivateModal = null;
        }

        this.initialized = false;
    }
};

document.addEventListener('DOMContentLoaded', function () {
    PhDStudentManager.init();
});

document.addEventListener('turbolinks:before-cache', function () {
    PhDStudentManager.destroy();
});

document.addEventListener('turbolinks:load', function () {
    PhDStudentManager.init();
});

