let departments = [];
let currentFilter = "all";
let searchTerm = "";
let currentPage = 1;
const itemsPerPage = 6;

async function fetchDepartments() {
  try {
    const res = await fetch("/medical/api/department/list/");

    if (!res.ok) {
      throw new Error(`HTTP error! Status: ${res.status}`);
    }

    const data = await res.json();

    departments = data.results || data.data || data.departments || data || [];

    render(); 

  } catch (err) {
    console.error("Error fetching departments:", err);
    const grid = document.getElementById("departmentGrid");
    grid.innerHTML = `
            <div class="col-12">
                <div class="department-empty-state">
                    <i class="fas fa-search"></i>
                    <h5>No departments found</h5>
                    <p>Try adjusting your search or filters</p>
                </div>
            </div>
        `;
  }
}


function isOpen(opening, closing) {
  if (!opening || !closing) return false;

  const now = new Date();
  const current = now.getHours() * 60 + now.getMinutes();

  const [oh, om] = opening.split(":").map(Number);
  const [ch, cm] = closing.split(":").map(Number);

  const openMin = oh * 60 + om;
  const closeMin = ch * 60 + cm;

  if (openMin === 0 && closeMin === 1439) return true;

  if (openMin <= closeMin) {
    return current >= openMin && current <= closeMin;
  }

  return current >= openMin || current <= closeMin;
}

function formatTime(time) {
  if (!time) return "-";

  const [h, m] = time.split(":").map(Number);
  const ampm = h >= 12 ? "PM" : "AM";
  const h12 = h % 12 || 12;

  return `${h12}:${String(m).padStart(2, "0")} ${ampm}`;
}

function getFilteredData() {
  return departments.filter((d) => {
    const keyword = searchTerm.toLowerCase();

    const matchSearch =
      (d.department_name || "").toLowerCase().includes(keyword) ||
      (d.department_code || "").toLowerCase().includes(keyword) ||
      (d.short_name || "").toLowerCase().includes(keyword) ||
      (d.department_type || "").toLowerCase().includes(keyword);
    const matchFilter =
      currentFilter === "all" ||
      (currentFilter === "emergency" && d.is_emergency) ||
      (currentFilter === "open" && isOpen(d.opening_time, d.closing_time)) ||
      (currentFilter === "closed" && !isOpen(d.opening_time, d.closing_time));
    return matchSearch && matchFilter;
  });
}

function render() {
  const filtered = getFilteredData();
  const totalItems = filtered.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage) || 1;

  if (currentPage > totalPages) currentPage = totalPages;

  const start = (currentPage - 1) * itemsPerPage;
  const end = Math.min(start + itemsPerPage, totalItems);
  const pageItems = filtered.slice(start, end);

  const total = departments.length;
  const openNow = departments.filter((d) =>
    isOpen(d.opening_time, d.closing_time),
  ).length;
  const emergency = departments.filter((d) => d.is_emergency).length;
  const active = departments.filter((d)=> d.is_active).length;

  document.getElementById("totalDepts").textContent = total;
  document.getElementById("openDepts").textContent = openNow;
  document.getElementById("emergencyDepts").textContent = emergency;
  document.getElementById("activeDepts").textContent = active;
  document.getElementById("resultCount").textContent = totalItems;

  const grid = document.getElementById("departmentGrid");
  grid.innerHTML = "";

  if (pageItems.length === 0) {
    grid.innerHTML = `
                <div class="col-12">
                    <div class="department-empty-state">
                        <i class="fas fa-search"></i>
                        <h5>No departments found</h5>
                        <p>Try adjusting your search or filters</p>
                    </div>
                </div>
            `;
  } else {
    pageItems.forEach((d) => {
      const open = isOpen(d.opening_time, d.closing_time);
      const is24hr = d.opening_time === "00:00" && d.closing_time === "23:59";

      const col = document.createElement("div");
      col.className = "col-12 col-md-6 col-lg-4";

      col.innerHTML = `
                    <div class="department-card">
                      <div class="department-card-actions">
                        <a href="/medical/department_edit/${d.uuid}" class="action-icon">
                          <i class="ti ti-edit"></i>
                        </a>
                      </div>
                        <!-- Card Header -->
                        <div class="department-card-header">
                            <div class="department-card-header-top">
                                <span class="department-card-code">${d.department_code || "-"}</span>
                                <span class="department-card-status ${open ? "open" : "closed"}">
                                    <span class="dot"></span>
                                    ${open ? "Open" : "Closed"}
                                </span>
                            </div>
                            <h4 class="department-card-name">${d.department_name || "Unknown Department"}</h4>
                            ${d.short_name
                                ? `<div class="department-card-short">${d.short_name}</div>`
                                : `<div class="department-card-short">${d.department_name.slice(0, 3)}</div>`
                            }
                        </div>
                        
                        <!-- Card Body -->
                        <div class="department-card-body">
                            <div class="department-card-header-top">
                              <span class="department-card-type ${d.is_emergency ? "emergency" : ""}">
                                  <span>${d.is_emergency ? `<i class="ti ti-urgent"></i> ` : ""}</span>
                                  <span>${d.department_type || "-"}</span>
                              </span>
                            
                              <span class="department-active-status ${d.is_active ? "active" : "inactive"}">
                                  <span class="dot"></span>
                                      <span class="status-tooltip">
                                          ${d.is_active ? "Active" : "Inactive"}
                                      </span>
                              </span>
                            </div>

                            <p class="department-card-desc">${d.description || "No description available"}</p>
                            <div class="department-card-info">
                                <div class="department-card-info-item">
                                    <i class="fas fa-location-dot"></i> ${d.location || "-"}
                                </div>
                                <div class="department-card-info-item">
                                    <i class="fas fa-phone"></i> ${d.phone || "-"}
                                </div>
                                <div class="department-card-info-item">
                                    <i class="fas fa-envelope"></i> ${d.email || "-"}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Card Footer -->
                        <div class="department-card-footer">
                            <span class="department-card-hours">
                                <i class="far fa-clock"></i>
                                ${is24hr ? "24/7" : formatTime(d.opening_time) + " - " + formatTime(d.closing_time)}
                            </span>
                            ${d.is_emergency ? '<span class="department-card-emergency-badge"><i class="fas fa-bolt"></i> Emergency</span>' : ""}
                        </div>
                    </div>
                `;

      grid.appendChild(col);
    });
  }

  renderPagination(totalPages, totalItems);
}

function renderPagination(totalPages, totalItems) {
  const numbers = document.getElementById("paginationNumbers");
  numbers.innerHTML = "";

  const prevBtn = document.getElementById("prevPage");
  const nextBtn = document.getElementById("nextPage");
  const info = document.getElementById("pageInfo");

  prevBtn.disabled = currentPage === 1;
  nextBtn.disabled = currentPage === totalPages;

  info.textContent = `Page ${currentPage} of ${totalPages} (${totalItems} items)`;

  let startPage = Math.max(1, currentPage - 2);
  let endPage = Math.min(totalPages, currentPage + 2);

  if (startPage > 1) {
    const btn = createPageBtn(1);
    numbers.appendChild(btn);
    if (startPage > 2) {
      const ellipsis = document.createElement("span");
      ellipsis.textContent = "…";
      ellipsis.style.cssText =
        "padding: 0.3rem 0.5rem; color: var(--gray-500);";
      numbers.appendChild(ellipsis);
    }
  }

  for (let i = startPage; i <= endPage; i++) {
    const btn = createPageBtn(i);
    if (i === currentPage) btn.classList.add("active");
    numbers.appendChild(btn);
  }

  if (endPage < totalPages) {
    if (endPage < totalPages - 1) {
      const ellipsis = document.createElement("span");
      ellipsis.textContent = "…";
      ellipsis.style.cssText =
        "padding: 0.3rem 0.5rem; color: var(--gray-500);";
      numbers.appendChild(ellipsis);
    }
    const btn = createPageBtn(totalPages);
    numbers.appendChild(btn);
  }
}

function createPageBtn(page) {
  const btn = document.createElement("button");
  btn.className = "department-pagination-btn";
  btn.textContent = page;
  btn.addEventListener("click", () => {
    currentPage = page;
    render();
  });
  return btn;
}


document.querySelectorAll(".department-filter-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document
      .querySelectorAll(".department-filter-btn")
      .forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    currentFilter = btn.dataset.filter;
    currentPage = 1;
    render();
  });
});

document.getElementById("searchInput").addEventListener("input", (e) => {
  searchTerm = e.target.value;
  currentPage = 1;
  render();
});

document.getElementById("prevPage").addEventListener("click", () => {
  if (currentPage > 1) {
    currentPage--;
    render();
  }
});

document.getElementById("nextPage").addEventListener("click", () => {
  const filtered = getFilteredData();
  const totalPages = Math.ceil(filtered.length / itemsPerPage) || 1;
  if (currentPage < totalPages) {
    currentPage++;
    render();
  }
});

document.addEventListener("DOMContentLoaded", () => {
  fetchDepartments();
});