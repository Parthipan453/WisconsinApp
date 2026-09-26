const hcChartInstances = [];

function hcGetSizeBucket(width) {
  if (width <= 220) return "micro";
  if (width <= 320) return "xs";
  if (width <= 480) return "sm";
  if (width <= 768) return "md";
  return "lg";
}

function hcResponsiveFont(width) {
  // const bucket = hcGetSizeBucket(width);
  // switch (bucket) {
  //   case "micro":
  //     return 8;
  //   case "xs":
  //     return 9;
  //   case "sm":
  //     return 11;
  //   case "md":
  //     return 12;
  //   default:
  //     return 13;
  // }
   if (width <= 170) return 6;
  if (width <= 200) return 7;
  if (width <= 240) return 8;
  if (width <= 320) return 9;
  if (width <= 480) return 11;
  if (width <= 768) return 12;

  return 13;
}

function hcResponsiveLegend(width) {
  // return width > 240;
   return true;
}

function hcResponsivePointRadius(width) {
  const bucket = hcGetSizeBucket(width);
  if (bucket === "micro") return 1.5;
  if (bucket === "xs") return 2.5;
  if (bucket === "sm") return 3.5;
  return 5;
}

function hcResponsiveBorderWidth(width) {
  const bucket = hcGetSizeBucket(width);
  if (bucket === "micro" || bucket === "xs") return 1;
  return 2;
}
function hcApplyResponsiveConfig(chart) {
  if (!chart || !chart.canvas) return;

  const width = chart.width || chart.canvas.clientWidth || 0;

  const fontSize = hcResponsiveFont(width);
  const legendDisplay = hcResponsiveLegend(width);
  const pointRadius = hcResponsivePointRadius(width);
  const borderWidth = hcResponsiveBorderWidth(width);

  // X/Y axis fonts
  // if (chart.options.scales) {
  //   if (chart.options.scales.x?.ticks) {
  //     chart.options.scales.x.ticks.font = {
  //       size: fontSize,
  //     };
  //   }

  //   if (chart.options.scales.y?.ticks) {
  //     chart.options.scales.y.ticks.font = {
  //       size: fontSize,
  //     };
  //   }
  // }

  if (chart.options.scales) {
    if (chart.options.scales.x?.ticks) {
      chart.options.scales.x.ticks.font = {
        size: fontSize,
      };

      chart.options.scales.x.ticks.maxRotation =
        width <= 220 ? 45 : 0;

      chart.options.scales.x.ticks.minRotation =
        width <= 220 ? 45 : 0;

      chart.options.scales.x.ticks.padding =
        width <= 220 ? 2 : 6;
    }

    if (chart.options.scales.y?.ticks) {
      chart.options.scales.y.ticks.font = {
        size: fontSize,
      };

      chart.options.scales.y.ticks.padding =
        width <= 220 ? 2 : 6;
    }
  }

  // Legend
  // if (chart.options.plugins?.legend) {
  //   chart.options.plugins.legend.display = legendDisplay;

  //   if (legendDisplay) {
  //     chart.options.plugins.legend.labels = {
  //       ...chart.options.plugins.legend.labels,
  //       font: {
  //         size: fontSize,
  //       },
  //       boxWidth: Math.max(8, fontSize),
  //       padding: width <= 320 ? 6 : 10,
  //     };
  //   }
  // }
   if (chart.options.plugins?.legend) {
    chart.options.plugins.legend.display = true;

    chart.options.plugins.legend.labels = {
      ...chart.options.plugins.legend.labels,

      font: {
        size: fontSize,
      },

      boxWidth:
        width <= 170
          ? 6
          : width <= 220
            ? 8
            : width <= 320
              ? 10
              : 12,

      boxHeight:
        width <= 170
          ? 6
          : width <= 220
            ? 8
            : width <= 320
              ? 10
              : 12,

      padding:
        width <= 170
          ? 2
          : width <= 220
            ? 4
            : width <= 320
              ? 6
              : 10,
    };

    /* Keep legend visible */
    chart.options.plugins.legend.position = "bottom";
  }

  // Dataset point radius / border
  // chart.data?.datasets?.forEach((dataset) => {
  //   if (chart.config.type === "line") {
  //     dataset.pointRadius = pointRadius;
  //     dataset.pointHoverRadius = Math.max(pointRadius + 1, 4);
  //     dataset.borderWidth = borderWidth;
  //   }

  //   if (chart.config.type === "pie" || chart.config.type === "doughnut") {
  //     dataset.borderWidth = width <= 320 ? 1 : 2;
  //   }
  // });
   chart.data?.datasets?.forEach((dataset) => {
    if (chart.config.type === "line") {
      dataset.pointRadius = pointRadius;
      dataset.pointHoverRadius = Math.max(pointRadius + 1, 4);
      dataset.borderWidth = borderWidth;
    }

    if (
      chart.config.type === "pie" ||
      chart.config.type === "doughnut"
    ) {
      dataset.borderWidth = width <= 220 ? 1 : 2;
    }
  });

  chart.update("none");
}

function hcRefreshAllCharts() {
  hcChartInstances.forEach(hcApplyResponsiveConfig);
}

let hcResizeTimer = null;
function hcScheduleRefresh() {
  clearTimeout(hcResizeTimer);
  hcResizeTimer = setTimeout(hcRefreshAllCharts, 120);
}

window.addEventListener("resize", hcScheduleRefresh);
window.addEventListener("orientationchange", hcScheduleRefresh);

if (typeof ResizeObserver !== "undefined") {
  const hcRO = new ResizeObserver(hcScheduleRefresh);
  document.addEventListener("DOMContentLoaded", () => {
    document
      .querySelectorAll(".hc-chart-box, .hc-chart-container, .hc-chart-card")
      .forEach((el) => hcRO.observe(el));
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const monthlyCtx = document.getElementById("yearlyCampChart");

  if (monthlyCtx) {
    const monthlyChart = new Chart(monthlyCtx, {
      type: "line",

      data: {
        labels: yearlyLabels,
        datasets: [
          {
            label: "Camps",
            data: yearlyValues,
            borderColor: "#c5050c",
            backgroundColor: "rgba(197,5,12,.18)",
            pointBackgroundColor: "#c5050c",
            pointBorderColor: "#ffffff",
            pointRadius: 5,
            borderWidth: 2,
            fill: true,
            tension: 0.4,
          },
        ],
      },

      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
            _forceHidden: true,
          },
        },
        scales: {
          x: { ticks: { font: { size: 12 } } },
          y: {
            beginAtZero: true,
            ticks: { font: { size: 12 } },
          },
        },
      },
    });

    hcChartInstances.push(monthlyChart);
  }
  const participantCtx = document.getElementById("participantChart");

  if (participantCtx) {
    const participantChart = new Chart(participantCtx, {
      type: "doughnut",

      data: {
        labels: participantLabels,
        datasets: [
          {
            data: participantValues,
            backgroundColor: [
              "#2563eb",
              "#10b981",
              "#f59e0b",
              "#ef4444",
              "#8b5cf6",
            ],
          },
        ],
      },

      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "70%",
        plugins: {
          legend: {
             display: true,
            position: "bottom",
          
          labels: {
        font: {
          size: 13,
        },
        boxWidth: 12,
        boxHeight: 12,
        padding: 10,
      },
      },
        },
      },
      plugins: [
        {
          id: "centerText",
          beforeDraw(chart) {
            const { ctx } = chart;
            const meta = chart.getDatasetMeta(0).data[0];
            if (!meta) return;
            const totalParticipants = chart.data.datasets[0].data.reduce(
              (sum, value) => sum + value,
              0,
            );
            const width = chart.width;
            let countFont = 16;
            let labelFont = 12;
            if (width <= 170) {
              countFont = 8;
              labelFont = 6;
            } else if (width <= 220) {
              countFont = 10;
              labelFont = 7;
            } else if (width <= 320) {
              countFont = 12;
              labelFont = 9;
            } else if (width <= 480) {
              countFont = 14;
              labelFont = 10;
            }

            ctx.save();
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";

            ctx.font = `bold ${countFont}px Poppins`;
            ctx.fillStyle = "#111827";
            ctx.fillText(totalParticipants, meta.x, meta.y - labelFont / 2);

            ctx.font = `${labelFont}px Poppins`;
            ctx.fillStyle = "#6b7280";
            ctx.fillText("Participants", meta.x, meta.y + countFont);

            ctx.restore();
          },
        },
      ],
    });
      hcChartInstances.push(participantChart);
  }

  // const statusCtx = new Chart(document.getElementById("statusChart"), {
  //   type: "pie",
  //   data: {
  //     labels: statusLabels,
  //     datasets: [
  //       {
  //         data: statusValues,
  //         backgroundColor: [
  //           "#38bdf8",
  //           "#22c55e",
  //           "#f59e0b",
  //           "#2563eb",
  //           "#ef4444",
  //         ],
  //         borderWidth: 0,
  //       },
  //     ],
  //   },
  //   options: {
  //     responsive: true,
  //     maintainAspectRatio: false,
  //     plugins: {
  //       legend: {
  //           display: true,
  //         position: "bottom",
  //       },

  //     labels: {
  //       font: {
  //         size: 13,
  //       },
  //       boxWidth: 12,
  //       boxHeight: 12,
  //       padding: 10,
  //     },
  //     },
  //   },
  // });
  //   hcChartInstances.push(statusChart);
  const statusCtx = document.getElementById("statusChart");

if (statusCtx) {
  const statusChart = new Chart(statusCtx, {
    type: "pie",

    data: {
      labels: statusLabels,
      datasets: [
        {
          data: statusValues,
          backgroundColor: [
            "#38bdf8",
            "#22c55e",
            "#f59e0b",
            "#2563eb",
            "#ef4444",
          ],
          borderWidth: 0,
        },
      ],
    },

    options: {
      responsive: true,
      maintainAspectRatio: false,

      plugins: {
        legend: {
          display: true,
          position: "bottom",

          labels: {
            font: {
              size: 13,
            },

            boxWidth: 12,
            boxHeight: 12,
            padding: 10,
          },
        },
      },
    },
  });

  hcChartInstances.push(statusChart);
}

});

// document.addEventListener("DOMContentLoaded", () => {
//   if (window.lucide) {
//     lucide.createIcons();
//   }

//   if (typeof AOS !== "undefined") {
//     AOS.init({
//       duration: 900,
//       once: true,
//       easing: "ease-in-out",
//       offset: 70,
//     });
//   }

//   document.querySelectorAll(".hc-filter select").forEach((select) => {
//       // Already initialized by Choices.js
//      if (
//     select.classList.contains("choices__input") ||
//     select.closest(".choices")
//   ) {
//     return;
//   }

//   new Choices(select, {
//     searchEnabled: false,
//     itemSelectText: "",
//     shouldSort: false,
//   });
//   });
//   animateCounters();
//   heroGlow();
//   statHoverEffect();
// });

document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) {
    lucide.createIcons();
  }

  if (typeof AOS !== "undefined") {
    AOS.init({
      duration: 900,
      once: true,
      easing: "ease-in-out",
      offset: 70,
    });
  }

  document.querySelectorAll(".hc-filter select").forEach((select) => {

    // Already initialized by Choices.js
    if (select.closest(".choices")) {
      return;
    }

    const choicesInstance = new Choices(select, {
      searchEnabled: false,
      itemSelectText: "",
      shouldSort: false,
      allowHTML: false,
      shouldFocusInput: false,
    });

    // Prevent dropdown from opening automatically
    choicesInstance.hideDropdown();

    // Remove accidental focus
    setTimeout(() => {
      select.blur();

      const wrapper = select.closest(".choices");
      if (wrapper) {
        wrapper.classList.remove("is-focused");
        wrapper.classList.remove("is-open");
      }
    }, 0);
  });

  // Make sure no filter dropdown is open on initial page load
  setTimeout(() => {
    document.querySelectorAll(".hc-filter .choices").forEach((wrapper) => {
      wrapper.classList.remove("is-open", "is-focused");
    });

    const active = document.activeElement;

    if (
      active &&
      active.closest &&
      active.closest(".hc-filter")
    ) {
      active.blur();
    }
  }, 50);

  animateCounters();
  heroGlow();
  statHoverEffect();
});
function animateCounters() {
  const counters = document.querySelectorAll(".counter");

  counters.forEach((counter) => {
    const target =
      parseInt(counter.textContent.trim().replace(/,/g, ""), 10) || 0;

    let current = 0;

    const duration = 1500;
    const stepTime = 16;
    const steps = duration / stepTime;
    const increment = target / steps;

    function update() {
      current += increment;

      if (current >= target) {
        counter.textContent = target.toLocaleString();
        return;
      }

      counter.textContent = Math.floor(current).toLocaleString();
      requestAnimationFrame(update);
    }

    update();
  });
}

function heroGlow() {
  const hero = document.querySelector(".hc-hero");

  if (!hero) return;

  const isFinePointer =
    window.matchMedia &&
    window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  if (!isFinePointer) return;

  const heading = hero.querySelector("h1");
  const para = hero.querySelector("p");
  const badge = hero.querySelector(".hc-badge");

  hero.addEventListener("mousemove", (e) => {
    const rect = hero.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    hero.style.background = `
        radial-gradient(
            circle at ${x}px ${y}px,
            rgba(255,255,255,.18),
            transparent 230px
        ),
        linear-gradient(
            135deg,
            #eb2525,
            #f63b3b,
            #fa6060
        )`;
    if (heading) heading.style.color = "#fff";
    if (para) para.style.color = "rgba(255,255,255,.9)";

    if (badge) {
      badge.style.background = "rgba(255,255,255,.18)";
      badge.style.color = "#fff";
      badge.style.border = "1px solid rgba(255,255,255,.35)";
    }
  });

  hero.addEventListener("mouseleave", () => {
    hero.style.background = `
        linear-gradient(
            135deg,
            #eb2525,
            #f63b3b,
            #fa6060
        )`;
  });
}

function statHoverEffect() {
  document.querySelectorAll(".hc-stat").forEach((card) => {
    card.addEventListener("mouseenter", () => {
      card.style.transform = "translateY(-10px) scale(1.02)";
    });
    card.addEventListener("mouseleave", () => {
      card.style.transform = "";
    });
  });
}
const searchInput = document.querySelector(".hc-search input");
if (searchInput) {
  searchInput.addEventListener("focus", () => {
    searchInput.parentElement.classList.add("active");
  });
  searchInput.addEventListener("blur", () => {
    searchInput.parentElement.classList.remove("active");
  });
}
document.querySelectorAll("a[href^='#']").forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    const target = document.querySelector(this.getAttribute("href"));
    if (!target) return;
    e.preventDefault();
    target.scrollIntoView({
      behavior: "smooth",
    });
  });
});

const heroImage = document.querySelector(".hc-hero__image img");
if (heroImage) {
  let angle = 0;
  setInterval(() => {
    angle += 0.8;
    heroImage.style.transform = `translateY(${Math.sin((angle * Math.PI) / 180) * 8}px)`;
  }, 40);
}
document.querySelectorAll(".hc-placeholder").forEach((box) => {
  box.addEventListener("mouseenter", () => {
    box.style.boxShadow = "0 20px 50px rgba(37,99,235,.15)";
  });
  box.addEventListener("mouseleave", () => {
    box.style.boxShadow = "";
  });
});

window.addEventListener("resize", () => {
  if (typeof AOS !== "undefined") {
    AOS.refresh();
  }
});

const buttons = document.querySelectorAll(".hc-float-btn");

buttons.forEach((btn) => {
  btn.addEventListener("click", () => {
    buttons.forEach((b) => b.classList.remove("active"));

    btn.classList.add("active");
  });
});

const form = document.getElementById("filterForm");

if (form) {
  form.addEventListener("submit", function (e) {
    e.preventDefault();

    const params = new URLSearchParams(new FormData(form));

    fetch(form.action + "?" + params.toString())
      .then((response) => response.text())
      .then((html) => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, "text/html");

        const newContent = doc.querySelector("#campResults");

        document.querySelector("#campResults").innerHTML = newContent.innerHTML;
      });
  });
}
document.addEventListener("click", function (e) {
  const link = e.target.closest(".hc-page-btn");

  if (!link || !link.href) return;

  e.preventDefault();

  fetch(link.href)
    .then((res) => res.text())
    .then((html) => {
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");

      document.querySelector("#campResults").innerHTML =
        doc.querySelector("#campResults").innerHTML;
    });
});
const resetBtn = document.getElementById("resetFilter");

if (resetBtn) {
  resetBtn.addEventListener("click", function (e) {
    e.preventDefault();

    fetch(this.href)
      .then((r) => r.text())
      .then((html) => {
        const doc = new DOMParser().parseFromString(html, "text/html");

        document.querySelector("#campResults").innerHTML =
          doc.querySelector("#campResults").innerHTML;

        document.getElementById("filterForm").reset();
      });
  });
}

document.addEventListener("click", function (e) {
  const btn = e.target.closest(".hc-toggle-btn");

  if (!btn) return;

  const targetId = btn.dataset.target;
  const targetPanel = document.getElementById(targetId);

  if (!targetPanel) return;

  document.querySelectorAll(".hc-toggle-btn").forEach((b) => {
    b.classList.remove("active");
  });

  btn.classList.add("active");

  document.querySelectorAll(".hc-expand-panel").forEach((panel) => {
    panel.classList.remove("show");
  });

  targetPanel.classList.add("show");
});
