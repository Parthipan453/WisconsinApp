(function(){
  "use strict";

  /* ---------------------------------------------------------
     Hospital context (in a Django integration this would be
     rendered server-side / pulled from the page context)
  --------------------------------------------------------- */
  var HOSPITAL = { id:"HOSP-0042", name:"Riverbend General Hospital" };

  /* ---------------------------------------------------------
     In-memory ambulance store (replace with API calls)
  --------------------------------------------------------- */

function getCsrfToken() {
    const token = document.querySelector(
        '#ambForm input[name="csrfmiddlewaretoken"]'
    );

    return token ? token.value : "";
}

var ambulances = Array.isArray(window.INITIAL_AMBULANCES)
    ? window.INITIAL_AMBULANCES
    : [];

  var editingId = null;
  var pendingAction = null; // { type:'deactivate'|'delete'|'activate', id:'...' }

  /* ---------------------------------------------------------
     Element refs
  --------------------------------------------------------- */
  var statsEl = document.getElementById("ambStats");
  var gridEl = document.getElementById("ambFleetGrid");
  var emptyEl = document.getElementById("ambEmptyState");
  var countEl = document.getElementById("ambFleetCount");
  var searchInput = document.getElementById("ambSearchInput");
  var toastStack = document.getElementById("ambToastStack");

  var formModalEl = document.getElementById("ambFormModal");
  var formModal = new bootstrap.Modal(formModalEl);
  var confirmModalEl = document.getElementById("ambConfirmModal");
  var confirmModal = new bootstrap.Modal(confirmModalEl);

  var form = document.getElementById("ambForm");
  var modalEyebrow = document.getElementById("ambModalEyebrow");
  var modalTitle = document.getElementById("ambFormModalTitle");
  var saveBtnLabel = document.getElementById("ambSaveBtnLabel");

  var STATUS_META = {
    available:      { label:"Available",           badge:"amb-badge-available",    dotIcon:"fa-solid fa-circle-check", lb:false },
    dispatched:     { label:"On Duty",              badge:"amb-badge-dispatched",   dotIcon:"fa-solid fa-circle",       lb:true  },
    maintenance:    { label:"Maintenance",          badge:"amb-badge-maintenance",  dotIcon:"fa-solid fa-wrench",       lb:false },
    reserved:       { label:"Reserved",             badge:"amb-badge-reserved",     dotIcon:"fa-solid fa-clock",        lb:false },
    outofservice:   { label:"Out of Service",       badge:"amb-badge-outofservice", dotIcon:"fa-solid fa-ban",          lb:false }
  };

  function esc(str){
    return String(str == null ? "" : str)
      .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
  }
  function fmtDate(iso){
    if(!iso) return "—";
    var d = new Date(iso + "T00:00:00");
    if(isNaN(d.getTime())) return "—";
    return d.toLocaleDateString("en-US", { month:"short", day:"numeric", year:"numeric" });
}

  /* ---------------------------------------------------------
     Rendering: stats
  --------------------------------------------------------- */
  function renderStats(){
    var total = ambulances.length;
    var counts = { available:0, dispatched:0, maintenance:0, outofservice:0, reserved:0 };
    ambulances.forEach(function(a){ counts[a.status] = (counts[a.status]||0)+1; });

    var cards = [
      { cls:"amb-stat-total", label:"Total fleet", value:total, icon:"fa-solid fa-truck-medical" },
      { cls:"amb-stat-available", label:"Available", value:counts.available, icon:"fa-solid fa-circle-check" },
      { cls:"amb-stat-dispatched", label:"On duty", value:counts.dispatched, icon:"fa-solid fa-truck-fast" },
      { cls:"amb-stat-maintenance", label:"Maintenance", value:counts.maintenance, icon:"fa-solid fa-wrench" },
      { cls:"amb-stat-outofservice", label:"Out of service", value:counts.outofservice, icon:"fa-solid fa-ban" }
    ];

    statsEl.innerHTML = cards.map(function(c){
        return (
            '<div class="amb-stat-card '+c.cls+'">'+
                '<div class="amb-stat-top">'+
                    '<div class="amb-stat-icon"><i class="'+c.icon+'"></i></div>'+
                '</div>'+
                '<div class="amb-stat-num">'+c.value+'</div>'+
                '<div class="amb-stat-label">'+c.label+'</div>'+
            '</div>'
        );
        }).join("");
    }

    /* ---------------------------------------------------------
    Rendering: fleet grid
  --------------------------------------------------------- */
    function getFiltered(){
        var q = (searchInput.value || "").trim().toLowerCase();
        var status = statusFilterChoice ? statusFilterChoice.getValue(true) : document.getElementById("ambStatusFilter").value;
        return ambulances.filter(function(a){
        var matchesStatus = status === "all" || a.status === status;
        var haystack = [a.unitNumber,a.plate,a.vin,a.model,a.make].join(" ").toLowerCase();
        var matchesQuery = q === "" || haystack.indexOf(q) !== -1;
        return matchesStatus && matchesQuery;
        });
    }

  function cardTemplate(a){
    var meta = STATUS_META[a.status] || STATUS_META.available;
    var lightbarClass = "amb-card-lightbar";
    if(meta.lb) lightbarClass += " is-pulse";
    if(a.status === "available") lightbarClass += " lb-available";
    else if(a.status === "maintenance") lightbarClass += " lb-maintenance";
    else if(a.status === "outofservice") lightbarClass += " lb-outofservice";
    else if(a.status === "reserved") lightbarClass += " lb-reserved";

    var isOut = a.status === "outofservice";
    var toggleLabel = isOut ? "Activate" : "Deactivate";
    var toggleIcon = isOut ? "fa-solid fa-power-off" : "fa-solid fa-ban";

    return (
      '<article class="amb-card" data-id="'+esc(a.id)+'">'+
        '<div class="'+lightbarClass+'"></div>'+
        '<div class="amb-card-body">'+
          '<div class="amb-card-top">'+
            '<div class="amb-card-idblock">'+
              '<div class="amb-card-icon"><i class="fa-solid fa-truck-medical"></i></div>'+
              '<div class="amb-card-title-wrap">'+
                '<div class="amb-card-unit">'+esc(a.unitNumber)+'</div>'+
                '<div class="amb-card-plate">'+esc(a.plate)+'</div>'+
              '</div>'+
            '</div>'+            '<span class="amb-badge '+meta.badge+'"><i class="'+meta.dotIcon+'"></i>'+meta.label+'</span>'+
          '</div>'+

          '<div class="amb-card-service"><i class="fa-solid fa-notes-medical"></i><span>'+esc(a.serviceType)+'</span></div>'+

          '<div class="amb-card-specs">'+
            '<div class="amb-spec"><div class="amb-spec-label">Vehicle</div><div class="amb-spec-value">'+esc(a.make)+' '+esc(a.model)+'</div></div>'+
            '<div class="amb-spec"><div class="amb-spec-label">VIN</div><div class="amb-spec-value is-mono">'+esc(a.vin)+'</div></div>'+
            '<div class="amb-spec"><div class="amb-spec-label">Next maintenance</div><div class="amb-spec-value">'+fmtDate(a.nextMaint)+'</div></div>'+
          '</div>'+

          '<div class="amb-card-people">'+
            '<div class="amb-people-row"><i class="fa-solid fa-phone-volume"></i><span>Dispatch: '+esc(a.dispatchPhone)+'</span></div>'+
            (a.altContact ? '<div class="amb-people-row"><i class="fa-solid fa-phone"></i><span>Alt. contact: '+esc(a.altContact)+'</span></div>' : '')+
          '</div>'+
        '</div>'+
        '<div class="amb-card-actions">'+
          '<button class="amb-btn amb-btn-outline amb-edit-btn" '+
          'type="button" data-id="'+esc(a.id)+'">'+
            '<i class="fa-solid fa-pen"></i>'+
            '<span class="amb-btn-label">Edit</span>'+
          '</button>'+

          '<button class="amb-btn amb-btn-danger-ghost amb-toggle-btn" '+
          'type="button" data-id="'+esc(a.id)+'">'+
            '<i class="'+toggleIcon+'"></i>'+
            '<span class="amb-btn-label">'+toggleLabel+'</span>'+
          '</button>'+

        '</div>'+
      '</article>'
    );
  }

  function renderGrid(){
    var list = getFiltered();
    countEl.textContent = ambulances.length + (ambulances.length === 1 ? " vehicle" : " vehicles") + (list.length !== ambulances.length ? " · " + list.length + " shown" : "");

    if(ambulances.length === 0){
      gridEl.hidden = true;
      emptyEl.hidden = false;
      gridEl.innerHTML = "";
      return;
    }
    emptyEl.hidden = true;
    gridEl.hidden = false;

    if(list.length === 0){
      gridEl.innerHTML = '<div class="amb-empty amb-empty-inline"><div class="amb-empty-icon"><i class="fa-solid fa-magnifying-glass"></i></div><h3>No matches</h3><p>No ambulances match your search or filter. Try adjusting them.</p></div>';
      return;
    }
    gridEl.innerHTML = list.map(cardTemplate).join("");
  }

  function renderAll(){
    renderStats();
    renderGrid();
  }

  /* ---------------------------------------------------------
     Toasts
  --------------------------------------------------------- */
  function showToast(title, msg, isError){
    var el = document.createElement("div");
    el.className = "amb-toast" + (isError ? " is-error" : "");
    el.innerHTML =
      '<i class="amb-toast-icon fa-solid '+(isError ? 'fa-triangle-exclamation' : 'fa-circle-check')+'"></i>'+
      '<div class="amb-toast-text"><b>'+esc(title)+'</b><span>'+esc(msg)+'</span></div>'+
      '<button class="amb-toast-close" type="button" aria-label="Dismiss"><i class="fa-solid fa-xmark"></i></button>';
    toastStack.appendChild(el);
    var remove = function(){ el.style.animation = "amb-toast-in .2s ease reverse"; setTimeout(function(){ el.remove(); }, 180); };
    el.querySelector(".amb-toast-close").addEventListener("click", remove);
    setTimeout(remove, 4200);
  }

/* ---------------------------------------------------------
   Choices.js — init all dropdowns
--------------------------------------------------------- */
var choiceInstances = {};

function initChoices(id, opts) {
  var el = document.getElementById(id);
  if (!el) return null;

  // Read native <option> elements BEFORE Choices modifies the select
  var nativeChoices = Array.from(el.options).map(function (option) {
    return {
      value: option.value,
      label: option.textContent.trim(),
      selected: option.selected,
      disabled: option.disabled
    };
  });

  var instance = new Choices(
    el,
    Object.assign(
      {
        shouldSort: false,
        itemSelectText: "",
        allowHTML: false,
        searchEnabled: false,
        placeholderValue: null,
        choices: nativeChoices,
        classNames: {
          containerOuter: "choices"
        }
      },
      opts || {}
    )
  );

  choiceInstances[id] = instance;
  return instance;
}

  var fServiceTypeChoice = initChoices("fServiceType");
  var fStatusChoice      = initChoices("fStatus");
  var statusFilterChoice = initChoices("ambStatusFilter", { searchEnabled:false });

  statusFilterChoice.passedElement.element.addEventListener("change", renderGrid);

  /* ---------------------------------------------------------
     Flatpickr — next maintenance date
  --------------------------------------------------------- */
  var nextMaintPicker = flatpickr("#fNextMaint", {
      dateFormat: "Y-m-d",
      altInput: true,
      altFormat: "M j, Y",
      allowInput: false,
      disableMobile: true,
      minDate: "today"
  });

 /* ---------------------------------------------------------
   COMPLETE FORM VALIDATION
--------------------------------------------------------- */

var FIELDS = [
    {
        id: "fUnitNumber",
        required: true,
        kind: "input",

        sanitize: function (value) {
            return value
                .replace(/[^A-Za-z0-9 -]/g, "")
                .replace(/\s{2,}/g, " ")
                .replace(/-{2,}/g, "-");
        },

        validate: function (value) {
            value = value.trim();

            return (
                value.length >= 2 &&
                value.length <= 20 &&
                /^[A-Za-z0-9]+(?:[ -][A-Za-z0-9]+)*$/.test(value)
            );
        },

        message:
            "Use 2–20 characters with letters, numbers, spaces and hyphens only."
    },

    {
        id: "fPlate",
        required: true,
        kind: "input",

        sanitize: function (value) {
            return value
                .toUpperCase()
                .replace(/[^A-Z0-9 -]/g, "")
                .replace(/\s{2,}/g, " ")
                .replace(/-{2,}/g, "-");
        },

        validate: function (value) {
            value = value.trim();

            return (
                value.length >= 2 &&
                value.length <= 20 &&
                /^[A-Z0-9]+(?:[ -][A-Z0-9]+)*$/.test(value)
            );
        },

        message:
            "Use a valid registration number with letters, numbers, spaces or hyphens."
    },

    {
        id: "fVin",
        required: true,
        kind: "input",

        sanitize: function (value) {
            return value
                .toUpperCase()
                .replace(/[^A-HJ-NPR-Z0-9]/g, "")
                .slice(0, 17);
        },

        validate: function (value) {
            return /^[A-HJ-NPR-Z0-9]{17}$/.test(
                value.trim().toUpperCase()
            );
        },

        message:
            "VIN must contain exactly 17 valid characters."
    },

    {
        id: "fMake",
        required: true,
        kind: "input",

        sanitize: function (value) {
            return value
                .replace(/[^A-Za-z0-9 &'.,-]/g, "")
                .replace(/\s{2,}/g, " ");
        },

        validate: function (value) {
            value = value.trim();

            return (
                value.length >= 2 &&
                value.length <= 50 &&
                /^[A-Za-z0-9]+(?:[ &'.,-][A-Za-z0-9]+)*$/.test(value)
            );
        },

        message: "Enter a valid vehicle make."
    },

    {
        id: "fModel",
        required: true,
        kind: "input",

        sanitize: function (value) {
            return value
                .replace(/[^A-Za-z0-9 &'.,-]/g, "")
                .replace(/\s{2,}/g, " ");
        },

        validate: function (value) {
            value = value.trim();

            return (
                value.length >= 1 &&
                value.length <= 50 &&
                /^[A-Za-z0-9]+(?:[ &'.,-][A-Za-z0-9]+)*$/.test(value)
            );
        },

        message: "Enter a valid vehicle model."
    },

    {
        id: "fServiceType",
        required: true,
        kind: "choice"
    },

    {
        id: "fStatus",
        required: true,
        kind: "choice"
    },

    {
        id: "fDispatchPhone",
        required: true,
        kind: "input",

        sanitize: function (value) {
            return value.replace(/[^0-9+()\-\s]/g, "");
        },

        validate: function (value) {
            return isValidPhone(value);
        },

        message:
            "Enter a valid phone number containing 7–15 digits."
    }
];


/* ---------------------------------------------------------
   PHONE HELPERS
--------------------------------------------------------- */

function normalizePhone(value) {
    return (value || "").replace(/\D/g, "");
}


function isValidPhone(value) {

    var trimmed = (value || "").trim();

    // Empty is invalid for dispatch
    if (!trimmed) {
        return false;
    }

    // Only phone formatting characters allowed
    if (!/^[0-9+()\-\s]+$/.test(trimmed)) {
        return false;
    }

    var digits = normalizePhone(trimmed);

    return digits.length >= 7 && digits.length <= 15;
}


/* ---------------------------------------------------------
   ALTERNATE CONTACT
--------------------------------------------------------- */

function validateAlternativePhone() {

    var input = document.getElementById("fAltContact");

    if (!input) {
        return true;
    }

    var value = input.value.trim();

    // Optional
    if (!value) {
        clearCustomError(input);
        return true;
    }

    if (!isValidPhone(value)) {

        setCustomError(
            input,
            "Enter a valid phone number containing 7–15 digits."
        );

        return false;
    }

    var dispatchDigits = normalizePhone(
        document.getElementById("fDispatchPhone").value
    );

    var alternativeDigits = normalizePhone(value);

    if (
        dispatchDigits &&
        dispatchDigits === alternativeDigits
    ) {

        setCustomError(
            input,
            "Alternative contact must be different from dispatch number."
        );

        return false;
    }

    clearCustomError(input);

    return true;
}


/* ---------------------------------------------------------
   CUSTOM ERROR HELPERS
--------------------------------------------------------- */

function updateErrorMessage(input, message) {
    var wrap = fieldWrap(input);

    if (!wrap) {
        return;
    }

    var errorEl = wrap.querySelector(".amb-error-msg");

    if (!errorEl) {
        return;
    }

    var icon = errorEl.querySelector("i");

    errorEl.innerHTML = "";

    if (icon) {
        errorEl.appendChild(icon);
    }

    errorEl.appendChild(
        document.createTextNode(" " + message)
    );
}

function setCustomError(input, message) {

    var wrap = fieldWrap(input);

    if (wrap) {
        wrap.classList.add("has-error");
    }

    input.classList.add("is-invalid");

    input.setAttribute(
        "data-validation-error",
        message
    );

    updateErrorMessage(input, message);
}


function clearCustomError(input) {

    var wrap = fieldWrap(input);

    if (!wrap) {
        return;
    }

    wrap.classList.remove("has-error");
    input.classList.remove("is-invalid");

    input.removeAttribute("data-validation-error");

    var errorMsg = wrap.querySelector(".amb-error-msg");

    if (errorMsg) {

        var textSpan = errorMsg.querySelector("span");

        if (textSpan) {
            textSpan.textContent =
                "Enter a valid alternative contact number.";
        }
    }
}


/* ---------------------------------------------------------
   FIELD HELPERS
--------------------------------------------------------- */

function getChoiceInstance(def) {
      if (!def || !def.instance) {
          return null;
      }

      // If instance is a function
      if (typeof def.instance === "function") {
          return def.instance();
      }

      // If instance is already a Choices instance
      return def.instance;
  }

function fieldWrap(el) {
    return el ? el.closest(".amb-field") : null;
}


function clearFieldError(def) {

    var el = document.getElementById(def.id);

    if (!el) {
        return;
    }

    var wrap = fieldWrap(el);

    if (wrap) {
        wrap.classList.remove("has-error");
    }

    if (def.kind === "choice") {

        var inst = null;

        if (typeof def.instance === "function") {
            inst = def.instance();
        } else {
            inst = def.instance;
        }

        if (
            inst &&
            inst.containerOuter &&
            inst.containerOuter.element
        ) {
            inst.containerOuter.element.classList.remove(
                "is-invalid"
            );
        }

    } else {

        el.classList.remove("is-invalid");
    }
}


function setFieldError(def) {

    var el = document.getElementById(def.id);

    if (!el) {
        return;
    }

    var wrap = fieldWrap(el);

    if (wrap) {
        wrap.classList.add("has-error");

        if (def.message) {
            updateErrorMessage(el, def.message);
        }
    }

    if (def.kind === "choice") {

        var inst = getChoiceInstance(def);

        if (
            inst &&
            inst.containerOuter &&
            inst.containerOuter.element
        ) {
            inst.containerOuter.element.classList.add(
                "is-invalid"
            );
        }

    } else {

        el.classList.add("is-invalid");
    }
}


/* ---------------------------------------------------------
   CHOICE VALIDATION
--------------------------------------------------------- */

function validateChoice(def) {

    var el = document.getElementById(def.id);

    if (!el) {
        return false;
    }

    var value = el.value;

    if (def.required && !value) {
        setFieldError(def);
        return false;
    }

    // Make sure selected value actually exists
    var validOption = Array.from(el.options).some(
        function (option) {
            return (
                option.value === value &&
                !option.disabled
            );
        }
    );

    if (!validOption) {
        setFieldError(def);
        return false;
    }

    clearFieldError(def);

    return true;
}


/* ---------------------------------------------------------
   NORMAL FIELD VALIDATION
--------------------------------------------------------- */

function validateField(def) {

    var el = document.getElementById(def.id);

    if (!el) {
        return false;
    }

    if (def.kind === "choice") {
        return validateChoice(def);
    }

    var value = el.value || "";

    if (
        def.required &&
        value.trim() === ""
    ) {
        setFieldError(def);
        return false;
    }

    if (
        value.trim() !== "" &&
        def.validate &&
        !def.validate(value)
    ) {
        setFieldError(def);
        return false;
    }

    clearFieldError(def);

    return true;
}


/* ---------------------------------------------------------
   DUPLICATE VALIDATION
--------------------------------------------------------- */

function validateDuplicateField(inputId) {

    var input = document.getElementById(inputId);

    if (!input) {
        return true;
    }

    var value = input.value.trim();

    if (!value) {
        return true;
    }

    var duplicate = false;
    var message = "";

    if (inputId === "fUnitNumber") {

        duplicate = ambulances.some(function (a) {

            return (
                a.id !== editingId &&
                (a.unitNumber || "")
                    .trim()
                    .toLowerCase() ===
                value.toLowerCase()
            );
        });

        message =
            "This unit number is already registered.";

    }

    else if (inputId === "fPlate") {

        duplicate = ambulances.some(function (a) {

            return (
                a.id !== editingId &&
                (a.plate || "")
                    .trim()
                    .toUpperCase() ===
                value.toUpperCase()
            );
        });

        message =
            "This license plate is already registered.";

    }

    else if (inputId === "fVin") {

        duplicate = ambulances.some(function (a) {

            return (
                a.id !== editingId &&
                (a.vin || "")
                    .trim()
                    .toUpperCase() ===
                value.toUpperCase()
            );
        });

        message =
            "This VIN is already registered.";
    }

    if (duplicate) {

        setCustomError(input, message);

        return false;
    }

    clearCustomError(input);

    return true;
}


/* ---------------------------------------------------------
   MAINTENANCE DATE VALIDATION
--------------------------------------------------------- */

function validateMaintenanceDate() {

    var input =
        document.getElementById("fNextMaint");

    if (!input || !input.value) {
        return true;
    }

    var selected = new Date(
        input.value + "T00:00:00"
    );

    if (isNaN(selected.getTime())) {
        return false;
    }

    var today = new Date();

    today.setHours(0, 0, 0, 0);

    return selected >= today;
}


/* ---------------------------------------------------------
   COMPLETE FORM VALIDATION
--------------------------------------------------------- */

function validateForm() {

    var allOk = true;

    FIELDS.forEach(function (def) {

        if (!validateField(def)) {
            allOk = false;
        }
    });


    // Duplicate checks
    [
        "fUnitNumber",
        "fPlate",
        "fVin"
    ].forEach(function (id) {

        if (!validateDuplicateField(id)) {
            allOk = false;
        }
    });


    // Phones
    if (!validatePhoneFields()) {
        allOk = false;
    }


    // Maintenance date
    if (!validateMaintenanceDate()) {

        var dateInput =
            document.getElementById("fNextMaint");

        if (dateInput) {
            dateInput.classList.add("is-invalid");
        }

        allOk = false;

    } else {

        var dateInput =
            document.getElementById("fNextMaint");

        if (dateInput) {
            dateInput.classList.remove("is-invalid");
        }
    }


    return allOk;
}



  /* ---------------------------------------------------------
   REALTIME VALIDATION
--------------------------------------------------------- */

FIELDS.forEach(function (def) {

    var el = document.getElementById(def.id);

    if (!el) return;


    /* -----------------------------------------
       CHOICES
    ----------------------------------------- */

    if (def.kind === "choice") {

        el.addEventListener("change", function () {

            validateField(def);

        });

        return;
    }


    /* -----------------------------------------
       INPUT
    ----------------------------------------- */

    el.addEventListener("input", function () {

        // Sanitize BEFORE validation
        if (def.sanitize) {

            var oldValue = this.value;
            var newValue = def.sanitize(oldValue);

            if (oldValue !== newValue) {

                this.value = newValue;
            }
        }


        // Normal validation
        validateField(def);


        // Duplicate validation
        if (
            def.id === "fUnitNumber" ||
            def.id === "fPlate" ||
            def.id === "fVin"
        ) {

            validateDuplicateField(def.id);
        }


        // Phone validation
        if (def.id === "fDispatchPhone") {
            validateAlternativePhone();
        }
    });


    el.addEventListener("blur", function () {

        validateField(def);


        if (
            def.id === "fUnitNumber" ||
            def.id === "fPlate" ||
            def.id === "fVin"
        ) {

            validateDuplicateField(def.id);
        }


        if (def.id === "fDispatchPhone") {
            validateAlternativePhone();
        }
    });
});


/* ---------------------------------------------------------
   ALTERNATIVE CONTACT
--------------------------------------------------------- */

var altContactInput =
    document.getElementById("fAltContact");

if (altContactInput) {

    altContactInput.addEventListener(
        "input",
        function () {

            this.value = this.value.replace(
                /[^0-9+()\-\s]/g,
                ""
            );

            validateAlternativePhone();
        }
    );


    altContactInput.addEventListener(
        "blur",
        function () {

            validateAlternativePhone();
        }
    );
}


/* ---------------------------------------------------------
   NEXT MAINTENANCE
--------------------------------------------------------- */

var nextMaintInput =
    document.getElementById("fNextMaint");

if (nextMaintInput) {

    nextMaintInput.addEventListener(
        "change",
        function () {

            if (validateMaintenanceDate()) {

                this.classList.remove(
                    "is-invalid"
                );

            } else {

                this.classList.add(
                    "is-invalid"
                );
            }
        }
    );
}


function validatePhoneFields() {

    var dispatch = document.getElementById("fDispatchPhone");
    var alternative = document.getElementById("fAltContact");

    var dispatchValid = validateField(
        FIELDS.find(function (f) {
            return f.id === "fDispatchPhone";
        })
    );

    var alternativeValid = validateAlternativePhone();

    return dispatchValid && alternativeValid;
}

  /* ---------------------------------------------------------
     Modal open/reset helpers
  --------------------------------------------------------- */
  function resetForm(){
    form.reset();
    FIELDS.forEach(function(def){ clearFieldError(def); });
    fServiceTypeChoice.setChoiceByValue("");
    fStatusChoice.setChoiceByValue("available");
    nextMaintPicker.clear();
  }

  function openAddModal(){
    editingId = null;
    resetForm();
    modalEyebrow.textContent = "New registration";
    modalTitle.textContent = "Register Ambulance";
    saveBtnLabel.textContent = "Register Ambulance";
    formModal.show();
  }

  function openEditModal(id){
    var a = ambulances.find(function(x){ return x.id === id; });
    if(!a) return;
    editingId = id;
    resetForm();

    document.getElementById("fUnitNumber").value = a.unitNumber;
    document.getElementById("fPlate").value = a.plate;
    document.getElementById("fVin").value = a.vin;
    document.getElementById("fMake").value = a.make;
    document.getElementById("fModel").value = a.model;
    fServiceTypeChoice.setChoiceByValue(a.serviceType || "");
    fStatusChoice.setChoiceByValue(a.status);
    if(a.nextMaint) nextMaintPicker.setDate(a.nextMaint, true); else nextMaintPicker.clear();
    document.getElementById("fDispatchPhone").value = a.dispatchPhone;
    document.getElementById("fAltContact").value = a.altContact || "";
    document.getElementById("fNotes").value = a.notes || "";

    modalEyebrow.textContent = "Editing " + a.unitNumber;
    modalTitle.textContent = "Edit Ambulance Details";
    saveBtnLabel.textContent = "Save Changes";
    formModal.show();
  }

  /* ---------------------------------------------------------
     Form submit
  --------------------------------------------------------- */
  form.addEventListener("submit", function (e) {

    e.preventDefault();


    /* -----------------------------------------
       COMPLETE VALIDATION
    ----------------------------------------- */

    if (!validateForm()) {

        var firstErrorField = FIELDS.find(
            function (def) {

                var el =
                    document.getElementById(def.id);

                var wrap =
                    fieldWrap(el);

                return (
                    wrap &&
                    wrap.classList.contains(
                        "has-error"
                    )
                );
            }
        );


        if (firstErrorField) {

            var el =
                document.getElementById(
                    firstErrorField.id
                );

            if (
                firstErrorField.kind === "choice"
            ) {

                el.closest(
                    ".amb-field"
                ).scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });

            } else {

                el.focus();
            }
        }


        showToast(
            "Check the form",
            "Please correct the highlighted fields.",
            true
        );

        return;
    }


    /* -----------------------------------------
       CREATE PAYLOAD
    ----------------------------------------- */

    var data = {

        unitNumber:
            document.getElementById(
                "fUnitNumber"
            ).value.trim(),

        plate:
            document.getElementById(
                "fPlate"
            ).value.trim().toUpperCase(),

        vin:
            document.getElementById(
                "fVin"
            ).value.trim().toUpperCase(),

        make:
            document.getElementById(
                "fMake"
            ).value.trim(),

        model:
            document.getElementById(
                "fModel"
            ).value.trim(),

        serviceType:
            document.getElementById(
                "fServiceType"
            ).value,

        status:
            document.getElementById(
                "fStatus"
            ).value,

        nextMaint:
            document.getElementById(
                "fNextMaint"
            ).value,

        dispatchPhone:
            document.getElementById(
                "fDispatchPhone"
            ).value.trim(),

        altContact:
            document.getElementById(
                "fAltContact"
            ).value.trim(),

        notes:
            document.getElementById(
                "fNotes"
            ).value.trim()
    };


    if (editingId) {
        data.id = editingId;
    }


    /* -----------------------------------------
       SAVE
    ----------------------------------------- */

    fetch(window.location.href, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken(),
            "X-Requested-With": "XMLHttpRequest"
        },
        body: JSON.stringify(data)
    })
    .then(function(response) {

        return response.json().then(function(result) {

            return {
                ok: response.ok,
                result: result
            };

        });

    })
    .then(function(responseData) {

        var result = responseData.result;

        if (!responseData.ok || !result.success) {

            showToast(
                "Save failed",
                result.message || "Unable to save ambulance.",
                true
            );

            return;
        }

        // =========================================
        // EDIT SUCCESS
        // =========================================

        if (editingId) {

            var index = ambulances.findIndex(
                function(ambulance) {
                    return ambulance.id === editingId;
                }
            );

            if (index !== -1) {

                ambulances[index] = result.ambulance;
            }

            showToast(
                "Changes saved",
                result.ambulance.unitNumber +
                " was updated successfully.",
                false
            );

        }

        // =========================================
        // ADD SUCCESS
        // =========================================

        else {

            ambulances.unshift(result.ambulance);

            showToast(
                "Ambulance registered",
                result.ambulance.unitNumber +
                " was added successfully.",
                false
            );
        }

        editingId = null;

        formModal.hide();

        renderAll();

    })
    .catch(function(error) {

        console.error(
            "Ambulance save error:",
            error
        );

        showToast(
            "Save failed",
            "Unable to save ambulance.",
            true
        );

    });

    // keep your existing response handling here
});

  /* ---------------------------------------------------------
     Deactivate / activate / delete flow
  --------------------------------------------------------- */
  var confirmIcon = document.getElementById("ambConfirmIcon");
  var confirmTitle = document.getElementById("ambConfirmTitle");
  var confirmText = document.getElementById("ambConfirmText");
  var confirmUnit = document.getElementById("ambConfirmUnit");
  var confirmActionBtn = document.getElementById("ambConfirmActionBtn");

  function openConfirm(type, id){
    var a = ambulances.find(function(x){ return x.id === id; });
    if(!a) return;
    pendingAction = { type:type, id:id };
    confirmUnit.textContent = a.unitNumber;

    if(type === "delete"){
      confirmIcon.innerHTML = '<i class="fa-solid fa-trash"></i>';
      confirmTitle.textContent = "Remove this ambulance?";
      confirmText.innerHTML = 'This will permanently remove <b>'+esc(a.unitNumber)+'</b> from '+esc(HOSPITAL.name)+'\'s fleet. This action cannot be undone.';
      confirmActionBtn.textContent = "Yes, remove";
    } else if(type === "activate"){
      confirmIcon.innerHTML = '<i class="fa-solid fa-power-off"></i>';
      confirmTitle.textContent = "Reactivate this ambulance?";
      confirmText.innerHTML = '<b>'+esc(a.unitNumber)+'</b> will be marked <b>Available</b> and returned to active duty.';
      confirmActionBtn.textContent = "Yes, activate";
    } else {
      confirmIcon.innerHTML = '<i class="fa-solid fa-ban"></i>';
      confirmTitle.textContent = "Deactivate this ambulance?";
      confirmText.innerHTML = 'This will mark <b>'+esc(a.unitNumber)+'</b> as <b>Out of Service</b>. You can reactivate it later from the fleet list.';
      confirmActionBtn.textContent = "Yes, deactivate";
    }
    confirmModal.show();
  }

  confirmActionBtn.addEventListener("click", function(){

    if (!pendingAction) return;

    var a = ambulances.find(function(x) {
        return x.id === pendingAction.id;
    });

    if (!a) {
        confirmModal.hide();
        return;
    }

    // -----------------------------------------
    // ACTIVATE / DEACTIVATE
    // -----------------------------------------
    if (
        pendingAction.type === "activate" ||
        pendingAction.type === "deactivate"
    ) {

        var newStatus = pendingAction.type === "activate"
            ? "available"
            : "outofservice";

        fetch(window.location.href, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(),
                "X-Requested-With": "XMLHttpRequest"
            },
            body: JSON.stringify({
                id: pendingAction.id,
                status: newStatus
            })
        })
        .then(function(response) {
            return response.json().then(function(result) {
                return {
                    ok: response.ok,
                    result: result
                };
            });
        })
        .then(function(responseData) {

            var result = responseData.result;

            if (!responseData.ok || !result.success) {

                showToast(
                    "Update failed",
                    result.message || "Unable to update ambulance status.",
                    true
                );

                return;
            }

            // Update local UI only after DB success
            var index = ambulances.findIndex(function(ambulance) {
                return ambulance.id === pendingAction.id;
            });

            if (index !== -1) {
                ambulances[index] = result.ambulance;
            }

            showToast(
                newStatus === "available"
                    ? "Ambulance activated"
                    : "Ambulance deactivated",

                result.ambulance.unitNumber +
                (
                    newStatus === "available"
                        ? " is now available."
                        : " was marked out of service."
                ),

                false
            );

            pendingAction = null;
            confirmModal.hide();
            renderAll();
        })
        .catch(function(error) {

            console.error(
                "Ambulance status update error:",
                error
            );

            showToast(
                "Update failed",
                "Unable to update ambulance status.",
                true
            );
        });

        return;
    }


});

  /* ---------------------------------------------------------
    Event delegation for card actions
  --------------------------------------------------------- */
  gridEl.addEventListener("click", function(e){
    var editBtn = e.target.closest(".amb-edit-btn");
    var toggleBtn = e.target.closest(".amb-toggle-btn");

    if(editBtn){ openEditModal(editBtn.getAttribute("data-id")); return; }
    if(toggleBtn){
      var id = toggleBtn.getAttribute("data-id");
      var a = ambulances.find(function(x){ return x.id === id; });
      if(!a) return;
      openConfirm(a.status === "outofservice" ? "activate" : "deactivate", id);
    }
  });

  document.getElementById("ambAddBtn").addEventListener("click", openAddModal);
  document.getElementById("ambEmptyAddBtn").addEventListener("click", openAddModal);
  searchInput.addEventListener("input", renderGrid);

  formModalEl.addEventListener("hidden.bs.modal", function(){ editingId = null; });

  /* ---------------------------------------------------------
     Init
  --------------------------------------------------------- */
  fStatusChoice.setChoiceByValue("available");
  statusFilterChoice.setChoiceByValue("all");
  renderAll();
})();