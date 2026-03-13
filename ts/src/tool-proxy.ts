/**
 * Tool proxy: create AgentTool objects that forward calls to the Python server.
 */

import type { AgentTool, AgentToolResult } from "@mariozechner/pi-agent-core";
import type { TSchema } from "@sinclair/typebox";
import type { ToolMeta } from "./tool-discovery.js";
import { jsonSchemaToTypebox } from "./tool-discovery.js";

const TOOL_TIMEOUT_MS = 30_000;

// ---------------------------------------------------------------------------
// Create an AgentTool that proxies to the Python server
// ---------------------------------------------------------------------------

export function createProxyTool(
  meta: ToolMeta,
  serverUrl: string,
): AgentTool<TSchema, unknown> {
  const parameters = jsonSchemaToTypebox(meta.parameters as Record<string, unknown>);
  const baseUrl = serverUrl.replace(/\/+$/, "");

  return {
    name: meta.name,
    label: meta.label,
    description: meta.description,
    parameters,
    execute: async (
      _toolCallId: string,
      params: unknown,
      signal?: AbortSignal,
    ): Promise<AgentToolResult<unknown>> => {
      const args = (params ?? {}) as Record<string, unknown>;
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), TOOL_TIMEOUT_MS);

      // Combine external signal with our timeout
      const combinedSignal = signal
        ? AbortSignal.any([signal, controller.signal])
        : controller.signal;

      try {
        const res = await fetch(`${baseUrl}/tools/${meta.name}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ args }),
          signal: combinedSignal,
        });

        if (!res.ok) {
          const text = await res.text().catch(() => "");
          return {
            content: [{ type: "text", text: `Error calling ${meta.name}: ${res.status} ${text}` }],
            details: { error: true },
          };
        }

        const data = (await res.json()) as { result: string | null; error: string | null };

        if (data.error) {
          return {
            content: [{ type: "text", text: `Error: ${data.error}` }],
            details: { error: true },
          };
        }

        const resultText = typeof data.result === "string" ? data.result : JSON.stringify(data.result ?? "");
        return {
          content: [{ type: "text", text: resultText }],
          details: { toolName: meta.name },
        };
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        if (msg.includes("abort")) {
          return {
            content: [{ type: "text", text: `Tool ${meta.name} timed out or was cancelled` }],
            details: { error: true, timeout: true },
          };
        }
        return {
          content: [{ type: "text", text: `Tool ${meta.name} failed: ${msg}` }],
          details: { error: true },
        };
      } finally {
        clearTimeout(timeout);
      }
    },
  };
}

// ---------------------------------------------------------------------------
// Create all proxy tools from discovered metadata
// ---------------------------------------------------------------------------

export function createAllProxyTools(
  toolsMeta: ToolMeta[],
  serverUrl: string,
): AgentTool<TSchema, unknown>[] {
  return toolsMeta.map((meta) => createProxyTool(meta, serverUrl));
}
