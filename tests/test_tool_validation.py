from tradingagents.utils.tool_validation import validate_tool_parameters


def test_validate_stock_tool_parameters_sanitizes_html_and_symbol():
    params = {
        "symbol": "<b>reliance.ns</b>",
        "start_date": "2026-05-01",
        "end_date": "2026-05-06",
    }
    out = validate_tool_parameters("get_stock_data", params)
    assert out["symbol"] == "RELIANCE.NS"
    assert out["start_date"] == "2026-05-01"
    assert out["end_date"] == "2026-05-06"


def test_validate_stock_tool_parameters_rejects_bad_dates():
    params = {
        "symbol": "TCS",
        "start_date": "2026/05/01",
        "end_date": "invalid",
    }
    out = validate_tool_parameters("get_stock_data", params)
    assert out["symbol"] == "TCS"
    assert "start_date" not in out
    assert "end_date" not in out
