"""
空头研究员 (Bear Researcher)
"""

from openfr.agents.utils.content import extract_text


def create_bear_researcher(llm):
    """创建空头研究员节点"""

    def bear_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bear_history = investment_debate_state.get("bear_history", "")
        current_response = investment_debate_state.get("current_response", "")

        prompt = f"""你是空头研究员。基于以下报告，用300字内提出看空论据。直接输出观点，不要废话。

市场报告：{state["market_report"]}
基本面报告：{state["fundamentals_report"]}
新闻报告：{state["news_report"]}
宏观报告：{state["macro_report"]}

多头最新论点：{current_response}
辩论历史：{history}

要求：聚焦风险因素、估值担忧、负面数据。如有多头论点则直接反驳。300字内。"""

        response = llm.invoke(prompt)
        text = extract_text(response.content)
        argument = f"空头研究员：{text}"

        new_investment_debate_state = {
            "history": history + "\n\n" + argument,
            "bull_history": investment_debate_state.get("bull_history", ""),
            "bear_history": bear_history + "\n\n" + argument,
            "current_response": argument,
            "judge_decision": investment_debate_state.get("judge_decision", ""),
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bear_node
