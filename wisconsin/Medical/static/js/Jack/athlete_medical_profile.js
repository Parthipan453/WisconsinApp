let currentPage = 1;
const pageSize = 10;
let allRecords = [];
let filteredData = [];

async function fetchAthleteData() {
    try {
        const response = await fetch('/medical/api/athlete_medical_profile/list/');
        const data = await response.json();
        
        allRecords = data.athlete_medical_profile.map((item, index) => {
            let athleteName = 'Unknown Athlete';
            if (item.athlete) {
                if (typeof item.athlete === 'object' && item.athlete !== null) {
                    athleteName = item.athlete.name || item.athlete.full_name || 'Unknown Athlete';
                } else if (typeof item.athlete === 'string') {
                    athleteName = item.athlete;
                }
            }
            
            let sportName = 'N/A';
            if (item.primary_sport) {
                if (typeof item.primary_sport === 'object' && item.primary_sport !== null) {
                    sportName = item.primary_sport.name || 'N/A';
                } else if (typeof item.primary_sport === 'string') {
                    sportName = item.primary_sport;
                }
            }
            
            let avatarUrl = null;
            if (item.athlete_profile) {
                avatarUrl = item.athlete_profile;
            } else {
                const nameParts = athleteName.split(' ');
                const initials = nameParts.map(p => p[0]).join('');
                avatarUrl = `https://ui-avatars.com/api/?name=${encodeURIComponent(athleteName)}&background=c5050c&color=fff&size=34`;
            }
            
            return {
                uuid: item.uuid,
                id: item.athlete_medical_id || `ATH-${String(index + 1).padStart(4, '0')}`,
                athlete: athleteName,
                sport: sportName,
                blood: item.blood_group || 'N/A',
                clearance: item.medical_clearance_status || 'FIT',
                risk: item.injury_risk || 'LOW',
                avatar: avatarUrl,
                raw: item
            };
        });
        
        filteredData = [...allRecords];
        
        renderTablePage(filteredData, currentPage);
        updateOverview(filteredData);
        
        initializeSlimSelect();
        
        return allRecords;
    } catch (error) {
        console.error('Error fetching athlete data:', error);
        const tbody = document.getElementById('ampTableBody');
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-danger">
            <i class="ti ti-alert-circle fs-2 d-block"></i>
            Failed to load data. Please try again.
        </td></tr>`;
    }
}

function initializeSlimSelect() {
    window.slimSelectInstances = {};

    const clearanceSelect = document.getElementById("ampClearanceFilter");
    if (clearanceSelect) {
        window.slimSelectInstances.clearance = new SlimSelect({
            select: clearanceSelect,
            settings: {
                placeholderText: "All clearances",
                showSearch: false,
            },
        });
    }

    const riskSelect = document.getElementById("ampRiskFilter");
    if (riskSelect) {
        window.slimSelectInstances.risk = new SlimSelect({
            select: riskSelect,
            settings: {
                placeholderText: "All risks",
                showSearch: false,
            },
        });
    }
}

function clearanceBadge(status) {
    const map = {
        'FIT': 'amp-badge-fit',
        'LIMITED': 'amp-badge-limited',
        'REHAB': 'amp-badge-rehab',
        'NOT_FIT': 'amp-badge-notfit',
    };
    return map[status] || 'amp-badge-fit';
}

function riskBadge(risk) {
    const map = {
        'LOW': 'amp-risk-low',
        'MEDIUM': 'amp-risk-medium',
        'HIGH': 'amp-risk-high',
    };
    return map[risk] || 'amp-risk-low';
}

function updateOverview(data) {
    const total = data.length;
    const fit = data.filter((r) => r.clearance === 'FIT').length;
    const limited = data.filter((r) => r.clearance === 'LIMITED').length;
    const rehab = data.filter((r) => r.clearance === 'REHAB').length;
    const notFit = data.filter((r) => r.clearance === 'NOT_FIT').length;

    document.getElementById('ampOvFit').textContent = fit;
    document.getElementById('ampOvLimited').textContent = limited;
    document.getElementById('ampOvRehab').textContent = rehab;
    document.getElementById('ampOvNotFit').textContent = notFit;
    document.getElementById('ampOvTotal').textContent = total;

    updateProgress('ampProgressFit', 'ampPercentFit', fit, total);
    updateProgress('ampProgressLimited', 'ampPercentLimited', limited, total);
    updateProgress('ampProgressRehab', 'ampPercentRehab', rehab, total);
    updateProgress('ampProgressNotFit', 'ampPercentNotFit', notFit, total);
    updateProgress('ampProgressTotal', 'ampProgressTotal', total, total);

    // Total always 100%
    // document.getElementById('ampProgressTotal').style.width = '100%';
    // document.getElementById('ampPercentTotal').textContent = '100%';
}

function updateProgress(progressId, percentId, value, total) {
    const percent = total === 0 ? 0 : Math.round((value / total) * 100);
    const progressElement = document.getElementById(progressId);
    const percentElement = document.getElementById(percentId);
    if (progressElement) progressElement.style.width = percent + '%';
    if (percentElement) percentElement.textContent = percent + '%';
}

function renderTablePage(data, page) {
    const start = (page - 1) * pageSize;
    const end = Math.min(start + pageSize, data.length);
    const pageItems = data.slice(start, end);

    const tbody = document.getElementById('ampTableBody');
    if (!pageItems.length) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-3 text-muted">
            <i class="ti ti-inbox fs-4 d-block"></i> No athletes match
        </td></tr>`;
        document.getElementById('ampPageStart').innerText = 0;
        document.getElementById('ampPageEnd').innerText = 0;
        document.getElementById('ampTotalRecords').innerText = data.length;
        document.getElementById('ampTotalCountBadge').innerText = allRecords.length;
        updateOverview(data);
        renderPagination(data.length, page);
        return;
    }

    let html = '';
    pageItems.forEach((r, index) => {
        const serialNo = start + index + 1;
        const avatarHtml = r.avatar
            ? `<img src="${r.avatar}" alt="${r.athlete}" loading="lazy">`
            : r.athlete
                .split(' ')
                .map((w) => w[0])
                .join('');

        html += `<tr>
            <td class="amp-sno-cell"><span class="fw-bold text-muted">${serialNo}</span></td>
            <td class="amp-athlete-cell">
                <div class="amp-athlete-cell">
                    <span class="amp-athlete-avatar">${avatarHtml}</span>
                    <div>
                        <div class="fw-semibold" style="color:var(--amp-text-dark); font-size:0.85rem;">${r.athlete}</div>
                        <span class="amp-medical-id">${r.id}</span>
                    </div>
                </div>
            </td>
            <td class="amp-sport-cell"><span class="amp-sport-tag">${r.sport}</span></td>
            <td class="amp-blood-cell"><span class="fw-bold">${r.blood}</span></td>
            <td class="amp-clearance-cell"><span class="amp-badge-clearance ${clearanceBadge(r.clearance)}">${r.clearance.replace('_', ' ')}</span></td>
            <td class="amp-risk-cell"><span class="amp-badge-risk ${riskBadge(r.risk)}">${r.risk}</span></td>
            <td class="amp-actions-cell">
                <div class="amp-action-btn-group">
                    <button class="amp-btn-outline-injury btn-sm" onclick="viewInjuries('${r.uuid}')">
                        <i class="ti ti-activity me-1"></i> Injuries
                    </button>
                    <button class="btn btn-outline-secondary btn-sm" style="border-radius:40px;padding:0.15rem 0.5rem;font-size:0.65rem;" onclick="viewProfile('${r.uuid}')">
                        <i class="ti ti-eye"></i>
                    </button>
                </div>
            </td>
        </tr>`;
    });
    tbody.innerHTML = html;

    document.getElementById('ampPageStart').innerText = data.length ? start + 1 : 0;
    document.getElementById('ampPageEnd').innerText = data.length ? end : 0;
    document.getElementById('ampTotalRecords').innerText = data.length;
    document.getElementById('ampTotalCountBadge').innerText = allRecords.length;

    updateOverview(data);
    renderPagination(data.length, page);
}

function renderPagination(totalItems, current) {
    const totalPages = Math.ceil(totalItems / pageSize) || 1;
    const container = document.getElementById('ampPaginationControls');
    if (!container) return;
    
    let html = '';

    html += `<button class="amp-btn-page" onclick="goToPage(${current - 1})" ${current <= 1 ? 'disabled' : ''}>
        <i class="ti ti-chevron-left"></i>
    </button>`;

    let startPage = Math.max(1, current - 2);
    let endPage = Math.min(totalPages, startPage + 4);
    if (endPage - startPage < 4) startPage = Math.max(1, endPage - 4);

    for (let p = startPage; p <= endPage; p++) {
        html += `<button class="amp-btn-page ${p === current ? 'active' : ''}" onclick="goToPage(${p})">${p}</button>`;
    }

    html += `<button class="amp-btn-page" onclick="goToPage(${current + 1})" ${current >= totalPages ? 'disabled' : ''}>
        <i class="ti ti-chevron-right"></i>
    </button>`;

    container.innerHTML = html;
}

function goToPage(page) {
    const total = Math.ceil(filteredData.length / pageSize) || 1;
    if (page < 1 || page > total) return;
    currentPage = page;
    renderTablePage(filteredData, currentPage);
}

function applyFilters() {
    const searchVal = document.getElementById('ampSearchInput')
        .value.toLowerCase()
        .trim();
    const clearanceSelect = document.getElementById('ampClearanceFilter');
    const riskSelect = document.getElementById('ampRiskFilter');
    
    const clearanceVal = clearanceSelect ? clearanceSelect.value : '';
    const riskVal = riskSelect ? riskSelect.value : '';

    filteredData = allRecords.filter((r) => {
        const matchSearch =
            r.athlete.toLowerCase().includes(searchVal) ||
            r.id.toLowerCase().includes(searchVal) ||
            r.sport.toLowerCase().includes(searchVal);
        const matchClearance = clearanceVal === '' || r.clearance === clearanceVal;
        const matchRisk = riskVal === '' || r.risk === riskVal;
        return matchSearch && matchClearance && matchRisk;
    });

    currentPage = 1;
    renderTablePage(filteredData, currentPage);
}

function resetFilters() {
    document.getElementById("ampSearchInput").value = "";

    if (window.slimSelectInstances.clearance) {
        window.slimSelectInstances.clearance.setSelected("");
    }

    if (window.slimSelectInstances.risk) {
        window.slimSelectInstances.risk.setSelected("");
    }

    applyFilters();
}

function viewInjuries(athleteUUID) {
    window.location.href = `/medical/athlete_injury_record/${athleteUUID}`;
}

function viewProfile(athleteUUID) {
    window.location.href = `/medical/athlete_medical_profile_view/${athleteUUID}`;
}

function showLoading() {
    const tbody = document.getElementById('ampTableBody');
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4">
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        <div class="mt-2 text-muted">Loading athletes...</div>
    </td></tr>`;
}

document.addEventListener('DOMContentLoaded', function() {
    showLoading();
    
    window.slimSelectInstances = {};
    
    fetchAthleteData().then(() => {
        const clearanceSelect = document.getElementById('ampClearanceFilter');
        const riskSelect = document.getElementById('ampRiskFilter');
        
        if (clearanceSelect && clearanceSelect.slim) {
            window.slimSelectInstances.clearance = clearanceSelect.slim;
        }
        if (riskSelect && riskSelect.slim) {
            window.slimSelectInstances.risk = riskSelect.slim;
        }
    });
});

let searchTimeout;
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('ampSearchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(applyFilters, 300);
        });
    }
});

window.applyFilters = applyFilters;
window.resetFilters = resetFilters;
window.goToPage = goToPage;
window.viewInjuries = viewInjuries;
window.viewProfile = viewProfile;
window.renderTablePage = renderTablePage;
window.updateOverview = updateOverview;