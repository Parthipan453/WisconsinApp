// Steve code

document.addEventListener("DOMContentLoaded", () => {

    const nameInput = document.getElementById("id_program_name");
    const codeInput = document.getElementById("id_program_code");
    const typeRadios = document.querySelectorAll('input[name="program_type"]');
    const deptSelect = document.getElementById("id_department");
    const degreeSelect = document.getElementById("id_degree");
    const durationInput = document.getElementById("id_duration");
    const creditsInput = document.getElementById("id_total_credits");
    const descInput = document.getElementById("id_description");

    const prevAvatar = document.getElementById("prevAvatar");
    const prevName = document.getElementById("prevName");
    const prevCode = document.getElementById("prevCode");
    const prevType = document.getElementById("prevType");

    const typeColors = {
        FULL_TIME: "#1d4ed8",
        PART_TIME: "#9d174d",
        ONLINE: "#065f46",
        "": "#dc3545",
    };

    const typeLabels = {
        FULL_TIME: "Full Time",
        PART_TIME: "Part Time",
        ONLINE: "Online",
        "": "—",
    };

    function getType() {
        for (const r of typeRadios) {
            if (r.checked) return r.value;
        }
        return "";
    }

    function updatePreview() {
        const name = nameInput?.value.trim() || "";
        const code = codeInput?.value.trim() || "";
        const type = getType();

  
        prevAvatar.textContent = name ? name[0].toUpperCase() : "?";
        prevAvatar.style.background = typeColors[type] || "#dc3545";

        prevName.textContent = name || "Program Name";

        prevCode.textContent = code ? code.toUpperCase() : "CODE";

        prevType.textContent = typeLabels[type] || "—";
        prevType.className = "prev-type" + (type ? " " + type.toLowerCase() : "");
    }


    codeInput?.addEventListener("input", () => {
        const pos = codeInput.selectionStart;
        codeInput.value = codeInput.value.toUpperCase();
        codeInput.setSelectionRange(pos, pos);
        updatePreview();
    });


    function showError(input, message) {
        if (!input) return;
        const field = input.closest(".pf-field");
        field?.classList.add("has-error");
        let errEl = field?.querySelector(".pf-error");
        if (!errEl) {
            errEl = document.createElement("div");
            errEl.className = "pf-error";
            input.closest(".pf-input-wrap")?.after(errEl);
        }
        errEl.innerHTML = `<svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> ${message}`;
    }

    function clearError(input) {
        if (!input) return;
        const field = input.closest(".pf-field");
        field?.classList.remove("has-error");
        field?.querySelector(".pf-error")?.remove();
    }


    nameInput?.addEventListener("input", function() {
        updatePreview();
        clearError(this);
        const value = this.value.trim();
        

        if (/\d/.test(value)) {
            showError(this, "Program name cannot contain numbers.");
            return;
        }
        
        if (value.length < 3) {
            showError(this, "Program name must contain at least 3 characters.");
            return;
        }
        
  
        if (!/^[A-Za-z\s&()'.-]+$/.test(value)) {
            showError(this, "Program name can only contain letters, spaces, and basic punctuation.");
        }
    });


    codeInput?.addEventListener("input", function() {
        clearError(this);
        this.value = this.value.toUpperCase();
        const value = this.value.trim();
        

        if (/\d/.test(value)) {
            showError(this, "Program code cannot contain numbers.");
            return;
        }
        
        if (value.length < 2) {
            showError(this, "Program code must contain at least 2 characters.");
            return;
        }
        

        if (!/^[A-Z.-]+$/.test(value)) {
            showError(this, "Only uppercase letters, hyphen (-) and period (.) are allowed. Numbers are not allowed.");
        }
    });


    deptSelect?.addEventListener("change", function() {
        clearError(this);
        if (!this.value) {
            showError(this, "Please select a department.");
        }
    });


    degreeSelect?.addEventListener("change", function() {
        clearError(this);
        if (!this.value) {
            showError(this, "Please select a degree.");
        }
    });


    durationInput?.addEventListener("input", function () {

        // Allow only numbers
        this.value = this.value.replace(/\D/g, "");

        // Maximum 2 digits
        if (this.value.length > 2) {
            this.value = this.value.slice(0, 2);
        }

        clearError(this);

        const val = parseInt(this.value);

        if (isNaN(val) || val < 1) {
            showError(this, "Duration must be at least 1 year.");
        } else if (val > 10) {
            showError(this, "Duration cannot exceed 10 years.");
        }

    });


    creditsInput?.addEventListener("input", function () {

        // Allow only numbers
        this.value = this.value.replace(/\D/g, "");

        // Maximum 3 digits
        if (this.value.length > 3) {
            this.value = this.value.slice(0, 3);
        }

        clearError(this);

        const val = parseInt(this.value);

        if (isNaN(val) || val < 1) {
            showError(this, "Credits must be greater than zero.");
        } else if (val > 300) {
            showError(this, "Credits cannot exceed 300.");
        }

    });


    descInput?.addEventListener("input", function() {
        clearError(this);
        const val = this.value.trim();
        if (val.length < 20) {
            showError(this, "Description must contain at least 20 characters.");
        }
    });


    typeRadios.forEach(r => r.addEventListener("change", updatePreview));


    updatePreview();

    
    const form = document.getElementById("programForm");
    const submitBtn = document.getElementById("submitBtn");

    form?.addEventListener("submit", (e) => {
        let valid = true;


        clearError(nameInput);
        const nameVal = nameInput?.value.trim() || "";
        
        if (/\d/.test(nameVal)) {
            showError(nameInput, "Program name cannot contain numbers.");
            valid = false;
        } else if (nameVal.length < 3) {
            showError(nameInput, "Program name must contain at least 3 characters.");
            valid = false;
        } else if (!/^[A-Za-z\s&()'.-]+$/.test(nameVal)) {
            showError(nameInput, "Program name can only contain letters, spaces, and basic punctuation.");
            valid = false;
        }

  
        clearError(codeInput);
        const codeVal = codeInput?.value.trim() || "";
        
        if (/\d/.test(codeVal)) {
            showError(codeInput, "Program code cannot contain numbers.");
            valid = false;
        } else if (codeVal.length < 2) {
            showError(codeInput, "Program code must contain at least 2 characters.");
            valid = false;
        } else if (!/^[A-Z.-]+$/.test(codeVal)) {
            showError(codeInput, "Only uppercase letters, hyphen (-) and period (.) are allowed. Numbers are not allowed.");
            valid = false;
        }


        clearError(deptSelect);
        if (!deptSelect?.value) {
            showError(deptSelect, "Please select a department.");
            valid = false;
        }


        clearError(degreeSelect);
        if (!degreeSelect?.value) {
            showError(degreeSelect, "Please select a degree.");
            valid = false;
        }


        const typeErr = document.getElementById("type-error");
        if (typeErr) typeErr.remove();
        if (!getType()) {
            const picker = document.getElementById("typePicker");
            const err = document.createElement("div");
            err.id = "type-error";
            err.className = "pf-error";
            err.style.marginTop = "8px";
            err.innerHTML = `<svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> Please select a program type.`;
            picker?.after(err);
            valid = false;
        }


        clearError(durationInput);
        const durVal = parseInt(durationInput?.value);
        if (isNaN(durVal) || durVal < 1) {
            showError(durationInput, "Duration must be at least 1 year.");
            valid = false;
        } else if (durVal > 10) {
            showError(durationInput, "Duration cannot exceed 10 years.");
            valid = false;
        }


        clearError(creditsInput);
        const credVal = parseInt(creditsInput?.value);
        if (isNaN(credVal) || credVal < 1) {
            showError(creditsInput, "Credits must be greater than zero.");
            valid = false;
        } else if (credVal > 300) {
            showError(creditsInput, "Credits cannot exceed 300.");
            valid = false;
        }


        clearError(descInput);
        const descVal = descInput?.value.trim() || "";
        if (descVal.length < 20) {
            showError(descInput, "Description must contain at least 20 characters.");
            valid = false;
        }

        if (!valid) {
            e.preventDefault();
            document.querySelector(".pf-field.has-error, #type-error")
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

    const description = document.querySelector(".pf-textarea");
    const counter = document.getElementById("descriptionCounter");

    if (description && counter) {

        function updateDescriptionCounter() {

            console.log(description.value.split(""));   
            console.log(JSON.stringify(description.value));

            const length = description.value.length;
            counter.textContent = `${length} / 500`;

            counter.classList.remove("warning", "danger");

            if (length >= 400) {
                counter.classList.add("warning");
            }

            if (length >= 480) {
                counter.classList.remove("warning");
                counter.classList.add("danger");
            }
        }

        updateDescriptionCounter();

        description.addEventListener("input", updateDescriptionCounter);
    }

    nameInput?.addEventListener("input", () => { 
        if (nameInput.value.trim().length >= 3 && !/\d/.test(nameInput.value)) 
            clearError(nameInput); 
    });
    codeInput?.addEventListener("input", () => { 
        if (codeInput.value.trim().length >= 1 && !/\d/.test(codeInput.value)) 
            clearError(codeInput); 
    });
    durationInput?.addEventListener("input", () => { if (parseInt(durationInput.value) >= 1) clearError(durationInput); });
    creditsInput?.addEventListener("input", () => { if (parseInt(creditsInput.value) >= 1) clearError(creditsInput); });
});


document.addEventListener("DOMContentLoaded", function () {

    document.querySelectorAll("select.pf-select").forEach(function (select) {

        new Choices(select, {
            searchEnabled: true,
            shouldSort: false,
            itemSelectText: "",
            allowHTML: false,
        });

    });

});