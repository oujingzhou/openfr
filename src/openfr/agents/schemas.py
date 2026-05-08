"""
Pydantic schemas for structured output from agents.
"""

from pydantic import BaseModel, Field


class ResearchPlan(BaseModel):
    """研究经理的投资建议（结构化输出）"""
    rating: str = Field(
        description="评级：Buy（买入）/Overweight（增持）/Hold（持有）/Underweight（减持）/Sell（卖出）"
    )
    reasoning: str = Field(description="推理过程，说明为何给出该评级")
    key_points: list[str] = Field(description="关键要点列表，3-5 条")
    risks: list[str] = Field(description="主要风险列表，2-4 条")


class FinalDecision(BaseModel):
    """投资组合经理的最终结论（结构化输出）"""
    rating: str = Field(
        description="最终评级：Buy/Overweight/Hold/Underweight/Sell"
    )
    confidence: str = Field(
        description="信心水平：High（高）/Medium（中）/Low（低）"
    )
    summary: str = Field(description="结论摘要，1-2 段")
    reasoning: str = Field(description="详细推理，综合各方观点")
    action_items: list[str] = Field(description="行动建议列表，2-4 条")


def render_research_plan(plan: ResearchPlan) -> str:
    """将 ResearchPlan 渲染为 Markdown 格式"""
    lines = [
        f"## 研究经理投资建议\n",
        f"**评级**: {plan.rating}\n",
        f"### 推理过程\n{plan.reasoning}\n",
        f"### 关键要点",
    ]
    for i, point in enumerate(plan.key_points, 1):
        lines.append(f"{i}. {point}")
    lines.append("\n### 主要风险")
    for i, risk in enumerate(plan.risks, 1):
        lines.append(f"{i}. {risk}")
    return "\n".join(lines)


def render_final_decision(decision: FinalDecision) -> str:
    """将 FinalDecision 渲染为 Markdown 格式"""
    lines = [
        f"## 最终研究结论\n",
        f"**评级**: {decision.rating}",
        f"**信心水平**: {decision.confidence}\n",
        f"### 摘要\n{decision.summary}\n",
        f"### 详细推理\n{decision.reasoning}\n",
        f"### 行动建议",
    ]
    for i, item in enumerate(decision.action_items, 1):
        lines.append(f"{i}. {item}")
    return "\n".join(lines)
