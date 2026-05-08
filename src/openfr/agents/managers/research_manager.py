"""
研究经理 (Research Manager)

职责：综合多空辩论，给出初步投资建议
"""

from openfr.agents.schemas import ResearchPlan, render_research_plan
from openfr.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)


def create_research_manager(llm):
    """创建研究经理节点"""
    structured_llm = bind_structured(llm, ResearchPlan, "Research Manager")

    def research_manager_node(state) -> dict:
        research_target = state.get("research_target", "")
        history = state["investment_debate_state"].get("history", "")
        investment_debate_state = state["investment_debate_state"]

        prompt = f"""研究标的：{research_target}。综合以下多空辩论，给出投资建议。500字内。

辩论历史：
{history}

输出格式：
1. rating: Buy/Overweight/Hold/Underweight/Sell
2. reasoning: 推理过程
3. key_points: 3条关键要点
4. risks: 2条主要风险"""

        investment_plan = invoke_structured_or_freetext(
            structured_llm,
            llm,
            prompt,
            render_research_plan,
            "Research Manager",
        )

        new_investment_debate_state = {
            "judge_decision": investment_plan,
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": investment_plan,
            "count": investment_debate_state["count"],
        }

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": investment_plan,
        }

    return research_manager_node
