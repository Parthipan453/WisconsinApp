// Navina code

document.addEventListener("DOMContentLoaded", function () {

    initializeLibraryChoices();

});


function initializeLibraryChoices() {

    const selects = document.querySelectorAll(
        "select.library-choice"
    );

    selects.forEach(function (select) {

        // Already initialized
        if (select.dataset.initialized === "true") {
            return;
        }

        new Choices(select, {

            searchEnabled: false,

            searchChoices: false,

            itemSelectText: "",

            shouldSort: false,

            allowHTML: false,

            removeItemButton: false,

            duplicateItemsAllowed: false,

            position: "auto"

        });

        select.dataset.initialized = "true";

    });

}