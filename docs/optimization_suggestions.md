# OpenFR 项目优化建议

本文档汇总当前项目中可改进的**问题修复**与**优化方向**，便于按优先级逐步实施。

---

## 一、需修复的问题（建议优先处理）

### 1. 集成测试调用不存在的方法 `_get_tool_by_name`

**位置**：`tests/test_integration.py` 第 232-233 行。

**现象**：测试中使用 `agent._get_tool_by_name("get_stock_realtime")`，但 `FinancialResearchAgent` 并未定义该方法；实际通过 `self.tools_map.get(name)` 按名称获取工具。

**建议**：
- 将测试改为使用 `agent.tools_map.get("get_stock_realtime") is not None` 和 `agent.tools_map.get("search_stock_any") is not None`；或
- 在 `FinancialResearchAgent` 中增加 `_get_tool_by_name(self, name: str)`，内部返回 `self.tools_map.get(name)`，便于测试与未来扩展。

### 2. 自定义 `TimeoutError` 与内置类型重名

**位置**：`src/openfr/tools/errors.py` 第 37 行。

**现象**：定义了 `class TimeoutError(OpenFRError)`，与内置 `TimeoutError` 重名，易造成混淆或遮蔽（例如在 `from openfr.tools.errors import *` 时）。

**建议**：重命名为 `OpenFRTimeoutError` 或 `ToolTimeoutError`，并在所有使用该类型的地方同步修改（当前代码库中未见直接引用该自定义类，多为使用 `concurrent.futures.TimeoutError`，重命名后只需在 errors 模块内修改即可）。

---

## 二、代码质量与可维护性

### 3. 配置解析重复逻辑

**位置**：`config.py` 的 `Config.from_env()`。

**现象**：大量 `os.getenv(..., "true").lower() == "true"` 的重复写法。

**建议**：抽取辅助函数，例如：

```python
def _env_bool(key: str, default: bool = True) -> bool:
    return os.getenv(key, "true" if default else "false").lower() == "true"
```

然后在 `from_env()` 中统一使用 `_env_bool("OPENFR_VERBOSE", True)` 等，减少重复并降低出错概率。

### 4. 工具显示名称多处维护

**现象**：`cli.py` 中 `get_tool_display_name()` 内维护了一份工具名到中文名的映射，`formatter.py` 中另有 `_TOOL_DISPLAY_NAMES`，两处需同步更新。

**建议**：将「工具名 → 显示名」的映射集中在一处（例如仅在 `formatter.py` 中定义），`cli.py` 通过 `from openfr.formatter import _TOOL_DISPLAY_NAMES` 或封装为 `get_tool_display_name(tool_name)` 再导出使用，避免重复维护。

### 5. Agent 事件类型未定型

**现象**：`agent.run()` 返回 `Iterator[dict]`，事件结构（如 `type`、`content`、`steps` 等）仅通过约定使用，缺少类型约束。

**建议**：使用 `typing.TypedDict` 定义若干事件类型，例如 `ThinkingEvent`、`PlanEvent`、`ToolStartEvent`、`AnswerEvent` 等，并在 `run()` 的返回类型上使用 `Iterator[ThinkingEvent | PlanEvent | ...]` 或 Union，便于静态检查和文档化。

### 6. 工具调用异常处理过宽

**位置**：`agent.py` 中执行工具时 `except Exception as e`。

**现象**：所有异常都被捕获并转为字符串返回给 LLM，可能掩盖编程错误或环境问题。

**建议**：区分「预期异常」（网络超时、数据源不可用、参数错误等）与「非预期异常」：仅对预期异常做捕获并转换为友好信息；其余可记录日志后重新抛出，或至少在开发/verbose 模式下抛出，便于排查。

---

## 三、测试

### 7. 集成测试依赖未安装时的导入

**位置**：`tests/test_integration.py` 第 19 行 `from openfr import FinancialResearchAgent, Config`。

**现象**：若未安装 openfr 包或路径不对，整份测试文件导入即失败，不利于在未安装环境下做语法或导入检查。

**建议**：保持现状也可接受；若希望更稳健，可对「需要 openfr」的测试使用 `pytest.importorskip("openfr")` 或把集成测试与单元测试分离，确保单元测试不依赖包安装。

### 8. 单元测试覆盖率与边界情况

**现象**：`test_tools.py` 等主要覆盖「正常路径」和少量错误路径，工具内部的分支（如多数据源、降级、重试）覆盖有限。

**建议**：对核心工具（如 `get_index_realtime`、`get_stock_realtime`）增加「全部数据源失败」「部分成功」「超时」等用例；对 `Scratchpad` 的 `can_call_tool`、`is_loop_no_progress` 等增加边界测试，便于重构时保持行为稳定。

---

## 四、性能与架构（可选）

### 9. 指数/行情接口的串行与超时

**位置**：`tools/index.py` 等。

**现象**：为避免与 libmini_racer 的线程问题，部分接口已改为串行并带超时，逻辑较复杂。

**建议**：在注释或文档中明确「为何此处不用并行/为何用新浪而非东财」，便于后续维护；若未来 AKShare 或运行环境变化，可再评估是否恢复有限并行或切换数据源。

### 10. 日志与可观测性

**现象**：`base.py` 使用了 `logger`，其他模块较少使用统一日志；生产排查问题时主要依赖控制台输出。

**建议**：在关键路径（如规划开始/结束、每步工具调用开始/结束、最终回答、错误降级）增加结构化日志（如 `logger.info("step_finished", extra={"step": k, "tool": name})`），并考虑通过配置控制日志级别，便于在无 verbose 时也能排查问题。

### 11. CLI `query` 命令的脚本化

**现象**：`openfr query "..."` 通过 `process_agent_events` 仅把结果打印到控制台，若希望在脚本中获取答案字符串（例如用于管道或后续处理）并不方便。

**建议**：让 `process_agent_events` 返回最终答案字符串（已有 return），并在 `query` 命令中根据是否需要脚本化决定是否将答案再打印；或增加一个 `--output/--json` 选项，输出纯文本或 JSON 格式的答案，便于脚本消费。

---

## 五、文档与规范

### 12. README 与代码一致

**建议**：通读 README、README_EN、`.env.example` 与 `config.py`/`cli.py`，确保提供商列表、环境变量名、默认模型一致。

### 13. 类型与 Lint

**建议**：在 CI 中启用 `ruff`（或现有 lint）和类型检查（如 `pyright` 或 `mypy`），对 `src/openfr` 做严格检查；对 `Config(provider=provider)` 等处的 `# type: ignore` 可逐步用更精确的 `ModelProvider` 或字面量类型替代，减少忽略。

---

## 六、优先级建议

| 优先级 | 项 | 说明 |
|--------|----|------|
| P0 | 1. 集成测试 _get_tool_by_name | 会导致集成测试失败 |
| P1 | 2. TimeoutError 重命名 | 避免命名冲突与误解 |
| P1 | 3. 配置解析抽辅助函数 | 提升可维护性 |
| P1 | 4. 工具显示名统一 | 减少重复与遗漏 |
| P2 | 5–6. 类型与异常细化 | 提升可读性与可维护性 |
| P2 | 7–8. 测试加固 | 提高回归与重构安全性 |
| P3 | 9–11. 性能/日志/CLI 脚本化 | 按需求逐步做 |
| P3 | 12–13. 文档与 CI 类型检查 | 长期保持一致性 |

按上述顺序处理可先消除运行与测试中的问题，再逐步提升代码质量与可观测性。
