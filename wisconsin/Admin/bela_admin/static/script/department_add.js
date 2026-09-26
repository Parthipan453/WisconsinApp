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
    if (/[A-Za-z]/.test(v))
      return 'Phone number cannot contain letters.';
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
    if (isNaN(n) || v.trim().length !== 4)
      return 'Enter a valid 4-digit year.';
    if (n < 1800 || n > cur)
      return `Year must be between 1800 and ${cur}.`;
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

/* ── Validate one field ── */
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
  const isEmpty    = val.trim() === '' || val === '';
  const isRequired = rules.includes('required') || rules.includes('required-select');

  if (error) {
    el.classList.add('is-invalid');
    if (errEl) {
      errEl.querySelector('span').textContent = error;
      errEl.classList.add('show');
    }
  } else {
    el.classList.remove('is-invalid');
    if (errEl) errEl.classList.remove('show');
  }

  return !error;
}

/* ── Attach listeners ── */
document.querySelectorAll('[data-validate]').forEach(el => {
  /* Only show error on blur (not while typing) — better UX */
  el.addEventListener('blur', () => validateField(el));

  /* Once the field has been touched, validate live on input too */
  el.addEventListener('input', () => {
    if (el.classList.contains('is-invalid')) validateField(el);
    /* Auto-uppercase department code */
    if (el.id === 'department_code') {
    el.value = el.value
        .toUpperCase()
        .replace(/\s+/g, ' ')   // Collapse multiple spaces
        .trimStart();           // Prevent leading spaces
}
  });
  el.addEventListener('change', () => {
    if (el.classList.contains('is-invalid')) validateField(el);
  });
});

/* ── Char counter for description ── */
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
    if (first) {
      first.scrollIntoView({ behavior: 'smooth', block: 'center' });
      first.focus();
    }
    return;
  }

  const btn = document.getElementById('submitBtn');
  btn.disabled = true;
  btn.innerHTML = '<i data-lucide="loader-2"></i> Saving…';
  if (typeof lucide !== 'undefined') lucide.createIcons();
});



 // Live preview mirror — purely cosmetic, does not affect form validation or submission.
  (function () {
    const $ = (id) => document.getElementById(id);

    function setText(el, value, placeholder) {
    if (!el) return;   // Prevent null errors

    if (value && value.trim()) {
        el.textContent = value.trim();
        el.classList.remove('placeholder');
    } else {
        el.innerHTML = '<span class="ph">' + placeholder + '</span>';
        el.classList.add('placeholder');
    }
}

    function updatePreview() {
      const name   = $('department_name') ? $('department_name').value : '';
      const code   = $('department_code') ? $('department_code').value : '';
      const short  = $('short_name')       ? $('short_name').value       : '';
      const year   = $('established_year') ? $('established_year').value : '';
      // const email  = $('email')            ? $('email').value            : '';
      // const office = $('office_location')  ? $('office_location').value  : '';
      const desc   = $('description')      ? $('description').value      : '';
      const schoolSel = $('school');
      const schoolText = schoolSel && schoolSel.selectedIndex > 0
        ? schoolSel.options[schoolSel.selectedIndex].text
        : '';

      setText($('prev_name'), name, 'Department name');
      setText($('prev_short'), short, 'Short name appears here');
      setText($('prev_code'), code, 'No code yet');
      setText($('prev_school'), schoolText, 'No school selected');
      setText($('prev_year'), year, 'Year not set');
      setText($('prev_desc'), desc, 'Your description will appear here as you type…');

      // setText($('prev_email'), email, 'No email yet');
      // setText($('prev_location'), office, 'No office location yet');
      
    }

    const fieldIds = [
      'department_name', 'department_code', 'short_name', 'school',
      'established_year', 'email', 'office_location', 'description'
    ];

    fieldIds.forEach((id) => {
      const el = $(id);
      if (el) {
        el.addEventListener('input', updatePreview);
        el.addEventListener('change', updatePreview);
      }
    });

  

    updatePreview();
   
  })();

  /* ── Init Lucide ── */
document.addEventListener('DOMContentLoaded', () => {
  if (typeof lucide !== 'undefined') lucide.createIcons();
});