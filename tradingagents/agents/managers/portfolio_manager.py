from tradingagents.agents.utils.agent_utils import build_instrument_context, get_language_instruction


def create_portfolio_manager(llm, memory):
    def portfolio_manager_node(state) -> dict:

        instrument_context = build_instrument_context(state["company_of_interest"])

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        market_research_report = state["market_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        sentiment_report = state["sentiment_report"]
        research_plan = state["investment_plan"]
        trader_plan = state["trader_investment_plan"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""As the Portfolio Manager for an **Indian market (NSE/BSE) short-term trading desk**, synthesize the risk analysts' debate and deliver the final trading decision.

{instrument_context}

---

**Rating Scale** (use exactly one):
- **Strong Buy**: High conviction — enter immediately with full planned position
- **Buy**: Favorable setup — enter with partial position, scale in on dips
- **Hold**: No new action — maintain existing position if any
- **Sell**: Exit existing position or avoid entry
- **Short**: Consider short position or put options (for F&O eligible stocks)

**Context:**
- Research Manager's investment plan: **{research_plan}**
- Trader's transaction proposal: **{trader_plan}**
- Lessons from past decisions: **{past_memory_str}**

**Required Output Structure:**
1. **Rating**: One of Strong Buy / Buy / Hold / Sell / Short
2. **Entry Price**: Specific price level or "at market"
3. **Stop-Loss**: Mandatory — specific price with reasoning
4. **Target 1**: First profit-taking level
5. **Target 2**: Extended target (if momentum sustains)
6. **Position Size**: % of trading capital to deploy
7. **Time Horizon**: Intraday / 2-3 days / 1 week / 2 weeks
8. **Risk-Reward Ratio**: Computed from entry/SL/target
9. **Executive Summary**: Concise action plan with key risk levels
10. **Investment Thesis**: Detailed reasoning from the debate and reflections

**Indian Market Risk Factors to Consider:**
- NIFTY/BANKNIFTY trend and level (broader market context)
- FII/DII flow direction (institutional sentiment)
- RBI policy stance and upcoming announcements
- INR/USD movement impact on the stock
- Global cues: US markets, SGX Nifty, crude oil prices
- NSE circuit limits and liquidity of the stock
- Upcoming results/events that could cause gaps

---

**Risk Analysts Debate History:**
{history}

---

Be decisive. Every price level must be specific (not vague ranges). Ground conclusions in evidence from the analysts.{get_language_instruction()}"""

        response = llm.invoke(prompt)

        new_risk_debate_state = {
            "judge_decision": response.content,
            "history": risk_debate_state["history"],
            "aggressive_history": risk_debate_state["aggressive_history"],
            "conservative_history": risk_debate_state["conservative_history"],
            "neutral_history": risk_debate_state["neutral_history"],
            "latest_speaker": "Judge",
            "current_aggressive_response": risk_debate_state["current_aggressive_response"],
            "current_conservative_response": risk_debate_state["current_conservative_response"],
            "current_neutral_response": risk_debate_state["current_neutral_response"],
            "count": risk_debate_state["count"],
        }

        return {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": response.content,
        }

    return portfolio_manager_node
