import unittest

from agentlab.lm import Ledger


class TestLedger(unittest.TestCase):
    def test_price_arithmetic(self):
        ledger = Ledger()
        self.assertAlmostEqual(ledger.record(1_000_000, 1_000_000), 0.75)

    def test_totals_accumulate(self):
        ledger = Ledger()
        ledger.record(1000, 500)
        ledger.record(2000, 250)
        self.assertEqual(len(ledger.entries), 2)
        self.assertAlmostEqual(
            ledger.total_cost, (3000 * 0.15 + 750 * 0.60) / 1_000_000
        )

    def test_custom_rates(self):
        ledger = Ledger(price_in=1.0, price_out=2.0)
        self.assertAlmostEqual(ledger.record(1_000_000, 1_000_000), 3.0)


if __name__ == "__main__":
    unittest.main()
