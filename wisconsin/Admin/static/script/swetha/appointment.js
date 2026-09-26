document.addEventListener("DOMContentLoaded", () => {

    "use strict";
    if (window.lucide) {
        lucide.createIcons();
    }

    const searchInput =
        document.getElementById(
            "appointmentSearch"
        );

    const departmentFilter =
        document.getElementById(
            "departmentFilter"
        );

    const statusFilter =
        document.getElementById(
            "statusFilter"
        );

    const priorityFilter =
        document.getElementById(
            "priorityFilter"
        );

    const resetBtn =
        document.getElementById(
            "resetFilters"
        );

    const tableContainer =
        document.getElementById(
            "appointmentTableContainer"
        );


    if (!tableContainer) {
        return;
    }
    window.choicesMap =
        window.choicesMap || {};


    if (
        departmentFilter &&
        !window.choicesMap.departmentFilter
    ) {

        window.choicesMap.departmentFilter =
            new Choices(
                departmentFilter,
                {
                    searchEnabled: false,
                    shouldSort: false,
                    itemSelectText: "",
                    allowHTML: false,
                }
            );
    }


    if (
        statusFilter &&
        !window.choicesMap.statusFilter
    ) {

        window.choicesMap.statusFilter =
            new Choices(
                statusFilter,
                {
                    searchEnabled: false,
                    shouldSort: false,
                    itemSelectText: "",
                    allowHTML: false,
                }
            );
    }


    if (
        priorityFilter &&
        !window.choicesMap.priorityFilter
    ) {

        window.choicesMap.priorityFilter =
            new Choices(
                priorityFilter,
                {
                    searchEnabled: false,
                    shouldSort: false,
                    itemSelectText: "",
                    allowHTML: false,
                }
            );
    }

    let requestController = null;
    async function loadAppointments(
        page = 1,
        updateBrowserUrl = true
    ) {

        try {
            if (requestController) {
                requestController.abort();
            }

            requestController =
                new AbortController();


            const url =
                new URL(
                    window.location.href
                );
            const search =
                searchInput
                    ? searchInput.value.trim()
                    : "";

            const department =
                departmentFilter
                    ? departmentFilter.value
                    : "";

            const status =
                statusFilter
                    ? statusFilter.value
                    : "";

            const priority =
                priorityFilter
                    ? priorityFilter.value
                    : "";

            url.searchParams.set(
                "page",
                page
            );

            url.searchParams.set(
                "search",
                search
            );

            url.searchParams.set(
                "department",
                department
            );

            url.searchParams.set(
                "status",
                status
            );

            url.searchParams.set(
                "priority",
                priority
            );
            url.searchParams.set(
                "ajax",
                "1"
            );
            tableContainer.classList.add(
                "ao__table-loading"
            );

            const response =
                await fetch(
                    url.toString(),
                    {
                        method: "GET",

                        headers: {
                            "X-Requested-With":
                                "XMLHttpRequest",

                            "Accept":
                                "text/html",
                        },

                        signal:
                            requestController.signal,
                    }
                );


            if (!response.ok) {

                throw new Error(
                    `HTTP ${response.status}`
                );
            }


            const html =
                await response.text();
            const parser =
                new DOMParser();
            const doc =
                parser.parseFromString(
                    html,
                    "text/html"
                );
            const newContainer =
                doc.getElementById(
                    "appointmentTableContainer"
                );

            if (!newContainer) {

                throw new Error(
                    "appointmentTableContainer not found"
                );
            }

            tableContainer.innerHTML =
                newContainer.innerHTML;

            url.searchParams.delete(
                "ajax"
            );


            if (updateBrowserUrl) {

                window.history.pushState(
                    {},
                    "",
                    url.toString()
                );

            } else {

                window.history.replaceState(
                    {},
                    "",
                    url.toString()
                );
            }

            if (window.lucide) {
                lucide.createIcons();
            }


        } catch (error) {

            if (
                error.name ===
                "AbortError"
            ) {
                return;
            }

            console.error(
                "Appointment AJAX error:",
                error
            );

        } finally {

            tableContainer.classList.remove(
                "ao__table-loading"
            );
        }
    }
    document.addEventListener(
        "click",
        (event) => {

            const pageLink =
                event.target.closest(
                    "#appointmentPagination a[data-page]"
                );


            if (!pageLink) {
                return;
            }


            event.preventDefault();
            event.stopPropagation();


            const page =
                pageLink.dataset.page;


            if (!page) {
                return;
            }


            loadAppointments(
                page,
                true
            );
        }
    );

    let searchTimer = null;
    if (searchInput) {
        searchInput.addEventListener(
            "input",
            () => {

                clearTimeout(
                    searchTimer
                );
                searchTimer =
                    setTimeout(
                        () => {

                            loadAppointments(
                                1,
                                true
                            );
                        },
                        300
                    );
            }
        );
    }

    if (departmentFilter) {

        departmentFilter.addEventListener(
            "change",
            () => {

                loadAppointments(
                    1,
                    true
                );
            }
        );
    }

    if (statusFilter) {

        statusFilter.addEventListener(
            "change",
            () => {

                loadAppointments(
                    1,
                    true
                );
            }
        );
    }

    if (priorityFilter) {

        priorityFilter.addEventListener(
            "change",
            () => {

                loadAppointments(
                    1,
                    true
                );
            }
        );
    }

    if (resetBtn) {

        resetBtn.addEventListener(
            "click",
            (event) => {

                event.preventDefault();


                if (searchInput) {
                    searchInput.value = "";
                }


                if (
                    window.choicesMap
                        .departmentFilter
                ) {

                    window.choicesMap
                        .departmentFilter
                        .setChoiceByValue("");
                }


                if (
                    window.choicesMap
                        .statusFilter
                ) {

                    window.choicesMap
                        .statusFilter
                        .setChoiceByValue("");
                }


                if (
                    window.choicesMap
                        .priorityFilter
                ) {

                    window.choicesMap
                        .priorityFilter
                        .setChoiceByValue("");
                }


                loadAppointments(
                    1,
                    true
                );
            }
        );
    }

    window.addEventListener(
        "popstate",
        () => {

            const url =
                new URL(
                    window.location.href
                );

            const page =
                url.searchParams.get(
                    "page"
                ) || 1;

            if (searchInput) {

                searchInput.value =
                    url.searchParams.get(
                        "search"
                    ) || "";
            }

            if (
                window.choicesMap
                    .departmentFilter
            ) {

                window.choicesMap
                    .departmentFilter
                    .setChoiceByValue(
                        url.searchParams.get(
                            "department"
                        ) || ""
                    );
            }

            if (
                window.choicesMap
                    .statusFilter
            ) {

                window.choicesMap
                    .statusFilter
                    .setChoiceByValue(
                        url.searchParams.get(
                            "status"
                        ) || ""
                    );
            }


            if (
                window.choicesMap
                    .priorityFilter
            ) {

                window.choicesMap
                    .priorityFilter
                    .setChoiceByValue(
                        url.searchParams.get(
                            "priority"
                        ) || ""
                    );
            }


            loadAppointments(
                page,
                false
            );
        }
    );

});