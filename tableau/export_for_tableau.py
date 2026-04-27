"""
Exports PostgreSQL views to CSV for Tableau Public / Tableau Desktop.

Run this script to refresh the CSV data sources that power the Tableau dashboards.
For Tableau Desktop (direct PostgreSQL connection), see tableau/README.md.
"""
import os
import pandas as pd
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/finance_db")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

engine = create_engine(DATABASE_URL)

EXPORTS = {
    "monthly_spending.csv": "SELECT * FROM monthly_spending",
    "savings_rate.csv": "SELECT * FROM savings_rate",
    "budget_vs_actual.csv": "SELECT * FROM budget_vs_actual",
    "transactions.csv": """
        SELECT
            t.id, t.user_id, t.amount, t.category,
            t.merchant, t.date, t.is_income
        FROM transactions t
        ORDER BY t.date DESC
    """,
    "stock_prices.csv": """
        SELECT ticker, date, open, high, low, close, volume
        FROM stock_prices
        ORDER BY ticker, date
    """,
}


def export_all():
    with engine.connect() as conn:
        for filename, query in EXPORTS.items():
            df = pd.read_sql(text(query), conn)
            path = os.path.join(OUTPUT_DIR, filename)
            df.to_csv(path, index=False)
            print(f"Exported {len(df)} rows → {path}")


if __name__ == "__main__":
    export_all()
