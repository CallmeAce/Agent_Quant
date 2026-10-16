async function loadMonitor() {
  try {
    const status = await fetch("/api/v1/system/status").then((r) => r.json());
    const grid = document.getElementById("freshness");
    grid.innerHTML = (status.data_freshness || []).map((f) =>
      `<div class="card"><div class="k">${f.table_name}</div><div class="v">${f.latest_date || "-"}</div><div class="k">${f.row_count || 0} rows</div></div>`
    ).join("");

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
