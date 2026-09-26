let SPORTS = [];
let filtered = [];
let currentPage = 1;
const PER_PAGE = 6;

let sportToDeleteId = null;
let sportToDeleteName = '';

async function fetchSports() {
  try {
    const res = await fetch('/dashboard/api/sports/list/');
    
    const data = await res.json();
    
    SPORTS = data.sports.map(sport => ({
      ...sport,
      min_players: sport.min_players !== null ? parseInt(sport.min_players) : null,
      max_players: sport.max_players !== null ? parseInt(sport.max_players) : null,
      thumbnail: sport.thumbnail || null,
      icon: sport.icon || null
    }));
    
    filtered = [...SPORTS];
    currentPage = 1;
    renderSports();
    updateMetrics();
    updateCarousel();
    
    console.log('Sports loaded:', SPORTS);
  } catch (err) {
    console.error('Error fetching sports:', err);
    if (SPORTS.length === 0) {
      showError();
    }
  }
}

function showError() {
  const grid = document.getElementById('sportsGrid');
  const empty = document.getElementById('emptyState');
  const pagBar = document.getElementById('paginationBar');
  
  if (empty) empty.style.display = 'none';
  if (pagBar) pagBar.style.display = 'none';
  
  grid.innerHTML = `
    <div class="col-12">
      <div class="sp-error-glass text-center py-5">
        <i class="fas fa-exclamation-triangle" style="font-size: 48px; color: var(--danger);"></i>
        <h4 class="mt-3" style="color: var(--text-dark);">Failed to load sports</h4>
        <p class="text-muted">Please refresh the page or try again later.</p>
      </div>
    </div>
  `;
}

function updateCarousel() {
  const carouselInner = document.querySelector('.sp-banner .carousel-inner');
  if (!carouselInner) return;
  
  const sportsWithThumbnails = SPORTS.filter(s => s.thumbnail);
  
  if (sportsWithThumbnails.length === 0) {
    const defaultImages = [
      { src: '/static/image/close-up-athlete-playing-tennis.jpg', title: 'Sports Management', desc: 'Manage all your sports in one place' },
      { src: '/static/image/neon-style-american-football-player.jpg', title: 'Sports Management', desc: 'Track and organize sports efficiently' },
      { src: '/static/image/sports-tools.jpg', title: 'Sports Management', desc: 'Comprehensive sports management system' }
    ];
    
    let items = '';
    defaultImages.forEach((img, index) => {
      const isActive = index === 0 ? 'active' : '';
      items += `
        <div class="carousel-item ${isActive}">
          <img src="${img.src}" class="d-block w-100" alt="${img.title}">
          <div class="carousel-caption d-none d-md-block">
            <h4>${img.title}</h4>
            <p>${img.desc}</p>
          </div>
        </div>
      `;
    });
    carouselInner.innerHTML = items;
    return;
  }
  
  let items = '';
  sportsWithThumbnails.forEach((sport, index) => {
    const isActive = index === 0 ? 'active' : '';
    const sportType = sport.sport_type || 'Sport';
    const teamType = sport.is_team_sport ? 'Team' : 'Individual';
    
    items += `
      <div class="carousel-item ${isActive}">
        <img src="${sport.thumbnail}" class="d-block w-100" alt="${sport.sport_name}">
        <div class="carousel-caption d-none d-md-block">
          <h4>${sport.sport_name}</h4>
          <p>${sportType} • ${teamType} Sport</p>
        </div>
      </div>
    `;
  });
  
  carouselInner.innerHTML = items;
  
  const carouselElement = document.getElementById('carouselExampleAutoplaying');
  if (carouselElement && typeof bootstrap !== 'undefined') {
    try {
      const existingInstance = bootstrap.Carousel.getInstance(carouselElement);
      if (existingInstance) {
        existingInstance.dispose();
      }
      new bootstrap.Carousel(carouselElement, {
        interval: 3000,
        ride: 'carousel',
        wrap: true
      });
    } catch(e) {
      console.log('Carousel reinit skipped');
    }
  }
}

function updateMetrics() {
  const total = SPORTS.length;
  const active = SPORTS.filter(s => s.is_active).length;
  const teamSports = SPORTS.filter(s => s.is_team_sport).length;
  const olympic = SPORTS.filter(s => s.is_olympic_sport).length;

  const metrics = [
    {
      number: total,
      label: "Total",
      title: "Sports",
      value: 100,
      color: "var(--primary)",
      icon: "fas fa-futbol",
      trend: "100%",
      trendClass: "up",
      trendIcon: "fas fa-arrow-up"
    },
    {
      number: active,
      label: "Active",
      title: "Active",
      value: total ? (active / total) * 100 : 0,
      color: "var(--success)",
      icon: "fas fa-check-circle",
      trend: Math.round(total ? (active / total) * 100 : 0) + "%",
      trendClass: "up",
      trendIcon: "fas fa-arrow-up"
    },
    {
      number: teamSports,
      label: "Teams",
      title: "Teams",
      value: total ? (teamSports / total) * 100 : 0,
      color: "var(--warning)",
      icon: "fas fa-users",
      trend: Math.round(total ? (teamSports / total) * 100 : 0) + "%",
      trendClass: "up",
      trendIcon: "fas fa-arrow-up"
    },
    {
      number: olympic,
      label: "Olympic",
      title: "Olympic",
      value: total ? (olympic / total) * 100 : 0,
      color: "var(--secondary)",
      icon: "fas fa-trophy",
      trend: Math.round(total ? (olympic / total) * 100 : 0) + "%",
      trendClass: "up",
      trendIcon: "fas fa-arrow-up"
    }
  ];

  const circumference = 326.72;

  document.querySelectorAll(".sp-ring-card").forEach((card, index) => {
    const data = metrics[index];
    if (!data) return;

    card.querySelector(".sp-ring-number").textContent = data.number;

    card.querySelector(".sp-ring-label").textContent = data.label;

    card.querySelector(".sp-ring-info span").textContent = data.title;

    card.querySelector(".sp-ring-info i").className = data.icon;

    const progressCircle = card.querySelectorAll("circle")[1];
    const offset = circumference - (circumference * data.value) / 100;

    progressCircle.setAttribute("stroke", data.color);
    progressCircle.setAttribute("stroke-dasharray", circumference);
    progressCircle.setAttribute("stroke-dashoffset", offset);

    const trend = card.querySelector(".sp-ring-trend");
    trend.className = `sp-ring-trend ${data.trendClass}`;
    trend.innerHTML = `<i class="${data.trendIcon}"></i> ${data.trend}`;
  });
}

function getTypeClass(type) {
  return type === 'INDOOR' ? 'indoor' : type === 'OUTDOOR' ? 'outdoor' : 'both';
}

function getGenderClass(gender) {
  const map = { 
    MALE: 'male', 
    FEMALE: 'female', 
    TRANSGENDER: 'trans', 
    NON_BINARY: 'nonbinary', 
    OTHER: 'other' 
  };
  return map[gender] || 'other';
}

function getGenderIcon(gender) {
  const map = {
    MALE: 'fa-male',
    FEMALE: 'fa-female',
    TRANSGENDER: 'fa-user',
    NON_BINARY: 'fa-user',
    OTHER: 'fa-user'
  };
  return map[gender] || 'fa-user';
}

function getTypeIcon(type) {
  const map = {
    INDOOR: 'fa-building',
    OUTDOOR: 'fa-tree',
    BOTH: 'fa-arrows-alt-h'
  };
  return map[type] || 'fa-building';
}

function getColorValue(color) {
  if (color.startsWith('var(--')) {
    const prop = color.replace('var(', '').replace(')', '');
    return getComputedStyle(document.documentElement).getPropertyValue(prop).trim() || '#7c3aed';
  }
  return color;
}

function filterSports() {
  const q = document.getElementById('tableSearch').value.toLowerCase();
  const type = document.getElementById('filterType').value;
  const gender = document.getElementById('filterGender').value;
  const team = document.getElementById('filterTeam').value;
  const status = document.getElementById('filterStatus').value;

  filtered = SPORTS.filter(s => {
    const matchQ = !q || s.sport_name.toLowerCase().includes(q);
    const matchType = !type || s.sport_type === type;
    const matchGender = !gender || s.gender === gender;
    const matchTeam = team === '' || (team === 'true' ? s.is_team_sport : !s.is_team_sport);
    const matchStatus = status === '' || (status === 'true' ? s.is_active : !s.is_active);
    return matchQ && matchType && matchGender && matchTeam && matchStatus;
  });

  currentPage = 1;
  renderSports();
}

function renderSports() {
  const grid = document.getElementById('sportsGrid');
  const empty = document.getElementById('emptyState');
  const pagBar = document.getElementById('paginationBar');
  const info = document.getElementById('paginationInfo');
  const count = document.getElementById('resultCount');

  if (!filtered.length) {
    grid.innerHTML = '';
    empty.style.display = 'block';
    pagBar.style.display = 'none';
    count.textContent = '0 sports';
    return;
  }

  empty.style.display = 'none';
  pagBar.style.display = 'flex';

  const start = (currentPage - 1) * PER_PAGE;
  const page = filtered.slice(start, start + PER_PAGE);
  const total = filtered.length;

  count.textContent = `${total} sport${total !== 1 ? 's' : ''}`;
  info.textContent = `Showing ${Math.min(start + 1, total)}–${Math.min(start + PER_PAGE, total)} of ${total}`;

  grid.innerHTML = page.map((s, index) => {
    const color = getSportColor(s.sport_name);
    
    let playerText = 'Not specified';
    if (s.is_team_sport) {
      if (s.min_players !== null && s.max_players !== null) {
        playerText = `${s.min_players} - ${s.max_players} players`;
      } else if (s.min_players !== null) {
        playerText = `${s.min_players}+ players`;
      } else if (s.max_players !== null) {
        playerText = `Up to ${s.max_players} players`;
      }
    } else {
      playerText = 'Individual sport';
    }

    let thumbnailStyle = '';
    let overlayClass = 'sp-card-overlay';
    if (s.thumbnail) {
      thumbnailStyle = `background-image: url('${s.thumbnail}'); background-size: cover; background-position: center;`;
      overlayClass = 'sp-card-overlay active';
    }

    let iconHTML = '';
    if (s.icon) {
      iconHTML = `<img src="${s.icon}" alt="${s.sport_name}" class="sp-card-icon-img">`;
    } else {
      iconHTML = `<span style="font-size: 24px; font-weight: 700;">${s.sport_name.charAt(0)}</span>`;
    }

    return `
    <div class="col-12 col-sm-6 col-xl-4">
      <div class="sp-card-glass" data-aos="fade-up" data-aos-delay="${index * 100}" style="--card-color: ${color}; ${thumbnailStyle}">
        <div class="${overlayClass}"></div>
        <div class="sp-card-glow"></div>
        <div class="sp-card-content">
          <div class="sp-card-header">
            <div class="sp-card-icon" style="background: ${color}25; color: ${color}">
              ${iconHTML}
            </div>
            <span class="sp-card-status ${s.is_active ? 'active' : 'inactive'}">
              <span class="sp-status-dot"></span>
              ${s.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
          <div class="sp-card-actions">
            <a href="/dashboard/sports/edit/${s.sport_uuid}" class="sp-action sp-action-edit">
              <i class="fas fa-edit"></i>
            </a>
            <!-- <button class="sp-action sp-action-delete sport-delete-modal" data-sport-id="${s.id}" data-sport-name="${s.sport_name}">
              <i class="fas fa-trash"></i>
            </button> -->
          </div>
          <h3 class="sp-card-title">${s.sport_name}</h3>
          <div class="sp-card-badges">
            <span class="sp-badge sp-badge-${getTypeClass(s.sport_type)}">
              <i class="fas ${getTypeIcon(s.sport_type)}"></i> ${s.sport_type}
            </span>
            <span class="sp-badge sp-badge-${getGenderClass(s.gender)}">
              <i class="fas ${getGenderIcon(s.gender)}"></i> ${s.gender}
            </span>
            <span class="sp-badge ${s.is_team_sport ? 'sp-badge-team' : 'sp-badge-individual'}">
              <i class="fas fa-${s.is_team_sport ? 'users' : 'user'}"></i> ${s.is_team_sport ? 'Team' : 'Individual'}
            </span>
          </div>
          <div class="sp-card-metrics">
            <div class="sp-metric-item">
              <i class="fas fa-users"></i>
              <span>${playerText}</span>
            </div>
            <div class="sp-metric-item">
              <i class="fas fa-${s.is_olympic_sport ? 'trophy' : 'times'}"></i>
              <span>${s.is_olympic_sport ? 'Olympic' : 'Non-Olympic'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `}).join('');

  renderPagination(total);
}

function getSportColor(sportName) {
  const colors = [
    '#c5050c', '#228b22', '#185fa5', '#f59e0b', '#06b6d4',
    '#dc2626', '#7c3aed', '#ec4899', '#14b8a6', '#f97316',
    '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444'
  ];
  let hash = 0;
  for (let i = 0; i < sportName.length; i++) {
    hash = sportName.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % colors.length;
  return colors[index];
}

function renderPagination(total) {
  const pages = Math.ceil(total / PER_PAGE);
  const btns = document.getElementById('paginationBtns');
  if (!btns) return;

  let html = `<button class="sp-pag-btn" ${currentPage === 1 ? 'disabled' : ''} onclick="goPage(${currentPage - 1})"><i class="fas fa-chevron-left"></i></button>`;
  for (let p = 1; p <= pages; p++) {
    html += `<button class="sp-pag-btn ${p === currentPage ? 'active' : ''}" onclick="goPage(${p})">${p < 10 ? '0' : ''}${p}</button>`;
  }
  html += `<button class="sp-pag-btn" ${currentPage === pages ? 'disabled' : ''} onclick="goPage(${currentPage + 1})"><i class="fas fa-chevron-right"></i></button>`;
  btns.innerHTML = html;
}

function goPage(p) {
  const pages = Math.ceil(filtered.length / PER_PAGE);
  if (p < 1 || p > pages) return;
  currentPage = p;
  renderSports();
  document.querySelector('.sp-dashboard').scrollTo({ top: 0, behavior: 'smooth' });
}

function openDeleteModal(sportId, sportName) {
    console.log('Opening delete modal for:', sportId, sportName);
    
    sportToDeleteId = sportId;
    sportToDeleteName = sportName;
    
    const modal = document.getElementById("ub-delete-modal");
    if (!modal) {
        console.error('Modal element not found!');
        alert('Modal not found. Please check the HTML.');
        return;
    }
    
    const titleEl = document.getElementById("ub-modal-title");
    const bodyEl = document.getElementById("ub-modal-body");
    const usernameEl = document.getElementById("ub-status-modal-username");
    
    if (titleEl) titleEl.textContent = '🗑️ Delete Sport';
    if (bodyEl) bodyEl.textContent = `Are you sure you want to delete "${sportName}"? This action cannot be undone. All associated data will be permanently removed.`;
    if (usernameEl) usernameEl.textContent = sportName;
    
    modal.removeAttribute('hidden');
    modal.style.display = 'flex';
    modal.style.visibility = 'visible';
    modal.style.opacity = '1';
    document.body.style.overflow = 'hidden';
    
    console.log('Modal should be visible now');
    console.log('Modal display:', modal.style.display);
    console.log('Modal hidden:', modal.hidden);
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
    
    sportToDeleteId = null;
    sportToDeleteName = '';
}

function handleDeleteSport() {
    if (!sportToDeleteId) return;

    const confirmBtn = document.getElementById("ub-modal-confirm");

    confirmBtn.disabled = true;
    confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';

    window.location.href = `/dashboard/sports/delete/${sportToDeleteId}`;
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
    console.log('Setting up delete listeners');
    
    document.addEventListener('click', function(e) {
        const deleteBtn = e.target.closest('.sport-delete-modal');
        if (deleteBtn) {
            e.preventDefault();
            e.stopPropagation();
            
            const sportId = deleteBtn.getAttribute('data-sport-id');
            const sportName = deleteBtn.getAttribute('data-sport-name') || 
                             deleteBtn.closest('.sp-card-glass')?.querySelector('.sp-card-title')?.textContent || 
                             'Sport';
            
            console.log('Delete button clicked:', sportId, sportName);
            
            if (sportId) {
                openDeleteModal(parseInt(sportId), sportName);
            } else {
                console.error('Sport ID not found on delete button');
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    
    if (typeof AOS !== 'undefined') {
        AOS.init({ 
            duration: 600, 
            once: true, 
            easing: 'ease-out-cubic' 
        });
        console.log('AOS initialized');
    } else {
        console.warn('AOS not loaded');
    }
    
    fetchSports();
    
    setupDeleteListeners();
    setupModalListeners();
    
    document.querySelectorAll('.sp-select-glass').forEach(select => {
        new SlimSelect({
            select: select,
            settings: {
                placeholderText: select.options[0].text,
                showSearch: false
            }
        });
    });
});