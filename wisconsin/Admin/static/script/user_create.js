
/* ***************************************************** Arun code *************************************************** */

(function () {
  'use strict';


  const SECTIONS = ['role', 'identity', 'typedetails', 'review'];

  function showSection(name) {
    SECTIONS.forEach((s) => {
      const sec = document.getElementById('sec-' + s);
      const pill = document.querySelector(`.up-pill[data-section="${s}"]`);
      if (!sec) return;
      const isActive = s === name;
      sec.classList.toggle('up-section--active', isActive);
      if (pill) pill.classList.toggle('up-pill--active', isActive);
    });
    updateProgress(name);
    window.scrollTo({ top: 0, behavior: 'smooth' });
 
    if (name === 'review') populateReview();
  }

  document.querySelectorAll('[data-next]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const currentSection = btn.closest('.up-section');
      const sectionName = currentSection ? currentSection.dataset.section : null;
      if (!sectionName) { showSection(btn.dataset.next); return; }

      const formatOk = validateSection(sectionName);
      if (!formatOk) return;

      if (sectionName === 'identity') {
        btn.disabled = true;
        const origLabel = btn.innerHTML;
        btn.innerHTML = 'Checking…';
        const uniqueOk = await validateIdentityUniqueness();
        btn.disabled = false;
        btn.innerHTML = origLabel;
        if (!uniqueOk) return;
      }

      if (sectionName === 'typedetails') {
        btn.disabled = true;
        const origLabel = btn.innerHTML;
        btn.innerHTML = 'Checking…';
        const uniqueOk = await validateTypeDetailsUniqueness();
        btn.innerHTML = origLabel;
        btn.disabled = !sectionComplete('typedetails');
        if (!uniqueOk) return;
      }

      showSection(btn.dataset.next);
    });
  });

  const UNIQUE_CHECK_ENDPOINT = '/dashboard/users/check-unique/';

  async function checkUnique(field, value) {
    if (!value) return { taken: false };
    try {
      const editUserIdEl = document.getElementById('editUserId');
      const excludeId = editUserIdEl ? editUserIdEl.value : '';
      const params = new URLSearchParams({ field, value });
      if (excludeId) params.set('exclude_id', excludeId);
      const res = await fetch(`${UNIQUE_CHECK_ENDPOINT}?${params.toString()}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      if (!res.ok) return { taken: false };
      return await res.json();
    } catch {
      return { taken: false };
    }
  }

  async function validateIdentityUniqueness() {
    const checks = [
      { id: 'id_username', field: 'username', label: 'This username is already taken.' },
      // Jack Code Start's
      { id: 'id_ssn_number', field: 'ssn_number', label: 'This SSN number already exists.' },
      // Jack Code End's
      { id: 'id_email', field: 'email', label: 'A user with this email already exists.' },
      { id: 'id_university_id', field: 'university_id', label: 'This university ID is already registered.' },
      { id: 'id_mobile_number', field: 'mobile_number', label: 'This mobile number is already registered.' },
    ];

    let allOk = true;
    let firstInvalidEl = null;

    await Promise.all(checks.map(async (c) => {
      const input = document.getElementById(c.id);
      if (!input) return;
      const v = input.value.trim();
      if (!v) return;
      const result = await checkUnique(c.field, v);
      if (result.taken) {
        setFieldError(input, c.label);
        allOk = false;
        if (!firstInvalidEl) firstInvalidEl = input;
      }
    }));

    if (firstInvalidEl) {
      firstInvalidEl.focus();
      firstInvalidEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    return allOk;
  }

  const UNIQUE_FIELD_MAP = { id_username: 'username', id_ssn_number: 'ssn_number', id_email: 'email', id_university_id: 'university_id', id_mobile_number: 'mobile_number' };
  const UNIQUE_LABEL_MAP = {
    id_username: 'This username is already taken.',
    // Jack Code Start's
    id_ssn_number: 'This SSN number already exists.',
    // Jack Code End's
    id_email: 'A user with this email already exists.',
    id_university_id: 'This university ID is already registered.',
    id_mobile_number: 'This mobile number is already registered.',
  };


  const TYPEDETAILS_UNIQUE_FIELDS = {
    student: [
      { id: 'id_student_number', field: 'student_number', label: 'This student number is already taken.' },
      { id: 'id_university_email', field: 'university_email', label: 'This university email is already registered.' },
    ],
    faculty: [
      { id: 'id_faculty_employee_id', field: 'faculty_employee_id', label: 'This employee ID is already taken.' },
      { id: 'id_faculty_email', field: 'faculty_email', label: 'This work email is already registered.' },
    ],
    staff: [
      { id: 'id_staff_employee_id', field: 'staff_employee_id', label: 'This employee ID is already taken.' },
      { id: 'id_staff_work_email', field: 'staff_work_email', label: 'This work email is already registered.' },
    ],
    admin: [
      { id: 'id_admin_employee_id', field: 'admin_employee_id', label: 'This employee ID is already taken.' },
      { id: 'id_admin_work_email', field: 'admin_work_email', label: 'This work email is already registered.' },
    ],
  };

  const flaggedTypeDetailsValue = {};

  function wireTypeDetailsUniqueCheck(id, field, label) {
    const input = document.getElementById(id);
    if (!input) return;

    input.addEventListener('blur', async () => {
      const v = input.value.trim();
      if (!v) { clearFieldError(input); flaggedTypeDetailsValue[id] = null; refreshNextButtonStates(); return; }

      const result = await checkUnique(field, v);
      if (result.taken) {
        setFieldError(input, label);
        flaggedTypeDetailsValue[id] = v;
      } else {
        const errEl = getErrorEl(input);
        if (errEl && errEl.textContent === label) clearFieldError(input);
        flaggedTypeDetailsValue[id] = null;
      }
      refreshNextButtonStates();
    });

    input.addEventListener('input', () => {
      const v = input.value.trim();
      if (flaggedTypeDetailsValue[id] != null && v !== flaggedTypeDetailsValue[id]) {
        const errEl = getErrorEl(input);
        if (errEl && errEl.textContent === label) clearFieldError(input);
        flaggedTypeDetailsValue[id] = null;
        refreshNextButtonStates();
      }
    });
  }

  Object.values(TYPEDETAILS_UNIQUE_FIELDS).flat().forEach((c) => {
    wireTypeDetailsUniqueCheck(c.id, c.field, c.label);
  });

  async function validateTypeDetailsUniqueness() {
    const checks = TYPEDETAILS_UNIQUE_FIELDS[currentType] || [];
    let allOk = true;
    let firstInvalidEl = null;

    await Promise.all(checks.map(async (c) => {
      const input = document.getElementById(c.id);
      if (!input) return;
      const v = input.value.trim();
      if (!v) return;
      const result = await checkUnique(c.field, v);
      if (result.taken) {
        setFieldError(input, c.label);
        flaggedTypeDetailsValue[c.id] = v;
        allOk = false;
        if (!firstInvalidEl) firstInvalidEl = input;
      } else {
        const errEl = getErrorEl(input);
        if (errEl && errEl.textContent === c.label) clearFieldError(input);
        flaggedTypeDetailsValue[c.id] = null;
      }
    }));

    if (firstInvalidEl) {
      firstInvalidEl.focus();
      firstInvalidEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    return allOk;
  }

  const uniquenessFlaggedValue = { id_username: null, id_ssn_number: null, id_email: null, id_university_id: null, id_mobile_number: null };

  ['id_username', 'id_ssn_number', 'id_email', 'id_university_id', 'id_mobile_number'].forEach((id) => {
    const input = document.getElementById(id);
    if (!input) return;

    input.addEventListener('blur', async () => {
      const v = input.value.trim();
      if (!v) { clearFieldError(input); uniquenessFlaggedValue[id] = null; return; }

      const result = await checkUnique(UNIQUE_FIELD_MAP[id], v);
      if (result.taken) {
        setFieldError(input, UNIQUE_LABEL_MAP[id]);
        uniquenessFlaggedValue[id] = v;
      } else {
        const field = input.closest('.up-field');
        const errEl = field ? field.querySelector('.up-field-error') : null;
        if (errEl && errEl.textContent === UNIQUE_LABEL_MAP[id]) {
          clearFieldError(input);
        }
        uniquenessFlaggedValue[id] = null;
      }
    });

    input.addEventListener('input', () => {
      const v = input.value.trim();
      if (uniquenessFlaggedValue[id] !== null && v !== uniquenessFlaggedValue[id]) {
        const field = input.closest('.up-field');
        const errEl = field ? field.querySelector('.up-field-error') : null;
        if (errEl && errEl.textContent === UNIQUE_LABEL_MAP[id]) {
          clearFieldError(input);
        }
        uniquenessFlaggedValue[id] = null;
      }
    });
  });


  function getErrorEl(input) {
    const field = input.closest('.up-field');
    if (!field) return null;
    return (
      field.querySelector(`[data-error="${input.id}"]`) ||
      field.querySelector('.up-field-error')
    );
  }

  function setFieldError(input, msg) {
    const field = input.closest('.up-field');
    const errEl = getErrorEl(input);
    if (errEl) errEl.textContent = msg;
    if (field) {
      field.classList.add('up-field--error');
      field.classList.remove('up-field--valid');
    }
  }

  function clearFieldError(input) {
    const field = input.closest('.up-field');
    const errEl = getErrorEl(input);
    if (errEl) errEl.textContent = '';
    if (field) {
      field.classList.remove('up-field--error');
      if (input.value.trim()) field.classList.add('up-field--valid');
    }
  }

  const fieldValidators = { 
    id_username(input) {
      const v = input.value.trim();
      if (!v) { setFieldError(input, 'Username is required.'); return false; }
      if (v.length < 3) { setFieldError(input, 'At least 3 characters required.'); return false; }
      if (!/^[a-zA-Z0-9_]+$/.test(v)) { setFieldError(input, 'Letters, numbers, underscores only.'); return false; }
      clearFieldError(input);
      return true;
    },
    id_email(input) {
      const v = input.value.trim();
      if (!v) { setFieldError(input, 'Email address is required.'); return false; }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) { setFieldError(input, 'Enter a valid email address.'); return false; }
      clearFieldError(input);
      return true;
    },
    id_first_name(input) {
      const v = input.value.trim();
      if (!v) { setFieldError(input, 'First name is required.'); return false; }
      if (!/^[a-zA-Z\s\-']+$/.test(v)) { setFieldError(input, 'Letters, hyphens, apostrophes only.'); return false; }
      clearFieldError(input);
      return true;
    },
    id_last_name(input) {
      const v = input.value.trim();
      if (!v) { setFieldError(input, 'Last name is required.'); return false; }
      if (!/^[a-zA-Z\s\-']+$/.test(v)) { setFieldError(input, 'Letters, hyphens, apostrophes only.'); return false; }
      clearFieldError(input);
      return true;
    },
    // Jack Code Start's
    id_ssn_number(input) {
      const v = input.value.trim();

      if (!v) {
        setFieldError(input, 'SSN number is required.');
        return false;
      }

      if (!/^\d{3}-\d{2}-\d{4}$/.test(v)) {
        setFieldError(
          input,
          'Enter a valid SSN in the format XXX-XX-XXXX.'
        );
        return false;
      }

      const [area, group, serial] = v.split('-');

      if (area === '000' || group === '00' || serial === '0000') {
        setFieldError(input, 'Enter a valid SSN number.');
        return false;
      }

      clearFieldError(input);
      return true;
    },
    // Jack Code End's
    id_mobile_number(input) {
      const v = input.value.trim();
      if (!v) { setFieldError(input, 'Mobile number is required.'); return false; }
      if (!isValidPhone(v)) {
        setFieldError(input, 'Enter a valid phone number, e.g. 9876543210 or +1 608-555-0123.');
        return false;
      }
      clearFieldError(input);
      return true;
    },
    id_confirm_mobile(input) {
      const mobile = (document.getElementById('id_mobile_number') || {}).value || '';
      const v = input.value.trim();
      if (!v) { setFieldError(input, 'Please confirm the mobile number.'); return false; }
      if (!isValidPhone(v)) { setFieldError(input, 'Enter a valid phone number.'); return false; }
      if (normalizePhone(v) !== normalizePhone(mobile)) {
        setFieldError(input, 'Mobile numbers do not match.');
        return false;
      }
      clearFieldError(input);
      return true;
    },
    id_date_of_birth(input) {
      const v = input.value;
      if (!v) { clearFieldError(input); return true; }
      const dob = new Date(v);
      const now = new Date();
      if (dob > now) { setFieldError(input, 'Date of birth cannot be in the future.'); return false; }
      const age = (now - dob) / (365.25 * 24 * 3600 * 1000);
      if (age < 10) { setFieldError(input, 'User must be at least 10 years old.'); return false; }
      if (age > 120) { setFieldError(input, 'Enter a valid date of birth.'); return false; }
      clearFieldError(input);
      return true;
    },

    id_firearm_firearm_name(input) {
      const v = input.value.trim();
      if (!v) { setFieldError(input, 'Firearm name is required.'); return false; }
      clearFieldError(input);
      return true;
    },
    id_firearm_firearm_type(input) {
      const v = input.value.trim();
      if (!v) { setFieldError(input, 'Firearm type is required.'); return false; }
      clearFieldError(input);
      return true;
    },
    id_firearm_serial_number(input) {
      const v = input.value.trim();
      if (!v) { setFieldError(input, 'Serial number is required.'); return false; }
      clearFieldError(input);
      return true;
    },

  };
  
  // Jack Code Start's
  const ssnInput = document.getElementById('id_ssn_number');

  if (ssnInput) {
    ssnInput.setAttribute('maxlength', '11');
    ssnInput.setAttribute('inputmode', 'numeric');

    ssnInput.addEventListener('input', function () {
      let value = this.value.replace(/\D/g, '').substring(0, 9);

      if (value.length > 5) {
        value = value.slice(0, 3) + '-' +
                value.slice(3, 5) + '-' +
                value.slice(5);
      } else if (value.length > 3) {
        value = value.slice(0, 3) + '-' +
                value.slice(3);
      }

      this.value = value;

      fieldValidators.id_ssn_number(this);
      refreshNextButtonStates();
    });
  }

  // Jack Code End's

  function toggleFirearmSection() {
    document.querySelectorAll('.up-yn-option').forEach((opt) => {
      const input = opt.querySelector('input[type="radio"]');
      opt.classList.toggle('up-yn-option--active', !!(input && input.checked));
    });

    const section = document.getElementById('firearmDetailsSection');
    if (!section) return;

    if (isFirearmYes()) {
      section.classList.add('up-firearm-section--open');
      FIREARM_REQUIRED_IDS.forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.setAttribute('required', 'required');
      });
    } else {
      section.classList.remove('up-firearm-section--open');
      FIREARM_REQUIRED_IDS.forEach((id) => {
        const el = document.getElementById(id);
        if (el) { el.removeAttribute('required'); clearFieldError(el); }
      });
    }
    if (typeof refreshNextButtonStates === 'function') refreshNextButtonStates();
  }

  document.querySelectorAll('input[name="has_firearm"]').forEach((radio) => {
    radio.addEventListener('change', toggleFirearmSection);
  });
  



  const SECTION_REQUIRED_FIELDS = {
    role: [],
    identity: ['id_username', 'id_email', 'id_first_name', 'id_last_name', 'id_mobile_number', 'id_confirm_mobile', 'id_date_of_birth', 'id_ssn_number'],
    typedetails: [],
    review: [],
  };

   const FIREARM_REQUIRED_IDS = ['id_firearm_firearm_name', 'id_firearm_firearm_type', 'id_firearm_serial_number'];

  function isFirearmYes() {
    const yes = document.getElementById('id_has_firearm_yes');
    return !!(yes && yes.checked);
  }


  function validateSection(sectionName) {
    // const fieldIds = SECTION_REQUIRED_FIELDS[sectionName] || [];
    // let allValid = true;
     const fieldIds = (SECTION_REQUIRED_FIELDS[sectionName] || []).slice();
    if (sectionName === 'identity' && isFirearmYes()) {
      fieldIds.push(...FIREARM_REQUIRED_IDS);
    }
    let allValid = true;
    let firstInvalidEl = null;

    fieldIds.forEach((id) => {
      const input = document.getElementById(id);
      if (!input) return;
      const validator = fieldValidators[id];
      if (!validator) return;
      const ok = validator(input);
      if (!ok) {
        allValid = false;
        if (!firstInvalidEl) firstInvalidEl = input;
      }
    });

    if (!allValid && firstInvalidEl) {
      firstInvalidEl.focus();
      firstInvalidEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    return allValid;
  }

  Object.keys(fieldValidators).forEach((id) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('blur', () => fieldValidators[id](el));
    el.addEventListener('input', () => {
      const field = el.closest('.up-field');
      if (field && field.classList.contains('up-field--error')) {
        fieldValidators[id](el);
      }
    });
  });

  document.querySelectorAll('[data-prev]').forEach((btn) => {
    btn.addEventListener('click', () => showSection(btn.dataset.prev));
  });

  document.querySelectorAll('.up-review-edit-btn[data-goto]').forEach((btn) => {
    btn.addEventListener('click', () => showSection(btn.dataset.goto));
  });

  const pillOrder = SECTIONS;
  let furthestReached = 0;
  document.querySelectorAll('.up-pill[data-section]').forEach((pill) => {
    pill.addEventListener('click', () => {
      const idx = pillOrder.indexOf(pill.dataset.section);
      if (idx <= furthestReached) showSection(pill.dataset.section);
    });
  });

  function updateProgress(name) {
    const idx = SECTIONS.indexOf(name);
    if (idx > furthestReached) furthestReached = idx;
    const pct = Math.round(((idx + 1) / SECTIONS.length) * 100);
    const fill = document.getElementById('progressFill');
    const pctEl = document.getElementById('progressPct');
    if (fill) fill.style.width = pct + '%';
    if (pctEl) pctEl.textContent = pct + '%';
  }

  const ROLE_REQUIRED_IDS = ['id_role', 'id_account_status'];

  const IDENTITY_REQUIRED_IDS = [
    'id_username', 'id_email', 'id_first_name', 'id_last_name',
    'id_mobile_number', 'id_confirm_mobile', 'id_ssn_number'
  ];

  const TYPEDETAILS_REQUIRED_IDS = {
    student: [
      'id_student_number', 'id_university_email',
      'id_school', 'id_department', 'id_degree', 'id_program',
      'id_student_address_type', 'id_student_address_line_1',
      'id_student_city', 'id_student_state', 'id_student_postal_code', 'id_student_country',
      'id_student_emergency_name', 'id_student_emergency_relationship', 'id_student_emergency_phone',
    ],
    faculty: [
      'id_faculty_employee_id', 'id_faculty_email',
      'id_faculty_degree', 'id_faculty_institution_name',
    ],
    staff: [
      'id_staff_employee_id', 'id_staff_work_email', 'id_staff_job_title', 'id_staff_position_start_date',
      'id_staff_address_type', 'id_staff_address_line_1', 'id_staff_city', 'id_staff_state',
      'id_staff_postal_code', 'id_staff_country',
      'id_staff_emergency_name', 'id_staff_emergency_relationship', 'id_staff_emergency_phone',
      'id_staff_degree', 'id_staff_institution_name',
    ],
    admin: ['id_admin_employee_id', 'id_admin_work_email'],
  };

  const TYPE_META = {
    student: {
      label: 'Student',
      nextLabel: 'Student Details',
      detailTitle: 'Student Details',
      detailSub: 'Academic and enrollment information',
      hintText: 'Student selected — academic details collected in step 3.',
      iconSvg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 3L2 8l10 5 10-5-10-5z"/>
        <path d="M2 8v6c0 3.3 4.5 6 10 6s10-2.7 10-6V8"/>
      </svg>`,
    },
    faculty: {
      label: 'Faculty',
      nextLabel: 'Faculty Details',
      detailTitle: 'Faculty Details',
      detailSub: 'Employment and academic appointment information',
      hintText: 'Faculty selected — employment and rank details collected in step 3.',
      iconSvg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="3" y="4" width="18" height="16" rx="2"/>
        <path d="M8 4v16M16 4v16M3 12h18"/>
      </svg>`,
    },
    staff: {
      label: 'Staff',
      nextLabel: 'Staff Details',
      detailTitle: 'Staff Details',
      detailSub: 'Employment and position information',
      hintText: 'Staff selected — job title and department details collected in step 3.',
      iconSvg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="2" y="7" width="20" height="14" rx="2"/>
        <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>
      </svg>`,
    },
    admin: {
      label: 'Admin',
      nextLabel: 'Admin Details',
      detailTitle: 'Admin Details',
      detailSub: 'System access and administrative scope',
      hintText: 'Admin selected — scope and access details collected in step 3.',
      iconSvg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 2l3 7h7l-5.5 4 2 7L12 16l-6.5 4 2-7L2 9h7z"/>
      </svg>`,
    },
  };

  let currentType = 'student';

  function selectUserType(type) {
    if (!TYPE_META[type]) return;
    currentType = type;

    document.querySelectorAll('.up-type-card').forEach((card) => {
      const isSelected = card.dataset.type === type;
      card.classList.toggle('up-type-card--selected', isSelected);
      card.setAttribute('aria-checked', isSelected ? 'true' : 'false');
    });

    const hiddenInput = document.getElementById('id_user_type');
    if (hiddenInput) hiddenInput.value = type;

    const hintEl = document.getElementById('typeHintText');
    if (hintEl) hintEl.textContent = TYPE_META[type].hintText;

    const nextLabel = document.getElementById('nextTypeLabel');
    if (nextLabel) nextLabel.textContent = TYPE_META[type].nextLabel;

    const detailTitle = document.getElementById('typeDetailTitle');
    const detailSub = document.getElementById('typeDetailSub');
    const detailIcon = document.getElementById('typeDetailIcon');
    if (detailTitle) detailTitle.textContent = TYPE_META[type].detailTitle;
    if (detailSub) detailSub.textContent = TYPE_META[type].detailSub;
    if (detailIcon) detailIcon.innerHTML = TYPE_META[type].iconSvg;

    ['student', 'faculty', 'staff', 'admin'].forEach((t) => {
      const block = document.getElementById('fields-' + t);
      if (block) block.style.display = t === type ? '' : 'none';
    });

    filterRoles(type);

    const summaryTypeEl = document.getElementById('summaryUserType');
    if (summaryTypeEl) summaryTypeEl.textContent = TYPE_META[type].label;

    const rvLabel = document.getElementById('rv-typegroup-label');
    if (rvLabel) rvLabel.textContent = TYPE_META[type].detailTitle;

    toggleHostelAdminCheckbox(type);

    const roleSelect = document.getElementById('id_role');
    if (roleSelect) {
        // Re-check when role changes
        roleSelect.dispatchEvent(new Event('change'));
    }

    refreshNextButtonStates();
    
  }

  // <-------------Blaze code start--------------->

  function toggleHostelAdminCheckbox(userType) {
      const wrapper = document.querySelector('.hostel-admin-wrapper');
      const checkbox = document.getElementById('id_is_hostel_admin');
      const roleSelect = document.getElementById('id_role');

     
      if (roleSelect) {
          roleSelect.addEventListener('change', function() {
              // Re-check hostel admin checkbox visibility
              toggleHostelAdminCheckbox(currentType);
              refreshNextButtonStates();
          });
      }
      
      if (!wrapper) return;
      
      
      const isStaffType = (userType === 'staff');
      const isStaffRole = roleSelect && roleSelect.value && 
                          roleSelect.options[roleSelect.selectedIndex]?.text?.toLowerCase().includes('staff');
      
      // Show if User Type is Staff OR Role is Staff
      const showCheckbox = isStaffType || isStaffRole;
      
      if (showCheckbox) {
          wrapper.style.display = 'block';
          wrapper.style.opacity = '1';
          wrapper.style.maxHeight = '150px';
          wrapper.style.marginTop = '12px';
          wrapper.style.padding = '4px 0';
      } else {
          wrapper.style.display = 'none';
          wrapper.style.opacity = '0';
          wrapper.style.maxHeight = '0';
          wrapper.style.marginTop = '0';
          wrapper.style.padding = '0';
          if (checkbox) {
              checkbox.checked = false;
          }
      }
  }


  // <-------------Blaze code end--------------->


  document.querySelectorAll('.up-type-card').forEach((card) => {
    card.addEventListener('click', () => selectUserType(card.dataset.type));
    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        selectUserType(card.dataset.type);
      }
    });
  });

  selectUserType('student');

  function filterRoles(type) {
    const roleSelect = document.getElementById('id_role');
    const roleHint = document.getElementById('roleHint');
    if (!roleSelect) return;

    let allRoles = [];
    try {
      allRoles = JSON.parse(document.getElementById('allRolesData').textContent);
    } catch (e) {}

    const filtered = allRoles.filter((r) => !r.type || r.type === type);
    roleSelect.innerHTML = '<option value="">Select Role</option>';
    filtered.forEach((r) => {
      const opt = document.createElement('option');
      opt.value = r.id;
      opt.textContent = r.name;
      roleSelect.appendChild(opt);
    });

    if (roleHint) roleHint.style.display = filtered.length === 0 ? 'block' : 'none';
  }

  function updateAvatarInitials() {
    const first = (document.getElementById('id_first_name') || {}).value || '';
    const last = (document.getElementById('id_last_name') || {}).value || '';
    const initials = ((first[0] || '') + (last[0] || '')).toUpperCase() || '?';
    const avatarInitialsEl = document.getElementById('avatarInitials');
    const summaryInitialsEl = document.getElementById('summaryInitials');
    if (avatarInitialsEl) avatarInitialsEl.textContent = initials;
    if (summaryInitialsEl) summaryInitialsEl.textContent = initials;
  }

  const photoInput = document.getElementById('id_profile_photo');
  if (photoInput) {
    photoInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (ev) => {
        ['avatarImg', 'summaryAvatarImg'].forEach((id) => {
          const img = document.getElementById(id);
          if (img) { img.src = ev.target.result; img.style.display = 'block'; }
        });
        ['avatarInitials', 'summaryInitials'].forEach((id) => {
          const el = document.getElementById(id);
          if (el) el.style.display = 'none';
        });
      };
      reader.readAsDataURL(file);
    });
  }

  function bindLive(inputId, summaryId, transform) {
    const input = document.getElementById(inputId);
    const output = document.getElementById(summaryId);
    if (!input || !output) return;
    const update = () => {
      output.textContent = transform ? transform(input.value) : (input.value || '—');
    };
    input.addEventListener('input', update);
    input.addEventListener('change', update);
  }

  function fullNameVal() {
    const f = (document.getElementById('id_first_name') || {}).value || '';
    const m = (document.getElementById('id_middle_name') || {}).value || '';
    const l = (document.getElementById('id_last_name') || {}).value || '';
    return [f, m, l].filter(Boolean).join(' ') || '—';
  }

  ['id_first_name', 'id_middle_name', 'id_last_name'].forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('input', () => {
        updateAvatarInitials();
        const nameEl = document.getElementById('summaryName');
        if (nameEl) nameEl.textContent = fullNameVal();
      });
    }
  });

  bindLive('id_username', 'summaryUsername');
  bindLive('id_email', 'summaryEmail');
  const universitySelect = document.getElementById("id_university");
  const summaryUnivId = document.getElementById("summaryUnivId");

  if (universitySelect && summaryUnivId) {

      function updateUniversitySummary() {

          const text =
              universitySelect.options[universitySelect.selectedIndex]?.text || "—";

          summaryUnivId.textContent = text;

      }

      universitySelect.addEventListener("change", updateUniversitySummary);

      updateUniversitySummary();
  }
  bindLive('id_mobile_number', 'summaryMobile');

  const statusSelect = document.getElementById('id_account_status');
  if (statusSelect) {
    statusSelect.addEventListener('change', () => {
      const summaryStatusEl = document.getElementById('summaryStatus');
      if (summaryStatusEl) summaryStatusEl.textContent = statusSelect.value || '—';
    });
  }


  function val(id) {
    const el = document.getElementById(id);
    if (!el) return '';
    if (el.tagName === 'SELECT') return el.options[el.selectedIndex]?.text || '';
    return el.value || '';
  }

  const REVIEW_FIELDS = {
    student: [
      { label: 'Student number', id: 'id_student_number' },
      { label: 'Preferred name', id: 'id_student_preferred_name' },
      { label: 'University email', id: 'id_university_email' },
      { label: 'Personal email', id: 'id_student_personal_email' },
      { label: 'Citizenship', id: 'id_citizenship_status' },
      { label: 'Marital status', id: 'id_marital_status' },
      { label: 'Academic level', id: 'id_academic_level' },
      { label: 'Current status', id: 'id_student_current_status' },
      { label: 'Admission date', id: 'id_admission_date' },
      { label: 'Expected graduation', id: 'id_expected_graduation_date' },
      { label: 'College', id: 'id_school' },
      { label: 'Department', id: 'id_department' },
      { label: 'Degree', id: 'id_degree' },
      { label: 'Program', id: 'id_program' },
      { label: 'Catalog year', id: 'id_catalog_year' },
    ],
    faculty: [
      { label: 'Employee ID', id: 'id_faculty_employee_id' },
      { label: 'Preferred name', id: 'id_faculty_preferred_name' },
      { label: 'Work email', id: 'id_faculty_email' },
      { label: 'Office phone', id: 'id_faculty_phone' },
      { label: 'Faculty rank', id: 'id_faculty_rank' },
      { label: 'College', id: 'id_faculty_school' },
      { label: 'Department', id: 'id_faculty_department_id' },
      { label: 'Hire date', id: 'id_faculty_hire_date' },
      { label: 'Employment status', id: 'id_faculty_employment_status' },
      { label: 'Office location', id: 'id_faculty_office_location' },
      { label: 'Biography', id: 'id_faculty_biography' },
      { label: 'Degree', id: 'id_faculty_degree' },
      { label: 'Field of study', id: 'id_faculty_field_of_study' },
      { label: 'Institution', id: 'id_faculty_institution_name' },
      { label: 'Graduation year', id: 'id_faculty_graduation_year' },
    ],
    staff: [
      { label: 'Employee ID', id: 'id_staff_employee_id' },
      { label: 'Preferred name', id: 'id_staff_preferred_name' },
      { label: 'Work email', id: 'id_staff_work_email' },
      { label: 'Personal email', id: 'id_staff_personal_email' },
      { label: 'Office phone', id: 'id_staff_office_phone' },
      { label: 'Employment type', id: 'id_staff_employment_type' },
      { label: 'Employment status', id: 'id_staff_employment_status' },
      { label: 'Hire date', id: 'id_staff_hire_date' },
      { label: 'Job title', id: 'id_staff_job_title' },
      { label: 'College', id: 'id_staff_school' },
      { label: 'Department', id: 'id_staff_department_id' },
      { label: 'Unit ID', id: 'id_staff_unit_id' },
      { label: 'Position start', id: 'id_staff_position_start_date' },
      { label: 'Position status', id: 'id_staff_position_status' },
      { label: 'Degree', id: 'id_staff_degree' },
      { label: 'Institution', id: 'id_staff_institution_name' },
    ],
    admin: [
      { label: 'Employee ID', id: 'id_admin_employee_id' },
      { label: 'Work email', id: 'id_admin_work_email' },
      { label: 'Admin scope', id: 'id_admin_scope' },
      { label: 'Notes', id: 'id_admin_notes' },
    ],
  };

  function buildExtraReviewBlocks(type) {
    if (type === 'student') {
      const addrParts = [
        val('id_student_address_line_1'),
        val('id_student_address_line_2'),
        val('id_student_city'),
        val('id_student_state'),
        val('id_student_postal_code'),
        val('id_student_country'),
      ].filter(Boolean);
      const addressSummary = addrParts.length ? addrParts.join(', ') : '—';

      const emergencyName = val('id_student_emergency_name');
      const emergencySummary = emergencyName
        ? `${emergencyName} (${val('id_student_emergency_relationship') || 'relationship not set'}) — ${val('id_student_emergency_phone') || 'no phone'}`
        : '—';

      const docFileInputs = document.querySelectorAll('input[name="student_doc_file[]"]');
      let docCount = 0;
      docFileInputs.forEach((inp) => { if (inp.files && inp.files.length) docCount += 1; });

      return [
        { label: 'Address', value: addressSummary },
        { label: 'Emergency contact', value: emergencySummary },
        { label: 'Documents attached', value: docCount > 0 ? `${docCount} file(s)` : 'None attached' },
      ];
    }

    if (type === 'staff') {
      const addrParts = [
        val('id_staff_address_line_1'),
        val('id_staff_address_line_2'),
        val('id_staff_city'),
        val('id_staff_state'),
        val('id_staff_postal_code'),
        val('id_staff_country'),
      ].filter(Boolean);
      const addressSummary = addrParts.length ? addrParts.join(', ') : '—';

      const emergencyName = val('id_staff_emergency_name');
      const emergencySummary = emergencyName
        ? `${emergencyName} (${val('id_staff_emergency_relationship') || 'relationship not set'}) — ${val('id_staff_emergency_phone') || 'no phone'}`
        : '—';

      const certNameInputs = document.querySelectorAll('input[name="staff_cert_name[]"]');
      let certCount = 0;
      certNameInputs.forEach((inp) => { if (inp.value.trim()) certCount += 1; });

      const docFileInputs = document.querySelectorAll('input[name="staff_doc_file[]"]');
      let docCount = 0;
      docFileInputs.forEach((inp) => { if (inp.files && inp.files.length) docCount += 1; });

      return [
        { label: 'Address', value: addressSummary },
        { label: 'Emergency contact', value: emergencySummary },
        { label: 'Certifications', value: certCount > 0 ? `${certCount} added` : 'None added' },
        { label: 'Documents attached', value: docCount > 0 ? `${docCount} file(s)` : 'None attached' },
      ];
    }

    if (type === 'faculty') {
      const docFileInputs = document.querySelectorAll('input[name="faculty_doc_file[]"]');
      let docCount = 0;
      docFileInputs.forEach((inp) => { if (inp.files && inp.files.length) docCount += 1; });

      return [
        { label: 'Documents attached', value: docCount > 0 ? `${docCount} file(s)` : 'None attached' },
      ];
    }

    return [];
  }

  function populateReview() {
    setText('rv-usertype', TYPE_META[currentType]?.label || '—');
    setText('rv-role', val('id_role') || '—');
    setText('rv-status', val('id_account_status') || '—');

    const f = val('id_first_name'), m = val('id_middle_name'), l = val('id_last_name');
    setText('rv-fullname', [f, m, l].filter(Boolean).join(' ') || '—');
    setText('rv-username', val('id_username') || '—');
    setText('rv-ssn-number', val('id_ssn_number') || '—');
    setText('rv-email', val('id_email') || '—');
    setText('rv-univid',val('id_university') || 'Not assigned');
    setText('rv-mobile', val('id_mobile_number') || '—');
    setText('rv-dob', val('id_date_of_birth') || '—');
    setText('rv-gender', val('id_gender') || '—');

    const firearmYes = isFirearmYes();
    setText('rv-firearm', firearmYes ? 'Yes' : 'No');
    const firearmRow = document.getElementById('rv-firearm-details-row');
    if (firearmRow) firearmRow.style.display = firearmYes ? '' : 'none';
    if (firearmYes) {
      setText('rv-firearm-name', val('id_firearm_firearm_name') || '—');
      setText('rv-firearm-type', val('id_firearm_firearm_type') || '—');
      setText('rv-firearm-serial', val('id_firearm_serial_number') || '—');
    }

    const typeFields = REVIEW_FIELDS[currentType] || [];
    const extraBlocks = buildExtraReviewBlocks(currentType);
    const container = document.getElementById('rv-typefields');

    if (container) {
      const fieldRows = typeFields
        .map((field) => {
          const v = val(field.id) || '—';
          return `<div class="up-review-row">
            <span class="up-review-label">${field.label}</span>
            <span class="up-review-val">${escapeHtml(v)}</span>
          </div>`;
        })
        .join('');

      const extraRows = extraBlocks
        .map((block) => `<div class="up-review-row">
            <span class="up-review-label">${block.label}</span>
            <span class="up-review-val">${escapeHtml(block.value)}</span>
          </div>`)
        .join('');

      container.innerHTML = fieldRows + extraRows;
    }
  }

  function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  const REQUIRED_CORE_FIELDS = [
    { id: 'id_username', label: 'Username', section: 'identity' },
    { id: 'id_email', label: 'Email', section: 'identity' },
    { id: 'id_first_name', label: 'First name', section: 'identity' },
    { id: 'id_last_name', label: 'Last name', section: 'identity' },
    { id: 'id_mobile_number', label: 'Mobile number', section: 'identity' },
    { id: 'id_confirm_mobile', label: 'Confirm mobile', section: 'identity' },
    { id: 'id_ssn_number', label: 'SSN Number', section: 'identity' },
  ];

    const FIREARM_CORE_FIELDS = [
    { id: 'id_firearm_firearm_name', label: 'Firearm name', section: 'identity' },
    { id: 'id_firearm_firearm_type', label: 'Firearm type', section: 'identity' },
    { id: 'id_firearm_serial_number', label: 'Firearm serial number', section: 'identity' },
  ];


  const userForm = document.getElementById('userForm');
  if (userForm) {
    userForm.addEventListener('submit', (e) => {
      const missing = [];

      REQUIRED_CORE_FIELDS.forEach((f) => {
        const el = document.getElementById(f.id);
        if (el && !el.value.trim()) missing.push(f);
      });

      if (isFirearmYes()) {
        FIREARM_CORE_FIELDS.forEach((f) => {
          const el = document.getElementById(f.id);
          if (el && !el.value.trim()) missing.push(f);
        });
      }

      const mobile = document.getElementById('id_mobile_number');
      const confirmMobile = document.getElementById('id_confirm_mobile');
      if (mobile && confirmMobile && mobile.value.trim() &&
          mobile.value.trim() !== confirmMobile.value.trim()) {
        missing.push({ id: 'id_confirm_mobile', label: 'Mobile numbers do not match', section: 'identity' });
      }

      if (missing.length) {
        e.preventDefault();
        showSection(missing[0].section);
        const el = document.getElementById(missing[0].id);
        if (el) el.focus();
        alert('Please fix: ' + missing.map((m) => m.label).join(', '));
      }
    });
  }


  const editMode = document.getElementById('editMode');
  const updateBtn = document.getElementById('updateBtn');

  if (editMode && editMode.value === 'true' && updateBtn) {
    updateBtn.addEventListener('click', async () => {
      const userId = document.getElementById('editUserId').value;
      const form = document.getElementById('userForm');
      const formData = new FormData(form);

      updateBtn.disabled = true;
      updateBtn.textContent = 'Saving…';

      try {
        const res = await fetch(`/users/${userId}/update/`, {
          method: 'POST',
          body: formData,
          headers: { 'X-CSRFToken': getCookie('csrftoken') },
        });
        const data = await res.json();
        if (data.ok) {
          sessionStorage.setItem('ub_toast', JSON.stringify({ type: 'success', message: 'User updated successfully.' }));
          window.location.href = '/users/';
        } else {
          alert('Validation errors:\n' + JSON.stringify(data.errors, null, 2));
          updateBtn.disabled = false;
          updateBtn.textContent = 'Update User';
        }
      } catch (err) {
        console.error(err);
        updateBtn.disabled = false;
        updateBtn.textContent = 'Update User';
      }
    });
  }

  document.querySelectorAll('.up-copy-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      navigator.clipboard.writeText(btn.dataset.copy || '').then(() => {
        const orig = btn.innerHTML;
        btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>';
        setTimeout(() => { btn.innerHTML = orig; }, 1500);
      });
    });
  });

  const togglePass = document.getElementById('togglePass');
  if (togglePass) {
    togglePass.addEventListener('click', () => {
      const mask = document.querySelector('.up-pass-mask');
      const text = document.querySelector('.up-pass-text');
      if (!mask || !text) return;
      const showing = text.style.display !== 'none';
      mask.style.display = showing ? '' : 'none';
      text.style.display = showing ? 'none' : '';
    });
  }

  const successModal = document.getElementById('successModal');
  if (successModal) {
    const redirectUrl = successModal.dataset.redirectUrl;

    function goToUserPage() {
      if (redirectUrl) window.location.href = redirectUrl;
    }

    const modalCloseBtn = document.getElementById('modalCloseBtn');
    if (modalCloseBtn) {
      modalCloseBtn.addEventListener('click', goToUserPage);
    }

    successModal.addEventListener('click', (e) => {
      if (e.target === successModal) {
        goToUserPage();
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') goToUserPage();
    });
  }

  function getCookie(name) {
    const val = `; ${document.cookie}`;
    const parts = val.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  }

  document.querySelectorAll('.up-accordion__hd').forEach((hd) => {
    hd.addEventListener('click', () => {
      const acc = hd.closest('.up-accordion');
      const body = acc.querySelector('.up-accordion__bd');
      const isOpen = acc.classList.contains('up-accordion--open');

      acc.classList.toggle('up-accordion--open', !isOpen);
      if (body) body.style.display = isOpen ? 'none' : '';
    });
  });

  let docRowCounters = { student: 1, faculty: 1, staff: 1 };
  let certRowCounter = 1;

  function cloneAndClear(sourceEl, newId) {
    const clone = sourceEl.cloneNode(true);
    clone.id = newId;
    clone.querySelectorAll('input, select, textarea').forEach((el) => {
      if (el.type === 'file') {
        el.value = '';
      } else if (el.tagName === 'SELECT') {
        el.selectedIndex = 0;
      } else {
        el.value = '';
      }
    });
    return clone;
  }

  function addRemoveButton(rowEl, onRemove) {
    if (rowEl.querySelector('.up-remove-row-btn')) return;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'up-remove-row-btn';
    btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg> Remove`;
    btn.addEventListener('click', onRemove);
    rowEl.appendChild(btn);
  }

  window.addDocRow = function (type) {
    const lastRow = document.getElementById(`${type}-doc-${docRowCounters[type] - 1}`);
    if (!lastRow) return;
    const newId = `${type}-doc-${docRowCounters[type]}`;
    const clone = cloneAndClear(lastRow, newId);
    addRemoveButton(clone, () => clone.remove());
    lastRow.insertAdjacentElement('afterend', clone);
    docRowCounters[type] += 1;
  };

  window.addCertRow = function () {
    const lastRow = document.getElementById(`staff-cert-${certRowCounter - 1}`);
    if (!lastRow) return;
    const newId = `staff-cert-${certRowCounter}`;
    const clone = cloneAndClear(lastRow, newId);
    addRemoveButton(clone, () => clone.remove());
    lastRow.insertAdjacentElement('afterend', clone);
    wireAllDateOnlyFields(clone);   
    certRowCounter += 1;
  };

  const AUTO_ID_CONFIG = {
    student: {
      inputId: 'id_student_number',
      suggestedId: 'suggestedStudentNumber',
      dateFieldId: 'id_admission_date',
      endpoint: '/dashboard/users/next-student-number/',
      responseKey: 'student_number',
    },
    faculty: {
      inputId: 'id_faculty_employee_id',
      suggestedId: 'suggestedFacultyId',
      dateFieldId: 'id_faculty_hire_date',
      endpoint: '/dashboard/users/next-faculty-id/',
      responseKey: 'employee_id',
    },
    staff: {
      inputId: 'id_staff_employee_id',
      suggestedId: 'suggestedStaffId',
      dateFieldId: 'id_staff_hire_date',
      endpoint: '/dashboard/users/next-staff-id/',
      responseKey: 'employee_id',
    },
  };

  const autoIdTouchedByUser = { student: false, faculty: false, staff: false };

  function initAutoId(type) {
    const cfg = AUTO_ID_CONFIG[type];
    const input = document.getElementById(cfg.inputId);
    const suggestedEl = document.getElementById(cfg.suggestedId);
    if (!input) return;

    if (suggestedEl && suggestedEl.value && !input.value) {
      input.value = suggestedEl.value;
    }

    input.addEventListener('input', () => {
      autoIdTouchedByUser[type] = true;
    });

    const dateInput = document.getElementById(cfg.dateFieldId);
    if (dateInput) {
      dateInput.addEventListener('change', () => {
        if (autoIdTouchedByUser[type]) return;
        const year = dateInput.value ? dateInput.value.slice(0, 4) : '';
        fetchNextAutoId(type, year);
      });
    }
  }

  function fetchNextAutoId(type, year) {
    const cfg = AUTO_ID_CONFIG[type];
    const input = document.getElementById(cfg.inputId);
    if (!input) return;

    const params = new URLSearchParams();
    if (year) params.set('year', year);
    if (type === 'student') {
      const program = document.getElementById('id_program');
      if (program && program.value) params.set('program', program.value);
    }
    const qs = params.toString();
    const url = qs ? `${cfg.endpoint}?${qs}` : cfg.endpoint;

    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && data[cfg.responseKey] && !autoIdTouchedByUser[type]) {
          input.value = data[cfg.responseKey];
        }
      })
      .catch(() => { });
  }

  function initAllAutoIds() {
    Object.keys(AUTO_ID_CONFIG).forEach((type) => initAutoId(type));
  }


  function normalizePhone(v) {
    return (v || '').replace(/\D/g, '');
  }

  function isValidPhone(value) {
    if (!value) return false;
    const trimmed = value.trim();
    if (!/^\+?[\d\s\-()]+$/.test(trimmed)) return false;

    const digits = normalizePhone(trimmed);

    if (/^91?[6-9]\d{9}$/.test(digits) && (digits.length === 10 || digits.length === 12)) {
      return true;
    }

    return /^[1-9]\d{6,14}$/.test(digits);
  }

  const PHONE_FIELD_IDS = ['id_mobile_number', 'id_confirm_mobile'];

  PHONE_FIELD_IDS.forEach((id) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.setAttribute('maxlength', '17');
    el.setAttribute('inputmode', 'tel');
    el.addEventListener('input', () => {
      const cursorFromEnd = el.value.length - el.selectionStart;
      el.value = el.value.replace(/[^\d\s+\-()]/g, '').slice(0, 17);
      const pos = Math.max(0, el.value.length - cursorFromEnd);
      el.setSelectionRange(pos, pos);
    });
  });

  function isFieldFilledAndValid(el) {
  if (!el) return true;
  if (el.type === 'checkbox' || el.type === 'radio') return el.checked;
  if (typeof el.checkValidity === 'function' && !el.checkValidity()) return false;
  return el.value.trim() !== '';
}

function sectionComplete(sectionName) {
  if (sectionName === 'role') {
    return ROLE_REQUIRED_IDS.every((id) => isFieldFilledAndValid(document.getElementById(id)));
  }

  if (sectionName === 'identity') {
    const requiredIds = IDENTITY_REQUIRED_IDS.concat(isFirearmYes() ? FIREARM_REQUIRED_IDS : []);
    // const allFilled = IDENTITY_REQUIRED_IDS.every((id) => isFieldFilledAndValid(document.getElementById(id)));
     const allFilled = requiredIds.every((id) => isFieldFilledAndValid(document.getElementById(id)));
//     let allFilled = true;
//     requiredIds.forEach((id) => {
//     const el = document.getElementById(id);

//     const ok = isFieldFilledAndValid(el);

//     console.log(id, ok, el ? el.value : "NOT FOUND");

//     if (!ok) {
//         allFilled = false;
//     }
// });
    const mobile = document.getElementById('id_mobile_number');
    const confirm = document.getElementById('id_confirm_mobile');
    const phoneValid = mobile && isValidPhone(mobile.value.trim());
    const phonesMatch = mobile && confirm && normalizePhone(mobile.value) === normalizePhone(confirm.value);
    // const noVisibleErrors = !document.querySelector('#sec-identity .up-field--error');
    const visibleErrors = [
        ...document.querySelectorAll('#sec-identity .up-field--error')
    ].filter(field => {

        // Ignore firearm errors when Firearm = No
        if (
            !isFirearmYes() &&
            field.closest('#firearmDetailsSection')
        ) {
            return false;
        }

        return true;
    });

    const noVisibleErrors = visibleErrors.length === 0;
    return allFilled && phoneValid && phonesMatch && noVisibleErrors;
  }

  if (sectionName === 'typedetails') {
    const ids = TYPEDETAILS_REQUIRED_IDS[currentType] || [];
    return ids.every((id) => isFieldFilledAndValid(document.getElementById(id)));
  }

  return true;
}

function setNextButtonEnabled(targetSection, enabled) {
  const btn = document.querySelector(`[data-next="${targetSection}"]`);
  if (btn) btn.disabled = !enabled;
}

function refreshNextButtonStates() {
  setNextButtonEnabled('identity', sectionComplete('role'));
  setNextButtonEnabled('typedetails', sectionComplete('identity'));
  setNextButtonEnabled('review', sectionComplete('typedetails'));
}


// function refreshNextButtonStates() {

//     const identityComplete = sectionComplete("identity");

//     console.log("identityComplete =", identityComplete);

//     const btn = document.querySelector('[data-next="typedetails"]');

//     console.log(btn);

//     btn.disabled = !identityComplete;

//     console.log("after =", btn.disabled);
// }


  function restoreStateAfterServerReload() {
    const userTypeInput = document.getElementById('id_user_type');
    const postedType = userTypeInput && userTypeInput.value ? userTypeInput.value : 'student';
    selectUserType(postedType);

    toggleHostelAdminCheckbox(postedType);

    const erroredField = document.querySelector('.up-field--error input, .up-field--error select, .up-field--error textarea');
    if (erroredField) {
      const section = erroredField.closest('.up-section');
      if (section && section.dataset.section) {
        showSection(section.dataset.section);
        erroredField.focus();
        return;
      }
    }

    const nonFieldAlert = document.querySelector('.up-alert--error');
    if (nonFieldAlert) {
      showSection('identity');
      return;
    }

    showSection('role');
  }

  restoreStateAfterServerReload();
  updateAvatarInitials();
  initAllAutoIds();
  toggleFirearmSection();  
  refreshNextButtonStates();

const liveForm = document.getElementById('userForm');
if (liveForm) {
  liveForm.addEventListener('input', refreshNextButtonStates);
  liveForm.addEventListener('change', refreshNextButtonStates);
}

/* ==========================================
   Make ALL date fields "pick only" — calendar opens
   on click/focus, manual typing is blocked. Works for
   every date input currently on the page, and any date
   inputs added later (e.g. cloned certification rows)
   via wireAllDateOnlyFields(container).
========================================== */
function wireDateOnlyField(input) {
  if (!input || input.dataset.pickOnlyWired === '1') return;
  input.dataset.pickOnlyWired = '1';

  function openCalendar() {
    if (typeof input.showPicker === 'function') {
      try { input.showPicker(); } catch (e) {}
    }
  }

  input.addEventListener('keydown', function (e) {
    const allowedKeys = ['Tab', 'Escape'];
    if (!allowedKeys.includes(e.key)) {
      e.preventDefault();
    }
  });

  input.addEventListener('paste', (e) => e.preventDefault());
  input.addEventListener('click', openCalendar);
  input.addEventListener('focus', openCalendar);
}

function wireAllDateOnlyFields(root) {
  const scope = root || document;
  scope.querySelectorAll('input[type="date"]').forEach(wireDateOnlyField);
}

const dobInput = document.getElementById("id_date_of_birth");
if (dobInput) {
  dobInput.max = new Date().toISOString().split("T")[0];
}

wireAllDateOnlyFields(document);

/* ==========================================
   Generic College -> Department cascade wiring.
   Reused for: Student (school/department — existing),
   Faculty (faculty_school/faculty_department_id — new),
   Staff (staff_school/staff_department_id — new).
========================================== */
function wireCollegeDepartmentCascade(collegeSelectId, departmentSelectId) {
  const collegeSelect = document.getElementById(collegeSelectId);
  const departmentSelect = document.getElementById(departmentSelectId);
  if (!collegeSelect || !departmentSelect) return;

  collegeSelect.addEventListener("change", function () {
    departmentSelect.innerHTML = '<option value="">Loading...</option>';

    if (!this.value) {
      departmentSelect.innerHTML = '<option value="">Select Department</option>';
      return;
    }

    fetch(`/dashboard/ajax/get-departments/?school_id=${this.value}`)
      .then(res => res.json())
      .then(data => {
        departmentSelect.innerHTML = '<option value="">Select Department</option>';
        data.forEach(item => {
          departmentSelect.innerHTML += `
            <option value="${item.id}">
                ${item.name}
            </option>
          `;
        });
      })
      .catch(() => {
        departmentSelect.innerHTML = '<option value="">Select Department</option>';
      });
  });
}

const university = document.getElementById("id_university");
const school = document.getElementById("id_school");

const COLLEGE_SELECT_IDS = ["id_school", "id_faculty_school", "id_staff_school"];

function populateCollegeSelects(universityId) {
  const selects = COLLEGE_SELECT_IDS
    .map((id) => document.getElementById(id))
    .filter(Boolean);

  if (!selects.length) return;

  selects.forEach((sel) => {
    sel.innerHTML = '<option value="">Select College</option>';
  });

  if (!universityId) return;

  fetch(`/dashboard/ajax/get-schools/?university_id=${universityId}`)
    .then((res) => res.json())
    .then((data) => {
      selects.forEach((sel) => {
        data.forEach((item) => {
          sel.innerHTML += `
            <option value="${item.id}">
                ${item.name}
            </option>
          `;
        });
      });
    })
    .catch(() => {});
}

if (university) {
  university.addEventListener("change", function () {
    populateCollegeSelects(this.value);
  });

  if (university.value) {
    populateCollegeSelects(university.value);
  }
}

const department = document.getElementById("id_department");

if (school && department) {
  wireCollegeDepartmentCascade("id_school", "id_department");
}

const degree = document.getElementById("id_degree");

if (department && degree) {

    department.addEventListener("change", function () {

        degree.innerHTML =
            '<option value="">Loading...</option>';

        fetch(`/dashboard/ajax/get-degrees/`)

            .then(res => res.json())

            .then(data => {

                degree.innerHTML =
                    '<option value="">Select Degree</option>';

                data.forEach(item => {

                    degree.innerHTML += `
                        <option value="${item.id}">
                            ${item.name}
                        </option>
                    `;

                });

            });

    });

}

const program = document.getElementById("id_program");

if (degree && program) {

    degree.addEventListener("change", function () {

        program.innerHTML =
            '<option value="">Loading...</option>';

        fetch(
            `/dashboard/ajax/get-programs/?department_id=${department.value}&degree_id=${degree.value}`
        )

            .then(res => res.json())

            .then(data => {

                program.innerHTML =
                    '<option value="">Select Program</option>';

                data.forEach(item => {

                    program.innerHTML += `
                        <option value="${item.id}">
                            ${item.name}
                        </option>
                    `;

                });

            });

    });

}


const studentDepartment = document.getElementById("id_department");

if (studentDepartment) {

    studentDepartment.addEventListener("change", function () {

        if (currentType !== "student") return;

        if (autoIdTouchedByUser.student) return;

        const admissionDate = document.getElementById("id_admission_date");

        const year = admissionDate && admissionDate.value
            ? admissionDate.value.slice(0, 4)
            : "";
        fetchNextAutoId("student", year);
    });

}

const studentProgram = document.getElementById("id_program");

if (studentProgram) {

    studentProgram.addEventListener("change", function () {

        if (currentType !== "student") return;

        if (autoIdTouchedByUser.student) return;

        const admissionDate = document.getElementById("id_admission_date");

        const year = admissionDate && admissionDate.value
            ? admissionDate.value.slice(0, 4)
            : "";

        fetchNextAutoId("student", year);
    });

}


const citizenship = document.getElementById("id_citizenship_status");
const countryField = document.getElementById("countryField");

function toggleCountryField() {

    if (!citizenship) return;

    if (
        citizenship.value === "INTERNATIONAL" ||
        citizenship.value === "PERMANENT_RESIDENT"
    ) {
        countryField.style.display = "block";
    } else {
        countryField.style.display = "none";
        document.getElementById("id_country_of_citizenship").value = "";
    }
}

citizenship.addEventListener("change", toggleCountryField);
toggleCountryField();


wireCollegeDepartmentCascade("id_faculty_school", "id_faculty_department_id");

/* NEW: Staff college -> department cascade. Department is optional for staff —
   admin/office roles use the Unit ID field instead. */
wireCollegeDepartmentCascade("id_staff_school", "id_staff_department_id");


/* ==========================================
   Student - Add Another Address
========================================== */

const addressContainer = document.getElementById("studentAddressContainer");
const addAddressBtn = document.getElementById("addStudentAddress");

if (addressContainer && addAddressBtn) {

    addAddressBtn.addEventListener("click", function () {

        const firstAddress = addressContainer.querySelector(".student-address-item");

        if (!firstAddress) return;

        const clone = firstAddress.cloneNode(true);

        clone.querySelectorAll("input").forEach(input => {
            input.value = "";
        });

        clone.querySelectorAll("select").forEach(select => {
            select.selectedIndex = 0;
        });

        const removeBtn = clone.querySelector(".remove-address");
        if (removeBtn) {
            removeBtn.style.display = "inline-flex";
        }

        addressContainer.appendChild(clone);
    });

    addressContainer.addEventListener("click", function (e) {

        if (e.target.classList.contains("remove-address")) {

            const blocks = addressContainer.querySelectorAll(".student-address-item");

            if (blocks.length > 1) {
                e.target.closest(".student-address-item").remove();
            }
        }
    });

}


const staffAddressContainer = document.getElementById("staffAddressContainer");
const addStaffAddressBtn = document.getElementById("addStaffAddress");

if (staffAddressContainer && addStaffAddressBtn) {

    addStaffAddressBtn.addEventListener("click", function () {

        const firstAddress = staffAddressContainer.querySelector(".staff-address-item");

        if (!firstAddress) return;

        const clone = firstAddress.cloneNode(true);

        clone.querySelectorAll("input").forEach(input => {
            input.value = "";
        });

        clone.querySelectorAll("select").forEach(select => {
            select.selectedIndex = 0;
        });

        const removeBtn = clone.querySelector(".remove-staff-address");
        if (removeBtn) {
            removeBtn.style.display = "inline-flex";
        }

        staffAddressContainer.appendChild(clone);
    });

    staffAddressContainer.addEventListener("click", function (e) {

        if (e.target.classList.contains("remove-staff-address")) {

            const blocks = staffAddressContainer.querySelectorAll(".staff-address-item");

            if (blocks.length > 1) {
                e.target.closest(".staff-address-item").remove();
            }
        }
    });

}

const documentContainer = document.getElementById("studentDocumentContainer");

document.addEventListener("click", function (e) {

    if (e.target.id === "addStudentDocument") {

        const first = documentContainer.querySelector(".up-doc-entry");

        const clone = first.cloneNode(true);

        clone.querySelectorAll("input").forEach(i => {
            if (i.type !== "button") {
                i.value = "";
            }
        });

        clone.querySelectorAll("select").forEach(s => {
            s.selectedIndex = 0;
        });

        documentContainer.appendChild(clone);
    }

    if (e.target.classList.contains("remove-document")) {

        if (documentContainer.querySelectorAll(".up-doc-entry").length > 1) {
            e.target.closest(".up-doc-entry").remove();
        } else {
            alert("At least one document is required.");
        }

    }

});

})();



/* ***************************************************** Arun code *************************************************** */