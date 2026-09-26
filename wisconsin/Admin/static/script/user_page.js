// /* kali's  code  */


(function () {
  "use strict";

  let allUsers        = [];
  let filteredUsers   = [];
  let currentPage     = 1;
  let perPage         = 10;
  let activeMenuBtn   = null;
  let activeUserId    = null;
  let pendingDeleteId = null;
  let pendingStatusId = null;

  const tbody        = document.getElementById("ub-tbody");
  const searchInput  = document.getElementById("ub-search");
  const pagination   = document.getElementById("ub-pagination");
  const countEl      = document.getElementById("ub-count");
  const perPageSel   = document.getElementById("ub-per-page");
  const checkAll     = document.getElementById("ub-check-all");
  const filterToggle = document.getElementById("ub-filter-toggle");
  const filtersRow   = document.getElementById("ub-filters");
  const resetBtn     = document.getElementById("ub-reset");
  const actionMenu   = document.getElementById("ub-action-menu");
  // const deleteModal  = document.getElementById("ub-delete-modal");
    const statusModal  = document.getElementById("ub-delete-modal");
  const modalTitle   = document.getElementById("ub-modal-title");
  const modalBody    = document.getElementById("ub-modal-body");
  const modalUsername = document.getElementById("ub-status-modal-username");
  const modalCurrentStatus = document.getElementById("ub-status-modal-current");
  const modalStatusSelect  = document.getElementById("ub-status-modal-select");

  const fUsername = document.getElementById("f-username");
  const fUid      = document.getElementById("f-uid");
  const fRole     = document.getElementById("f-role");
  const fStatus   = document.getElementById("f-status");
  const fGender   = document.getElementById("f-gender");
  const fDateFrom = document.getElementById("f-date-from");
  const fDateTo   = document.getElementById("f-date-to");


  /**
 
   * @param {HTMLElement} btn  — the ⋮ button
   */

  
  function positionMenu(btn) {
    actionMenu.style.visibility = "hidden";
    actionMenu.hidden = false;

    const btnRect  = btn.getBoundingClientRect();
    const menuRect = actionMenu.getBoundingClientRect();
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    const MARGIN = 6;

    let top  = btnRect.bottom + MARGIN;
    let left = btnRect.right  - menuRect.width;

    if (top + menuRect.height > vh - MARGIN) {
      top = btnRect.top - menuRect.height - MARGIN;
    }
    if (left < MARGIN) left = MARGIN;
    if (left + menuRect.width > vw - MARGIN) {
      left = vw - menuRect.width - MARGIN;
    }
    if (top < MARGIN) top = MARGIN;

    actionMenu.style.top        = top  + "px";
    actionMenu.style.left       = left + "px";
    actionMenu.style.visibility = "";
  }

  function openMenu(btn, userId) {
    activeMenuBtn  = btn;
    activeUserId   = userId;
    positionMenu(btn);
  }

  function closeMenu() {
    actionMenu.hidden = true;
    activeMenuBtn  = null;
    activeUserId   = null;
  }

  function onScrollOrResize() {
    if (!actionMenu.hidden && activeMenuBtn) {
      positionMenu(activeMenuBtn);
    }
  }

  window.addEventListener("scroll", onScrollOrResize, { passive: true, capture: true });
  window.addEventListener("resize", onScrollOrResize, { passive: true });

  document.addEventListener("click", function (e) {
    if (actionMenu.hidden) return;
    if (e.target.closest(".ub-dots-btn") === activeMenuBtn) return;
    if (!actionMenu.contains(e.target)) closeMenu();
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !actionMenu.hidden) {
      closeMenu();
    }
  });

  function onDotsClick(e) {
    e.stopPropagation();
    const btn    = e.currentTarget;
    const userId = parseInt(btn.dataset.id, 10);

    if (!actionMenu.hidden && activeMenuBtn === btn) {
      closeMenu();
      return;
    }
    openMenu(btn, userId);
  }

  // document.getElementById("ub-action-edit").addEventListener("click", function () {
  //   if (activeUserId) {
  //     window.location.href = `/dashboard/user/${activeUserId}/edit/`;
  //   }
  //   closeMenu();
  // });
  document.getElementById("ub-action-edit").addEventListener("click", function () {
    if (!activeUserId) return;

    const user = allUsers.find(u => u.id === activeUserId);
    if (user) {
        window.location.href = `/dashboard/user/${user.uuid}/edit/`;
    }

    closeMenu();
});



 document.getElementById("ub-action-status").addEventListener("click", function () {
    if (activeUserId) {
      openStatusModal(activeUserId);
    }
    closeMenu();
  });

  function openStatusModal(userId) {
    const user = allUsers.find(function (u) { return u.id === userId; });
    if (!user) return;

    pendingStatusId = userId;

    modalTitle.textContent = "Change User Status";
    modalBody.textContent  = "Choose a new status for this user. This will be applied immediately.";

    modalUsername.textContent = user.full_name || user.username || "—";

    const currentCls   = statusClass(user.account_status);
    const currentLabel = statusLabel(user.account_status);
    modalCurrentStatus.textContent = currentLabel;
    modalCurrentStatus.className   = `ub-status-modal__value ub-status--${currentCls}`;

    modalStatusSelect.value = user.account_status || "ACTIVE";

    const confirmBtn = document.getElementById("ub-modal-confirm");
    confirmBtn.textContent = "Update Status";

    statusModal.hidden = false;
    setTimeout(function () {
      document.getElementById("ub-modal-cancel").focus();
    }, 50);
  }


  document.getElementById("ub-modal-cancel").addEventListener("click", function () {
    statusModal.hidden = true;
    pendingDeleteId = null;
  });

 statusModal.addEventListener("click", function (e) {
    if (e.target === statusModal) {
      statusModal.hidden = true;
      pendingStatusId = null;
    }
  });




    document.getElementById("ub-modal-confirm").addEventListener("click", async function () {
    if (!pendingStatusId) return;
    const confirmBtn = document.getElementById("ub-modal-confirm");
    const newStatus  = modalStatusSelect.value;
    confirmBtn.disabled = true;
    confirmBtn.textContent = "Updating…";

    try {
      const body = new URLSearchParams({ status: newStatus });
      const res = await fetch(`/dashboard/api/users/${pendingStatusId}/status/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCsrf(),
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: body,
      });
      const data = await res.json().catch(function () { return {}; });

      if (res.ok && data.ok) {
        const user = allUsers.find(function (u) { return u.id === pendingStatusId; });
        if (user) user.account_status = data.status;
        updateRowStatusBadge(pendingStatusId, data.status);
        renderStats();
        showToast("User status updated successfully.", "success");
      } else {
        showToast("Status update failed. Please try again.", "error");
      }
    } catch (_) {
      showToast("Network error. Please try again.", "error");
    }

    statusModal.hidden  = true;
    pendingStatusId     = null;
    confirmBtn.disabled = false;
    confirmBtn.textContent = "Update Status";
  });


  function updateRowStatusBadge(userId, status) {
    const row = tbody.querySelector(`tr[data-id="${userId}"]`);
    if (!row) return;
    const cell = row.children[6]; // STATUS column
    if (cell) cell.innerHTML = statusBadge(status);
  }

  function statusClass(status) {
    const map = { ACTIVE: "active", PENDING: "pending", SUSPENDED: "suspended", INACTIVE: "inactive" };
    return map[status] || "inactive";
  }

  function statusLabel(status) {
    return status ? status.charAt(0) + status.slice(1).toLowerCase() : "—";
  }


  async function fetchUsers() {
    try {
      const res  = await fetch("/dashboard/api/users/list/");
      const data = await res.json();
      allUsers   = data.users || data;
    } catch (e) {
      console.error("Fetch Error:", e);
      allUsers = [];
    }
    populateFilterDropdowns();
    applyFilters();
    renderStats();
    
  }

  function renderStats() {
    const total    = allUsers.length;
    const active   = allUsers.filter(function (u) { return u.account_status === "ACTIVE"; }).length;
    const students = allUsers.filter(function (u) { return u.is_student; }).length;
    const faculty  = allUsers.filter(function (u) { return u.is_faculty; }).length;
    const admins   = allUsers.filter(function (u) { return u.is_admin; }).length;

    animateCount("stat-total",    total);
    animateCount("stat-active",   active);
    animateCount("stat-students", students);
    animateCount("stat-faculty",  faculty);
    animateCount("stat-admins",   admins);

    setText("stat-total-delta",    "↑ 5.4% from last month");
    setText("stat-active-delta",   "↑ 4.2% from last month");
    setText("stat-students-delta", "↑ 6.3% from last month");
    setText("stat-faculty-delta",  "↑ 3.7% from last month");
    setText("stat-admins-delta",   "↑ 2.6% from last month");
  }

  function animateCount(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    let current = 0;
    const step  = Math.max(1, Math.ceil(target / 40));
    const timer = setInterval(function () {
      current = Math.min(current + step, target);
      el.textContent = current.toLocaleString();
      if (current >= target) clearInterval(timer);
    }, 20);
  }

  function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }

  function populateFilterDropdowns() {
    const usernames = [...new Set(allUsers.map(function (u) { return u.username; }))];
    // const uids      = [...new Set(allUsers.map(function (u) { return u.university_id; }))];
    const uids = [...new Set(
          allUsers
              .map(u => u.university_id)
              .filter(uid => uid && uid.trim() !== "")
      )];

    usernames.forEach(function (u) {
      const o = document.createElement("option");
      o.value = u; o.textContent = u;
      fUsername.appendChild(o);
    });
    uids.forEach(function (u) {
      const o = document.createElement("option");
      o.value = u; o.textContent = u;
      fUid.appendChild(o);
    });
  }

  function applyFilters() {
    const q           = searchInput.value.trim().toLowerCase();
    const roleVal     = fRole.value.toLowerCase();
    const statusVal   = fStatus.value;
    const genderVal   = fGender.value;
    const usernameVal = fUsername.value;
    const uidVal      = fUid.value;
    const dateFrom    = fDateFrom.value;
    const dateTo      = fDateTo.value;

    filteredUsers = allUsers.filter(function (u) {
      if (q) {
        const hay = [u.full_name, u.email, u.username, u.university_id].join(" ").toLowerCase();
        if (!hay.includes(q)) return false;
      }
      if (roleVal     && u.role             !== roleVal)     return false;
      if (statusVal   && u.account_status   !== statusVal)   return false;
      if (genderVal   && u.gender           !== genderVal)   return false;
      if (usernameVal && u.username         !== usernameVal) return false;
      if (uidVal      && u.university_id    !== uidVal)      return false;
      return true;
    });

    currentPage = 1;
    renderTable();
    renderPagination();
  }

  function renderTable() {
    const start = (currentPage - 1) * perPage;
    const slice = filteredUsers.slice(start, start + perPage);

    if (slice.length === 0) {
      tbody.innerHTML = `
        <tr><td colspan="9">
          <div class="ub-empty">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <p>No users found</p>
            <small>Try adjusting your search or filters.</small>
          </div>
        </td></tr>`;
      countEl.textContent = "Showing 0 results";
      return;
    }

    tbody.innerHTML = slice.map(function (u) {
       const editBtn = window.canEditUser
      ? `
            <a
                href="/dashboard/user/${u.uuid}/edit/"
                class="ub-action-btn ub-action-btn--edit"
                title="Edit User"
              >
                <i data-lucide="square-pen"></i>
              </a>`
      : "";
      return `
      <tr data-id="${u.id}">
        <td><input type="checkbox" class="ub-row-check" data-id="${u.id}" aria-label="Select ${escHtml(u.full_name)}" /></td>
        <td>
          <div class="ub-user-cell">
            <div class="ub-avatar">${avatarContent(u)}</div>
            <div>
              <div class="ub-user-name">${escHtml(u.full_name)}</div>
              <div class="ub-user-sub">${escHtml(u.username || "—")}</div>
            </div>
          </div>
        </td>
        <td>${escHtml(u.university_id || "—")}</td>
        <td>${escHtml(u.email || "—")}</td>
        <td>${roleBadge(u.role)}</td>
        <td>${escHtml(u.gender || "—")}</td>
        <td>${statusBadge(u.account_status)}</td>
        <td style="white-space:nowrap">${escHtml(u.created_at || "—")}</td>
        <td>
            <div class="ub-actions">

              <a href="/dashboard/user/${u.uuid}/view/"
                class="ub-action-btn ub-action-btn--view"
                title="View User"
              >
                <i data-lucide="eye"></i>
              </a>
              
              ${editBtn}

                ${window.canEditUser ? `
              <button
                class="ub-action-btn ub-action-btn--status"
                data-id="${u.id}"
                title="Change Status"
              >
                <i data-lucide="refresh-cw"></i>
              </button>` : ""}

            </div>
          </td>
      </tr>`;
    }).join("");

    if (window.lucide) {
    lucide.createIcons();
}

    

    const total = filteredUsers.length;
    const end   = Math.min(start + perPage, total);
    countEl.textContent = `Showing ${start + 1} to ${end} of ${total.toLocaleString()} results`;


    
    tbody.querySelectorAll(".ub-action-btn--status").forEach(function(btn) {
        btn.addEventListener("click", function() {
            const userId = parseInt(this.dataset.id, 10);
            openStatusModal(userId);
        });
    });

    checkAll.checked = false;
    checkAll.indeterminate = false;
  }

  function avatarContent(u) {
    if (u.profile_photo) {
      return `<img src="${u.profile_photo}" alt="${escHtml(u.full_name)}" loading="lazy" />`;
    }
    const initials = (u.full_name || "?")
      .split(" ")
      .map(function (w) { return w[0]; })
      .slice(0, 2)
      .join("")
      .toUpperCase();
    return initials;
  }
 
  function roleBadge(role) {
    const map = {
      student: ["ub-badge--student", "🎓", "Student"],
      faculty: ["ub-badge--faculty", "📚", "Faculty"],
      admin:   ["ub-badge--admin",   "🛡",  "Administrator"],
      staff:   ["ub-badge--staff",   "👨‍💼", "Staff"],
    };
    const [cls, icon, label] = map[role] || ["ub-badge--student", "", role || "—"];
    return `<span class="ub-badge ${cls}">${icon} ${escHtml(label)}</span>`;
  }

  function statusBadge(status) {
    const map = {
      ACTIVE:    "active",
      PENDING:   "pending",
      SUSPENDED: "suspended",
      INACTIVE:  "inactive",
    };
    const cls   = map[status] || "inactive";
    const label = status ? status.charAt(0) + status.slice(1).toLowerCase() : "—";
    return `<span class="ub-status ub-status--${cls}"><span class="ub-status__dot" aria-hidden="true"></span>${escHtml(label)}</span>`;
  }

  function escHtml(str) {
    return String(str ?? "").replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function getCsrf() {
    const match = document.cookie.split(";").find(function (c) {
      return c.trim().startsWith("csrftoken=");
    });
    return match ? match.split("=")[1] : "";
  }

  function renderPagination() {
    const total = filteredUsers.length;
    const pages = Math.ceil(total / perPage);
    if (pages <= 1) { pagination.innerHTML = ""; return; }

    const btns = [];
    const add  = function (label, page, cls) {
      btns.push({ label: label, page: page, cls: cls || "" });
    };

    add("‹", currentPage - 1);
    add("1", 1);
    if (currentPage > 4) add("…", null, "ub-page-btn--ellipsis");

    for (let p = Math.max(2, currentPage - 2); p <= Math.min(pages - 1, currentPage + 2); p++) {
      add(String(p), p);
    }

    if (currentPage < pages - 3) add("…", null, "ub-page-btn--ellipsis");
    if (pages > 1) add(String(pages), pages);
    add("›", currentPage + 1);

    pagination.innerHTML = btns.map(function (b) {
      const isActive = b.page === currentPage ? "active" : "";
      const disabled = (b.page === null || b.page < 1 || b.page > pages) ? "disabled" : "";
      return `<button class="ub-page-btn ${b.cls} ${isActive}" data-page="${b.page}" ${disabled} aria-label="Page ${b.label}">${b.label}</button>`;
    }).join("");

    pagination.querySelectorAll(".ub-page-btn:not([disabled])").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const p = parseInt(btn.dataset.page, 10);
        if (p && p !== currentPage) {
          currentPage = p;
          renderTable();
          renderPagination();
          document.getElementById("ub-tbody").closest(".ub-table-wrap").scrollIntoView({
            behavior: "smooth", block: "nearest"
          });
        }
      });
    });
  }

  function showToast(msg, type) {
    type = type || "success";
    const t = document.createElement("div");
    t.className = "ub-toast ub-toast--" + type;
    t.setAttribute("role", "status");
    t.setAttribute("aria-live", "polite");
    t.textContent = msg;
    document.body.appendChild(t);
    requestAnimationFrame(function () { t.classList.add("ub-toast--show"); });
    setTimeout(function () {
      t.classList.remove("ub-toast--show");
      setTimeout(function () { t.remove(); }, 300);
    }, 2500);
  }

  filterToggle.addEventListener("click", function () {
    const isOpen = filtersRow.classList.toggle("open");
    filterToggle.classList.toggle("active", isOpen);
    filterToggle.setAttribute("aria-expanded", String(isOpen));
  });

  resetBtn.addEventListener("click", function () {
    searchInput.value = "";
    [fUsername, fUid, fRole, fStatus, fGender].forEach(function (s) { s.value = ""; });
    fDateFrom.value = "";
    fDateTo.value   = "";
    applyFilters();
  });

  let searchTimer;
  searchInput.addEventListener("input", function () {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(applyFilters, 220);
  });

  [fUsername, fUid, fRole, fStatus, fGender, fDateFrom, fDateTo].forEach(function (el) {
    el.addEventListener("change", applyFilters);
  });

  perPageSel.addEventListener("change", function () {
    perPage     = parseInt(perPageSel.value, 10);
    currentPage = 1;
    renderTable();
    renderPagination();
  });

  checkAll.addEventListener("change", function () {
    tbody.querySelectorAll(".ub-row-check").forEach(function (c) {
      c.checked = checkAll.checked;
    });
  });

  tbody.addEventListener("change", function (e) {
    if (!e.target.classList.contains("ub-row-check")) return;
    const all     = tbody.querySelectorAll(".ub-row-check");
    const checked = tbody.querySelectorAll(".ub-row-check:checked");
    checkAll.checked       = checked.length === all.length;
    checkAll.indeterminate = checked.length > 0 && checked.length < all.length;
  });

  fetchUsers();
  

})();