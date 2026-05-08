"""
投资组合经理 (Portfolio Manager)

职责：综合三方风险辩论，给出最终研究结论
"""

from openfr.agents.schemas import FinalDecision, render_final_decision
from openfr.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)


def create_portfolio_manager(llm):
    """创建投资组合经理节点"""
    structured_llm = bind_structured(llm, FinalDecision, "Portfolio Manager")

    def portfolio_manager_node(state) -> dict:
        research_target = state.get("research_target", "")
        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        investment_plan = state["investment_plan"]

        prompt = f"""研究标的：{research_target}。综合以下风险辩论，给出最终投资决策。600字内。

研究经理建议：
{investment_plan}

风险辩论历史：
{history}

输出格式：
1. rating: Buy/Overweight/Hold/Underweight/Sell
2. confidence: High/Medium/Low
3. summary: 结论摘要（2-3句）
4. reasoning: 详细推理（综合各方观点）
5. action_items: 2-4条行动建议"""

        final_decision = invoke_structured_or_freetext(
            structured_llm,
            llm,
            prompt,
            render_final_decision,
            "Portfolio Manager",
        )

        new_risk_debate_state = {
            "judge_decision": final_decision,
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
            "final_decision": final_decision,
        }

    return portfolio_manager_node
