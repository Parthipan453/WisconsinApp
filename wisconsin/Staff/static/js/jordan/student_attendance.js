let currentData = [];
let selectedCourse = null;
let currentPage = 1;
let currentSemesterId = '';
let choicesInstances = {};
const itemsPerPage = 10;
let individualDepartments = [];  
let individualPrograms = [];     
let individualStudents = [];     

document.addEventListener('DOMContentLoaded', function() {
    loadData();
    setupEventListeners();
    initializeChoices();
});

function initializeChoices() {
    document.querySelectorAll('select').forEach(function (select) {
        if (select.dataset.choicesInitialized) return;

        const instance = new Choices(select, {
            searchEnabled: true,
            itemSelectText: '',
            shouldSort: false,
            allowHTML: false,
            searchPlaceholderValue: 'Search...',
            noResultsText: 'No results found',
            noChoicesText: 'No options available'
        });

        choicesInstances[select.id] = instance;
        select.choicesInstance = instance;
        select.dataset.choicesInitialized = 'true';
    });
}

function refreshChoicesFromSelect(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return;

    const instance = choicesInstances[selectId];
    if (!instance) return;

    const currentValue = select.value;

    const choicesData = Array.from(select.options)
        .filter(opt => !opt.hidden)
        .map(opt => ({
            value: opt.value,
            label: opt.textContent,
            selected: opt.value === currentValue,
            disabled: false
        }));

    instance.clearStore();
    instance.setChoices(choicesData, 'value', 'label', true);
}

function setChoicesFromList(selectId, items, selectedValue) {
    const select = document.getElementById(selectId);
    const instance = choicesInstances[selectId];
    if (!select) return;

    if (instance) {
        const choicesData = items.map(item => ({
            value: item.value,
            label: item.label,
            selected: item.value === selectedValue,
            disabled: false
        }));
        instance.clearStore();
        instance.setChoices(choicesData, 'value', 'label', true);
    } else {
        select.innerHTML = '';
        items.forEach(item => {
            const opt = document.createElement('option');
            opt.value = item.value;
            opt.textContent = item.label;
            if (item.value === selectedValue) opt.selected = true;
            select.appendChild(opt);
        });
    }
}

function setupEventListeners() {
    // Enter key on search
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                applySearch();
            }
        });
    }

    // Main filter change events (course grid level)
    const mainFilterIds = [
        'semesterFilter',
        'courseFilter',
        'facultyFilter',
        'departmentFilter',
        'programFilter'
    ];

    mainFilterIds.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', function() {
                applyFilters();
            });
        }
    });

    // Status filter lives inside the opened Attendance Table (student list),
    // same pattern as gradebook's Grade filter — it re-filters the CURRENTLY
    // selected course's students, not the whole course grid.
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            applyStudentFilters();
        });
    }

    // Date filter — re-filters the CURRENTLY selected course's student list,
    // and changes which date's status the Status filter/column reflects.
    const dateFilter = document.getElementById('dateFilter');
    if (dateFilter) {
        dateFilter.addEventListener('change', function() {
            applyStudentFilters();
        });
    }

    if (searchInput) {
        searchInput.addEventListener('input', function() {
            applyStudentFilters();
        });
    }

    // Individual Student Attendance cascading filters
    const individualDept = document.getElementById('individualDepartmentFilter');
    const individualProgram = document.getElementById('individualProgramFilter');

    if (individualDept) {
        individualDept.addEventListener('change', applyIndividualCascadeFilter);
    }
    if (individualProgram) {
        individualProgram.addEventListener('change', applyIndividualCascadeFilter);
    }
}

function loadData() {
    const dataEl = document.getElementById('courses-data');
    const currentSemesterEl = document.getElementById('current-semester-id');

    if (!dataEl) {
        console.error('courses-data not found');
        return;
    }

    currentData = JSON.parse(dataEl.textContent);
    currentSemesterId = currentSemesterEl ? JSON.parse(currentSemesterEl.textContent) : '';

    populateSemesterFilter(currentData);
    populateCourseFilter(currentData);
    populateFacultyFilter(currentData);
    populateDepartmentFilter(currentData);
    populateProgramFilter(currentData);
    buildIndividualMasterLists(currentData);
    renderIndividualFilterOptions();

    const semesterSelect = document.getElementById('semesterFilter');
    if (semesterSelect && currentSemesterId) {
        semesterSelect.value = currentSemesterId;
        refreshChoicesFromSelect('semesterFilter');
    }

    updateMonthLabel();
    updateSummaryDate();

    applyFilters(true);
}

function populateSemesterFilter(courses) {
    const select = document.getElementById('semesterFilter');
    if (!select) return;

    select.innerHTML = '<option value="">All Semesters</option>';
    const seen = new Set();

    courses.forEach(course => {
        const sem = (course.semester || '').trim();
        const semId = String(course.semesterId || '').trim();

        if (sem && sem !== 'Not assigned' && !seen.has(semId || sem.toLowerCase())) {
            seen.add(semId || sem.toLowerCase());
            const option = document.createElement('option');
            option.value = semId || sem.toLowerCase();
            option.textContent = (semId && semId === currentSemesterId) ? `${sem} (Current)` : sem;
            select.appendChild(option);
        }
    });

    refreshChoicesFromSelect('semesterFilter');
}

function populateCourseFilter(courses) {
    const select = document.getElementById('courseFilter');
    if (!select) return;

    select.innerHTML = '<option value="">All Courses</option>';
    const seen = new Set();

    courses.forEach(course => {
        const name = (course.name || '').trim();
        const code = (course.code || course.subject || '').trim();

        if (name && !seen.has(name.toLowerCase())) {
            seen.add(name.toLowerCase());
            const option = document.createElement('option');
            option.value = name.toLowerCase();
            option.textContent = code ? `${code} - ${name}` : name;
            select.appendChild(option);
        }
    });

    refreshChoicesFromSelect('courseFilter');
}

function populateFacultyFilter(courses) {
    const select = document.getElementById('facultyFilter');
    if (!select) return;

    select.innerHTML = '<option value="">All Faculty</option>';
    const seen = new Set();

    courses.forEach(course => {
        const faculty = (course.faculty || '').trim();
        const facultyId = String(course.facultyId || '').trim();

        if (faculty && faculty !== 'Not assigned' && !seen.has(facultyId || faculty.toLowerCase())) {
            seen.add(facultyId || faculty.toLowerCase());
            const option = document.createElement('option');
            option.value = facultyId || faculty.toLowerCase();
            option.textContent = faculty;
            select.appendChild(option);
        }
    });

    refreshChoicesFromSelect('facultyFilter');
}

function populateDepartmentFilter(courses) {
    const select = document.getElementById('departmentFilter');
    if (!select) return;

    select.innerHTML = '<option value="">All Departments</option>';
    const seen = new Set();

    courses.forEach(course => {
        const dept = (course.department || '').trim();
        const deptId = String(course.departmentId || '').trim();

        if (dept && dept !== 'Not assigned' && !seen.has(deptId || dept.toLowerCase())) {
            seen.add(deptId || dept.toLowerCase());
            const option = document.createElement('option');
            option.value = deptId || dept.toLowerCase();
            option.textContent = dept;
            select.appendChild(option);
        }
    });

    refreshChoicesFromSelect('departmentFilter');
}

function populateProgramFilter(courses) {
    const select = document.getElementById('programFilter');
    if (!select) return;

    select.innerHTML = '<option value="">All Programs</option>';
    const seen = new Set();

    courses.forEach(course => {
        (course.students || []).forEach(student => {
            const program = (student.program || '').trim();
            const programId = String(student.programId || '').trim();

            if (program && program !== 'Not assigned' && !seen.has(programId || program.toLowerCase())) {
                seen.add(programId || program.toLowerCase());
                const option = document.createElement('option');
                option.value = programId || program.toLowerCase();
                option.textContent = program;
                select.appendChild(option);
            }
        });
    });

    refreshChoicesFromSelect('programFilter');
}

// Populates the Date filter for the CURRENTLY opened course, from that
// course's list of attendance sessions (course.sessions = [{id, date}]).
// Newest date first.
function populateDateFilter(sessions) {
    const select = document.getElementById('dateFilter');
    if (!select) return;

    select.innerHTML = '<option value="">All Dates</option>';

    const sorted = [...(sessions || [])].sort((a, b) => b.date.localeCompare(a.date));
    sorted.forEach(session => {
        const option = document.createElement('option');
        option.value = session.date;
        option.textContent = formatDateLabel(session.date);
        select.appendChild(option);
    });

    select.value = '';
    refreshChoicesFromSelect('dateFilter');
}

function formatDateLabel(isoDate) {
    const d = new Date(isoDate + 'T00:00:00');
    if (isNaN(d.getTime())) return isoDate;
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function renderCourseCards(courses) {
    const grid = document.getElementById('courseGrid');
    grid.innerHTML = '';

    if (!courses || courses.length === 0) {
        grid.innerHTML = `
            <div class="empty-state" style="grid-column: 1/-1;">
                <i class="ti ti-book-off"></i>
                <p>No courses found</p>
                <span class="empty-sub">Try adjusting your filters</span>
            </div>
        `;
        return;
    }

    courses.forEach(course => {
        const students = course.students || [];
        const presentCount = students.filter(s => s.status === 'present').length;
        const absentCount = students.filter(s => s.status === 'absent').length;
        const lateCount = students.filter(s => s.status === 'late').length;
        const leaveCount = students.filter(s => s.status === 'leave' || s.status === 'half-day' || s.status === 'permission').length;
        const totalStudents = students.length;

        // Course-wide average attendance % — mean of each student's own
        // attendancePercent field (already sent by the view).
        const withPct = students.filter(s => s.attendancePercent !== undefined && s.attendancePercent !== null);
        const avgAttendance = withPct.length
            ? Math.round(withPct.reduce((sum, s) => sum + s.attendancePercent, 0) / withPct.length)
            : 0;

        const professorInitials = course.faculty ? course.faculty.split(' ').map(word => word[0]).join('') : 'NA';

        const card = document.createElement('div');
        card.className = 'course-card';
        card.onclick = () => showAttendanceTable(course);

        card.innerHTML = `
            <div class="course-header">
                <div>
                    <h4 class="course-title">${course.name}</h4>
                    <span class="course-code-badge">${course.code || 'N/A'}</span>
                </div>
                <div class="professor-badge" title="${course.faculty || 'Not assigned'}">
                    <span class="professor-initials">${professorInitials}</span>
                    <span class="professor-name">${course.faculty || 'Not assigned'}</span>
                </div>
            </div>
            <p class="course-subject">
                <i class="ti ti-layout-grid"></i>
                Section ${course.section || 'N/A'}
            </p>
            <div class="course-attendance-badge">
                <i class="ti ti-chart-donut"></i>
                <span>${avgAttendance}% Avg Attendance</span>
            </div>
            <div class="course-stats-inline">
                <div class="stat-item-inline">
                    <span class="stat-value text-blue">${totalStudents}</span>
                    <span class="stat-label">Total</span>
                </div>
                <div class="stat-item-inline">
                    <span class="stat-value text-green">${presentCount}</span>
                    <span class="stat-label">Present</span>
                </div>
                <div class="stat-item-inline">
                    <span class="stat-value text-red">${absentCount}</span>
                    <span class="stat-label">Absent</span>
                </div>
                <div class="stat-item-inline">
                    <span class="stat-value text-orange">${lateCount}</span>
                    <span class="stat-label">Late</span>
                </div>
                <div class="stat-item-inline">
                    <span class="stat-value text-purple">${leaveCount}</span>
                    <span class="stat-label">Leave</span>
                </div>
            </div>
            <div class="course-footer">
                <span class="course-date">
                    <i class="ti ti-calendar"></i>
                    ${course.semester || 'N/A'}
                </span>
                <span class="view-details-link">
                    View Details <i class="ti ti-chevron-right"></i>
                </span>
            </div>
        `;
        grid.appendChild(card);
    });
}

function updateStats(courses) {
    let totalStudents = 0;
    let totalPresent = 0;
    let totalAbsent = 0;
    let totalLate = 0;

    courses.forEach(course => {
        if (course.students) {
            course.students.forEach(student => {
                totalStudents++;
                if (student.status === 'present') totalPresent++;
                else if (student.status === 'absent') totalAbsent++;
                else if (student.status === 'late') totalLate++;
            });
        }
    });

    animateNumber('statTotalStudents', totalStudents);
    animateNumber('statPresentStudents', totalPresent);
    animateNumber('statAbsentStudents', totalAbsent);
    animateNumber('statLateStudents', totalLate);
}

function animateNumber(elementId, targetValue) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const currentValue = parseInt(element.textContent) || 0;
    const duration = 500;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(currentValue + (targetValue - currentValue) * eased);

        element.textContent = current;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

function updateCourseCount(count) {
    const badge = document.getElementById('courseCount');
    if (badge) {
        badge.textContent = `${count} Courses`;
    }
}

function updateMonthLabel() {
    const now = new Date();
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December'];
    const label = document.getElementById('currentMonthLabel');
    if (label) {
        label.textContent = `${monthNames[now.getMonth()]} ${now.getFullYear()}`;
    }
}

function updateSummaryDate() {
    const now = new Date();
    const options = { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' };
    const label = document.getElementById('summaryDate');
    if (label) {
        label.textContent = now.toLocaleDateString('en-US', options);
    }
}

function updateMonthlyStats(courses) {
    let present = 0, absent = 0, late = 0, halfDay = 0;
    let total = 0;

    courses.forEach(course => {
        if (course.students) {
            course.students.forEach(student => {
                total++;
                if (student.status === 'present') present++;
                else if (student.status === 'absent') absent++;
                else if (student.status === 'late') late++;
                else if (student.status === 'half-day') halfDay++;
            });
        }
    });

    const totalStudents = total > 0 ? total : 1;
    const presentPercent = Math.round((present / totalStudents) * 100);
    const absentPercent = Math.round((absent / totalStudents) * 100);
    const latePercent = Math.round((late / totalStudents) * 100);
    const halfDayPercent = Math.round((halfDay / totalStudents) * 100);

    document.getElementById('presentBar').style.width = Math.min(presentPercent, 100) + '%';
    document.getElementById('absentBar').style.width = Math.min(absentPercent, 100) + '%';
    document.getElementById('lateBar').style.width = Math.min(latePercent, 100) + '%';
    document.getElementById('halfdayBar').style.width = Math.min(halfDayPercent, 100) + '%';

    document.getElementById('presentPercent').textContent = presentPercent + '%';
    document.getElementById('absentPercent').textContent = absentPercent + '%';
    document.getElementById('latePercent').textContent = latePercent + '%';
    document.getElementById('halfdayPercent').textContent = halfDayPercent + '%';
}

function updateSummary(courses) {
    let totalStudents = 0;
    let present = 0;
    let absent = 0;
    let late = 0;
    let leave = 0;

    courses.forEach(course => {
        if (course.students) {
            course.students.forEach(student => {
                totalStudents++;
                if (student.status === 'present') present++;
                else if (student.status === 'absent') absent++;
                else if (student.status === 'late') late++;
                else if (student.status === 'leave' || student.status === 'half-day' || student.status === 'permission') leave++;
            });
        }
    });

    const attendanceRate = totalStudents > 0 ? Math.round((present / totalStudents) * 100) : 0;

    document.getElementById('summaryTotalStudents').textContent = totalStudents;
    document.getElementById('summaryPresent').textContent = present;
    document.getElementById('summaryAbsent').textContent = absent;
    document.getElementById('summaryLate').textContent = late;
    document.getElementById('summaryLeave').textContent = leave;
    document.getElementById('summaryAttendanceRate').textContent = attendanceRate + '%';
}

function showAttendanceTable(course) {
    if (!course) return;

    selectedCourse = course;
    const wrapper = document.getElementById('attendanceTableWrapper');

    document.getElementById('selectedCourseTitle').textContent = course.name;
    document.getElementById('facultyName').textContent = course.faculty || 'Not assigned';
    document.getElementById('courseCode').textContent = course.code || 'N/A';
    document.getElementById('courseSchedule').textContent = course.schedule || 'N/A';
    document.getElementById('courseRoom').textContent = course.room || 'N/A';

    // Subject-level overall attendance = average of each enrolled student's
    // overall attendance % in this course.
    const students = course.students || [];
    const overallEl = document.getElementById('courseOverallAttendance');
    if (overallEl) {
        const overallAttendance = students.length
            ? Math.round(students.reduce((sum, s) => sum + (s.attendancePercent || 0), 0) / students.length)
            : 0;
        overallEl.textContent = students.length ? overallAttendance + '%' : '—';
    }

    document.getElementById('searchInput').value = '';
    const statusSelect = document.getElementById('statusFilter');
    if (statusSelect) {
        statusSelect.value = '';
        refreshChoicesFromSelect('statusFilter');
    }

    // Date filter rebuilt fresh per course from its session list.
    populateDateFilter(course.sessions || []);

    wrapper.style.display = 'block';
    currentPage = 1;
    renderAttendanceTable(students, course, '');

    setTimeout(() => {
        wrapper.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }, 100);
}

function applyStudentFilters() {
    if (!selectedCourse) return;

    const statusElement = document.getElementById('statusFilter');
    const searchElement = document.getElementById('searchInput');
    const dateFrom = document.getElementById('dateFromFilter').value;
    const dateTo = document.getElementById('dateToFilter').value;

    const statusFilter = statusElement ? statusElement.value : '';
    const searchQuery = searchElement ? searchElement.value.toLowerCase().trim() : '';

    let students = (selectedCourse.students || []).map(student => {
        const allRecords = student.records || {};

        if (!dateFrom && !dateTo) {
            return student;
        }

        const filteredDates = Object.keys(allRecords).filter(date => {
            if (dateFrom && date < dateFrom) return false;
            if (dateTo && date > dateTo) return false;
            return true;
        });

        const totalSessions = filteredDates.length;
        const presentCount = filteredDates.filter(d => allRecords[d] === 'present').length;
        const attendancePercent = totalSessions
            ? Math.round((presentCount / totalSessions) * 100)
            : 0;

        const latestDateInRange = filteredDates.length
            ? filteredDates.sort().slice(-1)[0]
            : null;
        const latestStatus = latestDateInRange ? allRecords[latestDateInRange] : '';

        return {
            ...student,
            date: latestDateInRange || '',
            status: latestStatus,
            attendancePercent: attendancePercent,
            totalSessions: totalSessions,
            presentCount: presentCount,
        };
    }).filter(student => {
        if ((dateFrom || dateTo) && student.totalSessions === 0) return false;
        return true;
    });

    if (statusFilter) {
        students = students.filter(student => student.status === statusFilter);
    }

    if (searchQuery) {
        students = students.filter(student =>
            (student.name || '').toLowerCase().includes(searchQuery) ||
            String(student.rollNo || '').toLowerCase().includes(searchQuery)
        );
    }

    currentPage = 1;
    renderAttendanceTable(students, selectedCourse);
}

// selectedDate: '' means "no specific date chosen" -> show each student's
// latest/default status. Otherwise show that date's specific record.
function renderAttendanceTable(students, course, selectedDate = '') {
    const tbody = document.getElementById('attendanceTableBody');
    tbody.innerHTML = '';

    if (!students || students.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px; color: var(--text-secondary);">
                    <i class="ti ti-users" style="font-size: 32px; color: var(--text-light); display: block; margin-bottom: 12px;"></i>
                    No attendance records found for this course.
                </td>
            </tr>
        `;
        document.getElementById('paginationInfo').textContent = 'Showing 0 to 0 of 0 entries';
        return;
    }

    const totalItems = students.length;
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
    const pageItems = students.slice(startIndex, endIndex);

    const statusConfig = {
        present: { class: 'present', icon: 'ti ti-check', label: 'Present' },
        absent: { class: 'absent', icon: 'ti ti-x', label: 'Absent' },
        late: { class: 'late', icon: 'ti ti-clock', label: 'Late' },
        'half-day': { class: 'half-day', icon: 'ti ti-clock-half', label: 'Half Day' },
        leave: { class: 'leave', icon: 'ti ti-calendar-off', label: 'Leave' },
        permission: { class: 'permission', icon: 'ti ti-file-check', label: 'Permission' }
    };

    pageItems.forEach((student, index) => {
        const row = document.createElement('tr');

        const effectiveStatus = selectedDate
            ? (student.records ? student.records[selectedDate] : undefined)
            : student.status;

        const statusCell = effectiveStatus
            ? (() => {
                const config = statusConfig[effectiveStatus] || statusConfig.present;
                return `
                    <div class="status-badge ${config.class}">
                        <i class="${config.icon}"></i>
                        ${config.label}
                    </div>
                `;
            })()
            : `<span style="color: var(--text-light);">No session</span>`;

        const attendancePercentCell = typeof student.attendancePercent === 'number'
            ? `${student.attendancePercent}%`
            : '—';

        row.innerHTML = `
            <td>${startIndex + index + 1}</td>
            <td><strong>${student.name}</strong></td>
            <td>${student.rollNo}</td>
            <td>${course ? course.name : 'N/A'}</td>
            <td>${course ? course.faculty || 'Not assigned' : 'N/A'}</td>
            <td>${attendancePercentCell}</td>
            <td>${statusCell}</td>
        `;
        tbody.appendChild(row);
    });

    document.getElementById('paginationInfo').textContent =
        `Showing ${startIndex + 1} to ${endIndex} of ${totalItems} entries`;

    renderPagination(totalPages);
}

function renderPagination(totalPages) {
    const controls = document.getElementById('paginationControls');
    controls.innerHTML = '';

    if (currentPage > 1) {
        const prevFirst = document.createElement('a');
        prevFirst.href = '#';
        prevFirst.className = 'page-link pagination-link';
        prevFirst.dataset.page = '1';
        prevFirst.innerHTML = '&laquo;';
        prevFirst.onclick = (e) => { e.preventDefault(); goToPage(1); };
        controls.appendChild(prevFirst);

        const prev = document.createElement('a');
        prev.href = '#';
        prev.className = 'page-link pagination-link';
        prev.dataset.page = currentPage - 1;
        prev.innerHTML = '&lsaquo;';
        prev.onclick = (e) => { e.preventDefault(); goToPage(currentPage - 1); };
        controls.appendChild(prev);
    } else {
        controls.innerHTML += `<span class="page-link disabled">&laquo;</span>`;
        controls.innerHTML += `<span class="page-link disabled">&lsaquo;</span>`;
    }

    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    for (let i = startPage; i <= endPage; i++) {
        const pageLink = document.createElement('span');
        if (i === currentPage) {
            pageLink.className = 'page-link active';
            pageLink.textContent = i;
        } else {
            pageLink.className = 'page-link pagination-link';
            pageLink.textContent = i;
            pageLink.onclick = (e) => { e.preventDefault(); goToPage(i); };
        }
        controls.appendChild(pageLink);
    }

    if (currentPage < totalPages) {
        const next = document.createElement('a');
        next.href = '#';
        next.className = 'page-link pagination-link';
        next.dataset.page = currentPage + 1;
        next.innerHTML = '&rsaquo;';
        next.onclick = (e) => { e.preventDefault(); goToPage(currentPage + 1); };
        controls.appendChild(next);

        const nextLast = document.createElement('a');
        nextLast.href = '#';
        nextLast.className = 'page-link pagination-link';
        nextLast.dataset.page = totalPages;
        nextLast.innerHTML = '&raquo;';
        nextLast.onclick = (e) => { e.preventDefault(); goToPage(totalPages); };
        controls.appendChild(nextLast);
    } else {
        controls.innerHTML += `<span class="page-link disabled">&rsaquo;</span>`;
        controls.innerHTML += `<span class="page-link disabled">&raquo;</span>`;
    }
}

function goToPage(page) {
    if (!selectedCourse) return;
    currentPage = page;
    const dateElement = document.getElementById('dateFilter');
    const dateFilter = dateElement ? dateElement.value : '';
    renderAttendanceTable(selectedCourse.students || [], selectedCourse, dateFilter);
}

// Course-grid level filters ONLY (Semester/Course/Faculty/Department/
// Program). Status + Date + Search now live on the opened student table and
// are handled by applyStudentFilters() instead — same split as gradebook.
// NOTE: the old buggy `if (dayFilter)` block (referencing a variable that
// no longer exists after the Day filter was removed from the template) has
// been deleted — that ReferenceError was why course cards stopped
// rendering entirely.
function applyFilters(silent = false) {
    const semesterFilter = document.getElementById('semesterFilter').value.toLowerCase().trim();
    const courseFilter = document.getElementById('courseFilter').value.toLowerCase().trim();
    const facultyFilter = document.getElementById('facultyFilter').value.toLowerCase().trim();
    const departmentFilter = document.getElementById('departmentFilter').value.toLowerCase().trim();
    const programFilter = document.getElementById('programFilter').value.toLowerCase().trim();

    let filtered = JSON.parse(JSON.stringify(currentData));

    if (semesterFilter) {
        filtered = filtered.filter(course => {
            const semId = String(course.semesterId || '').toLowerCase();
            const semName = (course.semester || '').toLowerCase();
            return semId === semesterFilter || semName === semesterFilter;
        });
    }

    if (courseFilter) {
        filtered = filtered.filter(course =>
            course.name.toLowerCase().includes(courseFilter) ||
            (course.subject && course.subject.toLowerCase().includes(courseFilter))
        );
    }

    if (facultyFilter) {
        filtered = filtered.filter(course => {
            const fid = String(course.facultyId || '').toLowerCase();
            const fname = (course.faculty || '').toLowerCase();
            return fid === facultyFilter || fname === facultyFilter;
        });
    }

    if (departmentFilter) {
        filtered = filtered.filter(course => {
            const deptId = String(course.departmentId || '').toLowerCase();
            const deptName = (course.department || '').toLowerCase();
            return deptId === departmentFilter || deptName === departmentFilter;
        });
    }

    if (programFilter) {
        filtered = filtered.map(course => {
            const students = (course.students || []).filter(student => {
                const pid = String(student.programId || '').toLowerCase();
                const pname = (student.program || '').toLowerCase();
                return pid === programFilter || pname === programFilter;
            });
            return { ...course, students };
        }).filter(course => course.students && course.students.length > 0);
    }

    renderCourseCards(filtered);
    updateStats(filtered);
    updateCourseCount(filtered.length);
    updateMonthlyStats(filtered);
    updateSummary(filtered);

    const wrapper = document.getElementById('attendanceTableWrapper');
    if (wrapper.style.display !== 'none') {
        wrapper.style.display = 'none';
        selectedCourse = null;
    }

    if (silent) return;

    if (filtered.length === 0) {
        showNotification('No courses match your filters.', 'warning');
    } else {
        showNotification(`Found ${filtered.length} course(s) matching your filters.`, 'info');
    }
}

function applySearch() {
    applyStudentFilters();
}

function resetFilters() {
    document.getElementById('semesterFilter').value = currentSemesterId || '';
    document.getElementById('courseFilter').value = '';
    document.getElementById('facultyFilter').value = '';
    document.getElementById('departmentFilter').value = '';
    document.getElementById('programFilter').value = '';

    ['semesterFilter', 'courseFilter', 'facultyFilter', 'departmentFilter', 'programFilter']
        .forEach(refreshChoicesFromSelect);

    const dateSelect = document.getElementById('dateFilter');
    if (dateSelect) {
        dateSelect.value = '';
        refreshChoicesFromSelect('dateFilter');
    }

    document.getElementById('attendanceTableWrapper').style.display = 'none';
    selectedCourse = null;

    applyFilters(true);
    showNotification('Filters reset to the current semester.', 'info');
}

function refreshData() {
    showLoading();
    setTimeout(() => {
        loadData();
        document.getElementById('attendanceTableWrapper').style.display = 'none';
        selectedCourse = null;
        hideLoading();
        showNotification('Data refreshed successfully!', 'success');
    }, 500);
}

function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.style.display = 'flex';
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.style.display = 'none';
}

function closeTable() {
    document.getElementById('attendanceTableWrapper').style.display = 'none';
    selectedCourse = null;
}

function exportData(type) {
    if (type === 'excel') {
        exportToExcel();
    } else if (type === 'pdf') {
        exportToPDF();
    }
}

function exportToExcel() {
    if (!selectedCourse) {
        showNotification('Please select a course first.', 'error');
        return;
    }

    try {
        const excelData = [
            ['Attendance Report'],
            [`Course: ${selectedCourse.name}`],
            [`Subject: ${selectedCourse.subject || ''}`],
            [`Course Code: ${selectedCourse.code || 'N/A'}`],
            [`Faculty: ${selectedCourse.faculty || 'Not assigned'}`],
            [`Schedule: ${selectedCourse.schedule || 'N/A'}`],
            [`Room: ${selectedCourse.room || 'N/A'}`],
            [`Generated: ${new Date().toLocaleString()}`],
            [],
            ['#', 'Student Name', 'Student ID', 'Course', 'Faculty', 'Attendance %', 'Status']
        ];

        const students = selectedCourse.students || [];
        students.forEach((student, index) => {
            excelData.push([
                index + 1,
                student.name,
                student.rollNo,
                selectedCourse.name,
                selectedCourse.faculty || 'Not assigned',
                typeof student.attendancePercent === 'number' ? student.attendancePercent + '%' : '',
                (student.status || '').toUpperCase()
            ]);
        });

        const presentCount = students.filter(s => s.status === 'present').length;
        const absentCount = students.filter(s => s.status === 'absent').length;
        const lateCount = students.filter(s => s.status === 'late').length;
        const leaveCount = students.filter(s => s.status === 'leave' || s.status === 'half-day' || s.status === 'permission').length;
        const overallAttendance = students.length
            ? Math.round(students.reduce((sum, s) => sum + (s.attendancePercent || 0), 0) / students.length)
            : 0;

        excelData.push([]);
        excelData.push(['Summary']);
        excelData.push(['Total Students', students.length]);
        excelData.push(['Present (latest session)', presentCount]);
        excelData.push(['Absent (latest session)', absentCount]);
        excelData.push(['Late (latest session)', lateCount]);
        excelData.push(['On Leave (latest session)', leaveCount]);
        excelData.push(['Overall Attendance Rate', overallAttendance + '%']);

        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.aoa_to_sheet(excelData);

        ws['!cols'] = [
            { wch: 5 }, { wch: 25 }, { wch: 15 }, { wch: 20 }, { wch: 20 }, { wch: 14 }, { wch: 12 }
        ];

        XLSX.utils.book_append_sheet(wb, ws, 'Attendance');

        const fileName = `${selectedCourse.name}_Attendance_${new Date().toISOString().split('T')[0]}.xlsx`;
        XLSX.writeFile(wb, fileName);

        showNotification('Excel export completed successfully!', 'success');
    } catch (error) {
        console.error('Excel export error:', error);
        showNotification('Error exporting to Excel. Please try again.', 'error');
    }
}

function exportToPDF() {
    if (!selectedCourse) {
        showNotification('Please select a course first.', 'error');
        return;
    }

    try {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF('landscape', 'mm', 'a4');

        doc.setFontSize(18);
        doc.setTextColor(15, 23, 42);
        doc.text(`Attendance Report: ${selectedCourse.name}`, 14, 20);

        doc.setFontSize(11);
        doc.setTextColor(100, 116, 139);
        let y = 28;

        const details = [
            `Course Code: ${selectedCourse.code || 'N/A'}`,
            `Subject: ${selectedCourse.subject || ''}`,
            `Faculty: ${selectedCourse.faculty || 'Not assigned'}`,
            `Schedule: ${selectedCourse.schedule || 'N/A'}`,
            `Room: ${selectedCourse.room || 'N/A'}`,
            `Generated: ${new Date().toLocaleString()}`
        ];

        details.forEach(detail => {
            doc.text(detail, 14, y);
            y += 6;
        });

        const students = selectedCourse.students || [];
        const tableHeaders = ['#', 'Student Name', 'Student ID', 'Course', 'Faculty', 'Attendance %', 'Status'];
        const tableRows = students.map((student, index) => [
            index + 1,
            student.name,
            student.rollNo,
            selectedCourse.name,
            selectedCourse.faculty || 'Not assigned',
            typeof student.attendancePercent === 'number' ? student.attendancePercent + '%' : '—',
            (student.status || '').toUpperCase() || '—'
        ]);

        doc.autoTable({
            startY: y + 4,
            head: [tableHeaders],
            body: tableRows,
            theme: 'striped',
            headStyles: { fillColor: [37, 99, 235], textColor: [255, 255, 255], fontSize: 10, fontStyle: 'bold' },
            bodyStyles: { fontSize: 9 },
            columnStyles: {
                0: { cellWidth: 10 }, 1: { cellWidth: 35 }, 2: { cellWidth: 25 },
                3: { cellWidth: 30 }, 4: { cellWidth: 30 }, 5: { cellWidth: 22 }, 6: { cellWidth: 18 }
            }
        });

        const finalY = doc.lastAutoTable.finalY || y + 50;

        const presentCount = students.filter(s => s.status === 'present').length;
        const absentCount = students.filter(s => s.status === 'absent').length;
        const lateCount = students.filter(s => s.status === 'late').length;
        const leaveCount = students.filter(s => s.status === 'leave' || s.status === 'half-day' || s.status === 'permission').length;
        const overallAttendance = students.length
            ? Math.round(students.reduce((sum, s) => sum + (s.attendancePercent || 0), 0) / students.length)
            : 0;

        doc.setFontSize(11);
        doc.setTextColor(15, 23, 42);
        doc.text('Summary', 14, finalY + 12);

        doc.setFontSize(10);
        doc.setTextColor(100, 116, 139);
        doc.text(`Total Students: ${students.length}`, 14, finalY + 20);
        doc.text(`Present (latest session): ${presentCount}`, 14, finalY + 28);
        doc.text(`Absent (latest session): ${absentCount}`, 14, finalY + 36);
        doc.text(`Late (latest session): ${lateCount}`, 14, finalY + 44);
        doc.text(`On Leave (latest session): ${leaveCount}`, 14, finalY + 52);
        doc.text(`Overall Attendance Rate: ${overallAttendance}%`, 14, finalY + 60);

        const fileName = `${selectedCourse.name}_Attendance_${new Date().toISOString().split('T')[0]}.pdf`;
        doc.save(fileName);

        showNotification('PDF export completed successfully!', 'success');
    } catch (error) {
        console.error('PDF export error:', error);
        showNotification('Error exporting to PDF. Please try again.', 'error');
    }
}

function showNotification(message, type = 'info') {
    const existing = document.querySelector('.custom-notification');
    if (existing) existing.remove();

    const notification = document.createElement('div');
    notification.className = 'custom-notification';

    const colors = { success: '#22c55e', error: '#ef4444', info: '#3b82f6', warning: '#f97316' };
    const icons = {
        success: 'ti ti-check-circle', error: 'ti ti-exclamation-circle',
        info: 'ti ti-info-circle', warning: 'ti ti-alert-circle'
    };

    notification.style.cssText = `
        position: fixed; top: 24px; right: 24px; padding: 16px 24px; border-radius: 12px;
        background: ${colors[type] || colors.info}; color: white; font-weight: 500; z-index: 9999;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        display: flex; align-items: center; gap: 12px; font-size: 14px;
        animation: slideInRight 0.4s cubic-bezier(0.4, 0, 0.2, 1); min-width: 280px; max-width: 480px;
    `;

    notification.innerHTML = `
        <i class="${icons[type] || icons.info}" style="font-size: 20px;"></i>
        <span>${message}</span>
        <i class="ti ti-x" style="margin-left: auto; cursor: pointer; opacity: 0.7; font-size: 16px;" onclick="this.parentElement.remove()"></i>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
        setTimeout(() => notification.remove(), 400);
    }, 4000);
}

// ============================================================
// Individual Student Attendance 
// ============================================================

function buildIndividualMasterLists(courses) {
    const departments = new Map();
    const programs = new Map();
    const studentsMap = new Map();

    courses.forEach(course => {
        const departmentId = String(course.departmentId || course.department || '').trim();
        const departmentName = course.department || 'Unknown Department';

        if (departmentId) {
            departments.set(departmentId, departmentName);
        }

        (course.students || []).forEach(student => {
            const programId = String(student.programId || student.program || '').trim();
            const programName = student.program || 'Unknown Program';

            if (programId) {
                programs.set(programId, {
                    id: programId,
                    name: programName,
                    departmentId: departmentId
                });
            }

            const studentId = String(student.id || student.studentId || student.rollNo || '').trim();
            if (!studentId) return;

            if (!studentsMap.has(studentId)) {
                studentsMap.set(studentId, {
                    id: studentId,
                    name: student.name || 'Unknown Student',
                    rollNo: student.rollNo || studentId,
                    program: student.program || 'Not assigned',
                    departmentIds: new Set(),
                    programIds: new Set()
                });
            }

            const entry = studentsMap.get(studentId);
            if (departmentId) entry.departmentIds.add(departmentId);
            if (programId) entry.programIds.add(programId);
        });
    });

    individualDepartments = Array.from(departments.entries())
        .map(([id, name]) => ({ id, name }))
        .sort((a, b) => a.name.localeCompare(b.name));

    individualPrograms = Array.from(programs.values())
        .sort((a, b) => a.name.localeCompare(b.name));

    individualStudents = Array.from(studentsMap.values())
        .sort((a, b) => a.name.localeCompare(b.name));
}

function renderIndividualFilterOptions() {
    const deptSelect = document.getElementById('individualDepartmentFilter');
    const programSelect = document.getElementById('individualProgramFilter');
    const studentSelect = document.getElementById('individualStudentFilter');

    if (!deptSelect || !programSelect || !studentSelect) return;

    const selectedDept = deptSelect.value;
    const selectedProgram = programSelect.value;

    // Departments — always the full master list.
    const deptItems = [{ value: '', label: 'All Departments' }]
        .concat(individualDepartments.map(d => ({ value: d.id, label: d.name })));
    setChoicesFromList('individualDepartmentFilter', deptItems, selectedDept);

    // Programs — filtered by selected department, from the MASTER list.
    const visiblePrograms = individualPrograms.filter(p =>
        !selectedDept || p.departmentId === selectedDept
    );
    const programStillValid = visiblePrograms.some(p => p.id === selectedProgram);
    const programItems = [{ value: '', label: 'All Programs' }]
        .concat(visiblePrograms.map(p => ({ value: p.id, label: p.name })));
    setChoicesFromList('individualProgramFilter', programItems, programStillValid ? selectedProgram : '');

    const effectiveProgram = programStillValid ? selectedProgram : '';

    // Students — filtered by Department AND Program, from the MASTER list.
    const visibleStudents = individualStudents.filter(s => {
        if (selectedDept && !s.departmentIds.has(selectedDept)) return false;
        if (effectiveProgram && !s.programIds.has(effectiveProgram)) return false;
        return true;
    });
    const currentStudentVal = studentSelect.value;
    const studentStillValid = visibleStudents.some(s => s.id === currentStudentVal);
    const studentItems = [{ value: '', label: 'Select Student' }]
        .concat(visibleStudents.map(s => ({ value: s.id, label: `${s.name} (${s.rollNo})` })));
    setChoicesFromList('individualStudentFilter', studentItems, studentStillValid ? currentStudentVal : '');
}

function applyIndividualCascadeFilter() {
    renderIndividualFilterOptions();
}

function showIndividualStudentAttendance() {
    const studentSelect = document.getElementById('individualStudentFilter');

    if (!studentSelect || !studentSelect.value) {
        showNotification('Please select a student first.', 'warning');
        return;
    }

    const studentId = String(studentSelect.value);

    let studentMeta = null;       // just name/rollNo/program — same across courses
    let studentCourses = [];      // courses this student appears in

    currentData.forEach(course => {
        const match = (course.students || []).find(s => {
            const id = String(s.id || s.studentId || s.rollNo || '');
            return id === studentId;
        });
        if (match) {
            if (!studentMeta) {
                studentMeta = {
                    name: match.name,
                    rollNo: match.rollNo,
                    program: match.program
                };
            }
            studentCourses.push(course);   // just the course, NOT the matched record
        }
    });

    if (!studentMeta) {
        showNotification('Student attendance data not found.', 'warning');
        return;
    }

    renderIndividualStudentAttendance(studentMeta, studentId, studentCourses);
}

function renderIndividualStudentAttendance(studentMeta, studentId, studentCourses) {
    const wrapper = document.getElementById('individualStudentWrapper');

    document.getElementById('individualStudentName').textContent = studentMeta.name || '-';
    document.getElementById('individualStudentId').textContent = studentMeta.rollNo || '-';
    document.getElementById('individualStudentProgram').textContent = studentMeta.program || '-';

    const tbody = document.getElementById('individualStudentAttendanceBody');
    tbody.innerHTML = '';

    let present = 0, absent = 0, late = 0;

    studentCourses.forEach((course, index) => {
        // Look up THIS course's own record for the student — not the
        // reused single `student` variable from before.
        const record = (course.students || []).find(s => {
            const id = String(s.id || s.studentId || s.rollNo || '');
            return id === studentId;
        });

        if (!record) return;

        const status = record.status || '';
        const pct = record.attendancePercent !== undefined
            ? record.attendancePercent
            : null;

        if (status === 'present') present++;
        else if (status === 'absent') absent++;
        else if (status === 'late') late++;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${pct !== null ? pct + '%' : '-'}</td>
            <td>${course.name || '-'}</td>
            <td>${course.code || '-'}</td>
            <td>${course.faculty || '-'}</td>
            <td>
                <div class="status-badge ${status}">
                    ${(status || '-').toUpperCase()}
                </div>
            </td>
            <td>-</td>
        `;
        tbody.appendChild(row);
    });

    const totalClasses = studentCourses.length;
    const rate = totalClasses > 0 ? Math.round((present / totalClasses) * 100) : 0;

    document.getElementById('individualTotalClasses').textContent = totalClasses;
    document.getElementById('individualPresent').textContent = present;
    document.getElementById('individualAbsent').textContent = absent;
    document.getElementById('individualLate').textContent = late;
    document.getElementById('individualAttendanceRate').textContent = rate + '%';

    wrapper.style.display = 'block';

    setTimeout(() => {
        wrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

function exportIndividualStudentAttendance() {
    const studentSelect = document.getElementById('individualStudentFilter');

    if (!studentSelect || !studentSelect.value) {
        showNotification('Please select a student first.', 'warning');
        return;
    }

    const studentId = String(studentSelect.value);

    let student = null;
    const rows = [];

    currentData.forEach(course => {
        (course.students || []).forEach(s => {
            const id = String(s.id || s.studentId || s.rollNo || '');
            if (id === studentId) {
                if (!student) student = s;
                rows.push({
                    attendancePercent: typeof s.attendancePercent === 'number' ? s.attendancePercent : '',
                    course: course.name || 'N/A',
                    code: course.code || 'N/A',
                    faculty: course.faculty || 'Not assigned',
                    status: s.status || ''
                });
            }
        });
    });

    if (!rows.length) {
        showNotification('No attendance records found for this student.', 'warning');
        return;
    }

    const worksheetData = [
        ['Individual Student Attendance'],
        [],
        ['Student Name', student.name || ''],
        ['Student ID', student.rollNo || ''],
        ['Program', student.program || ''],
        [],
        ['S.No', 'Attendance %', 'Course', 'Code', 'Faculty', 'Status']
    ];

    rows.forEach((row, index) => {
        worksheetData.push([
            index + 1,
            row.attendancePercent !== '' ? row.attendancePercent + '%' : '',
            row.course,
            row.code,
            row.faculty,
            row.status.toUpperCase()
        ]);
    });

    const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
    worksheet['!cols'] = [{ wch: 8 }, { wch: 14 }, { wch: 28 }, { wch: 12 }, { wch: 22 }, { wch: 12 }];

    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Attendance');

    const safeName = (student.name || 'student').replace(/[^a-z0-9]/gi, '_').substring(0, 40);
    XLSX.writeFile(workbook, `${safeName}_Attendance.xlsx`);

    showNotification('Attendance Excel downloaded successfully.', 'success');
}

function closeIndividualStudentAttendance() {
    const wrapper = document.getElementById('individualStudentWrapper');
    wrapper.style.display = 'none';

    const select = document.getElementById('individualStudentFilter');
    if (select) {
        select.value = '';
        refreshChoicesFromSelect('individualStudentFilter');
    }
}