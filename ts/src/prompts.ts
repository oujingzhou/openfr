/**
 * Financial research prompts — ported from Python prompts.py.
 */

function getWeekday(): string {
  const map: Record<number, string> = {
    0: "星期日",
    1: "星期一",
    2: "星期二",
    3: "星期三",
    4: "星期四",
    5: "星期五",
    6: "星期六",
  };
  return map[new Date().getDay()] ?? "";
}

function formatDate(): string {
  const d = new Date();
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`;
}

// ---------------------------------------------------------------------------
// System prompt (matches Python get_system_prompt)
// ---------------------------------------------------------------------------

export function getSystemPrompt(): string {
  return `你是专业的金融研究分析师助手，专注于中国股票及港股市场分析。

今天是 ${formatDate()} ${getWeekday()}。

## 核心原则

1. **数据驱动**: 先获取数据再分析，基于事实而非推测
2. **高效执行**: 优先使用最直接的工具，避免重复调用
3. **并行思维**: 多个独立数据可以同时获取（如查询多只股票）
4. **结构化输出**: 用清晰的格式呈现分析结果
5. **风险提示**: 投资建议必须包含风险说明

## 工具使用技巧

- 搜索股票：优先用 \`search_stock_any\`（跨市场），明确市场时用 \`search_stock\` 或 \`search_stock_hk\`
- 行业分析：用 \`get_industry_board_detail\` 获取行业整体数据（涨跌幅、PE/PB）
- 多只股票：可以连续调用工具获取不同股票数据
- 历史数据：明确指定时间范围，避免获取过多数据

## 注意

- 信息仅供参考，不构成投资建议
- 数据可能存在延迟或误差
- 日期计算需准确（不要混淆星期几）
`;
}

// ---------------------------------------------------------------------------
// Planning prompt
// ---------------------------------------------------------------------------

export const PLANNING_SYSTEM_PROMPT = `你是金融研究任务规划助手。将用户问题拆解为 2～5 个可执行步骤。

输出格式（纯 JSON，无其他内容）：
{"steps": [{"goal": "步骤1描述"}, {"goal": "步骤2描述"}]}

示例：
用户问："分析贵州茅台"
输出：{"steps": [{"goal": "搜索茅台股票代码"}, {"goal": "获取实时行情和基本信息"}, {"goal": "查看行业板块表现"}]}

要求：
- 步骤顺序：先搜索/定位 → 查详情/行情 → 查板块/宏观
- 每步一句话，动词开头（如"搜索"、"获取"、"查看"）
- 步骤独立，可并行执行的合并为一步
- 不输出 markdown 代码块标记`;

// ---------------------------------------------------------------------------
// Final answer & validation prompts
// ---------------------------------------------------------------------------

export const FINAL_ANSWER_PROMPT = `基于以上收集到的所有信息，请给出最终的分析和回答。

要求：
1. 综合所有数据，给出清晰的结论
2. 用结构化的方式呈现分析结果
3. 如果涉及投资建议，提供风险提示
4. 使用中文回答
`;

export const SELF_VALIDATION_PROMPT = `请先自检当前已获取的工具结果：
1. 是否足以回答用户问题？有无明显遗漏（如缺少关键代码、时间范围、板块名称等）？
2. 是否存在矛盾或异常（如同一指标多处不一致）？

若数据已充分，请直接给出最终的分析和回答（要求：结论清晰、结构化、含风险提示、中文）。
若发现明显不足，请简要说明还缺哪类数据，然后基于现有信息给出力所能及的回答，并注明数据限制。
`;

export const LOOP_DETECTED_PROMPT = `检测到近期多次工具调用未取得有效数据或重复尝试，请基于目前已获取的任何信息，直接给出最终回答。

要求：简要总结已掌握的信息，说明数据上的限制（如有），给出力所能及的结论与风险提示，使用中文。不要再调用工具。
`;

// ---------------------------------------------------------------------------
// Parse plan output (matches Python parse_plan)
// ---------------------------------------------------------------------------

export interface PlanStep {
  goal: string;
}

export function parsePlan(llmOutput: string): PlanStep[] {
  if (!llmOutput?.trim()) return [];

  let text = llmOutput.trim();

  // Strip markdown code fences
  if (text.includes("```")) {
    for (const start of ["```json", "```"]) {
      const idx = text.indexOf(start);
      if (idx !== -1) {
        const contentStart = idx + start.length;
        const end = text.indexOf("```", contentStart);
        text = text.slice(contentStart, end !== -1 ? end : undefined).trim();
        break;
      }
    }
  }

  // Try JSON parse
  try {
    const data = JSON.parse(text);
    let steps: unknown[];
    if (typeof data === "object" && data !== null && "steps" in data) {
      steps = data.steps;
    } else if (Array.isArray(data)) {
      steps = data;
    } else {
      return [];
    }

    if (!Array.isArray(steps)) return [];

    const result: PlanStep[] = [];
    for (const s of steps) {
      if (typeof s === "object" && s !== null && "goal" in s) {
        result.push({ goal: String((s as { goal: unknown }).goal).trim() });
      } else if (typeof s === "string") {
        result.push({ goal: s.trim() });
      }
    }
    return result;
  } catch {
    // Fallback: parse "1. description" lines
  }

  const result: PlanStep[] = [];
  for (const line of text.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const m = trimmed.match(/^\d+[.．]\s*(.+)$/);
    if (m) {
      result.push({ goal: m[1].trim() });
    } else if (trimmed.length > 2 && !trimmed.startsWith("{")) {
      result.push({ goal: trimmed });
    }
  }
  return result.slice(0, 10);
}
