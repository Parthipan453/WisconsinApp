document.addEventListener('DOMContentLoaded', function () {
  var PAGE_SIZE = 4;

  var tabs = document.querySelectorAll('[data-role-tab]');
  var panels = document.querySelectorAll('[data-role-panel]');

  tabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      var target = tab.dataset.roleTab;

      tabs.forEach(function (t) { t.classList.remove('is-active'); });
      tab.classList.add('is-active');

      panels.forEach(function (panel) {
        panel.hidden = panel.dataset.rolePanel !== target;
      });
    });
  });

  function initRoleGrid(type) {
    var searchInput = document.getElementById('role-search-' + type);
    var grid = document.getElementById('rp-role-grid-' + type);
    var pager = document.getElementById('rp-pagination-' + type);
    var emptyState = document.getElementById('rp-search-empty-' + type);
    var resultCount = document.getElementById('rp-result-count-' + type);
    if (!grid) return;

    var cards = Array.prototype.slice.call(grid.querySelectorAll('.rp-role-card'));
    var currentPage = 1;

    function getFiltered() {
      var q = (searchInput ? searchInput.value : '').trim().toLowerCase();
      if (!q) return cards;
      return cards.filter(function (c) {
        return (c.dataset.roleName || '').indexOf(q) !== -1;
      });
    }

    function makePageBtn(label, page, opts) {
      opts = opts || {};
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = label;
      b.className = 'rp-page-btn' + (opts.active ? ' is-active' : '');
      b.disabled = !!opts.disabled;
      b.addEventListener('click', function () {
        currentPage = page;
        render();
        grid.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      });
      return b;
    }

    function renderPager(totalPages) {
      if (!pager) return;
      pager.innerHTML = '';
      if (totalPages <= 1) return;

      pager.appendChild(makePageBtn('Prev', currentPage - 1, { disabled: currentPage === 1 }));
      for (var p = 1; p <= totalPages; p++) {
        pager.appendChild(makePageBtn(String(p), p, { active: p === currentPage }));
      }
      pager.appendChild(makePageBtn('Next', currentPage + 1, { disabled: currentPage === totalPages }));
    }

    function render() {
      var filtered = getFiltered();
      var totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
      if (currentPage > totalPages) currentPage = totalPages;

      cards.forEach(function (c) { c.style.display = 'none'; });

      var start = (currentPage - 1) * PAGE_SIZE;
      filtered.slice(start, start + PAGE_SIZE).forEach(function (c) { c.style.display = ''; });

      grid.style.display = filtered.length === 0 ? 'none' : 'grid';
      if (emptyState) emptyState.style.display = filtered.length === 0 ? 'flex' : 'none';
      if (resultCount) {
        resultCount.textContent = filtered.length === cards.length
          ? cards.length + ' role' + (cards.length === 1 ? '' : 's')
          : filtered.length + ' of ' + cards.length + ' roles';
      }

      renderPager(totalPages);
    }

    if (searchInput) {
      searchInput.addEventListener('input', function () {
        currentPage = 1;
        render();
      });
    }

    render();
  }

  (window.PERMISSION_ROLE_TABS || ['user', 'medical']).forEach(initRoleGrid);
});