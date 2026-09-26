// Steve code

document.addEventListener("DOMContentLoaded", () => {


    const nameInput  = document.getElementById("id_degree_name");
    const codeInput  = document.getElementById("id_degree_code");
    const levelRadios = document.querySelectorAll('input[name="level"]');

    const prevAvatar = document.getElementById("prevAvatar");
    const prevName   = document.getElementById("prevName");
    const prevCode   = document.getElementById("prevCode");
    const prevLevel  = document.getElementById("prevLevel");


    const levelColors = {
        UG:  "#0d6efd",
        PG:  "#28a745",
        PHD: "#7c3aed",
        "": "#dc3545",
    };


    function getLevel() {
        for (const r of levelRadios) {
            if (r.checked) return r.value;
        }
        return "";
    }

    function updatePreview() {
        const name  = nameInput?.value.trim()  || "";
        const code  = codeInput?.value.trim()  || "";
        const level = getLevel();


        prevAvatar.textContent = name ? name[0].toUpperCase() : "?";
        prevAvatar.style.background = levelColors[level] || "#dc3545";


        prevName.textContent = name || "Degree Name";


        prevCode.textContent = code ? code.toUpperCase() : "CODE";


        prevLevel.textContent = level || "—";
        prevLevel.className   = "prev-level" + (level ? " " + level.toLowerCase() : "");
    }


    codeInput?.addEventListener("input", () => {
        const pos = codeInput.selectionStart;
        codeInput.value = codeInput.value.toUpperCase();
        codeInput.setSelectionRange(pos, pos);
        updatePreview();
    });

    nameInput?.addEventListener("input", function(){

        updatePreview();

        clearError(this);

        const value = this.value.trim();

        if(value.length < 3){

            showError(
                this,
                "Degree name must contain at least 3 characters."
            );

            return;
        }

        const regex = /^[A-Za-z\s&()'-]+$/;

        if(!regex.test(value)){

            showError(
                this,
                "Degree name can contain only letters and spaces."
            );

        }

    });
    levelRadios.forEach(r => r.addEventListener("change", updatePreview));

    codeInput?.addEventListener("input", function(){

        clearError(this);

        this.value = this.value.toUpperCase();

        const value = this.value.trim();

        if(value.length < 2){

            showError(
                this,
                "Degree code is required."
            );

            return;
        }

        const regex = /^[A-Z.-]+$/;

        if(!regex.test(value)){

            showError(
                this,
                "Only uppercase letters, hyphen (-) and period (.) are allowed."
            );

        }

    });


    updatePreview();


    const form      = document.getElementById("degreeForm");
    const submitBtn = document.getElementById("submitBtn");

    form?.addEventListener("submit", (e) => {
        let valid = true;


        const nameVal = nameInput?.value.trim() || "";

        clearError(nameInput);

        if(nameVal.length < 3){

            showError(
                nameInput,
                "Degree name must contain at least 3 characters."
            );

            valid = false;

        }
        else if(!/^[A-Za-z\s&()'-]+$/.test(nameVal)){

            showError(
                nameInput,
                "Degree name can contain only letters and spaces."
            );

            valid = false;
        }


        const codeVal = codeInput?.value.trim() || "";

        clearError(codeInput);

        if(codeVal.length < 2){

            showError(
                codeInput,
                "Degree code is required."
            );

            valid = false;

        }
        else if(!/^[A-Z.-]+$/.test(codeVal)){

            showError(
                codeInput,
                "Only uppercase letters, hyphen (-) and period (.) are allowed."
            );

            valid = false;
        }


        const lvlErr = document.getElementById("level-error");
        if (lvlErr) lvlErr.remove();
        if (!getLevel()) {
            const picker = document.getElementById("levelPicker");
            const err    = document.createElement("div");
            err.id        = "level-error";
            err.className = "df-error";
            err.style.marginTop = "8px";
            err.innerHTML = `<svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> Please select a degree level.`;
            picker?.after(err);
            valid = false;
        }

        if (!valid) {
            e.preventDefault();

            document.querySelector(".df-field.has-error, #level-error")
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
            input.closest(".df-input-wrap")?.after(errEl);
        }
        errEl.innerHTML = `<svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> ${message}`;
    }

    function clearError(input) {
        if (!input) return;
        const field = input.closest(".df-field");
        field?.classList.remove("has-error");
        field?.querySelector(".df-error")?.remove();
    }

    nameInput?.addEventListener("input", () => { if (nameInput.value.trim().length >= 3) clearError(nameInput); });
    codeInput?.addEventListener("input", () => { if (codeInput.value.trim().length >= 1) clearError(codeInput); });

});