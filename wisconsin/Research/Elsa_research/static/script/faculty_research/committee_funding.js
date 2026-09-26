document.addEventListener("DOMContentLoaded", function () {
    const selects = document.querySelectorAll(".rf-choice");
    selects.forEach(function(select){
        new Choices(select, {
            searchEnabled: true,
            itemSelectText: "",
            shouldSort: false,
            placeholder: true,
            placeholderValue: "Select option",
            noResultsText: "No results found",
            noChoicesText: "No options available"
        });
    });
    if(window.lucide){
        lucide.createIcons();
    }
});
// ---- Live updates on research_funding_added ----
window.addEventListener("research_funding_added", function (e) {
    const d = e.detail;
    const isDetailPage = !!document.querySelector(".rf-details-card");
 
    if (isDetailPage) {
        updateFundingDetailPage(d);
    } else {
        updateFundingListPage(d);
    }
});
 
function esc(str) {
    const div = document.createElement("div");
    div.textContent = str == null ? "" : str;
    return div.innerHTML;
}
 
// ---- LIST page: committee_funding.html ----
function updateFundingListPage(d) {
    const tbody = document.querySelector(".rf-table tbody");
    if (!tbody) return;
 
    let matchedRow = null;
    tbody.querySelectorAll("tr").forEach(function (row) {
        const firstCell = row.children[0];
        if (firstCell && firstCell.textContent.trim() === String(d.research_id)) {
            matchedRow = row;
        }
    });
 
    if (matchedRow) {
        matchedRow.children[4].textContent = `$ ${d.received_amount}`;
        matchedRow.children[5].textContent = `$ ${d.balance_amount}`;
        flashRow(matchedRow);
    } else {
        const emptyRow = tbody.querySelector("td.rf-empty");
        if (emptyRow) emptyRow.closest("tr").remove();
 
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${esc(d.research_id)}</td>
            <td>${esc(d.research_title)}</td>
            <td>${esc(d.faculty_name)}</td>
            <td>$ ${esc(d.estimated_amount)}</td>
            <td>$ ${esc(d.received_amount)}</td>
            <td>$ ${esc(d.balance_amount)}</td>
            <td>
                <a href="${d.view_url}" class="rf-btn rf-btn-view">
                    <i data-lucide="eye"></i>
                    View
                </a>
            </td>
        `;
        tbody.insertBefore(tr, tbody.firstChild);
        if (window.lucide) lucide.createIcons();
        flashRow(tr);
    }
}
 
// ---- DETAIL page: committee_funding_view.html ----
function updateFundingDetailPage(d) {
    const researchIdEl = document.querySelector(".rf-detail-item h4");
    if (!researchIdEl || researchIdEl.textContent.trim() !== String(d.research_id)) return;

    const statValues = document.querySelectorAll(".rf-stats-grid .rf-stat-card h3");
    if (statValues[1]) statValues[1].textContent = `$ ${d.received_amount}`;
    if (statValues[2]) statValues[2].textContent = `$ ${d.balance_amount}`;

    const tbody = document.querySelector(".rf-table tbody");
    if (!tbody) return;

    // d.funding_id now carries funding_code (see view change above)
    if (tbody.querySelector(`tr[data-funding-id="${d.funding_id}"]`)) return;

    const emptyRow = tbody.querySelector("td.rf-empty");
    if (emptyRow) emptyRow.closest("tr").remove();

    const tr = document.createElement("tr");
    tr.dataset.fundingId = d.funding_id;
    tr.innerHTML = `
        <td class="rf-serial">1</td>
        <td>${esc(d.funding_id)} <span class="rf-new-badge">New</span></td>
        <td>${esc(d.funding_source)}</td>
        <td>${esc(d.sponsor)}</td>
        <td>$ ${esc(d.amount)}</td>
        <td>${esc(d.award_date)}</td>
    `;
    tbody.insertBefore(tr, tbody.firstChild);
    markRowNew(tr, `funding-${d.funding_id}`);

    renumberFundingRows(tbody);
}

function renumberFundingRows(tbody) {
    tbody.querySelectorAll("tr").forEach(function (row, index) {
        const serialCell = row.querySelector(".rf-serial");
        if (serialCell) serialCell.textContent = index + 1;
    });
}
 
function flashRow(row) {
    row.style.transition = "background-color 1.3s ease";
    row.style.backgroundColor = "#fff3cd";
    setTimeout(() => { row.style.backgroundColor = ""; }, 1400);
}