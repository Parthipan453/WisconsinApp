document.addEventListener("DOMContentLoaded", function () {
    var venueModalEl = document.getElementById("venueModal");
    var venueModal = venueModalEl ? new bootstrap.Modal(venueModalEl) : null;

    var nameInput = document.querySelector('[name="venue_name"]');
    var buildingInput = document.querySelector('[name="building_name"]');
    var roomInput = document.querySelector('[name="room_number"]');
    var capacityInput = document.querySelector('[name="seating_capacity"]');
    var locationInput = document.querySelector('[name="location_details"]');
    var idInput = document.getElementById("venueIdInput");
    var titleEl = document.getElementById("venueModalLabel");
    var submitTextEl = document.getElementById("venueSubmitText");

    var listContainer = document.getElementById("venuesListContainer");
    var searchInput = document.getElementById("filterSearch");
    var resultCountEl = document.getElementById("venueResultCount");

    var searchDebounce = null;

    var addBtn = document.getElementById("btnAddVenue");
    if (addBtn) {
        addBtn.addEventListener("click", function () {
            resetVenueForm();
            setVenueModalMode(false);
            venueModal.show();
        });
    }

    if (searchInput) {
        searchInput.addEventListener("input", function () {
            clearTimeout(searchDebounce);
            searchDebounce = setTimeout(function () {
                fetchVenues(1);
            }, 350);
        });
    }

    if (listContainer) {
        listContainer.addEventListener("click", function (e) {
            var editBtn = e.target.closest(".btn-edit-venue");
            var deleteBtn = e.target.closest(".btn-delete-venue");
            var pageBtn = e.target.closest(".page-btn");

            if (editBtn) {
                e.preventDefault();
                var row = editBtn.closest("tr");

                if (nameInput) nameInput.value = row.dataset.venueName;
                if (buildingInput) buildingInput.value = row.dataset.buildingName;
                if (roomInput) roomInput.value = row.dataset.roomNumber;
                if (capacityInput) capacityInput.value = row.dataset.seatingCapacity;
                if (locationInput) locationInput.value = row.dataset.locationDetails;
                if (idInput) idInput.value = row.dataset.venueId;

                setVenueModalMode(true);
                venueModal.show();
                return;
            }

            if (deleteBtn) {
                e.preventDefault();
                var row = deleteBtn.closest("tr");
                var venueId = row.dataset.venueId;
                var venueName = row.dataset.venueName;

                if (!confirm('Delete venue "' + venueName + '"? This cannot be undone.')) {
                    return;
                }

                var form = document.createElement("form");
                form.method = "post";
                form.action = "";

                var csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
                form.innerHTML =
                    '<input type="hidden" name="csrfmiddlewaretoken" value="' + csrf + '">' +
                    '<input type="hidden" name="action" value="delete">' +
                    '<input type="hidden" name="venue_id" value="' + venueId + '">';

                document.body.appendChild(form);
                form.submit();
                return;
            }

            if (pageBtn) {
                e.preventDefault();
                fetchVenues(pageBtn.dataset.page);
            }
        });
    }

    function fetchVenues(page) {
        var params = new URLSearchParams();
        params.set("page", page);
        if (searchInput && searchInput.value.trim()) {
            params.set("search", searchInput.value.trim());
        }

        fetch(window.location.pathname + "?" + params.toString(), {
            headers: { "X-Requested-With": "XMLHttpRequest" },
        })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                listContainer.innerHTML = data.html;
                if (resultCountEl) resultCountEl.textContent = data.count_text;

                var newUrl = window.location.pathname + "?" + params.toString();
                window.history.replaceState({}, "", newUrl);
            })
            .catch(function (err) {
                console.error("Failed to load venues:", err);
            });
    }

    function resetVenueForm() {
        if (nameInput) nameInput.value = "";
        if (buildingInput) buildingInput.value = "";
        if (roomInput) roomInput.value = "";
        if (capacityInput) capacityInput.value = "";
        if (locationInput) locationInput.value = "";
        if (idInput) idInput.value = "";
    }

    window.setVenueModalMode = function (isEdit) {
        if (titleEl) titleEl.textContent = isEdit ? "Edit Event Venue" : "Add Event Venue";
        if (submitTextEl) submitTextEl.textContent = isEdit ? "Update Venue" : "Save Venue";
    };
});