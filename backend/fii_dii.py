"""FII/DII Daily Flow Tracker.

Fetches FII (Foreign Institutional Investor) and DII (Domestic Institutional Investor)
daily buy/sell data — the single biggest predictor of next-day market direction in Indian markets.

Data sources (with fallback chain):
1. NSE India official API (requires cookies + headers)
2. Moneycontrol scraper (fallback)
3. Manual entry via API (admin override)

Caches results in DB to avoid hammering external sources.
"""

import re
import requests
import time
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Optional, Literal, TypedDict
from backend.db import get_db


# Headers that mimic a real browser (NSE blocks most requests without these)
NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.nseindia.com/reports/fii-dii",
    "Connection": "keep-alive",
}


def _ensure_table():
    """Create fii_dii_history table if it doesn't exist."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fii_dii_history (
                date TEXT PRIMARY KEY,
                fii_buy REAL,
                fii_sell REAL,
                fii_net REAL,
                dii_buy REAL,
                dii_sell REAL,
                dii_net REAL,
                source TEXT,
                fetched_at TEXT DEFAULT (datetime('now'))
            )
        """)


def _get_nse_session() -> requests.Session:
    """Create a session with NSE cookies set."""
    session = requests.Session()
    session.headers.update(NSE_HEADERS)
    try:
        # First hit the main page to get cookies
        session.get("https://www.nseindia.com/reports/fii-dii", timeout=10)
        time.sleep(0.5)
    except Exception:
        pass
    return session


FiiDiiErrorType = Literal["missing_dependency", "blocked", "parse_error", "upstream_error", "no_cache"]


class FiiDiiFetchError(TypedDict, total=False):
    error_type: FiiDiiErrorType
    error: str
    details: str
    source: str


def _classify_exception(err: Exception) -> FiiDiiFetchError:
    msg = str(err) or err.__class__.__name__
    lowered = msg.lower()
    if isinstance(err, ImportError):
        return {"error_type": "missing_dependency", "error": "Python dependency missing", "details": msg}
    if "403" in lowered or "429" in lowered or "forbidden" in lowered or "too many requests" in lowered:
        return {"error_type": "blocked", "error": "Upstream blocked the request (rate-limit / forbidden)", "details": msg}
    if "json" in lowered and ("decode" in lowered or "parse" in lowered):
        return {"error_type": "parse_error", "error": "Upstream response changed (parse error)", "details": msg}
    return {"error_type": "upstream_error", "error": "Upstream request failed", "details": msg}


def _parse_nse_fiidii_raw(raw) -> list[dict]:
    # nse_fiidii has returned (across versions): a string table, a DataFrame-like, or list[dict]
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if hasattr(raw, "to_dict"):
        try:
            return raw.to_dict("records")
        except Exception:
            return []
    if isinstance(raw, str):
        lines = [l for l in raw.strip().split("\n") if l.strip()]
        if len(lines) < 2:
            return []
        out: list[dict] = []
        for line in lines[1:]:
            parts = line.split()
            if parts and parts[0].isdigit():
                parts = parts[1:]
            if len(parts) < 5:
                continue
            try:
                out.append(
                    {
                        "category": parts[0],
                        "date": parts[1],
                        "buyValue": float(parts[2].replace(",", "")),
                        "sellValue": float(parts[3].replace(",", "")),
                        "netValue": float(parts[4].replace(",", "")),
                    }
                )
            except Exception:
                continue
        return out
    return []


def _entries_to_fiidii(entries: list[dict], source: str) -> Optional[dict]:
    if not entries:
        return None
    result = {"fii_buy": 0, "fii_sell": 0, "fii_net": 0, "dii_buy": 0, "dii_sell": 0, "dii_net": 0}
    date_str = None
    for entry in entries:
        cat = (entry.get("category") or entry.get("clientType") or entry.get("type") or "").upper()
        buy = float(entry.get("buyValue", entry.get("buy", 0)) or 0)
        sell = float(entry.get("sellValue", entry.get("sell", 0)) or 0)
        net = float(entry.get("netValue", entry.get("net", 0)) or 0)
        d = entry.get("date") or entry.get("tradedDate") or entry.get("tradeDate")
        if d and not date_str:
            date_str = str(d)

        if "FII" in cat or "FPI" in cat or "FPI/FII" in cat:
            result["fii_buy"] = buy
            result["fii_sell"] = sell
            result["fii_net"] = net
        elif "DII" in cat:
            result["dii_buy"] = buy
            result["dii_sell"] = sell
            result["dii_net"] = net

    if date_str:
        for fmt in ("%d-%b-%Y", "%d-%b-%y", "%d/%m/%Y"):
            try:
                parsed = datetime.strptime(date_str, fmt)
                result["date"] = parsed.strftime("%Y-%m-%d")
                break
            except Exception:
                pass
        result.setdefault("date", date.today().strftime("%Y-%m-%d"))
    else:
        result["date"] = date.today().strftime("%Y-%m-%d")

    result["source"] = source
    if result["fii_buy"] == 0 and result["fii_sell"] == 0 and result["dii_buy"] == 0 and result["dii_sell"] == 0:
        # Some upstreams include only one side; still accept if nets exist, but reject fully empty rows.
        if result["fii_net"] == 0 and result["dii_net"] == 0:
            return None
    return result


def fetch_from_nse_api_with_error() -> tuple[Optional[dict], Optional[FiiDiiFetchError]]:
    """Fetch FII/DII data from NSE's JSON endpoint (cookie-primed session)."""
    url_candidates = [
        # Widely used endpoint (may change; keep a short list for resilience).
        "https://www.nseindia.com/api/fiidiiTradeReact?type=equities",
        "https://www.nseindia.com/api/fiidiiTradeReact",
    ]
    session = _get_nse_session()
    last_err: Optional[FiiDiiFetchError] = None
    for url in url_candidates:
        try:
            resp = session.get(url, timeout=10)
            if resp.status_code in (401, 403, 429):
                return None, {
                    "error_type": "blocked",
                    "error": "NSE blocked the request (cookie / bot protection / rate-limit)",
                    "details": f"HTTP {resp.status_code} from {url}",
                    "source": "nse_api",
                }
            if resp.status_code != 200:
                last_err = {
                    "error_type": "upstream_error",
                    "error": "NSE endpoint returned non-200",
                    "details": f"HTTP {resp.status_code} from {url}",
                    "source": "nse_api",
                }
                continue
            try:
                raw = resp.json()
            except Exception as e:
                last_err = {**_classify_exception(e), "source": "nse_api"}
                continue

            entries: list[dict] = []
            if isinstance(raw, list):
                entries = raw
            elif isinstance(raw, dict):
                if isinstance(raw.get("data"), list):
                    entries = raw["data"]
                elif isinstance(raw.get("data"), dict) and isinstance(raw["data"].get("data"), list):
                    entries = raw["data"]["data"]
            data = _entries_to_fiidii(entries, source="nse_api")
            if data:
                return data, None
            last_err = {
                "error_type": "parse_error",
                "error": "NSE JSON response could not be parsed",
                "details": f"No usable rows from {url}",
                "source": "nse_api",
            }
        except Exception as e:
            last_err = {**_classify_exception(e), "source": "nse_api"}
    return None, last_err or {"error_type": "upstream_error", "error": "NSE endpoint unavailable", "source": "nse_api"}


def fetch_from_nse_with_error() -> tuple[Optional[dict], Optional[FiiDiiFetchError]]:
    """Fetch latest FII/DII data from NSE via nsepython library.

    Returns:
        (data, error) where data is dict with date, fii_buy/sell/net, dii_buy/sell/net.
    """
    try:
        try:
            from nsepython import nse_fiidii
        except ImportError as e:
            return None, {**_classify_exception(e), "source": "nse"}

        try:
            raw = nse_fiidii()
        except Exception as e:
            return None, {**_classify_exception(e), "source": "nse"}

        entries = _parse_nse_fiidii_raw(raw)
        if not entries:
            return None, {"error_type": "parse_error", "error": "NSE response could not be parsed", "details": "No rows parsed from nsepython output", "source": "nse"}

        data = _entries_to_fiidii(entries, source="nsepython")
        if not data:
            return None, {"error_type": "parse_error", "error": "NSE response could not be parsed", "details": "Parsed rows did not contain FII/DII values", "source": "nsepython"}
        return data, None
    except Exception as e:
        print(f"[FII/DII] NSE fetch failed: {e}", flush=True)
        return None, {**_classify_exception(e), "source": "nsepython"}


def fetch_from_nse() -> Optional[dict]:
    data, _err = fetch_from_nse_with_error()
    return data


def fetch_from_moneycontrol() -> Optional[dict]:
    """Fallback: scrape moneycontrol's FII/DII data."""
    try:
        from bs4 import BeautifulSoup

        url = "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/"
        resp = requests.get(
            url,
            headers={
                "User-Agent": NSE_HEADERS["User-Agent"],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=15,
        )
        if resp.status_code != 200:
            return None

        html = resp.text or ""
        if "Login Consent" in html or "consent" in html.lower() and "moneycontrol" in html.lower():
            return None

        soup = BeautifulSoup(html, "html.parser")

        # Find any table rows that look like: Date | FII Gross Purchase | FII Gross Sales | FII Net | DII Gross Purchase | DII Gross Sales | DII Net
        # We scan row-by-row and extract 7 cells with numeric values in expected positions.
        def to_float(s: str) -> Optional[float]:
            s = (s or "").strip()
            if not s:
                return None
            s = s.replace(",", "")
            # Sometimes net values include parentheses or non-breaking spaces
            s = s.replace("(", "-").replace(")", "")
            m = re.search(r"-?\d+(?:\.\d+)?", s)
            return float(m.group(0)) if m else None

        best_row = None
        for tr in soup.find_all("tr"):
            tds = tr.find_all(["td", "th"])
            if len(tds) < 7:
                continue
            cells = [td.get_text(" ", strip=True) for td in tds]
            # Date is usually first cell like 30-Apr-2026
            if not re.search(r"\b\d{1,2}-[A-Za-z]{3}-\d{4}\b", cells[0]):
                continue
            # Skip summary rows like "Month Till Date"
            if "month" in cells[0].lower():
                continue
            nums = [to_float(c) for c in cells[1:7]]
            if any(v is None for v in nums):
                continue
            best_row = (cells[0], nums)
            break

        if not best_row:
            return None

        date_str, nums = best_row
        fii_buy, fii_sell, fii_net, dii_buy, dii_sell, dii_net = nums
        try:
            parsed = datetime.strptime(date_str, "%d-%b-%Y")
            out_date = parsed.strftime("%Y-%m-%d")
        except Exception:
            out_date = date.today().strftime("%Y-%m-%d")

        return {
            "date": out_date,
            "fii_buy": fii_buy,
            "fii_sell": fii_sell,
            "fii_net": fii_net,
            "dii_buy": dii_buy,
            "dii_sell": dii_sell,
            "dii_net": dii_net,
            "source": "moneycontrol",
        }
    except Exception:
        return None


def fetch_from_moneycontrol_with_error() -> tuple[Optional[dict], Optional[FiiDiiFetchError]]:
    try:
        data = fetch_from_moneycontrol()
        if not data:
            return None, {"error_type": "blocked", "error": "Moneycontrol fallback blocked/unavailable", "details": "No parseable table (possible consent/bot protection)", "source": "moneycontrol"}
        return data, None
    except Exception as e:
        return None, {**_classify_exception(e), "source": "moneycontrol"}


def get_today_data(force_refresh: bool = False) -> Optional[dict]:
    """Get today's FII/DII data — checks cache first, then fetches if needed."""
    _ensure_table()
    today_str = date.today().strftime("%Y-%m-%d")

    if not force_refresh:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM fii_dii_history WHERE date = ?", (today_str,)
            ).fetchone()
            if row:
                d = dict(row)
                # If fetched within last hour, use cache
                fetched = datetime.fromisoformat(d["fetched_at"])
                if (datetime.now() - fetched).total_seconds() < 3600:
                    return d

    # Fetch fresh
    data = fetch_from_nse()
    if not data:
        data = fetch_from_moneycontrol()

    if data:
        save_data(data)
        return get_data_for_date(data["date"])

    # Fail-soft: if live fetch fails (NSE blocks), return latest cached row (stale).
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM fii_dii_history ORDER BY date DESC LIMIT 1"
        ).fetchone()
        if row:
            d = dict(row)
            d["stale"] = True
            return d

    return None


def get_today_data_with_meta(force_refresh: bool = False) -> tuple[Optional[dict], Optional[FiiDiiFetchError]]:
    """Like get_today_data(), but also returns structured error info when live fetch fails."""
    _ensure_table()
    today_str = date.today().strftime("%Y-%m-%d")

    if not force_refresh:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM fii_dii_history WHERE date = ?", (today_str,)
            ).fetchone()
            if row:
                d = dict(row)
                fetched = datetime.fromisoformat(d["fetched_at"])
                if (datetime.now() - fetched).total_seconds() < 3600:
                    return d, None

    # Fetch fresh (NSE JSON -> nsepython -> Moneycontrol)
    data, err = fetch_from_nse_api_with_error()
    if not data:
        data, err2 = fetch_from_nse_with_error()
        err = err2 or err
    if not data:
        data, err2 = fetch_from_moneycontrol_with_error()
        err = err2 or err

    if data:
        save_data(data)
        return get_data_for_date(data["date"]), None

    # Fail-soft: if live fetch fails, return latest cached row (stale) if any.
    with get_db() as conn:
        row = conn.execute("SELECT * FROM fii_dii_history ORDER BY date DESC LIMIT 1").fetchone()
        if row:
            d = dict(row)
            d["stale"] = True
            # surface why live refresh failed (useful for UI)
            if err:
                d["last_error_type"] = err.get("error_type")
                d["last_error"] = err.get("error")
            return d, None

    # Cold start: no cache exists
    if not err:
        err = {"error_type": "no_cache", "error": "No FII/DII cache exists yet", "details": "No live data and no cached rows"}
    else:
        err = {**err, "details": err.get("details") or "No live data and no cached rows"}
    return None, err


def save_data(data: dict):
    """Save FII/DII data to DB."""
    _ensure_table()
    with get_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO fii_dii_history
            (date, fii_buy, fii_sell, fii_net, dii_buy, dii_sell, dii_net, source, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
            (
                data.get("date"),
                data.get("fii_buy"),
                data.get("fii_sell"),
                data.get("fii_net"),
                data.get("dii_buy"),
                data.get("dii_sell"),
                data.get("dii_net"),
                data.get("source", "manual"),
            ),
        )


def manual_entry(date_str: str, fii_net: float, dii_net: float,
                 fii_buy: float = None, fii_sell: float = None,
                 dii_buy: float = None, dii_sell: float = None) -> dict:
    """Manually enter FII/DII data for a date (used when scraping fails)."""
    if fii_buy is None:
        # If only net given, estimate buy/sell as +/- net
        fii_buy = abs(fii_net) if fii_net > 0 else 0
        fii_sell = abs(fii_net) if fii_net < 0 else 0
    if dii_buy is None:
        dii_buy = abs(dii_net) if dii_net > 0 else 0
        dii_sell = abs(dii_net) if dii_net < 0 else 0

    data = {
        "date": date_str,
        "fii_buy": fii_buy,
        "fii_sell": fii_sell,
        "fii_net": fii_net,
        "dii_buy": dii_buy,
        "dii_sell": dii_sell,
        "dii_net": dii_net,
        "source": "manual",
    }
    save_data(data)
    return data


def get_data_for_date(date_str: str) -> Optional[dict]:
    """Get FII/DII data for a specific date."""
    _ensure_table()
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM fii_dii_history WHERE date = ?", (date_str,)
        ).fetchone()
        return dict(row) if row else None


def get_recent_history(days: int = 10) -> list[dict]:
    """Get FII/DII data for the last N days."""
    _ensure_table()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM fii_dii_history ORDER BY date DESC LIMIT ?", (days,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_market_bias() -> dict:
    """Compute market bias based on recent FII/DII flows.

    Returns a structured assessment used by the recommendation engine.
    """
    history = get_recent_history(days=5)
    if not history:
        return {
            "bias": "NEUTRAL",
            "confidence": "NONE",
            "score_adjustment": 0,
            "reasoning": "No FII/DII data available",
            "today_fii_net": None,
            "today_dii_net": None,
        }

    today = history[0]
    fii_today = today.get("fii_net") or 0
    dii_today = today.get("dii_net") or 0

    # 5-day FII trend
    fii_5d = sum((d.get("fii_net") or 0) for d in history)
    dii_5d = sum((d.get("dii_net") or 0) for d in history)

    # Determine bias
    bias = "NEUTRAL"
    confidence = "LOW"
    score_adj = 0
    reasoning_parts = []

    # Strong FII selling (>2000 Cr) — bearish
    if fii_today < -2000:
        bias = "BEARISH"
        confidence = "HIGH"
        score_adj = -1.5
        reasoning_parts.append(f"FIIs selling heavily today (Rs.{fii_today:,.0f} Cr)")
    elif fii_today < -1000:
        bias = "BEARISH"
        confidence = "MEDIUM"
        score_adj = -1.0
        reasoning_parts.append(f"FIIs net sellers today (Rs.{fii_today:,.0f} Cr)")
    elif fii_today > 2000:
        bias = "BULLISH"
        confidence = "HIGH"
        score_adj = +1.5
        reasoning_parts.append(f"FIIs buying aggressively today (+Rs.{fii_today:,.0f} Cr)")
    elif fii_today > 1000:
        bias = "BULLISH"
        confidence = "MEDIUM"
        score_adj = +1.0
        reasoning_parts.append(f"FIIs net buyers today (+Rs.{fii_today:,.0f} Cr)")

    # DII offset
    if bias == "BEARISH" and dii_today > abs(fii_today) * 0.7:
        # DIIs absorbing the FII selling
        bias = "MIXED"
        score_adj = score_adj * 0.5  # reduce penalty
        reasoning_parts.append(f"DIIs absorbing some selling (+Rs.{dii_today:,.0f} Cr)")
    elif bias == "BULLISH" and dii_today < -abs(fii_today) * 0.5:
        bias = "MIXED"
        score_adj = score_adj * 0.5
        reasoning_parts.append(f"But DIIs selling (Rs.{dii_today:,.0f} Cr)")

    # 5-day trend
    if fii_5d < -5000:
        reasoning_parts.append(f"FIIs sold Rs.{abs(fii_5d):,.0f} Cr over 5 days — sustained outflow")
        if bias == "NEUTRAL":
            bias = "BEARISH"
            confidence = "MEDIUM"
            score_adj = -0.5
    elif fii_5d > 5000:
        reasoning_parts.append(f"FIIs bought Rs.{fii_5d:,.0f} Cr over 5 days — sustained inflow")
        if bias == "NEUTRAL":
            bias = "BULLISH"
            confidence = "MEDIUM"
            score_adj = +0.5

    if not reasoning_parts:
        reasoning_parts.append("FII/DII flows are neutral today")

    return {
        "bias": bias,
        "confidence": confidence,
        "score_adjustment": round(score_adj, 2),
        "reasoning": ". ".join(reasoning_parts),
        "today_fii_net": round(fii_today, 0),
        "today_dii_net": round(dii_today, 0),
        "fii_5d_net": round(fii_5d, 0),
        "dii_5d_net": round(dii_5d, 0),
        "data_date": today.get("date"),
    }
