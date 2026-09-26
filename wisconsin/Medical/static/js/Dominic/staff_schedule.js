(function () {
    'use strict';

    var config = window.schedConfig || {};

    function openBsModal(el) {
        if (!el || !window.bootstrap) return;
        bootstrap.Modal.getOrCreateInstance(el).show();
    }

    function hideBsModal(el) {
        if (!el || !window.bootstrap) return;
        var instance = bootstrap.Modal.getInstance(el);
        if (instance) instance.hide();
    }

    function setScheduleType(scope, type) {
        var toggleEl = scope === 'bulk' ? document.getElementById('bulkSchedTypeToggle') : document.getElementById('schedTypeToggle');
        var hiddenEl = scope === 'bulk' ? document.getElementById('id_bulk_schedule_type_hidden') : document.getElementById('id_schedule_type');
        var dayField = scope === 'bulk' ? document.getElementById('bulkDayOfWeekField') : document.getElementById('dayOfWeekField');
        var dateField = scope === 'bulk' ? document.getElementById('bulkSpecificDateField') : document.getElementById('specificDateField');

        if (hiddenEl) hiddenEl.value = type;
        if (toggleEl) {
            toggleEl.querySelectorAll('.sched-type-btn').forEach(function (btn) {
                btn.classList.toggle('is-active', btn.getAttribute('data-type') === type);
            });
        }
        if (dayField && dateField) {
            if (type === 'RECURRING') {
                dayField.classList.remove('d-none');
                dateField.classList.add('d-none');
            } else {
                dayField.classList.add('d-none');
                dateField.classList.remove('d-none');
            }
        }
    }

    var schedTypeToggle = document.getElementById('schedTypeToggle');
    if (schedTypeToggle) {
        schedTypeToggle.addEventListener('click', function (e) {
            var btn = e.target.closest('.sched-type-btn');
            if (btn) setScheduleType('single', btn.getAttribute('data-type'));
        });
    }

    var bulkTypeToggle = document.getElementById('bulkSchedTypeToggle');
    if (bulkTypeToggle) {
        bulkTypeToggle.addEventListener('click', function (e) {
            var btn = e.target.closest('.sched-type-btn');
            if (btn) setScheduleType('bulk', btn.getAttribute('data-type'));
        });
    }

    var advancedToggle = document.getElementById('advancedToggle');
    var advancedPanel = document.getElementById('advancedPanel');
    if (advancedToggle && advancedPanel) {
        advancedToggle.addEventListener('click', function () {
            advancedPanel.classList.toggle('d-none');
            advancedToggle.classList.toggle('is-open');
        });
    }

    var singleModalEl = document.getElementById('singleAssignModal');
    var singleForm = document.getElementById('singleAssignForm');
    var scheduleIdInput = document.getElementById('id_schedule_id');
    var modalTitleEl = document.getElementById('singleAssignModalTitle');
    var submitLabelEl = document.getElementById('singleAssignSubmitLabel');
    var deleteFromEditBtn = document.getElementById('deleteFromEditBtn');

    function resetSingleForm() {
        if (!singleForm) return;
        singleForm.reset();
        if (scheduleIdInput) scheduleIdInput.value = '';
        singleForm.action = config.createUrl || singleForm.action;
        if (modalTitleEl) modalTitleEl.textContent = 'Assign Shift';
        if (submitLabelEl) submitLabelEl.textContent = 'Assign Shift';
        if (deleteFromEditBtn) deleteFromEditBtn.classList.add('d-none');
        if (advancedPanel) advancedPanel.classList.add('d-none');
        if (advancedToggle) advancedToggle.classList.remove('is-open');
        setScheduleType('single', 'RECURRING');
    }

    function fillSingleFormFromData(data) {
        var setVal = function (id, val) {
            var el = document.getElementById(id);
            if (el) el.value = val != null ? val : '';
        };
        setVal('id_medical_staff', data.medical_staff);
        setVal('id_department', data.department);
        setVal('id_day_of_week', data.day_of_week);
        setVal('id_specific_date', data.specific_date);
        setVal('id_effective_from', data.effective_from);
        setVal('id_effective_until', data.effective_until);
        setVal('id_shift', data.shift);
        setVal('id_start_time', data.start_time);
        setVal('id_end_time', data.end_time);
        setVal('id_room_number', data.room_number);
        var overrideEl = document.getElementById('id_is_override');
        if (overrideEl) overrideEl.checked = !!data.is_override;
        setScheduleType('single', data.schedule_type || 'RECURRING');
    }

    var openSingleAssignBtn = document.getElementById('openSingleAssignBtn');
    if (openSingleAssignBtn) {
        openSingleAssignBtn.addEventListener('click', function () {
            resetSingleForm();
            openBsModal(singleModalEl);
        });
    }

    document.querySelectorAll('[data-add-date]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            resetSingleForm();
            setScheduleType('single', 'ONE_TIME');
            var dateEl = document.getElementById('id_specific_date');
            if (dateEl) dateEl.value = btn.getAttribute('data-add-date');
            openBsModal(singleModalEl);
        });
    });

    function loadScheduleForEdit(scheduleId) {
        if (!config.editUrlTemplate) return;
        var url = config.editUrlTemplate.replace('__ID__', scheduleId);
        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                resetSingleForm();
                fillSingleFormFromData(data);
                if (scheduleIdInput) scheduleIdInput.value = scheduleId;
                singleForm.action = url;
                if (modalTitleEl) modalTitleEl.textContent = 'Edit Shift';
                if (submitLabelEl) submitLabelEl.textContent = 'Save Changes';
                if (deleteFromEditBtn) {
                    deleteFromEditBtn.classList.remove('d-none');
                    deleteFromEditBtn.setAttribute('data-schedule-id', scheduleId);
                }
                openBsModal(singleModalEl);
                if (window.lucide) lucide.createIcons();
            })
            .catch(function () {
                console.error('Could not load schedule details.');
            });
    }

    document.querySelectorAll('.sched-chip[data-schedule-id], .sched-row-btn--edit[data-schedule-id]').forEach(function (el) {
        el.addEventListener('click', function () {
            loadScheduleForEdit(el.getAttribute('data-schedule-id'));
        });
    });

    if (singleModalEl) {
        singleModalEl.addEventListener('hidden.bs.modal', resetSingleForm);
    }

    var deleteModalEl = document.getElementById('deleteScheduleModal');
    var deleteForm = document.getElementById('deleteScheduleForm');
    var deleteNameEl = document.getElementById('deleteScheduleName');

    function openDeleteModal(scheduleId, staffName) {
        if (!config.deleteUrlTemplate || !deleteForm) return;
        deleteForm.action = config.deleteUrlTemplate.replace('__ID__', scheduleId);
        if (deleteNameEl) deleteNameEl.textContent = staffName || 'this staff member';
        hideBsModal(singleModalEl);
        openBsModal(deleteModalEl);
    }

    document.querySelectorAll('.sched-row-btn--delete').forEach(function (btn) {
        btn.addEventListener('click', function () {
            openDeleteModal(btn.getAttribute('data-schedule-id'), btn.getAttribute('data-schedule-name'));
        });
    });

    if (deleteFromEditBtn) {
        deleteFromEditBtn.addEventListener('click', function () {
            var staffSelect = document.getElementById('id_medical_staff');
            var label = staffSelect && staffSelect.options[staffSelect.selectedIndex] ? staffSelect.options[staffSelect.selectedIndex].text : '';
            openDeleteModal(deleteFromEditBtn.getAttribute('data-schedule-id'), label);
        });
    }

    var bulkSearch = document.getElementById('bulkStaffSearch');
    var bulkList = document.getElementById('bulkStaffList');
    var bulkCountEl = document.getElementById('bulkSelectedCount');

    function updateBulkCount() {
        if (!bulkList || !bulkCountEl) return;
        bulkCountEl.textContent = bulkList.querySelectorAll('input[type="checkbox"]:checked').length;
    }

    if (bulkSearch && bulkList) {
        bulkSearch.addEventListener('input', function () {
            var term = bulkSearch.value.trim().toLowerCase();
            bulkList.querySelectorAll('.sched-multiselect__item').forEach(function (item) {
                var haystack = item.getAttribute('data-search') || '';
                item.style.display = haystack.indexOf(term) !== -1 ? '' : 'none';
            });
        });
    }

    if (bulkList) bulkList.addEventListener('change', updateBulkCount);

    setScheduleType('single', 'RECURRING');
    setScheduleType('bulk', 'RECURRING');

    (function calendarDayPopover() {
        var openPopover = null;
        var openTrigger = null;
        var originalHome = new WeakMap();

        function restoreHome(popover) {
            var home = originalHome.get(popover);
            if (!home) return;
            if (home.nextSibling && home.nextSibling.parentNode === home.parent) {
                home.parent.insertBefore(popover, home.nextSibling);
            } else {
                home.parent.appendChild(popover);
            }
        }

        function closePopover() {
            if (!openPopover) return;
            openPopover.hidden = true;
            openPopover.classList.remove('is-open', 'sched-day-popover--sheet');
            openPopover.style.left = '';
            openPopover.style.top = '';
            openPopover.style.right = '';
            openPopover.style.bottom = '';
            restoreHome(openPopover);
            if (openTrigger) openTrigger.setAttribute('aria-expanded', 'false');
            document.removeEventListener('keydown', onKeydown, true);
            document.removeEventListener('click', onOutsideClick, true);
            window.removeEventListener('resize', closePopover);
            window.removeEventListener('scroll', onWindowScroll, true);
            var trigger = openTrigger;
            openPopover = null;
            openTrigger = null;
            if (trigger) trigger.focus();
        }

        function onWindowScroll(e) {
            if (openPopover && e.target && openPopover.contains(e.target)) return;
            closePopover();
        }

        function onKeydown(e) {
            if (e.key === 'Escape') closePopover();
        }

        function onOutsideClick(e) {
            if (!openPopover) return;
            if (openPopover.contains(e.target) || (openTrigger && openTrigger.contains(e.target))) return;
            closePopover();
        }

        function positionPopover(trigger, popover) {
            var isMobile = window.innerWidth <= 575.98;
            if (isMobile) {
                popover.classList.add('sched-day-popover--sheet');
                return;
            }
            popover.classList.remove('sched-day-popover--sheet');

            var rect = trigger.getBoundingClientRect();
            var popRect = popover.getBoundingClientRect();
            var margin = 10;

            var left = rect.left;
            if (left + popRect.width + margin > window.innerWidth) {
                left = window.innerWidth - popRect.width - margin;
            }
            if (left < margin) left = margin;

            var top = rect.bottom + 6;
            if (top + popRect.height + margin > window.innerHeight) {
                top = rect.top - popRect.height - 6;
                if (top < margin) top = margin;
            }

            popover.style.left = left + 'px';
            popover.style.top = top + 'px';
        }

        function openPopoverFor(trigger) {
            var day = trigger.closest('.sched-day');
            var popover = day ? day.querySelector('[data-day-popover]') : null;
            if (!popover) return;

            if (openPopover === popover) {
                closePopover();
                return;
            }
            closePopover();

            if (!originalHome.has(popover)) {
                originalHome.set(popover, { parent: popover.parentNode, nextSibling: popover.nextSibling });
            }
            
            document.body.appendChild(popover);

            popover.hidden = false;
            popover.classList.add('is-open');
            trigger.setAttribute('aria-expanded', 'true');
            openPopover = popover;
            openTrigger = trigger;

            positionPopover(trigger, popover);

            document.addEventListener('keydown', onKeydown, true);
            document.addEventListener('click', onOutsideClick, true);
            window.addEventListener('resize', closePopover);
            window.addEventListener('scroll', onWindowScroll, true);

            var closeBtn = popover.querySelector('[data-day-popover-close]');
            if (closeBtn) closeBtn.focus();
        }

        document.querySelectorAll('[data-day-toggle]').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.stopPropagation();
                openPopoverFor(btn);
            });
        });

        document.querySelectorAll('[data-day-popover-close]').forEach(function (btn) {
            btn.addEventListener('click', closePopover);
        });
    })();

    (function buildLegend() {
        var legendEl = document.getElementById('schedLegend');
        if (!legendEl) return;

        var seen = {};
        var items = [];
        document.querySelectorAll('[data-legend-label][data-legend-color]').forEach(function (row) {
            var color = row.getAttribute('data-legend-color');
            var label = row.getAttribute('data-legend-label');
            var key = color + '|' + label;
            if (!color || !label || seen[key]) return;
            seen[key] = true;
            items.push({ color: color, label: label });
        });

        if (!items.length) {
            legendEl.remove();
            return;
        }

        legendEl.setAttribute('aria-hidden', 'false');
        legendEl.innerHTML = items.map(function (item) {
            return '<span class="sched-legend__item">' +
                '<span class="sched-legend__dot sched-chip__dot--' + item.color + '"></span>' +
                item.label +
                '</span>';
        }).join('');
    })();
})();