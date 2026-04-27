from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from pydantic import BaseModel
from backend.api.models.database import get_db, Budget, Transaction, SpendingCategory

router = APIRouter()


class BudgetSet(BaseModel):
    category: SpendingCategory
    monthly_limit: float
    month: str  # "2025-04"


@router.get("/{month}")
def get_budget_status(user_id: int, month: str, db: Session = Depends(get_db)):
    year, mo = map(int, month.split("-"))
    budgets = db.query(Budget).filter(Budget.user_id == user_id, Budget.month == month).all()
    spending = (
        db.query(Transaction.category, func.sum(Transaction.amount).label("spent"))
        .filter(
            Transaction.user_id == user_id,
            Transaction.is_income == False,
            extract("year", Transaction.date) == year,
            extract("month", Transaction.date) == mo,
        )
        .group_by(Transaction.category)
        .all()
    )
    spent_map = {row.category: row.spent for row in spending}

    result = []
    for b in budgets:
        spent = spent_map.get(b.category, 0.0)
        result.append({
            "category": b.category,
            "limit": b.monthly_limit,
            "spent": round(spent, 2),
            "remaining": round(b.monthly_limit - spent, 2),
            "over_budget": spent > b.monthly_limit,
            "utilization_pct": round((spent / b.monthly_limit) * 100, 1) if b.monthly_limit else 0,
        })
    return result


@router.post("/", status_code=201)
def set_budget(user_id: int, payload: BudgetSet, db: Session = Depends(get_db)):
    existing = (
        db.query(Budget)
        .filter(Budget.user_id == user_id, Budget.category == payload.category, Budget.month == payload.month)
        .first()
    )
    if existing:
        existing.monthly_limit = payload.monthly_limit
        db.commit()
        return {"message": "Budget updated"}
    b = Budget(user_id=user_id, **payload.model_dump())
    db.add(b)
    db.commit()
    return {"message": "Budget set"}
