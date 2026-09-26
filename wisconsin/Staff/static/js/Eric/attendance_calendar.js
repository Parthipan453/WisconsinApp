/* ========================================================== */
/*  ATTENDANCE CALENDAR - VanillaCalendarPro integration       */
/* ========================================================== */
(function(){
  var calEl = document.getElementById('zaCalendar');
  var dataEl = document.getElementById('attendanceCalendarData');
  if (!calEl || !dataEl) return;
  var calData;
  try { calData = JSON.parse(dataEl.textContent); } catch(e) { return; }
  if (typeof VanillaCalendarPro === 'undefined') return;

  var Calendar = VanillaCalendarPro.Calendar;
  new Calendar('#zaCalendar', {
    selectedTheme: 'light',
    selectionDatesMode: 'single',
    selectedDates: [calData.selected_date || ''],
    selectedMonth: calData.selected_month || 0,
    selectedYear: calData.selected_year || 2026,
    popups: calData.popups || {},
    disableDates: function(date){
      return date > new Date(calData.today || new Date().toISOString().slice(0,10));
    },
    onClickDate: function(self){
      var chosenDate = self.context.selectedDates[0];
      if (chosenDate && chosenDate <= (calData.today || '')) {
        var url = '?date=' + chosenDate;
        if (calData.department) url += '&department=' + calData.department;
        window.location.href = url;
      }
    }
  }).init();
})();
