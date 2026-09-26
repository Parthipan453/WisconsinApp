/* ========================================================== */
/*  ATTENDANCE CHARTS - Chart.js donut, line, marked          */
/* ========================================================== */
(function(){
  var dataEl = document.getElementById('attendanceChartData');
  if (!dataEl) return;
  var pageData;
  try { pageData = JSON.parse(dataEl.textContent); } catch(e) { return; }

  function showNoData(canvas){
    if (!canvas) return;
    canvas.style.display = 'none';
    var parent = canvas.parentNode;
    if (!parent || parent.querySelector('.za-no-data')) return;
    var msg = document.createElement('div');
    msg.className = 'za-no-data';
    msg.innerHTML = '<i class="ti ti-database-off"></i><span>No data available</span>';
    parent.appendChild(msg);
  }

  function buildDonut(canvas, data) {
    if (!canvas || !data || !data.length || !data.some(function(d){ return d.v > 0; })) {
      showNoData(canvas);
      return null;
    }
    return new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: data.map(function(d){ return d.l; }),
        datasets: [{
          data: data.map(function(d){ return d.v; }),
          backgroundColor: data.map(function(d){ return d.c; }),
          borderWidth: 0
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 10, padding: 8, font: { size: 11 } } },
          tooltip: { callbacks: { label: function(ctx){ return ctx.label + ': ' + ctx.parsed; } } }
        },
        cutout: '65%'
      }
    });
  }

  var donutChart = buildDonut(document.getElementById('zaDonutChart'), pageData.donut);

  var markedData = pageData.marked;
  var markedCanvas = document.getElementById('zaMarkedChart');
  var markedChart = null;
  if (markedCanvas && markedData && markedData.length) {
    markedChart = new Chart(markedCanvas, {
      type: 'doughnut',
      data: {
        labels: markedData.map(function(d){ return d.l; }),
        datasets: [{
          data: markedData.map(function(d){ return d.v; }),
          backgroundColor: markedData.map(function(d){ return d.c; }),
          borderWidth: 0
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 10, padding: 8, font: { size: 11 } } },
          tooltip: {
            callbacks: {
              label: function(ctx){
                var total = ctx.dataset.data.reduce(function(a,b){ return a+b; }, 0);
                return ctx.label + ': ' + ctx.parsed + ' (' + ((ctx.parsed/total)*100).toFixed(1) + '%)';
              }
            }
          }
        },
        cutout: '65%'
      }
    });
  } else { showNoData(markedCanvas); }

  var trendData = pageData.trend;
  var trendCanvas = document.getElementById('zaTrendChart');
  var trendChart = null;
  if (trendCanvas && trendData && trendData.length) {
    trendChart = new Chart(trendCanvas, {
      type: 'line',
      data: {
        labels: trendData.map(function(d){ return d.d; }),
        datasets: [{
          label: 'Present %',
          data: trendData.map(function(d){ return d.present_pct; }),
          borderColor: '#6366f1',
          backgroundColor: 'rgba(99,102,241,0.08)',
          fill: true, tension: 0.35, pointRadius: 3,
          pointBackgroundColor: '#6366f1', borderWidth: 2
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function(ctx){
                var d = trendData[ctx.dataIndex];
                return 'Present: ' + d.p + '/' + (d.p+d.a+d.l+d.v+d.h) + ' (' + d.present_pct + '%)';
              }
            }
          }
        },
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: 9 }, maxTicksLimit: 15 } },
          y: { beginAtZero: true, max: 100, ticks: { font: { size: 9 }, callback: function(v){ return v + '%'; } } }
        }
      }
    });
  } else { showNoData(trendCanvas); }

  function handleChartResize(){
    var w = window.innerWidth;
    [donutChart, markedChart].forEach(function(chart){
      if (!chart) return;
      chart.options.plugins.legend.labels.font.size = w < 200 ? 5 : w < 280 ? 6 : w < 360 ? 8 : w < 480 ? 9 : 11;
      chart.options.plugins.legend.labels.boxWidth = w < 280 ? 6 : 12;
      chart.resize();
    });
    if (trendChart) {
      trendChart.options.scales.x.ticks.font.size = w < 200 ? 5 : w < 280 ? 6 : w < 360 ? 7 : w < 480 ? 8 : 9;
      trendChart.options.scales.y.ticks.font.size = w < 200 ? 5 : w < 280 ? 6 : w < 360 ? 7 : w < 480 ? 8 : 9;
      trendChart.resize();
    }
  }

  var resizeTimer;
  window.addEventListener('resize', function(){ clearTimeout(resizeTimer); resizeTimer = setTimeout(handleChartResize, 200); });
  handleChartResize();
})();
