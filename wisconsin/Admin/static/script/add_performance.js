/* kali's code  */

(function () {
    "use strict";

    const $ = (sel, ctx) => (ctx || document).querySelector(sel);
    const $$ = (sel, ctx) => Array.from((ctx || document).querySelectorAll(sel));

    const CREATE_URL = "/dashboard/olympics/performances/create/";
    const LIST_URL = "/dashboard/olympics/performances/";
    const UPDATE_URL_TEMPLATE = "/dashboard/olympics/performances/{uuid}/update/";

    let isSubmitting = false;
    let athleteChoices = null;

   
    function refreshIcons() {
        if (window.lucide && typeof window.lucide.createIcons === "function") {
            window.lucide.createIcons();
        }
    }


    function showOlyToast(type, title, message) {
        const toast = $("#roleToast");
        const iconWrap = $("#toastIconWrap");
        const icon = $("#toastIcon");
        const titleEl = $("#toastTitle");
        const msgEl = $("#toastMsg");
        if (!toast) return;

        iconWrap.classList.remove("role-toast__icon-wrap--success", "role-toast__icon-wrap--error");
        iconWrap.classList.add(type === "success" ? "role-toast__icon-wrap--success" : "role-toast__icon-wrap--error");

        if (icon) icon.setAttribute("data-lucide", type === "success" ? "check-circle-2" : "x-circle");
        if (titleEl) titleEl.textContent = title;
        if (msgEl) msgEl.textContent = message;

        toast.hidden = false;
        toast.classList.remove("hiding");
        refreshIcons();

        clearTimeout(toast._opfTimer);
        toast._opfTimer = setTimeout(() => hideOlyToast(), 4000);
    }

    function hideOlyToast() {
        const toast = $("#roleToast");
        if (!toast || toast.hidden) return;
        toast.classList.add("hiding");
        setTimeout(() => {
            toast.hidden = true;
            toast.classList.remove("hiding");
        }, 250);
    }

    function wireToastClose() {
        $("#toastClose")?.addEventListener("click", () => {
            clearTimeout($("#roleToast")?._opfTimer);
            hideOlyToast();
        });
    }



    function initAthleteSelect() {
        const el = $("#opfAthleteSelect");
        if (!el || !window.Choices) return;

        const optionEls = $$("option", el).filter((o) => o.value);
        const hasSelectedAthlete = optionEls.some((o) => o.hasAttribute("selected"));

        const choicesData = [
            {
                value: "",
                label: "Select an athlete",
                selected: !hasSelectedAthlete,
                disabled: true,
                placeholder: true,
            },
            ...optionEls.map((o) => ({
                value: o.value,
                label: o.textContent.trim(),
                selected: o.hasAttribute("selected"),
                customProperties: {
                    photo: o.dataset.photo || "",
                    subtext: o.dataset.subtext || "",
                },
            })),
        ];
        el.innerHTML = "";

        athleteChoices = new Choices(el, {
            searchEnabled: true,
            searchPlaceholderValue: "Search by name or athlete ID...",
            searchFields: ["label", "customProperties.subtext"],
            itemSelectText: "",
            shouldSort: false,
            placeholder: true,
            placeholderValue: "Select an athlete",
            renderSelectedChoices: "always",
            choices: choicesData,
            callbackOnCreateTemplates: function (template) {
                return {
                    item: ({ classNames }, data) => {
                        const photo = (data.customProperties && data.customProperties.photo) || "";
                        return template(`
                            <div class="${classNames.item} opf-choice-row" data-item data-id="${data.id}" data-value="${data.value}">
                                ${photo ? `<span class="opf-choice-avatar"><img src="${photo}" alt=""></span>` : ""}
                                <span>${data.label}</span>
                            </div>
                        `);
                    },
                    choice: ({ classNames }, data) => {
                        const photo = (data.customProperties && data.customProperties.photo) || "";
                        const subtext = (data.customProperties && data.customProperties.subtext) || "";
                        return template(`
                            <div class="${classNames.item} ${classNames.itemChoice} opf-choice-row" data-select-text="" data-choice ${data.disabled ? 'data-choice-disabled aria-disabled="true"' : 'data-choice-selectable'} data-id="${data.id}" data-value="${data.value}">
                                ${photo ? `<span class="opf-choice-avatar"><img src="${photo}" alt=""></span>` : ""}
                                <span class="opf-choice-info">
                                    <span class="opf-choice-name">${data.label}</span>
                                    ${subtext ? `<span class="opf-choice-id">${subtext}</span>` : ""}
                                </span>
                            </div>
                        `);
                    },
                };
            },
        });

        el.addEventListener("change", () => validateField("olympic_athlete"));
    }

    
    function initBasicSelects() {

        if (!window.Choices) return;

        document
            .querySelectorAll(".opf-choices-basic, .opf-choices-country")
            .forEach((el) => {

                new Choices(el, {

                    searchEnabled: el.classList.contains("opf-choices-country"),

                    searchPlaceholderValue: "Search country...",

                    shouldSort: false,

                    itemSelectText: "",

                    placeholder: true,

                });

                el.addEventListener("change", () => validateField(el.name));

            });

    }

   
    const REQUIRED_FIELDS = [
        "olympic_athlete",
        "competition_name",
        "competition_level",
        "event_name",
        "competition_date",
        "host_city",
        "host_country",
        "medal",
        "participation_status",
    ];

    const OPTIONAL_FIELDS = ["score_time", "ranking", "remarks"];

    function getFieldEl(name) {
        return $(`[data-field="${name}"]`);
    }

    function getControl(name) {
        return $(`[name="${name}"]`);
    }

    function setError(name, message) {
        const fieldEl = getFieldEl(name);
        const errorEl = $(`#err-${name}`);
        if (!fieldEl) return;
        if (message) {
            fieldEl.classList.add("opf-field--invalid");
            fieldEl.classList.remove("opf-field--valid");
            if (errorEl) errorEl.textContent = message;
        } else {
            fieldEl.classList.remove("opf-field--invalid");
            fieldEl.classList.add("opf-field--valid");
            if (errorEl) errorEl.textContent = "";
        }
    }

    function clearFieldState(name) {
        const fieldEl = getFieldEl(name);
        const errorEl = $(`#err-${name}`);
        if (!fieldEl) return;
        fieldEl.classList.remove("opf-field--invalid", "opf-field--valid");
        if (errorEl) errorEl.textContent = "";
    }

    function validateField(name) {
        const control = getControl(name);
        if (!control) return true;
        let value = control.value;

        if (typeof value === "string" && control.tagName !== "SELECT") {
            value = value.trim();
            control.value = value;
        }

        switch (name) {
            case "olympic_athlete":
                if (!value) return fail(name, "Please select an Olympic athlete.");
                break;

            case "competition_name":
                if (!value) return fail(name, "Competition name is required.");
                if (value.length > 150) return fail(name, "Must be 150 characters or fewer.");
                break;

            case "competition_level":
                if (!value) return fail(name, "Please select a competition level.");
                break;

            case "event_name":
                if (!value) return fail(name, "Event name is required.");
                if (value.length > 150) return fail(name, "Must be 150 characters or fewer.");
                break;

            case "competition_date": {
                if (!value) return fail(name, "Competition date is required.");
                const d = new Date(value);
                if (isNaN(d.getTime())) return fail(name, "Enter a valid date.");
                break;
            }

            case "host_city":
                if (!value) return fail(name, "Host city is required.");
                if (value.length > 100) return fail(name, "Must be 100 characters or fewer.");
                break;

            case "host_country":
                if (!value) return fail(name, "Host country is required.");
                if (value.length > 100) return fail(name, "Must be 100 characters or fewer.");
                break;

            case "score_time":
                if (!value) { clearFieldState(name); return true; }
                if (value.length > 100) return fail(name, "Must be 100 characters or fewer.");
                break;

            case "ranking": {
                if (!value) { clearFieldState(name); return true; }
                const n = Number(value);
                if (!Number.isInteger(n)) return fail(name, "Ranking must be a whole number.");
                if (n <= 0) return fail(name, "Ranking must be a positive number.");
                break;
            }

            case "medal":
                if (!value) return fail(name, "Please select a medal.");
                break;

            case "participation_status":
                if (!value) return fail(name, "Please select a participation status.");
                break;

            case "remarks":
                if (value.length > 5000) return fail(name, "Remarks are too long.");
                if (!value) { clearFieldState(name); return true; }
                break;

            default:
                break;
        }

        setError(name, null);
        return true;

        function fail(fieldName, message) {
            setError(fieldName, message);
            return false;
        }
    }

    function validateAll() {
        let allValid = true;
        REQUIRED_FIELDS.concat(OPTIONAL_FIELDS).forEach((name) => {
            const ok = validateField(name);
            if (!ok) allValid = false;
        });
        return allValid;
    }

    function wireLiveValidation() {
        REQUIRED_FIELDS.concat(OPTIONAL_FIELDS).forEach((name) => {
            if (name === "olympic_athlete") return; // handled by the Choices.js change listener
            const control = getControl(name);
            if (!control) return;
            control.addEventListener("blur", () => validateField(name));
            control.addEventListener("input", () => {
                const fieldEl = getFieldEl(name);
                if (fieldEl && fieldEl.classList.contains("opf-field--invalid")) {
                    validateField(name);
                }
            });
        });
    }

 

    function setLoading(isLoading) {
        const btn = $("#opfSaveBtn");
        const cancelBtn = $("#opfCancelBtn");
        if (!btn) return;
        if (isLoading) {
            btn.classList.add("is-loading");
            btn.setAttribute("disabled", "disabled");
            if (cancelBtn) cancelBtn.setAttribute("aria-disabled", "true");
        } else {
            btn.classList.remove("is-loading");
            btn.removeAttribute("disabled");
            if (cancelBtn) cancelBtn.removeAttribute("aria-disabled");
        }
    }

    function focusFirstError() {
        const firstInvalid = $(".opf-field--invalid");
        if (!firstInvalid) return;
        firstInvalid.scrollIntoView({ behavior: "smooth", block: "center" });
        const control = firstInvalid.querySelector("input, select, textarea, .choices__inner");
        if (control) control.focus();
    }

    function applyServerErrors(errors) {
        Object.keys(errors).forEach((name) => {
            const message = Array.isArray(errors[name]) ? errors[name][0] : errors[name];
            setError(name, message);
        });
        focusFirstError();
    }

    function wireSubmit() {
        const form = $("#opfForm");
        if (!form) return;

        form.addEventListener("submit", async function (e) {
            e.preventDefault();
            if (isSubmitting) return;

            const valid = validateAll();
            if (!valid) {
                focusFirstError();
                showOlyToast("error", "Error", "Please fix the highlighted fields and try again.");
                return;
            }

            isSubmitting = true;
            setLoading(true);

            try {
                const formData = new FormData(form);
                const isEditMode = form.dataset.mode === "edit";
                const submitUrl = isEditMode
                    ? UPDATE_URL_TEMPLATE.replace("{uuid}", form.dataset.performanceUuid)
                    : CREATE_URL;

                const res = await fetch(submitUrl, {
                    method: "POST",
                    body: formData,
                    headers: { "X-Requested-With": "XMLHttpRequest" },
                });

                let data = {};
                try { 
                    data = await res.json();
                } catch (parseErr) {
                    data = {};
                }

                if (res.ok && data.ok) {
                    showOlyToast("success", "Success", data.message || "Olympic Performance added successfully.");
                    setTimeout(() => {
                        window.location.href = data.redirect_url || LIST_URL;
                    }, 1200);
                } else if (data.errors) {
                    applyServerErrors(data.errors);
                    showOlyToast("error", "Error", "Please fix the highlighted fields and try again.");
                    isSubmitting = false;
                    setLoading(false);
                } else {
                    showOlyToast("error", "Error", "Something went wrong. Please try again.");
                    isSubmitting = false;
                    setLoading(false);
                }
            } catch (err) {
                console.error("Failed to save performance", err);
                showOlyToast("error", "Error", "Network error — please try again.");
                isSubmitting = false;
                setLoading(false);
            }
        });
    }



    document.addEventListener("DOMContentLoaded", function () {
        if (!$("#opfPage")) return;
        initAthleteSelect();
        initBasicSelects();
        wireLiveValidation();
        wireSubmit();
        wireToastClose();
        refreshIcons();
        initCompetitionDatePicker();

//         const dateInput = document.getElementById("opfCompetitionDate");

// if (dateInput) {

//     dateInput.addEventListener("click", function () {

//         if (this.showPicker) {
//             this.showPicker();
//         }

//     });

//     dateInput.addEventListener("focus", function () {

//         if (this.showPicker) {
//             this.showPicker();
//         }

//     });

// }

    function initCompetitionDatePicker() {
        const dateInput = document.getElementById("opfCompetitionDate");

        if (!dateInput || typeof flatpickr === "undefined") return;

        flatpickr(dateInput, {
            dateFormat: "Y-m-d",
            allowInput: false,
            clickOpens: true,
            disableMobile: true,
            defaultDate: dateInput.value || null
        });
    }


    });
})();