/**
 * CLI interface for OpenFR TypeScript Agent.
 *
 * Renders plan-execute events to the terminal using chalk + ora.
 */

import chalk from "chalk";
import ora, { type Ora } from "ora";
import readline from "node:readline";
import type { PlanExecuteEvent } from "./plan-execute.js";
import type { ToolMeta } from "./tool-discovery.js";

// ---------------------------------------------------------------------------
// Tool display name lookup (populated from Python server metadata)
// ---------------------------------------------------------------------------

let _toolLabels: Map<string, string> = new Map();

export function setToolLabels(tools: ToolMeta[]): void {
  _toolLabels = new Map(tools.map((t) => [t.name, t.label]));
}

function toolLabel(name: string): string {
  return _toolLabels.get(name) ?? name;
}

// ---------------------------------------------------------------------------
// Event renderer
// ---------------------------------------------------------------------------

export function createEventRenderer(): {
  onEvent: (event: PlanExecuteEvent) => void;
  cleanup: () => void;
} {
  let spinner: Ora | null = null;

  function stopSpinner(): void {
    if (spinner) {
      spinner.stop();
      spinner = null;
    }
  }

  function onEvent(event: PlanExecuteEvent): void {
    switch (event.type) {
      case "planning":
        spinner = ora({ text: chalk.cyan("正在规划研究步骤..."), spinner: "dots" }).start();
        break;

      case "plan":
        stopSpinner();
        console.log(chalk.bold.blue("\n研究计划:"));
        for (let i = 0; i < event.steps.length; i++) {
          console.log(chalk.cyan(`  ${i + 1}. ${event.steps[i].goal}`));
        }
        console.log();
        break;

      case "step_start":
        spinner = ora({
          text: chalk.cyan(`步骤 ${event.stepIndex + 1}: ${event.goal}`),
          spinner: "dots",
        }).start();
        break;

      case "tool_start":
        stopSpinner();
        spinner = ora({
          text: chalk.yellow(`  调用工具: ${toolLabel(event.toolName)}`),
          spinner: "dots",
        }).start();
        break;

      case "tool_end":
        if (spinner) {
          spinner.succeed(chalk.green(`  ${toolLabel(event.toolName)} 完成`));
          spinner = null;
        }
        break;

      case "tool_warning":
        stopSpinner();
        console.log(chalk.yellow(`  ! ${event.message}`));
        break;

      case "step_end":
        stopSpinner();
        break;

      case "synthesizing":
        spinner = ora({ text: chalk.cyan("正在综合分析..."), spinner: "dots" }).start();
        break;

      case "text_delta":
        stopSpinner();
        process.stdout.write(event.delta);
        break;

      case "answer":
        stopSpinner();
        console.log(chalk.bold.green("\n===== 分析结果 =====\n"));
        console.log(event.content);
        console.log(chalk.bold.green("\n====================\n"));
        break;

      case "error":
        stopSpinner();
        console.error(chalk.red(`Error: ${event.message}`));
        break;
    }
  }

  function cleanup(): void {
    stopSpinner();
  }

  return { onEvent, cleanup };
}

// ---------------------------------------------------------------------------
// Interactive chat loop
// ---------------------------------------------------------------------------

export async function interactiveChat(
  runQuery: (query: string) => Promise<void>,
): Promise<void> {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  console.log(chalk.bold.blue("OpenFR 金融研究助手 (交互模式)"));
  console.log(chalk.dim("输入问题开始研究，输入 exit/quit 退出\n"));

  const prompt = (): void => {
    rl.question(chalk.cyan("? "), async (input) => {
      const trimmed = input.trim();
      if (!trimmed) {
        prompt();
        return;
      }
      if (trimmed === "exit" || trimmed === "quit") {
        console.log(chalk.dim("再见!"));
        rl.close();
        return;
      }

      try {
        await runQuery(trimmed);
      } catch (err) {
        console.error(chalk.red(`Error: ${err}`));
      }
      prompt();
    });
  };

  prompt();

  return new Promise((resolve) => {
    rl.on("close", resolve);
  });
}

// ---------------------------------------------------------------------------
// Tool listing
// ---------------------------------------------------------------------------

export function printTools(tools: ToolMeta[]): void {
  const categories: Record<string, ToolMeta[]> = {};
  for (const t of tools) {
    const cat = t.category || "other";
    if (!categories[cat]) categories[cat] = [];
    categories[cat].push(t);
  }

  const categoryNames: Record<string, string> = {
    stock: "股票数据 (A股)",
    stock_hk: "股票数据 (港股)",
    fund: "基金数据",
    futures: "期货数据",
    index: "指数数据",
    macro: "宏观数据",
    other: "其他",
  };

  console.log(chalk.bold.blue("\n可用工具列表:\n"));

  for (const [cat, catTools] of Object.entries(categories)) {
    console.log(chalk.bold.cyan(`  ${categoryNames[cat] ?? cat}:`));
    for (const t of catTools) {
      const desc = t.description.split("\n")[0];
      console.log(`    ${chalk.yellow(t.name)} - ${t.label} - ${chalk.dim(desc)}`);
    }
    console.log();
  }

  console.log(chalk.dim(`共 ${tools.length} 个工具\n`));
}
