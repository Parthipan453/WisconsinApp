(function() {
  "use strict";

  const API_BASE = "/dashboard/medical_reports/api";
  const PAGE_SIZE = 10;

  const page = document.querySelector('.mr-page');
  if (!page) return;

  const els = {
    back: page.querySelector('#mrBack'),
    breadcrumb: page.querySelector('#mrBreadcrumb'),
    viewCategories: page.querySelector('#viewCategories'),
    viewReports: page.querySelector('#viewReports'),
    viewData: page.querySelector('#viewData'),
    categoryGrid: page.querySelector('#categoryGrid'),
    reportList: page.querySelector('#reportList'),
    dataFilters: page.querySelector('#dataFilters'),
    tableWrap: page.querySelector('#tableWrap'),
    tableHead: page.querySelector('#dataTableHead'),
    tableBody: page.querySelector('#dataTableBody'),
    emptyTable: page.querySelector('#emptyTable'),
    dataLoading: page.querySelector('#dataLoading'),
    exportBar: page.querySelector('#exportBar'),
    exportCount: page.querySelector('#exportCount'),
    totalReports: page.querySelector('#totalReports'),
    totalCategories: page.querySelector('#totalCategories'),
    totalRecords: page.querySelector('#totalRecords'),
    filteredCount: page.querySelector('#filteredCount'),
    paginationWrap: page.querySelector('#paginationWrap'),
    paginationInfo: page.querySelector('#paginationInfo'),
    paginationControls: page.querySelector('#paginationControls'),
  };

  const state = {
    view: 'categories',
    categories: [],
    activeCategory: null,
    activeReport: null,
    rows: [],
    columns: [],
    activeFilters: {},
    searchTerm: '',
    slimInstances: [],
    datePicker: null,
    currentPage: 1,
    totalPages: 1,
    filteredRows: [],
    reportFields: null,
  };

  function getDynamicCategories() {
    return [
      {
        key: 'patient',
        label: 'Patients',
        icon: 'ti-id-badge-2',
        desc: 'Patient profiles & registration',
        reports: [
          { key: 'patient-profile-list', name: 'Patient Profiles', desc: 'Complete patient directory with all types', icon: 'ti-users' },
          { key: 'patient-registry-list', name: 'Patient Registry', desc: 'Linked patient records by type', icon: 'ti-address-book' },
        ]
      },
      {
        key: 'clinical',
        label: 'Clinical',
        icon: 'ti-stethoscope',
        desc: 'Appointments, visits & consultations',
        reports: [
          { key: 'appointment-list', name: 'Appointments', desc: 'All medical appointments with status', icon: 'ti-calendar-event' },
          { key: 'medical-visit-list', name: 'Medical Visits', desc: 'Patient consultations & follow-ups', icon: 'ti-clipboard-heart' },
          { key: 'patient-registration-list', name: 'Patient Registrations', desc: 'Walk-in & appointment registrations', icon: 'ti-file-invoice' },
        ]
      },
      {
        key: 'sports',
        label: 'Sports Medicine',
        icon: 'ti-run',
        desc: 'Athletes, injuries & clearance',
        reports: [
          { key: 'athlete-medical-profile-list', name: 'Athlete Medical Profiles', desc: 'Athlete health & fitness records', icon: 'ti-shield-check' },
          { key: 'injury-record-list', name: 'Injury Records', desc: 'Athlete injuries & recovery status', icon: 'ti-heart-bolt' },
        ]
      },
      {
        key: 'lab',
        label: 'Lab & Tests',
        icon: 'ti-flask',
        desc: 'Laboratory tests & results',
        reports: [
          { key: 'laboratory-test-list', name: 'Laboratory Tests', desc: 'Test requests, results & status', icon: 'ti-microscope' },
        ]
      },
      {
        key: 'staff',
        label: 'Medical Staff',
        icon: 'ti-users-group',
        desc: 'Staff, shifts & leaves',
        reports: [
          { key: 'medical-staff-profile-list', name: 'Medical Staff', desc: 'Staff profiles & roles', icon: 'ti-id-badge' },
          { key: 'shift-list', name: 'Shift Management', desc: 'Shift schedules & assignments', icon: 'ti-clock' },
          { key: 'medical-staff-leave-list', name: 'Staff Leaves', desc: 'Leave applications & approvals', icon: 'ti-calendar-x' },
        ]
      },
      {
        key: 'admin',
        label: 'Facilities & Admin',
        icon: 'ti-building-hospital',
        desc: 'Hospitals, departments & services',
        reports: [
          { key: 'medical-center-list', name: 'Medical Centers', desc: 'Hospitals & facility details', icon: 'ti-building' },
          { key: 'medical-department-list', name: 'Departments', desc: 'Department directory & services', icon: 'ti-building-arch' },
          { key: 'health-camp-list', name: 'Health Camps', desc: 'Health camp management & registry', icon: 'ti-campfire' },
        ]
      }
    ];
  }


  function getReportFields(reportKey) {
    const fieldMaps = {
      'patient-profile-list': {
        model: 'PatientProfile',
        fields: ['patient_number', 'patient_name', 'patient_type', 'blood_group', 'allergies', 'chronic_conditions', 'created_at'],
        labels: {
          patient_number: 'Patient ID',
          patient_name: 'Patient Name',
          patient_type: 'Type',
          blood_group: 'Blood Group',
          allergies: 'Allergies',
          chronic_conditions: 'Chronic Conditions',
          created_at: 'Registered On'
        },
        filters: ['patient_type', 'blood_group'],
        dateField: 'created_at'
      },
      'patient-registry-list': {
        model: 'PatientRegistry',
        fields: ['patient_number', 'patient_type', 'registration_date'],
        labels: {
          patient_number: 'Registry ID',
          patient_type: 'Type',
          registration_date: 'Registration Date'
        },
        filters: ['patient_type'],
        dateField: 'registration_date'
      },
      'appointment-list': {
        model: 'Appointment',
        fields: ['appointment_number', 'patient', 'medical_staff', 'hospital', 'appointment_date', 'appointment_time', 'priority', 'status', 'service', 'reason'],
        labels: {
          appointment_number: 'Appointment #',
          patient: 'Patient',
          medical_staff: 'Doctor / Staff',
          hospital: 'Hospital',
          appointment_date: 'Date',
          appointment_time: 'Time',
          priority: 'Priority',
          status: 'Status',
          service: 'Service',
          reason: 'Reason'
        },
        filters: ['priority', 'status'],
        dateField: 'appointment_date'
      },
      'medical-visit-list': {
        model: 'MedicalVisit',
        fields: ['visit_number', 'patient', 'attending_staff', 'department', 'visit_date', 'visit_time', 'visit_type', 'visit_status', 'chief_complaint'],
        labels: {
          visit_number: 'Visit #',
          patient: 'Patient',
          attending_staff: 'Attending Staff',
          department: 'Department',
          visit_date: 'Date',
          visit_time: 'Time',
          visit_type: 'Type',
          visit_status: 'Status',
          chief_complaint: 'Chief Complaint'
        },
        filters: ['visit_type', 'visit_status'],
        dateField: 'visit_date'
      },
      'patient-registration-list': {
        model: 'PatientRegistration',
        fields: ['registration_number', 'patient', 'registration_date', 'registration_time', 'registration_type', 'status', 'token_number', 'chief_complaint'],
        labels: {
          registration_number: 'Registration #',
          patient: 'Patient',
          registration_date: 'Date',
          registration_time: 'Time',
          registration_type: 'Type',
          status: 'Status',
          token_number: 'Token #',
          chief_complaint: 'Chief Complaint'
        },
        filters: ['registration_type', 'status'],
        dateField: 'registration_date'
      },
      'athlete-medical-profile-list': {
        model: 'AthleteMedicalProfile',
        fields: ['athlete_medical_id', 'athlete', 'medical_clearance_status', 'fitness_level', 'injury_risk', 'clearance_date', 'next_medical_checkup'],
        labels: {
          athlete_medical_id: 'Athlete ID',
          athlete: 'Athlete',
          medical_clearance_status: 'Clearance',
          fitness_level: 'Fitness',
          injury_risk: 'Injury Risk',
          clearance_date: 'Clearance Date',
          next_medical_checkup: 'Next Checkup'
        },
        filters: ['medical_clearance_status', 'fitness_level', 'injury_risk'],
        dateField: 'next_medical_checkup'
      },
      'injury-record-list': {
        model: 'InjuryRecord',
        fields: ['injury_title', 'medical_profile', 'body_part', 'severity', 'injury_date', 'injury_status', 'estimated_recovery_days'],
        labels: {
          injury_title: 'Injury',
          medical_profile: 'Athlete',
          body_part: 'Body Part',
          severity: 'Severity',
          injury_date: 'Injury Date',
          injury_status: 'Status',
          estimated_recovery_days: 'Recovery Days'
        },
        filters: ['severity', 'injury_status'],
        dateField: 'injury_date'
      },
      'laboratory-test-list': {
        model: 'LaboratoryTest',
        fields: ['test_number', 'patient', 'test_name', 'test_category', 'sample_type', 'result', 'result_status', 'status', 'requested_date'],
        labels: {
          test_number: 'Test #',
          patient: 'Patient',
          test_name: 'Test Name',
          test_category: 'Category',
          sample_type: 'Sample Type',
          result: 'Result',
          result_status: 'Result Status',
          status: 'Status',
          requested_date: 'Requested Date'
        },
        filters: ['test_category', 'result_status', 'status'],
        dateField: 'requested_date'
      },
      'medical-staff-profile-list': {
        model: 'MedicalStaffProfile',
        fields: ['employee_id', 'role', 'department', 'status', 'employment_type', 'hire_date'],
        labels: {
          employee_id: 'Employee ID',
          role: 'Role',
          department: 'Department',
          status: 'Status',
          employment_type: 'Employment Type',
          hire_date: 'Hire Date'
        },
        filters: ['role', 'status', 'employment_type'],
        dateField: 'hire_date'
      },
      'shift-list': {
        model: 'Shift',
        fields: ['shift_label', 'department', 'hospital', 'shift_type', 'start_time', 'end_time', 'start_date', 'end_date'],
        labels: {
          shift_label: 'Shift Label',
          department: 'Department',
          hospital: 'Hospital',
          shift_type: 'Type',
          start_time: 'Start Time',
          end_time: 'End Time',
          start_date: 'Start Date',
          end_date: 'End Date'
        },
        filters: ['shift_type'],
        dateField: 'start_date'
      },
      'medical-staff-leave-list': {
        model: 'MedicalStaffLeave',
        fields: ['medical_staff', 'leave_type', 'start_date', 'end_date', 'status', 'reason'],
        labels: {
          medical_staff: 'Staff Member',
          leave_type: 'Leave Type',
          start_date: 'Start Date',
          end_date: 'End Date',
          status: 'Status',
          reason: 'Reason'
        },
        filters: ['leave_type', 'status'],
        dateField: 'start_date'
      },
      'medical-center-list': {
        model: 'MedicalCenter',
        fields: ['hospital_name', 'hospital_code', 'hospital_location', 'hospital_status', 'established_year', 'is_active'],
        labels: {
          hospital_name: 'Hospital Name',
          hospital_code: 'Code',
          hospital_location: 'Location',
          hospital_status: 'Status',
          established_year: 'Established',
          is_active: 'Active'
        },
        filters: ['hospital_status', 'is_active'],
        dateField: null
      },
      'medical-department-list': {
        model: 'MedicalDepartment',
        fields: ['department_code', 'department_name', 'department_type', 'location', 'is_emergency'],
        labels: {
          department_code: 'Code',
          department_name: 'Department',
          department_type: 'Type',
          location: 'Location',
          is_emergency: 'Emergency'
        },
        filters: ['department_type', 'is_emergency'],
        dateField: null
      },
      'health-camp-list': {
        model: 'HealthCamp',
        fields: ['camp_code', 'camp_name', 'department', 'organizer', 'camp_type', 'start_date', 'end_date', 'status', 'venue'],
        labels: {
          camp_code: 'Camp Code',
          camp_name: 'Camp Name',
          department: 'Department',
          organizer: 'Organizer',
          camp_type: 'Type',
          start_date: 'Start Date',
          end_date: 'End Date',
          status: 'Status',
          venue: 'Venue'
        },
        filters: ['camp_type', 'status'],
        dateField: 'start_date'
      },
    };
    return fieldMaps[reportKey] || null;
  }

  function fetchCategories() {
    return new Promise((resolve) => {
      const categories = getDynamicCategories();
      resolve(categories);
    });
  }

  function fetchReportData(reportKey, filters) {
    const url = `/dashboard/medical_reports/api/${reportKey}/data/`;
    const params = new URLSearchParams();
    
    if (filters) {
      Object.keys(filters).forEach(key => {
        if (filters[key]) {
          params.append(key, filters[key]);
        }
      });
    }
    
    const fullUrl = params.toString() ? `${url}?${params}` : url;
    
    return fetch(fullUrl)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        if (data.rows && data.columns) {
          return data;
        }
        if (Array.isArray(data)) {
          const columns = data.length > 0 ? Object.keys(data[0]).map(key => ({
            key: key,
            label: titleCase(key)
          })) : [];
          return { rows: data, columns: columns };
        }
        return { rows: [], columns: [] };
      })
      .catch(() => {
        return { rows: [], columns: [] };
      });
  }

  function titleCase(key) {
    return key.replace(/[_-]+/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }
  
  function normalize(str) {
    return (str === undefined || str === null ? '' : String(str)).toLowerCase().trim();
  }
  
  function escapeHtml(str) {
    if (str === undefined || str === null) return '';
    const d = document.createElement('div');
    d.textContent = String(str);
    return d.innerHTML;
  }

  function pad2(n) { return String(n).padStart(2, '0'); }

  function createDatePicker(onChange) {
    const wrap = document.createElement('div');
    wrap.className = 'mr-date-picker';
    wrap.innerHTML = `
      <i class="ti ti-calendar"></i>
      <input type="text" class="mr-datepicker-input" placeholder="Filter by date" readonly autocomplete="off">
    `;
    const input = wrap.querySelector('input');

    let panel = null;
    let viewDate = new Date();
    let selected = null;

    function fmtDisplay(d) {
      return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    }
    function fmtValue(d) {
      return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
    }
    function outsideClick(e) {
      if (panel && !wrap.contains(e.target) && !panel.contains(e.target)) closePanel();
    }
    function closePanel() {
      if (!panel) return;
      panel.remove();
      panel = null;
      document.removeEventListener('mousedown', outsideClick, true);
      window.removeEventListener('resize', reposition);
      window.removeEventListener('scroll', reposition, true);
    }
    function reposition() {
      if (!panel) return;
      const r = wrap.getBoundingClientRect();
      panel.style.minWidth = Math.max(r.width, 220) + 'px';
      let left = r.left;
      let top = r.bottom + 6;
      const pw = panel.offsetWidth || 260;
      if (left + pw > window.innerWidth - 8) left = Math.max(8, window.innerWidth - pw - 8);
      if (top + panel.offsetHeight > window.innerHeight - 8) top = Math.max(8, r.top - panel.offsetHeight - 6);
      panel.style.left = left + 'px';
      panel.style.top = top + 'px';
    }

    function renderPanel() {
      const isNew = !panel;
      if (isNew) {
        panel = document.createElement('div');
        panel.className = 'mr-datepicker-panel';
        document.body.appendChild(panel);
      }
      const year = viewDate.getFullYear();
      const month = viewDate.getMonth();
      const first = new Date(year, month, 1);
      const startDay = first.getDay();
      const daysInMonth = new Date(year, month + 1, 0).getDate();
      const daysInPrevMonth = new Date(year, month, 0).getDate();
      const monthLabel = viewDate.toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
      const weekdays = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];
      const today = new Date();

      let cells = '';
      for (let i = startDay - 1; i >= 0; i--) {
        cells += `<button type="button" class="mr-datepicker-day is-outside" disabled>${daysInPrevMonth - i}</button>`;
      }
      for (let d = 1; d <= daysInMonth; d++) {
        const cur = new Date(year, month, d);
        const isToday = cur.toDateString() === today.toDateString();
        const isSelected = selected && cur.toDateString() === selected.toDateString();
        cells += `<button type="button" class="mr-datepicker-day${isToday ? ' is-today' : ''}${isSelected ? ' is-selected' : ''}" data-date="${fmtValue(cur)}">${d}</button>`;
      }
      const totalCells = startDay + daysInMonth;
      const trailing = (7 - (totalCells % 7)) % 7;
      for (let d = 1; d <= trailing; d++) {
        cells += `<button type="button" class="mr-datepicker-day is-outside" disabled>${d}</button>`;
      }

      panel.innerHTML = `
        <div class="mr-datepicker-panel__header">
          <button type="button" class="mr-datepicker-nav" data-nav="-1" aria-label="Previous month"><i class="ti ti-chevron-left"></i></button>
          <span class="mr-datepicker-title">${monthLabel}</span>
          <button type="button" class="mr-datepicker-nav" data-nav="1" aria-label="Next month"><i class="ti ti-chevron-right"></i></button>
        </div>
        <div class="mr-datepicker-weekdays">${weekdays.map(w => `<span>${w}</span>`).join('')}</div>
        <div class="mr-datepicker-days">${cells}</div>
        <div class="mr-datepicker-footer">
          <button type="button" class="mr-datepicker-today">Today</button>
          <button type="button" class="mr-datepicker-clear">Clear</button>
        </div>
      `;

      panel.querySelectorAll('[data-nav]').forEach(btn => {
        btn.addEventListener('click', () => {
          viewDate = new Date(year, month + parseInt(btn.getAttribute('data-nav'), 10), 1);
          renderPanel();
        });
      });
      panel.querySelectorAll('.mr-datepicker-day:not(.is-outside)').forEach(btn => {
        btn.addEventListener('click', () => {
          const val = btn.getAttribute('data-date');
          const [yy, mm, dd] = val.split('-').map(Number);
          selected = new Date(yy, mm - 1, dd);
          input.value = fmtDisplay(selected);
          closePanel();
          onChange(val);
        });
      });
      panel.querySelector('.mr-datepicker-today').addEventListener('click', () => {
        const t = new Date();
        selected = t;
        viewDate = t;
        input.value = fmtDisplay(t);
        closePanel();
        onChange(fmtValue(t));
      });
      panel.querySelector('.mr-datepicker-clear').addEventListener('click', () => {
        selected = null;
        input.value = '';
        closePanel();
        onChange('');
      });

      reposition();
      if (isNew) {
        document.addEventListener('mousedown', outsideClick, true);
        window.addEventListener('resize', reposition);
        window.addEventListener('scroll', reposition, true);
      }
    }

    input.addEventListener('click', () => {
      if (panel) { closePanel(); return; }
      viewDate = selected ? new Date(selected) : new Date();
      renderPanel();
    });

    return {
      el: wrap,
      setValue(val) {
        if (!val) { selected = null; input.value = ''; return; }
        const [yy, mm, dd] = val.split('-').map(Number);
        selected = new Date(yy, mm - 1, dd);
        input.value = fmtDisplay(selected);
      },
      clear() { selected = null; input.value = ''; },
      destroy() { closePanel(); }
    };
  }

  // ===== OVERVIEW =====
  function updateOverview() {
    const totalCats = state.categories.length;
    let totalReports = 0;
    state.categories.forEach(c => totalReports += c.reports.length);
    els.totalReports.textContent = totalReports;
    els.totalCategories.textContent = totalCats;
    els.totalRecords.textContent = state.rows.length;
    
    const filteredRows = getFilteredRows();
    els.filteredCount.textContent = filteredRows.length;
  }

  // ===== BREADCRUMB =====
  function renderBreadcrumb() {
    const crumbs = [{ label: 'All Reports', icon: 'ti ti-home', onClick: goToCategories }];
    if (state.activeCategory) crumbs.push({ label: state.activeCategory.label, icon: null, onClick: goToReports });
    if (state.activeReport) crumbs.push({ label: state.activeReport.name, icon: null, onClick: null });
    
    els.breadcrumb.innerHTML = '';
    crumbs.forEach((c, i) => {
      if (i > 0) { 
        const sep = document.createElement('span'); 
        sep.className = 'sep'; 
        sep.innerHTML = '<i class="ti ti-chevron-right"></i>'; 
        els.breadcrumb.appendChild(sep); 
      }
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'crumb' + (c.onClick ? '' : ' is-current');
      const iconHtml = c.icon ? `<i class="${c.icon}"></i> ` : '';
      btn.innerHTML = iconHtml + c.label;
      if (c.onClick) btn.addEventListener('click', c.onClick);
      else btn.disabled = true;
      els.breadcrumb.appendChild(btn);
    });
    els.back.hidden = state.view === 'categories';
  }

  // ===== VIEWS =====
  function setView(v) {
    state.view = v;
    els.viewCategories.classList.toggle('is-hidden', v !== 'categories');
    els.viewReports.classList.toggle('is-hidden', v !== 'reports');
    els.viewData.classList.toggle('is-hidden', v !== 'data');
    if (v !== 'data') els.exportBar.classList.add('is-collapsed');
    els.paginationWrap.hidden = v !== 'data';
    
    const searchInput = els.dataFilters.querySelector('#mrFilterSearch');
    if (searchInput) {
      searchInput.value = '';
      state.searchTerm = '';
    }
    renderBreadcrumb();
    updateOverview();
  }
  
  function goToCategories() { 
    state.activeCategory = null; 
    state.activeReport = null; 
    setView('categories'); 
    renderCategories(); 
  }
  
  function goToReports() { 
    state.activeReport = null; 
    setView('reports'); 
    renderReportList(); 
  }
  
  function back() { 
    state.view === 'data' ? goToReports() : state.view === 'reports' ? goToCategories() : null; 
  }
  
  els.back.addEventListener('click', back);

  // ===== CATEGORIES =====
  function renderCategories() {
    els.categoryGrid.innerHTML = '';
    state.categories.forEach((cat, i) => {
      const card = document.createElement('article');
      card.className = 'folder';
      card.setAttribute('data-category', cat.key);
      card.setAttribute('data-aos', 'fade-up');
      card.setAttribute('data-aos-delay', String(Math.min(i * 60, 300)));
      card.innerHTML = `
        <div class="folder__tab"></div>
        <button type="button" class="folder__header">
          <span class="folder__icon"><i class="ti ${cat.icon}"></i></span>
          <span class="folder__title-wrap">
            <p class="folder__title">${cat.label}</p>
            <p class="folder__subtitle">${cat.desc}</p>
          </span>
          <span class="folder__count">${cat.reports.length}</span>
          <i class="ti ti-chevron-right folder__go"></i>
        </button>
      `;
      card.querySelector('.folder__header').addEventListener('click', () => openCategory(cat));
      els.categoryGrid.appendChild(card);
    });
    updateOverview();
  }
  
  function openCategory(cat) {
    state.activeCategory = cat;
    state.activeReport = null;
    setView('reports');
    renderReportList();
  }

  // ===== REPORTS =====
  function renderReportList() {
    const cat = state.activeCategory;
    els.reportList.innerHTML = '';
    if (!cat) return;
    cat.reports.forEach((rep, i) => {
      const item = document.createElement('button');
      item.type = 'button';
      item.className = 'report-item';
      item.setAttribute('data-aos', 'fade-up');
      item.setAttribute('data-aos-delay', String(Math.min(i * 50, 250)));
      item.innerHTML = `
        <span class="report-item__icon"><i class="ti ${rep.icon}"></i></span>
        <span class="report-item__info">
          <p class="report-item__name">${rep.name}</p>
          <p class="report-item__desc">${rep.desc}</p>
        </span>
        <i class="ti ti-chevron-right"></i>
      `;
      item.addEventListener('click', () => openReport(rep));
      els.reportList.appendChild(item);
    });
  }
  
  function openReport(rep) {
    state.activeReport = rep;
    state.activeFilters = {};
    state.currentPage = 1;
    state.slimInstances.forEach(s => {
      if (s && s.destroy) s.destroy();
    });
    state.slimInstances = [];
    if (state.datePicker) {
      state.datePicker.destroy();
      state.datePicker = null;
    }
    setView('data');
    loadReportData();
  }

  // ===== DATA =====
  function loadReportData() {
    els.dataLoading.hidden = false;
    els.tableWrap.classList.add('is-hidden');
    els.dataFilters.innerHTML = '';

    const reportFields = getReportFields(state.activeReport.key);
    if (!reportFields) {
      els.dataLoading.hidden = true;
      els.tableWrap.classList.add('is-hidden');
      els.emptyTable.hidden = false;
      els.paginationWrap.hidden = true;
      return;
    }

    fetchReportData(state.activeReport.key, {}).then(data => {
      els.dataLoading.hidden = true;
      
      const fields = reportFields.fields;
      const labels = reportFields.labels;
      
      const columns = [{ key: 'sno', label: 'S.No' }];
      fields.forEach(key => {
        columns.push({ key: key, label: labels[key] || titleCase(key) });
      });
      
      const rows = (data.rows || []).map((row, index) => {
        const newRow = { sno: index + 1 };
        fields.forEach(key => {
          const val = row[key];
          newRow[key] = (val === undefined || val === null || val === '') ? '-' : val;
        });
        return newRow;
      });
      
      state.rows = rows;
      state.columns = columns;
      state.reportFields = reportFields;
      state.filteredRows = [];
      
      buildFilters(reportFields);
      applyFiltersAndRender();
      updateOverview();
    });
  }

  // ===== BUILD FILTERS =====
  function buildFilters(reportFields) {
    els.dataFilters.innerHTML = '';
    if (!state.rows.length || !reportFields) return;

    const filterGroup = document.createElement('div');
    filterGroup.className = 'mr-filter-group';

    const searchWrap = document.createElement('div');
    searchWrap.className = 'mr-filter-search';
    searchWrap.innerHTML = `
      <i class="ti ti-search"></i>
      <input type="text" id="mrFilterSearch" placeholder="Search records…" aria-label="Filter search">
    `;
    const searchInput = searchWrap.querySelector('input');
    searchInput.addEventListener('input', function() {
      state.searchTerm = normalize(this.value);
      state.currentPage = 1;
      applyFiltersAndRender();
    });
    filterGroup.appendChild(searchWrap);

    if (reportFields.dateField) {
      const dateCol = state.columns.find(c => c.key === reportFields.dateField);
      if (dateCol) {
        const dp = createDatePicker((val) => {
          if (val) state.activeFilters[reportFields.dateField] = val;
          else delete state.activeFilters[reportFields.dateField];
          state.currentPage = 1;
          applyFiltersAndRender();
        });
        dp.el.querySelector('input').id = 'mrDateFilter';
        state.datePicker = dp;
        filterGroup.appendChild(dp.el);
      }
    }

    (reportFields.filters || []).forEach(key => {
      const col = state.columns.find(c => c.key === key);
      if (!col) return;
      const vals = uniqueValues(key);
      if (vals.length < 2) return;
      
      const item = document.createElement('div');
      item.className = 'mr-filter-item';
      
      const wrap = document.createElement('div');
      wrap.className = 'mr-filter';
      
      const sel = document.createElement('select');
      sel.setAttribute('data-filter-key', key);
      sel.innerHTML = `<option value="">All ${col.label}</option>` +
        vals.map(v => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join('');
      wrap.appendChild(sel);
      item.appendChild(wrap);
      filterGroup.appendChild(item);

      const ss = new SlimSelect({
        select: sel,
        settings: { 
          placeholderText: 'All ' + col.label,
          showSearch: false
        }
      });
      
      sel.slim = ss;
      state.slimInstances.push(ss);
      
      sel.addEventListener('change', function() {
        if (this.value) state.activeFilters[key] = this.value;
        else delete state.activeFilters[key];
        state.currentPage = 1;
        applyFiltersAndRender();
      });
    });

    els.dataFilters.appendChild(filterGroup);

    const actionsWrap = document.createElement('div');
    actionsWrap.className = 'mr-filters-actions';
    
    const clearBtn = document.createElement('button');
    clearBtn.type = 'button';
    clearBtn.className = 'mr-filters-clear';
    clearBtn.innerHTML = '<i class="ti ti-x"></i> Clear all';
    clearBtn.addEventListener('click', function(e) {
      e.preventDefault();
      clearAllFilters();
    });
    actionsWrap.appendChild(clearBtn);
    els.dataFilters.appendChild(actionsWrap);
  }

  // ===== CLEAR ALL FILTERS =====
  function clearAllFilters() {
    state.activeFilters = {};
    state.searchTerm = '';
    state.currentPage = 1;
    
    els.dataFilters.querySelectorAll('select').forEach(s => {
      s.value = '';
      if (s.slim) {
        try {
          s.slim.set('');
        } catch (e) {
          console.warn('Failed to clear SlimSelect:', e);
        }
      }
      const event = new Event('change', { bubbles: true });
      s.dispatchEvent(event);
    });
    
    if (state.datePicker) {
      state.datePicker.clear();
    }
    
    const searchInput = els.dataFilters.querySelector('#mrFilterSearch');
    if (searchInput) {
      searchInput.value = '';
      const event = new Event('input', { bubbles: true });
      searchInput.dispatchEvent(event);
    }
    
    applyFiltersAndRender();
  }

  function uniqueValues(key) {
    const set = new Set();
    state.rows.forEach(row => { 
      if (row[key] !== undefined && row[key] !== '—') set.add(String(row[key])); 
    });
    return Array.from(set);
  }

  function getFilteredRows() {
    return state.rows.filter(row => {
      for (const k in state.activeFilters) {
        if (String(row[k]) !== state.activeFilters[k]) return false;
      }
      if (state.searchTerm) {
        const hay = state.columns.map(c => String(row[c.key] || '')).join(' ');
        if (normalize(hay).indexOf(state.searchTerm) === -1) return false;
      }
      return true;
    });
  }

  function applyFiltersAndRender() {
    state.filteredRows = getFilteredRows();
    state.totalPages = Math.ceil(state.filteredRows.length / PAGE_SIZE) || 1;
    
    if (state.currentPage > state.totalPages) {
      state.currentPage = state.totalPages;
    }
    
    renderTable();
    renderPagination();
    updateOverview();
    updateExportBar();
  }

  function getCurrentPageRows() {
    const start = (state.currentPage - 1) * PAGE_SIZE;
    const end = start + PAGE_SIZE;
    return state.filteredRows.slice(start, end);
  }

  function renderTable() {
    const pageRows = getCurrentPageRows();
    
    if (!pageRows.length) {
      els.tableWrap.classList.add('is-hidden');
      els.emptyTable.hidden = false;
      els.tableHead.innerHTML = '';
      els.tableBody.innerHTML = '';
      return;
    }
    
    els.tableWrap.classList.remove('is-hidden');
    els.emptyTable.hidden = true;

    let headHtml = '<tr>';
    state.columns.forEach(c => {
      const cls = c.key === 'sno' ? ' class="sno-col"' : '';
      headHtml += `<th${cls}>${escapeHtml(c.label)}</th>`;
    });
    headHtml += '</tr>';
    els.tableHead.innerHTML = headHtml;

    const startIndex = (state.currentPage - 1) * PAGE_SIZE;
    els.tableBody.innerHTML = pageRows.map((row, idx) => {
      const sno = startIndex + idx + 1;
      const cells = state.columns.map(c => {
        const cls = c.key === 'sno' ? ' class="sno-col"' : '';
        let value = c.key === 'sno' ? sno : row[c.key];
        if (value === undefined || value === null || value === '') value = '-';
        return `<td${cls} data-label="${escapeHtml(c.label)}">${escapeHtml(value)}</td>`;
      }).join('');
      return `<tr>${cells}</tr>`;
    }).join('');
  }

  // ===== PAGINATION =====
  function renderPagination() {
    const total = state.filteredRows.length;
    const start = (state.currentPage - 1) * PAGE_SIZE + 1;
    const end = Math.min(state.currentPage * PAGE_SIZE, total);
    
    els.paginationInfo.innerHTML = `
      Showing <strong>${total > 0 ? start : 0}</strong> to <strong>${end}</strong> 
      of <strong>${total}</strong> records
    `;
    
    if (state.totalPages <= 1) {
      els.paginationControls.innerHTML = '';
      return;
    }
    
    let html = '';
    const current = state.currentPage;
    const totalPages = state.totalPages;
    
    html += `<button class="pagination-prev" ${current <= 1 ? 'disabled' : ''} 
             data-page="${current - 1}"><i class="ti ti-chevron-left"></i></button>`;
    
    const pages = getPageNumbers(current, totalPages);
    pages.forEach(p => {
      if (p === '...') {
        html += `<span class="pagination-ellipsis">…</span>`;
      } else {
        html += `<button class="${p === current ? 'active' : ''}" data-page="${p}">${p}</button>`;
      }
    });
    
    html += `<button class="pagination-next" ${current >= totalPages ? 'disabled' : ''} 
             data-page="${current + 1}"><i class="ti ti-chevron-right"></i></button>`;
    
    els.paginationControls.innerHTML = html;
    
    els.paginationControls.querySelectorAll('button[data-page]').forEach(btn => {
      btn.addEventListener('click', function() {
        const page = parseInt(this.getAttribute('data-page'));
        if (page && page !== state.currentPage) {
          state.currentPage = page;
          renderTable();
          renderPagination();
        }
      });
    });
  }

  function getPageNumbers(current, total) {
    const pages = [];
    const delta = 2;
    const range = [];
    const rangeWithDots = [];
    let l;

    for (let i = 1; i <= total; i++) {
      if (i === 1 || i === total || (i >= current - delta && i <= current + delta)) {
        range.push(i);
      }
    }

    range.forEach(i => {
      if (l) {
        if (i - l === 2) {
          rangeWithDots.push(l + 1);
        } else if (i - l !== 1) {
          rangeWithDots.push('...');
        }
      }
      rangeWithDots.push(i);
      l = i;
    });

    return rangeWithDots;
  }

  function updateExportBar() {
    const count = state.filteredRows.length;
    if (count > 0 && state.view === 'data') {
      els.exportCount.innerHTML = `<i class="ti ti-file-export"></i> Export ${count} filtered record${count > 1 ? 's' : ''}`;
      els.exportBar.classList.remove('is-collapsed');
    } else {
      els.exportBar.classList.add('is-collapsed');
    }
  }

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function getExportData() {
    const cols = state.columns.filter(c => c.key !== 'sno');
    const rows = state.filteredRows.map((row, idx) => {
      const r = { sno: idx + 1 };
      cols.forEach(c => { r[c.key] = row[c.key]; });
      return r;
    });
    return { cols: [{ key: 'sno', label: 'S.No' }, ...cols], rows };
  }

  function exportXLSX(filenameBase) {
    if (!window.XLSX) { console.warn('XLSX library not loaded'); return; }
    const { cols, rows } = getExportData();
    const data = rows.map(row => {
      const obj = {};
      cols.forEach(c => { obj[c.label] = (row[c.key] === undefined || row[c.key] === null || row[c.key] === '') ? '-' : row[c.key]; });
      return obj;
    });
    const ws = XLSX.utils.json_to_sheet(data, { header: cols.map(c => c.label) });
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Report');
    XLSX.writeFile(wb, filenameBase + '.xlsx');
  }

  function exportPDF(filenameBase, title) {
    if (!window.jspdf) { console.warn('jsPDF library not loaded'); return; }
    const { cols, rows } = getExportData();
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({
      orientation: cols.length > 6 ? 'landscape' : 'portrait',
      unit: 'mm',
      format: 'a4',
    });
    const pageWidth = doc.internal.pageSize.getWidth();

    doc.setFontSize(14);
    doc.text(title || 'Report', 14, 14);
    doc.setFontSize(9);
    doc.setTextColor(120);
    doc.text(`Generated ${new Date().toLocaleDateString()} · ${rows.length} record${rows.length === 1 ? '' : 's'}`, 14, 20);
    doc.setTextColor(0);

    doc.autoTable({
      startY: 25,
      head: [cols.map(c => c.label)],
      body: rows.map(row => cols.map(c => {
        const v = row[c.key];
        return (v === undefined || v === null || v === '') ? '-' : String(v);
      })),
      styles: { fontSize: 8, cellPadding: 2, overflow: 'linebreak' },
      headStyles: { fillColor: [197, 5, 12] },
      margin: { left: 10, right: 10 },
      tableWidth: pageWidth - 20,
    });

    const totalPages = doc.internal.getNumberOfPages();
    const pageHeight = doc.internal.pageSize.getHeight();
    for (let i = 1; i <= totalPages; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setTextColor(140);
      doc.text(`Page ${i} of ${totalPages}`, pageWidth - 10, pageHeight - 6, { align: 'right' });
    }
    doc.save(filenameBase + '.pdf');
  }

  els.exportBar.addEventListener('click', function(e) {
    const btn = e.target.closest('button[data-format]');
    if (!btn || btn.classList.contains('is-loading') || !state.activeReport) return;

    const format = btn.getAttribute('data-format');
    btn.classList.add('is-loading');

    const filenameBase = `${state.activeReport.key}-${new Date().toISOString().slice(0, 10)}`;

    try {
      if (format === 'xlsx') exportXLSX(filenameBase);
      else if (format === 'pdf') exportPDF(filenameBase, state.activeReport.name);
    } catch (err) {
      console.error('Export failed', err);
    } finally {
      btn.classList.remove('is-loading');
    }
  });

  fetchCategories().then(cats => {
    state.categories = cats;
    renderCategories();
    setView('categories');
    if (window.AOS) AOS.init({ duration: 400, once: true, offset: 20 });
  });

})();