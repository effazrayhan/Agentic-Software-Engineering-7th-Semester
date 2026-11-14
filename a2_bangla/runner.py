import argparse
import csv
import os

import counter
import llm


RESULT_COLUMNS = [
    "id", "language", "prompt", "output", "input_tokens", "output_tokens",
    "cost_usd", "latency_s", "done_reason",
]


def load_dataset(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            rows.append(r)
    return rows


def _read_done_keys(results_path):
    done = set()
    if not os.path.exists(results_path):
        return done
    with open(results_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                done.add((str(r.get("id")), r.get("language")))
            except Exception:
                pass
    return done


def run(dataset_path="dataset.tsv", out_path="results.csv", client=None, limit_pairs=None,
        system_prompt=counter.FIXED_SYSTEM_PROMPT, temperature=0, seed=0, num_predict=256):
    client = client or llm.OllamaClient()
    data = load_dataset(dataset_path)
    if limit_pairs is not None:
        data = data[:limit_pairs]

    done = _read_done_keys(out_path)
    file_exists = os.path.exists(out_path) and os.path.getsize(out_path) > 0
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    with open(out_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RESULT_COLUMNS)
        if not file_exists:
            writer.writeheader()
            f.flush()

        for row in data:
            rid = str(row["id"])
            for lang, text in (("english", row["english"]), ("bangla", row["bangla"])):
                key = (rid, lang)
                if key in done:
                    continue
                res = counter.count_tokens(
                    client,
                    text,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    seed=seed,
                    num_predict=num_predict,
                )
                c = counter.cost_usd(res["input_tokens"], res["output_tokens"])
                out = {
                    "id": rid,
                    "language": lang,
                    "prompt": text,
                    "output": res.get("output_text", ""),
                    "input_tokens": res["input_tokens"],
                    "output_tokens": res["output_tokens"],
                    "cost_usd": f"{c:.12f}",
                    "latency_s": f"{res.get('latency_s', 0.0):.6f}",
                    "done_reason": res.get("done_reason") or "",
                }
                writer.writerow(out)
                f.flush()
                done.add(key)
                print(f"done id={rid} lang={lang}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="dataset.tsv")
    ap.add_argument("--out", default="results.csv")
    ap.add_argument("--limit-pairs", type=int, default=None)
    ap.add_argument("--num-predict", type=int, default=256)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--temperature", type=float, default=0.0)
    args = ap.parse_args()
    run(
        dataset_path=args.dataset,
        out_path=args.out,
        limit_pairs=args.limit_pairs,
        temperature=args.temperature,
        seed=args.seed,
        num_predict=args.num_predict,
    )


if __name__ == "__main__":
    main()
