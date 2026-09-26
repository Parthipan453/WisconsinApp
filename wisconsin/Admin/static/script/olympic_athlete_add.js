/*  kali's code */

(function () {
    "use strict";

    const CREATE_URL = window.OLY_ADD_ATHLETE_URL;
    const UPDATE_URL = window.OLY_UPDATE_ATHLETE_URL;
    const LIST_URL = window.OLY_ATHLETE_LIST_URL;
    const IS_EDIT = !!window.OLY_IS_EDIT;
    const SUBMIT_URL = IS_EDIT ? UPDATE_URL : CREATE_URL;

    let isSubmitting = false;

    function getCookie(name) {
        let value = null;
        if (document.cookie && document.cookie !== "") {
            document.cookie.split(";").forEach((c) => {
                c = c.trim();
                if (c.startsWith(name + "=")) {
                    value = decodeURIComponent(c.substring(name.length + 1));
                }
            });
        }
        return value;
    }

 
    function getErrorTarget(input) {
        if (!input) return null;
        return input.closest(".choices") || input;
    }

    function showFieldError(fieldName, message) {
        const errEl = document.getElementById(`err-${fieldName}`);
        const input = document.querySelector(`[name="${fieldName}"]`);
        if (errEl) {
            errEl.textContent = message;
            errEl.classList.add("show");
        }
        const target = getErrorTarget(input);
        if (target) target.classList.add("is-invalid");
    }

    function clearFieldError(fieldName) {
        const errEl = document.getElementById(`err-${fieldName}`);
        const input = document.querySelector(`[name="${fieldName}"]`);
        if (errEl) {
            errEl.textContent = "";
            errEl.classList.remove("show");
        }
        const target = getErrorTarget(input);
        if (target) target.classList.remove("is-invalid");
    }

    function clearAllErrors(form) {
        form.querySelectorAll(".oly-field__error").forEach((el) => {
            el.textContent = "";
            el.classList.remove("show");
        });
        form.querySelectorAll(".is-invalid").forEach((el) => el.classList.remove("is-invalid"));
    }

    
    function bindChoicesDropdowns() {
        if (!window.Choices) return;
        const selectors = [
            "#olyAthleteSelect",
            "#olyNationality",
            "#olySport",
            "#olyTeam",
            "#olyCoach",
            "#olyOlympicStatus",
            "#olyQualStatus",
        ];
        selectors.forEach((sel) => {
            const el = document.querySelector(sel);
            if (!el) return;
            new window.Choices(el, {
                searchEnabled: true,
                searchChoices: true,
                shouldSort: false,
                itemSelectText: "",
                placeholderValue: el.dataset.placeholder || undefined,
                searchPlaceholderValue: "Search...",
                fuseOptions: { threshold: 0.2 },
                position: "auto",
            });
        });
    }

   
    function bindAthletePreview() {
        const select = document.getElementById("olyAthleteSelect");
        const photoEl = document.getElementById("olyAddPreviewPhoto");
        const nameEl = document.getElementById("olyAddPreviewName");
        if (!select) return;

        select.addEventListener("change", () => {
            const opt = select.options[select.selectedIndex];
            clearFieldError("athlete");

            if (!opt || !opt.value) {
                photoEl.src = "https://ui-avatars.com/api/?name=Select+Athlete&background=e7e9f0&color=6b7280&size=128";
                nameEl.textContent = "No athlete selected";
                return;
            }

            const photo = opt.getAttribute("data-photo");
            const name = opt.getAttribute("data-name") || opt.textContent;
            photoEl.src = photo || `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=0081C8&color=fff&size=128`;
            nameEl.textContent = name;
        });
    }

    
    

    function bindQualificationDatePicker() {
        const dateInput = document.getElementById("olyQualDate");

        if (!dateInput || typeof flatpickr === "undefined") return;

        flatpickr(dateInput, {
            dateFormat: "Y-m-d",
            maxDate: "today",
            allowInput: false,
            clickOpens: true,
            disableMobile: true,
            defaultDate: dateInput.value || null
        });
    }


    function validateForm(form) {
        clearAllErrors(form);
        let valid = true;

        const requiredSelects = ["athlete", "nationality", "sport", "olympic_status", "qualification_status"];
        requiredSelects.forEach((name) => {
            const el = form.querySelector(`[name="${name}"]`);
            if (el && !el.value) {
                showFieldError(name, "This field is required.");
                valid = false;
            }
        });

        const requiredTexts = [
            ["target_olympics", "Target Olympics is required."],
            ["event_name", "Event name is required."],
            ["governing_body", "Governing body is required."],
        ];
        requiredTexts.forEach(([name, msg]) => {
            const el = form.querySelector(`[name="${name}"]`);
            if (el && !el.value.trim()) {
                showFieldError(name, msg);
                valid = false;
            }
        });

        const eventCategory = form.querySelector('input[name="event_category"]:checked');
        if (!eventCategory) {
            showFieldError("event_category", "Select an event category.");
            valid = false;
        }

        const worldRanking = form.querySelector('[name="world_ranking"]');
        if (worldRanking && worldRanking.value.trim()) {
            const num = Number(worldRanking.value);
            if (!Number.isInteger(num) || num <= 0) {
                showFieldError("world_ranking", "World ranking must be a positive whole number.");
                valid = false;
            }
        }

        const qualDate = form.querySelector('[name="qualification_date"]');
        if (qualDate && qualDate.value) {
            const picked = new Date(qualDate.value);
            const today = new Date();
            today.setHours(23, 59, 59, 999);
            if (isNaN(picked.getTime())) {
                showFieldError("qualification_date", "Enter a valid date.");
                valid = false;
            } else if (picked > today) {
                showFieldError("qualification_date", "Qualification date cannot be in the future.");
                valid = false;
            }
        }

        return valid;
    }

    
    function showOlyToast(type, title, message) {
        const toast = document.getElementById("roleToast");
        const iconWrap = document.getElementById("toastIconWrap");
        const icon = document.getElementById("toastIcon");
        const titleEl = document.getElementById("toastTitle");
        const msgEl = document.getElementById("toastMsg");
        if (!toast) return;

        toast.classList.remove("role-toast--success", "role-toast--error");
        toast.classList.add(type === "success" ? "role-toast--success" : "role-toast--error");

        if (icon) icon.setAttribute("data-lucide", type === "success" ? "check-circle-2" : "x-circle");
        if (titleEl) titleEl.textContent = title;
        if (msgEl) msgEl.textContent = message;

        toast.hidden = false;
        if (window.lucide) window.lucide.createIcons();

        clearTimeout(toast._olyTimer);
        toast._olyTimer = setTimeout(() => { toast.hidden = true; }, 4000);
    }

    
    function setSubmitting(state) {
        isSubmitting = state;
        const btn = document.getElementById("olySaveAthleteBtn");
        const label = document.getElementById("olySaveBtnLabel");
        if (!btn) return;
        btn.disabled = state;
        if (label) {
            label.textContent = state
                ? (IS_EDIT ? "Updating..." : "Saving...")
                : (IS_EDIT ? "Update Athlete" : "Save Athlete");
        }
    }

    function bindFormSubmit() {
        const form = document.getElementById("olyAddAthleteForm");
        if (!form) return;

        form.addEventListener("submit", (e) => {
            e.preventDefault();
            if (isSubmitting) return;

            if (!SUBMIT_URL) {
                console.error("[Olympics] No submit URL configured for this form.");
                return;
            }

            if (!validateForm(form)) {
                const firstError = form.querySelector(".is-invalid, .oly-field__error.show");
                if (firstError) firstError.scrollIntoView({ behavior: "smooth", block: "center" });
                return;
            }

            setSubmitting(true);

            const formData = new FormData(form);

            fetch(SUBMIT_URL, {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                body: formData,
            })
                .then((res) => res.json().then((data) => ({ status: res.status, data })))
                .then(({ status, data }) => {
                    if (status === 200 && data.ok) {
                        showOlyToast(
                            "success",
                            "Success",
                            data.message || (IS_EDIT ? "Olympic Athlete updated successfully." : "Olympic Athlete added successfully.")
                        );
                        setTimeout(() => {
                            window.location.href = data.redirect_url || LIST_URL;
                        }, 1200);
                    } else {
                        setSubmitting(false);
                        const errors = data.errors || {};
                        Object.keys(errors).forEach((field) => showFieldError(field, errors[field]));
                        showOlyToast("error", "Error", "Please fix the highlighted fields and try again.");
                    }
                })
                .catch(() => {
                    setSubmitting(false);
                    showOlyToast("error", "Error", "Something went wrong. Please try again.");
                });
        });

        document.getElementById("olyCancelBtn")?.addEventListener("click", () => {
            window.location.href = LIST_URL;
        }); 
    }

    function init() {
        bindChoicesDropdowns();
        bindAthletePreview();
        bindQualificationDatePicker();
        bindFormSubmit();
        if (window.lucide) window.lucide.createIcons();
    }

    document.addEventListener("DOMContentLoaded", init);
})();