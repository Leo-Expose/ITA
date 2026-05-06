"""NSE-specific data functions — fully implemented for Indian markets."""

import requests
from datetime import datetime, date
from typing import Optional
from backend.fii_dii import get_data_for_date, get_today_data, get_market_bias


def get_fii_dii_activity(date_str: str) -> str:
    """Get FII/DII buy/sell activity for a given date.

    Args:
        date_str: Date in yyyy-mm-dd format

    Returns:
        Formatted string with FII/DII net buy/sell data
    """
    try:
        # Try to get data for specific date, fallback to today if not available
        data = get_data_for_date(date_str)
        if not data and date_str == date.today().strftime("%Y-%m-%d"):
            data = get_today_data()
        
        if not data:
            return (
                f"FII/DII activity data for {date_str} is not available. "
                "This could be due to market holiday or data source issues. "
                "Please check https://www.nseindia.com/reports/fii-dii for official data."
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
        return (
            f"Error fetching FII/DII data for {date_str}: {str(e)}. "
            "Please try again later or check NSE website directly."
        )


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
        # NSE bulk/block deals URL - this requires proper headers and cookies
        base_url = "https://www.nseindia.com/api/corporates-bulk-deals"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/reports/bulk-block-deals",
            "Connection": "keep-alive",
        }
        
        session = requests.Session()
        session.headers.update(headers)
        
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
        
        response = session.get(base_url, params=params, timeout=15)
        
        if response.status_code != 200:
            # Try alternative approach - use moneycontrol as fallback
            return _get_bulk_deals_from_moneycontrol(symbol, start_date, end_date)
        
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
            return _get_bulk_deals_from_moneycontrol(symbol, start_date, end_date)
        except Exception:
            return (
                f"Error fetching bulk/block deals for {symbol}: {str(e)}. "
                "This could be due to market restrictions or data availability. "
                "Please check NSE website directly for the latest information."
            )


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


def get_delivery_percentage(symbol: str, date: str) -> str:
    """Get delivery percentage data for a symbol.

    High delivery percentage indicates genuine buying interest.

    Args:
        symbol: Stock ticker symbol
        date: Date in yyyy-mm-dd format

    Returns:
        Formatted string with delivery data
    """
    try:
        # NSE bhavcopy URL for delivery data
        base_url = "https://www.nseindia.com/api/equity-stockHistorical"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/get-quotes/equity",
            "Connection": "keep-alive",
        }
        
        session = requests.Session()
        session.headers.update(headers)
        
        # First visit main page to get cookies
        try:
            session.get("https://www.nseindia.com/get-quotes/equity", timeout=10)
        except Exception:
            pass
        
        # Get historical data for the specific date
        params = {
            "symbol": symbol.upper(),
            "series": "EQ",
            "from": date,
            "to": date,
            "csv": "true"
        }
        
        response = session.get(base_url, params=params, timeout=15)
        
        if response.status_code != 200:
            # Try alternative approach - use moneycontrol as fallback
            return _get_delivery_from_moneycontrol(symbol, date)
        
        # Parse CSV data
        csv_data = response.text
        if not csv_data or "No Data" in csv_data:
            return f"No delivery data available for {symbol} on {date}"
        
        lines = csv_data.strip().split('\n')
        if len(lines) < 2:
            return f"Invalid delivery data format for {symbol} on {date}"
        
        # Skip header, parse data
        data_line = lines[1]
        columns = data_line.split(',')
        
        if len(columns) < 15:  # NSE bhavcopy has many columns
            return f"Insufficient delivery data columns for {symbol} on {date}"
        
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
                f"Delivery Analysis for {symbol} on {date}:\n"
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
            return f"Error parsing delivery data for {symbol} on {date}: Invalid data format"
        
    except Exception as e:
        # Fallback to moneycontrol
        try:
            return _get_delivery_from_moneycontrol(symbol, date)
        except Exception:
            return (
                f"Error fetching delivery data for {symbol} on {date}: {str(e)}. "
                "This could be due to market holiday or data availability. "
                "Please check NSE website directly for latest delivery information."
            )


def _get_delivery_from_moneycontrol(symbol: str, date: str) -> str:
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
                f"for detailed delivery analysis for {date}."
            )
        else:
            return f"No delivery data found for {symbol} on {date} from alternative sources"
            
    except Exception:
        return f"Unable to fetch delivery data for {symbol} from alternative sources"
