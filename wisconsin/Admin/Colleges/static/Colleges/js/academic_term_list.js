//Steve code

document.addEventListener("DOMContentLoaded", () => {


    
    const statusModal = document.getElementById("statusModal");

    statusModal.addEventListener("show.bs.modal", function (event) {

        const button = event.relatedTarget;

        const url = button.dataset.url;
        const action = button.dataset.action;
        const name = button.dataset.name;

        document.getElementById("confirmStatusBtn").href = url;

        document.getElementById("statusMessage").innerHTML =
            `Are you sure you want to <strong>${action}</strong> <strong>${name}</strong>?`;

    });

    document.getElementById("clearSearch")?.addEventListener("click", () => {
        const input = document.getElementById("atSearch");
        if (input) {
            input.value = "";
            input.focus();
        }
    });

   
    document.querySelectorAll(".filter-select").forEach(sel => {
        sel.addEventListener("change", () => {
            document.getElementById("filterForm")?.submit();
        });
    });

});


document.addEventListener("DOMContentLoaded", function () {

    document.querySelectorAll("select.filter-select").forEach(function (select) {

        new Choices(select, {
            searchEnabled: true,
            shouldSort: false,
            itemSelectText: "",
            allowHTML: false,
        });

    });

});