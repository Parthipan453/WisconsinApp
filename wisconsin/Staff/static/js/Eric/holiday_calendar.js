(function(){
  var modalEl = document.getElementById('zaHcModal');
  if (!modalEl) return;
  var modal = new bootstrap.Modal(modalEl);

  var dateInput = document.getElementById('zaHcDate');
  var nameInput = document.getElementById('zaHcName');
  var titleEl = document.getElementById('zaHcModalTitle');
  var actionInput = document.getElementById('zaHcAction');
  var noteEl = document.getElementById('zaHcNote');
  var deleteBtn = document.getElementById('zaHcDelete');
  var workingToggle = document.getElementById('zaHcWorkingToggle');
  var workingToggleText = document.getElementById('zaHcWorkingToggleText');
  var cells = document.querySelectorAll('.za-hc-cell:not(.za-hc-empty)');

  modalEl.addEventListener('hidden.bs.modal', function(){
    dateInput.value = '';
    nameInput.value = '';
    nameInput.disabled = false;
    dateInput.disabled = false;
  });

  function openModal(dateVal, nameVal, isCustom, isWorking) {
    dateInput.value = dateVal || '';
    nameInput.value = nameVal || '';
    actionInput.value = 'add';
    if (nameVal) {
      titleEl.textContent = isCustom ? 'Edit Holiday' : 'Standard Holiday';
      nameInput.disabled = !isCustom;
      dateInput.disabled = !isCustom;
    } else {
      titleEl.textContent = 'Add Holiday';
      nameInput.disabled = false;
      dateInput.disabled = false;
    }
    if (deleteBtn) deleteBtn.style.display = (nameVal && isCustom) ? '' : 'none';
    if (workingToggle) {
      var showToggle = !nameVal || !isCustom;
      workingToggle.style.display = showToggle ? '' : 'none';
      if (isWorking) {
        workingToggleText.textContent = 'Restore to Normal';
      } else {
        workingToggleText.textContent = 'Mark as Working Day';
      }
    }
    if (noteEl) {
      var msg = '';
      if (isCustom) {
        msg = 'This is a custom holiday. You can edit the name or delete it.';
      } else if (nameVal) {
        msg = 'This is a standard holiday and cannot be modified.';
      }
      if (isWorking) {
        msg = 'This date is overridden as a working day. Attendance can be marked.';
      }
      noteEl.querySelector('span').textContent = msg || 'This holiday will be visible for all faculty on the selected date.';
    }
    modal.show();
  }

  if (deleteBtn) {
    deleteBtn.addEventListener('click', function(){
      var name = nameInput.value.trim();
      if (!confirm('Delete "' + name + '" holiday? This cannot be undone.')) return;
      actionInput.value = 'delete';
      var form = deleteBtn.closest('form');
      if (form) form.submit();
    });
  }

  if (workingToggle) {
    workingToggle.addEventListener('click', function(){
      var reason = nameInput.value.trim() || 'Working day override';
      actionInput.value = 'toggle_working_day';
      nameInput.value = reason;
      nameInput.disabled = false;
      var form = workingToggle.closest('form');
      if (form) form.submit();
    });
  }

  cells.forEach(function(cell) {
    cell.addEventListener('click', function() {
      openModal(
        cell.getAttribute('data-date') || '',
        cell.getAttribute('data-name') || '',
        cell.getAttribute('data-custom') === 'true',
        cell.getAttribute('data-working') === 'true'
      );
    });
  });
})();
