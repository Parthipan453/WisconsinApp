(function () {
  'use strict';

  var countries = [
    {name:"United States",code:"US",dial:"+1",regex:"^\\d{10}$",example:"5551234567"},
    {name:"United Kingdom",code:"GB",dial:"+44",regex:"^\\d{10}$",example:"7911123456"},
    {name:"Canada",code:"CA",dial:"+1",regex:"^\\d{10}$",example:"5551234567"},
    {name:"Afghanistan",code:"AF",dial:"+93",regex:"^\\d{9}$",example:"701234567"},
    {name:"Albania",code:"AL",dial:"+355",regex:"^\\d{9}$",example:"691234567"},
    {name:"Algeria",code:"DZ",dial:"+213",regex:"^\\d{9}$",example:"551234567"},
    {name:"Argentina",code:"AR",dial:"+54",regex:"^\\d{10}$",example:"1151234567"},
    {name:"Australia",code:"AU",dial:"+61",regex:"^\\d{9}$",example:"412345678"},
    {name:"Austria",code:"AT",dial:"+43",regex:"^\\d{10}$",example:"6641234567"},
    {name:"Bangladesh",code:"BD",dial:"+880",regex:"^\\d{10}$",example:"1712345678"},
    {name:"Belgium",code:"BE",dial:"+32",regex:"^\\d{9}$",example:"471234567"},
    {name:"Brazil",code:"BR",dial:"+55",regex:"^\\d{10,11}$",example:"11981234567"},
    {name:"China",code:"CN",dial:"+86",regex:"^\\d{11}$",example:"13800138000"},
    {name:"Colombia",code:"CO",dial:"+57",regex:"^\\d{10}$",example:"3001234567"},
    {name:"Denmark",code:"DK",dial:"+45",regex:"^\\d{8}$",example:"12345678"},
    {name:"Egypt",code:"EG",dial:"+20",regex:"^\\d{10}$",example:"1001234567"},
    {name:"Ethiopia",code:"ET",dial:"+251",regex:"^\\d{9}$",example:"911234567"},
    {name:"Finland",code:"FI",dial:"+358",regex:"^\\d{9}$",example:"401234567"},
    {name:"France",code:"FR",dial:"+33",regex:"^\\d{9}$",example:"612345678"},
    {name:"Germany",code:"DE",dial:"+49",regex:"^\\d{10,11}$",example:"15112345678"},
    {name:"Ghana",code:"GH",dial:"+233",regex:"^\\d{9}$",example:"201234567"},
    {name:"Greece",code:"GR",dial:"+30",regex:"^\\d{10}$",example:"6912345678"},
    {name:"Hong Kong",code:"HK",dial:"+852",regex:"^\\d{8}$",example:"51234567"},
    {name:"India",code:"IN",dial:"+91",regex:"^\\d{10}$",example:"9876543210"},
    {name:"Indonesia",code:"ID",dial:"+62",regex:"^\\d{10,12}$",example:"81234567890"},
    {name:"Ireland",code:"IE",dial:"+353",regex:"^\\d{9}$",example:"851234567"},
    {name:"Israel",code:"IL",dial:"+972",regex:"^\\d{9}$",example:"501234567"},
    {name:"Italy",code:"IT",dial:"+39",regex:"^\\d{10}$",example:"3312345678"},
    {name:"Jamaica",code:"JM",dial:"+1",regex:"^\\d{10}$",example:"8761234567"},
    {name:"Japan",code:"JP",dial:"+81",regex:"^\\d{10,11}$",example:"9012345678"},
    {name:"Jordan",code:"JO",dial:"+962",regex:"^\\d{9}$",example:"791234567"},
    {name:"Kenya",code:"KE",dial:"+254",regex:"^\\d{9}$",example:"712345678"},
    {name:"South Korea",code:"KR",dial:"+82",regex:"^\\d{10,11}$",example:"1012345678"},
    {name:"Kuwait",code:"KW",dial:"+965",regex:"^\\d{8}$",example:"51234567"},
    {name:"Lebanon",code:"LB",dial:"+961",regex:"^\\d{7,8}$",example:"3123456"},
    {name:"Malaysia",code:"MY",dial:"+60",regex:"^\\d{9,10}$",example:"123456789"},
    {name:"Mexico",code:"MX",dial:"+52",regex:"^\\d{10}$",example:"5512345678"},
    {name:"Netherlands",code:"NL",dial:"+31",regex:"^\\d{9}$",example:"612345678"},
    {name:"New Zealand",code:"NZ",dial:"+64",regex:"^\\d{9}$",example:"212345678"},
    {name:"Nigeria",code:"NG",dial:"+234",regex:"^\\d{10}$",example:"8012345678"},
    {name:"Norway",code:"NO",dial:"+47",regex:"^\\d{8}$",example:"41234567"},
    {name:"Pakistan",code:"PK",dial:"+92",regex:"^\\d{10}$",example:"3012345678"},
    {name:"Philippines",code:"PH",dial:"+63",regex:"^\\d{10}$",example:"9171234567"},
    {name:"Poland",code:"PL",dial:"+48",regex:"^\\d{9}$",example:"601234567"},
    {name:"Portugal",code:"PT",dial:"+351",regex:"^\\d{9}$",example:"912345678"},
    {name:"Qatar",code:"QA",dial:"+974",regex:"^\\d{8}$",example:"33123456"},
    {name:"Russia",code:"RU",dial:"+7",regex:"^\\d{10}$",example:"9123456789"},
    {name:"Saudi Arabia",code:"SA",dial:"+966",regex:"^\\d{9}$",example:"501234567"},
    {name:"Singapore",code:"SG",dial:"+65",regex:"^\\d{8}$",example:"91234567"},
    {name:"South Africa",code:"ZA",dial:"+27",regex:"^\\d{9}$",example:"821234567"},
    {name:"Spain",code:"ES",dial:"+34",regex:"^\\d{9}$",example:"612345678"},
    {name:"Sri Lanka",code:"LK",dial:"+94",regex:"^\\d{9}$",example:"712345678"},
    {name:"Sweden",code:"SE",dial:"+46",regex:"^\\d{9}$",example:"701234567"},
    {name:"Switzerland",code:"CH",dial:"+41",regex:"^\\d{9}$",example:"791234567"},
    {name:"Taiwan",code:"TW",dial:"+886",regex:"^\\d{9}$",example:"912345678"},
    {name:"Thailand",code:"TH",dial:"+66",regex:"^\\d{9}$",example:"812345678"},
    {name:"Turkey",code:"TR",dial:"+90",regex:"^\\d{10}$",example:"5321234567"},
    {name:"Uganda",code:"UG",dial:"+256",regex:"^\\d{9}$",example:"771234567"},
    {name:"Ukraine",code:"UA",dial:"+380",regex:"^\\d{9}$",example:"501234567"},
    {name:"United Arab Emirates",code:"AE",dial:"+971",regex:"^\\d{9}$",example:"501234567"},
    {name:"Venezuela",code:"VE",dial:"+58",regex:"^\\d{10}$",example:"4121234567"},
    {name:"Vietnam",code:"VN",dial:"+84",regex:"^\\d{9,10}$",example:"912345678"},
  ];

  var phoneCountryMap = {};
  countries.forEach(function (c) { phoneCountryMap[c.code] = c; });

  function flagEmoji(code) {
    if (!code || code.length !== 2) return '';
    return code.toUpperCase().replace(/./g, function (ch) {
      return String.fromCodePoint(0x1F1E6 + ch.charCodeAt(0) - 65);
    });
  }

  function initSearchableDropdowns() {
    var wrappers = document.querySelectorAll('.uw-country-wrapper');
    wrappers.forEach(function (wrapper) {
      var input = wrapper.querySelector('input[data-country-search="true"]');
      var dropdown = wrapper.querySelector('.uw-country-dropdown');
      var search = wrapper.querySelector('.uw-country-search');
      var list = wrapper.querySelector('.uw-country-list');
      if (!input || !dropdown || !search || !list) return;

      var items = list.querySelectorAll('li');

      function filterItems(q) {
        var f = q.toLowerCase();
        items.forEach(function (li) {
          var name = (li.getAttribute('data-value') || '').toLowerCase();
          li.style.display = (!f || name.indexOf(f) > -1) ? '' : 'none';
        });
      }

      function selectItem(li) {
        input.value = li.getAttribute('data-value') || '';
        dropdown.classList.remove('open');
        items.forEach(function (i) { i.classList.remove('selected'); });
        li.classList.add('selected');
        search.value = '';
        filterItems('');
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('blur'));
      }

    input.addEventListener('focus', function () {
        dropdown.classList.add('open');
        showBackdrop(function () { closeDropdown(); });
        search.value = '';
        filterItems('');
        setTimeout(function () { search.focus(); }, 50);
    });

    input.addEventListener('input', function () {
        if (this.value) {
            dropdown.classList.add('open');
            search.value = this.value;
            filterItems(this.value);
        } else {
            closeDropdown();
        }
    });

    search.addEventListener('input', function () { filterItems(this.value); });

    items.forEach(function (li) {
        li.addEventListener('mousedown', function (e) {
            e.preventDefault();
            selectItem(this);
        });
        li.addEventListener('touchstart', function (e) {
            e.preventDefault();
            selectItem(this);
        });
    });

    function closeDropdown() {
        dropdown.classList.remove('open');
        hideBackdrop();
    }

    input.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') { closeDropdown(); }
        if (e.key === 'Enter') {
          var visible = list.querySelector('li:not([style*="display: none"])');
          if (visible) { selectItem(visible); }
        }
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          var visible = list.querySelectorAll('li:not([style*="display: none"])');
          if (visible.length) { visible[0].focus(); }
        }
      });
    });
  }

  function buildPhonePicker(container, fieldName, currentValue) {
    var wrapper = document.createElement('div');
    wrapper.className = 'uw-phone-wrapper';

    var toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'uw-phone-toggle';
    toggle.setAttribute('aria-haspopup', 'listbox');
    toggle.setAttribute('aria-expanded', 'false');

    var hidden = document.createElement('input');
    hidden.type = 'hidden';
    hidden.name = fieldName + '_country_code';
    hidden.value = '+1';

    var dd = document.createElement('div');
    dd.className = 'uw-phone-dropdown';

    var search = document.createElement('input');
    search.type = 'text';
    search.className = 'uw-phone-search';
    search.placeholder = 'Search countries\u2026';

    var list = document.createElement('ul');
    list.className = 'uw-phone-list';
    list.setAttribute('role', 'listbox');

    function renderList(filter) {
      list.innerHTML = '';
      var f = filter ? filter.toLowerCase() : '';
      var filtered = f
        ? countries.filter(function (c) { return c.name.toLowerCase().indexOf(f) > -1 || c.dial.indexOf(filter) > -1; })
        : countries;
      if (!filtered.length) {
        var li = document.createElement('li');
        li.className = 'uw-phone-no-result';
        li.textContent = 'No countries found';
        list.appendChild(li);
        return;
      }
      filtered.forEach(function (c) {
        var li = document.createElement('li');
        li.className = 'uw-phone-option';
        li.setAttribute('role', 'option');
        li.setAttribute('data-dial', c.dial);
        li.setAttribute('data-code', c.code);
        li.setAttribute('data-regex', c.regex);
        li.setAttribute('data-example', c.example);
        li.tabIndex = -1;
        li.innerHTML = '<span class="uw-phone-flag">' + flagEmoji(c.code) + '</span>'
          + '<span class="uw-phone-dial">' + c.dial + '</span>'
          + '<span class="uw-phone-name">' + c.name + '</span>';
        li.addEventListener('click', function () { selectCountry(c.dial, c.code, c.regex); });
        li.addEventListener('touchstart', function (e) {
          e.preventDefault();
          selectCountry(c.dial, c.code, c.regex);
        });
        list.appendChild(li);
      });
    }

    function selectCountry(dial, code, regex) {
      hidden.value = dial;
      toggle.innerHTML = '<span class="uw-phone-flag">' + flagEmoji(code) + '</span>'
        + '<span class="uw-phone-dial">' + dial + '</span>'
        + '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="6 9 12 15 18 9"/></svg>';
      dd.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
      search.value = '';
      renderList('');
      phoneInput.setAttribute('data-phone-regex', regex || '');
      var example = countries.find(function (c) { return c.code === code; });
      phoneInput.placeholder = example ? 'e.g. ' + example.example : 'Phone number';
      validateField(phoneInput);
    }

    function closeDropdown() {
      dd.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
    }

    toggle.addEventListener('click', function (e) {
      e.stopPropagation();
      var isOpen = dd.classList.contains('open');
      document.querySelectorAll('.uw-phone-dropdown.open').forEach(function (openDropdown) {
        openDropdown.classList.remove('open');
        var openToggle = openDropdown.closest('.uw-phone-wrapper').querySelector('.uw-phone-toggle');
        if (openToggle) openToggle.setAttribute('aria-expanded', 'false');
      });
      if (!isOpen) {
        dd.classList.add('open');
        toggle.setAttribute('aria-expanded', 'true');
        search.focus();
        search.select();
      }
    });

    dd.addEventListener('click', function (e) { e.stopPropagation(); });
    search.addEventListener('input', function () { renderList(this.value); });
    search.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === 'Escape') {
        closeDropdown();
      }
    });

    document.addEventListener('click', function (e) {
      if (!wrapper.contains(e.target)) closeDropdown();
    });

    dd.appendChild(search);
    dd.appendChild(list);
    wrapper.appendChild(toggle);
    wrapper.appendChild(hidden);
    wrapper.appendChild(dd);

    var phoneInput = document.createElement('input');
    phoneInput.type = 'tel';
    phoneInput.className = 'uw-input uw-phone-input';
    phoneInput.name = fieldName;
    phoneInput.value = currentValue || '';
    phoneInput.placeholder = 'Phone number';
    phoneInput.autocomplete = 'tel-national';
    wrapper.appendChild(phoneInput);

    container.innerHTML = '';
    container.appendChild(wrapper);

    renderList('');

    var defaultCountry = phoneCountryMap['US'];
    if (defaultCountry) {
      selectCountry(defaultCountry.dial, defaultCountry.code, defaultCountry.regex);
    }
    return phoneInput;
  }

  function initPhoneFields() {
    var containers = document.querySelectorAll('.uw-phone-field');
    containers.forEach(function (container) {
      var existingInput = container.querySelector('input[type="tel"]');
      if (!existingInput) return;
      var fieldName = existingInput.name;
      var currentValue = existingInput.value;
      var wrapper = document.createElement('div');
      wrapper.id = 'uw-phone-container-' + fieldName;
      container.appendChild(wrapper);
      existingInput.style.display = 'none';
      var phoneInput = buildPhonePicker(wrapper, fieldName, currentValue);
      attachFieldValidation(phoneInput);
    });
  }

  function getErrorEl(el) {
    var group = el.closest('.uw-form-group');
    return group ? group.querySelector('.uw-field-error') : null;
  }

  function setError(el, msg) {
    var group = el.closest('.uw-form-group');
    if (!group) return;
    el.classList.add('error');
    var err = group.querySelector('.uw-field-error');
    if (!err) {
      err = document.createElement('span');
      err.className = 'uw-field-error';
      err.style.animation = 'uwFadeIn 0.2s ease';
      group.appendChild(err);
    }
    err.textContent = msg;
  }

  function clearError(el) {
    var group = el.closest('.uw-form-group');
    if (!group) return;
    el.classList.remove('error');
    var err = group.querySelector('.uw-field-error');
    if (err) err.remove();
  }

  function validateField(el) {
    var group = el.closest('.uw-form-group');
    if (group && group.style.display === 'none') return true;
    var v = el.value.trim();
    if (el.getAttribute('type') === 'checkbox') {
      if (el.required && !el.checked) {
        setError(el, 'Please select this option to continue.');
        return false;
      }
      clearError(el);
      return true;
    }

    var required = el.hasAttribute('required')
      || el.closest('.uw-form-group')?.querySelector('.text-c05');
    if (required && !v.length) {
      setError(el, 'This field is required.');
      return false;
    }
    if (!v.length) {
      clearError(el);
      return true;
    }

    if (!el.checkValidity()) {
      var rangeMessage = el.getAttribute('data-live-msg') || 'Enter a value within the allowed range.';
      setError(el, rangeMessage);
      return false;
    }

    var regex = el.getAttribute('data-live-regex');
    if (regex) {
      try {
        var re = new RegExp(regex);
        if (!re.test(v)) {
          var specificMsg = getSpecificErrorMessage(v, regex, el);
          setError(el, specificMsg || el.getAttribute('data-live-msg') || 'Invalid format.');
          return false;
        }
      } catch (e) {
        console.warn('Invalid regex:', regex, e);
      }
    }

    var phoneRegex = el.getAttribute('data-phone-regex');
    if (phoneRegex) {
      var digits = v.replace(/[\s\-\+\(\)]/g, '');
      try {
        var pre = new RegExp(phoneRegex);
        if (!pre.test(digits)) {
          setError(el, el.getAttribute('data-live-msg') || 'Invalid phone number for selected country.');
          return false;
        }
      } catch (e) {
        console.warn('Invalid phone regex:', phoneRegex, e);
      }
    }

    if (el.getAttribute('type') === 'email' && v.indexOf('@') === -1) {
      setError(el, 'Enter a valid email address.');
      return false;
    }

    var match = el.getAttribute('data-match');
    if (match) {
      var target = document.querySelector('[name="' + match + '"]');
      if (target && v !== target.value) {
        setError(el, el.getAttribute('data-live-msg') || 'Values do not match.');
        return false;
      }
    }

    clearError(el);
    return true;
  }

  function getSpecificErrorMessage(value, regexPattern, el) {
    return null;
  }

  function extractMinLength(pattern) {
    var match = pattern.match(/\{(\d+)(?:,\d*)?\}$/);
    if (match) return parseInt(match[1], 10);
    return null;
  }

  function extractMaxLength(pattern) {
    var match = pattern.match(/\{\d+,(\d+)\}$/);
    if (match) return parseInt(match[1], 10);
    return null;
  }

  function attachFieldValidation(el) {
    el.addEventListener('blur', function () { validateField(el); });
    el.addEventListener('input', function () {
      if (getErrorEl(this)) validateField(this);
      var match = this.getAttribute('data-match');
      if (match) {
        var target = document.querySelector('[name="' + match + '"]');
        if (target && getErrorEl(target)) validateField(target);
        var source = document.querySelector('[data-match="' + this.name + '"]');
        if (source && getErrorEl(source)) validateField(source);
      }
    });
    if (el.tagName === 'SELECT') {
      el.addEventListener('change', function () {
        validateField(this);
      });
    }
  }

  function validateAll(form) {
    var valid = true;
    var fields = form.querySelectorAll('.uw-form-group .uw-input, .uw-form-group select.uw-input, .uw-form-group select.uw-select, .uw-form-group input[type="checkbox"]');
    fields.forEach(function (el) {
      if (!validateField(el)) valid = false;
    });
    form.querySelectorAll('.uw-radio-group input[type="radio"][required]').forEach(function (radio) {
      var group = radio.closest('.uw-form-group');
      if (!group || group.dataset.radioChecked || group.style.display === 'none') return;
      group.dataset.radioChecked = 'true';
      var selected = form.querySelector('input[name="' + radio.name + '"]:checked');
      if (!selected) {
        setError(radio, 'Choose one option.');
        valid = false;
      } else {
        clearError(radio);
      }
    });
    form.querySelectorAll('[data-radio-checked]').forEach(function (group) { delete group.dataset.radioChecked; });
    form.querySelectorAll('[data-field-compare]').forEach(function (el) {
      if (el.closest('.uw-form-group') && el.closest('.uw-form-group').style.display === 'none') return;
      var src = el.value.trim();
      var tgtName = el.getAttribute('data-field-compare');
      var tgt = form.querySelector('[name="' + tgtName + '"]');
      if (!src || !tgt || !tgt.value) return;
      var op = el.getAttribute('data-field-compare-op') || 'lte';
      var sNum = parseFloat(src);
      var tNum = parseFloat(tgt.value);
      if (isNaN(sNum) || isNaN(tNum)) return;
      var ok = false;
      if (op === 'lte') ok = sNum <= tNum;
      else if (op === 'lt') ok = sNum < tNum;
      else if (op === 'gte') ok = sNum >= tNum;
      else if (op === 'gt') ok = sNum > tNum;
      else if (op === 'eq') ok = sNum === tNum;
      if (!ok) {
        var labels = { lte: 'cannot be later than', lt: 'must be before', gte: 'must be at least', gt: 'must be after', eq: 'must equal' };
        var targetLabel = tgtName.replace(/_/g, ' ').replace(/\b\w/g, function(c) { return c.toUpperCase(); });
        setError(el, (labels[op] || 'is invalid compared to') + ' ' + targetLabel);
        valid = false;
      }
    });
    return valid;
  }

  var backdrop = null;

  function showBackdrop(onClick) {
    if (!backdrop) {
      backdrop = document.createElement('div');
      backdrop.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;z-index:999;background:transparent;';
      document.body.appendChild(backdrop);
      backdrop.addEventListener('click', onClick);
      backdrop.addEventListener('touchstart', function (e) { e.preventDefault(); onClick(); });
    }
  }

  function hideBackdrop() {
    if (backdrop) { backdrop.remove(); backdrop = null; }
  }

  function initDynamicAutosave() {
    var form = document.querySelector('form[data-dynamic-autosave]');
    if (!form || !window.fetch) return;

    var url = form.getAttribute('data-autosave-url');
    var appId = form.getAttribute('data-app-id');
    var section = form.getAttribute('data-section-code');
    var csrf = form.querySelector('[name="csrfmiddlewaretoken"]');
    var status = form.querySelector('.uw-autosave-status');
    var timers = new Map();
    var requests = [];

    function setStatus(message, className) {
      if (!status) return;
      status.textContent = message;
      status.className = 'uw-autosave-status' + (className ? ' ' + className : '');
    }

    function fieldValue(el) {
      if (el.type === 'checkbox') return el.checked ? 'on' : '';
      if (el.type === 'radio') {
        var selected = form.querySelector('input[name="' + CSS.escape(el.name) + '"]:checked');
        return selected ? selected.value : '';
      }
      if (el.multiple) return Array.prototype.map.call(el.selectedOptions, function (option) { return option.value; });
      return el.value;
    }

    function saveField(el) {
      if (!el.name || el.type === 'file') return Promise.resolve();
      if (el.type === 'hidden' && !el.closest('.uw-date-selects')) return Promise.resolve();
      if (el.type === 'radio' && !el.checked) return Promise.resolve();
      timers.delete(el);

      var value = fieldValue(el);
      var empty = value === '' || (Array.isArray(value) && !value.length);
      if (!empty && !validateField(el)) return Promise.resolve();

      var data = new URLSearchParams();
      data.append('app_id', appId);
      data.append('section', section);
      data.append('field', el.name);
      if (Array.isArray(value)) value.forEach(function (item) { data.append('value', item); });
      else data.append('value', value);
      form.querySelectorAll('[name]').forEach(function(f) {
        if (f.name && f.name !== el.name && f.type !== 'file') {
          data.append('ctx_' + f.name, fieldValue(f));
        }
      });

      setStatus('Savingâ€¦', '');
      var request = fetch(url, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
          'X-CSRFToken': csrf ? csrf.value : ''
        },
        body: data.toString()
      }).then(function (response) {
        if (!response.ok) throw new Error('Autosave failed');
        return response.json();
      }).then(function () {
        setStatus('Saved', 'is-saved');
      }).catch(function () {
        setStatus('Not saved', 'is-error');
      });
      requests.push(request);
      request.finally(function () {
        var index = requests.indexOf(request);
        if (index > -1) requests.splice(index, 1);
      });
      return request;
    }

    function queueSave(el, immediately) {
      if (!el || !el.name || el.type === 'file') return;
      if (el.type === 'hidden' && !el.closest('.uw-date-selects')) return;
      if (timers.has(el)) clearTimeout(timers.get(el));
      if (immediately) return saveField(el);
      setStatus('Savingâ€¦', '');
      timers.set(el, setTimeout(function () { saveField(el); }, 650));
    }

    form.addEventListener('input', function (event) {
      var el = event.target;
      if (el.matches('input, textarea')) queueSave(el, false);
    });
    form.addEventListener('change', function (event) {
      var el = event.target;
      if (el.matches('select, input[type="checkbox"], input[type="radio"]')) queueSave(el, true);
      if (el.type === 'hidden' && el.closest('.uw-date-selects')) queueSave(el, true);
    });

    function flush() {
      var pending = Array.from(timers.keys());
      pending.forEach(function (el) {
        clearTimeout(timers.get(el));
        saveField(el);
      });
      return Promise.all(requests.slice());
    }

    form.querySelectorAll('a.uw-btn-outline').forEach(function (link) {
      link.addEventListener('click', function (event) {
        if (!timers.size && !requests.length) return;
        event.preventDefault();
        var destination = link.href;
        flush().finally(function () { window.location.assign(destination); });
      });
    });
    form.addEventListener('submit', function () { flush(); });
  }

  function initConditionalFieldRequirements() {
    document.querySelectorAll('[data-conditional-trigger]').forEach(function (el) {
      function getTriggerInp() {
        if (el.tagName === 'INPUT' || el.tagName === 'SELECT' || el.tagName === 'TEXTAREA') return el;
        var nonHidden = el.querySelector('input:not([type="hidden"]), select, textarea');
        if (nonHidden) return nonHidden;
        return el.querySelector('input, select, textarea');
      }
      function resolveMatch() {
        var inp = getTriggerInp();
        var expectedVal = el.getAttribute('data-conditional-value') || 'yes';
        if (!inp) return false;
        if (inp.type === 'radio') {
          var checked = el.closest('form')?.querySelector('input[name="' + inp.name + '"]:checked');
          return !!checked && checked.value.toLowerCase() === expectedVal.toLowerCase();
        }
        if (inp.type === 'checkbox') {
          return inp.checked && inp.value.toLowerCase() === expectedVal.toLowerCase();
        }
        return inp.value.toLowerCase() === expectedVal.toLowerCase();
      }
      function _norm(v) {
        var s = String(v).toLowerCase();
        if (['true', 'on', 'yes', '1', 'y', 't'].indexOf(s) !== -1) return 'yes';
        if (['false', 'off', 'no', '0', '', 'n', 'f'].indexOf(s) !== -1) return 'no';
        return s;
      }
      function getCurrentVal(fieldCode) {
        var form = el.closest('form') || document;
        var targetInp = form.querySelector('[name="' + fieldCode + '"]:not([type="hidden"])');
        if (!targetInp) targetInp = form.querySelector('[name="' + fieldCode + '"]');
        if (!targetInp) return '';
        if (targetInp.type === 'radio') {
          var checked = form.querySelector('input[name="' + fieldCode + '"]:checked');
          return checked ? checked.value : '';
        }
        if (targetInp.type === 'checkbox') return targetInp.checked ? 'yes' : '';
        return targetInp.value;
      }
      function updateConditional() {
        var targetSel = el.getAttribute('data-conditional-target');
        var targets = document.querySelectorAll(targetSel || '[data-conditional]');
        targets.forEach(function (t) {
          var group = t.closest('.uw-form-group') || t;
          var input = group.querySelector('input.uw-input, select.uw-input, select.uw-select, textarea.uw-input, input[type="checkbox"], input[type="radio"]') || group.querySelector('.uw-input') || t;
          var show = false;
          var rulesAttr = t.getAttribute('data-conditional-rules');
          if (rulesAttr) {
            try {
              var rules = JSON.parse(rulesAttr);
              var andRules = rules.filter(function(r) { return (r.l || 'AND') === 'AND'; });
              var orRules = rules.filter(function(r) { return r.l === 'OR'; });
              function matchRule(rule) {
                var cv = _norm(getCurrentVal(rule.f));
                var rv = _norm(rule.v);
                var isEmpty = cv === '';
                if (rule.op === 'neq') return isEmpty || cv !== rv;
                if (rule.op === 'not_empty') return !isEmpty;
                if (rule.op === 'is_empty') return isEmpty;
                if (rule.op === 'contains') return cv.indexOf(rv) !== -1;
                if (rule.op === 'gt') { var a = parseFloat(cv), b = parseFloat(rv); return !isNaN(a) && !isNaN(b) && a > b; }
                if (rule.op === 'gte') { var a = parseFloat(cv), b = parseFloat(rv); return !isNaN(a) && !isNaN(b) && a >= b; }
                if (rule.op === 'lt') { var a = parseFloat(cv), b = parseFloat(rv); return !isNaN(a) && !isNaN(b) && a < b; }
                if (rule.op === 'lte') { var a = parseFloat(cv), b = parseFloat(rv); return !isNaN(a) && !isNaN(b) && a <= b; }
                if (rule.op === 'in') return rv.split(',').map(function(x) { return x.trim(); }).indexOf(cv) !== -1;
                if (rule.op === 'not_in') return rv.split(',').map(function(x) { return x.trim(); }).indexOf(cv) === -1;
                if (rule.op === 'checked') return cv === 'yes';
                if (rule.op === 'not_checked') return cv === 'no';
                return isEmpty || cv === rv;
              }
              var andOk = andRules.length === 0 || andRules.every(matchRule);
              var orOk = orRules.length === 0 || orRules.some(matchRule);
              show = andOk && orOk;
            } catch(e) {}
          }
          if (!show) {
            var simpleVal = t.getAttribute('data-conditional');
            if (simpleVal && simpleVal.length) {
              var cv = getCurrentVal(simpleVal).toLowerCase();
              var expected = (t.getAttribute('data-conditional-value') || 'yes').toLowerCase();
              show = !cv || cv === expected;
            }
          }
          if (input.getAttribute('data-orig-required') === null) {
            input.setAttribute('data-orig-required', input.required ? 'true' : 'false');
          }
          if (show) {
            input.required = input.getAttribute('data-orig-required') === 'true';
            if (group) group.style.display = '';
            if (group) {
              var existingStar = group.querySelector('label .req-star');
              if (existingStar) existingStar.remove();
            }
            if (input.required && group?.querySelector('label') && !group.querySelector('.req-star')) {
              var star = document.createElement('span');
              star.className = 'text-c05 req-star';
              star.textContent = '*';
              group.querySelector('label').appendChild(star);
            }
          } else {
            input.required = false;
            if (group) group.style.display = 'none';
            clearError(input);
            var star = group?.querySelector('.req-star');
            if (star) star.remove();
          }
        });
      }
      var inp = getTriggerInp();
      if (inp) {
        if (inp.type === 'radio') {
          var form = el.closest('form');
          if (form) {
            form.querySelectorAll('input[name="' + inp.name + '"]').forEach(function (r) {
              r.addEventListener('change', updateConditional);
            });
          }
        } else {
          inp.addEventListener('change', updateConditional);
          inp.addEventListener('input', updateConditional);
        }
      }
      setTimeout(updateConditional, 100);
    });
  }




  function initParentRelationshipLabels() {
    var sel = document.querySelector('select[name="parent_relationship"]');
    if (!sel) return;
    var relMap = {
      father: { title: 'Father', lower: 'father' },
      mother: { title: 'Mother', lower: 'mother' },
      legal_guardian: { title: 'Legal Guardian', lower: 'legal guardian' },
      other: { title: 'Parent/Guardian', lower: 'parent/guardian' },
    };
    var parentFields = ['parent_us_citizen', 'parent_residence_12mo',
      'parent_employment', 'parent_tax_return', 'parent_vote_registration', 'parent_drivers_license'];
    function updateLabels() {
      var opt = sel.options[sel.selectedIndex];
      var rel = opt && relMap[opt.value] || { title: 'Parent/Guardian', lower: 'parent/guardian' };
      var heading = document.querySelector('[data-field="_parent_chosen_heading"] .section-heading');
      if (heading) heading.textContent = rel.title;
      parentFields.forEach(function (fc) {
        var group = document.querySelector('[data-field="' + fc + '"]');
        if (!group) return;
        var label = group.querySelector('label[for="id_' + fc + '"], .section-heading');
        if (!label) return;
        var base = label.getAttribute('data-rel-base');
        if (!base) {
          base = label.textContent;
          label.setAttribute('data-rel-base', base);
        }
        label.textContent = base.replace(/\{rel_title\}/g, rel.title).replace(/\{rel_lower\}/g, rel.lower);
      });
    }
    sel.addEventListener('change', updateLabels);
    setTimeout(updateLabels, 150);
  }

  function initMaxValueValidation() {
    document.querySelectorAll('input[type="number"][max]').forEach(function (el) {
      el.addEventListener('input', function () {
        var max = parseFloat(this.getAttribute('max'));
        if (!isNaN(max) && this.value) {
          var val = parseFloat(this.value);
          if (val > max) {
            this.value = max;
          }
        }
      });
      el.addEventListener('blur', function () {
        var max = parseFloat(this.getAttribute('max'));
        if (!isNaN(max) && this.value) {
          var val = parseFloat(this.value);
          if (val > max) {
            setError(this, 'Maximum value is ' + max + '.');
          } else {
            clearError(this);
          }
        }
      });
    });
  }

  function initAddRepeat() {
    document.querySelectorAll('.add-repeat').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var section = btn.closest('.dynamic-section');
        if (!section) return;
        var grid = section.querySelector('.dynamic-form-grid');
        if (!grid) return;
        if (grid.style.display === 'none') {
          grid.style.display = '';
          btn.style.display = 'none';
        }
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initSearchableDropdowns();
    initPhoneFields();
    initDynamicAutosave();
    initConditionalFieldRequirements();
    initParentRelationshipLabels();
    initMaxValueValidation();
    initAddRepeat();

    var fields = document.querySelectorAll('.uw-form-group .uw-input, .uw-form-group select.uw-input, .uw-form-group select.uw-select');
    fields.forEach(attachFieldValidation);

    document.querySelectorAll('.uw-radio-group input[type="radio"]').forEach(function (radio) {
      radio.addEventListener('change', function () {
        var group = radio.closest('.uw-form-group');
        if (group) clearError(radio);
      });
    });
    document.querySelectorAll('.uw-checkbox-label input[type="checkbox"]').forEach(attachFieldValidation);

    var form = document.querySelector('.uw-dash-card-body form');
    if (!form) form = document.querySelector('form');
    if (form) {
      form.addEventListener('submit', function (e) {
        var valid = true;
        try {
          valid = validateAll(form);
        } catch (ex) {
          valid = false;
        }
        if (!valid) {
          e.preventDefault();
          var btn = form.querySelector('button[type="submit"]');
          if (btn) {
            btn.disabled = false;
            var orig = btn.getAttribute('data-uw-original-text');
            if (orig) btn.innerHTML = orig;
          }
          var firstErr = form.querySelector('.uw-input.error');
          if (firstErr) {
            firstErr.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstErr.focus();
          }
        }
      });
    }

    initCascadingDropdowns();
  });

  function _destroyChoices(el) {
    var wrapper = el.closest('.choices');
    if (wrapper) {
      wrapper.parentNode.insertBefore(el, wrapper);
      wrapper.remove();
    }
    el.style.display = '';
    el.classList.remove('choices__input');
  }

  function _initChoices(el) {
    if (typeof Choices === 'undefined') return;
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
  }

  function loadStates(countrySel, keepValue) {
    var fieldCode = countrySel.getAttribute('data-field');
    var prefix = fieldCode.replace(/_country$/, '');
    var section = countrySel.closest('.dynamic-section') || countrySel.closest('.uw-dash-card') || countrySel.closest('form');
    if (!section) return;
    var stateSel = section.querySelector('[data-field="' + prefix + '_state"]');
    var citySel = section.querySelector('[data-field="' + prefix + '_city"]');
    var countryCode = countrySel.value;

    if (stateSel) {
      var prevState = stateSel.value;
      _destroyChoices(stateSel);
      stateSel.disabled = true;
      stateSel.innerHTML = '<option value="">Select State/Province</option>';
      if (citySel) {
        _destroyChoices(citySel);
        citySel.disabled = true;
        citySel.innerHTML = '<option value="">Select City</option>';
      }
      if (countryCode) {
        fetch('/applicants/api/states/?country=' + encodeURIComponent(countryCode))
          .then(function(r) { return r.json(); })
          .then(function(states) {
            states.forEach(function(s) {
              stateSel.innerHTML += '<option value="' + s.id + '">' + s.name + '</option>';
            });
            stateSel.disabled = false;
            if (keepValue && prevState) {
              stateSel.value = prevState;
            }
            _initChoices(stateSel);
            if (stateSel.value) {
              loadCities(stateSel, keepValue);
            }
          })
          .catch(function() {
            stateSel.disabled = false;
            _initChoices(stateSel);
          });
      } else {
        stateSel.disabled = false;
        _initChoices(stateSel);
      }
    }
  }

  function loadCities(stateSel, keepValue) {
    var fieldCode = stateSel.getAttribute('data-field');
    var prefix = fieldCode.replace(/_state$/, '');
    var section = stateSel.closest('.dynamic-section') || stateSel.closest('.uw-dash-card') || stateSel.closest('form');
    if (!section) return;
    var citySel = section.querySelector('[data-field="' + prefix + '_city"]');
    var stateId = stateSel.value;

    if (citySel) {
      var prevCity = citySel.value;
      _destroyChoices(citySel);
      citySel.disabled = true;
      citySel.innerHTML = '<option value="">Select City</option>';
      if (stateId) {
        fetch('/applicants/api/cities/?state=' + encodeURIComponent(stateId))
          .then(function(r) { return r.json(); })
          .then(function(cities) {
            cities.forEach(function(c) {
              citySel.innerHTML += '<option value="' + c.name + '">' + c.name + '</option>';
            });
            citySel.disabled = false;
            if (keepValue && prevCity) {
              citySel.value = prevCity;
            }
            _initChoices(citySel);
          })
          .catch(function() {
            citySel.disabled = false;
            _initChoices(citySel);
          });
      } else {
        citySel.disabled = false;
        _initChoices(citySel);
      }
    }
  }

  function initCascadingDropdowns() {
    document.querySelectorAll('[data-country-select="true"]').forEach(function(countrySel) {
      countrySel.addEventListener('change', function() {
        loadStates(this, false);
      });
    });

    document.querySelectorAll('[data-state-select="true"]').forEach(function(stateSel) {
      stateSel.addEventListener('change', function() {
        loadCities(this, false);
      });
    });

    document.querySelectorAll('[data-country-select="true"]').forEach(function(countrySel) {
      if (countrySel.value) {
        loadStates(countrySel, true);
      }
    });

    document.querySelectorAll('[data-state-select="true"]').forEach(function(stateSel) {
      if (stateSel.value && !stateSel.options.length) {
        loadCities(stateSel, true);
      }
    });

  }

})();
