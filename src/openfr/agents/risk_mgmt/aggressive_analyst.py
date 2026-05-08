"""
激进分析师 (Aggressive Analyst)

职责：强调高收益机会，支持激进策略
"""

from openfr.agents.utils.content import extract_text


def create_aggressive_analyst(llm):
    """创建激进分析师节点"""

    def aggressive_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        aggressive_history = risk_debate_state.get("aggressive_history", "")

        current_conservative_response = risk_debate_state.get("current_conservative_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")
        investment_plan = state["investment_plan"]

        prompt = f"""你是激进风险分析师。300字内，强调上行潜力和高回报机会，反驳保守派的担忧。

投资建议：{investment_plan}
辩论历史：{history}
保守派论点：{current_conservative_response}
中性派论点：{current_neutral_response}

直接输出观点，300字内。"""

        response = llm.invoke(prompt)
        text = extract_text(response.content)
        argument = f"激进分析师：{text}"

        new_risk_debate_state = {
            "history": history + "\n\n" + argument,
            "aggressive_history": aggressive_history + "\n\n" + argument,
            "conservative_history": risk_debate_state.get("conservative_history", ""),
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Aggressive",
            "current_aggressive_response": argument,
            "current_conservative_response": risk_debate_state.get("current_conservative_response", ""),
            "current_neutral_response": risk_debate_state.get("current_neutral_response", ""),
            "judge_decision": risk_debate_state.get("judge_decision", ""),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return aggressive_node
