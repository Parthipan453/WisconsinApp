document.addEventListener("DOMContentLoaded", function () {

    function initIcons() {
        if (window.lucide && typeof window.lucide.createIcons === "function") {
            window.lucide.createIcons();
        }
    }

    function fixBrokenPageIcons() {
        document.querySelectorAll(".permission-page-icon i[data-lucide]").forEach(function (el) {
            if (!el.querySelector("svg")) {
                el.setAttribute("data-lucide", "file");
            }
        });
        initIcons();
    }

    initIcons();

    requestAnimationFrame(function () {
        initIcons();
        fixBrokenPageIcons();
    });

    var allGroups = document.querySelectorAll(".permission-page-group");
    allGroups.forEach(function (group, index) {

        if (index !== 0) {
            group.classList.add("is-collapsed");
        }
    });


    document.querySelectorAll("[data-toggle-group]").forEach(function (head) {
            head.addEventListener("click", function () {
                var group = head.closest(".permission-page-group");
                if (group) {
                    group.classList.toggle("is-collapsed");
                }
            });
        });

    document.querySelectorAll("[data-toggle-tech]").forEach(function (btn) {
            btn.addEventListener("click", function (e) {
                e.stopPropagation();
                var details = btn.nextElementSibling;
                if (details) {
                    details.hidden = !details.hidden;
                }
            });
        });

    function closeLocationPopover(group) {
        if (!group) {
            return;
        }
        var trail = group.querySelector(".page-location__trail");
        var btn = group.querySelector("[data-toggle-location]");
        if (trail) {
            trail.hidden = true;
        }
        if (btn) {
            btn.setAttribute("aria-expanded", "false");
        }
        group.classList.remove("is-expanded");
    }

    document.querySelectorAll("[data-toggle-location]").forEach(function (btn) {
            btn.addEventListener("click", function (e) {
                e.stopPropagation();
                var trail = btn.nextElementSibling;
                if (!trail) {
                    return;
                }
                var group = btn.closest(".page-location");
                var wasHidden = trail.hidden;

                document.querySelectorAll(".page-location.is-expanded").forEach(function (openGroup) {
                    if (openGroup !== group) {
                        closeLocationPopover(openGroup);
                    }
                });

                trail.hidden = !wasHidden;
                btn.setAttribute("aria-expanded", wasHidden ? "true" : "false");
                if (group) {
                    group.classList.toggle("is-expanded", wasHidden);
                }
            });
        });

    document.addEventListener("click", function (e) {
            document.querySelectorAll(".page-location.is-expanded").forEach(function (group) {
                if (!group.contains(e.target)) {
                    closeLocationPopover(group);
                }
            });
        }
    );

    document.addEventListener("keydown", function (e) {
            if (e.key === "Escape") {
                document.querySelectorAll(".page-location.is-expanded").forEach(closeLocationPopover);
            }
        }
    );

    document.querySelectorAll("[data-role-chip]").forEach(function (chip) {
            var input = chip.querySelector("input");
            if (!input) {
                return;
            }
            var sync = function () {
                chip.classList.toggle(
                    "is-checked",
                    input.checked
                );
            };

            sync();

            input.addEventListener(
                "change",
                sync
            );
        });

    var editModal = document.getElementById("editPageModal");
    var currentEditPk = null;
    var editIconSelect = document.getElementById("editIcon");
    var editIconPreview = document.getElementById("editIconPreview");
    var iconDropdown = null;
    var iconDropdownTrigger = null;
    var iconDropdownMenu = null;

    function getIconLabel(value) {
        if (!editIconSelect) {
            return value || "File";
        }

        var option = null;

        try {
            option = editIconSelect.querySelector(
                'option[value="' +
                CSS.escape(value || "") +
                '"]'
            );
        } catch (error) {
            var options = editIconSelect.options;

            for (var i = 0; i < options.length; i++) {
                if (options[i].value === value) {
                    option = options[i];
                    break;
                }
            }
        }

        return option
            ? option.textContent.trim()
            : (value || "File");
    }

    function renderCustomIconDropdown() {
        if (!editIconSelect || !editIconSelect.parentElement) {
            return;
        }

        var existing = editIconSelect.parentElement.querySelector(".permission-icon-dropdown");

        if (existing) {
            existing.remove();
        }

        iconDropdown = document.createElement("div");
        iconDropdown.className = "permission-icon-dropdown";
        iconDropdown.setAttribute("data-icon-dropdown", "");
        iconDropdown.innerHTML =
            '<button ' + 'type="button" ' + 'class="permission-icon-dropdown__trigger" ' + 'aria-haspopup="listbox" ' + 'aria-expanded="false">' +
                '<span ' + 'class="permission-icon-dropdown__trigger-icon" ' + 'aria-hidden="true">' + '</span>' +
                '<span ' + 'class="permission-icon-dropdown__label">' + '</span>' +
                '<span ' + 'class="permission-icon-dropdown__chevron" ' + 'aria-hidden="true">' +
                    '<i data-lucide="chevron-down"></i>' +
                '</span>' +
            '</button>' +

            '<div ' + 'class="permission-icon-dropdown__menu" ' + 'role="listbox" ' + 'tabindex="-1">' + '</div>';
        editIconSelect.parentElement.appendChild(iconDropdown);

        iconDropdownTrigger = iconDropdown.querySelector(".permission-icon-dropdown__trigger");
        iconDropdownMenu = iconDropdown.querySelector(".permission-icon-dropdown__menu");

        Array.prototype.forEach.call(
            editIconSelect.options,
            function (option) {
                var item = document.createElement("button");
                item.type = "button";
                item.className = "permission-icon-dropdown__option";
                item.dataset.value = option.value;
                item.setAttribute("role", "option");
                item.setAttribute("aria-selected", "false");
                item.innerHTML =
                    '<span ' + 'class="permission-icon-dropdown__option-icon" ' + 'aria-hidden="true">' +
                        '<i data-lucide="' + option.value + '"></i>' +
                    '</span>' +
                    '<span ' + 'class="permission-icon-dropdown__option-label">' + '</span>';

                var label = item.querySelector(".permission-icon-dropdown__option-label");
                if (label) {
                    label.textContent = option.textContent.trim();
                }

                item.addEventListener(
                    "click",
                    function () {
                        setIconValue(option.value, true);

                        closeIconDropdown();

                        if (iconDropdownTrigger) {
                            iconDropdownTrigger.focus();
                        }
                    }
                );
                iconDropdownMenu.appendChild(item);
            }
        );

        iconDropdownTrigger.addEventListener("click", function (e) {
                e.preventDefault();
                e.stopPropagation();
                toggleIconDropdown();
            }
        );

        iconDropdownTrigger.addEventListener("keydown", function (e) {
                if (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    openIconDropdown();
                    focusSelectedIconOption();
                } else if (e.key === "Escape") {
                    closeIconDropdown();
                }
            }
        );

        iconDropdownMenu.addEventListener("keydown", function (e) {
                var options = Array.prototype.slice.call(iconDropdownMenu.querySelectorAll(".permission-icon-dropdown__option"));
                var current = options.indexOf(document.activeElement);

                if (e.key === "ArrowDown") {
                    e.preventDefault();
                    if (options.length) {
                        options[
                            Math.min(current + 1, options.length - 1)
                        ].focus();
                    }
                } else if (e.key === "ArrowUp") {
                    e.preventDefault();
                    if (options.length) {
                        options[
                            Math.max(current - 1, 0)
                        ].focus();
                    }
                } else if (e.key === "Home") {
                    e.preventDefault();
                    if (options.length) {
                        options[0].focus();
                    }
                } else if (e.key === "End") {
                    e.preventDefault();
                    if (options.length) {
                        options[
                            options.length - 1
                        ].focus();
                    }
                } else if (e.key === "Escape") {
                    e.preventDefault();
                    closeIconDropdown();
                    if (iconDropdownTrigger) {
                        iconDropdownTrigger.focus();
                    }
                }
            }
        );
        updateCustomIconDropdown();
        initIcons();
    }

    function updateIconPreview() {
        if (!editIconPreview || !editIconSelect) {
            return;
        }
        var iconName = editIconSelect.value || "file";
        editIconPreview.innerHTML = '<i data-lucide="' + iconName + '"></i>';
        initIcons();
        updateCustomIconDropdown();
    }

    function updateCustomIconDropdown() {
        if (!iconDropdown || !editIconSelect) {
            return;
        }
        var iconName = editIconSelect.value || "file";
        var label = getIconLabel(iconName);
        var triggerIcon = iconDropdown.querySelector(".permission-icon-dropdown__trigger-icon");
        if (triggerIcon) {
            triggerIcon.innerHTML = '<i data-lucide="' + iconName +'"></i>';
        }
        var triggerLabel = iconDropdown.querySelector(".permission-icon-dropdown__label");
        if (triggerLabel) {
            triggerLabel.textContent = label;
        }

        iconDropdown.querySelectorAll(".permission-icon-dropdown__option").forEach(function (item) {
            var selected = item.dataset.value === iconName;
            item.classList.toggle("is-selected", selected);
            item.setAttribute("aria-selected", selected ? "true" : "false");
        });
        initIcons();
    }

    function setIconValue(value, fireChange) {
        if (!editIconSelect) {
            return;
        }
        editIconSelect.value = value || "file";
        updateIconPreview();
        if (fireChange) {
            editIconSelect.dispatchEvent(new Event("change",
                    {
                        bubbles: true
                    }
                )
            );
        }
    }

    function openIconDropdown() {
        if (!iconDropdown) {
            return;
        }
        iconDropdown.classList.add("is-open");
        if (iconDropdownTrigger) {
            iconDropdownTrigger.setAttribute("aria-expanded", "true");
        }
    }

    function closeIconDropdown() {
        if (!iconDropdown) {
            return;
        }
        iconDropdown.classList.remove("is-open");
        if (iconDropdownTrigger) {
            iconDropdownTrigger.setAttribute("aria-expanded", "false");
        }
    }

    function toggleIconDropdown() {
        if (!iconDropdown) {
            return;
        }

        if (iconDropdown.classList.contains("is-open")) {
            closeIconDropdown();
        } else {
            openIconDropdown();
        }
    }

    function focusSelectedIconOption() {
        if (!iconDropdownMenu || !editIconSelect) {
            return;
        }
        var selected = null;
        try {
            selected = iconDropdownMenu.querySelector('.permission-icon-dropdown__option[data-value="' + CSS.escape(editIconSelect.value) + '"]');
        } catch (error) {
            var options = iconDropdownMenu.querySelectorAll(".permission-icon-dropdown__option");
            for (var i = 0; i < options.length; i++) {
                if (options[i].dataset.value === editIconSelect.value) {
                    selected = options[i];
                    break;
                }
            }
        }

        if (selected) {
            selected.focus();
            selected.scrollIntoView({
                block: "nearest"
            });
        }
    }
    renderCustomIconDropdown();

    if (editIconSelect) {
        editIconSelect.addEventListener("change",
            updateIconPreview
        );
    }

    document.addEventListener("click", function (e) {
            if (iconDropdown &&!iconDropdown.contains(e.target)) {
                closeIconDropdown();
            }
        }
    );

    document.querySelectorAll("[data-edit-page]").forEach(function (btn) {
            btn.addEventListener("click", function () {
                    currentEditPk = btn.dataset.pk;
                    var nameInput = document.getElementById("editName");
                    if (nameInput) {
                        nameInput.value = btn.dataset.name || "";
                    }

                    if (editIconSelect) {
                        editIconSelect.value = btn.dataset.icon || "file";
                    }
                    updateIconPreview();
                    closeIconDropdown();

                    if (editModal) {
                        editModal.hidden = false;
                    }
                }
            );
        });

    function closeEditModal() {
        if (editModal) {
            editModal.hidden = true;
        }
        currentEditPk = null;
        closeIconDropdown();
    }

    var editClose = document.getElementById("editPageClose");
    var editCancel = document.getElementById("editPageCancel");
    if (editClose) {
        editClose.addEventListener("click", closeEditModal);
    }

    if (editCancel) {
        editCancel.addEventListener("click", closeEditModal);
    }

    if (editModal) {
        editModal.addEventListener("click", function (e) {
            if (e.target === editModal) {
                closeEditModal();
            }
        });
    }

    var editSave = document.getElementById("editPageSave");
    if (editSave) {
        editSave.addEventListener("click", function () {
            if (!currentEditPk) {
                return;
            }

            var csrfInput = document.querySelector("[name=csrfmiddlewaretoken]");
            fetch(window.PA_UPDATE_URL_BASE + currentEditPk + "/update/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfInput ? csrfInput.value : "",
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    display_name: document.getElementById("editName").value,
                    icon: editIconSelect ? editIconSelect.value : ""
                })

            }).then(function (res) {
                return res.json();
            }).then(function () {
                closeEditModal();
                window.location.reload();
            }).catch(function () {
                console.error("Update failed. Could not save changes. Try again.");
            });
        });
    }
});