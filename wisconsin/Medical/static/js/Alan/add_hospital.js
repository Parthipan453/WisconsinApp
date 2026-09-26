const hospitalForm = document.getElementById("createHospitalForm");

if (hospitalForm) {
    hospitalForm.addEventListener("submit", submitHospital);
}

function getCSRFToken() {
  return document.querySelector(
    "[name=csrfmiddlewaretoken]"
  ).value;

}

function clearBackendErrors() {

    document
        .querySelectorAll(".is-invalid")
        .forEach((element) => {
            element.classList.remove("is-invalid");
        });

    document
        .querySelectorAll(".invalid-feedback")
        .forEach((element) => {

            if (element.id) {
                element.textContent = "";
            }

        });

}


function showBackendErrors(errors) {

    Object.keys(errors).forEach((field) => {

        const input = document.querySelector(`[name="${field}"]`);

        if (!input) return;

        input.classList.add("is-invalid");
        input.classList.remove("is-valid");

        const feedback = input.parentElement.querySelector(".invalid-feedback");

        if (feedback) {
            feedback.textContent = errors[field][0];
        }

    });

}

async function submitHospital(event) {

    event.preventDefault();

    console.log("========== HOSPITAL SUBMIT ==========");

    const director = document.getElementById("directorName");

    console.log("1. Director element:", director);
    console.log("2. Director value:", director ? director.value : "NOT FOUND");

    clearBackendErrors();

    console.log("3. Calling validateHospitalForm()");

    let isValid;

    try {
        isValid = validateHospitalForm();
    } catch (error) {
        console.error("❌ ERROR INSIDE validateHospitalForm():", error);
        return;
    }

    console.log("4. Validation result:", isValid);

    if (!isValid) {

        console.log("❌ Hospital validation FAILED");

        const firstInvalid = hospitalForm.querySelector(".is-invalid");

        console.log("First invalid element:", firstInvalid);

        if (firstInvalid) {
            firstInvalid.scrollIntoView({
                behavior: "smooth",
                block: "center"
            });
        }

        return;
    }

    console.log("✅ Hospital validation PASSED");

    const formData = new FormData(hospitalForm);

    formData.set(
        "selected_facilities",
        JSON.stringify(getSelectedFacilities())
    );

    formData.set(
        "selected_other_facilities",
        JSON.stringify(getSelectedOtherFacilities())
    );

    formData.set(
        "selected_departments",
        JSON.stringify(
            Array.from(selectedDepartments.keys())
        )
    );

    console.log("5. Sending hospital data");

    try {

        const response = await fetch("/medical/add_hospital/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
            },
            body: formData,
        });

        console.log("6. Response status:", response.status);

        const data = await response.json();

        console.log("7. Response data:", data);

        if (response.ok && data.success) {

            console.log("✅ Hospital saved successfully");

            window.location.href = hospitalDashboardUrl;
            return;
        }

        if (data.errors) {
            console.log(
        "❌ Backend validation errors:",
        JSON.stringify(data.errors, null, 2)
    );
            showBackendErrors(data.errors);
        }

    } catch (error) {

        console.error("❌ FETCH ERROR:", error);

    }
}