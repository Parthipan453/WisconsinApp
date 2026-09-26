// kali code 

(function () {
    "use strict";



    function loadPermissionUsers() {
        const el = document.getElementById("faPermissionUsersData");
        if (!el) return [];
        try {
            return JSON.parse(el.textContent); 
        } catch (e) {
            return [];
        }
    }

    document.addEventListener("DOMContentLoaded", init);

    function init() { 
        refreshIcons();

        const firearms = loadFirearms();

        animateCounterBars();
        buildDerivedStats(firearms);
        buildStorageOverview(firearms);
        buildCharts(firearms);
        // renderPermissionUsers(PERMISSION_USERS);
        const permissionUsers = loadPermissionUsers();
        renderPermissionUsers(permissionUsers);
        wireUserRowNavigation();
        wireUserRowEditFirearm();
        wireUserFilters();
        wireQuickActions();
        wireAddFirearmFlow();
        initCustomDropdowns();
        wirePurchaseDatePicker();
    }

    function refreshIcons() {
        if (window.lucide) lucide.createIcons();
    }



    function openEditFirearmForm(firearmId, username) {
        const record = loadFirearms().find((f) => String(f.id) === String(firearmId));
        if (!record) {
            showToast("Unable to load that firearm record.", "error");
            return;
        }

        resetAddFirearmForm();

        const form = document.getElementById("faAddFirearmForm");
        form.dataset.mode = "edit";
        document.getElementById("faFirearmRecordId").value = record.id;

        // Lock the Assigned User field to this row's user
        faSelectedUsername = username;
        document.getElementById("faUserSearchValue").value = username;
        const searchField = document.getElementById("faUserSearchField");
        searchField.value = username;
        searchField.setAttribute("readonly", "true");
        searchField.classList.add("fa-form__input--locked");

        document.getElementById("faFirearmName").value = record.name || "";
        document.getElementById("faManufacturer").value = record.manufacturer || "";
        document.getElementById("faModelName").value = record.model || "";
        document.getElementById("faSerialNumber").value = record.serial || "";
        document.getElementById("faCaliber").value = record.caliber || "";
        document.getElementById("faPurchaseDate").value = record.purchase || "";
        document.getElementById("faLocationName").value = record.location || "";
        document.getElementById("faBuildingName").value = record.building || "";
        document.getElementById("faRoomNumber").value = record.room || "";
        document.getElementById("faSecurityLevel").value = record.security || "";
        document.getElementById("faNotes").value = record.notes || "";

        


        setDropdownValue("faFirearmType", record.type || "");
        setDropdownValue("faAcquisitionMethod", record.acquisition || "PURCHASE");
        setDropdownValue("faCurrentStatus", record.status || "ACTIVE");

        document.getElementById("faFormHeadTitle").textContent = "Edit Firearm Record";
        document.getElementById("faFormHeadSub").textContent = `Updating the firearm assigned to ${username}`;

        const dashboard = document.getElementById("faDashboardSections");
        const formSection = document.getElementById("faAddFirearmSection");
        dashboard.style.display = "none";
        formSection.style.display = "block";
        formSection.classList.remove("fa-form-section");
        void formSection.offsetWidth;
        formSection.classList.add("fa-form-section");
        refreshIcons();
    }

   

    const faChoicesInstances = {};

    function initCustomDropdowns() {
        if (typeof Choices === "undefined") return;

        document.querySelectorAll("select.fa-choices-target").forEach((select) => {
            if (faChoicesInstances[select.id]) return;

            const instance = new Choices(select, {
                searchEnabled: false,
                shouldSort: false,
                itemSelectText: "",
                allowHTML: false,
                position: "bottom",
            });

            

            faChoicesInstances[select.id] = instance;
        });
    }

   
  
   
function syncCustomDropdown(selectId) {
    const select = document.getElementById(selectId);
    const instance = faChoicesInstances[selectId];

    if (!select || !instance) return;

    instance.removeActiveItems();
    instance.setChoiceByValue(select.value);
}


function setDropdownValue(selectId, value) {
    const select = document.getElementById(selectId);
    const instance = faChoicesInstances[selectId];
    if (!select) return;

    if (instance) {
        instance.setChoiceByValue(value);
    } else {
        select.value = value;
    }
}

    function wirePurchaseDatePicker() {
        const input = document.getElementById("faPurchaseDate");
        if (!input) return;

        function openPicker() {
            if (typeof input.showPicker === "function") {
                try {
                    input.showPicker();
                } catch (e) {
                    
                }
            }
        }

        input.addEventListener("click", openPicker);
        input.addEventListener("focus", openPicker);

        
        input.addEventListener("keydown", (e) => {
            if (e.key === "Tab" || e.key === "Shift") return;
            e.preventDefault();
        });
    }

    function loadFirearms() {
        const el = document.getElementById("faFirearmsData");
        if (!el) return [];
        try {
            return JSON.parse(el.textContent) || [];
        } catch (e) {
            console.error("Firearm data parse error:", e);
            return [];
        }
    }


    function buildDerivedStats(firearms) {
        const types = new Set(firearms.map((f) => f.type).filter(Boolean));
        const locations = new Set(
            firearms.map((f) => `${f.building}::${f.room}`).filter(Boolean)
        );

        const typeEl = document.getElementById("faTypeCount");
        const locEl = document.getElementById("faLocationCount");
        if (typeEl) typeEl.setAttribute("data-count-to", String(types.size));
        if (locEl) locEl.setAttribute("data-count-to", String(locations.size));

        
        [typeEl, locEl].forEach((el) => {
            if (!el) return;
            animateNumber(el, parseInt(el.getAttribute("data-count-to"), 10) || 0);
        });
    }


    function animateCounterBars() {
        document.querySelectorAll(".fa-stat__number[data-count-to]").forEach((el) => {
            const target = parseInt(el.getAttribute("data-count-to"), 10) || 0;
            animateNumber(el, target);
        });

        document.querySelectorAll(".fa-stat__pct[data-pct-of]").forEach((el) => {
            const total = parseFloat(el.getAttribute("data-pct-of")) || 0;
            const value = parseFloat(el.getAttribute("data-pct-value")) || 0;
            const pct = total > 0 ? Math.round((value / total) * 100) : 0;
            el.textContent = `${pct}% of total`;
        });

        document.querySelectorAll(".fa-stat__bar span[data-fill-total]").forEach((el) => {
            const total = parseFloat(el.getAttribute("data-fill-total")) || 0;
            const value = parseFloat(el.getAttribute("data-fill-pct")) || 0;
            const pct = total > 0 ? (value / total) * 100 : 0;
            requestAnimationFrame(() => { el.style.width = `${pct}%`; });
        });
    }

    function animateNumber(el, target) {
        const duration = 900;
        const start = performance.now();

        function tick(now) {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.round(target * eased).toLocaleString();
            if (progress < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    }

    

    function buildStorageOverview(firearms) {
        const container = document.getElementById("faLocations");
        if (!container) return;

        const groups = new Map();
        firearms.forEach((f) => {
            const key = `${f.building}::${f.room}`;
            if (!groups.has(key)) {
                groups.set(key, {
                    building: f.building,
                    room: f.room,
                    location: f.location,
                    security: f.security,
                    count: 0,
                });
            }
            groups.get(key).count += 1;
        });

   

    container.innerHTML = "";
        groups.forEach((g) => {
      
            const capacity = Math.max(g.count + 2, Math.ceil(g.count / 0.65));
            const pct = Math.round((g.count / capacity) * 100);

            const card = document.createElement("div");
            card.className = "fa-location-card";
            card.innerHTML = `
                <div class="fa-location-card__title">
                    <i data-lucide="building-2"></i>
                    <span>${g.building} · ${g.room}</span>
                </div>
                <div class="fa-location-card__sub">${g.location}</div>
                <div class="fa-location-card__row"><span>Security Level</span><strong>${g.security}</strong></div>
                <div class="fa-location-card__row"><span>Current Firearms</span><strong>${g.count} / ${capacity}</strong></div>
                <div class="fa-location-card__bar"><span data-target="${pct}"></span></div>
            `;
            container.appendChild(card);
        });

        refreshIcons();

        requestAnimationFrame(() => {
            container.querySelectorAll(".fa-location-card__bar span").forEach((bar) => {
                bar.style.width = `${bar.getAttribute("data-target")}%`;
            });
        });

        initLocationCarousel(container, groups.size);
    }

    function initLocationCarousel(track, count) {
        const dotsWrap = document.getElementById("faLocationDots");
        const carouselEl = document.getElementById("faLocationCarousel");
        if (dotsWrap) dotsWrap.innerHTML = "";
        track.style.transform = "translateX(0%)";

        if (count <= 1) {
            if (dotsWrap) dotsWrap.style.display = "none";
            return;
        }

        if (dotsWrap) {
            dotsWrap.style.display = "flex";
            for (let i = 0; i < count; i++) {
                const dot = document.createElement("span");
                if (i === 0) dot.classList.add("is-active");
                dot.addEventListener("click", () => goToSlide(i));
                dotsWrap.appendChild(dot);
            }
        }

        let index = 0;
        const intervalMs = 4000;

        function goToSlide(i) {
            index = i;
            track.style.transform = `translateX(-${index * 100}%)`;
            if (dotsWrap) {
                dotsWrap.querySelectorAll("span").forEach((d, di) => {
                    d.classList.toggle("is-active", di === index);
                });
            }
        }

        function next() {
            goToSlide((index + 1) % count);
        }

        let timer = setInterval(next, intervalMs);

        if (carouselEl) {
            carouselEl.addEventListener("mouseenter", () => clearInterval(timer));
            carouselEl.addEventListener("mouseleave", () => {
                clearInterval(timer);
                timer = setInterval(next, intervalMs);
            });
        }
    }


    function buildCharts(firearms) {
        if (!window.Chart) return;

        const dataEl = document.getElementById("faChartData");
        let payload = { typeLabels: [], typeData: [], statusLabels: [], statusData: [] };
        if (dataEl) {
            try { payload = JSON.parse(dataEl.textContent); } catch (e) {  }
        }

        const palette = ["#c5050c", "#2563eb", "#059669", "#d97706", "#7c3aed", "#6b7280"];

        const typeCanvas = document.getElementById("faTypeChart");
        if (typeCanvas) {
            new Chart(typeCanvas, {
                type: "doughnut",
                data: {
                    labels: payload.typeLabels,
                    datasets: [{
                        data: payload.typeData,
                        backgroundColor: palette,
                        borderColor: "#ffffff",
                        borderWidth: 2,
                        hoverOffset: 8,
                    }],
                },
                options: {
                    maintainAspectRatio: false,
                    plugins: { legend: { position: "bottom", labels: { boxWidth: 10, font: { size: 11 } } } },
                    cutout: "62%",
                },
            });
        }

        const statusCanvas = document.getElementById("faStatusChart");
        if (statusCanvas) {
            new Chart(statusCanvas, {
                type: "bar",
                data: {
                    labels: payload.statusLabels,
                    datasets: [{
                        label: "Firearms",
                        data: payload.statusData,
                        backgroundColor: ["#059669", "#2563eb", "#d97706", "#c5050c"],
                        borderRadius: 8,
                        maxBarThickness: 42,
                    }],
                },
                options: {
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "rgba(0,0,0,0.06)" } },
                        x: { grid: { display: false } },
                    },
                },
            });
        }

        const acquisitionCanvas = document.getElementById("faAcquisitionChart");
        if (acquisitionCanvas) {
            const counts = {};
            firearms.forEach((f) => {
                const key = f.acquisition || "OTHER";
                counts[key] = (counts[key] || 0) + 1;
            });
            const labels = Object.keys(counts).map(
                (k) => k.charAt(0) + k.slice(1).toLowerCase()
            );

            new Chart(acquisitionCanvas, {
                type: "pie",
                data: {
                    labels,
                    datasets: [{
                        data: Object.values(counts),
                        backgroundColor: palette,
                        borderColor: "#ffffff",
                        borderWidth: 2,
                    }],
                },
                options: {
                    maintainAspectRatio: false,
                    plugins: { legend: { position: "bottom", labels: { boxWidth: 10, font: { size: 11 } } } },
                },
            });
        }
    }


    function permBadgeClass(level) {
        if (level === "Full Access") return "fa-perm-badge--full";
        if (level === "Custody Only") return "fa-perm-badge--custody";
        return "fa-perm-badge--view";
    }

    function typeBadgeClass(type) {
        if (type === "Handgun") return "fa-perm-badge--full";
        if (type === "Rifle") return "fa-perm-badge--custody";
        if (type === "Shotgun") return "fa-perm-badge--view";
        return "fa-perm-badge--view";
    }

    function statusBadgeClass(status) {

    switch (status) {
        case "Active":
            return "fa-status-badge--active";

        case "Stored":
            return "fa-status-badge--stored";

        case "Retired":
            return "fa-status-badge--retired";

        case "Disposed":
            return "fa-status-badge--disposed";

        default:
            return "fa-status-badge--expired";
    }
}

    function formatDate(iso) {
        const d = new Date(iso);
        if (isNaN(d.getTime())) return iso;
        return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
    }

    function renderPermissionUsers(users) {
        const tbody = document.getElementById("faUserTableBody");
        const cardsWrap = document.getElementById("faUserCards");
        if (!tbody || !cardsWrap) return;

        tbody.innerHTML = "";
        cardsWrap.innerHTML = "";

        if (users.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--gray-500); padding:24px;">No users match this filter.</td></tr>`;
            cardsWrap.innerHTML = `<div class="fa-user-card"><span style="color:var(--gray-500); font-size:13px;">No users match this filter.</span></div>`;
            return;
        }

        users.forEach((u) => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>
                    <div class="fa-user-cell">
                        <span class="fa-avatar">${u.initials}</span>
                        <div class="fa-user-cell__body">
                            <span class="fa-user-cell__name">${u.name}</span>
                            <span class="fa-user-cell__id">${u.employeeId}</span>
                        </div>
                    </div> 
                </td>
                <td>${u.department}<br><span style="color:var(--gray-500); font-size:12px;">${u.role}</span></td>
                <td><span class="fa-perm-badge ${typeBadgeClass(u.firearmType)}">${u.firearmType || "—"}</span></td>
                <td>${u.firearmsAssigned}</td>
                <td>${formatDate(u.grantedOn)}</td>
                <td><span class="fa-status-badge ${statusBadgeClass(u.status)}">${u.status}</span></td>
                <td>
                    <button type="button" class="fa-row-action" data-fa-view-user="${u.uuid}" title="View user"><i data-lucide="eye"></i></button>
                    ${(u.firearmId && window.FA_CAN_UPDATE_FIREARM) ? `<button type="button" class="fa-row-action" data-fa-edit-firearm="${u.firearmId}" data-fa-edit-username="${u.username}" title="Edit firearm record"><i data-lucide="pencil"></i></button>` : ""}
                </td>
            `;
            tbody.appendChild(row);

            const card = document.createElement("div");
            card.className = "fa-user-card";
            card.innerHTML = `
                <div class="fa-user-card__top"> 
                    <div class="fa-user-cell">
                        <span class="fa-avatar">${u.initials}</span>
                        <div class="fa-user-cell__body">
                            <span class="fa-user-cell__name">${u.name}</span>
                            <span class="fa-user-cell__id">${u.employeeId} · ${u.department}</span>
                        </div>
                    </div>
                    <span class="fa-status-badge ${statusBadgeClass(u.status)}">${u.status}</span>
                </div>
                <div class="fa-user-card__meta">
                    <span class="fa-perm-badge ${typeBadgeClass(u.firearmType)}">${u.firearmType || "—"}</span>
                    <span>${u.firearmsAssigned} firearm(s)</span>
                    <span>Granted ${formatDate(u.grantedOn)}</span>
                </div>
                <button type="button" class="fa-row-action fa-user-card__view" data-fa-view-user="${u.uuid}" title="View user">
                    <i data-lucide="eye"></i><span>View Profile</span>
                </button>
                 ${(u.firearmId && window.FA_CAN_UPDATE_FIREARM) ? `<button type="button" class="fa-row-action fa-user-card__view" data-fa-edit-firearm="${u.firearmId}" data-fa-edit-username="${u.username}" title="Edit firearm record">
                    <i data-lucide="pencil"></i><span>Edit Firearm</span>
                </button>` : ""}
            `;
            cardsWrap.appendChild(card);
        });

        refreshIcons();
    }

    
    function wireUserRowNavigation() {
        const tbody = document.getElementById("faUserTableBody");
        const cardsWrap = document.getElementById("faUserCards");
        [tbody, cardsWrap].forEach((wrap) => {
            if (!wrap) return;
            wrap.addEventListener("click", (e) => {
                const trigger = e.target.closest("[data-fa-view-user]");
                if (!trigger) return;
                const uuid = trigger.getAttribute("data-fa-view-user");
                if (!uuid) return;
                window.location.href = `/dashboard/firearm/view/${uuid}/`;
            });
        });
    }


    function wireUserRowEditFirearm() {
        const tbody = document.getElementById("faUserTableBody");
        const cardsWrap = document.getElementById("faUserCards");
        [tbody, cardsWrap].forEach((wrap) => {
            if (!wrap) return;
            wrap.addEventListener("click", (e) => {
                const trigger = e.target.closest("[data-fa-edit-firearm]");
                if (!trigger) return;
                const firearmId = trigger.getAttribute("data-fa-edit-firearm");
                const username = trigger.getAttribute("data-fa-edit-username");
                openEditFirearmForm(firearmId, username);
            });
        });
    }

    

    function wireUserFilters() {

        const searchInput = document.getElementById("faUserSearch");
        const permissionFilter = document.getElementById("faPermissionFilter");

        const permissionUsers = loadPermissionUsers();

        function apply() {

            const keyword = searchInput.value.trim().toLowerCase();
            const permission = permissionFilter.value;

            const filtered = permissionUsers.filter(user => {

                const matchesSearch =
                    !keyword ||
                    user.name.toLowerCase().includes(keyword) ||
                    user.employeeId.toLowerCase().includes(keyword) ||
                    user.department.toLowerCase().includes(keyword) ||
                    user.role.toLowerCase().includes(keyword);

                const matchesPermission =
                    !permission ||
                    user.permission === permission;

                return matchesSearch && matchesPermission;

            });

            renderPermissionUsers(filtered);
        }

        searchInput.addEventListener("input", apply);
        permissionFilter.addEventListener("change", apply);
    }


    function wireQuickActions() {
        document.querySelectorAll(".fa-btn[data-fa-action]").forEach((btn) => {
            btn.addEventListener("click", (e) => spawnRipple(btn, e));
        });
    }

    function spawnRipple(btn, e) {
        const rect = btn.getBoundingClientRect();
        const ripple = document.createElement("span");
        const size = Math.max(rect.width, rect.height);
        ripple.className = "fa-btn__ripple";
        ripple.style.width = ripple.style.height = `${size}px`;
        ripple.style.left = `${(e.clientX ?? rect.left + rect.width / 2) - rect.left - size / 2}px`;
        ripple.style.top = `${(e.clientY ?? rect.top + rect.height / 2) - rect.top - size / 2}px`;
        btn.appendChild(ripple);
        setTimeout(() => ripple.remove(), 650);
    }


    /* =========================================================
       Firearm form 
       ========================================================= */

    const FA_FIELD_RULES = {
        username: { required: true, maxLength: 150 },
        firearm_name: { required: true, maxLength: 150 },
        firearm_type: { required: true, choices: ["HANDGUN", "RIFLE", "SHOTGUN", "TRAINING", "OTHER"] },
        manufacturer: { required: false, maxLength: 150 },
        model_name: { required: false, maxLength: 150 },
        serial_number: { required: true, maxLength: 150 },
        caliber: { required: false, maxLength: 50 },
        purchase_date: { required: false, isDate: true },
        acquisition_method: { required: false, choices: ["PURCHASE", "DONATION", "TRANSFER", "OTHER"] },
        location_name: { required: false, maxLength: 150 },
        building_name: { required: false, maxLength: 150 },
        room_number: { required: false, maxLength: 50 },
        security_level: { required: false, maxLength: 100 },
        current_status: { required: false, choices: ["ACTIVE", "STORED", "RETIRED", "DISPOSED"] },
        notes: { required: false, maxLength: 5000 },
    };

    let faSelectedUsername = "";
    let faUserSearchAbort = null;
    let faUserSearchDebounce = null;

    function getCsrfToken() {
        const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : "";
    }

    function faEndpoint(name) {
        return (window.FA_ENDPOINTS && window.FA_ENDPOINTS[name]) || "";
    }

    function wireAddFirearmFlow() {
        const dashboard = document.getElementById("faDashboardSections");
        const formSection = document.getElementById("faAddFirearmSection");
        const addBtn = document.querySelector('.fa-btn[data-fa-action="add"]');
        const cancelBtn = document.getElementById("faCancelAddFirearm");
        const form = document.getElementById("faAddFirearmForm");

        if (!dashboard || !formSection || !form) return;

        function showForm() {
            dashboard.style.display = "none";
            formSection.style.display = "block";
            formSection.classList.remove("fa-form-section");
            void formSection.offsetWidth; // restart animation
            formSection.classList.add("fa-form-section");
            refreshIcons();
        }

        function showDashboard() {
            formSection.style.display = "none";
            dashboard.style.display = "";
        }

        if (addBtn) {
            addBtn.addEventListener("click", (e) => {
                e.preventDefault();
                resetAddFirearmForm();
                showForm();
            });
        }

        if (cancelBtn) {
            cancelBtn.addEventListener("click", (e) => {
                e.preventDefault();
                resetAddFirearmForm();
                showDashboard();
            });
        }

        wireUserAutocomplete();

        form.addEventListener("submit", (e) => {
            e.preventDefault();
            submitAddFirearmForm(form, showDashboard);
        });
    }

    function resetAddFirearmForm() {
        const form = document.getElementById("faAddFirearmForm");
        if (!form) return;
        form.reset();
        form.dataset.mode = "add";

        const recordIdField = document.getElementById("faFirearmRecordId");
        if (recordIdField) recordIdField.value = "";

        faSelectedUsername = "";
        const hidden = document.getElementById("faUserSearchValue");
        if (hidden) hidden.value = "";
        const searchField = document.getElementById("faUserSearchField");
        if (searchField) {
            searchField.value = "";
            searchField.removeAttribute("readonly");
            searchField.classList.remove("fa-form__input--locked");
        }
        const list = document.getElementById("faUserAutocompleteList");
        if (list) { list.innerHTML = ""; list.hidden = true; }
        clearAllFormErrors(form);

        const titleEl = document.getElementById("faFormHeadTitle");
        if (titleEl) titleEl.textContent = "Add Firearm";
        const subEl = document.getElementById("faFormHeadSub");
        if (subEl) subEl.textContent = "Register a new firearm into the armory registry";

        ["faFirearmType", "faAcquisitionMethod", "faCurrentStatus"].forEach(syncCustomDropdown);
    }

    function clearAllFormErrors(form) {
        form.querySelectorAll(".fa-form__error").forEach((el) => (el.textContent = ""));
        form.querySelectorAll(".fa-form__group.has-error").forEach((el) => el.classList.remove("has-error"));
    }

    function setFieldError(fieldName, message) {
        const errorEl = document.querySelector(`[data-error-for="${fieldName}"]`);
        if (!errorEl) return;
        errorEl.textContent = message || "";
        const group = errorEl.closest(".fa-form__group");
        if (group) group.classList.toggle("has-error", Boolean(message));
    }

    function wireUserAutocomplete() {
        const input = document.getElementById("faUserSearchField");
        const hidden = document.getElementById("faUserSearchValue");
        const list = document.getElementById("faUserAutocompleteList");
        if (!input || !hidden || !list) return;

        input.addEventListener("input", () => {
            faSelectedUsername = "";
            hidden.value = "";
            const term = input.value.trim();
            setFieldError("username", "");

            clearTimeout(faUserSearchDebounce);
            if (!term) {
                list.innerHTML = "";
                list.hidden = true;
                return;
            }

            faUserSearchDebounce = setTimeout(() => runUserSearch(term, input, hidden, list), 250);
        });

        input.addEventListener("blur", () => {
            setTimeout(() => { list.hidden = true; }, 150);
        });

        input.addEventListener("focus", () => {
            if (list.innerHTML && input.value.trim()) list.hidden = false;
        });
    }

    function runUserSearch(term, input, hidden, list) {
        const url = faEndpoint("userSearch");
        if (!url) return;

        if (faUserSearchAbort) faUserSearchAbort.abort();
        faUserSearchAbort = new AbortController();

        list.innerHTML = `<li class="fa-user-autocomplete__loading">Searching...</li>`;
        list.hidden = false;

        fetch(`${url}?q=${encodeURIComponent(term)}`, {
            method: "GET",
            headers: { "X-Requested-With": "XMLHttpRequest" },
            signal: faUserSearchAbort.signal,
        })
            .then((res) => res.json())
            .then((data) => {
                const results = (data && data.results) || [];
                list.innerHTML = "";

                if (results.length === 0) {
                    list.innerHTML = `<li class="fa-user-autocomplete__empty">Username does not exist.</li>`;
                    list.hidden = false;
                    return;
                }

                results.forEach((u) => {
                    const item = document.createElement("li");
                    item.className = "fa-user-autocomplete__item";
                    item.innerHTML = `${u.username}<span>${u.full_name || ""}</span>`;
                    item.addEventListener("mousedown", (e) => {
                        e.preventDefault();
                        input.value = u.username;
                        hidden.value = u.username;
                        faSelectedUsername = u.username;
                        list.hidden = true;
                        setFieldError("username", "");
                    });
                    list.appendChild(item);
                });
                list.hidden = false;
            })
            .catch((err) => {
                if (err && err.name === "AbortError") return;
                list.innerHTML = `<li class="fa-user-autocomplete__empty">Unable to search users right now.</li>`;
                list.hidden = false;
            });
    }

    function validateAddFirearmForm(form) {
        clearAllFormErrors(form);
        let isValid = true;

        const values = {
            username: faSelectedUsername || document.getElementById("faUserSearchValue").value.trim(),
            firearm_name: form.firearm_name.value.trim(),
            firearm_type: form.firearm_type.value,
            manufacturer: form.manufacturer.value.trim(),
            model_name: form.model_name.value.trim(),
            serial_number: form.serial_number.value.trim(),
            caliber: form.caliber.value.trim(),
            purchase_date: form.purchase_date.value,
            acquisition_method: form.acquisition_method.value,
            location_name: form.location_name.value.trim(),
            building_name: form.building_name.value.trim(),
            room_number: form.room_number.value.trim(),
            security_level: form.security_level.value.trim(),
            current_status: form.current_status.value,
            notes: form.notes.value.trim(),
        };

        const usernameTyped = document.getElementById("faUserSearchField").value.trim();
        if (!values.username) {
            setFieldError("username", usernameTyped ? "Username does not exist." : "Please select an existing username.");
            isValid = false;
        }

        Object.keys(FA_FIELD_RULES).forEach((field) => {
            if (field === "username") return;
            const rule = FA_FIELD_RULES[field];
            const value = values[field] || "";

            if (rule.required && !value) {
                setFieldError(field, "This field is required.");
                isValid = false;
                return;
            }
            if (value && rule.maxLength && value.length > rule.maxLength) {
                setFieldError(field, `Must be ${rule.maxLength} characters or fewer.`);
                isValid = false;
                return;
            }
            if (value && rule.choices && !rule.choices.includes(value)) {
                setFieldError(field, "Select a valid option.");
                isValid = false;
                return;
            }
            if (value && rule.isDate) {
                const d = new Date(value);
                const today = new Date();
                today.setHours(23, 59, 59, 999);
                if (isNaN(d.getTime())) {
                    setFieldError(field, "Enter a valid date.");
                    isValid = false;
                } else if (d > today) {
                    setFieldError(field, "Purchase date cannot be in the future.");
                    isValid = false;
                }
            }
        });

        if (values.serial_number && values.serial_number.length < 3) {
            setFieldError("serial_number", "Serial number looks too short.");
            isValid = false;
        }

        return { isValid, values };
    }

    // function submitAddFirearmForm(form, onSuccess) {
    //     const { isValid, values } = validateAddFirearmForm(form);
    //     if (!isValid) {
    //         showToast("Please fix the highlighted fields.", "error");
    //         return;
    //     }

    //     const saveBtn = document.getElementById("faSaveFirearm");
    //     if (saveBtn) saveBtn.disabled = true;

    //     const body = new URLSearchParams();
    //     Object.keys(values).forEach((key) => body.append(key, values[key] ?? ""));
    //     // body.append("is_full_crud", form.is_full_crud.checked ? "on" : "");

    //     const url = faEndpoint("createFirearm");

    //     fetch(url, {
    //         method: "POST",
    //         headers: {
    //             "Content-Type": "application/x-www-form-urlencoded",
    //             "X-Requested-With": "XMLHttpRequest",
    //             "X-CSRFToken": getCsrfToken(),
    //         },
    //         body: body.toString(),
    //     })
    //         .then((res) => res.json().then((data) => ({ status: res.status, data })))
    //         .then(({ status, data }) => {
    //             if (status >= 200 && status < 300 && data && data.ok) {
    //                 showToast(data.message || "Firearm added successfully.", "success");
    //                 resetAddFirearmForm();
    //                 if (typeof onSuccess === "function") onSuccess();
    //                 setTimeout(() => window.location.reload(), 900);
    //             } else {
    //                 const errors = (data && data.errors) || {};
    //                 Object.keys(errors).forEach((field) => setFieldError(field, errors[field]));
    //                 showToast("Please fix the highlighted fields.", "error");
    //             }
    //         })
    //         .catch(() => {
    //             showToast("Something went wrong. Please try again.", "error");
    //         })
    //         .finally(() => {
    //             if (saveBtn) saveBtn.disabled = false;
    //         });
    // }


    function submitAddFirearmForm(form, onSuccess) {
        const { isValid, values } = validateAddFirearmForm(form);
        if (!isValid) {
            showToast("Please fix the highlighted fields.", "error");
            return;
        }

        const saveBtn = document.getElementById("faSaveFirearm");
        if (saveBtn) saveBtn.disabled = true;

        const body = new URLSearchParams();
        Object.keys(values).forEach((key) => body.append(key, values[key] ?? ""));

        const isEdit = form.dataset.mode === "edit";
        const firearmId = document.getElementById("faFirearmRecordId").value;
        const url = isEdit
            ? `${faEndpoint("updateFirearmBase")}${firearmId}/update/`
            : faEndpoint("createFirearm");

        fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": getCsrfToken(),
            },
            body: body.toString(),
        })
            .then((res) => res.json().then((data) => ({ status: res.status, data })))
            .then(({ status, data }) => {
                if (status >= 200 && status < 300 && data && data.ok) {
                    showToast(data.message || (isEdit ? "Firearm updated successfully." : "Firearm added successfully."), "success");
                    resetAddFirearmForm();
                    if (typeof onSuccess === "function") onSuccess();
                    setTimeout(() => window.location.reload(), 900);
                } else {
                    const errors = (data && data.errors) || {};
                    Object.keys(errors).forEach((field) => setFieldError(field, errors[field]));
                    showToast("Please fix the highlighted fields.", "error");
                }
            })
            .catch(() => {
                showToast("Something went wrong. Please try again.", "error");
            })
            .finally(() => {
                if (saveBtn) saveBtn.disabled = false;
            });
    }


   

    let faToastTimer = null;
    function showToast(message, type) {
        const toast = document.getElementById("faToast");
        const iconWrap = document.getElementById("faToastIconWrap");
        const icon = document.getElementById("faToastIcon");
        const title = document.getElementById("faToastTitle");
        const msg = document.getElementById("faToastMsg");
        const closeBtn = document.getElementById("faToastClose");
        if (!toast) return;

        const isSuccess = type !== "error";
        iconWrap.classList.toggle("fa-toast__icon-wrap--success", isSuccess);
        icon.setAttribute("data-lucide", isSuccess ? "check-circle" : "x-circle");
        title.textContent = isSuccess ? "Success" : "Error";
        msg.textContent = message;

        toast.hidden = false;
        toast.classList.remove("hiding");
        refreshIcons();

        if (closeBtn && !closeBtn.dataset.wired) {
            closeBtn.dataset.wired = "true";
            closeBtn.addEventListener("click", () => hideToast(toast));
        }

        clearTimeout(faToastTimer);
        faToastTimer = setTimeout(() => hideToast(toast), 3500);
    }
 
    function hideToast(toast) {
        toast.classList.add("hiding");
        setTimeout(() => { toast.hidden = true; toast.classList.remove("hiding"); }, 250);
    }
})();