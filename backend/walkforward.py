"""Offline evaluation utilities (policy/backtest summarization).

This is not a full market simulator. It’s a pragmatic evaluator to answer:
“If I follow this pick-selection policy, what happens (net of costs)?”

We build on the existing recommender historical backtest machinery to avoid
re-implementing date handling and yfinance fetching.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from backend.cost_model import get_estimated_round_trip_cost_bps, cost_pct_from_bps
from backend.db import get_db, save_eval_run
from backend.simulation import run_recommender_backtest


@dataclass
class WalkforwardParams:
    universe: str = "nifty50"
    start_date: str | None = None
    end_date: str | None = None
    interval_days: int = 1  # evaluate every trading day
    horizon_days: int = 5   # return_5d
    top_n_per_day: int = 5
    equal_weight: bool = True


def _max_drawdown(equity_curve: list[float]) -> float:
    peak = None
    max_dd = 0.0
    for x in equity_curve:
        if peak is None or x > peak:
            peak = x
        if peak and peak > 0:
            dd = (peak - x) / peak
            if dd > max_dd:
                max_dd = dd
    return max_dd


def _load_backtest_rows(run_id: str) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT trade_date, ticker, signal, score, return_1d, return_3d, return_5d, return_10d "
            "FROM recommender_backtests WHERE run_id = ?",
            (run_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def run_walkforward_eval(params: WalkforwardParams) -> dict:
    """Run a simple policy evaluation using historical recommender backtest rows."""
    run_id = f"wf_{str(uuid.uuid4())[:8]}"

    # Step 1: generate (or regenerate) backtest rows for the period.
    backtest_summary = run_recommender_backtest(
        universe=params.universe,
        start_date=params.start_date,
        end_date=params.end_date,
        interval_days=params.interval_days,
    )
    bt_run_id = backtest_summary["run_id"]

    rows = _load_backtest_rows(bt_run_id)
    if not rows:
        metrics = {"ok": False, "error": "No backtest rows generated", "backtest": backtest_summary}
        save_eval_run(run_id, "walkforward", params.__dict__, metrics)
        return {"run_id": run_id, **metrics}

    # Step 2: pick top-N per day (by absolute score magnitude within that day).
    by_day: dict[str, list[dict]] = {}
    for r in rows:
        by_day.setdefault(r["trade_date"], []).append(r)

    horizon_key = f"return_{params.horizon_days}d"
    cost_pct = cost_pct_from_bps(get_estimated_round_trip_cost_bps())

    daily_returns = []
    trade_returns = []
    for d, picks in sorted(by_day.items()):
        # Filter to picks with the horizon return available
        picks = [p for p in picks if p.get(horizon_key) is not None]
        if not picks:
            continue
        # Rank by |score|, so STRONG signals dominate, regardless of direction.
        picks.sort(key=lambda p: abs(p.get("score") or 0), reverse=True)
        chosen = picks[: max(1, int(params.top_n_per_day))]

        # Equal-weight across chosen positions; use net-of-cost return.
        net_rets = []
        for c in chosen:
            gross = float(c[horizon_key])
            net = gross - (cost_pct if gross is not None else 0.0)
            net_rets.append(net)
            trade_returns.append(net)
        day_ret = sum(net_rets) / len(net_rets) if net_rets else 0.0
        daily_returns.append(day_ret)

    if not daily_returns:
        metrics = {"ok": False, "error": "No ripe picks with horizon returns", "backtest": backtest_summary}
        save_eval_run(run_id, "walkforward", params.__dict__, metrics)
        return {"run_id": run_id, **metrics}

    # Step 3: build equity curve (starting at 1.0) using simple compounding.
    equity = 1.0
    curve = [equity]
    for r in daily_returns:
        equity *= (1.0 + (r / 100.0))
        curve.append(equity)

    n_days = len(daily_returns)
    avg_day = sum(daily_returns) / n_days
    win_rate = sum(1 for r in trade_returns if r > 0) / len(trade_returns) if trade_returns else 0.0
    max_dd = _max_drawdown(curve)

    metrics = {
        "ok": True,
        "policy": {
            "top_n_per_day": params.top_n_per_day,
            "horizon_days": params.horizon_days,
            "interval_days": params.interval_days,
            "estimated_round_trip_cost_bps": get_estimated_round_trip_cost_bps(),
        },
        "backtest": backtest_summary,
        "n_days": n_days,
        "n_trades": len(trade_returns),
        "avg_daily_return_net_pct": round(avg_day, 4),
        "equity_multiple": round(curve[-1], 4),
        "max_drawdown_pct": round(max_dd * 100.0, 2),
        "trade_win_rate": round(win_rate, 3),
        "avg_trade_return_net_pct": round(sum(trade_returns) / len(trade_returns), 4) if trade_returns else None,
    }

    save_eval_run(run_id, "walkforward", params.__dict__, metrics)
    return {"run_id": run_id, **metrics}

