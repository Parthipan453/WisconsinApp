let ATHLETES = [];
let filtered = [];
let currentPage = 1;
const PER_PAGE = 6;
let currentFilter = "all";
const slimSelects = {}

const CLASS_YEAR_MAP = {
  FRESHMAN: "Freshman",
  SOPHOMORE: "Sophomore",
  JUNIOR: "Junior",
  SENIOR: "Senior",
  GRADUATE: "Graduate",
  FACULTY: "Faculty",
  STAFF: "Staff",
};

async function fetchAthletes() {
  try {
    const res = await fetch("/dashboard/api/athletes/list/");
    const data = await res.json();

    ATHLETES = data.athletes.map((athlete) => ({
      athlete_id: athlete.id,
      student: {
        username: athlete.student.username,
        first_name: athlete.student.full_name.split(" ")[0] || "Unknown",
        last_name: athlete.student.full_name.split(" ").slice(1).join(" ") || "",
        full_name: athlete.student.full_name,
      },
      athlete_uuid: athlete.athlete_uuid,
      profile_photo: athlete.profile_photo,
      team: athlete.team
        ? {
            team_name: athlete.team.name,
            sport_type: athlete.team.sport_type || "Team Sport",
          }
        : null,
      individual_sports: athlete.individual_sports || [],
      jersey_number: athlete.jersey_number,
      position: athlete.position,
      height: athlete.height,
      weight: athlete.weight,
      class_year: athlete.class_year,
      class_year_display: athlete.class_year_display || CLASS_YEAR_MAP[athlete.class_year] || athlete.class_year,
      eligibility_status: athlete.eligibility_status,
      eligibility_status_display: athlete.eligibility_status_display,
      scholarship_status: athlete.scholarship_status,
      is_active: athlete.is_active,
      created_at: athlete.created_at || "2024-01-01",
    }));

    filtered = [...ATHLETES];
    populateFilters();
    updateStats();
    renderAthletes();
  } catch (err) {
    console.error("Error fetching athletes:", err);
    showError();
  }
}

function populateFilters() {
  const classFilter = document.getElementById("filterClass");
  if (classFilter) {
    classFilter.innerHTML = '<option value="">All Classes</option>';
    const classYears = [...new Set(ATHLETES.map(a => a.class_year).filter(Boolean))];
    
    if (slimSelects.filterClass) {
        slimSelects.filterClass.setData([
            {
                text: "All Classes",
                value: "",
                selected: true
            },
            ...classYears.map(year => ({
                text: CLASS_YEAR_MAP[year] || year,
                value: year
            }))
        ]);
    }

  }
}

function showError() {
  const grid = document.getElementById("athletesGrid");
  const empty = document.getElementById("emptyState");

  grid.style.display = "none"
  empty.style.display = "block"
}

let previousStats = {
  total: 0,
  active: 0,
  teams: 0,
  classYears: 0,
};

function getTrend(current, previous) {
  if (previous === 0) {
    return {
      percent: current > 0 ? 100 : 0,
      direction: "up",
    };
  }

  const change = ((current - previous) / previous) * 100;

  return {
    percent: Math.abs(Math.round(change)),
    direction: change >= 0 ? "up" : "down",
  };
}

function updateChange(elementId, trend) {
  const el = document.getElementById(elementId);

  el.classList.remove("up", "down");

  if (trend.direction === "up") {
    el.classList.add("up");
    el.innerHTML = `<i class="fas fa-arrow-up"></i> ${trend.percent}%`;
  } else {
    el.classList.add("down");
    el.innerHTML = `<i class="fas fa-arrow-down"></i> ${trend.percent}%`;
  }
}

function updateStats() {
  const total = ATHLETES.length;
  const active = ATHLETES.filter(a => a.is_active).length;
  const teams = [...new Set(
    ATHLETES.filter(a => a.team).map(a => a.team.team_name)
  )].length;
  const classYears = [...new Set(
    ATHLETES.map(a => a.class_year)
  )].length;

  document.getElementById("totalAthletes").textContent = total;
  document.getElementById("activeAthletes").textContent = active;
  document.getElementById("teamsCount").textContent = teams;
  document.getElementById("classYears").textContent = classYears;

  updateChange(
    "totalAthletesChange",
    getTrend(total, previousStats.total)
  );

  updateChange(
    "activeAthletesChange",
    getTrend(active, previousStats.active)
  );

  updateChange(
    "teamsCountChange",
    getTrend(teams, previousStats.teams)
  );

  updateChange(
    "classYearsChange",
    getTrend(classYears, previousStats.classYears)
  );

  previousStats = {
    total,
    active,
    teams,
    classYears,
  };
}

function getInitials(firstName, lastName) {
  return (firstName?.charAt(0) || "") + (lastName?.charAt(0) || "");
}

function getAvatarColor(name) {
  const colors = [
    "#ef4444", "#f97316", "#f59e0b", "#eab308", "#84cc16",
    "#22c55e", "#10b981", "#14b8a6", "#06b6d4", "#0ea5e9",
    "#3b82f6", "#6366f1", "#8b5cf6", "#a855f7", "#d946ef",
    "#ec4899", "#f43f5e", "#fb7185", "#f472b6", "#e879f9",
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

function getBannerColor(name) {
  const colors = [
    "#c5050c", "#185fa5", "#228b22", "#7c3aed", "#ec4899",
    "#f59e0b", "#14b8a6", "#dc2626", "#8b5cf6", "#06b6d4",
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

function getClassTagClass(year) {
  const map = {
    FRESHMAN: "freshman",
    SOPHOMORE: "sophomore",
    JUNIOR: "junior",
    SENIOR: "senior",
    GRADUATE: "graduate",
    STAFF: "staff",
    FACULTY: "faculty",
  };
  return map[year] || "freshman";
}

function getEligibilityTagClass(status) {
  const map = {
    ELIGIBLE: "eligible",
    INELIGIBLE: "ineligible",
    PROBATION: "probation",
    REDSHIRT: "redshirt",
    MEDICAL: "medical",
  };
  return map[status] || "eligible";
}

function filterAthletes() {
  const q = document.getElementById("tableSearch").value.toLowerCase();
  const classYear = document.getElementById("filterClass").value;
  const status = document.getElementById("filterStatus").value;

  filtered = ATHLETES.filter((a) => {
    const fullName = a.student.full_name?.toLowerCase() || "";
    const matchQ =
      !q ||
      fullName.includes(q) ||
      a.student.username.toLowerCase().includes(q);
    const matchClass = !classYear || a.class_year === classYear;
    const matchStatus = status === "" || (status === "true" ? a.is_active : !a.is_active);
    return matchQ && matchClass && matchStatus;
  });

  currentPage = 1;
  renderAthletes();
}

function renderAthletes() {
  const grid = document.getElementById("athletesGrid");
  const empty = document.getElementById("emptyState");
  const pagBar = document.getElementById("paginationBar");
  const info = document.getElementById("paginationInfo");
  const count = document.getElementById("resultCount");

  if (!filtered.length) {
    grid.innerHTML = "";
    grid.style.display = "none";
    empty.style.display = "block";
    pagBar.style.display = "none";
    count.textContent = "0 athletes";
    return;
  }
  else{
    grid.style.display = "grid"
  }

  empty.style.display = "none";
  pagBar.style.display = "flex";

  const start = (currentPage - 1) * PER_PAGE;
  const page = filtered.slice(start, start + PER_PAGE);
  const total = filtered.length;

  count.textContent = `${total} athlete${total !== 1 ? "s" : ""}`;
  info.textContent = `Showing ${Math.min(start + 1, total)}–${Math.min(
    start + PER_PAGE,
    total
  )} of ${total}`;

  grid.innerHTML = page
    .map((a, index) => {
      const fullName = a.student.full_name || "Unknown Athlete";
      const initials = getInitials(
        a.student.first_name,
        a.student.last_name
      ) || "NA";
      const avatarColor = getAvatarColor(a.student.username);
      const bannerColor = getBannerColor(a.student.username);
      const classTag = getClassTagClass(a.class_year);
      const eligTag = getEligibilityTagClass(a.eligibility_status);
      const statusClass = a.is_active ? "active" : "inactive";

      const teamName = a.team
        ? a.team.team_name
        : a.individual_sports && a.individual_sports.length > 0
        ? "Individual Athlete"
        : "Not Assigned";

      const scholarshipClass = a.scholarship_status ? "yes" : "no";
      const scholarshipLabel = a.scholarship_status ? "Yes" : "No";

      const individualSportsList = a.individual_sports || [];
      const hasIndividualSports = individualSportsList.length > 0;

      const classDisplay = CLASS_YEAR_MAP[a.class_year] || a.class_year;

      return `
        <div class="al-athlete-card" data-aos="fade-up" data-aos-delay="${index * 100}">
          <!-- Card Cover -->
          <div class="al-card-cover" style="background: linear-gradient(135deg, ${bannerColor} 0%, ${bannerColor}dd 100%);">
            <div class="al-cover-pattern">
              <i class="fa-solid fa-medal"></i>
            </div>
            <div class="al-cover-overlay"></div>
            
            <!-- Avatar on Cover -->
            <div class="al-card-avatar-wrapper">
              <div class="al-card-avatar" style="background: ${avatarColor}">
                ${a.profile_photo ? 
                `<img src="${a.profile_photo}" />`:
                `${initials}`
                }
                <span class="al-status-dot ${statusClass}"></span>
              </div>
              <div>
                <div class="al-card-name">${fullName}</div>
                <div class="al-card-username">@${a.student.username}</div>
              </div>
            </div>
          </div>

          <!-- Card Body -->
          <div class="al-card-body">
            <div class="al-card-tags">
              <span class="al-tag al-tag-team">
                <i class="fas fa-users"></i> ${teamName}
              </span>
              ${a.team ? `
                <span class="al-tag al-tag-sport">
                  <i class="fas fa-trophy"></i> ${a.team.sport_type || "Team Sport"}
                </span>
              ` : ''}

              <span class="al-tag al-tag-class-${classTag}">
                <i class="fas fa-graduation-cap"></i> ${classDisplay}
              </span>
              <span class="al-tag al-tag-eligibility-${eligTag}">
                <i class="fas fa-shield-alt"></i> ${a.eligibility_status_display || a.eligibility_status}
              </span>
            </div>

            <!-- Stats -->
            <div class="al-card-stats">
              <div class="al-card-stat">
                <span class="al-stat-number">${a.jersey_number || "N/A"}</span>
                <span class="al-stat-label">Jersey</span>
              </div>
              <div class="al-card-stat">
                <span class="al-stat-number">${a.position || "N/A"}</span>
                <span class="al-stat-label">Position</span>
              </div>
              <div class="al-card-stat">
                <span class="al-stat-number">${a.height ? `${a.height}"` : "N/A"}</span>
                <span class="al-stat-label">Height</span>
              </div>
            </div>

            <!-- Bottom Row -->
            <div class="al-card-bottom-row">
              <span class="al-scholarship-badge ${scholarshipClass}">
                <i class="fas fa-${a.scholarship_status ? "check-circle" : "times-circle"}"></i>
                ${scholarshipLabel} Scholarship
              </span>
            </div>
          </div>

          <!-- Card Footer -->
          <div class="al-card-footer">
            <a href="/dashboard/athlete_view/${a.athlete_uuid}" class="al-action al-action-view">
              <i class="fas fa-eye"></i>
            </a>
            <a href="/dashboard/athlete_edit/${a.athlete_uuid}" class="al-action al-action-edit">
              <i class="fas fa-edit"></i>
            </a>
          </div>
        </div>
      `;
    })
    .join("");

  renderPagination(total);
}

function renderPagination(total) {
  const pages = Math.ceil(total / PER_PAGE);
  const btns = document.getElementById("paginationBtns");
  if (!btns) return;

  let html = `<button class="al-pag-btn" ${currentPage === 1 ? "disabled" : ""} onclick="goPage(${currentPage - 1})"><i class="fas fa-chevron-left"></i></button>`;
  for (let p = 1; p <= pages; p++) {
    html += `<button class="al-pag-btn ${p === currentPage ? "active" : ""}" onclick="goPage(${p})">${p < 10 ? "0" : ""}${p}</button>`;
  }
  html += `<button class="al-pag-btn" ${currentPage === pages ? "disabled" : ""} onclick="goPage(${currentPage + 1})"><i class="fas fa-chevron-right"></i></button>`;
  btns.innerHTML = html;
}

function goPage(p) {
  const pages = Math.ceil(filtered.length / PER_PAGE);
  if (p < 1 || p > pages) return;
  currentPage = p;
  renderAthletes();
  document
    .querySelector(".al-dashboard")
    .scrollTo({ top: 0, behavior: "smooth" });
}

document.addEventListener("DOMContentLoaded", function () {
  AOS.init({ duration: 600, once: true, easing: "ease-out-cubic" });
  fetchAthletes();

    document.querySelectorAll('.al-filter-chip').forEach(select => {
        slimSelects[select.id] = new SlimSelect({
            select: select,
            settings: {
                placeholderText: select.options[0].text,
                showSearch: false
            }
        });
  });
});