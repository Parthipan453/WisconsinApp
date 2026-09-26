// ======================================================
// GLOBAL VARIABLES
// ======================================================

let sportChoice = null;
let statusChoice = null;
let categoryChoice = null;

let editClubStatusChoice = null;
let editClubSportChoice = null;

// ======================================================
// SINGLE GLOBAL CHOICES MAP
// ======================================================

window.choicesInstances = window.choicesInstances || {};
window.choicesMap = window.choicesInstances;


// ======================================================
// SAFE CHOICES INITIALIZATION
// ======================================================

function initializeChoices() {

  document
    .querySelectorAll("select.form-select, select.df-select")
    .forEach(function (select) {

      if (!select.id) return;

      // ------------------------------------------------
      // DO NOT INITIALIZE SAME SELECT TWICE
      // ------------------------------------------------

      if (window.choicesInstances[select.id]) {
        return;
      }

      // ------------------------------------------------
      // EXTRA SAFETY:
      // Choices adds this attribute after initialization
      // ------------------------------------------------

      if (select.dataset.choicesInitialized === "true") {
        return;
      }

      try {

        const instance = new Choices(select, {
          searchEnabled: true,
          shouldSort: false,
          itemSelectText: "",
          allowHTML: false,
        });

        window.choicesInstances[select.id] = instance;

        select.dataset.choicesInitialized = "true";

      } catch (error) {

        console.error(
          "Choices initialization error for:",
          select.id,
          error
        );

      }

    });


  // ==================================================
  // ASSIGN FILTER INSTANCES
  // ==================================================

  sportChoice =
    window.choicesInstances["clubSportFilter"] || null;

  statusChoice =
    window.choicesInstances["clubStatusFilter"] || null;

  categoryChoice =
    window.choicesInstances["clubCategoryFilter"] || null;

  editClubStatusChoice =
    window.choicesInstances["editclubstatus"] || null;

  editClubSportChoice =
    window.choicesInstances["editclubsport"] || null;
}


// ======================================================
// SAFE RESET CHOICES
// ======================================================

function resetChoices(instance, selectElement) {

  if (!selectElement) return;

  try {

    // --------------------------------------------------
    // Use the stored instance only
    // --------------------------------------------------

    if (instance) {

      instance.removeActiveItems();

      // Find empty option
      const emptyOption = Array.from(
        selectElement.options
      ).find(function (option) {

        return option.value === "";

      });


      // ------------------------------------------------
      // Select empty option if it exists
      // ------------------------------------------------

      if (emptyOption) {

        instance.setChoiceByValue("");

      } else {

        // If there is no empty option,
        // clear the native select safely

        selectElement.selectedIndex = 0;

      }

    } else {

      // ------------------------------------------------
      // NORMAL SELECT FALLBACK
      // ------------------------------------------------

      selectElement.value = "";

    }


  } catch (error) {

    console.error(
      "Choices reset error:",
      selectElement.id,
      error
    );

    // Fallback

    selectElement.value = "";

  }

}


// ======================================================
// CAROUSEL HERO
// ======================================================

document.addEventListener("DOMContentLoaded", function () {

  const slides =
    document.querySelectorAll(".club-slide");

  let current = 0;

  if (slides.length > 1) {

    setInterval(function () {

      slides[current].classList.remove("active");

      current =
        (current + 1) % slides.length;

      slides[current].classList.add("active");

    }, 4000);

  }

});


// ======================================================
// MAIN PAGE INITIALIZATION
// ======================================================

document.addEventListener("DOMContentLoaded", function () {


  // ==================================================
  // INITIALIZE CHOICES ONLY ONCE
  // ==================================================

  initializeChoices();


  // ==================================================
  // LUCIDE
  // ==================================================

  if (
    window.lucide &&
    typeof window.lucide.createIcons === "function"
  ) {

    window.lucide.createIcons();

  }


  // ==================================================
  // AOS
  // ==================================================

  if (
    window.AOS &&
    typeof window.AOS.init === "function"
  ) {

    window.AOS.init({
      once: true,
      offset: 40,
    });

  }


  // ==================================================
  // CARD ACTIONS
  // ==================================================

  document
    .querySelectorAll(".club-menu-btn")
    .forEach(function (btn) {

      btn.addEventListener(
        "click",
        function (e) {

          e.stopPropagation();

          document
            .querySelectorAll(".club-dropdown-menu")
            .forEach(function (menu) {

              if (
                menu !==
                btn.nextElementSibling
              ) {

                menu.classList.remove("show");

              }

            });


          if (btn.nextElementSibling) {

            btn
              .nextElementSibling
              .classList.toggle("show");

          }

        }
      );

    });


  // ==================================================
  // CLOSE DROPDOWNS
  // ==================================================

  document.addEventListener(
    "click",
    function () {

      document
        .querySelectorAll(".club-dropdown-menu")
        .forEach(function (menu) {

          menu.classList.remove("show");

        });

    }
  );


  // ==================================================
  // PAGINATION VARIABLES
  // ==================================================

  const grid =
    document.getElementById("clubGrid");

  const prevBtn =
    document.getElementById("clubPrevPage");

  const nextBtn =
    document.getElementById("clubNextPage");

  const pageNumbers =
    document.getElementById("clubPageNumbers");

  const cardsPerPage = 4;

  let currentPage = 1;


  // ==================================================
  // FILTER VARIABLES
  // ==================================================

  const filterForm =
    document.getElementById("clubFilterForm");

  const searchInput =
    document.getElementById("clubSearchInput");

  const categoryFilter =
    document.getElementById("clubCategoryFilter");

  const sportFilter =
    document.getElementById("clubSportFilter");

  const statusFilter =
    document.getElementById("clubStatusFilter");

  const resetBtn =
    document.getElementById("clubResetBtn");

  const cards =
    [
      ...document.querySelectorAll(".club-card")
    ];

  let filteredCards =
    [...cards];

  const emptyState =
    document.getElementById("clubEmptyState");


  // ==================================================
  // RENDER PAGINATION
  // ==================================================

  function renderPagination() {

    if (!pageNumbers) return;

    const totalPages =
      Math.ceil(
        filteredCards.length /
        cardsPerPage
      ) || 1;


    pageNumbers.innerHTML = "";


    for (
      let i = 1;
      i <= totalPages;
      i++
    ) {

      const btn =
        document.createElement("button");

      btn.className =
        "club-page-btn";

      btn.type =
        "button";

      btn.textContent =
        i;


      if (i === currentPage) {

        btn.classList.add("active");

      }


      btn.addEventListener(
        "click",
        function () {

          currentPage = i;

          showPage();

        }
      );


      pageNumbers.appendChild(btn);

    }


    if (prevBtn) {

      prevBtn.disabled =
        currentPage === 1;

    }


    if (nextBtn) {

      nextBtn.disabled =
        currentPage === totalPages;

    }

  }


  // ==================================================
  // SHOW CURRENT PAGE
  // ==================================================

  function showPage() {

    cards.forEach(function (card) {

      card.style.display = "none";

    });


    const start =
      (currentPage - 1) *
      cardsPerPage;

    const end =
      start +
      cardsPerPage;


    filteredCards
      .slice(start, end)
      .forEach(function (card) {

        card.style.display = "flex";

      });


    renderPagination();

  }


  // ==================================================
  // FILTER CARDS
  // ==================================================

  function filterCards() {

    const search =
      searchInput
        ? searchInput.value
            .toLowerCase()
            .trim()
        : "";


    const category =
      categoryFilter
        ? categoryFilter.value
            .toLowerCase()
        : "";


    const sport =
      sportFilter
        ? sportFilter.value
            .toLowerCase()
        : "";


    const status =
      statusFilter
        ? statusFilter.value
            .toLowerCase()
        : "";


    filteredCards =
      cards.filter(function (card) {

        const name =
          (
            card.dataset.name ||
            ""
          ).toLowerCase();


        const cardCategory =
          (
            card.dataset.category ||
            ""
          ).toLowerCase();


        const cardSport =
          (
            card.dataset.sport ||
            ""
          ).toLowerCase();


        const cardStatus =
          (
            card.dataset.status ||
            ""
          ).toLowerCase();


        return (
          (
            search === "" ||
            name.includes(search)
          ) &&

          (
            category === "" ||
            cardCategory === category
          ) &&

          (
            sport === "" ||
            cardSport === sport
          ) &&

          (
            status === "" ||
            cardStatus === status
          )
        );

      });


    currentPage = 1;


    if (emptyState) {

      emptyState.hidden =
        filteredCards.length !== 0;

    }


    showPage();

  }


  // ==================================================
  // FILTER FORM SUBMIT
  // ==================================================

  if (filterForm) {

    filterForm.addEventListener(
      "submit",
      function (e) {

        e.preventDefault();

        filterCards();

      }
    );

  }


  // ==================================================
  // LIVE SEARCH
  // ==================================================

  if (searchInput) {

    searchInput.addEventListener(
      "input",
      function () {

        filterCards();

      }
    );

  }


  // ==================================================
  // CATEGORY CHANGE
  // ==================================================

  if (categoryFilter) {

    categoryFilter.addEventListener(
      "change",
      function () {

        filterCards();

      }
    );

  }


  // ==================================================
  // SPORT CHANGE
  // ==================================================

  if (sportFilter) {

    sportFilter.addEventListener(
      "change",
      function () {

        filterCards();

      }
    );

  }


  // ==================================================
  // STATUS CHANGE
  // ==================================================

  if (statusFilter) {

    statusFilter.addEventListener(
      "change",
      function () {

        filterCards();

      }
    );

  }


  // ==================================================
  // RESET FILTERS
  // ==================================================

  if (resetBtn) {

    resetBtn.addEventListener(
      "click",
      function (e) {

        e.preventDefault();

        e.stopPropagation();


        console.log(
          "RESET STARTED"
        );


        // ----------------------------------------------
        // RESET SEARCH
        // ----------------------------------------------

        if (searchInput) {

          searchInput.value = "";

        }


        // ----------------------------------------------
        // RESET NATIVE FORM
        // ----------------------------------------------

        if (filterForm) {

          filterForm.reset();

        }


        // ----------------------------------------------
        // GET FRESH INSTANCES
        // ----------------------------------------------

        const currentCategoryChoice =
          window.choicesInstances[
            "clubCategoryFilter"
          ] || null;


        const currentSportChoice =
          window.choicesInstances[
            "clubSportFilter"
          ] || null;


        const currentStatusChoice =
          window.choicesInstances[
            "clubStatusFilter"
          ] || null;


        // ----------------------------------------------
        // RESET CHOICES
        // ----------------------------------------------

        resetChoices(
          currentCategoryChoice,
          categoryFilter
        );


        resetChoices(
          currentSportChoice,
          sportFilter
        );


        resetChoices(
          currentStatusChoice,
          statusFilter
        );


        // ----------------------------------------------
        // UPDATE GLOBAL VARIABLES
        // ----------------------------------------------

        categoryChoice =
          currentCategoryChoice;

        sportChoice =
          currentSportChoice;

        statusChoice =
          currentStatusChoice;


        // ----------------------------------------------
        // ENSURE NATIVE SELECT VALUES
        // ----------------------------------------------

        if (categoryFilter) {

          categoryFilter.value = "";

        }


        if (sportFilter) {

          sportFilter.value = "";

        }


        if (statusFilter) {

          statusFilter.value = "";

        }


        // ----------------------------------------------
        // RESTORE ALL CARDS
        // ----------------------------------------------

        filteredCards =
          [...cards];


        // ----------------------------------------------
        // RESET PAGE
        // ----------------------------------------------

        currentPage = 1;


        // ----------------------------------------------
        // HIDE EMPTY STATE
        // ----------------------------------------------

        if (emptyState) {

          emptyState.hidden = true;

        }


        // ----------------------------------------------
        // CLOSE DROPDOWNS
        // ----------------------------------------------

        document
          .querySelectorAll(
            ".club-dropdown-menu"
          )
          .forEach(function (menu) {

            menu.classList.remove("show");

          });


        // ----------------------------------------------
        // SHOW FIRST PAGE
        // ----------------------------------------------

        showPage();


        console.log(
          "RESET COMPLETED"
        );

      }
    );

  }


  // ==================================================
  // PREVIOUS PAGE
  // ==================================================

  if (prevBtn) {

    prevBtn.addEventListener(
      "click",
      function () {

        if (currentPage > 1) {

          currentPage--;

          showPage();

        }

      }
    );

  }


  // ==================================================
  // NEXT PAGE
  // ==================================================

  if (nextBtn) {

    nextBtn.addEventListener(
      "click",
      function () {

        const totalPages =
          Math.ceil(
            filteredCards.length /
            cardsPerPage
          );


        if (
          currentPage <
          totalPages
        ) {

          currentPage++;

          showPage();

        }

      }
    );

  }


  // ==================================================
  // INITIAL PAGINATION
  // ==================================================

  showPage();


  // ==================================================
  // CLUB FORM VALIDATION
  // ==================================================

  const clubForm =
    document.getElementById("clubForm");


  if (clubForm) {

    const clubName =
      document.getElementById(
        "club_name"
      );

    const description =
      document.getElementById(
        "description"
      );

    const logo =
      document.getElementById(
        "logo"
      );

    const image =
      document.getElementById(
        "image"
      );

    const sport =
      document.getElementById(
        "addclubsport"
      );

    const status =
      document.getElementById(
        "addclubstatus"
      );


    const allowedTypes = [
      "image/jpeg",
      "image/png",
      "image/webp",
    ];


    // ================================================
    // SPORT VALIDATION
    // ================================================

    if (sport) {

      sport.addEventListener(
        "change",
        function () {

          if (this.value === "") {

            showError(
              this,
              "Please select a sport."
            );

          } else {

            clearFieldError(this);

          }

        }
      );

    }


    // ================================================
    // STATUS VALIDATION
    // ================================================

    if (status) {

      status.addEventListener(
        "change",
        function () {

          if (this.value === "") {

            showError(
              this,
              "Please select a status."
            );

          } else {

            clearFieldError(this);

          }

        }
      );

    }


    // ================================================
    // CLUB NAME VALIDATION
    // ================================================

    if (clubName) {

      clubName.addEventListener(
        "input",
        function () {

          const value =
            this.value.trim();


          if (value === "") {

            showError(
              this,
              "Club name is required."
            );

          } else if (
            !/^[A-Za-z ]+$/.test(value)
          ) {

            showError(
              this,
              "Only letters and spaces are allowed."
            );

          } else if (
            value.length < 3
          ) {

            showError(
              this,
              "Minimum 3 characters required."
            );

          } else if (
            value.length > 20
          ) {

            showError(
              this,
              "Maximum 20 characters allowed."
            );

          } else {

            clearFieldError(this);

          }

        }
      );

    }


    // ================================================
    // DESCRIPTION VALIDATION
    // ================================================

    if (description) {

      description.addEventListener(
        "input",
        function () {

          if (
            this.value.length > 100
          ) {

            showError(
              this,
              "Maximum 100 characters allowed."
            );

          } else {

            clearFieldError(this);

          }

        }
      );

    }


    // ================================================
    // LOGO VALIDATION
    // ================================================

    if (logo) {

      logo.addEventListener(
        "change",
        function () {

          if (
            this.files.length === 0
          ) {

            clearFieldError(this);

            return;

          }


          if (
            !allowedTypes.includes(
              this.files[0].type
            )
          ) {

            showError(
              this,
              "Only JPG, JPEG, PNG and WEBP images are allowed."
            );

          } else {

            clearFieldError(this);

          }

        }
      );

    }


    // ================================================
    // IMAGE VALIDATION
    // ================================================

    if (image) {

      image.addEventListener(
        "change",
        function () {

          if (
            this.files.length === 0
          ) {

            showError(
              this,
              "Cover image is required."
            );

            return;

          }


          if (
            !allowedTypes.includes(
              this.files[0].type
            )
          ) {

            showError(
              this,
              "Only JPG, JPEG, PNG and WEBP images are allowed."
            );

          } else {

            clearFieldError(this);

          }

        }
      );

    }


    // ================================================
    // ADD CLUB SUBMIT
    // ================================================

    clubForm.addEventListener(
      "submit",
      function (e) {

        e.preventDefault();

        let valid = true;

        clearErrors();


        const name =
          clubName
            ? clubName.value.trim()
            : "";


        if (
          clubName &&
          name === ""
        ) {

          showError(
            clubName,
            "Club name is required."
          );

          valid = false;

        } else if (
          clubName &&
          !/^[A-Za-z ]+$/.test(name)
        ) {

          showError(
            clubName,
            "Only letters and spaces are allowed."
          );

          valid = false;

        } else if (
          clubName &&
          name.length < 3
        ) {

          showError(
            clubName,
            "Minimum 3 characters required."
          );

          valid = false;

        } else if (
          clubName &&
          name.length > 20
        ) {

          showError(
            clubName,
            "Maximum 20 characters allowed."
          );

          valid = false;

        }


        if (
          description &&
          description.value.length > 200
        ) {

          showError(
            description,
            "Maximum 200 characters allowed."
          );

          valid = false;

        }


        if (
          logo &&
          logo.files.length > 0 &&
          !allowedTypes.includes(
            logo.files[0].type
          )
        ) {

          showError(
            logo,
            "Only JPG, JPEG, PNG and WEBP images are allowed."
          );

          valid = false;

        }


        if (
          image &&
          image.files.length === 0
        ) {

          showError(
            image,
            "Cover image is required."
          );

          valid = false;

        } else if (
          image &&
          image.files.length > 0 &&
          !allowedTypes.includes(
            image.files[0].type
          )
        ) {

          showError(
            image,
            "Only JPG, JPEG, PNG and WEBP images are allowed."
          );

          valid = false;

        }


        if (
          sport &&
          sport.value === ""
        ) {

          showError(
            sport,
            "Please select a sport."
          );

          valid = false;

        }


        if (
          status &&
          status.value === ""
        ) {

          showError(
            status,
            "Please select a status."
          );

          valid = false;

        }


        if (!valid) return;


        const formData =
          new FormData(clubForm);


        fetch(
          clubForm.action,
          {
            method: "POST",

            headers: {
              "X-CSRFToken":
                document.querySelector(
                  "[name=csrfmiddlewaretoken]"
                ).value,

              "X-Requested-With":
                "XMLHttpRequest",
            },

            body: formData,
          }
        )

          .then(function (response) {

            return response.json();

          })

          .then(function (data) {

            if (data.success) {

              const modalElement =
                document.getElementById(
                  "addClubModal"
                );


              const modalInstance =
                bootstrap.Modal.getInstance(
                  modalElement
                );


              if (modalInstance) {

                modalInstance.hide();

              }


              clubForm.reset();

              location.reload();

            } else {

              if (clubName) {

                clubName.focus();

                showError(
                  clubName,
                  data.message
                );

              }

            }

          })

          .catch(function (error) {

            console.error(
              "Error:",
              error
            );

          });

      }
    );


    // ================================================
    // ADD CLUB MODAL RESET
    // ================================================

    const clubCancelBtn =
      document.getElementById(
        "clubCancelBtn"
      );

    const clubCloseBtn =
      document.getElementById(
        "clubCloseBtn"
      );


    function resetClubForm() {

      clubForm.reset();

      clearErrors();

    }


    if (clubCancelBtn) {

      clubCancelBtn.addEventListener(
        "click",
        resetClubForm
      );

    }


    if (clubCloseBtn) {

      clubCloseBtn.addEventListener(
        "click",
        resetClubForm
      );

    }

  }


  // ==================================================
  // EDIT CLUB
  // ==================================================

  const editModalEl =
    document.getElementById(
      "editClubModal"
    );

  const editForm =
    document.getElementById(
      "editClubForm"
    );


  // ==================================================
  // EDIT BUTTON
  // ==================================================

  document
    .querySelectorAll(".edit-btn")
    .forEach(function (btn) {

      btn.addEventListener(
        "click",
        function () {

          if (!editForm) return;


          editForm.action =
            this.dataset.url;


          const editName =
            editForm.querySelector(
              "[name='club_name']"
            );


          const editDescription =
            editForm.querySelector(
              "[name='description']"
            );


          if (editName) {

            editName.value =
              this.dataset.name || "";

          }


          if (editDescription) {

            editDescription.value =
              this.dataset.description || "";

          }


          // Get fresh instances

          const currentEditSport =
            window.choicesInstances[
              "editclubsport"
            ] || null;


          const currentEditStatus =
            window.choicesInstances[
              "editclubstatus"
            ] || null;


          if (
            currentEditSport &&
            this.dataset.sport
          ) {

            currentEditSport.setChoiceByValue(
              this.dataset.sport
            );

          }


          if (
            currentEditStatus &&
            this.dataset.status
          ) {

            currentEditStatus.setChoiceByValue(
              this.dataset.status
            );

          }

        }
      );

    });


  // ==================================================
  // EDIT MODAL EVENTS
  // ==================================================

  if (editModalEl) {

    editModalEl.addEventListener(
      "shown.bs.modal",
      function () {

        if (
          window.lucide &&
          typeof window.lucide.createIcons ===
            "function"
        ) {

          window.lucide.createIcons();

        }

      }
    );


    editModalEl.addEventListener(
      "show.bs.modal",
      function () {

        if (!editForm) return;


        editForm
          .querySelectorAll(".is-invalid")
          .forEach(function (field) {

            field.classList.remove(
              "is-invalid"
            );

          });


        editForm
          .querySelectorAll(
            ".invalid-feedback"
          )
          .forEach(function (msg) {

            msg.textContent = "";

          });

      }
    );

  }


  // ==================================================
  // EDIT FORM VALIDATION
  // ==================================================

  if (editForm) {

    const editClubName =
      editForm.querySelector(
        "[name='club_name']"
      );

    const editDescription =
      editForm.querySelector(
        "[name='description']"
      );

    const editLogo =
      editForm.querySelector(
        "[name='logo']"
      );

    const editImage =
      editForm.querySelector(
        "[name='image']"
      );


    const allowedTypes = [
      "image/jpeg",
      "image/png",
      "image/webp",
    ];


    // ================================================
    // EDIT NAME
    // ================================================

    if (editClubName) {

      editClubName.addEventListener(
        "input",
        function () {

          const value =
            this.value.trim();


          if (value === "") {

            showError(
              this,
              "Club name is required."
            );

          } else if (
            !/^[A-Za-z ]+$/.test(value)
          ) {

            showError(
              this,
              "Only letters and spaces are allowed."
            );

          } else if (
            value.length < 3
          ) {

            showError(
              this,
              "Minimum 3 characters required."
            );

          } else if (
            value.length > 20
          ) {

            showError(
              this,
              "Maximum 20 characters allowed."
            );

          } else {

            clearFieldError(this);

          }

        }
      );

    }


    // ================================================
    // EDIT DESCRIPTION
    // ================================================

    if (editDescription) {

      editDescription.addEventListener(
        "input",
        function () {

          if (
            this.value.length > 100
          ) {

            showError(
              this,
              "Maximum 100 characters allowed."
            );

          } else {

            clearFieldError(this);

          }

        }
      );

    }


    // ================================================
    // EDIT LOGO
    // ================================================

    if (editLogo) {

      editLogo.addEventListener(
        "change",
        function () {

          if (
            this.files.length === 0
          ) {

            clearFieldError(this);

            return;

          }


          if (
            !allowedTypes.includes(
              this.files[0].type
            )
          ) {

            showError(
              this,
              "Only JPG, JPEG, PNG and WEBP images are allowed."
            );

          } else {

            clearFieldError(this);

          }

        }
      );

    }


    // ================================================
    // EDIT IMAGE
    // ================================================

    if (editImage) {

      editImage.addEventListener(
        "change",
        function () {

          if (
            this.files.length === 0
          ) {

            clearFieldError(this);

            return;

          }


          if (
            !allowedTypes.includes(
              this.files[0].type
            )
          ) {

            showError(
              this,
              "Only JPG, JPEG, PNG and WEBP images are allowed."
            );

          } else {

            clearFieldError(this);

          }

        }
      );

    }


    // ================================================
    // EDIT SUBMIT
    // ================================================

    editForm.addEventListener(
      "submit",
      function (e) {

        e.preventDefault();

        let valid = true;

        clearErrors();


        const name =
          editClubName
            ? editClubName.value.trim()
            : "";


        if (
          editClubName &&
          name === ""
        ) {

          showError(
            editClubName,
            "Club name is required."
          );

          valid = false;

        } else if (
          editClubName &&
          !/^[A-Za-z ]+$/.test(name)
        ) {

          showError(
            editClubName,
            "Only letters and spaces are allowed."
          );

          valid = false;

        } else if (
          editClubName &&
          name.length < 3
        ) {

          showError(
            editClubName,
            "Minimum 3 characters required."
          );

          valid = false;

        } else if (
          editClubName &&
          name.length > 20
        ) {

          showError(
            editClubName,
            "Maximum 20 characters allowed."
          );

          valid = false;

        }


        if (
          editDescription &&
          editDescription.value.length > 100
        ) {

          showError(
            editDescription,
            "Maximum 100 characters allowed."
          );

          valid = false;

        }


        if (
          editLogo &&
          editLogo.files.length > 0 &&
          !allowedTypes.includes(
            editLogo.files[0].type
          )
        ) {

          showError(
            editLogo,
            "Only JPG, JPEG, PNG and WEBP images are allowed."
          );

          valid = false;

        }


        if (
          editImage &&
          editImage.files.length > 0 &&
          !allowedTypes.includes(
            editImage.files[0].type
          )
        ) {

          showError(
            editImage,
            "Only JPG, JPEG, PNG and WEBP images are allowed."
          );

          valid = false;

        }


        if (!valid) return;


        const formData =
          new FormData(editForm);


        fetch(
          editForm.action,
          {
            method: "POST",

            headers: {
              "X-CSRFToken":
                document.querySelector(
                  "[name=csrfmiddlewaretoken]"
                ).value,

              "X-Requested-With":
                "XMLHttpRequest",
            },

            body: formData,
          }
        )

          .then(function (response) {

            return response.json();

          })

          .then(function (data) {

            if (data.success) {

              const modalInstance =
                bootstrap.Modal.getInstance(
                  editModalEl
                );


              if (modalInstance) {

                modalInstance.hide();

              }


              location.reload();

            } else {

              if (editClubName) {

                showError(
                  editClubName,
                  data.message
                );

              }

            }

          })

          .catch(function (error) {

            console.error(
              "Error:",
              error
            );

          });

      }
    );

  }


});


// ======================================================
// ERROR FUNCTIONS
// ======================================================

function showError(input, message) {

  if (!input) return;


  input.classList.add(
    "is-invalid"
  );


  if (
    input.tagName === "SELECT"
  ) {

    const wrapper =
      input.closest(".mb-3");


    if (wrapper) {

      const error =
        wrapper.querySelector(
          ".invalid-feedback"
        );


      if (error) {

        error.textContent =
          message;

      }

    }


    const choice =
      window.choicesInstances
        ? window.choicesInstances[
            input.id
          ]
        : null;


    if (
      choice &&
      choice.containerOuter &&
      choice.containerOuter.element
    ) {

      choice.containerOuter.element.classList.add(
        "is-invalid"
      );

    }


    return;

  }


  const error =
    input.nextElementSibling;


  if (error) {

    error.textContent =
      message;

  }

}


// ======================================================
// CLEAR SINGLE FIELD ERROR
// ======================================================

function clearFieldError(input) {

  if (!input) return;


  input.classList.remove(
    "is-invalid"
  );


  if (
    input.tagName === "SELECT"
  ) {

    const wrapper =
      input.closest(".mb-3");


    if (wrapper) {

      const error =
        wrapper.querySelector(
          ".invalid-feedback"
        );


      if (error) {

        error.textContent = "";

      }

    }


    const choice =
      window.choicesInstances
        ? window.choicesInstances[
            input.id
          ]
        : null;


    if (
      choice &&
      choice.containerOuter &&
      choice.containerOuter.element
    ) {

      choice.containerOuter.element.classList.remove(
        "is-invalid"
      );

    }


    return;

  }


  const error =
    input.nextElementSibling;


  if (error) {

    error.textContent = "";

  }

}


// ======================================================
// CLEAR ALL ERRORS
// ======================================================

function clearErrors() {

  document
    .querySelectorAll(
      ".is-invalid"
    )
    .forEach(function (input) {

      input.classList.remove(
        "is-invalid"
      );

    });


  document
    .querySelectorAll(
      ".invalid-feedback"
    )
    .forEach(function (error) {

      error.textContent = "";

    });


  Object
    .values(
      window.choicesInstances || {}
    )
    .forEach(function (choice) {

      if (
        choice &&
        choice.containerOuter &&
        choice.containerOuter.element
      ) {

        choice.containerOuter.element.classList.remove(
          "is-invalid"
        );

      }

    });

}