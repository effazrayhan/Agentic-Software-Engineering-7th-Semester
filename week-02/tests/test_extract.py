import json
import unittest

from agentlab.lm import Ledger
from extract import SYSTEM_PROMPT, parse_reply, run_extraction, summarize
from notices import load_corpus

VALID = {
    "schema_version": "1.0",
    "notice_id": "N001",
    "domain": "example.com",
    "notice_type": "renewal",
    "severity": "info",
    "due_date": "2026-03-01",
    "summary": "Renewal is due.",
}


class FakeBackend:
    def __init__(self, text=None):
        self.text = text
        self.calls = []

    def chat(self, system, prompt, schema=None):
        self.calls.append({"system": system, "prompt": prompt, "schema": schema})
        text = self.text if self.text is not None else json.dumps(VALID)
        return {"text": text, "input_tokens": 10, "output_tokens": 5}


class GrammarOnlyBackend(FakeBackend):
    def chat(self, system, prompt, schema=None):
        super().chat(system, prompt, schema)
        return {
            "text": json.dumps(VALID) if schema else "not json",
            "input_tokens": 10,
            "output_tokens": 5,
        }


class TestExtract(unittest.TestCase):
    def setUp(self):
        self.notices = [{"id": "N001", "text": "Renew example.com by 2026-03-01."}]

    def test_runs_per_notice_per_approach(self):
        backend = FakeBackend()
        rows = run_extraction(self.notices, backend, Ledger(), runs=3)
        self.assertEqual(len(rows), 6)
        self.assertEqual(
            {(r["approach"], r["run"]) for r in rows},
            {(a, n) for a in ("prompt_only", "grammar") for n in (1, 2, 3)},
        )

    def test_schema_only_passed_to_grammar(self):
        backend = FakeBackend()
        run_extraction(self.notices, backend, Ledger(), runs=3)
        with_schema = [c for c in backend.calls if c["schema"]]
        without = [c for c in backend.calls if not c["schema"]]
        self.assertEqual((len(with_schema), len(without)), (3, 3))
        self.assertEqual(len({c["system"] for c in backend.calls}), 1)
        self.assertEqual(len({c["prompt"] for c in backend.calls}), 1)
        self.assertEqual(backend.calls[0]["system"], SYSTEM_PROMPT)

    def test_ledger_prices_every_call(self):
        ledger = Ledger()
        run_extraction(self.notices, FakeBackend(), ledger, runs=3)
        self.assertEqual(len(ledger.entries), 6)
        self.assertAlmostEqual(ledger.total_cost, 6 * (10 * 0.15 + 5 * 0.60) / 1_000_000)

    def test_result_columns(self):
        row = run_extraction(self.notices, FakeBackend(), Ledger(), runs=1)[0]
        self.assertEqual(
            set(row),
            {
                "notice_id",
                "approach",
                "run",
                "output",
                "valid",
                "input_tokens",
                "output_tokens",
                "cost_usd",
            },
        )

    def test_invalid_output_is_recorded_not_raised(self):
        rows = run_extraction(
            self.notices, FakeBackend("not json"), Ledger(), runs=3
        )
        self.assertTrue(all(not r["valid"] for r in rows))
        self.assertTrue(all(r["output"] == "not json" for r in rows))

    def test_fenced_json_is_accepted(self):
        text = "```json\n" + json.dumps(VALID) + "\n```"
        self.assertTrue(parse_reply(text))

    def test_summarize_compares_approaches(self):
        rows = run_extraction(self.notices, GrammarOnlyBackend(), Ledger(), runs=3)
        summary = summarize(rows)
        self.assertEqual(summary["prompt_only"]["valid"], 0)
        self.assertEqual(summary["grammar"]["valid"], 3)
        self.assertAlmostEqual(
            summary["grammar"]["cost_usd"], 3 * (10 * 0.15 + 5 * 0.60) / 1_000_000
        )

    def test_full_corpus_is_300_calls(self):
        rows = run_extraction(
            load_corpus()["notices"], FakeBackend(), Ledger(), runs=3
        )
        self.assertEqual(len(rows), 300)


if __name__ == "__main__":
    unittest.main()
