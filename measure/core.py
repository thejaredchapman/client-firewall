"""Pure helpers for measuring Client Firewall: load data, build prompts."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

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
