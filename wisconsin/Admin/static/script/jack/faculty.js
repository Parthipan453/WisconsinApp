const FACULTY = [
  {
    id: "FAC-2024-001",
    name: "Dr. Sarah Johnson",
    email: "sjohnson@wisc.edu",
    rank: "Professor",
    phone: "+1(608)5550101",
    office: "Science Hall 301",
    status: "ACTIVE",
    initials: "SJ",
    color: "#c5050c",
  },
  {
    id: "FAC-2023-045",
    name: "Dr. Michael Chen",
    email: "mchen@wisc.edu",
    rank: "Associate Professor",
    phone: "+1 (608) 555-0102",
    office: "Engineering 204",
    status: "ACTIVE",
    initials: "MC",
    color: "#185fa5",
  },
  {
    id: "FAC-2024-012",
    name: "Prof. Emily Williams",
    email: "ewilliams@wisc.edu",
    rank: "Professor",
    phone: "+1 (608) 555-0103",
    office: "Arts Building 150",
    status: "ACTIVE",
    initials: "EW",
    color: "#228b22",
  },
  {
    id: "FAC-2022-078",
    name: "Dr. James Rodriguez",
    email: "jrodriguez@wisc.edu",
    rank: "Assistant Professor",
    phone: "+1 (608) 555-0104",
    office: "Business Hall 210",
    status: "LEAVE",
    initials: "JR",
    color: "#ba7517",
  },
  {
    id: "FAC-2024-023",
    name: "Prof. Lisa Thompson",
    email: "lthompson@wisc.edu",
    rank: "Lecturer",
    phone: "+1 (608) 555-0105",
    office: "Education 102",
    status: "ACTIVE",
    initials: "LT",
    color: "#534ab7",
  },
  {
    id: "FAC-2021-056",
    name: "Dr. Robert Kim",
    email: "rkim@wisc.edu",
    rank: "Professor",
    phone: "+1 (608) 555-0106",
    office: "Science Hall 401",
    status: "ACTIVE",
    initials: "RK",
    color: "#0f6e56",
  },
  {
    id: "FAC-2023-089",
    name: "Dr. Maria Garcia",
    email: "mgarcia@wisc.edu",
    rank: "Associate Professor",
    phone: "+1 (608) 555-0107",
    office: "Medical Center 305",
    status: "ACTIVE",
    initials: "MG",
    color: "#7c3aed",
  },
  {
    id: "FAC-2020-034",
    name: "Prof. David O'Brien",
    email: "dobrien@wisc.edu",
    rank: "Professor",
    phone: "+1 (608) 555-0108",
    office: "Law School 120",
    status: "RETIRED",
    initials: "DO",
    color: "#374151",
  },
  {
    id: "FAC-2024-056",
    name: "Dr. Amanda Foster",
    email: "afoster@wisc.edu",
    rank: "Assistant Professor",
    phone: "+1 (608) 555-0109",
    office: "Engineering 308",
    status: "ACTIVE",
    initials: "AF",
    color: "#b45309",
  },
  {
    id: "FAC-2022-091",
    name: "Prof. Thomas Clark",
    email: "tclark@wisc.edu",
    rank: "Adjunct",
    phone: "+1 (608) 555-0110",
    office: "Business Hall 305",
    status: "ACTIVE",
    initials: "TC",
    color: "#dc2626",
  },
];

function getStatusDistribution() {
  const counts = { ACTIVE: 0, LEAVE: 0, RETIRED: 0 };
  FACULTY.forEach((f) => {
    if (counts[f.status] !== undefined) {
      counts[f.status]++;
    }
  });
  return counts;
}

const statusData = getStatusDistribution();
const statusLabels = Object.keys(statusData);
const statusValues = Object.values(statusData);

let filtered = [...FACULTY];
let currentPage = 1;
let currentPageGrid = 1;
const PER_PAGE = 6;

function statusClass(s) {
  return (
    { ACTIVE: "sp-active", LEAVE: "sp-leave", RETIRED: "sp-withdrawn" }[s] || ""
  );
}

function rankClass(r) {
  const classes = {
    Professor: "rank-professor",
    "Associate Professor": "rank-associate",
    "Assistant Professor": "rank-assistant",
    Lecturer: "rank-lecturer",
    Adjunct: "rank-adjunct",
  };
  return classes[r] || "";
}

function filterTable() {
  const q = (document.getElementById("tableSearch").value || "").toLowerCase();
  const status = document.getElementById("filterStatus").value;
  const rank = document.getElementById("filterRank").value;

  filtered = FACULTY.filter((f) => {
    const matchQ =
      !q ||
      f.name.toLowerCase().includes(q) ||
      f.id.toLowerCase().includes(q) ||
      f.email.toLowerCase().includes(q) ||
      f.office.toLowerCase().includes(q);
    const matchS = !status || f.status === status;
    const matchR = !rank || f.rank === rank;
    return matchQ && matchS && matchR;
  });

  currentPage = 1;
  currentPageGrid = 1;
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
  info.textContent = `Showing ${Math.min(start + 1, total)}–${Math.min(start + PER_PAGE, total)} of ${total} faculty`;

  tbody.innerHTML = page
    .map(
      (f) => `
        <tr data-id="${f.id}">
          <td>
            <div class="faculty-cell">
              <div class="f-avatar" style="background:${f.color}">${f.initials}</div>
              <div>
                <div class="f-name">${f.name}</div>
                <div class="f-id">${f.id}</div>
              </div>
            </div>
          </td>
          <td class="col-email">${f.email}</td>
          <td class="col-rank"><span class="rank-chip ${rankClass(f.rank)}">${f.rank}</span></td>
          <td class="col-phone">${f.phone}</td>
          <td class="col-office">${f.office}</td>
          <td><span class="status-pill ${statusClass(f.status)}">${f.status}</span></td>
          <td>
            <div class="row-actions">
              <button class="act-btn act-view" onclick="viewFaculty('${f.id}')"><i class="ti ti-eye"></i></button>
              <button class="act-btn act-edit" onclick="editFaculty('${f.id}')"><i class="ti ti-edit"></i></button>
              <button class="act-btn act-del" onclick="deleteFaculty('${f.id}')"><i class="ti ti-trash"></i></button>
            </div>
          </td>
        </tr>
      `,
    )
    .join("");

  renderPagination(
    total,
    "paginationBtns",
    "paginationInfo",
    currentPage,
    "goPage",
  );
}

function renderGrid() {
  const grid = document.getElementById("cardGrid");
  const emptyGrid = document.getElementById("emptyStateGrid");
  const pagBar = document.getElementById("paginationBarGrid");
  const info = document.getElementById("paginationInfoGrid");

  if (!filtered.length) {
    grid.innerHTML = "";
    emptyGrid.style.display = "block";
    pagBar.style.display = "none";
    return;
  }

  emptyGrid.style.display = "none";
  pagBar.style.display = "flex";

  const start = (currentPageGrid - 1) * PER_PAGE;
  const page = filtered.slice(start, start + PER_PAGE);
  const total = filtered.length;

  info.textContent = `Showing ${Math.min(start + 1, total)}–${Math.min(start + PER_PAGE, total)} of ${total} faculty`;

  grid.innerHTML = page
    .map(
      (f) => `
        <div class="faculty-card">
          <div class="fc-head">
              <div class="fc-avatar" style="background:${f.color}">
                <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(f.name)}&size=80&background=${f.color.replace("#", "")}&color=fff&bold=true" alt="${f.name}">
              </div>
            <div class="fc-info">
              <div class="fc-name">${f.name}</div>
              <div class="fc-id">${f.id}</div>
              <span class="rank-chip ${rankClass(f.rank)}">${f.rank}</span>
            </div>
          </div>
          <hr class="fc-divider">
          <div class="fc-row">
            <span class="fc-lbl"><i class="ti ti-mail em-color"></i> Email</span>
            <span class="fc-val">${f.email}</span>
          </div>
          <div class="fc-row">
            <span class="fc-lbl"><i class="ti ti-phone ph-color"></i> Phone</span>
            <span class="fc-val">${f.phone}</span>
          </div>
          <div class="fc-row">
            <span class="fc-lbl"><i class="ti ti-building of-color"></i> Office</span>
            <span class="fc-val">${f.office}</span>
          </div>
          <div class="fc-footer">
            <span class="status-pill ${statusClass(f.status)}">${f.status}</span>
            <div class="fc-actions">
              <button class="fc-act view" onclick="viewFaculty('${f.id}')"><i class="ti ti-eye"></i></button>
              <button class="fc-act edit" onclick="editFaculty('${f.id}')"><i class="ti ti-edit"></i></button>
              <button class="fc-act del" onclick="deleteFaculty('${f.id}')"><i class="ti ti-trash"></i></button>
            </div>
          </div>
        </div>
      `,
    )
    .join("");

  renderPagination(
    total,
    "paginationBtnsGrid",
    "paginationInfoGrid",
    currentPageGrid,
    "goPageGrid",
  );
}

function renderPagination(total, btnsId, infoId, currentPageNum, goPageFn) {
  const pages = Math.ceil(total / PER_PAGE);
  const btns = document.getElementById(btnsId);
  if (!btns) return;

  let html = `<button class="pag-btn" ${currentPageNum === 1 ? "disabled" : ""} onclick="${goPageFn}(${currentPageNum - 1})"><i class="ti ti-chevron-left"></i></button>`;
  for (let p = 1; p <= pages; p++) {
    html += `<button class="pag-btn ${p === currentPageNum ? "active" : ""}" onclick="${goPageFn}(${p})">${p}</button>`;
  }
  html += `<button class="pag-btn" ${currentPageNum === pages ? "disabled" : ""} onclick="${goPageFn}(${currentPageNum + 1})"><i class="ti ti-chevron-right"></i></button>`;
  btns.innerHTML = html;
}

function goPage(p) {
  const pages = Math.ceil(filtered.length / PER_PAGE);
  if (p < 1 || p > pages) return;
  currentPage = p;
  renderTable();
  document
    .querySelector(".content-wrapper")
    .scrollTo({ top: 0, behavior: "smooth" });
}

function goPageGrid(p) {
  const pages = Math.ceil(filtered.length / PER_PAGE);
  if (p < 1 || p > pages) return;
  currentPageGrid = p;
  renderGrid();
  document
    .querySelector(".content-wrapper")
    .scrollTo({ top: 0, behavior: "smooth" });
}

function switchView(v) {
  document.getElementById("gridView").style.display =
    v === "grid" ? "block" : "none";
  document.getElementById("tableView").style.display =
    v === "table" ? "block" : "none";
  document.getElementById("btnGrid").classList.toggle("active", v === "grid");
  document.getElementById("btnTable").classList.toggle("active", v === "table");

  currentPage = 1;
  currentPageGrid = 1;
  renderView();
}

function renderView() {
  const gridView = document.getElementById("gridView");
  if (gridView.style.display !== "none") {
    renderGrid();
  } else {
    renderTable();
  }
}

function viewFaculty(id) {
  alert(`View faculty: ${id}`);
}
function editFaculty(id) {
  alert(`Edit faculty: ${id}`);
}
function deleteFaculty(id) {
  if (confirm(`Delete ${id}?`)) alert(`Deleted: ${id}`);
}

function initChart() {
  const ctx = document.getElementById("pieChart").getContext("2d");

  const colors = {
    ACTIVE: "#228b22",
    LEAVE: "#f59e0b",
    RETIRED: "#7c3aed",
  };

  const pieColors = statusLabels.map((label) => colors[label] || "#888");
  const total = statusValues.reduce((a, b) => a + b, 0);

  new Chart(ctx, {
    type: "pie",
    data: {
      labels: statusLabels.map((label, i) => `${label} (${statusValues[i]})`),
      datasets: [
        {
          data: statusValues,
          backgroundColor: pieColors,
          borderWidth: 2,
          borderColor: "#fff",
          hoverOffset: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "right",
          labels: {
            boxWidth: 12,
            padding: 10,
            font: { size: 11 },
            usePointStyle: true,
            pointStyle: "circle",
          },
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              const value = context.parsed;
              const percentage = ((value / total) * 100).toFixed(1);
              return `${context.label}: ${value} (${percentage}%)`;
            },
          },
        },
      },
    },
  });
}

document.addEventListener("DOMContentLoaded", function () {
  renderGrid();
  initChart();
});