import csv
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import runner


class FakeClient:
    def __init__(self):
        self.calls = []

    def chat(self, messages, tools=None, options=None, keep_alive=None):
        self.calls.append({"messages": messages, "options": options, "keep_alive": keep_alive, "tools": tools})
        prompt = messages[1]["content"]
        # deterministic token counts based on content/language marker
        in_tok = 10 + len(prompt)
        out_tok = 5
        lang = "en"
        if any('\u0980' <= ch <= '\u09FF' for ch in prompt):
            out_tok = 7
            lang = "bn"
        return {
            "prompt_eval_count": in_tok,
            "eval_count": out_tok,
            "done_reason": "stop",
            "message": {"content": f"out-{lang}"},
        }


class TestRunner(unittest.TestCase):
    def _write_dataset(self, path, rows):
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id", "category", "english", "bangla"], delimiter="\t")
            w.writeheader()
            for r in rows:
                w.writerow(r)

    def test_same_settings_for_both_languages_and_columns(self):
        with tempfile.TemporaryDirectory() as td:
            dpath = os.path.join(td, "dataset.tsv")
            out = os.path.join(td, "results.csv")
            self._write_dataset(dpath, [
                {"id": "1", "category": "question", "english": "Hello?", "bangla": "হ্যালো?"},
                {"id": "2", "category": "instruction", "english": "Do it.", "bangla": "এটা করো।"},
            ])
            fake = FakeClient()
            runner.run(dataset_path=dpath, out_path=out, client=fake, temperature=0, seed=42, num_predict=256)
            # 2 pairs * 2 languages = 4 calls
            self.assertEqual(len(fake.calls), 4)
            for c in fake.calls:
                self.assertEqual(c["keep_alive"], 0)
                self.assertEqual(c["options"]["temperature"], 0)
                self.assertEqual(c["options"]["seed"], 42)
                self.assertEqual(c["options"]["num_predict"], 256)
                self.assertEqual(c["messages"][0]["content"], __import__('counter').FIXED_SYSTEM_PROMPT)

            with open(out, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, runner.RESULT_COLUMNS)
                rows = list(reader)
            self.assertEqual(len(rows), 4)
            langs = [(r["id"], r["language"]) for r in rows]
            self.assertEqual(langs, [("1","english"),("1","bangla"),("2","english"),("2","bangla")])

    def test_resume_works(self):
        with tempfile.TemporaryDirectory() as td:
            dpath = os.path.join(td, "dataset.tsv")
            out = os.path.join(td, "results.csv")
            self._write_dataset(dpath, [
                {"id": "1", "category": "question", "english": "Hello?", "bangla": "হ্যালো?"},
                {"id": "2", "category": "instruction", "english": "Do it.", "bangla": "এটা করো।"},
            ])
            fake1 = FakeClient()
            runner.run(dataset_path=dpath, out_path=out, client=fake1, limit_pairs=1)
            self.assertEqual(len(fake1.calls), 2)  # first pair only
            fake2 = FakeClient()
            runner.run(dataset_path=dpath, out_path=out, client=fake2)  # resume all
            # should only do remaining 2
            self.assertEqual(len(fake2.calls), 2)
            with open(out, "r", encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 4)


if __name__ == "__main__":
    unittest.main()
