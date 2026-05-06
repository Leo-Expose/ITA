import pandas as pd

from tradingagents.utils.rule_based_analysis import create_rule_based_payload


def test_rule_based_payload_has_core_fields():
    rows = []
    price = 100.0
    for i in range(80):
        price += 0.2
        rows.append(
            {
                "Open": price - 0.4,
                "High": price + 0.8,
                "Low": price - 0.8,
                "Close": price,
                "Volume": 100000 + i * 100,
            }
        )
    df = pd.DataFrame(rows)
    payload = create_rule_based_payload("RELIANCE", df)
    assert payload["symbol"] == "RELIANCE"
    assert "confidence" in payload
    assert "entry_exit" in payload
    assert isinstance(payload["buy_signals"], list)
