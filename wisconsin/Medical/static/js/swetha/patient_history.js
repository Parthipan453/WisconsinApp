//**************************************************** */ swetha's code************************************************************************

(function () {
  "use strict";

  const navigationEntry =
    performance.getEntriesByType("navigation")[0];

  if (
    navigationEntry &&
    navigationEntry.type === "reload"
  ) {
    const url = new URL(
      window.location.href
    );

    if (url.searchParams.has("page")) {
      url.searchParams.delete("page");
      url.searchParams.delete("ajax");

      window.location.replace(
        url.pathname + url.search
      );

      return;
    }
  }

  class PatientHistory {

    constructor() {

      this.filters = {
        search: "",
        visitType: "all",
        dateRange: "all",
        status: "all",
      };

      this.init();
    }

    init() {

      this.setupFilterDropdowns();
      this.setupSearch();
      this.setupViewLinks();
      this.setupCharts();
      this.applyFilters();
      this.setupPagination();

      console.log(
        "Patient history initialized"
      );
    }

    setupFilterDropdowns() {

      const filterChips =
        document.querySelectorAll(
          ".filter-chip"
        );

      if (!filterChips.length) {
        return;
      }

      filterChips.forEach((chip) => {

        const dropdown =
          chip.querySelector(
            ".filter-dropdown"
          );

        if (!dropdown) {
          return;
        }

        chip.addEventListener(
          "click",
          (event) => {

            event.stopPropagation();

            document
              .querySelectorAll(
                ".filter-dropdown.show"
              )
              .forEach(
                (openDropdown) => {

                  if (
                    openDropdown !==
                    dropdown
                  ) {
                    openDropdown.classList.remove(
                      "show"
                    );
                  }
                }
              );

            dropdown.classList.toggle(
              "show"
            );
          }
        );

        const items =
          dropdown.querySelectorAll(
            ".filter-dropdown-item"
          );

        items.forEach((item) => {

          item.addEventListener(
            "click",
            (event) => {

              event.stopPropagation();

              const value =
                item.dataset.value ||
                "all";

              const filterType =
                chip.dataset.filter;

              const label =
                item.textContent.trim();

              this.setFilterValue(
                filterType,
                value
              );

              this.updateFilterLabel(
                chip,
                label
              );

              dropdown.classList.remove(
                "show"
              );

              this.applyFilters();
            }
          );
        });
      });

      document.addEventListener(
        "click",
        () => {

          document
            .querySelectorAll(
              ".filter-dropdown.show"
            )
            .forEach((dropdown) => {

              dropdown.classList.remove(
                "show"
              );

            });
        }
      );
    }

    setFilterValue(
      filterType,
      value
    ) {

      switch (filterType) {

        case "visit_type":

          this.filters.visitType =
            value;

          break;

        case "date":

          this.filters.dateRange =
            value;

          break;

        case "status":

          this.filters.status =
            value;

          break;

        default:
          break;
      }
    }

    updateFilterLabel(
      chip,
      label
    ) {

      const filterType =
        chip.dataset.filter;

      const iconClass =
        this.getFilterIcon(
          filterType
        );

      const dropdown =
        chip.querySelector(
          ".filter-dropdown"
        );

      if (!dropdown) {
        return;
      }

      Array.from(
        chip.childNodes
      ).forEach((node) => {

        if (
          node.nodeType ===
          Node.TEXT_NODE
        ) {
          node.remove();
        }
      });

      let icon =
        chip.querySelector(
          ":scope > i"
        );

      if (!icon) {

        icon =
          document.createElement(
            "i"
          );

        chip.insertBefore(
          icon,
          dropdown
        );
      }

      icon.className =
        iconClass;

      const existingLabel =
        chip.querySelector(
          ":scope > .filter-label"
        );

      if (existingLabel) {
        existingLabel.remove();
      }

      const labelElement =
        document.createElement(
          "span"
        );

      labelElement.className =
        "filter-label";

      labelElement.textContent =
        `${label} ▾`;

      chip.insertBefore(
        labelElement,
        dropdown
      );
    }

    getFilterIcon(
      filterType
    ) {

      const icons = {

        visit_type:
          "fas fa-filter",

        date:
          "far fa-calendar-alt",

        status:
          "fas fa-circle",
      };

      return (
        icons[filterType] ||
        "fas fa-filter"
      );
    }

    setupSearch() {

      const searchInput =
        document.getElementById(
          "searchInput"
        );

      if (!searchInput) {
        return;
      }

      let timeoutId = null;

      searchInput.addEventListener(
        "input",
        (event) => {

          clearTimeout(
            timeoutId
          );

          timeoutId =
            setTimeout(() => {

              this.filters.search =
                event.target.value
                  .trim()
                  .toLowerCase();

              this.applyFilters();

            }, 200);
        }
      );
    }

    // applyFilters() {

    //   const tbody =
    //     document.getElementById(
    //       "patientTableBody"
    //     );

    //   if (!tbody) {
    //     return;
    //   }

    //   const rows =
    //     Array.from(
    //       tbody.querySelectorAll(
    //         "tr"
    //       )
    //     );

    //   let visibleCount = 0;

    //   rows.forEach((row) => {

    //     if (
    //       row.querySelector(
    //         ".empty-state"
    //       )
    //     ) {
    //       return;
    //     }

    //     let show = true;

    //     // Search
    //     if (this.filters.search) {

    //       const patientName =
    //         row
    //           .querySelector(
    //             ".patient-name"
    //           )
    //           ?.textContent
    //           ?.trim()
    //           ?.toLowerCase() ||
    //         "";

    //       const patientId =
    //         row
    //           .querySelector(
    //             ".patient-id"
    //           )
    //           ?.textContent
    //           ?.trim()
    //           ?.toLowerCase() ||
    //         "";

    //       if (
    //         !patientName.includes(
    //           this.filters.search
    //         ) &&
    //         !patientId.includes(
    //           this.filters.search
    //         )
    //       ) {
    //         show = false;
    //       }
    //     }

    //     // Status
    //     if (
    //       show &&
    //       this.filters.status !==
    //         "all"
    //     ) {

    //       const rowStatus =
    //         row.dataset.status ||
    //         "";

    //       if (
    //         rowStatus !==
    //         this.filters.status
    //       ) {
    //         show = false;
    //       }
    //     }

    //     if (
    //       show &&
    //       this.filters.visitType !==
    //         "all"
    //     ) {

    //       const visitType =
    //         this.getRowVisitType(
    //           row
    //         );

    //       if (
    //         visitType !==
    //         this.filters.visitType
    //       ) {
    //         show = false;
    //       }
    //     }

    //     // Date
    //     if (
    //       show &&
    //       this.filters.dateRange !==
    //         "all"
    //     ) {

    //       const lastVisit =
    //         this.getRowLastVisitDate(
    //           row
    //         );

    //       if (
    //         !this.matchesDateFilter(
    //           lastVisit,
    //           this.filters.dateRange
    //         )
    //       ) {
    //         show = false;
    //       }
    //     }

    //     row.style.display =
    //       show ? "" : "none";

    //     if (show) {
    //       visibleCount++;
    //     }
    //   });

    //   this.updateEmptyState(
    //     tbody,
    //     visibleCount
    //   );
    // }
    async applyFilters() {

    try {

        const url =
            new URL(
                window.location.href
            );

        // Filter apply ஆனதும் always first page
        url.searchParams.delete("page");

        // Send filters to Django
        url.searchParams.set(
            "search",
            this.filters.search || ""
        );

        url.searchParams.set(
            "visit_type",
            this.filters.visitType || "all"
        );

        url.searchParams.set(
            "date",
            this.filters.dateRange || "all"
        );

        url.searchParams.set(
            "status",
            this.filters.status || "all"
        );

        // AJAX
        url.searchParams.set(
            "ajax",
            "1"
        );

        const response =
            await fetch(
                url.toString(),
                {
                    headers: {
                        "X-Requested-With":
                            "XMLHttpRequest",
                    },
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

        // -----------------------------
        // Replace table
        // -----------------------------

        const currentBody =
            document.getElementById(
                "patientTableBody"
            );

        const newBody =
            doc.getElementById(
                "patientTableBody"
            );

        if (
            currentBody &&
            newBody
        ) {

            currentBody.innerHTML =
                newBody.innerHTML;
        }

        // -----------------------------
        // Replace pagination
        // -----------------------------

        const currentPagination =
            document.getElementById(
                "patientPagination"
            );

        const newPagination =
            doc.getElementById(
                "patientPagination"
            );

        if (
            currentPagination &&
            newPagination
        ) {

            currentPagination.innerHTML =
                newPagination.innerHTML;
        }

        // -----------------------------
        // Update URL
        // -----------------------------

        window.history.replaceState(
            {},
            "",
            url.toString()
        );

        // Re-bind view links
        this.setupViewLinks();

        console.log(
            "Filters applied:",
            this.filters
        );

    } catch (error) {

        console.error(
            "Filter error:",
            error
        );
    }
}

    getRowVisitType(row) {

      const cells =
        row.querySelectorAll(
          "td"
        );

      if (cells.length < 3) {
        return "";
      }

      const text =
        cells[2]
          ?.textContent
          ?.trim()
          ?.toLowerCase() ||
        "";

      if (
        text.includes("walk-in") ||
        text.includes("walk in")
      ) {
        return "walk_in";
      }

      if (
        text.includes(
          "appointment"
        )
      ) {
        return "appointment";
      }

      return "";
    }

    getRowLastVisitDate(row) {

      const cells =
        row.querySelectorAll(
          "td"
        );

      if (cells.length < 4) {
        return null;
      }

      const dateText =
        cells[3]
          ?.textContent
          ?.trim();

      if (!dateText) {
        return null;
      }

      return this.parseDate(
        dateText
      );
    }

    parseDate(dateString) {

      const parts =
        dateString.split(
          /\s+/
        );

      if (parts.length < 3) {
        return null;
      }

      const day =
        parseInt(
          parts[0],
          10
        );

      const monthMap = {

        jan: 0,
        feb: 1,
        mar: 2,
        apr: 3,
        may: 4,
        jun: 5,
        jul: 6,
        aug: 7,
        sep: 8,
        oct: 9,
        nov: 10,
        dec: 11,
      };

      const month =
        monthMap[
          parts[1]
            .substring(
              0,
              3
            )
            .toLowerCase()
        ];

      const year =
        parseInt(
          parts[2],
          10
        );

      if (
        Number.isNaN(day) ||
        month === undefined ||
        Number.isNaN(year)
      ) {
        return null;
      }

      return new Date(
        year,
        month,
        day
      );
    }

    matchesDateFilter(
      date,
      filter
    ) {

      if (!date) {
        return false;
      }

      const today =
        new Date();

      today.setHours(
        0,
        0,
        0,
        0
      );

      const target =
        new Date(date);

      target.setHours(
        0,
        0,
        0,
        0
      );

      if (
        filter === "today"
      ) {

        return (
          target.getTime() ===
          today.getTime()
        );
      }

      if (
        filter === "week"
      ) {

        const day =
          today.getDay();

        const diff =
          day === 0
            ? 6
            : day - 1;

        const weekStart =
          new Date(today);

        weekStart.setDate(
          today.getDate() -
            diff
        );

        const weekEnd =
          new Date(
            weekStart
          );

        weekEnd.setDate(
          weekStart.getDate() +
            6
        );

        return (
          target >= weekStart &&
          target <= weekEnd
        );
      }

      if (
        filter === "month"
      ) {

        return (
          target.getFullYear() ===
            today.getFullYear() &&
          target.getMonth() ===
            today.getMonth()
        );
      }

      return true;
    }

    updateEmptyState(
      tbody,
      visibleCount
    ) {

      let emptyRow =
        tbody.querySelector(
          ".js-filter-empty"
        );

      if (visibleCount === 0) {

        if (!emptyRow) {

          emptyRow =
            document.createElement(
              "tr"
            );

          emptyRow.className =
            "js-filter-empty";

          tbody.appendChild(
            emptyRow
          );
        }

        emptyRow.style.display =
          "";

      } else {

        if (emptyRow) {
          emptyRow.style.display =
            "none";
        }
      }
    }

    setupViewLinks() {

      document
        .querySelectorAll(
          ".view-link"
        )
        .forEach((link) => {

          link.addEventListener(
            "click",
            (e) => {

              e.preventDefault();

              const patientId =
                link.dataset.patientId;

              if (!patientId) {

                console.warn(
                  "Patient ID not found"
                );

                return;
              }

              console.log(
                "Viewing patient:",
                patientId
              );

              window.location.href =
                `/medical/patient-history/${patientId}/`;
            }
          );
        }
      );
    }

    setupCharts() {

      this.setupActivityBars();

      this.setupVisitDonut();
    }

    setupActivityBars() {

      const chart =
        document.getElementById(
          "consultationChart"
        );

      if (!chart) {
        return;
      }

      const bars =
        chart.querySelectorAll(
          ".bar"
        );

      if (!bars.length) {
        return;
      }

      const counts =
        Array.from(
          bars
        ).map((bar) =>
          Number(
            bar.dataset.count ||
              0
          )
        );

      const maxCount =
        Math.max(
          ...counts,
          1
        );

      bars.forEach(
        (bar, index) => {

          const count =
            Number(
              bar.dataset.count ||
                0
            );

          let height;

          if (count === 0) {

            height = 8;

          } else {

            height =
              Math.max(
                14,
                (count /
                  maxCount) *
                  100
              );
          }

          bar.style.height =
            `${height}%`;

          bar.style.opacity =
            "0";

          bar.style.transform =
            "scaleY(0)";

          setTimeout(
            () => {

              bar.style.transition =
                "all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)";

              bar.style.opacity =
                "1";

              bar.style.transform =
                "scaleY(1)";

            },
            100 +
              index * 80
          );

          const label =
            bar.dataset.label ||
            "";

          bar.setAttribute(
            "title",
            `${label}: ${count} consultation${
              count !== 1
                ? "s"
                : ""
            }`
          );
        }
      );
    }

    setupVisitDonut() {

      const donut =
        document.getElementById(
          "visitDonut"
        );

      if (!donut) {
        return;
      }

      const walkIn =
        Number(
          donut.dataset.walkin ||
            0
        );

      const appointment =
        Number(
          donut.dataset.appointment ||
            0
        );

      const total =
        walkIn +
        appointment;

      let walkInPercentage = 0;
      let appointmentPercentage = 0;

      if (total > 0) {

        walkInPercentage =
          Math.round(
            (walkIn / total) *
              100
          );

        appointmentPercentage =
          100 -
          walkInPercentage;
      }

      donut.style.setProperty(
        "--walkin-percent",
        `${walkInPercentage}%`
      );

      const walkinPercentageElement =
        document.getElementById(
          "walkinPercentage"
        );

      const appointmentPercentageElement =
        document.getElementById(
          "appointmentPercentage"
        );

      if (
        walkinPercentageElement
      ) {

        walkinPercentageElement.textContent =
          `${walkInPercentage}%`;
      }

      if (
        appointmentPercentageElement
      ) {

        appointmentPercentageElement.textContent =
          `${appointmentPercentage}%`;
      }

      donut.setAttribute(
        "title",
        `Walk-in: ${walkIn} | Appointment: ${appointment}`
      );

      donut.style.opacity =
        "0";

      donut.style.transform =
        "scale(0.85)";

      requestAnimationFrame(
        () => {

          donut.style.transition =
            "all 0.5s ease";

          donut.style.opacity =
            "1";

          donut.style.transform =
            "scale(1)";
        }
      );

      console.log(
        "Visit breakdown:",
        {
          walkIn,
          appointment,
          total,
          walkInPercentage,
          appointmentPercentage,
        }
      );
    }

    setupPagination() {

      document.addEventListener(
        "click",
        (event) => {

          const link =
            event.target.closest(
              "#patientPagination a[data-page]"
            );

          if (!link) {
            return;
          }

          event.preventDefault();

          const page =
            link.dataset.page;

          if (!page) {
            return;
          }

          this.loadPage(page);
        }
      );
    }

    async loadPage(page) {

      try {

        const url =
          new URL(
            window.location.href
          );

        url.searchParams.set(
          "page",
          page
        );

        const fetchUrl =
          new URL(
            url.toString()
          );

        fetchUrl.searchParams.set(
          "ajax",
          "1"
        );

        const response =
          await fetch(
            fetchUrl.toString(),
            {
              headers: {
                "X-Requested-With":
                  "XMLHttpRequest",
              },
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

        const currentBody =
          document.getElementById(
            "patientTableBody"
          );

        const newBody =
          doc.getElementById(
            "patientTableBody"
          );

        if (
          currentBody &&
          newBody
        ) {

          currentBody.innerHTML =
            newBody.innerHTML;
        }

        const currentPagination =
          document.getElementById(
            "patientPagination"
          );

        const newPagination =
          doc.getElementById(
            "patientPagination"
          );

        if (
          currentPagination &&
          newPagination
        ) {

          currentPagination.innerHTML =
            newPagination.innerHTML;
        }

        window.history.pushState(
          {},
          "",
          url.toString()
        );

        this.setupViewLinks();


        console.log(
          `Patient history page ${page} loaded using AJAX`
        );

      } catch (error) {

        console.error(
          "Pagination error:",
          error
        );
      }
    }
  }


  function initializePatientHistory() {

    if (
      !document.querySelector(
        ".patient-table"
      )
    ) {
      return;
    }

    window.patientHistory =
      new PatientHistory();
  }

  if (
    document.readyState ===
    "loading"
  ) {

    document.addEventListener(
      "DOMContentLoaded",
      initializePatientHistory
    );

  } else {

    initializePatientHistory();
  }

})();