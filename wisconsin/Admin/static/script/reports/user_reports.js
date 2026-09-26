// ur-btn ddropdown
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
document.querySelector(".roleBtn").addEventListener("click", function (e) {
    e.preventDefault();
    e.stopPropagation();

    document.querySelector(".genderMenu").classList.remove("show");
    document.querySelector(".statusMenu").classList.remove("show");

    document.querySelector(".roleMenu").classList.toggle("show");
});

document.querySelector(".genderBtn").addEventListener("click", function (e) {
    e.preventDefault();

    document.querySelector(".roleMenu").classList.remove("show");
    document.querySelector(".statusMenu").classList.remove("show");

    document.querySelector(".genderMenu").classList.toggle("show");
});

document.querySelector(".statusBtn").addEventListener("click", function (e) {
    e.preventDefault();

    document.querySelector(".roleMenu").classList.remove("show");
    document.querySelector(".genderMenu").classList.remove("show");

    document.querySelector(".statusMenu").classList.toggle("show");
});
// excel button
document.querySelector(".excelBtn").addEventListener("click", function () {

    document.querySelectorAll(".ur-submenu-content").forEach(menu => {
        menu.classList.remove("show");
    });

});


// chart
document.addEventListener("DOMContentLoaded", () => {

    const registrationYears = JSON.parse(document.getElementById("registration-years").textContent);
    const registrationCounts = JSON.parse(document.getElementById("registration-counts").textContent);
    // Registration chart
    const registrationCtx = document.getElementById("registrationChart");
    if (registrationCtx) {
        new Chart(registrationCtx, {
            type: "line",
            data: {
                labels: registrationYears,
                datasets: [{
                    label: "Registrations",
                    data: registrationCounts,

                    borderColor: "#c5050c",
                    backgroundColor: "rgba(197,5,12,.12)",

                    fill: true,
                    tension: .4
                }]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    // Gender Chart
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
            // let fontSize = Math.max(10, chart.width / 18);
            let fontSize = Math.min(chart.width, chart.height) / 12;
            ctx.save();

            ctx.textAlign = "center";
            ctx.textBaseline = "middle";

            // Heading
            ctx.font = `bold ${fontSize * 0.6}px Encode Sans`;
            // ctx.font = "bold 16px Arial";
            ctx.fillStyle = "#333";
            ctx.fillText("Gender report", x, y - fontSize / 2);
            ctx.restore();
        }
    };

    Chart.register(centerTextPlugin);
    const genderCtx = document.getElementById("genderChart");
    const maleCount = JSON.parse(document.getElementById("male-count").textContent);
    const femaleCount = JSON.parse(document.getElementById("female-count").textContent);
    const transgenderCount = JSON.parse(document.getElementById("transgender-count").textContent);
    const nonBinaryCount = JSON.parse(document.getElementById("non-binary-count").textContent);
    const otherCount = JSON.parse(document.getElementById("other-count").textContent);

    const preferNotSayCount =
        JSON.parse(document.getElementById("prefer-not-say-count").textContent);
    if (genderCtx) {
        new Chart(genderCtx, {
            type: "doughnut",
            data: {
                labels: ["Male", "Female", "Transgender", "Non-Binary", "Other", "Prefer Not To Say"],
                datasets: [{
                    label: "Users",
                    data: [
                        maleCount,
                        femaleCount,
                        transgenderCount,
                        nonBinaryCount,
                        otherCount,
                        preferNotSayCount
                    ],
                    backgroundColor: [
                        "#3b82f6",
                        "#ec4899",
                        "#8b5cf6",
                        "#14b8a6",
                        "#f59e0b",
                        "#9ca3af"
                    ],
                    borderRadius: 8,
                    maxBarThickness: 60
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "70%",
                plugins: [centerTextPlugin]
            }
        });
    }
    // Status Chart
    const statusCtx = document.getElementById("statusChart");
    const activeCount = JSON.parse(document.getElementById("active-count").textContent);
    const inactiveCount = JSON.parse(
        document.getElementById("inactive-count").textContent
    );

    const pendingCount =
        JSON.parse(
            document.getElementById("pending-count").textContent
        );
    const suspendedCount =
        JSON.parse(
            document.getElementById("suspended-count").textContent
        );
    if (statusCtx) {
        new Chart(statusCtx, {
            type: "bar",
            data: {
                labels: ["Active", "Inactive", "Pending", "Suspended"],

                datasets: [{
                    label: "users",
                    data: [
                        activeCount,
                        inactiveCount,
                        pendingCount,
                        suspendedCount
                    ],
                    backgroundColor: [
                        "#22c55e", // Active
                        "#9ca3af", // Inactive
                        "#f59e0b", // Pending
                        "#ef4444"  // Suspended

                    ],
                    borderRadius: 10,
                    categoryPercentage: 0.6,
                    barPercentage: 0.7,
                    maxBarThickness: 40

                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
});

// =====================================================
// OVERALL RECENT REGISTRATIONS SEARCH
// =====================================================

let searchTimer;

document.addEventListener("input", function (e) {

    if (e.target.id !== "ur-search") return;

    clearTimeout(searchTimer);

    const searchValue = e.target.value.trim();

    // Wait while user is typing
    searchTimer = setTimeout(() => {

        const url = new URL(window.location.href);

        // Add search query
        if (searchValue) {
            url.searchParams.set("q", searchValue);
        } else {
            url.searchParams.delete("q");
        }

        // Always return to first page after search
        url.searchParams.set("page", "1");

        fetch(url.toString())
            .then(res => res.text())
            .then(html => {

                const parser = new DOMParser();

                const doc = parser.parseFromString(
                    html,
                    "text/html"
                );

                const newContent =
                    doc.querySelector("#recent-users-container");

                if (newContent) {

                    document.querySelector(
                        "#recent-users-container"
                    ).innerHTML = newContent.innerHTML;
                }

                // Update browser URL
                window.history.replaceState(
                    {},
                    "",
                    url.toString()
                );

            })
            .catch(error => {
                console.error(
                    "Search error:",
                    error
                );
            });

    }, 400);

});

// pagination
// =====================================================
// PAGINATION
// =====================================================

document.addEventListener("click", function (e) {

    const btn = e.target.closest(".ur-page-btn");

    if (!btn || btn.tagName !== "A") return;

    e.preventDefault();

    fetch(btn.href)
        .then(res => res.text())
        .then(html => {

            const parser = new DOMParser();

            const doc = parser.parseFromString(
                html,
                "text/html"
            );

            const newContent =
                doc.querySelector(
                    "#recent-users-container"
                );

            if (newContent) {

                document.querySelector(
                    "#recent-users-container"
                ).innerHTML =
                    newContent.innerHTML;

                // Update URL
                window.history.pushState(
                    {},
                    "",
                    btn.href
                );
            }

        })
        .catch(error => {
            console.error(
                "Pagination error:",
                error
            );
        });

});