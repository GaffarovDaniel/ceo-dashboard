"""ПР №8. Диаграмма сгорания задач по выгрузке задач проекта (project/tasks.csv)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

t = pd.read_csv("project/tasks.csv", parse_dates=["created", "closed"])
days = pd.date_range("2026-10-05", "2026-11-04")
total = t["points"].sum()
remaining = [total - t.loc[t["closed"] <= d, "points"].sum() for d in days]
ideal = [total - total * i / (len(days) - 1) for i in range(len(days))]

fig, ax = plt.subplots(figsize=(9, 4), dpi=130)
ax.plot(days, ideal, "--", color="#9aa1ae", label="Идеальная линия")
ax.step(days, remaining, where="post", color="#2457d6", lw=2.5, label="Осталось (story points)")
ax.fill_between(days, remaining, step="post", alpha=.08, color="#2457d6")
ax.set_title("Диаграмма сгорания задач: проект «Дашборд для CEO»", loc="left", fontsize=12)
ax.set_ylabel("Story points"); ax.grid(alpha=.25); ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
fig.autofmt_xdate(); plt.tight_layout()
fig.savefig("project/burndown.png")

print(f"Задач: {len(t)}, всего story points: {total}")
print(t.groupby("label")["points"].sum().sort_values(ascending=False).to_string())
lead = (t["closed"] - t["created"]).dt.days
print(f"Среднее время выполнения задачи: {lead.mean():.1f} дн. (медиана {lead.median():.0f})")
print("Диаграмма сохранена -> project/burndown.png")
