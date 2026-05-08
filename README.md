<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![AKShare](https://img.shields.io/badge/powered%20by-AKShare-orange.svg)](https://github.com/akfamily/akshare)

**OpenFR：轻量级金融研究 Agent | 基于 AKShare | 支持多种 LLM | 多 Agent 协作深度分析**

[English](README_EN.md) | [快速开始](#快速开始) • [功能特性](#功能特性) • [使用指南](#使用指南) • [配置说明](#配置说明) • [架构设计](#架构设计)

</div>

---

## 📊 项目简介

OpenFR (Open Financial Research) 是一个**极简、轻量**的智能金融研究 Agent，基于大语言模型并集成 AKShare 数据接口，通过**多 Agent 协作**完成股票、基金、期货、指数、宏观经济等全方位投资研究。

<a id="功能特性"></a>
### ✨ 核心特性

- 🌱 **极简 & 轻量** — 纯 Python 包 + Typer CLI，仅依赖 AKShare 数据，一条命令即可开始研究
- 🧠 **多 Agent 协作** — 四分析师 + 多空辩论 + 风险三方评估，基于 LangGraph StateGraph 编排
- ⏱️ **节点级耗时打点** — 每个 Agent 节点执行后实时显示耗时，便于定位性能瓶颈
- 📋 **完整中间报告** — 市场/基本面/新闻/宏观报告、辩论过程、风险评估均完整展示
- 📈 **丰富的数据源** — 35+ 金融数据工具，覆盖 A 股、港股、基金、期货、指数、宏观及行业板块
- 🔄 **多 LLM 支持** — 支持 15+ 主流 LLM 提供商（国产 + 海外 + 本地），兼容 OpenAI / Anthropic 格式
- 🎨 **美观的 CLI** — Rich 终端界面，实时展示各阶段进度与完整分析内容
- 🔌 **智能备用切换** — 东方财富 + 新浪 + 同花顺多数据源自动切换与重试
- 💾 **缓存友好** — 股票列表缓存 6 小时，部分行情接口缓存 1 分钟，减少重复请求
- 🛡️ **错误恢复** — 失败重试、降级替代及"基于已有信息收尾"保护逻辑

---

<a id="架构设计"></a>
## 🏗️ 架构设计

OpenFR 采用 **LangGraph StateGraph** 编排多 Agent 协作流程，分三个阶段串行执行：

```
START
  ↓
┌─────────────────────────────────────────────┐
│  阶段一：数据收集与分析                        │
│                                             │
│  📈 市场分析师   ← 行情 / 指数 / 板块工具       │
│       ↓                                     │
│  📊 基本面分析师 ← 财务 / 资金流 / 龙虎榜工具   │
│       ↓                                     │
│  📰 新闻分析师   ← 新闻 / 公告工具             │
│       ↓                                     │
│  🏛️ 宏观分析师   ← CPI / PPI / PMI / GDP 工具 │
└─────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────┐
│  阶段二：投资辩论（多空对决）                   │
│                                             │
│  🐂 多头研究员 ⇄ 🐻 空头研究员（1–3 轮）       │
│       ↓                                     │
│  👔 研究经理 → 初步投资建议 + 评级              │
└─────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────┐
│  阶段三：风险评估（三方辩论）                   │
│                                             │
│  🔥 激进分析师 ⇄ 🛡️ 保守分析师 ⇄ ⚖️ 中性分析师 │
│       ↓                                     │
│  💼 投资组合经理 → 最终研究结论                 │
└─────────────────────────────────────────────┘
  ↓
END
```

**最终输出结构：**
- 评级：Buy / Overweight / Hold / Underweight / Sell
- 信心水平：High / Medium / Low
- 详细推理过程
- 行动建议列表

**节点耗时：** 每个节点名称后附带 `Xs` 耗时标注，工具调用耗时记录在 `DEBUG` 日志。

---

<a id="快速开始"></a>
## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/openmozi/openfr.git
cd openfr

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -e .
```

### 配置

创建 `.env` 文件并配置 API 密钥：

```bash
# 默认推荐：智谱 AI
ZHIPU_API_KEY=your_zhipu_api_key_here
OPENFR_PROVIDER=zhipu
OPENFR_MODEL=glm-4.7
```

更多提供商与配置项请参考下方 **[配置说明](#配置说明)** 章节。

### 开始使用

```bash
# 交互式聊天（推荐）
openfr chat

# 单次查询
openfr query "贵州茅台值得买吗？" --target 贵州茅台
openfr query "分析比亚迪的投资价值" --target 比亚迪 -p deepseek

# 列出可用工具
openfr tools

# 列出支持的提供商
openfr providers
```

---

<a id="使用指南"></a>
## 📖 使用指南

### 交互式聊天

```bash
openfr chat
openfr chat -p dashscope
openfr chat -p zhipu -m glm-4-plus
```

启动后直接输入问题：

```
你: 贵州茅台今天股价多少?
你: 分析今天的热门板块
你: 上证指数走势如何?
你: 比亚迪值得买吗？
```

每个 Agent 节点完成后会显示耗时，例如：

```
📈 市场分析师 · ✓ 市场分析报告已生成 (951 字符) 28.3s
📊 基本面分析师 · ✓ 基本面分析报告已生成 (778 字符) 31.7s
...
⏱ 共执行 11 个节点，用时 363.5 秒
```

### 单次查询

```bash
openfr query "贵州茅台值得买吗？" --target 贵州茅台
openfr query "上证指数今天表现如何？"
openfr query "分析比亚迪的投资价值" --target 比亚迪 -p zhipu
```

### 支持的查询类型

#### 📈 A 股查询

```
查询 000001 的实时行情
贵州茅台最近一周的走势
搜索新能源相关股票
今天的热门股票有哪些?
```

#### 🇭🇰 港股查询

```
查询港股 00700 的实时行情
腾讯控股今天股价
搜索港股理想汽车
```

#### 💼 基金查询

```
查询 510300 的 ETF 数据
股票型基金排行榜
```

#### 📊 指数和板块

```
上证指数今天走势
今天涨幅最大的行业板块
```

#### 🌍 宏观经济

```
最新的 CPI 数据
近期 GDP 增长情况
PMI 指数走势
```

---

<a id="配置说明"></a>
## ⚙️ 配置说明

### 模型配置

在 `.env` 中设置提供商和模型（参考 `.env.example`）：

```bash
OPENFR_PROVIDER=zhipu          # 提供商名称
OPENFR_MODEL=glm-4.7           # 模型名称（留空则使用提供商默认模型）
ZHIPU_API_KEY=your_api_key     # 对应提供商的 API Key
```

| provider | API Key 环境变量 | 默认模型 |
|---|---|---|
| deepseek | `DEEPSEEK_API_KEY` | `deepseek-chat` |
| doubao | `DOUBAO_API_KEY` | `doubao-1-5-pro-256k` |
| dashscope | `DASHSCOPE_API_KEY` | `qwen-max` |
| zhipu | `ZHIPU_API_KEY` | `glm-4.7`（**默认提供商**） |
| modelscope | `MODELSCOPE_API_KEY` | `qwen2.5-72b-instruct` |
| kimi | `KIMI_API_KEY` | `moonshot-v1-128k` |
| stepfun | `STEPFUN_API_KEY` | `step-2-16k` |
| minimax | `MINIMAX_API_KEY` | `MiniMax-Text-01` |
| openai | `OPENAI_API_KEY` | `gpt-4o` |
| anthropic | `ANTHROPIC_API_KEY` | `claude-sonnet-4-20250514` |
| openrouter | `OPENROUTER_API_KEY` | `anthropic/claude-sonnet-4` |
| together | `TOGETHER_API_KEY` | `meta-llama/Llama-3.3-70B-Instruct-Turbo` |
| groq | `GROQ_API_KEY` | `llama-3.3-70b-versatile` |
| ollama | `OLLAMA_BASE_URL` | `qwen2.5:14b` |
| custom | `CUSTOM_API_KEY` + `CUSTOM_BASE_URL` + `CUSTOM_API_STYLE` | （需指定） |

也可以在运行时通过 `-p` / `-m` 参数临时切换：

```bash
openfr chat -p deepseek
openfr chat -p openai -m gpt-4o
openfr query "分析茅台" -p groq
```

### 其他常用配置

```bash
# 调整辩论轮数（轮数越多，分析越深入，耗时越长）
OPENFR_MAX_DEBATE_ROUNDS=1          # 多空辩论轮数（默认 1）
OPENFR_MAX_RISK_DISCUSS_ROUNDS=1    # 风险辩论轮数（默认 1）

# 自定义 OpenAI 兼容接口
OPENFR_PROVIDER=custom
CUSTOM_BASE_URL=https://your-api.example.com
CUSTOM_API_KEY=your-api-key
CUSTOM_API_STYLE=openai             # openai 或 anthropic
```

---

## 🐛 故障排查

### 常见问题

#### 1. API Key 未配置

```bash
# 在 .env 文件中添加
ZHIPU_API_KEY=your-api-key-here

# 或临时设置
export ZHIPU_API_KEY=your-api-key-here
```

#### 2. 网络连接错误

系统会自动重试（最多 3 次）并切换备用数据源。如持续失败，请检查网络连接。

#### 3. 数据接口不可用

非交易时间（工作日 9:30–15:00）部分实时数据不可用，可使用历史数据接口替代。

#### 4. 执行速度慢

多 Agent 模式最少需要 ~15 次串行 LLM 调用，耗时受模型响应速度影响较大。建议：
- 使用响应速度快的模型（如 groq、deepseek）
- 调低 `OPENFR_MAX_DEBATE_ROUNDS` 和 `OPENFR_MAX_RISK_DISCUSS_ROUNDS`
- 查看每个节点后的耗时标注，定位最慢的节点

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 🙏 致谢

- [AKShare](https://github.com/akfamily/akshare) — 提供丰富的金融数据接口
- [LangChain](https://github.com/langchain-ai/langchain) — Agent 框架支持
- [LangGraph](https://github.com/langchain-ai/langgraph) — 多 Agent 图编排
- [TradingAgents](https://github.com/virattt/TradingAgents) — 多 Agent 金融研究架构参考
- [Rich](https://github.com/Textualize/rich) — 美观的终端界面
- [Typer](https://github.com/tiangolo/typer) — 优雅的 CLI 框架

---

<div align="center">

**[⬆ 回到顶部](#)**

Made with ❤️ by OpenFR Team

</div>
