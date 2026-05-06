from tradingagents.dataflows.nse_data import get_delivery_percentage, get_bulk_block_deals


def test_delivery_invalid_date_returns_contract():
    out = get_delivery_percentage("RELIANCE", "2026/01/01")
    assert "DATA_UNAVAILABLE" in out


def test_bulk_invalid_date_returns_contract():
    out = get_bulk_block_deals("RELIANCE", "bad-date", "2026-01-01")
    assert "DATA_UNAVAILABLE" in out
