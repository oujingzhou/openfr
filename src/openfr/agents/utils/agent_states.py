"""
Agent state definitions for the multi-agent research graph.
"""

from typing import Annotated
from typing_extensions import TypedDict


class InvestDebateState(TypedDict):
    """投资辩论状态（多空对决）"""
    bull_history: Annotated[str, "多头观点历史"]
    bear_history: Annotated[str, "空头观点历史"]
    history: Annotated[str, "完整辩论历史"]
    current_response: Annotated[str, "最新回应"]
    judge_decision: Annotated[str, "裁决结果"]
    count: Annotated[int, "辩论轮数"]


class RiskDebateState(TypedDict):
    """风险辩论状态（三方辩论）"""
    aggressive_history: Annotated[str, "激进观点历史"]
    conservative_history: Annotated[str, "保守观点历史"]
    neutral_history: Annotated[str, "中性观点历史"]
    history: Annotated[str, "完整辩论历史"]
    latest_speaker: Annotated[str, "最后发言者"]
    current_aggressive_response: Annotated[str, "激进最新回应"]
    current_conservative_response: Annotated[str, "保守最新回应"]
    current_neutral_response: Annotated[str, "中性最新回应"]
    judge_decision: Annotated[str, "裁决结果"]
    count: Annotated[int, "辩论轮数"]


class AgentState(TypedDict):
    """
    主 Agent 状态，包含整个研究流程的所有数据。
    """
    # 用户输入
    query: Annotated[str, "用户问题"]
    research_target: Annotated[str, "研究标的（股票代码/名称）"]

    # 四份分析报告
    market_report: Annotated[str, "市场分析报告"]
    fundamentals_report: Annotated[str, "基本面分析报告"]
    news_report: Annotated[str, "新闻分析报告"]
    macro_report: Annotated[str, "宏观分析报告"]

    # 投资辩论
    investment_debate_state: Annotated[InvestDebateState, "投资辩论状态"]
    investment_plan: Annotated[str, "研究经理的投资建议"]

    # 风险辩论
    risk_debate_state: Annotated[RiskDebateState, "风险辩论状态"]
    final_decision: Annotated[str, "最终研究结论"]
