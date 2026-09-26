document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("editCoachForm");
    if (!form) return;

    const hireDate = document.getElementById("hire_date");

    if (hireDate) {
        flatpickr(hireDate, {
            dateFormat: "Y-m-d",
            altInput: true,
            altFormat: "d M Y",
            allowInput: false,
            maxDate: "today",
            disableMobile: true
        });
    }

    const fields = ["role", "hire_date"];

    function showError(input, message) {
        input.classList.add("is-invalid");
        const feedback = input.parentElement.querySelector(".invalid-feedback");
        if (feedback) feedback.textContent = message;
    }

    function clearError(input) {
        input.classList.remove("is-invalid");
        const feedback = input.parentElement.querySelector(".invalid-feedback");
        if (feedback) feedback.textContent = "";
    }

    fields.forEach((name) => {
        const input = form.querySelector(`[name="${name}"]`);
        if (!input) return;
        input.addEventListener("input", () => clearError(input));
        input.addEventListener("change", () => clearError(input));
    });

    form.addEventListener("submit", function (e) {
        let hasError = false;

        fields.forEach((name) => {
            const input = form.querySelector(`[name="${name}"]`);
            if (!input) return;
            if (!input.value || !input.value.trim()) {
                showError(input, "This field is required.");
                hasError = true;
            } else {
                clearError(input);
            }
        });

        if (hasError) {
            e.preventDefault();
        }
    });
});

