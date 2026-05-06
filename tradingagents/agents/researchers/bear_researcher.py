

def create_bear_researcher(llm, memory):
    def bear_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bear_history = investment_debate_state.get("bear_history", "")

        current_response = investment_debate_state.get("current_response", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""You are a Bear Analyst arguing against a **short-term long trade** on this Indian market (NSE/BSE) stock. Present a well-reasoned case highlighting risks and negative signals for the next 1-day to 2-week period.

Key points to focus on:

- **Short-term Risk Signals**: Bearish technical patterns — breakdown below key MAs, RSI divergence, declining volume on rallies, distribution patterns
- **Immediate Threats**: Upcoming negative catalysts — weak results expected, sector under pressure, regulatory headwinds from SEBI/RBI
- **Indian Market Headwinds**: FII selling, NIFTY weakness, INR depreciation, crude oil spike, global risk-off sentiment
- **Overvaluation for Short-term**: High PE relative to sector, recent sharp rally without consolidation, gap-up exhaustion
- **Bull Counterpoints**: Expose weaknesses in the bull case — over-optimistic assumptions, ignoring sector rotation away from this stock
- **Engagement**: Debate style. Directly counter the bull analyst's points with specific data.

Resources available:

Market research report: {market_research_report}
Social media sentiment report: {sentiment_report}
Latest news (Indian & global): {news_report}
Company fundamentals report: {fundamentals_report}
Conversation history: {history}
Last bull argument: {current_response}
Past reflections and lessons: {past_memory_str}

Deliver a compelling short-term bear case. Focus on immediate risks and why this is not the right time to enter. Address past mistakes.
"""

        response = llm.invoke(prompt)

        argument = f"Bear Analyst: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bear_history": bear_history + "\n" + argument,
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bear_node
