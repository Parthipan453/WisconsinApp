AOS.init({ duration: 500, once: true, offset: 40 });

const athleteData = document.getElementById("athlete-data");

const riskLevel = athleteData.dataset.riskLevel;
const riskScore = { EXCELLENT: 100, GOOD: 85, AVERAGE: 65, POOR: 25 }[riskLevel] ?? 85;
const riskColor =
  { EXCELLENT: "#228b22", GOOD: "#185fa5" , AVERAGE: "#f59e0b", POOR: "#dc2626" }[riskLevel] ??
  "#185fa5";

document.addEventListener("DOMContentLoaded", () => {
  const ctx = document.getElementById("readinessGauge");

  if (ctx) {
    new Chart(ctx, {
      type: "doughnut",
      data: {
        datasets: [
          {
            data: [riskScore, 100 - riskScore],
            backgroundColor: [riskColor, "#f0f0f0"],
            borderWidth: 0,
            cutout: "78%",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        rotation: -90,
        circumference: 360,
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        animation: { duration: 900, easing: "easeOutQuart" },
      },
    });
  }
});
