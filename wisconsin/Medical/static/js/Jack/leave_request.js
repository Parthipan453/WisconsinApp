(function () {
  'use strict';

  function readJsonScript(id) {
    var el = document.getElementById(id);
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return null;
    }
  }

  var leavesFromServer = readJsonScript('leave-data');
  var leaves = leavesFromServer !== null ? leavesFromServer : "";

  var csrfToken = (function () {
    var el = document.getElementById('lm-csrf-token');
    return el ? el.getAttribute('data-token') : '';
  })();

  var statusUrlTemplate = (function () {
    var el = document.getElementById('lm-status-url-template');
    return el ? el.getAttribute('data-url') : null;
  })();

  function buildStatusUrl(id) {
    if (!statusUrlTemplate) return null;
    return statusUrlTemplate.replace(/\/0(\/|$)/, '/' + id + '$1');
  }

  var state = {
    status: 'ALL',
    type: 'ALL',
    query: '',
    expanded: {}
  };

  var AVATAR_PALETTE = ['#c5050c', '#185fa5', '#228b22', '#7c3aed', '#b45309', '#0f766e'];

  function avatarColor(name) {
    var sum = 0;
    for (var i = 0; i < name.length; i++) sum += name.charCodeAt(i);
    return AVATAR_PALETTE[sum % AVATAR_PALETTE.length];
  }

  function initials(name) {
    var parts = name.trim().split(/\s+/);
    var first = parts[0] ? parts[0][0] : '';
    var last = parts.length > 1 ? parts[parts.length - 1][0] : '';
    return (first + last).toUpperCase();
  }

  function formatDateRange(item) {
    var opts = { day: 'numeric', month: 'short' };
    var start = new Date(item.start_date + 'T00:00:00');
    var end = new Date(item.end_date + 'T00:00:00');
    var startStr = start.toLocaleDateString('en-IN', opts);
    var endStr = end.toLocaleDateString('en-IN', opts);

    if (item.leave_type === 'PERMISSION' && item.permission_start_time) {
      return startStr + ' \u00B7 ' + item.permission_start_time + '\u2013' + item.permission_end_time;
    }
    if (item.start_date === item.end_date) return startStr;
    return startStr + ' \u2013 ' + endStr;
  }

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str == null ? '' : String(str);
    return div.innerHTML;
  }

  var listEl = document.getElementById('lm-list');
  var emptyEl = document.getElementById('lm-empty');

  function computeCounts() {
    var counts = { ALL: leaves.length, PENDING: 0, APPROVED: 0, REJECTED: 0, CANCELLED: 0 };
    leaves.forEach(function (l) {
      if (counts[l.status] !== undefined) counts[l.status]++;
    });
    return counts;
  }

  function renderStats() {
    var c = computeCounts();
    document.getElementById('lm-count-pending').textContent = c.PENDING;
    document.getElementById('lm-count-approved').textContent = c.APPROVED;
    document.getElementById('lm-count-rejected').textContent = c.REJECTED;
    document.getElementById('lm-count-total').textContent = c.ALL;

    document.getElementById('lm-tab-count-all').textContent = c.ALL;
    document.getElementById('lm-tab-count-pending').textContent = c.PENDING;
    document.getElementById('lm-tab-count-approved').textContent = c.APPROVED;
    document.getElementById('lm-tab-count-rejected').textContent = c.REJECTED;
    document.getElementById('lm-tab-count-cancelled').textContent = c.CANCELLED;
  }

  function filteredLeaves() {
    return leaves.filter(function (l) {
      if (state.status !== 'ALL' && l.status !== state.status) return false;
      if (state.type !== 'ALL' && l.leave_type !== state.type) return false;
      if (state.query) {
        var haystack = (l.staff_name + ' ' + l.reason).toLowerCase();
        if (haystack.indexOf(state.query.toLowerCase()) === -1) return false;
      }
      return true;
    }).sort(function (a, b) {
      if (a.status === 'PENDING' && b.status !== 'PENDING') return -1;
      if (b.status === 'PENDING' && a.status !== 'PENDING') return 1;
      return new Date(b.created_at) - new Date(a.created_at);
    });
  }

  function reasonMarkup(item) {
    var maxLen = 90;
    var text = item.reason || '';
    var isLong = text.length > maxLen;
    var expanded = !!state.expanded[item.id];

    if (!isLong) {
      return '<p class="lm-reason">' + escapeHtml(text) + '</p>';
    }

    var shown = expanded ? text : text.slice(0, maxLen).trim() + '\u2026';
    return (
      '<p class="lm-reason">' + escapeHtml(shown) +
      '<button type="button" class="lm-reason-toggle" data-reason-toggle="' + item.id + '">' +
      (expanded ? 'Show less' : 'Show more') +
      '</button></p>'
    );
  }

  function decisionMarkup(item) {
    if (item.status !== 'PENDING') {
      if (item.status === 'APPROVED' && item.approved_by) {
        return '<div class="lm-decision-note"><i class="ti ti-circle-check"></i>Approved by ' + escapeHtml(item.approved_by) + '</div>';
      }
      if (item.status === 'REJECTED') {
        return (
          '<div class="lm-decision-note is-rejected"><i class="ti ti-circle-x"></i>' +
          (item.rejection_reason ? escapeHtml(item.rejection_reason) : 'Rejected') +
          '</div>'
        );
      }
      if (item.status === 'CANCELLED') {
        return '<div class="lm-decision-note"><i class="ti ti-ban"></i>Cancelled by staff</div>';
      }
      return '';
    }

    return (
      '<div class="lm-decision">' +
      '<div class="lm-toggle" data-toggle-for="' + item.id + '">' +
      '<span class="lm-toggle-thumb"></span>' +
      '<button type="button" class="lm-approve-btn" data-action="approve" data-id="' + item.id + '">Approve</button>' +
      '<button type="button" class="lm-reject-btn" data-action="reject" data-id="' + item.id + '">Reject</button>' +
      '</div>' +
      '</div>'
    );
  }

  function cardMarkup(item, index) {
    var color = avatarColor(item.staff_name);
    return (
      '<div class="lm-card lm-reveal" data-status="' + item.status + '" data-id="' + item.id + '" style="animation-delay:' + Math.min(index * 40, 280) + 'ms">' +
        '<div class="lm-avatar" style="background:' + color + '">' + initials(item.staff_name) + '</div>' +
        '<div class="lm-card-body">' +
          '<div class="lm-card-top">' +
            '<span class="lm-staff-name">' + escapeHtml(item.staff_name) + '</span>' +
            (item.staff_role ? '<span class="lm-meta-row"><span>' + escapeHtml(item.staff_role) + '</span></span>' : '') +
            '<span class="lm-badge" data-type="' + item.leave_type + '"><span class="lm-badge-dot"></span>' + escapeHtml(item.leave_type_display) + '</span>' +
            (item.status !== 'PENDING' ? '<span class="lm-status" data-status="' + item.status + '">' + item.status.charAt(0) + item.status.slice(1).toLowerCase() + '</span>' : '') +
          '</div>' +
          '<div class="lm-meta-row">' +
            '<span><i class="ti ti-calendar"></i>' + formatDateRange(item) + '</span>' +
          '</div>' +
          reasonMarkup(item) +
        '</div>' +
        decisionMarkup(item) +
      '</div>'
    );
  }

  function render() {
    renderStats();
    var items = filteredLeaves();

    if (!items.length) {
      listEl.innerHTML = '';
      emptyEl.hidden = false;
      return;
    }
    emptyEl.hidden = true;
    listEl.innerHTML = items.map(cardMarkup).join('');
  }

  function showToast(message, kind) {
    var stack = document.getElementById('lm-toast-stack');
    var toast = document.createElement('div');
    toast.className = 'lm-toast';
    toast.setAttribute('data-kind', kind || 'success');
    var icon = kind === 'error' ? 'ti-alert-circle' : 'ti-circle-check';
    toast.innerHTML = '<i class="ti ' + icon + '"></i><span>' + escapeHtml(message) + '</span>';
    stack.appendChild(toast);
    requestAnimationFrame(function () {
      toast.classList.add('is-visible');
    });
    setTimeout(function () {
      toast.classList.remove('is-visible');
      setTimeout(function () { toast.remove(); }, 250);
    }, 3200);
  }

  function findLeave(id) {
    for (var i = 0; i < leaves.length; i++) {
      if (String(leaves[i].id) === String(id)) return leaves[i];
    }
    return null;
  }

  function sendStatusUpdate(id, payload) {
    var url = buildStatusUrl(id);
    if (!url) {
      return Promise.resolve({ ok: true, local: true });
    }
    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify(payload)
    }).then(function (res) {
      if (!res.ok) throw new Error('Request failed with status ' + res.status);
      return res.json().catch(function () { return {}; });
    });
  }

  function approveLeave(id, triggerEl) {
    var item = findLeave(id);
    if (!item) return;

    setToggleBusy(id, true);
    sendStatusUpdate(id, { status: 'APPROVED' })
      .then(function (data) {
        item.status = 'APPROVED';
        item.approved_by = (data && data.approved_by) || item.approved_by || 'You';
        item.approved_at = new Date().toISOString();
        render();
        showToast(item.staff_name + '\u2019s leave request was approved.', 'success');
      })
      .catch(function () {
        showToast('Could not approve this request. Please try again.', 'error');
        setToggleBusy(id, false);
      });
  }

  function setToggleBusy(id, busy) {
    var toggle = document.querySelector('.lm-toggle[data-toggle-for="' + id + '"]');
    if (!toggle) return;
    var buttons = toggle.querySelectorAll('button');
    buttons.forEach(function (b) { b.disabled = busy; });
  }

  var rejectBackdrop = document.getElementById('lm-reject-backdrop');
  var rejectReasonInput = document.getElementById('lm-reject-reason');
  var rejectError = document.getElementById('lm-reject-error');
  var rejectConfirmBtn = document.getElementById('lm-reject-confirm');
  var rejectSubtitle = document.getElementById('lm-reject-subtitle');
  var pendingRejectId = null;

  function openRejectModal(id) {
    var item = findLeave(id);
    if (!item) return;
    pendingRejectId = id;
    rejectReasonInput.value = '';
    rejectError.textContent = '';
    rejectSubtitle.textContent = 'Let ' + item.staff_name + ' know why this request is being rejected.';
    rejectBackdrop.classList.add('is-open');
    lockBodyScroll();
    setTimeout(function () { rejectReasonInput.focus(); }, 50);
  }

  function closeRejectModal() {
    rejectBackdrop.classList.remove('is-open');
    unlockBodyScroll();
    pendingRejectId = null;
  }

  var scrollLockY = 0;

  function lockBodyScroll() {
      scrollLockY = window.scrollY || window.pageYOffset;
      var scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
      document.body.style.position = 'fixed';
      document.body.style.top = '-' + scrollLockY + 'px';
      document.body.style.left = '0';
      document.body.style.right = '0';
      document.body.style.width = '100%';
      if (scrollbarWidth > 0) {
          document.body.style.paddingRight = scrollbarWidth + 'px';
      }
  }

  function unlockBodyScroll() {
    document.body.style.position = '';
    document.body.style.top = '';
    document.body.style.left = '';
    document.body.style.right = '';
    document.body.style.width = '';
    document.body.style.paddingRight = '';
    window.scrollTo(0, scrollLockY);
  }

  document.getElementById('lm-reject-cancel').addEventListener('click', function () {
    if (pendingRejectId != null) setToggleBusy(pendingRejectId, false);
    closeRejectModal();
  });

  rejectBackdrop.addEventListener('click', function (e) {
    if (e.target === rejectBackdrop) {
      if (pendingRejectId != null) setToggleBusy(pendingRejectId, false);
      closeRejectModal();
    }
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && rejectBackdrop.classList.contains('is-open')) {
      if (pendingRejectId != null) setToggleBusy(pendingRejectId, false);
      closeRejectModal();
    }
  });

  rejectConfirmBtn.addEventListener('click', function () {
    var reason = rejectReasonInput.value.trim();
    if (!reason) {
      rejectError.textContent = 'Please add a reason for the staff member.';
      return;
    }
    var id = pendingRejectId;
    var item = findLeave(id);
    if (!item) return;

    rejectConfirmBtn.disabled = true;
    sendStatusUpdate(id, { status: 'REJECTED', rejection_reason: reason })
      .then(function () {
        item.status = 'REJECTED';
        item.rejection_reason = reason;
        item.approved_by = 'You';
        item.approved_at = new Date().toISOString();
        closeRejectModal();
        render();
        showToast(item.staff_name + '\u2019s leave request was rejected.', 'error');
      })
      .catch(function () {
        rejectError.textContent = 'Something went wrong. Please try again.';
        setToggleBusy(id, false);
      })
      .finally(function () {
        rejectConfirmBtn.disabled = false;
      });
  });

  listEl.addEventListener('click', function (e) {
    var reasonBtn = e.target.closest('[data-reason-toggle]');
    if (reasonBtn) {
      var rid = reasonBtn.getAttribute('data-reason-toggle');
      state.expanded[rid] = !state.expanded[rid];
      render();
      return;
    }

    var actionBtn = e.target.closest('[data-action]');
    if (actionBtn) {
      var id = actionBtn.getAttribute('data-id');
      var action = actionBtn.getAttribute('data-action');
      var toggle = actionBtn.closest('.lm-toggle');
      if (toggle) toggle.setAttribute('data-choice', action);

      if (action === 'approve') {
        approveLeave(id, actionBtn);
      } else if (action === 'reject') {
        openRejectModal(id);
      }
    }
  });

  document.getElementById('lm-status-tabs').addEventListener('click', function (e) {
    var tab = e.target.closest('.lm-tab');
    if (!tab) return;
    document.querySelectorAll('.lm-tab').forEach(function (t) {
      t.classList.remove('is-active');
      t.setAttribute('aria-selected', 'false');
    });
    tab.classList.add('is-active');
    tab.setAttribute('aria-selected', 'true');
    state.status = tab.getAttribute('data-status');
    render();
  });

  var typeFilterEl = document.getElementById('lm-type-filter');
  typeFilterEl.addEventListener('change', function (e) {
    state.type = e.target.value;
    render();
  });

  if (window.SlimSelect) {
    new window.SlimSelect({
      select: '#lm-type-filter',
      settings: {
        showSearch: false,
        placeholderText: 'All leave types'
      }
    });
  }

  var searchTimer;
  document.getElementById('lm-search-input').addEventListener('input', function (e) {
    clearTimeout(searchTimer);
    var val = e.target.value;
    searchTimer = setTimeout(function () {
      state.query = val;
      render();
    }, 180);
  });

  document.getElementById('lm-refresh-btn').addEventListener('click', function () {
    var btn = this;
    btn.classList.add('is-spinning');
    render();
    setTimeout(function () { btn.classList.remove('is-spinning'); }, 500);
  });

  render();
})();