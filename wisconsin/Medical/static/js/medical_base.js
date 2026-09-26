(function () {
  "use strict";

  const sidebar = document.getElementById("medSidebar");
  const hamburger = document.getElementById("medHamburger");

  function toggleSidebar() {
    if (window.innerWidth < 1000) {
      sidebar.classList.toggle("open");
      const isOpen = sidebar.classList.contains("open");
      hamburger.setAttribute("aria-expanded", isOpen);
    } else {
      document.body.classList.toggle("sidebar-collapsed");
      const isCollapsed = document.body.classList.contains("sidebar-collapsed");
      hamburger.setAttribute("aria-expanded", !isCollapsed);
    }
  }

  if (hamburger) {
    hamburger.addEventListener("click", toggleSidebar);
  }

  document.addEventListener("click", function (e) {
    const isSidebar = sidebar.contains(e.target);
    const isHamburger = hamburger ? hamburger.contains(e.target) : false;
    if (
      window.innerWidth < 1000 &&
      !isSidebar &&
      !isHamburger &&
      sidebar.classList.contains("open")
    ) {
      sidebar.classList.remove("open");
      if (hamburger) hamburger.setAttribute("aria-expanded", "false");
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && sidebar.classList.contains("open")) {
      sidebar.classList.remove("open");
      if (hamburger) hamburger.setAttribute("aria-expanded", "false");
    }
  });

  const parentItems = document.querySelectorAll(
    ".med-sidebar__item[data-target]",
  );

  parentItems.forEach((item) => {
    item.addEventListener("click", function () {
      if (
        window.innerWidth >= 1000 &&
        document.body.classList.contains("sidebar-collapsed")
      ) {
        document.body.classList.remove("sidebar-collapsed");
        hamburger?.setAttribute("aria-expanded", "true");
      }

      const targetId = this.dataset.target;
      const subMenu = document.getElementById(targetId);
      if (!subMenu) return;

      const chevron = this.querySelector(".chevron");
      const isOpen = subMenu.classList.contains("open");

      document.querySelectorAll(".med-sidebar__sub").forEach((sub) => {
        sub.classList.remove("open");

        const parent = document.querySelector(
          `.med-sidebar__item[data-target="${sub.id}"]`,
        );

        if (parent) {
          parent.classList.remove("active");
          parent.querySelector(".chevron")?.classList.remove("open");
        }
      });

      if (!isOpen) {
        subMenu.classList.add("open");
        this.classList.add("active");
        chevron?.classList.add("open");
      }
    });
  });

  document.querySelectorAll(".med-sidebar__sub").forEach((subMenu) => {
    if (subMenu.querySelector(".med-sidebar__sub-item.active")) {
      subMenu.classList.add("open");

      const parent = document.querySelector(
        `.med-sidebar__item[data-target="${subMenu.id}"]`,
      );

      if (parent) {
        parent.classList.add("active");
        parent.querySelector(".chevron")?.classList.add("open");
      }
    }
  });

  const searchContainer = document.getElementById("searchContainer");
  const searchInput = document.getElementById("searchInput");

  if (searchContainer && searchInput) {
    searchContainer.addEventListener("click", function (e) {
      if (!this.classList.contains("expanded")) {
        this.classList.add("expanded");
        searchInput.focus();
      }
    });

    searchInput.addEventListener("blur", function () {
      if (this.value === "") {
        searchContainer.classList.remove("expanded");
      }
    });

    searchInput.addEventListener("input", function () {
      if (
        this.value !== "" &&
        !searchContainer.classList.contains("expanded")
      ) {
        searchContainer.classList.add("expanded");
      }
    });

    searchInput.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        this.value = "";
        searchContainer.classList.remove("expanded");
        this.blur();
      }
      if (e.key === "Enter") {
        console.log("Search:", this.value);
      }
    });
  }

  const profileWrap = document.getElementById("profileWrap");
  const profileToggle = document.getElementById("profileToggle");
  const profileDropdown = document.getElementById("profileDropdown");

  function toggleDropdown(e) {
    e.stopPropagation();
    profileToggle.classList.toggle("active");
    profileDropdown.classList.toggle("open");
  }

  if (profileToggle) {
    profileToggle.addEventListener("click", toggleDropdown);
  }

  document.addEventListener("click", function (e) {
    if (profileWrap && !profileWrap.contains(e.target)) {
      profileToggle.classList.remove("active");
      profileDropdown.classList.remove("open");
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && profileDropdown.classList.contains("open")) {
      profileToggle.classList.remove("active");
      profileDropdown.classList.remove("open");
    }
  });

  document.querySelectorAll(".med-dropdown__item").forEach(function (item) {
    item.addEventListener("click", function () {
      profileToggle.classList.remove("active");
      profileDropdown.classList.remove("open");
    });
  });
})();
