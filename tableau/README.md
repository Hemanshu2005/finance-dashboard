# Tableau Dashboards

Three Tableau dashboards built on top of the dbt-transformed PostgreSQL views.

---

## Dashboard 1 — Monthly Spending Overview

**Data source:** `monthly_spending` (dbt materialized table)

**Sheets:**
- Bar chart: total spend per category per month (grouped)
- Line chart: month-over-month spending trend per category
- KPI tiles: total monthly spend, largest single transaction, transaction count
- Heat map: day-of-week vs category spend intensity

**Filters:** User, Month range, Category

---

## Dashboard 2 — Budget vs Actual

**Data source:** `budget_vs_actual` (dbt view)

**Sheets:**
- Bullet chart: budget limit vs actual spend per category
- Gauge indicators: utilization % per category (green < 80%, amber 80–100%, red > 100%)
- Table: remaining budget per category with over-budget flag
- Trend line: budget utilization month-over-month

**Filters:** User, Month, Category

---

## Dashboard 3 — Savings Rate & Financial Health

**Data source:** `savings_rate` (dbt view) + `stock_prices` table

**Sheets:**
- Line chart: monthly savings rate % over time
- Area chart: income vs expenses stacked
- Scatter: savings rate vs stock watchlist performance (correlation view)
- KPI: average savings rate (3-month rolling)

**Filters:** User, Date range

---

## Connecting Tableau

### Option A — Tableau Desktop (direct PostgreSQL)
1. Open Tableau Desktop
2. Connect → PostgreSQL
3. Host: your AWS RDS endpoint
4. Database: `finance_db`
5. Use the dbt views directly: `monthly_spending`, `savings_rate`, `budget_vs_actual`

### Option B — Tableau Public (CSV export)
```bash
# From project root
python tableau/export_for_tableau.py
# Outputs CSVs to tableau/data/
# Open Tableau Public → Connect to Text File → select CSV
```

---

## Publishing to Tableau Public
1. Build dashboards in Tableau Public Desktop (free)
2. Server → Tableau Public → Save to Tableau Public
3. Embed the public URL in the React frontend or link from the README
