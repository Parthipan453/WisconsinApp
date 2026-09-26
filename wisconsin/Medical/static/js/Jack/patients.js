(function () {
  "use strict";
// -------------swetha's changes  ---------------

  let patients = [];
    async function loadPatients(){

      try{

          const response = await fetch(patientAPI);
          const data = await response.json();

          patients = data.patients;

          updateOverviewCounts();
          updateGrowthStats(data.stats);

          render();

      }
      catch(error){

          console.error(
              "Patient loading failed:",
              error
          );

      }
      // -------------swetha's changes  end----------------

  }

  const grid = document.getElementById("patientGrid");
  const countDisplay = document.getElementById("patientCountDisplay");
  const totalDisplay = document.getElementById("totalPatients");
  const studentDisplay = document.getElementById("studentCount");
  const facultyDisplay = document.getElementById("facultyCount");
  const staffDisplay = document.getElementById("staffCount");
  const filterType = document.getElementById("filterType");
  const filterBlood = document.getElementById("filterBlood");
  const searchInput = document.getElementById("mdpSearchInput");
  const searchClear = document.getElementById("mdpSearchClear");
  const prevBtn = document.getElementById("prevPage");
  const nextBtn = document.getElementById("nextPage");
  const pageNumbers = document.getElementById("pageNumbers");
  const pageInfo = document.getElementById("pageInfo");

  let currentType = "all";
  let currentBlood = "all";
  let searchQuery = "";
  let currentPage = 1;
  const pageSize = 6;

  function getPatientName(p) {
    if (p.student) return `${p.student.first_name} ${p.student.last_name}`;
    if (p.faculty) return `${p.faculty.first_name} ${p.faculty.last_name}`;
    if (p.staff) return `${p.staff.first_name} ${p.staff.last_name}`;
    if (p.admin) return `${p.admin.first_name} ${p.admin.last_name}`;
    if (p.visitor_name) return p.visitor_name;
    return "Unknown";
  }

  function extractSlimSelectValue(newVal, fallback) {
    if (!newVal || !newVal.length) return fallback;
    const first = newVal[0];
    if (first && typeof first === "object") {
      return first.value || fallback;
    }
    return first || fallback;
  }

  function getFilteredData() {
    return patients.filter((p) => {
      if (currentType !== "all" && p.patient_type !== currentType) return false;
      if (currentBlood !== "all" && p.blood_group !== currentBlood)
        return false;
      if (searchQuery.trim() !== "") {
        const q = searchQuery.trim().toLowerCase();
        const fullName = getPatientName(p).toLowerCase();
        const num = p.patient_number.toLowerCase();
        const allergy = (p.allergies || "").toLowerCase();
        const chronic = (p.chronic_conditions || "").toLowerCase();
        const remark = (p.remarks || "").toLowerCase();
        if (
          !fullName.includes(q) &&
          !num.includes(q) &&
          !allergy.includes(q) &&
          !chronic.includes(q) &&
          !remark.includes(q)
        ) {
          return false;
        }
      }
      return true;
    });
  }

  function updateOverviewCounts() {
    const total = patients.length;
    const students = patients.filter(p => p.patient_type === 'STUDENT').length;
    const faculty = patients.filter(p => p.patient_type === 'FACULTY').length;
    const staff = patients.filter(p => p.patient_type === 'STAFF').length;
    const admin = patients.filter(p => p.patient_type === 'ADMIN').length;
    const visitor = patients.filter(p => p.patient_type === 'VISITOR').length;
    totalDisplay.textContent = total;
    studentDisplay.textContent = students;
    facultyDisplay.textContent = faculty;
    staffDisplay.textContent = staff;
  }
  function setTrend(elementId, value) {
    const el = document.getElementById(elementId);
    if (!el) return;
    if (value > 0) {
        el.innerHTML = `<i class="bi bi-arrow-up-short"></i> ${value}% this month`;
    }
    else if (value < 0) {
        el.innerHTML = `<i class="bi bi-arrow-down-short"></i> ${Math.abs(value)}% this month`;
    }
    else {
        el.innerHTML = `<i class="bi bi-dash"></i> No change`;
    }
}

// function updateGrowthStats(stats) {

//     setTrend("totalPatientsTrend", stats.total_growth);
//     setTrend("studentTrend", stats.student_growth);
//     setTrend("facultyTrend", stats.faculty_growth);
//     setTrend("staffTrend", stats.staff_growth);

// }
// -------------swetha's changes ----------------
function updateGrowthStats(stats) {
    if (!stats) return;

    document.getElementById("totalPatientsTrend").innerHTML =
        `<i class="bi bi-arrow-${stats.growth >= 0 ? "up" : "down"}-short"></i>
         ${Math.abs(stats.growth)}% this month`;

    document.getElementById("studentTrend").innerHTML =
        `<i class="bi bi-arrow-${stats.student_growth >= 0 ? "up" : "down"}-short"></i>
         ${Math.abs(stats.student_growth)}% this month`;

    document.getElementById("facultyTrend").innerHTML =
        `<i class="bi bi-arrow-${stats.faculty_growth >= 0 ? "up" : "down"}-short"></i>
         ${Math.abs(stats.faculty_growth)}% this month`;

    document.getElementById("staffTrend").innerHTML =
        `<i class="bi bi-arrow-${stats.staff_growth >= 0 ? "up" : "down"}-short"></i>
         ${Math.abs(stats.staff_growth)}% this month`;
}
// -------------swetha's changes  end----------------
  function render() {
    const filtered = getFilteredData();
    const totalItems = filtered.length;
    const totalPages = Math.ceil(totalItems / pageSize) || 1;

    if (currentPage > totalPages) currentPage = totalPages;
    if (currentPage < 1) currentPage = 1;

    const start = (currentPage - 1) * pageSize;
    const end = Math.min(start + pageSize, totalItems);
    const pageItems = filtered.slice(start, end);

    countDisplay.textContent = patients.length;
    updateOverviewCounts();

    if (pageItems.length === 0) {
      grid.innerHTML = `
          <div class="mdp-empty-state" data-aos="fade-up" data-aos-duration="600">
            <i class="bi bi-inbox"></i>
            <h5 class="mt-2">No patients match</h5>
            <p class="text-muted small">Try adjusting filters or search terms</p>
          </div>
        `;
    } else {
      grid.innerHTML = pageItems
        .map((p, index) => {
          const name = getPatientName(p);
          const initials = name
            .split(" ")
            .map((w) => w[0])
            .join("")
            .toUpperCase()
            .slice(0, 2);
          const typeLabel = p.patient_type.charAt(0) + p.patient_type.slice(1).toLowerCase();
          // const isAthlete =
          //             p.patient_type === "STUDENT" &&
          //             p.is_athlete
          const isAthlete = p.is_athlete === true;

          // --------- swetha's changes -----------
          let typeIcon;

          switch (p.patient_type) {
              case "STUDENT":
                  typeIcon = "bi-mortarboard-fill";
                  break;

              case "FACULTY":
                  typeIcon = "bi-person-workspace";
                  break;

              case "STAFF":
                  typeIcon = "bi-person-badge";
                  break;

              case "ADMIN":
                  typeIcon = "bi-shield-lock-fill";
                  break;

              case "VISITOR":
                  typeIcon = "bi-person-vcard-fill";
                  break;

              default:
                  typeIcon = "bi-person-fill";
          }

            // --------- swetha's changes end -----------
          const blood = p.blood_group || "N/A";
          const allergy = p.allergies || "None";
          const chronic = p.chronic_conditions || "None";
          const phone = p.phone || "—";
          const email = p.email || "—";
          const remarks = p.remarks || "";
          const isActive = p.is_active !== undefined ? p.is_active : true;

          let avatarHtml;
          if (p.avatar) {
            avatarHtml = `<img src="${p.avatar}" alt="${name}" />`;
          } else {
            avatarHtml = initials;
          }

          const statusBadge = isActive
            ? `<span class="mdp-status-badge active"><i class="bi bi-check-circle-fill me-1"></i>Active</span>`
            : `<span class="mdp-status-badge inactive"><i class="bi bi-x-circle-fill me-1"></i>Inactive</span>`;

          return `
            <div class="mdp-patient-card" data-id="${p.id}" data-aos="fade-up" data-aos-duration="600" data-aos-delay="${index * 80}">
              ${statusBadge}
              <div class="mdp-card-top">
                <div class="mdp-patient-avatar ${p.avatar ? "" : "initials"}">${avatarHtml}</div>
              </div>
              <div class="mdp-patient-name">${name}</div>
              <div class="mt-1 d-flex flex-wrap align-items-center gap-1">

                  <span class="mdp-patient-type-badge">
                      <i class="bi ${typeIcon} me-1"></i>
                      ${typeLabel}
                  </span>

                  ${
                      isAthlete
                          ? `
                          <span class="mdp-patient-athlete-badge">
                              <i class="bi bi-trophy-fill me-1"></i>
                              Athlete
                          </span>
                          `
                          : ""
                  }

              </div>
              <div class="mt-1 d-flex flex-wrap align-items-center gap-2">
                <span class="mdp-blood-group"><i class="bi bi-droplet me-1"></i> ${blood}</span>
                <span class="mdp-allergy-tag"><i class="bi bi-exclamation-triangle-fill me-1" style="color:var(--primary);"></i> ${allergy}</span>
              </div>
              <div class="mdp-detail-row"><i class="bi bi-telephone-fill"></i> ${phone}</div>
              <div class="mdp-detail-row"><i class="bi bi-envelope-fill"></i> ${email}</div>
              <hr class="mdp-card-divider" />
              ${remarks ? `<div class="mdp-remarks"><i class="bi bi-chat-left-quote me-1"></i> ${remarks}</div>` : ""}
              <div class="mdp-card-actions">
                <a href="/medical/view_patient/${p.uuid}" class="mdp-card-action-btn view-btn" title="View Details"><i class="bi bi-eye"></i></a>
                <a href="/medical/edit_patient/${p.uuid}" class="mdp-card-action-btn edit-btn" title="Edit Patient"><i class="bi bi-pencil"></i></a>
              </div>
            </div>

            
          `;
        })
        .join("");

    }

    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === totalPages || totalPages === 0;

    let pagesHtml = "";
    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    if (endPage - startPage < maxVisible - 1)
      startPage = Math.max(1, endPage - maxVisible + 1);

    for (let i = startPage; i <= endPage; i++) {
      pagesHtml += `<button class="mdp-page-btn ${i === currentPage ? "active" : ""}" data-page="${i}">${i}</button>`;
    }
    pageNumbers.innerHTML = pagesHtml;

    document.querySelectorAll("#pageNumbers .mdp-page-btn").forEach((btn) => {
      btn.addEventListener("click", function () {
        const page = parseInt(this.dataset.page, 10);
        if (page !== currentPage) {
          currentPage = page;
          render();
          if (window.AOS) {
            window.AOS.refresh();
          }
        }
      });
    });

    const startDisplay = totalItems === 0 ? 0 : start + 1;
    const endDisplay = totalItems === 0 ? 0 : end;
    pageInfo.textContent = `Showing ${startDisplay}–${endDisplay} of ${totalItems}`;

    if (window.AOS) {
      window.AOS.refresh();
    }
  }

  function initializeFilters() {
    new SlimSelect({
      select: filterType,
      settings: {
        placeholderText: 'All Types',
        showSearch: false,
        allowDeselect: false
      },
      events: {
        afterChange: function (newVal) {
          currentType = extractSlimSelectValue(newVal, 'all');
          currentPage = 1;
          render();
        }
      }
    });

    new SlimSelect({
      select: filterBlood,
      settings: {
        placeholderText: 'All Blood Groups',
        showSearch: false,
        allowDeselect: false
      },
      events: {
        afterChange: function (newVal) {
          currentBlood = extractSlimSelectValue(newVal, 'all');
          currentPage = 1;
          render();
        }
      }
    });

    currentType = filterType.value || 'all';
    currentBlood = filterBlood.value || 'all';
  }

  searchInput.addEventListener("input", function () {
    searchQuery = this.value;
    searchClear.classList.toggle("visible", this.value.length > 0);
    currentPage = 1;
    render();
  });

  searchClear.addEventListener("click", function () {
    searchInput.value = "";
    searchQuery = "";
    this.classList.remove("visible");
    currentPage = 1;
    render();
    searchInput.focus();
  });

  prevBtn.addEventListener("click", function () {
    if (currentPage > 1) {
      currentPage--;
      render();
    }
  });

  nextBtn.addEventListener("click", function () {
    const filtered = getFilteredData();
    const totalPages = Math.ceil(filtered.length / pageSize);
    if (currentPage < totalPages) {
      currentPage++;
      render();
    }
  });
  
  if (typeof AOS !== "undefined") {
    AOS.init({
      duration: 800,
      once: true,
      offset: 50,
    });
  }

  // updateOverviewCounts();
  // initializeFilters(); 
  // render();
  initializeFilters();
  loadPatients();

})();