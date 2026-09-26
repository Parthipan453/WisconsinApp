function openFilter(tabId) {

    // Open Bootstrap modal
    const modalElement = document.getElementById("filterModal");

    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);

    modal.show();

    // Activate selected tab after modal opens
    setTimeout(function () {

        const trigger = document.querySelector(
            '#filterTabs button[data-bs-target="#' + tabId + '"]'
        );

        if (trigger) {

            const tab = new bootstrap.Tab(trigger);

            tab.show();

        }

    }, 100);

}
function applyFilter(type, value) {

    const url = new URL(window.location.href);

    // Remove page number when applying a new filter
    url.searchParams.delete("page");

    // Add or update the filter
    url.searchParams.set(type, value);

    window.location.href = url.toString();

}