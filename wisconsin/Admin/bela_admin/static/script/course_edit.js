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

  'words': (v) => {
    if (!v.trim()) return null;
    const max = parseInt(document.getElementById('description')?.dataset.maxwords || '1000');
    const words = v.trim().split(/\s+/).filter(Boolean).length;
    return words > max ? `Description must be ${max} words or fewer (currently ${words} words).` : null;
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
  if (error) {
    el.classList.add('is-invalid');
    if (errEl) { errEl.querySelector('span').textContent = error; errEl.classList.add('show'); }
  } else {
    el.classList.remove('is-invalid');
    if (errEl) errEl.classList.remove('show');
  }
  return !error;
}

// Speed code: Attach listeners 
document.querySelectorAll('[data-validate]').forEach(el => {
  el.addEventListener('blur',   () => validateField(el));
  el.addEventListener('input',  () => {
    if (el.classList.contains('is-invalid')) validateField(el);
    // Speed code: Auto-uppercase course code
    if (el.id === 'course_code') el.value = el.value.toUpperCase();
  });
  el.addEventListener('change', () => {
    if (el.classList.contains('is-invalid')) validateField(el);
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
    if (first) { first.scrollIntoView({ behavior:'smooth', block:'center' }); first.focus(); }
    return;
  }
  const btn = document.getElementById('submitBtn');
  btn.disabled = true;
  btn.innerHTML = '<i data-lucide="loader-2"></i> Updating…';
  if (typeof lucide !== 'undefined') lucide.createIcons();
});



/* ══ ADD REQUIREMENT via AJAX POST ══════════════════════════ */
document.getElementById('addReqBtn').addEventListener('click', function () {
  console.log("Add Requirement button clicked");
  const typeEl  = document.getElementById('req_type');
  const typeId  = typeEl.value;
  const errEl   = document.getElementById('err_req_type');

  // validate
  if (!typeId) {
    typeEl.classList.add('is-invalid');
    errEl.classList.add('show');
    typeEl.focus();
    return;
  }
  typeEl.classList.remove('is-invalid');
  errEl.classList.remove('show');

  const relCourse = document.getElementById('req_related_course').value;
  const note      = document.getElementById('req_note').value.trim();
  const order     = document.getElementById('req_order').value || 1;

  const body = new FormData();
  body.append(
    'csrfmiddlewaretoken',
    document.querySelector('[name=csrfmiddlewaretoken]').value
);
  body.append('requirement_type_id', typeId);
  body.append('related_course_id',   relCourse);
  body.append('note',                note);
  body.append('display_order',       order);

  fetch(COURSE_REQUIREMENT_ADD_URL, {
    method: 'POST',
    body: body
})
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      // Remove empty row if present
      const emptyRow = document.getElementById('req-empty-row');
      if (emptyRow) emptyRow.remove();

      // Append new row
      const tbody = document.getElementById('reqTbody');
      const tr = document.createElement('tr');
      tr.id = `req-row-${data.requirement_id}`;
      tr.innerHTML = `
        <td><span class="order-badge">${data.display_order}</span></td>
        <td><span class="sub-type-pill">${data.requirement_type_name}</span></td>
        <td>
          ${data.related_course_code
            ? `<span class="sub-course-code">${data.related_course_code}</span>
               <span style="font-size:12px;color:#495057;margin-left:4px;">${data.related_course_name}</span>`
            : `<span style="font-size:12px;color:#adb5bd;font-style:italic;">None</span>`}
        </td>
        <td>${data.note
          ? `<span class="sub-note">${data.note}</span>`
          : `<span style="font-size:12px;color:#adb5bd;">—</span>`}
        </td>
        <td>
          <div class="sub-act-btns">
            <button type="button" class="sub-act-btn del" title="Remove"

                    data-kind="req" data-id="${data.requirement_id}" data-name="${data.requirement_type_name}"
                    onclick="confirmDeleteSub(this)">



              <i data-lucide="trash-2"></i>
            </button>
          </div>
        </td>`;
      tbody.appendChild(tr);
      updateCardCount("card-req", 1);

      // Reset fields
      typeEl.value = '';
      document.getElementById('req_related_course').value = '';
      document.getElementById('req_note').value = '';
      document.getElementById('req_order').value = 1;

      if (typeof lucide !== 'undefined') lucide.createIcons();
    } else {

    const err = document.getElementById("err_req_duplicate");

    err.querySelector("span").textContent =
        data.error || "Something went wrong.";

    err.classList.add("show");
  }
  })
  .catch(() => alert('Network error. Please try again.'));
});

/* ══ ADD DESIGNATION via AJAX POST ══════════════════════════ */
document.getElementById('addDesgBtn').addEventListener('click', function () {
  const typeEl = document.getElementById('desg_type');
  const typeId = typeEl.value;
  const errEl  = document.getElementById('err_desg_type');

  if (!typeId) {
    typeEl.classList.add('is-invalid');
    errEl.classList.add('show');
    typeEl.focus();
    return;
  }
  typeEl.classList.remove('is-invalid');
  errEl.classList.remove('show');

  const value = document.getElementById('desg_value').value.trim();
  const order = document.getElementById('desg_order').value || 1;

  const body = new FormData();
  body.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
  body.append('designation_type_id', typeId);
  body.append('designation_value',   value);
  body.append('display_order',       order);

  fetch(COURSE_DESIGNATION_ADD_URL, {
    method: 'POST', body
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      document.getElementById("err_desg_duplicate").classList.remove("show");
      const emptyRow = document.getElementById('desg-empty-row');
      if (emptyRow) emptyRow.remove();

      const tbody = document.getElementById('desgTbody');
      const tr = document.createElement('tr');
      tr.id = `desg-row-${data.designation_id}`;
      tr.innerHTML = `
        <td><span class="order-badge">${data.display_order}</span></td>
        <td><span class="sub-type-pill desg">${data.designation_type_name}</span></td>
        <td>${data.designation_value
          ? `<span style="font-size:13px;color:#495057;">${data.designation_value}</span>`
          : `<span style="font-size:12px;color:#adb5bd;font-style:italic;">No value</span>`}
        </td>
        <td>
          <div class="sub-act-btns">
            <button type="button" class="sub-act-btn del" title="Remove"

                    data-kind="desg" data-id="${data.designation_id}" data-name="${data.designation_type_name}"
                    onclick="confirmDeleteSub(this)">

              <i data-lucide="trash-2"></i>
            </button>
          </div>
        </td>`;
      tbody.appendChild(tr);
      updateCardCount("card-desg", 1);

      typeEl.value = '';
      document.getElementById('desg_value').value = '';
      document.getElementById('desg_order').value = 1;

      if (typeof lucide !== 'undefined') lucide.createIcons();
    } else {

    const err = document.getElementById("err_desg_duplicate");

    err.querySelector("span").textContent =
        data.error || "Something went wrong.";

    err.classList.add("show");
}
  })
  .catch(() => alert('Network error. Please try again.'));
});

/* ══ DELETE sub-item modal ══════════════════════════════════ */
function confirmDeleteSub(btn) {

    var kind, id, name;

    if (typeof btn === 'string') {
        kind = btn;
        id = arguments[1];
        name = arguments[2];
    } else {
        kind = btn.dataset.kind;
        id = btn.dataset.id;
        name = btn.dataset.name;
    }

    document.getElementById("subDeleteName").textContent = name;

    var url;
    if (kind === "req") {
        url = `/department/courses/requirement/${id}/delete/`;
    } else if (kind === "desg") {
        url = `/department/courses/designation/${id}/delete/`;
    } else if (kind === "offering") {
        url = COURSE_OFFERING_DELETE_URL.replace('/0/', `/${id}/`);
    } else if (kind === "outcome") {
        url = COURSE_OUTCOME_DELETE_URL.replace('/0/', `/${id}/`);
    }

    document.getElementById("subDeleteForm").action = url;
    document.getElementById("subDeleteForm").dataset.rowId = id;
    document.getElementById("subDeleteForm").dataset.rowKind = kind;

    new bootstrap.Modal(
        document.getElementById("subDeleteModal")
    ).show();
}

/* intercept form submit → AJAX so we stay on page */
document.getElementById('subDeleteForm').addEventListener('submit', function(e) {
  e.preventDefault();
  const fd  = new FormData(this);
  const url = this.action;
  const kind   = this.dataset.rowKind;
  const rowId  = this.dataset.rowId;

  fetch(url, { method: 'POST', body: fd })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      var prefixes = { req: 'req-row-', desg: 'desg-row-', offering: 'offering-row-', outcome: 'outcome-row-' };
      var prefix = prefixes[kind] || 'row-';
      var row = document.getElementById(prefix + rowId);
      if (row) row.remove();
      const cardMap = {
    req: "card-req",
    desg: "card-desg",
    offering: "card-offering",
    outcome: "card-outcome"
};

updateCardCount(cardMap[kind], -1);
      bootstrap.Modal.getInstance(document.getElementById('subDeleteModal')).hide();
    } else {
      alert(data.error || 'Delete failed.');
    }
  });
});

/* ══ Validate req_type on change ════════════════════════════ */
document.getElementById("req_type").addEventListener("change", function () {

    if (this.value) {
        this.classList.remove("is-invalid");
        document.getElementById("err_req_type").classList.remove("show");
    }

    // Hide duplicate error
    document.getElementById("err_req_duplicate").classList.remove("show");
});
document.getElementById('desg_type').addEventListener('change', function() {
  if (this.value) {
    this.classList.remove('is-invalid');
    document.getElementById('err_desg_type').classList.remove('show');
  }
   document.getElementById("err_desg_duplicate").classList.remove("show");
});

/* ══ Escape HTML for innerHTML safety ══════════════════════ */
function escapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}
function updateCardCount(cardId, change) {

    const badge = document.querySelector(`#${cardId} .sub-card-count`);

    if (!badge) return;

    badge.textContent = parseInt(badge.textContent, 10) + change;

}
/* ══ Init Lucide ════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  if (typeof lucide !== 'undefined') lucide.createIcons();
});


/*Ranganayagi code */
 
document.getElementById("addOfferingBtn").addEventListener("click", function () {
 
    var term = document.getElementById("id_term").value;
    var year = document.getElementById("id_year").value;
 
    var yearErrEl = document.getElementById("err_id_year");
    var termEl = document.getElementById("id_term");
    var yearEl = document.getElementById("id_year");

    termEl.classList.remove("is-invalid");
    yearEl.classList.remove("is-invalid");
    if (yearErrEl) yearErrEl.classList.remove("show");

    if (!term) {
        termEl.classList.add("is-invalid");
        termEl.focus();
        return;
    }

    if (!year) {
        yearEl.classList.add("is-invalid");
        if (yearErrEl) {
            yearErrEl.querySelector("span").textContent = "Please enter a year.";
            yearErrEl.classList.add("show");
        }
        yearEl.focus();
        return;
    }

    if (!/^\d{4}$/.test(year) || parseInt(year) < 1800 || parseInt(year) > 2100) {
        yearEl.classList.add("is-invalid");
        if (yearErrEl) {
            yearErrEl.querySelector("span").textContent = "Year must be a 4-digit number between 1800 and 2100.";
            yearErrEl.classList.add("show");
        }
        yearEl.focus();
        return;
    }
 
    var body = new URLSearchParams();
    body.append("csrfmiddlewaretoken", getCSRFToken());
    body.append("term", term);
    body.append("year", year);
 
    fetch(COURSE_OFFERING_ADD_URL, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString()
    })
    .then(function (res) { return res.json(); })
    .then(function (data) {
        if (data.success) {
            var emptyRow = document.getElementById("offering-empty-row");
            if (emptyRow) emptyRow.remove();
 
            var tbody = document.getElementById("offeringTableBody");
            var tr = document.createElement("tr");
            tr.id = 'offering-row-' + data.id;
            var count = tbody.querySelectorAll("tr").length + 1;
            tr.innerHTML =
                '<td><span class="order-badge">' + count + '</span></td>' +
                '<td>' + data.term + '</td>' +
                '<td>' + data.year + '</td>' +
                '<td><div class="sub-act-btns">' +
                    '<button type="button" class="sub-act-btn del" title="Remove" ' +
                            'onclick="confirmDeleteSub(\'offering\',' + data.id + ',\'' + data.term + ' ' + data.year + '\')">' +
                        '<i data-lucide="trash-2"></i>' +
                    '</button>' +
                '</div></td>';
            tbody.appendChild(tr);
            updateCardCount("card-offering", 1);
            if (typeof lucide !== 'undefined') lucide.createIcons();
 
            document.getElementById("id_term").value = "";
            document.getElementById("id_year").value = "";
        } else {
            var errMsg = "Unable to save.";
            if (data.errors) {
                var msgs = [];
                for (var key in data.errors) {
                    if (data.errors.hasOwnProperty(key)) {
                        msgs.push(data.errors[key].join(" "));
                    }
                }
                if (msgs.length) errMsg = msgs.join(" ");
            }
            alert(errMsg);
        }
    })
    .catch(function (err) {
        console.error("Offering add error:", err);
        alert("An error occurred. Check console for details.");
    });
 
});
 
 
document.getElementById("addOutcomeBtn").addEventListener("click", function () {
  
    var outcomeEl = document.getElementById("id_outcome");
    var outcomeErrEl = document.getElementById("err_id_outcome");
    var outcome = outcomeEl.value.trim().replace(/\n+/g, '\n');

    outcomeEl.classList.remove("is-invalid");
    if (outcomeErrEl) outcomeErrEl.classList.remove("show");
  
    if (outcome === "") {
        outcomeEl.classList.add("is-invalid");
        if (outcomeErrEl) {
            outcomeErrEl.querySelector("span").textContent = "Please enter a learning outcome.";
            outcomeErrEl.classList.add("show");
        }
        outcomeEl.focus();
        return;
    }
  
    var body = new URLSearchParams();
    body.append("csrfmiddlewaretoken", getCSRFToken());
    body.append("outcome", outcome);
 
    fetch(COURSE_OUTCOME_ADD_URL, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString()
    })
    .then(function (res) { return res.json(); })
    .then(function (data) {
        if (data.success) {
            var emptyRow = document.getElementById("learning-empty-row");
            if (emptyRow) emptyRow.remove();
 
            var tbody = document.getElementById("learningOutcomeTableBody");
            var tr = document.createElement("tr");
            tr.id = 'outcome-row-' + data.id;
            var count = tbody.querySelectorAll("tr").length + 1;
            var safeOutcome = escapeHtml(data.outcome).replace(/\n+/g, '<br>');
            tr.innerHTML =
                '<td><span class="order-badge">' + count + '</span></td>' +
                '<td>' + safeOutcome + '</td>' +
                '<td><div class="sub-act-btns">' +
                    '<button type="button" class="sub-act-btn del" title="Remove" ' +
                            'onclick="confirmDeleteSub(\'outcome\',' + data.id + ',\'' + data.outcome.replace(/'/g, "\\'") + '\')">' +
                        '<i data-lucide="trash-2"></i>' +
                    '</button>' +
                '</div></td>';
            tbody.appendChild(tr);
            updateCardCount("card-outcome", 1);
            if (typeof lucide !== 'undefined') lucide.createIcons();
 
            document.getElementById("id_outcome").value = "";
        } else {
            alert(data.error || "Unable to save.");
        }
    })
    .catch(function (err) {
        console.error("Outcome add error:", err);
        alert("An error occurred. Check console for details.");
    });
 
});

document.getElementById("id_outcome").addEventListener("input", function () {
    if (this.value.trim() !== "") {
        this.classList.remove("is-invalid");
        var errEl = document.getElementById("err_id_outcome");
        if (errEl) errEl.classList.remove("show");
    }
});
  
/*ranganayagi code end*/
const departmentSelect = document.getElementById("department");
const programSelect = document.getElementById("academic_program");

document.addEventListener("DOMContentLoaded", function () {

    const programChoices = window.choicesMap["academic_program"];

    if (!departmentSelect || !programSelect || !programChoices) {
        return;
    }

    // Store all options once
    const allOptions = Array.from(programSelect.options).map(option => ({
        value: option.value,
        label: option.text,
        department: option.dataset.department || ""
    }));

    // Store initially selected program
    let selectedProgram = programSelect.value;

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
                selected: option.value === selectedProgram
            })),
            "value",
            "label",
            true
        );

    }

    // Initial page load
    filterPrograms();

    // Department changed
    departmentSelect.addEventListener("change", function () {

        // Don't keep old program
        selectedProgram = "";

        filterPrograms();

        // Clear current selection
        programChoices.removeActiveItems();

    });

});


// Speed code: Init Lucide 
document.addEventListener('DOMContentLoaded', () => {
  if (typeof lucide !== 'undefined') lucide.createIcons();
});
