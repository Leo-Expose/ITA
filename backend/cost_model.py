"""Trading cost model (simple, conservative).

This project is a suggestion engine for manual execution. To avoid overfitting
to unrealistic paper results, we estimate round-trip trading costs and compute
net P&L (gross - costs).

We intentionally keep this model simple and configurable:
- costs are modeled as a fixed round-trip basis-point (bps) drag on notional
- applied equally to LONG and SHORT trades (because it's a cost, not alpha)
"""

from __future__ import annotations

from tradingagents.dataflows.config import get_config


def get_estimated_round_trip_cost_bps() -> float:
    """Return the configured round-trip cost estimate in bps."""
    cfg = get_config()
    try:
        return float(cfg.get("estimated_round_trip_cost_bps", 35.0))
    except Exception:
        return 35.0


def cost_pct_from_bps(cost_bps: float) -> float:
    """Convert basis points to percentage points (e.g. 35 bps -> 0.35%)."""
    return float(cost_bps) / 100.0


def net_pnl_pct(gross_pnl_pct: float | None, cost_bps: float | None = None) -> float | None:
    """Convert gross P&L percent to net P&L percent by subtracting cost drag."""
    if gross_pnl_pct is None:
        return None
    if cost_bps is None:
        cost_bps = get_estimated_round_trip_cost_bps()
    return round(float(gross_pnl_pct) - cost_pct_from_bps(float(cost_bps)), 4)

