// /* kali's code */

(() => {
    'use strict';

    const API_URL = window.AUDIT_LOG_API_URL || '';

    const state = {
        page: 1,
        pageSize: 25,
        sortBy: 'timestamp',
        sortDir: 'desc',
        filters: { search: '', date_from: '', date_to: '', user: '', action: '', module: '', status: '', browser: '', device: '' },
        rows: [],
        totalCount: 0,
        options: { users: [], actions: [], modules: [], browsers: [], devices: [] },
        stats: {},
        chartData: {},
        liveInterval: null,
    };

    const $ = sel => document.querySelector(sel);
    const $$ = sel => Array.from(document.querySelectorAll(sel));

    const els = {
        tableBody: $('#auditTableBody'),
        loadingState: $('#auditLoadingState'),
        emptyState: $('#auditEmptyState'),
        resultCount: $('#resultCount'),
        paginationInfo: $('#paginationInfo'),
        paginationControls: $('#paginationControls'),
        pageSizeSelect: $('#pageSizeSelect'),
        chips: $('#activeFiltersChips'),
        // exportBtn: $('#exportBtn'),
        // exportMenu: $('#exportMenu'),
        liveBtn: $('#liveToggleBtn'),
        refreshBtn: $('#refreshBtn'),
        filterToggleBtn: $('#filterToggleBtn'),
        filtersCard: $('#filtersCard'),
        filtersCloseBtn: $('#filtersCloseBtn'),
    };

    function initIcons() { if (window.lucide) lucide.createIcons(); }

    /* ===================== demo DATA  ===================== */
    function generateMockData() {
        const actions = [
            "CREATE",
            "UPDATE",
            "DELETE",
            "LOGIN",
            "LOGOUT",
            "DOWNLOAD",
            "UPLOAD",
            "EXPORT",
            "IMPORT",
            "VIEW",
            "PASSWORD_CHANGE",
            "ROLE_ASSIGN",
            "ROLE_REMOVE",
            "STATUS_CHANGE",
            "CANCEL",
            "APPROVE",
            "REJECT",
            "ISSUE",
            "RETURN",
            "RENEW",
        ];
        const modules = ["User Management", "Role Management", "Authentication", "Reports", "Content Management", "Settings", "Dashboard"];
        const browsers = ["Chrome 124", "Firefox 126", "Safari 17", "Edge 124"];
        const devices = ["Desktop", "Mobile", "Tablet"];
        const oses = ["Windows 11", "macOS 14", "Ubuntu 22.04", "Android 14", "iOS 17"];
        const users = ["amit.kumar", "sara.lee", "john.doe", "priya.singh", "mark.evans", "admin"];
        const statuses = ["SUCCESS", "SUCCESS", "SUCCESS", "SUCCESS", "FAILED"];
        const rows = [];
        const now = new Date();
        for (let i = 0; i < 240; i++) {
            const ts = new Date(now.getTime() - Math.floor(Math.random() * 30 * 24 * 3600 * 1000));
            const action = actions[Math.floor(Math.random() * actions.length)];
            const user = users[Math.floor(Math.random() * users.length)];
            rows.push({
                id: i + 1,
                user: user,
                action: action,
                module: modules[Math.floor(Math.random() * modules.length)],
                object_type: "User",
                object_id: String(1000 + Math.floor(Math.random() * 900)),
                description: `${user} performed ${action.toLowerCase()} on a record`,
                timestamp: ts.toISOString(),
                ip_address: `192.168.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
                browser: browsers[Math.floor(Math.random() * browsers.length)],
                operating_system: oses[Math.floor(Math.random() * oses.length)],
                device: devices[Math.floor(Math.random() * devices.length)],
                request_method: ["GET", "POST", "PUT", "DELETE"][Math.floor(Math.random() * 4)],
                request_url: "/admin/users/" + (1000 + i) + "/update/",
                status: statuses[Math.floor(Math.random() * statuses.length)],
                before_data: action === "UPDATE" ? { account_status: "ACTIVE", role: "Student" } : null,
                after_data: action === "UPDATE" ? { account_status: "INACTIVE", role: "Student" } : null,
                session_key: "sess_" + Math.random().toString(36).slice(2, 12),
                request_id: "req_" + Math.random().toString(36).slice(2, 10),
            });
        }
        return rows;
    }

    function buildOptionsFromRows(rows) {
        const uniq = key => Array.from(new Set(rows.map(r => r[key]))).filter(Boolean).sort();
        return { users: uniq('user'), actions: uniq('action'), modules: uniq('module'), browsers: uniq('browser'), devices: uniq('device') };
    }

    function computeStats(rows) {
        const today = new Date(); today.setHours(0, 0, 0, 0);
        const total = rows.length;
        const todayCount = rows.filter(r => new Date(r.timestamp) >= today).length;
        const success = rows.filter(r => r.status === 'SUCCESS').length;
        const failed = rows.filter(r => r.status === 'FAILED').length;
        const activeUsers = new Set(rows.map(r => r.user)).size;
        return {
            total, today: todayCount, success, failed, activeUsers,
            successPct: total ? Math.round((success / total) * 1000) / 10 : 0,
            failedPct: total ? Math.round((failed / total) * 1000) / 10 : 0
        };
    }

    function computeChartData(rows) {
        const days = [];
        for (let i = 29; i >= 0; i--) {
            const d = new Date(); d.setHours(0, 0, 0, 0); d.setDate(d.getDate() - i);
            days.push(d);
        }
        const dailyCounts = days.map(d => {
            const next = new Date(d); next.setDate(d.getDate() + 1);
            return rows.filter(r => { const t = new Date(r.timestamp); return t >= d && t < next; }).length;
        });

        const actionCounts = {};
        rows.forEach(r => actionCounts[r.action] = (actionCounts[r.action] || 0) + 1);

        const statusCounts = { SUCCESS: 0, FAILED: 0 };
        rows.forEach(r => statusCounts[r.status] = (statusCounts[r.status] || 0) + 1);

        const moduleCounts = {};
        rows.forEach(r => moduleCounts[r.module] = (moduleCounts[r.module] || 0) + 1);

        return {
            dailyLabels: days.map(d => d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })),
            dailyCounts,
            actionLabels: Object.keys(actionCounts),
            actionCounts: Object.values(actionCounts),
            statusLabels: Object.keys(statusCounts),
            statusCounts: Object.values(statusCounts),
            moduleLabels: Object.keys(moduleCounts),
            moduleCounts: Object.values(moduleCounts),
        };
    }

    /* ===================== DATA LOADING ===================== */
    async function loadData() {
        showLoading(true);
        let allRows;
        try {
            if (API_URL) {
                const res = await fetch(API_URL, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
                if (!res.ok) throw new Error('bad response');
                const data = await res.json();
                allRows = data.results || data.logs || [];
                if (!allRows.length && !data.results) throw new Error('empty');
            } else {
                throw new Error('no api');
            }
        } catch (e) {
            allRows = window.__auditMockCache || generateMockData();
            window.__auditMockCache = allRows;
        }

        state.allRows = allRows;
        state.options = buildOptionsFromRows(allRows);
        state.stats = computeStats(allRows);
        state.chartData = computeChartData(allRows);

        populateFilterOptions();
        renderStats();
        renderCharts();
        applyFiltersAndRender();
        showLoading(false);
    }

    function showLoading(isLoading) {
        els.loadingState.classList.toggle('is-visible', isLoading);
        els.loadingState.hidden = !isLoading;
        if (isLoading) { els.emptyState.hidden = true; els.emptyState.classList.remove('is-visible'); }
    }

    /* ===================== STATS ===================== */
    function animateCounter(el, target) {
        const start = 0;
        const duration = 700;
        const startTime = performance.now();
        function tick(now) {
            const progress = Math.min((now - startTime) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.round(start + (target - start) * eased).toLocaleString();
            if (progress < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    }

    function renderStats() {
        const s = state.stats;

        const values = [s.total, s.today, s.success, s.failed, s.activeUsers];
        $$('#auditStats [data-counter]').forEach((el, i) => animateCounter(el, values[i] || 0));
        const successTrend = $('#successPctTrend'); if (successTrend) successTrend.innerHTML = `<i data-lucide="trending-up"></i> ${s.successPct}% rate`;
        const failedTrend = $('#failedPctTrend'); if (failedTrend) failedTrend.innerHTML = `<i data-lucide="trending-down"></i> ${s.failedPct}% rate`;
        initIcons();
    }

    /* ===================== CHARTS ===================== */
    let chartRefs = {};
    function destroyCharts() {
        Object.values(chartRefs).forEach(c => c && c.destroy());
        chartRefs = {};
    }



    const verticalBarLabelPlugin = {
        id: 'verticalBarLabel',
        afterDatasetsDraw(chart) {
            const { ctx } = chart;
            const meta = chart.getDatasetMeta(0);
            if (!meta) return;
            ctx.save();
            ctx.fillStyle = '#ffffff';
            ctx.font = '600 11px Encode Sans, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            meta.data.forEach((bar, i) => {
                const label = chart.data.labels[i];
                if (!label) return;
                const x = bar.x;
                const barTop = bar.y;
                const barBottom = bar.base;
                const barHeight = barBottom - barTop;
                if (barHeight < 24) return;
                const y = barTop + barHeight / 2;
                ctx.save();
                ctx.translate(x, y);
                ctx.rotate(-Math.PI / 2);
                let text = String(label);

                const maxChars = Math.floor(barHeight / 7);
                if (text.length > maxChars && maxChars > 3) text = text.slice(0, maxChars - 1) + '…';
                ctx.fillText(text, 0, 0);
                ctx.restore();
            });
            ctx.restore();
        }
    };

    function renderCharts() {
        if (!window.Chart) return;
        destroyCharts();
        const cd = state.chartData;
        const red = '#c5050c';

        chartRefs.activity = new Chart($('#activityChart'), {
            type: 'line',
            data: {
                labels: cd.dailyLabels, datasets: [{
                    label: 'Events', data: cd.dailyCounts, borderColor: red,
                    backgroundColor: 'rgba(197,5,12,0.08)', fill: true, tension: 0.35, pointRadius: 0, borderWidth: 2,
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { maxTicksLimit: 8, font: { size: 10 } } },
                    y: { beginAtZero: true, grid: { color: '#f1f3f5' }, ticks: { font: { size: 10 } } }
                }
            }
        });

        const palette = ['#c5050c', '#2563eb', '#16a34a', '#d97706', '#7c3aed', '#0d9488', '#db2777', '#0284c7', '#6c757d', '#e0171f', '#9b0410', '#adb5bd', '#495057'];
        chartRefs.action = new Chart($('#actionChart'), {
            type: 'doughnut',
            data: { labels: cd.actionLabels, datasets: [{ data: cd.actionCounts, backgroundColor: palette, borderWidth: 2, borderColor: '#fff' }] },
            options: {
                responsive: true, maintainAspectRatio: false, cutout: '65%',
                plugins: { legend: { position: 'bottom', labels: { boxWidth: 9, font: { size: 9.5 }, padding: 8 } } }
            }
        });

        chartRefs.status = new Chart($('#statusChart'), {
            type: 'pie',
            data: { labels: cd.statusLabels, datasets: [{ data: cd.statusCounts, backgroundColor: ['#16a34a', '#c5050c'], borderWidth: 2, borderColor: '#fff' }] },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { boxWidth: 9, font: { size: 10.5 }, padding: 10 } } }
            }
        });

        chartRefs.module = new Chart($('#moduleChart'), {
            type: 'bar',
            data: { labels: cd.moduleLabels, datasets: [{ label: 'Logs', data: cd.moduleCounts, backgroundColor: '#c5050c', borderRadius: 6, maxBarThickness: 46 }] },
            plugins: [verticalBarLabelPlugin],
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { font: { size: 10 } } },
                    y: { beginAtZero: true, grid: { color: '#f1f3f5' }, ticks: { font: { size: 10 } } }
                }
            }
        });
    }

    /* ===================== FILTERS PANEL ===================== */
    function openFiltersPanel() {
        els.filtersCard.hidden = false;
        els.filterToggleBtn.classList.add('is-active');
        els.filtersCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    function closeFiltersPanel() {
        els.filtersCard.hidden = true;
        els.filterToggleBtn.classList.remove('is-active');
    }
    function toggleFiltersPanel() {
        if (els.filtersCard.hidden) openFiltersPanel(); else closeFiltersPanel();
    }

    /* ===================== FILTERS ===================== */
    function populateFilterOptions() {
        const fill = (id, list) => {
            const el = document.getElementById(id);
            const current = el.value;
            el.innerHTML = el.querySelector('option')?.outerHTML || '<option value="">All</option>';
            list.forEach(v => { const o = document.createElement('option'); o.value = v; o.textContent = v; el.appendChild(o); });
            el.value = current;
        };
        fill('filterUser', state.options.users);
        fill('filterAction', state.options.actions);
        fill('filterModule', state.options.modules);
        fill('filterBrowser', state.options.browsers);
        fill('filterDevice', state.options.devices);
    }

    function readFiltersFromUI() {
        state.filters.search = $('#filterSearch').value.trim().toLowerCase();
        state.filters.date_from = $('#filterDateFrom').value;
        state.filters.date_to = $('#filterDateTo').value;
        state.filters.user = $('#filterUser').value;
        state.filters.action = $('#filterAction').value;
        state.filters.module = $('#filterModule').value;
        state.filters.status = $('#filterStatus').value;
        state.filters.browser = $('#filterBrowser').value;
        state.filters.device = $('#filterDevice').value;
    }

    function renderChips() {
        const f = state.filters;
        const labels = {
            search: 'Search', date_from: 'From', date_to: 'To', user: 'User', action: 'Action',
            module: 'Module', status: 'Status', browser: 'Browser', device: 'Device',
        };
        const active = Object.keys(f).filter(k => f[k]);
        els.chips.innerHTML = active.map(k =>
            `<span class="audit-chip" data-filter-key="${k}">${labels[k]}: ${f[k]}<button data-clear="${k}"><i data-lucide="x"></i></button></span>`
        ).join('');
        initIcons();
    }

    function applyFiltersAndRender() {
        readFiltersFromUI();
        const f = state.filters;
        let rows = state.allRows.filter(r => {
            if (f.search) {
                const hay = `${r.description} ${r.object_type} ${r.object_id} ${r.request_url} ${r.user}`.toLowerCase();
                if (!hay.includes(f.search)) return false;
            }
            if (f.date_from && new Date(r.timestamp) < new Date(f.date_from)) return false;
            if (f.date_to) { const to = new Date(f.date_to); to.setHours(23, 59, 59, 999); if (new Date(r.timestamp) > to) return false; }
            if (f.user && r.user !== f.user) return false;
            if (f.action && r.action !== f.action) return false;
            if (f.module && r.module !== f.module) return false;
            if (f.status && r.status !== f.status) return false;
            if (f.browser && r.browser !== f.browser) return false;
            if (f.device && r.device !== f.device) return false;
            return true;
        });

        rows.sort((a, b) => {
            let av = a[state.sortBy], bv = b[state.sortBy];
            if (state.sortBy === 'timestamp') { av = new Date(av).getTime(); bv = new Date(bv).getTime(); }
            if (av < bv) return state.sortDir === 'asc' ? -1 : 1;
            if (av > bv) return state.sortDir === 'asc' ? 1 : -1;
            return 0;
        });

        state.rows = rows;
        state.totalCount = rows.length;
        state.page = 1;
        renderChips();
        renderTable();
    }

    /* ===================== TABLE ===================== */
    function initials(name) {
        return (name || '?').split(/[.\s_]/).filter(Boolean).slice(0, 2).map(s => s[0].toUpperCase()).join('');
    }

    function statusIcon(status) { return status === 'SUCCESS' ? 'check-circle-2' : 'x-circle'; }
    function actionIcon(action) {
        const map = {
            CREATE: "plus-circle",
            UPDATE: "pencil",
            DELETE: "trash-2",
            LOGIN: "log-in",
            LOGOUT: "log-out",
            DOWNLOAD: "download",
            UPLOAD: "upload",
            EXPORT: "file-output",
            IMPORT: "file-input",
            VIEW: "eye",
            PASSWORD_CHANGE: "key-round",
            ROLE_ASSIGN: "user-plus",
            ROLE_REMOVE: "user-minus",
            STATUS_CHANGE: "toggle-left",
            CANCEL: "ban",
            APPROVE: "circle-check-big",
            REJECT: "circle-x",
            ISSUE: "book-open-check",
            RETURN: "undo-2",
            RENEW: "refresh-cw",
            REQUEST: "send",
            CANCEL: "ban",
        };
        return map[action] || 'circle';
    }
    function deviceIcon(device) { return device === 'Mobile' ? 'smartphone' : device === 'Tablet' ? 'tablet' : 'monitor'; }

    function fmtDate(iso) {
        const d = new Date(iso);
        return d.toLocaleString(undefined, { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    }

    function renderTable() {
        const start = (state.page - 1) * state.pageSize;
        const pageRows = state.rows.slice(start, start + state.pageSize);

        els.resultCount.textContent = `${state.totalCount.toLocaleString()} record${state.totalCount === 1 ? '' : 's'}`;

        if (!pageRows.length) {
            els.tableBody.innerHTML = '';
            els.emptyState.hidden = false;
            els.emptyState.classList.add('is-visible');
        } else {
            els.emptyState.hidden = true;
            els.emptyState.classList.remove('is-visible');
            els.tableBody.innerHTML = pageRows.map(r => rowHtml(r)).join('');
            initIcons();
        }

        renderPagination();
    }

    function rowHtml(r) {
        return `
        <tr data-id="${r.id}">
            <td class="audit-th-expand"></td>
            <td><span class="audit-mono">${fmtDate(r.timestamp)}</span></td>
            <td>
                <div class="audit-user-cell">
                    <span class="audit-user-avatar">${initials(r.user)}</span>
                    <span><span class="audit-user-name">${r.user || 'Anonymous'}</span><span class="audit-user-meta">${r.module}</span></span>
                </div>
            </td>
            <td><span class="audit-badge audit-badge--${r.action}"><i data-lucide="${actionIcon(r.action)}"></i>${r.action.replace('_', ' ')}</span></td>
            <td>${r.module}</td>
            <td><span class="audit-truncate" title="${r.object_type} #${r.object_id}">${r.object_type} #${r.object_id}</span></td>
            <td><span class="audit-mono">${r.ip_address || '—'}</span></td>
            <td><span style="display:flex;align-items:center;gap:6px;"><i data-lucide="${deviceIcon(r.device)}" style="width:14px;height:14px;color:var(--gray-500);"></i>${r.device}</span></td>
            <td><span class="audit-status-pill audit-status-pill--${r.status}"><i data-lucide="${statusIcon(r.status)}"></i>${r.status}</span></td>
            <td><button class="audit-detail-btn" data-detail="${r.id}"><i data-lucide="maximize-2"></i> View</button></td>
        </tr>`;
    }

    function renderPagination() {
        const totalPages = Math.max(1, Math.ceil(state.totalCount / state.pageSize));
        const start = state.totalCount === 0 ? 0 : (state.page - 1) * state.pageSize + 1;
        const end = Math.min(state.page * state.pageSize, state.totalCount);
        els.paginationInfo.textContent = `Showing ${start}-${end} of ${state.totalCount.toLocaleString()}`;

        let html = `<button class="audit-page-btn" data-page="prev" ${state.page === 1 ? 'disabled' : ''}><i data-lucide="chevron-left"></i></button>`;
        const windowSize = 2;
        for (let p = 1; p <= totalPages; p++) {
            if (p === 1 || p === totalPages || (p >= state.page - windowSize && p <= state.page + windowSize)) {
                html += `<button class="audit-page-btn ${p === state.page ? 'active' : ''}" data-page="${p}">${p}</button>`;
            } else if (p === state.page - windowSize - 1 || p === state.page + windowSize + 1) {
                html += `<span style="padding:0 4px;color:var(--gray-400);">…</span>`;
            }
        }
        html += `<button class="audit-page-btn" data-page="next" ${state.page === totalPages ? 'disabled' : ''}><i data-lucide="chevron-right"></i></button>`;
        els.paginationControls.innerHTML = html;
        initIcons();
    }

    /* ===================== DETAIL MODAL ===================== */
    function openDetailModal(id) {
        const r = state.allRows.find(x => String(x.id) === String(id));
        if (!r) return;
        $('#auditModalRequestId').textContent = r.request_id ? `Request ID: ${r.request_id}` : '';
        $('#dlEventInfo').innerHTML = [
            ['User', r.user || 'Anonymous'], ['Action', r.action], ['Module', r.module],
            ['Object', `${r.object_type} #${r.object_id}`], ['Status', r.status], ['Timestamp', fmtDate(r.timestamp)],
        ].map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('');
        $('#dlRequestInfo').innerHTML = [
            ['IP Address', r.ip_address || '—'], ['Browser', r.browser || '—'], ['OS', r.operating_system || '—'],
            ['Device', r.device || '—'], ['Method', r.request_method || '—'], ['URL', r.request_url || '—'],
            ['Session Key', r.session_key || '—'],
        ].map(([k, v]) => `<div><dt>${k}</dt><dd style="word-break:break-all;">${v}</dd></div>`).join('');
        $('#auditModalDescription').textContent = r.description || 'No description provided.';
        $('#jsonBefore').textContent = r.before_data ? JSON.stringify(r.before_data, null, 2) : '— No before data —';
        $('#jsonAfter').textContent = r.after_data ? JSON.stringify(r.after_data, null, 2) : '— No after data —';

        $('#auditDetailModal').hidden = false;
        document.body.style.overflow = 'hidden';
        initIcons();
    }

    function closeDetailModal() {
        $('#auditDetailModal').hidden = true;
        document.body.style.overflow = '';
    }

    /* ===================== EVENTS ===================== */
    function bindEvents() {
        ['filterSearch', 'filterDateFrom', 'filterDateTo', 'filterUser', 'filterAction', 'filterModule', 'filterStatus', 'filterBrowser', 'filterDevice']
            .forEach(id => {
                const el = document.getElementById(id);
                const evt = el.tagName === 'SELECT' || el.type === 'date' ? 'change' : 'input';
                el.addEventListener(evt, debounce(applyFiltersAndRender, 250));
            });

        els.filterToggleBtn.addEventListener('click', toggleFiltersPanel);
        els.filtersCloseBtn.addEventListener('click', closeFiltersPanel);

        $('#clearFiltersBtn').addEventListener('click', clearAllFilters);
        $('#emptyStateClearBtn').addEventListener('click', () => { openFiltersPanel(); clearAllFilters(); });

        els.chips.addEventListener('click', e => {
            const btn = e.target.closest('[data-clear]');
            if (!btn) return;
            const key = btn.dataset.clear;
            const map = {
                search: 'filterSearch', date_from: 'filterDateFrom', date_to: 'filterDateTo', user: 'filterUser',
                action: 'filterAction', module: 'filterModule', status: 'filterStatus', browser: 'filterBrowser', device: 'filterDevice'
            };
            const el = document.getElementById(map[key]);
            if (el) el.value = '';
            applyFiltersAndRender();
        });

        els.pageSizeSelect.addEventListener('change', () => {
            state.pageSize = parseInt(els.pageSizeSelect.value, 10);
            state.page = 1;
            renderTable();
        });

        els.paginationControls.addEventListener('click', e => {
            const btn = e.target.closest('[data-page]');
            if (!btn || btn.disabled) return;
            const totalPages = Math.max(1, Math.ceil(state.totalCount / state.pageSize));
            if (btn.dataset.page === 'prev') state.page = Math.max(1, state.page - 1);
            else if (btn.dataset.page === 'next') state.page = Math.min(totalPages, state.page + 1);
            else state.page = parseInt(btn.dataset.page, 10);
            renderTable();
            els.tableBody.closest('.audit-table-wrap').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        });

        $$('.audit-table thead th[data-sort]').forEach(th => {
            th.addEventListener('click', () => {
                const key = th.dataset.sort;
                if (state.sortBy === key) state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';
                else { state.sortBy = key; state.sortDir = 'desc'; }
                applyFiltersAndRender();
            });
        });

        els.tableBody.addEventListener('click', e => {
            const btn = e.target.closest('[data-detail]');
            if (btn) openDetailModal(btn.dataset.detail);
        });

        $('#auditModalCloseBtn').addEventListener('click', closeDetailModal);
        $('#auditModalBackdrop').addEventListener('click', closeDetailModal);
        document.addEventListener('keydown', e => { if (e.key === 'Escape') closeDetailModal(); });

        // els.exportBtn.addEventListener('click', e => {
        //     e.stopPropagation();
        //     els.exportMenu.hidden = !els.exportMenu.hidden;
        // });
        // document.addEventListener('click', () => { els.exportMenu.hidden = true; });
        // els.exportMenu.addEventListener('click', e => {
        //     e.stopPropagation();
        //     const item = e.target.closest('.audit-export-item');
        //     if (!item) return;
        //     exportData(item.dataset.format);
        // });

        els.refreshBtn.addEventListener('click', () => loadData());

        els.liveBtn.addEventListener('click', () => {
            const isLive = els.liveBtn.classList.toggle('is-live');
            els.liveBtn.querySelector('span').textContent = isLive ? 'Live: On' : 'Live: Off';
            if (isLive) {
                state.liveInterval = setInterval(() => loadData(), 15000);
            } else {
                clearInterval(state.liveInterval);
            }
        });

        $('#activityRangeSelect').addEventListener('change', () => { renderCharts(); });
    }

    function clearAllFilters() {
        ['filterSearch', 'filterDateFrom', 'filterDateTo', 'filterUser', 'filterAction', 'filterModule', 'filterStatus', 'filterBrowser', 'filterDevice']
            .forEach(id => document.getElementById(id).value = '');
        applyFiltersAndRender();
    }

    // function exportData(format) {
    //     els.exportMenu.hidden = true;
    //     const rows = state.rows;
    //     if (format === 'json') {
    //         downloadBlob(JSON.stringify(rows, null, 2), 'audit_logs.json', 'application/json');
    //     } else if (format === 'csv') {
    //         const headers = ['id', 'user', 'action', 'module', 'object_type', 'object_id', 'status', 'ip_address', 'browser', 'device', 'timestamp'];
    //         const lines = [headers.join(',')].concat(rows.map(r => headers.map(h => `"${String(r[h] ?? '').replace(/"/g, '""')}"`).join(',')));
    //         downloadBlob(lines.join('\n'), 'audit_logs.csv', 'text/csv');
    //     } else {
    //         window.print();
    //     }
    // }

    function downloadBlob(content, filename, type) {
        const blob = new Blob([content], { type });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = filename;
        document.body.appendChild(a); a.click(); a.remove();
        URL.revokeObjectURL(url);
    }

    function debounce(fn, wait) {
        let t;
        return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), wait); };
    }

    /* ===================== INIT ===================== */
    function init() {
        initIcons();
        if (window.AOS) AOS.init({ duration: 500, once: true, offset: 20 });
        bindEvents();
        loadData();
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();

})();