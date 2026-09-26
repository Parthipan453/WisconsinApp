function medPositionPanel(trigger, panel) {
    var isMobile = window.matchMedia('(max-width: 480px)').matches;
    var margin = 8;
    var minHeight = 160;
    var maxHeight = 340;
    var rect = trigger.getBoundingClientRect();
    var viewportH = window.innerHeight;
    var viewportW = window.innerWidth;
    var spaceBelow = viewportH - rect.bottom - margin;
    var spaceAbove = rect.top - margin;
    var isCompact = panel.classList.contains('med-custom-select__panel--compact');

    panel.style.position = 'fixed';

    if (isMobile) {
        panel.style.left = '12px';
        panel.style.right = '12px';
        panel.style.width = 'auto';
    } else {
        var panelWidth = isCompact ? Math.max(rect.width, 170) : rect.width;
        var left = isCompact ? (rect.right - panelWidth) : rect.left;
        if (left + panelWidth + margin > viewportW) {
            left = viewportW - panelWidth - margin;
        }
        if (left < margin) left = margin;
        panel.style.left = left + 'px';
        panel.style.right = 'auto';
        panel.style.width = panelWidth + 'px';
    }

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

function medInitCustomSelect(opts) {
    var wrapper = document.getElementById(opts.wrapperId);
    if (!wrapper) return null;

    var trigger = document.getElementById(opts.triggerId);
    var panel   = document.getElementById(opts.panelId);
    var list    = document.getElementById(opts.listId);
    var label   = document.getElementById(opts.labelId);
    var iconBox = opts.iconId ? document.getElementById(opts.iconId) : null;
    var search  = opts.searchId ? document.getElementById(opts.searchId) : null;
    var nativeSel = document.getElementById(opts.nativeId);
    if (!nativeSel) return null;

    function iconFor(value) {
        if (!opts.icons) return opts.defaultIcon || 'tag';
        return opts.icons[(value || '').toUpperCase()] || opts.defaultIcon || 'tag';
    }

    function buildList() {
        list.innerHTML = '';
        var count = 0;
        Array.prototype.forEach.call(nativeSel.options, function (opt) {
            if (!opt.value) return;
            if (opts.allowedValues && opts.allowedValues.indexOf(opt.value) === -1) return;
            count++;
            var li = document.createElement('li');
            li.className = 'med-custom-select__item';
            li.setAttribute('data-value', opt.value);
            li.setAttribute('data-search', opt.text.toLowerCase());
            li.innerHTML =
                '<span class="med-custom-select__item-avatar med-role-icon med-role-icon--other"><i data-lucide="' + iconFor(opt.value) + '"></i></span>' +
                '<span class="med-custom-select__item-info"><strong>' + opt.text + '</strong></span>';
            list.appendChild(li);
        });
        if (count === 0) {
            var empty = document.createElement('li');
            empty.className = 'med-custom-select__empty';
            empty.textContent = opts.emptyHint || 'No options available';
            list.appendChild(empty);
        }
        if (window.lucide) lucide.createIcons();
    }

    function filterList(term) {
        if (!search) return;
        list.querySelectorAll('.med-custom-select__item').forEach(function (item) {
            var haystack = item.getAttribute('data-search') || '';
            item.style.display = haystack.indexOf(term) !== -1 ? '' : 'none';
        });
    }

    var panelHome = { parent: panel.parentNode, nextSibling: panel.nextSibling };

    function onAncestorScroll(e) {
        if (panel.hidden) return;
        if (e.target && (e.target === panel || panel.contains(e.target))) return;
        medPositionPanel(trigger, panel);
    }

    function openPanel() {
        if (!panelHome) panelHome = { parent: panel.parentNode, nextSibling: panel.nextSibling };
        document.body.appendChild(panel);
        panel.hidden = false;
        wrapper.classList.add('med-custom-select--open');
        medPositionPanel(trigger, panel);
        if (search) { search.value = ''; filterList(''); search.focus(); }
        window.addEventListener('scroll', onAncestorScroll, true);
    }
    function closePanel() {
        panel.hidden = true;
        wrapper.classList.remove('med-custom-select--open');
        window.removeEventListener('scroll', onAncestorScroll, true);
        if (panelHome && panelHome.parent) {
            if (panelHome.nextSibling && panelHome.nextSibling.parentNode === panelHome.parent) {
                panelHome.parent.insertBefore(panel, panelHome.nextSibling);
            } else {
                panelHome.parent.appendChild(panel);
            }
        }
        panel.style.position = '';
        panel.style.top = '';
        panel.style.bottom = '';
        panel.style.left = '';
        panel.style.right = '';
        panel.style.width = '';
        panel.style.maxHeight = '';
    }

    function setDisplay(item) {
        var nameEl = item.querySelector('strong');
        var text = nameEl ? nameEl.textContent : (opts.placeholder || 'Select');
        label.textContent = text;
        label.title = text;
        label.classList.add('med-custom-select__label--filled');
        if (iconBox) {
            var val = item.getAttribute('data-value');
            iconBox.innerHTML = '<i data-lucide="' + iconFor(val) + '"></i>';
            if (window.lucide) lucide.createIcons();
        }
    }

    function refresh() {
        buildList();
        var currentVal = (nativeSel.value || '').trim();
        if (currentVal) {
            var existing = list.querySelector('[data-value="' + currentVal + '"]');
            if (!existing) {
                existing = Array.prototype.find.call(
                    list.querySelectorAll('.med-custom-select__item'),
                    function (item) {
                        return (item.getAttribute('data-value') || '').trim().toLowerCase() === currentVal.toLowerCase();
                    }
                );
            }
            if (existing) {
                setDisplay(existing);
                return;
            }
        }
        label.textContent = opts.placeholder || 'Select';
        label.classList.remove('med-custom-select__label--filled');
        if (iconBox) {
            iconBox.innerHTML = '<i data-lucide="' + (opts.defaultIcon || 'tag') + '"></i>';
            if (window.lucide) lucide.createIcons();
        }
    }

    trigger.addEventListener('click', function (e) {
        e.stopPropagation();
        if (panel.hidden) openPanel(); else closePanel();
    });
    document.addEventListener('click', function (e) {
        if (!wrapper.contains(e.target) && !panel.contains(e.target)) closePanel();
    });
    if (search) {
        search.addEventListener('input', function () {
            filterList(search.value.trim().toLowerCase());
        });
    }
    list.addEventListener('click', function (e) {
        var item = e.target.closest('.med-custom-select__item');
        if (!item) return;
        nativeSel.value = item.getAttribute('data-value');
        nativeSel.dispatchEvent(new Event('change'));
        setDisplay(item);
        wrapper.classList.remove('is-invalid');
        closePanel();
    });

    refresh();
    return {
        refresh: refresh,
        close: closePanel,
        setAllowed: function (ids, hint) {
            opts.allowedValues = ids;
            if (hint !== undefined) opts.emptyHint = hint;
            refresh();
        }
    };
}

window.medCloseAllCustomSelects = function () {
    [window.shiftHospitalSelect, window.shiftDepartmentSelect, window.shiftTypeSelect].forEach(function (inst) {
        if (inst && inst.close) inst.close();
    });
};

window.shiftHospitalSelect = medInitCustomSelect({
    wrapperId: 'shiftHospitalCustomSelect',
    triggerId: 'shiftHospitalTrigger',
    panelId: 'shiftHospitalPanel',
    listId: 'shiftHospitalList',
    labelId: 'shiftHospitalLabel',
    iconId: 'shiftHospitalIcon',
    searchId: 'shiftHospitalSearch',
    nativeId: 'id_hospital',
    placeholder: 'Select Hospital',
    defaultIcon: 'hospital'
});

window.shiftDepartmentSelect = medInitCustomSelect({
    wrapperId: 'shiftDepartmentCustomSelect',
    triggerId: 'shiftDepartmentTrigger',
    panelId: 'shiftDepartmentPanel',
    listId: 'shiftDepartmentList',
    labelId: 'shiftDepartmentLabel',
    iconId: 'shiftDepartmentIcon',
    searchId: 'shiftDepartmentSearch',
    nativeId: 'id_department',
    placeholder: 'Select Department',
    defaultIcon: 'building-2',
    emptyHint: 'Select a hospital first'
});

window.shiftTypeSelect = medInitCustomSelect({
    wrapperId: 'shiftTypeCustomSelect',
    triggerId: 'shiftTypeTrigger',
    panelId: 'shiftTypePanel',
    listId: 'shiftTypeList',
    labelId: 'shiftTypeLabel',
    iconId: 'shiftTypeIcon',
    nativeId: 'id_shift_type',
    placeholder: 'Select Shift Type',
    defaultIcon: 'sun',
    icons: { MORNING: 'sunrise', AFTERNOON: 'sun', EVENING: 'sunset', NIGHT: 'moon' }
});

window.medRefreshShiftSelects = function () {
    if (window.shiftHospitalSelect) window.shiftHospitalSelect.refresh();
    if (window.shiftDepartmentSelect) window.shiftDepartmentSelect.refresh();
    if (window.shiftTypeSelect) window.shiftTypeSelect.refresh();
};

(function () {
    'use strict';

    var config = window.shiftConfig || {};

    function openBsModal(el) {
        if (!el || !window.bootstrap) return;
        bootstrap.Modal.getOrCreateInstance(el).show();
    }

    function hideBsModal(el) {
        if (!el || !window.bootstrap) return;
        var instance = bootstrap.Modal.getInstance(el);
        if (instance) instance.hide();
    }

    var recurrenceToggle = document.getElementById('recurrenceToggle');
    var recurrenceHidden = document.getElementById('id_recurrence_type');
    var weekdayField = document.getElementById('weekdayPatternField');
    var startDateLabel = document.getElementById('startDateLabel');
    var startDateHint = document.getElementById('startDateHint');

    var HINTS = {
        DAILY: { label: 'Date', hint: 'Pick the exact date this shift applies to.' },
        WEEKLY: { label: 'Any Date in the Week', hint: 'Pick any date — the shift auto-covers Mon–Sun of that week.' },
        MONTHLY: { label: 'Any Date in the Month', hint: 'Pick any date — the shift auto-covers the whole calendar month.' }
    };

    function setRecurrence(type) {
        if (recurrenceHidden) recurrenceHidden.value = type;
        if (recurrenceToggle) {
            recurrenceToggle.querySelectorAll('.sched-type-btn').forEach(function (btn) {
                btn.classList.toggle('is-active', btn.getAttribute('data-recurrence') === type);
            });
        }
        if (weekdayField) {
            weekdayField.classList.toggle('d-none', type === 'DAILY');
        }
        var info = HINTS[type] || HINTS.DAILY;
        if (startDateLabel) startDateLabel.textContent = info.label;
        if (startDateHint) startDateHint.textContent = info.hint;
        if (typeof renderWorkingHoursForSelection === 'function') renderWorkingHoursForSelection();
    }

    if (recurrenceToggle) {
        recurrenceToggle.addEventListener('click', function (e) {
            var btn = e.target.closest('.sched-type-btn');
            if (btn) setRecurrence(btn.getAttribute('data-recurrence'));
        });
    }

    var shiftModalEl = document.getElementById('shiftFormModal');
    var shiftForm = document.getElementById('shiftForm');
    var modalTitleEl = document.getElementById('shiftFormModalTitle');
    var submitLabelEl = document.getElementById('shiftFormSubmitLabel');
    var shiftFormErrorBanner = document.getElementById('shiftFormErrorBanner');
    var shiftFormErrorList = document.getElementById('shiftFormErrorList');

    var FIELD_ERROR_TARGETS = {
        hospital: { errorId: 'err_hospital', invalidId: 'shiftHospitalCustomSelect' },
        department: { errorId: 'err_department', invalidId: 'shiftDepartmentCustomSelect' },
        shift_label: { errorId: 'err_shift_label', invalidId: 'id_shift_label' },
        shift_type: { errorId: 'err_shift_type', invalidId: 'shiftTypeCustomSelect' },
        start_date: { errorId: 'err_start_date', invalidId: 'id_start_date' },
        start_time: { errorId: 'err_start_time', invalidId: 'id_start_time' },
        end_time: { errorId: 'err_end_time', invalidId: 'id_end_time' },
        weekday_pattern: { errorId: 'err_weekday_pattern', invalidId: null }
    };

    function escapeHtml(str) {
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function clearFormErrors() {
        document.querySelectorAll('.shiftmgmt-field-error').forEach(function (el) {
            el.textContent = '';
            el.classList.add('d-none');
        });
        document.querySelectorAll('#shiftFormModal .is-invalid').forEach(function (el) {
            el.classList.remove('is-invalid');
        });
        if (shiftFormErrorBanner) shiftFormErrorBanner.classList.add('d-none');
        if (shiftFormErrorList) shiftFormErrorList.innerHTML = '';
    }

    function applyFormErrors(errors) {
        clearFormErrors();
        var bannerItems = [];
        Object.keys(errors || {}).forEach(function (field) {
            var msgs = errors[field] || [];
            var target = FIELD_ERROR_TARGETS[field];
            if (target) {
                var errEl = document.getElementById(target.errorId);
                if (errEl) {
                    errEl.textContent = msgs.join(' ');
                    errEl.classList.remove('d-none');
                }
                if (target.invalidId) {
                    var invEl = document.getElementById(target.invalidId);
                    if (invEl) invEl.classList.add('is-invalid');
                }
            }
            msgs.forEach(function (m) { bannerItems.push(escapeHtml(m)); });
        });
        if (bannerItems.length && shiftFormErrorList && shiftFormErrorBanner) {
            shiftFormErrorList.innerHTML = bannerItems.map(function (m) { return '<li>' + m + '</li>'; }).join('');
            shiftFormErrorBanner.classList.remove('d-none');
            shiftFormErrorBanner.scrollIntoView({ block: 'nearest' });
        }
    }

    var hospitalNativeSelect = document.getElementById('id_hospital');
    var departmentNativeSelect = document.getElementById('id_department');

    function applyHospitalDeptFilter(hospitalId, preserveDeptId) {
        if (!config.isAdminView || !config.departmentsByHospitalUrlTemplate) {
            return;
        }
        if (!hospitalId) {
            if (departmentNativeSelect) departmentNativeSelect.value = '';
            if (window.shiftDepartmentSelect) window.shiftDepartmentSelect.setAllowed([], 'Select a hospital first');
            return;
        }
        var url = config.departmentsByHospitalUrlTemplate.replace('__ID__', hospitalId);
        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                var ids = (data.department_ids || []).map(String);
                if (departmentNativeSelect) {
                    var currentVal = preserveDeptId != null ? String(preserveDeptId) : departmentNativeSelect.value;
                    departmentNativeSelect.value = (currentVal && ids.indexOf(currentVal) !== -1) ? currentVal : '';
                }
                var hint = ids.length ? undefined : 'No departments found for this hospital';
                if (window.shiftDepartmentSelect) window.shiftDepartmentSelect.setAllowed(ids, hint);
            })
            .catch(function () {
                if (departmentNativeSelect) departmentNativeSelect.value = '';
                if (window.shiftDepartmentSelect) window.shiftDepartmentSelect.setAllowed([], 'Could not load departments — try again');
            });
    }

    var WEEKDAY_LABELS = { monday: 'Mon', tuesday: 'Tue', wednesday: 'Wed', thursday: 'Thu', friday: 'Fri', saturday: 'Sat', sunday: 'Sun' };
    var WEEKDAY_ORDER = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
    var WEEKDAY_CODES = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
    var hospitalHoursPanel = document.getElementById('hospitalHoursPanel');
    var hospitalHoursText = document.getElementById('hospitalHoursText');
    var workingHoursConflict = document.getElementById('workingHoursConflict');
    var workingHoursConflictText = document.getElementById('workingHoursConflictText');
    var startDateInput = document.getElementById('id_start_date');

    var hospitalScheduleCache = { schedule: {}, overrides: {}, loaded: false };
    var hoursConflictActive = false;

    function parseISODate(str) {
        if (!str) return null;
        var parts = str.split('-');
        if (parts.length !== 3) return null;
        var d = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
        return isNaN(d.getTime()) ? null : d;
    }
    function toISODate(d) {
        var y = d.getFullYear();
        var m = ('0' + (d.getMonth() + 1)).slice(-2);
        var day = ('0' + d.getDate()).slice(-2);
        return y + '-' + m + '-' + day;
    }
    function addDays(d, n) {
        var r = new Date(d);
        r.setDate(r.getDate() + n);
        return r;
    }
    function weekdayCodeOf(d) {
        return WEEKDAY_CODES[(d.getDay() + 6) % 7];
    }
    function getCheckedWeekdayCodes() {
        var codes = [];
        document.querySelectorAll('#weekdayPatternField input[type="checkbox"]:checked').forEach(function (cb) {
            codes.push(cb.value);
        });
        return codes;
    }

    function computeCandidateDates(recurrenceType, startDateStr) {
        var start = parseISODate(startDateStr);
        if (!start) return [];
        if (recurrenceType === 'WEEKLY') {
            var monday = addDays(start, -((start.getDay() + 6) % 7));
            var week = [];
            for (var i = 0; i < 7; i++) week.push(addDays(monday, i));
            return week;
        }
        if (recurrenceType === 'MONTHLY') {
            var first = new Date(start.getFullYear(), start.getMonth(), 1);
            var last = new Date(start.getFullYear(), start.getMonth() + 1, 0);
            var days = [];
            for (var cur = first; cur <= last; cur = addDays(cur, 1)) days.push(cur);
            return days;
        }
        return [start];
    }

    function setHoursConflict(active) {
        hoursConflictActive = active;
        var submitBtn = document.getElementById('shiftFormSubmitBtn');
        if (submitBtn) submitBtn.disabled = active;
        if (hospitalHoursPanel) hospitalHoursPanel.classList.toggle('shiftmgmt-hours-hint--blocked', active);
    }

    function resolveWorkingWindow(schedule, overrides, date) {
        var code = weekdayCodeOf(date);
        var key = WEEKDAY_ORDER[WEEKDAY_CODES.indexOf(code)];
        var day = schedule[key] || {};
        var override = overrides[toISODate(date)];

        if (override && override.closed) {
            return { closed: true, enabled: false, opening: null, closing: null, isOverride: true, weekdayLabel: WEEKDAY_LABELS[key] };
        }
        if (override) {
            return {
                closed: false,
                enabled: true,
                opening: override.opening || day.opening || null,
                closing: override.closing || day.closing || null,
                isOverride: true,
                weekdayLabel: WEEKDAY_LABELS[key]
            };
        }
        return {
            closed: false,
            enabled: !!day.enabled,
            opening: day.opening || null,
            closing: day.closing || null,
            isOverride: false,
            weekdayLabel: WEEKDAY_LABELS[key]
        };
    }

    function timeToMinutes(hhmm) {
        if (!hhmm) return null;
        var parts = hhmm.split(':');
        if (parts.length < 2) return null;
        var h = parseInt(parts[0], 10), m = parseInt(parts[1], 10);
        if (isNaN(h) || isNaN(m)) return null;
        return h * 60 + m;
    }

    function renderWorkingHoursForSelection() {
        if (!hospitalHoursText) return;

        if (!hospitalScheduleCache.loaded) {
            hospitalHoursText.textContent = 'Select a hospital to see its working hours.';
            if (workingHoursConflict) workingHoursConflict.classList.add('d-none');
            setHoursConflict(false);
            return;
        }

        var startDateStr = startDateInput ? startDateInput.value : '';
        var recurrenceType = recurrenceHidden ? recurrenceHidden.value : 'DAILY';

        if (!startDateStr) {
            hospitalHoursText.textContent = 'Pick a date to see the working hours that apply.';
            if (workingHoursConflict) workingHoursConflict.classList.add('d-none');
            setHoursConflict(false);
            return;
        }

        var schedule = hospitalScheduleCache.schedule || {};
        var overrides = hospitalScheduleCache.overrides || {};
        var checkedCodes = recurrenceType === 'DAILY' ? WEEKDAY_CODES.slice() : getCheckedWeekdayCodes();
        var candidateDates = computeCandidateDates(recurrenceType, startDateStr);
        var activeDates = candidateDates.filter(function (d) {
            return checkedCodes.indexOf(weekdayCodeOf(d)) !== -1;
        });

        if (!activeDates.length) {
            hospitalHoursText.textContent = 'No active days selected.';
            if (workingHoursConflict) workingHoursConflict.classList.add('d-none');
            setHoursConflict(false);
            return;
        }

        var summarize = recurrenceType === 'MONTHLY' && activeDates.length > 8;
        var displayDates = activeDates;
        if (summarize) {
            var seen = {};
            displayDates = [];
            activeDates.forEach(function (d) {
                var code = weekdayCodeOf(d);
                if (seen[code]) return;
                seen[code] = true;
                displayDates.push(d);
            });
        }

        var parts = displayDates.map(function (d) {
            var window = resolveWorkingWindow(schedule, overrides, d);
            var label = summarize ? window.weekdayLabel : (window.weekdayLabel + ' ' + (d.getMonth() + 1) + '/' + d.getDate());
            if (window.closed) return label + ': Holiday';
            if (!window.enabled) return label + ': Closed';
            var suffix = window.isOverride ? ' (modified)' : '';
            return label + ': ' + (window.opening || '\u2014') + '\u2013' + (window.closing || '\u2014') + suffix;
        });
        hospitalHoursText.textContent = parts.join(' \u00b7 ') + (summarize ? ' (weekday pattern \u2014 holidays checked separately)' : '');

        var startTimeInput = document.getElementById('id_start_time');
        var endTimeInput = document.getElementById('id_end_time');
        var startMinutes = timeToMinutes(startTimeInput ? startTimeInput.value : '');
        var endMinutes = timeToMinutes(endTimeInput ? endTimeInput.value : '');

        var conflicts = [];
        activeDates.forEach(function (d) {
            var window = resolveWorkingWindow(schedule, overrides, d);
            var iso = toISODate(d);

            if (window.closed) {
                conflicts.push(iso + ' is a holiday/closed for this hospital.');
                return;
            }
            if (!window.enabled) {
                conflicts.push(window.weekdayLabel + ' is not a working day for this hospital.');
                return;
            }

            var hoursLabel = window.isOverride ? ('the modified hours for ' + iso) : (window.weekdayLabel + '\u2019s hospital hours');
            var openingMin = timeToMinutes(window.opening);
            var closingMin = timeToMinutes(window.closing);
            if (startMinutes != null && openingMin != null && startMinutes < openingMin) {
                conflicts.push('Shift starts before ' + hoursLabel + ' opening time (' + window.opening + ').');
            }
            if (endMinutes != null && closingMin != null && endMinutes > closingMin) {
                conflicts.push('Shift ends after ' + hoursLabel + ' closing time (' + window.closing + ').');
            }
        });
        conflicts = conflicts.filter(function (msg, i) { return conflicts.indexOf(msg) === i; });

        if (conflicts.length) {
            var shown = conflicts.slice(0, 4);
            var extra = conflicts.length - shown.length;
            if (workingHoursConflictText) {
                workingHoursConflictText.textContent = shown.join(' \u2022 ') + (extra > 0 ? ' (+' + extra + ' more)' : '') +
                    ' \u2014 shift can\u2019t be created for this selection.';
            }
            if (workingHoursConflict) workingHoursConflict.classList.remove('d-none');
            setHoursConflict(true);
        } else {
            if (workingHoursConflict) workingHoursConflict.classList.add('d-none');
            setHoursConflict(false);
        }
    }

    function loadHospitalWorkingHours(hospitalId) {
        if (hospitalHoursPanel) hospitalHoursPanel.classList.add('d-none');
        hospitalScheduleCache = { schedule: {}, overrides: {}, loaded: false };
        setHoursConflict(false);
        if (!hospitalId || !config.hospitalWorkingHoursUrlTemplate) return;
        var url = config.hospitalWorkingHoursUrlTemplate.replace('__ID__', hospitalId);
        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (!data.found) return;
                hospitalScheduleCache = {
                    schedule: data.weekly_schedule || {},
                    overrides: data.overrides || {},
                    loaded: true
                };
                if (hospitalHoursPanel) hospitalHoursPanel.classList.remove('d-none');
                renderWorkingHoursForSelection();
            })
            .catch(function () {
                if (hospitalHoursText) hospitalHoursText.textContent = 'Could not load working hours for this hospital.';
                if (hospitalHoursPanel) hospitalHoursPanel.classList.remove('d-none');
            });
    }

    if (hospitalNativeSelect) {
        hospitalNativeSelect.addEventListener('change', function () {
            applyHospitalDeptFilter(this.value);
            loadHospitalWorkingHours(this.value);
        });
    }
    if (startDateInput) {
        startDateInput.addEventListener('change', renderWorkingHoursForSelection);
    }
    ['id_shift_label', 'id_start_date', 'id_start_time', 'id_end_time'].forEach(function (id) {
        var el = document.getElementById(id);
        if (!el) return;
        el.addEventListener('input', function () {
            el.classList.remove('is-invalid');
            var target = Object.keys(FIELD_ERROR_TARGETS).map(function (k) { return FIELD_ERROR_TARGETS[k]; })
                .find(function (t) { return t.invalidId === id; });
            if (target) {
                var errEl = document.getElementById(target.errorId);
                if (errEl) { errEl.textContent = ''; errEl.classList.add('d-none'); }
            }
            if (id === 'id_start_time' || id === 'id_end_time') renderWorkingHoursForSelection();
        });
    });
    if (weekdayField) {
        weekdayField.addEventListener('change', function (e) {
            if (e.target && e.target.matches('input[type="checkbox"]')) renderWorkingHoursForSelection();
        });
    }
    applyHospitalDeptFilter(hospitalNativeSelect ? hospitalNativeSelect.value : null);
    loadHospitalWorkingHours(hospitalNativeSelect ? hospitalNativeSelect.value : null);

    function resetShiftForm() {
        if (!shiftForm) return;
        shiftForm.reset();
        shiftForm.action = config.createUrl || shiftForm.action;
        if (modalTitleEl) modalTitleEl.textContent = 'Create Shift';
        if (submitLabelEl) submitLabelEl.textContent = 'Create Shift';
        document.querySelectorAll('#weekdayPatternField input[type="checkbox"]').forEach(function (cb) {
            cb.checked = true;
        });
        clearFormErrors();
        setRecurrence('DAILY');
        if (window.medRefreshShiftSelects) window.medRefreshShiftSelects();
        applyHospitalDeptFilter(hospitalNativeSelect ? hospitalNativeSelect.value : null);
        loadHospitalWorkingHours(hospitalNativeSelect ? hospitalNativeSelect.value : null);
    }

    if (shiftForm) {
        shiftForm.addEventListener('submit', function (e) {
            e.preventDefault();

            if (hoursConflictActive) {
                if (hospitalHoursPanel) hospitalHoursPanel.scrollIntoView({ block: 'center', behavior: 'smooth' });
                return;
            }

            clearFormErrors();
            var submitBtn = document.getElementById('shiftFormSubmitBtn');
            var originalLabel = submitLabelEl ? submitLabelEl.textContent : '';
            if (submitBtn) submitBtn.disabled = true;
            if (submitLabelEl) submitLabelEl.textContent = 'Saving...';

            fetch(shiftForm.action, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                body: new FormData(shiftForm)
            })
                .then(function (res) {
                    return res.json().then(function (data) { return { ok: res.ok, data: data }; });
                })
                .then(function (result) {
                    if (result.ok && result.data && result.data.success) {
                        hideBsModal(shiftModalEl);
                        window.location.reload();
                        return;
                    }
                    applyFormErrors((result.data && result.data.errors) || {});
                })
                .catch(function () {
                    if (shiftFormErrorList && shiftFormErrorBanner) {
                        shiftFormErrorList.innerHTML = '<li>Something went wrong while saving. Please try again.</li>';
                        shiftFormErrorBanner.classList.remove('d-none');
                    }
                })
                .finally(function () {
                    if (submitBtn) submitBtn.disabled = hoursConflictActive;
                    if (submitLabelEl) submitLabelEl.textContent = originalLabel;
                });
        });
    }

    var openCreateShiftBtn = document.getElementById('openCreateShiftBtn');
    if (openCreateShiftBtn) {
        openCreateShiftBtn.addEventListener('click', function () {
            resetShiftForm();
            openBsModal(shiftModalEl);
        });
    }

    if (shiftModalEl) {
        shiftModalEl.addEventListener('hidden.bs.modal', function () {
            if (window.medCloseAllCustomSelects) window.medCloseAllCustomSelects();
            resetShiftForm();
        });
    }

    function fillShiftForm(data) {
        var setVal = function (id, val) {
            var el = document.getElementById(id);
            if (el) el.value = val != null ? val : '';
        };
        setVal('id_hospital', data.hospital);
        setVal('id_department', data.department);
        setVal('id_shift_type', data.shift_type);
        setVal('id_shift_label', data.shift_label);
        setVal('id_start_date', data.start_date);
        setVal('id_start_time', data.start_time);
        setVal('id_end_time', data.end_time);

        var activeDays = data.weekday_pattern || [];
        document.querySelectorAll('#weekdayPatternField input[type="checkbox"]').forEach(function (cb) {
            cb.checked = activeDays.indexOf(cb.value) !== -1;
        });

        setRecurrence(data.recurrence_type || 'DAILY');
        if (window.medRefreshShiftSelects) window.medRefreshShiftSelects();
        applyHospitalDeptFilter(data.hospital, data.department);
        loadHospitalWorkingHours(data.hospital);
    }

    function loadShiftForEdit(shiftId) {
        if (!config.editUrlTemplate) return;
        var url = config.editUrlTemplate.replace('__ID__', shiftId);
        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                resetShiftForm();
                fillShiftForm(data);
                shiftForm.action = url;
                if (modalTitleEl) modalTitleEl.textContent = 'Edit Shift';
                if (submitLabelEl) submitLabelEl.textContent = 'Save Changes';
                openBsModal(shiftModalEl);
                if (window.lucide) lucide.createIcons();
            })
            .catch(function () {
                console.error('Could not load shift details.');
            });
    }

    document.querySelectorAll('.sched-row-btn--edit[data-shift-id]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            loadShiftForEdit(btn.getAttribute('data-shift-id'));
        });
    });

    var deleteModalEl = document.getElementById('deleteShiftModal');
    var deleteForm = document.getElementById('deleteShiftForm');
    var deleteNameEl = document.getElementById('deleteShiftName');

    document.querySelectorAll('.sched-row-btn--delete[data-shift-id]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            if (!config.deleteUrlTemplate || !deleteForm) return;
            deleteForm.action = config.deleteUrlTemplate.replace('__ID__', btn.getAttribute('data-shift-id'));
            if (deleteNameEl) deleteNameEl.textContent = btn.getAttribute('data-shift-name') || 'this shift';
            openBsModal(deleteModalEl);
        });
    });

    var assignModalEl = document.getElementById('shiftAssignModal');
    var assignModalShiftLabel = document.getElementById('assignModalShiftLabel');
    var assignedStaffListEl = document.getElementById('assignedStaffList');
    var assignedEmptyMsg = document.getElementById('assignedEmptyMsg');
    var assignStaffListEl = document.getElementById('assignStaffList');
    var assignStaffSearch = document.getElementById('assignStaffSearch');
    var assignSelectedCountEl = document.getElementById('assignSelectedCount');
    var assignStaffForm = document.getElementById('assignStaffForm');
    var customRangeCheckbox = document.getElementById('id_custom_range');
    var customRangeFields = document.getElementById('customRangeFields');

    var editAssignmentModalEl = document.getElementById('editAssignmentModal');
    var editAssignmentForm = document.getElementById('editAssignmentForm');
    var editAssignmentStaffName = document.getElementById('editAssignmentStaffName');

    var removeAssignmentModalEl = document.getElementById('removeAssignmentModal');
    var removeAssignmentForm = document.getElementById('removeAssignmentForm');
    var removeAssignmentName = document.getElementById('removeAssignmentName');

    if (customRangeCheckbox && customRangeFields) {
        customRangeCheckbox.addEventListener('change', function () {
            customRangeFields.classList.toggle('d-none', !customRangeCheckbox.checked);
        });
    }

    function renderAssignedStaff(assignments) {
        if (!assignedStaffListEl) return;
        assignedStaffListEl.innerHTML = '';

        if (!assignments.length) {
            assignedStaffListEl.appendChild(assignedEmptyMsg);
            return;
        }

        assignments.forEach(function (a) {
            var row = document.createElement('div');
            row.className = 'shiftassign-row';
            row.innerHTML =
                '<span class="shiftassign-row__avatar"><img src="' + a.avatar_url + '" alt=""></span>' +
                '<span class="shiftassign-row__info"><strong>' + a.full_name + '</strong><small>' + (a.role || '') + '</small></span>' +
                '<span class="shiftassign-row__range">' + a.start_date + ' \u2192 ' + a.end_date + (a.room ? ' \u00b7 ' + a.room : '') + '</span>' +
                '<span class="shiftassign-row__actions">' +
                    '<button type="button" class="sched-row-btn sched-row-btn--edit" data-assignment-edit="' + a.id + '" data-staff-name="' + a.full_name + '" data-start="' + a.start_date + '" data-end="' + a.end_date + '" title="Edit dates"><i data-lucide="calendar-clock"></i></button>' +
                    '<button type="button" class="sched-row-btn sched-row-btn--delete" data-assignment-remove="' + a.id + '" data-staff-name="' + a.full_name + '" title="Remove"><i data-lucide="trash-2"></i></button>' +
                '</span>';
            assignedStaffListEl.appendChild(row);
        });

        if (window.lucide) lucide.createIcons();
    }

    function renderAvailableStaff(staffList, shiftInfo) {
        if (!assignStaffListEl) return;
        assignStaffListEl.innerHTML = '';

        if (!staffList.length) {
            var scopeParts = [];
            if (shiftInfo && shiftInfo.hospital) scopeParts.push(shiftInfo.hospital);
            if (shiftInfo && shiftInfo.department) scopeParts.push(shiftInfo.department);
            var scopeText = scopeParts.length ? (' for ' + scopeParts.join(' \u2014 ')) : '';
            assignStaffListEl.innerHTML = '<p class="text-muted small mb-0 p-2">All staff' + scopeText + ' are already assigned.</p>';
            return;
        }

        staffList.forEach(function (s) {
            var label = document.createElement('label');
            label.className = 'sched-multiselect__item';
            label.setAttribute('data-search', s.full_name.toLowerCase());

            var checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.name = 'medical_staff';
            checkbox.value = s.id;

            var avatar = document.createElement('span');
            avatar.className = 'sched-multiselect__avatar';
            avatar.innerHTML = '<img src="' + s.avatar_url + '" alt="">';

            var info = document.createElement('span');
            info.className = 'sched-multiselect__info';
            info.innerHTML = '<strong>' + s.full_name + '</strong><small>' + (s.role || '') + '</small>';

            var roomWrap = document.createElement('span');
            roomWrap.className = 'sched-multiselect__room';
            roomWrap.innerHTML =
                '<div class="med-custom-select med-custom-select--compact" id="roomCustomSelect_' + s.id + '">' +
                    '<button type="button" class="med-custom-select__trigger" id="roomTrigger_' + s.id + '" disabled aria-label="Room for ' + s.full_name + '">' +
                        '<span class="med-custom-select__label" id="roomLabel_' + s.id + '">No room</span>' +
                        '<i data-lucide="chevron-down" class="med-custom-select__chevron"></i>' +
                    '</button>' +
                    '<div class="med-custom-select__panel med-custom-select__panel--compact" id="roomPanel_' + s.id + '" hidden>' +
                        '<ul class="med-custom-select__list" id="roomList_' + s.id + '"></ul>' +
                    '</div>' +
                '</div>' +
                '<select class="med-visually-hidden sched-multiselect__room-select" id="roomNative_' + s.id + '" name="room_' + s.id + '"><option value="">No room</option></select>';

            label.appendChild(checkbox);
            label.appendChild(avatar);
            label.appendChild(info);
            label.appendChild(roomWrap);
            assignStaffListEl.appendChild(label);

            var nativeSel = roomWrap.querySelector('#roomNative_' + s.id);
            buildRoomOptions(nativeSel);

            var roomInst = medInitCustomSelect({
                wrapperId: 'roomCustomSelect_' + s.id,
                triggerId: 'roomTrigger_' + s.id,
                panelId: 'roomPanel_' + s.id,
                listId: 'roomList_' + s.id,
                labelId: 'roomLabel_' + s.id,
                nativeId: 'roomNative_' + s.id,
                placeholder: 'No room',
                emptyHint: 'No rooms allocated to this hospital yet'
            });

            var trigger = roomWrap.querySelector('#roomTrigger_' + s.id);
            checkbox.addEventListener('change', function () {
                if (trigger) trigger.disabled = !checkbox.checked;
                if (!checkbox.checked) {
                    nativeSel.value = '';
                    if (roomInst) roomInst.refresh();
                }
            });
        });

        if (window.lucide) lucide.createIcons();
    }

    var availableRoomsCache = [];

    function buildRoomOptions(selectEl) {
        selectEl.innerHTML = '<option value="">No room</option>';
        availableRoomsCache.forEach(function (r) {
            var opt = document.createElement('option');
            opt.value = r.id;
            opt.textContent = r.name;
            selectEl.appendChild(opt);
        });
    }

    function updateAssignSelectedCount() {
        if (!assignStaffListEl || !assignSelectedCountEl) return;
        assignSelectedCountEl.textContent = assignStaffListEl.querySelectorAll('input[type="checkbox"]:checked').length;
    }

    function openAssignModal(shiftId) {
        if (!config.assignmentsUrlTemplate) return;
        var url = config.assignmentsUrlTemplate.replace('__ID__', shiftId);

        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (assignModalShiftLabel) {
                    var hospitalPart = data.shift.hospital ? (data.shift.hospital + ' \u2014 ') : '';
                    assignModalShiftLabel.textContent = hospitalPart + data.shift.label + ' \u2014 ' + data.shift.department + ' (' + data.shift.start_date + ' to ' + data.shift.end_date + ')';
                }
                renderAssignedStaff(data.assignments);
                availableRoomsCache = data.available_rooms || [];
                renderAvailableStaff(data.available_staff, data.shift);
                updateAssignSelectedCount();
                clearAssignFormErrors();

                if (customRangeCheckbox) customRangeCheckbox.checked = false;
                if (customRangeFields) customRangeFields.classList.add('d-none');
                var startEl = document.getElementById('id_assignment_start_date');
                var endEl = document.getElementById('id_assignment_end_date');
                if (startEl) startEl.value = data.shift.start_date;
                if (endEl) endEl.value = data.shift.end_date;

                if (config.assignCreateUrlTemplate) {
                    assignStaffForm.action = config.assignCreateUrlTemplate.replace('__ID__', shiftId);
                }

                openBsModal(assignModalEl);
                if (window.lucide) lucide.createIcons();
            })
            .catch(function () {
                console.error('Could not load shift assignments.');
            });
    }

    document.querySelectorAll('.sched-row-btn--assign[data-shift-id]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            openAssignModal(btn.getAttribute('data-shift-id'));
        });
    });

    if (assignStaffSearch && assignStaffListEl) {
        assignStaffSearch.addEventListener('input', function () {
            var term = assignStaffSearch.value.trim().toLowerCase();
            assignStaffListEl.querySelectorAll('.sched-multiselect__item').forEach(function (item) {
                var haystack = item.getAttribute('data-search') || '';
                item.style.display = haystack.indexOf(term) !== -1 ? '' : 'none';
            });
        });
    }
    if (assignStaffListEl) assignStaffListEl.addEventListener('change', function (e) {
        updateAssignSelectedCount();
        if (e.target && e.target.matches('input[type="checkbox"], select.sched-multiselect__room-select')) {
            clearAssignFormErrors();
        }
    });

    var assignFormErrorBanner = document.getElementById('assignFormErrorBanner');
    var assignFormErrorList = document.getElementById('assignFormErrorList');

    function clearAssignFormErrors() {
        if (assignFormErrorBanner) assignFormErrorBanner.classList.add('d-none');
        if (assignFormErrorList) assignFormErrorList.innerHTML = '';
        if (assignStaffListEl) {
            assignStaffListEl.querySelectorAll('.sched-multiselect__room-select.is-invalid').forEach(function (el) {
                el.classList.remove('is-invalid');
            });
            assignStaffListEl.querySelectorAll('.med-custom-select.is-invalid').forEach(function (el) {
                el.classList.remove('is-invalid');
            });
        }
    }

    if (assignStaffForm) {
        assignStaffForm.addEventListener('submit', function (e) {
            clearAssignFormErrors();
            var missingNames = [];
            var missingSelects = [];

            if (assignStaffListEl) {
                assignStaffListEl.querySelectorAll('.sched-multiselect__item').forEach(function (row) {
                    var checkbox = row.querySelector('input[type="checkbox"]');
                    var roomSelect = row.querySelector('.sched-multiselect__room-select');
                    if (checkbox && checkbox.checked && roomSelect && !roomSelect.value) {
                        var nameEl = row.querySelector('.sched-multiselect__info strong');
                        missingNames.push(nameEl ? nameEl.textContent : 'Selected staff');
                        missingSelects.push(roomSelect);
                    }
                });
            }

            if (missingNames.length) {
                e.preventDefault();
                missingSelects.forEach(function (sel) {
                    sel.classList.add('is-invalid');
                    var wrapper = sel.closest('.sched-multiselect__room');
                    var customSelect = wrapper ? wrapper.querySelector('.med-custom-select') : null;
                    if (customSelect) customSelect.classList.add('is-invalid');
                });
                if (assignFormErrorList && assignFormErrorBanner) {
                    assignFormErrorList.innerHTML = '<li>Select a room for: ' + missingNames.join(', ') + '.</li>';
                    assignFormErrorBanner.classList.remove('d-none');
                    assignFormErrorBanner.scrollIntoView({ block: 'nearest' });
                }
            }
        });
    }

    if (assignedStaffListEl) {
        assignedStaffListEl.addEventListener('click', function (e) {
            var editBtn = e.target.closest('[data-assignment-edit]');
            var removeBtn = e.target.closest('[data-assignment-remove]');

            if (editBtn) {
                var assignmentId = editBtn.getAttribute('data-assignment-edit');
                if (editAssignmentStaffName) editAssignmentStaffName.textContent = editBtn.getAttribute('data-staff-name');
                var startInput = document.getElementById('id_edit_start_date');
                var endInput = document.getElementById('id_edit_end_date');
                if (startInput) startInput.value = editBtn.getAttribute('data-start');
                if (endInput) endInput.value = editBtn.getAttribute('data-end');
                if (config.assignmentEditUrlTemplate && editAssignmentForm) {
                    editAssignmentForm.action = config.assignmentEditUrlTemplate.replace('__ID__', assignmentId);
                }
                hideBsModal(assignModalEl);
                openBsModal(editAssignmentModalEl);
            }

            if (removeBtn) {
                var removeId = removeBtn.getAttribute('data-assignment-remove');
                if (removeAssignmentName) removeAssignmentName.textContent = removeBtn.getAttribute('data-staff-name');
                if (config.assignmentDeleteUrlTemplate && removeAssignmentForm) {
                    removeAssignmentForm.action = config.assignmentDeleteUrlTemplate.replace('__ID__', removeId);
                }
                hideBsModal(assignModalEl);
                openBsModal(removeAssignmentModalEl);
            }
        });
    }

    setRecurrence('DAILY');
})();