/* ══════════════════════════════════════════════════════════════
   Universities of Wisconsin Applicant Portal — JavaScript
   ══════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ─── Init Lucide Icons ─── */
  function initLucide() {
    if (typeof lucide !== 'undefined' && lucide.createIcons) {
      lucide.createIcons();
    }
  }

  /* ─── Tab Switching ─── */
  window.switchTab = function (tabId) {
    // Update tab buttons
    document.querySelectorAll('.dashboard-tab').forEach(function (btn) {
      btn.classList.remove('active');
      btn.setAttribute('aria-selected', 'false');
    });

    var activeBtn = document.querySelector('.dashboard-tab[data-tab="' + tabId + '"]');
    if (activeBtn) {
      activeBtn.classList.add('active');
      activeBtn.setAttribute('aria-selected', 'true');
    }

    // Show/hide tab content
    document.querySelectorAll('.tab-content').forEach(function (content) {
      content.style.display = 'none';
    });

    var targetContent = document.getElementById('tab-' + tabId);
    if (targetContent) {
      targetContent.style.display = 'block';
    }
  };

  /* ─── Prevent Double Submit (shows loading state on submit buttons) ─── */
  function initSubmitLoading() {
    document.addEventListener('submit', function (e) {
      var form = e.target;
      if (!form || form.tagName !== 'FORM') return;
      var btn = form.querySelector('button[type="submit"][data-uw-loading-text]');
      if (!btn) return;
      if (e.defaultPrevented) return;
      if (btn.disabled) {
        e.preventDefault();
        return;
      }
      if (!btn.getAttribute('data-uw-original-text')) {
        btn.setAttribute('data-uw-original-text', btn.innerHTML);
      }
      btn.disabled = true;
      btn.classList.add('is-loading');
      btn.innerHTML = '<span class="spinner-border spinner-border-sm" aria-hidden="true" style="width:14px;height:14px;border-width:2px;margin-right:6px;vertical-align:-2px"></span>' +
        (btn.getAttribute('data-uw-loading-text') || 'Submitting\u2026');
    });
  }

  /* ─── Button Ripple Effect ─── */
  function initRippleEffect() {
    document.querySelectorAll('.start-app-btn, .uw-btn, .empty-state-btn').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        var rect = btn.getBoundingClientRect();
        var ripple = document.createElement('span');
        ripple.style.position = 'absolute';
        ripple.style.borderRadius = '50%';
        ripple.style.background = 'rgba(255,255,255,0.4)';
        ripple.style.width = '20px';
        ripple.style.height = '20px';
        ripple.style.left = (e.clientX - rect.left - 10) + 'px';
        ripple.style.top = (e.clientY - rect.top - 10) + 'px';
        ripple.style.pointerEvents = 'none';
        ripple.style.animation = 'ripple 0.6s ease-out';
        ripple.style.transform = 'scale(0)';
        btn.style.position = 'relative';
        btn.style.overflow = 'hidden';
        btn.appendChild(ripple);
        setTimeout(function () { ripple.remove(); }, 700);
      });
    });
  }

  /* ─── Mobile Sidebar Toggle ─── */
  function initMobileSidebar() {
    var nav = document.querySelector('.dash-top-nav');
    var toggler = document.querySelector('.dash-top-toggler');
    var backdrop = document.querySelector('.dash-menu-backdrop');
    if (!nav || !toggler || !backdrop) return;

    function setOpen(open) {
      nav.classList.toggle('open', open);
      backdrop.classList.toggle('open', open);
      toggler.setAttribute('aria-expanded', String(open));
      backdrop.setAttribute('aria-hidden', String(!open));
    }

    toggler.addEventListener('click', function () { setOpen(!nav.classList.contains('open')); });
    backdrop.addEventListener('click', function () { setOpen(false); });
    nav.querySelectorAll('.dash-top-menu a').forEach(function (link) {
      link.addEventListener('click', function () { setOpen(false); });
    });
  }

  /* ─── Application Step Navigation Accordions ─── */
  function initSubnavAccordions() {
    document.querySelectorAll('.js-subnav-sections').forEach(function (section) {
      var groups = section.querySelectorAll('.portal-subnav-group');
      if (!groups.length) return;

      function setExpanded(group, expanded) {
        group.classList.toggle('open', expanded);
        var title = group.querySelector('.portal-subnav-group-title');
        if (title) title.setAttribute('aria-expanded', String(expanded));
      }

      groups.forEach(function (group) {
        setExpanded(group, Boolean(group.querySelector('.portal-subnav-item.active')));
        var title = group.querySelector('.portal-subnav-group-title');
        if (!title) return;

        title.addEventListener('click', function () {
          var expanding = !group.classList.contains('open');
          groups.forEach(function (sibling) {
            setExpanded(sibling, sibling === group && expanding);
          });
        });
      });
    });
  }

  /* ─── Auto-hide Toasts ─── */
  function initToasts() {
    var toasts = document.querySelectorAll('.auth-toast');
    if (!toasts.length) return;
    setTimeout(function () {
      toasts.forEach(function (t) {
        t.classList.add('auth-toast-hide');
        setTimeout(function () { if (t.parentNode) t.remove(); }, 300);
      });
    }, 5000);
  }

  window.closeToast = function () {
    document.querySelectorAll('.auth-toast').forEach(function (t) {
      t.classList.add('auth-toast-hide');
      setTimeout(function () { if (t.parentNode) t.remove(); }, 300);
    });
  };

  /* ─── Animate Progress Bars on Scroll ─── */
  function initProgressAnimations() {
    var progressFills = document.querySelectorAll('.progress-fill');
    if (!progressFills.length) return;

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          var fill = entry.target;
          var width = fill.style.width;
          fill.style.width = '0%';
          setTimeout(function () {
            fill.style.transition = 'width 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
            fill.style.width = width;
          }, 100);
          observer.unobserve(fill);
        }
      });
    }, { threshold: 0.1 });

    progressFills.forEach(function (fill) {
      observer.observe(fill);
    });
  }

  /* ─── Choices.js Init ─── */
  function initChoices() {
    if (typeof Choices === 'undefined') return;
    var selectors = 'select.uw-input,select.uw-select,select.uw-campus-select,select.auth-input,.auth-form-group select,select.find-term-select,select.find-program-select,select.mil-field-select';
    document.querySelectorAll(selectors).forEach(function (el) {
      if (el.closest('.uw-phone-wrapper')) return;
      if (el.closest('.choices')) return;
      try {
        new Choices(el, {
          searchEnabled: el.options.length > 10,
          shouldSort: false,
          itemSelectText: '',
          placeholder: true,
          placeholderValue: el.options[0] && el.options[0].value === '' ? el.options[0].text : '',
          searchPlaceholderValue: 'Type to search...',
          noChoicesText: 'No options available',
          noResultsText: 'No results found',
          removeItemButton: el.multiple,
          silent: true,
        });
      } catch (e) {}
    });
  }

  /* ─── Date Selects Init ─── */
  function initDateSelects() {
    document.querySelectorAll('.uw-date-selects').forEach(function (w) {
      var hidden = w.querySelector('input[type="hidden"]');
      var parts = {
        m: w.querySelector('[data-part="month"]'),
        d: w.querySelector('[data-part="day"]'),
        y: w.querySelector('[data-part="year"]')
      };
      if (!parts.m) return;
      function sync() {
        var m = parts.m.value, d = parts.d ? parts.d.value : '', y = parts.y ? parts.y.value : '';
        if (w.hasAttribute('data-year-field')) {
          hidden.value = m && y ? y + '-' + m : y || '';
        } else {
          hidden.value = m && d && y ? y + '-' + m + '-' + d : '';
        }
        hidden.dispatchEvent(new Event('change', { bubbles: true }));
      }
      parts.m.addEventListener('change', sync);
      if (parts.d) parts.d.addEventListener('change', sync);
      if (parts.y) parts.y.addEventListener('change', sync);
    });
  }

  /* ─── Section Collapse (for info/workflow pages) ─── */

  window.filterProgs = function (q) {
    q = q.toLowerCase();
    document.querySelectorAll('.pi').forEach(function (e) {
      e.style.display = (!q || (e.dataset.search || '').toLowerCase().includes(q)) ? '' : 'none';
    });
    document.querySelectorAll('.dg').forEach(function (g) {
      var v = [].slice.call(g.querySelectorAll('.pi')).some(function (i) {
        return i.style.display !== 'none';
      });
      g.style.display = v ? '' : 'none';
    });
  };

  window.sel = { progId: null, progName: null, degreeName: null };

  /* ─── Premium Form Input Interactions ─── */
  function initPremiumForm() {
    var form = document.querySelector('.uw-form-premium');
    if (!form) return;

    form.querySelectorAll('.uw-input').forEach(function (input) {
      input.addEventListener('focus', function () {
        var group = input.closest('.uw-form-group');
        if (group) group.classList.add('focused');
      });
      input.addEventListener('blur', function () {
        var group = input.closest('.uw-form-group');
        if (group) group.classList.remove('focused');
        if (input.hasAttribute('required') && input.value.trim()) {
          input.classList.remove('error');
          input.classList.add('success');
        } else if (input.hasAttribute('required') && !input.value.trim()) {
          input.classList.remove('success');
        }
      });
    });

    form.addEventListener('input', function (e) {
      var input = e.target.closest('.uw-input');
      if (!input) return;
      input.classList.remove('error');
      if (input.value.trim() && input.hasAttribute('required')) {
        input.classList.add('success');
      } else {
        input.classList.remove('success');
      }
    });

    form.querySelectorAll('.uw-help-tooltip').forEach(function (tip) {
      tip.addEventListener('click', function (e) {
        e.stopPropagation();
        var text = tip.querySelector('.uw-tooltip-text');
        if (text) {
          var isVisible = text.style.visibility === 'visible';
          form.querySelectorAll('.uw-help-tooltip .uw-tooltip-text').forEach(function (t) {
            t.style.visibility = 'hidden';
            t.style.opacity = '0';
          });
          if (!isVisible) {
            text.style.visibility = 'visible';
            text.style.opacity = '1';
          }
        }
      });
    });

    document.addEventListener('click', function () {
      form.querySelectorAll('.uw-help-tooltip .uw-tooltip-text').forEach(function (t) {
        t.style.visibility = 'hidden';
        t.style.opacity = '0';
      });
    });

    var footer = form.querySelector('.uw-form-footer');
    if (footer) {
      setTimeout(function () { footer.style.opacity = '1'; }, 300);
    }
  }

  /* ─── Form Autosave Progress Indicator ─── */
  function initAutosaveStatus() {
    var forms = document.querySelectorAll('form[data-dynamic-autosave]');
    forms.forEach(function (form) {
      form.addEventListener('change', function () {
        var status = this.querySelector('.uw-autosave-status');
        if (status) status.textContent = 'Unsaved changes…';
      });
    });
  }

  /* ─── Military Benefits Page Init ─── */
  function initMilitaryBenefits() {
    var form = document.getElementById('milForm');
    if (!form) return;
    document.querySelectorAll('.mil-datepicker').forEach(function (el) {
      if (el.readOnly) return;
      if (typeof flatpickr !== 'undefined') {
        flatpickr(el, {
          dateFormat: 'm/d/Y',
          maxDate: 'today',
          minDate: new Date(1920, 0, 1),
          disableMobile: true,
        });
      }
    });
    document.querySelectorAll('.mil-accordion-header').forEach(function (header) {
      if (header.dataset.militaryAccordionInitialized === 'true') return;
      header.dataset.militaryAccordionInitialized = 'true';
      header.addEventListener('click', function () {
        var accordion = this.closest('.mil-accordion');
        var body = accordion.querySelector('.mil-accordion-body');
        var icon = this.querySelector('.mil-accordion-icon');
        var isOpen = accordion.classList.contains('open');
        if (isOpen) {
          accordion.classList.remove('open');
          this.setAttribute('aria-expanded', 'false');
          body.style.maxHeight = null;
          if (icon) icon.style.transform = 'rotate(0deg)';
        } else {
          accordion.classList.add('open');
          this.setAttribute('aria-expanded', 'true');
          body.style.maxHeight = body.scrollHeight + 'px';
          if (icon) icon.style.transform = 'rotate(180deg)';
        }
      });
    });
  }

  window.initMilitaryBenefits = initMilitaryBenefits;

  /* ─── Builder: Primary + Backup Program Picker ─── */
  function initProgramPicker() {
    var form = document.getElementById('createForm');
    var tiles = document.querySelectorAll('.builder-content .pi.prog-item[data-pid]');
    if (!form || !tiles.length) return;
    var base = form.getAttribute('action') || '';
    var btn = document.getElementById('progContinue');
    var params = new URLSearchParams(window.location.search);
    var state = { pid: params.get('pid') || null, bid: params.get('bid') || null };

    function refresh() {
      tiles.forEach(function (t) {
        var id = String(t.dataset.pid);
        var isP = id === String(state.pid);
        var isB = id === String(state.bid);
        t.classList.toggle('selected', isP);
        t.classList.toggle('prog-backup-selected', isB);
        var pBtn = t.querySelector('.prog-choice-primary');
        var bBtn = t.querySelector('.prog-choice-backup');
        if (pBtn) {
          pBtn.classList.toggle('active', isP);
          pBtn.setAttribute('aria-pressed', isP ? 'true' : 'false');
        }
        if (bBtn) {
          if (isP) {
            bBtn.style.display = 'none';
          } else if (state.pid) {
            bBtn.style.display = '';
            bBtn.classList.toggle('active', isB);
            bBtn.setAttribute('aria-pressed', isB ? 'true' : 'false');
          } else {
            bBtn.style.display = 'none';
            bBtn.classList.remove('active');
          }
        }
      });
      if (!btn) return;
      if (state.pid) {
        var url = base + (base.indexOf('?') === -1 ? '?' : '&') + 'pid=' + encodeURIComponent(state.pid);
        if (state.bid) url += '&bid=' + encodeURIComponent(state.bid);
        btn.href = url;
        btn.classList.remove('d-none');
      } else {
        btn.classList.add('d-none');
      }
    }

    tiles.forEach(function (t) {
      var pBtn = t.querySelector('.prog-choice-primary');
      if (pBtn) {
        pBtn.addEventListener('click', function (e) {
          e.stopPropagation();
          var id = String(t.dataset.pid);
          if (state.pid === id) {
            state.pid = null;
            state.bid = null;
          } else {
            state.pid = id;
            if (state.bid === id) state.bid = null;
          }
          refresh();
        });
      }
      var bBtn = t.querySelector('.prog-choice-backup');
      if (bBtn) {
        bBtn.addEventListener('click', function (e) {
          e.stopPropagation();
          var id = String(t.dataset.pid);
          if (id === String(state.pid)) return;
          if (state.bid === id) { state.bid = null; } else { state.bid = id; }
          refresh();
        });
      }
    });

    refresh();
  }

  window.initProgramPicker = initProgramPicker;

  document.addEventListener('DOMContentLoaded', function () {
    initLucide();
    initSubmitLoading();
    initRippleEffect();
    initMobileSidebar();
    initSubnavAccordions();
    initToasts();
    initProgressAnimations();
    initChoices();
    initDateSelects();
    initPremiumForm();
    initAutosaveStatus();
    initMilitaryBenefits();
    initProgramPicker();
  });

  var formObserver = new MutationObserver(function () {
    initPremiumForm();
    initChoices();
    initMilitaryBenefits();
  });
  formObserver.observe(document.body, { childList: true, subtree: true });

})();
