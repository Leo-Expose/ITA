"""News Feed API — aggregates news from multiple sources."""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from backend.news_sources import (
    fetch_all_news,
    fetch_ticker_news,
    get_news_sources_config,
    save_news_sources_config,
)

router = APIRouter(prefix="/api/news", tags=["news"])


class NewsSourcesUpdate(BaseModel):
    rss_feeds: dict | None = None
    yf_queries: list[str] | None = None


@router.get("/")
def get_news(max_per_source: int = Query(10)):
    """Get aggregated news from all enabled sources."""
    return {
        "articles": fetch_all_news(max_per_source),
    }


@router.get("/ticker/{ticker}")
def get_news_for_ticker(ticker: str, max_items: int = Query(15)):
    """Get news for a specific ticker."""
    return {
        "ticker": ticker,
        "articles": fetch_ticker_news(ticker, max_items),
    }


@router.get("/sources")
def get_sources():
    """Get current news sources configuration."""
    return get_news_sources_config()


@router.put("/sources")
def update_sources(data: NewsSourcesUpdate):
    """Update news sources configuration."""
    save_news_sources_config(rss_feeds=data.rss_feeds, yf_queries=data.yf_queries)
    return {"status": "saved", "config": get_news_sources_config()}
