const sections = {
  basic: document.getElementById("basic-section"),
  schedule: document.getElementById("schedule-section"),
  registration: document.getElementById("registration-section"),
};

const pills = {
  basic: document.getElementById("pill-basic"),
  schedule: document.getElementById("pill-schedule"),
  registration: document.getElementById("pill-registration"),
};

const organizerType = document.getElementById("id_organizer_type");
const schoolField = document.getElementById("school-field");
const departmentField = document.getElementById("department-field");
const organizerField = document.getElementById("organizer-field");
const studentOrganizationField = document.getElementById(
  "student-organization-field",
);

const schoolSelect = document.getElementById("id_school");
const departmentSelect = document.getElementById("id_department");
const organizerSelect = document.getElementById("id_organizer");
const organizationSelect = document.getElementById("id_student_organization");

const eventTitle = document.getElementById("id_event_title");
const subtitle = document.getElementById("id_event_subtitle");
const category = document.getElementById("id_event_category");
const startDate = document.getElementById("id_start_date");
const startTime = document.getElementById("id_start_time");
const endDate = document.getElementById("id_end_date");
const endTime = document.getElementById("id_end_time");
const maxCapacity = document.getElementById("id_max_capacity");
const registration = document.querySelector(
  'input[name="registration_required"]:checked',
);

const venueSelect = document.getElementById("id_venue");
const venueBuilding = document.getElementById("venue-building");
const venueRoom = document.getElementById("venue-room");
const venueCapacity = document.getElementById("venue-capacity");
const venueLocation = document.getElementById("venue-location");

const previewTitle = document.getElementById("preview-title");
const previewSubtitle = document.getElementById("preview-subtitle");
const previewCategory = document.getElementById("preview-category");
const previewDateTime = document.getElementById("preview-datetime");
const previewVenue = document.getElementById("preview-venue");
const previewCapacity = document.getElementById("preview-capacity");
const previewRegistration = document.getElementById("preview-registration");
const previewOrganizer = document.getElementById("preview-organizer");

const organizerGrid = document.getElementById("organizer-grid");
const organizerTypeGrid = document.getElementById("organizer-type-grid");
const eventFormEl = document.getElementById("event-form");
const IS_EDIT_MODE = eventFormEl.dataset.mode === "edit";
const EVENT_ID = eventFormEl.dataset.eventId;

const progressSteps = {
  basic: 0,
  schedule: 33,
  registration: 67,
};

const progressFill = document.getElementById("ec-progress-fill");
const progressPercent = document.getElementById("ec-progress-percent");
let highestUnlockedProgress = 0;

const DRAFT_KEY = IS_EDIT_MODE ? `event_edit_draft_${EVENT_ID}` : "event_create_draft";
const SECTION_KEY = IS_EDIT_MODE ? `event_edit_section_${EVENT_ID}` : "event_create_section";

const eventVisibility = document.getElementById("id_event_visibility");
const invitedUsersField = document.getElementById("invited-users-field");
const invitedUsersSelect = document.getElementById("id_invited_users");

const INVITATION_ONLY_VALUE = "Invitation Only";

const choicesInstances = window.choicesInstances || {};

function resetChoices(selectId, placeholder) {
  const instance = choicesInstances[selectId];

  if (!instance) return;

  const select = document.getElementById(selectId);

  select.value = "";

  instance.clearStore();
  // Removes populated choices
  instance.clearChoices();

  instance.setChoices(
    [
      {
        value: "",
        label: placeholder,
        selected: true,
      },
    ],
    "value",
    "label",
    true,
  );
}

function populateChoices(selectId, placeholder, items, selectedValue = null) {
  const instance = choicesInstances[selectId];

  if (!instance) return;

  instance.clearStore();
  instance.clearChoices();

  instance.setChoices(
    [
      {
        value: "",
        label: placeholder,
        selected: !selectedValue,
      },
      ...items,
    ],
    "value",
    "label",
    true,
  );

  if (selectedValue) {
    instance.setChoiceByValue(String(selectedValue));
  }
}

function updateProgress(section) {
  const percent = progressSteps[section];

  highestUnlockedProgress = Math.max(highestUnlockedProgress, percent);

  progressFill.style.width = highestUnlockedProgress + "%";
  progressPercent.textContent = highestUnlockedProgress + "%";
}

function showSection(section) {
  Object.values(sections).forEach((sec) => {
    sec.classList.remove("ec-section-active");
  });

  Object.values(pills).forEach((pill) => {
    pill.classList.remove("ec-pill-active");
  });

  sections[section].classList.add("ec-section-active");
  pills[section].classList.add("ec-pill-active");

  localStorage.setItem(SECTION_KEY, section);
  updateProgress(section);

  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
}

function updateVisibilityFields() {
  if (!eventVisibility || !invitedUsersField) return;

  const show = eventVisibility.value === INVITATION_ONLY_VALUE;

  invitedUsersField.classList.toggle("ec-hidden", !show);
  invitedUsersField
    .querySelectorAll("select, input")
    .forEach((el) => (el.disabled = !show));

  if (show) {
    ensureInvitedUsersPicker();
  }
}

function validateSection(sectionId) {
  const section = document.getElementById(sectionId);

  const fields = section.querySelectorAll("input, select, textarea");

  for (const field of fields) {
    if (field.disabled || field.offsetParent === null || !field.willValidate) {
      continue;
    }

    clearValidationError(field);

    if (!field.checkValidity()) {
      let message = field.validationMessage;

      // Custom messages for common validity states
      if (field.validity.valueMissing) {
        message = "This field is required.";
      } else if (field.validity.typeMismatch) {
        message = "Please enter a valid value.";
      } else if (field.validity.rangeUnderflow) {
        message = `Value must be at least ${field.min}.`;
      } else if (field.validity.rangeOverflow) {
        message = `Value cannot exceed ${field.max}.`;
      } else if (field.validity.tooShort) {
        message = `Minimum ${field.minLength} characters required.`;
      } else if (field.validity.tooLong) {
        message = `Maximum ${field.maxLength} characters allowed.`;
      } else if (field.validity.patternMismatch) {
        message = "Please enter a valid value.";
      }

      showValidationError(field, message);

      return false;
    }
  }

  return true;
}

function validateBasicSection() {
  // ---------------------------------------
  // HTML5 required validation
  // ---------------------------------------
  if (!validateSection("basic-section")) {
    return false;
  }

  // ---------------------------------------
  // Get fields
  // ---------------------------------------
  const eventTitle = document.getElementById("id_event_title");
  const eventSubtitle = document.getElementById("id_event_subtitle");
  const eventDescription = document.getElementById("id_event_description");
  const eventCategory = document.getElementById("id_event_category");
  const organizerType = document.getElementById("id_organizer_type");
  const school = document.getElementById("id_school");
  const organizer = document.getElementById("id_organizer");

  // Clear previous errors
  [
    eventTitle,
    eventSubtitle,
    eventDescription,
    eventCategory,
    organizerType,
    school,
    organizer,
    departmentSelect,
    organizationSelect,
  ].forEach(clearValidationError);

  // ==========================================================
  // Event Title
  // ==========================================================

  const title = eventTitle.value.trim();

  if (title.length < 5) {
    showValidationError(
      eventTitle,
      "Event title must contain at least 5 characters.",
    );
    return false;
  }

  if (title.length > 200) {
    showValidationError(
      eventTitle,
      "Event title cannot exceed 200 characters.",
    );
    return false;
  }

  if (!/^[A-Za-z0-9 &(),.:/'@\-]+$/.test(title)) {
    showValidationError(eventTitle, "Event title contains invalid characters.");
    return false;
  }

  if (!/[A-Za-z]/.test(title)) {
    showValidationError(
      eventTitle,
      "Event title must contain at least one alphabet.",
    );
    return false;
  }

  // ==========================================================
  // Event Subtitle (Optional)
  // ==========================================================

  const subtitle = eventSubtitle.value.trim();

  if (subtitle) {
    if (subtitle.length < 5) {
      showValidationError(
        eventSubtitle,
        "Event subtitle must contain at least 5 characters.",
      );
      return false;
    }

    if (subtitle.length > 200) {
      showValidationError(
        eventSubtitle,
        "Event subtitle cannot exceed 200 characters.",
      );
      return false;
    }

    if (!/[A-Za-z]/.test(subtitle)) {
      showValidationError(
        eventSubtitle,
        "Event subtitle must contain at least one alphabet.",
      );
      return false;
    }
  }

  // ==========================================================
  // Event Description
  // ==========================================================

  const description = eventDescription.value.trim();

  if (description.length < 10) {
    showValidationError(
      eventDescription,
      "Event description must contain at least 10 characters.",
    );
    return false;
  }

  if (description.length > 2000) {
    showValidationError(
      eventDescription,
      "Event description cannot exceed 2000 characters.",
    );
    return false;
  }

  // ==========================================================
  // Category
  // ==========================================================

  if (!eventCategory.value) {
    showValidationError(eventCategory, "Please select an event category.");
    return false;
  }

  // ==========================================================
  // Organizer Type
  // ==========================================================

  if (!organizerType.value) {
    showValidationError(organizerType, "Please select an organizer type.");
    return false;
  }

  if (
    (organizerType.value === "Department" ||
      organizerType.value === "Student Organization") &&
    !school.value
  ) {
    showValidationError(school, "Please select a school.");
    return false;
  }


  if (organizerType.value === "Department" && !departmentSelect.value) {
    showValidationError(departmentSelect, "Please select a department.");
    return false;
  }

  if (
    organizerType.value === "Student Organization" &&
    !organizationSelect.value
  ) {
    showValidationError(
      organizationSelect,
      "Please select a student organization.",
    );
    return false;
  }

  // ==========================================================
  // Organizer
  // ==========================================================

  if (!organizer.value) {
    showValidationError(organizer, "Please select an organizer.");
    return false;
  }

  if (
    eventVisibility &&
    eventVisibility.value === INVITATION_ONLY_VALUE &&
    invitedUsersSelect &&
    invitedUsersSelect.selectedOptions.length === 0
  ) {
    showValidationError(
      invitedUsersSelect,
      "Please select at least one person to invite.",
    );
    return false;
  }

  return true;
}

function validateScheduleSection() {
  if (!validateSection("schedule-section")) {
    return false;
  }

  const startDate = document.getElementById("id_start_date");
  const startTime = document.getElementById("id_start_time");
  const endDate = document.getElementById("id_end_date");
  const endTime = document.getElementById("id_end_time");
  const eventMode = document.getElementById("id_event_mode");
  const venue = document.getElementById("id_venue");
  const maxCapacity = document.getElementById("id_max_capacity");

  [
    startDate,
    startTime,
    endDate,
    endTime,
    eventMode,
    venue,
    maxCapacity,
  ].forEach(clearValidationError);

  // ----------------------------------------
  // Start Date
  // ----------------------------------------

  if (!startDate.value) {
    showValidationError(startDate, "Please select the event start date.");
    return false;
  }

  // ----------------------------------------
  // Start Time
  // ----------------------------------------

  if (!startTime.value) {
    showValidationError(startTime, "Please select the event start time.");
    return false;
  }

  // Combine start date & time
  const start = new Date(`${startDate.value}T${startTime.value}`);
  const now = new Date();

  if (start < now) {
    showValidationError(
      startDate,
      "The start date and time cannot be in the past.",
    );
    return false;
  }

  // ----------------------------------------
  // End Date & Time
  // ----------------------------------------

  if (endDate.value && !endTime.value) {
    showValidationError(endTime, "Please select the event end time.");
    return false;
  }

  if (endTime.value && !endDate.value) {
    showValidationError(endDate, "Please select the event end date.");
    return false;
  }

  if (endDate.value && endTime.value) {
    const end = new Date(`${endDate.value}T${endTime.value}`);

    const durationInMinutes = (end - start) / (1000 * 60);

    if (durationInMinutes <= 0) {
      showValidationError(
        endDate,
        "End date and time must be after the start date and time.",
      );
      return false;
    }

    if (durationInMinutes < 10) {
      showValidationError(endDate, "The event must last at least 10 minutes.");
      return false;
    }
  }

  const end = new Date(`${endDate.value}T${endTime.value}`);

  if (end <= start) {
    showValidationError(
      endDate,
      "End date and time must be after the start date and time.",
    );
    return false;
  }

  // ----------------------------------------
  // Event Mode
  // ----------------------------------------

  if (!eventMode.value) {
    showValidationError(eventMode, "Please select an event mode.");
    return false;
  }

  // ----------------------------------------
  // Venue
  // ----------------------------------------

  if (
    (eventMode.value === "Offline" || eventMode.value === "Hybrid") &&
    !venue.value
  ) {
    showValidationError(venue, "Please select an event venue.");
    return false;
  }

  // ----------------------------------------
  // Maximum Capacity
  // ----------------------------------------

  if (maxCapacity.value !== "") {
    const capacity = Number(maxCapacity.value);

    if (capacity < 1) {
      showValidationError(maxCapacity, "Maximum capacity must be at least 1.");
      return false;
    }

    if (capacity > 10000) {
      showValidationError(maxCapacity, "Maximum capacity cannot exceed 10000.");
      return false;
    }

    if (venue.value) {
      const venueCapacity = Number(
        venue.options[venue.selectedIndex].dataset.capacity,
      );

      if (venueCapacity && capacity > venueCapacity) {
        showValidationError(
          maxCapacity,
          `Maximum registration capacity cannot exceed the venue seating capacity (${venueCapacity}).`,
        );
        return false;
      }
    }
  }

  return true;
}

function updateVenueVisibility() {
  const eventMode = document.getElementById("id_event_mode");
  const venueWrapper = document.getElementById("venue-wrapper");

  const endDate = document.getElementById("id_end_date");
  const endTime = document.getElementById("id_end_time");

  const endDateRequired = document.getElementById("end-date-required");
  const endTimeRequired = document.getElementById("end-time-required");

  const showVenue =
    eventMode &&
    (eventMode.value === "Offline" || eventMode.value === "Hybrid");

  venueWrapper.classList.toggle("ec-hidden", !showVenue);

  const showEndRequired = endDate.value || endTime.value;

  endDateRequired.classList.toggle("ec-hidden", !showEndRequired);
  endTimeRequired.classList.toggle("ec-hidden", !showEndRequired);
}

function validateRegistrationSection() {
  if (!validateSection("registration-section")) {
    return false;
  }

  const eventMode = document.getElementById("id_event_mode");

  const isPaidEvent = document.querySelector(
    'input[name="is_paid_event"]:checked',
  );

  const hasAccessibilityInformation = document.querySelector(
    'input[name="has_accessibility_information"]:checked',
  );

  const eventCostWrapper = document.getElementById("event-cost-wrapper");

  const accessibilityContactWrapper = document.getElementById(
    "accessibility-contact-wrapper",
  );

  // ----------------------------------------
  // Elements
  // ----------------------------------------

  const registrationRequired = document.querySelector(
    'input[name="registration_required"]:checked',
  );

  const eventCost = document.getElementById("id_event_cost");

  const eventWebsite = document.getElementById("id_event_website");

  const contactEmail = document.getElementById("id_contact_email");

  const contactPhone = document.getElementById("id_contact_phone");

  const accessibilityEmail = document.getElementById("id_accessibility_email");

  const accessibilityPhone = document.getElementById("id_accessibility_phone");

  [
    eventMode,
    eventCost,
    eventWebsite,
    contactEmail,
    contactPhone,
    accessibilityEmail,
    accessibilityPhone,
  ].forEach(clearValidationError);

  // ----------------------------------------
  // Event Cost
  // ----------------------------------------

  if (isPaidEvent && isPaidEvent.value === "True") {
    if (eventCost.value.trim() === "") {
      showValidationError(
        eventCost,
        "Please provide pricing information for this paid event.",
      );

      return false;
    }

    if (eventCost.value.trim().length > 1000) {
      showValidationError(
        eventCost,
        "Pricing information cannot exceed 1000 characters.",
      );

      return false;
    }
  }

  // ----------------------------------------
  // Event Website
  // ----------------------------------------
  if (
    (eventMode.value === "Online" || eventMode.value === "Hybrid") &&
    eventWebsite.value.trim() === ""
  ) {
    showValidationError(
      eventWebsite,
      "Website URL is required for online and hybrid events.",
    );

    return false;
  }

  // ----------------------------------------
  // Contact Phone
  // ----------------------------------------

  const phone = contactPhone.value.trim();

  if (phone) {
    if (phone.length > 20) {
      showValidationError(
        contactPhone,
        "Phone number cannot exceed 20 characters.",
      );

      return false;
    }

    if (!/^[0-9+\-() ]+$/.test(phone)) {
      showValidationError(contactPhone, "Enter a valid phone number.");

      return false;
    }

    const digits = phone.replace(/\D/g, "");

    if (digits.length < 7) {
      showValidationError(contactPhone, "Enter a valid phone number.");

      return false;
    }
  }

  // ----------------------------------------
  // Registration Required
  // ----------------------------------------

  if (registrationRequired && registrationRequired.value === "True") {
    if (contactEmail.value.trim() === "") {
      showValidationError(
        contactEmail,
        "Provide an email when registration required",
      );

      return false;
    }
  }

  // ----------------------------------------
  // Accessibility
  // ----------------------------------------

  if (
    hasAccessibilityInformation &&
    hasAccessibilityInformation.value === "True"
  ) {
    if (accessibilityEmail.value.trim() === "") {
      showValidationError(
        accessibilityEmail,
        "Accessibility email is required.",
      );

      return false;
    }

    const accessibilityPhoneValue = accessibilityPhone.value.trim();

    if (accessibilityPhoneValue) {
      if (accessibilityPhoneValue.length > 20) {
        showValidationError(
          accessibilityPhone,
          "Phone number cannot exceed 20 characters.",
        );

        return false;
      }

      if (!/^[0-9+\-() ]+$/.test(accessibilityPhoneValue)) {
        showValidationError(accessibilityPhone, "Enter a valid phone number.");

        return false;
      }

      const digits = accessibilityPhoneValue.replace(/\D/g, "");

      if (digits.length < 7) {
        showValidationError(accessibilityPhone, "Enter a valid phone number.");

        return false;
      }
    }
  }

  return true;
}

let invitedUsersChoices = null;

function ensureInvitedUsersPicker() {
  if (invitedUsersChoices || !invitedUsersSelect || typeof Choices === "undefined") return;
  if (invitedUsersSelect.closest(".choices")) return;

  invitedUsersChoices = new Choices(invitedUsersSelect, {
    removeItemButton: true,
    searchEnabled: true,
    searchResultLimit: 20,
    shouldSort: false,
    noResultsText: "No matches found",
    noChoicesText: "Type a name to search...",
    placeholderValue: "Search by name...",
    searchPlaceholderValue: "Type at least 2 letters...",
  });

  choicesInstances["id_invited_users"] = invitedUsersChoices;

  let debounceTimer = null;

  async function runSearch(query) {
    try {
      const params = new URLSearchParams();
      params.set("q", query);

      const response = await fetch(`/dashboard/ajax/search-users/?${params.toString()}`);
      const data = await response.json();

      const existingValues = invitedUsersChoices.getValue(true);

      const newChoices = data
        .filter((user) => !existingValues.includes(String(user.id)))
        .map((user) => ({
          value: String(user.id),
          label: user.name,
        }));

      invitedUsersChoices.setChoices(newChoices, "value", "label", true);
    } catch (err) {
      console.error("User search failed:", err);
    }
  }

  invitedUsersSelect.addEventListener("search", function (event) {
    const query = event.detail.value.trim();

    clearTimeout(debounceTimer);

    if (query.length < 2) {
      return;
    }

    debounceTimer = setTimeout(() => runSearch(query), 300);
  });
}

function updateRegistrationVisibility() {
  const registrationRequired = document.querySelector(
    'input[name="registration_required"]:checked',
  );

  const requiredStar = document.getElementById("contact-email-required");

  requiredStar.classList.toggle(
    "ec-hidden",
    !registrationRequired || registrationRequired.value !== "True",
  );

  const eventMode = document.getElementById("id_event_mode");

  document
    .getElementById("event-website-required")
    .classList.toggle(
      "ec-hidden",
      !eventMode ||
        (eventMode.value !== "Online" && eventMode.value !== "Hybrid"),
    );

  const isPaidEvent = document.querySelector(
    'input[name="is_paid_event"]:checked',
  );

  const hasAccessibilityInformation = document.querySelector(
    'input[name="has_accessibility_information"]:checked',
  );

  document
    .getElementById("event-cost-wrapper")
    .classList.toggle(
      "ec-hidden",
      !isPaidEvent || isPaidEvent.value !== "True",
    );

  document
    .getElementById("event-website-required")
    .classList.toggle(
      "ec-hidden",
      !eventMode ||
        (eventMode.value !== "Online" && eventMode.value !== "Hybrid"),
    );

  document
    .getElementById("accessibility-contact-wrapper")
    .classList.toggle(
      "ec-hidden",
      !hasAccessibilityInformation ||
        hasAccessibilityInformation.value !== "True",
    );
}

function showValidationError(field, message) {
  const choices = field.closest(".ec-field")?.querySelector(".choices");

  if (choices) {
    choices.classList.add("is-invalid");
  }

  const errorDiv = document.getElementById(
    `${field.id.replace("id_", "").replace(/_/g, "-")}-error`,
  );

  if (errorDiv) {
    errorDiv.textContent = message;
    errorDiv.style.display = "block";
  }

  const scrollTarget = choices || field;
  const rect = scrollTarget.getBoundingClientRect();

  const isFullyVisible = rect.top >= 0 && rect.bottom <= window.innerHeight;

  if (!isFullyVisible) {
    scrollTarget.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  }

  // ---------------------------------------
  // Focus the field
  // ---------------------------------------
  if (!choices) {
    field.focus();
  }
}

function clearValidationError(field) {
  field.classList.remove("is-invalid");

  const choices = field.closest(".ec-field")?.querySelector(".choices");

  if (choices) {
    choices.classList.remove("is-invalid");
  }

  const errorDiv = document.getElementById(
    `${field.id.replace("id_", "").replace(/_/g, "-")}-error`,
  );

  if (errorDiv) {
    errorDiv.textContent = "";
    errorDiv.style.display = "none";
  }
}

function saveDraft() {
  const form = document.getElementById("event-form");

  const draft = {};

  form.querySelectorAll("input, select, textarea").forEach((field) => {
    if (!field.name) {
      return;
    }

    if (
      field.type === "hidden" ||
      field.name === "csrfmiddlewaretoken" ||
      field.name === "form_type" ||
      field.name === "action"
    ) {
      return;
    }

    if (field.type === "radio") {
      if (field.checked) {
        draft[field.name] = field.value;
      }

      return;
    }

    if (field.type === "checkbox") {
      draft[field.name] = field.checked;
      return;
    }

    // Everything else
    draft[field.name] = field.value;
  });

  localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
}

async function loadDraft() {
  const draft = localStorage.getItem(DRAFT_KEY);

  if (!draft) {
    return;
  }
  const values = JSON.parse(draft);

  const form = document.getElementById("event-form");

  Object.entries(values).forEach(([name, value]) => {
    if (
      name === "organizer" ||
      name === "csrfmiddlewaretoken" ||
      name === "form_type" ||
      name === "action"
    ) {
      return;
    }

    const fields = form.querySelectorAll(`[name="${name}"]`);

    if (!fields.length) {
      return;
    }

    fields.forEach((field) => {
      if (field.type === "radio") {
        field.checked = field.value === value;
      } else if (field.type === "checkbox") {
        field.checked = value;
      } else {
        field.value = value;

        const instance = choicesInstances[field.id];

        if (instance) {
          instance.setChoiceByValue(value);
        }
      }
    });
  });

  // Show proper fields
  toggleOrganizerFields(false, false);

  // Restore organizer list
  if (
    organizerType.value === "Department" ||
    organizerType.value === "Student Organization"
  ) {
    await handleSchoolChange();

    if (organizerType.value === "Department") {
      choicesInstances["id_department"]?.setChoiceByValue(values.department);

      await handleDepartmentChange();
    } else {
      choicesInstances["id_student_organization"]?.setChoiceByValue(
        values.student_organization,
      );

      await handleOrganizationChange();
    }
  } else if (organizerType.value === "Administration") {
    await populateOrganizerDropdown(
      "/dashboard/ajax/administrators/",
      values.organizer,
    );
  }

  // Restore organizer
  if (values.organizer) {
    organizerSelect.value = values.organizer;

    choicesInstances["id_organizer"]?.setChoiceByValue(values.organizer);
  }

  updateVenueVisibility();
  updateRegistrationVisibility();
  updateVisibilityFields();
  updateEventPreview();
  updateVenueInformation();
}

function clearChoicesSelection(selectId) {
  const instance = choicesInstances[selectId];

  if (!instance) return;

  instance.removeActiveItems(); 
  instance.setChoiceByValue(""); 
}

function toggleOrganizerFields(
  clearSelections = true,
  loadAdministrators = true,
) {
  const value = organizerType.value;

  if (value === "") {
    organizerTypeGrid.classList.remove("ec-grid-2");
  } else if (value === "Administration") {
    organizerTypeGrid.classList.remove("ec-grid-2");
    organizerGrid.classList.remove("ec-grid-2");
  } else {
    organizerTypeGrid.classList.add("ec-grid-2");
    organizerGrid.classList.add("ec-grid-2");
  }

  // Clear all dependent dropdowns
  if (clearSelections) {
    clearChoicesSelection("id_school");
    clearChoicesSelection("id_department");
    clearChoicesSelection("id_student_organization");

    resetChoices("id_organizer", "Select Organizer");
  }

  if (value === "Department") {
    schoolField.style.display = "block";
    departmentField.style.display = "block";
    studentOrganizationField.style.display = "none";
    organizerField.style.display = "block";

    schoolSelect.required = true;
    departmentSelect.required = true;
    organizationSelect.required = false;

    resetChoices("id_department", "Select Department");
  } else if (value === "Student Organization") {
    schoolField.style.display = "block";
    departmentField.style.display = "none";
    studentOrganizationField.style.display = "block";
    organizerField.style.display = "block";

    schoolSelect.required = true;
    departmentSelect.required = false;
    organizationSelect.required = true;

    resetChoices("id_student_organization", "Select Student Organization");
  } else if (value === "Administration") {
    schoolField.style.display = "none";
    departmentField.style.display = "none";
    studentOrganizationField.style.display = "none";
    organizerField.style.display = "block";

    schoolSelect.required = false;
    departmentSelect.required = false;
    organizationSelect.required = false;

    if (loadAdministrators) {
      populateOrganizerDropdown("/dashboard/ajax/administrators/");
    }
  } else {
    schoolField.style.display = "none";
    departmentField.style.display = "none";
    studentOrganizationField.style.display = "none";
    organizerField.style.display = "none";

    schoolSelect.required = false;
    departmentSelect.required = false;
    organizationSelect.required = false;
  }
}

async function populateOrganizerDropdown(url, selectedValue = null) {
  try {
    const response = await fetch(url);

    const data = await response.json();

    populateChoices(
      "id_organizer",
      "Select Organizer",
      data.map((user) => ({
        value: String(user.id),
        label: user.name,
      })),
      selectedValue,
    );
  } catch (error) {
    console.error(error);

    populateChoices("id_organizer", "Unable to load organizers", []);
  }
}

async function handleSchoolChange() {
  const schoolId = schoolSelect.value;

  if (!schoolId) {
    resetChoices("id_department", "Select Department");
    resetChoices("id_student_organization", "Select Student Organization");
    resetChoices("id_organizer", "Select Organizer");

    return;
  }

  if (organizerType.value === "Department") {
    const response = await fetch(
      `/dashboard/ajax/departments/?school_id=${schoolId}`,
    );

    const data = await response.json();

    populateChoices(
      "id_department",
      "Select Department",
      data.map((dept) => ({
        value: String(dept.id),
        label: dept.name,
      })),
    );
  } else if (organizerType.value === "Student Organization") {
    const response = await fetch(
      `/dashboard/ajax/student-organizations/?school_id=${schoolId}`,
    );

    const data = await response.json();

    populateChoices(
      "id_student_organization",
      "Select Student Organization",
      data.map((org) => ({
        value: String(org.id),
        label: org.name,
      })),
    );
  }

  resetChoices("id_organizer", "Select Organizer");
}

async function handleDepartmentChange() {
  const departmentId = departmentSelect.value;

  if (!departmentId) {
    resetChoices("id_organizer", "Select Organizer");

    return;
  }

  await populateOrganizerDropdown(
    `/dashboard/ajax/department-faculty/?department_id=${departmentId}`,
  );
}

async function handleOrganizationChange() {
  const organizationId = organizationSelect.value;

  if (!organizationId) {
    resetChoices("id_organizer", "Select Organizer");

    return;
  }

  await populateOrganizerDropdown(
    `/dashboard/ajax/organization-members/?organization_id=${organizationId}`,
  );
}

function updateVenueInformation() {
  const option = venueSelect.options[venueSelect.selectedIndex];

  if (!venueSelect.value) {
    venueBuilding.textContent = "-";
    venueRoom.textContent = "-";
    venueCapacity.textContent = "-";
    venueLocation.textContent = "-";

    return;
  }

  venueBuilding.textContent = option.dataset.building || "-";

  venueRoom.textContent = option.dataset.room || "-";

  venueCapacity.textContent = `${option.dataset.capacity || "-"} Seats`;

  venueLocation.textContent = option.dataset.location || "-";
}

function formatDateTime(dateTime) {
  if (!dateTime) {
    return "";
  }

  const date = new Date(dateTime);

  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(date);
}

function updateEventPreview() {
  previewTitle.textContent = eventTitle.value.trim() || "Event Title";

  previewSubtitle.textContent = subtitle.value.trim() || "Event Subtitle";

  previewCategory.textContent = category.value
    ? category.selectedOptions[0].text
    : "Category";

  previewVenue.textContent = venueSelect.selectedOptions[0]?.text || "Venue";

  // ----------------------------------------
  // Date & Time Preview
  // ----------------------------------------

  const startDateTime =
    startDate.value && startTime.value
      ? `${startDate.value}T${startTime.value}`
      : "";

  const endDateTime =
    endDate.value && endTime.value ? `${endDate.value}T${endTime.value}` : "";

  if (startDateTime && !endDateTime) {
    previewDateTime.textContent = formatDateTime(startDateTime);
  } else if (startDateTime && endDateTime) {
    previewDateTime.textContent = `${formatDateTime(startDateTime)} - ${formatDateTime(endDateTime)}`;
  } else {
    previewDateTime.textContent = "Date & Time";
  }

  // ----------------------------------------
  // Capacity
  // ----------------------------------------

  if (maxCapacity.value) {
    previewCapacity.textContent = `${maxCapacity.value} Participants`;
  } else {
    const capacity = venueSelect.selectedOptions[0]?.dataset.capacity;

    previewCapacity.textContent = capacity ? `${capacity} Participants` : "-";
  }

  // ----------------------------------------
  // Registration
  // ----------------------------------------

  const registration = document.querySelector(
    'input[name="registration_required"]:checked',
  );

  if (!registration) {
    previewRegistration.textContent = "-";
  } else if (registration.value === "True") {
    previewRegistration.textContent = "Required";
  } else {
    previewRegistration.textContent = "Not Required";
  }
}

async function initEditMode() {
  const dataEl = document.getElementById("edit-initial-data");
  if (!dataEl) {
    updateVenueVisibility();
    updateRegistrationVisibility();
    updateVisibilityFields();
    updateEventPreview();
    updateVenueInformation();
    return;
  }

  const initial = JSON.parse(dataEl.textContent);

  toggleOrganizerFields(false, false);

  if (initial.organizer_type === "Department" || initial.organizer_type === "Student Organization") {
    if (initial.school) {
      schoolSelect.value = initial.school;
      choicesInstances["id_school"]?.setChoiceByValue(initial.school);
      await handleSchoolChange();
    }

    if (initial.organizer_type === "Department" && initial.department) {
      choicesInstances["id_department"]?.setChoiceByValue(initial.department);
      await handleDepartmentChange();
    } else if (initial.organizer_type === "Student Organization" && initial.student_organization) {
      choicesInstances["id_student_organization"]?.setChoiceByValue(initial.student_organization);
      await handleOrganizationChange();
    }
  } else if (initial.organizer_type === "Administration") {
    await populateOrganizerDropdown("/dashboard/ajax/administrators/", initial.organizer);
  }

  if (initial.organizer && initial.organizer_type !== "Administration") {
    choicesInstances["id_organizer"]?.setChoiceByValue(initial.organizer);
  }

  updateVenueVisibility();
  updateRegistrationVisibility();
  updateVisibilityFields();
  updateEventPreview();
  updateVenueInformation();
}

document.addEventListener("DOMContentLoaded", async function () {
  flatpickr(".date-picker", {
    dateFormat: "Y-m-d",
    allowInput: false,
    disableMobile: true,
    appendTo: document.body,
    position: "auto center",
    minDate: "today",
    maxDate: new Date().fp_incr(365 * 5), 

    monthSelectorType: "static",

    onReady(_, __, instance) {
      const yearInput = instance.currentYearElement;

      yearInput.setAttribute("readonly", true);
    },
  });

  flatpickr(".time-picker", {
    enableTime: true,
    noCalendar: true,
    dateFormat: "H:i",
    time_24hr: true,
    minuteIncrement: 5,
    allowInput: false,
    disableMobile: true,
    appendTo: document.body,
    position: "auto center",
  });

  if (document.getElementById("reopen-category-modal")) {
    const categoryModal = new bootstrap.Modal(
      document.getElementById("categoryModal"),
    );

    categoryModal.show();
  }

  if (document.getElementById("reopen-venue-modal")) {
    const venueModal = new bootstrap.Modal(
      document.getElementById("venueModal"),
    );

    venueModal.show();
  }

  if (eventVisibility) {
    eventVisibility.addEventListener("change", updateVisibilityFields);
  }

  document.getElementById("to-schedule").addEventListener("click", () => {
    if (validateBasicSection()) {
      showSection("schedule");
    }
  });

  document.getElementById("back-basic").addEventListener("click", () => {
    showSection("basic");
  });

  document.getElementById("to-registration").addEventListener("click", () => {
    if (validateScheduleSection()) {
      showSection("registration");
    }
  });

  document.getElementById("back-schedule").addEventListener("click", () => {
    showSection("schedule");
  });

  organizerType.addEventListener("change", toggleOrganizerFields);

  schoolSelect.addEventListener("change", handleSchoolChange);

  departmentSelect.addEventListener("change", handleDepartmentChange);

  organizationSelect.addEventListener("change", handleOrganizationChange);

  venueSelect.addEventListener("change", () => {
    updateVenueInformation();
    updateEventPreview();
  });

  maxCapacity.addEventListener("input", function () {
    this.value = this.value.replace(/\D/g, "").slice(0, 5);

    if (parseInt(this.value, 10) > 10000) {
      this.value = "10000";
    }
  });

  document
    .getElementById("id_event_subtitle")
    .addEventListener("input", updateEventPreview);

  document
    .getElementById("id_event_category")
    .addEventListener("change", updateEventPreview);

  eventTitle.addEventListener("input", () => {
    clearValidationError(eventTitle);
    updateEventPreview();
  });

  document
    .getElementById("id_start_date")
    .addEventListener("change", updateEventPreview);

  document
    .getElementById("id_start_time")
    .addEventListener("change", updateEventPreview);

  document
    .getElementById("id_end_date")
    .addEventListener("change", updateEventPreview);

  document
    .getElementById("id_end_time")
    .addEventListener("change", updateEventPreview);

  document
    .getElementById("id_max_capacity")
    .addEventListener("input", updateEventPreview);

  pills.basic.addEventListener("click", () => {
    showSection("basic");
  });

  pills.schedule.addEventListener("click", () => {
    if (validateBasicSection()) {
      showSection("schedule");
    }
  });

  pills.registration.addEventListener("click", () => {
    if (validateBasicSection() && validateScheduleSection()) {
      showSection("registration");
    }
  });

  document
    .getElementById("event-form")
    .addEventListener("submit", function (e) {
      if (
        !validateBasicSection() ||
        !validateScheduleSection() ||
        !validateRegistrationSection()
      ) {
        e.preventDefault();
        return;
      }
      localStorage.removeItem(DRAFT_KEY);
      localStorage.removeItem(SECTION_KEY);
    });

  document
    .getElementById("id_end_date")
    .addEventListener("input", updateVenueVisibility);

  document
    .getElementById("id_end_time")
    .addEventListener("input", updateVenueVisibility);

  document
    .getElementById("id_event_mode")
    .addEventListener("change", updateVenueVisibility);

  // Initial page load
  // updateVenueVisibility();

  document.getElementById("id_event_mode").addEventListener("change", () => {
    updateVenueVisibility();
    updateRegistrationVisibility();
  });

  document
    .querySelectorAll('input[name="registration_required"]')
    .forEach((radio) => {
      radio.addEventListener("change", updateEventPreview);
    });

  document
    .querySelectorAll('input[name="registration_required"]')
    .forEach((radio) => {
      radio.addEventListener("change", updateRegistrationVisibility);
    });

  document.querySelectorAll('input[name="is_paid_event"]').forEach((radio) => {
    radio.addEventListener("change", updateRegistrationVisibility);
  });

  document
    .querySelectorAll('input[name="has_accessibility_information"]')
    .forEach((radio) => {
      radio.addEventListener("change", updateRegistrationVisibility);
    });

  const form = document.getElementById("event-form");

  form.addEventListener("input", saveDraft);

  form.addEventListener("change", saveDraft);

if (IS_EDIT_MODE) {
  await initEditMode();
} else {
  await loadDraft();
}

updateVisibilityFields();

const savedSection = localStorage.getItem(SECTION_KEY);

  if (savedSection && sections[savedSection]) {
    showSection(savedSection);
  } else {
    showSection("basic");
  }
});