

/* *********************************************** Arun code ***************************************************  */

AOS.init({
    once: true,
    duration: 600,
    easing: "ease-out-cubic",
    offset: 60,
});

      const gpaCtx = document.getElementById("gpaChart").getContext("2d");
      new Chart(gpaCtx, {
        type: "line",
        data: {
          labels: ["SP24", "SU24", "FA24", "SP25", "SU25", "FA25"],
          datasets: [
            {
              label: "GPA",
              data: [3.4, 3.5, 3.58, 3.64, 3.68, 3.72],
              borderColor: "#c5050c",
              backgroundColor: "rgba(197,5,12,0.07)",
              fill: true,
              tension: 0.4,
              pointBackgroundColor: "#c5050c",
              pointRadius: 4,
              borderWidth: 2,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          plugins: { legend: { display: false } },
          scales: {
            y: {
              min: 3.0,
              max: 4.0,
              grid: { color: "#f0f0f0" },
              ticks: { font: { size: 11 } },
            },
            x: {
              grid: { display: false },
              ticks: { font: { size: 11 } },
            },
          },
        },
      });

      const dCtx = document.getElementById("creditDonut").getContext("2d");
      new Chart(dCtx, {
        type: "doughnut",
        data: {
          datasets: [
            {
              data: [42, 28, 18, 32],
              backgroundColor: ["#c5050c", "#185fa5", "#228b22", "#e0e0e0"],
              borderWidth: 0,
            },
          ],
        },
        options: {
          cutout: "68%",
          responsive: true,
          maintainAspectRatio: true,
          plugins: {
            legend: { display: false },
            tooltip: { enabled: false },
          },
        },
      });

      window.addEventListener("load", () => {
        document.querySelectorAll(".prog-fill").forEach((el) => {
          const w = el.getAttribute("data-width");
          requestAnimationFrame(() => {
            el.style.width = w + "%";
          });
        });
      });

window.addEventListener("load", () => {

    document.querySelectorAll(".prog-fill").forEach((el) => {

        const w = el.getAttribute("data-width");

        requestAnimationFrame(() => {
            el.style.width = w + "%";
        });

    });

});


/* *********************************************** Arun code ***************************************************  */