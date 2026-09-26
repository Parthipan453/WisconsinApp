//************************************* swetha's code ***********************************************8

const dateEl = document.getElementById("currentDate");

if (dateEl) {
  dateEl.textContent = new Date().toLocaleDateString("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

document.addEventListener("DOMContentLoaded", function () {
  const page = document.getElementById("regPage");

  if (!page) return;
  const urls = {
    search: page.dataset.searchUrl,
    schedule: page.dataset.scheduleUrl,
    register: page.dataset.registerUrl,
    queue: page.dataset.queueUrl,
    appointment: page.dataset.appointmentUrl,
    appointmentStatus: page.dataset.appointmentStatusUrl,
    calendar: page.dataset.calendarUrl,
    ambulance: page.dataset.ambulanceUrl,
    ambulanceStatus: regPage.dataset.ambulanceStatusUrl,
    ambulanceAvailability: page.dataset.ambulanceAvailabilityUrl,
  };
  console.log("ALL URLS:", urls);

  console.log("AMBULANCE AVAILABILITY URL:", urls.ambulanceAvailability);
  console.log("Registration URLs:", urls);

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);

    if (parts.length === 2) {
      return parts.pop().split(";").shift();
    }

    return "";
  }

  const csrftoken = getCookie("csrftoken");
  const state = {
    selectedPatient: null,
    selectedSchedule: null,
    registrationType: "WALK_IN",

    arrivedByAmbulance: false,
    selectedAmbulance: null,

    ambulanceList: [],

    schedulePage: 1,
    scheduleQuery: "",
    scheduleTotalPages: 1,
    scheduleFilter: "ALL",

    queueDate: new Date().toISOString().split("T")[0],
    queuePage: 1,
    queueTotalPages: 1,

    appointmentStatus: "PENDING",
    appointmentQuery: "",
    appointmentPage: 1,
    appointmentTotalPages: 1,
  };

  function initials(name) {
    if (!name) return "?";

    return name
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((word) => word[0].toUpperCase())
      .join("");
  }

  function debounce(fn, wait) {
    let timer;

    return function (...args) {
      clearTimeout(timer);

      timer = setTimeout(() => {
        fn.apply(this, args);
      }, wait);
    };
  }

  function showToast(title, message, type = "success") {
    const toast = document.createElement("div");

    toast.className = `reg-toast reg-toast--${type}`;

    toast.innerHTML = `
      <div class="reg-toast__title">
        ${title}
      </div>

      <div class="reg-toast__message">
        ${message}
      </div>
    `;

    document.body.appendChild(toast);

    requestAnimationFrame(() => {
      toast.classList.add("show");
    });

    setTimeout(() => {
      toast.classList.remove("show");

      setTimeout(() => {
        toast.remove();
      }, 300);
    }, 3000);
  }

  function formatDate(dateString) {
    if (!dateString) {
      return "—";
    }

    const date = new Date(dateString + "T00:00:00");

    return date.toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "long",
      year: "numeric",
    });
  }

  function formatTime(timeValue) {
    if (!timeValue) {
      return "—";
    }
    const parts = timeValue.split(":");

    const hours = Number(parts[0]);
    const minutes = Number(parts[1]);

    if (Number.isNaN(hours) || Number.isNaN(minutes)) {
      return timeValue;
    }

    const date = new Date();

    date.setHours(hours, minutes, 0, 0);

    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
  }
  function isPastAppointmentTime(timeValue, appointmentDate) {
    if (!timeValue || !appointmentDate) {
      return true;
    }

    const today = new Date();

    const todayDate =
      today.getFullYear() +
      "-" +
      String(today.getMonth() + 1).padStart(2, "0") +
      "-" +
      String(today.getDate()).padStart(2, "0");
    if (appointmentDate > todayDate) {
      return false;
    }
    if (appointmentDate < todayDate) {
      return true;
    }

    const [hours, minutes] = timeValue.split(":").map(Number);

    const selectedTotalMinutes = hours * 60 + minutes;

    const currentTotalMinutes = today.getHours() * 60 + today.getMinutes();

    return selectedTotalMinutes < currentTotalMinutes;
  }

  function setAppointmentTimeMin() {
    const timeInputs = document.querySelectorAll(".appointment-time-input");

    if (!timeInputs.length) {
      return;
    }

    const now = new Date();

    const todayDate =
      now.getFullYear() +
      "-" +
      String(now.getMonth() + 1).padStart(2, "0") +
      "-" +
      String(now.getDate()).padStart(2, "0");

    const currentTime =
      String(now.getHours()).padStart(2, "0") +
      ":" +
      String(now.getMinutes()).padStart(2, "0");

    timeInputs.forEach((input) => {
      const card = input.closest(".appointment-card");

      const appointmentDate = card?.dataset.appointmentDate;

      if (appointmentDate === todayDate) {
        input.min = currentTime;
      } else {
        input.removeAttribute("min");
      }
    });
  }
  function statusClass(status) {
    return (
      {
        WAITING: "reg-status--waiting",
        IN_PROGRESS: "reg-status--progress",
        COMPLETED: "reg-status--completed",
        CANCELLED: "reg-status--cancelled",
      }[status] || "reg-status--waiting"
    );
  }

  function appointmentStatusClass(status) {
    return (
      {
        PENDING: "appointment-status--pending",
        CONFIRMED: "appointment-status--confirmed",
        ARRIVED: "appointment-status--arrived",
        IN_PROGRESS: "appointment-status--in-progress",
        CANCELLED: "appointment-status--cancelled",
        NOT_ARRIVED: "appointment-status--not-arrived",
      }[status] || ""
    );
  }

  const patientInput = document.getElementById("patientSearchInput");

  const patientResults = document.getElementById("patientSearchResults");

  const selectedPatientBox = document.getElementById("selectedPatientBox");

  function runPatientSearch(q) {
    if (!q || q.length < 2) {
      patientResults.innerHTML = "";

      return;
    }

    fetch(`${urls.search}?q=${encodeURIComponent(q)}`)
      .then((response) => response.json())

      .then((data) => {
        renderPatientResults(data.results || []);
      })

      .catch(() => {
        patientResults.innerHTML = `
          <div class="reg-table-empty">
            Search failed. Try again.
          </div>
        `;
      });
  }

  function renderPatientResults(results) {
    if (!results.length) {
      patientResults.innerHTML = `
        <div class="reg-table-empty">
          No matching patient found.
        </div>
      `;

      return;
    }

    patientResults.innerHTML = results
      .map(
        (patient) => `
          <div class="reg-result-card">

            <div class="reg-result-info">

              <div class="reg-avatar">
                ${initials(patient.name)}
              </div>

              <div>

                <div class="reg-result-name">
                  ${patient.name}

                  <small>
                    ${patient.patient_number}
                  </small>
                </div>

                <div class="reg-result-sub">

                    ${patient.patient_type}

                    ${
                      patient.is_athlete
                        ? `
                          <span class="athlete-badge">
                            <i class="fas fa-person-running"></i>
                            Athlete
                          </span>
                        `
                        : ""
                    }

                    &middot;

                    ${patient.phone || "—"}

                </div>

              </div>

            </div>

            <button
              type="button"
              class="reg-btn reg-btn--primary"
              data-select-patient='${JSON.stringify(patient)}'
            >
              Select patient
            </button>

          </div>
        `,
      )
      .join("");

    patientResults
      .querySelectorAll("[data-select-patient]")
      .forEach((button) => {
        button.addEventListener("click", () => {
          const patient = JSON.parse(button.dataset.selectPatient);

          selectPatient(patient);
        });
      });
  }

  function selectPatient(patient) {
    state.selectedPatient = patient;

    selectedPatientBox.classList.remove("reg-selected-box--empty");

    selectedPatientBox.innerHTML = `
      <button
        type="button"
        class="reg-selected-close"
        id="clearSelectedPatient"
      >
        <i class="fas fa-times"></i>
      </button>

      <i class="fas fa-user-check"></i>

      <span>

        <strong>
          ${patient.name}
        </strong>

        <br>

        <small>
          Patient ID: ${patient.patient_number}
        </small>

        <br>

        <small>
            ${patient.patient_type}

            ${
              patient.is_athlete
                ? `
                  <span class="athlete-badge">
                    <i class="fas fa-person-running"></i>
                    Athlete
                  </span>
                `
                : ""
            }
        </small>
      </span>
    `;

    document
      .getElementById("clearSelectedPatient")
      .addEventListener("click", clearSelectedPatient);

    patientResults.innerHTML = "";

    patientInput.value = "";

    updateRegistrationDetails();
  }

  function clearSelectedPatient() {
    state.selectedPatient = null;

    selectedPatientBox.classList.add("reg-selected-box--empty");

    selectedPatientBox.innerHTML = `
      <i class="fas fa-user"></i>

      <span>
        No patient selected yet.
        Search above to select one.
      </span>
    `;

    patientInput.value = "";

    patientResults.innerHTML = "";

    updateRegistrationDetails();
  }

  if (patientInput) {
    patientInput.addEventListener(
      "input",
      debounce((event) => {
        runPatientSearch(event.target.value.trim());
      }, 300),
    );
  }

  const scheduleInput = document.getElementById("scheduleSearchInput");
  const scheduleGrid = document.getElementById("scheduleGrid");
  const scheduleCount = document.getElementById("scheduleCount");
  const schedulePrev = document.getElementById("schedulePrev");
  const scheduleNext = document.getElementById("scheduleNext");
  const scheduleFilter = document.getElementById("scheduleFilter");
  async function loadSchedules() {
    if (!scheduleGrid) {
      return;
    }

    scheduleGrid.innerHTML = `
    <div class="reg-table-empty">
      Loading schedules…
    </div>
  `;

    const params = new URLSearchParams({
      q: state.scheduleQuery || "",
      page: state.schedulePage || 1,
      shift: state.scheduleFilter || "ALL",
    });

    try {
      const response = await fetch(`${urls.schedule}?${params.toString()}`, {
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      });

      const contentType = response.headers.get("content-type") || "";

      if (!response.ok) {
        const errorText = await response.text();

        console.error("Schedule API HTTP error:", response.status, errorText);

        throw new Error(
          `Schedule request failed with status ${response.status}`,
        );
      }

      if (!contentType.includes("application/json")) {
        const responseText = await response.text();

        console.error("Schedule API returned non-JSON:", responseText);

        throw new Error("Server returned HTML instead of JSON.");
      }

      const data = await response.json();

      console.log("SCHEDULE DATA:", data);

      renderSchedules(data);
    } catch (error) {
      console.error("Schedule load error:", error);

      scheduleGrid.innerHTML = `
      <div class="reg-table-empty">
        Could not load schedules.
      </div>
    `;

      if (scheduleCount) {
        scheduleCount.textContent = "Unable to load schedules";
      }
    }
  }

  function renderSchedules(data) {
    const results = data.results || [];

    state.scheduleTotalPages = data.total_pages || 1;

    if (!results.length) {
      scheduleGrid.innerHTML = `
        <div class="reg-table-empty">
          No doctors match your search.
        </div>
      `;
    } else {
      scheduleGrid.innerHTML = results
        .map((schedule) => {
          const isSelected =
            state.selectedSchedule && state.selectedSchedule.id === schedule.id;

          return `
              <div
                class="
                  reg-doctor-card
                  ${isSelected ? "reg-doctor-card--selected" : ""}
                "
                data-select-schedule='${JSON.stringify(schedule)}'
              >

                <div class="reg-doctor-avatar">
                  <i class="fas fa-user-doctor"></i>
                </div>

                <div class="reg-doctor-name">
                  ${schedule.doctor_name}
                </div>

                <div class="reg-doctor-dept">
                  ${schedule.department}
                </div>

                <div class="reg-doctor-meta">
                  ${schedule.start_time}
                  -
                  ${schedule.end_time}

                  <br>

                  Room
                  ${schedule.room_number || "—"}
                </div>

                <button
                  type="button"
                  class="reg-doctor-select"
                >
                  Select
                </button>

              </div>
            `;
        })
        .join("");

      scheduleGrid
        .querySelectorAll("[data-select-schedule]")
        .forEach((card) => {
          card.addEventListener("click", () => {
            const schedule = JSON.parse(card.dataset.selectSchedule);

            selectSchedule(schedule, card);
          });
        });
    }

    if (scheduleCount) {
      scheduleCount.textContent = `Showing ${data.start || 0}-${data.end || 0} of ${data.total || 0}`;
    }

    if (schedulePrev) {
      schedulePrev.disabled = state.schedulePage <= 1;
    }

    if (scheduleNext) {
      scheduleNext.disabled = state.schedulePage >= state.scheduleTotalPages;
    }
  }

  function selectSchedule(schedule, selectedCard) {
    state.selectedSchedule = schedule;

    scheduleGrid.querySelectorAll(".reg-doctor-card").forEach((card) => {
      card.classList.remove("reg-doctor-card--selected");
    });
    if (selectedCard) {
      selectedCard.classList.add("reg-doctor-card--selected");
    }

    updateRegistrationDetails();
  }
  if (scheduleInput) {
    scheduleInput.addEventListener(
      "input",
      debounce((event) => {
        state.scheduleQuery = event.target.value.trim();

        state.schedulePage = 1;

        loadSchedules();
      }, 300),
    );
  }

  if (schedulePrev) {
    schedulePrev.addEventListener("click", () => {
      if (state.schedulePage > 1) {
        state.schedulePage--;

        loadSchedules();
      }
    });
  }

  if (scheduleNext) {
    scheduleNext.addEventListener("click", () => {
      if (state.schedulePage < state.scheduleTotalPages) {
        state.schedulePage++;

        loadSchedules();
      }
    });
  }

  let scheduleFilterChoice = null;

  if (scheduleFilter) {
    scheduleFilterChoice = new Choices(scheduleFilter, {
      searchEnabled: false,
      itemSelectText: "",
      shouldSort: false,
      allowHTML: false,
    });

    scheduleFilter.addEventListener("change", function () {
      state.scheduleFilter = this.value;

      state.schedulePage = 1;

      loadSchedules();
    });
  }

  const detailPatient = document.getElementById("detailPatient");

  const detailSchedule = document.getElementById("detailSchedule");

  const registerBtn = document.getElementById("registerBtn");

  const regTypeGroup = document.getElementById("regTypeGroup");

  const chiefComplaint = document.getElementById("chiefComplaint");

  const tokenPreview = document.getElementById("tokenPreview");

  const regMessage = document.getElementById("regMessage");

  const arrivedByAmbulanceCheckbox =
    document.getElementById("arrivedByAmbulance");

  const ambulanceSelectionBox = document.getElementById(
    "ambulanceSelectionBox",
  );

  const ambulanceListEl = document.getElementById("ambulanceList");

  const selectedAmbulanceBox = document.getElementById("selectedAmbulanceBox");

  const noAmbulanceState = document.getElementById("noAmbulanceState");

  const availableAmbulanceCount = document.getElementById(
    "availableAmbulanceCount",
  );

  const ambulanceAvailableBadge = document.getElementById(
    "ambulanceAvailableBadge",
  );

  function escapeAmbulanceHtml(value) {
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

  function updateAmbulanceCount() {
    const count = state.ambulanceList.length;

    if (availableAmbulanceCount) {
      availableAmbulanceCount.textContent = count;
    }

    if (ambulanceAvailableBadge) {
      ambulanceAvailableBadge.textContent = `${count} available`;
    }
  }

  async function loadAvailableAmbulances() {
    if (!urls.ambulance) {
      console.warn("Ambulance URL is not configured.");

      return;
    }

    try {
      if (ambulanceListEl) {
        ambulanceListEl.innerHTML = `
        <div class="reg-table-empty">
          Loading ambulances...
        </div>
      `;
      }

      const response = await fetch(urls.ambulance, {
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        state.ambulanceList = [];

        updateAmbulanceCount();

        renderAmbulances();

        return;
      }

      state.ambulanceList = Array.isArray(data.ambulances)
        ? data.ambulances
        : [];

      updateAmbulanceCount();

      renderAmbulances();
    } catch (error) {
      console.error("Unable to load ambulances:", error);

      state.ambulanceList = [];

      updateAmbulanceCount();

      renderAmbulances();
    }
  }

  function getAmbulanceId(ambulance) {
    if (!ambulance) return null;

    return ambulance.uuid ?? ambulance.id ?? ambulance.ambulance_id ?? null;
  }

  function renderAmbulances() {
    if (!ambulanceListEl) {
      return;
    }

    if (!state.ambulanceList || state.ambulanceList.length === 0) {
      ambulanceListEl.innerHTML = "";

      ambulanceListEl.hidden = true;

      if (noAmbulanceState) {
        noAmbulanceState.hidden = false;
      }

      return;
    }
    ambulanceListEl.hidden = false;

    if (noAmbulanceState) {
      noAmbulanceState.hidden = true;
    }

    ambulanceListEl.innerHTML = state.ambulanceList
      .map(function (ambulance, index) {
        const isSelected = state.selectedAmbulanceIndex === index;

        const ambulanceId = getAmbulanceId(ambulance);

        console.log(
          "Rendered ambulance:",
          ambulance.unitNumber || ambulance.unit_number,
          "ID:",
          ambulanceId,
        );

        const vehicleName =
          `${ambulance.make || ""} ${ambulance.model || ""}`.trim() || "—";

        return `
                <button
                    type="button"
                    class="reg-ambulance-card${isSelected ? " is-selected" : ""}"
                    data-ambulance-index="${index}"
                    data-ambulance-id="${escapeAmbulanceHtml(ambulanceId)}"
                >

                    <div class="reg-ambulance-card-main">

                        <div class="reg-ambulance-card-icon">
                            <i class="fas fa-ambulance"></i>
                        </div>

                        <div class="reg-ambulance-card-info">

                            <strong>
                                ${escapeAmbulanceHtml(
                                  ambulance.unitNumber ||
                                    ambulance.unit_number ||
                                    "Ambulance",
                                )}
                            </strong>

                            <span>
                                ${escapeAmbulanceHtml(
                                  ambulance.plate ||
                                    ambulance.registration_number ||
                                    "—",
                                )}
                            </span>

                        </div>

                    </div>


                    <div class="reg-ambulance-card-meta">

                        <span>
                            ${escapeAmbulanceHtml(vehicleName)}
                        </span>

                        <span>
                            ${escapeAmbulanceHtml(
                              ambulance.serviceType ||
                                ambulance.service_type ||
                                "—",
                            )}
                        </span>

                    </div>

                </button>
            `;
      })
      .join("");

    ambulanceListEl
      .querySelectorAll(".reg-ambulance-card")
      .forEach(function (card) {
        card.addEventListener("click", function () {
          const index = Number(card.dataset.ambulanceIndex);

          selectAmbulance(index);
        });
      });
  }
  function selectAmbulance(index) {
    console.log("Clicked ambulance index:", index);

    if (index < 0 || index >= state.ambulanceList.length) {
      console.error("Invalid ambulance index:", index);

      return;
    }
    state.selectedAmbulanceIndex = index;

    state.selectedAmbulance = state.ambulanceList[index];

    console.log("Selected ambulance:", state.selectedAmbulance);

    console.log("Selected index:", state.selectedAmbulanceIndex);

    renderAmbulances();

    showSelectedAmbulance();
  }

  const ambulanceAvailabilitySearch = document.getElementById(
    "ambulanceAvailabilitySearch",
  );

  const ambulancePrevPage = document.getElementById("ambulancePrevPage");

  const ambulanceNextPage = document.getElementById("ambulanceNextPage");

  const ambulancePaginationInfo = document.getElementById(
    "ambulancePaginationInfo",
  );

  const ambulancePageNumber = document.getElementById("ambulancePageNumber");

  const ambulancePagination = document.getElementById("ambulancePagination");

  if (ambulanceAvailabilitySearch) {
    ambulanceAvailabilitySearch.addEventListener(
      "input",

      debounce(function (event) {
        ambulanceAvailabilityState.searchQuery = event.target.value.trim();

        ambulanceAvailabilityState.currentPage = 1;

        loadAmbulanceAvailability();
      }, 400),
    );
  }
  if (ambulancePrevPage) {
    ambulancePrevPage.addEventListener(
      "click",

      function () {
        if (ambulanceAvailabilityState.currentPage <= 1) {
          return;
        }

        ambulanceAvailabilityState.currentPage--;

        loadAmbulanceAvailability();
      },
    );
  }
  if (ambulanceNextPage) {
    ambulanceNextPage.addEventListener(
      "click",

      function () {
        if (
          ambulanceAvailabilityState.currentPage >=
          ambulanceAvailabilityState.totalPages
        ) {
          return;
        }

        ambulanceAvailabilityState.currentPage++;

        loadAmbulanceAvailability();
      },
    );
  }

  function showSelectedAmbulance() {
    if (!state.selectedAmbulance || !selectedAmbulanceBox) {
      return;
    }

    const ambulance = state.selectedAmbulance;

    selectedAmbulanceBox.hidden = false;

    const unit = document.getElementById("selectedAmbulanceUnit");

    const plate = document.getElementById("selectedAmbulancePlate");

    const vehicle = document.getElementById("selectedAmbulanceVehicle");

    const service = document.getElementById("selectedAmbulanceService");

    const phone = document.getElementById("selectedAmbulancePhone");

    if (unit) {
      unit.textContent = ambulance.unitNumber || ambulance.unit_number || "—";
    }

    if (plate) {
      plate.textContent =
        ambulance.plate || ambulance.registration_number || "—";
    }

    if (vehicle) {
      vehicle.textContent =
        `${ambulance.make || ""} ${ambulance.model || ""}`.trim() || "—";
    }

    if (service) {
      service.textContent =
        ambulance.serviceType || ambulance.service_type || "—";
    }

    if (phone) {
      phone.textContent =
        ambulance.dispatchPhone ||
        ambulance.dispatch_phone ||
        ambulance.phone ||
        "—";
    }
  }
  function clearAmbulanceSelection() {
    state.selectedAmbulance = null;

    if (selectedAmbulanceBox) {
      selectedAmbulanceBox.hidden = true;
    }

    renderAmbulances();
  }

  if (arrivedByAmbulanceCheckbox) {
    arrivedByAmbulanceCheckbox.addEventListener("change", function () {
      state.arrivedByAmbulance = this.checked;

      if (state.arrivedByAmbulance) {
        if (ambulanceSelectionBox) {
          ambulanceSelectionBox.hidden = false;
        }

        loadAvailableAmbulances();
      } else {
        clearAmbulanceSelection();

        if (ambulanceSelectionBox) {
          ambulanceSelectionBox.hidden = true;
        }
      }
    });

    state.arrivedByAmbulance = arrivedByAmbulanceCheckbox.checked;
  }

  function updateRegistrationDetails() {
    if (detailPatient && state.selectedPatient) {
      detailPatient.innerHTML = `
        <div class="reg-detail-title">
          ${state.selectedPatient.name}
        </div>

        <div class="reg-detail-sub">
          <strong>Patient ID:</strong>
          ${state.selectedPatient.patient_number}
        </div>
        <div class="reg-detail-sub">

            ${state.selectedPatient.patient_type}

            ${
              state.selectedPatient.is_athlete
                ? `
                  <span class="athlete-badge">
                    <i class="fas fa-person-running"></i>
                    Athlete
                  </span>
                `
                : ""
            }

            &middot;

            ${state.selectedPatient.phone || "No Phone"}

        </div>
      `;
    } else if (detailPatient) {
      detailPatient.innerHTML = `
        <div class="reg-detail-empty">
          None selected
        </div>
      `;
    }

    if (detailSchedule && state.selectedSchedule) {
      const schedule = state.selectedSchedule;

      detailSchedule.innerHTML = `
        <div class="reg-detail-title">
          ${schedule.doctor_name}
        </div>

        <div class="reg-detail-sub">
          <strong>Department:</strong>
          ${schedule.department}
        </div>

        <div class="reg-detail-sub">
          <strong>Room:</strong>
          ${schedule.room_number || "—"}
        </div>

        <div class="reg-detail-sub">
          <strong>Time:</strong>
          ${schedule.start_time}
          -
          ${schedule.end_time}
        </div>
      `;
    } else if (detailSchedule) {
      detailSchedule.innerHTML = `
        <div class="reg-detail-empty">
          None selected
        </div>
      `;
    }

    if (registerBtn) {
      registerBtn.disabled = !(state.selectedPatient && state.selectedSchedule);
    }
  }

  if (regTypeGroup) {
    regTypeGroup.querySelectorAll(".reg-type-pill").forEach((pill) => {
      pill.addEventListener("click", () => {
        regTypeGroup.querySelectorAll(".reg-type-pill").forEach((item) => {
          item.classList.remove("reg-type-pill--active");
        });

        pill.classList.add("reg-type-pill--active");

        state.registrationType = pill.dataset.type;
      });
    });
  }

  function resetRegistrationForm() {
    state.selectedPatient = null;
    state.selectedSchedule = null;
    state.arrivedByAmbulance = false;
    state.selectedAmbulance = null;

    state.ambulanceList = [];

    if (chiefComplaint) {
      chiefComplaint.value = "";
    }
    if (arrivedByAmbulanceCheckbox) {
      arrivedByAmbulanceCheckbox.checked = false;
    }

    if (ambulanceSelectionBox) {
      ambulanceSelectionBox.hidden = true;
    }

    if (selectedAmbulanceBox) {
      selectedAmbulanceBox.hidden = true;
    }

    if (ambulanceListEl) {
      ambulanceListEl.innerHTML = "";
    }

    if (detailPatient) {
      detailPatient.innerHTML = `
        <div class="reg-detail-empty">
          None selected
        </div>
      `;
    }

    if (detailSchedule) {
      detailSchedule.innerHTML = `
        <div class="reg-detail-empty">
          None selected
        </div>
      `;
    }

    if (selectedPatientBox) {
      selectedPatientBox.classList.add("reg-selected-box--empty");

      selectedPatientBox.innerHTML = `
        <i class="fas fa-user"></i>

        <span>
          No patient selected yet.
          Search above to select one.
        </span>
      `;
    }

    if (patientInput) {
      patientInput.value = "";
    }

    if (patientResults) {
      patientResults.innerHTML = "";
    }

    loadSchedules();

    updateRegistrationDetails();
  }

  if (registerBtn) {
    registerBtn.addEventListener("click", function () {
      if (!state.selectedPatient || !state.selectedSchedule) {
        showToast(
          "Missing Information",
          "Please select a patient and doctor schedule.",
          "error",
        );

        return;
      }
      const ambulanceChecked = state.arrivedByAmbulance;

      if (ambulanceChecked && !state.selectedAmbulance) {
        showToast(
          "Ambulance Required",
          "Please select the ambulance used to bring the patient.",
          "error",
        );

        return;
      }
      registerBtn.disabled = true;

      registerBtn.innerHTML = `
          <i class="fas fa-spinner fa-spin"></i>
          Registering…
        `;

      if (regMessage) {
        regMessage.textContent = "";

        regMessage.className = "reg-message";
      }

      console.log("ARRIVED BY AMBULANCE:", ambulanceChecked);

      console.log("SELECTED AMBULANCE:", state.selectedAmbulance);

      console.log(
        "SELECTED AMBULANCE ID:",
        state.selectedAmbulance ? state.selectedAmbulance.id : null,
      );

      const registrationPayload = {
        patient_id: state.selectedPatient.id,

        schedule_id: state.selectedSchedule.shift_id,

        assignment_id: state.selectedSchedule.assignment_id,

        registration_type: state.registrationType,

        chief_complaint: chiefComplaint ? chiefComplaint.value.trim() : "",

        arrived_by_ambulance: ambulanceChecked,

        ambulance_id:
          ambulanceChecked && state.selectedAmbulance
            ? state.selectedAmbulance.id || state.selectedAmbulance.uuid || ""
            : "",
      };

      console.log("REGISTRATION PAYLOAD:", registrationPayload);
      console.log("AMBULANCE ID BEING SENT:", registrationPayload.ambulance_id);

      fetch(urls.register, {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },

        body: JSON.stringify(registrationPayload),
      })
        .then((response) =>
          response.json().then((data) => ({
            ok: response.ok,
            data,
          })),
        )

        .then(({ ok, data }) => {
          console.log("CHECK IN RESPONSE:", ok, data);

          if (!ok) {
            throw new Error(data.error || "Could not register patient.");
          }

          if (tokenPreview) {
            tokenPreview.innerHTML = `
                <i class="fas fa-ticket"></i>

                <span>
                  Token ${data.token_number}
                </span>
              `;
          }

          showToast(
            "Registration Successful",

            `Token ${
              data.display_token || data.token_number
            } added to the queue.`,

            "success",
          );

          if (regMessage) {
            regMessage.classList.add("reg-message--success");
          }

          addQueueRow(data.queue_row);

          resetRegistrationForm();
        })

        .catch((error) => {
          console.error("Registration error:", error);

          if (regMessage) {
            regMessage.textContent = error.message;
          }

          showToast("Registration Failed", error.message, "error");
        })

        .finally(() => {
          registerBtn.innerHTML = `
              <i class="fas fa-check"></i>
              Register patient
            `;

          updateRegistrationDetails();
        });
    });
  }

  const ambulanceAvailabilityTableBody = document.getElementById(
    "ambulanceAvailabilityTableBody",
  );

  const ambulanceAvailabilityEmpty = document.getElementById(
    "ambulanceAvailabilityEmpty",
  );

  const refreshAmbulancesBtn = document.getElementById("refreshAmbulancesBtn");

  const ambulanceTotalCount = document.getElementById("ambulanceTotalCount");

  const ambulanceAvailableCount = document.getElementById(
    "ambulanceAvailableCount",
  );

  const ambulanceDispatchedCount = document.getElementById(
    "ambulanceDispatchedCount",
  );

  const ambulanceReservedCount = document.getElementById(
    "ambulanceReservedCount",
  );

  const ambulanceOutofserviceCount = document.getElementById(
    "ambulanceOutOfServiceCount",
  );

  const ambulanceMaintenanceCount = document.getElementById(
    "ambulanceMaintenanceCount",
  );
  function updateAmbulanceSummaryCounts(counts) {
    if (!counts) {
      return;
    }

    if (ambulanceTotalCount) {
      ambulanceTotalCount.textContent = counts.total || 0;
    }

    if (ambulanceAvailableCount) {
      ambulanceAvailableCount.textContent = counts.available || 0;
    }

    if (ambulanceDispatchedCount) {
      ambulanceDispatchedCount.textContent = counts.dispatched || 0;
    }

    if (ambulanceReservedCount) {
      ambulanceReservedCount.textContent = counts.reserved || 0;
    }

    if (ambulanceOutofserviceCount) {
      ambulanceOutofserviceCount.textContent = counts.outofservice || 0;
    }

    if (ambulanceMaintenanceCount) {
      ambulanceMaintenanceCount.textContent = counts.maintenance || 0;
    }
  }

  const ambulanceLastUpdated = document.getElementById("ambulanceLastUpdated");

  const ambulanceAvailabilityState = {
    ambulances: [],
    searchQuery: "",
    currentPage: 1,
    totalPages: 1,
    totalRecords: 0,
    start: 0,
    end: 0,
  };
  function normalizeAmbulanceStatus(status) {
    const value = String(status || "")
      .trim()
      .toLowerCase()
      .replace(/[\s-]+/g, "_");

    const aliases = {
      available: "available",

      dispatched: "dispatched",

      reserved: "reserved",

      maintenance: "maintenance",

      outofservice: "outofservice",

      out_of_service: "outofservice",
    };

    return aliases[value] || value;
  }

  function getAmbulanceStatusLabel(status) {
    const normalized = normalizeAmbulanceStatus(status);

    const labels = {
      available: "Available",

      dispatched: "Dispatched",

      reserved: "Reserved",

      outofservice: "Out of Service",

      maintenance: "Maintenance",
    };

    return labels[normalized] || "Unknown";
  }

  function getAmbulanceStatusClass(status) {
    const normalized = normalizeAmbulanceStatus(status);

    const classes = {
      available: "available",

      dispatched: "dispatched",

      reserved: "reserved",

      outofservice: "outofservice",

      maintenance: "maintenance",
    };

    return classes[normalized] || "maintenance";
  }

  function escapeAvailabilityHtml(value) {
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

  function formatAmbulanceUpdatedAt(value) {
    if (!value) {
      return "—";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return date.toLocaleString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function updateAmbulanceAvailabilitySummary() {
    const ambulances = ambulanceAvailabilityState.ambulances;

    const total = ambulances.length;

    const available = ambulances.filter(
      (ambulance) => normalizeAmbulanceStatus(ambulance.status) === "available",
    ).length;

    const dispatched = ambulances.filter(
      (ambulance) =>
        normalizeAmbulanceStatus(ambulance.status) === "dispatched",
    ).length;

    const reserved = ambulances.filter(
      (ambulance) => normalizeAmbulanceStatus(ambulance.status) === "reserved",
    ).length;

    const outofservice = ambulances.filter(
      (ambulance) =>
        normalizeAmbulanceStatus(ambulance.status) === "outofservice",
    ).length;

    const maintenance = ambulances.filter(
      (ambulance) =>
        normalizeAmbulanceStatus(ambulance.status) === "maintenance",
    ).length;

    if (ambulanceTotalCount) {
      ambulanceTotalCount.textContent = total;
    }

    if (ambulanceAvailableCount) {
      ambulanceAvailableCount.textContent = available;
    }

    if (ambulanceDispatchedCount) {
      ambulanceDispatchedCount.textContent = dispatched;
    }

    if (ambulanceReservedCount) {
      ambulanceReservedCount.textContent = reserved;
    }

    if (ambulanceOutofserviceCount) {
      ambulanceOutofserviceCount.textContent = outofservice;
    }

    if (ambulanceMaintenanceCount) {
      ambulanceMaintenanceCount.textContent = maintenance;
    }

    if (availableAmbulanceCount) {
      availableAmbulanceCount.textContent = available;
    }

    if (ambulanceAvailableBadge) {
      ambulanceAvailableBadge.textContent = `${available} available`;
    }
  }

  function getAvailabilityAmbulanceId(ambulance) {
    if (!ambulance) return "";

    return ambulance.uuid || ambulance.ambulance_id || ambulance.id || "";
  }

  const AMBULANCE_STATUS_CHOICES = [
    { value: "available", label: "Available" },
    { value: "dispatched", label: "Dispatched" },
    { value: "reserved", label: "Reserved" },
    { value: "maintenance", label: "Maintenance" },
    { value: "outofservice", label: "Out of Service" },
  ];
  let ambulanceStatusChoicesInstances = [];
//   function initializeAmbulanceStatusChoices() {
//   // Destroy old Choices instances
//   ambulanceStatusChoicesInstances.forEach((instance) => {
//     try {
//       instance.destroy();
//     } catch (error) {
//       console.warn("Unable to destroy Choices instance:", error);
//     }
//   });

//   ambulanceStatusChoicesInstances = [];

//   // Initialize Choices for every ambulance status dropdown
//   const selects = document.querySelectorAll(
//     ".ambulance-status-select"
//   );

//   selects.forEach((select) => {
//     const choice = new Choices(select, {
//       searchEnabled: false,
//       itemSelectText: "",
//       shouldSort: false,
//       allowHTML: false,
//     });

//     ambulanceStatusChoicesInstances.push(choice);
//   });
// }
function initializeAmbulanceStatusChoices() {
  ambulanceStatusChoicesInstances.forEach((instance) => {
    try {
      instance.destroy();
    } catch (error) {
      console.warn("Unable to destroy Choices instance:", error);
    }
  });

  ambulanceStatusChoicesInstances = [];

  const selects = document.querySelectorAll(
    ".ambulance-status-select"
  );

  selects.forEach((select) => {

    const statusClass = Array.from(select.classList).find(
      (className) =>
        [
          "available",
          "dispatched",
          "reserved",
          "maintenance",
          "outofservice",
        ].includes(className)
    );

    const choice = new Choices(select, {
      searchEnabled: false,
      itemSelectText: "",
      shouldSort: false,
      allowHTML: false,
       position: "bottom",
    });

    // Add status class to Choices wrapper
    if (statusClass && select.parentElement) {
      const choicesContainer =
        select.parentElement.querySelector(".choices");

      if (choicesContainer) {
        choicesContainer.classList.add(
          `ambulance-choice-${statusClass}`
        );
      }
    }

    ambulanceStatusChoicesInstances.push(choice);
  });
}
  function updateAmbulancePagination() {
    const currentPage = ambulanceAvailabilityState.currentPage;

    const totalPages = ambulanceAvailabilityState.totalPages;

    const totalRecords = ambulanceAvailabilityState.totalRecords;

    const start = ambulanceAvailabilityState.start;

    const end = ambulanceAvailabilityState.end;

    if (ambulancePaginationInfo) {
      ambulancePaginationInfo.textContent = `Showing ${start}-${end} of ${totalRecords}`;
    }

    if (ambulancePageNumber) {
      ambulancePageNumber.textContent = `Page ${currentPage} of ${totalPages}`;
    }

    if (ambulancePrevPage) {
      ambulancePrevPage.disabled = currentPage <= 1;
    }

    if (ambulanceNextPage) {
      ambulanceNextPage.disabled =
        currentPage >= totalPages || totalRecords === 0;
    }

    if (ambulancePagination) {
      ambulancePagination.hidden = totalRecords === 0;
    }
  }
  function renderAmbulanceAvailability() {
    if (!ambulanceAvailabilityTableBody) {
      return;
    }

    // Django already sends only the current page records

    const ambulances = ambulanceAvailabilityState.ambulances;

    // TOTAL RECORDS FROM AJAX RESPONSE

    const totalRecords = ambulanceAvailabilityState.totalRecords;

    // ==========================================
    // EMPTY STATE
    // ==========================================

    if (totalRecords === 0) {
      ambulanceAvailabilityTableBody.innerHTML = "";

      if (ambulanceAvailabilityEmpty) {
        ambulanceAvailabilityEmpty.hidden = false;
      }

      updateAmbulancePagination();

      return;
    }

    // ==========================================
    // HIDE EMPTY STATE
    // ==========================================

    if (ambulanceAvailabilityEmpty) {
      ambulanceAvailabilityEmpty.hidden = true;
    }

    // ==========================================
    // RENDER AMBULANCES
    // ==========================================

    ambulanceAvailabilityTableBody.innerHTML = ambulances
      .map(function (ambulance) {
        const ambulanceId = getAvailabilityAmbulanceId(ambulance);

        const status = normalizeAmbulanceStatus(ambulance.status);

        const statusClass = getAmbulanceStatusClass(status);

        const statusOptions = AMBULANCE_STATUS_CHOICES.map(function (choice) {
          return `
                <option
                  value="${choice.value}"
                  ${status === choice.value ? "selected" : ""}
                >
                  ${choice.label}
                </option>
              `;
        }).join("");

        const statusLabel = getAmbulanceStatusLabel(status);

        const unitNumber =
          ambulance.unitNumber || ambulance.unit_number || "Ambulance";

        const plate = ambulance.plate || ambulance.registration_number || "—";

        const make = ambulance.make || "";

        const model = ambulance.model || "";

        const vehicle = `${make} ${model}`.trim() || "—";

        const serviceType =
          ambulance.serviceType || ambulance.service_type || "—";

        const updatedAt = formatAmbulanceUpdatedAt(
          ambulance.updated_at ||
            ambulance.updatedAt ||
            ambulance.last_updated ||
            ambulance.lastUpdated,
        );

        return `

          <tr>

            <!-- UNIT -->

            <td>

              <div class="ambulance-unit-cell">

                <div
                  class="ambulance-unit-icon"
                >

                  <i
                    class="fas fa-ambulance"
                  ></i>

                </div>


                <div
                  class="ambulance-unit-info"
                >

                  <strong>

                    ${escapeAvailabilityHtml(unitNumber)}

                  </strong>


                  <span>
                    Unit Number
                  </span>

                </div>

              </div>

            </td>


            <!-- VEHICLE -->

            <td>

              <div
                class="ambulance-vehicle-info"
              >

                <span>

                  Plate:
                  ${escapeAvailabilityHtml(plate)}

                </span>


                <span>

                  Vehicle:
                  ${escapeAvailabilityHtml(vehicle)}

                </span>


                <span>

                  Type:
                  ${escapeAvailabilityHtml(serviceType)}

                </span>

              </div>

            </td>


            <!-- STATUS -->

            <td>

              <span
                class="
                  ambulance-status-badge
                  ${statusClass}
                "
              >

                ${escapeAvailabilityHtml(statusLabel)}

              </span>

            </td>


            <!-- LAST UPDATED -->

            <td>

              ${escapeAvailabilityHtml(updatedAt)}

            </td>


            <!-- ACTION -->

            <td>

              <select
                class="
                  ambulance-status-select
                  ${statusClass}
                "

                data-ambulance-status

                data-ambulance-id="${escapeAvailabilityHtml(ambulanceId)}"
              >

                ${statusOptions}

              </select>

            </td>

          </tr>

        `;
      })
      .join("");

      initializeAmbulanceStatusChoices();

    // ==========================================
    // STATUS DROPDOWN EVENTS
    // ==========================================

    ambulanceAvailabilityTableBody
      .querySelectorAll("[data-ambulance-status]")
      .forEach(function (select) {
        select.addEventListener(
          "change",

          function () {
            updateAmbulanceStatus(
              this.dataset.ambulanceId,

              this.value,

              this,
            );
          },
        );
      });

    // ==========================================
    // UPDATE PAGINATION UI
    // ==========================================

    updateAmbulancePagination();
  }

  async function loadAmbulanceAvailability() {
    if (!urls.ambulanceAvailability) {
      console.warn("Ambulance availability URL is not configured.");

      return;
    }

    try {
      const params = new URLSearchParams({
        q: ambulanceAvailabilityState.searchQuery || "",

        page: ambulanceAvailabilityState.currentPage || 1,
      });
      console.log("SEARCH QUERY:", ambulanceAvailabilityState.searchQuery);

      console.log(
        "REQUEST URL:",
        `${urls.ambulanceAvailability}?${params.toString()}`,
      );

      const response = await fetch(
        `${urls.ambulanceAvailability}?${params.toString()}`,
        {
          headers: {
            "X-Requested-With": "XMLHttpRequest",
          },
        },
      );

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Unable to load ambulances.");
      }

      updateAmbulanceSummaryCounts(data.counts);

      ambulanceAvailabilityState.ambulances = Array.isArray(data.ambulances)
        ? data.ambulances
        : [];

      ambulanceAvailabilityState.currentPage = data.page || 1;

      ambulanceAvailabilityState.totalPages = data.total_pages || 1;

      ambulanceAvailabilityState.totalRecords = data.total || 0;

      ambulanceAvailabilityState.start = data.start || 0;

      ambulanceAvailabilityState.end = data.end || 0;

      renderAmbulanceAvailability();

      updateAmbulancePagination();
    } catch (error) {
      console.error("Unable to load ambulance availability:", error);
    }
  }

  /* ==========================================================
   UPDATE AMBULANCE STATUS
========================================================== */

  async function updateAmbulanceStatus(ambulanceId, newStatus, selectElement) {
    console.log("=================================");
    console.log("UPDATING AMBULANCE");
    console.log("Ambulance ID:", ambulanceId);
    console.log("New Status:", newStatus);
    console.log("=================================");
    if (!ambulanceId || !urls.ambulanceStatus) {
      return;
    }

    const previousAmbulance = ambulanceAvailabilityState.ambulances.find(
      (ambulance) =>
        String(getAvailabilityAmbulanceId(ambulance)) === String(ambulanceId),
    );

    const previousStatus = previousAmbulance ? previousAmbulance.status : "";

    try {
      if (selectElement) {
        selectElement.disabled = true;
      }

      const response = await fetch(urls.ambulanceStatus, {
        method: "POST",

        headers: {
          "Content-Type": "application/json",

          "X-CSRFToken": csrftoken,

          "X-Requested-With": "XMLHttpRequest",
        },

        body: JSON.stringify({
          id: ambulanceId,

          status: newStatus,
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || "Unable to update ambulance status.");
      }

      const index = ambulanceAvailabilityState.ambulances.findIndex(
        (ambulance) =>
          String(getAvailabilityAmbulanceId(ambulance)) === String(ambulanceId),
      );

      if (index !== -1) {
        ambulanceAvailabilityState.ambulances[index] = {
          ...ambulanceAvailabilityState.ambulances[index],

          ...data.ambulance,
        };
      }

      await loadAmbulanceAvailability();

      if (ambulanceLastUpdated) {
        ambulanceLastUpdated.innerHTML = `
        <i class="fas fa-clock"></i>
        Last updated: Just now
      `;
      }

      showToast(
        "Status Updated",
        "Ambulance status updated successfully.",
        "success",
      );
    } catch (error) {
      console.error("Ambulance status update error:", error);
      if (selectElement) {
        selectElement.value = normalizeAmbulanceStatus(previousStatus);
      }

      showToast(
        "Status Update Failed",
        error.message || "Unable to update ambulance status.",
        "error",
      );
    } finally {
      if (selectElement) {
        selectElement.disabled = false;
      }
    }
  }
  if (refreshAmbulancesBtn) {
    refreshAmbulancesBtn.addEventListener("click", function () {
      loadAmbulanceAvailability();
    });
  }
  loadAmbulanceAvailability();

  const queueBody = document.getElementById("queueBody");

  const queueSearchInput = document.getElementById("queueSearchInput");

  const queueCount = document.getElementById("queueCount");

  const queuePrev = document.getElementById("queuePrev");

  const queueNext = document.getElementById("queueNext");

  const queueDateFilter = document.getElementById("queueDateFilter");

  function queueRowHtml(row) {
    return `
      <tr data-row-id="${row.id}">

        <td>
          ${row.display_token}
        </td>

        <td>
          ${row.patient_name}
        </td>

        <td>
          ${row.registration_type}
        </td>

        <td>
          ${row.doctor_name}
        </td>

        <td>
          ${row.room_number || "—"}
        </td>

        <td>
          ${row.registration_time}
        </td>

        <td>

          <span
            class="
              reg-status
              ${statusClass(row.status)}
            "
          >
            ${row.status_display}
          </span>

        </td>

      </tr>
    `;
  }

  function addQueueRow(row) {
    if (!row || !queueBody) {
      return;
    }

    if (queueBody.querySelector(".reg-table-empty")) {
      queueBody.innerHTML = "";
    }

    queueBody.insertAdjacentHTML("beforeend", queueRowHtml(row));
  }

  function loadQueue(q = "") {
    if (!queueBody) {
      return;
    }

    const params = new URLSearchParams({
      page: state.queuePage,
    });

    if (q) {
      params.append("q", q);
    }

    if (state.queueDate) {
      params.append("date", state.queueDate);
    }

    fetch(`${urls.queue}?${params.toString()}`)
      .then((response) => response.json())

      .then((data) => {
        const rows = data.results || [];

        state.queueTotalPages = data.total_pages || 1;

        if (queueCount) {
          queueCount.textContent = `Showing ${data.start || 0}-${
            data.end || 0
          } of ${data.total || 0}`;
        }

        if (queuePrev) {
          queuePrev.disabled = state.queuePage <= 1;
        }

        if (queueNext) {
          queueNext.disabled = state.queuePage >= state.queueTotalPages;
        }

        queueBody.innerHTML = rows.length
          ? rows.map(queueRowHtml).join("")
          : `
              <tr>
                <td
                  colspan="7"
                  class="reg-table-empty"
                >
                  No patients in the queue yet.
                </td>
              </tr>
            `;
      })

      .catch((error) => {
        console.error("Queue load error:", error);

        queueBody.innerHTML = `
          <tr>
            <td
              colspan="7"
              class="reg-table-empty"
            >
              Could not load queue.
            </td>
          </tr>
        `;
      });
  }

  if (queueDateFilter) {
    flatpickr(queueDateFilter, {
      dateFormat: "Y-m-d",

      defaultDate: state.queueDate,

      allowInput: false,

      onChange(selectedDates, dateStr) {
        state.queueDate = dateStr;

        state.queuePage = 1;

        loadQueue(queueSearchInput ? queueSearchInput.value.trim() : "");
      },
    });
  }

  if (queuePrev) {
    queuePrev.addEventListener("click", () => {
      if (state.queuePage > 1) {
        state.queuePage--;

        loadQueue(queueSearchInput ? queueSearchInput.value.trim() : "");
      }
    });
  }

  if (queueNext) {
    queueNext.addEventListener("click", () => {
      if (state.queuePage < state.queueTotalPages) {
        state.queuePage++;

        loadQueue(queueSearchInput ? queueSearchInput.value.trim() : "");
      }
    });
  }

  if (queueSearchInput) {
    queueSearchInput.addEventListener(
      "input",
      debounce((event) => {
        state.queuePage = 1;

        loadQueue(event.target.value.trim());
      }, 300),
    );
  }

  const appointmentList = document.getElementById("appointmentList");

  const appointmentSearchInput = document.getElementById(
    "appointmentSearchInput",
  );

  const appointmentCount = document.getElementById("appointmentCount");

  const pendingCount = document.getElementById("pendingCount");

  const confirmedCount = document.getElementById("confirmedCount");

  const arrivedCount = document.getElementById("arrivedCount");

  const notArrivedCount = document.getElementById("notArrivedCount");

  const appointmentTabs = document.querySelectorAll(".appointment-tab");

  const appointmentPrev = document.getElementById("appointmentPrev");

  const appointmentNext = document.getElementById("appointmentNext");

  const appointmentPageInfo = document.getElementById("appointmentPageInfo");

  function loadAppointments() {
    if (!appointmentList) {
      return;
    }

    const params = new URLSearchParams({
      status: state.appointmentStatus,

      page: state.appointmentPage,
    });

    if (state.appointmentQuery) {
      params.append("q", state.appointmentQuery);
    }

    appointmentList.innerHTML = `
      <div class="reg-table-empty">
        Loading appointments…
      </div>
    `;

    fetch(`${urls.appointment}?${params.toString()}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Could not load appointments.");
        }

        return response.json();
      })

      .then((data) => {
        console.log("Appointments:", data);

        const appointments = data.results || [];

        state.appointmentTotalPages = data.total_pages || 1;

        const counts = data.counts || {};

        if (appointmentCount) {
          appointmentCount.textContent = `${data.total || 0} appointments`;
        }

        if (pendingCount) {
          pendingCount.textContent = counts.pending || 0;
        }

        if (confirmedCount) {
          confirmedCount.textContent = counts.confirmed || 0;
        }

        if (arrivedCount) {
          arrivedCount.textContent = counts.arrived || 0;
        }

        if (notArrivedCount) {
          notArrivedCount.textContent = counts.not_arrived || 0;
        }

        if (appointmentPrev) {
          appointmentPrev.disabled = state.appointmentPage <= 1;
        }

        if (appointmentNext) {
          appointmentNext.disabled =
            state.appointmentPage >= state.appointmentTotalPages;
        }

        if (appointmentPageInfo) {
          appointmentPageInfo.textContent = `Page ${state.appointmentPage} of ${
            state.appointmentTotalPages
          }`;
        }

        renderAppointments(appointments);
      })

      .catch((error) => {
        console.error("Appointment load error:", error);

        appointmentList.innerHTML = `
          <div class="reg-table-empty">
            Could not load appointments.
          </div>
        `;
      });
  }

  function renderAppointments(appointments) {
    console.log("APPOINTMENT DATA:", appointments);
    if (!appointments.length) {
      const statusText = state.appointmentStatus
        .toLowerCase()
        .replace("_", " ");

      appointmentList.innerHTML = `
      <div class="reg-table-empty">
        No ${statusText} appointments found.
      </div>
    `;

      return;
    }

    appointmentList.innerHTML = appointments
      .map((appointment) => {
        let action = "";

        /* =========================
         PENDING
      ========================= */
        if (appointment.status === "PENDING") {
          action = `
          <div class="appointment-actions">

            <button
              type="button"
              class="reg-btn reg-btn--primary"
              data-appointment-confirm="${appointment.id}"
              disabled
            >
              <i class="fas fa-check"></i>
              Confirm
            </button>

            <button
              type="button"
              class="reg-btn reg-btn--danger"
              data-appointment-reject="${appointment.id}"
            >
              <i class="fas fa-times"></i>
              Reject
            </button>

          </div>
        `;
        } else if (appointment.status === "CONFIRMED") {
          const today = new Date();
          today.setHours(0, 0, 0, 0);

          const appointmentDate = new Date(
            `${appointment.appointment_date_raw}T00:00:00`,
          );
          appointmentDate.setHours(0, 0, 0, 0);

          const isAppointmentToday =
            appointmentDate.getTime() === today.getTime();

          action = `
    <div class="appointment-actions">

      <button
        type="button"
        class="reg-btn reg-btn--primary"
        data-appointment-arrive="${appointment.id}"
        ${isAppointmentToday ? "" : "disabled"}
      >
        <i class="fas fa-user-check"></i>
        Mark Arrived
      </button>

      <button
        type="button"
        class="reg-btn reg-btn--danger"
        data-appointment-not-arrive="${appointment.id}"
        ${isAppointmentToday ? "" : "disabled"}
      >
        <i class="fas fa-user-clock"></i>
        Not Arrived
      </button>

    </div>
  `;
        } else if (appointment.status === "ARRIVED") {
          /* =========================
         ARRIVED
      ========================= */
          action = `
          <button
            type="button"
            class="reg-btn reg-btn--primary"
            data-appointment-checkin="${appointment.id}"
          >
            <i class="fas fa-sign-in-alt"></i>
            Check In
          </button>
        `;
        } else if (appointment.status === "CANCELLED") {
          /* =========================
         CANCELLED
      ========================= */
          action = `
          <span class="appointment-action-rejected">
            <i class="fas fa-times-circle"></i>
            Rejected
          </span>
        `;
        } else if (appointment.status === "NOT_ARRIVED") {
          /* =========================
         NOT ARRIVED
      ========================= */
          action = `
          <span class="appointment-action-rejected">
            <i class="fas fa-user-clock"></i>
            Not Arrived
          </span>
        `;
        }

        return `
        <div
          class="appointment-card"
          data-appointment-id="${appointment.id}"
            data-appointment-date="${appointment.appointment_date_raw}"
        >

          <!-- =========================
               Patient Information
          ========================= -->
          <div class="appointment-card__main">

            <div class="reg-avatar">
              ${initials(appointment.patient_name)}
            </div>

            <div class="appointment-card__info">

              <!-- Patient Name -->
              <div class="appointment-card__name">
                ${appointment.patient_name}

                <small>
                  ${appointment.patient_number || "—"}
                </small>
              </div>

              <!-- Appointment Number -->
              <div class="appointment-card__meta">
                <strong>
                  Appointment No:
                </strong>
                ${appointment.appointment_number || appointment.id}
              </div>

              <!-- Patient Type + Phone -->
              <div class="appointment-card__meta">
                ${appointment.patient_type}

                &middot;

                ${appointment.phone || "No phone"}
              </div>

              <!-- Doctor + Department -->
              <div class="appointment-card__doctor">

                <i class="fas fa-user-doctor"></i>

                <strong>
                  ${appointment.doctor_name || "Doctor"}
                </strong>

                <span>
                    Room ${appointment.room_number || "—"}
                </span>

              </div>

            </div>

          </div>

          <div class="appointment-card__time">

            ${
              appointment.status === "PENDING"
                ? `
                  <div class="consultation-time-field">
                   <small>
                      Appointment Date
                    </small>

                    <strong>
                      ${appointment.appointment_date || "—"}
                    </strong>

                    <small>
                      Appointment Time
                    </small>

                    <input
                      type="time"
                      class="appointment-time-input"
                      data-appointment-time="${appointment.id}"
                      value="${appointment.appointment_time || ""}"
                    >

                  </div>
                `
                : `
                  <div class="consultation-time-display">
                    <small>
                      Appointment Date
                    </small>

                    <strong>
                      ${appointment.appointment_date || "—"}
                    </strong>

                    <small>
                      Appointment Time
                    </small>

                    <strong>
                      ${formatTime(appointment.appointment_time)}
                    </strong>
                    

                  </div>
                `
            }

            <small>
              ${appointment.service || "—"}
            </small>

          </div>


          <!-- =========================
               Status + Action
          ========================= -->
          <div class="appointment-card__status">

            <span
              class="
                appointment-status
                ${appointmentStatusClass(appointment.status)}
              "
            >
              ${appointment.status_display}
            </span>

            ${action}

          </div>

        </div>
      `;
      })
      .join("");

    /* =========================
     Check In
  ========================= */
    appointmentList
      .querySelectorAll("[data-appointment-checkin]")
      .forEach((button) => {
        button.addEventListener("click", () => {
          checkInAppointment(button.dataset.appointmentCheckin);
        });
      });

    /* =========================
     Confirm
  ========================= */
    appointmentList
      .querySelectorAll("[data-appointment-confirm]")
      .forEach((button) => {
        button.addEventListener("click", () => {
          confirmAppointment(button.dataset.appointmentConfirm);
        });
      });

    /* =========================
     Reject
  ========================= */
    appointmentList
      .querySelectorAll("[data-appointment-reject]")
      .forEach((button) => {
        button.addEventListener("click", () => {
          rejectAppointment(button.dataset.appointmentReject);
        });
      });

    /* =========================
     Mark Arrived
  ========================= */
    appointmentList
      .querySelectorAll("[data-appointment-arrive]")
      .forEach((button) => {
        button.addEventListener("click", () => {
          markAppointmentArrived(button.dataset.appointmentArrive);
        });
      });

    /* =========================
     Not Arrived
  ========================= */
    appointmentList
      .querySelectorAll("[data-appointment-not-arrive]")
      .forEach((button) => {
        button.addEventListener("click", () => {
          markAppointmentNotArrived(button.dataset.appointmentNotArrive);
        });
      });

    // Set minimum time for appointment inputs
    setAppointmentTimeMin();

    // Validate confirm button for each pending appointment
    appointmentList
      .querySelectorAll(".appointment-time-input")
      .forEach((input) => {
        validateAppointmentTime(input);
      });
  }

  function validateAppointmentTime(input) {
    if (!appointmentList) {
      return;
    }

    const appointmentId = input.dataset.appointmentTime;

    const confirmButton = appointmentList.querySelector(
      `[data-appointment-confirm="${appointmentId}"]`,
    );

    if (!confirmButton) {
      return;
    }

    const selectedTime = input.value;

    // No time selected
    if (!selectedTime) {
      confirmButton.disabled = true;
      return;
    }

    const appointmentCard = input.closest(".appointment-card");

    const appointmentDate = appointmentCard?.dataset.appointmentDate;

    if (isPastAppointmentTime(selectedTime, appointmentDate)) {
      confirmButton.disabled = true;
      return;
    }

    confirmButton.disabled = false;

    // Valid future time
    confirmButton.disabled = false;
  }

  if (appointmentList) {
    appointmentList.addEventListener("input", function (event) {
      if (!event.target.classList.contains("appointment-time-input")) {
        return;
      }

      validateAppointmentTime(event.target);
    });

    appointmentList.addEventListener("change", function (event) {
      if (!event.target.classList.contains("appointment-time-input")) {
        return;
      }

      validateAppointmentTime(event.target);
    });
  }

  appointmentTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      appointmentTabs.forEach((item) => {
        item.classList.remove("appointment-tab--active");
      });

      tab.classList.add("appointment-tab--active");

      state.appointmentStatus = tab.dataset.status;

      state.appointmentQuery = "";

      state.appointmentPage = 1;

      if (appointmentSearchInput) {
        appointmentSearchInput.value = "";
      }

      loadAppointments();
    });
  });

  if (appointmentSearchInput) {
    appointmentSearchInput.addEventListener(
      "input",
      debounce((event) => {
        state.appointmentQuery = event.target.value.trim();

        state.appointmentPage = 1;

        loadAppointments();
      }, 300),
    );
  }

  if (appointmentPrev) {
    appointmentPrev.addEventListener("click", () => {
      if (state.appointmentPage > 1) {
        state.appointmentPage--;

        loadAppointments();
      }
    });
  }

  if (appointmentNext) {
    appointmentNext.addEventListener("click", () => {
      if (state.appointmentPage < state.appointmentTotalPages) {
        state.appointmentPage++;

        loadAppointments();
      }
    });
  }

  function confirmAppointment(appointmentId) {
    if (!appointmentId) {
      return;
    }

    const button = document.querySelector(
      `[data-appointment-confirm="${appointmentId}"]`,
    );

    const timeInput = appointmentList.querySelector(
      `[data-appointment-time="${appointmentId}"]`,
    );

    const appointmentTime = timeInput ? timeInput.value : "";

    if (!appointmentTime) {
      return;
    }

    const appointmentCard = appointmentList.querySelector(
      `[data-appointment-id="${appointmentId}"]`,
    );

    const appointmentDate = appointmentCard?.dataset.appointmentDate;

    if (isPastAppointmentTime(appointmentTime, appointmentDate)) {
      return;
    }
    if (button) {
      button.disabled = true;

      button.innerHTML = `
        <i class="fas fa-spinner fa-spin"></i>
        Confirming...
      `;
    }

    fetch(urls.appointmentStatus, {
      method: "POST",

      headers: {
        "Content-Type": "application/json",

        "X-CSRFToken": csrftoken,
      },

      body: JSON.stringify({
        appointment_id: appointmentId,

        status: "CONFIRMED",

        appointment_time: appointmentTime,
      }),
    })
      .then((response) =>
        response.json().then((data) => ({
          ok: response.ok,

          data,
        })),
      )

      .then(({ ok, data }) => {
        if (!ok) {
          throw new Error(data.error || "Could not confirm appointment.");
        }

        showToast(
          "Appointment Confirmed",

          data.message || "Appointment confirmed successfully.",

          "success",
        );

        loadAppointments();
      })

      .catch((error) => {
        console.error("Confirm appointment error:", error);

        showToast("Confirmation Failed", error.message, "error");

        if (button) {
          button.disabled = false;

          button.innerHTML = `
            <i class="fas fa-check"></i>
            Confirm
          `;
        }
      });
  }

  function checkInAppointment(appointmentId) {
    if (!appointmentId) {
      return;
    }

    const button = document.querySelector(
      `[data-appointment-checkin="${appointmentId}"]`,
    );

    if (button) {
      button.disabled = true;

      button.innerHTML = `
        <i class="fas fa-spinner fa-spin"></i>
        Checking In...
      `;
    }

    fetch(urls.appointmentStatus, {
      method: "POST",

      headers: {
        "Content-Type": "application/json",

        "X-CSRFToken": csrftoken,
      },

      body: JSON.stringify({
        appointment_id: appointmentId,

        status: "CHECKED_IN",
      }),
    })
      .then((response) =>
        response.json().then((data) => ({
          ok: response.ok,

          data,
        })),
      )

      .then(({ ok, data }) => {
        if (!ok) {
          throw new Error(data.error || "Could not check in patient.");
        }

        showToast(
          "Patient Checked In",

          data.message || "Patient checked in successfully.",

          "success",
        );

        loadAppointments();

        state.queuePage = 1;

        loadQueue(queueSearchInput ? queueSearchInput.value.trim() : "");
      })

      .catch((error) => {
        console.error("Check in error:", error);

        showToast("Check In Failed", error.message, "error");

        if (button) {
          button.disabled = false;

          button.innerHTML = `
            <i class="fas fa-sign-in-alt"></i>
            Check In
          `;
        }
      });
  }

  function rejectAppointment(appointmentId) {
    if (!appointmentId) {
      return;
    }

    const button = document.querySelector(
      `[data-appointment-reject="${appointmentId}"]`,
    );

    if (button) {
      button.disabled = true;

      button.innerHTML = `
        <i class="fas fa-spinner fa-spin"></i>
        Rejecting...
      `;
    }

    fetch(urls.appointmentStatus, {
      method: "POST",

      headers: {
        "Content-Type": "application/json",

        "X-CSRFToken": csrftoken,
      },

      body: JSON.stringify({
        appointment_id: appointmentId,

        status: "CANCELLED",

        cancellation_reason: "Rejected by front desk.",
      }),
    })
      .then((response) =>
        response.json().then((data) => ({
          ok: response.ok,

          data,
        })),
      )

      .then(({ ok, data }) => {
        if (!ok) {
          throw new Error(data.error || "Could not reject appointment.");
        }

        showToast(
          "Appointment Rejected",

          data.message || "Appointment rejected successfully.",

          "success",
        );

        loadAppointments();
      })

      .catch((error) => {
        console.error("Reject appointment error:", error);

        showToast("Rejection Failed", error.message, "error");

        if (button) {
          button.disabled = false;

          button.innerHTML = `
            <i class="fas fa-times"></i>
            Reject
          `;
        }
      });
  }

  function markAppointmentArrived(appointmentId) {
    if (!appointmentId) {
      return;
    }

    const button = document.querySelector(
      `[data-appointment-arrive="${appointmentId}"]`,
    );

    if (button) {
      button.disabled = true;

      button.innerHTML = `
        <i class="fas fa-spinner fa-spin"></i>
        Updating...
      `;
    }

    fetch(urls.appointmentStatus, {
      method: "POST",

      headers: {
        "Content-Type": "application/json",

        "X-CSRFToken": csrftoken,
      },

      body: JSON.stringify({
        appointment_id: appointmentId,

        status: "ARRIVED",
      }),
    })
      .then((response) =>
        response.json().then((data) => ({
          ok: response.ok,

          data,
        })),
      )

      .then(({ ok, data }) => {
        if (!ok) {
          throw new Error(data.error || "Could not update appointment.");
        }

        showToast(
          "Patient Arrived",

          data.message || "Appointment marked as arrived.",

          "success",
        );

        loadAppointments();

        state.queuePage = 1;

        loadQueue(queueSearchInput ? queueSearchInput.value.trim() : "");
      })

      .catch((error) => {
        console.error("Mark arrived error:", error);

        showToast("Update Failed", error.message, "error");

        if (button) {
          button.disabled = false;

          button.innerHTML = `
            <i class="fas fa-user-check"></i>
            Mark Arrived
          `;
        }
      });
  }

  function markAppointmentNotArrived(appointmentId) {
    if (!appointmentId) {
      return;
    }

    const button = document.querySelector(
      `[data-appointment-not-arrive="${appointmentId}"]`,
    );

    if (button) {
      button.disabled = true;

      button.innerHTML = `
        <i class="fas fa-spinner fa-spin"></i>
        Updating...
      `;
    }

    fetch(urls.appointmentStatus, {
      method: "POST",

      headers: {
        "Content-Type": "application/json",

        "X-CSRFToken": csrftoken,
      },

      body: JSON.stringify({
        appointment_id: appointmentId,

        status: "NOT_ARRIVED",
      }),
    })
      .then((response) =>
        response.json().then((data) => ({
          ok: response.ok,

          data,
        })),
      )

      .then(({ ok, data }) => {
        if (!ok) {
          throw new Error(data.error || "Could not update appointment.");
        }

        showToast(
          "Appointment Updated",

          data.message || "Patient marked as not arrived.",

          "success",
        );

        loadAppointments();
      })

      .catch((error) => {
        console.error("Not arrived error:", error);

        showToast("Update Failed", error.message, "error");

        if (button) {
          button.disabled = false;

          button.innerHTML = `
            <i class="fas fa-user-clock"></i>
            Not Arrived
          `;
        }
      });
  }
  /* ==========================================================
   DYNAMIC DOCTOR SCHEDULE CALENDAR
========================================================== */

  function initDoctorScheduleCalendar() {
    const calendarDays = document.getElementById("calendarDays");

    const calendarMonthYear = document.getElementById("calendarMonthYear");

    const prevMonthBtn = document.getElementById("prevMonthBtn");

    const nextMonthBtn = document.getElementById("nextMonthBtn");

    const modalOverlay = document.getElementById("scheduleModalOverlay");

    const modalClose = document.getElementById("scheduleModalClose");

    const modalDate = document.getElementById("modalDate");

    const modalSummary = document.getElementById("modalSummary");

    const doctorList = document.getElementById("scheduleDoctorList");

    if (
      !calendarDays ||
      !calendarMonthYear ||
      !prevMonthBtn ||
      !nextMonthBtn ||
      !modalOverlay ||
      !modalClose ||
      !modalDate ||
      !modalSummary ||
      !doctorList
    ) {
      return;
    }

    /* ======================================================
       STATE
    ====================================================== */

    const today = new Date();

    let currentMonth = today.getMonth();

    let currentYear = today.getFullYear();

    const monthNames = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December",
    ];
    function formatDate(dateString) {
      const date = new Date(dateString + "T00:00:00");

      return date.toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "long",
        year: "numeric",
      });
    }

    function renderCalendar() {
      calendarDays.innerHTML = "";

      calendarMonthYear.textContent = `${monthNames[currentMonth]} ${currentYear}`;

      const firstDay = new Date(currentYear, currentMonth, 1).getDay();

      const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

      for (let i = 0; i < firstDay; i++) {
        const empty = document.createElement("div");

        empty.className = "calendar-day empty";

        calendarDays.appendChild(empty);
      }

      for (let day = 1; day <= daysInMonth; day++) {
        const dateCell = document.createElement("button");

        dateCell.type = "button";

        dateCell.className = "calendar-day";

        const dateString = `${currentYear}-${String(currentMonth + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;

        dateCell.dataset.date = dateString;

        dateCell.innerHTML = `

                <span class="calendar-date-number">
                    ${day}
                </span>

                <span
                    class="calendar-appointment-count"
                    data-count-date="${dateString}"
                >
                </span>

            `;

        const todayString =
          today.getFullYear() +
          "-" +
          String(today.getMonth() + 1).padStart(2, "0") +
          "-" +
          String(today.getDate()).padStart(2, "0");

        if (dateString === todayString) {
          dateCell.classList.add("today");
        }

        dateCell.addEventListener("click", function () {
          loadDateSchedule(this.dataset.date);
        });

        calendarDays.appendChild(dateCell);
      }

      loadMonthData();
    }

    async function loadMonthData() {
      try {
        const params = new URLSearchParams({
          year: currentYear,
          month: currentMonth + 1,
        });

        const response = await fetch(`${urls.calendar}?${params.toString()}`);

        if (!response.ok) {
          throw new Error("Could not load calendar");
        }

        const data = await response.json();

        const dates = data.dates || {};

        document
          .querySelectorAll(".calendar-day:not(.empty)")
          .forEach((dayCell) => {
            const date = dayCell.dataset.date;

            const countElement = dayCell.querySelector(
              ".calendar-appointment-count",
            );

            if (!countElement || !date) {
              return;
            }

            // Reset
            countElement.innerHTML = "";

            dayCell.classList.remove("has-schedule", "no-shift");

            countElement.classList.remove("calendar-no-shift");

            const info = dates[date];

            if (!info) {
              dayCell.classList.add("no-shift");

              countElement.classList.add("calendar-no-shift");

              countElement.innerHTML = `
                        <span>
                            No shifts
                        </span>
                    `;

              return;
            }

            const doctorCount = Number(info.doctors || 0);

            const appointmentCount = Number(info.appointments || 0);

            if (doctorCount > 0) {
              dayCell.classList.add("has-schedule");

              countElement.innerHTML = `
                        <span>
                            ${doctorCount}
                            Doctor${doctorCount !== 1 ? "s" : ""}
                            ·
                            ${appointmentCount}
                            Appointment${appointmentCount !== 1 ? "s" : ""}
                        </span>
                    `;
            } else {
              dayCell.classList.add("no-shift");

              countElement.classList.add("calendar-no-shift");

              countElement.innerHTML = `
                        <span>
                            No shifts
                        </span>
                    `;
            }
          });
      } catch (error) {
        console.error("Calendar month error:", error);
      }
    }

    async function loadDateSchedule(date) {
      openModal();

      modalDate.textContent = formatDate(date);

      modalSummary.textContent = "Loading...";

      doctorList.innerHTML = `

            <div class="schedule-loading">

                <i data-lucide="loader-circle"></i>

                <span>
                    Loading doctor schedules...
                </span>

            </div>

        `;

      if (window.lucide) {
        lucide.createIcons();
      }

      try {
        const response = await fetch(`${urls.calendar}?date=${date}`);

        if (!response.ok) {
          throw new Error("Could not load schedule");
        }

        const data = await response.json();
        modalDate.textContent = data.date_display || formatDate(date);

        modalSummary.textContent = `${data.total_doctors || 0} Doctors · ${data.total_appointments || 0} Appointments`;

        renderDoctors(data.doctors || []);
      } catch (error) {
        console.error("Date schedule error:", error);

        doctorList.innerHTML = `

                <div class="schedule-empty">

                    <i data-lucide="circle-alert"></i>

                    <p>
                        Unable to load doctor schedule.
                    </p>

                </div>

            `;

        if (window.lucide) {
          lucide.createIcons();
        }
      }
    }
    function renderDoctors(doctors) {
      doctorList.innerHTML = "";

      if (!doctors.length) {
        doctorList.innerHTML = `

                <div class="schedule-empty">

                    <i data-lucide="calendar-x"></i>

                    <p>
                        No doctor schedules available.
                    </p>

                </div>

            `;

        if (window.lucide) {
          lucide.createIcons();
        }

        return;
      }

      doctors.forEach((doctor) => {
        const appointmentCount = Number(doctor.appointment_count || 0);

        const startTime = doctor.start_time || "";

        const endTime = doctor.end_time || "";

        const shiftTime =
          startTime && endTime ? `${startTime} - ${endTime}` : "-";

        const card = document.createElement("div");

        card.className = "doctor-schedule-item";

        card.innerHTML = `

                    <div class="doctor-schedule-main">

                        <div class="doctor-avatar">

                            <i data-lucide="user-round"></i>

                        </div>


                        <div class="doctor-info">

                            <h4>
                                ${escapeHtml(doctor.doctor_name || "-")}
                            </h4>


                            <p class="doctor-department">

                                ${escapeHtml(doctor.department_name || "-")}

                            </p>


                            <div class="doctor-shift">

                                <span class="shift-name">

                                    ${escapeHtml(doctor.shift_name || "-")}

                                </span>


                                <span class="shift-time">

                                    ${escapeHtml(shiftTime)}

                                </span>

                            </div>

                        </div>

                    </div>


                    <div class="doctor-appointment-count">

                        <strong>
                            ${appointmentCount}
                        </strong>

                        <span>
                            Appointment${appointmentCount !== 1 ? "s" : ""}
                        </span>

                    </div>

                `;

        doctorList.appendChild(card);
      });

      if (window.lucide) {
        lucide.createIcons();
      }
    }

    function openModal() {
      modalOverlay.classList.add("active");

      document.body.classList.add("modal-open");
    }

    function closeModal() {
      modalOverlay.classList.remove("active");

      document.body.classList.remove("modal-open");
    }

    modalClose.addEventListener("click", closeModal);

    modalOverlay.addEventListener("click", function (event) {
      if (event.target === modalOverlay) {
        closeModal();
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && modalOverlay.classList.contains("active")) {
        closeModal();
      }
    });

    prevMonthBtn.addEventListener("click", function () {
      currentMonth--;

      if (currentMonth < 0) {
        currentMonth = 11;

        currentYear--;
      }

      renderCalendar();
    });

    nextMonthBtn.addEventListener("click", function () {
      currentMonth++;

      if (currentMonth > 11) {
        currentMonth = 0;

        currentYear++;
      }

      renderCalendar();
    });

    function escapeHtml(value) {
      const div = document.createElement("div");

      div.textContent = value ?? "";

      return div.innerHTML;
    }
    renderCalendar();
  }

  updateRegistrationDetails();

  loadSchedules();

  loadQueue();

  loadAppointments();

  initDoctorScheduleCalendar();
});
