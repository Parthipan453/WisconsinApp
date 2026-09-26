var typeColors = {
    casual: { color: 'var(--secondary)', colorLight: 'var(--secondary-light)', icon: 'ti ti-umbrella' },
    sick: { color: 'var(--danger)', colorLight: 'var(--danger-light)', icon: 'ti ti-ambulance' },
    annual: { color: 'var(--success)', colorLight: 'var(--success-light)', icon: 'ti ti-beach' },
    emergency: { color: 'var(--primary)', colorLight: 'var(--primary-light)', icon: 'ti ti-alert-triangle' },
    maternity: { color: 'var(--info)', colorLight: 'var(--info-light)', icon: 'ti ti-baby-carriage' },
    paternity: { color: 'var(--info)', colorLight: 'var(--info-light)', icon: 'ti ti-horse-toy' },
    unpaid: { color: 'var(--gray-700)', colorLight: 'var(--gray-200)', icon: 'ti ti-currency-dollar' },
    permission: { color: 'var(--warning)', colorLight: 'var(--warning-light)', icon: 'ti ti-clock-hour-3' }
};

document.querySelectorAll('.lp-seg').forEach(function(seg) {
    var type = seg.getAttribute('data-type');
    if (type && typeColors[type]) {
        seg.style.setProperty('--seg-color', typeColors[type].color);
    }
});

var lpData = {
    casual: {
        title: 'Casual Leave',
        desc: "For short personal matters that come up without much notice.",
        total: 12,
        used: 0,
        unit: 'days',
        notice: '24 hours',
        docs: 'None required'
    },
    sick: {
        title: 'Sick Leave',
        desc: "For recovery time when you're unwell or need medical care.",
        total: 10,
        used: 0,
        unit: 'days',
        notice: 'Same day',
        docs: 'Certificate after 2+ days'
    },
    annual: {
        title: 'Annual Leave',
        desc: 'Planned time away to rest, travel, and recharge.',
        total: 21,
        used: 0,
        unit: 'days',
        notice: '7 days',
        docs: 'None'
    },
    emergency: {
        title: 'Emergency Leave',
        desc: "For sudden, urgent situations that can't wait.",
        total: 5,
        used: 0,
        unit: 'days',
        notice: 'Immediate',
        docs: 'Explanation on return'
    },
    maternity: {
        title: 'Maternity Leave',
        desc: 'Paid leave surrounding childbirth and early care.',
        total: 182,
        used: 0,
        unit: 'days',
        notice: '30 days',
        docs: 'Medical certification'
    },
    paternity: {
        title: 'Paternity Leave',
        desc: 'Time to support your family after a new arrival.',
        total: 14,
        used: 0,
        unit: 'days',
        notice: '15 days',
        docs: 'Proof of birth'
    },
    unpaid: {
        title: 'Unpaid Leave',
        desc: 'Extended leave beyond your paid entitlements.',
        total: null,
        used: 0,
        unit: 'days',
        notice: '14 days',
        docs: 'Department head sign-off'
    },
    permission: {
        title: 'Permission',
        desc: 'Short, hours-based leave for brief personal errands.',
        total: 12,
        used: 0,
        unit: 'hrs / month',
        notice: '2 hours',
        docs: 'None'
    }
};

function updateUsedLeave() {

    const now = new Date();

    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth();

    const yearStart = new Date(
        currentYear,
        0,
        1
    );

    const nextYearStart = new Date(
        currentYear + 1,
        0,
        1
    );

    const monthStart = new Date(
        currentYear,
        currentMonth,
        1
    );

    const nextMonthStart = new Date(
        currentYear,
        currentMonth + 1,
        1
    );

    Object.keys(lpData).forEach(function (key) {
        lpData[key].used = 0;
    });


    const typeKeyMap = {
        CASUAL: 'casual',
        SICK: 'sick',
        ANNUAL: 'annual',
        EMERGENCY: 'emergency',
        MATERNITY: 'maternity',
        PATERNITY: 'paternity',
        UNPAID: 'unpaid',
        PERMISSION: 'permission'
    };

    leaveDataList.forEach(function (leave) {

        if (leave.status !== 'approved') {
            return;
        }


        const typeKey =
            typeKeyMap[leave.leave_type];


        if (!typeKey || !lpData[typeKey]) {
            return;
        }

        if (leave.leave_type === 'PERMISSION') {

            if (
                !leave.start_date ||
                !leave.permission_start_time ||
                !leave.permission_end_time
            ) {
                return;
            }


            const permissionDate =
                new Date(
                    leave.start_date + 'T00:00:00'
                );


            if (
                permissionDate < monthStart ||
                permissionDate >= nextMonthStart
            ) {
                return;
            }


            const start =
                timeToMinutes(
                    leave.permission_start_time
                );

            const end =
                timeToMinutes(
                    leave.permission_end_time
                );


            const minutes = end - start;

            const hours = minutes / 60;


            lpData.permission.used += hours;

            return;
        }

        if (leave.leave_type === 'UNPAID') {

            if (
                !leave.start_date ||
                !leave.end_date
            ) {
                return;
            }


            const start =
                new Date(
                    leave.start_date + 'T00:00:00'
                );

            const end =
                new Date(
                    leave.end_date + 'T00:00:00'
                );


            if (
                isNaN(start.getTime()) ||
                isNaN(end.getTime())
            ) {
                return;
            }


            const days =
                Math.floor(
                    (end - start) /
                    (1000 * 60 * 60 * 24)
                ) + 1;


            lpData.unpaid.used += days;

            return;
        }

        if (leave.leave_type === 'MATERNITY') {

            if (
                !leave.start_date ||
                !leave.end_date
            ) {
                return;
            }


            const start =
                new Date(
                    leave.start_date + 'T00:00:00'
                );

            const end =
                new Date(
                    leave.end_date + 'T00:00:00'
                );


            if (
                isNaN(start.getTime()) ||
                isNaN(end.getTime())
            ) {
                return;
            }


            const days =
                Math.floor(
                    (end - start) /
                    (1000 * 60 * 60 * 24)
                ) + 1;


            lpData.maternity.used += days;

            return;
        }

        if (leave.leave_type === 'PATERNITY') {

            if (
                !leave.start_date ||
                !leave.end_date
            ) {
                return;
            }


            const start =
                new Date(
                    leave.start_date + 'T00:00:00'
                );

            const end =
                new Date(
                    leave.end_date + 'T00:00:00'
                );


            if (
                isNaN(start.getTime()) ||
                isNaN(end.getTime())
            ) {
                return;
            }


            const days =
                Math.floor(
                    (end - start) /
                    (1000 * 60 * 60 * 24)
                ) + 1;


            lpData.paternity.used += days;

            return;
        }

        const start =
            new Date(
                leave.start_date + 'T00:00:00'
            );

        const end =
            new Date(
                leave.end_date + 'T00:00:00'
            );


        if (
            isNaN(start.getTime()) ||
            isNaN(end.getTime())
        ) {
            return;
        }

        if (
            end < yearStart ||
            start >= nextYearStart
        ) {
            return;
        }


        const days =
            Math.floor(
                (end - start) /
                (1000 * 60 * 60 * 24)
            ) + 1;


        lpData[typeKey].used += days;
    });

    Object.keys(lpData).forEach(function (key) {

        lpData[key].used =
            Math.round(
                lpData[key].used * 100
            ) / 100;
    });


    console.log(
        'Current year:',
        currentYear
    );

    console.log(
        'Current month:',
        currentMonth + 1
    );

    console.log(
        'Updated Leave Usage:',
        lpData
    );
}

function timeToMinutes(timeString) {

    const [hours, minutes] =
        timeString.split(':').map(Number);

    return (
        hours * 60 +
        minutes
    );
}

var meter = document.getElementById('lpMeter');
var panel = document.getElementById('lpPanel');

function renderPanel(key) {
    var d = lpData[key];
    if (!d) return;
    var colors = typeColors[key] || typeColors.casual;

    var hasTotal = typeof d.total === 'number';
    var remaining = hasTotal ? (d.total - d.used) : null;
    var pct = Math.min(100, Math.round(((d.total - d.used) / d.total) * 100));

    var usageBarHtml = '';
    if (hasTotal) {
        usageBarHtml =
            '<div class="lp-usage-bar-wrap">' +
            '<div class="lp-usage-bar-labels"><span><strong>' + d.used + '</strong> of ' + d.total + ' ' + d.unit +
            ' used</span><span>' + remaining + ' ' + d.unit + ' left</span></div>' +
            '<div class="lp-usage-bar-track"><div class="lp-usage-bar-fill" style="width:' + pct +
            '%; --panel-color:' + colors.color + ';"></div></div>' +
            '</div>';
    }

    panel.innerHTML =
        '<div class="lp-panel-head">' +
        '<div class="lp-panel-icon" style="--panel-color:' + colors.color + '; --panel-color-light:' + colors
        .colorLight + ';">' +
        '<i class="' + colors.icon + '"></i>' +
        '</div>' +
        '<div><h3>' + d.title + '</h3><p>' + d.desc + '</p></div>' +
        '</div>' +
        usageBarHtml +
        '<div class="lp-panel-facts">' +
        '<div class="lp-fact"><span class="lp-fact-label">Entitlement</span><span class="lp-fact-val">' + (
            hasTotal ? d.total + ' ' + d.unit : 'As approved') + '</span></div>' +
        '<div class="lp-fact"><span class="lp-fact-label">Used so far</span><span class="lp-fact-val">' +
        d.used + ' ' + d.unit + '</span></div>' +
        '<div class="lp-fact"><span class="lp-fact-label">Notice period</span><span class="lp-fact-val">' +
        d.notice + '</span></div>' +
        '<div class="lp-fact"><span class="lp-fact-label">Documentation</span><span class="lp-fact-val">' +
        d.docs + '</span></div>' +
        '</div>';

    requestAnimationFrame(function() {
        var fill = panel.querySelector('.lp-usage-bar-fill');
        if (fill) {
            fill.style.width = '0%';
            requestAnimationFrame(function() {
                fill.style.width = pct + '%';
            });
        }
    });
}

function switchType(key, btn) {
    meter.querySelectorAll('.lp-seg').forEach(function(s) {
        s.classList.remove('lp-active');
    });
    btn.classList.add('lp-active');
    panel.classList.add('lp-fade');
    setTimeout(function() {
        renderPanel(key);
        panel.classList.remove('lp-fade');
    }, 200);
}

if (meter) {
    meter.addEventListener('click', function(e) {
        var btn = e.target.closest('.lp-seg');
        if (!btn) return;
        switchType(btn.getAttribute('data-type'), btn);
    });
}
renderPanel('casual');

document.querySelectorAll('.lp-leave-row').forEach(function(row) {
    var typeText = row.querySelector('.lp-leave-type')?.textContent?.trim() || '';
    var colorMap = {
        'Casual Leave': 'var(--secondary)',
        'Sick Leave': 'var(--danger)',
        'Annual Leave': 'var(--success)',
        'Emergency Leave': 'var(--primary)',
        'Maternity Leave': 'var(--info)',
        'Paternity Leave': 'var(--info)',
        'Unpaid Leave': 'var(--gray-700)',
        'Permission': 'var(--warning)'
    };
    var color = colorMap[typeText] || 'var(--gray-400)';
    row.style.setProperty('--row-color', color);
    var dot = row.querySelector('.lp-chip-dot');
    if (dot) {
        dot.style.background = color;
    }
});

let leaveDataList = [];

const itemsPerPage = 5;
let currentPage = 1;

const leaveList = document.getElementById('leaveList');
const prevBtn = document.getElementById('prevPage');
const nextBtn = document.getElementById('nextPage');
const pageNumbers = document.getElementById('pageNumbers');

const statusClasses = {
    approved: 'lp-status-approved',
    pending: 'lp-status-pending',
    rejected: 'lp-status-rejected',
    cancelled: 'lp-status-cancelled'
};

const statusColors = {
    approved: '#228b22',
    pending: '#f59e0b',
    rejected: '#dc2626',
    cancelled: '#888'
};

const typeColorMap = {
    'Casual Leave': 'var(--secondary)',
    'Sick Leave': 'var(--danger)',
    'Annual Leave': 'var(--success)',
    'Emergency Leave': 'var(--primary)',
    'Maternity Leave': 'var(--info)',
    'Paternity Leave': 'var(--info)',
    'Unpaid Leave': 'var(--gray-700)',
    'Permission': 'var(--warning)'
};


async function loadLeaveData() {
    try {
        const response = await fetch('/medical/api/leave_list/');

        if (!response.ok) {
            throw new Error('Failed to load leave data');
        }

        const data = await response.json();

        if (!data.success) {
            throw new Error('Unable to load leaves');
        }

        leaveDataList = data.leaves.map(leave => {

            const leaveTypeMap = {
                CASUAL: 'Casual Leave',
                SICK: 'Sick Leave',
                ANNUAL: 'Annual Leave',
                EMERGENCY: 'Emergency Leave',
                MATERNITY: 'Maternity Leave',
                PATERNITY: 'Paternity Leave',
                UNPAID: 'Unpaid Leave',
                PERMISSION: 'Permission'
            };

            const type = leaveTypeMap[leave.leave_type] || leave.leave_type;

            const statusMap = {
                PENDING: 'Pending',
                APPROVED: 'Approved',
                REJECTED: 'Rejected',
                CANCELLED: 'Cancelled'
            };

            const status = leave.status.toLowerCase();
            const statusText = statusMap[leave.status] || leave.status;

            const startDate = formatDate(leave.start_date);
            const endDate = formatDate(leave.end_date);

            let dates;

            if (leave.leave_type === 'PERMISSION') {

                const startTime = formatTime(leave.permission_start_time);
                const endTime = formatTime(leave.permission_end_time);

                dates = `${startDate} · ${startTime}–${endTime}`;

            } else if (leave.start_date === leave.end_date) {

                dates = startDate;

            } else {

                dates = `${startDate} – ${endDate}`;
            }

            let meta = '';

            if (status === 'approved' && leave.approved_at) {

                const approvedDate = formatDate(
                    leave.approved_at.split('T')[0]
                );

                meta = `Approved on ${approvedDate}`;

            } else if (status === 'rejected' && leave.rejection_reason) {

                meta = `Reason for rejection: ${leave.rejection_reason}`;
            }

            return {
                id: leave.id,
                uuid: leave.uuid,

                leave_type: leave.leave_type,

                type: type,

                start_date: leave.start_date,
                end_date: leave.end_date,

                permission_start_time: leave.permission_start_time,
                permission_end_time: leave.permission_end_time,

                dates: dates,
                reason: leave.reason || '',
                status: status,
                statusText: statusText,
                meta: meta
            };
        });

        console.log('Dynamic Leave Data:', leaveDataList);

        updateUsedLeave();

        currentPage = 1;
        renderLeaveItems(currentPage);

        renderPanel('casual');

    } catch (error) {
        console.log('Error loading leave data:', error);
    }
}


function formatDate(dateString) {

    if (!dateString) {
        return '';
    }

    const date = new Date(dateString + 'T00:00:00');

    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: '2-digit',
        year: 'numeric'
    });
}


function formatTime(timeString) {

    if (!timeString) {
        return '';
    }

    const [hours, minutes] = timeString.split(':');

    const date = new Date();

    date.setHours(
        parseInt(hours),
        parseInt(minutes),
        0,
        0
    );

    return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit'
    });
}


function renderLeaveItems(page) {
    const start = (page - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const pageItems = leaveDataList.slice(start, end);

    leaveList.innerHTML = pageItems.length === 0
    ? `
        <div class="lp-no-leaves">
            No leave request found.
        </div>
      `
    : pageItems.map(item => {
        const statusClass = statusClasses[item.status] || '';
        const borderColor = typeColorMap[item.type] || 'var(--gray-400)';
        const dotColor = statusColors[item.status] || 'var(--gray-400)';

        const cancelButton = item.status === 'pending'
        ? `
            <form method="POST"
                    action="/medical/cancel_leave/${item.uuid}/"
                    class="lp-cancel-form">

                <input type="hidden" name="csrfmiddlewaretoken" value="${getCSRFToken()}">

                <button type="submit" class="lp-cancel-btn">
                    Cancel
                </button>
            </form>
            `
        : '';
        
        return `
            <div class="lp-leave-row" style="--row-color: ${borderColor};">
                <div class="lp-leave-type">
                    <span class="lp-chip-dot" style="background: ${dotColor};"></span>${item.type}
                </div>
                <div class="lp-leave-dates">${item.dates}</div>
                <div class="lp-leave-reason">${item.reason}</div>
                <span class="lp-status-badge ${statusClass}">${item.statusText}</span>
                ${item.meta ? `<div class="lp-leave-meta">${item.meta}</div>` : ''}
                ${cancelButton}
            </div>
        `;
    }).join('');

    updatePagination(page);
}

function getCSRFToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='));

    return cookieValue
        ? decodeURIComponent(cookieValue.split('=')[1])
        : '';
}

function updatePagination(current) {
    
    const totalPages = Math.ceil(leaveDataList.length / itemsPerPage);

    if (leaveDataList.length > itemsPerPage) {
        document.getElementById('pagination').style.display = '';
    } else {
        document.getElementById('pagination').style.display = 'none';
    }

    if (totalPages === 0) {
        pageNumbers.innerHTML = '';
        prevBtn.disabled = true;
        nextBtn.disabled = true;
        return;
    }

    prevBtn.disabled = current === 1;
    nextBtn.disabled = current === totalPages;

    let pagesHTML = '';
    
    if (totalPages <= 7) {
        for (let i = 1; i <= totalPages; i++) {
            pagesHTML += `<button class="lp-page-number ${i === current ? 'active' : ''}" data-page="${i}">${i}</button>`;
        }
    } else {
        pagesHTML += `<button class="lp-page-number ${1 === current ? 'active' : ''}" data-page="1">1</button>`;
        
        if (current > 3) {
            pagesHTML += `<span class="lp-page-number ellipsis">…</span>`;
        }
        
        let startPage = Math.max(2, current - 1);
        let endPage = Math.min(totalPages - 1, current + 1);
        
        if (current <= 3) {
            endPage = 4;
        }
        if (current >= totalPages - 2) {
            startPage = totalPages - 3;
        }
        
        for (let i = startPage; i <= endPage; i++) {
            pagesHTML += `<button class="lp-page-number ${i === current ? 'active' : ''}" data-page="${i}">${i}</button>`;
        }
        
        if (current < totalPages - 2) {
            pagesHTML += `<span class="lp-page-number ellipsis">…</span>`;
        }
        
        pagesHTML += `<button class="lp-page-number ${totalPages === current ? 'active' : ''}" data-page="${totalPages}">${totalPages}</button>`;
    }
    
    pageNumbers.innerHTML = pagesHTML;

    document.querySelectorAll('.lp-page-number[data-page]').forEach(btn => {
        btn.addEventListener('click', function() {
            const page = parseInt(this.dataset.page);
            if (page !== currentPage) {
                currentPage = page;
                renderLeaveItems(currentPage);

                document.querySelector('.lp-leave-list-container')?.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start' 
                });
            }
        });
    });
}

prevBtn.addEventListener('click', function() {
    if (currentPage > 1) {
        currentPage--;
        renderLeaveItems(currentPage);
    }
});

nextBtn.addEventListener('click', function() {
    const totalPages = Math.ceil(
        leaveDataList.length / itemsPerPage
    );

    if (currentPage < totalPages) {
        currentPage++;
        renderLeaveItems(currentPage);
    }
});


document.addEventListener('DOMContentLoaded', function () {

    loadLeaveData();
    
    AOS.init({
        duration: 800,
        easing: 'ease-out-cubic',
        once: true,
        offset: 50
    });
});