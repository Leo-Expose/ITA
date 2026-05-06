"""LangChain tool wrappers for Indian market-specific data."""

from langchain_core.tools import tool


@tool
def get_fii_dii_activity(date: str) -> str:
    """Get FII (Foreign Institutional Investor) and DII (Domestic Institutional Investor)
    buy/sell activity for the Indian stock market on a given date.
    FII/DII data is a key indicator of institutional sentiment in Indian markets.

    Args:
        date: Date in yyyy-mm-dd format
    """
    from tradingagents.dataflows.nse_data import get_fii_dii_activity as _get
    return _get(date)


@tool
def get_bulk_block_deals(symbol: str, start_date: str, end_date: str) -> str:
    """Get bulk and block deal data for an Indian stock.
    Bulk/block deals indicate large institutional transactions and can signal
    major position changes by big investors.

    Args:
        symbol: Stock ticker symbol (e.g., "RELIANCE.NS")
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format
    """
    from tradingagents.dataflows.nse_data import get_bulk_block_deals as _get
    return _get(symbol, start_date, end_date)


@tool
def get_delivery_percentage(symbol: str, date: str) -> str:
    """Get delivery percentage data for an Indian stock.
    High delivery percentage (>50%) indicates genuine buying interest rather than
    speculative intraday trading. Important for short-term trading decisions.

    Args:
        symbol: Stock ticker symbol (e.g., "RELIANCE.NS")
        date: Date in yyyy-mm-dd format
    """
    from tradingagents.dataflows.nse_data import get_delivery_percentage as _get
    return _get(symbol, date)
