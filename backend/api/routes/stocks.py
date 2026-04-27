from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime, timedelta
from backend.api.models.database import get_db, StockWatchlist, StockPrice
import yfinance as yf

router = APIRouter()


class WatchlistAdd(BaseModel):
    ticker: str
    target_price: float = None


class StockInfo(BaseModel):
    ticker: str
    current_price: float
    change_pct: float
    week_52_high: float
    week_52_low: float
    market_cap: float = None
    pe_ratio: float = None


@router.get("/watchlist")
def get_watchlist(user_id: int, db: Session = Depends(get_db)):
    items = db.query(StockWatchlist).filter(StockWatchlist.user_id == user_id).all()
    results = []
    for item in items:
        try:
            info = _fetch_stock_info(item.ticker)
            info["target_price"] = item.target_price
            info["at_target"] = (
                item.target_price is not None
                and info["current_price"] >= item.target_price
            )
            results.append(info)
        except Exception:
            results.append({"ticker": item.ticker, "error": "fetch failed"})
    return results


@router.post("/watchlist", status_code=201)
def add_to_watchlist(user_id: int, payload: WatchlistAdd, db: Session = Depends(get_db)):
    existing = (
        db.query(StockWatchlist)
        .filter(StockWatchlist.user_id == user_id, StockWatchlist.ticker == payload.ticker.upper())
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Ticker already in watchlist")
    entry = StockWatchlist(
        user_id=user_id,
        ticker=payload.ticker.upper(),
        target_price=payload.target_price,
    )
    db.add(entry)
    db.commit()
    return {"message": f"{payload.ticker.upper()} added to watchlist"}


@router.delete("/watchlist/{ticker}")
def remove_from_watchlist(user_id: int, ticker: str, db: Session = Depends(get_db)):
    entry = (
        db.query(StockWatchlist)
        .filter(StockWatchlist.user_id == user_id, StockWatchlist.ticker == ticker.upper())
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Ticker not in watchlist")
    db.delete(entry)
    db.commit()
    return {"message": f"{ticker.upper()} removed"}


@router.get("/quote/{ticker}")
def get_stock_quote(ticker: str):
    try:
        return _fetch_stock_info(ticker.upper())
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/history/{ticker}")
def get_stock_history(ticker: str, period: str = "3mo"):
    valid_periods = ["1mo", "3mo", "6mo", "1y", "2y"]
    if period not in valid_periods:
        raise HTTPException(status_code=400, detail=f"Period must be one of {valid_periods}")
    stock = yf.Ticker(ticker.upper())
    hist = stock.history(period=period)
    return hist.reset_index()[["Date", "Open", "High", "Low", "Close", "Volume"]].to_dict(orient="records")


def _fetch_stock_info(ticker: str) -> dict:
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="2d")
    current = float(hist["Close"].iloc[-1])
    prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current
    change_pct = ((current - prev) / prev) * 100 if prev else 0.0
    return {
        "ticker": ticker,
        "current_price": round(current, 2),
        "change_pct": round(change_pct, 2),
        "week_52_high": info.get("fiftyTwoWeekHigh", 0.0),
        "week_52_low": info.get("fiftyTwoWeekLow", 0.0),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
    }
