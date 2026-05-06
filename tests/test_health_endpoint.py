import pytest
from fastapi.testclient import TestClient

pytest.importorskip("yfinance")
from backend.app import app


def test_health_has_metrics_and_flags():
    client = TestClient(app)
    res = client.get("/api/health")
    assert res.status_code == 200
    payload = res.json()
    assert "metrics" in payload
    assert "stale_data_flags" in payload
    assert "status" in payload
