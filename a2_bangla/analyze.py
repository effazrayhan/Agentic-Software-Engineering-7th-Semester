import argparse
import csv
import math
import os
import random
import statistics
from collections import defaultdict


def read_results(path):
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            # normalize types
            r["id"] = str(r.get("id"))
            r["input_tokens"] = int(float(r.get("input_tokens", 0) or 0))
            r["output_tokens"] = int(float(r.get("output_tokens", 0) or 0))
            r["cost_usd"] = float(r.get("cost_usd", 0) or 0.0)
            r["latency_s"] = float(r.get("latency_s", 0) or 0.0)
            rows.append(r)
    return rows


def read_dataset_categories(dataset_path):
    cats = {}
    if not dataset_path or not os.path.exists(dataset_path):
        return cats
    with open(dataset_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            cats[str(r.get("id"))] = r.get("category")
    return cats


def build_pairs(results_rows):
    by_id_lang = {}
    for r in results_rows:
        by_id_lang[(r["id"], r["language"])] = r
    pairs = []
    ids = sorted({r["id"] for r in results_rows}, key=lambda x: int(x) if str(x).isdigit() else str(x))
    for rid in ids:
        en = by_id_lang.get((rid, "english"))
        bn = by_id_lang.get((rid, "bangla"))
        if not en or not bn:
            continue
        pairs.append((rid, en, bn))
    return pairs


def _safe_ratio(num, den):
    if den == 0:
        return float("inf") if num != 0 else 0.0
    return num / den


def compute_comparison(pairs, categories=None):
    rows = []
    for rid, en, bn in pairs:
        en_in, bn_in = en["input_tokens"], bn["input_tokens"]
        en_out, bn_out = en["output_tokens"], bn["output_tokens"]
        en_cost = en["cost_usd"]
        bn_cost = bn["cost_usd"]
        row = {
            "id": rid,
            "category": (categories or {}).get(rid, ""),
            "english_input_tokens": en_in,
            "bangla_input_tokens": bn_in,
            "english_output_tokens": en_out,
            "bangla_output_tokens": bn_out,
            "input_ratio": _safe_ratio(bn_in, en_in),
            "output_ratio": _safe_ratio(bn_out, en_out),
            "english_total_cost": en_cost,
            "bangla_total_cost": bn_cost,
            "total_cost_ratio": _safe_ratio(bn_cost, en_cost),
        }
        rows.append(row)
    return rows


def bootstrap_mean_ci(values, n=10000, seed=0, alpha=0.05):
    vals = list(values)
    if not vals:
        return (0.0, 0.0, 0.0)
    rng = random.Random(seed)
    means = []
    m = len(vals)
    for _ in range(n):
        sample = [vals[rng.randrange(m)] for _ in range(m)]
        means.append(statistics.fmean(sample))
    means.sort()
    lo_idx = int((alpha / 2.0) * n)
    hi_idx = int((1 - alpha / 2.0) * n) - 1
    lo_idx = max(0, min(lo_idx, n - 1))
    hi_idx = max(0, min(hi_idx, n - 1))
    return (statistics.fmean(vals), means[lo_idx], means[hi_idx])


def summarize(comparison_rows, results_rows):
    def stats(vals):
        if not vals:
            return {"mean": 0, "median": 0, "min": 0, "max": 0}
        return {
            "mean": statistics.fmean(vals),
            "median": statistics.median(vals),
            "min": min(vals),
            "max": max(vals),
        }

    input_ratios = [r["input_ratio"] for r in comparison_rows]
    output_ratios = [r["output_ratio"] for r in comparison_rows]
    total_cost_ratios = [r["total_cost_ratio"] for r in comparison_rows]

    total_en_in = sum(r["english_input_tokens"] for r in comparison_rows)
    total_bn_in = sum(r["bangla_input_tokens"] for r in comparison_rows)
    total_en_out = sum(r["english_output_tokens"] for r in comparison_rows)
    total_bn_out = sum(r["bangla_output_tokens"] for r in comparison_rows)
    total_en_cost = sum(r["english_total_cost"] for r in comparison_rows)
    total_bn_cost = sum(r["bangla_total_cost"] for r in comparison_rows)

    mean_ratio, ci_lo, ci_hi = bootstrap_mean_ci(total_cost_ratios, n=10000, seed=0)

    lat_en = [r["latency_s"] for r in results_rows if r["language"] == "english"]
    lat_bn = [r["latency_s"] for r in results_rows if r["language"] == "bangla"]

    # per-category ratios (mean of per-pair ratios)
    by_cat = defaultdict(lambda: {"input": [], "output": [], "total": []})
    for r in comparison_rows:
        cat = r.get("category") or "unknown"
        by_cat[cat]["input"].append(r["input_ratio"])
        by_cat[cat]["output"].append(r["output_ratio"])
        by_cat[cat]["total"].append(r["total_cost_ratio"])
    per_category = {}
    for cat, vals in sorted(by_cat.items()):
        per_category[cat] = {
            "mean_input_ratio": statistics.fmean(vals["input"]) if vals["input"] else 0,
            "mean_output_ratio": statistics.fmean(vals["output"]) if vals["output"] else 0,
            "mean_total_cost_ratio": statistics.fmean(vals["total"]) if vals["total"] else 0,
            "n": len(vals["total"]),
        }

    # largest gaps by total cost ratio
    sorted_by_gap = sorted(comparison_rows, key=lambda r: r["total_cost_ratio"], reverse=True)
    largest_gap_categories = []
    seen = set()
    for r in sorted_by_gap:
        cat = r.get("category") or "unknown"
        if cat not in seen:
            largest_gap_categories.append({"category": cat, "id": r["id"], "total_cost_ratio": r["total_cost_ratio"]})
            seen.add(cat)
        if len(largest_gap_categories) >= 3:
            break

    summary = {
        "totals": {
            "english_input_tokens": total_en_in,
            "bangla_input_tokens": total_bn_in,
            "english_output_tokens": total_en_out,
            "bangla_output_tokens": total_bn_out,
            "english_total_cost": total_en_cost,
            "bangla_total_cost": total_bn_cost,
        },
        "input_cost_ratio_total": _safe_ratio(total_bn_in, total_en_in),
        "total_cost_ratio_total": _safe_ratio(total_bn_cost, total_en_cost),
        "per_pair_input_ratio": stats(input_ratios),
        "per_pair_output_ratio": stats(output_ratios),
        "per_pair_total_cost_ratio": {**stats(total_cost_ratios), "bootstrap_mean": mean_ratio, "bootstrap_95ci_low": ci_lo, "bootstrap_95ci_high": ci_hi},
        "latency": {"english": stats(lat_en), "bangla": stats(lat_bn)},
        "per_category": per_category,
        "largest_gap_categories": largest_gap_categories,
    }
    return summary


def write_comparison_csv(rows, path):
    fields = [
        "id", "category", "english_input_tokens", "bangla_input_tokens",
        "english_output_tokens", "bangla_output_tokens",
        "input_ratio", "output_ratio", "english_total_cost", "bangla_total_cost", "total_cost_ratio",
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def make_chart(comparison_rows, out_path):
    # ratio per category (mean total cost ratio)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:
        # fallback: write a tiny placeholder text file? better create simple PNG-less note
        raise

    by_cat = defaultdict(list)
    for r in comparison_rows:
        by_cat[r.get("category") or "unknown"].append(r["total_cost_ratio"])
    cats = sorted(by_cat.keys())
    means = [statistics.fmean(by_cat[c]) for c in cats]

    plt.figure(figsize=(8, 4.5))
    plt.bar(cats, means, color="#4C78A8")
    plt.axhline(1.0, color="gray", linestyle="--", linewidth=1)
    plt.ylabel("Mean total cost ratio (Bangla / English)")
    plt.xlabel("Category")
    plt.title("Bangla vs English total cost ratio by category")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def analyze(results_path="results.csv", dataset_path="dataset.tsv", comparison_out="comparison.csv", chart_out="chart.png"):
    results = read_results(results_path)
    cats = read_dataset_categories(dataset_path)
    pairs = build_pairs(results)
    comp = compute_comparison(pairs, categories=cats)
    write_comparison_csv(comp, comparison_out)
    summary = summarize(comp, results)
    try:
        make_chart(comp, chart_out)
        summary["chart"] = chart_out
    except Exception as e:
        summary["chart_error"] = str(e)
    return summary, comp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results.csv")
    ap.add_argument("--dataset", default="dataset.tsv")
    ap.add_argument("--comparison", default="comparison.csv")
    ap.add_argument("--chart", default="chart.png")
    args = ap.parse_args()
    summary, _ = analyze(args.results, args.dataset, args.comparison, args.chart)
    import json
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
