/* ── Tab / filter state ── */
let activeTab = 'all';

function filterCourses() {
    const search = document.getElementById('courseSearch').value.toLowerCase().trim();
    const rows   = document.querySelectorAll('#courseTbody tr[data-status]');
    let visible  = 0;
    rows.forEach(row => {
        const name   = row.dataset.name || '';
        const code   = row.dataset.code || '';
        const dept   = row.dataset.dept || '';
        const status = row.dataset.status || '';
        const matchSearch = !search || name.includes(search) || code.includes(search) || dept.includes(search);
        const matchTab    = activeTab === 'all' || status === activeTab;
        const show        = matchSearch && matchTab;
        row.style.display = show ? '' : 'none';
        if (show) visible++;
    });
    const el = document.getElementById('noCourseResults');
    if (el) el.style.display = visible === 0 ? 'block' : 'none';
}

function resetCourseFilters() {
    document.getElementById('courseSearch').value = '';
    activeTab = 'all';
    document.querySelectorAll('.course-tab').forEach(t => t.classList.remove('active'));
    const first = document.querySelector('[data-tab="all"]');
    if (first) first.classList.add('active');
    filterCourses();
}

/* ── Custom modal ── */
function showInactiveModal(courseUuid, courseName) {
    document.getElementById('inactiveCourseName').textContent = courseName;
    document.getElementById('inactiveCourseForm').action =
        '/department/courses/' + courseUuid + '/inactivate/';
    document.getElementById('inactiveModal').classList.add('open');
}

function hideInactiveModal() {
    document.getElementById('inactiveModal').classList.remove('open');
}

/* ── Init ── */
document.addEventListener('DOMContentLoaded', function () {
    if (typeof lucide !== 'undefined') lucide.createIcons();

    /* Ban buttons */
    document.querySelectorAll('.ban-course-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            showInactiveModal(this.dataset.courseUuid, this.dataset.courseName);
        });
    });

    /* Tab clicks */
    document.querySelectorAll('.course-tab').forEach(function (tab) {
        tab.addEventListener('click', function () {
            document.querySelectorAll('.course-tab').forEach(function (t) { t.classList.remove('active'); });
            this.classList.add('active');
            activeTab = this.dataset.tab;
            filterCourses();
        });
    });
});
