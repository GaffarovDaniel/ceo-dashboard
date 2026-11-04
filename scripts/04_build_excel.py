"""ПР №4. Рабочая книга Excel с формулами: очищенные данные, статистика, сводная, диаграмма."""
import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

df = pd.read_csv("data/processed/kpi_clean.csv")
cols = ["month", "region", "revenue", "plan_revenue", "cogs", "opex", "orders",
        "active_clients", "new_clients", "churned_clients", "nps"]
ru = ["Месяц", "Регион", "Выручка", "План", "Себестоимость", "Опер. расходы", "Заказы",
      "Активные клиенты", "Новые клиенты", "Ушедшие клиенты", "NPS",
      "Валовая прибыль", "EBITDA", "Маржа EBITDA, %", "Выполнение плана, %"]
H = Font(bold=True, color="FFFFFF"); HF = PatternFill("solid", fgColor="2457D6")
thin = Border(bottom=Side(style="thin", color="D0D4DC"))
money = '#,##0'

wb = Workbook()
ws = wb.active; ws.title = "Данные"
ws.append(ru)
for i, r in enumerate(df[cols].itertuples(index=False), start=2):
    ws.append(list(r))
    ws[f"L{i}"] = f"=C{i}-E{i}"
    ws[f"M{i}"] = f"=L{i}-F{i}"
    ws[f"N{i}"] = f"=ROUND(M{i}/C{i}*100,1)"
    ws[f"O{i}"] = f"=ROUND(C{i}/D{i}*100,1)"
n = len(df) + 1
for c in ws[1]: c.font, c.fill, c.alignment = H, HF, Alignment(wrap_text=True, vertical="center")
for row in ws.iter_rows(min_row=2, max_row=n):
    for c in row[2:6] + row[11:13]: c.number_format = money
widths = [10, 17, 14, 14, 14, 14, 9, 10, 10, 10, 7, 14, 13, 10, 11]
for i, w in enumerate(widths, 1): ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = "C2"; ws.auto_filter.ref = f"A1:O{n}"

# --- Статистика ---
st = wb.create_sheet("Статистика")
st.append(["Показатель", "Выручка", "EBITDA", "Маржа EBITDA, %", "NPS"])
src = {"Выручка": "C", "EBITDA": "M", "Маржа EBITDA, %": "N", "NPS": "K"}
for name, fn in [("Среднее", "AVERAGE"), ("Медиана", "MEDIAN"), ("Ст. отклонение", "STDEV"),
                 ("Минимум", "MIN"), ("Максимум", "MAX"), ("Сумма", "SUM")]:
    st.append([name] + [f"={fn}(Данные!{c}2:{c}{n})" for c in src.values()])
st.append(["Коэф. вариации, %"] + [f"=ROUND(B4/B2*100,1)", f"=ROUND(C4/C2*100,1)",
                                    f"=ROUND(D4/D2*100,1)", f"=ROUND(E4/E2*100,1)"])
for c in st[1]: c.font, c.fill = H, HF
for row in st.iter_rows(min_row=2, max_row=7, min_col=2, max_col=3):
    for c in row: c.number_format = money
for row in st.iter_rows(min_row=2, max_row=8, min_col=4, max_col=5):
    for c in row: c.number_format = '0.0'
for i, w in enumerate([20, 16, 16, 16, 10], 1): st.column_dimensions[get_column_letter(i)].width = w

# --- Сводная по регионам (СУММЕСЛИМН) ---
sv = wb.create_sheet("Регионы")
sv.append(["Регион", "Выручка", "План", "EBITDA", "Выполнение плана, %", "Маржа EBITDA, %", "Доля выручки, %"])
regions = sorted(df["region"].unique())
for i, reg in enumerate(regions, start=2):
    sv.append([reg,
               f'=SUMIFS(Данные!$C$2:$C${n},Данные!$B$2:$B${n},A{i})',
               f'=SUMIFS(Данные!$D$2:$D${n},Данные!$B$2:$B${n},A{i})',
               f'=SUMIFS(Данные!$M$2:$M${n},Данные!$B$2:$B${n},A{i})',
               f'=ROUND(B{i}/C{i}*100,1)', f'=ROUND(D{i}/B{i}*100,1)',
               f'=ROUND(B{i}/SUM($B$2:$B${len(regions)+1})*100,1)'])
t = len(regions) + 2
sv.append(["Итого", f"=SUM(B2:B{t-1})", f"=SUM(C2:C{t-1})", f"=SUM(D2:D{t-1})",
           f"=ROUND(B{t}/C{t}*100,1)", f"=ROUND(D{t}/B{t}*100,1)", "=100"])
for c in sv[1]: c.font, c.fill, c.alignment = H, HF, Alignment(wrap_text=True)
for c in sv[t]: c.font = Font(bold=True)
for row in sv.iter_rows(min_row=2, max_row=t, min_col=2, max_col=4):
    for c in row: c.number_format = money
for i, w in enumerate([18, 16, 16, 15, 12, 12, 12], 1): sv.column_dimensions[get_column_letter(i)].width = w

ch = BarChart(); ch.title = "Выручка и EBITDA по регионам, ₽"; ch.height, ch.width = 7.5, 16
ch.add_data(Reference(sv, min_col=2, min_row=1, max_row=t - 1), titles_from_data=True)
ch.add_data(Reference(sv, min_col=4, min_row=1, max_row=t - 1), titles_from_data=True)
ch.set_categories(Reference(sv, min_col=1, min_row=2, max_row=t - 1))
sv.add_chart(ch, "A9")

# --- Динамика по месяцам ---
dm = wb.create_sheet("Динамика")
dm.append(["Месяц", "Выручка", "План", "Выполнение, %"])
months = sorted(df["month"].unique())
for i, m in enumerate(months, start=2):
    dm.append([m, f'=SUMIFS(Данные!$C$2:$C${n},Данные!$A$2:$A${n},A{i})',
               f'=SUMIFS(Данные!$D$2:$D${n},Данные!$A$2:$A${n},A{i})', f'=ROUND(B{i}/C{i}*100,1)'])
for c in dm[1]: c.font, c.fill = H, HF
for row in dm.iter_rows(min_row=2, max_row=len(months) + 1, min_col=2, max_col=3):
    for c in row: c.number_format = money
for i, w in enumerate([10, 16, 16, 13], 1): dm.column_dimensions[get_column_letter(i)].width = w
lc = LineChart(); lc.title = "Выручка: факт и план по месяцам"; lc.height, lc.width = 8, 18
lc.add_data(Reference(dm, min_col=2, max_col=3, min_row=1, max_row=len(months) + 1), titles_from_data=True)
lc.set_categories(Reference(dm, min_col=1, min_row=2, max_row=len(months) + 1))
dm.add_chart(lc, "F2")

for sh in wb.worksheets:                       # печать: альбомная, по ширине страницы
    sh.page_setup.orientation = "landscape"
    sh.page_setup.fitToWidth, sh.page_setup.fitToHeight = 1, 0
    sh.sheet_properties.pageSetUpPr.fitToPage = True
wb.save("excel/ceo_kpi_analysis.xlsx")
print("Книга сохранена -> excel/ceo_kpi_analysis.xlsx")
