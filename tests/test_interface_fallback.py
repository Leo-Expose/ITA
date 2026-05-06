import pytest

pytest.importorskip("yfinance")
from tradingagents.dataflows import interface


def test_route_to_vendor_falls_back_on_primary_failure(monkeypatch):
    def primary(*args, **kwargs):
        raise RuntimeError("primary failed")

    def secondary(*args, **kwargs):
        return "ok-secondary"

    monkeypatch.setitem(
        interface.VENDOR_METHODS,
        "test_method",
        {"primary": primary, "secondary": secondary},
    )
    monkeypatch.setattr(interface, "get_category_for_method", lambda m: "core_stock_apis")
    monkeypatch.setattr(interface, "get_vendor", lambda c, m=None: "primary")

    out = interface.route_to_vendor("test_method", "x")
    assert out == "ok-secondary"
