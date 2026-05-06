"""NSE-specific data functions — fully implemented for Indian markets."""

import requests
from datetime import datetime, date
from typing import Optional
from backend.health_metrics import incr
from backend.fii_dii import get_data_for_date, get_today_data, get_market_bias
from tradingagents.dataflows.corporate_actions import (
    get_corporate_actions_summary, 
    update_corporate_actions,
    get_corporate_actions
)


def _safe_error(source: str, message: str) -> str:
    incr("upstream_failures")
    return f"[{source}] DATA_UNAVAILABLE: {message}"


def _valid_iso_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _session_with_headers(referer: str) -> requests.Session:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": referer,
        "Connection": "keep-alive",
    }
    session = requests.Session()
    session.headers.update(headers)
    return session


def _get_with_retry(session: requests.Session, url: str, params: dict, retries: int = 3, timeout: int = 15):
    last_exc = None
    for attempt in range(retries):
        try:
            response = session.get(url, params=params, timeout=timeout)
            if response.status_code == 200:
                return response
            incr("upstream_failures")
        except Exception as exc:
            last_exc = exc
            incr("upstream_failures")
    if last_exc:
        raise last_exc
    raise RuntimeError("NSE request failed after retries")


def get_fii_dii_activity(date_str: str) -> str:
    """Get FII/DII buy/sell activity for a given date.

    Args:
        date_str: Date in yyyy-mm-dd format

    Returns:
        Formatted string with FII/DII net buy/sell data
    """
    try:
        if not _valid_iso_date(date_str):
            return _safe_error("FII_DII", f"Invalid date format: {date_str}")

        # Try to get data for specific date, fallback to today if not available
        data = get_data_for_date(date_str)
        if not data and date_str == date.today().strftime("%Y-%m-%d"):
            data = get_today_data()
        
        if not data:
            return _safe_error(
                "FII_DII",
                f"Activity data for {date_str} not available (holiday/source issue).",
            )
        
        # Format the data for display
        fii_net = data.get('fii_net', 0)
        dii_net = data.get('dii_net', 0)
        fii_buy = data.get('fii_buy', 0)
        fii_sell = data.get('fii_sell', 0)
        dii_buy = data.get('dii_buy', 0)
        dii_sell = data.get('dii_sell', 0)
        
        # Determine market sentiment based on FII activity
        if fii_net > 1000:  # Strong FII buying
            sentiment = "BULLISH (Strong FII Inflow)"
        elif fii_net < -1000:  # Strong FII selling
            sentiment = "BEARISH (Strong FII Outflow)"
        else:
            sentiment = "NEUTRAL (Modest FII Activity)"
        
        return (
            f"FII/DII Activity for {date_str}:\n"
            f"Market Sentiment: {sentiment}\n"
            f"FII: Buy ₹{fii_buy:,.2f} Cr | Sell ₹{fii_sell:,.2f} Cr | Net ₹{fii_net:+,.2f} Cr\n"
            f"DII: Buy ₹{dii_buy:,.2f} Cr | Sell ₹{dii_sell:,.2f} Cr | Net ₹{dii_net:+,.2f} Cr\n"
            f"Total Net Flow: ₹{(fii_net + dii_net):+,.2f} Cr\n"
            f"Data Source: {data.get('source', 'unknown').upper()}"
        )
        
    except Exception as e:
        return _safe_error("FII_DII", f"Fetch failed for {date_str}: {str(e)}")


def get_bulk_block_deals(symbol: str, start_date: str, end_date: str) -> str:
    """Get bulk and block deal data for a symbol.

    Args:
        symbol: Stock ticker symbol
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format

    Returns:
        Formatted string with bulk/block deal information
    """
    try:
        if not _valid_iso_date(start_date) or not _valid_iso_date(end_date):
            return _safe_error("BULK_BLOCK", "Invalid start_date/end_date format; expected YYYY-MM-DD.")

        # NSE bulk/block deals URL - this requires proper headers and cookies
        base_url = "https://www.nseindia.com/api/corporates-bulk-deals"
        session = _session_with_headers("https://www.nseindia.com/reports/bulk-block-deals")
        
        # First visit the main page to get cookies
        try:
            session.get("https://www.nseindia.com/reports/bulk-block-deals", timeout=10)
        except Exception:
            pass
        
        # Get bulk deals data
        params = {
            "symbol": symbol.upper(),
            "from": start_date,
            "to": end_date,
            "type": "bulk"
        }
        
        response = _get_with_retry(session, base_url, params=params, retries=3, timeout=15)
        
        data = response.json()
        
        if not data or not isinstance(data, list):
            return f"No bulk/block deals found for {symbol} from {start_date} to {end_date}"
        
        # Process the deals
        deals = []
        total_value = 0
        
        for deal in data:
            try:
                deal_date = deal.get('date', '')
                client_name = deal.get('clientName', 'N/A')
                buy_sell = deal.get('buySell', '')
                quantity = deal.get('quantity', 0)
                price = deal.get('price', 0)
                value = quantity * price
                
                deals.append({
                    'date': deal_date,
                    'client': client_name,
                    'action': buy_sell,
                    'quantity': f"{quantity:,}",
                    'price': f"₹{price:,.2f}",
                    'value': f"₹{value:,.2f}"
                })
                total_value += value
                
            except (KeyError, ValueError, TypeError):
                continue
        
        if not deals:
            return f"No bulk/block deals found for {symbol} from {start_date} to {end_date}"
        
        # Format the output
        result = [
            f"Bulk/Block Deals for {symbol} ({start_date} to {end_date}):",
            f"Total Deal Value: ₹{total_value:,.2f} Cr\n",
            "Date       | Client           | Action | Quantity    | Price     | Value",
            "-----------|------------------|---------|-------------|-----------|----------"
        ]
        
        for deal in deals[:10]:  # Show top 10 deals
            result.append(
                f"{deal['date']} | {deal['client'][:16]:16} | {deal['action']:7} | {deal['quantity']:11} | {deal['price']:9} | {deal['value']}"
            )
        
        if len(deals) > 10:
            result.append(f"\n... and {len(deals) - 10} more deals (showing top 10)")
        
        return "\n".join(result)
        
    except Exception as e:
        # Fallback to moneycontrol
        try:
            incr("fallback_activations")
            return _get_bulk_deals_from_moneycontrol(symbol, start_date, end_date)
        except Exception:
            return _safe_error("BULK_BLOCK", f"Fetch failed for {symbol}: {str(e)}")


def _get_bulk_deals_from_moneycontrol(symbol: str, start_date: str, end_date: str) -> str:
    """Fallback: Get bulk deals from moneycontrol (simplified implementation)."""
    try:
        # Moneycontrol URL for bulk deals
        url = f"https://www.moneycontrol.com/stocks/marketinfo/bulk_deals/{symbol.upper()}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return f"Unable to fetch bulk deals data from alternative sources for {symbol}"
        
        # Simple HTML parsing - in production, use BeautifulSoup
        text = response.text
        if "bulk deal" in text.lower() or "block deal" in text.lower():
            return (
                f"Bulk/Block deals data for {symbol} is available on Moneycontrol. "
                f"Visit https://www.moneycontrol.com/stocks/marketinfo/bulk_deals/{symbol.upper()} "
                f"for detailed information from {start_date} to {end_date}."
            )
        else:
            return f"No bulk/block deals found for {symbol} in the specified period"
            
    except Exception:
        return f"Unable to fetch bulk deals data for {symbol} from alternative sources"


def get_delivery_percentage(symbol: str, date_str: str) -> str:
    """Get delivery percentage data for a symbol.

    High delivery percentage indicates genuine buying interest.

    Args:
        symbol: Stock ticker symbol
        date_str: Date in yyyy-mm-dd format

    Returns:
        Formatted string with delivery data
    """
    try:
        if not _valid_iso_date(date_str):
            return _safe_error("DELIVERY", f"Invalid date format: {date_str}")

        # NSE bhavcopy URL for delivery data
        base_url = "https://www.nseindia.com/api/equity-stockHistorical"
        session = _session_with_headers("https://www.nseindia.com/get-quotes/equity")
        
        # First visit main page to get cookies
        try:
            session.get("https://www.nseindia.com/get-quotes/equity", timeout=10)
        except Exception:
            pass
        
        # Get historical data for specific date
        params = {
            "symbol": symbol.upper(),
            "series": "EQ",
            "from": date_str,
            "to": date_str,
            "csv": "true"
        }
        
        response = _get_with_retry(session, base_url, params=params, retries=3, timeout=15)
        
        # Parse CSV data
        csv_data = response.text
        if not csv_data or "No Data" in csv_data:
            return f"No delivery data available for {symbol} on {date_str}"
        
        lines = csv_data.strip().split('\n')
        if len(lines) < 2:
            return f"Invalid delivery data format for {symbol} on {date_str}"
        
        # Skip header, parse data
        data_line = lines[1]
        columns = data_line.split(',')
        
        if len(columns) < 15:  # NSE bhavcopy has many columns
            return f"Insufficient delivery data columns for {symbol} on {date_str}"
        
        try:
            # NSE bhavcopy columns (approximate indices):
            # 0: Symbol, 1: Series, 2: Date, 3: Prev Close, 4: Open, 5: High, 6: Low, 
            # 7: Last, 8: Close, 9: VWAP, 10: Volume, 11: Turnover, 
            # 12: Trades, 13: Deliverable Volume, 14: Delivery Percentage
            
            close_price = float(columns[8])
            total_volume = float(columns[10])
            deliverable_volume = float(columns[13])
            delivery_percentage = float(columns[14])
            
            # Calculate additional metrics
            non_deliverable = total_volume - deliverable_volume
            
            # Interpret delivery percentage
            if delivery_percentage >= 80:
                delivery_signal = "VERY STRONG (High institutional buying)"
            elif delivery_percentage >= 60:
                delivery_signal = "STRONG (Good buying interest)"
            elif delivery_percentage >= 40:
                delivery_signal = "MODERATE (Mixed interest)"
            else:
                delivery_signal = "WEAK (High speculative activity)"
            
            return (
                f"Delivery Analysis for {symbol} on {date_str}:\n"
                f"Closing Price: ₹{close_price:,.2f}\n"
                f"Total Volume: {total_volume:,} shares\n"
                f"Deliverable Volume: {deliverable_volume:,} shares\n"
                f"Non-Deliverable Volume: {non_deliverable:,} shares\n"
                f"Delivery Percentage: {delivery_percentage:.2f}%\n"
                f"Signal: {delivery_signal}\n\n"
                f"Note: Delivery percentage >60% indicates genuine buying, "
                f"<40% suggests speculative trading."
            )
            
        except (ValueError, IndexError) as e:
            return f"Error parsing delivery data for {symbol} on {date_str}: Invalid data format"
        
    except Exception as e:
        # Fallback to moneycontrol
        try:
            incr("fallback_activations")
            return _get_delivery_from_moneycontrol(symbol, date_str)
        except Exception:
            return _safe_error("DELIVERY", f"Fetch failed for {symbol} on {date_str}: {str(e)}")


def _get_delivery_from_moneycontrol(symbol: str, date_str: str) -> str:
    """Fallback: Get delivery data from moneycontrol (simplified implementation)."""
    try:
        # Moneycontrol URL for stock details
        url = f"https://www.moneycontrol.com/india/stockpricequote/{symbol.lower()}/{symbol.upper()}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return f"Unable to fetch delivery data from alternative sources for {symbol}"
        
        # Simple HTML parsing - look for delivery percentage in text
        text = response.text
        if "delivery" in text.lower():
            return (
                f"Delivery data for {symbol} is available on Moneycontrol. "
                f"Visit https://www.moneycontrol.com/india/stockpricequote/{symbol.lower()}/{symbol.upper()} "
                f"for detailed delivery analysis for {date_str}."
            )
        else:
            return f"No delivery data found for {symbol} on {date_str} from alternative sources"
            
    except Exception:
        return f"Unable to fetch delivery data for {symbol} from alternative sources"

    """Get corporate actions summary for a symbol.
    
    Args:
        symbol: Stock symbol
        days: Number of days to look back
        
    Returns:
        Formatted string with corporate actions summary
    """
    try:
        from datetime import timedelta
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get actions from database without updating (to avoid recursion)
        actions = get_corporate_actions(symbol, start_date=start_date, end_date=end_date)
        
        if not actions:
            return f"No corporate actions found for {symbol} in the last {days} days."
        
        # Group by action type
        bonus_actions = [a for a in actions if a.action_type == 'bonus']
        split_actions = [a for a in actions if a.action_type == 'split']
        dividend_actions = [a for a in actions if a.action_type == 'dividend']
        
        result = [f"Corporate Actions Summary for {symbol} (Last {days} days):"]
        
        if bonus_actions:
            result.append(f"\n🎁 Bonus Issues ({len(bonus_actions)}):")
            for action in bonus_actions[:5]:  # Show latest 5
                result.append(f"  • {action.record_date}: {action.ratio} - {action.description}")
        
        if split_actions:
            result.append(f"\n📊 Stock Splits ({len(split_actions)}):")
            for action in split_actions[:5]:  # Show latest 5
                result.append(f"  • {action.record_date}: {action.ratio} - {action.description}")
        
        if dividend_actions:
            result.append(f"\n💰 Dividends ({len(dividend_actions)}):")
            for action in dividend_actions[:5]:  # Show latest 5
                result.append(f"  • {action.record_date}: {action.ratio} - {action.description}")
        
        if len(bonus_actions) > 5 or len(split_actions) > 5 or len(dividend_actions) > 5:
            result.append(f"\n... and more actions (showing latest 5 per category)")
        
        return "\n".join(result)
        
    except Exception as e:
        return (
            f"Error fetching corporate actions for {symbol}: {str(e)}. "
            "This could be due to network issues or NSE API changes. "
            "Please check NSE website directly for latest corporate actions."
        )


def get_bonus_shares_history(symbol: str, start_date: str, end_date: str) -> str:
    """Get bonus shares history for a symbol.
    
    Args:
        symbol: Stock ticker symbol
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format
        
    Returns:
        Formatted string with bonus shares history
    """
    try:
        from datetime import datetime
        
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # Get bonus actions
        bonus_actions = get_corporate_actions(
            symbol=symbol, 
            action_type='bonus',
            start_date=start_dt,
            end_date=end_dt
        )
        
        if not bonus_actions:
            return f"No bonus shares found for {symbol} from {start_date} to {end_date}"
        
        result = [f"Bonus Shares History for {symbol} ({start_date} to {end_date}):"]
        result.append(f"Total Bonus Issues: {len(bonus_actions)}\n")
        
        for action in bonus_actions:
            result.append(
                f"• {action.record_date}: {action.ratio} - {action.company_name}"
            )
        
        return "\n".join(result)
        
    except Exception as e:
        return (
            f"Error fetching bonus shares history for {symbol}: {str(e)}. "
            "Please check NSE website directly for bonus share information."
        )


def get_stock_split_history(symbol: str, start_date: str, end_date: str) -> str:
    """Get stock split history for a symbol.
    
    Args:
        symbol: Stock ticker symbol
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format
        
    Returns:
        Formatted string with stock split history
    """
    try:
        from datetime import datetime
        
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # Get split actions
        split_actions = get_corporate_actions(
            symbol=symbol, 
            action_type='split',
            start_date=start_dt,
            end_date=end_dt
        )
        
        if not split_actions:
            return f"No stock splits found for {symbol} from {start_date} to {end_date}"
        
        result = [f"Stock Split History for {symbol} ({start_date} to {end_date}):"]
        result.append(f"Total Splits: {len(split_actions)}\n")
        
        for action in split_actions:
            result.append(
                f"• {action.record_date}: {action.ratio} - {action.company_name}"
            )
        
        return "\n".join(result)
        
    except Exception as e:
        return (
            f"Error fetching stock split history for {symbol}: {str(e)}. "
            "Please check NSE website directly for stock split information."
        )


def get_dividend_history(symbol: str, start_date: str, end_date: str) -> str:
    """Get dividend history for a symbol.
    
    Args:
        symbol: Stock ticker symbol
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format
        
    Returns:
        Formatted string with dividend history
    """
    try:
        from datetime import datetime
        
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # Get dividend actions
        dividend_actions = get_corporate_actions(
            symbol=symbol, 
            action_type='dividend',
            start_date=start_dt,
            end_date=end_dt
        )
        
        if not dividend_actions:
            return f"No dividends found for {symbol} from {start_date} to {end_date}"
        
        # Calculate total dividend amount
        total_dividend = sum(action.face_value for action in dividend_actions)
        
        result = [f"Dividend History for {symbol} ({start_date} to {end_date}):"]
        result.append(f"Total Dividends: {len(dividend_actions)}")
        result.append(f"Total Amount: ₹{total_dividend:,.2f}\n")
        
        for action in dividend_actions:
            result.append(
                f"• {action.record_date}: {action.ratio} - {action.company_name}"
            )
        
        return "\n".join(result)
        
    except Exception as e:
        return (
            f"Error fetching dividend history for {symbol}: {str(e)}. "
            "Please check NSE website directly for dividend information."
        )
