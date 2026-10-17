let freshChart = null;

function ensureFreshChart() {
  const el = document.getElementById("freshness-chart");
  if (!freshChart && window.echarts) {
    freshChart = echarts.init(el);
    window.addEventListener("resize", () => freshChart && freshChart.resize());
  }
  return freshChart;
}

async function loadMonitor() {
  try {
    const status = await fetch("/api/v1/system/status").then((r) => r.json());
    const freshness = status.data_freshness || [];
    const grid = document.getElementById("freshness");
    grid.innerHTML = freshness.map((f) =>
      `<div class="card"><div class="k">${f.table_name}</div><div class="v">${f.latest_date || "-"}</div><div class="k">${f.row_count || 0} rows</div></div>`
    ).join("");

    const chart = ensureFreshChart();
    if (chart) {
      chart.setOption({
        title: { text: "各表数据量", left: "center" },
        tooltip: { trigger: "axis" },
        grid: { left: 160, right: 30, top: 50, bottom: 30 },
        xAxis: { type: "value" },
        yAxis: { type: "category", data: freshness.map((f) => f.table_name) },
        series: [{ type: "bar", data: freshness.map((f) => f.row_count || 0), itemStyle: { color: "#3b82f6" } }],
      }, true);
      chart.resize();
    }

    const jobs = await fetch("/api/v1/jobs?limit=50").then((r) => r.json());
    const tbody = document.querySelector("#jobs tbody");
    tbody.innerHTML = (jobs || []).map((j) =>
      `<tr><td>${j.job_name}</td><td>${j.run_time || ""}</td><td class="${j.status === "success" ? "pos" : "neg"}">${j.status || ""}</td><td>${j.rows_affected ?? ""}</td><td>${j.duration_seconds ?? ""}</td></tr>`
    ).join("");
  } catch (e) {
    console.error("loadMonitor failed", e);
  }
}
window.loadMonitor = loadMonitor;
window.resizeCharts = () => { freshChart && freshChart.resize(); };
