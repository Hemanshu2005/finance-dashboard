from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.api.models.database import get_db
from backend.ml.spending_analyzer import SpendingAnalyzer
from backend.ml.investment_advisor import InvestmentAdvisor

router = APIRouter()
analyzer = SpendingAnalyzer()
advisor = InvestmentAdvisor()


@router.get("/spending-patterns/{user_id}")
def spending_patterns(user_id: int, months_back: int = 3, db: Session = Depends(get_db)):
    return analyzer.analyze(user_id, months_back, db)


@router.get("/investment-readiness/{user_id}")
def investment_readiness(user_id: int, ticker: str, db: Session = Depends(get_db)):
    return advisor.suggest(user_id, ticker, db)


@router.get("/paycheck-allocation/{user_id}")
def paycheck_allocation(user_id: int, month: str, db: Session = Depends(get_db)):
    return analyzer.paycheck_allocation(user_id, month, db)
