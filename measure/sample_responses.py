"""Capture one full reply per model per test message, with the exact prompt used.

Uses the same system prompt and user messages as measure_cost.py, and writes
measure/sample-responses.md.

Usage:
  ANTHROPIC_API_KEY=... measure/.venv/bin/python measure/sample_responses.py
"""
from __future__ import annotations

import datetime
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import core  # noqa: E402

MAX_TOKENS = 2048
DOT = {"GREEN": "🟢", "AMBER": "🟡", "RED": "🔴", None: "⚪"}


def fence(text: str) -> str:
    return f"````text\n{text.strip()}\n````"


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY in your environment first.", file=sys.stderr)
        return 2

    import anthropic

    prices = core.load_prices(core.REPO / "measure" / "prices.json")
    inputs = core.load_inputs(core.REPO / "demo" / "inputs.json")
    instructions = (core.REPO / "template" / "project-instructions.md").read_text()
    notes = (core.REPO / "demo" / "weekly-notes.md").read_text()
    client = anthropic.Anthropic()

    lines = [
        "# Sample responses",
        "",
        f"One reply from each model for each test message, captured {datetime.date.today().isoformat()} "
        "with `measure/sample_responses.py`. Every company, person and figure is made up.",
        "",
        "## How each reply was produced",
        "",
        "- **System prompt:** the contents of [`template/project-instructions.md`](../template/project-instructions.md), "
        "followed by the client's rules file wrapped as project knowledge, exactly as `core.build_system_prompt` builds it "
        "(see the first section below).",
        "- **User message:** the task, followed by the notes it refers to (shown under each message).",
        f"- **Settings:** Messages API, single turn, `max_tokens={MAX_TOKENS}`, default temperature. "
        "Replies vary from run to run; these are single samples.",
        "- **Not the same as claude.ai:** on stage, step 2 is a follow-up in the same chat as step 1. "
        "Here every message is sent on its own, with its notes pasted in.",
        "",
    ]

    total = 0.0
    shown_rules = set()
    for inp in inputs:
        rules = (core.REPO / "demo" / "clients" / f"{inp.client}.md").read_text()
        system = core.build_system_prompt(instructions, rules)
        user = core.build_user_message(inp, notes)
        if inp.client not in shown_rules:
            shown_rules.add(inp.client)
            lines += [
                f"## System prompt used for `{inp.client}`",
                "",
                "<details><summary>Show the full system prompt</summary>",
                "",
                fence(system),
                "",
                "</details>",
                "",
            ]
        kind = "Stage demo" if inp.stage else "Edge case (not shown on stage)"
        lines += [
            f"## `{inp.id}` · expected {DOT[inp.expected]} {inp.expected}",
            "",
            f"*{kind}.*",
            "",
            "**User message sent:**",
            "",
            fence(user),
            "",
        ]
        for model, price in prices["models"].items():
            response = client.messages.create(
                model=model,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text")
            verdict = core.parse_verdict(text)
            cost = core.cost_usd(response.usage.input_tokens, response.usage.output_tokens, price)
            total += cost
            mark = "✓" if verdict == inp.expected else "✗"
            print(f"{model}  {inp.id}: {verdict} (expected {inp.expected}) {mark}  ${cost:.5f}  stop={response.stop_reason}")
            lines += [
                f"### {price['label']} → {DOT[verdict]} {verdict} {mark}",
                "",
                f"`{model}` · {response.usage.input_tokens} input / {response.usage.output_tokens} output tokens · "
                f"${cost:.4f} · stop reason `{response.stop_reason}`",
                "",
                fence(text),
                "",
            ]

    out = core.REPO / "measure" / "sample-responses.md"
    out.write_text("\n".join(lines))
    print(f"\nWrote {out.relative_to(core.REPO)}. Total spend this run: ${total:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
