"""
TDD tests for InvestmentAdvisor.

Contracts:
  - Returns finance health score, stock signals, and recommendation
  - Suggested investment amount is non-negative
  - Action is one of: buy, hold, wait
  - Healthy finances + bullish trend → buy recommendation
  - Poor finances → hold regardless of stock signal
  - No income data → score of 0 with descriptive reason
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backend.ml.investment_advisor import InvestmentAdvisor


@pytest.fixture
def advisor():
    return InvestmentAdvisor()


VALID_ACTIONS = {"buy", "hold", "wait"}


def test_suggest_returns_required_keys(advisor, db, sample_transactions):
    with patch("backend.ml.investment_advisor.yf.Ticker") as mock_ticker:
        _mock_yf(mock_ticker)
        result = advisor.suggest(user_id=1, ticker="AAPL", db=db)
    for key in ["ticker", "finance_health_score", "stock_signals", "recommendation"]:
        assert key in result


def test_recommendation_action_is_valid(advisor, db, sample_transactions):
    with patch("backend.ml.investment_advisor.yf.Ticker") as mock_ticker:
        _mock_yf(mock_ticker)
        result = advisor.suggest(user_id=1, ticker="AAPL", db=db)
    assert result["recommendation"]["action"] in VALID_ACTIONS


def test_suggested_amount_non_negative(advisor, db, sample_transactions):
    with patch("backend.ml.investment_advisor.yf.Ticker") as mock_ticker:
        _mock_yf(mock_ticker)
        result = advisor.suggest(user_id=1, ticker="AAPL", db=db)
    assert result["recommendation"]["suggested_amount"] >= 0


def test_no_income_gives_zero_score(advisor, db, test_user):
    with patch("backend.ml.investment_advisor.yf.Ticker") as mock_ticker:
        _mock_yf(mock_ticker)
        result = advisor.suggest(user_id=999, ticker="AAPL", db=db)
    assert result["finance_health_score"]["score"] == 0


def test_score_bounded_zero_to_one_hundred(advisor, db, sample_transactions):
    with patch("backend.ml.investment_advisor.yf.Ticker") as mock_ticker:
        _mock_yf(mock_ticker)
        result = advisor.suggest(user_id=1, ticker="AAPL", db=db)
    score = result["finance_health_score"]["score"]
    assert 0 <= score <= 100


def _mock_yf(mock_ticker):
    dates = pd.date_range(end=datetime.utcnow(), periods=60, freq="D")
    prices = 150 + np.cumsum(np.random.randn(60))
    hist = pd.DataFrame({"Close": prices, "Open": prices - 1, "High": prices + 2, "Low": prices - 2}, index=dates)
    instance = MagicMock()
    instance.history.return_value = hist
    instance.info = {"fiftyTwoWeekHigh": 200.0, "fiftyTwoWeekLow": 120.0}
    mock_ticker.return_value = instance
