// kali code
document.addEventListener('DOMContentLoaded', function () {

  const form = document.getElementById('etaApplicationForm');
  if (!form) return; // already-submitted / closed panel is showing, nothing to wire up

  const otpPanel = document.getElementById('etaOtpPanel');
  const sendOtpBtn = document.getElementById('etaSendOtpBtn');
  const verifyBtn = document.getElementById('etaVerifyBtn');
  const backBtn = document.getElementById('etaBackBtn');
  const resendBtn = document.getElementById('etaResendBtn');
  const resendTimerEl = document.getElementById('etaResendTimer');
  const otpInput = document.getElementById('etaOtpInput');
  const otpEmailEl = document.getElementById('etaOtpEmail');
  const otpErrorEl = document.getElementById('etaOtpError');
  const formErrorEl = document.getElementById('etaFormError');

  let resendTimer = null;

  function getCookie(name) {
    let value = null;
    document.cookie.split(';').forEach(c => {
      c = c.trim();
      if (c.startsWith(name + '=')) value = decodeURIComponent(c.substring(name.length + 1));
    });
    return value;
  }

  function showFormError(message) {
    if (!formErrorEl) return;
    formErrorEl.textContent = message;
    formErrorEl.style.display = 'block';
  }

  function clearFormError() {
    if (!formErrorEl) return;
    formErrorEl.style.display = 'none';
    formErrorEl.textContent = '';
  }

  function showOtpError(message) {
    if (!otpErrorEl) return;
    otpErrorEl.textContent = message;
    otpErrorEl.style.display = 'block';
  }

  function clearOtpError() {
    if (!otpErrorEl) return;
    otpErrorEl.style.display = 'none';
    otpErrorEl.textContent = '';
  }


  function initChoices() {
    if (typeof Choices === 'undefined') {
      console.warn('Choices.js did not load — falling back to native selects.');
      return;
    }

    const configs = [
      { sel: '.eta-college-select', other: '.eta-other-college-input', placeholder: 'Select College' },
      { sel: '.eta-coach-select', other: '.eta-other-coach-input', placeholder: 'Select Coach' },
      { sel: '.eta-team-select', other: '.eta-other-team-input', placeholder: 'Select Internal Team' },
    ];

    configs.forEach(cfg => {
      const select = form.querySelector(cfg.sel);
      if (!select || select.dataset.choicesInitialized === 'true') return;

      try {
        new Choices(select, {
          searchEnabled: true,
          itemSelectText: '',
          shouldSort: false,
          allowHTML: false,
          removeItemButton: false,
          placeholder: true,
          placeholderValue: cfg.placeholder,
        });
        select.dataset.choicesInitialized = 'true';
      } catch (err) {
        console.error('Choices init failed for', cfg.sel, err);
      }

      select.addEventListener('change', function () {
        const otherInput = form.querySelector(cfg.other);
        if (!otherInput) return;
        if (select.value === 'OTHER') {
          otherInput.style.display = 'block';
          otherInput.required = true;
          otherInput.focus();
        } else {
          otherInput.style.display = 'none';
          otherInput.required = false;
          otherInput.value = '';
        }
      });
    });
  }

  try {
    initChoices();
  } catch (err) {
    console.error('initChoices() failed, continuing without it:', err);
  }

  const playersSection = form.querySelector('.eta-players-section');

  function updatePlayerCount() {
    if (!playersSection) return;
    const min = parseInt(form.dataset.minParticipants, 10) || 0;
    const max = parseInt(form.dataset.maxParticipants, 10) || 0;
    const filled = playersSection.querySelectorAll('.eta-player-row input').length;

    const currentEl = playersSection.querySelector('.eta-players-current');
    if (currentEl) currentEl.textContent = filled;

    const wrap = playersSection.querySelector('.eta-players-count');
    if (wrap) wrap.classList.toggle('eta-count-invalid', filled < min || filled > max);

    const addBtn = playersSection.querySelector('.eta-add-player-btn');
    if (addBtn) addBtn.disabled = max > 0 && filled >= max;

    playersSection.querySelectorAll('.eta-player-row').forEach((row, idx) => {
      const numEl = row.querySelector('.eta-player-row-num');
      if (numEl) numEl.textContent = idx + 1;
    });
  }

  function addPlayerRow() {
    if (!playersSection) return;
    const list = playersSection.querySelector('.eta-players-list');
    if (!list) return;

    const row = document.createElement('div');
    row.className = 'eta-player-row';
    row.innerHTML = `
      <span class="eta-player-row-num">${list.children.length + 1}</span>
      <input type="text" name="player_name[]" maxlength="150" placeholder="Player name">
      <button type="button" class="eta-remove-player-btn" aria-label="Remove player"><i class="ti ti-x"></i></button>
    `;
    list.appendChild(row);
    updatePlayerCount();
    const input = row.querySelector('input');
    if (input) input.focus();
  }

  function ensureMinPlayerRows() {
    if (!playersSection) return;
    const list = playersSection.querySelector('.eta-players-list');
    if (!list) return;
    const minRequired = parseInt(form.dataset.minParticipants, 10) || 1;
    while (list.children.length < minRequired) addPlayerRow();
  }

  if (playersSection) {
    playersSection.addEventListener('click', function (e) {
      if (e.target.closest('.eta-add-player-btn')) {
        addPlayerRow();
        return;
      }
      const removeBtn = e.target.closest('.eta-remove-player-btn');
      if (removeBtn) {
        removeBtn.closest('.eta-player-row').remove();
        updatePlayerCount();
      }
    });
    ensureMinPlayerRows();
  }

  function validateForm() {
    clearFormError();

    const participationType = form.dataset.participationType;

    const coachSelect = form.querySelector('.eta-coach-select');
    const otherCoachInput = form.querySelector('.eta-other-coach-input');
    if (coachSelect && coachSelect.value === 'OTHER' && (!otherCoachInput || !otherCoachInput.value.trim())) {
      showFormError('Please enter the coach name.');
      otherCoachInput?.focus();
      return false;
    }

    const collegeSelect = form.querySelector('.eta-college-select');
    const otherCollegeInput = form.querySelector('.eta-other-college-input');
    if (!collegeSelect || !collegeSelect.value) {
      showFormError('Please select a college.');
      return false;
    }
    if (collegeSelect.value === 'OTHER' && (!otherCollegeInput || !otherCollegeInput.value.trim())) {
      showFormError('Please enter the college name.');
      otherCollegeInput?.focus();
      return false;
    }

    const contactMobileInput = form.querySelector(
    'input[name="contact_mobile"]'
    );

    if (contactMobileInput) {
        const mobile = contactMobileInput.value.trim();

        if (mobile && !/^\d{1,15}$/.test(mobile)) {
            showFormError(
                'Contact mobile must contain only numbers and be 1 to 15 digits.'
            );

            contactMobileInput.focus();
            return false;
        }
    }

    if (participationType === 'TEAM') {
      const teamSelect = form.querySelector('.eta-team-select');
      const otherTeamInput = form.querySelector('.eta-other-team-input');
      if (!teamSelect || !teamSelect.value) {
        showFormError('Please select an internal team.');
        teamSelect?.focus();
        return false;
      }
      if (teamSelect.value === 'OTHER' && (!otherTeamInput || !otherTeamInput.value.trim())) {
        showFormError('Please enter the team name.');
        otherTeamInput?.focus();
        return false;
      }

      const min = parseInt(form.dataset.minParticipants, 10) || 0;
      const max = parseInt(form.dataset.maxParticipants, 10) || 0;
      const players = Array.from(form.querySelectorAll('input[name="player_name[]"]'))
        .map(i => i.value.trim())
        .filter(Boolean);

      const lowerNames = players.map(n => n.toLowerCase());
      if (new Set(lowerNames).size !== lowerNames.length) {
        showFormError('Duplicate player names are not allowed.');
        return false;
      }
      if (players.length < min) {
        showFormError(`At least ${min} player(s) are required.`);
        return false;
      }
      if (players.length > max) {
        showFormError(`No more than ${max} player(s) are allowed.`);
        return false;
      }
    } else {
      const entryNameInput = form.querySelector('input[name="entry_name"]');
      const entryName = entryNameInput ? entryNameInput.value.trim() : '';
      if (!entryName) {
        showFormError('Please enter your name before submitting.');
        entryNameInput?.focus();
        return false;
      }
    }

    return true;
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (!validateForm()) return;

    sendOtpBtn.disabled = true;
    sendOtpBtn.innerHTML = '<i class="ti ti-loader-2"></i> Sending...';

    fetch(form.dataset.sendOtpUrl, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken'), 'X-Requested-With': 'XMLHttpRequest' },
    })
      .then(res => res.json().then(data => ({ ok: res.ok, data })))
      .then(({ ok, data }) => {
        sendOtpBtn.disabled = false;
        sendOtpBtn.innerHTML = '<i class="ti ti-send"></i> Send Application';

        if (!ok || !data.success) {
          showFormError(data.error || 'Could not send verification code. Please try again.');
          return;
        }

        otpEmailEl.textContent = data.masked_email || 'your email';
        form.style.display = 'none';
        otpPanel.style.display = 'block';
        otpInput.value = '';
        clearOtpError();
        otpInput.focus();
        startResendCooldown(data.resend_in || 45);
        otpPanel.scrollIntoView({ behavior: 'smooth', block: 'center' });
      })
      .catch(() => {
        sendOtpBtn.disabled = false;
        sendOtpBtn.innerHTML = '<i class="ti ti-send"></i> Send Application';
        showFormError('Network error. Please try again.');
      });
  });

  function startResendCooldown(seconds) {
    let remaining = seconds;
    resendBtn.disabled = true;
    resendTimerEl.textContent = `(${remaining}s)`;
    if (resendTimer) clearInterval(resendTimer);
    resendTimer = setInterval(() => {
      remaining -= 1;
      if (remaining <= 0) {
        clearInterval(resendTimer);
        resendBtn.disabled = false;
        resendTimerEl.textContent = '';
      } else {
        resendTimerEl.textContent = `(${remaining}s)`;
      }
    }, 1000);
  }

  resendBtn.addEventListener('click', function () {
    if (resendBtn.disabled) return;
    resendBtn.disabled = true;
    clearOtpError();

    fetch(form.dataset.sendOtpUrl, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken'), 'X-Requested-With': 'XMLHttpRequest' },
    })
      .then(res => res.json().then(data => ({ ok: res.ok, data })))
      .then(({ ok, data }) => {
        if (!ok || !data.success) {
          showOtpError(data.error || 'Could not resend code. Please try again.');
          resendBtn.disabled = false;
          return;
        }
        otpEmailEl.textContent = data.masked_email || 'your email';
        startResendCooldown(data.resend_in || 45);
      })
      .catch(() => {
        showOtpError('Network error. Please try again.');
        resendBtn.disabled = false;
      });
  });

  backBtn.addEventListener('click', function () {
    otpPanel.style.display = 'none';
    form.style.display = 'block';
    clearOtpError();
  });

  verifyBtn.addEventListener('click', function () {
    const otp = otpInput.value.trim();
    clearOtpError();

    if (!/^\d{6}$/.test(otp)) {
      showOtpError('Please enter the 6-digit code.');
      return;
    }

    verifyBtn.disabled = true;
    verifyBtn.innerHTML = '<i class="ti ti-loader-2"></i> Verifying...';

    const fd = new FormData(form);
    fd.append('otp', otp);

    fetch(form.dataset.submitUrl, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken') },
      body: fd,
    })
      .then(res => res.json().then(data => ({ ok: res.ok, data })))
      .then(({ ok, data }) => {
        verifyBtn.disabled = false;
        verifyBtn.innerHTML = '<i class="ti ti-shield-check"></i> Verify &amp; Submit';

        if (!ok || !data.success) {
          showOtpError(data.error || 'Verification failed. Please try again.');
          return;
        }
        renderSubmittedState(data);
      })
      .catch(() => {
        verifyBtn.disabled = false;
        verifyBtn.innerHTML = '<i class="ti ti-shield-check"></i> Verify &amp; Submit';
        showOtpError('Network error. Please try again.');
      });
  });

  function renderSubmittedState(data) {
    const card = document.getElementById('etaFormCard');
    if (!card) return;

    const nameRow = data.participation_type === 'TEAM'
      ? `<div class="eta-summary-item"><span>Team Name</span><strong>${escapeHtml(data.entry_display)}</strong></div>`
      : `<div class="eta-summary-item"><span>Participant Name</span><strong>${escapeHtml(data.entry_display)}</strong></div>`;

    const playersHtml = (data.players && data.players.length)
      ? `<div class="eta-players-readonly"><span class="eta-info-label"><i class="ti ti-users"></i> Players</span><ul>${data.players.map(p => `<li>${escapeHtml(p)}</li>`).join('')}</ul></div>`
      : '';

    card.innerHTML = `
      <div class="eta-panel">
        <div class="eta-panel-icon eta-panel-icon-applied"><i class="ti ti-clock-hour-4"></i></div>
        <h2 class="eta-panel-title">Response Submitted</h2>
        <p class="eta-status-line eta-status-applied">${escapeHtml(data.status_display)}</p>
        <div class="eta-summary-grid">
          ${nameRow}
          <div class="eta-summary-item"><span>College</span><strong>${escapeHtml(data.college_name || '—')}</strong></div>
          <div class="eta-summary-item"><span>Coach</span><strong>${escapeHtml(data.coach_name || '—')}</strong></div>
          <div class="eta-summary-item"><span>Contact Person</span><strong>${escapeHtml(data.contact_person || '—')}</strong></div>
          <div class="eta-summary-item"><span>Contact Mobile</span><strong>${escapeHtml(data.contact_mobile || '—')}</strong></div>
          <div class="eta-summary-item"><span>Player Count</span><strong>${data.players_count}</strong></div>
          <div class="eta-summary-item"><span>Submitted On</span><strong>${escapeHtml(data.applied_at_display)}</strong></div>
        </div>
        ${playersHtml}
      </div>
    `;
    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str == null ? '' : String(str);
    return div.innerHTML;
  }
});