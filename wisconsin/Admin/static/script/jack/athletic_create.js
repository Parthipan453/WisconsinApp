document.addEventListener("DOMContentLoaded", function () {
  AOS.init({ duration: 600, once: true, easing: "ease-out-cubic" });


  function initSingleSelect(
    selectId,
    displayInputId,
    searchInputId,
    optionsId,
    hiddenId,
    noResultsId,
  ) {
    const container = document.getElementById(selectId);
    const displayInput = document.getElementById(displayInputId);
    const searchInput = document.getElementById(searchInputId);
    const optionsContainer = document.getElementById(optionsId);
    const hiddenInput = document.getElementById(hiddenId);
    const noResults = document.getElementById(noResultsId);

    const options = optionsContainer.querySelectorAll(
      ".af-custom-select-option",
    );

    function filterOptions(searchText) {
      const query = searchText.toLowerCase().trim();
      let hasVisible = false;

      options.forEach((opt) => {
        const searchData = (
          opt.dataset.search || opt.textContent
        ).toLowerCase();
        const matches = searchData.includes(query);
        opt.classList.toggle("hidden", !matches);
        if (matches) hasVisible = true;
      });

      noResults.style.display = hasVisible ? "none" : "block";
    }

    function updateDisplayInput() {
      const selected = optionsContainer.querySelector(
        ".af-custom-select-option.selected",
      );
      if (selected) {
        displayInput.value = selected.textContent.trim();
        hiddenInput.value = selected.dataset.value;
      }
    }

    function openDropdown() {
      document.querySelectorAll(".af-custom-select.open").forEach((el) => {
        if (el !== container) el.classList.remove("open");
      });

      container.classList.add("open");
      searchInput.value = "";
      filterOptions("");
      setTimeout(() => searchInput.focus(), 100);
    }

    function closeDropdown() {
      container.classList.remove("open");
      updateDisplayInput();
    }

    displayInput.addEventListener("click", function (e) {
      e.stopPropagation();
      if (container.classList.contains("open")) {
        closeDropdown();
      } else {
        openDropdown();
      }
    });

    document.addEventListener("click", function (e) {
      if (!container.contains(e.target)) {
        closeDropdown();
      }
    });

    searchInput.addEventListener("input", function () {
      filterOptions(this.value);
    });

    searchInput.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        closeDropdown();
        return;
      }

      if (e.key === "Enter") {
        const visibleOptions = optionsContainer.querySelectorAll(
          ".af-custom-select-option:not(.hidden)",
        );
        if (visibleOptions.length > 0) {
          selectOption(visibleOptions[0]);
          closeDropdown();
        }
        e.preventDefault();
      }

      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        const visibleOptions = optionsContainer.querySelectorAll(
          ".af-custom-select-option:not(.hidden)",
        );
        if (visibleOptions.length === 0) return;

        let currentIndex = -1;
        visibleOptions.forEach((opt, index) => {
          if (opt.classList.contains("highlighted")) {
            currentIndex = index;
            opt.classList.remove("highlighted");
          }
        });

        let newIndex;
        if (e.key === "ArrowDown") {
          newIndex =
            currentIndex < visibleOptions.length - 1 ? currentIndex + 1 : 0;
        } else {
          newIndex =
            currentIndex > 0 ? currentIndex - 1 : visibleOptions.length - 1;
        }

        visibleOptions[newIndex].classList.add("highlighted");
        visibleOptions[newIndex].scrollIntoView({ block: "nearest" });
      }
    });

    function selectOption(option) {
      optionsContainer
        .querySelectorAll(".af-custom-select-option")
        .forEach((opt) => {
          opt.classList.remove("selected");
        });
      option.classList.add("selected");
      hiddenInput.value = option.dataset.value;
      displayInput.value = option.textContent.trim();
      hiddenInput.dispatchEvent(new Event("change"));
    }

    optionsContainer.addEventListener("click", function (e) {
      const option = e.target.closest(".af-custom-select-option");
      if (!option || option.classList.contains("hidden")) return;
      selectOption(option);
      closeDropdown();
    });

    optionsContainer.addEventListener("mouseenter", function () {
      optionsContainer
        .querySelectorAll(".af-custom-select-option.highlighted")
        .forEach((opt) => {
          opt.classList.remove("highlighted");
        });
    });

    return { filterOptions, updateDisplayInput, openDropdown, closeDropdown };
  }


  function initMultiSelect(
    selectId,
    searchInputId,
    optionsId,
    hiddenId,
    noResultsId,
  ) {
    const container = document.getElementById(selectId);
    const searchInput = document.getElementById(searchInputId);
    const optionsContainer = document.getElementById(optionsId);
    const hiddenInput = document.getElementById(hiddenId);
    const noResults = document.getElementById(noResultsId);

    const options = optionsContainer.querySelectorAll(
      ".af-custom-select-option",
    );

    function filterOptions(searchText) {
      const query = searchText.toLowerCase().trim();
      let hasVisible = false;

      options.forEach((opt) => {
        const searchData = (
          opt.dataset.search || opt.textContent
        ).toLowerCase();
        const matches = searchData.includes(query);
        opt.classList.toggle("hidden", !matches);
        if (matches) hasVisible = true;
      });

      noResults.style.display = hasVisible ? "none" : "block";
    }

    function openDropdown() {
      document.querySelectorAll(".af-custom-select.open").forEach((el) => {
        if (el !== container) el.classList.remove("open");
      });
      container.classList.add("open");
      filterOptions(searchInput.value);
      setTimeout(() => searchInput.focus(), 100);
    }

    function closeDropdown() {
      container.classList.remove("open");
    }

    searchInput.addEventListener("click", function (e) {
      e.stopPropagation();
      if (container.classList.contains("open")) {
        closeDropdown();
      } else {
        openDropdown();
      }
    });

    document.addEventListener("click", function (e) {
      if (!container.contains(e.target)) {
        closeDropdown();
      }
    });

    searchInput.addEventListener("input", function () {
      if (container.classList.contains("open")) {
        filterOptions(this.value);
      }
    });

    searchInput.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        closeDropdown();
        return;
      }

      if (e.key === "Enter" && container.classList.contains("open")) {
        const visibleOptions = optionsContainer.querySelectorAll(
          ".af-custom-select-option:not(.hidden)",
        );
        if (visibleOptions.length > 0) {
          visibleOptions[0].classList.toggle("selected");
          updateSelectedSports();
        }
        e.preventDefault();
      }
    });

    function updateSelectedSports() {
      const selectedOptions = optionsContainer.querySelectorAll(
        ".af-custom-select-option.selected",
      );
      const selectedIds = [];
      const selectedNames = [];

      selectedOptions.forEach((opt) => {
        selectedIds.push(opt.dataset.value);
        selectedNames.push(opt.textContent.trim());
      });

      hiddenInput.value = selectedIds.join(",");

      const tagsContainer = document.getElementById("selectedSportsTags");
      tagsContainer.innerHTML = "";

      if (selectedNames.length === 0) {
        tagsContainer.innerHTML =
          '<span class="af-tag-placeholder">No sports selected</span>';
      } else {
        selectedNames.forEach((name, index) => {
          const tag = document.createElement("span");
          tag.className = "af-tag";
          tag.dataset.id = selectedIds[index];
          tag.innerHTML = `
                            ${name}
                            <span class="af-tag-remove" onclick="removeSport('${selectedIds[index]}')">
                                <i class="ti ti-x"></i>
                            </span>
                        `;
          tagsContainer.appendChild(tag);
        });
      }

      hiddenInput.dispatchEvent(new Event("change"));
    }

    optionsContainer.addEventListener("click", function (e) {
      const option = e.target.closest(".af-custom-select-option");
      if (!option || option.classList.contains("hidden")) return;
      option.classList.toggle("selected");
      updateSelectedSports();
      searchInput.focus();
    });

    function initializeFromHidden() {
      const initialValue = hiddenInput.value;
      if (initialValue) {
        const ids = initialValue.split(",").filter((id) => id.trim());
        options.forEach((opt) => {
          if (ids.includes(opt.dataset.value)) {
            opt.classList.add("selected");
          }
        });
        updateSelectedSports();
      }
    }

    setTimeout(initializeFromHidden, 100);

    return { filterOptions, updateSelectedSports, openDropdown, closeDropdown };
  }

  const studentDropdown = initSingleSelect(
    "studentSelect",
    "studentDisplayInput",
    "studentSearchInput",
    "studentOptions",
    "studentHidden",
    "studentNoResults",
  );

  const teamDropdown = initSingleSelect(
    "teamSelect",
    "teamDisplayInput",
    "teamSearchInput",
    "teamOptions",
    "teamHidden",
    "teamNoResults",
  );

  const sportDropdown = initMultiSelect(
    "sportSelect",
    "sportSearchInput",
    "sportOptions",
    "sportHidden",
    "sportNoResults",
  );


function initializeSelectedValues() {
    const studentHidden = document.getElementById('studentHidden');
    const studentDisplay = document.getElementById('studentDisplayInput');
    const studentOptions = document.querySelectorAll('#studentOptions .af-custom-select-option');
    
    if (studentHidden && studentHidden.value) {
        let found = false;
        studentOptions.forEach(opt => {
            if (opt.dataset.value === studentHidden.value) {
                opt.classList.add('selected');
                studentDisplay.value = opt.textContent.trim();
                found = true;
            }
        });
        if (!found) {
            studentDisplay.value = '';
        }
    } else {
        studentDisplay.value = '';
    }
    
    const teamHidden = document.getElementById('teamHidden');
    const teamDisplay = document.getElementById('teamDisplayInput');
    const teamOptions = document.querySelectorAll('#teamOptions .af-custom-select-option');
    
    if (teamHidden && teamHidden.value) {
        let found = false;
        teamOptions.forEach(opt => {
            if (opt.dataset.value === teamHidden.value) {
                opt.classList.add('selected');
                teamDisplay.value = opt.textContent.trim();
                found = true;
            }
        });
        if (!found) {
            teamOptions.forEach(opt => {
                if (opt.dataset.value === '') {
                    opt.classList.add('selected');
                    teamDisplay.value = 'None';
                }
            });
        }
    } else if (teamHidden) {
        teamOptions.forEach(opt => {
            if (opt.dataset.value === '') {
                opt.classList.add('selected');
                teamDisplay.value = 'None';
            }
        });
    }
    
    const classYearHidden = document.getElementById('classYearHidden');
    const classYearSelect = document.getElementById('id_class_year');
    
    if (classYearHidden && classYearHidden.value) {
        classYearSelect.value = classYearHidden.value;
        if (classYearHidden.value === 'FACULTY' || classYearHidden.value === 'STAFF') {
            classYearSelect.disabled = true;
        } else {
            classYearSelect.disabled = false;
        }
    } 
    else {
        const selectedOption = classYearSelect.querySelector('option[selected]');
        if (selectedOption && selectedOption.value) {
            classYearSelect.value = selectedOption.value;
            if (selectedOption.value === 'FACULTY' || selectedOption.value === 'STAFF') {
                classYearSelect.disabled = true;
            } else {
                classYearSelect.disabled = false;
            }
        }
    }
    
    updateClassYearVisibility();
}


function updateClassYearVisibility() {
    const selectedOption = document.querySelector('#studentOptions .af-custom-select-option.selected');
    const role = selectedOption ? selectedOption.dataset.role : '';
    const requiredStar = document.getElementById('classYearRequired');
    const optionalText = document.getElementById('classYearOptional');
    const helpText = document.getElementById('classYearHelpText');
    const classYearSelect = document.getElementById('id_class_year');
    const classYearHidden = document.getElementById('classYearHidden');
    
    const currentValue = classYearSelect.value;
    
    if (role === 'student') {
        requiredStar.style.display = 'inline';
        optionalText.style.display = 'none';
        helpText.textContent = 'Required for students. Auto-set for faculty/staff.';
        classYearSelect.required = true;
        classYearSelect.disabled = false;
        if (!currentValue || currentValue === 'FACULTY' || currentValue === 'STAFF') {
            const selectedStudentOption = classYearSelect.querySelector('option[selected]');
            if (selectedStudentOption && selectedStudentOption.value) {
                classYearSelect.value = selectedStudentOption.value;
            } else {
                if (classYearHidden && classYearHidden.value && 
                    classYearHidden.value !== 'FACULTY' && 
                    classYearHidden.value !== 'STAFF') {
                    classYearSelect.value = classYearHidden.value;
                } else {
                    classYearSelect.value = '';
                }
            }
        }
        if (classYearHidden) {
            classYearHidden.value = classYearSelect.value;
        }
    } else if (role === 'faculty') {
        requiredStar.style.display = 'none';
        optionalText.style.display = 'inline';
        helpText.textContent = 'Auto-set to "Faculty" for faculty members.';
        classYearSelect.required = false;
        classYearSelect.disabled = true;
        classYearSelect.value = 'FACULTY';
        if (classYearHidden) classYearHidden.value = 'FACULTY';
        classYearSelect.dispatchEvent(new Event('change'));
    } else if (role === 'staff') {
        requiredStar.style.display = 'none';
        optionalText.style.display = 'inline';
        helpText.textContent = 'Auto-set to "Staff" for staff members.';
        classYearSelect.required = false;
        classYearSelect.disabled = true;
        classYearSelect.value = 'STAFF';
        if (classYearHidden) classYearHidden.value = 'STAFF';
        classYearSelect.dispatchEvent(new Event('change'));
    } else {
        requiredStar.style.display = 'inline';
        optionalText.style.display = 'none';
        helpText.textContent = 'Please select an athlete first.';
        classYearSelect.required = true;
        classYearSelect.disabled = false;
        // Don't clear the value if it exists
        if (!classYearSelect.value) {
            classYearSelect.value = '';
            if (classYearHidden) classYearHidden.value = '';
        }
    }
}


document.getElementById('id_class_year').addEventListener('change', function() {
    const classYearHidden = document.getElementById('classYearHidden');
    if (classYearHidden) {
        classYearHidden.value = this.value;
    }
});


  window.removeSport = function (sportId) {
    const option = document.querySelector(
      `#sportOptions .af-custom-select-option[data-value="${sportId}"]`,
    );
    if (option) {
      option.classList.remove("selected");
      sportDropdown.updateSelectedSports();
    }
  };


  document
    .getElementById("studentHidden")
    .addEventListener("change", function () {
      updateClassYearVisibility();
      setTimeout(initializeSelectedValues, 100);
    });


  setTimeout(updateClassYearVisibility, 200);
  setTimeout(initializeSelectedValues, 300);

  window.addEventListener("load", function () {
    setTimeout(initializeSelectedValues, 500);
  });

  document.querySelectorAll('.ss-form-select').forEach(select => {
        new SlimSelect({
            select: select,
            settings: {
                placeholderText: select.options[0].text,
                showSearch: false
            }
        });
  });
});
