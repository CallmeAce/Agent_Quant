// Tab switching between monitoring and backtest views.
document.querySelectorAll("nav button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("nav button").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("view-" + btn.dataset.view).classList.add("active");
    // give the view a tick to become visible so ECharts gets a real size
    setTimeout(() => {
      if (btn.dataset.view === "monitor") window.loadMonitor();
      if (btn.dataset.view === "backtest") window.loadBacktests();
      if (window.resizeCharts) window.resizeCharts();
    }, 50);
  });
});

window.addEventListener("resize", () => window.resizeCharts && window.resizeCharts());
window.addEventListener("DOMContentLoaded", () => window.loadMonitor());
