document.addEventListener("DOMContentLoaded", function () {
    AOS.init({ once: true, offset: 50, easing: 'ease-in-out' });

    const dashboard = document.getElementById("medicalDashboard");
    if (!dashboard) return;

    fetch(dashboard.dataset.dashboardUrl, { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(renderDashboard)
        .catch((err) => console.error("Dashboard load error:", err));
});

function renderDashboard(data) {
    renderRoleBanner(data.role);
    renderStatCards(data.stat_cards);
    animateCounters();
    renderTimeline(data.timeline);
    renderSidePanel(data.side_panel);
    renderCharts(data);
}

function renderRoleBanner(role) {
    const el = document.getElementById("roleBanner");
    if (!el || !role) return;
    el.innerHTML = `<span class="badge-role">${role.role_name}</span> · ${role.department}`;
}

function renderStatCards(cards) {
    const grid = document.getElementById("statsGrid");
    if (!grid || !cards) return;

    grid.innerHTML = cards.map((c, i) => {
        const isNumeric = typeof c.value === "number";
        const valueMarkup = isNumeric
            ? `<div class="md-stat-value count-num" data-target="${c.value}">0</div>`
            : `<div class="md-stat-value">${c.value}</div>`;
        const changeMarkup = c.change_pct !== undefined
            ? `<div class="md-stat-change ${c.change_pct >= 0 ? 'up' : 'down'}">
                 <i class="fas fa-arrow-${c.change_pct >= 0 ? 'up' : 'down'}"></i> ${Math.abs(c.change_pct)}%
               </div>`
            : (c.suffix ? `<div class="md-stat-change up">${c.suffix}</div>` : "");

        return `
            <div class="md-stat-card" data-aos="fade-up" data-aos-delay="${i * 50}" data-aos-duration="600">
                <div class="md-stat-icon md-icon-${c.color}"><i class="fas ${c.icon}"></i></div>
                <div class="md-stat-info">
                    <div class="md-stat-label">${c.label}</div>
                    ${valueMarkup}
                    ${changeMarkup}
                </div>
                <div class="md-stat-bg"><i class="fas ${c.icon}"></i></div>
            </div>`;
    }).join("");
}

function animateCounters() {
    document.querySelectorAll(".md-stat-value.count-num").forEach((el) => {
        const target = parseInt(el.dataset.target, 10);
        if (isNaN(target)) return;
        const duration = 1200, start = performance.now();
        function tick(t) {
            const p = Math.min((t - start) / duration, 1);
            el.textContent = Math.floor((1 - Math.pow(1 - p, 3)) * target).toLocaleString();
            if (p < 1) requestAnimationFrame(tick); else el.textContent = target.toLocaleString();
        }
        requestAnimationFrame(tick);
    });
}

function renderTimeline(items) {
    const el = document.getElementById("recentActivityTimeline");
    if (!el) return;
    if (!items || !items.length) {
        el.innerHTML = `<div class="md-timeline-item"><div class="md-desc">No recent activity.</div></div>`;
        return;
    }
    el.innerHTML = items.map((i, idx) => `
        <div class="md-timeline-item" data-aos="fade-right" data-aos-delay="${idx * 50}">
            <div class="md-time">${i.time}</div>
            <div class="md-content"><div class="md-title">${i.title}</div><div class="md-desc">${i.desc}</div></div>
        </div>`).join("");
}

function renderSidePanel(panel) {
    const titleEl = document.getElementById("sidePanelTitle");
    const listEl = document.getElementById("sidePanelList");
    if (!panel || !listEl) return;

    if (titleEl) titleEl.innerHTML = `<i class="fas fa-circle"></i> ${panel.title || ""}`;
    if (!panel.items || !panel.items.length) {
        listEl.innerHTML = `<div class="md-status-item"><span class="md-label">No data yet</span></div>`;
        return;
    }
    listEl.innerHTML = panel.items.map((i) => `
        <div class="md-status-item">
            <div class="md-left"><span class="md-dot md-dot-primary"></span><span class="md-label">${i.label}</span></div>
            <span class="md-count">${i.count}</span>
        </div>`).join("");
}

function renderCharts(data) {
    if (typeof Chart === 'undefined') { setTimeout(() => renderCharts(data), 300); return; }

    const tooltipStyle = { backgroundColor: 'white', titleColor: '#1a1a1a', bodyColor: '#444', borderColor: '#e0e0e0', borderWidth: 1, cornerRadius: 10, padding: 12 };
    const palette = ["#c5050c", "#185fa5", "#dc2626", "#228b22", "#7c3aed", "#f59e0b", "#0d9488", "#ea580c"];

function isEmpty(chartData) {
    return !chartData || !chartData.labels || chartData.labels.length === 0 ||
           chartData.data.every((v) => !v || v === 0);
}

function showEmptyState(canvasId, titleId, title, iconClass) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    if (titleId) document.getElementById(titleId).innerHTML = `<i class="fas ${iconClass}"></i> ${title || ""}`;
    const wrapper = canvas.parentElement;
    canvas.style.display = "none";
    let msg = wrapper.querySelector(".md-chart-empty");
    if (!msg) {
        msg = document.createElement("div");
        msg.className = "md-chart-empty";
        wrapper.appendChild(msg);
    }
    msg.innerHTML = `<i class="fas fa-chart-simple"></i><span>No data available</span>`;
    msg.style.display = "flex";
}

function hideEmptyState(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    canvas.style.display = "";
    const msg = canvas.parentElement.querySelector(".md-chart-empty");
    if (msg) msg.style.display = "none";
}

function lineChart(canvasId, titleId, chartData, iconClass) {
    if (!chartData) return;
    if (isEmpty(chartData)) { showEmptyState(canvasId, titleId, chartData.title, iconClass); return; }
    hideEmptyState(canvasId);
    document.getElementById(titleId).innerHTML = `<i class="fas ${iconClass}"></i> ${chartData.title}`;
    const ctx = document.getElementById(canvasId).getContext("2d");
    const grad = ctx.createLinearGradient(0, 0, 0, 240);
    grad.addColorStop(0, "rgba(197,5,12,0.25)"); grad.addColorStop(1, "rgba(197,5,12,0)");
    new Chart(ctx, {
        type: "line",
        data: { labels: chartData.labels, datasets: [{ data: chartData.data, borderColor: "#c5050c", backgroundColor: grad, fill: true, tension: 0.4, pointBackgroundColor: "#c5050c", pointBorderColor: "white", pointBorderWidth: 2, pointRadius: 4, borderWidth: 2 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, grid: { color: "rgba(0,0,0,0.05)" } }, x: { grid: { display: false } } } },
    });
}

function barChart(canvasId, titleId, chartData, iconClass) {
    if (!chartData) return;
    if (isEmpty(chartData)) { showEmptyState(canvasId, titleId, chartData.title, iconClass); return; }
    hideEmptyState(canvasId);
    document.getElementById(titleId).innerHTML = `<i class="fas ${iconClass}"></i> ${chartData.title}`;
    const ctx = document.getElementById(canvasId).getContext("2d");
    const palette = ["#c5050c", "#185fa5", "#dc2626", "#228b22", "#7c3aed", "#f59e0b", "#0d9488", "#ea580c"];
    new Chart(ctx, {
        type: "bar",
        data: { labels: chartData.labels, datasets: [{ data: chartData.data, backgroundColor: palette, borderRadius: 6, borderSkipped: false }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, grid: { color: "rgba(0,0,0,0.05)" } }, x: { grid: { display: false }, ticks: { maxRotation: 45, font: { size: 9 } } } } },
    });
}

function circularChart(canvasId, titleId, chartData, type, iconClass) {
    if (!chartData) return;
    if (isEmpty(chartData)) { showEmptyState(canvasId, titleId, chartData.title, iconClass); return; }
    hideEmptyState(canvasId);
    document.getElementById(titleId).innerHTML = `<i class="fas ${iconClass}"></i> ${chartData.title}`;
    const ctx = document.getElementById(canvasId).getContext("2d");
    const palette = ["#c5050c", "#185fa5", "#dc2626", "#228b22", "#7c3aed", "#f59e0b", "#0d9488", "#ea580c"];
    new Chart(ctx, {
        type,
        data: { labels: chartData.labels, datasets: [{ data: chartData.data, backgroundColor: palette, borderWidth: type === "doughnut" ? 3 : 2, borderColor: "white" }] },
        options: { responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: "bottom", labels: { font: { size: 11 }, padding: 12, usePointStyle: true, pointStyle: 'circle' } } },
            cutout: type === "doughnut" ? "60%" : undefined,
            animation: { animateRotate: true, duration: 1200 } },
    });
}

    lineChart("chartOne", "chartOneTitle", data.chart_one, "fa-chart-line");
    barChart("chartTwo", "chartTwoTitle", data.chart_two, "fa-chart-bar");
    circularChart("chartThree", "chartThreeTitle", data.chart_three, data.chart_three?.type || "doughnut", "fa-chart-pie");
    circularChart("chartFour", "chartFourTitle", data.chart_four, data.chart_four?.type || "pie", "fa-chart-pie");
}