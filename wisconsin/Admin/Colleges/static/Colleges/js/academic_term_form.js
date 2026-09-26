// steve code
document.addEventListener('DOMContentLoaded', function () {


    var academicYearEl     = document.getElementById('id_academic_year');
    var termNameEl         = document.getElementById('id_term_name');
    var statusEl           = document.getElementById('id_status');
    var startDateEl        = document.getElementById('id_start_date');
    var endDateEl          = document.getElementById('id_end_date');
    var regStartEl         = document.getElementById('id_registration_start');
    var regEndEl           = document.getElementById('id_registration_end');


    var prevYear      = document.getElementById('prevYear');
    var prevTerm      = document.getElementById('prevTerm');
    var prevStatus    = document.getElementById('prevStatus');
    var prevTermDates = document.getElementById('prevTermDates');
    var prevRegStart  = document.getElementById('prevRegStart');
    var prevRegEnd    = document.getElementById('prevRegEnd');


    var durationBar  = document.getElementById('durationBar');
    var durationText = document.getElementById('durationText');


    var tlRegStart = document.getElementById('tlRegStart');
    var tlRegEnd   = document.getElementById('tlRegEnd');
    var tlStart    = document.getElementById('tlStart');
    var tlEnd      = document.getElementById('tlEnd');

    if (!academicYearEl) return;

    function formatDate(value) {
        if (!value) return null;
        var d = new Date(value + 'T00:00:00');
        if (isNaN(d.getTime())) return null;
        return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    }

    function daysBetween(a, b) {
        var d1 = new Date(a + 'T00:00:00');
        var d2 = new Date(b + 'T00:00:00');
        if (isNaN(d1.getTime()) || isNaN(d2.getTime())) return null;
        var diff = (d2 - d1) / (1000 * 60 * 60 * 24);
        return Math.round(diff);
    }

    function getSelectedLabel(selectEl) {
        if (!selectEl || selectEl.selectedIndex < 0) return null;
        var opt = selectEl.options[selectEl.selectedIndex];
        return opt && opt.value ? opt.textContent.trim() : null;
    }

    function updatePreview() {
        // Academic Year
        var yearVal = academicYearEl.value.trim();
        prevYear.textContent = yearVal || '—';

        // Term Name
        var termLabel = getSelectedLabel(termNameEl);
        prevTerm.textContent = termLabel || '—';

        // Status
        var statusLabel = getSelectedLabel(statusEl);
        prevStatus.textContent = statusLabel || '—';
        prevStatus.className = 'prev-status-badge';
        if (statusLabel) {
            prevStatus.classList.add('status-' + statusLabel.toLowerCase().replace(/\s+/g, '-'));
        }

        // Term dates
        var startVal = startDateEl.value;
        var endVal = endDateEl.value;
        var startFmt = formatDate(startVal);
        var endFmt = formatDate(endVal);
        if (startFmt && endFmt) {
            prevTermDates.textContent = startFmt + ' – ' + endFmt;
        } else if (startFmt) {
            prevTermDates.textContent = startFmt + ' – …';
        } else {
            prevTermDates.textContent = '—';
        }

        // Registration dates
        var regStartVal = regStartEl.value;
        var regEndVal = regEndEl.value;
        prevRegStart.textContent = formatDate(regStartVal) || '—';
        prevRegEnd.textContent = formatDate(regEndVal) || '—';

        // Duration bar
        if (startVal && endVal) {
            var days = daysBetween(startVal, endVal);
            if (days !== null && days > 0) {
                var weeks = Math.round(days / 7);
                durationText.textContent = days + ' days (~' + weeks + ' weeks)';
                durationBar.style.display = 'flex';
            } else if (days !== null && days <= 0) {
                durationText.textContent = 'End date must be after start date';
                durationBar.style.display = 'flex';
            } else {
                durationBar.style.display = 'none';
            }
        } else {
            durationBar.style.display = 'none';
        }

        // Timeline
        tlRegStart.textContent = formatDate(regStartVal) || 'Not set';
        tlRegEnd.textContent = formatDate(regEndVal) || 'Not set';
        tlStart.textContent = formatDate(startVal) || 'Not set';
        tlEnd.textContent = formatDate(endVal) || 'Not set';
    }


    [academicYearEl, termNameEl, statusEl, startDateEl, endDateEl, regStartEl, regEndEl]
        .forEach(function (el) {
            if (!el) return;
            el.addEventListener('input', updatePreview);
            el.addEventListener('change', updatePreview);
        });


    updatePreview();
});

document.addEventListener("DOMContentLoaded", function () {

    document.querySelectorAll("select.atf-select").forEach(function (select) {

        new Choices(select, {
            searchEnabled: true,
            shouldSort: false,
            itemSelectText: "",
            allowHTML: false,
        });

    });

});