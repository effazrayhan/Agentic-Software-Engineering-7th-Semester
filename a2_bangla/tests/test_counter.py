import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import counter


class FakeBackend:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def chat(self, messages, tools=None, options=None, keep_alive=None):
        self.calls.append({"messages": messages, "tools": tools, "options": options, "keep_alive": keep_alive})
        if not self.responses:
            raise RuntimeError("no more fake responses")
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


class TestCounter(unittest.TestCase):
    def test_tokens_read_from_prompt_eval_and_eval_count(self):
        fake = FakeBackend([
            {"prompt_eval_count": 12, "eval_count": 34, "done_reason": "stop", "message": {"content": "hello"}}
        ])
        res = counter.count_tokens(fake, "test prompt")
        self.assertEqual(res["input_tokens"], 12)
        self.assertEqual(res["output_tokens"], 34)
        self.assertEqual(res["done_reason"], "stop")
        self.assertEqual(res["output_text"], "hello")
        self.assertIn("latency_s", res)
        # keep_alive forced to 0 and fixed system prompt used
        self.assertEqual(fake.calls[0]["keep_alive"], 0)
        self.assertEqual(fake.calls[0]["messages"][0]["role"], "system")
        self.assertEqual(fake.calls[0]["messages"][0]["content"], counter.FIXED_SYSTEM_PROMPT)

    def test_cost_arithmetic_known_numbers(self):
        # 1,000,000 in + 1,000,000 out = $0.75
        self.assertAlmostEqual(counter.cost_usd(1_000_000, 1_000_000), 0.75, places=10)
        self.assertAlmostEqual(counter.cost_usd(0, 0), 0.0, places=10)
        self.assertAlmostEqual(counter.cost_usd(100, 200), 100/1e6*0.15 + 200/1e6*0.60, places=12)

    def test_baseline_uses_tiny_prompt_hi(self):
        fake = FakeBackend([
            {"prompt_eval_count": 5, "eval_count": 1, "done_reason": "stop", "message": {"content": "hi"}}
        ])
        res = counter.measure_baseline(fake)
        self.assertEqual(res["input_tokens"], 5)
        self.assertEqual(fake.calls[0]["messages"][1]["content"], "hi")

    def test_cache_check_flags_mismatch(self):
        fake = FakeBackend([
            {"prompt_eval_count": 10, "eval_count": 1, "done_reason": "stop", "message": {"content": "a"}},
            {"prompt_eval_count": 11, "eval_count": 1, "done_reason": "stop", "message": {"content": "b"}},
        ])
        ok, a, b, details = counter.check_cache(fake, prompt="hi")
        self.assertFalse(ok)
        self.assertEqual(a, 10)
        self.assertEqual(b, 11)
        self.assertEqual(details.get("flag"), "mismatch")
        self.assertTrue(all(c["keep_alive"] == 0 for c in fake.calls))

    def test_cache_check_ok_when_identical(self):
        fake = FakeBackend([
            {"prompt_eval_count": 10, "eval_count": 1, "done_reason": "stop", "message": {"content": "a"}},
            {"prompt_eval_count": 10, "eval_count": 1, "done_reason": "stop", "message": {"content": "b"}},
        ])
        ok, a, b, details = counter.check_cache(fake, prompt="hi")
        self.assertTrue(ok)
        self.assertEqual(a, 10)
        self.assertEqual(b, 10)

    def test_missing_counts_flagged(self):
        fake = FakeBackend([
            {"done_reason": "stop", "message": {"content": "x"}}  # missing counts
        ])
        res = counter.count_tokens(fake, "p")
        self.assertTrue(res.get("missing_counts"))

    def test_cache_check_flags_missing_counts(self):
        fake = FakeBackend([
            {"prompt_eval_count": 10, "eval_count": 1, "done_reason": "stop", "message": {"content": "a"}},
            {"eval_count": 1, "done_reason": "stop", "message": {"content": "b"}},  # missing prompt_eval_count
        ])
        ok, a, b, details = counter.check_cache(fake, prompt="hi")
        self.assertFalse(ok)
        self.assertEqual(details.get("flag"), "missing_counts")


if __name__ == "__main__":
    unittest.main()
