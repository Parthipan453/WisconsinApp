(function () {
    "use strict";

    const root = document.querySelector(".pp");
    if (!root) return;

    const listUrl = root.dataset.listUrl;
    const tableContainer = document.getElementById("ppTableContainer");
    const searchInput = document.getElementById("ppSearchInput");
    const typeFilter = document.getElementById("ppTypeFilter");
    const bloodFilter = document.getElementById("ppBloodFilter");
    const sortBy = document.getElementById("ppSortBy");
    const resetBtn = document.getElementById("ppResetFilters");

    const statTotal = document.getElementById("statTotal");

    let debounceTimer = null;
    let activeController = null;

    function currentPageNumber() {
        const paginationEl = tableContainer.querySelector(".pp__pagination");
        return paginationEl ? paginationEl.dataset.currentPage : "1";
    }

    function buildParams(page) {
        const params = new URLSearchParams();
        if (searchInput.value.trim()) params.set("search", searchInput.value.trim());
        if (typeFilter.value) params.set("patient_type", typeFilter.value);
        if (bloodFilter.value) params.set("blood_group", bloodFilter.value);
        if (sortBy.value) params.set("sort", sortBy.value);
        params.set("page", page || "1");
        return params;
    }

    async function refreshTable(page) {
        const params = buildParams(page);
        const url = `${listUrl}?${params.toString()}`;

        // Cancel any in-flight request so fast typing doesn't race itself.
        if (activeController) activeController.abort();
        activeController = new AbortController();

        const tableWrap = tableContainer.querySelector(".pp__table-wrap");
        if (tableWrap) tableWrap.classList.add("is-loading");

        try {
            const response = await fetch(url, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
                signal: activeController.signal,
            });
            if (!response.ok) throw new Error(`Request failed: ${response.status}`);

            const data = await response.json();
            tableContainer.innerHTML = data.html;

            // Re-render Lucide icons
            if (window.lucide && typeof window.lucide.createIcons === "function") {
                window.lucide.createIcons();
            }

            // Refresh AOS for newly injected table & pagination
            if (window.AOS) {
                AOS.refreshHard();
            }

            // Update browser URL
            window.history.replaceState(
                null,
                "",
                `${window.location.pathname}?${params.toString()}`
            );
        } catch (err) {
            if (err.name !== "AbortError") {
                console.error("Failed to refresh patient list:", err);
            }
        }
    }

    function scheduleRefresh() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => refreshTable(1), 300);
    }

    // ---- Search (debounced) ----
    searchInput.addEventListener("input", scheduleRefresh);

    // ---- Filters / sort (instant) ----
    [typeFilter, bloodFilter, sortBy].forEach((el) => {
        el.addEventListener("change", () => refreshTable(1));
    });

    // ---- Reset ----
    // resetBtn.addEventListener("click", () => {
    //     searchInput.value = "";
    //     typeFilter.selectedIndex = 0;
    //     bloodFilter.selectedIndex = 0;
    //     sortBy.value = "recent";
    //     refreshTable(1);
    // });
    resetBtn.addEventListener("click", () => {

        searchInput.value = "";

        if (window.choicesMap) {

            window.choicesMap["ppTypeFilter"]?.setChoiceByValue("");

            window.choicesMap["ppBloodFilter"]?.setChoiceByValue("");

            window.choicesMap["ppSortBy"]?.setChoiceByValue("recent");

        } else {

            typeFilter.selectedIndex = 0;
            bloodFilter.selectedIndex = 0;
            sortBy.value = "recent";

        }

        refreshTable(1);

    });

    // ---- Pagination + view button (event delegation, since table is replaced) ----
    tableContainer.addEventListener("click", (event) => {
        const pageBtn = event.target.closest(".pp__page-btn");
        if (pageBtn && !pageBtn.disabled) {
            refreshTable(pageBtn.dataset.page);
            return;
        }

        const viewBtn = event.target.closest(".pp__view-btn");
        if (viewBtn) {
            openPatientDetail(viewBtn.dataset.patientId);
        }
    });

    // ---- Detail modal ----
    const modal = document.getElementById("ppDetailModal");
    const modalBody = document.getElementById("ppModalBody");
    const modalClose = document.getElementById("ppModalClose");
    const modalBackdrop = document.getElementById("ppModalBackdrop");

    function fieldRow(label, value, full) {
        return `
            <div class="pp-modal__field${full ? " pp-modal__field--full" : ""}">
                <span class="pp-modal__label">${label}</span>
                <span class="pp-modal__value">${value || "-"}</span>
            </div>`;
    }

    async function openPatientDetail(patientId) {
        if (!patientId) return;
        modalBody.innerHTML = `<div class="pp-modal__field pp-modal__field--full">Loading…</div>`;
        modal.hidden = false;

        try {
            const response = await fetch(`${listUrl}${patientId}/`, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            if (!response.ok) throw new Error(`Request failed: ${response.status}`);
            const data = await response.json();

            modalBody.innerHTML = [
                fieldRow("Patient No", data.patient_number),
                fieldRow("Name", data.name),
                fieldRow("Type", data.patient_type),
                fieldRow("Blood Group", data.blood_group),
                fieldRow("Phone", data.phone),
                fieldRow("Last Visit", data.last_visit || "No visits yet"),
                fieldRow("Reason (last visit)", data.last_visit_reason, true),
                fieldRow("Allergies", data.allergies, true),
                fieldRow("Chronic Conditions", data.chronic_conditions, true),
                fieldRow("Emergency Contact", `${data.emergency_contact_name} (${data.emergency_contact_phone})`, true),
                fieldRow("Remarks", data.remarks, true),
            ].join("");
        } catch (err) {
            modalBody.innerHTML = `<div class="pp-modal__field pp-modal__field--full">Couldn't load patient details.</div>`;
            console.error(err);
        }
    }

    function closeModal() {
        modal.hidden = true;
    }

    modalClose.addEventListener("click", closeModal);
    modalBackdrop.addEventListener("click", closeModal);
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && !modal.hidden) closeModal();
    });

    // ---- Register Patient button (wire to your existing registration flow) ----
    const registerBtn = document.getElementById("registerPatientBtn");
    if (registerBtn) {
        registerBtn.addEventListener("click", () => {
            // Replace with your actual register-patient URL/modal.
            console.log("Open register-patient flow here.");
        });
    }
})();