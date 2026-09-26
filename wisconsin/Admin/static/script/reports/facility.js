const DEFAULT_FACILITY_IMAGE = "/static/images/feild.jpg";

window.choicesMap = {};
window.choicesInstances = {};

let sportChoice = null;
let typeChoice = null;
let statusChoice = null;

function initializeChoices() {
    const selectIds = [
        "sportFilter",
        "typeFilter",
        "statusFilter",

        "facilitySport",
        "facilityType",
        "facilityStatus",

        "edit_sport",
        "edit_type",
        "edit_status",
    ];

    selectIds.forEach(function (id) {
        const select = document.getElementById(id);

        if (!select) {
            return;
        }


        if (window.choicesMap && window.choicesMap[id]) {
            return;
        }

        const alreadyInitialized = select.closest(".choices") || select.parentElement.classList.contains("choices");

        if (alreadyInitialized) {
            console.warn("Choices already exists for:", id);

            return;
        }

        try {
            const instance = new Choices(select, {
                searchEnabled: select.options.length > 5,

                shouldSort: false,

                itemSelectText: "",

                allowHTML: false,
            });

            window.choicesMap[id] = instance;
        } catch (error) {
            console.error("Choices initialization error:", id, error);
        }
    });

    sportChoice = window.choicesMap["sportFilter"] || null;

    typeChoice = window.choicesMap["typeFilter"] || null;

    statusChoice = window.choicesMap["statusFilter"] || null;
}

function getCSRFToken() {
    const token = document.querySelector("[name=csrfmiddlewaretoken]");

    return token ? token.value : "";
}

function getFilterValues() {
    const searchInput = document.getElementById("facilitySearch");

    const sportFilter = document.getElementById("sportFilter");

    const typeFilter = document.getElementById("typeFilter");

    const statusFilter = document.getElementById("statusFilter");

    return {
        search: searchInput ? searchInput.value.trim() : "",

        sport: sportFilter ? sportFilter.value : "",

        type: typeFilter ? typeFilter.value : "",

        status: statusFilter ? statusFilter.value : "",
    };
}

window.loadFacilities = function (page = 1, resetScroll = false) {
    const container = document.getElementById("facilityTableContainer");

    if (!container) {
        console.error("facilityTableContainer not found.");

        return;
    }

    const filters = getFilterValues();
    const url = new URL(window.location.href);

    url.searchParams.set("page", page);

    if (filters.search) {
        url.searchParams.set("search", filters.search);
    } else {
        url.searchParams.delete("search");
    }
    if (filters.sport) {
        url.searchParams.set("sport", filters.sport);
    } else {
        url.searchParams.delete("sport");
    }

    if (filters.type) {
        url.searchParams.set("type", filters.type);
    } else {
        url.searchParams.delete("type");
    }

    if (filters.status) {
        url.searchParams.set("status", filters.status);
    } else {
        url.searchParams.delete("status");
    }

    url.searchParams.set("ajax", "1");
    container.classList.add("fc-loading");
    fetch(url.toString(), {
        method: "GET",

        headers: {
            "X-Requested-With": "XMLHttpRequest",
        },
    })
        .then(function (response) {
            if (!response.ok) {
                throw new Error("Failed to load facilities.");
            }

            return response.text();
        })

        .then(function (html) {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, "text/html");
            const newContainer = doc.getElementById("facilityTableContainer");

            if (!newContainer) {
                throw new Error("Updated facility container not found.");
            }

            container.innerHTML = newContainer.innerHTML;
            url.searchParams.delete("ajax");
            window.history.replaceState({}, "", url.toString());

            if (resetScroll) {
                const dashboard = document.querySelector(".fc-dashboard");

                if (dashboard) {
                    dashboard.scrollIntoView({
                        behavior: "smooth",

                        block: "start",
                    });
                }
            }
        })

        .catch(function (error) {
            console.error(error);
        })

        .finally(function () {
            container.classList.remove("fc-loading");
        });
};

let searchTimer = null;

function initializeSearchFilter() {
    const searchInput = document.getElementById("facilitySearch");

    if (!searchInput) {
        return;
    }

    searchInput.addEventListener("input", function () {
        clearTimeout(searchTimer);

        searchTimer = setTimeout(function () {
            loadFacilities(1, false);
        }, 400);
    });
}

function initializeFilterEvents() {
    const sportFilter = document.getElementById("sportFilter");

    const typeFilter = document.getElementById("typeFilter");

    const statusFilter = document.getElementById("statusFilter");

    if (sportFilter) {
        sportFilter.addEventListener("change", function () {
            loadFacilities(1, false);
        });
    }

    if (typeFilter) {
        typeFilter.addEventListener("change", function () {
            loadFacilities(1, false);
        });
    }

    if (statusFilter) {
        statusFilter.addEventListener("change", function () {
            loadFacilities(1, false);
        });
    }
}

function resetChoicesSelect(id) {

    const select =
        document.getElementById(id);


    if (!select) {
        return;
    }


    const instance =
        window.choicesMap[id];

    if (instance) {

        try {

            instance.removeActiveItems();

            instance.setChoiceByValue("");

        }

        catch (error) {

            console.warn(
                "Choices reset failed for:",
                id,
                error
            );

        }

    }

    select.value =
        "";

    select.dispatchEvent(
        new Event(
            "change",
            {
                bubbles: true
            }
        )
    );

}

function initializeResetFilters() {

    const resetButton =
        document.getElementById(
            "resetFilters"
        );


    if (!resetButton) {
        return;
    }

    if (
        resetButton.dataset.listenerAdded ===
        "true"
    ) {
        return;
    }

    resetButton.dataset.listenerAdded =
        "true";

    resetButton.addEventListener(
        "click",
        function () {
            const searchInput =
                document.getElementById(
                    "facilitySearch"
                );

            if (searchInput) {

                searchInput.value =
                    "";
            }
            resetChoicesSelect(
                "sportFilter"
            )
            resetChoicesSelect(
                "typeFilter"
            );
            resetChoicesSelect(
                "statusFilter"
            );

            loadFacilities(
                1,
                true
            );


        }
    );

}

function initializeViewFacility() {
    document.addEventListener("click", function (event) {
        const button = event.target.closest(".fc-view");

        if (!button) {
            return;
        }

        const viewName = document.getElementById("view_name");
        const viewSport = document.getElementById("view_sport");
        const viewType = document.getElementById("view_type");
        const viewStatus = document.getElementById("view_status");
        const viewCapacity = document.getElementById("view_capacity");
        const viewLocation = document.getElementById("view_location");
        const viewImage = document.getElementById("view_image");

        if (viewName) {
            viewName.textContent = button.dataset.name || "";
        }

        if (viewSport) {
            viewSport.textContent = button.dataset.sport || "-";
        }

        if (viewType) {
            viewType.textContent = button.dataset.type || "";
        }

        if (viewStatus) {
            viewStatus.textContent = button.dataset.status || "";
        }

        if (viewCapacity) {
            viewCapacity.textContent = button.dataset.capacity || "";
        }

        if (viewLocation) {
            viewLocation.textContent = button.dataset.location || "";
        }

        if (viewImage) {
            viewImage.src = button.dataset.image || DEFAULT_FACILITY_IMAGE;
        }

        const modalElement = document.getElementById("viewFacilityModal");

        if (modalElement) {
            const modal = bootstrap.Modal.getOrCreateInstance(modalElement);

            modal.show();
        }
    });
}

function setSelectValue(select, value) {

    if (!select) {
        return;
    }

    select.value = value;

    const choiceInstance =
        window.choicesMap
            ? window.choicesMap[select.id]
            : null;

    if (choiceInstance) {

        try {

            choiceInstance.removeActiveItems();

            choiceInstance.setChoiceByValue(
                String(value)
            );

        }

        catch (error) {

            console.warn(
                "Choices update failed for:",
                select.id,
                error
            );

        }

    }

    select.dispatchEvent(
        new Event(
            "change",
            {
                bubbles: true
            }
        )
    );

}

function initializeEditFacility() {

    document.addEventListener(
        "click",
        function (event) {

            const button =
                event.target.closest(".fc-edit");


            if (!button) {
                return;
            }


            event.preventDefault();


            console.log(
                "Edit button clicked:",
                button.dataset.id
            );

            const editId =
                document.getElementById("edit_id");

            const editName =
                document.getElementById("edit_name");

            const editSport =
                document.getElementById("edit_sport");

            const editType =
                document.getElementById("edit_type");

            const editStatus =
                document.getElementById("edit_status");

            const editCapacity =
                document.getElementById("edit_capacity");

            const editLocation =
                document.getElementById("edit_location");

            const editPreview =
                document.getElementById("edit_preview");

            const editImage =
                document.getElementById("edit_image");

            if (editId) {
                editId.value =
                    button.dataset.id || "";
            }


            if (editName) {
                editName.value =
                    button.dataset.name || "";
            }


            if (editCapacity) {
                editCapacity.value =
                    button.dataset.capacity || "";
            }


            if (editLocation) {
                editLocation.value =
                    button.dataset.location || "";
            }


            if (editSport) {

                setSelectValue(
                    editSport,
                    button.dataset.sport || ""
                );

            }

            if (editType) {

                setSelectValue(
                    editType,
                    button.dataset.type || ""
                );

            }

            if (editStatus) {
                setSelectValue(
                    editStatus,
                    button.dataset.status || ""
                );

            }

            if (editPreview) {
                editPreview.src =
                    button.dataset.image ||
                    DEFAULT_FACILITY_IMAGE;
            }

            if (editImage) {

                editImage.value = "";

            }

            const editNameError =
                document.getElementById(
                    "editNameError"
                );

            const editCapacityError =
                document.getElementById(
                    "editcapacityError"
                );

            const editImageError =
                document.getElementById(
                    "editimageError"
                );


            if (editNameError) {
                editNameError.textContent = "";
            }


            if (editCapacityError) {
                editCapacityError.textContent = "";
            }


            if (editImageError) {
                editImageError.textContent = "";
            }

            const modalElement =
                document.getElementById(
                    "editFacilityModal"
                );

            if (!modalElement) {
                console.error(
                    "Edit modal not found: #editFacilityModal"
                );
                return;
            }


            if (typeof bootstrap === "undefined") {
                console.error(
                    "Bootstrap JavaScript is not loaded."
                );
                return;
            }


            try {
                const modal =
                    bootstrap.Modal.getOrCreateInstance(
                        modalElement
                    );
                modal.show();


            } catch (error) {
                console.error(
                    "Unable to open edit modal:",
                    error
                );
            }

        }
    );

}


function initializeStatusToggle() {
    document.addEventListener("click", function (event) {
        const button = event.target.closest(".fc-toggle");
        if (!button) {
            return;
        }

        const statusId = document.getElementById("status_id");
        const statusValue = document.getElementById("status_value");
        const statusTitle = document.getElementById("status_title");
        const statusMessage = document.getElementById("status_message");
        const statusButton = document.getElementById("status_btn");

        if (statusId) {
            statusId.value = button.dataset.id || "";
        }

        if (statusValue) {
            statusValue.value = button.dataset.status || "";
        }

        if (button.dataset.status === "INACTIVE") {
            if (statusTitle) {
                statusTitle.innerText = "Deactivate Facility";
            }

            if (statusMessage) {
                statusMessage.innerHTML = `Are you sure you want to deactivate
                        <strong>${button.dataset.name}</strong>?`;
            }

            if (statusButton) {
                statusButton.innerText = "Deactivate";
            }
        } else {

            if (statusTitle) {
                statusTitle.innerText = "Activate Facility";
            }

            if (statusMessage) {
                statusMessage.innerHTML = `Are you sure you want to activate
                        <strong>${button.dataset.name}</strong>?`;
            }

            if (statusButton) {
                statusButton.innerText = "Activate";
            }
        }

        const modalElement = document.getElementById("statusModal");
        if (modalElement) {
            const modal = bootstrap.Modal.getOrCreateInstance(modalElement);

            modal.show();
        }
    });
}

function initializeAddFacilityForm() {
    const form = document.getElementById("facilityForm");

    if (!form) {
        return;
    }

    const facilityName = document.getElementById("facility_name");
    const facilityNameError = document.getElementById("facilityNameError");

    if (facilityName) {
        facilityName.addEventListener("input", function () {
            if (facilityNameError) {
                facilityNameError.textContent = "";
            }

            this.classList.remove("is-invalid");
        });
    }

    const capacity = document.getElementById("capacity");
    const capacityError = document.getElementById("capacityError");

    if (capacity) {
        capacity.addEventListener("input", function () {
            if (/[^0-9]/.test(this.value)) {
                if (capacityError) {
                    capacityError.textContent = "Only numbers are allowed";
                }

                this.classList.add("is-invalid");
            } else {
                if (capacityError) {
                    capacityError.textContent = "";
                }

                this.classList.remove("is-invalid");
            }
        });
    }

    const image = document.getElementById("image");
    const imageError = document.getElementById("imageError");
    const imagePreview = document.getElementById("image_preview");

    if (image) {
        image.addEventListener("change", function () {
            const file = this.files[0];

            if (!file) {
                if (imagePreview) {
                    imagePreview.src = DEFAULT_FACILITY_IMAGE;
                }

                if (imageError) {
                    imageError.textContent = "";
                }

                this.classList.remove("is-invalid");

                return;
            }

            const allowedTypes = ["image/jpeg", "image/png", "image/webp"];

            if (!allowedTypes.includes(file.type)) {
                if (imageError) {
                    imageError.textContent = "Only JPG, PNG and WEBP images are allowed.";
                }

                this.classList.add("is-invalid");

                this.value = "";

                if (imagePreview) {
                    imagePreview.src = DEFAULT_FACILITY_IMAGE;
                }
            } else {
                if (imageError) {
                    imageError.textContent = "";
                }

                this.classList.remove("is-invalid");

                if (imagePreview) {
                    imagePreview.src = URL.createObjectURL(file);
                }
            }
        });
    }

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        if (capacity && /[^0-9]/.test(capacity.value)) {
            if (capacityError) {
                capacityError.textContent = "Only numbers are allowed";
            }

            capacity.focus();

            return;
        }

        const formData = new FormData(form);
        const submitButton = form.querySelector('[type="submit"]');
        const originalButtonText = submitButton ? submitButton.innerHTML : "";

        if (submitButton) {
            submitButton.disabled = true;

            submitButton.innerHTML = `<span class="spinner-border spinner-border-sm"></span>
                     Saving...`;
        }

        fetch(form.action, {
            method: "POST",

            body: formData,

            headers: {
                "X-CSRFToken": getCSRFToken(),

                "X-Requested-With": "XMLHttpRequest",
            },
        })
            .then(function (response) {
                return response.json();
            })

            .then(function (data) {
                if (data.success) {

                    const modalElement = document.getElementById("facilityModal");

                    if (modalElement) {
                        const modal = bootstrap.Modal.getInstance(modalElement);

                        if (modal) {
                            modal.hide();
                        }
                    }

                    window.location.reload();
                } else {
                    if (facilityName) {
                        facilityName.classList.add("is-invalid");
                    }

                    if (facilityNameError) {
                        facilityNameError.textContent = data.message || "Unable to save facility.";
                    }
                }
            })

            .catch(function (error) {
                console.error(error);
            })

            .finally(function () {
                if (submitButton) {
                    submitButton.disabled = false;

                    submitButton.innerHTML = originalButtonText;
                }
            });
    });
}


function initializeEditValidation() {

    const editCapacity = document.getElementById("edit_capacity");

    const editCapacityError = document.getElementById("editcapacityError");

    if (editCapacity) {
        editCapacity.addEventListener("input", function () {
            if (/[^0-9]/.test(this.value)) {
                if (editCapacityError) {
                    editCapacityError.textContent = "Only numbers are allowed";
                }

                this.classList.add("is-invalid");
            } else {
                if (editCapacityError) {
                    editCapacityError.textContent = "";
                }

                this.classList.remove("is-invalid");
            }
        });
    }

    const editImage = document.getElementById("edit_image");
    const editImageError = document.getElementById("editimageError");
    const editPreview = document.getElementById("edit_preview");
    if (editImage) {
        editImage.addEventListener("change", function () {
            const file = this.files[0];

            if (!file) {
                return;
            }

            const allowedTypes = ["image/jpeg", "image/png", "image/webp"];

            if (!allowedTypes.includes(file.type)) {
                if (editImageError) {
                    editImageError.textContent = "Only JPG, PNG and WEBP images are allowed.";
                }

                this.value = "";

                return;
            }

            if (editImageError) {
                editImageError.textContent = "";
            }

            if (editPreview) {
                editPreview.src = URL.createObjectURL(file);
            }
        });
    }
}

function initializeStatusForm() {
    const statusModal = document.getElementById("statusModal");

    if (!statusModal) {
        return;
    }

    const form = statusModal.querySelector("form");

    if (!form) {
        return;
    }

    form.addEventListener("submit", function (event) {
        event.preventDefault();

        const formData = new FormData(form);

        const submitButton = document.getElementById("status_btn");

        const originalText = submitButton ? submitButton.innerHTML : "";

        if (submitButton) {
            submitButton.disabled = true;
        }

        fetch(form.action, {
            method: "POST",

            body: formData,

            headers: {
                "X-CSRFToken": getCSRFToken(),

                "X-Requested-With": "XMLHttpRequest",
            },
        })
            .then(function (response) {
                return response.json();
            })

            .then(function (data) {
                if (data.success) {
                    const modal = bootstrap.Modal.getInstance(statusModal);

                    if (modal) {
                        modal.hide();
                    }

                    loadFacilities(getCurrentPage());
                } else {
                    alert("Unable to update facility status.");
                }
            })

            .catch(function (error) {
                console.error(error);
            })

            .finally(function () {
                if (submitButton) {
                    submitButton.disabled = false;

                    submitButton.innerHTML = originalText;
                }
            });
    });
}

function getCurrentPage() {
    const activePage = document.querySelector(".fc-page-btn.active");

    if (!activePage) {
        return 1;
    }

    const page = parseInt(activePage.textContent.trim());

    return isNaN(page) ? 1 : page;
}

document.addEventListener("DOMContentLoaded", function () {
    initializeViewFacility();
    initializeEditFacility();
    initializeStatusToggle();
    initializeAddFacilityForm();
    initializeEditValidation();
    initializeStatusForm();
    initializeSearchFilter();
    initializeFilterEvents();
    initializeResetFilters();
    initializeChoices();
    if (typeof AOS !== "undefined") {
        AOS.init({
            once: true,

            duration: 600,
        });
    }
});