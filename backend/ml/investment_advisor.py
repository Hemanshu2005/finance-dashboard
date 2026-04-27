import numpy as np
import pandas as pd
import yfinance as yf
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime
from backend.api.models.database import Transaction, Paycheck


class InvestmentAdvisor:
    """
    Combines personal finance health metrics with stock technical signals
    to suggest optimal investment timing and sizing.
    """

    def suggest(self, user_id: int, ticker: str, db: Session) -> dict:
        finance_score = self._finance_health_score(user_id, db)
        stock_signals = self._stock_signals(ticker)
        recommendation = self._build_recommendation(finance_score, stock_signals, ticker)
        return {
            "ticker": ticker,
            "finance_health_score": finance_score,
            "stock_signals": stock_signals,
            "recommendation": recommendation,
        }

    def _finance_health_score(self, user_id: int, db: Session) -> dict:
        now = datetime.utcnow()
        year, mo = now.year, now.month

        income = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == user_id,
                Transaction.is_income == True,
                extract("year", Transaction.date) == year,
                extract("month", Transaction.date) == mo,
            )
            .scalar() or 0.0
        )
        expenses = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == user_id,
                Transaction.is_income == False,
                extract("year", Transaction.date) == year,
                extract("month", Transaction.date) == mo,
            )
            .scalar() or 0.0
        )

        if income == 0:
            return {"score": 0, "reason": "No income data available", "investable_surplus": 0.0}

        savings_rate = (income - expenses) / income
        surplus = income - expenses
        score = min(100, max(0, int(savings_rate * 100 * 1.5)))

        return {
            "score": score,
            "savings_rate_pct": round(savings_rate * 100, 1),
            "investable_surplus": round(max(0, surplus * 0.5), 2),
            "reason": self._score_reason(score),
        }

    def _stock_signals(self, ticker: str) -> dict:
        hist = yf.Ticker(ticker).history(period="3mo")
        if hist.empty:
            return {"error": "No price data available"}

        close = hist["Close"]
        sma_20 = float(close.rolling(20).mean().iloc[-1])
        sma_50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
        current = float(close.iloc[-1])

        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss
        rsi = float((100 - (100 / (1 + rs))).iloc[-1])

        trend = "bullish" if current > sma_20 else "bearish"
        rsi_signal = "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral"

        volatility = float(close.pct_change().std() * np.sqrt(252) * 100)

        return {
            "current_price": round(current, 2),
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2) if sma_50 else None,
            "rsi_14": round(rsi, 1),
            "trend": trend,
            "rsi_signal": rsi_signal,
            "annualized_volatility_pct": round(volatility, 1),
        }

    def _build_recommendation(self, health: dict, signals: dict, ticker: str) -> dict:
        if "error" in signals or health.get("score", 0) == 0:
            return {"action": "hold", "reason": "Insufficient data to make a recommendation"}

        score = health["score"]
        trend = signals.get("trend", "bearish")
        rsi_signal = signals.get("rsi_signal", "neutral")
        surplus = health.get("investable_surplus", 0)

        if score >= 60 and trend == "bullish" and rsi_signal != "overbought":
            action = "buy"
            reason = f"Strong financial health (score {score}) and bullish price trend. Consider investing up to ${surplus:.2f}."
        elif score < 40:
            action = "hold"
            reason = f"Financial health score {score} is low. Build savings buffer before investing."
        elif rsi_signal == "overbought":
            action = "wait"
            reason = f"{ticker} is currently overbought (RSI {signals['rsi_14']:.0f}). Wait for a pullback."
        else:
            action = "hold"
            reason = "Conditions are neutral. Monitor your spending trend and revisit next month."

        return {
            "action": action,
            "reason": reason,
            "suggested_amount": round(surplus * 0.3, 2) if action == "buy" else 0,
        }

    def _score_reason(self, score: int) -> str:
        if score >= 70:
            return "Excellent savings rate — you have room to invest"
        if score >= 50:
            return "Healthy finances — moderate investment capacity"
        if score >= 30:
            return "Spending is close to income — reduce discretionary expenses first"
        return "Expenses exceed or match income — focus on budgeting before investing"
