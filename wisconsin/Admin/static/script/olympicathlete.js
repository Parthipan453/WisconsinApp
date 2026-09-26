/*  kali's code */

(function () {
    "use strict";

    const ATHLETES_API_URL = "/dashboard/olympics/athletes/data/";

    const STATUS_META = {
        PENDING:       { label: "Pending",       badge: "oly-badge--pending" },
        QUALIFIED:     { label: "Qualified",     badge: "oly-badge--qualified" },
        SELECTED:      { label: "Selected",      badge: "oly-badge--selected" },
        PARTICIPATED:  { label: "Participated",  badge: "oly-badge--participated" },
        RETIRED:       { label: "Retired",       badge: "oly-badge--retired" },
        NOT_QUALIFIED: { label: "Not Qualified", badge: "oly-badge--not_qualified" },
    };

    let athletes = [];
    let filtered = [];
 
    
    function fetchAthletes() { 
        return fetch(ATHLETES_API_URL, {
            method: "GET",
            headers: { "X-Requested-With": "XMLHttpRequest" },
        })
            .then((res) => {
                if (!res.ok) throw new Error(`Request failed with status ${res.status}`);
                return res.json();
            })
            .then((data) => data)
            .catch((err) => {
                console.error("[Olympics] Failed to load athletes:", err);
                return { results: [], qualification_progress: [], recent_updates: [] };
            });
    }

   
    function escapeHtml(str) {
        if (str === null || str === undefined) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    function statusBadge(statusKey) {
        const meta = STATUS_META[statusKey] || { label: statusKey || "—", badge: "oly-badge--pending" };
        return `<span class="oly-badge ${meta.badge}">${escapeHtml(meta.label)}</span>`;
    }

    function formatDate(value) {
        if (!value) return "—";
        const d = new Date(value);
        if (isNaN(d)) return value;
        return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
    }

   
    function renderStats(list) {
        const total = list.length;
        const qualified = list.filter((a) => a.olympic_status === "QUALIFIED").length;
        const selected = list.filter((a) => a.olympic_status === "SELECTED").length;
        const participated = list.filter((a) => a.olympic_status === "PARTICIPATED").length;
        const retired = list.filter((a) => a.olympic_status === "RETIRED").length;
        const active = list.filter((a) => a.is_active).length;
        const rankedAthletes = list.filter((a) => typeof a.world_ranking === "number");
        const avgRanking = rankedAthletes.length
            ? Math.round(rankedAthletes.reduce((sum, a) => sum + a.world_ranking, 0) / rankedAthletes.length)
            : "—";

        const map = {
            olyStatTotal: total,
            olyStatQualified: qualified,
            olyStatSelected: selected,
            olyStatParticipated: participated,
            olyStatRetired: retired,
            olyStatActive: active,
            olyStatRanking: avgRanking,
        };

        Object.keys(map).forEach((id) => {
            const el = document.getElementById(id);
            if (el) el.textContent = map[id];
        });
    }

   
    function renderTable(list) {
        const tbody = document.getElementById("olyTableBody");
        const emptyState = document.getElementById("olyEmptyState");
        const countEl = document.getElementById("olyTableCount");
        if (!tbody) return;

        if (countEl) countEl.textContent = `${list.length} athlete${list.length === 1 ? "" : "s"}`;

        if (!list.length) {
            tbody.innerHTML = "";
            if (emptyState) emptyState.classList.add("show");
            return;
        }
        if (emptyState) emptyState.classList.remove("show");

        tbody.innerHTML = list
            .map((a) => {
                const rankBadge = a.world_ranking
                    ? `<span class="oly-rank ${a.world_ranking <= 5 ? "oly-rank--top" : ""}">
                            ${a.world_ranking <= 5 ? '<i data-lucide="star"></i>' : ""}#${a.world_ranking}
                       </span>`
                    : `<span class="text-muted">Unranked</span>`;

                return `
                <tr>
                    <td data-label="Athlete">
                        <div class="oly-athlete-cell">
                            <img class="oly-avatar" src="${escapeHtml(a.photo)}" alt="${escapeHtml(a.name)}">
                            <div>
                                <div class="oly-athlete-cell__name">${escapeHtml(a.name)}</div>
                                <div class="oly-athlete-cell__sub">${escapeHtml(a.event_name)}</div>
                            </div>
                        </div>
                    </td>
                    <td data-label="Athlete #">${escapeHtml(a.athlete_number)}</td>
                    <td data-label="Sport">${escapeHtml(a.sport)}</td>
                    <td data-label="Team">${escapeHtml(a.team)}</td>
                    <td data-label="Coach">${escapeHtml(a.coach)}</td>
                    <td data-label="Nationality">${escapeHtml(a.nationality)}</td>
                    <td data-label="Target Olympics">${escapeHtml(a.target_olympics)}</td>
                    <td data-label="Event">${escapeHtml(a.event_name)}</td>
                    <td data-label="Category">${escapeHtml(a.event_category === "TEAM" ? "Team" : "Individual")}</td>
                    <td data-label="World Ranking">${rankBadge}</td>
                    <td data-label="Qualification">${statusBadge(a.qualification_status)}</td>
                    <td data-label="Olympic Status">${statusBadge(a.olympic_status)}</td>
                    <td data-label="Personal Best">${escapeHtml(a.personal_best)}</td>
                    <td data-label="Active">
                        <span class="oly-badge ${a.is_active ? "oly-badge--active" : "oly-badge--inactive"}">
                            ${a.is_active ? "Active" : "Inactive"}
                        </span>
                    </td>
                    <td data-label="Actions">
                        <div class="oly-actions-cell">
                            <button type="button" class="oly-icon-btn oly-icon-btn--view" data-action="view" data-id="${a.id}" aria-label="View athlete">
                                <i data-lucide="eye"></i>
                            </button>
                            ${window.OLY_CAN_UPDATE_ATHLETE ? `
                            <button type="button" class="oly-icon-btn oly-icon-btn--edit" data-action="edit" data-id="${a.id}" data-uuid="${a.uuid}" aria-label="Edit athlete">
                                <i data-lucide="pencil"></i>
                            </button>
                            ` : ""}
                        </div>
                    </td>
                </tr>`;
            })
            .join("");

        if (window.lucide) window.lucide.createIcons();
    }

    
    function applyFilters() {
        const q = (document.getElementById("olySearchInput")?.value || "").trim().toLowerCase();
        const statusVal = document.getElementById("olyStatusFilter")?.value || "";
        const sportVal = document.getElementById("olySportFilter")?.value || "";
        const categoryVal = document.getElementById("olyCategoryFilter")?.value || "";
        const qualVal = document.getElementById("olyQualificationFilter")?.value || "";

        filtered = athletes.filter((a) => {
            const matchesSearch =
                !q ||
                a.name.toLowerCase().includes(q) ||
                a.athlete_number.toLowerCase().includes(q) ||
                a.nationality.toLowerCase().includes(q) ||
                a.event_name.toLowerCase().includes(q);

            const matchesStatus = !statusVal || a.olympic_status === statusVal;
            const matchesSport = !sportVal || a.sport === sportVal;
            const matchesCategory = !categoryVal || a.event_category === categoryVal;
            const matchesQual = !qualVal || a.qualification_status === qualVal;

            return matchesSearch && matchesStatus && matchesSport && matchesCategory && matchesQual;
        });

        renderTable(filtered);
    }

    function populateSportFilter(list) {
        const select = document.getElementById("olySportFilter");
        if (!select) return;
        const sports = [...new Set(list.map((a) => a.sport))].sort();
        sports.forEach((sport) => {
            const opt = document.createElement("option");
            opt.value = sport;
            opt.textContent = sport;
            select.appendChild(opt);
        });

        const sportSelect = document.getElementById("olySportFilter");

        if (sportSelect.choices) {
            sportSelect.choices.destroy();
        }

        sportSelect.choices = new Choices(sportSelect, {
            searchEnabled: true,
            shouldSort: false,
            itemSelectText: "",
            searchPlaceholderValue: "Search..."
        });


    }

   
    function openAthleteModal(id) {
        const a = athletes.find((x) => x.id === Number(id));
        if (!a) return;

        const set = (id_, val) => {
            const el = document.getElementById(id_);
            if (el) el.textContent = val;
        };

        document.getElementById("olyModalAvatar").src = a.photo;
        set("olyModalName", a.name);
        set("olyModalSub", `${a.sport} · ${a.athlete_number}`);

        set("olyModalNationality", a.nationality);
        set("olyModalTeam", a.team);
        set("olyModalCoach", a.coach);
        set("olyModalGoverning", a.governing_body);

        set("olyModalTarget", a.target_olympics);
        set("olyModalEvent", a.event_name);
        set("olyModalCategory", a.event_category === "TEAM" ? "Team" : "Individual");
        set("olyModalRanking", a.world_ranking ? `#${a.world_ranking}` : "Unranked");

        set("olyModalQualDate", formatDate(a.qualification_date));
        set("olyModalQualScore", a.qualification_score || "—");
        set("olyModalQualStandard", a.qualification_standard || "—");
        document.getElementById("olyModalQualStatus").innerHTML = statusBadge(a.qualification_status);

        set("olyModalPersonalBest", a.personal_best || "N/A");
        document.getElementById("olyModalOlympicStatus").innerHTML = statusBadge(a.olympic_status);
        document.getElementById("olyModalActiveStatus").innerHTML =
            `<span class="oly-badge ${a.is_active ? "oly-badge--active" : "oly-badge--inactive"}">${a.is_active ? "Active" : "Inactive"}</span>`;

        set("olyModalBio", a.biography || "No biography on file yet.");

        if (window.lucide) window.lucide.createIcons();

        const modalEl = document.getElementById("olyAthleteModal");
        if (modalEl && window.bootstrap) {
            const modal = window.bootstrap.Modal.getOrCreateInstance(modalEl);
            modal.show();
        }
    }


    function bindEvents() {
        ["olySearchInput", "olyStatusFilter", "olySportFilter", "olyCategoryFilter", "olyQualificationFilter"].forEach(
            (id) => {
                const el = document.getElementById(id);
                if (!el) return;
                el.addEventListener(el.tagName === "SELECT" ? "change" : "input", applyFilters);
            }
        );

        document.getElementById("olyFilterBtn")?.addEventListener("click", applyFilters);

        document.getElementById("olyRefreshBtn")?.addEventListener("click", () => {
            document.getElementById("olySearchInput").value = "";
            ["olyStatusFilter", "olySportFilter", "olyCategoryFilter", "olyQualificationFilter"].forEach((id) => {
                const el = document.getElementById(id);
                if (el) el.value = "";
            });
            applyFilters();
        });

        
        document.getElementById("olyExportBtn")?.addEventListener("click", () => {
            console.info("[Olympics] Export clicked — hook up to backend export endpoint.");
        });
        document.getElementById("olyAddAthleteBtn")?.addEventListener("click", () => {
            console.info("[Olympics] Add Athlete clicked — hook up to athlete creation flow.");
        });

        document.getElementById("olyTableBody")?.addEventListener("click", (e) => {
            const btn = e.target.closest("button[data-action]");
            if (!btn) return;
            const { action, id } = btn.dataset;

            if (action === "view") {
                openAthleteModal(id);
            } else if (action === "edit") {
                 const uuid = btn.dataset.uuid;
                if (uuid && window.OLY_EDIT_ATHLETE_URL_TEMPLATE) {
                    window.location.href = window.OLY_EDIT_ATHLETE_URL_TEMPLATE.replace(
                        "00000000-0000-0000-0000-000000000000",
                        uuid
                    );
                }
            } else if (action === "delete") {
                console.info(`[Olympics] Delete clicked for athlete #${id} — hook up to delete endpoint.`);
            }
        });
    }

    function initToolbarChoices() {

    if (!window.Choices) return;

    [
        "#olyStatusFilter",
        "#olySportFilter",
        "#olyCategoryFilter",
        "#olyQualificationFilter"
    ].forEach(selector => {

        const select = document.querySelector(selector);

        if (!select) return;

        new Choices(select, {
            searchEnabled: true,
            searchChoices: true,
            shouldSort: false,
            itemSelectText: "",
            placeholder: true,
            searchPlaceholderValue: "Search...",
            position: "auto"
        });

    });

}


   
    function init() {
        fetchAthletes().then((payload) => {
            athletes = payload.results || [];
            filtered = athletes;
            populateSportFilter(athletes);
            initToolbarChoices();
            renderStats(athletes);
            renderTable(filtered);
            renderQualificationProgress(payload.qualification_progress || []);
            renderRecentUpdates(payload.recent_updates || []);
            bindEvents();

            if (window.lucide) window.lucide.createIcons();
            if (window.AOS) window.AOS.refresh();
        });
    }

    document.addEventListener("DOMContentLoaded", init);


    function renderQualificationProgress(progressList) {
    const container = document.getElementById("olyQualificationProgress");
    if (!container) return;

    if (!progressList || !progressList.length) {
        container.innerHTML = `<p class="text-muted">No sports data available.</p>`;
        return;
    }

    container.innerHTML = progressList
        .map((p) => `
            <div class="oly-progress-item">
                <div class="oly-progress-item__top">
                    <span>${escapeHtml(p.sport)}</span>
                    <span>${p.percentage}%</span>
                </div>
                <div class="oly-progress-bar">
                    <div class="oly-progress-bar__fill" style="width:${p.percentage}%"></div>
                </div>
            </div>`)
        .join("");
}

function renderRecentUpdates(updates) {
    const container = document.getElementById("olyRecentUpdates");
    if (!container) return;

    if (!updates || !updates.length) {
        container.innerHTML = `<p class="text-muted">No recent updates.</p>`;
        return;
    }

    container.innerHTML = updates
        .map((u) => `
            <div class="oly-update">
                <div class="oly-update__text">${escapeHtml(u.text)}</div>
                <div class="oly-update__time">${escapeHtml(u.time)}</div>
            </div>`)
        .join("");
}



})();