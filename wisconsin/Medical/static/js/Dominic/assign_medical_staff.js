function medPositionPanel(trigger, panel) {
    if (!window.matchMedia('(max-width: 480px)').matches) {
        panel.style.position = '';
        panel.style.top = '';
        panel.style.bottom = '';
        panel.style.left = '';
        panel.style.right = '';
        panel.style.maxHeight = '';
        return;
    }

    var margin = 8;
    var minHeight = 160;
    var maxHeight = 340;
    var rect = trigger.getBoundingClientRect();
    var viewportH = window.innerHeight;
    var spaceBelow = viewportH - rect.bottom - margin;
    var spaceAbove = rect.top - margin;

    panel.style.position = 'fixed';
    panel.style.left = '12px';
    panel.style.right = '12px';

    if (spaceBelow >= minHeight || spaceBelow >= spaceAbove) {
        panel.style.top = (rect.bottom + margin) + 'px';
        panel.style.bottom = 'auto';
        panel.style.maxHeight = Math.max(minHeight, Math.min(maxHeight, spaceBelow)) + 'px';
    } else {
        panel.style.bottom = (viewportH - rect.top + margin) + 'px';
        panel.style.top = 'auto';
        panel.style.maxHeight = Math.max(minHeight, Math.min(maxHeight, spaceAbove)) + 'px';
    }
}

window.addEventListener('resize', function () {
    document.querySelectorAll('.med-custom-select--open').forEach(function (w) {
        var trig = w.querySelector('.med-custom-select__trigger');
        var pnl = w.querySelector('.med-custom-select__panel');
        if (trig && pnl && !pnl.hidden) medPositionPanel(trig, pnl);
    });
});

window.addEventListener('scroll', function () {
    if (!window.matchMedia('(max-width: 480px)').matches) return;
    document.querySelectorAll('.med-custom-select--open').forEach(function (w) {
        var pnl = w.querySelector('.med-custom-select__panel');
        if (pnl) pnl.hidden = true;
        w.classList.remove('med-custom-select--open');
    });
}, { passive: true });

(function () {
    var wrapper = document.getElementById('staffCustomSelect');
    if (!wrapper) return;

    var trigger   = document.getElementById('staffSelectTrigger');
    var panel     = document.getElementById('staffSelectPanel');
    var search    = document.getElementById('staffSelectSearch');
    var list      = document.getElementById('staffSelectList');
    var label     = document.getElementById('staffSelectLabel');
    var avatarBox = document.getElementById('staffSelectAvatar');
    var nativeSel = document.getElementById('id_user');
    var autofillCard = document.getElementById('autofillCard');
    var errUser = document.getElementById('err_user');

    var dirEl = document.getElementById('staffDirectoryData');
    var directory = {};
    try { directory = dirEl ? JSON.parse(dirEl.textContent) : {}; } catch (e) { directory = {}; }

    function openPanel() {
        panel.hidden = false;
        wrapper.classList.add('med-custom-select--open');
        medPositionPanel(trigger, panel);
        search.value = '';
        filterList('');
        search.focus();
    }

    function closePanel() {
        panel.hidden = true;
        wrapper.classList.remove('med-custom-select--open');
    }

    function filterList(term) {
        list.querySelectorAll('.med-custom-select__item').forEach(function (item) {
            var haystack = item.getAttribute('data-search') || '';
            item.style.display = haystack.indexOf(term) !== -1 ? '' : 'none';
        });
    }

    function setDisplay(item) {
        var nameEl = item.querySelector('strong');
        var imgEl = item.querySelector('img');
        label.textContent = nameEl ? nameEl.textContent : 'Select Staff User';
        label.classList.add('med-custom-select__label--filled');
        avatarBox.innerHTML = imgEl ? '<img src="' + imgEl.getAttribute('src') + '" alt="">' : '<i data-lucide="user"></i>';
        if (window.lucide) lucide.createIcons();
    }

    function setPreviewPerson(item) {
        var nameEl = item.querySelector('strong');
        var smallEl = item.querySelector('small');
        var imgEl = item.querySelector('img');
        document.getElementById('previewName').textContent = nameEl ? nameEl.textContent : 'No staff selected';
        document.getElementById('previewUsername').textContent = smallEl ? smallEl.textContent : '';
        var previewAvatar = document.getElementById('previewAvatar');
        previewAvatar.innerHTML = imgEl ? '<img src="' + imgEl.getAttribute('src') + '" alt="">' : '<i data-lucide="user"></i>';
        if (window.lucide) lucide.createIcons();
    }

    function autofillFromDirectory(userId) {
        var info = directory[userId];
        if (!info) return;
        setFieldValue('id_preferred_name', info.full_name);
        setFieldValue('id_personal_email', info.email);
        setFieldValue('id_phone', info.phone);
        setFieldValue('id_employee_id', info.employee_id);
        setFieldValue('id_work_email', info.work_email);
        setFieldValue('id_emergency_contact_name', info.emergency_contact_name);
        setFieldValue('id_emergency_contact_phone', info.emergency_contact_phone);
        autofillCard.hidden = false;
        if (window.assignUpdatePreview) window.assignUpdatePreview();
    }

    function setFieldValue(fieldId, value) {
        var el = document.getElementById(fieldId);
        if (el) el.value = value || '';
    }

    trigger.addEventListener('click', function (e) {
        e.stopPropagation();
        if (panel.hidden) openPanel(); else closePanel();
    });

    document.addEventListener('click', function (e) {
        if (!wrapper.contains(e.target)) closePanel();
    });

    search.addEventListener('input', function () {
        filterList(search.value.trim().toLowerCase());
    });

    list.addEventListener('click', function (e) {
        var item = e.target.closest('.med-custom-select__item');
        if (!item || !item.getAttribute('data-value')) return;

        var value = item.getAttribute('data-value');
        if (nativeSel) {
            nativeSel.value = value;
            nativeSel.dispatchEvent(new Event('change'));
        }
        setDisplay(item);
        setPreviewPerson(item);
        autofillFromDirectory(value);
        if (errUser) errUser.hidden = true;
        wrapper.classList.remove('is-invalid');
        closePanel();
    });

    if (nativeSel && nativeSel.value) {
        var existing = list.querySelector('[data-value="' + nativeSel.value + '"]');
        if (existing) { setDisplay(existing); setPreviewPerson(existing); autofillFromDirectory(nativeSel.value); }
    }
})();

(function () {
    var wrapper = document.getElementById('roleCustomSelect');
    if (!wrapper) return;

    var trigger = document.getElementById('roleSelectTrigger');
    var panel   = document.getElementById('roleSelectPanel');
    var list    = document.getElementById('roleSelectList');
    var label   = document.getElementById('roleSelectLabel');
    var iconBox = document.getElementById('roleSelectIcon');
    var nativeSel = document.getElementById('id_role');
    var pillsWrap = document.getElementById('roleCategoryPills');
    var errRole = document.getElementById('err_role');

    var ICONS = {
        DOCTOR: 'stethoscope', NURSE: 'heart-handshake', PHYSIO: 'activity',
        LAB: 'flask-conical', PHARMACY: 'pill', FRONT_DESK: 'user-round', OTHER: 'shapes'
    };

    list.querySelectorAll('.med-custom-select__item[data-category]').forEach(function (item) {
        var icon = item.querySelector('[data-lucide]');
        var cat = item.getAttribute('data-category');
        if (icon && ICONS[cat]) icon.setAttribute('data-lucide', ICONS[cat]);
    });
    if (window.lucide) lucide.createIcons();

    function openPanel() {
        panel.hidden = false;
        wrapper.classList.add('med-custom-select--open');
        medPositionPanel(trigger, panel);
    }

    function closePanel() {
        panel.hidden = true;
        wrapper.classList.remove('med-custom-select--open');
    }

    function setDisplay(item) {
        var nameEl = item.querySelector('strong');
        var cat = (item.getAttribute('data-category') || 'OTHER');
        label.textContent = nameEl ? nameEl.textContent : 'Select Role';
        label.classList.add('med-custom-select__label--filled');
        iconBox.className = 'med-custom-select__avatar med-role-icon med-role-icon--' + cat.toLowerCase();
        iconBox.innerHTML = '<i data-lucide="' + (ICONS[cat] || 'tag') + '"></i>';
        if (window.lucide) lucide.createIcons();
    }

    trigger.addEventListener('click', function (e) {
        e.stopPropagation();
        if (panel.hidden) openPanel(); else closePanel();
    });

    document.addEventListener('click', function (e) {
        if (!wrapper.contains(e.target)) closePanel();
    });

    list.addEventListener('click', function (e) {
        var item = e.target.closest('.med-custom-select__item');
        if (!item || !item.getAttribute('data-value')) return;

        var value = item.getAttribute('data-value');
        if (nativeSel) {
            nativeSel.value = value;
            nativeSel.dispatchEvent(new Event('change'));
        }
        setDisplay(item);
        if (errRole) errRole.hidden = true;
        wrapper.classList.remove('is-invalid');
        closePanel();
        if (window.assignUpdatePreview) window.assignUpdatePreview();
    });

    if (pillsWrap) {
        pillsWrap.addEventListener('click', function (e) {
            var pill = e.target.closest('.role-pill');
            if (!pill) return;
            pillsWrap.querySelectorAll('.role-pill').forEach(function (p) { p.classList.remove('is-active'); });
            pill.classList.add('is-active');
            var cat = pill.getAttribute('data-category');
            list.querySelectorAll('.med-custom-select__item[data-category]').forEach(function (item) {
                var show = cat === 'ALL' || item.getAttribute('data-category') === cat;
                item.style.display = show ? '' : 'none';
            });
            openPanel();
        });
    }

    if (nativeSel && nativeSel.value) {
        var existing = list.querySelector('[data-value="' + nativeSel.value + '"]');
        if (existing) setDisplay(existing);
    }
})();

(function () {
    var wrapper = document.getElementById('hospitalCustomSelect');
    if (!wrapper) return;

    var trigger = document.getElementById('hospitalSelectTrigger');
    var panel   = document.getElementById('hospitalSelectPanel');
    var search  = document.getElementById('hospitalSelectSearch');
    var list    = document.getElementById('hospitalSelectList');
    var label   = document.getElementById('hospitalSelectLabel');
    var nativeSel = document.getElementById('id_hospital');
    var errHospital = document.getElementById('err_hospital');

    if (!nativeSel) return;

    function buildList() {
        list.innerHTML = '';
        Array.prototype.forEach.call(nativeSel.options, function (opt) {
            if (!opt.value) return;
            var li = document.createElement('li');
            li.className = 'med-custom-select__item';
            li.setAttribute('data-value', opt.value);
            li.setAttribute('data-search', opt.text.toLowerCase());
            li.innerHTML =
                '<span class="med-custom-select__item-avatar med-role-icon med-role-icon--other"><i data-lucide="hospital"></i></span>' +
                '<span class="med-custom-select__item-info"><strong>' + opt.text + '</strong></span>';
            list.appendChild(li);
        });
        if (window.lucide) lucide.createIcons();
    }

    function filterList(term) {
        list.querySelectorAll('.med-custom-select__item').forEach(function (item) {
            var haystack = item.getAttribute('data-search') || '';
            item.style.display = haystack.indexOf(term) !== -1 ? '' : 'none';
        });
    }

    function openPanel() {
        panel.hidden = false;
        wrapper.classList.add('med-custom-select--open');
        medPositionPanel(trigger, panel);
        search.value = '';
        filterList('');
        search.focus();
    }
    function closePanel() {
        panel.hidden = true;
        wrapper.classList.remove('med-custom-select--open');
    }
    function setDisplay(item) {
        var nameEl = item.querySelector('strong');
        label.textContent = nameEl ? nameEl.textContent : 'Select Hospital';
        label.classList.add('med-custom-select__label--filled');
    }

    trigger.addEventListener('click', function (e) {
        e.stopPropagation();
        if (panel.hidden) openPanel(); else closePanel();
    });
    document.addEventListener('click', function (e) {
        if (!wrapper.contains(e.target)) closePanel();
    });
    search.addEventListener('input', function () {
        filterList(search.value.trim().toLowerCase());
    });
    list.addEventListener('click', function (e) {
        var item = e.target.closest('.med-custom-select__item');
        if (!item) return;
        nativeSel.value = item.getAttribute('data-value');
        nativeSel.dispatchEvent(new Event('change'));
        setDisplay(item);
        if (errHospital) errHospital.hidden = true;
        wrapper.classList.remove('is-invalid');
        closePanel();
        if (window.assignUpdatePreview) window.assignUpdatePreview();
    });

    buildList();
    if (nativeSel.value) {
        var existing = list.querySelector('[data-value="' + nativeSel.value + '"]');
        if (existing) setDisplay(existing);
    }
})();

(function () {
    var wrapper = document.getElementById('departmentCustomSelect');
    if (!wrapper) return;

    var trigger = document.getElementById('departmentSelectTrigger');
    var panel   = document.getElementById('departmentSelectPanel');
    var search  = document.getElementById('departmentSelectSearch');
    var list    = document.getElementById('departmentSelectList');
    var label   = document.getElementById('departmentSelectLabel');
    var nativeSel = document.getElementById('id_department');
    var errDept = document.getElementById('err_department');

    if (!nativeSel) return;

    function buildList() {
        list.innerHTML = '';
        Array.prototype.forEach.call(nativeSel.options, function (opt) {
            if (!opt.value) return;
            var li = document.createElement('li');
            li.className = 'med-custom-select__item';
            li.setAttribute('data-value', opt.value);
            li.setAttribute('data-search', opt.text.toLowerCase());
            li.innerHTML =
                '<span class="med-custom-select__item-avatar med-role-icon med-role-icon--other"><i data-lucide="building-2"></i></span>' +
                '<span class="med-custom-select__item-info"><strong>' + opt.text + '</strong></span>';
            list.appendChild(li);
        });
        if (window.lucide) lucide.createIcons();
    }

    function filterList(term) {
        list.querySelectorAll('.med-custom-select__item').forEach(function (item) {
            var haystack = item.getAttribute('data-search') || '';
            item.style.display = haystack.indexOf(term) !== -1 ? '' : 'none';
        });
    }

    function openPanel() {
        panel.hidden = false;
        wrapper.classList.add('med-custom-select--open');
        medPositionPanel(trigger, panel);
        search.value = '';
        filterList('');
        search.focus();
    }

    function closePanel() {
        panel.hidden = true;
        wrapper.classList.remove('med-custom-select--open');
    }

    function setDisplay(item) {
        var nameEl = item.querySelector('strong');
        label.textContent = nameEl ? nameEl.textContent : 'Select Department';
        label.classList.add('med-custom-select__label--filled');
    }

    trigger.addEventListener('click', function (e) {
        e.stopPropagation();
        if (wrapper.classList.contains('med-custom-select--locked')) return;
        if (panel.hidden) openPanel(); else closePanel();
    });

    document.addEventListener('click', function (e) {
        if (!wrapper.contains(e.target)) closePanel();
    });

    search.addEventListener('input', function () {
        filterList(search.value.trim().toLowerCase());
    });

    list.addEventListener('click', function (e) {
        var item = e.target.closest('.med-custom-select__item');
        if (!item) return;
        nativeSel.value = item.getAttribute('data-value');
        nativeSel.dispatchEvent(new Event('change'));
        setDisplay(item);
        if (errDept) errDept.hidden = true;
        wrapper.classList.remove('is-invalid');
        closePanel();
        if (window.assignUpdatePreview) window.assignUpdatePreview();
    });

    buildList();
    if (nativeSel.value) {
        var existing = list.querySelector('[data-value="' + nativeSel.value + '"]');
        if (existing) setDisplay(existing);
    }

    window.medDepartmentSelect = {
        wrapper: wrapper,
        label: label,
        list: list
    };
})();

(function () {
    var wrapper = document.getElementById('employmentTypeCustomSelect');
    if (!wrapper) return;

    var trigger = document.getElementById('employmentTypeSelectTrigger');
    var panel   = document.getElementById('employmentTypeSelectPanel');
    var list    = document.getElementById('employmentTypeSelectList');
    var label   = document.getElementById('employmentTypeSelectLabel');
    var nativeSel = document.getElementById('id_employment_type');
    var errType = document.getElementById('err_employment_type');

    if (!nativeSel) return;

    function buildList() {
        list.innerHTML = '';
        Array.prototype.forEach.call(nativeSel.options, function (opt) {
            if (!opt.value) return;
            var li = document.createElement('li');
            li.className = 'med-custom-select__item';
            li.setAttribute('data-value', opt.value);
            li.innerHTML =
                '<span class="med-custom-select__item-avatar med-role-icon med-role-icon--other"><i data-lucide="briefcase"></i></span>' +
                '<span class="med-custom-select__item-info"><strong>' + opt.text + '</strong></span>';
            list.appendChild(li);
        });
        if (window.lucide) lucide.createIcons();
    }

    function openPanel() {
        panel.hidden = false;
        wrapper.classList.add('med-custom-select--open');
        medPositionPanel(trigger, panel);
    }

    function closePanel() {
        panel.hidden = true;
        wrapper.classList.remove('med-custom-select--open');
    }

    function setDisplay(item) {
        var nameEl = item.querySelector('strong');
        label.textContent = nameEl ? nameEl.textContent : 'Select Employment Type';
        label.classList.add('med-custom-select__label--filled');
    }

    trigger.addEventListener('click', function (e) {
        e.stopPropagation();
        if (panel.hidden) openPanel(); else closePanel();
    });

    document.addEventListener('click', function (e) {
        if (!wrapper.contains(e.target)) closePanel();
    });
    
    list.addEventListener('click', function (e) {
        var item = e.target.closest('.med-custom-select__item');
        if (!item) return;
        nativeSel.value = item.getAttribute('data-value');
        nativeSel.dispatchEvent(new Event('change'));
        setDisplay(item);
        if (errType) errType.hidden = true;
        wrapper.classList.remove('is-invalid');
        closePanel();
        if (window.assignUpdatePreview) window.assignUpdatePreview();
    });

    buildList();
    if (nativeSel.value) {
        var existing = list.querySelector('[data-value="' + nativeSel.value + '"]');
        if (existing) setDisplay(existing);
    }
})();

(function () {
    var hospitalNative = document.getElementById('id_hospital');
    var roleNative = document.getElementById('id_role');
    var seniorToggle = document.getElementById('id_is_senior');
    var reportingNative = document.getElementById('id_reporting_to');
    if (!hospitalNative || !roleNative || !seniorToggle || !reportingNative) return;

    var wrapper = document.getElementById('reportingCustomSelect');
    var trigger = document.getElementById('reportingSelectTrigger');
    var panel = document.getElementById('reportingSelectPanel');
    var list = document.getElementById('reportingSelectList');
    var label = document.getElementById('reportingSelectLabel');
    var hint = document.getElementById('reportingHint');
    var directorNote = document.getElementById('reportingDirectorNote');
    var directorTextEl = document.getElementById('reportingDirectorText');
    var requiredStar = document.getElementById('reportingRequiredStar');
    var form = document.getElementById('assignMedicalStaffForm');
    var reportingUrl = form ? form.getAttribute('data-reporting-url') : '';

    var initialEl = document.getElementById('initialReportingData');
    var initialValue = '';
    try {
        var parsedInitial = initialEl ? JSON.parse(initialEl.textContent) : null;
        initialValue = (parsedInitial === null || parsedInitial === undefined) ? '' : String(parsedInitial);
    } catch (e) { initialValue = ''; }

    function openPanel() {
        if (wrapper.classList.contains('med-custom-select--locked')) return;
        panel.hidden = false;
        wrapper.classList.add('med-custom-select--open');
        medPositionPanel(trigger, panel);
    }
    function closePanel() {
        panel.hidden = true;
        wrapper.classList.remove('med-custom-select--open');
    }

    function lock(text) {
        wrapper.classList.add('med-custom-select--locked');
        label.textContent = text;
        label.classList.remove('med-custom-select__label--filled');
        reportingNative.innerHTML = '';
        reportingNative.dispatchEvent(new Event('change'));
    }

    function setListMode() {
        wrapper.hidden = false;
        directorNote.hidden = true;
        if (requiredStar) requiredStar.hidden = false;
    }

    function setDirectorMode(director) {
        wrapper.hidden = true;
        directorNote.hidden = false;
        hint.hidden = true;
        if (requiredStar) requiredStar.hidden = true;
        var errReporting = document.getElementById('err_reporting_to');
        if (errReporting) errReporting.hidden = true;
        var hasDirector = !!(director && director.name);
        directorNote.classList.toggle('assign-director-note--warning', !hasDirector);
        directorNote.setAttribute('data-director-name', hasDirector ? director.name : '');
        directorTextEl.textContent = hasDirector
            ? ('Senior doctors report directly to the hospital director — ' + director.name + '.')
            : "Senior doctors report directly to the hospital director, but this hospital doesn't have one assigned yet. Set one from the Hospital Dashboard.";

        reportingNative.innerHTML = '<option value="">---------</option>';
        reportingNative.value = '';
        reportingNative.dispatchEvent(new Event('change'));
        if (window.assignUpdatePreview) window.assignUpdatePreview();
    }

    function renderOptions(options) {
        reportingNative.innerHTML = '<option value="">---------</option>';
        list.innerHTML = '';

        if (!options.length) {
            var empty = document.createElement('li');
            empty.className = 'med-custom-select__empty';
            empty.textContent = 'No senior staff available yet for this selection.';
            list.appendChild(empty);
        }

        options.forEach(function (opt) {
            var o = document.createElement('option');
            o.value = opt.id;
            o.textContent = opt.name + ' (' + opt.role + ')';
            reportingNative.appendChild(o);

            var li = document.createElement('li');
            li.className = 'med-custom-select__item';
            li.setAttribute('data-value', opt.id);
            li.innerHTML =
                '<span class="med-custom-select__item-avatar"><i data-lucide="user-round"></i></span>' +
                '<span class="med-custom-select__item-info"><strong>' + opt.name + '</strong><small>' + opt.role + '</small></span>';
            list.appendChild(li);
        });
        if (window.lucide) lucide.createIcons();

        if (initialValue) {
            var match = options.filter(function (o) { return String(o.id) === initialValue; })[0];
            if (match) {
                reportingNative.value = initialValue;
                label.textContent = match.name + ' (' + match.role + ')';
                label.classList.add('med-custom-select__label--filled');
            }
        }
        if (window.assignUpdatePreview) window.assignUpdatePreview();
    }

    function loadReportingOptions() {
        var hospitalId = hospitalNative.value;
        var roleId = roleNative.value;
        var isSenior = seniorToggle.checked;

        if (!hospitalId || !roleId || !reportingUrl) {
            setListMode();
            lock('Select hospital & role first');
            hint.hidden = false;
            hint.textContent = 'Pick a hospital and role to see reporting options.';
            return;
        }

        hint.hidden = false;
        hint.textContent = 'Loading reporting options…';
        wrapper.classList.remove('med-custom-select--locked');

        var url = reportingUrl + '?hospital=' + encodeURIComponent(hospitalId) +
            '&role=' + encodeURIComponent(roleId) + '&is_senior=' + (isSenior ? '1' : '0');

        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (res) { return res.ok ? res.json() : null; })
            .then(function (data) {
                if (!data) { setListMode(); lock('Unable to load reporting staff'); return; }
                if (data.mode === 'director') {
                    setDirectorMode(data.director);
                    return;
                }
                setListMode();
                if (!data.options || !data.options.length) {
                    lock('No senior staff available yet');
                    hint.hidden = false;
                    hint.textContent = 'No senior staff match this hospital/role yet — assign a senior first.';
                } else {
                    wrapper.classList.remove('med-custom-select--locked');
                    label.textContent = 'Select reporting staff';
                    label.classList.remove('med-custom-select__label--filled');
                    hint.hidden = true;
                    renderOptions(data.options);
                }
            })
            .catch(function () {
                setListMode();
                lock('Unable to load reporting staff');
            });
    }

    trigger.addEventListener('click', function (e) {
        e.stopPropagation();
        if (panel.hidden) openPanel(); else closePanel();
    });
    document.addEventListener('click', function (e) {
        if (!wrapper.contains(e.target)) closePanel();
    });
    list.addEventListener('click', function (e) {
        var item = e.target.closest('.med-custom-select__item');
        if (!item || !item.getAttribute('data-value')) return;
        reportingNative.value = item.getAttribute('data-value');
        reportingNative.dispatchEvent(new Event('change'));
        var nameEl = item.querySelector('strong');
        var smallEl = item.querySelector('small');
        label.textContent = (nameEl ? nameEl.textContent : '') + (smallEl ? ' (' + smallEl.textContent + ')' : '');
        label.classList.add('med-custom-select__label--filled');
        closePanel();
        if (window.assignUpdatePreview) window.assignUpdatePreview();
    });

    hospitalNative.addEventListener('change', loadReportingOptions);
    roleNative.addEventListener('change', loadReportingOptions);
    seniorToggle.addEventListener('change', loadReportingOptions);

    loadReportingOptions();
})();

(function () {
    var hospitalNative = document.getElementById('id_hospital');
    var grid = document.getElementById('facilitiesGrid');
    var form = document.getElementById('assignMedicalStaffForm');
    if (!hospitalNative || !grid || !form) return;

    var urlTemplate = form.getAttribute('data-facilities-url-template') || '';

    var initialEl = document.getElementById('initialFacilitiesData');
    var initialIds = [];
    try {
        var parsed = initialEl ? JSON.parse(initialEl.textContent) : [];
        if (Array.isArray(parsed)) initialIds = parsed.map(String);
    } catch (e) { initialIds = []; }

    var hiddenWrap = document.getElementById('workFacilitiesHidden');
    if (hiddenWrap && hiddenWrap.parentNode) hiddenWrap.parentNode.removeChild(hiddenWrap);

    function renderMessage(text) {
        grid.innerHTML = '<p class="assign-field__hint">' + text + '</p>';
    }

    function renderFacilities(facilities) {
        grid.innerHTML = '';
        if (!facilities.length) {
            renderMessage('This hospital has no facilities configured yet.');
            return;
        }

        facilities.forEach(function (f) {
            var inputId = 'facility_' + f.id;

            var pill = document.createElement('label');
            pill.className = 'assign-facility-pill';
            pill.setAttribute('for', inputId);

            var input = document.createElement('input');
            input.type = 'checkbox';
            input.name = 'work_facilities';
            input.value = f.id;
            input.id = inputId;
            if (initialIds.indexOf(String(f.id)) !== -1) {
                input.checked = true;
                pill.classList.add('is-active');
            }

            var isOther = (f.type || '').toLowerCase() === 'other';
            var iconClass = f.icon || (isOther ? 'bi-building' : 'bi-heart-pulse');

            var icon = document.createElement('span');
            icon.className = 'assign-facility-pill__icon assign-facility-pill__icon--' + (isOther ? 'other' : 'medical');
            icon.innerHTML = '<i class="bi ' + iconClass + '"></i>';

            var text = document.createElement('span');
            text.className = 'assign-facility-pill__label';
            text.textContent = f.name;
            text.setAttribute('data-facility-name', f.name);

            pill.appendChild(input);
            pill.appendChild(icon);
            pill.appendChild(text);
            grid.appendChild(pill);
        });

        if (window.assignUpdatePreview) window.assignUpdatePreview();
    }

    grid.addEventListener('change', function (e) {
        if (!e.target.matches('input[name="work_facilities"]')) return;
        var pill = e.target.closest('.assign-facility-pill');
        if (pill) pill.classList.toggle('is-active', e.target.checked);
        if (window.assignUpdatePreview) window.assignUpdatePreview();
    });

    function loadFacilities(hospitalId) {
        if (!hospitalId || !urlTemplate) {
            renderMessage('Select a hospital to see its facilities.');
            return;
        }
        renderMessage('Loading facilities…');
        var url = urlTemplate.replace('999999', hospitalId);
        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (res) { return res.ok ? res.json() : null; })
            .then(function (data) {
                renderFacilities(data && data.facilities ? data.facilities : []);
            })
            .catch(function () {
                renderMessage('Unable to load facilities right now.');
            });
    }

    hospitalNative.addEventListener('change', function () {
        loadFacilities(hospitalNative.value);
    });

    loadFacilities(hospitalNative.value);
})();

(function () {
    var hospitalNative = document.getElementById('id_hospital');
    var deptNative = document.getElementById('id_department');
    if (!hospitalNative || !deptNative) return;

    var deptWrapper = document.getElementById('departmentCustomSelect');
    var deptLabel   = document.getElementById('departmentSelectLabel');
    var deptList    = document.getElementById('departmentSelectList');
    var deptEmpty   = null;

    var LOCKED_LABEL = 'Select hospital first';
    var EMPTY_LABEL  = 'Select Department';

    var assignForm = document.getElementById('assignMedicalStaffForm');
    var deptUrlTemplate = assignForm ? assignForm.getAttribute('data-dept-url-template') : '';

    function resetDeptDisplay(text) {
        if (!deptLabel) return;
        deptLabel.textContent = text;
        deptLabel.classList.remove('med-custom-select__label--filled');
    }

    function clearDeptSelection(placeholderText) {
        deptNative.value = '';
        deptNative.dispatchEvent(new Event('change'));
        resetDeptDisplay(placeholderText);
    }

    function showEmptyMessage(text) {
        if (!deptList) return;
        if (!deptEmpty) {
            deptEmpty = document.createElement('li');
            deptEmpty.className = 'med-custom-select__empty';
            deptEmpty.setAttribute('data-dept-empty', 'true');
        }
        deptEmpty.textContent = text;
        if (!deptEmpty.parentNode) deptList.appendChild(deptEmpty);
    }

    function hideEmptyMessage() {
        if (deptEmpty && deptEmpty.parentNode) deptEmpty.parentNode.removeChild(deptEmpty);
    }

    function lockDepartment() {
        if (deptWrapper) deptWrapper.classList.add('med-custom-select--locked');
        if (deptList) {
            deptList.querySelectorAll('.med-custom-select__item[data-value]').forEach(function (item) {
                item.classList.add('med-custom-select__item--hidden');
            });
        }
        showEmptyMessage(LOCKED_LABEL);
        clearDeptSelection(LOCKED_LABEL);
    }

    function unlockDepartment() {
        if (deptWrapper) deptWrapper.classList.remove('med-custom-select--locked');
    }

    function applyDeptFilter(allowedIds) {
        var currentValue = deptNative.value;
        var currentStillAllowed = !currentValue ||
            allowedIds.indexOf(parseInt(currentValue, 10)) !== -1;

        var visibleCount = 0;
        if (deptList) {
            deptList.querySelectorAll('.med-custom-select__item[data-value]').forEach(function (item) {
                var allowed = allowedIds.indexOf(parseInt(item.getAttribute('data-value'), 10)) !== -1;
                item.classList.toggle('med-custom-select__item--hidden', !allowed);
                if (allowed) visibleCount++;
            });
        }

        if (visibleCount === 0) {
            showEmptyMessage('No departments linked to this hospital yet.');
        } else {
            hideEmptyMessage();
        }

        if (!currentStillAllowed) {
            clearDeptSelection(EMPTY_LABEL);
        }
    }

    function loadDepartmentsForHospital(hospitalId) {
        unlockDepartment();
        showEmptyMessage('Loading departments…');
        var url = deptUrlTemplate.replace('999999', hospitalId);
        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (res) { return res.ok ? res.json() : null; })
            .then(function (data) {
                applyDeptFilter(data && data.department_ids ? data.department_ids : []);
            })
            .catch(function () {
                applyDeptFilter([]);
            });
    }

    hospitalNative.addEventListener('change', function () {
        if (hospitalNative.value) {
            loadDepartmentsForHospital(hospitalNative.value);
        } else {
            lockDepartment();
        }
    });

    if (hospitalNative.value) {
        loadDepartmentsForHospital(hospitalNative.value);
    } else {
        lockDepartment();
    }
})();

(function () {
    var form = document.getElementById('assignMedicalStaffForm');
    if (!form) return;

    var steps = Array.prototype.slice.call(form.querySelectorAll('.assign-card[data-step]'));
    var progressSteps = Array.prototype.slice.call(document.querySelectorAll('.assign-progress__step'));
    var progressFill = document.getElementById('assignProgressFill');
    var totalSteps = steps.length;
    var current = 1;

    var CUSTOM_SELECT_WRAPPERS = {
        id_hospital: 'hospitalCustomSelect',
        id_department: 'departmentCustomSelect',
        id_role: 'roleCustomSelect',
        id_employment_type: 'employmentTypeCustomSelect'
    };

    function validateStep(step) {
        var valid = true;
        var stepCard = steps[step - 1];
        if (!stepCard) return true;

        if (step === 1) {
            var userVal = document.getElementById('id_user') ? document.getElementById('id_user').value : '';
            var errUser = document.getElementById('err_user');
            var wrapper = document.getElementById('staffCustomSelect');
            if (!userVal) {
                valid = false;
                if (errUser) errUser.hidden = false;
                if (wrapper) wrapper.classList.add('is-invalid');
            } else {
                if (errUser) errUser.hidden = true;
                if (wrapper) wrapper.classList.remove('is-invalid');
            }
        }

        if (step === 2) {
            var reportingNativeEl = document.getElementById('id_reporting_to');
            var directorNoteEl = document.getElementById('reportingDirectorNote');
            var reportingWrapperEl = document.getElementById('reportingCustomSelect');
            var errReporting = document.getElementById('err_reporting_to');
            var isDirectorMode = directorNoteEl && !directorNoteEl.hidden;

            if (reportingNativeEl && !isDirectorMode) {
                var reportingVal = (reportingNativeEl.value || '').trim();
                if (!reportingVal) {
                    valid = false;
                    if (reportingWrapperEl) reportingWrapperEl.classList.add('is-invalid');
                    if (errReporting) errReporting.hidden = false;
                } else {
                    if (reportingWrapperEl) reportingWrapperEl.classList.remove('is-invalid');
                    if (errReporting) errReporting.hidden = true;
                }
            } else {
                if (reportingWrapperEl) reportingWrapperEl.classList.remove('is-invalid');
                if (errReporting) errReporting.hidden = true;
            }
        }

        var requiredEls = Array.prototype.slice.call(stepCard.querySelectorAll('[required]'));
        requiredEls.forEach(function (el) {
            if (el.tagName === 'SELECT' && el.multiple) return;

            var val = (el.value || '').trim();
            var ok = val !== '';

            if (ok && el.type === 'email') {
                ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);
            }

            var fieldName = el.id ? el.id.replace(/^id_/, '') : el.name;
            var errEl = fieldName ? document.getElementById('err_' + fieldName) : null;
            var customWrapperId = CUSTOM_SELECT_WRAPPERS[el.id];
            var customWrapper = customWrapperId ? document.getElementById(customWrapperId) : null;

            if (!ok) {
                valid = false;
                el.classList.add('is-invalid');
                if (customWrapper) customWrapper.classList.add('is-invalid');
                if (errEl) {
                    if (el.type === 'email' && val !== '') {
                        errEl.textContent = 'Enter a valid email address.';
                    }
                    errEl.hidden = false;
                }
            } else {
                el.classList.remove('is-invalid');
                if (customWrapper) customWrapper.classList.remove('is-invalid');
                if (errEl) errEl.hidden = true;
            }
        });

        return valid;
    }

    function goToStep(n) {
        steps.forEach(function (s) {
            s.hidden = parseInt(s.getAttribute('data-step'), 10) !== n;
        });
        progressSteps.forEach(function (p) {
            var n2 = parseInt(p.getAttribute('data-goto'), 10);
            var isComplete = n2 < n;
            p.classList.toggle('is-active', n2 === n);
            p.classList.toggle('is-complete', isComplete);
            var numEl = p.querySelector('.assign-progress__num');
            if (numEl) {
                numEl.textContent = isComplete ? '✓' : numEl.getAttribute('data-num');
            }
        });
        progressFill.style.width = (((n - 1) / (totalSteps - 1)) * 100) + '%';
        current = n;
        if (n === totalSteps) collectReviewSummary();
        window.scrollTo({ top: form.offsetTop - 90, behavior: 'smooth' });
    }

    form.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter') return;
        if (current < totalSteps) {
            e.preventDefault();
            var target = e.target;
            if (target && target.tagName === 'TEXTAREA') return;
            var nextBtn = steps[current - 1].querySelector('.assign-next');
            if (nextBtn) nextBtn.click();
        }
    });

    form.addEventListener('click', function (e) {
        var nextBtn = e.target.closest('.assign-next');
        var backBtn = e.target.closest('.assign-back');
        var editBtn = e.target.closest('.assign-review__edit');

        if (nextBtn) {
            if (validateStep(current)) {
                goToStep(parseInt(nextBtn.getAttribute('data-next'), 10));
            }
        } else if (backBtn) {
            goToStep(parseInt(backBtn.getAttribute('data-back'), 10));
        } else if (editBtn) {
            goToStep(parseInt(editBtn.getAttribute('data-goto'), 10));
        }
    });

    progressSteps.forEach(function (p) {
        p.addEventListener('click', function () {
            var target = parseInt(p.getAttribute('data-goto'), 10);
            if (target < current) { goToStep(target); return; }
            for (var s = current; s < target; s++) {
                if (!validateStep(s)) { goToStep(s); return; }
            }
            goToStep(target);
        });
    });

    form.addEventListener('submit', function (e) {
        for (var s = 1; s <= totalSteps; s++) {
            if (!validateStep(s)) {
                e.preventDefault();
                goToStep(s);
                return;
            }
        }
    });

    ['id_hospital', 'id_department', 'id_role', 'id_employee_id', 'id_employment_type', 'id_work_email'].forEach(function (id) {
        var el = document.getElementById(id);
        if (!el) return;
        el.addEventListener('input', updatePreview);
        el.addEventListener('change', updatePreview);
    });

    function textOf(el) {
        if (!el) return '—';
        if (el.tagName === 'SELECT') {
            var opt = el.options[el.selectedIndex];
            return opt && opt.value ? opt.text : '—';
        }
        return el.value.trim() || '—';
    }

    function updatePreview() {
        document.getElementById('previewHospital').textContent = textOf(document.getElementById('id_hospital'));
        document.getElementById('previewDepartment').textContent = textOf(document.getElementById('id_department'));
        document.getElementById('previewRole').textContent = textOf(document.getElementById('id_role'));
        document.getElementById('previewEmployeeId').textContent = textOf(document.getElementById('id_employee_id'));
        document.getElementById('previewEmploymentType').textContent = textOf(document.getElementById('id_employment_type'));
        document.getElementById('previewWorkEmail').textContent = textOf(document.getElementById('id_work_email'));
    }

    function collectReviewSummary() {
        var previewName = document.getElementById('previewName');
        var previewUsername = document.getElementById('previewUsername');
        var previewAvatar = document.getElementById('previewAvatar');
        var reviewName = document.getElementById('reviewName');
        var reviewUsername = document.getElementById('reviewUsername');
        var reviewAvatar = document.getElementById('reviewAvatar');

        if (reviewName) reviewName.textContent = previewName ? previewName.textContent : 'No staff selected';
        if (reviewUsername) reviewUsername.textContent = previewUsername ? previewUsername.textContent : '';
        if (reviewAvatar && previewAvatar) reviewAvatar.innerHTML = previewAvatar.innerHTML;

        setText('reviewHospital', textOf(document.getElementById('id_hospital')));
        setText('reviewDepartment', textOf(document.getElementById('id_department')));
        setText('reviewRole', textOf(document.getElementById('id_role')));
        setText('reviewEmployeeId', textOf(document.getElementById('id_employee_id')));
        setText('reviewEmploymentType', textOf(document.getElementById('id_employment_type')));
        setText('reviewHireDate', textOf(document.getElementById('id_hire_date')));
        setText('reviewWorkEmail', textOf(document.getElementById('id_work_email')));

        setText('reviewQualification', textOf(document.getElementById('id_qualification')));
        setText('reviewSpecialization', textOf(document.getElementById('id_specialization')));
        setText('reviewLicense', textOf(document.getElementById('id_medical_license_number')));

        var expEl = document.getElementById('id_years_of_experience');
        setText('reviewExperience', (expEl && expEl.value) ? expEl.value + ' years' : '—');
        setText('reviewAddress', textOf(document.getElementById('id_address')));

        setText('reviewEmergencyName', textOf(document.getElementById('id_emergency_contact_name')));
        setText('reviewEmergencyPhone', textOf(document.getElementById('id_emergency_contact_phone')));

        var seniorEl = document.getElementById('id_is_senior');
        setText('reviewSenior', seniorEl && seniorEl.checked ? 'Yes' : 'No');

        var reportingNative = document.getElementById('id_reporting_to');
        var directorNote = document.getElementById('reportingDirectorNote');
        if (directorNote && !directorNote.hidden) {
            var directorName = directorNote.getAttribute('data-director-name');
            setText('reviewReporting', directorName ? ('Hospital Director — ' + directorName) : 'Hospital Director (not yet assigned)');
        } else {
            var reportingOpt = reportingNative && reportingNative.selectedOptions ? reportingNative.selectedOptions[0] : null;
            setText('reviewReporting', reportingOpt && reportingOpt.value ? reportingOpt.textContent : '—');
        }

        var checkedFacilities = Array.prototype.slice.call(
            document.querySelectorAll('input[name="work_facilities"]:checked')
        ).map(function (cb) {
            var nameEl = cb.parentElement ? cb.parentElement.querySelector('[data-facility-name]') : null;
            return nameEl ? nameEl.getAttribute('data-facility-name') : cb.value;
        });
        setText('reviewFacilities', checkedFacilities.length ? checkedFacilities.join(', ') : '—');

        if (window.lucide) lucide.createIcons();
    }

    function setText(id, value) {
        var el = document.getElementById(id);
        if (el) el.textContent = value;
    }

    function firstStepWithError() {
        for (var i = 0; i < steps.length; i++) {
            var errs = steps[i].querySelectorAll('.assign-form__error');
            for (var j = 0; j < errs.length; j++) {
                if (!errs[j].hidden) return parseInt(steps[i].getAttribute('data-step'), 10);
            }
        }
        return 1;
    }

    function highlightServerErrors() {
        document.querySelectorAll('.assign-form__error').forEach(function (errEl) {
            if (errEl.hidden) return;
            var prev = errEl.previousElementSibling;
            if (prev && ['SELECT', 'INPUT', 'TEXTAREA'].indexOf(prev.tagName) !== -1) {
                prev.classList.add('is-invalid');
            }
        });
        var errUser = document.getElementById('err_user');
        var staffWrapper = document.getElementById('staffCustomSelect');
        if (errUser && !errUser.hidden && staffWrapper) {
            staffWrapper.classList.add('is-invalid');
        }
        var errHospital = document.getElementById('err_hospital');
        var hospitalWrapper = document.getElementById('hospitalCustomSelect');
        if (errHospital && !errHospital.hidden && hospitalWrapper) {
            hospitalWrapper.classList.add('is-invalid');
        }
        var errDept = document.getElementById('err_department');
        var deptWrapper = document.getElementById('departmentCustomSelect');
        if (errDept && !errDept.hidden && deptWrapper) {
            deptWrapper.classList.add('is-invalid');
        }
        var errRole = document.getElementById('err_role');
        var roleWrapper = document.getElementById('roleCustomSelect');
        if (errRole && !errRole.hidden && roleWrapper) {
            roleWrapper.classList.add('is-invalid');
        }
        var errEmploymentType = document.getElementById('err_employment_type');
        var employmentTypeWrapper = document.getElementById('employmentTypeCustomSelect');
        if (errEmploymentType && !errEmploymentType.hidden && employmentTypeWrapper) {
            employmentTypeWrapper.classList.add('is-invalid');
        }
    }

    window.assignUpdatePreview = updatePreview;
    updatePreview();
    highlightServerErrors();
    goToStep(firstStepWithError());
})();