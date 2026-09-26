/* =========================================================
   ISSUE BOOK DETAIL PAGE
   Frontend Interactions
   ========================================================= */

(function () {

    "use strict";


    /* =====================================================
       DOM READY
    ====================================================== */

    document.addEventListener("DOMContentLoaded", function () {

        initCopySelection();
        initIssueForm();
        initNoteInput();
        initCardAnimations();

    });



    /* =====================================================
       COPY SELECTION
       ====================================================== */

    function initCopySelection() {

        const copyOptions =
            document.querySelectorAll(".ib-copy-option");

        if (!copyOptions.length) {
            return;
        }


        copyOptions.forEach(function (option) {

            const radio =
                option.querySelector('input[type="radio"]');

            if (!radio) {
                return;
            }


            /*
             * Set initial selected state.
             */

            if (radio.checked) {
                option.classList.add("selected");
            }


            /*
             * Click on entire card.
             */

            option.addEventListener("click", function (event) {

                /*
                 * Ignore clicks that are already directly
                 * handled by the radio input.
                 */

                if (event.target !== radio) {
                    radio.checked = true;
                }


                updateSelectedCopy(copyOptions, option);

            });


            /*
             * Keyboard accessibility.
             */

            radio.addEventListener("change", function () {

                updateSelectedCopy(
                    copyOptions,
                    option
                );

            });

        });

    }



    /* =====================================================
       UPDATE SELECTED COPY
       ====================================================== */

    function updateSelectedCopy(copyOptions, selectedOption) {

        copyOptions.forEach(function (option) {

            option.classList.remove("selected");

        });


        selectedOption.classList.add("selected");


        /*
         * Small visual feedback.
         */

        selectedOption.animate(
            [
                {
                    transform: "translateX(0)"
                },
                {
                    transform: "translateX(4px)"
                },
                {
                    transform: "translateX(0)"
                }
            ],
            {
                duration: 230,
                easing: "ease-out"
            }
        );

    }



    /* =====================================================
       ISSUE FORM
       ====================================================== */

    function initIssueForm() {

        const form =
            document.getElementById("issueBookForm");

        if (!form) {
            return;
        }


        const submitButton =
            document.getElementById("issueBookButton");


        /*
         * If the page is blocked, there is no submit button.
         */

        if (!submitButton) {
            return;
        }


        form.addEventListener("submit", function (event) {

            /*
             * Find selected copy.
             */

            const selectedCopy =
                form.querySelector(
                    'input[name="copy_id"]:checked'
                );


            /*
             * No copy selected.
             */

            if (!selectedCopy) {

                event.preventDefault();

                showCopySelectionWarning();

                return;

            }


            /*
             * Prevent accidental double submission.
             */

            if (form.dataset.submitting === "true") {

                event.preventDefault();

                return;

            }


            form.dataset.submitting = "true";


            /*
             * Change button appearance.
             */

            submitButton.disabled = true;

            submitButton.classList.add(
                "ib-submit-loading"
            );


            submitButton.innerHTML = `
                <span class="ib-spinner"></span>
                <span>Issuing Book...</span>
            `;


            /*
             * Small selected-card animation.
             */

            const selectedOption =
                selectedCopy.closest(
                    ".ib-copy-option"
                );


            if (selectedOption) {

                selectedOption.classList.add(
                    "ib-copy-processing"
                );

            }

        });

    }



    /* =====================================================
       COPY SELECTION WARNING
       ====================================================== */

    function showCopySelectionWarning() {

        const copyCard =
            document.querySelector(".ib-copy-card");

        if (!copyCard) {
            return;
        }


        /*
         * Remove existing warning first.
         */

        const existing =
            copyCard.querySelector(
                ".ib-js-warning"
            );


        if (existing) {
            existing.remove();
        }


        /*
         * Create warning.
         */

        const warning =
            document.createElement("div");

        warning.className =
            "ib-copy-hint ib-js-warning";


        warning.innerHTML = `
            <svg viewBox="0 0 24 24" aria-hidden="true">
                <circle cx="12" cy="12" r="9"></circle>
                <path d="M12 7v5"></path>
                <path d="M12 16h.01"></path>
            </svg>

            <span>
                Please select an available copy before issuing the book.
            </span>
        `;


        copyCard.appendChild(warning);


        /*
         * Scroll to copy selection.
         */

        copyCard.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });


        /*
         * Shake the card.
         */

        copyCard.animate(
            [
                {
                    transform: "translateX(0)"
                },
                {
                    transform: "translateX(-5px)"
                },
                {
                    transform: "translateX(5px)"
                },
                {
                    transform: "translateX(-4px)"
                },
                {
                    transform: "translateX(4px)"
                },
                {
                    transform: "translateX(0)"
                }
            ],
            {
                duration: 380,
                easing: "ease-out"
            }
        );


        /*
         * Automatically remove warning.
         */

        setTimeout(function () {

            if (warning.isConnected) {
                warning.remove();
            }

        }, 4000);

    }



    /* =====================================================
       NOTE INPUT
       ====================================================== */

    function initNoteInput() {

        const noteInput =
            document.getElementById("issueNote");

        if (!noteInput) {
            return;
        }


        /*
         * Subtle active state.
         */

        noteInput.addEventListener(
            "focus",
            function () {

                noteInput.closest(".ib-note")
                    ?.classList.add(
                        "ib-note-active"
                    );

            }
        );


        noteInput.addEventListener(
            "blur",
            function () {

                noteInput.closest(".ib-note")
                    ?.classList.remove(
                        "ib-note-active"
                    );

            }
        );


        /*
         * Limit note length.
         */

        noteInput.addEventListener(
            "input",
            function () {

                const maxLength = 250;

                if (
                    noteInput.value.length >
                    maxLength
                ) {

                    noteInput.value =
                        noteInput.value.substring(
                            0,
                            maxLength
                        );

                }

            }
        );

    }



    /* =====================================================
       CARD ENTER ANIMATIONS
       ====================================================== */

    function initCardAnimations() {

        const cards =
            document.querySelectorAll(
                ".ib-card, .ib-action-card, .ib-policy"
            );

        if (!cards.length) {
            return;
        }


        cards.forEach(function (card, index) {

            card.style.setProperty(
                "--ib-animation-delay",
                `${Math.min(index * 70, 350)}ms`
            );

        });

    }



    /* =====================================================
       PREVENT ENTER KEY FROM ACCIDENTALLY SUBMITTING
       ====================================================== */

    const issueForm =
        document.getElementById("issueBookForm");


    if (issueForm) {

        issueForm.addEventListener(
            "keydown",
            function (event) {

                /*
                 * Prevent Enter inside the note field from
                 * submitting the entire issue form.
                 */

                if (
                    event.key === "Enter" &&
                    event.target.id === "issueNote"
                ) {

                    event.preventDefault();

                }

            }
        );

    }



    /* =====================================================
       ESCAPE KEY
       ====================================================== */

    document.addEventListener(
        "keydown",
        function (event) {

            if (event.key !== "Escape") {
                return;
            }


            const warning =
                document.querySelector(
                    ".ib-js-warning"
                );


            if (warning) {
                warning.remove();
            }

        }
    );

})();