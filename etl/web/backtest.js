let navChart = null;

function ensureChart() {
  const el = document.getElementById("nav-chart");
  if (!navChart && window.echarts) {
    navChart = echarts.init(el);
    window.addEventListener("resize", () => navChart && navChart.resize());
  }
  return navChart;
}

async function loadBacktests() {
  try {
    const runs = await fetch("/api/v1/backtests?limit=50").then((r) => r.json());
    const tbody = document.querySelector("#runs tbody");
    tbody.innerHTML = (runs || []).map((x) => {
      const tr = (v) => v == null ? "-" : (Number(v) * 100).toFixed(2) + "%";
      return `<tr data-run="${x.run_id}"><td>${x.run_id}</td><td>${x.strategy_id}</td><td>${x.start_date} ~ ${x.end_date}</td><td class="${Number(x.total_return) >= 0 ? "pos" : "neg"}">${tr(x.total_return)}</td><td>${tr(x.annual_return)}</td><td>${x.sharpe ?? "-"}</td><td class="neg">${tr(x.max_drawdown)}</td></tr>`;
    }).join("");
    tbody.querySelectorAll("tr").forEach((tr) => tr.addEventListener("click", () => loadRunDetail(tr.dataset.run)));
    if (runs && runs.length) loadRunDetail(runs[0].run_id); // auto-open first run so a chart shows immediately
  } catch (e) {
    console.error("loadBacktests failed", e);
  }
}

async function loadRunDetail(runId) {
  try {
    const d = await fetch("/api/v1/backtests/" + encodeURIComponent(runId)).then((r) => r.json());
    const m = d.metrics || {};
    const pct = (v) => v == null ? "-" : (Number(v) * 100).toFixed(2) + "%";
    document.getElementById("metrics").innerHTML = [
      ["总收益", pct(m.total_return)], ["年化", pct(m.annual_return)], ["Sharpe", m.sharpe ?? "-"],
      ["最大回撤", pct(m.max_drawdown)], ["胜率", pct(m.win_rate)], ["换手", m.turnover ?? "-"],
      ["基准收益", pct(m.benchmark_return)],
    ].map(([k, v]) => `<div class="card"><div class="k">${k}</div><div class="v">${v}</div></div>`).join("");

    const nav = d.nav || [];
    const chart = ensureChart();
    if (chart) {
      chart.setOption({
        title: { text: "策略净值 vs 基准", left: "center" },
        tooltip: { trigger: "axis" },
        legend: { data: ["策略净值", "基准净值"], bottom: 0 },
        xAxis: { type: "category", data: nav.map((p) => p.trade_date) },
        yAxis: { type: "value", scale: true },
        dataZoom: [{ type: "inside" }, { type: "slider" }],
        series: [
          { name: "策略净值", type: "line", showSymbol: false, data: nav.map((p) => p.nav) },
          { name: "基准净值", type: "line", showSymbol: false, data: nav.map((p) => p.benchmark_nav) },
        ],
      }, true);
      chart.resize();
    }

    const tbody = document.querySelector("#positions tbody");
    tbody.innerHTML = (d.positions || []).map((p) =>
      `<tr><td>${p.security_id}</td><td>${p.trade_date}</td><td>${(Number(p.weight) * 100).toFixed(2)}%</td></tr>`
    ).join("");
  } catch (e) {
    console.error("loadRunDetail failed", e);
  }
}
window.loadBacktests = loadBacktests;
window.resizeCharts = () => navChart && navChart.resize();
