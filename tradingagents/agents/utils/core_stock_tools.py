from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor
from tradingagents.utils.tool_validation import safe_tool_call


@tool
def get_stock_data(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve stock price data (OHLCV) for a given ticker symbol.
    Uses the configured core_stock_apis vendor.
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        start_date (str): Start date in yyyy-mm-dd format
        end_date (str): End date in yyyy-mm-dd format
    Returns:
        str: A formatted dataframe containing the stock price data for the specified ticker symbol in the specified date range.
    """
    response = safe_tool_call(
        lambda **params: route_to_vendor(
            "get_stock_data",
            params["symbol"],
            params["start_date"],
            params["end_date"],
        ),
        "get_stock_data",
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
    )
    if response["success"]:
        return response["result"]
    return f"Error: {response['error']}"
