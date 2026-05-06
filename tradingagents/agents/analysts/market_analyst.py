from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_indicators,
    get_language_instruction,
    get_stock_data,
)
from tradingagents.dataflows.config import get_config


def create_market_analyst(llm):

    def market_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])

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
5. Volume analysis"""
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

        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "market_report": report,
        }

    return market_analyst_node
