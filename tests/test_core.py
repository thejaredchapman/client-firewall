import csv
import json
from types import SimpleNamespace

import pytest

from core import (CallResult, CheckInput, cost_usd, format_table, load_prices, parse_verdict,
                  run_check, summarize, write_results_csv, write_summary_json)

PRICE = {"label": "Test", "input_per_mtok": 3.0, "output_per_mtok": 15.0}
PRICES = {"source_url": "https://example.test/pricing", "checked": "2026-10-23",
          "models": {"m1": PRICE}}
INP = CheckInput("step3-board", "acme-robotics", "all", "t", "RED", True)


@pytest.mark.parametrize("text,expected", [
    ("🔴 Firewall: RED\nThis contains Bluefin details.", "RED"),
    ("\n\nFirewall: AMBER\n- item", "AMBER"),
    ("🟢 Firewall: GREEN", "GREEN"),
    ("Sure! Here is the draft.\nFirewall: GREEN", None),
    ("", None),
])
def test_parse_verdict_reads_first_non_empty_line_only(text, expected):
    assert parse_verdict(text) == expected


def test_cost_usd_uses_per_million_prices():
    assert cost_usd(1_000_000, 0, PRICE) == pytest.approx(3.0)
    assert cost_usd(2000, 500, PRICE) == pytest.approx(0.0135)


def test_load_prices_rejects_zero_or_missing_values(tmp_path):
    path = tmp_path / "prices.json"
    path.write_text(json.dumps({**PRICES, "models": {"m1": {**PRICE, "input_per_mtok": 0}}}))
    with pytest.raises(ValueError):
        load_prices(path)
    path.write_text(json.dumps({**PRICES, "checked": ""}))
    with pytest.raises(ValueError):
        load_prices(path)
    path.write_text(json.dumps(PRICES))
    assert load_prices(path)["models"]["m1"]["label"] == "Test"


class FakeMessages:
    def __init__(self, text):
        self.text = text
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=self.text)],
            usage=SimpleNamespace(input_tokens=2000, output_tokens=500),
        )


def test_run_check_sends_system_and_user_and_scores_the_verdict():
    messages = FakeMessages("🔴 Firewall: RED\nBluefin details found.")
    client = SimpleNamespace(messages=messages)
    result = run_check(client, "m1", "SYS", "USER", INP, 2, PRICE)
    call = messages.calls[0]
    assert call["model"] == "m1" and call["system"] == "SYS"
    assert call["messages"] == [{"role": "user", "content": "USER"}]
    assert (result.verdict, result.match, result.run) == ("RED", True, 2)
    assert result.cost_usd == pytest.approx(0.0135)
    assert result.latency_s >= 0


def _result(model, match, cost, latency):
    return CallResult(model, "i", 1, "RED" if match else "GREEN", "RED", match, 10, 10, latency, cost)


def test_summarize_rolls_up_per_model_and_total():
    results = [_result("m1", True, 0.01, 1.0), _result("m1", False, 0.03, 3.0)]
    summary = summarize(results, PRICES, 2, "2026-10-23")
    assert summary["models"] == [{"model": "m1", "label": "Test", "checks": 2, "correct": 1,
                                  "avg_cost_usd": 0.02, "avg_latency_s": 2.0}]
    assert summary["total_spend_usd"] == pytest.approx(0.04)
    assert summary["prices_source"] == PRICES["source_url"]
    assert "| Test | 1/2 |" in format_table(summary)


def test_writers_produce_csv_and_json(tmp_path):
    results = [_result("m1", True, 0.01, 1.0)]
    write_results_csv(results, tmp_path / "r.csv")
    rows = list(csv.DictReader((tmp_path / "r.csv").open()))
    assert rows[0]["model"] == "m1" and rows[0]["match"] == "True"
    write_summary_json({"a": 1}, tmp_path / "s.json")
    assert json.loads((tmp_path / "s.json").read_text()) == {"a": 1}
