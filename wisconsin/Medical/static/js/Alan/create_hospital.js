// ─── AOS Init ───
AOS.init({
  duration: 700,
  once: true,
  offset: 30,
  easing: "ease-out-quad",
});

const directorChoices = new Choices("#directorName", {
  searchEnabled: true,
  shouldSort: false,
});

const hospitalStatusChoices = new Choices("#hospitalStatus", {
  searchEnabled: false,
});

const estYearChoices = new Choices("#estYear", {
  searchEnabled: false,
});

const selectedDepartments = new Map();

const hospitalDepartment = new Choices("#hospitalDepartment", {
    searchEnabled: false,
    shouldSort: false,
    removeItemButton: false,
});

const hospitalBuilding = new Choices("#hospitalBuilding", {
  searchEnabled: true,
  shouldSort: false,
});


// ─── Multiple Hospital Departments ───

const selectedDepartmentsContainer =
    document.getElementById("selectedDepartments");


hospitalDepartment.passedElement.element.addEventListener(
    "addItem",
    function (event) {

        const departmentId = String(event.detail.value);
        const departmentName = event.detail.label;

        if (!departmentId) return;

        // Prevent duplicate department
        if (selectedDepartments.has(departmentId)) {
            hospitalDepartment.removeActiveItems();
            return;
        }

        selectedDepartments.set(
            departmentId,
            departmentName
        );

        renderSelectedDepartments();

        // Reset dropdown so another department can be selected
        hospitalDepartment.removeActiveItems();
    }
);


function renderSelectedDepartments() {

    if (!selectedDepartmentsContainer) return;

    selectedDepartmentsContainer.innerHTML = "";

    selectedDepartments.forEach(
        (departmentName, departmentId) => {

            const pill = document.createElement("div");

            pill.className = "department-pill";

            pill.innerHTML = `
                <span class="department-pill-name">
                    ${departmentName}
                </span>

                <button
                    type="button"
                    class="department-pill-remove"
                    data-id="${departmentId}"
                    aria-label="Remove ${departmentName}"
                >
                    ×
                </button>
            `;

            selectedDepartmentsContainer.appendChild(pill);
        }
    );
}


if (selectedDepartmentsContainer) {

    selectedDepartmentsContainer.addEventListener(
        "click",
        function (event) {

            const removeButton =
                event.target.closest(
                    ".department-pill-remove"
                );

            if (!removeButton) return;

            const departmentId =
                removeButton.dataset.id;

            selectedDepartments.delete(departmentId);

            renderSelectedDepartments();
        }
    );
}

// ─── Character Counters ───
document.getElementById("shortDesc").addEventListener("input", function () {
  document.getElementById("shortDescCount").textContent = this.value.length;
  const count = document.getElementById("shortDescCount");
  if (this.value.length > 50) count.className = "count warning";
  if (this.value.length >= 120) count.className = "count danger";
  else count.className = "count";
});

document.getElementById("aboutHospital").addEventListener("input", function () {
  document.getElementById("aboutHospitalCount").textContent = this.value.length;
  const count = document.getElementById("aboutHospitalCount");
  if (this.value.length > 420) count.className = "count warning";
  if (this.value.length >= 500) count.className = "count danger";
  else count.className = "count";
});

// ─── Banner Upload ───
document.getElementById("bannerInput").addEventListener("change", function (e) {
  const file = e.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function (ev) {
      const preview = document.getElementById("bannerPreview");
      const img = document.getElementById("bannerImg");
      img.src = ev.target.result;
      preview.style.display = "block";
    };
    reader.readAsDataURL(file);
  }
});

// ─── Drag and Drop for Banner ───
const bannerUpload = document.getElementById("bannerUpload");
["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
  bannerUpload.addEventListener(eventName, (e) => {
    e.preventDefault();
    e.stopPropagation();
  });
});
bannerUpload.addEventListener("dragover", () =>
  bannerUpload.classList.add("dragover"),
);
bannerUpload.addEventListener("dragleave", () =>
  bannerUpload.classList.remove("dragover"),
);
bannerUpload.addEventListener("drop", (e) => {
  bannerUpload.classList.remove("dragover");
  const files = e.dataTransfer.files;
  if (files.length) {
    document.getElementById("bannerInput").files = files;
    document.getElementById("bannerInput").dispatchEvent(new Event("change"));
  }
});

// ─── Medical Facilities Data ───
const medicalFacilities = window.medicalFacilities || [];

// ─── Available icons for picker ───
const availableIcons = [
  // ─── Hospital & Buildings ───
  "bi-hospital",
  "bi-hospital-fill",
  "bi-building",
  "bi-building-fill",
  "bi-house",
  "bi-house-fill",
  "bi-house-heart",
  "bi-house-heart-fill",

  // ─── Medical & Healthcare ───
  "bi-heart",
  "bi-heart-fill",
  "bi-heart-pulse",
  "bi-heart-pulse-fill",
  "bi-activity",
  "bi-capsule",
  "bi-capsule-pill",
  "bi-prescription",
  "bi-prescription2",
  "bi-bandaid",
  "bi-bandaid-fill",
  "bi-thermometer",
  "bi-eyedropper",
  "bi-lungs",
  "bi-lungs-fill",
  "bi-virus",
  "bi-virus2",
  "bi-bug",
  "bi-bug-fill",
  "bi-clipboard2-pulse",
  "bi-clipboard2-pulse-fill",
  "bi-clipboard2-heart",
  "bi-clipboard2-heart-fill",

  // ─── Laboratory ───
  "bi-flask",
  "bi-flask-fill",
  "bi-beaker",
  "bi-beaker-fill",
  "bi-droplet",
  "bi-droplet-fill",
  "bi-droplet-half",

  // ─── Equipment ───
  "bi-cpu",
  "bi-camera",
  "bi-camera-fill",
  "bi-eye",
  "bi-eye-fill",
  "bi-display",
  "bi-display-fill",
  "bi-speaker",
  "bi-speaker-fill",
  "bi-soundwave",
  "bi-lightning",
  "bi-lightning-fill",

  // ─── People & Care ───
  "bi-person",
  "bi-person-fill",
  "bi-person-heart",
  "bi-person-plus",
  "bi-person-plus-fill",
  "bi-person-check",
  "bi-person-check-fill",
  "bi-person-vcard",
  "bi-person-vcard-fill",
  "bi-person-badge",
  "bi-person-badge-fill",
  "bi-person-wheelchair",
  "bi-person-walking",
  "bi-person-arms-up",
  "bi-people",
  "bi-people-fill",

  // ─── Emergency & Safety ───

  "bi-fire",

  "bi-truck",
  "bi-shield",
  "bi-shield-fill",
  "bi-shield-check",
  "bi-shield-fill-check",
  "bi-exclamation-triangle",
  "bi-exclamation-triangle-fill",

  // ─── Hospital Facilities ───
  "bi-door-open",
  "bi-door-open-fill",
  "bi-door-closed",
  "bi-door-closed-fill",

  "bi-p-circle",
  "bi-arrow-up-circle",
  "bi-wifi",
  "bi-cash",
  "bi-credit-card",
  "bi-credit-card-fill",
  "bi-bank",
  "bi-shop",
  "bi-cup-hot",
  "bi-cup-hot-fill",

  // ─── Maintenance & Utilities ───
  "bi-tools",
  "bi-wrench",
  "bi-wrench-adjustable",
  "bi-hammer",
  "bi-gear",
  "bi-gear-fill",
  "bi-lightbulb",
  "bi-lightbulb-fill",
  "bi-plug",
  "bi-plug-fill",
  "bi-box-seam",
  "bi-box-seam-fill",

  // ─── General ───
  "bi-grid-3x3-gap-fill",
  "bi-stars",
  "bi-star",
  "bi-star-fill",
  "bi-award",
  "bi-award-fill",
  "bi-bookmark",
  "bi-bookmark-fill",
  "bi-patch-check",
  "bi-patch-check-fill",
  "bi-check-circle",
  "bi-check-circle-fill",
];

function renderIconPicker(containerId, selectedInputId) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";
  availableIcons.forEach((icon) => {
    const div = document.createElement("div");
    div.className = "icon-option";
    div.innerHTML = `<i class="bi ${icon}"></i>`;
    div.dataset.icon = icon;
    if (icon === "bi-plus-circle" || icon === "bi-building") {
      div.classList.add("selected");
    }
    div.addEventListener("click", function () {
      container
        .querySelectorAll(".icon-option")
        .forEach((el) => el.classList.remove("selected"));
      this.classList.add("selected");
      document.getElementById(selectedInputId).value = this.dataset.icon;
    });
    container.appendChild(div);
  });
}

renderIconPicker("medicalIconPicker", "selectedMedicalIcon");
renderIconPicker("otherIconPicker", "selectedOtherIcon");

// ─── Render Medical Facilities ───
const grid = document.getElementById("medicalFacilitiesGrid");

function renderMedicalFacilities() {
  grid.innerHTML = "";
  medicalFacilities.forEach((item) => {
    const col = document.createElement("div");
    col.className = "col-4 col-md-3 col-lg-2";
    const iconClass = item.icon || "bi-plus-circle";
    col.innerHTML = `
                        <div class="facility-toggle-card" data-facility="${item.name}" onclick="toggleFacility(this, event)">
                            <div class="facility-icon"><i class="bi ${iconClass}"></i></div>
                            <div class="facility-name">${item.name}</div>
                            <div class="toggle-switch">
                                <input type="checkbox" class="facility-checkbox" data-id="${item.id}" />
                                <span class="slider"></span>
                            </div>
                        </div>
                    `;
    grid.appendChild(col);
  });

  // Re-bind checkbox events
  document
    .querySelectorAll(".facility-toggle-card .toggle-switch input")
    .forEach((input) => {
      input.addEventListener("change", function () {
        const card = this.closest(".facility-toggle-card");
        if (this.checked) {
          card.classList.add("active");
        } else {
          card.classList.remove("active");
        }

        // Clear validation error
        document.getElementById("MedicalFacilitiesError").textContent = "";
      });
    });
}

renderMedicalFacilities();

// ─── Get Selected Facilities ───
// This function returns an array of selected facility IDs based on the checked checkboxes in the medical facilities grid.
function getSelectedFacilities() {
  const selectedFacilities = [];

  document
    .querySelectorAll(".facility-checkbox:checked")
    .forEach((checkbox) => {
      selectedFacilities.push(Number(checkbox.dataset.id));
    });

  return selectedFacilities;
}

// getting selected other facilities

function getSelectedOtherFacilities() {
  console.log("Other Facilities Called");

  const selectedFacilities = [];

  document.querySelectorAll(".other-facility-card.selected").forEach((card) => {
    selectedFacilities.push(Number(card.dataset.id));
  });

  return selectedFacilities;
}

// ─── Toggle Facility ───
function toggleFacility(el, event) {
  const checkbox = el.querySelector(".toggle-switch input");
  checkbox.checked = !checkbox.checked;
  checkbox.dispatchEvent(new Event("change"));
  if (checkbox.checked) {
    el.classList.add("active");
  } else {
    el.classList.remove("active");
  }
  // Ripple
  const ripple = document.createElement("span");
  ripple.className = "ripple";
  const rect = el.getBoundingClientRect();
  const x =
    (event.clientX ||
      event.touches?.[0]?.clientX ||
      rect.left + rect.width / 2) - rect.left;
  const y =
    (event.clientY ||
      event.touches?.[0]?.clientY ||
      rect.top + rect.height / 2) - rect.top;
  ripple.style.left = x + "px";
  ripple.style.top = y + "px";
  ripple.style.width = "20px";
  ripple.style.height = "20px";
  el.appendChild(ripple);
  setTimeout(() => ripple.remove(), 700);
}

// ─── Add Medical Facility ───

const medicalModal = document.getElementById("addMedicalFacilityModal");

medicalModal.addEventListener("hidden.bs.modal", function () {
  // Remove focus
  if (document.activeElement) {
    document.activeElement.blur();
  }

  // Force cleanup
  document.body.classList.remove("modal-open");
  document.body.style.removeProperty("overflow");
  document.body.style.removeProperty("padding-right");

  document.querySelectorAll(".modal-backdrop").forEach((backdrop) => {
    backdrop.remove();
  });
});

document
  .getElementById("newMedicalFacilityName")
  .addEventListener("input", function () {
    this.classList.remove("is-invalid");
  });

// ─── Other Facilities ───
const otherFacilities = window.otherFacilities || [];

const otherGrid = document.getElementById("otherFacilitiesGrid");

function renderOtherFacilities() {
  otherGrid.innerHTML = "";
  otherFacilities.forEach((item, index) => {
    const col = document.createElement("div");
    col.className = "col-4 col-md-3 col-lg-2";
    col.innerHTML = `
                        <div class="other-facility-card" data-id="${item.id}" data-name="${item.name}" onclick="toggleOtherFacility(this)">
                            <span class="check-mark"><i class="bi bi-check-circle-fill"></i></span>
                            <div class="of-icon"><i class="bi ${item.icon}"></i></div>
                            <div class="of-name">${item.name}</div>
                        </div>
                    `;
    otherGrid.appendChild(col);
  });
}

renderOtherFacilities();

function toggleOtherFacility(el) {
  el.classList.toggle("selected");
}

// ─── Add Other Facility ───

const otherModal = document.getElementById("addOtherFacilityModal");

otherModal.addEventListener("hidden.bs.modal", function () {
  if (document.activeElement) {
    document.activeElement.blur();
  }

  document.body.classList.remove("modal-open");
  document.body.style.removeProperty("overflow");
  document.body.style.removeProperty("padding-right");

  document.querySelectorAll(".modal-backdrop").forEach((backdrop) => {
    backdrop.remove();
  });
});

// ─── Form Validation ───
const form = document.getElementById("createHospitalForm");
const otherFacilityForm = document.getElementById("otherFacilityForm");

// SUBMIT OTHER FACILITY

otherFacilityForm.addEventListener("submit", function (e) {
  e.preventDefault();

  if (!validateOtherFacilityName()) {
    return;
  }

  const formData = new FormData(this);

  fetch("/medical/facilities/add/", {
    method: "POST",
    body: formData,
    headers: {
      "X-Requested-With": "XMLHttpRequest",
    },
  })
    .then(async (response) => {
      const data = await response.json();

      if (!response.ok) {
        throw data;
      }

      return data;
    })

    .then((data) => {
      if (data.success) {
        otherFacilities.push(data.facility);

        renderOtherFacilities();

        // Reset form
        this.reset();

        document.getElementById("selectedOtherIcon").value = "bi-building";

        // Close modal
        const modal = bootstrap.Modal.getOrCreateInstance(
          document.getElementById("addOtherFacilityModal"),
        );

        modal.hide();

        Swal.fire({
          toast: true,
          position: "top-end",
          icon: "success",
          title: data.message,
          showConfirmButton: false,
          timer: 2000,
          timerProgressBar: true,
          didOpen: (toast) => {
            toast.addEventListener("mouseenter", Swal.stopTimer);
            toast.addEventListener("mouseleave", Swal.resumeTimer);
          },
        });
      }
    })

    .catch((error) => {
      Swal.fire({
        toast: true,
        position: "top-end",
        icon: "error",
        title: "Something went wrong.",
        showConfirmButton: false,
        timer: 2500,
        timerProgressBar: true,
      });
    });
});

// ─── Reset ───
form
  .querySelector('button[type="reset"]')
  .addEventListener("click", function (e) {
    e.preventDefault();
    if (confirm("Reset all fields?")) {
      form.reset();
      document
        .querySelectorAll(".facility-toggle-card")
        .forEach((c) => c.classList.remove("active"));
      document
        .querySelectorAll(".facility-toggle-card .toggle-switch input")
        .forEach((i) => (i.checked = false));
      document
        .querySelectorAll(".other-facility-card")
        .forEach((c) => c.classList.remove("selected"));
      document.getElementById("bannerPreview").style.display = "none";
      document.getElementById("galleryPreview").innerHTML = "";
      document.getElementById("shortDescCount").textContent = "0";
      document.getElementById("aboutHospitalCount").textContent = "0";
      document.querySelectorAll(".form-control").forEach((f) => {
        f.classList.remove("is-valid", "is-invalid");
      });
      //   document
      //     .querySelectorAll(".invalid-feedback")
      //     .forEach((f) => f.classList.remove("show"));
      //   document.getElementById("emergencyToggle").checked = true;
    }
  });


// add facility

const medicalFacilityForm = document.getElementById("medicalFacilityForm");

medicalFacilityForm.addEventListener("submit", function (e) {
  e.preventDefault();

  // Frontend validation
  if (!validateFacilityName()) {
    return;
  }

  // Clear previous errors
  facilityNameInput.classList.remove("is-invalid");
  facilityNameError.textContent = "";

  const formData = new FormData(this);

  fetch("/medical/facilities/add/", {
    method: "POST",
    body: formData,
    headers: {
      "X-Requested-With": "XMLHttpRequest",
    },
  })
    .then(async (response) => {
      const data = await response.json();

      // Backend validation failed
      if (!response.ok) {
        throw data;
      }

      return data;
    })
    .then((data) => {
      if (data.success) {
        // Add new facility to UI
        medicalFacilities.push(data.facility);

        renderMedicalFacilities();

        // Reset form
        this.reset();

        facilityNameInput.classList.remove("is-invalid");
        facilityNameError.textContent = "";

        document.getElementById("selectedMedicalIcon").value = "bi-plus-circle";

        // Close modal
        bootstrap.Modal.getInstance(
          document.getElementById("addMedicalFacilityModal"),
        ).hide();

        Swal.fire({
          icon: "success",
          title: "Success",
          text: data.message,
          timer: 1500,
          showConfirmButton: false,
        });
      }
    })
    .catch((error) => {
      console.error(error);

      // Backend validation errors
      if (error.errors) {
        if (error.errors.name) {
          facilityNameInput.classList.add("is-invalid");
          facilityNameError.textContent = error.errors.name[0];
          facilityNameInput.focus();
          return;
        }
      }

      Swal.fire({
        icon: "error",
        title: "Error",
        text: "Something went wrong.",
      });
    });
});

const hospitalId = document.getElementById("hospital_uuid").value;

if (hospitalId) {
  loadHospital(hospitalId);
}

// hospital edit detail fetch
async function loadHospital(hospitalId) {
  const response = await fetch(`/medical/hospital/${hospitalId}/detail/`);

  const data = await response.json();

  if (!data.success) return;

  const h = data.hospital;


  document.getElementById("hospitalName").value = h.hospital_name;
  document.getElementById("shortDesc").value = h.short_description;
  document.getElementById("aboutHospital").value = h.about_hospital;

  directorChoices.setChoiceByValue(String(h.director_id || ""));

  // Hospital Departments

selectedDepartments.clear();

(h.department_ids || []).forEach((id) => {

    const option = document.querySelector(
        `#hospitalDepartment option[value="${id}"]`
    );

    if (!option) return;

    selectedDepartments.set(
        String(id),
        option.textContent.trim()
    );
});

renderSelectedDepartments();

  hospitalBuilding.setChoiceByValue(String(h.building_id));

  estYearChoices.setChoiceByValue(String(h.established_year));
  hospitalStatusChoices.setChoiceByValue(h.hospital_status);


  document.getElementById("hospitalPhone").value = h.hospital_phone;

  document.getElementById("emergencyPhone").value = h.hospital_emgphone;

  document.getElementById("email").value = h.hospital_email;

  if (h.hospital_banner) {
    const bannerPreview = document.getElementById("bannerPreview");
    const bannerImg = document.getElementById("bannerImg");

    bannerImg.src = h.hospital_banner;

    bannerImg.onload = function () {
      bannerPreview.style.display = "block";
    };
  }

  // Medical Facilities

  document.querySelectorAll(".facility-checkbox").forEach((cb) => {
    cb.checked = false;

    cb.closest(".facility-toggle-card").classList.remove("active");
  });

  h.selected_facilities.forEach((id) => {
    const checkbox = document.querySelector(
      `.facility-checkbox[data-id="${id}"]`,
    );

    if (!checkbox) return;

    checkbox.checked = true;

    checkbox.closest(".facility-toggle-card").classList.add("active");
  });

  // Other Facilities

  document.querySelectorAll(".other-facility-card").forEach((card) => {
    card.classList.remove("selected");
  });

  h.selected_other_facilities.forEach((id) => {
    const card = document.querySelector(
      `.other-facility-card[data-id="${id}"]`,
    );

    if (card) {
      card.classList.add("selected");
    }
  });
}
