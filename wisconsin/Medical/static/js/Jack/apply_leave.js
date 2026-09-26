(function () {

  var leaveTypeSelect = new SlimSelect({
    select: "#id_leave_type",
    settings: {
      placeholderText: "Select leave type",
      showSearch: false,
    },
  });

  var MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];
  var WEEKDAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

  function pad(n) {
    return n < 10 ? "0" + n : "" + n;
  }

  function isToday(date) {
    var today = new Date();
    return (
      date.getFullYear() === today.getFullYear() &&
      date.getMonth() === today.getMonth() &&
      date.getDate() === today.getDate()
    );
  }

  function isPastDate(date) {
    var today = new Date();
    today.setHours(0, 0, 0, 0);
    return date < today;
  }

  function DatePicker(root) {
    this.root = root;
    this.input = root.querySelector(".dp-input");
    this.hidden = root.querySelector('input[type="hidden"]');
    this.panel = root.querySelector(".dp-panel");
    this.view = new Date();
    this.selected = null;

    if (this.hidden.value) {
      var parts = this.hidden.value.split("-");
      if (parts.length === 3) {
        this.selected = new Date(
          parseInt(parts[0]),
          parseInt(parts[1]) - 1,
          parseInt(parts[2]),
        );
      }
    }

    this.bind();
    this.render();
  }

  DatePicker.prototype.bind = function () {
    var self = this;
    this.input.addEventListener("click", function (e) {
      e.stopPropagation();
      self.toggle();
    });
    document.addEventListener("click", function (e) {
      if (!self.root.contains(e.target)) self.close();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") self.close();
    });
  };

  DatePicker.prototype.toggle = function () {
    this.panel.hidden ? this.open() : this.close();
  };

  DatePicker.prototype.open = function () {
    closeAllPanels();
    if (this.selected) {
      this.view = new Date(this.selected);
    }
    this.panel.hidden = false;
    this.root.classList.add("is-open");
    this.render();
  };

  DatePicker.prototype.close = function () {
    this.panel.hidden = true;
    this.root.classList.remove("is-open");
  };

  DatePicker.prototype.select = function (date) {
    if (isPastDate(date)) return;
    this.selected = date;
    this.hidden.value =
      date.getFullYear() +
      "-" +
      pad(date.getMonth() + 1) +
      "-" +
      pad(date.getDate());
    this.input.value =
      date.getDate() +
      " " +
      MONTHS[date.getMonth()].slice(0, 3) +
      " " +
      date.getFullYear();

    clearFieldError(this.hidden.id);

    this.hidden.dispatchEvent(new Event("change"));

    this.render();
    this.close();
  };

  DatePicker.prototype.clear = function () {
    this.selected = null;
    this.hidden.value = "";
    this.input.value = "";
    this.render();
  };

  DatePicker.prototype.render = function () {
    var self = this;
    var year = this.view.getFullYear();
    var month = this.view.getMonth();
    var today = new Date();
    var firstDay = new Date(year, month, 1);
    var startOffset = firstDay.getDay();
    var daysInMonth = new Date(year, month + 1, 0).getDate();
    var daysInPrevMonth = new Date(year, month, 0).getDate();

    var html =
      '<div class="dp-body">' +
      '<div class="dp-head">' +
      '<button type="button" class="dp-prev" aria-label="Previous month"><i class="ti ti-chevron-left"></i></button>' +
      '<span class="dp-title">' +
      MONTHS[month] +
      " " +
      year +
      "</span>" +
      '<button type="button" class="dp-next" aria-label="Next month"><i class="ti ti-chevron-right"></i></button>' +
      "</div>" +
      '<div class="dp-weekdays">' +
      WEEKDAYS.map(function (d) {
        return "<span>" + d + "</span>";
      }).join("") +
      "</div>" +
      '<div class="dp-days">';

    for (var i = 0; i < startOffset; i++) {
      var d = daysInPrevMonth - startOffset + i + 1;
      html +=
        '<button type="button" class="is-outside" disabled>' + d + "</button>";
    }

    for (var day = 1; day <= daysInMonth; day++) {
      var cellDate = new Date(year, month, day);
      var isTodayDate = isToday(cellDate);
      var isSelected =
        this.selected &&
        cellDate.toDateString() === this.selected.toDateString();
      var isPast = isPastDate(cellDate);
      var cls = [];
      if (isTodayDate) cls.push("is-today");
      if (isSelected) cls.push("is-selected");
      if (isPast) cls.push("is-disabled");

      var disabled = isPast ? "disabled" : "";
      html +=
        '<button type="button" class="' +
        cls.join(" ") +
        '" data-day="' +
        day +
        '" ' +
        disabled +
        ">" +
        day +
        "</button>";
    }

    html +=
      "</div></div>" +
      '<div class="dp-foot">' +
      '<button type="button" class="dp-clear">Clear</button>' +
      '<button type="button" class="dp-today">Today</button>' +
      "</div>";
    this.panel.innerHTML = html;

    this.panel
      .querySelector(".dp-prev")
      .addEventListener("click", function (e) {
        e.stopPropagation();
        self.view = new Date(year, month - 1, 1);
        self.render();
      });
    this.panel
      .querySelector(".dp-next")
      .addEventListener("click", function (e) {
        e.stopPropagation();
        self.view = new Date(year, month + 1, 1);
        self.render();
      });
    this.panel
      .querySelector(".dp-today")
      .addEventListener("click", function (e) {
        e.stopPropagation();
        var todayDate = new Date();
        self.view = new Date();
        self.select(todayDate);
      });
    this.panel
      .querySelector(".dp-clear")
      .addEventListener("click", function (e) {
        e.stopPropagation();
        self.clear();
      });
    this.panel
      .querySelectorAll(".dp-days button[data-day]:not(:disabled)")
      .forEach(function (btn) {
        btn.addEventListener("click", function (e) {
          e.stopPropagation();
          var date = new Date(year, month, parseInt(btn.dataset.day, 10));
          self.select(date);
        });
      });
  };

  function TimePicker(root) {
    this.root = root;
    this.input = root.querySelector(".tp-input");
    this.hidden = root.querySelector('input[type="hidden"]');
    this.panel = root.querySelector(".tp-panel");
    this.timeType = root.getAttribute("data-time-type") || "start";
    
    var defaultHour = this.timeType === "start" ? 9 : 10;
    var defaultMinute = 0;
    
    var displayValue = this.input.value;
    var parsed = this.parseDisplayTime(displayValue);
    
    if (parsed) {
      this.hour24 = parsed.hour24;
      this.minute = parsed.minute;
    } else if (this.hidden.value) {
      var parts = this.hidden.value.split(":");
      if (parts.length === 2) {
        var h = parseInt(parts[0], 10);
        var m = parseInt(parts[1], 10);
        if (!isNaN(h) && !isNaN(m)) {
          this.hour24 = h;
          this.minute = m;
        } else {
          this.hour24 = defaultHour;
          this.minute = defaultMinute;
        }
      } else {
        this.hour24 = defaultHour;
        this.minute = defaultMinute;
      }
    } else {
      this.hour24 = defaultHour;
      this.minute = defaultMinute;
    }
    
    this.updateFrom24Hour();
    
    if (!this.input.value && !this.hidden.value) {
      this.hidden.value = pad(this.hour24) + ":" + pad(this.minute);
      this.updateDisplay();
    } else {
      this.updateDisplay();
    }
    
    this.hourSlim = null;
    this.minuteSlim = null;
    this.periodSlim = null;
    this.initialized = false;
    this.isOpen = false;
    
    this.bind();
  }

  TimePicker.prototype.parseDisplayTime = function (timeStr) {
    if (!timeStr || timeStr.trim() === "") return null;
    var match = timeStr.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
    if (!match) return null;

    var hour = parseInt(match[1], 10);
    var minute = parseInt(match[2], 10);
    var period = match[3].toUpperCase();

    var hour24;
    if (period === "AM") {
      hour24 = hour === 12 ? 0 : hour;
    } else {
      hour24 = hour === 12 ? 12 : hour + 12;
    }

    return { hour24: hour24, minute: minute };
  };

  TimePicker.prototype.updateFrom24Hour = function () {
    if (this.hour24 >= 12) {
      this.period = "PM";
      this.hour = this.hour24 === 12 ? 12 : this.hour24 - 12;
    } else {
      this.period = "AM";
      this.hour = this.hour24 === 0 ? 12 : this.hour24;
    }
  };

  TimePicker.prototype.updateTo24Hour = function () {
    if (this.period === "AM") {
      this.hour24 = this.hour === 12 ? 0 : this.hour;
    } else {
      this.hour24 = this.hour === 12 ? 12 : this.hour + 12;
    }
  };

  TimePicker.prototype.bind = function () {
    var self = this;
    this.input.addEventListener("click", function (e) {
      e.stopPropagation();
      self.toggle();
    });
    document.addEventListener("click", function (e) {
      if (!self.root.contains(e.target)) self.close();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") self.close();
    });
  };

  TimePicker.prototype.toggle = function () {
    if (this.panel.hidden) {
      this.open();
    } else {
      this.close();
    }
  };

  TimePicker.prototype.open = function () {
    closeAllPanels();
    this.isOpen = true;
    
    var parsed = this.parseDisplayTime(this.input.value);
    if (parsed) {
      this.hour24 = parsed.hour24;
      this.minute = parsed.minute;
      this.updateFrom24Hour();
    } else if (this.hidden.value) {
      var parts = this.hidden.value.split(":");
      if (parts.length === 2) {
        var h = parseInt(parts[0], 10);
        var m = parseInt(parts[1], 10);
        if (!isNaN(h) && !isNaN(m)) {
          this.hour24 = h;
          this.minute = m;
          this.updateFrom24Hour();
        }
      }
    }
    
    this.panel.hidden = false;
    this.root.classList.add("is-open");
    this.updateDisplay();
    
    var self = this;
    setTimeout(function () {
      self.initSlimSelects();
      self.updateSlimSelectValues();
      self.disablePastTimes();
    }, 150);
  };

  TimePicker.prototype.disablePastTimes = function () {
    var startDateInput = document.getElementById("id_start_date");
    if (!startDateInput) return;

    var selectedDate = startDateInput.value;
    if (!selectedDate) return;

    var today = new Date();
    var todayStr =
      today.getFullYear() +
      "-" +
      pad(today.getMonth() + 1) +
      "-" +
      pad(today.getDate());

    if (selectedDate !== todayStr) return;

    var now = new Date();
    var currentHour = now.getHours();
    var currentMinute = now.getMinutes();

    var hourSelect = this.panel.querySelector("select.tp-hour-select");
    var minuteSelect = this.panel.querySelector("select.tp-minute-select");
    var periodSelect = this.panel.querySelector("select.tp-period-select-dropdown");

    if (!hourSelect || !minuteSelect || !periodSelect) return;

    var currentPeriod = this.period;

    hourSelect.querySelectorAll("option").forEach(function(opt) {
      opt.disabled = false;
      opt.style.color = "";
    });
    minuteSelect.querySelectorAll("option").forEach(function(opt) {
      opt.disabled = false;
      opt.style.color = "";
    });

    hourSelect.querySelectorAll("option").forEach(function(opt) {
      var hourVal = parseInt(opt.value, 10);
      var hour24;
      if (currentPeriod === "AM") {
        hour24 = hourVal === 12 ? 0 : hourVal;
      } else {
        hour24 = hourVal === 12 ? 12 : hourVal + 12;
      }

      if (hour24 < currentHour) {
        opt.disabled = true;
        opt.style.color = "#ccc";
      }
    });

    var currentHour12 = currentHour % 12;
    if (currentHour12 === 0) currentHour12 = 12;
    var currentPeriodText = currentHour >= 12 ? "PM" : "AM";

    if (this.hour === currentHour12 && this.period === currentPeriodText) {
      minuteSelect.querySelectorAll("option").forEach(function(opt) {
        var minuteVal = parseInt(opt.value, 10);
        if (minuteVal < currentMinute) {
          opt.disabled = true;
          opt.style.color = "#ccc";
        } else {
          opt.disabled = false;
          opt.style.color = "";
        }
      });
    }

    if (currentHour >= 12 && currentPeriod === "AM") {
      periodSelect.querySelectorAll("option").forEach(function(opt) {
        if (opt.value === "AM") {
          var hasAvailableHour = false;
          hourSelect.querySelectorAll("option").forEach(function(hourOpt) {
            if (!hourOpt.disabled) {
              hasAvailableHour = true;
            }
          });
          if (!hasAvailableHour) {
            opt.disabled = true;
            opt.style.color = "#ccc";
          }
        }
      });
    }

    if (currentHour >= 12 && currentPeriod === "AM") {
      var hasAvailableHour = false;
      hourSelect.querySelectorAll("option").forEach(function(hourOpt) {
        if (!hourOpt.disabled) {
          hasAvailableHour = true;
        }
      });
      if (!hasAvailableHour) {
        periodSelect.querySelectorAll("option").forEach(function(opt) {
          if (opt.value === "AM") {
            opt.disabled = true;
            opt.style.color = "#ccc";
          }
        });
      }
    }

    this.validateTimeRestrictions();
  };

  TimePicker.prototype.updateSlimSelectValues = function () {
    if (this.hourSlim) {
      try {
        this.hourSlim.set(String(this.hour));
      } catch (e) {
        console.log("Error setting hour:", e);
      }
    }
    if (this.minuteSlim) {
      try {
        this.minuteSlim.set(String(this.minute));
      } catch (e) {
        console.log("Error setting minute:", e);
      }
    }
    if (this.periodSlim) {
      try {
        this.periodSlim.set(this.period);
      } catch (e) {
        console.log("Error setting period:", e);
      }
    }
  };

  TimePicker.prototype.close = function () {
    this.panel.hidden = true;
    this.root.classList.remove("is-open");
    this.isOpen = false;
    this.destroySlimSelects();
  };

  TimePicker.prototype.destroySlimSelects = function () {
    if (this.hourSlim) {
      try {
        this.hourSlim.destroy();
      } catch (e) {}
      this.hourSlim = null;
    }
    if (this.minuteSlim) {
      try {
        this.minuteSlim.destroy();
      } catch (e) {}
      this.minuteSlim = null;
    }
    if (this.periodSlim) {
      try {
        this.periodSlim.destroy();
      } catch (e) {}
      this.periodSlim = null;
    }
    this.initialized = false;
  };

  TimePicker.prototype.initSlimSelects = function () {
    if (this.initialized) return;

    var self = this;

    var hourSelect = this.panel.querySelector("select.tp-hour-select");
    var minuteSelect = this.panel.querySelector("select.tp-minute-select");
    var periodSelect = this.panel.querySelector(
      "select.tp-period-select-dropdown",
    );

    if (hourSelect && !this.hourSlim) {
      try {
        this.hourSlim = new SlimSelect({
          select: hourSelect,
          settings: {
            showSearch: false,
            placeholderText: "Hour",
            contentHeight: 120,
          },
          events: {
            afterChange: function (newVal) {
              self.hour = parseInt(newVal[0].value, 10);
              self.updateTo24Hour();
              self.updateDisplay();
              self.validateTimeRestrictions();
              self.disablePastTimes();
            },
          },
        });
        this.hourSlim.set(String(this.hour));
      } catch (e) {
        console.error("Error initializing hour SlimSelect:", e);
      }
    }

    if (minuteSelect && !this.minuteSlim) {
      try {
        this.minuteSlim = new SlimSelect({
          select: minuteSelect,
          settings: {
            showSearch: false,
            placeholderText: "Minute",
            contentHeight: 120,
          },
          events: {
            afterChange: function (newVal) {
              self.minute = parseInt(newVal[0].value, 10);
              self.updateDisplay();
              self.validateTimeRestrictions();
              self.disablePastTimes();
            },
          },
        });
        this.minuteSlim.set(String(this.minute));
      } catch (e) {
        console.error("Error initializing minute SlimSelect:", e);
      }
    }

    if (periodSelect && !this.periodSlim) {
      try {
        this.periodSlim = new SlimSelect({
          select: periodSelect,
          settings: {
            showSearch: false,
            placeholderText: "Period",
            contentHeight: 80,
          },
          events: {
            afterChange: function (newVal) {
              self.period = newVal[0].value;
              self.updateTo24Hour();
              self.updateDisplay();
              self.validateTimeRestrictions();
              self.disablePastTimes();
            },
          },
        });
        this.periodSlim.set(this.period);
      } catch (e) {
        console.error("Error initializing period SlimSelect:", e);
      }
    }

    var doneBtn = this.panel.querySelector(".tp-done");
    var cancelBtn = this.panel.querySelector(".tp-cancel");

    if (doneBtn) {
      doneBtn.onclick = function (e) {
        e.stopPropagation();
        e.preventDefault();
        self.commit();
        self.close();
      };
    }

    if (cancelBtn) {
      cancelBtn.onclick = function (e) {
        e.stopPropagation();
        e.preventDefault();
        var parsed = self.parseDisplayTime(self.input.value);
        if (parsed) {
          self.hour24 = parsed.hour24;
          self.minute = parsed.minute;
          self.updateFrom24Hour();
          self.updateDisplay();
          self.updateSlimSelectValues();
        }
        self.close();
      };
    }

    this.validateTimeRestrictions();
    this.initialized = true;
  };

  TimePicker.prototype.updateDisplay = function () {
    var display = this.panel.querySelector(".tp-time-display");
    if (display) {
      var displayHour = this.hour;
      // Show 12:00 AM for midnight, not 0:00 AM
      if (this.hour24 === 0) {
        displayHour = 12;
        this.period = "AM";
      }
      display.innerHTML = displayHour + ":" + pad(this.minute) + 
        ' <span class="tp-period-display">' + this.period + "</span>";
    }

    this.hidden.value = pad(this.hour24) + ":" + pad(this.minute);
    
    var displayHour = this.hour;
    if (this.hour24 === 0) {
      displayHour = 12;
    }
    this.input.value = displayHour + ":" + pad(this.minute) + " " + this.period;
  };

  TimePicker.prototype.commit = function () {
    if (!this.validateTimeRestrictions()) {
      return false;
    }
    
    this.updateDisplay();
    clearFieldError(this.hidden.id);
    this.hidden.dispatchEvent(new Event("change"));

    if (document.getElementById("id_leave_type").value === "PERMISSION") {
      validatePermissionDuration();
    }
    return true;
  };

  TimePicker.prototype.validateTimeRestrictions = function () {
    var leaveType = document.getElementById("id_leave_type").value;
    if (leaveType !== "PERMISSION") return true;

    var startDateInput = document.getElementById("id_start_date");
    var selectedDate = startDateInput.value;

    if (!selectedDate) return true;

    var today = new Date();
    var todayStr =
      today.getFullYear() +
      "-" +
      pad(today.getMonth() + 1) +
      "-" +
      pad(today.getDate());

    var errorEl = document.getElementById(
      this.timeType === "start" ? "start_time_error" : "end_time_error",
    );

    if (selectedDate === todayStr) {
      var now = new Date();
      var currentHour = now.getHours();
      var currentMinute = now.getMinutes();

      if (
        this.hour24 < currentHour ||
        (this.hour24 === currentHour && this.minute <= currentMinute)
      ) {
        if (errorEl) {
          var timeDisplay = this.hour + ":" + pad(this.minute) + " " + this.period;
          errorEl.textContent = "Selected time " + timeDisplay + " is in the past. Please choose a future time.";
          errorEl.style.display = "block";
        }
        this.root.classList.add("has-error");
        return false;
      }
    }

    if (errorEl) {
      errorEl.style.display = "none";
    }
    this.root.classList.remove("has-error");
    return true;
  };

  function closeAllPanels() {
    document.querySelectorAll(".dp-panel, .tp-panel").forEach(function (p) {
      p.hidden = true;
    });
    document.querySelectorAll(".dp-field, .tp-field").forEach(function (f) {
      f.classList.remove("is-open");
    });
  }

  function clearFieldError(fieldId) {
    var field = document.getElementById(fieldId);
    if (field) {
      var formGroup = field.closest(".form-group");
      if (formGroup) {
        formGroup.classList.remove("has-error");
        var errorEl = formGroup.querySelector(
          ".field-error:not(#permission_error)",
        );
        if (errorEl) {
          errorEl.remove();
        }
      }
    }
  }

  var datePickers = [];
  document.querySelectorAll("[data-datepicker]").forEach(function (el) {
    datePickers.push(new DatePicker(el));
  });

  document.querySelectorAll("[data-timepicker]").forEach(function (el) {
    new TimePicker(el);
  });


  function validatePermissionFields() {
    var errors = [];
    var errorContainer = document.getElementById("permission_error");

    var leaveType = document.getElementById("id_leave_type").value;
    var startDate = document.getElementById("id_start_date").value;
    var startTime = document.getElementById("id_permission_start_time").value;
    var endTime = document.getElementById("id_permission_end_time").value;

    clearFieldErrors();

    if (leaveType !== "PERMISSION") {
      if (errorContainer) {
        errorContainer.style.display = "none";
      }
      return true;
    }

    if (!startDate) {
      errors.push({
        field: "start_date",
        message: "Please select a date for permission leave.",
      });
    }

    if (!startTime) {
      errors.push({
        field: "permission_start_time",
        message: "Please select a start time for permission leave.",
      });
    }

    if (!endTime) {
      errors.push({
        field: "permission_end_time",
        message: "Please select an end time for permission leave.",
      });
    }

    if (startTime && endTime) {
      var startParts = startTime.split(":");
      var endParts = endTime.split(":");

      if (startParts.length === 2 && endParts.length === 2) {
        var startMinutes =
          parseInt(startParts[0]) * 60 + parseInt(startParts[1]);
        var endMinutes = parseInt(endParts[0]) * 60 + parseInt(endParts[1]);

        if (endMinutes <= startMinutes) {
          errors.push({
            field: "permission_end_time",
            message: "End time must be after the start time.",
          });
        }

        var diffHours = (endMinutes - startMinutes) / 60;
        if (diffHours > 4) {
          errors.push({
            field: "permission_end_time",
            message:
              "Permission leave cannot exceed 4 hours. Current duration: " +
              diffHours.toFixed(1) +
              " hours.",
          });
        }
      }
    }

    if (errors.length > 0) {
      displayFieldErrors(errors);
      if (errorContainer) {
        errorContainer.innerHTML =
          '<i class="ti ti-alert-circle"></i> Please fix the errors above.';
        errorContainer.style.display = "block";
      }
      return false;
    }

    if (errorContainer) {
      errorContainer.style.display = "none";
    }
    return true;
  }

  function displayFieldErrors(errors) {
    errors.forEach(function (error) {
      var fieldId = error.field;
      var field = document.getElementById(fieldId);

      if (field) {
        var formGroup = field.closest(".form-group");
        if (formGroup) {
          formGroup.classList.add("has-error");

          var existingError = formGroup.querySelector(
            ".field-error:not(#permission_error)",
          );
          if (existingError) {
            existingError.remove();
          }

          var errorDiv = document.createElement("div");
          errorDiv.className = "field-error";
          errorDiv.innerHTML =
            '<i class="ti ti-alert-circle"></i> ' + error.message;
          formGroup.appendChild(errorDiv);
        }
      }
    });
  }

  function clearFieldErrors() {
    document
      .querySelectorAll(".field-error:not(#permission_error)")
      .forEach(function (el) {
        el.remove();
      });

    document.querySelectorAll(".has-error").forEach(function (el) {
      el.classList.remove("has-error");
    });

    var permError = document.getElementById("permission_error");
    if (permError) {
      permError.style.display = "none";
      permError.innerHTML = "";
    }
  }

  function validatePermissionDuration() {
    if (document.getElementById("id_leave_type").value !== "PERMISSION") return;

    var startTime = document.getElementById("id_permission_start_time").value;
    var endTime = document.getElementById("id_permission_end_time").value;
    var errorEl = document.getElementById("permission_error");

    document
      .querySelectorAll(".field-error:not(#permission_error)")
      .forEach(function (el) {
        var parent = el.closest(".form-group");
        if (
          parent &&
          (parent.querySelector("#id_permission_start_time") ||
            parent.querySelector("#id_permission_end_time"))
        ) {
          el.remove();
          parent.classList.remove("has-error");
        }
      });

    if (!startTime || !endTime) return;

    var startParts = startTime.split(":");
    var endParts = endTime.split(":");

    if (startParts.length === 2 && endParts.length === 2) {
      var startMinutes = parseInt(startParts[0]) * 60 + parseInt(startParts[1]);
      var endMinutes = parseInt(endParts[0]) * 60 + parseInt(endParts[1]);

      if (endMinutes <= startMinutes) {
        var endTimeField = document.getElementById("id_permission_end_time");
        var formGroup = endTimeField.closest(".form-group");
        if (formGroup) {
          formGroup.classList.add("has-error");
          var existingError = formGroup.querySelector(".field-error");
          if (!existingError) {
            var errorDiv = document.createElement("div");
            errorDiv.className = "field-error";
            errorDiv.innerHTML =
              '<i class="ti ti-alert-circle"></i> End time must be after start time.';
            formGroup.appendChild(errorDiv);
          }
        }
        if (errorEl) {
          errorEl.style.display = "block";
          errorEl.innerHTML =
            '<i class="ti ti-alert-circle"></i> End time must be after start time.';
        }
        return;
      }

      var diffHours = (endMinutes - startMinutes) / 60;

      if (diffHours > 4) {
        var endTimeField2 = document.getElementById("id_permission_end_time");
        var formGroup2 = endTimeField2.closest(".form-group");
        if (formGroup2) {
          formGroup2.classList.add("has-error");
          var existingError2 = formGroup2.querySelector(".field-error");
          if (!existingError2) {
            var errorDiv2 = document.createElement("div");
            errorDiv2.className = "field-error";
            errorDiv2.innerHTML =
              '<i class="ti ti-alert-circle"></i> Permission leave cannot exceed 4 hours.';
            formGroup2.appendChild(errorDiv2);
          }
        }
        if (errorEl) {
          errorEl.style.display = "block";
          errorEl.innerHTML =
            '<i class="ti ti-alert-circle"></i> Permission leave cannot exceed 4 hours. Current: ' +
            diffHours.toFixed(1) +
            " hours.";
        }
      } else {
        if (errorEl) {
          errorEl.style.display = "none";
          errorEl.innerHTML = "";
        }
        document.querySelectorAll(".field-error").forEach(function (el) {
          var parent = el.closest(".form-group");
          if (parent && parent.querySelector(".tp-field")) {
            el.remove();
            parent.classList.remove("has-error");
          }
        });
      }
    }
  }

  var permissionBlock = document.getElementById("permission_block");
  var durationHint = document.getElementById("duration_hint");
  var endDateGroup = document.getElementById("end_date_group");
  var startDateHidden = document.getElementById("id_start_date");
  var endDateHidden = document.getElementById("id_end_date");
  var permissionStartTime = document.getElementById("id_permission_start_time");
  var permissionEndTime = document.getElementById("id_permission_end_time");
  var leaveTypeSelectEl = document.getElementById("id_leave_type");

  function syncLeaveType() {
    var isPermission = document.getElementById("id_leave_type").value === "PERMISSION";
    var hasDate = document.getElementById("id_start_date").value !== "";
    
    if (isPermission && hasDate) {
        permissionBlock.hidden = false;
        durationHint.textContent = "same day only";
        endDateGroup.style.opacity = "0.5";
        endDateGroup.style.pointerEvents = "none";
        
        if (startDateHidden.value) {
            endDateHidden.value = startDateHidden.value;
            var endDateDisplay = document.getElementById("id_end_date_display");
            if (endDateDisplay && startDateHidden.value) {
                var parts = startDateHidden.value.split("-");
                if (parts.length === 3) {
                    var date = new Date(
                        parseInt(parts[0]),
                        parseInt(parts[1]) - 1,
                        parseInt(parts[2])
                    );
                    endDateDisplay.value = 
                        date.getDate() + 
                        " " + 
                        MONTHS[date.getMonth()].slice(0, 3) + 
                        " " + 
                        date.getFullYear();
                }
            }
        }
        
        permissionStartTime.required = true;
        permissionEndTime.required = true;
        endDateHidden.required = false;
        
        validatePermissionFields();
    } else {
        permissionBlock.hidden = true;
        durationHint.textContent = "for full-day leave";
        endDateGroup.style.opacity = "1";
        endDateGroup.style.pointerEvents = "auto";
        
        endDateHidden.required = true;
        permissionStartTime.required = false;
        permissionEndTime.required = false;
        
        permissionStartTime.value = "";
        permissionEndTime.value = "";
        var startDisplay = document.getElementById("id_permission_start_time_display");
        var endDisplay = document.getElementById("id_permission_end_time_display");
        if (startDisplay) startDisplay.value = "";
        if (endDisplay) endDisplay.value = "";
    }
    
    startDateHidden.required = true;
    clearFieldErrors();
  }

  document.getElementById("id_leave_type").addEventListener("change", function() {
      clearFieldErrors();
      syncLeaveType();
      if (this.value === "PERMISSION") {
          validatePermissionFields();
      }
  });

  document.getElementById("id_start_date").addEventListener("change", function() {
      syncLeaveType();
      if (document.getElementById("id_leave_type").value === "PERMISSION") {
          validatePermissionFields();
          document.querySelectorAll("[data-timepicker]").forEach(function(el) {
              var timePicker = el.__timePickerInstance;
              if (timePicker && timePicker.isOpen) {
                  timePicker.disablePastTimes();
              }
          });
      }
  });

  permissionStartTime.addEventListener("change", validatePermissionDuration);
  permissionEndTime.addEventListener("change", validatePermissionDuration);

  var reason = document.getElementById("id_reason");

  document.getElementById("leaveForm").addEventListener("submit", function (e) {
    var leaveType = document.getElementById("id_leave_type").value;
    var hasErrors = false;

    clearFieldErrors();

    if (!leaveType) {
      e.preventDefault();
      hasErrors = true;
      var leaveTypeField = document.getElementById("id_leave_type");
      var formGroup = leaveTypeField.closest(".form-group");
      if (formGroup) {
        formGroup.classList.add("has-error");
        var existingError = formGroup.querySelector(".field-error");
        if (!existingError) {
          var errorDiv = document.createElement("div");
          errorDiv.className = "field-error";
          errorDiv.innerHTML =
            '<i class="ti ti-alert-circle"></i> Please select a leave type.';
          formGroup.appendChild(errorDiv);
        }
      }
    }

    if (leaveType === "PERMISSION") {
      if (!startDateHidden.value) {
        e.preventDefault();
        hasErrors = true;
        var formGroup = startDateHidden.closest(".form-group");
        if (formGroup) {
          formGroup.classList.add("has-error");
          var existingError = formGroup.querySelector(".field-error");
          if (!existingError) {
            var errorDiv = document.createElement("div");
            errorDiv.className = "field-error";
            errorDiv.innerHTML =
              '<i class="ti ti-alert-circle"></i> Please select a date for permission leave.';
            formGroup.appendChild(errorDiv);
          }
        }
      }

      if (!permissionStartTime.value) {
        e.preventDefault();
        hasErrors = true;
        var formGroup = permissionStartTime.closest(".form-group");
        if (formGroup) {
          formGroup.classList.add("has-error");
          var existingError = formGroup.querySelector(".field-error");
          if (!existingError) {
            var errorDiv = document.createElement("div");
            errorDiv.className = "field-error";
            errorDiv.innerHTML =
              '<i class="ti ti-alert-circle"></i> Please select a start time for permission leave.';
            formGroup.appendChild(errorDiv);
          }
        }
      }

      if (!permissionEndTime.value) {
        e.preventDefault();
        hasErrors = true;
        var formGroup = permissionEndTime.closest(".form-group");
        if (formGroup) {
          formGroup.classList.add("has-error");
          var existingError = formGroup.querySelector(".field-error");
          if (!existingError) {
            var errorDiv = document.createElement("div");
            errorDiv.className = "field-error";
            errorDiv.innerHTML =
              '<i class="ti ti-alert-circle"></i> Please select an end time for permission leave.';
            formGroup.appendChild(errorDiv);
          }
        }
      }

      if (permissionStartTime.value && startDateHidden.value) {
        var today = new Date();
        var todayStr =
          today.getFullYear() +
          "-" +
          pad(today.getMonth() + 1) +
          "-" +
          pad(today.getDate());
        
        if (startDateHidden.value === todayStr) {
          var startParts = permissionStartTime.value.split(":");
          if (startParts.length === 2) {
            var startHour = parseInt(startParts[0]);
            var startMinute = parseInt(startParts[1]);
            var currentHour = today.getHours();
            var currentMinute = today.getMinutes();
            
            if (startHour < currentHour || (startHour === currentHour && startMinute <= currentMinute)) {
              e.preventDefault();
              hasErrors = true;
              var formGroup = permissionStartTime.closest(".form-group");
              if (formGroup) {
                formGroup.classList.add("has-error");
                var existingError = formGroup.querySelector(".field-error");
                if (!existingError) {
                  var errorDiv = document.createElement("div");
                  errorDiv.className = "field-error";
                  errorDiv.innerHTML =
                    '<i class="ti ti-alert-circle"></i> Start time cannot be in the past. Please select a future time.';
                  formGroup.appendChild(errorDiv);
                }
              }
            }
          }
        }
      }

      if (permissionEndTime.value && startDateHidden.value) {
        var today = new Date();
        var todayStr =
          today.getFullYear() +
          "-" +
          pad(today.getMonth() + 1) +
          "-" +
          pad(today.getDate());
        
        if (startDateHidden.value === todayStr) {
          var endParts = permissionEndTime.value.split(":");
          if (endParts.length === 2) {
            var endHour = parseInt(endParts[0]);
            var endMinute = parseInt(endParts[1]);
            var currentHour = today.getHours();
            var currentMinute = today.getMinutes();
            
            if (endHour < currentHour || (endHour === currentHour && endMinute <= currentMinute)) {
              e.preventDefault();
              hasErrors = true;
              var formGroup = permissionEndTime.closest(".form-group");
              if (formGroup) {
                formGroup.classList.add("has-error");
                var existingError = formGroup.querySelector(".field-error");
                if (!existingError) {
                  var errorDiv = document.createElement("div");
                  errorDiv.className = "field-error";
                  errorDiv.innerHTML =
                    '<i class="ti ti-alert-circle"></i> End time cannot be in the past. Please select a future time.';
                  formGroup.appendChild(errorDiv);
                }
              }
            }
          }
        }
      }

      if (permissionStartTime.value && permissionEndTime.value) {
        var startParts = permissionStartTime.value.split(":");
        var endParts = permissionEndTime.value.split(":");

        if (startParts.length === 2 && endParts.length === 2) {
          var startMinutes =
            parseInt(startParts[0]) * 60 + parseInt(startParts[1]);
          var endMinutes = parseInt(endParts[0]) * 60 + parseInt(endParts[1]);

          if (endMinutes <= startMinutes) {
            e.preventDefault();
            hasErrors = true;
            var formGroup = permissionEndTime.closest(".form-group");
            if (formGroup) {
              formGroup.classList.add("has-error");
              var existingError = formGroup.querySelector(".field-error");
              if (!existingError) {
                var errorDiv = document.createElement("div");
                errorDiv.className = "field-error";
                errorDiv.innerHTML =
                  '<i class="ti ti-alert-circle"></i> End time must be after the start time.';
                formGroup.appendChild(errorDiv);
              }
            }
            var errorEl = document.getElementById("permission_error");
            if (errorEl) {
              errorEl.innerHTML =
                '<i class="ti ti-alert-circle"></i> End time must be after start time.';
              errorEl.style.display = "block";
            }
          }

          var diffHours = (endMinutes - startMinutes) / 60;
          if (diffHours > 4) {
            e.preventDefault();
            hasErrors = true;
            var formGroup = permissionEndTime.closest(".form-group");
            if (formGroup) {
              formGroup.classList.add("has-error");
              var existingError = formGroup.querySelector(".field-error");
              if (!existingError) {
                var errorDiv = document.createElement("div");
                errorDiv.className = "field-error";
                errorDiv.innerHTML =
                  '<i class="ti ti-alert-circle"></i> Permission leave cannot exceed 4 hours. Current: ' +
                  diffHours.toFixed(1) +
                  " hours.";
                formGroup.appendChild(errorDiv);
              }
            }
            var errorEl = document.getElementById("permission_error");
            if (errorEl) {
              errorEl.innerHTML =
                '<i class="ti ti-alert-circle"></i> Permission leave cannot exceed 4 hours. Current: ' +
                diffHours.toFixed(1) +
                " hours.";
              errorEl.style.display = "block";
            }
          }
        }
      }

    } else {
      if (!startDateHidden.value) {
        e.preventDefault();
        hasErrors = true;
        var formGroup = startDateHidden.closest(".form-group");
        if (formGroup) {
          formGroup.classList.add("has-error");
          var existingError = formGroup.querySelector(".field-error");
          if (!existingError) {
            var errorDiv = document.createElement("div");
            errorDiv.className = "field-error";
            errorDiv.innerHTML =
              '<i class="ti ti-alert-circle"></i> Please select a start date.';
            formGroup.appendChild(errorDiv);
          }
        }
      }

      if (!endDateHidden.value) {
        e.preventDefault();
        hasErrors = true;
        var formGroup = endDateHidden.closest(".form-group");
        if (formGroup) {
          formGroup.classList.add("has-error");
          var existingError = formGroup.querySelector(".field-error");
          if (!existingError) {
            var errorDiv = document.createElement("div");
            errorDiv.className = "field-error";
            errorDiv.innerHTML =
              '<i class="ti ti-alert-circle"></i> Please select an end date.';
            formGroup.appendChild(errorDiv);
          }
        }
      }

      if (startDateHidden.value && endDateHidden.value) {
        var startDate = new Date(startDateHidden.value);
        var endDate = new Date(endDateHidden.value);
        if (endDate < startDate) {
          e.preventDefault();
          hasErrors = true;
          var formGroup = endDateHidden.closest(".form-group");
          if (formGroup) {
            formGroup.classList.add("has-error");
            var existingError = formGroup.querySelector(".field-error");
            if (!existingError) {
              var errorDiv = document.createElement("div");
              errorDiv.className = "field-error";
              errorDiv.innerHTML =
                '<i class="ti ti-alert-circle"></i> End date must be after start date.';
              formGroup.appendChild(errorDiv);
            }
          }
        }
      }
    }

    var reason = document.getElementById("id_reason");
    if (!reason.value.trim()) {
      e.preventDefault();
      hasErrors = true;
      var formGroup = reason.closest(".form-group");
      if (formGroup) {
        formGroup.classList.add("has-error");
        var existingError = formGroup.querySelector(".field-error");
        if (!existingError) {
          var errorDiv = document.createElement("div");
          errorDiv.className = "field-error";
          errorDiv.innerHTML =
            '<i class="ti ti-alert-circle"></i> Please provide a reason for your leave request.';
          formGroup.appendChild(errorDiv);
        }
      }
    }

    if (hasErrors) {
      var firstError = document.querySelector(".has-error");
      if (firstError) {
        firstError.scrollIntoView({ behavior: "smooth", block: "center" });
      }
      var errorEl = document.getElementById("permission_error");
      if (errorEl && errorEl.innerHTML) {
        errorEl.style.display = "block";
      }
      return false;
    }

    return true;
  });

  document
    .getElementById("id_leave_type")
    .addEventListener("change", function () {
      clearFieldErrors();
      syncLeaveType();
      if (this.value === "PERMISSION") {
        validatePermissionFields();
      }
    });

  document
    .getElementById("id_start_date")
    .addEventListener("change", function () {
      syncLeaveType();
      if (document.getElementById("id_leave_type").value === "PERMISSION") {
        validatePermissionFields();
        document.querySelectorAll("[data-timepicker]").forEach(function (el) {
          var timePicker = el.__timePickerInstance;
          if (timePicker && timePicker.isOpen) {
            timePicker.disablePastTimes();
          }
        });
      }
    });

  document
    .getElementById("id_permission_start_time")
    .addEventListener("change", function () {
      if (document.getElementById("id_leave_type").value === "PERMISSION") {
        validatePermissionFields();
        validatePastTime();
      }
    });

  document
    .getElementById("id_permission_end_time")
    .addEventListener("change", function () {
      if (document.getElementById("id_leave_type").value === "PERMISSION") {
        validatePermissionFields();
        validatePastTime();
      }
    });

  function validatePastTime() {
    var startDate = document.getElementById("id_start_date").value;
    if (!startDate) return;
    
    var today = new Date();
    var todayStr = today.getFullYear() + "-" + pad(today.getMonth() + 1) + "-" + pad(today.getDate());
    
    if (startDate !== todayStr) return;
    
    var startTime = document.getElementById("id_permission_start_time").value;
    var endTime = document.getElementById("id_permission_end_time").value;
    var currentHour = today.getHours();
    var currentMinute = today.getMinutes();
    
    if (startTime) {
      var startParts = startTime.split(":");
      if (startParts.length === 2) {
        var startHour = parseInt(startParts[0]);
        var startMinute = parseInt(startParts[1]);
        var startTimeField = document.getElementById("id_permission_start_time");
        var formGroup = startTimeField.closest(".form-group");
        var errorEl = document.getElementById("start_time_error");
        
        if (startHour < currentHour || (startHour === currentHour && startMinute <= currentMinute)) {
          if (formGroup) {
            formGroup.classList.add("has-error");
          }
          if (errorEl) {
            errorEl.textContent = "Start time cannot be in the past. Please select a future time.";
            errorEl.style.display = "block";
          }
        } else {
          if (formGroup) {
            formGroup.classList.remove("has-error");
          }
          if (errorEl) {
            errorEl.style.display = "none";
          }
        }
      }
    }
    
    if (endTime) {
      var endParts = endTime.split(":");
      if (endParts.length === 2) {
        var endHour = parseInt(endParts[0]);
        var endMinute = parseInt(endParts[1]);
        var endTimeField = document.getElementById("id_permission_end_time");
        var formGroup = endTimeField.closest(".form-group");
        var errorEl = document.getElementById("end_time_error");
        
        if (endHour < currentHour || (endHour === currentHour && endMinute <= currentMinute)) {
          if (formGroup) {
            formGroup.classList.add("has-error");
          }
          if (errorEl) {
            errorEl.textContent = "End time cannot be in the past. Please select a future time.";
            errorEl.style.display = "block";
          }
        } else {
          if (formGroup) {
            formGroup.classList.remove("has-error");
          }
          if (errorEl) {
            errorEl.style.display = "none";
          }
        }
      }
    }
  }

  syncLeaveType();

  if (document.getElementById("id_leave_type").value === "PERMISSION" && 
      document.getElementById("id_start_date").value !== "") {
    validatePermissionFields();
  }

  document.querySelectorAll("[data-timepicker]").forEach(function (el) {
  });

  window.disablePastTimesOnAllOpenPickers = function() {
    document.querySelectorAll("[data-timepicker]").forEach(function (el) {
      var panel = el.querySelector(".tp-panel");
      if (panel && !panel.hidden) {
        var input = el.querySelector(".tp-input");
        if (input) {
          input.click();
        }
      }
    });
  };

  if (typeof AOS !== "undefined") {
    AOS.init({
      duration: 600,
      once: true,
    });
  }
})();