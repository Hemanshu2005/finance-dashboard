import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import extract, func
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
from backend.api.models.database import Transaction, Paycheck


class SpendingAnalyzer:

    def analyze(self, user_id: int, months_back: int, db: Session) -> dict:
        df = self._load_transactions(user_id, months_back, db)
        if df.empty:
            return {"message": "Not enough data"}

        monthly_totals = df.groupby(["month", "category"])["amount"].sum().reset_index()
        trend = self._compute_trend(monthly_totals)
        anomalies = self._detect_anomalies(df)
        top_merchants = self._top_merchants(df)

        return {
            "monthly_category_totals": monthly_totals.to_dict(orient="records"),
            "trend_by_category": trend,
            "anomalies": anomalies,
            "top_merchants": top_merchants,
        }

    def paycheck_allocation(self, user_id: int, month: str, db: Session) -> dict:
        year, mo = map(int, month.split("-"))
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
        if income == 0:
            return {"message": "No income recorded for this month"}

        spending = (
            db.query(Transaction.category, func.sum(Transaction.amount).label("total"))
            .filter(
                Transaction.user_id == user_id,
                Transaction.is_income == False,
                extract("year", Transaction.date) == year,
                extract("month", Transaction.date) == mo,
            )
            .group_by(Transaction.category)
            .all()
        )

        actual_pct = {row.category: round((row.total / income) * 100, 1) for row in spending}
        return {
            "monthly_income": round(income, 2),
            "actual_allocation_pct": actual_pct,
            "recommended_50_30_20": {
                "needs_50pct": round(income * 0.50, 2),
                "wants_30pct": round(income * 0.30, 2),
                "savings_20pct": round(income * 0.20, 2),
            },
        }

    def _load_transactions(self, user_id: int, months_back: int, db: Session) -> pd.DataFrame:
        rows = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id, Transaction.is_income == False)
            .all()
        )
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame([{
            "amount": r.amount,
            "category": str(r.category),
            "merchant": r.merchant,
            "date": r.date,
        } for r in rows])
        df["month"] = df["date"].dt.to_period("M").astype(str)
        cutoff = pd.Timestamp.utcnow() - pd.DateOffset(months=months_back)
        return df[df["date"] >= cutoff]

    def _compute_trend(self, monthly_totals: pd.DataFrame) -> dict:
        trends = {}
        for cat, group in monthly_totals.groupby("category"):
            if len(group) < 2:
                continue
            X = np.arange(len(group)).reshape(-1, 1)
            y = group["amount"].values
            model = LinearRegression().fit(X, y)
            trends[cat] = {
                "slope": round(float(model.coef_[0]), 2),
                "direction": "increasing" if model.coef_[0] > 0 else "decreasing",
            }
        return trends

    def _detect_anomalies(self, df: pd.DataFrame) -> list:
        anomalies = []
        for cat, group in df.groupby("category"):
            mean = group["amount"].mean()
            std = group["amount"].std()
            if std == 0:
                continue
            outliers = group[np.abs(group["amount"] - mean) > 2 * std]
            for _, row in outliers.iterrows():
                anomalies.append({
                    "category": cat,
                    "amount": round(row["amount"], 2),
                    "merchant": row["merchant"],
                    "date": str(row["date"].date()),
                    "z_score": round((row["amount"] - mean) / std, 2),
                })
        return anomalies

    def _top_merchants(self, df: pd.DataFrame, top_n: int = 5) -> list:
        return (
            df.groupby("merchant")["amount"]
            .sum()
            .sort_values(ascending=False)
            .head(top_n)
            .reset_index()
            .rename(columns={"amount": "total_spent"})
            .to_dict(orient="records")
        )
