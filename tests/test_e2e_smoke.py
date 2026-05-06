import os
import pytest

from fastapi.testclient import TestClient

pytest.importorskip("yfinance")
from backend.app import app


RUN_E2E = os.getenv("RUN_E2E", "0") == "1"


@pytest.mark.skipif(not RUN_E2E, reason="Set RUN_E2E=1 to run network-backed smoke tests")
@pytest.mark.parametrize("ticker", ["RELIANCE", "TCS", "HDFCBANK"])
def test_recommend_stock_smoke(ticker: str):
    client = TestClient(app)
    res = client.get(f"/api/recommend/stock/{ticker}")
    assert res.status_code == 200
    payload = res.json()
    assert "error" in payload or "ticker" in payload


def test_market_closed_weekend_check():
    # E2E acceptance: verify closed-day logic is reachable and deterministic.
    from tradingagents.utils.market_calendar import is_trading_day
    import datetime
    # Sunday
    sunday = datetime.date(2026, 5, 10)
    assert is_trading_day(sunday) is False
