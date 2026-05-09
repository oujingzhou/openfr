<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![AKShare](https://img.shields.io/badge/powered%20by-AKShare-orange.svg)](https://github.com/akfamily/akshare)

**OpenFR: Lightweight Financial Research Agent | Powered by AKShare | Multi-LLM | Multi-Agent Deep Analysis**

[中文](README_CN.md) | [Quick Start](#quick-start) • [Features](#features) • [Usage](#usage) • [Configuration](#configuration) • [Architecture](#architecture)

</div>

---

## 📊 Overview

OpenFR (Open Financial Research) is a **minimal, lightweight** intelligent financial research Agent. Built on large language models and integrated with AKShare data APIs, it uses **multi-agent collaboration** to deliver in-depth investment research across stocks, funds, futures, indices, macroeconomics, and more.

<a id="features"></a>
### ✨ Features

- 🌱 **Minimal & Lightweight** — Pure Python package + Typer CLI, AKShare data only, one command to start researching
- 🧠 **Multi-Agent Collaboration** — Four analysts + bull/bear debate + three-way risk assessment, orchestrated via LangGraph StateGraph
- ⏱️ **Per-Node Timing** — Elapsed time displayed after each agent node, making it easy to identify performance bottlenecks
- 📋 **Full Intermediate Reports** — Market / fundamental / news / macro reports, debate transcripts, and risk assessments shown in full
- 📈 **Rich Data** — 35+ financial data tools: A-shares, HK stocks, funds, futures, indices, macro, and sectors
- 🔄 **Multi-LLM** — 15+ providers (domestic Chinese, overseas, local), compatible with OpenAI and Anthropic formats
- 🎨 **Nice CLI** — Rich terminal UI with live progress and complete analysis content per stage
- 🔌 **Fallback Sources** — East Money + Sina + Tonghuashun with automatic switch and retry
- 💾 **Cache Friendly** — Stock list cached 6h, some quote data cached 1min, reducing redundant requests
- 🛡️ **Error Recovery** — Retry, fallback, and "finish with available info" protection logic

---

<a id="architecture"></a>
## 🏗️ Architecture

OpenFR uses **LangGraph StateGraph** to orchestrate a three-phase multi-agent workflow:

```
START
  ↓
┌─────────────────────────────────────────────┐
│  Phase 1: Data Collection & Analysis         │
│                                             │
│  📈 Market Analyst      ← quote/index/sector │
│       ↓                                     │
│  📊 Fundamentals Analyst ← financials/flow   │
│       ↓                                     │
│  📰 News Analyst         ← news/announcements│
│       ↓                                     │
│  🏛️ Macro Analyst        ← CPI/PPI/PMI/GDP   │
└─────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────┐
│  Phase 2: Investment Debate (Bull vs Bear)   │
│                                             │
│  🐂 Bull Researcher ⇄ 🐻 Bear Researcher    │
│       ↓                 (1–3 rounds)        │
│  👔 Research Manager → Initial recommendation│
└─────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────┐
│  Phase 3: Risk Assessment (Three-Way Debate) │
│                                             │
│  🔥 Aggressive ⇄ 🛡️ Conservative ⇄ ⚖️ Neutral│
│       ↓                                     │
│  💼 Portfolio Manager → Final decision       │
└─────────────────────────────────────────────┘
  ↓
END
```

**Final output:**
- Rating: Buy / Overweight / Hold / Underweight / Sell
- Confidence: High / Medium / Low
- Detailed reasoning
- Action recommendations

**Per-node timing:** Each node name is followed by `Xs` elapsed time. Individual tool call timings are written to `DEBUG` logs.

---

<a id="quick-start"></a>
## 🚀 Quick Start

### Install

```bash
# Clone repo
git clone https://github.com/openmozi/openfr.git
cd openfr

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install
pip install -e .
```

### Configure

Create a `.env` file and set your API key:

```bash
# Recommended default: Zhipu AI
ZHIPU_API_KEY=your_zhipu_api_key_here
OPENFR_PROVIDER=zhipu
OPENFR_MODEL=glm-4.7
```

See **[Configuration](#configuration)** for more providers and options.

### Run

```bash
# Interactive chat (recommended)
openfr chat

# Single query
openfr query "Is Kweichow Moutai a good buy?" --target 贵州茅台
openfr query "Analyze BYD's investment value" --target 比亚迪 -p deepseek

# List tools and providers
openfr tools
openfr providers
```

---

<a id="usage"></a>
## 📖 Usage

### Interactive chat

```bash
openfr chat
openfr chat -p dashscope
openfr chat -p zhipu -m glm-4-plus
```

Then type your question:

```
You: What is Kweichow Moutai's price today?
You: Analyze today's hot sectors
You: How is the Shanghai Composite Index?
You: Is BYD worth buying?
```

After each agent node completes, you'll see timing info, for example:

```
📈 Market Analyst · ✓ Market report generated (951 chars) 28.3s
📊 Fundamentals Analyst · ✓ Fundamentals report generated (778 chars) 31.7s
...
⏱ 11 nodes executed, total time 363.5s
```

### Single query

```bash
openfr query "Is Kweichow Moutai a good buy?" --target 贵州茅台
openfr query "How did the Shanghai Composite Index perform today?"
openfr query "Analyze BYD's investment value" --target 比亚迪 -p zhipu
```

### Supported query types

#### 📈 A-shares

```
Real-time quote for 000001
Kweichow Moutai last week trend
Search new energy related stocks
Today's hot stocks
```

#### 🇭🇰 HK stocks

```
Real-time quote for HK 00700
Tencent Holdings price today
Search HK Li Auto
```

#### 💼 Funds

```
ETF data for 510300
Top equity fund ranking
```

#### 📊 Indices and sectors

```
Shanghai Composite today
Today's top sectors by gain
```

#### 🌍 Macro

```
Latest CPI data
Recent GDP growth
PMI trend
```

---

<a id="configuration"></a>
## ⚙️ Configuration

### Model setup

Set your provider and model in `.env` (see `.env.example`):

```bash
OPENFR_PROVIDER=zhipu          # provider name
OPENFR_MODEL=glm-4.7           # model name (leave empty to use provider default)
ZHIPU_API_KEY=your_api_key     # API key for the chosen provider
```

| provider | API Key env var | Default model |
|---|---|---|
| deepseek | `DEEPSEEK_API_KEY` | `deepseek-chat` |
| doubao | `DOUBAO_API_KEY` | `doubao-1-5-pro-256k` |
| dashscope | `DASHSCOPE_API_KEY` | `qwen-max` |
| zhipu | `ZHIPU_API_KEY` | `glm-4.7` (**default provider**) |
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
| custom | `CUSTOM_API_KEY` + `CUSTOM_BASE_URL` + `CUSTOM_API_STYLE` | (specify) |

You can also switch provider/model at runtime with `-p` / `-m`:

```bash
openfr chat -p deepseek
openfr chat -p openai -m gpt-4o
openfr query "Analyze Moutai" -p groq
```

### Other options

```bash
# Debate rounds (more rounds = deeper analysis, longer runtime)
OPENFR_MAX_DEBATE_ROUNDS=1          # bull/bear debate rounds (default 1)
OPENFR_MAX_RISK_DISCUSS_ROUNDS=1    # risk debate rounds (default 1)

# Custom OpenAI-compatible endpoint
OPENFR_PROVIDER=custom
CUSTOM_BASE_URL=https://your-api.example.com
CUSTOM_API_KEY=your-api-key
CUSTOM_API_STYLE=openai             # openai or anthropic
```

---

## 🐛 Troubleshooting

### Common issues

#### 1. API key not set

```bash
# In .env
ZHIPU_API_KEY=your-api-key-here

# Or temporarily
export ZHIPU_API_KEY=your-api-key-here
```

#### 2. Network errors

Auto retry (up to 3 times) with fallback to backup data source. If it keeps failing, check your network.

#### 3. Data API unavailable

Some real-time data is only available during market hours (weekdays 9:30–15:00 CST). Use history APIs instead.

#### 4. Slow execution

Multi-agent mode requires at minimum ~15 serial LLM calls. Total time depends heavily on model latency. To speed up:
- Use a fast model such as groq or deepseek
- Lower `OPENFR_MAX_DEBATE_ROUNDS` and `OPENFR_MAX_RISK_DISCUSS_ROUNDS`
- Check the per-node `Xs` timing in the output to find the slowest nodes

---

## 🤝 Contributing

Contributions, issues, and ideas are all welcome.

1. Fork the repo
2. Create a branch (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add some AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

**Code style:** format with Black, lint with Ruff, add type hints where useful.

---

## 🙏 Acknowledgments

- [AKShare](https://github.com/akfamily/akshare) — Financial data APIs
- [LangChain](https://github.com/langchain-ai/langchain) — Agent framework
- [LangGraph](https://github.com/langchain-ai/langgraph) — Multi-agent graph orchestration
- [TradingAgents](https://github.com/virattt/TradingAgents) — Multi-agent financial research architecture reference
- [Rich](https://github.com/Textualize/rich) — Terminal UI
- [Typer](https://github.com/tiangolo/typer) — CLI framework

---

<div align="center">

**[⬆ Back to top](#)**

[中文](README.md) | English

Made with ❤️ by OpenFR Team

</div>
