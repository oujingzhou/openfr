/**
 * Scratchpad: tool call tracking, duplicate detection, loop detection.
 *
 * Ported from Python scratchpad.py with O(1) operations.
 */

import crypto from "node:crypto";

export interface ToolCallRecord {
  toolName: string;
  args: Record<string, unknown>;
  result: string;
  error?: string;
  timestamp: number;
}

export class Scratchpad {
  readonly query: string;
  readonly maxCallsPerTool: number;
  readonly maxTotalCalls: number;

  private _calls: ToolCallRecord[] = [];
  private _toolCallCounts = new Map<string, number>();
  private _calledArgs = new Set<string>();

  constructor(query: string, maxCallsPerTool = 3, maxTotalCalls = 14) {
    this.query = query;
    this.maxCallsPerTool = maxCallsPerTool;
    this.maxTotalCalls = maxTotalCalls;
  }

  get calls(): readonly ToolCallRecord[] {
    return this._calls;
  }

  get totalCalls(): number {
    return this._calls.length;
  }

  addCall(
    toolName: string,
    args: Record<string, unknown>,
    result: string,
    error?: string,
  ): void {
    this._calls.push({ toolName, args, result, error, timestamp: Date.now() });
    this._toolCallCounts.set(toolName, (this._toolCallCounts.get(toolName) ?? 0) + 1);
    this._calledArgs.add(this._argsKey(toolName, args));
  }

  canCallTool(
    toolName: string,
    args?: Record<string, unknown>,
  ): { allowed: boolean; reason: string } {
    // Total limit
    if (this._calls.length >= this.maxTotalCalls) {
      return { allowed: false, reason: `已达到总工具调用上限 (${this.maxTotalCalls} 次)` };
    }

    // Per-tool limit
    const count = this._toolCallCounts.get(toolName) ?? 0;
    if (count >= this.maxCallsPerTool) {
      return {
        allowed: false,
        reason: `已达到工具 ${toolName} 的调用上限 (${this.maxCallsPerTool} 次)`,
      };
    }

    // Duplicate detection
    if (args) {
      if (this._calledArgs.has(this._argsKey(toolName, args))) {
        return { allowed: false, reason: `工具 ${toolName} 已使用相同参数调用过` };
      }
    }

    return { allowed: true, reason: "" };
  }

  /**
   * Count recent failures in the last `window` calls.
   */
  recentFailuresCount(window = 4): number {
    const failureKeywords = ["未找到", "失败", "超时", "无法获取", "跳过", "错误", "异常"];
    const recent = this._calls.slice(-window);
    let count = 0;
    for (const tc of recent) {
      if (tc.error) {
        count++;
      } else {
        const text = (tc.result ?? "").trim();
        if (!text || failureKeywords.some((k) => text.includes(k))) {
          count++;
        }
      }
    }
    return count;
  }

  /**
   * Detect no-progress loops.
   */
  isLoopNoProgress(window = 4, failureThreshold = 3): boolean {
    if (this._calls.length < failureThreshold) return false;
    return this.recentFailuresCount(window) >= failureThreshold;
  }

  /**
   * Get formatted context from recent tool calls.
   */
  getContext(maxResults = 5): string {
    if (this._calls.length === 0) return "";
    const recent = this._calls.slice(-maxResults);
    return recent
      .map((tc) => {
        if (tc.error) return `[${tc.toolName}] 错误: ${tc.error}`;
        const result = tc.result.length > 2000 ? tc.result.slice(0, 2000) + "..." : tc.result;
        return `[${tc.toolName}] ${result}`;
      })
      .join("\n\n");
  }

  private _argsKey(toolName: string, args: Record<string, unknown>): string {
    const sorted = JSON.stringify(args, Object.keys(args).sort());
    return `${toolName}:${sorted}`;
  }
}
