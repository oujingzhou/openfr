/**
 * OpenFR TypeScript Agent entry point.
 *
 * - Spawns the Python tool server as a child process
 * - Discovers tools via HTTP
 * - Creates pi-mono Agent with proxy tools
 * - Runs plan-execute workflow
 */

import { spawn, type ChildProcess } from "node:child_process";
import { Agent } from "@mariozechner/pi-agent-core";
import type { AgentMessage } from "@mariozechner/pi-agent-core";
import type { Message } from "@mariozechner/pi-ai";
import chalk from "chalk";
import { loadConfig, buildModel, getApiKey, type OpenFRConfig } from "./config.js";
import { discoverTools, type ToolMeta } from "./tool-discovery.js";
import { createAllProxyTools } from "./tool-proxy.js";
import { runPlanExecute, runSimple } from "./plan-execute.js";
import {
  createEventRenderer,
  setToolLabels,
  interactiveChat,
  printTools,
} from "./cli.js";

// ---------------------------------------------------------------------------
// Python server lifecycle
// ---------------------------------------------------------------------------

async function startPythonServer(config: OpenFRConfig): Promise<ChildProcess> {
  const serverUrl = config.toolServerUrl;
  const port = new URL(serverUrl).port || "18321";

  // Check if server is already running
  try {
    const res = await fetch(`${serverUrl}/health`);
    if (res.ok) {
      console.log(chalk.dim("Python tool server already running"));
      return null as unknown as ChildProcess; // Server already up
    }
  } catch {
    // Not running, start it
  }

  console.log(chalk.dim("Starting Python tool server..."));

  // Resolve Python executable: prefer .venv in repo root, then python3, then python
  const repoRoot = new URL("../../", import.meta.url).pathname.replace(/\/$/, "");
  const venvPython = `${repoRoot}/.venv/bin/python`;

  let pythonCmd: string;
  try {
    const fs = await import("node:fs");
    if (fs.existsSync(venvPython)) {
      pythonCmd = venvPython;
    } else {
      // Check python3 exists
      const { execFileSync } = await import("node:child_process");
      try {
        execFileSync("python3", ["--version"], { stdio: "ignore" });
        pythonCmd = "python3";
      } catch {
        pythonCmd = "python";
      }
    }
  } catch {
    pythonCmd = "python3";
  }

  const child = spawn(pythonCmd, ["-m", "openfr.server"], {
    env: { ...process.env, OPENFR_SERVER_PORT: port },
    stdio: ["ignore", "pipe", "pipe"],
    cwd: repoRoot,
  });

  // Catch spawn errors (e.g. executable not found)
  let spawnError: Error | undefined = undefined;
  child.on("error", (err) => {
    spawnError = err;
  });

  // Wait for server to be ready
  const maxWait = 30_000;
  const start = Date.now();
  while (Date.now() - start < maxWait) {
    if (spawnError) {
      const err = spawnError as Error;
      throw new Error(
        `Failed to start Python server (${pythonCmd}): ${err.message}\n` +
          "Make sure Python is installed and openfr is installed (pip install -e .)",
      );
    }
    try {
      const res = await fetch(`${serverUrl}/health`);
      if (res.ok) {
        console.log(chalk.dim("Python tool server ready"));
        return child;
      }
    } catch {
      // Not ready yet
    }
    await new Promise((r) => setTimeout(r, 500));
  }

  child.kill();
  throw new Error("Python tool server failed to start within 30s");
}

function stopPythonServer(child: ChildProcess | null): void {
  if (child && !child.killed) {
    child.kill("SIGTERM");
  }
}

// ---------------------------------------------------------------------------
// Agent factory
// ---------------------------------------------------------------------------

function createAgent(config: OpenFRConfig): Agent {
  const model = buildModel(config);

  const agent = new Agent({
    initialState: {
      systemPrompt: "",
      model,
      tools: [],
      thinkingLevel: "off",
    },
    convertToLlm: (messages: AgentMessage[]): Message[] => {
      return messages.filter(
        (m): m is Message =>
          m.role === "user" || m.role === "assistant" || m.role === "toolResult",
      );
    },
    getApiKey: (provider: string) => getApiKey(provider),
  });

  return agent;
}

// ---------------------------------------------------------------------------
// Main commands
// ---------------------------------------------------------------------------

async function commandQuery(
  query: string,
  config: OpenFRConfig,
  tools: ToolMeta[],
  agent: Agent,
): Promise<void> {
  const proxyTools = createAllProxyTools(tools, config.toolServerUrl);
  const model = buildModel(config);
  const { onEvent, cleanup } = createEventRenderer();

  try {
    if (config.enablePlanExecute) {
      await runPlanExecute(agent, query, model, proxyTools, config, onEvent);
    } else {
      await runSimple(agent, query, proxyTools, onEvent);
    }
  } finally {
    cleanup();
  }
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const command = args[0] ?? "chat";

  const config = loadConfig();
  let pythonServer: ChildProcess | null = null;

  // Graceful shutdown
  const shutdown = () => {
    stopPythonServer(pythonServer);
    process.exit(0);
  };
  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);

  try {
    // Start Python server
    pythonServer = await startPythonServer(config);

    // Discover tools
    console.log(chalk.dim("Discovering tools..."));
    const tools = await discoverTools(config.toolServerUrl);
    setToolLabels(tools);
    console.log(chalk.dim(`Found ${tools.length} tools`));

    if (command === "tools") {
      printTools(tools);
      return;
    }

    const agent = createAgent(config);

    if (command === "query") {
      const query = args.slice(1).join(" ");
      if (!query) {
        console.error(chalk.red("Usage: openfr query \"your question\""));
        process.exit(1);
      }
      await commandQuery(query, config, tools, agent);
    } else if (command === "chat") {
      await interactiveChat(async (query) => {
        await commandQuery(query, config, tools, agent);
      });
    } else {
      // Treat the entire args as a query
      const query = args.join(" ");
      if (query) {
        await commandQuery(query, config, tools, agent);
      } else {
        console.log(chalk.bold.blue("OpenFR - 金融研究助手"));
        console.log();
        console.log("Commands:");
        console.log(`  ${chalk.cyan("query")} "question"  - Single query mode`);
        console.log(`  ${chalk.cyan("chat")}              - Interactive chat mode`);
        console.log(`  ${chalk.cyan("tools")}             - List available tools`);
        console.log();
        console.log(`Provider: ${chalk.yellow(config.provider)} | Model: ${chalk.yellow(config.model)}`);
      }
    }
  } finally {
    stopPythonServer(pythonServer);
  }
}

main().catch((err) => {
  console.error(chalk.red(`Fatal: ${err}`));
  process.exit(1);
});
