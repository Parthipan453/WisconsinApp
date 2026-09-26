// Steve code

document.addEventListener("DOMContentLoaded", () => {

    const nameInput          = document.getElementById("id_university_name");
    const shortNameInput     = document.getElementById("id_university_short_name");
    const codeInput          = document.getElementById("id_university_code");
    const typeSelect         = document.getElementById("id_university_type");
    const ownershipSelect    = document.getElementById("id_ownership_type");

    const emailInput         = document.getElementById("id_official_email");
    const phoneInput         = document.getElementById("id_phone_number");
    const websiteInput       = document.getElementById("id_website");

    const address1Input      = document.getElementById("id_address_line_1");
    const address2Input      = document.getElementById("id_address_line_2");
    const cityInput          = document.getElementById("id_city");
    const stateInput         = document.getElementById("id_state");
    const countryInput       = document.getElementById("id_country");
    const postalInput        = document.getElementById("id_postal_code");

    const yearInput           = document.getElementById("id_established_year");
    const accreditationInput  = document.getElementById("id_accreditation");
    const logoInput           = document.getElementById("id_logo");

    const prevAvatar = document.getElementById("prevAvatar");
    const prevName   = document.getElementById("prevName");
    const prevCode   = document.getElementById("prevCode");
    const prevType   = document.getElementById("prevType");
    const prevYear   = document.getElementById("prevYear");

    const logoPreviewImg  = document.getElementById("logoPreviewImg");
    const logoDropContent = document.getElementById("logoDropContent");

    const form      = document.getElementById("universityForm");
    const submitBtn = document.getElementById("submitBtn");


    /* ---------------------------------------------------
       Accordion sections
    --------------------------------------------------- */
    const accordionCards = document.querySelectorAll("[data-accordion-card]");

    accordionCards.forEach(card => {
        const header = card.querySelector(".df-card-header");
        header?.addEventListener("click", () => {
            card.classList.toggle("collapsed");
        });
    });

    // If the page was re-rendered after a failed server-side submit,
    // auto-expand any section that already contains a Django error.
    accordionCards.forEach(card => {
        if (card.querySelector(".df-field.has-error")) {
            card.classList.remove("collapsed");
        }
    });

    function expandCardFor(element) {
        const card = element?.closest("[data-accordion-card]");
        card?.classList.remove("collapsed");
    }


    function updatePreview() {
        const name = nameInput?.value.trim() || "";
        const code = codeInput?.value.trim() || "";
        const year = yearInput?.value.trim() || "";
        const type = typeSelect?.value || "";

        prevAvatar.textContent = name ? name[0].toUpperCase() : "?";

        prevName.textContent = name || "University Name";

        prevCode.textContent = code ? code.toUpperCase() : "CODE";

        prevType.textContent = type || "—";

        prevYear.textContent = year || "—";
        prevYear.className   = "prev-year" + (year ? " set" : "");
    }


    // Keep the code field uppercase as the user types
    codeInput?.addEventListener("input", () => {
        const pos = codeInput.selectionStart;
        codeInput.value = codeInput.value.toUpperCase();
        codeInput.setSelectionRange(pos, pos);
    });

    // Established year: digits only, capped at 4 characters
    yearInput?.addEventListener("input", function () {
        this.value = this.value.replace(/\D/g, "").slice(0, 4);
    });

    // Phone: allow leading + and digits only
    phoneInput?.addEventListener("input", function () {
        this.value = this.value.replace(/[^\d+]/g, "");
    });

    // Logo: live image preview
    logoInput?.addEventListener("change", function () {
        const file = this.files?.[0];
        clearError(this);

        if (!file) {
            logoPreviewImg.style.display = "none";
            logoDropContent.style.display = "flex";
            return;
        }

        if (!file.type.startsWith("image/")) {
            showError(this, "Please choose a valid image file.");
            this.value = "";
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            logoPreviewImg.src = e.target.result;
            logoPreviewImg.style.display = "block";
            logoDropContent.style.display = "none";
        };
        reader.readAsDataURL(file);
    });


    const currentYear = new Date().getFullYear();

    const fields = [
        {
            element: nameInput,
            validate: value => value.trim().length >= 3,
            message: "Enter at least 3 characters for the university name."
        },
        {
            element: shortNameInput,
            validate: value => value.trim().length >= 2,
            message: "Enter at least 2 characters for the short name."
        },
        {
            element: codeInput,
            validate: value => value.trim() !== "",
            message: "University code is required."
        },
        {
            element: emailInput,
            validate: value => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim()),
            message: "Enter a valid email address."
        },
        {
            element: phoneInput,
            validate: value => /^\+?[0-9]{7,15}$/.test(value.trim()),
            message: "Enter a valid phone number (7-15 digits)."
        },
        {
            element: websiteInput,
            validate: value => {
                value = value.trim();
                if (value === "") return true;
                return /^https?:\/\/.+/i.test(value);
            },
            message: "Enter a valid website URL."
        },
        {
            element: address1Input,
            validate: value => value.trim().length >= 10,
            message: "Please enter a complete address (min. 10 characters)."
        },
        {
            element: cityInput,
            validate: value => value.trim().length >= 2,
            message: "Enter at least 2 characters for the city."
        },
        {
            element: stateInput,
            validate: value => value.trim().length >= 2,
            message: "Enter at least 2 characters for the state."
        },
        {
            element: countryInput,
            validate: value => value.trim().length >= 2,
            message: "Enter at least 2 characters for the country."
        },
        {
            element: postalInput,
            validate: value => value.trim().length >= 4,
            message: "Enter a valid postal code."
        },
        {
            element: accreditationInput,
            validate: value => {
                value = value.trim();
                if (value === "") return true;
                return value.length >= 2;
            },
            message: "Accreditation must contain at least 2 characters."
        },
        {
            element: yearInput,
            validate: value => {
                if (value.length !== 4) return false;
                const year = parseInt(value, 10);
                return year >= 1800 && year <= currentYear;
            },
            message: `Enter a valid 4-digit year between 1800 and ${currentYear}.`
        }
    ];

    fields.forEach(field => {
        field.element?.addEventListener("input", function () {
            updatePreview();
            clearError(this);

            if (!field.validate(this.value)) {
                showError(this, field.message);
            }
        });
    });

    typeSelect?.addEventListener("change", updatePreview);
    ownershipSelect?.addEventListener("change", updatePreview);

    updatePreview();


    form?.addEventListener("submit", (e) => {
        let valid = true;
        let firstInvalidField = null;

        fields.forEach(field => {
            clearError(field.element);

            if (!field.validate(field.element.value)) {
                // Make sure the section holding this field is open before
                // showing the error, otherwise it stays invisible.
                expandCardFor(field.element);
                showError(field.element, field.message);
                valid = false;
                if (!firstInvalidField) firstInvalidField = field.element;
            }
        });

        if (!valid) {
            e.preventDefault();

            firstInvalidField?.closest(".df-field")
                ?.scrollIntoView({ behavior: "smooth", block: "center" });
        } else {

            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
                    <path d="M21 12a9 9 0 11-6.219-8.56"/>
                </svg>
                Saving…`;
        }
    });


    function showError(input, message) {
        if (!input) return;
        const field = input.closest(".df-field");
        field?.classList.add("has-error");
        let errEl = field?.querySelector(".df-error");
        if (!errEl) {
            errEl = document.createElement("div");
            errEl.className = "df-error";
            (input.closest(".df-input-wrap") || input.closest(".df-file-wrap"))?.after(errEl);
        }
        errEl.innerHTML = `<svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> ${message}`;
    }

    function clearError(input) {
        if (!input) return;
        const field = input.closest(".df-field");
        field?.classList.remove("has-error");
        field?.querySelector(".df-error")?.remove();
    }

});