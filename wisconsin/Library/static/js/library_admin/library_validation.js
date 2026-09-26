
document.addEventListener("DOMContentLoaded", function () {

    const form =
    document.querySelector(".library-add-form") ||
    document.querySelector(".book-form");

    if (!form) return;

    const fields = form.querySelectorAll(
        "input, textarea, select"
    );

    fields.forEach(function (field) {

        field.addEventListener("blur", function () {

        //   console.log("Blur:", field.name);

           validateField(field);

        });

        field.addEventListener("input", function () {

            validateField(field);

        });

        field.addEventListener("change", function () {

            validateField(field);

        });

    });

    form.addEventListener("submit", function (e) {

        let valid = true;

        fields.forEach(function (field) {

            if (!validateField(field)) {

                valid = false;

            }

        });

        if (!valid) {

            e.preventDefault();

        }

    });

});

function showError(field, message) {

    console.log("Field ID:", field.id);

    const errorBox = document.getElementById(field.id + "_error");

    console.log("Error Box:", errorBox);

    if (!errorBox) {
        console.log("Error div not found!");
        return;
    }

    errorBox.innerHTML = message;

    field.classList.add("is-invalid");
}
function clearError(field) {

    const errorBox = document.getElementById(
        field.id + "_error"
    );

    if (!errorBox) return;

    errorBox.innerHTML = "";

    field.classList.remove("is-invalid");

}
function validateField(field) {

    clearError(field);

    const value = field.value.trim();
         
    if (field.name == "library_name") {

        if (value == "") {

            showError(
                field,
                "Library name is required."
            );

            return false;

        }

        if (value.length < 3) {

            showError(
                field,
                "Library name must contain at least 3 characters."
            );

            return false;

        }

        return true;

    }
        if (field.name == "library_code") {

        if (value == "") {

            showError(
                field,
                "Library code is required."
            );

            return false;

        }

        if (!/^[A-Za-z0-9_-]{3,50}$/.test(value)) {

            showError(
                field,
                "Library code may contain only letters, numbers, hyphens and underscores."
            );

            return false;

        }

        return true;

    }
        if (field.name == "building") {

        if (value == "") {

            showError(
                field,
                "Please select the building where this library is located."
            );

            return false;

        }

        return true;

    }
        if (field.name == "status") {

        if (value == "") {

            showError(
                field,
                "Please select a status."
            );

            return false;

        }

        return true;

    }
        if (field.name == "email") {

        if (value == "") {

            showError(
                field,
                "Email is required."
            );

            return false;

        }

        if (!value.endsWith("@wisc.edu")) {

            showError(
                field,
                "Email address must end with @wisc.edu."
            );

            return false;

        }

        return true;

    }

    if (field.name == "phone") {

    if (value == "") {

        showError(field, "Phone number is required.");

        return false;

    }

    const phonePattern = /^(?:\+1\s?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}$/;

    if (!phonePattern.test(value)) {

        showError(
            field,
            "Enter a valid U.S. phone number (Example: (608) 555-1234 or +1 608-555-1234)."
        );

        return false;

    }

    return true;

}
if (field.name == "website") {

    if (value == "") {

        return true;

    }

    if (!value.startsWith("https://")) {

        showError(
            field,
            "Website must begin with https://"
        );

        return false;

    }

    if (value.length > 200) {

        showError(
            field,
            "Website URL cannot exceed 200 characters."
        );

        return false;

    }

    return true;

}
if (field.name == "opening_hours") {

    if (value == "") {

        showError(
            field,
            "Opening hours are required."
        );

        return false;

    }

    const pattern = /^(0?[1-9]|1[0-2]):[0-5][0-9]\s?(AM|PM)\s?-\s?(0?[1-9]|1[0-2]):[0-5][0-9]\s?(AM|PM)$/i;

    if (!pattern.test(value)) {

        showError(
            field,
            "Opening hours must be in 12-hour format (Example: 9:00 AM - 6:00 PM)."
        );

        return false;

    }

    return true;

}
if (field.name == "address") {

    if (value == "") {

        showError(
            field,
            "Address is required."
        );

        return false;

    }

    if (value.length < 10) {

        showError(
            field,
            "Address must contain at least 10 characters."
        );

        return false;

    }

    if (value.length > 500) {

        showError(
            field,
            "Address cannot exceed 500 characters."
        );

        return false;

    }

    return true;

}
if (field.name == "description") {

    if (value == "") {

        return true;

    }

    if (value.length < 20) {

        showError(
            field,
            "Description must contain at least 20 characters."
        );

        return false;

    }

    if (value.length > 2000) {

        showError(
            field,
            "Description cannot exceed 2000 characters."
        );

        return false;

    }

    return true;

}
if (field.name == "image") {

    if (field.files.length === 0) {

        showError(
            field,
            "Library image is required."
        );

        return false;

    }

    const image = field.files[0];

    const allowed = [
        "image/jpeg",
        "image/png",
        "image/webp"
    ];

    if (!allowed.includes(image.type)) {

        showError(
            field,
            "Only JPG, JPEG, PNG and WEBP images are allowed."
        );

        return false;

    }

    if (image.size > 5 * 1024 * 1024) {

        showError(
            field,
            "Image size cannot exceed 5 MB."
        );

        return false;

    }

    return true;

}
if (field.name == "title") {

    if (value == "") {

        showError(field, "Book title is required.");

        return false;
    }

    if (value.length < 2) {

        showError(field,
            "Book title must contain at least 2 characters."
        );

        return false;
    }

    if (/^\d+$/.test(value)) {

        showError(field,
            "Book title cannot contain only numbers."
        );

        return false;
    }

    return true;
}
if (field.name == "author") {

    if (value == "") {

        showError(field, "Author name is required.");

        return false;
    }

    if (!/^[A-Za-z .'-]+$/.test(value)) {

        showError(field,
            "Author name contains invalid characters."
        );

        return false;
    }

    return true;
}
if (field.name == "isbn_issn") {

    if (value == "") {

        showError(
            field,
            "ISBN is required."
        );

        return false;
    }


    /*
     * Allow numbers only
     */
    if (!/^\d+$/.test(value)) {

        showError(
            field,
            "ISBN must contain numbers only."
        );

        return false;
    }


    /*
     * ISBN must contain exactly 13 digits
     */
    if (value.length !== 13) {

        showError(
            field,
            "ISBN must contain exactly 13 digits."
        );

        return false;
    }


    return true;
}
if (field.name == "category") {

    if (value == "") {

        showError(field,
            "Please select a category."
        );

        return false;
    }

    return true;
}
if (field.name == "resource_type") {

    if (value == "") {

        showError(field,
            "Please select a resource type."
        );

        return false;
    }

    return true;
}

if (field.name == "subject") {

    if (value == "") {

        showError(field,
            "Subject is required."
        );

        return false;
    }

    return true;
}
if (field.name == "publisher") {

    if (value == "") {

        showError(field,
            "Publisher is required."
        );

        return false;
    }

    if (value.length < 2) {

        showError(field,
            "Publisher name is too short."
        );

        return false;
    }

    return true;
}
if (field.name == "publication_year") {

    if (value == "") {

        showError(field,
            "Publication year is required."
        );

        return false;
    }

    let year = parseInt(value);

    let current = new Date().getFullYear();

    if (year < 1800) {

        showError(field,
            "Enter a valid publication year."
        );

        return false;
    }

    if (year > current) {

        showError(field,
            "Publication year cannot be in the future."
        );

        return false;
    }

    return true;
}
if (field.name == "edition") {

    if (value == "") {

        return true;
    }

    if (value.length > 50) {

        showError(field,
            "Edition cannot exceed 50 characters."
        );

        return false;
    }

    return true;
}
if (field.name == "language") {

    if (value == "") {

        showError(field,
            "Language is required."
        );

        return false;
    }

    if (!/^[A-Za-z ]+$/.test(value)) {

        showError(field,
            "Language can contain only letters."
        );

        return false;
    }

    return true;
}
if (field.name == "library") {

    if (value == "") {

        showError(field,
            "Please select a library."
        );

        return false;
    }

    return true;
}
if (field.name == "shelf_location") {

    if (value == "") {

        showError(field,
            "Shelf location is required."
        );

        return false;
    }

    return true;
}
if (field.name == "total_copies") {

    if (value == "") {

        showError(field,
            "Total copies is required."
        );

        return false;
    }

    if (parseInt(value) <= 0) {

        showError(field,
            "Total copies must be greater than zero."
        );

        return false;
    }

    return true;
}
if (field.name == "available_copies") {

    if (value == "") {

        showError(field,
            "Available copies is required."
        );

        return false;
    }

    if (parseInt(value) < 0) {

        showError(field,
            "Available copies cannot be negative."
        );

        return false;
    }

    const total = document.getElementById("id_total_copies");

    if (total && parseInt(value) > parseInt(total.value || 0)) {

        showError(field,
            "Available copies cannot exceed total copies."
        );

        return false;
    }

    return true;
}
if (field.name == "status") {

    if (value == "") {

        showError(field,
            "Please select a status."
        );

        return false;
    }

    return true;
}

return true;

}