document.addEventListener('DOMContentLoaded', function () {
  initToasts();
  initPasswordStrength();
});

const TOAST_DURATION = 4000;

function initToasts() {
  const container = document.getElementById('toast-container');
  if (!container) return;

  document.querySelectorAll('[data-toast-tag]').forEach(function (el) {
    showToast(el.getAttribute('data-toast-tag'), el.getAttribute('data-toast-message'));
    el.remove();
  });
}

function showToast(tag, message) {
  const container = document.getElementById('toast-container');
  if (!container || !message) return;

  const type = ['success', 'error', 'warning', 'info'].includes(tag) ? tag : 'info';
  const icons = {
    success: 'fa-circle-check',
    error: 'fa-circle-exclamation',
    warning: 'fa-triangle-exclamation',
    info: 'fa-circle-info',
  };
  const titles = { success: 'Success', error: 'Error', warning: 'Warning', info: 'Notice' };

  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.innerHTML = `
    <div class="toast__body">
      <i class="fa-solid ${icons[type]} toast__icon"></i>
      <div class="toast__content">
        <div class="toast__title">${titles[type]}</div>
        <div class="toast__message">${message}</div>
      </div>
    </div>
    <button type="button" class="toast__dismiss" aria-label="Dismiss">
      <i class="fa-solid fa-xmark"></i>
    </button>
    <div class="toast__progress"><div class="toast__progress-fill"></div></div>
  `;

  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('toast--visible'));

  const fill = toast.querySelector('.toast__progress-fill');
  fill.style.transition = `transform ${TOAST_DURATION}ms linear`;
  requestAnimationFrame(() => { fill.style.transform = 'scaleX(0)'; });

  const dismiss = () => {
    toast.classList.remove('toast--visible');
    toast.classList.add('toast--dismissing');
    setTimeout(() => toast.remove(), 300);
  };

  const timer = setTimeout(dismiss, TOAST_DURATION);
  toast.querySelector('.toast__dismiss').addEventListener('click', function () {
    clearTimeout(timer);
    dismiss();
  });
}

function togglePasswordVisibility(fieldId, button) {
  const input = document.getElementById(fieldId) || document.getElementById('id_' + fieldId);
  if (!input) return;

  const icon = button.querySelector('i');
  const showing = input.type === 'password';
  input.type = showing ? 'text' : 'password';

  if (icon) {
    icon.classList.toggle('fa-eye', !showing);
    icon.classList.toggle('fa-eye-slash', showing);
  }
  button.setAttribute('aria-label', showing ? 'Hide password' : 'Show password');
}

function initPasswordStrength() {
  const passwordInput = document.getElementById('id_new_password');
  const fill = document.getElementById('password-strength-fill');
  const label = document.getElementById('password-strength-label');
  if (!passwordInput || !fill || !label) return;

  const levels = [
    { min: 0, width: '0%', color: 'transparent', text: '' },
    { min: 1, width: '20%', color: '#dc2626', text: 'Very weak' },
    { min: 2, width: '40%', color: '#d97706', text: 'Weak' },
    { min: 3, width: '60%', color: '#eab308', text: 'Fair' },
    { min: 4, width: '80%', color: '#16a34a', text: 'Good' },
    { min: 5, width: '100%', color: '#15803d', text: 'Strong' },
  ];

  passwordInput.addEventListener('input', function () {
    const value = passwordInput.value;
    const score = scorePassword(value);
    const level = levels.slice().reverse().find((l) => score >= l.min) || levels[0];
    fill.style.width = level.width;
    fill.style.background = level.color;
    label.textContent = value ? level.text : '';
  });
}

function scorePassword(value) {
  let score = 0;
  if (value.length >= 8) score++;
  if (value.length >= 12) score++;
  if (/[A-Z]/.test(value) && /[a-z]/.test(value)) score++;
  if (/\d/.test(value)) score++;
  if (/[^A-Za-z0-9]/.test(value)) score++;
  return score;
}