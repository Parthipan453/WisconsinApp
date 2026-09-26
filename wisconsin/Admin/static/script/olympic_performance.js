/* kali's code */


(function () { 
    "use strict";

    

    let OP_DATA = [];
    let OP_TABLE_DATA = [];
 
    const state = { data: OP_DATA.slice(), search: "", level: "", medal: "", status: "", sortKey: "competition_date", sortDir: "desc", page: 1, pageSize: 5, viewArchived: false };

    function getCookie(name) {
        const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
        return match ? decodeURIComponent(match[2]) : null;
    }

    const $ = (sel, ctx) => (ctx || document).querySelector(sel);
    const $$ = (sel, ctx) => Array.from((ctx || document).querySelectorAll(sel));

   
    function initials(name) {
        return name.split(" ").map(p => p[0]).slice(0, 2).join("").toUpperCase();
    }

    function formatDate(dateStr) {
        const d = new Date(dateStr + "T00:00:00");
        return d.toLocaleDateString("en-US", { month: "short", day: "2-digit", year: "numeric" });
    }

    function monthShort(dateStr) {
        return new Date(dateStr + "T00:00:00").toLocaleDateString("en-US", { month: "short" });
    }

    function dayNum(dateStr) {
        return new Date(dateStr + "T00:00:00").getDate();
    }

    function daysUntil(dateStr) {
        const now = new Date(); now.setHours(0, 0, 0, 0);
        const target = new Date(dateStr + "T00:00:00");
        return Math.round((target - now) / 86400000);
    }

    function medalBadge(medal) {
        const map = {
            GOLD: { cls: "op-badge--gold", icon: "medal", label: "Gold" },
            SILVER: { cls: "op-badge--silver", icon: "medal", label: "Silver" },
            BRONZE: { cls: "op-badge--bronze", icon: "medal", label: "Bronze" },
            NONE: { cls: "op-badge--none", icon: "minus-circle", label: "No Medal" },
        };
        const m = map[medal] || map.NONE;
        return `<span class="op-badge ${m.cls}"><i data-lucide="${m.icon}"></i>${m.label}</span>`;
    }

    function levelBadge(level) {
        const map = {
            OLYMPICS: { cls: "op-badge--level-olympics", icon: "flag" },
            INTERNATIONAL: { cls: "op-badge--level-international", icon: "globe" },
            NATIONAL: { cls: "op-badge--level-national", icon: "landmark" },
            STATE: { cls: "op-badge--level-state", icon: "map-pin" },
        };
        const m = map[level] || map.STATE;
        const label = level.charAt(0) + level.slice(1).toLowerCase();
        return `<span class="op-badge ${m.cls}"><i data-lucide="${m.icon}"></i>${label}</span>`;
    }

    function statusBadge(status) {
        const map = {
            COMPLETED: { cls: "op-badge--status-completed", icon: "check-circle-2" },
            SCHEDULED: { cls: "op-badge--status-scheduled", icon: "clock" },
            WITHDRAWN: { cls: "op-badge--status-withdrawn", icon: "circle-minus" },
            DISQUALIFIED: { cls: "op-badge--status-disqualified", icon: "x-circle" },
        };
        const m = map[status] || map.SCHEDULED;
        const label = status.charAt(0) + status.slice(1).toLowerCase();
        return `<span class="op-badge ${m.cls}"><i data-lucide="${m.icon}"></i>${label}</span>`;
    }

    function refreshIcons() {
        if (window.lucide && typeof window.lucide.createIcons === "function") {
            window.lucide.createIcons();
        }
    }

   
    function animateCount(el, target, opts) {
        opts = opts || {};
        const duration = opts.duration || 1000;
        const decimals = opts.decimals || 0;
        const start = 0;
        const startTime = performance.now();
        function tick(now) {
            const p = Math.min((now - startTime) / duration, 1);
            const eased = 1 - Math.pow(1 - p, 3);
            const val = start + (target - start) * eased;
            el.textContent = decimals ? val.toFixed(decimals) : Math.round(val).toLocaleString();
            if (p < 1) requestAnimationFrame(tick);
            else el.textContent = decimals ? target.toFixed(decimals) : target.toLocaleString();
        }
        requestAnimationFrame(tick);
    }

 
   

    function toast(msg, icon, corner) {
        const stack = $("#opToastStack");
        if (!stack) return;
        const el = document.createElement("div");
        el.className = "op-toast" + (corner === "top-right" ? " op-toast--corner-tr" : "");
        el.innerHTML = `<i data-lucide="${icon || 'info'}"></i><span>${msg}</span>`;
        stack.appendChild(el);
        refreshIcons();
        setTimeout(() => { el.style.opacity = "0"; el.style.transform = "translateX(30px)"; setTimeout(() => el.remove(), 300); }, 2600);
    }


    function computeMetrics(data) {
        const completed = data.filter(d => d.participation_status === "COMPLETED");
        const gold = data.filter(d => d.medal === "GOLD").length;
        const silver = data.filter(d => d.medal === "SILVER").length;
        const bronze = data.filter(d => d.medal === "BRONZE").length;
        const intl = data.filter(d => d.competition_level === "INTERNATIONAL" || d.competition_level === "OLYMPICS").length;
        const olympicEvents = data.filter(d => d.competition_level === "OLYMPICS").length;
        const ranked = data.filter(d => typeof d.ranking === "number");
        const avgRank = ranked.length ? (ranked.reduce((a, b) => a + b.ranking, 0) / ranked.length) : 0;
        const activeParticipants = new Set(data.map(d => d.athlete)).size;
        const countries = new Set(data.map(d => d.host_country)).size;
        return { total: data.length, gold, silver, bronze, medals: gold + silver + bronze, intl, olympicEvents, avgRank, activeParticipants, countries, completed: completed.length };
    }

    async function openPerformanceViewModal(uuid) {
        const modalEl = $("#opViewModal");
        if (!modalEl || !window.bootstrap) return;
        try {
            const res = await fetch(`/dashboard/olympics/performances/${uuid}/`);
            const json = await res.json();
            if (!json.ok) { toast("Could not load performance details", "alert-triangle"); return; }
            renderPerformanceModal(json.result);
            const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
            modal.show();
        } catch (err) {
            console.error("Failed to load performance detail", err);
            toast("Could not load performance details", "alert-triangle");
        }
    }

    function renderPerformanceModal(d) {
        $("#opvAthletePhoto").src = d.athlete_photo || "";
        $("#opvAthleteName").textContent = d.athlete;
        $("#opvAthleteNo").textContent = d.athlete_no;
        $("#opvCompetitionName").textContent = d.competition_name;
        $("#opvEventName").textContent = d.event_name;
        $("#opvCompetitionDate").textContent = d.competition_date ? formatDate(d.competition_date) : "—";
        $("#opvHostCity").textContent = d.host_city;
        $("#opvHostCountry").textContent = d.host_country;
        $("#opvScoreTime").textContent = d.score_time || "—";
        $("#opvRanking").textContent = d.ranking ?? "—";
        $("#opvRemarks").textContent = d.remarks || "No remarks recorded.";
        $("#opvCreatedAt").textContent = d.created_at || "—";
        $("#opvUpdatedAt").textContent = d.updated_at || "—";
        $("#opvCompetitionLevel").innerHTML = levelBadge(d.competition_level);
        $("#opvMedal").innerHTML = medalBadge(d.medal);
        $("#opvStatus").innerHTML = statusBadge(d.participation_status);
        refreshIcons();
    }


    function renderHero(metrics) {
        animateCount($("#heroStatTotal"), metrics.total);
        animateCount($("#heroStatMedals"), metrics.medals);
        animateCount($("#heroStatCountries"), metrics.countries);
        animateCount($("#heroStatRank"), metrics.avgRank, { decimals: 1 });
    }


    function renderStatCards(metrics) {
        const cards = [
            { icon: "activity", color: "#c5050c", label: "Total Performances", value: metrics.total, trend: "+12%", up: true, bar: 100 },
            { icon: "medal", color: "#d4af37", label: "Gold Medals", value: metrics.gold, trend: "+2", up: true, bar: Math.min(100, metrics.gold * 12) },
            { icon: "medal", color: "#8f97a3", label: "Silver Medals", value: metrics.silver, trend: "+1", up: true, bar: Math.min(100, metrics.silver * 12) },
            { icon: "medal", color: "#c97a3d", label: "Bronze Medals", value: metrics.bronze, trend: "0", up: true, bar: Math.min(100, metrics.bronze * 12) },
            { icon: "globe", color: "#2563eb", label: "International Competitions", value: metrics.intl, trend: "+4", up: true, bar: Math.min(100, metrics.intl * 8) },
            { icon: "flag", color: "#17a568", label: "Olympic Events", value: metrics.olympicEvents, trend: "+3", up: true, bar: Math.min(100, metrics.olympicEvents * 20) },
            { icon: "trending-up", color: "#d97706", label: "Average Ranking", value: metrics.avgRank.toFixed(1), trend: "▼ better", up: true, bar: Math.max(10, 100 - metrics.avgRank * 10) },
            { icon: "users", color: "#c5050c", label: "Active Participants", value: metrics.activeParticipants, trend: "+3", up: true, bar: Math.min(100, metrics.activeParticipants * 10) },
        ];
        const grid = $("#opStatsGrid");
        grid.innerHTML = cards.map((c, i) => `
            <div class="op-card op-stat" style="--op-stat-color:${c.color}; animation-delay:${i * 0.05}s" data-op-animate>
                <div class="op-stat__top">
                    <div class="op-stat__icon"><i data-lucide="${c.icon}"></i></div>
                    <span class="op-stat__trend ${c.up ? '' : 'down'}"><i data-lucide="${c.up ? 'arrow-up-right' : 'arrow-down-right'}"></i>${c.trend}</span>
                </div>
                <div class="op-stat__value" data-count="${c.value}">${c.value}</div>
                <div class="op-stat__label">${c.label}</div>
                <div class="op-stat__bar"><span style="width:${c.bar}%"></span></div>
            </div>
        `).join("");
        refreshIcons();
        requestAnimationFrame(() => $$(".op-stat__bar span", grid).forEach(s => { s.style.width = s.style.width; }));
    }

 
    let donutChart, rankChart;
    function renderMedalDonut(metrics) {
        const ctx = $("#opMedalDonut");
        const values = [metrics.gold, metrics.silver, metrics.bronze];
        $("#opDonutCenterN").textContent = metrics.medals;
        if (donutChart) donutChart.destroy();
        donutChart = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: ["Gold", "Silver", "Bronze"],
                datasets: [{ data: values, backgroundColor: ["#d4af37", "#aab2bd", "#c97a3d"], borderWidth: 0, hoverOffset: 6 }]
            },
            options: {
                cutout: "72%",
                plugins: { legend: { display: false }, tooltip: { enabled: true } },
                animation: { animateRotate: true, duration: 1000 }
            }
        });
        const legendData = [
            { dot: "#d4af37", label: "Gold Medals", val: metrics.gold },
            { dot: "#aab2bd", label: "Silver Medals", val: metrics.silver },
            { dot: "#c97a3d", label: "Bronze Medals", val: metrics.bronze },
        ];
        $("#opMedalLegend").innerHTML = legendData.map(l => `
            <div class="op-medal-legend__row">
                <span class="op-medal-legend__dot" style="background:${l.dot}"></span>
                <span class="lbl">${l.label}</span>
                <span class="val">${l.val}</span>
            </div>
        `).join("");
    }


    function renderRankChart(data) {
        const ranked = data.filter(d => typeof d.ranking === "number")
            .sort((a, b) => new Date(a.competition_date) - new Date(b.competition_date));
        const ctx = $("#opRankChart");
        if (rankChart) rankChart.destroy();
        rankChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: ranked.map(d => formatDate(d.competition_date)),
                datasets: [{
                    label: "Ranking",
                    data: ranked.map(d => d.ranking),
                    borderColor: "#c5050c",
                    backgroundColor: "rgba(197,5,12,.12)",
                    tension: .35,
                    fill: true,
                    pointRadius: 4,
                    pointBackgroundColor: "#c5050c",
                }]
            },
            options: {
                scales: {
                    y: { reverse: true, ticks: { stepSize: 1 }, grid: { color: "#eef0f6" } },
                    x: { grid: { display: false } }
                },
                plugins: { legend: { display: false } },
                animation: { duration: 1000 }
            }
        });
    }

  
    function renderCountries(data) {
        const counts = {};
        data.forEach(d => { counts[d.host_country] = (counts[d.host_country] || 0) + 1; });
        const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 6);
        const max = entries.length ? entries[0][1] : 1;
        const flagFor = (country) => (data.find(d => d.host_country === country) || {}).flag || "🏳️";
        $("#opCountryList").innerHTML = entries.map(([country, count]) => `
            <div class="op-country-row">
                <span class="op-country-flag">${flagFor(country)}</span>
                <div class="op-country-info">
                    <div class="top"><span>${country}</span><span>${count} entries</span></div>
                    <div class="op-country-track"><span style="width:${(count / max) * 100}%"></span></div>
                </div>
            </div>
        `).join("");
    }

  
    function renderHighlights(data) {
        const completed = data.filter(d => d.participation_status === "COMPLETED");
        const bestRank = completed.filter(d => typeof d.ranking === "number").sort((a, b) => a.ranking - b.ranking)[0];
        const latestGold = completed.filter(d => d.medal === "GOLD").sort((a, b) => new Date(b.competition_date) - new Date(a.competition_date))[0];
        const mostRecent = completed.sort((a, b) => new Date(b.competition_date) - new Date(a.competition_date))[0];
        const items = [
            bestRank && { icon: "trophy", title: `Best World Ranking — #${bestRank.ranking}`, sub: `${bestRank.athlete} · ${bestRank.event_name}` },
            latestGold && { icon: "medal", title: `Latest Gold Medal`, sub: `${latestGold.athlete} · ${latestGold.competition_name}` },
            mostRecent && { icon: "flame", title: `Most Recent Result`, sub: `${mostRecent.athlete} · ${formatDate(mostRecent.competition_date)}` },
        ].filter(Boolean);
        $("#opHighlightList").innerHTML = items.map(i => `
            <div class="op-highlight-item">
                <div class="icn"><i data-lucide="${i.icon}"></i></div>
                <div class="txt"><strong>${i.title}</strong><span>${i.sub}</span></div>
            </div>
        `).join("");
    }

 
    function renderTimeline(data) {
        const items = data.slice().sort((a, b) => new Date(a.competition_date) - new Date(b.competition_date)).slice(-6);
        $("#opTimeline").innerHTML = items.map(d => `
            <div class="op-timeline-item">
                <div class="op-timeline-dot ${d.participation_status === 'COMPLETED' ? 'filled' : ''}"><i data-lucide="${d.medal !== 'NONE' ? 'medal' : 'flag'}"></i></div>
                <div class="date">${formatDate(d.competition_date)}</div>
                <div class="name">${d.competition_name}</div>
                <div class="loc">${d.host_city}, ${d.host_country}</div>
            </div>
        `).join("");
    }

   
    
    function renderRecent(data) {
        const recent = data.filter(d => d.participation_status === "COMPLETED")
            .sort((a, b) => new Date(b.competition_date) - new Date(a.competition_date)).slice(0, 6);
        $("#opRecentGrid").innerHTML = recent.map((d, i) => `
            <div class="op-card op-recent-card" style="animation-delay:${i * 0.05}s" data-op-animate>
                <div class="op-recent-card__medal ${d.medal.toLowerCase()}"><i data-lucide="medal" style="width:16px;height:16px;"></i></div>
                <div class="op-recent-card__avatar">${initials(d.athlete)}</div>
                <h4>${d.athlete}</h4>
                <div class="sub">${d.event_name}</div>
                <div class="op-recent-card__meta">
                    <span><i data-lucide="trophy"></i>${d.competition_name}</span>
                    <span><i data-lucide="map-pin"></i> ${d.host_country}</span>
                    <span><i data-lucide="calendar"></i>${formatDate(d.competition_date)}</span>
                    <span><i data-lucide="hash"></i>Rank ${d.ranking ?? "—"}</span>
                </div>
            </div>
        `).join("");
    }



    function ringSVG(id, pct, color) {
        const r = 35, c = 2 * Math.PI * r;
        const offset = c - (pct / 100) * c;
        return `
        <div class="op-ring">
            <svg width="84" height="84" viewBox="0 0 84 84">
                <circle class="bg" cx="42" cy="42" r="${r}"></circle>
                <circle class="fg" id="${id}" cx="42" cy="42" r="${r}" style="stroke:${color}; stroke-dasharray:${c}; stroke-dashoffset:${c};"></circle>
            </svg>
            <div class="txt">${pct}%</div>
        </div>`;
    }


    function getSearchFilteredData(data) {

    const keyword = state.search.trim().toLowerCase();

    if (!keyword) {
        return data;
    }

    return data.filter(item => {

        return (
            (item.athlete || "").toLowerCase().includes(keyword) ||
            (item.athlete_no || "").toLowerCase().includes(keyword) ||
            (item.competition_name || "").toLowerCase().includes(keyword) ||
            (item.event_name || "").toLowerCase().includes(keyword) ||
            (item.host_country || "").toLowerCase().includes(keyword) ||
            (item.host_city || "").toLowerCase().includes(keyword) ||
            (item.competition_level || "").toLowerCase().includes(keyword) ||
            (item.medal || "").toLowerCase().includes(keyword) ||
            (item.participation_status || "").toLowerCase().includes(keyword) ||
            String(item.ranking || "").includes(keyword)
        );

    });

}

   
    function getFilteredSorted() {
        // let rows = getSearchFilteredData(OP_DATA);
        let rows = getSearchFilteredData(OP_TABLE_DATA);
        rows = rows.filter(d => {
            const q = state.search.trim().toLowerCase();
            const matchesSearch = !q || [d.athlete, d.competition_name, d.event_name, d.host_country, d.host_city].join(" ").toLowerCase().includes(q);
            const matchesLevel = !state.level || d.competition_level === state.level;
            const matchesMedal = !state.medal || d.medal === state.medal;
            const matchesStatus = !state.status || d.participation_status === state.status;
            return matchesSearch && matchesLevel && matchesMedal && matchesStatus;
        });
        rows.sort((a, b) => {
            let av = a[state.sortKey], bv = b[state.sortKey];
            if (state.sortKey === "competition_date") { av = new Date(av); bv = new Date(bv); }
            if (av === null || av === undefined) av = state.sortDir === "asc" ? Infinity : -Infinity;
            if (bv === null || bv === undefined) bv = state.sortDir === "asc" ? Infinity : -Infinity;
            if (av < bv) return state.sortDir === "asc" ? -1 : 1;
            if (av > bv) return state.sortDir === "asc" ? 1 : -1;
            return 0;
        });
        return rows;
    }

    function renderTable() {
        const rows = getFilteredSorted();
        const totalPages = Math.max(1, Math.ceil(rows.length / state.pageSize));
        state.page = Math.min(state.page, totalPages);
        const start = (state.page - 1) * state.pageSize;
        const pageRows = rows.slice(start, start + state.pageSize);

        //  <td>${d.event_name}</td>
        //  <td>${d.score_time}</td>

        $("#opTableBody").innerHTML = pageRows.length ? pageRows.map(d => `
            
            <tr data-uuid="${d.uuid}">
                <td>
                    <div class="op-athlete-cell">
                        <div class="av">${initials(d.athlete)}</div>
                        <div><div class="name">${d.athlete}</div><div class="num">${d.athlete_no}</div></div>
                    </div>
                </td>
                <td>${d.competition_name}</td>
               
                <td><div class="op-country-cell">${d.host_country}</div></td>
                <td>${levelBadge(d.competition_level)}</td>
                <td>${formatDate(d.competition_date)}</td>
                <td><span class="op-rank-pill ${d.ranking === 1 ? 'top' : ''}">${d.ranking ?? "—"}</span></td>
               
                <td>${medalBadge(d.medal)}</td>
                <td>${statusBadge(d.participation_status)}</td>
                 <td>
                    <div class="op-row-actions">
                        <button class="view" title="View" type="button"><i data-lucide="eye"></i></button>
                        ${window.OP_CAN_UPDATE_PERFORMANCE ? `<button class="edit" title="Edit" type="button"><i data-lucide="pencil"></i></button>` : ""}
                        ${state.viewArchived
                            ? `<button class="restore" title="Unarchive" type="button"><i data-lucide="archive-restore"></i></button>`
                            : `<button class="archive" title="Archive" type="button"><i data-lucide="archive"></i></button>`}
                    </div>
                </td>
            </tr>
        `).join("") : `<tr><td colspan="11"><div class="op-empty"><i data-lucide="search-x"></i><div>No performances match your filters.</div></div></td></tr>`;

        $("#opTableCount").textContent = `Showing ${pageRows.length ? start + 1 : 0}-${start + pageRows.length} of ${rows.length} performances`;

        const pag = $("#opPagination");
        let pagHtml = "";
        for (let p = 1; p <= totalPages; p++) {
            pagHtml += `<button data-page="${p}" class="${p === state.page ? 'active' : ''}">${p}</button>`;
        }
        pag.innerHTML = pagHtml;
        refreshIcons();
    }

  
    function wireToolbar() {
        
        // $("#opSearchInput").addEventListener("input", (e) => { state.search = e.target.value; state.page = 1; renderTable(); });
        const searchInput = $("#opTableSearch");

        if (searchInput) {

            searchInput.addEventListener("input", function () {

                state.search = this.value;

                state.page = 1;

                renderTable();

            });

        }
        



        $("#opFilterLevel")?.addEventListener("change", (e) => { state.level = e.target.value; state.page = 1; renderTable(); });
        $("#opFilterMedal")?.addEventListener("change", (e) => { state.medal = e.target.value; state.page = 1; renderTable(); });
        $("#opFilterStatus")?.addEventListener("change", (e) => { state.status = e.target.value; state.page = 1; renderTable(); });

        $("#opRefreshBtn")?.addEventListener("click", () => {
            $("#opRefreshBtn i").style.transition = "transform .6s";
            $("#opRefreshBtn i").style.transform = "rotate(360deg)";
            setTimeout(() => { $("#opRefreshBtn i").style.transform = "rotate(0deg)"; }, 600);
            renderAll();
            toast("Dashboard refreshed", "refresh-cw");
        });
        $("#opFilterBtn")?.addEventListener("click", () => toast("Use the dropdowns above to filter results", "sliders-horizontal"));
        [$("#opExportBtn"), $("#opExportBtnHero")].forEach(btn => btn && btn.addEventListener("click", () => toast("Export queued — this is a UI preview only", "download")));
        [$("#opAddBtn2")].forEach(btn => btn && btn.addEventListener("click", () => { window.location.href = "/dashboard/olympics/performances/add/"; }));

        $("#opPagination")?.addEventListener("click", (e) => {
            const btn = e.target.closest("button[data-page]");
            if (!btn) return;
            state.page = Number(btn.dataset.page);
            renderTable();
        });

      
       $$(".op-table tbody").forEach(tbody => {
            tbody.addEventListener("click", (e) => {
                const actionBtn = e.target.closest("button");
                if (!actionBtn) return;
                const row = actionBtn.closest("tr[data-uuid]");   
                const uuid = row ? row.dataset.uuid : null;
                if (actionBtn.classList.contains("view")) { if (uuid) openPerformanceViewModal(uuid); }
                if (actionBtn.classList.contains("edit")) { if (uuid) window.location.href = `/dashboard/olympics/performances/${uuid}/edit/`; }
                if (actionBtn.classList.contains("archive")) { if (uuid) archivePerformance(uuid); }
                if (actionBtn.classList.contains("restore")) { if (uuid) restorePerformance(uuid); }
            });
        });
    }

    $("#opArchiveToggleLink")?.addEventListener("click", () => {
            state.viewArchived = !state.viewArchived;
            const link = $("#opArchiveToggleLink");
            if (link) link.textContent = state.viewArchived ? "View All Records" : "View Archived Records";
            fetchTableData(state.viewArchived);
        });
    

    
    async function fetchTableData(archived) {
        try {
            const res = await fetch(`/dashboard/olympics/performances/data/?archived=${archived ? "1" : "0"}`);
            const json = await res.json();
            OP_TABLE_DATA = json.results || [];
        } catch (err) {
            console.error("Failed to load table data", err);
            OP_TABLE_DATA = [];
        }
        state.page = 1;
        renderTable();
    }

    async function archivePerformance(uuid) {
        try {
            const res = await fetch(`/dashboard/olympics/performances/${uuid}/archive/`, {
                method: "POST",
                headers: { "X-CSRFToken": getCookie("csrftoken") },
            });
            const json = await res.json();
            if (!json.ok) { toast(json.message || "Could not archive record", "alert-triangle", "top-right"); return; }
            toast("Record archived successfully.", "archive", "top-right");
            await fetchTableData(state.viewArchived);
            await fetchPerformanceData();
        } catch (err) {
            console.error("Archive failed", err);
            toast("Could not archive record", "alert-triangle", "top-right");
        }
    }

    async function restorePerformance(uuid) {
        try {
            const res = await fetch(`/dashboard/olympics/performances/${uuid}/restore/`, {
                method: "POST",
                headers: { "X-CSRFToken": getCookie("csrftoken") },
            });
            const json = await res.json();
            if (!json.ok) { toast(json.message || "Could not restore record", "alert-triangle", "top-right"); return; }
            toast("Record restored successfully.", "archive-restore", "top-right");
            await fetchTableData(state.viewArchived);
            await fetchPerformanceData();
        } catch (err) {
            console.error("Restore failed", err);
            toast("Could not restore record", "alert-triangle", "top-right");
        }
    }

    function wireRipples() {
        $$(".op-btn").forEach(btn => {
            btn.addEventListener("click", function (e) {
                const rect = btn.getBoundingClientRect();
                const ripple = document.createElement("span");
                const size = Math.max(rect.width, rect.height);
                ripple.className = "op-ripple";
                ripple.style.width = ripple.style.height = size + "px";
                ripple.style.left = (e.clientX - rect.left - size / 2) + "px";
                ripple.style.top = (e.clientY - rect.top - size / 2) + "px";
                btn.appendChild(ripple);
                setTimeout(() => ripple.remove(), 650);
            });
        });
    }

   
    function wireScrollReveal() {
        const targets = $$("[data-op-animate]");
        if (!("IntersectionObserver" in window)) { targets.forEach(t => t.classList.add("op-in")); return; }
        const io = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) { entry.target.classList.add("op-in"); io.unobserve(entry.target); }
            });
        }, { threshold: 0.12 });
        targets.forEach(t => io.observe(t));
    }

  
    function renderAll() {
        const metrics = computeMetrics(OP_DATA);
        renderHero(metrics);
        renderStatCards(metrics);
        renderMedalDonut(metrics);
        renderRankChart(OP_DATA);
        renderCountries(OP_DATA);
        renderHighlights(OP_DATA);
        renderTimeline(OP_DATA);
        renderRecent(OP_DATA);
        
        renderTable();
        refreshIcons();
        requestAnimationFrame(wireScrollReveal);
    }


   
    document.addEventListener("DOMContentLoaded", function () {
        if (!$("#opPage")) return;
        fetchPerformanceData();
        wireToolbar();
        wireRipples();
        });

       async function fetchPerformanceData() {
        try {
            const res = await fetch("/dashboard/olympics/performances/data/");
            const json = await res.json();
            OP_DATA = json.results || [];
            if (!state.viewArchived) OP_TABLE_DATA = OP_DATA;
        } catch (err) {
            console.error("Failed to load performance data", err);
            OP_DATA = [];
            OP_TABLE_DATA = [];
        }
        renderAll();
    }
})();