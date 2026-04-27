import os
import boto3
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.api.models.database import StockPrice, SessionLocal

S3_BUCKET = os.getenv("AWS_S3_BUCKET", "finance-dashboard-data")
s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "ca-central-1"))


def fetch_and_store_prices(tickers: list[str], period: str = "1mo") -> pd.DataFrame:
    all_data = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            hist["ticker"] = ticker
            hist = hist.reset_index()
            all_data.append(hist)
        except Exception as e:
            print(f"Failed to fetch {ticker}: {e}")

    if not all_data:
        return pd.DataFrame()

    combined = pd.concat(all_data, ignore_index=True)
    _write_to_db(combined)
    _archive_to_s3(combined)
    return combined


def _write_to_db(df: pd.DataFrame) -> None:
    db: Session = SessionLocal()
    try:
        for _, row in df.iterrows():
            price = StockPrice(
                ticker=row["ticker"],
                date=row["Date"],
                open=row.get("Open"),
                high=row.get("High"),
                low=row.get("Low"),
                close=row.get("Close"),
                volume=row.get("Volume"),
            )
            db.merge(price)
        db.commit()
    finally:
        db.close()


def _archive_to_s3(df: pd.DataFrame) -> None:
    try:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        key = f"stock-prices/{date_str}/prices.parquet"
        buffer = df.to_parquet(index=False)
        s3.put_object(Bucket=S3_BUCKET, Key=key, Body=buffer)
    except Exception as e:
        print(f"S3 archive failed: {e}")


def get_all_watched_tickers() -> list[str]:
    db: Session = SessionLocal()
    try:
        from backend.api.models.database import StockWatchlist
        rows = db.query(StockWatchlist.ticker).distinct().all()
        return [r.ticker for r in rows]
    finally:
        db.close()
