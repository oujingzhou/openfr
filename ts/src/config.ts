/**
 * Configuration management for OpenFR TypeScript Agent.
 *
 * Reads environment variables and maps providers to pi-mono Model objects.
 * Domestic providers (deepseek, zhipu, dashscope, etc.) use openai-completions API
 * with custom base URLs.
 */

import dotenv from "dotenv";
import path from "node:path";
import fs from "node:fs";
import type { Model, Api } from "@mariozechner/pi-ai";

// Load .env from repo root (parent of ts/)
const envPath = path.resolve(process.cwd(), ".env");
const envPathParent = path.resolve(process.cwd(), "..", ".env");
if (fs.existsSync(envPath)) {
  dotenv.config({ path: envPath });
} else if (fs.existsSync(envPathParent)) {
  dotenv.config({ path: envPathParent });
}

// ---------------------------------------------------------------------------
// Provider configuration table (mirrors Python config.py)
// ---------------------------------------------------------------------------

export interface ProviderDef {
  envKey: string;
  baseUrl: string | null;
  defaultModel: string;
  description: string;
}

export const PROVIDER_CONFIG: Record<string, ProviderDef> = {
  // Domestic
  deepseek: {
    envKey: "DEEPSEEK_API_KEY",
    baseUrl: "https://api.deepseek.com/v1",
    defaultModel: "deepseek-chat",
    description: "DeepSeek",
  },
  doubao: {
    envKey: "DOUBAO_API_KEY",
    baseUrl: "https://ark.cn-beijing.volces.com/api/v3",
    defaultModel: "doubao-1-5-pro-256k",
    description: "Doubao (Volcengine)",
  },
  dashscope: {
    envKey: "DASHSCOPE_API_KEY",
    baseUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    defaultModel: "qwen-max",
    description: "DashScope (Alibaba)",
  },
  zhipu: {
    envKey: "ZHIPU_API_KEY",
    baseUrl: "https://open.bigmodel.cn/api/paas/v4",
    defaultModel: "glm-4.7",
    description: "Zhipu AI (GLM)",
  },
  modelscope: {
    envKey: "MODELSCOPE_API_KEY",
    baseUrl: "https://api-inference.modelscope.cn/v1",
    defaultModel: "qwen2.5-72b-instruct",
    description: "ModelScope (Alibaba)",
  },
  kimi: {
    envKey: "KIMI_API_KEY",
    baseUrl: "https://api.moonshot.cn/v1",
    defaultModel: "moonshot-v1-128k",
    description: "Kimi / Moonshot",
  },
  stepfun: {
    envKey: "STEPFUN_API_KEY",
    baseUrl: "https://api.stepfun.com/v1",
    defaultModel: "step-2-16k",
    description: "StepFun",
  },
  minimax: {
    envKey: "MINIMAX_API_KEY",
    baseUrl: "https://api.minimax.chat/v1",
    defaultModel: "MiniMax-Text-01",
    description: "MiniMax",
  },
  // International
  openai: {
    envKey: "OPENAI_API_KEY",
    baseUrl: null,
    defaultModel: "gpt-4o",
    description: "OpenAI",
  },
  anthropic: {
    envKey: "ANTHROPIC_API_KEY",
    baseUrl: null,
    defaultModel: "claude-sonnet-4-20250514",
    description: "Anthropic",
  },
  openrouter: {
    envKey: "OPENROUTER_API_KEY",
    baseUrl: "https://openrouter.ai/api/v1",
    defaultModel: "anthropic/claude-sonnet-4",
    description: "OpenRouter",
  },
  together: {
    envKey: "TOGETHER_API_KEY",
    baseUrl: "https://api.together.xyz/v1",
    defaultModel: "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    description: "Together AI",
  },
  groq: {
    envKey: "GROQ_API_KEY",
    baseUrl: "https://api.groq.com/openai/v1",
    defaultModel: "llama-3.3-70b-versatile",
    description: "Groq",
  },
  // Local
  ollama: {
    envKey: "OLLAMA_BASE_URL",
    baseUrl: "http://localhost:11434",
    defaultModel: "qwen2.5:14b",
    description: "Ollama (local)",
  },
  // Custom
  custom: {
    envKey: "CUSTOM_API_KEY",
    baseUrl: null,
    defaultModel: "",
    description: "Custom OpenAI-compatible",
  },
};

// Providers that use pi-mono's native API rather than openai-completions
const NATIVE_PROVIDERS = new Set(["openai", "anthropic"]);

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

export interface OpenFRConfig {
  provider: string;
  model: string;
  temperature: number;
  maxTokens: number;
  toolServerUrl: string;
  maxIterations: number;
  enablePlanExecute: boolean;
  enableSelfValidation: boolean;
  enableLoopDetection: boolean;
  maxTotalToolCalls: number;
}

function envBool(key: string, fallback: boolean): boolean {
  const v = process.env[key];
  if (v === undefined) return fallback;
  return v.toLowerCase() === "true";
}

export function loadConfig(): OpenFRConfig {
  const provider = process.env.OPENFR_PROVIDER ?? "zhipu";
  const def = PROVIDER_CONFIG[provider] ?? PROVIDER_CONFIG.zhipu;
  const model = process.env.OPENFR_MODEL || def.defaultModel;

  return {
    provider,
    model,
    temperature: parseFloat(process.env.OPENFR_TEMPERATURE ?? "0.0"),
    maxTokens: parseInt(process.env.OPENFR_MAX_TOKENS ?? "4096", 10),
    toolServerUrl: process.env.OPENFR_TOOL_SERVER_URL ?? "http://127.0.0.1:18321",
    maxIterations: parseInt(process.env.OPENFR_MAX_ITERATIONS ?? "10", 10),
    enablePlanExecute: envBool("OPENFR_ENABLE_PLAN_EXECUTE", true),
    enableSelfValidation: envBool("OPENFR_ENABLE_SELF_VALIDATION", true),
    enableLoopDetection: envBool("OPENFR_ENABLE_LOOP_DETECTION", true),
    maxTotalToolCalls: parseInt(process.env.OPENFR_MAX_TOTAL_TOOL_CALLS ?? "14", 10),
  };
}

// ---------------------------------------------------------------------------
// Model builder
// ---------------------------------------------------------------------------

/**
 * Build a pi-mono Model object from the config.
 *
 * For native providers (openai, anthropic) we try getModel() first.
 * For all OpenAI-compatible providers we construct a custom Model with
 * api: "openai-completions".
 */
export function buildModel(cfg: OpenFRConfig): Model<Api> {
  const provDef = PROVIDER_CONFIG[cfg.provider];
  if (!provDef) {
    throw new Error(`Unknown provider: ${cfg.provider}`);
  }

  // Try native pi-mono model for known providers
  if (NATIVE_PROVIDERS.has(cfg.provider)) {
    try {
      // Dynamic import not needed - we construct inline
      // The native providers use getModel from pi-ai, but we may not have
      // the exact model ID registered. Construct manually to be safe.
      const api = cfg.provider === "anthropic" ? "anthropic-messages" : "openai-completions";
      const baseUrl =
        cfg.provider === "openai"
          ? "https://api.openai.com/v1"
          : cfg.provider === "anthropic"
            ? "https://api.anthropic.com"
            : provDef.baseUrl ?? "";

      return {
        id: cfg.model,
        name: cfg.model,
        api: api as Api,
        provider: cfg.provider,
        baseUrl,
        reasoning: false,
        input: ["text"],
        cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
        contextWindow: 128000,
        maxTokens: cfg.maxTokens,
      };
    } catch {
      // Fall through to generic
    }
  }

  // OpenAI-compatible for everything else
  let baseUrl = provDef.baseUrl ?? "";

  // Special overrides
  if (cfg.provider === "ollama") {
    baseUrl = process.env.OLLAMA_BASE_URL ?? provDef.baseUrl ?? "http://localhost:11434";
    // Ollama uses /v1 endpoint for OpenAI compat
    if (!baseUrl.endsWith("/v1")) {
      baseUrl = baseUrl.replace(/\/+$/, "") + "/v1";
    }
  } else if (cfg.provider === "custom") {
    baseUrl = process.env.CUSTOM_BASE_URL ?? "";
  }

  return {
    id: cfg.model,
    name: cfg.model,
    api: "openai-completions" as Api,
    provider: cfg.provider,
    baseUrl,
    reasoning: false,
    input: ["text"],
    cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
    contextWindow: 128000,
    maxTokens: cfg.maxTokens,
    compat: {
      supportsUsageInStreaming: cfg.provider !== "ollama",
      maxTokensField: "max_tokens" as const,
      supportsStrictMode: false,
    },
  };
}

/**
 * Resolve the API key for a given provider name.
 */
export function getApiKey(provider: string): string | undefined {
  const def = PROVIDER_CONFIG[provider];
  if (!def) return undefined;

  // For custom provider
  if (provider === "custom") {
    return process.env.CUSTOM_API_KEY;
  }

  return process.env[def.envKey];
}
