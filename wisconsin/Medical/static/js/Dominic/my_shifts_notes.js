(function () {
    'use strict';

    var config = window.myShiftsConfig || {};

    function getCsrfToken() {
        var el = document.querySelector('#noteCsrfForm [name=csrfmiddlewaretoken]');
        return el ? el.value : '';
    }

    function renderIcons() {
        if (window.lucide && typeof window.lucide.createIcons === 'function') {
            window.lucide.createIcons();
        }
    }

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

    function closeNotePopover() {
        if (!openPopover) return;
        openPopover.hidden = true;
        openPopover.classList.remove('is-open', 'sched-day-popover--sheet');
        openPopover.style.left = '';
        openPopover.style.top = '';
        restoreHome(openPopover);
        if (openTrigger) openTrigger.setAttribute('aria-expanded', 'false');
        document.removeEventListener('keydown', onKeydown, true);
        document.removeEventListener('click', onOutsideClick, true);
        window.removeEventListener('resize', closeNotePopover);
        var trigger = openTrigger;
        openPopover = null;
        openTrigger = null;
        if (trigger) trigger.focus();
    }

    function onKeydown(e) {
        if (e.key === 'Escape') closeNotePopover();
    }

    function onOutsideClick(e) {
        if (!openPopover) return;
        if (openPopover.contains(e.target) || (openTrigger && openTrigger.contains(e.target))) return;
        if (e.target.closest('[data-reminder-dropdown], [data-reminder-menu], .sched-reminder-dropdown-portal')) return;
        closeNotePopover();
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

    function openNotePopover(trigger) {
        var day = trigger.closest('.sched-day');
        var popover = day ? day.querySelector('[data-note-popover]') : null;
        if (!popover) return;

        if (openPopover === popover) {
            closeNotePopover();
            return;
        }
        closeNotePopover();

        if (!originalHome.has(popover)) {
            originalHome.set(popover, {
                parent: popover.parentNode,
                nextSibling: popover.nextSibling,
                day: popover.closest('.sched-day'),
            });
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
        window.addEventListener('resize', closeNotePopover);

        var textarea = popover.querySelector('.sched-note-textarea');
        if (textarea) textarea.focus();
    }

    function getOwningDay(popover) {
        var home = originalHome.get(popover);
        if (home && home.day) return home.day;
        return popover.closest('.sched-day');
    }

    function bindNoteToggle(el) {
        el.addEventListener('click', function (e) {
            e.stopPropagation();
            openNotePopover(el);
        });
    }

    document.querySelectorAll('[data-note-toggle]').forEach(bindNoteToggle);

    document.querySelectorAll('[data-note-popover-close]').forEach(function (btn) {
        if (btn.closest('[data-note-popover]')) {
            btn.addEventListener('click', closeNotePopover);
        }
    });

    function bindReminderToggle(checkbox) {
        checkbox.addEventListener('change', function () {
            var fields = checkbox.closest('form').querySelector('[data-reminder-fields]');
            if (!fields) return;
            fields.hidden = !checkbox.checked;
            if (checkbox.checked) {
                var eventTimeInput = fields.querySelector('[data-event-time]');
                if (eventTimeInput && !eventTimeInput.value) eventTimeInput.value = '09:00';
            }
        });
    }
    document.querySelectorAll('[data-reminder-toggle]').forEach(bindReminderToggle);

    function truncateLabel(text) {
        var trimmed = (text || '').trim();
        return trimmed.length > 26 ? trimmed.slice(0, 26) + '…' : trimmed;
    }

    function buildNoteBtn(dateStr) {
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'sched-day__note-btn';
        btn.setAttribute('data-note-toggle', '');
        btn.setAttribute('data-date', dateStr);
        btn.setAttribute('aria-haspopup', 'dialog');
        btn.setAttribute('aria-expanded', 'false');
        btn.setAttribute('aria-label', 'Add note for ' + dateStr);
        btn.innerHTML = '<i data-lucide="plus"></i>';
        bindNoteToggle(btn);
        return btn;
    }

    function buildNoteChip(dateStr, noteText, hasReminder) {
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'sched-day__note-chip';
        btn.setAttribute('data-note-toggle', '');
        btn.setAttribute('data-date', dateStr);
        btn.setAttribute('aria-haspopup', 'dialog');
        btn.setAttribute('aria-expanded', 'false');
        btn.setAttribute('aria-label', 'Edit note for ' + dateStr);

        var iconSpan = document.createElement('span');
        iconSpan.className = 'sched-day__note-chip-icon';
        iconSpan.innerHTML = '<i data-lucide="sticky-note"></i>';

        var labelSpan = document.createElement('span');
        labelSpan.className = 'sched-day__note-chip-label';
        labelSpan.textContent = truncateLabel(noteText);

        btn.appendChild(iconSpan);
        btn.appendChild(labelSpan);

        if (hasReminder) {
            var bellIcon = document.createElement('i');
            bellIcon.setAttribute('data-lucide', 'bell');
            bellIcon.className = 'sched-day__note-chip-bell';
            btn.appendChild(bellIcon);
        }

        bindNoteToggle(btn);
        return btn;
    }

    function ensureEmptyState(day) {
        var body = day.querySelector('.sched-day__body');
        var hasStack = !!body.querySelector('.sched-day__stack');
        var hasNote = !!body.querySelector('.sched-day__note-chip');
        var emptyEl = body.querySelector('.sched-day__empty');
        if (!hasStack && !hasNote) {
            if (!emptyEl) {
                emptyEl = document.createElement('span');
                emptyEl.className = 'sched-day__empty';
                emptyEl.textContent = 'No shifts';
                body.appendChild(emptyEl);
            }
        } else if (emptyEl) {
            emptyEl.remove();
        }
    }

    function handleSave(e) {
        e.preventDefault();
        var form = e.target;
        if (!config.saveNoteUrl) return;

        var noteText = form.querySelector('.sched-note-textarea').value.trim();
        var reminderChecked = form.querySelector('[data-reminder-toggle]').checked;
        var eventTime = form.querySelector('[data-event-time]').value;
        var offsetMinutes = form.querySelector('[data-reminder-offset]').value;

        if (reminderChecked && !eventTime) {
            alert('Set an event time to attach a reminder, or turn the reminder off.');
            return;
        }

        var body = new URLSearchParams();
        body.set('date', form.getAttribute('data-date'));
        body.set('note_text', noteText);
        body.set('event_time', reminderChecked ? eventTime : '');
        body.set('reminder_offset_minutes', reminderChecked ? offsetMinutes : '');

        var saveBtn = form.querySelector('.sched-note-btn--save');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.textContent = 'Saving…';
        }

        fetch(config.saveNoteUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: body.toString(),
        })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (!data.success) {
                    alert(data.error || 'Could not save note.');
                    return;
                }

                var dateStr = form.getAttribute('data-date');
                var popover = form.closest('[data-note-popover]');
                var day = getOwningDay(popover);
                if (!day) {
                    closeNotePopover();
                    return;
                }
                var head = day.querySelector('.sched-day__head');
                var slot = day.querySelector('.sched-day__note-slot');

                var plusBtn = head.querySelector('.sched-day__note-btn');
                if (plusBtn) plusBtn.remove();

                slot.innerHTML = '';
                slot.appendChild(buildNoteChip(dateStr, data.note.note_text, !!data.note.reminder_offset_minutes));
                ensureEmptyState(day);
                renderIcons();

                form.setAttribute('data-note-id', data.note.id);

                var actions = form.querySelector('.sched-note-actions');
                if (actions && !actions.querySelector('[data-note-delete]')) {
                    var delBtn = document.createElement('button');
                    delBtn.type = 'button';
                    delBtn.className = 'sched-note-btn sched-note-btn--delete';
                    delBtn.setAttribute('data-note-delete', '');
                    delBtn.setAttribute('data-note-id', data.note.id);
                    delBtn.innerHTML = '<i data-lucide="trash-2"></i> Delete';
                    actions.insertBefore(delBtn, actions.firstChild);
                    bindDeleteButton(delBtn);
                    renderIcons();
                } else if (actions) {
                    var existingDel = actions.querySelector('[data-note-delete]');
                    if (existingDel) existingDel.setAttribute('data-note-id', data.note.id);
                }

                closeNotePopover();
            })
            .catch(function () {
                alert('Could not save note. Please try again.');
            })
            .finally(function () {
                if (saveBtn) {
                    saveBtn.disabled = false;
                    saveBtn.textContent = 'Save';
                }
            });
    }

    document.querySelectorAll('[data-note-form]').forEach(function (form) {
        form.addEventListener('submit', handleSave);
    });

    function resetNoteForm(form) {
        form.querySelector('.sched-note-textarea').value = '';
        var checkbox = form.querySelector('[data-reminder-toggle]');
        checkbox.checked = false;
        var fields = form.querySelector('[data-reminder-fields]');
        if (fields) fields.hidden = true;
        var eventTimeInput = form.querySelector('[data-event-time]');
        if (eventTimeInput) eventTimeInput.value = '';
        var offsetSelect = form.querySelector('[data-reminder-offset]');
        if (offsetSelect) offsetSelect.value = '10';
        form.removeAttribute('data-note-id');
    }

    function bindDeleteButton(btn) {
        btn.addEventListener('click', function () {
            var noteId = btn.getAttribute('data-note-id');
            if (!noteId || !config.deleteNoteUrlTemplate) return;
            if (!window.confirm('Delete this note?')) return;

            var url = config.deleteNoteUrlTemplate.replace('__ID__', noteId);
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
                .then(function (res) { return res.json(); })
                .then(function (data) {
                    if (!data.success) return;

                    var form = btn.closest('form');
                    var dateStr = form.getAttribute('data-date');
                    var popover = form.closest('[data-note-popover]');
                    var day = getOwningDay(popover);
                    if (!day) {
                        closeNotePopover();
                        return;
                    }
                    var head = day.querySelector('.sched-day__head');
                    var slot = day.querySelector('.sched-day__note-slot');

                    slot.innerHTML = '';
                    if (!head.querySelector('.sched-day__note-btn')) {
                        head.appendChild(buildNoteBtn(dateStr));
                        renderIcons();
                    }
                    ensureEmptyState(day);

                    resetNoteForm(form);
                    btn.remove();
                    closeNotePopover();
                })
                .catch(function () {
                    alert('Could not delete note. Please try again.');
                });
        });
    }

    document.querySelectorAll('[data-note-delete]').forEach(bindDeleteButton);

    function showToast(message) {
        var toast = document.createElement('div');
        toast.className = 'sched-toast';
        toast.textContent = message;
        document.body.appendChild(toast);
        requestAnimationFrame(function () { toast.classList.add('is-visible'); });
        setTimeout(function () {
            toast.classList.remove('is-visible');
            setTimeout(function () { toast.remove(); }, 250);
        }, 5000);
    }

    function pollReminders() {
        if (!config.dueRemindersUrl) return;
        fetch(config.dueRemindersUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                var fired = data.notifications || [];
                fired.forEach(function (n) {
                    showToast(n.message);
                });
                if (fired.length > 0 && typeof window.refreshNotifBell === 'function') {
                    window.refreshNotifBell();
                }
            })
            .catch(function () {});
    }

    if (config.dueRemindersUrl) {
        pollReminders();
        setInterval(pollReminders, 60000);
    }
})();