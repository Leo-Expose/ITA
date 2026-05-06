
from tradingagents.agents.utils.agent_utils import build_instrument_context


def create_research_manager(llm, memory):
    def research_manager_node(state) -> dict:
        instrument_context = build_instrument_context(state["company_of_interest"])
        history = state["investment_debate_state"].get("history", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        investment_debate_state = state["investment_debate_state"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""As the Research Manager for an **Indian market (NSE/BSE) short-term trading desk**, critically evaluate this debate round and make a definitive decision for a short-term trade (intraday to 2 weeks).

Your recommendation — Buy, Sell, or Hold — must be clear, actionable, and specific to the short-term horizon. Avoid defaulting to Hold unless both sides present equally compelling arguments with no clear edge. Commit to the stance with the strongest short-term evidence.

Develop a detailed trading plan for the trader:

1. **Recommendation**: Buy / Sell / Hold — decisive, with the strongest debate arguments supporting it
2. **Rationale**: Why these arguments win for the SHORT-TERM (not long-term investment thesis)
3. **Entry Strategy**: Specific entry price/zone, or conditions for entry (e.g., "buy on pullback to 2800 support")
4. **Stop-Loss Level**: Specific price — non-negotiable for short-term trades
5. **Profit Targets**: Target 1 (conservative) and Target 2 (extended)
6. **Time Horizon**: How long to hold — intraday / 2-3 days / 1 week
7. **Key Risks**: Top 2-3 risks to monitor during the trade

**Indian Market Context**: Consider NIFTY trend, FII/DII flows, sector momentum, and upcoming events (RBI policy, earnings, expiry) when making your decision.

Past reflections on mistakes:
\"{past_memory_str}\"

{instrument_context}

Debate History:
{history}"""
        response = llm.invoke(prompt)

        new_investment_debate_state = {
            "judge_decision": response.content,
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": response.content,
            "count": investment_debate_state["count"],
        }

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": response.content,
        }

    return research_manager_node
