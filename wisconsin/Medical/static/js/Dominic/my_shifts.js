document.addEventListener("DOMContentLoaded", function () {
    const dropdowns = document.querySelectorAll("[data-reminder-dropdown]");

    if (!dropdowns.length) {
        return;
    }

    dropdowns.forEach(function (dropdown) {
        const trigger = dropdown.querySelector("[data-reminder-trigger]");
        const menu = dropdown.querySelector("[data-reminder-menu]");
        const selectedText = dropdown.querySelector("[data-reminder-selected]");
        const hiddenInput = dropdown.querySelector("[data-reminder-value]");
        const options = dropdown.querySelectorAll(".sched-note-dropdown__option");

        if (!trigger || !menu || !selectedText || !hiddenInput) {
            console.warn("Reminder dropdown initialization failed:",dropdown);
            return;
        }

        let isOpen = false;
        const originalParent = menu.parentElement;
        const originalNextSibling = menu.nextSibling;
        const notePopover = dropdown.closest("[data-note-popover]");

        function positionMenu() {
            if (!isOpen) {
                return;
            }
            const triggerRect = trigger.getBoundingClientRect();
            const viewportWidth = window.innerWidth;
            const viewportHeight = window.innerHeight;

            const GAP = 5;
            const VIEWPORT_PADDING = 8;
            let menuWidth = Math.max( triggerRect.width, 210);
            menuWidth = Math.min( menuWidth, viewportWidth - (VIEWPORT_PADDING * 2));
            menu.style.width = menuWidth + "px";
            menu.style.maxHeight = "";

            const menuRect = menu.getBoundingClientRect();
            const menuHeight = menuRect.height;
            const spaceBelow = viewportHeight - triggerRect.bottom - GAP - VIEWPORT_PADDING;
            const spaceAbove = triggerRect.top - GAP - VIEWPORT_PADDING;
            let top;
            let left;

            if (spaceBelow >= menuHeight || spaceBelow >= spaceAbove) {
                top = triggerRect.bottom + GAP;
            } else {
                top = triggerRect.top - menuHeight - GAP;
            }

            if (top < VIEWPORT_PADDING) {
                top = VIEWPORT_PADDING;
            }

            const availableHeight = viewportHeight - top - VIEWPORT_PADDING;
            if (availableHeight < menuHeight) {
                menu.style.maxHeight = Math.max(availableHeight, 80) + "px";
                menu.style.overflowY = "auto";
            } else {
                menu.style.maxHeight = "";
                menu.style.overflowY = "";
            }

            left = triggerRect.left;
            if (left + menuWidth > viewportWidth - VIEWPORT_PADDING) {
                left = viewportWidth - menuWidth - VIEWPORT_PADDING;
            }

            if (left < VIEWPORT_PADDING) {
                left = VIEWPORT_PADDING;
            }
            menu.style.top = top + "px";
            menu.style.left = left + "px";
        }

        function closeOtherDropdowns() {
            document.querySelectorAll("[data-reminder-dropdown]").forEach(function (otherDropdown) {
                    if (otherDropdown !== dropdown) {
                        if (typeof otherDropdown ._closeReminderDropdown === "function") {
                            otherDropdown ._closeReminderDropdown();
                        }
                    }
                });
        }

        function openDropdown() {
            if (isOpen) {
                return;
            }
            closeOtherDropdowns();
            isOpen = true;
            dropdown.classList.add("is-open");
            document.body.appendChild(menu);
            menu.classList.add("sched-reminder-dropdown-portal");
            menu.classList.add("is-visible");
            trigger.setAttribute("aria-expanded",  "true");
            requestAnimationFrame(
                function () {
                    positionMenu();
                }
            );
        }

        function closeDropdown() {
            if (!isOpen) {
                return;
            }
            isOpen = false;
            dropdown.classList.remove("is-open");
            menu.classList.remove("is-visible");
            menu.classList.remove("sched-reminder-dropdown-portal");
            trigger.setAttribute("aria-expanded", "false");
            menu.style.top = "";
            menu.style.left = "";
            menu.style.width = "";
            menu.style.maxHeight = "";
            menu.style.overflowY = "";
            if (originalNextSibling && originalNextSibling.parentNode === originalParent) {
                originalParent.insertBefore(menu, originalNextSibling);
            } else {
                originalParent.appendChild(menu);
            }
        }
        dropdown._closeReminderDropdown =
            closeDropdown;
        function toggleDropdown() {
            if (isOpen) {
                closeDropdown();
            } else {
                openDropdown();
            }
        }

        trigger.addEventListener(
            "click",
            function (event) {
                event.preventDefault();
                event.stopPropagation();
                toggleDropdown();
            }
        );

        options.forEach(
            function (option) {

                option.addEventListener(
                    "click",
                    function (event) {
                        event.preventDefault();
                        event.stopPropagation();

                        const value = option.getAttribute("data-value");
                        const textElement = option.querySelector(".sched-note-dropdown__option-text");
                        const text = textElement ? textElement.textContent.trim() : "";
                        hiddenInput.value = value;
                        hiddenInput.setAttribute("data-reminder-offset", "");
                        selectedText.textContent =text;
                        options.forEach(
                            function (item) {
                                item.classList.remove("is-selected");
                                item.setAttribute("aria-selected", "false");
                            }
                        );

                        option.classList.add("is-selected");
                        option.setAttribute("aria-selected", "true");
                        hiddenInput.dispatchEvent(
                            new Event(
                                "change",
                                {
                                    bubbles: true
                                }
                            )
                        );
                        closeDropdown();
                        trigger.focus();
                    }
                );
            }
        );

        menu.addEventListener(
            "click",
            function (event) {
                event.stopPropagation();
            }
        );

        trigger.addEventListener(
            "keydown",
            function (event) {
                if (event.key === "Enter") {
                    event.preventDefault();
                    event.stopPropagation();
                    toggleDropdown();
                    return;
                }

                if (event.key === " ") {
                    event.preventDefault();
                    event.stopPropagation();
                    toggleDropdown();
                    return;
                }

                if (event.key === "Escape") {
                    event.preventDefault();
                    event.stopPropagation();
                    closeDropdown();
                    return;
                }
            }
        );


        options.forEach(
            function (option, index) {
                option.addEventListener(
                    "keydown",
                    function (event) {
                        if (event.key === "Escape") {
                            event.preventDefault();
                            event.stopPropagation();
                            closeDropdown();
                            trigger.focus();
                            return;
                        }

                        if (event.key === "Enter") {
                            event.preventDefault();
                            event.stopPropagation();
                            option.click();
                            return;
                        }
                        if (event.key === " ") {
                            event.preventDefault();
                            event.stopPropagation();
                            option.click();
                            return;
                        }
                    }
                );
            }
        );

        document.addEventListener(
            "click",
            function (event) {
                if (dropdown.contains(event.target) || menu.contains(event.target)) {
                    return;
                }
                closeDropdown();
            }
        );

        document.addEventListener(
            "keydown",
            function (event) {
                if (event.key === "Escape" && isOpen) {
                    event.preventDefault();
                    event.stopPropagation();
                    closeDropdown();
                    trigger.focus();
                }
            }
        );

        window.addEventListener(
            "resize",
            function () {
                if (isOpen) {
                    positionMenu();
                }
            }
        );

        window.addEventListener(
            "scroll",
            function () {
                if (isOpen) {
                    positionMenu();
                }
            },
            true
        );

        document.addEventListener(
            "visibilitychange",
            function () {
                if (document.hidden && isOpen) {
                    closeDropdown();
                }
            }
        );

        function syncInitialValue() {
            const currentValue =
                hiddenInput.value;
            if (!currentValue) {
                hiddenInput.value = "10";
            }
            hiddenInput.setAttribute("data-reminder-offset", "");
            options.forEach(
                function (option) {
                    const optionValue = option.getAttribute("data-value");
                    if (optionValue === hiddenInput.value) {
                        option.classList.add("is-selected");
                        option.setAttribute("aria-selected", "true");
                        const textElement =
                            option.querySelector(".sched-note-dropdown__option-text");
                        if (textElement) {
                            selectedText.textContent = textElement.textContent.trim();
                        }
                    } else {
                        option.classList.remove("is-selected");
                        option.setAttribute("aria-selected", "false");
                    }
                }
            );
        }
        syncInitialValue();
    });
});