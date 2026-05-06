"""Recommendation Engine API — combines all strategies into ranked trade ideas."""

from fastapi import APIRouter, Query
from backend.recommender import recommend, _analyze_stock

router = APIRouter(prefix="/api/recommend", tags=["recommend"])


@router.get("/")
def get_recommendations(
    universe: str = Query("nifty100", description="nifty50, nifty100, or bse250"),
    min_signals: int = Query(2, description="Min aligned signals to recommend"),
):
    """Get ranked trade recommendations combining all strategies."""
    return recommend(universe, min_signals)


@router.get("/stock/{ticker}")
def analyze_single_stock(ticker: str):
    """Get recommendation for a single stock."""
    result = _analyze_stock(ticker)
    if not result:
        return {"error": f"Could not analyze {ticker}"}
    return result
