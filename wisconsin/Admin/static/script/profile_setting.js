/* swetha's  code  */
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("ps-form");
  const saveBtn = document.getElementById("ps-save");
  const cancelBtn = document.getElementById("ps-cancel");
  const photoInput = document.getElementById("ps-photo-input");
  const avatarPreview = document.getElementById("ps-avatar-preview");
  const newPasswordInput = document.getElementById("ps-new-password");
  const confirmPasswordInput = document.getElementById("ps-confirm-password");
  const currentPasswordInput = document.getElementById("ps-current-password");
  const mismatchMsg = document.getElementById("ps-password-mismatch");
  const strengthBar = document.getElementById("ps-strength");

  /* ---- Avatar preview ---- */
  // if (photoInput) {
  //   photoInput.addEventListener("change", function () {
  //     const file = photoInput.files && photoInput.files[0];
  //     if (!file) return;
  //     const reader = new FileReader();
  //     reader.onload = function (e) {
  //       avatarPreview.innerHTML = '<img src="' + e.target.result + '" alt="" id="ps-avatar-img">';
  //     };
  //     reader.readAsDataURL(file);
  //   });
  // }
  const removeBtn = document.getElementById("remove-photo-btn");

  if (removeBtn) {
    removeBtn.addEventListener("click", function () {

      document.getElementById("remove_photo").value = "1";

      document.getElementById("ps-avatar-preview").innerHTML =
        `<span id="ps-avatar-initials">
                ${document.getElementById("ps-avatar-name").innerText
          .split(" ")
          .map(n => n[0])
          .join("")
          .substring(0, 2)
          .toUpperCase()}
            </span>`;
    });
  }

  /* ---- Password show/hide ---- */
  document.querySelectorAll(".ps-toggle-visibility").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const target = document.getElementById(btn.dataset.target);
      if (!target) return;
      const isHidden = target.type === "password";
      target.type = isHidden ? "text" : "password";
      btn.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
    });
  });

  /* ---- Password strength ---- */
  function scorePassword(pw) {
    if (!pw) return 0;
    let score = 0;
    if (pw.length >= 8) score++;
    if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score++;
    if (/\d/.test(pw)) score++;
    if (/[^A-Za-z0-9]/.test(pw) && pw.length >= 8) score++;
    return score;
  }

  function updateStrength() {
    if (!strengthBar) return;
    const pw = newPasswordInput.value;
    strengthBar.classList.remove("weak", "fair", "good", "strong");
    if (!pw) return;
    const score = scorePassword(pw);
    const label = ["weak", "weak", "fair", "good", "strong"][score];
    strengthBar.classList.add(label);
  }

  function validatePasswordMatch() {
    if (!newPasswordInput.value && !confirmPasswordInput.value) {
      mismatchMsg.hidden = true;
      return true;
    }
    const matches = newPasswordInput.value === confirmPasswordInput.value;
    mismatchMsg.hidden = matches;
    return matches;
  }

  if (newPasswordInput) {
    newPasswordInput.addEventListener("input", function () {
      updateStrength();
      validatePasswordMatch();
    });
  }
  if (confirmPasswordInput) {
    confirmPasswordInput.addEventListener("input", validatePasswordMatch);
  }

  /* ---- Toast ---- */
  function showToast(message, isError) {
    const existing = document.querySelector(".ps-toast");
    if (existing) existing.remove();
    const toast = document.createElement("div");
    toast.className = "ps-toast" + (isError ? " ps-toast--error" : "");
    toast.textContent = message;
    document.body.appendChild(toast);
    requestAnimationFrame(function () {
      toast.classList.add("ps-toast--show");
    });
    setTimeout(function () {
      toast.classList.remove("ps-toast--show");
      setTimeout(function () { toast.remove(); }, 200);
    }, 3200);
  }

  if (cancelBtn) {
    cancelBtn.addEventListener("click", function () {
      if (window.PS_CONFIG && PS_CONFIG.dashboardUrl) {
        window.location.href = PS_CONFIG.dashboardUrl;
      } else {
        window.history.back();
      }
    });
  }
  document.querySelectorAll("#ps-form input, #ps-form select").forEach(field => {

    field.addEventListener("input", function () {
      field.classList.remove("ps-error");

      const err = field.closest(".ps-field").querySelector(".ps-field-error");
      if (err) err.remove();
    });

    field.addEventListener("change", function () {
      field.classList.remove("ps-error");
      const err = field.closest(".ps-field").querySelector(".ps-field-error");
      if (err) err.remove();
    });

  });
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      clearErrors();
      function validateForm() {

        // First Name
        const nameRegex = /^[A-Za-z]+(?: [A-Za-z]+)*$/;
        const firstName = document.getElementById("ps-first-name");
        if (!firstName.value.trim()) {
          showFieldError(firstName,
            "First Name is required.");
          firstName.focus();
          return false;
        }
        if (!nameRegex.test(firstName.value.trim())) {
          showFieldError(firstName, "First Name should contain only letters.");
          return false;
        }

        if (firstName.value.trim().length < 2) {
          showFieldError(firstName,
            "First Name must contain at least 2 characters.");
          firstName.focus();
          return false;
        }

        // middle name
        const middleName = document.getElementById("ps-middle-name");

        if (middleName.value.trim() && !nameRegex.test(middleName.value.trim())) {
          showFieldError(middleName, "Middle Name should contain only letters.");
          return false;
        }
        // last name
        const lastName = document.getElementById("ps-last-name");

        if (lastName.value.trim() && !nameRegex.test(lastName.value.trim())) {
          showFieldError(lastName, "Last Name should contain only letters.");
          return false;
        }

        // Username
        const username = document.getElementById("ps-username");
        if (!username.value.trim()) {
          showFieldError(username, "Username is required.");
          username.focus();
          return false;
        }

        if (!/^[a-zA-Z0-9_.]+$/.test(username.value.trim())) {
          showFieldError(username,
            "Username contains invalid characters.");
          username.focus();
          return false;
        }


        // Email
        const email = document.getElementById("ps-email");
        // const emailRegex = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
        const emailRegex = /^[A-Za-z0-9._%+-]+@(gmail\.com|yahoo\.com|outlook\.com|hotmail\.com)$/i;

        if (!email.value.trim()) {
          showFieldError(email, "Email is required.");
          email.focus();
          return false;
        }

        if (!emailRegex.test(email.value.trim())) {
          showFieldError(email,
            "Enter a valid email address.");
          email.focus();
          return false;
        }

        // Mobile
        const mobile = document.getElementById("ps-mobile");

        if (!mobile.value.trim()) {
          showFieldError(mobile,
            "Mobile Number is required.");
          mobile.focus();
          return false;
        }

        if (!/^[0-9]{10}$/.test(mobile.value.trim())) {
          showFieldError(mobile,
            "Mobile Number must contain exactly 10 digits.");
          mobile.focus();
          return false;
        }

        // DOB
        const dob = document.getElementById("ps-dob");

        if (dob.value) {

          const today = new Date();
          const dobDate = new Date(dob.value);

          if (dobDate > today) {
            showFieldError(dob,
              "Date of Birth cannot be in the future.");
            dob.focus();
            return false;
          }
          let age = today.getFullYear() - dobDate.getFullYear();
          const monthDiff = today.getMonth() - dobDate.getMonth();

          if (
            monthDiff < 0 ||
            (monthDiff === 0 && today.getDate() < dobDate.getDate())
          ) {
            age--;
          }
          if (age < 18) {
            showFieldError(dob, "Administrator must be at least 18 years old.");
            dob.focus();
            return false;
          }
        }

        // Password Validation
        const currentPassword = document.getElementById("ps-current-password");
        const newPassword = document.getElementById("ps-new-password");
        const confirmPassword = document.getElementById("ps-confirm-password");

        if (newPassword.value || confirmPassword.value) {

          if (!currentPassword.value) {
            showFieldError(currentPassword,
              "Current Password is required.");
            currentPassword.focus();
            return false;
          }

          if (newPassword.value.length < 8) {
            showFieldError(newPassword,
              "Password must contain at least 8 characters.");
            newPassword.focus();
            return false;
          }

          if (newPassword.value !== confirmPassword.value) {
            showFieldError(confirmPassword,
              "Passwords do not match.");
            confirmPassword.focus();
            return false;
          }
        }

        return true;
      }
      if (!validateForm()) {
        return;
      }

      if (!validatePasswordMatch()) {
        confirmPasswordInput.focus();
        return;
      }

      const wantsPasswordChange = newPasswordInput.value || confirmPasswordInput.value;
      if (wantsPasswordChange && !currentPasswordInput.value) {
        showFieldError(currentPasswordInput, "Enter your current password to set a new one.");
        currentPasswordInput.focus();
        return;
      }

      const requiredFields = form.querySelectorAll("[required]");
      for (const field of requiredFields) {
        if (!field.value.trim()) {
          field.focus();
          showFieldError(field, "This field is required.");
          return;
        }
      }

      const formData = new FormData(form);
      saveBtn.disabled = true;
      saveBtn.querySelector(".ps-btn__label").textContent = "Saving…";
      saveBtn.querySelector(".ps-btn__spinner").hidden = false;
      fetch((window.PS_CONFIG && PS_CONFIG.updateUrl) || window.location.href, {
        method: "POST",
        headers: {
          "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]").value,
          "X-Requested-With": "XMLHttpRequest",
        },
        body: formData,
      })
        .then(async function (res) {
          const data = await res.json();
          if (!res.ok) {
            throw data;
          }
          return data;
        })
        .then(function (data) {
          if (data && data.success) {
            showToast("Profile updated successfully.");
            setTimeout(function () {
              window.location.href = PS_CONFIG.dashboardUrl;
            }, 1000);
            currentPasswordInput.value = "";
            newPasswordInput.value = "";
            confirmPasswordInput.value = "";
            updateStrength();
          } else {
            showToast((data && data.message) || "Could not save changes.", true);
          }
        })
        .catch(function (err) {
          if (err.message === "Current password is incorrect." ||
            err.message === "Current password is required.") {

            showFieldError(currentPasswordInput, err.message);
            return;
          }

          if (err.message === "Passwords do not match.") {
            showFieldError(confirmPasswordInput, err.message);
            return;
          }

          showToast(err.message || "Something went wrong.", true);
        })
        .finally(function () {
          saveBtn.disabled = false;
          saveBtn.querySelector(".ps-btn__label").textContent = "Save Changes";
          saveBtn.querySelector(".ps-btn__spinner").hidden = true;
        });
    });
  }
    document.querySelectorAll("#ps-dob").forEach(input => {
        flatpickr(input, {
            dateFormat: "Y-m-d",
            allowInput: false,
            static: true,
            monthSelectorType: "static",
    
        });
    });
});

function clearErrors() {
  document.querySelectorAll(".ps-field-error").forEach(e => e.remove());

  document.querySelectorAll(".ps-error").forEach(field => {
    field.classList.remove("ps-error");
  });
}

function showFieldError(field, message) {
  const oldError = field.closest(".ps-field").querySelector(".ps-field-error");
  if (oldError) oldError.remove();
  field.classList.add("ps-error");

  let error = document.createElement("small");
  error.className = "ps-field-error";
  error.textContent = message;

  field.closest(".ps-field").appendChild(error);

  field.focus();
}