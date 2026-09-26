document.addEventListener("DOMContentLoaded", function () {
    var rolePermEl = document.getElementById("role-permission-data");
    var actionEl = document.getElementById("action-count-data");

    if (!rolePermEl || !actionEl || typeof Chart === "undefined") return;

    var roleData = JSON.parse(rolePermEl.textContent);
    var actionData = JSON.parse(actionEl.textContent);

    var chartFont = { family: "inherit", size: 12 };

    if (roleData.length) {
        var ctx1 = document.getElementById("rolePermissionChart").getContext("2d");
        new Chart(ctx1, {
        type: "bar",
        data: {
            labels: roleData.map(function (r) { return r.role_name; }),
            datasets: [{
            label: "Permissions Granted",
            data: roleData.map(function (r) { return r.perm_count; }),
            backgroundColor: "#c5050c",
            borderRadius: 6,
            maxBarThickness: 36,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
            x: { ticks: { font: chartFont }, grid: { display: false } },
            y: { beginAtZero: true, ticks: { precision: 0, font: chartFont } },
            },
        },
        });
    }

    if (actionData.length) {
        var ctx2 = document.getElementById("actionBreakdownChart").getContext("2d");
        var palette = ["#c5050c", "#2563eb", "#16a34a", "#d97706", "#7c3aed", "#6b7280"];
        new Chart(ctx2, {
        type: "doughnut",
        data: {
            labels: actionData.map(function (a) { return a.label; }),
            datasets: [{
            data: actionData.map(function (a) { return a.count; }),
            backgroundColor: actionData.map(function (_, i) { return palette[i % palette.length]; }),
            borderWidth: 0,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "65%",
            plugins: {
            legend: { position: "bottom", labels: { boxWidth: 10, padding: 14, font: chartFont } },
            },
        },
        });
    }
});