 /* kali code */

document.addEventListener("DOMContentLoaded", function () {

    var form = document.getElementById("createTournamentForm");
    if (!form) return;

    var submitBtn = document.getElementById("submitTournamentBtn");
    var loader = document.getElementById("ctLoader");
    var loaderText = document.getElementById("ctLoaderText");
    var toastContainer = document.getElementById("ctToastContainer");
    var reviewSummary = document.getElementById("reviewSummary");

   
    function getCsrfToken() {
        var input = form.querySelector('input[name="csrfmiddlewaretoken"]');
        return input ? input.value : "";
    }
 

    function showToast(type, title, message) {
        var toast = document.createElement("div");
        toast.className = "ct-toast ct-toast--" + type;
        var iconName = type === "success" ? "check-circle-2" : "alert-circle";
        toast.innerHTML =
            '<span class="ct-toast__icon"><i data-lucide="' + iconName + '"></i></span>' +
            '<div class="ct-toast__body">' +
                '<p class="ct-toast__title"></p>' +
                '<p class="ct-toast__message"></p>' +
            "</div>";
        toast.querySelector(".ct-toast__title").textContent = title;
        toast.querySelector(".ct-toast__message").textContent = message || "";
        toastContainer.appendChild(toast);

        if (window.lucide && typeof window.lucide.createIcons === "function") {
            window.lucide.createIcons();
        }

        setTimeout(function () {
            toast.style.opacity = "0";
            toast.style.transform = "translateX(20px)";
            toast.style.transition = "opacity 200ms ease, transform 200ms ease";
            setTimeout(function () { toast.remove(); }, 220);
        }, 5000);
    }


    function clearAllErrors() {
        form.querySelectorAll(".ct-error").forEach(function (el) {
            el.textContent = "";
            el.classList.remove("is-visible");
        });
        form.querySelectorAll(".ct-field.is-invalid").forEach(function (el) {
            el.classList.remove("is-invalid");
        });
    }

    function setFieldError(fieldName, message) {
        var errorEl = form.querySelector('[data-error-for="' + fieldName + '"]');
        if (!errorEl) return;
        errorEl.textContent = message;
        errorEl.classList.add("is-visible");
        var fieldWrap = errorEl.closest(".ct-field");
        if (fieldWrap) fieldWrap.classList.add("is-invalid");
    }

    function applyServerErrors(errors) {
        clearAllErrors();
        var firstField = null;
        Object.keys(errors).forEach(function (key) {
            setFieldError(key, errors[key]);
            if (!firstField) {
                firstField = form.querySelector('[name="' + key + '"]') ||
                    document.querySelector('[data-error-for="' + key + '"]');
            }
        });
        if (firstField && typeof firstField.scrollIntoView === "function") {
            firstField.scrollIntoView({ behavior: "smooth", block: "center" });
        }
    }

       var contactPersonEl = document.getElementById("id_contact_person");
    if (contactPersonEl) {
        contactPersonEl.addEventListener("input", function () {
            var original = contactPersonEl.value;
            var cleaned = original.replace(/[0-9]/g, "");
            if (cleaned !== original) { 
                contactPersonEl.value = cleaned;
                setFieldError("contact_person", "Numbers are not allowed in contact person name.");
            } else {
                var errEl = form.querySelector('[data-error-for="contact_person"]');
                if (errEl) {
                    errEl.textContent = "";
                    errEl.classList.remove("is-visible");
                }
                var fieldWrap = contactPersonEl.closest(".ct-field");
                if (fieldWrap) fieldWrap.classList.remove("is-invalid");
            }
        });
    }

    // --- Mobile Number: block letters, allow only 1-15 digits ---
    var mobileNumberEl = document.getElementById("id_mobile_number");
    if (mobileNumberEl) {
        mobileNumberEl.addEventListener("input", function () {
            var original = mobileNumberEl.value;
            var cleaned = original.replace(/[^0-9]/g, "").slice(0, 15);
            if (cleaned !== original) {
                mobileNumberEl.value = cleaned;
                setFieldError("mobile_number", "Only digits are allowed (1-15 digits).");
            } else {
                var errEl = form.querySelector('[data-error-for="mobile_number"]');
                if (errEl) {
                    errEl.textContent = "";
                    errEl.classList.remove("is-visible");
                }
                var fieldWrap = mobileNumberEl.closest(".ct-field");
                if (fieldWrap) fieldWrap.classList.remove("is-invalid");
            }
        });
    }

 

    var choicesInstances = {};

    function initChoices(id, config) {
        var el = document.getElementById(id);
        if (!el || typeof Choices === "undefined") return null;
        var instance = new Choices(el, Object.assign({
            searchEnabled: true,
            itemSelectText: "",
            shouldSort: false,
            allowHTML: false,
        }, config || {}));
        choicesInstances[id] = instance;
        return instance;
    }

    initChoices("id_sport", { searchEnabled: true });
    initChoices("id_tournament_type", { searchEnabled: false });
    initChoices("id_participation_type", { searchEnabled: false });
    initChoices("id_status", { searchEnabled: false });
    initChoices("id_invitation_type", { searchEnabled: false });


    var DEPARTMENT_ONLY_TYPES = ["INTER_DEPARTMENT", "INTRA_DEPARTMENT"];
    var COLLEGE_TYPES = ["INTER_COLLEGE", "INTRA_COLLEGE"];

    var invitationTypeEl = document.getElementById("id_invitation_type");
    var tournamentTypeEl = document.getElementById("id_tournament_type");
    var collegeNameField = document.getElementById("collegeNameField");
    var departmentNameField = document.getElementById("departmentNameField");
    var collegeSelectField = document.getElementById("collegeSelectField");
    var departmentSelectField = document.getElementById("departmentSelectField");
    var receiverSelectField = document.getElementById("receiverSelectField");
    var recipientsSection = document.querySelector('[data-section="recipients"]');
    var collegeSelect = document.getElementById("id_college");
    var departmentSelect = document.getElementById("id_department");
    var receiverSelect = document.getElementById("id_receiver_faculty");

    var collegeChoices = initChoices("id_college", { searchEnabled: true });
    var departmentChoices = initChoices("id_department", { searchEnabled: true });
    var receiverChoices = initChoices("id_receiver_faculty", { searchEnabled: true, removeItemButton: true });

    var collegesLoaded = false;

    function setFieldHidden(fieldEl, selectEl, isHidden) {
        if (!fieldEl) return;
        fieldEl.hidden = isHidden;
        if (selectEl) selectEl.disabled = isHidden;
    }

    function loadColleges() {
        fetch("/dashboard/tournaments/invitation/colleges/", { credentials: "same-origin" })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                var choicesList = [{ value: "", label: "Select college…", selected: true, disabled: false }];
                data.forEach(function (item) { choicesList.push({ value: item.id, label: item.name }); });
                choicesList.push({ value: "OTHER", label: "Other" });
                collegeChoices.clearStore();
                collegeChoices.setChoices(choicesList, "value", "label", true);
            });
    }

    function loadDepartments(schoolId) {
        fetch("/dashboard/ajax/get-departments/?school_id=" + encodeURIComponent(schoolId), { credentials: "same-origin" })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                var choicesList = [{ value: "", label: "Select department…", selected: true, disabled: false }];
                data.forEach(function (item) { choicesList.push({ value: item.id, label: item.name }); });
                departmentChoices.clearStore();
                departmentChoices.setChoices(choicesList, "value", "label", true);
            });
    }

    function loadReceivers(departmentId) {
        fetch("/dashboard/tournaments/invitation/faculty/?department_id=" + encodeURIComponent(departmentId), { credentials: "same-origin" })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                var choicesList = data.map(function (item) { return { value: String(item.id), label: item.name }; });
                receiverChoices.clearStore();
                receiverChoices.setChoices(choicesList, "value", "label", true);
            });
    }

  
    function isCollegeCascadeActive() {
        return invitationTypeEl.value === "DEPARTMENT";
    }

    function isReceiverModeActive() {
        return isCollegeCascadeActive() && collegeSelect.value && collegeSelect.value !== "OTHER";
    }



    function updateInvitationModeUI() {
    var invitationType = invitationTypeEl.value;
    setFieldError("invitation_type", "");
    var invTypeErr = document.querySelector('[data-error-for="invitation_type"]');
    if (invTypeErr) invTypeErr.classList.remove("is-visible");

    if (invitationType !== "DEPARTMENT") {
        setFieldHidden(collegeNameField, null, false);
        setFieldHidden(departmentNameField, null, false);
        setFieldHidden(collegeSelectField, collegeSelect, true);
        setFieldHidden(departmentSelectField, departmentSelect, true);
        setFieldHidden(receiverSelectField, receiverSelect, true);
        if (recipientsSection) recipientsSection.hidden = false;
        return;
    }

    setFieldHidden(collegeNameField, null, true);
    setFieldHidden(departmentNameField, null, true);
    setFieldHidden(collegeSelectField, collegeSelect, false);
    collegeSelect.disabled = false;
    if (collegeChoices) collegeChoices.enable();

    if (!collegesLoaded) {
        loadColleges();
        collegesLoaded = true;
    }

    var isOther = collegeSelect.value === "OTHER";
    setFieldHidden(collegeNameField, null, !isOther);
    setFieldHidden(departmentNameField, null, !isOther);
    setFieldHidden(departmentSelectField, departmentSelect, isOther);
    setFieldHidden(receiverSelectField, receiverSelect, isOther);
    // if (recipientsSection) recipientsSection.hidden = isReceiverModeActive();
    if (recipientsSection) {
        recipientsSection.hidden = true;
    }
}

    invitationTypeEl.addEventListener("change", updateInvitationModeUI);
    tournamentTypeEl.addEventListener("change", updateInvitationModeUI);

 

    collegeSelect.addEventListener("change", function () {

   
    departmentSelect.disabled = false;

    if (departmentChoices) {
        departmentChoices.enable();
    }

    departmentChoices.clearStore();
    departmentChoices.setChoices(
        [{ value: "", label: "Select department…", selected: true, disabled: false }],
        "value", "label", true
    );

    receiverSelect.disabled = true;

    if (receiverChoices) {
        receiverChoices.disable();
    }

    receiverChoices.clearStore();

    if (collegeSelect.value && collegeSelect.value !== "OTHER") {
        loadDepartments(collegeSelect.value);
    }

    updateInvitationModeUI();
});


var participationTypeEl = document.getElementById("id_participation_type");
var minimumParticipantsEl = document.getElementById("id_minimum_participants");
var maximumParticipantsEl = document.getElementById("id_maximum_participants");


function updateParticipantFields() {
    if (!participationTypeEl || !minimumParticipantsEl || !maximumParticipantsEl) {
        return;
    }

    var isIndividual = participationTypeEl.value === "INDIVIDUAL";

    var minField = minimumParticipantsEl.closest(".ct-field");
    var maxField = maximumParticipantsEl.closest(".ct-field");

    if (isIndividual) {
        minimumParticipantsEl.disabled = true;
        maximumParticipantsEl.disabled = true;

        minimumParticipantsEl.required = false;
        maximumParticipantsEl.required = false;

        minimumParticipantsEl.value = "";
        maximumParticipantsEl.value = "";

        if (minField) {
            minField.classList.add("ct-field--disabled");
        }

        if (maxField) {
            maxField.classList.add("ct-field--disabled");
        }

        setFieldError("minimum_participants", "");
        setFieldError("maximum_participants", "");

        var minError = document.querySelector(
            '[data-error-for="minimum_participants"]'
        );

        var maxError = document.querySelector(
            '[data-error-for="maximum_participants"]'
        );

        if (minError) minError.classList.remove("is-visible");
        if (maxError) maxError.classList.remove("is-visible");

        if (minField) minField.classList.remove("is-invalid");
        if (maxField) maxField.classList.remove("is-invalid");

    } else {
        minimumParticipantsEl.disabled = false;
        maximumParticipantsEl.disabled = false;

        minimumParticipantsEl.required = true;
        maximumParticipantsEl.required = true;

        if (minField) {
            minField.classList.remove("ct-field--disabled");
        }

        if (maxField) {
            maxField.classList.remove("ct-field--disabled");
        }
    }
}


if (participationTypeEl) {
    participationTypeEl.addEventListener("change", updateParticipantFields);
}

updateParticipantFields();


   
    departmentSelect.addEventListener("change", function () {

        
        receiverSelect.disabled = false;

        if (receiverChoices) {
            receiverChoices.enable();
        }

        receiverChoices.clearStore();

        if (departmentSelect.value) {
            loadReceivers(departmentSelect.value);
        }
    });

    updateInvitationModeUI();

    var clubChoices = initChoices("id_club", { searchEnabled: true });
    var venueChoices = initChoices("id_venue", { searchEnabled: true });

   

    function readJsonScript(id) {
        var el = document.getElementById(id);
        if (!el) return [];
        try {
            return JSON.parse(el.textContent) || [];
        } catch (e) {
            return [];
        }
    }

    var allClubs = readJsonScript("clubs-data");
    var allVenues = readJsonScript("venues-data");

    function refreshDependentDropdown(instance, items, placeholder) {
        if (!instance) return;
        instance.clearStore();
        var choicesList = [{ value: "", label: placeholder, selected: true, disabled: false }];
        items.forEach(function (item) {
            choicesList.push({ value: String(item.id), label: item.name });
        });
        instance.setChoices(choicesList, "value", "label", true);
    }

    function onSportChange() {
        var sportSelect = document.getElementById("id_sport");
        var sportId = sportSelect ? sportSelect.value : "";

        var filteredClubs = sportId
            ? allClubs.filter(function (c) { return String(c.sport_id) === String(sportId); })
            : allClubs;

        var filteredVenues = sportId
            ? allVenues.filter(function (v) {
                return v.sport_id === null || String(v.sport_id) === String(sportId);
            })
            : allVenues;

        refreshDependentDropdown(clubChoices, filteredClubs, "Select club (optional)");
        refreshDependentDropdown(venueChoices, filteredVenues, "Select venue (optional)");
    }

    var sportEl = document.getElementById("id_sport");
    if (sportEl) {
        sportEl.addEventListener("change", onSportChange);
        onSportChange();
    }

  

    var fpDeadline, fpStart, fpEnd;

    if (typeof flatpickr !== "undefined") {
        fpDeadline = flatpickr("#id_registration_deadline", {
            dateFormat: "Y-m-d",
            onChange: validateDateChain,
        });
        fpStart = flatpickr("#id_start_date", {
            dateFormat: "Y-m-d",
            onChange: validateDateChain,
        });
        fpEnd = flatpickr("#id_end_date", {
            dateFormat: "Y-m-d",
            onChange: validateDateChain,
        });
    }

    function parseDate(value) {
        if (!value) return null;
        var d = new Date(value + "T00:00:00");
        return isNaN(d.getTime()) ? null : d;
    }

    function validateDateChain() {
        var deadline = parseDate(document.getElementById("id_registration_deadline").value);
        var start = parseDate(document.getElementById("id_start_date").value);
        var end = parseDate(document.getElementById("id_end_date").value);

        setFieldError("registration_deadline", "");
        setFieldError("start_date", "");
        setFieldError("end_date", "");
        document.querySelector('[data-error-for="registration_deadline"]').classList.remove("is-visible");
        document.querySelector('[data-error-for="start_date"]').classList.remove("is-visible");
        document.querySelector('[data-error-for="end_date"]').classList.remove("is-visible");

        var valid = true;

        if (deadline && start && deadline > start) {
            setFieldError("registration_deadline", "Registration deadline cannot be after the start date.");
            valid = false;
        }
        if (start && end && start > end) {
            setFieldError("end_date", "End date cannot be before the start date.");
            valid = false;
        }
        return valid;
    }

    

    var emailTagsWrap = document.getElementById("emailTags");
    var emailInput = document.getElementById("id_email_input");
    var emails = [];

    var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    function renderEmailTags() {
        emailTagsWrap.querySelectorAll(".ct-email-tag").forEach(function (el) { el.remove(); });

        emails.forEach(function (entry, index) {
            var tag = document.createElement("span");
            tag.className = "ct-email-tag" + (entry.valid ? "" : " ct-email-tag--invalid");
            tag.innerHTML =
                '<span class="ct-email-tag__text"></span>' +
                '<button type="button" class="ct-email-tag__remove" aria-label="Remove email">' +
                '<i data-lucide="x"></i></button>';
            tag.querySelector(".ct-email-tag__text").textContent = entry.value;
            tag.querySelector(".ct-email-tag__remove").addEventListener("click", function () {
                emails.splice(index, 1);
                renderEmailTags();
            });
            emailTagsWrap.insertBefore(tag, emailInput);
        });

        if (window.lucide && typeof window.lucide.createIcons === "function") {
            window.lucide.createIcons();
        }
    }

    function addEmail(raw) {
        var value = (raw || "").trim().replace(/,+$/, "");
        if (!value) return;
        var isDuplicate = emails.some(function (e) {
            return e.value.toLowerCase() === value.toLowerCase();
        });
        if (isDuplicate) {
            setFieldError("emails", "\"" + value + "\" was already added.");
            return;
        }
        emails.push({ value: value, valid: EMAIL_RE.test(value) });
        setFieldError("emails", "");
        document.querySelector('[data-error-for="emails"]').classList.remove("is-visible");
        renderEmailTags();
    }

    function addEmailsFromText(text) {
        text.split(/[,\n]/).forEach(function (part) { addEmail(part); });
    }

    if (emailInput) {
        emailInput.addEventListener("keydown", function (e) {
            if (e.key === "Enter" || e.key === ",") {
                e.preventDefault();
                addEmail(emailInput.value);
                emailInput.value = "";
            } else if (e.key === "Backspace" && !emailInput.value && emails.length) {
                emails.pop();
                renderEmailTags();
            }
        });

        emailInput.addEventListener("blur", function () {
            if (emailInput.value.trim()) {
                addEmail(emailInput.value);
                emailInput.value = "";
            }
        });

        emailInput.addEventListener("paste", function (e) {
            var pasted = (e.clipboardData || window.clipboardData).getData("text");
            if (pasted.indexOf(",") !== -1 || pasted.indexOf("\n") !== -1) {
                e.preventDefault();
                addEmailsFromText(pasted);
            }
        });
    }



    function formatBytes(bytes) {
        if (!bytes) return "0 KB";
        var kb = bytes / 1024;
        if (kb < 1024) return kb.toFixed(0) + " KB";
        return (kb / 1024).toFixed(1) + " MB";
    }

    function setupImageUpload(key, maxBytes) {
        var wrap = document.querySelector('[data-upload="' + key + '"]');
        if (!wrap) return;
        var input = wrap.querySelector(".ct-upload__input");
        var dropzone = wrap.querySelector(".ct-upload__dropzone");
        var preview = wrap.querySelector(".ct-upload__preview");
        var empty = wrap.querySelector(".ct-upload__empty");
        var removeBtn = wrap.querySelector(".ct-upload__remove");

        dropzone.addEventListener("click", function () { input.click(); });

        input.addEventListener("change", function () {
            var file = input.files[0];
            setFieldError(key, "");
            document.querySelector('[data-error-for="' + key + '"]').classList.remove("is-visible");
            if (!file) return;

            if (maxBytes && file.size > maxBytes) {
                setFieldError(key, "File is too large. Maximum size is " + formatBytes(maxBytes) + ".");
                input.value = "";
                return;
            }

            var reader = new FileReader();
            reader.onload = function (e) {
                preview.src = e.target.result;
                preview.hidden = false;
                empty.hidden = true;
                removeBtn.hidden = false;
            };
            reader.readAsDataURL(file);
        });

        removeBtn.addEventListener("click", function (e) {
            e.stopPropagation();
            input.value = "";
            preview.hidden = true;
            empty.hidden = false;
            removeBtn.hidden = true;
        });
    }

    function setupPdfUpload(key, maxBytes) {
        var wrap = document.querySelector('[data-upload="' + key + '"]');
        if (!wrap) return;
        var input = wrap.querySelector(".ct-upload__input");
        var dropzone = wrap.querySelector(".ct-upload__dropzone");
        var empty = wrap.querySelector(".ct-upload__empty");
        var fileInfo = wrap.querySelector(".ct-upload__file-info");
        var fileName = wrap.querySelector(".ct-upload__file-name");
        var fileSize = wrap.querySelector(".ct-upload__file-size");
        var removeBtn = wrap.querySelector(".ct-upload__remove");

        dropzone.addEventListener("click", function () { input.click(); });

        input.addEventListener("change", function () {
            var file = input.files[0];
            setFieldError(key, "");
            document.querySelector('[data-error-for="' + key + '"]').classList.remove("is-visible");
            if (!file) return;

            if (file.type !== "application/pdf") {
                setFieldError(key, "Only PDF files are accepted.");
                input.value = "";
                return;
            }
            if (maxBytes && file.size > maxBytes) {
                setFieldError(key, "File is too large. Maximum size is " + formatBytes(maxBytes) + ".");
                input.value = "";
                return;
            }

            fileName.textContent = file.name;
            fileSize.textContent = formatBytes(file.size);
            empty.hidden = true;
            fileInfo.hidden = false;
            removeBtn.hidden = false;
        });

        removeBtn.addEventListener("click", function (e) {
            e.stopPropagation();
            input.value = "";
            fileInfo.hidden = true;
            empty.hidden = false;
            removeBtn.hidden = true;
        });
    }

    setupImageUpload("banner", 5 * 1024 * 1024);
    setupImageUpload("logo", 5 * 1024 * 1024); 
    setupPdfUpload("rules_pdf", 10 * 1024 * 1024);


    function updateReviewSummary() {
        var name = document.getElementById("id_tournament_name").value.trim();
        var code = document.getElementById("id_tournament_code").value.trim();
        var sportSelect = document.getElementById("id_sport");
        var sportLabel = sportSelect && sportSelect.selectedIndex >= 0
            ? sportSelect.options[sportSelect.selectedIndex].text : "";
        var start = document.getElementById("id_start_date").value;
        var end = document.getElementById("id_end_date").value;
        var maxParticipants = document.getElementById("id_maximum_participants").value;

        var items = [];
        if (name) items.push(["Tournament", name]);
        if (code) items.push(["Code", code]);
        if (sportSelect && sportSelect.value) items.push(["Sport", sportLabel]);
        if (start && end) items.push(["Dates", start + " → " + end]);
        if (maxParticipants) items.push(["Max Participants", maxParticipants]);
        if (emails.length) items.push(["Recipients", emails.length + " email(s)"]);

        if (!items.length) {
            reviewSummary.innerHTML = '<div class="ct-review-summary__empty">Fill in the form above — a quick summary will appear here.</div>';
            return;
        }

        reviewSummary.innerHTML = items.map(function (pair) {
            return '<div class="ct-review-item">' +
                '<span class="ct-review-item__label"></span>' +
                '<span class="ct-review-item__value"></span>' +
                "</div>";
        }).join("");

        var nodes = reviewSummary.querySelectorAll(".ct-review-item");
        nodes.forEach(function (node, i) {
            node.querySelector(".ct-review-item__label").textContent = items[i][0];
            node.querySelector(".ct-review-item__value").textContent = items[i][1];
        });
    }

    form.addEventListener("input", updateReviewSummary);
    form.addEventListener("change", updateReviewSummary);



    var loaderSteps = [
        "Creating tournament...",
        "Preparing invitations...",
        "Sending tournament invitations...",
    ];
    var loaderInterval = null;

        function showLoader() {
        var step = 0;
        var steps = isReceiverModeActive()
            ? ["Creating tournament...", "Preparing invitations...", "Sending Invitations..."]
            : loaderSteps;
        loaderText.textContent = steps[0];
        loader.hidden = false;
        loaderInterval = setInterval(function () {
            step = (step + 1) % steps.length;
            loaderText.textContent = steps[step];
        }, 1400);
    }


    function hideLoader() {
        if (loaderInterval) clearInterval(loaderInterval);
        loader.hidden = true;
    }

   

    function validateForm() {
        clearAllErrors();
        var valid = true;

        function required(id, label) {
            var el = document.getElementById(id);
            if (!el.value || !el.value.trim()) {
                setFieldError(el.name, label + " is required.");
                valid = false;
            }
        }

        required("id_tournament_name", "Tournament name");
        required("id_tournament_code", "Tournament code");
        required("id_sport", "Sport");
        required("id_tournament_type", "Tournament type");
        required("id_participation_type", "Participation type");
        required("id_registration_deadline", "Registration deadline");
        required("id_start_date", "Start date");
        required("id_end_date", "End date");

               
       var contactPersonVal = document.getElementById("id_contact_person").value.trim();
       if (contactPersonVal && /[0-9]/.test(contactPersonVal)) {
           setFieldError("contact_person", "Numbers are not allowed in contact person name.");
           valid = false;
       }

       var mobileNumberVal = document.getElementById("id_mobile_number").value.trim();
       if (mobileNumberVal) {
           if (/[^0-9]/.test(mobileNumberVal)) {
               setFieldError("mobile_number", "Only digits are allowed (1-15 digits).");
               valid = false;
          } else if (mobileNumberVal.length < 1 || mobileNumberVal.length > 15) {
              setFieldError("mobile_number", "Mobile number must be 1-15 digits.");
              valid = false;
           }
       }
       

        if (!validateDateChain()) valid = false;


        if (participationTypeEl.value !== "INDIVIDUAL") {

    required(
        "id_minimum_participants",
        "Minimum participants"
    );

    required(
        "id_maximum_participants",
        "Maximum participants"
    );

    var minP = parseInt(
        minimumParticipantsEl.value,
        10
    );

    var maxP = parseInt(
        maximumParticipantsEl.value,
        10
    );

    if (!isNaN(minP) && minP < 1) {
        setFieldError(
            "minimum_participants",
            "Minimum participants must be at least 1."
        );
        valid = false;
    }

    if (!isNaN(minP) &&
        !isNaN(maxP) &&
        maxP < minP) {

        setFieldError(
            "maximum_participants",
            "Maximum participants must be greater than or equal to the minimum."
        );

        valid = false;
    }
}

        var entryFee = document.getElementById("id_entry_fee").value;
        if (entryFee !== "" && parseFloat(entryFee) < 0) {
            setFieldError("entry_fee", "Entry fee cannot be negative.");
            valid = false;
        }

                if (isReceiverModeActive()) {
            var selectedReceivers = receiverChoices ? receiverChoices.getValue(true) : [];
            if (!selectedReceivers.length) {
                setFieldError("receiver_faculty_ids", "Select at least one receiver.");
                valid = false;
            }
        } else if (!emails.length) {
            setFieldError("emails", "Add at least one recipient email.");
            valid = false;
        } else if (emails.some(function (e) { return !e.valid; })) {
            setFieldError("emails", "One or more email addresses are invalid. Remove or fix them before continuing.");
            valid = false;
        }
        return valid;
    }

    

    form.addEventListener("submit", function (e) {
        e.preventDefault();

        if (!validateForm()) {
            showToast("error", "Check the form", "Some fields need your attention before the tournament can be created.");
            return;
        }

        var formData = new FormData(form);
        formData.set("emails", JSON.stringify(emails.map(function (e) { return e.value; })));
        formData.set("receiver_faculty_ids", JSON.stringify(receiverChoices ? receiverChoices.getValue(true) : []));

        submitBtn.disabled = true;
        showLoader();

        fetch(form.dataset.submitUrl, {
            method: "POST",
            headers: { "X-CSRFToken": getCsrfToken() },
            body: formData,
            credentials: "same-origin",
        })
            // .then(function (response) {
            //     return response.json().then(function (data) {
            //         return { status: response.status, data: data };
            //     });
            // })
            .then(function (response) {
                return response.json().then(function (data) {

                    // console.log("===== TOURNAMENT CREATE RESPONSE =====");
                    // console.log("HTTP STATUS:", response.status);
                    // console.log("SERVER RESPONSE:", data);

                    if (data.errors) {
                        console.table(data.errors);
                    }
 
                    

                    return {
                        status: response.status,
                        data: data
                    };
                });
            })
            .then(function (result) {
                hideLoader();
                if (result.data && result.data.ok) {
                    showToast(
                        "success",
                        "Tournament created",
                        result.data.message || (
                            "Tournament created successfully. " +
                            (result.data.emails_sent || 0) + " invitation(s) sent."
                        )
                    );
                    setTimeout(function () {
                        window.location.href = result.data.redirect_url || "/tournaments/";
                    }, 1800);
                } else {
                    submitBtn.disabled = false;
                    if (result.data && result.data.errors) {
                        applyServerErrors(result.data.errors);
                    }
                    showToast(
                        "error",
                        "Could not create tournament",
                        (result.data && result.data.message) || "Please review the form and try again."
                    );
                }
            })
            .catch(function () {
                hideLoader();
                submitBtn.disabled = false;
                showToast("error", "Something went wrong", "The request failed. Check your connection and try again.");
            });
    });

    updateReviewSummary();
});