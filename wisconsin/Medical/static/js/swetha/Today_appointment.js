"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const allItems = Array.from(document.querySelectorAll(".mas-patient-item"));
  const searchInput = document.getElementById("appointmentSearch");
  const typeFilter = document.getElementById("typeFilter");
  const filterTabs = document.querySelectorAll(".mas-filter-tab");
  const patientGrid = document.getElementById("patientGrid");
  const prevPageBtn = document.getElementById("prevPage");
  const nextPageBtn = document.getElementById("nextPage");
  const pageInfo = document.getElementById("pageInfo");
  const preview = document.getElementById("patientPreview");
  const consultationContainer = document.getElementById(
    "consultationContainer",
  );

  let selectedCard = null;
  let currentFilter = "all";
  let currentPage = 1;
  const itemsPerPage = 12;
  let filteredItemsCache = [];
  let currentAthlete = null;
  let editingInjuryId = null;

  let pendingAthleteMedicalCare = null;
  let pendingAthleteInjury = null;

  window.currentPatientId = null;
  window.currentAthleteId = null;
  window.currentAthleteMedicalId = null;
  window.currentAthlete = null;

  const choicesInstances = new Map();

  function destroyChoices(selectElement) {
    if (!selectElement) {
      return;
    }

    const instance = choicesInstances.get(selectElement);

    if (instance) {
      instance.destroy();
      choicesInstances.delete(selectElement);
    }
  }
  function initChoicesSelect(selectElement, placeholder = "Select an option") {
    if (!selectElement) {
      return null;
    }

    destroyChoices(selectElement);
    const instance = new Choices(selectElement, {
      searchEnabled: true,
      searchChoices: true,
      shouldSort: false,
      itemSelectText: "",
      allowHTML: false,
      placeholder: true,
      placeholderValue: placeholder,
      removeItemButton: false,
    });

    choicesInstances.set(selectElement, instance);

    return instance;
  }

  function initChoicesInContainer(container) {
    if (!container) {
      return;
    }

    const selects = container.querySelectorAll("select");

    selects.forEach((selectElement) => {
      let placeholder = "Select an option";

      const firstOption = selectElement.querySelector("option");

      if (
        firstOption &&
        (firstOption.value === "" || firstOption.value === "NOT SELECTED")
      ) {
        placeholder = firstOption.textContent.trim() || "Select an option";
      }

      initChoicesSelect(selectElement, placeholder);
    });
  }

  function initDateFields(container) {
    if (!container) {
      return;
    }

    const dateInputs = container.querySelectorAll('input[type="date"]');

    dateInputs.forEach((input) => {
      input.addEventListener("change", function () {
        this.classList.remove("is-invalid");
      });
    });
  }

  function initDynamicFormFields(container) {
    if (!container) {
      return;
    }
    requestAnimationFrame(() => {
      initChoicesInContainer(container);

      initDateFields(container);
    });
  }

  function getCookie(name) {
    let value = null;

    if (!document.cookie) {
      return value;
    }

    document.cookie.split(";").forEach((cookie) => {
      cookie = cookie.trim();

      if (cookie.startsWith(name + "=")) {
        value = decodeURIComponent(cookie.substring(name.length + 1));
      }
    });

    return value;
  }

  const csrftoken = getCookie("csrftoken");

  function escapeHTML(value) {
    if (value === null || value === undefined) {
      return "";
    }

    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function convertDisplayDateToInput(value) {
    if (!value) {
      return "";
    }

    const text = String(value).trim();

    if (/^\d{4}-\d{2}-\d{2}$/.test(text)) {
      return text;
    }

    const match = text.match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})$/);

    if (match) {
      const day = match[1].padStart(2, "0");
      const month = match[2].padStart(2, "0");
      const year = match[3];

      return `${year}-${month}-${day}`;
    }

    const parsed = new Date(text);

    if (!Number.isNaN(parsed.getTime())) {
      return [
        parsed.getFullYear(),
        String(parsed.getMonth() + 1).padStart(2, "0"),
        String(parsed.getDate()).padStart(2, "0"),
      ].join("-");
    }

    return "";
  }

  function convertDisplayTimeToInput(value) {
    if (!value) {
      return "";
    }

    const text = String(value).trim();

    if (/^\d{2}:\d{2}$/.test(text)) {
      return text;
    }

    const match = text.match(/^(\d{1,2}):(\d{2})(?:\s*(AM|PM))?$/i);

    if (!match) {
      return "";
    }

    let hour = parseInt(match[1], 10);

    const minute = match[2];

    const meridiem = match[3]?.toUpperCase();

    if (meridiem === "PM" && hour !== 12) {
      hour += 12;
    }

    if (meridiem === "AM" && hour === 12) {
      hour = 0;
    }

    return `${String(hour).padStart(2, "0")}:${minute}`;
  }

  async function parseJsonResponse(response) {
    const contentType = response.headers.get("content-type") || "";

    const text = await response.text();

    if (!text) {
      return {
        success: false,
        message: `Server returned HTTP ${response.status}`,
      };
    }

    if (!contentType.includes("application/json")) {
      console.error("Non JSON response:", text);

      return {
        success: false,
        message:
          `Server returned HTTP ${response.status}. ` +
          `Expected JSON response.`,
      };
    }

    try {
      return JSON.parse(text);
    } catch (error) {
      console.error("JSON parse error:", error);

      return {
        success: false,
        message: "Invalid JSON response from server.",
      };
    }
  }

  async function apiRequest(url, method = "GET", payload = null) {
    const options = {
      method,

      credentials: "same-origin",

      headers: {
        Accept: "application/json",

        "X-Requested-With": "XMLHttpRequest",

        "X-CSRFToken": csrftoken || "",
      },
    };

    if (payload !== null) {
      options.headers["Content-Type"] = "application/json";

      options.body = JSON.stringify(payload);
    }

    const response = await fetch(url, options);

    const data = await parseJsonResponse(response);

    if (!response.ok || !data.success) {
      throw new Error(data.message || data.error || `HTTP ${response.status}`);
    }

    return data;
  }

  if (
    typeFilter &&
    typeof Choices !== "undefined" &&
    !typeFilter.dataset.choicesInitialized
  ) {
    new Choices(typeFilter, {
      searchEnabled: false,

      itemSelectText: "",

      shouldSort: false,

      allowHTML: false,
    });

    typeFilter.dataset.choicesInitialized = "true";
  }

  filterTabs.forEach((tab) => {
    tab.addEventListener("click", function () {
      filterTabs.forEach((item) => {
        item.classList.remove("active");
      });

      this.classList.add("active");

      currentFilter = this.dataset.status || "all";

      currentPage = 1;

      filterAndPaginate();
    });
  });

  function filterAndPaginate() {
    const search = (searchInput?.value || "").toLowerCase().trim();

    const type = (typeFilter?.value || "").toLowerCase().trim();

    filteredItemsCache = allItems.filter((item) => {
      const name = (item.dataset.name || "").toLowerCase();

      const patientType = (item.dataset.type || "").toLowerCase();

      const status = (item.dataset.status || "").toUpperCase();

      const patientNumber = (
        item.querySelector(".mas-patient-number")?.textContent || ""
      )
        .toLowerCase()
        .trim();

      const registrationType = (
        item.dataset.registrationType || ""
      ).toLowerCase();

      const searchMatch =
        !search ||
        name.includes(search) ||
        patientNumber.includes(search) ||
        registrationType.includes(search);

      const typeMatch = !type || patientType === type;
      const admissionStatus = (
        item.dataset.admissionStatus || "NOT_REQUESTED"
      ).toUpperCase();

      const isAdmittedFlow =
        admissionStatus === "REQUESTED" || admissionStatus === "ADMITTED";

      // const statusMatch = currentFilter === "all" || status === currentFilter;

      // return searchMatch && typeMatch && statusMatch;
       let statusMatch;

      if (currentFilter === "all") {
        statusMatch = true;
      } else if (currentFilter === "ADMITTED") {
        statusMatch = isAdmittedFlow;
      } else if (isAdmittedFlow) {
        statusMatch = false; 
      } else {
        statusMatch = status === currentFilter;
      }

      return searchMatch && typeMatch && statusMatch;

    });

    allItems.forEach((item) => {
      item.style.display = "none";
    });

    const totalPages = Math.ceil(filteredItemsCache.length / itemsPerPage) || 1;

    if (currentPage > totalPages) {
      currentPage = totalPages;
    }

    const start = (currentPage - 1) * itemsPerPage;

    const end = Math.min(start + itemsPerPage, filteredItemsCache.length);

    filteredItemsCache.forEach((item, index) => {
      if (index >= start && index < end) {
        item.style.display = "flex";
      }
    });

    updatePagination(totalPages, filteredItemsCache.length);

    showEmptyState(filteredItemsCache.length);
  }

  function updatePagination(totalPages, totalItems) {
    if (prevPageBtn) {
      prevPageBtn.disabled = currentPage <= 1;
    }

    if (nextPageBtn) {
      nextPageBtn.disabled = currentPage >= totalPages;
    }

    if (pageInfo) {
      pageInfo.textContent = `Page ${currentPage} of ${totalPages} (${totalItems} items)`;
    }
  }

  function showEmptyState(totalItems) {
    if (!patientGrid) {
      return;
    }

    const existing = patientGrid.querySelector(".mas-empty-state");

    if (totalItems === 0) {
      if (!existing) {
        const empty = document.createElement("div");

        empty.className = "mas-empty-state";

        empty.style.gridColumn = "1 / -1";

        empty.innerHTML = `
          <div class="mas-empty-icon">
            <i class="fas fa-calendar-times"></i>
          </div>

          <h3>
            No matching appointments
          </h3>

          <p>
            Try adjusting your search or filters.
          </p>
        `;

        patientGrid.appendChild(empty);
      }
    } else if (existing) {
      existing.remove();
    }
  }

  prevPageBtn?.addEventListener("click", () => {
    if (currentPage <= 1) {
      return;
    }

    currentPage--;

    filterAndPaginate();

    document.querySelector(".mas-patient-grid-wrapper")?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  });

  nextPageBtn?.addEventListener("click", () => {
    const totalPages = Math.ceil(filteredItemsCache.length / itemsPerPage);

    if (currentPage >= totalPages) {
      return;
    }

    currentPage++;

    filterAndPaginate();

    document.querySelector(".mas-patient-grid-wrapper")?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  });

  searchInput?.addEventListener("input", () => {
    currentPage = 1;

    filterAndPaginate();
  });

  typeFilter?.addEventListener("change", () => {
    currentPage = 1;

    filterAndPaginate();
  });

  allItems.forEach((item) => {
    item.addEventListener("click", function () {
      if (selectedCard) {
        selectedCard.classList.remove("active");
      }

      selectedCard = this;

      this.classList.add("active");

      const patientId = this.dataset.patient;

      const registrationId = this.dataset.id;

      const status = this.dataset.status;

      loadPatientDetails(patientId, registrationId, status);
    });
  });

  async function loadPatientDetails(patientId, registrationId, status) {
    if (!preview) {
      return;
    }

    currentAthlete = null;

    editingInjuryId = null;

    window.currentPatientId = patientId || null;

    window.currentAthleteId = null;

    window.currentAthleteMedicalId = null;

    window.currentAthlete = null;

    if (consultationContainer) {
      consultationContainer.innerHTML = "";
    }

    preview.innerHTML = `
      <div class="mas-preview-empty">
        <div class="mas-skeleton-avatar"></div>
        <div class="mas-skeleton-line medium"></div>
        <div class="mas-skeleton-line short"></div>
      </div>
    `;

    if (typeof patientDetailsUrl === "undefined") {
      preview.innerHTML = `
        <div class="mas-preview-empty">

          <i class="fas fa-link-slash"></i>

          <h3>
            Patient details URL missing
          </h3>

        </div>
      `;

      return;
    }

    const url = patientDetailsUrl.replace(
      "/0/",
      `/${encodeURIComponent(patientId)}/`,
    );

    try {
      const data = await apiRequest(
        `${url}?registration_id=${encodeURIComponent(registrationId)}`,
      );

      const patient = data.patient || {};

      const athlete = data.athlete || null;

      const teamPhysicians = Array.isArray(data.team_physicians)
        ? data.team_physicians
        : [];

      const physiotherapists = Array.isArray(data.physiotherapists)
        ? data.physiotherapists
        : [];
      if (athlete) {
        athlete.team_physician_options = teamPhysicians;
        athlete.physiotherapist_options = physiotherapists;
      }

      console.log("Team Physicians:", teamPhysicians);
      console.log("Physiotherapists:", physiotherapists);

      window.currentPatientId = patient.id || patientId || null;

      window.currentAthleteId = athlete?.athlete_id || null;

      window.currentAthleteMedicalId = athlete?.athlete_medical_id || null;

      window.currentAthlete = athlete;

      currentAthlete = athlete;

      console.log("==========================================");

      console.log("Patient Details Loaded");

      console.log("Patient ID:", window.currentPatientId);

      console.log("Athlete ID:", window.currentAthleteId);

      console.log("Athlete Medical ID:", window.currentAthleteMedicalId);

      console.log("Registration ID:", registrationId);

      console.log("Athlete:", athlete);

      console.log("==========================================");
      console.log("PATIENT DATA:", patient);
console.log("PATIENT NAME:", patient.name);
console.log("PATIENT NAME ALT:", patient.patient_name);
      const ambulanceBadge = patient.arrived_by_ambulance
        ? `
                        <div class="mas-preview-ambulance-badge">
                          <i class="fas fa-ambulance"></i>
                          <span>Arrived by Ambulance</span>
                        </div>
                      `
        : "";

      preview.innerHTML = `

        <div class="mas-preview mas-fade">

          <div class="mas-preview-top">

            <div class="mas-preview-avatar">
              ${
                patient.photo
                  ? `
                    <img
                      src="${escapeHTML(patient.photo)}"
                      alt="${escapeHTML(
                          patient.name ||
                          patient.patient_name ||
                          patient.full_name ||
                          "Patient"
                        )}"
                    >
                  `
                  : `
                    <i class="fas fa-user"></i>
                  `
              }
            </div>


             <h3>
  ${escapeHTML(
    patient.name ||
    patient.patient_name ||
    patient.full_name ||
    "-"
  )}
</h3>

            <div class="mas-preview-role">
              ${escapeHTML(patient.role || "-")}
            </div>
            <div class="mas-preview-id">
              ${escapeHTML(
                patient.queue_number || patient.registration_number || "-",
              )}
            </div>
            
            ${ambulanceBadge}
          </div>
          <div class="mas-preview-body">
            ${infoRow("Patient Number", patient.patient_number || "-")}
            ${infoRow("Age", patient.age ?? "-")}
            ${infoRow("Gender", patient.gender || "-")}
            ${infoRow("Blood Group", patient.blood_group || "-")}
            ${infoRow("Phone", patient.phone || "-")}
            ${infoRow("Email", patient.email || "-")}
            ${infoRow("Previous Visits", patient.previous_visits ?? 0)}
            ${infoRow("Last Visit", patient.last_visit || "-")}
            ${infoRowWithScroll("Reason", patient.reason || "-")}
          </div>
          <div class="mas-preview-actions">
            ${getActionButtons(status, registrationId)}
          </div>
        </div>
      `;

      if (!consultationContainer) {
        return;
      }

      if (status === "WAITING") {
        consultationContainer.innerHTML = "";

        return;
      }

      // if (status === "IN_PROGRESS") {
      //   consultationContainer.innerHTML = getConsultationSection(
      //     status,
      //     registrationId,
      //     data.medical_visit || null,
      //     athlete,
      //   );

      if (status === "IN_PROGRESS") {
        consultationContainer.innerHTML = getConsultationSection(
          status,
          registrationId,
          data.medical_visit || null,
          athlete,
          patient.admission_status || "NOT_REQUESTED",
        );

        initVisitTypeChoices();

        initDynamicFormControls();
        initDatePickers();

        bindConsultationEvents();

        return;
      }

      // if (status === "COMPLETED") {
      //   consultationContainer.innerHTML = getConsultationSection(
      //     status,
      //     registrationId,
      //     data.medical_visit || null,
      //     athlete,
      //   );


      if (status === "COMPLETED") {
        consultationContainer.innerHTML = getConsultationSection(
          status,
          registrationId,
          data.medical_visit || null,
          athlete,
          patient.admission_status || "NOT_REQUESTED",
        );


        initVisitTypeChoices();

        initDynamicFormControls();

        bindConsultationEvents();

        return;
      }

      consultationContainer.innerHTML = "";
    } catch (error) {
      console.error("Patient details error:", error);

      window.currentPatientId = patientId || null;

      preview.innerHTML = `

        <div class="mas-preview-empty">

          <i class="fas fa-wifi"></i>

          <h3>
            Unable to load patient
          </h3>

          <p>
            ${escapeHTML(error.message || "")}
          </p>

        </div>

      `;

      if (consultationContainer) {
        consultationContainer.innerHTML = "";
      }
    }
  }

  function infoRow(label, value) {
    return `
      <div class="mas-info-row">

        <span class="mas-info-label">
          ${escapeHTML(label)}
        </span>

        <span class="mas-info-value">
          ${escapeHTML(value ?? "-")}
        </span>

      </div>
    `;
  }

  function infoRowWithScroll(label, value) {
    return `
      <div class="mas-info-block">

        <div class="mas-info-block-label">
          ${escapeHTML(label)}
        </div>

        <div class="mas-info-block-value">
          ${escapeHTML(value || "-")}
        </div>

      </div>
    `;
  }

  function getActionButtons(status, registrationId) {
    if (status === "WAITING") {
      return `
        <button
          type="button"
          class="mas-btn mas-checkin"
          data-id="${escapeHTML(registrationId)}"
        >

          <i class="fas fa-user-check"></i>

          Check In

        </button>
      `;
    }

    if (status === "IN_PROGRESS") {
      return `
        <div
          class="mas-status-message in-progress"
        >

          <i class="fas fa-stethoscope"></i>

          Consultation In Progress

        </div>
      `;
    }

    if (status === "COMPLETED") {
      return `
        <div
          class="mas-status-message completed"
        >

          <i class="fas fa-circle-check"></i>

          Consultation Completed

        </div>
      `;
    }

    return `
      <div class="mas-status-message">

        ${escapeHTML(status || "-")}

      </div>
    `;
  }

  function getConsultationSection(
    status,
    registrationId,
    consultation = null,
    athlete = null,
    admissionStatus = "NOT_REQUESTED",
  ) {
    if (status === "WAITING") {
      return "";
    }

    const isCompleted = status === "COMPLETED";

    const isAthlete =
      athlete &&
      (athlete.is_athlete === true ||
        athlete.is_athlete === 1 ||
        athlete.is_athlete === "1" ||
        athlete.is_athlete === "true");

    const visitType = consultation?.visit_type || "";

    const diagnosis = consultation?.diagnosis || "";

    const treatment = consultation?.treatment || "";

    const medications = consultation?.medications || "";

    const notes = consultation?.notes || "";

    const followUpDate = consultation?.follow_up_date || "";

    return `

      <section
        class="mas-consultation-section"
      >

        <!-- =================================================
             CONSULTATION HEADER
        ================================================== -->

        <div
          class="mas-consultation-header"
        >

          <div
            class="mas-consultation-title"
          >

            <span
              class="mas-consultation-icon"
            >

              <i class="fas fa-stethoscope"></i>

            </span>


            <div>

              <h3>
                Consultation Details
              </h3>

              <p>

                ${
                  isCompleted
                    ? "Completed consultation"
                    : "Enter diagnosis and treatment information"
                }

              </p>

            </div>

          </div>

        </div>


        <!-- =================================================
             CONSULTATION FORM
        ================================================== -->

        <div
          class="mas-consultation-grid"
        >

          <!-- VISIT TYPE -->

          <div
            class="mas-form-group"
          >

            <label>

              Visit Type

              <span class="required">
                *
              </span>

            </label>


            <select
              id="consultVisitType"
              ${isCompleted ? "disabled" : ""}
            >

              <option value="">
                Select visit type
              </option>


              <option
                value="CONSULTATION"
                ${visitType === "CONSULTATION" ? "selected" : ""}
              >
                Consultation
              </option>


              <option
                value="FOLLOW_UP"
                ${visitType === "FOLLOW_UP" ? "selected" : ""}
              >
                Follow-up
              </option>


              <option
                value="EMERGENCY"
                ${visitType === "EMERGENCY" ? "selected" : ""}
              >
                Emergency
              </option>


              <option
                value="INJURY"
                ${visitType === "INJURY" ? "selected" : ""}
              >
                Sports Injury
              </option>


              <option
                value="HEALTH_CHECK"
                ${visitType === "HEALTH_CHECK" ? "selected" : ""}
              >
                Routine Health Check
              </option>


              <option
                value="VACCINATION"
                ${visitType === "VACCINATION" ? "selected" : ""}
              >
                Vaccination
              </option>

            </select>


            <div
              id="consultFollowUpDateWrapper"
              class="mas-followup-date"
              style="
                display:${visitType === "FOLLOW_UP" ? "flex" : "none"};
              "
            >

              <label>
                Follow-up Date
              </label>


              <input
                type="date"
                id="consultFollowUpDate"
                value="${escapeHTML(followUpDate)}"
                ${isCompleted ? "disabled" : ""}
              >

            </div>

          </div>


          <!-- DIAGNOSIS -->

          <div
            class="mas-form-group"
          >

            <label>

              Diagnosis

              <span class="required">
                *
              </span>

            </label>


            <textarea
              id="consultDiagnosis"
              rows="4"
              placeholder="Enter diagnosis..."
              ${isCompleted ? "readonly" : ""}
            >${escapeHTML(diagnosis)}</textarea>

          </div>


          <!-- TREATMENT -->

          <div
            class="mas-form-group"
          >

            <label>

              Treatment

              <span class="required">
                *
              </span>

            </label>


            <textarea
              id="consultTreatment"
              rows="4"
              placeholder="Enter treatment provided..."
              ${isCompleted ? "readonly" : ""}
            >${escapeHTML(treatment)}</textarea>

          </div>


          <!-- MEDICATIONS -->

          <div
            class="mas-form-group"
          >

            <label>
              Medications
            </label>


            <textarea
              id="consultMedications"
              rows="4"
              placeholder="Enter prescribed medicines..."
              ${isCompleted ? "readonly" : ""}
            >${escapeHTML(medications)}</textarea>

          </div>


          <!-- NOTES -->

          <div
            class="mas-form-group"
          >

            <label>
              Additional Notes
            </label>


            <textarea
              id="consultNotes"
              rows="4"
              placeholder="Enter consultation notes..."
              ${isCompleted ? "readonly" : ""}
            >${escapeHTML(notes)}</textarea>

          </div>

        </div>


        <!-- =================================================
             ATHLETE ACCORDIONS
        ================================================== -->

        ${
          isAthlete
            ? `
              <div
                class="mas-athlete-care-container"
                id="athleteCareContainer"
              >

                ${getAthleteAccordionSection(athlete, isCompleted)}

              </div>
            `
            : ""
        }


        <!-- =================================================
             COMPLETE
        ================================================== -->

      <div
          class="mas-consultation-footer"
        >

          ${
            isCompleted
              ? ""
              : `
                <button
                  type="button"
                  class="
                    mas-btn
                    mas-btn-success
                    mas-complete-consultation
                  "
                  data-id="${escapeHTML(registrationId)}"
                >

                  <i class="fas fa-circle-check"></i>

                  Complete Consultation

                </button>
              `
          }

          ${getAdmitButton(status, registrationId, admissionStatus)}

        </div>

      </section>
    `;
  }


    function getAdmitButton(status, registrationId, admissionStatus) {
 
      if (status === "COMPLETED") {
          return "";
        }

        if (status !== "IN_PROGRESS") {
          return "";
        }


    if (admissionStatus === "ADMITTED") {
      return `
        <div class="mas-status-message completed">
          <i class="fas fa-bed-pulse"></i>
          Patient Admitted
        </div>
      `;
    }

    if (admissionStatus === "REQUESTED") {
      return `
        <div class="mas-status-message in-progress">
          <i class="fas fa-hourglass-half"></i>
          Admission Requested
        </div>
      `;
    }

    return `
      <button
        type="button"
        class="mas-btn mas-btn-admit"
        data-id="${escapeHTML(registrationId)}"
      >
        <i class="fas fa-bed-pulse"></i>
        Admit
      </button>
    `;
  }

  function bindConsultationEvents() {
    const completeBtn = document.querySelector(".mas-complete-consultation");

    if (completeBtn && completeBtn.dataset.bound !== "true") {
      completeBtn.dataset.bound = "true";

      completeBtn.addEventListener("click", handleCompleteConsultation);
    }

    const admitBtn = document.querySelector(".mas-btn-admit");

    if (admitBtn && admitBtn.dataset.bound !== "true") {
      admitBtn.dataset.bound = "true";

      admitBtn.addEventListener("click", handleAdmitRequest);
    }

    /* ATHLETE */

    bindAthleteAccordions();

    bindMedicalCareEvents();

    bindInjuryEvents();

    bindInjuryEditEvents();
  }

  function getAthleteAccordionSection(athlete, isCompleted = false) {
    athlete = athlete || {};

    return `

      <section
        class="mas-athlete-accordion-wrapper"
      >

        <!-- =================================================
             MEDICAL CARE
        ================================================== -->

        <div
          class="mas-athlete-accordion"
        >

          <button
            type="button"
            class="mas-athlete-accordion-header"
            data-accordion="medical"
            aria-expanded="false"
          >

            <div
              class="mas-athlete-accordion-title"
            >

              <span
                class="
                  mas-athlete-accordion-icon
                  medical
                "
              >

                <i class="fas fa-heart-pulse"></i>

              </span>


              <div>

                <strong>
                  Medical Care
                </strong>

                <p>
                  View and update athlete medical information
                </p>

              </div>

            </div>


            <span
              class="mas-athlete-accordion-arrow"
            >

              <i
                class="fas fa-chevron-down"
              ></i>

            </span>

          </button>


          <div
            class="mas-athlete-accordion-content"
            data-content="medical"
          >

            ${getAthleteMedicalContent(athlete, isCompleted)}

          </div>

        </div>


        <!-- =================================================
             INJURY RECORD
        ================================================== -->

        <div
          class="mas-athlete-accordion"
        >

          <button
            type="button"
            class="mas-athlete-accordion-header"
            data-accordion="injury"
            aria-expanded="false"
          >

            <div
              class="mas-athlete-accordion-title"
            >

              <span
                class="
                  mas-athlete-accordion-icon
                  injury
                "
              >

                <i class="fas fa-notes-medical"></i>

              </span>


              <div>

                <strong>
                  Injury Record
                </strong>

                <p>
                  View previous injury and add new injury record
                </p>

              </div>

            </div>


            <span
              class="mas-athlete-accordion-arrow"
            >

              <i
                class="fas fa-chevron-down"
              ></i>

            </span>

          </button>


          <div
            class="mas-athlete-accordion-content"
            data-content="injury"
          >

            ${getAthleteInjuryContent(athlete, isCompleted)}

          </div>

        </div>

      </section>
    `;
  }

  function bindAthleteAccordions() {
    const container = document.getElementById("athleteCareContainer");

    if (!container) {
      return;
    }

    const headers = container.querySelectorAll(".mas-athlete-accordion-header");

    headers.forEach((header) => {
      if (header.dataset.bound === "true") {
        return;
      }

      header.dataset.bound = "true";

      header.addEventListener("click", () => {
        const accordion = header.closest(".mas-athlete-accordion");

        if (!accordion) {
          return;
        }

        const content = accordion.querySelector(
          ".mas-athlete-accordion-content",
        );

        if (!content) {
          return;
        }

        const isOpen = accordion.classList.contains("open");

        /*
         * CLOSE ALL
         */

        container.querySelectorAll(".mas-athlete-accordion").forEach((item) => {
          item.classList.remove("open");

          const itemHeader = item.querySelector(
            ".mas-athlete-accordion-header",
          );

          const itemContent = item.querySelector(
            ".mas-athlete-accordion-content",
          );

          itemHeader?.setAttribute("aria-expanded", "false");

          if (itemContent) {
            itemContent.style.maxHeight = null;
          }
        });

        /*
         * OPEN SELECTED
         */

        if (!isOpen) {
          accordion.classList.add("open");

          header.setAttribute("aria-expanded", "true");

          requestAnimationFrame(() => {
            content.style.maxHeight = content.scrollHeight + "px";
          });
        }
      });
    });
  }

  function getAthleteMedicalContent(athlete, isCompleted = false) {
    athlete = athlete || {};

    return `

      <div
        class="mas-athlete-medical-content"
      >

        <div
          class="mas-injury-subtitle"
        >

          <i class="fas fa-heart-pulse"></i>

          Current Medical Information

        </div>


        <div
          class="mas-athlete-medical-grid"
        >

          ${athleteMedicalItem("Fitness Level", athlete.fitness_level)}


          ${athleteMedicalItem("Injury Risk", athlete.injury_risk)}


          ${athleteMedicalItem("Medical Clearance", athlete.medical_clearance)}


          ${athleteMedicalItem(
            "Last Medical Checkup",
            athlete.last_medical_checkup,
          )}


          ${athleteMedicalItem(
            "Next Medical Checkup",
            athlete.next_medical_checkup,
          )}

        </div>


        <div
          class="athlete-medical-text"
        >

          <div
            class="athlete-medical-text-card"
          >

            <span>

              <i class="fas fa-ban"></i>

              Current Medical Restrictions

            </span>


            <p>
              ${escapeHTML(
                athlete.medical_restrictions || "No restrictions recorded.",
              )}
            </p>

          </div>


          <div
            class="athlete-medical-text-card"
          >

            <span>

              <i class="fas fa-kit-medical"></i>

              Emergency Action Plan

            </span>


            <p>
              ${escapeHTML(
                athlete.emergency_action_plan ||
                  "No emergency action plan recorded.",
              )}
            </p>

          </div>

        </div>


        ${!isCompleted ? getMedicalCareUpdateForm(athlete) : ""}

      </div>
    `;
  }

  function athleteMedicalItem(label, value) {
    return `
      <div
        class="athlete-medical-item"
      >

        <span>
          ${escapeHTML(label)}
        </span>


        <strong>
          ${escapeHTML(value || "-")}
        </strong>

      </div>
    `;
  }

  function getMedicalCareUpdateForm(athlete) {
    athlete = athlete || {};

    const fitnessLevel =
      athlete.fitness_level_code || athlete.fitness_level || "NOT SELECTED";

    const medicalClearance =
      athlete.medical_clearance_code ||
      athlete.medical_clearance ||
      "NOT SELECTED";

    const injuryRisk = athlete.injury_risk_code || athlete.injury_risk || "";
    const careTeam = athlete.care_team || {};

    const selectedTeamPhysician =
      careTeam.team_physician !== null && careTeam.team_physician !== undefined
        ? String(careTeam.team_physician)
        : "";

    const selectedPhysiotherapist =
      careTeam.physiotherapist !== null &&
      careTeam.physiotherapist !== undefined
        ? String(careTeam.physiotherapist)
        : "";

    const teamPhysicianStaff = Array.isArray(athlete.team_physician_options)
      ? athlete.team_physician_options
      : [];

    const teamPhysicianOptions = teamPhysicianStaff
      .map((staff) => {
        const staffId = String(staff.id || "");

        return `
        <option
          value="${escapeHTML(staffId)}"
          ${staffId === selectedTeamPhysician ? "selected" : ""}
        >
          ${escapeHTML(staff.name || "Unnamed Physician")}
        </option>
      `;
      })
      .join("");

    const physiotherapistStaff = Array.isArray(athlete.physiotherapist_options)
      ? athlete.physiotherapist_options
      : [];

    const physiotherapistOptions = physiotherapistStaff
      .map((staff) => {
        const staffId = String(staff.id || "");

        return `
        <option
          value="${escapeHTML(staffId)}"
          ${staffId === selectedPhysiotherapist ? "selected" : ""}
        >
          ${escapeHTML(staff.name || "Unnamed Physiotherapist")}
        </option>
      `;
      })
      .join("");

    return `

      <div
        class="mas-update-medical-care"
      >

        <div
          class="mas-injury-subtitle"
        >

          <i class="fas fa-user-doctor"></i>

          Update Medical Care Information

        </div>


        <div
          class="mas-consultation-grid"
        >

          <!-- FITNESS -->

        <div class="mas-form-group">

            <label>
              Fitness Level
              <span class="required">*</span>
            </label>

            <select id="athleteFitnessLevel">

              <option
                value="NOT SELECTED"
                ${fitnessLevel === "NOT SELECTED" ? "selected" : ""}
              >
                Not selected
              </option>

              <option
                value="EXCELLENT"
                ${fitnessLevel === "EXCELLENT" ? "selected" : ""}
              >
                Excellent
              </option>

              <option
                value="GOOD"
                ${fitnessLevel === "GOOD" ? "selected" : ""}
              >
                Good
              </option>

              <option
                value="AVERAGE"
                ${fitnessLevel === "AVERAGE" ? "selected" : ""}
              >
                Average
              </option>

              <option
                value="POOR"
                ${fitnessLevel === "POOR" ? "selected" : ""}
              >
                Poor
              </option>

            </select>

          </div>


          <!-- MEDICAL CLEARANCE -->

         <div class="mas-form-group">

            <label>
              Medical Clearance
              <span class="required">*</span>
            </label>

            <select id="athleteMedicalClearance">

              <option
                value="NOT SELECTED"
                ${medicalClearance === "NOT SELECTED" ? "selected" : ""}
              >
                Not selected
              </option>

              <option
                value="FIT"
                ${medicalClearance === "FIT" ? "selected" : ""}
              >
                Fit to Play
              </option>

              <option
                value="LIMITED"
                ${medicalClearance === "LIMITED" ? "selected" : ""}
              >
                Limited Participation
              </option>

              <option
                value="REHAB"
                ${medicalClearance === "REHAB" ? "selected" : ""}
              >
                Under Rehabilitation
              </option>

              <option
                value="NOT_FIT"
                ${medicalClearance === "NOT_FIT" ? "selected" : ""}
              >
                Not Fit to Play
              </option>

            </select>

          </div>

          <!-- INJURY RISK -->

     <div class="mas-form-group">

  <label>
    Injury Risk
  </label>

  <select id="athleteInjuryRisk">

    <option value="">
      Select injury risk
    </option>

    <option
      value="LOW"
      ${injuryRisk === "LOW" ? "selected" : ""}
    >
      Low
    </option>

    <option
      value="MODERATE"
      ${injuryRisk === "MODERATE" ? "selected" : ""}
    >
      Moderate
    </option>

    <option
      value="HIGH"
      ${injuryRisk === "HIGH" ? "selected" : ""}
    >
      High
    </option>

  </select>

</div>


          <!-- CLEARANCE DATE -->

          <div
            class="mas-form-group"
          >

            <label>
              Clearance Date
            </label>


            <input
              type="date"
              id="athleteClearanceDate"
              value="${escapeHTML(athlete.clearance_date_input || "")}"
            >

          </div>


          <!-- CLEARANCE EXPIRY -->

          <div
            class="mas-form-group"
          >

            <label>
              Clearance Expiry
            </label>


            <input
              type="date"
              id="athleteClearanceExpiry"
              value="${escapeHTML(athlete.clearance_expiry_input || "")}"
            >

          </div>


          <!-- NEXT CHECKUP -->

          <div
            class="mas-form-group"
          >

            <label>
              Next Medical Checkup
            </label>


            <input
              type="date"
              id="athleteNextMedicalCheckup"
              value="${escapeHTML(athlete.next_medical_checkup || "")}"
            >

          </div>
            <!-- TEAM PHYSICIAN -->

            <div class="mas-form-group">

              <label for="athleteTeamPhysician">
                Team Physician
              </label>

              <select
                id="athleteTeamPhysician"
                class="form-select"
              >

                <option value="">
                  Select Team Physician
                </option>

                ${teamPhysicianOptions}

              </select>

            </div>

            <!-- PHYSIOTHERAPIST -->

              <div class="mas-form-group">

                <label for="athletePhysiotherapist">
                  Physiotherapist
                </label>

                <select
                  id="athletePhysiotherapist"
                  class="form-select"
                >

                  <option value="">
                    Select Physiotherapist
                  </option>

                  ${physiotherapistOptions}

                </select>

              </div>


          <!-- RESTRICTIONS -->

          <div
            class="mas-form-group"
          >

            <label>
              Current Medical Restrictions
            </label>


            <textarea
              id="athleteMedicalRestrictions"
              rows="4"
              placeholder="Enter current medical restrictions..."
            >${escapeHTML(athlete.medical_restrictions || "")}</textarea>

          </div>


          <!-- EMERGENCY PLAN -->

          <div
            class="mas-form-group"
          >

            <label>
              Emergency Action Plan
            </label>


            <textarea
              id="athleteEmergencyActionPlan"
              rows="4"
              placeholder="Enter emergency action plan..."
            >${escapeHTML(athlete.emergency_action_plan || "")}</textarea>

          </div>

        </div>


        <div
          class="mas-medical-care-footer"
        >

          <button
            type="button"
            class="
              mas-btn
              mas-btn-primary
            "
            id="saveAthleteMedicalCare"

            data-athlete="${escapeHTML(athlete.athlete_id || "")}"

            data-registration="${escapeHTML(selectedCard?.dataset.id || "")}"

            data-patient="${escapeHTML(selectedCard?.dataset.patient || "")}"
          >

            <i class="fas fa-save"></i>

            Save Medical Care

          </button>

        </div>

      </div>
    `;
  }

  function getAthleteInjuryContent(athlete, isCompleted = false) {
    athlete = athlete || {};

    const latestInjury =
      athlete.latest_injury ||
      (Array.isArray(athlete.injuries) ? athlete.injuries[0] : null);

    return `

      <div
        class="mas-athlete-injury-content"
      >

        <!-- PREVIOUS -->

        <div
          class="mas-injury-subtitle"
        >

          <i
            class="fas fa-clock-rotate-left"
          ></i>

          Previous Injury Record

        </div>


        ${
          latestInjury
            ? getLatestInjuryCard(latestInjury, isCompleted)
            : `
              <div
                class="mas-no-injury-history"
              >

                <i
                  class="fas fa-circle-info"
                ></i>

                No previous injury records found.

              </div>
            `
        }


        ${
          !isCompleted
            ? `

              <div
                class="mas-new-injury-divider"
              ></div>

              ${getNewInjuryForm(athlete)}

            `
            : ""
        }

      </div>
    `;
  }

  function getLatestInjuryCard(injury, isCompleted = false) {
    injury = injury || {};

    return `

      <div
        class="mas-injury-card"
        data-injury-id="${escapeHTML(injury.id || "")}"
      >

        <div
          class="mas-injury-card-top"
        >

          <div>

            <strong>
              ${escapeHTML(injury.injury_title || "-")}
            </strong>


            <span>
              ${escapeHTML(injury.injury_date || "-")}
            </span>

          </div>


          <span
            class="
              injury-status
              ${getInjuryStatusClass(injury.injury_status)}
            "
          >

            ${escapeHTML(
              injury.injury_status_display || injury.injury_status || "-",
            )}

          </span>

        </div>


        <div
          class="mas-injury-details"
        >

          <span>

            <i class="fas fa-notes-medical"></i>

            ${escapeHTML(injury.injury_type || "-")}

          </span>


          <span>

            <i class="fas fa-bone"></i>

            ${escapeHTML(injury.body_part || "-")}

          </span>


          <span>

            <i class="fas fa-arrows-left-right"></i>

            ${escapeHTML(injury.side_display || injury.side || "-")}

          </span>


          <span>

            <i class="fas fa-triangle-exclamation"></i>

            ${escapeHTML(injury.severity_display || injury.severity || "-")}

          </span>

        </div>


        <div
          class="mas-injury-extra"
        >

          <div>

            <strong>
              Diagnosis
            </strong>

            <p>
              ${escapeHTML(injury.diagnosis || "-")}
            </p>

          </div>


          <div>

            <strong>
              Treatment
            </strong>

            <p>
              ${escapeHTML(injury.treatment || "-")}
            </p>

          </div>

        </div>

      </div>
    `;
  }

  function getNewInjuryForm(athlete) {
    athlete = athlete || {};

    return `

      <div
        class="mas-new-injury-form"
      >

        <div
          class="mas-injury-subtitle"
        >

          <i
            class="fas fa-notes-medical"
          ></i>

          Add New Injury Record

          <span
            class="new-record-badge"
          >
            New Record
          </span>

        </div>


        <div
          class="mas-injury-form-info"
        >

          <i
            class="fas fa-circle-info"
          ></i>

          Saving this form creates a
          <strong>new injury record</strong>.
          Previous injury records will not be modified.

        </div>


        <div
          class="mas-consultation-grid"
        >

          <!-- TITLE -->

          <div
            class="mas-form-group"
          >

            <label>

              Injury Title

              <span class="required">
                *
              </span>

            </label>


            <input
              type="text"
              id="injuryTitle"
              placeholder="e.g. Ankle Sprain"
            >

          </div>


          <!-- TYPE -->

          <div
            class="mas-form-group"
          >

            <label>

              Injury Type

              <span class="required">
                *
              </span>

            </label>


            <input
              type="text"
              id="injuryType"
              placeholder="e.g. Sprain, Fracture, Strain"
            >

          </div>


          <!-- BODY PART -->

          <div
            class="mas-form-group"
          >

            <label>

              Body Part

              <span class="required">
                *
              </span>

            </label>


            <input
              type="text"
              id="injuryBodyPart"
              placeholder="e.g. Ankle"
            >

          </div>


          <!-- SIDE -->

          <div
            class="mas-form-group"
          >

            <label>

              Side

              <span class="required">
                *
              </span>

            </label>


            <select
              id="injurySide"
            >

              <option value="">
                Select side
              </option>

              <option value="LEFT">
                Left
              </option>

              <option value="RIGHT">
                Right
              </option>

              <option value="BOTH">
                Both
              </option>

              <option value="CENTER">
                Center
              </option>

            </select>

          </div>


          <!-- SEVERITY -->

          <div
            class="mas-form-group"
          >

            <label>

              Severity

              <span class="required">
                *
              </span>

            </label>


            <select
              id="injurySeverity"
            >

              <option value="">
                Select severity
              </option>

              <option value="MINOR">
                Minor
              </option>

              <option value="MODERATE">
                Moderate
              </option>

              <option value="SEVERE">
                Severe
              </option>

              <option value="CRITICAL">
                Critical
              </option>

            </select>

          </div>


          <!-- CAUSE -->

          <div
            class="mas-form-group"
          >

            <label>
              Cause
            </label>


            <input
              type="text"
              id="injuryCause"
              placeholder="e.g. Training, Match, Fall"
            >

          </div>


          <!-- DATE -->

          <div
            class="mas-form-group"
          >

            <label>

              Injury Date

              <span class="required">
                *
              </span>

            </label>


            <input
              type="date"
              id="injuryDate"
            >

          </div>


          <!-- TIME -->

          <div
            class="mas-form-group"
          >

            <label>
              Injury Time
            </label>


            <input
              type="time"
              id="injuryTime"
            >

          </div>


          <!-- LOCATION -->

          <div
            class="mas-form-group"
          >

            <label>
              Location
            </label>


            <input
              type="text"
              id="injuryLocation"
              placeholder="e.g. College Ground"
            >

          </div>


          <!-- SYMPTOMS -->

          <div
            class="mas-form-group"
          >

            <label>
              Symptoms
            </label>


            <textarea
              id="injurySymptoms"
              rows="3"
              placeholder="Describe symptoms..."
            ></textarea>

          </div>


          <!-- DIAGNOSIS -->

          <div
            class="mas-form-group"
          >

            <label>

              Diagnosis

              <span class="required">
                *
              </span>

            </label>


            <textarea
              id="injuryDiagnosis"
              rows="3"
              placeholder="Enter injury diagnosis..."
            ></textarea>

          </div>


          <!-- TREATMENT -->

          <div
            class="mas-form-group"
          >

            <label>
              Treatment
            </label>


            <textarea
              id="injuryTreatment"
              rows="3"
              placeholder="Enter treatment provided..."
            ></textarea>

          </div>


          <!-- RECOVERY -->

          <div
            class="mas-form-group"
          >

            <label>
              Estimated Recovery (Days)
            </label>


            <input
              type="number"
              id="injuryRecoveryDays"
              min="0"
              placeholder="e.g. 14"
            >

          </div>


          <!-- EXPECTED RETURN -->

          <div
            class="mas-form-group"
          >

            <label>
              Expected Return Date
            </label>


            <input
              type="date"
              id="injuryExpectedReturn"
            >

          </div>


          <!-- ACTUAL RETURN -->

          <div
            class="mas-form-group"
          >

            <label>
              Actual Return Date
            </label>


            <input
              type="date"
              id="injuryActualReturn"
            >

          </div>


          <!-- HOSPITALIZATION -->

          <div
            class="mas-form-group"
          >

            <label>
              Hospitalization Required
            </label>


            <select
              id="injuryHospitalization"
            >

              <option value="false">
                No
              </option>

              <option value="true">
                Yes
              </option>

            </select>

          </div>


          <!-- SURGERY -->

          <div
            class="mas-form-group"
          >

            <label>
              Surgery Required
            </label>


            <select
              id="injurySurgery"
            >

              <option value="false">
                No
              </option>

              <option value="true">
                Yes
              </option>

            </select>

          </div>


          <!-- STATUS -->

          <div
            class="mas-form-group"
          >

            <label>

              Injury Status

              <span class="required">
                *
              </span>

            </label>


            <select
              id="injuryStatus"
            >

              <option value="ACTIVE">
                Under Treatment
              </option>

              <option value="RECOVERING">
                Recovering
              </option>

              <option value="REHABILITATION">
                Rehabilitation
              </option>

              <option value="RECOVERED">
                Recovered
              </option>

              <option value="RETURNED">
                Returned to Sport
              </option>

            </select>

          </div>


          <!-- NOTES -->

          <div
            class="mas-form-group"
          >

            <label>
              Notes
            </label>


            <textarea
              id="injuryNotes"
              rows="3"
              placeholder="Additional injury notes..."
            ></textarea>

          </div>

        </div>


        <div
          class="mas-injury-form-footer"
        >

          <button
            type="button"
            class="
              mas-btn
              mas-btn-success
            "
            id="saveAthleteInjury"

            data-athlete="${escapeHTML(athlete.athlete_id || "")}"

            data-registration="${escapeHTML(selectedCard?.dataset.id || "")}"
          >

            <i class="fas fa-save"></i>

            Save Injury Record

          </button>

        </div>

      </div>
    `;
  }

  function getInjuryStatusClass(status) {
    if (!status) {
      return "";
    }

    return String(status).toLowerCase().replaceAll("_", "-");
  }

  function bindMedicalCareEvents() {
    const btn = document.getElementById("saveAthleteMedicalCare");

    if (!btn) {
      return;
    }

    if (btn.dataset.bound === "true") {
      return;
    }

    btn.dataset.bound = "true";

    btn.addEventListener("click", saveAthleteMedicalCare);
  }

  function saveAthleteMedicalCare() {
    const saveBtn = document.getElementById("saveAthleteMedicalCare");

    if (!saveBtn) {
      return;
    }

    const patientId =
      window.currentPatientId || selectedCard?.dataset.patient || "";

    const athleteId = saveBtn.dataset.athlete || window.currentAthleteId || "";

    const registrationId =
      saveBtn.dataset.registration || selectedCard?.dataset.id || "";

    if (!patientId) {
      showToast("Patient ID is missing.", "error");
      return;
    }

    if (!registrationId) {
      showToast("Registration ID is missing.", "error");
      return;
    }

    if (!athleteId) {
      showToast("Athlete ID is missing.", "error");
      return;
    }

    const fitnessLevel =
      document.getElementById("athleteFitnessLevel")?.value || "";

    const medicalClearance =
      document.getElementById("athleteMedicalClearance")?.value || "";

    const clearanceDate =
      document.getElementById("athleteClearanceDate")?.value || "";

    const clearanceExpiry =
      document.getElementById("athleteClearanceExpiry")?.value || "";

    const injuryRisk =
      document.getElementById("athleteInjuryRisk")?.value || "";

    const teamPhysician =
      document.getElementById("athleteTeamPhysician")?.value || "";

    const physiotherapist =
      document.getElementById("athletePhysiotherapist")?.value || "";

    const nextMedicalCheckup =
      document.getElementById("athleteNextMedicalCheckup")?.value || "";

    const medicalRestrictions =
      document.getElementById("athleteMedicalRestrictions")?.value?.trim() ||
      "";

    const emergencyActionPlan =
      document.getElementById("athleteEmergencyActionPlan")?.value?.trim() ||
      "";

    /* VALIDATION */

    // if (!fitnessLevel) {
    //   showToast("Please select fitness level.", "error");
    //   return;
    // }

    // if (!medicalClearance) {
    //   showToast("Please select medical clearance.", "error");
    //   return;
    // }
    if (!fitnessLevel || fitnessLevel === "NOT SELECTED") {
      showToast("Please select fitness level.", "error");
      return;
    }

    if (!medicalClearance || medicalClearance === "NOT SELECTED") {
      showToast("Please select medical clearance.", "error");
      return;
    }

    pendingAthleteMedicalCare = {
      patient_id: patientId,
      registration_id: registrationId,
      athlete_id: athleteId,

      medical_clearance_status: medicalClearance,
      clearance_date: clearanceDate,
      clearance_expiry: clearanceExpiry,

      fitness_level: fitnessLevel,
      injury_risk: injuryRisk,

      team_physician: teamPhysician,
      physiotherapist: physiotherapist,

      next_medical_checkup: nextMedicalCheckup,

      medical_restrictions: medicalRestrictions,
      emergency_action_plan: emergencyActionPlan,
    };
    showToast(
      "Medical care information saved for this consultation.",
      "success",
    );

    console.log("Pending Medical Care:", pendingAthleteMedicalCare);
  }

  function bindInjuryEvents() {
    const btn = document.getElementById("saveAthleteInjury");

    if (!btn) {
      return;
    }

    if (btn.dataset.bound === "true") {
      return;
    }

    btn.dataset.bound = "true";

    btn.addEventListener("click", saveAthleteInjury);
  }

  function bindInjuryEditEvents() {
    const buttons = document.querySelectorAll(".mas-edit-injury");

    buttons.forEach((button) => {
      if (button.dataset.bound === "true") {
        return;
      }

      button.dataset.bound = "true";

      button.addEventListener("click", () => {
        const injuryId = button.dataset.injuryId;

        if (!injuryId) {
          showToast("Injury record ID is missing.", "error");

          return;
        }

        const injuries = Array.isArray(currentAthlete?.injuries)
          ? currentAthlete.injuries
          : [];

        const injury = injuries.find(
          (item) => String(item.id) === String(injuryId),
        );

        const injuryRecord =
          injury ||
          (currentAthlete?.latest_injury &&
          String(currentAthlete.latest_injury.id) === String(injuryId)
            ? currentAthlete.latest_injury
            : null);

        if (!injuryRecord) {
          showToast("Unable to load injury record.", "error");

          return;
        }

        populateInjuryFormForEdit(injuryRecord);
      });
    });
  }
  function populateInjuryFormForEdit(injury) {
    injury = injury || {};

    editingInjuryId = injury.id || null;

    const fields = {
      injuryTitle: injury.injury_title,

      injuryType: injury.injury_type,

      injuryBodyPart: injury.body_part,

      injurySide: injury.side_code || injury.side,

      injurySeverity: injury.severity_code || injury.severity,

      injuryCause: injury.cause,

      injuryDate: convertDisplayDateToInput(injury.injury_date),

      injuryTime: convertDisplayTimeToInput(injury.injury_time),

      injuryLocation: injury.location,

      injurySymptoms: injury.symptoms,

      injuryDiagnosis: injury.diagnosis,

      injuryTreatment: injury.treatment,

      injuryRecoveryDays: injury.estimated_recovery_days,

      injuryExpectedReturn: convertDisplayDateToInput(
        injury.expected_return_date,
      ),

      injuryActualReturn: convertDisplayDateToInput(injury.actual_return_date),

      injuryNotes: injury.notes,

      injuryStatus: injury.injury_status,
    };

    Object.entries(fields).forEach(([id, value]) => {
      const element = document.getElementById(id);

      if (element) {
        element.value = value ?? "";
      }
    });

    const hospitalization = document.getElementById("injuryHospitalization");

    if (hospitalization) {
      hospitalization.value = injury.hospitalization_required
        ? "true"
        : "false";
    }

    const surgery = document.getElementById("injurySurgery");

    if (surgery) {
      surgery.value = injury.surgery_required ? "true" : "false";
    }

    const saveBtn = document.getElementById("saveAthleteInjury");

    // if (saveBtn) {
    //   saveBtn.innerHTML = `
    //     <i class="fas fa-pen"></i>
    //     Update Injury Record
    //   `;
    // }

    // document.querySelector(".mas-new-injury-form")?.scrollIntoView({
    //   behavior: "smooth",
    //   block: "center",
    // });
  }

  async function saveAthleteInjury() {
    const saveBtn = document.getElementById("saveAthleteInjury");

    // Preserve whether this is an existing injury before changing anything
    const isEditing = !!editingInjuryId;

    try {
      const patientId =
        window.currentPatientId || selectedCard?.dataset.patient || "";

      const registrationId = selectedCard?.dataset.id || "";

      const athleteId =
        window.currentAthlete?.athlete_id || window.currentAthleteId || "";

      const athleteMedicalId = window.currentAthleteMedicalId || "";

      if (!patientId) {
        showToast("Patient ID is missing.", "error");
        return;
      }

      if (!registrationId) {
        showToast("Registration ID is missing.", "error");
        return;
      }

      if (!athleteId) {
        showToast("Athlete ID is missing.", "error");
        return;
      }

      if (!athleteMedicalId) {
        showToast("Athlete medical profile is missing.", "error");
        return;
      }

      const injuryTitle =
        document.getElementById("injuryTitle")?.value.trim() || "";

      const injuryType =
        document.getElementById("injuryType")?.value.trim() || "";

      const bodyPart =
        document.getElementById("injuryBodyPart")?.value.trim() || "";

      const side = document.getElementById("injurySide")?.value.trim() || "";

      const severity = document.getElementById("injurySeverity")?.value || "";

      const cause = document.getElementById("injuryCause")?.value.trim() || "";

      const injuryDate = document.getElementById("injuryDate")?.value || "";

      const injuryTime = document.getElementById("injuryTime")?.value || "";

      const location =
        document.getElementById("injuryLocation")?.value.trim() || "";

      const symptoms =
        document.getElementById("injurySymptoms")?.value.trim() || "";

      const diagnosis =
        document.getElementById("injuryDiagnosis")?.value.trim() || "";

      const treatment =
        document.getElementById("injuryTreatment")?.value.trim() || "";

      const recoveryDays =
        document.getElementById("injuryRecoveryDays")?.value || "";

      const expectedReturnDate =
        document.getElementById("injuryExpectedReturn")?.value || "";

      const actualReturnDate =
        document.getElementById("injuryActualReturn")?.value || "";

      const hospitalization =
        document.getElementById("injuryHospitalization")?.value === "true";

      const surgery =
        document.getElementById("injurySurgery")?.value === "true";

      const injuryStatus =
        document.getElementById("injuryStatus")?.value || "ACTIVE";

      const notes = document.getElementById("injuryNotes")?.value.trim() || "";

      if (!injuryTitle) {
        showToast("Injury title is required.", "error");
        return;
      }

      if (!injuryType) {
        showToast("Injury type is required.", "error");
        return;
      }

      if (!bodyPart) {
        showToast("Body part is required.", "error");
        return;
      }

      if (!side) {
        showToast("Please select injury side.", "error");

        document.getElementById("injurySide")?.focus();

        return;
      }

      if (!severity) {
        showToast("Please select injury severity.", "error");
        return;
      }

      if (!injuryDate) {
        showToast("Injury date is required.", "error");
        return;
      }

      if (!diagnosis) {
        showToast("Injury diagnosis is required.", "error");
        return;
      }

      const payload = {
        athlete_id: athleteId,

        athlete_medical_id: athleteMedicalId,

        patient_id: patientId,

        registration_id: registrationId,

        injury_title: injuryTitle,

        injury_type: injuryType,

        body_part: bodyPart,

        side: side,

        severity: severity,

        cause: cause,

        injury_date: injuryDate,

        injury_time: injuryTime,

        location: location,

        symptoms: symptoms,

        diagnosis: diagnosis,

        treatment: treatment,

        estimated_recovery_days: Number(recoveryDays || 0),

        expected_return_date: expectedReturnDate,

        actual_return_date: actualReturnDate,

        hospitalization_required: hospitalization,

        surgery_required: surgery,

        injury_status: injuryStatus,

        notes: notes,
        athlete_medical_care: pendingAthleteMedicalCare,
      };

      if (editingInjuryId) {
        payload.injury_id = editingInjuryId;
      }

      if (saveBtn) {
        saveBtn.disabled = true;

        saveBtn.innerHTML = `
        <i class="fas fa-spinner fa-spin"></i>
        ${isEditing ? "Updating..." : "Saving..."}
      `;
      }

      pendingAthleteInjury = payload;

      console.log("Pending Injury:", pendingAthleteInjury);

      showToast(
        isEditing
          ? "Injury changes saved for this consultation."
          : "Injury saved for this consultation.",
        "success",
      );

      editingInjuryId = null;

      if (saveBtn) {
        saveBtn.disabled = false;

        saveBtn.innerHTML = `
        <i class="fas fa-save"></i>
        Save Injury Record
      `;
      }
    } catch (error) {
      console.error("Save athlete injury error:", error);

      showToast(error.message || "Failed to save athlete injury.", "error");
    }
  }

  function initializeChoicesSelect(selectId, placeholder = "Select an option") {
    const select = document.getElementById(selectId);

    if (!select) {
      return;
    }

    if (select.dataset.choicesInitialized === "true") {
      return;
    }

    if (typeof Choices === "undefined") {
      console.error("Choices.js is not loaded.");
      return;
    }

    new Choices(select, {
      searchEnabled: false,
      itemSelectText: "",
      shouldSort: false,
      allowHTML: false,
      placeholder: true,
      placeholderValue: placeholder,
      position: "bottom",
    });

    select.dataset.choicesInitialized = "true";
  }

  function initMedicalCareChoices() {
    initializeChoicesSelect("athleteFitnessLevel", "Select fitness level");

    initializeChoicesSelect(
      "athleteMedicalClearance",
      "Select medical clearance",
    );

    initializeChoicesSelect("athleteInjuryRisk", "Select injury risk");

    initializeChoicesSelect("athleteTeamPhysician", "Select team physician");

    initializeChoicesSelect("athletePhysiotherapist", "Select physiotherapist");
  }

  function initInjuryChoices() {
    initializeChoicesSelect("injurySide", "Select side");

    initializeChoicesSelect("injurySeverity", "Select severity");

    initializeChoicesSelect("injuryHospitalization", "Select option");

    initializeChoicesSelect("injurySurgery", "Select option");

    initializeChoicesSelect("injuryStatus", "Select injury status");
  }

  function initMedicalDateFields() {
    const dateFieldIds = [
      "athleteClearanceDate",

      "athleteClearanceExpiry",

      "athleteNextMedicalCheckup",

      "injuryDate",

      "injuryExpectedReturn",

      "injuryActualReturn",

      /* Consultation */

      "consultFollowUpDate",
    ];

    dateFieldIds.forEach((id) => {
      const input = document.getElementById(id);

      if (!input) {
        return;
      }

      input.addEventListener("keydown", function (event) {
        const allowedKeys = [
          "Tab",
          "ArrowLeft",
          "ArrowRight",
          "ArrowUp",
          "ArrowDown",
        ];

        if (allowedKeys.includes(event.key)) {
          return;
        }
      });
    });
  }

  function initDynamicFormControls() {
    initMedicalCareChoices();

    initInjuryChoices();

    initMedicalDateFields();
  }
  function initVisitTypeChoices() {
    const select = document.getElementById("consultVisitType");

    if (!select) {
      return;
    }

    if (select.dataset.choicesInitialized === "true") {
      toggleFollowUpDate(select.value);

      return;
    }

    if (typeof Choices === "undefined") {
      console.error("Choices.js is not loaded.");

      return;
    }

    new Choices(select, {
      searchEnabled: false,

      itemSelectText: "",

      shouldSort: false,

      allowHTML: false,

      placeholder: true,

      placeholderValue: "Select visit type",

      position: "bottom",
    });

    select.dataset.choicesInitialized = "true";

    toggleFollowUpDate(select.value);
  }

  document.addEventListener("change", (event) => {
    if (event.target.id !== "consultVisitType") {
      return;
    }

    toggleFollowUpDate(event.target.value);
  });

  function toggleFollowUpDate(visitType) {
    const wrapper = document.getElementById("consultFollowUpDateWrapper");

    const dateInput = document.getElementById("consultFollowUpDate");

    if (!wrapper || !dateInput) {
      return;
    }

    if (visitType === "FOLLOW_UP") {
      wrapper.style.display = "flex";

      const today = new Date();

      const localDate = new Date(
        today.getTime() - today.getTimezoneOffset() * 60000,
      )
        .toISOString()
        .split("T")[0];

      dateInput.min = localDate;
    } else {
      wrapper.style.display = "none";

      if (!dateInput.disabled) {
        dateInput.value = "";
      }
    }
  }

  document.addEventListener("click", async (event) => {
    const btn = event.target.closest(".mas-checkin");

    if (!btn) {
      return;
    }

    const registrationId = btn.dataset.id;

    if (!registrationId) {
      showToast("Registration ID not found.", "error");

      return;
    }

    const originalHTML = btn.innerHTML;

    btn.disabled = true;

    btn.innerHTML = `
        <i class="fas fa-spinner fa-spin"></i>
        Checking In...
      `;

    try {
      const data = await apiRequest(
        `/medical/Register-patient/${registrationId}/check-in/`,
        "POST",
      );

      const item = allItems.find(
        (el) => String(el.dataset.id) === String(registrationId),
      );

      if (!item) {
        throw new Error("Patient card not found.");
      }

      updatePatientCardStatus(item, "IN_PROGRESS");

      const patientId = item.dataset.patient;

      await loadPatientDetails(patientId, registrationId, "IN_PROGRESS");

      if (data.counts) {
        updateOverviewCounts(data.counts);

        updateTabCounts(data.counts);
      }

      filterAndPaginate();

      showToast("Patient checked in successfully.", "success");
    } catch (error) {
      console.error("Check-in error:", error);

      showToast(error.message || "Unable to check in patient.", "error");

      btn.disabled = false;

      btn.innerHTML = originalHTML;
    }
  });

  async function handleCompleteConsultation(event) {
    const btn = event.currentTarget;

    const registrationId = btn.dataset.id;

    const visitType = document.getElementById("consultVisitType")?.value || "";

    const diagnosis =
      document.getElementById("consultDiagnosis")?.value?.trim() || "";

    const treatment =
      document.getElementById("consultTreatment")?.value?.trim() || "";

    const medications =
      document.getElementById("consultMedications")?.value?.trim() || "";

    const notes = document.getElementById("consultNotes")?.value?.trim() || "";

    const followUpDate =
      document.getElementById("consultFollowUpDate")?.value || "";

    const followUp = visitType === "FOLLOW_UP";

    if (!visitType) {
      showToast("Visit type is required.", "error");

      return;
    }

    if (!diagnosis) {
      showToast("Diagnosis is required.", "error");

      return;
    }

    if (!treatment) {
      showToast("Treatment is required.", "error");

      return;
    }

    if (followUp && !followUpDate) {
      showToast("Please select follow-up date.", "error");

      return;
    }

    const originalHTML = btn.innerHTML;

    btn.disabled = true;

    btn.innerHTML = `
      <i class="fas fa-spinner fa-spin"></i>
      Completing...
    `;

    try {
      const data = await apiRequest(
        `/medical/patient-status/${registrationId}/complete/`,
        "POST",
        {
          status: "COMPLETED",

          visit_type: visitType,

          diagnosis: diagnosis,

          treatment: treatment,

          medications: medications,

          notes: notes,

          follow_up_required: followUp,

          follow_up_date: followUpDate,

          athlete_medical_care: pendingAthleteMedicalCare || null,

          athlete_injury: pendingAthleteInjury || null,
        },
      );

      const item = allItems.find(
        (el) => String(el.dataset.id) === String(registrationId),
      );

      if (!item) {
        throw new Error("Patient card not found.");
      }

      updatePatientCardStatus(item, "COMPLETED");

      item.classList.add("active");

      const patientId = item.dataset.patient;

      await loadPatientDetails(patientId, registrationId, "COMPLETED");

      if (data.counts) {
        updateOverviewCounts(data.counts);

        updateTabCounts(data.counts);
      }

      filterAndPaginate();

      showToast("Consultation completed successfully.", "success");
    } catch (error) {
      console.error("Complete consultation error:", error);

      showToast(error.message || "Unable to complete consultation.", "error");

      btn.disabled = false;

      btn.innerHTML = originalHTML;
    }
  }


    function showAdmitRemarkModal(onConfirm) {
    const container = document.getElementById("mas-toast-container");

    if (!container) {
      return;
    }

    container.querySelector(".mas-toast-admit-modal")?.remove();

    const modal = document.createElement("div");

    modal.className = "mas-toast mas-toast-reject-modal mas-toast-admit-modal";

    modal.innerHTML = `
      <div class="mas-toast-reject-content">
        <div class="mas-toast-reject-icon">
          <i class="fas fa-bed-pulse"></i>
        </div>
        <div class="mas-toast-reject-text">
          <strong>Request Admission</strong>
          <p>Add a short admission remark for the Rooms team (optional).</p>
        </div>
        <div class="mas-toast-reject-input">
          <textarea id="admitRemark" placeholder="Reason for admission..." rows="3"></textarea>
        </div>
        <div class="mas-toast-reject-actions">
          <button type="button" class="mas-toast-btn mas-toast-btn-cancel">Cancel</button>
          <button type="button" class="mas-toast-btn mas-toast-btn-confirm">Send Request</button>
        </div>
      </div>
    `;

    container.appendChild(modal);

    setTimeout(() => {
      modal.classList.add("mas-toast-show");
      modal.querySelector("#admitRemark")?.focus();
    }, 50);

    modal.querySelector(".mas-toast-btn-cancel")?.addEventListener("click", () => {
      modal.classList.remove("mas-toast-show");
      setTimeout(() => modal.remove(), 300);
    });

    modal.querySelector(".mas-toast-btn-confirm")?.addEventListener("click", () => {
      const remark = modal.querySelector("#admitRemark")?.value || "";

      if (onConfirm) {
        onConfirm(remark);
      }

      modal.classList.remove("mas-toast-show");
      setTimeout(() => modal.remove(), 300);
    });
  }

  async function handleAdmitRequest(event) {
    const btn = event.currentTarget;
    const registrationId = btn.dataset.id;

    showAdmitRemarkModal(async (remark) => {
      const originalHTML = btn.innerHTML;

      btn.disabled = true;
      btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Sending...`;

      try {
        const response = await apiRequest(
          `/medical/patients/patient-status/${registrationId}/admit-request/`,
          "POST",
          { remark: remark.trim() },
        );
        btn.outerHTML = `
          <div class="mas-status-message in-progress">
            <i class="fas fa-hourglass-half"></i>
            Admission Requested
          </div>
        `;

         const item = document.querySelector(
          `.mas-patient-item[data-id="${registrationId}"]`,
        );

        if (item) {
          item.dataset.admissionStatus =
            response.admission_status || "REQUESTED";
        }

        if (response.counts) {
          updateTabCounts(response.counts);
          updateOverviewCounts(response.counts);
        }

        filterAndPaginate();


        showToast("Admission request sent to Rooms.", "success");
      } catch (error) {
        console.error("Admit request error:", error);

        showToast(error.message || "Unable to request admission.", "error");

        btn.disabled = false;
        btn.innerHTML = originalHTML;
      }
    });
  }

  function updatePatientCardStatus(item, newStatus) {
    if (!item) {
      return;
    }

    item.dataset.status = newStatus;

    const badge =
      item.querySelector(".mas-status-badge") ||
      item.querySelector(".mas-patient-status") ||
      item.querySelector(".mas-status");

    if (!badge) {
      return;
    }

    const statusText = {
      WAITING: "Waiting",

      IN_PROGRESS: "In Progress",

      COMPLETED: "Completed",

      CANCELLED: "Cancelled",
    };

    badge.textContent = statusText[newStatus] || newStatus;

    badge.classList.remove("waiting", "in-progress", "completed", "cancelled");

    badge.classList.add(newStatus.toLowerCase().replaceAll("_", "-"));
  }

  function updateOverviewCounts(counts) {
    if (!counts) {
      return;
    }

    const total = document.getElementById("totalCount");

    const waiting = document.getElementById("waitingCount");

    const inProgress = document.getElementById("inProgressCount");

    const completed = document.getElementById("completedCount");

    if (total) {
      total.textContent = counts.total ?? 0;
    }

    if (waiting) {
      waiting.textContent = counts.waiting ?? 0;
    }

    if (inProgress) {
      inProgress.textContent = counts.in_progress ?? 0;
    }

    if (completed) {
      completed.textContent = counts.completed ?? 0;
    }
  }

  function updateTabCounts(counts) {
    if (!counts) {
      return;
    }

    const countMap = {
      all: counts.total ?? 0,

      WAITING: counts.waiting ?? 0,

      IN_PROGRESS: counts.in_progress ?? 0,

      COMPLETED: counts.completed ?? 0,

      CANCELLED: counts.cancelled ?? 0,

      ADMITTED: counts.admitted ?? 0,
    };

    document.querySelectorAll(".mas-filter-tab").forEach((tab) => {
      const status = tab.dataset.status;

      const span = tab.querySelector(".mas-tab-count");

      if (span && countMap[status] !== undefined) {
        span.textContent = countMap[status];
      }
    });
  }

  document.addEventListener("click", (event) => {
    const btn = event.target.closest(".mas-accept");

    if (!btn) {
      return;
    }

    const appointmentId = btn.dataset.id;

    const timeInput = document.querySelector(
      `[data-appointment-time="${appointmentId}"]`,
    );

    const appointmentTime = timeInput?.value || "";

    if (!appointmentTime) {
      showToast("Please select appointment time.", "error");

      return;
    }

    updateAppointmentStatus(
      appointmentId,
      "CONFIRMED",
      btn,
      "",
      appointmentTime,
    );
  });

  document.addEventListener("click", (event) => {
    const btn = event.target.closest(".mas-reject");

    if (!btn) {
      return;
    }

    showRejectReasonModal(
      "Reject Appointment",
      "Please provide a reason for cancellation (Optional):",
      (reason) => {
        updateAppointmentStatus(
          btn.dataset.id,
          "CANCELLED",
          btn,
          reason.trim(),
        );
      },
    );
  });

  async function updateAppointmentStatus(
    registrationId,
    status,
    button,
    reason,
    appointmentTime = null,
  ) {
    const originalHTML = button.innerHTML;

    button.disabled = true;

    button.innerHTML = `
      <i class="fas fa-spinner fa-spin"></i>
      Updating...
    `;

    const payload = {
      status,

      cancellation_reason: reason || "",
    };

    if (status === "CONFIRMED") {
      payload.appointment_time = appointmentTime;
    }

    try {
      const data = await apiRequest(
        `/medical/appointments/${registrationId}/status/`,
        "POST",
        payload,
      );

      const item = allItems.find(
        (el) => String(el.dataset.id) === String(registrationId),
      );

      if (item) {
        updatePatientCardStatus(item, status);
      }

      if (data.counts) {
        updateOverviewCounts(data.counts);

        updateTabCounts(data.counts);
      }

      filterAndPaginate();

      showToast(
        status === "CONFIRMED"
          ? "Appointment Confirmed."
          : "Appointment Cancelled.",
        "success",
      );
    } catch (error) {
      console.error("Appointment status error:", error);

      showToast(error.message || "Unable to update appointment.", "error");
    } finally {
      button.disabled = false;

      button.innerHTML = originalHTML;
    }
  }

  function showRejectReasonModal(title, message, onConfirm) {
    const container = document.getElementById("mas-toast-container");

    if (!container) {
      return;
    }

    container.querySelector(".mas-toast-reject-modal")?.remove();

    const modal = document.createElement("div");

    modal.className = "mas-toast mas-toast-reject-modal";

    modal.innerHTML = `

      <div
        class="mas-toast-reject-content"
      >

        <div
          class="mas-toast-reject-icon"
        >

          <i
            class="fas fa-times-circle"
          ></i>

        </div>


        <div
          class="mas-toast-reject-text"
        >

          <strong>
            ${escapeHTML(title)}
          </strong>


          <p>
            ${escapeHTML(message)}
          </p>

        </div>


        <div
          class="mas-toast-reject-input"
        >

          <textarea
            id="rejectReason"
            placeholder="Enter cancellation reason..."
            rows="3"
          ></textarea>

        </div>


        <div
          class="mas-toast-reject-actions"
        >

          <button
            type="button"
            class="
              mas-toast-btn
              mas-toast-btn-cancel
            "
          >
            Cancel
          </button>


          <button
            type="button"
            class="
              mas-toast-btn
              mas-toast-btn-confirm
            "
          >
            Reject
          </button>

        </div>

      </div>
    `;

    container.appendChild(modal);

    setTimeout(() => {
      modal.classList.add("mas-toast-show");

      modal.querySelector("#rejectReason")?.focus();
    }, 50);

    modal
      .querySelector(".mas-toast-btn-cancel")
      ?.addEventListener("click", () => {
        modal.classList.remove("mas-toast-show");

        setTimeout(() => modal.remove(), 300);
      });

    modal
      .querySelector(".mas-toast-btn-confirm")
      ?.addEventListener("click", () => {
        const reason = modal.querySelector("#rejectReason")?.value || "";

        if (onConfirm) {
          onConfirm(reason);
        }

        modal.classList.remove("mas-toast-show");

        setTimeout(() => modal.remove(), 300);
      });
  }

  /* =========================================================
     TOAST
  ========================================================= */

  function showToast(message, type = "success") {
    const container = document.getElementById("mas-toast-container");

    if (!container) {
      console.warn(message);

      return;
    }

    const toast = document.createElement("div");

    toast.className = `mas-toast mas-toast-${type}`;

    const icon =
      type === "success" ? "fa-circle-check" : "fa-circle-exclamation";

    toast.innerHTML = `

      <i
        class="fas ${icon}"
      ></i>

      <span>
        ${escapeHTML(message)}
      </span>

    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.classList.add("show");
    }, 50);

    setTimeout(() => {
      toast.classList.remove("show");

      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  filterAndPaginate();
});

const choicesInstances = {};

function initChoicesSelect(selectId, searchEnabled = false) {
  const select = document.getElementById(selectId);

  if (!select) {
    return;
  }

  if (choicesInstances[selectId]) {
    try {
      choicesInstances[selectId].destroy();
    } catch (error) {
      console.warn(error);
    }

    choicesInstances[selectId] = null;
  }

  choicesInstances[selectId] = new Choices(select, {
    searchEnabled: searchEnabled,

    shouldSort: false,

    itemSelectText: "",

    allowHTML: false,

    searchPlaceholderValue: "Search...",

    noResultsText: "No results found",

    noChoicesText: "No choices available",

    position: "bottom",
  });
}

function initAllChoices() {
  initChoicesSelect("athleteFitnessLevel", false);
  initChoicesSelect("athleteMedicalClearance", false);
  initChoicesSelect("athleteInjuryRisk", false);
  initChoicesSelect("athleteTeamPhysician", true);

  initChoicesSelect("athletePhysiotherapist", true);

  initChoicesSelect("typeFilter", false);
}

const datePickerInstances = {};

function initDatePicker(inputId) {
  const input = document.getElementById(inputId);

  if (!input) {
    return;
  }

  /*
   * Check Flatpickr is loaded
   */

  if (typeof flatpickr === "undefined") {
    console.error("Flatpickr is not loaded.");

    return;
  }

  /*
   * Destroy old instance
   */

  if (datePickerInstances[inputId]) {
    try {
      datePickerInstances[inputId].destroy();
    } catch (error) {
      console.warn(error);
    }
  }

  /*
   * Initialize Flatpickr
   */

  datePickerInstances[inputId] = flatpickr(input, {
    dateFormat: "Y-m-d",

    altInput: true,

    altFormat: "d-m-Y",

    allowInput: true,

    disableMobile: true,
  });
}

function initAllDatePickers() {
  initDatePicker("athleteClearanceDate");

  initDatePicker("athleteClearanceExpiry");

  initDatePicker("athleteNextMedicalCheckup");

  initDatePicker("followUpDate");
}

function initDatePickers() {
  if (typeof flatpickr === "undefined") {
    console.error("Flatpickr is not loaded");
    return;
  }

  const dateInputs = document.querySelectorAll(
    `
      input[type="date"],
      input.mas-date-picker,
      #followUpDate,
      #athleteClearanceDate,
      #athleteClearanceExpiry,
      #athleteNextMedicalCheckup,
      #injuryDate,
      #expectedReturnDate,
      #actualReturnDate
    `,
  );

  dateInputs.forEach((input) => {
    if (input._flatpickr) {
      input._flatpickr.destroy();
    }

    flatpickr(input, {
      dateFormat: "Y-m-d",
      altInput: true,
      altFormat: "d-m-Y",
      allowInput: true,
      disableMobile: true,
    });
  });
}
