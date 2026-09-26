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

  const universityId = document.getElementById("universityId");
  const fullName = document.getElementById("fullName");
  const gender = document.getElementById("gender");
  const dob = document.getElementById("dob");
  const mobile = document.getElementById("mobile");
  const email = document.getElementById("email");

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

  const originalValues = {
    patientType: patientType.value,
    visitorName: document.getElementById("visitorName")?.value || "",
    visitorMobile: document.getElementById("visitorMobile")?.value || "",
    visitorEmail: document.getElementById("visitorEmail")?.value || "",
    visitorGender: document.getElementById("visitorGender")?.value || "",
    visitorAddress: document.getElementById("visitorAddress")?.value || "",
    emergencyName: emergencyName.value,
    emergencyPhone: emergencyPhone.value,
    allergies: document.getElementById("allergies")?.value || "",
    chronicConditions: document.getElementById("chronicConditions")?.value || "",
    remarks: document.getElementById("remarks")?.value || "",
    bloodGroup: document.querySelector("input[name='blood_group']:checked")?.value || "",
  };

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


  const patientTypeSelect = new SlimSelect({
    select: patientType,
    settings: {
      showSearch: false,
      placeholderText: "Select Patient Type",
    },
  });
  

  function showToast(message, type = "success") {
    const existingToasts = document.querySelectorAll('.ap-toast');
    existingToasts.forEach(toast => toast.remove());
    
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

  async function runSearch() {
    showToast("Search is not available in edit mode.", "warning");
    return;
  }

  searchBtn.addEventListener("click", runSearch);

  searchKeyword.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      runSearch();
    }
  });

  function renderResults(results) {
  }


  let currentPhoto = null;

  function initPhoto() {
    const imgSrc = previewAvatarImg.getAttribute('src');
    const dataPhoto = previewAvatarImg.getAttribute('data-photo');
    
    if (dataPhoto && dataPhoto !== '') {
      currentPhoto = dataPhoto;
      previewAvatarImg.src = dataPhoto;
      previewAvatarImg.style.display = 'block';
      previewAvatarIcon.style.display = 'none';
      return;
    }
    
    if (imgSrc && imgSrc !== '' && !imgSrc.includes('placeholder')) {
      currentPhoto = imgSrc;
      previewAvatarImg.style.display = 'block';
      previewAvatarIcon.style.display = 'none';
      return;
    }
    
    currentPhoto = null;
    previewAvatarImg.style.display = 'none';
    previewAvatarIcon.style.display = 'block';
  }

  function selectPerson(person) {
    showToast("Cannot change linked member in edit mode.", "warning");
  }

  function clearSelection() {
    showToast("Cannot change linked member in edit mode.", "warning");
  }

  if (clearSelectionBtn) {
    clearSelectionBtn.addEventListener("click", () => {
      showToast("Cannot change linked member in edit mode.", "warning");
    });
  }


  function validatePhone(value) {
    return /^\+?[1-9]\d{8,14}$/.test(value.trim());
  }

  function validateEmail(value) {
    if (!value.trim()) return true;
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
  }

  function validateForm() {
    let valid = true;

    if (patientType.value !== "VISITOR") {
      if (!selectedProfileId.value) {
        setFieldError(
          searchKeyword,
          "No university member is linked to this patient.",
        );
        valid = false;
      }
    } else {
      const visitorNameField = document.getElementById("visitorName");
      const visitorMobileField = document.getElementById("visitorMobile");
      const visitorEmailField = document.getElementById("visitorEmail");

      if (!visitorNameField.value.trim()) {
        setFieldError(visitorNameField, "Visitor name is required.");
        valid = false;
      }

      if (!visitorMobileField.value.trim()) {
        setFieldError(visitorMobileField, "Visitor mobile is required.");
        valid = false;
      } else if (!validatePhone(visitorMobileField.value)) {
        setFieldError(visitorMobileField, "Enter a valid mobile number.");
        valid = false;
      }

      if (visitorEmailField.value.trim() && !validateEmail(visitorEmailField.value)) {
        setFieldError(visitorEmailField, "Enter a valid email address.");
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
    } else if (!validatePhone(emergencyPhone.value.replace(/\D/g, "").slice(-10))) {
      setFieldError(emergencyPhone, "Enter a valid (9-15 digit) contact number.");
      valid = false;
    }

    if (!valid) {
      showToast("Please correct the highlighted fields.", "danger");
    }

    return valid;
  }


  function updatePreview() {
    console.log("Updating preview...");
    
    try {
      if (patientType.value === "VISITOR") {
        const visitorNameField = document.getElementById("visitorName");
        const visitorMobileField = document.getElementById("visitorMobile");
        const visitorEmailField = document.getElementById("visitorEmail");
        
        const visitorName = visitorNameField ? visitorNameField.value.trim() : "";
        const visitorMobile = visitorMobileField ? visitorMobileField.value.trim() : "";
        const visitorEmail = visitorEmailField ? visitorEmailField.value.trim() : "";

        previewName.textContent = visitorName || "No Visitor Selected";
        previewType.textContent = "Visitor";

        summaryUniversity.textContent = "Visitor";
        summaryPhone.textContent = visitorMobile || "—";
        summaryEmail.textContent = visitorEmail || "—";
        
        previewAvatarImg.style.display = "none";
        previewAvatarIcon.style.display = "block";
        
      } else {
        const fullNameVal = fullName ? fullName.value.trim() : "";
        const universityIdVal = universityId ? universityId.value.trim() : "";
        const mobileVal = mobile ? mobile.value.trim() : "";
        const emailVal = email ? email.value.trim() : "";

        const labels = {
          STUDENT: "Student",
          FACULTY: "Faculty",
          STAFF: "Staff",
          ADMIN: "Admin",
          VISITOR: "Visitor",
        };

        previewName.textContent = fullNameVal || "No Patient Selected";
        previewType.textContent = labels[patientType.value] || "—";

        summaryUniversity.textContent = universityIdVal || "—";
        summaryPhone.textContent = mobileVal || "—";
        summaryEmail.textContent = emailVal || "—";
        
        if (currentPhoto && currentPhoto !== "" && currentPhoto !== "null") {
          previewAvatarImg.src = currentPhoto;
          previewAvatarImg.style.display = "block";
          previewAvatarIcon.style.display = "none";
        } else {
          previewAvatarImg.style.display = "none";
          previewAvatarIcon.style.display = "block";
        }
      }

      const checkedBlood = document.querySelector("input[name='blood_group']:checked");
      summaryBlood.textContent = checkedBlood ? checkedBlood.value : "—";
      
      console.log("Preview updated successfully");
    } catch (error) {
      console.error("Error updating preview:", error);
    }
  }

  bloodRadios.forEach((radio) => {
    radio.addEventListener("change", updatePreview);
  });
  
  const visitorNameField = document.getElementById("visitorName");
  const visitorMobileField = document.getElementById("visitorMobile");
  const visitorEmailField = document.getElementById("visitorEmail");

  [visitorNameField, visitorMobileField, visitorEmailField].forEach((field) => {
    if (field) {
      field.addEventListener("input", updatePreview);
    }
  });

  emergencyName.addEventListener("input", updatePreview);
  emergencyPhone.addEventListener("input", updatePreview);


  function setSubmitLoading(state) {
    if (!submitBtn) return;

    if (state) {
      submitBtn.disabled = true;
      submitBtn.dataset.text = submitBtn.innerHTML;
      submitBtn.innerHTML = `<span class="ap-spinner"></span> Updating...`;
    } else {
      submitBtn.disabled = false;
      submitBtn.innerHTML =
        submitBtn.dataset.text ||
        `<i class="bi bi-check-circle-fill"></i> Update Patient`;
    }
  }


  function showSuccessAnimation(patientNumber) {
    const existingOverlays = document.querySelectorAll('.ap-success-overlay');
    existingOverlays.forEach(overlay => overlay.remove());
    
    document.body.style.overflow = 'hidden';
    document.body.style.position = 'fixed';
    document.body.style.width = '100%';
    
    const success = document.createElement("div");
    success.className = "ap-success-overlay";
    success.innerHTML = `
            <div class="ap-success-box">
                <div class="success-icon"><i class="bi bi-check-circle-fill"></i></div>
                <h3>Patient Updated</h3>
                <p>${patientNumber ? `Patient Number: <strong>${patientNumber}</strong>` : "Medical profile updated successfully."}</p>
            </div>
        `;
    document.body.appendChild(success);

    setTimeout(() => success.classList.add("show"), 50);

    setTimeout(() => {
      success.classList.remove("show");
      setTimeout(() => {
        success.remove();
        // Unlock body scroll
        document.body.style.overflow = '';
        document.body.style.position = '';
        document.body.style.width = '';
      }, 400);
    }, 2200);
  }


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
      allergies: document.getElementById("allergies"),
      chronic_conditions: document.getElementById("chronicConditions"),
      remarks: document.getElementById("remarks"),
      blood_group: document.querySelector("input[name='blood_group']"),
    };

    Object.keys(errors).forEach((key) => {
      const field = fieldMap[key];
      const message = Array.isArray(errors[key]) ? errors[key][0] : errors[key];
      if (field) {
        setFieldError(field, message);
      }
    });
  }


  function resetEntireForm() {
    patientType.value = originalValues.patientType;
    
    const visitorName = document.getElementById("visitorName");
    const visitorMobile = document.getElementById("visitorMobile");
    const visitorEmail = document.getElementById("visitorEmail");
    const visitorGender = document.getElementById("visitorGender");
    const visitorAddress = document.getElementById("visitorAddress");
    
    if (visitorName) visitorName.value = originalValues.visitorName;
    if (visitorMobile) visitorMobile.value = originalValues.visitorMobile;
    if (visitorEmail) visitorEmail.value = originalValues.visitorEmail;
    if (visitorGender) visitorGender.value = originalValues.visitorGender;
    if (visitorAddress) visitorAddress.value = originalValues.visitorAddress;
    
    emergencyName.value = originalValues.emergencyName;
    emergencyPhone.value = originalValues.emergencyPhone;
    
    const allergies = document.getElementById("allergies");
    const chronicConditions = document.getElementById("chronicConditions");
    const remarks = document.getElementById("remarks");
    
    if (allergies) allergies.value = originalValues.allergies;
    if (chronicConditions) chronicConditions.value = originalValues.chronicConditions;
    if (remarks) remarks.value = originalValues.remarks;
    
    bloodRadios.forEach((radio) => {
      radio.checked = radio.value === originalValues.bloodGroup;
    });

    form.querySelectorAll(".is-invalid").forEach((f) => clearFieldError(f));

    initPhoto();
    updatePreview();
    showToast("Form reset to original values.", "info");
  }

  resetBtn.addEventListener("click", () => {
    resetEntireForm();
  });


  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!validateForm()) return;

    setSubmitLoading(true);

    try {
      const formData = new FormData(form);
      
      console.log("Submitting form data:");
      for (let [key, value] of formData.entries()) {
        console.log(key, ":", value);
      }

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

        setTimeout(() => {
          if (data.redirect_url) {
            window.location.href = data.redirect_url;
          } else {
            window.location.reload();
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


  let formDirty = false;

  form.querySelectorAll("input, select, textarea").forEach((field) => {
    field.addEventListener("change", () => {
      formDirty = true;
    });
    field.addEventListener("input", () => {
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


  initPhoto();

  setTimeout(() => {
    updatePreview();
    console.log("Initial preview update complete");
  }, 200);

  console.log("Edit patient form initialized");
  console.log("Patient type:", patientType.value);
  console.log("Linked profile ID:", selectedProfileId.value);
  console.log("Current photo:", currentPhoto);
});


document.addEventListener("DOMContentLoaded", function() {
  const leftColumn = document.querySelector(".ap-left-column");
  const rightColumn = document.querySelector(".ap-right-column");

  if (!leftColumn || !rightColumn) return;

  const patientCard = document.querySelector(".ap-left-column .ap-card:first-child");
  const medicalCard = document.querySelector(".ap-left-column .ap-card:nth-child(2)");

  const previewCard = document.querySelector(".ap-summary-card");
  const emergencyCard = document.querySelector(".ap-right-column .ap-card");
  const infoCard = document.querySelector(".ap-info-card");

  function updateLayout() {
    if (!patientCard || !medicalCard || !previewCard || !emergencyCard || !infoCard) return;
    
    if (window.innerWidth <= 992) {
      if (medicalCard.parentNode !== leftColumn) {
        leftColumn.prepend(medicalCard);
      }
      if (previewCard.parentNode !== leftColumn) {
        medicalCard.after(previewCard);
      }
      if (emergencyCard.parentNode !== leftColumn) {
        previewCard.after(emergencyCard);
      }
      if (infoCard.parentNode !== leftColumn) {
        emergencyCard.after(infoCard);
      }
      if (patientCard.parentNode !== leftColumn) {
        infoCard.after(patientCard);
      }
    } else {
      if (patientCard.parentNode !== leftColumn) {
        leftColumn.appendChild(patientCard);
      }
      if (medicalCard.parentNode !== leftColumn) {
        leftColumn.appendChild(medicalCard);
      }
      if (previewCard.parentNode !== rightColumn) {
        rightColumn.appendChild(previewCard);
      }
      if (emergencyCard.parentNode !== rightColumn) {
        rightColumn.appendChild(emergencyCard);
      }
      if (infoCard.parentNode !== rightColumn) {
        rightColumn.appendChild(infoCard);
      }
    }
  }

  setTimeout(updateLayout, 100);
  
  let resizeTimeout;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(updateLayout, 100);
  });
});