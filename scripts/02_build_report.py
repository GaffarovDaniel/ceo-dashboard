"""
ПР №5. Автоматическая генерация HTML-отчёта -> docs/report.html
Запускается GitHub Actions при каждом изменении папки data/.
"""
import base64
import io
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv("data/processed/kpi_clean.csv")
last, prev = sorted(df["month"].unique())[-1], sorted(df["month"].unique())[-2]
yago = f"{int(last[:4]) - 1}{last[4:]}"

def total(m, col):
    return df.loc[df["month"] == m, col].sum()

rev, rev_prev, rev_y = total(last, "revenue"), total(prev, "revenue"), total(yago, "revenue")
plan = total(last, "plan_revenue")
ebitda = total(last, "ebitda")

# Сводка по регионам за последний месяц
reg = (df[df["month"] == last]
       .groupby("region")
       .agg(Выручка_млн=("revenue", lambda s: s.sum() / 1e6),
            План_млн=("plan_revenue", lambda s: s.sum() / 1e6),
            EBITDA_млн=("ebitda", lambda s: s.sum() / 1e6),
            NPS=("nps", "mean"),
            Отток_проц=("churn_rate_pct", "mean"))
       .round(1))
reg["Выполнение_плана_проц"] = (reg["Выручка_млн"] / reg["План_млн"] * 100).round(1)
reg = reg.sort_values("Выручка_млн", ascending=False)

# График динамики выручки
monthly = df.groupby("month")[["revenue", "plan_revenue"]].sum() / 1e6
fig, ax = plt.subplots(figsize=(9, 3.4), dpi=120)
ax.bar(monthly.index, monthly["revenue"], color="#2457d6", label="Факт")
ax.plot(monthly.index, monthly["plan_revenue"], color="#e07b39", ls=":", lw=2.5, label="План")
ax.set_ylabel("млн ₽"); ax.legend(frameon=False); ax.grid(axis="y", alpha=.25)
ax.spines[["top", "right"]].set_visible(False)
plt.xticks(rotation=60, fontsize=8); plt.tight_layout()
buf = io.BytesIO(); fig.savefig(buf, format="png"); plt.close(fig)
chart = base64.b64encode(buf.getvalue()).decode()

best = reg["Выполнение_плана_проц"].idxmax()
worst = reg["Выполнение_плана_проц"].idxmin()
now = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")

html = f"""<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Отчёт CEO {last}</title>
<style>
body{{font:15px/1.5 "Segoe UI",Roboto,Arial,sans-serif;max-width:960px;margin:24px auto;padding:0 16px;color:#1d2433;background:#fff}}
h1{{font-size:24px;margin-bottom:0}} .meta{{color:#6b7385;margin-bottom:20px}}
table{{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}}
th,td{{border-bottom:1px solid #e3e6ec;padding:6px 8px;text-align:right}} th:first-child,td:first-child{{text-align:left}}
th{{background:#f4f5f7}} .box{{background:#f4f5f7;border-radius:8px;padding:12px 16px}}
img{{max-width:100%}}
</style></head><body>
<h1>Ежемесячный отчёт для CEO — {last}</h1>
<div class="meta">Сформирован автоматически: {now} · источник: data/processed/kpi_clean.csv</div>
<div class="box">
<p><b>Выручка:</b> {rev/1e6:,.1f} млн ₽ ({(rev/rev_prev-1)*100:+.1f} % к {prev}, {(rev/rev_y-1)*100:+.1f} % к {yago}).<br>
<b>Выполнение плана:</b> {rev/plan*100:.1f} %. <b>EBITDA:</b> {ebitda/1e6:,.1f} млн ₽ (маржа {ebitda/rev*100:.1f} %).<br>
<b>Лучший регион по плану:</b> {best}; <b>требует внимания:</b> {worst}.</p></div>
<h2>Динамика выручки</h2><img src="data:image/png;base64,{chart}" alt="Динамика выручки">
<h2>Регионы, {last}</h2>
{reg.rename(columns=lambda c: c.replace("_проц", ", %").replace("_млн", ", млн ₽").replace("_", " ")).rename_axis("Регион").to_html(border=0)}
<p><a href="index.html">Открыть интерактивный дашборд →</a></p>
</body></html>"""
with open("docs/report.html", "w", encoding="utf-8") as fh:
    fh.write(html)
print(f"Отчёт за {last} сохранён -> docs/report.html")
print(f"Выручка {rev/1e6:,.1f} млн ₽, план {rev/plan*100:.1f} %, EBITDA {ebitda/1e6:,.1f} млн ₽")
