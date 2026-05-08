"""
Main research graph orchestrator.
"""

import logging
import time
from typing import Any, Dict, Iterator

from openfr.config import Config
from openfr.graph.propagation import Propagator
from openfr.graph.conditional_logic import ConditionalLogic
from openfr.graph.setup import GraphSetup

logger = logging.getLogger(__name__)


class ResearchGraph:
    """
    主研究图类，协调多 Agent 金融研究流程。

    架构：
    1. 四分析师并行收集数据（市场、基本面、新闻、宏观）
    2. 多空辩论（Bull vs Bear）
    3. 研究经理综合辩论，给出初步建议
    4. 风险三方辩论（Aggressive vs Conservative vs Neutral）
    5. 投资组合经理给出最终决策
    """

    def __init__(self, config: Config | None = None):
        """
        初始化研究图

        Args:
            config: 配置对象，如果为 None 则从环境变量加载
        """
        self.config = config or Config.from_env()
        self.llm = self._create_llm()

        # 初始化组件
        self.conditional_logic = ConditionalLogic(
            max_debate_rounds=self.config.max_debate_rounds,
            max_risk_discuss_rounds=self.config.max_risk_discuss_rounds,
        )
        self.graph_setup = GraphSetup(
            self.llm,
            self.conditional_logic,
        )
        self.propagator = Propagator(max_recur_limit=self.config.max_recur_limit)

        # 构建图
        workflow = self.graph_setup.setup_graph()
        self.graph = workflow.compile()

    def _create_llm(self):
        """创建 LLM 实例"""
        provider = self.config.provider
        model = self.config.get_model_name()
        api_key = self.config.get_api_key()
        base_url = self.config.get_base_url()

        if provider == "anthropic" or (provider == "custom" and self.config.custom_api_style == "anthropic"):
            from langchain_anthropic import ChatAnthropic

            kwargs = {
                "model": model,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "api_key": api_key,
            }
            if provider == "custom" and base_url:
                kwargs["base_url"] = base_url

            # 添加 thinking 配置（仅 Anthropic 支持）
            if self.config.enable_thinking:
                kwargs["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": self.config.thinking_budget,
                }

            return ChatAnthropic(**kwargs)

        if provider == "ollama":
            from langchain_ollama import ChatOllama

            return ChatOllama(
                model=model,
                temperature=self.config.temperature,
                base_url=base_url,
            )

        from langchain_openai import ChatOpenAI

        kwargs = {
            "model": model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "api_key": api_key,
        }
        if base_url:
            kwargs["base_url"] = base_url
        return ChatOpenAI(**kwargs)

    def run(self, query: str, research_target: str = "") -> Iterator[Dict[str, Any]]:
        """
        运行研究图

        Args:
            query: 用户问题
            research_target: 研究标的（股票代码/名称）

        Yields:
            事件字典，包含类型和数据
        """
        # 创建初始状态
        initial_state = self.propagator.create_initial_state(query, research_target)

        # 运行图
        try:
            prev_ts = time.perf_counter()
            for event in self.graph.stream(
                initial_state,
                config={"recursion_limit": self.config.max_recur_limit},
            ):
                # event 是一个字典，key 是节点名，value 是节点输出
                now = time.perf_counter()
                for node_name, node_output in event.items():
                    elapsed = now - prev_ts
                    yield {
                        "type": "node",
                        "node": node_name,
                        "output": node_output,
                        "elapsed": elapsed,
                    }
                prev_ts = time.perf_counter()
        except Exception as e:
            logger.error(f"Graph execution failed: {e}")
            yield {
                "type": "error",
                "message": str(e),
            }

    def query(self, query: str, research_target: str = "", verbose: bool = True) -> str:
        """
        简化接口：运行研究图并返回最终结论

        Args:
            query: 用户问题
            research_target: 研究标的
            verbose: 是否打印进度

        Returns:
            最终研究结论
        """
        final_decision = ""

        for event in self.run(query, research_target):
            if event["type"] == "node":
                node_name = event["node"]
                if verbose:
                    print(f"\n[{node_name}] 执行中...")

                # 提取最终决策
                if node_name == "Portfolio Manager":
                    output = event["output"]
                    if "final_decision" in output:
                        final_decision = output["final_decision"]

            elif event["type"] == "error":
                if verbose:
                    print(f"\n错误: {event['message']}")
                return f"执行失败: {event['message']}"

        return final_decision or "未能生成最终结论"
