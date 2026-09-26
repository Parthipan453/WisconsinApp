document.addEventListener('DOMContentLoaded', function () {

    if (window.lucide && typeof window.lucide.createIcons === 'function') {
        window.lucide.createIcons();
    }

    if (window.AOS && typeof window.AOS.init === 'function') {
        window.AOS.init({ once: true, offset: 40 });
    }

    var editModalEl = document.getElementById('editClubModal');
    var editForm = document.getElementById('editClubForm');

    if (editModalEl) {
        editModalEl.addEventListener('shown.bs.modal', function () {
            if (window.lucide) window.lucide.createIcons();
        });

        editModalEl.addEventListener('show.bs.modal', function () {
            if (!editForm) return;
            editForm.querySelectorAll('.is-invalid').forEach(function (field) {
                field.classList.remove('is-invalid');
            });
            editForm.querySelectorAll('.invalid-feedback').forEach(function (msg) {
                msg.textContent = '';
            });
        });
    }


    // EDIT FORM VALIDATION
 
    if (!editForm) return;

    const clubName = editForm.querySelector("[name='club_name']");
    const description = editForm.querySelector("[name='description']");
    const logo = editForm.querySelector("[name='logo']");
    const image = editForm.querySelector("[name='image']");

    const allowedTypes = [
        "image/jpeg",
        "image/png",
        "image/webp"
    ];

    // Club Name
    clubName.addEventListener("input", function () {

        const value = this.value.trim();

        if (value === "") {
            showError(this, "Club name is required.");
        }
        else if (!/^[A-Za-z ]+$/.test(value)) {
            showError(this, "Only letters and spaces are allowed.");
        }
        else if (value.length < 3) {
            showError(this, "Minimum 3 characters required.");
        }
        else if (value.length > 20) {
            showError(this, "Maximum 20 characters allowed.");
        }
        else {
            clearFieldError(this);
        }

    });

    // Description
    description.addEventListener("input", function () {

        if (this.value.length > 100) {
            showError(this, "Maximum 100 characters allowed.");
        }
        else {
            clearFieldError(this);
        }

    });

    // Logo
    logo.addEventListener("change", function () {

        if (this.files.length === 0) {
            clearFieldError(this);
            return;
        }

        if (!allowedTypes.includes(this.files[0].type)) {
            showError(this, "Only JPG, JPEG, PNG and WEBP images are allowed.");
        }
        else {
            clearFieldError(this);
        }

    });

    // Cover Image
    image.addEventListener("change", function () {

        if (this.files.length === 0) {
            clearFieldError(this);
            return;
        }

        if (!allowedTypes.includes(this.files[0].type)) {
            showError(this, "Only JPG, JPEG, PNG and WEBP images are allowed.");
        }
        else {
            clearFieldError(this);
        }

    });

    editForm.addEventListener("submit", function (e) {
        e.preventDefault();
        let valid = true;
        clearErrors();
        const name = clubName.value.trim();
        if (name === "") {
            showError(clubName, "Club name is required.");
            valid = false;
        }
        else if (!/^[A-Za-z ]+$/.test(name)) {
            showError(clubName, "Only letters and spaces are allowed.");
            valid = false;
        }
        else if (name.length < 3) {
            showError(clubName, "Minimum 3 characters required.");
            valid = false;
        }
        else if (name.length > 20) {
            showError(clubName, "Maximum 20 characters allowed.");
            valid = false;
        }

        if (description.value.length > 100) {
            showError(description, "Maximum 100 characters allowed.");
            valid = false;
        }

        if (
            logo.files.length > 0 &&
            !allowedTypes.includes(logo.files[0].type)
        ) {
            showError(logo, "Only JPG, JPEG, PNG and WEBP images are allowed.");
            valid = false;
        }

        if (
            image.files.length > 0 &&
            !allowedTypes.includes(image.files[0].type)
        ) {
            showError(image, "Only JPG, JPEG, PNG and WEBP images are allowed.");
            valid = false;
        }

        if (!valid) return;
        const formData = new FormData(editForm);

        fetch(editForm.action, {
            method: "POST",
            headers: {
                "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                "X-Requested-With": "XMLHttpRequest"
            },
            body: formData
        })
            .then(response => response.json())
            .then(data => {

                if (data.success) {

                    bootstrap.Modal.getInstance(
                        document.getElementById("editClubModal")
                    ).hide();

                    location.reload();

                } else {

                    showError(clubName, data.message);

                }

            });

    });

});



function showError(input, message) {
    input.classList.add("is-invalid");

    const error = input.nextElementSibling;
    if (error && error.classList.contains("invalid-feedback")) {
        error.textContent = message;
    }
}

function clearFieldError(input) {
    input.classList.remove("is-invalid");

    const error = input.nextElementSibling;
    if (error && error.classList.contains("invalid-feedback")) {
        error.textContent = "";
    }
}

function clearErrors() {
    document.querySelectorAll("#editClubForm .is-invalid").forEach(input => {
        input.classList.remove("is-invalid");
    });

    document.querySelectorAll("#editClubForm .invalid-feedback").forEach(error => {
        error.textContent = "";
    });
}

// dropdown cdn
document.addEventListener("DOMContentLoaded", function () {

    sportChoice = new Choices(".editclubsport", {
        searchEnabled: false,
        itemSelectText: "",
        shouldSort: false
    });

    statusChoice = new Choices(".editclubstatus", {
        searchEnabled: false,
        itemSelectText: "",
        shouldSort: false
    });
});


// Live Search
function enableCardSearch(inputId, containerId, emptyId) {

    const input = document.getElementById(inputId);
    const container = document.getElementById(containerId);
    const empty = document.getElementById(emptyId);

    if (!input || !container || !empty) return;

    input.addEventListener("input", function () {

        const value = this.value.trim().toLowerCase();
        let found = false;

        container.querySelectorAll(".cv-item-card").forEach(card => {

            const match = card.textContent.toLowerCase().includes(value);

            card.style.display = match ? "" : "none";

            if (match) found = true;
        });

        empty.style.display = found ? "none" : "block";

    });

}

enableCardSearch("teamSearch", "teamtable", "teamNoResults");
enableCardSearch("coachSearch", "coachtable", "coachNoResults");

// function enableCardSearch(inputId, containerId) {

//     const input = document.getElementById(inputId);
//     const container = document.getElementById(containerId);

//     if (!input || !container) return;

//     input.addEventListener("input", function () {

//         const value = this.value.toLowerCase().trim();

//         container.querySelectorAll(".cv-item-card").forEach(card => {

//             card.style.display = card.textContent.toLowerCase().includes(value)
//                 ? ""
//                 : "none";

//         });

//     });

// }

// enableCardSearch("teamSearch", "teamtable");
// enableCardSearch("coachSearch", "coachtable");