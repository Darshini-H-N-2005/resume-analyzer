document.addEventListener("DOMContentLoaded", () => {
  // ============================
  // ATS DOUGHNUT CHART
  // ============================
  const atsCanvas = document.getElementById("atsChart");
  if (atsCanvas && typeof ATS_SCORE !== "undefined") {
    const ctx = atsCanvas.getContext("2d");
    new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["ATS Score", "Remaining"],
        datasets: [{
          data: [ATS_SCORE, Math.max(0, 100 - ATS_SCORE)],
          backgroundColor: ["#22c55e", "#4b5563"],
          borderWidth: 0
        }]
      },
      options: {
        cutout: "70%",
        plugins: {
          legend: { display: false }
        }
      }
    });
  }

  // ============================
  // SKILL MATCH BAR CHART
  // ============================
  const skillCanvas = document.getElementById("skillChart");
  if (skillCanvas && typeof MATCHED_SKILLS !== "undefined") {
    const ctx2 = skillCanvas.getContext("2d");

    const matchedCount = MATCHED_SKILLS.length;
    const missingCount = MISSING_SKILLS.length;

    new Chart(ctx2, {
      type: "bar",
      data: {
        labels: ["Matched Skills", "Missing Skills"],
        datasets: [{
          label: "Skill Count",
          data: [matchedCount, missingCount],
          backgroundColor: ["#22c55e", "#facc15"]
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }
    });
  }
});
