// Both choicesInstances and choices map point to the same object

// Create a single shared object
window.choicesInstances = window.choicesInstances || {};

// Alias it so existing code using choicesMap also works
window.choicesMap = window.choicesInstances;

document.addEventListener("DOMContentLoaded", function () {

    document.querySelectorAll("select.form-select").forEach((select) => {
        const instance = new Choices(select, {
            searchEnabled: true,
            shouldSort: false,
            itemSelectText: "",
            allowHTML: false,
        });

        if (select.id) {
            window.choicesInstances[select.id] = instance;
        }
    });

});

document.addEventListener("DOMContentLoaded", function () {

    document.querySelectorAll("select.df-select").forEach(function (select) {

        new Choices(select, {
            searchEnabled: true,
            shouldSort: false,
            itemSelectText: "",
            allowHTML: false,
        });

    });

});


