"""
State initialization and propagation utilities.
"""

from typing import Dict, Any

from openfr.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)


class Propagator:
    """处理状态初始化和传播"""

    def __init__(self, max_recur_limit: int = 100):
        """
        初始化 Propagator

        Args:
            max_recur_limit: LangGraph 递归限制
        """
        self.max_recur_limit = max_recur_limit

    def create_initial_state(
        self, query: str, research_target: str = ""
    ) -> Dict[str, Any]:
        """
        创建初始 Agent 状态

        Args:
            query: 用户问题
            research_target: 研究标的（股票代码/名称）

        Returns:
            初始化的 AgentState 字典
        """
        return {
            "messages": [("human", query)],
            "query": query,
            "research_target": research_target,
            "investment_debate_state": InvestDebateState(
                {
                    "bull_history": "",
                    "bear_history": "",
                    "history": "",
                    "current_response": "",
                    "judge_decision": "",
                    "count": 0,
                }
            ),
            "risk_debate_state": RiskDebateState(
                {
                    "aggressive_history": "",
                    "conservative_history": "",
                    "neutral_history": "",
                    "history": "",
                    "latest_speaker": "",
                    "current_aggressive_response": "",
                    "current_conservative_response": "",
                    "current_neutral_response": "",
                    "judge_decision": "",
                    "count": 0,
                }
            ),
            "market_report": "",
            "fundamentals_report": "",
            "news_report": "",
            "macro_report": "",
            "investment_plan": "",
            "final_decision": "",
        }

    def get_graph_args(self) -> Dict[str, Any]:
        """
        获取图调用参数

        Returns:
            包含 recursion_limit 的配置字典
        """
        return {
            "recursion_limit": self.max_recur_limit,
        }
