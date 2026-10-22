import json

import pytest

import core
from core import REPO, CheckInput, build_system_prompt, build_user_message, load_inputs, split_notes

INSTRUCTIONS = (REPO / "template" / "project-instructions.md").read_text()
TEMPLATE = (REPO / "template" / "client-rules.template.md").read_text()
NOTES = (REPO / "demo" / "weekly-notes.md").read_text()
HEADINGS = [
    "## Protected (this client's sensitive details)",
    "## Other clients (flag if these appear)",
    "## Never share anywhere",
]


def test_instructions_define_all_three_verdicts_and_the_rules_file():
    for verdict in core.VERDICTS:
        assert f"Firewall: {verdict}" in INSTRUCTIONS
    assert "client-rules.md" in INSTRUCTIONS


def test_template_and_demo_rules_share_the_same_headings():
    files = [TEMPLATE] + [p.read_text() for p in (REPO / "demo" / "clients").glob("*.md")]
    assert len(files) == 4
    for text in files:
        assert text.startswith("# Client: ")
        for heading in HEADINGS:
            assert heading in text


def test_acme_rules_list_both_other_clients():
    acme = (REPO / "demo" / "clients" / "acme-robotics.md").read_text()
    other = acme.split("## Other clients")[1].split("## Never share")[0]
    assert "Bluefin" in other and "Corvid" in other


def test_split_notes_returns_one_section_per_client():
    sections = split_notes(NOTES)
    assert sorted(sections) == ["acme", "bluefin", "corvid"]
    assert sections["acme"].startswith("## Acme Robotics")
    assert "Bluefin" not in sections["acme"]


def test_inputs_reference_existing_clients_and_notes():
    inputs = load_inputs(REPO / "demo" / "inputs.json")
    for inp in inputs:
        assert (REPO / "demo" / "clients" / f"{inp.client}.md").exists()
        build_user_message(inp, NOTES)  # raises if a notes key is wrong


def test_stage_inputs_are_green_amber_red_in_order():
    stage = [i for i in load_inputs(REPO / "demo" / "inputs.json") if i.stage]
    assert [i.expected for i in stage] == ["GREEN", "AMBER", "RED"]


def test_only_the_red_stage_message_contains_another_client():
    stage = [i for i in load_inputs(REPO / "demo" / "inputs.json") if i.stage]
    messages = [build_user_message(i, NOTES) for i in stage]
    assert "Bluefin" not in messages[0] and "Bluefin" not in messages[1]
    assert "Bluefin" in messages[2]


def test_build_user_message_variants():
    none = CheckInput("x", "acme-robotics", "none", "Do it.", "GREEN", False)
    assert build_user_message(none, NOTES) == "Do it."
    allnotes = CheckInput("x", "acme-robotics", "all", "Do it.", "RED", False)
    assert build_user_message(allnotes, NOTES) == "Do it.\n\n" + NOTES.strip()
    bad = CheckInput("x", "acme-robotics", "zeta", "Do it.", "RED", False)
    with pytest.raises(KeyError):
        build_user_message(bad, NOTES)


def test_load_inputs_rejects_unknown_verdict(tmp_path):
    path = tmp_path / "inputs.json"
    path.write_text(json.dumps([{"id": "a", "client": "c", "notes": "none", "task": "t",
                                 "expected": "BLUE", "stage": False}]))
    with pytest.raises(ValueError):
        load_inputs(path)


def test_system_prompt_wraps_rules_as_project_knowledge():
    prompt = build_system_prompt("INSTR\n", "# Client: X\n")
    assert prompt.startswith("INSTR\n\n<project_knowledge file=\"client-rules.md\">\n# Client: X\n")
    assert prompt.rstrip().endswith("</project_knowledge>")
