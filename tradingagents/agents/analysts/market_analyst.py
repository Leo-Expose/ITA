from datetime import datetime, timedelta

import yfinance as yf
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_indicators,
    get_language_instruction,
    get_stock_data,
)
from tradingagents.utils.rule_based_analysis import create_rule_based_report


def create_market_analyst(llm):
    def _load_recent_price_data(ticker: str, trade_date: str):
        safe_ticker = ticker if "." in ticker else f"{ticker}.NS"
        end_dt = datetime.strptime(trade_date, "%Y-%m-%d") + timedelta(days=1)
        start_dt = end_dt - timedelta(days=90)
        hist = yf.Ticker(safe_ticker).history(start=start_dt, end=end_dt)
        if hist is None or hist.empty:
            return None
        return hist.reset_index()[["Open", "High", "Low", "Close", "Volume"]]

    def market_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        # Validate inputs
        if not ticker or not current_date:
            return {
                "messages": [AIMessage(content="Error: Missing ticker or date for analysis")],
                "market_report": "Analysis failed due to missing inputs"
            }

        # Build instrument context for LLM
        instrument_context = f"""
Instrument: {ticker}
Analysis Date: {current_date}
Market: Indian (NSE/BSE)
Trading Session: 9:15 AM - 3:30 PM IST
"""

        tools = [
            get_stock_data,
            get_indicators,
        ]

        system_message = (
            """You are a short-term trading analyst specializing in the **Indian stock market (NSE/BSE)**. Your role is to analyze technical indicators for short-term trading decisions (intraday to 1-week horizon). Select up to **8 indicators** that are most relevant for short-term momentum and swing trading. Categories and indicators:

Moving Averages:
- close_50_sma: 50 SMA: Medium-term trend. For short-term: acts as dynamic support/resistance. Price above 50 SMA = bullish bias.
- close_200_sma: 200 SMA: Long-term trend benchmark. Useful to confirm overall trend context even for short-term trades.
- close_10_ema: 10 EMA: **Critical for short-term trading.** Captures quick momentum shifts, ideal for swing entry/exit signals.

MACD Related:
- macd: MACD: Momentum via EMA differences. Short-term: look for crossovers on daily charts for 2-5 day swing signals.
- macds: MACD Signal: EMA smoothing of MACD. Crossovers with MACD line trigger short-term trades.
- macdh: MACD Histogram: Momentum strength. Histogram expansion = trend acceleration, contraction = potential reversal.

Momentum Indicators:
- rsi: RSI: Overbought (>70) / Oversold (<30). For short-term: use 60/40 levels in trending markets for pullback entries.

Volatility Indicators:
- boll: Bollinger Middle: 20 SMA basis for Bollinger Bands.
- boll_ub: Bollinger Upper Band: Overbought/breakout zone. Price riding upper band = strong momentum.
- boll_lb: Bollinger Lower Band: Oversold/reversal zone.
- atr: ATR: **Essential for stop-loss placement.** Use 1.5x-2x ATR for short-term stop-loss levels.

Volume-Based Indicators:
- vwma: VWMA: Volume-weighted average. Price above VWMA = buying pressure. Critical for confirming breakouts in Indian markets.

**SHORT-TERM TRADING FOCUS (Indian Market):**
- Prioritize: 10 EMA, RSI, MACD, ATR, VWMA for short-term signals
- Identify **key support/resistance levels** from recent price action
- Note **gap ups/gap downs** from previous close (common in Indian markets due to global cues)
- Check for **volume spikes** — high volume breakouts in NSE stocks are strong signals
- Consider the broader NIFTY/BANKNIFTY trend for sector-level context
- Use a **5-15 day lookback** for short-term pattern identification

When making tool calls, use exact indicator names above. Call get_stock_data first, then get_indicators. Write a detailed report with:
1. Current trend direction and strength
2. Key support and resistance levels
3. Entry zones and stop-loss levels (using ATR)
4. Short-term momentum signals
5. Volume analysis
        
        IMPORTANT: Always validate tool call parameters and use proper JSON formatting"""
            + """ Append a Markdown table summarizing: Indicator | Value | Signal (Bullish/Bearish/Neutral) | Action Implication."""
            + get_language_instruction()
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. {instrument_context}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(instrument_context=instrument_context)

        chain = prompt | llm.bind_tools(tools)

        try:
            result = chain.invoke(state["messages"])

            # Validate result
            if not result or not hasattr(result, "content"):
                return {
                    "messages": [AIMessage(content="Error: Invalid response from LLM")],
                    "market_report": "Analysis failed due to LLM error",
                }

            report = (result.content or "").strip()
            if not report:
                report = "LLM response pending tool execution."

            # Deterministic fallback section to prevent empty/low-quality output.
            try:
                df = _load_recent_price_data(ticker, current_date)
                if df is not None and not df.empty:
                    rule_report = create_rule_based_report(ticker, df)
                    report = f"{report}\n\n---\nRule-Based Cross-Check:\n{rule_report}"
            except Exception:
                pass

            return {
                "messages": [result],
                "market_report": report,
            }

        except Exception as e:
            # Handle chain invocation errors
            error_msg = f"Technical analysis failed: {str(e)}"

            # Try rule-based fallback
            try:
                df = _load_recent_price_data(ticker, current_date)
                if df is not None and not df.empty:
                    rule_report = create_rule_based_report(ticker, df)
                    error_msg = f"{error_msg}\n\n---\nRule-Based Fallback:\n{rule_report}"
            except Exception:
                pass

            return {
                "messages": [AIMessage(content=error_msg)],
                "market_report": error_msg,
            }

    return market_analyst_node
