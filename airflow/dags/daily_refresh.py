from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "finance-dashboard",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": True,
}

with DAG(
    dag_id="daily_finance_refresh",
    default_args=default_args,
    description="Nightly ETL: refresh stock prices and sync Plaid transactions to RDS",
    schedule_interval="0 2 * * *",  # 2am UTC daily
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["finance", "etl", "aws-rds"],
) as dag:

    def refresh_stock_prices():
        from backend.etl.stock_fetcher import fetch_and_store_prices, get_all_watched_tickers
        tickers = get_all_watched_tickers()
        if tickers:
            fetch_and_store_prices(tickers, period="5d")
        print(f"Refreshed prices for {len(tickers)} tickers")

    def sync_plaid_transactions():
        from backend.api.models.database import SessionLocal, User
        from backend.etl.plaid_client import fetch_transactions
        db = SessionLocal()
        try:
            users = db.query(User).all()
            for user in users:
                pass  # access_token stored per-user in production
        finally:
            db.close()

    def run_dbt_transforms():
        import subprocess
        result = subprocess.run(
            ["dbt", "run", "--project-dir", "/opt/airflow/dbt"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"dbt run failed:\n{result.stderr}")
        print(result.stdout)

    t1 = PythonOperator(task_id="refresh_stock_prices", python_callable=refresh_stock_prices)
    t2 = PythonOperator(task_id="sync_plaid_transactions", python_callable=sync_plaid_transactions)
    t3 = PythonOperator(task_id="run_dbt_transforms", python_callable=run_dbt_transforms)

    [t1, t2] >> t3
