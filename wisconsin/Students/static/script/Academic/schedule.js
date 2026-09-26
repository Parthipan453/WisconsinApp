document.addEventListener('DOMContentLoaded', function() {
  const viewSelect = document.getElementById('view-select');
  const yearSelect = document.getElementById('year-select');
  const weekSelect = document.getElementById('week-select');
  const monthSelect = document.getElementById('month-select');
  const semesterSelect = document.getElementById('semester-select');

  function reloadWith(params) {
    const url = new URL(window.location.href);
    Object.entries(params).forEach(([key, val]) => {
      if (val) url.searchParams.set(key, val);
      else url.searchParams.delete(key);
    });
    window.location.href = url.toString();
  }

  if (semesterSelect) {
    semesterSelect.addEventListener('change', function() {
      const view = viewSelect ? viewSelect.value : 'week';
      if (view === 'today') {
        reloadWith({ semester: this.value || null, view: 'today', date: null });
      } else {
        const year = yearSelect ? yearSelect.value : new Date().getFullYear();
        reloadWith({ semester: this.value || null, view: view, date: year + '-01-01' });
      }
    });
  }

  if (viewSelect) {
    viewSelect.addEventListener('change', function() {
      const view = this.value;
      const year = yearSelect ? yearSelect.value : new Date().getFullYear();
      const sem = semesterSelect ? semesterSelect.value : '';
      if (view === 'today') {
        reloadWith({ semester: sem || null, view: 'today', date: null });
      } else {
        reloadWith({ semester: sem || null, view: view, date: year + '-01-01' });
      }
    });
  }

  if (yearSelect) {
    yearSelect.addEventListener('change', function() {
      const view = viewSelect ? viewSelect.value : 'week';
      const sem = semesterSelect ? semesterSelect.value : '';
      reloadWith({ semester: sem || null, view: view, date: this.value + '-01-01' });
    });
  }

  if (monthSelect) {
    monthSelect.addEventListener('change', function() {
      const view = viewSelect ? viewSelect.value : 'week';
      const sem = semesterSelect ? semesterSelect.value : '';
      reloadWith({ semester: sem || null, view: view, date: this.value });
    });
  }

  if (weekSelect) {
    weekSelect.addEventListener('change', function() {
      const sem = semesterSelect ? semesterSelect.value : '';
      reloadWith({ semester: sem || null, view: 'week', date: this.value });
    });
  }
});



console.log(' Static Schedule loaded successfully!');