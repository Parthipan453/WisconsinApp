

console.log("maintenance.js loaded");
// ==========================
// DOM Elements
// ==========================

const form = document.getElementById("facilityMaintenanceForm");

const modal = document.getElementById("facilityMaintenanceModal");

const facilityId = document.getElementById("facility_id");
const facilityName = document.getElementById("id_facility");
const facilityType = document.getElementById("facility_type");
const facilityIcon = document.getElementById("selectedFacilityIcon");

const title = document.getElementById("id_title");
const description = document.getElementById("id_description");
const status = document.getElementById("id_status");
const priority = document.getElementById("id_priority");
const startDate = document.getElementById("id_start_date");
const expectedDate = document.getElementById("id_expected_completion");
const engineer = document.getElementById("id_engineer");
const contact = document.getElementById("id_contact_number");
const remarks = document.getElementById("id_remarks");

// MODAL EVENTS




modal.addEventListener("show.bs.modal", function (event) {

    

    const button = event.relatedTarget;

    console.log(button.outerHTML);

    // Modal opened through JavaScript (Edit)
    if (!button) {
        return;
    }

    facilityId.value = button.getAttribute("data-facility-id");
    facilityName.value = button.getAttribute("data-facility-name");
    facilityType.value = button.dataset.facilityType

    facilityIcon.className = `bi ${button.dataset.facilityIcon}`;

    console.log("Facility ID :", facilityId.value);
    console.log("Facility Name :", facilityName.value);

});



// ==========================
// Utility Functions
// ==========================

function showError(input, message) {

    input.classList.add("is-invalid");

    let feedback = input.parentElement.querySelector(".invalid-feedback");

    if (!feedback) {

        feedback = document.createElement("div");
        feedback.className = "invalid-feedback";
        input.parentElement.appendChild(feedback);

    }

    feedback.textContent = message;

}

function clearError(input) {

    input.classList.remove("is-invalid");

    const feedback = input.parentElement.querySelector(".invalid-feedback");

    if (feedback) {

        feedback.textContent = "";

    }

}

function clearErrors() {

    document.querySelectorAll(".is-invalid").forEach(function (input) {
        input.classList.remove("is-invalid");
    });

    document.querySelectorAll(".invalid-feedback").forEach(function (feedback) {
        feedback.textContent = "";
    });

}

const expectedPicker = flatpickr("#id_expected_completion", {
    dateFormat: "Y-m-d",
    minDate: "today",
    allowInput: false,
    disableMobile: true
});

flatpickr("#id_start_date", {
    dateFormat: "Y-m-d",
    minDate: "today",
    allowInput: false,
    disableMobile: true,

    onChange: function (selectedDates) {

        clearError(startDate);

        // Expected date cannot be before selected start date
        expectedPicker.set("minDate", selectedDates[0]);

        // Revalidate if expected date already selected
        if (expectedDate.value) {
            validateDates();
        }
    }
});


// VALIDATION STARTED HERE

// ==========================
// Validation Functions
// ==========================

function validateTitle() {

    const value = title.value.trim();

    // Empty
    if (!value) {
        showError(title, "Maintenance title is required.");
        return false;
    }

    // Length
    if (value.length < 5) {
        showError(title, "Title must contain at least 5 characters.");
        return false;
    }

    if (value.length > 100) {
        showError(title, "Title cannot exceed 100 characters.");
        return false;
    }

    // Only numbers not allowed
    if (/^\d+$/.test(value)) {
        showError(title, "Title cannot contain only numbers.");
        return false;
    }

    // Only symbols not allowed
    if (/^[^A-Za-z0-9]+$/.test(value)) {
        showError(title, "Title cannot contain only symbols.");
        return false;
    }

    // Must contain at least one alphabet
    if (!/[A-Za-z]/.test(value)) {
        showError(title, "Title must contain at least one alphabet.");
        return false;
    }

    // Allowed characters only
    if (!/^[A-Za-z0-9\s&()\-.,'/]+$/.test(value)) {
        showError(title, "Title contains invalid characters.");
        return false;
    }

    // Multiple spaces not allowed
    if (/\s{2,}/.test(value)) {
        showError(title, "Multiple consecutive spaces are not allowed.");
        return false;
    }

    clearError(title);
    return true;

}


// VALIDATE DESCRIPTION

function validateDescription() {

    const value = description.value.trim();

    // Required
    if (!value) {
        showError(description, "Description is required.");
        return false;
    }

    // Length
    if (value.length < 10) {
        showError(description, "Description must contain at least 10 characters.");
        return false;
    }

    if (value.length > 1000) {
        showError(description, "Description cannot exceed 1000 characters.");
        return false;
    }

    // Must contain at least one alphabet
    if (!/[A-Za-z]/.test(value)) {
        showError(description, "Description must contain at least one alphabet.");
        return false;
    }

    // Only numbers not allowed
    if (/^\d+$/.test(value)) {
        showError(description, "Description cannot contain only numbers.");
        return false;
    }

    // Only symbols not allowed
    if (/^[^A-Za-z0-9]+$/.test(value)) {
        showError(description, "Description cannot contain only symbols.");
        return false;
    }

    // Multiple consecutive spaces
    if (/\s{2,}/.test(value)) {
        showError(description, "Multiple consecutive spaces are not allowed.");
        return false;
    }

    // Invalid characters
    if (/[<>`{}[\]|\\^~]/.test(value)) {
        showError(description, "Description contains invalid characters.");
        return false;
    }

    clearError(description);

    return true;

}


// VALIDATE ENGINEER

function validateEngineer() {

    const value = engineer.value.trim();

    // Required
    if (!value) {
        showError(engineer, "Assigned engineer is required.");
        return false;
    }

    // Length
    if (value.length < 3) {
        showError(engineer, "Engineer name must contain at least 3 characters.");
        return false;
    }

    if (value.length > 100) {
        showError(engineer, "Engineer name cannot exceed 100 characters.");
        return false;
    }

    // Only numbers not allowed
    if (/^\d+$/.test(value)) {
        showError(engineer, "Engineer name cannot contain only numbers.");
        return false;
    }

    // Only symbols not allowed
    if (/^[^A-Za-z0-9]+$/.test(value)) {
        showError(engineer, "Engineer name cannot contain only symbols.");
        return false;
    }

    // Must contain at least one alphabet
    if (!/[A-Za-z]/.test(value)) {
        showError(engineer, "Engineer name must contain at least one alphabet.");
        return false;
    }

    // Allowed characters
    if (!/^[A-Za-z.\s'-]+$/.test(value)) {
        showError(engineer, "Engineer name contains invalid characters.");
        return false;
    }

    // Multiple spaces
    if (/\s{2,}/.test(value)) {
        showError(engineer, "Multiple consecutive spaces are not allowed.");
        return false;
    }

    clearError(engineer);

    return true;

}


function validateContact() {

    const value = contact.value.trim();

    // Required
    if (!value) {
        showError(contact, "Contact number is required.");
        return false;
    }

    // Only digits
    if (!/^\d+$/.test(value)) {
        showError(contact, "Contact number must contain only digits.");
        return false;
    }

    // Exactly 10 digits
    if (value.length !== 10) {
        showError(contact, "Contact number must be exactly 10 digits.");
        return false;
    }

    // Indian mobile number validation
    if (!/^[6-9]\d{9}$/.test(value)) {
        showError(contact, "Enter a valid Indian mobile number.");
        return false;
    }

    clearError(contact);

    return true;

}

// DATE VALIDATION

function validateDates() {

    const start = startDate.value;
    const expected = expectedDate.value;

    // Both dates are mandatory
    if (!start) {
        showError(startDate, "Please select the start date.");
        return false;
    }

    clearError(startDate);

    if (!expected) {
        showError(expectedDate, "Please select the expected completion date.");
        return false;
    }

    // Expected date should not be before Start date
    if (new Date(expected) < new Date(start)) {
        showError(
            expectedDate,
            "Expected completion date cannot be earlier than the start date."
        );
        return false;
    }

    clearError(expectedDate);

    return true;
}









































// ==========================
// Realtime Validation
// ==========================

title.addEventListener("input", validateTitle);

description.addEventListener("input", validateDescription);

engineer.addEventListener("input", validateEngineer);

contact.addEventListener("input", validateContact);

startDate.addEventListener("change", validateDates);

expectedDate.addEventListener("change", validateDates);








form.addEventListener("submit", function (e) {

    e.preventDefault();

    const formData = new FormData(form);

    console.log(formData.get("facility_id"));
    console.log(formData.get("facility_type"));

    fetch(form.action, {
        method: "POST",
        body: formData,
        headers: {
            "X-Requested-With": "XMLHttpRequest"
        }
    })
    .then(response => response.json())
    .then(data => {


        if (data.success) {

            Swal.fire({

                icon: "success",

                title: data.message,

            });

            const maintenanceId = document.getElementById("maintenance_id").value;

                if (maintenanceId) {

                    const index = window.maintenanceData.findIndex(
                        m => m.id == maintenanceId
                    );

                    if (index !== -1) {
                        window.maintenanceData[index] = data.maintenance;
                    }

                } else {
                    // Add newly created maintenance at the beginning

                    window.maintenanceData.unshift(data.maintenance);

                }

            
            

            // Re-render maintenance cards
            window.renderMaint();

            // ===== Update facility card =====
            const maintenance = data.maintenance;

            const card = document.querySelector(
                `[data-facility-id="${maintenance.facility_id}"][data-facility-type="${maintenance.facility_type}"]`
            );

            if (card) {

                card.classList.add("under-maintenance");

                const maintenanceBtn =
                    card.querySelector(".edit-facility-btn") ||
                    card.querySelector(".maintenance-btn");
                const badge = card.querySelector(".maintenance-badge");

                if (maintenanceBtn) {
                    maintenanceBtn.style.display = "none";
                }

                if (badge) {
                    badge.textContent = "Under Maintenance";
                    badge.classList.remove("smh-avail");
                    badge.classList.add("smh-unavail");
                }
            }

            // Close modal
            bootstrap.Modal.getInstance(modal).hide();
            refreshRecentActivities(1);

        } else {

            console.log(data.errors);

        }

    })
    .catch(error => {

        console.error(error);

    });

});

modal.addEventListener("hidden.bs.modal", function () {

    form.reset();

    facilityType.value = "";

    facilityIcon.className = "bi bi-heart-pulse";

    document.getElementById("maintenance_id").value = "";

    clearErrors();

});







