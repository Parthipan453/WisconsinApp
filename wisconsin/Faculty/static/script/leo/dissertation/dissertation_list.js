document.addEventListener("DOMContentLoaded", () => {
    const DOM = {
        phdStudent: document.querySelector("#id_phd_student"),
        programDisplay: document.querySelector("#id_phd_program_display"),
        proposalTitle: document.querySelector("#id_proposal_title"),
        abstract: document.querySelector("#id_abstract"),
        submissionDate: document.querySelector("#id_submission_date"),
        hearingDate: document.querySelector("#id_hearing_date"),
        result: document.querySelector("#id_result"),
        submit: document.querySelector("button[type='submit']"),
        reset: document.querySelector("button[type='reset']"),
        form: document.querySelector(".dissertation-form")
    };

    const CONFIG = {
        errorClass: "dissertation-form-error",
        invalidClass: "is-invalid",
        backendClass: "backend-error"
    };

    const VALIDATION_RULES = {
        student: {
            message: "Please select a PhD student.",
            validate: (field) => field?.value?.trim() || ""
        },
        title: {
            message: "Proposal title is required.",
            validate: (field) => {
                if (!field) return "";
                const val = field.value.trim();
                field.value = val;
                if (!val) return "";
                if (val.length < 10) return "Proposal title must contain at least 10 characters.";
                if (val.length > 255) return "Proposal title must not go over 255 characters.";
                return null;
            }
        },
        abstract: {
            validate: (field) => {
                if (!field) return "";
                const val = field.value.trim();
                field.value = val;
                if (!val) return "Abstract is required.";
                if (val.length < 100) return "Abstract must contain at least 100 characters.";
                if (val.length > 5000) return "Abstract cannot exceed 5000 characters.";
                return null;
            }
        },
        submissionDate: {
            validate: (field) => {
                if (!field) return "";
                if (!field.value.trim()) return "Submission date is required.";
                return null;
            }
        },
        hearingDate: {
            validate: (field) => {
                if (!field) return "";
                const val = field.value.trim();
                if (!val) return "";
                const subVal = DOM.submissionDate?.value?.trim() || "";
                if (!subVal) return "";
                const hearing = new Date(val);
                const submission = new Date(subVal);
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                if (hearing <= submission) return "Hearing date must be later than the submission date.";
                if (hearing < today) return "Hearing date must be tomorrow or a future date.";
                return null;
            }
        },
        result: {
            validate: (field) => {
                if (!field) return "";
                if (!field.value.trim()) return "Please select a result.";
                return null;
            }
        }
    };

    const fieldCache = {};

    function getFieldByKey(key) {
        return DOM[key] || null;
    }

    function getErrorContainer(field) {
        if (!field) return null;
        const parent = field.closest(".dissertation-form-group");
        if (!parent) return null;
        let container = fieldCache[field.id];
        if (!container) {
            container = parent.querySelector(`.${CONFIG.errorClass}`);
            if (!container) {
                container = document.createElement("div");
                container.className = CONFIG.errorClass;
                parent.appendChild(container);
            }
            fieldCache[field.id] = container;
        }
        return container;
    }

    function getBackendErrors(field) {
        const container = getErrorContainer(field);
        if (!container) return [];
        const errors = [];
        for (const child of container.children) {
            if (child.classList?.contains(CONFIG.backendClass)) {
                errors.push(child);
            }
        }
        return errors;
    }

    function setError(field, message) {
        if (!field || !message) return false;
        field.classList.add(CONFIG.invalidClass);
        const container = getErrorContainer(field);
        if (!container) return false;
        const children = container.children;
        let hasMessage = false;
        let hasCustomError = false;
        for (let i = 0; i < children.length; i++) {
            const child = children[i];
            if (child.textContent.trim() === message.trim()) {
                hasMessage = true;
            }
            if (!child.classList?.contains(CONFIG.backendClass)) {
                hasCustomError = true;
            }
        }
        if (!hasMessage) {
            if (hasCustomError) {
                const existingErrors = [];
                for (let i = 0; i < children.length; i++) {
                    if (!children[i].classList?.contains(CONFIG.backendClass)) {
                        existingErrors.push(children[i]);
                    }
                }
                existingErrors.forEach(el => el.remove());
            }
            const error = document.createElement("div");
            error.textContent = message;
            container.appendChild(error);
        }
        return false;
    }

    function clearError(field) {
        if (!field) return;
        field.classList.remove(CONFIG.invalidClass);
        const container = getErrorContainer(field);
        if (!container) return;
        const backendErrors = getBackendErrors(field);
        container.innerHTML = "";
        for (const err of backendErrors) {
            container.appendChild(err.cloneNode(true));
        }
    }

    function validateField(field, rule) {
        if (!field) return true;
        const result = rule.validate(field);
        if (result === null) {
            clearError(field);
            return true;
        }
        if (typeof result === "string" && result) {
            setError(field, result);
            return false;
        }
        if (result === "" && rule.message) {
            setError(field, rule.message);
            return false;
        }
        return true;
    }

    function updateProgramDisplay() {
        if (!DOM.phdStudent || !DOM.programDisplay) return;
        const selected = DOM.phdStudent.options[DOM.phdStudent.selectedIndex];
        DOM.programDisplay.value = selected?.dataset?.program || "";
    }

    function validateAll() {
        let isValid = true;
        for (const [key, rule] of Object.entries(VALIDATION_RULES)) {
            const field = getFieldByKey(key);
            if (field) {
                const result = rule.validate(field);
                if (result !== null && result !== "") {
                    setError(field, result);
                    isValid = false;
                } else {
                    clearError(field);
                }
            }
        }
        if (DOM.submit) {
            DOM.submit.disabled = false;
        }
        return isValid;
    }

    function clearAllErrors() {
        for (const key of Object.keys(VALIDATION_RULES)) {
            const field = getFieldByKey(key);
            if (field) {
                field.classList.remove(CONFIG.invalidClass);
                const container = getErrorContainer(field);
                if (container) {
                    const backendErrors = getBackendErrors(field);
                    container.innerHTML = "";
                    for (const err of backendErrors) {
                        container.appendChild(err.cloneNode(true));
                    }
                }
            }
        }
    }

    function handleReset() {
        clearAllErrors();
        if (DOM.programDisplay) {
            DOM.programDisplay.value = "";
        }
        if (DOM.submit) {
            DOM.submit.disabled = false;
        }
    }
// function preserveBackendErrors() {
//     document.querySelectorAll(".dissertation-form-error").forEach(container => {

//         // if (!container.querySelector(".errorlist")) {
//         //     return;
//         // }

//         // const backend = document.createElement("div");
//         // backend.className = "backend-error";
//         // backend.innerHTML = container.querySelector(".errorlist").innerHTML;

//         // container.innerHTML = "";
//         // container.appendChild(backend);
//     });
// }
    function validateFieldOnEvent(key, field) {
        const rule = VALIDATION_RULES[key];
        if (!rule) return;
        const result = rule.validate(field);
        if (result !== null && result !== "") {
            setError(field, result);
            if (DOM.submit) DOM.submit.disabled = false;
        } else {
            clearError(field);
        }
    }

    function bindEvents() {
        if (DOM.phdStudent) {
            DOM.phdStudent.addEventListener("change", () => {
                updateProgramDisplay();
                validateFieldOnEvent("student", DOM.phdStudent);
            });
            DOM.phdStudent.addEventListener("blur", () => {
                if (DOM.phdStudent.value.trim()) {
                    validateFieldOnEvent("student", DOM.phdStudent);
                }
            });
        }

        const textFields = ["proposalTitle", "abstract"];
        for (const key of textFields) {
            const field = DOM[key];
            if (!field) continue;
            field.addEventListener("input", () => {
                field.value = field.value.trim();
                validateFieldOnEvent(key, field);
            });
            field.addEventListener("blur", () => {
                validateFieldOnEvent(key, field);
            });
        }

        const dateFields = ["submissionDate", "hearingDate"];
        for (const key of dateFields) {
            const field = DOM[key];
            if (!field) continue;
            field.addEventListener("change", () => {
                validateFieldOnEvent(key, field);
                if (key === "submissionDate" && DOM.hearingDate && DOM.hearingDate.value) {
                    validateFieldOnEvent("hearingDate", DOM.hearingDate);
                }
            });
        }

        if (DOM.result) {
            DOM.result.addEventListener("change", () => {
                validateFieldOnEvent("result", DOM.result);
            });
        }

        if (DOM.reset) {
            DOM.reset.addEventListener("click", () => {
                setTimeout(handleReset, 10);
            });
        }

        if (DOM.submit && DOM.form) {
            DOM.form.addEventListener("submit", (e) => {
                const isValid = validateAll();
                if (!isValid) {
                    e.preventDefault();
                    DOM.submit.disabled = false;
                } else {
                    DOM.submit.disabled = true;
                }
            });
        }
    }

    function init() {
        if (!DOM.form) return;

        preserveBackendErrors();
        updateProgramDisplay();
        bindEvents();
    }

    init();
});