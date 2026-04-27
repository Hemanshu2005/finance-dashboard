from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    DateTime, ForeignKey, Enum, Boolean, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import enum

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/finance_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class SpendingCategory(str, enum.Enum):
    HOUSING = "housing"
    FOOD = "food"
    TRANSPORT = "transport"
    ENTERTAINMENT = "entertainment"
    HEALTH = "health"
    SAVINGS = "savings"
    INVESTMENTS = "investments"
    OTHER = "other"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    transactions = relationship("Transaction", back_populates="user")
    budgets = relationship("Budget", back_populates="user")
    watchlist = relationship("StockWatchlist", back_populates="user")
    paychecks = relationship("Paycheck", back_populates="user")


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plaid_transaction_id = Column(String, unique=True, nullable=True)
    amount = Column(Float, nullable=False)
    category = Column(Enum(SpendingCategory), default=SpendingCategory.OTHER)
    merchant = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False)
    is_income = Column(Boolean, default=False)
    user = relationship("User", back_populates="transactions")


class Budget(Base):
    __tablename__ = "budgets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(Enum(SpendingCategory), nullable=False)
    monthly_limit = Column(Float, nullable=False)
    month = Column(String, nullable=False)  # "2025-04"
    user = relationship("User", back_populates="budgets")


class Paycheck(Base):
    __tablename__ = "paychecks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    source = Column(String, nullable=True)
    user = relationship("User", back_populates="paychecks")


class StockWatchlist(Base):
    __tablename__ = "stock_watchlist"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticker = Column(String, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    target_price = Column(Float, nullable=True)
    user = relationship("User", back_populates="watchlist")


class StockPrice(Base):
    __tablename__ = "stock_prices"
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, nullable=False, index=True)
    date = Column(DateTime, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
