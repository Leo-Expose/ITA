export const analysisHelp = [
  {
    question: "What does this do?",
    answer: "This runs a full AI-powered multi-agent analysis on any NSE/BSE stock. 10 AI agents collaborate to give you a trading decision:\n\n1. Market Analyst \u2014 reads price data and technical indicators (RSI, MACD, Bollinger, etc.)\n2. Social Analyst \u2014 checks social media sentiment\n3. News Analyst \u2014 scans Indian and global news (RBI, FII/DII, macro)\n4. Fundamentals Analyst \u2014 reviews balance sheet, P&L, cash flow\n5. Bull Researcher \u2014 makes the case FOR buying\n6. Bear Researcher \u2014 makes the case AGAINST buying\n7. Research Manager \u2014 judges the debate, decides Buy/Sell/Hold\n8. Trader \u2014 sets specific entry price, stop-loss, targets\n9. Risk Debate \u2014 3 analysts (aggressive/conservative/neutral) debate risk\n10. Portfolio Manager \u2014 final decision with entry/SL/target/position size",
  },
  {
    question: "When should I use this?",
    answer: "Use this when you want a comprehensive opinion on a stock before taking a trade. Best scenarios:\n\n\u2022 You found a stock via the Scanner (gap, breakout, volume spike) and want deeper analysis\n\u2022 You're considering entering a position and want a second opinion with specific entry/SL/target\n\u2022 Before earnings or major events \u2014 get an AI assessment of the risk\n\u2022 When you're unsure whether to hold or exit an existing position\n\nDon't use this for: intraday scalping (too slow, ~3-5 min), index trading (better for individual stocks)",
  },
  {
    question: "How to trade based on the result?",
    answer: "The final decision gives you a specific trading plan:\n\nStrong Buy / Buy:\n  \u2192 Enter at the suggested entry price (or at market if urgent)\n  \u2192 Place stop-loss at the SL level immediately\n  \u2192 Book partial profits at Target 1, trail SL for Target 2\n  \u2192 Respect the time horizon (don't hold beyond it)\n\nHold:\n  \u2192 No new entry. If you already own it, keep holding.\n  \u2192 Re-analyze after the suggested time horizon\n\nSell / Short:\n  \u2192 Exit existing long positions\n  \u2192 For F&O traders: consider puts or short futures at the entry level\n  \u2192 Place SL above the resistance level mentioned\n\nKey rules:\n  \u2022 Always use the stop-loss. No exceptions.\n  \u2022 Position size: never risk more than 1-2% of capital on one trade\n  \u2022 If the analysis says HOLD but you have no position, just skip it",
  },
  {
    question: "How accurate is it?",
    answer: "This is an AI tool, not a guarantee. Use it as one input in your decision-making:\n\n\u2022 The agent considers technicals, fundamentals, news, and sentiment \u2014 more comprehensive than manual analysis\n\u2022 Bull vs Bear debate reduces confirmation bias\n\u2022 The agent can make mistakes, especially around sudden events (unexpected RBI decisions, global crises)\n\u2022 Run backtests on historical dates to see how it would have performed\n\u2022 Track P&L on your actual trades to build confidence over time\n\nTip: Cross-check the agent's entry/SL/target with the Support/Resistance levels from the Strategies page. If they align, it's a stronger signal.",
  },
];

export const scannerHelp = [
  {
    question: "What does the Scanner do?",
    answer: "The Scanner automatically checks all stocks in your selected universe (NIFTY 50 / 100 / BSE 250) for three types of short-term trading signals:\n\n1. Gap Scanner \u2014 finds stocks that opened significantly higher or lower than yesterday's close\n2. Volume Spike \u2014 finds stocks trading with unusually high volume compared to their average\n3. Breakout \u2014 finds stocks that just broke above their recent high (20-day default)\n\nIt fetches live data from yfinance and typically takes 30-60 seconds for NIFTY 50, or 2-3 minutes for BSE 250.",
  },
  {
    question: "How to trade Gap Up/Down stocks?",
    answer: "Gap Up (stock opened higher than prev close):\n  \u2022 Gap Up + NOT filled (price still above prev close) = strong bullish momentum\n    \u2192 Consider buying with SL below the gap level (prev close)\n    \u2192 Target: next resistance level\n  \u2022 Gap Up + filled (price came back down) = weak gap, possible reversal\n    \u2192 Avoid or wait for re-test of the gap level\n\nGap Down (stock opened lower than prev close):\n  \u2022 Gap Down + NOT filled = strong selling pressure\n    \u2192 Avoid buying. Consider shorting with SL above gap level\n  \u2022 Gap Down + filled (price recovered) = potential reversal/buy signal\n    \u2192 Buy near prev close level with tight SL\n\nKey rules:\n  \u2022 Trade gaps ONLY in first 30-60 minutes of market open (9:15-10:15 AM)\n  \u2022 Use the \"Analyze\" link to get the full AI opinion before entering\n  \u2022 Larger gaps (>3%) are riskier \u2014 use smaller position sizes",
  },
  {
    question: "How to trade Volume Spike stocks?",
    answer: "Volume spike means institutions (FII/DII/mutual funds) are actively trading the stock. This is one of the strongest signals:\n\nBullish Volume Spike (price up + volume 2x+ avg):\n  \u2192 Strong buying interest. This stock is in play.\n  \u2192 Enter on pullback to VWAP or nearest support\n  \u2192 SL below today's low\n  \u2192 Target: next resistance level\n\nBearish Volume Spike (price down + volume 2x+ avg):\n  \u2192 Heavy selling / distribution happening\n  \u2192 Avoid buying. Consider shorting on bounce to VWAP\n  \u2192 Wait for volume to normalize before considering long entry\n\nThe higher the volume ratio, the stronger the signal:\n  \u2022 2-3x = notable, worth watching\n  \u2022 3-5x = significant institutional activity\n  \u2022 5x+ = major event (earnings, block deal, news)",
  },
  {
    question: "How to trade Breakout stocks?",
    answer: "A breakout means the stock just made a new 20-day high \u2014 a sign of momentum:\n\nVolume-Confirmed Breakout (breakout + volume >1.5x avg):\n  \u2192 This is a high-probability setup\n  \u2192 Enter at or near the breakout level\n  \u2192 SL just below the breakout level (old resistance becomes support)\n  \u2192 Target: next major resistance (use Strategies page to find it)\n\nWeak Breakout (breakout but low volume):\n  \u2192 Higher chance of false breakout / bull trap\n  \u2192 Wait for a pullback and re-test of the breakout level\n  \u2192 Only enter if the re-test holds (price bounces off old resistance)\n\nKey rules:\n  \u2022 Don't chase breakouts \u2014 if it's already 3%+ above the level, wait for pullback\n  \u2022 Best breakouts happen in first 1-2 hours of market (9:15-11:15 AM)\n  \u2022 Always check the broader market (NIFTY trend) \u2014 breakouts fail more in a falling market",
  },
  {
    question: "When should I run the Scanner?",
    answer: "Best times to scan:\n  \u2022 9:30 AM \u2014 30 min after market open, gaps and early volume visible\n  \u2022 11:00 AM \u2014 morning session patterns established\n  \u2022 2:00 PM \u2014 last hour setups for next-day swing trades\n\nFor short-term trading:\n  1. Run Scanner \u2192 find interesting stocks\n  2. Check Strategies page \u2192 verify S/R levels and pivot points\n  3. Run Analysis \u2192 get the full AI opinion with entry/SL/target\n  4. If everything aligns \u2192 take the trade\n\nThe Scanner is your first filter \u2014 it narrows 100-250 stocks down to 5-10 actionable ideas.",
  },
];

export const strategiesHelp = [
  {
    question: "What are Support and Resistance levels?",
    answer: "Support = a price level where the stock tends to stop falling and bounce back up. Think of it as a \"floor.\"\nResistance = a price level where the stock tends to stop rising and pull back. Think of it as a \"ceiling.\"\n\nThese levels form because of collective market memory \u2014 many traders bought or sold at these prices before, so they react when the price returns there.\n\nS1 = nearest support (closest floor below current price)\nS2 = second support (deeper floor if S1 breaks)\nS3 = third support (emergency floor)\nR1 = nearest resistance (closest ceiling above)\nR2, R3 = higher ceilings\n\nStrength = how many times the price has touched this level. More touches = stronger level.",
  },
  {
    question: "How to trade using Support/Resistance?",
    answer: "Buy near support:\n  \u2192 When price drops to S1 and shows signs of bouncing (green candle, volume increase)\n  \u2192 Entry: at or slightly above S1\n  \u2192 Stop-loss: below S1 (if S1 breaks, the trade thesis is wrong)\n  \u2192 Target: R1 (nearest resistance above)\n\nSell/Short near resistance:\n  \u2192 When price rises to R1 and shows rejection (red candle, wick)\n  \u2192 Entry: at or slightly below R1\n  \u2192 Stop-loss: above R1\n  \u2192 Target: S1\n\nBreakout trade:\n  \u2192 When price breaks ABOVE R1 with high volume \u2192 R1 becomes new support\n  \u2192 Buy on the breakout or on a pullback to R1\n  \u2192 SL: below R1 (now support)\n  \u2192 Target: R2\n\nRisk-reward tip: Only take trades where distance to target is at least 2x your stop-loss distance.",
  },
  {
    question: "What are Pivot Points?",
    answer: "Pivot Points are calculated daily from yesterday's High, Low, and Close. They give you 7 levels for the day:\n\nPP (Pivot Point) = (High + Low + Close) / 3\n  \u2192 The \"fair value\" for the day. Price above PP = bullish bias, below = bearish.\n\nR1, R2, R3 = Resistance levels above PP\nS1, S2, S3 = Support levels below PP\n\nThese are widely used by intraday and swing traders. Many institutional traders use pivot points, so they often act as self-fulfilling prophecies.",
  },
  {
    question: "How to trade using Pivot Points?",
    answer: "Intraday strategy:\n  1. Check if market opens above or below PP\n  2. Above PP \u2192 bullish bias \u2192 look for long entries\n     \u2022 Buy near PP if it acts as support\n     \u2022 Target R1, then R2\n     \u2022 SL below PP\n  3. Below PP \u2192 bearish bias \u2192 look for short entries or avoid longs\n     \u2022 Short near PP if it acts as resistance\n     \u2022 Target S1, then S2\n     \u2022 SL above PP\n\nSwing trading:\n  \u2022 R2/S2 are your primary targets for multi-day trades\n  \u2022 R3/S3 are extreme levels \u2014 expect reversal near these\n  \u2022 If price closes above R1 \u2192 likely to reach R2 next day\n  \u2022 If price closes below S1 \u2192 likely to reach S2 next day\n\nCombine with Analysis: Run the AI analysis, then check if the entry/SL/target aligns with pivot levels. If they match, it's a much stronger signal.",
  },
  {
    question: "Which time period should I use?",
    answer: "Choose based on your trading horizon:\n\n1 Month \u2192 for intraday and 1-3 day trades. Shows very recent S/R levels.\n3 Months (recommended) \u2192 for swing trades (1-2 weeks). Good balance of recent and established levels.\n6 Months \u2192 for positional trades (2-4 weeks). Shows more significant levels.\n1 Year \u2192 for longer-term trades. Shows major structural S/R that even institutions respect.\n\nTip: Start with 3 months. If the levels seem too close together, switch to 6 months for clearer levels.",
  },
];

export const backtestHelp = [
  {
    question: "What is backtesting?",
    answer: "Backtesting answers the question: \"If I had used this AI agent in the past, would it have made money?\"\n\nIt runs the full AI analysis pipeline on historical dates, gets a Buy/Sell/Hold decision for each date, then checks what actually happened to the stock price the next day.\n\nExample: The AI says BUY RELIANCE on March 5 at Rs.2,850. Next day the price went to Rs.2,900.\nResult: +1.75% profit. This is a \"win.\"\n\nBy doing this across many dates, you build a track record: win rate, total return, max drawdown.",
  },
  {
    question: "How to configure a backtest?",
    answer: "Ticker: The stock to test (e.g., RELIANCE, TCS, HDFCBANK)\n\nStart/End Date: The period to test over. Use recent dates (last 3-6 months) for relevant results.\n\nInterval Days: Gap between analysis dates.\n  \u2022 5-7 days = weekly analysis (recommended, ~5-8 trades per month)\n  \u2022 1 day = daily analysis (expensive, many API calls)\n  \u2022 14 days = bi-weekly (fewer trades, cheaper to run)\n\nCapital: Starting portfolio value in INR. Used to calculate absolute P&L.\n\nPosition Size %: How much of your capital to risk per trade.\n  \u2022 10% = conservative (recommended)\n  \u2022 20% = moderate\n  \u2022 50%+ = aggressive (not recommended)\n\nEnable Learning: When ON, the agent reflects after each trade and remembers what worked and what didn't. Later trades in the same backtest benefit from this memory.",
  },
  {
    question: "How to interpret backtest results?",
    answer: "Total Return: Overall profit/loss percentage. Compare to NIFTY 50 return for the same period.\n\nWin Rate: Percentage of winning trades.\n  \u2022 >55% = good for short-term trading\n  \u2022 >60% = excellent\n  \u2022 <50% = the agent is losing more than it wins\n\nMax Drawdown: The worst peak-to-trough decline during the backtest.\n  \u2022 <5% = excellent risk management\n  \u2022 5-10% = acceptable\n  \u2022 >15% = too risky, reduce position size\n\nLook at the trade table: Are the losses bigger than the wins? Even with 60% win rate, if average loss > average win, you'll lose money.\n\nTip: Run the same backtest with Enable Learning ON and OFF. Compare results to see if the agent improves with memory.",
  },
  {
    question: "How much does a backtest cost?",
    answer: "Each date in the backtest runs the full 10-agent AI pipeline, making ~15-17 Claude API calls.\n\nEstimated cost per trade: ~Rs.60-80 (with Claude Sonnet)\n\nExamples:\n  \u2022 5 dates = ~Rs.300-400 (~15-25 min runtime)\n  \u2022 10 dates = ~Rs.600-800 (~30-50 min runtime)\n  \u2022 20 dates = ~Rs.1,200-1,600 (~1-2 hours runtime)\n\nStart with 5 dates to validate, then expand if results look promising.",
  },
  {
    question: "When should I run a backtest?",
    answer: "Run backtests to:\n  \u2022 Build confidence before trading real money on the agent's signals\n  \u2022 Compare different stocks \u2014 which ones does the agent perform best on?\n  \u2022 Test the impact of Enable Learning \u2014 does the agent improve over time?\n  \u2022 Validate after making changes to the agent prompts or configuration\n\nGood practice:\n  1. Backtest on 5-10 dates for 3-4 different stocks\n  2. Check if win rate is consistently >55%\n  3. If yes \u2192 start following the agent's signals with small positions\n  4. Track real P&L on the History page\n  5. Periodically re-backtest to ensure continued accuracy",
  },
];

export const chartsHelp = [
  {
    question: "How to read a candlestick chart?",
    answer: "Each candlestick represents one day (or period) of trading:\n\nGreen candle = price went UP (close > open)\n  \u2022 Bottom of body = open price\n  \u2022 Top of body = close price\n  \u2022 Upper wick = highest price of the day\n  \u2022 Lower wick = lowest price of the day\n\nRed candle = price went DOWN (close < open)\n  \u2022 Top of body = open price\n  \u2022 Bottom of body = close price\n\nLong body = strong momentum in that direction\nSmall body with long wicks = indecision (Doji pattern)\nLong lower wick = buyers stepped in (bullish signal)\nLong upper wick = sellers pushed back (bearish signal)",
  },
  {
    question: "What do the volume bars mean?",
    answer: "Volume bars at the bottom show how many shares were traded:\n\nGreen volume bar = price went up on that day\nRed volume bar = price went down on that day\n\nHigh volume = strong conviction (many traders agree on the direction)\nLow volume = weak conviction (the move may not sustain)\n\nKey patterns:\n  \u2022 Price up + high volume = strong bullish signal\n  \u2022 Price up + low volume = weak rally, may reverse\n  \u2022 Price down + high volume = strong selling (panic or institutional exit)\n  \u2022 Price down + low volume = normal pullback, less concerning\n\nTip: Compare current volume to the average. The Scanner page shows you stocks with unusual volume.",
  },
  {
    question: "Which time period should I use?",
    answer: "Choose based on your trading style:\n\n1 Month \u2192 Intraday and very short-term (1-3 day) trades\n  \u2022 Shows recent price action in detail\n  \u2022 Good for identifying entry/exit points\n\n3 Months (recommended) \u2192 Swing trades (1-2 weeks)\n  \u2022 Shows medium-term trends and patterns\n  \u2022 Good balance of detail and context\n\n6 Months \u2192 Positional trades (2-4 weeks)\n  \u2022 Shows broader trend direction\n  \u2022 Identifies major support/resistance levels\n\n1-2 Years \u2192 Long-term context\n  \u2022 Shows if the stock is in an overall uptrend or downtrend\n  \u2022 Useful for identifying 52-week highs/lows",
  },
  {
    question: "How to use charts with the AI analysis?",
    answer: "Best workflow:\n  1. Run Analysis on a stock \u2192 get Buy/Sell signal with entry/SL/target\n  2. Open Charts for the same stock\n  3. Visually verify:\n     \u2022 Is the entry price near a support level? (good)\n     \u2022 Is the SL below a clear support? (good)\n     \u2022 Is the target near a resistance level? (realistic)\n  4. Check the volume \u2014 is there buying interest?\n  5. Check the trend \u2014 is the stock in an uptrend? (better for Buy signals)\n\nIf the chart confirms the AI's analysis \u2192 stronger signal, take the trade.\nIf the chart contradicts \u2192 be cautious, reduce position size or skip.",
  },
];
