import pytest

pytest.importorskip("yfinance")
from backend import recommender


def test_recommend_includes_provenance_fields(monkeypatch):
    monkeypatch.setattr(recommender, "_refresh_active_weights", lambda: None)
    monkeypatch.setattr(recommender, "UNIVERSES", {"nifty100": ["AAA", "BBB"]})
    monkeypatch.setattr(recommender, "get_config", lambda: {"free_tier_mode": True})

    def fake_analyze(ticker):
        return {
            "ticker": ticker,
            "symbol": f"{ticker}.NS",
            "price": 100.0,
            "change_pct": 1.0,
            "rsi": 55.0,
            "score": 4.2,
            "direction": "STRONG BUY",
            "confidence": "HIGH",
            "success_probability": 72,
            "signals": [{"type": "Breakout (Volume Confirmed)", "direction": "BULLISH", "value": "x", "weight": 3.0}],
            "bullish_signal_count": 4,
            "bearish_signal_count": 0,
            "near_support": 95.0,
            "near_resistance": 110.0,
            "decision_source": "deterministic_rule_engine",
        }

    monkeypatch.setattr(recommender, "_analyze_stock", fake_analyze)
    result = recommender.recommend(universe="nifty100", min_signals=1, apply_market_bias=False, apply_event_filter=False, apply_concentration_check=False)
    assert result["decision_source"] == "deterministic_rule_engine"
    assert result["free_tier_mode"] is True
