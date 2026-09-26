/* ========================================================== */
/*  FACULTY ATTENDANCE - Date picker, time picker, bulk       */
/* ========================================================== */

/* ---------- Custom Date Picker ---------- */
(function () {
  function initDatePicker(input) {
    if (input.dataset.faDp === "1") return;
    input.dataset.faDp = "1";
    var MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];
    var DAYS_SHORT = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
    var wrap = document.createElement("div");
    wrap.className = "fa-dp";
    var trigger = document.createElement("div");
    trigger.className = "fa-dp-trigger"; trigger.tabIndex = 0;
    var label = document.createElement("span"); label.className = "fa-dp-label";
    trigger.appendChild(label);
    var icon = document.createElement("i"); icon.className = "ti ti-calendar";
    trigger.appendChild(icon);
    wrap.appendChild(trigger);
    var dropdown = document.createElement("div"); dropdown.className = "fa-dp-dropdown";
    wrap.appendChild(dropdown);
    input.classList.add("fa-dp-native");
    input.type = "date"; input.style.display = "none";
    input.parentNode.insertBefore(wrap, input);
    function toLocalDate(str) {
      if (!str) return null;
      var p = str.split("-");
      return new Date(parseInt(p[0],10), parseInt(p[1],10)-1, parseInt(p[2],10));
    }
    function fmt(d) {
      var mm = String(d.getMonth()+1).padStart(2,"0"), dd = String(d.getDate()).padStart(2,"0");
      return d.getFullYear()+"-"+mm+"-"+dd;
    }
    function updateLabel(d) {
      label.textContent = MONTHS[d.getMonth()].substring(0,3)+" "+d.getDate()+", "+d.getFullYear();
    }
    var renderDate = input.value ? toLocalDate(input.value) : new Date();
    var viewYear = renderDate.getFullYear(), viewMonth = renderDate.getMonth();
    var selectedDate = input.value ? toLocalDate(input.value) : null;
    if (selectedDate) updateLabel(selectedDate); else label.textContent = "Select date";

    function buildCalendar() {
      dropdown.innerHTML = "";
      var header = document.createElement("div"); header.className = "fa-dp-header";
      var prevBtn = document.createElement("button"); prevBtn.type = "button"; prevBtn.className = "fa-dp-prev";
      prevBtn.innerHTML = '<i class="ti ti-chevron-left"></i>';
      var monthLabel = document.createElement("span"); monthLabel.className = "fa-dp-month";
      monthLabel.textContent = MONTHS[viewMonth] + " " + viewYear;
      var nextBtn = document.createElement("button"); nextBtn.type = "button"; nextBtn.className = "fa-dp-next";
      nextBtn.innerHTML = '<i class="ti ti-chevron-right"></i>';
      header.append(prevBtn, monthLabel, nextBtn);
      dropdown.appendChild(header);
      var weekdays = document.createElement("div"); weekdays.className = "fa-dp-weekdays";
      DAYS_SHORT.forEach(function(d){ var el=document.createElement("span"); el.textContent=d; weekdays.appendChild(el); });
      dropdown.appendChild(weekdays);
      var daysGrid = document.createElement("div"); daysGrid.className = "fa-dp-days";
      var first = new Date(viewYear, viewMonth, 1), last = new Date(viewYear, viewMonth+1, 0);
      var startPad = first.getDay(), prevLast = new Date(viewYear, viewMonth, 0);
      for (var i=startPad-1; i>=0; i--) {
        var d = new Date(viewYear, viewMonth-1, prevLast.getDate()-i);
        var el = document.createElement("div"); el.className="fa-dp-day other"; el.textContent=prevLast.getDate()-i; el.dataset.date=fmt(d);
        daysGrid.appendChild(el);
      }
      for (var d2=1; d2<=last.getDate(); d2++) {
        var cd = new Date(viewYear, viewMonth, d2);
        var el2 = document.createElement("div"); el2.className="fa-dp-day"; el2.textContent=d2; el2.dataset.date=fmt(cd);
        var td = new Date();
        if (d2===td.getDate() && viewMonth===td.getMonth() && viewYear===td.getFullYear()) el2.classList.add("today");
        if (selectedDate && d2===selectedDate.getDate() && viewMonth===selectedDate.getMonth() && viewYear===selectedDate.getFullYear()) el2.classList.add("selected");
        daysGrid.appendChild(el2);
      }
      var remaining = 42 - daysGrid.children.length;
      for (var i2=1; i2<=remaining; i2++) {
        var nd = new Date(viewYear, viewMonth+1, i2);
        var el3 = document.createElement("div"); el3.className="fa-dp-day other"; el3.textContent=i2; el3.dataset.date=fmt(nd);
        daysGrid.appendChild(el3);
      }
      dropdown.appendChild(daysGrid);
    }
    buildCalendar();
    trigger.addEventListener("click", function(e){ e.stopPropagation(); wrap.classList.toggle("open"); });
    dropdown.addEventListener("click", function(e){
      var day = e.target.closest(".fa-dp-day");
      if (!day || !day.dataset.date) return;
      input.value = day.dataset.date; selectedDate = toLocalDate(input.value); updateLabel(selectedDate);
      input.dispatchEvent(new Event("change",{bubbles:true}));
      input.dispatchEvent(new Event("input",{bubbles:true}));
      wrap.classList.remove("open"); buildCalendar();
    });
    dropdown.addEventListener("click", function(e){
      var btn = e.target.closest(".fa-dp-header button");
      if (!btn) return;
      if (btn.classList.contains("fa-dp-prev")) { viewMonth--; if(viewMonth<0){viewMonth=11;viewYear--;} }
      if (btn.classList.contains("fa-dp-next")) { viewMonth++; if(viewMonth>11){viewMonth=0;viewYear++;} }
      buildCalendar();
    });
    input.addEventListener("change", function(){
      if (input.value) { selectedDate = toLocalDate(input.value); updateLabel(selectedDate); buildCalendar(); }
    });
  }
  document.querySelectorAll("input.fa-date-picker").forEach(initDatePicker);
})();

/* ---------- Custom Time Picker ---------- */
(function () {
  function initTimePicker(input) {
    if (input.dataset.faTp === "1") return;
    input.dataset.faTp = "1";
    var minT = input.getAttribute("min") || "00:00", maxT = input.getAttribute("max") || "23:59";
    var wrap = document.createElement("div"); wrap.className = "fa-tp";
    var trigger = document.createElement("div"); trigger.className = "fa-tp-trigger"; trigger.tabIndex = 0;
    var label = document.createElement("span"); label.className = "fa-tp-label";
    trigger.appendChild(label);
    var icon = document.createElement("i"); icon.className = "ti ti-clock";
    trigger.appendChild(icon);
    wrap.appendChild(trigger);
    var dropdown = document.createElement("div"); dropdown.className = "fa-tp-dropdown";
    wrap.appendChild(dropdown);
    input.classList.add("fa-tp-native"); input.type = "time"; input.style.display = "none";
    input.parentNode.insertBefore(wrap, input);
    function toMins2(str){ if(!str) return 0; var p=str.split(":"); return parseInt(p[0],10)*60+parseInt(p[1],10); }
    function buildOptions() {
      dropdown.innerHTML = "";
      var minM = toMins2(minT), maxM = toMins2(maxT);
      for (var h=0;h<24;h++) {
        for (var m=0;m<60;m+=5) {
          var t = fmtTime(h,m), tM = toMins2(t);
          if (tM<minM || tM>maxM) continue;
          var opt = document.createElement("div"); opt.className = "fa-tp-option";
          if (input.value===t) opt.classList.add("selected");
          opt.textContent = displayTime(t); opt.dataset.value = t;
          dropdown.appendChild(opt);
        }
      }
    }
    function updateLabel() { label.textContent = input.value ? displayTime(input.value) : "Select"; }
    buildOptions(); updateLabel();
    trigger.addEventListener("click", function(e){
      e.stopPropagation();
      var wasOpen = wrap.classList.contains("open");
      document.querySelectorAll(".fa-tp.open").forEach(function(w){w.classList.remove("open");});
      wrap.classList.toggle("open",!wasOpen);
      if (wrap.classList.contains("open")) {
        var sel = dropdown.querySelector(".fa-tp-option.selected");
        if (sel) sel.scrollIntoView({block:"nearest"});
      }
    });
    dropdown.addEventListener("click", function(e){
      var opt = e.target.closest(".fa-tp-option");
      if (!opt) return;
      input.value = opt.dataset.value; updateLabel();
      dropdown.querySelectorAll(".fa-tp-option").forEach(function(o){o.classList.remove("selected");});
      opt.classList.add("selected");
      input.dispatchEvent(new Event("change",{bubbles:true}));
      input.dispatchEvent(new Event("input",{bubbles:true}));
      wrap.classList.remove("open");
    });
    input.addEventListener("change", function(){
      updateLabel();
      dropdown.querySelectorAll(".fa-tp-option").forEach(function(o){o.classList.toggle("selected",o.dataset.value===input.value);});
    });
  }
  document.querySelectorAll("input.fa-time-picker").forEach(initTimePicker);
})();

/* ---------- Pagination Persistence ---------- */
(function(){
  var KEY="eric_attendance_pending";
  var form=document.querySelector('form[action*="mark_attendance"]');
  if (!form) return;
  document.querySelectorAll(".za-page-link").forEach(function(link){
    link.addEventListener("click",function(e){
      var rows=form.querySelectorAll("tbody tr"), data={};
      rows.forEach(function(row){
        var fid=row.querySelector("input[name=faculty_id]");
        if (!fid) return;
        var ci=row.querySelector(".za-ti-ci"), co=row.querySelector(".za-ti-co");
        var sel=row.querySelector("select");
        data[fid.value]={ci:ci?ci.value:"", co:co?co.value:"", st:sel?sel.value:""};
      });
      if (Object.keys(data).length) try{localStorage.setItem(KEY,JSON.stringify(data));}catch(e){}
    });
  });
  try{
    var saved=JSON.parse(localStorage.getItem(KEY));
    if (saved) {
      form.querySelectorAll("tbody tr").forEach(function(row){
        var fid=row.querySelector("input[name=faculty_id]");
        if (!fid||!saved[fid.value]) return;
        var d=saved[fid.value];
        var ci=row.querySelector(".za-ti-ci"), co=row.querySelector(".za-ti-co");
        var sel=row.querySelector("select[name='status']");
        if (ci&&d.ci){ci.value=d.ci;ci.dispatchEvent(new Event("change",{bubbles:true}));}
        if (co&&d.co){co.value=d.co;co.dispatchEvent(new Event("change",{bubbles:true}));}
        if (sel&&d.st){sel.value=d.st;sel.dispatchEvent(new Event("change",{bubbles:true}));}
      });
      localStorage.removeItem(KEY);
    }
  }catch(e){}
})();

/* ---------- Select All & Bulk Actions ---------- */
(function(){
  var selectAll=document.getElementById("zaSelectAll");
  var bulkBar=document.getElementById("zaBulk");
  var bulkCount=document.getElementById("zaBulkCount");
  var bulkClear=document.getElementById("zaBulkClear");
  if (!selectAll||!bulkBar||!bulkCount) return;
  window.zaForceScrollReflow = function(){
    var el = document.querySelector(".za-table-scroll");
    if (!el) return;
    el.style.overflowX = "hidden";
    el.scrollTop;
    requestAnimationFrame(function(){ el.style.overflowX = "auto"; });
  };
  var zaForceScrollReflow = window.zaForceScrollReflow;
  function updateBulkBar(){
    var checks=document.querySelectorAll(".za-row-chk:checked");
    var n=checks.length;
    bulkCount.textContent=n+" selected";
    if (n>0) {
      bulkBar.classList.remove("za-bulk-hidden");
      bulkBar.style.display="flex";
    } else {
      bulkBar.classList.add("za-bulk-hidden");
      bulkBar.style.display="none";
    }
    zaForceScrollReflow();
  }
  selectAll.addEventListener("change",function(){
    document.querySelectorAll(".za-row-chk").forEach(function(cb){cb.checked=selectAll.checked;});
    updateBulkBar();
  });
  document.addEventListener("change",function(e){
    if (e.target.classList.contains("za-row-chk")){
      var all=document.querySelectorAll(".za-row-chk");
      var checked=document.querySelectorAll(".za-row-chk:checked");
      selectAll.checked=all.length>0&&all.length===checked.length;
      updateBulkBar();
    }
  });
  document.querySelectorAll(".za-bulk-btn[data-status]").forEach(function(btn){
    btn.addEventListener("click",function(){
      var status=btn.getAttribute("data-status");
      document.querySelectorAll(".za-row-chk:checked").forEach(function(cb){
        var tr=cb.closest("tr");
        if (!tr) return;
        var sel=tr.querySelector("select[name='status']");
        if (sel) { sel.value=status; sel.dispatchEvent(new Event("change",{bubbles:true})); }
      });
    });
  });
  var bulkCi=document.getElementById("zaBulkCi");
  var bulkCo=document.getElementById("zaBulkCo");
  function zaSetInputValue(inp, val){
    if (!inp) return;
    inp.value = val || "";
    inp.dispatchEvent(new Event("input",{bubbles:true}));
    inp.dispatchEvent(new Event("change",{bubbles:true}));
  }
  function setBulkTime(name, val){
    document.querySelectorAll(".za-row-chk:checked").forEach(function(cb){
      var tr=cb.closest("tr");
      if (!tr) return;
      var cls = name === "check_in" ? "za-ti-ci" : "za-ti-co";
      zaSetInputValue(tr.querySelector("."+cls), val);
    });
  }
  if (bulkCi) bulkCi.addEventListener("change",function(){setBulkTime("check_in", bulkCi.value);});
  if (bulkCo) bulkCo.addEventListener("change",function(){setBulkTime("check_out", bulkCo.value);});
  if (bulkClear){
    bulkClear.addEventListener("click",function(){
      document.querySelectorAll(".za-row-chk:checked").forEach(function(cb){
        cb.checked=false;
        var tr=cb.closest("tr");
        if (!tr) return;
        zaSetInputValue(tr.querySelector(".za-ti-ci"), "");
        zaSetInputValue(tr.querySelector(".za-ti-co"), "");
        var sel=tr.querySelector("select[name='status']");
        if (sel){sel.value="";sel.dispatchEvent(new Event("change",{bubbles:true}));}
      });
      selectAll.checked=false; updateBulkBar();
    });
  }
})();

/* ---------- Native select helpers for edit-mode inputs ---------- */
function zaPopulateTimeSelect(sel){
  if (sel._zaPopulated) return;
  var min = sel.getAttribute('data-min') || '00:00';
  var max = sel.getAttribute('data-max') || '23:59';
  if (!toMins) return;
  var val = sel.value;
  sel.innerHTML = '';
  var minM = toMins(min) || 0, maxM = toMins(max) || 1439;
  for (var m = minM; m <= maxM; m += 5) {
    var h = Math.floor(m/60), i = m%60;
    var v = String(h).padStart(2,'0') + ':' + String(i).padStart(2,'0');
    var opt = document.createElement('option');
    opt.value = v; opt.textContent = v;
    if (v === val) opt.selected = true;
    sel.appendChild(opt);
  }
  sel._zaPopulated = true;
}
function zaInitEditChoices(){
  document.querySelectorAll('.za-edit-mode.za-ti-ci, .za-edit-mode.za-ti-co').forEach(function(el){
    if (el.tagName === 'SELECT') zaPopulateTimeSelect(el);
  });
}
function zaDestroyEditChoices(){
  document.querySelectorAll('.za-edit-mode.za-ti-ci, .za-edit-mode.za-ti-co').forEach(function(el){
    if (el._zaPopulated) {
      el._zaPopulated = false;
    }
  });
}

/* ---------- Bulk Edit Toggle ---------- */
(function(){
  var btn = document.getElementById("zaBulkEditToggle");
  var form = document.getElementById("attendanceForm");
  if (!btn || !form) return;
  var isEdit = false;
  var editUrl = btn.getAttribute("data-edit-url");
  var viewUrl = btn.getAttribute("data-view-url");

  btn.addEventListener("click", function(){
    isEdit = !isEdit;
    var rows = form.querySelectorAll("tr[data-record-exists]");

    if (isEdit) {
      form.classList.add("za-edit-active");
      btn.querySelector("span").textContent = "Cancel Edit";
      form.action = editUrl;

      rows.forEach(function(tr){
        var ciHidden = tr.querySelector("input.za-ci-hidden");
        var coHidden = tr.querySelector("input.za-co-hidden");
        var ciEdit = tr.querySelector(".za-edit-mode[name=edit_check_in]");
        var coEdit = tr.querySelector(".za-edit-mode[name=edit_check_out]");
        var sel = tr.querySelector("select[name=status]");

        if (ciHidden) ciHidden.name = "orig_check_in";
        if (ciEdit) { ciEdit.name = "check_in"; ciEdit.value = ciHidden ? ciHidden.value : ciEdit.value; }
        if (coHidden) coHidden.name = "orig_check_out";
        if (coEdit) { coEdit.name = "check_out"; coEdit.value = coHidden ? coHidden.value : coEdit.value; }
        if (sel) sel.disabled = false;
      });
      zaInitEditChoices();
      zaForceScrollReflow();
    } else {
      form.classList.remove("za-edit-active");
      btn.querySelector("span").textContent = "Bulk Edit";
      form.action = viewUrl;

      rows.forEach(function(tr){
        var ciHidden = tr.querySelector("input[name=orig_check_in]");
        var coHidden = tr.querySelector("input[name=orig_check_out]");
        var ciEdit = tr.querySelector(".za-edit-mode[name=check_in]");
        var coEdit = tr.querySelector(".za-edit-mode[name=check_out]");
        var sel = tr.querySelector("select[name=status]");

        if (ciHidden) ciHidden.name = "check_in";
        if (ciEdit) ciEdit.name = "edit_check_in";
        if (coHidden) coHidden.name = "check_out";
        if (coEdit) coEdit.name = "edit_check_out";
        if (sel) sel.disabled = true;
      });
      zaDestroyEditChoices();
      zaForceScrollReflow();
    }
  });
})();

/* ---------- Attendance select menu portal ---------- */
(function(){
  var root = document.querySelector(".za-root");
  if (!root) return;
  var menu = null, activeSelect = null;

  // Native select focus scrolls its nearest horizontal scroller so the control
  // is visible.  That is jarring in the attendance table: opening a picker
  // appears to move the entire table.  Keep the current scroll position while
  // the portal menu is opened and while focus is returned to the select.
  function preserveTableScroll(select, callback){
    var scroller = select && select.closest(".za-table-scroll");
    if (!scroller) {
      callback();
      return;
    }
    var left = scroller.scrollLeft;
    callback();
    requestAnimationFrame(function(){ scroller.scrollLeft = left; });
  }

  function closeMenu(){
    if (menu) menu.remove();
    menu = null;
    activeSelect = null;
  }

  function positionMenu(){
    if (!menu || !activeSelect) return;
    var rect = activeSelect.getBoundingClientRect();
    var gutter = 8;
    var width = Math.max(rect.width, 132);
    var height = Math.min(menu.scrollHeight, 260);
    var left = Math.max(gutter, Math.min(rect.left, window.innerWidth - width - gutter));
    var spaceBelow = window.innerHeight - rect.bottom - gutter;
    var spaceAbove = rect.top - gutter;
    // Prefer the side that can show the whole list. If neither can, use the
    // larger side and make the menu itself scroll instead of letting it run
    // underneath the table header/footer.
    var openAbove = spaceBelow < height && spaceAbove > spaceBelow;
    var availableSpace = openAbove ? spaceAbove : spaceBelow;
    menu.style.width = width + "px";
    menu.style.maxHeight = Math.max(72, Math.min(height, availableSpace)) + "px";
    menu.style.left = left + "px";
    menu.style.top = (openAbove ? Math.max(gutter, rect.top - menu.offsetHeight - 4) : rect.bottom + 4) + "px";
    menu.classList.toggle("za-select-menu--up", openAbove);
  }

  function openMenu(select){
    // Touch devices can emit both touchstart and pointerdown for one tap.
    // Keep the portal open rather than toggling it closed on the second event.
    if (activeSelect === select && menu) return;
    closeMenu();
    activeSelect = select;
    menu = document.createElement("div");
    menu.className = "za-select-menu";
    menu.setAttribute("role", "listbox");

    Array.from(select.options).forEach(function(option){
      var item = document.createElement("button");
      item.type = "button";
      item.className = "za-select-menu__option";
      item.textContent = option.textContent;
      item.disabled = option.disabled;
      item.setAttribute("role", "option");
      item.setAttribute("aria-selected", option.value === select.value ? "true" : "false");
      if (option.value === select.value) item.classList.add("is-selected");
      item.addEventListener("click", function(){
        if (option.disabled) return;
        select.value = option.value;
        select.dispatchEvent(new Event("change", {bubbles: true}));
        select.dispatchEvent(new Event("input", {bubbles: true}));
        // The portal is a button-based menu, so do not return focus to the
        // native select. Its focus makes browsers scroll the table to the
        // status/check-in column.
        preserveTableScroll(select, function(){
          closeMenu();
        });
      });
      menu.appendChild(item);
    });
    document.body.appendChild(menu);
    positionMenu();
    var selected = menu.querySelector(".is-selected");
    if (selected) selected.scrollIntoView({block: "nearest"});
  }

  function openSelectMenu(event){
    var select = event.target.closest("select");
    if (!select || select.disabled) return;
    event.preventDefault();
    event.stopPropagation();
    preserveTableScroll(select, function(){ openMenu(select); });
  }

  root.addEventListener("pointerdown", openSelectMenu, true);
  // Some mobile WebViews dispatch touchstart without pointer events. Handling
  // it in the capture phase prevents their native, clipped select sheet.
  root.addEventListener("touchstart", openSelectMenu, {capture: true, passive: false});
  // Touch browsers can still dispatch a follow-up click after pointerdown.
  // Suppress that click so the clipped native option list never opens behind
  // the table footer; the body-level portal above is the only menu shown.
  root.addEventListener("click", function(event){
    var select = event.target.closest("select");
    if (!select || select.disabled) return;
    event.preventDefault();
    event.stopPropagation();
  }, true);
  document.addEventListener("pointerdown", function(event){
    if (menu && !menu.contains(event.target) && event.target !== activeSelect) closeMenu();
  });
  document.addEventListener("keydown", function(event){
    if (event.key === "Escape") closeMenu();
  });
  window.addEventListener("resize", positionMenu);
  window.addEventListener("scroll", positionMenu, true);
})();

/* ---------- Live Auto-Status on CI/CO Change ---------- */
(function(){
  document.addEventListener("change", function(e){
    if (!e.target.classList.contains("za-ti-ci") && !e.target.classList.contains("za-ti-co")) return;
    var tr = e.target.closest("tr");
    if (!tr) return;
    var sel = tr.querySelector("select[name='status']");
    if (!sel) return;
    var ci = tr.querySelector(".za-ti-ci");
    var co = tr.querySelector(".za-ti-co");
    if (e.target.classList.contains("za-ti-ci") && ci && ci.value) {
      var ciM = toMins(ci.value), ciEnd = toMins(ci.getAttribute("data-ci-end"));
      sel.value = (ciM && ciEnd && ciM > ciEnd) ? "LATE" : "PRESENT";
      sel.dispatchEvent(new Event("change", {bubbles: true}));
    } else if (e.target.classList.contains("za-ti-ci") && ci && !ci.value) {
      if (sel.value === "PRESENT" || sel.value === "LATE") {
        sel.value = "";
        sel.dispatchEvent(new Event("change", {bubbles: true}));
      }
    }
    if (e.target.classList.contains("za-ti-co") && co && !co.value && ci && ci.value) {
      sel.value = "PRESENT";
      sel.dispatchEvent(new Event("change", {bubbles: true}));
    }
  });
})();
