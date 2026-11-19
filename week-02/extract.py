import argparse
import json
import urllib.request

from agentlab.lm import Ledger
from notices import load_corpus, load_schema, validate_notice

SYSTEM_PROMPT = (
    "Extract the domain notice into one JSON object with exactly these fields: "
    "schema_version, notice_id, domain, notice_type, severity, due_date, summary. "
    "Use schema_version '1.0'. notice_type is one of renewal, expiry, suspension, "
    "transfer, ownership, dns, security. severity is one of info, warning, critical. "
    "due_date is YYYY-MM-DD or null. Return JSON only."
)
APPROACHES = ("prompt_only", "grammar")


def build_prompt(notice):
    return f"Notice {notice['id']}: {notice['text']}"


def parse_reply(text):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = (
            cleaned.removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    return value if validate_notice(value) else None


def run_extraction(notices, backend, ledger, runs=3):
    schema = load_schema()
    rows = []
    for notice in notices:
        prompt = build_prompt(notice)
        for approach in APPROACHES:
            for run in range(1, runs + 1):
                reply = backend.chat(
                    SYSTEM_PROMPT,
                    prompt,
                    schema if approach == "grammar" else None,
                )
                cost = ledger.record(reply["input_tokens"], reply["output_tokens"])
                rows.append(
                    {
                        "notice_id": notice["id"],
                        "approach": approach,
                        "run": run,
                        "output": reply["text"],
                        "valid": parse_reply(reply["text"]) is not None,
                        "input_tokens": reply["input_tokens"],
                        "output_tokens": reply["output_tokens"],
                        "cost_usd": cost,
                    }
                )
    return rows


def summarize(rows):
    summary = {}
    for approach in APPROACHES:
        subset = [row for row in rows if row["approach"] == approach]
        valid = sum(row["valid"] for row in subset)
        summary[approach] = {
            "calls": len(subset),
            "valid": valid,
            "valid_rate": valid / len(subset) if subset else 0.0,
            "cost_usd": sum(row["cost_usd"] for row in subset),
        }
    return summary


class OllamaBackend:
    def __init__(self, model="qwen2.5:3b", url="http://localhost:11434/api/chat"):
        self.model = model
        self.url = url

    def chat(self, system, prompt, schema=None):
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "options": {"temperature": 0, "seed": 0, "num_predict": 256},
            "stream": False,
            "keep_alive": 0,
        }
        if schema is not None:
            body["format"] = schema
        request = urllib.request.Request(
            self.url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=300) as response:
            data = json.load(response)
        return {
            "text": data["message"]["content"],
            "input_tokens": data["prompt_eval_count"],
            "output_tokens": data["eval_count"],
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="results.jsonl")
    parser.add_argument("--summary", default="comparison.json")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--model", default="qwen2.5:3b")
    args = parser.parse_args()

    ledger = Ledger()
    rows = run_extraction(
        load_corpus()["notices"], OllamaBackend(args.model), ledger, args.runs
    )
    with open(args.out, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    with open(args.summary, "w", encoding="utf-8") as handle:
        json.dump(summarize(rows), handle, ensure_ascii=False, indent=2)
    print(f"{len(rows)} calls, ledger total ${ledger.total_cost:.6f}")


if __name__ == "__main__":
    main()
