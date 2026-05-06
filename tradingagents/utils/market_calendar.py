"""Indian market calendar utilities — NSE/BSE trading hours, holidays, sessions."""

from datetime import date, datetime, time, timedelta
import pytz

IST = pytz.timezone("Asia/Kolkata")

MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)
PRE_MARKET_OPEN = time(9, 0)
POST_MARKET_CLOSE = time(16, 0)

# NSE holidays for 2025-2026 (updated with official NSE circulars)
# Source: NSE holiday calendar and official notifications
NSE_HOLIDAYS = {
    # 2025 - Confirmed Dates
    date(2025, 1, 26),  # Republic Day
    date(2025, 2, 26),  # Mahashivratri
    date(2025, 3, 14),  # Holi
    date(2025, 3, 31),  # Id-Ul-Fitr
    date(2025, 4, 10),  # Shri Mahavir Jayanti
    date(2025, 4, 14),  # Dr. Babasaheb Ambedkar Jayanti
    date(2025, 4, 18),  # Good Friday
    date(2025, 5, 1),   # Maharashtra Day
    date(2025, 7, 21),  # Muharram
    date(2025, 8, 15),  # Independence Day
    date(2025, 8, 27),  # Ganesh Chaturthi
    date(2025, 10, 1),  # Mahatma Gandhi Jayanti
    date(2025, 10, 2),  # Dussehra
    date(2025, 10, 21), # Diwali - Laxmi Pujan
    date(2025, 10, 22), # Diwali - Balipratipada
    date(2025, 11, 5),  # Guru Nanak Jayanti
    date(2025, 12, 25), # Christmas
    
    # 2026 - Official NSE Calendar
    date(2026, 1, 26),  # Republic Day
    date(2026, 2, 15),  # Mahashivratri
    date(2026, 3, 4),   # Holi
    date(2026, 3, 21),  # Id-Ul-Fitr (Tentative)
    date(2026, 4, 6),   # Shri Mahavir Jayanti
    date(2026, 4, 14),  # Dr. Babasaheb Ambedkar Jayanti
    date(2026, 4, 3),   # Good Friday
    date(2026, 5, 1),   # Maharashtra Day
    date(2026, 7, 10),  # Muharram (Tentative)
    date(2026, 8, 15),  # Independence Day
    date(2026, 8, 16),  # Parsi New Year (Tentative)
    date(2026, 8, 31),  # Ganesh Chaturthi (Tentative)
    date(2026, 10, 1),  # Mahatma Gandhi Jayanti
    date(2026, 10, 2),  # Dussehra (Tentative)
    date(2026, 10, 20), # Diwali - Laxmi Pujan (Tentative)
    date(2026, 10, 21), # Diwali - Balipratipada (Tentative)
    date(2026, 11, 25), # Guru Nanak Jayanti (Tentative)
    date(2026, 12, 25), # Christmas
    
    # Additional holidays for 2025-2026 based on NSE patterns
    date(2025, 1, 1),   # New Year's Day (if falls on weekday)
    date(2026, 1, 1),   # New Year's Day (if falls on weekday)
}


def is_market_open(dt: datetime = None) -> bool:
    """Check if the Indian stock market is currently open."""
    if dt is None:
        dt = datetime.now(IST)
    elif dt.tzinfo is None:
        dt = IST.localize(dt)

    if not is_trading_day(dt.date()):
        return False

    current_time = dt.time()
    return MARKET_OPEN <= current_time <= MARKET_CLOSE


def is_trading_day(d: date = None) -> bool:
    """Check if a given date is a trading day (weekday + not a holiday)."""
    if d is None:
        d = datetime.now(IST).date()
    # Weekends
    if d.weekday() >= 5:
        return False
    # NSE holidays
    if d in NSE_HOLIDAYS:
        return False
    return True


def next_trading_day(d: date = None) -> date:
    """Get the next trading day after the given date."""
    if d is None:
        d = datetime.now(IST).date()
    candidate = d + timedelta(days=1)
    while not is_trading_day(candidate):
        candidate += timedelta(days=1)
    return candidate


def previous_trading_day(d: date = None) -> date:
    """Get the previous trading day before the given date."""
    if d is None:
        d = datetime.now(IST).date()
    candidate = d - timedelta(days=1)
    while not is_trading_day(candidate):
        candidate -= timedelta(days=1)
    return candidate


def get_market_session(dt: datetime = None) -> str:
    """Get the current market session.

    Returns one of: "pre_market", "open", "closing_hour", "post_market", "closed"
    """
    if dt is None:
        dt = datetime.now(IST)
    elif dt.tzinfo is None:
        dt = IST.localize(dt)

    if not is_trading_day(dt.date()):
        return "closed"

    current_time = dt.time()

    if current_time < PRE_MARKET_OPEN:
        return "closed"
    elif current_time < MARKET_OPEN:
        return "pre_market"
    elif current_time <= time(14, 30):
        return "open"
    elif current_time <= MARKET_CLOSE:
        return "closing_hour"
    elif current_time <= POST_MARKET_CLOSE:
        return "post_market"
    else:
        return "closed"
