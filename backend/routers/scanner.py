"""Market Scanner API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel
from backend.scanner import run_scan, UNIVERSES

router = APIRouter(prefix="/api/scanner", tags=["scanner"])


class ScanRequest(BaseModel):
    universe: str = "nifty50"
    strategies: list[str] = ["gap", "volume", "breakout"]
    gap_threshold: float = 2.0
    volume_multiplier: float = 2.0
    breakout_lookback: int = 20


@router.post("/run")
def run_scanner(req: ScanRequest):
    """Run a market scan synchronously. Returns results directly."""
    results = run_scan(
        universe=req.universe,
        strategies=req.strategies,
        gap_threshold=req.gap_threshold,
        volume_multiplier=req.volume_multiplier,
        breakout_lookback=req.breakout_lookback,
    )
    return results


@router.get("/universes/list")
def list_universes():
    """List available stock universes."""
    return {
        name: {"count": len(stocks), "sample": stocks[:5]}
        for name, stocks in UNIVERSES.items()
    }
