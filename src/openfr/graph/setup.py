"""
Graph setup and configuration.
"""

from typing import Any

from langgraph.graph import END, START, StateGraph

from openfr.agents.utils.agent_states import AgentState
from openfr.agents.analysts.market_analyst import create_market_analyst
from openfr.agents.analysts.fundamentals_analyst import create_fundamentals_analyst
from openfr.agents.analysts.news_analyst import create_news_analyst
from openfr.agents.analysts.macro_analyst import create_macro_analyst
from openfr.agents.researchers.bull_researcher import create_bull_researcher
from openfr.agents.researchers.bear_researcher import create_bear_researcher
from openfr.agents.managers.research_manager import create_research_manager
from openfr.agents.managers.portfolio_manager import create_portfolio_manager
from openfr.agents.risk_mgmt.aggressive_analyst import create_aggressive_analyst
from openfr.agents.risk_mgmt.conservative_analyst import create_conservative_analyst
from openfr.agents.risk_mgmt.neutral_analyst import create_neutral_analyst

from openfr.graph.conditional_logic import ConditionalLogic


class GraphSetup:
    """处理 Agent 图的设置和配置"""

    def __init__(
        self,
        llm: Any,
        conditional_logic: ConditionalLogic,
    ):
        """
        初始化 GraphSetup

        Args:
            llm: LLM 实例
            conditional_logic: 条件逻辑实例
        """
        self.llm = llm
        self.conditional_logic = conditional_logic

    def setup_graph(self) -> StateGraph:
        """
        设置并编译 Agent 工作流图

        Returns:
            未编译的 StateGraph 工作流
        """
        # 创建分析师节点
        market_analyst_node = create_market_analyst(self.llm)
        fundamentals_analyst_node = create_fundamentals_analyst(self.llm)
        news_analyst_node = create_news_analyst(self.llm)
        macro_analyst_node = create_macro_analyst(self.llm)

        # 创建研究员和经理节点
        bull_researcher_node = create_bull_researcher(self.llm)
        bear_researcher_node = create_bear_researcher(self.llm)
        research_manager_node = create_research_manager(self.llm)

        # 创建风险分析节点
        aggressive_analyst_node = create_aggressive_analyst(self.llm)
        conservative_analyst_node = create_conservative_analyst(self.llm)
        neutral_analyst_node = create_neutral_analyst(self.llm)
        portfolio_manager_node = create_portfolio_manager(self.llm)

        # 创建工作流
        workflow = StateGraph(AgentState)

        # 添加分析师节点
        workflow.add_node("Market Analyst", market_analyst_node)
        workflow.add_node("Fundamentals Analyst", fundamentals_analyst_node)
        workflow.add_node("News Analyst", news_analyst_node)
        workflow.add_node("Macro Analyst", macro_analyst_node)

        # 添加研究员和经理节点
        workflow.add_node("Bull Researcher", bull_researcher_node)
        workflow.add_node("Bear Researcher", bear_researcher_node)
        workflow.add_node("Research Manager", research_manager_node)

        # 添加风险分析节点
        workflow.add_node("Aggressive Analyst", aggressive_analyst_node)
        workflow.add_node("Conservative Analyst", conservative_analyst_node)
        workflow.add_node("Neutral Analyst", neutral_analyst_node)
        workflow.add_node("Portfolio Manager", portfolio_manager_node)

        # 定义边：串行执行四个分析师
        workflow.add_edge(START, "Market Analyst")
        workflow.add_edge("Market Analyst", "Fundamentals Analyst")
        workflow.add_edge("Fundamentals Analyst", "News Analyst")
        workflow.add_edge("News Analyst", "Macro Analyst")
        workflow.add_edge("Macro Analyst", "Bull Researcher")

        # 投资辩论流程
        workflow.add_conditional_edges(
            "Bull Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bear Researcher": "Bear Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_conditional_edges(
            "Bear Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bull Researcher": "Bull Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_edge("Research Manager", "Aggressive Analyst")

        # 风险辩论流程
        workflow.add_conditional_edges(
            "Aggressive Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Conservative Analyst": "Conservative Analyst",
                "Portfolio Manager": "Portfolio Manager",
            },
        )
        workflow.add_conditional_edges(
            "Conservative Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Neutral Analyst": "Neutral Analyst",
                "Portfolio Manager": "Portfolio Manager",
            },
        )
        workflow.add_conditional_edges(
            "Neutral Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Aggressive Analyst": "Aggressive Analyst",
                "Portfolio Manager": "Portfolio Manager",
            },
        )

        workflow.add_edge("Portfolio Manager", END)

        return workflow
