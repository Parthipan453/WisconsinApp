(function () {
  "use strict";

  const DOM = {
    modal: document.getElementById("phdProgramModal"),
    modalTitle: document.getElementById("modalTitle"),
    modalIcon: document.getElementById("modalIcon"),
    form: document.getElementById("phdProgramForm"),
    programId: document.getElementById("programId"),
    programName: document.getElementById("programName"),
    department: document.getElementById("department"),
    creditsRequired: document.getElementById("creditsRequired"),
    residencyRequirement: document.getElementById("residencyRequirement"),
    durationYears: document.getElementById("durationYears"),
    programDescription: document.getElementById("programDescription"),
    status: document.getElementById("status"),
    saveButton: document.getElementById("saveProgramBtn"),
    saveButtonText: document.getElementById("saveProgramText"),
    saveButtonIcon: document.getElementById("saveIcon"),
    serverErrors: document.getElementById("serverFormErrors"),
    searchInput: document.getElementById("searchInput"),
    tableBody: document.getElementById("programTableBody"),
    programCount: document.getElementById("programCount"),
    deactivateModal: document.getElementById("deactivateModal"),
    deactivateProgramName: document.getElementById("deactivateProgramName"),
    confirmDeactivateBtn: document.getElementById("confirmDeactivateBtn"),
    viewProgramName: document.getElementById("viewProgramName"),
    viewDepartment: document.getElementById("viewDepartment"),
    viewDegreeType: document.getElementById("viewDegreeType"),
    viewCredits: document.getElementById("viewCredits"),
    viewResidency: document.getElementById("viewResidency"),
    viewDuration: document.getElementById("viewDuration"),
    viewDescription: document.getElementById("viewDescription"),
    viewStatus: document.getElementById("viewStatus"),
    printButton: document.getElementById("printBtn"),
    exportButton: document.getElementById("exportBtn"),
  };

  const STATE = {
    isEditMode: false,
    currentEditId: null,
    selectedDeactivateForm: null,
    searchTimer: null,
    modalInstance: null,
    deactivateModalInstance: null,
    choicesInstances: {},
  };

  const CONFIG = {
    createUrl: DOM.form ? DOM.form.action : "",
    updateUrl: DOM.form ? DOM.form.dataset.updateUrl : "",
    searchUrl: DOM.searchInput ? DOM.searchInput.dataset.url : "",
  };

  function safeSetValue(element, value) {
    if (!element) {
      return;
    }

    element.value = value === null || value === undefined ? "" : String(value);
  }

  function safeSetText(element, text) {
    if (!element) {
      return;
    }

    element.textContent =
      text === null || text === undefined ? "" : String(text);
  }

  function escapeHtml(value) {
    const div = document.createElement("div");

    div.textContent =
      value === null || value === undefined ? "" : String(value);

    return div.innerHTML;
  }

  function getChoicesInstance(element) {
    if (!element) {
      return null;
    }

    return STATE.choicesInstances[element.id] || null;
  }

  function setChoicesValue(element, value) {
    const instance = getChoicesInstance(element);

    if (!instance) {
      safeSetValue(element, value);
      return;
    }

    try {
      instance.removeActiveItems();

      if (value !== null && value !== undefined && String(value) !== "") {
        instance.setChoiceByValue(String(value));
      }
    } catch (error) {
      safeSetValue(element, value);
    }
  }

  function getFieldFeedback(input) {
    if (!input) {
      return null;
    }

    let feedback = input.nextElementSibling;

    if (feedback && feedback.classList.contains("choices")) {
      feedback = feedback.nextElementSibling;
    }

    if (feedback && feedback.classList.contains("invalid-feedback")) {
      return feedback;
    }

    return null;
  }

  function clearFieldValidation(input) {
    if (!input) {
      return;
    }

    input.classList.remove("is-valid", "is-invalid");

    const feedback = getFieldFeedback(input);

    if (feedback) {
      feedback.textContent = "";
    }

    const choicesWrapper = input.parentElement
      ? input.parentElement.querySelector(".choices")
      : null;

    if (choicesWrapper) {
      choicesWrapper.classList.remove("is-valid", "is-invalid");
    }
  }

  function showError(input, message) {
    if (!input) {
      return;
    }

    input.classList.remove("is-valid");
    input.classList.add("is-invalid");

    const choicesWrapper = input.parentElement
      ? input.parentElement.querySelector(".choices")
      : null;

    if (choicesWrapper) {
      choicesWrapper.classList.add("is-invalid");
    }

    let feedback = getFieldFeedback(input);

    if (!feedback) {
      feedback = document.createElement("div");
      feedback.className = "invalid-feedback";

      if (
        input.nextElementSibling &&
        input.nextElementSibling.classList.contains("choices")
      ) {
        input.nextElementSibling.insertAdjacentElement("afterend", feedback);
      } else {
        input.insertAdjacentElement("afterend", feedback);
      }
    }

    feedback.textContent = message || "Invalid value.";
  }

  function showSuccess(input) {
    if (!input) {
      return;
    }

    input.classList.remove("is-invalid");
    input.classList.add("is-valid");

    const choicesWrapper = input.parentElement
      ? input.parentElement.querySelector(".choices")
      : null;

    if (choicesWrapper) {
      choicesWrapper.classList.remove("is-invalid");
      choicesWrapper.classList.add("is-valid");
    }

    const feedback = getFieldFeedback(input);

    if (feedback) {
      feedback.textContent = "";
    }
  }

  function clearValidation() {
    [
      DOM.programName,
      DOM.department,
      DOM.creditsRequired,
      DOM.residencyRequirement,
      DOM.durationYears,
      DOM.programDescription,
      DOM.status,
    ].forEach(clearFieldValidation);
  }

  function validateProgramName() {
    if (!DOM.programName) {
      return false;
    }

    const value = DOM.programName.value.trim();

    if (!value) {
      showError(DOM.programName, "Program Name is required.");
      return false;
    }

    if (value.length < 3) {
      showError(DOM.programName, "Minimum 3 characters required.");
      return false;
    }

    if (value.length > 100) {
      showError(DOM.programName, "Maximum 100 characters allowed.");
      return false;
    }

    if (!/[A-Za-z]/.test(value)) {
      showError(
        DOM.programName,
        "Program Name must contain at least one alphabet.",
      );
      return false;
    }

    showSuccess(DOM.programName);
    return true;
  }

  function validateDepartment() {
    if (!DOM.department) {
      return false;
    }

    const value = DOM.department.value;

    if (!value) {
      showError(DOM.department, "Department is required.");
      return false;
    }

    showSuccess(DOM.department);
    return true;
  }

  function validateCreditsRequired() {
    if (!DOM.creditsRequired) {
      return false;
    }

    const value = DOM.creditsRequired.value.trim();

    if (!value) {
      showError(DOM.creditsRequired, "Total Credits Required is required.");
      return false;
    }

    const credits = Number(value);

    if (!Number.isInteger(credits) || credits < 1 || credits > 300) {
      showError(DOM.creditsRequired, "Credits must be between 1 and 300.");
      return false;
    }

    showSuccess(DOM.creditsRequired);
    return true;
  }

  function validateResidencyRequirement() {
    if (!DOM.residencyRequirement) {
      return false;
    }

    const value = DOM.residencyRequirement.value.trim();

    if (!value) {
      showError(DOM.residencyRequirement, "Residency Requirement is required.");
      return false;
    }

    if (!/^\d+$/.test(value)) {
      showError(
        DOM.residencyRequirement,
        "Residency Requirement should contain only numbers.",
      );
      return false;
    }

    const residency = Number(value);

    if (residency <= 0) {
      showError(
        DOM.residencyRequirement,
        "Residency Requirement must be greater than 0.",
      );
      return false;
    }

    showSuccess(DOM.residencyRequirement);
    return true;
  }

  function validateDurationYears() {
    if (!DOM.durationYears) {
      return false;
    }

    const value = DOM.durationYears.value.trim();

    if (!value) {
      showError(DOM.durationYears, "Duration is required.");
      return false;
    }

    const duration = Number(value);

    if (!Number.isInteger(duration) || duration < 1 || duration > 10) {
      showError(DOM.durationYears, "Duration must be between 1 and 10 years.");
      return false;
    }

    showSuccess(DOM.durationYears);
    return true;
  }

  function validateProgramDescription() {
    if (!DOM.programDescription) {
      return false;
    }

    const value = DOM.programDescription.value.trim();

    if (!value) {
      showError(DOM.programDescription, "Program Description is required.");
      return false;
    }

    if (value.length < 10) {
      showError(DOM.programDescription, "Minimum 10 characters required.");
      return false;
    }

    if (value.length > 1000) {
      showError(DOM.programDescription, "Maximum 1000 characters allowed.");
      return false;
    }

    if (!/^[A-Za-z0-9\s&().,'/-]+$/.test(value)) {
      showError(DOM.programDescription, "Invalid Program Description.");
      return false;
    }

    showSuccess(DOM.programDescription);
    return true;
  }

  function validateStatus() {
    if (!DOM.status) {
      return false;
    }

    const value = DOM.status.value;

    if (!value) {
      showError(DOM.status, "Status is required.");
      return false;
    }

    showSuccess(DOM.status);
    return true;
  }

  function validateForm() {
    return [
      validateProgramName(),
      validateDepartment(),
      validateCreditsRequired(),
      validateResidencyRequirement(),
      validateDurationYears(),
      validateProgramDescription(),
      validateStatus(),
    ].every(Boolean);
  }

  function resetForm() {
    if (!DOM.form) {
      return;
    }

    DOM.form.reset();

    safeSetValue(DOM.programId, "");

    clearValidation();

    setChoicesValue(DOM.department, "");

    setChoicesValue(DOM.status, "");
  }

  function setAddMode() {
    STATE.isEditMode = false;
    STATE.currentEditId = null;

    if (DOM.modalTitle) {
      DOM.modalTitle.textContent = "Add PhD Program";
    }

    if (DOM.modalIcon) {
      DOM.modalIcon.className = "ti ti-plus me-2";
    }

    if (DOM.saveButtonText) {
      DOM.saveButtonText.textContent = "Save Program";
    }

    if (DOM.saveButtonIcon) {
      DOM.saveButtonIcon.className = "ti ti-device-floppy";
    }

    if (DOM.form) {
      DOM.form.action = CONFIG.createUrl;
    }

    resetForm();
  }

  function setEditMode(button) {
    if (!button || !button.dataset) {
      return;
    }

    const id = button.dataset.id || "";

    if (!id) {
      return;
    }

    STATE.isEditMode = true;
    STATE.currentEditId = id;

    if (DOM.modalTitle) {
      DOM.modalTitle.textContent = "Edit PhD Program";
    }

    if (DOM.modalIcon) {
      DOM.modalIcon.className = "ti ti-edit me-2";
    }

    if (DOM.saveButtonText) {
      DOM.saveButtonText.textContent = "Update Program";
    }

    if (DOM.saveButtonIcon) {
      DOM.saveButtonIcon.className = "ti ti-device-floppy";
    }

    safeSetValue(DOM.programId, button.dataset.id);

    safeSetValue(DOM.programName, button.dataset.programName);

    setChoicesValue(DOM.department, button.dataset.department);

    safeSetValue(DOM.creditsRequired, button.dataset.credits);

    safeSetValue(DOM.residencyRequirement, button.dataset.residency);

    safeSetValue(DOM.durationYears, button.dataset.duration);

    safeSetValue(DOM.programDescription, button.dataset.description);

    setChoicesValue(DOM.status, button.dataset.status);

    clearValidation();

    if (DOM.form && CONFIG.updateUrl) {
      DOM.form.action = CONFIG.updateUrl.replace("/0/", `/${id}/`);
    }
  }

  function handleModalShow(event) {
    const sidebar = document.querySelector(".sidebar_nav");

    if (sidebar) {
      sidebar.style.overflowY = "hidden";
    }

    const relatedTarget = event.relatedTarget;

    if (!relatedTarget) {
      return;
    }

    if (relatedTarget.classList.contains("edit-program-btn")) {
      setEditMode(relatedTarget);
    } else if (relatedTarget.classList.contains("add-program-btn")) {
      setAddMode();
    }
  }

  function handleModalHidden() {
    const sidebar = document.querySelector(".sidebar_nav");

    if (sidebar) {
      sidebar.style.overflowY = "";
    }

    STATE.isEditMode = false;
    STATE.currentEditId = null;

    resetForm();

    if (DOM.form) {
      DOM.form.action = CONFIG.createUrl;
    }

    if (DOM.modalTitle) {
      DOM.modalTitle.textContent = "Add PhD Program";
    }

    if (DOM.modalIcon) {
      DOM.modalIcon.className = "ti ti-plus me-2";
    }

    if (DOM.saveButtonText) {
      DOM.saveButtonText.textContent = "Save Program";
    }

    if (DOM.saveButtonIcon) {
      DOM.saveButtonIcon.className = "ti ti-device-floppy";
    }

    if (DOM.saveButton) {
      DOM.saveButton.disabled = false;
    }
  }

  function handleFormSubmit(event) {
    if (!validateForm()) {
      event.preventDefault();
      return;
    }

    if (DOM.saveButton) {
      DOM.saveButton.disabled = true;
    }

    if (DOM.saveButtonText) {
      DOM.saveButtonText.textContent = STATE.isEditMode
        ? "Updating..."
        : "Saving...";
    }

    if (DOM.saveButtonIcon) {
      DOM.saveButtonIcon.className = "ti ti-loader-2";
    }
  }

  function handleServerErrors() {
    if (!DOM.serverErrors) {
      return;
    }

    try {
      const errors = JSON.parse(DOM.serverErrors.textContent);

      if (DOM.modal && STATE.modalInstance) {
        STATE.modalInstance.show();
      }

      const fieldMap = {
        program_name: DOM.programName,
        department: DOM.department,
        total_credits_required: DOM.creditsRequired,
        residency_requirement: DOM.residencyRequirement,
        duration_years: DOM.durationYears,
        program_description: DOM.programDescription,
        status: DOM.status,
      };

      Object.keys(fieldMap).forEach((fieldName) => {
        const input = fieldMap[fieldName];

        if (input && errors[fieldName] && errors[fieldName].length) {
          showError(input, errors[fieldName][0].message);
        }
      });

      if (errors.__all__ && errors.__all__.length) {
        showToast("error", errors.__all__[0].message);
      }
    } catch (error) {
      showToast("error", "Unable to load form errors.");
    }
  }

  function buildProgramDetailsAttributes(program) {
    return `
            data-program-name="${escapeHtml(program.program_name || "")}"
            data-department="${escapeHtml(program.department || "")}"
            data-degree="${escapeHtml(program.degree_type || "")}"
            data-credits="${escapeHtml(program.total_credits_required || "")}"
            data-residency="${escapeHtml(program.residency_requirement || "")}"
            data-duration="${escapeHtml(program.duration_years || "")}"
            data-status="${escapeHtml(program.status || "")}"
            data-description="${escapeHtml(program.program_description || "")}"
        `;
  }

  function buildEditAttributes(program, isActive) {
    return `
            data-id="${escapeHtml(program.phd_program_id || "")}"
            data-program-name="${escapeHtml(program.program_name || "")}"
            data-department="${escapeHtml(program.department_id || "")}"
            data-degree-type="${escapeHtml(program.degree_type || "")}"
            data-credits="${escapeHtml(program.total_credits_required || "")}"
            data-residency="${escapeHtml(program.residency_requirement || "")}"
            data-duration="${escapeHtml(program.duration_years || "")}"
            data-description="${escapeHtml(program.program_description || "")}"
            data-status="${escapeHtml(program.status || "")}"
            ${
              !isActive
                ? 'disabled title="Inactive records cannot be edited"'
                : ""
            }
        `;
  }

  function renderProgramCards(results) {
    if (!DOM.tableBody) {
      return;
    }

    if (!results || results.length === 0) {
      DOM.tableBody.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <i class="ti ti-school"></i>
                    </div>

                    <h5>No PhD Programs Found</h5>

                    <p>
                        Start by creating your first PhD Program.
                    </p>

                    <button
                        type="button"
                        class="btn btn-primary add-program-btn"
                        data-bs-toggle="modal"
                        data-bs-target="#phdProgramModal"
                    >
                        <i class="ti ti-plus"></i>
                        Add Program
                    </button>
                </div>
            `;

      updateProgramCount(0);
      return;
    }

    let cards = "";

    results.forEach((program) => {
      const isActive = program.status === "ACTIVE";

      const programName = escapeHtml(program.program_name || "");

      const department = escapeHtml(program.department || "");

      const degreeType = escapeHtml(program.degree_type || "");

      const credits = escapeHtml(program.total_credits_required || "");

      const residency = escapeHtml(program.residency_requirement || "");

      const duration = escapeHtml(program.duration_years || "");

      const detailsAttributes = buildProgramDetailsAttributes(program);

      const editAttributes = buildEditAttributes(program, isActive);

      cards += `
                <article class="program-card">

                    <div class="program-card-top">

                        <div class="program-icon">
                            <i class="ti ti-school"></i>
                        </div>

                        <div class="program-card-actions">

                            <button
                                type="button"
                                class="program-action edit-program-btn"
                                data-bs-toggle="modal"
                                data-bs-target="#phdProgramModal"
                                ${editAttributes}
                            >
                                <i class="ti ti-edit"></i>
                            </button>

                            ${
                              isActive
                                ? `
                                        <form
                                            method="POST"
                                            action="${escapeHtml(
                                              program.deactivate_url || "",
                                            )}"
                                            class="deactivate-form"
                                            data-program-id="${escapeHtml(
                                              program.phd_program_id || "",
                                            )}"
                                        >

                                            <input
                                                type="hidden"
                                                name="csrfmiddlewaretoken"
                                                value="${escapeHtml(
                                                  getCsrfToken(),
                                                )}"
                                            >

                                            <button
                                                type="button"
                                                class="program-action danger deactivate-btn"
                                                data-program-name="${programName}"
                                            >
                                                <i class="ti ti-ban"></i>
                                            </button>

                                        </form>
                                    `
                                : `
                                        <form
                                            method="POST"
                                            action="${escapeHtml(
                                              program.activate_url || "",
                                            )}"
                                            class="activate-form"
                                            data-program-id="${escapeHtml(
                                              program.phd_program_id || "",
                                            )}"
                                        >

                                            <input
                                                type="hidden"
                                                name="csrfmiddlewaretoken"
                                                value="${escapeHtml(
                                                  getCsrfToken(),
                                                )}"
                                            >

                                            <button
                                                type="button"
                                                class="program-action success activate-btn"
                                                data-program-name="${programName}"
                                            >
                                                <i class="ti ti-check"></i>
                                            </button>

                                        </form>
                                    `
                            }

                        </div>

                    </div>

                    <div class="program-card-body">

                        <div class="program-card-title-row">

                            <a
                                href="javascript:void(0)"
                                class="program-details-link"
                                data-bs-toggle="modal"
                                data-bs-target="#programDetailsModal"
                                ${detailsAttributes}
                            >
                                ${programName}
                            </a>

                            ${
                              isActive
                                ? `
                                        <span class="status-badge active">
                                            <span></span>
                                            Active
                                        </span>
                                    `
                                : `
                                        <span class="status-badge inactive">
                                            <span></span>
                                            Inactive
                                        </span>
                                    `
                            }

                        </div>

                        <div class="program-department">
                            <i class="ti ti-building-community"></i>
                            <span>${department}</span>
                        </div>

                        <div class="program-meta-grid">

                            <div class="program-meta-item">

                                <div class="meta-icon degree">
                                    <i class="ti ti-school"></i>
                                </div>

                                <div>
                                    <span>Degree Type</span>
                                    <strong>${degreeType}</strong>
                                </div>

                            </div>

                            <div class="program-meta-item">

                                <div class="meta-icon credits">
                                    <i class="ti ti-books"></i>
                                </div>

                                <div>
                                    <span>Credits</span>
                                    <strong>${credits}</strong>
                                </div>

                            </div>

                            <div class="program-meta-item">

                                <div class="meta-icon duration">
                                    <i class="ti ti-calendar-time"></i>
                                </div>

                                <div>
                                    <span>Duration</span>
                                    <strong>${duration} Years</strong>
                                </div>

                            </div>

                            <div class="program-meta-item">

                                <div class="meta-icon residency">
                                    <i class="ti ti-map-pin"></i>
                                </div>

                                <div>
                                    <span>Residency</span>
                                    <strong>${residency}</strong>
                                </div>

                            </div>

                        </div>

                        <button
                            type="button"
                            class="view-program-btn program-details-link"
                            data-bs-toggle="modal"
                            data-bs-target="#programDetailsModal"
                            ${detailsAttributes}
                        >
                            View Program Details
                            <i class="ti ti-arrow-right"></i>
                        </button>

                    </div>

                </article>
            `;
    });

    DOM.tableBody.innerHTML = cards;

    updateProgramCount(results.length);
    initializeDynamicTooltips();
  }

  function updateProgramCount(count) {
    if (!DOM.programCount) {
      return;
    }

    DOM.programCount.textContent = String(count);
  }

  function initializeDynamicTooltips() {
    if (
      typeof bootstrap === "undefined" ||
      !bootstrap.Tooltip ||
      !DOM.tableBody
    ) {
      return;
    }

    const elements = DOM.tableBody.querySelectorAll(
      '[title="Inactive records cannot be edited"]',
    );

    elements.forEach((element) => {
      bootstrap.Tooltip.getOrCreateInstance(element);
    });
  }

  function handleProgramDetailsClick(element) {
    if (!element || !element.dataset) {
      return;
    }

    safeSetText(DOM.viewProgramName, element.dataset.programName || "-");

    safeSetText(DOM.viewDepartment, element.dataset.department || "-");

    safeSetText(DOM.viewDegreeType, element.dataset.degree || "-");

    safeSetText(DOM.viewCredits, element.dataset.credits || "-");

    safeSetText(DOM.viewResidency, element.dataset.residency || "-");

    safeSetText(
      DOM.viewDuration,
      element.dataset.duration ? `${element.dataset.duration} Years` : "-",
    );

    safeSetText(DOM.viewDescription, element.dataset.description || "-");

    if (DOM.viewStatus) {
      const status = element.dataset.status || "";

      if (status === "ACTIVE") {
        DOM.viewStatus.innerHTML =
          '<span class="badge bg-success">Active</span>';
      } else {
        DOM.viewStatus.innerHTML =
          '<span class="badge bg-danger">Inactive</span>';
      }
    }
  }

  function handleDeactivateClick(button) {
    if (!button) {
      return;
    }

    const form = button.closest(".deactivate-form");

    if (!form) {
      return;
    }

    STATE.selectedDeactivateForm = form;

    safeSetText(DOM.deactivateProgramName, button.dataset.programName || "");

    if (DOM.deactivateModal) {
      STATE.deactivateModalInstance = bootstrap.Modal.getOrCreateInstance(
        DOM.deactivateModal,
      );

      STATE.deactivateModalInstance.show();
    }
  }

  async function handleActivateClick(button) {
    if (!button) {
      return;
    }

    const form = button.closest(".activate-form");

    if (!form) {
      return;
    }

    button.disabled = true;

    try {
      const response = await fetch(form.action, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCsrfToken(),
          "X-Requested-With": "XMLHttpRequest",
        },
      });

      const data = await parseJsonResponse(response);

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Unable to activate the program.");
      }

      showToast("success", data.message || "Program activated successfully.");

      await refreshProgramList();
    } catch (error) {
      showToast(
        "error",
        error.message || "An error occurred while activating the program.",
      );
    } finally {
      button.disabled = false;
    }
  }

  async function handleConfirmDeactivate() {
    if (!STATE.selectedDeactivateForm) {
      return;
    }

    const form = STATE.selectedDeactivateForm;

    if (DOM.confirmDeactivateBtn) {
      DOM.confirmDeactivateBtn.disabled = true;
    }

    try {
      const response = await fetch(form.action, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCsrfToken(),
          "X-Requested-With": "XMLHttpRequest",
        },
      });

      const data = await parseJsonResponse(response);

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Unable to deactivate the program.");
      }

      if (STATE.deactivateModalInstance) {
        STATE.deactivateModalInstance.hide();
      }

      showToast("success", data.message || "Program deactivated successfully.");

      STATE.selectedDeactivateForm = null;

      await refreshProgramList();
    } catch (error) {
      showToast(
        "error",
        error.message || "An error occurred while deactivating the program.",
      );
    } finally {
      if (DOM.confirmDeactivateBtn) {
        DOM.confirmDeactivateBtn.disabled = false;
      }
    }
  }

  async function parseJsonResponse(response) {
    const contentType = response.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
      return await response.json();
    }

    const text = await response.text();

    return {
      success: false,
      message: text || "Unexpected server response.",
    };
  }

  function getCsrfToken() {
    const csrfInput = document.querySelector("[name=csrfmiddlewaretoken]");

    if (csrfInput) {
      return csrfInput.value;
    }

    const meta = document.querySelector('meta[name="csrf-token"]');

    return meta ? meta.getAttribute("content") : "";
  }

  async function performSearch(searchTerm, page) {
    if (!CONFIG.searchUrl || !DOM.tableBody) {
      return;
    }

    const params = new URLSearchParams(window.location.search);

    const currentPage = page || params.get("page") || "1";

    const sort = params.get("sort") || "program_name";

    const order = params.get("order") || "desc";

    const url = `${CONFIG.searchUrl}?search=${encodeURIComponent(
      searchTerm || "",
    )}&page=${encodeURIComponent(currentPage)}&sort=${encodeURIComponent(
      sort,
    )}&order=${encodeURIComponent(order)}`;

    try {
      DOM.tableBody.classList.add("loading");

      const response = await fetch(url, {
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      });

      if (!response.ok) {
        throw new Error("Unable to load programs.");
      }

      const data = await response.json();

      renderProgramCards(data.results || []);
    } catch (error) {
      showToast("error", "An error occurred while searching.");
    } finally {
      DOM.tableBody.classList.remove("loading");
    }
  }

  async function refreshProgramList() {
    const searchTerm = DOM.searchInput ? DOM.searchInput.value : "";

    await performSearch(searchTerm, 1);
  }

  function handleSearchInput() {
    if (!DOM.searchInput) {
      return;
    }

    clearTimeout(STATE.searchTimer);

    STATE.searchTimer = setTimeout(() => {
      performSearch(DOM.searchInput.value, 1);
    }, 300);
  }

  function handleProgramGridClick(event) {
    const detailsLink = event.target.closest(".program-details-link");

    if (detailsLink) {
      handleProgramDetailsClick(detailsLink);
      return;
    }

    const editButton = event.target.closest(".edit-program-btn");

    if (editButton) {
      if (editButton.disabled || editButton.hasAttribute("disabled")) {
        return;
      }

      setEditMode(editButton);
      return;
    }

    const deactivateButton = event.target.closest(".deactivate-btn");

    if (deactivateButton) {
      handleDeactivateClick(deactivateButton);
      return;
    }

    const activateButton = event.target.closest(".activate-btn");

    if (activateButton) {
      handleActivateClick(activateButton);
    }
  }

  function initializeChoices() {
    if (typeof Choices === "undefined") {
      return;
    }

    const selectElements = document.querySelectorAll(".choices-select");

    selectElements.forEach((element) => {
      if (STATE.choicesInstances[element.id]) {
        return;
      }

      try {
        STATE.choicesInstances[element.id] = new Choices(element, {
          searchEnabled: false,
          itemSelectText: "",
          shouldSort: false,
          allowHTML: false,
          shouldSortItems: false,
          removeItemButton: false,
        });
      } catch (error) {
        STATE.choicesInstances[element.id] = null;
      }
    });
  }

  function initializeModal() {
    if (!DOM.modal || typeof bootstrap === "undefined") {
      return;
    }

    STATE.modalInstance = bootstrap.Modal.getOrCreateInstance(DOM.modal);

    DOM.modal.addEventListener("show.bs.modal", handleModalShow);

    DOM.modal.addEventListener("hidden.bs.modal", handleModalHidden);
  }

  function initializeEventListeners() {
    if (DOM.form) {
      DOM.form.addEventListener("submit", handleFormSubmit);
    }

    if (DOM.tableBody) {
      DOM.tableBody.addEventListener("click", handleProgramGridClick);
    }

    if (DOM.searchInput) {
      DOM.searchInput.addEventListener("input", handleSearchInput);
    }

    if (DOM.confirmDeactivateBtn) {
      DOM.confirmDeactivateBtn.addEventListener(
        "click",
        handleConfirmDeactivate,
      );
    }

    if (DOM.programName) {
      DOM.programName.addEventListener("input", validateProgramName);

      DOM.programName.addEventListener("blur", validateProgramName);
    }

    if (DOM.department) {
      DOM.department.addEventListener("change", validateDepartment);
    }

    if (DOM.creditsRequired) {
      DOM.creditsRequired.addEventListener("input", validateCreditsRequired);

      DOM.creditsRequired.addEventListener("blur", validateCreditsRequired);
    }

    if (DOM.residencyRequirement) {
      DOM.residencyRequirement.addEventListener(
        "input",
        validateResidencyRequirement,
      );

      DOM.residencyRequirement.addEventListener(
        "blur",
        validateResidencyRequirement,
      );
    }

    if (DOM.durationYears) {
      DOM.durationYears.addEventListener("input", validateDurationYears);

      DOM.durationYears.addEventListener("blur", validateDurationYears);
    }

    if (DOM.programDescription) {
      DOM.programDescription.addEventListener(
        "input",
        validateProgramDescription,
      );

      DOM.programDescription.addEventListener(
        "blur",
        validateProgramDescription,
      );
    }

    if (DOM.status) {
      DOM.status.addEventListener("change", validateStatus);
    }

    if (DOM.printButton) {
      DOM.printButton.addEventListener("click", handlePrint);
    }

    if (DOM.exportButton) {
      DOM.exportButton.addEventListener("click", handleExport);
    }

    document.addEventListener("click", handleGlobalAddClick);
  }

  function handleGlobalAddClick(event) {
    const addButton = event.target.closest(".add-program-btn");

    if (!addButton) {
      return;
    }

    setAddMode();
  }

  function handlePrint() {
    const url =
      DOM.printButton && DOM.printButton.dataset.url
        ? DOM.printButton.dataset.url
        : "/dashboard/phd-program/print/";

    window.open(url, "_blank");
  }

  function handleExport() {
    const url =
      DOM.exportButton && DOM.exportButton.dataset.url
        ? DOM.exportButton.dataset.url
        : "/dashboard/phd-program/export/";

    window.location.href = url;
  }

  function handleEditModeFromForm() {
    if (!DOM.form || !DOM.form.dataset.editId) {
      return;
    }

    STATE.isEditMode = true;
    STATE.currentEditId = DOM.form.dataset.editId;

    if (DOM.modalTitle) {
      DOM.modalTitle.textContent = "Edit PhD Program";
    }

    if (DOM.modalIcon) {
      DOM.modalIcon.className = "ti ti-edit me-2";
    }

    if (DOM.saveButtonText) {
      DOM.saveButtonText.textContent = "Update Program";
    }

    if (DOM.saveButtonIcon) {
      DOM.saveButtonIcon.className = "ti ti-device-floppy";
    }

    if (DOM.form && CONFIG.updateUrl) {
      DOM.form.action = CONFIG.updateUrl.replace(
        "/0/",
        `/${DOM.form.dataset.editId}/`,
      );
    }
  }

  function initializeAlerts() {
    document.querySelectorAll(".alert").forEach((alert) => {
      setTimeout(() => {
        alert.classList.add("alert-hide");

        alert.addEventListener(
          "transitionend",
          function () {
            this.remove();
          },
          {
            once: true,
          },
        );
      }, 3000);
    });
  }

  function initializeAOS() {
    if (typeof AOS !== "undefined" && AOS.init) {
      AOS.init({
        duration: 700,
        easing: "ease-out-cubic",
        once: true,
        offset: 60,
      });
    }
  }

  function initializeFlatpickr() {
    if (typeof flatpickr === "undefined") {
      return;
    }

    document.querySelectorAll(".flatpickr-input").forEach((element) => {
      if (element._flatpickr) {
        return;
      }

      flatpickr(element, {
        dateFormat: "Y-m-d",
        allowInput: true,
      });
    });
  }

  function showToast(icon, title) {
    if (typeof Swal === "undefined" || !Swal.fire) {
      return;
    }

    Swal.fire({
      toast: true,
      position: "top-end",
      icon: icon,
      title: title,
      showConfirmButton: false,
      timer: 2500,
      timerProgressBar: true,
    });
  }

  function initialize() {
    initializeChoices();
    initializeModal();
    initializeEventListeners();
    initializeFlatpickr();
    handleEditModeFromForm();
    handleServerErrors();
    initializeAlerts();
    initializeAOS();

    if (DOM.searchInput) {
      performSearch(DOM.searchInput.value, 1);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize);
  } else {
    initialize();
  }
})();
