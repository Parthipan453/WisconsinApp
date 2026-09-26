document.addEventListener("DOMContentLoaded", function () {
  $("#opening_time").timepicker({
    timeFormat: "HH:mm",
    interval: 30,
    defaultTime: null,
  });

  $("#closing_time").timepicker({
    timeFormat: "HH:mm",
    interval: 30,
    defaultTime: null,
  });

  const codeInput = document.getElementById(
    "{{ form.department_code.id_for_label }}",
  );
  if (codeInput) {
    codeInput.addEventListener("input", function () {
      this.value = this.value.toUpperCase().replace(/\s/g, "");
    });
  }

  const emergencyCheckbox = document.getElementById("is_emergency");
  const openingTime = document.getElementById("opening_time");
  const closingTime = document.getElementById("closing_time");

  if (emergencyCheckbox && openingTime && closingTime) {

      const initialOpeningTime = openingTime.value;
      const initialClosingTime = closingTime.value;

      emergencyCheckbox.addEventListener("change", toggleTimeFields);

      toggleTimeFields();

      function toggleTimeFields() {
          if (emergencyCheckbox.checked) {
              openingTime.value = "00:00";
              closingTime.value = "23:59";

              openingTime.disabled = true;
              closingTime.disabled = true;
          } else {
              openingTime.disabled = false;
              closingTime.disabled = false;

              openingTime.value = initialOpeningTime;
              closingTime.value = initialClosingTime;
          }
      }
  }

  const form = document.getElementById("departmentForm");

  function showError(field, message) {
    const formGroup = field.closest(".department-form-group");
    if (!formGroup) return;

    const existingError = formGroup.querySelector(".form-text.error");
    if (existingError) {
      existingError.remove();
    }

    field.classList.add("is-invalid");

    const errorDiv = document.createElement("div");
    errorDiv.className = "form-text error";
    errorDiv.innerHTML = `<i class="ti ti-alert-circle"></i> ${message}`;

    if (field.type === "checkbox") {
      const wrapper = field.closest(".checkbox-wrapper");
      if (wrapper) {
        wrapper.classList.add("is-invalid");
        wrapper.parentNode.insertBefore(errorDiv, wrapper.nextSibling);
        return;
      }
    }

    field.parentNode.insertBefore(errorDiv, field.nextSibling);
  }

  function clearError(field) {
    const formGroup = field.closest(".department-form-group");
    if (!formGroup) return;

    field.classList.remove("is-invalid");

    if (field.type === "checkbox") {
      const wrapper = field.closest(".checkbox-wrapper");
      if (wrapper) {
        wrapper.classList.remove("is-invalid");
      }
    }

    const errorDiv = formGroup.querySelector(".form-text.error");
    if (errorDiv) {
      errorDiv.remove();
    }
  }

  form.querySelectorAll(".form-control, .form-select").forEach((field) => {
    field.addEventListener("input", function () {
      clearError(this);
    });
    field.addEventListener("change", function () {
      clearError(this);
    });
  });

  const departmentCode = document.getElementById("id_department_code");
  const departmentName = document.getElementById("id_department_name");
  const shortName = document.getElementById("id_short_name");
  const departmentType = document.getElementById("id_department_type");
  const phoneInput = document.getElementById("id_phone");

  if (departmentCode) {
    departmentCode.addEventListener("input", function () {
      clearError(this);

      this.value = this.value.toUpperCase().replace(/\s/g, "");

      if (this.value.length === 0) return;

      if (!/^[A-Z0-9]+$/.test(this.value)) {
        showError(
          this,
          "Department code can contain only letters and numbers.",
        );
        return;
      }

      if (this.value.length < 4) {
        showError(this, "Department code must contain at least 4 characters.");
      }
    });
  }

  if (departmentName) {
    departmentName.addEventListener("input", function () {
      clearError(this);

      this.value = this.value.replace(/[^A-Za-z ]/g, "");

      if (this.value.trim().length === 0) return;

      if (this.value.trim().length < 3) {
        showError(this, "Department name must contain at least 3 letters.");
      }
    });
  }

  if (shortName) {
    shortName.addEventListener("input", function () {
      clearError(this);

      this.value = this.value.replace(/[^A-Za-z ]/g, "");

      if (this.value.trim().length === 0) return;

      if (this.value.trim().length < 2) {
        showError(this, "Short name must contain at least 2 letters.");
      }
    });
  }

  if (departmentType) {
    departmentType.addEventListener("input", function () {
      clearError(this);

      this.value = this.value.replace(/[^A-Za-z ]/g, "");

      if (this.value.trim().length === 0) return;

      if (this.value.trim().length < 4) {
        showError(this, "Department type must contain at least 4 letters.");
      }
    });
  }

  if (phoneInput) {
    phoneInput.addEventListener("input", function () {
        this.value = this.value.replace(/[^0-9+ ]/g, "");

        this.value = this.value.replace(/(?!^)\+/g, "");

        const digits = this.value.replace(/\D/g, "");

        if (digits.length > 15) {
            this.value = this.value.slice(0, -1);
        }
    });
  }

  form.addEventListener("submit", function (e) {
    let hasError = false;
    let firstErrorField = null;

    if (emergencyCheckbox.checked) {
        openingTime.disabled = false;
        closingTime.disabled = false;

        openingTime.value = "00:00";
        closingTime.value = "23:59";
    }


    form.querySelectorAll(".is-invalid").forEach((el) => {
      el.classList.remove("is-invalid");
    });
    form.querySelectorAll(".form-text.error").forEach((el) => {
      el.remove();
    });

    const requiredFields = form.querySelectorAll("[required]");

    requiredFields.forEach((field) => {
      if (field.type === "checkbox") {
        if (!field.checked) {
          hasError = true;
          const label = field
            .closest(".checkbox-wrapper")
            .querySelector("label");
          const errorMsg = label
            ? `Please check ${label.textContent.trim().split(" ").slice(0, 3).join(" ")}`
            : "This field is required";
          showError(field, errorMsg);
          if (!firstErrorField) firstErrorField = field;
        }
        return;
      }

      if (field.tagName === "SELECT" && field.value === "") {
        hasError = true;
        const label = field
          .closest(".department-form-group")
          .querySelector("label");
        const errorMsg = label
          ? `${label.textContent.trim().replace("*", "").trim()} is required`
          : "This field is required";
        showError(field, errorMsg);
        if (!firstErrorField) firstErrorField = field;
        return;
      }

      if (!field.value.trim()) {
        hasError = true;
        const label = field
          .closest(".department-form-group")
          .querySelector("label");
        const errorMsg = label
          ? `${label.textContent.trim().replace("*", "").trim()} is required`
          : "This field is required";
        showError(field, errorMsg);
        if (!firstErrorField) firstErrorField = field;
      }

      if (field.type === "email" && field.value.trim()) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(field.value.trim())) {
          hasError = true;
          showError(field, "Please enter a valid email address");
          if (!firstErrorField) firstErrorField = field;
        }
      }

      if (
        field.id === "{{ form.department_code.id_for_label }}" &&
        field.value.trim()
      ) {
        const codeRegex = /^[A-Z0-9_]+$/;
        if (!codeRegex.test(field.value.trim())) {
          hasError = true;
          showError(
            field,
            "Department code can only contain letters, numbers, and underscores",
          );
          if (!firstErrorField) firstErrorField = field;
        }
      }

      if (field.id === "{{ form.phone.id_for_label }}" && field.value.trim()) {
        const phoneRegex = /^[\+\d\s\-\(\)]{7,20}$/;
        if (!phoneRegex.test(field.value.trim())) {
          hasError = true;
          showError(field, "Please enter a valid phone number");
          if (!firstErrorField) firstErrorField = field;
        }
      }
    });

    if (openingTime && closingTime && !emergencyCheckbox.checked) {
      const openVal = openingTime.value;
      const closeVal = closingTime.value;

      if (openVal && closeVal && openVal >= closeVal) {
        hasError = true;
        showError(closingTime, "Closing time must be after opening time");
        if (!firstErrorField) firstErrorField = closingTime;
      }
    }

    if (departmentCode.length > 1 && departmentCode.value.trim().length < 4) {
      hasError = true;
      showError(
        departmentCode,
        "Department code must contain at least 4 characters.",
      );
      if (!firstErrorField) firstErrorField = departmentCode;
    }

    if (departmentName.length > 1 && departmentName.value.trim().length < 3) {
      hasError = true;
      showError(
        departmentName,
        "Department name must contain at least 3 letters.",
      );
      if (!firstErrorField) firstErrorField = departmentName;
    }

    if (
      shortName.length > 1 &&
      shortName.value.trim().length > 0 &&
      shortName.value.trim().length < 2
    ) {
      hasError = true;
      showError(shortName, "Short name must contain at least 2 letters.");
      if (!firstErrorField) firstErrorField = shortName;
    }

    if (departmentType.length > 1 && departmentType.value.trim().length < 4) {
      hasError = true;
      showError(
        departmentType,
        "Department type must contain at least 4 letters.",
      );
      if (!firstErrorField) firstErrorField = departmentType;
    }

    if (phoneInput) {
        const value = phoneInput.value.trim();
        const digits = value.replace(/\D/g, "");

        if (value !== "") {
            if (!/^\+?[0-9\s\-\(\)]+$/.test(value)) {
                hasError = true;
                showError(phoneInput, "Please enter a valid phone number.");
                if (!firstErrorField) firstErrorField = phoneInput;
            } else if (digits.length < 10 || digits.length > 15) {
                hasError = true;
                showError(phoneInput, "Phone number must contain 10 to 15 digits.");
                if (!firstErrorField) firstErrorField = phoneInput;
            }
        }
    }

    if (hasError) {
      e.preventDefault();
      if (firstErrorField) {
        setTimeout(function () {
          firstErrorField.focus();
          firstErrorField.scrollIntoView({
            behavior: "smooth",
            block: "center",
          });
        }, 100);
      }
    }
  });

  document.querySelectorAll(".form-text.error").forEach(function (el) {
    const formGroup = el.closest(".department-form-group");
    if (formGroup) {
      const field = formGroup.querySelector(".form-control, .form-select");
      if (field) {
        field.classList.add("is-invalid");
      }
      const checkbox = formGroup.querySelector('input[type="checkbox"]');
      if (checkbox) {
        const wrapper = checkbox.closest(".checkbox-wrapper");
        if (wrapper) {
          wrapper.classList.add("is-invalid");
        }
      }
    }
  });
});