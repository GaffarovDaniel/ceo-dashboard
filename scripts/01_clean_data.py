"""
ПР №2/№4. Очистка сырой выгрузки и расчёт производных KPI.
Вход:  data/raw/kpi_raw.csv
Выход: data/processed/kpi_clean.csv
"""
import pandas as pd

RAW = "data/raw/kpi_raw.csv"
OUT = "data/processed/kpi_clean.csv"

df = pd.read_csv(RAW, dtype=str)
n0 = len(df)

# 1. Нормализуем названия регионов: пробелы и регистр
df["region"] = df["region"].str.strip().str.title()

# 2. Убираем дубли
df = df.drop_duplicates()
dups = n0 - len(df)

# 3. Приводим числовые поля к числам ("12 345 678" -> 12345678, "н/д" -> NaN)
num_cols = ["revenue", "plan_revenue", "cogs", "opex", "orders",
            "active_clients", "new_clients", "churned_clients", "nps"]
for c in num_cols:
    df[c] = pd.to_numeric(df[c].str.replace(" ", "", regex=False), errors="coerce")

missing_before = int(df[num_cols].isna().sum().sum())

# 4. Заполняем пропуски: выручку и расходы — через долю от плана/выручки
#    по региону, NPS — медианой региона
df["revenue"] = df["revenue"].fillna(
    df["plan_revenue"] * (df["revenue"] / df["plan_revenue"]).median())
df["opex"] = df["opex"].fillna(df["revenue"] * (df["opex"] / df["revenue"]).median())
df["nps"] = df["nps"].fillna(df.groupby("region")["nps"].transform("median"))

# 5. Производные показатели
df["gross_profit"] = df["revenue"] - df["cogs"]
df["ebitda"] = df["gross_profit"] - df["opex"]
df["gross_margin_pct"] = (df["gross_profit"] / df["revenue"] * 100).round(2)
df["ebitda_margin_pct"] = (df["ebitda"] / df["revenue"] * 100).round(2)
df["avg_check"] = (df["revenue"] / df["orders"]).round(0)
df["churn_rate_pct"] = (df["churned_clients"] / df["active_clients"] * 100).round(2)
df["plan_exec_pct"] = (df["revenue"] / df["plan_revenue"] * 100).round(2)

df = df.sort_values(["month", "region"]).reset_index(drop=True)
df.to_csv(OUT, index=False, encoding="utf-8")

print(f"Строк на входе:          {n0}")
print(f"Удалено дублей:          {dups}")
print(f"Пропусков после парсинга: {missing_before} -> {int(df[num_cols].isna().sum().sum())}")
print(f"Строк на выходе:         {len(df)}")
print(f"Регионы: {', '.join(sorted(df['region'].unique()))}")
print(f"Период:  {df['month'].min()} – {df['month'].max()}")
print(f"Сохранено -> {OUT}")
