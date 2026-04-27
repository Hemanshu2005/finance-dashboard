"""
Shared fixtures for Finance Dashboard TDD test suite.
Fixtures define the data contracts each module must satisfy.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.api.models.database import Base, Transaction, Budget, Paycheck, User, StockWatchlist


# ---------------------------------------------------------------------------
# In-memory SQLite DB for testing (mirrors PostgreSQL schema)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def db(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def test_user(db):
    user = User(id=1, email="test@example.com", name="Test User")
    db.merge(user)
    db.commit()
    return user


# ---------------------------------------------------------------------------
# Transaction fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_transactions(db, test_user):
    now = datetime.utcnow()
    txns = [
        Transaction(user_id=1, amount=1200.0, category="food", date=now - timedelta(days=5), is_income=False, merchant="Superstore"),
        Transaction(user_id=1, amount=500.0, category="transport", date=now - timedelta(days=10), is_income=False, merchant="Transit"),
        Transaction(user_id=1, amount=3000.0, category="housing", date=now - timedelta(days=2), is_income=False, merchant="Rent"),
        Transaction(user_id=1, amount=5000.0, category="other", date=now - timedelta(days=1), is_income=True, merchant="Employer"),
    ]
    for t in txns:
        db.add(t)
    db.commit()
    return txns


@pytest.fixture
def high_spend_transaction(db, test_user):
    txn = Transaction(
        user_id=1, amount=9999.0, category="entertainment",
        date=datetime.utcnow(), is_income=False, merchant="Anomaly Store"
    )
    db.add(txn)
    db.commit()
    return txn


@pytest.fixture
def paycheck(db, test_user):
    p = Paycheck(user_id=1, amount=5000.0, date=datetime.utcnow(), source="Employer")
    db.add(p)
    db.commit()
    return p


# ---------------------------------------------------------------------------
# Budget fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_budget(db, test_user):
    now = datetime.utcnow()
    month = f"{now.year}-{now.month:02d}"
    b = Budget(user_id=1, category="food", monthly_limit=1500.0, month=month)
    db.add(b)
    db.commit()
    return b


# ---------------------------------------------------------------------------
# Stock data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_stock_history():
    dates = pd.date_range(end=datetime.utcnow(), periods=60, freq="D")
    prices = 150 + np.cumsum(np.random.randn(60))
    return pd.DataFrame({"Date": dates, "Close": prices, "Open": prices - 1, "High": prices + 2, "Low": prices - 2, "Volume": np.random.randint(1e6, 5e6, 60)})


@pytest.fixture
def watchlist_entry(db, test_user):
    entry = StockWatchlist(user_id=1, ticker="AAPL", target_price=200.0)
    db.add(entry)
    db.commit()
    return entry
