import fs from "node:fs";
import path from "node:path";

export type Verdict = "GREEN" | "AMBER" | "RED";

export interface DemoInput {
  id: string;
  client: string;
  notes: string;
  task: string;
  expected: Verdict;
  stage: boolean;
}

export interface ModelSummary {
  model: string;
  label: string;
  checks: number;
  correct: number;
  avg_cost_usd: number;
  avg_latency_s: number;
}

export interface Summary {
  generated: string;
  prices_source: string;
  prices_checked: string;
  runs: number;
  models: ModelSummary[];
  total_spend_usd: number;
}

// Mirrors split_notes / build_user_message in measure/core.py.
export function splitNotes(md: string): Record<string, string> {
  const sections: Record<string, string> = {};
  for (const part of md.split(/^(?=## )/m)) {
    const match = part.match(/^## (\S+)/);
    if (match) sections[match[1].toLowerCase()] = part.trim();
  }
  return sections;
}

export function buildMessage(input: DemoInput, notesMd: string): string {
  if (input.notes === "none") return input.task;
  const body = input.notes === "all" ? notesMd.trim() : splitNotes(notesMd)[input.notes];
  if (body === undefined) throw new Error(`No notes section "${input.notes}"`);
  return `${input.task}\n\n${body}`;
}

export function formatUsd(n: number): string {
  return n < 0.01 ? `$${n.toFixed(4)}` : `$${n.toFixed(2)}`;
}

export function formatPerCheck(n: number): string {
  return `$${n.toFixed(4)}`;
}

export function readContent(dir = path.join(process.cwd(), "content")) {
  const read = (name: string) => fs.readFileSync(path.join(dir, name), "utf8");
  const notes = read("weekly-notes.md");
  const inputs = JSON.parse(read("inputs.json")) as DemoInput[];
  const summaryPath = path.join(dir, "summary.json");
  return {
    instructions: read("project-instructions.md"),
    rulesTemplate: read("client-rules.template.md"),
    acmeRules: read("acme-robotics.md"),
    notes,
    stageSteps: inputs.filter((i) => i.stage).map((input) => ({ input, message: buildMessage(input, notes) })),
    summary: fs.existsSync(summaryPath) ? (JSON.parse(fs.readFileSync(summaryPath, "utf8")) as Summary) : null,
  };
}
