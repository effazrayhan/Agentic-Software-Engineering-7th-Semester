import csv
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import analyze


class TestAnalyze(unittest.TestCase):
    def _write_results(self, path):
        # small fake results.csv with hand-computed ratios
        # pair 1: EN in=10,out=10,cost=10/1e6*0.15+10/1e6*0.60=7.5e-6; BN in=20,out=20,cost=15e-6 => input ratio 2, output 2, total 2
        # pair 2: EN in=10,out=20,cost=1.5e-6+12e-6=13.5e-6; BN in=10,out=40,cost=1.5e-6+24e-6=25.5e-6 => input 1, output 2, total 25.5/13.5=1.888...
        rows = [
            {"id":"1","language":"english","prompt":"p","output":"o","input_tokens":"10","output_tokens":"10","cost_usd":"0.0000075","latency_s":"1.0","done_reason":"stop"},
            {"id":"1","language":"bangla","prompt":"p","output":"o","input_tokens":"20","output_tokens":"20","cost_usd":"0.0000150","latency_s":"1.2","done_reason":"stop"},
            {"id":"2","language":"english","prompt":"p","output":"o","input_tokens":"10","output_tokens":"20","cost_usd":"0.0000135","latency_s":"0.8","done_reason":"stop"},
            {"id":"2","language":"bangla","prompt":"p","output":"o","input_tokens":"10","output_tokens":"40","cost_usd":"0.0000255","latency_s":"0.9","done_reason":"stop"},
        ]
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            for r in rows:
                w.writerow(r)

    def _write_dataset(self, path):
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id","category","english","bangla"], delimiter="\t")
            w.writeheader()
            w.writerow({"id":"1","category":"question","english":"a","bangla":"b"})
            w.writerow({"id":"2","category":"long","english":"c","bangla":"d"})

    def test_per_pair_ratios_totals_and_stats(self):
        with tempfile.TemporaryDirectory() as td:
            rpath = os.path.join(td, "results.csv")
            dpath = os.path.join(td, "dataset.tsv")
            cout = os.path.join(td, "comparison.csv")
            self._write_results(rpath)
            self._write_dataset(dpath)
            summary, comp = analyze.analyze(rpath, dpath, cout, os.path.join(td, "chart.png"))
            self.assertEqual(len(comp), 2)
            by_id = {r["id"]: r for r in comp}
            self.assertAlmostEqual(by_id["1"]["input_ratio"], 2.0)
            self.assertAlmostEqual(by_id["1"]["output_ratio"], 2.0)
            self.assertAlmostEqual(by_id["1"]["total_cost_ratio"], 2.0)
            self.assertAlmostEqual(by_id["2"]["input_ratio"], 1.0)
            self.assertAlmostEqual(by_id["2"]["output_ratio"], 2.0)
            self.assertAlmostEqual(by_id["2"]["total_cost_ratio"], 25.5/13.5)

            totals = summary["totals"]
            self.assertEqual(totals["english_input_tokens"], 20)
            self.assertEqual(totals["bangla_input_tokens"], 30)
            self.assertEqual(totals["english_output_tokens"], 30)
            self.assertEqual(totals["bangla_output_tokens"], 60)
            self.assertAlmostEqual(summary["input_cost_ratio_total"], 30/20)
            self.assertAlmostEqual(summary["total_cost_ratio_total"], (15.0+25.5)/(7.5+13.5) / 1e6 * 1e6, places=9)

            st = summary["per_pair_total_cost_ratio"]
            self.assertAlmostEqual(st["min"], min(2.0, 25.5/13.5))
            self.assertAlmostEqual(st["max"], max(2.0, 25.5/13.5))
            self.assertAlmostEqual(st["mean"], (2.0 + 25.5/13.5)/2)

    def test_bootstrap_interval_deterministic_and_brackets_mean(self):
        with tempfile.TemporaryDirectory() as td:
            rpath = os.path.join(td, "results.csv")
            dpath = os.path.join(td, "dataset.tsv")
            cout = os.path.join(td, "comparison.csv")
            self._write_results(rpath)
            self._write_dataset(dpath)
            s1, _ = analyze.analyze(rpath, dpath, cout, os.path.join(td, "chart1.png"))
            s2, _ = analyze.analyze(rpath, dpath, cout, os.path.join(td, "chart2.png"))
            ci1 = (s1["per_pair_total_cost_ratio"]["bootstrap_95ci_low"], s1["per_pair_total_cost_ratio"]["bootstrap_95ci_high"])
            ci2 = (s2["per_pair_total_cost_ratio"]["bootstrap_95ci_low"], s2["per_pair_total_cost_ratio"]["bootstrap_95ci_high"])
            self.assertEqual(ci1, ci2)  # deterministic with seed
            mean = s1["per_pair_total_cost_ratio"]["bootstrap_mean"]
            self.assertLessEqual(ci1[0], mean + 1e-12)
            self.assertGreaterEqual(ci1[1], mean - 1e-12)


if __name__ == "__main__":
    unittest.main()
