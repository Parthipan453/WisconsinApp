"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("patientForm");
  if (!form) return;

  const patientType = document.getElementById("patientType");

  const searchKeyword = document.getElementById("searchKeyword");
  const searchBtn = document.getElementById("searchBtn");
  const searchResultsList = document.getElementById("searchResultsList");
  const searchRow = document.getElementById("searchRow");
  const visitorBlock = document.getElementById("visitorBlock");
  const checklist = document.getElementById("registrationChecklist");

  const selectedProfileId = document.getElementById("selectedProfileId");
  const selectedPersonBlock = document.getElementById("selectedPersonBlock");
  const clearSelectionBtn = document.getElementById("clearSelectionBtn");
  const athleteBadge = document.getElementById("athleteBadge");

  const universityId = document.getElementById("universityId");
  const fullName = document.getElementById("fullName");
  const gender = document.getElementById("gender");
  const dob = document.getElementById("dob");
  const mobile = document.getElementById("mobile");
  const email = document.getElementById("email");

  allowOnlyLetters(document.getElementById("visitorName"));
  allowOnlyLetters(document.getElementById("emergencyName"));
  allowOnlyNumbers(document.getElementById("visitorMobile"));
  allowOnlyNumbers(document.getElementById("emergencyPhone"));

  const bloodRadios = document.querySelectorAll("input[name='blood_group']");

  const emergencyName = document.getElementById("emergencyName");
  const emergencyPhone = document.getElementById("emergencyPhone");

  const previewAvatar = document.getElementById("previewAvatar");
  const previewAvatarImg = document.getElementById("previewAvatarImg");
  const previewAvatarIcon = document.getElementById("previewAvatarIcon");

  const previewName = document.getElementById("previewName");
  const previewType = document.getElementById("previewType");
  const summaryUniversity = document.getElementById("summaryUniversity");
  const summaryBlood = document.getElementById("summaryBlood");
  const summaryPhone = document.getElementById("summaryPhone");
  const summaryEmail = document.getElementById("summaryEmail");

  const submitBtn = document.getElementById("submitBtn");
  const resetBtn = document.getElementById("resetBtn");

  const SEARCH_URL =
    form.dataset.searchUrl || "/medical/patients/ajax/search-members/";

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  const csrftoken = getCookie("csrftoken");

  /* ------------------------------------------------------
      //  Init SlimSelect on patient type
    ------------------------------------------------------ */

  const patientTypeSelect = new SlimSelect({
    select: patientType,
    settings: {
      showSearch: false,
      placeholderText: "Select Patient Type",
    },
  });
  // gender for visitor
  const visitorGender = document.getElementById("visitorGender");

  const visitorGenderSelect = new SlimSelect({
    select: visitorGender,
    settings: {
      showSearch: false,
      placeholderText: "Select Gender",
    },
  });

  function allowOnlyLetters(input) {
    input.addEventListener("input", function () {
      this.value = this.value.replace(/[^a-zA-Z\s]/g, "");
    });
  }

  function allowOnlyNumbers(input) {
    input.addEventListener("input", function () {
      this.value = this.value.replace(/[^\d+]/g, "");

      if (this.value.includes("+")) {
        this.value = "+" + this.value.substring(1).replace(/\+/g, "");
      }
    });
  }
  /* ------------------------------------------------------
       Toast
    ------------------------------------------------------ */

  function showToast(message, type = "success") {
    const toast = document.createElement("div");
    toast.className = `ap-toast ${type}`;
    toast.innerHTML = `
            <i class="bi ${type === "success" ? "bi-check-circle-fill" : "bi-exclamation-circle-fill"}"></i>
            <span>${message}</span>
        `;
    document.body.appendChild(toast);

    requestAnimationFrame(() => toast.classList.add("show"));

    setTimeout(() => {
      toast.classList.remove("show");
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  /* ------------------------------------------------------
       Field error helpers
    ------------------------------------------------------ */

  function setFieldError(field, message) {
    if (!field) return;
    field.classList.add("is-invalid");

    let feedback = field.parentNode.querySelector(".invalid-feedback");
    if (!feedback) {
      feedback = document.createElement("div");
      feedback.className = "invalid-feedback";
      field.parentNode.appendChild(feedback);
    }
    feedback.textContent = message;
  }

  function clearFieldError(field) {
    if (!field) return;
    field.classList.remove("is-invalid");
    const feedback = field.parentNode.querySelector(".invalid-feedback");
    if (feedback) feedback.remove();
  }

  function clearSearchError() {
    const wrapper = searchKeyword.closest(".ap-group");
    const feedback = wrapper.querySelector(".invalid-feedback");
    if (feedback) feedback.remove();
    searchKeyword.classList.remove("is-invalid");
  }

  form.querySelectorAll("input, select, textarea").forEach((field) => {
    field.addEventListener("input", () => clearFieldError(field));
    field.addEventListener("change", () => clearFieldError(field));
  });

  /* ------------------------------------------------------
       Patient type -> enable search
    ------------------------------------------------------ */

  patientType.addEventListener("change", () => {
    const type = patientType.value;
    const hasType = Boolean(type);

    searchKeyword.disabled = !hasType;
    searchBtn.disabled = !hasType;

    searchKeyword.value = "";
    searchResultsList.innerHTML = "";
    searchResultsList.classList.remove("show");

    const hint = searchRow.querySelector("small");

    switch (type) {
      case "STUDENT":
        hint.textContent = "Search Student by Name or University ID.";
        searchKeyword.placeholder = "Search Student...";
        searchRow.style.display = "";
        visitorBlock.style.display = "none";
        break;

      case "FACULTY":
        hint.textContent = "Search Faculty by Name or Employee ID.";
        searchKeyword.placeholder = "Search Faculty...";
        searchRow.style.display = "";
        visitorBlock.style.display = "none";
        break;

      case "STAFF":
        hint.textContent = "Search Staff by Name or Employee ID.";
        searchKeyword.placeholder = "Search Staff...";
        searchRow.style.display = "";
        visitorBlock.style.display = "none";
        break;

      case "ADMIN":
        hint.textContent = "Search Admin by Name, Username or University ID.";
        searchKeyword.placeholder = "Search Admin...";
        searchRow.style.display = "";
        visitorBlock.style.display = "none";
        break;

      case "VISITOR":
        searchRow.style.display = "none";
        visitorBlock.style.display = "";
        break;

      default:
        hint.textContent = "Select a Patient Type above to search.";
        searchKeyword.placeholder = "Search...";
        searchRow.style.display = "";
        visitorBlock.style.display = "none";
    }

    if (checklist) {
      if (type === "VISITOR") {
        checklist.innerHTML = `
                <li>Select Visitor.</li>
                <li>Enter Visitor Details.</li>
                <li>Provide Emergency Contact.</li>
                <li>Save Patient.</li>
            `;
      } else {
        checklist.innerHTML = `
                <li>Select Patient Type.</li>
                <li>Search University Member.</li>
                <li>Verify Personal Details.</li>
                <li>Enter Medical Information.</li>
                <li>Save Patient.</li>
            `;
      }
    }

    clearSelection();
    updatePreview();
  });
  /* ------------------------------------------------------
       Search
    ------------------------------------------------------ */

  async function runSearch() {
    clearSearchError();

    const keyword = searchKeyword.value.trim();

    if (!patientType.value) {
      showToast("Select a Patient Type first.", "warning");
      return;
    }

    if (!keyword) {
      setFieldError(searchKeyword, "Enter a name or ID to search.");
      return;
    }

    searchBtn.disabled = true;
    searchBtn.innerHTML = `<span class="ap-spinner"></span>`;

    try {
      const response = await fetch(SEARCH_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": csrftoken,
        },
        body: new URLSearchParams({
          patient_type: patientType.value,
          keyword: keyword,
        }),
      });

      const data = await response.json();

      searchBtn.disabled = false;
      searchBtn.innerHTML = `<i class="bi bi-search"></i>`;

      if (!data.success) {
        showToast(data.message || "Search failed.", "danger");
        return;
      }

      renderResults(data.results);
    } catch (err) {
      console.error(err);
      searchBtn.disabled = false;
      searchBtn.innerHTML = `<i class="bi bi-search"></i>`;
      showToast("Server error while searching.", "danger");
    }
  }

  searchBtn.addEventListener("click", runSearch);

  searchKeyword.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      runSearch();
    }
  });

  function renderResults(results) {
    searchResultsList.innerHTML = "";

    if (!results.length) {
      searchResultsList.innerHTML = `<div class="ap-search-empty">No matching, unregistered members found.</div>`;
      searchResultsList.classList.add("show");
      return;
    }

    // results.forEach((person) => {
    //   const item = document.createElement("div");
    //   item.className = "ap-search-item";
    //   item.innerHTML = `
    //             <div class="ap-search-item-avatar">
    //                 ${
    //                   person.photo
    //                     ? `<img src="${person.photo}" alt="">`
    //                     : `<i class="bi bi-person-fill"></i>`
    //                 }
    //             </div>
    //             <div class="ap-search-item-info">
    //                 <strong>${person.full_name}</strong>
    //                 <span>${person.university_id || "—"}</span>
    //             </div>
    //         `;
    //   item.addEventListener("click", () => selectPerson(person));
    //   searchResultsList.appendChild(item);
    // });
    results.forEach((person) => {
      const item = document.createElement("div");

      item.className = "ap-search-item";

      // =====================================================
      // ATHLETE BADGE
      // =====================================================

      const athleteBadge = person.is_athlete
        ? `
      <span class="ap-athlete-badge">
          <i class="bi bi-trophy-fill"></i>
          Athlete
      </span>
    `
        : "";

      item.innerHTML = `

      <div class="ap-search-item-avatar">

          ${
            person.photo
              ? `<img src="${person.photo}" alt="">`
              : `<i class="bi bi-person-fill"></i>`
          }

      </div>


      <div class="ap-search-item-info">

          <div class="ap-search-name-row">

              <strong>
                  ${person.full_name}
              </strong>

              ${athleteBadge}

          </div>


          <span>
              ${person.university_id || "—"}
          </span>

      </div>

  `;

      item.addEventListener("click", () => selectPerson(person));

      searchResultsList.appendChild(item);
    });
    searchResultsList.classList.add("show");
  }

  /* ------------------------------------------------------
       Select / clear person
    ------------------------------------------------------ */

  let currentPhoto = null;

  // function selectPerson(person) {
  //   selectedProfileId.value = person.profile_id;

  //   universityId.value = person.university_id || "";
  //   fullName.value = person.full_name || "";
  //   gender.value = person.gender || "";
  //   dob.value = person.date_of_birth || "";
  //   mobile.value = person.mobile || "";
  //   email.value = person.email || "";

  //   currentPhoto = person.photo || null;

  //   selectedPersonBlock.style.display = "block";
  //   searchResultsList.innerHTML = "";
  //   searchResultsList.classList.remove("show");
  //   searchKeyword.value = person.full_name;

  //   updatePreview();
  // }

  function selectPerson(person) {

    selectedProfileId.value = person.profile_id;

    universityId.value = person.university_id || "";
    fullName.value = person.full_name || "";
    gender.value = person.gender || "";
    dob.value = person.date_of_birth || "";
    mobile.value = person.mobile || "";
    email.value = person.email || "";

    currentPhoto = person.photo || null;


    // =====================================================
    // ATHLETE BADGE
    // =====================================================

    if (athleteBadge) {

        if (person.is_athlete === true) {

            athleteBadge.style.display = "inline-flex";

        } else {

            athleteBadge.style.display = "none";

        }
    }


    // =====================================================
    // SHOW SELECTED PERSON
    // =====================================================

    selectedPersonBlock.style.display = "block";

    searchResultsList.innerHTML = "";

    searchResultsList.classList.remove("show");

    searchKeyword.value = person.full_name;


    updatePreview();
}

  // function clearSelection() {
  //   selectedProfileId.value = "";

  //   universityId.value = "";
  //   fullName.value = "";
  //   gender.value = "";
  //   dob.value = "";
  //   mobile.value = "";
  //   email.value = "";

  //   currentPhoto = null;

  //   selectedPersonBlock.style.display = "none";
  // }

  function clearSelection() {

    selectedProfileId.value = "";

    universityId.value = "";
    fullName.value = "";
    gender.value = "";
    dob.value = "";
    mobile.value = "";
    email.value = "";

    currentPhoto = null;


    // Hide athlete badge
    if (athleteBadge) {
        athleteBadge.style.display = "none";
    }


    selectedPersonBlock.style.display = "none";
}

  clearSelectionBtn.addEventListener("click", () => {
    clearSelection();
    searchKeyword.value = "";
    searchKeyword.focus();
    updatePreview();
  });

  /* ------------------------------------------------------
       Validation
    ------------------------------------------------------ */

  function validatePhone(value) {
    // return /^[6-9]\d{9}$/.test(value.trim());
    return /^\+?[1-9]\d{8,14}$/.test(value.trim());
  }
  function validateEmail(value) {
    // return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
    //  return /^[^\s@]+@[^\s@]+\.com$/i.test(value.trim());
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
  }

  function validateForm() {
    let valid = true;

    if (!patientType.value) {
      setFieldError(patientType, "Please select a patient type.");
      valid = false;
    }

    if (patientType.value !== "VISITOR") {
      if (!selectedProfileId.value) {
        setFieldError(
          searchKeyword,
          "Please search and select a university member.",
        );
        valid = false;
      }
    } else {
      if (!document.getElementById("visitorName").value.trim()) {
        setFieldError(
          document.getElementById("visitorName"),
          "Visitor name is required.",
        );
        valid = false;
      }

      if (!validatePhone(document.getElementById("visitorMobile").value)) {
        setFieldError(
          document.getElementById("visitorMobile"),
          "Enter a valid mobile number.",
        );
        valid = false;
      }
      const visitorEmail = document.getElementById("visitorEmail");

      if (visitorEmail.value.trim() && !validateEmail(visitorEmail.value)) {
        setFieldError(visitorEmail, "Enter a valid email address.");
        valid = false;
      }
    }

    if (!emergencyName.value.trim()) {
      setFieldError(emergencyName, "Emergency contact name is required.");
      valid = false;
    }

    if (!emergencyPhone.value.trim()) {
      setFieldError(emergencyPhone, "Emergency contact number is required.");
      valid = false;
    } else if (
      !validatePhone(emergencyPhone.value.replace(/\D/g, "").slice(-10))
    ) {
      setFieldError(
        emergencyPhone,
        "Enter a valid (9-15 digit) contact number.",
      );
      valid = false;
    }

    if (!valid) {
      showToast("Please correct the highlighted fields.", "danger");
    }

    return valid;
  }

  /* ------------------------------------------------------
       Live preview card
    ------------------------------------------------------ */

  function updatePreview() {
    if (patientType.value === "VISITOR") {
      const visitorName = document.getElementById("visitorName").value.trim();
      const visitorMobile = document
        .getElementById("visitorMobile")
        .value.trim();
      const visitorEmail = document.getElementById("visitorEmail").value.trim();

      previewName.textContent = visitorName || "No Visitor Selected";
      previewType.textContent = "Visitor";

      summaryUniversity.textContent = "Visitor";
      summaryPhone.textContent = visitorMobile || "—";
      summaryEmail.textContent = visitorEmail || "—";
    } else {
      previewName.textContent = fullName.value.trim() || "No Patient Selected";

      const labels = {
        STUDENT: "Student",
        FACULTY: "Faculty",
        STAFF: "Staff",
        ADMIN: "Admin",
        VISITOR: "Visitor",
      };

      previewType.textContent = labels[patientType.value] || "—";

      summaryUniversity.textContent = universityId.value.trim() || "—";
      summaryPhone.textContent = mobile.value.trim() || "—";
      summaryEmail.textContent = email.value.trim() || "—";
    }

    const checkedBlood = document.querySelector(
      "input[name='blood_group']:checked",
    );
    summaryBlood.textContent = checkedBlood ? checkedBlood.value : "—";

    if (currentPhoto && patientType.value !== "VISITOR") {
      previewAvatarImg.src = currentPhoto;
      previewAvatarImg.style.display = "block";
      previewAvatarIcon.style.display = "none";
    } else {
      previewAvatarImg.style.display = "none";
      previewAvatarIcon.style.display = "block";
    }
  }

  bloodRadios.forEach((radio) => {
    radio.addEventListener("change", updatePreview);
  });
  const visitorName = document.getElementById("visitorName");
  const visitorMobile = document.getElementById("visitorMobile");
  const visitorEmail = document.getElementById("visitorEmail");

  [visitorName, visitorMobile, visitorEmail].forEach((field) => {
    if (field) {
      field.addEventListener("input", updatePreview);
    }
  });

  /* ------------------------------------------------------
       Submit button loading state
    ------------------------------------------------------ */

  function setSubmitLoading(state) {
    if (!submitBtn) return;

    if (state) {
      submitBtn.disabled = true;
      submitBtn.dataset.text = submitBtn.innerHTML;
      submitBtn.innerHTML = `<span class="ap-spinner"></span> Saving...`;
    } else {
      submitBtn.disabled = false;
      submitBtn.innerHTML =
        submitBtn.dataset.text ||
        `<i class="bi bi-check-circle-fill"></i> Save Patient`;
    }
  }

  /* ------------------------------------------------------
       Success animation
    ------------------------------------------------------ */

  function showSuccessAnimation(patientNumber) {
    const success = document.createElement("div");
    success.className = "ap-success-overlay";
    success.innerHTML = `
            <div class="ap-success-box">
                <div class="success-icon"><i class="bi bi-check-circle-fill"></i></div>
                <h3>Patient Added</h3>
                <p>${patientNumber ? `Patient Number: <strong>${patientNumber}</strong>` : "Medical profile created successfully."}</p>
            </div>
        `;
    document.body.appendChild(success);

    setTimeout(() => success.classList.add("show"), 50);

    setTimeout(() => {
      success.classList.remove("show");
      setTimeout(() => success.remove(), 400);
    }, 2200);
  }

  /* ------------------------------------------------------
       Server-side validation errors
    ------------------------------------------------------ */

  function showServerErrors(errors) {
    if (!errors) return;

    const fieldMap = {
      patient_type: patientType,
      selected_profile_id: searchKeyword,
      emergency_contact_name: emergencyName,
      emergency_contact_phone: emergencyPhone,
      visitor_name: document.getElementById("visitorName"),
      visitor_phone: document.getElementById("visitorMobile"),
      visitor_email: document.getElementById("visitorEmail"),
    };

    Object.keys(errors).forEach((key) => {
      const field = fieldMap[key];
      const message = Array.isArray(errors[key]) ? errors[key][0] : errors[key];
      if (field) {
        setFieldError(field, message);
      }
    });
  }

  /* ------------------------------------------------------
       Reset
    ------------------------------------------------------ */

  function resetEntireForm() {
    form.reset();

    form.querySelectorAll(".is-invalid").forEach((f) => clearFieldError(f));

    clearSelection();
    searchKeyword.value = "";
    searchKeyword.disabled = true;
    searchBtn.disabled = true;
    searchResultsList.innerHTML = "";
    searchResultsList.classList.remove("show");

    updatePreview();
  }

  resetBtn.addEventListener("click", () => {
    // if (confirm("Reset the entire form?")) {
    //   resetEntireForm();
    // }
    resetEntireForm();
    patientTypeSelect.setSelected("");
  });

  /* ------------------------------------------------------
       Submit (AJAX)
    ------------------------------------------------------ */

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!validateForm()) return;

    setSubmitLoading(true);

    try {
      const formData = new FormData(form);

      const response = await fetch(form.action, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrftoken,
        },
        body: formData,
      });

      const data = await response.json();

      setSubmitLoading(false);

      if (data.success) {
        showSuccessAnimation(data.patient_number);
        // showToast(data.message || "Patient added successfully.", "success");

        setTimeout(() => {
          if (data.redirect_url) {
            window.location.href = data.redirect_url;
          } else {
            resetEntireForm();
          }
        }, 2000);
      } else {
        showServerErrors(data.errors);
        showToast(
          data.message || "Please correct the highlighted fields.",
          "danger",
        );
      }
    } catch (err) {
      console.error(err);
      setSubmitLoading(false);
      showToast("Internal server error. Please try again.", "danger");
    }
  });

  /* ------------------------------------------------------
       Warn on unsaved changes
    ------------------------------------------------------ */

  let formDirty = false;

  form.querySelectorAll("input, select, textarea").forEach((field) => {
    field.addEventListener("change", () => {
      formDirty = true;
    });
  });

  form.addEventListener("submit", () => {
    formDirty = false;
  });

  window.addEventListener("beforeunload", (e) => {
    if (!formDirty) return;
    e.preventDefault();
    e.returnValue = "";
  });

  /* ------------------------------------------------------
       Initial state
    ------------------------------------------------------ */

  updatePreview();
});

const leftColumn = document.querySelector(".ap-left-column");
const rightColumn = document.querySelector(".ap-right-column");

const patientCard = document.querySelector(
  ".ap-left-column .ap-card:first-child",
);
const medicalCard = document.querySelector(
  ".ap-left-column .ap-card:nth-child(2)",
);

const previewCard = document.querySelector(".ap-summary-card");
const emergencyCard = document.querySelector(".ap-right-column .ap-card");
const infoCard = document.querySelector(".ap-info-card");

function updateLayout() {
  if (window.innerWidth <= 992) {
    leftColumn.prepend(medicalCard);
    medicalCard.after(previewCard);
    previewCard.after(emergencyCard);
    emergencyCard.after(infoCard);
    infoCard.after(patientCard);
  } else {
    leftColumn.appendChild(patientCard);
    leftColumn.appendChild(medicalCard);

    rightColumn.appendChild(previewCard);
    rightColumn.appendChild(emergencyCard);
    rightColumn.appendChild(infoCard);
  }
}
window.addEventListener("load", updateLayout);
window.addEventListener("resize", updateLayout);
