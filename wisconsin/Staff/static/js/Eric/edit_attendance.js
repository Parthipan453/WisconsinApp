/* ========================================================== */
/*  EDIT ATTENDANCE - Auto-status, working-hours bar, submit  */
/* ========================================================== */

(function(){
  var form = document.getElementById("ea-form");
  if (!form) return;
  var ci = document.getElementById("ea-ci");
  var co = document.getElementById("ea-co");
  var st = document.getElementById("ea-st");
  var lateEl = document.getElementById("ea-late");
  var earlyEl = document.getElementById("ea-early");
  var hoursEl = document.getElementById("ea-hours");
  var badge = document.getElementById("ea-auto-status");

  function update() {
    var res = compute(ci?ci.value:"", co?co.value:"", form);
    if (lateEl) lateEl.textContent = res.late>0 ? res.late+" min" : "0 min";
    if (earlyEl) earlyEl.textContent = res.early>0 ? res.early+" min" : "0 min";
    if (hoursEl) hoursEl.textContent = res.hours!==null&&res.hours>=0 ? res.hours+"h" : "\u2014";
    if (badge) {
      badge.textContent = res.suggest || "auto";
      badge.className = "ea-auto-badge"+(res.suggest?" "+res.suggest.toLowerCase():"");
    }
    if (st && res.suggest) {
      st.value = res.suggest;
      st.dispatchEvent(new Event("change", {bubbles: true}));
    }
  }
  if (ci) {ci.addEventListener("input",update);ci.addEventListener("change",update);}
  if (co) {co.addEventListener("input",update);co.addEventListener("change",update);}
})();

/* ---------- Working Hours Bar ---------- */
(function(){
  var ciInput=document.getElementById("ea-ci");
  var coInput=document.getElementById("ea-co");
  var fillBar=document.getElementById("zaWhFill");
  var hoursLabel=document.getElementById("zaWhLabel");
  var form=document.getElementById("ea-form");
  if (!ciInput||!coInput||!fillBar) return;
  function getDuration(){
    var s=toMins(form?form.getAttribute("data-ci-end"):null)||540;
    var e=toMins(form?form.getAttribute("data-co-end"):null)||1020;
    return e>s?(e-s)/60:8;
  }
  function updateBar(){
    var ciM=toMins(ciInput.value), coM=toMins(coInput.value);
    var denom=getDuration();
    if (ciM!==null&&coM!==null&&coM>ciM){
      var hrs=Math.round(((coM-ciM)/60)*100)/100;
      var pct=Math.min(100,Math.round((hrs/denom)*100));
      fillBar.style.width=pct+"%";
      if (hoursLabel) hoursLabel.textContent=hrs+"h";
      fillBar.style.background=pct>=100?"#16a34a":pct>=75?"#d97706":"#dc2626";
    } else {
      fillBar.style.width="0%";
      if (hoursLabel) hoursLabel.textContent="—";
    }
  }
  ciInput.addEventListener("input",updateBar);
  coInput.addEventListener("input",updateBar);
  updateBar();
})();

/* ---------- Submit Validation ---------- */
(function(){
  var form=document.getElementById("ea-form");
  if (!form) return;
  var ci=document.getElementById("ea-ci"), co=document.getElementById("ea-co");
  form.addEventListener("submit",function(e){
    if (ci.value&&co.value&&ci.value>=co.value) {
      if (!confirm("Check-in ("+ci.value+") is not before check-out ("+co.value+"). Submit anyway?")) e.preventDefault();
    }
  });
})();
