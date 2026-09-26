document.addEventListener("DOMContentLoaded", function () {
  var dataEl = document.getElementById("atl-rows-data");
  if (!dataEl) return;

  var rows = JSON.parse(dataEl.textContent);
  var rowsById = {};
  rows.forEach(function (r) { rowsById[r.id] = r; });

  var overlay = document.getElementById("atlModalOverlay");
  var body = document.getElementById("atlModalBody");
  var closeBtn = document.getElementById("atlModalClose");

  function fieldRow(label, value) {
    return (
      '<div class="atl-field">' +
        '<span class="atl-field__label">' + label + '</span>' +
        '<span class="atl-field__value">' + (value || "—") + "</span>" +
      "</div>"
    );
  }

  function openModal(id) {
    var r = rowsById[id];
    if (!r) return;

    body.innerHTML =
      '<div class="atl-modal-section">' +
        '<div class="atl-modal-section__title"><i data-lucide="info"></i> Event Information</div>' +
        fieldRow("Performed By", r.user) +
        fieldRow("Activity", r.action_label) +
        (r.target_role ? fieldRow("Role", r.target_role) : "") +
        (r.target_user ? fieldRow("Target User", r.target_user) : "") +
        fieldRow("Timestamp", r.timestamp) +
      "</div>" +
      '<div class="atl-modal-section">' +
        '<div class="atl-modal-section__title"><i data-lucide="globe"></i> Request Info</div>' +
        fieldRow("IP Address", r.ip_address) +
      "</div>" +
      '<div class="atl-modal-section">' +
        '<div class="atl-modal-section__title"><i data-lucide="message-square"></i> Description</div>' +
        '<div class="atl-modal-desc">' + r.description + "</div>" +
      "</div>";

    overlay.hidden = false;
    document.body.style.overflow = "hidden";
    if (window.lucide) window.lucide.createIcons();
  }

  function closeModal() {
    overlay.hidden = true;
    document.body.style.overflow = "";
  }

  document.querySelectorAll(".atl-btn-view").forEach(function (btn) {
    btn.addEventListener("click", function () {
      openModal(btn.getAttribute("data-log-id"));
    });
  });

  closeBtn.addEventListener("click", closeModal);
  overlay.addEventListener("click", function (e) {
    if (e.target === overlay) closeModal();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !overlay.hidden) closeModal();
  });
});

(function () {
  function initCustomSelects() {
    document.querySelectorAll('.al-custom-select').forEach(function (cs) {
      if (cs.dataset.csInit === '1') return;
      cs.dataset.csInit = '1';

      const trigger = cs.querySelector('.al-cs-trigger');
      const valueEl = cs.querySelector('.al-cs-value');
      const input   = cs.querySelector('input[type="hidden"]');
      const options = cs.querySelectorAll('.al-cs-option');

      const selected = cs.querySelector('.al-cs-option.is-selected') || options[0];
      if (selected) valueEl.textContent = selected.textContent.trim();

      trigger.addEventListener('click', function (e) {
        e.stopPropagation();
        document.querySelectorAll('.al-custom-select.is-open').forEach(function (other) {
          if (other !== cs) other.classList.remove('is-open');
        });
        cs.classList.toggle('is-open');
      });

      options.forEach(function (opt) {
        opt.addEventListener('click', function () {
          options.forEach(function (o) { o.classList.remove('is-selected'); });
          opt.classList.add('is-selected');
          valueEl.textContent = opt.textContent.trim();
          input.value = opt.dataset.value;
          cs.classList.remove('is-open');
        });
      });
    });
  }

  document.addEventListener('click', function () {
    document.querySelectorAll('.al-custom-select.is-open').forEach(function (cs) {
      cs.classList.remove('is-open');
    });
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('.al-custom-select.is-open').forEach(function (cs) {
        cs.classList.remove('is-open');
      });
    }
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCustomSelects);
  } else {
    initCustomSelects();
  }
  
  window.initAuditLogCustomSelects = initCustomSelects;
})();

(function () {
  function initRoleScopeTabs() {
    var form = document.getElementById('auditFilterForm');
    var input = document.getElementById('roleScopeInput');
    if (!form || !input) return;

    document.querySelectorAll('[data-set-role-scope]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        input.value = btn.dataset.setRoleScope;
        form.submit();
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRoleScopeTabs);
  } else {
    initRoleScopeTabs();
  }
})();