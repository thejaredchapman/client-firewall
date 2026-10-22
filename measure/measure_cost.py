"""Measure Client Firewall cost per check through the Anthropic API.

Recreates a Claude Project call: firewall instructions + the client's rules file
as the system prompt, one demo input as the user message.

Usage:
  ANTHROPIC_API_KEY=... measure/.venv/bin/python measure/measure_cost.py [--runs 3]
      [--models claude-haiku-5-5,claude-sonnet-5-5] [--stage-only]

Exits 1 if any verdict did not match the expected color.
"""
from __future__ import annotations

import argparse
import datetime
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import core  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--models", help="comma-separated model IDs (default: all in prices.json)")
    parser.add_argument("--stage-only", action="store_true", help="skip the test-only inputs")
    args = parser.parse_args(argv)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Set ANTHROPIC_API_KEY in your environment first.", file=sys.stderr)
        return 2

    import anthropic

    prices = core.load_prices(core.REPO / "measure" / "prices.json")
    models = args.models.split(",") if args.models else list(prices["models"])
    unknown = [m for m in models if m not in prices["models"]]
    if unknown:
        print(f"No prices for: {', '.join(unknown)}", file=sys.stderr)
        return 2

    inputs = core.load_inputs(core.REPO / "demo" / "inputs.json")
    if args.stage_only:
        inputs = [i for i in inputs if i.stage]
    instructions = (core.REPO / "template" / "project-instructions.md").read_text()
    notes = (core.REPO / "demo" / "weekly-notes.md").read_text()

    client = anthropic.Anthropic()
    results = []
    for model in models:
        price = prices["models"][model]
        for inp in inputs:
            rules = (core.REPO / "demo" / "clients" / f"{inp.client}.md").read_text()
            system = core.build_system_prompt(instructions, rules)
            user = core.build_user_message(inp, notes)
            for run in range(1, args.runs + 1):
                result = core.run_check(client, model, system, user, inp, run, price)
                results.append(result)
                mark = "✓" if result.match else "✗"
                print(f"{model}  {inp.id}  run {run}: {result.verdict} (expected {result.expected}) {mark}  ${result.cost_usd:.5f}")

    summary = core.summarize(results, prices, args.runs, datetime.date.today().isoformat())
    core.write_results_csv(results, core.REPO / "measure" / "results.csv")
    core.write_summary_json(summary, core.REPO / "measure" / "summary.json")
    print()
    print(core.format_table(summary))
    print(f"\nTotal spend this run: ${summary['total_spend_usd']:.4f}")
    return 0 if all(r.match for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
