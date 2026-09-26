
let currentData = [];
let selectedCourse = null;
let currentPage = 1;
let currentSemesterId = '';
let gradeScale = [];
let choicesInstances = {};
const itemsPerPage = 10;

let overallDepartments = [];
let overallCourses = [];  
let overallPrograms = [];    
let overallStudents = []; 
document.addEventListener('DOMContentLoaded', function () {
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
    const mainFilterIds = [
        'semesterFilter',
        'courseFilter',
        'facultyFilter',
        'departmentFilter',
        'programFilter',
        'yearFilter',
        'statusFilter'
    ];

    mainFilterIds.forEach(id => {
        const element = document.getElementById(id);

        if (element) {
            element.addEventListener('change', function () {
                applyFilters();
            });
        }
    });

    const gradeFilter = document.getElementById('gradeFilter');

    if (gradeFilter) {
        gradeFilter.addEventListener('change', function () {
            applyStudentFilters();
        });
    }

    const searchInput = document.getElementById('searchInput');

    if (searchInput) {
        searchInput.addEventListener('input', function () {
            applyStudentFilters();
        });

        searchInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                applyStudentFilters();
            }
        });
    }

    const overallDept = document.getElementById('overallDepartmentFilter');
    const overallProgram = document.getElementById('overallProgramFilter');

    if (overallDept) {
        overallDept.addEventListener('change', applyOverallCascadeFilter);
    }
    if (overallProgram) {
        overallProgram.addEventListener('change', applyOverallCascadeFilter);
    }
}

function loadData() {
    const dataEl = document.getElementById('courses-data');
    const currentSemesterEl = document.getElementById('current-semester-id');
    const gradeScaleEl = document.getElementById('grade-scale-data');

    if (!dataEl) {
        console.error('courses-data not found');
        return;
    }

    currentData = JSON.parse(dataEl.textContent);
    currentSemesterId = currentSemesterEl ? JSON.parse(currentSemesterEl.textContent) : '';
    gradeScale = gradeScaleEl ? JSON.parse(gradeScaleEl.textContent) : [];

    populateSemesterFilter(currentData);
    populateCourseFilter(currentData);
    populateFacultyFilter(currentData);
    populateDepartmentFilter(currentData);
    populateProgramFilter(currentData);
    buildOverallMasterLists(currentData);   // builds the in-memory master lists
    renderOverallFilterOptions();           // renders all three selects from those lists
    populateGradeFilter(gradeScale);
    buildGradeDistributionSkeleton(gradeScale);

    const semesterSelect = document.getElementById('semesterFilter');
    if (semesterSelect && currentSemesterId) {
        semesterSelect.value = currentSemesterId;
        refreshChoicesFromSelect('semesterFilter');
    }
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

function populateGradeFilter(scale) {
    const select = document.getElementById('gradeFilter');
    if (!select) return;
    select.innerHTML = '<option value="">All Grades</option>';
    scale.forEach(entry => {
        if (!entry.letter) return;
        const option = document.createElement('option');
        option.value = entry.letter;
        option.textContent = entry.letter;
        select.appendChild(option);
    });
    const ungraded = document.createElement('option');
    ungraded.value = 'ungraded';
    ungraded.textContent = 'Ungraded';
    select.appendChild(ungraded);
    refreshChoicesFromSelect('gradeFilter');
}

function buildGradeDistributionSkeleton(scale) {
    const container = document.getElementById('gradeDistribution');
    if (!container) return;
    container.innerHTML = '';

    if (!scale.length) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="ti ti-certificate-off"></i>
                <p>No grade scale configured</p>
                <span class="empty-sub">Set one up in Admin &rarr; Grade Scale</span>
            </div>
        `;
        return;
    }

    scale.forEach(entry => {
        const letter = entry.letter;
        const safeId = letter.replace(/[^a-zA-Z0-9]/g, '');
        const row = document.createElement('div');
        row.className = 'monthly-stat-item';
        row.innerHTML = `
            <span class="stat-label">${letter}</span>
            <div class="stat-bar-wrapper">
                <div class="stat-bar" id="grade${safeId}Bar" style="width: 0%"></div>
            </div>
            <span class="stat-percentage" id="grade${safeId}Percent">0%</span>
        `;
        container.appendChild(row);
    });
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
        const scored = students.filter(s => s.score !== null && s.score !== undefined);
        const avgScore = scored.length ? Math.round(scored.reduce((sum, s) => sum + s.score, 0) / scored.length) : 0;
        const aCount = students.filter(s => (s.grade || '').toUpperCase().startsWith('A')).length;
        const fCount = students.filter(s => (s.grade || '').toUpperCase().startsWith('F')).length;
        const pendingCount = students.filter(s => !s.finalized).length;

        const professorInitials = course.faculty ? course.faculty.split(' ').map(word => word[0]).join('') : 'NA';

        const card = document.createElement('div');
        card.className = 'course-card';
        card.onclick = () => showGradeTable(course);

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
                <i class="ti ti-building"></i>
                ${course.department || ''}
            </p>
            <div class="course-stats-inline">
                <div class="stat-item-inline">
                    <span class="stat-value text-blue">${students.length}</span>
                    <span class="stat-label">Total</span>
                </div>
                <div class="stat-item-inline">
                    <span class="stat-value text-green">${avgScore}%</span>
                    <span class="stat-label">Avg</span>
                </div>
                <div class="stat-item-inline">
                    <span class="stat-value text-green">${aCount}</span>
                    <span class="stat-label">A's</span>
                </div>
                <div class="stat-item-inline">
                    <span class="stat-value text-red">${fCount}</span>
                    <span class="stat-label">F's</span>
                </div>
                <div class="stat-item-inline">
                    <span class="stat-value text-orange">${pendingCount}</span>
                    <span class="stat-label">Pending</span>
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
    let scoreSum = 0;
    let scoreCount = 0;
    let finalizedCount = 0;
    const gradeCounts = {};

    courses.forEach(course => {
        (course.students || []).forEach(student => {
            totalStudents++;
            if (student.score !== null && student.score !== undefined) {
                scoreSum += student.score;
                scoreCount++;
            }
            if (student.finalized) finalizedCount++;
            const letter = (student.grade || '').toUpperCase();
            if (letter) gradeCounts[letter] = (gradeCounts[letter] || 0) + 1;
        });
    });

    const avgScore = scoreCount ? Math.round(scoreSum / scoreCount) : 0;

    let modeLetter = '—';
    let modeCount = 0;
    Object.entries(gradeCounts).forEach(([letter, count]) => {
        if (count > modeCount) {
            modeCount = count;
            modeLetter = letter;
        }
    });

    document.getElementById('statTotalStudents').textContent = totalStudents;
    document.getElementById('statAverageScore').textContent = avgScore + '%';
    document.getElementById('statAverageGrade').textContent = modeLetter;
    document.getElementById('statFinalized').textContent = finalizedCount;
}

function updateCourseCount(count) {
    const badge = document.getElementById('courseCount');
    if (badge) badge.textContent = `${count} Courses`;
    const summaryBadge = document.getElementById('summaryCourseCount');
    if (summaryBadge) summaryBadge.textContent = `${count} Courses`;
}

function updateGradeDistribution(courses) {
    if (!gradeScale.length) return;

    const counts = {};
    gradeScale.forEach(entry => { counts[entry.letter] = 0; });

    let total = 0;
    courses.forEach(course => {
        (course.students || []).forEach(student => {
            const letter = student.grade;
            if (letter && Object.prototype.hasOwnProperty.call(counts, letter)) {
                counts[letter]++;
                total++;
            }
        });
    });

    const base = total > 0 ? total : 1;
    gradeScale.forEach(entry => {
        const letter = entry.letter;
        const safeId = letter.replace(/[^a-zA-Z0-9]/g, '');
        const pct = Math.round((counts[letter] / base) * 100);

        const bar = document.getElementById(`grade${safeId}Bar`);
        const pctLabel = document.getElementById(`grade${safeId}Percent`);
        if (bar) bar.style.width = Math.min(pct, 100) + '%';
        if (pctLabel) pctLabel.textContent = pct + '%';
    });
}

function updateSummary(courses) {
    let totalStudents = 0;
    let scoreSum = 0;
    let scoreCount = 0;
    let pending = 0;
    let finalized = 0;

    const courseAverages = [];

    courses.forEach(course => {
        const students = course.students || [];
        const scored = students.filter(s => s.score !== null && s.score !== undefined);
        const courseAvg = scored.length ? scored.reduce((sum, s) => sum + s.score, 0) / scored.length : null;
        if (courseAvg !== null) {
            courseAverages.push({ name: course.name, avg: courseAvg });
        }

        students.forEach(student => {
            totalStudents++;
            if (student.score !== null && student.score !== undefined) {
                scoreSum += student.score;
                scoreCount++;
            }
            if (student.finalized) finalized++;
            else pending++;
        });
    });

    const avgScore = scoreCount ? Math.round(scoreSum / scoreCount) : 0;

    let best = null, lowest = null;
    courseAverages.forEach(c => {
        if (!best || c.avg > best.avg) best = c;
        if (!lowest || c.avg < lowest.avg) lowest = c;
    });

    document.getElementById('summaryTotalStudents').textContent = totalStudents;
    document.getElementById('summaryBestCourse').textContent = best ? `${best.name} (${Math.round(best.avg)}%)` : '-';
    document.getElementById('summaryLowestCourse').textContent = lowest ? `${lowest.name} (${Math.round(lowest.avg)}%)` : '-';
    document.getElementById('summaryPending').textContent = pending;
    document.getElementById('summaryFinalized').textContent = finalized;
    document.getElementById('summaryAverageScore').textContent = avgScore + '%';
}

function showGradeTable(course) {
    if (!course) return;

    selectedCourse = course;
    currentPage = 1;

    document.getElementById('selectedCourseTitle').textContent = course.name;
    document.getElementById('facultyName').textContent = course.faculty || 'Not assigned';
    document.getElementById('courseCode').textContent = course.code || 'N/A';
    document.getElementById('courseSemester').textContent = course.semester || 'N/A';
    document.getElementById('courseSection').textContent = course.section || 'N/A';  

    document.getElementById('searchInput').value = '';

    const gradeSelect = document.getElementById('gradeFilter');
    if (gradeSelect) {
        gradeSelect.value = '';
        refreshChoicesFromSelect('gradeFilter');
    }

    document.getElementById('gradeTableWrapper').style.display = 'block';

    renderGradeTable(course.students || [], course);

    setTimeout(() => {
        document.getElementById('gradeTableWrapper')
            .scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

function applyStudentFilters() {
    if (!selectedCourse) return;

    const gradeElement = document.getElementById('gradeFilter');
    const searchElement = document.getElementById('searchInput');

    const gradeFilter = gradeElement
        ? gradeElement.value.toLowerCase().trim()
        : '';

    const searchQuery = searchElement
        ? searchElement.value.toLowerCase().trim()
        : '';

    let students = [...(selectedCourse.students || [])];

    if (gradeFilter) {
        if (gradeFilter === 'ungraded') {
            students = students.filter(student => !student.grade);
        } else {
            students = students.filter(student =>
                (student.grade || '').toLowerCase() === gradeFilter
            );
        }
    }

    if (searchQuery) {
        students = students.filter(student =>
            (student.name || '').toLowerCase().includes(searchQuery) ||
            String(student.rollNo || '').toLowerCase().includes(searchQuery)
        );
    }

    currentPage = 1;
    renderGradeTable(students, selectedCourse);
}

function renderGradeTable(students, course) {
    const tbody = document.getElementById('gradeTableBody');
    tbody.innerHTML = '';

    if (!students || students.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px; color: var(--text-secondary);">
                    <i class="ti ti-users" style="font-size: 32px; color: var(--text-light); display: block; margin-bottom: 12px;"></i>
                    No grade records found for this course.
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

    pageItems.forEach((student, index) => {
        const row = document.createElement('tr');
        const letter = (student.grade || '').toUpperCase();
        const gradeClass = letter ? `grade-${letter.charAt(0).toLowerCase()}` : 'grade-none';
        const statusClass = student.finalized ? 'finalized' : 'pending';
        const statusIcon = student.finalized ? 'ti ti-circle-check' : 'ti ti-clock';
        const statusLabel = student.finalized ? 'Finalized' : 'Pending';

        row.innerHTML = `
            <td>${startIndex + index + 1}</td>
            <td><strong>${student.name}</strong></td>
            <td>${student.rollNo}</td>
            <td>${student.program || 'Not assigned'}</td>
            <td>${student.score !== null && student.score !== undefined ? student.score + '%' : '—'}</td>
            <td><span class="grade-badge ${gradeClass}">${letter || '—'}</span></td>
            <td>
                <div class="status-badge ${statusClass}">
                    <i class="${statusIcon}"></i>
                    ${statusLabel}
                </div>
            </td>
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
        prevFirst.innerHTML = '&laquo;';
        prevFirst.onclick = (e) => { e.preventDefault(); goToPage(1); };
        controls.appendChild(prevFirst);

        const prev = document.createElement('a');
        prev.href = '#';
        prev.className = 'page-link pagination-link';
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
        next.innerHTML = '&rsaquo;';
        next.onclick = (e) => { e.preventDefault(); goToPage(currentPage + 1); };
        controls.appendChild(next);

        const nextLast = document.createElement('a');
        nextLast.href = '#';
        nextLast.className = 'page-link pagination-link';
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
    renderGradeTable(selectedCourse.students || [], selectedCourse);
}

function applyFilters(silent = false) {
    const semesterFilter = document.getElementById('semesterFilter').value.toLowerCase().trim();
    const courseFilter = document.getElementById('courseFilter').value.toLowerCase().trim();
    const facultyFilter = document.getElementById('facultyFilter').value.toLowerCase().trim();
    const departmentFilter = document.getElementById('departmentFilter').value.toLowerCase().trim();
    const programFilter = document.getElementById('programFilter').value.toLowerCase().trim();
    const yearFilter = document.getElementById('yearFilter').value;
    const statusFilter = document.getElementById('statusFilter').value;

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

    if (yearFilter || programFilter || statusFilter) {
        filtered = filtered.map(course => {
            let students = course.students || [];

            if (yearFilter) {
                students = students.filter(s => s.year !== null && String(s.year) === yearFilter);
            }

            if (programFilter) {
                students = students.filter(student => {
                    const pid = String(student.programId || '').toLowerCase();
                    const pname = (student.program || '').toLowerCase();
                    return pid === programFilter || pname === programFilter;
                });
            }

            if (statusFilter) {
                students = students.filter(student =>
                    statusFilter === 'finalized' ? student.finalized : !student.finalized
                );
            }

            return { ...course, students };
        }).filter(course => course.students && course.students.length > 0);
    }

    renderCourseCards(filtered);
    updateStats(filtered);
    updateCourseCount(filtered.length);
    updateGradeDistribution(filtered);
    updateSummary(filtered);

    const wrapper = document.getElementById('gradeTableWrapper');
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
    document.getElementById('yearFilter').value = '';
    document.getElementById('statusFilter').value = '';

    ['semesterFilter', 'courseFilter', 'facultyFilter', 'departmentFilter', 'programFilter', 'yearFilter', 'statusFilter']
        .forEach(refreshChoicesFromSelect);

    document.getElementById('gradeTableWrapper').style.display = 'none';
    selectedCourse = null;

    applyFilters(true);
    showNotification('Filters reset to the current semester.', 'info');
}

function refreshData() {
    showLoading();
    setTimeout(() => {
        loadData();
        document.getElementById('gradeTableWrapper').style.display = 'none';
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
    document.getElementById('gradeTableWrapper').style.display = 'none';
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
            ['Gradebook Report'],
            [`Course: ${selectedCourse.name}`],
            [`Course Code: ${selectedCourse.code || 'N/A'}`],
            [`Faculty: ${selectedCourse.faculty || 'Not assigned'}`],
            [`Department: ${selectedCourse.department || 'N/A'}`],
            [`Semester: ${selectedCourse.semester || 'N/A'}`],
            [`Generated: ${new Date().toLocaleString()}`],
            [],
            ['#', 'Student Name', 'Student ID', 'Program', 'Score', 'Grade', 'Status']
        ];

        const students = selectedCourse.students || [];
        students.forEach((student, index) => {
            excelData.push([
                index + 1,
                student.name,
                student.rollNo,
                student.program || 'Not assigned',
                student.score !== null && student.score !== undefined ? student.score : '',
                student.grade || '',
                student.finalized ? 'FINALIZED' : 'PENDING'
            ]);
        });

        const scored = students.filter(s => s.score !== null && s.score !== undefined);
        const avgScore = scored.length ? Math.round(scored.reduce((sum, s) => sum + s.score, 0) / scored.length) : 0;
        const finalizedCount = students.filter(s => s.finalized).length;

        excelData.push([]);
        excelData.push(['Summary']);
        excelData.push(['Total Students', students.length]);
        excelData.push(['Average Score', avgScore + '%']);
        excelData.push(['Finalized', finalizedCount]);
        excelData.push(['Pending', students.length - finalizedCount]);

        const wb = XLSX.utils.book_new();
        const ws = XLSX.utils.aoa_to_sheet(excelData);
        ws['!cols'] = [{ wch: 5 }, { wch: 25 }, { wch: 15 }, { wch: 20 }, { wch: 10 }, { wch: 8 }, { wch: 12 }];
        XLSX.utils.book_append_sheet(wb, ws, 'Gradebook');

        const fileName = `${selectedCourse.name}_Gradebook_${new Date().toISOString().split('T')[0]}.xlsx`;
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
        doc.text(`Gradebook Report: ${selectedCourse.name}`, 14, 20);

        doc.setFontSize(11);
        doc.setTextColor(100, 116, 139);
        let y = 28;

        const details = [
            `Course Code: ${selectedCourse.code || 'N/A'}`,
            `Faculty: ${selectedCourse.faculty || 'Not assigned'}`,
            `Department: ${selectedCourse.department || 'N/A'}`,
            `Semester: ${selectedCourse.semester || 'N/A'}`,
            `Generated: ${new Date().toLocaleString()}`
        ];

        details.forEach(detail => {
            doc.text(detail, 14, y);
            y += 6;
        });

        const students = selectedCourse.students || [];
        const tableHeaders = ['#', 'Student Name', 'Student ID', 'Program', 'Score', 'Grade', 'Status'];
        const tableRows = students.map((student, index) => [
            index + 1,
            student.name,
            student.rollNo,
            student.program || 'Not assigned',
            student.score !== null && student.score !== undefined ? student.score + '%' : '—',
            student.grade || '—',
            student.finalized ? 'FINALIZED' : 'PENDING'
        ]);

        doc.autoTable({
            startY: y + 4,
            head: [tableHeaders],
            body: tableRows,
            theme: 'striped',
            headStyles: { fillColor: [37, 99, 235], textColor: [255, 255, 255], fontSize: 10, fontStyle: 'bold' },
            bodyStyles: { fontSize: 9 },
            columnStyles: {
                0: { cellWidth: 10 }, 1: { cellWidth: 40 }, 2: { cellWidth: 25 },
                3: { cellWidth: 35 }, 4: { cellWidth: 20 }, 5: { cellWidth: 20 }, 6: { cellWidth: 25 }
            }
        });

        const finalY = doc.lastAutoTable.finalY || y + 50;
        const scored = students.filter(s => s.score !== null && s.score !== undefined);
        const avgScore = scored.length ? Math.round(scored.reduce((sum, s) => sum + s.score, 0) / scored.length) : 0;
        const finalizedCount = students.filter(s => s.finalized).length;

        doc.setFontSize(11);
        doc.setTextColor(15, 23, 42);
        doc.text('Summary', 14, finalY + 12);

        doc.setFontSize(10);
        doc.setTextColor(100, 116, 139);
        doc.text(`Total Students: ${students.length}`, 14, finalY + 20);
        doc.text(`Average Score: ${avgScore}%`, 14, finalY + 28);
        doc.text(`Finalized: ${finalizedCount}`, 14, finalY + 36);
        doc.text(`Pending: ${students.length - finalizedCount}`, 14, finalY + 44);

        const fileName = `${selectedCourse.name}_Gradebook_${new Date().toISOString().split('T')[0]}.pdf`;
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
// Student Overall Marks — cascading Department → Course → Student
// ============================================================

function buildOverallMasterLists(courses) {

    const departments = new Map();
    const programs = new Map();
    const studentsMap = new Map();

    courses.forEach(course => {

        const departmentId = String(
            course.departmentId || course.department || ''
        ).trim();

        const departmentName =
            course.department || 'Unknown Department';

        if (departmentId) {
            departments.set(
                departmentId,
                departmentName
            );
        }

        /*
         * Build Academic Programs from students
         */
        (course.students || []).forEach(student => {

            const programId = String(
                student.programId ||
                student.program ||
                ''
            ).trim();

            const programName =
                student.program || 'Unknown Program';

            if (programId) {

                programs.set(programId, {
                    id: programId,
                    name: programName,
                    departmentId: departmentId
                });
            }

            /*
             * Build Student master list
             */
            const studentId = String(
                student.id ||
                student.studentId ||
                student.rollNo ||
                ''
            ).trim();

            if (!studentId) return;

            if (!studentsMap.has(studentId)) {

                studentsMap.set(studentId, {
                    id: studentId,
                    name: student.name || 'Unknown Student',
                    rollNo: student.rollNo || studentId,
                    program: student.program || 'Not assigned',
                    programId: programId,
                    departmentIds: new Set(),
                    programIds: new Set()
                });
            }

            const entry = studentsMap.get(studentId);

            if (departmentId) {
                entry.departmentIds.add(departmentId);
            }

            if (programId) {
                entry.programIds.add(programId);
            }

        });

    });

    overallDepartments =
        Array.from(departments.entries())
            .map(([id, name]) => ({
                id,
                name
            }))
            .sort((a, b) =>
                a.name.localeCompare(b.name)
            );

    overallPrograms =
        Array.from(programs.values())
            .sort((a, b) =>
                a.name.localeCompare(b.name)
            );

    overallStudents =
        Array.from(studentsMap.values())
            .sort((a, b) =>
                a.name.localeCompare(b.name)
            );
}

function renderOverallFilterOptions() {

    const deptSelect =
        document.getElementById('overallDepartmentFilter');

    const programSelect =
        document.getElementById('overallProgramFilter');

    const studentSelect =
        document.getElementById('studentOverallFilter');

    if (!deptSelect || !programSelect || !studentSelect) {
        return;
    }

    const selectedDept =
        deptSelect.value;

    const selectedProgram =
        programSelect.value;

    /*
     * --------------------------------------------------
     * Department
     * --------------------------------------------------
     */

    const deptItems = [
        {
            value: '',
            label: 'All Departments'
        }
    ].concat(
        overallDepartments.map(dept => ({
            value: dept.id,
            label: dept.name
        }))
    );

    setChoicesFromList(
        'overallDepartmentFilter',
        deptItems,
        selectedDept
    );


    /*
     * --------------------------------------------------
     * Academic Program
     * --------------------------------------------------
     */

    const visiblePrograms =
        overallPrograms.filter(program =>
            !selectedDept ||
            program.departmentId === selectedDept
        );

    const programStillValid =
        visiblePrograms.some(
            program => program.id === selectedProgram
        );

    const programItems = [
        {
            value: '',
            label: 'All Programs'
        }
    ].concat(
        visiblePrograms.map(program => ({
            value: program.id,
            label: program.name
        }))
    );

    setChoicesFromList(
        'overallProgramFilter',
        programItems,
        programStillValid
            ? selectedProgram
            : ''
    );

    const effectiveProgram =
        programStillValid
            ? selectedProgram
            : '';


    /*
     * --------------------------------------------------
     * Student
     * Department → Program
     * --------------------------------------------------
     */

    const visibleStudents =
        overallStudents.filter(student => {

            if (
                selectedDept &&
                !student.departmentIds.has(selectedDept)
            ) {
                return false;
            }

            if (
                effectiveProgram &&
                !student.programIds.has(effectiveProgram)
            ) {
                return false;
            }

            return true;
        });

    const currentStudentVal =
        studentSelect.value;

    const studentStillValid =
        visibleStudents.some(
            student => student.id === currentStudentVal
        );

    const studentItems = [
        {
            value: '',
            label: 'Select Student'
        }
    ].concat(
        visibleStudents.map(student => ({
            value: student.id,
            label: `${student.name} (${student.rollNo})`
        }))
    );

    setChoicesFromList(
        'studentOverallFilter',
        studentItems,
        studentStillValid
            ? currentStudentVal
            : ''
    );
}

// Fired on Department/Course change — just re-renders from the master
// lists using whatever is currently selected.
function applyOverallCascadeFilter() {
    renderOverallFilterOptions();
}

function showOverallStudentMarks() {

    const select = document.getElementById('studentOverallFilter');

    if (!select || !select.value) {

        showNotification(
            'Please select a student first.',
            'warning'
        );

        return;
    }

    const studentId = String(select.value);

    let studentCourses = [];
    let studentDetails = null;

    currentData.forEach(course => {

        const student = (course.students || []).find(s => {

            const id = String(
                s.id ||
                s.studentId ||
                s.rollNo ||
                ''
            );

            return id === studentId;

        });

        if (student) {

            if (!studentDetails) {

                studentDetails = {
                    name: student.name || 'Unknown Student',
                    rollNo: student.rollNo || studentId,
                    program: student.program || 'Not assigned'
                };

            }

            studentCourses.push({
                course: course,
                student: student
            });

        }

    });

    if (!studentCourses.length) {

        showNotification(
            'No marks found for this student.',
            'warning'
        );

        return;
    }

    renderOverallStudentMarks(
        studentDetails,
        studentCourses
    );
}

function renderOverallStudentMarks(student, studentCourses) {

    const wrapper =
        document.getElementById('overallStudentWrapper');

    document.getElementById('overallStudentName').textContent =
        student.name;

    document.getElementById('overallStudentId').textContent =
        student.rollNo;

    document.getElementById('overallStudentProgram').textContent =
        student.program;

    const tbody =
        document.getElementById('overallStudentBody');

    tbody.innerHTML = '';

    let scoreSum = 0;
    let scoreCount = 0;
    let finalizedCount = 0;

    const gradeCounts = {};

    studentCourses.forEach((item, index) => {

        const course = item.course;
        const s = item.student;

        const hasScore =
            s.score !== null &&
            s.score !== undefined;

        if (hasScore) {

            scoreSum += Number(s.score);
            scoreCount++;

        }

        if (s.finalized) {
            finalizedCount++;
        }

        const grade =
            (s.grade || '').toUpperCase();

        if (grade) {

            gradeCounts[grade] =
                (gradeCounts[grade] || 0) + 1;

        }

        const gradeClass = grade
            ? `grade-${grade.charAt(0).toLowerCase()}`
            : 'grade-none';

        const statusClass =
            s.finalized
                ? 'finalized'
                : 'pending';

        const statusIcon =
            s.finalized
                ? 'ti ti-circle-check'
                : 'ti ti-clock';

        const statusText =
            s.finalized
                ? 'Finalized'
                : 'Pending';

        const row =
            document.createElement('tr');

        row.innerHTML = `
            <td>${index + 1}</td>

            <td>
                <strong>
                    ${course.name || 'N/A'}
                </strong>
            </td>

            <td>
                ${course.code || 'N/A'}
            </td>

            <td>
                ${course.semester || 'N/A'}
            </td>

            <td>
                ${
                    hasScore
                        ? `${s.score}%`
                        : '—'
                }
            </td>

            <td>
                <span class="grade-badge ${gradeClass}">
                    ${grade || '—'}
                </span>
            </td>

            <td>
                <div class="status-badge ${statusClass}">
                    <i class="${statusIcon}"></i>
                    ${statusText}
                </div>
            </td>
        `;

        tbody.appendChild(row);

    });

    const average =
        scoreCount
            ? Math.round(scoreSum / scoreCount)
            : 0;

    let averageGrade = '—';
    let highestCount = 0;

    Object.entries(gradeCounts).forEach(
        ([grade, count]) => {

            if (count > highestCount) {

                highestCount = count;
                averageGrade = grade;

            }

        }
    );

    document.getElementById('overallCourseCount')
        .textContent = studentCourses.length;

    document.getElementById('overallAverageScore')
        .textContent = `${average}%`;

    document.getElementById('overallAverageGrade')
        .textContent = averageGrade;

    document.getElementById('overallFinalized')
        .textContent = finalizedCount;

    wrapper.style.display = 'block';

    setTimeout(() => {

        wrapper.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });

    }, 100);
}

function exportOverallStudentExcel() {
    const select = document.getElementById('studentOverallFilter');

    if (!select || !select.value) {
        showNotification('Please select a student first.', 'warning');
        return;
    }

    const studentId = String(select.value);

    let student = null;
    const rows = [];

    currentData.forEach(course => {
        const foundStudent = (course.students || []).find(s => {
            const id = String(
                s.id ||
                s.studentId ||
                s.rollNo ||
                ''
            ).trim();

            return id === studentId;
        });

        if (foundStudent) {
            if (!student) {
                student = {
                    name: foundStudent.name || 'Unknown Student',
                    rollNo: foundStudent.rollNo || studentId,
                    program: foundStudent.program || 'Not assigned'
                };
            }

            rows.push({
                course: course.name || 'N/A',
                code: course.code || 'N/A',
                semester: course.semester || 'N/A',
                score: foundStudent.score ?? '',
                grade: foundStudent.grade || '',
                status: foundStudent.finalized
                    ? 'Finalized'
                    : 'Pending'
            });
        }
    });

    if (!rows.length) {
        showNotification('No marks found for this student.', 'warning');
        return;
    }

    const worksheetData = [
        ['Student Overall Marks'],
        [],
        ['Student Name', student.name],
        ['Student ID', student.rollNo],
        ['Program', student.program],
        [],
        [
            'S.No',
            'Course',
            'Course Code',
            'Semester',
            'Score',
            'Grade',
            'Status'
        ]
    ];

    rows.forEach((row, index) => {
        worksheetData.push([
            index + 1,
            row.course,
            row.code,
            row.semester,
            row.score,
            row.grade,
            row.status
        ]);
    });

    const scores = rows
        .map(row => Number(row.score))
        .filter(score => !isNaN(score));

    const average = scores.length
        ? (scores.reduce((sum, score) => sum + score, 0) / scores.length).toFixed(2)
        : '0.00';

    worksheetData.push([]);
    worksheetData.push(['Overall Average', `${average}%`]);

    const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);

    worksheet['!cols'] = [
        { wch: 8 },
        { wch: 30 },
        { wch: 15 },
        { wch: 15 },
        { wch: 12 },
        { wch: 10 },
        { wch: 15 }
    ];

    const workbook = XLSX.utils.book_new();

    XLSX.utils.book_append_sheet(
        workbook,
        worksheet,
        'Overall Marks'
    );

    const safeName = student.name
        .replace(/[^a-z0-9]/gi, '_')
        .substring(0, 40);

    XLSX.writeFile(
        workbook,
        `${safeName}_Overall_Marks.xlsx`
    );

    showNotification('Overall marks Excel downloaded successfully.', 'success');
}

function closeOverallStudent() {

    const wrapper =
        document.getElementById('overallStudentWrapper');

    wrapper.style.display = 'none';

    const select =
        document.getElementById('studentOverallFilter');

    if (select) {
        select.value = '';
        refreshChoicesFromSelect('studentOverallFilter');
    }
}