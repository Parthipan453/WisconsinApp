(function () {
  "use strict";

  const DOM = {
    addBtn: document.getElementById("addCommitteeBtn"),
    addBtnToolbar: document.getElementById("addCommitteeBtnToolbar"),
    addBtnEmpty: document.getElementById("addCommitteeBtnEmpty"),
    saveBtn: document.getElementById("saveCommitteeBtn"),
    confirmDeleteBtn: document.getElementById("confirmDeleteBtn"),
    searchBtn: document.getElementById("searchBtn"),
    searchInput: document.getElementById("searchInput"),
    committeeModal: document.getElementById("committeeModal"),
    deleteModal: document.getElementById("deleteModal"),
    modalBody: document.getElementById("committeeModalBody"),
    modalLabel: document.getElementById("committeeModalLabel"),
    cardGrid: document.getElementById("committeeCardGrid"),
    toastContainer: document.getElementById("custom-toast-container"),
  };

  let state = {
    isEdit: false,
    committeeId: null,
    choicesInstances: [],
    flatpickrInstance: null,
    isSubmitting: false,
    deleteTargetId: null,
    searchTimeout: null,
  };

  let committeeModalInstance = null;
  let deleteModalInstance = null;
  function showSuccess(message) {
    Swal.fire({
      icon: "success",
      title: "Success",
      text: message,
      confirmButtonText: "OK",
      confirmButtonColor: "#C5050C",
    });
  }

  function showError(message) {
    Swal.fire({
      icon: "error",
      title: "Error",
      text: message,
      confirmButtonText: "OK",
      confirmButtonColor: "#C5050C",
    });
  }
  function getCSRFToken() {
    const cookieValue = document.cookie
      .split("; ")
      .find((row) => row.startsWith("csrftoken="));
    return cookieValue ? cookieValue.split("=")[1] : "";
  }

  function buildUrl(base, params) {
    const url = new URL(base, window.location.origin);
    Object.keys(params).forEach((key) => {
      if (params[key]) {
        url.searchParams.append(key, params[key]);
      }
    });
    return url.toString();
  }

  function getModalInstance(element, options) {
    if (element && element._bsModal) {
      return element._bsModal;
    }
    return new bootstrap.Modal(element, options || { backdrop: "static" });
  }

  function destroyChoices() {
    state.choicesInstances.forEach((instance) => {
      try {
        instance.destroy();
      } catch (e) {}
    });
    state.choicesInstances = [];

    document.querySelectorAll(".choices").forEach((el) => {
      if (el._choices) {
        try {
          el._choices.destroy();
        } catch (e) {}
      }
    });
  }

  function destroyFlatpickr() {
    if (state.flatpickrInstance) {
      try {
        state.flatpickrInstance.destroy();
      } catch (e) {}
      state.flatpickrInstance = null;
    }
  }

  function initChoices(form) {
    destroyChoices();

    const selects = form.querySelectorAll("select");

    selects.forEach((select) => {
      if (select.dataset.noChoices) return;

      try {
        const instance = new Choices(select, {
          searchEnabled: true,
          searchPlaceholderValue: "Search...",
          shouldSort: false,
          itemSelectText: "",
          position: "auto",
          renderSelectedChoices: "auto",
        });

        select._choices = instance;

        state.choicesInstances.push(instance);
      } catch (e) {
        console.warn("Choices init error:", e);
      }
    });

    setupAdvisorChairFilter(form);
  }
  function setupAdvisorChairFilter(form) {
    const studentSelect = form.querySelector("#id_phd_student");
    const chairSelect = form.querySelector("#id_chair_faculty");

    if (!studentSelect || !chairSelect) {
      return;
    }

    const chairChoices = chairSelect._choices;

    if (!chairChoices) {
      console.warn("Chair Faculty Choices instance not found.");
      return;
    }

    const originalChairOptions = Array.from(chairSelect.options).map(
      (option) => ({
        value: option.value,
        label: option.textContent.trim(),
        disabled: option.disabled,
        selected: option.selected,
      }),
    );

    function updateChairFaculty() {
      const selectedOption = studentSelect.options[studentSelect.selectedIndex];

      let advisorId = "";

      if (selectedOption) {
        advisorId = selectedOption.getAttribute("data-advisor-id") || "";
      }

      const currentChairValue = chairSelect.value;

      const filteredOptions = originalChairOptions.filter((option) => {
        if (!option.value) {
          return true;
        }

        if (!advisorId) {
          return true;
        }

        return String(option.value) !== String(advisorId);
      });

      chairChoices.clearChoices();

      chairChoices.setChoices(
        filteredOptions.map((option) => ({
          value: option.value,
          label: option.label,
          disabled: option.disabled,
          selected:
            option.value &&
            option.value === currentChairValue &&
            option.value !== advisorId,
        })),
        "value",
        "label",
        true,
      );

      if (advisorId && String(currentChairValue) === String(advisorId)) {
        chairChoices.removeActiveItems();
      }
    }

    studentSelect.addEventListener("change", updateChairFaculty);

    updateChairFaculty();
  }
  function initFlatpickr(form) {
    destroyFlatpickr();

    const dateInputs = form.querySelectorAll(".flatpickr-date");

    const today = new Date();

    dateInputs.forEach((input) => {
      try {
        const format = input.dataset.dateFormat || "Y-m-d";

        state.flatpickrInstance = flatpickr(input, {
          dateFormat: format,
          allowInput: true,
          enableTime: false,
          disableMobile: true,
          position: "auto",
          positionElement: input,
          static: false,
          minDate: "2020-01-01",
          maxDate: today,
        });
      } catch (e) {
        console.warn("Flatpickr init error:", e);
      }
    });
  }
  function cleanupPlugins() {
    destroyChoices();
    destroyFlatpickr();
  }
  function loadForm(committeeId) {
    const isEdit = !!committeeId;

    const url =
      "/dashboard/doctoral-committee/get-form/" +
      (isEdit ? `?committee_id=${committeeId}` : "");

    DOM.modalBody.innerHTML = `
        <div class="dcm-modal-loading">
            <div class="dcm-spinner"></div>
            <span>Loading form...</span>
        </div>
    `;

    fetch(url, {
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Failed to load form (${response.status})`);
        }
        return response.json();
      })
      .then((data) => {
        if (!data.html) {
          throw new Error("Form HTML was not returned by server.");
        }

        DOM.modalBody.innerHTML = data.html;
        DOM.modalLabel.textContent = isEdit
          ? "Edit Doctoral Committee"
          : "Add Doctoral Committee";

        state.isEdit = isEdit;
        state.committeeId = committeeId;

        initChoices(DOM.modalBody);
        initFlatpickr(DOM.modalBody);
        bindFormSubmit();
      })
      .catch((error) => {
        console.error("Form load error:", error);
        DOM.modalBody.innerHTML = `
                <div class="dcm-empty-state" style="padding:20px;">
                    <i class="fas fa-exclamation-circle"
                       style="font-size:2rem;color:var(--dcm-danger);"></i>
                    <p style="margin-top:12px;color:var(--dcm-text-secondary);">
                        ${escapeHtml(error.message)}
                    </p>
                    <button type="button"
                            class="dcm-btn dcm-btn--primary"
                            onclick="location.reload()">
                        <i class="fas fa-sync"></i> Retry
                    </button>
                </div>
            `;

        showError(error.message);
      });
  }

  function bindFormSubmit() {
    const newSaveBtn = DOM.saveBtn.cloneNode(true);
    DOM.saveBtn.parentNode.replaceChild(newSaveBtn, DOM.saveBtn);
    DOM.saveBtn = newSaveBtn;

    DOM.saveBtn.addEventListener("click", submitForm);

    const form = DOM.modalBody.querySelector("form");
    if (form) {
      form.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && e.target.tagName !== "TEXTAREA") {
          e.preventDefault();
          submitForm();
        }
      });
    }
  }

  function submitForm() {
    if (state.isSubmitting) return;

    const form = DOM.modalBody.querySelector("form");
    if (!form) {
      showError("Form not found. Please try again.");
      return;
    }

    const requiredFields = form.querySelectorAll("[required]");
    let isValid = true;
    requiredFields.forEach((field) => {
      if (!field.value || field.value.trim() === "") {
        field.classList.add("is-invalid");
        isValid = false;
      } else {
        field.classList.remove("is-invalid");
      }
    });

    if (!isValid) {
      showError("Please fill in all required fields.");
      return;
    }

    state.isSubmitting = true;
    DOM.saveBtn.disabled = true;
    DOM.saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

    const formData = new FormData(form);
    const url = state.isEdit
      ? `/dashboard/doctoral-committee/update/${state.committeeId}/`
      : "/dashboard/doctoral-committee/create/";

    fetch(url, {
      method: "POST",
      body: formData,
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCSRFToken(),
      },
    })
      .then((response) => response.json())
      .then((data) => {
        state.isSubmitting = false;
        DOM.saveBtn.disabled = false;
        DOM.saveBtn.innerHTML =
          '<i class="fas fa-save"></i><span>Save Committee</span>';

        if (data.success) {
          committeeModalInstance.hide();

          Swal.fire({
            icon: "success",
            title: state.isEdit
              ? "Updated Successfully"
              : "Created Successfully",
            text:
              data.message ||
              (state.isEdit
                ? "Doctoral Committee updated successfully."
                : "Doctoral Committee created successfully."),
            confirmButtonText: "OK",
            confirmButtonColor: "#C5050C",
            allowOutsideClick: false,
          }).then(function () {
            window.location.reload();
          });
        } else {
          const form = DOM.modalBody.querySelector("form");
          if (form) {
            form
              .querySelectorAll(".is-invalid")
              .forEach((el) => el.classList.remove("is-invalid"));
            form
              .querySelectorAll(".invalid-feedback")
              .forEach((el) => el.remove());
          }

          if (data.errors) {
            try {
              const errors = data.errors;
              Object.keys(errors).forEach((field) => {
                const messages = errors[field];
                if (Array.isArray(messages)) {
                  messages.forEach((msg) => {
                    const fieldLabel =
                      field.charAt(0).toUpperCase() +
                      field.slice(1).replace(/_/g, " ");
                    showError(`${fieldLabel}: ${msg}`);
                  });
                } else {
                  showError(messages);
                }
              });
            } catch (e) {
              console.error("Error parsing errors:", e);
              if (typeof data.errors === "string") {
                showError(data.errors);
              } else {
                showError("Form validation failed. Please check your inputs.");
              }
            }
          } else {
            showError(
              data.message || "Failed to save committee. Please try again.",
            );
          }
        }
      })
      .catch((error) => {
        state.isSubmitting = false;
        DOM.saveBtn.disabled = false;
        DOM.saveBtn.innerHTML =
          '<i class="fas fa-save"></i><span>Save Committee</span>';
        console.error("Submit error:", error);
        showError("An error occurred. Please try again.");
      });
  }

  function openDeleteModal(committeeId) {
    state.deleteTargetId = committeeId;
    deleteModalInstance.show();
  }

  function executeDelete() {
    if (!state.deleteTargetId) return;

    const committeeId = state.deleteTargetId;
    const url = `/dashboard/doctoral-committee/delete/${committeeId}/`;

    DOM.confirmDeleteBtn.disabled = true;
    DOM.confirmDeleteBtn.innerHTML =
      '<i class="fas fa-spinner fa-spin"></i> Deleting...';

    fetch(url, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCSRFToken(),
      },
    })
      .then((response) => response.json())
      .then((data) => {
        DOM.confirmDeleteBtn.disabled = false;
        DOM.confirmDeleteBtn.innerHTML =
          '<i class="fas fa-trash"></i><span>Delete</span>';

        if (data.success) {
          deleteModalInstance.hide();
          showSuccess(data.message || "Committee deleted successfully.");
          state.deleteTargetId = null;
          window.location.reload();
        } else {
          showError(data.message || "Failed to delete committee.");
        }
      })
      .catch((error) => {
        DOM.confirmDeleteBtn.disabled = false;
        DOM.confirmDeleteBtn.innerHTML =
          '<i class="fas fa-trash"></i><span>Delete</span>';
        console.error("Delete error:", error);
        showError("An error occurred. Please try again.");
      });
  }

  function refreshData() {
    const currentUrl = new URL(window.location.href);
    const search = currentUrl.searchParams.get("search") || "";
    const page = currentUrl.searchParams.get("page") || "1";

    fetch(
      buildUrl(window.location.pathname, {
        page: page,
        search: search,
      }),
      {
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      },
    )
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to refresh data");
        }
        return response.json();
      })
      .then((data) => {
        if (data.results && data.results.length > 0) {
          renderCards(data.results);
        } else {
          renderEmptyState();
        }
      })
      .catch((error) => {
        console.error("Refresh error:", error);
        window.location.reload();
      });
  }

  function renderCards(committees) {
    if (!DOM.cardGrid) return;

    let html = "";
    committees.forEach((committee, index) => {
      const statusClass = committee.approval_status.toLowerCase();
      const statusDisplay =
        committee.approval_status_display || committee.approval_status;

      html += `
                <article class="dcm-card" data-committee-id="${committee.committee_id}">
                    <div class="dcm-card-header">
                        <div class="dcm-card-header-left">
                            <i class="fas fa-users-cog dcm-card-icon"></i>
                            <span class="dcm-card-title">Doctoral Committee</span>
                        </div>
                        <span class="dcm-status-badge dcm-status-badge--${statusClass}">
                            ${statusDisplay}
                        </span>
                    </div>
                    <div class="dcm-card-body">
                        <div class="dcm-student-info">
                            <h3 class="dcm-student-name">${escapeHtml(committee.phd_student || "")}</h3>
                            <div class="dcm-student-meta">
                                <span class="dcm-student-id">
                                    <i class="fas fa-id-card"></i>
                                    ${escapeHtml(committee.student_number || "")}
                                </span>
                                <span class="dcm-student-program">
                                    <i class="fas fa-graduation-cap"></i>
                                    ${escapeHtml(committee.program || "")}
                                </span>
                            </div>
                        </div>
                        <div class="dcm-info-grid">
                            <div class="dcm-info-item">
                                <span class="dcm-info-label">
                                    <i class="fas fa-user-tie"></i>
                                    Chair Faculty
                                </span>
                                <span class="dcm-info-value">${escapeHtml(committee.chair_faculty || "")}</span>
                            </div>
                            <div class="dcm-info-item">
                                <span class="dcm-info-label">
                                    <i class="fas fa-calendar-alt"></i>
                                    Formation Date
                                </span>
                                <span class="dcm-info-value">${escapeHtml(committee.formation_date || "")}</span>
                            </div>
                        </div>
                    </div>
                    <div class="dcm-card-footer">
                        <button type="button" class="dcm-action-btn dcm-action-btn--edit" data-committee-id="${committee.committee_id}" aria-label="Edit committee">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button type="button" class="dcm-action-btn dcm-action-btn--delete" data-committee-id="${committee.committee_id}" aria-label="Delete committee">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </article>
            `;
    });

    DOM.cardGrid.innerHTML = html;
    bindCardEvents();
  }

  function renderEmptyState() {
    if (!DOM.cardGrid) return;
    DOM.cardGrid.innerHTML = `
            <div class="dcm-empty-state">
                <i class="fas fa-users-slash dcm-empty-icon"></i>
                <h2 class="dcm-empty-title">No Doctoral Committees Found</h2>
                <p class="dcm-empty-description">Create a doctoral committee to get started.</p>
                <button type="button" class="dcm-btn dcm-btn--primary dcm-empty-btn" id="addCommitteeBtnEmpty">
                    <i class="fas fa-plus"></i>
                    Add Committee
                </button>
            </div>
        `;

    const emptyBtn = document.getElementById("addCommitteeBtnEmpty");
    if (emptyBtn) {
      emptyBtn.addEventListener("click", openAddModal);
    }
  }

  function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function bindCardEvents() {
    document.querySelectorAll(".dcm-action-btn--edit").forEach((btn) => {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        const id = this.dataset.committeeId;
        if (id) openEditModal(id);
      });
    });

    document.querySelectorAll(".dcm-action-btn--delete").forEach((btn) => {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        const id = this.dataset.committeeId;
        if (id) openDeleteModal(id);
      });
    });
  }
  function openAddModal() {
    const page = document.querySelector(".dcm-page");

    if (!page) {
      showError("Unable to verify doctoral committee requirements.");
      return;
    }

    const hasActiveProgram = page.dataset.hasActivePhdProgram === "true";

    const hasPhdStudent = page.dataset.hasPhdStudent === "true";

    const hasActivePhdStudent = page.dataset.hasActivePhdStudent === "true";

    const hasMentorAssignedStudent =
      page.dataset.hasMentorAssignedStudent === "true";

    const hasEligibleCommitteeStudent =
      page.dataset.hasEligibleCommitteeStudent === "true";

    if (!hasActiveProgram) {
      Swal.fire({
        icon: "warning",
        title: "PhD Program Required",
        text: "Please create a PhD Program before creating a doctoral committee.",
        confirmButtonText: "Create PhD Program",
        confirmButtonColor: "#C5050C",
        showCloseButton: true,
        allowOutsideClick: false,
      }).then(function (result) {
        if (result.isConfirmed) {
          window.location.href = "/dashboard/phd-program/";
        }
      });

      return;
    }

    if (!hasPhdStudent) {
      Swal.fire({
        icon: "warning",
        title: "PhD Student Required",
        text: "Please create a PhD Student before creating a doctoral committee.",
        confirmButtonText: "Create PhD Student",
        confirmButtonColor: "#C5050C",
        allowOutsideClick: false,
      }).then(function (result) {
        if (result.isConfirmed) {
          window.location.href = "/dashboard/phd-student/";
        }
      });

      return;
    }

    if (!hasActivePhdStudent) {
      Swal.fire({
        icon: "warning",
        title: "Active PhD Student Required",
        text: "Please ensure that an active PhD Student is available before creating a doctoral committee.",
        confirmButtonText: "Go to PhD Students",
        confirmButtonColor: "#C5050C",
        allowOutsideClick: false,
      }).then(function (result) {
        if (result.isConfirmed) {
          window.location.href = "/dashboard/phd-student/";
        }
      });

      return;
    }

    if (!hasMentorAssignedStudent) {
      Swal.fire({
        icon: "warning",
        title: "Mentor Assignment Required",
        text: "Please assign a mentor to the PhD Student before creating a doctoral committee.",
        confirmButtonText: "Assign Mentor",
        confirmButtonColor: "#C5050C",
        allowOutsideClick: false,
      }).then(function (result) {
        if (result.isConfirmed) {
          window.location.href = "/dashboard/phd-student/";
        }
      });

      return;
    }

    if (!hasEligibleCommitteeStudent) {
      Swal.fire({
        icon: "info",
        title: "No PhD Students Available",
        text: "All eligible PhD students have already been assigned to a doctoral committee. There are no students available to assign at this time.",
        confirmButtonText: "Okay",
        confirmButtonColor: "#C5050C",
        showCloseButton: true,
        allowOutsideClick: false,
      });

      return;
    }

    cleanupPlugins();
    loadForm(null);
    committeeModalInstance.show();
  }
  function openEditModal(committeeId) {
    cleanupPlugins();
    loadForm(committeeId);
    committeeModalInstance.show();
  }

  function handleSearch() {
    const search = DOM.searchInput ? DOM.searchInput.value.trim() : "";
    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set("search", search);
    currentUrl.searchParams.delete("page");
    window.location.href = currentUrl.toString();
  }

  function debouncedSearch() {
    if (state.searchTimeout) {
      clearTimeout(state.searchTimeout);
    }
    state.searchTimeout = setTimeout(handleSearch, 400);
  }

  function init() {
    if (DOM.committeeModal) {
      committeeModalInstance = getModalInstance(DOM.committeeModal);
    }
    if (DOM.deleteModal) {
      deleteModalInstance = getModalInstance(DOM.deleteModal);
    }

    if (DOM.addBtn) {
      DOM.addBtn.addEventListener("click", openAddModal);
    }
    if (DOM.addBtnToolbar) {
      DOM.addBtnToolbar.addEventListener("click", openAddModal);
    }
    if (DOM.addBtnEmpty) {
      DOM.addBtnEmpty.addEventListener("click", openAddModal);
    }

    if (DOM.saveBtn) {
      DOM.saveBtn.addEventListener("click", submitForm);
    }

    if (DOM.confirmDeleteBtn) {
      DOM.confirmDeleteBtn.addEventListener("click", executeDelete);
    }

    if (DOM.searchBtn) {
      DOM.searchBtn.addEventListener("click", handleSearch);
    }
    if (DOM.searchInput) {
      DOM.searchInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          handleSearch();
        }
      });
      DOM.searchInput.addEventListener("input", debouncedSearch);
    }

    bindCardEvents();

    if (DOM.committeeModal) {
      DOM.committeeModal.addEventListener("hidden.bs.modal", function () {
        cleanupPlugins();
        DOM.modalBody.innerHTML = `
                    <div class="dcm-modal-loading">
                        <div class="dcm-spinner"></div>
                        <span>Loading form...</span>
                    </div>
                `;
        state.isSubmitting = false;
        state.isEdit = false;
        state.committeeId = null;
        DOM.saveBtn.disabled = false;
        DOM.saveBtn.innerHTML =
          '<i class="fas fa-save"></i><span>Save Committee</span>';
      });
    }

    if (DOM.deleteModal) {
      DOM.deleteModal.addEventListener("hidden.bs.modal", function () {
        state.deleteTargetId = null;
        DOM.confirmDeleteBtn.disabled = false;
        DOM.confirmDeleteBtn.innerHTML =
          '<i class="fas fa-trash"></i><span>Delete</span>';
      });
    }

    console.log("Doctoral Committee Management initialized.");
  }

  window.DoctoralCommittee = {
    openAddModal: openAddModal,
    openEditModal: openEditModal,
    openDeleteModal: openDeleteModal,
    refreshData: refreshData,
    init: init,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
