// =======================
// PAGE CONTEXT (from data attributes, no inline template script)
// =======================
const cgPageEl = document.querySelector(".cg-page");
const CG_COURSE_CODE = cgPageEl?.dataset.courseCode || "";
const CG_COURSE_ID = cgPageEl?.dataset.courseId || "";
const CG_SECTION_ID = cgPageEl?.dataset.sectionId || "";
let CG_PENDING_COUNT = parseInt(cgPageEl?.dataset.pendingCount || "0", 10);
let CG_PENDING_REVIEW_COUNT = parseInt(cgPageEl?.dataset.pendingReviewCount || "0", 10);
const CG_FINALIZE_URL = cgPageEl?.dataset.finalizeUrl || "";

function getCsrfToken() {
  return document.querySelector('input[name=csrfmiddlewaretoken]').value;
}

// =======================
// TOAST (Bootstrap toast — used on pages with #liveToast, e.g. update_request.html)
// =======================
const toastEl = document.getElementById("liveToast");
const toastMsg = document.getElementById("toastMessage");
const toast = toastEl ? new bootstrap.Toast(toastEl, { delay: 2200 }) : null;

function showToast(message, type) {
  if (!toastEl || !toastMsg || !toast) return;
  toastMsg.innerText = message;
  toastEl.classList.remove("text-bg-success", "text-bg-danger", "text-bg-warning", "text-bg-info");
  toastEl.classList.add(`text-bg-${type}`);
  toast.show();
}

// =======================
// MESSAGE BOX (replaces alert)
// =======================
function cgShowMessage(text, type = "success", duration = 3500) {
  const box = document.getElementById("cgMsgBox");
  if (!box) return;
  const icon = type === "success" ? "ti-circle-check" : "ti-alert-triangle";
  const item = document.createElement("div");
  item.className = `cg-msgbox-item cg-msgbox-${type}`;
  item.innerHTML = `
    <i class="ti ${icon}"></i>
    <span>${text}</span>
    <button type="button" class="cg-msgbox-close" aria-label="Close">
      <i class="ti ti-x"></i>
    </button>
  `;
  item.querySelector(".cg-msgbox-close").onclick = () => {
    item.classList.remove("cg-msgbox-show");
    setTimeout(() => item.remove(), 250);
  };
  box.appendChild(item);
  requestAnimationFrame(() => item.classList.add("cg-msgbox-show"));
  if (duration > 0) {
    setTimeout(() => {
      item.classList.remove("cg-msgbox-show");
      setTimeout(() => item.remove(), 250);
    }, duration);
  }
}

// =======================
// CONFIRM MODAL (replaces confirm())
// =======================
function cgOpenConfirm() {
  const modal = document.getElementById("cgConfirmModal");
  if (!modal) return;
  modal.style.display = "flex";
  requestAnimationFrame(() => modal.classList.add("cg-confirm-show"));
}

function cgCloseConfirm() {
  const modal = document.getElementById("cgConfirmModal");
  if (!modal) return;
  modal.classList.remove("cg-confirm-show");
  setTimeout(() => { modal.style.display = "none"; }, 200);
}

// =======================
// LIVE PENDING COUNT (keeps Final Submit button in sync without reload)
// =======================
function cgDecrementPending() {
  if (CG_PENDING_COUNT > 0) {
    CG_PENDING_COUNT -= 1;
  }
  const btn = document.getElementById("cgFinalizeBtn");
  if (!btn) return;
  if (CG_PENDING_COUNT <= 0) {
    btn.classList.remove("cg-btn-disabled");
    btn.removeAttribute("title");
  } else {
    btn.title = `Enter and save all scores before finalizing (${CG_PENDING_COUNT} pending)`;
  }
}

// =======================
// FINAL SUBMIT
// =======================
function cgFinalizeGrades() {
  if (CG_PENDING_COUNT > 0) {
    cgShowMessage(`Cannot finalize — ${CG_PENDING_COUNT} student(s) still need a score entered and saved.`, "error");
    return;
  }
  if (CG_PENDING_REVIEW_COUNT > 0) {
    cgShowMessage(`Cannot finalize — ${CG_PENDING_REVIEW_COUNT} student(s) have a pending grade change request.`, "error");
    return;
  }
  cgOpenConfirm();
}

function cgConfirmFinalize() {
  cgCloseConfirm();
  fetch(CG_FINALIZE_URL, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
      "Content-Type": "application/x-www-form-urlencoded"
    },
    body: `course_id=${CG_COURSE_ID}&section_id=${CG_SECTION_ID}`
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      cgShowMessage(`Grades finalized successfully. ${data.updated} record(s) locked.`, "success");
      setTimeout(() => location.reload(), 1200);
    } else {
      cgShowMessage(data.message || "Could not finalize grades.", "error");
    }
  })
  .catch(() => cgShowMessage("Something went wrong while finalizing grades.", "error"));
}

// =======================
// EXPORT MENU TOGGLE
// =======================
function toggleExportMenu() {
  const menu = document.getElementById("cgExportMenu");
  if (menu) menu.classList.toggle("show");
}

document.addEventListener("click", function (event) {
  const exportBox = document.querySelector(".cg-export");
  if (exportBox && !exportBox.contains(event.target)) {
    const menu = document.getElementById("cgExportMenu");
    if (menu) menu.classList.remove("show");
  }
});

// =======================
// SAVE SINGLE GRADE
// =======================
function cgSaveGrade(gradeId) {
  const input = document.querySelector(`input.cg-input[data-grade-id="${gradeId}"]`);
  const raw = input.value.trim();
  const val = parseFloat(raw);
  const validFormat = /^(\d{1,2}(\.\d{1,2})?|100)$/.test(raw);
  if (!validFormat || isNaN(val) || val < 0 || val > 100) {
    cgShowMessage("Enter a valid score between 0 and 100 (max 2 decimal places).", "error");
    return;
  }
  const row = input.closest('tr');
  fetch(`/faculty/teaching/save_course_grade/${gradeId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: `numeric_score=${encodeURIComponent(raw)}`,
  })
  .then(res => res.text().then(text => {
    try { return JSON.parse(text); }
    catch (e) { throw new Error("Response was not valid JSON. Status: " + res.status); }
  }))
  .then(data => {
    if (data.success) {
      input.value = data.numeric_score;
      row.querySelector('.cg-grade-badge').textContent = data.letter_grade;
      row.children[6].textContent = data.grade_points;  // shifted +1
      row.children[7].textContent = data.grade_date;     // shifted +1
      input.setAttribute('readonly', 'readonly');
      const studentNumber = row.children[2].textContent.trim(); // shifted +1
      const courseCode = CG_COURSE_CODE || '';
      const actionsCell = row.querySelector('.cg-row-actions');
      actionsCell.innerHTML = `
        <a href="/faculty/teaching/update_request/?student_id=${encodeURIComponent(studentNumber)}&course_id=${encodeURIComponent(courseCode)}"
           class="cg-btn cg-btn-request">
          Request Update
        </a>`;
      row.children[0].innerHTML = '';
      cgDecrementPending();
      cgShowMessage("Grade saved successfully.", "success");
    } else {
      cgShowMessage(data.message, "error");
    }
  })
  .catch(err => {
    console.error("cgSaveGrade failed:", err);
    cgShowMessage("Save failed — check console for details.", "error");
  });
}

// =======================
// PRINT TABLE
// =======================
function printGradeTable() {
  const table = document.querySelector(".cg-table");
  if (!table) {
    return;
  }
  const printWindow = window.open(
    "",
    "_blank",
    "width=1200,height=800"
  );
  const tableClone = table.cloneNode(true);
  const courseName =
    document.querySelector(".cg-table-title")?.textContent.trim()
    || "Grade Report";
  const sectionName =
    table?.dataset.sections || "All Sections";
  tableClone.querySelectorAll("tr").forEach(row => {
    const cells = row.querySelectorAll("th, td");
    if (cells.length > 0) {
      cells[cells.length - 1].remove();
    }
  });
  tableClone.querySelectorAll(".cg-input").forEach(input => {
    const value = input.value.trim();
    const span = document.createElement("span");
    span.textContent = value !== "" ? value : "—";
    input.replaceWith(span);
  });
  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>${courseName} - Grades</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          padding: 30px;
          color: #222;
        }
        h2 {
          margin: 0 0 5px;
          font-size: 22px;
        }
        p {
          margin: 0;
          color: #666;
          font-size: 13px;
        }
        table {
          width: 100%;
          border-collapse: collapse;
          margin-top: 20px;
        }
        th,
        td {
          border: 1px solid #ccc;
          padding: 8px;
          font-size: 12px;
          text-align: left;
        }
        th {
          font-weight: bold;
          background: #f5f5f5;
        }
        @media print {
          body {
            padding: 0;
          }
        }
      </style>
    </head>
    <body>
      <h2>${courseName}</h2>
      <p>Section: ${sectionName}</p>
      <p>Student Grade Report</p>
      ${tableClone.outerHTML}
    </body>
    </html>
  `);
  printWindow.document.close();
  printWindow.onload = function () {
    printWindow.focus();
    printWindow.print();
    printWindow.close();
  };
}

// =======================
// SCORE INPUT VALIDATION
// =======================
function cgValidateScoreInput(e) {
  const input = e.target;
  const char = String.fromCharCode(e.which);
  const current = input.value;
  if (!/[\d.]/.test(char)) {
    e.preventDefault();
    return;
  }
  if (char === "." && current.includes(".")) {
    e.preventDefault();
    return;
  }
  const start = input.selectionStart;
  const end = input.selectionEnd;
  const projected = current.slice(0, start) + char + current.slice(end);
  const partiallyValid =
    /^\d{0,2}(\.\d{0,2})?$/.test(projected) ||
    /^100$/.test(projected) ||
    /^1(0(0)?)?$/.test(projected);
  if (!partiallyValid) {
    e.preventDefault();
  }
}

function cgValidateScoreFinal(e) {
  const input = e.target;
  const raw = input.value.trim();
  const val = parseFloat(raw);
  const validFormat = /^(\d{1,2}(\.\d{1,2})?|100)$/.test(raw);
  if (raw !== "" && (!validFormat || isNaN(val) || val < 0 || val > 100)) {
    input.classList.add("cg-input-invalid");
  } else {
    input.classList.remove("cg-input-invalid");
  }
}

// =======================
// BULK SELECT / SAVE
// =======================
function cgToggleSelectAll(checkbox) {
  document.querySelectorAll('.cg-row-checkbox').forEach(cb => {
    cb.checked = checkbox.checked;
  });
  cgRowChecked();
}

function cgRowChecked() {
  const checked = document.querySelectorAll('.cg-row-checkbox:checked');
  const bar = document.getElementById('cgBulkBar');
  const countEl = bar.querySelector('.cg-bulk-count-number');
  countEl.textContent = checked.length;
  bar.style.display = checked.length > 0 ? 'flex' : 'none';
  const selectAll = document.getElementById('cgSelectAll');
  const allRowCheckboxes = document.querySelectorAll('.cg-row-checkbox');
  if (selectAll && allRowCheckboxes.length > 0) {
    selectAll.checked = checked.length === allRowCheckboxes.length;
  }
}

function cgBulkSaveGrades() {
  const checked = document.querySelectorAll('.cg-row-checkbox:checked');
  if (checked.length === 0) return;
  const entries = [];
  const invalidRows = [];
  checked.forEach(cb => {
    const row = cb.closest('tr');
    const input = row.querySelector('.cg-input');
    const raw = input.value.trim();
    const val = parseFloat(raw);
    const validFormat = /^(\d{1,2}(\.\d{1,2})?|100)$/.test(raw);
    if (!validFormat || isNaN(val) || val < 0 || val > 100) {
      invalidRows.push(row.dataset.gradeId);
      input.classList.add("cg-input-invalid");
      return;
    }
    entries.push({ grade_id: parseInt(row.dataset.gradeId, 10), numeric_score: raw });
  });
  if (invalidRows.length > 0) {
    cgShowMessage(`Fix invalid scores before bulk saving (row IDs: ${invalidRows.join(', ')}).`, "error");
    return;
  }
  const btn = document.getElementById('cgBulkSaveBtn');
  btn.disabled = true;
  btn.textContent = 'Saving...';
  fetch('/faculty/teaching/save_course_grades_bulk/', {
    method: "POST",
    headers: {
      "X-CSRFToken": getCsrfToken(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ entries }),
  })
  .then(res => res.text().then(text => {
    try { return JSON.parse(text); }
    catch (e) { throw new Error("Response was not valid JSON. Status: " + res.status); }
  }))
  .then(data => {
    if (!data.success) {
      cgShowMessage(data.message || "Bulk save failed.", "error");
      return;
    }
    data.results.forEach(result => {
      const row = document.querySelector(`tr[data-grade-id="${result.grade_id}"]`);
      if (!row) return;

      if (result.success) {
        const input = row.querySelector('.cg-input');
        input.value = result.numeric_score;
        input.setAttribute('readonly', 'readonly');

        row.querySelector('.cg-grade-badge').textContent = result.letter_grade;
        row.children[6].textContent = result.grade_points;
        row.children[7].textContent = result.grade_date;

        const studentNumber = row.children[2].textContent.trim();
        const courseCode = CG_COURSE_CODE || '';

        const actionsCell = row.querySelector('.cg-row-actions');
        actionsCell.innerHTML = `
          <a href="/faculty/teaching/update_request/?student_id=${encodeURIComponent(studentNumber)}&course_id=${encodeURIComponent(courseCode)}"
             class="cg-btn cg-btn-request">
            Request Update
          </a>`;

        row.children[0].innerHTML = '';
        cgDecrementPending();
      } else {
        const input = row.querySelector('.cg-input');
        input.classList.add("cg-input-invalid");
      }
    });

    cgShowMessage(`${data.updated} grade(s) saved successfully.`, "success");
    document.getElementById('cgSelectAll').checked = false;
    cgRowChecked();
  })
  .catch(err => {
    console.error("cgBulkSaveGrades failed:", err);
    cgShowMessage("Bulk save failed — check console for details.", "error");
  })
  .finally(() => {
    btn.disabled = false;
    btn.textContent = 'Bulk Save Scores';
  });
}

// =======================
// INIT
// =======================
document.addEventListener("DOMContentLoaded", function () {
  if (window.GCR_HAS_ERRORS) {
    showToast("Please fix the errors below before submitting.", "danger");
  }

  const requestedScore = document.getElementById("requested_score");
  const requestedError = document.getElementById("requested_score_error");

  if (requestedScore) {
    requestedScore.addEventListener("input", function () {
      const val = parseFloat(this.value);
      if (this.value !== "" && (isNaN(val) || val < 0 || val > 100)) {
        this.classList.add("gcr-input-invalid");
        if (requestedError) requestedError.textContent = "Must be between 0 and 100.";
      } else {
        this.classList.remove("gcr-input-invalid");
        if (requestedError) requestedError.textContent = "";
      }
    });
  }

  document.querySelectorAll(".cg-input").forEach(input => {
    input.addEventListener("keypress", cgValidateScoreInput);
    input.addEventListener("input", cgValidateScoreFinal);
  });
  const overlay = document.getElementById("cgConfirmModal");
  if (overlay) {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) cgCloseConfirm();
    });
  }
});

// =======================
// WEBSOCKET
// =======================
window.addEventListener("grade_request_decided", function (e) {
    const d = e.detail;
    const page = document.querySelector(".cg-page");
    if (!page || page.dataset.courseCode !== d.course_id) return;

    const row = document.querySelector(`tr[data-student-id="${d.student_id}"]`);
    if (!row) return;

    const actionsCell = row.querySelector(".cg-row-actions");
    if (actionsCell) {
        const baseUrl = page.dataset.updateRequestUrl;
        const courseCode = page.dataset.courseCode;
        const sectionId = page.dataset.sectionId;
        const url = `${baseUrl}?student_id=${encodeURIComponent(d.student_id)}&course_id=${encodeURIComponent(courseCode)}${sectionId ? "&section_id=" + encodeURIComponent(sectionId) : ""}`;
        actionsCell.innerHTML = `<a href="${url}" class="cg-btn cg-btn-request">Request Update</a>`;
    }

    row.style.transition = "background-color 1.5s ease";
    row.style.backgroundColor = d.status === "Approved" ? "#d4edda" : "#f8d7da";
    setTimeout(() => { row.style.backgroundColor = ""; }, 1600);
});