document.addEventListener("DOMContentLoaded", function () {
    if (window.lucide) lucide.createIcons();

    const researchSelect = document.getElementById("researchSelect");
    if (researchSelect) {
        new Choices(researchSelect, {
            searchEnabled: true,
            itemSelectText: "",
            shouldSort: false,
            allowHTML: false,
            placeholder: true,
            placeholderValue: "Select Research",
        });
        researchSelect.addEventListener("change", function () {
            this.form.submit();
        });
    }

    const reportForm = document.getElementById("reportForm");
    const baseReportActionTemplate = reportForm
        ? reportForm.getAttribute("action")
        : null;

    // ============= TABS  =============
    const tabs = document.querySelectorAll(".rp-tab");
    const TAB_STORAGE_KEY = "rpStudentActiveTab";

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

    if (reportForm) {
        reportForm.addEventListener("submit", function (e) {
            e.preventDefault();
            clearReportErrors();

            const submitBtn = document.getElementById("submitReportBtn");
            const originalHTML = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = "Submitting...";

            const assignmentId = window.currentReportAssignmentId;

            fetch(reportForm.action, {
                method: "POST",
                headers: { "X-Requested-With": "XMLHttpRequest" },
                body: new FormData(reportForm),
            })
                .then(res => res.json().then(data => ({ status: res.status, data })))
                .then(({ status, data }) => {
                    if (status === 200 && data.success) {
                        updateMilestoneCardAfterSubmit(assignmentId, data.assignment);
                        prependReportCard(data.report, assignmentId);
                        disableRevisionButton(assignmentId);
                        closeReportModal();
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalHTML;
                        if (window.lucide) lucide.createIcons();
                        return;
                    }
                    showReportErrors(data.errors || {});
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalHTML;
                })
                .catch(err => {
                    console.error("Report submit failed:", err);
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalHTML;
                    alert("Something went wrong. Please try again.");
                });
        });
    }

    window.openReportModal = function (assignmentId, milestoneTitle) {
        window.currentReportAssignmentId = assignmentId;
        if (reportForm && baseReportActionTemplate) {
            reportForm.setAttribute(
                "action",
                baseReportActionTemplate.replace(/\/0\/$/, "/" + assignmentId + "/")
            );
        }
        clearReportErrors();
        document.getElementById("reportMilestoneLabel").value = milestoneTitle;
        document.getElementById("reportModal").classList.add("active");
        if (window.lucide) lucide.createIcons();
    };

    function getCsrfToken() {
        const input = document.querySelector("#reportForm [name=csrfmiddlewaretoken]");
        return input ? input.value : "";
    }

    window.startWorking = function (btn, assignmentId) {
        if (btn.disabled) return;
        const originalHTML = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = "Starting...";

        const url = window.startWorkingUrlTemplate.replace(/\/0\/$/, "/" + assignmentId + "/");

        fetch(url, {
            method: "POST",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": getCsrfToken(),
            },
        })
            .then(res => res.json().then(data => ({ status: res.status, data })))
            .then(({ status, data }) => {
                if (status === 200 && data.success) {
                    updateMilestoneCardAfterStartWorking(assignmentId, data.assignment);
                    return;
                }
                btn.disabled = false;
                btn.innerHTML = originalHTML;
                alert(data.message || "Something went wrong. Please try again.");
            })
            .catch(err => {
                console.error("Start working failed:", err);
                btn.disabled = false;
                btn.innerHTML = originalHTML;
                alert("Something went wrong. Please try again.");
            });
    };
});

function clearReportErrors() {
    document.querySelectorAll("#reportForm .rp-error")
        .forEach(el => el.textContent = "");
    document.querySelectorAll("#reportForm .input-error")
        .forEach(el => el.classList.remove("input-error"));
}

function showReportErrors(errors) {
    const fieldToInput = {
        title: "reportTitle",
        description: "reportDescription",
        progress_percentage: "reportProgress",
        files: "reportFiles",
    };
    Object.keys(errors).forEach(function (field) {
        const errEl = document.getElementById("err-" + field);
        if (errEl) errEl.textContent = errors[field];
        const inputEl = document.getElementById(fieldToInput[field]);
        if (inputEl) inputEl.classList.add("input-error");
    });
}

window.closeReportModal = function () {
    document.getElementById("reportForm").reset();
    clearReportErrors();
    document.getElementById("reportModal").classList.remove("active");
};

window.addEventListener("click", function (event) {
    const modal = document.getElementById("reportModal");
    if (event.target === modal) closeReportModal();
});

// ============= LIVE UPDATE: MILESTONES TAB =============

function milestoneStatusClass(status) {
    const map = {
        completed: "rp-status-completed",
        submitted: "rp-status-progress",
        working: "rp-status-active",
        assigned: "rp-status-draft",
    };
    return map[status] || "rp-status-draft";
}

function updateMilestoneCardAfterStartWorking(assignmentId, assignmentData) {
    if (!assignmentId || !assignmentData) return;

    const card = document.querySelector(`.rp-milestone[data-assignment-id="${assignmentId}"]`);
    if (!card) return;

    const badge = card.querySelector(".rp-status");
    if (badge) {
        badge.className = "rp-status " + milestoneStatusClass(assignmentData.status);
        badge.textContent = assignmentData.status_display;
    }

    const btn = card.querySelector(".rp-btn-primary");
    if (btn) {
        const milestoneTitle = card.dataset.milestoneTitle || "";
        btn.disabled = false;
        btn.innerHTML = '<i data-lucide="upload"></i> Submit Report';
        btn.setAttribute("onclick", "");
        btn.onclick = function () {
            openReportModal(assignmentId, milestoneTitle);
        };
    }

    if (window.lucide) lucide.createIcons();
}

function updateMilestoneCardAfterSubmit(assignmentId, assignmentData) {
    if (!assignmentId || !assignmentData) return;

    const card = document.querySelector(`.rp-milestone[data-assignment-id="${assignmentId}"]`);
    if (!card) return;

    const badge = card.querySelector(".rp-status");
    if (badge) {
        badge.className = "rp-status " + milestoneStatusClass(assignmentData.status);
        badge.textContent = assignmentData.status_display;
    }

    const btn = card.querySelector(".rp-btn-primary");
    if (btn) {
        btn.innerHTML = '<i data-lucide="upload"></i> Submit Report';
    }
}

// ============= LIVE UPDATE: REPORTS TAB =============

function buildReportDetailPayload(r) {
    return {
        milestone: r.milestone_title,
        title: r.title,
        description: r.description || "",
        status: r.status_display,
        submitted: r.submitted_date,
        progress: r.progress,
        feedback: "",
        reviewed: "",
    };
}

function buildReportItemEl(r) {
    const statusClassMap = {
        approved: "rp-status-completed",
        under_review: "rp-status-progress",
        revision: "rp-status-closed",
        rejected: "rp-status-closed",
        submitted: "rp-status-active",
    };
    const statusClass = statusClassMap[r.status] || "rp-status-active";

    const attachmentsHtml = (r.attachments || []).map(a => `
        <a href="${a.url}" class="rp-file-link" target="_blank">
            <i data-lucide="file"></i> ${a.name}
        </a>`).join("");

    const div = document.createElement("div");
    div.className = "rp-report-item rp-clickable";
    div.dataset.reportId = r.report_id;
    div.innerHTML = `
        <div class="rp-report-top">
            <b>${r.milestone_title}</b>
            <span class="rp-status ${statusClass}">${r.status_display}</span>
        </div>
        <p>Report: ${r.title}</p>
        <p>Submitted: ${r.submitted_date}</p>
        <p>Progress: ${r.progress}%</p>
        ${attachmentsHtml}
    `;
    div.addEventListener("click", function () {
        openReportDetailModal(buildReportDetailPayload(r));
    });
    return div;
}

function prependReportCard(reportData, assignmentId) {
    if (!reportData) return;
    const panel = document.getElementById("rp-tab-reports");
    if (!panel) return;

    const emptyMsg = Array.from(panel.querySelectorAll(".rp-empty-message"))
        .find(el => el.textContent.toLowerCase().includes("no reports submitted"));
    if (emptyMsg) emptyMsg.remove();

    const el = buildReportItemEl(reportData);
    panel.insertBefore(el, panel.firstElementChild && panel.firstElementChild.tagName !== "H2"
        ? panel.firstElementChild
        : panel.children[1] || null);

    if (window.lucide) lucide.createIcons();
}

function disableRevisionButton(assignmentId) {
    if (!assignmentId) return;
    const btn = document.querySelector(
        `#rp-tab-feedback button[data-assignment-id="${assignmentId}"]`
    );
    if (!btn) return;
    btn.disabled = true;
    btn.classList.remove("rp-btn-primary");
    btn.classList.add("rp-btn-reset");
    btn.removeAttribute("onclick");
    btn.innerHTML = '<i data-lucide="check"></i> Revised Report Submitted';
}

// ============= REPORT DETAIL MODAL =============

window.openReportDetailModal = function (data) {
    document.getElementById("detailMilestone").textContent = data.milestone;
    document.getElementById("detailTitle").textContent = data.title;
    document.getElementById("detailDescription").textContent = data.description || "--";
    document.getElementById("detailStatus").textContent = data.status;
    document.getElementById("detailSubmitted").textContent = data.submitted;
    document.getElementById("detailProgress").textContent = data.progress + "%";

    const feedbackBlock = document.getElementById("detailFeedbackBlock");
    if (data.feedback) {
        feedbackBlock.style.display = "block";
        document.getElementById("detailFeedback").textContent = '"' + data.feedback + '"';
        document.getElementById("detailReviewed").textContent = data.reviewed || "--";
    } else {
        feedbackBlock.style.display = "none";
    }

    document.getElementById("reportDetailModal").classList.add("active");
    if (window.lucide) lucide.createIcons();
};

window.closeReportDetailModal = function () {
    document.getElementById("reportDetailModal").classList.remove("active");
};

window.addEventListener("click", function (event) {
    const modal = document.getElementById("reportDetailModal");
    if (event.target === modal) closeReportDetailModal();
});

// ============= LIVE UPDATES (WebSocket) =============

window.addEventListener("milestone_assigned", function (e) {
    const d = e.detail;
    const page = document.querySelector(".rp-page");
    if (!page || page.dataset.researchId !== String(d.research_id)) return;

    const panel = document.getElementById("rp-tab-milestones");
    if (!panel) return;

    const emptyMsg = document.getElementById("milestonesEmptyMsg");
    if (emptyMsg) emptyMsg.remove();

    const actionHtml = (d.milestone_status === "in_progress")
        ? `<button class="rp-btn rp-btn-primary" onclick="startWorking(this, '${d.assignment_id}')">
               <i data-lucide="play"></i>
               Start Working
           </button>`
        : `<button class="rp-btn rp-btn-reset" type="button" disabled title="Mentor hasn't started this milestone yet">
               <i data-lucide="clock"></i>
               Yet to start
           </button>`;

    const card = document.createElement("div");
    card.className = "rp-milestone";
    card.dataset.assignmentId = d.assignment_id;
    card.dataset.milestoneTitle = d.milestone_title;
    card.innerHTML = `
        <div class="rp-milestone-top">
            <h3>${escHtml(d.milestone_title)}</h3>
            <span class="rp-status ${milestoneStatusClass("assigned")}">Assigned</span>
        </div>
        <p><i data-lucide="file-text"></i> ${escHtml(d.milestone_description)}</p>
        <div class="rp-review">
            <p><i data-lucide="calendar"></i> Deadline: ${escHtml(d.deadline)}</p>
            <p><i data-lucide="chart-line"></i> Expected Contribution: ${escHtml(d.expected_percentage)}%</p>
        </div>
        <div class="rp-progress-bar rp-progress-bar-sm">
            <div class="rp-progress-fill" style="width:0%;">0%</div>
        </div>
        ${actionHtml}
    `;
    panel.appendChild(card);
    if (window.lucide) lucide.createIcons();
    flashEl(card);
});

window.addEventListener("report_reviewed", function (e) {
    const d = e.detail;
    const page = document.querySelector(".rp-page");
    if (!page || page.dataset.researchId !== String(d.research_id)) return;

    // ---- Milestones tab update ----
    const card = document.querySelector(`.rp-milestone[data-assignment-id="${d.assignment_id}"]`);
    if (card) {
        const badge = card.querySelector(".rp-status");
        const progressFill = card.querySelector(".rp-progress-fill");
        const actionBtn = card.querySelector(".rp-btn-primary, .rp-btn-completed, .rp-btn-warning, .rp-btn-reset");

        if (d.status === "approved") {
            if (badge) {
                badge.className = "rp-status " + milestoneStatusClass("completed");
                badge.textContent = "Your Work Approved";
            }
            if (progressFill) {
                progressFill.style.width = d.student_progress + "%";
                progressFill.textContent = d.student_progress + "%";
            }
            if (actionBtn) {
                if (d.milestone_status === "completed") {
                    actionBtn.outerHTML = `
                        <button class="rp-btn rp-btn-completed" type="button" disabled title="This milestone is already completed">
                            <i data-lucide="check"></i> Milestone Completed
                        </button>`;
                } else {
                    const milestoneTitle = card.dataset.milestoneTitle || "";
                    actionBtn.outerHTML = `<button class="rp-btn rp-btn-primary"><i data-lucide="upload"></i> Submit Report</button>`;
                    card.querySelector(".rp-btn-primary").onclick = function () {
                        openReportModal(d.assignment_id, milestoneTitle);
                    };
                }
            }
        } else {
            if (badge) {
                badge.className = "rp-status " + milestoneStatusClass("working");
                badge.textContent = "Working";
            }
            if (actionBtn && d.milestone_status !== "completed") {
                const milestoneTitle = card.dataset.milestoneTitle || "";
                actionBtn.innerHTML = '<i data-lucide="upload"></i> Upload Revised Report';
                actionBtn.onclick = function () {
                    openReportModal(d.assignment_id, milestoneTitle);
                };
            }
        }
        flashEl(card);
    }
    // ---- NEW: Reports tab status update ----
    if (d.report_id) {
        updateReportItemStatus(d.report_id, d.status, d.status_display);
    }
    // ---- NEW: Feedback tab entry ----
    if (d.feedback) {
        const feedbackPanel = document.getElementById("rp-tab-feedback");
        if (feedbackPanel) {
            const emptyMsg = Array.from(feedbackPanel.querySelectorAll(".rp-empty-message"))
                .find(el => el.textContent.toLowerCase().includes("no feedback yet"));
            if (emptyMsg) emptyMsg.remove();

            const existing = feedbackPanel.querySelector(`.rp-feedback-item[data-report-id="${d.report_id}"]`);
            if (existing) existing.remove();

            feedbackPanel.querySelectorAll(`button[data-assignment-id="${d.assignment_id}"]`).forEach(btn => {
                btn.disabled = true;
                btn.classList.remove("rp-btn-primary");
                btn.classList.add("rp-btn-reset");
                btn.removeAttribute("onclick");
                btn.innerHTML = '<i data-lucide="check"></i> Revised Report Submitted';
            });

            const el = buildFeedbackItemEl(d);
            const insertBefore = feedbackPanel.firstElementChild && feedbackPanel.firstElementChild.tagName !== "H2"
                ? feedbackPanel.firstElementChild
                : feedbackPanel.children[1] || null;
            feedbackPanel.insertBefore(el, insertBefore);
            flashEl(el);
        }
    }

    if (window.lucide) lucide.createIcons();
});

function escHtml(str) {
    const div = document.createElement("div");
    div.textContent = str == null ? "" : str;
    return div.innerHTML;
}

function flashEl(el) {
    el.style.transition = "background-color 1.5s ease";
    el.style.backgroundColor = "#fff3cd";
    setTimeout(() => { el.style.backgroundColor = ""; }, 1600);
}
function reportStatusClass(status) {
    const map = {
        approved: "rp-status-completed",
        under_review: "rp-status-progress",
        revision: "rp-status-closed",
        rejected: "rp-status-closed",
        submitted: "rp-status-active",
    };
    return map[status] || "rp-status-active";
}

function updateReportItemStatus(reportId, statusRaw, statusDisplay) {
    const item = document.querySelector(`.rp-report-item[data-report-id="${reportId}"]`);
    if (!item) return;
    const badge = item.querySelector(".rp-status");
    if (badge) {
        badge.className = "rp-status " + reportStatusClass(statusRaw);
        badge.textContent = statusDisplay;
    }
    flashEl(item);
}

function buildFeedbackItemEl(d) {
    const statusClass = d.status === "revision" ? "rp-status-closed" : "rp-status-completed";
    const div = document.createElement("div");
    div.className = "rp-feedback-item rp-clickable";
    div.dataset.reportId = d.report_id;
    div.innerHTML = `
        <div class="rp-report-top">
            <b>${escHtml(d.milestone_title)}</b>
            <span class="rp-status ${statusClass}">${escHtml(d.status_display)}</span>
        </div>
        <p class="rp-feedback-report-title">Report: ${escHtml(d.report_title)}</p>
        <p class="rp-feedback-text">"${escHtml(d.feedback)}"</p>
        <p>Reviewed: ${escHtml(d.reviewed_date || "--")}</p>
        ${d.status === "revision" ? `
        <button class="rp-btn rp-btn-primary" data-assignment-id="${d.assignment_id}"
                onclick="event.stopPropagation(); openReportModal('${d.assignment_id}', '${escHtml(d.milestone_title)}')">
            <i data-lucide="upload"></i> Upload Revised Report
        </button>` : ``}
    `;
    div.addEventListener("click", function () {
        openReportDetailModal({
            milestone: d.milestone_title,
            title: d.report_title,
            description: "",
            status: d.status_display,
            submitted: d.submitted_date,
            progress: d.student_progress,
            feedback: d.feedback,
            reviewed: d.reviewed_date,
        });
    });
    return div;
}