"""工具执行辅助函数"""
import logging
import time

from langchain_core.messages import ToolMessage

logger = logging.getLogger(__name__)

# 全局工具耗时记录，供外部读取
tool_timings: list[dict] = []


def execute_tool_calls(tool_calls, tools_dict):
    """
    执行工具调用列表

    Args:
        tool_calls: LLM 返回的 tool_calls 列表
        tools_dict: {tool_name: tool_function} 字典

    Returns:
        ToolMessage 列表
    """
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]

        if tool_name in tools_dict:
            try:
                t0 = time.perf_counter()
                output = tools_dict[tool_name].invoke(tool_args)
                elapsed = time.perf_counter() - t0
                logger.debug("[tool] %s %.3fs", tool_name, elapsed)
                tool_timings.append({"tool": tool_name, "elapsed": elapsed})
                results.append(ToolMessage(
                    content=str(output),
                    tool_call_id=tool_id,
                ))
            except Exception as e:
                results.append(ToolMessage(
                    content=f"Error: {e}",
                    tool_call_id=tool_id,
                ))
        else:
            results.append(ToolMessage(
                content=f"Tool {tool_name} not found",
                tool_call_id=tool_id,
            ))
    return results
