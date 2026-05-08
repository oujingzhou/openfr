"""
市场分析师 (Market Analyst)
"""

from langchain_core.messages import HumanMessage

from openfr.agents.utils.content import extract_text
from openfr.agents.utils.tool_executor import execute_tool_calls
from openfr.tools import (
    get_stock_realtime,
    get_stock_history,
    get_index_realtime,
    get_hot_stocks,
    get_industry_boards,
)

MAX_TOOL_ROUNDS = 2


def create_market_analyst(llm):
    """创建市场分析师节点"""

    tools = [
        get_stock_realtime,
        get_stock_history,
        get_index_realtime,
        get_hot_stocks,
        get_industry_boards,
    ]
    tools_dict = {tool.name: tool for tool in tools}
    llm_with_tools = llm.bind_tools(tools)

    def market_analyst_node(state):
        query = state["query"]
        research_target = state.get("research_target", "")

        system_message = f"""你是市场分析师。研究标的：{research_target or "待确定"}。问题：{query}

**重要：请在第一次回复时就同时调用所有需要的工具。** 不要分多次调用。

典型操作：同时调用 get_stock_realtime + get_index_realtime + get_hot_stocks 获取数据。

收到工具结果后，直接撰写简洁的市场分析报告（500字内），包含：行情数据、指数表现、市场热点。不要编造数据。"""

        messages = [HumanMessage(content=f"{system_message}\n\n请开始分析。")]

        # 内部工具调用循环
        for round_num in range(MAX_TOOL_ROUNDS):
            result = llm_with_tools.invoke(messages)
            messages.append(result)

            if not result.tool_calls:
                break

            # 执行工具
            tool_messages = execute_tool_calls(result.tool_calls, tools_dict)
            messages.extend(tool_messages)

        # 提取报告
        report = extract_text(messages[-1].content)
        if report and len(report) > 100:
            return {"market_report": report}
        return {"market_report": ""}

    return market_analyst_node
