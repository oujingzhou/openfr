"""
保守分析师 (Conservative Analyst)

职责：强调风险控制，支持保守策略
"""

from openfr.agents.utils.content import extract_text


def create_conservative_analyst(llm):
    """创建保守分析师节点"""

    def conservative_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        conservative_history = risk_debate_state.get("conservative_history", "")

        current_aggressive_response = risk_debate_state.get("current_aggressive_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")
        investment_plan = state["investment_plan"]

        prompt = f"""你是保守风险分析师。300字内，强调下行风险和资本保护，反驳激进派的乐观假设。

投资建议：{investment_plan}
辩论历史：{history}
激进派论点：{current_aggressive_response}
中性派论点：{current_neutral_response}

直接输出观点，300字内。"""

        response = llm.invoke(prompt)
        text = extract_text(response.content)
        argument = f"保守分析师：{text}"

        new_risk_debate_state = {
            "history": history + "\n\n" + argument,
            "aggressive_history": risk_debate_state.get("aggressive_history", ""),
            "conservative_history": conservative_history + "\n\n" + argument,
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Conservative",
            "current_aggressive_response": risk_debate_state.get("current_aggressive_response", ""),
            "current_conservative_response": argument,
            "current_neutral_response": risk_debate_state.get("current_neutral_response", ""),
            "judge_decision": risk_debate_state.get("judge_decision", ""),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return conservative_node
