"""
多头研究员 (Bull Researcher)
"""

from openfr.agents.utils.content import extract_text


def create_bull_researcher(llm):
    """创建多头研究员节点"""

    def bull_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bull_history = investment_debate_state.get("bull_history", "")
        current_response = investment_debate_state.get("current_response", "")

        prompt = f"""你是多头研究员。基于以下报告，用300字内提出看多论据。直接输出观点，不要废话。

市场报告：{state["market_report"]}
基本面报告：{state["fundamentals_report"]}
新闻报告：{state["news_report"]}
宏观报告：{state["macro_report"]}

空头最新论点：{current_response}
辩论历史：{history}

要求：聚焦成长潜力、竞争优势、正面数据。如有空头论点则直接反驳。300字内。"""

        response = llm.invoke(prompt)
        text = extract_text(response.content)
        argument = f"多头研究员：{text}"

        new_investment_debate_state = {
            "history": history + "\n\n" + argument,
            "bull_history": bull_history + "\n\n" + argument,
            "bear_history": investment_debate_state.get("bear_history", ""),
            "current_response": argument,
            "judge_decision": investment_debate_state.get("judge_decision", ""),
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bull_node
