"""Pure helpers for measuring Client Firewall: load data, build prompts."""
from __future__ import annotations

import csv
import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
VERDICTS = ("GREEN", "AMBER", "RED")


@dataclass
class CheckInput:
    id: str
    client: str
    notes: str  # "none", "all", or a section key such as "acme"
    task: str
    expected: str
    stage: bool


def load_inputs(path: Path) -> list[CheckInput]:
    inputs = [CheckInput(**row) for row in json.loads(Path(path).read_text())]
    for inp in inputs:
        if inp.expected not in VERDICTS:
            raise ValueError(f"{inp.id}: expected must be one of {VERDICTS}, got {inp.expected!r}")
    return inputs


def split_notes(notes_md: str) -> dict[str, str]:
    sections = {}
    for part in re.split(r"(?m)^(?=## )", notes_md):
        match = re.match(r"## (\S+)", part)
        if match:
            sections[match.group(1).lower()] = part.strip()
    return sections


def build_user_message(inp: CheckInput, notes_md: str) -> str:
    if inp.notes == "none":
        return inp.task
    body = notes_md.strip() if inp.notes == "all" else split_notes(notes_md)[inp.notes]
    return f"{inp.task}\n\n{body}"


def build_system_prompt(instructions: str, rules: str) -> str:
    return (
        f"{instructions.strip()}\n\n"
        f'<project_knowledge file="client-rules.md">\n{rules.strip()}\n</project_knowledge>\n'
    )

VERDICT_RE = re.compile(r"Firewall:\s*(GREEN|AMBER|RED)\b")


@dataclass
class CallResult:
    model: str
    input_id: str
    run: int
    verdict: Optional[str]
    expected: str
    match: bool
    input_tokens: int
    output_tokens: int
    latency_s: float
    cost_usd: float


def parse_verdict(text: str) -> Optional[str]:
    for line in text.splitlines():
        if line.strip():
            match = VERDICT_RE.search(line)
            return match.group(1) if match else None
    return None


def cost_usd(input_tokens: int, output_tokens: int, price: dict) -> float:
    return (input_tokens * price["input_per_mtok"] + output_tokens * price["output_per_mtok"]) / 1_000_000


def load_prices(path: Path) -> dict:
    prices = json.loads(Path(path).read_text())
    if not prices.get("source_url") or not prices.get("checked"):
        raise ValueError("prices.json needs source_url and checked")
    for model, price in prices["models"].items():
        for key in ("input_per_mtok", "output_per_mtok"):
            if not isinstance(price.get(key), (int, float)) or price[key] <= 0:
                raise ValueError(f"{model}: {key} must be a positive number from the pricing page")
    return prices


def run_check(client, model: str, system: str, user: str, inp: CheckInput, run: int,
              price: dict, max_tokens: int = 1024) -> CallResult:
    start = time.perf_counter()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    latency = time.perf_counter() - start
    text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
    verdict = parse_verdict(text)
    usage = response.usage
    return CallResult(
        model=model,
        input_id=inp.id,
        run=run,
        verdict=verdict,
        expected=inp.expected,
        match=verdict == inp.expected,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        latency_s=round(latency, 2),
        cost_usd=cost_usd(usage.input_tokens, usage.output_tokens, price),
    )


def summarize(results: list[CallResult], prices: dict, runs: int, generated: str) -> dict:
    models = []
    for model in dict.fromkeys(r.model for r in results):
        rows = [r for r in results if r.model == model]
        models.append({
            "model": model,
            "label": prices["models"][model]["label"],
            "checks": len(rows),
            "correct": sum(r.match for r in rows),
            "avg_cost_usd": round(sum(r.cost_usd for r in rows) / len(rows), 6),
            "avg_latency_s": round(sum(r.latency_s for r in rows) / len(rows), 2),
        })
    return {
        "generated": generated,
        "prices_source": prices["source_url"],
        "prices_checked": prices["checked"],
        "runs": runs,
        "models": models,
        "total_spend_usd": round(sum(r.cost_usd for r in results), 6),
    }


def write_results_csv(results: list[CallResult], path: Path) -> None:
    fields = list(CallResult.__dataclass_fields__)
    with Path(path).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))


def write_summary_json(summary: dict, path: Path) -> None:
    Path(path).write_text(json.dumps(summary, indent=2) + "\n")


def format_table(summary: dict) -> str:
    lines = ["| Model | Correct | Avg cost per check | Avg latency |", "|---|---|---|---|"]
    for m in summary["models"]:
        lines.append(f"| {m['label']} | {m['correct']}/{m['checks']} | ${m['avg_cost_usd']:.5f} | {m['avg_latency_s']}s |")
    return "\n".join(lines)
