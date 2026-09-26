/* ═════ GURU CODE ═════ */

let STUDENTS = []
let DASHBOARD = {}
let TREND = []
let filtered = [...STUDENTS];

async function fetchStudents(){
  try{
    const res = await fetch('/dashboard/api/students/list/')
    const data = await res.json()

    DASHBOARD = {
      "total": data.total_students,
      "active": data.active_students,
      "leave": data.leave_students,
      "graduated": data.graduated_students,
      "withdrawn": data.withdrawn_students,
    }

    TREND = data.student_trend || []

    updateStatCards();
    updateProgressBars();
    initCharts();
    
    STUDENTS = data.students || []

    STUDENTS = STUDENTS.map(stu=>({
      id: String(stu.id),
      name: stu.preferred_name,
      image: stu.image,
      email: stu.university_email,
      program: stu.program || "Not specified",
      level: stu.academic_level,
      gpa: parseFloat(stu.cumulative_gpa),
      status: stu.current_status,
      grad: stu.expected_graduation_date,
      initials: getInitials(stu.preferred_name),
      color: getRandomColor(),
      _raw: stu,
    }))

    
    filtered = [...STUDENTS];

    renderView()
    
  }
  catch(err){
    console.log(err, "Students data err");
  }
}

function updateStatCards() {
  document.querySelector('#total_stu .oc-value').textContent =
    DASHBOARD.total;

  document.querySelector('#active_stu .oc-value').textContent =
    DASHBOARD.active;

  document.querySelector('#graduated_stu .oc-value').textContent =
    DASHBOARD.graduated;

  document.querySelector('#leave_stu .oc-value').textContent =
    DASHBOARD.leave;

  const activeTotal = DASHBOARD.total - DASHBOARD.withdrawn;

  document.querySelector('#total_stu .oc-change').innerHTML =
    `<i class="ti ti-arrow-up"></i> ${
      DASHBOARD.total > 0
        ? Math.round((DASHBOARD.total / DASHBOARD.total) * 100)
        : 0
    }%`;


  document.querySelector('#active_stu .oc-change').innerHTML =
    `<i class="ti ti-arrow-up"></i> ${
      DASHBOARD.total > 0
        ? Math.round((DASHBOARD.active / DASHBOARD.total) * 100)
        : 0
    }%`;

  document.querySelector('#graduated_stu .oc-change').innerHTML =
    `<i class="ti ti-arrow-up"></i> ${
      DASHBOARD.total > 0
        ? Math.round((DASHBOARD.graduated / DASHBOARD.total) * 100)
        : 0
    }%`;

  document.querySelector('#leave_stu .oc-change').innerHTML =
    `<i class="ti ti-arrow-down"></i> ${
      DASHBOARD.total > 0
        ? Math.round((DASHBOARD.withdrawn / DASHBOARD.total) * 100)
        : 0
    }%`;
}

function updateProgressBars() {
  const total = DASHBOARD.total || 1;
  const activeTotal = total - DASHBOARD.withdrawn;

  document.querySelector('.oc-fill-primary').style.width =
    `${(DASHBOARD.total / total) * 100}%`;

  document.querySelector('.oc-fill-success').style.width =
    `${(DASHBOARD.active / total) * 100}%`;

  document.querySelector('.oc-fill-secondary').style.width =
    `${(DASHBOARD.graduated / total) * 100}%`;

  document.querySelector('.oc-fill-warning').style.width =
    `${(DASHBOARD.leave / total) * 100}%`;
}

function getInitials(name) {
  if (!name) return 'NA';
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .substring(0, 2);
}

function getRandomColor() {
  const colors = [
    '#c5050c', '#185fa5', '#228b22', '#f59e0b',
    '#7c3aed', '#dc2626', '#0f6e56', '#b45309',
    '#0891b2', '#d946ef', '#f43f5e', '#e11d48'
  ];
  return colors[Math.floor(Math.random() * colors.length)];
}

let currentPage = 1;
const PER_PAGE = 10;
let currentView = "table";

function statusClass(s) {
  return {
    ACTIVE: "sp-active",
    LEAVE: "sp-leave",
    GRADUATED: "sp-graduated",
    WITHDRAWN: "sp-withdrawn",
  }[s] || "";
}

function levelClass(l) {
  return {
    UNDERGRADUATE: "lc-ug",
    GRADUATE: "lc-grad",
    PHD: "lc-phd",
  }[l] || "";
}

function gpaClass(g) {
  if (g >= 3.7) return "gpa-high";
  if (g >= 3.3) return "gpa-mid";
  return "gpa-low";
}

function filterTable() {
  const q = (document.getElementById("tableSearch").value || "").toLowerCase();
  const status = document.getElementById("filterStatus").value;
  const level = document.getElementById("filterLevel").value;

  const statusUp = (status || "").toUpperCase();
  const levelUp = (level || "").toUpperCase();

  filtered = STUDENTS.filter((s) => {

    const matchQ =
      !q ||
      s.name.toLowerCase().includes(q) ||
      s.id.toLowerCase().includes(q) ||
      s.email.toLowerCase().includes(q) ||
      s.program.toLowerCase().includes(q);

    const matchS = !statusUp || s.status === statusUp;
    const matchL = !levelUp || s.level === levelUp;
    return matchQ && matchS && matchL;
  });
  currentPage = 1;
  renderView();
}

function renderTable() {
  const tbody = document.getElementById("tableBody");
  const empty = document.getElementById("emptyState");
  const pagBar = document.getElementById("paginationBar");
  const info = document.getElementById("paginationInfo");
  const count = document.getElementById("resultCount");

  if (!filtered.length) {
    tbody.innerHTML = "";
    empty.style.display = "block";
    pagBar.style.display = "none";
    count.textContent = "Showing 0 results";
    return;
  }

  empty.style.display = "none";
  pagBar.style.display = "flex";

  const start = (currentPage - 1) * PER_PAGE;
  const page = filtered.slice(start, start + PER_PAGE);
  const total = filtered.length;

  count.textContent = `Showing ${Math.min(start + 1, total)}–${Math.min(start + PER_PAGE, total)} of ${total}`;
  info.textContent = `Showing ${Math.min(start + 1, total)}–${Math.min(start + PER_PAGE, total)} of ${total} students`;

  tbody.innerHTML = page
    .map(
      (s) => `
      <tr data-id="${s.id}">
        <td>
          <div class="student-cell">
            <div class="s-avatar" style="background:${s.color}">
              ${
                s.image
                  ? `<img src="${s.image}" alt="${s.name}" class="sc-avatar-img">`
                  : s.initials
              }
            </div>
            <div>
              <div class="s-name">${s.name}</div>
            </div>
          </div>
        </td>
        <td class="col-email" style="color:#555">${s.email}</td>
        <td class="col-program">${s.program}</td>
        <td class="col-level"><span class="level-chip ${levelClass(s.level)}">${s.level}</span></td>
        <td class="col-gpa"><span class="gpa-val ${gpaClass(s.gpa)}">${s.gpa > 0 ? s.gpa.toFixed(2) : "—"}</span></td>
        <td><span class="status-pill ${statusClass(s.status)}">${s.status}</span></td>
        <td class="col-grad" style="color:#555;white-space:nowrap">${s.grad}</td>
        <td>
          <div class="row-actions">
            <a href="/dashboard/student_view/${s.id}" class="act-btn act-view"><i class="ti ti-eye"></i></a>
            <a class="act-btn act-edit" onclick="editStudent('${s.id}')"><i class="ti ti-edit"></i></a>
          </div>
        </td>
      </tr>
    `,
    )
    .join("");

  renderPagination(total);
}

function renderGrid() {
  const grid = document.getElementById("cardGrid");
  const emptyGrid = document.getElementById("emptyStateGrid");

  if (!filtered.length) {
    grid.innerHTML = "";
    emptyGrid.style.display = "block";
    return;
  }

  emptyGrid.style.display = "none";
  const start = (currentPage - 1) * PER_PAGE;
  const page = filtered.slice(start, start + PER_PAGE);

  grid.innerHTML = page
    .map(
      (s) => `
      <div class="student-card">
        <div class="sc-head">
          <div class="sc-avatar" style="background:${s.color}">
              ${
                s.image
                  ? `<img src="${s.image}" alt="${s.name}" class="sc-avatar-img">`
                  : s.initials
              }
          </div>
          <div>
            <div class="sc-name">${s.name}</div>
          </div>
        </div>
        <hr class="sc-divider">
        <div class="sc-row"><span class="sc-lbl">Program</span><span class="sc-val">${s.program}</span></div>
        <div class="sc-row"><span class="sc-lbl">Level</span><span class="level-chip ${levelClass(s.level)}">${s.level}</span></div>
        <div class="sc-row"><span class="sc-lbl">GPA</span><span class="gpa-val ${gpaClass(s.gpa)}">${s.gpa > 0 ? s.gpa.toFixed(2) : "—"}</span></div>
        <div class="sc-row"><span class="sc-lbl">Grad</span><span class="sc-val">${s.grad}</span></div>
        <div class="sc-footer">
          <span class="status-pill ${statusClass(s.status)}">${s.status}</span>
          <div class="sc-actions">
            <a href="/dashboard/student_view/${s.id}" class="sc-act view"><i class="ti ti-eye"></i></a>
            <a class="sc-act edit" onclick="editStudent('${s.id}')"><i class="ti ti-edit"></i></a>
          </div>
        </div>
      </div>
    `,
    )
    .join("");
}

function renderPagination(total) {
  const pages = Math.ceil(total / PER_PAGE);
  const btns = document.getElementById("paginationBtns");
  if (!btns) return;
  let html = `<button class="pag-btn" ${currentPage === 1 ? "disabled" : ""} onclick="goPage(${currentPage - 1})"><i class="ti ti-chevron-left"></i></button>`;
  for (let p = 1; p <= pages; p++) {
    html += `<button class="pag-btn ${p === currentPage ? "active" : ""}" onclick="goPage(${p})">${p}</button>`;
  }
  html += `<button class="pag-btn" ${currentPage === pages ? "disabled" : ""} onclick="goPage(${currentPage + 1})"><i class="ti ti-chevron-right"></i></button>`;
  btns.innerHTML = html;
}

function goPage(p) {
  const pages = Math.ceil(filtered.length / PER_PAGE);
  if (p < 1 || p > pages) return;
  currentPage = p;
  renderView();
  document
    .querySelector(".content-wrapper")
    .scrollTo({ top: 0, behavior: "smooth" });
}

function switchView(v) {
  currentView = v;
  document.getElementById("tableView").style.display =
    v === "table" ? "block" : "none";
  document.getElementById("gridView").style.display =
    v === "grid" ? "block" : "none";
  document.getElementById("btnTable").classList.toggle("active", v === "table");
  document.getElementById("btnGrid").classList.toggle("active", v === "grid");
  renderView();
}

function renderView() {
  if (currentView === "table") renderTable();
  else renderGrid();
}

function viewStudent(id) {
  alert(`View profile: ${id}`);
}
function editStudent(id) {
  alert(`Edit student: ${id}`);
}

  function initCharts() {
    const ctx1 = document.getElementById("trendChart").getContext("2d");
    new Chart(ctx1, {
      type: "line",
      data: {
        labels: TREND.map(item => item.year),
        datasets: [{
          label: "Total Students",
          data: TREND.map(item => item.stu_total),
          borderColor: "#c5050c",
          backgroundColor: "rgba(197, 5, 11, 0.22)",
          fill: true,
          tension: 0.3,
          pointRadius: 5,
          pointBackgroundColor: "#c5050c",
          pointBorderColor: "#fff",
          pointBorderWidth: 2,
          borderWidth: 3,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return 'Total: ' + context.parsed.y + ' students';
              }
            }
          }
        },
        scales: {
          y: { 
            beginAtZero: false,
            min: 2000,
            max: 8000,
            grid: { color: "rgba(0,0,0,0.06)" }, 
            ticks: { 
              font: { size: 11 },
              callback: function(value) {
                if (value >= 1000) {
                  return (value / 1000) + 'k';
                }
                return value;
              }
            },
            title: {
              display: true,
              text: 'Number of Students',
              font: { size: 11 }
            }
          },
          x: { 
            grid: { display: false }, 
            ticks: { font: { size: 11 } } 
          }
        }
      }
    });

    
    const ctx2 = document.getElementById("donutChart").getContext("2d");
    new Chart(ctx2, {
      type: "doughnut",
      data: {
        labels: [`Active (${DASHBOARD.active})`, `Graduated (${DASHBOARD.graduated})`, `On Leave (${DASHBOARD.leave})`, `Withdrawn (${DASHBOARD.withdrawn})`],
        datasets: [{
          data: [
            DASHBOARD.active,
            DASHBOARD.graduated,
            DASHBOARD.leave,
            DASHBOARD.leave,
          ],
          backgroundColor: ["#c5050c", "#228b22", "#f59e0b", "#cccccc"],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "70%",
        plugins: {
          legend: {
            position: "bottom",
            labels: { 
              boxWidth: 10, 
              padding: 8, 
              font: { size: 10 }, 
              usePointStyle: true, 
              pointStyle: "circle" 
            }
          }
        }
      }
    });
  }

document.addEventListener("DOMContentLoaded", function () {
  fetchStudents();
});