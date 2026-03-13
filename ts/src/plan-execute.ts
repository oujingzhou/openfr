/**
 * Plan-Execute orchestration layer.
 *
 * Implements the Dexter-style workflow:
 * 1. Planning: LLM decomposes query into steps (no tools)
 * 2. Execution: For each step, run agent with tools
 * 3. Finalization: LLM synthesizes final answer (no tools, optional self-validation)
 */

import type { Agent } from "@mariozechner/pi-agent-core";
import type { Model, Api, AssistantMessage, Message, TextContent } from "@mariozechner/pi-ai";
import { completeSimple } from "@mariozechner/pi-ai";
import type { AgentTool } from "@mariozechner/pi-agent-core";
import type { TSchema } from "@sinclair/typebox";
import {
  getSystemPrompt,
  PLANNING_SYSTEM_PROMPT,
  FINAL_ANSWER_PROMPT,
  SELF_VALIDATION_PROMPT,
  LOOP_DETECTED_PROMPT,
  parsePlan,
  type PlanStep,
} from "./prompts.js";
import { Scratchpad } from "./scratchpad.js";
import type { OpenFRConfig } from "./config.js";
import { getApiKey } from "./config.js";

// ---------------------------------------------------------------------------
// Event types emitted during plan-execute
// ---------------------------------------------------------------------------

export type PlanExecuteEvent =
  | { type: "planning" }
  | { type: "plan"; steps: PlanStep[] }
  | { type: "step_start"; stepIndex: number; goal: string }
  | { type: "tool_start"; toolName: string; args: Record<string, unknown>; stepIndex: number }
  | { type: "tool_end"; toolName: string; resultPreview: string; stepIndex: number }
  | { type: "tool_warning"; message: string }
  | { type: "step_end"; stepIndex: number }
  | { type: "synthesizing" }
  | { type: "text_delta"; delta: string }
  | { type: "answer"; content: string }
  | { type: "error"; message: string };

// ---------------------------------------------------------------------------
// Plan-Execute runner
// ---------------------------------------------------------------------------

export async function runPlanExecute(
  agent: Agent,
  query: string,
  model: Model<Api>,
  tools: AgentTool<TSchema, unknown>[],
  config: OpenFRConfig,
  onEvent: (event: PlanExecuteEvent) => void,
  signal?: AbortSignal,
): Promise<string> {
  const scratchpad = new Scratchpad(query, 3, config.maxTotalToolCalls);

  // ----- Step 1: Planning -----
  onEvent({ type: "planning" });

  let steps: PlanStep[];
  try {
    const planResponse = await completeSimple(
      model,
      {
        systemPrompt: PLANNING_SYSTEM_PROMPT,
        messages: [{ role: "user", content: `用户问题: ${query}`, timestamp: Date.now() }],
      },
      {
        temperature: 0,
        maxTokens: 1024,
        apiKey: getApiKey(config.provider),
        signal,
      },
    );

    const planText = extractText(planResponse);
    steps = parsePlan(planText);

    if (steps.length === 0) {
      // Fallback: single step
      steps = [{ goal: query }];
    }
  } catch (err) {
    onEvent({ type: "error", message: `Planning failed: ${err}` });
    steps = [{ goal: query }];
  }

  onEvent({ type: "plan", steps });

  // ----- Step 2: Execute each step -----
  for (let i = 0; i < steps.length; i++) {
    if (signal?.aborted) break;

    const step = steps[i];
    onEvent({ type: "step_start", stepIndex: i, goal: step.goal });

    // Check loop detection
    if (config.enableLoopDetection && scratchpad.isLoopNoProgress()) {
      onEvent({ type: "tool_warning", message: "检测到循环，跳过剩余步骤" });
      break;
    }

    // Check total call limit
    if (scratchpad.totalCalls >= config.maxTotalToolCalls) {
      onEvent({ type: "tool_warning", message: "已达到总工具调用上限" });
      break;
    }

    // Build step context
    const contextSoFar = scratchpad.getContext();
    const stepPrompt = contextSoFar
      ? `当前任务步骤：${step.goal}\n\n已获取的数据：\n${contextSoFar}\n\n请执行当前步骤，调用相关工具获取数据。`
      : `当前任务步骤：${step.goal}\n\n请执行当前步骤，调用相关工具获取数据。`;

    // Set up agent for this step
    agent.setSystemPrompt(getSystemPrompt());
    agent.setTools(tools);
    agent.clearMessages();

    // Subscribe to track tool calls for this step
    const unsubscribe = agent.subscribe((event) => {
      if (event.type === "tool_execution_start") {
        const check = scratchpad.canCallTool(event.toolName, event.args);
        if (!check.allowed) {
          onEvent({ type: "tool_warning", message: check.reason });
        }
        onEvent({
          type: "tool_start",
          toolName: event.toolName,
          args: event.args,
          stepIndex: i,
        });
      }
      if (event.type === "tool_execution_end") {
        const resultText = extractToolResultText(event.result);
        const preview = resultText.length > 200 ? resultText.slice(0, 200) + "..." : resultText;

        scratchpad.addCall(
          event.toolName,
          {},
          resultText,
          event.isError ? resultText : undefined,
        );

        onEvent({
          type: "tool_end",
          toolName: event.toolName,
          resultPreview: preview,
          stepIndex: i,
        });
      }
    });

    try {
      await agent.prompt(stepPrompt);
    } catch (err) {
      onEvent({ type: "error", message: `Step ${i + 1} failed: ${err}` });
    } finally {
      unsubscribe();
    }

    onEvent({ type: "step_end", stepIndex: i });
  }

  // ----- Step 3: Final synthesis -----
  onEvent({ type: "synthesizing" });

  const allContext = scratchpad.getContext(10);

  let finalPromptText: string;
  if (config.enableLoopDetection && scratchpad.isLoopNoProgress()) {
    finalPromptText = `用户问题: ${query}\n\n已获取的数据：\n${allContext}\n\n${LOOP_DETECTED_PROMPT}`;
  } else if (config.enableSelfValidation) {
    finalPromptText = `用户问题: ${query}\n\n已获取的数据：\n${allContext}\n\n${SELF_VALIDATION_PROMPT}`;
  } else {
    finalPromptText = `用户问题: ${query}\n\n已获取的数据：\n${allContext}\n\n${FINAL_ANSWER_PROMPT}`;
  }

  let finalAnswer = "";

  try {
    const finalResponse = await completeSimple(
      model,
      {
        systemPrompt: getSystemPrompt(),
        messages: [{ role: "user", content: finalPromptText, timestamp: Date.now() }],
      },
      {
        temperature: 0,
        maxTokens: config.maxTokens,
        apiKey: getApiKey(config.provider),
        signal,
      },
    );

    finalAnswer = extractText(finalResponse);
  } catch (err) {
    finalAnswer = `分析过程中出现错误: ${err}\n\n已获取的部分数据:\n${allContext}`;
  }

  onEvent({ type: "answer", content: finalAnswer });
  return finalAnswer;
}

// ---------------------------------------------------------------------------
// Simple (no-plan) single-shot mode
// ---------------------------------------------------------------------------

export async function runSimple(
  agent: Agent,
  query: string,
  tools: AgentTool<TSchema, unknown>[],
  onEvent: (event: PlanExecuteEvent) => void,
): Promise<string> {
  agent.setSystemPrompt(getSystemPrompt());
  agent.setTools(tools);
  agent.clearMessages();

  let answer = "";

  const unsubscribe = agent.subscribe((event) => {
    if (event.type === "tool_execution_start") {
      onEvent({
        type: "tool_start",
        toolName: event.toolName,
        args: event.args,
        stepIndex: 0,
      });
    }
    if (event.type === "tool_execution_end") {
      const text = extractToolResultText(event.result);
      onEvent({
        type: "tool_end",
        toolName: event.toolName,
        resultPreview: text.slice(0, 200),
        stepIndex: 0,
      });
    }
    if (event.type === "agent_end") {
      // Extract final assistant message
      for (const msg of event.messages) {
        if (msg.role === "assistant") {
          const asst = msg as AssistantMessage;
          for (const c of asst.content) {
            if (c.type === "text") {
              answer += c.text;
            }
          }
        }
      }
    }
  });

  try {
    await agent.prompt(query);
  } finally {
    unsubscribe();
  }

  if (answer) {
    onEvent({ type: "answer", content: answer });
  }
  return answer;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function extractText(msg: AssistantMessage): string {
  return msg.content
    .filter((c): c is TextContent => c.type === "text")
    .map((c) => c.text)
    .join("");
}

function extractToolResultText(result: unknown): string {
  if (!result || typeof result !== "object") return String(result ?? "");
  const r = result as { content?: { type: string; text: string }[] };
  if (Array.isArray(r.content)) {
    return r.content
      .filter((c) => c.type === "text")
      .map((c) => c.text)
      .join("");
  }
  return JSON.stringify(result);
}
