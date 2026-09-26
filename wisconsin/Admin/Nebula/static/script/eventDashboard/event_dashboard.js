document.addEventListener("DOMContentLoaded", () => {
    // -------------------------------------------------------------
    // 1. Initialize Flatpickr for Date Inputs
    // -------------------------------------------------------------
    const fpInstances = flatpickr(".date-picker", {
        dateFormat: "Y-m-d",
        allowInput: false,
        disableMobile: true,
        position: "auto center",
        monthSelectorType: "static",
        onReady(_, __, instance) {
            if (instance && instance.currentYearElement) {
                instance.currentYearElement.readOnly = true;
            }
        },
    });

    const fromInput = document.getElementById("filterFromDate");
    const toInput = document.getElementById("filterToDate");
    [fromInput, toInput].forEach((input) => {
        if (input) {
            input.addEventListener("keydown", (e) => e.preventDefault());
        }
    });

    // -------------------------------------------------------------
    // 2. Initialize Choices.js for Select Dropdowns
    // -------------------------------------------------------------
    const choicesInstances = [];
    document.querySelectorAll(".ev-filters select").forEach((select) => {
        const enableSearch = select.options.length > 5;
        const choice = new Choices(select, {
            searchEnabled: enableSearch,
            shouldSort: false,
            position: "auto",
            itemSelectText: "",
        });
        choicesInstances.push(choice);
    });


    // -------------------------------------------------------------
    // 3. DOM Elements References
    // -------------------------------------------------------------
    const evFilters = document.getElementById("evFilters");
    const filterCategory = document.getElementById("filterCategory");
    const filterStatus = document.getElementById("filterStatus");
    const filterVisibility = document.getElementById("filterVisibility");
    const filterSearch = document.getElementById("filterSearch");
    const btnApplyFilter = document.getElementById("btnApplyFilter");
    const btnResetFilter = document.getElementById("btnResetFilter");

    // Expand filter section on page load if filters are pre-selected
    const hasActiveFilters = Boolean(
        (filterCategory && filterCategory.value.trim()) ||
        (filterStatus && filterStatus.value.trim()) ||
        (filterVisibility && filterVisibility.value.trim()) ||
        (fromInput && fromInput.value.trim()) ||
        (toInput && toInput.value.trim())
    );

    let isAnimating = false;

    function slideDown(element, duration = 300) {
        if (isAnimating) return;
        isAnimating = true;

        element.classList.add("is-visible");
        element.style.display = "grid";

        const fullHeight = element.scrollHeight;
        const computedStyle = window.getComputedStyle(element);
        const paddingTop = computedStyle.paddingTop || "18px";
        const paddingBottom = computedStyle.paddingBottom || "18px";

        element.style.overflow = "hidden";
        element.style.maxHeight = "0px";
        element.style.opacity = "0";
        element.style.paddingTop = "0px";
        element.style.paddingBottom = "0px";
        element.style.transition = `max-height ${duration}ms cubic-bezier(0.4, 0, 0.2, 1), opacity ${duration}ms cubic-bezier(0.4, 0, 0.2, 1), padding ${duration}ms cubic-bezier(0.4, 0, 0.2, 1)`;

        element.offsetHeight; // Force reflow

        element.style.maxHeight = fullHeight + "px";
        element.style.opacity = "1";
        element.style.paddingTop = paddingTop;
        element.style.paddingBottom = paddingBottom;

        setTimeout(() => {
            element.style.removeProperty("max-height");
            element.style.removeProperty("opacity");
            element.style.removeProperty("overflow");
            element.style.removeProperty("padding-top");
            element.style.removeProperty("padding-bottom");
            element.style.removeProperty("transition");
            isAnimating = false;
        }, duration);
    }

    function slideUp(element, duration = 300) {
        if (isAnimating) return;
        isAnimating = true;

        const fullHeight = element.scrollHeight;
        element.style.overflow = "hidden";
        element.style.maxHeight = fullHeight + "px";
        element.style.opacity = "1";
        element.style.transition = `max-height ${duration}ms cubic-bezier(0.4, 0, 0.2, 1), opacity ${duration}ms cubic-bezier(0.4, 0, 0.2, 1), padding ${duration}ms cubic-bezier(0.4, 0, 0.2, 1)`;

        element.offsetHeight; // Force reflow

        element.style.maxHeight = "0px";
        element.style.opacity = "0";
        element.style.paddingTop = "0px";
        element.style.paddingBottom = "0px";

        setTimeout(() => {
            element.classList.remove("is-visible");
            element.style.display = "none";
            element.style.removeProperty("max-height");
            element.style.removeProperty("opacity");
            element.style.removeProperty("overflow");
            element.style.removeProperty("padding-top");
            element.style.removeProperty("padding-bottom");
            element.style.removeProperty("transition");
            isAnimating = false;
        }, duration);
    }

    if (hasActiveFilters && evFilters) {
        evFilters.classList.add("is-visible");
        if (btnApplyFilter) btnApplyFilter.classList.add("active");
    }

    let searchTimeout = null;

    // -------------------------------------------------------------
    // 4. AJAX Filtering Routine
    // -------------------------------------------------------------
    async function performAjaxFilter(page = 1) {
        const url = new URL(window.location.href);

        const categoryVal = filterCategory ? filterCategory.value.trim() : "";
        const statusVal = filterStatus ? filterStatus.value.trim() : "";
        const visibilityVal = filterVisibility ? filterVisibility.value.trim() : "";
        const fromDateVal = fromInput ? fromInput.value.trim() : "";
        const toDateVal = toInput ? toInput.value.trim() : "";
        const searchVal = filterSearch ? filterSearch.value.trim() : "";

        if (categoryVal) url.searchParams.set("category", categoryVal);
        else url.searchParams.delete("category");

        if (statusVal) url.searchParams.set("status", statusVal);
        else url.searchParams.delete("status");

        if (visibilityVal) url.searchParams.set("visibility", visibilityVal);
        else url.searchParams.delete("visibility");

        if (fromDateVal) url.searchParams.set("from_date", fromDateVal);
        else url.searchParams.delete("from_date");

        if (toDateVal) url.searchParams.set("to_date", toDateVal);
        else url.searchParams.delete("to_date");

        if (searchVal) url.searchParams.set("search", searchVal);
        else url.searchParams.delete("search");

        if (page && page > 1) url.searchParams.set("page", page);
        else url.searchParams.delete("page");

        try {
            const response = await fetch(url.toString(), {
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });

            if (!response.ok) return;

            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, "text/html");

            // Update Table View
            const newTable = doc.getElementById("tableView");
            const currentTable = document.getElementById("tableView");
            if (newTable && currentTable) {
                currentTable.innerHTML = newTable.innerHTML;
            }

            // Update Result Count
            const newCount = doc.getElementById("evResultCount");
            const currentCount = document.getElementById("evResultCount");
            if (newCount && currentCount) {
                currentCount.innerHTML = newCount.innerHTML;
            }

            // Update Pagination
            const newPagination = doc.getElementById("evPagination");
            const currentPagination = document.getElementById("evPagination");
            if (newPagination && currentPagination) {
                currentPagination.innerHTML = newPagination.innerHTML;
                attachPaginationListeners();
            }

            // Update URL without page refresh
            window.history.pushState({}, "", url.toString());
        } catch (err) {
            console.error("AJAX filter request failed:", err);
        }
    }

    // -------------------------------------------------------------
    // 5. Intercept Pagination Clicks for AJAX Navigation
    // -------------------------------------------------------------
    function attachPaginationListeners() {
        const paginationContainer = document.getElementById("evPagination");
        if (!paginationContainer) return;

        const links = paginationContainer.querySelectorAll("a");
        links.forEach((link) => {
            link.addEventListener("click", (e) => {
                e.preventDefault();
                const linkUrl = new URL(link.href);
                const pageParam = linkUrl.searchParams.get("page") || 1;
                performAjaxFilter(pageParam);
            });
        });
    }

    // -------------------------------------------------------------
    // 6. Bind Event Listeners on Filter Controls
    // -------------------------------------------------------------
    [filterCategory, filterStatus, filterVisibility].forEach((select) => {
        if (select) {
            select.addEventListener("change", () => performAjaxFilter(1));
        }
    });

    [fromInput, toInput].forEach((input) => {
        if (input) {
            input.addEventListener("change", () => performAjaxFilter(1));
        }
    });

    if (filterSearch) {
        filterSearch.addEventListener("input", () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performAjaxFilter(1);
            }, 300);
        });

        filterSearch.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                clearTimeout(searchTimeout);
                performAjaxFilter(1);
            }
        });
    }

    if (btnApplyFilter) {
        btnApplyFilter.addEventListener("click", (e) => {
            e.preventDefault();
            if (evFilters) {
                const isCurrentlyVisible = window.getComputedStyle(evFilters).display !== "none";
                if (!isCurrentlyVisible) {
                    btnApplyFilter.classList.add("active");
                    slideDown(evFilters, 300);
                } else {
                    btnApplyFilter.classList.remove("active");
                    slideUp(evFilters, 300);
                }
            }
        });
    }

    if (btnResetFilter) {
        btnResetFilter.addEventListener("click", (e) => {
            e.preventDefault();

            // Clear choices instances
            choicesInstances.forEach((choice) => {
                if (choice && typeof choice.setChoiceByValue === "function") {
                    choice.setChoiceByValue("");
                }
            });

            // Clear flatpickr date pickers
            if (Array.isArray(fpInstances)) {
                fpInstances.forEach((fp) => fp.clear());
            } else if (fpInstances && typeof fpInstances.clear === "function") {
                fpInstances.clear();
            }

            if (fromInput) fromInput.value = "";
            if (toInput) toInput.value = "";
            if (filterSearch) filterSearch.value = "";

            // Re-fetch default list via AJAX
            performAjaxFilter(1);
        });
    }

    // -------------------------------------------------------------
    // 7. Event Action Confirmation Modal (Publish, Unpublish, Cancel)
    // -------------------------------------------------------------
    const eventStatusModalEl = document.getElementById("eventStatusModal");
    let statusModalInstance = null;

    function getModalInstance() {
        if (!statusModalInstance && eventStatusModalEl && typeof bootstrap !== "undefined") {
            statusModalInstance = new bootstrap.Modal(eventStatusModalEl);
        }
        return statusModalInstance;
    }

    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    document.addEventListener("click", (e) => {
        const actionBtn = e.target.closest(".btn-event-action");
        if (!actionBtn) return;

        e.preventDefault();

        const eventId = actionBtn.getAttribute("data-event-id");
        const eventTitle = actionBtn.getAttribute("data-event-title") || "this event";
        const action = actionBtn.getAttribute("data-action");

        const modalEventIdInput = document.getElementById("statusModalEventId");
        const modalActionInput = document.getElementById("statusModalAction");
        const modalTitle = document.getElementById("eventStatusModalTitle");
        const modalMessage = document.getElementById("eventStatusModalMessage");
        const modalConfirmText = document.getElementById("statusModalConfirmText");
        const modalConfirmIcon = document.getElementById("statusModalConfirmIcon");

        if (modalEventIdInput) modalEventIdInput.value = eventId;
        if (modalActionInput) modalActionInput.value = action;

        if (action === "publish") {
            if (modalTitle) modalTitle.textContent = "Publish Event";
            if (modalMessage) {
                modalMessage.innerHTML = `Are you sure you want to publish <strong>${escapeHtml(eventTitle)}</strong>?`;
            }
            if (modalConfirmText) modalConfirmText.textContent = "Publish Event";
            if (modalConfirmIcon) modalConfirmIcon.className = "ti ti-world";
        } else if (action === "unpublish") {
            if (modalTitle) modalTitle.textContent = "Unpublish Event";
            if (modalMessage) {
                modalMessage.innerHTML = `Are you sure you want to unpublish <strong>${escapeHtml(eventTitle)}</strong>?`;
            }
            if (modalConfirmText) modalConfirmText.textContent = "Unpublish Event";
            if (modalConfirmIcon) modalConfirmIcon.className = "ti ti-world-off";
        } else if (action === "cancel") {
            if (modalTitle) modalTitle.textContent = "Cancel Event";
            if (modalMessage) {
                modalMessage.innerHTML = `Are you sure you want to cancel <strong>${escapeHtml(eventTitle)}</strong>?`;
            }
            if (modalConfirmText) modalConfirmText.textContent = "Cancel Event";
            if (modalConfirmIcon) modalConfirmIcon.className = "ti ti-ban";
        } else if (action === "complete") {
            if (modalTitle) modalTitle.textContent = "Complete Event";
            if (modalMessage) {
                modalMessage.innerHTML = `Are you sure you want to mark <strong>${escapeHtml(eventTitle)}</strong> as completed?`;
            }
            if (modalConfirmText) modalConfirmText.textContent = "Mark as Completed";
            if (modalConfirmIcon) modalConfirmIcon.className = "ti ti-circle-check";
        }

        const modalInst = getModalInstance();
        if (modalInst) {
            modalInst.show();
        } else if (eventStatusModalEl && typeof bootstrap !== "undefined") {
            const tempModal = new bootstrap.Modal(eventStatusModalEl);
            tempModal.show();
        }
    });

    // Initial listener binding
    attachPaginationListeners();
});

