"""
Command Line Interface for OpenFR.
"""

import os
import time

# 在导入任何其他模块之前禁用 tqdm 进度条
os.environ["TQDM_DISABLE"] = "1"

# 尝试 monkey patch tqdm 以完全禁用
try:
    import tqdm
    # 将 tqdm 替换为无操作版本
    class DummyTqdm:
        def __init__(self, *args, **kwargs):
            self.iterable = kwargs.get('iterable', args[0] if args else None)
        def __iter__(self):
            return iter(self.iterable) if self.iterable else iter([])
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def update(self, *args, **kwargs):
            pass
        def close(self):
            pass

    tqdm.tqdm = DummyTqdm
    tqdm.std.tqdm = DummyTqdm
except ImportError:
    pass

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

from openfr import __version__
from openfr.config import Config, PROVIDER_CONFIG
from openfr.formatter import format_final_answer

# 需要先加载 .env
from dotenv import load_dotenv
load_dotenv()

from openfr.tools import get_tool_descriptions



# 多 Agent 节点中文名映射
_NODE_DISPLAY = {
    "Market Analyst": ("📈", "市场分析师", "cyan"),
    "Fundamentals Analyst": ("📊", "基本面分析师", "yellow"),
    "News Analyst": ("📰", "新闻分析师", "green"),
    "Macro Analyst": ("🏛️", "宏观分析师", "magenta"),
    "Msg Clear Market": (None, None, None),
    "Msg Clear Fundamentals": (None, None, None),
    "Msg Clear News": (None, None, None),
    "Msg Clear Macro": (None, None, None),
    "tools_market": ("🔧", "调用市场数据工具", "dim"),
    "tools_fundamentals": ("🔧", "调用基本面数据工具", "dim"),
    "tools_news": ("🔧", "调用新闻数据工具", "dim"),
    "tools_macro": ("🔧", "调用宏观数据工具", "dim"),
    "Bull Researcher": ("🐂", "多头研究员", "green"),
    "Bear Researcher": ("🐻", "空头研究员", "red"),
    "Research Manager": ("👔", "研究经理", "blue"),
    "Aggressive Analyst": ("🔥", "激进分析师", "red"),
    "Conservative Analyst": ("🛡️", "保守分析师", "blue"),
    "Neutral Analyst": ("⚖️", "中性分析师", "yellow"),
    "Portfolio Manager": ("💼", "投资组合经理", "bold green"),
}

# 各阶段分组
_PHASE_NODES = {
    "phase1": ["Market Analyst", "Fundamentals Analyst", "News Analyst", "Macro Analyst"],
    "phase2": ["Bull Researcher", "Bear Researcher", "Research Manager"],
    "phase3": ["Aggressive Analyst", "Conservative Analyst", "Neutral Analyst", "Portfolio Manager"],
}


def process_multi_agent_events(
    graph,
    question: str,
    target: str,
    verbose: bool = True,
) -> str:
    """处理多 Agent 事件流并格式化输出"""
    import time

    current_phase = None
    node_count = 0
    start_time = time.time()

    # 阶段标题
    phase_titles = {
        "phase1": "[bold cyan]阶段一：数据收集与分析[/bold cyan]",
        "phase2": "[bold green]阶段二：投资辩论（多空对决）[/bold green]",
        "phase3": "[bold magenta]阶段三：风险评估（三方辩论）[/bold magenta]",
    }

    with console.status("[bold green]🚀 多Agent协作分析中...") as status:
        for event in graph.run(question, target):
            if event["type"] == "error":
                console.print(f"\n[bold red]✗ 错误: {event['message']}[/bold red]")
                return ""

            if event["type"] != "node":
                continue

            node_name = event["node"]
            output = event.get("output", {})
            node_elapsed = event.get("elapsed", 0.0)
            display = _NODE_DISPLAY.get(node_name)

            # 跳过消息清理节点
            if display and display[0] is None:
                continue

            node_count += 1

            # 检测阶段切换
            for phase_key, phase_nodes in _PHASE_NODES.items():
                if node_name in phase_nodes and current_phase != phase_key:
                    current_phase = phase_key
                    console.print(f"\n{'─' * 50}")
                    console.print(f"  {phase_titles[phase_key]}")
                    console.print(f"{'─' * 50}")
                    break

            if display:
                icon, cn_name, style = display
            else:
                icon, cn_name, style = "▶", node_name, "white"

            # 更新状态
            status.update(f"[bold {style}]{icon} {cn_name} 执行中...[/]")

            elapsed_str = f"[dim] {node_elapsed:.1f}s[/dim]"

            # 工具节点只在 verbose 模式下显示
            if node_name.startswith("tools_"):
                if verbose:
                    console.print(f"  [dim]  {icon} {cn_name}{elapsed_str}[/dim]")
                continue

            # 分析师完成报告
            report_fields = {
                "market_report": ("市场分析报告", "cyan"),
                "fundamentals_report": ("基本面分析报告", "yellow"),
                "news_report": ("新闻分析报告", "green"),
                "macro_report": ("宏观分析报告", "magenta"),
            }

            reported = False
            for field, (report_name, color) in report_fields.items():
                if field in output and output[field]:
                    report = output[field]
                    if isinstance(report, list):
                        report = "\n".join(
                            block.get("text", "") for block in report
                            if isinstance(block, dict) and block.get("type") == "text"
                        )
                    if not isinstance(report, str):
                        report = str(report)
                    console.print(
                        f"\n  {icon} [bold {style}]{cn_name}[/bold {style}]"
                        f" [dim]·[/dim] [green]✓ {report_name}已生成[/green]"
                        f" [dim]({len(report)} 字符)[/dim]{elapsed_str}"
                    )
                    if verbose and report:
                        from rich.markdown import Markdown
                        console.print(Markdown(report))
                    reported = True
                    break

            if reported:
                continue

            # 辩论节点
            if node_name in ("Bull Researcher", "Bear Researcher"):
                debate_state = output.get("investment_debate_state", {})
                current_resp = debate_state.get("current_response", "")
                count = debate_state.get("count", 0)
                console.print(
                    f"\n  {icon} [bold {style}]{cn_name}[/bold {style}]"
                    f" [dim]·[/dim] 第 {(count + 1) // 2} 轮辩论{elapsed_str}"
                )
                if verbose and current_resp:
                    from rich.markdown import Markdown
                    console.print(Markdown(current_resp))

            elif node_name == "Research Manager":
                plan = output.get("investment_plan", "")
                if plan:
                    console.print(
                        f"\n  {icon} [bold {style}]{cn_name}[/bold {style}]"
                        f" [dim]·[/dim] [green]✓ 投资建议已生成[/green]{elapsed_str}"
                    )
                    if verbose:
                        from rich.markdown import Markdown
                        console.print(Markdown(plan))

            elif node_name in ("Aggressive Analyst", "Conservative Analyst", "Neutral Analyst"):
                risk_state = output.get("risk_debate_state", {})
                count = risk_state.get("count", 0)
                # 找到当前说话者对应的历史字段
                speaker_field = {
                    "Aggressive Analyst": "current_aggressive_response",
                    "Conservative Analyst": "current_conservative_response",
                    "Neutral Analyst": "current_neutral_response",
                }.get(node_name, "")
                current_resp = risk_state.get(speaker_field, "")
                console.print(
                    f"\n  {icon} [bold {style}]{cn_name}[/bold {style}]"
                    f" [dim]·[/dim] 第 {(count + 2) // 3} 轮风险评估{elapsed_str}"
                )
                if verbose and current_resp:
                    from rich.markdown import Markdown
                    console.print(Markdown(current_resp))

            elif node_name == "Portfolio Manager":
                decision = output.get("final_decision", "")
                if not decision:
                    console.print(f"[dim]DEBUG: Portfolio Manager output keys: {list(output.keys())}[/dim]")
                    console.print(f"[dim]DEBUG: final_decision value: {repr(decision)}[/dim]")
                if decision:
                    total_elapsed = time.time() - start_time
                    console.print(
                        f"\n  {icon} [bold {style}]{cn_name}[/bold {style}]"
                        f" [dim]·[/dim] [green]✓ 最终决策已生成[/green]{elapsed_str}"
                    )
                    console.print()
                    console.print(f"[dim]⏱ 共执行 {node_count} 个节点，用时 {total_elapsed:.1f} 秒[/dim]")
                    console.print()
                    final_panel = format_final_answer(decision)
                    console.print(final_panel)
                    return decision

            else:
                console.print(f"\n  {icon} [bold {style}]{cn_name}[/bold {style}]{elapsed_str}")

    total_elapsed = time.time() - start_time
    console.print(f"\n[dim]⏱ 共执行 {node_count} 个节点，用时 {total_elapsed:.1f} 秒[/dim]")
    return ""


app = typer.Typer(
    name="openfr",
    help="OpenFR - 基于 AKShare 的金融研究 Agent",
    add_completion=False,
)
console = Console()


# 所有支持的提供商列表
PROVIDER_CHOICES = list(PROVIDER_CONFIG.keys())


def get_default_provider() -> str:
    """从环境变量获取默认提供商"""
    return os.getenv("OPENFR_PROVIDER", "zhipu")


def get_default_model() -> str:
    """从环境变量获取默认模型"""
    return os.getenv("OPENFR_MODEL", "")


def get_tool_display_name(tool_name: str) -> str:
    """获取工具的中文显示名称"""
    tool_names = {
        "get_stock_realtime": "获取股票实时行情",
        "get_stock_history": "获取股票历史数据",
        "get_stock_info": "获取股票基本信息",
        "get_stock_financials": "获取核心财务指标",
        "search_stock": "搜索股票（A股）",
        "search_stock_any": "智能搜索股票（A股/港股）",
        "get_stock_news": "获取股票新闻",
        "get_hot_stocks": "获取热门股票",
        "get_industry_boards": "获取行业板块",
        "get_industry_board_detail": "获取行业板块详情（涨跌幅+估值）",
        "get_stock_bid_ask": "获取五档买卖盘与涨跌停",
        "get_stock_fund_flow": "获取个股资金流向",
        "get_stock_lhb_detail": "获取龙虎榜明细（按日期）",
        "get_stock_lhb_dates": "获取某股龙虎榜上榜日期",
        "get_stock_lhb_rank": "获取龙虎榜上榜统计排行",
        "get_stock_yjyg": "获取业绩预告",
        "get_stock_yjbb": "获取业绩快报",
        "get_stock_profit_forecast": "获取机构盈利预测",
        "get_stock_hk_realtime": "获取港股实时行情",
        "get_stock_hk_history": "获取港股历史数据",
        "search_stock_hk": "搜索港股",
        "get_fund_list": "获取基金列表",
        "get_etf_realtime": "获取ETF实时行情",
        "get_etf_history": "获取ETF历史数据",
        "get_fund_rank": "获取基金排行",
        "get_futures_realtime": "获取期货实时行情",
        "get_futures_history": "获取期货历史数据",
        "get_futures_inventory": "获取期货库存",
        "get_index_realtime": "获取指数实时行情",
        "get_index_history": "获取指数历史数据",
        "get_macro_cpi": "获取CPI数据",
        "get_macro_ppi": "获取PPI数据",
        "get_macro_pmi": "获取PMI数据",
        "get_macro_gdp": "获取GDP数据",
        "get_money_supply": "获取货币供应量",
    }
    return tool_names.get(tool_name, tool_name)


@app.command()
def query(
    question: str = typer.Argument(..., help="要研究的问题"),
    model: str = typer.Option(None, "--model", "-m", help="使用的模型 (留空使用环境变量或默认)"),
    provider: str = typer.Option(None, "--provider", "-p", help="模型提供商 (留空使用环境变量或默认)"),
    verbose: bool = typer.Option(True, "--verbose/--quiet", "-v/-q", help="是否显示详细过程"),
    target: str = typer.Option("", "--target", "-t", help="研究标的（股票代码/名称）"),
):
    """
    向金融研究 Agent 提问（多Agent协作模式）。

    示例:
        openfr query "贵州茅台今天股价多少?"
        openfr query "分析今天的热门板块" -p deepseek
        openfr query "贵州茅台值得买吗？" --target 贵州茅台
        openfr query "分析比亚迪的投资价值" --target 比亚迪 -p zhipu
    """
    # 使用环境变量默认值
    if provider is None:
        provider = get_default_provider()
    if model is None:
        model = get_default_model()

    # 验证提供商
    if provider not in PROVIDER_CONFIG:
        console.print(f"[red]错误: 不支持的提供商 '{provider}'[/]")
        console.print(f"支持的提供商: {', '.join(PROVIDER_CHOICES)}")
        raise typer.Exit(1)

    config = Config(
        provider=provider,  # type: ignore
        model=model,
        verbose=verbose,
    )

    # 美化的问题显示
    query_text = Text()
    query_text.append("❓ ", style="bold blue")
    query_text.append(question, style="bold white")
    query_text.append("\n\n")
    query_text.append("🤖 模型: ", style="dim")
    query_text.append(f"{provider} / {config.get_model_name()}", style="cyan")
    query_text.append("\n")
    query_text.append("📊 模式: ", style="dim")
    query_text.append("多Agent协作", style="cyan")
    if target:
        query_text.append("\n")
        query_text.append("🎯 标的: ", style="dim")
        query_text.append(target, style="cyan")

    console.print(Panel(
        query_text,
        title="[bold blue]OpenFR 查询[/bold blue]",
        border_style="blue",
        box=box.ROUNDED,
        padding=(1, 2)
    ))

    # 检查 API Key
    api_key = config.get_api_key()
    if not api_key and provider != "ollama":
        env_key = PROVIDER_CONFIG[provider]["env_key"]
        console.print(f"[yellow]警告: 未设置 {env_key} 环境变量[/]")

    # 多 Agent 模式
    from openfr.graph import ResearchGraph
    graph = ResearchGraph(config)
    process_multi_agent_events(graph, question, target, verbose=verbose)


@app.command()
def chat(
    model: str = typer.Option(None, "--model", "-m", help="使用的模型 (留空使用环境变量或默认)"),
    provider: str = typer.Option(None, "--provider", "-p", help="模型提供商 (留空使用环境变量或默认)"),
):
    """
    进入交互式对话模式（多Agent协作）。

    示例:
        openfr chat
        openfr chat -p dashscope
        openfr chat -p zhipu -m glm-4-plus
    """
    # 使用环境变量默认值
    if provider is None:
        provider = get_default_provider()
    if model is None:
        model = get_default_model()

    if provider not in PROVIDER_CONFIG:
        console.print(f"[red]错误: 不支持的提供商 '{provider}'[/]")
        raise typer.Exit(1)

    config = Config(
        provider=provider,  # type: ignore
        model=model,
        verbose=True,
    )

    # 美化的欢迎界面
    welcome_text = Text()
    welcome_text.append("欢迎使用 ", style="bold")
    welcome_text.append("OpenFR", style="bold cyan")
    welcome_text.append(" 金融研究助手！", style="bold")
    welcome_text.append("\n\n")
    welcome_text.append("💹 当前配置: ", style="cyan")
    welcome_text.append(f"{provider} / {config.get_model_name()}", style="yellow")
    welcome_text.append("\n")
    welcome_text.append("📊 模式: ", style="cyan")
    welcome_text.append("多Agent协作", style="yellow")
    welcome_text.append("\n\n")
    welcome_text.append("📝 输入您的问题开始分析（可用 --target 指定标的）", style="dim")
    welcome_text.append("\n")
    welcome_text.append("🚪 输入 ", style="dim")
    welcome_text.append("exit", style="bold dim")
    welcome_text.append(" 或 ", style="dim")
    welcome_text.append("quit", style="bold dim")
    welcome_text.append(" 退出", style="dim")

    console.print(Panel(
        welcome_text,
        title="[bold blue]💡 OpenFR Chat[/bold blue]",
        border_style="blue",
        box=box.DOUBLE,
        padding=(1, 2)
    ))

    from openfr.graph import ResearchGraph

    # 创建带历史记录的输入会话
    session = PromptSession(history=InMemoryHistory())

    while True:
        try:
            console.print()
            try:
                question = session.prompt("你: ")
            except (EOFError, KeyboardInterrupt):
                break

            if question.lower() in ("exit", "quit", "q"):
                console.print("[dim]👋 再见！[/]")
                break

            if not question.strip():
                continue

            # 从问题中提取标的（简单策略：如果问题包含"分析"等关键词后面跟名称）
            target = ""

            console.print()
            start_time = time.time()
            graph = ResearchGraph(config)
            process_multi_agent_events(graph, question, target, verbose=True)
            elapsed = time.time() - start_time
            console.print(f"[dim]⏱ 本轮用时 {elapsed:.1f} 秒[/]")

        except KeyboardInterrupt:
            console.print("\n[dim]已取消当前操作[/]")
            continue


@app.command()
def tools():
    """
    列出所有可用的金融数据工具。
    """
    console.print(Panel(get_tool_descriptions(), title="🔧 可用工具"))


@app.command()
def providers():
    """
    列出所有支持的模型提供商。
    """
    table = Table(title="支持的模型提供商")
    table.add_column("提供商", style="cyan")
    table.add_column("环境变量", style="green")
    table.add_column("默认模型", style="yellow")
    table.add_column("说明")
    table.add_column("状态", style="bold")

    providers_list = Config.list_providers()
    provider_by_name = {p["name"]: p for p in providers_list}

    # 国产模型
    table.add_row("[bold]--- 国产模型 ---", "", "", "", "")
    for name in ["deepseek", "doubao", "dashscope", "zhipu", "modelscope", "kimi", "stepfun", "minimax"]:
        cfg = PROVIDER_CONFIG[name]
        provider_info = provider_by_name.get(name)
        status = "[green]✓ 已配置[/]" if provider_info and provider_info["configured"] else "[dim]未配置[/]"
        table.add_row(name, cfg["env_key"], cfg["default_model"], cfg["description"], status)

    # 海外模型
    table.add_row("[bold]--- 海外模型 ---", "", "", "", "")
    for name in ["openai", "anthropic", "openrouter", "together", "groq"]:
        cfg = PROVIDER_CONFIG[name]
        provider_info = provider_by_name.get(name)
        status = "[green]✓ 已配置[/]" if provider_info and provider_info["configured"] else "[dim]未配置[/]"
        table.add_row(name, cfg["env_key"], cfg["default_model"], cfg["description"], status)

    # 本地部署
    table.add_row("[bold]--- 本地部署 ---", "", "", "", "")
    cfg = PROVIDER_CONFIG["ollama"]
    table.add_row("ollama", cfg["env_key"], cfg["default_model"], cfg["description"], "[dim]本地[/]")

    # 自定义
    table.add_row("[bold]--- 自定义 ---", "", "", "", "")
    cfg = PROVIDER_CONFIG["custom"]
    table.add_row("custom", "CUSTOM_API_KEY + CUSTOM_BASE_URL", "(需指定)", cfg["description"], "[dim]自定义[/]")

    console.print(table)

    # 显示当前默认配置
    current_provider = get_default_provider()
    current_model = get_default_model() or PROVIDER_CONFIG.get(current_provider, {}).get("default_model", "")
    console.print(f"\n[bold]当前默认:[/] {current_provider} / {current_model}")
    console.print("[dim]提示: 在 .env 文件中设置 OPENFR_PROVIDER 和 OPENFR_MODEL 可修改默认值[/]")


@app.command()
def version():
    """
    显示版本信息。
    """
    console.print(f"OpenFR v{__version__}")


if __name__ == "__main__":
    app()
