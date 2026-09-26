document.addEventListener("DOMContentLoaded", function () {
    const table = document.querySelector(".sr-table");
    if (!table) return;

    table.addEventListener("click", function (e) {
        const approveBtn = e.target.closest("[data-approve-url]");
        const rejectBtn = e.target.closest("[data-reject-url]");
        const btn = approveBtn || rejectBtn;
        if (!btn) return;

        const url = approveBtn ? approveBtn.dataset.approveUrl : rejectBtn.dataset.rejectUrl;
        const action = approveBtn ? "Approved" : "Rejected";

        btn.disabled = true;
        const row = btn.closest("tr");
        const otherBtn = row.querySelector(approveBtn ? "[data-reject-url]" : "[data-approve-url]");
        if (otherBtn) otherBtn.disabled = true;

    fetch(url, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
    })
        .then((res) => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.text();
        })
        .then((rawText) => {
            if (!rawText.trim()) throw new Error("Empty response body");
            const data = JSON.parse(rawText);
            if (!data.success) {
                alert(data.message || "This request was already handled.");
                location.reload();
                return;
            }
            applyRowUpdate(row, data.status);
            bumpStat(1, -1);
            bumpStat(data.status === "Approved" ? 2 : 3, +1);
        })
        .catch((err) => {
            console.error("Approve/reject failed:", err);
            btn.disabled = false;
            if (otherBtn) otherBtn.disabled = false;
            alert("Request failed — please try again.");
        });
    });

    function applyRowUpdate(row, status) {
        const statusCell = row.children[7];
        const actionCell = row.querySelector(".sr-action-cell");

        const badgeClass = status === "Approved" ? "approved" : "rejected";
        statusCell.innerHTML = `<span class="badge ${badgeClass}">${status}</span>`;
        actionCell.innerHTML = `<span class="done">Done</span>`;

        row.style.transition = "background-color 1.2s ease";
        row.style.backgroundColor = status === "Approved" ? "#e6f9ec" : "#fdeaea";
        setTimeout(() => { row.style.backgroundColor = ""; }, 1300);
    }

    function bumpStat(index, delta) {
        const headers = document.querySelectorAll(".stat-card .stat-right h3");
        if (headers[index]) {
            headers[index].textContent = (parseInt(headers[index].textContent, 10) || 0) + delta;
        }
    }
});