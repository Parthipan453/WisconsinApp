let choices = null;
let searchInput = null;
let debounceTimer = null;
document.addEventListener("DOMContentLoaded", function () {

    const statusElement =
        document.getElementById("statusFilter");

    searchInput =
        document.getElementById("searchInput");

    if (statusElement) {

        choices = new Choices(
            statusElement,
            {
                searchEnabled: false,
                itemSelectText: "",
                shouldSort: false,
                shouldSortItems: false,
                position: "bottom",
                allowHTML: true
            }
        );
    }

    const navigationEntries =
        performance.getEntriesByType("navigation");

    const navigationType =
        navigationEntries.length
            ? navigationEntries[0].type
            : "";


    const isRefresh =
        navigationType === "reload";

    if (isRefresh) {

        resetFiltersAfterRefresh();

    } else {

        restoreFilterValues();
    }

    if (searchInput) {

        searchInput.addEventListener(
            "input",
            function () {

                clearTimeout(
                    debounceTimer
                );

                debounceTimer =
                    setTimeout(
                        function () {

                            applyFilters();

                        },
                        500
                    );
            }
        );
    }

    if (statusElement) {

        statusElement.addEventListener(
            "change",
            function () {

                applyFilters();

            }
        );
    }

    document.addEventListener(
        "click",
        function (event) {

            const pageLink =
                event.target.closest(
                    ".ajax-page"
                );

            if (!pageLink) {
                return;
            }

            event.preventDefault();

            loadAppointments(
                pageLink.href
            );
        }
    );

    checkReasonScroll();

    startCountdown();

    window.addEventListener(
        "resize",
        checkReasonScroll
    );
});

function resetFiltersAfterRefresh() {

    const url =
        new URL(
            window.location.href
        );

    url.searchParams.delete(
        "status"
    );

    url.searchParams.delete(
        "search"
    );

    url.searchParams.delete(
        "page"
    );

    window.history.replaceState(
        {},
        "",
        url.pathname
    );

    if (searchInput) {

        searchInput.value = "";
    }

    if (choices) {

        choices.removeActiveItems();

        choices.setChoiceByValue(
            "All Status"
        );
    }

    loadAppointments(
        url.pathname
    );
}
function restoreFilterValues() {

    const url =
        new URL(
            window.location.href
        );

    const searchValue =
        url.searchParams.get(
            "search"
        ) || "";


    if (searchInput) {

        searchInput.value =
            searchValue;
    }

    const statusValue =
        (
            url.searchParams.get(
                "status"
            ) || ""
        )
        .trim()
        .toUpperCase();


    if (choices) {

        if (statusValue) {

            choices.setChoiceByValue(
                statusValue
            );

        } else {

            choices.setChoiceByValue(
                "All Status"
            );
        }
    }
}
function applyFilters() {

    const url =
        new URL(
            window.location.href
        );
    const searchValue =
        searchInput
            ? searchInput.value.trim()
            : "";


    if (searchValue) {

        url.searchParams.set(
            "search",
            searchValue
        );

    } else {

        url.searchParams.delete(
            "search"
        );
    }

    let statusValue = "";


    if (choices) {

        statusValue =
            choices.getValue(true);
    }


    statusValue =
        String(
            statusValue || ""
        )
        .trim()
        .toUpperCase();


    if (
        statusValue &&
        statusValue !== "ALL STATUS"
    ) {

        url.searchParams.set(
            "status",
            statusValue
        );

    } else {

        url.searchParams.delete(
            "status"
        );
    }

    url.searchParams.delete(
        "page"
    );

    window.history.pushState(
        {},
        "",
        url.toString()
    );

    loadAppointments(
        url.toString()
    );
}
function loadAppointments(url) {

    const wrapper =
        document.getElementById(
            "appointmentTableWrapper"
        );

    const statsWrapper =
        document.getElementById(
            "appointmentStatsWrapper"
        );


    if (!wrapper) {
        return;
    }

    wrapper.style.opacity =
        "0.5";

    wrapper.style.pointerEvents =
        "none";


    if (statsWrapper) {

        statsWrapper.style.opacity =
            "0.5";

        statsWrapper.style.pointerEvents =
            "none";
    }

    fetch(
        url,
        {
            headers: {
                "X-Requested-With":
                    "XMLHttpRequest"
            }
        }
    )
    .then(
        function (response) {

            if (!response.ok) {

                throw new Error(
                    "Failed to load appointments"
                );
            }

            return response.text();
        }
    )
    .then(
        function (html) {

            const parser =
                new DOMParser();


            const doc =
                parser.parseFromString(
                    html,
                    "text/html"
                );

            const newWrapper =
                doc.getElementById(
                    "appointmentTableWrapper"
                );


            if (newWrapper) {

                wrapper.innerHTML =
                    newWrapper.innerHTML;
            }
            const newStatsWrapper =
                doc.getElementById(
                    "appointmentStatsWrapper"
                );


            if (
                statsWrapper &&
                newStatsWrapper
            ) {

                statsWrapper.innerHTML =
                    newStatsWrapper.innerHTML;
            }

            checkReasonScroll();

            startCountdown();

            wrapper.style.opacity =
                "1";

            wrapper.style.pointerEvents =
                "auto";


            if (statsWrapper) {

                statsWrapper.style.opacity =
                    "1";

                statsWrapper.style.pointerEvents =
                    "auto";
            }
        }
    )
    .catch(
        function (error) {

            console.error(
                "Appointment loading error:",
                error
            );


            wrapper.style.opacity =
                "1";

            wrapper.style.pointerEvents =
                "auto";


            if (statsWrapper) {

                statsWrapper.style.opacity =
                    "1";

                statsWrapper.style.pointerEvents =
                    "auto";
            }
        }
    );
}
function startCountdown() {

    document
        .querySelectorAll(".countdown")
        .forEach(
            function (timer) {

                const createdValue =
                    timer.dataset.created;


                if (!createdValue) {
                    return;
                }


                const created =
                    new Date(
                        createdValue
                    );


                if (
                    isNaN(
                        created.getTime()
                    )
                ) {
                    return;
                }


                const cancelBtn =
                    timer.previousElementSibling;


                if (!cancelBtn) {
                    return;
                }


                function update() {

                    const expire =
                        created.getTime()
                        +
                        (
                            10 *
                            60 *
                            1000
                        );


                    const diff =
                        expire -
                        Date.now();


                    if (diff <= 0) {

                        timer.innerHTML =
                            "Cancel time expired";


                        cancelBtn.classList.remove(
                            "btn-outline-danger"
                        );


                        cancelBtn.classList.add(
                            "btn-outline-secondary"
                        );


                        cancelBtn.removeAttribute(
                            "href"
                        );


                        cancelBtn.style.pointerEvents =
                            "none";


                        cancelBtn.style.opacity =
                            "0.6";


                        return;
                    }


                    const minutes =
                        Math.floor(
                            diff / 60000
                        );


                    const seconds =
                        Math.floor(
                            (
                                diff %
                                60000
                            ) / 1000
                        );


                    timer.innerHTML =
                        `${minutes}:${String(
                            seconds
                        ).padStart(
                            2,
                            "0"
                        )} remaining`;


                    setTimeout(
                        update,
                        1000
                    );
                }


                update();
            }
        );
}

function checkReasonScroll() {

    document
        .querySelectorAll(
            ".reason-cell"
        )
        .forEach(
            function (cell) {

                if (
                    cell.scrollWidth >
                    cell.clientWidth
                ) {

                    cell.classList.add(
                        "has-scroll"
                    );

                } else {

                    cell.classList.remove(
                        "has-scroll"
                    );
                }
            }
        );
}


