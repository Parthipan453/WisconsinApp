// Speed code: Client-side validation rules 
const RULES = {

  'required': (v) =>
    v.trim().length > 0 ? null : 'This field is required.',

  'required-select': (v, el) => {
    if (v && v !== '') return null;
    const labels = {
      department: 'Please select a department.',
      academic_program: 'Please select an academic program.',
      degree: 'Please select a degree.',
    };
    return labels[el.id] || 'This field is required.';
  },

  'text-only': (v) => {
    if (!v.trim()) return null;
    return /^[A-Za-z\s'\-\.]+$/.test(v.trim())
      ? null : 'Only letters and spaces are allowed — numbers are not accepted.';
  },

 'course-code': (v) => {

    if (!v.trim()) return null;

    if (!/^\d+$/.test(v.trim())) {
        return 'Course code must contain numbers only.';
    }

    return null;
},

  // Speed code: Credits validation rule
  'credits': (v) => {

    if (!v.trim()) return null;
    if (/[A-Za-z!@#$%^&*()_+=]/.test(v))
      return 'Credits must contain numbers only.';
    const n = parseInt(v, 10);
    if (isNaN(n) || n < 1 || n > 20)
      return 'Credits must be between 1 and 20.';
    return null;
  },

  'email': (v) => {
    if (!v.trim()) return null;
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim())
      ? null : 'Enter a valid email address (e.g. course@wisc.edu).';
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

  'words': (v) => {
    if (!v.trim()) return null;
    const max = parseInt(document.getElementById('description')?.dataset.maxwords || '1000');
    const words = v.trim().split(/\s+/).filter(Boolean).length;
    return words > max ? `Description must be ${max} words or fewer (currently ${words} words).` : null;
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

// Speed code: Validate one field 
function validateField(el) {
  const raw   = el.getAttribute('data-validate') || '';
  const rules = raw.split('|').map(r => r.trim()).filter(Boolean);
  const val   = el.value;
  let   error = null;

  for (const rule of rules) {
    if (RULES[rule]) { error = RULES[rule](val, el); if (error) break; }
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

// Speed code: Attach listeners 
document.querySelectorAll('[data-validate]').forEach(el => {
  el.addEventListener('blur', () => validateField(el));

  el.addEventListener('input', () => {
    validateField(el);
    if (el.id === 'course_code') el.value = el.value.toUpperCase();
  });
  el.addEventListener('change', () => {
    validateField(el);
  });
});

// Speed code: Word counter for description 
const descTA  = document.getElementById('description');
const counter = document.getElementById('desc_counter');
if (descTA && counter) {
  const updateWordCount = () => {
    const text = descTA.value.trim();
    const words = text ? text.split(/\s+/).filter(Boolean).length : 0;
    const max = parseInt(descTA.dataset.maxwords || '1000');
    counter.textContent = `${words} / ${max} words`;
    counter.className = 'char-count' +
      (words > max ? ' over' : words > max * .9 ? ' warn' : '');
  };
  descTA.addEventListener('input', updateWordCount);
  updateWordCount();
}

// Speed code: Submit 
document.getElementById('courseForm').addEventListener('submit', function(e) {
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

// Speed code: Live preview mirror 
(function () {
  const $ = (id) => document.getElementById(id);

  function setText(el, value, placeholder) {
    if (value && value.trim()) {
      el.textContent = value.trim();
      el.classList.remove('placeholder');
    } else {
      el.innerHTML = '<span class="ph">' + placeholder + '</span>';
      el.classList.add('placeholder');
    }
  }

  function updatePreview() {
    const name     = $('course_name')     ? $('course_name').value         : '';
    const code     = $('course_code')     ? $('course_code').value         : '';
    const credits  = $('credits')         ? $('credits').value             : '';
    const desc     = $('description')     ? $('description').value         : '';
    const deptSel  = $('department');
    const deptText = deptSel && deptSel.selectedIndex > 0
      ? deptSel.options[deptSel.selectedIndex].text
      : '';

    const progSel  = $('academic_program');
    const progText = progSel && progSel.selectedIndex > 0
      ? progSel.options[progSel.selectedIndex].text
      : '';

    const degSel  = $('degree');
    const degText = degSel && degSel.selectedIndex > 0
      ? degSel.options[degSel.selectedIndex].text
      : '';

    setText($('prev_name'), name, 'Course name');
    setText($('prev_code'), code, 'Course code appears here');
    setText($('prev_credits'), credits, 'Credits not set');
    setText($('prev_department'), deptText, 'No department selected');
    setText($('prev_program'), progText, 'No program selected');
    setText($('prev_degree'), degText, 'No degree selected');
    setText($('prev_desc'), desc, 'Your description will appear here as you type…');
  }

  const fieldIds = [
    'course_name', 'course_code', 'credits', 'department', 'academic_program', 'degree', 'description'
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



const departmentSelect = document.getElementById("department");
const programSelect = document.getElementById("academic_program");

document.addEventListener("DOMContentLoaded", function () {

    const programChoices = window.choicesMap["academic_program"];

    if (!departmentSelect || !programSelect || !programChoices) {
        return;
    }

    const allOptions = Array.from(programSelect.options).map(option => ({
        value: option.value,
        label: option.text,
        department: option.dataset.department || ""
    }));

    function filterPrograms() {

        const departmentId = departmentSelect.value;

        const filtered = allOptions.filter(option =>
    option.value !== "" &&
    option.department === departmentId
);

        programChoices.clearStore();

        programChoices.setChoices(
            filtered.map(option => ({
                value: option.value,
                label: option.label,
                selected: false
            })),
            "value",
            "label",
            true
        );
    }

    departmentSelect.addEventListener("change", filterPrograms);

    filterPrograms();

});






// Speed code: Init Lucide 
document.addEventListener('DOMContentLoaded', () => {
  if (typeof lucide !== 'undefined') lucide.createIcons();
});
