
  /* ── Tab filter ── */
  let activeTab = 'all';
  document.querySelectorAll('.dept-tab').forEach(btn => {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.dept-tab').forEach(t => t.classList.remove('active'));
      this.classList.add('active');
      activeTab = this.dataset.tab;
      filterDepts();
    });
  });

  /* ── Filter rows ── */
  function filterDepts() {
    const search = document.getElementById('deptSearch').value.toLowerCase().trim();
    const school = document.getElementById('schoolFilter').value;
    const rows   = document.querySelectorAll('#deptTbody tr[data-status]');
    let visible  = 0;
    rows.forEach(row => {
      const okSearch = !search || row.dataset.name.includes(search) || row.dataset.code.includes(search);
      const okSchool = !school || row.dataset.school === school;
      const okTab    = activeTab === 'all' || row.dataset.status === activeTab;
      const show     = okSearch && okSchool && okTab;
      row.style.display = show ? '' : 'none';
      if (show) visible++;
    });
    document.getElementById('noResults').style.display = visible === 0 ? 'block' : 'none';
  }

  /* ── Reset ── */
  function resetFilters() {
    document.getElementById('deptSearch').value   = '';
    document.getElementById('schoolFilter').value = '';
    activeTab = 'all';
    document.querySelectorAll('.dept-tab').forEach(t => t.classList.remove('active'));
    document.querySelector('[data-tab="all"]').classList.add('active');
    filterDepts();
  }

  /* ── Inactive modal ── */
  function confirmInactive(deptId, deptName) {
    document.getElementById('inactiveDeptName').textContent = deptName;
    document.getElementById('inactiveForm').action =
      `/department/departments/${deptId}/inactivate/`;
    new bootstrap.Modal(document.getElementById('inactiveModal')).show();
  }



  /* ── Init Lucide ── */
  document.addEventListener('DOMContentLoaded', () => {
    if (typeof lucide !== 'undefined') lucide.createIcons();
  });

 