/* ========================================================== */
/*  FACULTY MONTHLY - Donut chart, mini calendar, timeline    */
/* ========================================================== */
document.addEventListener('DOMContentLoaded', function(){
  var dataEl = document.getElementById('facultyMonthlyData');
  if (!dataEl) return;
  var pageData;
  try { pageData = JSON.parse(dataEl.textContent); } catch(e) { return; }

  var statusColors = {
    PRESENT: '#16a34a', ABSENT: '#dc2626', LATE: '#d97706',
    ON_LEAVE: '#7c3aed', HALF_DAY: '#2563eb',
    PENDING: '#e5e7eb', NO_DATA: '#f3f4f6'
  };
  var statusLabels = {
    PRESENT: 'Present', ABSENT: 'Absent', LATE: 'Late',
    ON_LEAVE: 'On Leave', HALF_DAY: 'Half Day',
    PENDING: 'Pending', NO_DATA: 'No Data'
  };

  /* ---------- Donut Chart ---------- */
  var donutData = pageData.donut || [];
  var donutCanvas = document.getElementById('zaMDonutChart');
  if (donutCanvas && donutData.length && typeof Chart !== 'undefined') {
    var monthlyChart = new Chart(donutCanvas, {
      type: 'doughnut',
      data: {
        labels: donutData.map(function(d){ return d.l; }),
        datasets: [{
          data: donutData.map(function(d){ return d.v; }),
          backgroundColor: donutData.map(function(d){ return d.c; }),
          borderWidth: 0
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 10, padding: 8, font: { size: 11 } } },
          tooltip: { callbacks: { label: function(ctx){ return ctx.label + ': ' + ctx.parsed; } } }
        },
        cutout: '62%'
      }
    });

    function handleResize(){
      var w = window.innerWidth;
      monthlyChart.options.plugins.legend.labels.font.size = w < 200 ? 5 : w < 280 ? 6 : w < 360 ? 8 : w < 480 ? 9 : 11;
      monthlyChart.options.plugins.legend.labels.boxWidth = w < 280 ? 6 : 12;
      monthlyChart.resize();
    }
    var rt; window.addEventListener('resize', function(){ clearTimeout(rt); rt = setTimeout(handleResize, 200); });
    handleResize();
  }

  /* ---------- Mini Calendar Grid ---------- */
  var dailyData = pageData.daily || [];
  var calGrid = document.getElementById('zaMCalGrid');
  var calYear = pageData.year || 2026;
  var calMonth = pageData.month || 1;
  var legendItems = pageData.legend || [];

  if (calGrid && dailyData.length) {
    var daysInMonth = new Date(calYear, calMonth, 0).getDate();
    var firstDow = new Date(calYear, calMonth - 1, 1).getDay();
    var statusMap = {};
    dailyData.forEach(function(d){ statusMap[d.day] = d.status; });

    var html = '<div class="za-cal-grid">';
    ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].forEach(function(h){ html += '<div class="za-cal-hd">' + h + '</div>'; });
    for (var i = 0; i < firstDow; i++) { html += '<div class="za-cal-empty"></div>'; }
    for (var dayNum = 1; dayNum <= daysInMonth; dayNum++) {
      var status = statusMap[dayNum] || 'NO_DATA';
      html += '<div class="za-cal-cell" style="background:' + (statusColors[status]||'#f3f4f6') + '" title="Day ' + dayNum + ': ' + (statusLabels[status]||status) + '">' + dayNum + '</div>';
    }
    html += '</div>';

    html += '<div class="za-cal-legend">';
    legendItems.forEach(function(item){
      if (item.count > 0) {
        html += '<span class="za-cal-leg-item"><span class="za-cal-leg-dot" style="background:' + item.color + '"></span>' + item.label + ' ' + item.count + '</span>';
      }
    });
    html += '</div>';
    calGrid.innerHTML = html;
  }

  /* ---------- Timeline Row Animation ---------- */
  document.querySelectorAll('.za-m-tl-row').forEach(function(row, i){ row.style.setProperty('--i', i); });

  /* ---------- Timeline Dot Status Sync ---------- */
  document.querySelectorAll('.za-m-tl-badge').forEach(function(badge){
    var row = badge.closest('.za-m-tl-row');
    if (!row) return;
    var dot = row.querySelector('.za-m-tl-spark');
    if (!dot) return;
    var cls = badge.className.match(/status-(\w+)/);
    if (!cls) return;
    var map = {present:'spark-green', absent:'spark-red', late:'spark-amber', on_leave:'spark-purple', half_day:'spark-blue'};
    var target = map[cls[1]];
    if (target) dot.className = 'za-m-tl-spark ' + target;
  });
});
