"""Offline evaluation API (walk-forward / policy evaluation)."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from backend.db import get_eval_run
from backend.walkforward import WalkforwardParams, run_walkforward_eval


router = APIRouter(prefix="/api/eval", tags=["eval"])


class WalkforwardRequest(BaseModel):
    universe: str = "nifty50"
    start_date: str | None = None
    end_date: str | None = None
    interval_days: int = 1
    horizon_days: int = 5
    top_n_per_day: int = 5


@router.post("/walkforward")
def start_walkforward(req: WalkforwardRequest):
    params = WalkforwardParams(
        universe=req.universe,
        start_date=req.start_date,
        end_date=req.end_date,
        interval_days=req.interval_days,
        horizon_days=req.horizon_days,
        top_n_per_day=req.top_n_per_day,
    )
    return run_walkforward_eval(params)


@router.get("/walkforward/{run_id}")
def get_walkforward(run_id: str):
    row = get_eval_run(run_id)
    if not row:
        return {"ok": False, "error": "Run not found", "run_id": run_id}
    return {"ok": True, **row}


@router.get("/walkforward")
def get_walkforward_inline(
    universe: str = Query("nifty50"),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    interval_days: int = Query(1),
    horizon_days: int = Query(5),
    top_n_per_day: int = Query(5),
):
    """Convenience GET wrapper for quick testing."""
    params = WalkforwardParams(
        universe=universe,
        start_date=start_date,
        end_date=end_date,
        interval_days=interval_days,
        horizon_days=horizon_days,
        top_n_per_day=top_n_per_day,
    )
    return run_walkforward_eval(params)

