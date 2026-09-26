// swetha's code
let invalidPhoto = false;
(function () {
  "use strict";

  const form = document.getElementById("ue-form");
  if (!form) return;

  /* ============================
       Animation
    ============================ */

  const animated = document.querySelectorAll("[data-animate]");

  if ("IntersectionObserver" in window && animated.length) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("ue-in-view");
            io.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.08,
      },
    );

    animated.forEach((el) => io.observe(el));
  } else {
    animated.forEach((el) => el.classList.add("ue-in-view"));
  }

  /* ============================
       Avatar Preview
    ============================ */

  const avatarInput = document.getElementById("ue-photo-input");
  const avatarPreview = document.getElementById("ue-avatar-preview");

  if (avatarInput && avatarPreview) {
    avatarInput.addEventListener("change", function () {
      clearErrors();

      const file = this.files[0];

      if (!file) {
        invalidPhoto = false;
        return;
      }

      const allowedTypes = [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
      ];

      if (!allowedTypes.includes(file.type)) {
        invalidPhoto = true;

        showError(
          avatarInput,
          "Only JPG, JPEG, PNG and WEBP images are allowed.",
        );

        avatarInput.value = "";

        return;
      }

      invalidPhoto = false;

      const imageURL = URL.createObjectURL(file);

      let img;

      if (avatarPreview.tagName === "IMG") {
        img = avatarPreview;
      } else {
        img = avatarPreview.querySelector("img");

        if (!img) {
          avatarPreview.innerHTML = "";

          img = document.createElement("img");
          img.id = "ue-avatar-preview";
          img.className = "ue-hero__avatar";

          avatarPreview.appendChild(img);
        }
      }

      img.src = imageURL;

      img.onload = function () {
        URL.revokeObjectURL(imageURL);
      };

      markDirty();
    });
  }

  /* ============================
       Add / Remove Repeatable Rows
    ============================ */

  document.querySelectorAll("[data-add-row]").forEach((btn) => {
    btn.addEventListener("click", function () {
      const group = btn.dataset.addRow;
      const list = document.getElementById(`row-${group}`);

      if (!list) return;

      const emptyHint = list.querySelector(".ue-empty-hint");

      if (emptyHint) {
        emptyHint.remove();
      }

      const template = list.querySelector(".ue-rec");

      let newRow;

      if (template) {
        newRow = template.cloneNode(true);

        // Clear all fields
        newRow.querySelectorAll("input").forEach((input) => {
          switch (input.type) {
            case "checkbox":
            case "radio":
              input.checked = false;
              break;

            case "file":
              input.value = "";
              break;

            default:
              input.value = "";
          }
        });

        newRow.querySelectorAll("textarea").forEach((t) => {
          t.value = "";
        });

        newRow.querySelectorAll("select").forEach((s) => {
          s.selectedIndex = 0;
        });

        newRow.querySelectorAll(".ue-rec__title").forEach((title) => {
          title.textContent = "New Entry";
        });
      } else {
        newRow = document.createElement("div");

        newRow.className = "ue-rec";

        newRow.innerHTML = `
                    <div class="ue-rec__top">
                        <span class="ue-rec__title">New Entry</span>

                        <button
                            type="button"
                            class="ue-rec__remove"
                            data-remove-row>

                            <svg viewBox="0 0 24 24"
                                 fill="none"
                                 stroke="currentColor">

                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>

                            </svg>

                            Remove

                        </button>

                    </div>

                    <div class="ue-rec__fields"></div>
                `;
      }

      // Update dynamic names
      const index = list.querySelectorAll(".ue-rec").length;

      newRow.querySelectorAll("[name]").forEach((field) => {
        field.name = field.name

          .replace(/student-\d+-/g, `student-${index}-`)
          .replace(/faculty-\d+-/g, `faculty-${index}-`)
          .replace(/staff-\d+-/g, `staff-${index}-`)
          .replace(/admin-\d+-/g, `admin-${index}-`)
          .replace(/address-\d+-/g, `address-${index}-`)
          .replace(/contact-\d+-/g, `contact-${index}-`);
      });

      list.appendChild(newRow);

      const firstInput = newRow.querySelector("input, select, textarea");

      if (firstInput) {
        firstInput.focus();
      }

      markDirty();
    });
  });

  /* ============================
       Remove Row
    ============================ */

  form.addEventListener("click", function (e) {
    const removeBtn = e.target.closest("[data-remove-row]");

    if (!removeBtn) return;

    const row = removeBtn.closest(".ue-rec");

    if (!row) return;

    const list = row.parentElement;

    row.remove();

    if (list && !list.querySelector(".ue-rec")) {
      const hint = document.createElement("p");

      hint.className = "ue-empty-hint";

      hint.textContent = "No entries yet.";

      list.appendChild(hint);
    }

    markDirty();
  });

  /* ============================
       Dirty State Tracking
    ============================ */

  const statusEl = document.getElementById("ue-status");

  let isDirty = false;
  let isSubmitting = false;

  const initialData = new FormData(form);

  function hasChanges() {
    const currentData = new FormData(form);

    if (currentData.entries().length !== initialData.entries().length) {
      return true;
    }

    for (const [key, value] of currentData.entries()) {
      if (initialData.get(key) != value) {
        return true;
      }
    }

    return false;
  }

  function markDirty() {
    isDirty = hasChanges();

    if (!statusEl) return;

    if (isDirty) {
      statusEl.textContent = "Unsaved changes";
      statusEl.classList.add("is-dirty");
    } else {
      statusEl.textContent = "No unsaved changes";
      statusEl.classList.remove("is-dirty");
    }
  }

  form.addEventListener("input", markDirty);
  form.addEventListener("change", markDirty);

  window.addEventListener("beforeunload", function (e) {
    if (isSubmitting || !isDirty) return;

    e.preventDefault();
    e.returnValue = "";
  });

  window.addEventListener("pageshow", function () {
    isDirty = false;
    isSubmitting = false;

    if (statusEl) {
      statusEl.textContent = "No unsaved changes";
      statusEl.classList.remove("is-dirty");
    }
  });

  const cancelBtn = document.getElementById("ue-cancel-btn");

  if (cancelBtn) {
    cancelBtn.addEventListener("click", function () {
      isDirty = false;
      isSubmitting = true;
    });
  }

  /* ============================
       Form Submit
    ============================ */

  form.addEventListener("submit", function (e) {
    clearErrors();

    let valid = true;

    isSubmitting = true;
    isDirty = false;

    /* ---------- Common Validation ---------- */

    valid = validateCommonFields() && valid;

    /* ---------- Student ---------- */

    if (document.getElementById("ue-sec-student")) {
      valid = validateStudentFields() && valid;
      valid = validateStudentAddresses() && valid;
      valid = validateEmergencyContacts() && valid;
    }

    /* ---------- Faculty ---------- */

    if (document.getElementById("ue-sec-faculty")) {
      valid = validateFacultyFields() && valid;
      valid = validateFacultyEducation() && valid;
    }

    /* ---------- Staff ---------- */

    if (document.getElementById("ue-sec-staff")) {
      valid = validateStaffFields() && valid;
      valid = validateStaffPosition() && valid;
      valid = validateStaffAddresses() && valid;
      valid = validateStaffEmergencyContacts() && valid;
      valid = validateStaffEducation() && valid;
      valid = validateStaffCertifications() && valid;
    }

    /* ---------- Admin ---------- */

    if (document.getElementById("ue-sec-admin")) {
      valid = validateAdminFields() && valid;
    }

    /* ---------- Validation Failed ---------- */

    if (!valid) {
      e.preventDefault();

      isSubmitting = false;
      isDirty = true;

      const firstError = document.querySelector(".error");

      if (firstError) {
        firstError.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });

        setTimeout(() => {
          firstError.focus({
            preventScroll: true,
          });
        }, 250);
      }

      return;
    }

    /* ---------- Saving UI ---------- */

    if (statusEl) {
      statusEl.textContent = "Saving...";
      statusEl.classList.remove("is-dirty");
    }

    const saveBtn = document.getElementById("ue-save-btn");

    if (saveBtn) {
      saveBtn.disabled = true;

      saveBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm"></span>
                Saving...
            `;
    }
  });

  function validateStaffPosition() {
    let valid = true;

    const jobTitle = document.querySelector("[name='staff-job_title']");
    const unitId = document.querySelector("[name='staff-unit_id']");
    const startDate = document.querySelector(
      "[name='staff-position_start_date']",
    );

    const titleRegex = /^[A-Za-z0-9 .,&()'/-]+$/;

    if (jobTitle) {
      const value = jobTitle.value.trim();

      if (!value) {
        showError(jobTitle, "Job title is required");
        valid = false;
      } else if (!titleRegex.test(value)) {
        showError(jobTitle, "Invalid job title");
        valid = false;
      }
    }

    if (unitId && unitId.value) {
      const id = Number(unitId.value);

      if (!Number.isInteger(id) || id <= 0) {
        showError(unitId, "Enter a valid Unit ID");
        valid = false;
      }
    }

    // if (startDate) {

    //     if (!startDate.value) {

    //         showError(startDate, "Position start date is required");
    //         valid = false;

    //     } else {

    //         const today = new Date();
    //         const start = new Date(startDate.value);

    //         today.setHours(0, 0, 0, 0);

    //         if (start > today) {

    //             showError(startDate, "Start date cannot be in the future");
    //             valid = false;

    //         }

    //     }

    // }

    if (startDate && !startDate.value) {
      showError(startDate, "Position start date is required");
      valid = false;
    }
    return valid;
  }

  /* ============================
       Staff Emergency Contacts
    ============================ */

  function validateStaffEmergencyContacts() {
    let valid = true;

    const rows = document.querySelectorAll("#row-staff-emergency .ue-rec");

    const nameRegex = /^[A-Za-z .'-]+$/;
    // const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    rows.forEach((row) => {
      const name = row.querySelector("[name='staff-emergency_name[]']");
      const relationship = row.querySelector(
        "[name='staff-emergency_relationship[]']",
      );
      const phone = row.querySelector("[name='staff-emergency_phone[]']");
      const email = row.querySelector("[name='staff-emergency_email[]']");
      const priority = row.querySelector("[name='staff-emergency_priority[]']");

      if (name) {
        const value = name.value.trim();

        if (!value) {
          showError(name, "Contact name is required");
          valid = false;
        } else if (!nameRegex.test(value)) {
          showError(name, "Invalid contact name");
          valid = false;
        }
      }

      if (relationship) {
        const value = relationship.value.trim();

        if (!value) {
          showError(relationship, "Relationship is required");
          valid = false;
        } else if (!nameRegex.test(value)) {
          showError(relationship, "Invalid relationship");
          valid = false;
        }
      }

      if (phone) {
        const value = phone.value.trim();

        if (!value) {
          showError(phone, "Phone number is required");
          valid = false;
        } else if (!isValidPhone(value)) {
          showError(phone, "Enter a valid (9-15 digit) phone number");
          valid = false;
        }
      }

      if (email) {
        const value = email.value.trim();

        if (value && !isValidEmail(value)) {
          showError(email, "Invalid email");
          valid = false;
        }
      }

      if (priority) {
        const p = Number(priority.value);

        if (!priority.value) {
          showError(priority, "Priority is required");
          valid = false;
        } else if (!Number.isInteger(p) || p < 1) {
          showError(priority, "Priority must be greater than zero");
          valid = false;
        }
      }
    });

    return valid;
  }

  /* ============================
       Faculty Education
    ============================ */

  function validateFacultyEducation() {
    let valid = true;

    const degreeRegex = /^[A-Za-z0-9 .,&()-]+$/;
    const fieldRegex = /^[A-Za-z .,&()-]+$/;
    const institutionRegex = /^[A-Za-z0-9 .,&()'/-]+$/;

    document
      .querySelectorAll("#row-faculty-education .ue-rec")
      .forEach((row) => {
        const degree = row.querySelector("[name='education_degree']");
        const field = row.querySelector("[name='education_field']");
        const institution = row.querySelector("[name='education_institution']");
        const year = row.querySelector("[name='education_year']");

        if (degree) {
          const value = degree.value.trim();

          if (!value) {
            showError(degree, "Degree is required");
            valid = false;
          } else if (!degreeRegex.test(value)) {
            showError(degree, "Invalid degree");
            valid = false;
          }
        }

        if (field) {
          const value = field.value.trim();

          if (value && !fieldRegex.test(value)) {
            showError(field, "Invalid field of study");
            valid = false;
          }
        }

        if (institution) {
          const value = institution.value.trim();

          if (!value) {
            showError(institution, "Institution is required");
            valid = false;
          } else if (!institutionRegex.test(value)) {
            showError(institution, "Invalid institution");
            valid = false;
          }
        }

        if (year && year.value) {
          const currentYear = new Date().getFullYear();
          const y = Number(year.value);

          if (!Number.isInteger(y) || y < 1950 || y > currentYear + 5) {
            showError(year, `Enter year between 1950 and ${currentYear + 5}`);

            valid = false;
          }
        }
      });

    return valid;
  }

  function normalizePhone(value) {
    return value.replace(/\D/g, "");
  }

  function isValidPhone(value) {
    if (!value) return false;
    const trimmed = value.trim();
    if (!/^\+?[\d\s\-()]+$/.test(trimmed)) {
      return false;
    }
    const digits = normalizePhone(trimmed);
    if (digits.length < 9 || digits.length > 15) {
      return false;
    }
    if (/^[6-9]\d{9}$/.test(digits) || /^91[6-9]\d{9}$/.test(digits)) {
      return true;
    }
    return /^[1-9]\d{8,14}$/.test(digits);
  }
  function isValidEmail(value) {
      return /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/i.test(
          value.trim()
      );
  }

  /* ===============================
       COMMON USER VALIDATION
    ================================*/
  
  // Jack Code Start's
  const ssn_number = document.getElementById("id_ssn_number");
  // Jack Code End's

  function validateCommonFields() {
    let valid = true;
    const firstName = document.getElementById("id_first_name");
    const middleName = document.getElementById("id_middle_name");
    const lastName = document.getElementById("id_last_name");
    const email = document.getElementById("id_email");
    const mobile = document.getElementById("id_mobile_number");
    const dob = document.querySelector("[name='date_of_birth']");
    const photo = document.getElementById("ue-photo-input");
    const nameRegex = /^[A-Za-z ]+$/;
    // const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    /* ---------- Profile Photo ---------- */

    if (typeof invalidPhoto !== "undefined" && invalidPhoto) {
      showError(photo, "Only JPG, JPEG, PNG and WEBP images are allowed.");

      valid = false;
    }

    if (photo && photo.files.length) {
      const file = photo.files[0];

      const allowedTypes = [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
      ];

      if (!allowedTypes.includes(file.type)) {
        showError(photo, "Only JPG, JPEG, PNG and WEBP images are allowed.");

        photo.value = "";
        valid = false;
      }
    }

    /* ---------- First Name ---------- */

    if (firstName) {
      const value = firstName.value.trim();

      if (!value) {
        showError(firstName, "First name is required");
        valid = false;
      } else if (!nameRegex.test(value)) {
        showError(firstName, "Only letters allowed");
        valid = false;
      }
    }

    /* ---------- Middle Name ---------- */

    if (middleName) {
      const value = middleName.value.trim();

      if (value && !nameRegex.test(value)) {
        showError(middleName, "Only letters allowed");
        valid = false;
      }
    }

    /* ---------- Last Name ---------- */

    if (lastName) {
      const value = lastName.value.trim();

      if (!value) {
        showError(lastName, "Last name is required");
        valid = false;
      } else if (!nameRegex.test(value)) {
        showError(lastName, "Only letters allowed");
        valid = false;
      }
    }

    // Jack Code Start's

    /* ---------- SSN Number ---------- */

    if (ssn_number) {
      const value = ssn_number.value.trim();

      if (!value) {
        showError(ssn_number, "SSN number is required");
        valid = false;

      } else if (!/^\d{3}-\d{2}-\d{4}$/.test(value)) {
        showError(
          ssn_number,
          "Enter a valid SSN in the format XXX-XX-XXXX"
        );
        valid = false;

      } else {
        const [area, group, serial] = value.split("-");

        if (area === "000" || group === "00" || serial === "0000") {
          showError(ssn_number, "Enter a valid SSN number");
          valid = false;
        } else {
          clearError(ssn_number);
        }
      }
    }

    // Jack Code End's

    /* ---------- Email ---------- */

    if (email) {
      const value = email.value.trim();

      if (!value) {
        showError(email, "Email is required");
        valid = false;
      } else if (!isValidEmail(value)) {
        showError(email, "Invalid email");
        valid = false;
      }
    }

    /* ---------- Mobile ---------- */

    if (mobile) {
      const value = mobile.value.trim();

      if (!value) {
        showError(mobile, "Mobile number is required");
        valid = false;
      } else if (!isValidPhone(value)) {
        showError(mobile, "Enter a valid (9-15 digit) mobile number");
        valid = false;
      }
    }

    /* ---------- Date Of Birth ---------- */

    if (dob && dob.value) {
      const today = new Date();
      const birthDate = new Date(dob.value);

      today.setHours(0, 0, 0, 0);

      if (birthDate > today) {
        showError(dob, "Date of birth cannot be in the future");

        valid = false;
      } else {
        let age = today.getFullYear() - birthDate.getFullYear();

        const monthDiff = today.getMonth() - birthDate.getMonth();

        if (
          monthDiff < 0 ||
          (monthDiff === 0 && today.getDate() < birthDate.getDate())
        ) {
          age--;
        }

        if (age < 16) {
          showError(dob, "User must be at least 16 years old");

          valid = false;
        } else if (age > 100) {
          showError(dob, "Enter a valid date of birth");

          valid = false;
        }
      }
    }

    return valid;
  }


  // Jack Code Start's

  if (ssn_number) {
  ssn_number.addEventListener("input", function () {
    let value = this.value
      .replace(/\D/g, "")
      .substring(0, 9);

    if (value.length > 5) {
      value =
        value.substring(0, 3) +
        "-" +
        value.substring(3, 5) +
        "-" +
        value.substring(5);
    } else if (value.length > 3) {
      value =
        value.substring(0, 3) +
        "-" +
        value.substring(3);
    }

    this.value = value;

  });
  }

  // Jack Code Start's

  /* ===============================
       STUDENT
    ================================*/

  function validateStudentFields() {
    let valid = true;

    const universityEmail = document.querySelector(
      "[name='student-university_email']",
    );
    const personalEmail = document.querySelector(
      "[name='student-personal_email']",
    );
    const gpa = document.querySelector("[name='student-cumulative_gpa']");
    const admission = document.querySelector("[name='student-admission_date']");
    const graduation = document.querySelector(
      "[name='student-expected_graduation_date']",
    );

    // const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    /* ---------- University Email ---------- */

    if (universityEmail) {
      const value = universityEmail.value.trim();

      if (!value) {
        showError(universityEmail, "University email is required");
        valid = false;
      } else if (!isValidEmail(value)) {
        showError(universityEmail, "Invalid university email");
        valid = false;
      }
    }

    /* ---------- Personal Email ---------- */

    if (personalEmail && personalEmail.value.trim()) {
      const value = personalEmail.value.trim();

      if (!isValidEmail(value)) {
        showError(personalEmail, "Invalid personal email");
        valid = false;
      } else if (
        universityEmail &&
        value.toLowerCase() === universityEmail.value.trim().toLowerCase()
      ) {
        showError(
          personalEmail,
          "Personal email cannot be same as university email",
        );

        valid = false;
      }
    }

    /* ---------- GPA ---------- */

    if (gpa && gpa.value.trim()) {
      const score = Number(gpa.value);

      if (isNaN(score) || score < 0 || score > 4) {
        showError(gpa, "GPA must be between 0 and 4");
        valid = false;
      }
    }

    /* ---------- Admission Date ---------- */

    if (admission && admission.value) {
      const admissionDate = new Date(admission.value);
      const today = new Date();

      today.setHours(0, 0, 0, 0);

      if (admissionDate > today) {
        showError(admission, "Admission date cannot be in the future");

        valid = false;
      }
    }

    /* ---------- Graduation Date ---------- */

    if (graduation && graduation.value && admission && admission.value) {
      const graduationDate = new Date(graduation.value);
      const admissionDate = new Date(admission.value);

      if (graduationDate <= admissionDate) {
        showError(graduation, "Graduation date must be after admission date");

        valid = false;
      }
    }

    return valid;
  }

  /* ===============================
       STUDENT ADDRESSES
    ================================*/

  function validateStudentAddresses() {
    let valid = true;

    const nameRegex = /^[A-Za-z .'-]+$/;
    const postalRegex = /^[A-Za-z0-9 -]{3,10}$/;

    document
      .querySelectorAll("#row-student-addresses .ue-rec")
      .forEach((row) => {
        const line1 = row.querySelector("[name='student-address_line_1[]']");
        const city = row.querySelector("[name='student-city[]']");
        const state = row.querySelector("[name='student-state[]']");
        const postal = row.querySelector("[name='student-postal_code[]']");
        const country = row.querySelector("[name='student-country[]']");

        if (line1 && !line1.value.trim()) {
          showError(line1, "Address Line 1 is required");
          valid = false;
        }

        if (city) {
          const value = city.value.trim();

          if (!value) {
            showError(city, "City is required");
            valid = false;
          } else if (!nameRegex.test(value)) {
            showError(city, "Invalid city");
            valid = false;
          }
        }

        if (state) {
          const value = state.value.trim();

          if (!value) {
            showError(state, "State is required");
            valid = false;
          } else if (!nameRegex.test(value)) {
            showError(state, "Invalid state");
            valid = false;
          }
        }

        if (postal) {
          const value = postal.value.trim();

          if (!value) {
            showError(postal, "Postal code is required");
            valid = false;
          } else if (!postalRegex.test(value)) {
            showError(postal, "Invalid postal code");
            valid = false;
          }
        }

        if (country) {
          const value = country.value.trim();

          if (!value) {
            showError(country, "Country is required");
            valid = false;
          } else if (!nameRegex.test(value)) {
            showError(country, "Invalid country");
            valid = false;
          }
        }
      });

    return valid;
  }

  /* ===============================
       STUDENT EMERGENCY CONTACTS
    ================================*/

  function validateEmergencyContacts() {
    let valid = true;

    const nameRegex = /^[A-Za-z .'-]+$/;

    document
      .querySelectorAll("#row-student-emergency .ue-rec")
      .forEach((row) => {
        const name = row.querySelector("[name='student-emergency_name[]']");
        const relationship = row.querySelector(
          "[name='student-emergency_relationship[]']",
        );
        const phone = row.querySelector("[name='student-emergency_phone[]']");

        if (name) {
          const value = name.value.trim();

          if (!value) {
            showError(name, "Contact name is required");
            valid = false;
          } else if (!nameRegex.test(value)) {
            showError(name, "Invalid contact name");
            valid = false;
          }
        }

        if (relationship) {
          const value = relationship.value.trim();

          if (!value) {
            showError(relationship, "Relationship is required");

            valid = false;
          } else if (!nameRegex.test(value)) {
            showError(relationship, "Invalid relationship");

            valid = false;
          }
        }

        if (phone) {
          const value = phone.value.trim();

          if (!value) {
            showError(phone, "Phone number is required");

            valid = false;
          } else if (!isValidPhone(value)) {
            showError(phone, "Enter a valid (9-15 digit) phone number");

            valid = false;
          }
        }
      });

    return valid;
  }

  function validateStaffEducation() {
    let valid = true;

    document.querySelectorAll("#row-staff-education .ue-rec").forEach((row) => {
      const degree = row.querySelector("[name='staff-degree[]']");
      const field = row.querySelector("[name='staff-field_of_study[]']");
      const institution = row.querySelector(
        "[name='staff-institution_name[]']",
      );
      const year = row.querySelector("[name='staff-graduation_year[]']");

      const degreeRegex = /^[A-Za-z0-9 .,&()\-]+$/;
      const fieldRegex = /^[A-Za-z .,&()\-]+$/;
      const institutionRegex = /^[A-Za-z0-9 .,&()'/-]+$/;

      // Degree
      if (degree && !degree.value.trim()) {
        showError(degree, "Degree is required");
        valid = false;
      } else if (degree && !degreeRegex.test(degree.value.trim())) {
        showError(degree, "Invalid degree");
        valid = false;
      }

      // Field of Study
      if (field) {
        const value = field.value.trim();

        if (value && !fieldRegex.test(value)) {
          showError(field, "Only letters allowed");
          valid = false;
        }
      }

      // Institution
      if (institution && !institution.value.trim()) {
        showError(institution, "Institution is required");
        valid = false;
      } else if (
        institution &&
        !institutionRegex.test(institution.value.trim())
      ) {
        showError(institution, "Invalid institution");
        valid = false;
      }

      // Graduation Year
      if (year) {
        const value = year.value.trim();

        if (value) {
          const currentYear = new Date().getFullYear();
          const y = parseInt(value, 10);

          if (isNaN(y) || y < 1950 || y > currentYear + 5) {
            showError(year, `Enter year between 1950 and ${currentYear + 5}`);
            valid = false;
          }
        }
      }
    });

    return valid;
  }

  function validateStaffCertifications() {
    let valid = true;

    document
      .querySelectorAll("#row-staff-certifications .ue-rec")
      .forEach((row) => {
        const certification = row.querySelector(
          "[name='staff-certification_name[]']",
        );
        const organization = row.querySelector(
          "[name='staff-issuing_organization[]']",
        );
        const issueDate = row.querySelector("[name='staff-issue_date[]']");
        const expiryDate = row.querySelector(
          "[name='staff-expiration_date[]']",
        );

        const nameRegex = /^[A-Za-z0-9 .,&()'/-]+$/;

        // Certification Name
        if (certification && !certification.value.trim()) {
          showError(certification, "Certification name is required");
          valid = false;
        } else if (
          certification &&
          !nameRegex.test(certification.value.trim())
        ) {
          showError(certification, "Invalid certification name");
          valid = false;
        }

        // Issuing Organization
        if (organization && !organization.value.trim()) {
          showError(organization, "Organization is required");
          valid = false;
        } else if (organization && !nameRegex.test(organization.value.trim())) {
          showError(organization, "Invalid organization name");
          valid = false;
        }

        // Issue Date
        if (issueDate && !issueDate.value) {
          showError(issueDate, "Issue date is required");
          valid = false;
        } else if (issueDate && new Date(issueDate.value) > new Date()) {
          showError(issueDate, "Issue date cannot be in the future");
          valid = false;
        }

        // Expiration Date
        if (expiryDate && expiryDate.value) {
          if (
            issueDate &&
            issueDate.value &&
            new Date(expiryDate.value) <= new Date(issueDate.value)
          ) {
            showError(expiryDate, "Expiration date must be after issue date");
            valid = false;
          }
        }
      });

    return valid;
  }

  // Faculty
  function validateFacultyFields() {
    let valid = true;

    const preferred = document.querySelector("[name='faculty-preferred_name']");
    const email = document.querySelector("[name='faculty-email']");
    const phone = document.querySelector("[name='faculty-phone']");
    const hireDate = document.querySelector("[name='faculty-hire_date']");
    const department = document.querySelector("[name='faculty-department_id']");
    const school = document.querySelector("[name='faculty-school_id']");
    const rank = document.querySelector("[name='faculty-faculty_rank']");
    const employment = document.querySelector(
      "[name='faculty-employment_type']",
    );

    const nameRegex = /^[A-Za-z ]+$/;

    if (email && !isValidEmail(email.value.trim())) {
      showError(email, "Invalid email");
      valid = false;
    }

    if (school && !school.value) {
      showError(school, "Select school");
      valid = false;
    }

    if (rank && !rank.value) {
      showError(rank, "Select faculty rank");
      valid = false;
    }

    if (employment && !employment.value) {
      showError(employment, "Select employment type");
      valid = false;
    }

    if (hireDate && hireDate.value) {
      if (new Date(hireDate.value) > new Date()) {
        showError(hireDate, "Hire date cannot be future");
        valid = false;
      }
    }

    return valid;
  }

  function validateStaffFields() {
    let valid = true;

    const preferred = document.querySelector("[name='staff-preferred_name']");
    const email = document.querySelector("[name='staff-email']");
    const phone = document.querySelector("[name='staff-phone']");

    const department = document.querySelector("[name='staff-department_id']");
    const school = document.querySelector("[name='staff-school_id']");
    const designation = document.querySelector("[name='staff-designation']");
    const employment = document.querySelector("[name='staff-employment_type']");
    const office = document.querySelector("[name='staff-office_location']");
    const personalEmail = document.querySelector(
      "[name='staff-personal_email']",
    );
    const officePhone = document.querySelector("[name='staff-office_phone']");
    const hireDate = document.querySelector("[name='staff-hire_date']");

    const nameRegex = /^[A-Za-z ]+$/;

    if (
      preferred &&
      preferred.value &&
      !nameRegex.test(preferred.value.trim())
    ) {
      showError(preferred, "Only letters allowed");
      valid = false;
    }

    if (email && !isValidEmail(email.value.trim())) {
      showError(email, "Invalid email");
      valid = false;
    }

    if (phone && !isValidPhone(phone.value.trim())) {
      showError(phone, "Enter valid (9-15) mobile number");
      valid = false;
    }
    if (personalEmail) {
      const value = personalEmail.value.trim();
      if (value) {
        if (!isValidEmail(value)) {
          showError(personalEmail, "Invalid personal email");
          valid = false;
        } else if (
          email &&
          value.toLowerCase() === email.value.trim().toLowerCase()
        ) {
          showError(
            personalEmail,
            "Personal email cannot be same as official email",
          );
          valid = false;
        }
      }
    }
    if (officePhone) {
      const value = officePhone.value.trim();
      if (value && !isValidPhone(value)) {
        showError(
          officePhone,
          "Office phone number must be between 9 and 15 digits.",
        );
        valid = false;
      }
    }

    if (hireDate && hireDate.value) {
      if (new Date(hireDate.value) > new Date()) {
        showError(hireDate, "Hire date cannot be future");
        valid = false;
      }
    }

    return valid;
  }
  function validateStaffAddresses() {
    let valid = true;

    document.querySelectorAll("#row-staff-addresses .ue-rec").forEach((row) => {
      const type = row.querySelector("[name='staff-address_type[]']");
      const line1 = row.querySelector("[name='staff-address_line_1[]']");
      const city = row.querySelector("[name='staff-city[]']");
      const state = row.querySelector("[name='staff-state[]']");
      const postal = row.querySelector("[name='staff-postal_code[]']");
      const country = row.querySelector("[name='staff-country[]']");

      const nameRegex = /^[A-Za-z .'-]+$/;
      const postalRegex = /^[A-Za-z0-9 -]{3,10}$/;

      if (type && !type.value) {
        showError(type, "Select address type");
        valid = false;
      }

      if (line1 && !line1.value.trim()) {
        showError(line1, "Address Line 1 is required");
        valid = false;
      }

      if (city && !city.value.trim()) {
        showError(city, "City is required");
        valid = false;
      } else if (city && !nameRegex.test(city.value.trim())) {
        showError(city, "Invalid city");
        valid = false;
      }

      if (state && !state.value.trim()) {
        showError(state, "State is required");
        valid = false;
      } else if (state && !nameRegex.test(state.value.trim())) {
        showError(state, "Invalid state");
        valid = false;
      }

      if (postal && !postal.value.trim()) {
        showError(postal, "Postal code is required");
        valid = false;
      } else if (!postalRegex.test(postal.value.trim())) {
        showError(postal, "Invalid postal code");
        valid = false;
      }

      if (country && !country.value.trim()) {
        showError(country, "Country is required");
        valid = false;
      } else if (!nameRegex.test(country.value.trim())) {
        showError(country, "Invalid country");
        valid = false;
      }
    });

    return valid;
  }

  function validateAdminFields() {
    let valid = true;

    const preferred = document.querySelector("[name='admin-preferred_name']");
    const email = document.querySelector("[name='admin-email']");
    const phone = document.querySelector("[name='admin-phone']");
    const department = document.querySelector("[name='admin-department_id']");
    const role = document.querySelector("[name='admin-role']");
    const office = document.querySelector("[name='admin-office_location']");

    const nameRegex = /^[A-Za-z ]+$/;

    if (
      preferred &&
      preferred.value &&
      !nameRegex.test(preferred.value.trim())
    ) {
      showError(preferred, "Only letters allowed");
      valid = false;
    }

    if (email && !isValidEmail(email.value.trim())) {
      showError(email, "Invalid email");
      valid = false;
    }

    if (phone && !isValidPhone(phone.value.trim())) {
      showError(phone, "Enter valid (9-15 digits) mobile number");
      valid = false;
    }

    return valid;
  }

  //    ERROR FUNCTIONS

  function showError(field, message) {
    field.classList.add("error");
    let parent = field.parentNode;
    if (field.type === "file") {
      parent = document.querySelector(".ue-avatar-meta");
    }
    let error = parent.querySelector(".ue-error");
    if (!error) {
      error = document.createElement("small");
      error.className = "ue-error";
      parent.appendChild(error);
    }
    error.textContent = message;
  }

  function clearErrors() {
    document.querySelectorAll(".ue-error").forEach((e) => e.remove());
    document
      .querySelectorAll(".error")
      .forEach((e) => e.classList.remove("error"));
  }

  // dropdown cdn
  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".ue-select").forEach((select) => {
      if (select.choices) {
        select.choices.destroy();
      }

      select.choices = new Choices(select, {
        searchEnabled: false,
        itemSelectText: "",
        shouldSort: false,
      });
    });
    document.querySelectorAll(".ue-date").forEach((input) => {

      const options = {
        dateFormat: "Y-m-d",
        allowInput: false,
        static: true,
        monthSelectorType: "static",
      };

      if (
        input.name === "date_of_birth" ||
        input.name === "staff-position_start_date"
      ) 
      flatpickr(input, options);
    });
  });
})();
