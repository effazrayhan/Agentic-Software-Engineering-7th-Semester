import json
import os
import tempfile
import unittest

import build_db
import eval as eval_mod


class TestEval(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "data.db")
        build_db.build_database(self.db_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_compute_expected_uses_expected_sql(self):
        questions = [
            {
                "id": "q1",
                "question": "How many orders are there?",
                "type": "simple",
                "expected": None,
                "expected_sql": "SELECT COUNT(*) FROM orders",
            },
            {
                "id": "q2",
                "question": "Unanswerable example",
                "type": "unanswerable",
                "expected": "CANNOT_ANSWER",
                "expected_sql": None,
            },
        ]
        # support function or in-place update
        if hasattr(eval_mod, "compute_expected"):
            out = eval_mod.compute_expected(questions, self.db_path)
            qs = out if out is not None else questions
        elif hasattr(eval_mod, "compute_expected_answers"):
            out = eval_mod.compute_expected_answers(questions, self.db_path)
            qs = out if out is not None else questions
        else:
            self.fail("eval must expose compute_expected(questions, db_path)")
        by_id = {q["id"]: q for q in qs}
        self.assertEqual(by_id["q1"]["expected"], 240)
        self.assertEqual(by_id["q2"]["expected"], "CANNOT_ANSWER")

    def test_numeric_tolerance_and_cannot_answer_matching(self):
        self.assertTrue(eval_mod.is_correct(10.0, "10", tol=1e-6))
        self.assertTrue(eval_mod.is_correct(10.0, "10.0000005", tol=1e-5))
        self.assertFalse(eval_mod.is_correct(10.0, "10.1", tol=1e-3))
        self.assertTrue(eval_mod.is_correct("CANNOT_ANSWER", "CANNOT_ANSWER: not in db"))
        self.assertTrue(eval_mod.is_correct("CANNOT_ANSWER", "  cannot_answer - missing "))
        self.assertFalse(eval_mod.is_correct("CANNOT_ANSWER", "42"))
        self.assertFalse(eval_mod.is_correct(5, "CANNOT_ANSWER"))

    def test_pass_at_1_and_pass_pow_3_from_fake_results(self):
        # 3 questions, 3 trials each
        # q1: all correct -> contributes 1 to pass^3, 1.0 avg
        # q2: 2 correct, 1 wrong -> contributes 0 to pass^3, 2/3 avg
        # q3: all wrong -> 0, 0
        results = []
        def rec(qid, trial, correct):
            results.append({"id": qid, "question_id": qid, "trial": trial, "correct": correct, "status": "ok"})
        for t in (1, 2, 3):
            rec("q1", t, True)
        rec("q2", 1, True); rec("q2", 2, True); rec("q2", 3, False)
        for t in (1, 2, 3):
            rec("q3", t, False)

        path = os.path.join(self.tmp.name, "fake.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r) + "\n")

        if hasattr(eval_mod, "compute_metrics"):
            metrics = eval_mod.compute_metrics(path)
        elif hasattr(eval_mod, "compute_pass_metrics"):
            metrics = eval_mod.compute_pass_metrics(path)
        elif hasattr(eval_mod, "summarize_results"):
            metrics = eval_mod.summarize_results(path)
        else:
            self.fail("eval must expose compute_metrics(results_path)")

        # accept common key names
        pass1 = metrics.get("pass@1", metrics.get("pass_at_1", metrics.get("pass1")))
        pass3 = metrics.get("pass^3", metrics.get("pass_pow_3", metrics.get("pass3", metrics.get("pass_all_3"))))
        self.assertIsNotNone(pass1)
        self.assertIsNotNone(pass3)
        self.assertAlmostEqual(float(pass1), (1.0 + 2/3 + 0.0) / 3.0, places=6)
        self.assertAlmostEqual(float(pass3), 1.0 / 3.0, places=6)


if __name__ == "__main__":
    unittest.main()
