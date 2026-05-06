"""Corporate Actions Database for Indian Markets.

Handles bonus shares, stock splits, dividends, and other corporate actions
from NSE/BSE listed companies with proper Indian market formatting.
"""

import requests
import sqlite3
from datetime import datetime, date
from typing import List, Dict, Optional, Any
import logging
from pathlib import Path

# Database setup
DB_PATH = Path(__file__).parent.parent.parent / "data" / "corporate_actions.db"
DB_PATH.parent.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)


class CorporateAction:
    """Represents a corporate action for an Indian stock."""
    
    def __init__(self, data: Dict[str, Any]):
        self.symbol = data.get('symbol', '')
        self.company_name = data.get('company_name', '')
        self.action_type = data.get('action_type', '')  # 'bonus', 'split', 'dividend', 'rights'
        self.record_date = data.get('record_date')
        self.ex_date = data.get('ex_date')
        self.announcement_date = data.get('announcement_date')
        self.ratio = data.get('ratio', '')
        self.description = data.get('description', '')
        self.face_value = data.get('face_value', 0)
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'company_name': self.company_name,
            'action_type': self.action_type,
            'record_date': self.record_date,
            'ex_date': self.ex_date,
            'announcement_date': self.announcement_date,
            'ratio': self.ratio,
            'description': self.description,
            'face_value': self.face_value
        }


def init_database():
    """Initialize the corporate actions database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS corporate_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            company_name TEXT,
            action_type TEXT NOT NULL,
            record_date TEXT,
            ex_date TEXT,
            announcement_date TEXT,
            ratio TEXT,
            description TEXT,
            face_value REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, record_date, action_type)
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_symbol ON corporate_actions(symbol)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_action_type ON corporate_actions(action_type)
    ''')
    
    conn.commit()
    conn.close()


def add_corporate_action(action: CorporateAction) -> bool:
    """Add a corporate action to the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO corporate_actions 
            (symbol, company_name, action_type, record_date, ex_date, 
             announcement_date, ratio, description, face_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            action.symbol, action.company_name, action.action_type,
            action.record_date, action.ex_date, action.announcement_date,
            action.ratio, action.description, action.face_value
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error adding corporate action: {e}")
        return False


def get_corporate_actions(
    symbol: str = None, 
    action_type: str = None,
    start_date: date = None,
    end_date: date = None
) -> List[CorporateAction]:
    """Get corporate actions with optional filters."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = "SELECT * FROM corporate_actions WHERE 1=1"
    params = []
    
    if symbol:
        query += " AND symbol = ?"
        params.append(symbol.upper())
    
    if action_type:
        query += " AND action_type = ?"
        params.append(action_type.lower())
    
    if start_date:
        query += " AND record_date >= ?"
        params.append(start_date.strftime('%Y-%m-%d'))
    
    if end_date:
        query += " AND record_date <= ?"
        params.append(end_date.strftime('%Y-%m-%d'))
    
    query += " ORDER BY record_date DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Get column names
    columns = [desc[0] for desc in cursor.description]
    
    actions = []
    for row in rows:
        data = dict(zip(columns, row))
        actions.append(CorporateAction(data))
    
    conn.close()
    return actions


def fetch_nse_bonus_shares(symbol: str = None) -> List[Dict[str, Any]]:
    """Fetch bonus shares data from NSE website.
    
    Args:
        symbol: Stock symbol (optional, if None fetches all recent bonus issues)
        
    Returns:
        List of bonus share dictionaries
    """
    try:
        # NSE corporate actions API
        base_url = "https://www.nseindia.com/api/corporate-bonus"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/reports/corporate-actions",
        }
        
        session = requests.Session()
        session.headers.update(headers)
        
        # Get cookies first
        try:
            session.get("https://www.nseindia.com/reports/corporate-actions", timeout=10)
        except Exception:
            pass
        
        params = {}
        if symbol:
            params['symbol'] = symbol.upper()
        
        response = session.get(base_url, params=params, timeout=15)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        return data if isinstance(data, list) else []
        
    except Exception as e:
        logger.error(f"Error fetching bonus shares from NSE: {e}")
        return []


def fetch_nse_stock_splits(symbol: str = None) -> List[Dict[str, Any]]:
    """Fetch stock split data from NSE website.
    
    Args:
        symbol: Stock symbol (optional, if None fetches all recent splits)
        
    Returns:
        List of stock split dictionaries
    """
    try:
        # NSE stock splits API
        base_url = "https://www.nseindia.com/api/corporate-splits"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/reports/corporate-actions",
        }
        
        session = requests.Session()
        session.headers.update(headers)
        
        # Get cookies first
        try:
            session.get("https://www.nseindia.com/reports/corporate-actions", timeout=10)
        except Exception:
            pass
        
        params = {}
        if symbol:
            params['symbol'] = symbol.upper()
        
        response = session.get(base_url, params=params, timeout=15)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        return data if isinstance(data, list) else []
        
    except Exception as e:
        logger.error(f"Error fetching stock splits from NSE: {e}")
        return []


def fetch_nse_dividends(symbol: str = None) -> List[Dict[str, Any]]:
    """Fetch dividend data from NSE website.
    
    Args:
        symbol: Stock symbol (optional, if None fetches all recent dividends)
        
    Returns:
        List of dividend dictionaries
    """
    try:
        # NSE dividends API
        base_url = "https://www.nseindia.com/api/corporate-dividends"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/reports/corporate-actions",
        }
        
        session = requests.Session()
        session.headers.update(headers)
        
        # Get cookies first
        try:
            session.get("https://www.nseindia.com/reports/corporate-actions", timeout=10)
        except Exception:
            pass
        
        params = {}
        if symbol:
            params['symbol'] = symbol.upper()
        
        response = session.get(base_url, params=params, timeout=15)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        return data if isinstance(data, list) else []
        
    except Exception as e:
        logger.error(f"Error fetching dividends from NSE: {e}")
        return []


def process_bonus_data(bonus_data: List[Dict[str, Any]]) -> List[CorporateAction]:
    """Process raw bonus data into CorporateAction objects."""
    actions = []
    
    for item in bonus_data:
        try:
            action = CorporateAction({
                'symbol': item.get('symbol', ''),
                'company_name': item.get('companyName', ''),
                'action_type': 'bonus',
                'record_date': item.get('recordDate'),
                'ex_date': item.get('exDate'),
                'announcement_date': item.get('announcementDate'),
                'ratio': f"1:{item.get('ratio', '0')}",
                'description': f"Bonus Issue - {item.get('ratio', '0')}:1",
                'face_value': item.get('faceValue', 0)
            })
            actions.append(action)
        except Exception as e:
            logger.error(f"Error processing bonus data: {e}")
    
    return actions


def process_split_data(split_data: List[Dict[str, Any]]) -> List[CorporateAction]:
    """Process raw split data into CorporateAction objects."""
    actions = []
    
    for item in split_data:
        try:
            action = CorporateAction({
                'symbol': item.get('symbol', ''),
                'company_name': item.get('companyName', ''),
                'action_type': 'split',
                'record_date': item.get('recordDate'),
                'ex_date': item.get('exDate'),
                'announcement_date': item.get('announcementDate'),
                'ratio': f"{item.get('fromFaceValue', '0')}:{item.get('toFaceValue', '0')}",
                'description': f"Stock Split - {item.get('fromFaceValue', '0')}:{item.get('toFaceValue', '0')}",
                'face_value': item.get('toFaceValue', 0)
            })
            actions.append(action)
        except Exception as e:
            logger.error(f"Error processing split data: {e}")
    
    return actions


def process_dividend_data(dividend_data: List[Dict[str, Any]]) -> List[CorporateAction]:
    """Process raw dividend data into CorporateAction objects."""
    actions = []
    
    for item in dividend_data:
        try:
            action = CorporateAction({
                'symbol': item.get('symbol', ''),
                'company_name': item.get('companyName', ''),
                'action_type': 'dividend',
                'record_date': item.get('recordDate'),
                'ex_date': item.get('exDate'),
                'announcement_date': item.get('announcementDate'),
                'ratio': f"₹{item.get('dividendValue', '0')}",
                'description': f"Dividend - ₹{item.get('dividendValue', '0')} per share",
                'face_value': item.get('dividendValue', 0)
            })
            actions.append(action)
        except Exception as e:
            logger.error(f"Error processing dividend data: {e}")
    
    return actions


def update_corporate_actions(symbol: str = None) -> int:
    """Update corporate actions from NSE for given symbol or all symbols.
    
    Args:
        symbol: Stock symbol (optional)
        
    Returns:
        Number of new actions added
    """
    init_database()
    
    total_added = 0
    
    # Fetch and process bonus shares
    bonus_data = fetch_nse_bonus_shares(symbol)
    bonus_actions = process_bonus_data(bonus_data)
    for action in bonus_actions:
        if add_corporate_action(action):
            total_added += 1
    
    # Fetch and process stock splits
    split_data = fetch_nse_stock_splits(symbol)
    split_actions = process_split_data(split_data)
    for action in split_actions:
        if add_corporate_action(action):
            total_added += 1
    
    # Fetch and process dividends
    dividend_data = fetch_nse_dividends(symbol)
    dividend_actions = process_dividend_data(dividend_data)
    for action in dividend_actions:
        if add_corporate_action(action):
            total_added += 1
    
    logger.info(f"Updated corporate actions for {symbol or 'all symbols'}: {total_added} new actions")
    return total_added


def get_corporate_actions_summary(symbol: str, days: int = 365) -> str:
    """Get formatted summary of corporate actions for a symbol.
    
    Args:
        symbol: Stock symbol
        days: Number of days to look back
        
    Returns:
        Formatted string with corporate actions summary
    """
    from datetime import timedelta
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
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


# Initialize database on import
init_database()
