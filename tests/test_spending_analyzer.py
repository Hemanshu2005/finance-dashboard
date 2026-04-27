"""
TDD tests for SpendingAnalyzer.

Contracts:
  - Returns category totals grouped by month
  - Detects anomalous transactions via z-score
  - Computes paycheck allocation as % of income
  - Returns top merchants by spend
  - Handles empty transaction history gracefully
"""
import pytest
from backend.ml.spending_analyzer import SpendingAnalyzer


@pytest.fixture
def analyzer():
    return SpendingAnalyzer()


def test_analyze_returns_required_keys(analyzer, db, sample_transactions):
    result = analyzer.analyze(user_id=1, months_back=3, db=db)
    for key in ["monthly_category_totals", "trend_by_category", "anomalies", "top_merchants"]:
        assert key in result


def test_analyze_empty_history_returns_message(analyzer, db, test_user):
    result = analyzer.analyze(user_id=999, months_back=3, db=db)
    assert "message" in result


def test_monthly_totals_are_positive(analyzer, db, sample_transactions):
    result = analyzer.analyze(user_id=1, months_back=3, db=db)
    for row in result["monthly_category_totals"]:
        assert row["amount"] >= 0


def test_top_merchants_sorted_descending(analyzer, db, sample_transactions):
    result = analyzer.analyze(user_id=1, months_back=3, db=db)
    totals = [m["total_spent"] for m in result["top_merchants"]]
    assert totals == sorted(totals, reverse=True)


def test_paycheck_allocation_returns_income(analyzer, db, sample_transactions):
    from datetime import datetime
    month = f"{datetime.utcnow().year}-{datetime.utcnow().month:02d}"
    result = analyzer.paycheck_allocation(user_id=1, month=month, db=db)
    assert "monthly_income" in result
    assert result["monthly_income"] > 0


def test_paycheck_allocation_recommended_split_sums_to_income(analyzer, db, sample_transactions):
    from datetime import datetime
    month = f"{datetime.utcnow().year}-{datetime.utcnow().month:02d}"
    result = analyzer.paycheck_allocation(user_id=1, month=month, db=db)
    if "recommended_50_30_20" in result:
        split = result["recommended_50_30_20"]
        total = split["needs_50pct"] + split["wants_30pct"] + split["savings_20pct"]
        assert abs(total - result["monthly_income"]) < 0.01


def test_no_income_returns_message(analyzer, db, test_user):
    result = analyzer.paycheck_allocation(user_id=999, month="2025-01", db=db)
    assert "message" in result
