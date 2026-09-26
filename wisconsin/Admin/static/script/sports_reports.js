 /* kali code */
(function () {
    "use strict";

    var root = document.getElementById("sportsReports");
    if (!root) return;

    var JSON_URL = root.dataset.jsonUrl;
    var EXPORT_EXCEL_URL = root.dataset.exportExcelUrl;
    var EXPORT_PDF_URL = root.dataset.exportPdfUrl;

    var PAGE_SIZE = 10;
    var state = {
        reportType: "sports",
        status: "ALL",
        page: 1
    };

    var TYPE_TITLES = {
        sports: "Sports Records",
        teams: "Team Records",
        clubs: "Club Records",
        facilities: "Facility Records",
        coaches: "Coach Records",
        tournaments: "Tournament Records",
        athletes: "Olympic Athlete Records",
        performances: "Performance Records"
    };

    var COLORS = ["#c5050c", "#e8757a", "#1a8f5e", "#c78a1f", "#3b6fb6", "#7a5cc5", "#2fa3a3", "#9a0309"];

    function initCharts() {
        var dataEl = document.getElementById("sportsReportsChartData");
        if (!dataEl || typeof Chart === "undefined") return;

        var chartData;
        try {
            chartData = JSON.parse(dataEl.textContent || "{}");
        } catch (e) {
            chartData = {};
        }

        buildDoughnut("chartSportsByType", chartData.sports_by_type);
        buildBar("chartTeamsBySport", chartData.teams_by_sport);
        buildBar("chartTournamentStatus", chartData.tournament_status);
        buildDoughnut("chartMedalDistribution", chartData.medal_distribution);
    }

    function buildDoughnut(canvasId, data) {
        var canvas = document.getElementById(canvasId);
        if (!canvas || !data || !data.labels || !data.labels.length) return;

        new Chart(canvas.getContext("2d"), {
            type: "doughnut",
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: COLORS,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom", labels: { boxWidth: 10, font: { size: 11 } } }
                },
                cutout: "62%"
            }
        });
    }

    function buildBar(canvasId, data) {
        var canvas = document.getElementById(canvasId);
        if (!canvas || !data || !data.labels || !data.labels.length) return;

        new Chart(canvas.getContext("2d"), {
            type: "bar",
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: "#c5050c",
                    borderRadius: 6,
                    maxBarThickness: 34
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, ticks: { precision: 0 } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    var tableHead = document.getElementById("sportsReportsTableHead");
    var tableBody = document.getElementById("sportsReportsTableBody");
    var recordsInfo = document.getElementById("tableRecordsInfo");
    var paginationEl = document.getElementById("sportsReportsPagination");
    var tableTitle = document.getElementById("tableSectionTitle");

    function buildUrl(base, params) {
        var url = new URL(base, window.location.origin);
        Object.keys(params).forEach(function (key) {
            url.searchParams.set(key, params[key]);
        });
        return url.toString();
    }

    function fetchTableData() {
        tableBody.innerHTML = '<tr><td class="sr-table__empty">Loading records…</td></tr>';

        var url = buildUrl(JSON_URL, {
            report_type: state.reportType,
            status: state.status,
            page: state.page
        });

        fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
            .then(function (res) { return res.json(); })
            .then(renderTable)
            .catch(function () {
                tableBody.innerHTML = '<tr><td class="sr-table__empty">Unable to load records. Please try again.</td></tr>';
            });
    }

    function renderTable(data) {
        tableTitle.textContent = TYPE_TITLES[state.reportType] || "Records";

        var columns = data.columns || [];
        var rows = data.rows || [];

        tableHead.innerHTML =
            "<tr>" +
            columns.map(function (col) { return "<th>" + col.label + "</th>"; }).join("") +
            "</tr>";

        if (!rows.length) {
            tableBody.innerHTML =
                '<tr><td class="sr-table__empty" colspan="' + columns.length + '">No records found for this filter.</td></tr>';
        } else {
            tableBody.innerHTML = rows.map(function (row) {
                return "<tr>" + columns.map(function (col) {
                    return "<td>" + renderCell(col.key, row[col.key]) + "</td>";
                }).join("") + "</tr>";
            }).join("");
        }

        renderPagination(data);
        renderRecordsInfo(data);
        if (window.lucide) { window.lucide.createIcons(); }
    }

    function renderCell(key, value) {
        if (value === null || value === undefined || value === "") return "—";

        if (key === "status") {
            var cls = value === "Active" ? "sr-badge--active" : "sr-badge--inactive";
            return '<span class="sr-badge ' + cls + '">' + value + "</span>";
        }

        if (key === "medal") {
            var medalCls = { Gold: "sr-badge--gold", Silver: "sr-badge--silver", Bronze: "sr-badge--bronze" }[value] || "sr-badge--none";
            return '<span class="sr-badge ' + medalCls + '">' + value + "</span>";
        }

        return String(value);
    }

    function renderRecordsInfo(data) {
        var total = data.count || 0;
        var start = total === 0 ? 0 : (data.page - 1) * data.page_size + 1;
        var end = Math.min(total, data.page * data.page_size);
        recordsInfo.textContent = total === 0
            ? "No records"
            : "Showing " + start + "–" + end + " of " + total + " records";
    }

    function renderPagination(data) {
        var numPages = data.num_pages || 1;
        var current = data.page || 1;
        paginationEl.innerHTML = "";

        if (numPages <= 1) return;

        paginationEl.appendChild(makePageBtn("«", current - 1, current === 1));

        var startPage = Math.max(1, current - 2);
        var endPage = Math.min(numPages, startPage + 4);
        startPage = Math.max(1, endPage - 4);

        for (var p = startPage; p <= endPage; p++) {
            var btn = makePageBtn(String(p), p, false, p === current);
            paginationEl.appendChild(btn);
        }

        paginationEl.appendChild(makePageBtn("»", current + 1, current === numPages));
    }

    function makePageBtn(label, targetPage, disabled, active) {
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "sr-pagination__btn" + (active ? " is-active" : "");
        btn.textContent = label;
        btn.disabled = !!disabled;
        btn.addEventListener("click", function () {
            state.page = targetPage;
            fetchTableData();
        });
        return btn;
    }

    var reportTypeSelect = document.getElementById("reportTypeSelect");
    var statusSelect = document.getElementById("statusSelect");
    var applyFilterBtn = document.getElementById("applyFilterBtn");
    var resetFilterBtn = document.getElementById("resetFilterBtn");
    var reportTypeChoices = new Choices(reportTypeSelect, {
    searchEnabled: false,
    itemSelectText: "",
    shouldSort: false
});
var statusChoices = new Choices(statusSelect, {
    searchEnabled: false,
    itemSelectText: "",
    shouldSort: false
});

    applyFilterBtn.addEventListener("click", function () {
        state.reportType = reportTypeSelect.value;
        state.status = statusSelect.value;
        state.page = 1;
        fetchTableData();
    });



    resetFilterBtn.addEventListener("click", function () {
        reportTypeChoices.setChoiceByValue("sports");
        statusChoices.setChoiceByValue("ALL");
        state.reportType = "sports";
        state.status = "ALL";
        state.page = 1;
        fetchTableData();
    });

    var exportDropdown = document.getElementById("exportDropdown");
    var exportToggleBtn = document.getElementById("exportToggleBtn");
    var exportPdfBtn = document.getElementById("exportPdfBtn");
    var exportExcelBtn = document.getElementById("exportExcelBtn");

    exportToggleBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        exportDropdown.classList.toggle("is-open");
    });

    document.addEventListener("click", function (e) {
        if (!exportDropdown.contains(e.target)) {
            exportDropdown.classList.remove("is-open");
        }
    });

    exportPdfBtn.addEventListener("click", function (e) {
        e.preventDefault();
        exportDropdown.classList.remove("is-open");
        window.location.href = buildUrl(EXPORT_PDF_URL, {
            report_type: state.reportType,
            status: state.status
        });
    });

    exportExcelBtn.addEventListener("click", function (e) {
        e.preventDefault();
        exportDropdown.classList.remove("is-open");
        window.location.href = buildUrl(EXPORT_EXCEL_URL, {
            report_type: state.reportType,
            status: state.status
        });
    });

    function init() {
        initCharts();
        fetchTableData();
    }

    if (document.readyState === "complete" || document.readyState === "interactive") {
        init();
    } else {
        document.addEventListener("DOMContentLoaded", init);
    }
})();