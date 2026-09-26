document.querySelectorAll(".cw-delete-form").forEach(function (form) {

    form.addEventListener("submit", function (e) {

        e.preventDefault();

        Swal.fire({
            title: "Delete Coursework?",
            text: "This coursework will be permanently deleted.",
            icon: "warning",
            showCancelButton: true,
            confirmButtonColor: "#C5050C",
            cancelButtonColor: "#6c757d",
            confirmButtonText: "Yes, Delete",
            cancelButtonText: "Cancel",
            reverseButtons: true,
        }).then(function (result) {

            if (result.isConfirmed) {
                form.submit();
            }

        });

    });

});