"""
中性分析师 (Neutral Analyst)

职责：平衡风险收益，提出中性观点
"""

from openfr.agents.utils.content import extract_text


def create_neutral_analyst(llm):
    """创建中性分析师节点"""

    def neutral_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        neutral_history = risk_debate_state.get("neutral_history", "")

        current_aggressive_response = risk_debate_state.get("current_aggressive_response", "")
        current_conservative_response = risk_debate_state.get("current_conservative_response", "")
        investment_plan = state["investment_plan"]

        prompt = f"""你是中性风险分析师。300字内，平衡激进派和保守派观点，提出务实的中间路径。

投资建议：{investment_plan}
辩论历史：{history}
激进派论点：{current_aggressive_response}
保守派论点：{current_conservative_response}

直接输出观点，300字内。"""

        response = llm.invoke(prompt)
        text = extract_text(response.content)
        argument = f"中性分析师：{text}"

        new_risk_debate_state = {
            "history": history + "\n\n" + argument,
            "aggressive_history": risk_debate_state.get("aggressive_history", ""),
            "conservative_history": risk_debate_state.get("conservative_history", ""),
            "neutral_history": neutral_history + "\n\n" + argument,
            "latest_speaker": "Neutral",
            "current_aggressive_response": risk_debate_state.get("current_aggressive_response", ""),
            "current_conservative_response": risk_debate_state.get("current_conservative_response", ""),
            "current_neutral_response": argument,
            "judge_decision": risk_debate_state.get("judge_decision", ""),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return neutral_node
