// Tab switching between monitoring and backtest views.
document.querySelectorAll("nav button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("nav button").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("view-" + btn.dataset.view).classList.add("active");
    if (btn.dataset.view === "monitor") window.loadMonitor();
    if (btn.dataset.view === "backtest") window.loadBacktests();
  });
});

window.addEventListener("DOMContentLoaded", () => window.loadMonitor());
