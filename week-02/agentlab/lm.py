class Ledger:
    def __init__(self, price_in=0.15, price_out=0.60):
        self.price_in = price_in
        self.price_out = price_out
        self.entries = []

    def record(self, input_tokens, output_tokens):
        cost = (
            input_tokens * self.price_in + output_tokens * self.price_out
        ) / 1_000_000
        self.entries.append(
            {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost,
            }
        )
        return cost

    @property
    def total_cost(self):
        return sum(entry["cost_usd"] for entry in self.entries)
