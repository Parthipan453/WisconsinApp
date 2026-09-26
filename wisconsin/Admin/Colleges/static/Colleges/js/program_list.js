// Steve code

document.addEventListener("DOMContentLoaded", () => {

    const searchInput = document.getElementById("programSearch");
    const rows = document.querySelectorAll(".prog-row");

    function filterRows() {
        const q = searchInput.value.trim().toLowerCase();
        const status = document.querySelector(".status-pill.active")?.dataset.status || "ALL";
        const type = document.querySelector(".type-pill.active")?.dataset.type || "ALL";

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const rowStatus = row.dataset.status || "";
            const rowType = row.dataset.type || "";
            
            const matchQ = !q || text.includes(q);
            const matchStatus = status === "ALL" || rowStatus === status;
            const matchType = type === "ALL" || rowType === type;
            
            row.classList.toggle("hidden", !(matchQ && matchStatus && matchType));
        });

        updateEmpty();
    }

    function updateEmpty() {

        const tbody = document.querySelector("#programTable tbody");

        // Total actual program rows
        const totalRows = tbody.querySelectorAll(".prog-row").length;

        // If there are no program rows in DB,
        // Django {% empty %} is already showing.
        if (totalRows === 0) return;

        const visible = tbody.querySelectorAll(".prog-row:not(.hidden)").length;

        let emptyRow = tbody.querySelector(".js-empty-row");

        if (visible === 0) {

            if (!emptyRow) {

                emptyRow = document.createElement("tr");
                emptyRow.className = "js-empty-row";

                emptyRow.innerHTML = `
                    <td colspan="10">
                        <div class="empty-state">
    
                            <h5>No Programs Found</h5>
                            <p>No results match your search. Try different keywords or reset the filter.</p>
                        </div>
                    </td>
                `;

                tbody.appendChild(emptyRow);
            }

        } else {

            if (emptyRow) {
                emptyRow.remove();
            }

        }
    }

    // Search input
    searchInput?.addEventListener("input", filterRows);

    // Status pills
    document.querySelectorAll(".status-pill").forEach(pill => {
        pill.addEventListener("click", () => {
            document.querySelectorAll(".status-pill").forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            filterRows();
        });
    });

    // Type pills
    document.querySelectorAll(".type-pill").forEach(pill => {
        pill.addEventListener("click", () => {
            document.querySelectorAll(".type-pill").forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            filterRows();
        });
    });

    // Reset button
    document.getElementById("resetSearch")?.addEventListener("click", () => {
        searchInput.value = "";
        
        document.querySelectorAll(".status-pill").forEach(p => p.classList.remove("active"));
        document.querySelector('.status-pill[data-status="ALL"]')?.classList.add("active");
        
        document.querySelectorAll(".type-pill").forEach(p => p.classList.remove("active"));
        document.querySelector('.type-pill[data-type="ALL"]')?.classList.add("active");
        
        rows.forEach(r => r.classList.remove("hidden"));
        const emptyRow = document.querySelector(".js-empty-row");
        if (emptyRow) emptyRow.remove();
    });

    // Status modal
    const statusModal = document.getElementById("statusModal");
    if (statusModal) {
        statusModal.addEventListener("show.bs.modal", event => {
            const btn = event.relatedTarget;
            const url = btn.dataset.url;
            const name = btn.dataset.name;
            const action = btn.dataset.action;

            const msg = document.getElementById("statusMessage");
            const conf = document.getElementById("confirmStatusBtn");

            if (action === "deactivate") {
                msg.innerHTML = `Are you sure you want to <strong>deactivate</strong> <em>${name}</em>?`;
                conf.className = "btn-confirm btn-confirm-danger";
            } else {
                msg.innerHTML = `Are you sure you want to <strong>activate</strong> <em>${name}</em>?`;
                conf.className = "btn-confirm btn-confirm-success";
            }

            conf.href = url;
        });
    }

});


