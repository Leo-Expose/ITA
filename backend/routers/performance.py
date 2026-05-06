"""Strategy Performance API endpoints — measure historical success rate of strategies."""

from fastapi import APIRouter, Query
from backend.performance import (
    measure_gap_strategy,
    measure_volume_strategy,
    measure_breakout_strategy,
    measure_sr_bounce_strategy,
    measure_all_strategies,
)

router = APIRouter(prefix="/api/performance", tags=["performance"])


@router.get("/all")
def run_all_strategies(
    universe: str = Query("nifty50", description="nifty50, nifty100, or bse250"),
    lookback_days: int = Query(60, description="How many days of history to analyze"),
):
    """Measure performance of all 4 strategies. Takes 30-120 seconds depending on universe."""
    return measure_all_strategies(universe, lookback_days, [1, 3, 5])


@router.get("/gap")
def run_gap_strategy(
    universe: str = Query("nifty50"),
    lookback_days: int = Query(60),
    gap_threshold: float = Query(2.0),
):
    return measure_gap_strategy(universe, lookback_days, gap_threshold, [1, 3, 5])


@router.get("/volume")
def run_volume_strategy(
    universe: str = Query("nifty50"),
    lookback_days: int = Query(60),
    volume_multiplier: float = Query(2.0),
):
    return measure_volume_strategy(universe, lookback_days, volume_multiplier, [1, 3, 5])


@router.get("/breakout")
def run_breakout_strategy(
    universe: str = Query("nifty50"),
    lookback_days: int = Query(60),
    breakout_window: int = Query(20),
    require_volume: bool = Query(True),
):
    return measure_breakout_strategy(universe, lookback_days, breakout_window, [1, 3, 5], require_volume)


@router.get("/sr-bounce")
def run_sr_bounce_strategy(
    universe: str = Query("nifty50"),
    lookback_days: int = Query(90),
):
    return measure_sr_bounce_strategy(universe, lookback_days, 3, [1, 3, 5])
