# Assignment 2 Report — English vs Bangla Token Cost

**Model:** `qwen2.5:3b` (Ollama, `http://localhost:11434`)  
**Settings (as implemented):** temperature `0`, fixed seed `0` (smoke/baseline used), `num_predict` `256` (smoke limited to 64 where noted), same fixed system prompt for every call, `keep_alive: 0` on every call, no "answer in the same language" instruction.  
**Cost model (notional):** input $0.15 / 1M tokens, output $0.60 / 1M tokens.  
**Status:** **DRAFT / NOT FINAL** — dataset requires student review/approval of every Bangla line; full 50-pair (100-prompt) run and full analysis/chart are not complete. Numbers below are from real smoke/baseline artifacts only.

## Dataset
- `a2_bangla/dataset.tsv`: **50 aligned pairs** drafted across categories `question, instruction, explanation, arithmetic, summarise, long` (3–5 sentence long items included), with matching meaning intended.
- **Needs approval:** per spec, student must review/correct EVERY Bangla line before the full run. See `a2_bangla/DATASET_REVIEW_NOTES.md` for pairs flagged as least certain.

## Measurement & methodology
- `counter.py`: reusable `count_tokens` with injectable backend; returns `input_tokens` (`prompt_eval_count`), `output_tokens` (`eval_count`), `latency_s`, `done_reason`, `output_text`; `keep_alive=0` always. Baseline measured once with tiny prompt `"hi"`; cache check runs same prompt twice and confirms identical `prompt_eval_count` (flags missing/mismatch).
- `runner.py`: sends English and Bangla with identical settings, writes `results.csv` with required columns, resumable.
- `analyze.py`: produces `comparison.csv` (per-pair EN/BN input/output tokens, input/output/total cost ratios), summary stats (totals, input/total cost ratios, mean/median/min/max, bootstrap 95% CI with 10,000 resamples, fixed seed), latency per language, per-category ratios, largest-gap categories, and a category-ratio chart PNG.

## Baseline & cache check (real)
From `a2_bangla/baseline_and_cache.json` (prompt `"hi"`):
- Baseline: `input_tokens=20`, `output_tokens=10`, `done_reason=stop`, latency ~`6.44s`, output: `"Hello! How can I assist you today?"`
- Cache check: **OK** (`prompt_eval_count` identical on two consecutive calls with `keep_alive=0`: `20`, `20`).

## Smoke run (real, partial/incomplete)
- Command: `python3 runner.py --dataset dataset.tsv --out smoke_results.csv --limit-pairs 3 --num-predict 64`
- `smoke_results.csv` contains partial results (run may not have completed all 6 prompts at generation time). Analysis artifacts generated: `smoke_comparison.csv`, attempt at `smoke_chart.png`.
- **Smoke summary (from completed pair(s) only, via `analyze.py` on `smoke_results.csv`):**
  - Totals (completed rows): EN in `27`, BN in `50`, EN out `10`, BN out `39`, EN cost `1.005e-05`, BN cost `3.09e-05`
  - Input cost ratio (total): `1.8518518518518519`; Total cost ratio (total): `3.074626865671642`
  - Per-pair total cost ratio: mean/median/min/max `3.074626865671642`, bootstrap 95% CI `[3.074626865671642, 3.074626865671642]` (n=1 completed pair)
  - Per-category (question, n=1): mean input ratio `1.8519`, mean output ratio `3.9`, mean total cost ratio `3.0746`
  - Latency (completed rows): EN mean `27.45s` (min `8.77`, max `46.14`), BN mean `47.32s`
  - Chart: generation failed in this environment (`No module named 'matplotlib'`) for the smoke analysis.

> These smoke numbers are **not** representative of the full 50-pair dataset; they reflect only the completed pair(s) in `smoke_results.csv`.

## Full run results (required for final)
_TODO — after dataset approval, run the full 100-prompt experiment and regenerate analysis:_
```bash
cd a2_bangla
python3 runner.py --dataset dataset.tsv --out results.csv --num-predict 256 --seed 0 --temperature 0
python3 analyze.py --results results.csv --dataset dataset.tsv --comparison comparison.csv --chart chart.png
```
Include in final report:
- Table of all measures (totals, input/total cost ratios, mean/median/min/max, bootstrap 95% CI of per-pair ratio, latency per language).
- Per-category ratios and largest-gap categories.
- Chart image (`chart.png`).

## TODO (student, after reading outputs)
- **10-pair quality check:** _TODO — manually review 10 pairs from outputs for meaning equivalence/quality._
- **Surprising prompt explanation:** _TODO — explain a surprising prompt/case._
- **Candidate extreme-ratio pairs (suggested after full run):** _TODO — populate from `comparison.csv` (highest/lowest total cost ratios) once full results exist._

## Reproducibility notes
- Identical settings for EN/BN, fixed system prompt, `keep_alive=0` each call, deterministic bootstrap seed. Results depend on the local `qwen2.5:3b` model/runtime and are written as real artifacts (no fabricated numbers).
