(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        if (window.lucide) lucide.createIcons();
        animateStatNumbers();
        renderBannerDate();
        renderCharts();
        initCustomSelects();
        setupModalSearches();
        maybeOpenRoleModal();
    });

    document.addEventListener("shown.bs.modal", function (e) {
        initCustomSelects(e.target);
    });

    function animateStatNumbers() {
        document.querySelectorAll(".med-stat-number[data-count]").forEach(function (el) {
            var target = parseInt(el.getAttribute("data-count"), 10) || 0;
            var duration = 900;
            var startTime = null;

            function step(timestamp) {
                if (!startTime) startTime = timestamp;
                var progress = Math.min((timestamp -  startTime) / duration, 1);
                var eased = 1 - Math.pow(1 - progress, 3);
                el.textContent = Math.round(eased * target);
                if (progress < 1) requestAnimationFrame(step);
                else el.textContent = target;
            }
            requestAnimationFrame(step);
        });
    }

    function renderBannerDate() {
        var el = document.getElementById("medBannerDate");
        if (!el) return;
        var today = new Date();
        var formatted = today.toLocaleDateString(undefined, {
            weekday: "long", year: "numeric", month: "long", day: "numeric"
        });
        el.innerHTML = '<i data-lucide="calendar"></i> ' + formatted;
        if (window.lucide) lucide.createIcons();
    }

    function renderCharts() {
        if (!window.Chart || !window.medDashboardData) return;
        var data = window.medDashboardData;

        var palette = ["#c5050c", "#e0171f", "#f2848a", "#8f0308", "#f4a3a7", "#6c757d"];

        var roleCanvas = document.getElementById("medRoleChart");
        if (roleCanvas && data.roleLabels && data.roleLabels.length) {
            new Chart(roleCanvas, {
                type: "doughnut",
                data: {
                    labels: data.roleLabels,
                    datasets: [{
                        data: data.roleValues,
                        backgroundColor: palette,
                        borderWidth: 0,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: "bottom", labels: { boxWidth: 10, font: { size: 11 } } },
                    },
                },
            });
        }

        var employmentCanvas = document.getElementById("medEmploymentChart");
        if (employmentCanvas && data.employmentLabels && data.employmentLabels.length) {
            new Chart(employmentCanvas, {
                type: "bar",
                data: {
                    labels: data.employmentLabels,
                    datasets: [{
                        label: "Staff",
                        data: data.employmentValues,
                        backgroundColor: "#c5050c",
                        borderRadius: 6,
                        maxBarThickness: 42,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, ticks: { precision: 0 } },
                    },
                },
            });
        }

        var trendCanvas = document.getElementById("medHiringTrendChart");
        if (trendCanvas && data.monthLabels && data.monthLabels.length) {
            new Chart(trendCanvas, {
                type: "line",
                data: {
                    labels: data.monthLabels,
                    datasets: [{
                        label: "New Staff",
                        data: data.monthCounts,
                        borderColor: "#c5050c",
                        backgroundColor: "rgba(197, 5, 12, 0.12)",
                        tension: 0.35,
                        fill: true,
                        pointRadius: 4,
                        pointBackgroundColor: "#c5050c",
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, ticks: { precision: 0 } },
                    },
                },
            });
        }
    }

    function initCustomSelects(scope) {
        var root = scope || document;
        var CATEGORY_ICONS = {
            DOCTOR: "stethoscope",
            NURSE: "heart-handshake",
            PHYSIO: "activity",
            LAB: "flask-conical",
            PHARMACY: "pill",
            FRONT_DESK: "badge-info"
        };
        root.querySelectorAll("select:not([data-custom-enhanced])").forEach(function (select) {
            buildCustomSelect(select, CATEGORY_ICONS);
        });
    }

    function buildCustomSelect(select, iconMap) {
        select.setAttribute("data-custom-enhanced", "true");
        select.classList.add("med-visually-hidden");
        select.setAttribute("tabindex", "-1");
        select.setAttribute("aria-hidden", "true");

        var wrapper = document.createElement("div");
        wrapper.className = "med-custom-select";

        var trigger = document.createElement("button");
        trigger.type = "button";
        trigger.className = "med-custom-select__trigger";
        trigger.setAttribute("aria-haspopup", "listbox");
        trigger.setAttribute("aria-expanded", "false");

        var iconWrap = document.createElement("span");
        iconWrap.className = "med-custom-select__avatar";
        iconWrap.innerHTML = '<i data-lucide="tag"></i>';

        var label = document.createElement("span");
        label.className = "med-custom-select__label";
        label.textContent = "Select an option";

        var chevron = document.createElement("span");
        chevron.className = "med-custom-select__chevron";
        chevron.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>';

        trigger.appendChild(iconWrap);
        trigger.appendChild(label);
        trigger.appendChild(chevron);

        var parentModal = select.closest(".modal");
        var panelHost = parentModal || document.body;

        var panel = document.createElement("div");
        panel.className = "med-custom-select__panel med-custom-select__panel--floating";
        panel.style.position = "fixed";
        panel.style.display = "none";
        panel.style.zIndex = "3000";

        var searchWrap = document.createElement("div");
        searchWrap.className = "med-custom-select__search";
        searchWrap.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>';
        var searchInput = document.createElement("input");
        searchInput.type = "text";
        searchInput.placeholder = "Search...";
        searchWrap.appendChild(searchInput);

        var list = document.createElement("ul");
        list.className = "med-custom-select__list";
        list.setAttribute("role", "listbox");

        var allOptions = Array.prototype.slice.call(select.options);
        var placeholderOption = allOptions.find(function (o) { return o.value === ""; });
        var options = allOptions.filter(function (o) { return o.value !== ""; });
        if (placeholderOption) label.textContent = placeholderOption.text;

        function renderList(filterText) {
            list.innerHTML = "";
            var filtered = options.filter(function (o) {
                return !filterText || o.text.toLowerCase().indexOf(filterText.toLowerCase()) !== -1;
            });
            if (!filtered.length) {
                var empty = document.createElement("li");
                empty.className = "med-custom-select__empty";
                empty.textContent = "No matches found";
                list.appendChild(empty);
                return;
            }
            filtered.forEach(function (opt) {
                var item = document.createElement("li");
                item.className = "med-custom-select__item";
                item.setAttribute("role", "option");
                item.tabIndex = 0;

                var itemIcon = document.createElement("span");
                itemIcon.className = "med-custom-select__item-avatar";
                var iconName = (iconMap && iconMap[opt.value]) || "tag";
                itemIcon.innerHTML = '<i data-lucide="' + iconName + '"></i>';

                var info = document.createElement("div");
                info.className = "med-custom-select__item-info";
                var strong = document.createElement("strong");
                strong.textContent = opt.text;
                info.appendChild(strong);

                item.appendChild(itemIcon);
                item.appendChild(info);

                item.addEventListener("click", function () { selectOption(opt); });
                item.addEventListener("keydown", function (e) {
                    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); selectOption(opt); }
                });

                list.appendChild(item);
            });
            if (window.lucide) lucide.createIcons();
        }

        function selectOption(opt) {
            select.value = opt.value;
            label.textContent = opt.text;
            label.classList.add("med-custom-select__label--filled");
            select.dispatchEvent(new Event("change", { bubbles: true }));
            closePanel();
            trigger.focus();
        }

        function positionPanel() {
            var rect = trigger.getBoundingClientRect();
            panel.style.left = rect.left + "px";
            panel.style.width = rect.width + "px";
            panel.style.top = (rect.bottom + 8) + "px";
            panel.style.maxHeight = "300px";

            var panelHeight = panel.offsetHeight;
            var spaceBelow = window.innerHeight - rect.bottom;
            if (spaceBelow < panelHeight + 16 && rect.top > panelHeight + 16) {
                panel.style.top = (rect.top - panelHeight - 8) + "px";
            }
        }

        function openPanel() {
            panel.style.display = "flex";
            wrapper.classList.add("med-custom-select--open");
            trigger.setAttribute("aria-expanded", "true");
            searchInput.value = "";
            renderList("");
            positionPanel();
            setTimeout(function () { searchInput.focus(); positionPanel(); }, 30);
            document.addEventListener("click", outsideClick, true);
            document.addEventListener("scroll", onReposition, true);
            window.addEventListener("resize", onReposition);
        }

        function closePanel() {
            panel.style.display = "none";
            wrapper.classList.remove("med-custom-select--open");
            trigger.setAttribute("aria-expanded", "false");
            document.removeEventListener("click", outsideClick, true);
            document.removeEventListener("scroll", onReposition, true);
            window.removeEventListener("resize", onReposition);
        }

        function onReposition() {
            if (panel.style.display !== "none") positionPanel();
        }

        function outsideClick(e) {
            if (!wrapper.contains(e.target) && !panel.contains(e.target)) closePanel();
        }

        trigger.addEventListener("click", function () {
            panel.style.display !== "none" ? closePanel() : openPanel();
        });
        trigger.addEventListener("keydown", function (e) {
            if (e.key === "Escape") closePanel();
            if (e.key === "ArrowDown") { e.preventDefault(); openPanel(); }
        });
        searchInput.addEventListener("input", function () { renderList(this.value); });

        panel.appendChild(searchWrap);
        panel.appendChild(list);
        wrapper.appendChild(trigger);
        panelHost.appendChild(panel);
        select.insertAdjacentElement("afterend", wrapper);

        if (parentModal) {
            parentModal.addEventListener("hidden.bs.modal", closePanel);
        }

        if (select.value) {
            var current = options.find(function (o) { return o.value === select.value; });
            if (current) {
                label.textContent = current.text;
                label.classList.add("med-custom-select__label--filled");
            }
        }
    }

    function setupModalSearch(inputId, gridId, emptyMsgId, cardSelector, matchAttr) {
        var input = document.getElementById(inputId);
        var grid = document.getElementById(gridId);
        var emptyMsg = document.getElementById(emptyMsgId);
        if (!input || !grid) return;

        input.addEventListener("input", function () {
            var query = this.value.trim().toLowerCase();
            var cards = grid.querySelectorAll(cardSelector);
            var visibleCount = 0;

            cards.forEach(function (card) {
                var haystack = card.getAttribute(matchAttr) || "";
                var isMatch = haystack.indexOf(query) !== -1;
                card.style.display = isMatch ? "" : "none";
                if (isMatch) visibleCount++;
            });

            if (emptyMsg) {
                emptyMsg.classList.toggle("d-none", visibleCount !== 0);
            }
        });
    }

    function setupModalSearches() {
        setupModalSearch("staffModalSearch", "staffModalGrid", "staffModalEmptyMsg", ".med-staff-card", "data-staff-search");
        setupModalSearch("deptModalSearch", "deptModalGrid", "deptModalEmptyMsg", ".med-dept-card", "data-dept-name");
    }

    function maybeOpenRoleModal() {
        var dashboardRoot = document.getElementById("medDashboardRoot");
        if (!dashboardRoot || dashboardRoot.getAttribute("data-open-role-modal") !== "true") return;

        var modalEl = document.getElementById("manageRolesModal");
        if (modalEl && window.bootstrap) { new bootstrap.Modal(modalEl).show(); }
    }
})();