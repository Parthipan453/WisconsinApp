"use strict";

const TOAST_DURATION = 4000;

const TOAST_CONFIG = {
  success: { icon: '<i class="fa-solid fa-circle-check"></i>', title: "Done" },
  error: { icon: '<i class="fa-solid fa-circle-xmark"></i>', title: "Error" },
  warning: { icon: '<i class="fa-solid fa-triangle-exclamation"></i>', title: "Warning" },
  info: { icon: '<i class="fa-solid fa-circle-info"></i>', title: "Info" },
};

function showToast(tag, message) {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const config = TOAST_CONFIG[tag] || TOAST_CONFIG.info;

  const toast = document.createElement("div");
  toast.className = `toast toast--${tag}`;
  toast.setAttribute("role", "alert");
  toast.setAttribute("aria-live", "assertive");

  const fillId = `toast-fill-${Date.now()}-${Math.random()}`;

  toast.innerHTML = `
    <div class="toast__body">
      <span class="toast__icon" aria-hidden="true">${config.icon}</span>
      <div class="toast__content">
        <div class="toast__title">${config.title}</div>
        <div class="toast__message">${message}</div>
      </div>
    </div>
    <button class="toast__dismiss" aria-label="Dismiss notification">
      <i class="fa-solid fa-xmark"></i>
    </button>
    <div class="toast__progress">
      <div class="toast__progress-fill" id="${fillId}"></div>
    </div>
  `;

  container.appendChild(toast);

  let dismissed = false;
  let autoTimer = null;
  let remainingMs = TOAST_DURATION;
  let startedAt = null;
  let isPaused = false;

  const fill = document.getElementById(fillId);

  function dismiss() {
    if (dismissed) return;
    dismissed = true;
    clearTimeout(autoTimer);
    toast.classList.remove("toast--visible");
    toast.classList.add("toast--dismissing");
    setTimeout(() => toast.remove(), 280);
  }

  function startTimer(durationMs) {
    clearTimeout(autoTimer);
    autoTimer = setTimeout(dismiss, durationMs);
  }

  toast.querySelector(".toast__dismiss").addEventListener("click", dismiss);

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      toast.classList.add("toast--visible");
    });
  });

  let animation = null;

  function startBarAnimation(durationMs) {
    if (animation) {
      animation.cancel();
    }
    animation = fill.animate(
      [{ transform: "scaleX(1)" }, { transform: "scaleX(0)" }],
      { duration: durationMs, easing: "linear", fill: "forwards" }
    );
    animation.onfinish = () => {
      dismiss();
    };
  }

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      startedAt = Date.now();
      startTimer(remainingMs);
      startBarAnimation(remainingMs);
    });
  });

  toast.addEventListener("mouseenter", () => {
    if (dismissed || isPaused) return;
    isPaused = true;
    clearTimeout(autoTimer);

    if (startedAt !== null) {
      const elapsed = Date.now() - startedAt;
      remainingMs = Math.max(0, remainingMs - elapsed);
      startedAt = null;
    }

    if (animation) {
      animation.pause();
    }
  });

  toast.addEventListener("mouseleave", () => {
    if (dismissed || !isPaused) return;
    isPaused = false;

    if (remainingMs <= 0) {
      dismiss();
      return;
    }

    startedAt = Date.now();
    startTimer(remainingMs);

    if (animation) {
      animation.updatePlaybackRate(1);
      animation.play();
    }
  });
}

function initToasts() {
  const items = document.querySelectorAll("[data-toast-tag]");
  items.forEach((el, index) => {
    setTimeout(() => {
      showToast(el.dataset.toastTag, el.dataset.toastMessage);
    }, index * 120);
  });
}

function togglePasswordVisibility(inputId, toggleBtn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const isHidden = input.type === "password";
  input.type = isHidden ? "text" : "password";
  toggleBtn.innerHTML = isHidden
    ? '<i class="fa-regular fa-eye-slash"></i>'
    : '<i class="fa-regular fa-eye"></i>';
  toggleBtn.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
}

const STRENGTH_LEVELS = [
  { width: "0%", color: "#c5050c", label: "" },
  { width: "25%", color: "#c5050c", label: "Weak" },
  { width: "50%", color: "#f59e0b", label: "Fair" },
  { width: "75%", color: "#3b82f6", label: "Good" },
  { width: "100%", color: "#22c55e", label: "Strong" },
];

function updatePasswordStrength(value) {
  const fill  = document.getElementById("password-strength-fill");
  const label = document.getElementById("password-strength-label");
  if (!fill || !label) return;

  let score = 0;
  if (value.length >= 8) score++;
  if (/[A-Z]/.test(value)) score++;
  if (/[0-9]/.test(value)) score++;
  if (/[^A-Za-z0-9]/.test(value)) score++;

  const level = STRENGTH_LEVELS[score];
  fill.style.width = level.width;
  fill.style.background = level.color;
  label.textContent = level.label;
  label.style.color = level.color;
}

function handleFormSubmit(form) {
  const btn = form.querySelector(".setup-form__submit");
  if (!btn) return;
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating account…';
}

const FIELD_VALIDATORS = {
  first_name(value) {
    if (!value.trim()) return "First name is required.";
    if (!/^[A-Za-z\s]+$/.test(value.trim())) return "First name may only contain letters.";
    return null;
  },
  last_name(value) {
    if (!value.trim()) return "Last name is required.";
    if (!/^[A-Za-z\s]+$/.test(value.trim())) return "Last name may only contain letters.";
    return null;
  },
  username(value) {
    if (!value.trim()) return "Username is required.";
    if (!/^[a-zA-Z0-9_]+$/.test(value.trim())) return "Username may only contain letters, digits, and underscores.";
    return null;
  },
  email(value) {
    if (!value.trim()) return "Email address is required.";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim())) return "Enter a valid email address.";
    return null;
  },
  mobile_number(value) {
    if (!value.trim()) return "Mobile number is required.";
    const digits = value.replace(/[\s\-\(\)\+]/g, "");
    if (!/^\d+$/.test(digits) || digits.length < 7 || digits.length > 15)
      return "Enter a valid mobile number (7–15 digits).";
    return null;
  },
  password(value) {
    if (!value) return "Password is required.";
    const errors = [];
    if (value.length < 8) errors.push("at least 8 characters");
    if (!/[A-Z]/.test(value)) errors.push("one uppercase letter");
    if (!/[0-9]/.test(value)) errors.push("one number");
    if (!/[^A-Za-z0-9]/.test(value)) errors.push("one special character");
    return errors.length ? `Password must contain ${errors.join(", ")}.` : null;
  },
  confirm_password(value) {
    if (!value) return "Please confirm your password.";
    const pw = document.getElementById("password");
    if (pw && value !== pw.value) return "Passwords do not match.";
    return null;
  },
};

function showFieldError(input, message) {
  clearFieldError(input);
  input.classList.add("setup-form__input--error");
  const err = document.createElement("span");
  err.className = "setup-form__field-error js-field-error";
  err.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> ${message}`;
  input.closest(".setup-form__field").appendChild(err);
}

function clearFieldError(input) {
  input.classList.remove("setup-form__input--error");
  const existing = input.closest(".setup-form__field")?.querySelector(".js-field-error");
  if (existing) existing.remove();
}

function validateField(input) {
  const name = input.name || input.id;
  const validator = FIELD_VALIDATORS[name];
  if (!validator) return true;
  const error = validator(input.value);
  if (error) {
    showFieldError(input, error);
    return false;
  }
  clearFieldError(input);
  return true;
}

function validateForm(form) {
  const inputs = form.querySelectorAll(".setup-form__input");
  let allValid = true;
  inputs.forEach(input => {
    if (!validateField(input)) allValid = false;
  });
  return allValid;
}

document.addEventListener("DOMContentLoaded", function () {
  initToasts();

  const passwordInput = document.getElementById("password");
  if (passwordInput) {
    passwordInput.addEventListener("input", () => updatePasswordStrength(passwordInput.value));
  }

  const form = document.getElementById("setup-form");
  if (!form) return;

  form.querySelectorAll(".setup-form__input").forEach(input => {
    input.addEventListener("input", () => {
      const serverErr = input.closest(".setup-form__field")?.querySelector(".setup-form__field-error:not(.js-field-error)");
      if (serverErr) serverErr.remove();
      clearFieldError(input);
    });
  });

  form.addEventListener("submit", (e) => {
    const valid = validateForm(form);
    if (!valid) {
      e.preventDefault();
      const firstErr = form.querySelector(".setup-form__input--error");
      if (firstErr) firstErr.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    handleFormSubmit(form);
  });

  form.querySelectorAll(".setup-form__password-toggle").forEach(btn =>
    btn.setAttribute("aria-label", "Show password")
  );
});