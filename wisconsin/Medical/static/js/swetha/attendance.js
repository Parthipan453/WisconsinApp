// swetha's code

function updateDateTime() {
  const now = new Date();

  document.getElementById("currentDate").textContent = now.toLocaleDateString(
    "en-IN",
    {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    },
  );
}

updateDateTime();

let attendanceRecords = [];
let filteredRecords = [];
let currentPage = 1;
const recordsPerPage = 10;

function updateStats(stats) {
  document.getElementById("totalDays").textContent = stats.total_days;
  document.getElementById("workingDays").textContent = stats.working_days;
  document.getElementById("avgHours").textContent = stats.avg_hours;
  document.getElementById("overtimeHours").textContent = stats.overtime_hours;
  document.getElementById("lateCount").textContent = stats.late_count;
}

function updateToday(today) {
  document.getElementById("checkIn").textContent = today.check_in;
  document.getElementById("checkOut").textContent = today.check_out;
  document.getElementById("workingHours").textContent = today.hours;
  document.getElementById("shift").textContent = today.shift;
  document.getElementById("shiftTime").textContent = today.shift_time;
  document.getElementById("todayStatusText").textContent = today.status;

  const badge = document.querySelector(".status-indicator");

  if (today.holiday) {
    badge.classList.remove("present", "holiday", "absent");
    badge.classList.add("working-holiday");

    badge.innerHTML = `<i class="fas fa-circle"></i> HOLIDAY`;
  } else if (today.present) {
    badge.classList.remove("absent", "holiday");
    badge.classList.add("present");

    badge.innerHTML = `<i class="fas fa-circle"></i> PRESENT`;
  } else {
    badge.classList.remove("present", "holiday");
    badge.classList.add("absent");

    badge.innerHTML = `<i class="fas fa-circle"></i> ABSENT`;
  }
}

function renderRecords(records, page = 1) {
  filteredRecords = records;
  currentPage = page;

  const tbody = document.getElementById("recordsBody");

  if (!tbody) return;

  tbody.innerHTML = "";

  const start = (page - 1) * recordsPerPage;
  const end = start + recordsPerPage;

  const pageRecords = records.slice(start, end);

  if (pageRecords.length === 0) {
    tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">
                    No attendance records found.
                </td>
            </tr>
        `;
  } else {
    pageRecords.forEach((record) => {
      tbody.innerHTML += `
                <tr>
                    <td>${record.no}</td>
                    <td>${record.date}</td>
                    <td>${record.check_in}</td>
                    <td>${record.check_out}</td>
                    <td>${record.hours}</td>

                    <td>
                        <span class="status-badge-small ${record.status.toLowerCase()}">
                            ${record.status}
                        </span>
                    </td>

                    <td>${record.remarks}
                    </td>
                </tr>
            `;
    });
  }

  document.getElementById("recordCount").textContent =
    `Showing ${records.length === 0 ? 0 : start + 1}-${Math.min(end, records.length)} of ${records.length} Records`;

  renderPagination(records.length);
}

function renderPagination(totalRecords) {
  const pageNumbers = document.getElementById("pageNumbers");
  const prevPage = document.getElementById("prevPage");
  const nextPage = document.getElementById("nextPage");

  if (!pageNumbers) return;

  pageNumbers.innerHTML = "";

  const totalPages = Math.ceil(totalRecords / recordsPerPage);

  // No records
  if (totalPages === 0) {
    if (prevPage) prevPage.disabled = true;
    if (nextPage) nextPage.disabled = true;
    return;
  }

  // Page buttons
  for (let i = 1; i <= totalPages; i++) {
    const btn = document.createElement("button");

    btn.className = "page-btn";
    btn.textContent = i;

    if (i === currentPage) {
      btn.classList.add("active");
    }

    btn.addEventListener("click", () => {
      renderRecords(filteredRecords, i);
    });

    pageNumbers.appendChild(btn);
  }

  if (prevPage) {
    prevPage.disabled = currentPage === 1;
  }

  if (nextPage) {
    nextPage.disabled = currentPage === totalPages;
  }
}



async function loadAttendance(month = "", year = "") {

    const futureMonthMessage =
        document.getElementById("futureMonthMessage");

    const futureMonthText =
        document.getElementById("futureMonthText");

    const recordsBody =
        document.getElementById("recordsBody");

    if (month && year) {

        const selectedMonth = parseInt(month);
        const selectedYear = parseInt(year);

        const now = new Date();

        const currentMonth = now.getMonth() + 1;
        const currentYear = now.getFullYear();

        // --------------------------------------------------
        // FUTURE MONTH CHECK
        // --------------------------------------------------

        const isFutureMonth =
            selectedYear > currentYear ||
            (
                selectedYear === currentYear &&
                selectedMonth > currentMonth
            );

        if (isFutureMonth) {

            // Show future month message
            if (futureMonthMessage) {
                futureMonthMessage.style.display = "flex";
            }

            if (futureMonthText) {

                const monthName = new Date(
                    selectedYear,
                    selectedMonth - 1,
                    1
                ).toLocaleString("en-US", {
                    month: "long"
                });

                futureMonthText.textContent =
                    `You are viewing ${monthName} ${selectedYear}`;
            }

            // Clear attendance table
            if (recordsBody) {

                recordsBody.innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center">
                            No attendance records available for this future month.
                        </td>
                    </tr>
                `;
            }

            // Reset stats
            updateStats({
                total_days: 0,
                working_days: 0,
                avg_hours: "0h 0m",
                overtime_hours: "0h 0m",
                late_count: 0
            });

            // Reset today
            updateToday({
                check_in: "--",
                check_out: "--",
                hours: "--",
                shift: "--",
                shift_time: "--",
                status: "Future Month",
                present: false,
                holiday: false
            });

            // Reset record count
            const recordCount =
                document.getElementById("recordCount");

            if (recordCount) {
                recordCount.textContent =
                    "Showing 0-0 of 0 Records";
            }

            // Reset pagination
            const pageNumbers =
                document.getElementById("pageNumbers");

            if (pageNumbers) {
                pageNumbers.innerHTML = "";
            }

            const prevPage =
                document.getElementById("prevPage");

            const nextPage =
                document.getElementById("nextPage");

            if (prevPage) {
                prevPage.disabled = true;
            }

            if (nextPage) {
                nextPage.disabled = true;
            }

            // Reset chart
            centerPercentage = "0%";

            drawAttendanceChart({
                present: 0,
                leave: 0,
                holiday: 0,
                absent: 0,
                attendance_rate: 0
            });

            drawTrendChart({
                labels: [],
                hours: []
            });

            // Reset breakdown counts
            document.getElementById("presentCount").textContent = "0";
            document.getElementById("leaveCount").textContent = "0";
            document.getElementById("holidayCount").textContent = "0";
            document.getElementById("absentCount").textContent = "0";

            attendanceRecords = [];
            filteredRecords = [];
            currentPage = 1;

            return;
        }
    }

    // --------------------------------------------------
    // NORMAL / CURRENT / PREVIOUS MONTH
    // --------------------------------------------------

    if (futureMonthMessage) {
        futureMonthMessage.style.display = "none";
    }

    let url = attendanceURL;

    if (month && year) {
        url += `?month=${month}&year=${year}`;
    }

    try {

        const response = await fetch(url);

        const data = await response.json();

        attendanceRecords = data.records || [];

        updateStats(data.stats);

        updateToday(data.today);

        renderRecords(
            attendanceRecords,
            1
        );

        centerPercentage =
            data.charts.breakdown.attendance_rate + "%";

        drawAttendanceChart(
            data.charts.breakdown
        );

        document.getElementById(
            "presentCount"
        ).textContent =
            data.charts.breakdown.present;

        document.getElementById(
            "leaveCount"
        ).textContent =
            data.charts.breakdown.leave;

        document.getElementById(
            "holidayCount"
        ).textContent =
            data.charts.breakdown.holiday;

        document.getElementById(
            "absentCount"
        ).textContent =
            data.charts.breakdown.absent;

        drawTrendChart(
            data.charts.trend
        );

    } catch (err) {

        console.error(
            "Attendance Load Error:",
            err
        );
    }
}



function populateMonthFilter() {
  const monthFilter = document.getElementById("monthFilter");

  const months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];

  monthFilter.innerHTML = "";

  months.forEach((month, index) => {
    const option = document.createElement("option");
    option.value = index + 1;
    option.textContent = month;

    if (index + 1 === new Date().getMonth() + 1) {
      option.selected = true;
    }

    monthFilter.appendChild(option);
  });
}
function populateYearFilter() {
  const yearFilter = document.getElementById("yearFilter");

  const currentYear = new Date().getFullYear();

  yearFilter.innerHTML = "";

  for (let year = currentYear; year >= currentYear - 5; year--) {
    const option = document.createElement("option");
    option.value = year;
    option.textContent = year;

    if (year === currentYear) {
      option.selected = true;
    }

    yearFilter.appendChild(option);
  }
  console.log(yearFilter.options.length);
  console.log(yearFilter.innerHTML);
}

setInterval(updateDateTime, 1000);

document.addEventListener("DOMContentLoaded", function () {
  populateMonthFilter();
  populateYearFilter();

  const monthFilter = document.getElementById("monthFilter");
  const yearFilter = document.getElementById("yearFilter");
  console.log(yearFilter.value);
  console.log(yearFilter.selectedIndex);

  // Choices.js
  new Choices(monthFilter, {
    searchEnabled: false,
    itemSelectText: "",
    shouldSort: false,
    allowHTML: false,
    position: "bottom",
  });

  new Choices(yearFilter, {
    searchEnabled: false,
    itemSelectText: "",
    shouldSort: false,
    allowHTML: false,
    position: "bottom",
  });

  // Initial Load
  loadAttendance(monthFilter.value, yearFilter.value);

  // Month Change
  monthFilter.addEventListener("change", function () {
    currentPage = 1;
    loadAttendance(monthFilter.value, yearFilter.value);
  });

  // Year Change
  yearFilter.addEventListener("change", function () {
    currentPage = 1;
    loadAttendance(monthFilter.value, yearFilter.value);
  });

  const exportBtn = document.getElementById("exportBtn");

  if (exportBtn) {
    exportBtn.addEventListener("click", function () {
      const month = document.getElementById("monthFilter").value;
      const year = document.getElementById("yearFilter").value;

      window.location.href = `${exportURL}?month=${month}&year=${year}`;
    });
  }

  const searchInput = document.getElementById("searchRecords");

  if (searchInput) {
    searchInput.addEventListener("input", function () {
      const keyword = this.value.trim().toLowerCase();

      const filtered = attendanceRecords.filter(
        (record) =>
          record.date.toLowerCase().includes(keyword) ||
          record.status.toLowerCase().includes(keyword) ||
          record.remarks.toLowerCase().includes(keyword),
      );

      renderRecords(filtered, 1);
    });
  }

  // ==========================
  // Previous Page
  // ==========================
  const prevPage = document.getElementById("prevPage");

  if (prevPage) {
    prevPage.addEventListener("click", function () {
      if (currentPage > 1) {
        currentPage--;

        renderRecords(filteredRecords, currentPage);
      }
    });
  }

  // ==========================
  // Next Page
  // ==========================
  const nextPage = document.getElementById("nextPage");

  if (nextPage) {
    nextPage.addEventListener("click", function () {
      const totalPages = Math.ceil(filteredRecords.length / recordsPerPage);

      if (currentPage < totalPages) {
        currentPage++;

        renderRecords(filteredRecords, currentPage);
      }
    });
  }
});

// ==============================
// Charts
// ==============================

let attendanceChart = null;
let trendChart = null;
let centerPercentage = "0%";

const centerText = {
  id: "centerText",

  afterDraw(chart) {
    const { ctx } = chart;
    const meta = chart.getDatasetMeta(0);

    if (!meta.data.length) return;

    const x = meta.data[0].x;
    const y = meta.data[0].y;

    ctx.save();
    const chartWidth = chart.width;

    let percentageFont = 23;
    let labelFont = 10;

    if (chartWidth < 220) {
      percentageFont = 18;
      labelFont = 8;
    }

    if (chartWidth < 180) {
      percentageFont = 15;
      labelFont = 7;
    }

    // ctx.font = "bold 23px Inter";
    ctx.font = `bold ${percentageFont}px Inter`;
    ctx.fillStyle = "#111827";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(centerPercentage, x, y - 10);

    // ctx.font = "500 10px Inter";
    ctx.font = `500 ${labelFont}px Inter`;
    ctx.fillStyle = "#6b7280";
    ctx.fillText("Attendance", x, y + 13);

    ctx.restore();
  },
};

function drawAttendanceChart(chartData) {
  const ctx = document.getElementById("attendanceChart");

  if (!ctx) return;

  if (attendanceChart) {
    attendanceChart.destroy();
  }

  attendanceChart = new Chart(ctx, {
    type: "doughnut",

    data: {
      labels: ["Present", "Leave", "Holiday", "Absent"],

      datasets: [
        {
          data: [
            chartData.present,
            chartData.leave,
            chartData.holiday,
            chartData.absent,
          ],

          backgroundColor: ["#22c55e", "#f59e0b", "#3b82f6", "#ef4444"],

          borderWidth: 0,
          hoverOffset: 8,
        },
      ],
    },

    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "70%",

      plugins: {
        legend: {
          display: false,
        },
      },
    },

    plugins: [centerText],
  });
}

function drawTrendChart(trend) {
    const ctx = document.getElementById("attendanceTrendChart");

    if (!ctx) return;

    if (trendChart) {
        trendChart.destroy();
    }

    const labels = trend.labels || [];
    const hours = labels.map((_, index) => {
        const value = trend.hours?.[index];
        return value == null || value === "" ? 0 : Number(value);
    });

    trendChart = new Chart(ctx, {
        type: "line",

        data: {
            labels: labels,

            datasets: [
                {
                    label: "Working Hours",

                    data: hours,

                    borderColor: "#c5050c",
                    backgroundColor: "rgba(197,5,12,.12)",

                    fill: true,
                    tension: 0.4,

                    borderWidth: 3,

                    pointRadius: 5,
                    pointHoverRadius: 7,

                    pointBackgroundColor: "#c5050c",

                    pointBorderColor: "#ffffff",
                    pointBorderWidth: 2,
                },
            ],
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,

            plugins: {
                legend: {
                    display: false,
                },
            },

            scales: {
                y: {
                    beginAtZero: true,
                },
            },
        },
    });
}