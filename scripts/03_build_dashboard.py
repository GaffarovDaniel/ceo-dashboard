"""
ПР №6. Интерактивный дашборд для CEO (Plotly.js) -> docs/index.html
Публикуется на GitHub Pages из папки /docs.
"""
import json
import pandas as pd

df = pd.read_csv("data/processed/kpi_clean.csv")
data = df.to_dict(orient="list")

html = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Дашборд CEO · Вектор Ритейл</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  :root { --bg:#f4f5f7; --card:#fff; --ink:#1d2433; --muted:#6b7385; --line:#e3e6ec;
          --accent:#2457d6; --good:#17845a; --bad:#c2410c; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
         font:14px/1.45 "Segoe UI", Roboto, Arial, sans-serif; }
  header { padding:20px 28px 8px; display:flex; flex-wrap:wrap; gap:16px;
           align-items:flex-end; justify-content:space-between; }
  h1 { font-size:22px; margin:0; }
  .sub { color:var(--muted); margin-top:2px; }
  .filters { display:flex; gap:6px; flex-wrap:wrap; }
  .filters button { border:1px solid var(--line); background:#fff; border-radius:16px;
         padding:5px 12px; cursor:pointer; font:inherit; color:var(--ink); }
  .filters button.on { background:var(--accent); color:#fff; border-color:var(--accent); }
  main { padding:8px 28px 28px; display:grid; gap:14px;
         grid-template-columns:repeat(12, 1fr); }
  .kpi { grid-column:span 2; background:var(--card); border:1px solid var(--line);
         border-radius:10px; padding:14px 16px; }
  .kpi .l { color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.03em; }
  .kpi .v { font-size:24px; font-weight:600; margin:4px 0 2px; font-variant-numeric:tabular-nums; }
  .kpi .d { font-size:12px; }
  .up { color:var(--good); } .down { color:var(--bad); }
  .card { background:var(--card); border:1px solid var(--line); border-radius:10px;
          padding:12px 14px 4px; }
  .card h2 { font-size:14px; margin:2px 0 0; font-weight:600; }
  .w8 { grid-column:span 8; } .w4 { grid-column:span 4; } .w6 { grid-column:span 6; }
  .chart { height:290px; }
  footer { color:var(--muted); font-size:12px; padding:0 28px 24px; }
  @media (max-width:900px) { .kpi { grid-column:span 6; } .w8,.w4,.w6 { grid-column:span 12; }
    header, main, footer { padding-left:16px; padding-right:16px; } }
</style>
</head>
<body>
<header>
  <div>
    <h1>Дашборд CEO — ООО «Вектор Ритейл»</h1>
    <div class="sub" id="period"></div>
  </div>
  <div class="filters" id="filters"></div>
</header>
<main>
  <div class="kpi"><div class="l">Выручка, мес.</div><div class="v" id="k_rev"></div><div class="d" id="k_rev_d"></div></div>
  <div class="kpi"><div class="l">Выполнение плана</div><div class="v" id="k_plan"></div><div class="d" id="k_plan_d"></div></div>
  <div class="kpi"><div class="l">EBITDA, мес.</div><div class="v" id="k_ebitda"></div><div class="d" id="k_ebitda_d"></div></div>
  <div class="kpi"><div class="l">Маржа EBITDA</div><div class="v" id="k_marg"></div><div class="d" id="k_marg_d"></div></div>
  <div class="kpi"><div class="l">NPS</div><div class="v" id="k_nps"></div><div class="d" id="k_nps_d"></div></div>
  <div class="kpi"><div class="l">Отток клиентов</div><div class="v" id="k_churn"></div><div class="d" id="k_churn_d"></div></div>

  <div class="card w8"><h2>Выручка: факт и план, млн ₽</h2><div class="chart" id="c_rev"></div></div>
  <div class="card w4"><h2>Структура выручки по регионам (последний месяц)</h2><div class="chart" id="c_reg"></div></div>
  <div class="card w6"><h2>Маржинальность, %</h2><div class="chart" id="c_marg"></div></div>
  <div class="card w6"><h2>Клиенты: новые и ушедшие</h2><div class="chart" id="c_cl"></div></div>
</main>
<footer>Данные: data/processed/kpi_clean.csv · отчёт пересобирается GitHub Actions при каждом обновлении данных · данные модельные (учебный проект)</footer>

<script>
const RAW = __DATA__;
const rows = RAW.month.map((_, i) => Object.fromEntries(Object.keys(RAW).map(k => [k, RAW[k][i]])));
const REGIONS = [...new Set(rows.map(r => r.region))];
const COLORS = ["#2457d6", "#e07b39", "#17845a", "#8a4fd1"];
let current = "Все";

const fmtM = v => (v / 1e6).toLocaleString("ru-RU", {maximumFractionDigits: 1}) + " млн ₽";
const pct = v => v.toLocaleString("ru-RU", {maximumFractionDigits: 1}) + " %";
function delta(el, now, prev, unit, invert) {
  const d = now - prev, good = invert ? d < 0 : d > 0;
  const s = (d > 0 ? "▲ " : "▼ ") + Math.abs(d).toLocaleString("ru-RU", {maximumFractionDigits: 1}) + unit + " к пред. мес.";
  el.textContent = s; el.className = "d " + (good ? "up" : "down");
}
function agg(region) {
  const src = region === "Все" ? rows : rows.filter(r => r.region === region);
  const by = {};
  src.forEach(r => {
    const m = by[r.month] ||= {month: r.month, revenue: 0, plan: 0, gp: 0, ebitda: 0,
                               active: 0, newc: 0, churn: 0, npsw: 0};
    m.revenue += r.revenue; m.plan += r.plan_revenue; m.gp += r.gross_profit; m.ebitda += r.ebitda;
    m.active += r.active_clients; m.newc += r.new_clients; m.churn += r.churned_clients;
    m.npsw += r.nps * r.active_clients;
  });
  return Object.values(by).sort((a, b) => a.month.localeCompare(b.month));
}
const layout = (extra) => Object.assign({
  margin: {l: 56, r: 12, t: 12, b: 62}, paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
  font: {family: "Segoe UI, Roboto, Arial", size: 12, color: "#1d2433"},
  xaxis: {gridcolor: "#eef0f4", type: "category", tickangle: -45, nticks: 12}, yaxis: {gridcolor: "#eef0f4", zeroline: false},
  legend: {orientation: "h", y: 1.12, x: 0}, hovermode: "x unified"}, extra || {});
const cfg = {displayModeBar: false, responsive: true};

function render() {
  const s = agg(current), last = s[s.length - 1], prev = s[s.length - 2];
  document.getElementById("period").textContent =
    "Период: " + s[0].month + " – " + last.month + " · срез: " + current;
  document.getElementById("k_rev").textContent = fmtM(last.revenue);
  delta(document.getElementById("k_rev_d"), last.revenue / 1e6, prev.revenue / 1e6, " млн", false);
  const pe = last.revenue / last.plan * 100, ppe = prev.revenue / prev.plan * 100;
  document.getElementById("k_plan").textContent = pct(pe);
  delta(document.getElementById("k_plan_d"), pe, ppe, " п.п.", false);
  document.getElementById("k_ebitda").textContent = fmtM(last.ebitda);
  delta(document.getElementById("k_ebitda_d"), last.ebitda / 1e6, prev.ebitda / 1e6, " млн", false);
  const mg = last.ebitda / last.revenue * 100, pmg = prev.ebitda / prev.revenue * 100;
  document.getElementById("k_marg").textContent = pct(mg);
  delta(document.getElementById("k_marg_d"), mg, pmg, " п.п.", false);
  const nps = last.npsw / last.active, pnps = prev.npsw / prev.active;
  document.getElementById("k_nps").textContent = nps.toLocaleString("ru-RU", {minimumFractionDigits: 1, maximumFractionDigits: 1});
  delta(document.getElementById("k_nps_d"), nps, pnps, "", false);
  const ch = last.churn / last.active * 100, pch = prev.churn / prev.active * 100;
  document.getElementById("k_churn").textContent = pct(ch);
  delta(document.getElementById("k_churn_d"), ch, pch, " п.п.", true);

  const x = s.map(r => r.month);
  Plotly.react("c_rev", [
    {x, y: s.map(r => r.revenue / 1e6), name: "Факт", type: "bar", marker: {color: "#2457d6"}},
    {x, y: s.map(r => r.plan / 1e6), name: "План", type: "scatter", mode: "lines",
     line: {color: "#e07b39", width: 2.5, dash: "dot"}}], layout(), cfg);

  const lastMonth = rows[rows.length - 1].month;
  const lr = rows.filter(r => r.month === lastMonth);
  Plotly.react("c_reg", [{type: "pie", hole: .55, labels: lr.map(r => r.region),
    values: lr.map(r => r.revenue), marker: {colors: COLORS}, sort: false,
    textinfo: "percent", hovertemplate: "%{label}: %{value:,.0f} ₽<extra></extra>"}],
    layout({showlegend: true, legend: {orientation: "v", x: 1, y: .5}, margin: {l: 8, r: 8, t: 8, b: 8}}), cfg);

  Plotly.react("c_marg", [
    {x, y: s.map(r => r.gp / r.revenue * 100), name: "Валовая маржа", mode: "lines+markers",
     line: {color: "#17845a", width: 2.5}},
    {x, y: s.map(r => r.ebitda / r.revenue * 100), name: "Маржа EBITDA", mode: "lines+markers",
     line: {color: "#8a4fd1", width: 2.5}}], layout({yaxis: {gridcolor: "#eef0f4", ticksuffix: " %"}}), cfg);

  Plotly.react("c_cl", [
    {x, y: s.map(r => r.newc), name: "Новые", type: "bar", marker: {color: "#17845a"}},
    {x, y: s.map(r => -r.churn), name: "Ушедшие", type: "bar", marker: {color: "#c2410c"},
     customdata: s.map(r => r.churn), hovertemplate: "%{customdata}"}],
    layout({barmode: "relative"}), cfg);
}

const f = document.getElementById("filters");
["Все", ...REGIONS].forEach(r => {
  const b = document.createElement("button");
  b.textContent = r; if (r === current) b.className = "on";
  b.onclick = () => { current = r; [...f.children].forEach(c => c.className = c === b ? "on" : ""); render(); };
  f.appendChild(b);
});
render();
</script>
</body>
</html>
"""
with open("docs/index.html", "w", encoding="utf-8") as fh:
    fh.write(html.replace("__DATA__", json.dumps(data, ensure_ascii=False)))
print("Дашборд сохранён -> docs/index.html")
