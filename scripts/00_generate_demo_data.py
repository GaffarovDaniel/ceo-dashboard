"""
Генерация учебного (модельного) набора данных для проекта «Дашборд для CEO».
Компания вымышленная: ООО «Вектор Ритейл», 4 региона, период янв 2025 – окт 2026.
В «сырую» выгрузку специально добавлены типичные ошибки учётных систем
(дубли, пропуски, текст в числовых полях, лишние пробелы), чтобы в ПР №4
было что очищать.
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

months = pd.period_range("2025-01", "2026-10", freq="M")
regions = {"Москва": 1.00, "Санкт-Петербург": 0.62, "Екатеринбург": 0.38, "Челябинск": 0.27}
season = {1: 0.82, 2: 0.85, 3: 0.95, 4: 0.97, 5: 1.00, 6: 0.98,
          7: 0.93, 8: 0.96, 9: 1.03, 10: 1.06, 11: 1.15, 12: 1.32}

rows = []
for i, m in enumerate(months):
    trend = 1 + 0.012 * i                     # рост бизнеса ~1,2 % в месяц
    for reg, scale in regions.items():
        base = 48_000_000 * scale * trend * season[m.month]
        revenue = base * rng.normal(1, 0.04)
        plan = 48_000_000 * scale * (1 + 0.013 * i) * season[m.month]
        cogs = revenue * rng.normal(0.61, 0.012)
        opex = revenue * rng.normal(0.22, 0.015)
        orders = int(revenue / rng.normal(3_450, 120))
        active = int(orders * rng.normal(0.71, 0.03))
        new_cl = int(active * rng.normal(0.16, 0.02))
        churned = int(active * rng.normal(0.055, 0.008))
        nps = round(rng.normal(41 + i * 0.35, 3), 1)
        rows.append([str(m), reg, round(revenue), round(plan), round(cogs), round(opex),
                     orders, active, new_cl, churned, nps])

cols = ["month", "region", "revenue", "plan_revenue", "cogs", "opex",
        "orders", "active_clients", "new_clients", "churned_clients", "nps"]
df = pd.DataFrame(rows, columns=cols)

# --- «Загрязняем» выгрузку, как это бывает в реальных системах ---
dirty = df.copy().astype(object)
dirty.loc[4, "region"] = "  москва "          # регистр и пробелы
dirty.loc[17, "revenue"] = "н/д"               # текст в числовом поле
dirty.loc[33, "nps"] = None                    # пропуск
dirty.loc[48, "opex"] = None                   # пропуск
dirty.loc[62, "region"] = "Екатеринбург "      # хвостовой пробел
dirty.loc[71, "revenue"] = f"{df.loc[71, 'revenue']:,}".replace(",", " ")  # «12 345 678»
dirty = pd.concat([dirty, dirty.iloc[[12, 40]]])   # 2 дубля строк
dirty.to_csv("data/raw/kpi_raw.csv", index=False, encoding="utf-8")
print(f"Сырые данные: {len(dirty)} строк, {dirty.shape[1]} столбцов -> data/raw/kpi_raw.csv")
