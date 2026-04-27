from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from backend.api.models.database import get_db, Transaction, SpendingCategory

router = APIRouter()


class TransactionCreate(BaseModel):
    amount: float
    category: SpendingCategory
    merchant: Optional[str] = None
    description: Optional[str] = None
    date: datetime
    is_income: bool = False


class TransactionOut(TransactionCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True


@router.get("/", response_model=List[TransactionOut])
def get_transactions(
    user_id: int,
    month: Optional[str] = None,
    category: Optional[SpendingCategory] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Transaction).filter(Transaction.user_id == user_id)
    if month:
        year, mo = map(int, month.split("-"))
        query = query.filter(
            extract("year", Transaction.date) == year,
            extract("month", Transaction.date) == mo,
        )
    if category:
        query = query.filter(Transaction.category == category)
    return query.order_by(Transaction.date.desc()).all()


@router.post("/", response_model=TransactionOut, status_code=201)
def create_transaction(
    user_id: int,
    payload: TransactionCreate,
    db: Session = Depends(get_db),
):
    tx = Transaction(user_id=user_id, **payload.model_dump())
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.get("/summary")
def monthly_summary(user_id: int, month: str, db: Session = Depends(get_db)):
    year, mo = map(int, month.split("-"))
    rows = (
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
    return {row.category: round(row.total, 2) for row in rows}


@router.get("/paycheck-split")
def paycheck_split(user_id: int, month: str, db: Session = Depends(get_db)):
    """
    Returns recommended vs actual spend per category as a % of monthly income.
    50/30/20 rule applied as default allocation.
    """
    year, mo = map(int, month.split("-"))
    income = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == user_id,
            Transaction.is_income == True,
            extract("year", Transaction.date) == year,
            extract("month", Transaction.date) == mo,
        )
        .scalar()
        or 0.0
    )

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

    actual = {row.category: row.total for row in spending}
    recommended = {
        "needs": round(income * 0.50, 2),
        "wants": round(income * 0.30, 2),
        "savings_investments": round(income * 0.20, 2),
    }

    return {
        "monthly_income": round(income, 2),
        "recommended_split": recommended,
        "actual_spending": {k: round(v, 2) for k, v in actual.items()},
    }
