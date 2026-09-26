    let deanResearchData = [
        {
            code: "RES-2026-011",
            title: "Long-Term Effects of Microplastics on Freshwater Ecosystems",
            description: "A multi-year field and lab study tracking microplastic accumulation in Lake Mendota and its measurable effects on native fish populations.",
            objectives: ["Quarterly water sampling", "Fish tissue analysis", "Publish year-one findings"],
            pi: "Prof. Daniel Wright",
            hod: "Prof. Karen Ibsen (Biology HOD)",
            department: "Biology",
            submittedDate: "2026-04-18",
            hodApprovedDate: "2026-05-02",
            status: "pending",
            fundingSource: "external",
            fundingLabel: "External Sponsor",
            budget: 182000,
            requiresIRB: false,
            requiresIACUC: true
        },
        {
            code: "RES-2026-003",
            title: "Battery Degradation Modeling for EV Charging Networks",
            description: "Ongoing project modeling lithium-ion battery degradation patterns to optimize public EV charging station scheduling.",
            objectives: ["Collect charge-cycle data", "Fit degradation curves", "Deploy scheduling recommendation prototype"],
            pi: "Prof. Daniel Wright",
            hod: "Prof. Alan Ferreira (Engineering HOD)",
            department: "Engineering",
            submittedDate: "2026-01-10",
            hodApprovedDate: "2026-01-25",
            status: "approved",
            fundingSource: "federal",
            fundingLabel: "Federal Grant",
            budget: 96500,
            requiresIRB: false,
            requiresIACUC: false
        },
        {
            code: "RES-2026-017",
            title: "Community Health Outreach in Rural Wisconsin Counties",
            description: "A collaborative outreach and data-collection initiative partnering with rural clinics to measure the impact of telehealth adoption.",
            objectives: ["Partner with 5 rural clinics", "Collect baseline health metrics", "Year-one impact report"],
            pi: "Prof. Elena Castillo",
            hod: "Prof. Karen Ibsen (Public Health HOD)",
            department: "Public Health",
            submittedDate: "2026-03-11",
            hodApprovedDate: "2026-03-29",
            status: "rejected",
            fundingSource: "external",
            fundingLabel: "External Sponsor",
            budget: 240000,
            requiresIRB: true,
            requiresIACUC: false,
            rejectReason: "Budget exceeds the school's current external-grant cost-share capacity this cycle. Please resubmit with a revised budget or additional co-funding source."
        },
        {
            code: "RES-2026-021",
            title: "Wisconsin Wetland Carbon Sequestration Survey",
            description: "Departmental-funded pilot study surveying carbon sequestration rates across restored wetland sites in southern Wisconsin.",
            objectives: ["Site selection and baseline soil sampling", "Carbon flux measurement", "Preliminary findings report"],
            pi: "Prof. Daniel Wright",
            hod: "Prof. Karen Ibsen (Biology HOD)",
            department: "Biology",
            submittedDate: "2026-06-01",
            hodApprovedDate: "2026-06-14",
            status: "pending",
            fundingSource: "department",
            fundingLabel: "Department Funding",
            budget: 8500,
            requiresIRB: false,
            requiresIACUC: false
        }
    ];

    let deanActiveRejectCode = null;

    function deanStatusLabel(status) {
        return { pending: "Pending", approved: "Approved", rejected: "Rejected" }[status] || status;
    }

    function deanFormatMoney(n) {
        return "$" + n.toLocaleString("en-US");
    }

    function populateDeanDeptFilter() {
        const select = document.getElementById("deanDeptFilter");
        const depts = [...new Set(deanResearchData.map(r => r.department))].sort();
        depts.forEach(d => {
            const opt = document.createElement("option");
            opt.value = d;
            opt.textContent = d;
            select.appendChild(opt);
        });
    }

    function renderDeanStats(data) {
        const total = data.length;
        const pending = data.filter(r => r.status === "pending").length;
        const approved = data.filter(r => r.status === "approved").length;
        const rejected = data.filter(r => r.status === "rejected").length;
        const totalBudget = data.reduce((sum, r) => sum + (r.budget || 0), 0);
        const depts = new Set(data.map(r => r.department)).size;

        document.getElementById("deanStatTotal").textContent = total;
        document.getElementById("deanStatPending").textContent = pending;
        document.getElementById("deanStatApproved").textContent = approved;
        document.getElementById("deanStatRejected").textContent = rejected;
        document.getElementById("deanStatBudget").textContent = deanFormatMoney(totalBudget);
        document.getElementById("deanStatDepts").textContent = depts;
    }

    function renderDeanCards(data) {
        const grid = document.getElementById("deanResearchGrid");
        document.getElementById("deanRecordCount").textContent = `${data.length} Requests`;

        if (data.length === 0) {
            grid.innerHTML = `<p class="deanr-empty"><i class="ti ti-mood-empty"></i> No proposals match your filters.</p>`;
            return;
        }

        grid.innerHTML = data.map(r => `
            <div class="deanr-card">
                <div class="deanr-card-top">
                    <span class="deanr-research-code">${r.code}</span>
                    <span class="deanr-badge deanr-badge-${r.status}">${deanStatusLabel(r.status)}</span>
                </div>
                <h4 class="deanr-card-title">${r.title}</h4>
                <p class="deanr-card-desc">${r.description.slice(0, 110)}${r.description.length > 110 ? "..." : ""}</p>

                <div class="deanr-meta-row">
                    <span><i class="ti ti-user"></i> ${r.pi}</span>
                    <span class="deanr-tag">${r.fundingLabel}</span>
                </div>
                <div class="deanr-meta-row">
                    <span><i class="ti ti-building"></i> ${r.department}</span>
                    <span><i class="ti ti-coin"></i> ${deanFormatMoney(r.budget)}</span>
                </div>
                <div class="deanr-meta-row">
                    <span><i class="ti ti-user-check"></i> HOD-approved ${r.hodApprovedDate}</span>
                </div>

                <div class="deanr-card-actions">
                    <button class="deanr-btn deanr-btn-view" onclick="showDeanDetails('${r.code}')" type="button">
                        <i class="ti ti-eye"></i> View
                    </button>
                    ${r.status === "pending" ? `
                        <button class="deanr-btn deanr-btn-approve" onclick="approveDeanResearch('${r.code}')" type="button">
                            <i class="ti ti-check"></i> Approve
                        </button>
                        <button class="deanr-btn deanr-btn-reject" onclick="openDeanRejectModal('${r.code}')" type="button">
                            <i class="ti ti-x"></i> Reject
                        </button>
                    ` : ``}
                </div>
            </div>
        `).join("");
    }

    function filterDeanCards() {
        const status = document.getElementById("deanStatusFilter").value;
        const dept = document.getElementById("deanDeptFilter").value;
        const funding = document.getElementById("deanFundingFilter").value;
        const search = document.getElementById("deanSearchInput").value.toLowerCase();

        const filtered = deanResearchData.filter(r => {
            const matchStatus = !status || r.status === status;
            const matchDept = !dept || r.department === dept;
            const matchFunding = !funding || r.fundingSource === funding;
            const matchSearch = !search ||
                r.code.toLowerCase().includes(search) ||
                r.title.toLowerCase().includes(search) ||
                r.pi.toLowerCase().includes(search);
            return matchStatus && matchDept && matchFunding && matchSearch;
        });

        renderDeanCards(filtered);
        renderDeanStats(filtered);
    }

    function resetDeanFilters() {
        deptChoice.setChoiceByValue('');
        fundChoice.setChoiceByValue('');
        statusChoice.setChoiceByValue('');
        document.getElementById("deanSearchInput").value = "";
        renderDeanCards(deanResearchData);
        renderDeanStats(deanResearchData);
    }

    function showDeanDetails(code) {
        const r = deanResearchData.find(x => x.code === code);
        if (!r) return;

        document.getElementById("deanModalCode").textContent = r.code;

        document.getElementById("deanDetailBody").innerHTML = `
            <h4 style="margin-bottom:6px;">${r.title}</h4>
            <span class="deanr-badge deanr-badge-${r.status}">${deanStatusLabel(r.status)}</span>
            <p style="margin-top:14px;">${r.description}</p>

            <div class="deanr-detail-grid">
                <div><span class="deanr-detail-label"><i class="ti ti-user"></i> Principal Investigator</span><p>${r.pi}</p></div>
                <div><span class="deanr-detail-label"><i class="ti ti-user-check"></i> Approved by HOD</span><p>${r.hod}</p></div>
                <div><span class="deanr-detail-label"><i class="ti ti-building"></i> Department</span><p>${r.department}</p></div>
                <div><span class="deanr-detail-label"><i class="ti ti-calendar"></i> HOD Approved On</span><p>${r.hodApprovedDate}</p></div>
                <div><span class="deanr-detail-label"><i class="ti ti-cash"></i> Funding Source</span><p>${r.fundingLabel}</p></div>
                <div><span class="deanr-detail-label"><i class="ti ti-coin"></i> Budget Requested</span><p>${deanFormatMoney(r.budget)}</p></div>
                <div><span class="deanr-detail-label"><i class="ti ti-calendar-event"></i> Originally Submitted</span><p>${r.submittedDate}</p></div>
                <div><span class="deanr-detail-label"><i class="ti ti-shield-check"></i> Compliance</span>
                    <p>${r.requiresIRB ? '<span class="deanr-compliance-tag">IRB Required</span>' : ''}
                       ${r.requiresIACUC ? '<span class="deanr-compliance-tag">IACUC Required</span>' : ''}
                       ${(!r.requiresIRB && !r.requiresIACUC) ? 'Not required' : ''}</p>
                </div>
            </div>

            <span class="deanr-detail-label"><i class="ti ti-list-check"></i> Objectives</span>
            <ul class="deanr-objectives">
                ${r.objectives.map(o => `<li>${o}</li>`).join("")}
            </ul>

            ${r.status === "rejected" && r.rejectReason ? `
                <div class="deanr-reject-box">
                    <span class="deanr-detail-label"><i class="ti ti-alert-triangle"></i> Rejection Reason</span>
                    <p>${r.rejectReason}</p>
                </div>
            ` : ``}
        `;

        const actions = document.getElementById("deanDetailActions");
        if (r.status === "pending") {
            actions.innerHTML = `
                <button class="deanr-btn deanr-btn-reset" onclick="document.getElementById('uploadsModal').style.display='flex'"><i class="ti ti-files"></i> Uploads</button>
                <button class="deanr-btn deanr-btn-reject" onclick="closeDeanModal('deanDetailModal'); openDeanRejectModal('${r.code}')" type="button">
                    <i class="ti ti-x"></i> Reject
                </button>
                <button class="deanr-btn deanr-btn-approve" onclick="approveDeanResearch('${r.code}'); closeDeanModal('deanDetailModal')" type="button">
                    <i class="ti ti-check"></i> Approve
                </button>
            `;
        } else {
            actions.innerHTML = `<button class="deanr-btn deanr-btn-reset" onclick="document.getElementById('uploadsModal').style.display='flex'"><i class="ti ti-files"></i> Uploads</button>`;
        }

        document.getElementById("deanDetailModal").style.display = "flex";
    }

    function approveDeanResearch(code) {
        const r = deanResearchData.find(x => x.code === code);
        if (r) r.status = "approved";
        filterDeanCards();
    }

    function openDeanRejectModal(code) {
        deanActiveRejectCode = code;
        document.getElementById("deanRejectReasonInput").value = "";
        document.getElementById("deanRejectModal").style.display = "flex";
    }

    function confirmDeanReject() {
        const reason = document.getElementById("deanRejectReasonInput").value.trim();
        if (!reason) {
            alert("Please provide a reason for rejection.");
            return;
        }
        const r = deanResearchData.find(x => x.code === deanActiveRejectCode);
        if (r) {
            r.status = "rejected";
            r.rejectReason = reason;
        }
        closeDeanModal("deanRejectModal");
        filterDeanCards();
    }

    function closeDeanModal(id) {
        document.getElementById(id).style.display = "none";
    }

    function closeHodModal(id) {
        document.getElementById(id).style.display = "none";
    }
    function exportDeanReport() {
        alert("Export coming soon.");
    }

    // Init
    populateDeanDeptFilter();
    renderDeanStats(deanResearchData);
    renderDeanCards(deanResearchData);


const statusChoice = new Choices('#deanStatusFilter', {
    searchEnabled: false,
    itemSelectText: '',
    shouldSort: false
});

const deptChoice = new Choices('#deanDeptFilter', {
    searchEnabled: false,
    itemSelectText: '',
    shouldSort: false
});

const fundChoice = new Choices('#deanFundingFilter', {
    searchEnabled: false,
    itemSelectText: '',
    shouldSort: false
});