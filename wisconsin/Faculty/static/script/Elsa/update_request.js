document.addEventListener("DOMContentLoaded", function () {
    const requestedScore = document.getElementById("requested_score");
    const requestedError = document.getElementById("requested_score_error");
    const gradeDisplay = document.getElementById("requested_grade_display");
    const gradeHidden = document.getElementById("requested_grade_hidden");
    const submitBtn = document.getElementById("gcrSubmitBtn");
    const scale = window.GCR_GRADE_SCALE || [];

    function findGrade(score) {
        return scale.find(g => score >= g.min && score <= g.max);
    }

    function validateAndUpdate() {
        const raw = requestedScore.value.trim();
        const val = parseFloat(raw);
        const validFormat = /^(\d{1,2}(\.\d{1,2})?|100)$/.test(raw);
        if (raw === "" || !validFormat || isNaN(val) || val < 0 || val > 100) {
            requestedScore.classList.add("gcr-input-invalid");
            requestedError.textContent = "Enter a score between 0 and 100 (max 2 decimal places).";
            gradeDisplay.value = "—";
            gradeHidden.value = "";
            submitBtn.disabled = true;
            return;
        }
        requestedScore.classList.remove("gcr-input-invalid");
        requestedError.textContent = "";
        const match = findGrade(val);
        if (match) {
            gradeDisplay.value = match.letter;
            gradeHidden.value = match.id;
            submitBtn.disabled = false;
        } else {
            gradeDisplay.value = "No matching grade band";
            gradeHidden.value = "";
            submitBtn.disabled = true;
        }
    }
    if (requestedScore) {
        requestedScore.addEventListener("keypress", function (e) {
            const char = String.fromCharCode(e.which);
            const current = this.value;
            if (!/[\d.]/.test(char)) {
                e.preventDefault();
                return;
            }
            if (char === "." && current.includes(".")) {
                e.preventDefault();
                return;
            }
            const projected = current.slice(0, this.selectionStart) + char + current.slice(this.selectionEnd);
            const partiallyValid =
                /^\d{0,2}(\.\d{0,2})?$/.test(projected) ||
                /^100$/.test(projected) ||
                /^1(0(0)?)?$/.test(projected);
           
            if (!partiallyValid) {
                e.preventDefault();
            }
        });

        requestedScore.addEventListener("input", validateAndUpdate);
        validateAndUpdate();
    }
});


window.addEventListener("grade_request_decided", function (e) {
    const d = e.detail;

    const row = document.querySelector(`tr[data-request-id="${d.request_id}"]`);
    if (row) {
        const badge = row.querySelector(".gcr-badge");
        if (badge) {
            badge.className = "gcr-badge " + (d.status === "Approved" ? "gcr-req-approved" : "gcr-req-rejected");
            badge.textContent = d.status;
        }
        const cells = row.querySelectorAll("td");
        if (cells[6]) cells[6].textContent = d.approved_by || "—";
        if (cells[7]) cells[7].textContent = d.approved_date || "—";

        row.style.transition = "background-color 1.5s ease";
        row.style.backgroundColor = d.status === "Approved" ? "#d4edda" : "#f8d7da";
        setTimeout(() => { row.style.backgroundColor = ""; }, 1600);
    }

    const toastEl = document.getElementById("liveToast");
    const toastMsg = document.getElementById("toastMessage");
    if (toastEl && toastMsg && window.bootstrap) {
        toastEl.classList.remove("bg-success", "bg-danger");
        toastEl.classList.add(d.status === "Approved" ? "bg-success" : "bg-danger");
        toastMsg.textContent = d.message;
        new bootstrap.Toast(toastEl).show();
    }
});