/* ========================================================== */
/*  ATTENDANCE BASE - Shared helpers and components            */
/* ========================================================== */

/* ---------- Helpers ---------- */
function toMins(t) {
  if (!t) return null;
  var p = t.split(":");
  return parseInt(p[0],10)*60 + parseInt(p[1],10);
}

function compute(ci,co,form) {
  var late=0, early=0, hours=null, suggest=null;
  var ciM=toMins(ci), coM=toMins(co);
  var ciEnd=toMins(form.getAttribute("data-ci-end"));
  var coEnd=toMins(form.getAttribute("data-co-end"));
  if (ciM && ciEnd && ciM>ciEnd) late=ciM-ciEnd;
  if (coM && coEnd && coEnd>coM) early=coEnd-coM;
  if (ciM && coM && coM>ciM) hours=Math.round(((coM-ciM)/60)*100)/100;
  if (late>0) suggest="LATE";
  else if (ciM) suggest="PRESENT";
  return {late:late, early:early, hours:hours, suggest:suggest};
}

function displayTime(t) {
  if (!t) return "";
  var p = t.split(":");
  var h = parseInt(p[0],10), m = p[1];
  var ampm = h >= 12 ? "PM" : "AM";
  var h12 = h % 12 || 12;
  return h12 + ":" + m + " " + ampm;
}

function fmtTime(h, m) {
  return String(h).padStart(2,"0") + ":" + String(m).padStart(2,"0");
}

/* ---------- Animate on Scroll ---------- */
(function(){
  var els=document.querySelectorAll("[data-aos]");
  if (!els.length) return;
  var observer=new IntersectionObserver(function(entries){
    entries.forEach(function(entry){
      if (!entry.isIntersecting) return;
      var el=entry.target, delay=el.getAttribute("data-aos-delay");
      if (delay) el.style.animationDelay=delay+"ms";
      el.style.animation="zaFadeUp 0.4s ease both";
      observer.unobserve(el);
    });
  },{threshold:0.1});
  els.forEach(function(el){observer.observe(el);});
})();

/* ---------- Click outside to close dropdowns ---------- */
document.addEventListener('click', function(e) {
  document.querySelectorAll('.za-dropdown.open').forEach(function(dd) {
    if (!dd.contains(e.target)) dd.classList.remove('open');
  });
  document.querySelectorAll('.fa-tp.open').forEach(function(w) {
    if (!w.contains(e.target)) w.classList.remove('open');
  });
  document.querySelectorAll('.fa-dp.open').forEach(function(w) {
    if (!w.contains(e.target)) w.classList.remove('open');
  });
});

/* ---------- KPI Counter Animation ---------- */
(function(){
  var els = document.querySelectorAll(".kpi-number");
  if (!els.length) return;
  var observer = new IntersectionObserver(function(entries){
    entries.forEach(function(entry){
      if (!entry.isIntersecting) return;
      var el = entry.target, target = parseInt(el.getAttribute("data-target"),10);
      if (isNaN(target)) {el.textContent="0";return;}
      var current=0, step=Math.max(1,Math.ceil(target/30)), timer=setInterval(function(){
        current+=step;
        if (current>=target) {el.textContent=target;clearInterval(timer);}
        else el.textContent=current;
      },30);
      observer.unobserve(el);
    });
  },{threshold:0.5});
  els.forEach(function(el){observer.observe(el);});
})();

/* ---------- Chart Bar Fill Animation ---------- */
(function(){
  var bars=document.querySelectorAll(".za-chart-pa-fill, .za-chart-fill, .za-weekly-fill, .za-deptov-fill");
  if (!bars.length) return;
  var observer=new IntersectionObserver(function(entries){
    entries.forEach(function(entry){
      if (!entry.isIntersecting) return;
      var bar=entry.target, w=bar.getAttribute("data-width")||bar.style.width||"0%";
      bar.style.width="0%";
      requestAnimationFrame(function(){bar.style.width=w;});
      observer.unobserve(bar);
    });
  },{threshold:0.3});
  bars.forEach(function(b){observer.observe(b);});
})();
