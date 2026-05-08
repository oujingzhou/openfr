"""
宏观分析师 (Macro Analyst)
"""

from langchain_core.messages import HumanMessage

from openfr.agents.utils.content import extract_text
from openfr.agents.utils.tool_executor import execute_tool_calls
from openfr.tools import (
    get_macro_cpi,
    get_macro_pmi,
    get_money_supply,
)

MAX_TOOL_ROUNDS = 2


def create_macro_analyst(llm):
    """创建宏观分析师节点"""

    tools = [
        get_macro_cpi,
        get_macro_pmi,
        get_money_supply,
    ]
    tools_dict = {tool.name: tool for tool in tools}
    llm_with_tools = llm.bind_tools(tools)

    def macro_analyst_node(state):
        query = state["query"]
        research_target = state.get("research_target", "")

        system_message = f"""你是宏观分析师。研究标的：{research_target or "待确定"}。问题：{query}

**重要：请在第一次回复时就同时调用所有需要的工具。** 不要分多次调用。

典型操作：同时调用 get_macro_cpi + get_macro_pmi + get_money_supply 获取数据。

收到工具结果后，直接撰写简洁的宏观分析报告（500字内），包含：经济指标解读、经济周期判断、货币政策分析、对标的行业的影响。"""

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
            return {"macro_report": report}
        return {"macro_report": ""}

    return macro_analyst_node
