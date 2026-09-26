document.addEventListener('DOMContentLoaded', function () {
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    const tabs = document.querySelectorAll('#crdTabs .crd-tab');
    const panels = document.querySelectorAll('.crd-tab-panel');
    tabs.forEach(function (tab) {
        tab.addEventListener('click', function () {
            tabs.forEach(function (t) {
                t.classList.remove('active');
            });
            tab.classList.add('active');
            panels.forEach(function (panel) {
                panel.style.display = 'none';
            });
            const targetId = tab.getAttribute('data-target');
            const target = document.getElementById(targetId);
            if (target) {
                target.style.display = 'block';
            }
        });
    });

    const researchSelect = document.getElementById('committeeResearchSelect');
    if (researchSelect && typeof Choices !== 'undefined') {
        const researchChoices = new Choices(researchSelect, {
            searchEnabled: true,
            searchPlaceholderValue: 'Search research project...',
            itemSelectText: '',
            shouldSort: false,
            allowHTML: false,
            noResultsText: 'No research project found',
            noChoicesText: 'No research projects available',
            position: 'bottom',
            searchResultLimit: 50
        });
        researchSelect.addEventListener('change', function () {
            const researchId = this.value;
            if (researchId) {
                window.location.href =
                    '?research=' + encodeURIComponent(researchId);
            }
        });
    }
});

// ============= LIVE UPDATES (WebSocket) =============

function overviewCurrentResearchId() {
    const select = document.getElementById("committeeResearchSelect");
    return select ? select.value : null;
}

function escOverviewHtml(str) {
    const div = document.createElement("div");
    div.textContent = str == null ? "" : str;
    return div.innerHTML;
}

function flashOverviewEl(el) {
    el.style.transition = "background-color 1.4s ease";
    el.style.backgroundColor = "#fff3cd";
    setTimeout(() => { el.style.backgroundColor = ""; }, 1500);
}

// ---- New milestone created ----
window.addEventListener("milestone_created", function (e) {
    const d = e.detail;
    if (String(d.research_id) !== overviewCurrentResearchId()) return;

    const panel = document.getElementById("crd-tab-milestones");
    if (!panel) return;

    const emptyMsg = panel.querySelector(".rp-empty-message");
    if (emptyMsg) emptyMsg.remove();

    const statusClassMap = {
        completed: "rp-status-completed",
        in_progress: "rp-status-active",
        delayed: "rp-status-closed",
        not_started: "rp-status-draft",
    };
    const statusClass = statusClassMap[d.status] || "rp-status-draft";

    const assigneeChips = (d.assigned_students || []).map(function (s) {
        const chipStatusMap = {
            completed: "rp-status-completed",
            submitted: "rp-status-progress",
            working: "rp-status-active",
            assigned: "rp-status-draft",
        };
        const chipClass = chipStatusMap[s.status] || "rp-status-draft";
        return `
            <div class="crd-assignee-chip">
                <i data-lucide="graduation-cap"></i>
                ${escOverviewHtml(s.name)} \u2014 ${s.progress}%
                <span class="rp-status ${chipClass}">${escOverviewHtml(s.status_display)}</span>
            </div>`;
    }).join("");

    const card = document.createElement("div");
    card.className = "rp-milestone";
    card.innerHTML = `
        <div class="rp-milestone-top">
            <h3>${escOverviewHtml(d.title_text)}</h3>
            <span class="rp-status ${statusClass}">${escOverviewHtml(d.status_display)}</span>
        </div>
        <p><i data-lucide="file-text"></i> ${escOverviewHtml(d.description)}</p>
        <div class="rp-review">
            <p><i data-lucide="calendar"></i> <span>Start: ${escOverviewHtml(d.start_date)} | Deadline: ${escOverviewHtml(d.deadline)}</span></p>
            <p><i data-lucide="chart-line"></i><span>Expected Contribution: ${d.expected_percentage}% </span></p>
        </div>
        ${assigneeChips ? `<div class="crd-assignee-list">${assigneeChips}</div>` : ""}
    `;
    panel.appendChild(card);
    if (window.lucide) lucide.createIcons();
    flashOverviewEl(card);
});

// ---- New funding entry (reuses the same event as committee_funding.js) ----
window.addEventListener("research_funding_added", function (e) {
    const d = e.detail;
    if (String(d.research_id) !== overviewCurrentResearchId()) return;

    const statCards = document.querySelectorAll("#crd-tab-funding .rp-stat-card b");
    if (statCards[0]) statCards[0].textContent = `$${d.estimated_amount}`;
    if (statCards[1]) statCards[1].textContent = `$${d.received_amount}`;

    const tbody = document.querySelector("#crd-tab-funding table.crd-table tbody");
    if (!tbody) return;

    if (tbody.querySelector(`tr[data-funding-id="${d.funding_id}"]`)) return;

    if (statCards[2]) statCards[2].textContent = (parseInt(statCards[2].textContent, 10) || 0) + 1;

    const emptyRow = tbody.querySelector(".crd-table-empty");
    if (emptyRow) {
        const tr = emptyRow.closest("tr");
        if (tr) tr.remove();
    }

    const row = document.createElement("tr");
    row.dataset.fundingId = d.funding_id;
    row.innerHTML = `
        <td>${escOverviewHtml(d.funding_source)}</td>
        <td>${escOverviewHtml(d.sponsor)}</td>
        <td>$${escOverviewHtml(d.amount)}</td>
        <td>${escOverviewHtml(d.award_date)}</td>
    `;
    tbody.appendChild(row);
    flashOverviewEl(row);
});

// ---- New presentation added ----
window.addEventListener("presentation_created", function (e) {
    const d = e.detail;
    if (String(d.research_id) !== overviewCurrentResearchId()) return;

    const statCards = document.querySelectorAll("#crd-tab-presentations .rp-stat-card b");
    if (statCards[0]) statCards[0].textContent = (parseInt(statCards[0].textContent, 10) || 0) + 1;
    if (d.award && statCards[1]) statCards[1].textContent = (parseInt(statCards[1].textContent, 10) || 0) + 1;

    const grid = document.querySelector("#crd-tab-presentations .rp-presentation-grid");
    if (!grid) return;

    const emptyMsg = grid.querySelector(".rp-empty-message");
    if (emptyMsg) emptyMsg.remove();

    const card = document.createElement("div");
    card.className = "rp-presentation-card crd-no-hover-lift";
    card.innerHTML = `
        <div class="rp-presentation-top">
            <i data-lucide="presentation"></i>
            ${d.award ? `<span class="rp-award-badge">${escOverviewHtml(d.award)}</span>` : ""}
        </div>
        <p class="rp-presentation-name">${escOverviewHtml(d.event_name)}</p>
        <p class="rp-presentation-date">${escOverviewHtml(d.presentation_date)}</p>
        ${d.certificate_url
            ? `<a href="${d.certificate_url}" target="_blank" class="rp-file-link"><i data-lucide="file-text"></i> View Certificate</a>`
            : ""}
    `;
    grid.appendChild(card);
    if (window.lucide) lucide.createIcons();
    flashOverviewEl(card);
});