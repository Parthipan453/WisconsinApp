/* ═══════════════════════════════════════════════════════════════
   Builder Preview — Conditional logic for live preview
   Drives show/hide from each field's data-conditional-rules.
   Mirror of the portal behavior in validation.js (scoped, safe).
   ═══════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  function norm(v) {
    var s = String(v == null ? '' : v).trim().toLowerCase();
    if (['true', 'on', 'yes', '1', 'y', 't'].indexOf(s) !== -1) return 'yes';
    if (['false', 'off', 'no', '0', '', 'n', 'f'].indexOf(s) !== -1) return 'no';
    return s;
  }

  function getVal(code) {
    var el = document.querySelector('[name="' + code + '"]:not([type="hidden"])') || document.querySelector('[name="' + code + '"]');
    if (!el) return '';
    if (el.type === 'radio') {
      var checked = document.querySelector('[name="' + code + '"]:checked');
      return checked ? checked.value : '';
    }
    if (el.type === 'checkbox') return el.checked ? 'yes' : '';
    return el.value;
  }

  function matchRule(rule) {
    var cv = norm(getVal(rule.f));
    var rv = norm(rule.v);
    var isEmpty = cv === '';
    var op = rule.op, a, b;
    if (op === 'neq') return isEmpty || cv !== rv;
    if (op === 'not_empty') return !isEmpty;
    if (op === 'is_empty') return isEmpty;
    if (op === 'contains') return cv.indexOf(rv) !== -1;
    a = parseFloat(cv); b = parseFloat(rv);
    if (op === 'gt') return !isNaN(a) && !isNaN(b) && a > b;
    if (op === 'gte') return !isNaN(a) && !isNaN(b) && a >= b;
    if (op === 'lt') return !isNaN(a) && !isNaN(b) && a < b;
    if (op === 'lte') return !isNaN(a) && !isNaN(b) && a <= b;
    if (op === 'in') return rv.split(',').map(function (x) { return x.trim(); }).indexOf(cv) !== -1;
    if (op === 'not_in') return rv.split(',').map(function (x) { return x.trim(); }).indexOf(cv) === -1;
    if (op === 'checked') return cv === 'yes';
    if (op === 'not_checked') return cv === 'no';
    return isEmpty || cv === rv;
  }

  function evaluate(target) {
    var raw = target.getAttribute('data-conditional-rules');
    if (!raw) return true;
    var rules;
    try { rules = JSON.parse(raw); } catch (e) { return true; }
    var andRules = rules.filter(function (r) { return (r.l || 'AND') === 'AND'; });
    var orRules = rules.filter(function (r) { return r.l === 'OR'; });
    var andOk = andRules.length === 0 || andRules.every(matchRule);
    var orOk = orRules.length === 0 || orRules.some(matchRule);
    return andOk && orOk;
  }

  function setGroupState(t, show) {
    var inp = t.querySelector('input:not([type="hidden"]), select, textarea') || t.querySelector('input, select, textarea');
    if (show) {
      if (inp && t.getAttribute('data-orig-required') === null) {
        t.setAttribute('data-orig-required', inp.required ? 'true' : 'false');
      }
      if (inp) inp.required = t.getAttribute('data-orig-required') === 'true';
      t.style.display = '';
      if (inp && inp.required) {
        var label = t.querySelector('label');
        if (label && !t.querySelector('label .req-star')) {
          var star = document.createElement('span');
          star.className = 'text-c05 req-star';
          star.textContent = '*';
          label.appendChild(star);
        }
      }
    } else {
      if (inp) inp.required = false;
      t.style.display = 'none';
      var err = t.querySelector('.uw-field-error');
      if (err) err.remove();
      t.querySelectorAll('.error').forEach(function (e) { e.classList.remove('error'); });
      var star = t.querySelector('label .req-star');
      if (star) star.remove();
    }
  }

  function refresh() {
    document.querySelectorAll('[data-conditional-target]').forEach(function (trig) {
      var sel = trig.getAttribute('data-conditional-target');
      if (!sel) return;
      document.querySelectorAll(sel).forEach(function (t) {
        var show = false;
        try { show = evaluate(t); } catch (e) {}
        var simpleCode = t.getAttribute('data-conditional');
        if (!show && simpleCode && simpleCode.length) {
          var cv = norm(getVal(simpleCode));
          show = !cv || cv === norm(t.getAttribute('data-conditional-value') || 'yes');
        }
        setGroupState(t, show);
      });
    });
  }

  function bind() {
    document.querySelectorAll('[data-conditional-trigger]').forEach(function (trig) {
      if (trig.getAttribute('data-prev-bound')) return;
      trig.setAttribute('data-prev-bound', '1');
      var code = trig.getAttribute('data-conditional-trigger');
      document.querySelectorAll('[name="' + code + '"]').forEach(function (inp) {
        if (inp.type === 'radio' || inp.type === 'checkbox') {
          inp.addEventListener('change', refresh);
        } else {
          inp.addEventListener('input', refresh);
          inp.addEventListener('change', refresh);
        }
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    bind();
    setTimeout(refresh, 60);
  });
})();