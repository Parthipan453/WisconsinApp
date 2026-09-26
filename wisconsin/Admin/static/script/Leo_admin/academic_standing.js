const modalTitle = document.getElementById("modalTitle");
const modalIcon = document.getElementById("modalIcon");
const academicStandingForm = document.getElementById("academicStandingForm");
const standingId = document.getElementById("standingId");
const standingName = document.getElementById("standingName");
const minimumGpa = document.getElementById("minimumGpa");
const description = document.getElementById("description");
const saveText = document.getElementById("saveText");
const saveIcon = document.getElementById("saveIcon");
const updateAction = academicStandingForm.dataset.updateUrl;
const inputs = [standingName, minimumGpa, description];
const createAction = academicStandingForm.action;
const serverErrors = document.getElementById("serverFormErrors");
const searchInput = document.getElementById("searchInput");
const tableBody = document.getElementById("standingTableBody");
const searchUrl = searchInput.dataset.url;
let searchTimer;
let selectedDeactivateForm = null;
const deactivateModal = new bootstrap.Modal(document.getElementById("deactivateModal"));
const deactivateStandingName = document.getElementById("deactivateStandingName");
const confirmDeactivateBtn = document.getElementById("confirmDeactivateBtn");

function clearValidation() {
    inputs.forEach(input => {
        input.classList.remove("is-valid", "is-invalid");
        const feedback = input.nextElementSibling;
        if (feedback && feedback.classList.contains("invalid-feedback")) {
            feedback.textContent = "";
        }
    });
}

function showError(input, message) {
    input.classList.remove("is-valid");
    input.classList.add("is-invalid");
    let feedback = input.nextElementSibling;
    if (!feedback || !feedback.classList.contains("invalid-feedback")) {
        feedback = document.createElement("div");
        feedback.className = "invalid-feedback";
        input.insertAdjacentElement("afterend", feedback);
    }
    feedback.textContent = message;
}

function showSuccess(input) {
    input.classList.remove("is-invalid");
    input.classList.add("is-valid");
    const feedback = input.nextElementSibling;
    if (feedback && feedback.classList.contains("invalid-feedback")) {
        feedback.textContent = "";
    }
}

function validateStandingName() {
    const value = standingName.value.trim();
    if (value === "") {
        showError(standingName, "Standing Name is required.");
        return false;
    }
    if (value.length < 3) {
        showError(standingName, "Minimum 3 characters required.");
        return false;
    }
    if (value.length > 100) {
        showError(standingName, "Maximum 100 characters allowed.");
        return false;
    }
    if (!/^[A-Za-z0-9\s'&-]+$/.test(value)) {
        showError(standingName, "Invalid Standing Name.");
        return false;
    }
    if (!/[A-Za-z]/.test(value)) {
        showError(
            standingName,
            "Standing Name must contain at least one alphabet."
        );
        return false;
    }
    showSuccess(standingName);
    return true;
}

function validateMinimumGpa() {
    const value = minimumGpa.value.trim();
    if (value === "") {
        showError(minimumGpa, "Minimum GPA is required.");
        return false;
    }
    const gpa = Number(value);
    if (isNaN(gpa) || gpa < 0 || gpa > 4) {
        showError(minimumGpa, "GPA must be between 0.00 and 4.00.");
        return false;
    }
    showSuccess(minimumGpa);
    return true;
}

function validateDescription() {
    const value = description.value.trim();
    description.classList.remove("is-valid", "is-invalid");
    const feedback = description.nextElementSibling;
    if (feedback) {
        feedback.textContent = "";
    }
    if (value === "") {
        showError(description, "Description is required.");
        return false;
    }
    if (value.length > 500) {
        showError(description, "Maximum 500 characters allowed.");
        return false;
    }
    showSuccess(description);
    return true;
}

function validateForm() {
    const nameValid = validateStandingName();
    const gpaValid = validateMinimumGpa();
    const descriptionValid = validateDescription();
    return nameValid && gpaValid && descriptionValid;
}

function resetForm() {
    academicStandingForm.reset();
    standingId.value = "";
    clearValidation();
}

function setAddMode() {
    modalTitle.textContent = "Add Academic Standing";
    modalIcon.className = "ti ti-plus me-2";
    saveText.textContent = "Save Standing";
    saveIcon.className = "ti ti-device-floppy";
    academicStandingForm.action = createAction;
    resetForm();
}

function setEditMode(button) {
    modalTitle.textContent = "Edit Academic Standing";
    modalIcon.className = "ti ti-edit me-2";
    saveText.textContent = "Update Standing";
    saveIcon.className = "ti ti-check";
    standingId.value = button.dataset.id || "";
    standingName.value = button.dataset.name || "";
    minimumGpa.value = button.dataset.gpa || "";
    description.value = button.dataset.description || "";
    academicStandingForm.action = updateAction.replace("0/", `${button.dataset.id}/`);
    clearValidation();
}

document.querySelectorAll(".add-standing-btn").forEach(button => {
    button.addEventListener("click", setAddMode);
});

document.querySelectorAll(".edit-standing-btn").forEach(button => {
    button.addEventListener("click", function () {
        setEditMode(this);
    });
});

document.querySelectorAll(".deactivate-btn").forEach(button => {
    button.addEventListener("click", function () {
        selectedDeactivateForm = this.closest(".deactivate-form");
        deactivateStandingName.textContent = this.dataset.standingName;
        deactivateModal.show();
    });
});

standingName.addEventListener("input", validateStandingName);
minimumGpa.addEventListener("input", validateMinimumGpa);
description.addEventListener("input", validateDescription);

academicStandingForm.addEventListener("submit", function (event) {
    if (!validateForm()) {
        event.preventDefault();
    }
});

if (serverErrors) {
    const errors = JSON.parse(serverErrors.textContent);
    const modal = new bootstrap.Modal(document.getElementById("academicStandingModal"));
    modal.show();
    if (errors.standing_name) {
        showError(standingName, errors.standing_name[0].message);
    }
    if (errors.minimum_gpa) {
        showError(minimumGpa, errors.minimum_gpa[0].message);
    }
    if (errors.description) {
        showError(description, errors.description[0].message);
    }
}

function searchStandings(search) {

    const params = new URLSearchParams(window.location.search);

    const page = params.get("page") || 1;
    const sort = params.get("sort") || "gpa";
    const order = params.get("order") || "desc";

    fetch(
        `${searchUrl}?search=${encodeURIComponent(search)}&page=${page}&sort=${sort}&order=${order}`,
        {
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        }
    )
        .then(response => response.json())
        .then(data => {
            tableBody.replaceChildren();

            if (data.results.length === 0) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center py-4">
                            No Academic Standing Found
                        </td>
                    </tr>
                `;
                return;
            }

            let rows = "";

            data.results.forEach((standing, index) => {
                rows += `
                <tr>
                    <td>${data.start_index + index}</td>
                  <td>
    <strong
        class="standing-name"
        title="${standing.name}"
    >
        ${standing.name}
    </strong>
</td>
                    <td>
                        <span class="badge bg-primary">
                            ${standing.gpa}
                        </span>
                    </td>
                    <td>${standing.description}</td>
                    <td class="text-center">
                        <div class="action-buttons">
                            <button
    class="btn btn-sm btn-outline-primary edit-standing-btn"
    data-bs-toggle="modal"
    data-bs-target="#academicStandingModal"
    data-id="${standing.id}"
    data-name="${standing.name}"
    data-gpa="${standing.gpa}"
    data-description="${standing.description}"
    ${!standing.is_active ? 'disabled title="Inactive records cannot be edited"' : ""}
>   <i class="ti ti-edit"></i>
</button>

                            ${standing.is_active
                        ? `
                                    <form
                                        method="POST"
                                        action="${standing.deactivate_url}"
                                        class="deactivate-form"
                                        style="display:inline;"
                                    ><input
    type="hidden"
    name="csrfmiddlewaretoken"
    value="${document.querySelector('[name=csrfmiddlewaretoken]').value}"
>
                                        <button
                                            type="button"
                                            class="btn btn-sm btn-outline-danger deactivate-btn"
                                            data-standing-name="${standing.name}"
                                            title="Deactivate"
                                        >
                                            <i class="ti ti-ban"></i>
                                        </button>
                                    </form>
                                    `
                        : `
                                    <form
                                        method="POST"
                                        action="${standing.activate_url}"
                                        class="activate-form"
                                        style="display:inline;"
                                    ><input
    type="hidden"
    name="csrfmiddlewaretoken"
    value="${document.querySelector('[name=csrfmiddlewaretoken]').value}"
>
                                        <button
                                            type="button"
                                            class="btn btn-sm btn-outline-success activate-btn"
                                            data-standing-name="${standing.name}"
                                            title="Activate"
                                        >
                                            <i class="ti ti-plus"></i>
                                        </button>
                                    </form>
                                    `
                    }
                        </div>
                    </td>
                </tr>
                `;
            });

            tableBody.innerHTML = rows;

            document.querySelectorAll(".edit-standing-btn").forEach(button => {
                button.addEventListener("click", function () {
                    setEditMode(this);
                });
            });

            document.querySelectorAll(".deactivate-btn").forEach(button => {
                button.addEventListener("click", function () {
                    selectedDeactivateForm = this.closest(".deactivate-form");
                    deactivateStandingName.textContent = this.dataset.standingName;
                    deactivateModal.show();
                });
            });

            document.querySelectorAll(".activate-btn").forEach(button => {
                button.addEventListener("click", function () {
                    const form = this.closest(".activate-form");

                    fetch(form.action, {
                        method: "POST",
                        headers: {
                            "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                            "X-Requested-With": "XMLHttpRequest",
                        },
                    })
                        .then(response => response.json())
                        .then(data => {

                            if (data.success) {

                                showToast("success", data.message);

                                searchStandings(searchInput.value);

                            }

                        });;
                });
            });

            AOS.refresh();
        });
}

searchInput.addEventListener("input", function () {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
        searchStandings(this.value);
    }, 300);
});

confirmDeactivateBtn.addEventListener("click", function () {
    if (!selectedDeactivateForm) return;
    fetch(selectedDeactivateForm.action, {
        method: "POST",
        headers: {
            "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
            "X-Requested-With": "XMLHttpRequest",
        },
    })
        .then(response => response.json())
        .then(data => {

            if (data.success) {

                deactivateModal.hide();

                showToast("success", data.message);

                searchStandings(searchInput.value);

            }

        })
        .catch(error => console.error(error));
});

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".alert").forEach((alert) => {
        setTimeout(() => {
            alert.classList.add("alert-hide");
            alert.addEventListener("transitionend", () => {
                alert.remove();
            }, { once: true });
        }, 3000);
    });
});

function showToast(icon, title) {

    Swal.fire({
        toast: true,
        position: "top-end",
        icon: icon,
        title: title,
        showConfirmButton: false,
        timer: 2500,
        timerProgressBar: true
    });

}

AOS.init({
    duration: 700,
    easing: "ease-out-cubic",
    once: true,
    offset: 60,
});

document.getElementById("printBtn").addEventListener("click", function () {
    window.open("/dashboard/academic-standing/print/", "_blank");
});

document.getElementById("exportBtn").addEventListener("click", function () {
    window.location.href = "/dashboard/academic-standing/export/";
});

document.querySelectorAll(".activate-btn").forEach((button) => {

    button.addEventListener("click", function () {

        const form = this.closest("form");

        fetch(form.action, {
            method: "POST",
            headers: {
                "X-CSRFToken": form.querySelector(
                    "[name=csrfmiddlewaretoken]"
                ).value,
                "X-Requested-With": "XMLHttpRequest",
            },
        })
        .then(response => response.json())
        .then(data => {

            if (data.success) {
                location.reload();
            }

        });

    });

});


const modal = document.getElementById("academicStandingModal");

modal.addEventListener("shown.bs.modal", function () {
    const scrollY = window.scrollY;

    document.body.dataset.scrollY = scrollY;
    document.body.style.position = "fixed";
    document.body.style.top = `-${scrollY}px`;
    document.body.style.left = "0";
    document.body.style.right = "0";
    document.body.style.width = "100%";
    document.body.style.overflow = "hidden";
});

modal.addEventListener("hidden.bs.modal", function () {
    const scrollY = parseInt(document.body.dataset.scrollY || "0");

    document.body.style.position = "";
    document.body.style.top = "";
    document.body.style.left = "";
    document.body.style.right = "";
    document.body.style.width = "";
    document.body.style.overflow = "";

    window.scrollTo(0, scrollY);
});