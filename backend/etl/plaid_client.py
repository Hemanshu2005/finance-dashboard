import os
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from datetime import datetime, timedelta
from typing import List, Dict

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID", "")
PLAID_SECRET = os.getenv("PLAID_SECRET", "")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")

_ENV_HOSTS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com",
}


def _get_client() -> plaid_api.PlaidApi:
    configuration = Configuration(
        host=_ENV_HOSTS.get(PLAID_ENV, _ENV_HOSTS["sandbox"]),
        api_key={"clientId": PLAID_CLIENT_ID, "secret": PLAID_SECRET},
    )
    return plaid_api.PlaidApi(ApiClient(configuration))


def fetch_transactions(access_token: str, days_back: int = 30) -> List[Dict]:
    client = _get_client()
    end = datetime.utcnow().date()
    start = (datetime.utcnow() - timedelta(days=days_back)).date()

    request = TransactionsGetRequest(
        access_token=access_token,
        start_date=start,
        end_date=end,
        options=TransactionsGetRequestOptions(count=500),
    )
    response = client.transactions_get(request)
    return [_normalize(t) for t in response.transactions]


def _normalize(txn) -> Dict:
    return {
        "plaid_transaction_id": txn.transaction_id,
        "amount": abs(txn.amount),
        "is_income": txn.amount < 0,
        "merchant": txn.merchant_name or txn.name,
        "date": txn.date,
        "category": _map_category(txn.category or []),
    }


def _map_category(plaid_categories: List[str]) -> str:
    cat_map = {
        "Food and Drink": "food",
        "Travel": "transport",
        "Entertainment": "entertainment",
        "Healthcare": "health",
        "Shops": "other",
        "Transfer": "savings",
        "Payment": "other",
        "Recreation": "entertainment",
    }
    for c in plaid_categories:
        for key, val in cat_map.items():
            if key.lower() in c.lower():
                return val
    return "other"
