// Steve code

document.addEventListener("DOMContentLoaded", () => {


    const searchInput = document.getElementById("degreeSearch");
    const rows        = document.querySelectorAll(".deg-row");

    function filterRows() {
        const q     = searchInput.value.trim().toLowerCase();
        const level = document.querySelector(".level-pill.active")?.dataset.level || "ALL";

        rows.forEach(row => {
            const text      = row.textContent.toLowerCase();
            const rowLevel  = row.dataset.level || "";
            const matchQ    = !q || text.includes(q);
            const matchLvl  = level === "ALL" || rowLevel === level;
            row.classList.toggle("hidden", !(matchQ && matchLvl));
        });

        updateEmpty();
    }

    function updateEmpty() {

        const tbody = document.querySelector("#degreeTable tbody");

        const totalRows = tbody.querySelectorAll(".deg-row").length;

        // No records in database
        if (totalRows === 0) return;

        const visible = tbody.querySelectorAll(".deg-row:not(.hidden)").length;

        let emptyRow = tbody.querySelector(".js-empty-row");

        if (visible === 0) {

            if (!emptyRow) {

                emptyRow = document.createElement("tr");
                emptyRow.className = "js-empty-row";

                emptyRow.innerHTML = `
                    <td colspan="6">
                        <div class="empty-state">
                 
                            <h5>No Degrees Found</h5>
                            <p>No results match your search. Try different keywords or reset the filter.</p>
                        </div>
                    </td>
                `;

                tbody.appendChild(emptyRow);
            }

        } else {

            if (emptyRow) emptyRow.remove();

        }
    }

    searchInput?.addEventListener("input", filterRows);


    document.querySelectorAll(".level-pill").forEach(pill => {
        pill.addEventListener("click", () => {
            document.querySelectorAll(".level-pill").forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            filterRows();
        });
    });


    document.getElementById("resetSearch")?.addEventListener("click", () => {
        searchInput.value = "";
        document.querySelectorAll(".level-pill").forEach(p => p.classList.remove("active"));
        document.querySelector('.level-pill[data-level="ALL"]')?.classList.add("active");
        rows.forEach(r => r.classList.remove("hidden"));
        const emptyRow = document.querySelector(".js-empty-row");
        if (emptyRow) emptyRow.remove();
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