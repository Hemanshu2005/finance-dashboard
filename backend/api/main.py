from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import transactions, stocks, budget, insights

app = FastAPI(
    title="Finance Dashboard API",
    description="Personal finance tracking, stock watchlist, and AI-powered investment insights",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(stocks.router, prefix="/api/stocks", tags=["Stocks"])
app.include_router(budget.router, prefix="/api/budget", tags=["Budget"])
app.include_router(insights.router, prefix="/api/insights", tags=["Insights"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
