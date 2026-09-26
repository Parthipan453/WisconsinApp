// ur-btn dropdown
const exportBtn = document.getElementById("exportBtn");
const exportBox = document.querySelector(".ur-export");
const pdfMenuBtn = document.getElementById("pdfMenuBtn");
const pdfSubmenu = document.getElementById("pdfSubmenu");


exportBtn.addEventListener("click", () => {
    exportBox.classList.toggle("active");
});

document.addEventListener("click", (e) => {
    if (!exportBox.contains(e.target)) {
        exportBox.classList.remove("active");
        document.querySelectorAll(".ur-submenu-content").forEach(menu => {
            menu.classList.remove("show");
        });
    }

});

document.querySelector("#exportMenu > .ur-submenu > .ur-submenu-btn")
    .addEventListener("click", function (e) {
        e.preventDefault();

        document.querySelector(".ur-submenu-content")
            .classList.toggle("show");
    });




let loginTrendChart;
let loginStatusChart;
let deviceChart;
let browserChart;
let peakHourChart;

// stats
document.addEventListener("DOMContentLoaded", function () {
    loadDashboard();
    loadSessions();

    setInterval(() => {
        refreshDashboard();
        loadSessions(currentPage); // keeps current page updated
    }, 1000);

});

function loadDashboard() {

    fetch("/dashboard/login-reports/json/")
        .then(response => response.json())
        .then(data => {
            document.getElementById("totalLoginGrowth").innerHTML =
            `${data.cards.total_login_growth >= 0 ? "↑" : "↓"} ${Math.abs(data.cards.total_login_growth)}% from last month`;

            document.getElementById("failedGrowth").innerHTML =
            `${data.cards.failed_growth >= 0 ? "↑" : "↓"} ${Math.abs(data.cards.failed_growth)}% from last month`;

            document.getElementById("todayGrowth").innerHTML =
            `${data.cards.today_growth >= 0 ? "↑" : "↓"} ${Math.abs(data.cards.today_growth)}% from yesterday`;
            document.getElementById("totalLogins").textContent = data.cards.total_logins;
            document.getElementById("onlineUsers").textContent = data.cards.online_users;
            document.getElementById("failedLogins").textContent = data.cards.failed_logins;
            document.getElementById("avrgLogins").textContent = data.cards.avg_logins;
            document.getElementById("todayLogins").textContent = data.cards.todays_logins;
            createCharts(data);
        })
        .catch(error => { console.log(error); });

        document.getElementById("totalLogins").textContent =
    data.cards.total_logins;



}




function createCharts(data) {

    Chart.defaults.font.family = "'Poppins', sans-serif";
    Chart.defaults.font.size = 13;
    Chart.defaults.color = "#666";

    // Login Trend
    const loginTrendCtx = document.getElementById("loginTrendChart").getContext("2d");
    loginTrendChart = new Chart(loginTrendCtx, {
        type: "bar",
        data: {
            labels: data.login_trend.labels,
            datasets: [{
                label: "Logins",
                data: data.login_trend.values,
                backgroundColor: "#c5050c",
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            maxBarThickness: 60,
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });

    // Login Status
    const loginStatusCtx = document
        .getElementById("loginStatusChart")
        .getContext("2d");
    loginStatusChart = new Chart(loginStatusCtx, {
        type: "bar",
        data: {
            labels: ["Success", "Failed"],
            datasets: [{
                data: [
                    data.cards.total_logins,
                    data.cards.failed_logins
                ],
                backgroundColor: [
                    "#2ecc71",
                    "#e74c3c"
                ],
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            maxBarThickness: 65,
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });

    // Device Usage
    const deviceCtx = document.getElementById("deviceChart").getContext("2d");
    deviceChart = new Chart(deviceCtx, {
        type: "pie",
        data: {
            labels: data.device_usage.labels,
            datasets: [{
                data: data.device_usage.values,
                backgroundColor: [
                    "#3498db",
                    "#9b59b6",
                    "#f39c12"],
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,

        }
    });

    // Browser Usage
    const centerTextPlugin = {
        id: "centerText",
        beforeDraw(chart) {
            if (chart.config.type !== "doughnut") return;

            const { ctx } = chart;
            const meta = chart.getDatasetMeta(0);

            if (!meta.data.length) return;
            const { chartArea } = chart;

            if (!chartArea) return;

            const x = (chartArea.left + chartArea.right) / 2;
            const y = (chartArea.top + chartArea.bottom) / 2;
            let fontSize = Math.min(chart.width, chart.height) / 12;
            ctx.save();

            ctx.textAlign = "center";
            ctx.textBaseline = "middle";

            // Heading
            ctx.font = `bold ${fontSize * 0.6}px "Encode Sans"`;
            ctx.fillStyle = "#212529";
            ctx.fillText("Browser Usage", x, y - fontSize / 2);

            ctx.restore();
        }
    };
    Chart.register(centerTextPlugin);
    const browserCtx = document.getElementById("browserChart").getContext("2d");
    browserChart = new Chart(browserCtx, {
        type: "doughnut",
        data: {
            labels: data.browser_usage.labels,
            datasets: [{
                data: data.browser_usage.values,
                backgroundColor: [

                    "#0F9D58",
                    "#DB4437",
                    "#4285F4",
                    "#F4B400"
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "70%",
            plugins: [centerTextPlugin]
        }
    });

    // Peak Login Hours
    const peakCtx = document.getElementById("peakHourChart").getContext("2d");
    peakHourChart = new Chart(peakCtx, {
        type: "line",
        data: {
            labels: data.peak_hours.labels,
            datasets: [{
                label: "Users",
                data: data.peak_hours.values,
                borderColor: "#c5050c",
                backgroundColor: "rgba(197,5,12,.15)",
                fill: true,
                tension: .4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
        }
    });
}

function updateCharts(data) {

    loginTrendChart.data.labels = data.login_trend.labels;
    loginTrendChart.data.datasets[0].data = data.login_trend.values;
    loginTrendChart.update();

    loginStatusChart.data.datasets[0].data = [
        data.cards.total_logins,
        data.cards.failed_logins];
    loginStatusChart.update();

    deviceChart.data.labels = data.device_usage.labels;
    deviceChart.data.datasets[0].data = data.device_usage.values;
    deviceChart.update();

    browserChart.data.labels = data.browser_usage.labels;
    browserChart.data.datasets[0].data = data.browser_usage.values;
    browserChart.update();

    peakHourChart.data.labels = data.peak_hours.labels;
    peakHourChart.data.datasets[0].data = data.peak_hours.values;
    peakHourChart.update();
}

// refresh charts
function refreshDashboard() {

    fetch("/dashboard/login-reports/json/")
        .then(res => res.json())
        .then(data => {
            document.getElementById("totalLogins").textContent = data.cards.total_logins;
            document.getElementById("onlineUsers").textContent = data.cards.online_users;
            document.getElementById("failedLogins").textContent = data.cards.failed_logins;
            document.getElementById("avrgLogins").textContent = data.cards.avg_logins;
            document.getElementById("todayLogins").textContent = data.cards.todays_logins;
            updateCharts(data);

        });
}

function loadSessions(page = 1) {
    const status = document.getElementById("statusFilter").value;
    fetch(`/dashboard/recent-sessions/json/?page=${page}&status=${status}`)
        .then(res => res.json())
        .then(data => {

            const tbody = document.getElementById("sessionTableBody");

            if (data.logs.length === 0) {
                tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">
                    No Records Found
                </td>
            </tr>
        `;

                document.getElementById("pageInfo").innerText = "";
                document.getElementById("prevPage").disabled = true;
                document.getElementById("nextPage").disabled = true;
                return;
            }

            let rows = "";

            data.logs.forEach(log => {

                const statusClass = log.status === "SUCCESS" || log.status === "ACTIVE"
                    ? "ur-status active"
                    : "ur-status inactive";

                const loginTime = log.login_time
                    ? new Date(log.login_time).toLocaleString()
                    : "--";
                rows += `
                    <tr>
                        <td>${log.user}</td>
                        <td>${log.role}</td>
                        <td>${loginTime}</td>
                        <td>${log.device}</td>
                        <td>${log.browser}</td>
                        <td>${log.ip}</td>
                        <td>
                            <span class="${statusClass}">
                                ${log.status}
                            </span>
                        </td>
                    </tr>
                `;
            });

            tbody.innerHTML = rows;
            document.getElementById("sessionCount").innerText = `Showing ${data.start_index} to ${data.end_index} of ${data.count} results`;
            currentPage = data.current_page;
            let pagination = "";
            if (data.has_previous) {
                pagination += `<button class="ur-page-btn" onclick="loadSessions(${data.previous_page})">‹</button>`;
            }
            else {
                pagination += `<span class="ur-page-btn ur-page-btn--disabled">‹</span>`;
            }
            data.page_range.forEach(page => {

                if (page === data.current_page) {
                    pagination += `<span class="ur-page-btn active">${page}</span>`;
                } else {
                    pagination += `<button class="ur-page-btn"onclick="loadSessions(${page})">${page}</button>`;
                }
            });
            if (data.has_next) {
                pagination += `<button class="ur-page-btn" onclick="loadSessions(${data.next_page})">›</button>`;
            } else {
                pagination += `<span class="ur-page-btn ur-page-btn--disabled"> ›</span>`;
            }

            document.getElementById("sessionPagination").innerHTML = pagination;

        })
        .catch(err => {
            console.error("Failed to load sessions:", err);
        });
}

document.addEventListener("DOMContentLoaded", () => {
    loadSessions();
    setInterval(() => {
        loadSessions();
    }, 10000);
});
// Search filter
document.getElementById("sessionSearch").addEventListener("input", function () {
    const value = this.value.toLowerCase().trim();
    const tbody = document.getElementById("sessionTableBody");
    const rows = tbody.querySelectorAll("tr");
    let visibleCount = 0;
    const oldNoRow = document.getElementById("noSearchRow");
    if (oldNoRow) oldNoRow.remove();
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(value)) {
            row.style.display = "";
            visibleCount++;
        } else {
            row.style.display = "none";
        }
    });

    if (visibleCount === 0) {
        const noRow = document.createElement("tr");
        noRow.id = "noSearchRow";
        noRow.innerHTML = `
            <td colspan="7" style="text-align:center; padding:12px;">
                No Matching User Found
            </td>
        `;
        tbody.appendChild(noRow);
    }
});

document.getElementById("statusFilter").addEventListener("change", function () {
    currentPage = 1;
    loadSessions(currentPage);
});
