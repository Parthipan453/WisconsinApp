let hodResearchData = [
        {
            code: "RES-2026-014",
            title: "Machine Learning Approaches to Crop Yield Prediction",
            description: "Investigating the use of convolutional neural networks on satellite imagery to predict crop yields across Wisconsin farmland, aiming to support early-season planning for local agricultural cooperatives.",
            objectives: ["Build a labeled imagery dataset", "Train and validate a CNN model", "Compare against baseline statistical models"],
            submittedBy: "Aditi Rao (Student)",
            mentor: "Prof. Daniel Wright",
            department: "Computer Science",
            type: "student",
            submittedDate: "2026-06-02",
            status: "pending",
            fundingSource: "Department Funding",
            budget: "$4,200",
            requiresIRB: false,
            requiresIACUC: false
        },
        {
            code: "RES-2026-011",
            title: "Long-Term Effects of Microplastics on Freshwater Ecosystems",
            description: "A multi-year field and lab study tracking microplastic accumulation in Lake Mendota and its measurable effects on native fish populations.",
            objectives: ["Quarterly water sampling", "Fish tissue analysis", "Publish year-one findings"],
            submittedBy: "Prof. Daniel Wright",
            mentor: "Prof. Daniel Wright",
            department: "Biology",
            type: "faculty",
            submittedDate: "2026-04-18",
            status: "approved",
            fundingSource: "External Sponsor",
            budget: "$182,000",
            requiresIRB: false,
            requiresIACUC: true
        },
        {
            code: "RES-2026-009",
            title: "Survey-Based Study on Remote Work and Student Mental Health",
            description: "Understanding how post-pandemic remote/hybrid coursework affects self-reported stress and social connection among undergraduates.",
            objectives: ["Design and pilot the survey instrument", "Recruit 300+ respondents", "Statistical analysis and writeup"],
            submittedBy: "Marcus Lee (Student)",
            mentor: "Prof. Elena Castillo",
            department: "Psychology",
            type: "student",
            submittedDate: "2026-05-25",
            status: "rejected",
            fundingSource: "Unfunded / Self-Directed",
            budget: "$0",
            requiresIRB: true,
            requiresIACUC: false,
            rejectReason: "Survey instrument needs IRB pre-clearance before resubmission; please attach the CITI training certificate."
        },
        {
            code: "RES-2026-003",
            title: "Battery Degradation Modeling for EV Charging Networks",
            description: "Ongoing project modeling lithium-ion battery degradation patterns to optimize public EV charging station scheduling.",
            objectives: ["Collect charge-cycle data", "Fit degradation curves", "Deploy scheduling recommendation prototype"],
            submittedBy: "Prof. Daniel Wright",
            mentor: "Prof. Daniel Wright",
            department: "Engineering",
            type: "faculty",
            submittedDate: "2026-01-10",
            status: "ongoing",
            fundingSource: "Federal Grant",
            budget: "$96,500",
            requiresIRB: false,
            requiresIACUC: false
        }
    ];

    let hodActiveRejectCode = null;

    function statusLabel(status) {
        return { pending: "Pending", approved: "Approved", rejected: "Rejected", ongoing: "Ongoing" }[status] || status;
    }

    function typeLabel(type) {
        return type === "student" ? "Student-Initiated" : "Faculty-Led";
    }

    function renderHodStats() {
        const total = hodResearchData.length;
        const pending = hodResearchData.filter(r => r.status === "pending").length;
        const approved = hodResearchData.filter(r => r.status === "approved").length;
        const rejected = hodResearchData.filter(r => r.status === "rejected").length;
        const ongoing = hodResearchData.filter(r => r.status === "ongoing").length;
        const researchers = new Set(hodResearchData.map(r => r.submittedBy)).size;

        document.getElementById("statTotalRequests").textContent = total;
        document.getElementById("statPending").textContent = pending;
        document.getElementById("statApproved").textContent = approved;
        document.getElementById("statRejected").textContent = rejected;
        document.getElementById("statOngoing").textContent = ongoing;
        document.getElementById("statResearchers").textContent = researchers;
    }

    function renderHodCards(data) {
        const grid = document.getElementById("hodResearchGrid");
        document.getElementById("hodRecordCount").textContent = `${data.length} Requests`;

        if (data.length === 0) {
            grid.innerHTML = `<p class="empty-state"><i class="ti ti-mood-empty"></i> No research requests match your filters.</p>`;
            return;
        }

        grid.innerHTML = data.map(r => `
            <div class="project-card research-card">
                <div class="card-top">
                    <span class="research-code">${r.code}</span>
                    <span class="status-badge status-${r.status}">${statusLabel(r.status)}</span>
                </div>
                <h4 class="project-title">${r.title}</h4>
                <p class="project-desc">${r.description.slice(0, 110)}${r.description.length > 110 ? "..." : ""}</p>

                <div class="meta-row">
                    <span><i class="ti ti-user"></i> ${r.submittedBy}</span>
                    <span class="type-tag type-${r.type}">${typeLabel(r.type)}</span>
                </div>
                <div class="meta-row">
                    <span><i class="ti ti-building"></i> ${r.department}</span>
                    <span><i class="ti ti-calendar"></i> ${r.submittedDate}</span>
                </div>

                <div class="card-actions">
                    <button class="filter-btn view-btn" onclick="showResearchDetails('${r.code}')">
                        <i class="ti ti-eye"></i> View
                    </button>
                    ${r.status === "pending" ? `
                        <button class="filter-btn approve-btn" onclick="approveResearch('${r.code}')">
                            <i class="ti ti-check"></i> Approve
                        </button>
                        <button class="filter-btn reject-btn" onclick="openRejectModal('${r.code}')">
                            <i class="ti ti-x"></i> Reject
                        </button>
                    ` : ``}
                </div>
            </div>
        `).join("");
    }

    function filterHodCards() {
        const status = document.getElementById("hodStatusFilter").value;
        const type = document.getElementById("hodTypeFilter").value;
        const search = document.getElementById("hodSearchInput").value.toLowerCase();

        const filtered = hodResearchData.filter(r => {
            const matchStatus = !status || r.status === status;
            const matchType = !type || r.type === type;
            const matchSearch = !search ||
                r.code.toLowerCase().includes(search) ||
                r.title.toLowerCase().includes(search) ||
                r.submittedBy.toLowerCase().includes(search);
            return matchStatus && matchType && matchSearch;
        });

        renderHodCards(filtered);
    }

    function resetHodFilters() {
        statusChoice.setChoiceByValue('');
        typeChoice.setChoiceByValue('');
        document.getElementById("hodSearchInput").value = "";
        renderHodCards(hodResearchData);
    }

    function showResearchDetails(code) {
        const r = hodResearchData.find(x => x.code === code);
        if (!r) return;

        document.getElementById("modalResearchCode").textContent = r.code;

        document.getElementById("researchDetailBody").innerHTML = `
            <h4 style="margin-bottom:6px;">${r.title}</h4>
            <span class="status-badge status-${r.status}">${statusLabel(r.status)}</span>
            <p style="margin-top:14px;">${r.description}</p>

            <div class="detail-grid">
                <div><span class="detail-label"><i class="ti ti-user"></i> Submitted By</span><p>${r.submittedBy}</p></div>
                <div><span class="detail-label"><i class="ti ti-user-check"></i> Faculty Mentor</span><p>${r.mentor}</p></div>
                <div><span class="detail-label"><i class="ti ti-building"></i> Department</span><p>${r.department}</p></div>
                <div><span class="detail-label"><i class="ti ti-tag"></i> Type</span><p>${typeLabel(r.type)}</p></div>
                <div><span class="detail-label"><i class="ti ti-calendar"></i> Submitted</span><p>${r.submittedDate}</p></div>
                <div><span class="detail-label"><i class="ti ti-cash"></i> Funding Source</span><p>${r.fundingSource}</p></div>
                <div><span class="detail-label"><i class="ti ti-coin"></i> Budget</span><p>${r.budget}</p></div>
                <div><span class="detail-label"><i class="ti ti-shield-check"></i> Compliance</span>
                    <p>${r.requiresIRB ? '<span class="compliance-tag">IRB Required</span>' : ''}
                       ${r.requiresIACUC ? '<span class="compliance-tag">IACUC Required</span>' : ''}
                       ${(!r.requiresIRB && !r.requiresIACUC) ? 'Not required' : ''}</p>
                </div>
            </div>

            <span class="detail-label"><i class="ti ti-list-check"></i> Objectives</span>
            <ul class="objectives-list">
                ${r.objectives.map(o => `<li>${o}</li>`).join("")}
            </ul>

            ${r.status === "rejected" && r.rejectReason ? `
                <div class="reject-reason-box">
                    <span class="detail-label"><i class="ti ti-alert-triangle"></i> Rejection Reason</span>
                    <p>${r.rejectReason}</p>
                </div>
            ` : ``}
        `;
                
        const actions = document.getElementById("researchDetailActions");
        if (r.status === "pending") {
            actions.innerHTML = `
                <button class="filter-btn view-btn" onclick="document.getElementById('uploadsModal').style.display='flex'"><i class="ti ti-files"></i> Uploads</button>
                <button class="filter-btn reject-btn" onclick="closeHodModal('researchDetailModal'); openRejectModal('${r.code}')">
                    <i class="ti ti-x"></i> Reject
                </button>
                <button class="filter-btn approve-btn" onclick="approveResearch('${r.code}'); closeHodModal('researchDetailModal')">
                    <i class="ti ti-check"></i> Approve
                </button>
            `;
        } else {
            actions.innerHTML = `<button class="filter-btn view-btn" onclick="document.getElementById('uploadsModal').style.display='flex'"><i class="ti ti-files"></i> Uploads</button>`;
        }

        document.getElementById("researchDetailModal").style.display = "flex";
    }

    function approveResearch(code) {
        const r = hodResearchData.find(x => x.code === code);
        if (r) r.status = "approved";
        filterHodCards();
        renderHodStats();
    }

    function openRejectModal(code) {
        hodActiveRejectCode = code;
        document.getElementById("rejectReasonInput").value = "";
        document.getElementById("rejectReasonModal").style.display = "flex";
    }

    function confirmRejectResearch() {
        const reason = document.getElementById("rejectReasonInput").value.trim();
        if (!reason) {
            alert("Please provide a reason for rejection.");
            return;
        }
    
        const r = hodResearchData.find(x => x.code === hodActiveRejectCode);
        if (r) {
            r.status = "rejected";
            r.rejectReason = reason;
        }
        closeHodModal("rejectReasonModal");
        filterHodCards();
        renderHodStats();
    }

    function closeHodModal(id) {
        document.getElementById(id).style.display = "none";
    }

    function exportHodReport() {
        
        alert("Export coming soon.");
    }

    // Init
    renderHodStats();
    renderHodCards(hodResearchData);





const statusChoice = new Choices('#hodStatusFilter', {
    searchEnabled: false,
    itemSelectText: '',
    shouldSort: false
});

const typeChoice = new Choices('#hodTypeFilter', {
    searchEnabled: false,
    itemSelectText: '',
    shouldSort: false
});