const hospitalName = document.getElementById("hospitalName");
const hospitalNameError = document.getElementById("hospitalNameError");

function validateHospitalName() {

    // Validation-ku mattum cleaned value
    const value = hospitalName.value.replace(/\s{2,}/g, " ").trim();

    // Required
    if (value === "") {
        return showHospitalNameError("Hospital name is required.");
    }

    // Minimum length
    if (value.length < 3) {
        return showHospitalNameError("Hospital name must be at least 3 characters.");
    }

    // Maximum length
    if (value.length > 50) {
        return showHospitalNameError("Hospital name cannot exceed 50 characters.");
    }

    // First character must be a letter
    if (!/^[A-Za-z]/.test(value)) {
        return showHospitalNameError("Hospital name must start with a letter.");
    }

    // Allowed characters
    if (!/^[A-Za-z0-9\s&().'-]+$/.test(value)) {
        return showHospitalNameError("Only letters, numbers, spaces, &, ., -, ', and () are allowed.");
    }

    clearHospitalNameError();
    return true;
}

function validateMedicalFacilities() {

    const medicalFacilitiesError =
        document.getElementById("MedicalFacilitiesError");

    const selectedFacilities = getSelectedFacilities();

    if (selectedFacilities.length === 0) {

        medicalFacilitiesError.textContent =
            "Please select at least one medical facility.";

        return false;
    }

    medicalFacilitiesError.textContent = "";

    return true;
}

function validateOtherFacilities() {

    const otherFacilitiesError =
        document.getElementById("OtherFacilitiesError");

    const selectedFacilities = getSelectedOtherFacilities();

    if (selectedFacilities.length === 0) {

        otherFacilitiesError.textContent =
            "Please select at least one other facility.";

        return false;
    }

    otherFacilitiesError.textContent = "";

    return true;

}

function showHospitalNameError(message) {
    hospitalName.classList.add("is-invalid");
    hospitalName.classList.remove("is-valid");
    hospitalNameError.textContent = message;
    return false;
}

function clearHospitalNameError() {
    hospitalName.classList.remove("is-invalid");
    hospitalName.classList.add("is-valid");
    hospitalNameError.textContent = "";
}

// Real-time validation
hospitalName.addEventListener("input", validateHospitalName);

// Cleanup only when leaving the field
hospitalName.addEventListener("blur", function () {
    hospitalName.value = hospitalName.value
        .replace(/\s{2,}/g, " ")
        .trim();

    validateHospitalName();
});




// SHORT DESCRIPTION VALIDATION

const shortDesc = document.getElementById("shortDesc");
const shortDescError = document.getElementById("shortDescError");
const shortDescCount = document.getElementById("shortDescCount");

function validateShortDescription() {

    // Validation-ku mattum cleaned value
    const value = shortDesc.value.replace(/\s{2,}/g, " ").trim();

    // Character Counter
    shortDescCount.textContent = value.length;

    shortDescCount.classList.remove("text-warning", "text-danger");

    if (value.length >= 50 && value.length < 120) {
        shortDescCount.classList.add("text-warning");
    }

    if (value.length === 120) {
        shortDescCount.classList.add("text-danger");
    }

    // Required
    if (value === "") {
        return showShortDescError("Short description is required.");
    }

    // Minimum length
    if (value.length < 10) {
        return showShortDescError("Short description must be at least 10 characters.");
    }

    // Maximum length (Extra safety)
    if (value.length > 120) {
        return showShortDescError("Short description cannot exceed 120 characters.");
    }

    // Minimum 2 words
    if (value.split(/\s+/).length < 2) {
        return showShortDescError("Please enter at least two words.");
    }

    // Must contain at least one alphabet
    if (!/[A-Za-z]/.test(value)) {
        return showShortDescError("Description must contain at least one letter.");
    }

    // Allowed characters
    if (!/^[A-Za-z0-9\s&.,()'-]+$/.test(value)) {
        return showShortDescError("Only letters, numbers and basic punctuation are allowed.");
    }

    clearShortDescError();
    return true;
}

function showShortDescError(message) {
    shortDesc.classList.add("is-invalid");
    shortDesc.classList.remove("is-valid");
    shortDescError.textContent = message;
    return false;
}

function clearShortDescError() {
    shortDesc.classList.remove("is-invalid");
    shortDesc.classList.add("is-valid");
    shortDescError.textContent = "";
}

// Real-time validation
shortDesc.addEventListener("input", validateShortDescription);

// Cleanup only when leaving the field
shortDesc.addEventListener("blur", function () {

    shortDesc.value = shortDesc.value
        .replace(/\s{2,}/g, " ")
        .trim();

    validateShortDescription();
});


// ESTABLISHED YEAR VALIDATION

const estYear = document.getElementById("estYear");
const currentYear = new Date().getFullYear();

// Generate years
for (let year = currentYear; year >= 1800; year--) {

    const option = document.createElement("option");

    option.value = year;
    option.textContent = year;

    estYear.appendChild(option);
}


const estYearError = document.getElementById("estYearError");

function validateEstablishedYear() {

    const choicesContainer = estYear.closest(".choices");

    if (estYear.value === "") {

        estYear.classList.add("is-invalid");
        estYear.classList.remove("is-valid");

        if (choicesContainer) {
            choicesContainer.classList.add("choices-invalid");
            choicesContainer.classList.remove("choices-valid");
        }

        estYearError.textContent =
            "Please select the established year.";

        estYearError.style.display = "block";

        console.log("year not selected");

        return false;
    }

    estYear.classList.remove("is-invalid");
    estYear.classList.add("is-valid");

    if (choicesContainer) {
        choicesContainer.classList.remove("choices-invalid");
        choicesContainer.classList.add("choices-valid");
    }

    estYearError.textContent = "";
    estYearError.style.display = "";

    return true;
}

estYear.addEventListener("change", validateEstablishedYear);
estYear.addEventListener("blur", validateEstablishedYear);






// ABOUT VALIDATION

const aboutHospital = document.getElementById("aboutHospital");
const aboutHospitalError = document.getElementById("aboutHospitalError");
const aboutHospitalCount = document.getElementById("aboutHospitalCount");

function validateAboutHospital() {

    // Validation-ku mattum cleaned value
    const value = aboutHospital.value.replace(/\s{2,}/g, " ").trim();

    // Character Counter
    aboutHospitalCount.textContent = aboutHospital.value.length;

    aboutHospitalCount.classList.remove("text-warning", "text-danger");

    if (aboutHospital.value.length >= 450 && aboutHospital.value.length < 500) {
        aboutHospitalCount.classList.add("text-warning");
    }

    if (aboutHospital.value.length === 500) {
        aboutHospitalCount.classList.add("text-danger");
    }

    // Required
    if (value === "") {
        return showAboutHospitalError("About hospital is required.");
    }

    // Minimum length
    if (value.length < 30) {
        return showAboutHospitalError("About hospital must be at least 30 characters.");
    }

    // Maximum length
    if (value.length > 500) {
        return showAboutHospitalError("About hospital cannot exceed 500 characters.");
    }

    // At least 5 words
    if (value.split(/\s+/).length < 5) {
        return showAboutHospitalError("Please enter at least 5 words.");
    }

    // Must contain at least one alphabet
    if (!/[A-Za-z]/.test(value)) {
        return showAboutHospitalError("Description must contain at least one letter.");
    }

    // Allowed characters
    if (!/^[A-Za-z0-9\s&.,()'\/:-]+$/.test(value)) {
        return showAboutHospitalError("Only letters, numbers and basic punctuation are allowed.");
    }

    clearAboutHospitalError();
    return true;
}

function showAboutHospitalError(message) {
    aboutHospital.classList.add("is-invalid");
    aboutHospital.classList.remove("is-valid");
    aboutHospitalError.textContent = message;
    return false;
}

function clearAboutHospitalError() {
    aboutHospital.classList.remove("is-invalid");
    aboutHospital.classList.add("is-valid");
    aboutHospitalError.textContent = "";
}

// Real-time validation
aboutHospital.addEventListener("input", validateAboutHospital);

// Cleanup only when leaving the field
aboutHospital.addEventListener("blur", function () {

    aboutHospital.value = aboutHospital.value
        .replace(/\s{2,}/g, " ")
        .trim();

    validateAboutHospital();
});


// DIRECTOR NAME VALIDATION

// DIRECTOR NAME VALIDATION

const directorName = document.getElementById("directorName");
const directorNameError = document.getElementById("directorNameError");

function validateDirectorName() {

    return true;
}

directorName.addEventListener("change", validateDirectorName);

// BANNER IMAGE VALIDATION

const bannerInput = document.getElementById("bannerInput");
const bannerImg = document.getElementById("bannerImg");
const bannerPreview = document.getElementById("bannerPreview");
const bannerError = document.getElementById("bannerError");

function validateBanner() {

    const file = bannerInput.files[0];

    // No file selected (optional field)
    if (!file) {
        clearBannerError();
        bannerPreview.style.display = "none";
        return true;
    }

    // Allowed image types
    const allowedTypes = [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp"
    ];

    if (!allowedTypes.includes(file.type)) {
        bannerInput.value = "";
        bannerPreview.style.display = "none";
        return showBannerError("Only JPG, JPEG, PNG and WEBP images are allowed.");
    }

    // Max 5MB
    if (file.size > 5 * 1024 * 1024) {
        bannerInput.value = "";
        bannerPreview.style.display = "none";
        return showBannerError("Image size must not exceed 5 MB.");
    }

    // Preview
    const reader = new FileReader();

    reader.onload = function (e) {
        bannerImg.src = e.target.result;
        bannerPreview.style.display = "block";
    };

    reader.readAsDataURL(file);

    clearBannerError();
    return true;
}

function showBannerError(message) {
    bannerInput.classList.add("is-invalid");
    bannerError.textContent = message;
    return false;
}

function clearBannerError() {
    bannerInput.classList.remove("is-invalid");
    bannerError.textContent = "";
}

bannerInput.addEventListener("change", validateBanner); 


// GALLERY IMAGE VALIDATION

// ─── Gallery Upload + Validation ───
// const galleryInput = document.getElementById("galleryInput");
// const galleryPreview = document.getElementById("galleryPreview");
// const galleryError = document.getElementById("galleryError");

// galleryInput.addEventListener("change", function (e) {

//     const files = Array.from(e.target.files);

//     if (files.length === 0) return;

//     const allowedTypes = [
//         "image/jpeg",
//         "image/jpg",
//         "image/png",
//         "image/webp"
//     ];

//     // Validation
//     for (const file of files) {

//         if (!allowedTypes.includes(file.type)) {
//             galleryInput.value = "";
//             return showGalleryError("Only JPG, JPEG, PNG and WEBP images are allowed.");
//         }

//         if (file.size > 2 * 1024 * 1024) {
//             galleryInput.value = "";
//             return showGalleryError(`"${file.name}" exceeds the 2 MB limit.`);
//         }
//     }

//     clearGalleryError();

//     // Existing Preview Logic
//     files.forEach(file => {

//         const reader = new FileReader();

//         reader.onload = function (ev) {

//             const div = document.createElement("div");
//             div.className = "gallery-item";

//             div.innerHTML = `
//                 <img src="${ev.target.result}" alt="Gallery image">
//                 <button class="remove-img" type="button" onclick="this.parentElement.remove()">
//                     <i class="bi bi-x"></i>
//                 </button>
//             `;

//             galleryPreview.appendChild(div);
//         };

//         reader.readAsDataURL(file);
//     });

//     galleryInput.value = "";
// });

// function showGalleryError(message) {
//     galleryInput.classList.add("is-invalid");
//     galleryError.textContent = message;
//     return false;
// }

// function clearGalleryError() {
//     galleryInput.classList.remove("is-invalid");
//     galleryError.textContent = "";
// }



// email


// EMAIL VALIDATION

const email = document.getElementById("email");
const emailError =
    email.parentElement.querySelector(".invalid-feedback");

function validateHospitalEmail() {

    const value = email.value.trim().toLowerCase();

    if (value === "") {

        email.classList.add("is-invalid");
        email.classList.remove("is-valid");

        emailError.textContent =
            "Email address is required.";

        emailError.style.display = "block";

        return false;
    }

    if (value.length > 254) {

        email.classList.add("is-invalid");
        email.classList.remove("is-valid");

        emailError.textContent =
            "Email address is too long.";

        emailError.style.display = "block";

        return false;
    }

    const emailRegex =
        /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;

    if (!emailRegex.test(value)) {

        email.classList.add("is-invalid");
        email.classList.remove("is-valid");

        emailError.textContent =
            "Enter a valid email address.";

        emailError.style.display = "block";

        return false;
    }

    email.classList.remove("is-invalid");
    email.classList.add("is-valid");

    emailError.textContent = "";
    emailError.style.display = "";

    return true;
}

email.addEventListener("input", validateHospitalEmail);

email.addEventListener("blur", function () {
    email.value = email.value.trim().toLowerCase();
    validateHospitalEmail();
});



// PHONE NUMBER VALIDATION

const hospitalPhone = document.getElementById("hospitalPhone");
const phoneError = document.getElementById("phoneError");

function validatePhone() {
    const value = hospitalPhone.value.trim();

    // Required
    if (value === "") {
        return showPhoneError("Phone number is required.");
    }

    // Only digits, spaces, + and -
    if (!/^[\d+\-\s]+$/.test(value)) {
        return showPhoneError("Enter a valid phone number.");
    }

    // + should appear only at the beginning
    if (value.includes("+") && !value.startsWith("+")) {
        return showPhoneError("Invalid phone number format.");
    }

    // Remove spaces, hyphens and +
    const digits = value.replace(/[\s\-+]/g, "");

    // Must contain only digits
    if (!/^\d+$/.test(digits)) {
        return showPhoneError("Enter a valid phone number.");
    }

    // 7 to 15 digits
    if (digits.length < 7 || digits.length > 15) {
        return showPhoneError("Phone number must contain 7 to 15 digits.");
    }

    clearPhoneError();
    return true;
}

function showPhoneError(message) {
    hospitalPhone.classList.add("is-invalid");
    hospitalPhone.classList.remove("is-valid");
    phoneError.textContent = message;
    return false;
}

function clearPhoneError() {
    hospitalPhone.classList.remove("is-invalid");
    hospitalPhone.classList.add("is-valid");
    phoneError.textContent = "";
}

hospitalPhone.addEventListener("input", validatePhone);

hospitalPhone.addEventListener("blur", function () {
    hospitalPhone.value = hospitalPhone.value.trim();
    validatePhone();
});

// EMERGENCY PHONE ERROR

const emergencyPhone = document.getElementById("emergencyPhone");
const emergencyPhoneError = document.getElementById("emergencyPhoneError");

function validateEmergencyPhone() {

    const value = emergencyPhone.value.trim();
    if (value === "") {
                return showEmergencyPhoneError(
            "Emergency phone number is required."
        );

    }
    if (!/^[\d+\-\s]+$/.test(value)) {
        return showEmergencyPhoneError("Phone number contains invalid characters.");
    }
    const cleaned = value.replace(/[\s-]/g, "");
    const indiaPattern = /^(?:\+91|91)?[6-9]\d{9}$/;
    const usPattern = /^(?:\+1|1)?\d{10}$/;

    if (!indiaPattern.test(cleaned) && !usPattern.test(cleaned)) {
        return showEmergencyPhoneError("Enter a valid Indian or US phone number.");
    }

    clearEmergencyPhoneError();
    return true;
}

function showEmergencyPhoneError(message) {
    emergencyPhone.classList.add("is-invalid");
    emergencyPhone.classList.remove("is-valid");
    emergencyPhoneError.textContent = message;
    return false;
}

function clearEmergencyPhoneError() {
    emergencyPhone.classList.remove("is-invalid");
    emergencyPhone.classList.add("is-valid");
    emergencyPhoneError.textContent = "";
}

emergencyPhone.addEventListener("input", validateEmergencyPhone);

emergencyPhone.addEventListener("blur", function () {
    emergencyPhone.value = emergencyPhone.value.trim();
    validatePhone();
});

//HOSPITAL STATUS VALIDATION

// HOSPITAL STATUS VALIDATION

const hospitalStatus =
    document.getElementById("hospitalStatus");

const hospitalstatuserror =
    document.getElementById("hospitalstatuserror");

function validateHospitalStatus() {

    const choicesContainer =
        hospitalStatus.closest(".choices");

    if (hospitalStatus.value === "") {

        // Original select
        hospitalStatus.classList.add("is-invalid");
        hospitalStatus.classList.remove("is-valid");

        // If Choices.js is being used
        if (choicesContainer) {
            choicesContainer.classList.add("choices-invalid");
            choicesContainer.classList.remove("choices-valid");
        }

        // Error
        hospitalstatuserror.textContent =
            "Please select a status.";

        hospitalstatuserror.style.display = "block";

        return false;
    }

    // Valid
    hospitalStatus.classList.remove("is-invalid");
    hospitalStatus.classList.add("is-valid");

    if (choicesContainer) {
        choicesContainer.classList.remove("choices-invalid");
        choicesContainer.classList.add("choices-valid");
    }

    hospitalstatuserror.textContent = "";
    hospitalstatuserror.style.display = "";

    return true;
}

hospitalStatus.addEventListener(
    "change",
    validateHospitalStatus
);

hospitalStatus.addEventListener(
    "blur",
    validateHospitalStatus
);

// statistics validation

function showFieldError(input, errorElement, message) {
    input.classList.add("is-invalid");
    input.classList.remove("is-valid");
    errorElement.textContent = message;
}

function clearFieldError(input, errorElement) {
    input.classList.remove("is-invalid");
    input.classList.add("is-valid");
    errorElement.textContent = "";
}





// MEDICAL FACILITY VALIDATION

// MEDICAL FACILITY VALIDATION

const facilityNameInput =
    document.getElementById("newMedicalFacilityName");

const facilityNameError =
    document.getElementById("namefacilityerror");

function validateFacilityName() {

    const value = facilityNameInput.value
        .replace(/\s{2,}/g, " ")
        .trim();

    // Keep cleaned value in input
    facilityNameInput.value = value;

    // Reset state
    facilityNameInput.classList.remove("is-invalid");
    facilityNameError.textContent = "";

    // Required
    if (value === "") {
        facilityNameError.textContent =
            "Facility name is required.";

        facilityNameInput.classList.add("is-invalid");
        return false;
    }

    // Minimum
    if (value.length < 2) {
        facilityNameError.textContent =
            "Facility name must contain at least 2 characters.";

        facilityNameInput.classList.add("is-invalid");
        return false;
    }

    // Maximum
    if (value.length > 50) {
        facilityNameError.textContent =
            "Facility name cannot exceed 50 characters.";

        facilityNameInput.classList.add("is-invalid");
        return false;
    }

    // Allowed characters
    if (!/^[A-Za-z0-9\s&()+-]+$/.test(value)) {
        facilityNameError.textContent =
            "Invalid characters.";

        facilityNameInput.classList.add("is-invalid");
        return false;
    }

    // At least one letter
    if (!/[A-Za-z]/.test(value)) {
        facilityNameError.textContent =
            "Facility name must contain at least one letter.";

        facilityNameInput.classList.add("is-invalid");
        return false;
    }

    return true;
}

facilityNameInput.addEventListener(
    "input",
    validateFacilityName
);

facilityNameInput.addEventListener("input", validateFacilityName);

// ADD OTHER FACILITY VALIDATION

const otherFacilityNameInput =
    document.getElementById("newOtherFacilityName");

const otherFacilityNameError =
    document.getElementById("otherFacilityNameError");

function validateOtherFacilityName() {

    let value = otherFacilityNameInput.value;
    value = value.replace(/\s+/g, " ");
    otherFacilityNameInput.value = value;

    otherFacilityNameInput.classList.remove("is-invalid");
    otherFacilityNameError.textContent = "";

    if (value.length === 0) {
        otherFacilityNameError.textContent = "Facility name is required.";
        otherFacilityNameInput.classList.add("is-invalid");
        return false;
    }

    if (value.length < 2) {
        otherFacilityNameError.textContent =
            "Facility name must contain at least 2 characters.";
        otherFacilityNameInput.classList.add("is-invalid");
        return false;
    }

    if (value.length > 50) {
        otherFacilityNameError.textContent =
            "Facility name cannot exceed 50 characters.";
        otherFacilityNameInput.classList.add("is-invalid");
        return false;
    }

    if (!/^[A-Za-z0-9\s&()+-]+$/.test(value)) {
        otherFacilityNameError.textContent = "Invalid characters.";
        otherFacilityNameInput.classList.add("is-invalid");
        return false;
    }

    if (!/[A-Za-z]/.test(value)) {
        otherFacilityNameError.textContent =
            "Facility name must contain at least one letter.";
        otherFacilityNameInput.classList.add("is-invalid");
        return false;
    }

    return true;
}

otherFacilityNameInput.addEventListener(
    "input",
    validateOtherFacilityName
);


function validateHospitalForm() {

    console.log("validateHospitalForm called");

    const results = [
        validateHospitalName(),
        validateShortDescription(),
        validateEstablishedYear(),
        validateHospitalStatus(), 
        validateAboutHospital(),
        validateDirectorName(),
        validateBanner(),
        validatePhone(),
        validateEmergencyPhone(),
        validateHospitalEmail(),
        validateMedicalFacilities(),
        validateOtherFacilities(),
    ];

    return results.every(Boolean);
}