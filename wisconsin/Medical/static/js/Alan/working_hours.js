

        (function() {
            'use strict';

            // ─── CSRF TOKEN HELPER ───
            /**
             * Retrieves the CSRF token from cookies for Django POST requests.
             * Django sets a 'csrftoken' cookie; this function reads it.
             * Required for all state-modifying AJAX calls to prevent CSRF attacks.
             */
            function getCSRFToken() {
                const cookie = document.cookie
                    .split("; ")
                    .find(row => row.startsWith("csrftoken="));
                return cookie ? decodeURIComponent(cookie.split("=")[1]) : "";
            }

            // ─── CONSTANTS ───
            /**
             * DAYS: Array of all weekdays in order (Monday first for calendar display).
             * DAY_FULL / DAY_SHORT: Mapping for display names.
             * DOW_MAP: Maps getDay() return value (0=Sunday) to our day names.
             */
            const DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
            const DAY_FULL = {
                monday: 'Monday',
                tuesday: 'Tuesday',
                wednesday: 'Wednesday',
                thursday: 'Thursday',
                friday: 'Friday',
                saturday: 'Saturday',
                sunday: 'Sunday'
            };
            const DAY_SHORT = {
                monday: 'Mon',
                tuesday: 'Tue',
                wednesday: 'Wed',
                thursday: 'Thu',
                friday: 'Fri',
                saturday: 'Sat',
                sunday: 'Sun'
            };
            const DOW_MAP = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];

            // ─── STATE ───
            /**
             * Application state object.
             * - weekly: Base schedule for each day (enabled + opening/closing times).
             *           Used by calendar to determine "normal" hours.
             * - overrides: Date-specific exceptions keyed by 'YYYY-MM-DD'.
             * - selectedDates: Array of date keys for multi-select mode.
             * - viewYear / viewMonth: Current calendar view position.
             * - modalTarget: Date key currently being edited in the modal.
             *
             * NOTE: The weekly UI has been removed, but the data remains for calendar logic.
             */

            const DEFAULT_WEEKLY_SCHEDULE = {
                monday: {
                    enabled: true,
                    opening: "09:00",
                    closing: "18:00"
                },
                tuesday: {
                    enabled: true,
                    opening: "09:00",
                    closing: "18:00"
                },
                wednesday: {
                    enabled: true,
                    opening: "09:00",
                    closing: "18:00"
                },
                thursday: {
                    enabled: true,
                    opening: "09:00",
                    closing: "18:00"
                },
                friday: {
                    enabled: true,
                    opening: "09:00",
                    closing: "18:00"
                },
                saturday: {
                    enabled: true,
                    opening: "09:00",
                    closing: "18:00"
                },
                sunday: {
                    enabled: true,
                    opening: "09:00",
                    closing: "18:00"
                }
            };


            const state = {
                weekly: structuredClone(DEFAULT_WEEKLY_SCHEDULE),
                overrides: {},
                viewYear: new Date().getFullYear(),
                viewMonth: new Date().getMonth(),
                modalTarget: null
            };

            const appContainer = document.getElementById("app");




            // ─────────────────────────────
            // LOAD ACTUAL DB DATA
            // ─────────────────────────────

            const workingHoursElement =
                document.getElementById('hospital-working-hours');

            if (workingHoursElement) {

                try {

                    const parsed =
                        JSON.parse(
                            workingHoursElement.textContent
                        );

                    if (
                        parsed.weekly_schedule &&
                        Object.keys(parsed.weekly_schedule).length
                    ) {
                        state.weekly = {
                            ...structuredClone(DEFAULT_WEEKLY_SCHEDULE),
                            ...parsed.weekly_schedule
                        };
                    }

                    state.overrides = parsed.overrides || {};

                    console.log(
                        '✅ Working hours loaded:',
                        parsed
                    );

                } catch (error) {

                    console.error(
                        '❌ Failed to parse working hours:',
                        error
                    );
                }
            }

            // ─── DOM REFS ───
            /** Shorthand selectors and cached DOM elements. */
            const $ = (s) => document.querySelector(s);
            const $$ = (s) => document.querySelectorAll(s);

            const calendarGrid = $('#calendarGrid');
            const monthLabel = $('#monthLabel');
            const yearGrid = $('#yearGrid');


        let bulkFromPicker;
        let bulkToPicker;

        function initBulkDatePickers() {

            const fromInput = document.getElementById('bulkFrom');
            const toInput = document.getElementById('bulkTo');

            if (!fromInput || !toInput) return;

            bulkFromPicker = flatpickr(fromInput, {
                dateFormat: 'Y-m-d',
                minDate: 'today',
                allowInput: false,

                onChange: function (selectedDates) {

                    if (!selectedDates.length) return;

                    // To date cannot be before From date
                    bulkToPicker.set('minDate', selectedDates[0]);

                    if (
                        bulkToPicker.selectedDates.length &&
                        bulkToPicker.selectedDates[0] < selectedDates[0]
                    ) {
                        bulkToPicker.clear();
                    }
                }
            });

            bulkToPicker = flatpickr(toInput, {
                dateFormat: 'Y-m-d',
                minDate: 'today',
                allowInput: false
            });
        }
            

            // ─── HELPERS ───

            /**
             * fmtDateKey: Converts year, month (0-indexed), day to 'YYYY-MM-DD' string.
             * Used as a unique key for date overrides in state.overrides.
             */
            function fmtDateKey(y, m, d) {
                return `${y}-${String(m+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
            }

            /**
             * parseDateKey: Parses 'YYYY-MM-DD' back into { year, month, day }.
             * Month is returned 0-indexed for Date constructor compatibility.
             */
            function parseDateKey(k) {
                const p = k.split('-').map(Number);
                return { year: p[0], month: p[1] - 1, day: p[2] };
            }

            /** daysInMonth: Returns number of days in a given month/year. */
            function daysInMonth(y, m) { return new Date(y, m + 1, 0).getDate(); }

            /** getDow: Returns day-of-week (0=Sunday) for a given date. */
            function getDow(y, m, d) { return new Date(y, m, d).getDay(); }

            /**
             * getWeekdaySchedule: Returns the weekly schedule object for a given DOW.
             * Used internally by getScheduleForDate to resolve base hours.
             */
            function getWeekdaySchedule(dow) {
                const dayName = DOW_MAP[dow];

                return state.weekly?.[dayName] || {
                    enabled: false,
                    opening: null,
                    closing: null
                };
            }

            /**
             * getScheduleForDate: Resolves the effective schedule for a specific date.
             * Priority: override > weekly schedule. Returns an object with:
             *   - type: 'normal' | 'modified' | 'closed' | 'weekly-off'
             *   - opening / closing: present for 'normal' and 'modified'
             * This is the core function used by rendering and summary calculations.
             */
            function getScheduleForDate(y, m, d) {
                const key = fmtDateKey(y, m, d);
                if (state.overrides[key]) return state.overrides[key];
                const dow = getDow(y, m, d);
                const wk = getWeekdaySchedule(dow);
                if (!wk.enabled) return { type: 'weekly-off' };
                return { type: 'normal', opening: wk.opening, closing: wk.closing };
            }

            /**
             * getStatusForDate: Returns a short status string for a date.
             * Used for styling calendar cells and dots.
             */
            function getStatusForDate(y, m, d) {
                const s = getScheduleForDate(y, m, d);
                if (s.type === 'closed') return 'closed';
                if (s.type === 'modified') return 'modified';
                if (s.type === 'weekly-off') return 'off';
                return 'normal';
            }

            /** isToday: Checks if the given date is today. */
            function isToday(y, m, d) {
                const t = new Date();
                return t.getFullYear() === y && t.getMonth() === m && t.getDate() === d;
            }

            /**
             * isPastDate: Returns true if the given date is before today (midnight comparison).
             * Used to disable editing of past dates.
             */
            function isPastDate(y, m, d) {
                const today = new Date();
                const target = new Date(y, m, d);
                target.setHours(0, 0, 0, 0);
                today.setHours(0, 0, 0, 0);
                return target < today;
            }

            /**
             * getDefaultHoursForDate: Returns the weekly default hours for a date,
             * or null if the day is closed by default.
             */
            function getDefaultHoursForDate(y, m, d) {
                const dow = getDow(y, m, d);
                const wk = getWeekdaySchedule(dow);
                if (wk.enabled) return { opening: wk.opening, closing: wk.closing };
                return null;
            }

            // ─── TOAST ───
            /** Toast notification system with auto-dismiss. */
            let toastTimer;

            function showToast(msg) {
                const el = $('#toast');
                const msgEl = $('#toastMessage');
                msgEl.textContent = msg;
                el.classList.add('show');
                clearTimeout(toastTimer);
                toastTimer = setTimeout(() => el.classList.remove('show'), 2800);
            }

            // ─── RENDER: CALENDAR ───

            /**
             * renderCalendar: Renders the month grid for the current viewYear/viewMonth.
             * - Builds a 7-column grid with day headers.
             * - Each cell shows: day number, status label, status dot, and checkmark if selected.
             * - Today's date gets a special class; past dates are disabled.
             * - Click handlers are attached to each cell for selection or modal opening.
             */
            function renderCalendar() {
                const y = state.viewYear,
                    m = state.viewMonth;
                const firstDow = new Date(y, m, 1).getDay();
                const days = daysInMonth(y, m);
                const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
                    'October', 'November', 'December'
                ];
                monthLabel.textContent = `${monthNames[m]} ${y}`;

                // Offset so Monday is first (if firstDow=0 Sunday, offset=6; else offset=firstDow-1)
                const startOffset = (firstDow === 0) ? 6 : firstDow - 1;
                const totalCells = Math.ceil((startOffset + days) / 7) * 7;

                let html = '';
                // Day-of-week headers (Mon–Sun)
                const headers = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
                headers.forEach(h => {
                    html +=
                        `<div class="day-header"><span class="short-label">${h.substring(0,2)}</span><span class="long-label">${h}</span></div>`;
                });

                // Loop through all cells in the grid
                for (let i = 0; i < totalCells; i++) {
                    let dayNum = i - startOffset + 1;
                    let isOther = dayNum < 1 || dayNum > days;
                    const realDay = isOther ? (dayNum < 1 ? days + dayNum : dayNum - days) : dayNum;
                    const displayDay = isOther ? realDay : dayNum;
                    const isCurrent = !isOther && dayNum >= 1 && dayNum <= days;
                    const dKey = fmtDateKey(y, m, isCurrent ? dayNum : 1);
                    const status = isCurrent ? getStatusForDate(y, m, dayNum) : 'off';
                    const isTodayFlag = isCurrent && isToday(y, m, dayNum);
                    
                    const isPast = isCurrent && isPastDate(y, m, dayNum);

                    // Build status label and dot class based on the resolved status
                    let statusLabel = '',
                        dotClass = 'dot-normal',
                        statusClass = 'normal';
                    if (status === 'closed') {
                        statusLabel = 'Closed';
                        dotClass = 'dot-closed';
                        statusClass = 'closed';
                    } else if (status === 'modified') {
                        const s = getScheduleForDate(y, m, dayNum);
                        statusLabel = s.opening + '–' + s.closing;
                        dotClass = 'dot-modified';
                        statusClass = 'modified';
                    } else if (status === 'off') {
                        statusLabel = 'Off';
                        dotClass = 'dot-off';
                        statusClass = 'weekly-off';
                    } else {
                        const s = getScheduleForDate(y, m, dayNum);
                        statusLabel = (isCurrent && s.opening) ? s.opening + '–' + s.closing : '';
                        dotClass = 'dot-normal';
                        statusClass = 'normal';
                    }
                    const cellClass =
    `calendar-cell ${isCurrent ? '' : 'other-month'} ${isTodayFlag ? 'today' : ''} ${isPast ? 'past-date' : ''}`;
                    const clickAttr = isCurrent ? `data-date="${dKey}"` : '';

                    html += `
                            <div class="${cellClass}" ${clickAttr}>
                                <span class="date-num">${displayDay}</span>
                                ${isCurrent ? `<span class="date-status ${statusClass}">${statusLabel}</span>` : `<span class="date-status" style="font-size:0.3rem;">&nbsp;</span>`}
                                <span class="date-dot ${dotClass}"></span>
                            </div>
                        `;
                }
                calendarGrid.innerHTML = html;

                // Attach click handlers to each date cell

                calendarGrid.onclick = function (e) {

                const cell = e.target.closest('.calendar-cell[data-date]');

                if (!cell) return;

                const dateKey = cell.dataset.date;

                if (!dateKey) return;

                console.log('📅 Calendar date clicked:', dateKey);

                const p = parseDateKey(dateKey);

                if (isPastDate(p.year, p.month, p.day)) {
                    showToast('Cannot edit past dates');
                    return;
                }

                openDateModal(dateKey);
            };


                updateSummary();

            }

            // ─── SUMMARY ───

            /**
             * updateSummary: Calculates and updates the four summary counters
             * (Open, Modified, Closed, Weekly Off) for the current month.
             * Iterates through all days of the month and counts by schedule type.
             */
            function updateSummary() {
                const y = state.viewYear,
                    m = state.viewMonth;
                const days = daysInMonth(y, m);
                let open = 0,
                    modified = 0,
                    closed = 0,
                    off = 0;
                for (let d = 1; d <= days; d++) {
                    const s = getScheduleForDate(y, m, d);
                    if (s.type === 'closed') closed++;
                    else if (s.type === 'modified') modified++;
                    else if (s.type === 'weekly-off') off++;
                    else open++;
                }
                document.getElementById('sumOpen').textContent = open;
                document.getElementById('sumModified').textContent = modified;
                document.getElementById('sumClosed').textContent = closed;
                document.getElementById('sumOff').textContent = off;
            }


            // ─── YEAR OVERVIEW ───

            /**
             * renderYear: Renders a 12-month grid with mini dot representations.
             * Each month shows up to 14 days of dots colored by status.
             * Clicking a month switches to the calendar tab at that month.
             */
            function renderYear() {
                const y = state.viewYear;
                document.getElementById('yearLabel').textContent = y;
                const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                let html = '';
                for (let m = 0; m < 12; m++) {
                    const days = daysInMonth(y, m);
                    let closed = 0,
                        modified = 0,
                        off = 0;
                    for (let d = 1; d <= days; d++) {
                        const s = getScheduleForDate(y, m, d);
                        if (s.type === 'closed') closed++;
                        else if (s.type === 'modified') modified++;
                        else if (s.type === 'weekly-off') off++;
                    }
                    // Build dots for the first 14 days of the month
                    const dots = [];
                    for (let d = 1; d <= Math.min(days, 14); d++) {
                        const st = getStatusForDate(y, m, d);
                        let cls = 'normal';
                        if (st === 'closed') cls = 'closed';
                        else if (st === 'modified') cls = 'modified';
                        else if (st === 'off') cls = 'off';
                        dots.push(`<span class="dot ${cls}"></span>`);
                    }
                    const summaryParts = [];
                    if (modified > 0) summaryParts.push(`${modified} modified`);
                    if (closed > 0) summaryParts.push(`${closed} closed`);
                    const summaryText = summaryParts.join(' · ') || 'No changes';

                    html += `
                            <div class="month-mini" data-month="${m}">
                                <div class="month-name">${monthNames[m]}</div>
                                <div class="mini-dots">${dots.join('')}</div>
                                <div class="mini-summary">${summaryText}</div>
                            </div>
                        `;
                }
                yearGrid.innerHTML = html;
                // Click handler: switch to calendar tab at the clicked month
                document.querySelectorAll('.month-mini').forEach(el => {
                    el.addEventListener('click', function() {
                        const m = parseInt(this.dataset.month);
                        state.viewMonth = m;
                        switchTab('calendar');
                        renderCalendar();
                    });
                });
            }

            

            // ─── MODAL ───

            /**
             * openDateModal: Opens the date edit modal for a given date key.
             * - If the date is in the past, the modal becomes read-only.
             * - Loads existing override data or defaults from the weekly schedule.
             * - Shows default hours for reference.
             */
            function openDateModal(dateKey) {

                console.log('🟢 Opening date modal:', dateKey);
                
                state.modalTarget = dateKey;
                const p = parseDateKey(dateKey);
                const dObj = new Date(p.year, p.month, p.day);
                document.getElementById('modalDateTitle').textContent = dObj.toLocaleDateString('en-US', {
                    weekday: 'long',
                    month: 'long',
                    day: 'numeric',
                    year: 'numeric'
                });
                document.getElementById('modalDateSub').textContent = 'Set schedule for this date';

                const isPast = isPastDate(p.year, p.month, p.day);
                const warningEl = document.getElementById('modalPastWarning');
                const saveBtn = document.getElementById('modalSaveBtn');
                const inputs = document.querySelectorAll('#dateModal input, #dateModal select, #dateModal textarea');
                const radioGroup = document.getElementById('scheduleTypeGroup');

                if (isPast) {
                    // Past date: read-only mode
                    warningEl.style.display = 'flex';
                    saveBtn.disabled = true;
                    inputs.forEach(el => el.disabled = true);
                    radioGroup.querySelectorAll('.radio-option').forEach(opt => opt.classList.add('disabled-opt'));
                    const ov = state.overrides[dateKey];
                    if (ov) {
                        if (ov.type === 'closed') {
                            document.querySelector('input[name="scheduleType"][value="closed"]').checked = true;
                            
                            document.getElementById('modalNote').value = ov.note || '';
                        } else if (ov.type === 'modified') {
                            document.querySelector('input[name="scheduleType"][value="modified"]').checked = true;
                            document.getElementById('modalOpenTime').value = ov.opening || '10:00';
                            document.getElementById('modalCloseTime').value = ov.closing || '15:00';
                            
                            document.getElementById('modalNote').value = ov.note || '';
                        } else {
                            document.querySelector('input[name="scheduleType"][value="follow"]').checked = true;
                        }
                    } else {
                        const def = getDefaultHoursForDate(p.year, p.month, p.day);
                        document.querySelector('input[name="scheduleType"][value="follow"]').checked = true;
                        if (def) {
                            document.getElementById('modalOpenTime').value = def.opening;
                            document.getElementById('modalCloseTime').value = def.closing;
                        } else {
                            document.getElementById('modalOpenTime').value = '09:00';
                            document.getElementById('modalCloseTime').value = '18:00';
                        }
                        
                        document.getElementById('modalNote').value = '';
                    }
                    updateModalFields();
                    document.getElementById('modalValidation').style.display = 'none';
                    document.getElementById('dateModal').classList.add('show');
                    document.body.style.overflow = 'hidden';
                    return;
                }

                // Not past: enable all fields
                warningEl.style.display = 'none';
                saveBtn.disabled = false;
                inputs.forEach(el => el.disabled = false);
                radioGroup.querySelectorAll('.radio-option').forEach(opt => opt.classList.remove('disabled-opt'));

                // Load existing override or default
                const ov = state.overrides[dateKey];
                if (ov) {
                    if (ov.type === 'closed') {
                        document.querySelector('input[name="scheduleType"][value="closed"]').checked = true;
                        
                        document.getElementById('modalNote').value = ov.note || '';
                    } else if (ov.type === 'modified') {
                        document.querySelector('input[name="scheduleType"][value="modified"]').checked = true;
                        document.getElementById('modalOpenTime').value = ov.opening || '10:00';
                        document.getElementById('modalCloseTime').value = ov.closing || '15:00';
                        
                        document.getElementById('modalNote').value = ov.note || '';
                    } else {
                        document.querySelector('input[name="scheduleType"][value="follow"]').checked = true;
                    }
                } else {
                    document.querySelector('input[name="scheduleType"][value="follow"]').checked = true;
                    const def = getDefaultHoursForDate(p.year, p.month, p.day);
                    if (def) {
                        document.getElementById('modalOpenTime').value = def.opening;
                        document.getElementById('modalCloseTime').value = def.closing;
                    } else {
                        document.getElementById('modalOpenTime').value = '09:00';
                        document.getElementById('modalCloseTime').value = '18:00';
                    }
                    
                    document.getElementById('modalNote').value = '';
                }

                const def = getDefaultHoursForDate(p.year, p.month, p.day);
                document.getElementById('defaultHoursDisplay').textContent = def ? `Default: ${def.opening} – ${def.closing}` :
                    'Default: Closed (weekly)';

                updateModalFields();
                document.getElementById('modalValidation').style.display = 'none';
                document.getElementById('dateModal').classList.add('show');
                document.body.style.overflow = 'hidden';
            }

            /** closeDateModal: Closes the date modal and restores body scroll. */
            function closeDateModal() {
                document.getElementById('dateModal').classList.remove('show');
                document.body.style.overflow = '';
                state.modalTarget = null;
            }

            /**
             * updateModalFields: Toggles visibility of sections based on selected
             * radio option (Follow / Modified / Closed). Also highlights the active option.
             */
            function updateModalFields() {
                const val = document.querySelector('input[name="scheduleType"]:checked').value;
                document.getElementById('modalFollowSection').style.display = (val === 'follow') ? 'block' : 'none';
                document.getElementById('modalModifiedSection').style.display = (val === 'modified') ? 'block' : 'none';
                document.getElementById('modalClosedSection').style.display = (val === 'closed') ? 'block' : 'none';
                document.querySelectorAll('.radio-option').forEach(el => {
                    el.classList.toggle('active-opt', el.querySelector('input').checked);
                });
            }

            /**
             * saveDateModal: Validates and saves the modal state to state.overrides.
             * - For 'modified': validates opening < closing.
             * - For 'closed': stores closed status with reason.
             * - For 'follow': deletes any override (reverts to weekly).
             * Shows validation errors via toast or inline message.
             */
            async function saveDateModal() {

                if (!state.modalTarget) return;

                const key = state.modalTarget;
                const p = parseDateKey(key);

                if (isPastDate(
                    p.year,
                    p.month,
                    p.day
                )) {
                    showToast('Cannot modify past dates');
                    return;
                }

                const val =
                    document.querySelector(
                        'input[name="scheduleType"]:checked'
                    ).value;

                const validationEl =
                    document.getElementById('modalValidation');

                validationEl.style.display = 'none';

                if (val === 'modified') {

                    const opening =
                        document.getElementById(
                            'modalOpenTime'
                        ).value;

                    const closing =
                        document.getElementById(
                            'modalCloseTime'
                        ).value;

                    if (!opening || !closing) {

                        validationEl.textContent =
                            'Opening and closing times are required.';

                        validationEl.style.display = 'block';

                        return;
                    }

                    if (opening >= closing) {

                        validationEl.textContent =
                            'Closing time must be after opening time.';

                        validationEl.style.display = 'block';

                        return;
                    }

                    state.overrides[key] = {
                        type: 'modified',
                        opening,
                        closing,
                        note:
                            document.getElementById(
                                'modalNote'
                            ).value || ''
                    };

                } else if (val === 'closed') {

                    state.overrides[key] = {
                        type: 'closed',
                        note:
                            document.getElementById(
                                'modalNote'
                            ).value || ''
                    };

                } else {

                    delete state.overrides[key];
                }

                // IMPORTANT
                const saved = await saveToDjango();

                if (!saved) {
                    return;
                }

                closeDateModal();
                updateAll();

                showToast(
                    `Schedule updated for ${key}`
                );
            }

            // ─── BULK MODAL ───

            /** openBulkModal: Opens the bulk update modal with default date range. */
            function openBulkModal() {

                const t = new Date();

                const t2 = new Date(t);
                t2.setDate(t2.getDate() + 3);

                // Reset minimum date
                bulkFromPicker.set('minDate', 'today');
                bulkToPicker.set('minDate', t);

                // Default dates
                bulkFromPicker.setDate(t, false);
                bulkToPicker.setDate(t2, false);

                document.getElementById('bulkOpen').value = '10:00';
                document.getElementById('bulkClose').value = '15:00';
                document.getElementById('bulkReason').value = '';
                document.getElementById('bulkValidation').style.display = 'none';

                document.getElementById('bulkModal').classList.add('show');
                document.body.style.overflow = 'hidden';
            }

            /** closeBulkModal: Closes the bulk modal. */
            function closeBulkModal() {
                document.getElementById('bulkModal').classList.remove('show');
                document.body.style.overflow = '';
            }

            /**
             * applyBulk: Validates date range, ensures all dates are future,
             * then applies the selected action (modified hours or closed) to all dates.
             * Shows confirmation dialog before applying.
             */
            async function applyBulk() {

            const fromVal =
                document.getElementById('bulkFrom').value;

            const toVal =
                document.getElementById('bulkTo').value;

            const vEl =
                document.getElementById('bulkValidation');

            const applyBtn =
                document.getElementById('bulkApplyBtn');

            vEl.style.display = 'none';

            // --------------------------------
            // BASIC VALIDATION
            // --------------------------------

            if (!fromVal || !toVal) {

                vEl.textContent =
                    'Please select both dates.';

                vEl.style.display = 'block';

                return;
            }

            if (fromVal > toVal) {

                vEl.textContent =
                    'Start date cannot be after end date.';

                vEl.style.display = 'block';

                return;
            }

            // --------------------------------
            // BUILD DATE RANGE
            // --------------------------------

            const start =
                new Date(fromVal + 'T00:00:00');

            const end =
                new Date(toVal + 'T00:00:00');

            const dates = [];

            for (
                let d = new Date(start);
                d <= end;
                d.setDate(d.getDate() + 1)
            ) {

                const y = d.getFullYear();
                const m = d.getMonth();
                const day = d.getDate();

                const key =
                    fmtDateKey(y, m, day);

                // Past dates are not allowed
                if (isPastDate(y, m, day)) {

                    vEl.textContent =
                        `Cannot include past dates (${key}). Please select only future dates.`;

                    vEl.style.display = 'block';

                    return;
                }

                dates.push(key);
            }

            if (dates.length === 0) {

                vEl.textContent =
                    'No valid dates in selected range.';

                vEl.style.display = 'block';

                return;
            }

            // --------------------------------
            // GET BULK TYPE
            // --------------------------------

            const typeEl =
                document.querySelector(
                    'input[name="bulkType"]:checked'
                );

            if (!typeEl) {

                vEl.textContent =
                    'Please select a schedule type.';

                vEl.style.display = 'block';

                return;
            }

            const type = typeEl.value;

            // --------------------------------
            // GET REASON
            // --------------------------------

            const reason =
                document.getElementById(
                    'bulkReason'
                ).value || '';

            const note = '';

            // --------------------------------
            // MODIFIED HOURS VALIDATION
            // --------------------------------

            let opening = '';
            let closing = '';

            if (type === 'modified') {

                opening =
                    document.getElementById(
                        'bulkOpen'
                    ).value;

                closing =
                    document.getElementById(
                        'bulkClose'
                    ).value;

                if (!opening || !closing) {

                    vEl.textContent =
                        'Opening and closing times are required.';

                    vEl.style.display = 'block';

                    return;
                }

                if (opening >= closing) {

                    vEl.textContent =
                        'Closing time must be after opening time.';

                    vEl.style.display = 'block';

                    return;
                }
            }

            // --------------------------------
            // CONFIRMATION
            // --------------------------------

            const confirmed = confirm(
                `Apply this schedule to ${dates.length} dates?`
            );

            if (!confirmed) {
                return;
            }

            // --------------------------------
            // BACKUP CURRENT STATE
            // --------------------------------

            const previousOverrides =
                JSON.parse(
                    JSON.stringify(state.overrides)
                );

            // --------------------------------
            // UPDATE STATE
            // --------------------------------

            dates.forEach(key => {

                if (type === 'closed') {

                    state.overrides[key] = {
                        type: 'closed',
                        reason: reason || 'Closed',
                        note: note
                    };

                } else if (type === 'modified') {

                    state.overrides[key] = {
                        type: 'modified',
                        opening: opening,
                        closing: closing,
                        reason: reason || 'Modified Hours',
                        note: note
                    };

                } else {

                    // Follow weekly schedule
                    delete state.overrides[key];
                }
            });

            // --------------------------------
            // SAVE TO DATABASE
            // --------------------------------

            applyBtn.disabled = true;

            const originalText =
                applyBtn.innerHTML;

            applyBtn.innerHTML =
                '<i class="bi bi-hourglass-split"></i> Saving...';

            try {

                const saved =
                    await saveToDjango();

                // --------------------------------
                // DB SAVE FAILED
                // ROLLBACK FRONTEND STATE
                // --------------------------------

                if (!saved) {

                    state.overrides =
                        previousOverrides;
                    


                    renderCalendar();
                    renderYear();

                    return;
                }

                // --------------------------------
                // SUCCESS
                // --------------------------------

                closeBulkModal();

                updateAll();

                showToast(
                    `Schedule updated for ${dates.length} dates`
                );

            } catch (error) {

                console.error(
                    '❌ Bulk update error:',
                    error
                );

                // Rollback
                state.overrides =
                    previousOverrides;

                updateAll();

                showToast(
                    'Bulk update failed. No changes were saved.'
                );

            } finally {

                applyBtn.disabled = false;

                applyBtn.innerHTML =
                    originalText;
            }
        }

            // ─── TABS ───

            /**
             * switchTab: Switches between tabs by toggling classes.
             * Only 'calendar' and 'year' tabs exist after removing weekly.
             * Re-renders the appropriate view when switching.
             */
            function switchTab(tabId) {
                document.querySelectorAll('.tab-btn').forEach(el => {
                    el.classList.toggle('active', el.dataset.tab === tabId);
                    el.setAttribute('aria-selected', el.dataset.tab === tabId);
                });
                document.querySelectorAll('.tab-pane').forEach(el => {
                    el.classList.toggle('active', el.id === 'tab-' + tabId);
                });
                if (tabId === 'calendar') renderCalendar();
                if (tabId === 'year') renderYear();
            }

            // ─── UPDATE ALL ───

            /**
             * updateAll: Re-renders both the calendar and year views.
             * Called after any state change (override added/removed, view changed).
             */
            function updateAll() {
                renderCalendar();
                renderYear();
            }

            // ─── DJANGO SAVE ───

            /**
             * saveToDjango: Sends the current state (weekly schedule + overrides)
             * to the Django backend via POST request.
             * - Retrieves hospital UUID from #app data attribute.
             * - Includes CSRF token for security.
             * - Handles response and shows success/error toast.
             * This function is called by the Save button, the Update Calendar button,
             * and was previously bound to Ctrl+S (now removed).
             */
            async function saveToDjango() {

            const appContainer =
                document.getElementById('app');

            const hospitalUuid =
                appContainer?.dataset.hospitalUuid;

            if (!hospitalUuid) {

                console.error(
                    '❌ Hospital UUID not found'
                );

                showToast(
                    'Hospital information is missing.'
                );

                return false;
            }

            const payload = {
                weekly_schedule: state.weekly,
                overrides: state.overrides
            };

            console.log(
                '📦 Working Hours Payload:',
                payload
            );

            try {

                const response = await fetch(
                    `/medical/hospital/${hospitalUuid}/working-hours/save/`,
                    {
                        method: 'POST',

                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCSRFToken(),
                            'X-Requested-With': 'XMLHttpRequest'
                        },

                        body: JSON.stringify(payload)
                    }
                );

                const data = await response.json();

                console.log(
                    '📥 Save response:',
                    data
                );

                if (!response.ok || !data.success) {

                    showToast(
                        data.message ||
                        'Failed to save working hours.'
                    );

                    return false;
                }

                return true;

            } catch (error) {

                console.error(
                    '❌ Working hours save error:',
                    error
                );

                showToast(
                    'Unable to save working hours.'
                );

                return false;
            }
        }

            // ─── EVENT BINDING ───

            // Tabs: switch on click
            document.querySelectorAll('.tab-btn').forEach(el => {
                el.addEventListener('click', function() { switchTab(this.dataset.tab); });
            });

            // Today: jump to current month
            document.getElementById('todayBtn').addEventListener('click', function() {
                const d = new Date();
                state.viewYear = d.getFullYear();
                state.viewMonth = d.getMonth();
                renderCalendar();
                showToast('Jumped to today');
            });

            // Month navigation
            document.getElementById('prevMonthBtn').addEventListener('click', function() {
                state.viewMonth--;
                if (state.viewMonth < 0) { state.viewMonth = 11;
                    state.viewYear--; }
                renderCalendar();
            });
            document.getElementById('nextMonthBtn').addEventListener('click', function() {
                state.viewMonth++;
                if (state.viewMonth > 11) { state.viewMonth = 0;
                    state.viewYear++; }
                renderCalendar();
            });

            // Year navigation (affects both calendar and year view)
            document.getElementById('prevYearBtn').addEventListener('click', function() {
                state.viewYear--;
                renderCalendar();
                renderYear();
            });
            document.getElementById('nextYearBtn').addEventListener('click', function() {
                state.viewYear++;
                renderCalendar();
                renderYear();
            });



            // Modal: close buttons and overlay click
            document.getElementById('modalCloseBtn').addEventListener('click', closeDateModal);
            document.getElementById('modalCancelBtn').addEventListener('click', closeDateModal);
            document.getElementById('dateModal').addEventListener('click', function(e) {
                if (e.target === this) closeDateModal();
            });
            // Modal: radio change updates visible sections
            document.querySelectorAll('input[name="scheduleType"]').forEach(el => {
                el.addEventListener('change', updateModalFields);
            });
            // Modal: save button
            document.getElementById('modalSaveBtn').addEventListener('click', saveDateModal);

            // Bulk modal: open/close
            document.getElementById('bulkUpdateBtn').addEventListener('click', openBulkModal);
            document.getElementById('bulkCloseBtn').addEventListener('click', closeBulkModal);
            document.getElementById('bulkCancelBtn').addEventListener('click', closeBulkModal);
            document.getElementById('bulkModal').addEventListener('click', function(e) {
                if (e.target === this) closeBulkModal();
            });
            document.getElementById('bulkApplyBtn').addEventListener('click', applyBulk);
            // Bulk: toggle modified fields visibility
            document.querySelectorAll('input[name="bulkType"]').forEach(el => {
                el.addEventListener('change', function() {
                    document.getElementById('bulkModifiedFields').style.display = (this.value ===
                        'modified') ? 'flex' : 'none';
                });
            });


            // ─── KEYBOARD SHORTCUTS ───

            /**
             * Keyboard event handler.
             * - Escape: closes any open modal.
             * - Ctrl+S: PREVENTED (removed) — the Update Calendar button now handles saving.
             *   The user explicitly requested to replace Ctrl+S with the button.
             */
            document.addEventListener('keydown', function(e) {
                // Escape closes modals
                if (e.key === 'Escape') {
                    if (document.getElementById('dateModal').classList.contains('show')) closeDateModal();
                    if (document.getElementById('bulkModal').classList.contains('show')) closeBulkModal();
                }
                // Ctrl+S is intentionally disabled — use the Update Calendar button instead.
                // The user requested: "replace function ctrl+s with this button"
                if (e.ctrlKey && e.key === 's') {
                    e.preventDefault();
                    // No action — the user should use the Update Calendar button.
                    showToast('Use the "Update Calendar" button to save.');
                }
            });

            // ─── DEMO DATA ───

            /**
             * Pre-populates the state with sample overrides for future dates.
             * Only adds data if the date is not in the past (prevents editing past dates).
             * These are for demonstration purposes and can be removed in production.
             */
            const now = new Date();
            now.setHours(0, 0, 0, 0);


            // ─── INIT ───

            // Set initial view to current month
            const nowDate = new Date();
            state.viewYear = nowDate.getFullYear();
            state.viewMonth = nowDate.getMonth();

            // Initialize bulk date pickers
            initBulkDatePickers();

            // Render all views
            renderCalendar();
            renderYear();

            // Show welcome toast with override count
            setTimeout(() => {
                showToast('✅ Schedule loaded · ' + Object.keys(state.overrides).length + ' overrides active');
            }, 400);

            // Expose state and save function for debugging
            window.__state = state;
            window.saveToDjango = saveToDjango;

            console.log('🏥 Hospital Schedule UI ready');
            console.log('🔄 Use the "Update Calendar" button to save changes.');

        })();
