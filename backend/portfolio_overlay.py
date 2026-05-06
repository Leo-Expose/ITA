"""Portfolio overlay for manual execution.

Transforms a raw recommendation pick into an actionable trade suggestion:
- position sizing (₹ value + shares)
- stop loss + target (mechanical, signal-derived)
- risk per trade and basic warnings

This is intentionally simple and deterministic: it should be predictable,
auditable, and easy to improve once we have more outcome data.
"""

from __future__ import annotations

import math
from typing import Any

from tradingagents.dataflows.config import get_config


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def suggest_trade_overlay(
    pick: dict[str, Any],
    *,
    total_capital_inr: float = 500000.0,
    per_trade_risk_pct: float = 0.005,   # 0.5% of equity
    per_trade_value_pct: float = 0.10,   # 10% of equity
) -> dict[str, Any]:
    """Return a sizing + risk overlay for one recommendation pick."""
    cfg = get_config()
    max_position_value = float(cfg.get("max_position_value", 100000))
    max_loss_per_trade = float(cfg.get("max_loss_per_trade", 5000))

    ticker = pick.get("ticker")
    direction = (pick.get("direction") or "").upper()
    price = float(pick.get("price") or 0)
    near_support = pick.get("near_support")
    near_resistance = pick.get("near_resistance")

    warnings: list[str] = []
    if not price or price <= 0:
        return {
            "ok": False,
            "ticker": ticker,
            "warnings": ["Missing/invalid price; cannot size trade"],
        }

    is_long = direction in ("STRONG BUY", "BUY")
    is_short = direction in ("STRONG SELL", "SELL")
    if not (is_long or is_short):
        return {
            "ok": False,
            "ticker": ticker,
            "warnings": ["Neutral/unknown direction; no trade overlay"],
        }

    # Budgets (capped by absolute safety limits)
    risk_budget_inr = min(total_capital_inr * per_trade_risk_pct, max_loss_per_trade)
    value_budget_inr = min(total_capital_inr * per_trade_value_pct, max_position_value)

    # Stop-loss: use support/resistance if available; otherwise use a conservative % fallback.
    if is_long:
        if isinstance(near_support, (int, float)) and float(near_support) > 0:
            stop_loss = float(near_support) * 0.99
        else:
            stop_loss = price * 0.97
        risk_per_share = price - stop_loss
        if risk_per_share <= 0:
            stop_loss = price * 0.97
            risk_per_share = price - stop_loss
            warnings.append("Support-derived stop invalid; used fallback stop at -3%")
        target_price = price + 2.0 * risk_per_share
        if isinstance(near_resistance, (int, float)) and float(near_resistance) > price:
            # If resistance is close, cap target near it to avoid unrealistic expectations.
            target_price = min(target_price, float(near_resistance) * 0.995)
    else:
        # Short
        if isinstance(near_resistance, (int, float)) and float(near_resistance) > 0:
            stop_loss = float(near_resistance) * 1.01
        else:
            stop_loss = price * 1.03
        risk_per_share = stop_loss - price
        if risk_per_share <= 0:
            stop_loss = price * 1.03
            risk_per_share = stop_loss - price
            warnings.append("Resistance-derived stop invalid; used fallback stop at +3%")
        target_price = price - 2.0 * risk_per_share
        if isinstance(near_support, (int, float)) and float(near_support) < price:
            target_price = max(target_price, float(near_support) * 1.005)

    # Shares: bound by both risk budget and value budget.
    shares_by_value = int(math.floor(value_budget_inr / price))
    shares_by_risk = int(math.floor(risk_budget_inr / risk_per_share)) if risk_per_share > 0 else 0
    shares = max(0, min(shares_by_value, shares_by_risk))

    if shares <= 0:
        warnings.append("Risk/value budgets too small for 1 share with this stop-loss")

    position_value_inr = round(shares * price, 2)
    est_risk_inr = round(shares * risk_per_share, 2)
    rr = (abs(target_price - price) / risk_per_share) if risk_per_share > 0 else None

    # Gentle warnings for extreme cases
    if rr is not None and rr < 1.2:
        warnings.append(f"Low reward:risk (~{rr:.2f}); consider skipping or tightening entry")
    if est_risk_inr > risk_budget_inr * 1.05:
        warnings.append("Estimated risk exceeds budget (unexpected); verify stop/size")

    return {
        "ok": True,
        "ticker": ticker,
        "direction": direction,
        "price": round(price, 2),
        "total_capital_inr": round(total_capital_inr, 2),
        "risk_budget_inr": round(risk_budget_inr, 2),
        "value_budget_inr": round(value_budget_inr, 2),
        "recommended_shares": shares,
        "recommended_position_value_inr": position_value_inr,
        "stop_loss": round(stop_loss, 2),
        "target_price": round(target_price, 2),
        "risk_per_share": round(risk_per_share, 2),
        "estimated_risk_inr": est_risk_inr,
        "reward_risk": round(rr, 2) if rr is not None else None,
        "warnings": warnings,
    }

