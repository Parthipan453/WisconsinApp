let TEAMS = [];
let filtered = [];
let currentPage = 1;
const PER_PAGE = 12;
const slimSelects = {}

async function fetchTeams() {
  try {
    let res = await fetch("/dashboard/api/teams/list/");
    let data = await res.json();

    TEAMS = data.teams.map((team) => ({
      ...team,
    }));
    
    filtered = [...TEAMS];
    
    populateFilters();
    updateStats();
    renderTeams();
    
  } catch (err) {
    console.log(err);
    const grid = document.getElementById("teamsGrid");
    const empty = document.getElementById("emptyState");
    grid.style.display = "none";
    empty.style.display = "block";
  }
}

function populateFilters() {
  const sportSelect = document.getElementById("filterSport");
  if (!sportSelect) return;
  
  sportSelect.innerHTML = '<option value="">All Sports</option>';
  
  const sports = [...new Set(TEAMS.map(t => t.sport_type).filter(Boolean))];

  slimSelects.filterSport.setData([
      {
          text: 'All Sports',
          value: '',
          selected: true
      },
      ...sports.map(sport => ({
          text: sport,
          value: sport
      }))
  ]);
}

function updateStats() {
  const total = TEAMS.length;
  const active = TEAMS.filter((t) => t.status).length;
  const sports = [...new Set(TEAMS.map((t) => t.sport_type))].filter(Boolean).length;
  const division = [...new Set(TEAMS.map((t) => t.division))].filter(Boolean).length;
  const clubs = [...new Set(TEAMS.map((t) => t.club))].filter(Boolean).length;

  document.getElementById("totalTeams").textContent = total;
  document.getElementById("activeTeams").textContent = active;
  document.getElementById("sportTypes").textContent = sports;
  document.getElementById("divisions").textContent = division;
  document.getElementById("seasons").textContent = clubs;
}

function getInitials(name) {
  if (!name) return "TE";
  return name
    .split(" ")
    .map((word) => word[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

function getAvatarColor(name) {
  const colors = [
    "#ef4444",
    "#f97316",
    "#f59e0b",
    "#eab308",
    "#84cc16",
    "#22c55e",
    "#10b981",
    "#14b8a6",
    "#06b6d4",
    "#0ea5e9",
    "#3b82f6",
    "#6366f1",
    "#8b5cf6",
    "#a855f7",
    "#d946ef",
    "#ec4899",
    "#f43f5e",
    "#fb7185",
    "#f472b6",
    "#e879f9",
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

function getBannerColor(name) {
  const colors = [
    "#c5050c",
    "#185fa5",
    "#228b22",
    "#7c3aed",
    "#ec4899",
    "#f59e0b",
    "#14b8a6",
    "#dc2626",
    "#8b5cf6",
    "#06b6d4",
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

function filterTeams() {
  const q = document.getElementById("tableSearch").value.toLowerCase();
  const sport = document.getElementById("filterSport").value;
  const status = document.getElementById("filterStatus").value;

  filtered = TEAMS.filter((t) => {
    const matchQ =
      !q ||
      t.team_name.toLowerCase().includes(q) ||
      t.team_code.toLowerCase().includes(q);
    const matchSport = !sport || t.sport_type === sport;
    const matchStatus =
      status === "" || (status === "true" ? t.status : !t.status);
    return matchQ && matchSport && matchStatus;
  });

  currentPage = 1;
  renderTeams();
}

function renderTeams() {
  const grid = document.getElementById("teamsGrid");
  const empty = document.getElementById("emptyState");
  const pagBar = document.getElementById("paginationBar");
  const info = document.getElementById("paginationInfo");
  const count = document.getElementById("resultCount");

  if (!filtered.length) {
    grid.innerHTML = "";
    grid.style.display = "none";
    empty.style.display = "block";
    pagBar.style.display = "none";
    count.textContent = "0 teams";
    return;
  } else {
    grid.style.display = "grid";
  }

  empty.style.display = "none";
  pagBar.style.display = "flex";

  const start = (currentPage - 1) * PER_PAGE;
  const page = filtered.slice(start, start + PER_PAGE);
  const total = filtered.length;

  count.textContent = `${total} team${total !== 1 ? "s" : ""}`;
  info.textContent = `Showing ${Math.min(start + 1, total)}–${Math.min(start + PER_PAGE, total)} of ${total}`;

  grid.innerHTML = page
    .map((t, index) => {
      const avatarColor = getAvatarColor(t.team_name);
      const bannerColor = getBannerColor(t.team_name);
      const initials = getInitials(t.team_name);
      const statusClass = t.status ? "active" : "inactive";

      return `
        <div class="tm-team-card-wrapper">
          <div class="tm-team-card" data-aos="fade-up" data-aos-delay="${index * 50}" style="background: linear-gradient(135deg, ${bannerColor} 0%, ${bannerColor}dd 100%);">
            
            ${
              t.icon 
                ? `<img src="${t.icon}" class="tm-card-img" />` 
                : `<div class="tm-card-initials-bg">${initials}</div>`
            }
            
            <div class="tm-card-hover-icons">
              <a href="/dashboard/team_view/${t.team_uuid}" class="tm-card-hover-icon tm-card-hover-icon-view">
                <i class="fas fa-eye"></i>
              </a>
              <a href="/dashboard/team_edit/${t.team_uuid}" class="tm-card-hover-icon tm-card-hover-icon-edit">
                <i class="fas fa-edit"></i>
              </a>
              <!-- <button class="tm-card-hover-icon tm-card-hover-icon-delete team-delete-modal" data-team-id="${t.id}" data-team-name="${t.team_name}">
                <i class="fas fa-trash"></i>
              </button> -->
            </div>
          </div>
          
          <a href="/dashboard/team_view/${t.team_uuid}" class="tm-card-team-name">${t.team_name}</a>
          <div class="tm-card-team-code">${t.team_code}</div>
          <span class="tm-card-status ${statusClass}">
            <span class="tm-status-dot"></span>
            ${t.status ? "Active": "Inactive"}
          </span>
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

  let html = `<button class="tm-pag-btn" ${currentPage === 1 ? "disabled" : ""} onclick="goPage(${currentPage - 1})"><i class="fas fa-chevron-left"></i></button>`;
  for (let p = 1; p <= pages; p++) {
    html += `<button class="tm-pag-btn ${p === currentPage ? "active" : ""}" onclick="goPage(${p})">${p < 10 ? "0" : ""}${p}</button>`;
  }
  html += `<button class="tm-pag-btn" ${currentPage === pages ? "disabled" : ""} onclick="goPage(${currentPage + 1})"><i class="fas fa-chevron-right"></i></button>`;
  btns.innerHTML = html;
}

function goPage(p) {
  const pages = Math.ceil(filtered.length / PER_PAGE);
  if (p < 1 || p > pages) return;
  currentPage = p;
  renderTeams();
  document
    .querySelector(".tm-dashboard")
    .scrollTo({ top: 0, behavior: "smooth" });
}

function openDeleteModal(teamId, teamName) {
    console.log('Opening delete modal for:', teamId, teamName);
    
    teamToDeleteId = teamId;
    teamToDeleteName = teamName;
    
    const modal = document.getElementById("ub-delete-modal");
    if (!modal) {
        console.error('Modal element not found!');
        alert('Modal not found. Please check the HTML.');
        return;
    }
    
    const titleEl = document.getElementById("ub-modal-title");
    const bodyEl = document.getElementById("ub-modal-body");
    const usernameEl = document.getElementById("ub-status-modal-username");
    
    if (titleEl) titleEl.textContent = '🗑️ Delete Team';
    if (bodyEl) bodyEl.textContent = `Are you sure you want to delete "${teamName}"? This action cannot be undone. All associated data will be permanently removed.`;
    if (usernameEl) usernameEl.textContent = teamName;
    
    modal.removeAttribute('hidden');
    modal.style.display = 'flex';
    modal.style.visibility = 'visible';
    modal.style.opacity = '1';
    document.body.style.overflow = 'hidden';
    
}

function closeDeleteModal() {
    console.log('Closing delete modal');
    
    const modal = document.getElementById("ub-delete-modal");
    if (!modal) return;
    
    modal.setAttribute('hidden', 'hidden');
    modal.style.display = 'none';
    modal.style.visibility = 'hidden';
    modal.style.opacity = '0';
    document.body.style.overflow = '';
    
    teamToDeleteId = null;
    teamToDeleteName = '';
}

function handleDeleteSport() {
    if (!teamToDeleteId) return;

    const confirmBtn = document.getElementById("ub-modal-confirm");

    confirmBtn.disabled = true;
    confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';

    window.location.href = `/dashboard/team_delete/${teamToDeleteId}`;
}

function setupModalListeners() {
    console.log('Setting up modal listeners');
    
    const cancelBtn = document.getElementById("ub-modal-cancel");
    if (cancelBtn) {
        cancelBtn.addEventListener("click", function(e) {
            e.preventDefault();
            e.stopPropagation();
            closeDeleteModal();
        });
    } else {
        console.warn('Cancel button not found');
    }
    
    const confirmBtn = document.getElementById("ub-modal-confirm");
    if (confirmBtn) {
        confirmBtn.addEventListener("click", function(e) {
            e.preventDefault();
            e.stopPropagation();
            handleDeleteSport();
        });
    } else {
        console.warn('Confirm button not found');
    }
    
    const modal = document.getElementById("ub-delete-modal");
    if (modal) {
        modal.addEventListener("click", function(e) {
            if (e.target === this) {
                closeDeleteModal();
            }
        });
    } else {
        console.warn('Modal not found');
    }
    
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const modal = document.getElementById("ub-delete-modal");
            if (modal && !modal.hidden && modal.style.display !== 'none') {
                closeDeleteModal();
            }
        }
    });
}

function setupDeleteListeners() {
    
    document.addEventListener('click', function(e) {
        const deleteBtn = e.target.closest('.team-delete-modal');
        if (deleteBtn) {
            e.preventDefault();
            e.stopPropagation();
            
            const teamId = deleteBtn.getAttribute('data-team-id');
            const teamName = deleteBtn.getAttribute('data-team-name') || 
                             deleteBtn.closest('.tm-team-card')?.querySelector('.tm-card-team-name')?.textContent || 
                             'Team';
            
            console.log('Delete button clicked:', teamId, teamName);
            
            if (teamId) {
                openDeleteModal(parseInt(teamId), teamName);
            } else {
                console.error('Team ID not found on delete button');
            }
        }
    });
}

document.addEventListener("DOMContentLoaded", function () {
  AOS.init({ duration: 600, once: true, easing: "ease-out-cubic" });
  fetchTeams();

  setupDeleteListeners();
  setupModalListeners();

  document.querySelectorAll('.tm-select-glass').forEach(select => {
        slimSelects[select.id] = new SlimSelect({
            select: select,
            settings: {
                placeholderText: select.options[0].text,
                showSearch: false
            }
        });
  });
});