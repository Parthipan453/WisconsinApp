// Steve code

document.addEventListener("DOMContentLoaded", () => {

    const form         = document.getElementById("filterForm");
    const searchInput  = document.getElementById("searchInput");
    const selects       = ["semesterSelect", "programSelect", "statusSelect", "electiveSelect"]
        .map(id => document.getElementById(id))
        .filter(Boolean);

    // Auto-apply immediately when a dropdown filter changes
    selects.forEach(select => {
        select.addEventListener("change", () => {
            form.requestSubmit();
        });
    });

    // Debounce the search box so we don't submit on every keystroke
    let debounceTimer;
    searchInput?.addEventListener("input", () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            form.requestSubmit();
        }, 500);
    });



    const statusModal = document.getElementById("statusModal");
    if (statusModal) {
        statusModal.addEventListener("show.bs.modal", event => {
            const btn    = event.relatedTarget;
            const url    = btn.dataset.url;
            const name   = btn.dataset.name;
            const action = btn.dataset.action;

            const msg  = document.getElementById("statusMessage");
            const conf = document.getElementById("confirmStatusBtn");

            if (action === "deactivate") {
                msg.innerHTML  = `Are you sure you want to <strong>deactivate</strong> <em>${name}</em>?`;
                conf.className = "btn-confirm btn-confirm-danger";
            } else {
                msg.innerHTML  = `Are you sure you want to <strong>activate</strong> <em>${name}</em>?`;
                conf.className = "btn-confirm btn-confirm-success";
            }

            conf.href = url;
        });
    }

});


document.addEventListener("DOMContentLoaded", function () {

    document.querySelectorAll("select.pc-filter-select").forEach(function (select) {

        new Choices(select, {
            searchEnabled: true,
            shouldSort: false,
            itemSelectText: "",
            allowHTML: false,
        });

    });

});


document.addEventListener("DOMContentLoaded", () => {

    const groupHeaders = document.querySelectorAll(".pc-group-header");
    const expandAllBtn = document.getElementById("expandAllBtn");

    function setExpanded(card, content, expand) {
        card.classList.toggle("expanded", expand);
        content.style.maxHeight = expand ? content.scrollHeight + "px" : "0px";
    }

    groupHeaders.forEach(header => {
        const card = header.closest(".pc-group-card");
        const content = document.getElementById(header.dataset.target);
        if (!content) return;

        header.addEventListener("click", () => {
            const isExpanded = card.classList.contains("expanded");
            setExpanded(card, content, !isExpanded);
        });
    });

    let allExpanded = false;
    expandAllBtn?.addEventListener("click", () => {
        allExpanded = !allExpanded;
        groupHeaders.forEach(header => {
            const card = header.closest(".pc-group-card");
            const content = document.getElementById(header.dataset.target);
            if (content) setExpanded(card, content, allExpanded);
        });
        expandAllBtn.textContent = allExpanded ? "Collapse All" : "Expand All";
    });

});