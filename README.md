# Finance Dashboard

![CI](https://github.com/Hemanshu2005/finance-dashboard/actions/workflows/test.yml/badge.svg)

A full-stack personal finance platform for tracking spending habits, managing budgets, monitoring a stock watchlist, and receiving AI-driven investment timing recommendations — built on a production-grade data engineering stack.

---

## System Architecture

```
Plaid API (bank transactions)
  +  Yahoo Finance (live stock data)
          ↓
   ETL Layer (Python)          — ingest, normalize, load into PostgreSQL
          ↓
  AWS RDS (PostgreSQL)         — transactional data store
          ↓
   dbt Transformations         — monthly_spending, savings_rate, budget_vs_actual views
          ↓
  Apache Airflow DAG           — nightly refresh scheduled at 2am UTC
          ↓
  FastAPI REST API             — serves all dashboard data
          ↓
  ML Layer                     — spending anomaly detection, investment readiness scoring
          ↓
  React Frontend               — interactive dashboard, charts, stock watchlist
          ↓
  AWS S3                       — Parquet archives of historical stock prices
```

---

## Features

### Spending Tracker
- Syncs real bank transactions via **Plaid API** (sandbox + production ready)
- Categorizes spending: housing, food, transport, health, entertainment, savings, investments
- Month-over-month trend analysis using **Linear Regression** per category
- Anomaly detection: flags unusually large transactions via **z-score analysis**
- Top merchant breakdown by monthly spend

### Budget Management
- Set monthly limits per category
- Real-time budget utilization (%) with over-budget alerts
- Powered by **dbt `budget_vs_actual`** view on PostgreSQL

### Paycheck Allocation
- Tracks income vs expenses per month
- Applies **50/30/20 rule**: needs / wants / savings-investments split
- Shows actual vs recommended allocation as percentage of income

### Stock Watchlist
- Search and track any ticker (NYSE, TSX, NASDAQ)
- Live quote: current price, daily change %, 52-week high/low, P/E ratio, market cap
- Price history charts (1mo / 3mo / 6mo / 1y / 2y)
- Set a target price — dashboard alerts when the stock reaches it
- Historical OHLCV data archived to **AWS S3** as Parquet

### AI Investment Advisor
- Combines **personal finance health score** (savings rate, surplus) with **stock technical signals**
- Technical signals: SMA-20, SMA-50, RSI-14, annualized volatility
- Output: `buy / hold / wait` recommendation with suggested dollar amount
- Mirrors risk-adjusted decision frameworks used in wealth management

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.11 |
| **API Framework** | FastAPI + Uvicorn |
| **Database** | PostgreSQL 16 on **AWS RDS** |
| **ORM** | SQLAlchemy + Alembic (migrations) |
| **Data Transforms** | **dbt** (monthly_spending, savings_rate, budget_vs_actual) |
| **Pipeline Orchestration** | **Apache Airflow** (nightly DAG) |
| **Cloud Storage** | **AWS S3** (Parquet archives) |
| **ML / Analytics** | scikit-learn, pandas, numpy |
| **Financial Data** | Plaid API, Yahoo Finance (yfinance) |
| **Containerization** | **Docker** + docker-compose |
| **CI/CD** | **GitHub Actions** (TDD staged pipeline) |
| **Testing** | pytest, TDD with shared fixtures |
| **Frontend** | React (TypeScript) |

---

## Skills Demonstrated

| Skill | Where |
|-------|-------|
| SQL schema design & querying | SQLAlchemy models, dbt SQL models |
| Cloud data engineering (AWS) | RDS, S3, ca-central-1 region |
| ETL pipeline development | Plaid + yfinance → PostgreSQL → S3 |
| Data pipeline orchestration | Apache Airflow DAG with retries |
| REST API development | FastAPI routes: transactions, stocks, budget, insights |
| Machine learning | Regression trend analysis, z-score anomaly detection, RSI |
| Test-Driven Development | pytest + conftest fixtures, 3-stage CI pipeline |
| Docker containerization | Multi-service docker-compose (API + DB + Airflow) |
| Financial data modeling | 50/30/20 rule, savings rate, investment readiness scoring |
| dbt data transformation | Materialized tables and views on PostgreSQL |

---

## Setup

### With Docker (recommended)
```bash
git clone https://github.com/Hemanshu2005/finance-dashboard.git
cd finance-dashboard
cp .env.example .env
# Fill in DATABASE_URL, AWS credentials, Plaid keys
docker compose up --build
```

API available at `http://localhost:8000`
Airflow UI at `http://localhost:8080`
API docs at `http://localhost:8000/docs`

### Without Docker
```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn backend.api.main:app --reload
pytest tests/ -v
```

---

## Project Structure

```
finance-dashboard/
├── .github/workflows/
│   └── test.yml                  # GitHub Actions CI — 3-stage TDD pipeline
├── backend/
│   ├── api/
│   │   ├── main.py               # FastAPI app
│   │   ├── routes/
│   │   │   ├── transactions.py   # Spending CRUD + monthly summary + paycheck split
│   │   │   ├── stocks.py         # Watchlist + live quotes + price history
│   │   │   ├── budget.py         # Budget set/get with utilization tracking
│   │   │   └── insights.py       # ML-powered spending patterns + investment advice
│   │   └── models/
│   │       └── database.py       # SQLAlchemy ORM: User, Transaction, Budget, Stock
│   ├── etl/
│   │   ├── plaid_client.py       # Plaid API transaction sync
│   │   └── stock_fetcher.py      # yfinance → PostgreSQL + S3 Parquet archive
│   └── ml/
│       ├── spending_analyzer.py  # Trend regression, anomaly detection, top merchants
│       └── investment_advisor.py # Finance health score + RSI/SMA signals → recommendation
├── dbt/
│   └── models/
│       ├── monthly_spending.sql  # Materialized table: spend by user/month/category
│       ├── savings_rate.sql      # View: income vs expenses → savings rate %
│       └── budget_vs_actual.sql  # View: budget limits vs real spend
├── airflow/
│   └── dags/
│       └── daily_refresh.py      # Nightly ETL: stocks + Plaid + dbt run
├── tests/
│   ├── conftest.py               # Shared fixtures: in-memory SQLite, sample data
│   ├── test_spending_analyzer.py # TDD: trend, anomalies, paycheck allocation
│   └── test_investment_advisor.py# TDD: health score, signals, recommendation logic
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/transactions/` | List transactions (filterable by month, category) |
| POST | `/api/transactions/` | Add a transaction |
| GET | `/api/transactions/summary` | Monthly spend by category |
| GET | `/api/transactions/paycheck-split` | 50/30/20 rule vs actual allocation |
| GET | `/api/stocks/watchlist` | Get watchlist with live prices |
| POST | `/api/stocks/watchlist` | Add ticker to watchlist |
| GET | `/api/stocks/quote/{ticker}` | Live stock quote |
| GET | `/api/stocks/history/{ticker}` | OHLCV price history |
| GET | `/api/budget/{month}` | Budget utilization per category |
| POST | `/api/budget/` | Set monthly budget limit |
| GET | `/api/insights/spending-patterns/{user_id}` | ML spending analysis |
| GET | `/api/insights/investment-readiness/{user_id}` | AI investment suggestion |

---

## API Keys Required

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| [Plaid](https://plaid.com) | Bank transaction sync | Sandbox: free |
| [AWS](https://aws.amazon.com) | RDS + S3 | Free tier eligible |
| Yahoo Finance | Stock data via yfinance | No key needed |
