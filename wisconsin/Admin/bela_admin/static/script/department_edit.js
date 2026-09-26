const RULES = {
  'required': (v) =>
    v.trim().length > 0 ? null : 'This field is required.',

  'required-select': (v) =>
    (v && v !== '') ? null : 'Please select a school.',

  'text-only': (v) => {
    if (!v.trim()) return null;
    return /^[A-Za-z\s'\-\.]+$/.test(v.trim())
      ? null : 'Only letters and spaces are allowed — numbers are not accepted.';
  },

  'department-code': (v) => {

    if (!v.trim()) return null;

    return /^[A-Za-z\s-]+$/.test(v.trim())
        ? null
        : 'Department code can contain only letters, spaces and hyphens.';
},

  'email': (v) => {
    if (!v.trim()) return null;
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim())
      ? null : 'Enter a valid email address (e.g. dept@wisc.edu).';
  },

  'phone': (v) => {
    if (!v.trim()) return null;
    if (/[A-Za-z]/.test(v)) return 'Phone number cannot contain letters.';
    return /^[0-9\s\+\-\(\)\.]{7,20}$/.test(v.trim())
      ? null : 'Enter a valid phone number (e.g. +1 608-123-4567).';
  },

  'url': (v) => {
    if (!v.trim()) return null;
    try { new URL(v.trim()); return null; }
    catch { return 'Enter a valid URL starting with https:// or http://'; }
  },

  'year': (v) => {
    if (!v.trim()) return null;
    if (/[A-Za-z!@#$%^&*()_+=]/.test(v))
      return 'Year must contain numbers only — letters are not accepted.';
    const n = parseInt(v, 10);
    const cur = new Date().getFullYear();
    if (isNaN(n) || v.trim().length !== 4) return 'Enter a valid 4-digit year.';
    if (n < 1800 || n > cur) return `Year must be between 1800 and ${cur}.`;
    return null;
  },
};

function applyMinMax(v, rules) {
  for (const rule of rules) {
    const minM = rule.match(/^min:(\d+)$/);
    const maxM = rule.match(/^max:(\d+)$/);
    if (minM && v.trim().length > 0 && v.trim().length < parseInt(minM[1]))
      return `Minimum ${minM[1]} characters required.`;
    if (maxM && v.trim().length > parseInt(maxM[1]))
      return `Maximum ${maxM[1]} characters allowed.`;
  }
  return null;
}

function validateField(el) {
  const raw   = el.getAttribute('data-validate') || '';
  const rules = raw.split('|').map(r => r.trim()).filter(Boolean);
  const val   = el.value;
  let   error = null;
  for (const rule of rules) {
    if (RULES[rule]) { error = RULES[rule](val); if (error) break; }
  }
  if (!error) error = applyMinMax(val, rules);
  const errEl = document.getElementById('err_' + el.id);
  if (error) {
    el.classList.add('is-invalid');
    if (errEl) { errEl.querySelector('span').textContent = error; errEl.classList.add('show'); }
  } else {
    el.classList.remove('is-invalid');
    if (errEl) errEl.classList.remove('show');
  }
  return !error;
}

document.querySelectorAll('[data-validate]').forEach(el => {
  el.addEventListener('blur',   () => validateField(el));
  el.addEventListener('input',  () => {
    if (el.classList.contains('is-invalid')) validateField(el);
    if (el.id === 'department_code') el.value = el.value.toUpperCase();
  });
  el.addEventListener('change', () => {
    if (el.classList.contains('is-invalid')) validateField(el);
  });
});

/* ── Char counter ── */
const descTA  = document.getElementById('description');
const counter = document.getElementById('desc_counter');
if (descTA && counter) {
  descTA.addEventListener('input', () => {
    const len = descTA.value.length;
    const max = parseInt(descTA.dataset.maxchars);
    counter.textContent = `${len} / ${max} characters`;
    counter.className = 'char-count' +
      (len > max ? ' over' : len > max * .9 ? ' warn' : '');
  });
}

/* ── Submit ── */
document.getElementById('deptForm').addEventListener('submit', function(e) {
  let allValid = true;
  document.querySelectorAll('[data-validate]').forEach(el => {
    if (!validateField(el)) allValid = false;
  });
  if (!allValid) {
    e.preventDefault();
    const first = document.querySelector('.is-invalid');
    if (first) { first.scrollIntoView({ behavior:'smooth', block:'center' }); first.focus(); }
    return;
  }
  const btn = document.getElementById('submitBtn');
  btn.disabled = true;
  btn.innerHTML = '<i data-lucide="loader-2"></i> Updating…';
  if (typeof lucide !== 'undefined') lucide.createIcons();
});

/* ── Init Lucide ── */
document.addEventListener('DOMContentLoaded', () => {
  if (typeof lucide !== 'undefined') lucide.createIcons();
});
