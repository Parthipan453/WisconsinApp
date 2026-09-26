
(function () {
  'use strict';

  var _gid = 0;
  function uid() { return 'vl' + (++_gid); }

  function getGroup(input) {
    return input.closest('.auth-form-group');
  }

  function showMsg(input, msg) {
    var g = getGroup(input);
    if (!g) return;
    var el = g.querySelector('.auth-live-msg');
    if (!el) {
      el = document.createElement('span');
      el.className = 'auth-live-msg';
      g.appendChild(el);
    }
    el.textContent = msg;
    el.style.display = 'block';
  }

  function hideMsg(input) {
    var g = getGroup(input);
    if (!g) return;
    var el = g.querySelector('.auth-live-msg');
    if (el) { el.textContent = ''; el.style.display = 'none'; }
  }

  function checkField(input) {
    var g = getGroup(input);
    if (!g) return;

    var val = input.value;
    var regex = input.getAttribute('data-live-regex');
    var match = input.getAttribute('data-match');
    var valid = true;
    var msg = '';

    input.classList.remove('auth-valid', 'auth-invalid', 'error');

    if (val.length === 0) { hideMsg(input); return; }

    if (regex) {
      try {
        if (!new RegExp(regex).test(val)) {
          valid = false;
          msg = input.getAttribute('data-live-msg') || 'Invalid format.';
        }
      } catch (e) {}
    }

    if (valid && match) {
      var target = document.querySelector('[name="' + match + '"]');
      if (target && val !== target.value) {
        valid = false;
        msg = 'Passwords do not match.';
      }
    }

    if (valid) {
      input.classList.add('auth-valid');
      hideMsg(input);
    } else {
      input.classList.add('auth-invalid');
      showMsg(input, msg);
    }
  }

  function pwChecklist(input) {
    var g = getGroup(input);
    if (!g) return;
    var cl = g.querySelector('.auth-pw-checklist');
    if (!cl) return;
    var v = input.value || '';
    var checks = { length: v.length >= 6, upper: /[A-Z]/.test(v), lower: /[a-z]/.test(v), number: /[0-9]/.test(v), special: /[@$!%*#?&]/.test(v) };
    cl.querySelectorAll('[data-pw-req]').forEach(function (li) {
      var ok = checks[li.getAttribute('data-pw-req')];
      li.classList.toggle('pw-met', ok);
      var ic = li.querySelector('i');
      if (ic) ic.className = ok ? 'ti ti-circle-check-filled' : 'ti ti-circle';
    });
  }

  function togglePw(btn) {
    var wrap = btn.closest('.auth-password-wrapper');
    if (!wrap) return;
    var inp = wrap.querySelector('input');
    if (!inp) return;
    var ic = btn.querySelector('i');
    if (inp.type === 'password') {
      inp.type = 'text';
      if (ic) ic.className = 'fas fa-eye-slash';
    } else {
      inp.type = 'password';
      if (ic) ic.className = 'fas fa-eye';
    }
  }

  function closeToast() {
    var t = document.getElementById('auth-toast');
    if (!t) return;
    t.classList.add('auth-toast-hide');
    setTimeout(function () { if (t.parentNode) t.remove(); }, 300);
  }

  function showToast(title, msg, type) {
    var old = document.getElementById('auth-toast');
    if (old) old.remove();
    type = type || 'error';
    var icons = {
      error: '<svg class="auth-toast-icon error" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/></svg>',
      success: '<svg class="auth-toast-icon success" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/></svg>',
      info: '<svg class="auth-toast-icon" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>',
    };
    var t = document.createElement('div');
    t.className = 'auth-toast';
    t.id = 'auth-toast';
    t.innerHTML = (icons[type] || icons.error) + '<div class="auth-toast-content"><strong>' + title + '</strong><small>' + msg + '</small></div><button class="auth-toast-close" type="button"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M18 6L6 18M6 6l12 12"/></svg></button>';
    t.querySelector('.auth-toast-close').addEventListener('click', closeToast);
    document.body.appendChild(t);
    setTimeout(closeToast, 4000);
  }

  document.addEventListener('DOMContentLoaded', function () {

    /* ── Parallax ── */
    var eco = document.querySelector('.floating-ecosystem');
    if (eco) {
      var els = eco.querySelectorAll('.glass-card, .circular-icon, .floating-avatar, .avatar-group, .glow-dot');
      document.addEventListener('mousemove', function (e) {
        var r = eco.getBoundingClientRect();
        var x = (e.clientX - r.left) / r.width - 0.5;
        var y = (e.clientY - r.top) / r.height - 0.5;
        els.forEach(function (el) {
          var sp = parseFloat(el.getAttribute('data-parallax-speed') || '0.03');
          el.style.transform = 'translate(' + (x * sp * 100) + 'px, ' + (y * sp * 100) + 'px)';
        });
      });
    }

    /* ── Particles ── */
    if (eco && !eco.querySelector('.particle')) {
      for (var i = 0; i < 40; i++) {
        var p = document.createElement('div');
        p.className = 'particle';
        var sz = Math.random() * 3 + 2;
        p.style.cssText = 'width:' + sz + 'px;height:' + sz + 'px;left:' + (Math.random() * 100) + '%;top:' + (Math.random() * 100) + '%;animation:float-up ' + (Math.random() * 20 + 15) + 's ease-in-out ' + (Math.random() * 10) + 's infinite;opacity:' + (Math.random() * 0.3 + 0.1) + ';background:rgba(' + (Math.floor(Math.random() * 128 + 128)) + ',' + (Math.floor(Math.random() * 128 + 128)) + ',' + (Math.floor(Math.random() * 128 + 128)) + ',0.6)';
        eco.appendChild(p);
      }
    }

    /* ── Live field validation ── */
    document.querySelectorAll('[data-live-regex], [data-match]').forEach(function (inp) {
      var id = uid();
      inp.dataset.vlId = id;

      inp.addEventListener('input', function () { checkField(this); });
      inp.addEventListener('blur', function () { checkField(this); });
      if (inp.tagName === 'SELECT') {
        inp.addEventListener('change', function () { checkField(this); });
      }

      var match = inp.getAttribute('data-match');
      if (match) {
        var target = document.querySelector('[name="' + match + '"]');
        if (target) {
          target.addEventListener('input', function () {
            var paired = document.querySelector('[data-vl-id="' + id + '"]');
            if (paired) checkField(paired);
          });
        }
      }
    });

    /* ── Password checklist ── */
    document.querySelectorAll('[data-password-checklist]').forEach(function (inp) {
      inp.addEventListener('input', function () { pwChecklist(this); });
      pwChecklist(inp);
    });

    /* ── Password toggle ── */
    document.querySelectorAll('.auth-pw-toggle').forEach(function (btn) {
      btn.addEventListener('click', function () { togglePw(this); });
    });

    /* ── Form submit validation ── */
    document.querySelectorAll('.auth-form-validate').forEach(function (form) {
      form.addEventListener('submit', function (e) {
        var firstErr = null;
        var inputs = form.querySelectorAll('input');
        inputs.forEach(function (inp) {
          inp.classList.remove('error');
          if (!inp.value && (inp.hasAttribute('required') || inp.getAttribute('data-live-regex'))) {
            inp.classList.add('error');
            if (!firstErr) firstErr = inp;
          }
        });

        var pw = form.querySelector('input[name="password"]');
        var cpw = form.querySelector('input[name="confirm_password"]');
        if (pw && cpw && cpw.value && pw.value !== cpw.value) {
          cpw.classList.add('error');
          if (!firstErr) firstErr = cpw;
          showToast('Passwords do not match', 'Please make sure both passwords are identical.', 'error');
          e.preventDefault();
          return;
        }

        if (firstErr) {
          e.preventDefault();
          showToast('Missing fields', 'Please fill in all required fields before continuing.', 'error');
          firstErr.scrollIntoView({ behavior: 'smooth', block: 'center' });
          firstErr.focus();
        }
      });
    });
  });

  window.closeToast = closeToast;
  window.showToast = showToast;
})();
