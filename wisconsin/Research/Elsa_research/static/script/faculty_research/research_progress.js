function rebuildDateInput(id, minValue, value) {
    const old = document.getElementById(id);
    if (!old) return null;

    const fresh = old.cloneNode(true);
    fresh.value = "";
    if (minValue) {
        fresh.setAttribute("min", minValue);
    } else {
        fresh.removeAttribute("min");
    }
    old.parentNode.replaceChild(fresh, old);
    fresh.value = value || "";
    return fresh;
}

document.addEventListener("DOMContentLoaded", function () {
    lucide.createIcons();

    // ===============================
    // Disable past dates on Milestone Start / Deadline
    // ===============================
    const todayStr = new Date().toLocaleDateString("en-CA"); // "YYYY-MM-DD" in local time
    rebuildDateInput("milestoneStart", todayStr, "");
    rebuildDateInput("milestoneDeadline", todayStr, "");

    new Choices(document.getElementById("progressResearchSelect"), {
        searchEnabled: true,
        itemSelectText: "",
        shouldSort: false,
    });

    const statusSelect = document.getElementById("milestoneStatus");
    if (statusSelect) {
        window.statusChoices = new Choices(statusSelect, {
            searchEnabled: false,
            itemSelectText: "",
            shouldSort: false,
        });
    }

    const tabs = document.querySelectorAll(".rp-tab");
    const TAB_STORAGE_KEY = "rpFacultyActiveTab";

    function activateTab(targetId) {
        tabs.forEach(t => t.classList.remove("active"));
        document.querySelectorAll(".rp-tab-panel").forEach(panel => {
            panel.style.display = "none";
        });
        const tabEl = document.querySelector(`.rp-tab[data-target="${targetId}"]`);
        if (tabEl) tabEl.classList.add("active");

        const panelEl = document.getElementById(targetId);
        if (panelEl) panelEl.style.display = "block";
    }
    tabs.forEach(function (tab) {
        tab.addEventListener("click", function () {
            activateTab(tab.dataset.target);
            sessionStorage.setItem(TAB_STORAGE_KEY, tab.dataset.target);
        });
    });

    const savedTab = sessionStorage.getItem(TAB_STORAGE_KEY);
    if (savedTab && document.getElementById(savedTab)) {
        activateTab(savedTab);
    }

    const milestoneForm = document.getElementById("milestoneForm");
    if (milestoneForm) {
        milestoneForm.addEventListener("submit", function (e) {
            e.preventDefault();
            clearMilestoneErrors();
            const saveBtn = document.getElementById("saveMilestoneBtn");
            const originalHTML = saveBtn.innerHTML;
            saveBtn.disabled = true;
            saveBtn.innerHTML = "Saving...";
            fetch(milestoneForm.action, {
                method: "POST",
                headers: { "X-Requested-With": "XMLHttpRequest" },
                body: new FormData(milestoneForm),
            })
                .then(res => res.json().then(data => ({ status: res.status, data })))
                .then(({ status, data }) => {
                    if (status === 200 && data.success) {
                        upsertMilestoneCard(data.milestone);
                        upsertStudentsTab(data.students_update);
                        closeMilestoneModal();
                        saveBtn.disabled = false;
                        saveBtn.innerHTML = originalHTML;
                        lucide.createIcons();
                        return;
                    }
                    showMilestoneErrors(data.errors || {});
                    saveBtn.disabled = false;
                    saveBtn.innerHTML = originalHTML;
                    lucide.createIcons();
                })
                .catch(err => {
                    console.error("Milestone save failed:", err);
                    saveBtn.disabled = false;
                    saveBtn.innerHTML = originalHTML;
                    lucide.createIcons();
                    alert("Something went wrong. Please try again.");
                });
        });
    }
});

// ============= ERROR HANDLING =============

function showMilestoneErrors(errors) {
    const fieldToInput = {
        title: "milestoneTitle",
        description: "milestoneDescription",
        start_date: "milestoneStart",
        deadline: "milestoneDeadline",
        expected_percentage: "expectedPercentage",
        status: "milestoneStatus",
    };

    Object.keys(errors).forEach(function (field) {
        const errEl = document.getElementById("err-" + field);
        if (errEl) errEl.textContent = errors[field];

        const inputEl = document.getElementById(fieldToInput[field]);
        if (!inputEl) return;

        if (field === "status") {
            const wrapper = inputEl.closest(".choices");
            if (wrapper) wrapper.classList.add("choices-error");
        } else {
            inputEl.classList.add("input-error");
        }
    });
}

function clearMilestoneErrors() {
    document.querySelectorAll("#milestoneForm .rp-error")
        .forEach(el => el.textContent = "");
    document.querySelectorAll("#milestoneForm .input-error")
        .forEach(el => el.classList.remove("input-error"));
    document.querySelectorAll("#milestoneForm .choices-error")
        .forEach(el => el.classList.remove("choices-error"));
}

// ============= CARD BUILD / UPDATE  =============

function buildMilestoneCardHTML(m) {
    const statusClassMap = {
        completed: "rp-status-completed",
        in_progress: "rp-status-progress",
        delayed: "rp-status-closed",
        not_started: "rp-status-draft",
    };
    const statusClass = statusClassMap[m.status] || "rp-status-draft";

    const studentsText = m.assigned_students.length
        ? m.assigned_students.join(", ")
        : "No students";

    return `
        <div class="rp-milestone-top">
            <h3>${m.title}</h3>
            <button class="rp-btn rp-btn-edit"
                    data-id="${m.milestone_id}"
                    data-title="${m.title}"
                    data-description="${m.description}"
                    data-start="${m.start_date_iso}"
                    data-deadline="${m.deadline_iso}"
                    data-expected="${m.expected_percentage}"
                    data-status="${m.status}"
                    onclick="editMilestone(this)">
                <i data-lucide="edit"></i>
                Edit
            </button>
        </div>
        <span class="rp-status ${statusClass}">${m.status_display}</span>
        <p><i data-lucide="file-text"></i> Description : ${m.description}</p>
        <div class="rp-review">
            <p><i data-lucide="calendar"></i> Start Date : ${m.start_date}</p>
            <p><i data-lucide="calendar"></i> Deadline : ${m.deadline}</p>
            <p><i data-lucide="chart-line"></i> Expected Completion : ${m.expected_percentage}%</p>
        </div>
        <p><i data-lucide="users"></i> Assigned Students : ${studentsText}</p>
    `;
}

function upsertMilestoneCard(m) {
    const list = document.querySelector("#rp-tab-milestones");

    const emptyMsg = Array.from(list.querySelectorAll("p"))
        .find(p => p.textContent.includes("No milestones found") || p.textContent.includes("No milestones created yet"));
    if (emptyMsg) emptyMsg.remove();

    let existingBtn = list.querySelector(`button[data-id="${m.milestone_id}"]`);
    let card = existingBtn ? existingBtn.closest(".rp-milestone") : null;

    if (card) {
        card.innerHTML = buildMilestoneCardHTML(m);
    } else {
        card = document.createElement("div");
        card.className = "rp-milestone";
        card.innerHTML = buildMilestoneCardHTML(m);
        list.appendChild(card);
    }

    lucide.createIcons();
}

// ============= STUDENTS TAB BUILD / UPDATE =============

function buildMilestoneNameHTML(m) {
    return `
        <div class="rp-milestone-name" data-milestone-id="${m.milestone_id}">
            <i data-lucide="flag"></i>
            ${m.title}
        </div>`;
}

function buildStudentRowHTML(s) {
    const statusHtml = s.all_completed
        ? '<span class="rp-status rp-status-completed">Completed</span>'
        : s.has_started
            ? '<span class="rp-status rp-status-progress">In Progress</span>'
            : '<span class="rp-status rp-status-draft">Not Started</span>';

    const milestonesHtml = s.milestones.length
        ? s.milestones.map(buildMilestoneNameHTML).join('')
        : '<span class="rp-empty">No milestone</span>';

    return `
        <td>
            <div class="rp-team-avatar rp-avatar-student">
                <i data-lucide="graduation-cap"></i>
            </div>
        </td>
        <td>
            <div class="rp-student-cell">
                <b>${s.name}</b>
                <div><span>${s.department_name}</span></div>
            </div>
        </td>
        <td>${milestonesHtml}</td>
        <td>
            <div class="rp-mini-bar">
                <div class="rp-mini-fill" style="width:${s.average_progress}%;"></div>
            </div>
            <span>${s.average_progress}%</span>
        </td>
        <td>${statusHtml}</td>
        <td>
            <button class="rp-btn rp-btn-view" onclick="viewStudent(this)" data-student-id="${s.student_id}">
                <i data-lucide="eye"></i>
                View
            </button>
        </td>
    `;
}

function upsertStudentsTab(studentsUpdate) {
    if (!studentsUpdate || !studentsUpdate.length) return;

    const table = document.querySelector('#rp-tab-students table.rp-table');
    if (!table) return;

    const emptyCell = Array.from(table.querySelectorAll('td'))
        .find(td => td.textContent.includes('No students assigned yet'));
    if (emptyCell) {
        const tr = emptyCell.closest('tr');
        if (tr) tr.remove();
    }

    studentsUpdate.forEach(s => {
        const viewBtn = table.querySelector(`button.rp-btn-view[data-student-id="${s.student_id}"]`);
        let row = viewBtn ? viewBtn.closest('tr') : null;

        if (row) {
            row.innerHTML = buildStudentRowHTML(s);
        } else {
            row = document.createElement('tr');
            row.innerHTML = buildStudentRowHTML(s);
            table.appendChild(row);
        }
    });

    lucide.createIcons();
}

// ============= MILESTONE MODAL CONTROLS =============

window.openMilestoneModal = function () {
    document.getElementById("milestoneForm").reset();
    if (window.statusChoices) {
        window.statusChoices.setChoiceByValue("not_started");
    }
    document.getElementById("milestoneId").value = "";
    clearMilestoneErrors();

    const todayStr = new Date().toLocaleDateString("en-CA");
    rebuildDateInput("milestoneStart", todayStr, "");
    rebuildDateInput("milestoneDeadline", todayStr, "");

    document.getElementById("milestoneModalTitle").innerHTML =
        '<i data-lucide="flag"></i> Add New Milestone';

    document.getElementById("saveMilestoneBtn").innerHTML =
        '<i data-lucide="save"></i> Save Milestone';

    document.getElementById("milestoneModal").classList.add("active");
    lucide.createIcons();
};

window.editMilestone = function (btn) {
    clearMilestoneErrors();

    document.getElementById("milestoneId").value = btn.dataset.id;
    document.getElementById("milestoneTitle").value = btn.dataset.title;
    document.getElementById("milestoneDescription").value = btn.dataset.description;
    document.getElementById("expectedPercentage").value = btn.dataset.expected;

    rebuildDateInput("milestoneStart", null, btn.dataset.start);
    rebuildDateInput("milestoneDeadline", null, btn.dataset.deadline);

    const currentStatus = btn.dataset.status;
    if (window.statusChoices) {
        window.statusChoices.clearChoices();
        if (currentStatus === "not_started") {
            window.statusChoices.setChoices([
                {
                    value: "in_progress",
                    label: "In Progress",
                    selected: true
                }
            ], "value", "label", true);

        } else if (currentStatus === "in_progress") {
            window.statusChoices.setChoices([
                {
                    value: "completed",
                    label: "Completed",
                    selected: true
                }
            ], "value", "label", true);
        } else if (currentStatus === "completed") {
            window.statusChoices.setChoices([
                {
                    value: "completed",
                    label: "Completed",
                    selected: true,
                    disabled: true
                }
            ], "value", "label", true);

        } else {
            window.statusChoices.setChoices([
                {
                    value: currentStatus,
                    label: btn.dataset.status,
                    selected: true,
                    disabled: true
                }
            ], "value", "label", true);
        }
    }
    document.getElementById("milestoneModalTitle").innerHTML =
        '<i data-lucide="edit"></i> Edit Milestone';

    document.getElementById("saveMilestoneBtn").innerHTML =
        '<i data-lucide="save"></i> Update Milestone';

    document.getElementById("milestoneModal").classList.add("active");
    lucide.createIcons();
};

window.closeMilestoneModal = function () {
    document.getElementById("milestoneForm").reset();

    if (window.statusChoices) {
        window.statusChoices.setChoiceByValue("not_started");
    }
    clearMilestoneErrors();
    document.getElementById("milestoneModal").classList.remove("active");
};

window.addEventListener("click", function (event) {
    const modal = document.getElementById("milestoneModal");
    if (event.target === modal) {
        closeMilestoneModal();
    }
});

// ============= TEAM REQUIRED ALERT =============

function showTeamAlert() {
    document.getElementById("teamAlert").style.display = "flex";
}

function closeTeamAlert() {
    document.getElementById("teamAlert").style.display = "none";
}

// ============= REPORT REVISION PROMPT =============

let activeRevisionForm = null;

function closeRevisionModal() {
    document.getElementById('revisionModal').classList.remove('active');
    activeRevisionForm = null;
}

function confirmRevision() {
    const feedbackField = document.getElementById('revisionFeedback');
    const feedback = feedbackField.value.trim();
    const errEl = document.getElementById('err-revisionFeedback');

    if (!feedback) {
        errEl.textContent = 'Feedback is required to request a revision.';
        return;
    }
    if (!/[A-Za-z]/.test(feedback)) {
        errEl.textContent = 'Feedback must contain at least one alphabet character.';
        return;
    }
    errEl.textContent = '';
    feedbackField.classList.remove('input-error');

    if (activeRevisionForm) {
        activeRevisionForm.querySelector('.rp-feedback-field').value = feedback;
        activeRevisionForm.submit();
    }
}

function requestRevision(btn) {
    activeRevisionForm = btn.closest('form');
    const field = document.getElementById('revisionFeedback');
    field.value = '';
    field.classList.remove('input-error');
    document.getElementById('err-revisionFeedback').textContent = '';
    document.getElementById('revisionModal').classList.add('active');
    if (window.lucide) lucide.createIcons();
}

window.addEventListener("click", function (event) {
    const modal = document.getElementById("revisionModal");
    if (event.target === modal) {
        closeRevisionModal();
    }
});

// ============= STUDENT DETAIL MODAL =============
function viewStudent(btn) {
    const studentId = btn.dataset.studentId;
    const url = studentDetailUrlTemplate.replace('999999', studentId);

    fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then(res => {
            if (!res.ok) {
                return res.text().then(text => { throw new Error(`${res.status}: ${text}`); });
            }
            return res.json();
        })
        .then(data => {
            document.getElementById('studentDetailName').textContent = data.name;
            document.getElementById('studentDetailEmail').textContent = data.email;
            document.getElementById('studentDetailDept').textContent = data.department;
            document.getElementById('studentDetailCount').textContent =
                data.completed_milestones + ' / ' + data.total_milestones;

            const fill = document.getElementById('studentDetailProgress');
            fill.style.width = data.overall_progress + '%';
            fill.textContent = data.overall_progress + '%';

            const list = document.getElementById('studentDetailMilestones');
            list.innerHTML = '';
            if (data.milestones.length === 0) {
                list.innerHTML = '<p class="rp-empty-message">No milestones assigned</p>';
            } else {
                data.milestones.forEach(m => {
                    const row = document.createElement('div');
                    row.className = 'rp-detail-milestone';
                    row.innerHTML = `
                        <div class="rp-detail-milestone-top">
                            <b>${m.title}</b>
                            <span class="rp-status rp-status-progress">${m.status}</span>
                        </div>
                        <div class="rp-progress-bar rp-progress-bar-sm">
                            <div class="rp-progress-fill" style="width:${m.progress}%;">${m.progress}%</div>
                        </div>
                        <p><i data-lucide="calendar"></i> Deadline: ${m.deadline}</p>
                    `;
                    list.appendChild(row);
                });
                if (window.lucide) lucide.createIcons();
            }
            const reportsStatusClassMap = {
                approved: "rp-status-completed",
                submitted: "rp-status-active",
                under_review: "rp-status-progress",
                revision: "rp-status-closed",
                rejected: "rp-status-closed",
            };

            const reportsList = document.getElementById('studentDetailReports');
            reportsList.innerHTML = '';
            if (data.reports.length === 0) {
                reportsList.innerHTML = '<p class="rp-empty-message">No reports submitted yet</p>';
            } else {
                data.reports.forEach(r => {
                    const statusClass = reportsStatusClassMap[r.status_raw] || "rp-status-draft";
                    const docsHtml = r.attachments.length
                        ? r.attachments.map(a => `
                            <a href="${a.url}" target="_blank" class="rp-file-link">
                                <i data-lucide="file-text"></i> ${a.name}
                            </a>`).join('')
                        : '<span class="rp-empty">No documents attached</span>';

                    const feedbackHtml = r.feedback
                        ? `<p class="rp-feedback-text">"${r.feedback}"</p>`
                        : '';

                    const row = document.createElement('div');
                    row.className = 'rp-detail-milestone';
                    row.innerHTML = `
                        <div class="rp-detail-milestone-top">
                            <b>${r.title}</b>
                            <span class="rp-status ${statusClass}">${r.status}</span>
                        </div>
                        <p><i data-lucide="flag"></i> Milestone: ${r.milestone}</p>
                        <p><i data-lucide="calendar"></i> Submitted: ${r.submitted_date} &nbsp; | &nbsp; Progress: ${r.progress}%</p>
                        <div class="rp-report-doc-list">${docsHtml}</div>
                        ${feedbackHtml}
                    `;
                    reportsList.appendChild(row);
                });
                if (window.lucide) lucide.createIcons();
            }
            document.getElementById('studentDetailModal').classList.add('active');
        })
        .catch(err => {
            console.error('Student detail load failed:', err);
            alert('Unable to load student details.');
        });
}

function closeStudentDetailModal() {
    document.getElementById('studentDetailModal').classList.remove('active');
}

// ============= LIVE UPDATES (WebSocket) =============

function currentResearchId() {
    const params = new URLSearchParams(window.location.search);
    return params.get("research");
}

window.addEventListener("milestone_started", function (e) {
    const d = e.detail;
    const rid = currentResearchId();
    if (rid && rid !== String(d.research_id)) return;

    upsertStudentsTab(d.students_update);
});

window.addEventListener("report_submitted", function (e) {
    const d = e.detail;
    const rid = currentResearchId();
    if (rid && rid !== String(d.research_id)) return;

    const table = document.querySelector("#rp-tab-reports table.rp-table");
    if (!table) return;

    const emptyCell = Array.from(table.querySelectorAll("td"))
        .find(td => td.textContent.includes("No pending reports"));
    if (emptyCell) {
        const tr = emptyCell.closest("tr");
        if (tr) tr.remove();
    }

    const csrfInput = document.querySelector('input[name=csrfmiddlewaretoken]');
    const csrfValue = csrfInput ? csrfInput.value : "";

    const row = document.createElement("tr");
    row.innerHTML = `
        <td>${escHtml(d.student_name)}</td>
        <td>${escHtml(d.milestone_title)}</td>
        <td>${escHtml(d.report_title)}</td>
        <td>
            ${d.attachment_url
                ? `<a href="${d.attachment_url}" target="_blank" class="rp-file-link"><i data-lucide="file-text"></i> ${escHtml(d.attachment_name)}</a>`
                : `<span class="rp-empty">No file attached</span>`}
        </td>
        <td class="rp-report-actions">
            <form method="POST" action="${d.approve_url}" class="rp-inline-form">
                <input type="hidden" name="csrfmiddlewaretoken" value="${csrfValue}">
                <input type="hidden" name="action" value="approve">
                <button type="submit" class="rp-btn rp-btn-approve">
                    <i data-lucide="check"></i> Approve
                </button>
            </form>
            <form method="POST" action="${d.approve_url}" class="rp-inline-form rp-revision-form">
                <input type="hidden" name="csrfmiddlewaretoken" value="${csrfValue}">
                <input type="hidden" name="action" value="revision">
                <input type="hidden" name="feedback" class="rp-feedback-field">
                <button type="button" class="rp-btn rp-btn-revision" onclick="requestRevision(this)">
                    <i data-lucide="rotate-ccw"></i> Revision
                </button>
            </form>
        </td>
    `;
    table.appendChild(row);
    if (window.lucide) lucide.createIcons();

    row.style.transition = "background-color 1.3s ease";
    row.style.backgroundColor = "#fff3cd";
    setTimeout(() => { row.style.backgroundColor = ""; }, 1400);
});

function escHtml(str) {
    const div = document.createElement("div");
    div.textContent = str == null ? "" : str;
    return div.innerHTML;
}