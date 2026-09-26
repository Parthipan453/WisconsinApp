window.addEventListener("researchOpportunityPublished", function (e) {
    const params = new URLSearchParams(window.location.search);
    const currentPage = parseInt(params.get("page") || "1", 10);
    if (currentPage !== 1) return; // only insert on page 1, matches admin pattern

    const d = e.detail.opportunity;
    const grid = document.querySelector(".research-card-grid");
    if (!grid) return;

    const emptyCard = grid.querySelector(".empty-card");
    if (emptyCard) emptyCard.remove();

    const skillBadges = (d.skills || [])
        .map(function (s) { return `<span class="skill-badge">${esc(s.toUpperCase())}</span>`; })
        .join("") || `<span class="skill-empty">No skills specified</span>`;

    const card = document.createElement("div");
    card.className = "research-card live-new-card";
    card.innerHTML = `
        <div class="stu-card-header">
            <h3>${esc(d.title)}</h3>
            <span class="dept-badge">${esc(d.department_name)}</span>
        </div>
        <p class="short-description">${esc(d.short_description)}</p>
        <div class="card-info">
            <div class="detail-item">
                <span class="rc-detail-label"><i class="bi bi-person-workspace"></i>Opportunity By</span>
                <span class="rc-detail-value">${esc(d.faculty_first_name)} ${esc(d.faculty_last_name)}</span>
            </div>
            <div class="detail-item">
                <span class="rc-detail-label"><i class="bi bi-people"></i>Total Slots</span>
                <span class="rc-detail-value">${esc(d.available_slots)} Slots</span>
            </div>
            <div class="detail-item">
                <span class="rc-detail-label"><i class="bi bi-calendar-event"></i>Application Deadline</span>
                <span class="rc-detail-value">${esc(d.application_deadline)}</span>
            </div>
        </div>
        <div class="skill-list">${skillBadges}</div>
        <a href="${d.view_url}" class="view-btn">View Details</a>
    `;

    grid.insertBefore(card, grid.firstChild);

    card.style.transition = "background-color 1.5s ease";
    card.style.backgroundColor = "#fff3cd";
    setTimeout(() => { card.style.backgroundColor = ""; }, 1600);

    const heading = document.querySelector("h3");
    if (heading && heading.textContent.includes("Total Opportunities")) {
        const match = heading.textContent.match(/\d+/);
        if (match) {
            const newCount = parseInt(match[0], 10) + 1;
            heading.textContent = heading.textContent.replace(/\d+/, newCount);
        }
    }
});

function esc(str) {
    const div = document.createElement("div");
    div.textContent = str == null ? "" : str;
    return div.innerHTML;
}